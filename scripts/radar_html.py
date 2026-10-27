"""Generación de la página HTML y orden de filas del radar multifractal.

Spec §3, §5, §6 y brief de Task 5. Ordena los activos por confluencia de eventos
y genera un reporte visual HTML autocontenido con estilos inline.
"""
from __future__ import annotations

import html
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from estrategia.tori.radar import Evento, LecturaMarco, RADAR_MARCOS

MARCOS_ORDEN = ("D1", "H4", "H1")
DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


@dataclass(frozen=True)
class Fila:
    ticker: str
    categoria: str                       # primer tramo de symbol_info.path
    digits: int
    marcos: dict[str, LecturaMarco]      # solo los marcos que se pudieron leer
    cierres: dict[str, datetime]         # marco -> cierre de la última vela, en Santiago


@dataclass(frozen=True)
class Falla:
    ticker: str
    marco: str | None                    # None: falló el símbolo entero
    motivo: str


@dataclass(frozen=True)
class Escaneo:
    inicio: datetime                     # Santiago
    duracion_s: float
    cuenta: int
    leidos: int
    filas: tuple[Fila, ...]
    fallas: tuple[Falla, ...]
    paridad: tuple[str, ...]


def _eventos_fila(f: Fila) -> list[Evento]:
    return [ev for lm in f.marcos.values() for ev in lm.eventos]


def _criterio_orden(f: Fila) -> tuple[int, int, int]:
    marcos_con_evento = sum(1 for lm in f.marcos.values() if len(lm.eventos) > 0)
    tiene_toco = any(ev.tipo == "toco" for ev in _eventos_fila(f))
    por_tocar = [ev.velas for ev in _eventos_fila(f) if ev.tipo == "por_tocar" and ev.velas is not None]
    min_velas = min(por_tocar) if por_tocar else 999
    return (-marcos_con_evento, 0 if tiene_toco else 1, min_velas)


def ordenar(filas: Iterable[Fila]) -> list[Fila]:
    """Filtra filas sin eventos y ordena por confluencia, toco y menor velas."""
    con_actividad = [f for f in filas if len(_eventos_fila(f)) > 0]
    return sorted(con_actividad, key=_criterio_orden)


def _direccion_fila(f: Fila) -> tuple[str, str, str]:
    """Determina la dirección del marco mayor con lectura (D1 > H4 > H1)."""
    for m in MARCOS_ORDEN:
        if m in f.marcos:
            d = f.marcos[m].direccion.upper()
            if "ALC" in d:
                return "⬆️", m, "alcista"
            elif "BAJ" in d:
                return "⬇️", m, "bajista"
            else:
                return "↔️", m, "lateral"
    return "↔️", "", ""


def _prioridad_evento(ev: Evento) -> tuple[int, int, float]:
    if ev.tipo == "toco":
        return (0, 0, ev.distancia_atr)
    velas = ev.velas if ev.velas is not None else 999
    return (1, velas, ev.distancia_atr)


def _clase_linea(linea: str) -> str:
    if linea == "seguridad":
        return "seg"
    elif linea == "accion":
        return "acc"
    elif linea in ("soporte", "resistencia"):
        return "sr"
    elif linea == "rango":
        return "rng"
    return "sr"


def _nombre_linea(linea: str) -> str:
    if linea == "seguridad":
        return "control"
    elif linea == "accion":
        return "acción"
    elif linea in ("soporte", "resistencia"):
        return "S/R"
    elif linea == "rango":
        return "rango"
    return linea


def _render_evento(ev: Evento, digits: int) -> str:
    clase = _clase_linea(ev.linea)
    nombre = _nombre_linea(ev.linea)
    valor_fmt = f"{ev.valor:,.{digits}f}"
    if ev.tipo == "toco":
        texto = f"✅ tocó {nombre} · {valor_fmt}"
    else:
        v_str = f"{ev.velas} vela" if ev.velas == 1 else f"{ev.velas} velas"
        texto = f"{nombre} a {v_str} · {valor_fmt}"

    if ev.linea in ("soporte", "resistencia"):
        tag = ev.linea
    else:
        partes = [p for p in (ev.calidad, ev.detalle) if p]
        tag = " · ".join(partes)

    tag_html = f'<span class="tag">{html.escape(tag)}</span>' if tag else ""
    return f'<span class="ev {clase}">{html.escape(texto)}{tag_html}</span>'


