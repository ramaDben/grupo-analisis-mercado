"""Corre Tori sobre activos reales y deja un PNG por activo para el gate del director.

    uv run --extra informe --with MetaTrader5 python scripts/tori_revision.py
    uv run --extra informe --with MetaTrader5 python scripts/tori_revision.py --tickers XAUUSD USDCLP

Salida: data/charts/tori/<YYYY-MM-DD_HH-MM>/<slug>.png, más resumen.json con la
lectura, las métricas y el puntaje de cada activo en los dos horizontes. Es la
medición del universo real con que el director decide los umbrales (spec §5).
No envía nada ni lo consume ningún pipeline.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from estrategia import registro  # noqa: E402
from estrategia.fuente import velas_mt5  # noqa: E402

COLOR = {"accion": "#d62728", "seguridad": "#2ca02c", "seguimiento": "#98df8a",
         "contexto": "#9467bd", "objetivo": "#ff7f0e", "rango": "#7f7f7f"}
PROYECCION = 14  # la semirrecta, proyectada a la derecha (doctrina 2.1)


def _slug(ticker: str) -> str:
    return ticker.lower().replace(".spot", "").replace("#", "").replace("/", "")


def _panel(ax, df, lineas, titulo, ticker="") -> list[dict]:
    """Dibuja velas y líneas; devuelve las líneas que no se pudieron dibujar y por qué."""
    no_dibujadas: list[dict] = []
    indice = {int(t): i for i, t in enumerate(df["time"])}
    for i, fila in enumerate(df.itertuples()):
        color = "#2ca02c" if fila.close >= fila.open else "#d62728"
        ax.vlines(i, fila.low, fila.high, color=color, linewidth=0.6)
        ax.vlines(i, min(fila.open, fila.close), max(fila.open, fila.close), color=color, linewidth=2.5)
    fin = len(df) - 1 + PROYECCION
    for x in lineas:
        estilo = "--" if x.rol in ("contexto", "objetivo", "rango") else "-"
        if x.tipo == "diagonal":
            (t1, p1), (t2, p2) = x.puntos
            if t1 not in indice or t2 not in indice:
                motivo = "ancla fuera de la ventana de velas dibujada"
                print(f"{ticker} {x.marco}: {motivo}, diagonal {x.rol} no se dibuja")
                no_dibujadas.append({"marco": x.marco, "rol": x.rol, "motivo": motivo})
                continue
            i1, i2 = indice[t1], indice[t2]
            pend = (p2 - p1) / (i2 - i1)
            ax.plot([i1, fin], [p1, p1 + pend * (fin - i1)], estilo, color=COLOR[x.rol], linewidth=1.4,
                    label=f"{x.rol} {x.calidad} ({x.toques} toques)")
        else:
            ax.hlines(x.puntos[0][1], 0, fin, linestyles="dashed", colors=COLOR[x.rol], linewidth=1.0,
                      label=f"{x.rol} {x.valor_actual}")
    ax.set_title(titulo)
    ax.set_xlim(0, fin)
    minimo, maximo = float(df["low"].min()), float(df["high"].max())
    margen = (maximo - minimo) * 0.08 or abs(maximo) * 0.01
    ax.set_ylim(minimo - margen, maximo + margen)  # la proyeccion no aplasta las velas
    if ax.get_legend_handles_labels()[0]:
        ax.legend(loc="upper left", fontsize=7)
    return no_dibujadas


def dibujar(destino: Path, lectura, velas, marcos) -> list[dict]:
    """Un panel por marco: el operativo y los de contexto del menor al mayor (D1, W1).

    Cada panel muestra todas las velas que recibió la lectura de ese marco, así las anclas
    viejas de una diagonal de contexto quedan dentro. Devuelve las líneas que no se pudieron
    dibujar, para el resumen.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    op = marcos.operativo
    orden = (op, *reversed(marcos.contexto))
    fig, ejes = plt.subplots(len(orden), 1, figsize=(16, 5.5 * len(orden)),
                             gridspec_kw={"height_ratios": (3, *([2] * (len(orden) - 1)))})
    ejes = ejes if len(orden) > 1 else [ejes]
    no_dibujadas: list[dict] = []
    for ax, marco in zip(ejes, orden):
        titulo = (f"{lectura.ticker} {op} · {lectura.estado} · {lectura.direccion} · "
                  f"vigilar {lectura.vigilar.precio}" if marco == op else f"{lectura.ticker} {marco} · contexto")
        no_dibujadas += _panel(ax, velas[marco].reset_index(drop=True),
                               [x for x in lectura.lineas if x.marco == marco], titulo, lectura.ticker)
    for x in lectura.lineas:
        if x.marco not in orden:
            motivo = "marco sin panel"
            print(f"{lectura.ticker} {x.marco}: {motivo}, línea {x.rol} no se dibuja")
            no_dibujadas.append({"marco": x.marco, "rol": x.rol, "motivo": motivo})
    fig.tight_layout()
    fig.savefig(destino, dpi=110)
    plt.close(fig)
    return no_dibujadas


