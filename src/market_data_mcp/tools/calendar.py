"""Tool obtener_calendario_macro — calendario vía triple feed Fair Economy.

ForexFactory (ff) + MetalsMine (mm) + Energy EXCH (ee) desde nfs.faireconomy.media.
Reemplaza el pipeline MT5 (CalendarExporter.mq5 + leer_calendario_json).
MT5 queda exclusivamente para precios y niveles técnicos (get_asset_levels).
"""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastmcp import FastMCP

_CDN = "https://nfs.faireconomy.media"
_FEEDS = ("ff", "mm", "ee")
_SANTIAGO = ZoneInfo("America/Santiago")

_IMPACTO_EN_ES: dict[str, str] = {
    "High": "alto",
    "Medium": "medio",
    "Low": "bajo",
    "Holiday": "festivo",
}
_IMPACTO_RANK_EN: dict[str, int] = {"low": 0, "medium": 1, "high": 2}
_IMPACTO_RANK_ES: dict[str, int] = {"bajo": 0, "medio": 1, "alto": 2, "festivo": -1}

_GLOSARIO_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent / "data" / "glosario_siglas.json"
)


def _cargar_glosario() -> dict[str, Any]:
    if not _GLOSARIO_PATH.exists():
        return {}
    return json.loads(_GLOSARIO_PATH.read_text(encoding="utf-8"))


def _fetch_feed(slug: str) -> list[dict]:
    """GET {CDN}/{slug}_calendar_thisweek.json. Retorna [] ante cualquier falla."""
    url = f"{_CDN}/{slug}_calendar_thisweek.json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []


def _iso_to_santiago(date_str: str) -> str:
    """Convierte fecha ISO 8601 con offset a America/Santiago, formato 'YYYY-MM-DD HH:MM'."""
    dt = datetime.fromisoformat(date_str)
    return dt.astimezone(_SANTIAGO).strftime("%Y-%m-%d %H:%M")


def _normalizar_evento(ev: dict, slug: str) -> dict:
    """Mapea campos Fair Economy al schema canónico del proyecto."""
    return {
        "nombre": ev["title"],
        "divisa": ev.get("country", ""),
        "impacto": _IMPACTO_EN_ES.get(ev.get("impact", ""), "bajo"),
        "hora_servidor": _iso_to_santiago(ev["date"]),
        "forecast": ev.get("forecast", ""),
        "previo": ev.get("previous", ""),
        "fuente": slug,
    }


def _enganchar_glosario(nombre: str, glosario: dict) -> dict | None:
    """Busca entrada del glosario para un nombre de evento Fair Economy.

    Paso 1: sigla como palabra en el título (case-insensitive).
    Paso 2: alias en titulos_ff.
    Retorna None si no hay match.
    """
    nombre_upper = nombre.upper()
    for key, entry in glosario.items():
        if key.startswith("_") or key.isdigit():
            continue
        if key.upper() in nombre_upper:
            return entry
        for alias in entry.get("titulos_ff", []):
            if alias.upper() in nombre_upper:
                return entry
    return None


def _merge_feeds() -> tuple[list[dict], list[str]]:
    """Fetch ff+mm+ee, normaliza y deduplica por (nombre, hora_servidor)."""
    todos: list[dict] = []
    fallidos: list[str] = []
    seen: set[tuple[str, str]] = set()

    for slug in _FEEDS:
        raw = _fetch_feed(slug)
        if not raw:
            fallidos.append(slug)
            continue
        for ev in raw:
            try:
                norm = _normalizar_evento(ev, slug)
            except (KeyError, ValueError):
                continue
            key = (norm["nombre"], norm["hora_servidor"])
            if key not in seen:
                seen.add(key)
                todos.append(norm)

    return todos, fallidos


def register(mcp: FastMCP) -> None:

    @mcp.tool
    def obtener_calendario_macro(
        solo_hoy: bool = True,
        min_impact: str = "medium",
    ) -> dict[str, Any]:
        """Calendario macro vía triple feed Fair Economy (ForexFactory + MetalsMine + Energy EXCH).

        Cubre los 4 activos del catálogo: USD/CLP · XAU/USD · US100 (ff),
        COPPER (mm), WTI/energía (ee). Hora en America/Santiago.
        Si los 3 feeds fallan, retorna error NO_CALENDAR_FEEDS → el comando
        debe caer a WebSearch investing.com como fallback.

        Args:
            solo_hoy: si True, solo eventos cuya fecha == hoy en Santiago (default True).
            min_impact: umbral mínimo — 'low' | 'medium' | 'high' (default 'medium').

        Returns:
            {"eventos": [...], "source": "faireconomy", ...}
            o {"error": CÓDIGO, "message": "..."} si todos los feeds fallan.
        """
        if min_impact not in _IMPACTO_RANK_EN:
            return {
                "error": "INVALID_IMPACT",
                "message": (
                    f"min_impact '{min_impact}' inválido. "
                    f"Opciones: {list(_IMPACTO_RANK_EN)}"
                ),
            }

        todos, fallidos = _merge_feeds()

        if len(fallidos) == len(_FEEDS):
            return {
                "error": "NO_CALENDAR_FEEDS",
                "message": (
                    "Los 3 feeds de Fair Economy fallaron (ff, mm, ee). "
                    "Usar WebSearch investing.com como fallback."
                ),
            }

        umbral = _IMPACTO_RANK_EN[min_impact]
        hoy = datetime.now(tz=_SANTIAGO).date()
        glosario = _cargar_glosario()

        eventos: list[dict[str, Any]] = []
        for ev in todos:
            if _IMPACTO_RANK_ES.get(ev.get("impacto", "bajo"), 0) < umbral:
                continue
            if solo_hoy:
                try:
                    fecha_ev = datetime.strptime(
                        ev["hora_servidor"], "%Y-%m-%d %H:%M"
                    ).date()
                except (KeyError, ValueError):
                    continue
                if fecha_ev != hoy:
                    continue
            ev = dict(ev)
            entrada = _enganchar_glosario(ev["nombre"], glosario)
            if entrada:
                ev["diccionario"] = entrada
            else:
                ev["glosario_pendiente"] = True
            eventos.append(ev)

        resultado: dict[str, Any] = {"source": "faireconomy"}
        if fallidos:
            resultado["feeds_fallidos"] = fallidos

        if not eventos:
            resultado["eventos"] = []
            resultado["info"] = "sin eventos de impacto medio/alto hoy"
            return resultado

        resultado["eventos"] = eventos
        return resultado
