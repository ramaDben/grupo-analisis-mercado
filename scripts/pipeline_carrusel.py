#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Carrusel de la tanda: del Top 3 del escáner a las 3 Stories listas.

Encadena lo que ya existe en vez de reimplementarlo: `screener_gi` elige,
`serie_mt5` trae la serie real, `story_grafico` calcula la geometría,
`story_render` produce el PNG y `ruta_story.ps1` decide dónde se guarda.

**El reparto de trabajo es deliberado y no conviene borrarlo.** Este script
produce los DATOS de cada pieza: precio, soporte, resistencia, dirección,
impulso proyectado, la serie del gráfico. No escribe el titular ni el párrafo,
porque eso es criterio editorial y un script no lo tiene. Por eso hay dos pasos:

    1. `--preparar`  arma los 3 payloads con todos los datos resueltos y los
                     campos editoriales vacíos, marcados como pendientes.
    2. `--rendir`    valida que estén escritos y produce las 6 imágenes
                     (3 piezas x 2 formatos).

Si el paso 2 encuentra un campo editorial vacío, se detiene. Es la misma razón
por la que el renderer falla ante una imagen inexistente: una pieza a medias que
sale sin avisar llega al cliente.

Uso:
    uv run --with MetaTrader5 python scripts/pipeline_carrusel.py --preparar
    # ... el comando /carrusel escribe titular y parrafo en cada payload ...
    uv run --extra stories python scripts/pipeline_carrusel.py --rendir data/carrusel/<dir>
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
for p in (str(SRC), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import screener_gi as sc  # noqa: E402

SANTIAGO = ZoneInfo("America/Santiago")
DIR_TRABAJO = RAIZ / "data" / "carrusel"
PLANTILLA = RAIZ / "templates" / "stories" / "alerta.html"

# Cuántas velas de H1 lleva el gráfico de la alerta. 60 velas de H1 son dos días
# y medio de sesión: suficiente para que el nivel que se está comunicando tenga
# historia visible detrás, sin que la línea se convierta en ruido.
VELAS_GRAFICO = 60
TIMEFRAME_GRAFICO = "H1"

# Los campos que este script NO puede llenar. Se escriben vacíos y `--rendir` se
# niega a trabajar hasta que tengan texto.
CAMPOS_EDITORIALES = ("titular", "parrafo")


def _slug_de_imagen(imagen: str) -> str:
    """El slug del activo es el nombre del archivo de imagen, sin extensión.

    Es la convención del repo (`oro.jpg` -> `activo-oro`) y la que hace que
    imagen y color salgan del mismo dato. Un ETF que replica un índice comparte
    las dos cosas: `GLD.US` usa `oro.jpg` y por tanto el dorado del Oro, que es
    exactamente como debe verse.
    """
    return Path(imagen).stem


def _chip_categoria(clase: str, nombre_activo: str) -> str:
    etiquetas = {
        "forex_commodities": "COMMODITIES",
        "crypto": "CRIPTOMONEDAS",
        "indices": "ÍNDICES",
        "etfs": "ETF",
        "acciones": "ACCIONES",
    }
    return f"{etiquetas.get(clase, 'MERCADO')} · {nombre_activo.upper()}"


def _serie_para(ticker: str) -> dict[str, Any]:
    """Serie real de cierres desde el terminal, como bloque `recorrido`."""
    from serie_mt5 import obtener_serie

    cierres, _tiempos = obtener_serie(ticker, TIMEFRAME_GRAFICO, VELAS_GRAFICO)
    return cierres


def construir_payload(
    seleccion: dict[str, Any],
    activo_catalogo: dict[str, Any],
    ahora: datetime,
    cierres: list[float],
) -> dict[str, Any]:
    """Payload de `alerta` con los datos resueltos y lo editorial en blanco."""
    digits = activo_catalogo["digits"]
    imagen = activo_catalogo["imagen"]
    slug = _slug_de_imagen(imagen)
    alcista = seleccion["direccion"] == "ALCISTA"

    def fmt(valor: float) -> str:
        return f"{valor:,.{digits}f}".replace(",", "@").replace(".", ",").replace("@", ".")

    return {
        "plantilla": "alerta",
        # Editorial: lo llena el comando, no el script.
        "titular": "",
        "parrafo": "",
        # Identidad y marco
        "activo": activo_catalogo["nombre"],
        "activo_slug": slug,
        "activo_imagen": imagen,
        "rotulo_activo": f"{activo_catalogo['nombre'].upper()} · {seleccion['ticker']}",
        "chip_categoria": _chip_categoria(seleccion["clase"], activo_catalogo["nombre"]),
        "fecha_hora": ahora.strftime("%d %b %Y · %H:%M").upper(),
        "sesgo": "Alcista" if alcista else "Bajista",
        "tag_riesgo": "ALCISTA" if alcista else "BAJISTA",
        # Datos del motor
        "precio_actual": fmt(seleccion["precio"]),
        "soporte": fmt(seleccion["soporte"]),
        "resistencia": fmt(seleccion["resistencia"]),
        "vol_pct": f"{fmt(seleccion['impulso_adc_atr'])} {activo_catalogo['unidad']}",
        "rotulo_grafico": (
            f"{seleccion['ticker']} · CIERRES {TIMEFRAME_GRAFICO} · "
            f"ÚLTIMAS {VELAS_GRAFICO} VELAS"
        ),
        "sello_datos": (
            f"DATOS REALES · METATRADER 5 · {ahora.strftime('%d %b %H:%M').upper()}"
        ),
        "fuente": "MT5 · GRUPO INTELIGENCIA",
        "chart_png": None,
        "recorrido": {
            "serie": cierres,
            "lienzo": "alto",
            "marcadores": [{
                "indice": len(cierres) - 1,
                "precio": seleccion["precio"],
                "clase": "actual",
                "etiqueta": fmt(seleccion["precio"]),
                "rol": "AHORA",
            }],
            "niveles": [
                {"precio": seleccion["resistencia"], "clase": "resistencia",
                 "etiqueta": fmt(seleccion["resistencia"]), "rol": "RESISTENCIA"},
                {"precio": seleccion["soporte"], "clase": "soporte",
                 "etiqueta": fmt(seleccion["soporte"]), "rol": "SOPORTE"},
            ],
        },
        # Trazabilidad: por qué este activo y no otro. No se rinde en la pieza,
        # pero deja el score auditable junto al payload que produjo.
        "_procedencia": {
            "score": seleccion["score"],
            "factores": seleccion["factores"],
            "ticker": seleccion["ticker"],
        },
        "_pendiente_editorial": list(CAMPOS_EDITORIALES),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Paso 1: preparar
# ─────────────────────────────────────────────────────────────────────────────
def preparar(
    tanda: int | None = None,
    top: int = 3,
    solo_renderizables: bool = True,
) -> dict[str, Any]:
    """Corre el escáner y deja los payloads listos salvo lo editorial."""
    resultado = sc.escanear(tanda=tanda, top=top, solo_renderizables=solo_renderizables)
    ahora = datetime.now(tz=SANTIAGO)
    n_tanda = resultado["tanda"]

    catalogo = {a["ticker"]: a for a in sc.cargar_universo(solo_renderizables=False)}

    destino = DIR_TRABAJO / f"{ahora.strftime('%Y-%m-%d')}_tanda{n_tanda}"
    destino.mkdir(parents=True, exist_ok=True)

    (destino / "_screener.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    payloads: list[dict[str, Any]] = []
    problemas: list[str] = []
    for i, sel in enumerate(resultado["seleccion"], 1):
        activo = catalogo.get(sel["ticker"])
        if not activo or not activo.get("imagen"):
            problemas.append(
                f"{sel['ticker']} no tiene imagen declarada: su pieza no se puede rendir"
            )
            continue
        try:
            cierres = _serie_para(sel["ticker"])
        except Exception as exc:  # noqa: BLE001
            problemas.append(f"{sel['ticker']}: no se pudo traer la serie ({exc})")
            continue

        payload = construir_payload(sel, activo, ahora, cierres)
        archivo = destino / f"{i}_{sc._normalizar(sel['ticker']).replace('.', '').replace('#', '')}.json"
        archivo.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        payloads.append({"archivo": str(archivo), "ticker": sel["ticker"], "score": sel["score"]})

    return {
        "tanda": n_tanda,
        "nombre_tanda": resultado["nombre_tanda"],
        "hora_chile_tanda": resultado["hora_chile_tanda"],
        "directorio": str(destino),
        "payloads": payloads,
        "problemas": problemas,
        "avisos": resultado["avisos"],
        "campos_por_escribir": list(CAMPOS_EDITORIALES),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Paso 2: rendir
# ─────────────────────────────────────────────────────────────────────────────
def _ruta_story(activo_slug: str, hora: str, fecha: str) -> Path:
    """Delega en `ruta_story.ps1`, que es el helper determinista del repo.

    No se arma la ruta a mano: la convención día/activo/plantilla vive en ese
    script y duplicarla acá garantizaría que las dos versiones se separen.
    """
    salida = subprocess.run(
        ["powershell", "-NoProfile", "-File", str(RAIZ / "scripts" / "ruta_story.ps1"),
         "-Fecha", fecha, "-Plantilla", "alerta", "-Hora", hora, "-Activo", activo_slug],
        capture_output=True, text=True, cwd=str(RAIZ),
    )
    if salida.returncode != 0:
        raise RuntimeError(f"ruta_story.ps1 fallo: {salida.stderr.strip()}")
    return Path(salida.stdout.strip())


def rendir(directorio: Path) -> dict[str, Any]:
    """Valida lo editorial y produce las piezas en horizontal y vertical."""
    from story_grafico import enriquecer
    from story_render import render_story

    archivos = sorted(p for p in directorio.glob("*.json") if not p.name.startswith("_"))
    if not archivos:
        raise SystemExit(f"No hay payloads en {directorio}")

    sin_escribir: list[str] = []
    for archivo in archivos:
        payload = json.loads(archivo.read_text(encoding="utf-8"))
        faltan = [c for c in CAMPOS_EDITORIALES if not str(payload.get(c, "")).strip()]
        if faltan:
            sin_escribir.append(f"{archivo.name}: falta {', '.join(faltan)}")

    if sin_escribir:
        raise SystemExit(
            "Hay piezas sin texto editorial. Una pieza a medias que sale sin avisar "
            "llega al cliente, asi que el render se detiene:\n  "
            + "\n  ".join(sin_escribir)
        )

    ahora = datetime.now(tz=SANTIAGO)
    fecha, hora = ahora.strftime("%Y-%m-%d"), ahora.strftime("%H-%M")
    generadas: list[dict[str, Any]] = []

    for archivo in archivos:
        payload = json.loads(archivo.read_text(encoding="utf-8"))
        procedencia = payload.pop("_procedencia", {})
        payload.pop("_pendiente_editorial", None)

        # `story_grafico.enriquecer` consume `recorrido` y lo reemplaza por
        # `grafico`: el reparto es estricto, el script calcula coordenadas y la
        # plantilla aporta color y tipografia con sus clases .g-*.
        payload = enriquecer(payload)

        for formato in ("horizontal", "vertical"):
            destino = _ruta_story(payload["activo_slug"], hora, fecha)
            if formato == "vertical":
                # `ruta_story.ps1` no distingue formato, y las dos piezas del
                # mismo activo se pisarían en la misma ruta. El sufijo va acá y
                # no en el helper para no cambiar el contrato que ya usan /story
                # y /oportunidad.
                destino = destino.with_name(destino.stem + "_vertical" + destino.suffix)
            render_story(payload, PLANTILLA, destino, formato=formato)
            generadas.append({
                "ticker": procedencia.get("ticker", payload["activo_slug"]),
                "formato": formato,
                "archivo": str(destino),
            })

    return {"directorio": str(directorio), "imagenes": generadas}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Carrusel de la tanda: 3 Stories de alerta")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--preparar", action="store_true",
                       help="corre el escaner y deja los payloads con lo editorial en blanco")
    grupo.add_argument("--rendir", type=Path, metavar="DIR",
                       help="rinde los payloads ya escritos de ese directorio")
    parser.add_argument("--tanda", type=int, choices=sorted(sc.TANDAS))
    parser.add_argument("--top", type=int, default=3,
                        help="tope de piezas (default 3: WhatsApp muestra 3 adjuntos sin el boton +2)")
    parser.add_argument("--todos", action="store_true",
                        help="incluye activos sin imagen (su pieza no se va a poder rendir)")
    args = parser.parse_args(argv)

    if args.preparar:
        if args.top > 3:
            print(
                f"AVISO: --top {args.top} rompe la regla de cero spam. WhatsApp muestra "
                "3 adjuntos con previsualizacion; del cuarto en adelante aparece el boton +2.",
                file=sys.stderr,
            )
        res = preparar(tanda=args.tanda, top=args.top, solo_renderizables=not args.todos)
        print(f"\nTANDA {res['tanda']} - {res['nombre_tanda']} ({res['hora_chile_tanda']} hora Chile)")
        print(f"Directorio: {res['directorio']}")
        print(f"\nPAYLOADS ({len(res['payloads'])})")
        for p in res["payloads"]:
            print(f"  {p['ticker']:<12} score {p['score']:>3}/100  {Path(p['archivo']).name}")
        if res["problemas"]:
            print("\nPROBLEMAS")
            for p in res["problemas"]:
                print(f"  - {p}")
        if res["avisos"]:
            print("\nAVISOS DEL ESCANER")
            for a in res["avisos"]:
                print(f"  - {a}")
        print(f"\nFalta escribir en cada payload: {', '.join(res['campos_por_escribir'])}")
        print(f"Despues: --rendir {res['directorio']}")
        return 0

    res = rendir(args.rendir)
    print(f"\n{len(res['imagenes'])} imagen(es) generadas")
    for img in res["imagenes"]:
        print(f"  {img['ticker']:<12} {img['formato']:<11} {img['archivo']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
