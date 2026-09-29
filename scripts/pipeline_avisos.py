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
import json
import sys
from datetime import date, datetime, timedelta
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
MOMENTOS = {"avisos_manana": "cita", "avisos_mediodia": "meta", "avisos_tarde": "tarde"}

# clave -> (_plantilla, nombre que ve el cliente en el pie de posición)
LAMINAS = {
    "portada": ("avisos_portada", "Portada"),
    "voz": ("vision", "La voz del banco"),
    "datos": ("avisos_datos", "Nuestros datos"),
    "semana": ("avisos_agenda", "La semana"),
    "lectura": ("avisos_lectura", "Nuestra lectura"),
}

SECUENCIAS = {
    "cita": ("portada", "voz", "datos", "lectura"),
    "meta": ("portada", "voz", "datos", "lectura"),
    "balance": ("portada", "voz", "datos", "lectura"),
    "agenda": ("portada", "semana", "lectura"),
}

# _plantilla -> archivo en templates/stories/. La lámina de datos se llama
# `avisos_datos` y no `alerta`: el refresco temático reescribe el mensaje con
# `construir_mensaje_alerta` y borraría el pie de posición.
PLANTILLAS = {
    "avisos_portada": "avisos_portada.html",
    "vision": "vision.html",
    "avisos_datos": "alerta.html",
    "avisos_agenda": "calendario.html",
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


def formato_del_momento(momento: str, fecha: date) -> str:
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
    return [
        {
            "clave": c,
            "stem": f"{i}_{c}",
            "plantilla": LAMINAS[c][0],
            "posicion": f"{i}/{total} · {LAMINAS[c][1]}",
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
    mejor: dict[str, dict[str, Any]] = {}
    for v in visiones.values():
        t = v.get("activo")
        if t in cands and vision_califica(v, variante, hoy, historial):
            actual = mejor.get(t)
            if actual is None or (v["fecha"], v["id"]) > (actual["fecha"], actual["id"]):
                mejor[t] = v

    def orden(t: str) -> tuple[int, str]:
        return (cobertura.get(t, 0), t)

    if mejor:
        t = min(mejor, key=orden)
        return t, mejor[t]["id"]
    return min(cands, key=orden), None


def activo_del_balance(historial: list[dict[str, Any]], hoy: date) -> tuple[str | None, str | None]:
    """El activo y la visión de la mañana; si no hubo, los del mediodía."""
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


# ---------------------------------------------------------------- láminas

CAMPOS_AVISOS = pl.CAMPOS_PRECIO + ("soporte_publicado", "resistencia_publicada")

_PAISES = {"United States": "EE.UU.", "Chile": "Chile", "China": "China",
           "Euro Zone": "Zona Euro", "Euro Area": "Zona Euro", "Zona Euro": "Zona Euro"}
_ETIQUETA_TIPO = {"textual": "", "traduccion": "Traducción nuestra", "parafrasis": "En palabras nuestras"}
CTA_AGENDA = ("¿Quieres seguir esta semana en detalle?", "Habla hoy con tu analista")


def _fmt(valor: float, digits: int) -> str:
    return pc.formatear_precio(float(valor), digits)


def _fecha_corta(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} {_MESES[d.month - 1]} {d.year}"


def fila_medida(lectura: dict[str, Any], payload_datos: dict[str, Any]) -> dict[str, Any]:
    """Lo que el texto puede citar: los niveles del terminal y los publicados en la alerta.

    La alerta acota sus niveles (`acotar_niveles_intradia`), así que el soporte
    que ve el cliente puede no ser el `s1` crudo: los dos cuentan como medidos.
    """
    niveles = {n["rol"]: n["precio"] for n in payload_datos["recorrido"]["niveles"]}
    fila: dict[str, Any] = {"nombre": lectura["activo"]["nombre"], "digits": lectura["activo"]["digits"]}
    fila.update({c: lectura["h1"].get(c) for c in pl.CAMPOS_PRECIO})
    fila["soporte_publicado"] = niveles.get("SOPORTE")
    fila["resistencia_publicada"] = niveles.get("RESISTENCIA")
    return fila


def lamina_portada(activo_nombre: str | None, precio: str, leido: datetime, ahora: datetime,
                   agenda: bool, ticker: str | None = None) -> dict[str, Any]:
    # Spec §3.7.4: toda lámina con precio lleva _procedencia.ticker; la agenda no tiene precio.
    if not agenda and not ticker:
        raise ValueError("la portada con precio exige el ticker de su procedencia")
    return {
        "_plantilla": "avisos_portada", "plantilla": "avisos_portada",
        "sello": "AVISOS · AGENDA DE LA SEMANA" if agenda else f"AVISOS · {str(activo_nombre).upper()}",
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
               ahora: datetime) -> dict[str, Any]:
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
        "sello": "AVISOS · LA VOZ DEL BANCO", "fecha_hora": fecha_hora(ahora),
        "titular": MARCA, "parrafo": MARCA,
        "bloque_cita": bloque_cita, "bloque_meta": bloque_meta, "posicion": "",
    }


def lamina_datos(lectura: dict[str, Any], ahora: datetime) -> dict[str, Any]:
    payload = pc.construir_payload(lectura["seleccion"], lectura["activo"], ahora, lectura["cierres"])
    payload.update({"_plantilla": "avisos_datos", "titular": MARCA, "parrafo": MARCA})
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


def armar_tanda(momento: str, formato: str, ahora: datetime, lectura: dict[str, Any] | None,
                vision: dict[str, Any] | None, agenda: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    agenda_semana = formato == "agenda"
    laminas: dict[str, dict[str, Any]] = {}
    activos: dict[str, dict[str, Any]] = {}
    direccion = None
    if agenda_semana:
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
            laminas["voz"] = lamina_voz(vision, variante, fila, ahora, ahora)
        laminas["datos"] = datos
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


def textos_de(laminas: list[tuple[str, dict[str, Any]]]) -> list[tuple[str, str]]:
    """Todo texto editorial de las láminas. Las citas no: salen del registro."""
    salida: list[tuple[str, str]] = []
    for stem, payload in laminas:
        for campo in _CAMPOS_TEXTO:
            if campo in payload:
                salida.append((f"{stem}.{campo}", str(payload[campo])))
        for lista in ("claves", "puntos"):
            for i, item in enumerate(payload.get(lista, []), 1):
                for campo in _CAMPOS_ITEM:
                    if campo in item:
                        salida.append((f"{stem}.{lista}[{i}].{campo}", str(item[campo])))
    return salida


def mensaje_de(payload: dict[str, Any], meta: dict[str, Any]) -> str:
    """El texto de la lámina. La portada lleva el pie completo; las demás, su posición.

    El cierre y el aviso los agrega el script, estables por tanda: el despacho
    vuelve a rendir y un texto distinto al aprobado no puede salir.
    """
    if payload.get("_clave") != "portada":
        return payload["posicion"]
    cierre = pc.elegir_variante(pc.CIERRES_ALERTA, meta.get("activo") or "agenda", meta["momento"], meta["fecha"])
    return "\n\n".join([str(payload["pie"]).strip(), cierre, AVISO_LEGAL, payload["posicion"]])


def validar_tanda(dir_canal: Path, ahora: datetime, visiones: dict[str, dict[str, Any]],
                  activos_extra: dict[str, dict[str, Any]] | None = None) -> list[str]:
    """Todos los motivos por los que el carrusel no puede rendirse. Vacío = puede."""
    meta = leer_meta(dir_canal)
    laminas = leer_laminas(dir_canal)
    textos = textos_de(laminas)
    errores = pl.validar_textos(textos)

    if len(laminas) > MAX_LAMINAS:
        errores.append(f"{len(laminas)} láminas: máximo {MAX_LAMINAS}")

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

    leido = datetime.fromisoformat(meta["leido_en"])
    errores.extend(pl.validar_frescura(leido, ahora, FRESCURA_MAX_HORAS, remedio="Corre --refrescar."))

    if meta["formato"] != "agenda" and meta.get("direccion"):
        pie = next((str(p.get("pie", "")) for _, p in laminas if p.get("_clave") == "portada"), "")
        if MARCA not in pie and meta["direccion"].lower() not in pie.lower():
            errores.append(
                f"1_portada.pie: no nombra la dirección ({meta['direccion'].lower()}). "
                "El cliente tiene que saber hacia dónde va el activo."
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
    elif plantilla == "avisos_datos":
        from story_grafico import enriquecer

        tokens = enriquecer(tokens)
    return tokens


def rendir_tanda(dir_canal: Path, ahora: datetime | None = None,
                 visiones: dict[str, dict[str, Any]] | None = None,
                 render: Callable[..., Path] | None = None,
                 activos_extra: dict[str, dict[str, Any]] | None = None) -> list[Path]:
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


def preparar(momento: str, ahora: datetime | None = None, *,
             lector: Callable[[str, datetime], dict[str, Any]] | None = None,
             lector_agenda: Callable[[datetime], tuple[list[dict[str, Any]], list[str]]] | None = None,
             visiones: dict[str, dict[str, Any]] | None = None,
             historial_ruta: Path | None = None, dir_base: Path | None = None) -> Path | None:
    """La tanda del momento, o `None` si hoy no corresponde.

    Una segunda corrida del mismo momento el mismo día devuelve la tanda que ya
    existe sin escribir nada: volver a elegir quemaría otra visión.
    """
    ahora = (ahora or datetime.now(SANTIAGO)).astimezone(SANTIAGO)
    hoy = ahora.date()
    formato = formato_del_momento(momento, hoy)
    if not es_dia_habil(hoy):
        return None
    dir_base = dir_base or pc.DIR_TRABAJO
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
    if formato == "agenda":
        agenda, avisos = (lector_agenda or _leer_agenda)(ahora)
        if avisos and not agenda:
            raise LecturaFallidaError("; ".join(avisos))
        activo = None
    else:
        if formato == "balance":
            activo, vid = activo_del_balance(historial, hoy)
            gastar_vision = False
            if activo is None:
                activo, vid = elegir("cita", hoy, {}, historial)
        else:
            activo, vid = elegir(formato, hoy, visiones, historial)
        vision = visiones.get(vid) if vid else None
        lectura = lector(activo, ahora)

    meta, laminas = armar_tanda(momento, formato, ahora, lectura, vision, agenda)
    dir_canal = dir_base / f"{ahora:%Y-%m-%d_%H-%M}_avisos_{momento}" / CANAL
    dir_canal.mkdir(parents=True, exist_ok=True)
    escribir_meta(dir_canal, meta)
    escribir_laminas(dir_canal, formato, laminas)
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
                      lectura: dict[str, Any], ahora: datetime) -> None:
    for stem, payload in nuevas.items():
        (dir_canal / f"{stem}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    datos = next(p for p in nuevas.values() if p["_plantilla"] == "avisos_datos")
    meta["activos"] = {lectura["ticker"]: fila_medida(lectura, datos)}
    meta["leido_en"] = ahora.isoformat(timespec="minutes")
    meta["direccion"] = datos.get("sesgo", meta.get("direccion"))
    escribir_meta(dir_canal, meta)


def refrescar_tanda(dir_canal: Path, ahora: datetime | None = None,
                    lector: Callable[[str, datetime], dict[str, Any]] | None = None,
                    reescribir: bool = False) -> list[str]:
    """Relee el terminal para el mismo activo. Conserva la visión y todo el texto.

    Si el precio cruzó un nivel o la lectura dio vuelta, el texto quedó escrito
    para otro mercado: sin `reescribir` no se toca nada; con `reescribir` se
    guardan los datos nuevos y los textos vuelven a `[[ESCRIBIR]]`.
    """
    ahora = (ahora or datetime.now(SANTIAGO)).astimezone(SANTIAGO)
    meta = leer_meta(dir_canal)
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
    _guardar_refresco(dir_canal, meta, nuevas, lectura, ahora)
    if motivos:
        for stem, payload in leer_laminas(dir_canal):
            for campo in _CAMPOS_TEXTO:
                if campo in payload:
                    payload[campo] = MARCA
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
    laminas["voz"] = lamina_voz(vision, variante, fila, leido, ahora)
    ordenadas = {c: laminas[c] for c in SECUENCIAS[meta["formato"]] if c in laminas}
    escribir_laminas(dir_canal, meta["formato"], ordenadas)
    meta.update(vision=vid, vision_variante=variante, _falta_vision=False)
    escribir_meta(dir_canal, meta)
    registrar_uso(ahora.date(), meta["momento"], None, vid, gastar_vision=True, ruta=historial_ruta)


# ---------------------------------------------------------------- CLI


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
    args = parser.parse_args(argv)

    if args.preparar:
        if not args.momento:
            print("ERROR: --preparar necesita --momento", file=sys.stderr)
            return 2
        try:
            ruta = preparar(args.momento)
        except LecturaFallidaError as exc:
            print(f"FALLA DE DATOS: {exc}. El momento queda pendiente.", file=sys.stderr)
            return 1
        except SinCandidatosError as exc:
            print(f"Sin tanda: {exc} Es un resultado válido, no una falla.")
            return 0
        if ruta is None:
            print("Hoy no corresponde: no es día hábil en la bolsa de Nueva York.")
            return 0
        meta = leer_meta(ruta)
        print(f"Tanda: {ruta.parent}\nActivo: {meta['activo'] or 'agenda de la semana'} · formato {meta['formato']}")
        if meta["_falta_vision"]:
            print("_falta_vision: el comando busca una visión y corre --completar-vision.")
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
