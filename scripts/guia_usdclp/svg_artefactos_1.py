# punto-de-entrada: script ad-hoc de mantenimiento y compilación
# -*- coding: utf-8 -*-
"""Artefactos visuales vectoriales para la Guía USD/CLP (Parte 1)."""

def svg_flujo_mercado(forward: str) -> str:
    return """
<div class="contenedor-diagrama">
<svg viewBox="0 0 680 145" xmlns="http://www.w3.org/2000/svg">
  <rect width="680" height="145" rx="8" fill="#0A181C" stroke="rgba(83, 193, 171, 0.25)" stroke-width="1.2"/>
  
  <text x="20" y="22" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="11" font-weight="700" letter-spacing="0.1em">MECANISMO INSTITUCIONAL · CADENA DE FORMACIÓN DE PRECIOS USD/CLP</text>
  <line x1="20" y1="28" x2="660" y2="28" stroke="rgba(83, 193, 171, 0.2)" stroke-width="1"/>

  <rect x="20" y="38" width="180" height="66" rx="6" fill="#0E232A" stroke="#53C1AB" stroke-width="1.2"/>
  <text x="30" y="54" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="11" font-weight="700">OFERTA DE USD (VENTA)</text>
  <text x="30" y="69" fill="#E2E8F0" font-family="'Plus Jakarta Sans', sans-serif" font-size="10" font-weight="600">· Gran Minería (Codelco / Priv)</text>
  <text x="30" y="83" fill="#94A3B8" font-family="'Plus Jakarta Sans', sans-serif" font-size="9.5">· Liquidaciones Hacienda</text>
  <text x="30" y="96" fill="#94A3B8" font-family="'Plus Jakarta Sans', sans-serif" font-size="9.5">· Exportadores Agrícolas</text>

  <rect x="240" y="34" width="200" height="74" rx="6" fill="#132E37" stroke="#3E91AF" stroke-width="1.5"/>
  <text x="250" y="51" fill="#FFFFFF" font-family="'Goldman', sans-serif" font-size="11" font-weight="700">MERCADO INTERBANCARIO</text>
  <text x="250" y="66" fill="#67E8F9" font-family="'Space Grotesk', monospace" font-size="10" font-weight="700">SIF / DATATEC (09:00 - 13:30)</text>
  <text x="250" y="82" fill="#E2E8F0" font-family="'Plus Jakarta Sans', sans-serif" font-size="9.5">Costos de transacción según liquidez</text>
  <text x="250" y="98" fill="#FBBF24" font-family="'Space Grotesk', monospace" font-size="9.5" font-weight="700">Fixing BCCh 13:30 (Dólar Obs.)</text>

  <rect x="480" y="38" width="180" height="66" rx="6" fill="#0E232A" stroke="#E76F51" stroke-width="1.2"/>
  <text x="490" y="54" fill="#E76F51" font-family="'Space Grotesk', monospace" font-size="11" font-weight="700">DEMANDA DE USD (COMPRA)</text>
  <text x="490" y="69" fill="#E2E8F0" font-family="'Plus Jakarta Sans', sans-serif" font-size="10" font-weight="600">· Importadores Combustible (ENAP)</text>
  <text x="490" y="83" fill="#94A3B8" font-family="'Plus Jakarta Sans', sans-serif" font-size="9.5">· AFPs Rebalanceo Fondo A/B</text>
  <text x="490" y="96" fill="#94A3B8" font-family="'Plus Jakarta Sans', sans-serif" font-size="9.5">· Comercio Mayorista & Retail</text>

  <rect x="20" y="114" width="640" height="24" rx="4" fill="#071317" stroke="rgba(255, 255, 255, 0.08)" stroke-width="1"/>
  <text x="30" y="130" fill="#94A3B8" font-family="'Space Grotesk', monospace" font-size="9">ARBITRAJE OFF-SHORE Y DERIVADOS:</text>
  <text x="225" y="130" fill="#67E8F9" font-family="'Space Grotesk', monospace" font-size="9.5" font-weight="700">Posición Neta Forward No Residentes: {{forward}}M USD (Presión Compradora de   Dólar)</text>
</svg>
</div>
""".replace("{{forward}}", forward)

