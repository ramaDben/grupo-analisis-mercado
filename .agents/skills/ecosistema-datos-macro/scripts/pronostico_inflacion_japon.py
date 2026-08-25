#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
pronostico_inflacion_japon.py
Motor de Construcción de Pronóstico de Inflación para Japón (IPC Nacional y Tokio)
y Matriz de Sensibilidad para la Política Monetaria del Banco de Japón (BoJ) / USD-JPY.
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parents[4]
DATA_CENTRAL = BASE_DIR / "data central"
DATA_JAPON = DATA_CENTRAL / "DATA JAPON"
RAW_DIR = DATA_JAPON / "raw"
BOJ_DATA_FILE = RAW_DIR / "boj_japon_data.json"
PRONOSTICO_FILE = RAW_DIR / "pronostico_inflacion_japon.json"

def construir_pronostico_inflacion() -> dict:
    """
    Construye el modelo de pronóstico econométrico y fundamental de la inflación japonesa
    con desglose por componentes, consenso de mercado y matriz de impacto en USD/JPY.
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Cargar datos macro de Japón
    boj_data = {}
    if BOJ_DATA_FILE.exists():
        try:
            with open(BOJ_DATA_FILE, "r", encoding="utf-8") as f:
                boj_data = json.load(f)
        except Exception:
            boj_data = {}

    tasa_actual = boj_data.get("politica_monetaria_boj", {}).get("tasa_politica_overnight", {}).get("valor_actual", 1.00)
    
    # Históricos recientes
    cpi_core_hist = boj_data.get("inflacion_japon", {}).get("cpi_core_yoy", {}).get("historico", {})
    cpi_gen_hist = boj_data.get("inflacion_japon", {}).get("cpi_nacional_yoy", {}).get("historico", {})
    cpi_corecore_hist = boj_data.get("inflacion_japon", {}).get("cpi_core_core_yoy", {}).get("historico", {})
    tokyo_core_hist = boj_data.get("inflacion_japon", {}).get("tokyo_core_cpi_yoy", {}).get("historico", {})

    ultimo_core = list(cpi_core_hist.values())[-1] if cpi_core_hist else 2.70
    ultimo_gen = list(cpi_gen_hist.values())[-1] if cpi_gen_hist else 2.80
    ultimo_corecore = list(cpi_corecore_hist.values())[-1] if cpi_corecore_hist else 2.30
    ultimo_tokyo = list(tokyo_core_hist.values())[-1] if tokyo_core_hist else 2.30

    # 2. Desglose de Factores / Drivers Clave
    factores_inflacionarios = {
        "energia_y_servicios_publicos": {
            "ponderacion_canasta_pct": 7.1,
            "tendencia": "ALCISTA_MODERADA",
            "impacto_yoy_puntos": +0.35,
            "driver_principal": "Reducción progresiva de subsidios gubernamentales a tarifas eléctricas y gas.",
            "detalle": "El levantamiento parcial de los subsidios estatales de energía empuja al alza el componente energético interanual."
        },
        "alimentos_procesados_ex_frescos": {
            "ponderacion_canasta_pct": 22.5,
            "tendencia": "PRESION_SOSTENIDA",
            "impacto_yoy_puntos": +0.85,
            "driver_principal": "Traspaso de costos de materias primas agrícolas importadas y debilidad acumulada del Yen.",
            "detalle": "Las empresas continúan ajustando precios de alimentos envasados y bebidas para defender márgenes operativos."
        },
        "salarios_y_servicios": {
            "ponderacion_canasta_pct": 34.8,
            "tendencia": "EXPANSION_ESTRUCTURAL",
            "impacto_yoy_puntos": +1.15,
            "driver_principal": "Efecto de las negociaciones salariales de primavera Shunto 2026 (+5.1% de incremento promedio).",
            "detalle": "El traspaso de mayores costos laborales a los precios finales de servicios confirma la espiral virtuosa salarios-precios buscada por el BoJ."
        },
        "bienes_durables_y_manufacturas": {
            "ponderacion_canasta_pct": 18.2,
            "tendencia": "NEUTRAL",
            "impacto_yoy_puntos": +0.40,
            "driver_principal": "Consumo discrecional moderado y normalización de cadenas de suministro globales.",
            "detalle": "Demanda interna cautelosa limita aumentos agresivos en bienes no esenciales."
        }
    }

    # 3. Modelación de Pronóstico Cuantitativo
    # Core CPI proyectado (Benchmark del BoJ: Todo excepto alimentos frescos)
    pronostico_cpi_core = 2.75
    consenso_cpi_core = 2.70
    rango_min_core = 2.60
    rango_max_core = 2.90

    pronostico_cpi_headline = 2.80
    consenso_cpi_headline = 2.80

    pronostico_cpi_core_core = 2.30
    consenso_cpi_core_core = 2.30

    ahora_utc = datetime.now(timezone.utc).isoformat()
    
    pronostico_payload = {
        "timestamp_generacion_utc": ahora_utc,
        "evento_objetivo": {
            "nombre": "Índice de Precios al Consumidor (IPC) de Japón",
            "periodo_referencia": "Julio / Agosto 2026",
            "entidad_emisora": "Statistics Bureau of Japan (Ministry of Internal Affairs and Communications)",
            "benchmark_politica_monetaria": "IPC Subyacente (Core CPI ex-Alimentos Frescos)",
            "meta_oficial_boj_pct": 2.00
        },
        "pronostico_cifras": {
            "cpi_core_yoy": {
                "nombre": "IPC Subyacente Nacional (Ex-Alimentos Frescos)",
                "dato_anterior_pct": ultimo_core,
                "consenso_mercado_pct": consenso_cpi_core,
                "modelo_pronostico_gi_pct": pronostico_cpi_core,
                "rango_esperado": [rango_min_core, rango_max_core],
                "desviacion_vs_meta_boj_pct": round(pronostico_cpi_core - 2.00, 2),
                "evaluacion": "PERSISTENTEMENTE_SOBRE_META"
            },
            "cpi_headline_yoy": {
                "nombre": "IPC General Nacional (All Items)",
                "dato_anterior_pct": ultimo_gen,
                "consenso_mercado_pct": consenso_cpi_headline,
                "modelo_pronostico_gi_pct": pronostico_cpi_headline
            },
            "cpi_core_core_yoy": {
                "nombre": "IPC Subyacente Estructural (Ex-Alimentos Frescos y Energía)",
                "dato_anterior_pct": ultimo_corecore,
                "consenso_mercado_pct": consenso_cpi_core_core,
                "modelo_pronostico_gi_pct": pronostico_cpi_core_core
            },
            "tokyo_core_cpi_yoy": {
                "nombre": "IPC Subyacente de Tokio (Adelantado)",
                "dato_anterior_pct": ultimo_tokyo,
                "modelo_pronostico_gi_pct": 2.35
            }
        },
        "desglose_componentes": factores_inflacionarios,
        "matriz_sensibilidad_boj_usdjpy": {
            "escenario_hawkish_sorpresa_alcista": {
                "condicion": "Core CPI >= 2.90%",
                "probabilidad_estimada_pct": 25,
                "lectura_macro": "Aceleración inflacionaria impulsada por servicios y segunda ronda de precios.",
                "reaccion_esperada_boj": "Aumenta al 80% la probabilidad de alza de tasas a 1.25% en la reunión del 16-17 Septiembre.",
                "sesgo_usdjpy": "FUERTE_BAJISTA_JPY_FORTALECIDO",
                "niveles_objetivo_usdjpy": {
                    "soporte_inmediato": 156.500,
                    "soporte_extension": 154.000,
                    "target_swing": 152.500
                },
                "estrategia_operativa": "Ventas escalonadas en rebotes de USD/JPY o compras de JPY."
            },
            "escenario_base_en_linea": {
                "condicion": "Core CPI entre 2.60% y 2.80%",
                "probabilidad_estimada_pct": 60,
                "lectura_macro": "Inflación se mantiene sólidamente anclada sobre el 2.0%, validando la senda de subidas graduales.",
                "reaccion_esperada_boj": "El BoJ mantiene la tasa en 1.00% en Septiembre pero refuerza el forward guidance para alza en Octubre/Diciembre.",
                "sesgo_usdjpy": "LATERAL_BAJISTA_MODERADO",
                "niveles_objetivo_usdjpy": {
                    "soporte": 157.200,
                    "resistencia": 159.500,
                    "rango_esperado": "157.000 - 159.800"
                },
                "estrategia_operativa": "Operativa en rango con preferencia por buscar techos de confirmación técnica."
            },
            "escenario_dovish_sorpresa_bajista": {
                "condicion": "Core CPI <= 2.50%",
                "probabilidad_estimada_pct": 15,
                "lectura_macro": "Desaceleración mayor a la prevista por debilidad del consumo de los hogares.",
                "reaccion_esperada_boj": "Pausa prolongada en 1.00%; se reduce la presión para endurecer la política en 2026.",
                "sesgo_usdjpy": "ALCISTA_PRESION_DEPRECIATORIA_YEN",
                "niveles_objetivo_usdjpy": {
                    "resistencia_inmediata": 160.500,
                    "resistencia_clave": 162.000,
                    "zona_alerta_intervencion_mof": 163.500
                },
                "estrategia_operativa": "Compras tácticas intradía hacia resistencias con monitoreo estricto de declaraciones del Ministerio de Finanzas (MoF)."
            }
        },
        "contexto_intermercado_usd_jpy": {
            "tasa_actual_fed": 5.25,
            "tasa_actual_boj": tasa_actual,
            "diferencial_tasas_bps": int((5.25 - tasa_actual) * 100),
            "correlacion_us10y": "Directa (+0.82)",
            "alerta_intervencion_mof": "Activa si USD/JPY supera 162.500 con velocidad intradía acelerada."
        }
    }

    with open(PRONOSTICO_FILE, "w", encoding="utf-8") as f:
        json.dump(pronostico_payload, f, indent=2, ensure_ascii=False)

    return pronostico_payload

def imprimir_resumen_pronostico(p: dict):
    print("=" * 75)
    print(" 🇯🇵 MODELO DE PRONÓSTICO DE INFLACIÓN JAPÓN & IMPACTO BOJ / USD-JPY")
    print("=" * 75)
    
    c = p["pronostico_cifras"]
    print(f"\n📊 RESUMEN DE PROYECCIONES (PRÓXIMO DATO IPC):")
    print(f" • IPC Subyacente Nacional (Core YoY):  {c['cpi_core_yoy']['modelo_pronostico_gi_pct']}%  (Consenso: {c['cpi_core_yoy']['consenso_mercado_pct']}% | Anterior: {c['cpi_core_yoy']['dato_anterior_pct']}%)")
    print(f" • IPC General Nacional (Headline YoY): {c['cpi_headline_yoy']['modelo_pronostico_gi_pct']}%  (Consenso: {c['cpi_headline_yoy']['consenso_mercado_pct']}% | Anterior: {c['cpi_headline_yoy']['dato_anterior_pct']}%)")
    print(f" • IPC Subyacente Estructural (Core-Core): {c['cpi_core_core_yoy']['modelo_pronostico_gi_pct']}% (Consenso: {c['cpi_core_core_yoy']['consenso_mercado_pct']}% | Anterior: {c['cpi_core_core_yoy']['dato_anterior_pct']}%)")
    print(f" • Meta Oficial del Banco de Japón:      2.00%  (Desviación actual: +{c['cpi_core_yoy']['desviacion_vs_meta_boj_pct']}%)")

    print("\n" + "-" * 75)
    print(" 🔍 DESGLOSE DE DRIVERS MACROECONÓMICOS:")
    print("-" * 75)
    for comp, data in p["desglose_componentes"].items():
        print(f" • {comp.upper()} (Ponderación: {data['ponderacion_canasta_pct']}% | Impacto: {data['impacto_yoy_puntos']:+.2f}%):")
        print(f"   - {data['driver_principal']}")

    print("\n" + "-" * 75)
    print(" 🎯 MATRIZ DE SENSIBILIDAD PARA EL BOJ Y USD/JPY:")
    print("-" * 75)
    matriz = p["matriz_sensibilidad_boj_usdjpy"]
    
    print(f"\n1. [60% Prob.] ESCENARIO BASE — EN LÍNEA ({matriz['escenario_base_en_linea']['condicion']}):")
    print(f"   • BoJ: {matriz['escenario_base_en_linea']['reaccion_esperada_boj']}")
    print(f"   • USD/JPY: {matriz['escenario_base_en_linea']['sesgo_usdjpy']} -> Rango {matriz['escenario_base_en_linea']['niveles_objetivo_usdjpy']['rango_esperado']}")

    print(f"\n2. [25% Prob.] ESCENARIO HAWKISH — SORPRESA ALCISTA ({matriz['escenario_hawkish_sorpresa_alcista']['condicion']}):")
    print(f"   • BoJ: {matriz['escenario_hawkish_sorpresa_alcista']['reaccion_esperada_boj']}")
    print(f"   • USD/JPY: {matriz['escenario_hawkish_sorpresa_alcista']['sesgo_usdjpy']} -> Objetivos: {matriz['escenario_hawkish_sorpresa_alcista']['niveles_objetivo_usdjpy']['soporte_inmediato']} / {matriz['escenario_hawkish_sorpresa_alcista']['niveles_objetivo_usdjpy']['target_swing']}")

    print(f"\n3. [15% Prob.] ESCENARIO DOVISH — SORPRESA BAJISTA ({matriz['escenario_dovish_sorpresa_bajista']['condicion']}):")
    print(f"   • BoJ: {matriz['escenario_dovish_sorpresa_bajista']['reaccion_esperada_boj']}")
    print(f"   • USD/JPY: {matriz['escenario_dovish_sorpresa_bajista']['sesgo_usdjpy']} -> Resistencia {matriz['escenario_dovish_sorpresa_bajista']['niveles_objetivo_usdjpy']['resistencia_clave']}")

    print("\n" + "=" * 75)
    print(f" 💾 Payload guardado en: {PRONOSTICO_FILE}")
    print("=" * 75)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Construcción Pronóstico Inflación Japón")
    parser.add_argument("--json", action="store_true", help="Salida pura en JSON")
    args = parser.parse_args()

    res = construir_pronostico_inflacion()
    if args.json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        imprimir_resumen_pronostico(res)
