#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Módulo de Producción y Despacho Ad-hoc Sistematizado.

Permite generar artefactos (Stories PNG, mensajes TXT en UTF-8), auditar guardrails
de cliente y precios, y despachar a WhatsApp de manera 100% declarativa a partir de
un manifiesto JSON, eliminando la creación de scripts .py desechables de un solo uso.

Uso:
    python scripts/produccion_adhoc.py --generar <manifiesto.json>
    python scripts/produccion_adhoc.py --auditar <manifiesto.json>
    python scripts/produccion_adhoc.py --despachar <manifiesto.json> [--dry-run]
    python scripts/produccion_adhoc.py --todo <manifiesto.json> [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
SRC = RAIZ / "src"
SCRIPTS = RAIZ / "scripts"

for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from story_grafico import enriquecer
    from story_render import render_story
except ImportError:
    enriquecer = None
    render_story = None

try:
    from whatsapp_sender import WhatsAppSender, huella
    from bitacora_despachos import cargar as cargar_bitacora
    from bitacora_despachos import registrar as anotar_despacho
    from bitacora_despachos import ya_despachada
except ImportError:
    WhatsAppSender = None
    huella = None
    cargar_bitacora = None
    anotar_despacho = None
    ya_despachada = None

from guardrails import texto_cliente, precios


def cargar_manifiesto(ruta: Path) -> dict[str, Any]:
    """Carga y valida el archivo de manifiesto JSON."""
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo de manifiesto: {ruta}")
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Error al decodificar JSON en {ruta}: {exc}") from exc

    if not isinstance(datos, dict):
        raise ValueError("El manifiesto debe ser un objeto JSON (dict).")
    if "tanda" not in datos:
        raise ValueError("El manifiesto requiere el campo 'tanda'.")
    if "despachos" not in datos or not isinstance(datos["despachos"], list):
        raise ValueError("El manifiesto requiere la lista 'despachos'.")
    return datos


def generar_artefactos(manifiesto: dict[str, Any], base_dir: Path | None = None) -> list[Path]:
    """Genera imágenes PNG y escribe archivos TXT declarados en el manifiesto."""
    archivos_generados: list[Path] = []
    raiz_relativa = base_dir or RAIZ

    # 1. Generar Story PNG si está definida
    story_cfg = manifiesto.get("story")
    if story_cfg:
        plantilla_rel = story_cfg.get("plantilla", "dato_macro.html")
        plantilla_path = RAIZ / "templates" / "stories" / plantilla_rel if not Path(plantilla_rel).is_absolute() else Path(plantilla_rel)
        if not plantilla_path.exists():
            plantilla_path = RAIZ / plantilla_rel

        salida_png_str = story_cfg.get("salida_png") or story_cfg.get("png")
        if not salida_png_str:
            raise ValueError("La configuración de 'story' requiere 'salida_png' o 'png'.")
        
        salida_png = Path(salida_png_str)
        if not salida_png.is_absolute():
            salida_png = RAIZ / salida_png

        payload = story_cfg.get("payload", {})
        motor = story_cfg.get("motor") or story_cfg.get("tipo")

        if motor == "tradingview":
            try:
                from tradingview_grafico import generar_grafico_tv
            except ImportError as exc:
                raise RuntimeError(f"tradingview_grafico no está disponible: {exc}") from exc

            ticker = story_cfg.get("ticker") or payload.get("ticker") or story_cfg.get("activo") or ""
            nombre = story_cfg.get("nombre") or payload.get("nombre") or ticker
            timeframe = story_cfg.get("timeframe", "H1")
            velas = int(story_cfg.get("velas", 60))
            soporte = story_cfg.get("soporte", payload.get("soporte"))
            resistencia = story_cfg.get("resistencia", payload.get("resistencia"))
            digits = story_cfg.get("digits", payload.get("digits"))

            salida_png.parent.mkdir(parents=True, exist_ok=True)
            generar_grafico_tv(
                ticker=ticker,
                nombre=nombre,
                destino=salida_png,
                timeframe=timeframe,
                n_velas=velas,
                digits=int(digits) if digits is not None else None,
                soporte=float(soporte) if soporte is not None else None,
                resistencia=float(resistencia) if resistencia is not None else None,
            )
            archivos_generados.append(salida_png)
            print(f"  📈 Gráfico TradingView 300 DPI generado: {salida_png.name} ({salida_png.stat().st_size} bytes)")
        else:
            if not payload:
                raise ValueError("La configuración de 'story' requiere un 'payload'.")

            # Si el payload requiere enriquecimiento gráfico (barras o serie)
            if "recorrido" in payload:
                if enriquecer is None:
                    raise RuntimeError("story_grafico.enriquecer no está disponible.")
                payload = enriquecer(payload.copy())

            if render_story is None:
                raise RuntimeError("story_render.render_story no está disponible.")

            salida_png.parent.mkdir(parents=True, exist_ok=True)
            formato = story_cfg.get("formato", "horizontal")
            render_story(payload, plantilla_path, salida_png, formato=formato)
            archivos_generados.append(salida_png)
            print(f"  🎨 Story generada: {salida_png.name} ({salida_png.stat().st_size} bytes)")

    # 2. Materializar archivos .txt de texto de cliente
    for item in manifiesto["despachos"]:
        mensaje_texto = item.get("mensaje_texto")
        archivo_txt_str = item.get("archivo_txt") or item.get("mensaje")
        if archivo_txt_str:
            archivo_txt = Path(archivo_txt_str)
            if not archivo_txt.is_absolute():
                archivo_txt = RAIZ / archivo_txt
            if mensaje_texto:
                archivo_txt.parent.mkdir(parents=True, exist_ok=True)
                archivo_txt.write_text(mensaje_texto.strip() + "\n", encoding="utf-8")
                archivos_generados.append(archivo_txt)
                print(f"  📝 Archivo TXT escrito: {archivo_txt.name} ({len(mensaje_texto)} chars)")
            elif not archivo_txt.exists():
                raise FileNotFoundError(f"No existe el archivo de texto declarado: {archivo_txt}")

    return archivos_generados


def auditar_manifiesto(manifiesto: dict[str, Any]) -> tuple[bool, list[str]]:
    """Ejecuta los guardrails institucionales sobre todos los mensajes y adjuntos."""
    errores: list[str] = []
    
    # 1. Auditar Story si fue declarada
    story_cfg = manifiesto.get("story")
    if story_cfg:
        salida_png_str = story_cfg.get("salida_png") or story_cfg.get("png")
        salida_png = Path(salida_png_str) if salida_png_str else None
        if salida_png and not salida_png.is_absolute():
            salida_png = RAIZ / salida_png
        if salida_png and salida_png.exists():
            if salida_png.stat().st_size < 5000:
                errores.append(f"PNG de Story sospechosamente pequeño (<5KB): {salida_png}")
        elif salida_png:
            errores.append(f"PNG de Story declarado no existe en disco: {salida_png}")

    # 2. Auditar cada despacho
    for idx, item in enumerate(manifiesto["despachos"], 1):
        canal = item.get("canal", f"canal_{idx}")
        pieza = item.get("pieza", f"pieza_{idx}")
        
        # Obtener texto a auditar
        texto = item.get("mensaje_texto")
        if not texto:
            archivo_txt_str = item.get("archivo_txt") or item.get("mensaje")
            if archivo_txt_str:
                archivo_txt = Path(archivo_txt_str)
                if not archivo_txt.is_absolute():
                    archivo_txt = RAIZ / archivo_txt
                if archivo_txt.exists():
                    texto = archivo_txt.read_text(encoding="utf-8")
                else:
                    errores.append(f"[{canal}|{pieza}] Archivo de mensaje no existe: {archivo_txt}")
                    continue
            else:
                errores.append(f"[{canal}|{pieza}] No se definió 'mensaje_texto' ni 'archivo_txt'")
                continue

        # Guardrail: Guiones largos (em-dash / en-dash)
        v_guion = texto_cliente.sin_guion_largo(texto)
        if not v_guion.ok:
            errores.append(f"[{canal}|{pieza}] Guión largo prohibido: {v_guion.detalle}")

        # Guardrail: Siglas explicadas
        v_siglas = texto_cliente.siglas_explicadas(texto, en_linea=False)
        if not v_siglas.ok:
            errores.append(f"[{canal}|{pieza}] Siglas no explicadas: {v_siglas.detalle} ({v_siglas.ubicacion})")

        # Guardrail: Tono admisible
        v_tono = texto_cliente.tono_admisible(texto)
        if not v_tono.ok:
            errores.append(f"[{canal}|{pieza}] Tono inadmisible: {v_tono.detalle}")

        # Guardrail: Sin voseo
        v_voseo = texto_cliente.sin_voseo(texto)
        if not v_voseo.ok:
            errores.append(f"[{canal}|{pieza}] Voseo detectado: {v_voseo.detalle}")

        # Guardrail: Canales existentes
        v_canales = texto_cliente.canales_existen(texto)
        if not v_canales.ok:
            errores.append(f"[{canal}|{pieza}] Canal inexistente referenciado: {v_canales.detalle}")

        # Guardrail: Precios y decimales
        v_precios = precios.revisar_texto(texto)
        if not v_precios.ok:
            errores.append(f"[{canal}|{pieza}] Precios/decimales inválidos: {v_precios.detalle}")
        
        activo = item.get("activo")
        if activo:
            v_activo_dec = precios.decimales_correctos(texto, activo)
            if not v_activo_dec.ok:
                errores.append(f"[{canal}|{pieza}] Decimales incorrectos para {activo}: {v_activo_dec.detalle}")

        # Adjunto si se declaró
        adjunto_str = item.get("adjunto")
        if adjunto_str:
            adjunto = Path(adjunto_str)
            if not adjunto.is_absolute():
                adjunto = RAIZ / adjunto
            if not adjunto.exists():
                errores.append(f"[{canal}|{pieza}] Archivo adjunto no existe: {adjunto}")

    return len(errores) == 0, errores


def ejecutar_despacho(manifiesto: dict[str, Any], dry_run: bool = False) -> int:
    """Ejecuta el despacho secuencial a WhatsApp con bitácora y cadencia anti-baneo."""
    tanda = manifiesto["tanda"]
    despachos = manifiesto["despachos"]

    # 1. Auditoría previa estricta
    ok, errores = auditar_manifiesto(manifiesto)
    if not ok:
        print(f"\n❌ FALLO DE AUDITORÍA PREVIA ({len(errores)} errores):", file=sys.stderr)
        for err in errores:
            print(f"  • {err}", file=sys.stderr)
        return 1

    if WhatsAppSender is None:
        raise RuntimeError("whatsapp_sender no está disponible.")

    sender = WhatsAppSender(headless=True)
    bitacora = cargar_bitacora()

    print(f"\n🚀 INICIANDO DESPACHO AD-HOC SISTEMATIZADO: {tanda}")
    print(f"Modo: {'SIMULADO (dry-run)' if dry_run else 'REAL (WhatsApp Web)'}")
    print(f"Total piezas: {len(despachos)}\n")

    exitos = 0
    for item in despachos:
        canal = item.get("canal") or item.get("alias", "")
        alias = item.get("alias") or item.get("canal", "")
        pieza = item.get("pieza", f"pieza_{canal}")
        activo = item.get("activo", "")
        
        # Obtener adjunto
        adjunto = None
        adjunto_str = item.get("adjunto")
        if adjunto_str:
            adjunto = Path(adjunto_str)
            if not adjunto.is_absolute():
                adjunto = RAIZ / adjunto

        # Obtener texto
        texto = item.get("mensaje_texto")
        if not texto:
            archivo_txt_str = item.get("archivo_txt") or item.get("mensaje")
            archivo_txt = Path(archivo_txt_str) if archivo_txt_str else None
            if archivo_txt and not archivo_txt.is_absolute():
                archivo_txt = RAIZ / archivo_txt
            if archivo_txt and archivo_txt.exists():
                texto = archivo_txt.read_text(encoding="utf-8")
        
        if not texto:
            print(f"  ❌ No hay texto para [{canal}|{pieza}]", file=sys.stderr)
            return 1
        
        texto = texto.strip()

        print(f"--- [{canal}] ({activo}) -> alias '{alias}' ---")
        if not dry_run and ya_despachada(bitacora, tanda, canal, pieza):
            print("  ⏭️ Ya despachada según bitácora: se omite.")
            continue

        print(f"  Enviando pieza '{pieza}' ({len(texto)} chars)...")
        res = sender.enviar(
            destinatario=alias,
            mensaje=texto,
            adjunto=adjunto,
            dry_run=dry_run,
        )

        if not dry_run:
            anotar_despacho(
                tanda,
                canal,
                pieza,
                activo=activo,
                huella=huella(texto) if huella else "",
            )
            bitacora = cargar_bitacora()

        print(f"  ✅ Entregado a '{res.get('destinatario')}': {res.get('status')}")
        exitos += 1

    print(f"\n✨ Despacho finalizado con éxito: {exitos} piezas procesadas.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Módulo de Producción y Despacho Ad-hoc")
    parser.add_argument("manifiesto", type=Path, help="Ruta al archivo manifiesto.json")
    parser.add_argument("--generar", action="store_true", help="Generar imágenes PNG y archivos TXT")
    parser.add_argument("--auditar", action="store_true", help="Auditar guardrails y consistencia")
    parser.add_argument("--despachar", action="store_true", help="Ejecutar despacho a WhatsApp")
    parser.add_argument("--todo", action="store_true", help="Generar, auditar y despachar en una sola corrida")
    parser.add_argument("--dry-run", action="store_true", help="Modo simulación (sin envío real)")

    args = parser.parse_args()

    if not (args.generar or args.auditar or args.despachar or args.todo):
        parser.print_help()
        return 1

    manifiesto = cargar_manifiesto(args.manifiesto)

    if args.generar or args.todo:
        print(f"\n📦 GENERANDO ARTEFACTOS PARA: {manifiesto['tanda']}")
        generar_artefactos(manifiesto)

    if args.auditar or args.todo:
        print(f"\n🛡️ AUDITANDO GUARDRAILS PARA: {manifiesto['tanda']}")
        ok, errores = auditar_manifiesto(manifiesto)
        if not ok:
            print(f"❌ FALLARON {len(errores)} GUARDRAILS:", file=sys.stderr)
            for err in errores:
                print(f"  • {err}", file=sys.stderr)
            return 1
        print("✅ Todos los guardrails aprobados (0 errores).")

    if args.despachar or args.todo:
        return ejecutar_despacho(manifiesto, dry_run=args.dry_run)

    return 0


if __name__ == "__main__":
    sys.exit(main())
