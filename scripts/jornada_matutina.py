#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Orquestador Maestro y Guardia de la Jornada Matutina de Grupo Inteligencia.

Blindaje integral del flujo end-to-end:
1. Diagnóstico previo (MetaTrader 5, sesión de WhatsApp, Playwright).
2. Cadena de datos macroeconómicos soberanos (ingesta -> precios).
3. Verificación de vigencia y relojes (pipeline_datos --estado).
4. Agenda macro y alertas del día.
5. Preparación del carrusel cuantitativo (Screener GI).
6. Linter editorial estricto (guiones largos, voseo, placeholders, anclaje al manual).
7. Renderizado oficial a 300 DPI con TradingView Lightweight Charts.
8. Certificación previa en Banco de Pruebas (GI · Banco de Pruebas).
9. Despacho oficial a canales con protección contra envíos accidentales.

Uso:
    uv run --with MetaTrader5 python scripts/jornada_matutina.py --diagnostico
    uv run --with MetaTrader5 python scripts/jornada_matutina.py --datos
    uv run --with MetaTrader5 python scripts/jornada_matutina.py --agenda
    uv run --with MetaTrader5 python scripts/jornada_matutina.py --preparar
    uv run python scripts/jornada_matutina.py --auditar
    uv run python scripts/jornada_matutina.py --rendir
    uv run --with MetaTrader5 python scripts/jornada_matutina.py --probar
    uv run --with MetaTrader5 python scripts/jornada_matutina.py --despachar --confirmar
    uv run --with MetaTrader5 python scripts/jornada_matutina.py --todo
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
SRC = RAIZ / "src"
SCRIPTS = RAIZ / "scripts"

for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

SANTIAGO = ZoneInfo("America/Santiago")
DIR_CARRUSEL = RAIZ / "data" / "carrusel"


