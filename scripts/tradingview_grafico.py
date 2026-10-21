#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Motor de renderizado de gráficos TradingView (Lightweight Charts™ v5) en 300 DPI y Alto Contraste.

Extrae velas en tiempo real desde MetaTrader 5 (o recibe un payload JSON por stdin),
dibuja las líneas de la `Lectura` de la estrategia activa (enchufe, fase 2) más las
zonas de soporte y resistencia del mensaje, y compila una imagen
PNG en ultra alta resolución (Retina / 300 DPI) usando Chromium headless (Playwright)
con polyfill de devicePixelContentBoxSize y paleta luminosa de marca Grupo Inteligencia.

Sin líneas explícitas (las piezas ad-hoc y el CLI) el motor lee la lectura del activo
y dibuja esa, en su marco. **Nunca dibuja medias** (director, 2026-10-12): hasta esa
fecha las piezas sin lectura salían con EMA 50/100, una segunda lectura técnica al
lado de la que publica el texto.

Uso CLI directo:
    uv run --with MetaTrader5 python scripts/tradingview_grafico.py --ticker USDCLP --nombre "USD/CLP" --out data/stories/tv_usdclp.png

Uso mediante stdin con payload:
    cat alerta.json | uv run python scripts/tradingview_grafico.py --out data/stories/tv_activo.png
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys
from typing import Any

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

VENDOR_JS = RAIZ / "scripts" / "vendor" / "lightweight-charts.standalone.production.js"


class TradingViewRenderError(RuntimeError):
    """Error accionable en el renderizado de TradingView."""


def _epoch(t: Any) -> int:
    if isinstance(t, str):
        return int(datetime.fromisoformat(t.replace("Z", "+00:00")).replace(tzinfo=timezone.utc).timestamp())
    if isinstance(t, (int, float)):
        return int(t)
    return int(t.timestamp())


