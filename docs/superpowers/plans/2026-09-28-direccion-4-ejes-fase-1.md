# Dirección de cuatro ejes, fase 1 — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir el modelo de dirección de cuatro ejes como función pura, correrlo en sombra dentro del escáner sin cambiar nada de lo que sale al cliente, y medirlo sobre la historia contra la EMA 50 con la regla de adopción fijada de antemano.

**Architecture:** `scripts/direccion_gi.py` es un árbol de reglas puro (solo stdlib) que lee los umbrales de `config/direccion.json`. El escáner lo llama en un `try` y guarda el resultado en el campo `direccion_4ejes`, que ningún consumidor lee. `scripts/medir_direccion.py` recalcula los indicadores desde el OHLC con las funciones de `market_data_mcp.mt5_client`, interpreta las marcas como hora de Santiago, arma para cada vela H1 los mismos dicts que entrega `analizar_activo`, y escribe `docs/mediciones/direccion-4-ejes.{md,json}`.

**Tech Stack:** Python 3 (stdlib, `zoneinfo`), pandas 3.0.3 y numpy 2.4.6 (solo en la medición), pytest vía `uv run pytest`.

**Spec:** `docs/superpowers/specs/2026-09-28-direccion-4-ejes-design.md` (revisión 2, commit `bd75f78`). Quien ejecute lee el spec y este plan.

## Global Constraints

- Rama `feat/direccion-4-ejes`. Nunca se commitea a `master`. Cada commit termina con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- **No se commitean** los `data central/*.json` modificados que ya están en el árbol (vienen de la reingesta). Siempre `git add` con rutas explícitas, nunca `git add -A` ni `git add .`.
- **Fase 1 = sombra.** `direccion`, `score`, el chip, el guardia de divergencia del despacho, el informe y los payloads del carrusel no cambian. Nada de este plan toca `pipeline_carrusel.py` ni `pipeline_informe.py`.
- **Umbrales fijos** (§3.3 del spec): `adx_rango` 20, `adx_fuerza` 25, `p_rango` [0,3, 0,7], `p_confirma` 0,6 / 0,4, `histeresis_atr` 0,25 y `consumo_sin_recorrido` 0,70. Viven solo en `config/direccion.json`, cada uno con su `origen`. **No se ajustan mirando el resultado de la medición.**
- `direccion_gi.py` usa solo la stdlib. No importa MT5, pandas ni red.
- Ningún número del árbol va escrito en el código. En `direccion_gi.py` las únicas constantes numéricas permitidas son `0` y `1`. Lo impone un test por AST.
- Todo `motivo` es texto de cliente: tuteo chileno neutro, sin `—` ni `–`, sin cifras de precio.
- Las marcas de las series son hora de **America/Santiago**, aunque digan `"timezone": "UTC"`. Se convierten con `zoneinfo` y **ninguna hora de sesión se escribe en el script**: salen de `config/agenda_mercado.json` y de `config/direccion.json`.
- Una serie que no salió de MT5 o de la cuenta de `config/cuenta_mt5.json` aborta la medición.
- Texto con acentos se escribe desde Python (`Path.write_text(..., encoding="utf-8")`), nunca desde PowerShell.
- Tests: `uv run pytest <archivo> -v`. La suite completa, al final: `uv run pytest -q`.

## Review Focus

Cinco entradas que el spec implica y que ningún test directo del árbol ejercita. Cada una tiene su test en la tarea que es dueña del código:

1. **`previa` con un valor que no es ALCISTA ni BAJISTA** (por ejemplo, un consumidor que pasa `direccion`, que puede ser LATERAL, en vez de `eje2`). Tiene que lanzar `ValueError` y no leerse en silencio sin histéresis. El test está en la Tarea 2.
2. **Un campo presente pero `None` o `NaN`** (el ADX da `NaN` en una serie plana). Cuenta como faltante y cae en `datos_incompletos`, sin llegar a comparar con `NaN`. El test está en la Tarea 2.
3. **Un horizonte que cruza un hueco de la serie** (una vela ausente, o el cierre del viernes del FX, donde `t+4` cae el domingo). El instante no vota, con el motivo `horizonte_con_hueco`, y no se mide un `m` de dos días. El test está en la Tarea 6.
4. **La vela D1 del cambio de horario de septiembre**, cuya marca 00:00 de Santiago no existe. El marco diario se alinea por fecha y no por hora localizada, así que no se descarta ningún día D1. El test está en la Tarea 5.
5. **Una corrida con `--series` sin US100.** La prueba de zona horaria necesita el US100 igual, así que se carga aunque no se mida. El test está en la Tarea 7.

---

## File Structure

| Archivo | Acción | Responsabilidad |
|---|---|---|
| `config/direccion.json` | Crear | Umbrales del árbol y parámetros de la medición, cada uno con `valor` y `origen` |
| `scripts/direccion_gi.py` | Crear | Árbol puro: ejes, histéresis, `leer_direccion`, `LecturaDireccion`, motivo |
| `scripts/screener_gi.py` | Modificar | `_direccion_en_sombra`, campo `direccion_4ejes` en `evaluar_activo`, `avisos_de_sombra` en `escanear` |
| `scripts/medir_direccion.py` | Crear | Carga y sellos, zona horaria, indicadores en serie, lecturas por instante, métricas, adopción, informe y CLI |
| `tests/test_direccion_gi.py` | Crear | Árbol, bordes, cobertura, contrato de config, motivo |
| `tests/test_screener_gi.py` | Modificar | Sombra inerte y avisos |
| `tests/test_pipeline_carrusel.py` | Modificar | El payload no cambia con la sombra |
| `tests/test_medir_direccion.py` | Crear | Sellos, zona horaria, paridad, anti fuga, giros, métricas, adopción |
| `docs/mediciones/direccion-4-ejes.md` y `.json` | Crear (salida) | Resultado de la corrida real |

`medir_direccion.py` es un solo archivo con secciones, igual que los otros scripts del repo. Si pasa de unas 600 líneas, se separa `medicion_metricas.py` en la Tarea 6.

---

### Task 1: Config de umbrales y ejes básicos

**Files:**
- Create: `config/direccion.json`
- Create: `scripts/direccion_gi.py`
- Test: `tests/test_direccion_gi.py`

**Interfaces:**
- Produces:
  - `direccion_gi.ALCISTA`, `BAJISTA`, `LATERAL` y `TRANSICION` (str)
  - `umbrales() -> dict[str, float]`
  - `posicion_canal(h1: dict) -> float | None`
  - `eje_fondo(d1: dict) -> str | None`, que devuelve ALCISTA, BAJISTA o TRANSICION
  - `eje_dia(h1: dict, previa: str | None = None) -> str`, que devuelve ALCISTA o BAJISTA
  - `canal_confirma(lado: str, p: float) -> bool`
  - `consumo_diario(d1: dict, hoy: str | None = None) -> float | None`
  - `_num(d: dict, campo: str) -> float | None`

- [ ] **Step 1: Crear `config/direccion.json`**

```json
{
  "_nota": "Umbrales del modelo de direccion de cuatro ejes (spec docs/superpowers/specs/2026-09-28-direccion-4-ejes-design.md). FIJOS en la fase 1: no se ajustan mirando el resultado de la medicion. Si algun dia se calibran, se ajustan con el 70 % mas antiguo de la historia y se validan con el 30 % mas reciente.",
  "umbrales": {
    "adx_rango": {"valor": 20, "origen": "Corte convencional de 'sin tendencia'; mismo valor que el piso del gate ADX de oportunidad (que se aplica al ADX diario; aca es el de H1)."},
    "adx_fuerza": {"valor": 25, "origen": "Umbral de factor_momentum para 'expansion' en screener_gi.py."},
    "p_rango_min": {"valor": 0.3, "origen": "Tercio central ampliado del canal Donchian 50 (limite inferior)."},
    "p_rango_max": {"valor": 0.7, "origen": "Tercio central ampliado del canal Donchian 50 (limite superior)."},
    "p_confirma_alcista": {"valor": 0.6, "origen": "Fuera de la mitad del canal por un decimo, lado alto."},
    "p_confirma_bajista": {"valor": 0.4, "origen": "Fuera de la mitad del canal por un decimo, lado bajo."},
    "histeresis_atr": {"valor": 0.25, "origen": "Un cuarto de la vela tipica de H1 (ATR 14)."},
    "consumo_sin_recorrido": {"valor": 0.70, "origen": "Corte de puntuacion de factor_espacio (screener_gi.py:645-651): sobre 0,70 el espacio deja de valer los 20 puntos."}
  },
  "medicion": {
    "horizonte_velas": {"valor": 4, "origen": "Spec 5.6: h = 4 velas H1."},
    "horizonte_minimo": {"valor": 3, "origen": "Spec 5.5: con menos de 3 horas por delante el instante no vota."},
    "min_velas_cerradas": {"valor": 150, "origen": "Minimo de analizar_activo (analisis.py:215), en D1 y en H1."},
    "min_instantes_voto": {"valor": 500, "origen": "Spec 5.7 condicion 5: bajo 500 instantes el activo se reporta y no vota."},
    "tolerancia_acierto_pts": {"valor": 1.0, "origen": "Spec 5.7 condicion 1: limite inferior del IC de (modelo menos EMA 50) mayor o igual a -1 punto."},
    "umbral_disidente_pts": {"valor": 2.0, "origen": "Spec 5.7 condicion 5: un activo mas de 2 puntos bajo la EMA 50 conserva la EMA 50."},
    "bootstrap_iteraciones": {"valor": 2000, "origen": "Remuestreos del bootstrap agrupado por dia."},
    "bootstrap_semilla": {"valor": 20260928, "origen": "Semilla fija para que el informe sea reproducible."},
    "nivel_confianza": {"valor": 0.95, "origen": "Spec 5.6: intervalo del 95 %."},
    "cierre_bolsa_ny": {"valor": "16:00", "clases": ["indices"], "origen": "Cierre de la bolsa de Nueva York: el horizonte de los indices se corta ahi (spec 5.5)."},
    "serie_prueba_zona": {"valor": "US100", "origen": "Spec 5.4: la moda mensual de la vela de mayor volumen del US100 verifica la zona horaria."},
    "series": {
      "XAUUSD": {"clase": "forex_commodities"},
      "WTI": {"clase": "forex_commodities"},
      "US100": {"clase": "indices"},
      "USDCLP": {"clase": "forex_commodities"},
      "COPPER": {"clase": "forex_commodities"},
      "USDIDX": {"clase": "forex_commodities"},
      "BRENT": {"clase": "forex_commodities"}
    }
  }
}
```

