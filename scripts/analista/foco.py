"""Foco técnico del día (`/oportunidad`): qué activo mirar hoy, elegido por una regla.

Lo piden los ejecutivos de ventas para un prospecto, y nadie en GI está inscrito
como asesor de inversión. Por eso lo elige una regla y no una persona, es el
mismo para todos los que lo piden a la misma hora, y algunos días no hay: el bot
lo dice en vez de rellenar. Spec: docs/superpowers/specs/2026-10-09-foco-tecnico-del-dia-design.md

La regla es la de la estrategia activa (enchufe de estrategia, S7): el puntaje de
sesión de `estrategia.puntuar`, y solo entra un activo en las dos primeras situaciones
del horizonte sesión (ruptura reciente con la línea de seguridad cerca, o a punto de
tocar una línea A+ o recién rebotado en ella). Antes ordenaba con técnico + momentum del
`Score_GI` y armaba el plan con el Chandelier: dos lecturas que no eran la publicada.

Dos decisiones que no conviene revertir:

1. **Sin calendario no hay foco.** Sin él no se puede verificar que no venga un
   dato fuerte, y entregar a ciegas a minutos del empleo es lo que el gate evita.
2. **Una sola lectura por pedido.** El elegido trae la selección con que se eligió,
   y la pieza se arma con ella: leer otra vez podría encontrar otro estado.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

AGREGADOS = ("US100.spot", "BRENT.spot")
CLASE_BASE = "forex_commodities"
CLASES_INDICE = {"indices"}
# El piso de la situación "a punto" del horizonte sesión (estrategia/tori/parametros.py,
# bandas_sesion): solo entran la ruptura reciente y el "a punto" (spec §5).
FOCO_PUNTOS_MIN = 50.0
EDAD_TICK_MAXIMA_MIN = 15.0

_AVISO_CALENDARIO = "calendario no disponible"


# ───────────────────────────────────────────────────────────── resultados


@dataclass(frozen=True)
class Elegido:
    activo: dict[str, Any]
    seleccion: dict[str, Any]  # la entrada del escáner: lectura, puntaje, marco, volatilidad
    plan: dict[str, Any]


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


def elegible(seleccion: dict[str, Any], plan: dict[str, Any]) -> str | None:
    """None si el activo sirve como foco hoy; si no, el motivo en palabras del ejecutivo."""
    if not plan.get("hay_plan"):
        return "sin una tendencia con línea de seguridad"
    if seleccion["score"] < FOCO_PUNTOS_MIN:
        return "sin una ruptura reciente ni un precio a punto de tocar su línea"
    return None


def _motivo_gate(texto: str) -> str:
    t = texto.lower()
    if t.startswith("feriado"):
        return "en feriado de su bolsa"
    if t.startswith("blackout"):
        return "por un dato económico fuerte"
    if "secuencia" in t:
        return "contra la tendencia de los marcos mayores"
    if "trazables" in t:
        return "sin estructura de tendencia"
    if "en prueba" in t:
        return "con una línea en prueba"
    return "sin datos del terminal"


# ───────────────────────────────────────────────────────────── lectura


def _conectar() -> list[str]:
    import screener_gi as sc

    return sc._conectar_terminal()


def _contexto_macro(ahora: datetime):
    import screener_gi as sc

    return sc._contexto_macro(ahora)


def _seleccion(activo: dict[str, Any], ahora: datetime) -> dict[str, Any]:
    import screener_gi as sc

    return sc.seleccion_fija(activo, ahora, fijo=False)


def _gate(ticker: str, eventos: list[dict[str, Any]], ahora: datetime) -> str | None:
    import screener_gi as sc

    return sc.gate_feriado(ticker, ahora.date()) or sc.gate_blackout(ticker, eventos, ahora)


def _edad_tick(ticker: str) -> float | None:
    """Minutos desde el último tick del símbolo, en hora del SERVIDOR.

    MT5 entrega hora de servidor empaquetada como UTC: compararla con el reloj
    local desplaza todo por el offset del broker. La referencia es el tick de
    BTCUSD, que cotiza todos los días a toda hora.
    """
    import MetaTrader5 as mt5  # noqa: PLC0415

    # Fuera del Market Watch, symbol_info_tick devuelve None hasta seleccionar el
    # símbolo: el activo quedaría descartado para siempre como "sin datos".
    for simbolo in (ticker, "BTCUSD"):
        mt5.symbol_select(simbolo, True)
    propio, ref = mt5.symbol_info_tick(ticker), mt5.symbol_info_tick("BTCUSD")
    if propio is None or ref is None:
        return None
    return max(0, max(ref.time, propio.time) - propio.time) / 60


def _activo(ticker: str) -> dict[str, Any]:
    import screener_gi as sc

    return next(a for a in sc.cargar_universo(solo_renderizables=False) if a["ticker"] == ticker)


def _divergencia(preparada, actual) -> str | None:
    from estrategia import registro

    return registro.activa().divergencia(preparada, actual)


def plan_de(seleccion: dict[str, Any], activo: dict[str, Any]) -> dict[str, Any]:
    """El plan del foco, desde la lectura con que se eligió."""
    from analista import plan as plan_mod
    from estrategia.contrato import lectura_de_dict

    return plan_mod.armar(lectura_de_dict(seleccion["lectura"]), int(activo["digits"]), activo["nombre"])


@dataclass
class LectoresFoco:
    conectar: Callable[[], list[str]] = _conectar
    contexto_macro: Callable[[datetime], tuple[list[dict[str, Any]], float | None, list[str]]] = _contexto_macro
    seleccion: Callable[[dict[str, Any], datetime], dict[str, Any]] = _seleccion
    gate: Callable[[str, list[dict[str, Any]], datetime], str | None] = _gate
    edad_tick: Callable[[str], float | None] = _edad_tick
    activo: Callable[[str], dict[str, Any]] = _activo
    divergencia: Callable[[Any, Any], str | None] = _divergencia


# ───────────────────────────────────────────────────────────── selección


def seleccionar(universo: list[dict[str, Any]], ahora: datetime,
                lec: LectoresFoco | None = None) -> Seleccion | SinFoco | MercadoIlegible:
    lec = lec or LectoresFoco()
    if lec.conectar():
        return MercadoIlegible("MetaTrader 5 no responde")
    eventos, _delta, avisos = lec.contexto_macro(ahora)
    if calendario_caido(avisos):
        return MercadoIlegible("el calendario económico no responde y sin él no se puede "
                               "verificar que no venga un dato fuerte")

    motivos: Counter[str] = Counter()
    candidatos: list[tuple[tuple, Elegido]] = []
    leidos = errores = 0
    for a in universo:
        t = a["ticker"]
        if not indice_habilitado(a, ahora):
            motivos["índice antes de la apertura de Nueva York"] += 1
            continue
        try:
            edad = lec.edad_tick(t)
        except Exception:  # noqa: BLE001
            edad = None
        if edad is None:
            errores += 1
            leidos += 1
            motivos["sin datos del terminal"] += 1
            continue
        if edad >= EDAD_TICK_MAXIMA_MIN:
            motivos["con el mercado cerrado"] += 1
            continue
        leidos += 1
        gate = lec.gate(t, eventos, ahora)
        if gate:
            motivos[_motivo_gate(gate)] += 1
            continue
        try:
            sel = lec.seleccion(a, ahora)
            if "excluido" in sel:
                motivos[_motivo_gate(str(sel["excluido"]))] += 1
                continue
            plan = plan_de(sel, a)
        except Exception:  # noqa: BLE001
            # Un activo con datos rotos se salta; no puede tumbar la selección de los demás.
            errores += 1
            motivos["sin datos del terminal"] += 1
            continue
        motivo = elegible(sel, plan)
        if motivo:
            motivos[motivo] += 1
            continue
        candidatos.append(((-sel["score"], t), Elegido(a, sel, plan)))

    if leidos and errores == leidos:
        return MercadoIlegible("el terminal no entregó datos de ningún activo")
    if not candidatos:
        return SinFoco(len(universo), dict(motivos))
    _, elegido = min(candidatos, key=lambda c: c[0])
    # "Entre N activos" es lo que se imprime al prospecto: cuenta los que compitieron,
    # no los saltados por mercado cerrado o por ser un índice antes de la apertura.
    return Seleccion(elegido, leidos, ahora)


# ───────────────────────────────────────────────────────────── vigencia


def _clase_estado(plan: dict[str, Any]) -> str:
    return str(plan.get("estado", "")).split(":", 1)[0]


def sigue_vigente(pieza: dict[str, Any], ahora: datetime, lec: LectoresFoco | None = None) -> bool:
    """¿Se puede volver a entregar este foco tal cual?

    La ventana de reuso sola no alcanza: un dato o un titular pueden invalidar el
    plan a los diez minutos, y otro ejecutivo recibiría un escenario que ya no
    existe. Se vuelve a leer el activo con la estrategia y, ante la menor duda, se rehace.
    """
    lec = lec or LectoresFoco()
    try:
        from estrategia.contrato import lectura_de_dict

        datos = pieza["datos"]
        ticker, previo = datos["ticker"], datos["plan"]
        if lec.conectar():
            return False
        eventos, _, avisos = lec.contexto_macro(ahora)
        if calendario_caido(avisos) or lec.gate(ticker, eventos, ahora):
            return False
        edad = lec.edad_tick(ticker)
        if edad is None or edad >= EDAD_TICK_MAXIMA_MIN:
            return False
        activo = lec.activo(ticker)
        sel = lec.seleccion(activo, ahora)
        if "excluido" in sel:
            return False
        if lec.divergencia(lectura_de_dict(datos["lectura"]), lectura_de_dict(sel["lectura"])):
            return False
        plan = plan_de(sel, activo)
        return (elegible(sel, plan) is None
                and plan["niveles"]["gatillo"] == previo["niveles"]["gatillo"]
                and _clase_estado(plan) == _clase_estado(previo))
    except Exception:  # noqa: BLE001
        return False