def calcular_indicadores(df_velas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Las velas con el ATR 14, que da alto a las zonas de soporte y resistencia.

    No hay indicadores de dirección: la dirección la dibujan las líneas de la lectura.
    Bollinger, Donchian, RSI, ADX y las EMA 20/200 se borraron con el enchufe (spec §6),
    y las EMA 50/100 el 2026-10-12, cuando también las piezas ad-hoc pasaron a la lectura.
    """
    if not df_velas:
        return []
    cierres = [float(v["close"]) for v in df_velas]
    rangos = []
    for i, v in enumerate(df_velas):
        alto, bajo = float(v["high"]), float(v["low"])
        previo = cierres[i - 1] if i else cierres[0]
        rangos.append(max(alto - bajo, abs(alto - previo), abs(bajo - previo)))
    atr14: list[float | None] = [None] * len(rangos)
    if len(rangos) >= 14:
        atr = sum(rangos[:14]) / 14
        atr14[13] = atr
        for i in range(14, len(rangos)):
            atr = (atr * 13 + rangos[i]) / 14
            atr14[i] = atr
    return [{"time": _epoch(v["time"]), "open": float(v["open"]), "high": float(v["high"]),
             "low": float(v["low"]), "close": float(v["close"]),
             "atr": atr14[i]}
            for i, v in enumerate(df_velas)]


# Las líneas de la `Lectura` de la estrategia activa (enchufe, fase 2, S5). El gráfico ya
# no calcula estructura propia: el canal de regresión y los swings del zigzag se borraron
# (spec §6), porque dibujaban una lectura que el texto no conocía.
COLOR_ROL = {"accion": "#FF4D5E", "seguridad": "#26C6A0", "seguimiento": "#9BE7C4",
             "contexto": "#B39DDB", "objetivo": "#FFB300", "rango": "#CBD5E1"}
NOMBRE_ROL = {"accion": "Línea de acción", "seguridad": "Línea de seguridad",
              "seguimiento": "Línea de seguimiento", "contexto": "Línea de contexto",
              "objetivo": "Objetivo", "rango": "Borde del rango"}
PROYECCION = 14  # velas de semirrecta a la derecha (doctrina 2.1)
VENTANA_MIN = 90  # velas visibles como mínimo: con menos, la diagonal no tiene contexto
VENTANA_SIN_DIAGONAL = 160  # sin diagonal que enmarcar, un tramo reciente en vez de dos meses
HOLGURA_ANCLA = 3  # la ventana mide el tramo de la diagonal por este factor


def ventana_visible(series: list[dict[str, Any]], tiempos: list[int]) -> int:
    """Cuántas velas se ven: las que enmarcan a la diagonal más antigua, con aire a la izquierda.

    La lectura se pide con muchas velas para que todas las anclas caigan adentro, pero mostrar
    todas aplasta la línea: una diagonal de tres días sobre dos meses de velas es un trazo de
    veinte pixeles (el EUR/USD de W42). Se muestra el tramo de la diagonal por `HOLGURA_ANCLA`,
    con un mínimo, y nunca más de lo que hay.
    """
    n = len(tiempos)
    primeros = [tiempos.index(int(x["puntos"][0]["time"])) for x in series
                if x["tipo"] == "diagonal" and int(x["puntos"][0]["time"]) in tiempos]
    if not primeros:
        return min(n, VENTANA_SIN_DIAGONAL)
    return min(n, max(VENTANA_MIN, (n - min(primeros)) * HOLGURA_ANCLA))


def series_de_lineas(lineas, tiempos: list[int], proyeccion: int = PROYECCION
                     ) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Las líneas de una lectura como series de Lightweight Charts, contadas en velas.

    Una diagonal lleva un punto por vela desde su primer ancla hasta la proyección: el eje
    de TradingView no reserva espacio a los fines de semana, así que la recta tiene que ser
    recta en velas y no en tiempo. Una diagonal con un ancla fuera de la ventana no se
    puede dibujar sin inventar su posición: se omite y se devuelve con el motivo.
    """
    indice = {int(t): i for i, t in enumerate(tiempos)}
    difs = sorted(b - a for a, b in zip(tiempos, tiempos[1:]))
    paso = difs[len(difs) // 2] if difs else 3600
    fin = len(tiempos) - 1 + proyeccion

    def t_de(i: int) -> int:
        return tiempos[i] if i < len(tiempos) else tiempos[-1] + (i - len(tiempos) + 1) * paso

    series: list[dict[str, Any]] = []
    omitidas: list[dict[str, str]] = []
    for x in lineas:
        dato: dict[str, Any] = {
            "rol": x.rol, "tipo": x.tipo, "color": COLOR_ROL[x.rol],
            "discontinua": x.rol in ("contexto", "objetivo", "rango"),
            "titulo": NOMBRE_ROL[x.rol] + (f" {x.calidad}" if x.calidad else ""),
        }
        if x.tipo == "diagonal":
            (t1, p1), (t2, p2) = x.puntos
            if t1 not in indice or t2 not in indice:
                omitidas.append({"marco": x.marco, "rol": x.rol,
                                 "motivo": "ancla fuera de la ventana de velas dibujada"})
                continue
            i1, i2 = indice[t1], indice[t2]
            pend = (p2 - p1) / (i2 - i1)
            dato["puntos"] = [{"time": t_de(i), "value": p1 + pend * (i - i1)} for i in range(i1, fin + 1)]
        else:
            dato["precio"] = x.puntos[0][1]
        series.append(dato)
    return series, omitidas


LIMPIO_N_VELAS = 60  # el modo limpio muestra un tramo corto: solo lo que se mueve hoy
LIMPIO_ANCHO, LIMPIO_ALTO = 888, 590  # el lienzo de la tarjeta de seguimiento, 1 px = 1 px de lámina
SEPARACION_ETIQUETAS = 46  # px entre centros: la píldora mide 42 y necesita aire
COLOR_NIVEL = {"ENTRADA": "#FFFFFF", "STOP": "#E84040", "OBJETIVO": "#00DC82"}
COLOR_LIMPIO_SUBE, COLOR_LIMPIO_BAJA, COLOR_LIMPIO_HOY = "#00DC82", "#E84040", "#50C0A8"
FONDO_PILDORA = "#04120e"
AIRE_VELAS = 50  # px entre la última vela y las píldoras
FUENTE_PJ_700 = RAIZ / "templates" / "stories" / "fonts" / "plus-jakarta-sans-700.woff2"


def separar_etiquetas(ys: list[float], minimo: float = SEPARACION_ETIQUETAS,
                      techo: float = 21.0, piso: float | None = None) -> list[float]:
    """Posiciones de las píldoras: cada una lo más cerca de su línea, sin pisarse.

    Las líneas se quedan en su precio; solo se mueve la etiqueta. Se reparte el choque hacia
    arriba y abajo (relajación por pares) y al final una pasada ordenada garantiza `minimo`.
    """
    n = len(ys)
    orden = sorted(range(n), key=lambda i: ys[i])
    pos = [float(ys[i]) for i in orden]
    for _ in range(200):
        movido = False
        for k in range(n - 1):
            falta = minimo - (pos[k + 1] - pos[k])
            if falta > 1e-6:
                pos[k] -= falta / 2
                pos[k + 1] += falta / 2
                movido = True
        pos = [max(techo, p) for p in pos]
        if piso is not None:
            pos = [min(piso, p) for p in pos]
        if not movido:
            break
    for k in range(1, n):  # garantía final contra el redondeo de los topes
        pos[k] = max(pos[k], pos[k - 1] + minimo)
    out = [0.0] * n
    for k, i in enumerate(orden):
        out[i] = pos[k]
    return out


def _precio_es(v: float, digits: int) -> str:
    """Notación chilena: punto de miles, coma decimal."""
    return f"{v:,.{digits}f}".replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def _font_b64() -> str:
    import base64

    return base64.b64encode(FUENTE_PJ_700.read_bytes()).decode("ascii") if FUENTE_PJ_700.exists() else ""


def construir_html_limpio(rows: list[dict[str, Any]], digits: int = 2, niveles=None,
                          ancho: int = LIMPIO_ANCHO, alto: int = LIMPIO_ALTO) -> str:
    """Gráfico limpio de la tarjeta de seguimiento: ~60 velas, los niveles de hoy y el precio de hoy.

    Sin leyenda, barra de pie, grilla, zonas ni logo: lo que la lámina cita en precios es solo lo
    que este gráfico traza. Fondo transparente (la lámina pone su degradado y su marca de agua).
    """
    rows = rows[-LIMPIO_N_VELAS:]
    hoy = float(rows[-1]["close"])
    filas = [(float(p), str(n).upper()) for p, n in (niveles or ())]
    tol = 0.5 * 10 ** -digits
    fundidos: list[list] = []  # dos niveles en el mismo precio son una etiqueta con los dos nombres
    for p, n in filas:
        previo = next((f for f in fundidos if abs(f[0] - p) <= tol), None)
        if previo is None:
            fundidos.append([p, n])
        elif n not in previo[1]:
            # fundida la etiqueta se acorta: "SOPORTE DEL RANGO" -> "SOPORTE RANGO", para que quepa en la píldora
            previo[1] += " · " + n.replace(" DEL ", " ").replace(" DE LA ", " ")
    etiquetas = [(p, n, COLOR_NIVEL.get(n.split(" · ")[0], COLOR_LIMPIO_HOY)) for p, n in fundidos]
    etiquetas.append((hoy, "HOY", None))

    textos = [f"{n} {_precio_es(p, digits)}" for p, n, _ in etiquetas]
    pad_r = int(min(400, max(330, max(len(t) for t in textos) * 0.62 * 24 + 42)))
    pad_t = pad_b = 26
    x2 = ancho - pad_r
    maximo = max([float(r["high"]) for r in rows] + [p for p, _, _ in etiquetas])
    minimo = min([float(r["low"]) for r in rows] + [p for p, _, _ in etiquetas])
    margen = (maximo - minimo) * 0.04 or 10 ** -digits
    lo, hi = minimo - margen, maximo + margen

    def y(v: float) -> float:
        return pad_t + (hi - v) / (hi - lo) * (alto - pad_t - pad_b)

    zona = x2 - AIRE_VELAS - 10
    paso = zona / len(rows)
    partes: list[str] = []
    for i, r in enumerate(rows):
        x = 10 + i * paso + paso / 2
        o, c, h, l = (float(r[k]) for k in ("open", "close", "high", "low"))
        col = COLOR_LIMPIO_SUBE if c >= o else COLOR_LIMPIO_BAJA
        partes.append(f'<line x1="{x:.1f}" x2="{x:.1f}" y1="{y(h):.1f}" y2="{y(l):.1f}" stroke="{col}" stroke-width="3.5"/>')
        partes.append(f'<rect x="{x - paso * 0.34:.1f}" width="{paso * 0.68:.1f}" y="{y(max(o, c)):.1f}" '
                      f'height="{max(3.0, abs(y(o) - y(c))):.1f}" fill="{col}"/>')

    reales = [y(p) for p, _, _ in etiquetas]
    pildoras = separar_etiquetas(reales, techo=21.0, piso=alto - 21.0)
    for (p, nombre, col), yr, yp, texto in zip(etiquetas, reales, pildoras, textos):
        es_hoy = col is None
        trazo = COLOR_LIMPIO_HOY if es_hoy else col
        dash = ' stroke-dasharray="3 7"' if es_hoy else (' stroke-dasharray="10 7"' if nombre == "STOP" else "")
        ancho_linea = 3.2 if es_hoy else 3.5
        partes.append(f'<line class="nivel" x1="0" x2="{x2}" y1="{yr:.1f}" y2="{yr:.1f}" stroke="{trazo}" '
                      f'stroke-width="{ancho_linea}"{dash}/>')
        if abs(yp - yr) > 1:
            partes.append(f'<polyline points="{x2},{yr:.1f} {x2 + 4},{yr:.1f} {x2 + 8},{yp:.1f}" fill="none" '
                          f'stroke="{trazo}" stroke-width="2.5"/>')
        w = pad_r - 14
        px = x2 + 8
        fuente = int(min(26, max(20, (w - 28) / (len(texto) * 0.62))))  # nunca bajo 20 px
        if es_hoy:
            partes.append(f'<rect class="pildora" data-y="{yp:.1f}" x="{px}" y="{yp - 21:.1f}" width="{w}" height="42" '
                          f'rx="21" fill="{COLOR_LIMPIO_HOY}"/>')
            partes.append(f'<text x="{px + 14}" y="{yp + 9:.1f}" font-size="{fuente}" font-weight="700" '
                          f'fill="{FONDO_PILDORA}">{texto}</text>')
        else:
            partes.append(f'<rect class="pildora" data-y="{yp:.1f}" x="{px}" y="{yp - 21:.1f}" width="{w}" height="42" '
                          f'rx="21" fill="{FONDO_PILDORA}" fill-opacity=".85" stroke="{trazo}" stroke-width="2.5"/>')
            partes.append(f'<text x="{px + 14}" y="{yp + 9:.1f}" font-size="{fuente}" font-weight="700" fill="#fff" '
                          f'stroke="{FONDO_PILDORA}" stroke-width="5" paint-order="stroke">'
                          f'<tspan fill="{trazo}">{nombre}</tspan> {_precio_es(p, digits)}</text>')
    b64 = _font_b64()
    fuente_css = (f'@font-face{{font-family:PJ;font-weight:700;src:url(data:font/woff2;base64,{b64}) format("woff2")}}'
                  if b64 else "")
    return f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8"><style>
{fuente_css}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{background:transparent;width:{ancho}px;height:{alto}px;overflow:hidden}}
svg{{display:block;font-family:PJ,'Plus Jakarta Sans','Segoe UI',sans-serif}}
</style></head><body>
<div class="tv-container" data-chart-ready="true"><svg width="{ancho}" height="{alto}" viewBox="0 0 {ancho} {alto}">{"".join(partes)}</svg></div>
</body></html>
"""


def construir_html_tradingview(
    rows: list[dict[str, Any]],
    simbolo: str,
    timeframe: str,
    digits: int = 2,
    soporte: float | None = None,
    resistencia: float | None = None,
    ancho: int = 1400,
    alto: int = 780,
    lineas=None,
    niveles=None,
    limpio: bool = False,
) -> str:
    """HTML autocontenido del gráfico: velas, las líneas de la lectura y las zonas de
    soporte y resistencia del mensaje.

    Con `lineas` dibuja la lectura de la estrategia y nada más: ni medias ni estructura
    propia, porque una segunda lectura en la imagen contradice al texto. Sin `lineas`
    quedan las velas y las zonas. Se conserva la paleta oscura de marca del rediseño
    del 2026-09-30.

    Con `limpio=True` (opt-in: el default no cambia) sale el gráfico de la tarjeta de seguimiento:
    solo `niveles` y el precio de hoy, ver `construir_html_limpio`.
    """
    if limpio:
        return construir_html_limpio(rows, digits, niveles, ancho if ancho != 1400 else LIMPIO_ANCHO,
                                     alto if alto != 780 else LIMPIO_ALTO)
    if not VENDOR_JS.exists():
        raise TradingViewRenderError(f"No se encontró el vendor JS: {VENDOR_JS}")

    vendor_code = VENDOR_JS.read_text(encoding="utf-8")
    # Con la lectura se dibujan sus líneas del marco del gráfico y los horizontales de
    # cualquier marco (el objetivo sale de D1 o W1). Sin lectura quedan solo las zonas.
    tiempos = [int(r["time"]) for r in rows]
    con_lectura = lineas is not None
    dibujables = [x for x in (lineas or ()) if x.marco == timeframe or x.tipo == "horizontal"]
    series, _omitidas = series_de_lineas(dibujables, tiempos)
    atrs = sorted(r["atr"] for r in rows if r.get("atr"))
    atr = atrs[len(atrs) // 2] if atrs else (max(r["high"] for r in rows) - min(r["low"] for r in rows)) / 50
    zonas = [
        {"precio": p, "rol": rol}
        for p, rol in ((resistencia, "RESISTENCIA"), (soporte, "SOPORTE")) if p is not None
    ]
    tolerancia = 0.5 * 10 ** -digits
    # Los niveles que cita el texto de la pieza, cada uno con su precio en el eje. Dos con el
    # mismo precio son una sola etiqueta con los dos nombres.
    for precio, nombre in niveles or ():
        zona = next((z for z in zonas if abs(z["precio"] - precio) <= tolerancia), None)
        if zona is None:
            zonas.append({"precio": precio, "rol": nombre})
        elif nombre not in zona["rol"]:
            zona["rol"] += " · " + nombre
    # Un horizontal de la lectura en el mismo precio que una zona (el objetivo suele ser
    # el soporte o la resistencia publicados) se funde con ella: dos etiquetas en el mismo
    # precio se apilan y empujan a las demás sobre el eje (medido el 2026-10-12 en el oro
    # y el USD/CLP). La leyenda lo sigue nombrando.
    en_eje = []
    for serie in series:
        zona = next((z for z in zonas if serie["tipo"] == "horizontal"
                     and abs(z["precio"] - serie["precio"]) <= tolerancia), None)
        nombre = NOMBRE_ROL[serie["rol"]].upper()
        if zona is None:
            en_eje.append(serie)
        elif nombre not in zona["rol"] and not (serie["rol"] == "rango" and "RANGO" in zona["rol"]):
            zona["rol"] += " · " + nombre
    datos = {
        "rows": rows,
        "lineas": en_eje,
        "zonas": zonas,
        "media_zona": 0.18 * atr,
        "digits": digits,
        "desde": len(rows) - ventana_visible(series, tiempos),
    }
    payload_json = json.dumps(datos, separators=(",", ":")).replace("</", "<\\/")

    fmt_p = f"{{:.{digits}f}}"
    last = rows[-1]
    p_close = fmt_p.format(last["close"])
    if con_lectura:
        leyenda = "".join(
            f'<span><span style="color:{d["color"]}">●</span> {d["titulo"]}</span>' for d in series)
        pie = "LÍNEAS DE TENDENCIA · ZONAS DE SOPORTE Y RESISTENCIA"
    else:
        leyenda = ""
        pie = "ZONAS DE SOPORTE Y RESISTENCIA"

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;700;800&family=Space+Grotesk:wght@600;700&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background: #04080E;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #FFFFFF;
    width: {ancho}px; height: {alto}px; overflow: hidden;
    display: flex; flex-direction: column; padding: 12px;
  }}
  .tv-container {{
    display: flex; flex-direction: column; width: 100%; height: 100%;
    background: #070D14; border: 1.5px solid rgba(80, 192, 168, 0.55);
    border-radius: 16px; overflow: hidden;
  }}
  .tv-topbar {{
    height: 50px; display: flex; justify-content: space-between; align-items: center;
    background: #0C1620; border-bottom: 1.5px solid rgba(80, 192, 168, 0.35);
    padding: 0 24px; flex-shrink: 0;
  }}
  .tv-left {{ display: flex; align-items: center; gap: 14px; }}
  .tv-symbol {{ font-weight: 800; font-size: 20px; letter-spacing: 0.04em; }}
  .tv-badge-tf {{
    background: rgba(80, 192, 168, 0.25); color: #50C0A8; border: 1.5px solid #50C0A8;
    padding: 3px 10px; border-radius: 6px; font-weight: 800; font-size: 13px;
  }}
  .tv-precio {{ font-family: 'Space Grotesk', monospace; font-size: 18px; font-weight: 700; color: #FFFFFF; }}
  .tv-legend {{ display: flex; gap: 18px; font-family: 'Space Grotesk', monospace; font-size: 14px; color: #CBD5E1; }}
  .tv-legend b {{ font-weight: 800; }}
  .tv-chart-wrapper {{ position: relative; flex: 1; min-height: 0; width: 100%; background: #070D14; }}
  #chart-container {{ width: 100%; height: 100%; display: block; }}
  #zonas {{ position: absolute; inset: 0; pointer-events: none; z-index: 1; }}
  .zona {{
    position: absolute; left: 0; background: rgba(255, 213, 79, 0.30);
    border-top: 1px solid rgba(255, 213, 79, 0.75); border-bottom: 1px solid rgba(255, 213, 79, 0.75);
  }}
  .tv-caption-bar {{
    height: 30px; display: flex; justify-content: space-between; align-items: center;
    padding: 0 24px; background: #050A0F; border-top: 1.5px solid rgba(80, 192, 168, 0.3);
    font-size: 12px; color: #94A3B8; font-family: 'Space Grotesk', monospace; font-weight: 600; flex-shrink: 0;
  }}
</style>
<script>
// Polyfill ResizeObserver devicePixelContentBoxSize para renderizado Retina/300 DPI en Chromium headless
(function() {{
  const OrigRO = window.ResizeObserver;
  window.ResizeObserver = class extends OrigRO {{
    constructor(cb) {{
      super((entries, obs) => {{
        const dpr = window.devicePixelRatio || 1;
        cb(entries.map(e => {{
          if (!e.devicePixelContentBoxSize) return e;
          const cs = e.contentBoxSize ? e.contentBoxSize[0] : e.devicePixelContentBoxSize[0];
          return new Proxy(e, {{ get(t, p) {{
            if (p === 'devicePixelContentBoxSize') return [{{ inlineSize: Math.round(cs.inlineSize * dpr), blockSize: Math.round(cs.blockSize * dpr) }}];
            return t[p];
          }} }});
        }}), obs);
      }});
    }}
  }};
}})();
</script>
</head>
<body>
<div class="tv-container" data-chart-ready="false">
  <div class="tv-topbar">
    <div class="tv-left">
      <span class="tv-symbol">{simbolo}</span>
      <span class="tv-badge-tf">{timeframe}</span>
      <span class="tv-precio">{p_close}</span>
    </div>
    <div class="tv-legend">{leyenda}</div>
  </div>
  <div class="tv-chart-wrapper">
    <div id="chart-container"></div>
    <div id="zonas"></div>
  </div>
  <div class="tv-caption-bar">
    <span>{len(rows) - datos["desde"]} VELAS {timeframe} · FEED MT5 · GRUPO INTELIGENCIA</span>
    <span>{pie}</span>
  </div>
</div>

<script>{vendor_code}</script>
<script>
(() => {{
  const D = {payload_json};
  const rows = D.rows;
  const container = document.getElementById('chart-container');
  if (!container || typeof LightweightCharts === 'undefined') return;
  const fmt = v => v.toFixed(D.digits);

  const chart = LightweightCharts.createChart(container, {{
    autoSize: true,
    layout: {{
      background: {{ type: 'solid', color: '#070D14' }},
      textColor: '#CBD5E1', fontSize: 12,
      fontFamily: "'Space Grotesk', 'Plus Jakarta Sans', sans-serif",
    }},
    grid: {{
      vertLines: {{ color: 'rgba(255, 255, 255, 0.04)' }},
      horzLines: {{ color: 'rgba(255, 255, 255, 0.04)' }},
    }},
    rightPriceScale: {{
      borderColor: 'rgba(80, 192, 168, 0.25)',
      scaleMargins: {{ top: 0.06, bottom: 0.06 }},
    }},
    timeScale: {{
      borderColor: 'rgba(80, 192, 168, 0.25)',
      timeVisible: true, secondsVisible: false,
      rightOffset: 2, minBarSpacing: 1,
      tickMarkFormatter: (time) => {{
        const date = new Date(time * 1000);
        const d = String(date.getUTCDate()).padStart(2, '0');
        const m = date.toLocaleString('es-CL', {{ month: 'short', timeZone: 'UTC' }}).replace('.', '');
        const h = String(date.getUTCHours()).padStart(2, '0');
        return `${{d}} ${{m}} ${{h}}:00`;
      }},
    }},
    crosshair: {{ mode: LightweightCharts.CrosshairMode.Hidden }},
  }});

  const candles = chart.addSeries(LightweightCharts.CandlestickSeries, {{
    upColor: '#26C6A0', downColor: '#FF4D5E',
    borderUpColor: '#26C6A0', borderDownColor: '#FF4D5E',
    wickUpColor: '#26C6A0', wickDownColor: '#FF4D5E',
    priceFormat: {{ type: 'price', precision: D.digits, minMove: Math.pow(10, -D.digits) }},
    lastValueVisible: true, priceLineVisible: true,
    priceLineColor: '#FFFFFF', priceLineWidth: 1,
    // El eje abarca también cada nivel y línea dibujados: una línea fuera de las velas
    // visibles (el objetivo del EUR/USD) quedaba sin verse.
    autoscaleInfoProvider: (original) => {{
      const r = original();
      if (!r) return r;
      const m = D.media_zona;
      const extra = [
        ...D.lineas.filter(l => l.tipo !== 'diagonal').map(l => l.precio),
        ...D.zonas.flatMap(z => [z.precio - m, z.precio + m]),
        ...D.lineas.filter(l => l.tipo === 'diagonal').flatMap(l => l.puntos.map(p => p.value)),
      ];
      r.priceRange.minValue = Math.min(r.priceRange.minValue, ...extra);
      r.priceRange.maxValue = Math.max(r.priceRange.maxValue, ...extra);
      return r;
    }},
    priceLineStyle: LightweightCharts.LineStyle.Dotted,
  }});
  candles.setData(rows.map(r => ({{ time: r.time, open: r.open, high: r.high, low: r.low, close: r.close }})));

  const linea = (color, ancho, datos, estilo) => {{
    const s = chart.addSeries(LightweightCharts.LineSeries, {{
      color, lineWidth: ancho, lineStyle: estilo ?? LightweightCharts.LineStyle.Solid,
      lastValueVisible: false, priceLineVisible: false,
      crosshairMarkerVisible: false, pointMarkersVisible: false,
      autoscaleInfoProvider: () => null,
    }});
    s.setData(datos);
    return s;
  }};

  // Las líneas de la lectura: diagonales proyectadas a la derecha y horizontales en el eje.
  D.lineas.forEach(l => {{
    const estilo = l.discontinua ? LightweightCharts.LineStyle.Dashed : LightweightCharts.LineStyle.Solid;
    if (l.tipo === 'diagonal') {{
      linea(l.color, 3.2, l.puntos, estilo);
    }} else {{
      candles.createPriceLine({{ price: l.precio, color: l.color, lineWidth: 1, lineStyle: estilo,
                                axisLabelVisible: true, title: l.titulo + ' ' + fmt(l.precio) }});
    }}
  }});

  // Soporte y resistencia del mensaje: la zona amarilla y su precio en el eje.
  D.zonas.forEach(z => candles.createPriceLine({{
    price: z.precio, color: 'rgba(255, 213, 79, 0.0)', lineWidth: 1,
    axisLabelVisible: true, axisLabelColor: '#FFD54F', axisLabelTextColor: '#050B10',
    title: z.rol + ' ' + fmt(z.precio),
  }}));

  // Futuro en blanco para que las diagonales se proyecten a la derecha.
  const ultimo = rows[rows.length - 1].time;
  const futuro = [...new Set(D.lineas.flatMap(l => (l.puntos || []).map(p => p.time)))]
    .filter(t => t > ultimo).sort((a, b) => a - b).map(t => ({{ time: t }}));
  if (futuro.length) candles.setData([...candles.data(), ...futuro]);
  chart.timeScale().setVisibleLogicalRange({{ from: D.desde, to: rows.length + 12 }});

  const pintarZonas = () => {{
    const capa = document.getElementById('zonas');
    capa.innerHTML = '';
    const anchoPrecio = chart.priceScale('right').width();
    const anchoGraf = container.clientWidth - anchoPrecio;
    D.zonas.forEach(z => {{
      const a = candles.priceToCoordinate(z.precio + D.media_zona);
      const b = candles.priceToCoordinate(z.precio - D.media_zona);
      if (a == null || b == null) return;
      const alto = Math.max(10, Math.abs(b - a));
      const centro = (a + b) / 2;
      const div = document.createElement('div');
      div.className = 'zona';
      div.style.top = (centro - alto / 2) + 'px';
      div.style.height = alto + 'px';
      div.style.width = anchoGraf + 'px';
      capa.appendChild(div);
    }});
  }};
  requestAnimationFrame(() => requestAnimationFrame(() => {{
    pintarZonas();
    document.querySelector('.tv-container').dataset.chartReady = 'true';
  }}));
}})();
</script>
</body>
</html>
"""
    return html


def renderizar_png(
    html: str,
    destino: Path,
    ancho: int = 1400,
    alto: int = 780,
    device_scale_factor: int = 2,
    transparente: bool = False,
) -> Path:
    """Renderiza el HTML a un archivo PNG nítido en alta resolución con Playwright y metadatos 300 DPI."""
    from playwright.sync_api import sync_playwright

    destino.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(
            viewport={"width": ancho, "height": alto},
            device_scale_factor=device_scale_factor,
        )
        page.set_content(html, wait_until="load")
        page.wait_for_function(
            "() => document.querySelector('.tv-container')?.dataset.chartReady === 'true'"
        )
        page.wait_for_timeout(450)
        buffer_png = page.screenshot(full_page=True, omit_background=transparente)
        browser.close()

    # Guardar con metadatos 300 DPI explícitos vía Pillow
    imagen = Image.open(io.BytesIO(buffer_png))
    imagen.save(destino, dpi=(300, 300), quality=100)

    return destino


MARCO_SIN_LECTURA = "H1"


def leer_lectura(ticker: str, digits: int):
    """La `Lectura` de la estrategia activa para un ticker, la misma que publica el carrusel."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    import referencia_semanal as rs
    from estrategia import registro
    from estrategia.fuente import velas_mt5

    lectura, _ = rs.lectura_actual(registro.activa(), ticker, digits, velas_mt5,
                                   datetime.now(tz=ZoneInfo("America/Santiago")))
    return lectura


def generar_grafico_tv(
    ticker: str,
    nombre: str,
    destino: Path,
    timeframe: str | None = None,
    n_velas: int = 60,
    digits: int | None = None,
    soporte: float | None = None,
    resistencia: float | None = None,
    ancho: int = 1400,
    alto: int = 780,
    lineas=None,
    niveles=None,
    limpio: bool = False,
) -> Path:
    """Función principal: obtiene datos de MT5, computa indicadores y renderiza el PNG.

    Con `lineas` (las de la `Lectura`) el gráfico dibuja esas. Sin ellas (piezas ad-hoc
    y el CLI) lee la lectura del activo y dibuja sus líneas, en su marco si no se pidió
    otro, con su soporte y resistencia si no vienen dados, y con velas suficientes para
    que las anclas caigan adentro. Si la estrategia no puede leer el activo, el gráfico
    sale con velas y zonas, y lo avisa: nunca con medias como sustituto.

    `niveles` son (precio, nombre) que cita el texto de la pieza: van al eje con su precio, y
    los que coinciden se funden en una etiqueta.

    Con `limpio=True` no lee la lectura ni dibuja sus líneas: ~60 velas y solo los `niveles`
    (ver `construir_html_limpio`), sobre fondo transparente.
    """
    from market_data_mcp import mt5_client
    from market_data_mcp.catalog import VALID_TICKERS

    if digits is None:
        digits = VALID_TICKERS.get(ticker, 2)

    if limpio:
        n_velas = LIMPIO_N_VELAS
        if (ancho, alto) == (1400, 780):
            ancho, alto = LIMPIO_ANCHO, LIMPIO_ALTO
    elif lineas is None:
        import pipeline_carrusel as pc

        try:
            lectura = leer_lectura(ticker, digits)
        except Exception as exc:  # noqa: BLE001
            print(f"[AVISO] {ticker}: gráfico sin la lectura de la estrategia ({exc}). "
                  "Sale con velas y zonas.", file=sys.stderr)
        else:
            lineas = lectura.lineas
            timeframe = timeframe or lectura.marco
            if soporte is None and resistencia is None:
                soporte, resistencia = pc.niveles_publicados(lectura)
            n_velas = max(n_velas, pc.VELAS_GRAFICO_TV)
    timeframe = timeframe or MARCO_SIN_LECTURA

    mt5_client.connect()
    # Velas extra para que el ATR 14 de las zonas ya esté formado en la ventana dibujada
    n_total = n_velas + 20
    df = mt5_client.get_rates(ticker, timeframe, n_total)
    if df is None or len(df) < 20:
        raise TradingViewRenderError(
            f"MT5 devolvió {len(df) if df is not None else 0} velas para {ticker} en {timeframe}."
        )

    velas_dict = df.to_dict(orient="records")
    con_indicadores = calcular_indicadores(velas_dict)

    # Recortar a las últimas `n_velas` para el gráfico
    recorte = con_indicadores[-n_velas:]

    html = construir_html_tradingview(
        rows=recorte,
        simbolo=nombre or ticker,
        timeframe=timeframe,
        digits=digits,
        soporte=soporte,
        resistencia=resistencia,
        ancho=ancho,
        alto=alto,
        lineas=lineas,
        niveles=niveles,
        limpio=limpio,
    )

    return renderizar_png(html, destino, ancho=ancho, alto=alto, transparente=limpio)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticker", default="")
    parser.add_argument("--nombre", default="")
    parser.add_argument("--timeframe", default=None,
                        help="por defecto, el marco de la lectura del activo")
    parser.add_argument("--velas", type=int, default=60)
    parser.add_argument("--soporte", type=float, default=None)
    parser.add_argument("--resistencia", type=float, default=None)
    parser.add_argument("--out", required=True)
    parser.add_argument("--ancho", type=int, default=1400)
    parser.add_argument("--alto", type=int, default=780)
    args = parser.parse_args(argv)

    # Modo stdin si no viene ticker
    if not args.ticker:
        if not sys.stdin.isatty():
            payload = json.load(sys.stdin)
            ticker = payload.get("ticker") or payload.get("activo", "")
            nombre = payload.get("rotulo_activo") or payload.get("activo", ticker)
            soporte = float(payload["soporte"]) if "soporte" in payload else None
            resistencia = float(payload["resistencia"]) if "resistencia" in payload else None
            out_path = Path(args.out)
            generar_grafico_tv(
                ticker=ticker,
                nombre=nombre,
                destino=out_path,
                timeframe=args.timeframe,
                n_velas=args.velas,
                soporte=soporte,
                resistencia=resistencia,
                ancho=args.ancho,
                alto=args.alto,
            )
            print(f"[OK] TradingView renderizado: {out_path}")
            return 0
        else:
            parser.error("--ticker es requerido si no se pasa JSON por stdin.")

    out_path = Path(args.out)
    generar_grafico_tv(
        ticker=args.ticker,
        nombre=args.nombre or args.ticker,
        destino=out_path,
        timeframe=args.timeframe,
        n_velas=args.velas,
        soporte=args.soporte,
        resistencia=args.resistencia,
        ancho=args.ancho,
        alto=args.alto,
    )
    print(f"[OK] TradingView renderizado: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