- [ ] **Step 2: Escribir los tests que fallan**

```python
"""Contrato del modelo de dirección de cuatro ejes (fase 1, en sombra).

Todo con dicts construidos a mano con los nombres reales de `analizar_activo`.
Spec: docs/superpowers/specs/2026-09-28-direccion-4-ejes-design.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

import direccion_gi as dg  # noqa: E402


def h1_base(**cambios) -> dict:
    """H1 alcista y fuerte: precio sobre la EMA 50, ADX 30, p = 0,8."""
    h1 = {
        "ticker": "TEST", "timeframe": "H1", "price": 108.0,
        "ema_50": 100.0, "atr_14": 2.0, "adx_14": 30.0,
        "donchian_50_high": 110.0, "donchian_50_low": 100.0,
    }
    h1.update(cambios)
    return h1


def d1_base(**cambios) -> dict:
    """D1 alcista: precio > EMA 50 > EMA 100, con 30 % del ATR consumido."""
    d1 = {
        "ticker": "TEST", "timeframe": "D1", "price": 108.0,
        "ema_50": 90.0, "ema_100": 80.0, "atr_14": 10.0,
        "rango_hoy": 3.0, "fecha_barra": "2026-09-28",
    }
    d1.update(cambios)
    return d1


def test_los_umbrales_salen_del_config():
    u = dg.umbrales()
    assert u == {
        "adx_rango": 20.0, "adx_fuerza": 25.0,
        "p_rango_min": 0.3, "p_rango_max": 0.7,
        "p_confirma_alcista": 0.6, "p_confirma_bajista": 0.4,
        "histeresis_atr": 0.25, "consumo_sin_recorrido": 0.70,
    }


def test_posicion_canal_dentro_y_en_quiebre():
    assert dg.posicion_canal(h1_base(price=105.0)) == pytest.approx(0.5)
    assert dg.posicion_canal(h1_base(price=112.0)) == pytest.approx(1.2)
    assert dg.posicion_canal(h1_base(price=98.0)) == pytest.approx(-0.2)


def test_posicion_canal_sin_ancho_no_se_calcula():
    assert dg.posicion_canal(h1_base(donchian_50_high=100.0, donchian_50_low=100.0)) is None
    assert dg.posicion_canal(h1_base(donchian_50_high=None)) is None


@pytest.mark.parametrize("precio, e50, e100, esperado", [
    (108.0, 90.0, 80.0, "ALCISTA"),
    (70.0, 75.0, 80.0, "BAJISTA"),
    (95.0, 90.0, 92.0, "TRANSICION"),   # precio sobre la 50, pero la 50 bajo la 100
    (85.0, 90.0, 80.0, "TRANSICION"),   # precio bajo la 50, con la 50 sobre la 100
    (90.0, 90.0, 80.0, "TRANSICION"),   # empate exacto con la 50
])
def test_eje_fondo(precio, e50, e100, esperado):
    assert dg.eje_fondo(d1_base(price=precio, ema_50=e50, ema_100=e100)) == esperado


def test_eje_fondo_con_campo_faltante_es_none():
    assert dg.eje_fondo(d1_base(ema_100=None)) is None


def test_eje_dia_sin_previa_y_empate_alcista():
    assert dg.eje_dia(h1_base(price=101.0)) == "ALCISTA"
    assert dg.eje_dia(h1_base(price=99.0)) == "BAJISTA"
    assert dg.eje_dia(h1_base(price=100.0)) == "ALCISTA"


@pytest.mark.parametrize("precio, previa, esperado", [
    (99.6, "ALCISTA", "ALCISTA"),    # cruzó 0,4 < 0,5 (0,25 x ATR 2): no alcanza
    (99.5, "ALCISTA", "ALCISTA"),    # exactamente en el borde: "más de" no se cumple
    (99.49, "ALCISTA", "BAJISTA"),
    (100.4, "BAJISTA", "BAJISTA"),
    (100.5, "BAJISTA", "BAJISTA"),
    (100.51, "BAJISTA", "ALCISTA"),
])
def test_eje_dia_con_histeresis(precio, previa, esperado):
    assert dg.eje_dia(h1_base(price=precio), previa) == esperado


def test_eje_dia_sin_precio_o_ema_lanza():
    with pytest.raises(ValueError):
        dg.eje_dia(h1_base(ema_50=None))


def test_canal_confirma_por_lado():
    assert dg.canal_confirma("ALCISTA", 0.6) is True
    assert dg.canal_confirma("ALCISTA", 0.59) is False
    assert dg.canal_confirma("ALCISTA", 1.3) is True     # quiebre al alza
    assert dg.canal_confirma("BAJISTA", 0.4) is True
    assert dg.canal_confirma("BAJISTA", 0.41) is False
    assert dg.canal_confirma("BAJISTA", -0.2) is True    # quiebre a la baja


def test_consumo_diario_y_regla_de_fecha_barra():
    assert dg.consumo_diario(d1_base()) == pytest.approx(0.3)
    assert dg.consumo_diario(d1_base(), hoy="2026-09-28") == pytest.approx(0.3)
    # vela D1 de un día anterior: el mercado de hoy no ha consumido nada
    assert dg.consumo_diario(d1_base(fecha_barra="2026-09-25"), hoy="2026-09-28") == 0.0
    assert dg.consumo_diario(d1_base(rango_hoy=None)) is None
    assert dg.consumo_diario(d1_base(atr_14=0.0)) is None


def test_num_trata_nan_e_inf_como_faltantes():
    assert dg._num({"x": float("nan")}, "x") is None
    assert dg._num({"x": float("inf")}, "x") is None
    assert dg._num({"x": True}, "x") is None
    assert dg._num({"x": "3.5"}, "x") == 3.5
    assert dg._num({}, "x") is None
```

- [ ] **Step 3: Verificar que fallan**

Run: `uv run pytest tests/test_direccion_gi.py -v`
Expected: ERROR de colección con `ModuleNotFoundError: No module named 'direccion_gi'`

- [ ] **Step 4: Implementar la base de `scripts/direccion_gi.py`**

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Dirección técnica de cuatro ejes. Fase 1: se calcula en sombra y se mide.

**El problema que cierra.** La dirección de toda pieza era una sola línea
(`screener_gi.direccion_tecnica`: precio contra la EMA 50 de H1). Nunca decía
LATERAL, no distinguía una corrección de un cambio de tendencia y no informaba
convicción.

**Ejes independientes, no votos.** EMA, MACD y RSI salen del mismo cierre
suavizado: si votaran juntos, "4 de 4" sería la misma señal contada cuatro
veces, que es la confianza inflada que hundió al Playbook V2. Cada eje mide algo
distinto y los combina un árbol explícito, cuya rama **es** el motivo que lee el
cliente:

1. Fondo (D1): precio contra `ema_50` y `ema_50` contra `ema_100`. Es el ancla.
2. Día (H1): precio contra `ema_50`, con histéresis, más la posición en el
   Donchian 50, que confirma el lado.
3. Fuerza (`adx_14` de H1): decide LATERAL, la convicción y el desempate de la
   corrección. **No vota dirección**, porque sube igual en una caída.
4. Espacio (consumo de ATR diario): **solo texto**. Ya pesa en el escáner como
   gate y como factor, y usarlo acá también lo contaría tres veces.

Los umbrales viven en `config/direccion.json` y en esta fase son fijos. Un test
impide que aparezcan escritos acá.

Spec: docs/superpowers/specs/2026-09-28-direccion-4-ejes-design.md
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
CONFIG = RAIZ / "config" / "direccion.json"

ALCISTA = "ALCISTA"
BAJISTA = "BAJISTA"
LATERAL = "LATERAL"
TRANSICION = "TRANSICION"


@lru_cache(maxsize=1)
def _cfg() -> dict[str, Any]:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def umbrales() -> dict[str, float]:
    return {k: float(v["valor"]) for k, v in _cfg()["umbrales"].items()}


def _num(d: dict[str, Any], campo: str) -> float | None:
    """El campo como número finito, o `None`.

    `None`, `NaN`, infinito o un booleano cuentan como ausentes: el ADX da `NaN`
    en una serie plana, y comparar contra `NaN` devuelve `False` en silencio en
    vez de avisar que falta el dato.
    """
    v = d.get(campo)
    if v is None or isinstance(v, bool):
        return None
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if math.isfinite(x) else None


def posicion_canal(h1: dict[str, Any]) -> float | None:
    """Dónde está el precio dentro del Donchian 50 de H1.

    El canal es de velas cerradas, así que en un quiebre `p` sale de [0, 1]:
    `p > 1` es un precio sobre el máximo de 50 velas y `p < 0` bajo el mínimo. Es
    un estado válido. Sin ancho de canal no hay posición.
    """
    precio = _num(h1, "price")
    alto = _num(h1, "donchian_50_high")
    bajo = _num(h1, "donchian_50_low")
    if precio is None or alto is None or bajo is None or alto <= bajo:
        return None
    return (precio - bajo) / (alto - bajo)


def eje_fondo(d1: dict[str, Any]) -> str | None:
    precio = _num(d1, "price")
    e50 = _num(d1, "ema_50")
    e100 = _num(d1, "ema_100")
    if precio is None or e50 is None or e100 is None:
        return None
    if precio > e50 and e50 > e100:
        return ALCISTA
    if precio < e50 and e50 < e100:
        return BAJISTA
    return TRANSICION


def eje_dia(h1: dict[str, Any], previa: str | None = None) -> str:
    """El lado del precio contra la EMA 50 de H1. Nunca LATERAL.

    Con `previa`, solo cambia de lado si el precio cruza la media por **más de**
    `histeresis_atr` x ATR 14 de H1. Sin `previa` (o sin ATR) se lee sin
    histéresis, y el empate exacto se resuelve alcista, igual que
    `direccion_tecnica`.
    """
    precio = _num(h1, "price")
    e50 = _num(h1, "ema_50")
    if precio is None or e50 is None:
        raise ValueError("H1 sin price o ema_50: no hay dirección que leer")
    atr = _num(h1, "atr_14")
    if previa is not None and atr is not None:
        banda = umbrales()["histeresis_atr"] * atr
        if previa == ALCISTA:
            return BAJISTA if precio < e50 - banda else ALCISTA
        return ALCISTA if precio > e50 + banda else BAJISTA
    return ALCISTA if precio >= e50 else BAJISTA


