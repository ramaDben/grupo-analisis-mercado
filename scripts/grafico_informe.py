#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Gráfico de un activo para el informe de la jornada, con datos reales de MT5.

Existe para que el informe de apertura deje de ser tres tablas seguidas: el
cliente reconoce una tendencia en un gráfico mucho antes que en una fila de
cifras, y el PDF gana el atractivo que el director pidió.

── Por qué no reusa `generar_graficos_drivers.py` ────────────────────────────
Ese script tiene las series escritas a mano (`yield_10y = [4.45, 4.48, ...]`,
`brent = [84.5, ...]`). Producen una imagen de aspecto institucional a partir de
números que nadie midió. Un gráfico miente más fuerte que una tabla, porque el
lector no audita una pendiente: la cree. Acá cada punto sale de
`serie_mt5.obtener_serie`, que lee el terminal, y si el terminal no responde el
script se detiene en vez de dibujar algo plausible.

── Solo la lectura, nunca otra ──────────────────────────────────────────────
Las horizontales del banner son las de la `Lectura` de la estrategia, que son
las que nombra el texto. Hasta el 2026-10-12 el motor dibujaba además las EMA
50 y 100 y, sin lectura, los pivotes crudos (R1, S1, Fibo 50 %): dos lecturas
técnicas en la misma imagen, que el cliente no tiene cómo reconciliar.

