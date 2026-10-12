"""El suplemento de un canal que quedo sin activos publicables.

**El motivo por el que un canal queda vacio ya es contenido.** Un canal que se
queda sin piezas porque todos sus activos estan en la ventana de un dato fuerte
explica algo que el cliente necesita entender: que no operar tambien es una
decision. Desde S8 del enchufe solo lo disparan el blackout y el feriado; nacio
con el gate de ATR agotado, que se borro.

El manual del comando prohibe el relleno ("una tanda de 2 piezas bien elegidas
es mejor que una de 3 con un relleno"), asi que el suplemento tiene que ganarse
el lugar. Por eso sale de las exclusiones que el escaner ya escribio, y no de un
generador de contenido.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for _p in (RAIZ / "scripts", RAIZ / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import pytest
import suplemento_canal as sup  # noqa: E402


@pytest.fixture(autouse=True)
def _aislar_historial(monkeypatch):
    """Evita que el historial en disco contamine los tests unitarios."""
    orig = sup.cargar_historial
    monkeypatch.setattr(
        sup,
        "cargar_historial",
        lambda ruta=None: orig(ruta) if ruta is not None else [],
    )

BLACKOUT = "blackout por IPC de EE.UU. (08:15-09:00 hora Chile)"

FOREX_EN_DATO_CON_CLASE = [
    {"ticker": "USDCLP", "nombre": "Dólar / Peso Chileno", "clase": "forex", "excluido": BLACKOUT},
    {"ticker": "EURUSD", "nombre": "Euro / Dólar", "clase": "forex", "excluido": BLACKOUT},
]

FOREX_EN_DATO = [
    {"ticker": "USDCLP", "nombre": "Dólar / Peso Chileno", "excluido": BLACKOUT},
    {"ticker": "USDJPY", "nombre": "Dólar / Yen Japonés", "excluido": BLACKOUT},
    {"ticker": "EURUSD", "nombre": "Euro / Dólar", "excluido": BLACKOUT},
    {"ticker": "GBPUSD", "nombre": "Libra / Dólar", "excluido": BLACKOUT},
]


# ─────────────────────────────────────────────────────────────────────────────
# El motivo se traduce a una categoria y a un concepto
# ─────────────────────────────────────────────────────────────────────────────
def test_un_activo_ya_publicado_no_es_contenido_para_el_cliente():
    """Hasta S8 "ya salio en una corrida anterior" caia en la categoria del ATR
    agotado, y el suplemento le habria dicho al cliente que el canal gasto su rango
    del dia cuando lo que paso es que su pieza ya habia salido."""
    cat = sup.categoria_del_motivo("ya salio en una corrida anterior de hoy")
    assert cat == {"categoria": "ya_publicado", "concepto": None, "publicable": False}


def test_los_motivos_de_los_gates_borrados_ya_no_tienen_categoria():
    for motivo in ("ATR diario consumido al 93%", "la vela tipica cubre la banda",
                   "niveles de respaldo por ATR"):
        assert sup.categoria_del_motivo(motivo) is None, motivo


def test_cada_gate_tiene_su_concepto():
    for motivo, concepto in (
        ("blackout por IPC de EE.UU. (08:15-09:00 hora Chile)", "precio-descontado"),
        ("feriado de NYSE", "temporalidades"),
    ):
        cat = sup.categoria_del_motivo(motivo)
        assert cat is not None, f"sin categoria: {motivo}"
        assert cat["concepto"] == concepto, motivo


def test_un_problema_nuestro_de_datos_no_es_contenido_para_el_cliente():
    """Un fallo del analizador es un problema de nuestra tuberia, no lecturas de mercado. No dan suplemento: publicar "no
    pudimos leer el activo" no le sirve a nadie y suena a excusa."""
    for motivo in (
        "MT5_UNAVAILABLE: el terminal no responde",
        "D1 SYMBOL_NOT_FOUND: no existe",
    ):
        cat = sup.categoria_del_motivo(motivo)
        assert cat is None or cat["publicable"] is False, f"{motivo} se daria por contenido"


