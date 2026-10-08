"""`pieza.json` → HTML autocontenido para el analista y, si se pidió, para su trader.

La maqueta es nuestra y fija: cabecera, franja, lema y pie del evergreen GI, y el
cuerpo con la legibilidad de la guía USD/CLP. agy solo aportó los textos, que
entran escapados: nada de lo que escribió puede convertirse en etiqueta.

El archivo no depende de nada externo (estilos, fuentes, logo e imágenes van
adentro), porque el analista lo reenvía y el trader lo abre sin conexión.
"""
from __future__ import annotations

import base64
import html
import re
import unicodedata
from pathlib import Path
from typing import Any

from analista import RAIZ
from analista import esquema as es

DIR_PLANTILLAS = RAIZ / "templates" / "informes_analista"
MARCA_CSS = RAIZ / "templates" / "stories" / "marca.css"
LOGO = RAIZ / "templates" / "stories" / "assets" / "LOGO Blanco.png"

TRADER_GENERICO = "Inversionista"


class InformeInvalido(ValueError):
    """La pieza no pasó el esquema; el mensaje lista cada problema."""


def e(texto: Any) -> str:
    return html.escape(str(texto), quote=True)


def slug(texto: str) -> str:
    plano = unicodedata.normalize("NFKD", texto)
    plano = "".join(c for c in plano if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "_", plano).strip("_")


def _data_uri(ruta: Path) -> str:
    tipo = "image/png" if ruta.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{tipo};base64,{base64.b64encode(ruta.read_bytes()).decode('ascii')}"


def parrafos(texto: str) -> str:
    bloques = [b.strip() for b in re.split(r"\n\s*\n", texto) if b.strip()]
    return "\n".join(f"<p>{e(b)}</p>" for b in bloques)


def vinetas(texto: str) -> str:
    lineas = [ln.strip(" •-*\t") for ln in texto.splitlines() if ln.strip(" •-*\t")]
    return "<ul>" + "".join(f"<li>{e(ln)}</li>" for ln in lineas) + "</ul>"


def figura(dir_pedido: Path, archivo: str | None, pie: str = "") -> str:
    if not archivo:
        return ""
    ruta = dir_pedido / archivo
    if not ruta.exists():
        raise InformeInvalido(f"falta la imagen {archivo}: la pieza no sale sin su gráfico")
    leyenda = f"<figcaption>{e(pie)}</figcaption>" if pie else ""
    return f'<figure class="figura"><img src="{_data_uri(ruta)}" alt="{e(pie)}">{leyenda}</figure>'


def capa(rotulo: str, texto: str, clase: str = "") -> str:
    return (
        f'<div class="capa {clase}"><div class="capa-rotulo">{e(rotulo)}</div>'
        f"{parrafos(texto)}</div>"
    )


def pildora(direccion: str) -> str:
    return f'<span class="direccion {slug(direccion)}">{e(direccion.upper())}</span>'


def tabla(columnas: list[str], filas: list[list[str]], cifras: set[int] | None = None) -> str:
    cifras = cifras or set()
    cab = "".join(f"<th>{e(c)}</th>" for c in columnas)
    cuerpo = ""
    for fila in filas:
        celdas = "".join(
            f'<td class="cifra">{c}</td>' if i in cifras else f"<td>{c}</td>"
            for i, c in enumerate(fila)
        )
        cuerpo += f"<tr>{celdas}</tr>"
    return f'<table class="tabla"><thead><tr>{cab}</tr></thead><tbody>{cuerpo}</tbody></table>'


def h2(numero: int, titulo: str) -> str:
    return f'<h2><span class="numero">{numero:02d}</span>{e(titulo)}</h2>'


# ───────────────────────────────────────────────────────────── cuerpos por pieza


