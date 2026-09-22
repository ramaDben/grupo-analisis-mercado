# -*- coding: utf-8 -*-
"""Actualiza los 8 diagramas SVG del manual con diseño de alta definición, tipografías legibles y velas nítidas."""

from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MANUAL = RAIZ / "docs" / "MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md"


def get_svg_1():
    return """<div class="contenedor-diagrama">
<svg viewBox="0 0 720 140" width="100%" height="140" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Paso 1 -->
  <rect x="20" y="20" width="195" height="55" rx="6" fill="#0B1926" stroke="#38BDF8" stroke-width="1.5"/>
  <text x="117" y="43" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#38BDF8" text-anchor="middle">1. EL CLIMA MACRO (D1)</text>
  <text x="117" y="60" font-size="9.5" fill="#94A3B8" text-anchor="middle">¿Confirmado por 2 días?</text>

  <line x1="215" y1="47" x2="255" y2="47" stroke="#00DC82" stroke-width="2.5"/>
  <polygon points="255,47 247,42 247,52" fill="#00DC82"/>
  <text x="235" y="40" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#00DC82" text-anchor="middle">SÍ</text>

  <line x1="117" y1="75" x2="117" y2="98" stroke="#EF4444" stroke-width="2"/>
  <polygon points="117,98 112,90 122,90" fill="#EF4444"/>

  <!-- Paso 2 -->
  <rect x="260" y="20" width="195" height="55" rx="6" fill="#0B1926" stroke="#38BDF8" stroke-width="1.5"/>
  <text x="357" y="43" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#38BDF8" text-anchor="middle">2. TU FICHA (H1)</text>
  <text x="357" y="60" font-size="9.5" fill="#94A3B8" text-anchor="middle">¿Los 8 campos completos?</text>

  <line x1="455" y1="47" x2="495" y2="47" stroke="#00DC82" stroke-width="2.5"/>
  <polygon points="495,47 487,42 487,52" fill="#00DC82"/>
  <text x="475" y="40" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#00DC82" text-anchor="middle">SÍ</text>

  <line x1="357" y1="75" x2="357" y2="98" stroke="#EF4444" stroke-width="2"/>
  <polygon points="357,98 352,90 362,90" fill="#EF4444"/>

  <!-- Paso 3 -->
  <rect x="500" y="20" width="200" height="55" rx="6" fill="#0A231C" stroke="#00DC82" stroke-width="2"/>
  <text x="600" y="43" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#00DC82" text-anchor="middle">3. EJECUCIÓN EN MT5</text>
  <text x="600" y="60" font-size="9.5" font-weight="600" fill="#A7F3D0" text-anchor="middle">Lote 1% neto + 5 filtros</text>

  <!-- No gates -->
  <rect x="40" y="98" width="155" height="26" rx="4" fill="#2A1215" stroke="#EF4444" stroke-width="1"/>
  <text x="117" y="115" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#F87171" text-anchor="middle">🛑 MANOS QUIETAS</text>

  <rect x="280" y="98" width="155" height="26" rx="4" fill="#2A1215" stroke="#EF4444" stroke-width="1"/>
  <text x="357" y="115" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#F87171" text-anchor="middle">🛑 MANOS QUIETAS</text>
</svg>
</div>"""


