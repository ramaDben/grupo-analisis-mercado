"""El avance de la simulación de la semana contra la foto, y la lectura de hoy, por separado.

Dos cosas distintas, con el mismo peso (spec §6): la simulación se mide contra sus precios
FIJOS del lunes; la lectura de la estrategia sigue la línea en movimiento. Nunca en pesos
(dependen del volumen de cada ejecutivo) y nunca «si hubieras entrado ganarías X».
"""
from __future__ import annotations

from typing import Any

ESTADOS = ("entrada_pendiente", "en_curso", "objetivo", "stop", "rango_roto", "descartada", "sin_simulacion")
SEPARADOR = "━━━━━━━━━━━━━━━━━━━"


def _fmt(valor: float, digits: int) -> str:
    import pipeline_carrusel as pc

    return pc.formatear_precio(valor, digits)


def _retesteo_fuera_de_rango(esc: dict[str, Any]) -> bool:
    return esc.get("condicion") == "retesteo" and esc.get("estado") != "RANGO"


def evaluar(esc: dict[str, Any], velas: list[dict[str, Any]], precio_vivo: float) -> dict[str, Any]:
    """Recorre las velas 4H cerradas desde la foto y termina en el precio vivo.

    Si una misma vela toca el stop y el objetivo, cuenta stop: sin datos dentro de la vela
    no se sabe qué pasó primero, y se cuenta lo prudente.

    Con la entrada pendiente (el falso quiebre del rango) la entrada se activa en una vela que
    pasa por su precio **sin llegar al stop**. Una vela que cruza el borde y sigue hasta el stop
    es una ruptura del rango, no el falso quiebre que se simula: la simulación queda descartada
    («rango_roto»), nunca «stop tocado» de una entrada que no se activó ni «pendiente» de un
    precio que ya no vale (director, 2026-10-12, tras la prueba real de la W41, cobre). En la
    vela que activa tampoco cuenta el objetivo: dentro de ella no se sabe qué tocó primero. El
    precio vivo se mide como un tramo desde el último cierre.

    La entrada por quiebre (`condicion == "quiebre"`) se activa con el CIERRE de una vela 4H al
    otro lado del nivel, y antes de eso el stop no cuenta: el precio viene justamente de ese
    lado. El tramo vivo no activa, porque todavía no cerró. Un retesteo que no es de rango y se
    rompe sin activar queda «descartada».
    """
    alcista = esc["direccion"] == "ALCISTA"
    entrada, stop, obj = float(esc["entrada"]), float(esc["stop"]), float(esc["objetivo"])
    activa = not esc.get("entrada_pendiente")
    quiebre = esc.get("condicion") == "quiebre"
    roto = "descartada" if _retesteo_fuera_de_rango(esc) else "rango_roto"
    previo = float(velas[-1]["close"]) if velas else precio_vivo
    tramos = [(float(x["high"]), float(x["low"]), float(x["close"])) for x in velas]
    tramos.append((max(previo, precio_vivo), min(previo, precio_vivo), None))
    for alto, bajo, cierre in tramos:
        toca_stop = (bajo <= stop) if alcista else (alto >= stop)
        if not activa:
            if quiebre:
                activa = cierre is not None and ((cierre > entrada) if alcista else (cierre < entrada))
                continue
            if toca_stop:
                return {"estado": roto, "avance_pct": None}
            if bajo <= entrada <= alto:
                activa = True
            continue
        if toca_stop:
            return {"estado": "stop", "avance_pct": None}
        if (alto >= obj) if alcista else (bajo <= obj):
            return {"estado": "objetivo", "avance_pct": 100}
    if not activa:
        return {"estado": "entrada_pendiente", "avance_pct": None}
    avance = (precio_vivo - entrada) / (obj - entrada) * 100
    return {"estado": "en_curso", "avance_pct": int(avance + 0.5) if avance >= 0 else -int(-avance + 0.5)}


def paso_la_entrada(esc: dict[str, Any], precio: float) -> bool:
    """Con la entrada pendiente, si el precio está del lado del stop (fuera del rango)."""
    entrada = float(esc["entrada"])
    return precio < entrada if esc["direccion"] == "ALCISTA" else precio > entrada


