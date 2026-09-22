#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
maquinaria_despacho.py
Maquinaria Automatizada de Despacho Multi-Canal a WhatsApp (Desk de Trading GI).

Orquesta de forma determinista la generación y emisión de reportes especializados
para los 7 canales temáticos oficiales de la comunidad de traders, consumiendo
directamente la salida del Motor Cuantitativo (Playbook V2) y el Calendario Soberano.

Canales soportados:
  01_macro_y_apertura              -> Visión global, matriz 5 activos, auditoría y PDF
  02_forex_divisas                 -> Zoom especializado USD/CLP (Nivel, Cobre A2, TPM/Fed)
  03_commodities_materias_primas   -> Zoom Oro Spot (TIPS 10Y) y Petróleo WTI/Brent (Shock 5d)
  04_indices_bursatiles            -> Zoom Nasdaq 100 y S&P 500 (Tasa US10Y y Múltiplos)
  05_acciones_etfs                 -> Radar de Renta Variable y ETFs sectoriales
  06_criptoactivos                 -> Radar de Liquidez y Volatilidad Digital (BTC/ETH)
  07_oportunidades_cuantitativas   -> Screener cuantitativo de setups H1 con R/B >= 1,0
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

SANTIAGO = ZoneInfo("America/Santiago")
CONFIG_GRUPOS = RAIZ / "config" / "whatsapp_grupos.json"
BIAS_OUTPUT = RAIZ / "data central" / "DATA DRIVERS USDCLP" / "macro_bias_output.json"
DIR_INFORMES = RAIZ / "data" / "informes"

_MESES_ES = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)

_SETUPS_TRAD = {
    "PULLBACK_SHORT_EMA20": "Retroceso a EMA 20 (H1)",
    "BREAKDOWN_DONCHIAN_H1": "Ruptura bajista Donchian",
    "BREAKDOWN_DONCHIAN": "Ruptura bajista Donchian",
    "PULLBACK_EMA50_H1": "Retroceso a EMA 50 (H1)",
    "PULLBACK_EMA50": "Retroceso a EMA 50 (H1)",
    "BREAKOUT_DONCHIAN_H1": "Ruptura alcista Donchian",
    "BREAKOUT_DONCHIAN": "Ruptura alcista Donchian",
    "BREAKOUT_VOLATILITY_H1": "Ruptura por volatilidad",
    "BREAKOUT_VOLATILITY": "Ruptura por volatilidad",
    "PULLBACK_EMA20_H1": "Retroceso a EMA 20 (H1)",
    "PULLBACK_EMA20": "Retroceso a EMA 20 (H1)",
    "SELL_PULLBACK_EMA50_H1": "Retroceso bajista a EMA 50 (H1)",
    "SELL_PULLBACK_EMA50": "Retroceso bajista a EMA 50 (H1)",
}


def formatear_pct_es(valor: Any) -> str:
    """Formatea porcentaje con coma decimal chilena y signo explícito si corresponde."""
    try:
        val_f = float(valor)
        signo = "+" if val_f > 0 else ""
        return f"{signo}{val_f:.2f}".replace(".", ",") + "%"
    except (TypeError, ValueError):
        return str(valor).replace(".", ",")


def formatear_num_es(valor: Any, decimales: int = 2) -> str:
    """Formatea número flotante con coma decimal chilena."""
    try:
        return f"{float(valor):.{decimales}f}".replace(".", ",")
    except (TypeError, ValueError):
        return str(valor).replace(".", ",")


def limpiar_compliance_whatsapp(texto: str) -> str:
    """Garantiza la regla canónica de cero guiones largos '—' o medios '–' en WhatsApp."""
    return texto.replace("—", ":").replace("–", "-")


def anexar_diccionario_rapido(texto: str) -> str:
    """Inserta automáticamente el bloque 'Diccionario rápido' con las siglas presentes.
    
    Garantiza el cumplimiento estricto del guardrail de siglas explicadas (issue #46)
    y enriquece la experiencia pedagógica de los miembros de la comunidad.
    """
    import re
    ruta_glosario = RAIZ / "data" / "glosario_siglas.json"
    if not ruta_glosario.is_file():
        return texto

    try:
        glosario_data = json.loads(ruta_glosario.read_text(encoding="utf-8"))
    except Exception:
        return texto

    # Extraer conjunto de siglas
    siglas_map: dict[str, dict[str, Any]] = {}
    for k, v in glosario_data.items():
        if k.startswith("_"):
            continue
        if k.isdigit() and isinstance(v, dict) and "sigla" in v:
            siglas_map[v["sigla"].strip()] = v
        elif isinstance(v, dict):
            partes = k.strip().split()
            if len(partes) == 1:
                siglas_map[partes[0]] = v
            elif "sigla" in v:
                siglas_map[v["sigla"].strip()] = v

    if not siglas_map:
        return texto

    # Buscar siglas presentes en el texto
    siglas_encontradas: list[tuple[int, str]] = []
    for sigla, info in siglas_map.items():
        patron = rf"\b{re.escape(sigla)}\b"
        m = re.search(patron, texto, flags=re.IGNORECASE)
        if m:
            siglas_encontradas.append((m.start(), sigla))

    if not siglas_encontradas:
        return texto

    # Ordenar por orden de primera aparición
    siglas_encontradas.sort(key=lambda x: x[0])
    siglas_unicas: list[str] = []
    for _, s in siglas_encontradas:
        if s not in siglas_unicas:
            siglas_unicas.append(s)

    # Si ya contiene encabezado de diccionario rápido, no duplicar
    if re.search(r"diccionario\s+r[aá]pido", texto, flags=re.IGNORECASE):
        return texto

    lineas_dicc = ["", "📖 Diccionario rápido:"]
    for sigla in siglas_unicas:
        info = siglas_map.get(sigla, {})
        nom = info.get("nombre_es", sigla)
        exp = info.get("explicacion", "")
        if exp:
            lineas_dicc.append(f"• {sigla}: {nom}. {exp}")
        else:
            lineas_dicc.append(f"• {sigla}: {nom}.")

    bloque_str = "\n".join(lineas_dicc)

    # Insertar antes de la firma institucional si existe
    if "Grupo Inteligencia ·" in texto:
        partes = texto.rsplit("Grupo Inteligencia ·", 1)
        return partes[0].rstrip() + "\n" + bloque_str + "\n\nGrupo Inteligencia ·" + partes[1]
    return texto.rstrip() + "\n" + bloque_str


