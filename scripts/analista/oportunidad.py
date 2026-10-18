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
    # Cómo se activa una entrada pendiente: "retesteo" (el precio vuelve al nivel y lo respeta,
    # como el borde del rango) o "quiebre" (una vela 4H cierra al otro lado del nivel).
    condicion: str | None = None

    @property
    def simulable(self) -> bool:
        return self.motivo is None

    def a_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sin(lectura: Lectura, motivo: str) -> Escenario:
    """El motivo lo lee el cliente (correo y /seguimiento): en su idioma, sin jerga interna
    (director, 2026-10-12). Cierra una frase que empieza con «Sin simulación esta semana:»."""
    return Escenario(lectura.ticker, lectura.estado, "", None, None, None, False, None, motivo)


def bordes_rango(lectura: Lectura) -> tuple[float, float]:
    """(superior, inferior) de las líneas `rango`, por su valor en la última vela."""
    valores = [x.valor_actual for x in lectura.lineas if x.rol == "rango"]
    if len(valores) < 2:
        raise ValueError(f"{lectura.ticker}: el rango no trae sus dos bordes")
    return max(valores), min(valores)


def _redondeo(valor: float, digits: int) -> float:
    return math.floor(valor * 10 ** digits + 0.5) / 10 ** digits


def _condicional(lectura: Lectura, atr: float, digits: int) -> Escenario:
    """La simulación cuando no hay una entrada a precio de hoy: se activa en el nivel a vigilar.

    La pieza es para que el ejecutivo invite a operar, así que nunca sale sin simulación por
    una lectura incómoda (director, 2026-10-12): sale condicionada. Si el precio ya está del
    lado de la dirección, la entrada es el retesteo del nivel; si no, el quiebre con cierre de
    vela 4H. El stop queda media volatilidad 4H al otro lado: el horizontal es una zona.
    """
    nivel = lectura.vigilar.precio
    if lectura.direccion in ("ALCISTA", "BAJISTA"):
        direccion = lectura.direccion
    else:  # sin dirección: el quiebre del nivel hacia donde no está el precio
        direccion = "ALCISTA" if lectura.precio < nivel else "BAJISTA"
    signo = 1 if direccion == "ALCISTA" else -1
    condicion = "retesteo" if (lectura.precio - nivel) * signo > 0 else "quiebre"
    entrada = _redondeo(nivel, digits)
    stop = _redondeo(nivel - signo * PARAMETROS.tolerancia_horizontal_atr * atr, digits)
    objetivo = _redondeo(entrada + signo * MULTIPLO * abs(entrada - stop), digits)
    atr_d1 = float(lectura.metricas.get("atr_d1") or 0.0)
    dias = round(abs(objetivo - lectura.precio) / atr_d1, 1) if atr_d1 else None
    return Escenario(lectura.ticker, lectura.estado, direccion, entrada, stop, objetivo, True, dias, None,
                     condicion)


def escenario(lectura: Lectura, digits: int) -> Escenario:
    atr = float(lectura.metricas.get("atr") or 0.0)
    atr_d1 = float(lectura.metricas.get("atr_d1") or 0.0)
    if atr <= 0:
        return _sin(lectura, "no se pudo medir cuánto se mueve el activo para dejar el stop con margen")
    if lectura.estado == "RANGO":
        superior, inferior = bordes_rango(lectura)
        arriba = abs(lectura.vigilar.precio - superior) <= abs(lectura.vigilar.precio - inferior)
        entrada = superior if arriba else inferior
        signo = -1 if arriba else 1  # falso quiebre: desde el borde hacia adentro
        stop = entrada - signo * PARAMETROS.tolerancia_horizontal_atr * atr
        direccion, pendiente, condicion = ("BAJISTA" if arriba else "ALCISTA"), True, "retesteo"
    elif (lectura.estado in SIMULAN and lectura.invalidacion is not None
          and lectura.direccion in ("ALCISTA", "BAJISTA")):
        entrada, stop = lectura.precio, lectura.invalidacion.precio
        signo = 1 if lectura.direccion == "ALCISTA" else -1
        direccion, pendiente, condicion = lectura.direccion, False, None
        if (entrada - stop) * signo <= 0:  # el precio ya pasó la invalidación
            return _condicional(lectura, atr, digits)
    else:  # en prueba, sin invalidación, sin dirección u otro estado
        return _condicional(lectura, atr, digits)

    entrada, stop = _redondeo(entrada, digits), _redondeo(stop, digits)
    riesgo = abs(entrada - stop)
    if riesgo < PARAMETROS.tolerancia_toque_atr * atr:  # pegado al nivel: el stop quedaría en el ruido
        return _condicional(lectura, atr, digits)
    objetivo = _redondeo(entrada + signo * MULTIPLO * riesgo, digits)
    dias = round(abs(objetivo - lectura.precio) / atr_d1, 1) if atr_d1 else None
    return Escenario(lectura.ticker, lectura.estado, direccion, entrada, stop, objetivo, pendiente, dias, None,
                     condicion)


def texto_condicion(esc: dict[str, Any], entrada: str) -> str | None:
    """Cuándo se activa la simulación, en el idioma del cliente (None si entra a precio de hoy)."""
    if not esc.get("entrada_pendiente"):
        return None
    alcista = esc["direccion"] == "ALCISTA"
    if esc.get("condicion") == "quiebre":
        return f"Se activa si una vela de 4 horas cierra {'sobre' if alcista else 'bajo'} {entrada}."
    if esc.get("estado") == "RANGO" or esc.get("condicion") is None:
        return f"Se activa si el precio llega a {entrada}, el borde del rango, y lo respeta."
    return f"Se activa si el precio vuelve a {entrada} y lo respeta."


MOTIVO_SIN_CONTRATO = "no tenemos los datos de la cuenta para calcular el tamaño de la operación en este activo"


def motivo_sin_simulacion(activo: dict[str, Any]) -> str | None:
    """Por qué un activo de la foto no tiene niveles de simulación (None si los tiene).

    Solo pasa sin volatilidad medida. Sin contrato los niveles existen igual: lo que falta es
    el volumen, y eso lo ve el ejecutivo en su panel (`sin_contrato`), no el cliente."""
    return activo["escenario"]["motivo"]


def sin_contrato(activo: dict[str, Any]) -> bool:
    return not activo.get("contrato")


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
