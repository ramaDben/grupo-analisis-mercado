#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
curva_reader.py
Lectura de solo lectura de la curva soberana de EE.UU. (rendimientos del Tesoro,
tasa real TIPS y compensación por inflación) desde `data central/`.

Existe porque la curva **no es un símbolo de mercado**: no se puede pedir con
`get_asset_levels`. Los datos ya los ingiere
`.agents/skills/ecosistema-datos-macro/scripts/extractor_usa.py` a
`data central/DATA USA/raw/treasury_fed_data.json`, pero lo único publicado hacia
afuera hasta ahora eran NIVELES (`metricas_clave` de `macro_bias_output.json`). Los
deltas en puntos base quedaban dentro de `scripts/macro_bias_engine.py`, y solo a 5
días.

Por qué importa: el Playbook no trata la curva como contexto sino como vector de
transmisión medido. `DFII10` (tasa real TIPS 10Y) es el driver dominante del Oro con
elasticidad β≈-1,5, y `DGS10` es la tasa de descuento del US100 con un umbral
explícito ("DGS10 > 4,70% comprime múltiplos P/E").

**No escribe nada.** El motor de sesgo (`macro_bias_engine.py`) sigue siendo el único
escritor de `macro_bias_output.json` (Single-Writer Pattern). Este módulo lee el dato
crudo, así que responde aunque el motor no haya corrido y no puede alterar el sesgo.

Nota de fuente, para que nadie la reintroduzca mal: la tasa real 10Y es la serie
`DFII10`. El archivo
`data central/DATA ORO Y COMMODITIES/raw/US_TIPS_Real_Rates_ETF_Historical_5Y.csv`
**no sirve** para eso: es el precio de un ETF de TIPS (valores en torno a 105), no una
tasa (2,40%). Usarlo daría un número que no significa lo que el lector cree.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from market_data_mcp.bias_reader import cargar_config_staleness, validar_staleness

BASE_DIR = Path(__file__).resolve().parents[2]
ARCHIVO_DEFAULT = BASE_DIR / "data central" / "DATA USA" / "raw" / "treasury_fed_data.json"

# Series que el extractor persiste hoy. "ALL" devuelve todas.
SERIES_VALIDAS = ("DGS2", "DGS10", "DGS30", "DFF", "DFII10", "T10YIE")

# Un punto base es una centésima de punto porcentual. Las series vienen en
# porcentaje ("unidad": "porcentaje"), así que la diferencia se multiplica por 100.
BPS_POR_PUNTO_PORCENTUAL = 100.0

# Rezago habitual de publicación de FRED (un día hábil). Por encima de esto la
# respuesta lo marca, pero NO es un error: el archivo puede estar recién bajado y la
# fuente simplemente no ha publicado todavía.
REZAGO_HABIL_ESPERADO = 1


def _serie_cronologica(historico: dict[str, Any]) -> list[tuple[str, float]]:
    """Ordena `{fecha_iso: valor}` de más antiguo a más reciente, descartando nulos.

    El extractor acumula el histórico en un dict y las claves NO quedan en orden
    (`2026-08-19` aparece después de `2026-07-08` en el archivo real), así que
    ordenar es obligatorio y no cosmético: sin esto el "último dato" sería el que
    quedó último en el JSON, que es cualquiera.
    """
    puntos: list[tuple[str, float]] = []
    for fecha, valor in historico.items():
        if valor is None:
            continue
        try:
            puntos.append((fecha, float(valor)))
        except (TypeError, ValueError):
            continue
    return sorted(puntos, key=lambda par: par[0])


def _delta_bps(puntos: list[tuple[str, float]], n_registros: int) -> tuple[float | None, str | None]:
    """Cambio en puntos base entre el último punto y el de `n_registros` atrás.

    Retorna `(None, None)` si no hay suficientes puntos. **Un delta desconocido es
    `None`, nunca `0.0`**: cero significa "no se movió", que es una afirmación
    distinta de "no sé".

    Los registros son días de PUBLICACIÓN, no días de calendario, y la frecuencia
    depende de la serie: las yields y los TIPS publican solo en días hábiles (un
    delta de 1 registro sobre un lunes compara contra el viernes, que es lo
    correcto), pero `DFF` publica los siete días porque es un promedio diario. Por eso
    cada serie informa su `frecuencia_publicacion` y la `fecha_base` de cada delta:
    sin eso, comparar el delta de 5 registros de `DFF` con el de `DGS10` mezclaría una
    semana corrida con una semana hábil.
    """
    if len(puntos) < n_registros + 1:
        return None, None
    fecha_base, valor_base = puntos[-1 - n_registros]
    _, valor_actual = puntos[-1]
    return round((valor_actual - valor_base) * BPS_POR_PUNTO_PORCENTUAL, 1), fecha_base


