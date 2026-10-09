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

import json
import re
from pathlib import Path
from typing import Any

from analista import RAIZ
from analista import autor as au
from analista import informe_html as ih
from analista import semanal as sm

PLANTILLA = RAIZ / "templates" / "correo_semanal" / "correo.html"
# Token de la plantilla → rol de `marca.css`. El correo es un documento claro: usa
# los roles de papel y tinta, y las bandas oscuras solo en la cabecera.
ROLES = {
    "fondo": "banda-1", "fondo_acento": "banda-2", "fondo_alt": "tinta", "acento": "acento",
    "acento_oscuro": "acento-doc", "sube": "sube-doc", "baja": "baja-doc", "texto_1": "papel-alt",
    "texto_3": "tinta-3", "texto_borde": "papel-linea", "texto_banda": "texto-borde", "blanco": "papel",
}


def pesos(valor: float) -> str:
    return "$" + f"{round(valor):,}".replace(",", ".")


def _decimales(paso: float) -> int:
    texto = f"{paso:.8f}".rstrip("0")
    return len(texto.split(".")[1]) if "." in texto else 0


def _numero_es(valor: float, decimales: int) -> str:
    return f"{valor:,.{decimales}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _parrafos(texto: str, color: str) -> str:
    bloques = [b.strip() for b in re.split(r"\n\s*\n", texto) if b.strip()]
    return "".join(f'<p style="margin:0 0 10px 0;font-size:15px;line-height:23px;color:{color};">{ih.e(b)}</p>'
                   for b in bloques)


def _vinetas(texto: str, color: str) -> str:
    lineas = [ln.strip(" •-*\t") for ln in texto.splitlines() if ln.strip(" •-*\t")]
    items = "".join(f'<li style="margin:0 0 6px 0;font-size:15px;line-height:22px;color:{color};">{ih.e(ln)}</li>'
                    for ln in lineas)
    return f'<ul style="margin:0;padding:0 0 0 20px;">{items}</ul>'


def _filas_escenario(esc: dict[str, Any], c: dict[str, str]) -> str:
    f = esc["fmt"]
    alcista = esc["sesgo"] == "Alcista"
    lado, borde = ("sobre", "bajo") if alcista else ("bajo", "sobre")
    filas = [
        ("Se activa", f"Cierre diario {lado} <strong>{ih.e(f['gatillo'])}</strong>", c["sube"] if alcista else c["baja"]),
        ("Se anula", f"Cierre diario {borde} <strong>{ih.e(f['invalidacion'])}</strong> (salida por volatilidad)",
         c["fondo_alt"]),
        ("Recorrido", f"Unos <strong>{ih.e(f['recorrido'])}</strong>, 1,5 veces la volatilidad típica de un día. "
                      "Es una distancia, no un objetivo de precio.", c["fondo_alt"]),
    ]
    return "".join(
        f'<tr><td width="110" style="padding:10px 12px;font-size:13px;font-weight:700;color:{color};'
        f'border-bottom:1px solid {c["texto_borde"]};">{rotulo}</td>'
        f'<td style="padding:10px 12px;font-size:14px;line-height:21px;color:{c["fondo_alt"]};'
        f'border-bottom:1px solid {c["texto_borde"]};">{celda}</td></tr>'
        for rotulo, celda, color in filas
    )


def armar(pieza: dict[str, Any], dir_pedido: Path, ejecutivo: dict[str, Any], autor: au.Autor) -> str:
    """El HTML del correo con el panel, listo para abrir en el navegador."""
    from cierre_semanal_contenido import AVISO_LEGAL

    d, ed = pieza["datos"], pieza["editorial"]
    esc, contrato = d["escenario"], d["contrato"]
    paleta = sm.colores_marca()
    c = {token: paleta[rol] for token, rol in ROLES.items()}
    sim = sm.simular(contrato, esc, d["monto_base"], contrato["vol_min"])
    dec_vol = _decimales(float(contrato["vol_paso"]))
    alcista = esc["sesgo"] == "Alcista"
    datos_js = {
        "contrato": {k: contrato[k] for k in ("clp_unidad", "margen_lote", "vol_min", "vol_paso")},
        "escenario": {k: esc[k] for k in ("precio", "entrada", "invalidacion", "recorrido")},
        "decimales_volumen": dec_vol,
    }
    tokens = {
        **{f"c_{rol}": color for rol, color in c.items()},
        "c_direccion": c["sube"] if alcista else c["baja"],
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
        "contexto_semana": _parrafos(ed["contexto_semana"], c["fondo_alt"]),
        "que_lo_mueve": _vinetas(ed["que_lo_mueve"], c["fondo_alt"]),
        "filas_escenario": _filas_escenario(esc, c),
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
    plantilla = PLANTILLA.read_text(encoding="utf-8")
    # Una sola pasada: un valor que contenga "{{x}}" no vuelve a expandirse.
    return re.sub(r"\{\{(\w+)\}\}", lambda m: tokens[m.group(1)], plantilla)


def guardar(pieza: dict[str, Any], dir_pedido: Path, ejecutivo: dict[str, Any], autor: au.Autor,
            nombre: str) -> Path:
    ruta = dir_pedido / nombre
    ruta.write_text(armar(pieza, dir_pedido, ejecutivo, autor), encoding="utf-8")
    return ruta
