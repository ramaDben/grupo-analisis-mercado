"""Trae la serie real de precios desde MT5 y arma el bloque `recorrido`.

Es el puente que faltaba entre dos piezas que ya existían y no se hablaban:
`mt5_client.get_rates()` sabe leer el histórico del terminal, y
`story_grafico.py` sabe convertir una serie en el SVG del gráfico. En
medio no había nada, y por eso los gráficos de las Stories eran dibujos fijos
que no correspondían al activo.

    cat operacion.json \
      | uv run python scripts/serie_mt5.py --ticker EURUSD --timeframe H1 --velas 60 \
      | uv run python scripts/story_grafico.py \
      | uv run python scripts/story_render.py --template templates/stories/operacion.html \
          --out data/stories/... --formato vertical

Entrada (stdin): el payload de la Story. Puede traer una clave `hitos` con los
precios de la operación; el script los ubica en la serie por proximidad y los
convierte en los marcadores que el generador de geometría espera.

    "hitos": [
      {"precio": 1.15038, "clase": "origen", "fecha": "2026-07-31 11:35",
       "rol": "ENTRADA"},
      {"precio": 1.16350, "clase": "meta",     "rol": "OBJETIVO"}
    ]

Salida (stdout): el mismo payload con `recorrido` = {serie, marcadores} listo, y
`hitos` fuera.

Por qué un script y no una tool MCP: el terminal MT5 vive en esta máquina y el
render también. Meter la serie en el protocolo MCP obligaría a mover cientos de
precios por el canal para que vuelvan a salir como coordenadas; acá el dato
nace y muere en el mismo proceso.

Reparto de responsabilidades, igual que en el resto del motor: este script trae
NÚMEROS. Las coordenadas las calcula `story_grafico.py` y el color y
la tipografía viven en las clases del snapshot.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

_TIMEFRAMES = ("M5", "M15", "M30", "H1", "H4", "D1")


class SerieError(RuntimeError):
    """Error accionable al pedir la serie (mismo criterio que StoryRenderError)."""


def obtener_serie(ticker: str, timeframe: str, n_velas: int) -> tuple[list[float], list]:
    """Cierres y marcas de tiempo de las últimas `n_velas` velas, cronológicos.

    El import de MT5 es perezoso —dentro de la función— por el mismo motivo que
    en `story_render.render_png`: así los tests de forma pueden importar este
    módulo sin el terminal instalado.
    """
    try:
        from market_data_mcp import mt5_client
    except ImportError as exc:  # pragma: no cover - depende del entorno
        raise SerieError(
            "No se pudo importar market_data_mcp. Ejecuta desde la raíz del repo "
            f"con `uv run`. (detalle: {exc})"
        ) from exc

    mt5_client.connect()
    df = mt5_client.get_rates(ticker, timeframe, n_velas)
    if df is None or len(df) == 0:
        raise SerieError(
            f"MT5 no devolvió velas para {ticker} en {timeframe}. Verifica que el "
            "terminal esté abierto y que el símbolo exista en el catálogo."
        )
    cierres = [float(v) for v in df["close"].tolist()]
    tiempos = list(df["time"]) if "time" in df.columns else []
    return cierres, tiempos


def _indice_hito(serie: list[float], tiempos: list, hito: dict) -> int:
    """En qué vela se ancla un hito sobre el eje X.

    Por proximidad de precio NO sirve como regla general, y es un error que se
    ve en el gráfico: el precio oscila, así que el cierre más parecido a "el
    precio de ahora" puede caer en cualquier punto de la serie. En la primera
    prueba el marcador AHORA se dibujó en la vela 8 de 60.

    El criterio correcto depende de qué es el hito:

    · `actual` -> siempre la última vela. "Ahora" es el extremo derecho por
      definición, no el cierre que más se le parece.
    · `meta`   -> también la última: un objetivo que todavía no se toca se lee
      proyectado hacia adelante, no en un punto del pasado donde el precio pasó
      por ahí de casualidad.
    · `origen` / `cumplido` -> ocurrieron en un momento concreto. Si el hito
      trae `fecha`, se ancla por TIEMPO, que es el dato verdadero. Sin fecha se
      cae a proximidad de precio, que es una aproximación aceptable para un
      nivel que efectivamente se tocó.
    """
    clase = hito.get("clase", "actual")
    if clase in ("actual", "meta"):
        return len(serie) - 1

    fecha = hito.get("fecha")
    if fecha and tiempos:
        import pandas as pd

        objetivo = pd.Timestamp(fecha)
        return min(range(len(tiempos)), key=lambda i: abs(tiempos[i] - objetivo))

    precio = float(hito["precio"])
    return min(range(len(serie)), key=lambda i: abs(serie[i] - precio))


def construir_recorrido(serie: list[float], hitos: list[dict], tiempos: list | None = None) -> dict:
    """Marcadores listos para `story_grafico.py`, uno por hito.

    La `etiqueta` viaja junto al hito y NO se recalcula acá: es el precio ya
    formateado con los `digits` del activo, coma decimal y punto de miles (regla
    de formato de precios del proyecto). Si se descarta, `story_grafico.py` cae
    a `str(precio)` y el gráfico publica el precio crudo de MT5 —`512.3` donde
    correspondía `512,30`—, que es exactamente lo que la regla prohíbe. Pasó en
    una pieza real de `/story recomendacion`.
    """
    marcadores = [
        {
            "indice": _indice_hito(serie, tiempos or [], h),
            "precio": float(h["precio"]),
            "clase": h.get("clase", "actual"),
            **({"rol": h["rol"]} if h.get("rol") else {}),
            **({"etiqueta": h["etiqueta"]} if h.get("etiqueta") else {}),
        }
        for h in hitos
    ]
    return {"serie": serie, "marcadores": marcadores}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticker", required=True, help="símbolo MT5 del catálogo")
    parser.add_argument("--timeframe", default="H1", choices=_TIMEFRAMES)
    parser.add_argument(
        "--velas",
        type=int,
        default=60,
        help="cuántas velas traer (60 por defecto: suficiente para que se lea la "
        "forma sin que la línea se convierta en ruido)",
    )
    args = parser.parse_args(argv)

    payload = json.load(sys.stdin)
    try:
        serie, tiempos = obtener_serie(args.ticker, args.timeframe, args.velas)
    except SerieError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    hitos = payload.pop("hitos", [])
    # Los `niveles` -entrada, objetivo, stop, soportes- no se anclan a una vela:
    # son precios que valen para toda la ventana, así que pasan derecho al
    # recorrido sin buscarles índice.
    niveles = payload.pop("niveles", [])
    recorrido = construir_recorrido(serie, hitos, tiempos)
    if niveles:
        recorrido["niveles"] = niveles
    payload["recorrido"] = recorrido
    json.dump(payload, sys.stdout, ensure_ascii=False)
    print(
        f"serie {args.ticker} {args.timeframe}: {len(serie)} velas, "
        f"{min(serie):.5f} - {max(serie):.5f}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
