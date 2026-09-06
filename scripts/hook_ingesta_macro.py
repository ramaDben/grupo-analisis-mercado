#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hook de SessionStart: el estado de la ingesta macro y su refresco en background.

Por que hay dos modos y no uno. La ingesta completa (bancos centrales, commodities
y el motor de sesgo que dispara al final) tarda ~55 s medidos el 2026-09-05: pagar
eso en cada arranque de sesion cuesta un minuto por sesion, y en un dia se abren
varias. Pero un hook que corre en background NO puede contarle nada al modelo,
porque su salida no entra al contexto. Asi que el evento lleva dos hooks del mismo
modulo:

    --estado     bloqueante, solo stdlib, < 1 s: lee el reloj de la ingesta y lo
                 inyecta como additionalContext.
    --refrescar  async: si ese mismo reloj esta vencido, corre el pipeline.

La condicion de vencimiento vive en `esta_vencida` y la consultan los dos modos.
Dos umbrales para la misma decision dejarian al contexto afirmando que el dato
esta fresco mientras el otro hook lo esta bajando, que es el defecto recurrente
del repo (ver "Contratos de nombres" en CLAUDE.md).

El hook nunca aborta la sesion: todo error se traga y se reporta como texto. Un
fallo de red del BCCh no puede impedir abrir Claude Code.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

RAIZ = Path(__file__).resolve().parent.parent
ESTADO = RAIZ / "data central" / "DATA AGENDA" / "estado_ejecucion.json"
INGESTA = RAIZ / ".agents" / "skills" / "ecosistema-datos-macro" / "scripts" / "pipeline_ingesta.py"
LOCK = RAIZ / "data" / ".ingesta_macro.lock"
LOG = RAIZ / "data" / "logs" / "hook_ingesta_macro.log"

# Seis horas: los emisores publican una vez al dia (FRED en T+1 habil, el BCCh en
# T-2 habiles), asi que refrescar mas seguido golpea las APIs sin traer un dato
# nuevo. Mas espaciado dejaria a la sesion de la tarde leyendo el cierre de la
# manana.
UMBRAL_HORAS = 6

# Un lock mas viejo que esto es huerfano: la ingesta medida tarda ~1 min, y quince
# minutos solo se explican por un proceso que murio sin limpiarlo.
LOCK_HUERFANO_MIN = 15

# La ingesta corre bajo `uv` porque los extractores necesitan requests y dotenv,
# que viven en el .venv del proyecto y no en el Python del sistema.
COMANDO = ["uv", "run", "python", str(INGESTA)]

CHILE = "America/Santiago"


# ─────────────────────────────────────────────────────────────────────────────
# El reloj de la ingesta: una sola lectura, dos consumidores
# ─────────────────────────────────────────────────────────────────────────────
def leer_estado() -> dict | None:
    """El estado de la ultima ingesta, o None si nunca corrio o esta ilegible."""
    try:
        return json.loads(ESTADO.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def antiguedad_horas(estado: dict | None) -> float | None:
    """Horas transcurridas desde la ultima ingesta. None si no se puede saber."""
    if not estado:
        return None
    marca = estado.get("ultima_ejecucion_utc")
    if not marca:
        return None
    try:
        cuando = datetime.fromisoformat(marca)
    except (ValueError, TypeError):
        return None
    if cuando.tzinfo is None:
        cuando = cuando.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - cuando).total_seconds() / 3600


def esta_vencida(estado: dict | None) -> bool:
    """Fuente unica de la decision de refrescar. Sin registro previo, vencida."""
    horas = antiguedad_horas(estado)
    return horas is None or horas >= UMBRAL_HORAS


def hora_chile(marca_utc: str) -> str:
    """La marca UTC del estado, en hora de Chile (regla canonica del proyecto)."""
    try:
        cuando = datetime.fromisoformat(marca_utc)
        if cuando.tzinfo is None:
            cuando = cuando.replace(tzinfo=timezone.utc)
        try:
            from zoneinfo import ZoneInfo

            local = cuando.astimezone(ZoneInfo(CHILE))
        except Exception:  # noqa: BLE001
            # Sin tzdata cae al reloj del sistema, que en esta maquina ES Chile.
            local = cuando.astimezone()
        return local.strftime("%Y-%m-%d %H:%M")
    except Exception:  # noqa: BLE001
        return marca_utc or "desconocida"


