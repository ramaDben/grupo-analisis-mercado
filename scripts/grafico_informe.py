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

── El calentamiento de las medias ───────────────────────────────────────────
Se piden más velas de las que se dibujan. Una EMA de 100 calculada sobre 100
velas arranca pegada al primer cierre y tarda decenas de barras en valer algo;
si se dibujara desde el borde izquierdo, el cliente vería una curva que sube
porque el indicador se está estabilizando, no porque el precio se mueva. Se
calcula sobre toda la ventana traída y se recorta al final.

── Escala del lienzo ────────────────────────────────────────────────────────
7,2 × 2,5 pulgadas a 300 DPI, que es la calibración del motor editorial de la
skill: el CSS del PDF impone `max-height: 240px` y con esa proporción la imagen
llega justo al tope. Cambiarla hace que `object-fit: contain` deje franjas
vacías arriba y abajo.
"""
from __future__ import annotations

import argparse
import json
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
        "ema_corta": "#E76F51",
        "ema_larga": "#53C1AB",
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
        "ema_corta": "#E76F51",
        "ema_larga": "#53C1AB",
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
EMA_CORTA = 50
EMA_LARGA = 100


def formatear_precio(valor: float, digits: int) -> str:
    """Precio en notación chilena, con los decimales que manda el catálogo.

    La regla de decimales del proyecto es del catálogo y no del gusto de quien
    dibuja: USD/CLP va a 2 y WTI a 3. Truncar un cero final cambia el número a
    la vista del cliente.
    """
    return f"{valor:,.{digits}f}".replace(",", "@").replace(".", ",").replace("@", ".")


def _ema(valores: list[float], span: int) -> list[float]:
    """EMA sin pandas: el mismo recurrente que usa `ewm(adjust=False)`."""
    k = 2.0 / (span + 1.0)
    salida: list[float] = []
    prom = valores[0]
    for v in valores:
        prom = v * k + prom * (1.0 - k)
        salida.append(prom)
    return salida


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
) -> Path:
    """Dibuja el activo y devuelve la ruta del PNG. Lanza `GraficoError` si no hay datos."""
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

    # Se traen las velas dibujadas más el calentamiento de la media larga.
    n_total = VELAS_DIBUJADAS + EMA_LARGA * 3
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

    ema_c = _ema(cierres, EMA_CORTA)
    ema_l = _ema(cierres, EMA_LARGA)

    corte = max(0, len(cierres) - VELAS_DIBUJADAS)
    x = list(tiempos[corte:]) if tiempos else list(range(len(cierres) - corte))
    y = cierres[corte:]

    fig, ax = plt.subplots(figsize=(7.2, 2.5), dpi=300)
    fig.patch.set_facecolor(c["fondo"])
    ax.set_facecolor(c["fondo"])
    ax.grid(True, linestyle="--", linewidth=0.6, color=c["grilla"], alpha=0.9)
    for spine in ax.spines.values():
        spine.set_color(c["borde"])
        spine.set_linewidth(0.7)
    ax.tick_params(colors=c["tenue"], labelsize=8)

    ax.plot(x, y, color=c["precio"], linewidth=2.0,
            label=f"{nombre} · cierre {timeframe}", zorder=5)

    # Una media solo se dibuja si tuvo espacio real para estabilizarse. Dibujar
    # una EMA 100 sobre 40 velas es mostrar el transitorio del indicador.
    for span, color, estilo, etiqueta in (
        (EMA_CORTA, c["ema_corta"], "--", f"Media de {EMA_CORTA} días"),
        (EMA_LARGA, c["ema_larga"], "-", f"Media de {EMA_LARGA} días"),
    ):
        if corte >= span:
            serie = (ema_c if span == EMA_CORTA else ema_l)[corte:]
            ax.plot(
                x, serie, color=color, linewidth=1.6, linestyle=estilo,
                label=f"{etiqueta} ({formatear_precio(serie[-1], digits)})", zorder=4,
            )

    niveles = niveles or {}
    for clave, color, rotulo in (
        ("r1", c["resistencia"], "Resistencia"),
        ("s1", c["soporte"], "Soporte"),
    ):
        nivel = niveles.get(clave)
        if not isinstance(nivel, (int, float)):
            continue
        # El rotulo va a la leyenda y no flotando sobre la linea. Una etiqueta
        # suelta se cruza con la leyenda apenas el nivel queda cerca del precio,
        # que es justo cuando el nivel importa: en USD/CLP la resistencia quedaba
        # ilegible detras del recuadro. `loc="best"` no lo evita porque solo
        # considera lineas y parches, no anotaciones.
        ax.axhline(
            float(nivel), color=color, linestyle=":", linewidth=1.3, alpha=0.95,
            zorder=3, label=f"{rotulo} {formatear_precio(float(nivel), digits)}",
        )

    actual = float(niveles.get("price") or y[-1])
    ax.scatter([x[-1]], [y[-1]], s=26, color=c["ema_larga"], zorder=7,
               edgecolors=c["fondo"], linewidths=0.8)
    ax.annotate(
        f"Ahora: {formatear_precio(actual, digits)}",
        xy=(x[-1], y[-1]), xytext=(-6, 14), textcoords="offset points",
        fontsize=7.5, fontweight="bold", color=c["texto"], ha="right",
        bbox=dict(boxstyle="round,pad=0.28", fc=c["globo_fondo"],
                  ec=c["ema_larga"], lw=0.9),
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
        # El subtitulo llega del sesgo del Playbook y su largo no esta acotado:
        # "acompañado por el buen momento de la economia" se salia del lienzo y
        # matplotlib lo recortaba a media palabra, sin avisar. Se envuelve a dos
        # lineas como maximo; mas alto de titulo se come el grafico, que es lo
        # que la pieza vino a mostrar.
        lineas = textwrap.wrap(subtitulo, width=ANCHO_SUBTITULO, max_lines=2,
                               placeholder="…")
        titulo += "\n" + "\n".join(lineas)
    ax.set_title(titulo, fontsize=9.5, fontweight="bold", color=c["texto"],
                 pad=7, loc="left")
    leg = ax.legend(loc="best", frameon=True, facecolor=c["fondo"],
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
    p.add_argument("--niveles", default="", help="JSON con price/s1/r1 (opcional)")
    a = p.parse_args(argv)

    niveles = json.loads(a.niveles) if a.niveles else None
    try:
        ruta = construir_grafico(
            a.ticker, a.nombre or a.ticker, Path(a.out),
            timeframe=a.timeframe, tema=a.tema, subtitulo=a.subtitulo,
            niveles=niveles,
        )
    except GraficoError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print(f"[OK] {ruta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