def test_un_motivo_desconocido_no_se_inventa_una_categoria():
    """Fail-closed. Un gate nuevo sin categoria deja al canal sin suplemento, que
    es preferible a un concepto que no explica nada."""
    assert sup.categoria_del_motivo("un motivo que nadie clasifico") is None


# ─────────────────────────────────────────────────────────────────────────────
# El resumen del canal, con las cifras medidas
# ─────────────────────────────────────────────────────────────────────────────
def test_el_resumen_toma_la_categoria_dominante():
    feriado = {"ticker": "#NVDA", "nombre": "NVIDIA", "excluido": "feriado de NYSE"}
    r = sup.resumen_del_canal([*FOREX_EN_DATO, feriado])

    assert r is not None
    assert r["categoria"] == "dato_en_curso"
    assert r["activos"] == 4
    assert r["concepto"] == "precio-descontado"


def test_sin_exclusiones_no_hay_resumen():
    assert sup.resumen_del_canal([]) is None


def test_una_categoria_no_publicable_no_da_resumen():
    solo_nuestros = [
        {"ticker": "X", "nombre": "X", "excluido": "MT5_UNAVAILABLE: sin terminal"},
        {"ticker": "Y", "nombre": "Y", "excluido": "D1 SYMBOL_NOT_FOUND: no existe"},
    ]
    assert sup.resumen_del_canal(solo_nuestros) is None


# ─────────────────────────────────────────────────────────────────────────────
# El mensaje
# ─────────────────────────────────────────────────────────────────────────────
def test_el_mensaje_dice_el_motivo_y_ensena_el_concepto():
    s = sup.suplemento("02_forex_divisas", FOREX_EN_DATO)
    assert s is not None

    mensaje = sup.construir_mensaje_suplemento(s)

    assert "catalizadores macroeconómicos" in mensaje, f"no dice el motivo: {mensaje}"
    assert "📚" in mensaje, "no ensena el concepto"
    assert "analista" in mensaje.lower(), "sin cierre con CTA"


def test_el_mensaje_no_promete_niveles_que_no_tiene():
    """El cierre canonico de tres escenarios necesita soporte y resistencia, y
    este mensaje no los tiene. Prometerlos seria inventarlos."""
    s = sup.suplemento("02_forex_divisas", FOREX_EN_DATO)
    mensaje = sup.construir_mensaje_suplemento(s)

    assert "Nivel a vigilar" not in mensaje
    assert "fuerza compradora" not in mensaje.lower()
    assert "presión vendedora" not in mensaje.lower()


def test_el_mensaje_no_usa_jerga_sin_traducir():
    """El motivo del escaner es log interno: no se copia al mensaje."""
    s = sup.suplemento("02_forex_divisas", FOREX_EN_DATO)
    mensaje = sup.construir_mensaje_suplemento(s)

    assert "blackout" not in mensaje.lower(), "se filtro el texto del log"
    assert "—" not in mensaje and "–" not in mensaje, "guion largo prohibido"


def test_sin_suplemento_publicable_devuelve_none():
    assert sup.suplemento("02_forex_divisas", []) is None


# ─────────────────────────────────────────────────────────────────────────────
# Contratos de nombres
# ─────────────────────────────────────────────────────────────────────────────
def _motivos_de_los_gates() -> list[tuple[str, str]]:
    """Todo texto que un `gate_*` del escaner puede devolver, con su funcion.

    Se recorre el AST y no un regex. La version anterior buscaba
    `return f?"(feriado|ATR diario|blackout|...)..."`,
    o sea que estaba **anclada a los seis prefijos que ya existian**: un gate
    nuevo con otro prefijo no lo capturaba y entraba sin categoria en silencio,
    que es justo lo que este contrato existe para impedir. El `assert len >= 4`
    solo protegia de que el regex dejara de encontrar los viejos.

    De un f-string se toma el tramo literal inicial, que es el prefijo por el que
    `categoria_del_motivo` mapea.
    """
    import ast

    arbol = ast.parse((RAIZ / "scripts" / "screener_gi.py").read_text(encoding="utf-8"))
    motivos: list[tuple[str, str]] = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, ast.FunctionDef) or not nodo.name.startswith("gate_"):
            continue
        for hijo in ast.walk(nodo):
            if not isinstance(hijo, ast.Return) or hijo.value is None:
                continue
            for texto in _literales_de(hijo.value):
                if texto.strip():
                    motivos.append((nodo.name, texto))
    return motivos


