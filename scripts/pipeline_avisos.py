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


# ---------------------------------------------------------------- elección


class SinCandidatosError(RuntimeError):
    """Ningún activo disponible para el momento: no hay carrusel que preparar."""


def variante_de(vision: dict[str, Any]) -> str:
    """Una paráfrasis con cifra de proyección es una meta; lo demás, una cita."""
    if vision.get("tipo") == "parafrasis" and pl._PRECIO.search(str(vision.get("cita", ""))):
        return "meta"
    return "cita"


def _edad_dias(entrada: dict[str, Any], hoy: date) -> int | None:
    try:
        return (hoy - date.fromisoformat(str(entrada.get("fecha")))).days
    except ValueError:
        return None


def _entradas(historial: list[dict[str, Any]], tipo: str) -> list[dict[str, Any]]:
    return [e for e in historial if e.get("tipo") == tipo and e.get("canal") == CANAL]


def vision_califica(vision: dict[str, Any], variante: str, hoy: date,
                    historial: list[dict[str, Any]]) -> bool:
    if variante_de(vision) != variante:
        return False
    if variante == "meta":
        meta = str(vision.get("meta", "")).strip()
        if not str(vision.get("horizonte", "")).strip() or not meta:
            return False
        if meta not in str(vision.get("cita", "")):
            return False  # la lámina mostraría una meta que la cita no respalda
    if pl.validar_vision(vision, hoy, None):
        return False
    for e in _entradas(historial, "vision"):
        edad = _edad_dias(e, hoy)
        if e.get("clave") == vision.get("id") and edad is not None and edad < VENTANA_VISION_DIAS:
            return False
    return True


def coberturas(historial: list[dict[str, Any]], hoy: date, dias: int) -> dict[str, int]:
    cuenta: dict[str, int] = {}
    for e in _entradas(historial, "avisos"):
        edad = _edad_dias(e, hoy)
        if edad is not None and 0 <= edad < dias:
            cuenta[e["clave"]] = cuenta.get(e["clave"], 0) + 1
    return cuenta


def cubiertos_hoy(historial: list[dict[str, Any]], hoy: date) -> set[str]:
    return {e["clave"] for e in _entradas(historial, "avisos") if e.get("fecha") == hoy.isoformat()}


def candidatos(hoy: date, historial: list[dict[str, Any]], universo: list[str] | None = None) -> list[str]:
    import screener_gi as sc

    if universo is None:
        from pipeline_informe import ACTIVOS_INFORME

        universo = list(dict.fromkeys([*ACTIVOS_INFORME, *sc.cobertura_fija()]))
    hechos = cubiertos_hoy(historial, hoy)
    return [t for t in universo if t not in hechos and sc.gate_feriado(t, hoy) is None]


def elegir(variante: str, hoy: date, visiones: dict[str, dict[str, Any]],
           historial: list[dict[str, Any]], universo: list[str] | None = None) -> tuple[str, str | None]:
    """El activo del carrusel y su visión (o `None`, que es `_falta_vision`).

    No usa el `Score_GI`: el score mide espacio para operar en el día, y lo que
    hace valer un carrusel de Avisos es que haya una voz de banco que contrastar.
    """
    cands = candidatos(hoy, historial, universo)
    if not cands:
        raise SinCandidatosError("Avisos ya cubrió hoy todos los activos disponibles.")
    cobertura = coberturas(historial, hoy, VENTANA_COBERTURA_DIAS)
    mejor: dict[str, dict[str, Any]] = {}
    for v in visiones.values():
        t = v.get("activo")
        if t in cands and vision_califica(v, variante, hoy, historial):
            actual = mejor.get(t)
            if actual is None or (v["fecha"], v["id"]) > (actual["fecha"], actual["id"]):
                mejor[t] = v

    def orden(t: str) -> tuple[int, str]:
        return (cobertura.get(t, 0), t)

    if mejor:
        t = min(mejor, key=orden)
        return t, mejor[t]["id"]
    return min(cands, key=orden), None


def activo_del_balance(historial: list[dict[str, Any]], hoy: date) -> tuple[str | None, str | None]:
    """El activo y la visión de la mañana; si no hubo, los del mediodía."""
    usos = [e for e in _entradas(historial, "avisos") if e.get("fecha") == hoy.isoformat()]
    for momento in ("avisos_manana", "avisos_mediodia"):
        for e in reversed(usos):
            if e.get("momento") == momento:
                return e["clave"], e.get("vision")
    return None, None


def _ruta_historial(ruta: Path | None) -> Path:
    from suplemento_canal import HISTORIAL

    return ruta or HISTORIAL


def cargar_historial(ruta: Path | None = None) -> list[dict[str, Any]]:
    from suplemento_canal import cargar_historial as _cargar

    return _cargar(_ruta_historial(ruta))


def registrar_uso(hoy: date, momento: str, activo: str | None, vision_id: str | None,
                  gastar_vision: bool, ruta: Path | None = None) -> None:
    """Se anota al PREPARAR: una tanda descartada gasta la ventana, hacia el lado seguro."""
    destino = _ruta_historial(ruta)
    historial = cargar_historial(destino)
    if vision_id and gastar_vision:
        historial.append({"fecha": hoy.isoformat(), "canal": CANAL, "tipo": "vision", "clave": vision_id})
    if activo:
        historial.append({"fecha": hoy.isoformat(), "canal": CANAL, "tipo": "avisos",
                          "clave": activo, "momento": momento, "vision": vision_id})
    destino.write_text(json.dumps(historial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
