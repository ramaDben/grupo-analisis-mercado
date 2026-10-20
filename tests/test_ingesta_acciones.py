"""Ingesta de earnings e informes SEC de las acciones (spec 2026-10-20, Task 7). Sin red."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(RAIZ / "scripts"), str(RAIZ / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import ingesta_acciones as ia  # noqa: E402
import pipeline_datos as pd_  # noqa: E402

from analista import preparar as pr  # noqa: E402

SUBMISSIONS = {"filings": {"recent": {
    "form": ["4", "8-K", "10-Q", "10-K", "8-K", "S-8"],
    "filingDate": ["2026-10-15", "2026-10-10", "2026-08-01", "2025-11-01", "2025-10-01", "2025-09-01"],
    "reportDate": ["", "2026-10-09", "2026-06-27", "2025-09-27", "", ""],
    "accessionNumber": ["0000320193-26-000001", "0000320193-26-000002", "0000320193-26-000003",
                        "0000320193-25-000004", "0000320193-25-000005", "0000320193-25-000006"],
    "primaryDocument": ["x.xml", "a8k.htm", "a10q.htm", "a10k.htm", "b8k.htm", "s8.htm"]}}}


def test_la_ingesta_marca_la_fecha_como_no_oficial_y_no_inventa_si_yfinance_falla():
    def descargar(ticker):
        if ticker == "MSFT":
            raise RuntimeError("sin red")
        return "2026-10-29"

    r = ia.fechas_earnings(["AAPL", "MSFT"], descargar)
    assert r["AAPL"] == {"fecha": "2026-10-29", "fuente": "yfinance (no oficial)"}
    assert r["MSFT"] == {"fecha": None, "fuente": "yfinance (no oficial)"}


def test_una_fecha_ilegible_es_none_y_no_se_inventa():
    assert ia.fechas_earnings(["AAPL"], lambda t: "pronto")["AAPL"]["fecha"] is None


def test_informes_sec_trae_solo_10k_10q_y_8k_con_su_url_y_el_user_agent(monkeypatch):
    # El User-Agent sale de SEC_USER_AGENT (revisión final): ya no hay uno fijo sin contacto.
    monkeypatch.setenv("SEC_USER_AGENT", "Equipo GI analistas")
    visto = {}

    def descargar(url, headers):
        visto.update(url=url, headers=headers)
        return SUBMISSIONS

    r = ia.informes_sec("0000320193", descargar)
    assert visto["url"] == "https://data.sec.gov/submissions/CIK0000320193.json"
    assert visto["headers"]["User-Agent"].strip()
    assert [i["forma"] for i in r] == ["8-K", "10-Q", "10-K", "8-K"]
    primero = r[0]
    assert primero["fecha"] == "2026-10-10" and primero["periodo"] == "2026-10-09"
    assert primero["url"] == "https://www.sec.gov/Archives/edgar/data/320193/000032019326000002/a8k.htm"
    assert all(set(i) == {"forma", "fecha", "periodo", "url"} for i in r)


def test_sec_que_falla_deja_la_lista_vacia():
    def descargar(url, headers):
        raise RuntimeError("403")

    assert ia.informes_sec("0000320193", descargar) == []


def _ingesta(base, ahora, fecha="2026-10-29"):
    anclas = {"#AAPL": ("acciones", {"ticker": "AAPL", "cik": "0000320193"})}
    ia.ingestar(anclas, base, ahora=ahora, descargar_fecha=lambda t: fecha,
                descargar_sec=lambda u, headers: SUBMISSIONS)


def test_la_ingesta_escribe_los_dos_archivos_con_sello(tmp_path):
    ahora = datetime(2026, 10, 20, 15, 0, tzinfo=timezone.utc)
    _ingesta(tmp_path, ahora)
    cal = json.loads((tmp_path / "earnings_calendar.json").read_text(encoding="utf-8"))
    est = json.loads((tmp_path / "estados_financieros.json").read_text(encoding="utf-8"))
    assert cal["ingesta"] == est["ingesta"] == "2026-10-20T15:00:00+00:00"
    assert cal["acciones"]["#AAPL"]["fecha"] == "2026-10-29"
    assert est["acciones"]["#AAPL"]["informes"][0]["forma"] == "8-K"


def test_sin_ingesta_o_vencida_la_accion_no_publica_y_el_bot_lo_dice(tmp_path):
    hoy = datetime(2026, 10, 20, 15, 0, tzinfo=timezone.utc)  # martes
    with pytest.raises(pr.PreparacionFallida, match="ingesta de acciones"):
        ia.leer_empresa("#AAPL", tmp_path, ahora=hoy)
    _ingesta(tmp_path, datetime(2026, 10, 10, 15, 0, tzinfo=timezone.utc))
    with pytest.raises(pr.PreparacionFallida, match="vencida"):
        ia.leer_empresa("#AAPL", tmp_path, ahora=hoy)


def test_la_fecha_futura_va_en_modo_anticipacion(tmp_path):
    hoy = datetime(2026, 10, 20, 15, 0, tzinfo=timezone.utc)
    _ingesta(tmp_path, hoy)
    e = ia.leer_empresa("#AAPL", tmp_path, ahora=hoy)
    assert e["proxima_earnings"] == "jueves 29/10" and e["fuente_fecha"] == "yfinance (no oficial)"
    assert e["ultimo_informe"]["forma"] == "8-K"
    texto = (RAIZ / ".claude" / "commands" / "analista.md").read_text(encoding="utf-8")
    assert "datos.empresa" in texto and "modo anticipación" in texto


def test_una_fecha_pasada_no_es_proxima(tmp_path):
    hoy = datetime(2026, 10, 20, 15, 0, tzinfo=timezone.utc)
    _ingesta(tmp_path, hoy, fecha="2026-10-01")
    assert ia.leer_empresa("#AAPL", tmp_path, ahora=hoy)["proxima_earnings"] is None


def test_preparar_sella_empresa_solo_en_acciones():
    import inspect

    fuente = inspect.getsource(pr.preparar_oportunidad)
    assert 'segmento == "acciones"' in fuente and "lec.empresa" in fuente
    assert pr.Lectores().empresa is pr._empresa


def test_pipeline_datos_corre_acciones_despues_de_precios():
    nombres = [p.nombre for p in pd_.PASOS]
    assert nombres.index("acciones") == nombres.index("precios") + 1
    assert next(p for p in pd_.PASOS if p.nombre == "acciones").script.name == "ingesta_acciones.py"


# ───────────────────────────────────────────── revisión final: la falla de la SEC no es silenciosa


def test_consultar_sec_devuelve_el_error_y_informes_sec_sigue_vacia():
    def descargar(url, headers):
        raise RuntimeError("403 Forbidden")

    informes, error = ia.consultar_sec("0000320193", descargar)
    assert informes == [] and "403" in error
    assert ia.consultar_sec("0000320193", lambda u, headers: SUBMISSIONS)[1] is None


def test_la_ingesta_guarda_el_error_por_ticker_y_lo_cuenta(tmp_path):
    def sec(url, headers):
        if "CIK0000789019" in url:
            raise RuntimeError("403 Forbidden")
        return SUBMISSIONS

    anclas = {"#AAPL": ("acciones", {"ticker": "AAPL", "cik": "0000320193"}),
              "#MSFT": ("acciones", {"ticker": "MSFT", "cik": "0000789019"})}
    r = ia.ingestar(anclas, tmp_path, ahora=datetime(2026, 10, 20, 15, 0, tzinfo=timezone.utc),
                    descargar_fecha=lambda t: "2026-10-29", descargar_sec=sec)
    est = json.loads((tmp_path / "estados_financieros.json").read_text(encoding="utf-8"))["acciones"]
    assert "403" in est["#MSFT"]["error"] and est["#MSFT"]["informes"] == []
    assert "error" not in est["#AAPL"]
    assert r["fallas_sec"] == 1 and r["con_informes"] == 1


def test_main_sale_con_error_si_falla_la_sec_en_todas(monkeypatch, capsys):
    monkeypatch.setattr(ia, "ingestar", lambda anclas: {"fechas": 14, "con_informes": 0, "fallas_sec": 14,
                                                        "total": 14, "error_sec": "RuntimeError: 403"})
    assert ia.main() != 0
    salida = capsys.readouterr().out
    assert "SEC" in salida and "14" in salida
    monkeypatch.setattr(ia, "ingestar", lambda anclas: {"fechas": 14, "con_informes": 13, "fallas_sec": 1,
                                                        "total": 14, "error_sec": "RuntimeError: 403"})
    assert ia.main() == 0
    assert "1" in capsys.readouterr().out


def test_leer_empresa_avisa_si_el_ticker_no_tiene_informes_por_error(tmp_path):
    hoy = datetime(2026, 10, 20, 15, 0, tzinfo=timezone.utc)
    anclas = {"#AAPL": ("acciones", {"ticker": "AAPL", "cik": "0000320193"})}

    def sec(url, headers):
        raise RuntimeError("403 Forbidden")

    ia.ingestar(anclas, tmp_path, ahora=hoy, descargar_fecha=lambda t: "2026-10-29", descargar_sec=sec)
    e = ia.leer_empresa("#AAPL", tmp_path, ahora=hoy)
    assert e["ultimo_informe"] is None
    assert e["avisos"] and "SEC" in e["avisos"][0]
    assert "—" not in e["avisos"][0] and "–" not in e["avisos"][0]
    _ingesta(tmp_path, hoy)
    assert ia.leer_empresa("#AAPL", tmp_path, ahora=hoy)["avisos"] == []


def test_el_user_agent_sale_de_sec_user_agent_y_sin_el_no_se_consulta(monkeypatch):
    monkeypatch.delenv("SEC_USER_AGENT", raising=False)
    with pytest.raises(RuntimeError, match="SEC_USER_AGENT"):
        ia._descargar_sec("https://data.sec.gov/submissions/CIK0000320193.json", {"User-Agent": ia._user_agent()})
    monkeypatch.setenv("SEC_USER_AGENT", "Equipo GI analistas")
    visto = {}
    ia.informes_sec("0000320193", lambda u, headers: visto.update(headers) or SUBMISSIONS)
    assert visto["User-Agent"] == "Equipo GI analistas"
    doc = (RAIZ / "docs" / "bot-analistas.md").read_text(encoding="utf-8")
    assert "SEC_USER_AGENT" in doc
