"""Umbral de frescura de los datos macro, con calendario de negocio.

Vivía dentro del lector del Playbook (`bias_reader`) aunque no es del Playbook:
lo consultan los relojes de `pipeline_datos --estado` y `get_curva_tasas`. Al
retirar el Playbook (2026-09-27) se mudó acá, con su config propia.

El umbral es más ancho en fin de semana y lunes porque los emisores no publican
el sábado ni el domingo: un dato del viernes sigue siendo el último que existe.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_FRESCURA = BASE_DIR / "config" / "frescura_datos.json"

DEFAULTS = {
    "staleness_hours_weekday": 24.0,
    "staleness_hours_weekend": 80.0,
}


def cargar_config_staleness(config_path: Path | None = None) -> dict[str, float]:
    """Lee los umbrales de `config/frescura_datos.json`, o los defaults si falta."""
    ruta = config_path or CONFIG_FRESCURA
    if not ruta.exists():
        return dict(DEFAULTS)
    try:
        cfg = json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:
        return dict(DEFAULTS)
    return {k: float(cfg.get(k, v)) for k, v in DEFAULTS.items()}


def validar_staleness(
    as_of_str: str | None,
    config: dict[str, float] | None = None,
    now_dt: datetime | None = None,
) -> tuple[bool, float, float, str | None]:
    """Evalúa si `as_of_str` es fresco según el calendario de negocio.

    Retorna `(es_fresco, horas_antiguedad, umbral_horas, motivo_error)`.
    """
    if not as_of_str or not isinstance(as_of_str, str):
        return False, 0.0, 0.0, "MALFORMED_DATE"

    try:
        dt_as_of = datetime.fromisoformat(as_of_str.replace("Z", "+00:00"))
    except Exception:
        return False, 0.0, 0.0, "MALFORMED_DATE"

    now = now_dt or datetime.now(timezone.utc)
    if dt_as_of.tzinfo is None:
        dt_as_of = dt_as_of.replace(tzinfo=timezone.utc)

    horas = max((now - dt_as_of).total_seconds() / 3600.0, 0.0)

    cfg = config or cargar_config_staleness()
    # Sábado = 5, domingo = 6, lunes = 0: el umbral largo cubre el fin de semana.
    es_fin_de_semana_o_lunes = now.weekday() in (5, 6, 0)
    umbral = cfg["staleness_hours_weekend"] if es_fin_de_semana_o_lunes else cfg["staleness_hours_weekday"]

    if horas > umbral:
        return False, horas, umbral, "STALE_DATA"
    return True, horas, umbral, None
