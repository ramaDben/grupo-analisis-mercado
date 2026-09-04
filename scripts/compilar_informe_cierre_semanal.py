#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Compila el informe de cierre semanal en PDF A4 de 5 páginas.

**Parametrizado el 2026-09-04.** Hasta esa fecha este script era un molde de una
sola fecha: `GRAFICOS_DIR` apuntaba a `2026-08-28_cierre`, el PDF de salida
llevaba `20260828` en el nombre y los textos de análisis estaban escritos dentro
de sus 908 líneas de HTML. Correrlo una semana después regeneraba el informe de
la semana anterior, y producir el de hoy obligaba a duplicar el archivo.

Reparto de responsabilidades, el mismo de la capacitación en PPTX:

- `cierre_semanal_datos.py`   → los números, leídos del terminal AL CIERRE
- `cierre_semanal_contenido.py` → el juicio editorial de la semana
- `cierre_semanal_estilo.py`  → la hoja de estilos, sin cambios de diseño
- este archivo                → la maqueta que los junta

**El diseño no cambió**: el ejemplar del 28 de agosto ya salió al canal con este
aspecto y el estándar está aprobado. Lo que cambió es de dónde sale el contenido.

Uso:
    uv run --extra informe --extra stories --with MetaTrader5 --with pypdf \\
        python scripts/compilar_informe_cierre_semanal.py
"""

from __future__ import annotations

import base64
import html
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import cierre_semanal_contenido as C  # noqa: E402
from cierre_semanal_datos import ACTIVOS, DatosError, leer_niveles, reunir  # noqa: E402
from cierre_semanal_estilo import hoja_de_estilos  # noqa: E402

SANTIAGO = ZoneInfo("America/Santiago")
FUENTES = RAIZ / "templates" / "stories" / "fonts"
PAGINAS_TOTALES = 6

CATALOGO_FUENTES = (
    ("plus-jakarta-sans-400.woff2", "Plus Jakarta Sans", 400),
    ("plus-jakarta-sans-600.woff2", "Plus Jakarta Sans", 600),
    ("plus-jakarta-sans-700.woff2", "Plus Jakarta Sans", 700),
    ("plus-jakarta-sans-800.woff2", "Plus Jakarta Sans", 800),
    ("goldman-400.woff2", "Goldman", 400),
    ("goldman-700.woff2", "Goldman", 700),
)


def caras_de_fuente() -> str:
    reglas = []
    for archivo, familia, peso in CATALOGO_FUENTES:
        ruta = FUENTES / archivo
        if not ruta.exists():
            continue
        datos = base64.b64encode(ruta.read_bytes()).decode("ascii")
        reglas.append(
            f'@font-face{{font-family:"{familia}";font-weight:{peso};'
            f'font-style:normal;font-display:swap;'
            f'src:url(data:font/woff2;base64,{datos}) format("woff2");}}'
        )
    return "\n".join(reglas)


def imagen_embebida(ruta: Path) -> str:
    """El PNG en base64. Lanza si falta: el renderer no dibuja un sustituto."""
    if not ruta.exists():
        raise DatosError(
            f"falta el grafico {ruta.name}. Corre `cierre_semanal_datos.py` "
            "antes de compilar: el informe no sale con una ficha sin imagen."
        )
    return f"data:image/png;base64,{base64.b64encode(ruta.read_bytes()).decode('ascii')}"


def e(texto: Any) -> str:
    """Escapa el texto editorial. Va a HTML y puede traer `&` o `<`."""
    return html.escape(str(texto), quote=False)


# ─────────────────────────────────────────────────────────────────────────────
# Bloques
# ─────────────────────────────────────────────────────────────────────────────
def bloque_encabezado(pagina: int, fecha_larga: str) -> str:
    izq = C.ENCABEZADOS.get(pagina, "RESEARCH INTERMERCADO")
    return (
        '<div class="page-header">'
        f'<span class="page-header-left">{e(izq)}</span>'
        f'<span class="page-header-right">{e(fecha_larga.upper())}</span>'
        "</div>"
    )


def bloque_pie(pagina: int) -> str:
    return (
        '<div class="page-footer">'
        '<span class="page-footer-left">GRUPO INTELIGENCIA · RESEARCH &amp; ESTRATEGIA</span>'
        f'<span class="page-footer-right">PÁGINA {pagina:02d} / {PAGINAS_TOTALES:02d}</span>'
        "</div>"
    )


def bloque_tarjeta_portada(a: dict[str, Any]) -> str:
    """Una tarjeta del snapshot semanal.

    El color lo decide el signo del dato y nada más: es la convención que el
    cliente lee sin pensar, no una decisión de marca.
    """
    color = "#4ADE80" if a["sube"] else "#F87171"
    flecha = "▲" if a["sube"] else "▼"
    nota = C.NOTAS_PORTADA.get(a["slug"], "")
    return (
        '<div class="cover-card">'
        f'<div class="cover-card-header"><span>{a["emoji"]} {e(a["rotulo"])}</span>'
        f'<span style="color:{color};">{flecha} {e(a["var_txt"])}</span></div>'
        f'<div class="cover-card-price">{e(a["moneda"])}{e(a["actual_txt"])}</div>'
        f'<div class="cover-card-driver">{e(nota)}</div>'
        "</div>"
    )


def pagina_portada(datos: dict[str, Any]) -> str:
    tarjetas = "".join(bloque_tarjeta_portada(a) for a in datos["activos"])
    return f"""
