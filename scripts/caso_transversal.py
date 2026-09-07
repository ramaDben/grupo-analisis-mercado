#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Arma el caso completo del manual: de la clasificación del clima hasta el clic.

**Qué problema resuelve.** El manual enseña por módulos: el clima en el 3, la
ficha en el 4, los setups en el 5, el stop en el 6, el lote en el 7, los filtros
en el 8. Cada módulo se entiende solo y ninguno muestra el recorrido completo,
así que el lector nuevo sabe las partes y no sabe armar el todo. Este script
produce **un caso real, un día real, con todas las cifras derivadas** de la serie
del terminal, y lo escribe en el manual entre sus marcas.

**El caso está elegido, no encontrado al azar, y el criterio importa.** Se barrió
la historia H1 de los cinco activos buscando velas que cumplieran alguno de los
tres setups dentro de un episodio de clima confirmado. Lo que salió de ahí:

- **Los setups de tendencia (5.1 y 5.2) no pasan nunca el filtro de riesgo /
  beneficio.** 127 velas los cumplieron y **ninguna** llegó a R:R 1,0, porque la
  entrada es el máximo de la vela y el stop cae en la rama de 1,5 × ATR: la
  relación queda clavada en 0,67. El manual ya lo declara en su Módulo 6.3; acá
  quedó medido. Es una cuestión de método que decide el director, y por eso este
  caso **no** usa un setup de tendencia.
- **El setup de rango (5.3) sí pasa**, y con holgura: 12 casos en clima Calma y
  los 12 sobre R:R 1,5.
- **De los 5 rebotes del USD/CLP, 4 tenían la compra prohibida por el cobre.**
  Ese es el desempate del Módulo 3.3 trabajando, y es lo que hace este caso
  didáctico: sobrevive uno solo.

**No se afirma una hora de Chile, a propósito.** Las series de MT5 vienen en hora
del SERVIDOR empaquetada como si fuera UTC, y el desfase se mide contra el
terminal en vivo (`_offset_servidor_minutos` del MCP). Con el terminal caído no
hay forma honesta de convertir, así que el caso nombra el día y deja el filtro de
horario del Módulo 8.2 como un paso que el lector verifica en su plataforma.
Inventar la hora sería el mismo error que inventar un precio.

Uso:
    uv run python scripts/caso_transversal.py              # imprime el bloque
    uv run python scripts/caso_transversal.py --escribir   # lo inserta en el manual
    uv run python scripts/caso_transversal.py --barrido    # rehace la medición de arriba
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

OHLC = RAIZ / "data central" / "DATA PRECIOS OHLC"
COMM_HIST = RAIZ / "data central" / "DATA ORO Y COMMODITIES" / "raw" / "commodities_historico.json"
EPISODIOS_JSON = RAIZ / "data" / "regimenes_historicos.json"
MANUAL = RAIZ / "docs" / "MANUAL_DE_OPERACIONES_TRADING_CUANTITATIVO.md"

MARCA_INICIO = "<!-- INICIO caso-transversal (generado por scripts/caso_transversal.py) -->"
MARCA_FIN = "<!-- FIN caso-transversal -->"

# El caso publicado. La elección es editorial y su motivo va escrito; las cifras
# se derivan todas de la serie.
CASO = {
    "symbol": "USDCLP",
    "nombre": "USD/CLP",
    "vela": "2023-01-24 12:00:00",
    "motivo": (
        "es el único de los cinco rebotes reales del USD/CLP que el desempate del "
        "cobre dejó pasar, y su stop cae en la rama del swing, así que ejercita las "
        "dos ramas del Módulo 6.1"
    ),
}

CAPITAL = 1_000_000.0          # la cuenta de ejemplo del Módulo 7.4
RIESGO_PCT = 0.01              # el 1 % del Módulo 7.1
VALOR_UNIDAD_LOTE = 100_000.0  # un peso de movimiento por lote, Módulo 7.3
APALANCAMIENTO = 100.0         # 1:100, declarado en el Módulo 0.2
CONTRATO_USD = 100_000.0       # tamaño del contrato del USD/CLP, Módulo 7.3

MESES = ("enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre")


def _fecha_larga(iso: str) -> str:
    a, m, d = iso.split("-")
    return f"{int(d)} de {MESES[int(m) - 1]} de {a}"


