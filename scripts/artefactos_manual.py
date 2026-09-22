# -*- coding: utf-8 -*-
"""Artefactos visuales vectoriales y gráficos TradingView para el Manual de Operaciones v2.1."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
USDCLP_JSON = RAIZ / "data central" / "DATA PRECIOS OHLC" / "USDCLP_H1.json"


def svg_algoritmo_stop_loss() -> str:
    """Genera el diagrama HUD del algoritmo de Stop Loss de 2 pasos."""
    return """<!-- START_SVG_STOP_LOSS -->
<div class="contenedor-diagrama" style="break-inside: avoid; page-break-inside: avoid;">
<svg viewBox="0 0 760 230" width="100%" height="230" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1.5px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Cabecera HUD -->
  <rect x="0" y="0" width="760" height="34" fill="#0A1624"/>
  <line x1="0" y1="34" x2="760" y2="34" stroke="#1E3A5F" stroke-width="1.5"/>
  <text x="20" y="22" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#38BDF8" letter-spacing="0.08em">ALGORITMO CUANTITATIVO · DETERMINACIÓN EXACTA DEL STOP LOSS</text>
  <rect x="580" y="7" width="160" height="20" rx="4" fill="#052E20" stroke="#00DC82" stroke-width="1"/>
  <text x="660" y="21" font-family="'Goldman', sans-serif" font-size="8.5" font-weight="700" fill="#00DC82" text-anchor="middle">REGLA 2-PASOS SSOT</text>

  <!-- Paso 1: Medición de Distancia al Swing -->
  <g transform="translate(20, 48)">
    <rect x="0" y="0" width="220" height="98" rx="6" fill="#0B1926" stroke="#38BDF8" stroke-width="1.5"/>
    <rect x="8" y="8" width="70" height="18" rx="3" fill="#0369A1"/>
    <text x="43" y="21" font-family="'Goldman', sans-serif" font-size="8.5" font-weight="700" fill="#FFFFFF" text-anchor="middle">PASO 1</text>
    <text x="86" y="22" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#E2E8F0">MEDIR SWING</text>
    
    <rect x="8" y="32" width="204" height="24" rx="4" fill="#060F19" stroke="#1E293B" stroke-width="1"/>
    <text x="110" y="48" font-family="'Space Grotesk', monospace" font-size="9" font-weight="700" fill="#38BDF8" text-anchor="middle">dist = |Entrada − Swing(20v)|</text>
    
    <text x="12" y="72" font-size="8.2" font-weight="600" fill="#94A3B8">• Compras: Mínimo 20 velas H1</text>
    <text x="12" y="88" font-size="8.2" font-weight="600" fill="#94A3B8">• Ventas: Máximo 20 velas H1</text>
  </g>

  <!-- Conector / Flecha 1 hacia Evaluador -->
  <path d="M 240 97 L 270 97" stroke="#38BDF8" stroke-width="2.5" fill="none"/>
  <polygon points="270,97 262,92 262,102" fill="#38BDF8"/>

  <!-- Paso 2: Evaluador Central de Banda de Volatilidad -->
  <g transform="translate(275, 48)">
    <rect x="0" y="0" width="200" height="98" rx="6" fill="#0D1B2A" stroke="#F59E0B" stroke-width="1.5"/>
    <rect x="8" y="8" width="70" height="18" rx="3" fill="#B45309"/>
    <text x="43" y="21" font-family="'Goldman', sans-serif" font-size="8.5" font-weight="700" fill="#FFFFFF" text-anchor="middle">PASO 2</text>
    <text x="86" y="22" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#FDE68A">EVALUAR</text>

    <text x="100" y="44" font-size="8.5" font-weight="700" fill="#94A3B8" text-anchor="middle">¿Cae dentro de la banda?</text>
    <rect x="8" y="52" width="184" height="25" rx="4" fill="#1A1505" stroke="#F59E0B" stroke-width="1"/>
    <text x="100" y="69" font-family="'Space Grotesk', monospace" font-size="9.2" font-weight="700" fill="#FBBF24" text-anchor="middle">0,5×ATR ≤ dist ≤ 1,5×ATR</text>
    
    <text x="100" y="90" font-size="8" font-weight="600" fill="#CBD5E1" text-anchor="middle">Filtro de ruido vs. presupuesto</text>
  </g>

  <!-- Bifurcación Rama A (SÍ) -->
  <path d="M 475 75 L 505 60" stroke="#00DC82" stroke-width="2.5" fill="none"/>
  <polygon points="505,60 496,57 499,66" fill="#00DC82"/>
  <rect x="474" y="50" width="22" height="15" rx="2" fill="#052E20"/>
  <text x="485" y="61" font-family="'Goldman', sans-serif" font-size="8.5" font-weight="700" fill="#00DC82" text-anchor="middle">SÍ</text>

  <!-- Rama A: Stop en Swing -->
  <g transform="translate(510, 42)">
    <rect x="0" y="0" width="230" height="48" rx="5" fill="#06231A" stroke="#00DC82" stroke-width="1.5"/>
    <text x="10" y="18" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#00DC82">🟢 RAMA A: STOP EN EL SWING</text>
    <text x="10" y="32" font-family="'Space Grotesk', monospace" font-size="8.8" font-weight="700" fill="#FFFFFF">Stop = Mínimo / Máximo de 20v</text>
    <text x="10" y="44" font-size="7.8" font-weight="600" fill="#A7F3D0">✓ Nivel estructural del mercado · R:R óptimo</text>
  </g>

  <!-- Bifurcación Rama B (NO) -->
  <path d="M 475 118 L 505 130" stroke="#38BDF8" stroke-width="2.5" fill="none"/>
  <polygon points="505,130 499,124 496,133" fill="#38BDF8"/>
  <rect x="474" y="115" width="22" height="15" rx="2" fill="#082F49"/>
  <text x="485" y="126" font-family="'Goldman', sans-serif" font-size="8.5" font-weight="700" fill="#38BDF8" text-anchor="middle">NO</text>

  <!-- Rama B: Stop Fijo 1.5 ATR -->
  <g transform="translate(510, 100)">
    <rect x="0" y="0" width="230" height="48" rx="5" fill="#071E2D" stroke="#38BDF8" stroke-width="1.5"/>
    <text x="10" y="18" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#38BDF8">🔵 RAMA B: STOP PARAMÉTRICO</text>
    <text x="10" y="32" font-family="'Space Grotesk', monospace" font-size="8.8" font-weight="700" fill="#FFFFFF">Stop = Entrada ± 1,5 × ATR(14)</text>
    <text x="10" y="44" font-size="7.8" font-weight="600" fill="#BAE6FD">✓ Techo de seguridad · Presupuesto 1% neto</text>
  </g>

  <!-- Barra de Prohibición Sagrada -->
  <g transform="translate(20, 156)">
    <rect x="0" y="0" width="720" height="62" rx="6" fill="#1C0A0E" stroke="#EF4444" stroke-width="1.5"/>
    <text x="15" y="20" font-family="'Goldman', sans-serif" font-size="9.8" font-weight="700" fill="#F87171">🛑 PROHIBICIÓN SAGRADA: NUNCA USES EL MÍNIMO DE LA VELA DE SEÑAL (GATILLO)</text>
    <text x="15" y="38" font-size="8.6" fill="#E2E8F0">El mínimo de la vela de señal suele estar a menos de 0,5 × ATR. Usarlo provoca dos fallas fatales simultáneas:</text>
    <text x="15" y="53" font-size="8.4" font-weight="700" fill="#FCA5A5">1) Te expulsa por ruido ordinario de mercado. &nbsp;|&nbsp; 2) Infla artificialmente el lote calculado al dividir por una distancia diminuta.</text>
  </g>