def main(argv: list[str] | None = None) -> int:
    from market_data_mcp.catalog import VALID_TICKERS
    from pipeline_informe import ACTIVOS_INFORME

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tickers", nargs="*", default=list(ACTIVOS_INFORME))
    args = ap.parse_args(argv)

    estrategia = registro.activa()
    sello = datetime.now(ZoneInfo("America/Santiago")).strftime("%Y-%m-%d_%H-%M-%S")
    carpeta = RAIZ / "data" / "charts" / "tori" / sello
    carpeta.mkdir(parents=True)  # sin exist_ok: una corrida nunca pisa a otra
    resumen: list[dict] = []
    fallas = 0
    for ticker in args.tickers:
        try:
            if ticker not in VALID_TICKERS:
                raise KeyError(f"{ticker} no esta en el catalogo: no se adivinan los decimales")
            velas, en_curso = velas_mt5(ticker, estrategia.marcos)
            lectura = estrategia.leer(ticker, velas, VALID_TICKERS[ticker], en_curso)
            sesion, semana = estrategia.puntuar(lectura, "sesion"), estrategia.puntuar(lectura, "semana")
            no_dibujadas = dibujar(carpeta / f"{_slug(ticker)}.png", lectura, velas, estrategia.marcos)
            resumen.append({
                "ticker": ticker, "estado": lectura.estado, "direccion": lectura.direccion,
                "precio": lectura.precio, "vigilar": lectura.vigilar.precio,
                "invalidacion": lectura.invalidacion.precio if lectura.invalidacion else None,
                "objetivo": lectura.objetivo.precio if lectura.objetivo else None,
                "metricas": lectura.metricas, "avisos": list(lectura.avisos),
                "lineas_no_dibujadas": no_dibujadas,
                "sesion": {"puntos": sesion.puntos, "excluido": sesion.excluido, "desglose": sesion.desglose},
                "semana": {"puntos": semana.puntos, "excluido": semana.excluido, "desglose": semana.desglose},
                "escenarios": [f"{e.flecha} {e.texto}" for e in lectura.escenarios],
            })
            print(f"{ticker:12} {lectura.estado:9} {lectura.direccion:8} "
                  f"sesion={sesion.puntos:5.1f} semana={semana.puntos:5.1f} "
                  f"dist_seg={lectura.metricas.get('dist_seguridad_atr_d1', float('nan')):.2f}")
        except Exception as exc:  # una falla no inventa velas ni detiene al resto
            fallas += 1
            resumen.append({"ticker": ticker, "error": f"{type(exc).__name__}: {exc}"})
            print(f"{ticker:12} ERROR {type(exc).__name__}: {exc}")
        (carpeta / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2),
                                              encoding="utf-8")
    print(f"PNG y resumen en {carpeta}")
    if fallas:
        print(f"{fallas} activo(s) fallaron")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