def texto_simulacion(esc: dict[str, Any], ev: dict[str, Any], precio_vivo: float, digits: int) -> str:
    f = lambda x: _fmt(x, digits)  # noqa: E731
    estado = ev["estado"]
    if estado == "sin_simulacion":
        return f"Esta semana este activo no tiene simulación: {ev['motivo']}."
    if estado == "entrada_pendiente" and esc.get("condicion") == "quiebre":
        return (f"La simulación se activa si una vela de 4 horas cierra "
                f"{'sobre' if esc['direccion'] == 'ALCISTA' else 'bajo'} {f(esc['entrada'])}: "
                f"el precio va en {f(precio_vivo)}.")
    if estado == "entrada_pendiente" and _retesteo_fuera_de_rango(esc):
        return f"La simulación se activa si el precio vuelve a {f(esc['entrada'])}: va en {f(precio_vivo)}."
    if estado == "descartada":
        return (f"El precio rompió {f(esc['entrada'])} sin activar la entrada y va en {f(precio_vivo)}: "
                "la simulación de esta semana queda descartada.")
    if estado == "entrada_pendiente":
        if paso_la_entrada(esc, precio_vivo):
            return (f"El precio salió del rango y va en {f(precio_vivo)}: la simulación se activa si "
                    f"vuelve a la entrada de {f(esc['entrada'])}.")
        return f"El precio todavía no llega a la entrada de {f(esc['entrada'])}: va en {f(precio_vivo)}."
    if estado == "rango_roto":
        return (f"El precio rompió el rango y va en {f(precio_vivo)}: la simulación de esta semana "
                "queda descartada.")
    if estado == "stop":
        return f"El precio tocó el stop de {f(esc['stop'])}."
    if estado == "objetivo":
        return f"El precio alcanzó el objetivo de {f(esc['objetivo'])}."
    pct = ev["avance_pct"]
    if pct >= 0:
        return f"En curso: el precio va en {f(precio_vivo)}, un {pct} % del recorrido hacia el objetivo."
    return (f"En curso: el precio va en {f(precio_vivo)}, un {-pct} % del recorrido en contra, "
            "sin tocar el stop.")


def texto_lectura(actual, reemplazada: bool, digits: int) -> str:
    f = lambda x: _fmt(x, digits)  # noqa: E731
    if reemplazada:
        return (f"La lectura de la semana cambió: ahora se vigila {actual.vigilar.etiqueta} "
                f"en {f(actual.vigilar.precio)}.")
    if actual.estado == "PRUEBA" and actual.en_prueba is not None:
        return (f"El precio está probando {actual.vigilar.etiqueta} en {f(actual.en_prueba.valor_ahora)}: "
                f"se define al cierre de la vela de las {actual.en_prueba.cierre_vela:%H:%M}.")
    return (f"La lectura del lunes sigue en pie: {actual.estado.lower()} "
            f"{actual.direccion.lower()}, con {actual.vigilar.etiqueta} en {f(actual.vigilar.precio)}.")


MARCA_SALUDO = "[[SALUDO]]"
SALUDO_POR_DEFECTO = "Hola,"
# Poco avance: casi todo el recorrido sigue por delante. Mucho avance: queda poco.
AVANCE_POCO, AVANCE_MUCHO = 10, 70

# Varias formas de abrir y de cerrar: un solo texto repetido cada día se lee como plantilla. Se elige
# una por día y activo (estable), como los cierres del carrusel, para que no cambie entre reenvíos.
ABRIR = (
    "te cuento cómo va la simulación de {n}",
    "te actualizo la simulación de {n}",
    "quería contarte cómo viene la simulación de {n}",
)
CERRAR = (
    "En la lámina lo ves sobre el gráfico. Si quieres, lo vemos juntos.",
    "Te dejo la lámina con los niveles dibujados. Cualquier duda, me avisas.",
    "La lámina muestra todo sobre el gráfico de hoy. Cuando quieras, lo conversamos.",
)


def saludo_de(texto: str) -> str:
    """Cómo abre el mensaje: lo que el ejecutivo escribió, o un saludo neutro.

    «Estimado Sr. Pérez» se usa tal cual (con su puntuación); un nombre suelto queda «Hola Juan,».
    Un nombre escrito todo en minúscula («hari») se capitaliza: a mano nadie lo deja así.
    """
    texto = " ".join((texto or "").split())
    if not texto:
        return SALUDO_POR_DEFECTO
    if texto == texto.lower():
        texto = texto.title()
    if not texto.lower().startswith(("estimad", "apreciad")):
        texto = f"Hola {texto}"
    return texto if texto[-1] in ":,;." else texto + ","


def con_saludo(whatsapp: str, saludo: str = "") -> str:
    """Pone el saludo del ejecutivo donde la pieza guardada dejó la marca.

    La pieza se reusa entre ejecutivos, así que el saludo no se guarda con ella.
    """
    return whatsapp.replace(MARCA_SALUDO, saludo_de(saludo))


