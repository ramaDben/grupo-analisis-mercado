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

TANDA = "2026-09-09_11-14_apertura_ny"
DIR_TANDA = RAIZ / "data" / "carrusel" / TANDA

PLAN_DESPACHO = [
    {
        "canal": "05_acciones_etfs",
        "alias": "acciones",
        "pieza": "1_qqqus",
        "activo": "QQQ.US",
        "adjunto": DIR_TANDA / "05_acciones_etfs" / "1_qqqus.png",
        "mensaje": DIR_TANDA / "05_acciones_etfs" / "1_qqqus_mensaje.txt",
    },
    {
        "canal": "05_acciones_etfs",
        "alias": "acciones",
        "pieza": "2_cat",
        "activo": "#CAT",
        "adjunto": DIR_TANDA / "05_acciones_etfs" / "2_cat.png",
        "mensaje": DIR_TANDA / "05_acciones_etfs" / "2_cat_mensaje.txt",
    },
    {
        "canal": "05_acciones_etfs",
        "alias": "acciones",
        "pieza": "3_msft",
        "activo": "#MSFT",
        "adjunto": DIR_TANDA / "05_acciones_etfs" / "3_msft.png",
        "mensaje": DIR_TANDA / "05_acciones_etfs" / "3_msft_mensaje.txt",
    },
]


def ejecutar(dry_run: bool = False) -> int:
    sender = WhatsAppSender(headless=True)
    bitacora = cargar_bitacora()

    print(f"\n🚀 INICIANDO DESPACHO DE ACCIONES Y ETFS: {TANDA}")
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