def cuerpo_activo(p: dict[str, Any], dir_pedido: Path) -> str:
    d, ed = p["datos"], p["editorial"]
    escenarios = "".join(f"<li>{e(s)}</li>" for s in d["escenarios"])
    return "\n".join([
        '<div class="resumen">'
        f"<p>🎯 Activo: <strong>{e(d['nombre'])} ({e(d['ticker_visible'])})</strong></p>"
        f"<p>📌 Nivel a vigilar: <strong>{e(d['nivel_vigilar'])}</strong></p>"
        f"<p>⚡ Qué esperar: {e(d['que_esperar'])}</p></div>",
        h2(1, "Lectura del día"),
        f"<p>{pildora(d['direccion'])}</p>",
        parrafos(ed["lectura"]),
        figura(dir_pedido, p["imagenes"].get("principal"), d.get("pie_imagen", "")),
        h2(2, "Qué mueve al activo"),
        '<div class="dos-columnas">'
        f'<div class="caja caja-alza"><div class="caja-titulo">⬆️ Qué lo empuja al alza</div>{vinetas(ed["empuja_alza"])}</div>'
        f'<div class="caja caja-baja"><div class="caja-titulo">⬇️ Qué lo empuja a la baja</div>{vinetas(ed["empuja_baja"])}</div>'
        "</div>",
        h2(3, "Escenarios"),
        f'<ul class="escenarios">{escenarios}</ul>',
        f'<p class="temporalidad">⏱️ <strong>Temporalidad:</strong> {e(d["temporalidad"])}</p>',
        f'<p class="temporalidad">💡 {e(d["por_que_temporalidad"])}</p>' if d.get("por_que_temporalidad") else "",
        capa("Qué NO hacer", ed["que_no_hacer"], "no-hacer"),
    ])


def _estado(ev: dict[str, Any]) -> str:
    if ev.get("estado") == "salio":
        return '<span class="estado-salio">✅ YA SALIÓ</span>'
    if ev.get("estado") == "pendiente":
        return '<span class="estado-proximo">⏳ SIN CIFRA AÚN</span>'
    return '<span class="estado-proximo">🕐 PRÓXIMO</span>'


def cuerpo_calendario(p: dict[str, Any], dir_pedido: Path) -> str:
    d, ed = p["datos"], p["editorial"]
    filas = [
        [e(ev.get("dia", "")), e(ev["hora"]), e(ev["pais"]), e(ev["evento"]),
         e(ev.get("anterior") or "·"), e(ev.get("esperado") or "·"), e(ev.get("actual") or "·"), _estado(ev)]
        for ev in d["eventos"]
    ]
    columnas = ["Día", "Hora Chile", "País", "Dato", "Anterior", "Esperado", "Actual", "Estado"]
    if d.get("alcance") == "hoy":
        columnas, filas = columnas[1:], [f[1:] for f in filas]
    explicaciones = "".join(
        f'<div class="explicacion"><strong>{e(ev["evento"])} · {e(ev["hora"])}</strong>'
        f'{parrafos(ed["explicaciones"][ev["id"]])}</div>'
        for ev in d["eventos"] if ev["id"] in ed.get("explicaciones", {})
    )
    return "\n".join([
        h2(1, "Lo que importa"),
        parrafos(ed["lectura"]),
        figura(dir_pedido, p["imagenes"].get("principal"), d.get("pie_imagen", "")),
        h2(2, "Agenda"),
        tabla(columnas, filas, cifras=set(range(len(columnas) - 4, len(columnas) - 1))),
        h2(3, "Qué significa cada dato") if explicaciones else "",
        explicaciones,
    ])