<div class="a4-page cover-page">
    <div class="cover-bg-glow"></div>
    <div class="cover-content">
        <div class="cover-top">
            <div class="cover-logo">
                <div class="cover-logo-icon">GI</div>
                <div class="cover-logo-text">GRUPO INTELIGENCIA</div>
            </div>
            <div class="cover-badge">INFORME OFICIAL · CIERRE SEMANAL</div>
        </div>

        <div class="cover-hero">
            <div class="cover-kicker">{e(C.KICKER)}</div>
            <h1 class="cover-title">{e(C.TITULO)} <span>{e(C.TITULO_ACENTO)}</span></h1>
            <p class="cover-subtitle">{e(C.BAJADA)}</p>
        </div>

        <div style="background: rgba(11, 35, 29, 0.8); border: 1px solid rgba(80, 192, 168, 0.35); border-radius: 10px; padding: 14px 18px; margin-bottom: 14px;">
            <div style="font-family:'Goldman',sans-serif; font-size:12px; font-weight:700; color:#50C0A8; letter-spacing:0.06em; margin-bottom:6px;">01. RESUMEN EJECUTIVO DE LA SEMANA</div>
            <p style="font-size:10px; line-height:1.55; color:#E2E8F0; text-align:justify;">{e(C.RESUMEN_EJECUTIVO)}</p>
        </div>

        <div>
            <div style="font-family:'Goldman',sans-serif; font-size:11px; font-weight:700; color:#3E91AF; letter-spacing:0.08em; margin-bottom:6px;">SNAPSHOT SEMANAL DE ACTIVOS CLAVE (CIERRE MT5)</div>
            <div class="cover-grid">{tarjetas}</div>
        </div>

        <div style="border-top:1px solid rgba(255,255,255,0.18); padding-top:10px; display:flex; justify-content:space-between; align-items:center; font-size:9.5px; color:#94A3B8;">
            <div>FECHA: <strong style="color:#FFFFFF;">{e(datos["fecha_larga"])}</strong> · ANALISTA: <strong style="color:#FFFFFF;">Área de Research &amp; Estrategia</strong></div>
            <div style="font-family:'Goldman',sans-serif; color:#50C0A8; font-weight:700;">PÁGINA 01 / {PAGINAS_TOTALES:02d}</div>
        </div>
    </div>
