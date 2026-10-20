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
    "volatilidad_tipica": 0.441,
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


def payload_de_prueba(activo=None, lectura=None, **extra) -> dict:
    """Una pieza de alerta del oro, armada desde la lectura como en producción."""
    return pc.construir_payload_lectura(
        _sel(lectura or _lectura_alcista(), **extra), activo or ORO, AHORA, [4119.0, 4120.0],
    )


def _lectura_bajista():
    from dataclasses import replace

    return replace(_lectura_alcista(), direccion="BAJISTA")


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
    "volatilidad_tipica": 2.61,
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


def test_construir_payload_se_niega_ante_un_precio_que_no_es_el_de_su_serie():
    """No alcanza con detectarlo: el payload no puede llegar a existir."""
    with pytest.raises(pc.PayloadIncoherenteError) as exc:
        pc.construir_payload_lectura(_sel(_lectura_alcista()), ORO, AHORA, [4000.0, 4001.0])
    assert "XAUUSD" in str(exc.value)

def test_el_desfase_de_un_tick_pasa():
    """El unico payload sano de disco con desfase no nulo: USD/JPY, un tick.

    Si el control fuera estricto, la pieza legitima se caeria. Medido: 0,001 de
    desfase sobre un ATR de 0,304, o sea 0,0033 ATR, 75 veces por debajo del tope.
    """
    sel = {**SELECCION, "precio": 163.731, "soporte": 163.400,
           "resistencia": 164.100, "volatilidad_tipica": 0.304}
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
    son cuatro velas en el oro y un tick en el Nasdaq."""
    sel = {k: v for k, v in SELECCION.items() if k != "volatilidad_tipica"}
    motivo = pc.incoherencia_del_payload(sel, cierres_para(SELECCION["precio"]))
    assert motivo is not None and "vela tipica" in motivo


def test_una_serie_vacia_no_se_publica():
    assert pc.incoherencia_del_payload(SELECCION, []) is not None


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
        # Los payloads de antes del enchufe medían con 1,5 x ATR de H1 y ya no se producen.
        if not crudos or not serie or "lectura" not in datos:
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
            "volatilidad_tipica": valor,    # vol_pct = la vela típica del marco
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
    gld = {**ORO, "ticker": "GLD.US", "nombre": "SPDR Gold Shares"}
    assert payload_de_prueba(gld, ticker="GLD.US")["activo_slug"] == "oro"

def test_cada_slug_del_universo_renderizable_tiene_token_de_color():
    """Si un activo tiene imagen pero no token, su pieza sale con cromo de marca
    contra una foto de otro tono. Pasó con XAGUSD, #MELI y SOXX.US."""
    import screener_gi as sc

    marca = (RAIZ / "templates" / "stories" / "marca.css").read_text(encoding="utf-8")
    faltan = []
    for activo in sc.cargar_universo(solo_renderizables=True):
        slug = pc.slug_del_activo(activo["ticker"], activo["imagen"])
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
    assert payload["precio_actual"] == "4.120,00", "no se truncan ceros al final"
    assert payload["soporte"] == "4.080,00"
    assert payload["resistencia"] == "4.200,00"

    tres = payload_de_prueba({**ORO, "digits": 3})
    assert tres["precio_actual"] == "4.120,000"

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
    mueve en dólares, el USD/CLP en pesos y el USD/JPY en yenes. Se usa el código
    de moneda y no el símbolo: en Chile `$` es ambiguo entre peso y dólar.
    """
    assert payload_de_prueba()["vol_pct"] == "18,50 USD"
    assert payload_de_prueba({**ORO, "unidad": "CLP"})["vol_pct"] == "18,50 CLP"
    assert payload_de_prueba({**ORO, "unidad": "puntos"})["vol_pct"] == "18,50 puntos"

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
    rec = payload_de_prueba()["recorrido"]
    assert rec["lienzo"] == "alto"
    assert rec["marcadores"][0]["indice"] == len(rec["serie"]) - 1
    assert rec["marcadores"][0]["rol"] == "AHORA"
    assert {n["rol"] for n in rec["niveles"]} == {"OBJETIVO", "VIGILAR", "INVALIDA"}

def test_la_direccion_bajista_cambia_sesgo_y_tag_pero_no_el_color_del_activo():
    """Identidad del activo y dirección de mercado son roles de color distintos:
    si se colapsaran, una pieza dorada bajista se leería como alcista."""
    payload = payload_de_prueba(lectura=_lectura_bajista())
    assert (payload["sesgo"], payload["tag_riesgo"]) == ("Bajista", "BAJISTA")
    assert payload["activo_slug"] == "oro", "el slug no depende de la direccion"

def test_la_procedencia_del_puntaje_viaja_con_el_payload():
    """Deja auditable por qué este activo y no otro, al lado de la pieza que
    produjo. No se rinde: las claves con guion bajo se quitan antes del render."""
    payload = payload_de_prueba()
    assert payload["_procedencia"]["score"] == 60.0
    assert payload["_procedencia"]["ticker"] == "XAUUSD"

# ─────────────────────────────────────────────────────────────────────────────
# El freno editorial
# ─────────────────────────────────────────────────────────────────────────────
def test_rendir_se_niega_si_falta_el_texto_editorial(tmp_path):
    """Misma razón que el fail-fast de imagen: una pieza a medias que sale sin
    avisar llega al cliente."""
    (tmp_path / "1_xauusd.json").write_text(
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
    (tmp_path / "1_xauusd.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        pc.rendir(tmp_path)
    assert "titular" in str(exc.value)


def test_rendir_rechaza_guion_largo_en_titular_o_parrafo(tmp_path):
    payload = payload_de_prueba()
    payload["titular"] = "Oro sube \u2014 nuevo máximo"
    payload["parrafo"] = "El activo mantiene fuerza compradora sobre el soporte clave."
    (tmp_path / "1_xauusd.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        pc.rendir(tmp_path)
    assert "guion largo" in str(exc.value)


def test_rendir_rechaza_voseo_en_titular_o_parrafo(tmp_path):
    payload = payload_de_prueba()
    payload["titular"] = "Oro en soporte clave"
    payload["parrafo"] = "Mirá cómo reacciona en la zona de demanda para operar."
    (tmp_path / "1_xauusd.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        pc.rendir(tmp_path)
    assert "voseo" in str(exc.value)


def test_rendir_falla_claro_si_el_directorio_no_tiene_payloads(tmp_path):
    """Los archivos que empiezan con guion bajo son insumos, no piezas."""
    (tmp_path / "_screener.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        pc.rendir(tmp_path)
    assert "No hay payloads" in str(exc.value)


def test_el_universo_del_escaner_trae_lo_que_el_payload_consume():
    """Contrato entre `cargar_universo` y `construir_payload_lectura`, contra el catalogo REAL.

    `cargar_universo` no pasa el activo del catalogo tal cual: lo PROYECTA a un
    puñado de campos. Un campo nuevo en config/activos.json no llega solo al
    pipeline, hay que agregarlo tambien a esa proyeccion. Cuando se agrego
    `unidad` al catalogo, el fixture se actualizo y la proyeccion no, y el
    carrusel reventaba con KeyError en la primera tanda real con todos los tests
    en verde. Por eso este test usa el universo de verdad.
    """
    universo = sc.cargar_universo(solo_renderizables=True)
    con_nota = [a for a in universo if pc.marco_operativo() in a["notas_marco"]]
    assert {a["ticker"] for a in con_nota} >= set(sc.cobertura_fija()), (
        "un activo de cobertura fija sin la nota de su marco no puede publicarse"
    )
    for activo in con_nota:
        payload = payload_de_prueba(activo, ticker=activo["ticker"])
        assert payload["vol_pct"].endswith(activo["unidad"]), activo["ticker"]
        # La cobertura fija sale sin foto (2026-09-28): el cobre.
        assert payload["activo_imagen"] or activo["ticker"] in sc.cobertura_fija(), activo["ticker"]

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


def test_el_carrusel_tematico_no_escribe_en_avisos():
    """Decisión del director el 2026-09-29: Avisos es de `pipeline_avisos`.

    Hasta ese día la regla era "el canal de avisos, siempre" (2026-09-03), y la
    bitácora deduplica por tanda: una tanda de solo WTI reenvió a Avisos el
    contexto del VIX media hora después del bueno. Ni un canal pedido ni una
    pieza mal mapeada pueden meter Avisos en la corrida del carrusel.
    """
    assert pc.canales_con_contexto_macro([], grupo_pedido=None) == set()
    assert pc.CANAL_AVISOS not in pc.canales_con_contexto_macro(
        [{"grupo": pc.CANAL_AVISOS}], grupo_pedido=pc.CANAL_AVISOS)


def test_los_canales_con_piezas_reciben_su_contexto_macro():
    payloads = [{"grupo": "06_criptoactivos"}, {"grupo": "03_commodities_materias_primas"}]
    canales = pc.canales_con_contexto_macro(payloads, grupo_pedido=None)
    assert canales == {"03_commodities_materias_primas", "06_criptoactivos"}


# ─────────────────────────────────────────────────────────────────────────────
# La temporalidad, justificada por la volatilidad del activo
# ─────────────────────────────────────────────────────────────────────────────
def test_el_mensaje_justifica_la_temporalidad_con_la_nota_de_su_marco():
    """`CLAUDE.md` la declara OBLIGATORIA desde el issue #44 y nunca se implemento:
    el token `por_que_temporalidad` existia en un solo lugar del repo, que era la
    propia norma. El 2026-09-04 dos piezas salieron sin el bloque.
    """
    msg = pc.construir_mensaje_alerta(payload_de_prueba())
    assert "⏱️ *Temporalidad*" in msg
    assert "Por qué 4H acá" in msg
    # La justificacion es la del activo en ese marco, no una frase generica.
    assert ORO["notas_marco"]["H4"] in msg

def test_la_temporalidad_usa_la_etiqueta_que_declara_la_estrategia():
    """Prohibido decir "corto" sin numero: la etiqueta trae su duración."""
    msg = pc.construir_mensaje_alerta(payload_de_prueba())
    assert "4H · marco swing (de una a dos semanas)" in msg

def test_la_temporalidad_la_declara_la_estrategia_y_no_una_tabla_aparte():
    """Hasta S8 vivía una tabla de cuatro marcos en el código y otra en story.md,
    con un test que las comparaba. El marco de la pieza lo decide la estrategia y
    sus etiquetas viven en `Marcos.etiquetas`: una tercera copia volvería a divergir."""
    assert not hasattr(pc, "MARCOS_CANONICOS")
    tabla = (RAIZ / ".claude" / "commands" / "story.md").read_text(encoding="utf-8")
    assert not re.search(r"\|\s*`(15M|1H|4H|1D)`\s*\|", tabla), "volvió la tabla de cuatro marcos"

def test_sin_la_nota_de_su_marco_el_payload_no_se_construye():
    """Fail-closed, igual que con `unidad`: la linea es obligatoria, asi que un
    activo sin su nota no puede producir una pieza a medias en silencio."""
    with pytest.raises(KeyError):
        payload_de_prueba({**ORO, "notas_marco": {}})

def test_construir_mensaje_alerta_cumple_reglas_canonicas_whatsapp():
    payload = payload_de_prueba()
    payload["titular"] = "El oro sigue sobre su línea"
    payload["parrafo"] = "El oro mantiene la tendencia sobre su línea de seguridad."
    msg = pc.construir_mensaje_alerta(payload)

    # 1. Resumen al inicio
    assert "🎯 Activo:" in msg
    assert "📌 Nivel a vigilar:" in msg
    assert "⚡ Qué esperar:" in msg

    # 2. Separadores
    assert "━━━━━━━━━━━━━━━━━━━" in msg

    # 3. Flechas de escenarios
    for flecha in ("⬆️ ", "↔️ ", "⬇️ "):
        assert flecha in msg

    # 4. Niveles y cifras
    assert "4.120,00" in msg
    # La volatilidad tipica salio del texto con el formato compacto (2026-09-28);
    # sigue en la pieza visual.
    assert "18,50 USD" not in msg

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


def test_el_payload_preparado_guarda_los_precios_crudos():
    """Sin los números sin formatear, el corte por divergencia es imposible.

    El payload solo lleva precios ya en notación chilena ('936,32'), que sirven
    para dibujar pero no para comparar. Y son los de la lectura tal cual: el
    acotado a precio ± ATR del 2026-10-02 se retiró.
    """
    crudos = payload_de_prueba()["_procedencia"]["crudos"]
    assert crudos == {"precio": 4120.0, "soporte": 4080.0, "resistencia": 4200.0}
    assert not hasattr(pc, "acotar_niveles_intradia")

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


# ─────────────────────────────────────────────────────────────────────────────
# El chip sigue a la lectura tecnica (el Playbook V2 se retiro el 2026-09-27)
# ─────────────────────────────────────────────────────────────────────────────
def test_el_chip_es_la_lectura_tecnica():
    p = payload_de_prueba()
    assert (p["sesgo"], p["tag_riesgo"]) == ("Alcista", "ALCISTA")
    p = payload_de_prueba(lectura=_lectura_bajista())
    assert (p["sesgo"], p["tag_riesgo"]) == ("Bajista", "BAJISTA")

def test_el_payload_ya_no_lleva_vigencia_del_playbook():
    """Ni en la pieza ni en la procedencia: un campo que nadie calcula es una
    promesa que el mensaje podria volver a publicar."""
    p = payload_de_prueba()
    assert "vigencia" not in p
    assert "vigencia" not in p["_procedencia"]
    assert "vigencia_nivel" not in p["_procedencia"]["crudos"]

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


def test_preparar_persiste_la_seleccion_para_que_publicados_hoy_la_vea():
    """`preparar` llama a `sc.escanear` como funcion, no por su CLI.

    `_publicados_hoy` lee de `sc.DIR_SALIDA` (`data/screener/`), y solo
    `sc._guardar` escribe ahi. Sin la llamada, una segunda tanda del mismo dia
    no veia la primera y el escaner repetia el activo: medido el 2026-09-14,
    USD/JPY salio dos veces en menos de dos horas, en dos tandas manuales
    corridas la misma manana.
    """
    import inspect

    fuente = inspect.getsource(pc.preparar)
    assert "sc._guardar(resultado)" in fuente, (
        "preparar dejo de persistir el resultado del escaner: "
        "'ya salio hoy' vuelve a quedar ciego entre tandas"
    )


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
    (tmp_path / "1_xauusd.json").write_text(
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

    monkeypatch.setattr(pc, "refrescar_payload_lectura", no_llamar)
    monkeypatch.setattr(pc, "lectura_para_despacho", no_llamar)
    (tmp_path / "1_xauusd.json").write_text(
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


def test_despachar_modo_pruebas_redirige_a_banco_de_pruebas(tmp_path, monkeypatch):
    """En modo pruebas, todo el despacho debe dirigirse al banco de pruebas interno
    y no debe registrarse en la bitácora de despachos para no bloquear el canal real."""
    grupo_dir = tmp_path / "02_forex_divisas"
    grupo_dir.mkdir()
    (grupo_dir / "1_test.png").write_bytes(b"fake_png")
    (grupo_dir / "1_test_mensaje.txt").write_text("Mensaje test", encoding="utf-8")

    llamadas_lote = []

    class MockConfig:
        destino_de_pruebas = "GI · Banco de Pruebas"

    class MockSender:
        def __init__(self, headless=True):
            self.config = MockConfig()

        def enviar_lote(self, destinatario, piezas, dry_run=False, al_entregar=None):
            llamadas_lote.append((destinatario, len(piezas)))
            if al_entregar:
                for pz in piezas:
                    al_entregar(pz)
            return {"destinatario": destinatario, "piezas": len(piezas), "status": "enviado"}

    monkeypatch.setattr("whatsapp_sender.WhatsAppSender", MockSender)
    monkeypatch.setattr(pc, "_refrescar_y_rendir", lambda _d: [])

    bitacora_anotaciones = []
    monkeypatch.setattr("bitacora_despachos.registrar", lambda *a, **k: bitacora_anotaciones.append((a, k)))

    pc.despachar(tmp_path, dry_run=False, pruebas=True)
    assert len(llamadas_lote) == 1
    assert llamadas_lote[0][0] == "GI · Banco de Pruebas"
    assert len(bitacora_anotaciones) == 0


# ─────────────────────────────────────────────────────────────────────────────
# Formato compacto (decisión del director, 2026-09-28): resumido y para actuar
# ─────────────────────────────────────────────────────────────────────────────
def _msg_compacto():
    payload = payload_de_prueba()
    payload["titular"] = "El oro sigue sobre su línea de seguridad"
    payload["parrafo"] = "PARRAFO_LARGO_QUE_YA_NO_VA_EN_EL_MENSAJE"
    return pc.construir_mensaje_alerta(payload), payload


def test_el_mensaje_compacto_trae_solo_lo_que_sirve_para_actuar():
    msg, p = _msg_compacto()
    assert p["titular"] in msg
    assert f"Precio actual: {p['precio_actual']}" in msg
    assert msg.splitlines()[-1] in pc.CIERRES_ALERTA
    for linea in ("⬆️ ", "↔️ ", "⬇️ ", "⏱️ *Temporalidad*"):
        assert linea in msg


@pytest.mark.parametrize("sobra", [
    "PARRAFO_LARGO_QUE_YA_NO_VA_EN_EL_MENSAJE",
    "Diccionario rápido",
    "Manual de Operaciones",
    "Fijación de objetivos",
    "Volatilidad típica",
    "Coméntanos",
])
def test_el_mensaje_compacto_no_arrastra_los_bloques_largos(sobra):
    msg, _ = _msg_compacto()
    assert sobra not in msg


def test_el_mensaje_compacto_cabe_en_un_vistazo():
    """Tope editorial: bajo 900 caracteres aun con la nota de temporalidad."""
    msg, _ = _msg_compacto()
    assert len(msg) < 900, len(msg)


def test_un_activo_sin_foto_arma_su_payload_con_el_ticker_como_slug():
    """Cobertura fija (2026-09-28): el cobre no tiene foto y sale igual, con el
    grafico del motor. Su slug no puede quedar vacio."""
    p = payload_de_prueba({k: v for k, v in ORO.items() if k != "imagen"})
    assert p["activo_slug"] == "xauusd"
    assert p["activo_imagen"] == ""

def test_preparar_no_descarta_a_un_fijo_por_no_tener_foto():
    import inspect
    fuente = inspect.getsource(pc.preparar)
    assert "cobertura_fija" in fuente


# ─────────────────────────────────────────────────────────────────────────────
# Mensaje humanizado (decisión del director, 2026-09-28)
# ─────────────────────────────────────────────────────────────────────────────
def test_el_cierre_no_es_siempre_el_mismo_ni_siempre_el_analista():
    import screener_gi as sc
    cierres = set()
    for activo in sc.cargar_universo(solo_renderizables=False)[:20]:
        p = payload_de_prueba()
        p.update(titular="x", activo=activo["nombre"], rotulo_activo=f"X · {activo['ticker']}")
        cierres.add(pc.construir_mensaje_alerta(p).splitlines()[-1])
    assert len(cierres) >= 3, cierres
    assert sum("analista" in c for c in cierres) < len(cierres)


def test_el_cierre_es_estable_para_la_misma_pieza():
    """Variar no es azar: rendir dos veces la misma pieza da el mismo texto, o el
    guardia de huella del despacho veria un mensaje distinto al aprobado."""
    msg1, _ = _msg_compacto()
    msg2, _ = _msg_compacto()
    assert msg1 == msg2


def test_el_cobre_se_escribe_entero_y_sin_separador_de_miles():
    """digits = 0 se escribe entero (CLAUDE.md, formato de precios): "14.417" se
    confunde con un decimal y ademas no coincide con la etiqueta del grafico."""
    assert pc.formatear_precio(14417.0, 0) == "14417"


def test_con_decimales_se_mantiene_la_notacion_chilena():
    assert pc.formatear_precio(4134.736, 2) == "4.134,74"
    assert pc.formatear_precio(90.1814, 3) == "90,181"


def test_un_solo_formateador_de_precios_en_el_carrusel():
    """Tres copias de la misma formula divergen; es el defecto recurrente del repo."""
    fuente = Path(pc.__file__).read_text(encoding="utf-8")
    assert fuente.count('.replace("@", ".")') == 1


# ---------------------------------------------------------------- niveles del gráfico
def test_el_nivel_publicado_se_lee_en_notacion_chilena():
    assert pc._nivel_publicado("4.143,09", 4165.48) == 4143.09
    assert pc._nivel_publicado("970,25", 968.0) == 970.25
    assert pc._nivel_publicado("14341", None) == 14341.0


def test_sin_nivel_publicado_cae_al_respaldo():
    assert pc._nivel_publicado("", 968.0) == 968.0
    assert pc._nivel_publicado(None, None) is None


def test_las_dos_rutas_de_render_dibujan_el_nivel_publicado():
    """El gráfico dibuja lo que lee el cliente, no los crudos del motor.

    El 2026-10-02 `rendir` pasaba `crudos` al gráfico (968,00/988,94) mientras
    el texto publicaba los niveles acotados (970,25/991,35).
    """
    import inspect
    for fn in (pc.rendir, pc._refrescar_y_rendir):
        fuente = inspect.getsource(fn)
        assert "_nivel_publicado(" in fuente, fn.__name__


# ─────────────────────────────────────────────────────────────────────────────
# Fase 2 del enchufe: la pieza sale de la Lectura (spec §7 fase 2)
# ─────────────────────────────────────────────────────────────────────────────
from estrategia.contrato import (  # noqa: E402
    Escenario, Lectura, Linea, Referencia, lectura_a_dict,
)

LUNES = datetime(2026, 10, 12, 11, 0, tzinfo=pc.SANTIAGO)


def _lectura_alcista(objetivo=True):
    seg = Linea("seguridad", "diagonal", ((100, 4000.0), (200, 4050.0)), "H4", 3, "A+", 4080.0)
    obj = Referencia(4200.0, "resistencia de D1") if objetivo else None
    esc = (
        Escenario("⬆️", "Sobre 4.080,00",
                  "Mientras el precio cierre sobre 4.080,00, la tendencia alcista sigue."),
        Escenario("↔️", "Vuelta a 4.080,00",
                  "Si el precio vuelve a 4.080,00 y la respeta, la línea suma un toque."),
        Escenario("⬇️", "Cierre bajo 4.080,00",
                  "Si una vela de 4 horas cierra bajo 4.080,00, la línea alcista se rompe."),
    )
    ref = Referencia(4080.0, "línea alcista de seguridad", seg)
    return Lectura(
        ticker="XAUUSD", marco="H4", precio=4120.0, direccion="ALCISTA", estado="TENDENCIA",
        lineas=(seg,), en_prueba=None, vigilar=ref, invalidacion=ref, objetivo=obj, escenarios=esc,
        salida=("En compras, sal si una vela de 4 horas cierra bajo la línea de seguridad (la que "
                "protege tu operación), hoy en 4.080,00. Mientras no pase, mantén la posición y "
                "deja correr la ganancia."),
        conceptos=(), avisos=(), metricas={}, vela=200,
    )


def _sel(lectura, **extra):
    return {"ticker": lectura.ticker, "nombre": "Oro", "clase": "forex_commodities",
            "cobertura_fija": True, "gates_omitidos": [], "score": 60.0,
            "puntaje": {"desglose": {"base": 50.0}, "excluido": None},
            "direccion": lectura.direccion, "estado": lectura.estado, "precio": lectura.precio,
            "marco": "H4", "volatilidad_tipica": 18.5, "lectura": lectura_a_dict(lectura), **extra}


ORO = {"ticker": "XAUUSD", "nombre": "Oro", "digits": 2, "unidad": "USD", "categoria": "commodity",
       "clase": "forex_commodities", "imagen": "assets/activos/oro.jpg",
       "notas_marco": {"H4": "el oro hace tramos de varios días: en 4H se ven las líneas que esos tramos respetan."},
       "nota_volatilidad": "nota vieja de 1H"}


def _payload_lectura(lectura=None, **extra):
    return pc.construir_payload_lectura(_sel(lectura or _lectura_alcista(), **extra), ORO, LUNES,
                                        [4119.0, 4120.0])


def test_los_niveles_publicados_son_los_mas_cercanos_a_cada_lado():
    assert pc.niveles_publicados(_lectura_alcista()) == (4080.0, 4200.0)


def test_sin_nivel_sobre_el_precio_la_resistencia_sale_vacia():
    lec = _lectura_alcista(objetivo=False)
    assert pc.niveles_publicados(lec) == (4080.0, None)
    payload = _payload_lectura(lec)
    assert payload["resistencia"] == "--" and payload["soporte"] == "4.080,00"


def test_el_payload_lleva_la_lectura_el_marco_y_la_nota_del_marco():
    p = _payload_lectura()
    assert p["lectura"]["ticker"] == "XAUUSD" and p["marco"] == "H4" and p["digits"] == 2
    assert p["sesgo"] == "Alcista" and p["vol_pct"] == "18,50 USD"
    assert p["nota_volatilidad"] == ORO["notas_marco"]["H4"]
    assert p["_procedencia"]["puntaje"]["desglose"] == {"base": 50.0}
    assert "factores" not in p["_procedencia"]


def test_el_mensaje_sale_de_la_lectura():
    p = _payload_lectura()
    p["titular"] = "El oro sigue sobre su línea"
    msg = pc.construir_mensaje_alerta(p)
    assert "📌 Nivel a vigilar: 4.080,00 (línea alcista de seguridad)" in msg
    assert "⬆️ Mientras el precio cierre sobre 4.080,00, la tendencia alcista sigue." in msg
    assert "⏱️ *Temporalidad*: 4H · marco swing (de una a dos semanas)" in msg
    assert "💡 Por qué 4H acá:" in msg
    assert "En compras, sal si una vela de 4 horas cierra bajo la línea de seguridad" in msg
    assert "al otro lado" not in msg and "No hay objetivo fijo" not in msg
    assert "falso quiebre" not in msg
    assert "—" not in msg and "–" not in msg


def test_el_mensaje_dice_el_motivo_de_un_fijo_excluido():
    p = _payload_lectura(gates_omitidos=[
        "va contra la secuencia de los marcos mayores: es donde nacen las falsas rupturas"])
    assert "⚠️ Ojo, va contra la secuencia de los marcos mayores" in pc.construir_mensaje_alerta(p)


def test_la_temporalidad_sale_de_la_estrategia_activa():
    assert pc.marco_operativo() == "H4"
    assert pc.temporalidad_de("H4") == "4H · marco swing (de una a dos semanas)"


def test_un_payload_incoherente_con_su_serie_no_se_arma():
    with pytest.raises(pc.PayloadIncoherenteError):
        pc.construir_payload_lectura(_sel(_lectura_alcista()), ORO, LUNES, [4000.0, 4010.0])


def test_sin_nota_del_marco_el_payload_lectura_no_se_construye():
    sin_nota = {k: v for k, v in ORO.items() if k != "notas_marco"}
    with pytest.raises(KeyError):
        pc.construir_payload_lectura(_sel(_lectura_alcista()), sin_nota, LUNES, [4119.0, 4120.0])


def _preparar_simulado(tmp_path, monkeypatch, seleccion):
    """`preparar` de punta a punta con el escáner, la serie y lo macro simulados."""
    import contexto_macro_grupos as cmg
    import noticia_oficial
    import suplemento_canal

    resultado = {"tanda": 1, "sesion_slug": "apertura_ny", "nombre_tanda": "Apertura",
                 "nombre_sesion": "Apertura", "foco": "", "hora_chile_tanda": "11:00",
                 "generado": "2026-10-12 11:00", "seleccion": seleccion, "excluidos": [],
                 "avisos": []}
    monkeypatch.setattr(pc, "DIR_TRABAJO", tmp_path)
    monkeypatch.setattr(sc, "escanear", lambda **kw: resultado)
    monkeypatch.setattr(sc, "_guardar", lambda r: tmp_path / "screener.json")
    monkeypatch.setattr(sc, "_contexto_macro", lambda ahora: ([], None, []))
    monkeypatch.setattr(pc, "_serie_para", lambda ticker, marco="H1": [4119.0, 4120.0])
    monkeypatch.setattr(cmg, "asegurar_contexto_macro_grupo", lambda **kw: None)
    monkeypatch.setattr(pc, "escribir_suplementos", lambda *a, **k: ([], []))
    monkeypatch.setattr(noticia_oficial, "descargar_con_cache", lambda *a, **k: None)
    monkeypatch.setattr(suplemento_canal, "cargar_historial", lambda *a, **k: [])
    return pc.preparar(modo_matriz=True)


def test_preparar_arma_la_pieza_desde_la_lectura(tmp_path, monkeypatch):
    res = _preparar_simulado(tmp_path, monkeypatch, [_sel(_lectura_alcista())])
    assert res["problemas"] == []
    payload = json.loads(Path(res["payloads"][0]["archivo"]).read_text(encoding="utf-8"))
    assert payload["lectura"]["ticker"] == "XAUUSD" and payload["marco"] == "H4"
    mensaje = Path(res["payloads"][0]["archivo"]).with_name("1_xauusd_mensaje.txt").read_text(encoding="utf-8")
    assert "4H · marco swing" in mensaje


def test_preparar_avisa_si_falta_la_nota_del_marco(tmp_path, monkeypatch):
    sel = _sel(_lectura_alcista(), ticker="XAUUSD", marco="D1")
    res = _preparar_simulado(tmp_path, monkeypatch, [sel])
    assert res["payloads"] == []
    assert any("notas_marco.D1" in p for p in res["problemas"])


# ─────────────────────────────────────────────────────────────────────────────
# Fase 2 del enchufe: el despacho vuelve a pedir la Lectura (decisión del 2026-10-11)
# ─────────────────────────────────────────────────────────────────────────────
MEDIA_HORA = datetime(2026, 10, 12, 11, 30, tzinfo=pc.SANTIAGO)


def _payload_listo():
    p = _payload_lectura()
    p["titular"], p["parrafo"] = "t", "p"
    p.pop("_pendiente_editorial")
    return p


def test_el_refresco_mueve_el_precio_y_los_niveles_sin_tocar_lo_editorial():
    from dataclasses import replace

    actual = replace(_lectura_alcista(), precio=4130.0)
    nuevo, motivo = pc.refrescar_payload_lectura(_payload_listo(), MEDIA_HORA, actual, 2,
                                                 [4129.0, 4130.0], 19.0, lambda a, b: None)
    assert motivo is None
    assert nuevo["precio_actual"] == "4.130,00" and nuevo["vol_pct"] == "19,00 USD"
    assert nuevo["lectura"]["precio"] == 4130.0
    assert nuevo["titular"] == "t" and nuevo["parrafo"] == "p"
    assert nuevo["fecha_hora"].endswith("11:30")


def test_el_refresco_respeta_los_niveles_fijados_por_el_director():
    p = _payload_listo()
    p["_procedencia"]["niveles_fijados"] = {"soporte": 4090.0}
    nuevo, _ = pc.refrescar_payload_lectura(p, MEDIA_HORA, _lectura_alcista(), 2,
                                            [4119.0, 4120.0], 18.5, lambda a, b: None)
    assert nuevo["soporte"] == "4.090,00" and nuevo["resistencia"] == "4.200,00"


def test_el_refresco_pone_la_invalidacion_fijada_en_escenario_y_salida():
    p = _payload_listo()
    p["_procedencia"]["niveles_fijados"] = {"invalidacion": 4080.0}
    nuevo, _ = pc.refrescar_payload_lectura(p, MEDIA_HORA, _lectura_alcista(), 2,
                                            [4119.0, 4120.0], 18.5, lambda a, b: None)
    bajista = next(e for e in nuevo["lectura"]["escenarios"] if e["flecha"] == "⬇️")
    assert "4.080,00" in bajista["condicion"] and "4.080,00" in bajista["texto"]
    assert "4.080,00" in nuevo["lectura"]["salida"]


def test_la_divergencia_de_la_estrategia_frena_la_pieza():
    vista = []

    def divergencia(preparada, actual):
        vista.append((preparada.precio, actual.precio))
        return "la dirección cambió de alcista a bajista"

    _, motivo = pc.refrescar_payload_lectura(_payload_listo(), MEDIA_HORA, _lectura_alcista(), 2,
                                             [4119.0, 4120.0], 18.5, divergencia)
    assert motivo == "la dirección cambió de alcista a bajista"
    assert vista == [(4120.0, 4120.0)]  # compara la preparada contra la de ahora


def test_un_refresco_desacoplado_de_su_serie_no_sale():
    _, motivo = pc.refrescar_payload_lectura(_payload_listo(), MEDIA_HORA, _lectura_alcista(), 2,
                                             [4000.0, 4010.0], 18.5, lambda a, b: None)
    assert motivo is not None and "ultimo cierre" in motivo


def test_un_payload_sin_lectura_no_se_despacha(tmp_path, monkeypatch):
    viejo = {"plantilla": "alerta", "titular": "El oro sigue firme",
             "parrafo": "El oro se mantiene sobre su soporte de la semana.", "activo": "Oro",
             "_procedencia": {"ticker": "XAUUSD"}}
    (tmp_path / "1_xauusd.json").write_text(json.dumps(viejo), encoding="utf-8")
    monkeypatch.setattr(pc, "falta_metatrader5", lambda: False)
    avisos = pc._refrescar_y_rendir(tmp_path)
    assert (tmp_path / "1_xauusd.json.divergente").exists()
    assert any("antes del enchufe" in a for a in avisos)


def test_sin_referencia_el_despacho_lee_de_nuevo(tmp_path):
    from estrategia.contrato import Etiqueta, Marcos

    lec = _lectura_alcista()

    class Est:
        marcos = Marcos(("D1",), "H4", {"D1": 5, "H4": 5},
                        {"D1": Etiqueta("p", "d"), "H4": Etiqueta("s", "u")})

        def leer(self, ticker, velas, digits, en_curso=None):
            return lec

    def lector(ticker, marcos, extra):
        return {"H4": "v"}, None

    lectura, velas = pc.lectura_para_despacho(Est(), "XAUUSD", 2, lector, LUNES, base=tmp_path)
    assert lectura == lec and velas == {"H4": "v"}


def test_con_referencia_el_despacho_sigue_la_de_la_semana_y_no_guarda(tmp_path):
    import referencia_semanal as rs
    from estrategia.contrato import Etiqueta, Marcos

    ref = _lectura_alcista()
    rs.guardar(ref, "2026-W42", "semanal", LUNES, base=tmp_path)

    class Est:
        marcos = Marcos(("D1",), "H4", {"D1": 5, "H4": 5},
                        {"D1": Etiqueta("p", "d"), "H4": Etiqueta("s", "u")})

        def seguir(self, referencia, velas, digits, en_curso=None):
            from dataclasses import replace
            return replace(referencia, estado="RUPTURA",
                           lineas=tuple(replace(x, rol="accion") for x in referencia.lineas))

        def leer(self, ticker, velas, digits, en_curso=None):
            return ref

    lectura, _ = pc.lectura_para_despacho(Est(), "XAUUSD", 2, lambda t, m, e: ({"H4": "v"}, None),
                                          LUNES, base=tmp_path)
    assert lectura.estado == "RUPTURA"
    guardada = json.loads(rs.ruta("2026-W42", "XAUUSD", tmp_path).read_text(encoding="utf-8"))
    assert guardada["motivo"] == "semanal"  # el reemplazo lo guarda el escáner, no el despacho


def test_que_esperar_es_corto_y_no_repite_el_escenario():
    """Lo que se ve sobre el pliegue: estado, dirección y la condición, sin repetir el escenario."""
    op = pc.lectura_operativa(_payload_lectura())
    assert op["que_esperar"] == "Tendencia alcista: sobre 4.080,00"
    assert op["que_esperar"] not in " ".join(op["escenarios"])


def test_que_esperar_en_rango_y_en_prueba():
    from dataclasses import replace

    rango = replace(_lectura_alcista(), estado="RANGO", direccion="LATERAL", escenarios=(
        Escenario("⬆️", "Cierre sobre 4.200,00", "a"), Escenario("↔️", "Entre 4.080,00 y 4.200,00", "b"),
        Escenario("⬇️", "Cierre bajo 4.080,00", "c")))
    p = _payload_lectura()
    p["lectura"] = lectura_a_dict(rango)
    assert pc.lectura_operativa(p)["que_esperar"] == "Rango: entre 4.080,00 y 4.200,00"


def test_el_despacho_sigue_la_referencia_con_que_se_preparo_la_pieza(tmp_path):
    """Un día de ruptura el escáner guarda una referencia nueva; la pieza de la mañana se
    escribió contra la vieja y el despacho tiene que releerla igual, o se contradice."""
    import referencia_semanal as rs
    from estrategia.contrato import Etiqueta, Marcos

    vieja = _lectura_alcista()
    nueva = replace_lectura(vieja, estado="RANGO", direccion="LATERAL")
    rs.guardar(nueva, "2026-W42", "ruptura", LUNES, base=tmp_path)
    vistas = []

    class Est:
        marcos = Marcos(("D1",), "H4", {"D1": 5, "H4": 5},
                        {"D1": Etiqueta("p", "d"), "H4": Etiqueta("s", "u")})

        def seguir(self, referencia, velas, digits, en_curso=None):
            vistas.append(referencia.estado)
            return referencia

    lectura, _ = pc.lectura_para_despacho(Est(), "XAUUSD", 2, lambda t, m, e: ({"H4": "v"}, None),
                                          LUNES, base=tmp_path, referencia=vieja)
    assert vistas == ["TENDENCIA"] and lectura == vieja


def test_la_pieza_guarda_la_referencia_de_su_lectura():
    p = _payload_lectura(referencia=lectura_a_dict(_lectura_alcista()))
    assert p["_procedencia"]["referencia"]["ticker"] == "XAUUSD"


def replace_lectura(lectura, **cambios):
    from dataclasses import replace

    return replace(lectura, **cambios)


def test_las_lineas_del_grafico_salen_de_la_lectura_del_payload():
    lineas = pc.lineas_de(_payload_lectura())
    assert [x.rol for x in lineas] == ["seguridad"]
    assert pc.lineas_de({"activo": "Oro"}) is None  # un payload sin lectura (Avisos) no trae


def test_las_dos_rutas_de_render_pasan_las_lineas_al_grafico():
    """S5: el gráfico dibuja `Lectura.lineas` tanto al rendir como al refrescar antes de enviar."""
    import inspect
    for fn in (pc.rendir, pc._refrescar_y_rendir):
        assert "lineas=lineas_de(" in inspect.getsource(fn), fn.__name__