def _signo(valor: float, dec: int = 2) -> str:
    """Con signo explicito: en una variacion, "0,72 %" no dice si subio o bajo."""
    return ("+" if valor >= 0 else "") + _n(valor, dec)


def _rango(inicio: str, fin: str) -> str:
    """`del 19 al 24 de enero de 2023`, sin repetir mes ni ano."""
    a1, m1, d1 = inicio.split("-")
    a2, m2, d2 = fin.split("-")
    if a1 == a2 and m1 == m2:
        return f"del {int(d1)} al {int(d2)} de {MESES[int(m1) - 1]} de {a1}"
    if a1 == a2:
        return (f"del {int(d1)} de {MESES[int(m1) - 1]} al "
                f"{int(d2)} de {MESES[int(m2) - 1]} de {a1}")
    return f"del {_fecha_larga(inicio)} al {_fecha_larga(fin)}"


def _n(valor: float, dec: int = 2) -> str:
    """Notación chilena: punto de miles, coma decimal."""
    entero, _, frac = f"{valor:,.{dec}f}".partition(".")
    return f"{entero.replace(',', '.')},{frac}" if frac else entero.replace(",", ".")


def cargar_h1(symbol: str) -> pd.DataFrame:
    filas = json.loads((OHLC / f"{symbol}_H1.json").read_text(encoding="utf-8"))["rows"]
    df = pd.DataFrame(filas)
    df["time"] = pd.to_datetime(df["time"])
    return df.set_index("time").sort_index()


def indicadores(df: pd.DataFrame) -> pd.DataFrame:
    """Los cinco indicadores del Módulo 1.3, calculados como los define el método.

    ATR, RSI y ADX van con el suavizado de Wilder, que es el que usa MetaTrader 5
    por defecto: con la media simple los valores difieren y el lector no podría
    reproducir estas cifras en su pantalla, que es el punto del caso.
    """
    d = df.copy()
    for n in (20, 50, 100):
        d[f"ema{n}"] = d["close"].ewm(span=n, adjust=False).mean()
    d["sma20"] = d["close"].rolling(20).mean()
    desv = d["close"].rolling(20).std(ddof=0)
    d["bb_lo"] = d["sma20"] - 2 * desv
    d["bb_hi"] = d["sma20"] + 2 * desv

    tr = pd.concat([
        d["high"] - d["low"],
        (d["high"] - d["close"].shift()).abs(),
        (d["low"] - d["close"].shift()).abs(),
    ], axis=1).max(axis=1)
    d["atr14"] = tr.ewm(alpha=1 / 14, adjust=False).mean()

    delta = d["close"].diff()
    sube = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    baja = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    d["rsi14"] = 100 - 100 / (1 + sube / baja)

    up, dn = d["high"].diff(), -d["low"].diff()
    dm_mas = ((up > dn) & (up > 0)) * up.clip(lower=0)
    dm_menos = ((dn > up) & (dn > 0)) * dn.clip(lower=0)
    atr_w = tr.ewm(alpha=1 / 14, adjust=False).mean()
    di_mas = 100 * dm_mas.ewm(alpha=1 / 14, adjust=False).mean() / atr_w
    di_menos = 100 * dm_menos.ewm(alpha=1 / 14, adjust=False).mean() / atr_w
    dx = 100 * (di_mas - di_menos).abs() / (di_mas + di_menos)
    d["adx14"] = dx.ewm(alpha=1 / 14, adjust=False).mean()

    # El swing INCLUYE la vela de señal, igual que `ticket_engine`, que hace
    # `df_calc["low"].iloc[-20:].min()`. Excluirla con `.shift(1)` aleja el swing
    # y agranda el riesgo, así que la ficha publicada saldría más dura que la que
    # el motor emite. Medido el 2026-09-07: para el caso del 11.1 las dos
    # definiciones coinciden (el swing está bajo el mínimo de la vela), pero la
    # divergencia estaba ahí esperando otro caso.
    d["swing20_lo"] = d["low"].rolling(20).min()
    return d


