# -*- coding: utf-8 -*-
"""
test_ecosistema_macro.py
Suite de pruebas automatizadas para el Ecosistema de Ingesta Macro, Agenda y Detección de Novedades.
"""

import json
import sys
from datetime import datetime, timezone, date
from pathlib import Path
from zoneinfo import ZoneInfo
import pytest

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / ".agents" / "skills" / "ecosistema-datos-macro" / "scripts"))
sys.path.insert(0, str(BASE_DIR / "scripts"))  # RAIZ_SCRIPTS: macro_bias_engine

import agenda
import extractor_chile
import extractor_commodities
import extractor_japon
import extractor_usa
import pipeline_ingesta


@pytest.fixture
def sin_backoff(monkeypatch):
    """Anula la espera entre reintentos de tenacity, no los reintentos.

    Los extractores reintentan 3 veces con backoff exponencial de hasta 10 s.
    Contra un emisor real eso es correcto -una API de gobierno se cae un rato y
    vuelve-, pero en un test contra una funcion falsa la espera no prueba nada
    y son 30 s por corrida. Se anula el `sleep` y no el `stop`, para que el
    test siga ejercitando los 3 intentos de verdad.
    """
    for nombre in ("extraer_buybacks_tesoro", "extraer_serie_fred"):
        fn = getattr(extractor_usa, nombre)
        monkeypatch.setattr(fn.retry, "sleep", lambda _segundos: None)


def test_calculo_hash_canonico_orden_invariante():
    """El hash canonico debe ser identico sin importar el orden de insercion de claves."""
    obj1 = {"a": 1, "b": {"x": 10, "y": 20}, "c": [1, 2, 3]}
    obj2 = {"c": [1, 2, 3], "b": {"y": 20, "x": 10}, "a": 1}
    
    h1 = pipeline_ingesta.calcular_hash_canonico(obj1)
    h2 = pipeline_ingesta.calcular_hash_canonico(obj2)
    assert h1 == h2, "El hash canonico debe ser deterministico e invariante al orden de claves."

def test_deteccion_revisiones_historicas():
    """Valida que una modificacion retroactiva en un dato pasado se detecte como revision."""
    hist_ant = {"2026-05-01": -0.3, "2026-06-01": 2.1}
    hist_nue = {"2026-05-01": -0.3, "2026-06-01": 2.4, "2026-07-01": 1.8}
    
    revisiones = pipeline_ingesta.detectar_revisiones_historicas(hist_ant, hist_nue)
    assert len(revisiones) == 1
    assert "2026-06-01" in revisiones[0]
    assert "2.1" in revisiones[0] and "2.4" in revisiones[0]

def test_conversion_zonas_horarias_y_dst():
    """Valida la conversion horaria precisa entre husos IANA (New York, Berlin, London, Santiago)."""
    # Evento FOMC a las 14:00 ET
    tz_ny = ZoneInfo("America/New_York")
    tz_cl = ZoneInfo("America/Santiago")
    
    dt_ny = datetime(2026, 8, 19, 14, 0, tzinfo=tz_ny)
    dt_cl = dt_ny.astimezone(tz_cl)
    
    # En agosto, NY es UTC-4 y Santiago es UTC-4 (mismo offset en invierno de Chile)
    assert dt_cl.hour == 14, f"En agosto, 14:00 NY debe ser 14:00 Santiago (ambos UTC-4). Obtenido: {dt_cl.hour}"
    
    # Evento BCE a las 14:15 CET (Berlin)
    tz_berlin = ZoneInfo("Europe/Berlin")
    dt_berlin = datetime(2026, 9, 10, 14, 15, tzinfo=tz_berlin) # CEST es UTC+2
    dt_cl_bce = dt_berlin.astimezone(tz_cl) # En sept, Chile pasa a UTC-3 tras cambio de hora de primavera
    assert dt_cl_bce.minute == 15

def test_normalizacion_unidades_cobre():
    """Valida el factor de conversion de USD/libra a USD/tonelada."""
    precio_lb = 4.50
    factor_ton = 2204.62
    precio_ton = round(precio_lb * factor_ton, 2)
    assert precio_ton == 9920.79

def test_agenda_retorno_estructurado():
    """Valida que agenda.py retorne la estructura completa esperada."""
    res = agenda.obtener_agenda(datetime(2026, 8, 20, 10, 0, tzinfo=ZoneInfo("America/Santiago")))
    assert "hay_eventos_hoy" in res
    assert "eventos_hoy" in res
    assert "eventos_proximos_7_dias" in res
    assert isinstance(res["eventos_hoy"], list)


