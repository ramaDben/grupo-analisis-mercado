#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Datos y gráficos del informe de cierre semanal, leídos del terminal al cierre.

Separado del compilador por la misma razón que `capacitacion_fundamental_ppt.py`
está separado de su `_contenido.py`: editar un número no debe obligar a tocar el
dibujo, ni al revés.

**Los precios se leen AL CIERRE y no del snapshot de la mañana.** El 2026-09-04
la serie `USDCLP_W1.json` y `macro_bias_output.json` traían 935,60, que era el
precio de las 08:37; el cierre real de esa jornada fue **933,15**. Publicar el
snapshot como cierre de la semana mueve todas las variaciones: el Oro pasaba de
-0,53 % a -1,53 % y el WTI de +9,18 % a +8,13 %. La regla 1 del proyecto ya lo
dice, y acá el error es doblemente visible porque el titular del informe es
justamente la variación semanal.

**La variación de la semana se mide contra el cierre de la vela W1 anterior**, no
contra el lunes: la vela semanal en curso arranca el domingo, así que su apertura
no es el precio con que el cliente vio cerrar el viernes pasado. Se verificó
contra el informe del 28 de agosto, cuyos seis precios publicados coinciden al
centavo con los cierres W1 que este módulo lee.

Uso:
    uv run --extra informe --with MetaTrader5 python scripts/cierre_semanal_datos.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
