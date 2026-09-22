# -*- coding: utf-8 -*-
"""Linter y validador de estilo editorial para piezas de análisis y WhatsApp.

Asegura el cumplimiento estricto de las directrices institucionales de Grupo Inteligencia:
1. Prohibición absoluta de guiones largos ('—', U+2014).
2. Prohibición de voseo (ej. tenés, mirá, hacé, podés) en favor del trato directo neutral/chileno.
3. Bloqueo de placeholders ('TODO', 'PENDIENTE', 'TBD', etc.).
4. Verificación de anclaje pedagógico al Manual de Operaciones y apertura a debate en mensajes finales.
"""
from __future__ import annotations

import re
from typing import Any

# Palabras características de voseo rioplatense a evitar
PATRON_VOSEO = re.compile(
    r"\b(tenés|podés|mirá|fijate|hacé|sabés|querés|andá|sos|vení|decime|avisame|contanos|esperá|tomá|che)\b",
    re.IGNORECASE,
)

# Textos temporales o placeholders no permitidos en producción
PATRONES_PLACEHOLDER = [
    re.compile(r"\[pendiente\]", re.IGNORECASE),
    re.compile(r"\bTODO\b"),
    re.compile(r"\bTBD\b"),
    re.compile(r"\[insertar", re.IGNORECASE),
    re.compile(r"\[completar", re.IGNORECASE),
    re.compile(r"\blorem ipsum\b", re.IGNORECASE),
]

GUION_LARGO = "\u2014"  # '—'


def validar_texto(texto: str, campo: str = "texto") -> list[str]:
    """Evalúa un fragmento de texto contra las normas de estilo y ortografía institucional."""
    errores: list[str] = []
    if not texto or not texto.strip():
        return [f"{campo}: texto vacío o inexistente"]

    if GUION_LARGO in texto:
        errores.append(
            f"{campo}: contiene guion largo ('—', U+2014) no permitido. Use guion estándar ('-'), dos puntos o paréntesis."
        )

    voseo_match = PATRON_VOSEO.search(texto)
    if voseo_match:
        errores.append(
            f"{campo}: contiene voseo no admitido ('{voseo_match.group(0)}'). Utilice trato neutro/chileno (ej. tienes, mira, haz, puedes)."
        )

    for patron in PATRONES_PLACEHOLDER:
        match = patron.search(texto)
        if match:
            errores.append(
                f"{campo}: contiene marcador temporal/placeholder no permitido ('{match.group(0)}')."
            )

    return errores


def validar_payload_editorial(payload: dict[str, Any], identificador: str = "") -> list[str]:
    """Valida los campos editoriales ('titular', 'parrafo') de un payload de carrusel/story."""
    prefijo = f"[{identificador}] " if identificador else ""
    errores: list[str] = []

    titular = str(payload.get("titular", "")).strip()
    parrafo = str(payload.get("parrafo", "")).strip()

    if not titular:
        errores.append(f"{prefijo}Falta el titular editorial.")
    else:
        if len(titular) < 4:
            errores.append(f"{prefijo}Titular demasiado corto (< 4 caracteres): '{titular}'")
        elif len(titular) > 100:
            errores.append(f"{prefijo}Titular excede los 100 caracteres recomendados ({len(titular)} car.).")
        errores.extend(f"{prefijo}{e}" for e in validar_texto(titular, campo="titular"))

    if not parrafo:
        errores.append(f"{prefijo}Falta el párrafo editorial.")
    else:
        if len(parrafo) < 10:
            errores.append(f"{prefijo}Párrafo demasiado corto (< 10 caracteres): '{parrafo}'")
        errores.extend(f"{prefijo}{e}" for e in validar_texto(parrafo, campo="parrafo"))

    return errores


def validar_mensaje_whatsapp(mensaje: str, identificador: str = "") -> list[str]:
    """Valida la integridad del mensaje de texto que acompaña al gráfico en WhatsApp."""
    prefijo = f"[{identificador}] " if identificador else ""
    errores: list[str] = []

    errores.extend(f"{prefijo}{e}" for e in validar_texto(mensaje, campo="mensaje_whatsapp"))

    # Anclaje al Manual de Operaciones
    if "Manual de Operaciones" not in mensaje and "Módulo" not in mensaje:
        errores.append(
            f"{prefijo}El mensaje no incluye la referencia obligatoria al Manual de Operaciones o a sus Módulos."
        )

    # Apertura a debate comunitario
    if "¿" not in mensaje and "?" not in mensaje:
        errores.append(
            f"{prefijo}El mensaje no incluye una pregunta dialógica de apertura a la comunidad."
        )

    return errores