</div>"""


def bloque_tabla_curva(datos: dict[str, Any]) -> str:
    filas = []
    for f in datos["filas_curva"]:
        diag = C.DIAGNOSTICO_CURVA.get(f["codigo"], "")
        filas.append(
            "<tr>"
            f'<td><strong>{e(f["nombre"])}</strong></td>'
            f'<td><strong>{e(f["nivel"])}</strong></td>'
            f'<td>{e(f["d1"])}</td>'
            f'<td><strong>{e(f["d5"])}</strong></td>'
            f'<td>{e(diag)}</td>'
            f'<td style="white-space:nowrap;">{e(f["fecha"])}</td>'
            "</tr>"
        )
    return f"""
<table class="table-custom">
    <thead><tr>
        <th>Instrumento / Tramo Soberano</th>
        <th>Nivel</th>
        <th>1 día</th>
        <th>Semana</th>
        <th>Lectura &amp; Diagnóstico</th>
        <th>Dato al</th>
    </tr></thead>
    <tbody>{"".join(filas)}</tbody>
</table>"""


def bloque_ficha(a: dict[str, Any], capas: dict[str, str], img: str) -> str:
    clase_badge = "badge-up" if a["sube"] else "badge-down"
    flecha = "▲" if a["sube"] else "▼"
    unidad = f" · {a['unidad'].strip()}" if a["unidad"].strip() else ""
    return f"""
<div class="asset-card">
    <div class="asset-card-header">
        <span class="asset-card-title">{a['emoji']} {e(a['nombre'])} ({e(a['ticker'])} · Cierre: {e(a['moneda'])}{e(a['actual_txt'])}{e(unidad)})</span>
        <span class="asset-badge {clase_badge}">{flecha} {e(a['var_txt'])} SEMANAL</span>
    </div>
    <img class="asset-chart-img" src="{img}" alt="Grafico diario de {e(a['nombre'])}" />
    <div class="three-layers">
        <div class="layer-item">
            <span class="layer-label">📌 Qué pasó esta semana:</span>
            <span>{e(capas['pasando'])}</span>
        </div>
        <div class="layer-item">
            <span class="layer-label">💡 Qué significa para ti:</span>
            <span>{e(capas['significa'])}</span>
        </div>
        <div class="layer-item layer-prohibited">
            <span class="layer-label">🚫 Qué NO operar la próxima semana:</span>
            <span>{e(capas['prohibido'])}</span>
        </div>
    </div>
</div>"""


def pagina_contenido(
    pagina: int, datos: dict[str, Any], fichas: dict[str, str], titulos: list[str]
) -> str:
    slugs = C.PAGINAS_ACTIVOS[pagina]
    cuerpo = []
    if pagina == 2:
        cuerpo.append('<div class="section-title">02. Curva Soberana de EE.UU. y Transmisión de Tasas</div>')
        cuerpo.append(f'<p class="body-p">{e(C.INTRO_CURVA)}</p>')
        cuerpo.append(bloque_tabla_curva(datos))
        cuerpo.append(f'<p class="body-p" style="font-size:8.5px; color:#64748B;">{e(C.NOTA_CURVA_REZAGO)}</p>')
    if titulos:
        cuerpo.append(f'<div class="section-title">{e(titulos.pop(0))}</div>')
    cuerpo.extend(fichas[s] for s in slugs)
    return f"""
<div class="a4-page">
    <div>
        {bloque_encabezado(pagina, datos["fecha_larga"])}
        {"".join(cuerpo)}
    </div>
    {bloque_pie(pagina)}
