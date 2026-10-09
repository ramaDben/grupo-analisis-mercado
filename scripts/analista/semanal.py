"""La pieza semanal comercial: el escenario de la semana en diario y su simulación.

Es material de venta del área comercial (correo para Outlook, imagen y texto de
WhatsApp), pero el análisis sigue las reglas del informe: lo escribe Python con
datos del terminal y agy solo redacta el contexto. Tres decisiones del director
(2026-10-09) que no conviene revertir:

1. **Visión diaria, no de una hora.** La pieza vale toda la semana: el escenario
   se arma con velas D1 y lo dice con su temporalidad.
2. **El análisis es de Benjamín y la simulación del ejecutivo.** El escenario
   (gatillo, invalidación, recorrido) es igual para todos; el monto y el volumen
   los pone el ejecutivo en el panel del correo y salen rotulados con su nombre.
3. **Sin objetivo de precio.** El recorrido es una distancia (1,5 ATR diario),
   igual que en el plan del informe de activo, y la pérdida a la invalidación se
   muestra del mismo tamaño y al lado de lo que vale el recorrido.
"""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from analista.estadistica import CHANDELIER_K, MULT_RECORRIDO

SANTIAGO = ZoneInfo("America/Santiago")

TEMPORALIDAD = "1D · posicional (días a semanas)"
POR_QUE_1D = ("La pieza acompaña toda la semana: el gráfico diario deja fuera el ruido de las "
              "horas y muestra la tendencia que ordena los próximos días.")
AVISO_CORTO = "Análisis informativo. No constituye recomendación de inversión."
# Una ruptura cuenta como activación del escenario si ocurrió en la última semana
# de mercado; una más vieja ya es historia y el gatillo pasa al nivel siguiente.
VENTANA_ACTIVACION = 5


def lunes_de(ahora: datetime) -> date:
    """El lunes de la semana de `ahora`, en hora de Chile: identifica la pieza semanal."""
    local = ahora.astimezone(SANTIAGO).date()
    return local - timedelta(days=local.weekday())


def fmt(valor: float, digits: int) -> str:
    import pipeline_carrusel as pc

    return pc.formatear_precio(valor, digits)


def ruptura_semana(df, digits: int, alcista: bool):
    """La última ruptura diaria a favor de la tendencia, como `(nivel, índice)`, o None."""
    from analista import estadistica as est

    if len(df) <= est.VENTANA:
        return None
    return est.ultima_ruptura(df, digits, alcista, est.indicadores(df))


def escenario(d1: dict[str, Any], df, digits: int, ruptura: tuple[float, int] | None = None) -> dict[str, Any]:
    """El escenario de la semana a favor de la tendencia diaria (precio contra la EMA 50 de D1).

    `d1` es `analizar_activo(ticker, "D1")` y `df` las velas diarias cerradas.
    `ruptura` es `ruptura_semana(...)`: solo cuenta si ocurrió en las últimas
    `VENTANA_ACTIVACION` velas.
    """
    from analista import estadistica as est
    from analista import plan

    precio = float(d1["price"])
    alcista = precio > float(d1["ema_50"])
    sesgo = "Alcista" if alcista else "Bajista"
    clave = "r1" if alcista else "s1"
    activacion = None
    if ruptura is not None and ruptura[1] >= len(df) - VENTANA_ACTIVACION:
        activacion = float(ruptura[0])
    if activacion is None and d1.get("niveles_origen", {}).get(clave) != "swing":
        return {"hay_escenario": False, "sesgo": sesgo,
                "motivo": "Esta semana el activo no tiene una estructura de precio medible a favor de "
                          "su tendencia diaria: sin ese nivel no hay escenario que plantear."}

    ind = est.indicadores(df)
    ultima = plan.ultima_vela(df, ind)
    k_atr = CHANDELIER_K * ultima["atr22"]
    invalidacion = ultima["hh22"] - k_atr if alcista else ultima["ll22"] + k_atr
    gatillo = activacion if activacion is not None else float(d1[clave])
    recorrido = MULT_RECORRIDO * float(d1["atr_14"])
    anulado = precio < invalidacion if alcista else precio > invalidacion
    if anulado and activacion is None:
        return {"hay_escenario": False, "sesgo": sesgo,
                "motivo": "El precio ya está del otro lado de la invalidación diaria: no hay "
                          "escenario limpio que plantear esta semana."}
    estado = "invalidado" if anulado else ("activado" if activacion is not None else "armado")
    lado, borde = ("sobre", "bajo") if alcista else ("bajo", "sobre")
    f = {"precio": fmt(precio, digits), "gatillo": fmt(gatillo, digits),
         "invalidacion": fmt(invalidacion, digits), "recorrido": fmt(recorrido, digits)}
    textos = {
        "gatillo": f"El escenario {sesgo.lower()} se activa con un cierre diario {lado} {f['gatillo']}.",
        "invalidacion": f"Se anula con un cierre diario {borde} {f['invalidacion']}. Es una salida por "
                        "volatilidad, que se ajusta a favor a medida que el precio avanza.",
        "recorrido": f"Recorrido de referencia: unos {f['recorrido']}, 1,5 veces la volatilidad típica de "
                     "un día. Es una distancia, no un objetivo de precio.",
        "estado": {
            "armado": "Armado: el precio todavía no cruza el gatillo.",
            "activado": f"Activado: un cierre diario de esta semana cruzó {lado} el gatillo.",
            "invalidado": "Invalidado: tras activarse, el precio quedó del otro lado de la invalidación.",
        }[estado],
    }
    return {
        "hay_escenario": True, "sesgo": sesgo, "estado": estado,
        "precio": precio, "gatillo": round(gatillo, digits), "invalidacion": round(invalidacion, digits),
        "recorrido": round(recorrido, digits),
        "entrada": round(gatillo, digits) if estado == "armado" else precio,
        "vela": str(ultima["vela"]), "fmt": f, "textos": textos,
    }


