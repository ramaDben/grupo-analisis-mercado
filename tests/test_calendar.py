"""Tests del calendario macro vía triple feed Fair Economy (ff + mm + ee)."""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from market_data_mcp.tools import calendar

_SANTIAGO = ZoneInfo("America/Santiago")


# ── helpers ───────────────────────────────────────────────────────────────────

def _ev(title="CPI m/m", impact="High", dias_offset=0) -> dict:
    """Evento Fair Economy con fecha en Santiago (hoy + dias_offset) al mediodía."""
    now = datetime.now(tz=_SANTIAGO).replace(
        hour=12, minute=0, second=0, microsecond=0
    ) + timedelta(days=dias_offset)
    return {
        "title": title,
        "country": "USD",
        "date": now.isoformat(),
        "impact": impact,
        "forecast": "0.3%",
        "previous": "0.4%",
    }


_GLOSARIO_TEST = {
    "_meta": {"descripcion": "test"},
    "840030016": {"sigla": "NFP", "nombre_es": "Nóminas", "explicacion": "empleos"},
    "CPI": {"nombre_es": "IPC", "explicacion": "precios al consumidor"},
    "NFP": {
        "nombre_es": "Nóminas no agrícolas",
        "explicacion": "empleos nuevos",
        "titulos_ff": ["Nonfarm Payrolls"],
    },
}


# ── unit: _iso_to_santiago ────────────────────────────────────────────────────

def test_iso_to_santiago_convierte_utc_correctamente():
    # 2026-06-10T18:30:00+00:00 UTC = 14:30 Santiago (UTC-4, invierno junio)
    result = calendar._iso_to_santiago("2026-06-10T18:30:00+00:00")
    assert result == "2026-06-10 14:30"


def test_iso_to_santiago_preserva_hora_ya_en_santiago():
    # Fecha ya con offset -04:00 (Santiago invierno)
    result = calendar._iso_to_santiago("2026-06-10T14:30:00-04:00")
    assert result == "2026-06-10 14:30"


# ── unit: _enganchar_glosario ─────────────────────────────────────────────────

def test_enganchar_por_sigla_literal():
    entry = calendar._enganchar_glosario("Core CPI m/m", _GLOSARIO_TEST)
    assert entry is not None
    assert entry["nombre_es"] == "IPC"


def test_enganchar_por_titulos_ff():
    entry = calendar._enganchar_glosario("Nonfarm Payrolls", _GLOSARIO_TEST)
    assert entry is not None
    assert entry["nombre_es"] == "Nóminas no agrícolas"


def test_enganchar_sin_match_retorna_none():
    entry = calendar._enganchar_glosario("Baker Hughes Oil Rig Count", _GLOSARIO_TEST)
    assert entry is None


def test_enganchar_ignora_meta_y_event_id_numericos():
    # _meta y "840030016" no deben producir match
    entry = calendar._enganchar_glosario("840030016 meta descripcion", _GLOSARIO_TEST)
    assert entry is None


# ── unit: _fetch_feed ─────────────────────────────────────────────────────────

def test_fetch_feed_retorna_lista_vacia_en_error(monkeypatch):
    import urllib.request as urllib_req

    def _raise(*args, **kwargs):
        raise Exception("connection refused")

    monkeypatch.setattr(urllib_req, "urlopen", _raise)
    assert calendar._fetch_feed("ff") == []


# ── integration: obtener_calendario_macro ─────────────────────────────────────

def test_camino_feliz_merge_tres_feeds(collector, monkeypatch):
    feeds = {
        "ff": [_ev("CPI m/m", "High")],
        "mm": [_ev("LME Copper Inventories", "Medium")],
        "ee": [_ev("Crude Oil Inventories", "High")],
    }
    monkeypatch.setattr(calendar, "_fetch_feed", lambda slug: feeds.get(slug, []))
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: _GLOSARIO_TEST)

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="medium")

    assert "error" not in res, res
    assert res["source"] == "faireconomy"
    nombres = [e["nombre"] for e in res["eventos"]]
    assert "CPI m/m" in nombres
    assert "LME Copper Inventories" in nombres
    assert "Crude Oil Inventories" in nombres


def test_deduplicacion_evento_en_dos_feeds(collector, monkeypatch):
    ev_opec = _ev("OPEC Meetings", "Medium")
    feeds = {
        "ff": [ev_opec],
        "mm": [],
        "ee": [ev_opec],  # mismo evento en ff y ee
    }
    monkeypatch.setattr(calendar, "_fetch_feed", lambda slug: feeds.get(slug, []))
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: {})

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="low")

    assert "error" not in res
    assert sum(1 for e in res["eventos"] if e["nombre"] == "OPEC Meetings") == 1


