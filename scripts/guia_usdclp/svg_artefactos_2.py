# -*- coding: utf-8 -*-
"""Artefactos visuales vectoriales para la Guía USD/CLP (Parte 2)."""

def svg_diagrama_lotajes() -> str:
    return """
<div class="contenedor-diagrama">
<svg viewBox="0 0 680 150" xmlns="http://www.w3.org/2000/svg">
  <rect width="680" height="150" rx="8" fill="#0A181C" stroke="rgba(83, 193, 171, 0.25)" stroke-width="1.2"/>
  
  <rect x="20" y="12" width="640" height="32" rx="4" fill="#0F2B33" stroke="#53C1AB" stroke-width="1"/>
  <text x="30" y="32" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="11" font-weight="700">FÓRMULA REGLA DEL 1%:</text>
  <text x="210" y="32" fill="#FFFFFF" font-family="'Space Grotesk', monospace" font-size="11" font-weight="700">Lote = (Capital USD × 0.01) ÷ (Distancia SL CLP × $10 USD/CLP)</text>

  <rect x="20" y="52" width="205" height="60" rx="6" fill="#0E232A" stroke="rgba(83,193,171,0.3)" stroke-width="1"/>
  <text x="30" y="69" fill="#94A3B8" font-family="'Space Grotesk', monospace" font-size="10">CUENTA INICIAL</text>
  <text x="30" y="86" fill="#FFFFFF" font-family="'Goldman', sans-serif" font-size="14" font-weight="700">$1.000 USD</text>
  <text x="30" y="103" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="10.5" font-weight="700">Riesgo: $10 USD ➔ 0.01 Lotes</text>

  <rect x="237" y="52" width="205" height="60" rx="6" fill="#0E232A" stroke="#53C1AB" stroke-width="1.2"/>
  <text x="247" y="69" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="10" font-weight="700">CUENTA INTERMEDIA</text>
  <text x="247" y="86" fill="#FFFFFF" font-family="'Goldman', sans-serif" font-size="14" font-weight="700">$5.000 USD</text>
  <text x="247" y="103" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="10.5" font-weight="700">Riesgo: $50 USD ➔ 0.05 Lotes</text>

  <rect x="455" y="52" width="205" height="60" rx="6" fill="#0E232A" stroke="rgba(83,193,171,0.3)" stroke-width="1"/>
  <text x="465" y="69" fill="#94A3B8" font-family="'Space Grotesk', monospace" font-size="10">CUENTA AVANZADA</text>
  <text x="465" y="86" fill="#FFFFFF" font-family="'Goldman', sans-serif" font-size="14" font-weight="700">$10.000 USD</text>
  <text x="465" y="103" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="10.5" font-weight="700">Riesgo: $100 USD ➔ 0.10 Lotes</text>

  <rect x="20" y="120" width="640" height="22" rx="3" fill="#071418"/>
  <text x="30" y="135" fill="#FBBF24" font-family="'Space Grotesk', monospace" font-size="9.5" font-weight="700">MÉTRICA DE SUPERVIVENCIA:</text>
  <text x="210" y="135" fill="#E2E8F0" font-family="'Plus Jakarta Sans', sans-serif" font-size="9.5">20 pérdidas consecutivas al 1% = 81.8% de capital intacto. Sin riesgo de ruina.</text>
</svg>
</div>
"""