def cuerpo_dato(p: dict[str, Any], dir_pedido: Path) -> str:
    d, ed = p["datos"], p["editorial"]
    filas = [
        [e(ev["evento"]), e(ev["hora"]), e(ev.get("actual") or "·"), e(ev.get("esperado") or "·"),
         e(ev.get("anterior") or "·"), e(ev.get("veredicto") or "·")]
        for ev in d["eventos"]
    ]
    movimientos = [
        [e(m["nombre"]), e(m["desde"]), e(m["ahora"]), e(m["lectura"])] for m in d.get("movimientos", [])
    ]
    rotulo_hecho = "El hecho" if d["modo"] == "resultado" else "Qué se espera"
    return "\n".join([
        f'<div class="resumen"><p>{e(d["resumen"])}</p></div>',
        figura(dir_pedido, p["imagenes"].get("principal"), d.get("pie_imagen", "")),
        h2(1, "Las cifras"),
        tabla(["Dato", "Hora Chile", "Actual", "Esperado", "Anterior", "Veredicto"], filas, cifras={2, 3, 4}),
        h2(2, "Lectura en tres capas"),
        capa(rotulo_hecho, ed["que_paso"]),
        capa("Qué significa", ed["que_significa"]),
        capa("Qué NO hacer", ed["que_no_hacer"], "no-hacer"),
        h2(3, "Impacto por activo"),
        vinetas(ed["impacto"]),
        tabla(["Activo", "Antes del dato", "Ahora", "Lectura"], movimientos, cifras={1, 2}) if movimientos else "",
        f'<p class="temporalidad">⏱️ <strong>Temporalidad del impacto:</strong> {e(d["temporalidad"])}</p>',
    ])


def cuerpo_jornada(p: dict[str, Any], dir_pedido: Path) -> str:
    d, ed = p["datos"], p["editorial"]
    bloques = []
    for a in d["activos"]:
        bloques.append(
            '<section class="bloque-activo">'
            f'<h2>{e(a["nombre"])} {pildora(a["direccion"])}</h2>'
            f'<p class="temporalidad">Precio {e(a["precio"])} · Soporte {e(a["soporte"])} · Resistencia {e(a["resistencia"])}</p>'
            f'{figura(dir_pedido, p["imagenes"].get(a["ticker"]), a.get("pie_imagen", ""))}'
            f'{parrafos(ed["por_activo"][a["ticker"]])}</section>'
        )
    curva = d.get("curva") or []
    return "\n".join([
        h2(1, "Panorama"),
        parrafos(ed["lectura"]),
        *bloques,
        h2(2, "Curva de tasas de EE.UU.") if curva else "",
        tabla(["Plazo", "Rendimiento", "Cambio 1 día", "Cambio 5 días"],
              [[e(c) for c in fila] for fila in curva], cifras={1, 2, 3}) if curva else "",
        capa("Qué NO hacer", ed["que_no_hacer"], "no-hacer"),
    ])


CUERPOS = {
    "activo": cuerpo_activo,
    "calendario": cuerpo_calendario,
    "dato": cuerpo_dato,
    "jornada": cuerpo_jornada,
}


# ───────────────────────────────────────────────────────────── armado


def _estilos_inline(base: str) -> str:
    # Sin comentarios: documentan el repo, no el informe, y uno de marca.css cita
    # un <link> que en el archivo entregado parecería una dependencia externa.
    def sin_comentarios(css: str) -> str:
        return re.sub(r"/\*.*?\*/", "", css, flags=re.S)

    marca = sin_comentarios(MARCA_CSS.read_text(encoding="utf-8"))
    propio = sin_comentarios((DIR_PLANTILLAS / "informe.css").read_text(encoding="utf-8"))
    base = base.replace('<link rel="stylesheet" href="../stories/marca.css">', f"<style>{marca}</style>")
    return base.replace('<link rel="stylesheet" href="informe.css">', f"<style>{propio}</style>")


def _fuentes() -> str:
    from guia_usdclp.estilos import caras_de_fuente

    return caras_de_fuente()


BARRA = """<div class="barra no-imprimir">
  <label for="in-trader">Trader</label><input id="in-trader" value="" placeholder="Nombre del trader">
  <label for="in-asesor">Asesor</label><input id="in-asesor" value="{asesor}">
  <button type="button" id="btn-guardar">Guardar versión del trader</button>
  <button type="button" onclick="window.print()">Imprimir o PDF</button>
</div>"""

