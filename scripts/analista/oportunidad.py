"""La simulación de la pieza semanal: entrada, stop y objetivo 1:3 sobre la lectura.

El objetivo 1:3 NO es de la estrategia (la salida de Tori no tiene objetivo fijo): es la
simulación que el ejecutivo arma para su cliente, y por eso vive acá y no en el análisis
que firma el director (spec 2026-10-12-oportunidad-semanal §1). Todo nivel sale de la
`Lectura`; nada se calcula con indicadores.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

from analista import RAIZ
from estrategia.contrato import Lectura
from estrategia.tori.parametros import PARAMETROS

MULTIPLO = 3  # objetivo = 3 × riesgo (director, 2026-10-12; la gerencia pidió 1:5 y no cabe)
SIMULAN = {"TENDENCIA", "REBOTE", "RUPTURA"}
SIMULADOR_JS = RAIZ / "templates" / "oportunidad" / "simulador.js"


@dataclass(frozen=True)
class Escenario:
    ticker: str
    estado: str
    direccion: str  # de la simulación: ALCISTA o BAJISTA ("" sin simulación)
    entrada: float | None
    stop: float | None
    objetivo: float | None
    entrada_pendiente: bool  # rango: el precio todavía tiene que llegar al borde
    dias_objetivo: float | None  # a cuántos ATR D1 del precio está el objetivo
    motivo: str | None  # por qué no hay simulación; None si la hay

    @property
    def simulable(self) -> bool:
        return self.motivo is None

    def a_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sin(lectura: Lectura, motivo: str) -> Escenario:
    return Escenario(lectura.ticker, lectura.estado, "", None, None, None, False, None, motivo)


def bordes_rango(lectura: Lectura) -> tuple[float, float]:
    """(superior, inferior) de las líneas `rango`, por su valor en la última vela."""
    valores = [x.valor_actual for x in lectura.lineas if x.rol == "rango"]
    if len(valores) < 2:
        raise ValueError(f"{lectura.ticker}: el rango no trae sus dos bordes")
    return max(valores), min(valores)


def _redondeo(valor: float, digits: int) -> float:
    return math.floor(valor * 10 ** digits + 0.5) / 10 ** digits


def escenario(lectura: Lectura, digits: int) -> Escenario:
    atr = float(lectura.metricas.get("atr") or 0.0)
    atr_d1 = float(lectura.metricas.get("atr_d1") or 0.0)
    if lectura.estado == "PRUEBA":
        return _sin(lectura, "el precio está en prueba sobre una línea: se espera el cierre de la vela")
    if atr <= 0:
        return _sin(lectura, "la lectura no trae ATR del marco operativo")
    if lectura.estado == "RANGO":
        superior, inferior = bordes_rango(lectura)
        arriba = abs(lectura.vigilar.precio - superior) <= abs(lectura.vigilar.precio - inferior)
        entrada = superior if arriba else inferior
        signo = -1 if arriba else 1  # falso quiebre: desde el borde hacia adentro
        stop = entrada - signo * PARAMETROS.tolerancia_horizontal_atr * atr
        direccion, pendiente = ("BAJISTA" if arriba else "ALCISTA"), True
    elif lectura.estado in SIMULAN:
        if lectura.invalidacion is None:
            return _sin(lectura, "la lectura no trae nivel de invalidación")
        if lectura.direccion not in ("ALCISTA", "BAJISTA"):
            return _sin(lectura, "la lectura no tiene dirección")
        entrada, stop = lectura.precio, lectura.invalidacion.precio
        signo = 1 if lectura.direccion == "ALCISTA" else -1
        direccion, pendiente = lectura.direccion, False
        if (entrada - stop) * signo <= 0:
            return _sin(lectura, "el precio ya está del otro lado de la invalidación")
    else:
        return _sin(lectura, f"estado {lectura.estado} sin simulación")

    entrada, stop = _redondeo(entrada, digits), _redondeo(stop, digits)
    riesgo = abs(entrada - stop)
    if riesgo < PARAMETROS.tolerancia_toque_atr * atr:
        return _sin(lectura, "el precio está sobre la línea: el riesgo es menor que el ruido de una vela")
    objetivo = _redondeo(entrada + signo * MULTIPLO * riesgo, digits)
    dias = round(abs(objetivo - lectura.precio) / atr_d1, 1) if atr_d1 else None
    return Escenario(lectura.ticker, lectura.estado, direccion, entrada, stop, objetivo, pendiente, dias, None)


def _pesos(valor: float) -> int:
    """Mitad hacia arriba, como `Math.round` del panel: `round` de Python va al par."""
    return math.floor(valor + 0.5)


def _volumen(crudo: float, minimo: float, paso: float) -> tuple[float, bool]:
    if crudo < minimo:
        return minimo, True
    pasos = math.floor((crudo - minimo) / paso + 1e-9)
    return math.floor((minimo + pasos * paso) * 1e8 + 0.5) / 1e8, False


def _pct(valor: float, capital: float | None) -> float | None:
    return math.floor(valor / capital * 10000 + 0.5) / 100 if capital and capital > 0 else None


def simular(contrato: dict[str, Any], esc: dict[str, Any], perdida: float | None,
            capital: float | None = None) -> dict[str, Any] | None:
    """Lo que el panel calcula: volumen para la pérdida aceptable, y la ganancia 1:3.

    `contrato["clp_unidad"]` son los pesos que mueve 1,0 de precio con 1 lote
    (`order_calc_profit`). El panel repite este cálculo en `simulador.js`, y un test los compara.
    """
    if perdida is None or perdida <= 0:
        return None
    riesgo = abs(float(esc["entrada"]) - float(esc["stop"]))
    clp = float(contrato["clp_unidad"])
    if riesgo <= 0 or clp <= 0:
        return None
    vol, bajo = _volumen(perdida / (riesgo * clp), float(contrato["vol_min"]), float(contrato["vol_paso"]))
    p = _pesos(riesgo * clp * vol)
    g = MULTIPLO * p
    return {"volumen": vol, "perdida": p, "ganancia": g, "bajo_minimo": bajo,
            "perdida_pct": _pct(p, capital), "ganancia_pct": _pct(g, capital)}