</div>"""


def pagina_escenarios(datos: dict[str, Any]) -> str:
    tarjetas = []
    for esc in C.ESCENARIOS:
        vinetas = "".join(f"<li>{e(b)}</li>" for b in esc["bullets"])
        tarjetas.append(
            f'<div class="scenario-card scenario-{esc["clase"]}">'
            f'<div class="scenario-title">{esc["emoji"]} {e(esc["titulo"])} '
            f'· PROBABILIDAD {esc["prob"]}%</div>'
            f'<ul class="scenario-bullets">{vinetas}</ul></div>'
        )

    filas = "".join(
        "<tr>"
        f'<td><strong>{e(r["cuando"])}</strong></td>'
        f'<td><strong>{e(r["evento"])}</strong></td>'
        f'<td>{e(r["fuente"])}</td>'
        f'<td>{e(r["impacto"])}</td>'
        "</tr>"
        for r in C.RADAR
    )

    return f"""
<div class="a4-page">
    <div>
        {bloque_encabezado(6, datos["fecha_larga"])}
        <div class="section-title">04. Escenarios para la Próxima Semana</div>
        {"".join(tarjetas)}

        <div class="section-title" style="margin-top:10px;">🗓️ Radar Clave de la Próxima Semana</div>
        <table class="table-custom" style="margin-bottom:8px;">
            <thead><tr>
                <th>Fecha y hora (Chile)</th>
                <th>Evento</th>
                <th>Fuente oficial</th>
                <th>Por qué importa</th>
            </tr></thead>
            <tbody>{filas}</tbody>
        </table>

        <div class="highlight-box">{e(C.AVISO_HORARIO)}</div>

        <div style="background:#04100D; color:#C1E5E4; border-radius:8px; padding:12px 16px; border:1px solid rgba(80,192,168,0.25); margin-top:8px;">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(255,255,255,0.12); padding-bottom:6px; margin-bottom:8px;">
                <span style="font-family:'Goldman',sans-serif; font-size:11px; font-weight:700; color:#50C0A8;">05. FUENTES OFICIALES Y AVISO LEGAL</span>
                <span style="font-size:8.5px; color:#94A3B8;">GRUPO INTELIGENCIA RESEARCH</span>
            </div>
            <p style="font-size:8.5px; line-height:1.45; color:#94A3B8; text-align:justify;">{e(C.AVISO_LEGAL)}</p>
        </div>
    </div>
    {bloque_pie(6)}
