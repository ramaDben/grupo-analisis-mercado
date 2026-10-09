"""Foco técnico del día (`/oportunidad`): qué activo mirar hoy, elegido por una regla.

Lo piden los ejecutivos de ventas para un prospecto, y nadie en GI está inscrito
como asesor de inversión. Por eso lo elige una regla y no una persona, es el
mismo para todos los que lo piden a la misma hora, y algunos días no hay: el bot
lo dice en vez de rellenar. Spec: docs/superpowers/specs/2026-10-09-foco-tecnico-del-dia-design.md

Tres decisiones que no conviene revertir:

1. **No usa el `Score_GI` entero.** `factor_espacio` mide la distancia AL R1
   como objetivo y da 0 puntos cerca de él, pero en el plan el R1 es el gatillo:
   con el puntaje tal cual, el activo a punto de activarse saldría último. Y
   `factor_catalizador` suma puntos por un movimiento de tasas sin mirar hacia
   dónde empuja. El orden es técnico + momentum.
2. **Sin calendario no hay foco.** Sin él no se puede verificar que no venga un
   dato fuerte, y entregar a ciegas a minutos del empleo es lo que el gate evita.
3. **Una sola lectura del terminal por pedido.** Elegir con una y armar la pieza
   con otra puede encontrar el precio del otro lado de la EMA 50.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

AGREGADOS = ("US100.spot", "BRENT.spot")
CLASE_BASE = "forex_commodities"
CLASES_INDICE = {"indices"}
DISTANCIA_ARMADO_ATR = 1.0
VELAS_ACTIVACION = 2  # la ruptura en una de las 2 últimas velas cerradas
AVANCE_MAXIMO = 0.5  # fracción del recorrido típico ya hecha desde el gatillo
EDAD_TICK_MAXIMA_MIN = 15.0
VELAS_SERIE = 400  # alcanza para los 300 de los niveles más las 24 de la activación

_AVISO_CALENDARIO = "calendario no disponible"


# ───────────────────────────────────────────────────────────── resultados


@dataclass(frozen=True)
class PlanFoco:
    plan: dict[str, Any]
    velas_desde_ruptura: int | None  # 0 = la última vela cerrada; None = sin ruptura
    precio: float
    atr14: float


@dataclass(frozen=True)
class Elegido:
    activo: dict[str, Any]
    evaluacion: dict[str, Any]
    h1: dict[str, Any]
    d1: dict[str, Any]
    plan_foco: PlanFoco
    serie: Any


@dataclass(frozen=True)
class Seleccion:
    elegido: Elegido
    evaluados: int
    ahora: datetime


@dataclass(frozen=True)
class SinFoco:
    evaluados: int
    motivos: dict[str, int] = field(default_factory=dict)

    def texto(self) -> str:
        detalle = ", ".join(f"{n} {m}" for m, n in sorted(self.motivos.items(), key=lambda x: (-x[1], x[0])))
        return (f"El escáner no encontró una configuración clara entre los {self.evaluados} activos"
                + (f": {detalle}." if detalle else "."))


@dataclass(frozen=True)
class MercadoIlegible:
    motivo: str

    def texto(self) -> str:
        return f"No puedo leer el mercado ahora ({self.motivo}). Prueba en unos minutos."


# ───────────────────────────────────────────────────────────── reglas puras


def universo_ventas() -> list[dict[str, Any]]:
    """El forex y commodities que publica el carrusel, más el US100 y el Brent.

    Si un canal se apaga en `config/whatsapp_grupos.json`, ventas lo pierde igual
    que el carrusel, salvo los dos agregados a mano por decisión del director.
    """
    import screener_gi as sc

    todo = sc.cargar_universo(solo_renderizables=False)
    cubiertos, _ = sc.solo_canales_cubiertos(todo)
    base = [a for a in cubiertos if a["clase"] == CLASE_BASE]
    vistos = {a["ticker"] for a in base}
    return base + [a for a in todo if a["ticker"] in AGREGADOS and a["ticker"] not in vistos]


def indice_habilitado(activo: dict[str, Any], ahora: datetime) -> bool:
    """Un índice solo desde la apertura de índices de la agenda (10:00 Nueva York).

    La hora se convierte en el instante: el desfase con Chile se mueve dos veces
    al año, y una hora de Chile fija publicaría niveles de antes de la campana.
    """
    if activo.get("clase") not in CLASES_INDICE:
        return True
    import agenda_mercado as am

    return ahora >= am.instante(am.momento("apertura_indices"), ahora)


def calendario_caido(avisos: list[str]) -> bool:
    return any(a.startswith(_AVISO_CALENDARIO) for a in avisos)


def elegible(pf: PlanFoco) -> str | None:
    """None si el plan sirve para hoy; si no, el motivo en palabras del ejecutivo."""
    p = pf.plan
    if not p.get("hay_plan"):
        return "sin estructura a favor de la tendencia"
    n = p["niveles"]
    alcista = p["sesgo"] == "Alcista"
    if pf.velas_desde_ruptura is None:
        if abs(pf.precio - n["gatillo"]) > DISTANCIA_ARMADO_ATR * pf.atr14:
            return "lejos del gatillo"
        return None
    if str(p.get("estado", "")).startswith("Invalidado"):
        return "con el plan invalidado"
    if pf.velas_desde_ruptura >= VELAS_ACTIVACION:
        return "activados hace más de 2 horas"
    avance = (pf.precio - n["gatillo"]) if alcista else (n["gatillo"] - pf.precio)
    if avance >= AVANCE_MAXIMO * n["recorrido"]:
        return "con más de la mitad del recorrido hecho"
    return None


def _distancia(pf: PlanFoco) -> float:
    return abs(pf.precio - pf.plan["niveles"]["gatillo"]) / pf.atr14 if pf.atr14 else float("inf")


def _motivo_gate(texto: str) -> str:
    t = texto.lower()
    if t.startswith("feriado"):
        return "en feriado de su bolsa"
    if t.startswith("atr diario"):
        return "sin recorrido en el día"
    if t.startswith("blackout"):
        return "por un dato económico fuerte"
    if t.startswith(("niveles de respaldo", "la vela tipica")):
        return "con niveles muy estrechos o sin estructura"
    return "sin datos del terminal"


# ───────────────────────────────────────────────────────────── lectura


class AnalizadorMemo:
    """`analizar_activo` con memoria por pedido: una lectura por (ticker, marco)."""

    def __init__(self, analizador: Callable[[str, str], dict[str, Any]]):
        self._analizador = analizador
        self._lecturas: dict[tuple[str, str], dict[str, Any]] = {}

    def __call__(self, ticker: str, marco: str) -> dict[str, Any]:
        clave = (ticker, marco)
        if clave not in self._lecturas:
            self._lecturas[clave] = self._analizador(ticker, marco)
        return self._lecturas[clave]

    def con_error(self, ticker: str) -> bool:
        return any("error" in v for (t, _), v in self._lecturas.items() if t == ticker)


def _conectar() -> list[str]:
    import screener_gi as sc

    return sc._conectar_terminal()


def _contexto_macro(ahora: datetime):
    import screener_gi as sc

    return sc._contexto_macro(ahora)


def _analizador(ticker: str, marco: str) -> dict[str, Any]:
    from market_data_mcp.analisis import analizar_activo

    return analizar_activo(ticker, marco)


def _evaluar(activo, eventos, delta, ahora, analizador):
    import screener_gi as sc

    return sc.evaluar_activo(activo, eventos, delta, ahora, analizador=analizador)


def _edad_tick(ticker: str) -> float | None:
    """Minutos desde el último tick del símbolo, en hora del SERVIDOR.

    MT5 entrega hora de servidor empaquetada como UTC: compararla con el reloj
    local desplaza todo por el offset del broker. La referencia es el tick de
    BTCUSD, que cotiza todos los días a toda hora.
    """
    import MetaTrader5 as mt5  # noqa: PLC0415

    propio, ref = mt5.symbol_info_tick(ticker), mt5.symbol_info_tick("BTCUSD")
    if propio is None or ref is None:
        return None
    return max(0, max(ref.time, propio.time) - propio.time) / 60


def _serie(ticker: str):
    from market_data_mcp import mt5_client

    return mt5_client.get_rates(ticker, "H1", VELAS_SERIE).iloc[:-1].reset_index(drop=True)


def plan_foco(df, h1: dict[str, Any], activo: dict[str, Any], sesgo: str) -> PlanFoco:
    """El plan del `/activo`, sin estadística: el foco no la muestra y no la mide."""
    from analista import estadistica as est
    from analista import plan as plan_mod

    ind = est.indicadores(df)
    digits = int(activo["digits"])
    ruptura = est.ultima_ruptura(df, digits, sesgo == "Alcista", ind) if len(df) > est.VENTANA else None
    p = plan_mod.armar(h1, digits, sesgo, activo["nombre"], None, plan_mod.ultima_vela(df, ind),
                       ruptura[0] if ruptura else None)
    p.pop("estadistica", None)
    velas = (len(df) - 1 - ruptura[1]) if ruptura else None
    return PlanFoco(p, velas, float(df["close"].iat[-1]), float(h1["atr_14"]))


@dataclass
class LectoresFoco:
    conectar: Callable[[], list[str]] = _conectar
    contexto_macro: Callable[[datetime], tuple[list[dict[str, Any]], float | None, list[str]]] = _contexto_macro
    analizador: Callable[[str, str], dict[str, Any]] = _analizador
    evaluar: Callable[..., dict[str, Any]] = _evaluar
    edad_tick: Callable[[str], float | None] = _edad_tick
    serie: Callable[[str], Any] = _serie
    armar_plan: Callable[..., PlanFoco] = plan_foco


# ───────────────────────────────────────────────────────────── selección


def seleccionar(universo: list[dict[str, Any]], ahora: datetime,
                lec: LectoresFoco | None = None) -> Seleccion | SinFoco | MercadoIlegible:
    lec = lec or LectoresFoco()
    if lec.conectar():
        return MercadoIlegible("MetaTrader 5 no responde")
    eventos, delta, avisos = lec.contexto_macro(ahora)
    if calendario_caido(avisos):
        return MercadoIlegible("el calendario económico no responde y sin él no se puede "
                               "verificar que no venga un dato fuerte")

    memo = AnalizadorMemo(lec.analizador)
    motivos: Counter[str] = Counter()
    candidatos: list[tuple[tuple, Elegido]] = []
    leidos = errores = 0
    for a in universo:
        t = a["ticker"]
        if not indice_habilitado(a, ahora):
            motivos["índice antes de la apertura de Nueva York"] += 1
            continue
        edad = lec.edad_tick(t)
        if edad is None:
            errores += 1
            leidos += 1
            motivos["sin datos del terminal"] += 1
            continue
        if edad >= EDAD_TICK_MAXIMA_MIN:
            motivos["con el mercado cerrado"] += 1
            continue
        leidos += 1
        ev = lec.evaluar(a, eventos, delta, ahora, analizador=memo)
        if "excluido" in ev:
            if memo.con_error(t):
                errores += 1
                motivos["sin datos del terminal"] += 1
            else:
                motivos[_motivo_gate(str(ev["excluido"]))] += 1
            continue
        h1, d1 = memo(t, "H1"), memo(t, "D1")
        sesgo = "Alcista" if ev["direccion"] == "ALCISTA" else "Bajista"
        df = lec.serie(t)
        pf = lec.armar_plan(df, h1, a, sesgo)
        motivo = elegible(pf)
        if motivo:
            motivos[motivo] += 1
            continue
        puntos = ev["factores"]["tecnico"]["puntos"] + ev["factores"]["momentum"]["puntos"]
        clave = (-puntos, _distancia(pf), t)
        candidatos.append((clave, Elegido(a, ev, h1, d1, pf, df)))

    if leidos and errores == leidos:
        return MercadoIlegible("el terminal no entregó datos de ningún activo")
    if not candidatos:
        return SinFoco(len(universo), dict(motivos))
    _, elegido = min(candidatos, key=lambda c: c[0])
    return Seleccion(elegido, len(universo), ahora)
