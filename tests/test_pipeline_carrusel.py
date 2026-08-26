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
}

CIERRES = [68.0 + i * 0.01 for i in range(60)]


def payload_de_prueba(seleccion=None, activo=None) -> dict:
    return pc.construir_payload(seleccion or SELECCION, activo or ACTIVO, AHORA, CIERRES)


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

