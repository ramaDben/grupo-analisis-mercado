"""Guardrail de precios y decimales: broker rigor y Regla 1 (Cero hardcoding).

Este módulo implementa dos de las reglas más críticas del proyecto:
1. Respeto estricto del campo `digits` definido en `config/activos.json`. En
   producción, truncar un cero final (como escribir '$889.6' en vez de '$889.60')
   o agregar decimales a activos enteros como el Cobre ($14197 vs $14.197) genera
   confusión operativa inmediata en los clientes de MT5 y destruye la credibilidad
   técnica del Área de Research.
2. Prohibición absoluta de hardcodear precios en el código fuente (Regla 1). Todo
   precio debe obtenerse en tiempo de ejecución desde MT5 o el MCP market-data.
   Un precio fijo en una plantilla o script no solo envejece al instante, sino que
   ha llevado a emitir análisis desfasados cuando el mercado se mueve con fuerza.

Como todo guardrail del proyecto, este módulo es una función pura: nunca escribe
en disco, no interactúa con MT5 ni con la red, y nunca levanta excepciones. Si la
lectura del catálogo falla, devuelve fail-closed mediante el slug `error_interno`.
"""

from __future__ import annotations

import functools
import json
import re
from pathlib import Path

from .veredicto import Veredicto, aprueba, falla, primer_fallo

# Ruta al catálogo canónico de activos en el repo
_CATALOGO_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "activos.json"

# Patrón para extraer cifras con pinta de precio en texto:
# Una cifra con pinta de precio es un número con separador decimal o precedido de $.
# La coma separa miles ($4,539.72) y el punto separa decimales (889.60).
PATRON_PRECIO = re.compile(
    r"(?<![\w$])"
    r"(?P<cifra>"
    r"(?P<dolar>\$)?"
    r"\s*"
    r"(?P<entero>\d{1,3}(?:,\d{3})+|\d+)"
    r"(?:\.(?P<decimal>\d+))?"
    r")"
    r"(?![\w$])"
)


@functools.lru_cache(maxsize=1)
def _cargar_catalogo() -> dict[str, int] | None:
    """Carga config/activos.json y expone un mapeo {ticker: digits}.

    Los activos están repartidos en varios bloques (forex_commodities, indices,
    etfs, acciones, activos_complementarios). Se indexan tanto el ticker corto
    como el ticker_mt5 y las variantes conocidas para garantizar una resolución
    precisa de los decimales de cada activo.
    """
    try:
        if not _CATALOGO_PATH.exists():
            return None
        with open(_CATALOGO_PATH, encoding="utf-8") as f:
            data = json.load(f)

        mapa: dict[str, int] = {}

        # 1. forex_commodities
        for item in data.get("forex_commodities", []):
            digits = item.get("digits")
            if digits is not None:
                if "ticker" in item:
                    mapa[item["ticker"]] = digits
                if "ticker_mt5" in item:
                    mapa[item["ticker_mt5"]] = digits

        # 2. indices
        for item in data.get("indices", []):
            digits = item.get("digits")
            if digits is not None:
                if "ticker" in item:
                    mapa[item["ticker"]] = digits
                if "ticker_mt5" in item:
                    mapa[item["ticker_mt5"]] = digits

        # 3. etfs (componentes)
        for item in data.get("etfs", {}).get("componentes", []):
            digits = item.get("digits")
            if digits is not None:
                if "ticker" in item:
                    mapa[item["ticker"]] = digits
                if "ticker_mt5" in item:
                    mapa[item["ticker_mt5"]] = digits

        # 4. acciones (por sectores)
        for sector in data.get("acciones", {}).values():
            for comp in sector.get("componentes", []):
                digits = comp.get("digits")
                if digits is not None:
                    if "ticker" in comp:
                        mapa[comp["ticker"]] = digits
                    if "ticker_mt5" in comp:
                        mapa[comp["ticker_mt5"]] = digits
                        # Si tiene prefijo #, soportar también sin prefijo (#AAPL -> AAPL)
                        if comp["ticker_mt5"].startswith("#"):
                            mapa[comp["ticker_mt5"][1:]] = digits

        # 5. activos_complementarios (se evalúan al final; sobrescriben si corresponde)
        for clave, comp in data.get("activos_complementarios", {}).items():
            digits = comp.get("digits")
            if digits is not None:
                mapa[clave] = digits
                if "ticker_mt5" in comp:
                    mapa[comp["ticker_mt5"]] = digits

        return mapa
    except Exception:
        return None


