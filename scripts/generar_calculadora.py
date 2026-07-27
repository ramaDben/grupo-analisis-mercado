"""Genera la calculadora de lotaje pública a partir de datos reales del broker.

Pipeline determinista, sin IA: lee el catálogo de activos, consulta MT5 (precio,
valor del movimiento con `order_calc_profit`, ATR diario y margen), y escribe un
HTML autocontenido a partir de `tools/calculadora/plantilla.html`.

Por qué `order_calc_profit` y no `trade_tick_value`: el tick_value del broker está
mal configurado para los CFDs de acciones (reporta 1.0 CLP por centavo cuando el
valor real con contrato de 50 acciones es ~471 CLP). `order_calc_profit` le pide el
cálculo al terminal, que aplica contrato, moneda del instrumento y conversión.

Uso:
    uv run --with MetaTrader5 python scripts/generar_calculadora.py --out ruta/index.html

Códigos de salida:
    0  HTML escrito
    1  MT5 no disponible o sin datos suficientes -> NO se escribe nada (así una
       tarea programada no publica una página a medias)
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

REPO = Path(__file__).resolve().parent.parent
CATALOGO = REPO / "config" / "activos.json"
PLANTILLA = REPO / "tools" / "calculadora" / "plantilla.html"
FUENTES = REPO / "templates" / "stories" / "fonts"

# Nombres de presentación para los activos complementarios, que en el catálogo
# figuran solo por su clave (COBRE/DXY/GER40) y sin campo `nombre`.
NOMBRES_COMPLEMENTARIOS = {
    "COBRE": "Cobre",
    "DXY": "Índice del dólar",
    "GER40": "DAX 40 (Alemania)",
}

FUENTES_PLANTILLA = {
    "__F_SYNE__": "syne-800.woff2",
    "__F_DM400__": "dm-sans-400.woff2",
    "__F_DM700__": "dm-sans-700.woff2",
    "__F_SG600__": "space-grotesk-600.woff2",
}


def ahora_chile() -> datetime:
    """Hora de Chile (CLT/CLST, con horario de verano automático)."""
    return datetime.now(ZoneInfo("America/Santiago"))


def tickers_del_catalogo() -> list[tuple[str, str]]:
    """Lista [(ticker_mt5, nombre legible)] en el orden en que se mostrará."""
    catalogo = json.loads(CATALOGO.read_text(encoding="utf-8"))
    salida: list[tuple[str, str]] = []

    for activo in catalogo["forex_commodities"] + catalogo["indices"]:
        salida.append((activo["ticker_mt5"], activo["nombre"]))
    for clave, meta in catalogo["activos_complementarios"].items():
        salida.append((meta["ticker_mt5"], NOMBRES_COMPLEMENTARIOS.get(clave, clave)))
    for sector in catalogo["acciones"].values():
        for componente in sector["componentes"]:
            salida.append((componente["ticker_mt5"], componente["nombre"]))

    return salida


def atr_diario(mt5, ticker: str, periodo: int = 14) -> float | None:
    """ATR de Wilder simplificado (media de los últimos `periodo` rangos verdaderos)."""
    velas = mt5.copy_rates_from_pos(ticker, mt5.TIMEFRAME_D1, 0, periodo * 2 + 2)
    if velas is None or len(velas) < periodo + 1:
        return None
    rangos = []
    for i in range(1, len(velas)):
        alto, bajo = velas[i]["high"], velas[i]["low"]
        cierre_previo = velas[i - 1]["close"]
        rangos.append(max(alto - bajo, abs(alto - cierre_previo), abs(bajo - cierre_previo)))
    return sum(rangos[-periodo:]) / periodo


def recolectar() -> tuple[list[dict], float, str]:
    """Devuelve (activos, usdclp, moneda_cuenta). Lanza RuntimeError si MT5 no responde."""
    import MetaTrader5 as mt5

    if not mt5.initialize():
        raise RuntimeError(f"MT5 no responde: {mt5.last_error()}")

    try:
        cuenta = mt5.account_info()
        if cuenta is None:
            raise RuntimeError("MT5 no reporta cuenta conectada")
        if cuenta.currency != "CLP":
            raise RuntimeError(
                f"La cuenta está en {cuenta.currency}, no en CLP. La calculadora asume que "
                "los valores que devuelve MT5 ya vienen en pesos."
            )

        clp = mt5.symbol_info("USDCLP")
        if clp is None or not clp.bid:
            raise RuntimeError("No se pudo leer USDCLP para el tipo de cambio")
        usdclp = (clp.bid + clp.ask) / 2

        activos: list[dict] = []
        omitidos: list[str] = []

        for ticker, nombre in tickers_del_catalogo():
            info = mt5.symbol_info(ticker)
            if info is None:
                omitidos.append(f"{ticker} (no existe)")
                continue
            if not info.visible:
                mt5.symbol_select(ticker, True)
                info = mt5.symbol_info(ticker)

            precio = info.bid or info.ask
            if not precio:
                omitidos.append(f"{ticker} (sin precio)")
                continue

            clp_punto = mt5.order_calc_profit(
                mt5.ORDER_TYPE_BUY, ticker, 1.0, precio, precio + info.point
            )
            margen = mt5.order_calc_margin(mt5.ORDER_TYPE_BUY, ticker, 1.0, precio)
            atr = atr_diario(mt5, ticker)

            if clp_punto is None or margen is None or atr is None:
                omitidos.append(f"{ticker} (cálculo incompleto)")
                continue

            activos.append({
                "tk": ticker.lstrip("#").replace(".spot", ""),
                "nom": nombre,
                "dig": info.digits,
                "point": info.point,
                "precio": round(precio, info.digits),
                "clpPunto": round(clp_punto, 2),
                "atr": round(atr, info.digits),
                "margen": round(margen),
                "volMin": info.volume_min,
                "volStep": info.volume_step,
            })

        if omitidos:
            print(f"AVISO: omitidos {len(omitidos)}: {', '.join(omitidos)}", file=sys.stderr)
        if len(activos) < 5:
            raise RuntimeError(f"Solo {len(activos)} activos con datos completos; no se publica")

        return activos, usdclp, cuenta.currency
    finally:
        mt5.shutdown()


def construir_html(activos: list[dict], usdclp: float, sello: str, sello_iso: str) -> str:
    """Sustituye los marcadores de la plantilla; falla si queda alguno sin resolver."""
    html = PLANTILLA.read_text(encoding="utf-8")

    for marcador, archivo in FUENTES_PLANTILLA.items():
        # Una sola ocurrencia por marcador: si la plantilla lo repite (por ejemplo en un
        # comentario de documentación), la fuente se embebería dos veces y el HTML pesaría
        # el doble. El conteo es la guardia contra esa regresión.
        repeticiones = html.count(marcador)
        if repeticiones != 1:
            raise RuntimeError(
                f"{marcador} aparece {repeticiones} veces en la plantilla; debe aparecer 1"
            )
        b64 = base64.b64encode((FUENTES / archivo).read_bytes()).decode("ascii")
        html = html.replace(marcador, f"data:font/woff2;base64,{b64}")

    datos_js = json.dumps(activos, ensure_ascii=False, indent=2)
    html = html.replace("__DATOS__", datos_js)
    html = html.replace("__USDCLP__", "$" + f"{usdclp:,.2f}".replace(",", "."))
    # __SELLO_ISO__ antes que __SELLO__: el segundo es prefijo del primero y lo rompería.
    html = html.replace("__SELLO_ISO__", sello_iso)
    html = html.replace("__SELLO__", sello)

    pendientes = [m for m in ("__DATOS__", "__USDCLP__", "__SELLO__", "__F_") if m in html]
    if pendientes:
        raise RuntimeError(f"Quedaron marcadores sin resolver: {pendientes}")

    return html


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Genera la calculadora de lotaje pública")
    parser.add_argument("--out", required=True, type=Path, help="ruta del HTML de salida")
    args = parser.parse_args(argv)

    try:
        activos, usdclp, moneda = recolectar()
    except Exception as exc:  # noqa: BLE001 — cualquier fallo debe evitar la publicación
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    momento = ahora_chile()
    sello = momento.strftime("%d-%m-%Y %H:%M") + " hora de Chile"

    try:
        html = construir_html(activos, usdclp, sello, momento.isoformat(timespec="seconds"))
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8")

    print(f"OK {args.out} · {len(activos)} activos · USD/CLP {usdclp:.2f} · "
          f"moneda {moneda} · {sello} · {len(html) / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
