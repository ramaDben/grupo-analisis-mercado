"""La pieza que agy rellena: datos del terminal congelados y huecos de texto.

`pieza.json` tiene cuatro partes: `orden` (qué se pidió), `datos` (lo que salió
del terminal y del calendario), `imagenes` (los PNG de WhatsApp ya rendidos) y
`editorial` (los únicos campos que agy escribe). Las tres primeras van selladas
con una huella: si agy las toca, la pieza no sale.

agy no decide la maqueta. Por eso el texto no puede traer HTML, y por la Regla 1
tampoco cifras que no estén en `datos`: un número inventado en un párrafo es un
precio escrito a mano, aunque lo haya escrito un modelo.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any

from pipeline_linkedin import MARCA_EDITORIAL as MARCA
from pipeline_linkedin import validar_textos

# Campos de texto plano por pieza. Los que dependen de los datos (una explicación
# por evento, una lectura por activo) se declaran al preparar, en `anidados`.
CAMPOS: dict[str, tuple[str, ...]] = {
    "activo": ("titular", "bajada", "lectura", "empuja_alza", "empuja_baja", "que_no_hacer"),
    "calendario": ("titular", "bajada", "lectura"),
    "dato": ("titular", "bajada", "que_paso", "que_significa", "que_no_hacer", "impacto"),
    "jornada": ("titular", "bajada", "lectura", "que_no_hacer"),
}

# El titular y la bajada también van impresos dentro de las láminas de WhatsApp,
# que tienen el espacio medido: un titular largo se corta en la imagen.
LARGO_MAXIMO = {"titular": 70, "bajada": 160}

# El informe es análisis general: nadie en GI está inscrito como asesor de
# inversión. Se prohíben FRASES y no palabras sueltas, porque "compra" o
# "entrar" aparecen en texto legítimo ("gerentes de compra (PMI)", "vuelve a
# entrar") y un candado que bloquea eso termina desactivado. Se comparan sin
# tildes y en minúsculas; las que van en `_PALABRA_EXACTA` exigen borde al final
# ("lote" no puede atrapar "lotería"), el resto también atrapa sus derivadas.
FRASES_PROHIBIDAS: tuple[str, ...] = (
    "compra ya", "vende ya", "es momento de comprar", "es momento de vender",
    "entra al mercado", "abre una posicion", "cierra tu posicion", "toma ganancias",
    "debes comprar", "debes vender", "deberias comprar", "deberias vender",
    "recomendamos", "te recomiendo", "te conviene", "senal de compra", "senal de venta",
    "lote", "lotes", "apalanca", "de tu capital", "arriesga",
)
_PALABRA_EXACTA = {"lote", "lotes"}

_HTML = re.compile(r"<\s*[a-zA-Z/!]")
_NUMERO = re.compile(r"\d[\d.,]*\d|\d")


def _plano(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def frases_prohibidas(texto: str) -> list[str]:
    """Las frases de instrucción o recomendación que trae `texto`."""
    plano = _plano(texto)
    return [
        f for f in FRASES_PROHIBIDAS
        if re.search(rf"\b{re.escape(f)}" + (r"\b" if f in _PALABRA_EXACTA else ""), plano)
    ]


def _huella(pieza: dict[str, Any]) -> str:
    sellado = {k: pieza.get(k) for k in ("orden", "datos", "imagenes", "anidados", "laminas")}
    crudo = json.dumps(sellado, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(crudo.encode("utf-8")).hexdigest()


def nueva_pieza(
    pieza: str,
    args: dict[str, Any],
    datos: dict[str, Any],
    imagenes: dict[str, str],
    extra_campos: dict[str, list[str]] | None = None,
    laminas: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Pieza recién preparada: todo sellado y cada campo editorial sin escribir.

    `laminas` son las imágenes de WhatsApp que llevan texto adentro (la agenda
    del día): se guardan como payload y se rinden después de validar el texto.
    """
    anidados = {campo: [str(i) for i in ids] for campo, ids in (extra_campos or {}).items()}
    editorial: dict[str, Any] = {campo: MARCA for campo in CAMPOS[pieza]}
    for campo, ids in anidados.items():
        editorial[campo] = {i: MARCA for i in ids}
    p = {
        "orden": {"pieza": pieza, "args": args},
        "datos": datos,
        "imagenes": imagenes,
        "anidados": anidados,
        "laminas": laminas or {},
        "editorial": editorial,
    }
    p["huella"] = _huella(p)
    return p


def textos(pieza: dict[str, Any]) -> list[tuple[str, str]]:
    salida: list[tuple[str, str]] = []
    for campo, valor in pieza.get("editorial", {}).items():
        if isinstance(valor, dict):
            salida.extend((f"{campo}.{k}", str(v)) for k, v in valor.items())
        else:
            salida.append((campo, str(valor)))
    return salida


def _plano_numero(token: str) -> str:
    return token.replace(".", "").replace(",", "")


def _significativo(token: str) -> bool:
    return any(c in token for c in ".,") or len(token) >= 3


def cifras_ajenas(texto: str, datos: Any) -> list[str]:
    volcado = json.dumps(datos, ensure_ascii=False)
    permitidas = {_plano_numero(t) for t in _NUMERO.findall(volcado)}
    return [
        t for t in _NUMERO.findall(texto)
        if _significativo(t) and _plano_numero(t) not in permitidas
    ]


def errores(pieza: dict[str, Any]) -> list[str]:
    """Todo lo que impide armar el HTML; lista vacía si la pieza puede salir."""
    errs: list[str] = []
    tipo = pieza.get("orden", {}).get("pieza")
    if tipo not in CAMPOS:
        return [f"pieza desconocida: {tipo!r}"]

    if pieza.get("huella") != _huella(pieza):
        errs.append("los datos, las imágenes o la orden cambiaron después de preparar: la pieza no es confiable")

    editorial = pieza.get("editorial", {})
    anidados = pieza.get("anidados", {})
    esperados = set(CAMPOS[tipo]) | set(anidados)
    for faltante in sorted(esperados - set(editorial)):
        errs.append(f"{faltante}: falta el campo")
    for sobrante in sorted(set(editorial) - esperados):
        errs.append(f"{sobrante}: campo no previsto")
    for campo, ids in anidados.items():
        valor = editorial.get(campo)
        if not isinstance(valor, dict) or set(valor) != set(ids):
            errs.append(f"{campo}: tiene que traer exactamente {', '.join(ids) or 'ningún elemento'}")

    pares = textos(pieza)
    errs.extend(validar_textos(pares))
    for campo, tope in LARGO_MAXIMO.items():
        largo = len(str(editorial.get(campo, "")))
        if largo > tope:
            errs.append(f"{campo}: tiene {largo} caracteres y el máximo es {tope}")
    for donde, texto in pares:
        if _HTML.search(texto):
            errs.append(f"{donde}: trae HTML; la maqueta la pone la plantilla, no el texto")
        for frase in frases_prohibidas(texto):
            errs.append(f"{donde}: «{frase}» es una instrucción de operar o una recomendación; "
                        "el informe es análisis general")
        for cifra in cifras_ajenas(texto, pieza.get("datos")):
            errs.append(f"{donde}: la cifra {cifra} no está en los datos del terminal")
    return errs