def test_los_buybacks_piden_el_dataset_que_existe(monkeypatch):
    """El extractor pedia `v2/accounting/od/treasury_securities_buybacks`, que la
    API de Fiscal Data no sirve: devolvia 404 en todas sus versiones y el dataset
    no aparece en el catalogo. El real es `v1/accounting/od/buybacks_operations`.

    El fallo era mudo hacia afuera. El extractor capturaba la excepcion, dejaba
    los datos anteriores y seguia imprimiendo "[OK] Ingesta USA completada", asi
    que la unica senal era `usa: ERROR_FALLBACK` en estado_ejecucion.json, sin el
    motivo. Vivio desde que el archivo entro al repo.

    Se verifica el comportamiento -que URL se pide- y no el texto del codigo: un
    assert sobre el fuente pasaria con la URL escrita en un comentario.
    """
    pedidas = {}

    class RespuestaFalsa:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return {"data": [{"operation_date": "2026-08-25"}]}

    def falsa_get(url, params=None, timeout=None):
        pedidas["url"] = url
        pedidas["params"] = params or {}
        return RespuestaFalsa()

    monkeypatch.setattr(extractor_usa.requests, "get", falsa_get)
    filas = extractor_usa.extraer_buybacks_tesoro()

    assert pedidas["url"].endswith("/v1/accounting/od/buybacks_operations"), (
        f"pide un dataset que la API no sirve: {pedidas['url']}"
    )
    # El campo de fecha de este dataset es `operation_date`. Con `record_date`
    # la API responde 400 "Invalid query parameter", no 404: seria el mismo
    # sintoma por otra causa.
    assert pedidas["params"].get("sort") == "-operation_date"
    assert filas == [{"operation_date": "2026-08-25"}]


