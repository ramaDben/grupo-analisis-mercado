# -*- coding: utf-8 -*-
"""Suite de pruebas para scripts/guardrails/texto_cliente.py.

Verifica el comportamiento de las cinco comprobaciones de texto dirigidas a clientes,
su orden de cortocircuito en `revisar()`, los invariantes de fallo cerrado
(`error_interno` sin lanzar excepciones) y los casos críticos de falsos positivos:
- El punto medio `·` no dispara `guion_largo`.
- `tienes` y `sabes` (tuteo neutro sin tilde) no disparan `voseo`.
- Errores de lectura o configuración inexistente devuelven `error_interno` y no lanzan.
"""

from __future__ import annotations

import sys
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from guardrails import texto_cliente  # noqa: E402
from guardrails.texto_cliente import (  # noqa: E402
    canales_existen,
    revisar,
    siglas_explicadas,
    sin_guion_largo,
    sin_voseo,
    tono_admisible,
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. sin_guion_largo
# ─────────────────────────────────────────────────────────────────────────────


def test_sin_guion_largo_aprueba_texto_correcto():
    texto = (
        "El stop loss se ubica en 1.758,09. Para eso está la gestión de riesgo.\n"
        "Continuamos monitoreando la sesión americana."
    )
    v = sin_guion_largo(texto)
    assert v.ok
    assert v.motivo == ""


def test_sin_guion_largo_falla_con_guion_largo():
    texto = (
        "Primera línea sin problemas.\n"
        "El stop en 1.758,09 — para eso está.\n"
        "Tercera línea."
    )
    v = sin_guion_largo(texto)
    assert not v.ok
    assert v.motivo == "guion_largo"
    assert v.ubicacion == "linea 2"


def test_sin_guion_largo_falla_con_guion_medio():
    texto = "Niveles de soporte – a considerar en la sesión de hoy."
    v = sin_guion_largo(texto)
    assert not v.ok
    assert v.motivo == "guion_largo"
    assert v.ubicacion == "linea 1"


def test_sin_guion_largo_permite_punto_medio():
    """El punto medio · es separador de marca institucional (ej. 'ORO · XAU/USD')

    No constituye puntuación de frase ni delata IA: no debe ser penalizado.
    """
    texto = "ORO · XAU/USD: Sesgo comprador tras consolidar en soporte clave."
    v = sin_guion_largo(texto)
    assert v.ok, f"El punto medio disparó un falso positivo: {v.detalle}"


# ─────────────────────────────────────────────────────────────────────────────
# 2. siglas_explicadas
# ─────────────────────────────────────────────────────────────────────────────


def test_siglas_explicadas_con_bloque_diccionario_valido():
    texto = (
        "El mercado espera con atención el reporte de NFP en EE.UU.\n\n"
        "Diccionario rápido\n"
        "NFP: Nóminas no agrícolas que miden el empleo formal."
    )
    v = siglas_explicadas(texto, en_linea=False)
    assert v.ok


def test_siglas_explicadas_falta_bloque_diccionario():
    texto = "Atentos al dato de NFP que se publicará a las 09:30 CLT."
    v = siglas_explicadas(texto, en_linea=False)
    assert not v.ok
    assert v.motivo == "sigla_sin_explicar"
    assert v.ubicacion == "NFP"


def test_siglas_explicadas_sigla_omitida_en_bloque_existente():
    texto = (
        "Se esperan sorpresas en NFP y en el IPC chileno.\n\n"
        "Diccionario rápido\n"
        "IPC: Índice de precios al consumidor."
    )
    v = siglas_explicadas(texto, en_linea=False)
    assert not v.ok
    assert v.motivo == "sigla_sin_explicar"
    assert v.ubicacion == "NFP"


def test_siglas_explicadas_en_linea_con_parentesis():
    texto = "Presión bajista tras las vacantes de empleo (JOLTS) por debajo de lo previsto."
    v = siglas_explicadas(texto, en_linea=True)
    assert v.ok


def test_siglas_explicadas_en_linea_falla_sin_parentesis():
    texto = "Presión bajista tras las vacantes de empleo JOLTS por debajo de lo previsto."
    v = siglas_explicadas(texto, en_linea=True)
    assert not v.ok
    assert v.motivo == "sigla_sin_explicar"
    assert v.ubicacion == "JOLTS"


def test_siglas_desconocidas_no_disparan_error():
    """Palabras en mayúsculas o siglas no catalogadas en glosario no son evaluadas."""
    texto = "El índice NASDAQ consolidó junto al indicador XYZ sin novedades."
    v = siglas_explicadas(texto, en_linea=False)
    assert v.ok


# ─────────────────────────────────────────────────────────────────────────────
# 3. tono_admisible
# ─────────────────────────────────────────────────────────────────────────────


def test_tono_admisible_aprueba_lenguaje_profesional():
    texto = (
        "El cobre mantiene un sesgo bajista tras encontrar presión vendedora en resistencia.\n"
        "Impulso comprador acotado a la espera de catalizadores."
    )
    v = tono_admisible(texto)
    assert v.ok


def test_tono_admisible_falla_frase_prohibida():
    texto = "Todo indica que el activo se va a derrumbar durante la tarde."
    v = tono_admisible(texto)
    assert not v.ok
    assert v.motivo == "tono_catastrofico"
    assert v.ubicacion == "linea 1"


def test_tono_admisible_falla_palabra_con_tilde():
    texto = "Se desató el pánico entre los operadores al inicio de la jornada."
    v = tono_admisible(texto)
    assert not v.ok
    assert v.motivo == "tono_catastrofico"


def test_tono_admisible_falso_positivo_palabra_contenida():
    """'panico' debe matchear como palabra completa y no dentro de 'hispánico'."""
    texto = "El mercado hispánico muestra estabilidad en sus cotizaciones."
    v = tono_admisible(texto)
    assert v.ok, f"'hispánico' disparó erróneamente tono_catastrofico: {v.detalle}"


# ─────────────────────────────────────────────────────────────────────────────
# 4. sin_voseo
# ─────────────────────────────────────────────────────────────────────────────


def test_sin_voseo_aprueba_tuteo_chileno():
    texto = "Si quieres operar este quiebre, tienes que confirmar con el volumen en H1."
    v = sin_voseo(texto)
    assert v.ok


def test_sin_voseo_falla_con_voseo_rioplatense():
    texto = "Si querés operar este quiebre, tenés que confirmar con el volumen."
    v = sin_voseo(texto)
    assert not v.ok
    assert v.motivo == "voseo"


def test_sin_voseo_falla_con_pronombre_vos():
    texto = "Para vos que sigues las materias primas día a día."
    v = sin_voseo(texto)
    assert not v.ok
    assert v.motivo == "voseo"


def test_sin_voseo_tuteo_tienes_y_sabes_no_disparan():
    """'tienes' y 'sabes' (tuteo sin tilde) no deben disparar voseo bajo ninguna circunstancia."""
    texto = "Tú tienes la palabra y ya sabes qué niveles esperar hoy."
    v = sin_voseo(texto)
    assert v.ok, f"Tuteo neutro ('tienes'/'sabes') disparó voseo: {v.detalle}"


def test_sin_voseo_distincion_estricta_por_tilde():
    """Demuestra que la discriminación por tilde separa limpiamente voseo de tuteo.

    Normalizar acentos rompería la distinción entre 'sabés' (voseo) y 'sabes' (tuteo).
    """
    v_voseo_sabes = sin_voseo("Vos sabés lo que pasó.")
    v_tuteo_sabes = sin_voseo("Tú sabes lo que pasó.")
    assert not v_voseo_sabes.ok
    assert v_voseo_sabes.motivo == "voseo"
    assert v_tuteo_sabes.ok

    v_voseo_mira = sin_voseo("Mirá el nivel de soporte.")
    v_tuteo_mira = sin_voseo("Mira el nivel de soporte.")
    assert not v_voseo_mira.ok
    assert v_voseo_mira.motivo == "voseo"
    assert v_tuteo_mira.ok


# ─────────────────────────────────────────────────────────────────────────────
# 5. canales_existen
# ─────────────────────────────────────────────────────────────────────────────


def test_canales_existen_aprueba_canales_reales():
    texto = (
        "Revisa la actualización en 02_forex_divisas y en "
        "Grupo Inteligencia | Dólar & FX antes de la apertura."
    )
    v = canales_existen(texto)
    assert v.ok


def test_canales_existen_falla_slug_inexistente():
    texto = "La orden fue enviada al canal 99_canal_fantasma para ejecución."
    v = canales_existen(texto)
    assert not v.ok
    assert v.motivo == "canal_inexistente"
    assert v.ubicacion == "99_canal_fantasma"


def test_canales_existen_falla_nombre_oficial_inventado():
    texto = "Publicado en Grupo Inteligencia | Renta Fija y Bonos para la comunidad."
    v = canales_existen(texto)
    assert not v.ok
    assert v.motivo == "canal_inexistente"


# ─────────────────────────────────────────────────────────────────────────────
# 6. revisar (integración y cortocircuito)
# ─────────────────────────────────────────────────────────────────────────────


def test_revisar_aprueba_texto_integro():
    texto = (
        "ORO · XAU/USD: Mantiene sesgo bajista intradiario. "
        "Si quieres entrar, espera confirmación en soporte.\n\n"
        "Diccionario rápido\n"
        "RSI: Índice de fuerza relativa."
    )
    v = revisar(texto, en_linea=False)
    assert v.ok


def test_revisar_cortocircuita_en_orden_estricto():
    """El guion largo debe detectarse antes que el voseo según el orden de precedencia."""
    texto = "Atención — tenés que cerrar la posición ahora."
    v = revisar(texto, en_linea=False)
    assert not v.ok
    assert v.motivo == "guion_largo"


# ─────────────────────────────────────────────────────────────────────────────
# 7. Invariantes de robustez y fail-closed (error_interno sin lanzar)
# ─────────────────────────────────────────────────────────────────────────────


def test_lectura_glosario_imposible_devuelve_error_interno_sin_lanzar(monkeypatch, tmp_path):
    ruta_falsa = tmp_path / "glosario_que_no_existe.json"
    monkeypatch.setattr(texto_cliente, "RUTA_GLOSARIO", ruta_falsa)

    v = siglas_explicadas("Monitoreando NFP hoy.", en_linea=False)
    assert not v.ok
    assert v.motivo == "error_interno"


def test_lectura_grupos_imposible_devuelve_error_interno_sin_lanzar(monkeypatch, tmp_path):
    ruta_falsa = tmp_path / "grupos_que_no_existen.json"
    monkeypatch.setattr(texto_cliente, "RUTA_WHATSAPP_GRUPOS", ruta_falsa)

    v = canales_existen("Seguimiento en 02_forex_divisas.")
    assert not v.ok
    assert v.motivo == "error_interno"


def test_guardrail_no_lanza_con_entradas_atipicas():
    """Verifica fail-safe frente a None, tipos erróneos o strings vacíos."""
    # Texto vacío aprueba limpiamente
    assert sin_guion_largo("").ok
    assert tono_admisible("").ok
    assert sin_voseo("").ok
    assert canales_existen("").ok

    # Entrada None no debe lanzar excepción no controlada
    v_guion = sin_guion_largo(None)  # type: ignore
    assert not v_guion.ok
    assert v_guion.motivo == "error_interno"
