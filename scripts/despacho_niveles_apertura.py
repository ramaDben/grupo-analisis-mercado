"""Script de despacho de piezas de niveles técnicos (Apertura Wall Street) a WhatsApp.

Despacha secuencialmente las Stories PNG y textos de análisis técnico a los canales
de Forex, Commodities, Índices y Criptomonedas, respetando la cadencia anti-baneo de 45s
y registrando cada entrega en data/historial_despachos.json.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from whatsapp_sender import WhatsAppSender, huella
from bitacora_despachos import cargar as cargar_bitacora
from bitacora_despachos import registrar as anotar_despacho
from bitacora_despachos import ya_despachada

TANDA = "2026-09-09_10-25_apertura_ny"
DIR_TANDA = RAIZ / "data" / "carrusel" / TANDA

PLAN_DESPACHO = [
    # 1. FOREX & DIVISAS: USD/JPY y GBP/USD
    {
        "canal": "02_forex_divisas",
        "alias": "forex",
        "pieza": "1_usdjpy",
        "activo": "USDJPY",
        "adjunto": DIR_TANDA / "02_forex_divisas" / "1_usdjpy.png",
        "mensaje": DIR_TANDA / "02_forex_divisas" / "1_usdjpy_mensaje.txt",
    },
    {
        "canal": "02_forex_divisas",
        "alias": "forex",
        "pieza": "2_gbpusd",
        "activo": "GBPUSD",
        "adjunto": DIR_TANDA / "02_forex_divisas" / "2_gbpusd.png",
        "mensaje": DIR_TANDA / "02_forex_divisas" / "2_gbpusd_mensaje.txt",
    },
    # 2. COMMODITIES: PLATA Y ORO
    {
        "canal": "03_commodities_materias_primas",
        "alias": "commodities",
        "pieza": "3_xagusd",
        "activo": "XAGUSD",
        "adjunto": DIR_TANDA / "03_commodities_materias_primas" / "3_xagusd.png",
        "mensaje": DIR_TANDA / "03_commodities_materias_primas" / "3_xagusd_mensaje.txt",
    },
    {
        "canal": "03_commodities_materias_primas",
        "alias": "commodities",
        "pieza": "4_xauusd",
        "activo": "XAUUSD",
        "adjunto": DIR_TANDA / "03_commodities_materias_primas" / "4_xauusd.png",
        "mensaje": DIR_TANDA / "03_commodities_materias_primas" / "4_xauusd_mensaje.txt",
    },
    # 3. ÍNDICES: NASDAQ 100
    {
        "canal": "04_indices_bursatiles",
        "alias": "indices",
        "pieza": "5_us100spot",
        "activo": "US100.spot",
        "adjunto": DIR_TANDA / "04_indices_bursatiles" / "5_us100spot.png",
        "mensaje": DIR_TANDA / "04_indices_bursatiles" / "5_us100spot_mensaje.txt",
    },
    # 4. CRIPTOMONEDAS: DOGECOIN Y ETHEREUM
    {
        "canal": "06_criptoactivos",
        "alias": "cripto",
        "pieza": "6_dogusd",
        "activo": "DOGUSD",
        "adjunto": DIR_TANDA / "06_criptoactivos" / "6_dogusd.png",
        "mensaje": DIR_TANDA / "06_criptoactivos" / "6_dogusd_mensaje.txt",
    },
    {
        "canal": "06_criptoactivos",
        "alias": "cripto",
        "pieza": "7_ethusd",
        "activo": "ETHUSD",
        "adjunto": DIR_TANDA / "06_criptoactivos" / "7_ethusd.png",
        "mensaje": DIR_TANDA / "06_criptoactivos" / "7_ethusd_mensaje.txt",
    },
]


def ejecutar(dry_run: bool = False) -> int:
    sender = WhatsAppSender(headless=True)
    bitacora = cargar_bitacora()

    print(f"\n🚀 INICIANDO DESPACHO DE NIVELES TÉCNICOS: {TANDA}")
    print(f"Modo: {'SIMULADO (dry-run)' if dry_run else 'REAL (WhatsApp Web)'}\n")

    exitos = 0
    for item in PLAN_DESPACHO:
        canal = item["canal"]
        alias = item["alias"]
        pieza = item["pieza"]
        activo = item.get("activo", "")
        adjunto = item["adjunto"]
        mensaje_path = item["mensaje"]

        print(f"\n--- [{canal}] ({activo}) -> alias '{alias}' ---")
        if not dry_run and ya_despachada(bitacora, TANDA, canal, pieza):
            print(f"  ⏭️ Ya despachada según bitácora: se omite.")
            continue

        if not mensaje_path.exists():
            print(f"  ❌ Archivo de mensaje no existe: {mensaje_path}", file=sys.stderr)
            return 1

        texto = mensaje_path.read_text(encoding="utf-8").strip()

        if adjunto and not adjunto.exists():
            print(f"  ❌ Archivo adjunto no existe: {adjunto}", file=sys.stderr)
            return 1

        print(f"  Enviando pieza '{pieza}' ({len(texto)} chars)...")
        res = sender.enviar(
            destinatario=alias,
            mensaje=texto,
            adjunto=adjunto,
            dry_run=dry_run,
        )

        if not dry_run:
            anotar_despacho(
                TANDA, canal, pieza,
                activo=activo,
                huella=huella(texto),
            )
            bitacora = cargar_bitacora()

        print(f"  ✅ Entregado a '{res.get('destinatario')}': {res.get('status')}")
        exitos += 1

    print(f"\n🎉 DESPACHO DE NIVELES COMPLETADO: {exitos} pieza(s) procesada(s) exitosamente.")
    return 0


if __name__ == "__main__":
    dry_run_flag = "--dry-run" in sys.argv
    sys.exit(ejecutar(dry_run=dry_run_flag))
