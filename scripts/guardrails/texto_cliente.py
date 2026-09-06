# -*- coding: utf-8 -*-
"""Guardrails de texto dirigido a clientes de la comunidad de WhatsApp.

Este módulo implementa comprobaciones puras sobre piezas textuales (mensajes,
pies de foto, análisis y comunicados) para prevenir cinco defectos recurrentes
que deterioran la credibilidad institucional o generan confusión operativa:

1. **Guiones largos o medios como incisos**: delatan generación automática por IA
   en textos firmados por analistas reales.
2. **Siglas sin explicar**: excluyen a clientes novatos al introducir jerga macro
   sin traducción pedagógica (issue #46).
3. **Tono dramático o catastrofista**: sustituye el análisis direccional profesional
   por histeria o atribución de sentimientos al mercado.
4. **Voseo rioplatense**: quiebra la voz corporativa del proyecto, fijada en tuteo
   chileno neutro. La distinción exige evaluar tildes de forma estricta.
5. **Canales inexistentes**: evita referenciar destinos de publicación o nombres
   aspiracionales que no existen en WhatsApp (incidente real del 2026-09-03).

Invariantes del módulo:
- Función pura: recibe cadenas, devuelve `Veredicto`, no produce efectos colaterales.
- Fail-closed: ante cualquier error de lectura de configuración, devuelve `error_interno`.
- Jamás lanza excepciones hacia el exterior (`raise` prohibido).
"""

from __future__ import annotations

import functools
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from .veredicto import Veredicto, aprueba, falla, primer_fallo

RAIZ = Path(__file__).resolve().parent.parent.parent
RUTA_GLOSARIO = RAIZ / "data" / "glosario_siglas.json"
RUTA_WHATSAPP_GRUPOS = RAIZ / "config" / "whatsapp_grupos.json"

# Expresiones prohibidas por la política de registro del proyecto (.agents/rules/proyecto.md,
# Sección 4: "Tono: profesional con gancho, nunca dramático").
# Toda pieza debe tomar postura direccional técnica ("sesgo bajista", "presión vendedora"),
# pero sin dramatismos, sensacionalismo ni psicología de masas infundada.
EXPRESIONES_PROHIBIDAS: tuple[str, ...] = (
    "se va a derrumbar",
    "sensacion pesima",
    "se va a disparar",
    "va a explotar",
    "esta volando",
    "por las nubes",
    "panico",
    "euforia",
    "terror",
    "colapso",
    "catastrofe",
    "desplome",
)

# Formas de voseo rioplatense prohibidas en textos de cliente.
# La distinción frente al tuteo neutro chileno descansa en la acentuación exacta:
# 'sabés' es voseo mientras que 'sabes' es tuteo válido; 'mirá' es voseo mientras
# que 'mira' es tuteo correcto. Normalizar acentos eliminaría esta frontera y
# generaría falsos positivos sobre redacción reglamentaria.
FORMAS_VOSEO: tuple[str, ...] = (
    "vos",
    "tenés",
    "tenes",
    "sabés",
    "podés",
    "podes",
    "querés",
    "queres",
    "hacés",
    "venís",
    "decís",
    "andá",
    "mirá",
    "fijate",
    "acordate",
)


def _quitar_tildes(texto: str) -> str:
    """Elimina acentos y diacríticos preservando caracteres base en minúsculas."""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


@functools.lru_cache(maxsize=8)
def _leer_json_cache(ruta_str: str) -> dict[str, Any]:
    """Lee y decodifica un archivo JSON con caché de lectura para optimizar llamadas puras."""
    with open(ruta_str, "r", encoding="utf-8") as f:
        return json.load(f)


def _obtener_glosario() -> tuple[dict[str, Any] | None, str | None]:
    """Carga de forma segura el glosario canónico de siglas macro."""
    try:
        data = _leer_json_cache(str(RUTA_GLOSARIO.resolve()))
        return data, None
    except Exception as err:
        return None, str(err)


def _obtener_grupos() -> tuple[dict[str, Any] | None, str | None]:
    """Carga de forma segura el catálogo de grupos de WhatsApp del sistema."""
    try:
        data = _leer_json_cache(str(RUTA_WHATSAPP_GRUPOS.resolve()))
        return data, None
    except Exception as err:
        return None, str(err)


def _extraer_siglas(glosario: dict[str, Any]) -> set[str]:
    """Extrae el conjunto canónico de siglas financieras y macroeconómicas del glosario."""
    siglas: set[str] = set()
    for k, v in glosario.items():
        if k.startswith("_"):
            continue
        if k.isdigit():
            if isinstance(v, dict) and "sigla" in v and isinstance(v["sigla"], str):
                siglas.add(v["sigla"].strip())
        elif isinstance(v, dict):
            partes = k.strip().split()
            if len(partes) == 1:
                siglas.add(partes[0])
            elif "sigla" in v and isinstance(v["sigla"], str):
                siglas.add(v["sigla"].strip())
    return siglas