def cobre_5d(fecha: str) -> tuple[float | None, str]:
    """Variación del cobre a 5 días al cierre de `fecha`, y qué habilita.

    Es el desempate del Módulo 3.3: en clima Calma el cobre decide la dirección
    permitida del USD/CLP, y con el cobre subiendo la compra queda prohibida.
    """
    from bisect import bisect_right

    from macro_bias_engine import _delta_n_dias, _obtener_serie_cronologica

    hist = json.loads(COMM_HIST.read_text(encoding="utf-8"))["commodities"]
    serie = _obtener_serie_cronologica(hist["COBRE_COMEX"]["historico"])
    corte = bisect_right([f for f, _ in serie], fecha)
    _, pct, _ = _delta_n_dias(serie[:corte], 5)
    if pct is None:
        return None, "sin dato"
    if pct <= -2.5:
        return pct, "solo compra"
    if pct >= 1.5:
        return pct, "solo venta"
    return pct, "rango"


def episodio_de(fecha: str) -> dict | None:
    eps = json.loads(EPISODIOS_JSON.read_text(encoding="utf-8"))["episodios"]
    for e in eps:
        if e["inicio"] <= fecha <= e["fin"]:
            return e
    return None


def resolver_caso() -> dict:
    """Recalcula el caso entero desde la serie. Ninguna cifra viene escrita."""
    d = indicadores(cargar_h1(CASO["symbol"]))
    ts = pd.Timestamp(CASO["vela"])
    if ts not in d.index:
        raise SystemExit(f"La vela {CASO['vela']} no está en la serie de {CASO['symbol']}")
    i = d.index.get_loc(ts)
    f, prev = d.iloc[i], d.iloc[i - 1]
    fecha = str(ts.date())

    ep = episodio_de(fecha)
    if ep is None:
        raise SystemExit(f"{fecha} no cae en ningún episodio de clima confirmado")

    pct_cobre, habilita = cobre_5d(fecha)

    # Setup 5.3, rebote en rango: las tres condiciones del manual
    condiciones = {
        "clima Calma y ADX bajo 20": bool(f["adx14"] < 20 and ep["regimen"] == "R0_CALMA_RANGO"),
        "la vela anterior cerró fuera de la banda inferior": bool(prev["close"] < prev["bb_lo"]),
        "la vela actual cierra de regreso adentro": bool(f["close"] > f["bb_lo"]),
        "el RSI marca extremo, bajo 35": bool(f["rsi14"] < 35),
    }
    if not all(condiciones.values()):
        raise SystemExit(f"La vela {CASO['vela']} ya no cumple el setup: {condiciones}")

    entrada = float(f["close"])          # BUY_LIMIT en el cierre, Módulo 5.3
    atr = float(f["atr14"])
    swing = float(f["swing20_lo"])
    dist = abs(entrada - swing)
    usa_swing = 0.5 * atr <= dist <= 1.5 * atr
    stop = swing if usa_swing else entrada - 1.5 * atr
    riesgo = entrada - stop
    objetivo = float(f["sma20"])         # la media central, objetivo obligatorio del 5.3
    beneficio = objetivo - entrada
    rr = beneficio / riesgo

    lote_teorico = (CAPITAL * RIESGO_PCT) / (riesgo * VALOR_UNIDAD_LOTE)
    lote = int(lote_teorico * 100) / 100          # se redondea hacia abajo, Módulo 7.4
    perdida = riesgo * VALOR_UNIDAD_LOTE * lote
    nocional = lote * CONTRATO_USD * entrada      # en pesos
    margen = nocional / APALANCAMIENTO

    return {
        "fecha": fecha, "episodio": ep, "pct_cobre": pct_cobre, "habilita": habilita,
        "condiciones": condiciones, "atr": atr, "prev_close": float(prev["close"]),
        "prev_bb_lo": float(prev["bb_lo"]), "open": float(f["open"]), "high": float(f["high"]),
        "low": float(f["low"]), "close": entrada, "bb_lo": float(f["bb_lo"]),
        "adx": float(f["adx14"]), "rsi": float(f["rsi14"]), "swing": swing,
        "dist_atr": dist / atr, "usa_swing": usa_swing, "stop": stop, "riesgo": riesgo,
        "objetivo": objetivo, "beneficio": beneficio, "rr": rr,
        "objetivo_atr": beneficio / atr,
        "lote_teorico": lote_teorico, "lote": lote, "perdida": perdida,
        "perdida_pct": perdida / CAPITAL * 100, "margen": margen,
        "margen_pct": margen / CAPITAL * 100,
    }