def svg_balancin_cobre(copper: str) -> str:
    return """
<div class="contenedor-diagrama">
<svg viewBox="0 0 680 145" xmlns="http://www.w3.org/2000/svg">
  <rect width="680" height="145" rx="8" fill="#0A181C" stroke="rgba(83, 193, 171, 0.25)" stroke-width="1.2"/>
  
  <text x="20" y="22" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="11" font-weight="700" letter-spacing="0.1em">RELACIÓN INTERMERCADO: SEÑAL, NO CERTEZA</text>
  <line x1="20" y1="28" x2="660" y2="28" stroke="rgba(83, 193, 171, 0.2)" stroke-width="1"/>

  <rect x="20" y="36" width="305" height="98" rx="6" fill="#0E232A" stroke="#53C1AB" stroke-width="1.2"/>
  <rect x="28" y="43" width="120" height="19" rx="3" fill="rgba(83, 193, 171, 0.2)"/>
  <text x="34" y="57" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="10.5" font-weight="700">▲ COBRE EN ALZA</text>
  <text x="155" y="57" fill="#67E8F9" font-family="'Space Grotesk', monospace" font-size="10.5" font-weight="700">SPOT: ${{copper}} USD/t</text>
  
  <text x="28" y="78" fill="#E2E8F0" font-family="'Plus Jakarta Sans', sans-serif" font-size="10">· Mayor recaudación fiscal minera</text>
  <text x="28" y="93" fill="#E2E8F0" font-family="'Plus Jakarta Sans', sans-serif" font-size="10">· Ingreso masivo de dólares a Santiago</text>
  
  <rect x="28" y="104" width="289" height="22" rx="3" fill="#061215" stroke="#53C1AB" stroke-width="0.8"/>
  <text x="36" y="119" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="10" font-weight="700">EFECTO: PESO SE APRECIA ➔ USD/CLP CAE</text>

  <circle cx="340" cy="85" r="13" fill="#132E37" stroke="#3E91AF" stroke-width="1.5"/>
  <text x="340" y="89" text-anchor="middle" fill="#FFFFFF" font-family="'Goldman', sans-serif" font-size="10.5" font-weight="700">VS</text>

  <rect x="355" y="36" width="305" height="98" rx="6" fill="#0E232A" stroke="#E76F51" stroke-width="1.2"/>
  <rect x="363" y="43" width="120" height="19" rx="3" fill="rgba(231, 111, 81, 0.2)"/>
  <text x="369" y="57" fill="#E76F51" font-family="'Space Grotesk', monospace" font-size="10.5" font-weight="700">▼ COBRE A LA BAJA</text>
  <text x="490" y="57" fill="#94A3B8" font-family="'Space Grotesk', monospace" font-size="9.5">ESTRÉS COMERCIAL</text>

  <text x="363" y="78" fill="#E2E8F0" font-family="'Plus Jakarta Sans', sans-serif" font-size="10">· Menor liquidación de divisas</text>
  <text x="363" y="93" fill="#E2E8F0" font-family="'Plus Jakarta Sans', sans-serif" font-size="10">· Déficit en cuenta corriente proyectado</text>

  <rect x="363" y="104" width="289" height="22" rx="3" fill="#061215" stroke="#E76F51" stroke-width="0.8"/>
  <text x="371" y="119" fill="#E76F51" font-family="'Space Grotesk', monospace" font-size="10" font-weight="700">EFECTO: DÓLAR SE ENCARECE ➔ USD/CLP SUBE</text>
</svg>
</div>
""".replace("{{copper}}", copper)