def svg_checklist_hud() -> str:
    return """
<div class="contenedor-diagrama">
<svg viewBox="0 0 680 140" xmlns="http://www.w3.org/2000/svg">
  <rect width="680" height="140" rx="8" fill="#0A181C" stroke="rgba(83, 193, 171, 0.25)" stroke-width="1.2"/>
  
  <text x="20" y="22" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="11" font-weight="700" letter-spacing="0.1em">TABLERO HUD · CHECKLIST PRE-OPERATIVO OBLIGATORIO DE 5 PASOS</text>
  <line x1="20" y1="28" x2="660" y2="28" stroke="rgba(83, 193, 171, 0.2)" stroke-width="1"/>

  <rect x="20" y="38" width="120" height="65" rx="5" fill="#0E232A" stroke="#53C1AB" stroke-width="1"/>
  <text x="28" y="54" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="10" font-weight="700">1. COBRE COPPER</text>
  <text x="28" y="70" fill="#FFFFFF" font-family="'Plus Jakarta Sans', sans-serif" font-size="9.5">Sesgo macro</text>
  <rect x="28" y="79" width="55" height="16" rx="3" fill="rgba(83,193,171,0.2)"/>
  <text x="35" y="91" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="9" font-weight="700">✓ VERIFICAR</text>

  <rect x="150" y="38" width="120" height="65" rx="5" fill="#0E232A" stroke="#53C1AB" stroke-width="1"/>
  <text x="158" y="54" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="10" font-weight="700">2. CALENDARIO</text>
  <text x="158" y="70" fill="#FFFFFF" font-family="'Plus Jakarta Sans', sans-serif" font-size="9.5">Sin IPoM/CPI &lt;2h</text>
  <rect x="158" y="79" width="55" height="16" rx="3" fill="rgba(83,193,171,0.2)"/>
  <text x="165" y="91" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="9" font-weight="700">✓ CLEAR</text>

  <rect x="280" y="38" width="120" height="65" rx="5" fill="#0E232A" stroke="#53C1AB" stroke-width="1"/>
  <text x="288" y="54" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="10" font-weight="700">3. ESTRUCTURA H1</text>
  <text x="288" y="70" fill="#FFFFFF" font-family="'Plus Jakarta Sans', sans-serif" font-size="9.5">Sobre EMA 50</text>
  <rect x="288" y="79" width="55" height="16" rx="3" fill="rgba(83,193,171,0.2)"/>
  <text x="295" y="91" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="9" font-weight="700">✓ ALINEADO</text>

  <rect x="410" y="38" width="120" height="65" rx="5" fill="#0E232A" stroke="#53C1AB" stroke-width="1"/>
  <text x="418" y="54" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="10" font-weight="700">4. RIESGO 1%</text>
  <text x="418" y="70" fill="#FFFFFF" font-family="'Plus Jakarta Sans', sans-serif" font-size="9.5">Lote por fórmula</text>
  <rect x="418" y="79" width="55" height="16" rx="3" fill="rgba(83,193,171,0.2)"/>
  <text x="425" y="91" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="9" font-weight="700">✓ EXACTO</text>

  <rect x="540" y="38" width="120" height="65" rx="5" fill="#0E232A" stroke="#53C1AB" stroke-width="1"/>
  <text x="548" y="54" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="10" font-weight="700">5. RATIO R:B</text>
  <text x="548" y="70" fill="#FFFFFF" font-family="'Plus Jakarta Sans', sans-serif" font-size="9.5">Mínimo 1:2 TP/SL</text>
  <rect x="548" y="79" width="55" height="16" rx="3" fill="rgba(83,193,171,0.2)"/>
  <text x="555" y="91" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="9" font-weight="700">✓ CARGADO</text>

  <rect x="20" y="110" width="640" height="22" rx="3" fill="#1A1212" stroke="#EF4444" stroke-width="0.8"/>
  <text x="30" y="125" fill="#F87171" font-family="'Space Grotesk', monospace" font-size="9.5" font-weight="700">CONDICIÓN INQUEBRANTABLE: SI UNO DE LOS 5 FILTROS NO SE CUMPLE, LA OPERACIÓN NO SE ABRE.</text>
</svg>
</div>
"""