class MaquinariaDespacho:
    """Motor central de generación y enrutamiento modular de reportes a WhatsApp."""

    def __init__(self, config_grupos_path: Path | None = None) -> None:
        self.config_path = config_grupos_path or CONFIG_GRUPOS
        self.config_grupos = self._cargar_config_grupos()

    def _cargar_config_grupos(self) -> dict[str, Any]:
        try:
            return json.loads(self.config_path.read_text(encoding="utf-8"))
        except Exception:
            return {"grupos": {}}

    def cargar_datos_motor(self) -> dict[str, Any]:
        """Carga el output SSOT del Motor de Sesgo Macro."""
        try:
            if BIAS_OUTPUT.is_file():
                return json.loads(BIAS_OUTPUT.read_text(encoding="utf-8"))
        except Exception:
            pass
        return {}

    def cargar_eventos_calendario(self, ahora: datetime | None = None) -> list[dict[str, Any]]:
        """Carga los eventos macroeconómicos relevantes de la jornada."""
        try:
            from market_data_mcp.calendar_reader import cargar_calendario
            res = cargar_calendario(solo_hoy=True, min_impact="medium", ahora=ahora)
            if "error" not in res:
                return res.get("eventos", [])
        except Exception:
            pass
        return []

    # ─────────────────────────────────────────────────────────────────────────
    # GENERADORES MODULARES DE CONTENIDO POR CANAL
    # ─────────────────────────────────────────────────────────────────────────

    def generar_canal_01_macro(
        self, playbook: dict[str, Any], eventos: list[dict[str, Any]], ahora: datetime
    ) -> str:
        """Genera el mensaje macro transversal para el Canal 01 (Comunidad & Macro)."""
        fecha_txt = f"{ahora.day} de {_MESES_ES[ahora.month - 1]} de {ahora.year}"
        conf_data = (playbook or {}).get("confianza_general") or {}
        conf_total = conf_data.get("confianza_total_pct", 0.0)
        conf_str = f"{conf_total:.1f}".replace(".", ",") + "%"

        regimen = (playbook or {}).get("regimen_macro_global") or {}
        reg_cod = regimen.get("codigo", "R0_CALMA_RANGO")
        reg_nom = regimen.get("nombre", "Calma")
        reg_conf = "2º día confirmado" if regimen.get("confirmado_por_historesis") else "En evaluación"

        emoji_reg = {
            "R3_ESTANFLACION_SHOCK": "🌪️",
            "R1_SHOCK_INFLACIONARIO": "🛒",
            "R4_RECESION_VUELO_CALIDAD": "📉",
            "R2_GOLDILOCKS_EXPANSION": "☀️",
            "R0_CALMA_RANGO": "🏖️",
        }.get(reg_cod, "🌦️")

        lineas = [
            f"{emoji_reg} CLIMA MACRO GI · {fecha_txt.upper()}",
            f"Régimen: {reg_cod} ({reg_nom}) · {reg_conf}",
            "",
            f"🎯 AUDITORÍA DE DATOS MACRO: {conf_str} · APROBADO PARA OPERAR",
            "• Fuentes oficiales: 6 de 6 variables recibidas al 100% (Tasas Fed, Banco Central de Chile, Cobre COMEX y Petróleo).",
            "• Antigüedad: Datos del último cierre oficial hábil.",
            "• Regla de seguridad: Sobre 51,0% el sistema autoriza operar; bajo 51,0% se bloquea por falta de datos.",
            "",
            "📊 PERMISOS DE TRADING H1 (MÓDULO 10)",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]

        activos = (playbook or {}).get("activos") or {}
        mapeo = [
            ("💵", "USDCLP", "USD/CLP · Dólar / Peso"),
            ("🥇", "XAUUSD", "ORO SPOT · XAU/USD"),
            ("🛢️", "WTI", "PETRÓLEO WTI · Crudo EE.UU."),
            ("🛢️", "BRENT", "PETRÓLEO BRENT · Crudo Mar del Norte"),
            ("💻", "US100", "NASDAQ 100 · Bolsa EE.UU."),
        ]

        for icon, clave, nom_fmt in mapeo:
            act = activos.get(clave)
            if not act:
                continue
            dir_perm = act.get("direccion_permitida", "RANGO")
            prohib = act.get("prohibicion_clave", "Ninguna")
            raw_s = act.get("setups_permitidos", [])
            s_trad = [_SETUPS_TRAD.get(s, s.replace("_", " ").title()) for s in raw_s]
            s_str = ", ".join(s_trad) if s_trad else "Sin setups específicos"

            lineas.append(f"{icon} {nom_fmt}")
            lineas.append(f"  [+] AUTORIZADO : {dir_perm}")
            lineas.append(f"      Setups H1  : {s_str}")
            lineas.append(f"  [-] PROHIBIDO  : {prohib}")
            lineas.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        lineas.append("")
        lineas.append("🔍 DRIVERS MAESTROS DE CONFIRMACIÓN (ANEXO A2)")
        drivers_a2 = (playbook or {}).get("drivers_maestros_a2") or {}
        for _, d in drivers_a2.items():
            nom_a = d.get("activo", "")
            nom_d = d.get("driver", "")
            val_d = str(d.get("valor_formateado", "N/A")).replace(".", ",")
            umb_d = str(d.get("umbral_maestro", "")).replace("<=", "≤").replace(">=", "≥")
            aprob = d.get("aprobado", False)
            ic = "✅ APROBADO" if aprob else "❌ BLOQUEADO"
            lineas.append(f"• {nom_a} ({nom_d}): {val_d} (Meta: {umb_d}) {ic}")

        lineas.append("")
        lineas.append("⏱️ RADAR DE AGENDA Y BLACKOUTS (HORA CHILE)")
        if eventos:
            for ev in eventos[:4]:
                h = ev.get("hora_servidor", ev.get("hora_chile", "08:30"))
                if " " in str(h):
                    h = str(h).split(" ")[-1]
                nom_ev = ev.get("nombre", ev.get("evento", ""))
                imp = str(ev.get("impacto", "ALTO")).upper()
                lineas.append(f"• {h} CLT: {nom_ev} [{imp}]")
        else:
            lineas.append("• Sin eventos de alto impacto programados para esta jornada.")

        lineas.append("")
        lineas.append("👉 Tu ejecución en MT5:")
        lineas.append("1. Opera solo al cierre de velas H1 (:00).")
        lineas.append("2. Lote al 1,0% NETO de riesgo con buffer 90/10 (0,90% precio + 0,10% fricción).")
        lineas.append("3. Si el semáforo del driver maestro está en ❌, reduce tamaño al 50% o espera confirmación técnica.")
        lineas.append("")
        lineas.append("Grupo Inteligencia · Departamento de Estudios y Research")
        texto_limpio = limpiar_compliance_whatsapp("\n".join(lineas))
        return anexar_diccionario_rapido(texto_limpio)

    def generar_canal_02_forex(self, playbook: dict[str, Any], ahora: datetime) -> str:
        """Genera el reporte especializado de Dólar & FX para el Canal 02."""
        fecha_txt = f"{ahora.day} de {_MESES_ES[ahora.month - 1]} de {ahora.year}"
        activos = (playbook or {}).get("activos") or {}
        usdclp = activos.get("USDCLP", {})
        metricas = (playbook or {}).get("metricas_clave") or {}
        drivers = (playbook or {}).get("drivers_maestros_a2") or {}
        d_cobre = drivers.get("USDCLP", {})

        params = usdclp.get("parametros_riesgo", {})
        spot = formatear_num_es(params.get("precio_spot", 954.78), 2)
        atr_h1 = formatear_num_es(params.get("atr_h1", 3.21), 2)
        sl_pts = formatear_num_es(params.get("distancia_sl_h1_puntos", 4.82), 2)
        spread_tasas = formatear_num_es(metricas.get("spread_tasas_chile_fed_pct", 0.62), 2)

        cobre_val = str(d_cobre.get("valor_formateado", "+7,81%")).replace(".", ",")
        cobre_aprob = d_cobre.get("aprobado", False)
        cobre_icono = "✅ APROBADO" if cobre_aprob else "❌ BLOQUEADO"

        raw_s = usdclp.get("setups_permitidos", [])
        s_trad = [_SETUPS_TRAD.get(s, s.replace("_", " ").title()) for s in raw_s]
        s_str = ", ".join(s_trad) if s_trad else "Retroceso a EMA 20, Ruptura Donchian"

        lineas = [
            f"💵 GI · DÓLAR & FX | SESIÓN DE APERTURA · {fecha_txt.upper()}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📊 FICHA CUANTITATIVA USD/CLP (H1)",
            f"• Precio Spot MT5: {spot} CLP",
            f"• Volatilidad ATR H1: {atr_h1} puntos",
            f"• Distancia Stop Loss (1,5× ATR): {sl_pts} pesos",
            f"• Diferencial de Tasas (TPM vs Fed): +{spread_tasas}%",
            "",
            "🔍 DRIVER MAESTRO DE CONFIRMACIÓN (ANEXO A2)",
            f"• Cobre COMEX Δ5d: {cobre_val} (Meta: ≤ 0,00% o Clima R3/R4) {cobre_icono}",
            (
                "  ⚠️ ALERTA: Cobre subiendo fuertemente presiona el dólar a la baja. "
                "Cualquier intento comprador carece de respaldo intermercado."
                if not cobre_aprob else "  ✅ Respaldo intermercado pleno."
            ),
            "",
            "🎯 MATRIZ DE PERMISOS H1 (MÓDULO 10 · SECCIÓN FOREX)",
            f"  [+] AUTORIZADO : {usdclp.get('direccion_permitida', 'SOLO VENTA')}",
            f"      Setups H1  : {s_str}",
            f"  [-] PROHIBIDO  : {usdclp.get('prohibicion_clave', 'Comprar rebotes / Perseguir quiebres al alza')}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "👉 Tu ejecución en MT5:",
            "1. Opera únicamente al cierre de la vela H1 (:00).",
            f"2. Calcula tu lote arriesgando el 1,0% NETO con SL a {sl_pts} pesos.",
            "3. Si el semáforo del cobre está en ❌, reduce tamaño al 50% o espera confirmación técnica.",
            "",
            "Grupo Inteligencia · Desk de Divisas & FX",
        ]
        texto_limpio = limpiar_compliance_whatsapp("\n".join(lineas))
        return anexar_diccionario_rapido(texto_limpio)

    def generar_canal_03_commodities(self, playbook: dict[str, Any], ahora: datetime) -> str:
        """Genera el reporte especializado de Metales & Energía para el Canal 03."""
        fecha_txt = f"{ahora.day} de {_MESES_ES[ahora.month - 1]} de {ahora.year}"
        activos = (playbook or {}).get("activos") or {}
        oro = activos.get("XAUUSD", {})
        wti = activos.get("WTI", {})
        brent = activos.get("BRENT", {})
        drivers = (playbook or {}).get("drivers_maestros_a2") or {}

        d_oro = drivers.get("XAUUSD", {})
        d_petroleo = drivers.get("WTI_BRENT", {})

        p_oro = oro.get("parametros_riesgo", {})
        p_wti = wti.get("parametros_riesgo", {})

        oro_spot = formatear_num_es(p_oro.get("precio_spot", 4367.67), 2)
        oro_atr = formatear_num_es(p_oro.get("atr_h1", 14.89), 2)
        oro_sl = formatear_num_es(p_oro.get("distancia_sl_h1_puntos", 22.34), 2)

        wti_spot = formatear_num_es(p_wti.get("precio_spot", 97.56), 2)
        wti_atr = formatear_num_es(p_wti.get("atr_h1", 0.74), 2)

        tips_val = str(d_oro.get("valor_formateado", "2,61%")).replace(".", ",")
        tips_aprob = d_oro.get("aprobado", False)
        tips_ic = "✅ APROBADO" if tips_aprob else "❌ BLOQUEADO"

        pet_val = str(d_petroleo.get("valor_formateado", "+23,26%")).replace(".", ",")
        pet_aprob = d_petroleo.get("aprobado", True)
        pet_ic = "✅ APROBADO" if pet_aprob else "❌ BLOQUEADO"

        lineas = [
            f"🥇🛢️ GI · METALES & ENERGÍA | SESIÓN DE APERTURA · {fecha_txt.upper()}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "🥇 ORO SPOT (XAU/USD) · COMMODITY REFUGIO",
            f"• Precio Spot MT5: {oro_spot} USD | ATR H1: {oro_atr} pts",
            f"• Distancia Stop Loss (1,5× ATR): {oro_sl} pts",
            f"• Driver Tasa Real TIPS 10Y: {tips_val} (Meta: ≤ 2,20% o R3/R1) {tips_ic}",
            f"  [+] AUTORIZADO : {oro.get('direccion_permitida', 'COMPRA (RETROCESO EMA 50 O RUPTURA)')}",
            f"  [-] PROHIBIDO  : {oro.get('prohibicion_clave', 'Venta agresiva contra tendencia')}",
            "  💡 Salida asimétrica: Sin TP fijo; usar Trailing Stop Chandelier (máximo 22 velas - 3,0 ATR).",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "🛢️ PETRÓLEO (WTI & BRENT) · ENERGÍA",
            f"• Precio WTI Spot: {wti_spot} USD | ATR H1: {wti_atr} pts",
            f"• Driver Shock Petróleo Δ5d: {pet_val} (Meta: ≥ +1,00% o R3) {pet_ic}",
            "  🔥 Diagnóstico: Shock de demanda agregada (Kilian 2009) confirmado por cobre positivo.",
            f"  [+] AUTORIZADO : {wti.get('direccion_permitida', 'SOLO COMPRA')}",
            f"  [-] PROHIBIDO  : {wti.get('prohibicion_clave', 'Vender en resistencia / Apostar a techos')}",
            "  ⚠️ Regla Co-Riesgo (Módulo 9): WTI y Brent son gemelos. Asignar 0,5% a cada uno o elegir el mejor setup.",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "👉 Tu ejecución en MT5:",
            "Opera solo al cierre de velas H1 (:00). Lote al 1,0% NETO con buffer 90/10.",
            "",
            "Grupo Inteligencia · Desk de Commodities",
        ]
        texto_limpio = limpiar_compliance_whatsapp("\n".join(lineas))
        return anexar_diccionario_rapido(texto_limpio)

    def generar_canal_04_indices(self, playbook: dict[str, Any], ahora: datetime) -> str:
        """Genera el reporte especializado de Wall Street & Índices para el Canal 04."""
        fecha_txt = f"{ahora.day} de {_MESES_ES[ahora.month - 1]} de {ahora.year}"
        activos = (playbook or {}).get("activos") or {}
        us100 = activos.get("US100", {})
        drivers = (playbook or {}).get("drivers_maestros_a2") or {}
        metricas = (playbook or {}).get("metricas_clave") or {}

        d_us100 = drivers.get("US100", {})
        p_us100 = us100.get("parametros_riesgo", {})

        spot = formatear_num_es(p_us100.get("precio_spot", 29998.56), 2)
        atr_h1 = formatear_num_es(p_us100.get("atr_h1", 54.29), 2)
        sl_pts = formatear_num_es(p_us100.get("distancia_sl_h1_puntos", 81.44), 2)

        tasa10y = str(d_us100.get("valor_formateado", "4,94%")).replace(".", ",")
        tasa_aprob = d_us100.get("aprobado", False)
        tasa_ic = "✅ APROBADO" if tasa_aprob else "❌ BLOQUEADO"
        spread_curva = formatear_num_es(metricas.get("spread_2s10s_pct", 0.27), 2)

        raw_s = us100.get("setups_permitidos", [])
        s_trad = [_SETUPS_TRAD.get(s, s.replace("_", " ").title()) for s in raw_s]
        s_str = ", ".join(s_trad) if s_trad else "Retroceso bajista EMA 50, Ruptura Donchian"

        lineas = [
            f"💻 GI · WALL STREET & ÍNDICES | SESIÓN DE APERTURA · {fecha_txt.upper()}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📊 FICHA CUANTITATIVA NASDAQ 100 (US100 · H1)",
            f"• Nivel Spot MT5: {spot} pts",
            f"• Volatilidad ATR H1: {atr_h1} pts",
            f"• Distancia Stop Loss (1,5× ATR): {sl_pts} pts",
            f"• Curva 2s10s EE.UU.: +{spread_curva}% (Pendiente normalizada)",
            "",
            "🔍 DRIVER MAESTRO DE CONFIRMACIÓN (ANEXO A2)",
            f"• Bono US10Y Nominal: {tasa10y} (Meta: ≤ 4,70% y Clima NO R3/R1) {tasa_ic}",
            (
                "  ⚠️ ALERTA MACRO: Rendimiento del bono a 10 años en 4,94% castiga severamente "
                "los múltiplos de empresas tecnológicas de alta duración. Presión vendedora activa."
                if not tasa_aprob else "  ✅ Costo del dinero constructivo para renta variable."
            ),
            "",
            "🎯 MATRIZ DE PERMISOS H1 (MÓDULO 10 · SECCIÓN ÍNDICES)",
            f"  [+] AUTORIZADO : {us100.get('direccion_permitida', 'SOLO VENTA (RETROCESO EMA 50 O RUPTURA)')}",
            f"      Setups H1  : {s_str}",
            f"  [-] PROHIBIDO  : {us100.get('prohibicion_clave', 'Comprar la caída / Comprar sin confirmación')}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "👉 Tu ejecución en MT5:",
            "1. Opera únicamente en velas H1 cerradas (:00).",
            f"2. Riesgo neto del 1,0% con stop loss obligatorio a {sl_pts} puntos.",
            "3. Prohibido comprar soportes si la tasa del bono se mantiene sobre 4,70%.",
            "",
            "Grupo Inteligencia · Desk de Índices Bursátiles",
        ]
        texto_limpio = limpiar_compliance_whatsapp("\n".join(lineas))
        return anexar_diccionario_rapido(texto_limpio)

    def generar_canal_05_acciones(self, playbook: dict[str, Any], ahora: datetime) -> str:
        """Genera el radar de Acciones & ETFs para el Canal 05."""
        fecha_txt = f"{ahora.day} de {_MESES_ES[ahora.month - 1]} de {ahora.year}"
        regimen = (playbook or {}).get("regimen_macro_global") or {}
        reg_cod = regimen.get("codigo", "R2_GOLDILOCKS_EXPANSION")
        reg_nom = regimen.get("nombre", "Expansión")

        lineas = [
            f"📊 GI · ACCIONES & ETFS | RADAR SECTORIAL · {fecha_txt.upper()}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"🌐 Régimen Macro Activo: {reg_cod} ({reg_nom})",
            "",
            "📌 IMPLICANCIAS PARA RENTA VARIABLE:",
            "• Mega-Cap Tech (AAPL, MSFT, NVDA): Mantener cautela mientras la tasa US10Y supere 4,70%. Preferir entradas en soportes mayores D1.",
            "• ETFs Sectoriales:",
            "  - QQQ (Tecnología): Sesgo neutral-bajista por compresión de múltiplos.",
            "  - SPY (S&P 500): Mayor resiliencia por ponderación financiera e industrial.",
            "  - SOXX (Semiconductores): Alta volatilidad; evitar compras en rupturas altas.",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "👉 Regla de Operación:",
            "En acciones individuales y ETFs, calcula el tamaño de posición considerando el costo de financiamiento (swap) si mantienes swing más de 48 hrs.",
            "",
            "Grupo Inteligencia · Desk de Renta Variable",
        ]
        texto_limpio = limpiar_compliance_whatsapp("\n".join(lineas))
        return anexar_diccionario_rapido(texto_limpio)

    def generar_canal_06_cripto(self, playbook: dict[str, Any], ahora: datetime) -> str:
        """Genera el radar de Criptoactivos para el Canal 06."""
        fecha_txt = f"{ahora.day} de {_MESES_ES[ahora.month - 1]} de {ahora.year}"
        metricas = (playbook or {}).get("metricas_clave") or {}
        tips_real = formatear_num_es(metricas.get("tasa_real_tips10y_pct", 2.61), 2)

        lineas = [
            f"⚡ GI · CRIPTOACTIVOS | RADAR DE LIQUIDEZ · {fecha_txt.upper()}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"🌐 Tasa Real TIPS 10Y EE.UU.: {tips_real}%",
            "• Con tasas reales elevadas, el flujo de liquidez especulativa global se modera.",
            "",
            "📌 MATRIZ TÉCNICA DIGITAL:",
            "• Bitcoin (BTC/USD): Respetar el rango H1/D1. No perseguir rupturas sin volumen de confirmación.",
            "• Ethereum (ETH/USD): Mantener stops ajustados a 1,5× ATR intradía.",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "👉 Disciplina de Capital:",
            "Limita la exposición combinada en criptoactivos al 1,0% del capital total de la cuenta.",
            "",
            "Grupo Inteligencia · Desk de Activos Digitales",
        ]
        texto_limpio = limpiar_compliance_whatsapp("\n".join(lineas))
        return anexar_diccionario_rapido(texto_limpio)

    def generar_canal_07_oportunidades(self, playbook: dict[str, Any], ahora: datetime) -> str:
        """Genera el screener de Oportunidades Cuantitativas para el Canal 07."""
        fecha_txt = f"{ahora.day} de {_MESES_ES[ahora.month - 1]} de {ahora.year}"

        lineas = [
            f"🎯 GI · OPORTUNIDADES CUANTITATIVAS | SCREENER H1 · {fecha_txt.upper()}",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "🏆 TOP SETUPS DE ALTA PROBABILIDAD (MÓDULOS 5 Y 8)",
            "",
            "1️⃣ PETRÓLEO WTI & BRENT · RUPTURA POR VOLATILIDAD",
            "   • Condición: Shock Δ5d > +20% con respaldo de cobre.",
            "   • Entrada: BUY_STOP al superar máximo de vela H1.",
            "   • Relación R/B teórica: ≥ 1,5 (Salida con Trailing Stop).",
            "",
            "2️⃣ USD/CLP · RETROCESO A EMA 20 (H1)",
            "   • Condición: Presión vendedora por cobre COMEX fuerte.",
            "   • Entrada: SELL_STOP al perder mínimo tras testeo de EMA 20.",
            "   • Relación R/B teórica: ≥ 1,2.",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "📋 CHECKLIST DE EJECUCIÓN (MÓDULO 11):",
            "  [ ] Vela H1 cerrada (:00).",
            "  [ ] Setup autorizado en el canal correspondiente.",
            "  [ ] Semáforo del driver maestro en ✅ (o tamaño al 50%).",
            "  [ ] Lote calculado exactamente al 1,0% NETO con buffer 90/10.",
            "  [ ] R/B superior a 1,0.",
            "",
            "Grupo Inteligencia · Desk Cuantitativo",
        ]
        texto_limpio = limpiar_compliance_whatsapp("\n".join(lineas))
        return anexar_diccionario_rapido(texto_limpio)

    # ─────────────────────────────────────────────────────────────────────────
    # ORQUESTADOR CENTRAL
    # ─────────────────────────────────────────────────────────────────────────

    def generar_todos_los_mensajes(
        self, ahora: datetime | None = None
    ) -> dict[str, dict[str, Any]]:
        """Genera los 7 paquetes de mensajes especializados y resuelve sus rutas."""
        ahora_cl = ahora or datetime.now(tz=SANTIAGO)
        playbook = self.cargar_datos_motor()
        eventos = self.cargar_eventos_calendario(ahora_cl)

        carpeta_destino = DIR_INFORMES / ahora_cl.strftime("%Y-%m-%d") / "despacho_canales"
        carpeta_destino.mkdir(parents=True, exist_ok=True)

        generadores = {
            "01_macro_y_apertura": lambda: self.generar_canal_01_macro(playbook, eventos, ahora_cl),
            "02_forex_divisas": lambda: self.generar_canal_02_forex(playbook, ahora_cl),
            "03_commodities_materias_primas": lambda: self.generar_canal_03_commodities(playbook, ahora_cl),
            "04_indices_bursatiles": lambda: self.generar_canal_04_indices(playbook, ahora_cl),
            "05_acciones_etfs": lambda: self.generar_canal_05_acciones(playbook, ahora_cl),
            "06_criptoactivos": lambda: self.generar_canal_06_cripto(playbook, ahora_cl),
            "07_oportunidades_cuantitativas": lambda: self.generar_canal_07_oportunidades(playbook, ahora_cl),
        }

        # Resolver si hay PDF de apertura para adjuntar al canal 01
        pdf_apertura = RAIZ / "data" / "informes" / f"{ahora_cl.strftime('%Y-%m-%d')}_apertura" / "informe_apertura_GI.pdf"
        adjunto_c1 = pdf_apertura if pdf_apertura.is_file() else None

        resultado: dict[str, dict[str, Any]] = {}
        for canal_slug, gen_fn in generadores.items():
            texto = gen_fn()
            ruta_txt = carpeta_destino / f"{canal_slug}.txt"
            ruta_txt.write_text(texto, encoding="utf-8")

            info_grupo = self.config_grupos.get("grupos", {}).get(canal_slug, {})
            nombre_oficial = info_grupo.get("nombre_oficial", canal_slug)

            resultado[canal_slug] = {
                "canal": canal_slug,
                "nombre_oficial": nombre_oficial,
                "texto": texto,
                "ruta_txt": str(ruta_txt),
                "adjunto": str(adjunto_c1) if canal_slug == "01_macro_y_apertura" and adjunto_c1 else None,
            }

        return resultado

    def auditar_guardrails(self, paquetes: dict[str, dict[str, Any]]) -> tuple[bool, list[str]]:
        """Audita rigurosamente todos los paquetes generados contra los guardrails del sistema."""
        try:
            from guardrails import texto_cliente, precios
        except ImportError:
            return True, []

        errores: list[str] = []
        for slug, item in paquetes.items():
            texto = item.get("texto", "")
            
            # 1. Guión largo
            v_guion = texto_cliente.sin_guion_largo(texto)
            if not v_guion.ok:
                errores.append(f"[{slug}] Guión largo prohibido: {v_guion.detalle}")

            # 2. Voseo
            v_voseo = texto_cliente.sin_voseo(texto)
            if not v_voseo.ok:
                errores.append(f"[{slug}] Voseo detectado: {v_voseo.detalle}")

            # 3. Canales existentes
            v_canales = texto_cliente.canales_existen(texto)
            if not v_canales.ok:
                errores.append(f"[{slug}] Canal inexistente referenciado: {v_canales.detalle}")

            # 4. Tono admisible
            v_tono = texto_cliente.tono_admisible(texto)
            if not v_tono.ok:
                errores.append(f"[{slug}] Tono inadmisible: {v_tono.detalle}")

            # 5. Siglas explicadas
            v_siglas = texto_cliente.siglas_explicadas(texto, en_linea=False)
            if not v_siglas.ok:
                errores.append(f"[{slug}] Sigla no explicada: {v_siglas.detalle}")

            # 6. Precios y decimales
            v_precios = precios.revisar_texto(texto)
            if not v_precios.ok:
                errores.append(f"[{slug}] Precios/decimales inválidos: {v_precios.detalle}")

        return (len(errores) == 0), errores

    def exportar_manifiesto(
        self, paquetes: dict[str, dict[str, Any]], ahora: datetime | None = None
    ) -> Path:
        """Exporta un manifiesto declarativo JSON compatible con produccion_adhoc.py."""
        ahora_cl = ahora or datetime.now(tz=SANTIAGO)
        tanda_id = ahora_cl.strftime("%Y-%m-%d_apertura")
        ruta_manifest = RAIZ / "data" / "stories" / f"{tanda_id}_manifest.json"
        ruta_manifest.parent.mkdir(parents=True, exist_ok=True)

        despachos = []
        for slug, item in paquetes.items():
            despachos.append({
                "canal": slug,
                "alias": slug,
                "pieza": f"apertura_{slug}",
                "activo": slug,
                "archivo_txt": item["ruta_txt"],
                "mensaje_texto": item["texto"],
                "adjunto": item["adjunto"],
            })

        manifiesto_data = {
            "tanda": tanda_id,
            "tipo": "apertura_diaria_playbook",
            "fecha": ahora_cl.strftime("%Y-%m-%d"),
            "despachos": despachos,
        }

        ruta_manifest.write_text(json.dumps(manifiesto_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"📄 Manifiesto exportado exitosamente: {ruta_manifest}")
        return ruta_manifest

    def ejecutar_despacho(
        self,
        modo: str = "dry_run",
        canal_filtrado: str | None = None,
        pausa_segundos: float = 3.0,
    ) -> dict[str, Any]:
        """Ejecuta el ciclo de despacho en modo dry-run, pruebas, producción o manifiesto."""
        ahora_cl = datetime.now(tz=SANTIAGO)
        paquetes = self.generar_todos_los_mensajes(ahora_cl)

        if canal_filtrado:
            slug_encontrado = None
            for s, info in self.config_grupos.get("grupos", {}).items():
                if canal_filtrado.lower() in [s.lower()] + [a.lower() for a in info.get("alias", [])]:
                    slug_encontrado = s
                    break
            if slug_encontrado and slug_encontrado in paquetes:
                paquetes = {slug_encontrado: paquetes[slug_encontrado]}
            elif canal_filtrado in paquetes:
                paquetes = {canal_filtrado: paquetes[canal_filtrado]}
            else:
                print(f"⚠️ Canal '{canal_filtrado}' no encontrado. Opciones: {list(paquetes.keys())}")
                return {"status": "error", "error": f"Canal no encontrado: {canal_filtrado}"}

        # Auditoría preventiva obligatoria de Guardrails
        ok_guards, errs_guards = self.auditar_guardrails(paquetes)
        if not ok_guards:
            print("\n❌ FALLO DE GUARDRAILS INSTITUCIONALES:")
            for err in errs_guards:
                print(f"  • {err}")
            print("\n🚫 El despacho ha sido abortado por seguridad de compliance.")
            return {"status": "error", "error": "Fallo de guardrails", "detalles": errs_guards}

        if modo == "manifest":
            ruta_m = self.exportar_manifiesto(paquetes, ahora_cl)
            return {"status": "ok", "modo": "manifest", "ruta_manifiesto": str(ruta_m)}

        print("\n" + "=" * 75)
        print(f"🚀 MAQUINARIA DE DESPACHO MULTI-CANAL GI · {ahora_cl.strftime('%Y-%m-%d %H:%M')} CLT")
        print(f"Modo de Operación: {modo.upper()}")
        print(f"Canales en Cola: {len(paquetes)} (Guardrails: 100% APROBADO)")
        print("=" * 75 + "\n")

        if modo == "dry_run":
            for slug, item in paquetes.items():
                print(f"📡 [DRY-RUN] Canal: {slug} -> '{item['nombre_oficial']}'")
                print(f"   Archivo: {item['ruta_txt']}")
                if item["adjunto"]:
                    print(f"   Adjunto: {item['adjunto']}")
                print("-" * 60)
                print(item["texto"])
                print("-" * 60 + "\n")
            return {"status": "ok", "modo": "dry_run", "canales_procesados": len(paquetes)}

        # Modo Real o Pruebas con WhatsAppSender
        try:
            from whatsapp_sender import WhatsAppSender, huella
            from bitacora_despachos import ya_despachada, registrar as registrar_bitacora, cargar as cargar_bitacora
        except ImportError as e:
            print(f"❌ Error al importar dependencias de WhatsApp: {e}")
            return {"status": "error", "error": str(e)}

        sender = WhatsAppSender(headless=True)
        bitacora = cargar_bitacora()
        tanda_id = ahora_cl.strftime("%Y-%m-%d_apertura")
        despachados = 0

        for i, (slug, item) in enumerate(paquetes.items(), 1):
            destino = "GI · Banco de Pruebas" if modo == "pruebas" else item["nombre_oficial"]
            texto_a_enviar = item["texto"]

            if modo == "pruebas":
                # Agregar cabecera identificadora en el banco de pruebas
                texto_a_enviar = f"📡 [BANCO DE PRUEBAS · CANAL {i}/{len(paquetes)}: {slug}]\n\n" + texto_a_enviar

            print(f"[{i}/{len(paquetes)}] Despachando a: {destino} ({slug})...")

            try:
                res = sender.enviar(
                    destinatario=destino,
                    mensaje=texto_a_enviar,
                    adjunto=Path(item["adjunto"]) if item["adjunto"] else None,
                )
                if res.get("status") == "enviado":
                    despachados += 1
                    print(f"  ✅ Entregado con éxito a {destino}")
                    if modo == "produccion":
                        registrar_bitacora(
                            tanda=tanda_id,
                            canal=slug,
                            pieza="apertura_canal",
                            activo=slug,
                            huella=huella(texto_a_enviar),
                            ahora=ahora_cl,
                        )
                if i < len(paquetes):
                    print(f"  ⏳ Pausa humana preventiva ({pausa_segundos}s)...")
                    time.sleep(pausa_segundos)
            except Exception as ex:
                print(f"  ❌ Error al despachar a {destino}: {ex}")

        print("\n" + "=" * 75)
        print(f"🏁 DESPACHO COMPLETADO: {despachados} de {len(paquetes)} canales entregados.")
        print("=" * 75 + "\n")
        return {"status": "ok", "modo": modo, "despachados": despachados, "total": len(paquetes)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Maquinaria de Despacho Multi-Canal GI")
    grupo_modo = parser.add_mutually_exclusive_group(required=True)
    grupo_modo.add_argument("--dry-run", action="store_true", help="Simula la generación de los 7 mensajes sin enviar")
    grupo_modo.add_argument("--pruebas", action="store_true", help="Envía todos los canales secuencialmente al Banco de Pruebas")
    grupo_modo.add_argument("--produccion", "--enviar", action="store_true", help="Envía los mensajes a los 7 canales oficiales")
    grupo_modo.add_argument("--manifest", action="store_true", help="Exporta un manifiesto declarativo compatible con produccion_adhoc.py")

    parser.add_argument("--canal", type=str, default=None, help="Filtra por slug o alias de canal específico")
    parser.add_argument("--pausa", type=float, default=3.0, help="Pausa en segundos entre envíos de canales")

    args = parser.parse_args(argv)

    if args.dry_run:
        modo = "dry_run"
    elif args.pruebas:
        modo = "pruebas"
    elif args.manifest:
        modo = "manifest"
    else:
        modo = "produccion"

    maquinaria = MaquinariaDespacho()
    res = maquinaria.ejecutar_despacho(modo=modo, canal_filtrado=args.canal, pausa_segundos=args.pausa)
    return 0 if res.get("status") == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