def _literales_de(valor) -> list[str]:
    """El texto literal de un `return`, sea str, f-string o concatenacion."""
    import ast

    if isinstance(valor, ast.Constant) and isinstance(valor.value, str):
        return [valor.value]
    if isinstance(valor, ast.JoinedStr):
        # Solo el arranque literal: lo interpolado no forma parte del prefijo.
        trozos = []
        for parte in valor.values:
            if isinstance(parte, ast.Constant) and isinstance(parte.value, str):
                trozos.append(parte.value)
            else:
                break
        return ["".join(trozos)] if trozos else []
    if isinstance(valor, ast.BinOp) and isinstance(valor.op, ast.Add):
        izq = _literales_de(valor.left)
        return izq or _literales_de(valor.right)
    return []


def test_todo_gate_del_escaner_tiene_categoria_o_esta_declarado_no_publicable():
    """El contrato que impide que un gate nuevo deje al canal sin suplemento en
    silencio. Se leen los motivos del CODIGO del escaner, que es donde estan
    todos, y no los del snapshot de hoy."""
    motivos = _motivos_de_los_gates()

    gates = {nombre for nombre, _ in motivos}
    assert gates >= {"gate_feriado", "gate_blackout"}, f"se dejaron de encontrar gates: {sorted(gates)}"

    sin_clasificar = [
        f"{nombre}: {texto!r}"
        for nombre, texto in motivos
        if sup.categoria_del_motivo(texto) is None
    ]
    assert not sin_clasificar, (
        "motivos del escaner sin categoria ni declaracion de no publicable: "
        + ", ".join(sin_clasificar)
    )


def test_todo_motivo_de_la_estrategia_tiene_categoria_y_no_se_publica():
    """Desde el enchufe (fase 2) el escáner también excluye por motivos de la estrategia.

    No se publican como suplemento: son motivos técnicos, no una lectura para el
    cliente, y la cobertura fija ya garantiza una pieza por canal cubierto.
    """
    sys.path.insert(0, str(RAIZ / "scripts"))
    from estrategia.tori import puntaje

    for motivo in (puntaje.SIN_ESTRUCTURA, puntaje.CONTRA_SECUENCIA, puntaje.PRUEBA_SEMANAL,
                   "no se pudo leer: MT5 no entregó velas"):
        cat = sup.categoria_del_motivo(motivo)
        assert cat is not None and cat["publicable"] is False, motivo


def test_todo_concepto_referido_existe_en_el_mapa_de_conceptos():
    """El defecto recurrente: dos modulos que se hablan por nombre. Un concepto
    mal escrito deja el suplemento sin su parte educativa, en silencio."""
    import json

    mapa = json.loads((RAIZ / "data" / "mapa_conceptos.json").read_text(encoding="utf-8"))
    conceptos = mapa["conceptos"]

    for entrada in sup.CATEGORIAS.values():
        clave = entrada.get("concepto")
        if clave is None:
            continue
        assert clave in conceptos, f"el concepto {clave!r} no existe en mapa_conceptos.json"
        assert conceptos[clave].get("glosario"), f"{clave} sin glosario que publicar"


def test_todo_concepto_del_suplemento_trae_su_explicacion_larga():
    """El campo `glosario` es la linea del mensaje fijado del grupo, y para eso
    una linea esta bien. El suplemento necesita un parrafo que ensene.

    Y tiene que ser NEUTRAL DE CANAL: el de volatilidad decia "clave en USD/CLP"
    y salio publicado en el canal de indices, donde no aplica.
    """
    import json

    mapa = json.loads((RAIZ / "data" / "mapa_conceptos.json").read_text(encoding="utf-8"))
    conceptos = mapa["conceptos"]

    for entrada in sup.CATEGORIAS.values():
        clave = entrada.get("concepto")
        if clave is None:
            continue
        ficha = conceptos[clave]
        assert ficha.get("explicacion"), f"{clave} sin explicacion larga"
        assert len(ficha["explicacion"]) > 150, f"{clave}: la explicacion es demasiado corta"
        for atado in ("USD/CLP", "USDCLP", "peso chileno"):
            assert atado not in ficha["explicacion"], (
                f"{clave} amarra la explicacion a un activo: se publica en varios canales"
            )


