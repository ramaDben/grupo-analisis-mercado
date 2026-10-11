"""La referencia semanal: lo que fijó el análisis del lunes, por activo (spec §4).

Guardarla y reemplazarla es infraestructura; la estrategia solo la lee con `seguir()`.
Es historia de lo que el cliente leyó, así que se versiona igual que
`data/historial_despachos.json`.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from estrategia.contrato import SCL, Lectura, lectura_a_dict, lectura_de_dict

RAIZ = Path(__file__).resolve().parent.parent
DIR = RAIZ / "data" / "referencias_semanales"
MANIFIESTO = "_semana.json"


def semana_de(momento: datetime) -> str:
    """La semana ISO de la fecha de Santiago: el lunes del cliente, no el de UTC."""
    año, semana, _ = momento.astimezone(SCL).date().isocalendar()
    return f"{año}-W{semana:02d}"


def slug(ticker: str) -> str:
    return ticker.lower().replace(".spot", "").replace("#", "").replace("/", "")


def ruta(semana: str, ticker: str, base: Path = DIR) -> Path:
    return base / semana / f"{slug(ticker)}.json"


def guardar(lectura: Lectura, semana: str, motivo: str, ahora: datetime, base: Path = DIR) -> Path:
    if lectura.estado == "PRUEBA":
        raise ValueError(f"{lectura.ticker}: una referencia no se guarda en PRUEBA; se lee con en_curso=None")
    destino = ruta(semana, lectura.ticker, base)
    destino.parent.mkdir(parents=True, exist_ok=True)
    datos = {"ticker": lectura.ticker, "semana": semana, "motivo": motivo,
             "guardada": ahora.astimezone(SCL).isoformat(timespec="minutes"),
             "lectura": lectura_a_dict(lectura)}
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def cargar(semana: str, ticker: str, base: Path = DIR) -> Lectura | None:
    origen = ruta(semana, ticker, base)
    if not origen.exists():
        return None
    return lectura_de_dict(json.loads(origen.read_text(encoding="utf-8"))["lectura"])


def manifiesto(semana: str, base: Path = DIR) -> dict[str, Any] | None:
    origen = base / semana / MANIFIESTO
    return json.loads(origen.read_text(encoding="utf-8")) if origen.exists() else None


def guardar_manifiesto(semana: str, datos: dict[str, Any], base: Path = DIR) -> Path:
    destino = base / semana / MANIFIESTO
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def firma(lectura: Lectura) -> tuple:
    """La estructura de la lectura: qué línea cumple qué papel y dónde está anclada."""
    return tuple(sorted((x.rol, x.tipo, x.marco, x.puntos) for x in lectura.lineas))


def debe_reemplazar(referencia: Lectura, actual: Lectura) -> bool:
    """La tesis del lunes terminó: una línea se rompió por cierre o la estrategia volvió a trazar.

    No lee los avisos ni las métricas de la estrategia: compara la estructura, que es
    parte del contrato. Entre TENDENCIA, REBOTE y PRUEBA la estructura no cambia.
    """
    if firma(referencia) != firma(actual):
        return True
    return actual.estado == "RUPTURA" and referencia.estado != "RUPTURA"
