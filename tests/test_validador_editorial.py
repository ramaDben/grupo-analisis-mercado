# -*- coding: utf-8 -*-
"""Pruebas unitarias para el linter y validador editorial."""
from __future__ import annotations

import pytest
from validador_editorial import (
    validar_texto,
    validar_payload_editorial,
    validar_mensaje_whatsapp,
)


def test_texto_limpio_no_arroja_errores():
    texto = "El crudo WTI mantiene soporte en 64,50 dólares antes de la apertura americana."
    assert validar_texto(texto) == []


def test_detecta_guion_largo():
    texto_con_emdash = "El oro sube — nuevo máximo histórico en la jornada."
    errores = validar_texto(texto_con_emdash)
    assert any("guion largo" in e for e in errores)


def test_detecta_voseo_comun():
    textos_con_voseo = [
        "Fijate cómo reacciona en la resistencia",
        "Si tenés dudas, revisá el gráfico",
        "Mirá el retroceso de Fibonacci",
        "Hacé tu análisis técnico",
        "Sos libre de decidir",
    ]
    for texto in textos_con_voseo:
        errores = validar_texto(texto)
        assert any("voseo" in e for e in errores), f"Falló en detectar voseo en: {texto}"


def test_detecta_placeholders():
    placeholders = [
        "Titular con [PENDIENTE]",
        "Texto de TODO para completar luego",
        "Párrafo con Lorem Ipsum dolor sit amet",
        "Sección [insertar nivel]",
    ]
    for texto in placeholders:
        errores = validar_texto(texto)
        assert any("placeholder" in e for e in errores), f"Falló en detectar placeholder en: {texto}"


def test_validar_payload_editorial_exitoso():
    payload_valido = {
        "titular": "WTI Consolida en Soporte Clave",
        "parrafo": "El precio del barril respeta la zona de demanda tras la reunión de la OPEP.",
    }
    assert validar_payload_editorial(payload_valido) == []


def test_validar_payload_editorial_errores():
    payload_incompleto = {
        "titular": "WTI",  # Muy corto (< 4 car.)
        "parrafo": "TODO: escribir parrafo",
    }
    errores = validar_payload_editorial(payload_incompleto)
    assert any("demasiado corto" in e for e in errores)
    assert any("placeholder" in e for e in errores)


def test_validar_mensaje_whatsapp_completo():
    mensaje_bueno = (
        "🎯 Activo: Petróleo WTI (CL)\n"
        "💬 Te compartimos nuestra lectura: ¿cuál es tu visión para la sesión?\n"
        "📖 Si quieres profundizar, consulta el Módulo 7 y Módulo 10 de nuestro Manual de Operaciones."
    )
    assert validar_mensaje_whatsapp(mensaje_bueno) == []


def test_validar_mensaje_whatsapp_falta_manual_o_pregunta():
    mensaje_incompleto = (
        "🎯 Activo: Petróleo WTI (CL)\n"
        "El precio está subiendo hacia la resistencia de 65,00."
    )
    errores = validar_mensaje_whatsapp(mensaje_incompleto)
    assert any("Manual de Operaciones" in e for e in errores)
    assert any("pregunta dialógica" in e for e in errores)
