#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Motor de renderizado de gráficos TradingView (Lightweight Charts™ v5) en 300 DPI y Alto Contraste.

Extrae velas en tiempo real desde MetaTrader 5 (o recibe un payload JSON por stdin),
calcula indicadores técnicos de alta fidelidad (EMAs 20/50/200, Canal Donchian 50,
ATR 14, RSI 14, y niveles de soporte/resistencia/operativa), y compila una imagen
PNG en ultra alta resolución (Retina / 300 DPI) usando Chromium headless (Playwright)
con polyfill de devicePixelContentBoxSize y paleta luminosa de marca Grupo Inteligencia.

Uso CLI directo:
    uv run python scripts/tradingview_grafico.py --ticker USDCLP --nombre "USD/CLP" --timeframe H1 --velas 60 --out data/stories/tv_usdclp.png

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
    """Calcula EMAs 20/50/200, Donchian 50, ATR 14 y RSI 14 sobre la lista de velas."""
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
    ema200 = ema_series(cierres, 200)

    # 2. Donchian 50
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

    # 3. ATR 14
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

    # 4. RSI 14
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
            "ema200": ema200[i] if i < len(ema200) else None,
            "donchianHigh": don_high[i] if i < len(don_high) else None,
            "donchianLow": don_low[i] if i < len(don_low) else None,
            "atr": atr14[i] if i < len(atr14) else None,
            "rsi": rsi14[i] if i < len(rsi14) else None,
        }
        resultado.append(fila)

    return resultado


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
    """Genera el código HTML autocontenido con LightweightCharts en alta fidelidad y contraste."""
    if not VENDOR_JS.exists():
        raise TradingViewRenderError(f"No se encontró el vendor JS: {VENDOR_JS}")

    vendor_code = VENDOR_JS.read_text(encoding="utf-8")
    payload_json = json.dumps(rows, separators=(",", ":")).replace("</", "<\\/")

    last = rows[-1]
    chg = ((last["close"] - last["open"]) / last["open"]) * 100 if last["open"] else 0.0
    chg_sign = "+" if chg >= 0 else ""
    chg_class = "up" if chg >= 0 else "down"

    fmt_p = f"{{:.{digits}f}}"
    p_open = fmt_p.format(last["open"])
    p_high = fmt_p.format(last["high"])
    p_low = fmt_p.format(last["low"])
    p_close = fmt_p.format(last["close"])

    e20_str = fmt_p.format(last["ema20"]) if last.get("ema20") is not None else "--"
    e50_str = fmt_p.format(last["ema50"]) if last.get("ema50") is not None else "--"
    e200_str = fmt_p.format(last["ema200"]) if last.get("ema200") is not None else "--"
    atr_str = f"{last['atr']:.2f}" if last.get("atr") is not None else "--"
    rsi_str = f"{last['rsi']:.1f}" if last.get("rsi") is not None else "--"

    dh_str = fmt_p.format(last["donchianHigh"]) if last.get("donchianHigh") is not None else "--"
    dl_str = fmt_p.format(last["donchianLow"]) if last.get("donchianLow") is not None else "--"

    # Líneas de niveles
    price_lines_js = []
    if resistencia is not None:
        price_lines_js.append(f"""
        candles.createPriceLine({{
            price: {resistencia},
            color: '#FF334B',
            lineWidth: 2.2,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            axisLabelVisible: true,
            axisLabelColor: '#FF334B',
            axisLabelTextColor: '#FFFFFF',
            title: 'RESISTENCIA: {fmt_p.format(resistencia)}',
        }});
        """)
    if soporte is not None:
        price_lines_js.append(f"""
        candles.createPriceLine({{
            price: {soporte},
            color: '#00E676',
            lineWidth: 2.2,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            axisLabelVisible: true,
            axisLabelColor: '#00E676',
            axisLabelTextColor: '#050B10',
            title: 'SOPORTE: {fmt_p.format(soporte)}',
        }});
        """)

    lineas_extra = "\n".join(price_lines_js)

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
    width: {ancho}px;
    height: {alto}px;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    padding: 12px;
  }}
  .tv-container {{
    display: flex;
    flex-direction: column;
    width: 100%;
    height: 100%;
    background: #070D14;
    border: 1.5px solid rgba(80, 192, 168, 0.55);
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.75), inset 0 1px 0 rgba(255, 255, 255, 0.15);
  }}
  .tv-topbar {{
    height: 52px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #0C1620;
    border-bottom: 1.5px solid rgba(80, 192, 168, 0.35);
    padding: 0 24px;
    font-size: 14px;
    flex-shrink: 0;
  }}
  .tv-topbar-left {{
    display: flex;
    align-items: center;
    gap: 14px;
  }}
  .tv-symbol {{
    color: #FFFFFF;
    font-weight: 800;
    font-size: 20px;
    letter-spacing: 0.04em;
  }}
  .tv-badge-tf {{
    background: rgba(80, 192, 168, 0.25);
    color: #50C0A8;
    border: 1.5px solid #50C0A8;
    padding: 3px 10px;
    border-radius: 6px;
    font-weight: 800;
    font-size: 13px;
    letter-spacing: 0.05em;
  }}
  .tv-badge-feed {{
    background: rgba(0, 230, 118, 0.15);
    color: #00E676;
    border: 1.5px solid rgba(0, 230, 118, 0.5);
    padding: 4px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.06em;
    display: inline-flex;
    align-items: center;
    gap: 7px;
  }}
  .tv-badge-feed::before {{
    content: "";
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #00E676;
    box-shadow: 0 0 10px #00E676;
  }}
  .tv-ohlc {{
    display: inline-flex;
    gap: 12px;
    font-size: 14px;
    color: #CBD5E1;
    margin-left: 12px;
    font-family: 'Space Grotesk', monospace;
  }}
  .tv-ohlc strong {{ color: #FFFFFF; font-weight: 700; }}
  .tv-ohlc .up {{ color: #00E676; font-weight: 800; }}
  .tv-ohlc .down {{ color: #FF334B; font-weight: 800; }}

  .tv-brand-tv {{
    display: flex;
    align-items: center;
    gap: 8px;
    color: #CBD5E1;
    font-size: 13px;
    font-weight: 800;
    letter-spacing: 0.08em;
  }}
  .tv-brand-tv svg {{ fill: #50C0A8; filter: drop-shadow(0 0 6px rgba(80, 192, 168, 0.6)); }}

  .tv-legend {{
    height: 38px;
    display: flex;
    align-items: center;
    gap: 20px;
    padding: 0 24px;
    background: #09121B;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    font-size: 13px;
    font-family: 'Space Grotesk', monospace;
    flex-shrink: 0;
  }}
  .tv-legend-item {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
  }}
  .tv-dot {{
    width: 9px;
    height: 9px;
    border-radius: 50%;
  }}

  .tv-chart-wrapper {{
    position: relative;
    flex: 1;
    min-height: 0;
    width: 100%;
    background: #070D14;
  }}
  #chart-container {{
    width: 100%;
    height: 100%;
    display: block;
  }}

  .tv-caption-bar {{
    height: 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 24px;
    background: #050A0F;
    border-top: 1.5px solid rgba(80, 192, 168, 0.3);
    font-size: 12px;
    color: #94A3B8;
    font-family: 'Space Grotesk', monospace;
    font-weight: 600;
    flex-shrink: 0;
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
        const patchedEntries = entries.map(e => {{
          if (e.devicePixelContentBoxSize) {{
            const s = e.devicePixelContentBoxSize[0];
            const cs = e.contentBoxSize ? e.contentBoxSize[0] : s;
            return new Proxy(e, {{
              get(target, prop) {{
                if (prop === 'devicePixelContentBoxSize') {{
                  return [{{
                    inlineSize: Math.round(cs.inlineSize * dpr),
                    blockSize: Math.round(cs.blockSize * dpr)
                  }}];
                }}
                return target[prop];
              }}
            }});
          }}
          return e;
        }});
        cb(patchedEntries, obs);
      }});
    }}
  }};
}})();
</script>
</head>
<body>

