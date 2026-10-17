"""Contrato de la pieza que agy rellena: solo textos, sin tocar datos ni maqueta."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import esquema as es  # noqa: E402

DATOS = {"precio": "4.110,65", "soporte": "4.098,20", "resistencia": "4.131,00", "fecha_hora": "08/10/2026 09:39"}


def pieza_llena(**editorial) -> dict:
    """La pieza semanal con un activo; `bajada` hace de campo de texto libre en las pruebas."""
    p = es.nueva_pieza("oportunidad", {"semana": "2026-W42"}, dict(DATOS), {"principal": "alerta.png"},
                       extra_campos={"titulares": ["XAUUSD"], "contexto": ["XAUUSD"]})
    p["editorial"] = {"titular": "El oro mantiene presión compradora",
                      "bajada": "El oro mantiene presión compradora mientras siga sobre 4.110,65.",
                      "titulares": {"XAUUSD": "El oro sigue sobre 4.110,65"},
                      "contexto": {"XAUUSD": "El oro mantiene presión compradora mientras siga sobre 4.110,65, "
                                             "y la simulación está en la plataforma."}}
    p["editorial"]["fuentes"] = []
    p["editorial"].update(editorial)
    return p


def test_pieza_nueva_trae_todos_los_campos_sin_escribir():
    p = es.nueva_pieza("oportunidad", {"semana": "2026-W42"}, DATOS, {})
    assert set(p["editorial"]) == set(es.CAMPOS["oportunidad"])
    assert all(v == es.MARCA for v in p["editorial"].values())
    assert es.errores(p)  # sin escribir no pasa


def test_pieza_bien_escrita_pasa():
    assert es.errores(pieza_llena()) == []


def test_campo_sin_escribir():
    errs = es.errores(pieza_llena(titular=es.MARCA))
    assert any("titular" in e and "sin escribir" in e for e in errs)


@pytest.mark.parametrize("texto", ["sube fuerte — ojo", "sube fuerte – ojo"])
def test_guion_largo_o_medio(texto):
    assert es.errores(pieza_llena(bajada=texto))


def test_voseo():
    assert es.errores(pieza_llena(bajada="Si tenés posición, cuidado."))


@pytest.mark.parametrize("texto", ["<b>alza</b>", "ver <img src=x onerror=alert(1)>", "<!-- x -->"])
def test_rechaza_html(texto):
    errs = es.errores(pieza_llena(bajada=texto))
    assert any("HTML" in e for e in errs)


def test_rechaza_cifra_que_no_esta_en_los_datos():
    errs = es.errores(pieza_llena(bajada="El objetivo es 4.200,00."))
    assert any("4.200,00" in e for e in errs)


def test_acepta_cifra_de_los_datos_aunque_cambie_el_formato():
    assert es.errores(pieza_llena(bajada="Sobre 4110,65 sigue arriba.")) == []


def test_acepta_numeros_chicos_sin_decimales():
    assert es.errores(pieza_llena(bajada="Mira las 2 zonas y los 3 escenarios en 15 minutos.")) == []


def test_no_puede_agregar_ni_quitar_campos():
    p = pieza_llena()
    p["editorial"]["extra"] = "hola mundo"
    assert any("extra" in e for e in es.errores(p))
    p = pieza_llena()
    del p["editorial"]["titular"]
    assert any("titular" in e for e in es.errores(p))


def test_no_puede_tocar_los_datos():
    p = pieza_llena()
    p["datos"]["precio"] = "4.200,00"
    assert any("datos" in e for e in es.errores(p))


def test_no_puede_tocar_las_imagenes():
    p = pieza_llena()
    p["imagenes"]["principal"] = "otra.png"
    assert any("datos" in e for e in es.errores(p))


def test_campos_anidados_se_validan_uno_a_uno():
    p = es.nueva_pieza("oportunidad", {"semana": "2026-W42"}, {"activos": []}, {},
                       extra_campos={"contexto": ["1", "2"]})
    for campo in es.CAMPOS["oportunidad"]:
        p["editorial"][campo] = "Texto suficientemente largo para pasar."
    p["editorial"]["fuentes"] = []
    p["editorial"]["contexto"] = {"1": "Explica el activo uno con calma y lo deja a la vista.", "2": es.MARCA}
    errs = es.errores(p)
    assert len(errs) == 1 and "contexto.2" in errs[0]


def test_cada_pieza_tiene_campos():
    """Solo las dos piezas que existen: las retiradas no dejan campos muertos."""
    assert set(es.CAMPOS) == {"oportunidad", "seguimiento"}


def test_titular_largo_no_cabe_en_la_lamina():
    errs = es.errores(pieza_llena(titular="El oro " * 15))
    assert any("titular" in e and "máximo" in e for e in errs)


def test_no_puede_tocar_las_laminas():
    p = es.nueva_pieza("oportunidad", {"semana": "2026-W42"}, {"activos": []}, {},
                       laminas={"lamina.png": {"titular": es.MARCA}})
    for campo in es.CAMPOS["oportunidad"]:
        p["editorial"][campo] = "Texto suficientemente largo para pasar."
    p["editorial"]["fuentes"] = []
    assert es.errores(p) == []
    p["laminas"]["lamina.png"]["titular"] = "otra cosa"
    assert any("datos" in e for e in es.errores(p))


# ───────────────────────────────────────────── candados de lenguaje


@pytest.mark.parametrize("texto", [
    "Es momento de comprar oro.", "Te recomiendo vender.", "Abre una posición larga.",
    "Toma ganancias en la resistencia.", "Usa 2 lotes.", "Recomendamos esperar.",
    "Señal de compra clara.", "Deberías vender ya.", "No arriesgues más del 2 % de tu capital.",
    "Compra ya antes del dato.", "Cierra tu posición antes del cierre.",
    "Arriesga tu capital solo si confirmas.", "Apalancate para aprovechar el quiebre.",
])
def test_frases_prohibidas_caen(texto):
    assert es.frases_prohibidas(texto)


@pytest.mark.parametrize("texto", [
    "El índice de gerentes de compra (PMI) sube.",
    "Si rompe un borde y vuelve a entrar, es falso quiebre.",
    "El escenario alcista se activa sobre la resistencia.",
    "Hay presión compradora.",
    "Los vendedores dominan la sesión.",
    "La lotería no es una estrategia.",
    "No conviene arriesgar más de lo previsto.",
    "El apalancamiento amplifica las pérdidas.",
])
def test_formas_impersonales_pasan(texto):
    assert es.frases_prohibidas(texto) == []


def test_errores_reporta_la_frase():
    errs = es.errores(pieza_llena(bajada="Te recomiendo no perseguir el precio."))
    assert any("te recomiendo" in x for x in errs)


def test_el_texto_no_nombra_a_la_cmf():
    errs = es.errores(pieza_llena(bajada="Este análisis está regulado por la CMF."))
    assert any("CMF" in x for x in errs)


# ───────────────────────────────────────────────────────────── pieza semanal


@pytest.mark.parametrize("frase", [
    "No te lo pierdas: el oro está listo.", "Es la última oportunidad de la semana.",
    "Aprovecha el impulso.", "Una ganancia asegurada.", "Es una ganancia segura.",
    "Una oportunidad única.", "Esta condición acierta casi siempre.", "Tiene buena efectividad.",
    "Se cumplió la mitad de las veces.", "Su tasa de éxito es alta.", "Sube un 2% en el día.",
])
def test_la_semanal_bloquea_captacion_y_estadistica(tmp_path, frase):
    p = fx.pieza_oportunidad(tmp_path)
    p["editorial"]["contexto"]["XAUUSD"] = frase
    assert any("contexto.XAUUSD" in x for x in es.errores(p))


def test_la_semanal_usa_sus_frases_prohibidas():
    assert "oportunidad" in es.FRASES_PROHIBIDAS_SEMANAL


def test_la_semanal_deja_pasar_el_texto_legitimo(tmp_path):
    assert es.errores(fx.pieza_oportunidad(tmp_path)) == []


def test_la_semanal_no_escribe_oportunidad(tmp_path):
    p = fx.pieza_oportunidad(tmp_path)
    p["editorial"]["titular"] = "Una oportunidad para los compradores del oro"
    assert any("titular" in x for x in es.errores(p))


def test_oportunidad_exige_titular_por_activo_de_hasta_70():
    p = es.nueva_pieza("oportunidad", {}, {"activos": []}, {},
                       extra_campos={"titulares": ["XAUUSD"], "contexto": ["XAUUSD"]})
    p["editorial"] = {"titular": "La semana técnica", "bajada": "Seis activos con su lectura.",
                      "titulares": {"XAUUSD": "x" * 71}, "contexto": {"XAUUSD": "Texto."}}
    assert any("titulares.XAUUSD" in e and "70" in e for e in es.errores(p))


def test_oportunidad_rechaza_la_palabra_oportunidad_y_porcentajes():
    p = es.nueva_pieza("oportunidad", {}, {"activos": []}, {},
                       extra_campos={"titulares": ["XAUUSD"], "contexto": ["XAUUSD"]})
    p["editorial"] = {"titular": "Una oportunidad en el oro", "bajada": "Sube 2 %",
                      "titulares": {"XAUUSD": "Oro"}, "contexto": {"XAUUSD": "Texto."}}
    errs = es.errores(p)
    assert any("oportunidad" in e for e in errs) and any("porcentaje" in e for e in errs)


def test_el_contexto_no_puede_invitar_a_operar(tmp_path):
    p = fx.pieza_oportunidad(tmp_path)
    for frase in ("El escenario se puede operar si el precio respeta la línea.", "Conviene operarlo con stop.",
                  "Es un nivel operable.", "Opera el rebote."):
        p["editorial"]["contexto"]["XAUUSD"] = f"Contexto. {frase}"
        errs = es.errores(p)
        assert any("invita a operar" in e for e in errs), frase


def test_el_contexto_sin_invitacion_pasa(tmp_path):
    assert es.errores(fx.pieza_oportunidad(tmp_path)) == []


def test_las_fuentes_se_exigen_como_lista(tmp_path):
    p = fx.pieza_oportunidad(tmp_path)
    p["editorial"]["fuentes"] = "texto suelto"
    assert any("fuentes" in e for e in es.errores(p))
    p["editorial"]["fuentes"] = es.MARCA
    assert any("sin escribir" in e.lower() or "fuentes" in e for e in es.errores(p))
    p["editorial"]["fuentes"] = []  # sin voces es válido: se avisa, no se rellena
    assert es.errores(p) == []


def test_una_fuente_con_postura_o_campos_rotos_se_rechaza(tmp_path):
    p = fx.pieza_oportunidad(tmp_path)
    p["editorial"]["fuentes"] = [{**fx.FUENTES_EJEMPLO[0], "postura": "muy alcista"}]
    assert any("fuentes.0" in e for e in es.errores(p))
    p["editorial"]["fuentes"] = [{"entidad": "UBS"}]
    assert any("fuentes.0" in e for e in es.errores(p))


def test_la_tesis_de_una_fuente_pasa_por_los_mismos_candados_de_texto(tmp_path):
    p = fx.pieza_oportunidad(tmp_path)
    p["editorial"]["fuentes"][0]["tesis"] = "Goldman — ve el oro alcista."
    assert any("fuentes.0.tesis" in e for e in es.errores(p))


def test_una_cifra_de_tercero_atribuida_en_la_misma_frase_pasa(tmp_path):
    p = fx.pieza_oportunidad(tmp_path)
    p["editorial"]["contexto"]["XAUUSD"] = "Contexto. Goldman Sachs ve el oro en 4.800 dólares, y nuestra lectura es distinta."
    assert es.errores(p) == []


def test_una_cifra_de_tercero_sin_atribucion_se_rechaza(tmp_path):
    p = fx.pieza_oportunidad(tmp_path)
    p["editorial"]["contexto"]["XAUUSD"] = "Contexto. El oro llegaría a 4.800 dólares."
    assert any("4.800" in e for e in es.errores(p))


def test_la_cifra_atribuida_a_otra_entidad_se_rechaza(tmp_path):
    p = fx.pieza_oportunidad(tmp_path)
    p["editorial"]["contexto"]["XAUUSD"] = "Contexto. UBS ve el oro en 4.800 dólares."
    assert any("4.800" in e for e in es.errores(p))


def test_una_cifra_inventada_nunca_pasa_aunque_se_atribuya(tmp_path):
    p = fx.pieza_oportunidad(tmp_path)
    p["editorial"]["contexto"]["XAUUSD"] = "Contexto. Goldman Sachs ve el oro en 9.999 dólares."
    assert any("9.999" in e for e in es.errores(p))


# ───────────────────────────────────────────── invitación a comprar o vender (fix final)


@pytest.mark.parametrize("frase", [
    "El oro se puede comprar en la caída.", "Conviene vender el rebote.", "Pueden vender en la resistencia.",
    "Es buen momento para comprarlo.", "Hay que aprovechar el quiebre.", "Es mejor entrar tras el cierre.",
    "Lo ideal es venderlo en la resistencia.",
])
def test_el_texto_no_invita_a_comprar_ni_vender(tmp_path, frase):
    p = fx.pieza_oportunidad(tmp_path)
    p["editorial"]["contexto"]["XAUUSD"] = f"Contexto. {frase}"
    assert any("contexto.XAUUSD" in e and "invita" in e for e in es.errores(p)), frase


@pytest.mark.parametrize("frase", [
    "El índice de gerentes de compra (PMI) sube.", "La nueva norma entra en vigor el lunes.",
    "Hay presión compradora y los vendedores retroceden.",
])
def test_las_palabras_vecinas_de_comprar_no_se_bloquean(tmp_path, frase):
    p = fx.pieza_oportunidad(tmp_path)
    p["editorial"]["contexto"]["XAUUSD"] = f"Contexto. {frase}"
    assert es.errores(p) == [], frase


def test_la_tesis_que_recomienda_comprar_se_detecta():
    assert es.errores_tesis("Goldman Sachs recomienda comprar oro por la demanda de bancos centrales.")


def test_la_tesis_limpia_no_tiene_errores():
    assert es.errores_tesis(fx.FUENTES_EJEMPLO[0]["tesis"]) == []


def test_una_tesis_rota_descarta_solo_su_fuente(tmp_path):
    p = fx.pieza_oportunidad(tmp_path)
    rota = {**fx.FUENTES_EJEMPLO[0], "entidad": "UBS", "tesis": "UBS ve un alza de 5% en el oro."}
    p["editorial"]["fuentes"] = [dict(fx.FUENTES_EJEMPLO[0]), rota]
    p, descartes = es.descartar_tesis_rotas(p)
    assert [f["entidad"] for f in p["editorial"]["fuentes"]] == ["Goldman Sachs"]
    assert len(descartes) == 1 and descartes[0].startswith("UBS: ")
    assert es.errores(p) == []


# ───────────────────────────────────────────── atribución por palabra completa (fix final)


def test_la_entidad_dentro_de_otra_palabra_no_atribuye_la_cifra(tmp_path):
    ubs = {**fx.FUENTES_EJEMPLO[0], "entidad": "UBS", "tesis": "UBS ve el oro en 4.800 dólares."}
    p = fx.pieza_oportunidad(tmp_path, fuentes=[ubs])
    p["editorial"]["contexto"]["XAUUSD"] = "Contexto. Los subsidios llevarían el oro a 4.800 dólares."
    assert any("4.800" in e for e in es.errores(p))


def test_la_entidad_como_palabra_completa_atribuye_la_cifra(tmp_path):
    ubs = {**fx.FUENTES_EJEMPLO[0], "entidad": "UBS", "tesis": "UBS ve el oro en 4.800 dólares."}
    p = fx.pieza_oportunidad(tmp_path, fuentes=[ubs])
    p["editorial"]["contexto"]["XAUUSD"] = "Contexto. UBS ve el oro en 4.800 dólares."
    assert es.errores(p) == []
