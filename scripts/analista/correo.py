"""El correo semanal para Outlook: maqueta de tablas, estilos en línea y un panel que no se copia.

Sigue el formato de la referencia del área comercial (MasQueUF): arriba un panel
de edición y abajo el correo de 640 px que se copia con «Copiar correo para
Outlook». Tres reglas que no conviene revertir:

1. **El análisis no se edita.** El panel solo toca el saludo, los datos de quien
   envía y la simulación (monto y volumen). Contexto, escenario y niveles son de
   quien firma el análisis y salen igual para todos (criterio 1 del plan).
2. **Sin `var()` ni hojas externas.** Outlook no entiende variables de CSS ni
   carga `<link>`: los colores se inyectan como hex leídos de `marca.css`, y el
   logo y el gráfico van en base64.
3. **La simulación se calcula dos veces con la misma fórmula**: Python
   (`semanal.simular`) para el valor inicial y el JavaScript del panel al
   editar. Un test corre las dos y las compara.
"""
from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any

from analista import RAIZ
from analista import autor as au
from analista import informe_html as ih
from analista import semanal as sm

PLANTILLA = RAIZ / "templates" / "correo_semanal" / "correo.html"
CUERPO = RAIZ / "templates" / "correo_semanal" / "cuerpo.html"
# Token de la plantilla → rol de `marca.css`, una tabla por versión. La oscura es
# la línea de las láminas (negro y tinte esmeralda); la clara, la del documento
# (papel y tinta, con el acento oscuro que da contraste sobre blanco). En las dos
# la cabecera es la banda oscura porque el logo es blanco, el cromo va en el
# acento y solo la dirección y el resultado se colorean.
TEMAS = {
    "oscuro": {
        "fondo": "fondo", "fondo_alt": "fondo-alt", "portada": "fondo-acento", "tarjeta": "fondo-acento",
        "acento": "acento", "sube": "sube", "baja": "baja", "fondo_sube": "fondo-sube", "fondo_baja": "fondo-baja",
        "texto_1": "texto-1", "texto_2": "texto-2", "texto_borde": "texto-borde", "sobre_direccion": "fondo",
        "cabecera": "fondo", "cabecera_texto_1": "texto-1", "cabecera_texto_2": "texto-2",
        "filete_1": "acento-azul", "filete_2": "acento",
    },
    "claro": {
        "fondo": "papel-alt", "fondo_alt": "papel", "portada": "acento-tenue", "tarjeta": "papel-alt",
        "acento": "acento-doc", "sube": "sube-doc", "baja": "baja-doc", "fondo_sube": "sube-tenue",
        "fondo_baja": "baja-tenue", "texto_1": "tinta", "texto_2": "tinta-3", "texto_borde": "tinta-2",
        "sobre_direccion": "papel", "linea": "papel-linea",
        "cabecera": "banda-1", "cabecera_texto_1": "texto-1", "cabecera_texto_2": "texto-2",
        "filete_1": "acento-azul", "filete_2": "acento",
    },
}
# La familia va escrita en cada elemento: «Copiar correo» lleva solo el cuerpo y
# el <head> se queda atrás. El cuerpo va en Segoe UI, que traen Windows y Outlook,
# así que el cliente lo ve tal cual; en Mac cae a Arial. Goldman queda solo en
# titulares y cifras: el navegador la carga y Outlook de escritorio pone Segoe UI.
F_DISPLAY = "'Goldman','Segoe UI',Arial,Helvetica,sans-serif"
F_SANS = "'Segoe UI',Arial,Helvetica,sans-serif"
FUENTES = RAIZ / "templates" / "stories" / "fonts"


def paleta(tema: str) -> dict[str, str]:
    marca = sm.colores_marca()
    c = {token: marca[rol] for token, rol in TEMAS[tema].items()}
    # El filete del cristal de marca (acento al 35 % sobre el fondo de los bloques).
    c.setdefault("linea", _mezclar(c["acento"], c["fondo_alt"], 0.35))
    return c