_CSS = """
<style>
  body{background:#04080e;color:#e6edf3;font-family:Arial,Helvetica,sans-serif;margin:0;padding:20px}
  .rd{background:#070d14;color:#e6edf3;border:1px solid #50C0A8;border-radius:10px;padding:18px;max-width:1100px;margin:0 auto}
  .rd h3{margin:0 0 4px;color:#50C0A8;font-size:20px}
  .rd .meta{font-size:12px;opacity:.75;margin-bottom:14px}
  .rd table{width:100%;border-collapse:separate;border-spacing:4px;font-size:12.5px}
  .rd th{opacity:.7;font-weight:normal;text-align:center;padding:4px}
  .rd th.l,.rd td.l{text-align:left}
  .rd td{vertical-align:top;padding:6px;border-radius:6px}
  .rd td.c{background:#0f1a26;min-width:150px}
  .rd .hora{font-size:10px;opacity:.6;margin-bottom:3px}
  .rd .vacio{opacity:.3;text-align:center}
  .rd .ev{display:block;margin:2px 0;padding:2px 6px;border-radius:4px}
  .seg{background:#26C6A033;border-left:3px solid #26C6A0}
  .acc{background:#FF4D5E33;border-left:3px solid #FF4D5E}
  .sr{background:#FFD54F2b;border-left:3px solid #FFD54F}
  .rng{background:#CBD5E122;border-left:3px solid #CBD5E1}
  .tag{font-size:10px;opacity:.8;margin-left:4px}
  .conf{display:inline-block;background:#50C0A8;color:#070d14;font-weight:bold;border-radius:10px;padding:1px 7px;font-size:11px}
  .rd details summary{cursor:pointer;font-size:11px;opacity:.7;margin-top:2px}
  .ley{font-size:11px;margin-top:14px;opacity:.8}
  .ley span{margin-right:12px}
  .fallas{margin-top:14px;font-size:12px;border-top:1px solid #ffffff22;padding-top:8px;opacity:.85}
</style>
"""