def test_la_negrita_es_la_de_whatsapp_y_no_la_de_markdown():
    """WhatsApp usa *un asterisco*, no **dos**. Con dos, el cliente ve los
    asteriscos literales en el mensaje."""
    s = sup.suplemento("02_forex_divisas", FOREX_EN_DATO)
    mensaje = sup.construir_mensaje_suplemento(s)

    assert "**" not in mensaje, f"negrita de markdown en el mensaje: {mensaje}"
    assert "*" in mensaje, "el mensaje perdio toda su negrita"


def test_el_despacho_manda_el_suplemento_aunque_no_tenga_imagen():
    """`piezas_del_grupo` recorre los PNG, y el suplemento es solo texto.

    Sin esta rama el suplemento se escribia a disco y el despacho lo saltaba en
    silencio: preparado y nunca entregado, que es la peor combinacion porque
    parece que funciono.
    """
    import inspect

    import pipeline_carrusel as pc

    fuente = inspect.getsource(pc.despachar)
    assert "0_suplemento.txt" in fuente, (
        "el despacho no busca el suplemento cuando el canal no tiene imagenes"
    )
    pos_vacio = fuente.index("sin piezas: se omite")
    pos_sup = fuente.index("0_suplemento.txt")
    assert pos_sup < pos_vacio, (
        "el canal se omite antes de mirar si tiene suplemento"
    )


def test_el_suplemento_se_escribe_con_su_json_de_procedencia(tmp_path):
    """El .txt es lo que se manda; el .json deja auditable de que exclusiones
    salio, igual que `_procedencia` en las piezas de activo."""
    import pipeline_carrusel as pc

    # La ruta del historial va aparte: sin esto el test escribia en el historial
    # REAL y gastaba la ventana anti repeticion de produccion. Paso de verdad.
    escritos, avisos = pc.escribir_suplementos(
        tmp_path, FOREX_EN_DATO_CON_CLASE, grupos_activos=set(), catalogo={},
        ruta_historial=tmp_path / "historial.json",
    )

    assert len(escritos) == 1
    canal = tmp_path / "02_forex_divisas"
    assert (canal / "0_suplemento.txt").exists()
    assert (canal / "_suplemento.json").exists()
    assert any("se suplementa con dato_en_curso" in a for a in avisos)


def test_un_canal_con_piezas_no_recibe_suplemento(tmp_path):
    """El suplemento junto a piezas de activo seria el relleno que el manual
    prohibe. Su valor esta en aparecer cuando no hay nada mas que decir."""
    import pipeline_carrusel as pc

    escritos, _ = pc.escribir_suplementos(
        tmp_path, FOREX_EN_DATO_CON_CLASE,
        grupos_activos={"02_forex_divisas"}, catalogo={},
        ruta_historial=tmp_path / "historial.json",
    )
    assert escritos == []
    assert not (tmp_path / "02_forex_divisas").exists()


# ─────────────────────────────────────────────────────────────────────────────
# La ventana anti repeticion
# ─────────────────────────────────────────────────────────────────────────────
from datetime import date  # noqa: E402

HOY = date(2026, 9, 3)


def test_un_concepto_recien_usado_no_se_repite_en_el_mismo_canal():
    """El riesgo real de lo que ya esta en produccion: hoy tres canales
    recibieron el MISMO concepto porque los tres se vaciaron por el mismo
    motivo. Si manana pasa igual, lo reciben otra vez.
    """
    historial = [{"fecha": "2026-08-28", "canal": "02_forex_divisas",
                  "tipo": "concepto", "clave": "volatilidad-atr"}]

    assert sup.concepto_en_cooldown("02_forex_divisas", "volatilidad-atr", HOY, historial)