</svg>
</div>
<!-- END_SVG_STOP_LOSS -->"""


def svg_comprobacion_margen() -> str:
    """Genera el HUD de verificación de margen operativo y apalancamiento efectivo en SVG puro."""
    return """<!-- START_SVG_MARGEN -->
<div class="contenedor-diagrama" style="break-inside: avoid; page-break-inside: avoid;">
<svg viewBox="0 0 760 215" width="100%" height="215" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1.5px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Cabecera HUD -->
  <rect x="0" y="0" width="760" height="34" fill="#0A1624"/>
  <line x1="0" y1="34" x2="760" y2="34" stroke="#1E3A5F" stroke-width="1.5"/>
  <text x="20" y="22" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#00DC82" letter-spacing="0.08em">7.6 · VERIFICADOR DE MARGEN OPERATIVO Y SOLVENCIA INTRA-HORA</text>
  <rect x="580" y="7" width="160" height="20" rx="4" fill="#082F49" stroke="#38BDF8" stroke-width="1"/>
  <text x="660" y="21" font-family="'Goldman', sans-serif" font-size="8.5" font-weight="700" fill="#38BDF8" text-anchor="middle">FILTRO DE SOLVENCIA</text>

  <!-- Fórmula Superior Central -->
  <g transform="translate(20, 44)">
    <rect x="0" y="0" width="720" height="36" rx="5" fill="#0B1926" stroke="#1E3A5F" stroke-width="1"/>
    <text x="360" y="22" font-family="'Space Grotesk', monospace" font-size="9.8" font-weight="700" fill="#38BDF8" text-anchor="middle">Margen = ( Lote × Tamaño Contrato × Precio Spot en CLP ) / Apalancamiento Broker</text>
  </g>

  <!-- 3 Columnas de Verificación -->
  <!-- Columna 1: Caso Real USD/CLP -->
  <g transform="translate(20, 88)">
    <rect x="0" y="0" width="230" height="114" rx="6" fill="#091824" stroke="#38BDF8" stroke-width="1.2"/>
    <rect x="8" y="8" width="60" height="16" rx="3" fill="#0284C7"/>
    <text x="38" y="20" font-family="'Goldman', sans-serif" font-size="8" font-weight="700" fill="#FFFFFF" text-anchor="middle">PASO 1</text>
    <text x="74" y="20" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#E2E8F0">CÁLCULO REAL</text>
    
    <text x="12" y="42" font-size="8.2" fill="#94A3B8">• Activo: <tspan fill="#FFFFFF" font-weight="700">USD/CLP (0,02 lotes)</tspan></text>
    <text x="12" y="58" font-size="8.2" fill="#94A3B8">• Contrato: 100.000 USD | Spot: 935,60</text>
    <text x="12" y="74" font-size="8.2" fill="#94A3B8">• Apalancamiento Broker: 1:100</text>

    <rect x="8" y="82" width="214" height="24" rx="4" fill="#06121E" stroke="#38BDF8" stroke-width="1"/>
    <text x="115" y="98" font-family="'Space Grotesk', monospace" font-size="9.5" font-weight="700" fill="#38BDF8" text-anchor="middle">Margen = $18.712 CLP</text>
  </g>

  <!-- Columna 2: Impacto en Cuenta -->
  <g transform="translate(265, 88)">
    <rect x="0" y="0" width="230" height="114" rx="6" fill="#062219" stroke="#00DC82" stroke-width="1.2"/>
    <rect x="8" y="8" width="60" height="16" rx="3" fill="#059669"/>
    <text x="38" y="20" font-family="'Goldman', sans-serif" font-size="8" font-weight="700" fill="#FFFFFF" text-anchor="middle">PASO 2</text>
    <text x="74" y="20" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#E2E8F0">IMPACTO CAPITAL</text>

    <text x="12" y="42" font-size="8.2" fill="#94A3B8">• Cuenta Total: <tspan fill="#FFFFFF" font-weight="700">$1.000.000 CLP</tspan></text>
    <text x="12" y="58" font-size="8.2" fill="#94A3B8">• Retención: <tspan fill="#00DC82" font-weight="700">1,87 % del capital</tspan></text>
    <text x="12" y="74" font-size="8.2" fill="#94A3B8">• Margen Libre: <tspan fill="#A7F3D0" font-weight="700">$981.288 (98,13 %)</tspan></text>

    <rect x="8" y="82" width="214" height="24" rx="4" fill="#051912" stroke="#00DC82" stroke-width="1"/>
    <text x="115" y="98" font-family="'Space Grotesk', monospace" font-size="9.5" font-weight="700" fill="#00DC82" text-anchor="middle">Apalancamiento: 1 : 1,87 ✓</text>
  </g>

  <!-- Columna 3: Semáforo de Aprobación -->
  <g transform="translate(510, 88)">
    <rect x="0" y="0" width="230" height="114" rx="6" fill="#0B1926" stroke="#F59E0B" stroke-width="1.2"/>
    <rect x="8" y="8" width="60" height="16" rx="3" fill="#D97706"/>
    <text x="38" y="20" font-family="'Goldman', sans-serif" font-size="8" font-weight="700" fill="#FFFFFF" text-anchor="middle">PASO 3</text>
    <text x="74" y="20" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#FDE68A">DECISIÓN CLIC</text>

    <text x="12" y="42" font-size="8.2" fill="#A7F3D0">✓ Margen ≤ 30 % del Libre</text>
    <text x="12" y="58" font-size="8.2" fill="#A7F3D0">✓ Apalancamiento Real ≤ 1:10</text>
    <text x="12" y="74" font-size="8" fill="#F87171">⛔ Bloqueo si garantía excede 30%</text>

    <rect x="8" y="82" width="214" height="24" rx="4" fill="#042F24" stroke="#00DC82" stroke-width="1.5"/>
    <text x="115" y="98" font-family="'Goldman', sans-serif" font-size="9.2" font-weight="700" fill="#00DC82" text-anchor="middle">🟢 APROBADO PARA EJECUCIÓN</text>
  </g>
