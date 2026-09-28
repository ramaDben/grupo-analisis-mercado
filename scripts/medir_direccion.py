#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Medición histórica de la dirección de cuatro ejes contra la EMA 50 sola.

Fase 1 del spec `docs/superpowers/specs/2026-09-28-direccion-4-ejes-design.md`
(§5). Recorre las series de `data central/DATA PRECIOS OHLC/`, arma en cada vela
H1 los mismos dicts que entrega `analizar_activo` (indicadores de velas
cerradas, `rango_hoy` reconstruido sin fuga) y aplica la regla de adopción
fijada antes de ver los números.

**Las marcas son hora de Santiago aunque el sello diga UTC** (medido el
2026-09-28). La medición no deriva un desfase constante: interpreta cada marca
como `America/Santiago`, la convierte con `zoneinfo`, verifica la hipótesis con
dos pruebas y aborta si alguna falla.

Uso:
    uv run python scripts/medir_direccion.py
    uv run python scripts/medir_direccion.py --series XAUUSD USDCLP
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
SRC = RAIZ / "src"
for _p in (SRC, RAIZ / "scripts"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import agenda_mercado as agenda  # noqa: E402
import direccion_gi as dg  # noqa: E402
from guardrails.cuenta import cuenta_correcta  # noqa: E402
from market_data_mcp.mt5_client import adx, atr, ema  # noqa: E402

DIR_SERIES = RAIZ / "data central" / "DATA PRECIOS OHLC"
DIR_SALIDA = RAIZ / "docs" / "mediciones"
SANTIAGO = ZoneInfo("America/Santiago")
NY = ZoneInfo("America/New_York")
COLUMNAS = ["time", "open", "high", "low", "close", "tick_volume"]


class MedicionAbortada(RuntimeError):
    """La medición no puede seguir sin mentir: se detiene con el detalle."""


@lru_cache(maxsize=1)
def cfg_medicion() -> dict[str, Any]:
    return json.loads(dg.CONFIG.read_text(encoding="utf-8"))["medicion"]


def valor(clave: str) -> Any:
    return cfg_medicion()[clave]["valor"]


# ─────────────────────────────────────────────────────────────────────────────
# Carga y sellos
# ─────────────────────────────────────────────────────────────────────────────
def cargar_serie(simbolo: str, marco: str, directorio: Path = DIR_SERIES) -> tuple[pd.DataFrame, dict[str, Any]]:
    """La serie ordenada, o `MedicionAbortada` si no salió de MT5 y de la cuenta declarada."""
    ruta = directorio / f"{simbolo}_{marco}.json"
    if not ruta.exists():
        raise MedicionAbortada(f"falta {ruta.name}: corre el extractor antes de medir")
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    meta = {k: v for k, v in datos.items() if k != "rows"}
    if meta.get("source") != "MT5" or meta.get("broker") != "MT5":
        raise MedicionAbortada(
            f"{ruta.name}: la serie no salio de MT5 (source={meta.get('source')}, broker={meta.get('broker')})"
        )
    veredicto = cuenta_correcta(meta.get("cuenta"), ubicacion=ruta.name)
    if not veredicto.ok:
        raise MedicionAbortada(f"{ruta.name}: {veredicto.detalle}")
    df = pd.DataFrame(datos["rows"])[COLUMNAS]
    df["time"] = pd.to_datetime(df["time"])
    return df.sort_values("time", kind="stable").reset_index(drop=True), meta


# ─────────────────────────────────────────────────────────────────────────────
# Zona horaria (spec §5.4)
# ─────────────────────────────────────────────────────────────────────────────
def localizar(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega `time_ny` leyendo cada marca como hora de Santiago.

    Las horas ambiguas (la que se repite en abril) y las inexistentes (la que
    falta en septiembre) quedan en `NaT`: resolverlas por el orden de las filas
    sería suponer algo que el archivo no dice. Marca, no borra, para que los
    indicadores sigan viendo todas las velas.
    """
    out = df.copy()
    local = out["time"].dt.tz_localize(SANTIAGO, ambiguous="NaT", nonexistent="NaT")
    out["time_ny"] = local.dt.tz_convert(NY)
    return out


def prueba_hora_extraccion(df: pd.DataFrame, meta: dict[str, Any]) -> dict[str, Any]:
    """La última vela cae dentro de la hora de extracción, leída en Santiago.

    Solo aplica a las series cuyo mercado estaba abierto al extraer (última vela
    del mismo día que la extracción). Las demás no dicen nada de la zona.
    """
    extraccion = datetime.fromisoformat(meta["as_of_utc"]).astimezone(SANTIAGO).replace(tzinfo=None)
    ultima = pd.Timestamp(df["time"].iloc[-1]).to_pydatetime()
    if ultima.date() != extraccion.date():
        return {"aplica": False, "ok": None,
                "detalle": f"ultima vela {ultima:%Y-%m-%d %H:%M}, extraida {extraccion:%Y-%m-%d %H:%M}: mercado cerrado"}
    ok = ultima <= extraccion < ultima + timedelta(hours=1)
    return {"aplica": True, "ok": ok,
            "detalle": f"ultima vela {ultima:%H:%M}, extraccion {extraccion:%H:%M} (Santiago)"}


def prueba_moda_volumen(df_loc: pd.DataFrame) -> dict[str, Any]:
    """La moda mensual de la hora NY de la vela de mayor volumen es la misma todos los meses."""
    d = df_loc.dropna(subset=["time_ny"]).copy()
    d = d[d["time_ny"].dt.weekday < 5]
    d["dia"] = d["time_ny"].dt.date
    picos = d.loc[d.groupby("dia")["tick_volume"].idxmax()].copy()
    picos["mes"] = picos["time_ny"].dt.strftime("%Y-%m")
    picos["hora"] = picos["time_ny"].dt.hour
    horas = picos.groupby("mes")["hora"].agg(lambda s: int(s.mode().iloc[0]))
    ok = len(horas) > 0 and horas.nunique() == 1
    return {"ok": bool(ok), "hora": int(horas.iloc[0]) if ok else None,
            "horas_por_mes": {k: int(v) for k, v in horas.items()}}


def verificar_zona(cargadas: dict[str, tuple[pd.DataFrame, dict[str, Any]]], serie_moda: str) -> dict[str, Any]:
    """Las dos pruebas de §5.4. Aborta si alguna falla o si ninguna serie permite la primera."""
    extraccion = {s: prueba_hora_extraccion(df, meta) for s, (df, meta) in cargadas.items()}
    aplican = {s: r for s, r in extraccion.items() if r["aplica"]}
    if not aplican:
        raise MedicionAbortada("ninguna serie tenia el mercado abierto al extraer: no se puede verificar la zona")
    fallan = {s: r["detalle"] for s, r in aplican.items() if not r["ok"]}
    if fallan:
        raise MedicionAbortada(f"la ultima vela no cae en la hora de extraccion: {fallan}")
    if serie_moda not in cargadas:
        raise MedicionAbortada(f"falta {serie_moda} para la prueba de volumen")
    moda = prueba_moda_volumen(localizar(cargadas[serie_moda][0]))
    if not moda["ok"]:
        raise MedicionAbortada(f"la hora NY del pico de volumen de {serie_moda} cambia entre meses: {moda['horas_por_mes']}")
    return {"extraccion": extraccion, "moda_volumen": {serie_moda: moda}}


# ─────────────────────────────────────────────────────────────────────────────
# Indicadores en serie y punto en el tiempo (spec §5.2 y §5.3)
# ─────────────────────────────────────────────────────────────────────────────
def indicadores(df: pd.DataFrame) -> pd.DataFrame:
    """Los indicadores de `analizar_activo`, en cada fila, con las mismas funciones.

    `ema`, `atr` y `adx` son recursivas (`adjust=False`): se calculan una vez
    sobre la serie completa y se leen en la fila que corresponda, sin fuga. El
    Donchian no tiene versión en serie en `mt5_client`, y acá se calcula con la
    misma fórmula rodante. El valor de la fila `i` INCLUYE la vela `i`: quien lee
    el instante `t` tiene que tomar la fila `t-1`.

    Los períodos (50, 100, 14, 50) son los de `analisis.py` y no umbrales del
    árbol; el test de paridad los ata.
    """
    return pd.DataFrame({
        "ema_50": ema(df["close"], 50),
        "ema_100": ema(df["close"], 100),
        "atr_14": atr(df, 14),
        "adx_14": adx(df, 14),
        "donchian_50_high": df["high"].rolling(50).max(),
        "donchian_50_low": df["low"].rolling(50).min(),
    }, index=df.index)


def rango_hoy_intradia(h1: pd.DataFrame) -> pd.Series:
    """`max(high) - min(low)` de las velas H1 del mismo día de Santiago hasta la fila inclusive.

    Es lo que la vela D1 en curso habría mostrado a esa hora. Leer la vela D1 del
    día de `t` sería una fuga: ya contiene el día completo.
    """
    dia = h1["time"].dt.date
    return h1.groupby(dia)["high"].cummax() - h1.groupby(dia)["low"].cummin()


def indice_d1_cerrado(h1_time: pd.Series, d1_time: pd.Series) -> np.ndarray:
    """Para cada fila H1, la posición del último D1 con fecha anterior a la de esa fila.

    Se alinea por FECHA de Santiago, sin localizar la marca D1: la vela diaria
    del cambio de horario de septiembre está marcada a una medianoche que no
    existe, y localizarla la perdería.
    """
    fechas_d1 = d1_time.dt.normalize().to_numpy()
    fechas_h1 = h1_time.dt.normalize().to_numpy()
    return np.searchsorted(fechas_d1, fechas_h1, side="left") - 1


def dicts_en(
    i: int, h1: pd.DataFrame, ind_h1: pd.DataFrame, rango: pd.Series,
    d1: pd.DataFrame, ind_d1: pd.DataFrame, j: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Los dicts que `analizar_activo` habría entregado al cierre de la vela H1 `i`.

    Precio: cierre de `i`. Indicadores de H1: fila `i-1` (la última cerrada).
    Indicadores de D1: fila `j`, el último día cerrado antes del día de `i`.
    `rango_hoy`: reconstruido desde H1 hasta `i`, con `fecha_barra` = día de `i`.
    """
    precio = float(h1["close"].iat[i])
    fila_h1 = ind_h1.iloc[i - 1]
    fila_d1 = ind_d1.iloc[j]
    h1d = {"price": precio, **{c: float(fila_h1[c]) for c in ind_h1.columns}}
    d1d = {
        "price": precio,
        "ema_50": float(fila_d1["ema_50"]),
        "ema_100": float(fila_d1["ema_100"]),
        "atr_14": float(fila_d1["atr_14"]),
        "rango_hoy": float(rango.iat[i]),
        "fecha_barra": h1["time"].iat[i].date().isoformat(),
    }
    return h1d, d1d


# ─────────────────────────────────────────────────────────────────────────────
# Qué instantes votan (spec §5.5)
# ─────────────────────────────────────────────────────────────────────────────
def _minutos(hhmm: str) -> int:
    h, m = (int(x) for x in str(hhmm).split(":"))
    return h * 60 + m


def _a_la_hora(minutos: int) -> int:
    """Lleva una hora de la agenda a la última vela H1 cerrada a esa hora."""
    return minutos - minutos % 60


def ventana_votante(clase: str) -> tuple[int, int]:
    """Minutos NY del CIERRE de vela en que un instante de esta clase vota.

    Inicio: el momento del día de la clase (08:30 divisas, 10:00 índices), llevado
    a la vela cerrada. Fin: la última tanda (pre-cierre de las 16:45), igual.
    Ninguna hora se escribe acá: salen de `config/agenda_mercado.json`.
    """
    horas = [_minutos(m["hora"]) for m in agenda.momentos() if clase in m.get("clases", [])]
    if not horas:
        raise MedicionAbortada(f"la clase {clase!r} no tiene momento en config/agenda_mercado.json")
    fin = max(_minutos(t["hora_ny"]) for t in agenda.tandas().values())
    return _a_la_hora(min(horas)), _a_la_hora(fin)


def _cierre_bolsa(clase: str) -> int | None:
    c = cfg_medicion()["cierre_bolsa_ny"]
    return _minutos(c["valor"]) if clase in c["clases"] else None


def _fila_sin_lectura(i: int, t: pd.Timestamp, motivo: str) -> dict[str, Any]:
    return {"i": i, "t_ny": t, "dia": t.date().isoformat(), "en_sesion": False, "vota": False,
            "motivo": motivo, "h": 0, "m": float("nan"), "modelo": None, "conviccion": None,
            "fase": None, "ema50": None, "ema50_hist": None}


def lecturas(h1: pd.DataFrame, d1: pd.DataFrame, clase: str, tolerancia_hueco_h: int = 0) -> pd.DataFrame:
    """Una fila por instante H1 medible, en orden, con su lectura y su futuro.

    El horizonte son `h` velas, y por defecto tienen que ser contiguas: un hueco
    (una vela ausente, el fin de semana, la pausa diaria) lo invalida.
    `tolerancia_hueco_h` admite hasta esas horas de hueco, y la usa solo la
    corrida de sensibilidad.

    El modelo encadena `previa = lectura.eje2` a lo largo de la serie; la EMA 50
    con histéresis encadena su propio lado. La EMA 50 sin histéresis (`ema50`) es
    la que hoy sale al cliente.
    """
    h1 = localizar(h1)
    ind_h1, ind_d1 = indicadores(h1), indicadores(d1)
    rango = rango_hoy_intradia(h1)
    jd1 = indice_d1_cerrado(h1["time"], d1["time"])
    minimo = int(valor("min_velas_cerradas"))
    h_std, h_min = int(valor("horizonte_velas")), int(valor("horizonte_minimo"))
    ini, fin = ventana_votante(clase)
    cierre_bolsa = _cierre_bolsa(clase)
    t_ny = h1["time_ny"]
    close = h1["close"].to_numpy()
    atr_prev = ind_h1["atr_14"].shift(1).to_numpy()

    filas: list[dict[str, Any]] = []
    previa_modelo: str | None = None
    previa_ema: str | None = None
    # Las primeras `minimo` velas H1 son la ventana de arranque y no se cuentan.
    # Las horas ambiguas se cuentan aparte en `medir`, desde `localizar`.
    for i in range(minimo, len(h1)):
        if pd.isna(t_ny.iat[i]):
            continue
        j = int(jd1[i])
        if j + 1 < minimo:
            # Sin 150 días cerrados no hay marco diario (spec §6): no se mide, se cuenta.
            filas.append(_fila_sin_lectura(i, t_ny.iat[i], "sin_historia_d1"))
            continue
        h1d, d1d = dicts_en(i, h1, ind_h1, rango, d1, ind_d1, j)
        lec = dg.leer_direccion(h1d, d1d, previa_modelo, hoy=d1d["fecha_barra"])
        previa_modelo = lec.eje2
        ema_hist = dg.eje_dia(h1d, previa_ema)
        previa_ema = ema_hist

        cierre = t_ny.iat[i] + pd.Timedelta(hours=1)
        minuto = cierre.hour * 60 + cierre.minute
        en_sesion = cierre.weekday() < 5 and ini <= minuto <= fin
        h = h_std
        if en_sesion and cierre_bolsa is not None:
            h = min(h_std, (cierre_bolsa - minuto) // 60)
        motivo = None if en_sesion else "fuera_de_sesion"
        m = float("nan")
        if en_sesion and h < h_min:
            motivo = "horizonte_corto"
        elif i + h >= len(h1):
            motivo = motivo or "sin_futuro"
        else:
            destino = t_ny.iat[i + h]
            lapso = destino - t_ny.iat[i] if not pd.isna(destino) else None
            if lapso is None or not (pd.Timedelta(hours=h) <= lapso <= pd.Timedelta(hours=h + tolerancia_hueco_h)):
                motivo = motivo or "horizonte_con_hueco"
            elif atr_prev[i] > 0:
                m = (close[i + h] - close[i]) / atr_prev[i]
        filas.append({
            "i": i, "t_ny": t_ny.iat[i], "dia": t_ny.iat[i].date().isoformat(),
            "en_sesion": en_sesion, "vota": en_sesion and motivo is None and math.isfinite(m),
            "motivo": motivo, "h": h, "m": m,
            "modelo": lec.direccion, "conviccion": lec.conviccion, "fase": lec.fase,
            "ema50": dg.ALCISTA if h1d["price"] >= h1d["ema_50"] else dg.BAJISTA,
            "ema50_hist": ema_hist,
        })
    return pd.DataFrame(filas).set_index("i") if filas else pd.DataFrame()


# ─────────────────────────────────────────────────────────────────────────────
# Métricas (spec §5.6)
# ─────────────────────────────────────────────────────────────────────────────
def acierta(direccion: str, m: float) -> bool:
    return (direccion == dg.ALCISTA and m > 0) or (direccion == dg.BAJISTA and m < 0)


def contar_giros(direcciones) -> int:
    """Solo ALCISTA a BAJISTA o al revés, entre lecturas direccionales consecutivas."""
    giros, previa = 0, None
    for d in direcciones:
        if d == dg.LATERAL:
            continue
        if previa is not None and d != previa:
            giros += 1
        previa = d
    return giros


def ic_por_dia(por_dia: pd.DataFrame, f: Callable[[dict[str, float]], float]) -> tuple[float, float]:
    """Intervalo por bootstrap agrupado por día.

    `por_dia` tiene una fila por día con SUMAS (aciertos, conteos). Se remuestrean
    días enteros, porque las velas de un mismo día no son independientes y
    remuestrearlas sueltas achica el intervalo en falso.
    """
    rng = np.random.default_rng(int(valor("bootstrap_semilla")))
    matriz = por_dia.to_numpy(dtype=float)
    n = len(matriz)
    if n == 0:
        return (float("nan"), float("nan"))
    stats = []
    for _ in range(int(valor("bootstrap_iteraciones"))):
        suma = matriz[rng.integers(0, n, n)].sum(axis=0)
        v = f(dict(zip(por_dia.columns, suma)))
        if math.isfinite(v):
            stats.append(v)
    if not stats:
        return (float("nan"), float("nan"))
    alfa = (1 - float(valor("nivel_confianza"))) / 2
    lo, hi = np.quantile(stats, [alfa, 1 - alfa])
    return float(lo), float(hi)


def _div(a: float, b: float) -> float:
    return a / b if b else float("nan")


def resumir(lec: pd.DataFrame) -> dict[str, Any]:
    """Las cuatro condiciones medibles de §5.7 sobre los instantes que votan, en puntos."""
    v = lec[lec["vota"]].copy() if len(lec) else lec
    if not len(v):
        return {"n_votos": 0, "n_dias": 0}
    v["hit_modelo"] = [acierta(d, m) for d, m in zip(v["modelo"], v["m"])]
    v["hit_ema"] = [acierta(d, m) for d, m in zip(v["ema50"], v["m"])]
    v["dir"] = v["modelo"] != dg.LATERAL
    v["lat"] = ~v["dir"]
    por_dia = pd.DataFrame({
        "hm": (v["hit_modelo"] & v["dir"]).groupby(v["dia"]).sum(),
        "he_dir": (v["hit_ema"] & v["dir"]).groupby(v["dia"]).sum(),
        "n_dir": v["dir"].groupby(v["dia"]).sum(),
        "he_lat": (v["hit_ema"] & v["lat"]).groupby(v["dia"]).sum(),
        "n_lat": v["lat"].groupby(v["dia"]).sum(),
    }).astype(float)
    tot = por_dia.sum()

    def dif_c1(s):
        return 100 * _div(s["hm"] - s["he_dir"], s["n_dir"])

    def dif_c2(s):
        return 100 * (_div(s["he_lat"], s["n_lat"]) - _div(s["he_dir"], s["n_dir"]))

    absm = v["m"].abs()
    c4 = {}
    for conv in ("debil", "moderada", "fuerte"):
        sub = v[(v["conviccion"] == conv) & v["dir"]]
        c4[conv] = 100 * float(sub["hit_modelo"].mean()) if len(sub) else None
    return {
        "n_votos": int(len(v)), "n_dias": int(v["dia"].nunique()),
        "c1": {"acierto_modelo": 100 * _div(tot["hm"], tot["n_dir"]),
               "acierto_ema50": 100 * _div(tot["he_dir"], tot["n_dir"]),
               "diferencia": dif_c1(tot), "ic": ic_por_dia(por_dia, dif_c1)},
        "c2": {"n_lateral": int(tot["n_lat"]),
               "acierto_ema50_lateral": 100 * _div(tot["he_lat"], tot["n_lat"]),
               "acierto_ema50_resto": 100 * _div(tot["he_dir"], tot["n_dir"]),
               "diferencia": dif_c2(tot), "ic": ic_por_dia(por_dia, dif_c2),
               "mediana_m_lateral": float(absm[v["lat"]].median()) if tot["n_lat"] else None,
               "mediana_m_direccional": float(absm[v["dir"]].median())},
        "c3": {"giros_modelo_100": 100 * contar_giros(v["modelo"]) / len(v),
               "giros_ema50_100": 100 * contar_giros(v["ema50_hist"]) / len(v)},
        "c4": c4,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Regla de adopción (spec §5.7, fijada antes de ver números)
# ─────────────────────────────────────────────────────────────────────────────
def evaluar_adopcion(total: dict[str, Any], por_activo: dict[str, dict[str, Any]]) -> dict[str, Any]:
    tol = float(valor("tolerancia_acierto_pts"))
    umbral = float(valor("umbral_disidente_pts"))
    minimo = int(valor("min_instantes_voto"))
    c1 = bool(total.get("c1") and total["c1"]["ic"][0] >= -tol)
    c2d = total.get("c2") or {}
    med_l, med_d = c2d.get("mediana_m_lateral"), c2d.get("mediana_m_direccional")
    c2 = bool(c2d and math.isfinite(c2d["ic"][1]) and c2d["ic"][1] < 0
              and med_l is not None and med_d is not None and med_l < med_d)
    c3d = total.get("c3") or {}
    c3 = bool(c3d and c3d["giros_modelo_100"] < c3d["giros_ema50_100"])
    c4v = [(total.get("c4") or {}).get(k) for k in ("debil", "moderada", "fuerte")]
    c4 = bool(all(x is not None for x in c4v) and c4v[0] < c4v[1] < c4v[2])
    sin_voto = sorted(s for s, r in por_activo.items() if r.get("n_votos", 0) < minimo)
    disidentes = sorted(
        s for s, r in por_activo.items()
        if r.get("n_votos", 0) >= minimo and r["c1"]["diferencia"] < -umbral
    )
    return {"c1": c1, "c2": c2, "c3": c3, "c4": c4, "adopta": c1 and c2 and c3,
            "disidentes": disidentes, "sin_voto": sin_voto}


# ─────────────────────────────────────────────────────────────────────────────
# Orquestación
# ─────────────────────────────────────────────────────────────────────────────
def _series_a_cargar(series: list[str] | None) -> list[str]:
    """Las series a cargar: las pedidas más la de la prueba de zona, aunque no se mida."""
    elegidas = list(series or cfg_medicion()["series"])
    prueba = str(valor("serie_prueba_zona"))
    return elegidas + ([prueba] if prueba not in elegidas else [])


def _paridad_ema100(h1: pd.DataFrame) -> float:
    """Diferencia, en ATR de H1, entre la EMA 100 de la serie completa y la de una ventana de 300 velas.

    En vivo `analizar_activo` pide 300 velas y su EMA 100 arranca con menos
    historia. Se mide en vez de suponerla (spec §5.2).
    """
    completa = indicadores(h1).iloc[-2]
    ventana = indicadores(h1.tail(300).reset_index(drop=True)).iloc[-2]
    return abs(float(completa["ema_100"]) - float(ventana["ema_100"])) / float(completa["atr_14"])


def medir(series: list[str] | None = None, directorio: Path = DIR_SERIES) -> dict[str, Any]:
    medibles = list(series or cfg_medicion()["series"])
    h1s = {s: cargar_serie(s, "H1", directorio) for s in _series_a_cargar(series)}
    zona = verificar_zona(h1s, str(valor("serie_prueba_zona")))
    minimo_votos = int(valor("min_instantes_voto"))
    por_activo: dict[str, dict[str, Any]] = {}
    lecs: list[pd.DataFrame] = []
    for s in medibles:
        h1, _ = h1s[s]
        d1, _ = cargar_serie(s, "D1", directorio)
        lec = lecturas(h1, d1, cfg_medicion()["series"][s]["clase"])
        resumen = resumir(lec)
        descartes = {str(k): int(v) for k, v in lec["motivo"].value_counts().items()} if len(lec) else {}
        descartes["hora_ambigua"] = int(localizar(h1)["time_ny"].isna().sum())
        resumen["descartes"] = descartes
        fuera = lec[~lec["en_sesion"] & lec["m"].notna()].assign(vota=True) if len(lec) else lec
        resumen["fuera_de_sesion"] = resumir(fuera)
        resumen["paridad_ema100_atr"] = _paridad_ema100(h1)
        resumen["por_hora_ny"] = _por_hora(lec)
        por_activo[s] = resumen
        if resumen["n_votos"] >= minimo_votos:
            lecs.append(lec)
    total = resumir(pd.concat(lecs)) if lecs else {"n_votos": 0, "n_dias": 0}
    return {
        "generado": datetime.now(SANTIAGO).strftime("%Y-%m-%d %H:%M"),
        "zona": zona, "por_activo": por_activo, "total": total,
        "adopcion": evaluar_adopcion(total, por_activo),
        "sensibilidad_hueco": _sensibilidad_hueco(medibles, h1s, directorio),
    }


def _por_hora(lec: pd.DataFrame) -> dict[str, dict[str, int]]:
    """Por hora NY de cierre de vela, en sesion: cuantos votan y cuantos caen por hueco.

    Declara donde cae la muestra: la contiguidad estricta del horizonte descarta
    la tarde de los activos con pausa diaria, y el veredicto no puede leerse como
    si cubriera la sesion entera sin decirlo.
    """
    if not len(lec):
        return {}
    en = lec[lec["en_sesion"]]
    hora = (en["t_ny"] + pd.Timedelta(hours=1)).dt.strftime("%H:00")
    tabla = pd.DataFrame({"hora": hora, "vota": en["vota"].astype(bool),
                          "hueco": en["motivo"] == "horizonte_con_hueco"})
    agrupado = tabla.groupby("hora").agg(votan=("vota", "sum"), horizonte_con_hueco=("hueco", "sum"))
    return {h: {"votan": int(f.votan), "horizonte_con_hueco": int(f.horizonte_con_hueco)}
            for h, f in agrupado.iterrows()}


def _sensibilidad_hueco(medibles: list[str], h1s: dict[str, tuple[pd.DataFrame, dict[str, Any]]],
                        directorio: Path) -> dict[str, Any]:
    """El veredicto repetido tolerando huecos cortos en el horizonte. No decide nada."""
    tol = int(valor("sensibilidad_hueco_horas"))
    minimo_votos = int(valor("min_instantes_voto"))
    por_activo: dict[str, dict[str, Any]] = {}
    lecs: list[pd.DataFrame] = []
    for s in medibles:
        d1, _ = cargar_serie(s, "D1", directorio)
        lec = lecturas(h1s[s][0], d1, cfg_medicion()["series"][s]["clase"], tolerancia_hueco_h=tol)
        por_activo[s] = resumir(lec)
        if por_activo[s]["n_votos"] >= minimo_votos:
            lecs.append(lec)
    total = resumir(pd.concat(lecs)) if lecs else {"n_votos": 0, "n_dias": 0}
    return {"tolerancia_horas": tol, "n_votos": total["n_votos"],
            "adopcion": evaluar_adopcion(total, por_activo)}


# ─────────────────────────────────────────────────────────────────────────────
# Informe (spec §5.8)
# ─────────────────────────────────────────────────────────────────────────────
def _json(o: Any) -> Any:
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return str(o)


def _pct(x: Any) -> str:
    return "n/d" if x is None or (isinstance(x, float) and not math.isfinite(x)) else f"{x:.1f}"


def _ic(ic: Any) -> str:
    return f"[{_pct(ic[0])}, {_pct(ic[1])}]" if ic else "n/d"


def _si(ok: bool) -> str:
    return "cumple" if ok else "no cumple"


def escribir_informe(resultado: dict[str, Any], salida: Path) -> tuple[Path, Path]:
    salida.mkdir(parents=True, exist_ok=True)
    a, t = resultado["adopcion"], resultado["total"]
    lineas = [
        "# Medición: dirección de cuatro ejes contra la EMA 50",
        "",
        f"Generado {resultado['generado']} (hora Chile) por `scripts/medir_direccion.py`. "
        "Spec: `docs/superpowers/specs/2026-09-28-direccion-4-ejes-design.md`, §5. "
        "Umbrales fijos de `config/direccion.json`: no se ajustaron mirando este resultado.",
        "",
        "## Adopción",
        "",
        f"**Veredicto: {'se adopta' if a['adopta'] else 'no se adopta'}** (requiere 1, 2 y 3).",
        "",
        "| Condición | Resultado | Números |",
        "|---|---|---|",
    ]
    if t.get("n_votos"):
        lineas += [
            f"| 1. Acierto direccional | {_si(a['c1'])} | modelo {_pct(t['c1']['acierto_modelo'])} vs EMA 50 "
            f"{_pct(t['c1']['acierto_ema50'])}; diferencia {_pct(t['c1']['diferencia'])} pts, IC {_ic(t['c1']['ic'])} |",
            f"| 2. LATERAL aparta ruido | {_si(a['c2'])} | EMA 50 en LATERAL {_pct(t['c2']['acierto_ema50_lateral'])} "
            f"vs resto {_pct(t['c2']['acierto_ema50_resto'])}, IC {_ic(t['c2']['ic'])}; mediana abs(m) "
            f"{_pct(t['c2']['mediana_m_lateral'])} vs {_pct(t['c2']['mediana_m_direccional'])} |",
            f"| 3. Estabilidad | {_si(a['c3'])} | giros cada 100: modelo {_pct(t['c3']['giros_modelo_100'])} "
            f"vs EMA 50 con histéresis {_pct(t['c3']['giros_ema50_100'])} |",
            f"| 4. Convicción ordena | {_si(a['c4'])} | " + ", ".join(
                f"{k} {_pct(v)}" for k, v in t["c4"].items()) + " |",
        ]
    lineas += [
        "",
        f"Activos disidentes (conservan la EMA 50): {', '.join(a['disidentes']) or 'ninguno'}. "
        f"Con menos de {int(valor('min_instantes_voto'))} instantes, reportados sin voto: "
        f"{', '.join(a['sin_voto']) or 'ninguno'}.",
        "",
        "## Por activo (instantes que votan)",
        "",
        "| Activo | Votos | Días | Modelo | EMA 50 | Dif. (IC) | Giros modelo / EMA 50 | Paridad EMA 100 (ATR) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for s, r in resultado["por_activo"].items():
        if not r.get("n_votos"):
            lineas.append(f"| {s} | 0 | 0 | n/d | n/d | n/d | n/d | {r.get('paridad_ema100_atr', 0):.3f} |")
            continue
        lineas.append(
            f"| {s} | {r['n_votos']} | {r['n_dias']} | {_pct(r['c1']['acierto_modelo'])} | "
            f"{_pct(r['c1']['acierto_ema50'])} | {_pct(r['c1']['diferencia'])} {_ic(r['c1']['ic'])} | "
            f"{_pct(r['c3']['giros_modelo_100'])} / {_pct(r['c3']['giros_ema50_100'])} | "
            f"{r['paridad_ema100_atr']:.3f} |"
        )
    lineas += ["", "## Dónde cae la muestra", "",
               "El horizonte de 4 velas tiene que ser contiguo. En los activos con pausa diaria "
               "(oro y petróleo a las 17:00 NY) o sesión corta (USD/CLP), eso descarta las velas "
               "de la tarde: **el veredicto describe sobre todo la mañana**. Por hora NY de cierre, "
               "sumando todos los activos:", "",
               "| Hora NY | Votan | Descartadas por hueco |", "|---|---|---|"]
    horas: dict[str, list[int]] = {}
    for r in resultado["por_activo"].values():
        for h, v in (r.get("por_hora_ny") or {}).items():
            acum = horas.setdefault(h, [0, 0])
            acum[0] += v["votan"]
            acum[1] += v["horizonte_con_hueco"]
    for h in sorted(horas):
        lineas.append(f"| {h} | {horas[h][0]} | {horas[h][1]} |")
    sens = resultado.get("sensibilidad_hueco")
    if sens:
        sa = sens["adopcion"]
        lineas += ["", f"**Sensibilidad:** tolerando hasta {sens['tolerancia_horas']} h de hueco en el horizonte "
                   f"votan {sens['n_votos']} instantes y el veredicto es "
                   f"**{'se adopta' if sa['adopta'] else 'no se adopta'}** "
                   f"(1 {_si(sa['c1'])}, 2 {_si(sa['c2'])}, 3 {_si(sa['c3'])}, 4 {_si(sa['c4'])})."]
    lineas += ["", "## Fuera de sesión (no vota)", "",
               "| Activo | Instantes | Modelo | EMA 50 |", "|---|---|---|---|"]
    for s, r in resultado["por_activo"].items():
        f = r.get("fuera_de_sesion") or {}
        if f.get("n_votos"):
            lineas.append(f"| {s} | {f['n_votos']} | {_pct(f['c1']['acierto_modelo'])} | {_pct(f['c1']['acierto_ema50'])} |")
    lineas += ["", "## Descartes", "", "| Activo | Motivo | Instantes |", "|---|---|---|"]
    for s, r in resultado["por_activo"].items():
        for motivo, n in sorted((r.get("descartes") or {}).items()):
            lineas.append(f"| {s} | {motivo} | {n} |")
    lineas += ["", "## Verificación de la zona horaria", "",
               "Las marcas se leyeron como hora de Santiago (§5.4). Las dos pruebas pasaron; si no, "
               "este informe no existiría.", ""]
    for s, r in resultado["zona"]["extraccion"].items():
        lineas.append(f"- {s}: {'aplica' if r['aplica'] else 'no aplica'}. {r['detalle']}")
    for s, r in resultado["zona"]["moda_volumen"].items():
        lineas.append(f"- Pico de volumen de {s}: {r['hora']}:00 NY en {len(r['horas_por_mes'])} meses.")
    texto = "\n".join(lineas).replace("—", ",").replace("–", "-") + "\n"
    md_path = salida / "direccion-4-ejes.md"
    js_path = salida / "direccion-4-ejes.json"
    md_path.write_text(texto, encoding="utf-8")
    js_path.write_text(json.dumps(resultado, ensure_ascii=False, indent=2, default=_json), encoding="utf-8")
    return md_path, js_path


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Mide la direccion de cuatro ejes contra la EMA 50.")
    ap.add_argument("--series", nargs="*", default=None, help="simbolos a medir (por defecto, todos los del config)")
    ap.add_argument("--salida", default=str(DIR_SALIDA))
    args = ap.parse_args(argv)
    try:
        resultado = medir(args.series)
    except MedicionAbortada as exc:
        print(f"MEDICION ABORTADA: {exc}", file=sys.stderr)
        return 2
    md_path, _ = escribir_informe(resultado, Path(args.salida))
    a = resultado["adopcion"]
    print(f"Informe: {md_path}")
    print(f"Veredicto: {'SE ADOPTA' if a['adopta'] else 'NO SE ADOPTA'} "
          f"(c1={a['c1']} c2={a['c2']} c3={a['c3']} c4={a['c4']}; disidentes={a['disidentes']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
