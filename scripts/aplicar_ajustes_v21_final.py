# punto-de-entrada: script ad-hoc de mantenimiento y compilación
# -*- coding: utf-8 -*-
"""Aplica de forma limpia, determinista y de alta definición todos los ajustes editoriales al Manual de Operaciones."""

from pathlib import Path
import re

RAIZ = Path(__file__).resolve().parent.parent
MANUAL = RAIZ / "docs" / "MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md"


def get_svg_intro():
    return """<div class="contenedor-diagrama">
<svg viewBox="0 0 760 140" width="100%" height="140" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Paso 1 -->
  <rect x="20" y="18" width="205" height="56" rx="6" fill="#0B1926" stroke="#38BDF8" stroke-width="1.5"/>
  <text x="122" y="42" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#38BDF8" text-anchor="middle">1. EL CLIMA MACRO (D1)</text>
  <text x="122" y="60" font-size="9.5" fill="#94A3B8" text-anchor="middle">¿Confirmado por 2 días?</text>

  <line x1="225" y1="46" x2="265" y2="46" stroke="#00DC82" stroke-width="2.5"/>
  <polygon points="265,46 257,41 257,51" fill="#00DC82"/>
  <text x="245" y="38" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#00DC82" text-anchor="middle">SÍ</text>

  <line x1="122" y1="74" x2="122" y2="98" stroke="#EF4444" stroke-width="2"/>
  <polygon points="122,98 117,90 127,90" fill="#EF4444"/>

  <!-- Paso 2 -->
  <rect x="270" y="18" width="205" height="56" rx="6" fill="#0B1926" stroke="#38BDF8" stroke-width="1.5"/>
  <text x="372" y="42" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#38BDF8" text-anchor="middle">2. TU FICHA (H1)</text>
  <text x="372" y="60" font-size="9.5" fill="#94A3B8" text-anchor="middle">¿Los 8 campos completos?</text>

  <line x1="475" y1="46" x2="515" y2="46" stroke="#00DC82" stroke-width="2.5"/>
  <polygon points="515,46 507,41 507,51" fill="#00DC82"/>
  <text x="495" y="38" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#00DC82" text-anchor="middle">SÍ</text>

  <line x1="372" y1="74" x2="372" y2="98" stroke="#EF4444" stroke-width="2"/>
  <polygon points="372,98 367,90 377,90" fill="#EF4444"/>

  <!-- Paso 3 -->
  <rect x="520" y="18" width="220" height="56" rx="6" fill="#0A231C" stroke="#00DC82" stroke-width="2"/>
  <text x="630" y="42" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#00DC82" text-anchor="middle">3. EJECUCIÓN EN MT5</text>
  <text x="630" y="60" font-size="9.5" font-weight="600" fill="#A7F3D0" text-anchor="middle">Lote 1% neto + 5 filtros</text>

  <!-- Botones Manos Quietas -->
  <rect x="42" y="98" width="160" height="26" rx="4" fill="#2A1215" stroke="#EF4444" stroke-width="1"/>
  <text x="122" y="115" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#F87171" text-anchor="middle">🛑 MANOS QUIETAS</text>

  <rect x="292" y="98" width="160" height="26" rx="4" fill="#2A1215" stroke="#EF4444" stroke-width="1"/>
  <text x="372" y="115" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#F87171" text-anchor="middle">🛑 MANOS QUIETAS</text>
</svg>
</div>"""


def get_svg_velas():
    return """<div class="contenedor-diagrama">
<svg viewBox="0 0 760 210" width="100%" height="210" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- LADO IZQUIERDO: Vela Alcista (Compra) -->
  <g transform="translate(40, 15)">
    <text x="120" y="18" font-family="'Goldman', sans-serif" font-size="12" font-weight="700" fill="#00DC82" text-anchor="middle">VELA ALCISTA (COMPRA)</text>
    
    <!-- Mechas y Cuerpo -->
    <line x1="120" y1="30" x2="120" y2="55" stroke="#00DC82" stroke-width="3"/>
    <rect x="85" y="55" width="70" height="85" rx="3" fill="#063223" stroke="#00DC82" stroke-width="2.5"/>
    <line x1="120" y1="140" x2="120" y2="175" stroke="#00DC82" stroke-width="3"/>

    <!-- Etiquetas a la izquierda -->
    <text x="70" y="34" font-size="10.5" font-weight="700" fill="#F8FAFC" text-anchor="end">Máximo (High)</text>
    <line x1="75" y1="30" x2="115" y2="30" stroke="#38BDF8" stroke-width="1" stroke-dasharray="2,2"/>

    <text x="70" y="62" font-size="10.5" font-weight="700" fill="#00DC82" text-anchor="end">Cierre (Close)</text>
    <line x1="75" y1="58" x2="85" y2="58" stroke="#00DC82" stroke-width="1.5"/>

    <text x="70" y="145" font-size="10.5" font-weight="700" fill="#94A3B8" text-anchor="end">Apertura (Open)</text>
    <line x1="75" y1="140" x2="85" y2="140" stroke="#94A3B8" stroke-width="1.5"/>

    <text x="70" y="179" font-size="10.5" font-weight="700" fill="#F8FAFC" text-anchor="end">Mínimo (Low)</text>
    <line x1="75" y1="175" x2="115" y2="175" stroke="#38BDF8" stroke-width="1" stroke-dasharray="2,2"/>

    <!-- Caja Explicativa de Cuerpo Verde -->
    <rect x="175" y="75" width="125" height="45" rx="4" fill="#0B1926" stroke="#1E293B" stroke-width="1"/>
    <text x="185" y="93" font-size="9" font-weight="700" fill="#00DC82">CUERPO VERDE</text>
    <text x="185" y="108" font-size="8.5" fill="#94A3B8">Cierre > Apertura</text>
  </g>

  <!-- Separador Vertical -->
  <line x1="380" y1="20" x2="380" y2="190" stroke="#1E293B" stroke-width="1.5" stroke-dasharray="4,4"/>

  <!-- LADO DERECHO: Vela Bajista (Venta) -->
  <g transform="translate(420, 15)">
    <text x="140" y="18" font-family="'Goldman', sans-serif" font-size="12" font-weight="700" fill="#F87171" text-anchor="middle">VELA BAJISTA (VENTA)</text>
    
    <!-- Caja Explicativa de Cuerpo Rojo (Simétrica a la izquierda de la vela roja) -->
    <rect x="0" y="75" width="125" height="45" rx="4" fill="#0B1926" stroke="#1E293B" stroke-width="1"/>
    <text x="10" y="93" font-size="9" font-weight="700" fill="#EF4444">CUERPO ROJO</text>
    <text x="10" y="108" font-size="8.5" fill="#94A3B8">Cierre &lt; Apertura</text>

    <!-- Mechas y Cuerpo -->
    <line x1="140" y1="30" x2="140" y2="55" stroke="#EF4444" stroke-width="3"/>
    <rect x="105" y="55" width="70" height="85" rx="3" fill="#320C10" stroke="#EF4444" stroke-width="2.5"/>
    <line x1="140" y1="140" x2="140" y2="175" stroke="#EF4444" stroke-width="3"/>

    <!-- Etiquetas a la derecha -->
    <text x="190" y="34" font-size="10.5" font-weight="700" fill="#F8FAFC" text-anchor="start">Máximo (High)</text>
    <line x1="145" y1="30" x2="185" y2="30" stroke="#38BDF8" stroke-width="1" stroke-dasharray="2,2"/>

    <text x="190" y="62" font-size="10.5" font-weight="700" fill="#94A3B8" text-anchor="start">Apertura (Open)</text>
    <line x1="175" y1="58" x2="185" y2="58" stroke="#94A3B8" stroke-width="1.5"/>

    <text x="190" y="145" font-size="10.5" font-weight="700" fill="#F87171" text-anchor="start">Cierre (Close)</text>
    <line x1="175" y1="140" x2="185" y2="140" stroke="#EF4444" stroke-width="1.5"/>

    <text x="190" y="179" font-size="10.5" font-weight="700" fill="#F8FAFC" text-anchor="start">Mínimo (Low)</text>
    <line x1="145" y1="175" x2="185" y2="175" stroke="#38BDF8" stroke-width="1" stroke-dasharray="2,2"/>
  </g>
</svg>
</div>"""


