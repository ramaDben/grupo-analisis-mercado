"""Carruseles de Avisos: la voz de los bancos contra nuestros datos, tres veces al día.

Spec: docs/superpowers/specs/2026-09-28-carruseles-avisos-design.md

El reparto es el mismo de `pipeline_carrusel`: el script prepara los datos y
deja los huecos en `[[ESCRIBIR]]`; el texto lo escribe el comando `/avisos`, y
`--rendir` se detiene ante un hueco, una cifra sin respaldo, una cita vieja o
datos de más de 2 horas.

La tanda se escribe con la carpeta que el despacho ya recorre
(`data/carrusel/<tanda>/01_macro_y_apertura/N_<lamina>.*`), así el único camino
al cliente sigue siendo `pipeline_carrusel.py --despachar`.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from datetime import date, datetime, time as dtime, timedelta
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import pipeline_carrusel as pc  # noqa: E402
import pipeline_linkedin as pl  # noqa: E402

SANTIAGO = ZoneInfo("America/Santiago")
CANAL = pc.CANAL_AVISOS
MARCA = pl.MARCA_EDITORIAL
DIR_PLANTILLAS = RAIZ / "templates" / "stories"

FRESCURA_MAX_HORAS = 2
VENTANA_VISION_DIAS = 14
VENTANA_COBERTURA_DIAS = 7
MAX_LAMINAS = 9
AVISO_LEGAL = "Análisis informativo. No constituye recomendación de inversión."
FIRMA = "Grupo Inteligencia · Equipo de análisis"

# Momento del reloj -> formato. "tarde" se resuelve por día de la semana.
# Spec §13 (2026-09-29): la agenda del día abre la jornada y cada dato fuerte
# tiene su resultado; el carrusel de mediodía salió, y el de la mañana (cita)
# solo corre los días sin datos de alto impacto.
MOMENTOS = {
    "avisos_agenda": "agenda_dia",
    "avisos_resultado": "resultado",
    "avisos_manana": "cita",
    "avisos_tarde": "tarde",
}

# La jornada de Avisos: desde la agenda (07:45) hasta la última noticia de
# Chile, el comunicado de la RPM de las 18:00, con media hora para su lectura.
INICIO_JORNADA = dtime(7, 45)
CIERRE_JORNADA = dtime(18, 30)

# Formatos sin activo protagonista: no llevan dirección técnica en el pie.
FORMATOS_SIN_ACTIVO = frozenset({"agenda", "agenda_dia", "resultado"})

# Formatos de una lámina cuyo pie escribe el editor entero: sin cierre, sin
# aviso legal (no citan niveles) y sin pie de posición.
FORMATOS_PIE_LIBRE = frozenset({"balance"})

SELLO_VOZ = "AVISOS · LA VOZ DEL BANCO"

# clave -> (_plantilla, nombre que ve el cliente en el pie de posición)
LAMINAS = {
    "portada": ("avisos_portada", "Portada"),
    "voz": ("vision", "La voz del banco"),
    "datos": ("avisos_datos", "Nuestros datos"),
    "semana": ("avisos_agenda", "La semana"),
    "dia": ("avisos_agenda", "La agenda de hoy"),
    "resultado": ("avisos_resultado", "Resultado del dato"),
    "lectura": ("avisos_lectura", "Nuestra lectura"),
}

SECUENCIAS = {
    "cita": ("portada", "voz", "datos", "lectura"),
    "meta": ("portada", "voz", "datos", "lectura"),
    # Una sola lámina (director, 2026-09-29): cuatro seguidas se leían como spam,
    # y los niveles ya salen en cada grupo temático. La voz y su pie son la pieza.
    "balance": ("voz",),
    "agenda": ("portada", "semana", "lectura"),
    "agenda_dia": ("portada", "dia", "lectura"),
    "resultado": ("resultado",),
}

# _plantilla -> archivo en templates/stories/. La lámina de datos se llama
# `avisos_datos` y no `alerta`: el refresco temático reescribe el mensaje con
# `construir_mensaje_alerta` y borraría el pie de posición.
PLANTILLAS = {
    "avisos_portada": "avisos_portada.html",
    "vision": "vision.html",
    "avisos_datos": "alerta.html",
    "avisos_agenda": "calendario.html",
    "avisos_resultado": "calendario.html",
    "avisos_lectura": "avisos_lectura.html",
}

_DIAS = ("LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO")
_MESES = ("ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC")


# ---------------------------------------------------------------- calendario


def es_dia_habil(fecha: date) -> bool:
    """Lunes a viernes y hábil en la bolsa de Nueva York (el calendario del escáner)."""
    from market_data_mcp.tools.symbol_spec import _cargar_feriados

    if fecha.weekday() >= 5:
        return False
    return fecha.isoformat() not in _cargar_feriados().get("NYSE", [])


class HoyNoCorresponde(RuntimeError):
    """El momento no produce tanda hoy, y es un resultado válido (código 0)."""


def formato_del_momento(momento: str, fecha: date) -> str:
    """El formato por momento y día. `agenda_dia` baja a `agenda` en `preparar`
    si la jornada no trae datos: eso depende del calendario, no de la fecha."""
    if momento not in MOMENTOS:
        raise SystemExit(f"Momento desconocido: {momento}. Opciones: {', '.join(MOMENTOS)}")
    formato = MOMENTOS[momento]
    if formato == "tarde":
        return "agenda" if fecha.weekday() == 0 else "balance"
    return formato


def laminas_de(formato: str, con_voz: bool) -> list[dict[str, str]]:
    """Las láminas del carrusel en orden, con su archivo y su pie de posición.

    El pie es obligatorio en toda lámina: si un envío se corta y se retoma, las
    que faltan pueden llegar separadas de las primeras y el pie le conserva el
    orden al lector.
    """
    claves = [c for c in SECUENCIAS[formato] if con_voz or c != "voz"]
    if len(claves) > MAX_LAMINAS:
        raise ValueError(
            f"{len(claves)} láminas: el despacho ordena como texto y desde 10 la `10_` "
            f"saldría antes que la `2_`. Máximo {MAX_LAMINAS}."
        )
    total = len(claves)
    # Una pieza sola no tiene orden que conservar: "1/1" sería ruido.
    sola = total == 1 and formato in FORMATOS_PIE_LIBRE
    return [
        {
            "clave": c,
            "stem": f"{i}_{c}",
            "plantilla": LAMINAS[c][0],
            "posicion": "" if sola else f"{i}/{total} · {LAMINAS[c][1]}",
        }
        for i, c in enumerate(claves, 1)
    ]


def etiqueta_hora(ahora: datetime) -> str:
    """HH:MM con CLT o CLST, del horario que de verdad rige ese instante."""
    local = ahora.astimezone(SANTIAGO)
    return f"{local:%H:%M} {'CLST' if local.dst() else 'CLT'}"


def fecha_hora(ahora: datetime) -> str:
    local = ahora.astimezone(SANTIAGO)
    return f"{_DIAS[local.weekday()]} {local.day} {_MESES[local.month - 1]} · {etiqueta_hora(local)}"


# ---------------------------------------------------------------- elección


class SinCandidatosError(RuntimeError):
    """Ningún activo disponible para el momento: no hay carrusel que preparar."""


class VisionPedidaError(RuntimeError):
    """La visión que pidió el director no se puede citar en esta tanda."""


def _errores_vision_pedida(vision: dict[str, Any] | None, vid: str, activo: str, hoy: date,
                           historial: list[dict[str, Any]]) -> list[str]:
    """Los mismos frenos del selector, dichos en voz alta en vez de saltar la visión."""
    if vision is None:
        return [f"`{vid}` no está en el registro de visiones"]
    if vision.get("activo") != activo:
        return [f"la visión `{vid}` es de {vision.get('activo')} y el activo pedido es {activo}"]
    if not vision_califica(vision, variante_de(vision), hoy, historial):
        return [f"la visión `{vid}` no califica: revisa fecha (máximo {pl.ANTIGUEDAD_MAX_DIAS} días), "
                f"campos obligatorios y uso en Avisos ({VENTANA_VISION_DIAS} días)"]
    return []


def variante_de(vision: dict[str, Any]) -> str:
    """Una paráfrasis con cifra de proyección es una meta; lo demás, una cita."""
    if vision.get("tipo") == "parafrasis" and pl._PRECIO.search(str(vision.get("cita", ""))):
        return "meta"
    return "cita"


def _edad_dias(entrada: dict[str, Any], hoy: date) -> int | None:
    try:
        return (hoy - date.fromisoformat(str(entrada.get("fecha")))).days
    except ValueError:
        return None


def _entradas(historial: list[dict[str, Any]], tipo: str) -> list[dict[str, Any]]:
    return [e for e in historial if e.get("tipo") == tipo and e.get("canal") == CANAL]


def vision_califica(vision: dict[str, Any], variante: str, hoy: date,
                    historial: list[dict[str, Any]]) -> bool:
    if variante_de(vision) != variante:
        return False
    if variante == "meta":
        meta = str(vision.get("meta", "")).strip()
        if not str(vision.get("horizonte", "")).strip() or not meta:
            return False
        if meta not in str(vision.get("cita", "")):
            return False  # la lámina mostraría una meta que la cita no respalda
    if pl.validar_vision(vision, hoy, None):
        return False
    for e in _entradas(historial, "vision"):
        edad = _edad_dias(e, hoy)
        if e.get("clave") == vision.get("id") and edad is not None and edad < VENTANA_VISION_DIAS:
            return False
    return True


def coberturas(historial: list[dict[str, Any]], hoy: date, dias: int) -> dict[str, int]:
    cuenta: dict[str, int] = {}
    for e in _entradas(historial, "avisos"):
        edad = _edad_dias(e, hoy)
        if edad is not None and 0 <= edad < dias:
            cuenta[e["clave"]] = cuenta.get(e["clave"], 0) + 1
    return cuenta


def cubiertos_hoy(historial: list[dict[str, Any]], hoy: date) -> set[str]:
    return {e["clave"] for e in _entradas(historial, "avisos") if e.get("fecha") == hoy.isoformat()}


def candidatos(hoy: date, historial: list[dict[str, Any]], universo: list[str] | None = None) -> list[str]:
    import screener_gi as sc

    if universo is None:
        from pipeline_informe import ACTIVOS_INFORME

        universo = list(dict.fromkeys([*ACTIVOS_INFORME, *sc.cobertura_fija()]))
    hechos = cubiertos_hoy(historial, hoy)
    return [t for t in universo if t not in hechos and sc.gate_feriado(t, hoy) is None]


def elegir(variante: str, hoy: date, visiones: dict[str, dict[str, Any]],
           historial: list[dict[str, Any]], universo: list[str] | None = None) -> tuple[str, str | None]:
    """El activo del carrusel y su visión (o `None`, que es `_falta_vision`).

    No usa el `Score_GI`: el score mide espacio para operar en el día, y lo que
    hace valer un carrusel de Avisos es que haya una voz de banco que contrastar.
    """
    cands = candidatos(hoy, historial, universo)
    if not cands:
        raise SinCandidatosError("Avisos ya cubrió hoy todos los activos disponibles.")
    cobertura = coberturas(historial, hoy, VENTANA_COBERTURA_DIAS)
    catalogo = pl._catalogo()
    mejor: dict[str, dict[str, Any]] = {}
    for v in visiones.values():
        t = v.get("activo")
        if t in cands and vision_califica(v, variante, hoy, historial):
            actual = mejor.get(t)
            if actual is None or (v["fecha"], v["id"]) > (actual["fecha"], actual["id"]):
                mejor[t] = v

    def orden(t: str) -> tuple[int, bool, str]:
        # Antes del orden alfabético: cobertura, y luego si el activo tiene
        # foto (`imagen`) en el catálogo. Sin ella el escáner ni siquiera lo
        # cubre (interruptor del activo), así que un desempate ciego podía
        # elegir uno fuera de la rotación diaria (BRENT.spot, sin `.jpg`).
        tiene_imagen = bool(catalogo.get(t, {}).get("imagen"))
        return (cobertura.get(t, 0), not tiene_imagen, t)

    if mejor:
        t = min(mejor, key=orden)
        return t, mejor[t]["id"]
    return min(cands, key=orden), None


def activo_del_balance(historial: list[dict[str, Any]], hoy: date) -> tuple[str | None, str | None]:
    """El activo y la visión de la mañana; si no hubo, los del mediodía.

    El mediodía ya no se prepara (spec §13), pero el historial viejo lo tiene.
    """
    usos = [e for e in _entradas(historial, "avisos") if e.get("fecha") == hoy.isoformat()]
    for momento in ("avisos_manana", "avisos_mediodia"):
        for e in reversed(usos):
            if e.get("momento") == momento:
                return e["clave"], e.get("vision")
    return None, None


def _ruta_historial(ruta: Path | None) -> Path:
    from suplemento_canal import HISTORIAL

    return ruta or HISTORIAL


def cargar_historial(ruta: Path | None = None) -> list[dict[str, Any]]:
    from suplemento_canal import cargar_historial as _cargar

    return _cargar(_ruta_historial(ruta))


def registrar_uso(hoy: date, momento: str, activo: str | None, vision_id: str | None,
                  gastar_vision: bool, ruta: Path | None = None) -> None:
    """Se anota al PREPARAR: una tanda descartada gasta la ventana, hacia el lado seguro."""
    destino = _ruta_historial(ruta)
    historial = cargar_historial(destino)
    if vision_id and gastar_vision:
        historial.append({"fecha": hoy.isoformat(), "canal": CANAL, "tipo": "vision", "clave": vision_id})
    if activo:
        historial.append({"fecha": hoy.isoformat(), "canal": CANAL, "tipo": "avisos",
                          "clave": activo, "momento": momento, "vision": vision_id})
    destino.write_text(json.dumps(historial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def registrar_vision_completada(hoy: date, momento: str, activo: str, vision_id: str,
                                ruta: Path | None = None) -> None:
    """Gasta la visión y la anota en el uso "avisos" de ese momento.

    `activo_del_balance` lee la visión desde la entrada "avisos": si solo se
    agregara la entrada "vision", el balance de la tarde saldría sin la voz que
    el director completó en la mañana.
    """
    destino = _ruta_historial(ruta)
    historial = cargar_historial(destino)
    historial.append({"fecha": hoy.isoformat(), "canal": CANAL, "tipo": "vision", "clave": vision_id})
    for e in historial:
        if (e.get("tipo") == "avisos" and e.get("canal") == CANAL and e.get("fecha") == hoy.isoformat()
                and e.get("momento") == momento and e.get("clave") == activo):
            e["vision"] = vision_id
    destino.write_text(json.dumps(historial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ---------------------------------------------------------------- láminas

CAMPOS_AVISOS = pl.CAMPOS_PRECIO + ("soporte_publicado", "resistencia_publicada")

_PAISES = {"United States": "EE.UU.", "Chile": "Chile", "China": "China",
           "Euro Zone": "Zona Euro", "Euro Area": "Zona Euro", "Zona Euro": "Zona Euro"}
_ETIQUETA_TIPO = {"textual": "", "traduccion": "Traducción nuestra", "parafrasis": "En palabras nuestras"}
CTA_AGENDA = ("¿Quieres seguir esta semana en detalle?", "Habla hoy con tu analista")
# La agenda no tiene activo ni niveles: sus cierres hablan de planificar la
# semana, no de bordes ni de precio como los de `pc.CIERRES_ALERTA`.
CIERRES_AGENDA: tuple[str, ...] = (
    "Anota estos datos en tu calendario y arma tu semana con tiempo.",
    "Cada dato suma una pieza: te lo vamos contando a medida que salga.",
    "¿Cuál de estos datos te interesa más? Te leemos en el grupo.",
    "Planifica tu semana con la agenda a la vista y sin apuro.",
)


def _fmt(valor: float, digits: int) -> str:
    return pc.formatear_precio(float(valor), digits)


def _fecha_corta(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} {_MESES[d.month - 1]} {d.year}"


def fila_medida(lectura: dict[str, Any], payload_datos: dict[str, Any] | None) -> dict[str, Any]:
    """Lo que el texto puede citar: los niveles del terminal y los publicados en la alerta.

    El director puede fijar a mano los niveles de la alerta (`niveles_fijados`),
    así que el soporte que ve el cliente puede no ser el `s1` crudo: los dos
    cuentan como medidos.
    """
    niveles = ({n["rol"]: n["precio"] for n in payload_datos["recorrido"]["niveles"]}
               if payload_datos else {})
    fila: dict[str, Any] = {"nombre": lectura["activo"]["nombre"], "digits": lectura["activo"]["digits"]}
    fila.update({c: lectura["h1"].get(c) for c in pl.CAMPOS_PRECIO})
    fila["soporte_publicado"] = niveles.get("SOPORTE")
    fila["resistencia_publicada"] = niveles.get("RESISTENCIA")
    return fila


def lamina_portada(activo_nombre: str | None, precio: str, leido: datetime, ahora: datetime,
                   agenda: bool, ticker: str | None = None,
                   sello_agenda: str = "AVISOS · AGENDA DE LA SEMANA") -> dict[str, Any]:
    # Spec §3.7.4: toda lámina con precio lleva _procedencia.ticker; la agenda no tiene precio.
    if not agenda and not ticker:
        raise ValueError("la portada con precio exige el ticker de su procedencia")
    return {
        "_plantilla": "avisos_portada", "plantilla": "avisos_portada",
        "sello": sello_agenda if agenda else f"AVISOS · {str(activo_nombre).upper()}",
        "fecha_hora": fecha_hora(ahora),
        "kicker": MARCA, "titular": MARCA, "parrafo": MARCA,
        "claves": [{"texto": MARCA} for _ in range(3)],
        "pie": MARCA,
        "dato_precio": "" if agenda else f"{activo_nombre} {precio}",
        "dato_hora": "" if agenda else f"LEÍDO {etiqueta_hora(leido)}",
        "total_laminas": "", "posicion": "",
        "_procedencia": {"ticker": None if agenda else ticker},
    }


def lamina_voz(vision: dict[str, Any], variante: str, fila: dict[str, Any], leido: datetime,
               ahora: datetime, con_pie: bool = False) -> dict[str, Any]:
    """La cita. `con_pie` cuando es la única lámina: su pie es el mensaje entero.

    El sello dice "la voz del banco" salvo que la visión declare el suyo: quien
    habla puede no ser un banco (el 2026-09-29 fue el presidente de la Cámara).
    """
    firma = f"{vision['quien']} · {vision['institucion']}"
    fuente_fecha = f"{vision.get('fuente') or vision['institucion']} · {_fecha_corta(vision['fecha'])}"
    if variante == "meta":
        bloque_cita: list[dict[str, str]] = []
        bloque_meta = [{
            "meta": vision["meta"], "horizonte": vision["horizonte"], "firma": firma,
            "precio_hoy": _fmt(fila["price"], fila["digits"]), "hora_precio": etiqueta_hora(leido),
            "fuente_fecha": fuente_fecha,
        }]
    else:
        tipo = vision.get("tipo", "textual")
        cita = vision["cita"] if tipo == "parafrasis" else f"“{vision['cita']}”"
        bloque_cita = [{"etiqueta": _ETIQUETA_TIPO.get(tipo, ""), "cita": cita, "firma": firma,
                        "fuente_fecha": fuente_fecha}]
        bloque_meta = []
    return {
        "_plantilla": "vision", "plantilla": "vision",
        "_procedencia": {"vision": vision["id"], "ticker": vision.get("activo")},
        "sello": vision.get("sello") or SELLO_VOZ, "fecha_hora": fecha_hora(ahora),
        "titular": MARCA, "parrafo": MARCA,
        "bloque_cita": bloque_cita, "bloque_meta": bloque_meta, "posicion": "",
        **({"pie": MARCA} if con_pie else {}),
    }


def lamina_datos(lectura: dict[str, Any], ahora: datetime) -> dict[str, Any]:
    payload = pc.construir_payload(lectura["seleccion"], lectura["activo"], ahora, lectura["cierres"])
    payload.update({"_plantilla": "avisos_datos", "titular": MARCA, "parrafo": MARCA,
                    "disclaimer": AVISO_LEGAL})
    return payload


def eventos_calendario(agenda: list[dict[str, Any]], ahora: datetime, maximo: int = 6) -> list[dict[str, Any]]:
    """Los tokens que espera `calendario.html`, que antes nadie armaba.

    Solo los días hábiles de la semana de `ahora` (lunes a viernes), en orden de
    reloj. `leer_agenda` ya entrega la hora en Santiago: no se vuelve a convertir.
    """
    local = ahora.astimezone(SANTIAGO)
    lunes = local.date() - timedelta(days=local.weekday())
    viernes = lunes + timedelta(days=4)
    elegidos = []
    for ev in agenda:
        cuando = datetime.strptime(f"{ev['fecha']} {ev['hora']}", "%Y-%m-%d %H:%M").replace(tzinfo=SANTIAGO)
        if lunes <= cuando.date() <= viernes:
            elegidos.append((cuando, ev))
    elegidos.sort(key=lambda par: par[0])
    salida = []
    for i, (cuando, ev) in enumerate(elegidos[:maximo], 1):
        esperado = str(ev.get("consenso") or "").strip()
        salida.append({
            "numero": f"{i:02d}",
            "dia": f"{_DIAS[cuando.weekday()]} {cuando.day}",
            "hora": etiqueta_hora(cuando),
            "evento": ev.get("nombre_es") or ev.get("evento", ""),
            "pais": _PAISES.get(ev.get("pais", ""), ev.get("pais", "")),
            "impacto": "Alto impacto", "impacto_slug": "alto",
            "anterior": str(ev.get("anterior") or ""),
            "esperado": esperado, "tiene_esperado": bool(esperado),
        })
    return salida


def lamina_semana(agenda: list[dict[str, Any]], ahora: datetime) -> dict[str, Any]:
    return {
        "_plantilla": "avisos_agenda", "plantilla": "calendario",
        "sello": "AVISOS · AGENDA DE LA SEMANA", "fecha_hora": fecha_hora(ahora),
        "titular": MARCA, "parrafo": MARCA,
        "eventos": eventos_calendario(agenda, ahora),
        "cta": CTA_AGENDA[0], "cta_sub": CTA_AGENDA[1], "posicion": "",
    }


def lamina_lectura(ahora: datetime) -> dict[str, Any]:
    return {
        "_plantilla": "avisos_lectura", "plantilla": "avisos_lectura",
        "sello": "AVISOS · NUESTRA LECTURA", "fecha_hora": fecha_hora(ahora),
        "titular": MARCA, "parrafo": MARCA,
        "puntos": [{"icono": "🔎", "titulo_punto": MARCA, "texto": MARCA} for _ in range(3)],
        "firma": FIRMA, "aviso_legal": AVISO_LEGAL, "posicion": "",
    }


# ---------------------------------------------------------------- la jornada


CIERRES_DIA: tuple[str, ...] = (
    "Te contamos cada resultado apenas salga.",
    "Anota las horas: antes de un dato fuerte el precio suele moverse poco.",
    "¿Cuál de estos datos te interesa más? Te leemos en el grupo.",
    "Planifica tus operaciones pensando en estas horas.",
)

VEREDICTOS = {"peor": ("Peor", "📉"), "mejor": ("Mejor", "📈"), "en_linea": ("En línea", "➖")}

# País del dato -> monedas que se miden en el resultado (spec §13.4).
MONEDAS_DEL_DATO: dict[str, tuple[str, ...]] = {
    "United States": ("USDCLP", "XAUUSD"),
    "Chile": ("USDCLP",),
    "Euro Zone": ("EURUSD", "XAUUSD"),
    "Euro Area": ("EURUSD", "XAUUSD"),
    "China": ("COPPER", "USDCLP"),
}
ROTULOS_MONEDA = {"USDCLP": ("Dólar", "el USD/CLP"), "XAUUSD": ("Oro", "el oro"),
                  "EURUSD": ("Euro", "el EUR/USD"), "COPPER": ("Cobre", "el cobre"),
                  "WTI.spot": ("Petróleo WTI", "el WTI")}
_PARES_CON_NOMBRE = frozenset({"USDCLP", "EURUSD"})
TEMPORALIDAD_RESULTADO = "intradía (dentro de la jornada)"
CALENDARIO_URL = "https://es.investing.com/economic-calendar/"
# Minutos que el resultado espera la cifra antes de darla por ausente: la fuente
# publica con retraso, y un discurso nunca trae cifra.
ESPERA_CIFRA_MIN = 90
# Datos de la misma hora van juntos: si uno ya trae cifra y el otro no, se
# espera un rato antes de publicar el que está, para no partir la pieza.
ESPERA_COMPANERO_MIN = 20


def _cuando(ev: dict[str, Any]) -> datetime:
    return datetime.strptime(f"{ev['fecha']} {ev['hora']}", "%Y-%m-%d %H:%M").replace(tzinfo=SANTIAGO)


def leer_jornada(ahora: datetime) -> tuple[list[dict[str, Any]], list[str]]:
    """Los datos de alto impacto de HOY entre las 07:45 y las 18:30, en hora de Chile.

    Trae los que ya salieron (con `actual`) y los que faltan: la agenda mira
    hacia adelante y el resultado hacia atrás. `cargar_calendario` entrega la
    hora en America/Santiago y no se vuelve a convertir (issue #38).
    """
    from market_data_mcp.tools.calendar import cargar_calendario

    res = cargar_calendario(solo_hoy=True, min_impact="high", ahora=ahora)
    if "error" in res:
        return [], [f"calendario no disponible ({res['error']})"]
    hoy = ahora.astimezone(SANTIAGO).date()
    eventos: list[dict[str, Any]] = []
    for ev in res.get("eventos", []):
        try:
            cuando = datetime.strptime(ev["hora_servidor"], "%Y-%m-%d %H:%M").replace(tzinfo=SANTIAGO)
        except (KeyError, ValueError):
            continue
        if cuando.date() != hoy or not (INICIO_JORNADA <= cuando.time() <= CIERRE_JORNADA):
            continue
        dic = ev.get("diccionario") or {}
        eventos.append({
            "fecha": cuando.strftime("%Y-%m-%d"), "hora": cuando.strftime("%H:%M"),
            "pais": ev.get("pais", ""), "evento": ev.get("nombre", ""),
            "nombre_es": dic.get("nombre_es", ""), "explicacion": dic.get("explicacion", ""),
            "consenso": ev.get("forecast", ""), "anterior": ev.get("previo", ""),
            "actual": ev.get("actual", ""), "resultado": ev.get("resultado", ""),
        })
    eventos.sort(key=_cuando)
    return eventos, []


def _cifra(valor: Any) -> str:
    from pipeline_informe import _cifra_es

    return _cifra_es(str(valor or "").strip())


_FUENTE_ENTRE_PARENTESIS = re.compile(r"\s*\((?=[^)]*\s)[^)]*\)")


def _nombre_evento(ev: dict[str, Any]) -> str:
    """El nombre en español con su país. Un paréntesis con espacios es el nombre de
    la fuente ("(The Conference Board)") y se quita de la fila; una sigla ("(JOLTS)")
    se queda, porque es lo que el cliente va a volver a leer en las noticias."""
    nombre = _FUENTE_ENTRE_PARENTESIS.sub("", ev.get("nombre_es") or ev.get("evento", "")).strip()
    pais = _PAISES.get(ev.get("pais", ""), ev.get("pais", ""))
    return f"{nombre} de {pais}" if pais and pais not in nombre else nombre


def _tokens_evento(i: int, ev: dict[str, Any], dia: str, con_resultado: bool) -> dict[str, Any]:
    esperado = _cifra(ev.get("consenso"))
    fila = {
        "numero": f"{i:02d}", "dia": dia, "hora": etiqueta_hora(_cuando(ev)),
        "evento": _nombre_evento(ev),
        "pais": _PAISES.get(ev.get("pais", ""), ev.get("pais", "")),
        "impacto": "Alto impacto", "impacto_slug": "alto",
        "anterior": _cifra(ev.get("anterior")),
        "esperado": esperado, "tiene_esperado": bool(esperado),
        "actual": "", "tiene_actual": False,
    }
    if con_resultado:
        etiqueta, _ = VEREDICTOS.get(ev.get("resultado", ""), ("Publicado", "📊"))
        fila.update(actual=_cifra(ev.get("actual")), tiene_actual=True,
                    impacto=etiqueta, impacto_slug=ev.get("resultado") or "alto")
    return fila


def lamina_dia(eventos: list[dict[str, Any]], ahora: datetime) -> dict[str, Any]:
    dia = f"HOY {ahora.astimezone(SANTIAGO).day}"
    return {
        "_plantilla": "avisos_agenda", "plantilla": "calendario",
        "sello": "AVISOS · AGENDA DEL DÍA", "fecha_hora": fecha_hora(ahora),
        "titular": MARCA, "parrafo": MARCA,
        "eventos": [_tokens_evento(i, ev, dia, False) for i, ev in enumerate(eventos[:6], 1)],
        "cta": "¿Quieres entender cómo operar estos datos?", "cta_sub": CTA_AGENDA[1], "posicion": "",
    }


_VERBO_INFINITIVO = {"sube": "subir", "baja": "bajar"}


def frase_reaccion(efecto: dict[str, Any] | None) -> str | None:
    """Qué hacen el dólar, el USD/CLP, el oro y el petróleo si el dato sale sobre lo esperado.

    Sale del glosario (`si_sale_sobre_consenso`), nunca de la redacción: si el
    dato no declara su efecto, la lectura queda por escribir y el render frena.
    """
    if not efecto:
        return None
    partes: dict[str, list[str]] = {"subir": [], "bajar": []}
    for clave, nombre in (("dolar", "el dólar"), ("usdclp", "el USD/CLP"), ("oro", "el oro"),
                          ("petroleo", "el petróleo")):
        verbo = _VERBO_INFINITIVO.get(str(efecto.get(clave, "")))
        if verbo:
            partes[verbo].append(nombre)
    trozos = [f"{' y '.join(nombres)} a {verbo}" for verbo, nombres in partes.items() if nombres]
    if not trozos:
        return None
    verbo = "tienden" if sum(map(len, partes.values())) > 1 else "tiende"
    return f"Sobre lo esperado {verbo} {', y '.join(trozos)}. Bajo lo esperado, al revés."


def _efecto_del_glosario(ev: dict[str, Any]) -> dict[str, Any] | None:
    from clasificacion_macro import efecto_direccional

    return efecto_direccional({"nombre": ev.get("evento", ""), "pais": ev.get("pais", "")})


def lamina_lectura_dia(eventos: list[dict[str, Any]], ahora: datetime,
                       efecto_de: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None) -> dict[str, Any]:
    efecto_de = efecto_de or _efecto_del_glosario
    # Un indicador a la misma hora es un solo punto: el PCE mensual y el anual
    # (2026-09-30) salían como dos puntos idénticos y dejaban fuera al PIB.
    unicos: dict[tuple[str, str], dict[str, Any]] = {}
    for ev in eventos:
        unicos.setdefault((ev["hora"], ev.get("nombre_es") or ev.get("evento", "")), ev)
    puntos = []
    for ev in list(unicos.values())[:3]:
        reaccion = frase_reaccion(efecto_de(ev))
        explicacion = str(ev.get("explicacion") or "").strip()
        texto = f"{explicacion} {reaccion}".strip() if reaccion else MARCA
        puntos.append({"icono": "🕐", "titulo_punto": f"{ev['hora']} · {ev.get('nombre_es') or ev.get('evento', '')}",
                       "texto": texto})
    lamina = lamina_lectura(ahora)
    lamina["puntos"] = puntos
    return lamina


def titular_resultado(eventos: list[dict[str, Any]]) -> str:
    """El titular sale del veredicto, no de la redacción: datos de la misma hora
    van juntos, y si se contradicen el titular lo dice (spec §13.4)."""
    veredictos = {ev.get("resultado") or "" for ev in eventos}
    plural = len(eventos) > 1
    if veredictos == {"peor"}:
        return "Datos más débiles de lo esperado" if plural else "Dato más débil de lo esperado"
    if veredictos == {"mejor"}:
        return "Datos más fuertes de lo esperado" if plural else "Dato más fuerte de lo esperado"
    if veredictos == {"en_linea"}:
        return "Datos en línea con lo esperado" if plural else "Dato en línea con lo esperado"
    return f"Señales mixtas en los datos de las {eventos[0]['hora']}"


# Fracción del ATR 14 de M15 bajo la que un movimiento es ruido y no reacción.
# El 2026-09-30 el resultado de la EIA se frenó dos veces con el WTI moviéndose
# 0,04, 0,07 y 0,00 desde las 11:30: sin banda muerta, un tick daba vuelta la
# dirección y el freno saltaba con el precio quieto.
FRACCION_BANDA_RUIDO = 0.25


def banda_de_ruido(velas_m15: list[dict[str, Any]]) -> float:
    """Un cuarto del ATR 14 de M15: lo que el activo se mueve solo, sin noticia."""
    tr = []
    for i, v in enumerate(velas_m15):
        rango = float(v["high"]) - float(v["low"])
        if i:
            previo = float(velas_m15[i - 1]["close"])
            rango = max(rango, abs(float(v["high"]) - previo), abs(float(v["low"]) - previo))
        tr.append(rango)
    ultimas = tr[-14:]
    return FRACCION_BANDA_RUIDO * sum(ultimas) / len(ultimas) if ultimas else 0.0


def _verbo_movimiento(desde: float, hasta: float, banda: float = 0.0) -> str:
    if abs(hasta - desde) <= banda:
        return "se mantiene"
    return "sube" if hasta > desde else "cede"


def _verbo(m: dict[str, Any]) -> str:
    return _verbo_movimiento(m["desde"], m["ahora"], float(m.get("banda") or 0.0))


def _trozo_movimiento(ticker: str, m: dict[str, Any]) -> str:
    _, sujeto = ROTULOS_MONEDA.get(ticker, (ticker, ticker))
    verbo = _verbo(m)
    a, b = _fmt(m["desde"], m["digits"]), _fmt(m["ahora"], m["digits"])
    if verbo == "se mantiene":
        # Dentro de la banda no se narra "sube de A a B" por centavos de ruido.
        return f"{sujeto} se mantiene {'en' if a == b else 'cerca de'} {b}"
    return f"{sujeto} {verbo} de {a} a {b}"


def frase_movimiento(movimientos: dict[str, dict[str, Any]], hora: str) -> str:
    """Desde las 11:00 el USD/CLP cede de 970,80 a 968,97 y el oro sube de…"""
    trozos = [_trozo_movimiento(t, m) for t, m in movimientos.items()]
    cuerpo = trozos[0] if len(trozos) == 1 else ", ".join(trozos[:-1]) + " y " + trozos[-1]
    return f"Desde las {hora} {cuerpo}."


def lamina_resultado(eventos: list[dict[str, Any]], movimientos: dict[str, dict[str, Any]],
                     ahora: datetime) -> dict[str, Any]:
    dia = f"HOY {ahora.astimezone(SANTIAGO).day}"
    return {
        "_plantilla": "avisos_resultado", "plantilla": "calendario",
        "sello": "AVISOS · RESULTADO DEL DATO", "fecha_hora": fecha_hora(ahora),
        "titular": titular_resultado(eventos),
        "movimiento": frase_movimiento(movimientos, eventos[0]["hora"]),
        "parrafo": MARCA,
        "eventos": [_tokens_evento(i, ev, dia, True) for i, ev in enumerate(eventos[:6], 1)],
        "cta": "¿Quieres entender cómo operar tras un dato?", "cta_sub": CTA_AGENDA[1], "posicion": "",
        "_procedencia": {"tickers": list(movimientos)},
    }


def mensaje_resultado(payload: dict[str, Any], meta: dict[str, Any]) -> str:
    """El pie de la imagen (Modo resultado, issue #93): veredicto, qué significa,
    el movimiento medido y la temporalidad. Solo `parrafo` es editorial."""
    sep = "━━━━━━━━━━━━━━━━━━━"
    eventos = meta["eventos"]
    paises = dict.fromkeys(_PAISES.get(e.get("pais", ""), e.get("pais", "")) for e in eventos)
    lineas = [f"📊 *DATO MACRO · {' · '.join(paises).upper()}* · {meta['hora_dato']} hrs Chile", sep]
    for ev in eventos:
        etiqueta, emoji = VEREDICTOS.get(ev.get("resultado", ""), ("Publicado", "📊"))
        esperado = _cifra(ev.get("consenso"))
        cola = f" frente a {esperado} esperado" if esperado else ""
        nombre = ev.get("nombre_es") or ev.get("evento")
        lineas.append(f"{emoji} *{nombre}*: {_cifra(ev.get('actual'))}{cola} → *{etiqueta.upper()}*")
    lineas += [sep, f"🎯 *Qué significa*: {str(payload.get('parrafo', '')).strip()}"]
    for ticker, m in meta["movimientos"].items():
        rotulo, _ = ROTULOS_MONEDA.get(ticker, (ticker, ticker))
        flecha = {"sube": "⬆️", "cede": "⬇️"}.get(_verbo(m), "↔️")
        trozo = _trozo_movimiento(ticker, m)
        # "Oro: el oro sube" repite el rótulo; el par sí se nombra, porque aclara cuál es.
        if ticker not in _PARES_CON_NOMBRE:
            trozo = trozo.split(" ", 2)[2]
        lineas.append(f"{flecha} *{rotulo}*: {trozo[:1].upper()}{trozo[1:]} desde las {meta['hora_dato']}.")
    cierre = pc.elegir_variante(pc.CIERRES_ALERTA, "resultado", meta["momento"], meta["fecha"])
    lineas += [
        sep,
        f"⏱️ *Temporalidad del impacto*: {TEMPORALIDAD_RESULTADO}",
        "⚠️ La primera reacción es rápida y a veces se revierte: los niveles de cada activo están en sus grupos.",
        f"🔗 Calendario completo: {CALENDARIO_URL}",
        cierre,
        f"_{AVISO_LEGAL}_",
    ]
    return "\n".join(lineas)


def leer_movimiento(ticker: str, desde: datetime, ahora: datetime) -> dict[str, Any]:
    """Precio a la hora del dato (apertura de la vela M1) y precio actual, del terminal.

    MT5 entrega la hora del SERVIDOR empaquetada como timestamp UTC: el offset
    se mide contra el reloj en vez de suponerlo (CLAUDE.md, "Ojo con MT5").
    """
    import time as _time

    from market_data_mcp import mt5_client

    try:
        mt5_client.connect()
        import MetaTrader5 as mt5  # noqa: PLC0415
    except Exception as exc:  # noqa: BLE001
        raise LecturaFallidaError(f"MT5 no conectó ({exc.__class__.__name__})") from exc
    info = mt5.symbol_info(ticker)
    tick = mt5.symbol_info_tick(ticker)
    if info is None or tick is None:
        raise LecturaFallidaError(f"{ticker}: sin cotización en el terminal")
    offset = round((tick.time - _time.time()) / 3600) * 3600
    objetivo = desde.timestamp() + offset
    velas = mt5.copy_rates_from_pos(ticker, mt5.TIMEFRAME_M1, 0, 600)
    previas = [v for v in (velas if velas is not None else []) if v["time"] <= objetivo]
    if not previas:
        raise LecturaFallidaError(f"{ticker}: sin velas M1 a la hora del dato")
    m15 = mt5.copy_rates_from_pos(ticker, mt5.TIMEFRAME_M15, 1, 15)
    banda = banda_de_ruido(list(m15)) if m15 is not None and len(m15) else 0.0
    return {"desde": float(previas[-1]["open"]), "ahora": float(tick.bid), "digits": int(info.digits),
            "banda": round(banda, int(info.digits) + 1)}


def monedas_de(eventos: list[dict[str, Any]]) -> list[str]:
    tickers: list[str] = []
    for ev in eventos:
        for t in MONEDAS_DEL_DATO.get(ev.get("pais", ""), ("USDCLP",)):
            if t not in tickers:
                tickers.append(t)
    return tickers


def resultado_pendiente(jornada: list[dict[str, Any]], ahora: datetime,
                        ya_hecho: Callable[[str], bool]) -> list[dict[str, Any]] | None:
    """El grupo de datos (misma hora) que toca publicar, o `None` si no hay.

    Lanza `LecturaFallidaError` (código 1: el latido reintenta) cuando la hora
    ya pasó y la cifra todavía no llega, o cuando llegó solo la de uno de los
    datos de esa hora y conviene esperar al otro para no partir la pieza.
    """
    horas = sorted({ev["hora"] for ev in jornada if _cuando(ev) <= ahora})
    for hora in horas:
        if ya_hecho(hora):
            continue
        grupo = [ev for ev in jornada if ev["hora"] == hora]
        con_cifra = [ev for ev in grupo if str(ev.get("actual") or "").strip()]
        minutos = (ahora - _cuando(grupo[0])).total_seconds() / 60
        if not con_cifra:
            if minutos < ESPERA_CIFRA_MIN:
                raise LecturaFallidaError(f"los datos de las {hora} todavía no traen cifra")
            continue  # un discurso o un dato sin cifra: no hay resultado que contar
        if len(con_cifra) < len(grupo) and minutos < ESPERA_COMPANERO_MIN:
            raise LecturaFallidaError(f"de los datos de las {hora} falta la cifra de alguno")
        return con_cifra
    return None


def armar_tanda(momento: str, formato: str, ahora: datetime, lectura: dict[str, Any] | None,
                vision: dict[str, Any] | None, agenda: list[dict[str, Any]],
                extra: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    extra = extra or {}
    agenda_semana = formato in FORMATOS_SIN_ACTIVO
    laminas: dict[str, dict[str, Any]] = {}
    activos: dict[str, dict[str, Any]] = {}
    direccion = None
    if formato == "agenda_dia":
        laminas["portada"] = lamina_portada(None, "", ahora, ahora, agenda=True,
                                            sello_agenda="AVISOS · AGENDA DEL DÍA")
        laminas["dia"] = lamina_dia(agenda, ahora)
    elif formato == "resultado":
        laminas["resultado"] = lamina_resultado(agenda, extra["movimientos"], ahora)
    elif agenda_semana:
        laminas["portada"] = lamina_portada(None, "", ahora, ahora, agenda=True)
        laminas["semana"] = lamina_semana(agenda, ahora)
    else:
        datos = lamina_datos(lectura, ahora)
        fila = fila_medida(lectura, datos)
        activos[lectura["ticker"]] = fila
        direccion = pc.direccion_publicada(lectura["seleccion"]["direccion"])
        laminas["portada"] = lamina_portada(lectura["activo"]["nombre"], datos["precio_actual"],
                                            ahora, ahora, agenda=False, ticker=lectura["ticker"])
        if vision is not None:
            variante = variante_de(vision)
            laminas["voz"] = lamina_voz(vision, variante, fila, ahora, ahora,
                                        con_pie=formato in FORMATOS_PIE_LIBRE)
        laminas["datos"] = datos
        # La lectura sigue midiendo (la cita con meta necesita el precio y el
        # despacho, la hora de lectura), pero solo salen las láminas del formato.
        laminas = {c: laminas[c] for c in SECUENCIAS[formato] if c in laminas}
    if formato == "agenda_dia":
        laminas["lectura"] = lamina_lectura_dia(agenda, ahora, extra.get("efecto_de"))
    elif "lectura" in SECUENCIAS[formato]:
        laminas["lectura"] = lamina_lectura(ahora)
    meta = {
        "version": 1, "momento": momento, "formato": formato, "fecha": ahora.date().isoformat(),
        "activo": None if agenda_semana else lectura["ticker"],
        "vision": vision["id"] if vision else None,
        "vision_variante": variante_de(vision) if vision else None,
        "_falta_vision": (not agenda_semana) and vision is None,
        "leido_en": ahora.isoformat(timespec="minutes"),
        "direccion": direccion,
        "activos": activos,
        "activos_preparacion": json.loads(json.dumps(activos)),
        "cifras_citadas": {}, "aceptar_antiguas": {},
    }
    if formato == "resultado":
        meta.update(hora_dato=agenda[0]["hora"], eventos=agenda,
                    movimientos=extra["movimientos"],
                    movimientos_preparacion=copy.deepcopy(extra["movimientos"]))
    return meta, laminas


# ---------------------------------------------------------------- disco


def escribir_meta(dir_canal: Path, meta: dict[str, Any]) -> None:
    (dir_canal / "_avisos.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def leer_meta(dir_canal: Path) -> dict[str, Any]:
    return json.loads((dir_canal / "_avisos.json").read_text(encoding="utf-8"))


def _archivos_de_lamina(dir_canal: Path) -> list[Path]:
    return [p for p in dir_canal.iterdir() if p.is_file() and p.name[:1].isdigit()]


def escribir_laminas(dir_canal: Path, formato: str, laminas: dict[str, dict[str, Any]]) -> None:
    """Escribe las láminas numeradas desde cero. Renumerar es borrar y volver a escribir."""
    for viejo in _archivos_de_lamina(dir_canal):
        viejo.unlink()
    orden = laminas_de(formato, con_voz="voz" in laminas)
    total = f"{len(orden)} LÁMINAS"
    for lamina in orden:
        payload = laminas[lamina["clave"]]
        payload["_clave"] = lamina["clave"]
        payload["posicion"] = lamina["posicion"]
        if lamina["clave"] == "portada":
            payload["total_laminas"] = total
        (dir_canal / f"{lamina['stem']}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def leer_laminas(dir_canal: Path) -> list[tuple[str, dict[str, Any]]]:
    return [
        (p.stem, json.loads(p.read_text(encoding="utf-8")))
        for p in sorted(dir_canal.glob("*.json"))
        if p.stem[:1].isdigit()
    ]


# ---------------------------------------------------------------- frenos

_CAMPOS_TEXTO = ("kicker", "titular", "parrafo", "pie")
_CAMPOS_ITEM = ("texto", "titulo_punto")
_LISTAS_TEXTO = ("claves", "puntos")


def textos_de(laminas: list[tuple[str, dict[str, Any]]]) -> list[tuple[str, str]]:
    """Todo texto editorial de las láminas. Las citas no: salen del registro."""
    salida: list[tuple[str, str]] = []
    for stem, payload in laminas:
        for campo in _CAMPOS_TEXTO:
            if campo in payload:
                salida.append((f"{stem}.{campo}", str(payload[campo])))
        for lista in _LISTAS_TEXTO:
            for i, item in enumerate(payload.get(lista, []), 1):
                for campo in _CAMPOS_ITEM:
                    if campo in item:
                        salida.append((f"{stem}.{lista}[{i}].{campo}", str(item[campo])))
    return salida


def _resetear_textos(payload: dict[str, Any]) -> None:
    """Vuelve `[[ESCRIBIR]]` todo campo que `textos_de` reporta de esta lámina.

    Misma recorrida que `textos_de` (los mismos `_CAMPOS_TEXTO`/`_CAMPOS_ITEM`/
    `_LISTAS_TEXTO`): antes solo se reseteaban los campos de nivel de lámina y
    `claves[*].texto`/`puntos[*].texto`/`titulo_punto` quedaban con el texto
    escrito para la dirección que el mercado ya invalidó.
    """
    for campo in _CAMPOS_TEXTO:
        if campo in payload:
            payload[campo] = MARCA
    for lista in _LISTAS_TEXTO:
        for item in payload.get(lista, []):
            for campo in _CAMPOS_ITEM:
                if campo in item:
                    item[campo] = MARCA


# Los cierres de alerta sin el del analista (director, 2026-09-29): en la
# portada de Avisos se lee como plantilla de soporte, "ordinario".
CIERRES_AVISOS: tuple[str, ...] = tuple(c for c in pc.CIERRES_ALERTA if "analista" not in c)


def mensaje_de(payload: dict[str, Any], meta: dict[str, Any]) -> str:
    """El texto de la lámina. La portada lleva el pie completo; las demás, su posición.

    El cierre lo agrega el script, estable por tanda: el despacho vuelve a rendir
    y un texto distinto al aprobado no puede salir. El aviso legal NO va en el pie
    de la portada: la última lámina ya lo lleva impreso, y repetirlo en el mismo
    carrusel es ruido (director, 2026-10-02).
    """
    if meta.get("formato") == "resultado":
        return mensaje_resultado(payload, meta)
    if meta.get("formato") in FORMATOS_PIE_LIBRE:
        return str(payload["pie"]).strip()
    if payload.get("_clave") != "portada":
        return payload["posicion"]
    cierres = {"agenda": CIERRES_AGENDA, "agenda_dia": CIERRES_DIA}.get(meta.get("formato"), CIERRES_AVISOS)
    cierre = pc.elegir_variante(cierres, meta.get("activo") or "agenda", meta["momento"], meta["fecha"])
    return "\n\n".join([str(payload["pie"]).strip(), cierre, payload["posicion"]])


def validar_tanda(dir_canal: Path, ahora: datetime, visiones: dict[str, dict[str, Any]],
                  activos_extra: dict[str, dict[str, Any]] | None = None) -> list[str]:
    """Todos los motivos por los que el carrusel no puede rendirse. Vacío = puede."""
    meta = leer_meta(dir_canal)
    laminas = leer_laminas(dir_canal)
    textos = textos_de(laminas)
    errores = pl.validar_textos(textos)

    if len(laminas) > MAX_LAMINAS:
        errores.append(f"{len(laminas)} láminas: máximo {MAX_LAMINAS}")
    if meta.get("_falta_vision") and "voz" in SECUENCIAS[meta["formato"]] and len(SECUENCIAS[meta["formato"]]) == 1:
        errores.append("falta la voz: el balance es solo la cita. Corre --completar-vision.")

    usadas: list[dict[str, Any]] = []
    vid = meta.get("vision")
    if vid:
        if vid not in visiones:
            errores.append(f"visión `{vid}`: no está en el registro {pl.REGISTRO_VISIONES.name}")
        else:
            usadas.append(visiones[vid])
            errores.extend(pl.validar_vision(visiones[vid], ahora.date(), meta.get("aceptar_antiguas", {}).get(vid)))

    activos = dict(meta.get("activos", {}))
    for ticker, fila in (activos_extra or {}).items():
        activos[f"{ticker}#preparacion"] = fila
    errores.extend(pl.validar_cifras(textos, activos, usadas, meta.get("cifras_citadas", {}), campos=CAMPOS_AVISOS))
    errores.extend(precio_actual_citado(textos, meta))

    leido = datetime.fromisoformat(meta["leido_en"])
    errores.extend(pl.validar_frescura(leido, ahora, FRESCURA_MAX_HORAS, remedio="Corre --refrescar."))

    # El balance no cita niveles: su pie no tiene que nombrar la dirección.
    if (meta["formato"] not in FORMATOS_SIN_ACTIVO | FORMATOS_PIE_LIBRE
            and meta.get("direccion")):
        pie = next((str(p.get("pie", "")) for _, p in laminas if p.get("_clave") == "portada"), "")
        if MARCA not in pie and meta["direccion"].lower() not in pie.lower():
            errores.append(
                f"1_portada.pie: no nombra la dirección ({meta['direccion'].lower()}). "
                "El cliente tiene que saber hacia dónde va el activo."
            )
    return errores


def precio_actual_citado(textos: list[tuple[str, str]], meta: dict[str, Any]) -> list[str]:
    """Texto editorial que escribe el precio actual del activo.

    El despacho vuelve a leer el terminal y solo acepta los niveles de la
    preparación, no su precio: un texto con el spot pasa acá y se frena al
    primer tick. La cifra se reconoce igual que en `pl.validar_cifras`
    (formateada con los `digits` del activo, con o sin `$`). Un precio que
    coincide con un nivel publicado no se rechaza: ese número es el nivel.
    """
    precios: set[str] = set()
    niveles: set[str] = set()
    for filas in (meta.get("activos", {}), meta.get("activos_preparacion", {})):
        for fila in filas.values():
            if fila.get("price") is not None:
                precios.add(_fmt(fila["price"], fila["digits"]))
            niveles.update(_fmt(fila[c], fila["digits"]) for c in CAMPOS_AVISOS
                           if c != "price" and fila.get(c) is not None)
    precios -= niveles
    errores: list[str] = []
    for donde, texto in textos:
        for cifra in dict.fromkeys(pl._NUMERO.findall(texto)):
            if cifra in precios:
                errores.append(
                    f"{donde}: {cifra} es el precio actual. Ya va en la portada y en la lámina de datos, "
                    "y escribirlo hace que el despacho frene al primer movimiento del mercado. "
                    "Cita el soporte o la resistencia."
                )
    return errores


# ---------------------------------------------------------------- render


def tokens_de(payload: dict[str, Any]) -> dict[str, Any]:
    """Del contrato del despacho (`titular`, `parrafo`) a los tokens de cada plantilla."""
    tokens = {k: v for k, v in payload.items() if not k.startswith("_")}
    tokens.pop("pie", None)
    plantilla = payload["_plantilla"]
    if plantilla == "avisos_portada":
        tokens["bajada"] = tokens.pop("parrafo")
    elif plantilla == "vision":
        tokens["remate"] = tokens.pop("parrafo")
    elif plantilla == "avisos_lectura":
        tokens["titulo"] = tokens.pop("titular")
        tokens["conclusion"] = tokens.pop("parrafo")
    elif plantilla == "avisos_agenda":
        tokens["titulo"] = tokens.pop("titular")
        tokens["subtitulo"] = tokens.pop("parrafo")
    elif plantilla == "avisos_resultado":
        # El párrafo es el "qué significa" del pie; en la imagen va el movimiento.
        tokens["titulo"] = tokens.pop("titular")
        tokens["subtitulo"] = tokens.pop("movimiento")
        tokens.pop("parrafo", None)
    elif plantilla == "avisos_datos":
        from story_grafico import enriquecer

        tokens = enriquecer(tokens)
    return tokens


# El hueco del gráfico en `alerta.html` mide ~810x870. A ese ancho el encabezado
# del motor se corta; se rinde a 1100 con la misma proporción y la plantilla lo
# escala con object-fit: contain (medido el 2026-09-29: 810 corta, 1400 queda chico).
GRAFICO_TV_ANCHO, GRAFICO_TV_ALTO = 1100, 1180


def grafico_tradingview(payload: dict[str, Any], destino: Path) -> Path:
    """El gráfico de velas del motor TradingView, con los niveles que cita la lámina."""
    from tradingview_grafico import generar_grafico_tv

    crudos = payload["_procedencia"]["crudos"]
    return generar_grafico_tv(
        ticker=payload["_procedencia"]["ticker"],
        nombre=payload.get("rotulo_activo", payload.get("activo", "")),
        destino=destino,
        timeframe=pc.TIMEFRAME_GRAFICO,
        n_velas=60,
        soporte=crudos.get("soporte"),
        resistencia=crudos.get("resistencia"),
        ancho=GRAFICO_TV_ANCHO,
        alto=GRAFICO_TV_ALTO,
    )


def _con_grafico_tv(payload: dict[str, Any], dir_canal: Path, stem: str,
                    grafico: Callable[[dict[str, Any], Path], Path]) -> dict[str, Any]:
    """La lámina de datos con el PNG de TradingView embebido, o la geometría SVG si falla.

    Es el estándar de gráficos de alerta del proyecto; el SVG queda solo como
    respaldo cuando no hay MT5 o Chromium, y el respaldo se dice en voz alta.
    """
    try:
        png = grafico(payload, dir_canal / f"{stem}_grafico.png")
    except Exception as exc:  # noqa: BLE001
        print(f"AVISO: el gráfico TradingView de {stem} no se generó ({exc}); sale el SVG de respaldo.",
              file=sys.stderr)
        return payload
    return {**payload, "chart_png": str(png),
            "rotulo_grafico": f"{payload['_procedencia']['ticker'].upper()} · VELAS {pc.TIMEFRAME_GRAFICO} · ÚLTIMAS 60"}


def rendir_tanda(dir_canal: Path, ahora: datetime | None = None,
                 visiones: dict[str, dict[str, Any]] | None = None,
                 render: Callable[..., Path] | None = None,
                 activos_extra: dict[str, dict[str, Any]] | None = None,
                 grafico: Callable[[dict[str, Any], Path], Path] | None = None) -> list[Path]:
    ahora = ahora or datetime.now(SANTIAGO)
    visiones = visiones if visiones is not None else pl.cargar_visiones()
    errores = validar_tanda(dir_canal, ahora, visiones, activos_extra=activos_extra)
    if errores:
        raise SystemExit("El carrusel no se rinde:\n  " + "\n  ".join(errores))
    laminas = leer_laminas(dir_canal)
    # El mismo freno de las dos rutas de render del carrusel (su test de contrato).
    pc.exigir_texto_editorial(laminas)
    if render is None:
        from story_render import render_story as render
    meta = leer_meta(dir_canal)
    salidas: list[Path] = []
    for stem, payload in laminas:
        png = dir_canal / f"{stem}.png"
        if payload["_plantilla"] == "avisos_datos":
            payload = _con_grafico_tv(payload, dir_canal, stem, grafico or grafico_tradingview)
        render(tokens_de(payload), DIR_PLANTILLAS / PLANTILLAS[payload["_plantilla"]], png, formato="horizontal")
        (dir_canal / f"{stem}_mensaje.txt").write_text(mensaje_de(payload, meta), encoding="utf-8")
        salidas.append(png)
    return salidas


# ---------------------------------------------------------------- terminal


class LecturaFallidaError(RuntimeError):
    """El terminal no entregó el activo: falla de datos, el momento queda pendiente."""


def leer_terminal(ticker: str, ahora: datetime) -> dict[str, Any]:
    """Una lectura del activo, con la misma vara que el escáner (cobertura fija)."""
    import screener_gi as sc
    from market_data_mcp import mt5_client
    from market_data_mcp.analisis import analizar_activo

    try:
        mt5_client.connect()
    except Exception as exc:  # noqa: BLE001
        raise LecturaFallidaError(f"MT5 no conectó ({exc.__class__.__name__})") from exc
    catalogo = pl._catalogo()
    if ticker not in catalogo:
        raise LecturaFallidaError(f"{ticker} no está en el catálogo")
    activo = catalogo[ticker]
    sel = sc.evaluar_activo(activo, [], None, ahora, fijo=True, ignorar_agotamiento=True)
    if "excluido" in sel:
        raise LecturaFallidaError(f"{ticker}: {sel['excluido']}")
    h1 = analizar_activo(ticker, "H1")
    if "error" in h1:
        raise LecturaFallidaError(f"{ticker}: {h1['error']}")
    try:
        cierres = pc._serie_para(ticker)
    except Exception as exc:  # noqa: BLE001
        raise LecturaFallidaError(f"{ticker}: sin serie ({exc})") from exc
    return {"ticker": ticker, "activo": activo, "seleccion": sel, "h1": h1, "cierres": cierres}


def _leer_agenda(ahora: datetime) -> tuple[list[dict[str, Any]], list[str]]:
    return pl.leer_agenda(ahora)


# ---------------------------------------------------------------- preparar


def _tanda_existente(dir_base: Path, fecha: date, momento: str) -> Path | None:
    for d in sorted(dir_base.glob(f"{fecha.isoformat()}_*_avisos_{momento}")):
        canal = d / CANAL
        if (canal / "_avisos.json").exists():
            return canal
    return None


_Lector = Callable[[datetime], tuple[list[dict[str, Any]], list[str]]]


def _jornada_o_falla(lector_jornada: _Lector, ahora: datetime) -> list[dict[str, Any]]:
    jornada, avisos = lector_jornada(ahora)
    if avisos and not jornada:
        raise LecturaFallidaError("; ".join(avisos))
    return jornada


def _clave_resultado(momento: str, hora: str) -> str:
    return f"{momento}_{hora.replace(':', '')}"


def _preparar_resultado(momento: str, ahora: datetime, dir_base: Path, lector_jornada: _Lector,
                        lector_movimiento: Callable[[str, datetime, datetime], dict[str, Any]]) -> Path:
    """Una tanda por hora de datos: la misma hora es una sola pieza (spec §13.4)."""
    hoy = ahora.date()
    jornada = _jornada_o_falla(lector_jornada, ahora)
    grupo = resultado_pendiente(
        jornada, ahora,
        ya_hecho=lambda hora: _tanda_existente(dir_base, hoy, _clave_resultado(momento, hora)) is not None,
    )
    if grupo is None:
        raise HoyNoCorresponde("no hay resultados de datos pendientes de publicar.")
    desde = _cuando(grupo[0])
    movimientos = {t: lector_movimiento(t, desde, ahora) for t in monedas_de(grupo)}
    meta, laminas = armar_tanda(momento, "resultado", ahora, None, None, grupo,
                                extra={"movimientos": movimientos})
    etiqueta = _clave_resultado(momento, grupo[0]["hora"])
    dir_canal = dir_base / f"{ahora:%Y-%m-%d_%H-%M}_avisos_{etiqueta}" / CANAL
    dir_canal.mkdir(parents=True, exist_ok=True)
    escribir_laminas(dir_canal, "resultado", laminas)
    escribir_meta(dir_canal, meta)
    return dir_canal


def preparar(momento: str, ahora: datetime | None = None, *,
             lector: Callable[[str, datetime], dict[str, Any]] | None = None,
             lector_agenda: _Lector | None = None,
             lector_jornada: _Lector | None = None,
             lector_movimiento: Callable[[str, datetime, datetime], dict[str, Any]] | None = None,
             efecto_de: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None,
             visiones: dict[str, dict[str, Any]] | None = None,
             historial_ruta: Path | None = None, dir_base: Path | None = None,
             activo_pedido: str | None = None, vision_pedida: str | None = None) -> Path | None:
    """La tanda del momento, o `None` si hoy no es día hábil.

    `activo_pedido` y `vision_pedida` fijan a mano el activo y la voz de un
    carrusel con activo (cita o balance), en vez de dejarlos al selector.

    Una segunda corrida del mismo momento el mismo día devuelve la tanda que ya
    existe sin escribir nada: volver a elegir quemaría otra visión. El resultado
    es la excepción: sale una tanda por cada hora de datos de la jornada.

    Lanza `HoyNoCorresponde` (código 0) cuando el momento no produce nada hoy:
    la cita de la mañana en un día con datos fuertes, o un resultado sin datos
    pendientes.
    """
    ahora = (ahora or datetime.now(SANTIAGO)).astimezone(SANTIAGO)
    hoy = ahora.date()
    formato = formato_del_momento(momento, hoy)
    if not es_dia_habil(hoy):
        return None
    dir_base = dir_base or pc.DIR_TRABAJO
    lector_jornada = lector_jornada or leer_jornada
    if formato == "resultado":
        return _preparar_resultado(momento, ahora, dir_base, lector_jornada,
                                   lector_movimiento or leer_movimiento)
    existente = _tanda_existente(dir_base, hoy, momento)
    if existente is not None:
        return existente

    lector = lector or leer_terminal
    visiones = visiones if visiones is not None else pl.cargar_visiones()
    historial = cargar_historial(historial_ruta)

    lectura: dict[str, Any] | None = None
    vision: dict[str, Any] | None = None
    agenda: list[dict[str, Any]] = []
    gastar_vision = True

    if formato == "agenda_dia":
        # Solo lo que falta por salir: la agenda mira hacia adelante. Sin datos
        # fuertes en la jornada, Avisos recibe lo que queda de la semana.
        agenda = [ev for ev in _jornada_o_falla(lector_jornada, ahora) if _cuando(ev) >= ahora]
        if not agenda:
            formato = "agenda"
    elif momento == "avisos_manana":
        # La cita de un banco solo los días sin datos fuertes (spec §13.2). Si el
        # calendario no responde se prepara igual: la cita no depende de él.
        jornada, _ = lector_jornada(ahora)
        if jornada:
            raise HoyNoCorresponde(
                "hoy hay datos de alto impacto: Avisos lleva la agenda del día y sus "
                "resultados, no la cita de la mañana."
            )
    elif formato == "agenda" and momento == "avisos_tarde":
        # El lunes la tarde muestra la semana, salvo que ya haya salido en la
        # mañana por falta de datos del día: entonces toca el balance.
        manana = _tanda_existente(dir_base, hoy, "avisos_agenda")
        if manana is not None and leer_meta(manana).get("formato") == "agenda":
            formato = "balance"

    if formato == "agenda_dia":
        activo = None
    elif formato == "agenda":
        agenda, avisos = (lector_agenda or _leer_agenda)(ahora)
        if avisos and not agenda:
            raise LecturaFallidaError("; ".join(avisos))
        activo = None
    else:
        if activo_pedido:
            # El director elige el activo y la voz: pasa el día en que no hubo
            # cita en la mañana y el respaldo del balance saldría sin voz.
            activo, vid = activo_pedido, vision_pedida
            if vid:
                errores = _errores_vision_pedida(visiones.get(vid), vid, activo, hoy, historial)
                if errores:
                    raise VisionPedidaError(errores)
        elif formato == "balance":
            activo, vid = activo_del_balance(historial, hoy)
            gastar_vision = False
            if activo is None:
                activo, vid = elegir("cita", hoy, {}, historial)
        else:
            activo, vid = elegir(formato, hoy, visiones, historial)
        vision = visiones.get(vid) if vid else None
        lectura = lector(activo, ahora)

    meta, laminas = armar_tanda(momento, formato, ahora, lectura, vision, agenda,
                                extra={"efecto_de": efecto_de})
    dir_canal = dir_base / f"{ahora:%Y-%m-%d_%H-%M}_avisos_{momento}" / CANAL
    dir_canal.mkdir(parents=True, exist_ok=True)
    # Las láminas primero: `_avisos.json` es la marca de que la tanda quedó
    # completa, y `_tanda_existente` solo la mira a ella. Escribirla antes
    # dejaría una carpeta que parece preparada con las láminas todavía sin
    # escribir si el proceso se corta entre medio.
    escribir_laminas(dir_canal, formato, laminas)
    escribir_meta(dir_canal, meta)
    registrar_uso(hoy, momento, activo, meta["vision"], gastar_vision=gastar_vision, ruta=historial_ruta)
    return dir_canal


# ---------------------------------------------------------------- refrescar


def refrescar_portada(payload: dict[str, Any], lectura: dict[str, Any], ahora: datetime) -> tuple[dict[str, Any], str | None]:
    nuevo = json.loads(json.dumps(payload))
    precio = _fmt(lectura["h1"]["price"], lectura["activo"]["digits"])
    nuevo["dato_precio"] = f"{lectura['activo']['nombre']} {precio}"
    nuevo["dato_hora"] = f"LEÍDO {etiqueta_hora(ahora)}"
    nuevo["fecha_hora"] = fecha_hora(ahora)
    return nuevo, None


def refrescar_voz(payload: dict[str, Any], lectura: dict[str, Any], ahora: datetime) -> tuple[dict[str, Any], str | None]:
    nuevo = json.loads(json.dumps(payload))
    for bloque in nuevo.get("bloque_meta", []):
        bloque["precio_hoy"] = _fmt(lectura["h1"]["price"], lectura["activo"]["digits"])
        bloque["hora_precio"] = etiqueta_hora(ahora)
    nuevo["fecha_hora"] = fecha_hora(ahora)
    return nuevo, None


def refrescar_datos(payload: dict[str, Any], lectura: dict[str, Any], ahora: datetime) -> tuple[dict[str, Any], str | None]:
    return pc.refrescar_payload(payload, ahora=ahora, h1=lectura["h1"],
                                digits=lectura["activo"]["digits"], cierres=lectura["cierres"])


# Toda `_plantilla` que este script escribe tiene entrada. `None` es una
# decisión explícita (la lámina no lleva precio), no una ausencia: así ninguna
# lámina cae en el camino "se despacha tal cual" sin que alguien lo haya decidido.
REFRESCOS: dict[str, Callable[[dict[str, Any], dict[str, Any], datetime], tuple[dict[str, Any], str | None]] | None] = {
    "avisos_portada": refrescar_portada,
    "vision": refrescar_voz,
    "avisos_datos": refrescar_datos,
    "avisos_agenda": None,
    "avisos_lectura": None,
    # El resultado sí lleva precio, pero se refresca por tanda y no por lámina:
    # sus cifras son el movimiento de la moneda desde la hora del dato, que vive
    # en el meta (`refrescar_resultado`).
    "avisos_resultado": None,
}


def _aplicar_refresco(dir_canal: Path, lectura: dict[str, Any], ahora: datetime) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Las láminas refrescadas en memoria y los motivos de divergencia. No escribe."""
    nuevas: dict[str, dict[str, Any]] = {}
    motivos: list[str] = []
    for stem, payload in leer_laminas(dir_canal):
        funcion = REFRESCOS[payload["_plantilla"]]
        if funcion is None:
            continue
        nuevo, motivo = funcion(payload, lectura, ahora)
        if motivo:
            motivos.append(f"{stem}: {motivo}")
        nuevas[stem] = nuevo
    return nuevas, motivos


def _guardar_refresco(dir_canal: Path, meta: dict[str, Any], nuevas: dict[str, dict[str, Any]],
                      lectura: dict[str, Any], ahora: datetime, reescribir: bool = False) -> None:
    for stem, payload in nuevas.items():
        (dir_canal / f"{stem}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    datos = next((p for p in nuevas.values() if p["_plantilla"] == "avisos_datos"), None)
    meta["activos"] = {lectura["ticker"]: fila_medida(lectura, datos)}
    meta["leido_en"] = ahora.isoformat(timespec="minutes")
    if datos is not None:
        meta["direccion"] = datos.get("sesgo", meta.get("direccion"))
    if reescribir:
        # Los textos vuelven a escribirse contra esta lectura: la de
        # preparación, la que el despacho acepta como citable, pasa a ser esta.
        meta["activos_preparacion"] = copy.deepcopy(meta["activos"])
    escribir_meta(dir_canal, meta)


def refrescar_resultado(dir_canal: Path, ahora: datetime,
                        lector_movimiento: Callable[[str, datetime, datetime], dict[str, Any]] | None = None,
                        reescribir: bool = False) -> list[str]:
    """Vuelve a medir las monedas desde la hora del dato.

    El texto ("qué significa") se escribió para el movimiento de la preparación:
    si una moneda dio vuelta desde entonces, el texto quedó escrito para otro
    mercado y la pieza no sale sin reescribirlo.
    """
    meta = leer_meta(dir_canal)
    medir = lector_movimiento or leer_movimiento
    desde = datetime.strptime(f"{meta['fecha']} {meta['hora_dato']}", "%Y-%m-%d %H:%M").replace(tzinfo=SANTIAGO)
    nuevos = {t: medir(t, desde, ahora) for t in meta["movimientos"]}
    motivos = []
    for t, m in nuevos.items():
        antes = meta.get("movimientos_preparacion", {}).get(t)
        if not antes:
            continue
        # Dar vuelta es pasar de subir a ceder, o al revés, fuera de la banda de
        # ruido. Salir de "se mantiene" o volver a él no invalida el texto: el
        # movimiento nunca tuvo dirección que contradecir.
        previo, actual = _verbo(antes), _verbo(m)
        if {previo, actual} == {"sube", "cede"}:
            motivos.append(
                f"{ROTULOS_MONEDA.get(t, (t, t))[1]} dio vuelta: el texto se escribió cuando "
                f"{previo} y ahora {actual}"
            )
    if motivos and not reescribir:
        raise SystemExit(
            "El mercado invalidó el texto:\n  " + "\n  ".join(motivos)
            + "\nCorre --refrescar con --reescribir y vuelve a escribir el párrafo."
        )
    for stem, payload in leer_laminas(dir_canal):
        payload["movimiento"] = frase_movimiento(nuevos, meta["hora_dato"])
        payload["fecha_hora"] = fecha_hora(ahora)
        if motivos:
            payload["parrafo"] = MARCA
        (dir_canal / f"{stem}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    meta["movimientos"] = nuevos
    meta["leido_en"] = ahora.isoformat(timespec="minutes")
    if motivos:
        meta["movimientos_preparacion"] = copy.deepcopy(nuevos)
    escribir_meta(dir_canal, meta)
    if motivos:
        return motivos + ["párrafo vuelto a [[ESCRIBIR]]"]
    return [f"refrescado a las {etiqueta_hora(ahora)}"]


def refrescar_tanda(dir_canal: Path, ahora: datetime | None = None,
                    lector: Callable[[str, datetime], dict[str, Any]] | None = None,
                    reescribir: bool = False,
                    lector_movimiento: Callable[[str, datetime, datetime], dict[str, Any]] | None = None) -> list[str]:
    """Relee el terminal para el mismo activo. Conserva la visión y todo el texto.

    Si el precio cruzó un nivel o la lectura dio vuelta, el texto quedó escrito
    para otro mercado: sin `reescribir` no se toca nada; con `reescribir` se
    guardan los datos nuevos y los textos vuelven a `[[ESCRIBIR]]`.
    """
    ahora = (ahora or datetime.now(SANTIAGO)).astimezone(SANTIAGO)
    meta = leer_meta(dir_canal)
    if meta.get("formato") == "resultado":
        return refrescar_resultado(dir_canal, ahora, lector_movimiento, reescribir)
    if not meta.get("activo"):
        meta["leido_en"] = ahora.isoformat(timespec="minutes")
        escribir_meta(dir_canal, meta)
        return ["agenda: sin precio que refrescar, se renovó la hora de lectura"]
    lectura = (lector or leer_terminal)(meta["activo"], ahora)
    nuevas, motivos = _aplicar_refresco(dir_canal, lectura, ahora)
    if motivos and not reescribir:
        raise SystemExit(
            "El mercado invalidó el texto:\n  " + "\n  ".join(motivos)
            + "\nCorre --refrescar con --reescribir y vuelve a escribir las láminas."
        )
    _guardar_refresco(dir_canal, meta, nuevas, lectura, ahora, reescribir=bool(motivos))
    if motivos:
        for stem, payload in leer_laminas(dir_canal):
            _resetear_textos(payload)
            (dir_canal / f"{stem}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return motivos + ["textos vueltos a [[ESCRIBIR]]"]
    return [f"refrescado a las {etiqueta_hora(ahora)}"]


# ---------------------------------------------------------------- completar visión


def completar_vision(dir_canal: Path, vid: str, ahora: datetime | None = None,
                     visiones: dict[str, dict[str, Any]] | None = None,
                     historial_ruta: Path | None = None) -> None:
    """Arma la lámina de la voz en una tanda que salió sin visión. No cambia el activo."""
    ahora = (ahora or datetime.now(SANTIAGO)).astimezone(SANTIAGO)
    meta = leer_meta(dir_canal)
    if not meta.get("_falta_vision"):
        raise SystemExit("La tanda ya tiene visión o no la necesita (agenda).")
    visiones = visiones if visiones is not None else pl.cargar_visiones()
    vision = visiones.get(vid)
    if vision is None:
        raise SystemExit(f"`{vid}` no está en el registro {pl.REGISTRO_VISIONES.name}.")
    if vision.get("activo") != meta["activo"]:
        raise SystemExit(f"La visión `{vid}` es de {vision.get('activo')} y el activo de la tanda es {meta['activo']}.")
    variante = meta["formato"] if meta["formato"] in ("cita", "meta") else variante_de(vision)
    if not vision_califica(vision, variante, ahora.date(), cargar_historial(historial_ruta)):
        raise SystemExit(
            f"La visión `{vid}` no sirve para la variante {variante}: revisa fecha (máximo "
            f"{pl.ANTIGUEDAD_MAX_DIAS} días), uso en Avisos (14 días) y, si es meta, `meta` y `horizonte`."
        )
    laminas = {p["_clave"]: p for _, p in leer_laminas(dir_canal)}
    fila = meta["activos"][meta["activo"]]
    leido = datetime.fromisoformat(meta["leido_en"])
    laminas["voz"] = lamina_voz(vision, variante, fila, leido, ahora,
                                con_pie=meta["formato"] in FORMATOS_PIE_LIBRE)
    ordenadas = {c: laminas[c] for c in SECUENCIAS[meta["formato"]] if c in laminas}
    escribir_laminas(dir_canal, meta["formato"], ordenadas)
    meta.update(vision=vid, vision_variante=variante, _falta_vision=False)
    escribir_meta(dir_canal, meta)
    registrar_vision_completada(date.fromisoformat(meta["fecha"]), meta["momento"], meta["activo"], vid,
                                ruta=historial_ruta)


# ---------------------------------------------------------------- CLI


_SIN_ACTIVO = {"agenda": "agenda de la semana", "agenda_dia": "agenda del día", "resultado": "resultado de los datos"}


def _mensaje_preparar(ruta: Path, meta: dict[str, Any], ya_existia: bool) -> list[str]:
    """Las líneas que informan si la tanda es nueva o si ya estaba preparada."""
    if ya_existia:
        return [f"La tanda de este momento ya estaba preparada: {ruta.parent}"]
    lineas = [f"Tanda: {ruta.parent}",
              f"Activo: {meta['activo'] or _SIN_ACTIVO.get(meta['formato'], meta['formato'])} · formato {meta['formato']}"]
    if meta["_falta_vision"]:
        lineas.append("_falta_vision: el comando busca una visión y corre --completar-vision.")
    return lineas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Carruseles de Avisos: la voz de los bancos contra nuestros datos")
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument("--preparar", action="store_true", help="prepara la tanda del momento (--momento)")
    modo.add_argument("--refrescar", type=Path, metavar="DIR", help="relee el terminal y conserva el texto")
    modo.add_argument("--rendir", type=Path, metavar="DIR", help="aplica los frenos y rinde las láminas")
    modo.add_argument("--validar", type=Path, metavar="DIR", help="informa qué falta, sin escribir")
    modo.add_argument("--completar-vision", nargs=2, metavar=("DIR", "ID"), help="arma la voz con una visión nueva")
    parser.add_argument("--momento", choices=sorted(MOMENTOS))
    parser.add_argument("--reescribir", action="store_true", help="con --refrescar: acepta la divergencia y vacía los textos")
    parser.add_argument("--activo", help="con --preparar: el activo del carrusel (cita o balance), elegido por el director")
    parser.add_argument("--vision", help="con --preparar y --activo: el id de la visión que da la voz")
    args = parser.parse_args(argv)

    if args.preparar:
        if not args.momento:
            print("ERROR: --preparar necesita --momento", file=sys.stderr)
            return 2
        ahora = datetime.now(SANTIAGO)
        # Se mira ANTES de preparar: `preparar` devuelve la misma ruta para una
        # tanda nueva y para una ya existente, y el director necesita saber
        # cuál de las dos pasó (issue de la revisión: dos `--preparar` del
        # mismo momento el mismo día).
        ya_existia = es_dia_habil(ahora.date()) and _tanda_existente(pc.DIR_TRABAJO, ahora.date(), args.momento) is not None
        if args.vision and not args.activo:
            print("ERROR: --vision necesita --activo", file=sys.stderr)
            return 2
        try:
            ruta = preparar(args.momento, ahora, activo_pedido=args.activo, vision_pedida=args.vision)
        except VisionPedidaError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        except LecturaFallidaError as exc:
            print(f"FALLA DE DATOS: {exc}. El momento queda pendiente.", file=sys.stderr)
            return 1
        except (SinCandidatosError, HoyNoCorresponde) as exc:
            print(f"Sin tanda: {exc} Es un resultado válido, no una falla.")
            return 0
        if ruta is None:
            print("Hoy no corresponde: no es día hábil en la bolsa de Nueva York.")
            return 0
        meta = leer_meta(ruta)
        for linea in _mensaje_preparar(ruta, meta, ya_existia):
            print(linea)
        return 0
    if args.refrescar:
        try:
            for linea in refrescar_tanda(args.refrescar, reescribir=args.reescribir):
                print(linea)
        except LecturaFallidaError as exc:
            print(f"FALLA DE DATOS: {exc}", file=sys.stderr)
            return 1
        return 0
    if args.rendir:
        for png in rendir_tanda(args.rendir):
            print(png)
        return 0
    if args.validar:
        errores = validar_tanda(args.validar, datetime.now(SANTIAGO), pl.cargar_visiones())
        print("Lista para rendir." if not errores else "\n".join(errores))
        return 0 if not errores else 1
    directorio, vid = args.completar_vision
    completar_vision(Path(directorio), vid)
    print(f"Voz armada con `{vid}`. Escribe su titular y su párrafo y corre --rendir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
