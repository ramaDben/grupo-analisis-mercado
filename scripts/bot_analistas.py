"""Bot de Telegram para analistas y ejecutivos: piezas a pedido en PDF.

Uso:
    uv run --with MetaTrader5 --extra stories --extra informe python scripts/bot_analistas.py --escuchar
    uv run python scripts/bot_analistas.py --probar-token
    uv run --with MetaTrader5 --extra stories --extra informe python scripts/bot_analistas.py \\
        --una "/activo oro" --usuario <id>                     # un pedido, sin Telegram
    uv run python scripts/bot_analistas.py --validar data/informes_analistas/.../pieza.json
    uv run --with MetaTrader5 python scripts/bot_analistas.py --desenlaces   # completa la bitácora de planes

Diseño y reglas: docs/bot-analistas.md y la spec
docs/superpowers/specs/2026-10-08-bot-telegram-analistas-design.md.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analista import RAIZ  # noqa: E402


def leer_token() -> str | None:
    """De la variable de entorno o del `.env`, sin depender de python-dotenv."""
    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        return os.environ["TELEGRAM_BOT_TOKEN"].strip()
    env = RAIZ / ".env"
    if env.exists():
        for linea in env.read_text(encoding="utf-8").splitlines():
            clave, _, valor = linea.partition("=")
            if clave.strip() == "TELEGRAM_BOT_TOKEN":
                return valor.strip().strip("'\"") or None
    return None


def validar(ruta: Path) -> int:
    from analista import esquema as es
    from analista.preparar import cargar_pieza

    errores = es.errores(cargar_pieza(ruta.parent))
    if errores:
        for e in errores:
            print(f"ERROR: {e}")
        return 1
    print("OK")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modo = ap.add_mutually_exclusive_group(required=True)
    modo.add_argument("--escuchar", action="store_true", help="atiende Telegram de forma continua")
    modo.add_argument("--probar-token", action="store_true", help="verifica el token contra Telegram")
    modo.add_argument("--una", metavar="PEDIDO", help="atiende un pedido sin Telegram e imprime el resultado")
    modo.add_argument("--validar", type=Path, metavar="PIEZA_JSON", help="valida una pieza redactada")
    modo.add_argument("--desenlaces", action="store_true",
                      help="completa el desenlace de los planes de más de 24 h en la bitácora")
    ap.add_argument("--usuario", help="con --una: id del analista en config/analistas_telegram.json")
    args = ap.parse_args(argv)

    if args.validar:
        return validar(args.validar)

    if args.desenlaces:
        from datetime import datetime
        from zoneinfo import ZoneInfo

        from analista import bitacora as bt
        from analista.preparar import _serie_h1

        n = bt.completar(_serie_h1, datetime.now(ZoneInfo("America/Santiago")))
        print(f"OK: {n} plan(es) con desenlace nuevo en {bt.RUTA.relative_to(RAIZ)}")
        return 0

    from analista import autor as au
    from analista import bot

    def autor_o_nada(config):
        try:
            return au.cargar(config, RAIZ)
        except au.AutorInvalido as exc:
            print(f"ERROR: {exc}")
            return None

    if args.una:
        from analista import orden as od

        config = bot.cargar_config()
        usuario = args.usuario or next(iter(config["analistas"]), None)
        if usuario not in config["analistas"]:
            print("ERROR: --usuario no está en config/analistas_telegram.json")
            return 2
        try:
            orden = od.interpretar(args.una)
        except od.PedidoInvalido as exc:
            # Desde Git Bash, "/activo" llega convertido en una ruta de Windows:
            # hay que correrlo con MSYS_NO_PATHCONV=1.
            print(f"ERROR: {exc} (recibí {args.una!r})")
            return 2
        autor = autor_o_nada(config)
        if autor is None:
            return 2
        atendedor = bot.Atendedor(config, bot.Estado.cargar(), autor)
        respuesta = bot.Bot(tg=None, atendedor=atendedor).procesar_uno(bot.Pedido(usuario, 0, orden))
        print(respuesta.texto)
        for ruta in respuesta.archivos:
            print(f"  → {ruta}")
        return 0 if respuesta.archivos else 1

    token = leer_token()
    if not token:
        print("ERROR: falta TELEGRAM_BOT_TOKEN en el entorno o en .env")
        return 2
    tg = bot.Telegram(token)
    if args.probar_token:
        try:
            yo = tg.soy()
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: Telegram no aceptó el token ({exc})")
            return 1
        print(f"OK: @{yo.get('username')} ({yo.get('first_name')})")
        return 0

    config = bot.cargar_config()
    if not config["analistas"]:
        print("ERROR: config/analistas_telegram.json no tiene analistas autorizados")
        return 2
    autor = autor_o_nada(config)
    if autor is None:
        return 2
    print(f"Escuchando Telegram con {len(config['analistas'])} analista(s) autorizado(s). Ctrl+C para salir.")
    bot.Bot(tg, bot.Atendedor(config, bot.Estado.cargar(), autor)).escuchar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
