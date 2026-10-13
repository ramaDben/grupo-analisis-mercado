"""La agenda macro dentro del seguimiento: un dato de la semana como motivo para conversar.

Un seguimiento abre con el dato que se viene (o que acaba de salir) cuando ese dato mueve al activo,
porque una cita con hora es un enganche real y no una frase de relleno. Tres reglas lo mantienen
del lado de la información:

1. **El efecto sale del glosario, nunca de la redacción.** Un dato solo es relevante para un activo
   si `data/glosario_siglas.json` declara qué le hace (`si_sale_sobre_consenso`). Sin efecto
   declarado (cobre, Brent, cripto, USD/JPY) no hay párrafo macro: callarse es más honesto que
   inventar una correlación.
2. **La reacción es condicional y simétrica.** «Si sale sobre lo esperado… si sale bajo lo esperado…»,
   con el mismo peso para el camino al objetivo y el camino al stop. Jamás un pronóstico del dato.
3. **Con un dato pendiente no se invita a tomar posición.** El mensaje quita la frase de «aún hay
   espacio» y deja una cautela factual: entrar justo antes de un dato fuerte es la lectura que el
   proyecto no quiere sugerir.

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
HORAS_SIN_INVITAR = 24      # un dato a menos de un día quita la invitación a tomar posición
DIAS_HORIZONTE = 7

CIERRES_PENDIENTE = (
    "¿Lo vemos juntos cuando salga el dato?",
    "Cuando salga el dato, lo revisamos juntos si quieres.",
)
CIERRE_VENTANA = "Lo revisamos con calma cuando pase."


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
    """«el dato X de EE.UU.»: sin artículo del nombre, que cambia de género de un dato a otro. Sin
    comillas angulares: nadie las escribe a mano en WhatsApp y delatan texto armado (director, 2026-10-13)."""
    nombre = (ev.get("diccionario") or {}).get("nombre_es") or ev.get("nombre", "")
    return f"el dato {nombre} {PAISES.get(ev.get('pais', ''), 'de ' + str(ev.get('pais', '')))}"


def _cuando_txt(cuando: datetime, ahora: datetime) -> str:
    hora = f"{cuando:%H:%M} (hora de Chile)"
    dias = (cuando.date() - ahora.date()).days
    return f"hoy a las {hora}" if dias == 0 else f"mañana a las {hora}" if dias == 1 \
        else f"el {DIAS[cuando.weekday()]} a las {hora}"


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


def _reaccion(ctx: dict[str, Any], nombre: str, esc: dict[str, Any] | None, vivo: bool, fmt_stop: str) -> str:
    """Los dos caminos, con el mismo peso. Con la simulación viva, dice cuál va a favor y cuál al stop."""
    el = _el(ctx["clave"], nombre)
    sobre = "subir" if ctx["verbo"] == "sube" else "bajar"
    bajo = _opuesto(sobre)
    if not (vivo and esc):
        return f"Si sale sobre lo esperado, {el} tiende a {sobre}; si sale bajo lo esperado, tiende a {bajo}."
    alcista = esc["direccion"] == "ALCISTA"
    favor, accion = ("subir" if alcista else "bajar"), ("compra" if alcista else "venta")

    def efecto(verbo: str) -> str:
        return (f"lo que iría a favor de la {accion}" if verbo == favor
                else f"lo que lo acercaría al stop de {fmt_stop}")

    return (f"Si sale sobre lo esperado, {el} tiende a {sobre}, {efecto(sobre)}; si sale bajo lo esperado, "
            f"tiende a {bajo}, {efecto(bajo)}. Son los dos caminos, y el stop del lunes es el límite en ambos.")


def redactar(ctx: dict[str, Any], nombre: str, esc: dict[str, Any] | None, estado_sim: str,
             ahora: datetime, digits: int, variante: int = 0) -> dict[str, Any]:
    """Los textos del bloque macro: apertura, reacción, si quita la invitación, cierre y aviso al ejecutivo."""
    from analista.seguimiento import _fmt

    ahora = ahora.astimezone(SANTIAGO)
    ev, cuando, estado = ctx["evento"], ctx["cuando"], ctx["estado"]
    vivo = estado_sim == "en_curso"
    stop = _fmt(float(esc["stop"]), digits) if esc and "stop" in esc else ""
    dato = _dato(ev)
    salida = {"apertura": "", "reaccion": "", "quita_espacio": False, "cierre": None, "aparte": ""}

    if estado == "publicado":
        actual, previsto = str(ev.get("actual") or "").strip(), str(ev.get("forecast") or "").strip()
        a, p = _num(actual), _num(previsto)
        lado = None if a is None or p is None else ("sobre" if a > p else "bajo" if a < p else "linea")
        comparacion = {"sobre": "sobre lo esperado", "bajo": "bajo lo esperado",
                       "linea": "en línea con lo esperado", None: ""}[lado]
        cifras = f"{_cifra(actual)} frente a {_cifra(previsto)} esperado" if previsto else _cifra(actual)
        texto = f"ya se publicó {dato}: {cifras}" + (f", es decir, {comparacion}." if comparacion else ".")
        if lado in ("sobre", "bajo"):
            sobre = "subir" if ctx["verbo"] == "sube" else "bajar"
            verbo = sobre if lado == "sobre" else _opuesto(sobre)
            texto += f" Con un dato así, {_el(ctx['clave'], nombre)} tiende a {verbo}."
        salida["apertura"] = texto
        return salida

    salida["quita_espacio"] = estado in ("ventana", "pendiente") or (
        estado == "proximo" and cuando - ahora <= timedelta(hours=HORAS_SIN_INVITAR))
    if estado == "ventana":
        salida["apertura"] = (f"en unos minutos ({cuando:%H:%M}) se publica {dato}, y mientras el mercado lo "
                              f"absorbe el precio suele moverse a saltos. Te dejo cómo va {_el(ctx['clave'], nombre)}.")
        salida["cierre"] = CIERRE_VENTANA
    else:
        salida["apertura"] = (f"{_cuando_txt(cuando, ahora)} se publica {dato}, y quería contarte cómo se "
                              f"cruza con {_el(ctx['clave'], nombre)}.")
        salida["reaccion"] = _reaccion(ctx, nombre, esc, vivo, stop)
        if estado == "pendiente":
            salida["cierre"] = CIERRES_PENDIENTE[variante % len(CIERRES_PENDIENTE)]
    if estado in ("pendiente", "ventana"):
        alias = ALIAS_DEL_BOT.get(ctx["ticker"], ctx["ticker"].lower())
        salida["aparte"] = (f"Tip: cuando salga el dato ({cuando:%H:%M}), vuelve a pedir /seguimiento {alias} "
                            "y el mensaje ya contará cómo salió.")
    return salida