def _variante(opciones: tuple[str, ...], fecha_hoy: str, nombre: str, salto: int = 0) -> str:
    import zlib

    return opciones[(zlib.crc32(f"{fecha_hoy}|{nombre}".encode()) >> salto) % len(opciones)]


def _variante_n(fecha_hoy: str, nombre: str) -> int:
    import zlib

    return zlib.crc32(f"{fecha_hoy}|{nombre}".encode()) >> 16


def _titular(ev: dict[str, Any]) -> str:
    """Lo que le pasó a la simulación, en pocas palabras: va en la primera línea."""
    estado = ev["estado"]
    if estado == "en_curso":
        pct = ev["avance_pct"]
        return ("va en contra por ahora, sin tocar el stop" if pct < 0
                else "sigue en curso" if pct < AVANCE_POCO else "va a favor")
    return {"entrada_pendiente": "todavía espera su entrada", "objetivo": "llegó a su objetivo",
            "stop": "tocó su stop", "rango_roto": "quedó descartada", "descartada": "quedó descartada",
            "sin_simulacion": "esta semana no tiene"}[estado]


def _hoy(esc: dict[str, Any], ev: dict[str, Any], precio_vivo: float, digits: int,
         con_espacio: bool = True) -> str:
    """Dónde está el precio hoy frente a la simulación, y si todavía queda espacio para tomar posición.

    Solo dice «hay espacio» cuando es cierto: con la entrada pendiente o con poco recorrido hecho. Con
    el precio en contra, con el objetivo cumplido o con el stop tocado, no lo dice. Con un dato fuerte
    por salir (`con_espacio=False`) tampoco: no se invita a tomar posición justo antes de la noticia.
    """
    f = lambda x: _fmt(x, digits)  # noqa: E731
    estado, stop = ev["estado"], f(esc["stop"]) if "stop" in esc else ""
    limite = f"con el stop en {stop} como límite"
    if estado == "en_curso":
        pct, p = ev["avance_pct"], f(precio_vivo)
        if pct < 0:
            return (f"Hoy el precio va en {p}, en contra de la entrada, pero sin tocar el stop: mientras "
                    "eso no pase, la simulación sigue vigente.")
        if not con_espacio:
            return (f"Hoy el precio va en {p} y se ha movido muy poco a favor." if pct < AVANCE_POCO
                    else f"Hoy el precio va en {p}: ya recorrió un {pct} % del camino al objetivo.")
        if pct < AVANCE_POCO:
            return (f"Hoy el precio va en {p} y se ha movido muy poco a favor. Todavía queda casi todo el "
                    f"recorrido hasta el objetivo, así que aún hay espacio para tomar posición en esa "
                    f"dirección, {limite}.")
        if pct < AVANCE_MUCHO:
            return (f"Hoy el precio va en {p}: ya recorrió un {pct} % del camino al objetivo y todavía "
                    f"queda espacio para tomar posición en esa dirección, {limite}.")
        return (f"Hoy el precio va en {p}: ya recorrió un {pct} % del camino al objetivo, así que queda "
                "poco espacio para tomar posición en esa dirección.")
    if estado == "entrada_pendiente" and not con_espacio:
        return texto_simulacion(esc, ev, precio_vivo, digits)
    if estado == "entrada_pendiente":
        return (texto_simulacion(esc, ev, precio_vivo, digits) + " Como todavía no se activa, aún hay "
                f"espacio para tomar posición en esa dirección cuando se dé esa condición, {limite}.")
    if estado == "objetivo":
        return (f"El precio llegó al objetivo de {f(esc['objetivo'])}: la simulación de esta semana se da "
                "por cumplida.")
    if estado == "stop":
        return (f"El precio tocó el stop de {stop}: la simulación de esta semana se da por cerrada. Para "
                "eso está el stop: limitar la pérdida cuando el escenario no se da.")
    return texto_simulacion(esc, ev, precio_vivo, digits)  # descartada, rango roto o sin simulación


def _cifras(esc: dict[str, Any], ev: dict[str, Any], digits: int) -> str:
    """Entrada, stop y objetivo con el mismo peso y explicados; solo mientras la simulación vive."""
    if ev["estado"] not in ("entrada_pendiente", "en_curso"):
        return ""
    f = lambda x: _fmt(x, digits)  # noqa: E731
    return (f"Las cifras de la simulación no cambian desde el lunes: entrada en {f(esc['entrada'])}, "
            f"stop en {f(esc['stop'])} (si el precio llega ahí, se da por fallida) y objetivo en "
            f"{f(esc['objetivo'])} (si llega ahí, se da por cumplida).")


