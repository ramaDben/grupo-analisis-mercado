"""Control de paridad entre las líneas del radar y los objetos dibujados por el indicador en MT5.

Spec §7 y brief de Task 4. Compara el `valor_actual` del indicador en la vela en curso
con `LineaRadar.valor_abierta` del motor Tori para seguridad, acción, soporte y resistencia.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

_RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(_RAIZ / "src"), str(_RAIZ / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from estrategia.tori.parametros import Parametros
from estrategia.tori.radar import LecturaMarco
from market_data_mcp import mt5_client

SANTIAGO = ZoneInfo("America/Santiago")

# Nombres de objeto en MT5 -> rol en el radar
NOMBRES_INDICADOR: dict[str, str] = {
    "GI_TV_DIAG_SEGURIDAD": "seguridad",
    "GI_TV_DIAG_ACCION": "accion",
    "GI_TV_LINE_SOPORTE": "soporte",
    "GI_TV_LINE_RESISTENCIA": "resistencia",
}

ROLES_PARIDAD: tuple[str, ...] = ("seguridad", "accion", "soporte", "resistencia")
ETIQUETA_ROL: dict[str, str] = {
    "seguridad": "seguridad",
    "accion": "acción",
    "soporte": "soporte",
    "resistencia": "resistencia",
}
_STALE_SECONDS = 3600


def ruta_objetos() -> Path | None:
    """Ruta a $MT5_COMMON_FILES/chart_objects.json; carga antes mt5_client.cargar_env()."""
    mt5_client.cargar_env()
    common_dir = os.environ.get("MT5_COMMON_FILES")
    if not common_dir:
        return None
    return Path(common_dir) / "chart_objects.json"


def _parse_generado(generated_at: str) -> datetime | None:
    """'YYYY-MM-DD HH:MM' a datetime con tz Santiago."""
    try:
        return datetime.strptime(generated_at, "%Y-%m-%d %H:%M").replace(tzinfo=SANTIAGO)
    except (ValueError, TypeError):
        return None


def leer_objetos(ruta: Path | None, ahora: datetime) -> dict | str:
    """dict con los objetos del exportador, o el motivo en texto por el que no se pudo leer."""
    if ruta is None or not ruta.exists():
        return "no se pudo verificar la paridad: falta chart_objects.json (¿corre ChartObjectsExporter?)"

    try:
        data = json.loads(ruta.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return f"no se pudo verificar la paridad: error al leer chart_objects.json ({exc})"

    generado_str = data.get("generated_at", "")
    generado = _parse_generado(generado_str)
    if generado is not None:
        ahora_tz = ahora if ahora.tzinfo is not None else ahora.replace(tzinfo=SANTIAGO)
        antiguedad = (ahora_tz - generado).total_seconds()
        if antiguedad > _STALE_SECONDS:
            minutos = int(antiguedad // 60)
            return f"no se pudo verificar la paridad: chart_objects.json tiene {minutos} min"

    return data


def comparar(
    objetos: dict,
    lecturas: dict[tuple[str, str], LecturaMarco],
    digits: dict[str, int],
    p: Parametros,
) -> list[str]:
    """Compara los objetos del indicador contra las líneas del motor.

    Por cada gráfico (symbol, timeframe) con lectura del radar y cada trendlines[].name de
    NOMBRES_INDICADOR, compara valor_actual del indicador contra LineaRadar.valor_abierta
    del mismo rol.
    """
    discrepancias: list[str] = []
    charts = objetos.get("charts", [])

    for chart in charts:
        symbol = chart.get("symbol")
        timeframe = chart.get("timeframe")
        clave = (symbol, timeframe)
        if clave not in lecturas:
            continue

        lectura = lecturas[clave]
        d = digits.get(symbol, 2)
        tol = p.tolerancia_toque_atr * lectura.atr

        # Mapear roles del indicador desde trendlines
        indicador_lineas: dict[str, float] = {}
        for tl in chart.get("trendlines", []):
            name = tl.get("name")
            if name in NOMBRES_INDICADOR and "valor_actual" in tl:
                rol = NOMBRES_INDICADOR[name]
                indicador_lineas[rol] = float(tl["valor_actual"])

        # Mapear roles del motor desde lectura.lineas (usando valor_abierta)
        motor_lineas: dict[str, float] = {}
        for linea in lectura.lineas:
            if linea.rol in ROLES_PARIDAD:
                motor_lineas[linea.rol] = float(linea.valor_abierta)

        # Comparar por cada uno de los 4 roles
        for rol in ROLES_PARIDAD:
            en_ind = rol in indicador_lineas
            en_mot = rol in motor_lineas
            nombre_rol = ETIQUETA_ROL.get(rol, rol)

            if en_ind and en_mot:
                val_ind = indicador_lineas[rol]
                val_mot = motor_lineas[rol]
                if abs(val_ind - val_mot) > tol:
                    val_ind_str = f"{val_ind:.{d}f}"
                    val_mot_str = f"{val_mot:.{d}f}"
                    discrepancias.append(
                        f"{symbol} {timeframe}: indicador y motor difieren en la línea de {nombre_rol}: {val_ind_str} vs {val_mot_str}"
                    )
            elif en_ind and not en_mot:
                discrepancias.append(
                    f"{symbol} {timeframe}: la línea de {nombre_rol} solo está en el indicador"
                )
            elif en_mot and not en_ind:
                discrepancias.append(
                    f"{symbol} {timeframe}: la línea de {nombre_rol} solo está en el motor"
                )

    return discrepancias