def canal_confirma(lado: str, p: float) -> bool:
    u = umbrales()
    if lado == ALCISTA:
        return p >= u["p_confirma_alcista"]
    return p <= u["p_confirma_bajista"]


def consumo_diario(d1: dict[str, Any], hoy: str | None = None) -> float | None:
    """`rango_hoy / atr_14` de D1, con la regla de `fecha_barra` del escáner.

    Si la vela D1 es de un día anterior a `hoy` (fecha ISO de Santiago), el
    mercado todavía no registra la jornada y el consumo es 0: la misma regla que
    `screener_gi.gate_agotamiento`.
    """
    fecha = d1.get("fecha_barra")
    if hoy and fecha and str(fecha) < hoy:
        return 0.0
    atr = _num(d1, "atr_14")
    rango = _num(d1, "rango_hoy")
    if atr is None or rango is None or atr <= 0:
        return None
    return rango / atr
```

- [ ] **Step 5: Verificar que pasan**

Run: `uv run pytest tests/test_direccion_gi.py -v`
Expected: PASS en todos

- [ ] **Step 6: Commit**

```bash
git add config/direccion.json scripts/direccion_gi.py tests/test_direccion_gi.py
git commit -m "feat(direccion): umbrales en config y ejes basicos del modelo de cuatro ejes

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: El árbol, la lectura y el motivo

**Files:**
- Modify: `scripts/direccion_gi.py`
- Test: `tests/test_direccion_gi.py`

**Interfaces:**
- Consumes: todo lo de la Tarea 1.
- Produces:
  - `LecturaDireccion`, dataclass congelada con estos campos:
    - `direccion: str`
    - `conviccion: str | None`, que vale `"fuerte"`, `"moderada"`, `"debil"` o `None` en rango
    - `fase: str`
    - `sin_recorrido: bool`
    - `eje2: str`
    - `motivo: str`
    - `ejes: dict`
  - `leer_direccion(h1: dict, d1: dict, previa: str | None = None, *, hoy: str | None = None) -> LecturaDireccion`
  - `a_dict(lectura: LecturaDireccion) -> dict`
  - Fases: `datos_incompletos`, `rango`, `tendencia_alineada`, `correccion_con_fuerza`, `correccion` y `sin_ancla`.
  - `ejes` trae las claves `fondo`, `dia`, `p`, `adx`, `consumo` y, solo en `datos_incompletos`, `faltan` (lista de `"h1.<campo>"` o `"d1.<campo>"`).

> **Nota sobre la firma.** El spec fija `leer_direccion(h1, d1, previa=None)`. Este plan le agrega el argumento solo por nombre `hoy`, que hace falta para aplicar la regla de `fecha_barra` de la marca `sin_recorrido` (§3.1). Sin `hoy`, la marca se calcula sin esa regla. La firma del spec sigue funcionando igual.

- [ ] **Step 1: Agregar los tests que fallan**

Se agregan al final de `tests/test_direccion_gi.py`:

```python
import ast
import json
from itertools import product


# ── Una por rama ────────────────────────────────────────────────────────────
def test_rama_0_datos_incompletos_nombra_el_campo():
    lec = dg.leer_direccion(h1_base(adx_14=None), d1_base())
    assert lec.fase == "datos_incompletos"
    assert lec.direccion == "ALCISTA"          # la de H1
    assert lec.conviccion == "debil"
    assert "h1.adx_14" in lec.ejes["faltan"]


def test_rama_0_con_nan_y_con_d1_incompleto():
    lec = dg.leer_direccion(h1_base(adx_14=float("nan")), d1_base(ema_100=None))
    assert lec.fase == "datos_incompletos"
    assert set(lec.ejes["faltan"]) >= {"h1.adx_14", "d1.ema_100"}


def test_rama_0_canal_sin_ancho():
    lec = dg.leer_direccion(h1_base(donchian_50_high=100.0, donchian_50_low=100.0), d1_base())
    assert lec.fase == "datos_incompletos"
    assert "h1.donchian_50 sin ancho" in lec.ejes["faltan"]


def test_rama_1_rango():
    lec = dg.leer_direccion(h1_base(adx_14=15.0, price=105.0), d1_base())
    assert (lec.direccion, lec.conviccion, lec.fase) == ("LATERAL", None, "rango")
    assert lec.eje2 == "ALCISTA"                # el eje 2 nunca es LATERAL


def test_rama_2_fuerte_moderada_debil():
    fuerte = dg.leer_direccion(h1_base(), d1_base())
    assert (fuerte.direccion, fuerte.conviccion, fuerte.fase) == ("ALCISTA", "fuerte", "tendencia_alineada")
    sin_canal = dg.leer_direccion(h1_base(price=101.0), d1_base(price=101.0))  # p = 0,1 no confirma
    assert sin_canal.conviccion == "moderada"
    media = dg.leer_direccion(h1_base(adx_14=22.0), d1_base())
    assert media.conviccion == "moderada"
    debil = dg.leer_direccion(h1_base(adx_14=15.0), d1_base())  # p = 0,8: fuera de la zona media
    assert (debil.conviccion, debil.fase) == ("debil", "tendencia_alineada")


def test_rama_3a_correccion_con_fuerza_manda_el_dia():
    # D1 bajista, H1 alcista, ADX 30
    lec = dg.leer_direccion(h1_base(), d1_base(price=108.0, ema_50=115.0, ema_100=120.0))
    assert (lec.direccion, lec.conviccion, lec.fase) == ("ALCISTA", "moderada", "correccion_con_fuerza")


def test_rama_3b_correccion_sin_fuerza_manda_el_fondo():
    lec = dg.leer_direccion(h1_base(adx_14=22.0), d1_base(price=108.0, ema_50=115.0, ema_100=120.0))
    assert (lec.direccion, lec.conviccion, lec.fase) == ("BAJISTA", "debil", "correccion")
    assert "resistencia" in lec.motivo


def test_rama_4_sin_ancla():
    lec = dg.leer_direccion(h1_base(), d1_base(ema_50=90.0, ema_100=95.0))
    assert (lec.direccion, lec.conviccion, lec.fase) == ("ALCISTA", "debil", "sin_ancla")


# ── Marca sin_recorrido ─────────────────────────────────────────────────────
def test_sin_recorrido_desde_0_70_y_con_fecha_barra():
    assert dg.leer_direccion(h1_base(), d1_base(rango_hoy=6.9)).sin_recorrido is False
    assert dg.leer_direccion(h1_base(), d1_base(rango_hoy=7.0)).sin_recorrido is True
    ayer = d1_base(rango_hoy=9.0, fecha_barra="2026-09-25")
    assert dg.leer_direccion(h1_base(), ayer, hoy="2026-09-28").sin_recorrido is False
    lec = dg.leer_direccion(h1_base(), d1_base(rango_hoy=8.0))
    assert lec.fase == "tendencia_alineada"     # no cambia dirección ni convicción
    assert lec.conviccion == "fuerte"


def test_sin_rango_hoy_no_marca_ni_degrada():
    lec = dg.leer_direccion(h1_base(), d1_base(rango_hoy=None))
    assert lec.sin_recorrido is False
    assert lec.fase == "tendencia_alineada"


# ── Bordes exactos ──────────────────────────────────────────────────────────
@pytest.mark.parametrize("adx, esperado", [(19.99, "rango"), (20.0, "tendencia_alineada")])
def test_borde_adx_20(adx, esperado):
    assert dg.leer_direccion(h1_base(adx_14=adx, price=105.0), d1_base(price=105.0)).fase == esperado


@pytest.mark.parametrize("adx, conv", [(24.99, "moderada"), (25.0, "fuerte")])
def test_borde_adx_25_en_rama_2(adx, conv):
    assert dg.leer_direccion(h1_base(adx_14=adx), d1_base()).conviccion == conv


@pytest.mark.parametrize("adx, fase", [(24.99, "correccion"), (25.0, "correccion_con_fuerza")])
def test_borde_adx_25_en_rama_3(adx, fase):
    d1_bajista = d1_base(ema_50=115.0, ema_100=120.0)
    assert dg.leer_direccion(h1_base(adx_14=adx), d1_bajista).fase == fase


@pytest.mark.parametrize("precio, fase", [
    (102.99, "tendencia_alineada"),   # p = 0,299
    (103.0, "rango"),                 # p = 0,3
    (107.0, "rango"),                 # p = 0,7
    (107.01, "tendencia_alineada"),   # p = 0,701
])
def test_bordes_p_rango(precio, fase):
    assert dg.leer_direccion(h1_base(adx_14=15.0, price=precio), d1_base(price=precio)).fase == fase


@pytest.mark.parametrize("precio, conv", [(106.0, "fuerte"), (105.99, "moderada")])
def test_borde_p_confirma_0_6(precio, conv):
    assert dg.leer_direccion(h1_base(price=precio), d1_base(price=precio)).conviccion == conv


def test_borde_p_confirma_0_4_bajista():
    # H1 bajo la EMA 50: la ubico en 110 para que el precio quede bajo ella
    h1 = h1_base(ema_50=110.0, price=104.0)          # p = 0,4
    d1 = d1_base(price=104.0, ema_50=115.0, ema_100=120.0)
    assert dg.leer_direccion(h1, d1).conviccion == "fuerte"
    h1b = h1_base(ema_50=110.0, price=104.01)        # p = 0,401
    assert dg.leer_direccion(h1b, d1_base(price=104.01, ema_50=115.0, ema_100=120.0)).conviccion == "moderada"


def test_quiebres_confirman_su_lado():
    assert dg.leer_direccion(h1_base(price=112.0), d1_base(price=112.0)).conviccion == "fuerte"
    h1 = h1_base(ema_50=103.0, price=98.0)           # p = -0,2
    d1 = d1_base(price=98.0, ema_50=115.0, ema_100=120.0)
    assert dg.leer_direccion(h1, d1).conviccion == "fuerte"


def test_histeresis_viaja_en_eje2():
    h1 = h1_base(price=99.6, adx_14=30.0)             # bajo la media, dentro de la banda
    lec = dg.leer_direccion(h1, d1_base(price=99.6), previa="ALCISTA")
    assert lec.eje2 == "ALCISTA"
    assert dg.leer_direccion(h1, d1_base(price=99.6)).eje2 == "BAJISTA"   # sin previa


def test_previa_invalida_lanza():
    with pytest.raises(ValueError):
        dg.leer_direccion(h1_base(), d1_base(), previa="LATERAL")


# ── Cobertura del árbol ─────────────────────────────────────────────────────
FONDOS = {
    "ALCISTA": dict(ema_50=90.0, ema_100=80.0),
    "BAJISTA": dict(ema_50=200.0, ema_100=210.0),
    "TRANSICION": dict(ema_50=90.0, ema_100=95.0),
}
DIAS = {"ALCISTA": 50.0, "BAJISTA": 200.0}          # ema_50 de H1 bajo o sobre el precio
ADXS = [19.99, 20.0, 24.99, 25.0]
PRECIOS = [102.99, 103.0, 105.0, 107.0, 107.01, 112.0, 98.0]   # p a los dos lados de cada umbral


def test_cobertura_seis_combinaciones_una_rama_cada_una():
    for (fondo, cfg_d1), (dia, e50_h1), adx, precio in product(FONDOS.items(), DIAS.items(), ADXS, PRECIOS):
        h1 = h1_base(price=precio, ema_50=e50_h1, adx_14=adx)
        d1 = d1_base(price=precio, **cfg_d1)
        lec = dg.leer_direccion(h1, d1)
        assert lec.ejes["fondo"] == fondo and lec.ejes["dia"] == dia
        p = lec.ejes["p"]
        if adx < 20 and 0.3 <= p <= 0.7:
            esperada = "rango"
        elif fondo == "TRANSICION":
            esperada = "sin_ancla"
        elif fondo == dia:
            esperada = "tendencia_alineada"
        else:
            esperada = "correccion_con_fuerza" if adx >= 25 else "correccion"
        assert lec.fase == esperada, (fondo, dia, adx, precio, lec)


# ── Contrato de config y motivo de cliente ──────────────────────────────────
def test_ningun_numero_del_arbol_esta_escrito_en_el_codigo():
    fuente = (RAIZ / "scripts" / "direccion_gi.py").read_text(encoding="utf-8")
    numeros = {
        n.value for n in ast.walk(ast.parse(fuente))
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
        and not isinstance(n.value, bool)
    }
    assert numeros <= {0, 1}, f"umbrales escritos a mano: {sorted(numeros - {0, 1})}"


def test_todo_umbral_tiene_valor_y_origen():
    datos = json.loads((RAIZ / "config" / "direccion.json").read_text(encoding="utf-8"))
    for bloque in ("umbrales", "medicion"):
        for clave, v in datos[bloque].items():
            if clave == "series":
                continue
            assert "valor" in v and str(v.get("origen", "")).strip(), clave


def test_ningun_motivo_lleva_guion_largo_ni_medio():
    for fondo, cfg_d1 in FONDOS.items():
        for dia, e50_h1 in DIAS.items():
            for adx in (15.0, 22.0, 30.0):
                for precio in (105.0, 112.0):
                    for rango in (3.0, 8.0):
                        lec = dg.leer_direccion(
                            h1_base(price=precio, ema_50=e50_h1, adx_14=adx),
                            d1_base(price=precio, rango_hoy=rango, **cfg_d1),
                        )
                        assert "—" not in lec.motivo and "–" not in lec.motivo, lec.motivo
                        assert lec.motivo.strip()
    lec = dg.leer_direccion(h1_base(adx_14=None), d1_base())
    assert "—" not in lec.motivo and "–" not in lec.motivo


def test_a_dict_es_serializable():
    json.dumps(dg.a_dict(dg.leer_direccion(h1_base(), d1_base())))
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_direccion_gi.py -v`
Expected: FAIL con `AttributeError: module 'direccion_gi' has no attribute 'leer_direccion'`. Los tests de la Tarea 1 siguen en PASS.