def svg_matriz_cuadrantes(tpm: str, fed: str) -> str:
    return """
<div class="contenedor-diagrama">
<svg viewBox="0 0 680 150" xmlns="http://www.w3.org/2000/svg">
  <rect width="680" height="150" rx="8" fill="#0A181C" stroke="rgba(83, 193, 171, 0.25)" stroke-width="1.2"/>
  
  <text x="20" y="22" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="11" font-weight="700" letter-spacing="0.1em">MATRIZ DE POLÍTICA MONETARIA · DIFERENCIAL BCCH ({{tpm}}%) VS FED ({{fed}}%)</text>
  <line x1="20" y1="28" x2="660" y2="28" stroke="rgba(83, 193, 171, 0.2)" stroke-width="1"/>

  <rect x="20" y="35" width="310" height="50" rx="4" fill="#1C1414" stroke="#E76F51" stroke-width="1"/>
  <text x="30" y="50" fill="#E76F51" font-family="'Space Grotesk', monospace" font-size="10" font-weight="700">1. BCCh DOVISH (RECORTA) + FED HAWKISH</text>
  <text x="30" y="64" fill="#E2E8F0" font-family="'Plus Jakarta Sans', sans-serif" font-size="9">El diferencial se destruye. Desarme de Carry Trade.</text>
  <text x="30" y="77" fill="#F87171" font-family="'Space Grotesk', monospace" font-size="9.5" font-weight="700">➔ MÁXIMA PRESIÓN ALCISTA EN USD/CLP</text>

  <rect x="345" y="35" width="315" height="50" rx="4" fill="#0E232A" stroke="rgba(83, 193, 171, 0.4)" stroke-width="1"/>
  <text x="355" y="50" fill="#67E8F9" font-family="'Space Grotesk', monospace" font-size="10" font-weight="700">2. BCCh HAWKISH + FED HAWKISH</text>
  <text x="355" y="64" fill="#E2E8F0" font-family="'Plus Jakarta Sans', sans-serif" font-size="9">Tasas altas globales. Contracción del crédito y liquidez.</text>
  <text x="355" y="77" fill="#94A3B8" font-family="'Space Grotesk', monospace" font-size="9.5" font-weight="700">➔ LATERALIZACIÓN POR PARIDAD DE FUERZAS</text>

  <rect x="20" y="90" width="310" height="52" rx="4" fill="#0E232A" stroke="rgba(83, 193, 171, 0.4)" stroke-width="1"/>
  <text x="30" y="105" fill="#94A3B8" font-family="'Space Grotesk', monospace" font-size="10" font-weight="700">3. BCCh DOVISH + FED DOVISH</text>
  <text x="30" y="119" fill="#E2E8F0" font-family="'Plus Jakarta Sans', sans-serif" font-size="9">Inyección de liquidez global. Emergentes reciben flujos.</text>
  <text x="30" y="133" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="9.5" font-weight="700">➔ TENDENCIA DEPENDIENTE DEL CICLO DEL COBRE</text>

  <rect x="345" y="90" width="315" height="52" rx="4" fill="#0E2A22" stroke="#53C1AB" stroke-width="1.2"/>
  <text x="355" y="105" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="10" font-weight="700">4. BCCh HAWKISH + FED DOVISH (RECORTA)</text>
  <text x="355" y="119" fill="#E2E8F0" font-family="'Plus Jakarta Sans', sans-serif" font-size="9">Spread se amplía a favor de Chile, según la lectura vigente.</text>
  <text x="355" y="133" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="9.5" font-weight="700">➔ MÁXIMA PRESIÓN BAJISTA EN USD/CLP (PESO FUERTE)</text>
</svg>
</div>
""".replace("{{tpm}}", tpm).replace("{{fed}}", fed)