def get_svg_semaforo():
    return """<div class="contenedor-diagrama">
<svg viewBox="0 0 760 175" width="100%" height="175" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Tarjeta 1: Verde -->
  <g transform="translate(15, 12)">
    <rect width="170" height="150" rx="6" fill="#0A231C" stroke="#00DC82" stroke-width="1.5"/>
    <circle cx="26" cy="26" r="10" fill="#00DC82"/>
    <text x="26" y="30" font-size="11" font-weight="800" fill="#060F19" text-anchor="middle">✓</text>
    <text x="44" y="30" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#00DC82">VERDE</text>
    <text x="14" y="56" font-size="9" font-weight="700" fill="#A7F3D0">Los 8 campos listos</text>
    <text x="14" y="74" font-size="8.2" fill="#94A3B8">Vela H1 cerrada.</text>
    <text x="14" y="88" font-size="8.2" fill="#94A3B8">Filtros aprobados.</text>
    <rect x="10" y="106" width="150" height="32" rx="4" fill="#00DC82"/>
    <text x="85" y="126" font-family="'Goldman', sans-serif" font-size="9" font-weight="800" fill="#060F19" text-anchor="middle">INGRESAR EN MT5</text>
  </g>

  <!-- Tarjeta 2: Amarillo -->
  <g transform="translate(200, 12)">
    <rect width="170" height="150" rx="6" fill="#261A08" stroke="#F59E0B" stroke-width="1.5"/>
    <circle cx="26" cy="26" r="10" fill="#F59E0B"/>
    <text x="26" y="30" font-size="10" font-weight="800" fill="#060F19" text-anchor="middle">⏳</text>
    <text x="44" y="30" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#F59E0B">AMARILLO</text>
    <text x="14" y="56" font-size="9" font-weight="700" fill="#FDE68A">Setup sin gatillo</text>
    <text x="14" y="74" font-size="8.2" fill="#94A3B8">El clima habilita,</text>
    <text x="14" y="88" font-size="8.2" fill="#94A3B8">la vela aún no gatilla.</text>
    <rect x="10" y="106" width="150" height="32" rx="4" fill="#D97706"/>
    <text x="85" y="126" font-family="'Goldman', sans-serif" font-size="9" font-weight="800" fill="#FFFFFF" text-anchor="middle">ESPERAR EL :00</text>
  </g>

  <!-- Tarjeta 3: Blanco -->
  <g transform="translate(385, 12)">
    <rect width="170" height="150" rx="6" fill="#0B1926" stroke="#475569" stroke-width="1.5"/>
    <circle cx="26" cy="26" r="10" fill="#64748B"/>
    <text x="26" y="30" font-size="10" font-weight="800" fill="#060F19" text-anchor="middle">○</text>
    <text x="44" y="30" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#94A3B8">BLANCO</text>
    <text x="14" y="56" font-size="9" font-weight="700" fill="#CBD5E1">Sin setup aplicable</text>
    <text x="14" y="74" font-size="8.2" fill="#64748B">El clima y la</text>
    <text x="14" y="88" font-size="8.2" fill="#64748B">estructura no calzan.</text>
    <rect x="10" y="106" width="150" height="32" rx="4" fill="#334155"/>
    <text x="85" y="126" font-family="'Goldman', sans-serif" font-size="8.5" font-weight="800" fill="#FFFFFF" text-anchor="middle">MERCADO NO OPERABLE</text>
  </g>

  <!-- Tarjeta 4: Rojo -->
  <g transform="translate(570, 12)">
    <rect width="170" height="150" rx="6" fill="#280D12" stroke="#EF4444" stroke-width="1.5"/>
    <circle cx="26" cy="26" r="10" fill="#EF4444"/>
    <text x="26" y="30" font-size="10" font-weight="800" fill="#FFFFFF" text-anchor="middle">✕</text>
    <text x="44" y="30" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#EF4444">ROJO</text>
    <text x="14" y="56" font-size="9" font-weight="700" fill="#FCA5A5">Filtro bloquea</text>
    <text x="14" y="74" font-size="8.2" fill="#94A3B8">Spread alto, blackout,</text>
    <text x="14" y="88" font-size="8.2" fill="#94A3B8">o contra clima macro.</text>
    <rect x="10" y="106" width="150" height="32" rx="4" fill="#DC2626"/>
    <text x="85" y="126" font-family="'Goldman', sans-serif" font-size="9" font-weight="800" fill="#FFFFFF" text-anchor="middle">PROHIBIDO OPERAR</text>
  </g>
</svg>
</div>"""


