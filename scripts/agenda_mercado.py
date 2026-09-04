#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""La agenda de mercado: fuente única de ventanas de sesión y momentos del día.

**El problema que cierra: dos relojes.** Las ventanas de sesión vivían en una
cadena de `elif` dentro de `screener_gi.detectar_sesion`, con los minutos
escritos a mano (`8 * 60 + 30`), y los anclajes de tanda vivían en otra tabla del
mismo archivo. El reloj de sucesos que viene necesita ventanas propias, y con eso
serían tres lugares declarando el mismo hecho.

Ese es **el defecto recurrente del repo**: dos módulos que se hablan por nombre
sin que nada verifique que coinciden. A la segunda copia una queda atrás y nadie
se entera hasta que sale una pieza mal. Acá la única fuente es
`config/agenda_mercado.json`, y hay un test que falla si las ventanas vuelven al
código del escáner.

**El ancla es Nueva York y se comunica en hora real de Chile.** El desfase no se
escribe en ninguna parte: Chile y EE.UU. cambian de horario en sentido opuesto,
así que se mueve dos veces al año (hoy es +0 h y desde el 2026-09-06 pasa a
+1 h). Un offset fijo es el error de ±1 h del issue #38.

**Los momentos separan por clase de activo, y esa es la decisión de fondo.** Las
divisas, el oro y el petróleo cotizan las 24 horas y se mueven con el dato macro
de las 08:30 de Nueva York. Los índices, las acciones y los ETF **no tienen
precio** hasta que abre la bolsa a las 09:30: publicar sus niveles a las 08:30 es
publicar el cierre de ayer con fecha de hoy.
"""

from __future__ import annotations

import json
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "config" / "agenda_mercado.json"

SABADO = 5
DOMINGO = 6


@lru_cache(maxsize=1)
def _cfg() -> dict[str, Any]:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def zona_ancla() -> ZoneInfo:
    return ZoneInfo(_cfg()["zona_ancla"])


def sesiones() -> list[dict[str, Any]]:
    return list(_cfg()["sesiones"])


def tandas() -> dict[int, dict[str, Any]]:
    """Las tandas de referencia, con la clave ya como entero.

    En JSON las claves de objeto son strings; el resto del repo indexa las tandas
    por número. Convertir acá evita que cada consumidor lo recuerde.
    """
    return {int(k): dict(v) for k, v in _cfg()["tandas"].items()}


def momentos() -> list[dict[str, Any]]:
    return list(_cfg().get("momentos") or [])


def clases_sin_momento() -> list[str]:
    """Las clases que a propósito todavía no tienen momento.

    Declararlas es lo que impide que una clase se quede fuera del reloj en
    silencio. Hoy es cripto, que opera 24/7 y cuya hora natural sería el rollover
    diario: hay que medirlo antes de fijarlo.
    """
    return list(_cfg().get("clases_sin_momento") or [])


def tolerancia_minutos() -> int:
    return int(_cfg().get("tolerancia_minutos", 20))


# ─────────────────────────────────────────────────────────────────────────────
# Horas
# ─────────────────────────────────────────────────────────────────────────────
def _minutos(hhmm: str) -> int:
    h, m = (int(x) for x in str(hhmm).split(":"))
    return h * 60 + m


def _es_finde(cuando: datetime) -> bool:
    """Sábado completo, más domingo hasta que abre la semana.

    La hora de apertura semanal **se deriva** de la sesión marcada
    `abre_la_semana`. Escribirla en la entrada del fin de semana sería el segundo
    reloj que este módulo vino a eliminar.
    """
    dow = cuando.weekday()
    if dow == SABADO:
        return True
    if dow != DOMINGO:
        return False
    apertura = next(
        (_minutos(s["desde"]) for s in sesiones() if s.get("abre_la_semana")), 18 * 60
    )
    return (cuando.hour * 60 + cuando.minute) < apertura


def dentro_de(sesion: dict[str, Any], cuando: datetime) -> bool:
    """¿Esta sesión está activa a esta hora de Nueva York?

    Las sesiones son mutuamente excluyentes **por construcción**, no por el orden
    de la tabla: la del fin de semana es la única que aplica en el fin de semana,
    y las demás son las únicas que aplican fuera de él. Si el resultado dependiera
    del orden, sería un accidente esperando a que alguien reordene el JSON.
    """
    finde = _es_finde(cuando)
    if sesion.get("dias") == "finde":
        return finde
    if finde:
        return False

    ahora = cuando.hour * 60 + cuando.minute
    desde, hasta = _minutos(sesion["desde"]), _minutos(sesion["hasta"])
    if desde <= hasta:
        return desde <= ahora < hasta
    # La sesión asiática cruza la medianoche (18:00 a 02:00).
    return ahora >= desde or ahora < hasta


def sesion_en(cuando: datetime) -> dict[str, Any]:
    """La sesión activa a esa hora de Nueva York."""
    for s in sesiones():
        if dentro_de(s, cuando):
            return s
    # No debería pasar: el test de cobertura verifica que cada minuto del día
    # tenga exactamente una sesión. Si pasa, el JSON quedó con un hueco.
    raise ValueError(
        f"ninguna sesión cubre las {cuando:%H:%M} de Nueva York: "
        "config/agenda_mercado.json tiene un hueco"
    )


def momento(slug: str) -> dict[str, Any]:
    for m in momentos():
        if m["slug"] == slug:
            return m
    raise KeyError(f"no hay momento {slug!r} en la agenda")


def momento_en(
    cuando: datetime, tolerancia: int | None = None
) -> dict[str, Any] | None:
    """El momento que corresponde a esta hora, o `None` si no hay ninguno.

    Hay tolerancia porque el reloj no dispara al segundo exacto: el disparo del
    sistema operativo, la lectura de precios y el render se llevan minutos. Sin
    ventana de gracia, un momento se pierde por llegar dos minutos tarde.

    La tolerancia es **solo hacia adelante**. Disparar el momento de las 08:30 a
    las 08:15 publicaría niveles anteriores al dato que motiva la hora.
    """
    margen = tolerancia if tolerancia is not None else tolerancia_minutos()
    ahora = cuando.hour * 60 + cuando.minute
    for m in momentos():
        inicio = _minutos(m["hora"])
        if inicio <= ahora <= inicio + margen:
            return m
    return None


def clases_del_momento(cuando: datetime) -> list[str]:
    """Las clases de activo que le toca publicar a esta hora.

    Lista vacía significa que no es hora de nadie, y es la respuesta normal la
    mayor parte del día.
    """
    m = momento_en(cuando)
    return list(m["clases"]) if m else []