def _ajustar_volumen(volumen: float, minimo: float, paso: float) -> float:
    if volumen <= minimo:
        return minimo
    pasos = int((volumen - minimo) / paso + 1e-9)
    return round(minimo + pasos * paso, 8)


def _redondear(valor: float) -> int:
    """Mitad hacia arriba, como `Math.round` del panel: `round` de Python va al par
    (218,5 da 218) y el correo mostraría un peso distinto del que calcula el panel."""
    return math.floor(valor + 0.5)


def simular(contrato: dict[str, Any], esc: dict[str, Any], monto: float, volumen: float) -> dict[str, Any]:
    """Lo que el panel del correo calcula, en pesos (la cuenta del terminal es en CLP).

    `contrato["clp_unidad"]` son los pesos que mueve 1,0 de precio con 1 lote
    (`order_calc_profit`), y `margen_lote` el margen de 1 lote. El panel repite
    este cálculo en JavaScript; un test compara los dos.
    """
    r = _redondear
    vol = _ajustar_volumen(float(volumen), float(contrato["vol_min"]), float(contrato["vol_paso"]))
    valor_punto = float(contrato["clp_unidad"]) * vol
    nocional = valor_punto * float(esc["precio"])
    monto = float(monto or 0)
    return {
        "volumen": vol,
        "valor_punto": r(valor_punto),
        "margen": r(float(contrato["margen_lote"]) * vol),
        "nocional": r(nocional),
        "apalancamiento": r(nocional / monto * 100) / 100 if monto > 0 else None,
        "perdida_invalidacion": r(abs(float(esc["entrada"]) - float(esc["invalidacion"])) * valor_punto),
        "valor_recorrido": r(float(esc["recorrido"]) * valor_punto),
        "uno_pct_contra": r(0.01 * nocional),
    }


def mensaje_whatsapp(pieza: dict[str, Any]) -> str:
    """El texto que acompaña la imagen: lo redactado por agy y las cifras en negrita."""
    d = pieza["datos"]
    esc = d["escenario"]
    f = esc["fmt"]
    alcista = esc["sesgo"] == "Alcista"
    flecha, lado, borde = ("⬆️", "sobre", "bajo") if alcista else ("⬇️", "bajo", "sobre")
    lineas = [
        f"📊 *{d['nombre']} · {d['ticker_visible']}* · Escenario de la semana",
        f"📌 Precio de referencia: *{d['precio']}*",
        "",
        pieza["editorial"]["whatsapp"].strip(),
        "",
        f"{flecha} Se activa con un cierre diario {lado} *{f['gatillo']}*",
        f"⚠️ Se anula con un cierre diario {borde} *{f['invalidacion']}*",
        f"↔️ Recorrido de referencia: unos *{f['recorrido']}* (una distancia, no un objetivo)",
        f"⏱️ {d['temporalidad']}",
        "",
        f"Datos al {d['datos_al']}. _{AVISO_CORTO}_",
    ]
    return "\n".join(lineas)


# ───────────────────────────────────────────────────────────── utilidades de la pieza

MONTO_BASE = 1_000_000  # pesos: el monto con que abre el panel del correo


def colores_marca() -> dict[str, str]:
    """Los hex de `templates/stories/marca.css` por rol (`sube`, `baja`, `aviso`...).

    El correo no puede usar `var()` (Outlook no lo entiende) y el gráfico tampoco:
    los colores se leen de la hoja para que la fuente única siga siendo una.
    """
    import re

    from analista import RAIZ

    hoja = (RAIZ / "templates" / "stories" / "marca.css").read_text(encoding="utf-8")
    return {m.group(1): m.group(2) for m in re.finditer(r"--([\w-]+):\s*(#[0-9A-Fa-f]{6})\b", hoja)}


DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")


def datos_al(ahora: datetime) -> str:
    """'jueves 08-10 · 11:00 CLST': la fecha de los datos, visible en las tres salidas."""
    import pipeline_avisos as pa

    local = ahora.astimezone(SANTIAGO)
    return f"{DIAS[local.weekday()]} {local:%d-%m} · {pa.etiqueta_hora(local)}"


def pct_es(valor: float) -> str:
    return f"{valor:+.1f}".replace(".", ",") + " %"


def variacion_semana(df, precio: float, lunes: date, digits: int) -> str:
    """Cuánto lleva el activo desde el cierre de la semana pasada, o 'sin dato'."""
    import pandas as pd

    previas = df[pd.to_datetime(df["time"]).dt.date < lunes]
    if previas.empty:
        return "sin dato"
    ref = float(previas["close"].iat[-1])
    return f"{pct_es(100 * (precio / ref - 1))} desde el cierre de la semana pasada ({fmt(ref, digits)})"


# ───────────────────────────────────────────────────────────── seguimiento diario

ESTADOS = ("vigente", "avanzando", "completado", "invalidado")
SELLOS = {"vigente": "VIGENTE", "avanzando": "AVANZANDO", "completado": "COMPLETADO",
          "invalidado": "INVALIDADO"}


def evaluar(esc: dict[str, Any], velas, precio_vivo: float) -> dict[str, Any]:
    """El estado del escenario de la semana frente a lo que hizo el precio desde la foto.

    `velas` son las velas DIARIAS cerradas posteriores a la vela de la foto, en
    orden; `precio_vivo` es el precio de ahora (la vela del día en curso).
    Mismas reglas que la pieza: activa y anula un CIERRE diario; el recorrido se
    cuenta cumplido apenas el precio lo toca. Si en la misma vela cierra del otro
    lado de la invalidación y toca el recorrido, gana la invalidación: sin datos
    intravela no se sabe qué pasó primero, y se cuenta lo que perjudica (igual que
    `estadistica.desenlace`). La invalidación es la de la foto: el seguimiento
    mide el escenario que se comunicó, no uno recalculado.
    """
    alcista = esc["sesgo"] == "Alcista"
    signo = 1 if alcista else -1
    activado = esc.get("estado") == "activado"
    entrada = float(esc["entrada"])
    gatillo, inval, rec = float(esc["gatillo"]), float(esc["invalidacion"]), float(esc["recorrido"])

    def mas_alla(valor: float, nivel: float) -> bool:
        return (valor - nivel) * signo > 0

    def objetivo() -> float:
        return entrada + signo * rec

    estado = None
    for _, v in velas.iterrows() if hasattr(velas, "iterrows") else enumerate(velas):
        cierre, alto, bajo = float(v["close"]), float(v["high"]), float(v["low"])
        extremo = alto if alcista else bajo
        if not activado:
            if mas_alla(cierre, gatillo):
                activado, entrada = True, gatillo
                if mas_alla(extremo, objetivo()) or extremo == objetivo():
                    estado = "completado"
                    break
            elif mas_alla(inval, cierre):
                estado = "invalidado"
                break
            continue
        if mas_alla(inval, cierre):
            estado = "invalidado"
            break
        if mas_alla(extremo, objetivo()) or extremo == objetivo():
            estado = "completado"
            break
    if estado is None:
        if activado and (mas_alla(precio_vivo, objetivo()) or precio_vivo == objetivo()):
            estado = "completado"
        else:
            estado = "avanzando" if activado else "vigente"
    avance = round(100 * signo * (precio_vivo - entrada) / rec) if rec and activado else None
    if estado == "completado":
        avance = 100
    return {"estado": estado, "activado": activado, "entrada": entrada, "avance_pct": avance}