def get_svg_ruptura():
    return """<div class="contenedor-diagrama">
<svg viewBox="0 0 760 200" width="100%" height="200" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Zona de Compresión Donchian 50 -->
  <rect x="20" y="20" width="220" height="160" rx="6" fill="#0A1624" stroke="#1E3A5F" stroke-width="1.5" stroke-dasharray="3,3"/>
  <text x="130" y="44" font-family="'Goldman', sans-serif" font-size="10.5" font-weight="700" fill="#38BDF8" text-anchor="middle">50 HORAS COMPRIMIDAS</text>
  <line x1="30" y1="65" x2="230" y2="65" stroke="#38BDF8" stroke-width="1.5"/>
  <text x="130" y="80" font-size="9" font-weight="600" fill="#94A3B8" text-anchor="middle">Techo Donchian 50</text>
  <line x1="30" y1="145" x2="230" y2="145" stroke="#38BDF8" stroke-width="1.5"/>
  <text x="130" y="138" font-size="9" font-weight="600" fill="#94A3B8" text-anchor="middle">Piso Donchian 50</text>
  <rect x="50" y="96" width="160" height="24" rx="4" fill="#052E20" stroke="#00DC82" stroke-width="1"/>
  <text x="130" y="112" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#00DC82" text-anchor="middle">Ancho: 2,1 × ATR (máx 2,5) ✓</text>

  <!-- Vela de Ruptura -->
  <g transform="translate(290, 15)">
    <line x1="40" y1="20" x2="40" y2="40" stroke="#00DC82" stroke-width="3"/>
    <rect x="15" y="40" width="50" height="85" rx="3" fill="#063223" stroke="#00DC82" stroke-width="2.5"/>
    <line x1="40" y1="125" x2="40" y2="160" stroke="#00DC82" stroke-width="3"/>

    <!-- Nivel de Entrada BUY_STOP -->
    <line x1="40" y1="20" x2="190" y2="20" stroke="#00DC82" stroke-width="2" stroke-dasharray="3,3"/>
    <rect x="175" y="8" width="245" height="28" rx="4" fill="#0A281E" stroke="#00DC82" stroke-width="1.5"/>
    <text x="185" y="26" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#00DC82">BUY_STOP en el máximo (vence 2h)</text>

    <!-- Checklist Técnico en SVG -->
    <rect x="175" y="44" width="245" height="80" rx="4" fill="#0B1926" stroke="#1E293B" stroke-width="1"/>
    <text x="185" y="63" font-size="9.5" font-weight="700" fill="#F8FAFC">✓ Cierre fuera del canal</text>
    <text x="185" y="79" font-size="9" font-weight="600" fill="#38BDF8">✓ Cuerpo 68 % (mínimo 50 %)</text>
    <text x="185" y="95" font-size="9" font-weight="600" fill="#38BDF8">✓ Rango 1,3 × ATR (mínimo 1,0)</text>
    <text x="185" y="111" font-size="9" font-weight="600" fill="#38BDF8">✓ RSI en 58 (no extremo &lt; 75)</text>

    <!-- Nivel de Stop Loss -->
    <line x1="40" y1="160" x2="190" y2="160" stroke="#EF4444" stroke-width="2" stroke-dasharray="3,3"/>
    <rect x="175" y="146" width="245" height="28" rx="4" fill="#2A1014" stroke="#EF4444" stroke-width="1.5"/>
    <text x="185" y="164" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#F87171">STOP: Swing o 1,5 × ATR (Módulo 6)</text>
  </g>
</svg>
</div>"""