def test_el_mismo_concepto_en_OTRO_canal_no_esta_en_cooldown():
    """La ventana es por canal: cada uno tiene su propia audiencia."""
    historial = [{"fecha": "2026-08-28", "canal": "02_forex_divisas",
                  "tipo": "concepto", "clave": "volatilidad-atr"}]

    assert not sup.concepto_en_cooldown("06_criptoactivos", "volatilidad-atr", HOY, historial)


def test_pasada_la_ventana_el_concepto_vuelve_a_estar_disponible():
    viejo = [{"fecha": "2026-07-01", "canal": "02_forex_divisas",
              "tipo": "concepto", "clave": "volatilidad-atr"}]

    assert not sup.concepto_en_cooldown("02_forex_divisas", "volatilidad-atr", HOY, viejo)


def test_el_estado_se_publica_igual_y_solo_se_cae_el_concepto():
    """El estado ES la novedad; lo que se gasta con la repeticion es la parte
    educativa. Por eso la pieza sale igual, sin el bloque del concepto."""
    historial = [{"fecha": "2026-09-01", "canal": "02_forex_divisas",
                  "tipo": "concepto", "clave": "precio-descontado"}]

    s = sup.suplemento("02_forex_divisas", FOREX_EN_DATO, hoy=HOY, historial=historial)

    assert s is not None, "el estado no deberia perderse por un concepto repetido"
    assert s["concepto"] is None

    mensaje = sup.construir_mensaje_suplemento(s)
    assert "catalizadores macroeconómicos" in mensaje, "el estado tiene que seguir ahi"
    assert "📚" not in mensaje, "el bloque del concepto no se cayo"


def test_sin_historial_nada_esta_en_cooldown():
    s = sup.suplemento("02_forex_divisas", FOREX_EN_DATO, hoy=HOY, historial=[])
    assert s["concepto"] is not None


def test_registrar_deja_la_entrada_con_su_fecha_y_canal(tmp_path):
    ruta = tmp_path / "historial_suplementos.json"
    s = sup.suplemento("02_forex_divisas", FOREX_EN_DATO, hoy=HOY, historial=[])

    sup.registrar_suplemento(s, HOY, ruta=ruta)
    historial = sup.cargar_historial(ruta)

    assert len(historial) == 1
    assert historial[0]["canal"] == "02_forex_divisas"
    assert historial[0]["fecha"] == "2026-09-03"
    assert historial[0]["clave"] == "precio-descontado"
    # Y registrar de nuevo lo pone en cooldown.
    assert sup.concepto_en_cooldown("02_forex_divisas", "precio-descontado", HOY, historial)


def test_un_suplemento_sin_concepto_no_ensucia_el_historial(tmp_path):
    """Si el concepto ya estaba en cooldown no hay nada nuevo que registrar:
    anotarlo de nuevo extenderia la ventana sola, indefinidamente."""
    ruta = tmp_path / "h.json"
    historial = [{"fecha": "2026-09-01", "canal": "02_forex_divisas",
                  "tipo": "concepto", "clave": "precio-descontado"}]
    s = sup.suplemento("02_forex_divisas", FOREX_EN_DATO, hoy=HOY, historial=historial)

    sup.registrar_suplemento(s, HOY, ruta=ruta)
    assert sup.cargar_historial(ruta) == []


def test_el_historial_esta_gitignoreado_o_versionado_a_proposito():
    """Decision explicita: se VERSIONA. Es historia editorial de lo que se
    publico, igual que `historial_senales.json`, no un archivo generado."""
    gitignore = (RAIZ / ".gitignore").read_text(encoding="utf-8")
    assert "historial_suplementos" not in gitignore


def test_el_pipeline_registra_el_suplemento_al_prepararlo():
    """Sin el registro, la ventana anti repeticion nunca se llena y el mismo
    concepto sale todos los dias."""
    import inspect

    import pipeline_carrusel as pc

    fuente = inspect.getsource(pc.escribir_suplementos)
    assert "registrar_suplemento(sup" in fuente, (
        "el pipeline escribe el suplemento y no lo anota: la ventana queda vacia"
    )
    pos_registro = fuente.index("registrar_suplemento(sup")
    pos_append = fuente.index("escritos.append(sup)")
    assert pos_registro < pos_append


