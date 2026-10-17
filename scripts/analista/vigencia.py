"""Caducidad anticipada: un análisis vigente deja de valer si la lectura se rompió.

Con vigencia fija de 7 días, un análisis del lunes cuya invalidación se rompió el martes seguiría
circulando el jueves (spec 2026-10-16 §2). Al reutilizarlo, Python vuelve a seguir su referencia
contra el mercado de hoy: si cambió la estructura, el precio tocó la invalidación o alcanzó el
objetivo, caduca y se rehace aunque no hayan pasado los 7 días.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from estrategia.contrato import Lectura, lectura_de_dict


def motivo_caducidad(referencia: Lectura, actual: Lectura, velas: Any) -> str | None:
    """Por qué el análisis ya no vale, o None. `velas` son las del marco operativo, con `time/high/low`."""
    import referencia_semanal as rs

    if rs.debe_reemplazar(referencia, actual):
        return "la estructura de la lectura cambió: una línea se rompió por cierre"
    desde = velas[velas["time"] > referencia.vela] if len(velas) else velas
    altos = [actual.precio] + ([float(desde["high"].max())] if len(desde) else [])
    bajos = [actual.precio] + ([float(desde["low"].min())] if len(desde) else [])
    inv, obj = referencia.invalidacion, referencia.objetivo
    if referencia.direccion == "ALCISTA":
        if inv and min(bajos) <= inv.precio:
            return "el precio tocó la invalidación"
        if obj and max(altos) >= obj.precio:
            return "el precio alcanzó el objetivo técnico"
    elif referencia.direccion == "BAJISTA":
        if inv and max(altos) >= inv.precio:
            return "el precio tocó la invalidación"
        if obj and min(bajos) <= obj.precio:
            return "el precio alcanzó el objetivo técnico"
    return None


def verificar(pieza: dict[str, Any], ahora: datetime, lectores=None) -> tuple[str | None, str | None]:
    """(motivo de caducidad, aviso). Con el terminal caído no se rehace: se entrega con el aviso."""
    from analista import preparar as pr

    lec = lectores or pr.Lectores()
    a = pieza["datos"]["activos"][0]
    referencia = lectura_de_dict(a["lectura"])
    try:
        actual, velas = lec.lectura_actual(lec.estrategia(), a["ticker"], a["digits"], lec.velas, ahora,
                                           referencia=referencia)
        return motivo_caducidad(referencia, actual, velas[referencia.marco]), None
    except Exception:  # noqa: BLE001  el terminal es un extra de esta verificación
        return None, "No pude verificar si sigue vigente (el terminal no respondió): te lo entrego tal cual."