def get_svg_retroceso():
    return """<div class="contenedor-diagrama">
<svg viewBox="0 0 760 210" width="100%" height="210" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Medias Móviles Exponenciales -->
  <path d="M 30 145 Q 220 115 440 70 T 720 35" fill="none" stroke="#00DC82" stroke-width="3"/>
  <text x="735" y="32" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#00DC82" text-anchor="end">EMA 20</text>

  <path d="M 30 165 Q 220 138 440 95 T 720 60" fill="none" stroke="#38BDF8" stroke-width="2.5"/>
  <text x="735" y="58" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#38BDF8" text-anchor="end">EMA 50</text>

  <path d="M 30 185 Q 220 160 440 120 T 720 85" fill="none" stroke="#94A3B8" stroke-width="2"/>
  <text x="735" y="83" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#94A3B8" text-anchor="end">EMA 100</text>

  <!-- Vela de Rebote en EMA 20 -->
  <g transform="translate(160, 15)">
    <line x1="40" y1="15" x2="40" y2="35" stroke="#00DC82" stroke-width="3"/>
    <rect x="25" y="35" width="30" height="40" rx="2" fill="#063223" stroke="#00DC82" stroke-width="2.5"/>
    <line x1="40" y1="75" x2="40" y2="105" stroke="#00DC82" stroke-width="3"/>

    <!-- Anotaciones de la vela con fondo oscuro protector -->
    <rect x="-35" y="125" width="150" height="36" rx="4" fill="#0A1624" stroke="#1E293B" stroke-width="1"/>
    <text x="40" y="139" font-size="9" font-weight="700" fill="#00DC82" text-anchor="middle">1. Mecha perfora EMA 20</text>
    <text x="40" y="153" font-size="9" font-weight="700" fill="#00DC82" text-anchor="middle">2. Cierre recupera SOBRE ella</text>

    <!-- Orden BUY_STOP -->
    <line x1="40" y1="15" x2="135" y2="15" stroke="#00DC82" stroke-width="2" stroke-dasharray="3,3"/>
    <rect x="135" y="3" width="245" height="28" rx="4" fill="#0A281E" stroke="#00DC82" stroke-width="1.5"/>
    <text x="145" y="21" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#00DC82">BUY_STOP en el máximo (vence 2h)</text>

    <!-- Reglas Obligatorias -->
    <rect x="135" y="41" width="245" height="54" rx="4" fill="#0B1926" stroke="#1E293B" stroke-width="1"/>
    <text x="145" y="61" font-size="9.5" font-weight="700" fill="#F8FAFC">✓ EMAs alineadas (20 > 50 > 100)</text>
    <text x="145" y="79" font-size="9" font-weight="700" fill="#38BDF8">✓ ADX ≥ 20 en clima tendencial</text>
  </g>
</svg>
</div>"""


def get_svg_rango():
    return """<div class="contenedor-diagrama">
<svg viewBox="0 0 760 200" width="100%" height="200" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Bandas de Bollinger -->
  <line x1="30" y1="35" x2="730" y2="35" stroke="#00DC82" stroke-width="2.5"/>
  <text x="730" y="28" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#00DC82" text-anchor="end">MEDIA CENTRAL (SMA 20)</text>
  <text x="730" y="48" font-size="8.5" font-weight="700" fill="#A7F3D0" text-anchor="end">Objetivo Obligatorio</text>

  <line x1="30" y1="115" x2="730" y2="115" stroke="#F59E0B" stroke-width="2" stroke-dasharray="4,4"/>
  <text x="730" y="110" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#F59E0B" text-anchor="end">BANDA INFERIOR</text>

  <!-- Vela 1: Cierra afuera -->
  <g transform="translate(120, 20)">
    <line x1="20" y1="75" x2="20" y2="90" stroke="#EF4444" stroke-width="2"/>
    <rect x="5" y="90" width="30" height="35" rx="2" fill="#320C10" stroke="#EF4444" stroke-width="2"/>
    <line x1="20" y1="125" x2="20" y2="140" stroke="#EF4444" stroke-width="2"/>
    <text x="20" y="158" font-size="9.5" font-weight="700" fill="#F87171" text-anchor="middle">1. Cierra afuera</text>
  </g>

  <!-- Vela 2: Reingresa adentro -->
  <g transform="translate(220, 20)">
    <line x1="20" y1="45" x2="20" y2="60" stroke="#00DC82" stroke-width="2.5"/>
    <rect x="5" y="60" width="30" height="45" rx="2" fill="#063223" stroke="#00DC82" stroke-width="2.5"/>
    <line x1="20" y1="105" x2="20" y2="125" stroke="#00DC82" stroke-width="2.5"/>
    <text x="20" y="158" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#00DC82" text-anchor="middle">2. Reingresa (Gatillo)</text>
  </g>

  <!-- Panel de Entrada BUY_LIMIT -->
  <g transform="translate(320, 48)">
    <rect x="0" y="0" width="260" height="82" rx="6" fill="#0B1926" stroke="#00DC82" stroke-width="1.5"/>
    <text x="16" y="25" font-family="'Goldman', sans-serif" font-size="10.5" font-weight="700" fill="#00DC82">BUY_LIMIT en el cierre</text>
    <text x="16" y="47" font-size="9" font-weight="600" fill="#94A3B8">✓ RSI en zona de sobreventa (&lt; 35)</text>
    <text x="16" y="67" font-size="9" font-weight="700" fill="#F59E0B">✓ Exige Clima Calma (R0) y ADX &lt; 20</text>
  </g>
</svg>
</div>"""


def get_svg_blackout():
    return """<div class="contenedor-diagrama">
<svg viewBox="0 0 760 120" width="100%" height="120" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <line x1="40" y1="60" x2="720" y2="60" stroke="#1E3A5F" stroke-width="3"/>

  <!-- Sesión Normal -->
  <circle cx="110" cy="60" r="10" fill="#00DC82"/>
  <text x="110" y="38" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#00DC82" text-anchor="middle">SESIÓN NORMAL</text>

  <!-- Antes del Dato -->
  <rect x="210" y="28" width="150" height="64" rx="6" fill="#280D12" stroke="#EF4444" stroke-width="1.5"/>
  <text x="285" y="52" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#F87171" text-anchor="middle">ANTES DEL DATO</text>
  <text x="285" y="72" font-size="8.5" font-weight="600" fill="#FCA5A5" text-anchor="middle">Cancelar pendientes</text>

  <!-- Dato Macro (!) -->
  <circle cx="430" cy="60" r="18" fill="#EF4444"/>
  <text x="430" y="67" font-family="'Goldman', sans-serif" font-size="15" font-weight="800" fill="#FFFFFF" text-anchor="middle">!</text>
  <text x="430" y="22" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#F87171" text-anchor="middle">DATO MACRO</text>

  <!-- Después del Dato -->
  <rect x="500" y="28" width="170" height="64" rx="6" fill="#280D12" stroke="#EF4444" stroke-width="1.5"/>
  <text x="585" y="52" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#F87171" text-anchor="middle">DESPUÉS DEL DATO</text>
  <text x="585" y="72" font-size="8.5" font-weight="600" fill="#FCA5A5" text-anchor="middle">Esperar vela cerrada</text>
</svg>
</div>"""


