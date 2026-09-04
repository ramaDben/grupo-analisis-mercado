"""Contrato del pipeline del carrusel: el payload, el slug y el freno editorial.

Sin MT5 y sin Playwright: se prueba la construcción del payload y la validación,
que es donde están las decisiones. El render ya tiene su propia suite en
`test_story_render.py`.
"""
from __future__ import annotations

import json
import sys
import re
from datetime import datetime
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

import pipeline_carrusel as pc  # noqa: E402
import screener_gi as sc  # noqa: E402

AHORA = datetime(2026, 8, 25, 10, 30, tzinfo=pc.SANTIAGO)

SELECCION = {
    "ticker": "XAGUSD", "nombre": "Plata", "clase": "forex_commodities",
    "direccion": "ALCISTA", "score": 70,
    "precio": 68.716, "soporte": 68.394, "resistencia": 68.974,
    "atr_h1": 0.441, "impulso_adc_atr": 0.661,
    "factores": {"tecnico": {"puntos": 35, "max": 35, "detalle": "quiebre"}},
}

ACTIVO = {
    "ticker": "XAGUSD", "nombre": "Plata", "clase": "forex_commodities",
    "categoria": "commodity", "digits": 3, "unidad": "USD",
    "imagen": "assets/activos/plata.jpg",
    "volatilidad": "alta",
    "nota_volatilidad": (
        "se mueve rápido y en tramos amplios, así que en 15M los movimientos se "
        "desdicen solos; 1H y 4H sostienen mejor la lectura"
    ),
}

def cierres_para(precio: float, n: int = 60, paso: float = 0.01) -> list[float]:
    """Serie de `n` cierres que TERMINA en `precio`.

    Los payloads reales terminan exactamente en el precio: de los 16 que quedaron
    en disco, 15 dan desfase 0,000 y el peor sano da un tick. Las fixtures traian
    series que no llegaban al precio (68,00 a 68,59 contra un precio de 68,716;
    o [1, 2, 3] contra 936,32), y esa incoherencia es justamente la razon por la
    que nadie noto que la invariante no existia. Una fixture imposible no protege.
    """
    return [round(precio - (n - 1 - i) * paso, 6) for i in range(n)]


CIERRES = cierres_para(SELECCION["precio"])