def svg_grafico_tradingview_h1(datos: dict[str, object], lightweight_js: str) -> str:
    from datetime import datetime, timezone
    import json

    rows = [row for row in datos["rows"][-80:] if row["high"] >= row["low"]]
    chart_rows = [
        {
            "time": int(
                datetime.fromisoformat(row["time"].replace("Z", "+00:00"))
                .replace(tzinfo=timezone.utc)
                .timestamp()
            ),
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"],
            "ema50": row.get("ema_50"),
            "ema200": row.get("ema_200"),
            "donchianHigh": row.get("donchian_50_high"),
            "donchianLow": row.get("donchian_50_low"),
            "rsi": row.get("rsi_14"),
        }
        for row in rows
    ]
    payload = json.dumps(chart_rows, separators=(",", ":")).replace("</", "<\\/")
    last_row = rows[-1]
    chg = ((last_row["close"] - last_row["open"]) / last_row["open"]) * 100
    chg_sign = "+" if chg >= 0 else ""
    chg_class = "up" if chg >= 0 else "down"

    return f"""
<div class="contenedor-diagrama chart-tv" data-chart-ready="false">
  <!-- Topbar TradingView Oficial con Feed Grupo Inteligencia -->
  <div class="chart-tv-topbar">
    <div class="chart-tv-topbar-left">
      <span class="chart-tv-symbol">USD/CLP</span>
      <span class="chart-tv-badge-tf">1H</span>
      <span class="chart-tv-badge-feed">FEED GRUPO INTELIGENCIA</span>
      <div class="chart-tv-ohlc">
        <span>O: <strong>{last_row["open"]:.2f}</strong></span>
        <span>H: <strong>{last_row["high"]:.2f}</strong></span>
        <span>L: <strong>{last_row["low"]:.2f}</strong></span>
        <span>C: <strong class="{chg_class}">{last_row["close"]:.2f}</strong></span>
        <span class="{chg_class}">({chg_sign}{chg:.2f}%)</span>
      </div>
    </div>
    <div class="chart-tv-brand-tv">
      <svg width="15" height="11" viewBox="0 0 36 28" fill="#53C1AB" style="vertical-align: middle; margin-right: 4px;">
        <path d="M14 22H7V11H14V22ZM21 22H15V6H21V22ZM28 22H22V16H28V22Z"/>
      </svg>
      <span>TRADINGVIEW™ CHARTS</span>
    </div>
  </div>

  <!-- Barra de Indicadores y Niveles Canónicos -->
  <div class="chart-tv-legend">
    <div class="chart-tv-legend-item">
      <span class="chart-tv-dot" style="background: #53C1AB;"></span>
      <span class="chart-tv-leg-lbl">EMA 50:</span>
      <span class="chart-tv-leg-val" style="color: #53C1AB;">{datos["ema50"]}</span>
    </div>
    <div class="chart-tv-legend-item">
      <span class="chart-tv-dot" style="background: #E76F51;"></span>
      <span class="chart-tv-leg-lbl">EMA 200:</span>
      <span class="chart-tv-leg-val" style="color: #E76F51;">{datos["ema200"]}</span>
    </div>
    <div class="chart-tv-legend-item">
      <span class="chart-tv-dot" style="background: #3E91AF;"></span>
      <span class="chart-tv-leg-lbl">Donchian (50):</span>
      <span class="chart-tv-leg-val" style="color: #67E8F9;">[{datos["donchian_low"]}, {datos["donchian_high"]}]</span>
    </div>
    <div class="chart-tv-legend-item">
      <span class="chart-tv-dot" style="background: #FBBF24;"></span>
      <span class="chart-tv-leg-lbl">ATR (14):</span>
      <span class="chart-tv-leg-val" style="color: #FBBF24;">{datos["atr_h1"]}</span>
    </div>
    <div class="chart-tv-legend-item" style="margin-left: auto;">
      <span class="chart-tv-dot" style="background: #F08063;"></span>
      <span class="chart-tv-leg-lbl">RSI (14):</span>
      <span class="chart-tv-leg-val" style="color: #F08063;">{datos["rsi_h1"]}</span>
    </div>
  </div>

  <!-- Canvas Multi-panel Unificado (Panel 0: Velas y Medias, Panel 1: RSI) -->
  <div class="chart-tv-wrapper">
    <div id="usdclp-tv-chart" class="chart-tv-canvas"></div>
  </div>

  <!-- Pie Institucional del Gráfico -->
  <div class="chart-tv-caption">
    <span class="chart-tv-caption-left">80 velas H1 · Motor TradingView · Feed de datos en tiempo real Grupo Inteligencia</span>
    <span class="chart-tv-caption-right">Canal Donchian 50 (R1/S1) · Oscilador RSI 14 (70/30)</span>
  </div>

  <script>
  (() => {{
    const rows = {payload};
    const container = document.getElementById('usdclp-tv-chart');
    if (!container) return;

    const chart = LightweightCharts.createChart(container, {{
      width: 680,
      height: 235,
      layout: {{
        background: {{ type: 'solid', color: '#071317' }},
        textColor: '#94A3B8',
        fontSize: 10,
        fontFamily: "'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif",
        panes: {{
          enableResize: false,
          separatorColor: 'rgba(83, 193, 171, 0.25)',
          separatorHoverColor: 'rgba(83, 193, 171, 0.4)',
        }},
      }},
      grid: {{
        vertLines: {{ color: 'rgba(255, 255, 255, 0.03)' }},
        horzLines: {{ color: 'rgba(255, 255, 255, 0.03)' }},
      }},
      rightPriceScale: {{
        borderColor: 'rgba(255, 255, 255, 0.08)',
        scaleMargins: {{ top: 0.12, bottom: 0.12 }},
        autoScale: true,
        alignLabels: true,
      }},
      timeScale: {{
        borderColor: 'rgba(255, 255, 255, 0.08)',
        timeVisible: true,
        secondsVisible: false,
        rightOffset: 8,
        barSpacing: 7.5,
        minBarSpacing: 4,
        tickMarkFormatter: (time) => {{
          const date = new Date(time * 1000);
          const d = String(date.getUTCDate()).padStart(2, '0');
          const m = date.toLocaleString('es-CL', {{ month: 'short', timeZone: 'UTC' }}).replace('.', '');
          return `${{d}} ${{m}}`;
        }},
      }},
      crosshair: {{
        mode: LightweightCharts.CrosshairMode.Normal,
        vertLine: {{ color: 'rgba(83, 193, 171, 0.35)', width: 1, style: 2 }},
        horzLine: {{ color: 'rgba(83, 193, 171, 0.35)', width: 1, style: 2 }},
      }},
    }});

    // Panel 0: Velas Japonesas con paleta canónica TradingView Pine / Brandkit
    const candles = chart.addSeries(LightweightCharts.CandlestickSeries, {{
      upColor: '#089981',
      downColor: '#F23645',
      borderUpColor: '#089981',
      borderDownColor: '#F23645',
      wickUpColor: '#089981',
      wickDownColor: '#F23645',
      priceFormat: {{ type: 'price', precision: 2, minMove: 0.01 }},
      lastValueVisible: true,
      priceLineVisible: true,
      priceLineColor: '#089981',
      priceLineWidth: 1,
      priceLineStyle: LightweightCharts.LineStyle.Dotted,
    }}, 0);

    candles.setData(rows.map(r => ({{
      time: r.time, open: r.open, high: r.high, low: r.low, close: r.close
    }})));

    // Panel 0: Medias Móviles Exponenciales (líneas finas institucionales 1.5px)
    const ema50 = chart.addSeries(LightweightCharts.LineSeries, {{
      color: '#53C1AB',
      lineWidth: 1.5,
      lineStyle: LightweightCharts.LineStyle.Solid,
      lastValueVisible: false,
      priceLineVisible: false,
      title: '',
    }}, 0);
    ema50.setData(rows.filter(r => r.ema50 != null).map(r => ({{ time: r.time, value: r.ema50 }})));

    const ema200 = chart.addSeries(LightweightCharts.LineSeries, {{
      color: '#E76F51',
      lineWidth: 1.5,
      lineStyle: LightweightCharts.LineStyle.Solid,
      lastValueVisible: false,
      priceLineVisible: false,
      title: '',
    }}, 0);
    ema200.setData(rows.filter(r => r.ema200 != null).map(r => ({{ time: r.time, value: r.ema200 }})));

    // Panel 0: Bandas Donchian 50 (Resistencia R1 y Soporte S1 sutiles)
    const donHigh = chart.addSeries(LightweightCharts.LineSeries, {{
      color: 'rgba(62, 145, 175, 0.7)',
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      lastValueVisible: false,
      priceLineVisible: false,
      title: '',
    }}, 0);
    donHigh.setData(rows.filter(r => r.donchianHigh != null).map(r => ({{ time: r.time, value: r.donchianHigh }})));

    const donLow = chart.addSeries(LightweightCharts.LineSeries, {{
      color: 'rgba(62, 145, 175, 0.7)',
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      lastValueVisible: false,
      priceLineVisible: false,
      title: '',
    }}, 0);
    donLow.setData(rows.filter(r => r.donchianLow != null).map(r => ({{ time: r.time, value: r.donchianLow }})));

    // Panel 1: Oscilador RSI 14 con guías de sobrecompra (70) y sobreventa (30)
    const rsiGuide70 = chart.addSeries(LightweightCharts.LineSeries, {{
      color: 'rgba(242, 54, 69, 0.35)',
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      lastValueVisible: false,
      priceLineVisible: false,
      title: '',
    }}, 1);
    rsiGuide70.setData(rows.map(r => ({{ time: r.time, value: 70 }})));

    const rsiGuide30 = chart.addSeries(LightweightCharts.LineSeries, {{
      color: 'rgba(8, 153, 129, 0.35)',
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      lastValueVisible: false,
      priceLineVisible: false,
      title: '',
    }}, 1);
    rsiGuide30.setData(rows.map(r => ({{ time: r.time, value: 30 }})));

    const rsiLine = chart.addSeries(LightweightCharts.LineSeries, {{
      color: '#F08063',
      lineWidth: 1.5,
      lastValueVisible: true,
      priceLineVisible: false,
      priceFormat: {{ type: 'price', precision: 1, minMove: 0.1 }},
      title: '',
    }}, 1);
    rsiLine.setData(rows.filter(r => r.rsi != null).map(r => ({{ time: r.time, value: r.rsi }})));

    // Distribución proporcional nativa: Panel 0 (76%) vs Panel 1 (24%)
    const panes = chart.panes();
    panes[0].setStretchFactor(3.2);
    panes[1].setStretchFactor(1.0);

    chart.timeScale().setVisibleLogicalRange({{ from: -4, to: rows.length + 6 }});
    document.querySelector('.chart-tv').dataset.chartReady = 'true';
  }})();
  </script>
</div>
"""


# Alias para compatibilidad con código existente
svg_grafico_mt5_h1 = svg_grafico_tradingview_h1

