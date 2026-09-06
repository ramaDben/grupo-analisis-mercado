"""Guardrail de nombres: consistencia en rutas, tickers, temporalidades y canales.

Este módulo ataca de frente el defecto recurrente del repositorio: dos subsistemas
que se comunican por nombre sin que nada verifique que los nombres coincidan.
En este proyecto, un desfase de nomenclatura cuesta caro:
- Un ticker sin su sufijo del broker ('US100' en lugar de 'US100.spot') impide que
  el motor o MT5 encuentren el activo en tiempo de ejecución, provocando fallas
  silenciosas o abortos de tanda.
- Una temporalidad escrita libremente ('2H' o '1h') rompe la sincronización con
  las cuatro etiquetas canónicas de las Stories y descalza los textos con las plantillas.
- Un alias de canal que no resuelve contra 'config/whatsapp_grupos.json' arriesga
  enviar una pieza a un grupo inexistente o erróneo.
- Una ruta de cliente no reconocida centralizadamente provoca que distintos hooks
  diverjan en qué archivos auditar, permitiendo que piezas sin validar escapen
  al control previo a la entrega.

Todas las funciones de este módulo son puras: no modifican el entorno, no lanzan
excepciones (fail-closed emitiendo 'error_interno') y emiten exclusivamente los
slugs estables declarados en motivos.py.
"""

from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from pathlib import Path, PurePosixPath

from .veredicto import Veredicto, aprueba, falla, primer_fallo

# Carga segura del módulo catalog (src/market_data_mcp/catalog.py)
try:
    from market_data_mcp import catalog
except ImportError:
    import sys

    _SRC = Path(__file__).resolve().parent.parent.parent / "src"
    if str(_SRC) not in sys.path:
        sys.path.insert(0, str(_SRC))
    try:
        from market_data_mcp import catalog
    except Exception:
        catalog = None
except Exception:
    catalog = None

# Carga segura de pipeline_carrusel (scripts/pipeline_carrusel.py)
try:
    import pipeline_carrusel
except ImportError:
    import sys

    _SCRIPTS = Path(__file__).resolve().parent.parent
    if str(_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS))
    try:
        import pipeline_carrusel
    except Exception:
        pipeline_carrusel = None
except Exception:
    pipeline_carrusel = None

__all__ = [
    "Veredicto",
    "aprueba",
    "falla",
    "primer_fallo",
    "es_ruta_de_cliente",
    "ticker_valido",
    "marco_canonico",
    "alias_de_canal_valido",
]


def _normalizar_texto(texto: str) -> str:
    """Elimina tildes y diacríticos y pasa a minúsculas para comparaciones insensibles."""
    nfkd = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in nfkd if not unicodedata.combining(c))
    return sin_tildes.lower().strip()


@lru_cache(maxsize=1)
def _catalogo_tickers() -> dict[str, int] | None:
    """Obtiene el catálogo de tickers válidos llamando a catalog.load_valid_tickers.

    Se apoya exclusivamente en el módulo catalog como fuente única de verdad para no
    releer config/activos.json de forma independiente, lo que crearía una segunda
    fuente de verdad en el repositorio.
    """
    if catalog is None:
        return None
    return catalog.load_valid_tickers()


@lru_cache(maxsize=1)
def _cargar_alias_canales() -> set[str]:
    """Carga los slugs de carpetas y alias declarados desde config/whatsapp_grupos.json.

    Carga el archivo una sola vez gracias a lru_cache. Se registran tanto las formas
    en minúsculas directas como las formas normalizadas sin tildes, permitiendo
    búsquedas tolerantes a acentos y mayúsculas.
    """
    ruta_config = Path(__file__).resolve().parent.parent.parent / "config" / "whatsapp_grupos.json"
    with open(ruta_config, encoding="utf-8") as f:
        data = json.load(f)

    validos: set[str] = set()
    grupos = data.get("grupos", {})
    for slug, info in grupos.items():
        slug_limpio = str(slug).strip().lower()
        validos.add(slug_limpio)
        validos.add(_normalizar_texto(slug_limpio))

        for alias in info.get("alias", []):
            alias_limpio = str(alias).strip().lower()
            validos.add(alias_limpio)
            validos.add(_normalizar_texto(alias_limpio))

    return validos


def es_ruta_de_cliente(ruta: str | Path) -> bool:
    """Determina si una ruta corresponde a una pieza entregable o insumo de cliente.

    Que esta definición viva en UNA función y no repartida por los hooks es lo que
    impide que un hook nuevo se olvide de una carpeta crítica o diverja en la
    convención de rutas. Centralizar este predicado protege los tres puntos de
    contacto con el cliente:

    1. 'data/mensajes/**' — piezas de texto aprobadas y guardadas para WhatsApp.
    2. 'data/stories/**/*.json' — payloads de tanda con datos y textos de Stories.
    3. 'templates/stories/*.html' — plantillas que contienen la narrativa de las Stories.

    Cualquier otra ruta devuelve False (archivos de scripts, logs, datos internos,
    hojas de estilo CSS o configuraciones). Acepta rutas absolutas y relativas, con
    separadores POSIX ('/') o de Windows ('\\').
    """
    try:
        if not isinstance(ruta, (str, Path)):
            return False

        ruta_str = str(ruta).replace("\\", "/").strip()
        if not ruta_str:
            return False

        posix_path = PurePosixPath(ruta_str)
        partes = [p.lower() for p in posix_path.parts]
        n = len(partes)

        for i in range(n - 1):
            # data/mensajes/** -> piezas aprobadas y guardadas
            if partes[i] == "data" and partes[i + 1] == "mensajes":
                if n > i + 2:
                    return True

            # data/stories/**/*.json -> payloads de tanda
            if partes[i] == "data" and partes[i + 1] == "stories":
                if n > i + 2 and posix_path.suffix.lower() == ".json":
                    return True

            # templates/stories/*.html -> texto que viaja dentro de la pieza
            if partes[i] == "templates" and partes[i + 1] == "stories":
                if n == i + 3 and posix_path.suffix.lower() == ".html":
                    return True

        return False
    except Exception:
        return False


