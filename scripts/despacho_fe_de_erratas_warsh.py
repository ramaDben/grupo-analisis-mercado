# -*- coding: utf-8 -*-
"""Despacho oficial de Fe de Erratas sobre la Presidencia de la Fed (Kevin Warsh) a WhatsApp.

Rectifica formalmente en los canales afectados (01 Macro, 04 Índices, 06 Cripto) la mención
involuntaria a Jerome Powell, confirmando que la presidencia de la Reserva Federal está a cargo
de Kevin Warsh, quien lidera el anuncio de política monetaria (15:00 CLT) y la conferencia
de prensa (15:30 CLT).

Respeta la cadencia anti-baneo de 45s y registra cada entrega en data/historial_despachos.json.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from whatsapp_sender import WhatsAppSender, huella
from bitacora_despachos import cargar as cargar_bitacora
from bitacora_despachos import registrar as anotar_despacho
from bitacora_despachos import ya_despachada
from guardrails.texto_cliente import revisar as revisar_guardrails

TANDA = "2026-09-16_12-00_fe_de_erratas_warsh"

PLAN_DESPACHO = [
    {
        "canal": "01_macro_y_apertura",
        "alias": "macro",
        "pieza": "fe_de_erratas_warsh_macro",
        "activo": "FED_CHAIR_WARSH",
        "adjunto": None,
        "mensaje": RAIZ / "data" / "stories" / "2026-09-16_fe_de_erratas_macro.txt",
    },
    {
        "canal": "04_indices_bursatiles",
        "alias": "indices",
        "pieza": "fe_de_erratas_warsh_indices",
        "activo": "US100",
        "adjunto": None,
        "mensaje": RAIZ / "data" / "stories" / "2026-09-16_fe_de_erratas_indices.txt",
    },
    {
        "canal": "06_criptoactivos",
        "alias": "cripto",
        "pieza": "fe_de_erratas_warsh_cripto",
        "activo": "BTCUSD",
        "adjunto": None,
        "mensaje": RAIZ / "data" / "stories" / "2026-09-16_fe_de_erratas_cripto.txt",
    },
]


def ejecutar(dry_run: bool = False) -> int:
    sender = WhatsAppSender(headless=True)
    bitacora = cargar_bitacora()

    print(f"\n📢 INICIANDO DESPACHO OFICIAL DE FE DE ERRATAS (KEVIN WARSH): {TANDA}")
    print(f"Modo: {'SIMULADO (dry-run)' if dry_run else 'REAL (WhatsApp Web)'}\n")

    # Validación previa estricta de todas las piezas contra los guardrails de texto
    for item in PLAN_DESPACHO:
        canal = item["canal"]
        mensaje_path = item["mensaje"]
        if not mensaje_path.exists():
            print(f"❌ Archivo de mensaje no existe: {mensaje_path}", file=sys.stderr)
            return 1
        texto = mensaje_path.read_text(encoding="utf-8").strip()
        veredicto = revisar_guardrails(texto)
        if not veredicto.ok:
            print(
                f"❌ Guardrail violado en [{canal}] ({veredicto.motivo}): {veredicto.detalle}",
                file=sys.stderr,
            )
            return 1
    print("✅ Todas las piezas pasaron la validación de guardrails exitosamente.\n")

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

        texto = mensaje_path.read_text(encoding="utf-8").strip()

        print(f"  Enviando pieza '{pieza}' ({len(texto)} chars)...")
        res = sender.enviar(
            destinatario=alias,
            mensaje=texto,
            adjunto=adjunto,
            dry_run=dry_run,
        )

        if not dry_run:
            anotar_despacho(
                TANDA,
                canal,
                pieza,
                activo=activo,
                huella=huella(texto),
            )
            bitacora = cargar_bitacora()

        print(f"  ✅ Entregado a '{res.get('destinatario')}': {res.get('status')}")
        exitos += 1

    print(f"\n🎉 DESPACHO DE FE DE ERRATAS COMPLETADO: {exitos} pieza(s) procesada(s) exitosamente.")
    return 0


if __name__ == "__main__":
    dry_run_flag = "--dry-run" in sys.argv
    sys.exit(ejecutar(dry_run=dry_run_flag))