── Escala del lienzo ────────────────────────────────────────────────────────
7,2 × 2,5 pulgadas a 300 DPI, que es la calibración del motor editorial de la
skill: el CSS del PDF impone `max-height: 240px` y con esa proporción la imagen
llega justo al tope. Cambiarla hace que `object-fit: contain` deje franjas
vacías arriba y abajo.
"""
from __future__ import annotations

import argparse
import sys
import textwrap
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # nosec B110 - consola sin soporte: se sigue igual
        pass


class GraficoError(RuntimeError):
    """El gráfico no se pudo construir. Nunca se dibuja un sustituto."""


# ── Temas ────────────────────────────────────────────────────────────────────
# El cuerpo del PDF es blanco (`body { background: #FFFFFF }`), así que el tema
# claro es el que se ve nativo dentro del informe. El oscuro reproduce la pieza
# suelta y sirve para adjuntar el gráfico a un mensaje.
#
# La paleta clara es la del motor editorial de la skill, no la de `marca.css`.
# Son distintas (#53C1AB vs #50C0A8) y unificarlas cambia cómo se ven los
# informes que el director aprobó: es un Change aparte, con su visto bueno.
TEMAS: dict[str, dict[str, str]] = {
    "claro": {
        "fondo": "#FFFFFF",
        "texto": "#0D0D1A",
        "precio": "#0D0D1A",
        "acento": "#53C1AB",
        "resistencia": "#E76F51",
        "soporte": "#3E91AF",
        "grilla": "#E9ECEF",
        "borde": "#D0D7DE",
        "tenue": "#737373",
        "globo_fondo": "#F8FAF9",
    },
    "oscuro": {
        "fondo": "#12121F",
        "texto": "#F5F3F7",
        "precio": "#FFFFFF",
        "acento": "#53C1AB",
        "resistencia": "#E76F51",
        "soporte": "#3E91AF",
        "grilla": "#2A2A3C",
        "borde": "#3A3A4E",
        "tenue": "#A9A5B4",
        "globo_fondo": "#1C1C2E",
    },
}

VELAS_DIBUJADAS = 90
# Caracteres que entran en una linea de subtitulo a 9,5 pt sobre 7,2 pulgadas.
# Medido sobre el caso que se cortaba (Nasdaq, 88 caracteres), no estimado.
ANCHO_SUBTITULO = 78


def formatear_precio(valor: float, digits: int) -> str:
    """Precio en notación chilena, con los decimales que manda el catálogo.

    La regla de decimales del proyecto es del catálogo y no del gusto de quien
    dibuja: USD/CLP va a 2 y WTI a 3. Truncar un cero final cambia el número a
    la vista del cliente.

    **Con `digits = 0` no va separador de miles.** Ese caso es solo el Cobre, y
    `CLAUDE.md` lo lista entero (`$14197 USD/t`) marcando `$14.197` como
    incorrecto: sin decimales, el punto de millar se confunde con el decimal
    inglés, y el mismo metal cotiza también en USD/libra con 4 decimales
    (6,602). Ahí un `$14.197` mal leído es un error de dos órdenes de magnitud.
    """
    if digits == 0:
        return f"{valor:.0f}"
    return f"{valor:,.{digits}f}".replace(",", "@").replace(".", ",").replace("@", ".")


_COLOR_ROL = {"soporte": "soporte", "resistencia": "resistencia", "nivel": "acento"}


def lineas_de_nivel(horizontales: list[tuple[float, str, str]] | None
                    ) -> list[tuple[float, str, str, str]]:
    """Las horizontales del banner: (precio, clave de color del tema, estilo, rótulo).

    Son los niveles de la lectura, que son los que nombra el texto. Sin lectura no hay
    horizontales: los pivotes crudos serían una segunda lectura en la imagen.
    """
    return [(float(p), _COLOR_ROL.get(rol, "acento"), "--" if rol == "nivel" else ":", rotulo)
            for p, rotulo, rol in horizontales or ()]


def construir_grafico(
    ticker: str,
    nombre: str,
    destino: Path,
    *,
    timeframe: str = "D1",
    tema: str = "claro",
    subtitulo: str = "",
    niveles: dict[str, Any] | None = None,
    digits: int | None = None,
    horizontales: list[tuple[float, str, str]] | None = None,
) -> Path:
    """Dibuja el activo y devuelve la ruta del PNG. Lanza `GraficoError` si no hay datos.

    `horizontales` son los niveles que nombra la lectura de la estrategia; `niveles` solo
    aporta `price`, el precio del globo "Ahora".
    """
    if tema not in TEMAS:
        raise GraficoError(f"Tema '{tema}' desconocido. Opciones: {sorted(TEMAS)}")
    c = TEMAS[tema]

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.dates as mdates
        import matplotlib.pyplot as plt
    except ImportError as exc:
        raise GraficoError(
            "matplotlib no está instalado. Es dependencia opcional del informe: "
            "`uv sync --extra informe`, o `uv run --with matplotlib`."
        ) from exc

    from serie_mt5 import SerieError, obtener_serie

    n_total = VELAS_DIBUJADAS
    try:
        cierres, tiempos = obtener_serie(ticker, timeframe, n_total)
    except SerieError as exc:
        raise GraficoError(str(exc)) from exc
    if len(cierres) < 20:
        raise GraficoError(
            f"{ticker}: MT5 devolvió {len(cierres)} velas, insuficientes para un gráfico."
        )

    if digits is None:
        from market_data_mcp.catalog import VALID_TICKERS
        digits = VALID_TICKERS.get(ticker, 2)

    corte = max(0, len(cierres) - VELAS_DIBUJADAS)
    x = list(tiempos[corte:]) if tiempos else list(range(len(cierres) - corte))
    y = cierres[corte:]

    fig, ax = plt.subplots(figsize=(7.2, 2.82), dpi=300)
    fig.patch.set_facecolor(c["fondo"])
    ax.set_facecolor(c["fondo"])
    ax.grid(True, linestyle="--", linewidth=0.6, color=c["grilla"], alpha=0.9)
    for spine in ax.spines.values():
        spine.set_color(c["borde"])
        spine.set_linewidth(0.7)
    ax.tick_params(colors=c["tenue"], labelsize=8)

    ax.plot(x, y, color=c["precio"], linewidth=2.0,
            label=f"{nombre} · cierre {timeframe}", zorder=5)

    niveles = niveles or {}
    for nivel, clave_color, estilo, rotulo in lineas_de_nivel(horizontales):
        ax.axhline(
            nivel, color=c[clave_color], linestyle=estilo, linewidth=1.2, alpha=0.95,
            zorder=3, label=f"{rotulo} {formatear_precio(nivel, digits)}",
        )

    actual = float(niveles.get("price") or y[-1])
    ax.scatter([x[-1]], [y[-1]], s=26, color=c["acento"], zorder=7,
               edgecolors=c["fondo"], linewidths=0.8)
    ax.annotate(
        f"Ahora: {formatear_precio(actual, digits)}",
        xy=(x[-1], y[-1]), xytext=(-6, 14), textcoords="offset points",
        fontsize=7.5, fontweight="bold", color=c["texto"], ha="right",
        bbox=dict(boxstyle="round,pad=0.28", fc=c["globo_fondo"],
                  ec=c["acento"], lw=0.9),
        zorder=8,
    )

    # Aire vertical para que la leyenda quepa en el margen y no se apoye sobre
    # la linea de precio. `loc="best"` minimiza el solape pero no puede crear
    # espacio donde no lo hay: en un banner de 2,5 pulgadas siempre lo falta.
    ax.margins(y=0.16)

    if tiempos:
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=7))

    titulo = f"{nombre} · marco {'diario' if timeframe == 'D1' else timeframe}"
    if subtitulo:
        # El subtitulo llega de afuera y su largo no esta acotado:
        # "acompañado por el buen momento de la economia" se salia del lienzo y
        # matplotlib lo recortaba a media palabra, sin avisar. Se envuelve a dos
        # lineas como maximo; mas alto de titulo se come el grafico, que es lo
        # que la pieza vino a mostrar.
        lineas = textwrap.wrap(subtitulo, width=ANCHO_SUBTITULO, max_lines=2,
                               placeholder="…")
        titulo += "\n" + "\n".join(lineas)
    ax.set_title(titulo, fontsize=9.5, fontweight="bold", color=c["texto"],
                 pad=7, loc="left")
    leg = ax.legend(loc="lower left", frameon=True, facecolor=c["fondo"],
                    edgecolor=c["borde"], fontsize=7, framealpha=0.93,
                    ncol=2, columnspacing=1.1, handlelength=1.8)
    for t in leg.get_texts():
        t.set_color(c["texto"])

    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(destino, dpi=300, facecolor=c["fondo"])
    plt.close(fig)
    return destino


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ticker", required=True)
    p.add_argument("--nombre", default="")
    p.add_argument("--timeframe", default="D1")
    p.add_argument("--tema", default="claro", choices=sorted(TEMAS))
    p.add_argument("--subtitulo", default="")
    p.add_argument("--out", required=True)
    a = p.parse_args(argv)

    # Mismos niveles que el informe: los de la lectura de la estrategia activa.
    import pipeline_informe as pi
    from market_data_mcp.catalog import VALID_TICKERS
    from tradingview_grafico import leer_lectura

    try:
        lectura = leer_lectura(a.ticker, VALID_TICKERS.get(a.ticker, 2))
    except Exception as exc:  # noqa: BLE001
        print(f"[ERROR] {a.ticker}: sin la lectura de la estrategia ({exc})", file=sys.stderr)
        return 1
    try:
        ruta = construir_grafico(
            a.ticker, a.nombre or a.ticker, Path(a.out),
            timeframe=a.timeframe, tema=a.tema, subtitulo=a.subtitulo,
            niveles={"price": lectura.precio}, horizontales=pi._horizontales(lectura),
        )
    except GraficoError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print(f"[OK] {ruta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
