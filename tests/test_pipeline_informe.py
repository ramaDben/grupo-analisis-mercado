"""Contrato del informe: la regla de frescura, las tablas y el idioma.

Sin red y sin Playwright: se prueban las decisiones (cuándo NO se emite, qué dice
una tabla sin datos, cómo se nombra un indicador), no la maqueta del PDF.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

import pipeline_informe as pi  # noqa: E402


# ─────────────────────────────────────────────────────────────────────────────
# La regla de frescura
# ─────────────────────────────────────────────────────────────────────────────
def test_la_apertura_no_se_emite_sin_sesgo_del_playbook(monkeypatch):
    """Un PDF institucional sin régimen ni sesgo se cita después como si fuera de
    hoy. El freno es explícito y nombra el remedio."""
    monkeypatch.setattr(pi, "_playbook", lambda: ({}, ["sesgo no disponible (STALE_DATA)"]))
    monkeypatch.setattr(pi, "_curva", lambda: ({}, []))
    monkeypatch.setattr(pi, "_calendario", lambda ahora: ([], []))

    with pytest.raises(SystemExit) as exc:
        pi.preparar("apertura")
    mensaje = str(exc.value)
    assert "NO se emite" in mensaje
    assert "pipeline_ingesta.py" in mensaje, "el error tiene que nombrar el remedio"
    assert "--con-datos-viejos" in mensaje, "y la salida explicita"


def test_con_datos_viejos_si_emite_pero_estampa_el_aviso(monkeypatch, tmp_path):
    """La decisión de publicar con datos vencidos es del director; que el lector
    lo sepa, no."""
    monkeypatch.setattr(pi, "DIR_TRABAJO", tmp_path)
    monkeypatch.setattr(pi, "_playbook", lambda: ({}, ["stale"]))
    monkeypatch.setattr(pi, "_curva", lambda: ({}, []))
    monkeypatch.setattr(pi, "_calendario", lambda ahora: ([], []))

    res = pi.preparar("apertura", con_datos_viejos=True)
    texto = Path(res["markdown"]).read_text(encoding="utf-8")
    assert "Aviso de frescura" in texto
    assert "sin el sesgo cuantitativo del Motor GI" in texto
    assert "ninguna cifra de este documento debe leerse como lectura del motor" in texto


def test_el_cierre_no_exige_el_playbook_porque_no_lleva_pdf(monkeypatch, tmp_path):
    """El cierre es chat-first por criterio de canal, así que no arrastra la
    exigencia del informe institucional."""
    monkeypatch.setattr(pi, "DIR_TRABAJO", tmp_path)
    monkeypatch.setattr(pi, "_playbook", lambda: ({}, ["stale"]))
    monkeypatch.setattr(pi, "_curva", lambda: ({}, []))
    monkeypatch.setattr(pi, "_calendario", lambda ahora: ([], []))

    res = pi.preparar("cierre")
    assert res["canal"].startswith("chat-first")


def test_rendir_se_niega_si_quedan_secciones_sin_escribir(tmp_path):
    md = tmp_path / "informe_apertura.md"
    md.write_text(f"## 01\n\n{pi.MARCA_EDITORIAL} falta esto\n", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        pi.rendir(tmp_path, "apertura")
    assert pi.MARCA_EDITORIAL in str(exc.value)


def test_el_cierre_escrito_no_produce_pdf(tmp_path):
    """Decisión de canal: un PDF al día, no dos."""
    md = tmp_path / "informe_cierre.md"
    md.write_text("## 01\n\nTexto completo del cierre.\n", encoding="utf-8")
    res = pi.rendir(tmp_path, "cierre")
    assert res["canal"] == "chat-first"
    assert "pdf" not in res


# ─────────────────────────────────────────────────────────────────────────────
# Las tablas: una ausencia declarada, no una tabla vacía
# ─────────────────────────────────────────────────────────────────────────────
def test_la_curva_sin_series_dice_que_no_hay_dato_en_vez_de_quedar_vacia():
    """Una tabla con solo encabezado se lee como "no se movió nada", que es una
    afirmación falsa."""
    salida = pi._tabla_curva({})
    assert "no disponible" in salida
    assert "pipeline_ingesta.py" in salida
    assert "|---|" not in salida


def test_un_delta_nulo_se_muestra_como_sin_dato_y_nunca_como_cero():
    """`null` y `0` son afirmaciones distintas: cero es "no se movió"."""
    curva = {"series": {"DGS10": {
        "nombre": "Tesoro 10 años", "nivel_pct": 4.74,
        "delta_1d_bps": None, "delta_5d_bps": 5.0, "fecha_dato": "2026-08-21",
    }}}
    salida = pi._tabla_curva(curva)
    assert "sin dato" in salida
    assert "+5 puntos base" in salida
    assert "+0 puntos base" not in salida
    assert "bps" not in salida, "bps es taquigrafia de mesa, no va a un cliente"


def test_el_playbook_sin_activos_declara_la_ausencia():
    assert "no disponible" in pi._tabla_playbook({})


# ─────────────────────────────────────────────────────────────────────────────
# Idioma: el informe lo lee un cliente en español
# ─────────────────────────────────────────────────────────────────────────────
def test_los_paises_de_la_fuente_se_traducen():
    eventos = [{"hora_servidor": "2026-08-25 10:00", "pais": "United States",
                "nombre": "X", "impacto": "alto"}]
    assert "EE.UU." in pi._tabla_calendario(eventos)
    assert "United States" not in pi._tabla_calendario(eventos)


def test_el_indicador_usa_el_nombre_en_espanol_y_descarta_el_de_la_fuente():
    """No se traduce a mano: el calendario ya engancha `glosario_siglas.json`.

    El nombre en ingles se descarta y no se arrastra entre parentesis: en un
    informe en espanol es ruido con el que el lector tiene que lidiar antes de
    llegar a la hora y al impacto, que es lo unico que iba a mirar.
    """
    ev = {"nombre": "ADP Employment Change Weekly",
          "diccionario": {"nombre_es": "Empleo privado ADP"}}
    assert pi._nombre_indicador(ev) == "Empleo privado ADP"


def test_el_nombre_conserva_el_periodo_porque_es_lo_que_distingue_dos_filas():
    """Descartar el nombre de la fuente no puede costar la desambiguacion: dos
    lecturas del mismo indicador tienen que poder distinguirse."""
    ev = {"nombre": "CB Consumer Confidence (Aug)",
          "diccionario": {"nombre_es": "Confianza del consumidor (The Conference Board)"}}
    salida = pi._nombre_indicador(ev)
    # Solo el nombre del mes: la palabra "dato" ocupa trece caracteres en la
    # columna que decide el alto de la fila y no distingue una fila de otra.
    assert salida == "Confianza del consumidor (The Conference Board) \u00b7 agosto"
    assert salida.count("(") == 1, "un solo parentesis: los anidados son ilegibles"


def test_un_indicador_fuera_del_glosario_conserva_el_nombre_de_la_fuente():
    """Es la senal de que hay una sigla nueva por agregar al JSON, no un error."""
    ev = {"nombre": "Building Permits (Jul)", "glosario_pendiente": True}
    assert pi._nombre_indicador(ev) == "Building Permits (Jul)"


@pytest.mark.parametrize("mes, esperado", [(1, "enero"), (8, "agosto"), (12, "diciembre")])
def test_la_fecha_va_en_espanol_y_no_segun_el_locale(mes, esperado):
    """`strftime('%B')` usa el locale del sistema, que aca es ingles: la portada
    salia "25 de August de 2026"."""
    assert pi._fecha_es(datetime(2026, mes, 25)) == f"25 de {esperado} de 2026"


# ─────────────────────────────────────────────────────────────────────────────
# La agenda del día: si el dato ya salió, y con qué cifras
# ─────────────────────────────────────────────────────────────────────────────
AHORA = datetime(2026, 8, 26, 9, 15, tzinfo=pi.SANTIAGO)


def _evento(**campos):
    base = {"hora_servidor": "2026-08-26 08:30", "pais": "United States",
            "nombre": "Durable Goods Orders (MoM) (Jul)", "impacto": "alto",
            "forecast": "", "previo": "", "actual": ""}
    base.update(campos)
    return base


def _celdas(tabla: str) -> list[list[str]]:
    """Las filas de datos, ya partidas en celdas."""
    return [
        [c.strip() for c in linea.strip("|").split("|")]
        for linea in tabla.splitlines()
        if linea.startswith("| ") and "Indicador" not in linea and "---" not in linea
    ]


def test_la_agenda_dice_si_el_dato_ya_salio():
    """Es lo que pidió el director: la tabla anterior no permitía distinguir un
    dato publicado de uno que faltaba, y el informe se emite justo a la hora en
    que EE.UU. publica."""
    tabla = pi._tabla_calendario(
        [_evento(actual="1.1%", forecast="0.4%"),
         _evento(hora_servidor="2026-08-26 10:30", forecast="1.600M")],
        AHORA,
    )
    estados = [fila[0] for fila in _celdas(tabla)]
    assert estados == ["Publicado", "Pendiente"]


def test_el_estado_lo_decide_la_cifra_y_no_el_reloj():
    """La fuente publica con retraso más seguido de lo que uno querría. Un
    informe que dice "ya salió" porque pasó la hora obliga al lector a
    desmentirlo con la pantalla al lado."""
    pasada_con_dato = pi._estado_evento(
        _evento(hora_servidor="2026-08-26 08:30", actual="1.1%"), AHORA)
    futura_con_dato = pi._estado_evento(
        _evento(hora_servidor="2026-08-26 23:00", actual="1.1%"), AHORA)
    assert pasada_con_dato == "Publicado"
    assert futura_con_dato == "Publicado", "el testigo es la cifra, no la hora"


def test_un_evento_sin_cifra_al_que_ya_le_paso_la_hora_no_queda_pendiente():
    """Las subastas del Tesoro, las intervenciones de gobernadores y los feriados
    nunca traen cifra. Marcarlos "pendiente" para siempre haría que la tabla del
    cierre mienta todas las tardes."""
    ev = _evento(hora_servidor="2026-08-26 08:00", nombre="2-Year Note Auction",
                 previo="4.315%")
    assert pi._estado_evento(ev, AHORA) == "Sin cifra"


def test_un_dato_publicado_se_muestra_contra_su_consenso():
    """El número solo no dice nada: 3,3% de inflación es una noticia distinta
    según si el mercado esperaba 3,1% o 3,5%."""
    tabla = pi._tabla_calendario([_evento(actual="3.3%", forecast="3.1%")], AHORA)
    cifras = _celdas(tabla)[0][-1]
    assert "3,3%" in cifras and "esperado 3,1%" in cifras


def test_antes_de_publicarse_la_columna_lleva_el_consenso_y_nunca_un_dato():
    tabla = pi._tabla_calendario(
        [_evento(hora_servidor="2026-08-26 10:30", forecast="1.600M", previo="4.405M")],
        AHORA,
    )
    cifras = _celdas(tabla)[0][-1]
    assert cifras == "esperado 1,600M"
    assert "4" not in cifras.replace("1,600M", ""), "el anterior no entra teniendo consenso"


def test_sin_consenso_publicado_la_columna_cae_al_anterior():
    """Las subastas no tienen consenso. Una celda vacía se lee como dato faltante
    cuando en realidad hay algo que decir."""
    tabla = pi._tabla_calendario(
        [_evento(nombre="2-Year Note Auction", previo="4.315%")], AHORA)
    assert _celdas(tabla)[0][-1] == "anterior 4,315%"


def test_la_columna_de_cifras_nunca_lleva_tres_numeros():
    """Es la razón de que la tabla tenga seis columnas y no ocho: el anterior
    importa antes de que salga el dato y el dato después, nunca los tres juntos.
    Con una columna más, el nombre del indicador se va a tres líneas y el bloque
    no cabe en la página."""
    completo = _evento(actual="1.1%", forecast="0.4%", previo="0.3%")
    assert pi._cifras_evento(completo).count("%") == 2

    encabezado = pi._tabla_calendario([completo], AHORA).splitlines()[0]
    assert encabezado.strip("|").count("|") == 5, "la agenda tiene seis columnas"


def test_la_agenda_lleva_el_link_al_calendario():
    """La tabla trae los eventos de impacto medio y alto de cuatro países: no es
    el calendario completo, y el lector tiene que poder llegar al resto."""
    con_eventos = pi._tabla_calendario([_evento(actual="1.1%")], AHORA)
    sin_eventos = pi._tabla_calendario([], AHORA)
    for tabla in (con_eventos, sin_eventos):
        assert pi.CALENDARIO_URL in tabla
        assert "calendario económico" in tabla


def test_el_pie_de_la_agenda_cuenta_cuantos_datos_ya_salieron():
    """En una tabla de quince filas, el recuento es lo que se lee de un golpe."""
    eventos = [_evento(actual="1.1%"), _evento(actual="3.3%"),
               _evento(hora_servidor="2026-08-26 13:00", forecast="0.2%")]
    assert "2 de 3 eventos ya publicados" in pi._tabla_calendario(eventos, AHORA)


# ─────────────────────────────────────────────────────────────────────────────
# Unicidad: ninguna fila puede leerse igual que otra
# ─────────────────────────────────────────────────────────────────────────────
def test_el_subyacente_no_se_lee_igual_que_el_general():
    """El caso que motivó el cambio. El glosario engancha por sigla, así que
    "Core PCE" y "PCE" caen en la misma entrada y la tabla mostraba dos filas
    idénticas con cifras distintas. Y la distinción no es menor: el subyacente
    excluye alimentos y energía, y es el que mira la Fed."""
    core = pi._nombre_indicador({
        "nombre": "Core PCE Price Index (YoY) (Jul)",
        "diccionario": {"nombre_es": "Gasto en consumo personal"}})
    general = pi._nombre_indicador({
        "nombre": "PCE Price index (YoY) (Jul)",
        "diccionario": {"nombre_es": "Gasto en consumo personal"}})
    assert "subyacente" in core
    assert "subyacente" not in general
    assert core != general


def test_un_agregado_no_se_lee_igual_que_su_deflactor():
    """"GDP" y "GDP Price Index" comparten la sigla y miden cosas distintas:
    cuánto se produjo contra cuánto subieron los precios de lo producido."""
    pib = pi._nombre_indicador({
        "nombre": "GDP (QoQ) (Q2)",
        "diccionario": {"nombre_es": "Producto interno bruto (PIB)"}})
    deflactor = pi._nombre_indicador({
        "nombre": "GDP Price Index (QoQ) (Q2)",
        "diccionario": {"nombre_es": "Producto interno bruto (PIB)"}})
    assert "índice de precios" in deflactor
    assert "índice de precios" not in pib
    assert "segundo trimestre" in pib


def test_dos_subastas_se_distinguen_por_su_plazo():
    dos = pi._nombre_indicador({
        "nombre": "2-Year Note Auction",
        "diccionario": {"nombre_es": "Subasta de bonos del Tesoro de EE.UU."}})
    cinco = pi._nombre_indicador({
        "nombre": "5-Year Note Auction",
        "diccionario": {"nombre_es": "Subasta de bonos del Tesoro de EE.UU."}})
    assert "a 2 años" in dos and "a 5 años" in cinco


def test_el_desempate_cita_la_palabra_propia_y_no_el_nombre_en_ingles():
    """Entre "Crude Oil Inventories" y "Cushing Crude Oil Inventories" la
    diferencia es Cushing. Pegar los dos nombres completos para decir eso metería
    seis palabras en inglés en un informe en español."""
    eia = {"nombre_es": "Inventarios de petróleo crudo (EIA)"}
    eventos = [
        _evento(nombre="Crude Oil Inventories", forecast="1.600M", diccionario=eia),
        _evento(nombre="Cushing Crude Oil Inventories", previo="-1.314M", diccionario=eia),
    ]
    tabla = pi._tabla_calendario(eventos, AHORA)
    indicadores = [fila[3] for fila in _celdas(tabla)]
    assert indicadores[0].endswith("(general)")
    assert indicadores[1].endswith("(Cushing)")
    assert "Crude Oil Inventories" not in tabla


def test_ninguna_fila_de_la_agenda_se_lee_igual_que_otra():
    """Barrido sobre la mañana real que destapó el defecto: diez datos de EE.UU.
    a las 08:30, de los cuales seis colapsaban en tres pares idénticos.

    Dos filas iguales no son un defecto cosmético: el lector no puede saber cuál
    de las dos cifras corresponde a cuál indicador, y la tabla deja de servir
    para lo único que sirve una tabla.
    """
    familias = {
        "Gasto en consumo personal": [
            "Core PCE Price Index (MoM) (Jul)", "Core PCE Price Index (YoY) (Jul)",
            "Core PCE Prices (Q2)", "PCE price index (MoM) (Jul)",
            "PCE Price index (YoY) (Jul)",
        ],
        "Pedidos de bienes durables": [
            "Core Durable Goods Orders (MoM) (Jul)", "Durable Goods Orders (MoM) (Jul)",
        ],
        "Producto interno bruto (PIB)": [
            "GDP (QoQ) (Q2)", "GDP Price Index (QoQ) (Q2)",
        ],
        "Subasta de bonos del Tesoro de EE.UU.": [
            "2-Year Note Auction", "5-Year Note Auction",
        ],
        "Inventarios de petróleo crudo (EIA)": [
            "Crude Oil Inventories", "Cushing Crude Oil Inventories",
        ],
    }
    eventos = [
        _evento(nombre=fuente, diccionario={"nombre_es": es})
        for es, fuentes in familias.items() for fuente in fuentes
    ]
    indicadores = [fila[3] for fila in _celdas(pi._tabla_calendario(eventos, AHORA))]
    repetidos = {n for n in indicadores if indicadores.count(n) > 1}
    assert not repetidos, f"filas indistinguibles: {sorted(repetidos)}"
    assert len(indicadores) == len(eventos)

