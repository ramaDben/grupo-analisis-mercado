"""Arma el mensaje con las operaciones abiertas del director para el grupo de colegas.

Lee el terminal MT5 (posiciones y equity), no calcula precios a mano. Solo ARMA el
texto: el envío lo hace `enviar_whatsapp.py`, después de que el director lo apruebe.

    uv run --with MetaTrader5 python scripts/compartir_trades.py --listar
    uv run --with MetaTrader5 python scripts/compartir_trades.py --armar 1,3 -o msg.txt
    uv run --with MetaTrader5 python scripts/compartir_trades.py --armar todas -o msg.txt

El riesgo es lo que se pierde si toca el stop, medido con `order_calc_profit` (en la
moneda de la cuenta) y expresado como % del equity.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))


def numero(valor: float, decimales: int) -> str:
    """Notación chilena: punto de miles y coma decimal. Con 0 decimales va entero."""
    if decimales == 0:
        return f"{valor:.0f}"
    return f"{valor:,.{decimales}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def monto(valor: float) -> str:
    """Pesos enteros con separador de miles (1.234.567). `numero` con 0 decimales no lo lleva."""
    return f"{valor:,.0f}".replace(",", ".")


def con_signo(valor: float) -> str:
    return ("+" if valor >= 0 else "-") + monto(abs(valor))


def nombres_del_catalogo() -> dict[str, str]:
    """Ticker del broker -> nombre en español de `config/activos.json`."""
    import json

    datos = json.loads((BASE_DIR / "config" / "activos.json").read_text(encoding="utf-8"))
    nombres: dict[str, str] = {}
    for valor in datos.values():
        if isinstance(valor, list):
            for a in valor:
                if isinstance(a, dict) and a.get("ticker_mt5") and a.get("nombre"):
                    nombres[a["ticker_mt5"]] = a["nombre"]
    return nombres


def leer_terminal() -> tuple[object, list[dict]]:
    """Cuenta y posiciones abiertas, con riesgo y recompensa medidos por el terminal."""
    import MetaTrader5 as mt5  # noqa: PLC0415

    from market_data_mcp import mt5_client

    mt5_client.connect()
    cuenta = mt5.account_info()
    if cuenta is None:
        raise SystemExit("MT5 no reporta la cuenta. ¿Está abierto el terminal?")
    posiciones = mt5.positions_get()
    if posiciones is None:
        raise SystemExit("MT5 no pudo responder las posiciones abiertas.")

    catalogo = nombres_del_catalogo()
    filas = []
    for p in sorted(posiciones, key=lambda x: x.ticket):
        info = mt5.symbol_info(p.symbol)
        es_compra = p.type == mt5.POSITION_TYPE_BUY
        accion = mt5.ORDER_TYPE_BUY if es_compra else mt5.ORDER_TYPE_SELL

        def _calc(precio_final: float) -> float | None:
            if not precio_final:
                return None
            return mt5.order_calc_profit(accion, p.symbol, p.volume, p.price_open, precio_final)

        riesgo = _calc(p.sl)
        filas.append({
            "ticket": p.ticket,
            "simbolo": p.symbol,
            "nombre": catalogo.get(p.symbol) or (info.description if info else p.symbol),
            "digits": info.digits if info else 2,
            "compra": es_compra,
            "volumen": p.volume,
            "entrada": p.price_open,
            "sl": p.sl,
            "tp": p.tp,
            "actual": p.price_current,
            "flotante": p.profit + p.swap,
            "riesgo": abs(riesgo) if riesgo is not None else None,
            "recompensa": _calc(p.tp),
        })
    return cuenta, filas


def bloque(f: dict, equity: float, con_flotante: bool) -> list[str]:
    d = f["digits"]
    flecha, lado = ("⬆️", "Compra (BUY)") if f["compra"] else ("⬇️", "Venta (SELL)")
    lineas = [
        f"{flecha} *{f['nombre']}* · {f['simbolo']} · {lado}",
        f"Volumen: {numero(f['volumen'], 2)} lotes",
        f"Entrada: {numero(f['entrada'], d)}",
        f"⚠️ Stop loss: {numero(f['sl'], d)}" if f["sl"] else "⚠️ Sin stop loss",
        f"🎯 Take profit: {numero(f['tp'], d)}" if f["tp"] else "🎯 Sin take profit",
        f"Precio ahora: {numero(f['actual'], d)}",
    ]
    if f["riesgo"] is not None:
        pct = f["riesgo"] / equity * 100
        lineas.append(f"Riesgo si toca el stop: {numero(pct, 2)} % del capital ({monto(f['riesgo'])} CLP)")
    if f["recompensa"] is not None:
        lineas.append(f"Si llega al take profit: {con_signo(f['recompensa'])} CLP")
    if con_flotante:
        lineas.append(f"Resultado ahora: {con_signo(f['flotante'])} CLP")
    return lineas


def armar_mensaje(cuenta, filas: list[dict], con_flotante: bool) -> str:
    ahora = datetime.now(ZoneInfo("America/Santiago"))
    sep = "━━━━━━━━━━━━━━━━━━━"
    titulo = "Trade abierto" if len(filas) == 1 else "Trades abiertos"
    salida = [f"📌 *{titulo}* · {ahora:%d-%m-%Y %H:%M} hrs", sep,
              f"Capital de referencia: *{monto(cuenta.equity)} {cuenta.currency}*", sep]
    for i, f in enumerate(filas):
        if i:
            salida.append(sep)
        salida.extend(bloque(f, cuenta.equity, con_flotante))
    return "\n".join(salida) + "\n"


def enviar_telegram(texto: str, destino: str) -> None:
    """Manda el mensaje por el bot de analistas (solo `sendMessage`, no compite con `getUpdates`).

    `destino`: un `chat_id` (los grupos son negativos) o `yo`, el chat privado del primer admin.
    """
    import json

    import requests

    from bot_analistas import leer_token

    token = leer_token()
    if not token:
        raise SystemExit("Falta TELEGRAM_BOT_TOKEN en el entorno o en .env")
    if destino == "yo":
        config = json.loads((BASE_DIR / "config" / "analistas_telegram.json").read_text(encoding="utf-8"))
        destino = config["admins"][0]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, json={"chat_id": destino, "text": texto, "parse_mode": "Markdown"}, timeout=30)
    if not r.ok:  # un carácter que Markdown no entiende no puede impedir que salga la señal
        r = requests.post(url, json={"chat_id": destino, "text": texto}, timeout=30)
    if not r.ok:
        raise SystemExit(f"Telegram rechazó el envío: {r.status_code} {r.json().get('description', '')}")
    print(f"Enviado por Telegram al chat {destino}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--listar", action="store_true", help="Muestra las operaciones abiertas, numeradas.")
    ap.add_argument("--armar", metavar="N,N|todas", help="Cuáles compartir: números del listado o 'todas'.")
    ap.add_argument("-o", "--salida", type=Path, help="Archivo UTF-8 donde dejar el mensaje.")
    ap.add_argument("--telegram", metavar="CHAT_ID|yo",
                    help="Envía el mensaje armado por Telegram: un chat_id de grupo, o 'yo' (privado del director).")
    ap.add_argument("--sin-flotante", action="store_true", help="No muestra el resultado actual.")
    args = ap.parse_args()
    if not (args.listar or args.armar):
        ap.error("indica --listar o --armar")

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    cuenta, filas = leer_terminal()
    if not filas:
        print("No hay operaciones abiertas en el terminal.")
        return 0

    if args.listar:
        print(f"Cuenta {cuenta.login} · equity {monto(cuenta.equity)} {cuenta.currency}")
        for n, f in enumerate(filas, 1):
            riesgo = f"{numero(f['riesgo'] / cuenta.equity * 100, 2)} %" if f["riesgo"] is not None else "sin stop"
            print(f"{n}. {f['simbolo']} {'BUY' if f['compra'] else 'SELL'} {numero(f['volumen'], 2)} lotes "
                  f"· entrada {numero(f['entrada'], f['digits'])} · riesgo {riesgo} "
                  f"· resultado {con_signo(f['flotante'])} CLP")

    if args.armar:
        if args.armar.strip().lower() == "todas":
            elegidas = filas
        else:
            try:
                idx = [int(x) for x in args.armar.split(",")]
            except ValueError:
                raise SystemExit("--armar espera números separados por coma o 'todas'.")
            if any(i < 1 or i > len(filas) for i in idx):
                raise SystemExit(f"Los números válidos son del 1 al {len(filas)}.")
            elegidas = [filas[i - 1] for i in idx]
        texto = armar_mensaje(cuenta, elegidas, not args.sin_flotante)
        if args.salida:
            args.salida.write_text(texto, encoding="utf-8")
            print(f"Mensaje guardado en {args.salida}")
        print(texto)
        if args.telegram:
            enviar_telegram(texto, args.telegram)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
