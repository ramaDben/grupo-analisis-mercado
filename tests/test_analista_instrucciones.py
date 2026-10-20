"""Las instrucciones de agy dicen lo que el validador exige: un test que los ata."""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import fuentes as fu  # noqa: E402

TEXTO = (RAIZ / ".claude" / "commands" / "analista.md").read_text(encoding="utf-8")


def test_nombra_cada_campo_de_la_fuente():
    for campo in fu.CAMPOS:
        assert f"`{campo}`" in TEXTO


def test_permite_la_web_solo_para_las_fuentes():
    assert "búsqueda web" in TEXTO.lower() or "busca en la web" in TEXTO.lower()
    assert "no uses la web" not in TEXTO.lower()


def test_ya_no_manda_invitar_a_operar_y_lo_prohibe():
    bajo = TEXTO.lower()
    assert "invita a operar el escenario" not in bajo
    assert "nunca invites a operar" in bajo


def test_pide_revisar_la_plataforma_y_no_pone_cifras_de_bancos_sin_atribucion():
    assert "revisar" in TEXTO.lower() and "atribu" in TEXTO.lower()


def test_enumera_las_entidades_de_la_lista_cerrada():
    lista = fu.cargar_lista()
    assert all(e in TEXTO for e in ("Goldman Sachs", "Banco Central de Chile", "Fed"))
    assert len(lista["medios"]) > 10  # la lista real vive en config/fuentes_prestigio.json


def test_la_regla_de_no_operar_dice_lo_que_el_bot_rechaza_de_verdad():
    """El bot rechaza `opera*`, el infinitivo de comprar/vender/entrar y «puede/conviene + verbo»;
    no rechaza "compra" ni "vende" sueltos, así que la regla no puede decir que rechaza "esas formas"."""
    assert "El bot rechaza esas formas" not in TEXTO
    for forma in ('"comprar"', '"vender"', '"entrar"', '"aprovechar"', '"se puede comprar"'):
        assert forma in TEXTO, forma


def test_la_tesis_no_lleva_porcentaje_guion_largo_ni_oportunidad():
    linea = next(x for x in TEXTO.splitlines() if x.strip().startswith("- `tesis`"))
    bajo = linea.lower()
    assert "`%`" in linea and "guion largo" in bajo and "oportunidad" in bajo


def test_manda_citar_los_hechos_del_dia_y_ya_no_el_mecanismo_condicional():
    assert "datos.hechos" in TEXTO and "con_la_lectura" in TEXTO and "en_curso" in TEXTO
    assert "como mecanismo condicional si no hay un hecho medido" not in TEXTO


def test_explica_los_dias_clave():
    assert "dias_clave" in TEXTO and "datos.agenda" in TEXTO and "420" in TEXTO


def test_las_instrucciones_exigen_una_fuente_directa():
    bajo = TEXTO.lower()
    assert "datos.fuente_directa" in TEXTO and "al menos una directa" in bajo and "fuentes_intento_1.json" in TEXTO
    assert "al menos una de un banco" not in bajo
    assert "lista vacía" not in bajo  # ya no se permite entregar fuentes vacías