def sin_guion_largo(texto: str) -> Veredicto:
    """Verifica que el texto no incluya guiones largos (—) ni medios (–).

    El guion largo como inciso delata automatización por modelos de lenguaje.
    En piezas institucionales firmadas por analistas, su aparición resta
    credibilidad técnica. El punto medio (·) sí está autorizado por ser
    separador de identidad de marca (ej. 'ORO · XAU/USD').
    """
    try:
        for num_linea, linea in enumerate(texto.splitlines(), start=1):
            if "—" in linea or "–" in linea:
                return falla(
                    "guion_largo",
                    "El guion largo o medio como inciso delata redacción por IA. Reescribir con punto, coma o dos puntos.",
                    ubicacion=f"linea {num_linea}",
                )
        return aprueba()
    except Exception as err:
        return falla("error_interno", f"Error inesperado al revisar guiones: {err}")


def siglas_explicadas(texto: str, en_linea: bool = False) -> Veredicto:
    """Verifica que toda sigla del glosario que figure en el texto esté explicada.

    Garantiza que la audiencia principiante no quede marginada por jerga macro
    sin traducir (issue #46).
    - En modo mensaje regular (`en_linea=False`): exige el bloque 'Diccionario rápido'
      y la presencia de la sigla dentro de dicho bloque.
    - En modo pie de foto o Story (`en_linea=True`): exige que la sigla se introduzca
      entre paréntesis acompañada de su traducción en español.
    """
    try:
        glosario_data, err = _obtener_glosario()
        if glosario_data is None:
            return falla(
                "error_interno",
                f"No se pudo cargar el glosario de siglas: {err}",
                ubicacion="data/glosario_siglas.json",
            )

        siglas_conocidas = _extraer_siglas(glosario_data)
        if not siglas_conocidas:
            return aprueba()

        # Identificar siglas presentes en el texto ordenadas por primera aparición
        siglas_encontradas: list[tuple[int, str]] = []
        for sigla in siglas_conocidas:
            patron = rf"\b{re.escape(sigla)}\b"
            m = re.search(patron, texto, flags=re.IGNORECASE)
            if m:
                siglas_encontradas.append((m.start(), sigla))

        siglas_encontradas.sort(key=lambda x: x[0])
        if not siglas_encontradas:
            return aprueba()

        if en_linea:
            for _, sigla in siglas_encontradas:
                patron_paren = rf"\(\s*{re.escape(sigla)}\s*\)"
                if not re.search(patron_paren, texto, flags=re.IGNORECASE):
                    return falla(
                        "sigla_sin_explicar",
                        f"La sigla '{sigla}' debe explicarse en línea entre paréntesis, ej. 'vacantes de empleo ({sigla})'.",
                        ubicacion=sigla,
                    )
            return aprueba()
        else:
            encabezado_match = re.search(r"diccionario\s+r[aá]pido", texto, flags=re.IGNORECASE)
            if not encabezado_match:
                primera_sigla = siglas_encontradas[0][1]
                return falla(
                    "sigla_sin_explicar",
                    f"El mensaje contiene la sigla '{primera_sigla}' pero carece del bloque 'Diccionario rápido'.",
                    ubicacion=primera_sigla,
                )

            bloque_diccionario = texto[encabezado_match.start():]
            for _, sigla in siglas_encontradas:
                patron_sigla = rf"\b{re.escape(sigla)}\b"
                if not re.search(patron_sigla, bloque_diccionario, flags=re.IGNORECASE):
                    return falla(
                        "sigla_sin_explicar",
                        f"La sigla '{sigla}' aparece en el cuerpo pero no está explicada en el 'Diccionario rápido'.",
                        ubicacion=sigla,
                    )
            return aprueba()
    except Exception as err:
        return falla("error_interno", f"Error inesperado al evaluar siglas: {err}")


def tono_admisible(texto: str) -> Veredicto:
    """Verifica que el texto no contenga giros dramáticos ni sensacionalistas.

    El proyecto exige una postura direccional rigurosa y lenguaje profesional,
    restringiendo expresiones hiperbólicas como 'se va a disparar' o 'pánico',
    las cuales generan impulsividad o miedo injustificado en los lectores.
    """
    try:
        for num_linea, linea in enumerate(texto.splitlines(), start=1):
            linea_norm = _quitar_tildes(linea.lower())
            for expr in EXPRESIONES_PROHIBIDAS:
                expr_norm = _quitar_tildes(expr.lower())
                partes = expr_norm.split()
                if len(partes) == 1:
                    patron = rf"\b{re.escape(partes[0])}\b"
                else:
                    patron = r"\b" + r"\s+".join(re.escape(p) for p in partes) + r"\b"

                if re.search(patron, linea_norm):
                    return falla(
                        "tono_catastrofico",
                        f"Expresión prohibida por tono sensacionalista: '{expr}'. Usar terminología profesional objetiva.",
                        ubicacion=f"linea {num_linea}",
                    )
        return aprueba()
    except Exception as err:
        return falla("error_interno", f"Error inesperado al revisar tono: {err}")


