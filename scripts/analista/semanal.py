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


def _fmt(valor: float, digits: int) -> str:
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
    f = {"precio": _fmt(precio, digits), "gatillo": _fmt(gatillo, digits),
         "invalidacion": _fmt(invalidacion, digits), "recorrido": _fmt(recorrido, digits)}
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


def simular(contrato: dict[str, Any], esc: dict[str, Any], monto: float, volumen: float) -> dict[str, Any]:
    """Lo que el panel del correo calcula, en pesos (la cuenta del terminal es en CLP).

    `contrato["clp_unidad"]` son los pesos que mueve 1,0 de precio con 1 lote
    (`order_calc_profit`), y `margen_lote` el margen de 1 lote. El panel repite
    este cálculo en JavaScript; un test compara los dos.
    """
    vol = _ajustar_volumen(float(volumen), float(contrato["vol_min"]), float(contrato["vol_paso"]))
    valor_punto = float(contrato["clp_unidad"]) * vol
    nocional = valor_punto * float(esc["precio"])
    monto = float(monto or 0)
    return {
        "volumen": vol,
        "valor_punto": round(valor_punto),
        "margen": round(float(contrato["margen_lote"]) * vol),
        "nocional": round(nocional),
        "apalancamiento": round(nocional / monto, 2) if monto > 0 else None,
        "perdida_invalidacion": round(abs(float(esc["entrada"]) - float(esc["invalidacion"])) * valor_punto),
        "valor_recorrido": round(float(esc["recorrido"]) * valor_punto),
        "uno_pct_contra": round(0.01 * nocional),
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
