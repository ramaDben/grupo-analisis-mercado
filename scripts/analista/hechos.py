"""Lo que pasa hoy con los drivers de un activo, medido por Python antes de llamar a agy.

La corrida del oro del 2026-10-17 salió genérica porque agy solo recibía los nombres de los
drivers del catálogo y el prompt le mandaba explicarlos como mecanismo condicional (spec
2026-10-17 §1). Acá se mide cada driver medible (Dollar Index, tasa real, bono a 10 años, tasa de
la Fed, cobre, petróleo) con su fecha, su cambio en 5 sesiones y su efecto sobre el activo.

Qué se mide y con qué signo lo dice `config/drivers.json` (la `correlacion` de cada driver), no
el código. El efecto y si acompaña nuestra lectura los calcula Python, como la discrepancia con
los bancos: un modelo tiende a alinearse con lo que lee. Un dato que no está se avisa y falta.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

from analista import RAIZ
from analista.agenda import dia_corto

DRIVERS = RAIZ / "config" / "drivers.json"
SESIONES = 5
# Bajo estos cambios a 5 sesiones el driver se dice «estable» y no se le atribuye efecto:
# puntos del DXY, puntos base de las tasas y fracción del precio en cobre y petróleo.
UMBRAL_ESTABLE = {"dxy": 0.15, "tasa_real": 3.0, "bono_10": 3.0, "fed": 3.0, "cobre": 0.005, "petroleo": 0.005}
RELATIVO = frozenset({"cobre", "petroleo"})
CLAVE_DRIVERS = {"XAUUSD": "XAU/USD", "USDCLP": "USD/CLP", "USDJPY": "USD/JPY", "EURUSD": "EUR/USD",
                 "USDCHF": "USD/CHF", "GBPUSD": "GBP/USD", "WTI.spot": "WTI", "US100.spot": "US100",
                 "XAGUSD": "XAG/USD", "BRENT.spot": "BRENT", "COPPER": "COPPER"}
MEDIBLE_DE_DRIVER = {"dollar_index": "dxy", "tasas_reales": "tasa_real", "rendimientos_treasury": "bono_10",
                     "decisiones_fed": "fed", "tasas_fed": "fed", "cobre": "cobre", "precios_energia": "petroleo"}
GENERALES = ("dxy", "bono_10")
SIMBOLOS = {"dxy": ("USDIDX", 3, "puntos"), "cobre": ("COPPER", 0, "dólares por tonelada"),
            "petroleo": ("WTI.spot", 3, "dólares por barril")}
CURVA = {"tasa_real": "DFII10", "bono_10": "DGS10", "fed": "DFF"}
NOMBRES = {"dxy": "Dollar Index (DXY)", "tasa_real": "Tasa real a 10 años de EE.UU. (TIPS)",
           "bono_10": "Bono del Tesoro a 10 años", "fed": "Tasa de la Fed (fondos federales)",
           "cobre": "Cobre", "petroleo": "Petróleo WTI"}
FUENTE_CURVA = "FRED (Reserva Federal de St. Louis)"
_DECISION_FED = re.compile(r"fed interest rate decision|fomc statement", re.IGNORECASE)


def signos(ticker: str, ruta: Path = DRIVERS) -> dict[str, int]:
    """Medible -> +1 (correlación directa), -1 (inversa) o 0 (sin signo declarado), en el orden del archivo.

    Un activo sin ficha en `drivers.json` recibe los generales sin signo: se describen, no se interpretan.
    """
    clave = CLAVE_DRIVERS.get(ticker)
    datos = json.loads(ruta.read_text(encoding="utf-8")) if clave else {}
    salida: dict[str, int] = {}
    for driver, info in (datos.get(clave) or {}).get("drivers", {}).items():
        medible = MEDIBLE_DE_DRIVER.get(driver)
        if medible and medible not in salida:
            c = str(info.get("correlacion", "")).lower()
            salida[medible] = 1 if c.startswith("directa") else -1 if c.startswith("inversa") else 0
    return salida or {m: 0 for m in GENERALES}


def _fmt(valor: float, digits: int) -> str:
    from pipeline_carrusel import formatear_precio

    return formatear_precio(valor, digits)


def _sentido(medible: str, cambio: float | None, base: float | None) -> str:
    if cambio is None:
        return "sin_dato"
    medida = abs(cambio) / abs(base) if medible in RELATIVO and base else abs(cambio)
    if medida < UMBRAL_ESTABLE[medible]:
        return "estable"
    return "subió" if cambio > 0 else "bajó"


def _de_serie(medible: str, puntos: list[tuple[date, float]], fuente: str, hoy: date) -> dict[str, Any] | None:
    _, digits, unidad = SIMBOLOS[medible]
    if len(puntos) < SESIONES + 1:
        return None
    (f0, v0), (_, v1), (_, v5) = puntos[-1], puntos[-2], puntos[-(SESIONES + 1)]
    return {"id": medible, "driver": NOMBRES[medible], "fecha": dia_corto(f0), "en_curso": f0 == hoy,
            "nivel": _fmt(v0, digits), "cambio_1d": _fmt(abs(v0 - v1), digits),
            "cambio_5d": _fmt(abs(v0 - v5), digits), "unidad_cambio": unidad,
            "sentido": _sentido(medible, v0 - v5, v5), "sentido_1d": _sentido(medible, v0 - v1, v1),
            "fuente": fuente}


def _pb(valor: float | None) -> str:
    # `None` es "no se pudo calcular", no "no se movió" (CLAUDE.md, get_curva_tasas).
    return "sin dato" if valor is None else f"{abs(float(valor)):.0f} pb"


def _de_curva(medible: str, curva: dict[str, Any] | None, eventos: list[dict[str, Any]]) -> dict[str, Any] | None:
    serie = ((curva or {}).get("series") or {}).get(CURVA[medible]) or {}
    if serie.get("status") != "OK" or serie.get("nivel_pct") is None or not serie.get("fecha_dato"):
        return None
    d1, d5 = serie.get("delta_1d_bps"), serie.get("delta_5d_bps")
    h = {"id": medible, "driver": NOMBRES[medible], "fecha": dia_corto(date.fromisoformat(serie["fecha_dato"])),
         "en_curso": False, "nivel": f"{float(serie['nivel_pct']):.2f}".replace(".", ",") + " por ciento",
         "cambio_1d": _pb(d1), "cambio_5d": _pb(d5), "unidad_cambio": "puntos base",
         "sentido": _sentido(medible, d5, None), "sentido_1d": _sentido(medible, d1, None), "fuente": FUENTE_CURVA}
    if medible == "fed":
        decision = next((e for e in eventos or [] if _DECISION_FED.search(str(e.get("fuente_nombre", "")))), None)
        h["proxima_decision"] = f"{decision['dia']} {decision['hora']}" if decision else None
    return h


def _de(el: str) -> str:
    return "del " + el[3:] if el.startswith("el ") else "de " + el


def _efecto(h: dict[str, Any], signo: int, el: str, direccion: str) -> dict[str, Any]:
    impacto = signo * {"subió": 1, "bajó": -1}.get(h["sentido"], 0)
    if not impacto:
        return {"efecto": None, "con_la_lectura": None}
    efecto = f"juega a favor del alza {_de(el)}" if impacto > 0 else f"juega a favor de la baja {_de(el)}"
    lectura = {"ALCISTA": 1, "BAJISTA": -1}.get(str(direccion).upper(), 0)
    con = None if not lectura else ("acompaña nuestra lectura" if lectura == impacto
                                    else "va en contra de nuestra lectura")
    return {"efecto": efecto, "con_la_lectura": con}


def medir(ticker: str, nombre: str, direccion: str, curva: dict[str, Any] | None, eventos: list[dict[str, Any]],
          leer_d1: Callable[[str, int], list[tuple[date, float]]], hoy: date,
          respaldo_dxy: Callable[[int], list[tuple[date, float]]] | None = None
          ) -> tuple[list[dict[str, Any]], list[str]]:
    """Los hechos del día del activo y los avisos de lo que no se pudo medir."""
    from analista import macro_seguimiento as mac

    el = mac._el(mac.CLAVE_DEL_ACTIVO.get(ticker, ""), nombre)
    hechos: list[dict[str, Any]] = []
    avisos: list[str] = []
    for medible, signo in signos(ticker).items():
        try:
            if medible in SIMBOLOS:
                simbolo = SIMBOLOS[medible][0]
                fuente = f"MT5 ({simbolo})"
                try:
                    puntos = leer_d1(simbolo, SESIONES + 2)
                except Exception:  # noqa: BLE001  con el terminal caído, el DXY todavía tiene respaldo
                    if medible != "dxy" or respaldo_dxy is None:
                        raise
                    puntos = []
                if len(puntos) < SESIONES + 1 and medible == "dxy" and respaldo_dxy is not None:
                    puntos, fuente = respaldo_dxy(SESIONES + 2), "ICE (DX-Y.NYB) vía yfinance"
                h = _de_serie(medible, puntos, fuente, hoy)
            else:
                h = _de_curva(medible, curva, eventos)
        except Exception as exc:  # noqa: BLE001  un driver que no se mide se avisa: no tumba la pieza
            avisos.append(f"no pude medir {NOMBRES[medible]} ({exc.__class__.__name__})")
            continue
        if h is None:
            avisos.append(f"sin dato de {NOMBRES[medible]}")
            continue
        h.update(_efecto(h, signo, el, direccion))
        hechos.append(h)
    return hechos, avisos


def leer_d1_mt5(simbolo: str, n: int) -> list[tuple[date, float]]:
    """Los últimos `n` cierres diarios del terminal, del más antiguo al más nuevo.

    MT5 entrega la hora del servidor empaquetada como timestamp: la fecha de la vela D1 es la del
    servidor, que es la de la sesión (CLAUDE.md, «Ojo con MT5»).
    """
    from market_data_mcp import mt5_client

    mt5_client.connect()
    import MetaTrader5 as mt5  # noqa: PLC0415

    mt5.symbol_select(simbolo, True)
    rates = mt5.copy_rates_from_pos(simbolo, mt5.TIMEFRAME_D1, 0, n)
    if rates is None or len(rates) == 0:
        return []
    return [(datetime.fromtimestamp(int(r["time"]), tz=timezone.utc).date(), float(r["close"])) for r in rates]