def _dias_habiles_entre(desde: date, hasta: date) -> int:
    """Días hábiles (lunes a viernes) transcurridos entre dos fechas, sin contar `desde`.

    No conoce feriados: es una medida de rezago para informar, no para decidir si el
    mercado opera. Para eso está `get_symbol_spec`, que sí cruza el calendario NYSE.
    """
    if hasta <= desde:
        return 0
    dias = 0
    cursor = desde
    while cursor < hasta:
        cursor = date.fromordinal(cursor.toordinal() + 1)
        if cursor.weekday() < 5:
            dias += 1
    return dias


def _frecuencia_publicacion(puntos: list[tuple[str, float]]) -> str | None:
    """Deduce si la serie publica los siete días o solo en días hábiles.

    Se deduce del histórico y no de una tabla fija por serie: si FRED cambia el
    calendario de una serie, el campo lo refleja en vez de mentir. `DFF` (tasa
    efectiva de fondos federales) trae sábados y domingos porque es un promedio
    diario; las yields y los TIPS, no.

    Devuelve `None` cuando la ventana observada no abarca un fin de semana completo:
    ahí la ausencia de sábados no distingue nada, porque tampoco los habría habido.
    Lo que importa es el rango de fechas y no la cantidad de puntos.
    """
    if len(puntos) < 2:
        return None
    try:
        recientes = [date.fromisoformat(f) for f, _ in puntos[-14:]]
    except ValueError:
        return None
    if (recientes[-1] - recientes[0]).days < 7:
        return None
    return "diaria" if any(f.weekday() >= 5 for f in recientes) else "dias_habiles"


def _construir_serie(
    codigo: str, bloque: dict[str, Any], hoy: date
) -> dict[str, Any]:
    """Arma la respuesta de una serie: nivel, fecha del dato, deltas y rezago."""
    historico = bloque.get("historico") or {}
    puntos = _serie_cronologica(historico)
    status = bloque.get("status", "DESCONOCIDO")

    salida: dict[str, Any] = {
        "codigo": codigo,
        "nombre": bloque.get("nombre"),
        "unidad": bloque.get("unidad", "porcentaje"),
        "status": status,
    }

    if not puntos:
        salida.update({
            "nivel_pct": None,
            "fecha_dato": None,
            "delta_1d_bps": None,
            "delta_5d_bps": None,
            "rezago_dias_habiles": None,
            "nota": "La serie no trae ningún punto con valor. Ejecutar pipeline_ingesta.py.",
        })
        return salida

    fecha_dato, nivel = puntos[-1]

    # Con la serie marcada como fallida los deltas van nulos, aunque haya puntos
    # para calcularlos: serían la variación entre dos datos viejos, y una cifra como
    # "+5 bps" viaja sola con facilidad hasta una pieza de cliente. El nivel y la
    # fecha sí se informan, porque no engañan: dicen de cuándo son.
    if status != "OK":
        delta_1d = delta_5d = None
        base_1d = base_5d = None
    else:
        delta_1d, base_1d = _delta_bps(puntos, 1)
        delta_5d, base_5d = _delta_bps(puntos, 5)

    try:
        rezago = _dias_habiles_entre(date.fromisoformat(fecha_dato), hoy)
    except ValueError:
        rezago = None

    salida.update({
        "nivel_pct": round(nivel, 2),
        "fecha_dato": fecha_dato,
        "delta_1d_bps": delta_1d,
        "fecha_base_1d": base_1d,
        "delta_5d_bps": delta_5d,
        "fecha_base_5d": base_5d,
        "frecuencia_publicacion": _frecuencia_publicacion(puntos),
        "puntos_disponibles": len(puntos),
        "rezago_dias_habiles": rezago,
    })

    if status != "OK":
        salida["nota"] = (
            f"El extractor marcó esta serie como '{status}', así que los deltas van "
            "nulos: se calcularían sobre datos que no se pudieron refrescar. El nivel "
            f"es el del {fecha_dato}. Ejecutar pipeline_ingesta.py."
        )
    elif rezago is not None and rezago > REZAGO_HABIL_ESPERADO:
        salida["nota"] = (
            f"El último dato es del {fecha_dato}, {rezago} días hábiles atrás. FRED "
            f"publica con {REZAGO_HABIL_ESPERADO} día hábil de rezago, así que "
            "conviene correr pipeline_ingesta.py antes de citar la cifra."
        )

    return salida


def _construir_spread(
    dgs2: dict[str, Any], dgs10: dict[str, Any]
) -> dict[str, Any]:
    """Pendiente 2s10s (DGS10 - DGS2) en nivel y en deltas.

    Se calcula sobre las fechas COMUNES a las dos series: restar el último valor de
    cada una por separado mezclaría días distintos si una viene con más rezago que la
    otra, y la pendiente de la curva es justamente una comparación entre tramos.
    """
    puntos_2 = dict(_serie_cronologica(dgs2.get("historico") or {}))
    puntos_10 = dict(_serie_cronologica(dgs10.get("historico") or {}))
    fechas = sorted(set(puntos_2) & set(puntos_10))

    if not fechas:
        return {
            "nivel_pct": None,
            "fecha_dato": None,
            "delta_1d_bps": None,
            "delta_5d_bps": None,
            "nota": "Sin fechas comunes entre DGS2 y DGS10.",
        }

    serie = [(f, puntos_10[f] - puntos_2[f]) for f in fechas]
    delta_1d, base_1d = _delta_bps(serie, 1)
    delta_5d, base_5d = _delta_bps(serie, 5)

    return {
        "descripcion": "Pendiente de la curva: rendimiento a 10 años menos el de 2 años",
        "nivel_pct": round(serie[-1][1], 2),
        "fecha_dato": serie[-1][0],
        "delta_1d_bps": delta_1d,
        "fecha_base_1d": base_1d,
        "delta_5d_bps": delta_5d,
        "fecha_base_5d": base_5d,
        "invertida": serie[-1][1] < 0,
    }