def render(e: Escaneo) -> str:
    """Renderiza la matriz HTML del radar multifractal."""
    filas_ordenadas = ordenar(e.filas)

    # Encabezado
    dia_nombre = DIAS_SEMANA[e.inicio.weekday()]
    fecha_str = f"{dia_nombre} {e.inicio.strftime('%d-%m-%Y')}"
    hora_str = e.inicio.strftime("%H:%M")

    meta_partes = [
        f"{fecha_str}",
        f"escaneo {hora_str} Chile",
        f"{e.leidos} leídos",
        f"{len(filas_ordenadas)} con actividad",
    ]
    if len(e.fallas) > 0:
        meta_partes.append(f"{len(e.fallas)} no se pudieron leer")
    meta_partes.extend([
        f"cuenta MT5 {e.cuenta}",
        f"duración {e.duracion_s:.1f} s",
    ])
    meta_linea = " · ".join(meta_partes)

    # Aviso lectura incompleta
    aviso_html = ""
    if e.leidos > 0 and len({f.ticker for f in e.fallas}) > (e.leidos / 2):
        aviso_html = (
            '<div class="aviso-incompleto" style="background:#FF4D5E22;border:1px solid #FF4D5E;'
            'padding:10px 14px;border-radius:6px;margin-bottom:14px;font-size:13px;font-weight:bold;color:#FF4D5E;">'
            '⚠️ Lectura incompleta: no confíes en la ausencia de un activo'
            '</div>\n'
        )

    # Filas de la tabla
    filas_html: list[str] = []
    for fila in filas_ordenadas:
        flecha, marco_mayor, dir_txt = _direccion_fila(fila)
        subtitulo_partes = []
        if fila.categoria:
            subtitulo_partes.append(html.escape(fila.categoria))
        if marco_mayor:
            subtitulo_partes.append(f"{flecha} {marco_mayor} {dir_txt}")
        subtitulo = " · ".join(subtitulo_partes)
        subtitulo_html = f"<br>{subtitulo}" if subtitulo else ""

        col_activo = f'<td class="l"><b>{html.escape(fila.ticker)}</b>{subtitulo_html}</td>'

        marcos_con_ev = sum(1 for lm in fila.marcos.values() if len(lm.eventos) > 0)
        conf_txt = f"{marcos_con_ev} marcos" if marcos_con_ev != 1 else "1 marco"
        conf_badge = f'<span class="conf">{conf_txt}</span>' if marcos_con_ev > 1 else conf_txt
        col_conf = f'<td style="text-align:center">{conf_badge}</td>'

        cols_marcos: list[str] = []
        for marco in ("H1", "H4", "D1"):
            if marco not in fila.marcos or len(fila.marcos[marco].eventos) == 0:
                cols_marcos.append('<td class="vacio">·</td>')
                continue

            lectura = fila.marcos[marco]
            evs = sorted(lectura.eventos, key=_prioridad_evento)

            cierre = fila.cierres.get(marco)
            cierre_str = ""
            if cierre is not None:
                if cierre.date() == e.inicio.date():
                    cierre_str = cierre.strftime("%H:%M")
                else:
                    cierre_str = cierre.strftime("%H:%M %d-%m")

            cierre_html = f'<div class="hora">{cierre_str}</div>' if cierre_str else ""
            primer_ev = _render_evento(evs[0], fila.digits)

            detalles_html = ""
            if len(evs) > 1:
                resto = evs[1:]
                n_mas = len(resto)
                s_mas = f"+{n_mas} evento" if n_mas == 1 else f"+{n_mas} eventos"
                resto_html = "".join(_render_evento(ev, fila.digits) for ev in resto)
                detalles_html = f"<details><summary>{s_mas}</summary>{resto_html}</details>"

            cols_marcos.append(f'<td class="c">{cierre_html}{primer_ev}{detalles_html}</td>')

        filas_html.append(
            f'    <tr>\n      {col_activo}\n      {col_conf}\n      {"".join(cols_marcos)}\n    </tr>'
        )

    tabla_contenido = "\n".join(filas_html) if filas_html else '    <tr><td colspan="5" class="vacio" style="padding:18px">Sin activos con actividad</td></tr>'

    # Fallas
    fallas_html = ""
    if e.fallas:
        items_f = []
        for f in e.fallas:
            if f.marco:
                items_f.append(f"{f.ticker} {f.marco} ({f.motivo})")
            else:
                items_f.append(f"{f.ticker} ({f.motivo})")
        fallas_str = " · ".join(html.escape(item) for item in items_f)
        fallas_html = f'<div class="fallas"><b>No se pudieron leer ({len(e.fallas)}):</b> {fallas_str}</div>\n'

    # Paridad
    paridad_html = ""
    if e.paridad:
        items_p = "<br>".join(html.escape(p) for p in e.paridad)
        paridad_html = f'<div class="fallas" style="border-top-color:#50C0A844;"><b>Control de paridad ({len(e.paridad)}):</b><br>{items_p}</div>\n'

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Radar Multifractal · Qué mirar hoy</title>
{_CSS}
</head>
<body>
<div class="rd">
  {aviso_html}<h3>Qué mirar hoy</h3>
  <div class="meta">{meta_linea}</div>

  <table>
    <tr><th class="l">Activo</th><th>Confluencia</th><th>1H</th><th>4H</th><th>1D</th></tr>
{tabla_contenido}
  </table>

  <div class="ley">
    <span><b style="color:#26C6A0">■</b> Línea de control</span>
    <span><b style="color:#FF4D5E">■</b> Línea de acción</span>
    <span><b style="color:#FFD54F">■</b> Zona S/R</span>
    <span><b style="color:#CBD5E1">■</b> Rango</span>
    <span>✅ = tocó en la última vela cerrada de ese marco · "N velas" = llega a la línea en N velas al ritmo típico (ATR)</span>
  </div>

  {fallas_html}  {paridad_html}</div>
</body>
</html>
"""


def render_error(titulo: str, motivo: str, inicio: datetime) -> str:
    """Renderiza una página HTML limpia de error en caso de fallo crítico previo al escaneo."""
    dia_nombre = DIAS_SEMANA[inicio.weekday()]
    fecha_str = f"{dia_nombre} {inicio.strftime('%d-%m-%Y')} · {inicio.strftime('%H:%M')} Chile"

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Radar Multifractal · {html.escape(titulo)}</title>
{_CSS}
</head>
<body>
<div class="rd">
  <h3>{html.escape(titulo)}</h3>
  <div class="meta">{fecha_str}</div>
  <div class="error" style="background:#FF4D5E22;border:1px solid #FF4D5E;padding:12px;border-radius:6px;margin-top:12px;color:#FF4D5E;font-size:13px">
    <b>Error:</b> {html.escape(motivo)}
  </div>
</div>
</body>
</html>
"""
