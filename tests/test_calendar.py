"""Tests del calendario macro vía Investing.com (getCalendarFilteredData)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from market_data_mcp.tools import calendar

_SANTIAGO = ZoneInfo("America/Santiago")


# ── helpers ───────────────────────────────────────────────────────────────────

def _fila(
    row_id=550758,
    nombre="Core CPI (MoM) (May)",
    pais="Chile",
    divisa="CLP",
    volatilidad="High Volatility Expected",
    actual="0.4%",
    titulo_actual="",
    forecast="0.3%",
    previo="0.2%",
    dias_offset=0,
) -> str:
    """Fila HTML como la retorna getCalendarFilteredData (timeZone=55 → UTC)."""
    dt_utc = (
        datetime.now(tz=_SANTIAGO).replace(hour=12, minute=0, second=0, microsecond=0)
        + timedelta(days=dias_offset)
    ).astimezone(timezone.utc)
    dt = dt_utc.strftime("%Y/%m/%d %H:%M:%S")
    return (
        f'<tr id="eventRowId_{row_id}" class="js-event-item " event_attr_ID="1218" '
        f'data-event-datetime="{dt}">'
        f'<td class="first left time js-time" >08:00</td>'
        f'<td class="left flagCur noWrap"><span title="{pais}" class="ceFlags" '
        f'data-img_key="x">&nbsp;</span> {divisa}</td>'
        f'<td class="left textNum sentiment noWrap" title="{volatilidad}" '
        f'data-img_key="bull3"><i></i></td>'
        f'<td class="left event" title="Click to view more info"><a href="/x" '
        f'target="_blank">      {nombre}</a></td>'
        f'<td class="bold act blackFont event-{row_id}-actual" title="{titulo_actual}" '
        f'id="eventActual_{row_id}">{actual or "&nbsp;"}</td>'
        f'<td class="fore event-{row_id}-forecast" '
        f'id="eventForecast_{row_id}">{forecast or "&nbsp;"}</td>'
        f'<td class="prev blackFont event-{row_id}-previous" '
        f'id="eventPrevious_{row_id}"><span title="">{previo or "&nbsp;"}</span></td>'
        f'</tr>'
    )


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


# ── unit: _utc_a_santiago ─────────────────────────────────────────────────────

def test_utc_a_santiago_convierte_correctamente():
    # 2026-06-10 12:30 UTC = 08:30 Santiago (UTC-4, invierno junio)
    assert calendar._utc_a_santiago("2026/06/10 12:30:00") == "2026-06-10 08:30"


# ── unit: _parsear_filas ──────────────────────────────────────────────────────

def test_parsear_fila_completa():
    evs = calendar._parsear_filas(_fila())
    assert len(evs) == 1
    ev = evs[0]
    assert ev["nombre"] == "Core CPI (MoM) (May)"
    assert ev["pais"] == "Chile"
    assert ev["divisa"] == "CLP"
    assert ev["impacto"] == "alto"
    assert ev["actual"] == "0.4%"
    assert ev["forecast"] == "0.3%"
    assert ev["previo"] == "0.2%"
    assert ev["fuente"] == "investing"


def test_parsear_actual_vacio_sin_resultado():
    evs = calendar._parsear_filas(_fila(actual=""))
    assert evs[0]["actual"] == ""
    assert "resultado" not in evs[0]


def test_resultado_mejor_que_esperado():
    evs = calendar._parsear_filas(_fila(titulo_actual="Better Than Expected"))
    assert evs[0]["resultado"] == "mejor"


def test_resultado_peor_que_esperado():
    evs = calendar._parsear_filas(_fila(titulo_actual="Worse Than Expected"))
    assert evs[0]["resultado"] == "peor"


def test_resultado_en_linea_con_forecast():
    evs = calendar._parsear_filas(_fila(titulo_actual=""))
    assert evs[0]["resultado"] == "en_linea"


def test_resultado_omitido_sin_forecast():
    evs = calendar._parsear_filas(_fila(forecast=""))
    assert "resultado" not in evs[0]


def test_volatilidad_a_impacto():
    evs = calendar._parsear_filas(
        _fila(row_id=1, volatilidad="Low Volatility Expected")
        + _fila(row_id=2, volatilidad="Moderate Volatility Expected")
        + _fila(row_id=3, volatilidad="High Volatility Expected")
    )
    assert [e["impacto"] for e in evs] == ["bajo", "medio", "alto"]


def test_fila_sin_evento_se_ignora():
    html = '<tr id="eventRowId_99" class="js-event-item" data-event-datetime="2026/06/10 12:00:00"><td>festivo</td></tr>'
    assert calendar._parsear_filas(html) == []


# ── unit: _enganchar_glosario ─────────────────────────────────────────────────

def test_enganchar_por_sigla_literal():
    entry = calendar._enganchar_glosario("Core CPI (MoM) (May)", _GLOSARIO_TEST)
    assert entry is not None
    assert entry["nombre_es"] == "IPC"


def test_enganchar_por_titulos_ff():
    entry = calendar._enganchar_glosario("Nonfarm Payrolls", _GLOSARIO_TEST)
    assert entry is not None
    assert entry["nombre_es"] == "Nóminas no agrícolas"


def test_enganchar_sin_match_retorna_none():
    assert calendar._enganchar_glosario("Baker Hughes Oil Rig Count", _GLOSARIO_TEST) is None


def test_enganchar_ignora_meta_y_event_id_numericos():
    assert calendar._enganchar_glosario("840030016 meta descripcion", _GLOSARIO_TEST) is None


# ── unit: _fetch_calendario ───────────────────────────────────────────────────

def test_fetch_retorna_vacio_en_error(monkeypatch, tmp_path):
    import urllib.request as urllib_req

    monkeypatch.setattr(calendar, "_CACHE_DIR", tmp_path)

    def _raise(*args, **kwargs):
        raise Exception("connection refused")

    monkeypatch.setattr(urllib_req, "urlopen", _raise)
    assert calendar._fetch_calendario("thisWeek") == ""


def test_fetch_usa_cache_vencida_como_respaldo(monkeypatch, tmp_path):
    import urllib.request as urllib_req

    monkeypatch.setattr(calendar, "_CACHE_DIR", tmp_path)
    cache = tmp_path / "investing_calendar_thisWeek.html"
    cache.write_text("<tr>cached</tr>", encoding="utf-8")
    monkeypatch.setattr(calendar, "_cache_valid", lambda p: False)

    def _raise(*args, **kwargs):
        raise Exception("timeout")

    monkeypatch.setattr(urllib_req, "urlopen", _raise)
    assert calendar._fetch_calendario("thisWeek") == "<tr>cached</tr>"


# ── integration: obtener_calendario_macro ─────────────────────────────────────

def test_camino_feliz(collector, monkeypatch):
    monkeypatch.setattr(calendar, "_fetch_calendario", lambda tab: _fila())
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: _GLOSARIO_TEST)

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="medium")

    assert "error" not in res, res
    assert res["source"] == "investing"
    ev = res["eventos"][0]
    assert ev["nombre"] == "Core CPI (MoM) (May)"
    assert ev["actual"] == "0.4%"
    assert ev["diccionario"]["nombre_es"] == "IPC"


def test_schema_normalizado_campos_correctos(collector, monkeypatch):
    monkeypatch.setattr(calendar, "_fetch_calendario", lambda tab: _fila())
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: _GLOSARIO_TEST)

    calendar.register(collector)
    ev = collector.tools["obtener_calendario_macro"](min_impact="medium")["eventos"][0]

    for campo in ("nombre", "divisa", "pais", "impacto", "hora_servidor",
                  "forecast", "previo", "actual", "fuente"):
        assert campo in ev, campo
    assert ev["fuente"] == "investing"


def test_glosario_pendiente_si_no_hay_match(collector, monkeypatch):
    monkeypatch.setattr(
        calendar, "_fetch_calendario",
        lambda tab: _fila(nombre="Baker Hughes Oil Rig Count"),
    )
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: _GLOSARIO_TEST)

    calendar.register(collector)
    ev = collector.tools["obtener_calendario_macro"](min_impact="medium")["eventos"][0]
    assert ev.get("glosario_pendiente") is True
    assert "diccionario" not in ev


def test_filtro_min_impact_excluye_bajo(collector, monkeypatch):
    html = (
        _fila(row_id=1, nombre="CPI (MoM)", volatilidad="High Volatility Expected")
        + _fila(row_id=2, nombre="Minor Release", volatilidad="Low Volatility Expected")
    )
    monkeypatch.setattr(calendar, "_fetch_calendario", lambda tab: html)
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: {})

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="medium")

    assert all(e["impacto"] in ("medio", "alto") for e in res["eventos"])
    assert not any(e["nombre"] == "Minor Release" for e in res["eventos"])


def test_solo_hoy_filtra_otros_dias(collector, monkeypatch):
    html = (
        _fila(row_id=1, nombre="CPI (MoM)", dias_offset=0)
        + _fila(row_id=2, nombre="PPI (MoM)", dias_offset=2)
    )
    monkeypatch.setattr(calendar, "_fetch_calendario", lambda tab: html)
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: {})

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](solo_hoy=True, min_impact="medium")

    nombres = [e["nombre"] for e in res["eventos"]]
    assert "CPI (MoM)" in nombres
    assert "PPI (MoM)" not in nombres


def test_falla_total_retorna_no_calendar_feeds(collector, monkeypatch):
    monkeypatch.setattr(calendar, "_fetch_calendario", lambda tab: "")

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"]()

    assert res["error"] == "NO_CALENDAR_FEEDS"
    assert isinstance(res["message"], str) and res["message"]


def test_sin_eventos_es_caso_legitimo(collector, monkeypatch):
    monkeypatch.setattr(
        calendar, "_fetch_calendario",
        lambda tab: _fila(volatilidad="Low Volatility Expected"),
    )
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: {})

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="medium")

    assert "error" not in res
    assert res["eventos"] == []
    assert "info" in res


def test_min_impact_invalido_retorna_error(collector, monkeypatch):
    monkeypatch.setattr(calendar, "_fetch_calendario", lambda tab: "")

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="extremo")

    assert res["error"] == "INVALID_IMPACT"
    assert isinstance(res["message"], str) and res["message"]
