"""Lo que sale de la pieza semanal hacia el cliente: láminas y textos de WhatsApp.

Las láminas y el texto base llevan el ANÁLISIS (lo que firma el director). La simulación
1:3 del ejecutivo no va en la lámina: la agrega el panel al texto de WhatsApp, con el
nombre de quien la hizo (spec §1 y §5).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

# Fijo y no editable (spec §7). Sin «recomendación» ni «oportunidad».
AVISO_PIEZA = ("Análisis técnico general, igual para todos sus destinatarios. No es una instrucción "
               "de inversión: un escenario puede cumplirse o invalidarse.")
SEPARADOR = "━━━━━━━━━━━━━━━━━━━"
SELLOS = {"entrada_pendiente": "ENTRADA PENDIENTE", "en_curso": "EN CURSO",
          "objetivo": "OBJETIVO 1:3 ALCANZADO", "stop": "STOP TOCADO", "sin_simulacion": "SIN SIMULACIÓN"}


def nombre_lamina(ticker: str) -> str:
    """El archivo de la lámina semanal de un activo. Lo usan el bot al rendirla y el HTML al
    enlazarla: con dos fórmulas, la de `WTI.spot` se rendía y el botón no la encontraba."""
    from analista.informe_html import slug

    return f"lamina_{slug(ticker)}.png"


def firma(autor) -> str:
    return f"Análisis: {autor.nombre} · {autor.cargo}"


def _fundir(filas: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Dos filas con el mismo precio son una sola, con las dos etiquetas: repetir la cifra en dos
    filas se lee como dos niveles (mismo criterio que las etiquetas del gráfico)."""
    salida: list[tuple[str, str]] = []
    for rotulo, valor in filas:
        i = next((k for k, (_, v) in enumerate(salida) if valor and v == valor), None)
        if i is None:
            salida.append((rotulo, valor))
        else:
            salida[i] = (f"{salida[i][0]} · {rotulo}", valor)
    return salida


def _niveles(activo: dict[str, Any]) -> list[tuple[str, str]]:
    """Los niveles del análisis: los de la lectura, nunca los de la simulación."""
    f, lec = activo["fmt"], activo["lectura"]
    if lec["estado"] == "RANGO":
        return _fundir([("Resistencia del rango", f["borde_superior"]), ("Soporte del rango", f["borde_inferior"]),
                        ("Nivel a vigilar", f["vigilar"])])
    return _fundir([("Nivel a vigilar", f["vigilar"]), ("Invalidación", f["invalidacion"] or "sin nivel"),
                    ("Objetivo técnico", f["objetivo_tori"] or "sin nivel")])


CLASES_NIVEL = ("nivel-activa", "nivel-anula", "")


def payload_semanal(activo: dict[str, Any], titular: str, datos_al: str, autor, chart: Path) -> dict[str, Any]:
    lec = activo["lectura"]
    niveles = _niveles(activo)
    return {
        "chip": "ANÁLISIS TÉCNICO DE LA SEMANA", "datos_al": datos_al,
        "activo": f"{activo['nombre']} · {activo['ticker_visible']}", "titular": titular,
        "precio": f"{activo['fmt']['precio']} {activo['unidad']}".strip(),
        "direccion": lec["direccion"], "sesgo_slug": lec["direccion"].lower(),
        "frase_lectura": lec["escenarios"][0]["texto"],
        "niveles": [{"rotulo": r, "valor": v, "clase": CLASES_NIVEL[i]} for i, (r, v) in enumerate(niveles)],
        "temporalidad": activo["temporalidad"],
        "pie_imagen": f"{activo['nombre']} · velas de 4 horas · MetaTrader 5",
        "firma": firma(autor), "aviso": AVISO_PIEZA, "chart_png": str(chart),
    }


def _avance(pct: int | None) -> str:
    if pct is None:
        return ""
    if pct < 0:
        return f"{-pct} % del camino en contra, sin tocar el stop"
    return f"{pct} % del camino al objetivo 1:3"


def payload_seguimiento(activo: dict[str, Any], ev: dict[str, Any], precio_vivo: float, lectura_hoy: str,
                        datos_al: str, autor, chart: Path) -> dict[str, Any]:
    from analista.seguimiento import _fmt, paso_la_entrada

    f, esc, d = activo["fmt"], activo["escenario"], activo["digits"]
    estado = ev["estado"]
    if estado == "entrada_pendiente":
        avance = ("El precio salió del rango: la entrada sigue pendiente" if paso_la_entrada(esc, precio_vivo)
                  else "El precio no llega a la entrada")
    else:
        avance = {"en_curso": _avance(ev.get("avance_pct")),
                  "objetivo": "Objetivo 1:3 alcanzado", "stop": "Stop tocado",
                  "sin_simulacion": "Esta semana este activo no tiene simulación"}[estado]
    sin = estado == "sin_simulacion"
    niveles = "" if sin else f"Entrada {f['entrada']} · Stop {f['stop']} · Objetivo 1:3 {f['objetivo']}"
    return {
        "chip": f"SEGUIMIENTO · {SELLOS[ev['estado']]}", "datos_al": datos_al,
        "activo": f"{activo['nombre']} · {activo['ticker_visible']}",
        "direccion": (activo["lectura"]["direccion"] if sin else esc["direccion"]).lower(),
        "sello": SELLOS[ev["estado"]],
        "precio_lunes": f["precio"], "precio_hoy": _fmt(precio_vivo, d), "avance": avance,
        "lectura_hoy": lectura_hoy, "niveles": niveles,
        "pie_imagen": f"{activo['nombre']} · velas de 4 horas · MetaTrader 5",
        "firma": firma(autor), "aviso": AVISO_PIEZA, "chart_png": str(chart),
    }


def texto_whatsapp_base(activo: dict[str, Any], titular: str, contexto: str) -> str:
    """El texto del análisis, con las 6 reglas de formato. El panel le agrega la simulación."""
    lec = activo["lectura"]
    return "\n".join([
        f"🎯 Activo: {activo['nombre']}",
        f"📌 Nivel a vigilar: *{activo['fmt']['vigilar']}*",
        f"⚡ Qué esperar: {titular}",
        SEPARADOR,
        contexto,
        SEPARADOR,
        *[f"{e['flecha']} {e['texto']}" for e in lec["escenarios"]],
        f"⏱️ *Temporalidad*: {activo['temporalidad']}",
        SEPARADOR,
        AVISO_PIEZA,
    ])


def rendir(payload: dict[str, Any], plantilla: str, destino: Path,
           render: Callable[..., Path] | None = None) -> Path:
    """Lámina horizontal 1920×1080 (`semanal` o `seguimiento`)."""
    import pipeline_avisos as pa

    if render is None:
        from story_render import render_story as render
    render(payload, pa.DIR_PLANTILLAS / f"{plantilla}.html", destino, formato="horizontal")
    return destino