@functools.lru_cache(maxsize=128)
def digits_de(ticker: str) -> int | None:
    """Devuelve los digits de un ticker según config/activos.json, o None si no está.

    Mapea variantes del símbolo (ej. USDCLP, USD/CLP, COPPER, COBRE). Si la lectura
    del archivo falla o el símbolo no existe en el catálogo, devuelve None.
    """
    try:
        catalogo = _cargar_catalogo()
        if catalogo is None:
            return None
        limpio = ticker.strip()
        if limpio in catalogo:
            return catalogo[limpio]
        mayus = limpio.upper()
        if mayus in catalogo:
            return catalogo[mayus]
        sin_barra = mayus.replace("/", "")
        if sin_barra in catalogo:
            return catalogo[sin_barra]
        if mayus.startswith("#") and mayus[1:] in catalogo:
            return catalogo[mayus[1:]]
        if f"#{mayus}" in catalogo:
            return catalogo[f"#{mayus}"]
        return None
    except Exception:
        return None


def formatear(valor: float, ticker: str) -> str | None:
    """El formateador canónico: valor con exactamente digits decimales.

    Nunca trunca ceros al final ('889.60', no '889.6') y nunca redondea a
    entero salvo que digits sea 0. Devuelve None si el ticker no está en el
    catálogo. Existe para que nadie escriba un segundo formateador en otro lado.
    """
    try:
        d = digits_de(ticker)
        if d is None:
            return None
        if d == 0:
            return f"{round(valor):d}"
        return f"{valor:.{d}f}"
    except Exception:
        return None


def _extraer_cifras_con_pinta_precio(texto: str) -> list[tuple[str, int]]:
    """Extrae tuplas (cifra, n_decimales) de números con pinta de precio en el texto.

    Descarta porcentajes (ej. 4.70%) y multiplicadores técnicos (ej. 1.5x ATR).
    """
    cifras: list[tuple[str, int]] = []
    for m in PATRON_PRECIO.finditer(texto):
        pos_fin = m.end()
        resto = texto[pos_fin:].lstrip()
        if resto.startswith(("%", "x ", "X ")):
            continue
        if re.match(r"^[xX]\b", resto):
            continue

        cifra = m.group("cifra").strip()
        tiene_dolar = bool(m.group("dolar"))
        decimal = m.group("decimal")

        if not (tiene_dolar or decimal is not None):
            continue

        n_dec = len(decimal) if decimal is not None else 0
        cifras.append((cifra, n_dec))
    return cifras


def decimales_correctos(texto: str, ticker: str) -> Veredicto:
    """Verifica que toda cifra con pinta de precio en el texto tenga exactamente digits decimales.

    Dado un ticker, toda cifra con pinta de precio (número con separador decimal o
    precedido de $) debe coincidir con sus digits. El separador de miles es la coma y
    el punto es decimal. Si el ticker no figura en el catálogo, aprueba ya que la
    validación de nombres pertenece a nombres.py.
    """
    try:
        catalogo = _cargar_catalogo()
        if catalogo is None:
            return falla(
                "error_interno",
                "No se pudo cargar el catálogo de activos config/activos.json",
                ubicacion=ticker,
            )

        esperados = digits_de(ticker)
        if esperados is None:
            return aprueba()

        cifras = _extraer_cifras_con_pinta_precio(texto)
        veredictos: list[Veredicto] = []

        for cifra, n_dec in cifras:
            if n_dec != esperados:
                if esperados == 0:
                    detalle = (
                        f"El precio '{cifra}' para {ticker} tiene decimales, "
                        "pero el activo cotiza en enteros (digits = 0)."
                    )
                else:
                    detalle = (
                        f"El precio '{cifra}' para {ticker} tiene {n_dec} decimales, "
                        f"pero se esperaban exactamente {esperados}."
                    )
                veredictos.append(
                    falla(
                        "decimales_incorrectos",
                        detalle,
                        ubicacion=f"{ticker}: {cifra}",
                    )
                )

        return primer_fallo(veredictos)
    except Exception as exc:
        return falla("error_interno", f"Fallo interno en decimales_correctos: {exc}", ubicacion=ticker)


