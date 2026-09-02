"""El status "OK" se gana, no se asume.

El 2026-09-02 `commodities_data.json` traía `as_of` de ese día, `status: "OK"` en
WTI y Brent, y las series detenidas el 2026-08-25. Ocho días.

La causa no era FRED: verificado contra la fuente el mismo día, `DCOILWTICO`
tenía observación del 2026-09-01 ($91,48) publicada con un día hábil de rezago, y
la propia `extraer_fred_petroleo` del repo devolvía 30 observaciones hasta esa
fecha. El agujero estaba en el ensamblado:

    "status": "OK"                      # <- valor inicial hardcodeado
    try:
        wti = extraer_fred_petroleo(...)
        if wti:                         # <- si viene vacio, no entra
            historico.update(wti)
            status = "OK"
    except Exception:
        status = "ERROR_STALE"

Una descarga que devuelve vacío sin lanzar no entra al `if`, no toca el
histórico, y deja el status en el "OK" inicial. Semáforo verde sobre datos de la
semana pasada.

El daño no era cosmético: el régimen y el sesgo de WTI/BRENT leían **-7,40 %** en
la ventana de 5 sesiones cuando el movimiento real era **+7,70 %**. Signo
opuesto, y cruza el umbral `oil_signed > 2.0` que separa "NEUTRAL /
CONSOLIDACIÓN" (score 0,0) de "ALCISTA POR SHOCK" (score +1,50).

El Oro ya tenía la disciplina correcta (`else: raise ValueError(...)`), puesta
cuando Stooq empezó a devolver HTML con HTTP 200. Petróleo y Cobre quedaron sin
ella.
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SKILL = RAIZ / ".agents" / "skills" / "ecosistema-datos-macro" / "scripts"
if str(SKILL) not in sys.path:
    sys.path.insert(0, str(SKILL))

ec = pytest.importorskip("extractor_commodities")
pi = pytest.importorskip("pipeline_ingesta")


@pytest.fixture
def aislado(tmp_path, monkeypatch):
    """Redirige la escritura a tmp_path: el extractor sobreescribe el dato real."""
    monkeypatch.setattr(ec, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(ec, "OUTPUT_FILE", tmp_path / "commodities_data.json")
    return tmp_path


def _sin_datos(*_a, **_k):
    """Una descarga que no consigue nada y NO lanza: el caso que pasaba de largo."""
    return {}


def test_una_descarga_vacia_no_deja_el_status_en_ok(aislado, monkeypatch):
    monkeypatch.setattr(ec, "extraer_fred_petroleo", _sin_datos)
    monkeypatch.setattr(ec, "extraer_cobre_hg", _sin_datos)
    monkeypatch.setattr(ec, "extraer_oro_lbma", _sin_datos)
    monkeypatch.setattr(ec, "extraer_oro_fallback", _sin_datos)

    res = ec.ejecutar_extraccion_commodities()

    for serie in ("PETROLEO_WTI", "PETROLEO_BRENT", "COBRE_COMEX", "ORO_SPOT"):
        status = res["commodities"][serie]["status"]
        assert status != "OK", (
            f"{serie} quedó en 'OK' sin haber recibido ni una observación. "
            "Un semáforo verde sobre datos que no se actualizaron es peor que un error."
        )


def test_una_descarga_con_datos_si_gana_el_ok(aislado, monkeypatch):
    """El contrapeso del test anterior: el arreglo no puede dejar todo en rojo."""
    hoy = date.today().isoformat()
    monkeypatch.setattr(ec, "extraer_fred_petroleo", lambda sid: {hoy: 90.0})
    monkeypatch.setattr(ec, "extraer_cobre_hg", lambda: {hoy: 6.6})
    monkeypatch.setattr(ec, "extraer_oro_lbma", lambda: {hoy: 4350.0})

    res = ec.ejecutar_extraccion_commodities()

    for serie in ("PETROLEO_WTI", "PETROLEO_BRENT", "COBRE_COMEX", "ORO_SPOT"):
        assert res["commodities"][serie]["status"].startswith("OK"), serie
        assert hoy in res["commodities"][serie]["historico"], serie


def test_la_cadencia_del_petroleo_refleja_el_rezago_real_de_fred():
    """La ventana estaba en 14 días con el comentario "la EIA llega a FRED con
    rezago propio: se han visto 8 dias corridos".

    Ese diagnóstico era falso y la tolerancia ancha tapaba el bug de arriba.
    Verificado el 2026-09-02 contra fred.stlouisfed.org/series/DCOILWTICO: última
    observación 2026-09-01, un día hábil de rezago, igual que las yields del
    Tesoro. La ventana correcta es la misma que ellas: 6 días, que cubre un fin
    de semana largo sin gritar.
    """
    assert pi.CADENCIA_DIAS["PETROLEO_BRENT"] == 6

    hoy = date(2026, 9, 2)
    hace_8_dias = (hoy - timedelta(days=8)).isoformat()
    assert pi.esta_vencido("PETROLEO_BRENT", hace_8_dias, "OK", hoy=hoy), (
        "una serie de petróleo con 8 días de atraso tiene que marcarse vencida"
    )
    hace_2_dias = (hoy - timedelta(days=2)).isoformat()
    assert not pi.esta_vencido("PETROLEO_BRENT", hace_2_dias, "OK", hoy=hoy)


def test_no_data_es_el_peor_status():
    """`peor_status` ya trataba lo desconocido como lo peor, pero el vocabulario
    tiene que estar declarado: un estado que no figura en la lista depende de un
    fallback para no volverse invisible."""
    assert "NO_DATA" in pi.ORDEN_STATUS
    assert pi.peor_status({"a": {"status": "OK"}, "b": {"status": "NO_DATA"}}) == "NO_DATA"