def test_una_fuente_degradada_deja_escrito_el_motivo(monkeypatch, tmp_path, sin_backoff):
    """`ERROR_FALLBACK` sin causa es un aviso que nadie puede accionar.

    Asi vivio el 404 de las recompras: el extractor imprimia el error por
    consola, el pipeline corre desatendido y esa salida no queda en ningun
    lado, y hacia afuera solo se veia el estado degradado. El motivo tiene que
    viajar CON el dato para poder leerlo despues.
    """
    def get_que_falla(url, params=None, timeout=None):
        raise ConnectionError("boom en el emisor")

    monkeypatch.setattr(extractor_usa.requests, "get", get_que_falla)
    monkeypatch.setattr(extractor_usa, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(extractor_usa, "OUTPUT_FILE", tmp_path / "treasury_fed_data.json")

    resultado = extractor_usa.ejecutar_extraccion_usa()

    assert resultado["tesoro_status"] == "ERROR_FALLBACK"
    assert "boom en el emisor" in resultado["tesoro_error"], (
        "la causa se perdio: queda un estado degradado sin nada que investigar"
    )


def test_sin_fallos_no_hay_motivo_que_reportar(monkeypatch, tmp_path, sin_backoff):
    """La contraparte. Sin esto, "siempre escribe un motivo" y "escribe el
    motivo correcto" serian indistinguibles, y el campo dejaria de significar
    algo: su valor esta en que aparezca SOLO cuando hay algo que contar."""
    class RespuestaFalsa:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return {"data": [], "observations": []}

    monkeypatch.setattr(extractor_usa.requests, "get",
                        lambda url, params=None, timeout=None: RespuestaFalsa())
    monkeypatch.setattr(extractor_usa, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(extractor_usa, "OUTPUT_FILE", tmp_path / "treasury_fed_data.json")

    resultado = extractor_usa.ejecutar_extraccion_usa()

    assert resultado["tesoro_status"] == "OK"
    assert "tesoro_error" not in resultado


def test_la_serie_forward_del_bcch_existe_en_el_catalogo():
    """`F073.FWD.EXT.NETA.D` no existe en el BCCh.

    La API respondia HTTP 200 con `Codigo=-50` ("an internal error has
    occurred, information is not available") y `Series.Obs` en null, asi que el
    extractor moria con "'NoneType' object is not iterable". Las otras tres
    series del mismo archivo -TPM, Imacec y dolar observado- respondian bien.

    La real es la posicion neta VIGENTE (STO, un stock) de forwards por
    compensacion de bancos residentes con no residentes en USD-CLP. Coincide
    con lo que el campo dice ser, incluido el rezago: publica en T-2 habiles.
    """
    codigo = extractor_chile.SERIES_BCCH["POSICION_FORWARD_EXTRANJEROS"]
    assert codigo == "F099.DER.STO.Z.40.N.NR.NET.NDF.MMUSD.CLPUSD.C.Z.0.D"
    assert ".STO." in codigo, "tiene que ser un stock (posicion), no un flujo (FLU)"
    assert ".NR." in codigo, "tiene que ser frente a no residentes"


def _bcch_responde(monkeypatch, payload):
    class Respuesta:
        status_code = 200
        def raise_for_status(self): pass
        def json(self): return payload
    monkeypatch.setattr(extractor_chile.requests, "get", lambda *a, **k: Respuesta())
    monkeypatch.setattr(extractor_chile, "BCCH_USER", "usuario")
    monkeypatch.setattr(extractor_chile, "BCCH_PASS", "clave")


def test_un_codigo_inexistente_falla_con_su_motivo(monkeypatch):
    """`data.get("Series", {})` no protege de un null: el default solo aplica si
    la CLAVE falta, y aca viene presente con valor null. El `.get("Obs", [])`
    siguiente devolvia None y el `for` moria con "'NoneType' object is not
    iterable", un mensaje que no dice ni que serie ni por que.

    No basta con devolver {} y seguir: un codigo que el BCCh no reconoce es un
    error de configuracion, no un dato que todavia no publicaron. Tiene que
    fallar, y el mensaje tiene que nombrar la serie y el codigo de la API.
    """
    _bcch_responde(monkeypatch, {"Codigo": -50, "Descripcion": "An internal error has occurred",
                                 "Series": None})

    with pytest.raises(ValueError) as err:
        extractor_chile.extraer_bde_serie("F073.NO.EXISTE.D")

    mensaje = str(err.value)
    assert "F073.NO.EXISTE.D" in mensaje, "el error no dice que serie fallo"
    assert "-50" in mensaje, "el error no trae el codigo que devolvio la API"


def test_una_serie_valida_sin_datos_en_el_rango_devuelve_vacio(monkeypatch):
    """La contraparte, y la razon por la que el fallo se distingue del vacio.

    Una serie que existe pero no publico en el rango pedido responde `Codigo=0`
    con la lista vacia. Eso NO es un error: es un feriado, o una serie con
    rezago. Sin esta distincion, o se traga los codigos rotos o alarma cada vez
    que el BCCh no publico todavia.
    """
    _bcch_responde(monkeypatch, {"Codigo": 0, "Series": {"Obs": []}})
    assert extractor_chile.extraer_bde_serie("F029.FWD.STO.ME.D") == {}


def test_el_oro_sale_de_lbma_y_no_de_stooq(monkeypatch):
    """Stooq dejo de servir el CSV: responde HTTP 200 con una pagina que pide
    JavaScript, asi que `raise_for_status()` no dispara y el codigo parseaba
    HTML como si fueran filas. El fallo se notaba recien al quedar cero filas.

    LBMA es el emisor primario que declara la propia skill, publica el fixing
    del dia y su JSON trae `v` como [USD, GBP, EUR].
    """
    pedidas = []

    class RespuestaLBMA:
        status_code = 200
        def raise_for_status(self): pass
        def json(self):
            return [{"d": "2026-08-24", "v": [4600.0, 3380.0, 3950.0]},
                    {"d": "2026-08-25", "v": [4615.45, 3383.12, 3954.06]}]

    def falsa_get(url, **kwargs):
        pedidas.append(url)
        return RespuestaLBMA()

    monkeypatch.setattr(extractor_commodities.requests, "get", falsa_get)
    obs = extractor_commodities.extraer_oro_lbma()

    assert "lbma.org.uk" in pedidas[0], f"sigue pidiendo a otra fuente: {pedidas}"
    assert "stooq" not in pedidas[0]
    assert obs["2026-08-25"] == 4615.45, "debe tomar el precio en USD, que es v[0]"


def test_el_estado_de_una_fuente_mira_todas_sus_series():
    """Miraba UNA serie testigo por fuente: chile el Imacec, commodities el
    cobre. Por eso el forward roto del BCCh y el Oro cayendo a respaldo no
    aparecian en ningun lado, y las dos fuentes se reportaban OK.

    Un estado que resume por muestreo no es un estado: es una serie con nombre
    de fuente.
    """
    fuente = {
        "IMACEC_TOTAL": {"status": "OK"},
        "DOLAR_OBSERVADO": {"status": "OK"},
        "POSICION_FORWARD_EXTRANJEROS": {"status": "ERROR_STALE"},
    }
    assert pipeline_ingesta.peor_status(fuente) == "ERROR_STALE"

    assert pipeline_ingesta.peor_status({"A": {"status": "OK"}, "B": {"status": "OK"}}) == "OK"
    # Un respaldo no es un fallo, pero tampoco es "salio del emisor primario".
    assert pipeline_ingesta.peor_status(
        {"A": {"status": "OK"}, "B": {"status": "OK_FALLBACK"}}
    ) == "OK_FALLBACK"



def test_la_frase_del_forward_sigue_al_signo_del_dato():
    """La justificacion decia "compradora (+...)" con el signo escrito a mano.

    Funcionaba por casualidad: la serie traia un valor de relleno positivo
    porque su codigo del BCCh no existia. Con el dato real, que es negativo, esa
    frase salia como "(+-16866M USD)" y afirmaba que la posicion era compradora
    cuando el BCCh publica lo contrario. Es texto que llega al informe.
    """
    import macro_bias_engine as mbe

    fuente = Path(mbe.__file__).read_text(encoding="utf-8")
    assert 'compradora (+{fwd_ext' not in fuente, "el sentido volvio a estar escrito a mano"
    assert 'fwd_sentido = "vendedora" if fwd_ext < 0 else "compradora"' in fuente


def test_stale_mide_antiguedad_y_no_solo_si_la_descarga_funciono():
    """`is_stale` era `status != "OK"`: medía si BAJAR el archivo funcionó.

    Un dato de ocho días con la descarga correcta salía `is_stale: False`. El
    Imacec llevaba 86 días declarandose fresco. El booleano que alguien lee para
    decidir si confiar en un driver no miraba la unica cosa que importa.
    """
    hoy = date(2026, 8, 26)
    # Serie diaria con dato de ayer: fresca.
    assert not pipeline_ingesta.esta_vencido("COBRE_HG", "2026-08-25", "OK", hoy)
    # La misma serie con tres semanas: vencida, aunque la descarga saliera bien.
    assert pipeline_ingesta.esta_vencido("COBRE_HG", "2026-08-05", "OK", hoy)


def test_la_ventana_es_la_cadencia_de_cada_serie_y_no_un_numero_fijo():
    """Un umbral unico marcaria vencido al Imacec todos los meses.

    El Imacec de junio se publica a inicios de agosto: 86 dias de antiguedad son
    su ritmo normal, no un fallo. El Brent de FRED llega con rezago propio de la
    EIA. Aplicarles la ventana de una serie diaria seria alarmismo, y bajaria la
    confianza del motor bajo su umbral por datos que estan al dia.
    """
    hoy = date(2026, 8, 26)
    # Mensuales en su ritmo: no vencidos.
    assert not pipeline_ingesta.esta_vencido("CHILE_IMACEC_12M", "2026-06-01", "OK", hoy)
    assert not pipeline_ingesta.esta_vencido("PETROLEO_BRENT", "2026-08-18", "OK", hoy)
    # Un Imacec de hace medio año si esta vencido.
    assert pipeline_ingesta.esta_vencido("CHILE_IMACEC_12M", "2026-02-01", "OK", hoy)


def test_una_tasa_de_politica_no_envejece_por_calendario():
    """La TPM en 4,5 % no esta "vieja" porque el Banco Central no la movio: es el
    valor VIGENTE. Envejece por reuniones, no por dias, asi que para estas
    series el unico criterio es si la descarga funciono."""
    hoy = date(2026, 8, 26)
    assert not pipeline_ingesta.esta_vencido("CHILE_TPM", "2026-01-30", "OK", hoy)
    assert pipeline_ingesta.esta_vencido("CHILE_TPM", "2026-08-26", "ERROR_STALE", hoy)


def test_una_descarga_fallida_vence_el_driver_aunque_la_fecha_sea_de_hoy():
    """Los dos criterios se suman, no se reemplazan."""
    hoy = date(2026, 8, 26)
    assert pipeline_ingesta.esta_vencido("COBRE_HG", "2026-08-26", "ERROR_FALLBACK", hoy)


def test_la_fecha_del_boj_no_puede_ser_la_de_su_proxima_reunion():
    """`fecha_dato` traia `proxima_reunion`: cuando se va a REVISAR, no cuando se
    midio. La antiguedad daba negativa, asi que ese driver pasaba cualquier
    filtro de frescura para siempre."""
    fuente = Path(pipeline_ingesta.__file__).read_text(encoding="utf-8")
    # Se prohibe el USO incorrecto, no la cadena: exponer la proxima reunion
    # como campo informativo aparte si es correcto, y un assert sobre el texto
    # suelto impediria justamente eso.
    assert 'boj_tasa_fecha = japon_data.get("politica_monetaria_boj"' not in fuente, (
        "la fecha del dato volvio a salir de la proxima reunion"
    )
    # Y una fecha futura cuenta como vencida, sea cual sea su origen: es un
    # campo mal poblado, no un dato muy fresco.
    assert pipeline_ingesta.esta_vencido("COBRE_HG", "2026-09-17", "OK", date(2026, 8, 26))



def test_una_fecha_futura_vence_hasta_a_las_tasas_de_politica():
    """El caso que motivo todo esto, y que casi se escapa.

    Las tasas de politica no tienen ventana de cadencia, asi que `esta_vencido`
    salia temprano con False sin mirar la fecha. Justamente el driver que traia
    una fecha futura -la tasa del BoJ, fechada con su proxima reunion- era uno
    de ellos: el guardia no habria detectado la reincidencia.
    """
    hoy = date(2026, 8, 26)
    assert pipeline_ingesta.esta_vencido("BOJ_POLICY_RATE", "2026-09-17", "OK", hoy)
    assert pipeline_ingesta.esta_vencido("CHILE_TPM", "2026-12-01", "OK", hoy)
    # Sigue sin envejecer por calendario hacia atras.
    assert not pipeline_ingesta.esta_vencido("BOJ_POLICY_RATE", "2026-01-30", "OK", hoy)


def test_una_fecha_ilegible_vence_aunque_la_serie_no_tenga_ventana():
    hoy = date(2026, 8, 26)
    assert pipeline_ingesta.esta_vencido("BOJ_POLICY_RATE", "no es una fecha", "OK", hoy)


# ── La tasa del BoJ, que estaba escrita a mano ──────────────────────────────

CSV_BIS = """FREQ,REF_AREA,COMPILATION,TITLE,TIME_PERIOD,OBS_VALUE
D,JP,"From 17 Jun 2026 onwards: the BOJ encourages the uncollateralized overnight call rate to remain at around 1.00 percent; From 22 Dec 2025 to 16 Jun 2026: the BOJ encourages it to remain at around 0.75 percent",Central bank policy rates - Japan,2026-08-18,1
"""


def _responde(monkeypatch, texto, registro=None):
    class Respuesta:
        status_code = 200
        text = texto
        def raise_for_status(self): pass
    def get(url, **kwargs):
        if registro is not None:
            registro.append(url)
        return Respuesta()
    monkeypatch.setattr(extractor_japon.requests, "get", get)


def test_la_tasa_del_boj_sale_de_una_fuente_y_no_de_un_literal(monkeypatch):
    """`tasa_politica_actual: 1.00` estaba escrito a mano en el extractor, en un
    pipeline cuyo principio rector es "100 % del organismo emisor primario".

    El valor resultaba correcto, pero un literal no se entera de una reunion: el
    dia que el BoJ mueva la tasa, el pipeline seguiria informando la vieja sin
    una sola senal de que algo quedo atras.
    """
    urls = []
    _responde(monkeypatch, CSV_BIS, urls)
    datos = extractor_japon.extraer_tasa_politica_boj()

    assert datos["tasa"] == 1.00
    assert "bis.org" in urls[0]


def test_la_tasa_trae_la_fecha_de_la_decision_que_la_fijo(monkeypatch):
    """Es lo que faltaba para poder medir su frescura.

    Una tasa de politica no envejece por dias, pero si por reuniones, y sin la
    fecha de la decision no habia con que compararla. El pipeline terminaba
    fechandola con su PROXIMA reunion, que es al reves.
    """
    _responde(monkeypatch, CSV_BIS)
    datos = extractor_japon.extraer_tasa_politica_boj()
    assert datos["vigente_desde"] == "2026-06-17"


def test_el_calendario_del_boj_da_la_proxima_reunion(monkeypatch):
    """`proxima_reunion: "2026-09-17"` tambien estaba escrita a mano. La fecha
    era correcta, y ese es justamente el problema: nadie se entera cuando deja
    de serlo."""
    html = """<table><tr><td>July 30 (Thurs.), 31 (Fri.)</td></tr>
              <tr><td>Sept. 17 (Thurs.), 18 (Fri.)</td></tr>
              <tr><td>Oct. 29 (Thurs.), 30 (Fri.)</td></tr></table>"""
    _responde(monkeypatch, html)
    # Desde el 26 de agosto, la proxima es la de septiembre y no la de julio.
    assert extractor_japon.extraer_proxima_reunion_boj(
        hoy=date(2026, 8, 26)) == "2026-09-17"
    # Y en octubre ya no puede seguir devolviendo la de septiembre.
    assert extractor_japon.extraer_proxima_reunion_boj(
        hoy=date(2026, 10, 1)) == "2026-10-29"


def test_el_cpi_de_japon_se_declara_como_lo_que_es():
    """No se pudo automatizar: FRED tiene sus series de CPI Japon congeladas en
    junio de 2021, y el Statistics Bureau exige un appId de e-Stat que el
    proyecto no tiene. Se deja escrito a mano, pero DECLARADO: un dato manual
    disfrazado de ingesta es peor que uno manual que lo dice."""
    fuente = Path(extractor_japon.__file__).read_text(encoding="utf-8")
    assert '"origen": "declarado a mano"' in fuente


def test_el_payload_usa_las_fuentes_y_no_vuelve_a_los_literales(monkeypatch, tmp_path):
    """Los tests de arriba prueban las FUNCIONES; este, que el payload las use.

    Sin el, alguien puede volver a escribir la tasa a mano en el payload y la
    suite sigue verde: las funciones seguirian existiendo y andando, solo que
    nadie las llamaria. Lo detecto una prueba de mutacion, no los tests.

    Los valores falsos son deliberadamente distintos de los literales que
    estaban (1.00 y 2026-09-17), para que reaparecer un literal no pueda
    confundirse con un mock que funciono.
    """
    monkeypatch.setattr(extractor_japon, "extraer_tasa_politica_boj",
                        lambda: {"tasa": 7.77, "vigente_desde": "2026-03-03",
                                 "observacion": "2026-08-18", "glosa": "glosa de prueba"})
    monkeypatch.setattr(extractor_japon, "extraer_proxima_reunion_boj",
                        lambda: "2027-01-15")
    monkeypatch.setattr(extractor_japon, "extraer_curva_jgb_mof",
                        lambda: {"jgb_10y_yield": 2.5, "ultima_fecha_oficial": "2026-08-25",
                                 "curva_completa": {}, "historico_reciente": []})
    monkeypatch.setattr(extractor_japon, "obtener_us_10y_y_fx", lambda: (4.5, 150.0))
    monkeypatch.setattr(extractor_japon, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(extractor_japon, "OUTPUT_FILE", tmp_path / "boj_japon_data.json")

    bloque = extractor_japon.ejecutar_extraccion_japon()["politica_monetaria_boj"]

    assert bloque["tasa_politica_actual"] == 7.77, "la tasa volvio a estar escrita a mano"
    assert bloque["proxima_reunion"] == "2027-01-15", "la reunion volvio a estar escrita a mano"
    assert bloque["vigente_desde"] == "2026-03-03"


def test_si_la_fuente_de_la_tasa_cae_el_extractor_no_se_lleva_todo(monkeypatch, tmp_path):
    """El BoJ es un bloque de un payload que trae ademas la curva del MOF. Que
    el BIS no responda no puede costar tambien los datos que si llegaron."""
    def explota():
        raise ConnectionError("el BIS no responde")

    monkeypatch.setattr(extractor_japon, "extraer_tasa_politica_boj", explota)
    monkeypatch.setattr(extractor_japon, "extraer_proxima_reunion_boj", explota)
    monkeypatch.setattr(extractor_japon, "extraer_curva_jgb_mof",
                        lambda: {"jgb_10y_yield": 2.5, "ultima_fecha_oficial": "2026-08-25",
                                 "curva_completa": {}, "historico_reciente": []})
    monkeypatch.setattr(extractor_japon, "obtener_us_10y_y_fx", lambda: (4.5, 150.0))
    monkeypatch.setattr(extractor_japon, "OUTPUT_DIR", tmp_path)
    monkeypatch.setattr(extractor_japon, "OUTPUT_FILE", tmp_path / "boj_japon_data.json")

    payload = extractor_japon.ejecutar_extraccion_japon()

    assert payload["indicadores_financieros"]["jgb_10y_yield"] == 2.5
    # Y la tasa cae a None, que `esta_vencido` traduce en un driver vencido en
    # vez de en un numero inventado.
    assert payload["politica_monetaria_boj"]["tasa_politica_actual"] is None

