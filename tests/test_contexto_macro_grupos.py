"""Tests para el módulo de cobertura macro diaria por grupo de WhatsApp."""
from __future__ import annotations

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


def test_el_canal_de_avisos_pregunta_que_significa_para_el_mercado():
    """La pregunta necesita un sujeto. En un canal tematico es el tema; en el de
    avisos, que no tiene tema, es el mercado."""
    txt = _macro_de("01_macro_y_apertura")
    assert "¿QUÉ SIGNIFICA PARA EL MERCADO?" in txt


@pytest.mark.parametrize("grupo, esperado", [
    ("02_forex_divisas", "FOREX & DIVISAS"),
    ("04_indices_bursatiles", "ÍNDICES BURSÁTILES"),
    ("06_criptoactivos", "CRIPTOACTIVOS & DIGITAL ASSETS"),
])
def test_los_canales_tematicos_siguen_nombrandose(grupo, esperado):
    """El cambio es solo para el canal sin tema: los demas no se tocan."""
    txt = _macro_de(grupo)
    assert f"CONTEXTO MACRO DIARIO · {esperado}" in txt
    assert f"¿QUÉ SIGNIFICA PARA {esperado}?" in txt


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
    assert "Consulta a tu analista" in txt


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


def test_construir_texto_contexto_macro_formatea_cifras_reales_y_curva():
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
    assert "FOCO LOCAL · ACTIVIDAD ECONÓMICA (IMACEC)" in txt
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