def _mezclar(color: str, fondo: str, alfa: float) -> str:
    """El hex de `color` con opacidad `alfa` sobre `fondo`: Outlook no entiende rgba()."""
    a, b = (tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) for h in (color, fondo))
    return "#" + "".join(f"{round(y + (x - y) * alfa):02X}" for x, y in zip(a, b))


def _fuente(nombre: str) -> str:
    return "data:font/woff2;base64," + base64.b64encode((FUENTES / nombre).read_bytes()).decode("ascii")


def pesos(valor: float) -> str:
    return "$" + f"{round(valor):,}".replace(",", ".")


def _decimales(paso: float) -> int:
    texto = f"{paso:.8f}".rstrip("0")
    return len(texto.split(".")[1]) if "." in texto else 0


def _numero_es(valor: float, decimales: int) -> str:
    return f"{valor:,.{decimales}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _parrafos(texto: str, c: dict[str, str]) -> str:
    bloques = [b.strip() for b in re.split(r"\n\s*\n", texto) if b.strip()]
    return "".join(f'<p style="margin:0 0 14px 0;font-family:{F_SANS};font-size:17px;line-height:27px;'
                   f'font-weight:500;color:{c["texto_borde"]};">{ih.e(b)}</p>' for b in bloques)


def _vinetas(texto: str, c: dict[str, str]) -> str:
    """Una fila por driver con una barra de acento: las viñetas de lista se ven distinto en cada cliente."""
    lineas = [ln.strip(" •-*\t") for ln in texto.splitlines() if ln.strip(" •-*\t")]
    filas = "".join(
        f'<tr><td width="4" bgcolor="{c["acento"]}" style="background:{c["acento"]};font-size:0;">&nbsp;</td>'
        f'<td style="padding:4px 0 4px 14px;font-family:{F_SANS};font-size:17px;line-height:26px;'
        f'font-weight:500;color:{c["texto_borde"]};">{ih.e(ln)}</td></tr>'
        f'<tr><td colspan="2" style="height:10px;font-size:0;line-height:0;">&nbsp;</td></tr>'
        for ln in lineas)
    return f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">{filas}</table>'


def _fila(rotulo: str, celda: str, color_rotulo: str, c: dict[str, str], ultima: bool = False,
          alinear: str = "left", ancho: str = ' width="130"') -> str:
    borde = "" if ultima else f'border-bottom:1px solid {c["linea"]};'
    return (f'<tr><td{ancho} valign="top" style="padding:14px 16px;font-family:{F_SANS};font-size:15px;'
            f'line-height:22px;font-weight:800;text-transform:uppercase;letter-spacing:.5px;'
            f'color:{color_rotulo};{borde}">{rotulo}</td>'
            f'<td align="{alinear}" style="padding:14px 16px;font-family:{F_SANS};font-size:16px;line-height:24px;'
            f'font-weight:500;color:{c["texto_borde"]};{borde}">{celda}</td></tr>')


def _destacar(cifra: str, c: dict[str, str], id_: str = "") -> str:
    ident = f' id="{id_}"' if id_ else ""
    return f'<strong{ident} style="color:{c["texto_1"]};font-weight:800;">{cifra}</strong>'


def _filas_escenario(esc: dict[str, Any], c: dict[str, str]) -> str:
    f = esc["fmt"]
    alcista = esc["sesgo"] == "Alcista"
    lado, borde = ("sobre", "bajo") if alcista else ("bajo", "sobre")
    filas = [
        ("Se activa", f"Cierre diario {lado} {_destacar(ih.e(f['gatillo']), c)}", c["sube"] if alcista else c["baja"]),
        ("Se anula", f"Cierre diario {borde} {_destacar(ih.e(f['invalidacion']), c)} (salida por volatilidad)",
         c["texto_2"]),
        ("Recorrido", f"Unos {_destacar(ih.e(f['recorrido']), c)}, 1,5 veces la volatilidad típica de un día. "
                      "Es una distancia, no un objetivo de precio.", c["acento"]),
    ]
    return "".join(_fila(r, celda, color, c, ultima=i == len(filas) - 1) for i, (r, celda, color) in enumerate(filas))


