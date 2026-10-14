"""Láminas y textos de WhatsApp de la pieza semanal."""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import comercial as cm  # noqa: E402


def test_la_lamina_semanal_muestra_el_analisis_y_no_la_simulacion(tmp_path):
    a = fx.activo_semanal()
    p = cm.payload_semanal(a, "El oro sigue con la línea bajista a favor", "lunes 12-10 · 09:05 CLST",
                           fx.AUTOR, tmp_path / "g.png")
    assert [n["valor"] for n in p["niveles"]] == ["4.227,32", "4.149,96"]  # vigilar y objetivo de Tori
    assert "4.062,72" not in json.dumps(p, ensure_ascii=False)       # el 1:3 no va en el análisis
    assert "recorrido" not in p                                        # clave reservada de story_render
    assert p["firma"].endswith("Dirección de Análisis Técnico")


def test_la_lamina_de_rango_nombra_los_bordes(tmp_path):
    a = fx.activo_semanal(rango=True)
    p = cm.payload_semanal(a, "El cobre sigue dentro de su rango", "lunes 12-10", fx.AUTOR, tmp_path / "g.png")
    assert [n["rotulo"] for n in p["niveles"]][1] == "Soporte del rango"
    assert p["niveles"][0]["rotulo"].startswith("Resistencia del rango")


def test_el_texto_base_de_whatsapp_sigue_las_reglas_de_formato():
    t = cm.texto_whatsapp_base(fx.activo_semanal(), "El oro sigue con la línea bajista a favor",
                               "La semana trae el dato de inflación de EE.UU.")
    lineas = t.splitlines()
    assert lineas[0].startswith("🎯 Activo:") and lineas[1].startswith("📌 Nivel a vigilar:")
    assert lineas[2].startswith("⚡ Qué esperar:")
    assert "━━━━━━━━━━━━━━━━━━━" in t and "⏱️ *Temporalidad*" in t
    assert cm.AVISO_PIEZA in t
    for prohibida in ("oportunidad", "recomendaci", "—", "–"):
        assert prohibida not in t.lower()


def test_la_lamina_de_seguimiento_no_lleva_pesos(tmp_path):
    p = cm.payload_seguimiento(fx.activo_semanal(), {"estado": "en_curso", "avance_pct": 40}, 4120.0,
                               "La lectura del lunes sigue en pie.", "miércoles 14-10", fx.AUTOR,
                               tmp_path / "g.png")
    assert p["sello"] == "EN CURSO" and "$" not in json.dumps(p, ensure_ascii=False)
    assert "recorrido" not in p


def test_la_lamina_de_entrada_pendiente_fuera_del_rango_no_dice_que_no_llega(tmp_path):
    p = cm.payload_seguimiento(fx.activo_semanal(rango=True), {"estado": "entrada_pendiente", "avance_pct": None},
                               14593.0, "La lectura del lunes sigue en pie.", "lunes 12/10", fx.AUTOR,
                               tmp_path / "g.png")
    assert "no llega" not in p["avance"] and "rango" in p["avance"]


def test_la_lamina_en_contra_no_lleva_avance_negativo(tmp_path):
    p = cm.payload_seguimiento(fx.activo_semanal(), {"estado": "en_curso", "avance_pct": -12}, 4190.0,
                               "La lectura del lunes sigue en pie.", "lunes 12/10", fx.AUTOR, tmp_path / "g.png")
    assert "-" not in p["avance"] and "en contra" in p["avance"]


def test_la_lamina_de_seguimiento_sin_simulacion(tmp_path):
    from analista import oportunidad as op

    a = fx.activo_semanal()
    a["escenario"] = op.escenario(fx.lectura(invalidacion=None), 2).a_dict()
    p = cm.payload_seguimiento(a, {"estado": "sin_simulacion", "avance_pct": None,
                                   "motivo": "el gráfico no marca un nivel claro donde el análisis dejaría de valer, y sin ese nivel no hay dónde poner el stop"},
                               4190.0, "La lectura del lunes sigue en pie.", "lunes 12/10", fx.AUTOR,
                               tmp_path / "g.png")
    assert p["sello"] == "SIN SIMULACIÓN" and p["direccion"] == "bajista"
    assert "no tiene simulación" in p["avance"] and p["niveles"] == ""


def test_dos_niveles_con_el_mismo_precio_se_funden_en_una_fila(tmp_path):
    """Oro W41: «Nivel a vigilar» e «Invalidación» eran el mismo 4.227,32; cobre: la resistencia
    del rango era también la que se vigila."""
    oro = cm.payload_semanal(fx.activo_semanal(), "t", "lunes 12/10", fx.AUTOR, tmp_path / "g.png")["niveles"]
    assert [(n["rotulo"], n["valor"]) for n in oro] == [("Nivel a vigilar · Se anula si cierra sobre", "4.227,32"),
                                                         ("Objetivo", "4.149,96")]
    cobre = cm.payload_semanal(fx.activo_semanal(rango=True), "t", "lunes 12/10", fx.AUTOR,
                               tmp_path / "g.png")["niveles"]
    assert [(n["rotulo"], n["valor"]) for n in cobre] == [("Resistencia del rango · Nivel a vigilar", "14567"),
                                                           ("Soporte del rango", "14206")]
