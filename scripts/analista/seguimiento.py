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


# Cada mensaje es un solo párrafo que cierra con una pregunta concreta, y hay tres redacciones por estado:
# tres bloques apilados, el mismo cierre genérico y una sola forma delatan al bot (gerencia, 2026-10-13).
# Se elige una por día y activo (estable el mismo día) para que no cambie entre reenvíos. Reglas de cada
# texto: «CFD» una vez, sin precios (van en la lámina), el stop como límite y el otro lado solo se «revisa».
PLANTILLAS = {
    "entrada_pendiente": (
        "{el} todavía no confirma la entrada de la {accion} que vimos el {dia}. Sigue en espera, y con CFD se "
        "puede operar hacia cualquiera de los dos lados si cambia la lectura. Te dejé la lámina, ¿la revisamos?",
        "la {accion} {del} que te compartí el {dia} aún espera su entrada: el precio no llega a donde la "
        "lectura la activa. Con CFD se puede operar al alza o a la baja, así que sigo atento a cómo se mueve. "
        "¿Lo vemos en la lámina?",
        "te escribo por {el}: la {accion} del {dia} todavía no se activa, así que por ahora no hay entrada. Si "
        "cambia la lectura, con CFD también se opera el otro lado. ¿Te muestro la lámina?",
    ),
    "a_favor": (
        "{el} va a favor de la {accion} que te compartí el {dia}. Mientras el stop no se toque sigue vigente, "
        "y si se toca se revisa el otro lado, que con CFD también se opera. Está todo en la lámina, ¿la vemos?",
        "te cuento que la {accion} {del} del {dia} viene a favor y sigue dentro del plan. Si llegara al stop se "
        "revisa el otro lado, ya que con CFD se opera en los dos sentidos. ¿Alcanzaste a ver la lámina?",
        "{el} se ha movido a favor de la {accion} del {dia}. El stop sigue como límite y, si se toca, miramos "
        "el otro lado: con CFD se puede operar hacia ambos. Te dejo la lámina, ¿conversamos?",
    ),
    "en_contra": (
        "{el} viene en contra de la {accion} del {dia}, pero sin tocar el stop, así que sigue en pie. Si lo "
        "toca, se revisa el otro lado, que con CFD también se opera. ¿Te cuento cómo lo estoy viendo?",
        "la {accion} {del} que vimos el {dia} está pasando por un tramo en contra, todavía dentro del stop. Si "
        "se invalida, se revisa el otro lado; con CFD se opera en ambos sentidos. ¿La revisamos en la lámina?",
        "te aviso que {el} se movió en contra de la {accion} del {dia}, aunque sin llegar al stop. Si lo toca "
        "miramos el otro lado, que con CFD también se puede operar. ¿Hablamos?",
    ),
    "avance_mucho": (
        "{el} ya recorrió buena parte del camino de la {accion} que te compartí el {dia}. Queda poco para el "
        "objetivo, y con CFD se puede operar en ambos sentidos cuando eso se cumpla. Te dejo la lámina, ¿la vemos?",
        "la {accion} {del} del {dia} va muy avanzada hacia su objetivo. Con el stop como límite, vamos viendo "
        "el siguiente paso, y con CFD se puede operar hacia los dos lados. ¿Lo conversamos?",
        "{el} lleva casi todo el recorrido de la {accion} del {dia}. Falta poco para el objetivo y después se "
        "revisa hacia dónde sigue, con CFD en cualquiera de los dos lados. ¿Te muestro la lámina?",
    ),
    "objetivo": (
        "{el} llegó al objetivo de la {accion} que te compartí el {dia}. Con CFD se opera hacia los dos lados, "
        "así que ahora revisamos el siguiente movimiento. ¿Lo conversamos?",
        "se cumplió la {accion} {del} del {dia}: el precio llegó al objetivo. Cerrado ese plan, miramos qué "
        "sigue, y con CFD se puede operar al alza o a la baja. ¿La revisamos en la lámina?",
        "te cuento que {el} alcanzó el objetivo de la {accion} del {dia}. Ahora toca ver el siguiente tramo, de "
        "cualquiera de los dos lados con CFD. ¿Lo vemos juntos?",
    ),
    "stop": (
        "{el} tocó el stop de la {accion} del {dia} y ese plan quedó cerrado, que es justo para lo que está el "
        "stop. Hoy reviso si la lectura apunta al otro lado, y con CFD se puede operar hacia allá también. ¿Lo vemos?",
        "la {accion} {del} que te compartí el {dia} llegó al stop y quedó invalidada. Ahora se revisa el otro "
        "lado, sin apuro: con CFD se puede operar en ambos sentidos. ¿Te muestro la lámina?",
        "te cuento que {el} llegó al stop de la {accion} del {dia}. El stop hizo su trabajo, que es limitar el "
        "riesgo, y ahora miramos la lectura de hoy hacia el otro lado con CFD. ¿Conversamos?",
    ),
    "descartada": (
        "la {accion} {del} que vimos el {dia} se descartó antes de activarse: el precio salió del nivel sin dar "
        "la entrada. Ahora miramos hacia dónde sigue, y con CFD se puede operar cualquiera de los dos lados. ¿Lo vemos?",
        "te aviso que {el} rompió el nivel sin activar la {accion} del {dia}, así que ese plan quedó descartado. "
        "Con CFD se opera en ambos sentidos, y hoy revisamos qué lectura queda. ¿Te muestro la lámina?",
        "la {accion} del {dia} sobre {el} no llegó a activarse y quedó descartada. Seguimos mirando el precio "
        "para ver hacia dónde define, que con CFD se puede operar hacia ambos lados. ¿La revisamos?",
    ),
    "sin_simulacion": (
        "{el} no tiene un plan definido esta semana, pero te dejo cómo viene la lectura de hoy en la lámina. "
        "Con CFD se opera tanto al alza como a la baja. ¿La vemos?",
        "te escribo por {el}: esta semana no quedó con un plan definido. Igual te dejé la lectura de hoy en la "
        "lámina, ¿la revisamos?",
        "sobre {el}: no tiene un plan definido esta semana, pero la lectura de hoy está en la lámina. Con CFD "
        "se opera hacia los dos lados, ¿la miramos juntos?",
    ),
}
ARTICULOS = {"Oro": "el oro", "Cobre": "el cobre", "Petróleo": "el petróleo", "Bitcoin": "Bitcoin",
             "Plata": "la plata"}


