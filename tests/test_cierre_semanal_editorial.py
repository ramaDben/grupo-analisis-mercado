"""El texto del cierre semanal se escribe cada semana y el render no sale a medias.

Hasta el 2026-10-12 el texto vivía en `cierre_semanal_contenido.py` y era el de la
semana del 11 de septiembre: cada cierre posterior lo republicaba con la fecha del día.
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
for p in (str(RAIZ / "scripts"), str(RAIZ / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

import cierre_semanal_contenido as C  # noqa: E402
import compilar_informe_cierre_semanal as comp  # noqa: E402

DATOS = {
    "activos": [{"slug": "usdclp"}, {"slug": "wti"}],
    "filas_curva": [{"codigo": "DGS2"}, {"codigo": "DGS10"}],
}


def _lleno() -> dict:
    ed = C.plantilla_editorial(DATOS)

    def llenar(nodo):
        if isinstance(nodo, dict):
            return {k: (v if k.startswith("_") else llenar(v)) for k, v in nodo.items()}
        if isinstance(nodo, list):
            return [llenar(v) for v in nodo]
        return "texto" if nodo == "" else nodo

    ed = llenar(ed)
    for esc, prob in zip(ed["escenarios"], (30, 50, 20)):
        esc["prob"] = prob
    return ed


def test_la_plantilla_sale_de_los_datos_y_no_de_una_lista_fija():
    ed = C.plantilla_editorial(DATOS)
    assert set(ed["activos"]) == {"usdclp", "wti"}
    assert set(ed["notas_portada"]) == {"usdclp", "wti"}
    assert set(ed["curva"]["diagnostico"]) == {"DGS2", "DGS10"}
    assert [e["clase"] for e in ed["escenarios"]] == ["pos", "base", "risk"]


def test_la_plantilla_vacia_tiene_todo_pendiente():
    problemas = C.problemas_editorial(C.plantilla_editorial(DATOS), DATOS)
    assert "portada.titulo: vacío" in problemas
    assert "activos.wti.prohibido: vacío" in problemas
    assert "curva.diagnostico.DGS10: vacío" in problemas
    assert any(p.startswith("escenarios.prob") for p in problemas)


def test_un_editorial_completo_pasa():
    assert C.problemas_editorial(_lleno(), DATOS) == []


def test_el_guion_largo_se_rechaza():
    ed = _lleno()
    ed["portada"]["bajada"] = "El petróleo subió — y mucho."
    assert "portada.bajada: trae guion largo" in C.problemas_editorial(ed, DATOS)


def test_las_probabilidades_suman_cien():
    ed = _lleno()
    ed["escenarios"][0]["prob"] = 40
    assert "escenarios.prob: suman 110 y deben sumar 100" in C.problemas_editorial(ed, DATOS)


def test_un_activo_sin_ficha_se_nombra():
    ed = _lleno()
    del ed["activos"]["wti"]
    assert "activos.wti: falta la ficha" in C.problemas_editorial(ed, DATOS)


def test_un_marcador_desconocido_se_rechaza():
    ed = _lleno()
    ed["activos"]["usdclp"]["pasando"] = "Cerró en {cierre}."
    assert any("marcador inválido" in p for p in C.problemas_editorial(ed, DATOS))


def test_exigir_lanza_con_todos_los_problemas_juntos():
    with pytest.raises(ValueError) as exc:
        C.exigir_editorial(C.plantilla_editorial(DATOS), DATOS)
    assert "portada.titulo" in str(exc.value) and "activos.wti.pasando" in str(exc.value)


def test_completar_no_pisa_lo_escrito_y_suma_lo_nuevo():
    ed = _lleno()
    del ed["activos"]["wti"]
    datos = copy.deepcopy(DATOS)
    resultado = comp.completar_editorial(ed, datos)
    assert resultado["activos"]["usdclp"]["pasando"] == "texto"
    assert resultado["activos"]["wti"] == {"pasando": "", "prohibido": ""}
    assert resultado["portada"]["titulo"] == "texto"


def test_rendir_se_detiene_con_el_editorial_vacio(tmp_path):
    import json

    datos = {**DATOS, "fecha_corta": "2026-10-16"}
    (tmp_path / comp.DATOS_JSON).write_text(json.dumps(datos), encoding="utf-8")
    (tmp_path / comp.EDITORIAL_JSON).write_text(
        json.dumps(C.plantilla_editorial(DATOS)), encoding="utf-8")
    with pytest.raises(ValueError, match="incompleto"):
        comp.rendir(tmp_path)
    assert not list(tmp_path.glob("*.pdf"))
