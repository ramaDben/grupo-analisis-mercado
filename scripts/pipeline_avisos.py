"""Carruseles de Avisos: la voz de los bancos contra nuestros datos, tres veces al día.

Spec: docs/superpowers/specs/2026-09-28-carruseles-avisos-design.md

El reparto es el mismo de `pipeline_carrusel`: el script prepara los datos y
deja los huecos en `[[ESCRIBIR]]`; el texto lo escribe el comando `/avisos`, y
`--rendir` se detiene ante un hueco, una cifra sin respaldo, una cita vieja o
datos de más de 2 horas.

La tanda se escribe con la carpeta que el despacho ya recorre
(`data/carrusel/<tanda>/01_macro_y_apertura/N_<lamina>.*`), así el único camino
al cliente sigue siendo `pipeline_carrusel.py --despachar`.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import pipeline_carrusel as pc  # noqa: E402
import pipeline_linkedin as pl  # noqa: E402

SANTIAGO = ZoneInfo("America/Santiago")
CANAL = pc.CANAL_AVISOS
MARCA = pl.MARCA_EDITORIAL
DIR_PLANTILLAS = RAIZ / "templates" / "stories"

FRESCURA_MAX_HORAS = 2
VENTANA_VISION_DIAS = 14
VENTANA_COBERTURA_DIAS = 7
MAX_LAMINAS = 9
AVISO_LEGAL = "Análisis informativo. No constituye recomendación de inversión."
FIRMA = "Grupo Inteligencia · Equipo de análisis"

# Momento del reloj -> formato. "tarde" se resuelve por día de la semana.
MOMENTOS = {"avisos_manana": "cita", "avisos_mediodia": "meta", "avisos_tarde": "tarde"}

# clave -> (_plantilla, nombre que ve el cliente en el pie de posición)
LAMINAS = {
    "portada": ("avisos_portada", "Portada"),
    "voz": ("vision", "La voz del banco"),
    "datos": ("avisos_datos", "Nuestros datos"),
    "semana": ("avisos_agenda", "La semana"),
    "lectura": ("avisos_lectura", "Nuestra lectura"),
}

SECUENCIAS = {
    "cita": ("portada", "voz", "datos", "lectura"),
    "meta": ("portada", "voz", "datos", "lectura"),
    "balance": ("portada", "voz", "datos", "lectura"),
    "agenda": ("portada", "semana", "lectura"),
}

# _plantilla -> archivo en templates/stories/. La lámina de datos se llama
# `avisos_datos` y no `alerta`: el refresco temático reescribe el mensaje con
# `construir_mensaje_alerta` y borraría el pie de posición.
PLANTILLAS = {
    "avisos_portada": "avisos_portada.html",
    "vision": "vision.html",
    "avisos_datos": "alerta.html",
    "avisos_agenda": "calendario.html",
    "avisos_lectura": "avisos_lectura.html",
}

_DIAS = ("LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO")
_MESES = ("ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC")


# ---------------------------------------------------------------- calendario


def es_dia_habil(fecha: date) -> bool:
    """Lunes a viernes y hábil en la bolsa de Nueva York (el calendario del escáner)."""
    from market_data_mcp.tools.symbol_spec import _cargar_feriados

    if fecha.weekday() >= 5:
        return False
    return fecha.isoformat() not in _cargar_feriados().get("NYSE", [])


def formato_del_momento(momento: str, fecha: date) -> str:
    if momento not in MOMENTOS:
        raise SystemExit(f"Momento desconocido: {momento}. Opciones: {', '.join(MOMENTOS)}")
    formato = MOMENTOS[momento]
    if formato == "tarde":
        return "agenda" if fecha.weekday() == 0 else "balance"
    return formato


def laminas_de(formato: str, con_voz: bool) -> list[dict[str, str]]:
    """Las láminas del carrusel en orden, con su archivo y su pie de posición.

    El pie es obligatorio en toda lámina: si un envío se corta y se retoma, las
    que faltan pueden llegar separadas de las primeras y el pie le conserva el
    orden al lector.
    """
    claves = [c for c in SECUENCIAS[formato] if con_voz or c != "voz"]
    if len(claves) > MAX_LAMINAS:
        raise ValueError(
            f"{len(claves)} láminas: el despacho ordena como texto y desde 10 la `10_` "
            f"saldría antes que la `2_`. Máximo {MAX_LAMINAS}."
        )
    total = len(claves)
    return [
        {
            "clave": c,
            "stem": f"{i}_{c}",
            "plantilla": LAMINAS[c][0],
            "posicion": f"{i}/{total} · {LAMINAS[c][1]}",
        }
        for i, c in enumerate(claves, 1)
    ]


def etiqueta_hora(ahora: datetime) -> str:
    """HH:MM con CLT o CLST, del horario que de verdad rige ese instante."""
    local = ahora.astimezone(SANTIAGO)
    return f"{local:%H:%M} {'CLST' if local.dst() else 'CLT'}"


def fecha_hora(ahora: datetime) -> str:
    local = ahora.astimezone(SANTIAGO)
    return f"{_DIAS[local.weekday()]} {local.day} {_MESES[local.month - 1]} · {etiqueta_hora(local)}"
