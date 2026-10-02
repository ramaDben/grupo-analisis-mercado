#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Motor de renderizado de gráficos TradingView (Lightweight Charts™ v5) en 300 DPI y Alto Contraste.

Extrae velas en tiempo real desde MetaTrader 5 (o recibe un payload JSON por stdin),
calcula indicadores (EMA 50/100 a la vista; ATR 14 para medir la estructura), traza
canales de tendencia y swings mayores automáticos más las zonas de soporte y
resistencia del mensaje, y compila una imagen
PNG en ultra alta resolución (Retina / 300 DPI) usando Chromium headless (Playwright)
con polyfill de devicePixelContentBoxSize y paleta luminosa de marca Grupo Inteligencia.

Uso CLI directo:
    uv run python scripts/tradingview_grafico.py --ticker USDCLP --nombre "USD/CLP" --timeframe H1 --velas 320 --out data/stories/tv_usdclp.png

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


def calcular_indicadores(df_velas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Calcula EMAs 20/50/200, Bandas de Bollinger (20,2), Donchian 50, ATR 14, RSI 14 y ADX 14."""
    import math
    n = len(df_velas)
    if n == 0:
        return []

    cierres = [float(v["close"]) for v in df_velas]
    altos = [float(v["high"]) for v in df_velas]
    bajos = [float(v["low"]) for v in df_velas]

    # 1. EMAs
    def ema_series(valores: list[float], span: int) -> list[float | None]:
        if len(valores) < span:
            return [None] * len(valores)
        k = 2.0 / (span + 1.0)
        res: list[float | None] = [None] * (span - 1)
        prom = sum(valores[:span]) / span
        res.append(prom)
        for v in valores[span:]:
            prom = v * k + prom * (1.0 - k)
            res.append(prom)
        return res

    ema20 = ema_series(cierres, 20)
    ema50 = ema_series(cierres, 50)
    ema100 = ema_series(cierres, 100)
    ema200 = ema_series(cierres, 200)

    # 2. Bandas de Bollinger (20, 2)
    bb_upper: list[float | None] = []
    bb_lower: list[float | None] = []
    bb_mid: list[float | None] = []
    periodo_bb = 20
    for i in range(n):
        if i < periodo_bb - 1:
            bb_upper.append(None)
            bb_lower.append(None)
            bb_mid.append(None)
        else:
            ventana = cierres[i - periodo_bb + 1 : i + 1]
            sma = sum(ventana) / periodo_bb
            var = sum((x - sma) ** 2 for x in ventana) / periodo_bb
            std = math.sqrt(var)
            bb_mid.append(sma)
            bb_upper.append(sma + 2.0 * std)
            bb_lower.append(sma - 2.0 * std)

    # 3. Donchian 50
    don_high: list[float | None] = []
    don_low: list[float | None] = []
    periodo_don = 50
    for i in range(n):
        if i < periodo_don - 1:
            don_high.append(None)
            don_low.append(None)
        else:
            don_high.append(max(altos[i - periodo_don + 1 : i + 1]))
            don_low.append(min(bajos[i - periodo_don + 1 : i + 1]))

    # 4. ATR 14
    tr_list: list[float] = [altos[0] - bajos[0]]
    for i in range(1, n):
        tr = max(
            altos[i] - bajos[i],
            abs(altos[i] - cierres[i - 1]),
            abs(bajos[i] - cierres[i - 1]),
        )
        tr_list.append(tr)

    atr14: list[float | None] = [None] * 13
    if len(tr_list) >= 14:
        val = sum(tr_list[:14]) / 14.0
        atr14.append(val)
        for tr in tr_list[14:]:
            val = (val * 13.0 + tr) / 14.0
            atr14.append(val)
    else:
        atr14 = [None] * n

    # 5. RSI 14
    rsi14: list[float | None] = [None] * 14
    if n > 14:
        gains = []
        losses = []
        for i in range(1, n):
            delta = cierres[i] - cierres[i - 1]
            gains.append(max(0.0, delta))
            losses.append(max(0.0, -delta))

        avg_gain = sum(gains[:14]) / 14.0
        avg_loss = sum(losses[:14]) / 14.0
        if avg_loss == 0:
            rsi14.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi14.append(100.0 - (100.0 / (1.0 + rs)))

        for i in range(14, len(gains)):
            avg_gain = (avg_gain * 13.0 + gains[i]) / 14.0
            avg_loss = (avg_loss * 13.0 + losses[i]) / 14.0
            if avg_loss == 0:
                rsi14.append(100.0)
            else:
                rs = avg_gain / avg_loss
                rsi14.append(100.0 - (100.0 / (1.0 + rs)))

    # 6. ADX 14 (Average Directional Index)
    adx14: list[float | None] = [None] * n
    if n >= 28:
        plus_dm = [0.0]
        minus_dm = [0.0]
        for i in range(1, n):
            up_move = altos[i] - altos[i - 1]
            down_move = bajos[i - 1] - bajos[i]
            if up_move > down_move and up_move > 0:
                plus_dm.append(up_move)
            else:
                plus_dm.append(0.0)
            if down_move > up_move and down_move > 0:
                minus_dm.append(down_move)
            else:
                minus_dm.append(0.0)

        # Wilder's smoothing para TR, +DM, -DM
        smooth_tr = sum(tr_list[1:15])
        smooth_pdm = sum(plus_dm[1:15])
        smooth_mdm = sum(minus_dm[1:15])

        dx_list = []
        pdi = (smooth_pdm / smooth_tr) * 100.0 if smooth_tr > 0 else 0.0
        mdi = (smooth_mdm / smooth_tr) * 100.0 if smooth_tr > 0 else 0.0
        dx = (abs(pdi - mdi) / (pdi + mdi)) * 100.0 if (pdi + mdi) > 0 else 0.0
        dx_list.append((14, dx))

        for i in range(15, n):
            smooth_tr = smooth_tr - (smooth_tr / 14.0) + tr_list[i]
            smooth_pdm = smooth_pdm - (smooth_pdm / 14.0) + plus_dm[i]
            smooth_mdm = smooth_mdm - (smooth_mdm / 14.0) + minus_dm[i]
            pdi = (smooth_pdm / smooth_tr) * 100.0 if smooth_tr > 0 else 0.0
            mdi = (smooth_mdm / smooth_tr) * 100.0 if smooth_tr > 0 else 0.0
            dx = (abs(pdi - mdi) / (pdi + mdi)) * 100.0 if (pdi + mdi) > 0 else 0.0
            dx_list.append((i, dx))

        if len(dx_list) >= 14:
            first_14_dx = [d[1] for d in dx_list[:14]]
            adx_val = sum(first_14_dx) / 14.0
            idx_start = dx_list[13][0]
            adx14[idx_start] = adx_val
            for k in range(14, len(dx_list)):
                idx_k, dx_k = dx_list[k]
                adx_val = (adx_val * 13.0 + dx_k) / 14.0
                adx14[idx_k] = adx_val

    # Combinar todo
    resultado = []
    for i, v in enumerate(df_velas):
        t = v["time"]
        if isinstance(t, str):
            ts = int(
                datetime.fromisoformat(t.replace("Z", "+00:00"))
                .replace(tzinfo=timezone.utc)
                .timestamp()
            )
        elif isinstance(t, (int, float)):
            ts = int(t)
        else:
            ts = int(t.timestamp())

        fila = {
            "time": ts,
            "open": float(v["open"]),
            "high": float(v["high"]),
            "low": float(v["low"]),
            "close": float(v["close"]),
            "ema20": ema20[i] if i < len(ema20) else None,
            "ema50": ema50[i] if i < len(ema50) else None,
            "ema100": ema100[i] if i < len(ema100) else None,
            "ema200": ema200[i] if i < len(ema200) else None,
            "bollingerUpper": bb_upper[i] if i < len(bb_upper) else None,
            "bollingerLower": bb_lower[i] if i < len(bb_lower) else None,
            "bollingerMiddle": bb_mid[i] if i < len(bb_mid) else None,
            "donchianHigh": don_high[i] if i < len(don_high) else None,
            "donchianLow": don_low[i] if i < len(don_low) else None,
            "atr": atr14[i] if i < len(atr14) else None,
            "rsi": rsi14[i] if i < len(rsi14) else None,
            "adx": adx14[i] if i < len(adx14) else None,
        }
        resultado.append(fila)

    return resultado


def _zigzag(rows: list[dict[str, Any]], umbral: float) -> list[tuple[int, float, str]]:
    """Pivotes mayores: un giro cuenta cuando el precio retrocede `umbral` desde el extremo.

    Devuelve `(indice, precio, 'H'|'L')` en orden temporal. Es el mismo criterio que
    usa quien traza a mano: un máximo es máximo cuando el precio ya se alejó de él.
    """
    if not rows or umbral <= 0:
        return []
    pivotes: list[tuple[int, float, str]] = []
    dir_ = 0
    ext_i, ext_h, ext_l = 0, rows[0]["high"], rows[0]["low"]
    ext_hi_i, ext_lo_i = 0, 0
    for i, r in enumerate(rows):
        if dir_ >= 0:
            if r["high"] >= ext_h:
                ext_h, ext_hi_i = r["high"], i
            if dir_ == 1 and ext_h - r["low"] >= umbral:
                pivotes.append((ext_hi_i, ext_h, "H"))
                dir_, ext_l, ext_lo_i = -1, r["low"], i
                continue
        if dir_ <= 0:
            if r["low"] <= ext_l:
                ext_l, ext_lo_i = r["low"], i
            if dir_ == -1 and r["high"] - ext_l >= umbral:
                pivotes.append((ext_lo_i, ext_l, "L"))
                dir_, ext_h, ext_hi_i = 1, r["high"], i
                continue
        if dir_ == 0:
            if ext_h - r["low"] >= umbral and ext_hi_i < i:
                pivotes.append((ext_hi_i, ext_h, "H"))
                dir_, ext_l, ext_lo_i = -1, r["low"], i
            elif r["high"] - ext_l >= umbral and ext_lo_i < i:
                pivotes.append((ext_lo_i, ext_l, "L"))
                dir_, ext_h, ext_hi_i = 1, r["high"], i
    return pivotes


def _canal(rows: list[dict[str, Any]], i0: int, i1: int, direccion: int,
           proyeccion: int) -> list[list[tuple[int, float]]] | None:
    """Canal paralelo del tramo [i0, i1]: pendiente de la regresión de cierres, y dos
    rectas que envuelven los máximos y los mínimos del tramo.

    Los bordes se toman con percentiles (97/3) y no con el extremo absoluto, para
    que una sola mecha no ensanche el canal entero. Se descarta si la pendiente no
    tiene la dirección del tramo: eso es un rango, no un canal.
    """
    n = i1 - i0 + 1
    if n < 24:
        return None
    xs = list(range(i0, i1 + 1))
    ys = [rows[i]["close"] for i in xs]
    mx, my = sum(xs) / n, sum(ys) / n
    var = sum((x - mx) ** 2 for x in xs)
    if var == 0:
        return None
    pend = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / var
    if pend * direccion <= 0:
        return None
    res_h = sorted(rows[i]["high"] - pend * i for i in xs)
    res_l = sorted(rows[i]["low"] - pend * i for i in xs)
    b_sup = res_h[min(n - 1, int(n * 0.97))]
    b_inf = res_l[max(0, int(n * 0.03))]
    fin = i1 + proyeccion
    return [
        [(i0, pend * i0 + b_sup), (fin, pend * fin + b_sup)],
        [(i0, pend * i0 + b_inf), (fin, pend * fin + b_inf)],
    ]


def calcular_estructura(
    rows: list[dict[str, Any]],
    soporte: float | None = None,
    resistencia: float | None = None,
    proyeccion: int = 14,
) -> dict[str, Any]:
    """Canales de tendencia y swings mayores de la ventana visible, calculados.

    Tramos: el extremo más reciente de la ventana (máximo o mínimo absoluto) parte
    la serie en el tramo anterior y el tramo en curso, que es como se lee la
    referencia del director: un canal alcista hasta el techo y uno bajista desde
    ahí. Cada tramo lleva su canal solo si tiene pendiente en su dirección.

    Swings: pivotes del zigzag (umbral 3 x ATR H1) que no se pisan con el soporte ni
    la resistencia del mensaje, hasta dos por lado del precio.
    """
    n = len(rows)
    if n < 30:
        return {"canales": [], "swings": []}
    atrs = sorted(r["atr"] for r in rows if r.get("atr"))
    atr = atrs[len(atrs) // 2] if atrs else (max(r["high"] for r in rows) - min(r["low"] for r in rows)) / 50

    i_max = max(range(n), key=lambda i: rows[i]["high"])
    i_min = min(range(n), key=lambda i: rows[i]["low"])
    i_ult, i_prev = (i_max, i_min) if i_max > i_min else (i_min, i_max)
    dir_ult = -1 if i_ult == i_max else 1          # tras un máximo, el tramo baja
    canales: list[dict[str, Any]] = []
    actual = _canal(rows, i_ult, n - 1, dir_ult, proyeccion)
    if actual:
        previo = _canal(rows, i_prev, i_ult, -dir_ult, 0)
        if previo:
            canales.append({"direccion": -dir_ult, "lineas": previo})
        canales.append({"direccion": dir_ult, "lineas": actual})
    else:
        # El tramo en curso todavía no tiene velas para un canal propio: el precio
        # sigue leyéndose contra el canal anterior, que se proyecta a la derecha
        # desde el final de la serie para que se vea dónde está hoy.
        previo = _canal(rows, i_prev, n - 1, -dir_ult, proyeccion)
        if previo:
            canales.append({"direccion": -dir_ult, "lineas": previo})
        if i_prev >= 60:
            inicial = _canal(rows, 0, i_prev, dir_ult, 0)
            if inicial:
                canales.insert(0, {"direccion": dir_ult, "lineas": inicial})

    precio = rows[-1]["close"]
    ocupados = [p for p in (soporte, resistencia) if p is not None]
    arriba: list[float] = []
    abajo: list[float] = []
    for _, p, tipo in sorted(_zigzag(rows, 3.0 * atr), key=lambda t: -t[0]):
        if any(abs(p - q) < 0.8 * atr for q in ocupados + arriba + abajo):
            continue
        if p > precio and tipo == "H" and len(arriba) < 2:
            arriba.append(p)
        elif p < precio and tipo == "L" and len(abajo) < 2:
            abajo.append(p)
    return {"canales": canales, "swings": arriba + abajo, "atr": atr}


def construir_html_tradingview(
    rows: list[dict[str, Any]],
    simbolo: str,
    timeframe: str,
    digits: int = 2,
    soporte: float | None = None,
    resistencia: float | None = None,
    ancho: int = 1400,
    alto: int = 780,
) -> str:
    """HTML autocontenido del gráfico de estructura: velas, EMA 50/100, canales de
    tendencia, zonas de soporte y resistencia y swings mayores.

    Rediseño del 2026-09-30 a pedido del director, sobre su gráfico de referencia
    de MT5: ventana de semanas y no de horas, dos medias en vez de seis
    indicadores, y la estructura (canales y niveles) como protagonista. Se
    conserva la paleta oscura de marca.
    """
    if not VENDOR_JS.exists():
        raise TradingViewRenderError(f"No se encontró el vendor JS: {VENDOR_JS}")

    vendor_code = VENDOR_JS.read_text(encoding="utf-8")
    estructura = calcular_estructura(rows, soporte, resistencia)
    paso = 3600
    if len(rows) > 2:
        difs = sorted(rows[i + 1]["time"] - rows[i]["time"] for i in range(len(rows) - 1))
        paso = difs[len(difs) // 2] or 3600

    def t_de(i: int) -> int:
        return rows[i]["time"] if i < len(rows) else rows[-1]["time"] + (i - len(rows) + 1) * paso

    canales_js = [
        {"direccion": c["direccion"],
         "lineas": [[{"time": t_de(i), "value": v} for i, v in linea] for linea in c["lineas"]]}
        for c in estructura["canales"]
    ]
    zonas = [
        {"precio": p, "rol": rol}
        for p, rol in ((resistencia, "RESISTENCIA"), (soporte, "SOPORTE")) if p is not None
    ]
    datos = {
        "rows": rows,
        "canales": canales_js,
        "swings": estructura["swings"],
        "zonas": zonas,
        "media_zona": 0.18 * estructura.get("atr", 0),
        "digits": digits,
    }
    payload_json = json.dumps(datos, separators=(",", ":")).replace("</", "<\\/")

    fmt_p = f"{{:.{digits}f}}"
    last = rows[-1]
    e50_str = fmt_p.format(last["ema50"]) if last.get("ema50") is not None else "--"
    e100_str = fmt_p.format(last["ema100"]) if last.get("ema100") is not None else "--"
    p_close = fmt_p.format(last["close"])

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
    <div class="tv-legend">
      <span><span style="color:#00B0FF">●</span> EMA 50 <b style="color:#00B0FF">{e50_str}</b></span>
      <span><span style="color:#FFB300">●</span> EMA 100 <b style="color:#FFB300">{e100_str}</b></span>
    </div>
  </div>
  <div class="tv-chart-wrapper">
    <div id="chart-container"></div>
    <div id="zonas"></div>
  </div>
  <div class="tv-caption-bar">
    <span>{len(rows)} VELAS {timeframe} · FEED MT5 · GRUPO INTELIGENCIA</span>
    <span>EMA 50 · EMA 100 · CANALES DE TENDENCIA · ZONAS DE SOPORTE Y RESISTENCIA</span>
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

  linea('#00B0FF', 2, rows.filter(r => r.ema50 != null).map(r => ({{ time: r.time, value: r.ema50 }})));
  linea('#FFB300', 2, rows.filter(r => r.ema100 != null).map(r => ({{ time: r.time, value: r.ema100 }})));

  // Canales de tendencia: blanco, como el trazo del director sobre MT5.
  D.canales.forEach(c => c.lineas.forEach(l => linea('rgba(236, 240, 245, 0.92)', 2.4, l)));

  // Swings mayores: línea fina con su precio en el eje.
  D.swings.forEach(p => candles.createPriceLine({{
    price: p, color: 'rgba(203, 213, 225, 0.55)', lineWidth: 1,
    lineStyle: LightweightCharts.LineStyle.Solid, axisLabelVisible: true,
    axisLabelColor: '#334155', axisLabelTextColor: '#FFFFFF', title: '',
  }}));

  // Soporte y resistencia del mensaje: la zona amarilla y su precio en el eje.
  D.zonas.forEach(z => candles.createPriceLine({{
    price: z.precio, color: 'rgba(255, 213, 79, 0.0)', lineWidth: 1,
    axisLabelVisible: true, axisLabelColor: '#FFD54F', axisLabelTextColor: '#050B10',
    title: z.rol + ' ' + fmt(z.precio),
  }}));

  // Futuro en blanco para que el canal en curso se proyecte a la derecha.
  const extra = D.canales.flatMap(c => c.lineas.flatMap(l => l.map(p => p.time)))
    .filter(t => t > rows[rows.length - 1].time);
  const nFuturo = extra.length ? new Set(extra).size : 0;
  chart.timeScale().setVisibleLogicalRange({{ from: 0, to: rows.length + 12 }});

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
        buffer_png = page.screenshot(full_page=True)
        browser.close()

    # Guardar con metadatos 300 DPI explícitos vía Pillow
    imagen = Image.open(io.BytesIO(buffer_png))
    imagen.save(destino, dpi=(300, 300), quality=100)

    return destino


def generar_grafico_tv(
    ticker: str,
    nombre: str,
    destino: Path,
    timeframe: str = "H1",
    n_velas: int = 60,
    digits: int | None = None,
    soporte: float | None = None,
    resistencia: float | None = None,
    ancho: int = 1400,
    alto: int = 780,
) -> Path:
    """Función principal: obtiene datos de MT5, computa indicadores y renderiza el PNG."""
    from market_data_mcp import mt5_client
    from market_data_mcp.catalog import VALID_TICKERS

    if digits is None:
        digits = VALID_TICKERS.get(ticker, 2)

    mt5_client.connect()
    # Traemos velas extra para estabilización de EMA 200 y Donchian 50
    n_total = max(n_velas + 220, 260)
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
    )

    return renderizar_png(html, destino, ancho=ancho, alto=alto)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticker", default="")
    parser.add_argument("--nombre", default="")
    parser.add_argument("--timeframe", default="H1")
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
