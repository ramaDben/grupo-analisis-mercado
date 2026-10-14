"""La agenda macro dentro del seguimiento: un dato de la semana como motivo para conversar.

Un seguimiento abre con el dato que se viene (o que acaba de salir) cuando ese dato mueve al activo,
porque una cita con hora es un enganche real y no una frase de relleno. Tres reglas lo mantienen
del lado de la información:

1. **El efecto sale del glosario, nunca de la redacción.** Un dato solo es relevante para un activo
   si `data/glosario_siglas.json` declara qué le hace (`si_sale_sobre_consenso`). Sin efecto
   declarado (cobre, Brent, cripto, USD/JPY) no hay párrafo macro: callarse es más honesto que
   inventar una correlación.
2. **El resultado se dice con el mismo peso en los dos sentidos**, atado al plan cuando está vivo
   («sobre lo esperado juega a favor, y lo contrario si sale bajo»). Jamás un pronóstico del dato.
3. **Se dice como se habla.** Un solo párrafo con su pregunta, «el dato del IPC de EE.UU. (índice de
   precios al consumidor)» y no el nombre institucional con sigla, sin viñetas ni precios, y con dos
   redacciones por momento: el mensaje que se lee como armado por un bot no sirve para conversar
   (gerencia, 2026-10-13).

Si el calendario no responde, no hay párrafo macro y el seguimiento sale como siempre.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

SANTIAGO = ZoneInfo("America/Santiago")

# El efecto declarado en el glosario se llama distinto en cada activo. Lo que no está acá no tiene
# reacción auditada y por eso no lleva párrafo macro.
CLAVE_DEL_ACTIVO = {"XAUUSD": "oro", "USDCLP": "usdclp", "US100.spot": "indices", "US500.spot": "indices",
                    "US30.spot": "indices", "WTI.spot": "petroleo"}
# La palabra con que el ejecutivo pide cada uno: el aviso aparte le dice qué volver a pedir.
ALIAS_DEL_BOT = {"XAUUSD": "oro", "USDCLP": "dolar", "US100.spot": "nasdaq", "US500.spot": "sp500",
                 "US30.spot": "dow", "WTI.spot": "petroleo"}
PAISES = {"United States": "de EE.UU.", "Chile": "de Chile", "China": "de China", "Euro Zone": "de la Zona Euro",
          "Euro Area": "de la Zona Euro", "Zona Euro": "de la Zona Euro"}
DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")

MINUTOS_VENTANA = 30        # faltando tan poco, el precio ya se mueve a saltos
HORAS_PUBLICADO = 3         # un dato de hace más de esto ya no es noticia
DIAS_HORIZONTE = 7


def eventos_de_la_semana(ahora: datetime) -> list[dict[str, Any]]:
    """Los datos de alto impacto de la semana; vacío si el calendario no responde."""
    try:
        from market_data_mcp.tools.calendar import cargar_calendario

        res = cargar_calendario(solo_hoy=False, min_impact="high", ahora=ahora)
    except Exception:  # noqa: BLE001  el calendario es un extra: nunca rompe el seguimiento
        return []
    return [] if "error" in res else list(res.get("eventos") or [])


def _cuando(ev: dict[str, Any]) -> datetime | None:
    try:
        return datetime.strptime(ev["hora_servidor"], "%Y-%m-%d %H:%M").replace(tzinfo=SANTIAGO)
    except (KeyError, ValueError):
        return None


def _prioridad(estado: str, cuando: datetime, tier: int, ahora: datetime) -> tuple:
    orden = {"ventana": 0, "pendiente": 1, "publicado": 2, "proximo": 3}[estado]
    # Entre los publicados manda el más reciente; entre los pendientes, el más cercano.
    return (orden, tier, -cuando.timestamp() if estado == "publicado" else cuando.timestamp())


def contexto(ticker: str, ahora: datetime, eventos: list[dict[str, Any]]) -> dict[str, Any] | None:
    """El dato que corresponde mencionar para este activo ahora, o None."""
    clave = CLAVE_DEL_ACTIVO.get(ticker)
    if clave is None:
        return None
    ahora = ahora.astimezone(SANTIAGO)
    elegido = None
    for ev in eventos:
        dic = ev.get("diccionario") or {}
        verbo = (dic.get("si_sale_sobre_consenso") or {}).get(clave)
        cuando = _cuando(ev)
        if ev.get("impacto") != "alto" or verbo not in ("sube", "baja") or cuando is None:
            continue
        if str(ev.get("actual") or "").strip():
            if cuando > ahora or ahora - cuando > timedelta(hours=HORAS_PUBLICADO):
                continue
            estado = "publicado"
        elif cuando <= ahora:
            continue  # ya pasó la hora y el resultado todavía no está: no se afirma nada
        elif cuando - ahora <= timedelta(minutes=MINUTOS_VENTANA):
            estado = "ventana"
        elif cuando.date() == ahora.date():
            estado = "pendiente"
        elif cuando - ahora <= timedelta(days=DIAS_HORIZONTE):
            estado = "proximo"
        else:
            continue
        pri = _prioridad(estado, cuando, int(dic.get("tier") or 9), ahora)
        if elegido is None or pri < elegido[0]:
            elegido = (pri, {"estado": estado, "evento": ev, "cuando": cuando, "verbo": verbo, "clave": clave,
                             "ticker": ticker})
    return elegido[1] if elegido else None


# ───────────────────────────────────────────────────────────── redacción


def _el(clave: str, nombre: str) -> str:
    return {"oro": "el oro", "usdclp": "el USD/CLP", "petroleo": "el petróleo"}.get(clave, f"el {nombre}")


def _dato(ev: dict[str, Any]) -> str:
    """El dato como se dice en voz alta: «el dato del IPC de EE.UU. (índice de precios al consumidor)».

    La sigla va primero y su nombre completo entre paréntesis, una sola vez: el nombre institucional
    entero con sigla es lo que ningún ejecutivo escribe en un chat (gerencia, 2026-10-13). «El dato
    del» evita el género de la sigla.
    """
    import re

    nombre = (ev.get("diccionario") or {}).get("nombre_es") or ev.get("nombre", "")
    pais = PAISES.get(ev.get("pais", ""), "de " + str(ev.get("pais", "")))
    m = re.search(r"\(([^)]+)\)\s*$", nombre)
    base = re.sub(r"\s*\([^)]*\)\s*$", "", nombre).strip()
    base = base[:1].lower() + base[1:]
    return f"el dato del {m.group(1)} {pais} ({base})" if m else f"el dato de {base} {pais}"


def _cuando_txt(cuando: datetime, ahora: datetime) -> str:
    dias = (cuando.date() - ahora.date()).days
    return "hoy" if dias == 0 else "mañana" if dias == 1 else f"el {DIAS[cuando.weekday()]}"


def _num(texto: Any) -> float | None:
    """La cifra de la fuente (notación estadounidense, con %, K, M, B) como número, o None."""
    limpio = "".join(c for c in str(texto or "") if c.isdigit() or c in "-.")
    try:
        return float(limpio)
    except ValueError:
        return None


def _cifra(texto: Any) -> str:
    from pipeline_informe import _cifra_es

    cifra = _cifra_es(str(texto or "").strip())
    return cifra[:-1] + " %" if cifra.endswith("%") else cifra  # «0,4 %», como el resto del seguimiento


def _opuesto(verbo: str) -> str:
    return "bajar" if verbo == "subir" else "subir"


def _plan_vivo(esc: dict[str, Any] | None, estado_sim: str) -> dict[str, str] | None:
    """Con la simulación viva, las palabras del plan; sin ella (cerrada, descartada, sin plan), None."""
    if not esc or estado_sim not in ("entrada_pendiente", "en_curso"):
        return None
    return {"accion": "compra" if esc["direccion"] == "ALCISTA" else "venta",
            "estado": "todavía en espera" if estado_sim == "entrada_pendiente" else "en curso",
            "alcista": esc["direccion"] == "ALCISTA"}


def _efectos(ctx: dict[str, Any], plan: dict[str, Any] | None) -> dict[str, str]:
    """Qué hace el dato con el activo y, si hay plan vivo, con él. Cada resultado nombrado con su lado."""
    sobre = "subir" if ctx["verbo"] == "sube" else "bajar"
    ef = {"v1": sobre, "v2": _opuesto(sobre)}
    if plan:
        favorece = (ctx["verbo"] == "sube") == plan["alcista"]
        ef["sobre"], ef["bajo"] = ("a favor", "en contra") if favorece else ("en contra", "a favor")
    return ef


# Cada mensaje es un solo párrafo que cierra con una pregunta concreta: tres bloques apilados con un
# cierre genérico delatan al bot. Una variante por día y activo (estable), elegida por `variante`.
CON_PLAN = {
    "pendiente": (
        "{cuando} a las {hora} sale {dato} y suele mover {el}. Con la {accion} del {dia} {estado}, si sale "
        "sobre lo esperado juega {sobre}, y lo contrario si sale bajo. Con CFD se puede operar "
        "cualquiera de los dos movimientos. ¿Lo miramos juntos cuando salga?",
        "te escribo porque {cuando} a las {hora} se conoce {dato}, que suele mover {el}. Para la {accion} del "
        "{dia}, un resultado sobre lo esperado juega {sobre} y uno bajo lo esperado, {bajo}; con CFD se opera "
        "hacia ambos lados. ¿Hablamos cuando salga?",
    ),
    "proximo": (
        "{cuando} a las {hora} sale {dato} y suele mover {el}. Para la {accion} del {dia} {estado}, un "
        "resultado sobre lo esperado juega {sobre} y uno bajo lo esperado, {bajo}. Con CFD se puede operar "
        "cualquiera de los dos movimientos. ¿Lo vemos antes?",
        "te aviso que {cuando} a las {hora} se conoce {dato}, que suele mover {el}. Con la {accion} del {dia} "
        "{estado}, sobre lo esperado juega {sobre} y bajo lo esperado, {bajo}, y con CFD se opera hacia ambos "
        "lados. ¿Lo conversamos?",
    ),
}
SIN_PLAN = {
    "pendiente": (
        "{cuando} a las {hora} sale {dato} y suele mover {el}: si sale sobre lo esperado tiende a {v1}, y lo "
        "contrario si sale bajo. Con CFD se puede operar cualquiera de los dos movimientos. ¿Lo miramos "
        "juntos cuando salga?",
        "te escribo porque {cuando} a las {hora} se conoce {dato}, que suele mover {el}. Sobre lo esperado "
        "tiende a {v1}; bajo lo esperado, a {v2}, y con CFD se opera hacia ambos lados. ¿Hablamos cuando salga?",
    ),
    "proximo": (
        "{cuando} a las {hora} sale {dato} y suele mover {el}: sobre lo esperado tiende a {v1}, y bajo lo "
        "esperado, a {v2}. Con CFD se puede operar cualquiera de los dos movimientos. ¿Lo vemos antes?",
        "te aviso que {cuando} a las {hora} se conoce {dato}, que suele mover {el}. Sobre lo esperado tiende "
        "a {v1} y bajo lo esperado, a {v2}; con CFD se opera hacia ambos lados. ¿Lo conversamos?",
    ),
}
VENTANA = (
    "en unos minutos, a las {hora}, sale {dato}, y mientras el mercado lo absorbe el precio suele moverse a "
    "saltos. {coletilla} y lo revisamos con calma apenas pase. ¿Te parece?",
    "a las {hora} sale {dato}, y en ese rato el precio puede moverse a saltos. {coletilla}; cuando pase lo "
    "miramos con calma. ¿Hablamos?",
)
PUBLICADO = (
    "ya salió {dato}: {cifras}{comparacion}.{efecto} ¿Te cuento cómo queda la lectura?",
    "salió {dato} y {cifras}{comparacion}.{efecto} ¿Lo revisamos en la lámina?",
)


def _publicado(ctx: dict[str, Any], nombre: str, plan: dict[str, Any] | None, dia: str, variante: int) -> str:
    ev = ctx["evento"]
    actual, previsto = str(ev.get("actual") or "").strip(), str(ev.get("forecast") or "").strip()
    a, p = _num(actual), _num(previsto)
    lado = None if a is None or p is None else ("sobre" if a > p else "bajo" if a < p else "linea")
    comparacion = {"sobre": ", sobre lo esperado", "bajo": ", bajo lo esperado",
                   "linea": ", en línea con lo esperado", None: ""}[lado]
    cifras = f"{_cifra(actual)} frente a {_cifra(previsto)} esperado" if previsto else _cifra(actual)
    efecto = ""
    if lado in ("sobre", "bajo"):
        sobre = "subir" if ctx["verbo"] == "sube" else "bajar"
        verbo = sobre if lado == "sobre" else _opuesto(sobre)
        efecto = f" Con un dato así, {_el(ctx['clave'], nombre)} tiende a {verbo}"
        if plan:
            sube_activo = verbo == "subir"
            efecto += f", lo que juega {'a favor' if sube_activo == plan['alcista'] else 'en contra'} de la " \
                      f"{plan['accion']} del {dia}"
        efecto += "."
    plantilla = PUBLICADO[variante % len(PUBLICADO)]
    return plantilla.format(dato=_dato(ev), cifras=cifras, comparacion=comparacion, efecto=efecto)


def redactar(ctx: dict[str, Any], nombre: str, esc: dict[str, Any] | None, estado_sim: str,
             ahora: datetime, digits: int, variante: int = 0, dia: str = "lunes") -> dict[str, Any]:
    """El cuerpo del mensaje cuando hay dato macro (un párrafo con su pregunta) y el aviso al ejecutivo."""
    ahora = ahora.astimezone(SANTIAGO)
    ev, cuando, estado = ctx["evento"], ctx["cuando"], ctx["estado"]
    el, plan = _el(ctx["clave"], nombre), _plan_vivo(esc, estado_sim)
    base = {"dato": _dato(ev), "hora": f"{cuando:%H:%M}", "el": el, "dia": dia,
            "cuando": _cuando_txt(cuando, ahora), **_efectos(ctx, plan), **(plan or {})}
    salida = {"cuerpo": "", "aparte": ""}

    if estado == "publicado":
        salida["cuerpo"] = _publicado(ctx, nombre, plan, dia, variante)
        return salida
    if estado == "ventana":
        coletilla = (f"Te dejo cómo va la {plan['accion']} del {dia}" if plan else f"Te dejo cómo va {el}")
        salida["cuerpo"] = VENTANA[variante % len(VENTANA)].format(coletilla=coletilla, **base)
    else:
        clave = "pendiente" if estado == "pendiente" else "proximo"
        opciones = (CON_PLAN if plan else SIN_PLAN)[clave]
        salida["cuerpo"] = opciones[variante % len(opciones)].format(**base)
    if estado in ("pendiente", "ventana"):
        alias = ALIAS_DEL_BOT.get(ctx["ticker"], ctx["ticker"].lower())
        salida["aparte"] = (f"Tip: cuando salga el dato ({cuando:%H:%M}), vuelve a pedir /seguimiento {alias} "
                            "y el mensaje ya contará cómo salió.")
    return salida