def _filas_simulacion(sim_txt: dict[str, str], c: dict[str, str]) -> str:
    filas = [
        ("Monto de la cuenta", "v-monto", "sim_monto"),
        ("Volumen", "v-volumen", "sim_volumen"),
        ("Cuánto mueve cada punto de precio", "v-valor-punto", "sim_valor_punto"),
        ("Garantía que pide el broker (margen)", "v-margen", "sim_margen"),
        ("Exposición total", "v-nocional", "sim_nocional"),
        ("Apalancamiento efectivo (exposición ÷ monto)", "v-apalancamiento", "sim_apalancamiento"),
        ("Si el precio se mueve 1 % en contra", "v-uno-pct", "sim_uno_pct"),
    ]
    borde = f'border-bottom:1px solid {c["linea"]};'
    return "".join(
        f'<tr><td style="padding:12px 16px;font-family:{F_SANS};font-size:16px;line-height:23px;font-weight:500;'
        f'color:{c["texto_borde"]};{"" if i == len(filas) - 1 else borde}">{rotulo}</td>'
        f'<td align="right" style="padding:12px 16px;font-family:{F_SANS};font-size:17px;line-height:23px;'
        f'white-space:nowrap;{"" if i == len(filas) - 1 else borde}">{_destacar(sim_txt[clave], c, id_)}</td></tr>'
        for i, (rotulo, id_, clave) in enumerate(filas))


