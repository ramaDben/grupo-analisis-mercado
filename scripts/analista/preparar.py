"""Datos e imágenes de cada pieza, en la carpeta del pedido y en ningún otro lado.

Usa los constructores puros de producción (los que arman las piezas de
WhatsApp), nunca los `preparar()` de los pipelines: esos escriben en
`data/carrusel/`, `data/screener/` y en los historiales de despacho, y un pedido
de un analista no puede cambiar qué considera "ya publicado" la tanda real.

Cada lector se puede reemplazar (`Lectores`), así los tests corren sin MT5.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from analista import esquema as es
from analista.orden import Orden

SANTIAGO = ZoneInfo("America/Santiago")


class PreparacionFallida(RuntimeError):
    """El dato no está; el mensaje se le muestra al analista tal cual."""


class SinSemanaError(PreparacionFallida):
    """La semana no tiene análisis semanal: el bot no corre el escáner (spec §5)."""


class SinFotoError(PreparacionFallida):
    """La semana no tiene foto todavía."""


class FueraDeLaFotoError(PreparacionFallida):
    """El activo no está en la foto de esta semana."""


class EsperaVelaError(PreparacionFallida):
    """Una línea A+ está en prueba: la foto espera el cierre de esa vela (spec §5)."""


# ───────────────────────────────────────────────────────────── lectores reales


def _agenda(ahora: datetime):
    import pipeline_linkedin as pl

    return pl.leer_agenda(ahora)


def _curva():
    import pipeline_informe as pi

    return pi._curva()


def _drivers(ticker: str) -> list[str]:
    """Los drivers que el catálogo declara para el activo (`config/activos.json`)."""
    from analista import RAIZ

    datos = json.loads((RAIZ / "config" / "activos.json").read_text(encoding="utf-8"))

    def recorrer(nodo: Any):
        if isinstance(nodo, dict):
            if nodo.get("ticker_mt5") == ticker:
                yield nodo
            for v in nodo.values():
                yield from recorrer(v)
        elif isinstance(nodo, list):
            for v in nodo:
                yield from recorrer(v)

    for activo in recorrer(datos):
        return [str(d) for d in activo.get("drivers", [])]
    return []


def _catalogo_de(ticker: str) -> dict[str, Any]:
    import pipeline_linkedin as pl

    return pl._catalogo()[ticker]


def _cuenta() -> str | None:
    """`None` si el terminal está en la cuenta declarada; si no, el motivo."""
    from guardrails.cuenta import cuenta_correcta
    from market_data_mcp import mt5_client

    try:
        mt5_client.connect()
        import MetaTrader5 as mt5  # noqa: PLC0415

        info = mt5.account_info()
    except Exception as exc:  # noqa: BLE001
        return f"MT5 no conectó ({exc.__class__.__name__}). ¿Está abierto el terminal?"
    veredicto = cuenta_correcta(getattr(info, "login", None))
    return None if veredicto.ok else veredicto.detalle


def _contrato(ticker: str, precio: float) -> dict[str, Any]:
    """Lo que el panel necesita para simular, medido en la cuenta declarada.

    `order_calc_profit` y no `tick_value` (miente en los CFD de acciones). Son cálculos, no órdenes.
    """
    from market_data_mcp import mt5_client

    try:
        mt5_client.connect()
        import MetaTrader5 as mt5  # noqa: PLC0415

        mt5.symbol_select(ticker, True)
        info = mt5.symbol_info(ticker)
        clp_unidad = mt5.order_calc_profit(mt5.ORDER_TYPE_BUY, ticker, 1.0, precio, precio + 1.0)
    except Exception as exc:  # noqa: BLE001
        raise PreparacionFallida(f"no pude leer el contrato de {ticker} ({exc.__class__.__name__})") from exc
    if not info or not clp_unidad:
        raise PreparacionFallida(f"el terminal no calculó el contrato de {ticker}: sin él no hay simulación")
    return {"clp_unidad": float(clp_unidad), "vol_min": float(info.volume_min),
            "vol_paso": float(info.volume_step)}


def _grafico_lectura(ticker: str, nombre: str, lectura, destino: Path) -> Path:
    from tradingview_grafico import generar_grafico_tv

    return generar_grafico_tv(ticker=ticker, nombre=nombre, destino=destino, timeframe=lectura.marco,
                              lineas=lectura.lineas)


def _estrategia():
    from estrategia import registro

    return registro.activa()


def _estado_semanal(estrategia, semana, lector, ahora, digits, base=None):
    import referencia_semanal as rs

    return rs.estado_semanal(estrategia, semana, lector, ahora, digits, base=base or rs.DIR)


def _velas(ticker, marcos, extra=0):
    from estrategia.fuente import velas_mt5

    return velas_mt5(ticker, marcos, extra)


def _lectura_del_dia(estrategia, ticker, digits, semana, lector, base=None):
    import referencia_semanal as rs

    return rs.lectura_del_dia(estrategia, ticker, digits, semana, lector, base=base or rs.DIR)


@dataclass
class Lectores:
    contrato: Callable[[str, float], dict[str, Any]] = _contrato
    grafico_lectura: Callable[..., Path] = _grafico_lectura
    estrategia: Callable[[], Any] = _estrategia
    estado_semanal: Callable[..., list[dict[str, Any]]] = _estado_semanal
    velas: Callable[..., Any] = _velas
    agenda: Callable[[datetime], tuple[list[dict[str, Any]], list[str]]] = _agenda
    curva: Callable[[], tuple[dict[str, Any], list[str]]] = _curva
    drivers: Callable[[str], list[str]] = _drivers
    cuenta: Callable[[], str | None] = _cuenta
    catalogo: Callable[[str], dict[str, Any]] = _catalogo_de
    base_referencias: Path | None = None
    registro: Path | None = None
    lectura_del_dia: Callable[..., Any] = _lectura_del_dia


@dataclass
class Preparada:
    pieza: dict[str, Any]
    avisos: list[str] = field(default_factory=list)


# ───────────────────────────────────────────────────────────── piezas


DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")


def fecha_corta(momento: datetime) -> str:
    m = momento.astimezone(SANTIAGO)
    return f"{DIAS[m.weekday()]} {m:%d-%m}"


def _entrada_activo(ticker: str, referencia, guardada: datetime, puntaje: float, dir_pedido: Path,
                    lec: Lectores, estrategia) -> dict[str, Any]:
    import pipeline_carrusel as pc
    from estrategia.contrato import lectura_a_dict

    from analista import oportunidad as op

    cat = lec.catalogo(ticker)
    d = int(cat["digits"])
    f = lambda x: pc.formatear_precio(x, d) if x is not None else ""  # noqa: E731
    esc = op.escenario(referencia, d)
    sup = inf = None
    if referencia.estado == "RANGO":
        sup, inf = op.bordes_rango(referencia)
    grafico = f"grafico_{ticker.lower().replace('.', '_')}.png"
    lec.grafico_lectura(ticker, cat["nombre"], referencia, dir_pedido / grafico)
    etiqueta = estrategia.marcos.etiquetas[referencia.marco]
    return {
        "ticker": ticker, "nombre": cat["nombre"], "ticker_visible": cat.get("ticker_visible", ticker),
        "digits": d, "unidad": cat.get("unidad") or "", "puntaje": puntaje,
        "foto": {"guardada": guardada.isoformat(), "fecha": fecha_corta(guardada), "precio": referencia.precio},
        "lectura": lectura_a_dict(referencia), "escenario": esc.a_dict(),
        "fmt": {"precio": f(referencia.precio), "vigilar": f(referencia.vigilar.precio),
                "invalidacion": f(referencia.invalidacion.precio if referencia.invalidacion else None),
                "objetivo_tori": f(referencia.objetivo.precio if referencia.objetivo else None),
                "entrada": f(esc.entrada), "stop": f(esc.stop), "objetivo": f(esc.objetivo),
                "borde_superior": f(sup), "borde_inferior": f(inf)},
        "contrato": lec.contrato(ticker, referencia.precio) if esc.simulable else None,
        "temporalidad": f"{pc.ETIQUETA_CORTA.get(referencia.marco, referencia.marco)} · "
                        f"{etiqueta.nombre} ({etiqueta.duracion})",
        "grafico": grafico,
    }


def preparar_oportunidad(orden: Orden, dir_pedido: Path, ahora: datetime, lec: Lectores) -> Preparada:
    """La foto de la semana: los elegidos del análisis semanal, con su referencia del lunes."""
    import referencia_semanal as rs

    base = lec.base_referencias or rs.DIR
    semana = rs.semana_de(ahora)
    manifiesto = rs.manifiesto(semana, base)
    if manifiesto is None:
        raise SinSemanaError(f"La semana {semana} todavía no tiene análisis semanal: la pieza sale "
                             "cuando el escáner la fije.")
    estrategia = lec.estrategia()
    digits = {t: int(lec.catalogo(t)["digits"]) for t in manifiesto["elegidos"]}
    esperas = [f["espera_hasta"] for f in lec.estado_semanal(estrategia, semana, lec.velas, ahora, digits,
                                                             base=base) if f.get("espera_hasta")]
    if esperas:
        hora = max(esperas).astimezone(SANTIAGO)
        raise EsperaVelaError(f"Una línea clave está en prueba: se publica al cierre de la vela de las "
                              f"{hora:%H:%M}.")
    puntajes = manifiesto.get("puntajes", {})
    orden_tickers = sorted(manifiesto["elegidos"], key=lambda t: (-float(puntajes.get(t, 0)), t))
    activos, avisos = [], []
    for ticker in orden_tickers:
        referencia = rs.cargar(semana, ticker, base)
        if referencia is None:
            avisos.append(f"{ticker} no tiene referencia en {semana}: queda fuera")
            continue
        guardada = datetime.fromisoformat(
            json.loads(rs.ruta(semana, ticker, base).read_text(encoding="utf-8"))["guardada"])
        activos.append(_entrada_activo(ticker, referencia, guardada, float(puntajes.get(ticker, 0)),
                                       dir_pedido, lec, estrategia))
    agenda, av = lec.agenda(ahora)
    avisos += [f"contexto sin agenda: {a}" for a in av]
    curva, av = lec.curva()
    avisos += [f"contexto sin curva de tasas: {a}" for a in av]
    sin_pct = _contexto_sin_porcentajes({"curva": _filas_curva(curva)})
    datos = {"semana": semana, "chip": "ANÁLISIS TÉCNICO DE LA SEMANA",
             "edicion": fecha_corta(ahora) + f" · {ahora.astimezone(SANTIAGO):%H:%M}",
             "activos": activos, "drivers": {a["ticker"]: lec.drivers(a["ticker"]) for a in activos},
             "agenda_semana": [f"{ev.get('hora', '')} · {ev.get('nombre_es') or ev.get('evento', '')}"
                               for ev in agenda],
             "curva": sin_pct["curva"]}
    tickers = [a["ticker"] for a in activos]
    pieza = es.nueva_pieza("oportunidad", {"semana": semana}, datos,
                           {a["ticker"]: a["grafico"] for a in activos},
                           extra_campos={"titulares": tickers, "contexto": tickers})
    return Preparada(pieza, avisos)


def preparar_seguimiento(orden: Orden, dir_pedido: Path, ahora: datetime, lec: Lectores) -> Preparada:
    """El avance de un activo contra la foto: la simulación y la lectura de hoy, por separado."""
    import referencia_semanal as rs
    from estrategia.contrato import lectura_de_dict

    from analista import registro_semanal as rg
    from analista import seguimiento as sg

    semana = rs.semana_de(ahora)
    foto = rg.foto(semana, lec.registro or rg.RUTA)  # un registro corrupto levanta ValueError: no es "sin foto"
    if foto is None:
        raise SinFotoError("Esta semana todavía no hay análisis publicado: pide primero /oportunidad.")
    pieza_foto = cargar_pieza(Path(foto["dir"]))
    activos = {a["ticker"]: a for a in pieza_foto["datos"]["activos"]}
    ticker = orden.args["ticker"]
    if ticker not in activos:
        nombres = ", ".join(a["nombre"] for a in activos.values())
        raise FueraDeLaFotoError(f"Ese activo no está en el análisis de esta semana. Los de esta semana: {nombres}.")
    a = activos[ticker]
    esc = a["escenario"]
    if esc["motivo"]:
        raise PreparacionFallida(f"{a['nombre']} no tiene simulación esta semana: {esc['motivo']}.")
    referencia_foto = lectura_de_dict(a["lectura"])
    base = lec.base_referencias or rs.DIR
    estrategia = lec.estrategia()
    try:
        diaria = lec.lectura_del_dia(estrategia, ticker, a["digits"], semana, lec.velas, base=base)
    except rs.SinReferencia as exc:
        raise PreparacionFallida(f"{ticker}: {exc}") from exc
    vigente = rs.cargar(semana, ticker, base)
    reemplazada = diaria.reemplazo is not None or (vigente is not None
                                                   and rs.firma(vigente) != rs.firma(referencia_foto))
    h4 = diaria.velas[referencia_foto.marco]
    posteriores = h4[h4["time"] > referencia_foto.vela].to_dict("records") if len(h4) else []
    precio = diaria.lectura.precio
    ev = sg.evaluar(esc, posteriores, precio)
    lectura_hoy = sg.texto_lectura(diaria.lectura, reemplazada, a["digits"])
    hoy = fecha_corta(ahora)
    texto = sg.mensaje(a["nombre"], hoy, a["foto"]["fecha"], esc, ev, precio, diaria.lectura, reemplazada,
                       a["digits"])
    lec.grafico_lectura(ticker, a["nombre"], diaria.lectura, dir_pedido / "grafico.png")
    datos = {"semana": semana, "ticker": ticker, "nombre": a["nombre"], "evaluacion": ev, "precio_vivo": precio,
             "lectura_hoy": lectura_hoy, "reemplazada": reemplazada, "whatsapp": texto,
             "edicion": f"{hoy} · {ahora.astimezone(SANTIAGO):%H:%M}", "activo": a}
    pieza = es.nueva_pieza("seguimiento", {"ticker": ticker}, datos, {"principal": "grafico.png"})
    return Preparada(pieza, list(diaria.avisos))


def _contexto_sin_porcentajes(contexto: dict[str, Any]) -> dict[str, Any]:
    """El contexto de la pieza semanal: sin la tabla de tasas y sin "%".

    La pieza no muestra ningún porcentaje al prospecto (candado de `esquema`). La
    tabla de tasas se imprimiría igual, y una cifra con "%" en los datos invitaría
    a agy a citarla y haría rechazar la pieza después de gastar la redacción.
    """
    def limpio(v: Any) -> Any:
        if isinstance(v, str):
            return v.replace(" %", " por ciento").replace("%", " por ciento")
        if isinstance(v, list):
            return [limpio(x) for x in v]
        if isinstance(v, dict):
            return {k: limpio(x) for k, x in v.items()}
        return v

    return limpio({k: v for k, v in contexto.items() if k != "curva_tasas"})


def _filas_curva(curva: dict[str, Any]) -> list[list[str]]:
    import pipeline_informe as pi

    series = curva.get("series", {}) if curva else {}

    def puntos(v: Any) -> str:
        # `None` es "no se pudo calcular", no "no se movió" (CLAUDE.md, get_curva_tasas).
        return "sin dato" if v is None else f"{v:+.0f} pb"

    return [
        [pi._TRAMOS_ES.get(k, k), pi._pct_es(series[k].get("nivel_pct")),
         puntos(series[k].get("delta_1d_bps")), puntos(series[k].get("delta_5d_bps"))]
        for k in pi.TRAMOS_CURVA if series.get(k)
    ]


PREPARADORES = {
    "oportunidad": preparar_oportunidad,
    "seguimiento": preparar_seguimiento,
}

# Piezas que leen precios del terminal: sin la cuenta declarada no salen.
CON_TERMINAL = {"oportunidad", "seguimiento"}


def preparar(orden: Orden, dir_pedido: Path, ahora: datetime | None = None,
             lectores: Lectores | None = None) -> Preparada:
    """Escribe `pieza.json` y las imágenes sin texto en `dir_pedido`."""
    ahora = ahora or datetime.now(SANTIAGO)
    lec = lectores or Lectores()
    dir_pedido.mkdir(parents=True, exist_ok=True)
    if orden.pieza in CON_TERMINAL:
        problema = lec.cuenta()
        if problema:
            raise PreparacionFallida(f"no uso el terminal: {problema}")
    hecha = PREPARADORES[orden.pieza](orden, dir_pedido, ahora, lec)
    guardar_pieza(hecha.pieza, dir_pedido)
    return hecha


def guardar_pieza(pieza: dict[str, Any], dir_pedido: Path) -> Path:
    ruta = dir_pedido / "pieza.json"
    ruta.write_text(json.dumps(pieza, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def cargar_pieza(dir_pedido: Path) -> dict[str, Any]:
    return json.loads((dir_pedido / "pieza.json").read_text(encoding="utf-8"))