def get_svg_2():
    return """<div class="contenedor-diagrama">
<svg viewBox="0 0 720 210" width="100%" height="210" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Vela Alcista -->
  <g transform="translate(60, 15)">
    <text x="100" y="18" font-family="'Goldman', sans-serif" font-size="12" font-weight="700" fill="#00DC82" text-anchor="middle">VELA ALCISTA (COMPRA)</text>
    <line x1="100" y1="30" x2="100" y2="55" stroke="#00DC82" stroke-width="3"/>
    <rect x="65" y="55" width="70" height="85" rx="3" fill="#063223" stroke="#00DC82" stroke-width="2.5"/>
    <line x1="100" y1="140" x2="100" y2="175" stroke="#00DC82" stroke-width="3"/>

    <!-- Callouts Alcista -->
    <text x="50" y="34" font-size="10.5" font-weight="700" fill="#F8FAFC" text-anchor="end">Máximo (High)</text>
    <line x1="55" y1="30" x2="95" y2="30" stroke="#38BDF8" stroke-width="1" stroke-dasharray="2,2"/>

    <text x="50" y="62" font-size="10.5" font-weight="700" fill="#00DC82" text-anchor="end">Cierre (Close)</text>
    <line x1="55" y1="58" x2="65" y2="58" stroke="#00DC82" stroke-width="1.5"/>

    <text x="50" y="145" font-size="10.5" font-weight="700" fill="#94A3B8" text-anchor="end">Apertura (Open)</text>
    <line x1="55" y1="140" x2="65" y2="140" stroke="#94A3B8" stroke-width="1.5"/>

    <text x="50" y="179" font-size="10.5" font-weight="700" fill="#F8FAFC" text-anchor="end">Mínimo (Low)</text>
    <line x1="55" y1="175" x2="95" y2="175" stroke="#38BDF8" stroke-width="1" stroke-dasharray="2,2"/>

    <rect x="150" y="75" width="115" height="45" rx="4" fill="#0B1926" stroke="#1E293B" stroke-width="1"/>
    <text x="160" y="93" font-size="9" font-weight="700" fill="#00DC82">CUERPO VERDE</text>
    <text x="160" y="108" font-size="8.5" fill="#94A3B8">Cierre > Apertura</text>
  </g>

  <!-- Separador Vertical -->
  <line x1="380" y1="20" x2="380" y2="190" stroke="#1E293B" stroke-width="1.5" stroke-dasharray="4,4"/>

  <!-- Vela Bajista -->
  <g transform="translate(420, 15)">
    <text x="100" y="18" font-family="'Goldman', sans-serif" font-size="12" font-weight="700" fill="#F87171" text-anchor="middle">VELA BAJISTA (VENTA)</text>
    <line x1="100" y1="30" x2="100" y2="55" stroke="#EF4444" stroke-width="3"/>
    <rect x="65" y="55" width="70" height="85" rx="3" fill="#320C10" stroke="#EF4444" stroke-width="2.5"/>
    <line x1="100" y1="140" x2="100" y2="175" stroke="#EF4444" stroke-width="3"/>

    <!-- Callouts Bajista -->
    <text x="150" y="34" font-size="10.5" font-weight="700" fill="#F8FAFC" text-anchor="start">Máximo (High)</text>
    <line x1="105" y1="30" x2="145" y2="30" stroke="#38BDF8" stroke-width="1" stroke-dasharray="2,2"/>

    <text x="150" y="62" font-size="10.5" font-weight="700" fill="#94A3B8" text-anchor="start">Apertura (Open)</text>
    <line x1="135" y1="58" x2="145" y2="58" stroke="#94A3B8" stroke-width="1.5"/>

    <text x="150" y="145" font-size="10.5" font-weight="700" fill="#F87171" text-anchor="start">Cierre (Close)</text>
    <line x1="135" y1="140" x2="145" y2="140" stroke="#EF4444" stroke-width="1.5"/>

    <text x="150" y="179" font-size="10.5" font-weight="700" fill="#F8FAFC" text-anchor="start">Mínimo (Low)</text>
    <line x1="105" y1="175" x2="145" y2="175" stroke="#38BDF8" stroke-width="1" stroke-dasharray="2,2"/>
  </g>
</svg>
</div>"""