def test_ningun_test_escribe_en_el_historial_real():
    """El bug que se acaba de corregir: `escribir_suplementos` registraba en el
    historial REAL aunque el test le pasara un `tmp_path` para la tanda. Un test
    contaminando datos de produccion y gastando la ventana anti repeticion.

    La ruta del historial tiene que ser un parametro, no una constante.
    """
    import inspect

    import pipeline_carrusel as pc

    firma = inspect.signature(pc.escribir_suplementos)
    assert "ruta_historial" in firma.parameters, (
        "sin parametro de ruta, cualquier test que llame a esta funcion escribe "
        "en el historial de produccion"
    )
    fuente = inspect.getsource(pc.escribir_suplementos)
    assert "registrar_suplemento(sup, ruta=ruta_historial)" in fuente


def test_suplemento_cierre_amigable():
    """En sesión de cierre, el suplemento presenta un balance amable y no un tono de exclusión."""
    sup_datos = sup.suplemento("04_indices_bursatiles", [
        {"ticker": "US100", "nombre": "Nasdaq 100", "clase": "indices", "excluido": BLACKOUT}
    ])
    assert sup_datos is not None
    msg_cierre = sup.construir_mensaje_suplemento(sup_datos, es_cierre=True)
    assert "Balance de Cierre de Jornada" in msg_cierre
    assert "hoy no hay niveles, y el motivo importa" not in msg_cierre
    assert "no hay niveles que valga la pena mirar" not in msg_cierre
    assert "abrimos la encuesta de la jornada" in msg_cierre


def test_encuesta_cierre_canales_principales():
    """Verifica que cada canal de mercado disponga de una encuesta de cierre válida."""
    for canal in ("02_forex_divisas", "03_commodities_materias_primas", "04_indices_bursatiles", "05_acciones_etfs", "06_criptoactivos"):
        enc = sup.encuesta_cierre(canal)
        assert enc is not None, f"Falta encuesta de cierre para {canal}"
        assert "pregunta" in enc and len(enc["pregunta"]) > 10
        assert "opciones" in enc and 2 <= len(enc["opciones"]) <= 4
        assert enc.get("permitir_multiples") is False


def test_escribir_suplementos_en_cierre_genera_encuesta(tmp_path):
    """En cierre, escribir_suplementos genera 0_suplemento.txt con balance y _encuesta.json."""
    import pipeline_carrusel as pc

    escritos, avisos = pc.escribir_suplementos(
        tmp_path, FOREX_EN_DATO_CON_CLASE, grupos_activos=set(), catalogo={},
        ruta_historial=tmp_path / "historial.json",
        es_cierre=True,
    )
    assert len(escritos) == 1
    canal = tmp_path / "02_forex_divisas"
    assert (canal / "0_suplemento.txt").exists()
    assert (canal / "_encuesta.json").exists()
    contenido = (canal / "0_suplemento.txt").read_text(encoding="utf-8")
    assert "Balance de Cierre" in contenido


def test_despachar_suplemento_y_encuesta_cierre(tmp_path, monkeypatch):
    """Verifica que despachar procese tanto el balance como la encuesta en un canal vacío."""
    import json
    import pipeline_carrusel as pc

    tanda_dir = tmp_path / "2026-09-08_17-00_cierre_ny"
    canal_dir = tanda_dir / "02_forex_divisas"
    canal_dir.mkdir(parents=True)

    (canal_dir / "0_suplemento.txt").write_text(
        "📊 *DIVISAS · Balance de Cierre de Jornada*\nPrueba de balance.", encoding="utf-8"
    )
    (canal_dir / "_encuesta.json").write_text(
        json.dumps({
            "pregunta": "¿Cómo proyectas la apertura del dólar (USD/CLP) mañana?",
            "opciones": ["🟢 Alcista", "🔴 Bajista"],
            "permitir_multiples": False,
        }),
        encoding="utf-8",
    )

    bitacora_path = tmp_path / "historial_despachos.json"
    bitacora_path.write_text("[]", encoding="utf-8")
    monkeypatch.setattr("bitacora_despachos.HISTORIAL_PATH", bitacora_path)

    res = pc.despachar(tanda_dir, dry_run=True)
    grupos = res.get("grupos", [])
    assert any(g.get("suplemento") is True for g in grupos)
    assert any(g.get("encuesta") is True for g in grupos)


