"""Generador de la geometría del gráfico de recorrido para la Story `operacion`.

Traduce el recorrido real de un precio (una serie de valores más los hitos de la
operación) al SVG que la plantilla `templates/stories/operacion.html` inyecta en su
token `{{grafico}}`. Es un paso **previo** al render: enriquece el payload y lo deja
listo para `story_render.py`.

    cat operacion.json \
      | uv run python scripts/story_grafico_operacion.py \
      | uv run python scripts/story_render.py --template templates/stories/operacion.html \
          --out data/stories/... --formato vertical

Reparto de responsabilidades (mismo criterio que el resto del motor de Stories): acá
solo se calculan **coordenadas**; el color, el grosor y la tipografía viven en las
clases `.g-*` del snapshot. Por eso el SVG que se emite no lleva ni un atributo de
estilo -- si el gráfico se ve mal, se corrige en la plantilla, no acá.

Entrada (JSON por stdin): el payload de la Story más una clave `recorrido`:

    {
      "titular": "...",                    <- resto del payload, se pasa tal cual
      "recorrido": {
        "serie": [163.62, 163.80, ...],    <- precios, equiespaciados en X
        "marcadores": [
          {"indice": 6, "precio": 163.444, "clase": "origen", "rol": "ENTRADA"}
        ]
      }
    }

Salida (JSON por stdout): el mismo payload con `grafico` resuelto y `recorrido` fuera
(la plantilla no lo referencia y `build_context` lo ignoraría de todos modos).

`clase` corresponde a los estados que el snapshot sabe pintar -- `origen`,
`cumplido`, `meta`, `actual` -- y `rol` es opcional: se omite donde dos etiquetas
consecutivas quedarían demasiado juntas (el color del punto ya comunica el estado).
"""
from __future__ import annotations

import json
import sys
from typing import Any

# ---- Lienzo del SVG -----------------------------------------------------------
# El viewBox va al ratio del contenedor real (~1.10 en vertical, ~1.16 en horizontal).
# Un viewBox más ancho que su caja hace que `preserveAspectRatio` escale por el ancho
# y deje bandas vacías arriba y abajo: espacio que no comunica nada.
VB_W, VB_H = 440, 400
# `PLOT_X0` deja a la izquierda la columna de etiquetas de precio.
PLOT_X0, PLOT_X1 = 134, 424
PLOT_Y0, PLOT_Y1 = 30, 370
LABEL_X = 118          # etiquetas ancladas a la derecha, antes de la zona de trazado
GUIA_X = 126           # donde arranca la guía punteada hacia el marcador
MARGEN_ESCALA = 0.05   # aire vertical sobre el máximo y bajo el mínimo de la serie


class GraficoError(RuntimeError):
    """Error accionable del generador (nunca un traceback críptico)."""


def resolver_escala(serie: list[float]) -> tuple[float, float]:
    """Devuelve `(precio_max, precio_min)` del eje vertical.

    Se derivan de la serie con un margen proporcional al rango, de modo que la curva
    nunca toca los bordes del área de trazado. Una serie plana (rango 0) recibe un
    margen fijo para no dividir por cero más adelante.
    """
    if not serie:
        raise GraficoError("recorrido.serie está vacío: no hay nada que graficar.")
    alto, bajo = max(serie), min(serie)
    rango = alto - bajo
    margen = rango * MARGEN_ESCALA if rango else 0.1
    return alto + margen, bajo - margen


