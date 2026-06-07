"""Tool obtener_calendario_macro — calendario nativo MT5 con contrato de error explícito.

Reemplaza a get_economic_events (deprecado). Lee el JSON que escribe el Service
MQL5 CalendarExporter, valida frescura, engancha el Diccionario rápido por
event_id y devuelve los eventos en hora del servidor MT5 (sin conversiones).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from market_data_mcp import mt5_client

# Ranking de impacto del campo `impacto` del evento (español, viene de MT5).
_IMPACTO_RANK_ES = {"bajo": 0, "medio": 1, "alto": 2}
# Ranking del argumento público `min_impact` de la tool (inglés, API externa).
_IMPACTO_RANK_EN = {"low": 0, "medium": 1, "high": 2}

# Frescura: el JSON se considera viejo si supera estas horas (issue #53).
_STALE_HORAS = 3

# data/glosario_siglas.json — src/market_data_mcp/tools/calendar.py → 4 niveles arriba = raíz repo.
_GLOSARIO_PATH = Path(__file__).resolve().parent.parent.parent.parent / "data" / "glosario_siglas.json"


def _cargar_glosario() -> dict[str, Any]:
    """Lee el glosario keyed por event_id. Si no existe, retorna {} (no es error)."""
    if not _GLOSARIO_PATH.exists():
        return {}
    return json.loads(_GLOSARIO_PATH.read_text(encoding="utf-8"))


def register(mcp: FastMCP) -> None:

    @mcp.tool
    def obtener_calendario_macro(
        solo_hoy: bool = True,
        min_impact: str = "medium",
    ) -> dict[str, Any]:
        """Calendario macro nativo de MT5 (fuente primaria; WebSearch es fallback).

        Lee el JSON exportado por el Service MQL5, valida que esté fresco, filtra
        por impacto y (si solo_hoy) por la fecha de hoy, y engancha la explicación
        novata por event_id. Hora en el reloj del servidor MT5, sin conversiones.

        Args:
            solo_hoy: si True, solo eventos cuya fecha == hoy (default True).
            min_impact: umbral mínimo — 'low' | 'medium' | 'high' (default 'medium').

        Returns:
            {"eventos":[...], "generated_at":..., "source":"mt5_native", ...}
            o {"error": CÓDIGO, "message": "..."} si el calendario no está disponible.
        """
        if min_impact not in _IMPACTO_RANK_EN:
            return {
                "error": "INVALID_IMPACT",
                "message": f"min_impact '{min_impact}' inválido. Opciones: {list(_IMPACTO_RANK_EN)}",
            }

        try:
            data = mt5_client.leer_calendario_json()
        except FileNotFoundError as exc:
            return {"error": "NO_CALENDAR_FILE", "message": str(exc)}
        except (json.JSONDecodeError, ValueError) as exc:
            return {"error": "BAD_CALENDAR_JSON", "message": f"Calendario MT5 ilegible: {exc}"}

        # --- Frescura ---
        try:
            generado = datetime.strptime(data["generated_at"], "%Y-%m-%d %H:%M")
        except (KeyError, ValueError) as exc:
            return {"error": "BAD_CALENDAR_JSON", "message": f"generated_at inválido: {exc}"}
        if datetime.now() - generado > timedelta(hours=_STALE_HORAS):
            return {
                "error": "STALE_CALENDAR",
                "message": (
                    f"Calendario MT5 viejo (generado {data['generated_at']}, "
                    f"umbral {_STALE_HORAS} h). ¿Service CalendarExporter caído?"
                ),
            }

        # --- Filtrado ---
        umbral = _IMPACTO_RANK_EN[min_impact]
        hoy = datetime.now().date()
        glosario = _cargar_glosario()

        eventos: list[dict[str, Any]] = []
        for ev in data.get("eventos", []):
            if _IMPACTO_RANK_ES.get(ev.get("impacto", "bajo"), 0) < umbral:
                continue
            if solo_hoy:
                try:
                    fecha_ev = datetime.strptime(ev["hora_servidor"], "%Y-%m-%d %H:%M").date()
                except (KeyError, ValueError):
                    continue
                if fecha_ev != hoy:
                    continue
            ev = dict(ev)  # copia para no mutar el origen
            entrada = glosario.get(str(ev.get("event_id")))
            if entrada:
                ev["diccionario"] = entrada
            else:
                ev["glosario_pendiente"] = True
            eventos.append(ev)

        if not eventos:
            return {
                "eventos": [],
                "info": "sin eventos de impacto medio/alto hoy",
                "generated_at": data["generated_at"],
                "source": "mt5_native",
            }

        return {
            "eventos": eventos,
            "generated_at": data["generated_at"],
            "server_tz_note": data.get("server_tz_note", ""),
            "source": "mt5_native",
        }
