#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fecha cuándo ocurrió cada régimen macro, corriendo el motor sobre la historia.

**Por qué existe.** El manual enseña los cinco climas de mercado con sus
umbrales, y un miembro razonablemente pregunta cuándo pasó cada uno. Escribir
esos ejemplos de memoria sería inventar la historia con aspecto institucional,
que es exactamente lo que el proyecto prohíbe. Así que se derivan: se corre el
**mismo clasificador que usa el motor** día por día sobre las series reales.

**No reimplementa la clasificación.** Importa `evaluar_regimen_candidato` y
`aplicar_histeresis` de `macro_bias_engine`, con su misma configuración. Una
segunda implementación de los umbrales sería un tercer lugar donde viven, y el
manual ya es el tercero: el defecto recurrente del repo.

**De dónde salen los datos.** De los dos archivos de relleno histórico
(`curva_fred_historico.json` y `commodities_historico.json`), que traen las
mismas series y las mismas fuentes que la ingesta diaria, solo que completas.
El límite es la tasa real TIPS (`DFII10`), que en FRED empieza el 2003-01-02.

**Cómo replica lo que el motor veía cada día.** El motor calcula sus deltas
sobre "los últimos 5 registros disponibles" de cada serie, no sobre días de
calendario, y cada serie tiene su propio último dato. Así que para la fecha D se
recorta cada serie a las observaciones anteriores o iguales a D y se aplica la
misma función. Mirar el dato de mañana para clasificar el ayer sería el
anacronismo que el proyecto persigue en los textos, cometido con números.

Uso:
    uv run python scripts/regimenes_historicos.py
    uv run python scripts/regimenes_historicos.py --desde 2015-01-01 --min-dias 3