# ─────────────────────────────────────────────────────────────────────────────
# Modo --estado: lo unico que llega al contexto del modelo
# ─────────────────────────────────────────────────────────────────────────────
def texto_estado(estado: dict | None) -> str:
    if estado is None:
        return (
            "[DATOS MACRO] No hay registro de ingesta previa (falta o esta ilegible "
            "'data central/DATA AGENDA/estado_ejecucion.json'). Se lanzo una ingesta en "
            "segundo plano; hasta que termine no hay datos de bancos centrales que citar."
        )

    horas = antiguedad_horas(estado)
    edad = "antiguedad desconocida" if horas is None else f"hace {horas:.1f} h"
    cuando = hora_chile(estado.get("ultima_ejecucion_utc", ""))

    status = estado.get("status_por_fuente") or {}
    fuentes = ", ".join(f"{k} {v}" for k, v in status.items()) if status else "sin detalle"
    errores = estado.get("errores_por_fuente") or {}

    lineas = [
        f"[DATOS MACRO] Ultima ingesta: {cuando} hora Chile ({edad}).",
        f"Fuentes: {fuentes}.",
    ]
    if errores:
        detalle = "; ".join(f"{k}: {v}" for k, v in errores.items())
        lineas.append(f"Errores de la ultima corrida: {detalle}.")

    novedades = estado.get("novedades_detalle") or []
    if estado.get("hay_novedades") and novedades:
        lineas.append("Novedades: " + " | ".join(novedades[:4]) + ".")

    if esta_vencida(estado):
        lineas.append(
            f"Supera el umbral de {UMBRAL_HORAS} h: se lanzo un refresco en segundo plano "
            "(~1 min). Los JSON de 'data central/' y macro_bias_output.json van a cambiar "
            "durante esta sesion, asi que releelos antes de citar cifras macro."
        )
    else:
        lineas.append(f"Dentro del umbral de {UMBRAL_HORAS} h: no se refresco nada.")

    return " ".join(lineas)


def modo_estado() -> int:
    estado = leer_estado()
    salida: dict = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": texto_estado(estado),
        },
        "suppressOutput": True,
    }
    if esta_vencida(estado):
        salida["systemMessage"] = (
            "Datos macro vencidos: refrescando bancos centrales en segundo plano (~1 min)."
        )
    print(json.dumps(salida, ensure_ascii=False))
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Modo --refrescar: el que de verdad baja los datos, sin bloquear la sesion
# ─────────────────────────────────────────────────────────────────────────────
def lock_vigente() -> bool:
    """True si otra sesion ya esta corriendo la ingesta ahora mismo.

    Dos ventanas abiertas a la vez dispararian dos ingestas sobre los mismos
    archivos. Un lock viejo se ignora: un proceso que murio sin limpiarlo no puede
    dejar la ingesta bloqueada para siempre.
    """
    try:
        edad = datetime.now(timezone.utc) - datetime.fromtimestamp(
            LOCK.stat().st_mtime, tz=timezone.utc
        )
    except Exception:  # noqa: BLE001
        return False
    return edad < timedelta(minutes=LOCK_HUERFANO_MIN)


def anotar(mensaje: str) -> None:
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        sello = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with LOG.open("a", encoding="utf-8") as fh:
            fh.write(f"[{sello}] {mensaje}\n")
    except Exception:  # noqa: BLE001
        pass


def modo_refrescar() -> int:
    estado = leer_estado()
    if not esta_vencida(estado):
        horas = antiguedad_horas(estado) or 0.0
        anotar(f"sin refresco: ingesta de hace {horas:.1f} h, bajo el umbral de {UMBRAL_HORAS} h")
        return 0
    if lock_vigente():
        anotar("sin refresco: otra sesion tiene la ingesta en curso")
        return 0

    try:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(
            f"{os.getpid()} {datetime.now(timezone.utc).isoformat()}\n", encoding="utf-8"
        )
    except Exception as exc:  # noqa: BLE001
        anotar(f"no se pudo tomar el lock: {exc}")
        return 0

    anotar("ingesta lanzada")
    try:
        proc = subprocess.run(
            COMANDO,
            cwd=str(RAIZ),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=600,
        )
        anotar(f"ingesta terminada con codigo {proc.returncode}")
        # Solo lineas con contenido: el pipeline cierra con lineas en blanco y una
        # cola vacia en el log no dice si la corrida sirvio.
        utiles = [ln for ln in (proc.stdout or "").splitlines() if ln.strip()]
        for linea in utiles[-3:]:
            anotar(f"  | {linea.strip()}")
        if proc.returncode != 0:
            for linea in (proc.stderr or "").strip().splitlines()[-5:]:
                anotar(f"  ! {linea}")
    except subprocess.TimeoutExpired:
        anotar("ingesta abortada: supero los 600 s")
    except Exception as exc:  # noqa: BLE001
        anotar(f"ingesta fallida: {exc}")
    finally:
        try:
            LOCK.unlink(missing_ok=True)
        except Exception:  # noqa: BLE001
            pass
    return 0


def main() -> int:
    modo = sys.argv[1] if len(sys.argv) > 1 else "--estado"
    if modo == "--refrescar":
        return modo_refrescar()
    if modo == "--estado":
        return modo_estado()
    print(f"uso: {Path(__file__).name} [--estado|--refrescar]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    # Un hook que revienta no puede tumbar el arranque de la sesion.
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"systemMessage": f"hook_ingesta_macro fallo: {exc}"}, ensure_ascii=False))
        sys.exit(0)
