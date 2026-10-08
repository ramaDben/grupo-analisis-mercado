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

_HTML = re.compile(r"<\s*[a-zA-Z/!]")
_NUMERO = re.compile(r"\d[\d.,]*\d|\d")


def _huella(pieza: dict[str, Any]) -> str:
    sellado = {k: pieza.get(k) for k in ("orden", "datos", "imagenes", "anidados")}
    crudo = json.dumps(sellado, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(crudo.encode("utf-8")).hexdigest()


def nueva_pieza(
    pieza: str,
    args: dict[str, Any],
    datos: dict[str, Any],
    imagenes: dict[str, str],
    extra_campos: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    anidados = {campo: [str(i) for i in ids] for campo, ids in (extra_campos or {}).items()}
    editorial: dict[str, Any] = {campo: MARCA for campo in CAMPOS[pieza]}
    for campo, ids in anidados.items():
        editorial[campo] = {i: MARCA for i in ids}
    p = {
        "orden": {"pieza": pieza, "args": args},
        "datos": datos,
        "imagenes": imagenes,
        "anidados": anidados,
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
    for donde, texto in pares:
        if _HTML.search(texto):
            errs.append(f"{donde}: trae HTML; la maqueta la pone la plantilla, no el texto")
        for cifra in cifras_ajenas(texto, pieza.get("datos")):
            errs.append(f"{donde}: la cifra {cifra} no está en los datos del terminal")
    return errs