def cargar_curva_tasas(
    serie: str = "ALL",
    archivo: Path | None = None,
    config_path: Path | None = None,
    now_dt: datetime | None = None,
) -> dict[str, Any]:
    """Curva soberana de EE.UU. con niveles, deltas en bps, procedencia y frescura.

    Contrato de error del MCP: `SERIE_NO_DISPONIBLE`, `STALE_DATA` o `READ_ERROR`.
    Nunca array vacío ni None silencioso.
    """
    pedida = (serie or "ALL").upper().strip()
    if pedida != "ALL" and pedida not in SERIES_VALIDAS:
        return {
            "error": "SERIE_NO_DISPONIBLE",
            "message": (
                f"Serie '{serie}' no está en el archivo de curva. "
                f"Opciones: ALL, {', '.join(SERIES_VALIDAS)}."
            ),
        }

    ruta = archivo or ARCHIVO_DEFAULT
    if not ruta.exists():
        return {
            "error": "STALE_DATA",
            "message": (
                f"No existe {ruta.name}. Ejecutar previamente "
                "python .agents/skills/ecosistema-datos-macro/scripts/pipeline_ingesta.py"
            ),
        }

    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"error": "READ_ERROR", "message": f"Error leyendo la curva: {exc}"}

    as_of = datos.get("as_of")
    cfg = cargar_config_staleness(config_path)
    es_fresco, horas, umbral, razon = validar_staleness(as_of, cfg, now_dt=now_dt)

    if razon == "MALFORMED_DATE":
        return {
            "error": "READ_ERROR",
            "message": f"Campo 'as_of' malformado o ilegible: {as_of}",
        }

    if not es_fresco:
        return {
            "error": "STALE_DATA",
            "as_of": as_of,
            "antiguedad_horas": round(horas, 1),
            "umbral_horas": round(umbral, 1),
            "message": (
                f"El archivo de curva tiene {horas:.1f}h de antigüedad (umbral "
                f"{umbral:.1f}h). Ejecutar previamente pipeline_ingesta.py."
            ),
        }

    yields = datos.get("curva_rendimientos_yields") or {}
    if not yields:
        return {
            "error": "READ_ERROR",
            "message": "El archivo no trae el bloque 'curva_rendimientos_yields'.",
        }

    ahora = now_dt or datetime.now(timezone.utc)
    hoy = ahora.date()

    # Procedencia explícita: la skill ecosistema-datos-macro exige soberanía de
    # fuente, y `tesoro_status` dice si el Tesoro respondió o si la cifra viene del
    # fallback de FRED. Un número sin decir de dónde salió no es auditable, y la
    # sección "05. Fuentes Consultadas" del PDF institucional tiene que citarlo.
    tesoro_status = datos.get("tesoro_status")
    procedencia = {
        "fuente_tesoro": datos.get("fuente_tesoro"),
        "fuente_fed": datos.get("fuente_fed"),
        "tesoro_status": tesoro_status,
    }
    if tesoro_status and tesoro_status != "OK":
        procedencia["nota"] = (
            "El Tesoro (Fiscal Data) no respondió en la última ingesta, así que los "
            "rendimientos vienen de FRED. La skill ecosistema-datos-macro acepta FRED "
            "como fuente oficial diaria de EE.UU., pero hay que citarla como tal."
        )

    respuesta: dict[str, Any] = {
        "as_of": as_of,
        "antiguedad_horas": round(horas, 1),
        "procedencia": procedencia,
        "series": {},
    }

    codigos = SERIES_VALIDAS if pedida == "ALL" else (pedida,)
    for codigo in codigos:
        bloque = yields.get(codigo)
        if bloque is None:
            if pedida != "ALL":
                return {
                    "error": "SERIE_NO_DISPONIBLE",
                    "message": (
                        f"La serie '{codigo}' no está en el archivo. Series presentes: "
                        f"{', '.join(sorted(yields))}."
                    ),
                }
            continue
        respuesta["series"][codigo] = _construir_serie(codigo, bloque, hoy)

    # El spread solo tiene sentido con las dos patas, así que se calcula cuando se
    # piden todas (o cuando se pide una de las dos, como contexto de esa pata).
    if pedida in ("ALL", "DGS2", "DGS10") and "DGS2" in yields and "DGS10" in yields:
        respuesta["spread_2s10s"] = _construir_spread(yields["DGS2"], yields["DGS10"])

    return respuesta
