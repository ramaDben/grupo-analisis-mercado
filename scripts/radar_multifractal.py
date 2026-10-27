"""Radar multifractal: qué líneas tocó cada activo y cuáles va a tocar, en 1H, 4H y 1D.

Spec `docs/superpowers/specs/2026-10-26-radar-multifractal-design.md` §4, §6 y §8. Es el
orquestador: arma el universo, verifica la cuenta, lee las velas, le pide al motor la
lectura de cada marco (`estrategia.tori.radar.leer_marco`) y escribe una página HTML.
No traza nada propio: toda la técnica vive en `scripts/estrategia/`.

Es una herramienta interna del director. **No publica ni manda nada a ningún canal**:
su única salida es un archivo en `data/radar/` (gitignoreado).

    uv run --with MetaTrader5 python scripts/radar_multifractal.py
    uv run --with MetaTrader5 python scripts/radar_multifractal.py --simbolos XAUUSD,USDCLP --sin-abrir

Tres decisiones que conviene no revertir:

1. **La cuenta se verifica antes de leer.** El radar lee en vivo y no tiene sello en
   archivo, así que compara `account_info().login` con `config/cuenta_mt5.json`. Si no
   coincide no escanea: una matriz leída sobre otra cuenta es la de otro instrumento.
2. **Observación de Mercado se registra antes y se restaura en un `finally`.**
   `mt5_client.get_rates` hace `symbol_select(True)` para poder leer, y el radar recorre
   todo el universo: sin restaurar, el terminal del director quedaría con 137 símbolos
   abiertos.
3. **Una falla es de un marco o de un símbolo, nunca del escaneo.** Cada una queda en la
   página con su motivo; un radar que descarta en silencio no se puede auditar.
"""
from __future__ import annotations

import argparse
import sys
import time
import webbrowser
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

_RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(_RAIZ / "src"), str(_RAIZ / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from estrategia.fuente import RELOJ, cierre_santiago, offset_servidor, velas_mt5  # noqa: E402
from estrategia.tori.parametros import PARAMETROS  # noqa: E402
from estrategia.tori.radar import MARCOS_RADAR, RADAR_MARCOS, LecturaMarco, leer_marco  # noqa: E402
from guardrails.cuenta import cuenta_correcta  # noqa: E402
from market_data_mcp import mt5_client  # noqa: E402
from radar_html import Escaneo, Falla, Fila, render, render_error  # noqa: E402
from radar_paridad import comparar, leer_objetos, ruta_objetos  # noqa: E402

SANTIAGO = ZoneInfo("America/Santiago")
SALIDA = _RAIZ / "data" / "radar"


@dataclass(frozen=True)
class Simbolo:
    ticker: str
    digits: int
    categoria: str            # primer tramo de symbol_info.path ("Forex", "Stocks"...)
    visible: bool             # estaba en Observación de Mercado antes de empezar


def _ahora_santiago() -> datetime:
    return datetime.now(SANTIAGO)


def _terminal():
    """El módulo MetaTrader5. Va en una función para que los tests le pongan uno falso."""
    import MetaTrader5 as mt5

    return mt5


def universo(mt5) -> list[Simbolo]:
    """Los símbolos operables del terminal: `trade_mode` FULL, como `simulador_gi.py`.

    Un símbolo en solo cierre o deshabilitado no tiene a quién avisarle que toca una
    línea. La visibilidad se toma acá, antes de cualquier lectura, porque leer lo
    selecciona y después ya no se sabe cómo estaba.
    """
    full = mt5.SYMBOL_TRADE_MODE_FULL
    return [
        Simbolo(s.name, int(s.digits), str(s.path or "").split("\\")[0], bool(s.visible))
        for s in (mt5.symbols_get() or ())
        if s.trade_mode == full
    ]


def _cuenta(mt5) -> int:
    info = mt5.account_info()
    try:
        return int(info.login)
    except (AttributeError, TypeError, ValueError):
        return 0


def escanear(simbolos: list[Simbolo], mt5, leer_velas=velas_mt5,
             ahora: Callable[[], datetime] = _ahora_santiago) -> Escaneo:
    """Lee cada símbolo en los marcos del radar y junta filas y fallas.

    Una sola lectura de velas por símbolo (W1/D1/H4/H1 cerradas; la vela en curso la
    separa `velas_mt5` y no entra). Una excepción de la lectura es falla del símbolo; una
    del motor (historia insuficiente, marco ausente, ATR 0) es falla de ese marco, y los
    demás marcos y símbolos se leen igual. La paridad la agrega `main`.
    """
    inicio = ahora()
    t0 = time.monotonic()
    filas: list[Fila] = []
    fallas: list[Falla] = []
    # El desfase del servidor se mide una vez: es el mismo para todo el universo.
    reloj = mt5.symbol_info_tick(RELOJ)
    offset = offset_servidor(int(reloj.time), time.time()) if reloj is not None else None
    if offset is None:
        fallas.append(Falla(RELOJ, None, "sin cotización del reloj del servidor: "
                                         "las horas de cierre no se muestran"))
    try:
        for sim in simbolos:
            try:
                velas, _en_curso = leer_velas(sim.ticker, MARCOS_RADAR)
            except Exception as exc:  # noqa: BLE001 - un símbolo no corta el escaneo
                fallas.append(Falla(sim.ticker, None, str(exc) or type(exc).__name__))
                continue
            marcos: dict[str, LecturaMarco] = {}
            cierres: dict[str, datetime] = {}
            for marco in RADAR_MARCOS:
                try:
                    lectura = leer_marco(velas, marco, sim.digits, PARAMETROS)
                except KeyError as exc:
                    fallas.append(Falla(sim.ticker, marco, f"MT5 no entregó velas de {exc}"))
                    continue
                except ValueError as exc:  # incluye HistoriaInsuficiente
                    fallas.append(Falla(sim.ticker, marco, str(exc)))
                    continue
                marcos[marco] = lectura
                if offset is not None:
                    cierres[marco] = cierre_santiago(lectura.vela, marco, offset)
            if marcos:
                filas.append(Fila(sim.ticker, sim.categoria, sim.digits, marcos, cierres))
    finally:
        # Lo que el director no tenía abierto vuelve a cerrarse, pase lo que pase.
        for sim in simbolos:
            if not sim.visible:
                try:
                    mt5.symbol_select(sim.ticker, False)
                except Exception:  # noqa: BLE001 - restaurar uno no impide restaurar el resto
                    pass
    return Escaneo(inicio=inicio, duracion_s=time.monotonic() - t0, cuenta=_cuenta(mt5),
                   leidos=len(simbolos), filas=tuple(filas), fallas=tuple(fallas), paridad=())


def _paridad(e: Escaneo) -> tuple[str, ...]:
    """Las diferencias contra el indicador de MT5. Nunca mata el escaneo.

    Un JSON del exportador mal formado puede lanzar dentro de `leer_objetos` o de
    `comparar`; eso es una línea más de la página, no una corrida perdida.
    """
    try:
        objetos = leer_objetos(ruta_objetos(), e.inicio)
        if isinstance(objetos, str):
            return (objetos,)
        lecturas = {(f.ticker, m): lm for f in e.filas for m, lm in f.marcos.items()}
        digits = {f.ticker: f.digits for f in e.filas}
        return tuple(comparar(objetos, lecturas, digits, PARAMETROS))
    except Exception as exc:  # noqa: BLE001
        return (f"no se pudo verificar la paridad: {exc}",)


def _escribir(html: str, raiz: Path, inicio: datetime) -> Path:
    """La página del día y la copia en `ultimo.html`, siempre en UTF-8."""
    destino = raiz / inicio.strftime("%Y-%m-%d") / f"radar_{inicio.strftime('%H-%M')}.html"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    (raiz / "ultimo.html").write_text(html, encoding="utf-8")
    return destino


def _args(argv: list[str] | None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Radar multifractal: qué mirar hoy en 1H, 4H y 1D.")
    ap.add_argument("--simbolos", help="lista separada por comas, para una prueba acotada")
    ap.add_argument("--sin-abrir", action="store_true", help="no abrir la página al terminar")
    ap.add_argument("--salida", type=Path, default=SALIDA,
                    help="carpeta raíz de las páginas (por defecto data/radar)")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _args(argv)
    inicio = _ahora_santiago()

    def terminar(html: str, codigo: int) -> int:
        destino = _escribir(html, args.salida, inicio)
        if not args.sin_abrir:
            webbrowser.open(destino.resolve().as_uri())
        print(destino)
        return codigo

    try:
        mt5 = _terminal()
        mt5_client.connect()
    except Exception as exc:  # noqa: BLE001 - incluye el paquete MetaTrader5 ausente
        return terminar(render_error("MT5 no responde", str(exc) or type(exc).__name__, inicio), 1)

    info = mt5.account_info()
    veredicto = cuenta_correcta(getattr(info, "login", None))
    if not veredicto.ok:
        detalle = getattr(veredicto, "detalle", "") or getattr(veredicto, "motivo", "")
        return terminar(render_error("Cuenta MT5 inesperada", detalle, inicio), 1)

    simbolos = universo(mt5)
    fuera: list[Falla] = []
    if args.simbolos:
        pedidos = [t.strip() for t in args.simbolos.split(",") if t.strip()]
        por_ticker = {s.ticker: s for s in simbolos}
        simbolos = [por_ticker[t] for t in pedidos if t in por_ticker]
        fuera = [Falla(t, None, "no está entre los símbolos operables del terminal")
                 for t in pedidos if t not in por_ticker]

    # `velas_mt5` se pasa explícito para leer el nombre del módulo en el momento.
    e = escanear(simbolos, mt5, leer_velas=velas_mt5, ahora=lambda: inicio)
    e = replace(e, leidos=e.leidos + len(fuera), fallas=tuple(fuera) + e.fallas,
                paridad=_paridad(e))
    return terminar(render(e), 0)


if __name__ == "__main__":
    raise SystemExit(main())
