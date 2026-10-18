"""El mapa de la semana y la víspera: Python puro sobre el calendario y el glosario, sin IA ni red."""
from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from analista import semana as sm  # noqa: E402
from market_data_mcp.tools.calendar import _cargar_glosario, _enganchar_glosario  # noqa: E402

SCL = ZoneInfo("America/Santiago")
LUNES = datetime(2026, 10, 19, 7, 45, tzinfo=SCL)
GLOSARIO = _cargar_glosario()
PROHIBIDAS = re.compile(r"\b(compra\w*|vende\w*|oportunidad\w*|cobertura\w*)\b", re.IGNORECASE)


def ev(nombre, hora="2026-10-21 09:30", pais="United States", impacto="alto", glosario=True):
    e = {"nombre": nombre, "pais": pais, "impacto": impacto, "hora_servidor": hora, "forecast": "", "previo": "",
         "actual": ""}
    entrada = _enganchar_glosario(nombre, GLOSARIO) if glosario else None
    if entrada:
        e["diccionario"] = entrada
    else:
        e["glosario_pendiente"] = True
    return e


FOMC = ev("Fed Interest Rate Decision", "2026-10-21 15:00")
CPI = ev("CPI (MoM) (Sep)", "2026-10-22 09:30")
NFP = ev("Nonfarm Payrolls (Sep)", "2026-10-23 09:30")
PMI = ev("ISM Manufacturing PMI (Sep)", "2026-10-22 11:00")
CRUDO = ev("Crude Oil Inventories", "2026-10-21 12:30")


# ───────────────────────────────────────────── tipo y tema


@pytest.mark.parametrize("evento,tipo", [(FOMC, "tasas"), (CPI, "inflacion"), (NFP, "empleo"), (PMI, "actividad"),
                                          (CRUDO, "petroleo"),
                                          (ev("Chile Interest Rate Decision", pais="Chile"), "tasas"),
                                          (ev("Core PCE Price Index (MoM)"), "inflacion"),
                                          (ev("Imacec (YoY) (Aug)", pais="Chile"), "actividad")])
def test_tipo_de_evento(evento, tipo):
    assert sm.tipo_de_evento(evento) == tipo


def test_un_evento_sin_glosario_no_tiene_tipo():
    assert sm.tipo_de_evento(ev("Nonfarm Payrolls (Sep)", glosario=False)) is None


def test_productividad_no_es_empleo():
    assert sm.tipo_de_evento(ev("Nonfarm Productivity (QoQ)")) is None


@pytest.mark.parametrize("eventos,tipo", [
    ([FOMC, CPI, NFP], "tasas"),                 # empate de tier 1: manda la decisión de tasas
    ([CPI, NFP], "inflacion"),                    # empate: inflación sobre empleo
    ([NFP], "empleo"),
    ([PMI], "actividad"),                         # solo PMI: tier 2 igual es tema
    ([PMI, NFP], "empleo"),                       # el tier manda sobre la precedencia
    ([PMI, CRUDO], "actividad"),                  # empate de tier 2: actividad sobre petróleo
    ([CRUDO], "petroleo"),
])
def test_tema_de_la_semana(eventos, tipo):
    t = sm.tema_de_la_semana(eventos)
    assert t["tipo"] == tipo and not t["tranquila"]
    assert t["titular"].startswith("Semana de ")


@pytest.mark.parametrize("eventos", [[], [ev("Fed Waller Speaks")], [ev("Nonfarm Payrolls (Sep)", glosario=False)],
                                      [ev("Imports (Aug)")]])
def test_semana_tranquila_sin_dato_fuerte(eventos):
    t = sm.tema_de_la_semana(eventos)
    assert t["tranquila"] and t["tipo"] is None and t["titular"] == "Semana tranquila"


def test_las_series_semanales_solo_mandan_si_no_hay_nada_mas():
    reclamos = ev("Initial Jobless Claims", "2026-10-22 09:30")
    assert sm.tema_de_la_semana([reclamos, PMI])["tipo"] == "actividad"
    assert sm.tema_de_la_semana([CRUDO, PMI])["tipo"] == "actividad"
    assert sm.tema_de_la_semana([reclamos])["tipo"] == "empleo"


# ───────────────────────────────────────────── el mapa


def test_mapa_de_una_semana_con_tasas():
    texto = sm.armar_mapa([FOMC, CPI, NFP, PMI], LUNES)
    assert texto.splitlines()[0] == "📅 Semana de tasas"
    assert "miércoles 21/10 · 15:00 CLST" in texto
    assert "jueves 22/10 · 09:30 CLST" in texto
    assert "💬 Qué conversar:" in texto
    assert sm.AVISO_RIESGO in texto
    assert sm.guia()["tasas"]["conversar"] in texto