<div class="tv-container" data-chart-ready="false">
  <!-- Topbar -->
  <div class="tv-topbar">
    <div class="tv-topbar-left">
      <span class="tv-symbol">{simbolo}</span>
      <span class="tv-badge-tf">{timeframe}</span>
      <span class="tv-badge-feed">FEED EN VIVO · METATRADER 5 OFICIAL</span>
      <div class="tv-ohlc">
        <span>O: <strong>{p_open}</strong></span>
        <span>H: <strong>{p_high}</strong></span>
        <span>L: <strong>{p_low}</strong></span>
        <span>C: <strong class="{chg_class}">{p_close}</strong></span>
        <span class="{chg_class}">({chg_sign}{chg:.2f}%)</span>
      </div>
    </div>
    <div class="tv-brand-tv">
      <svg width="20" height="15" viewBox="0 0 36 28">
        <path d="M14 22H7V11H14V22ZM21 22H15V6H21V22ZM28 22H22V16H28V22Z"/>
      </svg>
      <span>TRADINGVIEW™ ENGINE · 300 DPI</span>
    </div>
  </div>

  <!-- Legend Bar -->
  <div class="tv-legend">
    <div class="tv-legend-item">
      <span class="tv-dot" style="background: #00E676; box-shadow: 0 0 6px #00E676;"></span>
      <span style="color: #CBD5E1;">EMA 20:</span>
      <span style="color: #00E676; font-weight: 800;">{e20_str}</span>
    </div>
    <div class="tv-legend-item">
      <span class="tv-dot" style="background: #00B0FF; box-shadow: 0 0 6px #00B0FF;"></span>
      <span style="color: #CBD5E1;">EMA 50:</span>
      <span style="color: #00B0FF; font-weight: 800;">{e50_str}</span>
    </div>
    <div class="tv-legend-item">
      <span class="tv-dot" style="background: #90A4AE;"></span>
      <span style="color: #CBD5E1;">EMA 200:</span>
      <span style="color: #ECEFF1; font-weight: 800;">{e200_str}</span>
    </div>
    <div class="tv-legend-item">
      <span class="tv-dot" style="background: #00E5FF;"></span>
      <span style="color: #CBD5E1;">Donchian (50):</span>
      <span style="color: #00E5FF; font-weight: 700;">[{dl_str}, {dh_str}]</span>
    </div>
    <div class="tv-legend-item">
      <span class="tv-dot" style="background: #FFD54F;"></span>
      <span style="color: #CBD5E1;">ATR (14):</span>
      <span style="color: #FFD54F; font-weight: 800;">{atr_str}</span>
    </div>
    <div class="tv-legend-item" style="margin-left: auto;">
      <span class="tv-dot" style="background: #FF4081; box-shadow: 0 0 6px #FF4081;"></span>
      <span style="color: #CBD5E1;">RSI (14):</span>
      <span style="color: #FF80AB; font-weight: 800;">{rsi_str}</span>
    </div>
  </div>

  <!-- Main Multi-pane Chart -->
  <div class="tv-chart-wrapper">
    <div id="chart-container"></div>
  </div>

  <!-- Caption Footer -->
  <div class="tv-caption-bar">
    <span>{len(rows)} VELAS {timeframe} · MOTOR TRADINGVIEW™ · FEED MT5 GRUPO INTELIGENCIA</span>
    <span>EMAS 20/50/200 · CANAL DONCHIAN 50 · OSCILADOR RSI 14 (70/30)</span>
  </div>