def sin_voseo(texto: str) -> Veredicto:
    """Verifica la ausencia de voseo rioplatense en textos para clientes.

    El tono oficial del canal es tuteo chileno neutro. Se discriminan las formas
    de voseo mediante su acentuación explícita para evitar falsos positivos sobre
    formas válidas de tuteo (ej. 'sabés' es voseo, pero 'sabes' es tuteo correcto).
    """
    try:
        for num_linea, linea in enumerate(texto.splitlines(), start=1):
            for forma in FORMAS_VOSEO:
                patron = rf"\b{re.escape(forma)}\b"
                if re.search(patron, linea, flags=re.IGNORECASE):
                    return falla(
                        "voseo",
                        f"Forma de voseo '{forma}' no admitida en texto de cliente. Emplear tuteo neutro.",
                        ubicacion=f"linea {num_linea}",
                    )
        return aprueba()
    except Exception as err:
        return falla("error_interno", f"Error inesperado al verificar voseo: {err}")


def canales_existen(texto: str) -> Veredicto:
    """Verifica que los canales citados existan en config/whatsapp_grupos.json.

    Previene referencias a canales inventados o inexistentes que los clientes no
    pueden encontrar en su aplicación de mensajería (incidente 2026-09-03).
    Inspecciona tanto identificadores canónicos ('NN_algo_algo') como los nombres
    oficiales ('Grupo Inteligencia | ...').
    """
    try:
        grupos_data, err = _obtener_grupos()
        if grupos_data is None:
            return falla(
                "error_interno",
                f"No se pudo cargar la configuración de grupos de WhatsApp: {err}",
                ubicacion="config/whatsapp_grupos.json",
            )

        grupos = grupos_data.get("grupos", {})
        slugs_validos = {k.lower() for k in grupos.keys()}

        sufijos_oficiales: list[str] = []
        for g in grupos.values():
            if isinstance(g, dict) and "nombre_oficial" in g:
                nom = g["nombre_oficial"].strip()
                if "|" in nom:
                    sufijos_oficiales.append(nom.split("|", 1)[1].strip())
                else:
                    sufijos_oficiales.append(nom)

        # 1. Comprobar identificadores tipo NN_algo_algo
        for match in re.finditer(r"\b(\d{2}_[a-zA-Z0-9_]+)\b", texto):
            slug_encontrado = match.group(1)
            if slug_encontrado.lower() not in slugs_validos:
                return falla(
                    "canal_inexistente",
                    f"El slug de canal '{slug_encontrado}' no existe en config/whatsapp_grupos.json.",
                    ubicacion=slug_encontrado,
                )

        # 2. Comprobar menciones con prefijo oficial 'Grupo Inteligencia |'
        for match in re.finditer(r"\bGrupo Inteligencia\s*\|\s*", texto, flags=re.IGNORECASE):
            resto = texto[match.end():]
            canal_valido_hallado = False
            for sufijo in sufijos_oficiales:
                patron_sufijo = rf"^{re.escape(sufijo)}(?:\b|[^\w]|$)"
                if re.search(patron_sufijo, resto, flags=re.IGNORECASE):
                    canal_valido_hallado = True
                    break

            if not canal_valido_hallado:
                corte = re.search(r"^([^\n\r,\.\;\"\'\(\)]+)", resto)
                nombre_inventado = corte.group(1).strip() if corte else resto.strip()
                canal_reportado = f"Grupo Inteligencia | {nombre_inventado}".strip()
                return falla(
                    "canal_inexistente",
                    f"El canal '{canal_reportado}' no existe en config/whatsapp_grupos.json.",
                    ubicacion=canal_reportado,
                )

        return aprueba()
    except Exception as err:
        return falla("error_interno", f"Error inesperado al validar canales: {err}")


def revisar(texto: str, en_linea: bool = False) -> Veredicto:
    """Evalúa las cinco comprobaciones de texto en orden canónico de precedencia.

    Devuelve el primer veredicto negativo encontrado, o veredicto positivo si
    el texto satisface la totalidad de las reglas.
    """
    return primer_fallo([
        sin_guion_largo(texto),
        siglas_explicadas(texto, en_linea=en_linea),
        tono_admisible(texto),
        sin_voseo(texto),
        canales_existen(texto),
    ])