- [ ] **Step 3: Implementar el árbol**

Agregar `from dataclasses import asdict, dataclass, field` a los imports y esto al final de `scripts/direccion_gi.py`:

```python
@dataclass(frozen=True)
class LecturaDireccion:
    direccion: str
    conviccion: str | None
    fase: str
    sin_recorrido: bool
    eje2: str
    motivo: str
    ejes: dict[str, Any] = field(default_factory=dict)


def a_dict(lectura: LecturaDireccion) -> dict[str, Any]:
    return asdict(lectura)


_HACIA = {ALCISTA: "al alza", BAJISTA: "a la baja"}
_SUBE = {ALCISTA: "sube", BAJISTA: "baja"}
_TENDENCIA = {ALCISTA: "alcista", BAJISTA: "bajista"}
_VIGILA = {ALCISTA: "el soporte", BAJISTA: "la resistencia"}


def _motivo(direccion: str, fase: str, fondo: str | None, sin_recorrido: bool) -> str:
    """Una línea en voz de cliente: la rama del árbol dicha en simple.

    Sin guion largo, sin cifras de precio y en tuteo chileno neutro.
    """
    if fase == "rango":
        texto = ("Se mueve de lado: no tiene fuerza de tendencia y está en la zona "
                 "media de su canal de las últimas cincuenta horas.")
    elif fase == "tendencia_alineada":
        texto = f"La tendencia de fondo y la del día van {_HACIA[direccion]}."
    elif fase == "correccion_con_fuerza":
        texto = (f"Hoy {_SUBE[direccion]} con fuerza, contra la tendencia de fondo, "
                 f"que sigue {_HACIA[fondo]}.")
    elif fase == "correccion":
        texto = (f"Corrige dentro de una tendencia {_TENDENCIA[direccion]}: se vigila "
                 f"{_VIGILA[direccion]} para retomar.")
    elif fase == "sin_ancla":
        texto = f"Hoy {_SUBE[direccion]}, pero la tendencia de fondo todavía no define dirección."
    else:
        texto = (f"La lectura de la hora va {_HACIA[direccion]}, pero falta información "
                 "para contrastarla con la tendencia de fondo.")
    if sin_recorrido:
        texto += " Ojo: ya recorrió buena parte de su movimiento típico del día."
    return texto


def _faltantes(h1: dict[str, Any], d1: dict[str, Any], p: float | None) -> list[str]:
    """Los campos que impiden una lectura completa, con el marco de cada uno."""
    faltan = [f"h1.{c}" for c in ("adx_14", "donchian_50_high", "donchian_50_low") if _num(h1, c) is None]
    bordes = _num(h1, "donchian_50_high") is not None and _num(h1, "donchian_50_low") is not None
    if p is None and bordes:
        faltan.append("h1.donchian_50 sin ancho")
    faltan += [f"d1.{c}" for c in ("price", "ema_50", "ema_100") if _num(d1, c) is None]
    return faltan


def leer_direccion(
    h1: dict[str, Any],
    d1: dict[str, Any],
    previa: str | None = None,
    *,
    hoy: str | None = None,
) -> LecturaDireccion:
    """La dirección de cuatro ejes. Gana la primera rama que calce (spec §3.1).

    `previa` es el `eje2` de la lectura anterior (ALCISTA o BAJISTA), nunca la
    `direccion`, que puede ser LATERAL. La función no guarda estado.
    `hoy` (fecha ISO de Santiago) activa la regla de `fecha_barra` del consumo.
    """
    if previa is not None and previa not in (ALCISTA, BAJISTA):
        raise ValueError(f"previa tiene que ser ALCISTA o BAJISTA (el eje2), no {previa!r}")
    u = umbrales()
    dia = eje_dia(h1, previa)
    p = posicion_canal(h1)
    adx = _num(h1, "adx_14")
    fondo = eje_fondo(d1)
    consumo = consumo_diario(d1, hoy)
    sin_rec = consumo is not None and consumo >= u["consumo_sin_recorrido"]
    ejes: dict[str, Any] = {"fondo": fondo, "dia": dia, "p": p, "adx": adx, "consumo": consumo}

    def lectura(direccion: str, conviccion: str | None, fase: str) -> LecturaDireccion:
        return LecturaDireccion(
            direccion=direccion, conviccion=conviccion, fase=fase,
            sin_recorrido=sin_rec, eje2=dia,
            motivo=_motivo(direccion, fase, fondo, sin_rec), ejes=ejes,
        )

    faltan = _faltantes(h1, d1, p)
    if faltan:                                                     # rama 0
        ejes["faltan"] = faltan
        return lectura(dia, "debil", "datos_incompletos")
    if adx < u["adx_rango"] and u["p_rango_min"] <= p <= u["p_rango_max"]:   # rama 1
        return lectura(LATERAL, None, "rango")
    if fondo == TRANSICION:                                        # rama 4
        return lectura(dia, "debil", "sin_ancla")
    if fondo == dia:                                               # rama 2
        if adx >= u["adx_fuerza"]:
            conviccion = "fuerte" if canal_confirma(dia, p) else "moderada"
        elif adx >= u["adx_rango"]:
            conviccion = "moderada"
        else:
            conviccion = "debil"
        return lectura(dia, conviccion, "tendencia_alineada")
    if adx >= u["adx_fuerza"]:                                     # rama 3a
        return lectura(dia, "moderada", "correccion_con_fuerza")
    return lectura(fondo, "debil", "correccion")                   # rama 3b
```

- [ ] **Step 4: Verificar que pasan**

Run: `uv run pytest tests/test_direccion_gi.py -v`
Expected: PASS en todos. Si falla `test_ningun_numero_del_arbol_esta_escrito_en_el_codigo`, hay un número escrito a mano, y se mueve al config.

- [ ] **Step 5: Commit**