def payload_de_prueba(seleccion=None, activo=None, cierres=None) -> dict:
    sel = seleccion or SELECCION
    return pc.construir_payload(
        sel, activo or ACTIVO, AHORA,
        cierres if cierres is not None else cierres_para(sel["precio"]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Un payload describe UN instante del mercado, o no se publica
# ─────────────────────────────────────────────────────────────────────────────
# Las cifras son las del caso real: GLD.US el 2026-09-04, score 100/100, con el
# precio y la serie leidos en momentos distintos. Su ATR de H1 sale del `vol_pct`
# del payload del dia anterior (3,92 USD = 1,5 x ATR).
GLD = {
    "ticker": "GLD.US", "nombre": "SPDR Gold Shares", "clase": "etfs",
    "direccion": "ALCISTA", "score": 100,
    "precio": 410.37, "soporte": 409.72, "resistencia": 424.45,
    "atr_h1": 2.61, "impulso_adc_atr": 3.92,
    "factores": {},
}
GLD_ACTIVO = {
    "ticker": "GLD.US", "nombre": "SPDR Gold Shares", "clase": "etfs",
    "categoria": "etf", "digits": 2, "unidad": "USD",
    "imagen": "assets/activos/oro.jpg",
}


def test_un_precio_que_no_es_el_ultimo_cierre_de_su_serie_no_se_publica():
    """El caso GLD.US, tal como quedo registrado en PAUSADOS.txt.

    El payload traia precio 410,37 y su propia serie terminaba en 405,32: el
    precio era el cuarto valor desde el final. Con score perfecto y sello
    "DATOS REALES · METATRADER 5", a un paso de un canal de cliente.
    """
    serie = cierres_para(405.32)
    motivo = pc.incoherencia_del_payload(GLD, serie)
    assert motivo is not None
    assert "no es el ultimo cierre de su propia serie" in motivo
    assert "1.93" in motivo          # veces el ATR de H1


def test_construir_payload_se_niega_ante_el_caso_gld():
    """No alcanza con detectarlo: el payload no puede llegar a existir."""
    with pytest.raises(pc.PayloadIncoherenteError) as exc:
        pc.construir_payload(GLD, GLD_ACTIVO, AHORA, cierres_para(405.32))
    assert "GLD.US" in str(exc.value)


def test_el_desfase_de_un_tick_pasa():
    """El unico payload sano de disco con desfase no nulo: USD/JPY, un tick.

    Si el control fuera estricto, la pieza legitima se caeria. Medido: 0,001 de
    desfase sobre un ATR de 0,304, o sea 0,0033 ATR, 75 veces por debajo del tope.
    """
    sel = {**SELECCION, "precio": 163.731, "soporte": 163.400,
           "resistencia": 164.100, "atr_h1": 0.304}
    serie = cierres_para(163.730)
    assert pc.incoherencia_del_payload(sel, serie) is None


def test_un_desfase_exacto_pasa():
    """El caso normal: 15 de los 16 payloads de disco dan desfase 0,000."""
    assert pc.incoherencia_del_payload(SELECCION, cierres_para(SELECCION["precio"])) is None


def test_un_soporte_sobre_el_precio_no_se_publica():
    """Publicar un soporte por encima del precio es publicar un nivel ya roto.

    Este control **no** habria atajado a GLD (410,37 si cae entre 409,72 y
    424,45): sostiene una falla distinta. Se verifica porque es gratis.
    """
    sel = {**SELECCION, "soporte": 68.800}      # sobre el precio de 68,716
    motivo = pc.incoherencia_del_payload(sel, cierres_para(SELECCION["precio"]))
    assert motivo is not None and "no cae entre el soporte" in motivo


def test_sin_atr_el_desfase_no_se_puede_juzgar_y_la_pieza_no_sale():
    """Fail-closed. Sin la escala del activo, "5 de diferencia" no significa nada:
    son cuatro ATR en el oro y un tick en el Nasdaq."""
    sel = {k: v for k, v in SELECCION.items() if k != "atr_h1"}
    motivo = pc.incoherencia_del_payload(sel, cierres_para(SELECCION["precio"]))
    assert motivo is not None and "ATR de H1" in motivo


def test_una_serie_vacia_no_se_publica():
    assert pc.incoherencia_del_payload(SELECCION, []) is not None


def test_el_refresco_detiene_la_pieza_si_el_precio_y_la_serie_se_desacoplan():
    """El refresco vuelve a juntar las dos lecturas, con el mismo acoplamiento
    ciego. Si llegan desacopladas, la pieza se renombra a `.divergente`."""
    from pipeline_carrusel import refrescar_payload

    _, motivo = refrescar_payload(
        _payload_preparado(),
        ahora=datetime(2026, 9, 2, 11, 30),
        h1={"price": 937.80, "s1": 926.90, "r1": 938.27, "atr_14": 2.70,
            "ema_50": 930.00},
        digits=2,
        cierres=cierres_para(930.00, n=3, paso=0.5),
    )
    assert motivo is not None
    assert "no es el ultimo cierre de su propia serie" in motivo


def test_el_refresco_corrige_un_sesgo_obsoleto_sin_ficha_del_playbook():
    """El agujero por el que paso GLD.US, y es el caso mayoritario.

    Antes el sesgo solo se recalculaba `if vigencia_cruda`, y los 33 activos del
    catalogo que no tienen ficha del Playbook llegan con `vigencia: None`. GLD se
    preparo "Alcista" y el H1 vivo daba bajista: la direccion invertida sobrevivio
    el refresco intacta porque esa rama nunca se ejecutaba para el.
    """
    from pipeline_carrusel import refrescar_payload

    payload = _payload_preparado()
    assert payload["_procedencia"]["vigencia"] is None
    assert payload["sesgo"] == "Alcista"

    nuevo, _ = refrescar_payload(
        payload,
        ahora=datetime(2026, 9, 2, 11, 30),
        # El precio quedo BAJO su EMA 50: la lectura de ahora es bajista.
        h1={"price": 928.00, "s1": 926.90, "r1": 938.27, "atr_14": 2.70,
            "ema_50": 934.00},
        digits=2,
        cierres=cierres_para(928.00, n=3, paso=0.5),
    )
    assert nuevo["sesgo"] == "Bajista"
    assert nuevo["tag_riesgo"] == "BAJISTA"


def test_el_refresco_no_deriva_la_direccion_del_propio_payload():
    """Era circular: `tecnica` se leia del string `nuevo["sesgo"]`, asi que un
    sesgo que venia mal se confirmaba a si mismo. Ahora sale del mercado."""
    from pipeline_carrusel import refrescar_payload

    payload = _payload_preparado()
    payload["sesgo"] = "Bajista"          # el payload afirma lo contrario
    payload["tag_riesgo"] = "BAJISTA"

    nuevo, _ = refrescar_payload(
        payload,
        ahora=datetime(2026, 9, 2, 11, 30),
        h1={"price": 937.80, "s1": 926.90, "r1": 938.27, "atr_14": 2.70,
            "ema_50": 930.00},          # precio SOBRE la EMA 50: alcista
        digits=2,
        cierres=cierres_para(937.80, n=3, paso=0.5),
    )
    assert nuevo["sesgo"] == "Alcista"


def test_sin_ema50_el_refresco_no_confirma_la_direccion_y_detiene_la_pieza():
    """Fail-closed: sin la media no hay con que contrastar el sesgo escrito."""
    from pipeline_carrusel import refrescar_payload

    _, motivo = refrescar_payload(
        _payload_preparado(),
        ahora=datetime(2026, 9, 2, 11, 30),
        h1={"price": 937.80, "s1": 926.90, "r1": 938.27, "atr_14": 2.70},
        digits=2,
        cierres=cierres_para(937.80, n=3, paso=0.5),
    )
    assert motivo is not None and "EMA 50" in motivo


def test_ningun_payload_de_disco_es_incoherente():
    """Contrato contra los payloads reales que quedaron en `data/carrusel/`.

    `data/carrusel/` esta gitignoreado, asi que en un clon nuevo este test no
    tiene nada que mirar y se salta. Cuando hay tandas en disco, ninguna puede
    contener un payload que el control de hoy rechazaria: si aparece uno, o el
    umbral esta mal calibrado o volvio el defecto.
    """
    import glob

    revisados = 0
    for ruta in glob.glob("data/carrusel/*/0*/[1-9]_*.json"):
        datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
        crudos = (datos.get("_procedencia") or {}).get("crudos")
        serie = (datos.get("recorrido") or {}).get("serie")
        if not crudos or not serie:
            continue
        vol = datos.get("vol_pct") or ""
        cifra = re.match(r"^([\d.]*\d)(?:,(\d+))?", str(vol))
        if not cifra:
            continue
        valor = float(cifra.group(1).replace(".", "")
                      + ("." + cifra.group(2) if cifra.group(2) else ""))
        sel = {
            "ticker": datos.get("activo", "?"),
            "precio": crudos["precio"],
            "soporte": crudos["soporte"],
            "resistencia": crudos["resistencia"],
            "atr_h1": valor / 1.5,          # vol_pct = 1,5 x ATR de H1
        }
        assert pc.incoherencia_del_payload(sel, serie) is None, ruta
        revisados += 1

    if not revisados:
        pytest.skip("no hay tandas en data/carrusel/ (esta gitignoreado)")


# ─────────────────────────────────────────────────────────────────────────────
# El slug: imagen y color salen del mismo dato
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("imagen, slug", [
    ("assets/activos/oro.jpg", "oro"),
    ("assets/activos/plata.jpg", "plata"),
    ("assets/activos/us100.jpg", "us100"),
    ("assets/activos/tech-circuito.jpg", "tech-circuito"),
])
def test_el_slug_es_el_nombre_del_archivo_de_imagen(imagen, slug):
    assert pc._slug_de_imagen(imagen) == slug


def test_un_etf_que_replica_un_indice_hereda_su_identidad_visual():
    """`GLD.US` usa `oro.jpg`, así que su pieza sale dorada como la del Oro. No es
    un accidente: a la vista del cliente no son dos activos distintos."""
    gld = {**ACTIVO, "ticker": "GLD.US", "nombre": "SPDR Gold Shares",
           "digits": 2, "imagen": "assets/activos/oro.jpg"}
    payload = payload_de_prueba({**SELECCION, "ticker": "GLD.US"}, gld)
    assert payload["activo_slug"] == "oro"


def test_cada_slug_del_universo_renderizable_tiene_token_de_color():
    """Si un activo tiene imagen pero no token, su pieza sale con cromo de marca
    contra una foto de otro tono. Pasó con XAGUSD, #MELI y SOXX.US."""
    import screener_gi as sc

    marca = (RAIZ / "templates" / "stories" / "marca.css").read_text(encoding="utf-8")
    faltan = []
    for activo in sc.cargar_universo(solo_renderizables=True):
        slug = pc._slug_de_imagen(activo["imagen"])
        if f"body.activo-{slug}" not in marca:
            faltan.append(f"{activo['ticker']} -> activo-{slug}")
    assert not faltan, "slugs sin token de color en marca.css: " + ", ".join(faltan)


# ─────────────────────────────────────────────────────────────────────────────
# El payload
# ─────────────────────────────────────────────────────────────────────────────
def test_los_precios_respetan_los_decimales_del_catalogo_en_notacion_chilena():
    """La regla de decimales del proyecto: se respeta `digits` y nunca se truncan
    ceros. La notación es la chilena: punto para miles, coma para decimales."""
    payload = payload_de_prueba()
    assert payload["precio_actual"] == "68,716"     # 3 digits
    assert payload["soporte"] == "68,394"
    assert payload["resistencia"] == "68,974"

    us100 = {**ACTIVO, "ticker": "US100.spot", "nombre": "Nasdaq 100", "digits": 2,
             "unidad": "puntos", "imagen": "assets/activos/us100.jpg"}
    grande = payload_de_prueba(
        {**SELECCION, "ticker": "US100.spot", "precio": 29225.28,
         "soporte": 29000.5, "resistencia": 29400.0},
        us100,
    )
    assert grande["precio_actual"] == "29.225,28"
    assert grande["soporte"] == "29.000,50", "no se truncan ceros al final"
    assert grande["resistencia"] == "29.400,00"


def test_los_campos_editoriales_nacen_vacios_y_marcados():
    """Un script no tiene criterio editorial: el titular y el párrafo los escribe
    el comando."""
    payload = payload_de_prueba()
    for campo in pc.CAMPOS_EDITORIALES:
        assert payload[campo] == ""
    assert payload["_pendiente_editorial"] == list(pc.CAMPOS_EDITORIALES)


def test_la_volatilidad_sale_en_la_moneda_en_que_cotiza_el_activo():
    """`vol_pct` alimenta el bloque "Volatilidad típica" de la Story.

    Decía "pts" para todos, y puntos solo es correcto para un índice: el Oro se
    mueve en dólares, el USD/CLP en pesos y el USD/JPY en yenes. Una distancia
    de precio sin su unidad no se puede leer, y con la unidad equivocada se lee
    mal, que es peor.

    Se usa el código de moneda y no el símbolo a propósito: en Chile `$` es
    ambiguo entre peso y dólar, y esta cifra aparece justo al lado de dos
    precios en una pieza que ve el cliente.
    """
    plata = payload_de_prueba()                       # XAGUSD, cotiza en dólares
    assert plata["vol_pct"] == "0,661 USD"

    clp = payload_de_prueba(
        {**SELECCION, "ticker": "USDCLP"},
        {**ACTIVO, "ticker": "USDCLP", "nombre": "Dólar / Peso Chileno",
         "digits": 2, "unidad": "CLP", "imagen": "assets/activos/usdclp.jpg"},
    )
    assert clp["vol_pct"] == "0,66 CLP"

    indice = payload_de_prueba(
        {**SELECCION, "ticker": "US100.spot"},
        {**ACTIVO, "ticker": "US100.spot", "nombre": "Nasdaq 100",
         "digits": 2, "unidad": "puntos", "imagen": "assets/activos/us100.jpg"},
    )
    assert indice["vol_pct"] == "0,66 puntos"


def test_la_volatilidad_no_afirma_un_recorrido_futuro():
    """El rótulo del bloque no puede sugerir a qué precio va a llegar el activo.

    La pieza no lleva firma acreditada -esa es `recomendacion`-, así que un
    precio objetivo la convertiría en una recomendación de inversión sin quién
    la respalde. El ATR es un promedio de rangos pasados: describe cuánto se
    mueve el instrumento, no hacia dónde va. El rótulo tiene que decir eso y no
    otra cosa, sobre todo porque a diez centímetros hay una píldora que sí
    marca dirección y el cliente compone las dos lecturas.
    """
    plantilla = (
        Path(__file__).resolve().parents[1] / "templates" / "stories" / "alerta.html"
    ).read_text(encoding="utf-8")
    # Solo los rótulos VISIBLES. Buscar en todo el archivo daría un falso
    # positivo con cualquier comentario que explique por qué el bloque no
    # proyecta, que es justo lo que queremos que alguien escriba.
    rotulos = re.findall(r'<div class="stat-label">([^<]+)</div>', plantilla)
    assert "Volatilidad típica" in rotulos
    for rotulo in rotulos:
        bajo = rotulo.lower()
        for prohibido in ("objetivo", "impulso", "proyect", "esperad", "target"):
            assert prohibido not in bajo, (
                f"el rótulo {rotulo!r} insinúa un destino de precio; la pieza no "
                "lleva firma acreditada y no puede recomendar"
            )


def test_el_recorrido_pide_lienzo_alto_y_ancla_el_ahora_al_ultimo_cierre():
    """El marcador `actual` va al extremo derecho por definición de su rol, no
    por parecido de precio."""
    payload = payload_de_prueba()
    rec = payload["recorrido"]
    assert rec["lienzo"] == "alto"
    assert len(rec["serie"]) == pc.VELAS_GRAFICO
    assert rec["marcadores"][0]["indice"] == pc.VELAS_GRAFICO - 1
    assert rec["marcadores"][0]["rol"] == "AHORA"
    roles = {n["rol"] for n in rec["niveles"]}
    assert roles == {"RESISTENCIA", "SOPORTE"}


def test_la_direccion_bajista_cambia_sesgo_y_tag_pero_no_el_color_del_activo():
    """Identidad del activo y dirección de mercado son roles de color distintos:
    si se colapsaran, una pieza plateada bajista se leería como alcista."""
    payload = payload_de_prueba({**SELECCION, "direccion": "BAJISTA"})
    assert payload["sesgo"] == "Bajista"
    assert payload["tag_riesgo"] == "BAJISTA"
    assert payload["activo_slug"] == "plata", "el slug no depende de la direccion"


def test_la_procedencia_del_score_viaja_con_el_payload():
    """Deja auditable por qué este activo y no otro, al lado de la pieza que
    produjo. No se rinde: las claves con guion bajo se quitan antes del render."""
    payload = payload_de_prueba()
    assert payload["_procedencia"]["score"] == 70
    assert payload["_procedencia"]["ticker"] == "XAGUSD"


# ─────────────────────────────────────────────────────────────────────────────
# El freno editorial
# ─────────────────────────────────────────────────────────────────────────────
def test_rendir_se_niega_si_falta_el_texto_editorial(tmp_path):
    """Misma razón que el fail-fast de imagen: una pieza a medias que sale sin
    avisar llega al cliente."""
    (tmp_path / "1_xagusd.json").write_text(
        json.dumps(payload_de_prueba(), ensure_ascii=False), encoding="utf-8"
    )
    with pytest.raises(SystemExit) as exc:
        pc.rendir(tmp_path)
    mensaje = str(exc.value)
    assert "titular" in mensaje and "parrafo" in mensaje


def test_rendir_no_acepta_un_titular_de_solo_espacios(tmp_path):
    payload = payload_de_prueba()
    payload["titular"] = "   "
    payload["parrafo"] = "texto real"
    (tmp_path / "1_xagusd.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        pc.rendir(tmp_path)
    assert "titular" in str(exc.value)


def test_rendir_falla_claro_si_el_directorio_no_tiene_payloads(tmp_path):
    """Los archivos que empiezan con guion bajo son insumos, no piezas."""
    (tmp_path / "_screener.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        pc.rendir(tmp_path)
    assert "No hay payloads" in str(exc.value)


def test_el_universo_del_escaner_trae_lo_que_el_payload_consume():
    """Contrato entre `cargar_universo` y `construir_payload`, contra el catalogo REAL.

    `cargar_universo` no pasa el activo del catalogo tal cual: lo PROYECTA a un
    puñado de campos. Un campo nuevo en config/activos.json no llega solo al
    pipeline, hay que agregarlo tambien a esa proyeccion.

    Los demas tests de este archivo arman el activo a mano con un dict de
    prueba, asi que no pueden ver esa divergencia: verifican el fixture, no la
    proyeccion. Cuando se agrego `unidad` al catalogo, el fixture se actualizo
    y la proyeccion no, y el carrusel reventaba con KeyError en la primera
    tanda real con todos los tests en verde.

    Por eso este test usa el universo de verdad y no un dict inventado.
    """
    universo = sc.cargar_universo(solo_renderizables=True)
    assert universo, "el catalogo debe tener activos renderizables"

    for activo in universo:
        payload = pc.construir_payload(
            {**SELECCION, "ticker": activo["ticker"]},
            activo,
            datetime(2026, 8, 26, 9, 15),
            CIERRES,
        )
        assert payload["vol_pct"].endswith(activo["unidad"]), activo["ticker"]
        assert payload["activo_imagen"], activo["ticker"]


def test_preparar_barre_los_payloads_de_la_corrida_anterior(tmp_path):
    """Dos corridas de la misma tanda no pueden acumular piezas.

    El directorio es por fecha y tanda, asi que correr `--preparar` dos veces
    -por un reintento, o porque el escaner eligio distinto al volver a mirar-
    dejaba los payloads viejos al lado de los nuevos. Y `rendir()` toma TODOS
    los .json sin prefijo `_`, no una lista: la tanda salia con 5 piezas en vez
    de 3, dos de ellas de activos que el escaner ya habia descartado y con
    precios de horas antes.

    El tope de 3 no es estetico: a partir de la cuarta imagen WhatsApp colapsa
    el resto detras de un `+2` y el cliente no las ve.
    """
    viejo = tmp_path / "2_us100spot.json"
    viejo.write_text('{"plantilla": "alerta"}', encoding="utf-8")
    conservar = tmp_path / "_screener.json"
    conservar.write_text('{"tanda": 1}', encoding="utf-8")

    pc.limpiar_payloads(tmp_path)

    assert not viejo.exists(), "el payload de la corrida anterior sobrevivio"
    assert conservar.exists(), "se llevo puesto el registro del escaner"


# ─────────────────────────────────────────────────────────────────────────────
# Modularización de grupos de WhatsApp
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("cat, ticker, grupo_esperado", [
    ("forex", "USDCLP", "02_forex_divisas"),
    ("forex", "EURUSD", "02_forex_divisas"),
    ("forex", "USDJPY", "02_forex_divisas"),
    ("commodity", "XAUUSD", "03_commodities_materias_primas"),
    ("commodity", "WTI.spot", "03_commodities_materias_primas"),
    ("commodity", "COPPER", "03_commodities_materias_primas"),
    ("crypto", "BTCUSD", "06_criptoactivos"),
    ("crypto", "ETHUSD", "06_criptoactivos"),
    ("indices", "US100.spot", "04_indices_bursatiles"),
    ("indices", "US500.spot", "04_indices_bursatiles"),
    ("acciones", "#AAPL", "05_acciones_etfs"),
    ("acciones", "#MELI", "05_acciones_etfs"),
    ("etfs", "QQQ.US", "05_acciones_etfs"),
    ("etfs", "SOXX.US", "05_acciones_etfs"),
])
def test_obtener_grupo_whatsapp_mapea_correctamente_cada_categoria(cat, ticker, grupo_esperado):
    assert pc.obtener_grupo_whatsapp(cat, ticker) == grupo_esperado


# ─────────────────────────────────────────────────────────────────────────────
# El canal de avisos llega por intención, no por un default
# ─────────────────────────────────────────────────────────────────────────────
SLUGS_DE_CANAL = [
    "01_macro_y_apertura",
    "02_forex_divisas",
    "03_commodities_materias_primas",
    "04_indices_bursatiles",
    "05_acciones_etfs",
    "06_criptoactivos",
    "07_oportunidades_cuantitativas",
]


def test_una_categoria_desconocida_falla_en_vez_de_caer_al_canal_de_avisos():
    """El default silencioso publicaba en el grupo de la comunidad.

    `MAPEO_GRUPOS_WHATSAPP.get(clave, "01_macro_y_apertura")` convertía cualquier
    categoría que no reconociéramos en un envío al canal de avisos, que es el que
    más gente lee. Ninguna categoría real del universo necesita ese default
    (verificado contra `cargar_universo`), así que su único efecto era tapar
    errores de nombre.
    """
    with pytest.raises(pc.GrupoDesconocidoError):
        pc.obtener_grupo_whatsapp("categoria_que_no_existe", "")


@pytest.mark.parametrize("slug", SLUGS_DE_CANAL)
def test_el_slug_de_un_canal_no_se_confunde_con_una_categoria(slug):
    """Es el defecto exacto del 2026-09-04.

    `preparar` pasaba a `obtener_grupo_whatsapp` el slug ya resuelto por
    `resolver_grupo_solicitado`, y esta función espera una categoría. Ninguna rama
    aplicaba, caía al default, y **todo** `--preparar --grupo <canal>` terminaba
    escribiéndole contexto macro al canal de avisos en vez de al canal pedido.
    """
    with pytest.raises(pc.GrupoDesconocidoError):
        pc.obtener_grupo_whatsapp(slug, "")


def test_el_canal_pedido_recibe_contexto_macro_aunque_no_tenga_piezas():
    """Era el daño de fondo, y no se veía.

    Con el canal pedido vacío, `grupos_activos` quedaba en {avisos}: el canal que
    el director pidió no recibía **nada** y el macro se lo llevaba entero el grupo
    de la comunidad. Asegurar el canal pedido era justamente la intención de esa
    línea, y nunca funcionó.
    """
    canales = pc.canales_con_contexto_macro([], grupo_pedido="04_indices_bursatiles")
    assert "04_indices_bursatiles" in canales


def test_el_canal_de_avisos_recibe_el_macro_por_declaracion():
    """Decisión del director el 2026-09-03: el macro vive en Avisos.

    Se conserva, pero declarada. Antes el mismo resultado salía del default de
    `obtener_grupo_whatsapp`, así que habría seguido ocurriendo aunque la decisión
    hubiera sido la contraria.
    """
    canales = pc.canales_con_contexto_macro([], grupo_pedido=None)
    assert canales == {"01_macro_y_apertura"}


def test_los_canales_con_piezas_reciben_su_contexto_macro():
    payloads = [{"grupo": "06_criptoactivos"}, {"grupo": "03_commodities_materias_primas"}]
    canales = pc.canales_con_contexto_macro(payloads, grupo_pedido=None)
    assert canales == {
        "01_macro_y_apertura",
        "03_commodities_materias_primas",
        "06_criptoactivos",
    }


# ─────────────────────────────────────────────────────────────────────────────
# La temporalidad, justificada por la volatilidad del activo
# ─────────────────────────────────────────────────────────────────────────────
def test_el_mensaje_justifica_la_temporalidad_con_la_volatilidad_del_activo():
    """`CLAUDE.md` la declara OBLIGATORIA desde el issue #44 y nunca se implemento:
    el token `por_que_temporalidad` existia en un solo lugar del repo, que era la
    propia norma. El 2026-09-04 dos piezas salieron sin el bloque.
    """
    msg = pc.construir_mensaje_alerta(payload_de_prueba())
    assert "⏱️ *Temporalidad*" in msg
    assert "Por qué 1H acá" in msg
    # La justificacion es la del activo, no una frase generica.
    assert "los movimientos se desdicen solos" in msg


def test_la_temporalidad_usa_la_etiqueta_canonica_de_su_marco():
    """Cuatro etiquetas y ni una mas: prohibido decir "corto" sin numero."""
    msg = pc.construir_mensaje_alerta(payload_de_prueba())
    assert "1H · marco intradía (dentro de la jornada)" in msg


def test_las_cuatro_etiquetas_canonicas_calzan_con_las_documentadas():
    """El contrato que evita el tercer reloj.

    Las etiquetas vivian SOLO en markdown (`CLAUDE.md` y `.claude/commands/story.md`)
    y ahora tambien en codigo, que es lo que las publica. Tres copias de la misma
    tabla divergen: la de `apertura.md` que `CLAUDE.md` todavia nombra como fuente
    unica ni existe, porque ese comando se retiro.
    """
    tabla = (RAIZ / ".claude" / "commands" / "story.md").read_text(encoding="utf-8")
    filas = dict(re.findall(r"\|\s*`(15M|1H|4H|1D)`\s*\|\s*([^|]+?)\s*\|", tabla))
    assert len(filas) == 4, f"la tabla de story.md cambio de forma: {filas}"
    for marco, (etiqueta, descripcion) in pc.MARCOS_CANONICOS.items():
        assert filas[etiqueta] == descripcion, (
            f"{marco}: el codigo dice {descripcion!r} y story.md dice {filas[etiqueta]!r}"
        )


def test_sin_nota_de_volatilidad_el_payload_no_se_construye():
    """Fail-closed, igual que con `unidad`: la linea es obligatoria, asi que un
    activo sin su nota no puede producir una pieza a medias en silencio."""
    activo = {k: v for k, v in ACTIVO.items() if k != "nota_volatilidad"}
    with pytest.raises(KeyError):
        pc.construir_payload(SELECCION, activo, AHORA, CIERRES)


def test_una_banda_estrecha_se_estampa_en_el_mensaje():
    """Zona de aviso del gate de banda: la pieza sale, pero diciendo que sus
    bordes son estrechos para lo que ese activo se mueve."""
    sel = {**SELECCION, "banda_estrecha": 0.80}
    msg = pc.construir_mensaje_alerta(payload_de_prueba(seleccion=sel))
    assert "niveles estrechos" in msg.lower()


def test_sin_banda_estrecha_no_se_estampa_nada():
    msg = pc.construir_mensaje_alerta(payload_de_prueba())
    assert "estrechos" not in msg.lower()


def test_construir_mensaje_alerta_cumple_reglas_canonicas_whatsapp():
    payload = payload_de_prueba()
    payload["titular"] = "Quiebre alcista sobre 68,97"
    payload["parrafo"] = "La plata consolida fuerza compradora tras cruzar la resistencia técnica."
    msg = pc.construir_mensaje_alerta(payload)

    # 1. Resumen al inicio
    assert "🎯 Activo:" in msg
    assert "📌 Nivel a vigilar:" in msg
    assert "⚡ Qué esperar:" in msg

    # 2. Separadores
    assert "━━━━━━━━━━━━━━━━━━━" in msg

    # 3. Código de emojis de escenarios
    assert "🟢 Sobre" in msg
    assert "🟡 Entre" in msg
    assert "🔴 Bajo" in msg

    # 4. Niveles y cifras
    assert "68,716" in msg
    assert "0,661 USD" in msg




# ---------------------------------------------------------------------------
# El destino que pide el director se resuelve contra el config, o falla fuerte
# ---------------------------------------------------------------------------

def test_el_grupo_pedido_se_resuelve_con_los_alias_del_config():
    """`--grupo metales` tiene que llegar a Metales & Energía, no al cajón macro."""
    from pipeline_carrusel import resolver_grupo_solicitado
    casos = {
        "commodities": "03_commodities_materias_primas",
        "metales": "03_commodities_materias_primas",
        "oro": "03_commodities_materias_primas",
        "Grupo Inteligencia | Metales & Energía": "03_commodities_materias_primas",
        "cripto": "06_criptoactivos",
        "crypto": "06_criptoactivos",
        "forex": "02_forex_divisas",
        "indices": "04_indices_bursatiles",
    }
    for pedido, esperado in casos.items():
        assert resolver_grupo_solicitado(pedido) == esperado, pedido


def test_un_grupo_desconocido_aborta_en_vez_de_caer_al_canal_macro():
    """Un destino que no se reconoce publica en el canal equivocado: mejor detenerse."""
    import pytest as _pytest
    from pipeline_carrusel import GrupoDesconocidoError, resolver_grupo_solicitado
    with _pytest.raises(GrupoDesconocidoError):
        resolver_grupo_solicitado("bonos soberanos")


# ---------------------------------------------------------------------------
# Despacho por lote: la tanda de un canal sale en una acción, y cada pieza
# se rinde justo antes de salir para que el precio no llegue viejo.
# ---------------------------------------------------------------------------


def _carpeta_de_grupo(tmp_path):
    """Reproduce la forma real de una carpeta de grupo ya rendida."""
    d = tmp_path / "02_forex_divisas"
    d.mkdir()
    for nombre in [
        "0_contexto_macro.png", "1_usdclp.png", "2_usdjpy.png", "3_gbpusd.png",
        # Copias sin prefijo que deja `rendir`: NO son piezas nuevas.
        "contexto_macro.png",
    ]:
        (d / nombre).write_bytes(b"x")
    (d / "0_contexto_macro.txt").write_text("agenda del dia", encoding="utf-8")
    (d / "1_usdclp_mensaje.txt").write_text("usdclp", encoding="utf-8")
    (d / "2_usdjpy_mensaje.txt").write_text("usdjpy", encoding="utf-8")
    (d / "3_gbpusd_mensaje.txt").write_text("gbpusd", encoding="utf-8")
    (d / "contexto_macro.txt").write_text("agenda del dia", encoding="utf-8")
    (d / "mensaje.txt").write_text("gbpusd", encoding="utf-8")
    return d


def test_las_piezas_del_grupo_salen_con_el_macro_primero_y_en_orden(tmp_path):
    """El orden canónico del proyecto: la agenda arriba, los niveles después."""
    from pipeline_carrusel import piezas_del_grupo

    piezas = piezas_del_grupo(_carpeta_de_grupo(tmp_path))

    assert [p.adjunto.name for p in piezas] == [
        "0_contexto_macro.png",
        "1_usdclp.png",
        "2_usdjpy.png",
        "3_gbpusd.png",
    ]
    assert piezas[0].mensaje == "agenda del dia"
    assert piezas[3].mensaje == "gbpusd"


def test_las_copias_sin_prefijo_no_se_despachan_dos_veces(tmp_path):
    """`rendir` deja `contexto_macro.png` y `mensaje.txt` como copias.

    Contarlas como piezas mandaría la agenda dos veces al mismo canal.
    """
    from pipeline_carrusel import piezas_del_grupo

    nombres = [p.adjunto.name for p in piezas_del_grupo(_carpeta_de_grupo(tmp_path))]
    assert "contexto_macro.png" not in nombres
    assert len(nombres) == len(set(nombres))


def test_una_pieza_sin_su_mensaje_aborta_en_vez_de_salir_muda(tmp_path):
    from pipeline_carrusel import PiezaSinMensajeError, piezas_del_grupo

    d = _carpeta_de_grupo(tmp_path)
    (d / "2_usdjpy_mensaje.txt").unlink()

    with pytest.raises(PiezaSinMensajeError, match="2_usdjpy"):
        piezas_del_grupo(d)


def test_divergencia_detecta_que_el_precio_perforo_el_soporte():
    """El texto dice 'se apoya en el soporte' y el precio ya lo perforó."""
    from pipeline_carrusel import divergencia_editorial

    crudos = {"precio": 936.32, "soporte": 926.90, "resistencia": 938.27}
    motivo = divergencia_editorial(crudos, precio_nuevo=924.10)

    assert motivo is not None
    assert "soporte" in motivo.lower()


def test_divergencia_detecta_que_el_precio_quebro_la_resistencia():
    from pipeline_carrusel import divergencia_editorial

    crudos = {"precio": 936.32, "soporte": 926.90, "resistencia": 938.27}
    motivo = divergencia_editorial(crudos, precio_nuevo=941.00)

    assert motivo is not None
    assert "resistencia" in motivo.lower()


def test_sin_cruzar_ningun_nivel_no_hay_divergencia():
    """Que el precio se mueva es normal: solo importa si invalida el texto."""
    from pipeline_carrusel import divergencia_editorial

    crudos = {"precio": 936.32, "soporte": 926.90, "resistencia": 938.27}
    assert divergencia_editorial(crudos, precio_nuevo=937.80) is None


def test_sin_precios_crudos_no_se_puede_juzgar_y_se_avisa():
    """Un payload viejo sin `_crudos` no permite comparar: no se finge que sí."""
    from pipeline_carrusel import divergencia_editorial

    motivo = divergencia_editorial({}, precio_nuevo=100.0)
    assert motivo is not None
    assert "no se pudo" in motivo.lower()


def test_el_payload_preparado_guarda_los_precios_crudos():
    """Sin los números sin formatear, el corte por divergencia es imposible.

    El payload solo lleva precios ya en notación chilena ('936,32'), que sirven
    para dibujar pero no para comparar.
    """
    from pipeline_carrusel import construir_payload

    seleccion = {
        "ticker": "USDCLP", "direccion": "ALCISTA", "clase": "forex",
        "precio": 936.32, "soporte": 926.90, "resistencia": 938.27,
        "impulso_adc_atr": 4.02, "atr_h1": 2.68, "score": 71, "factores": {},
    }
    activo = {
        "nombre": "Dólar / Peso Chileno", "digits": 2, "imagen": "dolar.jpg",
        "categoria": "forex", "unidad": "CLP", "volatilidad": "baja",
        "nota_volatilidad": (
            "se mueve poco dentro del día, así que marcos más amplios (1H/4H) dan "
            "una lectura más limpia; en 15M aparece mucho ruido"
        ),
    }
    payload = construir_payload(
        seleccion, activo, datetime(2026, 9, 2, 10, 0),
        cierres_para(seleccion["precio"], n=3, paso=0.5),
    )

    crudos = payload["_procedencia"]["crudos"]
    assert crudos["precio"] == 936.32
    assert crudos["soporte"] == 926.90
    assert crudos["resistencia"] == 938.27


def _payload_preparado():
    from pipeline_carrusel import construir_payload
    seleccion = {
        "ticker": "USDCLP", "direccion": "ALCISTA", "clase": "forex",
        "precio": 936.32, "soporte": 926.90, "resistencia": 938.27,
        "impulso_adc_atr": 4.02, "atr_h1": 2.68, "score": 71, "factores": {},
    }
    activo = {
        "nombre": "Dólar / Peso Chileno", "digits": 2, "imagen": "dolar.jpg",
        "categoria": "forex", "unidad": "CLP", "volatilidad": "baja",
        "nota_volatilidad": (
            "se mueve poco dentro del día, así que marcos más amplios (1H/4H) dan "
            "una lectura más limpia; en 15M aparece mucho ruido"
        ),
    }
    p = construir_payload(
        seleccion, activo, datetime(2026, 9, 2, 10, 0),
        cierres_para(seleccion["precio"], n=3, paso=0.5),
    )
    p["titular"] = "Dólar consolida sobre $935"
    p["parrafo"] = "La cotización presiona la resistencia."
    return p


def test_el_refresco_actualiza_las_cifras_y_el_sello_de_datos():
    """La pieza se rinde justo antes de salir: su sello no puede mentir la hora."""
    from pipeline_carrusel import refrescar_payload

    payload = _payload_preparado()
    sello_viejo = payload["sello_datos"]

    nuevo, motivo = refrescar_payload(
        payload,
        ahora=datetime(2026, 9, 2, 11, 30),
        h1={"price": 937.80, "s1": 926.90, "r1": 938.27, "atr_14": 2.70,
            "ema_50": 930.00},
        digits=2,
        cierres=cierres_para(937.80, n=3, paso=0.5),
    )

    assert motivo is None
    assert nuevo["precio_actual"] == "937,80"
    assert nuevo["_procedencia"]["crudos"]["precio"] == 937.80
    assert nuevo["sello_datos"] != sello_viejo
    assert "11:30" in nuevo["sello_datos"]


def test_el_refresco_conserva_el_texto_editorial():
    """El refresco toca las cifras, no el criterio de quien escribió."""
    from pipeline_carrusel import refrescar_payload

    nuevo, _ = refrescar_payload(
        _payload_preparado(),
        ahora=datetime(2026, 9, 2, 11, 30),
        h1={"price": 937.80, "s1": 926.90, "r1": 938.27, "atr_14": 2.70,
            "ema_50": 930.00},
        digits=2,
        cierres=cierres_para(937.80, n=3, paso=0.5),
    )
    assert nuevo["titular"] == "Dólar consolida sobre $935"
    assert nuevo["parrafo"] == "La cotización presiona la resistencia."


def test_el_refresco_avisa_cuando_el_precio_invalido_el_texto():
    from pipeline_carrusel import refrescar_payload

    _, motivo = refrescar_payload(
        _payload_preparado(),
        ahora=datetime(2026, 9, 2, 11, 30),
        h1={"price": 924.10, "s1": 926.90, "r1": 938.27, "atr_14": 2.70,
            "ema_50": 930.00},
        digits=2,
        cierres=cierres_para(924.10, n=3, paso=0.5),
    )
    assert motivo is not None and "soporte" in motivo.lower()


# ─────────────────────────────────────────────────────────────────────────────
# Las dos gramaticas de vigencia
# ─────────────────────────────────────────────────────────────────────────────
VIGENCIA_NIVEL = {
    "gramatica": "NIVEL", "direccion": "LARGO",
    "nivel": 933.44, "borde_inferior": None, "borde_superior": None,
    "multiplo_atr": 3.0, "lookback": 22, "vigente": True,
    "take_profit_tipo": "TRAILING_STOP_ASYMMETRIC",
}

VIGENCIA_RANGO = {
    "gramatica": "RANGO", "direccion": None,
    "nivel": None, "borde_inferior": 68.394, "borde_superior": 68.974,
    "multiplo_atr": None, "lookback": None, "vigente": True,
    "take_profit_tipo": "NIVEL_OPUESTO_CANAL",
}


def _mensaje_con(vigencia, direccion="ALCISTA"):
    payload = pc.construir_payload(
        {**SELECCION, "direccion": direccion, "vigencia": vigencia},
        ACTIVO, AHORA, CIERRES,
    )
    payload["titular"] = "La plata se apoya en su soporte"
    payload["parrafo"] = "El metal sostiene el nivel."
    return pc.construir_mensaje_alerta(payload), payload


def test_un_sesgo_sostenido_se_comunica_como_un_solo_hasta_donde():
    """`TRAILING_STOP_ASYMMETRIC` significa posicion sostenida: la lectura vale
    mientras el precio no pierda el Chandelier. Un nivel, no un rango."""
    mensaje, payload = _mensaje_con(VIGENCIA_NIVEL)

    assert payload["vigencia"]["gramatica"] == "NIVEL"
    assert "vigente hasta 933,440" in mensaje
    assert "rota entre" not in mensaje


def test_un_activo_en_rango_se_comunica_entre_dos_bordes():
    """`NIVEL_OPUESTO_CANAL` es score cero: no hay tendencia que sostener, hay un
    canal. Decir "vigente hasta X" ahi afirmaria una direccion inexistente."""
    mensaje, _ = _mensaje_con(VIGENCIA_RANGO)

    assert "rota entre 68,394 y 68,974" in mensaje
    assert "vigente hasta" not in mensaje


def test_las_dos_gramaticas_no_producen_el_mismo_texto():
    """El defecto que este cambio cierra: el carrusel las trataba igual. Un
    activo sostenido y uno en rotacion salian con el mismo cierre, y el cliente
    no tenia forma de distinguir "sigue vigente hasta X" de "no hay direccion"."""
    sostenido, _ = _mensaje_con(VIGENCIA_NIVEL)
    rotando, _ = _mensaje_con(VIGENCIA_RANGO)

    assert sostenido != rotando


def test_sin_vigencia_el_mensaje_no_inventa_un_hasta_donde():
    """Fail-closed y sin perder el cierre canonico: la lectura practica de tres
    escenarios es obligatoria en todo mensaje, con Playbook o sin el."""
    mensaje, payload = _mensaje_con(None)

    assert payload["vigencia"] is None
    assert "vigente hasta" not in mensaje and "rota entre" not in mensaje
    assert "🟢 Sobre" in mensaje and "🟡 Entre" in mensaje and "🔴 Bajo" in mensaje


def test_un_sesgo_ya_invalidado_lo_dice_en_vez_de_afirmar_vigencia():
    """Brent el 2026-09-02: sesgo +1,50 con el precio ya bajo su Chandelier.
    Publicar "sigue vigente" ahi es afirmar lo contrario de lo que pasa."""
    mensaje, _ = _mensaje_con({**VIGENCIA_NIVEL, "vigente": False})

    assert "vigente hasta" not in mensaje
    assert "invalid" in mensaje.lower()


def test_una_direccion_de_playbook_contraria_a_la_tecnica_no_se_publica():
    """Nunca dos direcciones opuestas en el mismo mensaje. La lectura tecnica
    dice compradores y el Playbook dice corto: el mensaje callaria la vigencia
    antes que contradecirse a si mismo en dos lineas seguidas."""
    _, payload = _mensaje_con({**VIGENCIA_NIVEL, "direccion": "CORTO"}, direccion="ALCISTA")

    assert payload["vigencia"] is None
    assert "contradice" in payload["_procedencia"]["vigencia_omitida"].lower()


def test_la_vigencia_viaja_cruda_en_la_procedencia():
    """El despacho necesita el numero, no el texto: comparar "933,440" con un
    float no se puede, y es justo lo que hay que hacer antes de que la pieza
    salga."""
    _, payload = _mensaje_con(VIGENCIA_NIVEL)

    assert payload["_procedencia"]["crudos"]["vigencia_nivel"] == 933.44


def test_el_precio_que_pierde_el_chandelier_invalida_la_pieza():
    """La divergencia por S1/R1 no cubre este caso: el Chandelier no es ninguno
    de los dos, y es el stop del propio Playbook."""
    from pipeline_carrusel import divergencia_vigencia

    motivo = divergencia_vigencia(VIGENCIA_NIVEL, precio_nuevo=932.90)

    assert motivo is not None and "933,44" in motivo.replace(".", ",")


def test_un_precio_sobre_el_chandelier_no_es_divergencia():
    from pipeline_carrusel import divergencia_vigencia

    assert divergencia_vigencia(VIGENCIA_NIVEL, precio_nuevo=936.10) is None
    assert divergencia_vigencia(None, precio_nuevo=936.10) is None
    assert divergencia_vigencia(VIGENCIA_RANGO, precio_nuevo=936.10) is None, (
        "el rango ya lo cubre la divergencia por soporte y resistencia"
    )


def test_el_refresco_recalcula_el_nivel_con_las_anclas_de_ahora():
    """El Chandelier se mueve con cada vela cerrada. Publicar el nivel calculado
    veinte minutos antes es publicar un dato viejo con cara de fresco."""
    from pipeline_carrusel import refrescar_payload

    payload = _mensaje_con(VIGENCIA_NIVEL)[1]

    nuevo, motivo = refrescar_payload(
        payload,
        ahora=datetime(2026, 8, 25, 11, 30, tzinfo=pc.SANTIAGO),
        h1={"price": 68.900, "s1": 68.500, "r1": 69.300, "atr_14": 0.050,
            "chandelier_max": 69.000, "chandelier_min": 68.100,
            "ema_50": 68.600},
        digits=3,
        cierres=cierres_para(68.900),
    )

    assert motivo is None
    assert nuevo["_procedencia"]["crudos"]["vigencia_nivel"] == pytest.approx(
        69.000 - 3.0 * 0.050, abs=0.001
    )
    assert "68,850" in pc.construir_mensaje_alerta(nuevo)


def test_el_refresco_detiene_la_pieza_si_el_sesgo_quedo_invalidado():
    from pipeline_carrusel import refrescar_payload

    _, motivo = refrescar_payload(
        _mensaje_con(VIGENCIA_NIVEL)[1],
        ahora=datetime(2026, 8, 25, 11, 30, tzinfo=pc.SANTIAGO),
        h1={"price": 68.500, "s1": 68.400, "r1": 69.300, "atr_14": 0.050,
            "chandelier_max": 69.000, "chandelier_min": 68.100,
            "ema_50": 68.600},
        digits=3,
        cierres=cierres_para(68.500),
    )

    assert motivo is not None and "sesgo" in motivo.lower()


# ─────────────────────────────────────────────────────────────────────────────
# El chip refleja el Playbook, no solo la lectura tecnica
# ─────────────────────────────────────────────────────────────────────────────
def _payload_chip(vigencia, direccion="ALCISTA"):
    return pc.construir_payload(
        {**SELECCION, "direccion": direccion, "vigencia": vigencia},
        ACTIVO, AHORA, CIERRES,
    )


def test_sin_ficha_del_playbook_el_chip_sigue_siendo_la_lectura_tecnica():
    """Los 33 activos del catalogo sin ficha son la mayoria del universo: ahi la
    lectura tecnica es lo unico que hay, y el chip la refleja como siempre."""
    p = _payload_chip(None)
    assert p["sesgo"] == "Alcista"
    assert p["tag_riesgo"] == "ALCISTA"


def test_con_sesgo_sostenido_el_chip_lo_toma_del_playbook():
    p = _payload_chip(VIGENCIA_NIVEL)
    assert p["sesgo"] == "Alcista"

    corto = {**VIGENCIA_NIVEL, "direccion": "CORTO"}
    p = _payload_chip(corto, direccion="BAJISTA")
    assert p["sesgo"] == "Bajista"


def test_un_sesgo_invalidado_deja_el_chip_neutro_y_no_alcista():
    """El defecto que el director mando arreglar: la pieza mostraba `ALCISTA` en
    verde junto al aviso de que el sesgo alcista quedo invalidado. Un cliente lee
    esa contradiccion en 30 segundos.

    La plantilla ya tenia el estado neutro (`tag-sesgo--lateral`, flecha y color
    de texto), y el `body` sin clase de sesgo deja el cromo en el acento de
    marca: no habia que inventar nada visual.
    """
    p = _payload_chip({**VIGENCIA_NIVEL, "vigente": False})
    assert p["sesgo"] == "Lateral"
    assert p["tag_riesgo"] == "LATERAL"


def test_un_activo_en_rango_no_afirma_direccion_en_el_chip():
    """`NIVEL_OPUESTO_CANAL` es score cero: no hay direccion que mostrar."""
    p = _payload_chip(VIGENCIA_RANGO)
    assert p["sesgo"] == "Lateral"


def test_si_el_playbook_contradice_la_lectura_tecnica_el_chip_queda_neutro():
    """El caso donde el chip mas engana. La vigencia ya se omitia por
    contradiccion, pero el chip seguia afirmando la direccion tecnica como si
    nada: justo cuando las dos capas discrepan es cuando no hay que afirmar."""
    p = _payload_chip({**VIGENCIA_NIVEL, "direccion": "CORTO"}, direccion="ALCISTA")
    assert p["vigencia"] is None, "la vigencia se sigue omitiendo"
    assert p["sesgo"] == "Lateral", "el chip afirma una direccion que el Playbook niega"


def test_el_mensaje_lateral_no_habla_de_presion_vendedora():
    """Con el chip neutro, el bloque de apertura no puede caer al caso bajista:
    `alcista == False` no significa bajista, significa que no hay direccion."""
    p = _payload_chip(VIGENCIA_RANGO)
    p["titular"] = "La plata se mueve de lado"
    p["parrafo"] = "Sin definicion por ahora."
    mensaje = pc.construir_mensaje_alerta(p)

    assert "Presión vendedora bajo" not in mensaje.split("━")[0]
    assert "Fuerza compradora sobre" not in mensaje.split("━")[0]
    # Y nombra los DOS bordes, que es lo que hay que vigilar en un rango.
    assert "68,394" in mensaje and "68,974" in mensaje


def test_el_refresco_recalcula_el_chip_si_el_sesgo_cambio_de_estado():
    """Si entre preparar y despachar el precio recupera su nivel, el chip no
    puede seguir neutro mientras el bloque dice que el sesgo esta vigente."""
    from pipeline_carrusel import refrescar_payload

    payload = _payload_chip({**VIGENCIA_NIVEL, "vigente": False})
    payload["titular"] = "t"
    payload["parrafo"] = "p"
    assert payload["sesgo"] == "Lateral"

    nuevo, motivo = refrescar_payload(
        payload,
        ahora=datetime(2026, 8, 25, 11, 30, tzinfo=pc.SANTIAGO),
        h1={"price": 68.900, "s1": 68.500, "r1": 68.960, "atr_14": 0.050,
            "chandelier_max": 69.000, "chandelier_min": 68.100,
            "ema_50": 68.600},
        digits=3,
        cierres=cierres_para(68.900),
    )

    assert motivo is None
    assert nuevo["vigencia"]["vigente"] is True
    assert nuevo["sesgo"] == "Alcista", "el chip quedo neutro con el sesgo ya vigente"


def test_los_avisos_de_la_fuente_macro_no_se_descartan():
    """`preparar` recogia los avisos de `_contexto_macro` en un `_`.

    Esa funcion ya emitia "la UST 10Y no tiene variacion diaria calculable hoy" y
    "calendario no disponible: blackouts sin verificar", y nadie los leia. Un
    aviso que se calcula y se tira es peor que no calcularlo: da la impresion de
    que se verifico.
    """
    import inspect

    fuente = inspect.getsource(pc.preparar)
    assert "avisos_macro" in fuente, "los avisos de _contexto_macro volvieron al piso"
    assert ", _ = sc._contexto_macro" not in fuente


# ─────────────────────────────────────────────────────────────────────────────
# El barrido mide en la unidad del preparado, no en la de la tanda
# ─────────────────────────────────────────────────────────────────────────────
def _tanda_con_dos_canales(tmp_path):
    tanda = tmp_path / "2026-09-04_10-12_apertura_ny"
    for canal, pieza in (("02_forex_divisas", "1_usdclp"), ("04_indices_bursatiles", "1_us500spot")):
        d = tanda / canal
        d.mkdir(parents=True)
        (d / f"{pieza}.json").write_text("{}", encoding="utf-8")
        (d / f"{pieza}.png").write_bytes(b"png")
        (d / f"{pieza}_mensaje.txt").write_text("pie", encoding="utf-8")
        (d / "0_contexto_macro.txt").write_text("macro", encoding="utf-8")
    (tanda / "_screener.json").write_text("{}", encoding="utf-8")
    return tanda


def test_preparar_un_canal_no_barre_los_payloads_de_otro(tmp_path):
    """El defecto del 2026-09-04: dos `--preparar --grupo` en el mismo minuto.

    El directorio se nombra por MINUTO y el preparado opera por CANAL, asi que la
    segunda corrida reutilizaba la carpeta y `limpiar_payloads` hacia `rglob` sobre
    la tanda ENTERA. Me borro los doce payloads de commodities y el escaner reporto
    "barridos 12 payload(s)" sin que eso significara nada malo a la vista.
    """
    tanda = _tanda_con_dos_canales(tmp_path)
    barridos = pc.limpiar_payloads(tanda, solo_canales={"04_indices_bursatiles"})

    assert (tanda / "02_forex_divisas" / "1_usdclp.json").exists(), "se barrio otro canal"
    assert not (tanda / "04_indices_bursatiles" / "1_us500spot.json").exists()
    assert any("us500" in b for b in barridos)
    assert not any("usdclp" in b for b in barridos)


def test_sin_canales_declarados_el_barrido_sigue_siendo_de_toda_la_tanda(tmp_path):
    """`--matriz` prepara todos los canales, asi que ahi el barrido global es el
    correcto. El cambio acota la unidad, no la elimina."""
    tanda = _tanda_con_dos_canales(tmp_path)
    pc.limpiar_payloads(tanda)
    assert not (tanda / "02_forex_divisas" / "1_usdclp.json").exists()
    assert not (tanda / "04_indices_bursatiles" / "1_us500spot.json").exists()


def test_el_barrido_nunca_toca_el_screener(tmp_path):
    """Sobrevive por el prefijo `_`, y eso es deliberado."""
    tanda = _tanda_con_dos_canales(tmp_path)
    pc.limpiar_payloads(tanda)
    assert (tanda / "_screener.json").exists()


def test_preparar_acota_el_barrido_al_canal_pedido():
    """El contrato: `preparar` tiene que pasarle los canales que va a escribir.

    Si volviera a llamar `limpiar_payloads(destino)` sin acotar, el defecto
    reaparece y ningun test de arriba lo detecta, porque prueban la funcion y no
    su uso.
    """
    import inspect

    fuente = inspect.getsource(pc.preparar)
    assert "solo_canales=" in fuente, "preparar volvio a barrer la tanda completa"


# ─────────────────────────────────────────────────────────────────────────────
# El freno editorial vale para las DOS rutas de render
#
# `rendir` lo tenía y el despacho no, y el despacho es el que llega al cliente:
# `_refrescar_y_rendir` hacía `pop("_pendiente_editorial")`, descartando la
# marca que existe justamente para frenar. Es el patrón de dos caminos al mismo
# resultado con el freno en uno solo.
# ─────────────────────────────────────────────────────────────────────────────
def test_el_despacho_se_niega_a_rendir_una_pieza_sin_editorial(tmp_path):
    """El camino que llega al cliente necesita el mismo freno que `rendir`."""
    (tmp_path / "1_xagusd.json").write_text(
        json.dumps(payload_de_prueba(), ensure_ascii=False), encoding="utf-8"
    )
    with pytest.raises(SystemExit) as exc:
        pc._refrescar_y_rendir(tmp_path)
    mensaje = str(exc.value)
    assert "titular" in mensaje and "parrafo" in mensaje


def test_el_freno_editorial_del_despacho_actua_antes_de_leer_el_mercado(tmp_path, monkeypatch):
    """Si el guardia corriera después, gastaría una lectura del terminal para
    descubrir algo que el payload ya decía en disco."""
    def no_llamar(*_a, **_k):
        raise AssertionError("se leyó el mercado antes de validar lo editorial")

    monkeypatch.setattr("market_data_mcp.analisis.analizar_activo", no_llamar)
    (tmp_path / "1_xagusd.json").write_text(
        json.dumps(payload_de_prueba(), ensure_ascii=False), encoding="utf-8"
    )
    with pytest.raises(SystemExit):
        pc._refrescar_y_rendir(tmp_path)


def test_el_contexto_macro_no_necesita_editorial(tmp_path):
    """`0_contexto_macro` no tiene titular ni párrafo por diseño: su texto lo
    escribe `contexto_macro_grupos`. El guardia no puede confundirlo con una
    pieza a medias."""
    (tmp_path / "0_contexto_macro.json").write_text(
        json.dumps({"activo": "Mercado"}, ensure_ascii=False), encoding="utf-8"
    )
    assert pc._refrescar_y_rendir(tmp_path) == []


def test_las_dos_rutas_comparten_un_solo_guardia_editorial():
    """Dos implementaciones del mismo freno divergen: es el defecto recurrente
    del repo. Ambas rutas tienen que llamar a la misma función."""
    import inspect

    guardia = pc.exigir_texto_editorial
    for funcion in (pc.rendir, pc._refrescar_y_rendir):
        fuente = inspect.getsource(funcion)
        assert guardia.__name__ in fuente, (
            f"{funcion.__name__} no usa {guardia.__name__}: el freno se duplicó"
        )
