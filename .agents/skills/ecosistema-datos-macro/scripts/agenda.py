#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
agenda.py
Motor de consulta de agenda macroeconomica y resolucion de zonas horarias.
Soporta salida interactiva en consola y salida --json estructurada.
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parents[4]
DATA_AGENDA = BASE_DIR / "data central" / "DATA AGENDA"
LOCAL_TZ = ZoneInfo("America/Santiago")

def obtener_agenda(fecha_base: datetime = None) -> dict:
    if fecha_base is None:
        ahora_local = datetime.now(LOCAL_TZ)
    else:
        ahora_local = fecha_base.astimezone(LOCAL_TZ)
        
    year = ahora_local.year
    archivo_cal = DATA_AGENDA / f"calendario_{year}.json"
    
    if not archivo_cal.exists():
        return {
            "error": f"No se encontro el archivo de calendario para el año {year}",
            "fecha_consulta": ahora_local.isoformat(),
            "eventos_hoy": [],
            "eventos_proximos": []
        }
        
    with open(archivo_cal, "r", encoding="utf-8") as f:
        todos_los_eventos = json.load(f)
        
    eventos_hoy = []
    eventos_proximos = []
    
    hoy_str = ahora_local.strftime("%Y-%m-%d")
    limite_7d = ahora_local + timedelta(days=7)
    
    for ev in todos_los_eventos:
        # Construir datetime en la zona horaria del evento
        tz_evento = ZoneInfo(ev["timezone"])
        dt_evento = datetime.strptime(
            f"{ev['fecha_publicacion']} {ev['hora_publicacion']}",
            "%Y-%m-%d %H:%M"
        ).replace(tzinfo=tz_evento)
        
        # Convertir a hora local (Chile)
        dt_local = dt_evento.astimezone(LOCAL_TZ)
        dt_utc = dt_evento.astimezone(timezone.utc)
        
        ev_info = {
            **ev,
            "hora_local_cl": dt_local.strftime("%H:%M"),
            "fecha_local_cl": dt_local.strftime("%Y-%m-%d"),
            "dt_local_iso": dt_local.isoformat(),
            "dt_utc_iso": dt_utc.isoformat()
        }
        
        # Determinar estado
        diferencia_min = (ahora_local - dt_local).total_seconds() / 60.0
        if diferencia_min < 0:
            ev_info["estado"] = "PENDIENTE"
        elif 0 <= diferencia_min <= 45:
            ev_info["estado"] = "EN_VENTANA"
        else:
            ev_info["estado"] = "PUBLICADO"
            
        if ev_info["fecha_local_cl"] == hoy_str:
            eventos_hoy.append(ev_info)
        elif ahora_local < dt_local <= limite_7d:
            eventos_proximos.append(ev_info)
            
    # Ordenar por fecha y hora
    eventos_hoy.sort(key=lambda x: x["dt_local_iso"])
    eventos_proximos.sort(key=lambda x: x["dt_local_iso"])
    
    return {
        "fecha_consulta": ahora_local.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "timezone_local": "America/Santiago",
        "hay_eventos_hoy": len(eventos_hoy) > 0,
        "eventos_hoy": eventos_hoy,
        "eventos_proximos_7_dias": eventos_proximos
    }

def imprimir_agenda_consola(res: dict):
    print("=" * 70)
    print(f" 🧭 AGENDA MACROECONÓMICA OFICIAL — {res['fecha_consulta']}")
    print("=" * 70)
    
    if res["hay_eventos_hoy"]:
        print(f"\n🚨 EVENTOS PROGRAMADOS PARA HOY ({len(res['eventos_hoy'])}):")
        for ev in res["eventos_hoy"]:
            badge_estado = {
                "PENDIENTE": "⏳ PENDIENTE",
                "EN_VENTANA": "🔥 EN VENTANA DE PUBLICACIÓN",
                "PUBLICADO": "✅ PUBLICADO (Disponible en API)"
            }.get(ev["estado"], ev["estado"])
            
            print(f"\n  • [{ev['hora_local_cl']} CL / {ev['hora_publicacion']} {ev['timezone']}] {ev['nombre']}")
            print(f"    Entidad: {ev['entidad']} ({ev['pais']}) | Impacto: {ev['impacto']}")
            print(f"    Estado: {badge_estado}")
            print(f"    Reporte Asociado: {ev['reporte_asociado']}")
            print(f"    Fuente: {ev['fuente_oficial']}")
    else:
        print("\n☕ HOY: No hay eventos oficiales de alto impacto programados para Chile, EE.UU. o Europa.")
        
    print("\n" + "-" * 70)
    print(f" 📅 PRÓXIMOS EVENTOS EN LOS SIGUIENTES 7 DÍAS ({len(res['eventos_proximos_7_dias'])}):")
    print("-" * 70)
    
    if res["eventos_proximos_7_dias"]:
        for ev in res["eventos_proximos_7_dias"]:
            print(f"  • [{ev['fecha_local_cl']} a las {ev['hora_local_cl']} CL] {ev['nombre']} ({ev['entidad']})")
    else:
        print("  • No hay eventos agendados en los próximos 7 días.")
        
    print("\n" + "=" * 70)

def main():
    parser = argparse.ArgumentParser(description="Consulta de Agenda Macro")
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON estructurado")
    parser.add_argument("--fecha", type=str, help="Simular fecha YYYY-MM-DD")
    args = parser.parse_args()
    
    fecha_simulada = None
    if args.fecha:
        fecha_simulada = datetime.strptime(args.fecha, "%Y-%m-%d").replace(tzinfo=LOCAL_TZ)
        
    resultado = obtener_agenda(fecha_simulada)
    
    if args.json:
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    else:
        imprimir_agenda_consola(resultado)

if __name__ == "__main__":
    main()