def svg_timeline_sesiones() -> str:
    return """
<div class="contenedor-diagrama">
<svg viewBox="0 0 680 145" xmlns="http://www.w3.org/2000/svg">
  <rect width="680" height="145" rx="8" fill="#0A181C" stroke="rgba(83, 193, 171, 0.25)" stroke-width="1.2"/>
  
  <text x="20" y="22" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="11" font-weight="700" letter-spacing="0.1em">CRONOGRAMA DE LIQUIDEZ HORARIA EN SANTIAGO (HORA DE CHILE · CLT)</text>
  <line x1="20" y1="28" x2="660" y2="28" stroke="rgba(83, 193, 171, 0.2)" stroke-width="1"/>

  <line x1="40" y1="65" x2="640" y2="65" stroke="#334155" stroke-width="4" stroke-linecap="round"/>

  <rect x="100" y="48" width="60" height="34" rx="4" fill="#2A1414" stroke="#EF4444" stroke-width="1"/>
  <text x="130" y="69" text-anchor="middle" fill="#F87171" font-family="'Space Grotesk', monospace" font-size="9" font-weight="700">09:00 - 09:15</text>
  <text x="130" y="94" text-anchor="middle" fill="#EF4444" font-family="'Plus Jakarta Sans', sans-serif" font-size="9" font-weight="700">Spreads Altos</text>

  <rect x="175" y="42" width="280" height="46" rx="6" fill="#0D2E28" stroke="#53C1AB" stroke-width="1.8"/>
  <text x="315" y="64" text-anchor="middle" fill="#53C1AB" font-family="'Goldman', sans-serif" font-size="11" font-weight="700">09:15 A 12:30 CLT · LA VENTANA DE ORO</text>
  <text x="315" y="79" text-anchor="middle" fill="#E2E8F0" font-family="'Space Grotesk', monospace" font-size="9.5">Cruce Santiago + Apertura NY (09:30) + Metales Londres</text>
  <text x="315" y="103" text-anchor="middle" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="10" font-weight="700">★ MÁXIMA LIQUIDEZ Y MENORES SPREADS (0.20 - 0.35 CLP) ★</text>

  <rect x="470" y="48" width="70" height="34" rx="4" fill="#1E293B" stroke="#64748B" stroke-width="1"/>
  <text x="505" y="69" text-anchor="middle" fill="#94A3B8" font-family="'Space Grotesk', monospace" font-size="9" font-weight="700">12:30 - 13:30</text>
  <text x="505" y="94" text-anchor="middle" fill="#94A3B8" font-family="'Plus Jakarta Sans', sans-serif" font-size="9">Cierre Local</text>

  <rect x="555" y="48" width="85" height="34" rx="4" fill="#1C1818" stroke="#F59E0B" stroke-width="1"/>
  <text x="597" y="69" text-anchor="middle" fill="#FBBF24" font-family="'Space Grotesk', monospace" font-size="9" font-weight="700">13:30 EN ADELANTE</text>
  <text x="597" y="94" text-anchor="middle" fill="#FBBF24" font-family="'Plus Jakarta Sans', sans-serif" font-size="9">Off-shore / Iliquidez</text>

  <text x="30" y="132" fill="#CBD5E1" font-family="'Plus Jakarta Sans', sans-serif" font-size="9.5">Regla operativa: Opera tus órdenes en la Ventana de Oro y apaga la pantalla el resto del día para no sobreoperar.</text>
</svg>
</div>
"""

