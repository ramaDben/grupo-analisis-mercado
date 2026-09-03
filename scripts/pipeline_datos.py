#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""La cadena de datos del Playbook: un punto de entrada y un solo reloj.

Por qué existe. La cadena eran tres invocaciones manuales con un orden que solo
vivía en la cabeza del director:

    pipeline_ingesta.py   ->  data central/DATA */raw + latest_drivers.json
    extractor_precios.py  ->  data central/DATA PRECIOS OHLC/
    macro_bias_engine.py  ->  macro_bias_output.json

Saltarse un paso o invertir el orden no rompe nada de forma visible, que es el
problema: correr el motor sobre precios que no se actualizaron produce un sesgo
que *parece* fresco. Y si faltan las series, `ticket_engine.cargar_serie_h1_archivo`
devuelve `None` en silencio y el motor simplemente deja de emitir tickets.

Y había tres archivos de fecha (`estado_ejecucion.json`, `latest_prices_summary.json`,
`macro_bias_output.json`) que ningún consumidor miraba juntos, así que cada uno
decidía por su cuenta si el dato servía y casi todos decidían que sí por defecto.

Este módulo hace dos cosas y nada más: corre la cadena en orden abortando al
primer fallo, y lee los tres relojes en una sola respuesta.

El umbral de vencimiento NO se inventa acá: sale de `bias_reader`, que ya lo lee
de `playbook_config.yaml` y contempla el fin de semana. Dos reglas de staleness
distintas serían el mismo error que dos fórmulas de ATR.

Uso:
    uv run --with MetaTrader5 python scripts/pipeline_datos.py            # corre la cadena
    uv run python scripts/pipeline_datos.py --estado                      # solo reporta
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Sequence

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "src") not in sys.path:
    sys.path.insert(0, str(RAIZ / "src"))

DATA_CENTRAL = RAIZ / "data central"
INGESTA = RAIZ / ".agents" / "skills" / "ecosistema-datos-macro" / "scripts" / "pipeline_ingesta.py"

# El mismo umbral que aplica el escaner, importado y no copiado: dos numeros para
# la misma decision dejarian al estado diciendo que se puede publicar mientras el
# escaner excluye igual.
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))
from screener_gi import UMBRAL_CONFIANZA_PCT  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# Los pasos, en el único orden que produce un resultado coherente
# ─────────────────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Paso:
    nombre: str
    script: Path
    produce: str


@dataclass(frozen=True)
class Resultado:
    nombre: str
    ok: bool
    detalle: str = ""


PASOS: tuple[Paso, ...] = (
    Paso("ingesta", INGESTA, "drivers macro oficiales (FRED, BCCh, BCE, COMEX)"),
    Paso("precios", RAIZ / "scripts" / "extractor_precios.py", "series OHLC + indicadores"),
    Paso("sesgo", RAIZ / "scripts" / "macro_bias_engine.py", "régimen, sesgo y SL del Playbook"),
)