```bash
git add scripts/direccion_gi.py tests/test_direccion_gi.py
git commit -m "feat(direccion): arbol de cuatro ejes con conviccion, fase y motivo de cliente

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Sombra en el escáner

**Files:**
- Modify: `scripts/screener_gi.py`, en el bloque de imports (~línea 63), en `evaluar_activo` (~674-748) y en `escanear` (~857-1000)
- Test: `tests/test_screener_gi.py` y `tests/test_pipeline_carrusel.py`

**Interfaces:**
- Consumes: `direccion_gi.leer_direccion(h1, d1, hoy=...)` y `direccion_gi.a_dict`.
- Produces:
  - `screener_gi._direccion_en_sombra(h1: dict, d1: dict, ahora_santiago: datetime) -> dict`, que devuelve la lectura serializada o `{"error": "<Tipo>: <mensaje>"}`
  - `screener_gi.avisos_de_sombra(evaluados: list[dict]) -> list[str]`
  - El campo `direccion_4ejes` en cada resultado evaluado de `evaluar_activo`

- [ ] **Step 1: Escribir los tests que fallan**

Se agregan a `tests/test_screener_gi.py`, después de las fábricas:

```python
# ─────────────────────────────────────────────────────────────────────────────
# Dirección de cuatro ejes en sombra: se calcula, no decide nada
# ─────────────────────────────────────────────────────────────────────────────
def _evaluar(h1=None, d1=None):
    return sc.evaluar_activo(
        ACTIVO, [], delta_ust_bps=None,
        ahora_santiago=AHORA.astimezone(sc.SANTIAGO),
        analizador=analizador_falso(h1 or h1_perfecto(), d1 or d1_con_consumo(0.30)),
    )


def test_la_sombra_viaja_en_el_resultado():
    res = _evaluar()
    assert res["direccion_4ejes"]["direccion"] in {"ALCISTA", "BAJISTA", "LATERAL"}
    assert res["direccion_4ejes"]["fase"]


def test_la_sombra_es_inerte(monkeypatch):
    """Con la lectura nueva cambiada o rota, todo lo demás es idéntico."""
    base = _evaluar()
    monkeypatch.setattr(sc.dg, "leer_direccion", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("roto")))
    roto = _evaluar()
    assert roto["direccion_4ejes"] == {"error": "RuntimeError: roto"}
    sin_sombra = lambda r: {k: v for k, v in r.items() if k != "direccion_4ejes"}  # noqa: E731
    assert sin_sombra(roto) == sin_sombra(base)
    assert roto["direccion"] == sc.direccion_tecnica(h1_perfecto())


def test_avisos_de_sombra_solo_cuando_difieren_o_falla():
    iguales = {"ticker": "A", "direccion": "ALCISTA", "direccion_4ejes": {"direccion": "ALCISTA", "fase": "tendencia_alineada"}}
    distinto = {"ticker": "B", "direccion": "ALCISTA", "direccion_4ejes": {"direccion": "LATERAL", "fase": "rango"}}
    fallo = {"ticker": "C", "direccion": "BAJISTA", "direccion_4ejes": {"error": "ValueError: x"}}
    avisos = sc.avisos_de_sombra([iguales, distinto, fallo])
    assert len(avisos) == 2
    assert avisos[0].startswith("B:") and "LATERAL" in avisos[0] and "ALCISTA" in avisos[0]
    assert avisos[1].startswith("C:") and "ValueError" in avisos[1]
    assert all("—" not in a and "–" not in a for a in avisos)


def test_escanear_reporta_la_diferencia_de_la_sombra():
    h1 = dict(h1_perfecto(), adx_14=15.0, donchian_50_high=105.0, donchian_50_low=95.0)  # p = 0,5: rango

    def fake(ticker, tf):
        res = dict(h1 if tf == "H1" else d1_con_consumo(0.30))
        res["ticker"] = ticker
        return res

    resultado = sc.escanear(tanda=1, top=1, solo_renderizables=True, analizador=fake)
    assert any("sombra 4 ejes dice LATERAL" in a for a in resultado["avisos"])
```

Se agrega a `tests/test_pipeline_carrusel.py`:

```python
def test_la_direccion_en_sombra_no_entra_al_payload():
    """Fase 1: la lectura de cuatro ejes viaja en la selección y el payload la ignora."""
    con_sombra = {**SELECCION, "direccion_4ejes": {"direccion": "LATERAL", "fase": "rango"}}
    assert payload_de_prueba(con_sombra) == payload_de_prueba()
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_screener_gi.py -k sombra -v`
Expected: FAIL con `KeyError: 'direccion_4ejes'` o `AttributeError: module 'screener_gi' has no attribute 'dg'`. El test del carrusel ya puede pasar, porque `construir_payload` no copia claves desconocidas. Se deja igual, porque protege contra una regresión.

- [ ] **Step 3: Implementar la sombra**

En `scripts/screener_gi.py`, justo después de `import agenda_mercado as agenda  # noqa: E402 ...`:

```python
import direccion_gi as dg  # noqa: E402  (fase 1: solo en sombra)
```

Antes de `def evaluar_activo(`:

```python
def _direccion_en_sombra(
    h1: dict[str, Any], d1: dict[str, Any], ahora_santiago: datetime
) -> dict[str, Any]:
    """La dirección de cuatro ejes, **en sombra**: se calcula y se guarda, no decide.

    Fase 1 del spec `2026-09-28-direccion-4-ejes-design.md`: la `direccion` que
    puntúa, pinta el chip y alimenta el guardia de divergencia sigue siendo
    `direccion_tecnica`. Si la lectura nueva lanza, se anota y la tanda sigue:
    la sombra nunca tumba la tanda. Se llama con `previa=None` a propósito,
    porque el escáner no guarda estado entre corridas.
    """
    try:
        lectura = dg.leer_direccion(h1, d1, hoy=ahora_santiago.date().isoformat())
        return dg.a_dict(lectura)
    except Exception as exc:  # noqa: BLE001
        return {"error": f"{type(exc).__name__}: {exc}"}


def avisos_de_sombra(evaluados: list[dict[str, Any]]) -> list[str]:
    """Una línea por activo donde la sombra difiere de la EMA 50, o falló."""
    avisos: list[str] = []
    for r in evaluados:
        sombra = r.get("direccion_4ejes") or {}
        if "error" in sombra:
            avisos.append(
                f"{r['ticker']}: la direccion de 4 ejes (sombra) fallo ({sombra['error']}); "
                "la tanda sigue con la EMA 50"
            )
        elif sombra.get("direccion") and sombra["direccion"] != r.get("direccion"):
            avisos.append(
                f"{r['ticker']}: sombra 4 ejes dice {sombra['direccion']} "
                f"({sombra.get('fase')}) y la EMA 50 dice {r.get('direccion')}"
            )
    return avisos
```

En `evaluar_activo`, entre el bloque `motivo = gate_banda(h1)` y `t, det_t = factor_tecnico(...)`:

```python
    sombra = _direccion_en_sombra(h1, d1, ahora_santiago)
```

En el `return` final de `evaluar_activo`, justo después de `"direccion": direccion,`:

```python
        # Fase 1: la lectura de cuatro ejes viaja al lado y nadie la consume.
        "direccion_4ejes": sombra,
```

En `escanear`, justo después de `evaluados.sort(key=lambda r: (-r["score"], r["ticker"]))`:

```python
    avisos.extend(avisos_de_sombra(evaluados))
```

- [ ] **Step 4: Verificar que pasan, junto con la suite del escáner y del carrusel**

Run: `uv run pytest tests/test_screener_gi.py tests/test_pipeline_carrusel.py -v`
Expected: PASS en todos. Los tests que ya existían no cambian. Si alguno compara el dict completo de `evaluar_activo`, se ajusta para excluir `direccion_4ejes` y se deja anotado en el commit.

- [ ] **Step 5: Commit**