def test_el_mapa_lista_entre_tres_y_cinco_eventos_cuando_hay_de_sobra():
    muchos = [ev("ISM Manufacturing PMI (Sep)", f"2026-10-2{d} 11:00") for d in range(0, 6)] + [FOMC, CPI, NFP]
    lineas = [x for x in sm.armar_mapa(muchos, LUNES).splitlines() if x.startswith("• ")]
    assert 3 <= len(lineas) <= 5


def test_la_sigla_se_explica_una_vez_y_en_castellano():
    texto = sm.armar_mapa([CPI], LUNES)
    assert "Índice de precios al consumidor (IPC) de EE.UU." in texto
    assert "CPI" not in texto


def test_mapa_que_cruza_el_cambio_de_horario_etiqueta_cada_evento_con_su_hora():
    # Chile pasa a horario de invierno el domingo 2027-04-04: el viernes es CLST y el lunes CLT.
    antes = ev("Nonfarm Payrolls (Mar)", "2027-04-02 09:30")
    despues = ev("CPI (MoM) (Mar)", "2027-04-05 09:30")
    texto = sm.armar_mapa([antes, despues], datetime(2027, 3, 29, 7, 45, tzinfo=SCL))
    assert "viernes 02/04 · 09:30 CLST" in texto
    assert "lunes 05/04 · 09:30 CLT" in texto


def test_sin_linea_de_efecto_si_el_glosario_no_la_tiene():
    sin_efecto = ev("Imacec (YoY) (Aug)", pais="Chile")
    sin_efecto["diccionario"] = {k: v for k, v in sin_efecto["diccionario"].items() if k != "si_sale_sobre_consenso"}
    texto = sm.armar_mapa([sin_efecto], LUNES)
    assert "mueve:" not in texto


def test_el_efecto_de_un_dato_chileno_con_entrada_estadounidense_no_se_afirma():
    # «CPI» en Chile engancha con la entrada de EE.UU. (dólar sube): esa lectura no vale para un dato chileno.
    chile = ev("CPI (MoM) (Sep)", pais="Chile")
    assert "mueve:" not in sm.armar_mapa([chile], LUNES)


def test_el_efecto_de_un_dato_de_china_o_la_zona_euro_no_se_afirma():
    # Las entradas del glosario (PIB, PMI) describen a EE.UU.: aplicarlas a otro país sería inventar el efecto.
    for pais in ("China", "Euro Zone"):
        assert "mueve:" not in sm.armar_mapa([ev("GDP (QoQ) (Q3)", pais=pais)], LUNES)


def test_mapa_de_semana_tranquila():
    texto = sm.armar_mapa([], LUNES)
    assert texto.splitlines()[0] == "📅 Semana tranquila"
    assert sm.AVISO_RIESGO in texto


# ───────────────────────────────────────────── la víspera


def test_vispera_tiene_a_lo_mas_cinco_lineas_y_el_aviso():
    texto = sm.armar_vispera(CPI, datetime(2026, 10, 21, 16, 0, tzinfo=SCL))
    lineas = [x for x in texto.splitlines() if x.strip()]
    assert len(lineas) <= 5 and lineas[-1] == sm.AVISO_RIESGO
    assert "Mañana a las 09:30 CLST" in lineas[0]
    assert "Si sale sobre lo esperado" in texto
    assert sm.guia()["inflacion"]["no_decir"] in texto


def test_vispera_del_viernes_para_un_dato_del_lunes_dice_el_dia():
    texto = sm.armar_vispera(ev("CPI (MoM) (Sep)", "2026-10-26 09:30"), datetime(2026, 10, 23, 16, 0, tzinfo=SCL))
    assert "El lunes 26/10 a las 09:30 CLST" in texto


def test_el_activo_mas_afectado():
    assert sm.activo_mas_afectado(CPI) == "USDCLP"
    assert sm.activo_mas_afectado(CRUDO) == "WTI.spot"
    assert sm.activo_mas_afectado(ev("Fed Waller Speaks")) is None


# ───────────────────────────────────────────── reglas de texto de todo lo que sale


@pytest.mark.parametrize("texto", [
    sm.armar_mapa([FOMC, CPI, NFP, PMI, CRUDO], LUNES), sm.armar_mapa([], LUNES),
    sm.armar_vispera(FOMC, datetime(2026, 10, 20, 16, 0, tzinfo=SCL)),
    sm.armar_vispera(CRUDO, datetime(2026, 10, 20, 16, 0, tzinfo=SCL)),
])
def test_ningun_texto_trae_guion_largo_ni_palabras_de_asesoria(texto):
    assert "—" not in texto and "–" not in texto
    # «Índice de gerentes de compra» es el nombre del PMI, no una orden.
    limpio = texto.replace("gerentes de compra", "gerentes")
    assert not PROHIBIDAS.search(limpio), PROHIBIDAS.search(limpio).group(0)