def get_svg_4():
    return """<div class="contenedor-diagrama">
<svg viewBox="0 0 720 190" width="100%" height="190" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Zona de Compresión Donchian 50 -->
  <rect x="20" y="20" width="220" height="150" rx="6" fill="#0A1624" stroke="#1E3A5F" stroke-width="1.5" stroke-dasharray="3,3"/>
  <text x="130" y="42" font-family="'Goldman', sans-serif" font-size="10.5" font-weight="700" fill="#38BDF8" text-anchor="middle">50 HORAS COMPRIMIDAS</text>
  <line x1="30" y1="60" x2="230" y2="60" stroke="#38BDF8" stroke-width="1.5"/>
  <text x="130" y="75" font-size="9" font-weight="600" fill="#94A3B8" text-anchor="middle">Techo Donchian 50</text>
  <line x1="30" y1="140" x2="230" y2="140" stroke="#38BDF8" stroke-width="1.5"/>
  <text x="130" y="133" font-size="9" font-weight="600" fill="#94A3B8" text-anchor="middle">Piso Donchian 50</text>
  <rect x="50" y="92" width="160" height="22" rx="4" fill="#052E20" stroke="#00DC82" stroke-width="1"/>
  <text x="130" y="107" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#00DC82" text-anchor="middle">Ancho: 2,1 × ATR (máx 2,5) ✓</text>

  <!-- Vela de Ruptura -->
  <g transform="translate(280, 10)">
    <line x1="40" y1="20" x2="40" y2="40" stroke="#00DC82" stroke-width="3"/>
    <rect x="15" y="40" width="50" height="85" rx="3" fill="#063223" stroke="#00DC82" stroke-width="2.5"/>
    <line x1="40" y1="125" x2="40" y2="160" stroke="#00DC82" stroke-width="3"/>

    <!-- Nivel de Entrada BUY_STOP -->
    <line x1="40" y1="20" x2="200" y2="20" stroke="#00DC82" stroke-width="2" stroke-dasharray="3,3"/>
    <rect x="180" y="8" width="240" height="28" rx="4" fill="#0A281E" stroke="#00DC82" stroke-width="1.5"/>
    <text x="190" y="26" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#00DC82">BUY_STOP en el máximo (vence 2h)</text>

    <!-- Checklist Técnico en SVG -->
    <rect x="180" y="44" width="240" height="78" rx="4" fill="#0B1926" stroke="#1E293B" stroke-width="1"/>
    <text x="190" y="62" font-size="9.5" font-weight="700" fill="#F8FAFC">✓ Cierre fuera del canal</text>
    <text x="190" y="78" font-size="9" font-weight="600" fill="#38BDF8">✓ Cuerpo 68 % (mínimo 50 %)</text>
    <text x="190" y="94" font-size="9" font-weight="600" fill="#38BDF8">✓ Rango 1,3 × ATR (mínimo 1,0)</text>
    <text x="190" y="110" font-size="9" font-weight="600" fill="#38BDF8">✓ RSI en 58 (no extremo &lt; 75)</text>

    <!-- Nivel de Stop Loss -->
    <line x1="40" y1="160" x2="200" y2="160" stroke="#EF4444" stroke-width="2" stroke-dasharray="3,3"/>
    <rect x="180" y="145" width="240" height="28" rx="4" fill="#2A1014" stroke="#EF4444" stroke-width="1.5"/>
    <text x="190" y="163" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#F87171">STOP: Swing o 1,5 × ATR (Módulo 6)</text>
  </g>
</svg>
</div>"""


def get_svg_5():
    return """<div class="contenedor-diagrama">
<svg viewBox="0 0 720 190" width="100%" height="190" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Medias Móviles Exponenciales -->
  <path d="M 30 150 Q 200 120 400 70 T 680 40" fill="none" stroke="#00DC82" stroke-width="3"/>
  <text x="630" y="32" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#00DC82">EMA 20</text>

  <path d="M 30 165 Q 200 140 400 95 T 680 65" fill="none" stroke="#38BDF8" stroke-width="2.5"/>
  <text x="630" y="58" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#38BDF8">EMA 50</text>

  <path d="M 30 180 Q 200 160 400 120 T 680 90" fill="none" stroke="#94A3B8" stroke-width="2"/>
  <text x="630" y="84" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#94A3B8">EMA 100</text>

  <!-- Vela de Rebote en EMA 20 -->
  <g transform="translate(340, 20)">
    <line x1="30" y1="15" x2="30" y2="35" stroke="#00DC82" stroke-width="3"/>
    <rect x="15" y="35" width="30" height="40" rx="2" fill="#063223" stroke="#00DC82" stroke-width="2.5"/>
    <line x1="30" y1="75" x2="30" y2="105" stroke="#00DC82" stroke-width="3"/>

    <!-- Callout de la Mecha -->
    <text x="30" y="130" font-size="9.5" font-weight="700" fill="#00DC82" text-anchor="middle">1. Mecha perfora EMA 20</text>
    <text x="30" y="145" font-size="9.5" font-weight="700" fill="#00DC82" text-anchor="middle">2. Cierre recupera SOBRE ella</text>

    <!-- Orden BUY_STOP -->
    <line x1="30" y1="15" x2="140" y2="15" stroke="#00DC82" stroke-width="2" stroke-dasharray="3,3"/>
    <rect x="140" y="3" width="220" height="28" rx="4" fill="#0A281E" stroke="#00DC82" stroke-width="1.5"/>
    <text x="150" y="21" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#00DC82">BUY_STOP en el máximo</text>

    <!-- Reglas Obligatorias -->
    <rect x="140" y="42" width="220" height="52" rx="4" fill="#0B1926" stroke="#1E293B" stroke-width="1"/>
    <text x="150" y="60" font-size="9" font-weight="700" fill="#F8FAFC">✓ EMAs alineadas (20 > 50 > 100)</text>
    <text x="150" y="78" font-size="9" font-weight="700" fill="#38BDF8">✓ ADX ≥ 20 en clima tendencial</text>
  </g>
</svg>
</div>"""


