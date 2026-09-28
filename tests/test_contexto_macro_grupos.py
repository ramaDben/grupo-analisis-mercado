"""Tests para el módulo de cobertura macro diaria por grupo de WhatsApp."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))
if str(RAIZ / "src") not in sys.path:
    sys.path.insert(0, str(RAIZ / "src"))

import contexto_macro_grupos as cmg

SANTIAGO = ZoneInfo("America/Santiago")
_AHORA = datetime(2026, 9, 1, 10, 0, tzinfo=SANTIAGO)


def test_filtrar_eventos_para_forex_incluye_eurozona_usa_y_chile():
    eventos = [
        {"nombre": "CPI (YoY)", "pais": "Euro Zone", "impacto": "alto"},
        {"nombre": "JOLTS Job Openings", "pais": "United States", "impacto": "alto"},
        {"nombre": "Interest Rate Decision", "pais": "Chile", "impacto": "alto"},
        {"nombre": "API Weekly Crude Oil Stock", "pais": "United States", "impacto": "medio"},
    ]
    filtrados = cmg.filtrar_eventos_para_grupo("02_forex_divisas", eventos)
    nombres = [e["nombre"] for e in filtrados]
    assert "CPI (YoY)" in nombres
    assert "JOLTS Job Openings" in nombres
    assert "Interest Rate Decision" in nombres


# ─────────────────────────────────────────────────────────────────────────────
# La curva con rezago: un cero de anteayer no es "no se movió"
# ─────────────────────────────────────────────────────────────────────────────
# Los valores son los reales de DGS10 el 2026-09-04, que es el dia en que un
# "0,0 bps" salio a cinco canales.
SERIE_CON_REZAGO = {
    "nivel_pct": 4.79, "fecha_dato": "2026-09-02", "delta_1d_bps": 0.0,
    "fecha_base_1d": "2026-09-01", "delta_5d_bps": 13.0, "rezago_dias_habiles": 2,
}
SERIE_FRESCA = {
    "nivel_pct": 4.79, "fecha_dato": "2026-09-04", "delta_1d_bps": 6.0,
    "fecha_base_1d": "2026-09-03", "delta_5d_bps": 13.0, "rezago_dias_habiles": 1,
}


def test_con_rezago_se_publica_la_variacion_de_cinco_dias_con_su_fecha():
    """El caso del 2026-09-04. `delta_1d_bps` valia 0,0 porque el ultimo dato era
    del 02-sep y el anterior del 01-sep: cierto y editorialmente falso, porque se
    publico el 04-sep sin fecha. Los 13 bps de la semana estaban en el JSON y no
    salieron.
    """
    texto, fecha = cmg.variacion_soberana(SERIE_CON_REZAGO)
    assert "13,0" in texto and "5 días" in texto
    assert "0,0" not in texto
    assert "02 Sep" in fecha


def test_sin_rezago_se_publica_la_variacion_del_dia_y_sin_fecha():
    """Con el dato fresco la fecha es hoy y decirla es ruido."""
    texto, fecha = cmg.variacion_soberana(SERIE_FRESCA)
    assert texto == "+6,0 bps"
    assert fecha == ""


def test_un_delta_que_no_se_puede_calcular_se_dice_en_vez_de_desaparecer():
    """`null` significa "no sé" y `0` significa "no se movió": son distintos.

    El codigo solo miraba `is not None`, asi que un `null` hacia **desaparecer la
    linea**, y si el bloque quedaba vacio se iba tambien el encabezado de la curva
    completo. Callar es peor que el cero: el cero al menos se puede cuestionar.
    """
    serie = {**SERIE_FRESCA, "delta_1d_bps": None, "delta_5d_bps": None}
    texto, _ = cmg.variacion_soberana(serie)
    assert "no disponible" in texto.lower() or "sin variación" in texto.lower()
    assert "bps" not in texto


def test_una_serie_vacia_no_produce_linea():
    assert cmg.variacion_soberana({}) is None


def test_el_texto_publicado_nombra_los_trece_bps_y_no_el_cero(monkeypatch):
    """El contrato de punta a punta, sobre el mensaje que recibe el cliente."""
    monkeypatch.setattr(
        cmg, "cargar_curva_tasas",
        lambda serie="ALL": {"series": {"DGS10": SERIE_CON_REZAGO}},
    )
    txt = cmg.construir_texto_contexto_macro(
        grupo="01_macro_y_apertura", eventos_grupo=[], delta_ust_bps=0.0,
        ahora=_AHORA, con_imagen=True, piezas_de_niveles=0,
    )
    assert "13,0 bps en 5 días" in txt
    assert "*0,0 bps*" not in txt
    assert "02 Sep" in txt


# ─────────────────────────────────────────────────────────────────────────────
# El canal de avisos no nombra un canal que no existe
# ─────────────────────────────────────────────────────────────────────────────
def _macro_de(grupo: str) -> str:
    return cmg.construir_texto_contexto_macro(
        grupo=grupo, eventos_grupo=[], delta_ust_bps=6.0, ahora=_AHORA,
        con_imagen=True, piezas_de_niveles=0,
    )


def test_el_canal_de_avisos_no_nombra_el_canal_aspiracional():
    """El 2026-09-03 se decidio no crear un canal tematico aparte para el macro.

    El nombre inventado se quito del config y sobrevivio en
    `CONFIG_MACRO_GRUPOS`, que es texto de cliente: el 2026-09-04 el grupo de
    Avisos recibio "¿QUE SIGNIFICA PARA MACRO & APERTURA GLOBAL?", nombrando un
    canal que nadie puede abrir en WhatsApp.
    """
    txt = _macro_de("01_macro_y_apertura").upper()
    assert "APERTURA GLOBAL" not in txt


def test_el_encabezado_del_canal_de_avisos_no_lleva_sufijo_de_canal():
    """No es un canal tematico: su macro ES el panorama general, sin apellido."""
    txt = _macro_de("01_macro_y_apertura")
    assert "📊 *CONTEXTO MACRO DIARIO*" in txt
    assert "CONTEXTO MACRO DIARIO ·" not in txt


def test_el_canal_de_avisos_lleva_su_linea_de_accion():
    """Con el formato compacto (2026-09-28) la pregunta "¿que significa para X?"
    salio; el canal de avisos, sin tema propio, lee la tasa para el mercado."""
    txt = _macro_de("01_macro_y_apertura")
    assert "🎯 *Qué significa*" in txt
    assert "¿QUÉ SIGNIFICA PARA" not in txt


@pytest.mark.parametrize("grupo, esperado", [
    ("02_forex_divisas", "FOREX & DIVISAS"),
    ("04_indices_bursatiles", "ÍNDICES BURSÁTILES"),
    ("06_criptoactivos", "CRIPTOACTIVOS & DIGITAL ASSETS"),
])
def test_los_canales_tematicos_siguen_nombrandose(grupo, esperado):
    """El cambio es solo para el canal sin tema: los demas no se tocan."""
    txt = _macro_de(grupo)
    assert f"CONTEXTO MACRO DIARIO · {esperado}" in txt


def test_ninguna_fuente_del_repo_nombra_el_canal_aspiracional():
    """Contrato: el nombre no puede volver por ninguna puerta.

    Ya volvio una vez. Se quito del config el 2026-09-03 y siguio vivo en el
    modulo que redacta el mensaje, en la ficha del canal y en el indice de
    `docs/grupos_whatsapp/`, hasta que llego a un cliente. Un `grep` a mano no
    lo ataja: por eso es un test.

    `data/` queda fuera a proposito: guarda mensajes ya enviados y tandas
    generadas, o sea historia. Lo que este test protege son las FUENTES que
    producen texto nuevo.
    """
    prohibido = ("apertura global", "macro & apertura", "macro y apertura global")
    raices = ["scripts", "src", "config", "templates", "conceptos",
              "docs/grupos_whatsapp", ".claude/commands", ".agents"]
    ofensores = []
    for raiz in raices:
        base = RAIZ / raiz
        if not base.exists():
            continue
        for archivo in base.rglob("*"):
            if not archivo.is_file() or "__pycache__" in archivo.parts:
                continue
            if archivo.suffix.lower() in {".png", ".jpg", ".jpeg", ".woff2", ".pdf", ".pptx", ".xlsx"}:
                continue
            try:
                texto = archivo.read_text(encoding="utf-8", errors="ignore").lower()
            except OSError:
                continue
            for frase in prohibido:
                if frase in texto:
                    ofensores.append(f"{archivo.relative_to(RAIZ)} -> {frase!r}")
    assert not ofensores, "el nombre del canal que no existe volvio a aparecer: " + "; ".join(
        ofensores
    )


PROMESA = "compartimos los niveles"


def _texto(piezas_de_niveles):
    return cmg.construir_texto_contexto_macro(
        grupo="04_indices_bursatiles",
        eventos_grupo=[],
        delta_ust_bps=6.0,
        ahora=_AHORA,
        con_imagen=True,
        piezas_de_niveles=piezas_de_niveles,
    )


def test_sin_piezas_de_niveles_el_cierre_no_los_promete():
    """El defecto que llego a un canal real el 2026-09-04.

    El cierre prometia "a continuacion compartimos los niveles tecnicos" en el
    canal de avisos, que estructuralmente solo lleva el contexto macro y nunca
    tuvo una pieza de niveles. El archivo ya aplicaba este mismo criterio a la
    imagen ("un texto que anuncia un grafico inexistente llega roto al cliente");
    esto lo extiende a lo que el texto promete despues.
    """
    txt = _texto(0)
    assert PROMESA not in txt
    assert txt.splitlines()[-1] in cmg.CIERRES_MACRO


def test_con_piezas_de_niveles_el_cierre_si_las_anuncia():
    """El reciproco: quitar la promesa cuando SI se cumple dejaria al cliente sin
    saber que vienen mas piezas en el mismo canal."""
    txt = _texto(3)
    assert PROMESA in txt


def test_el_cierre_sigue_prometiendo_la_imagen_solo_si_existe():
    """La regla vieja no se toca al agregar la nueva."""
    con = cmg.construir_texto_contexto_macro(
        grupo="04_indices_bursatiles", eventos_grupo=[], delta_ust_bps=6.0,
        ahora=_AHORA, con_imagen=True, piezas_de_niveles=2,
    )
    sin = cmg.construir_texto_contexto_macro(
        grupo="04_indices_bursatiles", eventos_grupo=[], delta_ust_bps=6.0,
        ahora=_AHORA, con_imagen=False, piezas_de_niveles=2,
    )
    assert "imagen adjunta" in con
    assert "imagen adjunta" not in sin


def test_construir_texto_contexto_macro_formatea_cifras_reales_y_curva(monkeypatch):
    """La notacion chilena de la curva, sobre una fuente determinista.

    Este test afirmaba `+6,0 bps` pasando 6,0 por el parametro `delta_ust_bps`,
    que era el unico camino por el que la linea del 10Y NO salia de la curva. Al
    unificar las tres lineas bajo `variacion_soberana`, el parametro paso a ser
    respaldo y la cifra sale de `cargar_curva_tasas`, que en disco trae rezago:
    con el dato real el mensaje publica la variacion de 5 dias, no la de 1.

    Se monkeypatchea la curva para probar la notacion sin depender de la frescura
    de `data central/`, que cambia con cada ingesta.
    """
    monkeypatch.setattr(
        cmg, "cargar_curva_tasas",
        lambda serie="ALL": {"series": {"DGS10": SERIE_FRESCA}},
    )
    ahora = datetime(2026, 9, 1, 10, 0, tzinfo=SANTIAGO)
    eventos = [
        {
            "nombre": "CPI (YoY)",
            "pais": "Euro Zone",
            "hora_servidor": "2026-09-01 05:00",
            "previo": "2.9%",
            "forecast": "3.3%",
            "actual": "3.3%",
            "impacto": "alto",
        }
    ]
    txt = cmg.construir_texto_contexto_macro(
        grupo="02_forex_divisas",
        eventos_grupo=eventos,
        delta_ust_bps=6.0,
        ahora=ahora,
    )
    assert "CONTEXTO MACRO DIARIO · FOREX & DIVISAS" in txt
    assert ("FOCO LOCAL · ACTIVIDAD ECONÓMICA (IMACEC)" in txt) or ("FOCO LOCAL · INFLACIÓN" in txt)
    assert "+6,0 bps" in txt
    assert "+6.0 bps" not in txt
    assert "━━━━━━━━━━━━━━━━━━━" in txt



def test_asegurar_contexto_macro_grupo_crea_archivo_en_directorio(tmp_path):
    ahora = datetime(2026, 9, 1, 10, 0, tzinfo=SANTIAGO)
    eventos = [{"nombre": "JOLTS", "pais": "United States", "impacto": "alto"}]
    destino = tmp_path / "02_forex_divisas"
    
    archivo = cmg.asegurar_contexto_macro_grupo(
        grupo="02_forex_divisas",
        destino_grupo=destino,
        eventos=eventos,
        delta_ust_bps=6.0,
        ahora=ahora,
    )
    assert archivo.is_file()
    assert (destino / "0_contexto_macro.txt").is_file()
    assert "FOREX & DIVISAS" in archivo.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Guardas de integridad de datos (REGLA 1: cero hardcoding)
# ---------------------------------------------------------------------------

GRUPOS = (
    "01_macro_y_apertura",
    "02_forex_divisas",
    "03_commodities_materias_primas",
    "04_indices_bursatiles",
    "05_acciones_etfs",
    "06_criptoactivos",
    "07_oportunidades_cuantitativas",
)


def _escribir_treasury(tmp_path, fechas_valores: dict[str, float]) -> object:
    """Deja un treasury_fed_data.json de prueba con las series mínimas."""
    import json
    serie = {"historico": dict(fechas_valores)}
    payload = {"curva_rendimientos_yields": {s: serie for s in ("DGS2", "DGS10", "DGS30", "DFII10")}}
    destino = tmp_path / "treasury_fed_data.json"
    destino.write_text(json.dumps(payload), encoding="utf-8")
    return destino


def _escribir_bcch(tmp_path, imacec: dict[str, float], tpm: dict[str, float]) -> object:
    import json
    payload = {"series": {
        "IMACEC_12M_VAR": {"historico": dict(imacec)},
        "TPM": {"historico": dict(tpm)},
    }}
    destino = tmp_path / "bcch_macro_data.json"
    destino.write_text(json.dumps(payload), encoding="utf-8")
    return destino


def test_etiquetas_de_serie_usan_el_mes_real_y_no_agosto_fijo(tmp_path, monkeypatch):
    """El rótulo del eje sale de la fecha del dato, no del literal 'Ago'."""
    ruta = _escribir_treasury(tmp_path, {
        "2026-09-08": 4.10, "2026-09-09": 4.12, "2026-09-10": 4.15,
    })
    monkeypatch.setattr(cmg, "TREASURY_FED_DATA_PATH", ruta)
    etiquetas = [b["etiqueta"] for b in cmg._obtener_historial_treasury("DGS10")]
    assert all("Ago" not in e for e in etiquetas), etiquetas
    assert any("Sep" in e for e in etiquetas), etiquetas


def test_sin_datos_del_tesoro_se_detiene_en_vez_de_inventar_la_serie(tmp_path, monkeypatch):
    """Sin fuente, el módulo aborta: nunca devuelve una serie escrita a mano."""
    monkeypatch.setattr(cmg, "TREASURY_FED_DATA_PATH", tmp_path / "no_existe.json")
    with pytest.raises(cmg.DatosMacroNoDisponiblesError):
        cmg._obtener_serie_continua_treasury("DFII10", 15)


def test_sin_datos_del_bcch_se_detiene_en_vez_de_inventar_el_imacec(tmp_path, monkeypatch):
    monkeypatch.setattr(cmg, "BCCH_DATA_PATH", tmp_path / "no_existe.json")
    with pytest.raises(cmg.DatosMacroNoDisponiblesError):
        cmg._obtener_historial_imacec()


def test_payload_forex_no_inventa_el_consenso_del_imacec(tmp_path, monkeypatch):
    """Sin consenso publicado, el campo esperado y el veredicto van vacíos (CLAUDE.md)."""
    monkeypatch.setattr(cmg, "BCCH_DATA_PATH", _escribir_bcch(
        tmp_path, {"2026-06-01": 2.0, "2026-07-01": -1.49}, {"2026-09-01": 4.5}))
    monkeypatch.setattr(cmg, "TREASURY_FED_DATA_PATH", _escribir_treasury(
        tmp_path, {"2026-08-27": 4.70, "2026-08-28": 4.73}))
    p = cmg.construir_payload_story_macro("02_forex_divisas", [], 3.0, _AHORA)
    assert p["esperado"] == "", p["esperado"]
    assert p["veredicto"] == "", p["veredicto"]


def test_ningun_payload_macro_trae_precios_ni_niveles_escritos_a_mano(tmp_path, monkeypatch):
    """Ningún payload puede llevar un precio o nivel de mercado literal."""
    import json as _json
    monkeypatch.setattr(cmg, "BCCH_DATA_PATH", _escribir_bcch(
        tmp_path, {"2026-06-01": 2.0, "2026-07-01": -1.49}, {"2026-09-01": 4.5}))
    monkeypatch.setattr(cmg, "TREASURY_FED_DATA_PATH", _escribir_treasury(
        tmp_path, {"2026-08-27": 4.70, "2026-08-28": 4.73}))
    prohibidos = ("938", "5.500", "4.20", "$")
    for g in GRUPOS:
        crudo = _json.dumps(cmg.construir_payload_story_macro(g, [], 3.0, _AHORA), ensure_ascii=False)
        for token in prohibidos:
            assert token not in crudo, f"{g} lleva '{token}' escrito a mano"


def test_periodo_de_la_imagen_sale_de_la_fecha_del_dato(tmp_path, monkeypatch):
    monkeypatch.setattr(cmg, "TREASURY_FED_DATA_PATH", _escribir_treasury(
        tmp_path, {"2026-09-09": 4.10, "2026-09-10": 4.15}))
    p = cmg.construir_payload_story_macro("04_indices_bursatiles", [], 3.0, _AHORA)
    assert p["periodo"].lower().startswith("septiembre"), p["periodo"]


def test_texto_macro_de_forex_no_trae_precio_de_usdclp_escrito_a_mano(tmp_path, monkeypatch):
    monkeypatch.setattr(cmg, "BCCH_DATA_PATH", _escribir_bcch(
        tmp_path, {"2026-06-01": 2.0, "2026-07-01": -1.49}, {"2026-09-01": 4.5}))
    txt = cmg.construir_texto_contexto_macro("02_forex_divisas", [], 3.0, _AHORA)
    assert "938" not in txt
    assert "$" not in txt


def test_direccion_del_activo_reacciona_al_signo_del_driver(tmp_path, monkeypatch):
    """Con la tasa real subiendo el Oro va a la baja; bajando, al alza."""
    def oro(serie):
        monkeypatch.setattr(cmg, "TREASURY_FED_DATA_PATH", _escribir_treasury(tmp_path, serie))
        p = cmg.construir_payload_story_macro("03_commodities_materias_primas", [], 3.0, _AHORA)
        return next(a for a in p["activos"] if "Oro" in a["nombre"])["direccion"]

    assert oro({"2026-08-27": 2.10, "2026-08-28": 2.45}) == "baja"
    assert oro({"2026-08-27": 2.45, "2026-08-28": 2.10}) == "sube"


# ---------------------------------------------------------------------------
# La agenda del día: cada grupo lee los eventos que le tocan (issue de mantención)
# ---------------------------------------------------------------------------

def _evento(nombre, pais, hora, *, actual="", forecast="", previo="", impacto="alto", nombre_es=None):
    ev = {
        "nombre": nombre, "pais": pais, "hora_servidor": hora,
        "actual": actual, "forecast": forecast, "previo": previo, "impacto": impacto,
    }
    if nombre_es:
        ev["diccionario"] = {"nombre_es": nombre_es}
    return ev


def test_el_texto_macro_incluye_la_agenda_del_grupo_con_el_estado_de_cada_dato(tmp_path, monkeypatch):
    """El evento con cifra va como publicado; el que aún no sale, en modo anticipación."""
    monkeypatch.setattr(cmg, "TREASURY_FED_DATA_PATH", _escribir_treasury(
        tmp_path, {"2026-08-27": 4.70, "2026-08-28": 4.73}))
    eventos = [
        _evento("Nonfarm Payrolls", "United States", "2026-09-01 08:30",
                actual="145K", forecast="120K", nombre_es="Nóminas no agrícolas (NFP)"),
        _evento("ISM Manufacturing PMI", "United States", "2026-09-01 23:00",
                forecast="48.5", nombre_es="PMI manufacturero del ISM"),
    ]
    txt = cmg.construir_texto_contexto_macro("04_indices_bursatiles", eventos, 3.0, _AHORA)

    assert "AGENDA DEL DÍA" in txt, txt
    assert "✅" in txt and "🕐" in txt, txt
    # El publicado muestra su cifra; el pendiente muestra su hora, no un pasado.
    assert "145K" in txt, txt
    assert "23:00" in txt, txt


def test_la_agenda_usa_el_nombre_en_espanol_del_glosario_y_no_el_de_la_fuente(tmp_path, monkeypatch):
    monkeypatch.setattr(cmg, "TREASURY_FED_DATA_PATH", _escribir_treasury(
        tmp_path, {"2026-08-27": 4.70, "2026-08-28": 4.73}))
    eventos = [
        _evento("Nonfarm Payrolls", "United States", "2026-09-01 08:30",
                actual="145K", nombre_es="Nóminas no agrícolas (NFP)"),
    ]
    txt = cmg.construir_texto_contexto_macro("04_indices_bursatiles", eventos, 3.0, _AHORA)
    assert "Nóminas no agrícolas (NFP)" in txt, txt
    assert "Nonfarm Payrolls" not in txt, txt
    assert "EE.UU." in txt, txt


def test_la_agenda_convierte_las_cifras_a_notacion_chilena(tmp_path, monkeypatch):
    """Investing publica 3.3 con punto decimal; al cliente chileno le llega 3,3."""
    monkeypatch.setattr(cmg, "TREASURY_FED_DATA_PATH", _escribir_treasury(
        tmp_path, {"2026-08-27": 4.70, "2026-08-28": 4.73}))
    eventos = [
        _evento("CPI (YoY)", "United States", "2026-09-01 08:30",
                actual="3.3%", forecast="3.1%", nombre_es="Índice de precios al consumidor (IPC)"),
    ]
    txt = cmg.construir_texto_contexto_macro("04_indices_bursatiles", eventos, 3.0, _AHORA)
    assert "3,3%" in txt, txt
    assert "3.3%" not in txt, txt


def test_sin_eventos_del_dia_la_agenda_lo_dice_en_vez_de_desaparecer(tmp_path, monkeypatch):
    monkeypatch.setattr(cmg, "TREASURY_FED_DATA_PATH", _escribir_treasury(
        tmp_path, {"2026-08-27": 4.70, "2026-08-28": 4.73}))
    txt = cmg.construir_texto_contexto_macro("04_indices_bursatiles", [], 3.0, _AHORA)
    assert "AGENDA DEL DÍA" in txt, txt
    assert "Sin datos de alto impacto" in txt, txt


def test_cada_grupo_ve_solo_los_eventos_que_le_tocan(tmp_path, monkeypatch):
    """El filtro por grupo tiene que llegar al texto, no quedarse en el cálculo."""
    monkeypatch.setattr(cmg, "BCCH_DATA_PATH", _escribir_bcch(
        tmp_path, {"2026-06-01": 2.0, "2026-07-01": -1.49}, {"2026-09-01": 4.5}))
    eventos = [
        _evento("Interest Rate Decision", "Chile", "2026-09-01 18:00",
                actual="4.50%", nombre_es="Decisión de tasa de interés (TPM)"),
        _evento("Caixin Manufacturing PMI", "China", "2026-09-01 22:45",
                forecast="50.1", nombre_es="PMI manufacturero de Caixin"),
    ]
    txt = cmg.construir_texto_contexto_macro("02_forex_divisas", eventos, 3.0, _AHORA)
    assert "Decisión de tasa de interés (TPM)" in txt, txt
    # China no está en los países de Forex & Divisas.
    assert "Caixin" not in txt, txt


# ─────────────────────────────────────────────────────────────────────────────
# El sello de frescura de la IMAGEN
# ─────────────────────────────────────────────────────────────────────────────
def test_la_imagen_avisa_cuando_el_dato_viene_rezagado(monkeypatch):
    """La pieza no puede rotular "dato de cierre" una serie de hace varios dias.

    El 2026-09-14 salio al canal una imagen que decia "10 Sep 2026 . dato de
    cierre" un lunes 14: FRED no tenia el viernes 11 y el ultimo dato publicado
    era del jueves 10. Leido por un cliente, "dato de cierre" es el cierre de HOY,
    asi que la pieza afirmaba que el bono llevaba cuatro dias sin moverse.

    El texto del mensaje ya distinguia los dos casos desde `variacion_soberana`;
    la imagen no miraba el rezago. Este test ata los dos caminos al mismo umbral.
    """
    import datetime as _dt

    class _Lunes14(_dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 9, 14, 12, 0, tzinfo=tz or _dt.timezone.utc)

    monkeypatch.setattr(cmg, "datetime", _Lunes14)

    # Jueves 10 visto el lunes 14: dos dias habiles de rezago (viernes y lunes).
    assert cmg._sello_frescura("2026-09-10") == "último dato disponible"
    # Viernes 11 visto el lunes 14: un dia habil, la cadencia normal de FRED.
    assert cmg._sello_frescura("2026-09-11") == "dato de cierre"
    # El dato del propio dia.
    assert cmg._sello_frescura("2026-09-14") == "dato de cierre"


def test_el_sello_de_frescura_usa_el_mismo_umbral_que_el_texto():
    """Dos dias habiles, el mismo corte que `variacion_soberana`.

    Si divergieran, la pieza se contradiria sola: el texto pasaria a la variacion
    de 5 dias "porque el dato esta viejo" mientras la imagen lo sigue llamando
    cierre del dia.
    """
    serie_rezagada = {"delta_1d_bps": 12, "delta_5d_bps": 16,
                      "rezago_dias_habiles": 2, "fecha_dato": "2026-09-10"}
    texto, fecha = cmg.variacion_soberana(serie_rezagada)
    assert "5 días" in texto, "el texto no cambio a la variacion de 5 dias"
    assert fecha, "el texto no acompano la cifra con la fecha del dato"


def test_cifras_whatsapp_evita_anacronismo_en_evento_pasado():
    """Un evento de las 09:30 evaluado a las 11:00 sin cifra no puede decir 'se espera'."""
    ev = {
        "nombre": "NY Empire State", "pais": "United States", "hora_servidor": "2026-09-15 09:30",
        "forecast": "14.80", "actual": "",
    }
    ahora = datetime(2026, 9, 15, 11, 0, tzinfo=SANTIAGO)
    txt = cmg._cifras_para_whatsapp(ev, ahora=ahora)
    assert "se espera" not in txt
    assert "esperado 14,80 · pendiente de confirmación" == txt


def test_cifras_whatsapp_mantiene_se_espera_en_evento_futuro():
    """Un evento de las 14:00 evaluado a las 11:00 sí debe decir 'se espera'."""
    ev = {
        "nombre": "Bond Auction", "pais": "United States", "hora_servidor": "2026-09-15 14:00",
        "forecast": "5.20%", "actual": "",
    }
    ahora = datetime(2026, 9, 15, 11, 0, tzinfo=SANTIAGO)
    txt = cmg._cifras_para_whatsapp(ev, ahora=ahora)
    assert "se espera 5,20%" == txt


def test_forex_utiliza_driver_soberano_si_no_hay_evento_de_chile_hoy():
    """En un día regular sin eventos de Chile, Forex genera el driver DGS2 y no el Imacec viejo."""
    eventos_usa = [
        {"nombre": "NY Empire State", "pais": "United States", "hora_servidor": "2026-09-15 09:30", "impacto": "alto"}
    ]
    ahora = datetime(2026, 9, 15, 11, 0, tzinfo=SANTIAGO)
    payload = cmg.construir_payload_story_macro("02_forex_divisas", eventos_usa, 5.0, ahora)
    # Desde el 2026-09-28 forex cuelga del dolar global; sin su fuente, del bono.
    assert payload["indicador"] in ("Dólar global (DXY)", "Rendimiento Bono 10Y (UST 10Y)")
    assert "Actividad Económica" not in payload["indicador"]


def test_bloque_agenda_marca_concluido_discurso_pasado_sin_cifra():
    """Un discurso de Lagarde a las 12:00 evaluado a las 17:00 debe marcarse como Concluido con check verde."""
    ev = {
        "nombre": "ECB President Lagarde Speaks", "pais": "Euro Zone",
        "hora_servidor": "2026-09-21 12:00", "actual": "", "forecast": "",
    }
    ahora = datetime(2026, 9, 21, 17, 0, tzinfo=SANTIAGO)
    bloque = cmg._bloque_agenda([ev], ahora=ahora)
    texto = "\n".join(bloque)
    assert "✅" in texto
    assert "Concluido" in texto


def test_contexto_macro_da_por_concluido_el_discurso_de_lagarde_sin_inventarle_tono():
    """El discurso ya ocurrido sale en la agenda como concluido, con su nombre.

    Hasta el 2026-09-28 un bloque aparte le atribuia "un mensaje de cautela" que
    ninguna fuente habia medido. El formato compacto lo saco.
    """
    ev = {
        "nombre": "ECB President Lagarde Speaks", "pais": "Euro Zone",
        "hora_servidor": "2026-09-21 12:00", "actual": "", "forecast": "", "impacto": "alto",
    }
    ahora = datetime(2026, 9, 21, 17, 0, tzinfo=SANTIAGO)
    txt = cmg.construir_texto_contexto_macro(
        grupo="01_macro_y_apertura",
        eventos_grupo=[ev],
        delta_ust_bps=-1.0,
        ahora=ahora,
    )
    assert "SEGUIMIENTO DE BANCOS CENTRALES" not in txt
    assert "cautela" not in txt
    assert "Lagarde" in txt
    assert "Concluido" in txt




# ─────────────────────────────────────────────────────────────────────────────
# Formato compacto y sin TIPS (decisión del director, 2026-09-28)
# ─────────────────────────────────────────────────────────────────────────────
_TODOS = ("01_macro_y_apertura", "02_forex_divisas", "03_commodities_materias_primas",
          "04_indices_bursatiles", "05_acciones_etfs", "06_criptoactivos")


def _curva(monkeypatch, delta):
    serie = {"delta_1d_bps": delta, "delta_5d_bps": delta, "rezago_dias_habiles": 0,
             "fecha_dato": "2026-09-01"}
    monkeypatch.setattr(cmg, "cargar_curva_tasas",
                        lambda serie_id="ALL": {"series": {k: serie for k in ("DGS2", "DGS10", "DFII10")}})


@pytest.mark.parametrize("grupo", _TODOS)
def test_ningun_canal_publica_la_tasa_tips(grupo, monkeypatch):
    _curva(monkeypatch, 5.0)
    txt = _macro_de(grupo)
    assert "TIPS" not in txt and "DFII10" not in txt


def test_la_imagen_de_commodities_ya_no_cuelga_de_la_tasa_tips():
    assert cmg.DRIVERS_SOBERANOS["03_commodities_materias_primas"]["serie"] == "DGS10"
    assert "TIPS" not in json.dumps(cmg.DRIVERS_SOBERANOS, ensure_ascii=False)
    assert "TIPS" not in json.dumps(cmg.CONFIG_MACRO_GRUPOS, ensure_ascii=False)


@pytest.mark.parametrize("grupo", _TODOS)
def test_el_macro_compacto_no_trae_bloques_largos(grupo, monkeypatch):
    _curva(monkeypatch, 5.0)
    txt = _macro_de(grupo)
    for sobra in ("SEGUIMIENTO DE BANCOS CENTRALES", "CURVA SOBERANA Y TASAS", "¿QUÉ SIGNIFICA PARA"):
        assert sobra not in txt
    assert len(txt) < 900, len(txt)


@pytest.mark.parametrize("delta, esperado", [(5.0, "sube"), (-5.0, "baja"), (0.0, "lateral")])
def test_la_linea_de_accion_sigue_el_movimiento_medido_de_la_tasa(delta, esperado, monkeypatch):
    _curva(monkeypatch, delta)
    txt = _macro_de("02_forex_divisas")
    lectura = cmg.CONFIG_MACRO_GRUPOS["02_forex_divisas"]["lectura"][esperado]
    assert f"🎯 *Qué significa*: {lectura}" in txt


@pytest.mark.parametrize("grupo", _TODOS)
def test_la_agenda_publicada_solo_lleva_impacto_alto(grupo):
    """Decision del director, 2026-09-28: al canal solo van noticias de impacto 3.

    El escaner sigue pidiendo impacto medio al calendario, porque los blackouts
    los necesita; el filtro es de lo que se PUBLICA.
    """
    eventos = [
        {"nombre": "Interest Rate Decision", "pais": "United States", "impacto": "alto"},
        {"nombre": "Crude Oil Inventories", "pais": "United States", "impacto": "medio"},
        {"nombre": "Fed Speaks", "pais": "United States", "impacto": "bajo"},
    ]
    filtrados = cmg.filtrar_eventos_para_grupo(grupo, eventos)
    assert {e["impacto"] for e in filtrados} <= {"alto"}
    assert any(e["nombre"] == "Interest Rate Decision" for e in filtrados)


# ─────────────────────────────────────────────────────────────────────────────
# Tasas frescas del día (decisión del director, 2026-09-28)
# ─────────────────────────────────────────────────────────────────────────────
_NY = ZoneInfo("America/New_York")


def _en_vivo(monkeypatch, valor, previo, momento=datetime(2026, 9, 1, 9, 31, tzinfo=_NY)):
    def falso(series=("DGS2", "DGS10"), descargar=None):
        return {s: {"valor": valor, "cierre_previo": previo,
                    "delta_1d_bps": round((valor - previo) * 100, 1), "momento": momento,
                    "fecha": momento.date().isoformat(), "fuente": "prueba"} for s in series}
    monkeypatch.setattr(cmg, "rendimientos_en_vivo", falso)


def test_el_texto_usa_la_tasa_en_vivo_del_dia_y_no_la_de_fred(monkeypatch):
    _curva(monkeypatch, 24.0)   # FRED dice +24 en 5 dias
    _en_vivo(monkeypatch, 4.918, 4.864)
    txt = _macro_de("02_forex_divisas")
    assert "4,92%" in txt and "+5,4 bps hoy" in txt
    assert "dato al" not in txt and "5 días" not in txt
    # El 1 de septiembre Chile y Nueva York estan ambos en UTC-4.
    assert "09:31" in txt, "la hora de la cotizacion va en hora Chile"


def test_la_lectura_sigue_el_movimiento_en_vivo(monkeypatch):
    _curva(monkeypatch, 24.0)   # FRED sube, pero hoy baja
    _en_vivo(monkeypatch, 4.80, 4.864)
    txt = _macro_de("02_forex_divisas")
    assert cmg.CONFIG_MACRO_GRUPOS["02_forex_divisas"]["lectura"]["baja"] in txt


def test_una_cotizacion_de_otro_dia_no_se_publica_como_del_dia(monkeypatch):
    _curva(monkeypatch, 24.0)
    _en_vivo(monkeypatch, 4.918, 4.864, momento=datetime(2026, 8, 29, 16, 0, tzinfo=_NY))
    txt = _macro_de("02_forex_divisas")
    assert "hoy" not in txt
    assert "24,0 bps" in txt


def test_la_imagen_termina_en_la_cotizacion_en_vivo(tmp_path, monkeypatch):
    monkeypatch.setattr(cmg, "TREASURY_FED_DATA_PATH", _escribir_treasury(
        tmp_path, {"2026-08-27": 4.70, "2026-08-28": 4.73}))
    _en_vivo(monkeypatch, 4.918, 4.864)
    p = cmg.construir_payload_story_macro("04_indices_bursatiles", [], 3.0, _AHORA)
    assert p["recorrido"]["serie"][-1] == 4.92
    assert p["actual"] == "4,92%" and p["anterior"] == "4,86%"
    assert "en vivo" in p["fecha_hora"] and "09:31" in p["fecha_hora"]


# ─────────────────────────────────────────────────────────────────────────────
# Un indicador distinto por canal (decisión del director, 2026-09-28)
# ─────────────────────────────────────────────────────────────────────────────
from datetime import date as _date  # noqa: E402


def _indices(monkeypatch, vix=(15.0, 16.2), dxy=(100.97, 101.18), hoy=_date(2026, 9, 1)):
    def falso(codigo, n=15, descargar=None):
        par = {"VIX": vix, "DXY": dxy}.get(codigo)
        if par is None:
            return []
        base = [(_date(2026, 8, 1 + i), par[0]) for i in range(n - 2)]
        return base + [(_date(2026, 8, 31), par[0]), (hoy, par[1])]
    monkeypatch.setattr(cmg, "serie_diaria", falso)


def test_los_tres_canales_del_dia_llevan_imagenes_distintas(tmp_path, monkeypatch):
    monkeypatch.setattr(cmg, "TREASURY_FED_DATA_PATH", _escribir_treasury(
        tmp_path, {"2026-08-27": 4.70, "2026-08-28": 4.73}))
    _indices(monkeypatch)
    # Un dia sin dato chileno: si lo hay, forex antepone el Imacec o el IPC.
    monkeypatch.setattr(cmg, "_es_dia_foco_chile", lambda *a, **k: False)
    indicadores = [cmg.construir_payload_story_macro(g, [], 3.0, _AHORA)["indicador"]
                   for g in ("01_macro_y_apertura", "02_forex_divisas", "03_commodities_materias_primas")]
    assert len(set(indicadores)) == 3, indicadores
    assert "VIX" in indicadores[0] and "DXY" in indicadores[1] and "10Y" in indicadores[2]


def test_el_texto_de_avisos_lee_el_vix_en_porcentaje_y_con_su_lectura(monkeypatch):
    _curva(monkeypatch, 5.0)
    _indices(monkeypatch, vix=(15.0, 16.2))
    txt = _macro_de("01_macro_y_apertura")
    assert "VIX" in txt and "16,20" in txt and "+8,0% hoy" in txt
    assert cmg.CONFIG_MACRO_GRUPOS["01_macro_y_apertura"]["lectura"]["sube"] in txt


def test_la_imagen_del_vix_no_lleva_signo_de_porcentaje(tmp_path, monkeypatch):
    _indices(monkeypatch, vix=(15.0, 16.2))
    p = cmg.construir_payload_story_macro("01_macro_y_apertura", [], 3.0, _AHORA)
    assert p["actual"] == "16,20" and p["anterior"] == "15,00"
    assert "%" not in p["recorrido"]["marcadores"][0]["etiqueta"]


def test_sin_fuente_del_indice_se_cae_al_bono_con_su_propia_lectura(tmp_path, monkeypatch):
    """El VIX caido no deja al canal mudo, y la lectura no habla de volatilidad
    cuando lo que se publica es la tasa."""
    monkeypatch.setattr(cmg, "TREASURY_FED_DATA_PATH", _escribir_treasury(
        tmp_path, {"2026-08-27": 4.70, "2026-08-28": 4.73}))
    _curva(monkeypatch, 5.0)
    monkeypatch.setattr(cmg, "serie_diaria", lambda *a, **k: [])
    p = cmg.construir_payload_story_macro("01_macro_y_apertura", [], 3.0, _AHORA)
    assert "10Y" in p["indicador"]
    txt = _macro_de("01_macro_y_apertura")
    assert "VIX" not in txt
    assert cmg.CONFIG_MACRO_GRUPOS["01_macro_y_apertura"]["lectura_respaldo"]["sube"] in txt


def test_el_cierre_del_macro_no_es_siempre_el_analista(monkeypatch):
    _curva(monkeypatch, 5.0)
    cierres = set()
    for dia in range(1, 13):
        ahora = datetime(2026, 9, dia, 10, 0, tzinfo=SANTIAGO)
        txt = cmg.construir_texto_contexto_macro("01_macro_y_apertura", [], 3.0, ahora)
        cierres.add(txt.splitlines()[-1])
    assert len(cierres) >= 2 and not all("analista" in c for c in cierres)