def _activo_con_articulo(nombre: str) -> tuple[str, str]:
    """(«el oro», «del oro»): el artículo cambia según el activo y «de el» no existe."""
    el = ARTICULOS.get(nombre, f"el {nombre}")
    return el, el.replace("el ", "del ", 1) if el.startswith("el ") else f"de {el}"


def _estado_de_texto(ev: dict[str, Any]) -> str:
    estado = ev["estado"]
    if estado == "en_curso":
        pct = ev["avance_pct"]
        return "en_contra" if pct < 0 else "avance_mucho" if pct >= AVANCE_MUCHO else "a_favor"
    return "descartada" if estado == "rango_roto" else estado


def _armar(nombre: str, fecha_hoy: str, esc: dict[str, Any], ev: dict[str, Any], precio_vivo: float,
           lectura_hoy: str, digits: int, macro: dict[str, Any] | None = None, dia: str = "lunes") -> str:
    """El mensaje con la marca del saludo: un párrafo corto y sin precios que cierra con una pregunta.

    Con dato macro (`macro_seguimiento.redactar`) el cuerpo es el del dato; sin él, el del estado.
    """
    macro = macro or {}
    if macro.get("cuerpo"):
        return f"{MARCA_SALUDO} {macro['cuerpo']}"
    el, del_ = _activo_con_articulo(nombre)
    accion = "compra" if esc.get("direccion") == "ALCISTA" else "venta"
    plantilla = _variante(PLANTILLAS[_estado_de_texto(ev)], fecha_hoy, nombre)
    return f"{MARCA_SALUDO} " + plantilla.format(el=el, **{"del": del_}, accion=accion, dia=dia)


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
    dia = str((activo.get("foto") or {}).get("fecha") or "lunes").split()[0]
    macro: dict[str, Any] = {}
    if ctx_macro is not None and ahora is not None:
        try:
            from analista import macro_seguimiento as mac

            macro = mac.redactar(ctx_macro, datos["nombre"], None if ev["estado"] == "sin_simulacion" else esc,
                                 ev["estado"], ahora, digits, variante=_variante_n(fecha_hoy, datos["nombre"]),
                                 dia=dia)
        except Exception:  # noqa: BLE001  el dato macro es un extra: sin él, el seguimiento sale igual
            macro = {}
    texto = _armar(datos["nombre"], fecha_hoy, esc, ev, float(datos["precio_vivo"]), datos["lectura_hoy"],
                   digits, macro, dia)
    return con_saludo(texto, saludo), macro.get("aparte", "")