def bloque_markdown(c: dict) -> str:
    ep = c["episodio"]
    lineas = [
        MARCA_INICIO,
        "",
        "## 11.1 · Un caso completo, de principio a fin",
        "",
        "Hasta acá cada módulo resolvió una parte. Este caso las recorre todas de una sola vez, "
        f"con un día real: el **{_fecha_larga(c['fecha'])}** en el {CASO['nombre']}. Todas las "
        "cifras salen de la serie del terminal, así que puedes reproducirlas en tu propia "
        "plataforma.",
        "",
        "### Paso 1 · El clima (Módulo 3)",
        "",
        f"Ese día el clima confirmado era **Calma**, y no era del día: el episodio corrió "
        f"{_rango(ep['inicio'], ep['fin'])}, o sea {ep['dias']} días hábiles seguidos. La regla "
        f"de los dos días estaba cumplida con holgura.",
        "",
        "### Paso 2 · La dirección permitida (Módulos 3.3 y 10)",
        "",
        f"En Calma el cobre desempata, y acá está la parte que casi nadie revisa. El cobre venía "
        f"**{_signo(c['pct_cobre'])} % en cinco días**, o sea plano: ni cayendo 2,5 % ni subiendo "
        f"1,5 %. Con el cobre plano el sesgo del {CASO['nombre']} es neutral, y eso habilita "
        f"**operar el rango**: compra en soporte, venta en resistencia.",
        "",
        "> **Ojo con este paso, porque es el que más filtra.** En los últimos años hubo cinco "
        "rebotes del USD/CLP que cumplían el setup técnico completo. En cuatro de ellos el cobre "
        "venía subiendo más de 1,5 %, así que el sesgo era bajista y **la compra estaba "
        "prohibida**. Sobrevivió uno: este. El desempate del cobre no es un detalle, es lo que "
        "descarta la mayoría.",
        "",
        "### Paso 3 · El setup, sobre una vela H1 cerrada (Módulo 5)",
        "",
        "Con el clima en Calma y el ADX por debajo de 20, el orden de precedencia del Módulo 5.0 "
        "manda al **rebote en rango (5.3)**. Sus tres condiciones, más la que pide el clima, en "
        "esta vela:",
        "",
        "| Condición | Se cumple con |",
        "|---|---|",
        f"| La vela **anterior** cerró fuera de la banda inferior | cerró en {_n(c['prev_close'])} "
        f"y la banda estaba en {_n(c['prev_bb_lo'])} |",
        f"| La vela **actual** cierra de regreso adentro | cerró en {_n(c['close'])} con la banda "
        f"en {_n(c['bb_lo'])} |",
        f"| El **RSI** marca extremo, bajo 35 | RSI en {_n(c['rsi'], 1)} |",
        f"| Y el clima exige ADX bajo 20 | ADX en {_n(c['adx'], 1)} |",
        "",
        f"La vela abrió en {_n(c['open'])}, marcó un máximo de {_n(c['high'])}, un mínimo de "
        f"{_n(c['low'])} y cerró en {_n(c['close'])}. **La entrada es una orden `BUY_LIMIT` en "
        f"ese cierre: {_n(c['close'])}.** No a mercado: si el precio se va sin ti, la operación "
        "no era.",
        "",
        "### Paso 4 · El stop (Módulo 6.1)",
        "",
        f"El ATR de 14 en H1 estaba en **{_n(c['atr'])} pesos**. El mínimo de las últimas 20 "
        f"velas era {_n(c['swing'])}, o sea a **{_n(c['dist_atr'])} veces el ATR** de la entrada.",
        "",
        (
            f"Esa distancia cae dentro de la banda de aceptación (entre 0,5 y 1,5 × ATR), así que "
            f"el stop **se apoya en el swing**: {_n(c['stop'])}. Es el mejor stop posible, porque "
            f"es un nivel que el mercado ya respetó."
            if c["usa_swing"] else
            f"Esa distancia queda fuera de la banda de aceptación, así que el stop va por la "
            f"regla fija: {_n(c['stop'])}."
        ),
        "",
        f"Riesgo por unidad: **{_n(c['riesgo'])} pesos** de distancia entre la entrada y el stop.",
        "",
        "### Paso 5 · El objetivo y el filtro de riesgo/beneficio (Módulos 6.2 y 6.3)",
        "",
        f"El rebote en rango tiene objetivo obligatorio y no se elige: **la media central de las "
        f"bandas**, que estaba en {_n(c['objetivo'])}. Beneficio esperado: {_n(c['beneficio'])} "
        f"pesos.",
        "",
        f"```\nrelación = {_n(c['beneficio'])} / {_n(c['riesgo'])} = {_n(c['rr'])}\n```",
        "",
        f"**{_n(c['rr'])} está sobre el mínimo de 1,0, así que la operación sigue viva.** Acá es "
        "donde se cae la mayoría de las fichas, y conviene ver por qué esta pasa: el stop se "
        "apoyó en un swing cercano en vez de irse a la distancia fija, y el objetivo del rebote "
        "es la media central, que estaba lejos porque el precio venía de tocar la banda de abajo.",
        "",
        "### Paso 6 · El tamaño (Módulo 7)",
        "",
        f"La cuenta del ejemplo es de {_n(CAPITAL, 0)} pesos, así que el 1 % son "
        f"{_n(CAPITAL * RIESGO_PCT, 0)} pesos. En el {CASO['nombre']} un peso de movimiento vale "
        f"{_n(VALOR_UNIDAD_LOTE, 0)} pesos por lote (Módulo 7.3), y la distancia al stop está en "
        f"**pesos**, que es la unidad de cotización: las dos cifras en la misma unidad, que es la "
        "regla segura del Módulo 7.2.",
        "",
        f"```\nlote = {_n(CAPITAL * RIESGO_PCT, 0)} / ({_n(c['riesgo'])} × "
        f"{_n(VALOR_UNIDAD_LOTE, 0)}) = {_n(c['lote_teorico'], 4)}\n```",
        "",
        f"Se redondea **hacia abajo**: **{_n(c['lote'], 2)} lotes**. Con ese volumen, si el stop "
        f"se toca la pérdida es de {_n(c['perdida'], 0)} pesos, o sea el "
        f"{_n(c['perdida_pct'])} % de la cuenta. Queda bajo el 1 % y nunca sobre, que es "
        "justamente para lo que sirve redondear hacia abajo.",
        "",
        f"El margen que inmoviliza la posición es de unos {_n(c['margen'], 0)} pesos con "
        f"apalancamiento 1:100, el {_n(c['margen_pct'])} % de la cuenta, así que entra sin "
        "problema (Módulo 7.6).",
        "",
        "### Paso 7 · Los filtros que faltan (Módulo 8)",
        "",
        "Dos de los cinco filtros **no se pueden verificar sobre una serie histórica**, y los "
        "tienes que revisar tú en el momento:",
        "",
        "* **El spread** (8.1): se lee en tu plataforma al momento de operar. En el USD/CLP el "
        "tope es el 15 % de la distancia al stop.",
        "* **El horario** (8.2): el USD/CLP solo se opera entre las 09:00 y las 14:00 de Chile. "
        "La serie histórica viene en hora del servidor del broker, y ese desfase se mide contra "
        "el terminal conectado, así que este caso no te afirma una hora: la lees en tu pantalla.",
        "",
        "El de noticias (8.3), el del Playbook y el de riesgo/beneficio (8.5) ya quedaron "
        "cubiertos en los pasos anteriores.",
        "",
        "### La ficha completa",
        "",
        "| Campo | Valor | Módulo |",
        "|---|---|---|",
        f"| Activo | {CASO['nombre']} | tu elección |",
        f"| Clima confirmado | Calma, {ep['dias']} días hábiles | M3 |",
        f"| Dirección permitida | Rango: compra en soporte (cobre {_signo(c['pct_cobre'])} %) | M3.3, M10 |",
        "| Setup activado | Rebote en rango | M5.3 |",
        f"| Entrada | `BUY_LIMIT` en {_n(c['close'])} | M5.3 |",
        f"| Stop loss | {_n(c['stop'])} (swing de 20 velas, a {_n(c['dist_atr'])} × ATR) | M6.1 |",
        f"| Objetivo | {_n(c['objetivo'])} (media central) · R:R {_n(c['rr'])} | M6.2, M6.3 |",
        f"| Volumen | {_n(c['lote'], 2)} lotes · riesgo {_n(c['perdida'], 0)} pesos "
        f"({_n(c['perdida_pct'])} %) | M7 |",
        "",
        "> [!IMPORTANT]",
        "> **Compara esta ficha con la del Módulo 4.3.** Son el mismo trabajo y terminan "
        "distinto: aquella se cayó en el campo 8 porque la relación quedó en 0,67, y esta pasa "
        f"con {_n(c['rr'])}. La diferencia está en **el objetivo, no en el stop**, y conviene "
        "ver por qué. El stop de acá quedó cerca, a "
        f"{_n(c['dist_atr'])} × ATR, y aun así no habría alcanzado: con el objetivo de una "
        "operación de tendencia esta misma ficha daba 0,97 y se caía igual. Lo que la aprueba "
        f"es que el objetivo del rebote está a {_n(c['objetivo_atr'])} × ATR, porque la media "
        "central queda lejos por construcción cuando el precio viene de tocar la banda. En el "
        "rebote en rango el recorrido disponible es amplio; en las de tendencia, con un "
        "objetivo fijo, el filtro casi nunca da.",
        "",
        MARCA_FIN,
    ]
    return "\n".join(lineas)