</svg>
</div>
<!-- END_SVG_MARGEN -->"""


def generar_bloque_grafico_tradingview() -> str:
    """Genera el gráfico TradingView de caso de estudio real auditado (USD/CLP H1, 02-Sep-2026)."""
    if not USDCLP_JSON.exists():
        return ""

    data = json.loads(USDCLP_JSON.read_text(encoding="utf-8"))
    # Ventana histórica alrededor del caso de estudio auditado (índices 9858 a 9915)
    idx_target = 9898
    rows = data["rows"][idx_target - 40 : idx_target + 16]
    
    chart_rows = [
        {
            "time": int(
                datetime.fromisoformat(r["time"].replace("Z", "+00:00"))
                .replace(tzinfo=timezone.utc)
                .timestamp()
            ),
            "open": r["open"],
            "high": r["high"],
            "low": r["low"],
            "close": r["close"],
            "ema20": r.get("ema_20"),
            "ema50": r.get("ema_50"),
            "ema200": r.get("ema_200"),
            "donchianHigh": r.get("donchian_50_high"),
            "donchianLow": r.get("donchian_50_low"),
            "rsi": r.get("rsi_14"),
        }
        for r in rows
    ]
    payload = json.dumps(chart_rows, separators=(",", ":")).replace("</", "<\\/")

    # Vela de señal (10:00 CLT) y Vela de Take Profit (12:00 CLT)
    sig_row = rows[40]
    tp_row = rows[42]
    sig_time = int(
        datetime.fromisoformat(sig_row["time"].replace("Z", "+00:00"))
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )
    tp_time = int(
        datetime.fromisoformat(tp_row["time"].replace("Z", "+00:00"))
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )

    last = rows[-1]

    return f"""<!-- START_CHART_TV_BLOCK -->
