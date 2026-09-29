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