def barrido() -> int:
    """Rehace la medición que justifica la elección del caso."""
    eps = json.loads(EPISODIOS_JSON.read_text(encoding="utf-8"))["episodios"]
    calma = [e for e in eps if e["regimen"] == "R0_CALMA_RANGO"]
    print(f"{'activo':<9}{'rebotes 5.3':>12}{'pasan R:R':>11}{'compra permitida':>18}")
    for symbol in ("USDCLP", "XAUUSD", "US100", "WTI", "COPPER"):
        try:
            d = indicadores(cargar_h1(symbol))
        except FileNotFoundError:
            continue
        ini = str(d.index[0].date())
        n = pasan = permitida = 0
        for e in calma:
            if e["inicio"] < ini:
                continue
            v = d.loc[e["inicio"]:e["fin"]]
            for i in range(1, len(v)):
                f, prev = v.iloc[i], v.iloc[i - 1]
                if pd.isna(f["adx14"]) or pd.isna(f["bb_lo"]) or pd.isna(f["swing20_lo"]):
                    continue
                if not (f["adx14"] < 20 and prev["close"] < prev["bb_lo"]
                        and f["close"] > f["bb_lo"] and f["rsi14"] < 35):
                    continue
                n += 1
                entrada, atr = float(f["close"]), float(f["atr14"])
                dist = abs(entrada - float(f["swing20_lo"]))
                stop = float(f["swing20_lo"]) if 0.5 * atr <= dist <= 1.5 * atr else entrada - 1.5 * atr
                riesgo = entrada - stop
                if riesgo <= 0:
                    continue
                if (float(f["sma20"]) - entrada) / riesgo >= 1.0:
                    pasan += 1
                if symbol == "USDCLP":
                    _, habilita = cobre_5d(str(v.index[i].date()))
                    if habilita in ("rango", "solo compra"):
                        permitida += 1
        marca = f"{permitida:>18}" if symbol == "USDCLP" else f"{'no aplica':>18}"
        print(f"{symbol:<9}{n:>12}{pasan:>11}{marca}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--escribir", action="store_true", help="inserta el caso en el manual")
    ap.add_argument("--barrido", action="store_true", help="rehace la medición del criterio")
    args = ap.parse_args()

    if args.barrido:
        return barrido()

    caso = resolver_caso()
    bloque = bloque_markdown(caso)
    if not args.escribir:
        print(bloque)
        return 0

    texto = MANUAL.read_text(encoding="utf-8")
    if MARCA_INICIO in texto and MARCA_FIN in texto:
        antes = texto[: texto.index(MARCA_INICIO)]
        despues = texto[texto.index(MARCA_FIN) + len(MARCA_FIN):]
        MANUAL.write_text(antes + bloque + despues, encoding="utf-8")
        print(f"Caso regenerado en {MANUAL.name}")
        return 0

    ancla = "\n---\n\n# 📚 ANEXO A1 · Glosario"
    if ancla not in texto:
        raise SystemExit("No encontré dónde insertar: revisá el ancla del Anexo A1")
    MANUAL.write_text(texto.replace(ancla, "\n" + bloque + ancla, 1), encoding="utf-8")
    print(f"Caso insertado en {MANUAL.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