def test_schema_normalizado_campos_correctos(collector, monkeypatch):
    monkeypatch.setattr(calendar, "_fetch_feed",
                        lambda slug: [_ev("CPI m/m", "High")] if slug == "ff" else [])
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: _GLOSARIO_TEST)

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="medium")

    ev = res["eventos"][0]
    assert "nombre" in ev
    assert "divisa" in ev
    assert "impacto" in ev
    assert "hora_servidor" in ev
    assert "forecast" in ev
    assert "previo" in ev
    assert "fuente" in ev
    assert ev["impacto"] == "alto"  # High → alto
    assert ev["fuente"] == "ff"


def test_glosario_enganchado_por_sigla(collector, monkeypatch):
    monkeypatch.setattr(calendar, "_fetch_feed",
                        lambda slug: [_ev("CPI m/m", "High")] if slug == "ff" else [])
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: _GLOSARIO_TEST)

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="medium")

    ev = res["eventos"][0]
    assert "diccionario" in ev
    assert ev["diccionario"]["nombre_es"] == "IPC"


def test_glosario_pendiente_si_no_hay_match(collector, monkeypatch):
    monkeypatch.setattr(calendar, "_fetch_feed",
                        lambda slug: [_ev("Baker Hughes Oil Rig Count", "Medium")] if slug == "ee" else [])
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: _GLOSARIO_TEST)

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="low")

    ev = res["eventos"][0]
    assert ev.get("glosario_pendiente") is True
    assert "diccionario" not in ev


def test_filtro_min_impact_excluye_bajo(collector, monkeypatch):
    feeds = {
        "ff": [_ev("CPI m/m", "High"), _ev("Minor Release", "Low")],
        "mm": [], "ee": [],
    }
    monkeypatch.setattr(calendar, "_fetch_feed", lambda slug: feeds.get(slug, []))
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: {})

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="medium")

    assert all(e["impacto"] in ("medio", "alto") for e in res["eventos"])
    assert not any(e["nombre"] == "Minor Release" for e in res["eventos"])


def test_solo_hoy_filtra_otros_dias(collector, monkeypatch):
    feeds = {
        "ff": [_ev("CPI m/m", "High", dias_offset=0),
               _ev("PPI m/m", "High", dias_offset=2)],  # pasado mañana
        "mm": [], "ee": [],
    }
    monkeypatch.setattr(calendar, "_fetch_feed", lambda slug: feeds.get(slug, []))
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: {})

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](solo_hoy=True, min_impact="medium")

    nombres = [e["nombre"] for e in res["eventos"]]
    assert "CPI m/m" in nombres
    assert "PPI m/m" not in nombres


def test_falla_parcial_incluye_feeds_fallidos(collector, monkeypatch):
    feeds = {"ff": [_ev("CPI m/m", "High")], "mm": [], "ee": []}
    monkeypatch.setattr(calendar, "_fetch_feed", lambda slug: feeds.get(slug, []))
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: {})

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="medium")

    assert "error" not in res
    assert "feeds_fallidos" in res
    assert set(res["feeds_fallidos"]) == {"mm", "ee"}


def test_falla_total_retorna_no_calendar_feeds(collector, monkeypatch):
    monkeypatch.setattr(calendar, "_fetch_feed", lambda slug: [])

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"]()

    assert res["error"] == "NO_CALENDAR_FEEDS"
    assert isinstance(res["message"], str) and res["message"]


def test_sin_eventos_es_caso_legitimo(collector, monkeypatch):
    # Feeds responden pero todos son de bajo impacto → filtro deja vacío
    feeds = {"ff": [_ev("Minor Data", "Low")], "mm": [], "ee": []}
    monkeypatch.setattr(calendar, "_fetch_feed", lambda slug: feeds.get(slug, []))
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: {})

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="medium")

    assert "error" not in res
    assert res["eventos"] == []
    assert "info" in res


def test_min_impact_invalido_retorna_error(collector, monkeypatch):
    monkeypatch.setattr(calendar, "_fetch_feed", lambda slug: [])

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="extremo")

    assert res["error"] == "INVALID_IMPACT"
    assert isinstance(res["message"], str) and res["message"]
