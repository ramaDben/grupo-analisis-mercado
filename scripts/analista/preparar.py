"""Datos e imágenes de cada pieza, en la carpeta del pedido y en ningún otro lado.

Usa los constructores puros de producción (los que arman las piezas de
WhatsApp), nunca los `preparar()` de los pipelines: esos escriben en
`data/carrusel/`, `data/screener/` y en los historiales de despacho, y un pedido
de un analista no puede cambiar qué considera "ya publicado" la tanda real.

Cada lector se puede reemplazar (`Lectores`), así los tests corren sin MT5.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

from analista import esquema as es
from analista import registro_semanal as rg
from analista.orden import Orden

SANTIAGO = ZoneInfo("America/Santiago")


class PreparacionFallida(RuntimeError):
    """El dato no está; el mensaje se le muestra al analista tal cual."""


class SinAnalisisError(PreparacionFallida):
    """El activo no tiene un análisis vigente: `/seguimiento` mide contra él (spec 2026-10-16 §2)."""


# ───────────────────────────────────────────────────────────── lectores reales


def _agenda(ahora: datetime, ticker: str, nombre: str):
    """Los datos de alto impacto de los 7 días de vigencia (spec 2026-10-17 §3)."""
    from analista import agenda as ag

    return ag.leer_ventana(ahora, ticker, nombre)


def _hechos(ticker: str, nombre: str, direccion: str, curva: dict[str, Any], eventos: list[dict[str, Any]],
            ahora: datetime) -> tuple[list[dict[str, Any]], list[str]]:
    """Los drivers del día medidos en el terminal y la curva (spec 2026-10-17 §2)."""
    from market_data_mcp.indices_referencia import serie_diaria

    from analista import hechos as hc

    return hc.medir(ticker, nombre, direccion, curva, eventos, hc.leer_d1_mt5, ahora.astimezone(SANTIAGO).date(),
                    respaldo_dxy=lambda n: serie_diaria("DXY", n))


def _rendir_calendario(payload: dict[str, Any], destino: Path) -> Path:
    """La lámina del calendario con la plantilla `calendario` de Stories (1920×1080)."""
    import pipeline_avisos as pa
    from story_render import render_story

    render_story(payload, pa.DIR_PLANTILLAS / "calendario.html", destino, formato="horizontal")
    return destino


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


def _catalogo_o_terminal(ticker: str) -> dict[str, Any]:
    """El catálogo de la casa; un símbolo que no está se arma con lo que dice el terminal."""
    try:
        return _catalogo_de(ticker)
    except KeyError:
        from analista import simbolos

        info = simbolos.buscar(ticker)
        if info is None:
            raise PreparacionFallida(f"{ticker} no existe en el terminal") from None
        return {"ticker": info["ticker"], "nombre": info["descripcion"], "ticker_visible": info["ticker"],
                "digits": info["digits"], "unidad": "", "notas_marco": {}, "fuera_catalogo": True}


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


def _grafico_lectura(ticker: str, nombre: str, lectura, destino: Path, digits: int | None = None,
                     niveles: list[tuple[float, str]] | None = None) -> Path:
    """El gráfico de la lámina: las líneas de la lectura y cada nivel que cita su texto.

    Con las velas del carrusel y no 60: con menos, el ancla de una diagonal cae fuera de la
    ventana y la línea no se dibuja (la de seguridad del oro, W41).
    """
    import pipeline_carrusel as pc
    from tradingview_grafico import generar_grafico_tv

    return generar_grafico_tv(ticker=ticker, nombre=nombre, destino=destino, timeframe=lectura.marco,
                              n_velas=pc.VELAS_GRAFICO_TV, digits=digits, lineas=lectura.lineas,
                              niveles=niveles)


def niveles_lamina_semanal(lectura) -> list[tuple[float, str]]:
    """Los niveles que nombra la lámina semanal (`comercial._niveles`), en precio, para trazarlos."""
    from analista import oportunidad as op

    if lectura.estado == "RANGO":
        sup, inf = op.bordes_rango(lectura)
        filas = [(sup, "RESISTENCIA DEL RANGO"), (inf, "SOPORTE DEL RANGO"), (lectura.vigilar.precio, "NIVEL A VIGILAR")]
    else:
        filas = [(lectura.vigilar.precio, "NIVEL A VIGILAR")]
        if lectura.invalidacion:
            filas.append((lectura.invalidacion.precio, "INVALIDACIÓN"))
        if lectura.objetivo:
            filas.append((lectura.objetivo.precio, "OBJETIVO TÉCNICO"))
    return filas


def niveles_lamina_seguimiento(esc: dict[str, Any], simula: bool, hoy) -> list[tuple[float, str]]:
    """Los niveles que nombra el seguimiento: la simulación (si la hay) y la línea de hoy."""
    filas = ([(esc["entrada"], "ENTRADA"), (esc["stop"], "STOP"), (esc["objetivo"], "OBJETIVO")]
             if simula else [])
    if hoy.estado == "PRUEBA" and hoy.en_prueba is not None:
        filas.append((hoy.en_prueba.valor_ahora, hoy.vigilar.etiqueta.upper()))
    else:
        filas.append((hoy.vigilar.precio, hoy.vigilar.etiqueta.upper()))
    return filas


def _sin_segundo_objetivo(lectura, simula: bool):
    """Con simulación, el gráfico muestra un solo objetivo: el de la simulación.

    La línea de objetivo técnico de la lectura quedaba a pocos puntos del objetivo de la simulación y
    el cliente veía dos metas distintas y etiquetas apiladas (director, 2026-10-13: «no la veo limpia»).
    """
    if not simula:
        return lectura
    from dataclasses import replace

    return replace(lectura, lineas=tuple(x for x in lectura.lineas if x.rol != "objetivo"))


def _estrategia():
    from estrategia import registro

    return registro.activa()


def _velas(ticker, marcos, extra=0):
    from estrategia.fuente import velas_mt5

    return velas_mt5(ticker, marcos, extra)


def _referencia(estrategia, ticker, digits, semana, ahora, base):
    """La referencia semanal si existe (la que ya circuló); si no, se lee de nuevo sin vela en curso,
    así nunca queda en PRUEBA. No escribe en `referencias_semanales/`: el escáner es su dueño."""
    import referencia_semanal as rs

    guardada = rs.cargar(semana, ticker, base)
    if guardada is not None:
        crudo = json.loads(rs.ruta(semana, ticker, base).read_text(encoding="utf-8"))
        return guardada, datetime.fromisoformat(crudo["guardada"]), "semanal"
    lectura, momento = _propia(estrategia, ticker, digits, ahora)
    return lectura, momento, "propia"


def _propia(estrategia, ticker, digits, ahora):
    """Lectura nueva sin vela en curso (nunca queda en PRUEBA), fechada ahora."""
    import referencia_semanal as rs

    velas, _ = _velas(ticker, estrategia.marcos, rs.EXTRA)
    return estrategia.leer(ticker, velas, digits, None), ahora


def _lectura_actual(estrategia, ticker, digits, lector, ahora, referencia=None):
    import referencia_semanal as rs

    return rs.lectura_actual(estrategia, ticker, digits, lector, ahora, referencia=referencia)


@dataclass
class Lectores:
    contrato: Callable[[str, float], dict[str, Any]] = _contrato
    grafico_lectura: Callable[..., Path] = _grafico_lectura
    estrategia: Callable[[], Any] = _estrategia
    velas: Callable[..., Any] = _velas
    agenda: Callable[[datetime, str, str], Any] = _agenda
    hechos: Callable[..., tuple[list[dict[str, Any]], list[str]]] = _hechos
    rendir_calendario: Callable[[dict[str, Any], Path], Path] = _rendir_calendario
    curva: Callable[[], tuple[dict[str, Any], list[str]]] = _curva
    drivers: Callable[[str], list[str]] = _drivers
    cuenta: Callable[[], str | None] = _cuenta
    catalogo: Callable[[str], dict[str, Any]] = _catalogo_o_terminal
    base_referencias: Path | None = None
    registro: Path | None = None
    referencia: Callable[..., tuple[Any, datetime, str]] = _referencia
    propia: Callable[..., tuple[Any, datetime]] = _propia
    lectura_actual: Callable[..., tuple[Any, dict[str, Any]]] = _lectura_actual


@dataclass
class Preparada:
    pieza: dict[str, Any]
    avisos: list[str] = field(default_factory=list)


# ───────────────────────────────────────────────────────────── piezas


DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")


def fecha_corta(momento: datetime) -> str:
    m = momento.astimezone(SANTIAGO)
    # Con barra: el guion entre día y mes se ve como guion medio en la tipografía de la lámina.
    return f"{DIAS[m.weekday()]} {m:%d/%m}"


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
    lec.grafico_lectura(ticker, cat["nombre"], referencia, dir_pedido / grafico, digits=d,
                        niveles=niveles_lamina_semanal(referencia))
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


def _caducidad_de_la_semanal(referencia, estrategia, ticker, digits, ahora, lec: Lectores) -> str | None:
    """Si la referencia semanal ya cumple una condición de caducidad, el motivo; si no o si el terminal
    no responde, None (la semanal es la que circuló, y sin terminal no hay lectura propia que valga)."""
    from analista import vigencia as vg

    try:
        actual, velas = lec.lectura_actual(estrategia, ticker, digits, lec.velas, ahora, referencia=referencia)
    except Exception:  # noqa: BLE001  verificación extra: sin ella se usa la semanal, como antes
        return None
    return vg.motivo_caducidad(referencia, actual, velas[referencia.marco])


def preparar_oportunidad(orden: Orden, dir_pedido: Path, ahora: datetime, lec: Lectores) -> Preparada:
    """El análisis de UN activo: la lectura de nuestros sistemas, sus drivers y la agenda.

    La referencia es la semanal si el activo la tiene; si no, se lee de nuevo (spec 2026-10-16 §4).
    Las voces de bancos las agrega agy después; Python las valida (`fuentes.py`).
    """
    import referencia_semanal as rs

    ticker = orden.args["ticker"]
    estrategia = lec.estrategia()
    cat = lec.catalogo(ticker)
    digits = int(cat["digits"])
    base = lec.base_referencias or rs.DIR
    referencia, guardada, origen = lec.referencia(estrategia, ticker, digits, rs.semana_de(ahora), ahora, base)
    avisos: list[str] = []
    if origen == "semanal":
        motivo = _caducidad_de_la_semanal(referencia, estrategia, ticker, digits, ahora, lec)
        if motivo:
            # Un análisis creado sobre una referencia ya caducable lo caducaría el pedido siguiente y se
            # rehace sobre la misma referencia, gastando agy y cupo en cada pedido.
            referencia, guardada = lec.propia(estrategia, ticker, digits, ahora)
            origen = "propia"
            avisos.append(f"La referencia semanal de {ticker} ya no vale ({motivo}): usé una lectura nueva de hoy.")
    activo = _entrada_activo(ticker, referencia, guardada, 0.0, dir_pedido, lec, estrategia)
    if cat.get("fuera_catalogo"):
        avisos.append(f"{ticker} no está en el catálogo (activo fuera del catálogo): usé el nombre del terminal y "
                      "un marco genérico, sin drivers declarados.")
    from analista import agenda as ag

    nombre = activo["nombre"]
    agenda = lec.agenda(ahora, ticker, nombre)
    avisos += [f"agenda: {a}" for a in agenda.avisos]
    if agenda.estado == "sin_calendario":
        avisos.append(f"No pude leer el calendario económico: revisa los días clave en {ag.URL_CALENDARIO} "
                      "antes de enviar el correo.")
    elif agenda.estado == "vacia":
        avisos.append(ag.texto_vacia(agenda.a_dict()) + " La ficha muestra la ventana completa.")
    curva, av = lec.curva()
    avisos += [f"contexto sin curva de tasas: {a}" for a in av]
    hechos, av = lec.hechos(ticker, nombre, referencia.direccion, curva, agenda.eventos, ahora)
    avisos += [f"drivers del día: {a}" for a in av]
    if not hechos:
        avisos.append("No medí ningún driver del día: el contexto sale sin cifras propias.")
    drivers = lec.drivers(ticker)
    # Sin "%": la pieza no muestra porcentajes y una cifra con "%" en los datos invitaría a agy a citarla.
    limpio = _contexto_sin_porcentajes({"curva": _filas_curva(curva), "agenda": agenda.a_dict(), "hechos": hechos})
    imagenes = {ticker: activo["grafico"]}
    extra = {"titulares": [ticker], "contexto": [ticker]}
    if limpio["agenda"]["eventos"]:
        extra["dias_clave"] = [ticker]
        nombre_cal = f"calendario_{ticker.lower().replace('.', '_')}.png"
        try:
            lec.rendir_calendario(ag.payload_lamina(limpio["agenda"]), dir_pedido / nombre_cal)
            imagenes["calendario"] = nombre_cal
        except Exception as exc:  # noqa: BLE001  la tabla de la ficha sigue: la imagen es un extra
            avisos.append(f"No pude rendir la imagen del calendario ({exc.__class__.__name__}): la ficha lleva la tabla.")
    datos = {"ticker": ticker, "chip": "ANÁLISIS TÉCNICO Y FUNDAMENTAL",
             "edicion": fecha_corta(ahora) + f" · {ahora.astimezone(SANTIAGO):%H:%M}",
             "vigencia": {"desde": fecha_corta(ahora), "hasta": fecha_corta(ahora + rg.VIGENCIA)},
             "activos": [activo], "drivers": {ticker: drivers}, "hechos": limpio["hechos"],
             "agenda": limpio["agenda"], "curva": limpio["curva"],
             "fundamental": {"fuera_catalogo": bool(cat.get("fuera_catalogo")), "sin_drivers": not drivers,
                             "referencia": origen}}
    pieza = es.nueva_pieza("oportunidad", {"ticker": ticker}, datos, imagenes, extra_campos=extra)
    return Preparada(pieza, avisos)


def preparar_seguimiento(orden: Orden, dir_pedido: Path, ahora: datetime, lec: Lectores) -> Preparada:
    """El avance de un activo contra la foto: la simulación y la lectura de hoy, por separado."""
    import referencia_semanal as rs
    from estrategia.contrato import lectura_de_dict

    from analista import oportunidad as op
    from analista import seguimiento as sg

    ticker = orden.args["ticker"]
    vig = rg.vigente(ticker, ahora, lec.registro or rg.RUTA)  # un registro corrupto levanta: no es "sin análisis"
    if vig is None:
        raise SinAnalisisError(f"No hay un análisis vigente de {ticker}: pide primero /oportunidad {ticker}.")
    a = cargar_pieza(Path(vig["dir"]))["datos"]["activos"][0]
    esc = a["escenario"]
    # Sin simulación es un estado válido (el activo va igual al correo con su motivo): se
    # entrega la lectura de hoy y la simulación dice por qué no la hay.
    motivo = op.motivo_sin_simulacion(a)
    referencia_foto = lectura_de_dict(a["lectura"])
    estrategia = lec.estrategia()
    lectura, velas = lec.lectura_actual(estrategia, ticker, a["digits"], lec.velas, ahora, referencia=referencia_foto)
    reemplazada = rs.debe_reemplazar(referencia_foto, lectura)
    h4 = velas[referencia_foto.marco]
    posteriores = h4[h4["time"] > referencia_foto.vela].to_dict("records") if len(h4) else []
    ultima_cerrada = posteriores[-1]["time"] if posteriores else (int(h4.iloc[-1]["time"]) if len(h4) else int(referencia_foto.vela))
    vela_viva = None
    if len(h4):
        mas_nuevas = h4[h4["time"] > ultima_cerrada]
        if len(mas_nuevas):
            v_fila = mas_nuevas.iloc[-1]
            vela_viva = {"high": float(v_fila["high"]), "low": float(v_fila["low"])}
    if vela_viva is None:
        try:
            from market_data_mcp import mt5_client

            mt5_client.connect()
            import MetaTrader5 as mt5  # noqa: PLC0415

            mt5.symbol_select(ticker, True)
            rates = mt5.copy_rates_from_pos(ticker, mt5.TIMEFRAME_H4, 0, 1)
            if rates is not None and len(rates) > 0:
                r = rates[0]
                if int(r["time"]) > ultima_cerrada:
                    vela_viva = {"high": float(r["high"]), "low": float(r["low"])}
        except Exception:  # noqa: BLE001
            vela_viva = None
    precio = lectura.precio
    atr = float(referencia_foto.metricas.get("atr") or 0.0)
    tolerancia = sg.TOLERANCIA_ATR * atr
    ev = ({"estado": "sin_simulacion", "avance_pct": None, "motivo": motivo} if motivo
          else sg.evaluar(esc, posteriores, precio, vela_viva=vela_viva, tolerancia=tolerancia))
    lectura_hoy = sg.texto_lectura(lectura, reemplazada, a["digits"])
    hoy = fecha_corta(ahora)
    texto = sg.mensaje(a["nombre"], hoy, a["foto"]["fecha"], esc, ev, precio, lectura, reemplazada,
                       a["digits"])
    lec.grafico_lectura(ticker, a["nombre"], _sin_segundo_objetivo(lectura, not motivo),
                        dir_pedido / "grafico.png", digits=a["digits"],
                        niveles=niveles_lamina_seguimiento(esc, not motivo, lectura))
    datos = {"semana": rs.semana_de(ahora), "ticker": ticker, "nombre": a["nombre"], "evaluacion": ev, "precio_vivo": precio,
             "lectura_hoy": lectura_hoy, "reemplazada": reemplazada, "whatsapp": texto,
             "edicion": f"{hoy} · {ahora.astimezone(SANTIAGO):%H:%M}", "activo": a}
    pieza = es.nueva_pieza("seguimiento", {"ticker": ticker}, datos, {"principal": "grafico.png"})
    return Preparada(pieza, [])


def _contexto_sin_porcentajes(contexto: dict[str, Any]) -> dict[str, Any]:
    """El contexto de la pieza semanal sin "%".

    La pieza no muestra ningún porcentaje al prospecto (candado de `esquema`), y una
    cifra con "%" en los datos invitaría a agy a citarla y haría rechazar la pieza
    después de gastar la redacción.
    """
    def limpio(v: Any) -> Any:
        if isinstance(v, str):
            return v.replace(" %", " por ciento").replace("%", " por ciento")
        if isinstance(v, list):
            return [limpio(x) for x in v]
        if isinstance(v, dict):
            return {k: limpio(x) for k, x in v.items()}
        return v

    return limpio(contexto)


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
             lectores: Lectores | None = None, registro: Path | None = None) -> Preparada:
    """Escribe `pieza.json` y las imágenes sin texto en `dir_pedido`.

    `registro` es el registro semanal del bot: una sola fuente para los dos (antes cada uno
    tenía la suya, y con un registro inyectado el seguimiento miraba el real).
    """
    ahora = ahora or datetime.now(SANTIAGO)
    lec = lectores or Lectores()
    if registro is not None:
        lec = replace(lec, registro=registro)
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