def textos_seguimiento(esc: dict[str, Any], ev: dict[str, Any], precio_vivo: float, digits: int,
                       ticker: str, dia: str) -> dict[str, str]:
    """Las frases fijas del estado, con sus cifras en negrita de WhatsApp.

    Los cuatro estados se cuentan con el mismo peso y ninguno se vende: nunca
    "si hubieras entrado", nunca una ganancia (criterio 11 del plan).
    """
    import pipeline_carrusel as pc

    f = esc["fmt"]
    alcista = esc["sesgo"] == "Alcista"
    lado, borde = ("sobre", "bajo") if alcista else ("bajo", "sobre")
    hoy = fmt(precio_vivo, digits)
    avance = ev.get("avance_pct")
    opciones = {
        "vigente": (
            f"El escenario sigue *VIGENTE*: el precio, en *{hoy}*, todavía no cierra {lado} *{f['gatillo']}*.",
            f"*VIGENTE*: sin activarse aún. El precio está en *{hoy}* y la activación sigue en *{f['gatillo']}*.",
        ),
        "avanzando": (
            f"El escenario está *AVANZANDO*: se activó y el precio, en *{hoy}*, lleva el *{avance} %* del recorrido de referencia.",
            f"*AVANZANDO*: activado, con el precio en *{hoy}* y el *{avance} %* del recorrido de referencia hecho.",
        ),
        "completado": (
            f"El escenario quedó *COMPLETADO*: el precio cubrió el recorrido de referencia de *{f['recorrido']}*. Hoy está en *{hoy}*.",
            f"*COMPLETADO*: el recorrido de referencia de *{f['recorrido']}* se cumplió. El precio está en *{hoy}*.",
        ),
        "invalidado": (
            f"El escenario quedó *INVALIDADO*: hubo un cierre diario {borde} *{f['invalidacion']}*. El precio está en *{hoy}*.",
            f"*INVALIDADO*: un cierre diario {borde} *{f['invalidacion']}* anuló el escenario. Hoy el precio está en *{hoy}*.",
        ),
    }[ev["estado"]]
    if ev["estado"] == "avanzando" and avance is not None and avance < 0:
        opciones = (f"El escenario está *AVANZANDO* sin invalidarse, pero el precio, en *{hoy}*, volvió "
                    f"{borde} el nivel de activación. La invalidación sigue en *{f['invalidacion']}*.",)
    return {"estado": pc.elegir_variante(opciones, ticker, dia, ev["estado"]),
            "referencia": f"Precio del lunes: *{f['precio']}* · hoy: *{hoy}*"}


def mensaje_seguimiento(pieza: dict[str, Any]) -> str:
    """'Te envío una actualización': estado y cifras de Python, lo de hoy de agy."""
    d = pieza["datos"]
    lineas = [
        f"📊 *{d['nombre']} · {d['ticker_visible']}* · Actualización del escenario de la semana",
        "",
        d["textos"]["estado"],
        d["textos"]["referencia"],
        "",
        f"📅 Lo de hoy: {pieza['editorial']['hoy'].strip()}",
        "",
        f"⏱️ {TEMPORALIDAD}",
        f"Datos al {d['datos_al']}. _{AVISO_CORTO}_",
    ]
    return "\n".join(lineas)


# ───────────────────────────────────────────────────────────── temáticas del lunes

# Las cinco plantillas que pidió el área comercial. Oro y USD/CLP son un activo;
# índices, ETF y acciones eligen cada semana el suyo dentro de su clase.
LOTE = ("oro", "usdclp", "indices", "etf", "acciones")
CLASE_DE_TEMATICA = {"indices": "indices", "etf": "etfs", "acciones": "acciones"}
NOMBRE_TEMATICA = {"indices": "índices", "etf": "ETF", "acciones": "acciones"}


def elegir(universo: list[dict[str, Any]], leer_d1, leer_serie) -> dict[str, Any] | None:
    """El activo de la clase con el escenario semanal más claro, o None si ninguno tiene.

    Mismo orden que el foco técnico (`foco.seleccionar`): puntos técnicos más
    momentum, y a igualdad, el más cerca de su gatillo en ATR. Pero en DIARIO y
    sin los gates de la jornada (agotamiento, blackout): la pieza vale la semana.
    Un activo sin escenario o con el escenario ya invalidado no compite.
    """
    import screener_gi as sc

    candidatos = []
    for activo in universo:
        t = activo["ticker"]
        try:
            d1, df = leer_d1(t), leer_serie(t)
            digits = int(activo["digits"])
            alcista = float(d1["price"]) > float(d1["ema_50"])
            esc = escenario(d1, df, digits, ruptura_semana(df, digits, alcista))
            if not esc["hay_escenario"] or esc["estado"] == "invalidado":
                continue
            direccion = "ALCISTA" if alcista else "BAJISTA"
            puntos = sc.factor_tecnico(d1, d1, direccion)[0] + sc.factor_momentum(d1, direccion)[0]
            atr = float(d1["atr_14"]) or float("inf")
        except Exception:  # noqa: BLE001
            # Un activo con datos rotos se salta: no puede tumbar la elección de los demás.
            continue
        clave = (-puntos, abs(esc["precio"] - esc["gatillo"]) / atr, t)
        candidatos.append((clave, {"ticker": t, "d1": d1, "serie": df}))
    if not candidatos:
        return None
    _, elegido = min(candidatos, key=lambda c: c[0])
    return {**elegido, "evaluados": len(universo)}