def ticker_valido(ticker: str) -> Veredicto:
    """Verifica que un ticker esté presente en el catálogo de activos del proyecto.

    La fuente de verdad es `catalog.load_valid_tickers`. Si el ticker no se
    encuentra pero existe una variante con sufijo del broker (por ejemplo, 'US100'
    frente a 'US100.spot' o 'SPY' frente a 'SPY.US'), el veredicto lo informa
    explícitamente en su detalle para subsanar el error más común del operador.
    """
    if not isinstance(ticker, str) or not ticker.strip():
        return falla(
            "ticker_desconocido",
            "El ticker no puede estar vacío.",
            ubicacion=str(ticker),
        )

    ticker_limpio = ticker.strip()

    try:
        tickers = _catalogo_tickers()
        if tickers is None:
            return falla(
                "error_interno",
                "No se pudo cargar el catálogo de tickers desde el módulo catalog.",
                ubicacion=ticker_limpio,
            )
    except Exception as e:
        return falla(
            "error_interno",
            f"No se pudo consultar el catálogo de tickers: {e}",
            ubicacion=ticker_limpio,
        )

    if ticker_limpio in tickers:
        return aprueba()

    # Buscar si existe en el catálogo con sufijo del broker (.spot, .US, etc.)
    candidatos_sufijo = [
        t
        for t in tickers
        if t.split(".")[0].upper() == ticker_limpio.upper()
        or t.upper().startswith(f"{ticker_limpio.upper()}.")
    ]
    if candidatos_sufijo:
        sugerencia = candidatos_sufijo[0]
        detalle = (
            f"El ticker '{ticker_limpio}' no existe en el catálogo. "
            f"Para este activo debe usarse el símbolo exacto del broker: '{sugerencia}'."
        )
        return falla("ticker_desconocido", detalle, ubicacion=ticker_limpio)

    # Buscar si corresponde a una acción con prefijo '#'
    candidatos_prefijo = [t for t in tickers if t.upper() == f"#{ticker_limpio.upper()}"]
    if candidatos_prefijo:
        sugerencia = candidatos_prefijo[0]
        detalle = (
            f"El ticker '{ticker_limpio}' no existe en el catálogo. "
            f"Para acciones debe usarse el prefijo '#' del broker: '{sugerencia}'."
        )
        return falla("ticker_desconocido", detalle, ubicacion=ticker_limpio)

    return falla(
        "ticker_desconocido",
        f"El ticker '{ticker_limpio}' no está en el catálogo de activos (config/activos.json).",
        ubicacion=ticker_limpio,
    )


def marco_canonico(etiqueta: str) -> Veredicto:
    """Verifica que la etiqueta de temporalidad corresponda a una de las cuatro canónicas.

    La fuente única de verdad es `pipeline_carrusel.MARCOS_CANONICOS`. No se copian
    las etiquetas en este módulo para evitar mantener tablas duplicadas que
    inevitablemente divergen con el tiempo.
    """
    if not isinstance(etiqueta, str) or not etiqueta.strip():
        return falla(
            "marco_no_canonico",
            "La etiqueta de temporalidad no puede estar vacía.",
            ubicacion=str(etiqueta),
        )

    etiqueta_limpia = etiqueta.strip()

    try:
        if pipeline_carrusel is None:
            return falla(
                "error_interno",
                "No se pudo importar pipeline_carrusel para verificar MARCOS_CANONICOS.",
                ubicacion=etiqueta_limpia,
            )
        etiquetas_validas = {val[0] for val in pipeline_carrusel.MARCOS_CANONICOS.values()}
    except Exception as e:
        return falla(
            "error_interno",
            f"Error al obtener MARCOS_CANONICOS de pipeline_carrusel: {e}",
            ubicacion=etiqueta_limpia,
        )

    if etiqueta_limpia in etiquetas_validas:
        return aprueba()

    opciones = ", ".join(sorted(etiquetas_validas))
    return falla(
        "marco_no_canonico",
        f"La temporalidad '{etiqueta_limpia}' no es una de las cuatro etiquetas canónicas ({opciones}).",
        ubicacion=etiqueta_limpia,
    )


def alias_de_canal_valido(alias: str) -> Veredicto:
    """Valida si un alias o slug de canal existe en config/whatsapp_grupos.json.

    Acepta tanto el slug de carpeta (ej. '02_forex_divisas') como cualquier alias
    declarado en lenguaje natural ('metales', 'oro', 'forex', 'cripto'), siendo
    insensible a mayúsculas y a tildes.
    """
    if not isinstance(alias, str) or not alias.strip():
        return falla(
            "alias_de_canal_desconocido",
            "El alias o slug de canal no puede estar vacío.",
            ubicacion=str(alias),
        )

    alias_limpio = alias.strip()

    try:
        validos = _cargar_alias_canales()
    except Exception as e:
        return falla(
            "error_interno",
            f"Error al leer la configuración de grupos de WhatsApp: {e}",
            ubicacion=alias_limpio,
        )

    if alias_limpio.lower() in validos or _normalizar_texto(alias_limpio) in validos:
        return aprueba()

    return falla(
        "alias_de_canal_desconocido",
        f"El alias de canal '{alias_limpio}' no resuelve contra config/whatsapp_grupos.json.",
        ubicacion=alias_limpio,
    )