def get_svg_checklist():
    return """<div class="contenedor-diagrama">
<svg viewBox="0 0 760 250" width="100%" height="250" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <rect x="0" y="0" width="760" height="34" fill="#0B1926" rx="8 8 0 0"/>
  <text x="24" y="22" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#38BDF8">CHECKLIST ANTES DEL CLIC · 30 SEGUNDOS</text>

  <circle cx="35" cy="60" r="10" fill="#00DC82"/>
  <text x="35" y="64" font-family="'Goldman', sans-serif" font-size="10" font-weight="800" fill="#060F19" text-anchor="middle">1</text>
  <text x="58" y="64" font-size="9.8" font-weight="600" fill="#F8FAFC">¿El clima está confirmado por 2 días y la confianza sobre 51 % (mínimo de Anexo A2)?</text>

  <circle cx="35" cy="94" r="10" fill="#00DC82"/>
  <text x="35" y="98" font-family="'Goldman', sans-serif" font-size="10" font-weight="800" fill="#060F19" text-anchor="middle">2</text>
  <text x="58" y="98" font-size="9.8" font-weight="600" fill="#F8FAFC">¿La dirección que quiero tomar es la que el clima permite en el Módulo 10?</text>

  <circle cx="35" cy="128" r="10" fill="#00DC82"/>
  <text x="35" y="132" font-family="'Goldman', sans-serif" font-size="10" font-weight="800" fill="#060F19" text-anchor="middle">3</text>
  <text x="58" y="132" font-size="9.8" font-weight="600" fill="#F8FAFC">¿El setup calificó sobre una vela H1 CERRADA, con todas sus condiciones?</text>

  <circle cx="35" cy="162" r="10" fill="#00DC82"/>
  <text x="35" y="166" font-family="'Goldman', sans-serif" font-size="10" font-weight="800" fill="#060F19" text-anchor="middle">4</text>
  <text x="58" y="166" font-size="9.8" font-weight="600" fill="#F8FAFC">¿El stop sale de las 20 velas o de 1,5 × ATR, y el R:R llega al menos a 1,0?</text>

  <circle cx="35" cy="196" r="10" fill="#00DC82"/>
  <text x="35" y="200" font-family="'Goldman', sans-serif" font-size="10" font-weight="800" fill="#060F19" text-anchor="middle">5</text>
  <text x="58" y="200" font-size="9.8" font-weight="600" fill="#F8FAFC">¿El lote es del 1 % NETO (0,90% precio + 0,10% fricción), redondeado hacia abajo?</text>

  <circle cx="35" cy="230" r="10" fill="#00DC82"/>
  <text x="35" y="234" font-family="'Goldman', sans-serif" font-size="10" font-weight="800" fill="#060F19" text-anchor="middle">6</text>
  <text x="58" y="234" font-size="9.8" font-weight="600" fill="#F8FAFC">¿Spread bajo el tope del activo, horario válido, sin blackout, con confirmación cruzada?</text>
</svg>
</div>"""


