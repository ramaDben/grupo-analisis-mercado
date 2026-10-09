"""`pieza.json` → HTML autocontenido: un análisis general, igual para todos.

La maqueta es nuestra y fija: cabecera, franja, lema y pie del evergreen GI, y el
cuerpo con la legibilidad de la guía USD/CLP. agy solo aportó los textos, que
entran escapados: nada de lo que escribió puede convertirse en etiqueta.

El archivo no depende de nada externo (estilos, fuentes, logo e imágenes van
adentro), porque el analista lo reenvía tal cual y quien lo recibe lo abre sin
conexión. No se personaliza: nadie en GI está inscrito como asesor de inversión,
y un informe con el nombre del cliente se acerca a una recomendación personalizada.
"""
from __future__ import annotations

import base64
import html
import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any

from analista import RAIZ
from analista import autor as au
from analista import esquema as es

DIR_PLANTILLAS = RAIZ / "templates" / "informes_analista"
MARCA_CSS = RAIZ / "templates" / "stories" / "marca.css"
LOGO = RAIZ / "templates" / "stories" / "assets" / "LOGO Blanco.png"

FRASE_GENERAL = ("Análisis general de mercado, idéntico para todos sus destinatarios. "
                 "No es asesoría de inversión ni considera el perfil de quien lo lee.")

# Reemplaza la estadística en el foco técnico: protege igual, sin una cifra que
# sin su línea base insinúe una ventaja (decisión del director, 2026-10-09).
FRASE_ESCENARIO = ("Un escenario técnico no anticipa el resultado: puede cumplirse o invalidarse, "
                   "y por eso siempre trae su nivel de invalidación.")


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


def cuerpo_oportunidad(p: dict[str, Any], dir_pedido: Path) -> str:
    """El foco técnico del día: el cuerpo del activo, con su transparencia y sin estadística."""
    s = p["datos"]["seleccion"]
    transparencia = (f'<p class="transparencia">Elegido por el escáner de Grupo Inteligencia entre '
                     f'{e(s["evaluados"])} activos, el {e(s["fecha"])} a las {e(s["hora"])} (hora de Chile).</p>')
    return transparencia + "\n" + cuerpo_activo(p, dir_pedido, foco=True)


def cuerpo_activo(p: dict[str, Any], dir_pedido: Path, foco: bool = False) -> str:
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
        h2(4, "Plan de escenarios") if d.get("plan") else "",
        seccion_plan(d["plan"], con_estadistica=not foco) if d.get("plan") else "",
        capa("Qué NO hacer", ed["que_no_hacer"], "no-hacer"),
        # El foco no imprime la tabla de tasas: trae "%" y el prospecto no ve porcentajes.
        "" if foco else _tabla_tasas(d.get("contexto", {}).get("curva_tasas") or [], 5 if d.get("plan") else 4),
    ])


def seccion_plan(plan: dict[str, Any], con_estadistica: bool = True) -> str:
    """El plan que escribió Python: gatillo, invalidación, recorrido, historia y estado.

    Sin estadística (foco técnico) la historia se reemplaza por `FRASE_ESCENARIO`.
    """
    if not plan.get("hay_plan"):
        return f'<div class="plan plan-vacio"><p>{e(plan.get("motivo", ""))}</p></div>'
    historia = (("Qué dice la historia", plan["estadistica"]) if con_estadistica
                else ("Antes de leerlo", FRASE_ESCENARIO))
    filas = [("Gatillo", plan["gatillo"]), ("Invalidación", plan["invalidacion"]),
             ("Recorrido", plan["recorrido"]), historia, ("Estado", plan["estado"])]
    cuerpo = "".join(
        f'<div class="plan-fila"><div class="plan-rotulo">{e(r)}</div><p>{e(t)}</p></div>' for r, t in filas
    )
    return f'<div class="plan"><p>{pildora(plan["sesgo"])}</p>{cuerpo}</div>'