def _armar(nombre: str, fecha_hoy: str, esc: dict[str, Any], ev: dict[str, Any], precio_vivo: float,
           lectura_hoy: str, digits: int, macro: dict[str, Any] | None = None) -> str:
    """El texto con la marca del saludo. `macro` (ver `macro_seguimiento.redactar`) lo abre con el dato."""
    sin = ev["estado"] == "sin_simulacion"
    macro = macro or {}
    cierre = macro.get("cierre") or _variante(CERRAR, fecha_hoy, nombre, 8)
    if sin:
        primera = (f"{MARCA_SALUDO} te cuento cómo va {nombre}: esta semana no tiene simulación, "
                   "y te dejo la lectura de hoy.")
        detalle = texto_simulacion(esc, ev, precio_vivo, digits)
    else:
        accion = "una compra" if esc["direccion"] == "ALCISTA" else "una venta"
        sentido = "alcista" if esc["direccion"] == "ALCISTA" else "bajista"
        apertura = _variante(ABRIR, fecha_hoy, nombre).format(n=nombre)
        primera = f"{MARCA_SALUDO} {apertura}: {_titular(ev)}."
        con_direccion = ev["estado"] not in ("rango_roto", "descartada")
        hoy = _hoy(esc, ev, precio_vivo, digits, con_espacio=not macro.get("quita_espacio"))
        detalle = " ".join(x for x in ((f"Es {accion}, porque la tendencia es {sentido}." if con_direccion else ""),
                                       hoy) if x)
    if macro.get("apertura"):
        primera = f"{MARCA_SALUDO} {macro['apertura']}" + (f" {macro['reaccion']}" if macro.get("reaccion") else "")
    partes = [primera, detalle, _cifras(esc, ev, digits), lectura_hoy, cierre]
    return "\n\n".join(p for p in partes if p)


def mensaje(nombre: str, fecha_hoy: str, fecha_foto: str, esc: dict[str, Any], ev: dict[str, Any],
            precio_vivo: float, actual, reemplazada: bool, digits: int) -> str:
    """El texto de WhatsApp del seguimiento: una persona que retoma la conversación con su cliente.

    Abre con la marca del saludo (`con_saludo` la reemplaza al responder) y el estado en la primera
    línea; después, en párrafos y sin encabezados, la simulación fijada el lunes (con su dirección,
    el espacio que queda y las cifras) y la lectura de hoy, que se informan por separado y con el
    mismo peso. Sin aviso legal (gerencia, 2026-10-13): lo lleva la lámina.
    """
    return _armar(nombre, fecha_hoy, esc, ev, precio_vivo, texto_lectura(actual, reemplazada, digits), digits)


def redactar(datos: dict[str, Any], saludo: str = "", ctx_macro: dict[str, Any] | None = None,
             ahora=None) -> tuple[str, str]:
    """El texto final para un ejecutivo, armado AL RESPONDER desde los datos de la pieza guardada.

    La pieza se reusa 30 minutos entre ejecutivos y el bot cambia de código entre reinicios: un texto
    guardado con la pieza servía el redactado por la versión anterior (pasó el 2026-10-13: el bot
    mandó el mensaje viejo después de actualizarlo). Armarlo acá lo deja siempre al día, con el
    saludo de quien pide y con el dato macro de ese instante. Devuelve (texto, aviso al ejecutivo).
    """
    activo = datos["activo"]
    fecha_hoy = str(datos["edicion"]).split(" · ")[0]
    esc, ev, digits = activo["escenario"], datos["evaluacion"], activo["digits"]
    macro: dict[str, Any] = {}
    if ctx_macro is not None and ahora is not None:
        try:
            from analista import macro_seguimiento as mac

            macro = mac.redactar(ctx_macro, datos["nombre"], None if ev["estado"] == "sin_simulacion" else esc,
                                 ev["estado"], ahora, digits, variante=_variante_n(fecha_hoy, datos["nombre"]))
        except Exception:  # noqa: BLE001  el dato macro es un extra: sin él, el seguimiento sale igual
            macro = {}
    texto = _armar(datos["nombre"], fecha_hoy, esc, ev, float(datos["precio_vivo"]), datos["lectura_hoy"],
                   digits, macro)
    return con_saludo(texto, saludo), macro.get("aparte", "")
