"""Bitácora de uso del bot: una línea JSON por interacción, para el panel `scripts/uso_bot.py`.

Es un registro aparte del log de errores (`data/logs/bot_telegram.log`): ese mezcla trazas de red con
pedidos y no dice quién es quién. Acá cada evento lleva el número de usuario de Telegram, y el nombre
se resuelve al armar el panel con `config/analistas_telegram.json`, no al escribir: así un cambio de
nombre o de cargo se ve en todo el historial.

Registrar nunca debe botar al bot: cualquier fallo de escritura se traga.
"""
from __future__ import annotations

import json
import re
import threading
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from analista import RAIZ

SANTIAGO = ZoneInfo("America/Santiago")
RUTA = RAIZ / "data" / "uso_bot.jsonl"
LOG_BOT = RAIZ / "data" / "logs" / "bot_telegram.log"
MAX_TEXTO = 120

_candado = threading.Lock()

# Tipos de evento. El panel agrupa por estos nombres, así que son contrato.
MENSAJE = "mensaje"      # algo que escribió una persona (clase: pedido, comando, no_entendido, no_autorizado...)
BOTON = "boton"          # el toque de un botón de un aviso
RESULTADO = "resultado"  # cómo terminó un pedido encolado (ok, fallo, error) y cuánto tardó


def registrar(tipo: str, usuario: str, *, ahora: datetime | None = None, ruta: Path | None = None, **campos: Any) -> None:
    evento = {"ts": (ahora or datetime.now(SANTIAGO)).isoformat(timespec="seconds"), "tipo": tipo, "usuario": str(usuario)}
    for k, v in campos.items():
        if v is None:
            continue
        evento[k] = v[:MAX_TEXTO] if isinstance(v, str) else v
    try:
        destino = ruta or RUTA
        destino.parent.mkdir(parents=True, exist_ok=True)
        with _candado, destino.open("a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False) + "\n")
    except Exception:  # noqa: BLE001  la bitácora es un extra: nunca bota un pedido
        pass


def leer(ruta: Path | None = None) -> list[dict]:
    destino = ruta or RUTA
    if not destino.exists():
        return []
    eventos = []
    for linea in destino.read_text(encoding="utf-8").splitlines():
        try:
            eventos.append(json.loads(linea))
        except ValueError:
            continue  # una línea cortada por un cierre brusco no tira el panel
    return eventos


_LINEA_LOG = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) (pedido|desconocido) (\d+): (.*)$")


def desde_log(ruta: Path | None = None, antes_de: str | None = None) -> list[dict]:
    """Rescata del log viejo los pedidos y los intentos de extraños, que es lo único que dejaba.

    Solo trae lo anterior a `antes_de` (la primera marca de la bitácora nueva), para no contar dos veces.
    """
    origen = ruta or LOG_BOT
    if not origen.exists():
        return []
    eventos = []
    with origen.open(encoding="utf-8", errors="replace") as f:
        for linea in f:
            m = _LINEA_LOG.match(linea)
            if not m:
                continue
            ts = datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=SANTIAGO).isoformat(timespec="seconds")
            if antes_de and ts >= antes_de:
                continue
            if m.group(2) == "desconocido":
                eventos.append({"ts": ts, "tipo": MENSAJE, "usuario": m.group(3), "clase": "no_autorizado",
                                "texto": m.group(4).strip("'\"")[:MAX_TEXTO], "origen": "log"})
                continue
            pieza, *params = m.group(4).split("|")
            args = dict(p.split("=", 1) for p in params if "=" in p)
            eventos.append({"ts": ts, "tipo": MENSAJE, "usuario": m.group(3), "clase": "pedido", "pieza": pieza,
                            "ticker": args.get("ticker"), "origen": "log"})
    return eventos


def todos(ruta: Path | None = None, log: Path | None = None) -> list[dict]:
    """La bitácora nueva más lo que el log viejo recuerda de antes de ella, en orden de hora."""
    vivos = leer(ruta)
    primera = min((e["ts"] for e in vivos), default=None)
    return sorted(desde_log(log, antes_de=primera) + vivos, key=lambda e: e["ts"])
