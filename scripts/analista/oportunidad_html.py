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


MOTIVO_SIN_CONTRATO = "no hay datos de contrato de la cuenta para simular este activo"


def _motivo(a: dict[str, Any]) -> str | None:
    """Por qué el activo no se simula (None si se simula). Sin contrato no hay con qué calcular."""
    return a["escenario"]["motivo"] or (None if a["contrato"] else MOTIVO_SIN_CONTRATO)


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


def _bloque_correo(a: dict[str, Any], titular: str, contexto: str, dir_pedido: Path) -> str:
    """El bloque del activo en el correo: tablas de 640 px, estilos en línea (Outlook clásico)."""
    fuente = "Segoe UI,Arial,Helvetica,sans-serif"
    filas = "".join(
        f'<tr><td style="padding:6px 0;color:#9aa4b2;font:600 13px {fuente}">{ih.e(r)}</td>'
        f'<td style="padding:6px 0;text-align:right;color:#ffffff;font:700 15px {fuente}">{ih.e(v)}</td></tr>'
        for r, v in cm._niveles(a))
    escenarios = "".join(
        f'<tr><td style="padding:4px 24px;color:#d6dde6;font:500 14px/21px {fuente}">'
        f'{ih.e(x["flecha"])} {ih.e(x["texto"])}</td></tr>' for x in a["lectura"]["escenarios"])
    return (
        '<table role="presentation" width="640" cellpadding="0" cellspacing="0" border="0" bgcolor="#16202b" '
        'style="width:640px;background:#16202b">'
        f'<tr><td style="padding:18px 24px 6px;color:#50C0A8;font:700 13px {fuente}">'
        f'{ih.e(a["nombre"])} · {ih.e(a["ticker_visible"])}</td></tr>'
        f'<tr><td style="padding:0 24px;color:#ffffff;font:700 20px/26px {fuente}">{ih.e(titular)}</td></tr>'
        f'<tr><td style="padding:12px 24px"><img src="{ih._data_uri(dir_pedido / a["grafico"])}" width="592" '
        f'style="width:592px;display:block;border:0" alt="{ih.e(a["nombre"])}"></td></tr>'
        f'<tr><td style="padding:0 24px 8px;color:#d6dde6;font:500 15px/23px {fuente}">{ih.e(contexto)}</td></tr>'
        f'<tr><td style="padding:8px 24px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'border="0">{filas}</table></td></tr>'
        f'{escenarios}'
        f'<tr><td style="padding:8px 24px 0;color:#9aa4b2;font:500 13px {fuente}">⏱️ {ih.e(a["temporalidad"])}</td></tr>'
        f'<tr><td class="sim-correo" style="padding:8px 24px 18px;color:#d6dde6;font:500 14px/21px {fuente}"></td></tr>'
        '</table>'
    )


def armar(pieza: dict[str, Any], dir_pedido: Path, ejecutivo: dict[str, Any], autor, hoy: date) -> str:
    errs = es.errores(pieza)
    if errs:
        raise InformeInvalido("; ".join(errs))
    d, ed = pieza["datos"], pieza["editorial"]
    nombre_ej = ejecutivo["nombre"]
    bloques, correos, datos_js = [], [], []
    for a in d["activos"]:
        t = a["ticker"]
        lec = a["lectura"]
        escenarios = "".join(f"<li>{ih.e(x['flecha'])} {ih.e(x['texto'])}</li>" for x in lec["escenarios"])
        lamina = dir_pedido / f"lamina_{t.lower()}.png"
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
                       f'{_bloque_correo(a, ed["titulares"][t], ed["contexto"][t], dir_pedido)}</template>')
        datos_js.append({"ticker": t, "digits": a["digits"], "escenario": a["escenario"], "contrato": a["contrato"],
                         "fmt": a["fmt"], "motivo": _motivo(a), "whatsapp": cm.texto_whatsapp_base(a, ed["titulares"][t], ed["contexto"][t])})
    tokens = {
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