</div>"""


def construir_html(datos: dict[str, Any], graficos: Path) -> str:
    por_slug = {a["slug"]: a for a in datos["activos"]}
    fichas: dict[str, str] = {}
    for a in datos["activos"]:
        niveles = leer_niveles(a["ticker"])
        capas = C.capas_de(a["slug"], a, niveles)
        fichas[a["slug"]] = bloque_ficha(a, capas, imagen_embebida(graficos / f"{a['slug']}.png"))

    faltan = set(por_slug) - set(fichas)
    if faltan:
        raise DatosError(f"sin ficha para: {sorted(faltan)}")

    titulos = ["03. Análisis Técnico y Transmisión por Activo"]
    paginas = [pagina_portada(datos)]
    for n in (2, 3, 4, 5):
        paginas.append(pagina_contenido(n, datos, fichas, titulos))
    paginas.append(pagina_escenarios(datos))

    css = hoja_de_estilos(caras_de_fuente())
    return (
        '<!DOCTYPE html>\n<html lang="es">\n<head>\n<meta charset="utf-8">\n'
        "<title>Informe de Cierre Semanal · Grupo Inteligencia</title>\n"
        f"<style>{css}</style>\n</head>\n<body>\n{''.join(paginas)}\n</body>\n</html>\n"
    )


def _medir_desbordes(pagina: Any) -> list[dict[str, Any]]:
    """Cuanto se pasa cada pagina de su alto util, medido en el DOM.

    Existe porque el control de "cuantas paginas salieron" **no detecta el
    desborde dentro de una pagina**. El 2026-09-04 la pagina 4 llevaba cuatro
    fichas, la del yen no cabia y desaparecio completa: `.a4-page` mide 1123 px
    con `overflow: hidden`, asi que lo que sobra no se recorta a la vista, se
    borra. El PDF salio con las cinco paginas esperadas y el informe se leia
    como completo.

    Se mide, no se estima, que es la misma regla del folleto de capacitacion.
    """
    return pagina.evaluate(
        """() => Array.from(document.querySelectorAll('.a4-page')).map((el, i) => {
            // Solo los hijos EN FLUJO: la portada lleva una capa de brillo con
            // `position: absolute` que no ocupa espacio y falsea la suma.
            const hijos = Array.from(el.children).filter(
                c => getComputedStyle(c).position !== 'absolute'
            );
            // `scrollHeight` del contenedor no sirve: `.a4-page` es flex con
            // `space-between`, asi que los hijos se COMPRIMEN para caber y el
            // valor queda clavado en el alto de la pagina. El alto natural es
            // el de cada hijo por separado.
            const natural = hijos.reduce((suma, c) => suma + c.scrollHeight, 0);
            const cs = getComputedStyle(el);
            const util = el.clientHeight
                - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
            return {
                pagina: i + 1,
                util: Math.round(util),
                contenido: Math.round(natural),
            };
        })"""
    )

def compilar(fecha: str | None = None) -> Path:
    from playwright.sync_api import sync_playwright
    from pypdf import PdfReader

    hoy = fecha or datetime.now(tz=SANTIAGO).strftime("%Y-%m-%d")
    carpeta = RAIZ / "data" / "informes" / f"{hoy}_cierre"
    graficos = carpeta / "graficos"
    salida = carpeta / f"informe_cierre_semanal_{hoy.replace('-', '')}_GI.pdf"

    print(f"Fecha    : {hoy}")
    datos = reunir(destino_graficos=graficos)
    html_doc = construir_html(datos, graficos)
    print(f"HTML     : {len(html_doc) / 1024:.1f} KB")

    with sync_playwright() as pw:
        navegador = pw.chromium.launch()
        pagina = navegador.new_page(viewport={"width": 794, "height": 1123})
        pagina.set_content(html_doc, wait_until="load")
        pagina.emulate_media(media="print")
        medidas = _medir_desbordes(pagina)
        pdf = pagina.pdf(
            format="A4", print_background=True,
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
        )
        navegador.close()

    carpeta.mkdir(parents=True, exist_ok=True)
    salida.write_bytes(pdf)

    paginas = len(PdfReader(salida).pages)
    print(f"Salida   : {salida.relative_to(RAIZ)}")
    print(f"Tamano   : {len(pdf) / 1024:.1f} KB")
    print(f"Paginas  : {paginas}")

    # Las paginas son fijas y con `overflow: hidden`: si salen mas o menos de
    # cinco, algo desbordo o se recorto, y un informe recortado se lee como
    # completo. Es el mismo control que el compilador del manual.
    # Tolerancia de 2 px: el redondeo de subpixeles del layout no es un desborde.
    pasadas = [m for m in medidas if m["contenido"] > m["util"] + 2]
    print("Altos    : " + " . ".join(
        f"p{m['pagina']} {m['contenido']}/{m['util']}" for m in medidas
    ))

    if paginas != PAGINAS_TOTALES:
        raise SystemExit(
            f"El PDF salio con {paginas} paginas y el formato son {PAGINAS_TOTALES}."
        )
    if pasadas:
        detalle = ", ".join(
            f"pagina {m['pagina']} se pasa {m['contenido'] - m['util']} px" for m in pasadas
        )
        raise SystemExit(
            f"Hay contenido que no cabe y se perderia sin aviso: {detalle}. "
            "Mover una ficha a otra pagina en `PAGINAS_ACTIVOS` o acortar el texto."
        )
    print(f"\nOK: informe completo en {PAGINAS_TOTALES} paginas, sin desbordes.")
    return salida


if __name__ == "__main__":
    try:
        compilar()
    except (DatosError, KeyError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
