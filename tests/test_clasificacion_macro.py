"""La clasificacion PROPIA de los datos macro, independiente del juicio de Investing.

Investing dice `resultado: peor`, que es un juicio economico. Lo que la pieza
necesita es la direccion de mercado, y no es lo mismo: subsidios peores significa
empleo mas debil, mas chance de recorte de la Fed, y por tanto dolar mas debil y
oro ARRIBA. "Peor" para la economia es alcista para el oro.

Eso Investing no lo da y no es su trabajo. Este modulo es donde vive.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

import clasificacion_macro as cm  # noqa: E402

GLOSARIO = RAIZ / "data" / "glosario_siglas.json"


# ─────────────────────────────────────────────────────────────────────────────
# La direccion de mercado, que es lo que Investing no puede dar
# ─────────────────────────────────────────────────────────────────────────────
def test_un_dato_peor_para_la_economia_puede_ser_alcista_para_el_oro():
    """El caso que justifica todo el modulo, y que ocurrio hoy.

    Los subsidios salieron 206K contra 205K esperado: `peor` segun Investing. El
    dolar cedio 0,65% y el oro subio 0,93%. O sea que "peor" fue alcista para el
    oro, y una pieza que tradujera `peor` como `bajista` habria dicho lo
    contrario de lo que paso.
    """
    c = cm.clasificar({"nombre": "Initial Jobless Claims"})
    assert c is not None, "los subsidios no estan clasificados"

    efecto = c["si_sale_sobre_consenso"]
    assert efecto["dolar"] == "baja"
    assert efecto["oro"] == "sube"
    assert efecto["porque"], "sin el porque, la pieza no puede explicarlo"


def test_un_ipc_caliente_empuja_al_dolar_y_castiga_al_oro():
    """La direccion contraria a los subsidios, por la via de las tasas reales."""
    c = cm.clasificar({"nombre": "CPI (MoM)"})
    assert c is not None
    assert c["si_sale_sobre_consenso"]["dolar"] == "sube"
    assert c["si_sale_sobre_consenso"]["oro"] == "baja"


def test_los_datos_de_chile_mueven_el_dolar_contra_el_peso():
    """Un Imacec o una TPM mas altos fortalecen al peso, o sea BAJAN el USD/CLP.
    El signo es el que se confunde: "mejor para Chile" es menos pesos por dolar."""
    for nombre in ("Imacec", "Chile Interest Rate Decision"):
        c = cm.clasificar({"nombre": nombre})
        assert c is not None, f"{nombre} sin clasificar"
        assert c["si_sale_sobre_consenso"]["usdclp"] == "baja", nombre


def test_el_efecto_esta_declarado_como_primer_orden_y_no_como_pronostico():
    """Hoy el mapeo acerto en dolar y oro y FALLO en indices: deberian haber
    subido por la expectativa de recortes y bajaron, porque el ISM de precios
    salio caliente y el regimen es R3 estanflacion.

    El Playbook manda sobre el dato, asi que el campo tiene que decir que es
    primer orden y que el regimen le pasa por encima.
    """
    for clave, entrada in cm.cargar_clasificacion().items():
        efecto = entrada.get("si_sale_sobre_consenso")
        if not efecto:
            continue
        assert efecto.get("orden") == "primero", (
            f"{clave}: el efecto no se declara de primer orden y se leeria como pronostico"
        )


# ─────────────────────────────────────────────────────────────────────────────
# La fuente: oficial cuando existe, declarada cuando no
# ─────────────────────────────────────────────────────────────────────────────
def test_los_datos_con_fuente_oficial_la_declaran_con_su_serie():
    """FRED ya esta cableado en el repo y tiene los datos de evento: `ICSA`
    devolvio 206.000 hoy, el mismo numero que Investing."""
    c = cm.clasificar({"nombre": "Initial Jobless Claims"})
    assert c["fuente"]["tipo"] == "fred"
    assert c["fuente"]["serie"] == "ICSA"
    assert c["fuente"]["organismo"], "sin organismo no se puede citar la fuente"


def test_el_ism_y_los_pmi_se_declaran_comerciales_y_no_disparan_momentos():
    """Medido contra FRED: `NAPM` y `NMFCI` devuelven NO DISPONIBLE. Son datos
    de organizaciones privadas que licencian su distribucion.

    Como no podemos confiar en su hora de llegada, no pueden disparar un momento
    programado: la pieza sale cuando el numero esta, no cuando el reloj dice.
    """
    for nombre in ("ISM Non-Manufacturing PMI", "S&P Global Services PMI"):
        c = cm.clasificar({"nombre": nombre})
        assert c is not None, f"{nombre} sin clasificar"
        assert c["fuente"]["tipo"] == "comercial", nombre
        assert c["puede_disparar_momento"] is False, nombre


def test_ningun_dato_con_fuente_oficial_queda_sin_serie():
    """Contrato: declarar `fred` sin `serie` deja el dato sin forma de traerse."""
    for clave, entrada in cm.cargar_clasificacion().items():
        fuente = entrada.get("fuente") or {}
        if fuente.get("tipo") == "fred":
            assert fuente.get("serie"), f"{clave} dice fred y no trae serie"


# ─────────────────────────────────────────────────────────────────────────────
# La regla de seleccion: un dato por momento, no siete
# ─────────────────────────────────────────────────────────────────────────────
LOTE_DE_HOY = [
    {"nombre": "Initial Jobless Claims", "impacto": "alto", "forecast": "205K",
     "hora_servidor": "2026-09-03 08:30"},
    {"nombre": "Continuing Jobless Claims", "impacto": "medio", "forecast": "",
     "hora_servidor": "2026-09-03 08:30"},
    {"nombre": "Exports (Jul)", "impacto": "medio", "forecast": "",
     "hora_servidor": "2026-09-03 08:30"},
    {"nombre": "Imports (Jul)", "impacto": "medio", "forecast": "",
     "hora_servidor": "2026-09-03 08:30"},
    {"nombre": "Trade Balance (Jul)", "impacto": "medio", "forecast": "-89.40B",
     "hora_servidor": "2026-09-03 08:30"},
    {"nombre": "Nonfarm Productivity (QoQ) (Q2)", "impacto": "medio", "forecast": "1.4%",
     "hora_servidor": "2026-09-03 08:30"},
    {"nombre": "Unit Labor Costs (QoQ) (Q2)", "impacto": "medio", "forecast": "1.3%",
     "hora_servidor": "2026-09-03 08:30"},
    {"nombre": "Fed Waller Speaks", "impacto": "medio", "forecast": "",
     "hora_servidor": "2026-09-03 08:30"},
]


def test_del_lote_de_las_ocho_y_media_se_elige_uno_solo():
    """Las 08:30 no son un dato, son siete. Publicarlos todos es spam."""
    elegido = cm.dato_que_manda(LOTE_DE_HOY, "02_forex_divisas")

    assert elegido is not None
    assert elegido["nombre"] == "Initial Jobless Claims", (
        f"eligio {elegido['nombre']!r}: el que manda es el de menor tier con consenso"
    )


def test_un_dato_sin_consenso_no_puede_ganar_el_momento():
    """Sin consenso no se puede juzgar mejor ni peor, asi que no da pieza."""
    sin_consenso = [dict(e, forecast="") for e in LOTE_DE_HOY]
    assert cm.dato_que_manda(sin_consenso, "02_forex_divisas") is None


def test_un_dato_que_no_toca_el_canal_no_lo_gana():
    """El Imacec manda en divisas y no tiene nada que decirle a las cripto."""
    imacec = [{"nombre": "Imacec", "impacto": "alto", "forecast": "2.0%",
               "hora_servidor": "2026-09-03 08:30"}]
    assert cm.dato_que_manda(imacec, "02_forex_divisas") is not None
    assert cm.dato_que_manda(imacec, "06_criptoactivos") is None


def test_un_evento_que_no_esta_en_el_diccionario_devuelve_none_y_no_adivina():
    """Fail-closed: la pieza dice "sin clasificar" en vez de inventar direccion."""
    assert cm.clasificar({"nombre": "Un Indicador Que No Existe"}) is None
    assert cm.dato_que_manda(
        [{"nombre": "Un Indicador Que No Existe", "impacto": "alto",
          "forecast": "1", "hora_servidor": "2026-09-03 08:30"}],
        "02_forex_divisas",
    ) is None


# ─────────────────────────────────────────────────────────────────────────────
# Contratos de nombres
# ─────────────────────────────────────────────────────────────────────────────
def test_la_clasificacion_vive_en_el_glosario_que_el_mcp_ya_entrega():
    """No se crea un archivo nuevo: el MCP del calendario ya adjunta la entrada
    de `glosario_siglas.json` en el campo `diccionario` de cada evento, asi que
    extender ese archivo hace que la clasificacion llegue sola a las piezas."""
    glosario = json.loads(GLOSARIO.read_text(encoding="utf-8"))
    clasificados = cm.cargar_clasificacion()

    assert clasificados, "no hay ningun indicador clasificado"
    for clave in clasificados:
        assert clave in glosario, f"{clave} no esta en glosario_siglas.json"


def test_todo_canal_nombrado_en_la_clasificacion_existe_de_verdad():
    """El defecto recurrente del repo: dos modulos que se hablan por nombre. Un
    canal mal escrito aca deja el dato sin destino, en silencio."""
    if str(RAIZ / "src") not in sys.path:
        sys.path.insert(0, str(RAIZ / "src"))
    from whatsapp_sender import WhatsAppConfig

    reales = set(WhatsAppConfig().grupos)
    for clave, entrada in cm.cargar_clasificacion().items():
        for canal in entrada.get("canales", []):
            assert canal in reales, f"{clave} apunta a un canal inexistente: {canal}"


def test_todo_tier_esta_en_la_escala_declarada():
    """Tres tiers y no mas: 1 reprecia todo, 2 mueve su clase, 3 es contexto."""
    for clave, entrada in cm.cargar_clasificacion().items():
        assert entrada["tier"] in (1, 2, 3), f"{clave} tiene tier {entrada['tier']}"


def test_el_tier_es_nuestro_y_no_el_impacto_de_investing():
    """Dos campos con dueños distintos: `impacto` es la opinion de la fuente y
    `tier` es la nuestra. La que gobierna nuestras decisiones es la nuestra."""
    import inspect

    fuente = inspect.getsource(cm.dato_que_manda)
    assert "impacto" not in fuente, (
        "la seleccion usa el impacto de Investing en vez del tier propio"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Los dos defectos que solo aparecieron al probar contra el calendario real
# ─────────────────────────────────────────────────────────────────────────────
def test_una_entrada_sin_mapeo_direccional_no_puede_ganar_un_momento():
    """El crash que destapo la prueba contra la fuente.

    "Atlanta Fed GDPNow" calzaba con la entrada `Fed`, que cubre discursos y
    hoja de balance y NO lleva efecto direccional porque un discurso no tiene
    direccion. Asi ganaba el momento de cripto y reventaba al consumidor.

    Una entrada que no puede decir que le hace al mercado no puede gobernar un
    momento: la pieza no tendria que escribir.
    """
    inventado = {
        "nombre": "Fed's Balance Sheet",
        "pais": "United States",
        "impacto": "medio",
        "forecast": "6700B",
        "hora_servidor": "2026-09-03 16:30",
    }
    clase = cm.clasificar(inventado)
    assert clase is not None, "la hoja de balance si esta clasificada"
    assert not clase.get("si_sale_sobre_consenso"), (
        "esta entrada no deberia declarar direccion: es contexto, no un dato con signo"
    )
    assert cm.dato_que_manda([inventado], "06_criptoactivos") is None


def test_gdpnow_no_se_confunde_con_la_entrada_de_discursos_de_la_fed():
    """El calce por substring: "Atlanta Fed GDPNow" contiene "Fed".

    Se resuelve por el largo de lo que calza: "GDPNow" son 6 caracteres contra
    los 3 de "Fed", asi que gana la entrada correcta sin reglas especiales.
    """
    clase = cm.clasificar({
        "nombre": "Atlanta Fed GDPNow (Q3)",
        "pais": "United States",
    })
    assert clase is not None
    assert clase["_clave"] == "GDP", f"calzo con {clase['_clave']!r} en vez de GDP"
    assert clase["fuente"]["tipo"] == "fred"


def test_los_pmi_de_la_zona_euro_quedan_fuera_porque_su_signo_es_el_contrario():
    """El chequeo de pais haciendo su trabajo, y hay que dejarlo hacerlo.

    Un PMI europeo mas fuerte fortalece al EURO, o sea DEBILITA al dolar: signo
    contrario al del PMI de EE.UU. Heredar el mapeo estadounidense publicaria la
    direccion al reves, asi que se rechaza y la pieza dice "sin clasificar".
    """
    europeo = {
        "nombre": "HCOB Eurozone Services PMI (Aug)",
        "pais": "Euro Zone",
        "impacto": "medio",
        "forecast": "51.7",
        "hora_servidor": "2026-09-03 04:00",
    }
    assert cm.clasificar(europeo) is None
    assert cm.dato_que_manda([europeo], "02_forex_divisas") is None

    # Y el de EE.UU. con el mismo nombre de indicador SI se clasifica.
    estadounidense = dict(europeo, nombre="S&P Global Services PMI (Aug)",
                          pais="United States")
    assert cm.clasificar(estadounidense) is not None


def test_todo_lo_que_puede_disparar_un_momento_declara_su_efecto():
    """Contrato: si un dato puede activar un momento programado, la pieza que
    ese momento produce necesita saber que direccion comunicar."""
    for clave, entrada in cm.cargar_clasificacion().items():
        if entrada.get("puede_disparar_momento"):
            assert entrada.get("si_sale_sobre_consenso"), (
                f"{clave} puede disparar un momento y no declara su efecto"
            )


def test_la_seleccion_y_el_disparo_son_preguntas_distintas():
    """El PMI de S&P Global gana el momento del canal de acciones y NO puede
    dispararlo: es comercial y su hora de llegada depende de un tercero.

    Son dos preguntas distintas a proposito. Puede ser el dato de la pieza sin
    ser el gatillo del reloj.
    """
    pmi = {
        "nombre": "S&P Global Composite PMI (Aug)",
        "pais": "United States",
        "impacto": "medio",
        "forecast": "56.0",
        "hora_servidor": "2026-09-03 09:45",
    }
    assert cm.dato_que_manda([pmi], "05_acciones_etfs") is not None
    assert cm.puede_disparar_momento(pmi) is False
