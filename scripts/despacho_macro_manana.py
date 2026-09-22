"""Script de despacho de la tanda macroeconómica matinal a WhatsApp.

Despacha secuencialmente las piezas de contexto macro y suplementos a los 6 canales
oficiales, respetando la cadencia anti-baneo de 45 segundos por acción y registrando
cada entrega confirmada en data/historial_despachos.json.
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

from whatsapp_sender import WhatsAppSender, huella
from bitacora_despachos import cargar as cargar_bitacora
from bitacora_despachos import registrar as anotar_despacho
from bitacora_despachos import ya_despachada

def resolver_tanda(tanda_param: str | None = None) -> tuple[str, Path]:
    carrusel_dir = RAIZ / "data" / "carrusel"
    if tanda_param:
        dir_t = carrusel_dir / tanda_param
        if not dir_t.is_dir():
            raise FileNotFoundError(f"La tanda especificada no existe: {dir_t}")
        return tanda_param, dir_t

    hoy_prefix = datetime.now().strftime("%Y-%m-%d")
    tandas_hoy = sorted([d for d in carrusel_dir.iterdir() if d.is_dir() and d.name.startswith(hoy_prefix)])
    if tandas_hoy:
        return tandas_hoy[-1].name, tandas_hoy[-1]

    # Respaldo por defecto
    tanda_default = "2026-09-09_08-56_europea"
    return tanda_default, carrusel_dir / tanda_default


def construir_plan(dir_tanda: Path) -> list[dict[str, Any]]:
    return [
        {
            "canal": "01_macro_y_apertura",
            "alias": "macro",
            "pieza": "0_contexto_macro",
            "adjunto": dir_tanda / "01_macro_y_apertura" / "0_contexto_macro.png",
            "mensaje": dir_tanda / "01_macro_y_apertura" / "0_contexto_macro.txt",
        },
        {
            "canal": "02_forex_divisas",
            "alias": "forex",
            "pieza": "0_contexto_macro",
            "adjunto": dir_tanda / "02_forex_divisas" / "0_contexto_macro.png",
            "mensaje": dir_tanda / "02_forex_divisas" / "0_contexto_macro.txt",
        },
        {
            "canal": "04_indices_bursatiles",
            "alias": "indices",
            "pieza": "0_contexto_macro",
            "adjunto": dir_tanda / "04_indices_bursatiles" / "0_contexto_macro.png",
            "mensaje": dir_tanda / "04_indices_bursatiles" / "0_contexto_macro.txt",
        },
        {
            "canal": "03_commodities_materias_primas",
            "alias": "commodities",
            "pieza": "0_suplemento",
            "adjunto": None,
            "mensaje": dir_tanda / "03_commodities_materias_primas" / "0_suplemento.txt",
        },
        {
            "canal": "05_acciones_etfs",
            "alias": "acciones",
            "pieza": "0_suplemento",
            "adjunto": None,
            "mensaje": dir_tanda / "05_acciones_etfs" / "0_suplemento.txt",
        },
        {
            "canal": "06_criptoactivos",
            "alias": "cripto",
            "pieza": "0_suplemento",
            "adjunto": None,
            "mensaje": dir_tanda / "06_criptoactivos" / "0_suplemento.txt",
        },
    ]


def ejecutar(dry_run: bool = False, tanda_solicitada: str | None = None) -> int:
    sender = WhatsAppSender(headless=True)
    bitacora = cargar_bitacora()
    nombre_tanda, dir_tanda = resolver_tanda(tanda_solicitada)
    plan_despacho = construir_plan(dir_tanda)

    print(f"\n🚀 INICIANDO DESPACHO MACRO: {nombre_tanda}")
    print(f"Modo: {'SIMULADO (dry-run)' if dry_run else 'REAL (WhatsApp Web)'}\n")

    exitos = 0
    for item in plan_despacho:
        canal = item["canal"]
        alias = item["alias"]
        pieza = item["pieza"]
        adjunto = item["adjunto"]
        mensaje_path = item["mensaje"]

        print(f"\n--- [{canal}] -> alias '{alias}' ---")
        if not dry_run and ya_despachada(bitacora, nombre_tanda, canal, pieza):
            print(f"  ⏭️ Ya despachada según bitácora: se omite.")
            continue

        if not mensaje_path.exists():
            print(f"  ⏭️ No hay pieza para '{canal}' en esta tanda: se omite.")
            continue

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
                nombre_tanda, canal, pieza,
                huella=huella(texto),
            )
            bitacora = cargar_bitacora()

        print(f"  ✅ Entregado a '{res.get('destinatario')}': {res.get('status')}")
        exitos += 1

    print(f"\n🎉 DESPACHO COMPLETADO: {exitos} pieza(s) procesada(s) exitosamente.")
    return 0


if __name__ == "__main__":
    dry_run_flag = "--dry-run" in sys.argv
    tanda_arg = None
    for idx, arg in enumerate(sys.argv):
        if arg == "--tanda" and idx + 1 < len(sys.argv):
            tanda_arg = sys.argv[idx + 1]
    sys.exit(ejecutar(dry_run=dry_run_flag, tanda_solicitada=tanda_arg))