def armar(pieza: dict[str, Any], dir_pedido: Path, ejecutivo: dict[str, Any], autor: au.Autor) -> str:
    """El HTML del correo con el panel, listo para abrir en el navegador."""
    from cierre_semanal_contenido import AVISO_LEGAL

    d, ed = pieza["datos"], pieza["editorial"]
    esc, contrato = d["escenario"], d["contrato"]
    sim = sm.simular(contrato, esc, d["monto_base"], contrato["vol_min"])
    dec_vol = _decimales(float(contrato["vol_paso"]))
    alcista = esc["sesgo"] == "Alcista"
    datos_js = {
        "contrato": {k: contrato[k] for k in ("clp_unidad", "margen_lote", "vol_min", "vol_paso")},
        "escenario": {k: esc[k] for k in ("precio", "entrada", "invalidacion", "recorrido")},
        "decimales_volumen": dec_vol,
    }
    comunes = {
        "f_display": F_DISPLAY,
        "f_sans": F_SANS,
        "fuente_goldman": _fuente("goldman-700.woff2"),
        "titulo_documento": ih.e(f"{d['nombre']} · Escenario de la semana"),
        "logo": ih._data_uri(ih.LOGO),
        "grafico": ih._data_uri(dir_pedido / pieza["imagenes"]["principal"]),
        "pie_imagen": ih.e(d["pie_imagen"]),
        "datos_al": ih.e(d["datos_al"]),
        "chip": ih.e(d["chip"]),
        "titular": ih.e(ed["titular"]),
        "bajada": ih.e(ed["bajada"]),
        "nombre": ih.e(d["nombre"]),
        "ticker_visible": ih.e(d["ticker_visible"]),
        "precio": ih.e(d["precio"]),
        "unidad": ih.e(d["unidad"]),
        "direccion": ih.e(d["direccion"]),
        "direccion_mayus": ih.e(d["direccion"].upper()),
        "autor_nombre": ih.e(autor.nombre),
        "autor_cargo": ih.e(autor.cargo),
        "estado": ih.e(esc["textos"]["estado"]),
        "temporalidad": ih.e(d["temporalidad"]),
        "por_que_1d": ih.e(d["por_que_1d"]),
        "invalidacion": ih.e(esc["fmt"]["invalidacion"]),
        "recorrido": ih.e(esc["fmt"]["recorrido"]),
        "ejecutivo_nombre": ih.e(ejecutivo.get("nombre", "")),
        "ejecutivo_cargo": ih.e(ejecutivo.get("cargo", "")),
        "ejecutivo_contacto": ih.e(ejecutivo.get("contacto", "")),
        "monto_base": str(int(d["monto_base"])),
        "vol_min": repr(float(contrato["vol_min"])),
        "vol_paso": repr(float(contrato["vol_paso"])),
        "vol_min_es": _numero_es(float(contrato["vol_min"]), dec_vol),
        "vol_paso_es": _numero_es(float(contrato["vol_paso"]), dec_vol),
        "sim_monto": pesos(d["monto_base"]),
        "sim_volumen": _numero_es(sim["volumen"], dec_vol),
        "sim_valor_punto": pesos(sim["valor_punto"]),
        "sim_margen": pesos(sim["margen"]),
        "sim_nocional": pesos(sim["nocional"]),
        "sim_apalancamiento": (f"{_numero_es(sim['apalancamiento'], 2)} veces"
                               if sim["apalancamiento"] is not None else "sin monto"),
        "sim_uno_pct": pesos(sim["uno_pct_contra"]),
        "sim_perdida": "−" + pesos(sim["perdida_invalidacion"]),
        "sim_recorrido": "+" + pesos(sim["valor_recorrido"]),
        "aviso_legal": ih.e(AVISO_LEGAL),
        # Dentro de <script>: "</" cerraría la etiqueta antes de tiempo.
        "datos_js": json.dumps(datos_js, ensure_ascii=False).replace("</", "<\\/"),
    }

    def con_tema(tema: str) -> dict[str, str]:
        c = paleta(tema)
        return {
            **comunes,
            **{f"c_{rol}": color for rol, color in c.items()},
            "c_direccion": c["sube"] if alcista else c["baja"],
            "contexto_semana": _parrafos(ed["contexto_semana"], c),
            "que_lo_mueve": _vinetas(ed["que_lo_mueve"], c),
            "filas_escenario": _filas_escenario(esc, c),
            "filas_simulacion": _filas_simulacion(comunes, c),
            # Índices, ETF y acciones: cómo se eligió el activo, a la vista del cliente.
            "seleccion": (f'<p style="margin:12px 0 0 0;font-family:{F_SANS};font-size:15px;line-height:22px;'
                          f'font-weight:500;color:{c["texto_2"]};">'
                          f'{ih.e(d["seleccion"]["texto"])}</p>') if d.get("seleccion") else "",
        }

    oscuro = con_tema("oscuro")
    # El panel siempre va en la versión oscura; el correo, en la que elija el ejecutivo.
    return _rellenar(PLANTILLA, {**oscuro, "cuerpo_oscuro": _compactar(_rellenar(CUERPO, oscuro)),
                                 "cuerpo_claro": _compactar(_rellenar(CUERPO, con_tema("claro")))})


def _compactar(html: str) -> str:
    """Quita los saltos de línea del código entre etiquetas.

    Outlook pega con el motor de Word, que convierte esos espacios en sangría.
    Solo se quita el espacio que lleva un salto de línea: un espacio simple entre
    etiquetas es contenido («4.196,62</strong> <span>USD»).
    """
    return re.sub(r">\s*\n\s*<", "><", html).strip()


def _rellenar(plantilla: Path, tokens: dict[str, str]) -> str:
    # Una sola pasada: un valor que contenga "{{x}}" no vuelve a expandirse.
    return re.sub(r"\{\{(\w+)\}\}", lambda m: tokens[m.group(1)], plantilla.read_text(encoding="utf-8"))


def guardar(pieza: dict[str, Any], dir_pedido: Path, ejecutivo: dict[str, Any], autor: au.Autor,
            nombre: str) -> Path:
    ruta = dir_pedido / nombre
    ruta.write_text(armar(pieza, dir_pedido, ejecutivo, autor), encoding="utf-8")
    return ruta