def main():
    text = MANUAL.read_text(encoding="utf-8")

    # 1. Update Header & Version Control Table (SIN REGLAS OBSOLETAS)
    nuevo_intro = """# Manual de Operaciones · Trading Cuantitativo Intermercado
### De la macroeconomía real a tu plataforma MetaTrader 5
**Grupo Inteligencia · Departamento de Estudios y Research**  
*Manual formativo modular para el trader cuantitativo. Versión Oficial 2.1 · Septiembre 2026*

---

### 📜 Control de Versiones y Gobernanza del Manual

| Versión | Fecha | Cambios Principales y Justificación Técnica |
|---|---|---|
| **v1.0** | Agosto 2026 | Versión inicial formativa con stops discrecionales en mínimos de velas. |
| **v2.0** | Septiembre 2026 | Formalización matemática del ATR de 14 en H1, conmutador de climas R0–R4, precedencia de setups y Chandelier Trailing Exit. |
| **v2.1** | **Septiembre 2026** *(Actual)* | **Centralización de umbrales en Anexo A2 (SSOT)**, unificación de tasa real para Oro en 2,20 %, **Presupuesto de Riesgo Neto (Buffer 90/10 para Spread + Comisión)**, **Matriz 2D Clima × Setup**, **Regla de Tolerancia de Slippage**, **Mapa de Correlación Intermercado y Co-Riesgo**, **Caso de Estudio de Pérdida Disciplinada**, y **Módulo 12 de Bitácora de Auditoría Operativa**. |

---

> [!CAUTION]
> **Aviso de riesgo y transparencia.** Este documento es material educativo y formativo de Grupo Inteligencia. No constituye asesoría financiera personalizada ni garantiza rentabilidades futuras. El trading en Contratos por Diferencia (CFD) con apalancamiento conlleva un alto riesgo de pérdida de capital, y puedes perder la totalidad de lo que depositas.
>
> Este manual no es un robot que opera solo. Nosotros publicamos a diario el clima económico y el sesgo por activo; **la decisión, el cálculo del tamaño y la ejecución de cada orden son tuyas**, en tu plataforma y bajo tu criterio.

---

## 🧭 Cómo usar este manual

El manual está dividido en **12 módulos y 3 anexos**. Cada módulo es autocontenido: responde una pregunta concreta y no necesitas haber leído el anterior para aplicarlo.

| Si lo que quieres es… | Lee estos módulos |
|---|---|
| Entender qué estás operando y las expectativas estadísticas reales | **M0**, **M1** |
| Entender por qué se mueve el dinero en el mundo | **M2**, **M3** |
| Armar una operación concreta de principio a fin | **M4** → **M5** → **M6** → **M7** → **M8** |
| Saber cuándo NO operar y gestionar el co-riesgo de cartera | **M8**, **M9** |
| Consultar la regla y el swap de un activo puntual | **M10** |
| Repasar en 30 segundos antes de hacer clic | **M11** |
| Registrar y auditar tu disciplina operativa | **M12** |
| Buscar una sigla o un umbral maestro | **A1**, **A2** |"""

    idx_intro_end = text.find("### Qué te damos nosotros y qué determinas tú")
    text = nuevo_intro + "\n\n" + text[idx_intro_end:]

    # Reemplazo de SVGs con expresiones regulares
    # SVG 1 (Intro)
    text = re.sub(
        r'<div class="contenedor-diagrama">\s*<svg viewBox="0 0 7[26]0 140".*?</svg>\s*</div>|<div style="[^"]*">\s*<svg viewBox="0 0 720 150".*?</svg>\s*</div>',
        get_svg_intro(),
        text,
        count=1,
        flags=re.DOTALL
    )

    # SVG 2 (Velas Módulo 1) con simetría verde y roja
    text = re.sub(
        r'<div class="contenedor-diagrama">\s*<svg viewBox="0 0 7[26]0 210".*?</svg>\s*</div>|<div style="[^"]*">\s*<svg viewBox="0 0 720 220".*?</svg>\s*</div>',
        get_svg_velas(),
        text,
        count=1,
        flags=re.DOTALL
    )

    # SVG 3 (Semáforo Módulo 4)
    text = re.sub(
        r'<div class="contenedor-diagrama">\s*<svg viewBox="0 0 7[26]0 1[78]0".*?</svg>\s*</div>|<div style="[^"]*">\s*<svg viewBox="0 0 720 180".*?</svg>\s*</div>',
        get_svg_semaforo(),
        text,
        count=1,
        flags=re.DOTALL
    )

    # SVG 7 (Blackout Módulo 8.3)
    text = re.sub(
        r'<div class="contenedor-diagrama">\s*<svg viewBox="0 0 7[26]0 120".*?</svg>\s*</div>|<div style="[^"]*">\s*<svg viewBox="0 0 720 120".*?</svg>\s*</div>',
        get_svg_blackout(),
        text,
        count=1,
        flags=re.DOTALL
    )

    # SVG 8 (Checklist Módulo 11)
    text = re.sub(
        r'<div class="contenedor-diagrama">\s*<svg viewBox="0 0 7[26]0 2[35]0".*?</svg>\s*</div>|<div style="[^"]*">\s*<svg viewBox="0 0 720 250".*?</svg>\s*</div>',
        get_svg_checklist(),
        text,
        count=1,
        flags=re.DOTALL
    )

    # Módulo 5 Completo con Matriz, Precedencia, Slippage y SVGs HD
    modulo_5_completo = f"""# 📐 MÓDULO 5 · Los tres setups

**Pregunta que responde**: ¿qué tiene que hacer el precio para que yo tenga permiso de entrar?

---

El método usa **tres setups y ninguno más**, todos sobre velas H1 cerradas. Son **mutuamente excluyentes**: en cada momento aplica uno solo, y hay un orden para decidir cuál.

## 5.0 · Primero decides cuál aplica: Matriz Clima × Setup

No eliges el setup que más te gusta. El **clima macroeconómico es el primer filtro jerárquico**: decide qué tipo de microestructura tenemos antes de tocar cualquier indicador técnico.

### Matriz de Permisos: Clima Macro × Setup Técnico

| Clima Macro Vigente | Ruptura por Compresión (5.1) | Retroceso al Promedio (5.2) | Rebote en Rango (5.3) |
|---|---|---|---|
| 🌪️ **Tormenta (R3)** | **Habilitado** (1º Orden) | **Habilitado** (2º Orden si ADX ≥ 20) | ⛔ **PROHIBIDO** |
| 🛒 **Inflación (R1)** | **Habilitado** (1º Orden) | **Habilitado** (2º Orden si ADX ≥ 20) | ⛔ **PROHIBIDO** |
| 📉 **Recesión (R4)** | **Habilitado** (1º Orden) | **Habilitado** (2º Orden si ADX ≥ 20) | ⛔ **PROHIBIDO** |
| ☀️ **Día bueno (R2)** | **Habilitado** (1º Orden) | **Habilitado** (2º Orden si ADX ≥ 20) | ⛔ **PROHIBIDO** |
| 🏖️ **Calma (R0)** | ⛔ **PROHIBIDO** | ⛔ **PROHIBIDO** | **Habilitado** (Único si ADX < 20) |

### Árbol de Precedencia Estricta

1. **Si el Clima es Calma (R0)**:
   * Evalúa **Rebote en Rango (5.3)**: ¿ADX < 20 y RSI extremo fuera de bandas? → Si cumple, se opera. Si ADX ≥ 20, **NO se opera** (es ruido transitorio sin tendencia macro).
2. **Si el Clima es Tendencial (R1, R2, R3, R4)**:
   * 1º **Ruptura por compresión (5.1)**: ¿Ancho Donchian 50 ≤ 2,5 × ATR y vela cerrada afuera? → Si cumple, se coloca orden STOP.
   * 2º **Retroceso al promedio (5.2)**: ¿EMAs 20/50/100 alineadas y ADX ≥ 20? → Si cumple, se coloca orden STOP en rebote.
3. **Si ninguno califica**: **Esperar con manos quietas.** Es el resultado más frecuente y protege tu capital.

## 5.1 · Ruptura por compresión

*El precio estaba apretado y cerró afuera.*

* **Cuándo aplica**: Climas con tendencia (**Tormenta, Inflación, Recesión o Día bueno**). **Prohibido en Calma.**
* **Qué busca**: El precio estuvo comprimido en un rango estrecho las últimas 50 horas y una vela H1 **cierra fuera** del canal.
* **Las cuatro condiciones, todas obligatorias**:
  1. El **cierre** queda sobre el techo del canal Donchian 50 (en compras) o bajo el piso (en ventas).
  2. **Regla del cuerpo**: El cuerpo mide **al menos la mitad (50 % o más)** del total de la vela. No sirve una mecha larga con cuerpo chico.
  3. **Rango de la vela igual o mayor a 1,0 × ATR**: La vela de ruptura tiene que ser al menos de tamaño normal. Una ruptura con una vela diminuta no tiene fuerza detrás.
  4. **RSI no extremo**: En compras el RSI va en 75 o menos; en ventas, en 25 o más. Entrar en un extremo es comprar el final del movimiento.
* **Entrada**: Orden pendiente `BUY_STOP` en el **máximo de esa vela** (o `SELL_STOP` en el mínimo), con **vencimiento a 2 velas H1**. Si no se activa en dos horas, se cancela.
* **Regla de Tolerancia de Deslizamiento (Slippage Cap)**: Al activarse la orden `BUY_STOP` o `SELL_STOP`, verifica el precio real de llenado (*fill price*). Si el deslizamiento desfavorable es mayor a **0,2 × ATR** (o supera el **15 %** de la distancia al stop), **la operación debe cancelarse/cerrarse de inmediato a mercado**. Un deslizamiento excesivo distorsiona la relación riesgo/beneficio y amplifica la pérdida real fuera de presupuesto.

{get_svg_ruptura()}

## 5.2 · Retroceso al promedio

*El precio descansó sobre su media y volvió a retomar.*

* **Cuándo aplica**: Mercados con **clima tendencial activo (R1, R2, R3 o R4)** y con **ADX en 20 o más**. **Estrictamente prohibido en clima Calma (R0)**, donde un pico transitorio de ADX suele ser un engaño de noticias sin momentum estructural.
* **Las tres condiciones, todas obligatorias**:
  1. **Las tres medias alineadas**: En compras, EMA 20 sobre EMA 50 sobre EMA 100. En ventas, al revés. Sin esa alineación no hay tendencia que respaldar.
  2. El **mínimo** de la vela toca o perfora la EMA 20 (en compras).
  3. El **cierre** queda sobre la EMA 20. El precio la perforó durante la hora, pero los compradores la recuperaron antes del cierre.
* **Entrada**: `BUY_STOP` en el **máximo de la vela de rebote**, vencimiento a 2 velas H1.

{get_svg_retroceso()}

<div style="break-before: page;"></div>

## 5.3 · Rebote en rango

*El precio se salió de la banda y volvió a entrar.*

* **Cuándo aplica**: **Exclusivamente en clima Calma (R0)**, y con **ADX menor a 20**. Prohibido en cualquier clima tendencial.
* **Las tres condiciones, todas obligatorias**:
  1. La vela **anterior** cerró **fuera** de la banda de Bollinger, bajo la inferior en compras.
  2. La vela **actual** cierra **de regreso adentro**.
  3. El **RSI** marca extremo: **bajo 35** en compras, **sobre 65** en ventas. Los dos lados tienen umbral.
* **Entrada**: `BUY_LIMIT` en el **precio de cierre** de la vela que reingresó. Es orden límite y no a mercado.
* **Objetivo obligatorio**: La **media central de las bandas** (SMA 20). Nada más lejos. En un mercado lateral, buscar objetivos amplios es pedirle al precio algo que en rango no hace.

{get_svg_rango()}
"""
    idx_m5_start = text.find("# 📐 MÓDULO 5 · Los tres setups")
    idx_m6_start = text.find("# 🛡️ MÓDULO 6 · El stop y el objetivo")
    text = text[:idx_m5_start] + modulo_5_completo + "\n---\n\n" + text[idx_m6_start:]

    # Rediseño de Módulo 6: Reemplazo de bloques <pre> por Cajas de Fórmulas Elegantes
    modulo_6_completo = """# 🛡️ MÓDULO 6 · El stop y el objetivo

**Pregunta que responde**: ¿dónde pongo el stop y hasta dónde aspiro, sin inventar?

---

## 6.1 · El stop: dos reglas, en este orden

Aquí hay una idea que conviene entender antes que la mecánica. **El stop no se pone donde te duele menos: se pone donde la operación deja de tener sentido.** Un stop muy pegado al precio te saca por ruido normal; uno muy lejano te hace perder más de lo presupuestado.

El método resuelve esa tensión con una regla de dos pasos:

<div class="caja-formula">
  <div class="caja-formula-titulo">⚙️ Algoritmo de Determinación del Stop Loss</div>
  <div class="caja-formula-paso">
    <span class="caja-formula-badge">PASO 1</span> <strong>Mide la distancia al swing:</strong><br>
    <code>distancia = | precio_entrada − mínimo_últimas_20_velas |</code> <em>(en ventas: máximo de 20 velas)</em>
  </div>
  <div class="caja-formula-paso" style="margin-bottom:0;">
    <span class="caja-formula-badge">PASO 2</span> <strong>Evalúa la banda de volatilidad:</strong><br>
    • Si <code>0,5 × ATR ≤ distancia ≤ 1,5 × ATR</code> ➔ <strong>Stop = ese mínimo (o máximo)</strong><br>
    • Si la distancia queda fuera de la banda ➔ <strong>Stop = precio_entrada − 1,5 × ATR</strong>
  </div>
</div>

**La lógica de la banda de aceptación**: un swing real es el mejor stop posible, porque es un nivel que el mercado ya respetó. Pero solo si su distancia es razonable. Si el swing está demasiado cerca (menos de 0,5 ATR) te saca el primer movimiento aleatorio; si está demasiado lejos (más de 1,5 ATR) rompe tu presupuesto de riesgo. Cuando el swing no cae en esa banda, se usa la distancia fija por volatilidad.

> [!CAUTION]
> **No uses el mínimo de la vela de señal.** Es un error frecuente y caro. Ese mínimo suele estar mucho más cerca que 1,5 × ATR, y eso produce dos daños a la vez: te saca del trade por ruido normal **y** te hace calcular un lote mucho más grande del que corresponde, porque el lote es inversamente proporcional a la distancia al stop (Módulo 7).
>
> El stop de este método es el de las 20 velas o el de 1,5 × ATR. Nada más.

## 6.2 · El objetivo depende del tipo de mercado

| Tipo de operación | Primer objetivo | Segundo objetivo |
|---|---|---|
| **Tendencia** (ruptura y retroceso) | entrada + **1,0 × ATR** | entrada + **1,5 × ATR** |
| **Rango** (rebote en calma) | la **media central** de las bandas | no lleva |
| **Tendencia sostenida** (ver 6.4) | **sin objetivo fijo** | se arrastra el stop |

En ventas se resta en vez de sumar. El ATR es siempre el de 14 períodos en H1, el mismo con el que calculaste el stop.

## 6.3 · El filtro que cierra el módulo: riesgo/beneficio mínimo 1,0

Con el stop y el primer objetivo ya puestos, calculas:

<div class="caja-formula" style="border-left-color: #38BDF8;">
  <div class="caja-formula-titulo">📐 Cálculo de la Relación Riesgo / Beneficio (R:R)</div>
  <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; text-align: center; margin-top: 1mm;">
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:1.5mm; border-radius:4px;">
      <div style="font-size:7.5pt; color:#64748B; font-weight:700;">RIESGO INICIAL</div>
      <div style="font-family:'Space Grotesk', monospace; font-weight:700; color:#EF4444; font-size:8.5pt;">| Entrada − Stop |</div>
    </div>
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:1.5mm; border-radius:4px;">
      <div style="font-size:7.5pt; color:#64748B; font-weight:700;">BENEFICIO ESPERADO</div>
      <div style="font-family:'Space Grotesk', monospace; font-weight:700; color:#00DC82; font-size:8.5pt;">| Objetivo − Entrada |</div>
    </div>
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:1.5mm; border-radius:4px;">
      <div style="font-size:7.5pt; color:#64748B; font-weight:700;">RATIO MÍNIMO</div>
      <div style="font-family:'Space Grotesk', monospace; font-weight:700; color:#0F172A; font-size:8.5pt;">Beneficio / Riesgo ≥ 1,0</div>
    </div>
  </div>
</div>

**Si la relación queda bajo 1,0, la operación no se toma.** Sin excepciones, sin "pero el setup estaba lindo".

**Y esto ocurre más seguido de lo que parece.** Fíjate en la aritmética: cuando el stop cae en la rama de 1,5 × ATR y el primer objetivo está a 1,0 × ATR, la relación es 1,0 / 1,5 = **0,67**, y la operación se cae sola. Es el caso del ejemplo del Módulo 4.3.

Dicho de otro modo: **este método solo autoriza la operación cuando el stop pudo apoyarse en un swing cercano**, porque solo entonces el riesgo es menor que el objetivo. Ese es el filtro trabajando, no una falla.

## 6.4 · La salida asimétrica: cuando no hay objetivo fijo

En activos con sesgo fuerte y sostenido, sobre todo el **Oro**, el método **prohíbe el objetivo rígido**. La razón es del Módulo 2.6: cerrar en un objetivo fijo te saca de la tendencia que justamente querías acompañar.

Se reemplaza por un **stop que persigue al precio**:

<div class="caja-formula" style="border-left-color: #F59E0B;">
  <div class="caja-formula-titulo">🏹 Stop Dinámico Asimétrico (Chandelier Trailing Exit)</div>
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 1mm;">
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:2mm; border-radius:4px;">
      <strong style="color:#00DC82;">En Compras (Long):</strong><br>
      <code>Stop = Máximo(últimas 22 velas) − 3,0 × ATR(14)</code>
    </div>
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:2mm; border-radius:4px;">
      <strong style="color:#EF4444;">En Ventas (Short):</strong><br>
      <code>Stop = Mínimo(últimas 22 velas) + 3,0 × ATR(14)</code>
    </div>
  </div>
</div>

**Dos cosas que no se cambian:**

1. **El stop solo se mueve a favor.** Si el cálculo da un nivel peor que el actual, se ignora y el stop se queda donde está. Nunca se afloja.
2. **Las 22 velas y el 3,0 van juntos.** Son un par calibrado y separarlos deja el nivel indeterminado. Con 22 velas el nivel es utilizable; con 50, el "stop" puede quedar por encima del precio en una tendencia alcista normal, que es una contradicción y no un stop ceñido.

Contra la intuición: **una ventana más larga aprieta el stop, no lo suelta**, porque el máximo de más velas es más alto y el nivel resultante sube.

> [!IMPORTANT]
> **Costo de Acarreo (Swap Overnight) en operaciones multi-jornada**:
> Cuando una operación en Oro o Nasdaq utiliza el stop que persigue al precio y permanece abierta durante varias sesiones (cruzando el corte diario de las 17:00 NY), el broker cobra o abona el *swap* o *rollover*.
> 
> En contratos con swap negativo relevante, un mantenimiento de 3 a 5 días puede restar entre un 0,10 % y 0,25 % de la cuenta. Por esta razón, el **Módulo 7.1** establece el **Presupuesto de Riesgo Neto (buffer 90/10)**, garantizando que el swap acumulado jamás haga que la pérdida real supere el 1,0 %.

## 6.5 · Cuando la operación ya va ganando

Cuando el precio recorre la mitad del camino hacia el primer objetivo, o cuando cierra una vela H1 a tu favor, **puedes mover el stop al precio exacto de entrada**. A partir de ahí la operación no puede costarte dinero.

Es opcional y conservador: reduce tanto la pérdida posible como la probabilidad de aguantar hasta el segundo objetivo. Decídelo antes de entrar, no en el momento.
"""
    idx_m6_end = text.find("# 💰 MÓDULO 7 · El tamaño de la posición")
    text = text[:idx_m6_start] + modulo_6_completo + "\n---\n\n" + text[idx_m6_end:]

    MANUAL.write_text(text, encoding="utf-8")
    print(f"Manual v2.1 actualizado y estandarizado con 8 SVGs HD y Cajas de Fórmulas en {MANUAL}.")


if __name__ == "__main__":
    main()