def _tabla_tasas(curva: list[list[str]], numero: int) -> str:
    """Las tasas que el texto pudo citar, a la vista: una cifra citada que el lector no ve
    le pide confiar en un número que no puede comprobar."""
    if not curva:
        return ""
    return h2(numero, "Tasas de EE.UU. hoy") + tabla(
        ["Plazo", "Rendimiento", "Cambio 1 día", "Cambio 5 días"],
        [[e(c) for c in fila] for fila in curva], cifras={1, 2, 3})


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
    "oportunidad": cuerpo_oportunidad,
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


def bloque_firma(a: au.Autor, hoy: date) -> str:
    """Quién firma, con la acreditación solo si sigue vigente a la fecha del pedido."""
    foto = f'<img class="firma-foto" src="{_data_uri(a.foto)}" alt="{e(a.nombre)}">' if a.foto else ""
    trazo = f'<img class="firma-trazo" src="{_data_uri(a.firma)}" alt="Firma">' if a.firma else ""
    credencial = ""
    if au.vigente(a, hoy):
        ac = a.acreditacion
        hasta = date.fromisoformat(ac["vigente_hasta"]).strftime("%d-%m-%Y")
        # Sin enlace aunque el config traiga uno: el de la CMV no reconocía el certificado.
        credencial = (
            f'<p class="firma-credencial">Acreditación {e(ac["entidad"])} · Categoría {e(ac["categoria"])}'
            f' · N° {e(ac["numero"])} · Vigente hasta el {hasta}</p>'
        )
    return (
        f'<section class="firma">{foto}<div class="firma-texto">{trazo}'
        f'<p class="firma-nombre">{e(a.nombre)}</p>'
        f'<p class="firma-cargo">{e(a.cargo)} · Grupo Inteligencia</p>{credencial}'
        f'<p class="firma-general">{e(FRASE_GENERAL)}</p></div></section>'
    )


def armar(pieza: dict[str, Any], dir_pedido: Path, analista: dict[str, Any], autor: au.Autor, hoy: date) -> str:
    """HTML completo del informe general, firmado por `autor` a la fecha `hoy`."""
    errs = es.errores(pieza)
    if errs:
        raise InformeInvalido("; ".join(errs))

    from cierre_semanal_contenido import AVISO_LEGAL

    tipo = pieza["orden"]["pieza"]
    d, ed = pieza["datos"], pieza["editorial"]
    nombre = analista["nombre"]
    contacto = " · ".join(x for x in (analista.get("cargo"), analista.get("contacto")) if x)
    tokens = {
        "titulo_documento": e(ed["titular"]),
        "fuentes": _fuentes(),
        "logo": _data_uri(LOGO),
        "chip": e(d["chip"]),
        "titular": e(ed["titular"]),
        "bajada": e(ed["bajada"]),
        "autor_nombre": e(autor.nombre),
        "compartido_por": e(nombre),
        "rotulo_referencia": e(d["rotulo_referencia"]),
        "referencia": e(d["referencia"]),
        "edicion": e(d["edicion"]),
        "cuerpo": CUERPOS[tipo](pieza, dir_pedido),
        "firma": bloque_firma(autor, hoy),
        "aviso_legal": e(AVISO_LEGAL),
        "contacto": e(f"{nombre} · {contacto}" if contacto else nombre),
    }
    salida = _estilos_inline((DIR_PLANTILLAS / "base.html").read_text(encoding="utf-8"))
    # Reemplazo en una sola pasada: un valor que contenga "{{x}}" no vuelve a expandirse.
    return re.sub(r"\{\{(\w+)\}\}", lambda m: tokens[m.group(1)], salida)


def guardar(pieza: dict[str, Any], dir_pedido: Path, analista: dict[str, Any], autor: au.Autor,
            hoy: date, nombre_base: str) -> Path:
    """Escribe el informe y devuelve su ruta."""
    ruta = dir_pedido / f"{nombre_base}.html"
    ruta.write_text(armar(pieza, dir_pedido, analista, autor, hoy), encoding="utf-8")
    return ruta
