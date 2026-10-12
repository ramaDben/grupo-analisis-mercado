"""Datos e imágenes de cada pieza, en la carpeta del pedido y en ningún otro lado.

Usa los constructores puros de producción (los que arman las piezas de
WhatsApp), nunca los `preparar()` de los pipelines: esos escriben en
`data/carrusel/`, `data/screener/` y en los historiales de despacho, y un pedido
de un analista no puede cambiar qué considera "ya publicado" la tanda real.

Cada lector se puede reemplazar (`Lectores`), así los tests corren sin MT5.
"""
from __future__ import annotations

import json
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from analista import esquema as es
from analista.orden import Orden

SANTIAGO = ZoneInfo("America/Santiago")
NUEVA_YORK = ZoneInfo("America/New_York")


class PreparacionFallida(RuntimeError):
    """El dato no está; el mensaje se le muestra al analista tal cual."""


class SinFocoError(PreparacionFallida):
    """Ningún activo tiene hoy una configuración clara: es una lectura, no una falla."""


class MercadoIlegibleError(PreparacionFallida):
    """MT5 o el calendario no responden: no se sabe si hay foco o no."""


class SinSemanaError(PreparacionFallida):
    """La semana no tiene análisis semanal: el bot no corre el escáner (spec §5)."""


class SinFotoError(PreparacionFallida):
    """La semana no tiene foto todavía."""


class FueraDeLaFotoError(PreparacionFallida):
    """El activo no está en la foto de esta semana."""


class EsperaVelaError(PreparacionFallida):
    """Una línea A+ está en prueba: la foto espera el cierre de esa vela (spec §5)."""


# ───────────────────────────────────────────────────────────── lectores reales


def _terminal(ticker: str, ahora: datetime) -> dict[str, Any]:
    import pipeline_avisos as pa

    try:
        return pa.leer_terminal(ticker, ahora)
    except pa.LecturaFallidaError as exc:
        raise PreparacionFallida(f"el terminal no entregó {ticker}: {exc}") from exc


def _grafico_tv(payload: dict[str, Any], destino: Path) -> Path:
    """El mismo gráfico que sale por WhatsApp en el carrusel (`pc.rendir`)."""
    import pipeline_carrusel as pc
    from tradingview_grafico import generar_grafico_tv

    crudos = payload["_procedencia"].get("crudos", {})
    return generar_grafico_tv(
        ticker=payload["_procedencia"]["ticker"],
        nombre=payload.get("rotulo_activo", payload["activo"]),
        destino=destino,
        timeframe=payload["marco"],
        n_velas=pc.VELAS_GRAFICO_TV,
        soporte=pc._nivel_publicado(payload.get("soporte"), crudos.get("soporte")),
        resistencia=pc._nivel_publicado(payload.get("resistencia"), crudos.get("resistencia")),
        lineas=pc.lineas_de(payload),
    )


def _jornada(ahora: datetime):
    import pipeline_avisos as pa

    return pa.leer_jornada(ahora)


def _agenda(ahora: datetime):
    import pipeline_linkedin as pl

    return pl.leer_agenda(ahora)


def _movimiento(ticker: str, desde: datetime, ahora: datetime) -> dict[str, Any]:
    import pipeline_avisos as pa

    try:
        return pa.leer_movimiento(ticker, desde, ahora)
    except pa.LecturaFallidaError as exc:
        raise PreparacionFallida(f"no se pudo medir {ticker}: {exc}") from exc


def _activos_jornada(destino: Path):
    import pipeline_informe as pi

    return pi.leer_activos(destino)


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


def _foco(ahora: datetime):
    from analista import foco as fo

    return fo.seleccionar(fo.universo_ventas(), ahora)


def _catalogo_de(ticker: str) -> dict[str, Any]:
    import pipeline_linkedin as pl

    return pl._catalogo()[ticker]


def _cierres(ticker: str, marco: str | None = None) -> list[float]:
    import pipeline_carrusel as pc

    try:
        return pc._serie_para(ticker, marco or pc.marco_operativo())
    except Exception as exc:  # noqa: BLE001
        raise PreparacionFallida(f"{ticker}: sin serie para el gráfico ({exc})") from exc


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