def revisar_texto(texto: str) -> Veredicto:
    """Revisa línea por línea que las cifras respeten los digits de los tickers citados.

    El alcance por línea es la decisión de fondo de esta función, y es deliberadamente
    conservadora: inferir a qué activo pertenece un precio a través de varios párrafos
    produce falsos positivos, y un guardia que grita sobre texto correcto termina
    desactivado.

    Una línea que no nombra ningún ticker no se juzga. Si la línea nombra dos tickers
    con digits distintos, la cifra pasa si coincide con alguno de los dos: no hay
    forma honesta de decidir a cuál pertenece.
    """
    try:
        catalogo = _cargar_catalogo()
        if catalogo is None:
            return falla(
                "error_interno",
                "No se pudo cargar el catálogo de activos config/activos.json",
            )

        tickers_ordenados = sorted(catalogo.keys(), key=len, reverse=True)
        lineas = texto.splitlines()
        veredictos_lineas: list[Veredicto] = []

        for num_linea, linea in enumerate(lineas, 1):
            tickers_en_linea: list[str] = []
            for t in tickers_ordenados:
                pat = r"(?<![A-Za-z0-9])" + re.escape(t) + r"(?![A-Za-z0-9])"
                if re.search(pat, linea):
                    if t not in tickers_en_linea:
                        tickers_en_linea.append(t)

            if not tickers_en_linea:
                continue

            cifras = _extraer_cifras_con_pinta_precio(linea)
            if not cifras:
                continue

            digits_permitidos = {catalogo[t] for t in tickers_en_linea}

            for cifra, n_dec in cifras:
                if n_dec not in digits_permitidos:
                    etiqueta_tickers = "/".join(tickers_en_linea)
                    if len(digits_permitidos) == 1:
                        d_esp = next(iter(digits_permitidos))
                        detalle = (
                            f"En la línea {num_linea}, el precio '{cifra}' tiene {n_dec} decimales, "
                            f"pero {etiqueta_tickers} exige {d_esp} decimales."
                        )
                    else:
                        esperados_str = ", ".join(str(d) for d in sorted(digits_permitidos))
                        detalle = (
                            f"En la línea {num_linea}, el precio '{cifra}' tiene {n_dec} decimales, "
                            f"lo cual no coincide con ninguno de los digits de {etiqueta_tickers} ({esperados_str})."
                        )
                    veredictos_lineas.append(
                        falla(
                            "decimales_incorrectos",
                            detalle,
                            ubicacion=f"{etiqueta_tickers}: {cifra}",
                        )
                    )

        return primer_fallo(veredictos_lineas)
    except Exception as exc:
        return falla("error_interno", f"Fallo interno en revisar_texto: {exc}")


def _quitar_comentario(linea: str) -> str:
    """Quita el comentario (# ...) de una línea de código respetando comillas."""
    en_comillas = None
    escapado = False
    for i, char in enumerate(linea):
        if escapado:
            escapado = False
            continue
        if char == "\\":
            escapado = True
            continue
        if char in ('"', "'"):
            if en_comillas is None:
                en_comillas = char
            elif en_comillas == char:
                en_comillas = None
        elif char == "#" and en_comillas is None:
            return linea[:i]
    return linea


def _es_archivo_test(fuente: str) -> bool:
    """Determina si la fuente proviene de un archivo de test."""
    patrones_test = (
        "def test_",
        "class Test",
        "import pytest",
        "from pytest",
        "import unittest",
        "from unittest",
    )
    return any(p in fuente for p in patrones_test)


