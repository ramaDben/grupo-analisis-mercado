"""CLI de envío automatizado a WhatsApp Web.

Permite enviar reportes, textos formateados y piezas multimedia (PNGs/PDFs) a los
7 grupos temáticos oficiales de WhatsApp o contactos individuales.

Uso:
  # 1. Vincular sesión con código QR (primera vez)
  python scripts/enviar_whatsapp.py --login

  # 2. Verificar estado de la sesión guardada
  python scripts/enviar_whatsapp.py --status

  # 3. Listar grupos y alias configurados
  python scripts/enviar_whatsapp.py --listar-grupos

  # 4. Enviar mensaje de texto a un grupo
  python scripts/enviar_whatsapp.py --grupo forex --mensaje "Alerta USD/CLP..."

  # 5. Enviar reporte desde archivo de texto
  python scripts/enviar_whatsapp.py --grupo macro --mensaje-archivo "data central/DATA CHILE/reportes_generados/mensaje_resumen_whatsapp.txt"

  # 6. Enviar Story / Gráfico PNG con pie de foto
  python scripts/enviar_whatsapp.py --grupo commodities --adjunto "data/stories/2026-09-01_oro_h1.png" --mensaje-archivo "data central/DATA ORO Y COMMODITIES/reportes_generados/mensaje_whatsapp_oro.txt"

  # 7. Modo simulación (Dry-Run)
  python scripts/enviar_whatsapp.py --grupo indices --mensaje "Test" --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Configurar encoding seguro para consola de Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Añadir src/ al path para importar módulos locales
RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "src") not in sys.path:
    sys.path.insert(0, str(RAIZ / "src"))

from whatsapp_sender import (
    WhatsAppConfig,
    WhatsAppSender,
    WhatsAppError,
    SesionNoIniciadaError,
    DestinatarioInvalidoError,
)


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Envío automatizado de mensajes, reportes y multimedia a WhatsApp Web."
    )
    parser.add_argument(
        "--login",
        action="store_true",
        help="Abre una ventana visible de Chromium para escanear el código QR de WhatsApp Web y guardar la sesión.",
    )
    parser.add_argument(
        "--status", "--verificar-sesion",
        action="store_true",
        dest="verificar_status",
        help="Verifica en segundo plano si la sesión guardada en .whatsapp_session/ está activa y autenticada.",
    )
    parser.add_argument(
        "--listar-grupos",
        action="store_true",
        help="Muestra el catálogo de los 7 grupos oficiales con sus alias reconocidos.",
    )
    parser.add_argument(
        "-g", "--grupo", "--destinatario",
        dest="destinatario",
        type=str,
        help="Alias, slug o nombre oficial del grupo de WhatsApp destino (ej. 'macro', 'forex', '03_commodities_materias_primas').",
    )
    parser.add_argument(
        "-m", "--mensaje",
        type=str,
        default="",
        help="Texto del mensaje a enviar (o pie de foto si se acompaña de un archivo adjunto).",
    )
    parser.add_argument(
        "-f", "--mensaje-archivo",
        type=Path,
        help="Ruta a un archivo de texto (.txt / .md) cuyo contenido será el cuerpo del mensaje.",
    )
    parser.add_argument(
        "-a", "--adjunto",
        type=Path,
        help="Ruta al archivo adjunto (PNG de Story, gráfico H1, PDF de informe, etc.).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Modo simulación: valida los parámetros y muestra lo que se enviaría sin abrir WhatsApp Web.",
    )
    parser.add_argument(
        "--visible", "--no-headless",
        action="store_false",
        dest="headless",
        help="Muestra la ventana del navegador durante el envío (útil para depuración).",
    )
    parser.add_argument(
        "--session-dir",
        type=Path,
        help="Ruta personalizada para el directorio de sesión persistente de Chromium.",
    )
    parser.add_argument(
        "--timeout-login",
        type=int,
        default=120,
        help="Segundos máximos de espera para escanear el QR en modo --login (por defecto: 120s).",
    )
    return parser


def main() -> int:
    parser = construir_parser()
    args = parser.parse_args()

    sender = WhatsAppSender(
        session_dir=args.session_dir,
        headless=args.headless,
    )

    # 1. Modo Listar Grupos
    if args.listar_grupos:
        config = sender.config
        print("\n=== GRUPOS OFICIALES CONFIGURADOS EN WHATSAPP ===")
        for clave, info in config.grupos.items():
            print(f"\n📂 [{clave}] -> \"{info.get('nombre_oficial')}\"")
            print(f"   Alias: {', '.join(info.get('alias', []))}")
            print(f"   Descripción: {info.get('descripcion')}")
        print("\n================================================\n")
        return 0

    # 2. Modo Status / Verificación de Sesión
    if args.verificar_status:
        print("\n[WHATSAPP STATUS] Verificando estado de sesión en segundo plano...")
        try:
            resultado = sender.verificar_estado_sesion()
            if resultado["autenticado"]:
                print(f"[ESTADO] ✅ {resultado['mensaje']}")
                return 0
            else:
                print(f"[ESTADO] ⚠️ {resultado['mensaje']}")
                return 1
        except Exception as exc:
            print(f"[ERROR STATUS] {exc}", file=sys.stderr)
            return 1

    # 3. Modo Login / Setup QR
    if args.login:
        try:
            exito = sender.ejecutar_login_interactivo(timeout_s=args.timeout_login)
            return 0 if exito else 1
        except Exception as exc:
            print(f"\n[ERROR SETUP] {exc}", file=sys.stderr)
            return 1

    # 4. Validación de Parámetros de Envío
    if not args.destinatario:
        print("[ERROR] Debe especificar un destinatario o grupo con --grupo o --destinatario.", file=sys.stderr)
        print("Use --listar-grupos para ver los canales disponibles.", file=sys.stderr)
        return 1

    cuerpo_mensaje = args.mensaje
    if args.mensaje_archivo:
        if not args.mensaje_archivo.exists():
            print(f"[ERROR] El archivo de mensaje no existe: {args.mensaje_archivo}", file=sys.stderr)
            return 1
        contenido = args.mensaje_archivo.read_text(encoding="utf-8")
        cuerpo_mensaje = f"{cuerpo_mensaje}\n\n{contenido}".strip() if cuerpo_mensaje else contenido

    if not cuerpo_mensaje.strip() and not args.adjunto:
        print("[ERROR] Debe proporcionar al menos un mensaje (--mensaje / --mensaje-archivo) o un adjunto (--adjunto).", file=sys.stderr)
        return 1

    if args.adjunto and not args.adjunto.exists():
        print(f"[ERROR] El archivo adjunto no existe: {args.adjunto}", file=sys.stderr)
        return 1

    # 5. Ejecución del Envío
    try:
        resultado = sender.enviar(
            destinatario=args.destinatario,
            mensaje=cuerpo_mensaje,
            adjunto=args.adjunto,
            dry_run=args.dry_run,
        )
        print("\n[ÉXITO] Operación completada:")
        print(f"  • Destinatario : {resultado['destinatario']}")
        print(f"  • Estado       : {resultado['status']}")
        if resultado.get("adjunto"):
            print(f"  • Adjunto      : {resultado['adjunto']}")
        print(f"  • Caracteres   : {resultado['mensaje_len']}")
        return 0

    except SesionNoIniciadaError as exc:
        print(f"\n[ERROR DE SESIÓN] {exc}", file=sys.stderr)
        return 2
    except DestinatarioInvalidoError as exc:
        print(f"\n[ERROR DE SEGURIDAD / DESTINATARIO] {exc}", file=sys.stderr)
        return 3
    except WhatsAppError as exc:
        print(f"\n[ERROR WHATSAPP] {exc}", file=sys.stderr)
        return 4
    except Exception as exc:
        print(f"\n[ERROR INESPERADO] {exc}", file=sys.stderr)
        return 5


if __name__ == "__main__":
    sys.exit(main())
