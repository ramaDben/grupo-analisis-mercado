"""Guardrail de autoridades: evita menciones a presidentes pasados.

Este módulo audita que los textos no hagan referencia a autoridades
obsoletas (ej. Jerome Powell) exigiendo el nombre vigente (ej. Kevin Warsh).
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from .veredicto import Veredicto, aprueba, falla

@lru_cache(maxsize=1)
def _cargar_autoridades() -> dict:
    ruta_config = Path(__file__).resolve().parent.parent.parent / "config" / "autoridades.json"
    if not ruta_config.exists():
        return {}
    with open(ruta_config, encoding="utf-8") as f:
        return json.load(f).get("bancos_centrales", {})

def autoridad_vigente(texto: str) -> Veredicto:
    """Verifica que no se mencionen autoridades obsoletas en el texto."""
    if not isinstance(texto, str) or not texto.strip():
        return aprueba()

    try:
        bancos = _cargar_autoridades()
    except Exception as e:
        return falla(
            "error_interno",
            f"No se pudo cargar config/autoridades.json: {e}",
            ubicacion="autoridades"
        )
    
    for sigla, datos in bancos.items():
        vigente = datos.get("vigente", "")
        obsoletos = datos.get("obsoletos", [])
        
        for obs in obsoletos:
            patron = rf"\b{re.escape(obs)}\b"
            if re.search(patron, texto, flags=re.IGNORECASE):
                detalle = (
                    f"Se mencionó a '{obs}', pero la autoridad vigente de "
                    f"{datos.get('institucion', sigla)} es {vigente}."
                )
                return falla("autoridad_obsoleta", detalle, ubicacion=obs)
                
    return aprueba()