```bash
git add scripts/screener_gi.py tests/test_screener_gi.py tests/test_pipeline_carrusel.py
git commit -m "feat(screener): direccion de cuatro ejes en sombra, sin tocar lo que sale al cliente

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Medición — carga, sellos y zona horaria

**Files:**
- Create: `scripts/medir_direccion.py`
- Test: `tests/test_medir_direccion.py`

**Interfaces:**
- Consumes:
  - `guardrails.cuenta.cuenta_correcta(login, ubicacion=...) -> Veredicto`, con `.ok` y `.detalle`
  - `config/direccion.json` (bloque `medicion`)
- Produces:
  - `MedicionAbortada(RuntimeError)`
  - `cfg_medicion() -> dict`, que devuelve el bloque `medicion` crudo
  - `valor(clave: str) -> Any`
  - `cargar_serie(simbolo: str, marco: str, directorio: Path = DIR_SERIES) -> tuple[pd.DataFrame, dict]`. El DataFrame trae las columnas `time` (naive, Santiago), `open`, `high`, `low`, `close` y `tick_volume`, ordenadas y con índice 0..n-1. El dict es la metadata sin `rows`.
  - `localizar(df) -> pd.DataFrame`: copia con la columna `time_ny` (aware NY; `NaT` en horas ambiguas o inexistentes de Santiago)
  - `prueba_hora_extraccion(df, meta) -> dict`, con las claves `aplica`, `ok` y `detalle`
  - `prueba_moda_volumen(df_localizado) -> dict`, con las claves `ok`, `hora` y `horas_por_mes`
  - `verificar_zona(cargadas: dict[str, tuple[pd.DataFrame, dict]], serie_moda: str) -> dict`, que lanza `MedicionAbortada` si falla

- [ ] **Step 1: Escribir los tests que fallan**

```python
"""Contrato de la medición de la dirección de cuatro ejes.

Todo sintético: la suite no puede depender de las series en disco, que están
gitignoradas.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))

import medir_direccion as md  # noqa: E402

NY = ZoneInfo("America/New_York")
SCL = ZoneInfo("America/Santiago")


def serie_h1(inicio_utc: datetime, horas: int, *, rotulo: str = "santiago",
             pico_ny: int = 10, paso: float = 0.01) -> pd.DataFrame:
    """Velas H1 de lunes a viernes (NY), con el pico de volumen a `pico_ny`.

    `rotulo="santiago"` estampa la hora local de Santiago, como hacen las series
    reales; `rotulo="utc"` estampa UTC, que es lo que el sello dice y no es.
    """
    filas = []
    for k in range(horas):
        utc = inicio_utc + timedelta(hours=k)
        ny = utc.astimezone(NY)
        if ny.weekday() >= 5:
            continue
        stamp = (utc.astimezone(SCL) if rotulo == "santiago" else utc).replace(tzinfo=None)
        c = 100.0 + paso * k
        filas.append({"time": stamp, "open": c, "high": c + 0.5, "low": c - 0.5, "close": c,
                      "tick_volume": 1000 if ny.hour == pico_ny else 100})
    return pd.DataFrame(filas)


def escribir_serie(directorio: Path, simbolo: str, marco: str, df: pd.DataFrame, **meta) -> None:
    datos = {"symbol": simbolo, "timeframe": marco, "source": "MT5", "broker": "MT5",
             "cuenta": 51492, "timezone": "UTC", "as_of_utc": "2026-09-28T08:20:00+00:00"}
    datos.update(meta)
    filas = df.assign(time=df["time"].dt.strftime("%Y-%m-%dT%H:%M:%S")).to_dict("records")
    datos["rows"] = filas
    (directorio / f"{simbolo}_{marco}.json").write_text(json.dumps(datos), encoding="utf-8")


# ── Sellos ──────────────────────────────────────────────────────────────────
def test_cargar_serie_ordena_y_tipa(tmp_path):
    df = serie_h1(datetime(2025, 3, 3, 12, tzinfo=timezone.utc), 30)
    escribir_serie(tmp_path, "XAUUSD", "H1", df.iloc[::-1])
    cargada, meta = md.cargar_serie("XAUUSD", "H1", tmp_path)
    assert cargada["time"].is_monotonic_increasing
    assert list(cargada.index) == list(range(len(cargada)))
    assert meta["cuenta"] == 51492 and "rows" not in meta


@pytest.mark.parametrize("cambio", [{"source": "YFINANCE"}, {"broker": "YFINANCE"},
                                    {"cuenta": 51256}, {"cuenta": None}])
def test_serie_que_no_salio_de_mt5_o_de_la_cuenta_aborta(tmp_path, cambio):
    escribir_serie(tmp_path, "XAUUSD", "H1", serie_h1(datetime(2025, 3, 3, 12, tzinfo=timezone.utc), 30), **cambio)
    with pytest.raises(md.MedicionAbortada):
        md.cargar_serie("XAUUSD", "H1", tmp_path)


# ── Zona horaria ────────────────────────────────────────────────────────────
def test_localizar_descarta_horas_ambiguas_e_inexistentes():
    df = pd.DataFrame({"time": pd.to_datetime([
        "2025-04-05 22:00", "2025-04-05 23:00", "2025-04-05 23:00",   # abril: 23:00 se repite
        "2025-04-06 00:00", "2025-09-06 23:00", "2025-09-07 00:00",   # septiembre: 00:00 no existe
        "2025-09-07 01:00"])})
    loc = md.localizar(df)
    assert loc["time_ny"].isna().tolist() == [False, True, True, False, False, True, False]
    assert len(loc) == len(df)                      # marca, no borra


def test_la_serie_en_hora_de_santiago_pasa_las_dos_pruebas():
    inicio = datetime(2025, 1, 6, 5, tzinfo=timezone.utc)
    df = serie_h1(inicio, 24 * 360, rotulo="santiago")
    ultima_utc = inicio + timedelta(hours=24 * 360 - 1)
    meta = {"as_of_utc": (ultima_utc + timedelta(minutes=20)).isoformat()}
    assert md.prueba_moda_volumen(md.localizar(df))["ok"] is True
    assert md.prueba_moda_volumen(md.localizar(df))["hora"] == 10
    r = md.prueba_hora_extraccion(df, meta)
    assert r["aplica"] is True and r["ok"] is True


def test_la_misma_serie_rotulada_en_utc_falla_y_aborta():
    inicio = datetime(2025, 1, 6, 5, tzinfo=timezone.utc)
    df = serie_h1(inicio, 24 * 360, rotulo="utc")
    assert md.prueba_moda_volumen(md.localizar(df))["ok"] is False
    ultima_utc = inicio + timedelta(hours=24 * 360 - 1)
    meta = {"as_of_utc": (ultima_utc + timedelta(minutes=20)).isoformat()}
    with pytest.raises(md.MedicionAbortada):
        md.verificar_zona({"US100": (df, meta)}, "US100")


def test_serie_de_mercado_cerrado_no_entra_a_la_prueba_de_extraccion():
    df = serie_h1(datetime(2025, 3, 3, 12, tzinfo=timezone.utc), 30)   # termina el martes
    meta = {"as_of_utc": "2025-03-10T08:20:00+00:00"}                   # se extrajo el lunes siguiente
    assert md.prueba_hora_extraccion(df, meta)["aplica"] is False
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_medir_direccion.py -v`
Expected: ERROR de colección con `ModuleNotFoundError: No module named 'medir_direccion'`

- [ ] **Step 3: Implementar la carga y la zona**

```python
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
```

- [ ] **Step 4: Verificar que pasan**

Run: `uv run pytest tests/test_medir_direccion.py -v`
Expected: PASS en todos. El caso `cuenta=None` depende de que `cuenta_correcta` lea `config/cuenta_mt5.json` (login 51492).

- [ ] **Step 5: Commit**

```bash
git add scripts/medir_direccion.py tests/test_medir_direccion.py
git commit -m "feat(medicion): carga con sellos y verificacion de la zona horaria de Santiago

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Indicadores en serie, paridad y lecturas sin fuga

**Files:**
- Modify: `scripts/medir_direccion.py`
- Test: `tests/test_medir_direccion.py`

**Interfaces:**
- Consumes: `mt5_client.ema/atr/adx`, `direccion_gi.leer_direccion` y `direccion_gi.eje_dia`.
- Produces:
  - `indicadores(df) -> pd.DataFrame`, con las columnas `ema_50`, `ema_100`, `atr_14`, `adx_14`, `donchian_50_high` y `donchian_50_low`. El valor de la fila `i` incluye la vela `i`.
  - `rango_hoy_intradia(h1) -> pd.Series`, con el `max(high) − min(low)` de las velas H1 del mismo día de Santiago hasta la fila inclusive
  - `indice_d1_cerrado(h1_time, d1_time) -> np.ndarray`, que da, para cada fila H1, la posición del último D1 con fecha menor a la fecha de Santiago de esa fila (−1 si no hay)
  - `dicts_en(i, h1, ind_h1, rango, d1, ind_d1, j) -> tuple[dict, dict]`

- [ ] **Step 1: Escribir los tests que fallan**

```python
from market_data_mcp import analisis, mt5_client  # noqa: E402


def ohlc_aleatorio(n: int, semilla: int = 7) -> pd.DataFrame:
    rng = __import__("numpy").random.default_rng(semilla)
    c = 100 + rng.normal(0, 1, n).cumsum()
    t = pd.date_range("2025-03-03 08:00", periods=n, freq="h")
    return pd.DataFrame({"time": t, "open": c, "high": c + rng.uniform(0.1, 1, n),
                         "low": c - rng.uniform(0.1, 1, n), "close": c, "tick_volume": 100})


def test_paridad_con_analizar_activo(monkeypatch):
    """Leer la serie completa en t-1 da lo mismo que analizar_activo con df_closed."""
    df = ohlc_aleatorio(300)
    monkeypatch.setattr(mt5_client, "connect", lambda: None)
    monkeypatch.setattr(mt5_client, "get_rates", lambda ticker, tf, n_bars=300: df.copy())
    vivo = analisis.analizar_activo("XAUUSD", "H1")
    assert "error" not in vivo, vivo
    ind = md.indicadores(df).iloc[-2]                 # t-1: la última cerrada
    for campo in ("ema_50", "ema_100", "atr_14", "donchian_50_high", "donchian_50_low"):
        assert round(float(ind[campo]), 2) == vivo[campo], campo
    assert round(float(ind["adx_14"]), 1) == vivo["adx_14"]


def test_donchian_rodante_coincide_con_mt5_client():
    df = ohlc_aleatorio(200)
    alto, bajo, _ = mt5_client.donchian(df)
    ind = md.indicadores(df).iloc[-1]
    assert float(ind["donchian_50_high"]) == alto and float(ind["donchian_50_low"]) == bajo


def test_rango_hoy_no_ve_velas_posteriores_del_mismo_dia():
    df = pd.DataFrame({
        "time": pd.to_datetime(["2025-03-03 09:00", "2025-03-03 10:00", "2025-03-03 11:00", "2025-03-04 09:00"]),
        "high": [10.0, 12.0, 30.0, 5.0], "low": [9.0, 8.0, 1.0, 4.0],
    })
    assert md.rango_hoy_intradia(df).tolist() == [1.0, 4.0, 29.0, 1.0]


def test_d1_se_alinea_por_fecha_y_no_por_hora_localizada():
    """La vela D1 del 2025-09-07 tiene marca 00:00, que en Santiago no existe; no se pierde."""
    d1_time = pd.Series(pd.to_datetime(["2025-09-05", "2025-09-07", "2025-09-08"]))
    h1_time = pd.Series(pd.to_datetime(["2025-09-07 10:00", "2025-09-08 10:00", "2025-09-09 10:00"]))
    assert md.indice_d1_cerrado(h1_time, d1_time).tolist() == [0, 1, 2]


def test_lectura_en_t_no_cambia_si_se_altera_el_futuro():
    """Anti fuga: tocar las velas posteriores a t (H1 y D1 del día de t) no cambia la lectura de t."""
    h1 = ohlc_aleatorio(400)                                   # 2025-03-03 08:00 en adelante
    # D1 hasta el 2025-03-19: incluye el día de t (2025-03-15) y los siguientes
    d1 = ohlc_aleatorio(200, semilla=3).assign(time=pd.date_range("2024-09-01", periods=200, freq="D"))
    i = 300
    fecha_t = h1["time"].iloc[i].normalize()

    def leer(h1x, d1x):
        j = md.indice_d1_cerrado(h1x["time"], d1x["time"])[i]
        return md.dicts_en(i, h1x, md.indicadores(h1x), md.rango_hoy_intradia(h1x), d1x, md.indicadores(d1x), j)

    base = leer(h1, d1)
    h1_mod = h1.copy()
    h1_mod.loc[i + 1:, ["high", "low", "close"]] *= 3
    d1_mod = d1.copy()
    futuro_d1 = d1_mod["time"] >= fecha_t
    assert futuro_d1.sum() >= 2                         # el test sí toca el D1 del día de t
    d1_mod.loc[futuro_d1, ["high", "low", "close"]] *= 3
    assert leer(h1_mod, d1_mod) == base
    h1d, d1d = base
    assert h1d["price"] == float(h1["close"].iloc[i])
    assert d1d["fecha_barra"] == fecha_t.date().isoformat()
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_medir_direccion.py -v`
Expected: FAIL con `AttributeError: module 'medir_direccion' has no attribute 'indicadores'`

- [ ] **Step 3: Implementar**

Se agrega a `scripts/medir_direccion.py`:

```python
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
    """
    return pd.DataFrame({
        "ema_50": ema(df["close"], 50),
        "ema_100": ema(df["close"], 100),
        "atr_14": atr(df, 14),
        "adx_14": adx(df, 14),
        "donchian_50_high": df["high"].rolling(50).max(),
        "donchian_50_low": df["low"].rolling(50).min(),
    }, index=df.index)
