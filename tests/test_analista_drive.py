"""Drive ordenado por sector, activo y fecha."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import drive as dr  # noqa: E402


def test_carpeta_por_sector_activo_y_fecha(tmp_path):
    assert dr.carpeta(tmp_path, "XAUUSD", "Oro", date(2026, 10, 23)) == \
        tmp_path / "GI Informes" / "Commodities" / "Oro (XAUUSD)" / "2026-10-23"


def test_par_fuera_del_catalogo_va_a_divisas(tmp_path):
    assert dr.carpeta(tmp_path, "USDCHF", "USD/CHF", date(2026, 10, 23)).parts[-3] == "Divisas"


def test_activo_sin_segmento_va_a_otros(tmp_path):
    assert dr.carpeta(tmp_path, "USDIDX", "Dollar Index", date(2026, 10, 23)).parts[-3] == "Otros"


def test_nombre_con_barra_no_crea_subcarpeta(tmp_path):
    assert dr.carpeta(tmp_path, "USDCLP", "USD/CLP", date(2026, 10, 23)).parts[-2] == "USDCLP (USDCLP)"


def test_dos_laminas_del_mismo_nombre_no_se_pisan(tmp_path):
    a, b = tmp_path / "a.png", tmp_path / "b.png"
    a.write_bytes(b"1")
    b.write_bytes(b"22")
    dr.copiar([(a, "seguimiento.png")], tmp_path / "d")
    dr.copiar([(b, "seguimiento.png")], tmp_path / "d")
    assert sorted(p.name for p in (tmp_path / "d").iterdir()) == ["seguimiento.png", "seguimiento_2.png"]


def test_recopiar_el_mismo_archivo_no_duplica(tmp_path):
    a = tmp_path / "a.png"
    a.write_bytes(b"1")
    dr.copiar([(a, "x.png")], tmp_path / "d")
    dr.copiar([(a, "x.png")], tmp_path / "d")
    assert [p.name for p in (tmp_path / "d").iterdir()] == ["x.png"]
