"""Script de despacho de la Subasta de Bonos del Tesoro de EE.UU. a 20 Años (UST 20Y) a WhatsApp.

Despacha secuencialmente la Story PNG y textos de análisis macro e intermercado a los canales
de Macro (Avisos), Índices Bursátiles y Forex & Divisas, respetando la cadencia anti-baneo de 45s
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

TANDA = "2026-09-15_14-15_subasta_ust20y"
IMAGEN_BREAKING = RAIZ / "data" / "stories" / "2026-09-15_ust20y_auction_macro.png"

PLAN_DESPACHO = [
    {
        "canal": "01_macro_y_apertura",
        "alias": "avisos",
        "pieza": "subasta_20y_macro",
        "activo": "UST20Y_AUCTION",
        "adjunto": IMAGEN_BREAKING,
        "mensaje": RAIZ / "data" / "stories" / "2026-09-15_ust20y_auction_macro.txt",
    },
    {
        "canal": "04_indices_bursatiles",
        "alias": "indices",
        "pieza": "subasta_20y_indices",
        "activo": "US100",
        "adjunto": IMAGEN_BREAKING,
        "mensaje": RAIZ / "data" / "stories" / "2026-09-15_ust20y_auction_indices.txt",
    },
    {
        "canal": "02_forex_divisas",
        "alias": "divisas",
        "pieza": "subasta_20y_forex",
        "activo": "USDCLP",
        "adjunto": IMAGEN_BREAKING,
        "mensaje": RAIZ / "data" / "stories" / "2026-09-15_ust20y_auction_forex.txt",
    },
]


def ejecutar(dry_run: bool = False) -> int:
    sender = WhatsAppSender(headless=True)
    bitacora = cargar_bitacora()

    print(f"\n🚀 INICIANDO DESPACHO DE SUBASTA UST 20Y: {TANDA}")
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

    print(f"\n🎉 DESPACHO DE SUBASTA UST 20Y COMPLETADO: {exitos} pieza(s) procesada(s) exitosamente.")
    return 0


if __name__ == "__main__":
    dry_run_flag = "--dry-run" in sys.argv
    sys.exit(ejecutar(dry_run=dry_run_flag))