def svg_curva_drawdown() -> str:
    return """
<div class="contenedor-diagrama">
<svg viewBox="0 0 680 145" xmlns="http://www.w3.org/2000/svg">
  <rect width="680" height="145" rx="8" fill="#0A181C" stroke="rgba(83, 193, 171, 0.25)" stroke-width="1.2"/>
  
  <text x="20" y="22" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="11" font-weight="700" letter-spacing="0.1em">LA ASIMETRÍA DEL DRAWDOWN · POR QUÉ LA REGLA DEL 1% ES INNEGOCIABLE</text>
  <line x1="20" y1="28" x2="660" y2="28" stroke="rgba(83, 193, 171, 0.2)" stroke-width="1"/>

  <g transform="translate(20, 38)">
    <rect x="0" y="0" width="135" height="42" rx="4" fill="#0E2A22" stroke="#53C1AB" stroke-width="1"/>
    <text x="10" y="18" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="10" font-weight="700">PÉRDIDA: -5%</text>
    <text x="10" y="33" fill="#E2E8F0" font-family="'Space Grotesk', monospace" font-size="9.5">Requiere: +5.3% ganar</text>

    <rect x="145" y="0" width="135" height="42" rx="4" fill="#0E232A" stroke="#3E91AF" stroke-width="1"/>
    <text x="155" y="18" fill="#67E8F9" font-family="'Space Grotesk', monospace" font-size="10" font-weight="700">PÉRDIDA: -10%</text>
    <text x="155" y="33" fill="#E2E8F0" font-family="'Space Grotesk', monospace" font-size="9.5">Requiere: +11.1% ganar</text>

    <rect x="290" y="0" width="135" height="42" rx="4" fill="#1C1E14" stroke="#F59E0B" stroke-width="1"/>
    <text x="300" y="18" fill="#FBBF24" font-family="'Space Grotesk', monospace" font-size="10" font-weight="700">PÉRDIDA: -20%</text>
    <text x="300" y="33" fill="#E2E8F0" font-family="'Space Grotesk', monospace" font-size="9.5">Requiere: +25.0% ganar</text>

    <rect x="435" y="0" width="205" height="42" rx="4" fill="#2A1414" stroke="#EF4444" stroke-width="1.2"/>
    <text x="445" y="18" fill="#F87171" font-family="'Space Grotesk', monospace" font-size="10.5" font-weight="700">PÉRDIDA: -50% (QUIEBRA)</text>
    <text x="445" y="33" fill="#FFFFFF" font-family="'Space Grotesk', monospace" font-size="10" font-weight="700">REQUIERE: +100.0% DE GANANCIA</text>
  </g>

  <rect x="20" y="90" width="640" height="42" rx="4" fill="#071418" stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
  <text x="30" y="106" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="9.5" font-weight="700">CAMPOS AUDITABLES DEL TRADING JOURNAL:</text>
  <text x="30" y="122" fill="#94A3B8" font-family="'Space Grotesk', monospace" font-size="9">1. Fecha y Hora | 2. Nivel Spot y Cobre COPPER | 3. Razón Técnica | 4. Lotaje al 1% | 5. R:B Ratio | 6. Resultado en USD | 7. Sesgo Emocional</text>
</svg>
</div>
"""

