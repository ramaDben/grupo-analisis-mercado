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
        timeframe=pc.TIMEFRAME_GRAFICO,
        n_velas=pc.VELAS_GRAFICO_TV,
        soporte=pc._nivel_publicado(payload.get("soporte"), crudos.get("soporte")),
        resistencia=pc._nivel_publicado(payload.get("resistencia"), crudos.get("resistencia")),
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


def _serie_h1(ticker: str):
    """Las últimas 10.000 velas H1 cerradas del terminal, para la estadística del plan."""
    from market_data_mcp import mt5_client

    try:
        df = mt5_client.get_rates(ticker, "H1", 10000)
    except Exception as exc:  # noqa: BLE001
        raise PreparacionFallida(f"sin serie H1 de {ticker} para el plan ({exc})") from exc
    return df.iloc[:-1].reset_index(drop=True)


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


@dataclass
class Lectores:
    terminal: Callable[[str, datetime], dict[str, Any]] = _terminal
    grafico_tv: Callable[[dict[str, Any], Path], Path] = _grafico_tv
    jornada: Callable[[datetime], tuple[list[dict[str, Any]], list[str]]] = _jornada
    agenda: Callable[[datetime], tuple[list[dict[str, Any]], list[str]]] = _agenda
    movimiento: Callable[[str, datetime, datetime], dict[str, Any]] = _movimiento
    activos_jornada: Callable[[Path], tuple[dict[str, dict[str, Any]], list[str]]] = _activos_jornada
    curva: Callable[[], tuple[dict[str, Any], list[str]]] = _curva
    drivers: Callable[[str], list[str]] = _drivers
    cuenta: Callable[[], str | None] = _cuenta
    serie_h1: Callable[[str], Any] = _serie_h1


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
    import pipeline_carrusel as pc

    lectura = lec.terminal(orden.args["ticker"], ahora)
    try:
        payload = pc.construir_payload(lectura["seleccion"], lectura["activo"], ahora, lectura["cierres"])
    except pc.PayloadIncoherenteError as exc:
        raise PreparacionFallida(f"los datos del terminal no son coherentes ahora ({exc}); prueba en unos minutos") from exc
    except KeyError as exc:
        raise PreparacionFallida(f"al activo le falta {exc} en config/activos.json") from exc

    op = pc.lectura_operativa(payload)
    activo = lectura["activo"]
    plan = _plan(orden.args["ticker"], lectura, payload["sesgo"], activo, lec)
    precio = payload["precio_actual"]
    unidad = activo.get("unidad") or ""
    clase = CLASES.get(str(activo.get("categoria") or activo.get("clase") or "").lower(), "MERCADOS")
    lec.grafico_tv(payload, dir_pedido / "grafico.png")
    contexto, avisos_contexto = _contexto(orden.args["ticker"], ahora, lec)
    datos = {
        **_comunes(ahora, f"NOTA DE MERCADO · {clase}", "Cotización de referencia", f"{precio} {unidad}".strip()),
        "ticker": orden.args["ticker"],
        "nombre": activo["nombre"],
        "precio": precio,
        "soporte": payload["soporte"],
        "resistencia": payload["resistencia"],
        "direccion": payload["sesgo"],
        **op,
        "pie_imagen": f"{payload.get('rotulo_activo', activo['nombre'])} · velas de 1 hora · MetaTrader 5",
        "contexto": contexto,
        "plan": plan,
    }
    avisos = list(avisos_contexto)
    if payload.get("banda_estrecha"):
        avisos.append("niveles estrechos para la volatilidad del activo: ojo con los falsos quiebres")
    pieza = es.nueva_pieza("activo", orden.args, datos, {"principal": "grafico.png"})
    return Preparada(pieza, avisos)


def _plan(ticker: str, lectura: dict[str, Any], sesgo: str, activo: dict[str, Any], lec: Lectores) -> dict[str, Any]:
    """El plan de escenarios con su estadística: lo escribe Python y queda sellado en `datos`."""
    from analista import estadistica as est
    from analista import plan as plan_mod

    if "h1" not in lectura:
        raise PreparacionFallida("la lectura del terminal no trae el análisis H1 que necesita el plan")
    df = lec.serie_h1(ticker)
    ind = est.indicadores(df)
    ultima = plan_mod.ultima_vela(df, ind)
    digits = int(activo["digits"])
    alcista = sesgo == "Alcista"
    medida = est.medir(df, digits, alcista) if len(df) > est.VENTANA + est.HORIZONTE else None
    activacion = est.activacion_reciente(df, digits, alcista, ind) if len(df) > est.VENTANA else None
    return plan_mod.armar(lectura["h1"], digits, sesgo, activo["nombre"], medida, ultima, activacion)


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
    import screener_gi as sc
    from grafico_informe import formatear_precio

    momento = orden.args.get("momento") or _momento_por_hora(ahora)
    activos, avisos = lec.activos_jornada(dir_pedido)
    filas, imagenes = [], {}
    for ticker, info in activos.items():
        d1 = info.get("d1")
        if not d1 or not info.get("grafico"):
            continue
        dg = info["digits"]
        filas.append({
            "ticker": ticker, "nombre": info["nombre"],
            "precio": formatear_precio(d1["price"], dg),
            "soporte": formatear_precio(d1["s1"], dg),
            "resistencia": formatear_precio(d1["r1"], dg),
            "direccion": "Alcista" if sc.direccion_tecnica(d1) == "ALCISTA" else "Bajista",
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
}

# Piezas que leen precios del terminal: sin la cuenta declarada no salen.
CON_TERMINAL = {"activo", "dato", "jornada"}


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