```

> Los períodos 50, 100, 14 y 50 son los de `analizar_activo` (`analisis.py:227-236`) y no umbrales del árbol, así que quedan escritos acá igual que allá. El test de paridad los ata.

```python
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
```

- [ ] **Step 4: Verificar que pasan**

Run: `uv run pytest tests/test_medir_direccion.py -v`
Expected: PASS en todos. Si la paridad del ADX falla por redondeo en el último decimal, **no se relaja la tolerancia**: se revisa primero que `indicadores` use `df` completo, igual que `adx(df_closed)` usa todas las columnas.

- [ ] **Step 5: Commit**

```bash
git add scripts/medir_direccion.py tests/test_medir_direccion.py
git commit -m "feat(medicion): indicadores en serie con paridad y lecturas sin fuga del futuro

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Instantes que votan, métricas y giros

**Files:**
- Modify: `scripts/medir_direccion.py`
- Test: `tests/test_medir_direccion.py`

**Interfaces:**
- Consumes: todo lo anterior, más `agenda.momentos()` y `agenda.tandas()`.
- Produces:
  - `ventana_votante(clase: str) -> tuple[int, int]`, que da los minutos NY del cierre de vela, de inicio y de fin, inclusive
  - `lecturas(h1, d1, clase) -> pd.DataFrame`. Tiene una fila por instante medible, con estas columnas:
    - `t_ny` y `dia`
    - `en_sesion`, `vota` y `motivo`
    - `h` y `m`
    - `modelo`, `conviccion` y `fase`
    - `ema50` (sin histéresis, la de hoy) y `ema50_hist` (con la misma histéresis)
  - `acierta(direccion: str, m: float) -> bool`
  - `contar_giros(direcciones: Iterable[str]) -> int`
  - `ic_por_dia(por_dia: pd.DataFrame, f: Callable[[dict], float]) -> tuple[float, float]`
  - `resumir(lec: pd.DataFrame) -> dict`, con las claves:
    - `n_votos` y `n_dias`
    - `c1`, un dict con `acierto_modelo`, `acierto_ema50`, `diferencia` e `ic`
    - `c2`, un dict con `acierto_ema50_lateral`, `acierto_ema50_resto`, `diferencia`, `ic`, `mediana_m_lateral`, `mediana_m_direccional` y `n_lateral`
    - `c3`, un dict con `giros_modelo_100` y `giros_ema50_100`
    - `c4`, un dict `{conviccion: acierto}`

> **Qué EMA 50 compite en cada condición.** En la condición 1 (acierto), la EMA 50 **sin** histéresis, que es la que hoy sale al cliente. En la condición 3 (giros), la EMA 50 **con la misma histéresis de 0,25 ATR**, como exige el spec, para que el modelo no gane por la histéresis. El modelo encadena `previa = lectura.eje2` a lo largo de toda la serie, en orden.

- [ ] **Step 1: Escribir los tests que fallan**

```python
import numpy as np  # noqa: E402


def test_ventana_sale_de_la_agenda_por_clase():
    assert md.ventana_votante("forex_commodities") == (8 * 60, 16 * 60)
    assert md.ventana_votante("indices") == (10 * 60, 16 * 60)
    with pytest.raises(md.MedicionAbortada):
        md.ventana_votante("clase_inventada")


def test_giros():
    assert md.contar_giros(["ALCISTA", "LATERAL", "ALCISTA"]) == 0
    assert md.contar_giros(["ALCISTA", "LATERAL", "BAJISTA"]) == 1
    assert md.contar_giros(["ALCISTA", "BAJISTA", "ALCISTA"]) == 2
    assert md.contar_giros([]) == 0


def test_acierta():
    assert md.acierta("ALCISTA", 0.5) and md.acierta("BAJISTA", -0.1)
    assert not md.acierta("ALCISTA", 0.0) and not md.acierta("BAJISTA", 0.0)
    assert not md.acierta("LATERAL", 1.0)


def _serie_mercado(dias: int, pendiente: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """H1 en hora de Santiago con tendencia lineal conocida, y su D1 derivado."""
    h1 = serie_h1(datetime(2024, 1, 8, 5, tzinfo=timezone.utc), 24 * dias, paso=pendiente)
    d1 = (h1.assign(fecha=h1["time"].dt.normalize())
            .groupby("fecha").agg(open=("open", "first"), high=("high", "max"),
                                  low=("low", "min"), close=("close", "last"),
                                  tick_volume=("tick_volume", "sum"))
            .reset_index().rename(columns={"fecha": "time"}))
    return h1, d1


def test_metrica_m_anti_fuga_da_el_valor_esperado():
    """Serie lineal: m = (close[t+4] - close[t]) / ATR[t-1], y el modelo acierta siempre al alza."""
    h1, d1 = _serie_mercado(260, 0.01)
    lec = md.lecturas(h1, d1, "forex_commodities")
    votos = lec[lec["vota"]]
    assert len(votos) > 0
    ind = md.indicadores(h1)
    fila = votos.iloc[0]
    i = int(fila.name)
    esperado = (h1["close"].iat[i + 4] - h1["close"].iat[i]) / ind["atr_14"].iat[i - 1]
    assert fila["m"] == pytest.approx(esperado)
    assert (votos["ema50"] == "ALCISTA").all()


def test_horizonte_con_hueco_no_vota():
    """Si falta una vela dentro del horizonte, t+4 cae 5 horas después: no se mide ese m."""
    h1, d1 = _serie_mercado(260, 0.01)
    lec = md.lecturas(h1, d1, "forex_commodities")
    fila = lec[lec["vota"]].iloc[5]
    i = int(fila.name)
    con_hueco = h1.drop(index=i + 2).reset_index(drop=True)   # la vela t+2 desaparece
    lec2 = md.lecturas(con_hueco, d1, "forex_commodities")
    misma = lec2[lec2["t_ny"] == fila["t_ny"]].iloc[0]
    assert not misma["vota"]
    assert misma["motivo"] == "horizonte_con_hueco"


def test_indices_cortan_al_cierre_y_exigen_tres_horas():
    h1, d1 = _serie_mercado(260, 0.01)
    lec = md.lecturas(h1, d1, "indices")
    en = lec[lec["en_sesion"]]
    cierre = (en["t_ny"] + pd.Timedelta(hours=1)).dt.hour
    assert (en.loc[cierre == 13, "h"] == 3).all() and en.loc[cierre == 13, "vota"].all()
    assert (en.loc[cierre == 14, "motivo"] == "horizonte_corto").all()
    assert not en.loc[cierre == 9].shape[0]            # antes de las 10:00 no está en sesión


def test_ic_por_dia_agrupa_y_es_reproducible():
    por_dia = pd.DataFrame({"a": [1.0, 0.0, 1.0, 1.0], "n": [1.0, 1.0, 1.0, 1.0]})
    ic1 = md.ic_por_dia(por_dia, lambda s: s["a"] / s["n"])
    ic2 = md.ic_por_dia(por_dia, lambda s: s["a"] / s["n"])
    assert ic1 == ic2 and 0.0 <= ic1[0] <= 0.75 <= ic1[1] <= 1.0


def test_resumir_trae_las_cuatro_condiciones():
    h1, d1 = _serie_mercado(260, 0.01)
    r = md.resumir(md.lecturas(h1, d1, "forex_commodities"))
    assert r["n_votos"] > 0 and r["n_dias"] > 0
    assert set(r) >= {"c1", "c2", "c3", "c4"}
    assert r["c1"]["acierto_modelo"] == pytest.approx(100.0)
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_medir_direccion.py -v`
Expected: FAIL con `AttributeError: module 'medir_direccion' has no attribute 'ventana_votante'`

- [ ] **Step 3: Implementar**

```python
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


def lecturas(h1: pd.DataFrame, d1: pd.DataFrame, clase: str) -> pd.DataFrame:
    """Una fila por instante H1 medible, en orden, con su lectura y su futuro."""
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
            filas.append({"i": i, "t_ny": t_ny.iat[i], "dia": t_ny.iat[i].date().isoformat(),
                          "en_sesion": False, "vota": False, "motivo": "sin_historia_d1",
                          "h": 0, "m": float("nan"), "modelo": None, "conviccion": None,
                          "fase": None, "ema50": None, "ema50_hist": None})
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
            if pd.isna(destino) or destino - t_ny.iat[i] != pd.Timedelta(hours=h):
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
        sub = v[v["conviccion"] == conv]
        sub = sub[sub["dir"]]
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
```

> **Nota para quien implemente.** En c2, "el resto" son las velas con dirección del modelo, y la EMA 50 se mide en esas mismas velas. Esa es la comparación del spec: la EMA 50 en las velas LATERAL contra la EMA 50 en las que el modelo sí dio dirección.

- [ ] **Step 4: Verificar que pasan**

Run: `uv run pytest tests/test_medir_direccion.py -v`
Expected: PASS en todos. `test_indices_cortan_al_cierre_y_exigen_tres_horas` usa velas cuyo cierre cae a las 13:00 (h = 3, vota) y a las 14:00 (h = 2, `horizonte_corto`).

- [ ] **Step 5: Commit**

