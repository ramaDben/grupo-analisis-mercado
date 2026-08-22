#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
actualizar_calendario.py
Modulo para validar, actualizar y refrescar los calendarios anuales de eventos macroeconomicos.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parents[4]
DATA_AGENDA = BASE_DIR / "data central" / "DATA AGENDA"

def validar_evento(evento: dict) -> bool:
    campos_obligatorios = [
        "id", "nombre", "entidad", "pais", "fecha_publicacion",
        "hora_publicacion", "timezone", "impacto", "reporte_asociado",
        "fuente_oficial", "series_afectadas"
    ]
    for campo in campos_obligatorios:
        if campo not in evento:
            raise ValueError(f"Falta el campo obligatorio '{campo}' en el evento {evento.get('id', 'desconocido')}")
    
    # Validar formato fecha y hora
    datetime.strptime(f"{evento['fecha_publicacion']} {evento['hora_publicacion']}", "%Y-%m-%d %H:%M")
    
    # Validar timezone
    try:
        ZoneInfo(evento["timezone"])
    except Exception as e:
        raise ValueError(f"Zona horaria invalida '{evento['timezone']}': {e}")
        
    return True

def refrescar_calendario(year: int = 2026):
    archivo_cal = DATA_AGENDA / f"calendario_{year}.json"
    if not archivo_cal.exists():
        print(f"[WARN] No existe {archivo_cal}. Creando base vacia...")
        eventos = []
    else:
        with open(archivo_cal, "r", encoding="utf-8") as f:
            eventos = json.load(f)
            
    ahora_utc = datetime.now(timezone.utc).isoformat()
    for ev in eventos:
        validar_evento(ev)
        ev["ultima_verificacion"] = ahora_utc
        
    with open(archivo_cal, "w", encoding="utf-8") as f:
        json.dump(eventos, f, indent=2, ensure_ascii=False)
        
    print(f"[OK] Calendario {year} validado y actualizado con exito ({len(eventos)} eventos).")

if __name__ == "__main__":
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2026
    refrescar_calendario(year)