def resolver_ultima_tanda(tanda_especifica: str | Path | None = None) -> Path:
    """Obtiene el directorio de la tanda solicitada o la más reciente de HOY.

    **Sin respaldo a días anteriores.** Si hoy no hay tanda, se detiene: un
    `--despachar --confirmar` sin argumento que tomara la última tanda existente
    mandaría a los clientes la de ayer, con fecha y niveles de ayer.
    """
    if tanda_especifica:
        p = Path(tanda_especifica)
        if not p.is_absolute():
            p = RAIZ / p if (RAIZ / p).is_dir() else DIR_CARRUSEL / p
        if not p.is_dir():
            raise FileNotFoundError(f"El directorio de tanda no existe: {p}")
        return p

    hoy = datetime.now(tz=SANTIAGO).strftime("%Y-%m-%d")
    tandas_hoy = sorted(d for d in DIR_CARRUSEL.iterdir() if d.is_dir() and d.name.startswith(hoy))
    if tandas_hoy:
        return tandas_hoy[-1]

    raise FileNotFoundError(
        f"No hay tandas de hoy ({hoy}) en {DIR_CARRUSEL}. Prepara una o pasa la tanda explícita."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Gate 0: Diagnóstico de Entorno
# ─────────────────────────────────────────────────────────────────────────────
def diagnosticar_entorno() -> dict[str, Any]:
    """Verifica la salud de los servicios externos críticos: MT5, WhatsApp y Playwright."""
    print("🔍 [Gate 0] Diagnosticando entorno de ejecución...", flush=True)
    reporte: dict[str, Any] = {"ok": True, "detalles": {}}

    # 1. MetaTrader 5
    try:
        import MetaTrader5 as mt5  # type: ignore

        if not mt5.initialize():
            error_code, error_str = mt5.last_error()
            reporte["ok"] = False
            reporte["detalles"]["mt5"] = f"Fallo al inicializar MT5: {error_str} ({error_code})"
        else:
            terminal_info = mt5.terminal_info()
            conectado = terminal_info.connected if terminal_info else False
            cuenta = mt5.account_info().login if mt5.account_info() else "N/A"
            mt5.shutdown()
            if not conectado:
                reporte["ok"] = False
                reporte["detalles"]["mt5"] = "Terminal MT5 abierto pero sin conexión al broker"
            else:
                reporte["detalles"]["mt5"] = f"Conectado OK (Cuenta: {cuenta})"
    except ImportError:
        reporte["ok"] = False
        reporte["detalles"]["mt5"] = "Paquete MetaTrader5 no disponible en el entorno"
    except Exception as exc:
        reporte["ok"] = False
        reporte["detalles"]["mt5"] = f"Excepción en diagnóstico MT5: {exc}"

    # 2. Sesión WhatsApp Web
    sesion_dir = RAIZ / ".whatsapp_session"
    if not sesion_dir.is_dir():
        reporte["ok"] = False
        reporte["detalles"]["whatsapp"] = "Directorio .whatsapp_session/ no encontrado"
    else:
        default_dir = sesion_dir / "Default"
        if default_dir.is_dir():
            reporte["detalles"]["whatsapp"] = "Sesión persistida detectada OK"
        else:
            reporte["ok"] = False
            reporte["detalles"]["whatsapp"] = "Carpeta Default de sesión no existe (requiere login QR)"

    # 3. Playwright
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            nav = p.chromium.launch(headless=True)
            nav.close()
        reporte["detalles"]["playwright"] = "Chromium operativo OK"
    except Exception as exc:
        reporte["ok"] = False
        reporte["detalles"]["playwright"] = f"Chromium no disponible: {exc}"

    # Visualización
    for servicio, estado in reporte["detalles"].items():
        simbolo = "✅" if "OK" in str(estado) else "❌"
        print(f"  {simbolo} {servicio.upper()}: {estado}", flush=True)

    return reporte


# ─────────────────────────────────────────────────────────────────────────────
# Gate 1: Cadena de Datos Macroeconómicos
# ─────────────────────────────────────────────────────────────────────────────
def ejecutar_cadena_datos() -> bool:
    """Ejecuta los pasos de datos (ingesta soberana -> precios MT5) y valida el estado."""
    print("\n📦 [Gate 1] Ejecutando cadena de datos macroeconómicos...", flush=True)
    cmd = ["uv", "run", "--with", "MetaTrader5", "python", str(SCRIPTS / "pipeline_datos.py")]
    res = subprocess.run(cmd, cwd=RAIZ, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        print("❌ Fallo en la ejecución de scripts/pipeline_datos.py", file=sys.stderr)
        return False

    print("\n🔍 [Gate 1] Validando estado de relojes y vigencia...", flush=True)
    cmd_estado = ["uv", "run", "python", str(SCRIPTS / "pipeline_datos.py"), "--estado"]
    proc_estado = subprocess.run(cmd_estado, cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(proc_estado.stdout.strip(), flush=True)

    if proc_estado.returncode != 0 or "NO utilizable" in proc_estado.stdout:
        print("❌ El estado de los datos reporta NO utilizable. Corrija los errores antes de continuar.", file=sys.stderr)
        return False

    if "YFINANCE" in proc_estado.stdout:
        print("❌ Se detectó caída a YFINANCE. Prohibido continuar con instrumentos desalineados.", file=sys.stderr)
        return False

    print("✅ Cadena de datos sincronizada y vigente.", flush=True)
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Gate 2: Agenda Oficial del Día
# ─────────────────────────────────────────────────────────────────────────────
def consultar_agenda() -> bool:
    """Consulta la agenda oficial del día para revisar eventos y blackouts."""
    print("\n📅 [Gate 2] Consultando agenda macroeconómica oficial...", flush=True)
    script_agenda = RAIZ / ".agents" / "skills" / "ecosistema-datos-macro" / "scripts" / "agenda.py"
    if not script_agenda.exists():
        print(f"⚠️ Script de agenda no encontrado en {script_agenda}", flush=True)
        return True

    res = subprocess.run(["uv", "run", "python", str(script_agenda)], cwd=RAIZ, text=True, encoding="utf-8", errors="replace")
    return res.returncode == 0


# ─────────────────────────────────────────────────────────────────────────────
# Gate 3: Preparación del Carrusel / Escáner
# ─────────────────────────────────────────────────────────────────────────────
def preparar_carrusel(top: int = 3, matriz: bool = False) -> Path:
    """Ejecuta el escáner cuantitativo y arma los payloads base de la tanda."""
    print(f"\n📊 [Gate 3] Ejecutando escáner y preparando tanda (top={top}, matriz={matriz})...", flush=True)
    cmd = ["uv", "run", "--with", "MetaTrader5", "python", str(SCRIPTS / "pipeline_carrusel.py"), "--preparar", "--top", str(top)]
    if matriz:
        cmd.append("--matriz")

    res = subprocess.run(cmd, cwd=RAIZ, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        raise RuntimeError("Fallo al preparar los payloads con pipeline_carrusel.py")

    tanda_dir = resolver_ultima_tanda()
    print(f"✅ Tanda preparada en: {tanda_dir}", flush=True)
    return tanda_dir


# ─────────────────────────────────────────────────────────────────────────────
# Gate 4: Auditoría y Linter Editorial
# ─────────────────────────────────────────────────────────────────────────────
def auditar_editorial(tanda_dir: Path) -> bool:
    """Inspecciona todos los payloads de la tanda con el linter de estilo estricto."""
    from validador_editorial import validar_payload_editorial

    print(f"\n✍️ [Gate 4] Auditando textos editoriales en: {tanda_dir.name}...", flush=True)
    archivos = sorted(p for p in tanda_dir.rglob("*.json") if not p.name.startswith("_") and not p.name.startswith("0_contexto_macro"))

    if not archivos:
        print(f"❌ No se encontraron payloads de alerta en {tanda_dir}", file=sys.stderr)
        return False

    todos_ok = True
    for p in archivos:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            errores = validar_payload_editorial(data, identificador=p.stem)
            if errores:
                todos_ok = False
                print(f"  ❌ {p.name}:", flush=True)
                for err in errores:
                    print(f"     • {err}", flush=True)
            else:
                print(f"  ✅ {p.name}: texto editorial válido y conforme.", flush=True)
        except Exception as exc:
            todos_ok = False
            print(f"  ❌ {p.name}: Error al leer JSON: {exc}", file=sys.stderr)

    if not todos_ok:
        print("\n⚠️ Hay piezas con campos pendientes o infracciones de estilo (guion largo, voseo o placeholders).", flush=True)
        print("   Complete o corrija los archivos JSON antes de rendir.", flush=True)
    else:
        print("\n✅ Todos los textos editoriales cumplen las directrices institucionales.", flush=True)

    return todos_ok


# ─────────────────────────────────────────────────────────────────────────────
# Gate 5: Renderizado Oficial TradingView 300 DPI
# ─────────────────────────────────────────────────────────────────────────────
def rendir_carrusel(tanda_dir: Path) -> bool:
    """Renderiza los gráficos y mensajes de la tanda."""
    print(f"\n🎨 [Gate 5] Renderizando gráficos TradingView 300 DPI en {tanda_dir.name}...", flush=True)
    cmd = ["uv", "run", "--extra", "stories", "python", str(SCRIPTS / "pipeline_carrusel.py"), "--rendir", str(tanda_dir)]
    res = subprocess.run(cmd, cwd=RAIZ, text=True, encoding="utf-8", errors="replace")
    if res.returncode != 0:
        print("❌ Fallo en el renderizado.", file=sys.stderr)
        return False
    print("✅ Gráficos e imágenes generadas exitosamente.", flush=True)
    return True


# ─────────────────────────────────────────────────────────────────────────────
# Gate 6: Despacho a Banco de Pruebas
# ─────────────────────────────────────────────────────────────────────────────
def despachar_a_pruebas(tanda_dir: Path) -> bool:
    """Envía la tanda completa a GI · Banco de Pruebas para certificación visual."""
    print(f"\n🧪 [Gate 6] Despachando a 'GI · Banco de Pruebas'...", flush=True)
    cmd = [
        "uv", "run", "--extra", "stories", "--with", "MetaTrader5",
        "python", str(SCRIPTS / "pipeline_carrusel.py"),
        "--despachar", str(tanda_dir),
        "--pruebas",
    ]
    res = subprocess.run(cmd, cwd=RAIZ, text=True, encoding="utf-8", errors="replace")
    return res.returncode == 0


# ─────────────────────────────────────────────────────────────────────────────
# Gate 7: Despacho a Canales Oficiales
# ─────────────────────────────────────────────────────────────────────────────
def despachar_oficial(tanda_dir: Path, confirmado: bool = False) -> bool:
    """Despacha a los canales de producción en WhatsApp con confirmación explícita."""
    if not confirmado:
        print("⚠️ Despacho a producción detenido: se requiere la bandera --confirmar para enviar a clientes.", file=sys.stderr)
        return False

    print(f"\n🚀 [Gate 7] Despachando a CANALES OFICIALES DE PRODUCCIÓN ({tanda_dir.name})...", flush=True)
    cmd = [
        "uv", "run", "--extra", "stories", "--with", "MetaTrader5",
        "python", str(SCRIPTS / "pipeline_carrusel.py"),
        "--despachar", str(tanda_dir),
    ]
    res = subprocess.run(cmd, cwd=RAIZ, text=True, encoding="utf-8", errors="replace")
    return res.returncode == 0


# ─────────────────────────────────────────────────────────────────────────────
# Modo End-to-End
# ─────────────────────────────────────────────────────────────────────────────
def ejecutar_todo(
    tanda_dir: Path | None = None,
    confirmar_despacho: bool = False,
    top: int = 1,
    matriz: bool = True,
) -> int:
    """Ejecuta la jornada matutina completa con todos sus gates de seguridad."""
    print("=====================================================================")
    print("🛡️  ORQUESTADOR MAESTRO DE LA JORNADA MATUTINA · GRUPO INTELIGENCIA")
    print("=====================================================================")

    # 1. Diagnóstico
    diag = diagnosticar_entorno()
    if not diag["ok"]:
        print("\n❌ Diagnóstico fallido. Resuelva las alertas antes de operar.", file=sys.stderr)
        return 1

    # 2. Datos macro
    if not ejecutar_cadena_datos():
        return 1

    # 3. Agenda
    consultar_agenda()

    # 4. Preparar
    tanda = tanda_dir or preparar_carrusel(top=top, matriz=matriz)

    # 5. Auditar editorial
    editorial_ok = auditar_editorial(tanda)
    if not editorial_ok:
        print("\n⏸️ Flujo pausado: Ingrese los textos editoriales pendientes en la tanda y vuelva a ejecutar.", flush=True)
        return 2

    # 6. Rendir
    if not rendir_carrusel(tanda):
        return 1

    # 7. Probar en Banco de Pruebas
    print("\n¿Desea enviar la prueba a 'GI · Banco de Pruebas'? Ejecutando...")
    if not despachar_a_pruebas(tanda):
        print("❌ Fallo en el despacho de prueba.", file=sys.stderr)
        return 1

    # 8. Despacho oficial
    if confirmar_despacho:
        if not despachar_oficial(tanda, confirmado=True):
            return 1
    else:
        print("\n✅ Tanda probada y certificada en 'GI · Banco de Pruebas'.")
        print(f"Para emitir a los canales oficiales de clientes, ejecute:")
        print(f"  uv run --with MetaTrader5 python scripts/jornada_matutina.py --despachar {tanda} --confirmar")

    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Orquestador Maestro y Guardia de la Jornada Matutina")
    parser.add_argument("--diagnostico", action="store_true", help="verifica salud de MT5, WhatsApp y navegadores")
    parser.add_argument("--datos", action="store_true", help="ejecuta cadena de datos macro y valida relojes")
    parser.add_argument("--agenda", action="store_true", help="consulta la agenda oficial del día")
    parser.add_argument("--preparar", action="store_true", help="prepara la tanda con el escáner cuantitativo")
    parser.add_argument("--auditar", nargs="?", const="", help="audita los textos con el linter editorial")
    parser.add_argument("--rendir", nargs="?", const="", help="renderiza las imágenes TradingView a 300 DPI")
    parser.add_argument("--probar", nargs="?", const="", help="despacha la tanda a GI · Banco de Pruebas")
    parser.add_argument("--despachar", nargs="?", const="", help="despacha la tanda a los canales oficiales")
    parser.add_argument("--confirmar", action="store_true", help="autorización explícita para despacho real a clientes")
    parser.add_argument("--todo", action="store_true", help="ejecuta el pipeline completo de punta a punta")
    parser.add_argument("--top", type=int, default=1, help="cantidad de piezas por canal (default: 1)")
    parser.add_argument("--matriz", action="store_true", default=True, help="cobertura de los 5 grupos de mercado (default: True)")
    parser.add_argument("--no-matriz", dest="matriz", action="store_false", help="desactiva el modo matriz y usa top global")

    args = parser.parse_args(argv)

    if args.diagnostico:
        return 0 if diagnosticar_entorno()["ok"] else 1
    elif args.datos:
        return 0 if ejecutar_cadena_datos() else 1
    elif args.agenda:
        return 0 if consultar_agenda() else 1
    elif args.preparar:
        preparar_carrusel(top=args.top, matriz=args.matriz)
        return 0
    elif args.auditar is not None:
        tanda = resolver_ultima_tanda(args.auditar or None)
        return 0 if auditar_editorial(tanda) else 1
    elif args.rendir is not None:
        tanda = resolver_ultima_tanda(args.rendir or None)
        return 0 if rendir_carrusel(tanda) else 1
    elif args.probar is not None:
        tanda = resolver_ultima_tanda(args.probar or None)
        return 0 if despachar_a_pruebas(tanda) else 1
    elif args.despachar is not None:
        tanda = resolver_ultima_tanda(args.despachar or None)
        return 0 if despachar_oficial(tanda, confirmado=args.confirmar) else 1
    elif args.todo:
        return ejecutar_todo(confirmar_despacho=args.confirmar, top=args.top, matriz=args.matriz)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
