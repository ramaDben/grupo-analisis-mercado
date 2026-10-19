"""Lo que sale de la pieza semanal hacia el cliente: láminas y textos de WhatsApp.

Las láminas y el texto base llevan el ANÁLISIS (lo que firma el director). La simulación
del ejecutivo no va en la lámina: la agrega el panel al texto de WhatsApp, con el
nombre de quien la hizo (spec §1 y §5).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

# Fijo y no editable (spec §7). Sin «recomendación» ni «oportunidad».
AVISO_PIEZA = ("Análisis técnico de carácter informativo. No es una instrucción "
               "de inversión: un escenario puede cumplirse o invalidarse.")
# La lámina de seguimiento lleva el aviso en una sola línea corta (director, 2026-10-13: la veía sucia).
AVISO_SEGUIMIENTO = "Análisis técnico informativo. No es una instrucción de inversión."
INVITACION_ACTIVA = "¿Te interesa operar este escenario? Conversémoslo, con el stop como límite."
INVITACION_CERRADA = "Si quieres, vemos juntos cómo sigue."
ROTULO_ILUSTRATIVO = "Ejemplo ilustrativo para revisar en MT5"
INVITACION_MT5 = "Si quieres, lo revisamos juntos en la plataforma MT5."
SEPARADOR = "━━━━━━━━━━━━━━━━━━━"
MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre",
         "noviembre", "diciembre")


def semana_visible(semana: str) -> str:
    """«2026-W42» como lo lee una persona: «semana del 12 al 16 de octubre».

    La etiqueta ISO confunde (director, 2026-10-12): queda solo para archivos y el registro.
    """
    from datetime import date

    anio, num = semana.split("-W")
    lunes = date.fromisocalendar(int(anio), int(num), 1)
    viernes = date.fromisocalendar(int(anio), int(num), 5)
    if lunes.month == viernes.month:
        return f"semana del {lunes.day} al {viernes.day} de {MESES[viernes.month - 1]}"
    return f"semana del {lunes.day} de {MESES[lunes.month - 1]} al {viernes.day} de {MESES[viernes.month - 1]}"
SELLOS = {"entrada_pendiente": "ENTRADA PENDIENTE", "en_curso": "EN CURSO",
          "objetivo": "OBJETIVO ALCANZADO", "stop": "STOP TOCADO", "rango_roto": "RANGO ROTO",
          "descartada": "SIMULACIÓN DESCARTADA",
          "sin_simulacion": "SIN SIMULACIÓN"}


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
    # Rótulos en lenguaje de cliente: la invalidación dice qué hacer ("se anula si cierra bajo X"), y un
    # nivel que la lectura no trae no se muestra: «sin nivel» no le sirve a nadie para decidir.
    anula = {"ALCISTA": "Se anula si cierra bajo", "BAJISTA": "Se anula si cierra sobre"}.get(
        lec["direccion"].upper(), "Se anula en")
    filas = [("Nivel a vigilar", f["vigilar"]), (anula, f["invalidacion"]), ("Objetivo", f["objetivo_tori"])]
    return _fundir([(r, v) for r, v in filas if v])


def _clase_nivel(rotulo: str) -> str:
    """La clase sale del rótulo y no de la posición: una fila que falta no corre los colores."""
    return "nivel-anula" if "anula" in rotulo else "nivel-activa" if "vigilar" in rotulo else ""


def texto_acompanamiento(nombre_activo: str, saludo: str) -> str:
    """El mensaje breve que el ejecutivo reenvía junto al análisis: siempre invita a revisar MT5."""
    hola = f"Hola {saludo}, " if saludo else "Hola, "
    return (f"{hola}te comparto el análisis técnico y fundamental de {nombre_activo}. "
            f"Me gustaría revisarlo contigo en la plataforma MT5: miramos el gráfico, los escenarios y la "
            f"estrategia juntos. ¿Cuándo te acomoda?")


def payload_semanal(activo: dict[str, Any], titular: str, datos_al: str, autor, chart: Path) -> dict[str, Any]:
    lec = activo["lectura"]
    niveles = _niveles(activo)
    return {
        "chip": "ANÁLISIS TÉCNICO", "datos_al": datos_al,
        "activo": f"{activo['nombre']} · {activo['ticker_visible']}", "titular": titular,
        "precio": f"{activo['fmt']['precio']} {activo['unidad']}".strip(),
        "direccion": lec["direccion"], "sesgo_slug": lec["direccion"].lower(),
        "frase_lectura": lec["escenarios"][0]["texto"],
        "niveles": [{"rotulo": r, "valor": v, "clase": _clase_nivel(r)} for r, v in niveles],
        "temporalidad": activo["temporalidad"],
        "pie_imagen": f"{activo['nombre']} · velas de 4 horas · MetaTrader 5",
        "firma": firma(autor), "aviso": AVISO_PIEZA, "chart_png": str(chart),
    }


def _avance(pct: int | None) -> str:
    if pct is None:
        return ""
    if pct < 0:
        return f"{-pct} % del camino en contra, sin tocar el stop"
    return f"{pct} % del camino al objetivo"


def payload_seguimiento(activo: dict[str, Any], ev: dict[str, Any], precio_vivo: float, lectura_hoy: str,
                        datos_al: str, autor, chart: Path) -> dict[str, Any]:
    from analista.seguimiento import _fmt, paso_la_entrada

    f, esc, d = activo["fmt"], activo["escenario"], activo["digits"]
    estado = ev["estado"]
    if estado == "entrada_pendiente" and esc.get("condicion") == "quiebre":
        avance = (f"Se activa con un cierre de vela 4H {'sobre' if esc['direccion'] == 'ALCISTA' else 'bajo'} "
                  f"{f['entrada']}")
    elif estado == "entrada_pendiente" and esc.get("condicion") == "retesteo" and esc.get("estado") != "RANGO":
        avance = f"Se activa si el precio vuelve a {f['entrada']}"
    elif estado == "entrada_pendiente":
        avance = ("El precio salió del rango: la entrada sigue pendiente" if paso_la_entrada(esc, precio_vivo)
                  else "El precio no llega a la entrada")
    else:
        avance = {"en_curso": _avance(ev.get("avance_pct")),
                  "objetivo": "Objetivo alcanzado", "stop": "Stop tocado",
                  "rango_roto": "El precio rompió el rango: simulación descartada",
                  "descartada": "El precio rompió el nivel sin activar la entrada: simulación descartada",
                  "sin_simulacion": "Esta semana este activo no tiene simulación"}[estado]
    sin = estado == "sin_simulacion"
    niveles = "" if sin else f"Entrada {f['entrada']} · Stop {f['stop']} · Objetivo {f['objetivo']}"
    viva = estado in ("entrada_pendiente", "en_curso")
    return {
        "chip": "SEGUIMIENTO DE LA SEMANA", "datos_al": datos_al,
        "activo": f"{activo['nombre']} · {activo['ticker_visible']}",
        "direccion": (activo["lectura"]["direccion"] if sin else esc["direccion"]).lower(),
        "sello": SELLOS[ev["estado"]],
        "precio_lunes": f["precio"], "precio_hoy": _fmt(precio_vivo, d), "avance": avance,
        "lectura_hoy": lectura_hoy, "niveles": niveles,
        "entrada": "" if sin else f["entrada"], "stop": "" if sin else f["stop"],
        "objetivo": "" if sin else f["objetivo"],
        "invitacion": INVITACION_ACTIVA if viva else INVITACION_CERRADA,
        "pie_imagen": f"{activo['nombre']} · velas de 4 horas · MetaTrader 5",
        "firma": firma(autor), "aviso": AVISO_SEGUIMIENTO, "chart_png": str(chart),
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
        INVITACION_MT5,
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
