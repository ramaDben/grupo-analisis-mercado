"""La pieza semanal en HTML: el análisis firmado, el panel del ejecutivo y el correo.

Es una herramienta interna (spec §2): por eso sale en HTML y no en PDF. Lo que llega al
cliente es lo que el ejecutivo copia desde acá: el correo, el texto de WhatsApp y la lámina.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from analista import RAIZ
from analista import comercial as cm
from analista import esquema as es
from analista import informe_html as ih
from analista import oportunidad as op

PLANTILLA = RAIZ / "templates" / "oportunidad" / "pieza.html"


class InformeInvalido(ValueError):
    """La pieza no pasó los controles: no se arma."""


def _slug(texto: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", es._plano(texto)).strip("-")


def _filas_niveles(a: dict[str, Any]) -> str:
    return "".join(f'<tr><th>{ih.e(r)}</th><td class="cifra">{ih.e(v)}</td></tr>' for r, v in cm._niveles(a))


MOTIVO_SIN_CONTRATO = op.MOTIVO_SIN_CONTRATO
_motivo = op.motivo_sin_simulacion


def _panel(a: dict[str, Any], ejecutivo: str) -> str:
    esc, f = a["escenario"], a["fmt"]
    motivo = _motivo(a)
    if motivo:
        return ('<div class="panel sin-simulacion"><p>Sin simulación esta semana: '
                f'{ih.e(motivo)}</p>'
                '<label><input type="checkbox" name="incluir" checked> Incluir en el correo</label></div>')
    lejos = (f'<p class="nota">El objetivo está a {str(esc["dias_objetivo"]).replace(".", ",")} días de '
             'movimiento típico (ATR diario).</p>' if esc.get("dias_objetivo") else "")
    return (
        '<div class="panel">'
        '<h4>Objetivo de la simulación (1:3)</h4>'
        f'<p class="niveles-sim">Entrada {ih.e(f["entrada"])} · Stop {ih.e(f["stop"])} · '
        f'Objetivo {ih.e(f["objetivo"])}</p>{lejos}'
        '<label><input type="checkbox" name="incluir" checked> Incluir en el correo</label>'
        '<label>Pérdida aceptable (CLP)<input type="number" name="perdida" min="0" step="1000"></label>'
        '<label>Capital (opcional)<input type="number" name="capital" min="0" step="10000"></label>'
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


def _cuadro(fondo: str, borde: str, rotulo: str, pie: str, clase: str, c: dict[str, str]) -> str:
    return (f'<td class="stack" width="49%" valign="top" bgcolor="{c[fondo]}" style="padding:18px;'
            f'background:{c[fondo]};border:2px solid {c[borde]};border-radius:12px;">'
            f'<p style="margin:0 0 6px 0;font-family:{F_SANS};font-size:14px;line-height:20px;font-weight:800;'
            f'text-transform:uppercase;letter-spacing:1px;color:{c[borde]};">{rotulo}</p>'
            f'<p style="margin:0;font-family:{F_DISPLAY};font-size:28px;line-height:34px;font-weight:700;'
            f'color:{c["texto_1"]};"><strong class="{clase}">Sin calcular</strong></p>'
            f'<p style="margin:6px 0 0 0;font-family:{F_SANS};font-size:14px;line-height:20px;font-weight:500;'
            f'color:{c["texto_borde"]};">{pie}</p></td>')


def _simulacion_correo(a: dict[str, Any], ejecutivo: str, c: dict[str, str]) -> str:
    """La simulación del ejecutivo: cuadro rojo (stop) y verde (objetivo) del mismo tamaño."""
    motivo = _motivo(a)
    if motivo:
        celda = _p(f'<strong style="color:{c["texto_1"]};">Sin simulación esta semana:</strong> {ih.e(motivo)}',
                   c, tam=15, margen="0")
        return _tabla(f'<tr><td bgcolor="{c["fondo"]}" style="padding:14px 16px;background:{c["fondo"]};'
                      f'border:1px solid {c["linea"]};border-radius:12px;">{celda}</td></tr>')
    f = a["fmt"]
    fuerte = lambda x: f'<strong style="color:{c["texto_1"]};">{ih.e(x)}</strong>'  # noqa: E731
    cuadros = _tabla(
        '<tr>'
        + _cuadro("fondo_baja", "baja", "Si toca el stop", f"Pérdida al llegar a {ih.e(f['stop'])}", "sim-perdida", c)
        + '<td class="stack stack-gap" width="2%" style="font-size:0;line-height:0;">&nbsp;</td>'
        + _cuadro("fondo_sube", "sube", "Si llega al objetivo", f"Ganancia al llegar a {ih.e(f['objetivo'])}",
                  "sim-ganancia", c)
        + '</tr>')
    return (
        '<table class="sim-bloque" role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">'
        '<tr><td style="padding:0;">'
        + _rotulo(f"Simulación realizada por {ih.e(ejecutivo)}", c)
        + _p(f'Objetivo 1:3 · Entrada {fuerte(f["entrada"])} · Stop {fuerte(f["stop"])} · '
             f'Objetivo {fuerte(f["objetivo"])}', c, tam=15)
        + cuadros
        + _p("", c, tam=15, margen="12px 0 0 0", clase="sim-volumen")
        + _p("Las dos cifras se muestran juntas y del mismo tamaño a propósito: el apalancamiento amplifica "
             "igual las ganancias y las pérdidas.", c, tam=14, color="texto_2", margen="6px 0 0 0")
        + '</td></tr></table>'
    )


def _bloque_correo(a: dict[str, Any], titular: str, contexto: str, dir_pedido: Path, ejecutivo: str,
                   c: dict[str, str]) -> str:
    """El bloque del activo en el correo: una fila de la tabla de 640 px, estilos en línea."""
    lec, f = a["lectura"], a["fmt"]
    color_dir = _color_direccion(lec["direccion"], c)
    niveles = cm._niveles(a)
    linea = f'border-bottom:1px solid {c["linea"]};'
    filas = "".join(
        f'<tr><td style="padding:12px 16px;font-family:{F_SANS};font-size:15px;line-height:22px;font-weight:700;'
        f'color:{c["texto_borde"]};{"" if i == len(niveles) - 1 else linea}">{ih.e(r)}</td>'
        f'<td align="right" style="padding:12px 16px;font-family:{F_SANS};font-size:17px;line-height:22px;'
        f'font-weight:800;white-space:nowrap;color:{c["texto_1"]};{"" if i == len(niveles) - 1 else linea}">'
        f'{ih.e(v)}</td></tr>' for i, (r, v) in enumerate(niveles))
    escenarios = "".join(_p(f'{ih.e(x["flecha"])} {ih.e(x["texto"])}', c, margen="0 0 8px 0")
                         for x in lec["escenarios"])
    precio = _tabla(
        '<tr><td valign="middle" style="padding:14px 20px;">'
        + _p("Precio de referencia", c, tam=14, peso=600, color="texto_2", margen="0")
        + f'<p style="margin:2px 0 0 0;font-family:{F_DISPLAY};font-size:28px;line-height:34px;font-weight:700;'
          f'color:{c["texto_1"]};white-space:nowrap;"><strong>{ih.e(f["precio"])}</strong></p></td>'
          f'<td valign="middle" align="right" style="padding:14px 20px;"><span style="display:inline-block;'
          f'padding:8px 18px;border-radius:999px;background:{color_dir};color:{c["fondo"]};font-family:{F_SANS};'
          f'font-size:14px;line-height:20px;font-weight:800;letter-spacing:1.5px;">'
          f'{ih.e(lec["direccion"].upper())}</span></td></tr>',
        estilo=f'background:{c["fondo"]};border:1px solid {c["linea"]};border-radius:12px;', fondo=c["fondo"])
    grafico = _tabla(
        f'<tr><td style="padding:6px;"><img src="{ih._data_uri(dir_pedido / a["grafico"])}" width="546" '
        f'alt="Gráfico de {ih.e(a["nombre"])}" style="display:block;border:0;width:100%;max-width:546px;'
        f'height:auto;border-radius:8px;"></td></tr>', estilo=f'border:1px solid {c["linea"]};border-radius:12px;')
    return (
        f'<tr><td class="pad" style="padding:30px 40px 0 40px;border-top:1px solid {c["linea"]};">'
        + _rotulo(f'{ih.e(a["nombre"])} · {ih.e(a["ticker_visible"])}', c)
        + f'<p style="margin:0 0 14px 0;font-family:{F_DISPLAY};font-size:22px;line-height:29px;font-weight:700;'
          f'color:{c["texto_1"]};">{ih.e(titular)}</p>'
        + precio + _separador() + grafico + _separador()
        + _p(ih.e(contexto), c)
        + _rotulo(f'Escenario de la semana · <span style="color:{color_dir};">'
                  f'{ih.e(lec["direccion"].capitalize())}</span>', c, margen="10px 0 8px 0")
        + _tabla(filas, estilo=f'background:{c["tarjeta"]};border:1px solid {c["linea"]};border-radius:12px;',
                 fondo=c["tarjeta"])
        + _separador() + escenarios
        + _p(f'⏱️ <strong style="color:{c["texto_1"]};">{ih.e(a["temporalidad"])}</strong>', c, tam=15,
             margen="4px 0 18px 0")
        + _simulacion_correo(a, ejecutivo, c)
        + _separador(26) + '</td></tr>'
    )


def _firma_correo(rotulo: str, lineas: list[str], c: dict[str, str]) -> str:
    textos = "".join(
        f'<p style="margin:0;font-family:{F_SANS};font-size:16px;line-height:23px;font-weight:{700 if i == 0 else 500};'
        f'color:{c["texto_1"] if i == 0 else c["texto_borde"]};">{ih.e(t)}</p>'
        for i, t in enumerate(x for x in lineas if x))
    return (f'<td class="stack" width="50%" valign="top" style="padding:18px 10px 0 0;">'
            f'<p style="margin:0 0 4px 0;font-family:{F_SANS};font-size:13px;line-height:20px;font-weight:700;'
            f'letter-spacing:1.4px;text-transform:uppercase;color:{c["acento"]};">{rotulo}</p>{textos}</td>')


def _marco_correo(d: dict[str, Any], ed: dict[str, Any], ejecutivo: dict[str, Any], autor,
                  c: dict[str, str]) -> str:
    """El correo sin los activos: cabecera con logo, portada, saludo, firmas y aviso.

    Los activos marcados entran en el lugar de `<!--ACTIVOS-->` al armar el correo.
    """
    cabecera = (
        f'<tr><td class="pad" bgcolor="{c["fondo"]}" style="background:{c["fondo"]};padding:24px 40px;">'
        + _tabla(f'<tr><td valign="middle"><img src="{ih._data_uri(ih.LOGO)}" width="150" alt="Grupo Inteligencia" '
                 'style="display:block;border:0;width:150px;height:auto;"></td>'
                 f'<td valign="middle" align="right" style="font-family:{F_SANS};font-size:14px;line-height:20px;'
                 f'font-weight:600;color:{c["texto_2"]};">Semana<br><span style="color:{c["texto_1"]};">'
                 f'{ih.e(d["semana"])}</span></td></tr>')
        + '</td></tr>'
        f'<tr><td bgcolor="{c["acento"]}" style="height:3px;line-height:3px;font-size:3px;background:{c["acento"]};'
        f'background-image:linear-gradient(90deg,{c["acento_azul"]},{c["acento"]});">&nbsp;</td></tr>')
    portada = (
        f'<tr><td class="pad" bgcolor="{c["tarjeta"]}" style="background:{c["tarjeta"]};'
        f'background-image:linear-gradient(135deg,{c["tarjeta"]} 0%,{c["fondo_alt"]} 100%);padding:34px 40px 32px 40px;">'
        + _rotulo("Análisis técnico de la semana", c, margen="0 0 14px 0")
        + f'<h1 class="h1" style="margin:0 0 14px 0;font-family:{F_DISPLAY};font-size:30px;line-height:37px;'
          f'font-weight:700;color:{c["texto_1"]};">{ih.e(ed["titular"])}</h1>'
        + _p(ih.e(ed["bajada"]), c, tam=17, margen="0") + '</td></tr>'
        '<tr><td class="pad" style="padding:30px 40px 30px 40px;">'
        + _p("Hola:", c, tam=17, peso=700, color="texto_1")
        + _p("Te comparto el análisis técnico de la semana, preparado por la Dirección de Análisis Técnico de "
             "Grupo Inteligencia. Es una lectura general, igual para todos.", c, tam=17, margen="0")
        + '</td></tr>')
    firmas = (
        '<tr><td class="pad" style="padding:6px 40px 0 40px;">'
        + _tabla('<tr>' + _firma_correo("Análisis", [autor.nombre, autor.cargo], c)
                 + _firma_correo("Te lo envía", [ejecutivo["nombre"], ejecutivo.get("cargo", ""),
                                                 ejecutivo.get("contacto", "")], c) + '</tr>',
                 estilo=f'border-top:1px solid {c["linea"]};')
        + '</td></tr>'
        '<tr><td class="pad" style="padding:26px 40px 32px 40px;">'
        # El fondo y el relleno van en la celda: Word ignora el relleno de un párrafo.
        + _tabla(f'<tr><td bgcolor="{c["fondo"]}" style="padding:14px 16px;background:{c["fondo"]};border-radius:10px;">'
                 + _p(ih.e(cm.AVISO_PIEZA), c, tam=14, color="texto_2", margen="0") + '</td></tr>')
        + '</td></tr>')
    return (
        f'<table id="correo-root" role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" '
        f'bgcolor="{c["fondo"]}" style="width:100%;background:{c["fondo"]};font-family:{F_SANS};">'
        '<tr><td align="center" style="padding:28px 10px;">'
        f'<table role="presentation" class="shell" width="640" cellspacing="0" cellpadding="0" border="0" '
        f'bgcolor="{c["fondo_alt"]}" style="width:640px;max-width:640px;background:{c["fondo_alt"]};'
        f'border:1px solid {c["linea"]};">'
        + cabecera + portada + '<!--ACTIVOS-->' + firmas
        + '</table></td></tr></table>'
    )


def armar(pieza: dict[str, Any], dir_pedido: Path, ejecutivo: dict[str, Any], autor, hoy: date) -> str:
    errs = es.errores(pieza)
    if errs:
        raise InformeInvalido("; ".join(errs))
    d, ed = pieza["datos"], pieza["editorial"]
    nombre_ej = ejecutivo["nombre"]
    c = paleta()
    bloques, correos, datos_js = [], [], []
    for a in d["activos"]:
        t = a["ticker"]
        lec = a["lectura"]
        escenarios = "".join(f"<li>{ih.e(x['flecha'])} {ih.e(x['texto'])}</li>" for x in lec["escenarios"])
        lamina = dir_pedido / cm.nombre_lamina(t)
        bloques.append(
            f'<section class="activo" data-ticker="{ih.e(t)}">'
            f'<header><h2>{ih.e(a["nombre"])} · {ih.e(a["ticker_visible"])}</h2>'
            f'{ih.pildora(lec["direccion"].capitalize())}</header>'
            f'<div class="analisis"><h3>{ih.e(ed["titulares"][t])}</h3>'
            f'<img src="{ih._data_uri(dir_pedido / a["grafico"])}" alt="Gráfico de {ih.e(a["nombre"])}">'
            f'<p>{ih.e(ed["contexto"][t])}</p><table class="niveles">{_filas_niveles(a)}</table>'
            f'<ul class="escenarios">{escenarios}</ul><p class="salida">{ih.e(lec["salida"])}</p>'
            f'<p class="temporalidad">⏱️ {ih.e(a["temporalidad"])} · Foto del {ih.e(a["foto"]["fecha"])}, '
            f'precio {ih.e(a["fmt"]["precio"])}</p>'
            f'<p class="firma-analisis">Análisis: {ih.e(autor.nombre)} · {ih.e(autor.cargo)}</p></div>'
            f'{_panel(a, nombre_ej)}'
            '<div class="acciones"><button type="button" class="copiar-wa">Copiar texto de WhatsApp</button>'
            + (f'<a class="descargar" download="{ih.e(lamina.name)}" href="{ih._data_uri(lamina)}">Descargar lámina</a>'
               if lamina.exists() else "")
            + '</div></section>')
        correos.append(f'<template class="correo-activo" data-ticker="{ih.e(t)}">'
                       f'{_bloque_correo(a, ed["titulares"][t], ed["contexto"][t], dir_pedido, nombre_ej, c)}</template>')
        datos_js.append({"ticker": t, "digits": a["digits"], "escenario": a["escenario"], "contrato": a["contrato"],
                         "fmt": a["fmt"], "motivo": _motivo(a), "whatsapp": cm.texto_whatsapp_base(a, ed["titulares"][t], ed["contexto"][t])})
    tokens = {
        "marco": _marco_correo(d, ed, ejecutivo, autor, c),
        "raiz": "".join(f"--{k.replace('_', '-')}:{v};" for k, v in c.items()),
        "titulo": ih.e(ed["titular"]), "logo": ih._data_uri(ih.LOGO), "semana": ih.e(d["semana"]),
        "edicion": ih.e(d["edicion"]), "titular": ih.e(ed["titular"]), "bajada": ih.e(ed["bajada"]),
        "activos": "".join(bloques), "correos": "".join(correos), "firma": ih.bloque_firma(autor, hoy),
        "aviso": ih.e(cm.AVISO_PIEZA), "ejecutivo": ih.e(nombre_ej),
        "fuentes": ih._fuentes(),
        "datos": json.dumps({"ejecutivo": nombre_ej, "cargo": ejecutivo.get("cargo", ""),
                             "contacto": ejecutivo.get("contacto", ""), "autor": cm.firma(autor),
                             "aviso": cm.AVISO_PIEZA, "titular": ed["titular"], "activos": datos_js},
                            ensure_ascii=False).replace("</", "<\\/"),
        "simulador": op.SIMULADOR_JS.read_text(encoding="utf-8").strip(),
    }
    return re.sub(r"\{\{(\w+)\}\}", lambda m: tokens[m.group(1)], PLANTILLA.read_text(encoding="utf-8"))


def guardar(pieza: dict[str, Any], dir_pedido: Path, ejecutivo: dict[str, Any], autor, hoy: date) -> Path:
    ruta = dir_pedido / f"analisis-semanal_{pieza['datos']['semana']}_{_slug(ejecutivo['nombre'])}.html"
    ruta.write_text(armar(pieza, dir_pedido, ejecutivo, autor, hoy), encoding="utf-8")
    return ruta