def _comunes(ahora: datetime, chip: str, rotulo_referencia: str, referencia: str) -> dict[str, Any]:
    import pipeline_avisos as pa

    return {"chip": chip, "rotulo_referencia": rotulo_referencia, "referencia": referencia,
            "edicion": pa.fecha_hora(ahora)}


def preparar_activo(orden: Orden, dir_pedido: Path, ahora: datetime, lec: Lectores) -> Preparada:
    lectura = lec.terminal(orden.args["ticker"], ahora)
    return _pieza_de_activo("activo", orden.args, lectura, dir_pedido, ahora, lec)


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
    """El contexto del foco técnico: sin la tabla de tasas y sin "%".

    El foco no muestra ningún porcentaje al prospecto (candado de `esquema`). La
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


def _pieza_de_activo(tipo: str, args: dict[str, Any], lectura: dict[str, Any], dir_pedido: Path,
                     ahora: datetime, lec: Lectores, plan: dict[str, Any] | None = None,
                     extra: dict[str, Any] | None = None, chip: str | None = None) -> Preparada:
    import pipeline_carrusel as pc

    if not (lectura.get("seleccion") or {}).get("lectura"):
        raise PreparacionFallida("la lectura del terminal no trae la lectura de la estrategia que necesita la pieza")
    try:
        payload = pc.construir_payload_lectura(lectura["seleccion"], lectura["activo"], ahora, lectura["cierres"])
    except pc.PayloadIncoherenteError as exc:
        raise PreparacionFallida(f"los datos del terminal no son coherentes ahora ({exc}); prueba en unos minutos") from exc
    except KeyError as exc:
        raise PreparacionFallida(f"al activo le falta {exc} en config/activos.json") from exc

    op = pc.lectura_operativa(payload)
    activo = lectura["activo"]
    ticker = args["ticker"]
    plan = plan if plan is not None else _plan(ticker, lectura, payload["sesgo"], activo, lec)
    precio = payload["precio_actual"]
    unidad = activo.get("unidad") or ""
    clase = CLASES.get(str(activo.get("categoria") or activo.get("clase") or "").lower(), "MERCADOS")
    lec.grafico_tv(payload, dir_pedido / "grafico.png")
    contexto, avisos_contexto = _contexto(ticker, ahora, lec)
    if tipo == "oportunidad":
        contexto = _contexto_sin_porcentajes(contexto)
    datos = {
        **_comunes(ahora, chip or f"NOTA DE MERCADO · {clase}", "Cotización de referencia",
                   f"{precio} {unidad}".strip()),
        "ticker": ticker,
        "nombre": activo["nombre"],
        "precio": precio,
        "soporte": payload["soporte"],
        "resistencia": payload["resistencia"],
        "direccion": payload["sesgo"],
        **op,
        "pie_imagen": f"{payload.get('rotulo_activo', activo['nombre'])} · velas de "
                      f"{MARCO_LEGIBLE.get(payload['marco'], payload['marco'])} · MetaTrader 5",
        # La lectura con que se armó: el foco la compara al reusar la pieza (`sigue_vigente`).
        "lectura": lectura["seleccion"]["lectura"],
        "contexto": contexto,
        "plan": plan,
        **(extra or {}),
    }
    avisos = list(avisos_contexto)
    if payload.get("aviso_lectura"):
        avisos.append(f"la estrategia habría excluido el activo: {payload['aviso_lectura']}")
    pieza = es.nueva_pieza(tipo, args, datos, {"principal": "grafico.png"})
    return Preparada(pieza, avisos)


MARCO_LEGIBLE = {"H1": "1 hora", "H4": "4 horas", "D1": "1 día", "W1": "1 semana"}


def _plan(ticker: str, lectura: dict[str, Any], sesgo: str, activo: dict[str, Any], lec: Lectores) -> dict[str, Any]:
    """El plan de escenarios desde la lectura de la estrategia: lo escribe Python y queda sellado.

    Sin estadística ni Chandelier (enchufe de estrategia, S7; spec §8.4).
    """
    from analista import plan as plan_mod
    from estrategia.contrato import lectura_de_dict

    if "lectura" not in lectura.get("seleccion", {}):
        raise PreparacionFallida("la lectura del terminal no trae la lectura de la estrategia que necesita el plan")
    return plan_mod.armar(lectura_de_dict(lectura["seleccion"]["lectura"]), int(activo["digits"]), activo["nombre"])


CLASES = {
    "commodity": "COMMODITIES", "forex": "DIVISAS", "crypto": "CRIPTOMONEDAS",
    "indice": "ÍNDICES", "indices": "ÍNDICES", "acciones": "ACCIONES", "accion": "ACCIONES",
    "etf": "ETF", "etfs": "ETF",
}


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


def _contexto(ticker: str, ahora: datetime, lec: Lectores) -> tuple[dict[str, Any], list[str]]:
    """Lo medido del día que agy puede usar para explicar los drivers.

    Sin esto, agy redactaba "debilidad del dólar global" sin un solo dato que lo
    respaldara (prueba real del 2026-10-08): los drivers quedaban enumerados, no
    analizados. Lo que no está acá, el texto no lo puede afirmar como hecho.
    """
    import pipeline_avisos as pa

    avisos: list[str] = []
    curva, av = lec.curva()
    avisos += [f"contexto sin curva de tasas: {a}" for a in av]
    jornada, av = lec.jornada(ahora)
    avisos += [f"contexto sin agenda: {a}" for a in av]
    agenda = []
    for ev in jornada:
        actual = pa._cifra(ev.get("actual"))
        esperado = pa._cifra(ev.get("consenso"))
        estado = f"salió {actual}" + (f" frente a {esperado} esperado" if esperado else "") if actual             else ("esperado " + esperado if esperado else "sin cifra aún")
        agenda.append(f"{ev['hora']} · {pa._nombre_evento(ev)}: {estado}")
    return {"drivers_del_activo": lec.drivers(ticker), "curva_tasas": _filas_curva(curva),
            "agenda_hoy": agenda}, avisos


def _estado(cuando: datetime, actual: str, ahora: datetime) -> str:
    if actual:
        return "salio"
    return "pendiente" if cuando <= ahora else "proximo"


def preparar_calendario(orden: Orden, dir_pedido: Path, ahora: datetime, lec: Lectores) -> Preparada:
    import pipeline_avisos as pa

    if orden.args["alcance"] == "hoy":
        eventos, avisos = lec.jornada(ahora)
        if not eventos:
            motivo = "; ".join(avisos) or "hoy no hay datos de alto impacto en la jornada"
            raise PreparacionFallida(f"{motivo}. Prueba con /calendario semana.")
        lamina = pa.lamina_dia(eventos, ahora)
        fuentes = eventos[:6]
        chip = "CALENDARIO ECONÓMICO · HOY"
    else:
        agenda, avisos = lec.agenda(ahora)
        lamina = pa.lamina_semana(agenda, ahora)
        if not lamina["eventos"]:
            raise PreparacionFallida("; ".join(avisos) or "no hay datos de alto impacto esta semana")
        local = ahora.astimezone(SANTIAGO)
        fuentes = sorted(
            (ev for ev in agenda
             if pa._cuando(ev).isocalendar()[:2] == local.isocalendar()[:2] and pa._cuando(ev).weekday() < 5),
            key=pa._cuando,
        )[: len(lamina["eventos"])]
        chip = "CALENDARIO ECONÓMICO · SEMANA"

    filas = []
    for token, ev in zip(lamina["eventos"], fuentes):
        actual = pa._cifra(ev.get("actual"))
        filas.append({
            "id": token["numero"], "dia": token["dia"], "hora": token["hora"], "pais": token["pais"],
            "evento": token["evento"], "anterior": token["anterior"], "esperado": token["esperado"],
            "actual": actual, "estado": _estado(pa._cuando(ev), actual, ahora),
        })
    datos = {
        **_comunes(ahora, chip, "Datos de alto impacto", str(len(filas))),
        "alcance": orden.args["alcance"],
        "eventos": filas,
        "pie_imagen": "Agenda en hora de Chile · calendario de Investing.com",
    }
    pieza = es.nueva_pieza(
        "calendario", orden.args, datos, {"principal": "calendario.png"},
        extra_campos={"explicaciones": [f["id"] for f in filas]},
        laminas={"calendario.png": lamina},
    )
    return Preparada(pieza, list(avisos))


def _plano(texto: str) -> str:
    sin = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in sin if not unicodedata.combining(c)).lower()


def _grupo_del_dato(jornada: list[dict[str, Any]], busqueda: str, ahora: datetime):
    """Los datos que se piden: el último con cifra, o los que calzan con el nombre."""
    import pipeline_avisos as pa

    if busqueda == "ultimo":
        horas = sorted({ev["hora"] for ev in jornada if pa._cuando(ev) <= ahora and str(ev.get("actual") or "").strip()})
        if not horas:
            proximos = [ev for ev in jornada if pa._cuando(ev) > ahora]
            if not proximos:
                raise PreparacionFallida("hoy todavía no sale ningún dato fuerte con cifra")
            hora = proximos[0]["hora"]
        else:
            hora = horas[-1]
        return [ev for ev in jornada if ev["hora"] == hora]
    calzan = [ev for ev in jornada
              if busqueda in _plano(f"{ev.get('nombre_es', '')} {ev.get('evento', '')}")]
    if not calzan:
        raise PreparacionFallida(f"no encontré «{busqueda}» entre los datos fuertes de hoy. Prueba /calendario hoy.")
    return [ev for ev in jornada if ev["hora"] == calzan[0]["hora"] and ev in calzan]


def preparar_dato(orden: Orden, dir_pedido: Path, ahora: datetime, lec: Lectores) -> Preparada:
    import pipeline_avisos as pa

    jornada, avisos = lec.jornada(ahora)
    if not jornada:
        raise PreparacionFallida("; ".join(avisos) or "hoy no hay datos de alto impacto")
    grupo = _grupo_del_dato(jornada, orden.args["busqueda"], ahora)
    con_cifra = [ev for ev in grupo if str(ev.get("actual") or "").strip()]
    hora = grupo[0]["hora"]
    paises = " · ".join(dict.fromkeys(pa._PAISES.get(ev.get("pais", ""), ev.get("pais", "")) for ev in grupo))

    filas, resumen = [], []
    for i, ev in enumerate(grupo, 1):
        etiqueta, _ = pa.VEREDICTOS.get(ev.get("resultado", ""), ("", ""))
        fila = {"id": str(i), "hora": pa.etiqueta_hora(pa._cuando(ev)), "evento": pa._nombre_evento(ev),
                "actual": pa._cifra(ev.get("actual")), "esperado": pa._cifra(ev.get("consenso")),
                "anterior": pa._cifra(ev.get("anterior")), "veredicto": etiqueta.upper()}
        filas.append(fila)
        if con_cifra:
            cola = f" frente a {fila['esperado']} esperado" if fila["esperado"] else ""
            resumen.append(f"{fila['evento']}: {fila['actual'] or 'sin cifra'}{cola}"
                           + (f". {fila['veredicto']} de lo esperado" if fila["veredicto"] and fila["veredicto"] != "EN LÍNEA"
                              else (". En línea con lo esperado" if fila["veredicto"] else "")) + ".")
        else:
            cola = f" Esperado: {fila['esperado']}." if fila["esperado"] else ""
            resumen.append(f"{fila['evento']} sale a las {fila['hora']}.{cola}")

    movimientos, laminas = [], {}
    if con_cifra:
        medidos = {t: lec.movimiento(t, pa._cuando(grupo[0]), ahora) for t in pa.monedas_de(con_cifra)}
        for t, m in medidos.items():
            nombre, _ = pa.ROTULOS_MONEDA.get(t, (t, t))
            movimientos.append({"nombre": nombre, "desde": pa._fmt(m["desde"], m["digits"]),
                                "ahora": pa._fmt(m["ahora"], m["digits"]), "lectura": pa._verbo(m)})
        lamina = pa.lamina_resultado(con_cifra, medidos, ahora)
        referencia = ("Resultado", filas[0]["actual"])
        modo = "resultado"
    else:
        lamina = pa.lamina_dia(grupo, ahora)
        referencia = ("Hora del dato", filas[0]["hora"])
        modo = "anticipacion"
    laminas["dato.png"] = lamina

    datos = {
        **_comunes(ahora, f"DATO MACRO · {paises.upper()}", *referencia),
        "modo": modo,
        "hora": hora,
        "resumen": " ".join(resumen),
        "eventos": filas,
        "movimientos": movimientos,
        "temporalidad": f"1H · marco {pa.TEMPORALIDAD_RESULTADO}",
        "pie_imagen": "Resultado frente a lo esperado · calendario de Investing.com y MetaTrader 5"
        if modo == "resultado" else "Agenda del dato en hora de Chile",
    }
    pieza = es.nueva_pieza("dato", orden.args, datos, {"principal": "dato.png"}, laminas=laminas)
    return Preparada(pieza, list(avisos))


def _momento_por_hora(ahora: datetime) -> str:
    return "apertura" if ahora.astimezone(NUEVA_YORK).hour < 13 else "cierre"


def preparar_jornada(orden: Orden, dir_pedido: Path, ahora: datetime, lec: Lectores) -> Preparada:
    import pipeline_carrusel as pc
    from estrategia.contrato import lectura_de_dict
    from grafico_informe import formatear_precio

    momento = orden.args.get("momento") or _momento_por_hora(ahora)
    activos, avisos = lec.activos_jornada(dir_pedido)
    filas, imagenes = [], {}
    for ticker, info in activos.items():
        if not info.get("lectura") or not info.get("grafico"):
            continue
        lectura = lectura_de_dict(info["lectura"])
        dg = info["digits"]
        soporte, resistencia = pc.niveles_publicados(lectura)
        filas.append({
            "ticker": ticker, "nombre": info["nombre"],
            "precio": formatear_precio(lectura.precio, dg),
            "soporte": formatear_precio(soporte, dg) if soporte is not None else "--",
            "resistencia": formatear_precio(resistencia, dg) if resistencia is not None else "--",
            "direccion": pc._sesgo_de(lectura.direccion),
            "pie_imagen": f"{info['nombre']}: precio de los últimos meses, gráfico diario",
        })
        imagenes[ticker] = info["grafico"]
    if not filas:
        raise PreparacionFallida("; ".join(avisos) or "el terminal no entregó ningún activo de la jornada")

    curva, avisos_curva = lec.curva()
    tabla_curva = _filas_curva(curva)
    datos = {
        **_comunes(ahora, f"INFORME DE {momento.upper()}", "Activos cubiertos", str(len(filas))),
        "momento": momento,
        "activos": filas,
        "curva": tabla_curva,
    }
    pieza = es.nueva_pieza(
        "jornada", {"momento": momento}, datos, imagenes,
        extra_campos={"por_activo": [f["ticker"] for f in filas]},
    )
    return Preparada(pieza, list(avisos) + list(avisos_curva))


PREPARADORES = {
    "activo": preparar_activo,
    "calendario": preparar_calendario,
    "dato": preparar_dato,
    "jornada": preparar_jornada,
    "oportunidad": preparar_oportunidad,
    "seguimiento": preparar_seguimiento,
}

# Piezas que leen precios del terminal: sin la cuenta declarada no salen.
CON_TERMINAL = {"activo", "dato", "jornada", "oportunidad", "seguimiento"}


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


def rendir_laminas(pieza: dict[str, Any], dir_pedido: Path, render: Callable[..., Path] | None = None) -> None:
    """Rinde las láminas de WhatsApp con el texto ya validado.

    La agenda lleva el titular y la bajada adentro; el resultado de un dato no
    (su titular sale del veredicto). Por eso este paso va después de agy.
    """
    import pipeline_avisos as pa

    if render is None:
        from story_render import render_story as render
    ed = pieza["editorial"]
    for nombre, lamina in pieza.get("laminas", {}).items():
        payload = dict(lamina)
        if payload["titular"] == es.MARCA:
            payload["titular"] = ed["titular"]
        if payload.get("parrafo") == es.MARCA:
            payload["parrafo"] = ed["bajada"]
        tokens = pa.tokens_de(payload)
        render(tokens, pa.DIR_PLANTILLAS / pa.PLANTILLAS[payload["_plantilla"]], dir_pedido / nombre,
               formato="horizontal")