def construir_svg(
    serie: list[float], marcadores: list[dict[str, Any]]
) -> str:
    """Arma el SVG del recorrido: área, línea, guías, puntos y etiquetas.

    La X de la serie es equiespaciada entre `PLOT_X0` y `PLOT_X1`; la X de cada
    marcador sale de su `indice` en la serie y su Y del `precio` propio (que puede
    diferir del punto de la serie: el hito real de la operación manda sobre el
    muestreo del gráfico).
    """
    p_max, p_min = resolver_escala(serie)
    n = len(serie)

    def coord_y(precio: float) -> float:
        return PLOT_Y0 + (p_max - precio) / (p_max - p_min) * (PLOT_Y1 - PLOT_Y0)

    def coord_x(indice: float) -> float:
        if n == 1:
            return PLOT_X0
        return PLOT_X0 + indice / (n - 1) * (PLOT_X1 - PLOT_X0)

    pts = [(coord_x(i), coord_y(p)) for i, p in enumerate(serie)]
    trazo = " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)

    partes = [
        f'<svg viewBox="0 0 {VB_W} {VB_H}" preserveAspectRatio="xMidYMid meet">',
        '<defs><linearGradient id="gradArea" x1="0" y1="0" x2="0" y2="1">',
        '<stop offset="0%" stop-color="#F5A3A3" stop-opacity="0.20"/>',
        '<stop offset="100%" stop-color="#F5A3A3" stop-opacity="0"/>',
        "</linearGradient></defs>",
        f'<path class="g-area" d="M {pts[0][0]:.1f},{PLOT_Y1} L {trazo} '
        f'L {pts[-1][0]:.1f},{PLOT_Y1} Z"/>',
    ]

    # Las guías se dibujan ANTES de la línea para que nunca la tapen.
    for m in marcadores:
        y = coord_y(m["precio"])
        x = coord_x(m["indice"])
        partes.append(
            f'<line class="g-guia" x1="{GUIA_X}" y1="{y:.1f}" x2="{x:.1f}" y2="{y:.1f}"/>'
        )

    partes.append(f'<path class="g-linea" d="M {trazo}"/>')

    for m in marcadores:
        clase = m.get("clase", "actual")
        x, y = coord_x(m["indice"]), coord_y(m["precio"])
        if clase == "meta":
            partes.append(f'<circle class="g-halo" cx="{x:.1f}" cy="{y:.1f}" r="11"/>')
        partes.append(
            f'<circle class="g-punto g-punto-{clase}" cx="{x:.1f}" cy="{y:.1f}" r="5.5"/>'
        )
        partes.append(
            f'<text class="g-precio g-precio-{clase}" x="{LABEL_X}" y="{y + 6:.1f}" '
            f'text-anchor="end">{m["etiqueta"]}</text>'
        )
        if m.get("rol"):
            partes.append(
                f'<text class="g-rol" x="{LABEL_X}" y="{y + 21:.1f}" '
                f'text-anchor="end">{m["rol"]}</text>'
            )

    partes.append("</svg>")
    return "".join(partes)


def enriquecer(payload: dict[str, Any]) -> dict[str, Any]:
    """Reemplaza la clave `recorrido` del payload por el token `grafico` resuelto."""
    recorrido = payload.pop("recorrido", None)
    if not isinstance(recorrido, dict):
        raise GraficoError(
            "El payload no trae la clave 'recorrido' con {serie, marcadores}."
        )

    serie = recorrido.get("serie")
    if not isinstance(serie, list):
        raise GraficoError("recorrido.serie debe ser un array de precios.")

    marcadores = recorrido.get("marcadores") or []
    for m in marcadores:
        faltantes = {"indice", "precio"} - set(m)
        if faltantes:
            raise GraficoError(
                f"Marcador incompleto (faltan {sorted(faltantes)}): {m!r}"
            )
        if not 0 <= m["indice"] <= len(serie) - 1:
            raise GraficoError(
                f"indice {m['indice']} fuera de la serie (0..{len(serie) - 1})."
            )
        # La etiqueta visible respeta los `digits` del activo, así que la trae el
        # payload ya formateada; si falta, se cae al precio crudo.
        m.setdefault("etiqueta", str(m["precio"]))

    payload["grafico"] = construir_svg([float(p) for p in serie], marcadores)
    return payload


def main(argv: list[str] | None = None) -> int:
    """CLI: payload JSON por stdin, payload enriquecido por stdout."""
    try:
        # stdin no siempre es UTF-8 en Windows (usa la codepage de la consola):
        # leer bytes y decodificar explícito evita mojibake en tildes y ñ.
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8-sig"))
        salida = enriquecer(payload)
    except GraficoError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"Payload JSON inválido en stdin: {exc}", file=sys.stderr)
        return 1

    sys.stdout.buffer.write(
        (json.dumps(salida, ensure_ascii=False) + "\n").encode("utf-8")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