def get_svg_6():
    return """<div class="contenedor-diagrama">
<svg viewBox="0 0 720 190" width="100%" height="190" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Bandas de Bollinger -->
  <line x1="30" y1="35" x2="690" y2="35" stroke="#00DC82" stroke-width="2.5"/>
  <text x="640" y="28" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#00DC82">MEDIA CENTRAL (SMA 20)</text>
  <text x="640" y="48" font-size="8.5" font-weight="700" fill="#A7F3D0">Objetivo Obligatorio</text>

  <line x1="30" y1="105" x2="690" y2="105" stroke="#F59E0B" stroke-width="2" stroke-dasharray="4,4"/>
  <text x="640" y="100" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#F59E0B">BANDA INFERIOR</text>

  <!-- Vela 1: Cierra afuera -->
  <g transform="translate(180, 20)">
    <line x1="20" y1="75" x2="20" y2="90" stroke="#EF4444" stroke-width="2"/>
    <rect x="5" y="90" width="30" height="35" rx="2" fill="#320C10" stroke="#EF4444" stroke-width="2"/>
    <line x1="20" y1="125" x2="20" y2="140" stroke="#EF4444" stroke-width="2"/>
    <text x="20" y="160" font-size="9.5" font-weight="700" fill="#F87171" text-anchor="middle">1. Cierra afuera</text>
  </g>

  <!-- Vela 2: Reingresa adentro -->
  <g transform="translate(290, 20)">
    <line x1="20" y1="45" x2="20" y2="60" stroke="#00DC82" stroke-width="2.5"/>
    <rect x="5" y="60" width="30" height="45" rx="2" fill="#063223" stroke="#00DC82" stroke-width="2.5"/>
    <line x1="20" y1="105" x2="20" y2="125" stroke="#00DC82" stroke-width="2.5"/>
    <text x="20" y="160" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#00DC82" text-anchor="middle">2. Reingresa (Gatillo)</text>
  </g>

  <!-- Panel de Entrada BUY_LIMIT -->
  <rect x="390" y="65" width="290" height="75" rx="6" fill="#0B1926" stroke="#00DC82" stroke-width="1.5"/>
  <text x="405" y="88" font-family="'Goldman', sans-serif" font-size="10.5" font-weight="700" fill="#00DC82">BUY_LIMIT en el cierre</text>
  <text x="405" y="106" font-size="9" font-weight="600" fill="#94A3B8">✓ RSI en zona de sobreventa (&lt; 35)</text>
  <text x="405" y="122" font-size="9" font-weight="700" fill="#F59E0B">✓ Exige Clima Calma (R0) y ADX &lt; 20</text>
</svg>
</div>"""


def main():
    text = MANUAL.read_text(encoding="utf-8")

    import re

    # Replace all 6 core SVGs with high-definition versions
    svgs = list(re.finditer(r'<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">\s*<svg.*?</svg>\s*</div>', text, re.DOTALL))
    print(f"Encontrados {len(svgs)} contenedores SVG antiguos.")

    # We will replace them sequentially by matching their unique text
    # SVG 1 (Intro)
    text = re.sub(
        r'<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">\s*<svg viewBox="0 0 720 150".*?</svg>\s*</div>',
        get_svg_1(),
        text,
        flags=re.DOTALL
    )

    # SVG 2 (Velas)
    text = re.sub(
        r'<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">\s*<svg viewBox="0 0 720 220".*?</svg>\s*</div>',
        get_svg_2(),
        text,
        flags=re.DOTALL
    )

    # SVG 4 (5.1 Ruptura)
    text = re.sub(
        r'<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">\s*<svg viewBox="0 0 720 180" width="100%" height="180"[^>]*>.*?50 HORAS COMPRIMIDAS.*?</svg>\s*</div>',
        get_svg_4(),
        text,
        flags=re.DOTALL
    )

    # SVG 5 (5.2 Retroceso)
    text = re.sub(
        r'<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">\s*<svg viewBox="0 0 720 180" width="100%" height="180"[^>]*>.*?EMA 20.*?Mecha perfora.*?</svg>\s*</div>',
        get_svg_5(),
        text,
        flags=re.DOTALL
    )

    # SVG 6 (5.3 Rango)
    text = re.sub(
        r'<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">\s*<svg viewBox="0 0 720 180" width="100%" height="180"[^>]*>.*?BANDA INFERIOR.*?Reingresa.*?</svg>\s*</div>',
        get_svg_6(),
        text,
        flags=re.DOTALL
    )

    MANUAL.write_text(text, encoding="utf-8")
    print("Manual actualizado con SVGs de alta definición.")


if __name__ == "__main__":
    main()