</div>

<script>{vendor_code}</script>

<script>
(() => {{
  const rows = {payload_json};
  const container = document.getElementById('chart-container');
  if (!container || typeof LightweightCharts === 'undefined') return;

  const chart = LightweightCharts.createChart(container, {{
    autoSize: true,
    layout: {{
      background: {{ type: 'solid', color: '#070D14' }},
      textColor: '#CBD5E1',
      fontSize: 12,
      fontFamily: "'Space Grotesk', 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif",
      panes: {{
        enableResize: false,
        separatorColor: 'rgba(80, 192, 168, 0.4)',
        separatorHoverColor: 'rgba(80, 192, 168, 0.7)',
      }},
    }},
    grid: {{
      vertLines: {{ color: 'rgba(255, 255, 255, 0.05)' }},
      horzLines: {{ color: 'rgba(255, 255, 255, 0.05)' }},
    }},
    rightPriceScale: {{
      borderColor: 'rgba(80, 192, 168, 0.25)',
      scaleMargins: {{ top: 0.10, bottom: 0.10 }},
      autoScale: true,
      alignLabels: true,
    }},
    timeScale: {{
      borderColor: 'rgba(80, 192, 168, 0.25)',
      timeVisible: true,
      secondsVisible: false,
      rightOffset: 5,
      barSpacing: 14,
      minBarSpacing: 6,
      tickMarkFormatter: (time) => {{
        const date = new Date(time * 1000);
        const d = String(date.getUTCDate()).padStart(2, '0');
        const m = date.toLocaleString('es-CL', {{ month: 'short', timeZone: 'UTC' }}).replace('.', '');
        const h = String(date.getUTCHours()).padStart(2, '0');
        return `${{d}} ${{m}} ${{h}}:00`;
      }},
    }},
    crosshair: {{
      mode: LightweightCharts.CrosshairMode.Normal,
      vertLine: {{ color: 'rgba(80, 192, 168, 0.45)', width: 1.5, style: 2 }},
      horzLine: {{ color: 'rgba(80, 192, 168, 0.45)', width: 1.5, style: 2 }},
    }},
  }});

  // Panel 0: Velas Japonesas
  const candles = chart.addSeries(LightweightCharts.CandlestickSeries, {{
    upColor: '#00E676',
    downColor: '#FF334B',
    borderUpColor: '#00E676',
    borderDownColor: '#FF334B',
    wickUpColor: '#00E676',
    wickDownColor: '#FF334B',
    priceFormat: {{ type: 'price', precision: {digits}, minMove: {10**(-digits)} }},
    lastValueVisible: true,
    priceLineVisible: true,
    priceLineColor: '#00E676',
    priceLineWidth: 1.5,
    priceLineStyle: LightweightCharts.LineStyle.Dotted,
  }}, 0);

  candles.setData(rows.map(r => ({{
    time: r.time, open: r.open, high: r.high, low: r.low, close: r.close
  }})));

  {lineas_extra}

  // Medias Móviles
  const ema20 = chart.addSeries(LightweightCharts.LineSeries, {{
    color: '#00E676',
    lineWidth: 2.2,
    lineStyle: LightweightCharts.LineStyle.Solid,
    lastValueVisible: false,
    priceLineVisible: false,
  }}, 0);
  ema20.setData(rows.filter(r => r.ema20 != null).map(r => ({{ time: r.time, value: r.ema20 }})));

  const ema50 = chart.addSeries(LightweightCharts.LineSeries, {{
    color: '#00B0FF',
    lineWidth: 2.0,
    lineStyle: LightweightCharts.LineStyle.Solid,
    lastValueVisible: false,
    priceLineVisible: false,
  }}, 0);
  ema50.setData(rows.filter(r => r.ema50 != null).map(r => ({{ time: r.time, value: r.ema50 }})));

  const ema200 = chart.addSeries(LightweightCharts.LineSeries, {{
    color: '#90A4AE',
    lineWidth: 1.8,
    lineStyle: LightweightCharts.LineStyle.Solid,
    lastValueVisible: false,
    priceLineVisible: false,
  }}, 0);
  ema200.setData(rows.filter(r => r.ema200 != null).map(r => ({{ time: r.time, value: r.ema200 }})));

  // Donchian Bands
  const donHigh = chart.addSeries(LightweightCharts.LineSeries, {{
    color: 'rgba(0, 229, 255, 0.75)',
    lineWidth: 1.2,
    lineStyle: LightweightCharts.LineStyle.Dashed,
    lastValueVisible: false,
    priceLineVisible: false,
  }}, 0);
  donHigh.setData(rows.filter(r => r.donchianHigh != null).map(r => ({{ time: r.time, value: r.donchianHigh }})));

  const donLow = chart.addSeries(LightweightCharts.LineSeries, {{
    color: 'rgba(0, 229, 255, 0.75)',
    lineWidth: 1.2,
    lineStyle: LightweightCharts.LineStyle.Dashed,
    lastValueVisible: false,
    priceLineVisible: false,
  }}, 0);
  donLow.setData(rows.filter(r => r.donchianLow != null).map(r => ({{ time: r.time, value: r.donchianLow }})));

  // Panel 1: Oscilador RSI 14
  const rsiGuide70 = chart.addSeries(LightweightCharts.LineSeries, {{
    color: 'rgba(255, 51, 75, 0.55)',
    lineWidth: 1.2,
    lineStyle: LightweightCharts.LineStyle.Dashed,
    lastValueVisible: false,
    priceLineVisible: false,
  }}, 1);
  rsiGuide70.setData(rows.map(r => ({{ time: r.time, value: 70 }})));

  const rsiGuide30 = chart.addSeries(LightweightCharts.LineSeries, {{
    color: 'rgba(0, 230, 118, 0.55)',
    lineWidth: 1.2,
    lineStyle: LightweightCharts.LineStyle.Dashed,
    lastValueVisible: false,
    priceLineVisible: false,
  }}, 1);
  rsiGuide30.setData(rows.map(r => ({{ time: r.time, value: 30 }})));

  const rsiLine = chart.addSeries(LightweightCharts.LineSeries, {{
    color: '#FF4081',
    lineWidth: 2.0,
    lastValueVisible: true,
    priceLineVisible: false,
    priceFormat: {{ type: 'price', precision: 1, minMove: 0.1 }},
  }}, 1);
  rsiLine.setData(rows.filter(r => r.rsi != null).map(r => ({{ time: r.time, value: r.rsi }})));

  // Proporciones Panel 0 (Velas) vs Panel 1 (RSI)
  const panes = chart.panes();
  if (panes && panes.length > 1) {{
    panes[0].setStretchFactor(3.2);
    panes[1].setStretchFactor(1.0);
  }}

  chart.timeScale().setVisibleLogicalRange({{ from: -2, to: rows.length + 4 }});
  document.querySelector('.tv-container').dataset.chartReady = 'true';
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
