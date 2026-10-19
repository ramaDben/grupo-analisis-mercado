"""La pieza semanal en HTML: el análisis firmado, el panel del ejecutivo y el correo.

Es una herramienta interna (spec §2): por eso sale en HTML y no en PDF. Lo que llega al
cliente es lo que el ejecutivo copia desde acá: el correo, el texto de WhatsApp y la lámina.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any

from analista import RAIZ
from analista import agenda as ag
from analista import comercial as cm
from analista import esquema as es
from analista import fuentes as fu
from analista import informe_html as ih
from analista import oportunidad as op

PLANTILLA = RAIZ / "templates" / "oportunidad" / "pieza.html"


class InformeInvalido(ValueError):
    """La pieza no pasó los controles: no se arma."""


def _slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", es._plano(texto)).strip("-")


def _filas_niveles(a: dict[str, Any]) -> str:
    return "".join(f'<tr><th>{ih.e(r)}</th><td class="cifra">{ih.e(v)}</td></tr>' for r, v in cm._niveles(a))


def _seccion(titulo: str, cuerpo: str) -> str:
    return f'<h4 class="seccion">{ih.e(titulo)}</h4>{cuerpo}'


def _seccion_voces(fuentes: list[dict[str, Any]], direccion: str) -> str:
    if not fuentes:
        return _seccion("Voces de bancos y prensa",
                        '<p class="sin-voces">Sin voces de bancos o prensa atingentes esta vez.</p>')
    items, hay_discrepancia = [], False
    for f in fuentes:
        discrepa = fu.discrepa(f, direccion)
        hay_discrepancia |= discrepa
        marcas = ((' <span class="marca-discrepa">Discrepa de nuestra lectura</span>' if discrepa else "")
                  + (' <span class="marca-sin-verificar">enlace sin verificar</span>'
                     if f.get("verificacion") == "sin_verificar" else ""))
        items.append(f'<li><strong>{ih.e(f["entidad"])}</strong> · {ih.e(f["medio"])} · {ih.e(f["fecha"])}{marcas}'
                     f'<br>{ih.e(f["tesis"])} <a href="{ih.e(f["url"])}" target="_blank" rel="noopener noreferrer">'
                     'Ver nota</a></li>')
    nota = ('<p class="nota">Estas voces ven distinto que nuestra lectura: la nuestra es la que manda.</p>'
            if hay_discrepancia else "")
    return _seccion("Voces de bancos y prensa", f'<ul class="voces">{"".join(items)}</ul>{nota}')


def _cambio(h: dict[str, Any]) -> str:
    """«bajó 0,288 puntos en 5 sesiones»; las tasas ya traen «pb» y no repiten la unidad."""
    if h.get("sentido") == "estable":
        return "estable en 5 sesiones"
    if h.get("sentido") not in ("subió", "bajó"):
        return "sin dato a 5 sesiones"
    unidad = "" if str(h["cambio_5d"]).endswith(" pb") else f" {h['unidad_cambio']}"
    return f"{h['sentido']} {h['cambio_5d']}{unidad} en 5 sesiones"


def _efecto_hecho(h: dict[str, Any]) -> str:
    partes = [h.get("efecto") or "sin efecto atribuido"]
    if h.get("con_la_lectura"):
        partes.append(h["con_la_lectura"])
    if h.get("proxima_decision"):
        partes.append(f"próxima decisión: {h['proxima_decision']}")
    return " · ".join(partes)


def _tabla_hechos(hechos: list[dict[str, Any]]) -> str:
    if not hechos:
        return ""
    filas = "".join(
        f'<tr><th>{ih.e(h["driver"])}</th><td>{ih.e(h["nivel"])}<br><span class="nota">{ih.e(h["fecha"])} · '
        f'{ih.e(h["fuente"])}</span></td><td>{ih.e(_cambio(h))}</td><td>{ih.e(_efecto_hecho(h))}</td></tr>'
        for h in hechos)
    return ('<p class="rotulo-chico">Lo que pasa hoy con sus drivers</p><table class="hechos"><tr><th>Driver</th>'
            f'<th>Dato</th><th>Cambio</th><th>Qué hace con el activo</th></tr>{filas}</table>')


def _enlace_calendario(texto: str) -> str:
    return f'<a href="{ih.e(ag.URL_CALENDARIO)}" target="_blank" rel="noopener noreferrer">{ih.e(texto)}</a>'


def _agenda_ficha(d: dict[str, Any], dias_clave: str, dir_pedido: Path | None, imagen: str) -> str:
    agenda = d.get("agenda")
    if agenda is None:  # pieza anterior al 2026-10-17: la agenda venía en texto
        lista = d.get("agenda_semana") or []
        return ('<p class="rotulo-chico">Agenda de la semana</p><ul>' + "".join(f"<li>{ih.e(x)}</li>" for x in lista)
                + '</ul>') if lista else ""
    cuerpo = f'<p class="rotulo-chico">Días clave del {ih.e(agenda["desde"])} al {ih.e(ag.hasta_cubierto(agenda))}</p>'
    if agenda.get("parcial"):
        cuerpo += ('<p class="nota">El calendario respondió a medias: revisa el resto de los días en el '
                   f'{_enlace_calendario("calendario de Investing.com")}.</p>')
    if agenda["estado"] == "sin_calendario":
        return cuerpo + ('<p class="nota">No pude leer el calendario económico para esta ventana: revisa los días '
                         f'clave en el {_enlace_calendario("calendario de Investing.com")} antes de enviar el correo.</p>')
    if not agenda["eventos"]:
        return cuerpo + f'<p>{ih.e(ag.texto_vacia(agenda))}</p>'
    if dias_clave:
        cuerpo += f'<p>{ih.e(dias_clave)}</p>'
    if imagen and dir_pedido is not None and (dir_pedido / imagen).exists():
        cuerpo += (f'<img class="calendario-img" src="{ih._data_uri(dir_pedido / imagen)}" '
                   f'alt="Calendario económico del {ih.e(agenda["desde"])} al {ih.e(ag.hasta_cubierto(agenda))}">')
    filas = "".join(
        f'<tr><td>{ih.e(e["dia"])}<br>{ih.e(e["hora"])}</td><td>{ih.e(e["evento"])} · {ih.e(e["pais"])}</td>'
        f'<td>{ih.e(e["anterior"] or "sin dato")}</td><td>{ih.e(e["esperado"] or "sin dato")}</td>'
        f'<td>{ih.e(e["efecto"] or "sin efecto declarado")}</td></tr>' for e in agenda["eventos"])
    return (cuerpo + '<table class="agenda"><tr><th>Cuándo</th><th>Dato</th><th>Previo</th><th>Esperado</th>'
            f'<th>Qué hace con el activo</th></tr>{filas}</table>'
            f'<p class="nota">Fuente: {_enlace_calendario("calendario completo de Investing.com")}.</p>')


def _seccion_fundamental(d: dict[str, Any], a: dict[str, Any], contexto: str, dias_clave: str = "",
                         dir_pedido: Path | None = None, imagen: str = "") -> str:
    t = a["ticker"]
    drivers = d["drivers"].get(t, [])
    cuerpo = f'<p>{ih.e(contexto)}</p>' + _tabla_hechos(d.get("hechos") or [])
    if drivers:
        cuerpo += '<p class="rotulo-chico">Drivers del activo</p><ul>' + "".join(f"<li>{ih.e(x)}</li>" for x in drivers) + '</ul>'
    if d["curva"]:
        filas = "".join("<tr>" + "".join(f"<td>{ih.e(c)}</td>" for c in fila) + "</tr>" for fila in d["curva"])
        cuerpo += f'<p class="rotulo-chico">Curva de tasas de EE.UU.</p><table class="curva">{filas}</table>'
    cuerpo += _agenda_ficha(d, dias_clave, dir_pedido, imagen)
    if d["fundamental"]["sin_drivers"]:
        cuerpo += '<p class="nota">Este activo no tiene drivers declarados en el catálogo de la casa.</p>'
    return _seccion("Fundamental", cuerpo)


MOTIVO_SIN_CONTRATO = op.MOTIVO_SIN_CONTRATO
_motivo = op.motivo_sin_simulacion


def _panel(a: dict[str, Any], ejecutivo: str) -> str:
    esc, f = a["escenario"], a["fmt"]
    motivo = _motivo(a)
    if motivo:
        return ('<div class="panel sin-simulacion"><p>Sin simulación en este análisis: '
                f'{ih.e(motivo)}</p>'
                '<label><input type="checkbox" name="incluir" checked> Incluir en el correo</label></div>')
    lejos = (f'<p class="nota">El objetivo está a {str(esc["dias_objetivo"]).replace(".", ",")} días de '
             'movimiento típico (ATR diario).</p>' if esc.get("dias_objetivo") else "")
    condicion = op.texto_condicion(esc, f["entrada"])
    cond = f'<p class="condicion">{ih.e(condicion)}</p>' if condicion else ""
    cabeza = (
        f'<p class="rotulo-ilustrativo">{ih.e(cm.ROTULO_ILUSTRATIVO)}</p><h4>Objetivo de la simulación (1:3)</h4>'
        f'<p class="niveles-sim">Entrada {ih.e(f["entrada"])} · Stop {ih.e(f["stop"])} · '
        f'Objetivo {ih.e(f["objetivo"])}</p>{cond}{lejos}'
        '<label><input type="checkbox" name="incluir" checked> Incluir en el correo</label>')
    if op.sin_contrato(a):  # nota interna del ejecutivo: el cliente igual ve los niveles
        return (f'<div class="panel">{cabeza}<p class="nota">{ih.e(MOTIVO_SIN_CONTRATO.capitalize())}: el correo '
                'lleva los niveles, sin los montos.</p></div>')
    return (
        '<div class="panel">' + cabeza +
        '<label>Pérdida aceptable (CLP)<input type="number" name="perdida" min="0" step="1000" value="100000"></label>'
        '<label>Capital<input type="number" name="capital" min="0" step="10000" value="2000000"></label>'
        '<div class="resultado"><div class="perdida"><span>Pérdida si toca el stop</span>'
        '<strong data-r="perdida">Escribe la pérdida aceptable</strong></div>'
        '<div class="ganancia"><span>Ganancia si llega al objetivo</span><strong data-r="ganancia"></strong></div>'
        '<p data-r="volumen"></p></div>'
        f'<p class="autor-sim">Simulación realizada por {ih.e(ejecutivo)}</p>'
        '</div>'
    )


# El correo sigue la maqueta del prototipo (#254), que el director pidió de vuelta: banda con el
# logo, portada, precio con la píldora de dirección, cuadros rojo y verde del mismo tamaño y las
# dos firmas en columnas. Outlook clásico no entiende `var()` ni `rgba()`: los colores van en hex
# leídos de `marca.css`, la familia en cada elemento y las imágenes en base64.
F_SANS = "'Segoe UI',Arial,Helvetica,sans-serif"
F_DISPLAY = "'Goldman','Segoe UI',Arial,Helvetica,sans-serif"
_ROLES = {"fondo": "fondo", "fondo_alt": "fondo-alt", "tarjeta": "fondo-acento", "acento": "acento",
          "acento_azul": "acento-azul", "sube": "sube", "baja": "baja", "fondo_sube": "fondo-sube",
          "fondo_baja": "fondo-baja", "texto_1": "texto-1", "texto_2": "texto-2", "texto_borde": "texto-borde"}


def _mezclar(color: str, fondo: str, alfa: float) -> str:
    """El hex de `color` con opacidad `alfa` sobre `fondo`."""
    a, b = (tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in (color, fondo))
    return "#" + "".join(f"{round(y + (x - y) * alfa):02X}" for x, y in zip(a, b))


def paleta() -> dict[str, str]:
    """Los colores de la pieza por rol, leídos de `marca.css` para que la fuente siga siendo una."""
    hoja = ih.MARCA_CSS.read_text(encoding="utf-8")
    m = dict(re.findall(r"--([\w-]+):\s*(#[0-9A-Fa-f]{6})\b", hoja))
    c = {k: m[v] for k, v in _ROLES.items()}
    c["linea"] = _mezclar(c["acento"], c["fondo_alt"], 0.35)
    return c


def paleta_correo(c: dict[str, str]) -> dict[str, str]:
    """La paleta del correo: cuerpo claro y una apertura oscura (director, 2026-10-18).

    Outlook invierte los fondos oscuros en modo oscuro y al reenviar, y un correo todo negro se
    rompe o se imprime mal: el cuerpo va sobre blanco y solo la apertura de cada activo es oscura.
    Los roles son los mismos de `paleta()` para que el resto del módulo no cambie; el acento de
    texto se oscurece (el de marca no se lee sobre blanco) y el de marca queda en `marca`.
    """
    return {**c, "fondo": "#F3F6F5", "fondo_alt": "#FFFFFF", "tarjeta": "#F3F6F5", "acento": "#2F8F7A",
            "sube": "#1F8F5F", "baja": "#C93434", "fondo_sube": "#E3F6EE", "fondo_baja": "#FDECEC",
            "texto_1": "#0B1517", "texto_2": "#6B7779", "texto_borde": "#1D2528", "linea": "#DFE6E4",
            "blanco": "#FFFFFF", "marca": c["acento"], "hero": "#0B1214", "hero_tarjeta": "#101C1F",
            "hero_linea": "#24383C", "hero_texto_2": "#B7C6C8", "hero_rotulo": "#8EA3A6"}


def _color_direccion(direccion: str, c: dict[str, str]) -> str:
    return {"ALCISTA": c["sube"], "BAJISTA": c["baja"]}.get(direccion.upper(), c["texto_2"])


def _p(texto: str, c: dict[str, str], tam: int = 16, peso: int = 500, color: str = "texto_borde",
       margen: str = "0 0 12px 0", clase: str = "") -> str:
    cl = f' class="{clase}"' if clase else ""
    return (f'<p{cl} style="margin:{margen};font-family:{F_SANS};font-size:{tam}px;line-height:{round(tam * 1.5)}px;'
            f'font-weight:{peso};color:{c[color]};">{texto}</p>')


def _rotulo(texto: str, c: dict[str, str], margen: str = "0 0 8px 0") -> str:
    return (f'<p style="margin:{margen};font-family:{F_DISPLAY};font-size:14px;line-height:20px;letter-spacing:1.8px;'
            f'text-transform:uppercase;font-weight:700;color:{c["acento"]};">{texto}</p>')


def _tabla(contenido: str, estilo: str = "", fondo: str = "") -> str:
    bg = f' bgcolor="{fondo}"' if fondo else ""
    return (f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0"{bg} '
            f'style="{estilo}">{contenido}</table>')


def _separador(alto: int = 14) -> str:
    # Fila de alto fijo: Word ignora el margen de una tabla.
    return _tabla(f'<tr><td height="{alto}" style="height:{alto}px;font-size:0;line-height:0;">&nbsp;</td></tr>')


def _cuadro(fondo: str, borde: str, rotulo: str, pie: str, clase: str, c: dict[str, str],
            valor: str = "Sin calcular") -> str:
    return (f'<td class="stack" width="49%" valign="top" bgcolor="{c[fondo]}" style="padding:18px;'
            f'background:{c[fondo]};border:2px solid {c[borde]};border-radius:12px;">'
            f'<p style="margin:0 0 6px 0;font-family:{F_SANS};font-size:14px;line-height:20px;font-weight:800;'
            f'text-transform:uppercase;letter-spacing:1px;color:{c[borde]};">{rotulo}</p>'
            f'<p style="margin:0;font-family:{F_DISPLAY};font-size:28px;line-height:34px;font-weight:700;'
            f'color:{c["texto_1"]};"><strong class="{clase}">{valor}</strong></p>'
            f'<p style="margin:6px 0 0 0;font-family:{F_SANS};font-size:14px;line-height:20px;font-weight:500;'
            f'color:{c["texto_borde"]};">{pie}</p></td>')


def _simulacion_correo(a: dict[str, Any], ejecutivo: str, c: dict[str, str]) -> str:
    """La simulación del ejecutivo: cuadro rojo (stop) y verde (objetivo) del mismo tamaño."""
    motivo = _motivo(a)
    if motivo:
        celda = _p(f'<strong style="color:{c["texto_1"]};">Sin simulación en este análisis:</strong> {ih.e(motivo)}',
                   c, tam=15, margen="0")
        return _tabla(f'<tr><td bgcolor="{c["fondo"]}" style="padding:14px 16px;background:{c["fondo"]};'
                      f'border:1px solid {c["linea"]};border-radius:12px;">{celda}</td></tr>')
    f = a["fmt"]
    condicion = op.texto_condicion(a["escenario"], f["entrada"])
    fuerte = lambda x: f'<strong style="color:{c["texto_1"]};">{ih.e(x)}</strong>'  # noqa: E731

    contrato = a.get("contrato")
    s = op.simular(contrato, a["escenario"], 100000, 2000000) if contrato else None

    if s:
        perdida_str = f"−${s['perdida']:,}".replace(",", ".")
        ganancia_str = f"+${s['ganancia']:,}".replace(",", ".")
        volumen_str = f"Volumen {str(s['volumen']).replace('.', ',')}{': es el mínimo que permite el broker.' if s['bajo_minimo'] else '.'}"
    else:
        perdida_str = "Sin calcular"
        ganancia_str = "Sin calcular"
        volumen_str = ""

    cuadros = _tabla(
        '<tr>'
        + _cuadro("fondo_baja", "baja", "Si toca el stop", f"Pérdida al llegar a {ih.e(f['stop'])}", "sim-perdida", c, perdida_str)
        + '<td class="stack stack-gap" width="2%" style="font-size:0;line-height:0;">&nbsp;</td>'
        + _cuadro("fondo_sube", "sube", "Si llega al objetivo", f"Ganancia al llegar a {ih.e(f['objetivo'])}",
                  "sim-ganancia", c, ganancia_str)
        + '</tr>').replace("<table ", '<table class="sim-montos" ', 1)
    return (
        '<table class="sim-bloque" role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">'
        '<tr><td style="padding:0;">'
        + _rotulo(f"Simulación realizada por {ih.e(ejecutivo)}", c, margen="0 0 4px 0")
        + _p(ih.e(cm.ROTULO_ILUSTRATIVO), c, tam=13, color="texto_2", margen="0 0 10px 0")
        + _p(f'Objetivo 1:3 · Entrada {fuerte(f["entrada"])} · Stop {fuerte(f["stop"])} · '
             f'Objetivo {fuerte(f["objetivo"])}', c, tam=14, margen="0 0 16px 0")
        + (_p(f'<strong style="color:{c["texto_1"]};">{ih.e(condicion)}</strong>', c, tam=14, margen="0 0 12px 0") if condicion else "")
        + ("" if op.sin_contrato(a) else cuadros)
        + _p(volumen_str, c, tam=13, peso=700, margen="14px 0 4px 0", clase="sim-volumen sim-montos")
        + _p("Las dos cifras se muestran juntas y del mismo tamaño a propósito: el apalancamiento amplifica "
             "igual las ganancias y las pérdidas.", c, tam=12, color="texto_2", margen="0",
             clase="sim-montos")
        + '</td></tr></table>'
    )


TIPS_EXPLICADO = ", medida en bonos del Tesoro que se ajustan por inflación (TIPS)"


def _cambio_correo(h: dict[str, Any]) -> str:
    """El cambio en texto de cliente: «puntos base» y no «pb»; sin cifra no hay cláusula (no se escribe «sin dato»)."""
    if h.get("sentido") not in ("estable", "subió", "bajó"):
        return ""
    return ", " + re.sub(r" pb\b", " puntos base", _cambio(h))


def _fecha_hechos(hechos: list[dict[str, Any]]) -> str:
    """La fecha del dato más reciente, con la que los hechos mismos se fechan: «viernes 09/10»."""
    def clave(h: dict[str, Any]) -> tuple[int, int]:
        m = re.search(r"(\d{2})/(\d{2})", h.get("fecha", ""))
        return (int(m.group(2)), int(m.group(1))) if m else (0, 0)
    return max(hechos, key=clave)["fecha"]


def _celda_hecho(texto: str, c: dict[str, str], ultima: bool, peso: int = 500, color: str = "texto_borde",
                 ancho: str = "", extra: str = "") -> str:
    borde = "" if ultima else f"border-bottom:1px solid {c['linea']};"
    w = f' width="{ancho}"' if ancho else ""
    return (f'<td valign="top"{w} style="padding:10px 8px;{borde}font-family:{F_SANS};font-size:14px;line-height:20px;'
            f'font-weight:{peso};color:{c[color]};">{texto}{extra}</td>')


def _sintesis_dominancia(seleccionados: list[dict[str, Any]]) -> str:
    if not seleccionados:
        return ""

    def clave_fecha(h: dict[str, Any]) -> tuple[int, int]:
        m = re.search(r"(\d{2})/(\d{2})", h.get("fecha", ""))
        return (int(m.group(2)), int(m.group(1))) if m else (0, 0)

    h_dom = max(seleccionados, key=lambda h: (clave_fecha(h), 1 if h.get("sentido") in ("subió", "bajó") else 0))
    sentido = h_dom.get("sentido", "")
    driver_raw = h_dom.get("driver", "")

    if "dollar index" in driver_raw.lower() or "dxy" in driver_raw.lower():
        mov = "el retroceso" if sentido == "bajó" else ("el avance" if sentido == "subió" else "el nivel")
        contra = "contra nuestra lectura técnica bajista" if "contra" in (h_dom.get("con_la_lectura") or "") else "a favor de nuestra lectura técnica"
        efecto_fuerza = "alcista" if "alza" in (h_dom.get("efecto") or "") else "bajista"
        return f"Hoy domina {mov} del Dollar Index (DXY) en el mercado cambiario, cuya debilidad ejerce la mayor fuerza {efecto_fuerza} inmediata {contra}."

    driver = driver_raw.replace(" (TIPS)", "").strip()
    mov = "el retroceso" if sentido == "bajó" else ("el avance" if sentido == "subió" else "la evolución")
    art = "del" if any(w in driver.lower() for w in ("dólar", "dollar", "bono", "petróleo", "cobre", "oro")) else "de la"
    efecto = h_dom.get("efecto", "")
    con_lec = h_dom.get("con_la_lectura", "")

    partes = [f"Hoy domina {mov} {art} {driver}"]
    if efecto:
        partes.append(f"que {efecto}")
    if con_lec:
        partes.append(f"y {con_lec}")

    return " ".join(partes).rstrip(".") + "."


def seleccionar_drivers_correo(hechos: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str]:
    """Selecciona deterministamente los dos drivers más representativos para el correo.

    Criterio:
    1. Si hay 2 o menos hechos, se usan los que existan.
    2. Si hay hechos a favor y en contra de nuestra lectura, selecciona exactamente 1 de cada grupo,
       priorizando aquellos con movimiento efectivo (subió/bajó) y mayor inmediatez temporal.
    3. Si todos los hechos apuntan al mismo lado, selecciona los 2 con mayor desplazamiento o
       efecto activo (descarta los estáticos o sin efecto atribuido; si no hay con postura clara,
       usa los dos primeros con efecto no neutro).
    4. Genera una síntesis de dominancia determinista dictaminando cuál factor domina hoy en el
       mercado por inmediatez temporal y peso de mercado, describiendo su efecto sin inventar cifras.
    """
    if not hechos:
        return [], ""
    if len(hechos) <= 2:
        sel = list(hechos)
        return sel, _sintesis_dominancia(sel)

    def clave_fecha(h: dict[str, Any]) -> tuple[int, int]:
        m = re.search(r"(\d{2})/(\d{2})", h.get("fecha", ""))
        return (int(m.group(2)), int(m.group(1))) if m else (0, 0)

    def es_dinamico(h: dict[str, Any]) -> bool:
        return h.get("sentido") in ("subió", "bajó")

    a_favor = [h for h in hechos if "a favor" in (h.get("con_la_lectura") or "").lower()]
    en_contra = [h for h in hechos if "en contra" in (h.get("con_la_lectura") or "").lower()]

    if a_favor and en_contra:
        mejor_favor = max(a_favor, key=lambda h: (1 if es_dinamico(h) else 0, clave_fecha(h)))
        mejor_contra = max(en_contra, key=lambda h: (1 if es_dinamico(h) else 0, clave_fecha(h)))
        if clave_fecha(mejor_contra) > clave_fecha(mejor_favor):
            seleccionados = [mejor_contra, mejor_favor]
        else:
            seleccionados = [mejor_favor, mejor_contra]
    else:
        dinamicos = [h for h in hechos if es_dinamico(h) and h.get("efecto")]
        if len(dinamicos) >= 2:
            dinamicos.sort(key=clave_fecha, reverse=True)
            seleccionados = dinamicos[:2]
        else:
            con_efecto = [h for h in hechos if h.get("efecto")]
            if len(con_efecto) >= 2:
                seleccionados = con_efecto[:2]
            else:
                seleccionados = hechos[:2]

    return seleccionados, _sintesis_dominancia(seleccionados)


def _hechos_correo(hechos: list[dict[str, Any]], c: dict[str, str]) -> str:
    """Los drivers del día en tabla: factor, dato, cambio y efecto sobre el activo."""
    if not hechos:
        return ""
    seleccionados, sintesis = seleccionar_drivers_correo(hechos)
    if not seleccionados:
        return ""

    cab = "".join(
        f'<th align="left" style="padding:6px 8px;border-bottom:2px solid {c["marca"]};font-family:{F_SANS};'
        f'font-size:12px;line-height:16px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;'
        f'color:{c["texto_2"]};">{t}</th>' for t in ("Factor", "Hoy", "Cambio", "Efecto en el activo"))
    filas = []
    for i, h in enumerate(seleccionados):
        ultima = i == len(seleccionados) - 1
        efecto = ""
        if h.get("efecto"):
            efecto = ih.e(h["efecto"][:1].upper() + h["efecto"][1:])
            if h.get("con_la_lectura"):
                efecto += f'<br><span style="color:{c["texto_2"]};font-weight:500;">{ih.e(h["con_la_lectura"])}</span>'
        cambio = _cambio_correo(h).lstrip(", ") or "sin cambio medido"
        filas.append('<tr>'
                     + _celda_hecho(ih.e(h["driver"].replace(" (TIPS)", TIPS_EXPLICADO)), c, ultima, 700, "texto_1", "34%")
                     + _celda_hecho(ih.e(h["nivel"]), c, ultima, 700, "texto_1", "16%")
                     + _celda_hecho(ih.e(cambio), c, ultima, ancho="20%")
                     + _celda_hecho(efecto or "sin efecto atribuido", c, ultima, color="texto_1", ancho="30%") + '</tr>')

    sintesis_html = ""
    if sintesis:
        sintesis_html = (
            f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="{c["fondo"]}" '
            f'style="background:{c["fondo"]};border:1px solid {c["linea"]};border-left:3px solid #50C0A8;border-radius:6px;margin:10px 0 14px 0;">'
            f'<tr><td style="padding:10px 14px;font-family:{F_SANS};font-size:13px;line-height:19px;color:{c["texto_1"]};">'
            f'<strong style="color:{c["acento"]};">Síntesis de dominancia:</strong> {ih.e(sintesis)}'
            f'</td></tr></table>'
        )

    return (_rotulo(f"Los drivers al {ih.e(_fecha_hechos(seleccionados))}", c, margen="10px 0 8px 0")
            + _tabla(f'<tr>{cab}</tr>' + "".join(filas))
            + sintesis_html
            + _separador(8))


def _grafico_dolar_correo(ruta: Path | None, c: dict[str, str]) -> str:
    """El gráfico del Dollar Index, bajo la tabla de drivers: solo sale si el dólar es uno de ellos."""
    if ruta is None or not ruta.exists():
        return ""
    return (_p("El dólar (Dollar Index), marco 4H", c, tam=13, peso=600, color="texto_2", margen="0 0 6px 0")
            + _tabla(f'<tr><td style="padding:0;"><img src="{ih._data_uri(ruta)}" width="558" height="{_alto_png(ruta, 558)}" '
                     'alt="Gráfico del Dollar Index (DXY)" style="display:block;border:0;width:558px;max-width:100%;'
                     'height:auto;border-radius:11px;"></td></tr>',
                     estilo=f'border:1px solid {c["linea"]};border-radius:12px;') + _separador(8))


def _dias_clave_correo(d: dict[str, Any], dias_clave: str, dir_pedido: Path, imagen: str, c: dict[str, str]) -> str:
    """Sin calendario el bloque no va: «no pude leer» no es texto de cliente."""
    agenda = d.get("agenda")
    if not agenda or agenda["estado"] == "sin_calendario":
        return ""
    cuerpo = _rotulo(f'Días clave hasta el {ih.e(ag.hasta_cubierto(agenda))}', c, margen="14px 0 8px 0")
    if not agenda["eventos"]:
        return cuerpo + _p(ih.e(ag.texto_vacia(agenda)), c, tam=15)
    if dias_clave:
        cuerpo += _p(ih.e(dias_clave), c, tam=15)
    ruta = dir_pedido / imagen if imagen else None
    if ruta is not None and ruta.exists():
        cuerpo += _tabla(
            f'<tr><td style="padding:0;"><img src="{ih._data_uri(ruta)}" width="558" height="{_alto_png(ruta, 558)}" '
            f'alt="Calendario económico del {ih.e(agenda["desde"])} al {ih.e(ag.hasta_cubierto(agenda))}" '
            'style="display:block;border:0;width:558px;max-width:100%;height:auto;border-radius:11px;"></td></tr>',
            estilo=f'border:1px solid {c["linea"]};border-radius:12px;') + _separador(8)
    return cuerpo + _p(f'<a href="{ih.e(ag.URL_CALENDARIO)}" style="color:{c["acento"]};">Ver el calendario '
                       'económico completo</a>', c, tam=14)


def _fecha_es(iso: str) -> str:
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return iso


_FLECHAS_DIR = {
    "ALCISTA": ("⬆️", "⬇️"),
    "BAJISTA": ("⬇️", "⬆️"),
    "LATERAL": ("↔️", "↔️"),
}


def _seleccionar_bancos_correo(fuentes: list[dict[str, Any]], direccion: str) -> list[dict[str, Any]]:
    """Selecciona hasta un banco a favor y uno en contra de la lista cerrada de prestigio."""
    bancos = fu.bancos(fuentes) if hasattr(fu, "bancos") else [
        f for f in fuentes if isinstance(f, dict) and f.get("entidad")
    ]
    a_favor = [b for b in bancos if not fu.discrepa(b, direccion)]
    en_contra = [b for b in bancos if fu.discrepa(b, direccion)]
    a_favor.sort(key=lambda b: b.get("fecha", ""), reverse=True)
    en_contra.sort(key=lambda b: b.get("fecha", ""), reverse=True)
    seleccionados = []
    if a_favor:
        seleccionados.append(a_favor[0])
    if en_contra:
        seleccionados.append(en_contra[0])
    return seleccionados


def _voces_correo(fuentes: list[dict[str, Any]], direccion: str, c: dict[str, str]) -> str:
    """Las voces bancarias seleccionadas (hasta 1 a favor y 1 en contra) con flechas y sin semáforos."""
    if not fuentes:
        return ""
    if hasattr(fu, "seleccionar_bancos_correo"):
        bancos_sel = fu.seleccionar_bancos_correo(fuentes, direccion)
    else:
        bancos_sel = _seleccionar_bancos_correo(fuentes, direccion)

    if not bancos_sel:
        return ""

    flechas = _FLECHAS_DIR.get(direccion.upper(), ("⬇️", "⬆️"))
    tarjetas = []
    for f in bancos_sel:
        discrepa = fu.discrepa(f, direccion)
        color_etiqueta = "#6B7779" if discrepa else "#2F8F7A"
        flecha = flechas[1] if discrepa else flechas[0]
        texto_postura = f"{flecha} {'En contra' if discrepa else 'A favor'} de nuestra lectura"

        tarjetas.append(
            f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#F8FAFC" '
            f'style="background:#F8FAFC;border:1px solid #DFE6E4;border-radius:6px;margin:0 0 10px 0;">'
            f'<tr><td style="padding:12px 14px;">'
            f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">'
            f'<tr><td align="left" style="font-family:{F_SANS};font-size:13px;font-weight:700;color:{c["texto_1"]};">'
            f'{ih.e(f["entidad"])} · {ih.e(f["medio"])} · {ih.e(_fecha_es(f["fecha"]))}'
            f'</td>'
            f'<td align="right" style="font-family:{F_SANS};font-size:12px;font-weight:700;color:{color_etiqueta};">'
            f'{texto_postura}'
            f'</td></tr></table>'
            f'<p style="margin:6px 0 6px 0;font-family:{F_SANS};font-size:14px;line-height:20px;color:{c["texto_borde"]};">'
            f'{ih.e(f["tesis"])}</p>'
            f'<p style="margin:0;font-family:{F_SANS};font-size:12px;font-weight:600;">'
            f'<a href="{ih.e(f["url"])}" target="_blank" rel="noopener noreferrer" style="color:{c["acento"]};text-decoration:underline;">'
            f'Ver nota completa en {ih.e(f["medio"])} →</a></p>'
            f'</td></tr></table>'
        )

    intro = _p("Contrastamos nuestro mapa técnico con las proyecciones públicas de la banca global. "
               "Cuando una entidad ve distinto que nuestra lectura, lo transparentamos para ofrecer una perspectiva completa e informada.",
               c, tam=15, margen="0 0 14px 0")

    return _rotulo("Qué dicen los bancos", c, margen="14px 0 8px 0") + intro + "".join(tarjetas) + _separador(8)


def _alto_png(ruta: Path, ancho: int) -> int:
    """Alto proporcional al ancho de impresión, leído del encabezado del PNG (Outlook lo pide)."""
    cab = ruta.read_bytes()[:24]
    w, h = int.from_bytes(cab[16:20], "big"), int.from_bytes(cab[20:24], "big")
    return round(ancho * h / w) if w and h else ancho * 9 // 16


_ARTICULO_ACTIVO = {"oro": "del", "dólar": "del", "euro": "del", "petróleo": "del", "cobre": "del",
                    "nasdaq": "del", "dow": "del", "libra": "de la", "plata": "de la"}

_SUJETO_MAP = {
    "oro": "El oro", "plata": "La plata", "petróleo": "El petróleo",
    "cobre": "El cobre", "dólar": "El dólar", "euro": "El euro",
    "nasdaq": "El Nasdaq", "dow": "El Dow", "libra": "La libra",
}


def _articulo_sujeto(nombre: str) -> str:
    """«El oro», «La plata»: retorna el sujeto con artículo determinado según _ARTICULO_ACTIVO."""
    primero = nombre.split()[0].lower() if nombre.split() else ""
    if primero in _SUJETO_MAP:
        return _SUJETO_MAP[primero]
    art = _ARTICULO_ACTIVO.get(primero)
    if art == "del":
        return f"El {nombre}"
    if art == "de la":
        return f"La {nombre}"
    return nombre


def _titulo_analisis(nombre: str) -> str:
    """«Análisis técnico del oro»: el artículo sale del primer término del nombre; sin artículo, «de»."""
    primero = nombre.split()[0].lower() if nombre.split() else ""
    return f"Análisis técnico {_ARTICULO_ACTIVO.get(primero, 'de')} {nombre}"


def _nombre_firma(nombre: str) -> str:
    """«Benjamín Ignacio Bravo Soza» firma como «Benjamín Bravo Soza»: nombre y dos apellidos."""
    partes = nombre.split()
    return " ".join([partes[0], *partes[-2:]]) if len(partes) > 3 else nombre


def titular_base(a: dict[str, Any]) -> str:
    """Fórmula base Alt. 3: foco en claridad direccional, nivel de control y escaneo rápido."""
    lec, f = a["lectura"], a["fmt"]
    return (
        f"{_articulo_sujeto(a['nombre'])} en {f['precio']}: la línea de seguridad en {f['invalidacion']} "
        f"marca el pulso {lec['direccion'].lower()} hacia {f['objetivo_tori']}"
    )


_NUMERO = re.compile(r"\b\d+(?:[.,]\d+)*\b")


def _parsear_precio(s: str) -> float:
    s = s.strip()
    if "." in s and "," in s:
        s = s.replace(".", "").replace(",", ".")
    elif "." in s:
        partes = s.split(".")
        if len(partes) == 2 and len(partes[1]) == 3:
            s = s.replace(".", "")
    elif "," in s:
        partes = s.split(",")
        if len(partes) == 2 and len(partes[1]) != 3:
            s = s.replace(",", ".")
    return float(s)


def _formatear_precio_banco(valor: float, digits: int) -> str:
    if valor == int(valor):
        return f"{int(valor):,}".replace(",", ".")
    try:
        from pipeline_carrusel import formatear_precio
        return formatear_precio(valor, digits)
    except Exception:
        return f"{valor:,.{digits}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def titular_variante(a: dict[str, Any], fuentes: list[dict[str, Any]]) -> str:
    """Alt. 2 (choque de bancos) si hay exactamente 1 a favor y 1 en contra con un precio inequívoco."""
    direccion = a["lectura"]["direccion"]
    if hasattr(fu, "seleccionar_bancos_correo"):
        bancos_sel = fu.seleccionar_bancos_correo(fuentes, direccion)
    else:
        bancos_sel = _seleccionar_bancos_correo(fuentes, direccion)

    a_favor = [b for b in bancos_sel if not fu.discrepa(b, direccion)]
    en_contra = [b for b in bancos_sel if fu.discrepa(b, direccion)]
    if len(a_favor) != 1 or len(en_contra) != 1:
        return titular_base(a)

    b_favor, b_contra = a_favor[0], en_contra[0]
    nums_favor = _NUMERO.findall(b_favor.get("tesis", ""))
    nums_contra = _NUMERO.findall(b_contra.get("tesis", ""))
    if len(nums_favor) != 1 or len(nums_contra) != 1:
        return titular_base(a)

    try:
        val_favor = _parsear_precio(nums_favor[0])
        val_contra = _parsear_precio(nums_contra[0])
        digits = a.get("digits", 2)
        precio_favor = _formatear_precio_banco(val_favor, digits)
        precio_contra = _formatear_precio_banco(val_contra, digits)
    except (ValueError, TypeError):
        return titular_base(a)

    primero = a["nombre"].split()[0].lower() if a["nombre"].split() else ""
    art_nom = _ARTICULO_ACTIVO.get(primero, "de")
    return (
        f"Entre los {precio_favor} de {b_favor['entidad']} y los {precio_contra} de {b_contra['entidad']}: "
        f"el gráfico {art_nom} {a['nombre'].lower()} fija su frontera en {a['fmt']['invalidacion']}"
    )


def titular_correo(a: dict[str, Any], fuentes: list[dict[str, Any]] | None = None, variante: bool = False) -> str:
    """El titular editorial del correo: variante si se pide y califica, o base."""
    if variante and fuentes:
        return titular_variante(a, fuentes)
    return titular_base(a)


def asunto_sugerido(a: dict[str, Any], fuentes: list[dict[str, Any]] | None = None, variante: bool = False) -> str:
    """Función pura y exportada: devuelve el titular sugerido como asunto."""
    return titular_correo(a, fuentes, variante)


def preheader_sugerido(a: dict[str, Any], fuentes: list[dict[str, Any]] | None = None,
                       d: dict[str, Any] | None = None) -> str:
    """Texto descriptivo para la bandeja de entrada: lectura técnica, bancos y agenda."""
    lec, f = a["lectura"], a["fmt"]
    temp = a.get("temporalidad", "4H").split()[0]
    base = f"Sesgo {lec['direccion'].lower()} en {temp} condicionado a la línea de {f['invalidacion']}."

    if hasattr(fu, "seleccionar_bancos_correo"):
        bancos_sel = fu.seleccionar_bancos_correo(fuentes or [], lec["direccion"])
    else:
        bancos_sel = _seleccionar_bancos_correo(fuentes or [], lec["direccion"])

    bancos_txt = ""
    if len(bancos_sel) >= 2:
        bancos_txt = f" Qué proyectan {bancos_sel[0]['entidad']} y {bancos_sel[1]['entidad']}"
    elif len(bancos_sel) == 1:
        bancos_txt = f" Qué proyecta {bancos_sel[0]['entidad']}"

    eventos = ((d or {}).get("agenda") or {}).get("eventos") or []
    paises = []
    for ev in eventos:
        pais = ev.get("pais", "")
        if pais and pais not in paises:
            paises.append(pais)

    if paises:
        p_str = " y ".join(paises[:2])
        cierre = f", y qué vigila la mesa antes de los datos de {p_str}."
    else:
        cierre = ", y qué vigila la mesa antes de los próximos datos macroeconómicos."

    if bancos_txt:
        return f"{base}{bancos_txt}{cierre}"
    return f"{base}{cierre.lstrip(',')}"


def _hero_activo(a: dict[str, Any], titular: str, c: dict[str, str], bajada: str = "", autor=None,
                 d: dict[str, Any] | None = None) -> str:
    """La apertura oscura del activo: kicker, titular, bajada, firma y snapshot de 4 cifras."""
    lec, f = a["lectura"], a["fmt"]
    titular_final = titular or titular_base(a)

    kicker = (
        f'<p style="margin:0 0 10px 0;font-family:{F_SANS};font-size:12px;line-height:16px;font-weight:700;'
        f'letter-spacing:1.8px;text-transform:uppercase;color:#50C0A8;">'
        f'ANÁLISIS TÉCNICO Y FUNDAMENTAL · {ih.e(a["nombre"].upper())} ({ih.e(a["ticker_visible"])})'
        f'</p>'
    )

    titular_bloque = (
        f'<h1 class="hero-title" style="margin:0 0 14px 0;font-family:{F_SANS};font-size:25px;line-height:32px;'
        f'font-weight:800;letter-spacing:-0.3px;color:{c["blanco"]};">'
        f'{ih.e(titular_final)}</h1>'
    )

    bajada_bloque = (
        f'<p style="margin:0 0 20px 0;font-family:{F_SANS};font-size:15px;line-height:23px;font-weight:400;'
        f'color:{c["hero_texto_2"]};">{ih.e(bajada)}</p>' if bajada else ""
    )

    nombre_autor = _nombre_firma(autor.nombre) if autor else "Benjamín Bravo Soza"
    cargo_autor = autor.cargo if autor else "Dirección de Análisis Técnico"
    vigencia_txt = (
        f"Vigencia del análisis: {d['vigencia']['desde']} al {d['vigencia']['hasta']} · Hora oficial de Chile"
        if d and "vigencia" in d else ""
    )
    firma_hero = (
        f'<table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin:0 0 22px 0;">'
        f'<tr><td style="border-left:2px solid #50C0A8;padding-left:10px;">'
        f'<p style="margin:0;font-family:{F_SANS};font-size:12px;line-height:17px;font-weight:600;color:{c["hero_rotulo"]};">'
        f'Realizado por {ih.e(nombre_autor)} · {ih.e(cargo_autor)} GI</p>'
        + (f'<p style="margin:1px 0 0 0;font-family:{F_SANS};font-size:12px;line-height:16px;color:#50C0A8;font-weight:600;">'
           f'{ih.e(vigencia_txt)}</p>' if vigencia_txt else "")
        + '</td></tr></table>'
    )

    dir_nombre = lec["direccion"].upper()
    color_dir = c["baja"] if dir_nombre == "BAJISTA" else (c["sube"] if dir_nombre == "ALCISTA" else c["hero_rotulo"])
    temp_corta = a.get("temporalidad", "4H").split()[0]

    cifras_datos = [
        ("Precio de referencia", f["precio"], "Precio de foto"),
        ("Sesgo técnico", dir_nombre, f"{temp_corta} · swing", color_dir),
        ("Línea de seguridad", f.get("invalidacion") or "sin nivel", "Invalida el sesgo"),
        ("Objetivo técnico", f.get("objetivo_tori") or "sin nivel", "Proyección técnica", "#50C0A8"),
    ]

    celdas = []
    for i, c_item in enumerate(cifras_datos):
        rotulo, valor, sub = c_item[0], c_item[1], c_item[2]
        col_val = c_item[3] if len(c_item) > 3 else c["blanco"]
        pad_r = 0 if i == len(cifras_datos) - 1 else 6
        celdas.append(
            f'<td class="stack-col" width="25%" valign="top" style="padding-right:{pad_r}px;">'
            f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#101C1F" '
            f'style="background:#101C1F;border:1px solid #24383C;border-radius:6px;">'
            f'<tr><td style="padding:10px 10px 9px 10px;">'
            f'<p style="margin:0;font-family:{F_SANS};font-size:10px;line-height:14px;font-weight:700;'
            f'letter-spacing:0.6px;text-transform:uppercase;color:{c["hero_rotulo"]};">{ih.e(rotulo)}</p>'
            f'<p class="hero-cifra" style="margin:3px 0 0 0;font-family:{F_SANS};font-size:17px;line-height:22px;'
            f'font-weight:800;color:{col_val};white-space:nowrap;">{ih.e(valor)}</p>'
            f'<p style="margin:2px 0 0 0;font-family:{F_SANS};font-size:10px;line-height:13px;color:{c["hero_rotulo"]};">{ih.e(sub)}</p>'
            f'</td></tr></table></td>'
        )

    snapshot_tabla = _tabla(f'<tr>{"".join(celdas)}</tr>')

    return (
        f'<tr><td class="pad-hero" bgcolor="{c["hero"]}" style="padding:26px 36px 26px 36px;background:{c["hero"]};">'
        f'{kicker}{titular_bloque}{bajada_bloque}{firma_hero}{snapshot_tabla}'
        f'</td></tr>'
    )


def _bloque_correo(a: dict[str, Any], titular: str, contexto: str, dir_pedido: Path, ejecutivo: str,
                   c: dict[str, str], d: dict[str, Any] | None = None, dias_clave: str = "",
                   fuentes: list[dict[str, Any]] | tuple = (), imagen_calendario: str = "",
                   imagen_dolar: str = "", autor=None, bajada: str = "") -> str:
    """El bloque del activo en el correo: apertura oscura y cuerpo claro."""
    lec = a["lectura"]
    color_dir = _color_direccion(lec["direccion"], c)
    grafico = _tabla(
        f'<tr><td style="padding:0;background:#000000;">'
        f'<img src="{ih._data_uri(dir_pedido / a["grafico"])}" width="558" height="{_alto_png(dir_pedido / a["grafico"], 558)}" '
        f'alt="Gráfico de {ih.e(a["nombre"])}" style="display:block;border:0;width:558px;max-width:100%;'
        f'height:auto;border-radius:8px;"></td></tr>',
        estilo=f'border:1px solid {c["linea"]};border-radius:8px;overflow:hidden;')

    salida = lec.get("salida", "")
    pull_quote = ""
    if salida:
        pull_quote = (
            f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="{c["fondo"]}" '
            f'style="background:{c["fondo"]};border-left:4px solid #50C0A8;border-radius:0 8px 8px 0;margin:0 0 24px 0;">'
            f'<tr><td style="padding:16px 20px;">'
            f'<p style="margin:0 0 6px 0;font-family:Georgia,\'Times New Roman\',serif;font-size:16px;line-height:24px;'
            f'font-style:italic;color:{c["texto_1"]};font-weight:600;">'
            f'«{ih.e(salida)}»</p>'
            f'<p style="margin:0;font-family:{F_SANS};font-size:12px;line-height:16px;font-weight:700;'
            f'letter-spacing:0.8px;text-transform:uppercase;color:{c["acento"]};">'
            'Dirección de Análisis Técnico · Grupo Inteligencia</p>'
            f'</td></tr></table>'
        )

    escenarios = "".join(_p(f'{ih.e(x["flecha"])} {ih.e(x["texto"])}', c, margen="0 0 8px 0")
                         for x in lec["escenarios"])
    ruta_dolar = dir_pedido / imagen_dolar if imagen_dolar else None

    cierre_consultivo = (
        f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="{c["fondo"]}" '
        f'style="background:{c["fondo"]};border:1px solid {c["linea"]};border-radius:10px;margin:20px 0 24px 0;">'
        f'<tr><td style="padding:20px 24px;">'
        f'<p style="margin:0 0 8px 0;font-family:{F_SANS};font-size:16px;line-height:22px;font-weight:800;color:{c["texto_1"]};">'
        '¿Revisamos este análisis juntos en la plataforma MT5?</p>'
        f'<p style="margin:0;font-family:{F_SANS};font-size:14px;line-height:21px;color:{c["texto_borde"]};">'
        'Podemos mirar en conjunto el gráfico en tiempo real, comprobar el comportamiento del precio frente a la línea de seguridad '
        'y revisar la plataforma con tu cuenta de inversión.</p>'
        f'</td></tr></table>'
    )

    return (
        _hero_activo(a, titular, c, bajada=bajada, autor=autor, d=d)
        + '<tr><td class="pad" style="padding:28px 40px 0 40px;">'
        + (_rotulo(ih.e(_titulo_analisis(a["nombre"])), c, margen="0 0 2px 0")
           + _p(f"Realizado por {ih.e(_nombre_firma(autor.nombre))} · {ih.e(autor.cargo)} GI", c, tam=13,
                color="texto_2", margen="0 0 14px 0")
           if autor is not None else "")
        + grafico + _separador()
        + _p(ih.e(contexto), c)
        + pull_quote
        + _hechos_correo((d or {}).get("hechos") or [], c)
        + _grafico_dolar_correo(ruta_dolar, c)
        + _dias_clave_correo(d or {}, dias_clave, dir_pedido, imagen_calendario, c)
        + _voces_correo(list(fuentes), lec["direccion"], c)
        + _rotulo(f'Los tres escenarios · <span style="color:{color_dir};">'
                  f'{ih.e(lec["direccion"].capitalize())}</span>', c, margen="10px 0 8px 0")
        + escenarios
        + _p(f'⏱️ <strong style="color:{c["texto_1"]};">{ih.e(a["temporalidad"])}</strong>', c, tam=15,
             margen="4px 0 18px 0")
        + _simulacion_correo(a, ejecutivo, c)
        + cierre_consultivo
        + _separador(26) + '</td></tr>'
    )


WA_MARCA = "%%WA%%"  # lo reemplaza la página por el enlace de WhatsApp del ejecutivo


def _boton_whatsapp(c: dict[str, str]) -> str:
    """El botón de WhatsApp del cierre: una celda con fondo (Outlook no pinta el fondo de un enlace)."""
    return (
        '<tr><td class="pad" style="padding:6px 40px 0 40px;">'
        + _tabla(f'<tr><td align="center" bgcolor="{c["marca"]}" style="background:{c["marca"]};border-radius:8px;">'
                 f'<a href="{WA_MARCA}" style="display:block;padding:16px 20px;font-family:{F_SANS};font-size:17px;'
                 f'line-height:24px;font-weight:700;text-decoration:none;color:#06201A;">'
                 'Escríbeme por WhatsApp para revisar este análisis →</a></td></tr>')
        + '</td></tr>'
    )


def _firma_correo(ejecutivo: dict[str, Any], autor, c: dict[str, str]) -> str:
    """El ejecutivo comercial en grande: quien le escribe al cliente."""
    rol = " · ".join(x for x in (CARGO_SIMULA, "GI") if x)
    contacto = ejecutivo.get("contacto", "")
    return (
        '<tr><td class="pad" style="padding:24px 40px 6px 40px;">'
        f'<p style="margin:0;font-family:{F_SANS};font-size:26px;line-height:32px;font-weight:800;'
        f'letter-spacing:-.3px;color:{c["texto_1"]};">{ih.e(ejecutivo["nombre"])}</p>'
        f'<p style="margin:2px 0 0 0;font-family:{F_SANS};font-size:13px;line-height:20px;font-weight:500;'
        f'color:{c["texto_2"]};">{ih.e(rol)}</p>'
        + (f'<p style="margin:2px 0 0 0;font-family:{F_SANS};font-size:13px;line-height:20px;font-weight:500;'
           f'color:{c["texto_2"]};">{ih.e(contacto)}</p>' if contacto else "")
        + '</td></tr>'
    )


def _marco_correo(d: dict[str, Any], ed: dict[str, Any], ejecutivo: dict[str, Any], autor,
                  c: dict[str, str], asunto: str = "", preheader: str = "") -> str:
    """El marco del correo: preheader oculto, ficha de control, cabecera con logo, cierre y aviso."""
    if not asunto and d.get("activos"):
        asunto = asunto_sugerido(d["activos"][0], ed.get("fuentes"))
    if not preheader and d.get("activos"):
        preheader = preheader_sugerido(d["activos"][0], ed.get("fuentes"), d)

    preheader_oculto = (
        f'<div style="display:none;font-size:1px;color:#EEF2F1;line-height:1px;max-height:0px;'
        f'max-width:0px;opacity:0;overflow:hidden;mso-hide:all;">'
        f'{ih.e(preheader)}'
        f'&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;'
        f'&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;'
        f'&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;&zwnj;&nbsp;'
        f'</div>'
    )

    ficha_control = (
        f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#101D20" '
        f'style="background:#101D20;border-bottom:1px solid #24383C;">'
        f'<tr><td align="center" style="padding:14px 16px;">'
        f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="max-width:640px;">'
        f'<tr><td style="font-family:{F_SANS};font-size:12px;line-height:18px;color:#B7C6C8;">'
        f'<p style="margin:0 0 4px 0;"><strong style="color:#50C0A8;text-transform:uppercase;letter-spacing:0.8px;">'
        f'Asunto sugerido:</strong> {ih.e(asunto)}</p>'
        f'<p style="margin:0;"><strong style="color:#50C0A8;text-transform:uppercase;letter-spacing:0.8px;">'
        f'Preheader:</strong> {ih.e(preheader)}</p>'
        f'</td></tr></table></td></tr></table>'
    )

    cabecera = (
        f'<tr><td class="pad" bgcolor="{c["hero"]}" style="background:{c["hero"]};padding:22px 40px;'
        f'border-bottom:1px solid #1A282B;">'
        + _tabla(f'<tr><td valign="middle" align="left">'
                 f'<table role="presentation" cellspacing="0" cellpadding="0" border="0">'
                 f'<tr><td valign="middle" style="padding-right:12px;">'
                 f'<img src="{ih._data_uri(ih.LOGO)}" width="190" alt="Grupo Inteligencia" '
                 f'style="display:block;border:0;width:190px;height:auto;"></td></tr></table></td>'
                 f'<td valign="middle" align="right" style="font-family:{F_SANS};font-size:12px;line-height:16px;'
                 f'font-weight:600;color:{c["hero_rotulo"]};">Edición técnica<br>'
                 f'<span style="color:{c["blanco"]};font-weight:700;">{ih.e(d.get("edicion", d["vigencia"]["desde"]))}</span></td></tr>')
        + '</td></tr>'
        f'<tr><td bgcolor="{c["marca"]}" height="3" style="height:3px;line-height:3px;font-size:3px;'
        f'background:{c["marca"]};background-image:linear-gradient(90deg,{c["acento_azul"]},{c["marca"]});">&nbsp;</td></tr>'
    )

    portada = (
        '<tr><td class="pad" style="padding:30px 40px 22px 40px;">'
        + _p('<span class="saludo-cliente">Estimado(a):</span>', c, tam=18, peso=700, color="texto_1", margen="0 0 12px 0")
        + _p("Te escribo para compartirte el análisis técnico y fundamental vigente, preparado por la "
             "Dirección de Análisis Técnico de Grupo Inteligencia: la lectura del activo, sus niveles, lo que "
             "puede mover su precio y qué dicen los bancos. Me gustaría revisarlo contigo en la plataforma MT5.",
             c, tam=17, margen="0")
        + '</td></tr>'
        f'<tr><td class="pad" bgcolor="{c["tarjeta"]}" style="background:{c["tarjeta"]};'
        f'border-left:4px solid {c["marca"]};padding:18px 40px 20px 36px;">'
        + _rotulo("Análisis técnico vigente", c, margen="0 0 8px 0")
        + f'<h1 class="h1" style="margin:0;font-family:{F_DISPLAY};font-size:22px;line-height:29px;'
          f'font-weight:700;color:{c["texto_1"]};"><!--TITULO--></h1></td></tr>'
    )

    cierre = (
        '<!--WA-->' + _firma_correo(ejecutivo, autor, c)
        + f'<tr><td class="pad" bgcolor="{c["fondo_alt"]}" style="background:{c["fondo_alt"]};padding:0 40px 32px 40px;">'
        + _tabla(f'<tr><td bgcolor="{c["fondo"]}" style="padding:14px 18px;background:{c["fondo"]};border-radius:8px;">'
                 + _p(ih.e(cm.AVISO_PIEZA), c, tam=12, color="texto_2", margen="0 0 6px 0")
                 + _p("Análisis general de mercado, idéntico para todos sus destinatarios. No es asesoría de inversión "
                      "ni considera el perfil de quien lo lee. Prohibida su reproducción total o parcial sin autorización de Grupo Inteligencia.",
                      c, tam=11, color="hero_rotulo", margen="0")
                 + '</td></tr>')
        + '</td></tr>'
    )

    return (
        preheader_oculto + ficha_control
        + f'<table id="correo-root" role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" '
        f'bgcolor="{c["fondo_alt"]}" style="width:100%;background:{c["fondo_alt"]};font-family:{F_SANS};">'
        '<tr><td align="center" style="padding:28px 10px;">'
        '<!--[if (gte mso 9)|(IE)]>'
        '<table role="presentation" width="640" align="center" cellpadding="0" cellspacing="0" border="0">'
        '<tr><td>'
        '<![endif]-->'
        f'<table role="presentation" class="shell" width="640" cellspacing="0" cellpadding="0" border="0" '
        f'bgcolor="{c["fondo_alt"]}" style="width:640px;max-width:640px;background:{c["fondo_alt"]};'
        f'border:1px solid {c["linea"]};">'
        + cabecera + portada + '<!--ACTIVOS-->' + cierre
        + '</table>'
        '<!--[if (gte mso 9)|(IE)]>'
        '</td></tr></table>'
        '<![endif]-->'
        '</td></tr></table>'
    )


PENDIENTE = "[Tu nombre]"
CARGO_SIMULA = "Departamento de Inversiones"


def _norma(nombre: str) -> str:
    return " ".join(nombre.lower().split())


def es_el_autor(nombre: str, autor) -> bool:
    return _norma(nombre) == _norma(autor.nombre)


def _enlazar_imagenes(html: str, rutas: list[Path], publicar) -> str:
    """Cambia, en el correo, cada imagen embebida por su URL pública (Gmail no muestra las `data:`)."""
    for ruta in dict.fromkeys(rutas):
        if ruta.exists():
            html = html.replace(ih._data_uri(ruta), publicar(ruta))
    return html


def armar(pieza: dict[str, Any], dir_pedido: Path, ejecutivo: dict[str, Any], autor, hoy: date,
          publicar=None) -> str:
    """`publicar(ruta) -> url` deja las imágenes del correo en una URL pública; sin él van embebidas."""
    errs = es.errores(pieza)
    if errs:
        raise InformeInvalido("; ".join(errs))
    d, ed = pieza["datos"], pieza["editorial"]
    # El autor firma el análisis y jamás la simulación: si quien pide es el propio autor (el director
    # probando), la simulación queda a nombre de un campo que el comercial completa, con su nombre.
    pendiente = es_el_autor(ejecutivo["nombre"], autor)
    if pendiente:
        ejecutivo = {"nombre": PENDIENTE, "cargo": "", "contacto": ""}
    nombre_ej = ejecutivo["nombre"]
    c0 = paleta()
    c = paleta_correo(c0)
    bloques, correos, datos_js = [], [], []
    for a in d["activos"]:
        t = a["ticker"]
        lec = a["lectura"]
        escenarios = "".join(f"<li>{ih.e(x['flecha'])} {ih.e(x['texto'])}</li>" for x in lec["escenarios"])
        lamina = dir_pedido / cm.nombre_lamina(t)
        dias = (ed.get("dias_clave") or {}).get(t, "")
        imagen_cal = (pieza.get("imagenes") or {}).get("calendario", "")
        imagen_dolar = (pieza.get("imagenes") or {}).get("dolar", "")
        bloques.append(
            f'<section class="activo" data-ticker="{ih.e(t)}">'
            f'<header><h2>{ih.e(a["nombre"])} · {ih.e(a["ticker_visible"])}</h2>'
            f'{ih.pildora(lec["direccion"].capitalize())}</header>'
            f'<div class="analisis"><h3>{ih.e(ed["titulares"][t])}</h3>'
            + _seccion("Lectura técnica",
                       f'<img src="{ih._data_uri(dir_pedido / a["grafico"])}" alt="Gráfico de {ih.e(a["nombre"])}">'
                       f'<table class="niveles">{_filas_niveles(a)}</table><ul class="escenarios">{escenarios}</ul>'
                       f'<p class="salida">{ih.e(lec["salida"])}</p>'
                       f'<p class="temporalidad">⏱️ {ih.e(a["temporalidad"])} · Foto del {ih.e(a["foto"]["fecha"])}, '
                       f'precio {ih.e(a["fmt"]["precio"])}</p>')
            + _seccion_fundamental(d, a, ed["contexto"][t], dias, dir_pedido, imagen_cal)
            + _seccion_voces(ed["fuentes"], lec["direccion"])
            + f'<p class="firma-analisis">Análisis: {ih.e(autor.nombre)} · {ih.e(autor.cargo)}</p></div>'
            f'{_panel(a, nombre_ej)}'
            '<div class="acciones"><button type="button" class="copiar-wa">Copiar texto de WhatsApp</button>'
            + (f'<a class="descargar" download="{ih.e(lamina.name)}" href="{ih._data_uri(lamina)}">Descargar lámina</a>'
               if lamina.exists() else "")
            + '</div></section>')
        titular_act = titular_correo(a, ed.get("fuentes"))
        correos.append(f'<template class="correo-activo" data-ticker="{ih.e(t)}">'
                       f'{_bloque_correo(a, titular_act, ed["contexto"][t], dir_pedido, nombre_ej, c, d=d, dias_clave=dias, fuentes=ed["fuentes"], imagen_calendario=imagen_cal, imagen_dolar=imagen_dolar, autor=autor, bajada=ed.get("bajada", ""))}</template>')
        datos_js.append({"ticker": t, "nombre": a["nombre"], "digits": a["digits"], "escenario": a["escenario"], "contrato": a["contrato"],
                         "fmt": a["fmt"], "motivo": _motivo(a),
                         "condicion": op.texto_condicion(a["escenario"], a["fmt"]["entrada"]), "whatsapp": cm.texto_whatsapp_base(a, ed["titulares"][t], ed["contexto"][t])})
    marco = _marco_correo(d, ed, ejecutivo, autor, c)
    if publicar is not None:
        imgs = (pieza.get("imagenes") or {})
        rutas = [ih.LOGO, *(dir_pedido / a["grafico"] for a in d["activos"]),
                 *(dir_pedido / imgs[k] for k in ("calendario", "dolar") if imgs.get(k))]
        marco = _enlazar_imagenes(marco, rutas, publicar)
        correos = [_enlazar_imagenes(x, rutas, publicar) for x in correos]
    tokens = {
        "marco": marco,
        "raiz": "".join(f"--{k.replace('_', '-')}:{v};" for k, v in c0.items()),
        "boton_wa": _boton_whatsapp(c),
        "titulo": ih.e(ed["titular"]), "logo": ih._data_uri(ih.LOGO), "semana": ih.e(f"Vigente hasta el {d['vigencia']['hasta']}"),
        "edicion": ih.e(d["edicion"]), "titular": ih.e(ed["titular"]), "bajada": ih.e(ed["bajada"]),
        "activos": "".join(bloques), "correos": "".join(correos), "firma": ih.bloque_firma(autor, hoy),
        "aviso": ih.e(cm.AVISO_PIEZA), "ejecutivo": "" if pendiente else ih.e(nombre_ej),
        "fuentes": ih._fuentes(),
        "datos": json.dumps({"ejecutivo": nombre_ej, "pendiente": pendiente, "autor_nombre": autor.nombre, "cargo": ejecutivo.get("cargo", ""),
                             "contacto": ejecutivo.get("contacto", ""), "autor": cm.firma(autor),
                             "aviso": cm.AVISO_PIEZA, "titular": ed["titular"], "activos": datos_js},
                            ensure_ascii=False).replace("</", "<\\/"),
        "simulador": op.SIMULADOR_JS.read_text(encoding="utf-8").strip(),
    }
    return re.sub(r"\{\{(\w+)\}\}", lambda m: tokens[m.group(1)], PLANTILLA.read_text(encoding="utf-8"))


def guardar(pieza: dict[str, Any], dir_pedido: Path, ejecutivo: dict[str, Any], autor, hoy: date,
            publicar=None) -> Path:
    ruta = dir_pedido / f"analisis_{_slug(pieza['datos']['ticker'])}_{_slug(ejecutivo['nombre'])}.html"
    ruta.write_text(armar(pieza, dir_pedido, ejecutivo, autor, hoy, publicar), encoding="utf-8")
    return ruta
