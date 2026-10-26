# -*- coding: utf-8 -*-
"""Renderizador autónomo del lienzo interactivo para el webinar diario (Prezi-style).

Genera data/webinar/<fecha>/lienzo.html y opcionalmente lienzo.pdf, totalmente autónomo,
sin dependencias de red externas y con todas las imágenes y fuentes embebidas en base64.
"""
from __future__ import annotations

import argparse
import base64
import html
import json
import re
import sys
import zoneinfo
from datetime import date, datetime
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parents[2]
for _p in (RAIZ / "src", RAIZ / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

MOTIVOS_CATALOGO_DEFAULT = {
    "oro_lingotes",
    "banco_central",
    "billetes_dolar",
    "peso_chileno",
    "cobre",
    "petroleo",
    "bolsa_pantallas",
    "tecnologia",
    "acciones_generico",
}

POSICIONES_BLOQUES: list[dict[str, Any]] = [
    {"id": "portada", "x": 0, "y": 0, "titulo": "Portada"},
    {"id": "aviso_legal", "x": 2160, "y": 0, "titulo": "Aviso Legal"},
    {"id": "agenda", "x": 4320, "y": 0, "titulo": "Agenda Macroeconómica"},
    {"id": "noticia", "x": 6480, "y": 0, "titulo": "Premisa de la Sesión"},
    {"id": "bancos", "x": 0, "y": 1280, "titulo": "Visión de Bancos"},
    {"id": "datos", "x": 2160, "y": 1280, "titulo": "Curva y Drivers"},
    {"id": "teoria", "x": 4320, "y": 1280, "titulo": "Smart Money y Técnica"},
    {"id": "mt5", "x": 6480, "y": 1280, "titulo": "Lectura en Vivo MT5"},
    {"id": "preguntas", "x": 2160, "y": 2560, "titulo": "Preguntas de la Audiencia"},
    {"id": "cierre", "x": 4320, "y": 2560, "titulo": "Cierre y Próximos Pasos"},
]


def e(val: Any) -> str:
    """Escapa de forma segura caracteres HTML."""
    if val is None:
        return ""
    return html.escape(str(val), quote=True)


def obtener_motivos_validos(config_path: Path | None = None) -> set[str]:
    """Carga los motivos permitidos desde config/motivos_imagen.json o respaldo."""
    if config_path is None:
        config_path = RAIZ / "config" / "motivos_imagen.json"
    if config_path.exists():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            motivos = data.get("motivos", {})
            if isinstance(motivos, dict) and motivos:
                return set(motivos.keys())
        except Exception:
            pass
    return set(MOTIVOS_CATALOGO_DEFAULT)


def _buscar_guiones_largos(obj: Any, ruta: str = "") -> list[str]:
    """Detecta infracciones de la regla de estilo: CERO guiones largos (U+2014 / U+2013)."""
    errores: list[str] = []
    if isinstance(obj, str):
        if "\u2014" in obj or "\u2013" in obj:
            errores.append(
                f"Regla de estilo: el campo '{ruta}' contiene un guion largo prohibido (U+2014 o U+2013)"
            )
    elif isinstance(obj, dict):
        for k, v in obj.items():
            sub_ruta = f"{ruta}.{k}" if ruta else str(k)
            errores.extend(_buscar_guiones_largos(v, sub_ruta))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            sub_ruta = f"{ruta}[{idx}]"
            errores.extend(_buscar_guiones_largos(item, sub_ruta))
    return errores


def _es_fecha_valida(f_str: str) -> bool:
    """Verifica si la cadena tiene formato AAAA-MM-DD y corresponde a una fecha de calendario real."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", f_str):
        return False
    try:
        date.fromisoformat(f_str)
        return True
    except (ValueError, TypeError):
        return False


def validar_editorial(ed: dict, config_path: Path | None = None) -> list[str]:
    """Valida el contenido de editorial.json según especificación editorial estricta."""
    errores: list[str] = []
    if not isinstance(ed, dict):
        return ["editorial.json debe ser un objeto JSON (dict)"]

    motivos_validos = obtener_motivos_validos(config_path)

    # 1. Validación de 'noticia'
    if "noticia" not in ed or not isinstance(ed["noticia"], dict):
        errores.append("editorial: falta la sección obligatoria 'noticia'")
    else:
        noticia = ed["noticia"]
        for campo in ("titular", "bajada", "url", "fecha", "medio"):
            val = noticia.get(campo)
            if val is None or not isinstance(val, str) or not val.strip():
                errores.append(f"noticia: falta el campo obligatorio '{campo}'")

        if isinstance(noticia.get("fecha"), str):
            f_str = noticia["fecha"].strip()
            if not _es_fecha_valida(f_str):
                errores.append(f"noticia.fecha: formato inválido '{f_str}', debe ser AAAA-MM-DD")

        if isinstance(noticia.get("url"), str):
            u_str = noticia["url"].strip()
            if not (u_str.startswith("http://") or u_str.startswith("https://")):
                errores.append(f"noticia.url: la URL debe comenzar con http:// o https:// (valor: '{u_str}')")

        if not (noticia.get("activo") or noticia.get("motivo_imagen")):
            errores.append("noticia: falta 'activo' o 'motivo_imagen' para la imagen")
        if noticia.get("activo") and imagen_de_activo(str(noticia["activo"])) is None:
            errores.append(f"noticia.activo: '{noticia['activo']}' no tiene imagen en config/activos.json")
        if isinstance(noticia.get("motivo_imagen"), str):
            motivo = noticia["motivo_imagen"].strip()
            if motivo not in motivos_validos:
                errores.append(f"noticia.motivo_imagen: motivo '{motivo}' no existe en config/motivos_imagen.json")

    # 2. Validación de 'teoria'
    if "teoria" not in ed or not isinstance(ed["teoria"], dict):
        errores.append("editorial: falta la sección obligatoria 'teoria'")
    else:
        teoria = ed["teoria"]
        for campo in ("tema", "idea_central", "ejemplo"):
            val = teoria.get(campo)
            if val is None or not isinstance(val, str) or not val.strip():
                errores.append(f"teoria: falta el campo obligatorio '{campo}'")

        puntos = teoria.get("puntos")
        if not isinstance(puntos, list) or not (3 <= len(puntos) <= 5) or not all(
            isinstance(p, str) and p.strip() for p in puntos
        ):
            num = len(puntos) if isinstance(puntos, list) else 0
            errores.append(f"teoria.puntos: debe ser una lista de 3 a 5 strings no vacíos (recibidos: {num})")

        preguntas = teoria.get("preguntas_chat")
        if not isinstance(preguntas, list) or not (2 <= len(preguntas) <= 3) or not all(
            isinstance(q, str) and q.strip() for q in preguntas
        ):
            num = len(preguntas) if isinstance(preguntas, list) else 0
            errores.append(f"teoria.preguntas_chat: debe ser una lista de 2 a 3 strings no vacíos (recibidos: {num})")

    # 3. Validación de 'bancos' (opcional, 0 a 4 elementos)
    bancos = ed.get("bancos")
    if bancos is not None:
        if not isinstance(bancos, list):
            errores.append("bancos: debe ser una lista")
        elif len(bancos) > 4:
            errores.append(f"bancos: debe contener entre 0 y 4 elementos (recibidos: {len(bancos)})")
        else:
            for idx, b in enumerate(bancos):
                if not isinstance(b, dict):
                    errores.append(f"bancos[{idx}]: debe ser un objeto JSON (dict)")
                    continue
                for campo in ("banco", "fecha", "url", "resumen", "lectura"):
                    val = b.get(campo)
                    if val is None or not isinstance(val, str) or not val.strip():
                        errores.append(f"bancos[{idx}]: falta el campo obligatorio '{campo}'")

                if isinstance(b.get("fecha"), str):
                    f_str = b["fecha"].strip()
                    if not _es_fecha_valida(f_str):
                        errores.append(f"bancos[{idx}].fecha: formato inválido '{f_str}', debe ser AAAA-MM-DD")

                if isinstance(b.get("url"), str):
                    u_str = b["url"].strip()
                    if not (u_str.startswith("http://") or u_str.startswith("https://")):
                        errores.append(
                            f"bancos[{idx}].url: la URL debe comenzar con http:// o https:// (valor: '{u_str}')"
                        )

                if not (b.get("activo") or b.get("motivo_imagen")):
                    errores.append(f"bancos[{idx}]: falta 'activo' o 'motivo_imagen' para la imagen")
                if b.get("activo") and imagen_de_activo(str(b["activo"])) is None:
                    errores.append(f"bancos[{idx}].activo: '{b['activo']}' no tiene imagen en config/activos.json")
                if isinstance(b.get("motivo_imagen"), str):
                    motivo = b["motivo_imagen"].strip()
                    if motivo not in motivos_validos:
                        errores.append(
                            f"bancos[{idx}].motivo_imagen: motivo '{motivo}' no existe en config/motivos_imagen.json"
                        )

    # 4. Regla de estilo: CERO guiones largos
    errores.extend(_buscar_guiones_largos(ed))

    return errores


def resolver_fuentes_css(dir_base: Path) -> str:
    """Embebe fuentes WOFF2 locales como base64 para render autónomo offline."""
    fonts_dir = dir_base / "templates" / "stories" / "fonts"
    fuentes_map = [
        ("Goldman", 700, "goldman-700.woff2"),
        ("Plus Jakarta Sans", 400, "plus-jakarta-sans-400.woff2"),
        ("Plus Jakarta Sans", 600, "plus-jakarta-sans-600.woff2"),
        ("Plus Jakarta Sans", 700, "plus-jakarta-sans-700.woff2"),
    ]
    caras: list[str] = []
    for familia, peso, archivo in fuentes_map:
        f_path = fonts_dir / archivo
        if f_path.exists():
            b64 = base64.b64encode(f_path.read_bytes()).decode("ascii")
            caras.append(
                f"@font-face {{\n"
                f"  font-family: '{familia}';\n"
                f"  font-style: normal;\n"
                f"  font-weight: {peso};\n"
                f"  font-display: swap;\n"
                f"  src: url('data:font/woff2;base64,{b64}') format('woff2');\n"
                f"}}"
            )
    return "\n".join(caras)


def _formatear_fecha_es(f: date) -> str:
    """Formatea la fecha en español: '26 de octubre de 2026'."""
    meses = [
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    ]
    return f"{f.day} de {meses[f.month - 1]} de {f.year}"


def _construir_nota_guion_html(bloque_id: str, notas_guion: dict[str, str]) -> str:
    """Genera el bloque HTML de nota de apoyo docente si existe en notas_guion."""
    if not notas_guion or bloque_id not in notas_guion:
        return ""
    nota = notas_guion[bloque_id].strip()
    if not nota:
        return ""
    return (
        f'<div class="nota-guion">'
        f"<strong>Nota de apoyo docente:</strong>"
        f"<span>{e(nota)}</span>"
        f"</div>"
    )


def resolver_imagen_motivo(motivo: str, fecha: date, dir_base: Path) -> str | None:
    """La imagen ilustrativa del motivo como Data URL, o None si el banco no tiene ninguna.

    Elige por la fecha entre las que hay en disco y NO escribe `uso.json`: ese registro es el
    enfriamiento de las imágenes del correo, y el lienzo no debe gastárselo. Tampoco genera: si el
    motivo no tiene imágenes, el bloque sale sin imagen en vez de con un sustituto.
    """
    dir_motivo = dir_base / "data" / "imagenes_ilustrativas" / motivo
    if not dir_motivo.is_dir():
        return None
    imagenes = sorted(p for p in dir_motivo.iterdir() if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg"))
    if not imagenes:
        return None
    ruta = imagenes[fecha.toordinal() % len(imagenes)]
    mime = "image/png" if ruta.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(ruta.read_bytes()).decode('ascii')}"


def imagen_de_activo(ticker: str, raiz: Path = RAIZ) -> Path | None:
    """La imagen característica del activo: el campo `imagen` de config/activos.json.

    Es la misma que usan las Stories (templates/stories/assets/activos/), así cada par, índice y
    materia prima se reconoce por su foto y no por una genérica repetida.
    """
    try:
        catalogo = json.loads((raiz / "config" / "activos.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    pila: list[Any] = [catalogo]
    while pila:
        nodo = pila.pop()
        if isinstance(nodo, dict):
            if (nodo.get("ticker_mt5") == ticker or nodo.get("ticker") == ticker) and nodo.get("imagen"):
                ruta = raiz / "templates" / "stories" / str(nodo["imagen"])
                return ruta if ruta.exists() else None
            pila.extend(nodo.values())
        elif isinstance(nodo, list):
            pila.extend(nodo)
    return None


def _data_url(ruta: Path) -> str:
    mime = "image/png" if ruta.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(ruta.read_bytes()).decode('ascii')}"


def imagen_de(item: dict[str, Any], fecha: date, dir_base: Path) -> str | None:
    """Data URL de la imagen de una noticia o un banco: la del activo primero, el motivo después."""
    if item.get("activo"):
        ruta = imagen_de_activo(str(item["activo"]), dir_base)
        if ruta is not None:
            return _data_url(ruta)
    if item.get("motivo_imagen"):
        return resolver_imagen_motivo(str(item["motivo_imagen"]), fecha, dir_base)
    return None


def grafico_noticia(ticker: str, nombre: str, destino: Path) -> tuple[Path | None, str]:
    """La evolución real del activo de la noticia (cierres diarios de MT5), o el motivo de no tenerla.

    Reutiliza el banner del informe. Sin terminal no hay gráfico, y el bloque lo dice.
    """
    # Se dibuja en cada render: uno de una corrida anterior mostraría el precio de esa hora.
    destino.unlink(missing_ok=True)
    try:
        from grafico_informe import GraficoError, construir_grafico
    except ImportError as exc:
        return None, f"sin gráfico ({exc})"
    try:
        construir_grafico(ticker, nombre, destino, timeframe="D1", tema="oscuro",
                          subtitulo="Cierres diarios · MT5")
    except GraficoError as exc:
        return None, f"sin gráfico: {exc}"
    return destino, ""


DIAS_ES = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
NOMBRES_ACTIVO = {"USDCLP": "USD/CLP", "XAUUSD": "Oro · XAU/USD", "WTI.spot": "Petróleo WTI", "US100.spot": "Nasdaq 100 · US100"}
MAX_FILAS_AGENDA = 20
VENTANA_NOTICIA_H = 72


def _pie(fuente: str, fecha: str) -> str:
    return f'<div class="bloque-footer"><span>FUENTE: {e(fuente)}</span><span>{e(fecha)}</span></div>'


def _bloque(bid: str, kicker: str, titulo: str, horario: str, cuerpo: str, pie: str, notas: dict[str, str]) -> str:
    pos = next(p for p in POSICIONES_BLOQUES if p["id"] == bid)
    chip = f'<div class="bloque-horario">{e(horario)}</div>' if horario else ""
    return (
        f'<div class="bloque" id="bloque-{bid}" data-bloque="{bid}" style="left: {pos["x"]}px; top: {pos["y"]}px;">'
        f'<div class="bloque-header"><div><div class="bloque-kicker">{e(kicker)}</div>'
        f'<h2 class="bloque-titulo">{e(titulo)}</h2></div>{chip}</div>'
        f'<div class="bloque-cuerpo cuerpo-{bid}">{cuerpo}{_construir_nota_guion_html(bid, notas)}</div>{pie}</div>'
    )


def _fecha_corta(iso: str) -> str:
    """'2026-10-27' -> 'mar 27/10'; deja intacto lo que no sea una fecha."""
    try:
        d = date.fromisoformat(iso)
    except (TypeError, ValueError):
        return str(iso)
    return f"{DIAS_ES[d.weekday()][:3]} {d.day:02d}/{d.month:02d}"


def _hora_chile_de(fecha: date, hora_ny: str) -> str:
    """Una hora de Nueva York de ese día, en hora de Chile, con el desfase real de la fecha."""
    h, m = (int(x) for x in hora_ny.split(":"))
    ny = datetime(fecha.year, fecha.month, fecha.day, h, m, tzinfo=zoneinfo.ZoneInfo("America/New_York"))
    return ny.astimezone(zoneinfo.ZoneInfo("America/Santiago")).strftime("%H:%M")


def _filas_agenda(agenda: dict[str, Any], semanal: bool) -> tuple[list[dict[str, Any]], int]:
    eventos = [ev for ev in agenda.get("eventos", []) if isinstance(ev, dict)]
    # Chile va siempre: Investing marca "bajo" hasta la decisión de tasa del Banco Central.
    umbral = {"alto"} if semanal else {"alto", "medio"}
    eventos = [ev for ev in eventos if ev.get("pais") == "Chile" or str(ev.get("impacto", "")).lower() in umbral]
    vistos: set[tuple[str, str, str]] = set()
    unicos = []
    for ev in sorted(eventos, key=lambda ev: (str(ev.get("fecha", "")), str(ev.get("hora", "")))):
        clave = (str(ev.get("fecha", "")), str(ev.get("hora", "")), str(ev.get("nombre", "")))
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(ev)
    eventos = unicos
    return eventos[:MAX_FILAS_AGENDA], max(0, len(eventos) - MAX_FILAS_AGENDA)


def armar_bloques_html(
    fecha: date,
    datos: dict[str, Any],
    editorial: dict[str, Any],
    webinar_config: dict[str, Any],
    dia_nombre: str,
    dir_base: Path,
) -> str:
    """Los diez bloques del lienzo. Cada cifra sale de `datos.json` o del editorial con su fuente.

    No hay valores de respaldo: lo que falta se dice ("sin dato", "sin terminal"), nunca se rellena.
    """
    dia_cfg = webinar_config["dias"][dia_nombre]
    notas = editorial.get("notas_guion") or {}
    horarios: dict[str, str] = {}
    for paso in dia_cfg["guion"]:
        horarios.setdefault(paso["bloque"], f'{paso["desde"]} a {paso["hasta"]}')
    fecha_es = _formatear_fecha_es(fecha)
    generado = str(datos.get("meta", {}).get("generado", ""))[:16].replace("T", " ")
    noticia = editorial["noticia"]
    teoria = editorial["teoria"]
    bancos = editorial.get("bancos") or []
    bloques: list[str] = []

    # Portada
    temas = [noticia["titular"], f'Teoría: {teoria["tema"]}', "Lectura en vivo en MT5"]
    highlights = "".join(
        f'<div class="highlight-card"><span class="highlight-num">0{i}</span><span class="highlight-text">{e(t)}</span></div>'
        for i, t in enumerate(temas, 1)
    )
    cuerpo = (
        '<div class="portada-hero"><div class="portada-relator">'
        '<span class="relator-etiqueta">Relator de la sesión</span>'
        '<span class="relator-nombre">Benjamín Bravo Soza</span>'
        '<span class="relator-cargo">Departamento de Estudios GI</span></div>'
        f'<div class="portada-fecha-box"><span class="fecha-dia">{e(DIAS_ES[fecha.weekday()].upper())}</span>'
        f'<span class="fecha-valor">{e(fecha_es)}</span></div></div>'
        f'<div class="portada-highlights">{highlights}</div>'
    )
    bloques.append(_bloque("portada", "Grupo de Análisis de Mercado · Webinar educativo", dia_cfg["titulo"],
                           f'{dia_cfg["hora_inicio"]} a {dia_cfg["hora_fin"]} hora de Chile', cuerpo,
                           _pie("Departamento de Estudios GI", fecha_es), notas))

    # Aviso legal
    cuerpo = (
        '<div class="aviso-credencial"><span class="credencial-icono">⚖️</span><div>'
        '<div class="credencial-titulo">Acreditación CMV · Categoría Operadores · N° A-32915</div>'
        '<div class="credencial-sub">Benjamín Bravo Soza</div></div></div>'
        f'<div class="aviso-parrafos"><p>{e(webinar_config["disclaimer"])}</p>'
        '<p>Cada cifra de esta presentación lleva al pie su fuente y su fecha. Lo que no tiene dato, lo dice.</p></div>'
    )
    bloques.append(_bloque("aviso_legal", "Aviso legal", "Contenido educativo", horarios.get("aviso_legal", ""),
                           cuerpo, _pie("Departamento de Estudios GI", fecha_es), notas))

    # Agenda
    agenda = datos.get("agenda") if isinstance(datos.get("agenda"), dict) else {}
    semanal = dia_nombre == "lunes"
    if agenda.get("estado") == "sin_calendario":
        cuerpo = f'<div class="banner-sin-datos">El calendario no respondió al preparar: {e(agenda.get("motivo", "sin detalle"))}.</div>'
    else:
        filas, resto = _filas_agenda(agenda, semanal)
        if not filas:
            alcance = "de alto impacto esta semana" if semanal else "para hoy"
            cuerpo = f'<div class="banner-sin-datos">El calendario no trae eventos {alcance}.</div>'
        else:
            tr = "".join(
                f'<tr class="{"fila-chile" if ev.get("pais") == "Chile" else ""}">'
                f'<td><strong>{e(_fecha_corta(ev.get("fecha", "")))}</strong> {e(ev.get("hora", ""))}</td>'
                f'<td>{e(ev.get("pais", ""))}</td><td>{e(ev.get("nombre", ""))}</td>'
                f'<td>{e(ev.get("anterior") or "·")}</td><td>{e(ev.get("consenso") or "·")}</td>'
                f'<td><strong>{e(ev.get("actual") or "·")}</strong></td></tr>'
                for ev in filas
            )
            mas = f'<p class="agenda-mas">Y {resto} eventos más en el calendario completo.</p>' if resto else ""
            cuerpo = (
                '<table class="agenda-tabla"><thead><tr><th>Día y hora (Chile)</th><th>País</th><th>Evento</th>'
                f'<th>Anterior</th><th>Consenso</th><th>Actual</th></tr></thead><tbody>{tr}</tbody></table>{mas}'
            )
    titulo = "Los datos fuertes de la semana" if semanal else "La agenda de hoy"
    bloques.append(_bloque("agenda", "Calendario económico", titulo, horarios.get("agenda", ""), cuerpo,
                           _pie("Investing.com · hora de Chile", f"Preparado {generado}"), notas))

    # Noticia
    img = imagen_de(noticia, fecha, dir_base)
    img_html = (
        f'<div class="imagen-contenedor"><img class="imagen-ilustrativa" src="{img}" alt="">'
        '<span class="rotulo-imagen">Imagen ilustrativa</span></div>' if img else ""
    )
    vieja = ""
    try:
        if (fecha - date.fromisoformat(noticia["fecha"])).days * 24 > VENTANA_NOTICIA_H:
            vieja = f'Noticia del {_formatear_fecha_es(date.fromisoformat(noticia["fecha"]))}. '
    except ValueError:
        pass
    cuerpo = (
        f'<div class="noticia-grid"><div><h3 class="noticia-titular">{e(noticia["titular"])}</h3>'
        f'<p class="noticia-bajada">{e(noticia["bajada"])}</p>'
        f'<p class="noticia-origen">{e(vieja)}{e(noticia["medio"])} · {e(noticia["fecha"])} · '
        f'<a href="{e(noticia["url"])}" target="_blank" rel="noopener">Abrir la nota</a></p>'
        f'</div>{img_html}</div>'
    )
    if noticia.get("activo"):
        ticker = str(noticia["activo"])
        nombre = NOMBRES_ACTIVO.get(ticker, ticker)
        destino = dir_base / "data" / "webinar" / str(fecha) / f"grafico_{ticker.split('.')[0].lower()}.png"
        ruta, motivo = grafico_noticia(ticker, nombre, destino)
        cuerpo += (f'<div class="noticia-grafico"><img src="{_data_url(ruta)}" alt="{e(nombre)}"></div>'
                   if ruta else f'<p class="noticia-sin-grafico">{e(nombre)}: {e(motivo)}</p>')
    bloques.append(_bloque("noticia", "La noticia", "Lo que mueve al mercado", horarios.get("noticia", ""), cuerpo,
                           _pie(noticia["medio"], noticia["fecha"]), notas))

    # Bancos
    if bancos:
        tarjetas = []
        for b in bancos:
            thumb = imagen_de(b, fecha, dir_base)
            th = f'<img class="banco-thumb" src="{thumb}" alt="">' if thumb else ""
            extracto = f'<p class="banco-extracto">«{e(b["extracto"])}»</p>' if b.get("extracto") else ""
            tarjetas.append(
                f'<div class="banco-card"><div class="banco-header"><span class="banco-nombre">{e(b["banco"])}</span>'
                f'<span class="banco-fecha">{e(b["fecha"])}</span></div>'
                f'<p class="banco-resumen">{e(b["resumen"])}</p>{extracto}'
                f'<p class="banco-lectura"><strong>Nuestra lectura:</strong> {e(b["lectura"])}</p>'
                f'<div class="banco-media">{th}<a class="banco-fuente-link" href="{e(b["url"])}" '
                'target="_blank" rel="noopener">Abrir la fuente</a></div></div>'
            )
        cuerpo = f'<div class="bancos-grid">{"".join(tarjetas)}</div>'
        fechas = sorted({b["fecha"] for b in bancos})
        pie = _pie("Cada tarjeta con su enlace", " · ".join(fechas))
    else:
        cuerpo = '<div class="banner-sin-datos">Hoy no hay visiones de bancos verificadas con enlace y fecha.</div>'
        pie = _pie("Sin fuentes", fecha_es)
    bloques.append(_bloque("bancos", "Qué dicen los bancos", "Visiones con fuente", horarios.get("bancos", ""),
                           cuerpo, pie, notas))

    # Datos de data central
    items = []
    for d in datos.get("datos", []):
        if not isinstance(d, dict):
            continue
        valor = d.get("valor", "sin dato")
        cifra = valor if valor == "sin dato" else f'{valor} {d.get("unidad", "")}'.strip()
        cambio = d.get("cambio_5d")
        sub_cambio = f'<span class="sub">5 sesiones: {e(cambio)}</span>' if cambio else ""
        items.append(
            f'<div class="curva-item"><span class="lbl">{e(d.get("etiqueta", ""))}</span>'
            f'<span class="val">{e(cifra)}</span>{sub_cambio}'
            f'<span class="sub">Al {e(d.get("fecha", "sin dato"))} · {e(d.get("fuente", "sin fuente"))}</span></div>'
        )
    cuerpo = f'<div class="curva-items">{"".join(items)}</div>' if items else \
        '<div class="banner-sin-datos">Sin datos de data central al preparar.</div>'
    bloques.append(_bloque("datos", "Los números de fondo", "Tasas, dólar y materias primas",
                           horarios.get("datos", ""), cuerpo, _pie("data central y MT5, fuente en cada cifra",
                                                                   f"Preparado {generado}"), notas))

    # Teoría
    puntos = "".join(f"<li>{e(p)}</li>" for p in teoria["puntos"])
    cuerpo = (
        f'<div class="idea-central-box"><span class="idea-etiqueta">Idea central</span>'
        f'<span class="idea-texto">{e(teoria["idea_central"])}</span></div>'
        f'<ul class="puntos-lista">{puntos}</ul>'
        f'<div class="ejemplo-box"><span class="ejemplo-etiqueta">Ejemplo de esta semana</span>{e(teoria["ejemplo"])}</div>'
    )
    bloques.append(_bloque("teoria", "Teoría", teoria["tema"], horarios.get("teoria", ""), cuerpo,
                           _pie("Departamento de Estudios GI", fecha_es), notas))

    # MT5
    tarjetas = []
    for ticker, a in (datos.get("activos") or {}).items():
        nombre = NOMBRES_ACTIVO.get(ticker, ticker)
        if not isinstance(a, dict) or a.get("estado") == "sin_terminal" or "direccion" not in a:
            tarjetas.append(f'<div class="mt5-card sin-terminal"><div class="mt5-card-header">'
                            f'<span class="mt5-ticker">{e(nombre)}</span></div>'
                            '<div class="mt5-estado-linea">sin terminal al preparar</div></div>')
            continue
        direccion = str(a["direccion"])
        tarjetas.append(
            f'<div class="mt5-card"><div class="mt5-card-header"><span class="mt5-ticker">{e(nombre)}</span>'
            f'<span class="pill-direccion {e(direccion.lower())}">{e(direccion)}</span></div>'
            f'<div class="mt5-estado-linea">Estado: {e(str(a.get("estado", "")).lower())}</div>'
            f'<div class="mt5-nivel-caja"><span class="mt5-nivel-label">Nivel a vigilar</span>'
            f'<span class="mt5-nivel-valor">{e(a.get("vigilar", "sin dato"))}</span></div></div>'
        )
    campana = _hora_chile_de(fecha, "09:30")
    cuerpo = (
        '<div class="mt5-banner-destacado"><span class="mt5-icono">▶</span>'
        f'<span class="mt5-texto-banner">Paso a MT5: lectura en vivo. Wall Street abre a las {campana} hora de Chile.</span></div>'
        f'<div class="mt5-activos-grid">{"".join(tarjetas)}</div>'
    )
    bloques.append(_bloque("mt5", "Lectura en vivo", "Paso a MT5", horarios.get("mt5", ""), cuerpo,
                           _pie("MT5 · lectura de la estrategia activa", f"Preparado {generado}"), notas))

    # Preguntas
    preguntas = "".join(
        f'<div class="pregunta-item"><span class="icono">💬</span><span>{e(q)}</span></div>' for q in teoria["preguntas_chat"]
    )
    cuerpo = (
        '<p class="preguntas-intro">¿Qué activo quieres que revisemos en vivo?</p>'
        f'<div class="preguntas-chat-caja">{preguntas}</div>'
    )
    bloques.append(_bloque("preguntas", "Preguntas del chat", "Tu turno", horarios.get("preguntas", ""), cuerpo,
                           _pie("Departamento de Estudios GI", fecha_es), notas))

    # Cierre
    cuerpo = (
        f'<div class="cierre-resumen-box"><p class="cierre-resumen-texto">{e(teoria["idea_central"])}</p></div>'
        '<div class="cta-box"><span class="cta-kicker">Capacitaciones 1 a 1</span>'
        f'<span class="cta-descripcion">{e(webinar_config["cta"])}</span></div>'
    )
    bloques.append(_bloque("cierre", "Cierre", "Para llevarte hoy", horarios.get("cierre", ""), cuerpo,
                           _pie("Departamento de Estudios GI", fecha_es), notas))
    return "\n".join(bloques)


def exportar_a_pdf(html_path: Path, pdf_path: Path) -> Path:
    """Exporta el lienzo a PDF usando Playwright con una página 1920x1080 por bloque."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        try:
            pagina = navegador.new_page(viewport={"width": 1920, "height": 1080})
            pagina.goto(html_path.resolve().as_uri(), wait_until="networkidle")
            pagina.evaluate("document.fonts.ready.then(() => true)")
            pagina.emulate_media(media="print")
            pagina.pdf(
                path=str(pdf_path),
                print_background=True,
                prefer_css_page_size=True,
            )
        finally:
            navegador.close()
    return pdf_path


def rendir(
    fecha: date | None = None,
    *,
    exportar_pdf: bool = False,
    dir_base: Path | None = None,
) -> Path:
    """Genera el lienzo HTML interactivo (y opcionalmente PDF) para la fecha dada."""
    if dir_base is None:
        dir_base = RAIZ

    if fecha is None:
        tz = zoneinfo.ZoneInfo("America/Santiago")
        fecha = datetime.now(tz).date()
    elif isinstance(fecha, str):
        fecha = date.fromisoformat(fecha)

    fecha_str = str(fecha)
    data_dir = dir_base / "data" / "webinar" / fecha_str
    datos_file = data_dir / "datos.json"
    editorial_file = data_dir / "editorial.json"

    # 1. Verificar existencia de datos.json
    if not datos_file.exists():
        raise FileNotFoundError(f"Falta el archivo de datos requerido: {datos_file}")

    # 2. Verificar existencia de editorial.json
    if not editorial_file.exists():
        raise SystemExit(f"Falta el archivo editorial requerido: {editorial_file}")

    # 3. Validar editorial.json
    try:
        editorial = json.loads(editorial_file.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Error al leer editorial.json: {exc}")

    config_motivos_file = dir_base / "config" / "motivos_imagen.json"
    errores = validar_editorial(editorial, config_path=config_motivos_file)
    if errores:
        raise SystemExit("Hay piezas sin texto editorial o con infracciones:\n  " + "\n  ".join(errores))

    # 4. Leer datos.json
    try:
        datos = json.loads(datos_file.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"Error al leer datos.json: {exc}")

    # 5. Cargar configuración general del webinar
    config_webinar_file = dir_base / "config" / "webinar.json"
    webinar_config: dict[str, Any] = {}
    if config_webinar_file.exists():
        try:
            webinar_config = json.loads(config_webinar_file.read_text(encoding="utf-8"))
        except Exception:
            webinar_config = {}

    dias_semana_map = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    dia_nombre = dias_semana_map[fecha.weekday()]
    dias_cfg = webinar_config.get("dias", {})
    dia_cfg = dias_cfg.get(dia_nombre, {})

    if not dia_cfg.get("guion"):
        raise SystemExit(f"config/webinar.json no tiene guion para el {dia_nombre}")
    titulo_webinar = dia_cfg["titulo"]
    guion_pasos = dia_cfg["guion"]

    # 6. Resolver fuentes y bloques HTML
    fuentes_css = resolver_fuentes_css(dir_base)
    bloques_html = armar_bloques_html(
        fecha=fecha,
        datos=datos,
        editorial=editorial,
        webinar_config=webinar_config,
        dia_nombre=dia_nombre,
        dir_base=dir_base,
    )

    # 7. Cargar plantilla lienzo.html
    plantilla_file = dir_base / "templates" / "webinar" / "lienzo.html"
    if not plantilla_file.exists():
        raise FileNotFoundError(f"No se encontró la plantilla del lienzo: {plantilla_file}")

    plantilla = plantilla_file.read_text(encoding="utf-8")

    tokens: dict[str, str] = {
        "titulo_pestana": f"{titulo_webinar} · {fecha_str}",
        "fuentes_css": fuentes_css,
        "bloques_html": bloques_html,
        "guion_json": json.dumps(guion_pasos, ensure_ascii=False),
        "posiciones_json": json.dumps(POSICIONES_BLOQUES, ensure_ascii=False),
    }

    html_final = re.sub(r"\{\{(\w+)\}\}", lambda m: tokens.get(m.group(1), ""), plantilla)

    # 8. Escribir data/webinar/<fecha>/lienzo.html
    data_dir.mkdir(parents=True, exist_ok=True)
    salida_html = data_dir / "lienzo.html"
    salida_html.write_text(html_final, encoding="utf-8")

    # 9. Exportar PDF si fue solicitado
    if exportar_pdf:
        salida_pdf = data_dir / "lienzo.pdf"
        exportar_a_pdf(salida_html, salida_pdf)

    return salida_html


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Renderiza el lienzo HTML autónomo del webinar diario")
    parser.add_argument("--fecha", type=str, default=None, help="Fecha en formato AAAA-MM-DD")
    parser.add_argument("--pdf", action="store_true", help="Exportar también en formato PDF con Playwright")
    args = parser.parse_args()

    fecha_parsed = date.fromisoformat(args.fecha) if args.fecha else None
    ruta_generada = rendir(fecha_parsed, exportar_pdf=args.pdf)
    print(f"Lienzo generado exitosamente: {ruta_generada}")