def test_suplemento_asigna_activo_ancla_al_canal():
    """Verifica que cada canal reciba su activo ancla representativo."""
    for canal, ticker_esp in [
        ("02_forex_divisas", "USDCLP"),
        ("03_commodities_materias_primas", "XAUUSD"),
        ("04_indices_bursatiles", "US100.spot"),
        ("05_acciones_etfs", "#NVDA"),
        ("06_criptoactivos", "BTCUSD"),
    ]:
        s = sup.suplemento(canal, [
            {"ticker": ticker_esp, "nombre": "Test", "excluido": BLACKOUT}
        ])
        assert s is not None
        assert s.get("activo_ancla") is not None
        assert s["activo_ancla"]["ticker"] == ticker_esp


def test_suplemento_cierre_estructura_3_tiempos():
    """El mensaje de cierre debe estructurarse en 3 tiempos con mención al gráfico TradingView."""
    s = sup.suplemento("02_forex_divisas", FOREX_EN_DATO)
    msg = sup.construir_mensaje_suplemento(s, es_cierre=True)
    assert "1️⃣ *QUÉ PASÓ EN LA JORNADA*" in msg
    assert "2️⃣ *QUÉ ESTÁ PASANDO AHORA*" in msg
    assert "3️⃣ *QUÉ VIGILAR PARA LA PRÓXIMA APERTURA*" in msg
    assert "gráfico TradingView™" in msg
    assert "Activo en foco" in msg


def test_escribir_suplementos_genera_el_recap_desde_la_lectura_del_ancla(tmp_path):
    """El recap del canal vacío es una pieza de la estrategia (enchufe, fase 3): sus niveles
    salen de la lectura del activo ancla, no de `get_asset_levels`, y su texto lo escribe el
    comando como el de cualquier pieza."""
    import json
    import pipeline_carrusel as pc

    vistos = []

    def seleccion(ticker):
        vistos.append(ticker)
        return None  # sin terminal: el canal queda con su suplemento de texto

    escritos, avisos = pc.escribir_suplementos(
        tmp_path, FOREX_EN_DATO_CON_CLASE, grupos_activos=set(), catalogo={},
        ruta_historial=tmp_path / "historial.json",
        es_cierre=True, seleccion_de=seleccion,
    )
    assert len(escritos) == 1 and vistos == ["USDCLP"]
    canal_dir = tmp_path / "02_forex_divisas"
    assert not list(canal_dir.glob("1_recap_*.json"))
    assert any("recap" in a and "USDCLP" in a for a in avisos)


def test_con_terminal_el_recap_es_una_pieza_de_la_lectura_con_texto_por_escribir(tmp_path):
    import json
    import pipeline_carrusel as pc
    sys.path.insert(0, str(RAIZ / "tests"))
    from test_pipeline_carrusel import ORO, _lectura_alcista, _sel

    usdclp = {**ORO, "ticker": "USDCLP", "nombre": "Dólar / Peso Chileno", "categoria": "forex"}
    sel = {**_sel(_lectura_alcista()), "ticker": "USDCLP"}
    pc.escribir_suplementos(
        tmp_path, FOREX_EN_DATO_CON_CLASE, grupos_activos=set(), catalogo={"USDCLP": usdclp},
        ruta_historial=tmp_path / "historial.json", es_cierre=True,
        seleccion_de=lambda t: (sel, [4119.0, 4120.0]),
    )
    payload = json.loads((tmp_path / "02_forex_divisas" / "1_recap_usdclp.json").read_text(encoding="utf-8"))
    assert payload["tipo_pieza"] == "recap" and "lectura" in payload
    assert payload["titular"] == "" and payload["_pendiente_editorial"] == ["titular", "parrafo"]