<div class="contenedor-diagrama chart-tv" data-chart-ready="false" style="break-inside: avoid; page-break-inside: avoid;">
  <!-- Topbar TradingView Oficial con Feed Oficial Grupo Inteligencia -->
  <div class="chart-tv-topbar">
    <div class="chart-tv-topbar-left">
      <span class="chart-tv-symbol">USD/CLP</span>
      <span class="chart-tv-badge-tf">1H</span>
      <span class="chart-tv-badge-feed">CASO AUDITADO 02-SEP-2026 · MT5 #51492</span>
      <div class="chart-tv-ohlc">
        <span>O: <strong>{sig_row["open"]:.2f}</strong></span>
        <span>H: <strong>{sig_row["high"]:.2f}</strong></span>
        <span>L: <strong>{sig_row["low"]:.2f}</strong></span>
        <span>C: <strong class="up">{sig_row["close"]:.2f}</strong></span>
        <span class="up">(+0,31%)</span>
      </div>
    </div>
    <div class="chart-tv-brand-tv">
      <svg width="15" height="11" viewBox="0 0 36 28" fill="#00DC82" style="vertical-align: middle; margin-right: 4px;">
        <path d="M14 22H7V11H14V22ZM21 22H15V6H21V22ZM28 22H22V16H28V22Z"/>
      </svg>
      <span>TRADINGVIEW™ ENGINE · CASO DE ESTUDIO</span>
    </div>
  </div>

  <!-- Barra de Indicadores y Niveles Canónicos -->
  <div class="chart-tv-legend">
    <div class="chart-tv-legend-item">
      <span class="chart-tv-dot" style="background: #00DC82;"></span>
      <span class="chart-tv-leg-lbl">EMA 20:</span>
      <span class="chart-tv-leg-val" style="color: #00DC82;">{sig_row.get('ema_20', 935.08):.2f}</span>
    </div>
    <div class="chart-tv-legend-item">
      <span class="chart-tv-dot" style="background: #38BDF8;"></span>
      <span class="chart-tv-leg-lbl">EMA 50:</span>
      <span class="chart-tv-leg-val" style="color: #38BDF8;">{sig_row.get('ema_50', 931.20):.2f}</span>
    </div>
    <div class="chart-tv-legend-item">
      <span class="chart-tv-dot" style="background: #94A3B8;"></span>
      <span class="chart-tv-leg-lbl">EMA 200:</span>
      <span class="chart-tv-leg-val" style="color: #94A3B8;">{sig_row.get('ema_200', 924.50):.2f}</span>
    </div>
    <div class="chart-tv-legend-item">
      <span class="chart-tv-dot" style="background: #F59E0B;"></span>
      <span class="chart-tv-leg-lbl">ATR 14:</span>
      <span class="chart-tv-leg-val" style="color: #FBBF24;">{sig_row.get('atr_14', 2.51):.2f}</span>
    </div>
    <div class="chart-tv-legend-item" style="margin-left: auto;">
      <span class="chart-tv-dot" style="background: #F43F5E;"></span>
      <span class="chart-tv-leg-lbl">RSI 14:</span>
      <span class="chart-tv-leg-val" style="color: #FDA4AF;">{sig_row.get('rsi_14', 57.6):.1f}</span>
    </div>
  </div>

  <!-- Canvas Multi-panel Unificado -->
  <div class="chart-tv-wrapper">
    <div id="manual-tv-chart" class="chart-tv-canvas"></div>
  </div>

  <!-- Pie Institucional del Gráfico -->
  <div class="chart-tv-caption">
    <span class="chart-tv-caption-left">56 velas H1 · Motor TradingView · Feed Real MT5 Cuenta 51492</span>
    <span class="chart-tv-caption-right">Setup 5.2 (Retroceso EMA 20) · Entrada 936,57 · Salida TP 939,08 (+1,0×ATR)</span>
  </div>

  <script>
  (() => {{
    const rows = {payload};
    const container = document.getElementById('manual-tv-chart');
    if (!container || typeof LightweightCharts === 'undefined') return;

    const chart = LightweightCharts.createChart(container, {{
      width: 710,
      height: 215,
      layout: {{
        background: {{ type: 'solid', color: '#060F19' }},
        textColor: '#94A3B8',
        fontSize: 10,
        fontFamily: "'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif",
        panes: {{
          enableResize: false,
          separatorColor: 'rgba(56, 189, 248, 0.25)',
          separatorHoverColor: 'rgba(56, 189, 248, 0.4)',
        }},
      }},
      grid: {{
        vertLines: {{ color: 'rgba(255, 255, 255, 0.04)' }},
        horzLines: {{ color: 'rgba(255, 255, 255, 0.04)' }},
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
        rightOffset: 5,
        barSpacing: 10,
        minBarSpacing: 5,
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
        vertLine: {{ color: 'rgba(56, 189, 248, 0.35)', width: 1, style: 2 }},
        horzLine: {{ color: 'rgba(56, 189, 248, 0.35)', width: 1, style: 2 }},
      }},
    }});

    // Panel 0: Velas Japonesas
    const candles = chart.addSeries(LightweightCharts.CandlestickSeries, {{
      upColor: '#00DC82',
      downColor: '#EF4444',
      borderUpColor: '#00DC82',
      borderDownColor: '#EF4444',
      wickUpColor: '#00DC82',
      wickDownColor: '#EF4444',
      priceFormat: {{ type: 'price', precision: 2, minMove: 0.01 }},
      lastValueVisible: true,
      priceLineVisible: true,
      priceLineColor: '#00DC82',
      priceLineWidth: 1,
      priceLineStyle: LightweightCharts.LineStyle.Dotted,
    }}, 0);

    candles.setData(rows.map(r => ({{
      time: r.time, open: r.open, high: r.high, low: r.low, close: r.close
    }})));

    // Marcadores de Ejecución (Gatillo y TP Alcanzado)
    candles.setMarkers([
      {{
        time: {sig_time},
        position: 'aboveBar',
        color: '#00DC82',
        shape: 'arrowDown',
        text: '1. GATILLO BUY_STOP (936,57)',
        size: 1.4,
      }},
      {{
        time: {tp_time},
        position: 'aboveBar',
        color: '#38BDF8',
        shape: 'arrowDown',
        text: '2. TP1 ALCANZADO (939,08)',
        size: 1.4,
      }}
    ]);

    // Líneas Horizontales de Referencia Operativa
    candles.createPriceLine({{
      price: 936.57,
      color: '#00DC82',
      lineWidth: 1.5,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      axisLabelVisible: true,
      title: 'ENTRADA BUY_STOP: 936,57',
    }});

    candles.createPriceLine({{
      price: 933.33,
      color: '#EF4444',
      lineWidth: 1.5,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      axisLabelVisible: true,
      title: 'STOP LOSS (Swing): 933,33',
    }});

    candles.createPriceLine({{
      price: 939.08,
      color: '#38BDF8',
      lineWidth: 1.5,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      axisLabelVisible: true,
      title: 'TAKE PROFIT 1 (+1,0×ATR): 939,08',
    }});

    // Panel 0: Medias Móviles
    const ema20 = chart.addSeries(LightweightCharts.LineSeries, {{
      color: '#00DC82',
      lineWidth: 2,
      lineStyle: LightweightCharts.LineStyle.Solid,
      lastValueVisible: false,
      priceLineVisible: false,
    }}, 0);
    ema20.setData(rows.filter(r => r.ema20 != null).map(r => ({{ time: r.time, value: r.ema20 }})));

    const ema50 = chart.addSeries(LightweightCharts.LineSeries, {{
      color: '#38BDF8',
      lineWidth: 1.8,
      lineStyle: LightweightCharts.LineStyle.Solid,
      lastValueVisible: false,
      priceLineVisible: false,
    }}, 0);
    ema50.setData(rows.filter(r => r.ema50 != null).map(r => ({{ time: r.time, value: r.ema50 }})));

    const ema200 = chart.addSeries(LightweightCharts.LineSeries, {{
      color: '#94A3B8',
      lineWidth: 1.5,
      lineStyle: LightweightCharts.LineStyle.Solid,
      lastValueVisible: false,
      priceLineVisible: false,
    }}, 0);
    ema200.setData(rows.filter(r => r.ema200 != null).map(r => ({{ time: r.time, value: r.ema200 }})));

    // Panel 1: Oscilador RSI 14
    const rsiGuide70 = chart.addSeries(LightweightCharts.LineSeries, {{
      color: 'rgba(239, 68, 68, 0.35)',
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      lastValueVisible: false,
      priceLineVisible: false,
    }}, 1);
    rsiGuide70.setData(rows.map(r => ({{ time: r.time, value: 70 }})));

    const rsiGuide30 = chart.addSeries(LightweightCharts.LineSeries, {{
      color: 'rgba(0, 220, 130, 0.35)',
      lineWidth: 1,
      lineStyle: LightweightCharts.LineStyle.Dashed,
      lastValueVisible: false,
      priceLineVisible: false,
    }}, 1);
    rsiGuide30.setData(rows.map(r => ({{ time: r.time, value: 30 }})));

    const rsiLine = chart.addSeries(LightweightCharts.LineSeries, {{
      color: '#F43F5E',
      lineWidth: 1.5,
      lastValueVisible: true,
      priceLineVisible: false,
      priceFormat: {{ type: 'price', precision: 1, minMove: 0.1 }},
    }}, 1);
    rsiLine.setData(rows.filter(r => r.rsi != null).map(r => ({{ time: r.time, value: r.rsi }})));

    // Proporciones Panel 0 vs Panel 1
    const panes = chart.panes();
    panes[0].setStretchFactor(3.0);
    panes[1].setStretchFactor(1.0);

    chart.timeScale().setVisibleLogicalRange({{ from: -2, to: rows.length + 4 }});
    const wrapper = document.querySelector('.chart-tv');
    if (wrapper) wrapper.dataset.chartReady = 'true';
  }})();
  </script>
</div>
<!-- END_CHART_TV_BLOCK -->"""