SRC = RAIZ / "src"
for p in (str(SRC), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SANTIAGO = ZoneInfo("America/Santiago")

# El orden es el de la portada y el de las fichas. `clase` agrupa las páginas.
ACTIVOS: tuple[dict[str, Any], ...] = (
    {"ticker": "USDCLP",     "nombre": "Dólar / Peso Chileno", "slug": "usdclp",
     "emoji": "🇨🇱", "rotulo": "USD/CLP", "digits": 2, "unidad": "",
     "clase": "soberana", "moneda": "$"},
    {"ticker": "XAUUSD",     "nombre": "Oro Spot", "slug": "xauusd",
     "emoji": "🥇", "rotulo": "ORO SPOT", "digits": 2, "unidad": " USD/oz",
     "clase": "commodities", "moneda": "$"},
    {"ticker": "COPPER",     "nombre": "Cobre de Alta Pureza", "slug": "copper",
     "emoji": "⚡", "rotulo": "COBRE", "digits": 0, "unidad": " USD/t",
     "clase": "commodities", "moneda": "$"},
    {"ticker": "WTI.spot",   "nombre": "Petróleo Crudo WTI", "slug": "wti",
     "emoji": "⛽", "rotulo": "PETRÓLEO WTI", "digits": 3, "unidad": "",
     "clase": "commodities", "moneda": "$"},
    {"ticker": "BRENT.spot", "nombre": "Petróleo Crudo Brent", "slug": "brent",
     "emoji": "🛢️", "rotulo": "BRENT", "digits": 3, "unidad": "",
     "clase": "commodities", "moneda": "$"},
    {"ticker": "US100.spot", "nombre": "Nasdaq 100", "slug": "us100",
     "emoji": "📱", "rotulo": "NASDAQ 100", "digits": 2, "unidad": " puntos",
     "clase": "equity", "moneda": ""},
    {"ticker": "USDJPY",     "nombre": "Dólar / Yen Japonés", "slug": "usdjpy",
     "emoji": "💴", "rotulo": "USD/JPY", "digits": 3, "unidad": "",
     "clase": "equity", "moneda": ""},
)

SERIES_CURVA = ("DGS2", "DGS10", "DGS30", "DFII10", "T10YIE")

NOMBRES_CURVA = {
    "DGS2": "Bono del Tesoro a 2 años (DGS2)",
    "DGS10": "Bono del Tesoro a 10 años (DGS10)",
    "DGS30": "Bono del Tesoro a 30 años (DGS30)",
    "DFII10": "Tasa real a 10 años (TIPS · DFII10)",
    "T10YIE": "Inflación esperada 10 años (T10YIE)",
}


class DatosError(RuntimeError):
    """No se pudo leer el terminal o una serie. No se emite informe sin datos."""


def coma(valor: float, digits: int) -> str:
    """Notación chilena con los decimales del catálogo.

    Es la misma función que `grafico_informe.formatear_precio`, importada de allá
    para no tener dos: un informe donde la imagen y el texto escriben el precio
    distinto se lee como un error de datos.
    """
    from grafico_informe import formatear_precio
    return formatear_precio(valor, digits)


def leer_activos() -> list[dict[str, Any]]:
    """Precio al cierre, cierre de la semana anterior y variación, por activo."""
    import MetaTrader5 as mt5

    if not mt5.initialize():
        raise DatosError(f"MT5 no inicializa: {mt5.last_error()}")
    try:
        salida: list[dict[str, Any]] = []
        for a in ACTIVOS:
            w1 = mt5.copy_rates_from_pos(a["ticker"], mt5.TIMEFRAME_W1, 0, 3)
            tick = mt5.symbol_info_tick(a["ticker"])
            if w1 is None or len(w1) < 2 or tick is None:
                raise DatosError(
                    f"{a['ticker']}: el terminal no devolvió serie semanal o precio. "
                    "El informe no sale con un activo estimado."
                )
            previo = float(w1[-2]["close"])
            actual = float(tick.bid)
            if previo <= 0:
                raise DatosError(f"{a['ticker']}: cierre semanal previo en {previo}")
            var = 100.0 * (actual / previo - 1.0)
            salida.append({
                **a,
                "previo": previo,
                "actual": actual,
                "var_pct": var,
                "previo_txt": coma(previo, a["digits"]),
                "actual_txt": coma(actual, a["digits"]),
                "var_txt": f"{var:+.2f}%".replace(".", ","),
                "sube": var >= 0,
            })
        return salida
    finally:
        mt5.shutdown()


def leer_niveles(ticker: str) -> dict[str, Any]:
    """Soportes, resistencias e indicadores de H1, para el gráfico y el texto."""
    from market_data_mcp.analisis import analizar_activo
    return analizar_activo(ticker, "H1")


def leer_curva() -> dict[str, Any]:
    """La curva soberana desde el MCP, que aplica el gate de frescura.

    Se usa la tool y no el JSON crudo a propósito: el camino crudo se saltea el
    `status` y el rezago, y este informe cita las cifras con su fecha.
    """
    from market_data_mcp.curva_reader import cargar_curva_tasas

    datos = cargar_curva_tasas("ALL")
    if "error" in datos:
        raise DatosError(f"curva soberana: {datos.get('message', datos['error'])}")
    return datos


def _bps(valor: Any) -> str:
    """Un delta en puntos base. `None` se dice, no se publica como cero.

    Cero significa "no se movió" y es distinto de "no sé": el informe del
    2026-08-28 publicó `0.0 bps` en el tramo a 2 años cuando en realidad el dato
    no se podía calcular, y esa semana el tramo se movió 20 bps.
    """
    if valor is None:
        return "no disponible"
    signo = "+" if valor > 0 else ""
    return f"{signo}{valor:.0f} bps".replace(".", ",")


def filas_curva(curva: dict[str, Any]) -> list[dict[str, str]]:
    """Las cinco series más la pendiente, listas para la tabla del informe."""
    filas: list[dict[str, str]] = []
    series = curva.get("series", {})
    for codigo in SERIES_CURVA:
        s = series.get(codigo)
        if not s or s.get("status") != "OK":
            continue
        filas.append({
            "codigo": codigo,
            "nombre": NOMBRES_CURVA[codigo],
            "nivel": f"{s['nivel_pct']:.2f}%".replace(".", ","),
            "d1": _bps(s.get("delta_1d_bps")),
            "d5": _bps(s.get("delta_5d_bps")),
            "fecha": s.get("fecha_dato", ""),
        })
    sp = curva.get("spread_2s10s") or {}
    if sp:
        filas.append({
            "codigo": "SPREAD",
            "nombre": "Diferencial Curva 10Y - 2Y (Spread)",
            "nivel": f"{sp['nivel_pct']:+.2f}%".replace(".", ","),
            "d1": _bps(sp.get("delta_1d_bps")),
            "d5": _bps(sp.get("delta_5d_bps")),
            "fecha": sp.get("fecha_dato", ""),
        })
    return filas


def generar_graficos(activos: list[dict[str, Any]], destino: Path) -> dict[str, Path]:
    """Un gráfico diario por activo, con el subtítulo del CIERRE.

    El subtítulo importa: `pipeline_informe` lo arma con el sesgo de apertura y
    escribe "Hoy lo vemos con más probabilidad de subir", que en un cierre de
    viernes le ofrece al cliente una operativa que ya no existe. Y va **dentro
    de la imagen**, así que no se arregla editando texto.
    """
    from grafico_informe import GraficoError, construir_grafico

    destino.mkdir(parents=True, exist_ok=True)
    rutas: dict[str, Path] = {}
    for a in activos:
        sub = (
            f"Cerró la semana en {a['actual_txt']}{a['unidad']} · "
            f"{a['var_txt']} en cinco sesiones"
        )
        try:
            niveles = leer_niveles(a["ticker"])
        except Exception as exc:  # noqa: BLE001
            raise DatosError(f"{a['ticker']}: sin niveles para el gráfico ({exc})") from exc
        ruta = construir_grafico(
            a["ticker"], a["nombre"], destino / f"{a['slug']}.png",
            timeframe="D1", tema="claro", subtitulo=sub,
            niveles=niveles, digits=a["digits"],
        )
        rutas[a["slug"]] = ruta
        print(f"  [OK] {a['slug']:8} {sub}")
    return rutas


def reunir(destino_graficos: Path | None = None) -> dict[str, Any]:
    """Todo lo que el compilador necesita del terminal y de las series oficiales."""
    ahora = datetime.now(tz=SANTIAGO)
    activos = leer_activos()
    curva = leer_curva()
    rutas = {}
    if destino_graficos is not None:
        print("Graficos:")
        rutas = generar_graficos(activos, destino_graficos)
    return {
        "generado": ahora.isoformat(),
        "fecha_larga": _fecha_larga(ahora),
        "fecha_corta": ahora.strftime("%Y-%m-%d"),
        "activos": activos,
        "curva": curva,
        "filas_curva": filas_curva(curva),
        "graficos": {k: str(v) for k, v in rutas.items()},
    }


_MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
          "agosto", "septiembre", "octubre", "noviembre", "diciembre")
_DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")


def _fecha_larga(dt: datetime) -> str:
    return f"{_DIAS[dt.weekday()]} {dt.day} de {_MESES[dt.month - 1]} de {dt.year}"


def main() -> int:
    fecha = datetime.now(tz=SANTIAGO).strftime("%Y-%m-%d")
    destino = RAIZ / "data" / "informes" / f"{fecha}_cierre" / "graficos"
    datos = reunir(destino_graficos=destino)

    print(f"\nCIERRE SEMANAL · {datos['fecha_larga']}")
    print(f"{'activo':13} {'cierre 5d atras':>16} {'cierre de hoy':>15} {'semana':>9}")
    for a in datos["activos"]:
        print(f"{a['rotulo']:13} {a['previo_txt']:>16} {a['actual_txt']:>15} {a['var_txt']:>9}")
    print("\nCurva soberana:")
    for f in datos["filas_curva"]:
        print(f"  {f['nombre']:42} {f['nivel']:>8}  1d {f['d1']:>14}  5d {f['d5']:>14}  ({f['fecha']})")

    salida = destino.parent / "_datos_semanal.json"
    salida.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nDatos: {salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