```bash
git add scripts/medir_direccion.py tests/test_medir_direccion.py
git commit -m "feat(medicion): instantes que votan, metricas por condicion y bootstrap agrupado por dia

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Regla de adopción, informe y CLI; corrida real

**Files:**
- Modify: `scripts/medir_direccion.py`
- Test: `tests/test_medir_direccion.py`
- Create (salida): `docs/mediciones/direccion-4-ejes.md` y `docs/mediciones/direccion-4-ejes.json`

**Interfaces:**
- Consumes: `resumir`, `verificar_zona`, `cargar_serie` y `lecturas`.
- Produces:
  - `evaluar_adopcion(total: dict, por_activo: dict[str, dict]) -> dict`, con las claves `c1`, `c2`, `c3`, `c4`, `disidentes`, `sin_voto` y `adopta`
  - `medir(series: list[str] | None = None, directorio: Path = DIR_SERIES) -> dict`
  - `escribir_informe(resultado: dict, salida: Path) -> tuple[Path, Path]`
  - `main(argv: list[str] | None = None) -> int`, que devuelve 0 si midió (se adopte o no) y 2 si la medición se abortó

- [ ] **Step 1: Escribir los tests que fallan**

```python
def _resumen(n=1000, c1=(55.0, 54.0, 1.0, (-0.5, 2.5)), c2_ic=(-8.0, -2.0),
             med=(0.4, 0.9), giros=(3.0, 5.0), c4=(50.0, 54.0, 58.0)):
    return {
        "n_votos": n, "n_dias": 100,
        "c1": {"acierto_modelo": c1[0], "acierto_ema50": c1[1], "diferencia": c1[2], "ic": c1[3]},
        "c2": {"ic": c2_ic, "mediana_m_lateral": med[0], "mediana_m_direccional": med[1], "n_lateral": 50},
        "c3": {"giros_modelo_100": giros[0], "giros_ema50_100": giros[1]},
        "c4": dict(zip(("debil", "moderada", "fuerte"), c4)),
    }


def test_adopta_si_cumple_1_2_y_3():
    r = md.evaluar_adopcion(_resumen(), {"XAUUSD": _resumen()})
    assert r["adopta"] is True and r["c4"] is True and r["disidentes"] == []


@pytest.mark.parametrize("cambio, condicion", [
    ({"c1": (50.0, 52.0, -2.0, (-3.5, -0.5))}, "c1"),     # límite inferior bajo -1
    ({"c2_ic": (-5.0, 0.5)}, "c2"),                       # la EMA 50 no acierta menos en LATERAL
    ({"med": (1.0, 0.9)}, "c2"),                          # LATERAL no aparta ruido
    ({"giros": (5.0, 5.0)}, "c3"),                        # empate no alcanza
])
def test_no_adopta_si_falla_una_condicion(cambio, condicion):
    r = md.evaluar_adopcion(_resumen(**cambio), {})
    assert r[condicion] is False and r["adopta"] is False


def test_conviccion_solo_si_ordena():
    assert md.evaluar_adopcion(_resumen(c4=(55.0, 54.0, 58.0)), {})["c4"] is False
    assert md.evaluar_adopcion(_resumen(c4=(50.0, None, 58.0)), {})["c4"] is False


def test_disidentes_y_activos_sin_voto():
    por_activo = {
        "XAUUSD": _resumen(c1=(50.0, 53.0, -3.0, (-5.0, -1.0))),      # 1000 votos, 3 pts bajo: disidente
        "WTI": _resumen(c1=(52.0, 53.5, -1.5, (-3.0, 0.0))),          # 1,5 pts bajo: no alcanza
        "BRENT": _resumen(n=300, c1=(40.0, 55.0, -15.0, (-20.0, -10.0))),  # < 500: no vota
    }
    r = md.evaluar_adopcion(_resumen(), por_activo)
    assert r["disidentes"] == ["XAUUSD"]
    assert r["sin_voto"] == ["BRENT"]


def test_medir_carga_us100_aunque_no_se_pida(tmp_path, monkeypatch):
    """La prueba de zona necesita el US100: se carga aunque --series no lo nombre."""
    assert md._series_a_cargar(["XAUUSD"]) == ["XAUUSD", "US100"]
    assert md._series_a_cargar(["US100"]) == ["US100"]
    pedidas = []

    def espia(simbolo, marco, directorio=md.DIR_SERIES):
        pedidas.append((simbolo, marco))
        return pd.DataFrame(columns=md.COLUMNAS), {}

    def zona_que_corta(cargadas, serie_moda):
        raise md.MedicionAbortada(f"corte del test con {sorted(cargadas)}")

    monkeypatch.setattr(md, "cargar_serie", espia)
    monkeypatch.setattr(md, "verificar_zona", zona_que_corta)
    with pytest.raises(md.MedicionAbortada, match="US100"):
        md.medir(["XAUUSD"], tmp_path)
    assert ("US100", "H1") in pedidas and ("XAUUSD", "H1") in pedidas
    assert ("US100", "D1") not in pedidas               # se carga para la prueba, no se mide


def test_main_devuelve_2_si_aborta(monkeypatch, capsys):
    monkeypatch.setattr(md, "medir", lambda *a, **k: (_ for _ in ()).throw(md.MedicionAbortada("x")))
    assert md.main([]) == 2
    assert "MEDICION ABORTADA" in capsys.readouterr().err


def test_informe_se_escribe_en_utf8_sin_guion_largo(tmp_path):
    resultado = {
        "generado": "2026-09-28 10:00", "zona": {"extraccion": {}, "moda_volumen": {}},
        "por_activo": {"XAUUSD": {**_resumen(), "descartes": {"fuera_de_sesion": 3}, "paridad_ema100_atr": 0.01,
                                  "fuera_de_sesion": _resumen(n=40)}},
        "total": _resumen(), "adopcion": md.evaluar_adopcion(_resumen(), {"XAUUSD": _resumen()}),
    }
    md_path, js_path = md.escribir_informe(resultado, tmp_path)
    texto = md_path.read_text(encoding="utf-8")
    assert "Adopción" in texto and "XAUUSD" in texto
    assert "—" not in texto and "–" not in texto
    json.loads(js_path.read_text(encoding="utf-8"))
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_medir_direccion.py -v`
Expected: FAIL con `AttributeError: module 'medir_direccion' has no attribute 'evaluar_adopcion'`

- [ ] **Step 3: Implementar la adopción, `medir`, el informe y `main`**

```python
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
    c4 = all(x is not None for x in c4v) and c4v[0] < c4v[1] < c4v[2]
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
    por_activo: dict[str, dict[str, Any]] = {}
    lecs: list[pd.DataFrame] = []
    for s in medibles:
        h1, _ = h1s[s]
        d1, _ = cargar_serie(s, "D1", directorio)
        lec = lecturas(h1, d1, cfg_medicion()["series"][s]["clase"])
        resumen = resumir(lec)
        resumen["descartes"] = lec["motivo"].value_counts().to_dict() if len(lec) else {}
        resumen["descartes"]["hora_ambigua"] = int(localizar(h1)["time_ny"].isna().sum())
        fuera = lec[~lec["en_sesion"] & lec["m"].notna()].assign(vota=True) if len(lec) else lec
        resumen["fuera_de_sesion"] = resumir(fuera)
        resumen["paridad_ema100_atr"] = _paridad_ema100(h1)
        por_activo[s] = resumen
        if resumen["n_votos"] >= int(valor("min_instantes_voto")):
            lecs.append(lec)
    total = resumir(pd.concat(lecs)) if lecs else {"n_votos": 0, "n_dias": 0}
    return {
        "generado": datetime.now(SANTIAGO).strftime("%Y-%m-%d %H:%M"),
        "zona": zona, "por_activo": por_activo, "total": total,
        "adopcion": evaluar_adopcion(total, por_activo),
    }
```

> **Por qué el total concatena sin reindexar.** `resumir` agrupa por `dia`, que es la fecha NY, y no por índice. Así los días de distintos activos que caen la misma fecha quedan en el mismo grupo del bootstrap, que es lo conservador: esas velas tampoco son independientes entre sí. La giro-cuenta del total recorre activos pegados uno tras otro, y la unión entre dos activos puede sumar a lo sumo un giro por activo, cosa despreciable frente a miles de instantes. El informe da los giros por activo, que son los exactos.

```python
def _json(o: Any) -> Any:
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.bool_,)):
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
```

Además, `test_medir_carga_us100_aunque_no_se_pida` exige que `medir` pase por `_series_a_cargar`. La implementación de arriba ya lo hace.

- [ ] **Step 4: Verificar que pasan**

Run: `uv run pytest tests/test_medir_direccion.py -v`
Expected: PASS en todos.

- [ ] **Step 5: Correr la suite completa**

Run: `uv run pytest -q`
Expected: todo en verde, más los tests nuevos. Si algo que ya existía se pone rojo, se detiene la tarea y se diagnostica antes de seguir.

- [ ] **Step 6: Correr la medición real**

Run: `uv run python scripts/medir_direccion.py`
Expected: imprime `Informe: ...docs/mediciones/direccion-4-ejes.md` y el veredicto, con salida 0. Si sale con 2, **no se toca ningún umbral**: se lee el motivo (sellos o zona), se reporta al director y se detiene.

Después se abre el `.md` y se revisan cuatro cosas:
- que el pico de volumen del US100 salga a las 10:00 NY en 23 meses o más;
- que los descartes de `hora_ambigua` sean pocos, del orden de un par por año por serie;
- que BRENT aparezca en `sin_voto`;
- que la paridad de la EMA 100 quede bajo 0,1 ATR. Si no, se anota en el informe, porque cambia cómo leer la fase 2.

- [ ] **Step 7: Commit del código y del resultado**

```bash
git add scripts/medir_direccion.py tests/test_medir_direccion.py docs/mediciones/direccion-4-ejes.md docs/mediciones/direccion-4-ejes.json
git commit -m "feat(medicion): regla de adopcion, informe y primera corrida sobre la historia real

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 8: Reportar al director**

Se le lleva el veredicto con los números de las condiciones 1 a 4, los disidentes y los activos sin voto, tal como salieron. **No se escribe el spec de la fase 2** hasta que el director vea el informe. Si el modelo no se adopta, eso también es un resultado: la EMA 50 queda y la sombra se puede retirar o dejar en observación, según decida el director.

---

## Fuera de este plan (el spec lo deja afuera o lo remite aparte)

- Abrir el issue del sello `"timezone": "UTC"` falso (§5.4). Es una acción hacia afuera, así que se le propone al director al cerrar y no se abre desde el plan.
- Todo el §8 del spec: que el chip, el guardia de divergencia, el informe o el `Score_GI` consuman la lectura; la pieza de rango; unificar `trend`; el estado de la histéresis en el escáner; y la capa de opinión experta.
