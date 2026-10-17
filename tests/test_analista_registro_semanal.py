"""El registro por activo: vigencia de 7 días, reúsos, caducidad y seguimientos."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import registro_semanal as rg  # noqa: E402

SCL = ZoneInfo("America/Santiago")
CREADA = datetime(2026, 10, 12, 9, 0, tzinfo=SCL)
CAMILA = {"nombre": "Camila Rojas", "id": "111"}


def _pieza(tmp_path: Path, nombre: str = "a") -> Path:
    d = tmp_path / nombre
    d.mkdir()
    (d / "pieza.json").write_text("{}", encoding="utf-8")
    return d


def _anotar(tmp_path, ticker="XAUUSD", creada=CREADA, nombre="a"):
    ruta = tmp_path / "registro.json"
    d = _pieza(tmp_path, nombre)
    rg.anotar(ticker, d, creada, "ALCISTA", CAMILA, ruta)
    return ruta, d


def test_sin_registro_no_hay_analisis_vigente(tmp_path):
    assert rg.vigente("XAUUSD", CREADA, tmp_path / "registro.json") is None


def test_el_dia_6_se_reusa_y_el_dia_8_se_rehace(tmp_path):
    ruta, d = _anotar(tmp_path)
    assert rg.vigente("XAUUSD", CREADA + timedelta(days=6), ruta)["dir"] == str(d)
    assert rg.vigente("XAUUSD", CREADA + timedelta(days=8), ruta) is None


def test_exactamente_a_los_7_dias_ya_no_se_reusa(tmp_path):
    ruta, _ = _anotar(tmp_path)
    assert rg.vigente("XAUUSD", CREADA + rg.VIGENCIA, ruta) is None


def test_queda_a_nombre_de_quien_lo_genero(tmp_path):
    ruta, _ = _anotar(tmp_path)
    e = rg.vigente("XAUUSD", CREADA, ruta)
    assert e["creado_por"] == CAMILA and e["vence"].startswith("2026-10-19T09:00")
    assert e["reusos"] == [] and e["seguimientos"] == [] and e["caducada"] is None


def test_cada_activo_tiene_su_propia_vigencia(tmp_path):
    ruta, _ = _anotar(tmp_path)
    assert rg.vigente("USDCLP", CREADA, ruta) is None


def test_el_reuso_queda_anotado_con_quien_lo_pidio(tmp_path):
    ruta, _ = _anotar(tmp_path)
    rg.anotar_reuso("XAUUSD", {"nombre": "Pedro Soto", "id": "222"}, CREADA + timedelta(days=2), ruta)
    r = rg.vigente("XAUUSD", CREADA + timedelta(days=2), ruta)["reusos"]
    assert [x["nombre"] for x in r] == ["Pedro Soto"]


def test_un_analisis_caducado_no_se_reusa_aunque_no_hayan_pasado_7_dias(tmp_path):
    ruta, _ = _anotar(tmp_path)
    rg.caducar("XAUUSD", "el precio tocó la invalidación", CREADA + timedelta(days=2), ruta)
    assert rg.vigente("XAUUSD", CREADA + timedelta(days=3), ruta) is None
    e = json.loads(ruta.read_text(encoding="utf-8"))[0]
    assert e["caducada"]["motivo"] == "el precio tocó la invalidación"  # queda como historia


def test_el_analisis_nuevo_reemplaza_al_caducado(tmp_path):
    ruta, _ = _anotar(tmp_path)
    rg.caducar("XAUUSD", "x", CREADA + timedelta(days=2), ruta)
    nueva = _pieza(tmp_path, "b")
    rg.anotar("XAUUSD", nueva, CREADA + timedelta(days=2), "BAJISTA", CAMILA, ruta)
    assert rg.vigente("XAUUSD", CREADA + timedelta(days=3), ruta)["dir"] == str(nueva)


def test_una_carpeta_borrada_no_se_reusa(tmp_path):
    ruta, d = _anotar(tmp_path)
    (d / "pieza.json").unlink()
    assert rg.vigente("XAUUSD", CREADA, ruta) is None


def test_los_seguimientos_quedan_en_la_historia_del_analisis(tmp_path):
    ruta, _ = _anotar(tmp_path)
    rg.anotar_seguimiento("XAUUSD", {"estado": "en_curso", "ejecutivo": "111"}, ruta)
    assert rg.vigente("XAUUSD", CREADA, ruta)["seguimientos"] == [{"estado": "en_curso", "ejecutivo": "111"}]


def test_las_entradas_del_formato_antiguo_se_conservan_y_se_ignoran(tmp_path):
    ruta = tmp_path / "registro.json"
    antigua = {"semana": "2026-W41", "dir": "x", "creada": "2026-10-05T09:00:00-03:00",
               "tickers": ["XAUUSD"], "seguimientos": []}
    ruta.write_text(json.dumps([antigua]), encoding="utf-8")
    assert rg.vigente("XAUUSD", CREADA, ruta) is None
    rg.anotar("XAUUSD", _pieza(tmp_path), CREADA, "ALCISTA", CAMILA, ruta)
    entradas = json.loads(ruta.read_text(encoding="utf-8"))
    assert entradas[0] == antigua and entradas[1]["ticker"] == "XAUUSD"


def test_un_registro_corrupto_no_se_sobrescribe(tmp_path):
    ruta = tmp_path / "registro.json"
    ruta.write_text("{no es json", encoding="utf-8")
    with pytest.raises(rg.RegistroDanado):
        rg.anotar("XAUUSD", _pieza(tmp_path), CREADA, "ALCISTA", CAMILA, ruta)
    assert ruta.read_text(encoding="utf-8") == "{no es json"


def test_sin_el_grafico_en_disco_el_analisis_no_esta_vigente(tmp_path):
    """La ficha necesita el PNG del gráfico: sin él fallaría en cada pedido por 7 días. Se rehace."""
    ruta = tmp_path / "registro.json"
    d = tmp_path / "a"
    d.mkdir()
    (d / "pieza.json").write_text(json.dumps({"imagenes": {"XAUUSD": "grafico_xauusd.png"}}), encoding="utf-8")
    (d / "grafico_xauusd.png").write_bytes(b"png")
    rg.anotar("XAUUSD", d, CREADA, "ALCISTA", CAMILA, ruta)
    assert rg.vigente("XAUUSD", CREADA + timedelta(days=1), ruta) is not None
    (d / "grafico_xauusd.png").unlink()
    assert rg.vigente("XAUUSD", CREADA + timedelta(days=1), ruta) is None
