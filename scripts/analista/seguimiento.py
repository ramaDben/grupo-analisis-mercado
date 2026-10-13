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
    "te actualizo el análisis de {n} que te compartí el {dia}.",
    "quería contarte cómo viene el análisis de {n} que te compartí el {dia}.",
    "te cuento cómo va lo que te compartí el {dia} sobre {n}.",
)
CERRAR = (
    "El detalle va en la lámina, sobre el gráfico.",
    "Te dejo la lámina con el detalle. Si quieres, lo vemos juntos.",
    "En la lámina lo ves todo. Cuando quieras, lo conversamos.",
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


def _enlace(nombre: str, dia: str, sesgo: str) -> str:
    """Lo que ata el seguimiento al mensaje del día de la foto: qué se compartió y con qué sesgo."""
    return f"El {dia} te compartí el análisis de {nombre}" + (f" (sesgo {sesgo})" if sesgo else "")


def _con(cabeza: str, frase: str) -> str:
    """Une la cabecera (el enlace o el sesgo) con la frase; sin cabecera, la frase abre con mayúscula."""
    return f"{cabeza} {frase}" if cabeza else frase[0].upper() + frase[1:]


def _plan(nombre: str, esc: dict[str, Any], ev: dict[str, Any], dia: str = "lunes", sesgo: str = "",
          con_enlace: bool = True) -> str:
    """El plan en una o dos frases y sin precios (director, 2026-10-13): enlaza con el análisis que se
    mandó el día de la foto, dice de qué lado se opera con CFD, cómo va y que, si se invalida, nos
    cambiamos de lado. Las cifras van solo en la lámina."""
    estado = ev["estado"]
    # Sin dato macro, el enlace con el mensaje del día de la foto ya lo hizo la apertura.
    cabeza = (f"{_enlace(nombre, dia, sesgo)}:" if con_enlace else f"Con sesgo {sesgo}," if sesgo else "")
    if estado == "sin_simulacion":
        return _con(cabeza, f"esta semana no hay un plan definido. Te dejo la lectura de hoy.")
    alcista = esc["direccion"] == "ALCISTA"
    lado, otro = ("al alza", "a la baja") if alcista else ("a la baja", "al alza")
    cambio = f"Si el plan se invalida, nos cambiamos de lado y operamos {otro}."
    if estado == "entrada_pendiente":
        return _con(cabeza, f"el plan es operar {lado} con CFD y se activa cuando el precio confirme la "
                    f"entrada. {cambio}")
    if estado == "en_curso":
        pct = ev["avance_pct"]
        como = ("hoy va en contra, pero sigue vigente" if pct < 0
                else "ya lleva buena parte del camino hecho" if pct >= AVANCE_MUCHO else "hoy va a favor")
        return _con(cabeza, f"el plan es operar {lado} con CFD y {como}. {cambio}")
    if estado == "objetivo":
        return _con(cabeza, "el plan llegó a su objetivo. Con CFD se opera de los dos lados, así que ahora "
                    "miramos el siguiente movimiento.")
    if estado == "stop":
        return _con(cabeza, f"el plan se invalidó, y ahí nos cambiamos de lado. Miramos la lectura de hoy "
                    f"para operar {otro}.")
    return _con(cabeza, "el plan se descartó antes de activarse. Ahora miramos hacia dónde sale el precio, "
                "y con CFD se puede operar cualquiera de los dos lados.")


def _armar(nombre: str, fecha_hoy: str, esc: dict[str, Any], ev: dict[str, Any], precio_vivo: float,
           lectura_hoy: str, digits: int, macro: dict[str, Any] | None = None, dia: str = "lunes",
           sesgo: str = "") -> str:
    """El texto corto con la marca del saludo: gancho, dato (si hay), plan y cierre. Sin precios."""
    macro = macro or {}
    apertura = macro.get("apertura") or _variante(ABRIR, fecha_hoy, nombre).format(n=nombre, dia=dia)
    cierre = macro.get("cierre") or _variante(CERRAR, fecha_hoy, nombre, 8)
    partes = [f"{MARCA_SALUDO} {apertura}", macro.get("reaccion") or "", _plan(nombre, esc, ev, dia, sesgo, bool(macro.get("apertura"))), cierre]
    return "\n\n".join(p for p in partes if p)


def mensaje(nombre: str, fecha_hoy: str, fecha_foto: str, esc: dict[str, Any], ev: dict[str, Any],
            precio_vivo: float, actual, reemplazada: bool, digits: int) -> str:
    """El texto de WhatsApp del seguimiento: una persona que retoma la conversación con su cliente.

    Abre con la marca del saludo (`con_saludo` la reemplaza al responder) y el estado en la primera
    línea; después, en párrafos y sin encabezados, la simulación fijada el lunes (con su dirección,
    el espacio que queda y las cifras) y la lectura de hoy, que se informan por separado y con el
    mismo peso. Sin aviso legal (gerencia, 2026-10-13): lo lleva la lámina.
    """
    return _armar(nombre, fecha_hoy, esc, ev, precio_vivo, texto_lectura(actual, reemplazada, digits), digits,
                  dia=(fecha_foto.split() or ["lunes"])[0])


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
    dia = str((activo.get("foto") or {}).get("fecha") or "lunes").split()[0]
    sesgo = str((activo.get("lectura") or {}).get("direccion") or "").lower()
    texto = _armar(datos["nombre"], fecha_hoy, esc, ev, float(datos["precio_vivo"]), datos["lectura_hoy"],
                   digits, macro, dia, sesgo)
    return con_saludo(texto, saludo), macro.get("aparte", "")