def svg_ticket_mesa_tecnica() -> str:
    return """
<div class="contenedor-diagrama">
<svg viewBox="0 0 680 180" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="ticketGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0F2B33"/>
      <stop offset="50%" stop-color="#0B1E24"/>
      <stop offset="100%" stop-color="#071418"/>
    </linearGradient>
  </defs>
  
  <rect width="680" height="180" rx="10" fill="url(#ticketGrad)" stroke="#53C1AB" stroke-width="1.5"/>
  <line x1="510" y1="10" x2="510" y2="170" stroke="#53C1AB" stroke-width="1.5" stroke-dasharray="6,4"/>

  <rect x="25" y="18" width="170" height="20" rx="3" fill="rgba(83, 193, 171, 0.25)"/>
  <text x="32" y="32" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="9.5" font-weight="700">PASE VIP EXCLUSIVO</text>
  <text x="210" y="32" fill="#94A3B8" font-family="'Space Grotesk', monospace" font-size="9.5">GRUPO INTELIGENCIA SpA · RESEARCH &amp; ESTRATEGIA</text>

  <text x="25" y="62" fill="#FFFFFF" font-family="'Goldman', sans-serif" font-size="18" font-weight="700">CLÍNICA TÁCTICA USD/CLP EN VIVO</text>
  <text x="25" y="80" fill="#67E8F9" font-family="'Plus Jakarta Sans', sans-serif" font-size="11" font-weight="600">Sesión Técnica Especializada · Cada Martes 19:30 CLT (40 Minutos Estrictos)</text>

  <g transform="translate(25, 96)">
    <rect x="0" y="0" width="150" height="42" rx="4" fill="#061215" stroke="rgba(83,193,171,0.3)" stroke-width="1"/>
    <text x="8" y="16" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="9" font-weight="700">1. PANTALLA MT5 REAL</text>
    <text x="8" y="30" fill="#CBD5E1" font-family="'Plus Jakarta Sans', sans-serif" font-size="8.5">Niveles H1 y Spread en vivo</text>

    <rect x="160" y="0" width="155" height="42" rx="4" fill="#061215" stroke="rgba(83,193,171,0.3)" stroke-width="1"/>
    <text x="168" y="16" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="9" font-weight="700">2. PLANTILLA DE RIESGO</text>
    <text x="168" y="30" fill="#CBD5E1" font-family="'Plus Jakarta Sans', sans-serif" font-size="8.5">Calculadora 1% Excel/Sheets</text>

    <rect x="325" y="0" width="150" height="42" rx="4" fill="#061215" stroke="rgba(83,193,171,0.3)" stroke-width="1"/>
    <text x="333" y="16" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="9" font-weight="700">3. CONSULTORÍA DIRECTA</text>
    <text x="333" y="30" fill="#CBD5E1" font-family="'Plus Jakarta Sans', sans-serif" font-size="8.5">Respuestas con Analistas</text>
  </g>

  <text x="25" y="162" fill="#FBBF24" font-family="'Space Grotesk', monospace" font-size="9" font-weight="700">COORDINACIÓN: Contacta a tu asesor comercial asignado o responde al WhatsApp de entrega.</text>

  <text x="525" y="35" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="9" font-weight="700">TICKET ACCESO</text>
  <text x="525" y="55" fill="#FFFFFF" font-family="'Goldman', sans-serif" font-size="13" font-weight="700">MARTES</text>
  <text x="525" y="72" fill="#67E8F9" font-family="'Space Grotesk', monospace" font-size="12" font-weight="700">19:30 CLT</text>

  <g transform="translate(525, 86)">
    <rect x="0" y="0" width="3" height="40" fill="#53C1AB"/>
    <rect x="6" y="0" width="6" height="40" fill="#53C1AB"/>
    <rect x="15" y="0" width="2" height="40" fill="#53C1AB"/>
    <rect x="20" y="0" width="8" height="40" fill="#53C1AB"/>
    <rect x="32" y="0" width="4" height="40" fill="#53C1AB"/>
    <rect x="40" y="0" width="2" height="40" fill="#53C1AB"/>
    <rect x="46" y="0" width="7" height="40" fill="#53C1AB"/>
    <rect x="58" y="0" width="3" height="40" fill="#53C1AB"/>
    <rect x="65" y="0" width="5" height="40" fill="#53C1AB"/>
    <rect x="74" y="0" width="3" height="40" fill="#53C1AB"/>
    <rect x="81" y="0" width="6" height="40" fill="#53C1AB"/>
    <rect x="91" y="0" width="4" height="40" fill="#53C1AB"/>
    <rect x="99" y="0" width="2" height="40" fill="#53C1AB"/>
    <rect x="105" y="0" width="8" height="40" fill="#53C1AB"/>
    <rect x="117" y="0" width="3" height="40" fill="#53C1AB"/>
    <rect x="124" y="0" width="5" height="40" fill="#53C1AB"/>
  </g>
  <text x="525" y="142" fill="#94A3B8" font-family="'Space Grotesk', monospace" font-size="8">ID: GI-POSTVENTA-USDCLP</text>
  <text x="525" y="156" fill="#53C1AB" font-family="'Space Grotesk', monospace" font-size="8.5" font-weight="700">VALIDEZ: ACTIVA</text>
</svg>
</div>
"""