"""

from __future__ import annotations

import argparse
import json
import sys
from bisect import bisect_right
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from macro_bias_engine import (  # noqa: E402
    _delta_n_dias,
    _obtener_serie_cronologica,
    _shock_petroleo_con_signo,
    aplicar_histeresis,
    cargar_config,
    evaluar_regimen_candidato,
)

CURVA_HIST = RAIZ / "data central" / "DATA USA" / "raw" / "curva_fred_historico.json"
COMM_HIST = RAIZ / "data central" / "DATA ORO Y COMMODITIES" / "raw" / "commodities_historico.json"
OHLC = RAIZ / "data central" / "DATA PRECIOS OHLC"
SALIDA = RAIZ / "data" / "regimenes_historicos.json"

# El activo con el que se ilustra cada clima. Se lee del terminal (MT5), que es
# la fuente de precios del proyecto.
ACTIVOS_ILUSTRACION = ("XAUUSD", "USDCLP", "WTI", "US100", "COPPER")


def _serie_desde(archivo: Path, ruta: tuple[str, ...], clave: str) -> list[tuple[str, float]]:
    """Devuelve [(fecha, valor)] cronológico de una serie de los archivos históricos."""
    if not archivo.exists():
        raise SystemExit(
            f"Falta {archivo.name}. Generalo con:\n"
            f"  uv run python .agents/skills/ecosistema-datos-macro/scripts/"
            f"{'extractor_usa.py' if 'USA' in str(archivo) else 'extractor_commodities.py'} --historico"
        )
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    nodo = datos
    for paso in ruta:
        nodo = nodo.get(paso, {})
    return _obtener_serie_cronologica(nodo.get(clave, {}).get("historico", {}))


def _hasta(serie: list[tuple[str, float]], fecha: str) -> list[tuple[str, float]]:
    """Recorta la serie a lo que se conocía en `fecha`, esa fecha incluida."""
    corte = bisect_right([f for f, _ in serie], fecha)
    return serie[:corte]


def _cierres_mt5(symbol: str) -> list[tuple[str, float]]:
    archivo = OHLC / f"{symbol}_D1.json"
    if not archivo.exists():
        return []
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    return [(r["time"][:10], float(r["close"])) for r in datos.get("rows", [])]


def _variacion(serie: list[tuple[str, float]], inicio: str, fin: str) -> float | None:
    """Variación porcentual del cierre entre dos fechas, con los datos que haya."""
    dentro = [v for f, v in serie if inicio <= f <= fin]
    if len(dentro) < 2 or dentro[0] == 0:
        return None
    return round((dentro[-1] - dentro[0]) / dentro[0] * 100.0, 2)


def construir_deltas(series: dict, fecha: str) -> dict:
    """Arma el payload de deltas tal como lo arma el motor, pero al cierre de `fecha`."""
    def d5(nombre: str) -> tuple[float | None, float | None]:
        abs_, pct, _ = _delta_n_dias(_hasta(series[nombre], fecha), 5)
        return abs_, pct

    dgs10_diff, _ = d5("DGS10")
    dgs2_diff, _ = d5("DGS2")
    tips_diff, _ = d5("DFII10")
    breakeven_diff, _ = d5("T10YIE")
    _, wti_pct = d5("PETROLEO_WTI")
    _, brent_pct = d5("PETROLEO_BRENT")
    _, copper_pct = d5("COBRE_COMEX")

    oil_max, oil_signed = _shock_petroleo_con_signo(wti_pct, brent_pct)

    dgs10 = _hasta(series["DGS10"], fecha)
    dgs2 = _hasta(series["DGS2"], fecha)
    tips = _hasta(series["DFII10"], fecha)
    dgs10_actual = dgs10[-1][1] if dgs10 else None
    dgs2_actual = dgs2[-1][1] if dgs2 else None

    return {
        "dgs10_actual": dgs10_actual,
        "dgs10_diff_5d": dgs10_diff,
        "us10y_diff_5d": dgs10_diff,
        "dgs2_diff_5d": dgs2_diff,
        "spread_2s10s_actual": (
            dgs10_actual - dgs2_actual
            if dgs10_actual is not None and dgs2_actual is not None
            else None
        ),
        "spread_2s10s_diff_5d": (
            dgs10_diff - dgs2_diff
            if dgs10_diff is not None and dgs2_diff is not None
            else None
        ),
        "tips10y_diff_5d": tips_diff,
        "breakeven_diff_5d": breakeven_diff,
        "oil_max_pct_5d": oil_max,
        "oil_signed_pct_5d": oil_signed,
        "copper_pct_5d": copper_pct,
        "tips_10y": tips[-1][1] if tips else None,
    }


def recorrer(desde: str, hasta: str | None) -> list[dict]:
    """Clasifica cada día hábil y devuelve la lista de días con su régimen."""
    cfg = cargar_config()

    series = {
        "DGS2": _serie_desde(CURVA_HIST, ("series",), "DGS2"),
        "DGS10": _serie_desde(CURVA_HIST, ("series",), "DGS10"),
        "DFII10": _serie_desde(CURVA_HIST, ("series",), "DFII10"),
        "T10YIE": _serie_desde(CURVA_HIST, ("series",), "T10YIE"),
        "PETROLEO_WTI": _serie_desde(COMM_HIST, ("commodities",), "PETROLEO_WTI"),
        "PETROLEO_BRENT": _serie_desde(COMM_HIST, ("commodities",), "PETROLEO_BRENT"),
        "COBRE_COMEX": _serie_desde(COMM_HIST, ("commodities",), "COBRE_COMEX"),
    }

    # El eje de fechas es el del cobre, que es el driver que aparece en tres de
    # los cinco regímenes y cotiza los días hábiles de EE.UU.
    fechas = [f for f, _ in series["COBRE_COMEX"] if f >= desde and (hasta is None or f <= hasta)]

    dias: list[dict] = []
    estado = None
    for fecha in fechas:
        deltas = construir_deltas(series, fecha)
        # Sin tasa real no hay clasificación honesta: es el driver que separa
        # estanflación de shock inflacionario y de Goldilocks.
        if deltas["tips10y_diff_5d"] is None or deltas["copper_pct_5d"] is None:
            continue
        cod, nom, extremo, desc = evaluar_regimen_candidato(deltas, cfg)
        estado = aplicar_histeresis(estado, cod, nom, extremo, desc, cfg)
        dias.append({
            "fecha": fecha,
            "candidato": cod,
            "regimen": estado["codigo"],
            "confirmado": estado["confirmado_por_historesis"],
            "extremo": extremo,
            "deltas": deltas,
        })
    return dias


def agrupar_episodios(dias: list[dict], min_dias: int) -> list[dict]:
    """Junta los días consecutivos del mismo régimen confirmado en episodios."""
    ilustracion = {s: _cierres_mt5(s) for s in ACTIVOS_ILUSTRACION}

    episodios: list[dict] = []
    actual: dict | None = None
    for dia in dias:
        if not dia["confirmado"]:
            continue
        if actual and dia["regimen"] == actual["regimen"]:
            actual["fin"] = dia["fecha"]
            actual["dias"] += 1
            continue
        if actual and actual["dias"] >= min_dias:
            episodios.append(actual)
        actual = {
            "regimen": dia["regimen"],
            "inicio": dia["fecha"],
            "fin": dia["fecha"],
            "dias": 1,
            "extremo": dia["extremo"],
            "deltas_inicio": {
                k: (round(v, 3) if isinstance(v, float) else v)
                for k, v in dia["deltas"].items()
            },
        }
    if actual and actual["dias"] >= min_dias:
        episodios.append(actual)

    for ep in episodios:
        ep["variacion_activos_pct"] = {
            s: _variacion(serie, ep["inicio"], ep["fin"])
            for s, serie in ilustracion.items()
        }
    return episodios


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--desde", default="2003-01-02", help="primera fecha a clasificar")
    ap.add_argument("--hasta", default=None, help="última fecha a clasificar")
    ap.add_argument("--min-dias", type=int, default=3, help="duración mínima de un episodio")
    args = ap.parse_args()

    dias = recorrer(args.desde, args.hasta)
    if not dias:
        print("Sin días clasificables: revisá que existan los dos archivos históricos.")
        return 1

    episodios = agrupar_episodios(dias, args.min_dias)

    conteo: dict[str, int] = {}
    for dia in dias:
        conteo[dia["regimen"]] = conteo.get(dia["regimen"], 0) + 1

    print(f"Clasificados {len(dias)} días hábiles, de {dias[0]['fecha']} a {dias[-1]['fecha']}\n")
    print(f"{'Régimen':<28}{'días':>7}{'% del tiempo':>14}{'episodios':>11}{'el más largo':>14}")
    for cod in sorted(conteo, key=lambda c: -conteo[c]):
        del_reg = [e for e in episodios if e["regimen"] == cod]
        largo = max((e["dias"] for e in del_reg), default=0)
        print(f"{cod:<28}{conteo[cod]:>7}{conteo[cod] / len(dias) * 100:>13.1f}%"
              f"{len(del_reg):>11}{largo:>12} d")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(
        json.dumps(
            {
                "generado_desde": dias[0]["fecha"],
                "generado_hasta": dias[-1]["fecha"],
                "dias_clasificados": len(dias),
                "min_dias_episodio": args.min_dias,
                "conteo_dias_por_regimen": conteo,
                "episodios": episodios,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n{len(episodios)} episodios -> {SALIDA.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