# Arma la versión dedicada en el navegador: copia el documento, fija los nombres,
# quita la barra y este script, y lo descarga. No hay servidor ni red de por medio.
SCRIPT = """<script>
(function () {
  var base = %s;
  var trader = document.getElementById('in-trader');
  var asesor = document.getElementById('in-asesor');
  var lblT = document.getElementById('lbl-trader');
  var lblA = document.getElementById('lbl-asesor');
  function sync() {
    lblT.textContent = trader.value.trim() || %s;
    lblA.textContent = asesor.value.trim() || asesor.defaultValue;
  }
  trader.addEventListener('input', sync);
  asesor.addEventListener('input', sync);
  document.getElementById('btn-guardar').addEventListener('click', function () {
    sync();
    var copia = document.documentElement.cloneNode(true);
    copia.querySelectorAll('.no-imprimir, script').forEach(function (n) { n.remove(); });
    var html = '<!DOCTYPE html>\\n' + copia.outerHTML;
    var nombre = (trader.value.trim() || 'trader').normalize('NFD')
      .replace(/[\\u0300-\\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '_');
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([html], {type: 'text/html;charset=utf-8'}));
    a.download = base + '_' + nombre + '.html';
    a.click();
  });
})();
</script>"""


def armar(
    pieza: dict[str, Any],
    dir_pedido: Path,
    analista: dict[str, Any],
    trader: str | None = None,
    nombre_base: str = "informe",
) -> str:
    """HTML completo. Sin `trader` es la versión genérica, con barra para personalizar."""
    errs = es.errores(pieza)
    if errs:
        raise InformeInvalido("; ".join(errs))

    from cierre_semanal_contenido import AVISO_LEGAL

    tipo = pieza["orden"]["pieza"]
    d, ed = pieza["datos"], pieza["editorial"]
    generica = trader is None
    asesor = analista["nombre"]
    contacto = " · ".join(x for x in (analista.get("cargo"), analista.get("contacto")) if x)
    tokens = {
        "titulo_documento": e(ed["titular"]),
        "fuentes": _fuentes(),
        "logo": _data_uri(LOGO),
        "chip": e(d["chip"]),
        "titular": e(ed["titular"]),
        "bajada": e(ed["bajada"]),
        "trader": e(trader or TRADER_GENERICO),
        "asesor": e(asesor),
        "rotulo_referencia": e(d["rotulo_referencia"]),
        "referencia": e(d["referencia"]),
        "edicion": e(d["edicion"]),
        "cuerpo": CUERPOS[tipo](pieza, dir_pedido),
        "aviso_legal": e(AVISO_LEGAL),
        "contacto": e(f"{asesor} · {contacto}" if contacto else asesor),
        "barra": BARRA.format(asesor=e(asesor)) if generica else "",
        "script": SCRIPT % (repr(nombre_base), repr(TRADER_GENERICO)) if generica else "",
    }
    salida = _estilos_inline((DIR_PLANTILLAS / "base.html").read_text(encoding="utf-8"))
    # Reemplazo en una sola pasada: un valor que contenga "{{x}}" no vuelve a expandirse.
    return re.sub(r"\{\{(\w+)\}\}", lambda m: tokens[m.group(1)], salida)


def guardar(
    pieza: dict[str, Any],
    dir_pedido: Path,
    analista: dict[str, Any],
    trader: str | None,
    nombre_base: str,
) -> list[Path]:
    """Escribe la genérica y, si hay trader, la dedicada. Devuelve las rutas."""
    rutas = []
    generica = dir_pedido / f"{nombre_base}.html"
    generica.write_text(armar(pieza, dir_pedido, analista, None, nombre_base), encoding="utf-8")
    rutas.append(generica)
    if trader:
        dedicada = dir_pedido / f"{nombre_base}_{slug(trader)}.html"
        dedicada.write_text(armar(pieza, dir_pedido, analista, trader, nombre_base), encoding="utf-8")
        rutas.append(dedicada)
    return rutas
