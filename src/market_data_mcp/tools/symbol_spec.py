"""Tool get_symbol_spec — especificaciones de contrato y sesiones de trading (#104).

Responde de forma determinista "¿opera el activo X en la fecha Y, y en qué
horario (hora Chile)?", cruzando tres señales complementarias: el patrón
semanal de sesiones que reporta MT5, el calendario de feriados versionado
(`config/feriados_bolsa.json`) y el `trade_mode` en tiempo real del símbolo.

Arquitectura hexagonal: este módulo (service/tool) nunca importa `MetaTrader5`
directamente — solo consume las funciones I/O de `market_data_mcp.mt5_client`
(`get_symbol_info`, `get_session`), que hacen el import perezoso. Así el
módulo es importable y testeable sin el paquete `MetaTrader5` instalado.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, time as dtime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastmcp import FastMCP

from market_data_mcp.catalog import VALID_TICKERS as _VALID_TICKERS

_SANTIAGO = ZoneInfo("America/Santiago")

# config/feriados_bolsa.json está en la raíz del repo (4 niveles arriba de este archivo).
_FERIADOS_PATH = Path(__file__).resolve().parent.parent.parent.parent / "config" / "feriados_bolsa.json"

# Máximo de ventanas de sesión a inspeccionar por día (salvaguarda anti loop
# infinito ante brokers/mocks mal comportados; ningún símbolo real reporta
# tantas ventanas en un día).
_MAX_VENTANAS_POR_DIA = 10

# Días de la semana en español, sin tilde, en el orden fijo de R3.1.
# Índice = datetime.weekday() de Python (0=lunes ... 6=domingo).
_DIAS_ES: tuple[str, ...] = (
    "lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo",
)

# Q1 (design.md §5.1): mapeo SYMBOL_TRADE_MODE_* -> string legible, por entero
# literal (no se importan las constantes de MetaTrader5, para que este módulo
# sea importable sin el paquete). Valores fuera de {0..4}: "UNKNOWN".
_TRADE_MODE_MAP: dict[int, str] = {
    0: "DISABLED",
    1: "LONGONLY",
    2: "SHORTONLY",
    3: "CLOSEONLY",
    4: "FULL",
}

# Q3 (design.md §5.3): mapeo ticker -> exchange cubierto por el calendario de
# feriados. D-GATE-1 aceptado: 3 índices US + 13 acciones = 16 tickers -> NYSE.
# Vive aquí (no en config/activos.json) para no acoplar el catálogo de activos
# a la lógica de feriados de esta tool.
_TICKER_EXCHANGE: dict[str, str] = {
    "US100.spot": "NYSE",
    "US500.spot": "NYSE",
    "US30.spot": "NYSE",
    "#AAPL": "NYSE",
    "#MSFT": "NYSE",
    "#NVDA": "NYSE",
    "#AMZN": "NYSE",
    "#AMD": "NYSE",
    "#JPM": "NYSE",
    "#BAC": "NYSE",
    "#GS": "NYSE",
    "#MS": "NYSE",
    "#BA": "NYSE",
    "#CAT": "NYSE",
    "#GE": "NYSE",
    "#DE": "NYSE",
}

_RE_FECHA_ISO = re.compile(r"\d{4}-\d{2}-\d{2}")

# R11: limitación documentada (no bug) — se reutiliza en el docstring de la
# tool y queda accesible como constante para poder verificarla en tests.
_DOCSTRING_LIMITACION = (
    "Limitación conocida (no es un bug): USDCLP, XAUUSD y WTI.spot no tienen "
    "calendario de feriados en esta iteración (no mapean a ningún exchange "
    "cubierto). Para ellos, `opera` con `fecha` futura se decide solo con el "
    "patrón semanal de MT5 (y, si `fecha` es hoy, con `trade_mode`); "
    "`motivo` nunca es \"feriado_bolsa\" y `calendario_feriados_fuente` es null."
)


def _parsear_fecha_iso(fecha: Any) -> date | None:
    """Parsea `fecha` como ISO `YYYY-MM-DD` estricto. Retorna `None` si no es válida.

    Rechaza formatos alternativos (`DD-MM-YYYY`), fechas de calendario
    inexistentes (`2026-02-30`) y valores que no son `str` — sin lanzar
    excepciones (R7/R8: se valida antes de tocar MT5).
    """
    if not isinstance(fecha, str) or not _RE_FECHA_ISO.fullmatch(fecha):
        return None
    try:
        return date.fromisoformat(fecha)
    except ValueError:
        return None


def _cargar_feriados() -> dict[str, list[str]]:
    """Carga `config/feriados_bolsa.json` (sin la clave `_meta`)."""
    if not _FERIADOS_PATH.exists():
        return {}
    data = json.loads(_FERIADOS_PATH.read_text(encoding="utf-8"))
    return {clave: valor for clave, valor in data.items() if clave != "_meta"}


def _offset_servidor_minutos(info: Any) -> int:
    """Deriva el offset del servidor MT5 respecto a UTC, en minutos.

    Compara la hora del servidor (`info.time`, epoch de la última cotización,
    en hora "de pared" del broker) contra la hora real UTC en el momento de
    la consulta, redondeado únicamente a resolución de minuto entero (RNF2 —
    sin offsets fijos hardcodeados, se deriva en runtime). Se expone **crudo**
    (sin ajustar a una grilla de 15/30/60 minutos) para preservar trazabilidad
    del clock drift real del servidor del broker — design.md §6.1.
    """
    server_epoch = getattr(info, "time", None)
    if not server_epoch:
        return 0
    server_naive = datetime.fromtimestamp(server_epoch, tz=timezone.utc).replace(tzinfo=None)
    ahora_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    delta_minutos = (server_naive - ahora_utc).total_seconds() / 60
    return round(delta_minutos)


def _server_datetime(info: Any) -> datetime:
    """Hora del servidor MT5 (naive, "de pared") en el momento de la consulta."""
    server_epoch = getattr(info, "time", None)
    if not server_epoch:
        return datetime.now(timezone.utc).replace(tzinfo=None)
    return datetime.fromtimestamp(server_epoch, tz=timezone.utc).replace(tzinfo=None)


def _fecha_referencia_dia(python_weekday: int, hoy: date) -> date:
    """Próxima fecha (>= hoy) que cae en `python_weekday` (0=lunes...6=domingo).

    Ancla la conversión de cada día de `sesiones_semana` a una fecha real
    concreta, para que `zoneinfo` resuelva el offset de Chile (DST) de forma
    correcta para ese día específico (design.md §6).
    """
    delta = (python_weekday - hoy.weekday()) % 7
    return hoy + timedelta(days=delta)


def _hora_str(hora: dtime, offset_minutes: int, fecha_referencia: date) -> str:
    """Convierte una hora "de pared" del servidor a `"HH:MM"` en America/Santiago.

    Ancla la hora a `fecha_referencia` con un huso fijo `offset_minutes`
    (offset del servidor respecto a UTC) y convierte con `zoneinfo` — nunca
    con offsets fijos hardcodeados (RNF2).
    """
    servidor_tz = timezone(timedelta(minutes=offset_minutes))
    server_dt = datetime.combine(fecha_referencia, hora, tzinfo=servidor_tz)
    return server_dt.astimezone(_SANTIAGO).strftime("%H:%M")


def _llamar_sesion(get_session_fn, ticker: str, mt5_dow: int, index: int, tipo: str):
    """Envoltorio defensivo sobre `get_session`: cualquier excepción que no sea
    de disponibilidad de MT5 se trata como "sin ventana" para ese índice/tipo."""
    try:
        return get_session_fn(ticker, mt5_dow, index, tipo)
    except (ImportError, ModuleNotFoundError):
        raise
    except Exception:
        return None


def _ventana_dict(quote, trade, offset_minutes: int, fecha_referencia: date) -> dict[str, list[str]]:
    """Arma `{"quote": [apertura, cierre], "trade": [apertura, cierre]}` (R3.1).

    Si el broker solo configuró uno de los dos (quote o trade) para un índice
    dado, se usa el disponible para ambas claves — nunca se deja una clave sin
    su par `[apertura, cierre]`.
    """
    quote = quote or trade
    trade = trade or quote
    return {
        "quote": [
            _hora_str(quote[0], offset_minutes, fecha_referencia),
            _hora_str(quote[1], offset_minutes, fecha_referencia),
        ],
        "trade": [
            _hora_str(trade[0], offset_minutes, fecha_referencia),
            _hora_str(trade[1], offset_minutes, fecha_referencia),
        ],
    }


def _construir_sesiones_semana(
    ticker: str, get_session_fn, offset_minutes: int, fecha_ancla: date,
) -> dict[str, list[dict[str, list[str]]]] | None:
    """Arma `sesiones_semana` (R3.1) iterando las 7 claves de día y, por día,
    las ventanas de sesión (índice 0, 1, 2, ... hasta que MT5 no reporte más).

    `fecha_ancla` es la fecha real usada para resolver el offset de Chile
    (DST) de cada día de la semana (design.md §6): sin `fecha` en la consulta
    (R3) es "hoy"; con `fecha` (R4) es la fecha consultada, para que el día de
    semana que coincide con `fecha_ancla` quede anclado exactamente a esa
    fecha real (crítico para `horario_chile`).

    Retorna `None` (sentinela de `SESSION_UNAVAILABLE`) si el broker no tiene
    NINGUNA ventana configurada para el ticker en ningún día — distinto de un
    día puntual sin sesión (fin de semana típico), que es un resultado válido
    (lista vacía) y no un error.
    """
    resultado: dict[str, list[dict[str, list[str]]]] = {}
    alguna_ventana = False

    for python_weekday, dia in enumerate(_DIAS_ES):
        mt5_dow = (python_weekday + 1) % 7
        fecha_referencia = _fecha_referencia_dia(python_weekday, fecha_ancla)

        ventanas: list[dict[str, list[str]]] = []
        for index in range(_MAX_VENTANAS_POR_DIA):
            quote = _llamar_sesion(get_session_fn, ticker, mt5_dow, index, "quote")
            trade = _llamar_sesion(get_session_fn, ticker, mt5_dow, index, "trade")
            if quote is None and trade is None:
                break
            ventanas.append(_ventana_dict(quote, trade, offset_minutes, fecha_referencia))

        if ventanas:
            alguna_ventana = True
        resultado[dia] = ventanas

    if not alguna_ventana:
        return None
    return resultado


def _resolver_opera(
    ticker: str,
    fecha: date,
    sesiones_semana: dict[str, list[dict[str, list[str]]]],
    trade_mode: str,
    hoy_santiago: date,
) -> dict[str, Any]:
    """Algoritmo determinista "feriado primero" (design.md §4, R4.1).

    Orden: (1) feriado versionado (máxima prioridad, gana sobre el patrón
    semanal — CB-9); (2) sesión vacía ese día de semana (fin de semana vs.
    día hábil sin sesión); (3) `trade_mode` en vivo, solo si `fecha` es hoy;
    (4) si ninguna señal anterior determina `false` -> opera.
    """
    exchange = _TICKER_EXCHANGE.get(ticker)
    calendario_feriados_fuente = (
        f"config/feriados_bolsa.json ({exchange})" if exchange else None
    )
    dia = _DIAS_ES[fecha.weekday()]
    feriados_exchange = _cargar_feriados().get(exchange, []) if exchange else []

    opera = True
    motivo: str | None = None

    if exchange and fecha.isoformat() in feriados_exchange:
        opera = False
        motivo = "feriado_bolsa"
    elif not sesiones_semana[dia]:
        opera = False
        motivo = "fin_de_semana" if dia in ("sabado", "domingo") else "fuera_de_sesion_recurrente"
    elif fecha == hoy_santiago and trade_mode == "DISABLED":
        opera = False
        motivo = "trade_mode_disabled"

    horario_chile: dict[str, str] | None = None
    if opera:
        primera_ventana = sesiones_semana[dia][0]
        horario_chile = {
            "apertura": primera_ventana["trade"][0],
            "cierre": primera_ventana["trade"][1],
        }

    return {
        "fecha_consultada": fecha.isoformat(),
        "opera": opera,
        "motivo": motivo,
        "horario_chile": horario_chile,
        "calendario_feriados_fuente": calendario_feriados_fuente,
    }


def register(mcp: FastMCP) -> None:

    @mcp.tool
    def get_symbol_spec(ticker: str, fecha: str | None = None) -> dict[str, Any]:
        """Especificaciones de contrato y sesiones de trading de un ticker.

        Responde de forma determinista "¿opera el activo X en la fecha Y, y en
        qué horario (hora Chile)?", cruzando el patrón semanal de sesiones de
        MT5, el calendario de feriados versionado (`config/feriados_bolsa.json`,
        cobertura NYSE: 3 índices US + 13 acciones) y el `trade_mode` en tiempo
        real del símbolo.

        Args:
            ticker: símbolo MT5 del catálogo (ej: XAUUSD, USDCLP, US100.spot, #AAPL).
            fecha: fecha ISO `YYYY-MM-DD` a consultar, o `None` para solo
                specs estáticas + patrón semanal (sin resolver `opera`).

        Returns:
            Sin `fecha`: dict con `ticker`, `trade_mode`, `digits`, `volume_min`,
            `volume_step`, `contract_size`, `server_time`,
            `server_utc_offset_minutes`, `sesiones_semana` (7 días en español,
            0/1/N ventanas c/u, hora Chile) y `fuente`.
            Con `fecha`: además `fecha_consultada`, `opera`, `motivo`,
            `horario_chile` y `calendario_feriados_fuente`.
            O `{"error": "CÓDIGO", "message": "..."}`: `TICKER_NOT_FOUND`,
            `INVALID_FECHA`, `MT5_UNAVAILABLE`, `SESSION_UNAVAILABLE`.

        Limitación conocida (no es un bug, R11): USDCLP, XAUUSD y WTI.spot no
        tienen calendario de feriados en esta iteración (no mapean a ningún
        exchange cubierto). Para ellos, `opera` con `fecha` futura se decide
        solo con el patrón semanal de MT5 (y, si `fecha` es hoy, con
        `trade_mode`); `motivo` nunca es "feriado_bolsa" y
        `calendario_feriados_fuente` es `null`.
        """
        if ticker not in _VALID_TICKERS:
            return {
                "error": "TICKER_NOT_FOUND",
                "message": (
                    f"'{ticker}' no está en el catálogo de activos. "
                    f"Tickers válidos: {', '.join(sorted(_VALID_TICKERS.keys()))}"
                ),
            }

        fecha_dt: date | None = None
        if fecha is not None:
            fecha_dt = _parsear_fecha_iso(fecha)
            if fecha_dt is None:
                return {
                    "error": "INVALID_FECHA",
                    "message": (
                        f"'{fecha}' no es una fecha ISO válida (formato esperado: "
                        f"YYYY-MM-DD, ej. 2026-07-03)."
                    ),
                }

        try:
            from market_data_mcp.mt5_client import get_session, get_symbol_info
        except ImportError:
            return {
                "error": "MT5_UNAVAILABLE",
                "message": "No se pudo importar mt5_client. Verificar que MT5 esté iniciado.",
            }

        try:
            info = get_symbol_info(ticker)
        except (ImportError, ModuleNotFoundError):
            return {
                "error": "MT5_UNAVAILABLE",
                "message": "MetaTrader5 no está instalado en este entorno. El MCP requiere MT5 en la máquina del director.",
            }
        except Exception as exc:
            return {
                "error": "MT5_UNAVAILABLE",
                "message": f"Error al obtener specs de {ticker}: {exc}",
            }

        if info is None:
            return {
                "error": "MT5_UNAVAILABLE",
                "message": f"MT5 no retornó specs para '{ticker}'. Verificar terminal/conexión.",
            }

        offset_minutes = _offset_servidor_minutos(info)
        hoy_santiago = datetime.now(_SANTIAGO).date()
        fecha_ancla = fecha_dt if fecha_dt is not None else hoy_santiago

        try:
            sesiones_semana = _construir_sesiones_semana(ticker, get_session, offset_minutes, fecha_ancla)
        except (ImportError, ModuleNotFoundError):
            return {
                "error": "MT5_UNAVAILABLE",
                "message": "MetaTrader5 no está instalado en este entorno. El MCP requiere MT5 en la máquina del director.",
            }

        if sesiones_semana is None:
            return {
                "error": "SESSION_UNAVAILABLE",
                "message": f"MT5 no reporta sesiones configuradas para '{ticker}'.",
            }

        trade_mode = _TRADE_MODE_MAP.get(info.trade_mode, "UNKNOWN")

        payload: dict[str, Any] = {
            "ticker": ticker,
            "trade_mode": trade_mode,
            "digits": info.digits,
            "volume_min": info.volume_min,
            "volume_step": info.volume_step,
            "contract_size": info.trade_contract_size,
            "server_time": _server_datetime(info).strftime("%Y-%m-%d %H:%M:%S"),
            "server_utc_offset_minutes": offset_minutes,
            "sesiones_semana": sesiones_semana,
            "fuente": "mt5",
        }

        if fecha_dt is not None:
            payload.update(
                _resolver_opera(ticker, fecha_dt, sesiones_semana, trade_mode, hoy_santiago)
            )

        return payload