def _es_numero_no_precio(
    linea_codigo: str,
    cifra: str,
    entero: str,
    decimal: str | None,
    tiene_dolar: bool,
    digits: int,
) -> bool:
    """Evalúa si un número en código fuente corresponde claramente a un valor no-precio."""
    linea_lower = linea_codigo.lower()

    if tiene_dolar:
        return False

    # Cualquier entero sin $ cuando el ticker de la línea tiene digits > 0
    if digits > 0 and decimal is None:
        return True

    # Parámetros de configuración de digits
    if "digits" in linea_lower and decimal is None:
        return True

    # Timeouts o esperas
    if "timeout" in linea_lower or "wait" in linea_lower:
        return True

    # Versiones de librerías o APIs
    if "version" in linea_lower or re.search(r"\bv\d", linea_lower):
        return True

    # Años e índices
    if decimal is None:
        try:
            val = int(entero)
            if 1990 <= val <= 2050:
                return True
            if val in range(0, 10) and (
                "[" in linea_codigo
                or "idx" in linea_lower
                or "index" in linea_lower
                or "i =" in linea_lower
                or "range" in linea_lower
            ):
                return True
        except ValueError:
            pass

    return False


def sin_precio_literal(fuente: str) -> Veredicto:
    """Regla 1: prohibido escribir precios a mano en el código.

    Recibe el código fuente de un archivo. Falla si encuentra un literal numérico
    con pinta de precio (tiene decimales, o va precedido de $) en la misma línea
    que un ticker del catálogo.

    Excepciones que no son infracción:
    - Líneas dentro de un docstring o de un comentario (#).
    - Líneas de un archivo de test.
    - Números que claramente no son precios: digits, índices, años (2026),
      versiones, timeouts, y cualquier número entero sin $ cuando el ticker de la
      línea tiene digits > 0.
    """
    try:
        catalogo = _cargar_catalogo()
        if catalogo is None:
            return falla(
                "error_interno",
                "No se pudo cargar el catálogo de activos config/activos.json",
            )

        if _es_archivo_test(fuente):
            return aprueba()

        lineas = fuente.splitlines()
        en_docstring = None
        tickers_ordenados = sorted(catalogo.keys(), key=len, reverse=True)
        veredictos: list[Veredicto] = []

        for num_linea, linea in enumerate(lineas, 1):
            linea_strip = linea.strip()

            if en_docstring:
                if en_docstring in linea:
                    en_docstring = None
                continue
            else:
                if linea_strip.startswith('"""') and not (
                    linea_strip.count('"""') >= 2 and linea_strip.endswith('"""')
                ):
                    en_docstring = '"""'
                    continue
                if linea_strip.startswith("'''") and not (
                    linea_strip.count("'''") >= 2 and linea_strip.endswith("'''")
                ):
                    en_docstring = "'''"
                    continue
                if linea_strip.startswith(('"""', "'''")):
                    continue

            codigo = _quitar_comentario(linea).strip()
            if not codigo:
                continue

            tickers_en_linea: list[str] = []
            for t in tickers_ordenados:
                pat = r"(?<![A-Za-z0-9])" + re.escape(t) + r"(?![A-Za-z0-9])"
                if re.search(pat, codigo):
                    if t not in tickers_en_linea:
                        tickers_en_linea.append(t)

            if not tickers_en_linea:
                continue

            for m in PATRON_PRECIO.finditer(codigo):
                cifra = m.group("cifra").strip()
                tiene_dolar = bool(m.group("dolar"))
                entero = m.group("entero").replace(",", "")
                decimal = m.group("decimal")

                es_infraccion = False
                for t in tickers_en_linea:
                    d = catalogo[t]
                    if not _es_numero_no_precio(codigo, cifra, entero, decimal, tiene_dolar, d):
                        es_infraccion = True
                        break

                if es_infraccion:
                    ticker_infractor = tickers_en_linea[0]
                    detalle = (
                        f"Precio literal '{cifra}' encontrado en el código en la línea {num_linea} "
                        f"junto al ticker {ticker_infractor}. Todo precio debe leerse en tiempo "
                        "de ejecución desde MT5 o el MCP market-data (Regla 1)."
                    )
                    veredictos.append(
                        falla(
                            "precio_literal",
                            detalle,
                            ubicacion=f"{ticker_infractor}: {cifra}",
                        )
                    )

        return primer_fallo(veredictos)
    except Exception as exc:
        return falla("error_interno", f"Fallo interno en sin_precio_literal: {exc}")