def correr_subproceso(paso: Paso) -> tuple[bool, str]:
    """Corredor real. Se inyecta en los tests para no depender de MT5 ni de la red."""
    proc = subprocess.run(
        [sys.executable, str(paso.script)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode == 0:
        return True, ""
    salida = (proc.stderr or proc.stdout or "").strip()
    return False, salida[-600:] or f"código de salida {proc.returncode}"


def ejecutar_cadena(
    pasos: Sequence[Paso],
    corredor: Callable[[Paso], tuple[bool, str]] = correr_subproceso,
) -> list[Resultado]:
    """Corre los pasos en orden y ABORTA al primer fallo.

    Abortar es deliberado: seguir con el paso siguiente sobre datos que no se
    actualizaron no deja el sistema a medias, lo deja convincentemente mal.
    """
    resultados: list[Resultado] = []
    for paso in pasos:
        ok, detalle = corredor(paso)
        resultados.append(Resultado(paso.nombre, ok, detalle))
        if not ok:
            break
    return resultados


# ─────────────────────────────────────────────────────────────────────────────
# Los tres relojes, leídos juntos
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Reloj:
    nombre: str
    describe: str
    as_of: str | None = None
    antiguedad_h: float | None = None
    umbral_h: float | None = None
    error: str | None = None

    @property
    def fresco(self) -> bool:
        return self.error is None


@dataclass
class EstadoDatos:
    relojes: list[Reloj] = field(default_factory=list)
    confianza_pct: float | None = None

    @property
    def confianza_suficiente(self) -> bool:
        """Un snapshot sin confianza declarada NO pasa.

        Asumir que alcanza seria la puerta de atras que el umbral existe para
        cerrar: bastaria con que el motor dejara de emitir el campo.
        """
        return self.confianza_pct is not None and self.confianza_pct >= UMBRAL_CONFIANZA_PCT

    @property
    def listo(self) -> bool:
        """Relojes frescos Y modelo que ve.

        Frescura y confianza son cosas distintas, pero ninguna sola alcanza para
        publicar. El estado decia "Datos frescos" con la confianza en 54,7 % y
        dos drivers rotos: tecnicamente cierto y operativamente inutil.
        """
        return (
            bool(self.relojes)
            and all(r.fresco for r in self.relojes)
            and self.confianza_suficiente
        )


def _leer(ruta: Path) -> tuple[dict | None, str | None]:
    if not ruta.exists():
        return None, f"no existe {ruta.name}"
    try:
        return json.loads(ruta.read_text(encoding="utf-8")), None
    except Exception as exc:  # noqa: BLE001
        return None, f"{ruta.name} ilegible ({exc.__class__.__name__})"


def _evaluar(reloj: Reloj, as_of: str | None, ahora: datetime | None) -> Reloj:
    """Aplica el mismo umbral de staleness del Playbook, fin de semana incluido."""
    from market_data_mcp.bias_reader import cargar_config_staleness, validar_staleness

    fresco, horas, umbral, razon = validar_staleness(
        as_of, cargar_config_staleness(), now_dt=ahora
    )
    reloj.as_of = as_of
    reloj.umbral_h = round(umbral, 1)
    if razon == "MALFORMED_DATE":
        reloj.error = "fecha ilegible o ausente"
        return reloj
    reloj.antiguedad_h = round(horas, 1)
    if not fresco:
        reloj.error = f"vencido: {horas:.1f} h sobre un umbral de {umbral:.0f} h"
    return reloj


def estado_datos(data_central: Path | None = None, ahora: datetime | None = None) -> EstadoDatos:
    """Los tres relojes de la cadena en una sola respuesta.

    `data_central` se parametriza para poder testear sin tocar los datos reales.
    """
    raiz = data_central or DATA_CENTRAL
    ahora = ahora or datetime.now(timezone.utc)
    est = EstadoDatos()

    # 1. Ingesta: además de la fecha, informa si alguna fuente falló.
    r = Reloj("ingesta", "drivers macro oficiales")
    data, err = _leer(raiz / "DATA AGENDA" / "estado_ejecucion.json")
    if err:
        r.error = err
    else:
        _evaluar(r, data.get("ultima_ejecucion_utc"), ahora)
        fallidas = sorted(
            set(data.get("errores_por_fuente") or {})
            | {f for f, s in (data.get("status_por_fuente") or {}).items() if s != "OK"}
        )
        if fallidas and r.error is None:
            r.error = f"fuentes con problemas: {', '.join(fallidas)}"
    est.relojes.append(r)

    # 2. Precios
    r = Reloj("precios", "series OHLC + indicadores")
    data, err = _leer(raiz / "DATA PRECIOS OHLC" / "latest_prices_summary.json")
    if err:
        r.error = err
    else:
        _evaluar(r, data.get("as_of_utc"), ahora)
    est.relojes.append(r)

    # 3. Sesgo del Playbook
    r = Reloj("sesgo", "régimen, sesgo y SL")
    data, err = _leer(raiz / "DATA DRIVERS USDCLP" / "macro_bias_output.json")
    if err:
        r.error = err
    else:
        _evaluar(r, data.get("as_of_utc"), ahora)
        conf = (data.get("confianza_general") or {}).get("confianza_total_pct")
        est.confianza_pct = float(conf) if conf is not None else None
    est.relojes.append(r)

    return est


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────
def imprimir_estado(est: EstadoDatos) -> None:
    print("\n=== CADENA DE DATOS ===")
    for r in est.relojes:
        if r.fresco:
            print(f"  [OK]   {r.nombre:8s} {r.antiguedad_h:5.1f} h  ({r.describe})")
        else:
            edad = f"{r.antiguedad_h:5.1f} h  " if r.antiguedad_h is not None else "  --    "
            print(f"  [FALLA]{r.nombre:8s} {edad}{r.error}")
    # El umbral es el piso algebraico del §3: si frescura y cobertura valen 1,0
    # -la condición que ese párrafo llama "operación normal"- el puntaje arrastra
    # 0,40 + 0,25 = 0,65 antes de que la antigüedad aporte nada. Bajo eso es
    # aritméticamente imposible que ambas sean 1,0.
    if est.confianza_pct is None:
        print(f"\n  [FALLA]confianza no declarada por el motor (mínimo {UMBRAL_CONFIANZA_PCT:.0f} %)")
    elif est.confianza_suficiente:
        print(f"\n  [OK]   confianza {est.confianza_pct:.1f} %  (mínimo {UMBRAL_CONFIANZA_PCT:.0f} %)")
    else:
        print(f"\n  [FALLA]confianza {est.confianza_pct:.1f} %, bajo el mínimo de "
              f"{UMBRAL_CONFIANZA_PCT:.0f} %: falta un driver o está roto")

    if est.listo:
        print("\n  LISTO: relojes frescos y el modelo ve\n")
    else:
        print("\n  NO utilizable para publicar: revisa las líneas [FALLA] de arriba\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Cadena de datos del Playbook Cuantitativo.")
    parser.add_argument("--estado", action="store_true",
                        help="Solo reporta la frescura de las tres fuentes; no ejecuta nada.")
    args = parser.parse_args()

    if args.estado:
        imprimir_estado(estado_datos())
        return 0

    print("\n=== EJECUTANDO CADENA DE DATOS ===")
    for paso in PASOS:
        print(f"  · {paso.nombre}: {paso.produce}")
    print()

    for res in ejecutar_cadena(PASOS):
        if res.ok:
            print(f"  [OK]    {res.nombre}")
        else:
            print(f"  [FALLA] {res.nombre}: {res.detalle}", file=sys.stderr)
            print("\nLa cadena se detuvo. Los pasos siguientes NO corrieron: hacerlo "
                  "sobre datos viejos produce un resultado que parece fresco.\n", file=sys.stderr)
            return 1

    imprimir_estado(estado_datos())
    return 0


if __name__ == "__main__":
    sys.exit(main())
