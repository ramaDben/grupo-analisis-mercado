# Enchufe de estrategia, fase 2: referencia semanal, escáner, carrusel y despacho

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** que el carrusel publique la `Lectura` de la estrategia activa (Tori), comparada a diario contra la referencia que fija el análisis semanal, y que el despacho la vuelva a pedir antes de enviar.

**Architecture:** la referencia semanal es infraestructura (`scripts/referencia_semanal.py`): guarda y lee la `Lectura` del lunes por activo y decide cuándo reemplazarla. El escáner (`screener_gi.escanear`) deja de puntuar con EMA/ADX/RSI/MACD y ordena con `estrategia.puntuar(seguir(...), "sesion")`. `pipeline_carrusel` arma el payload, el mensaje y el refresco desde la `Lectura`. Lo que todavía usan Avisos y el analista (S6 y S7) queda vivo y marcado como transitorio.

**Tech Stack:** Python 3.12, pandas, pytest, MetaTrader5 (solo en producción), `uv`.

**Spec:** `docs/superpowers/specs/2026-10-09-enchufe-estrategia-design.md` (§4 "La referencia semanal", §5, §6, §7 fase 2, §8, §9). Doctrina: `docs/metodologia-tendencias.md`. Mapa de sesiones: `docs/superpowers/plans/2026-10-09-enchufe-sesiones.md`.

## Global Constraints

- La estrategia no consume nada macro (spec §8.2). El calendario queda solo para el gate de blackout, que es infraestructura (spec §3).
- Feriado y blackout siguen siendo gates de infraestructura; agotamiento y banda salen del carrusel (spec §8.3).
- Texto de cliente: sin guion largo `—` ni medio `–`, tuteo chileno sin voseo, flechas ⬆️ ↔️ ⬇️, precios con los `digits` del activo (`formatear_precio`).
- La referencia se guarda en `data/referencias_semanales/<AAAA-Www>/<slug>.json` y se versiona (spec §4, "Dónde vive").
- Una referencia nunca se guarda en `PRUEBA`: se guarda con `en_curso=None`.
- `seguir()` se llama con velas pedidas con `extra=60` (sesiones.md, S4).
- Sin backtesting y sin tasa de acierto en ninguna pieza (spec §8.4).
- Commits con `git add` explícito, nunca `-a`. El árbol trae cambios ajenos (`data central/`, bitácoras).
- TDD: el test va primero; `uv run pytest` verde antes del PR, salvo los 4 de `tests/test_despacho_avisos.py`, que fallan en master desde el 2026-10-10 por la fecha y no son de esta fase.

## Decisiones del director para esta fase (2026-10-11)

1. **Si el lunes no corrió, la semanal corre sola** (spec §9). La primera corrida diaria de una semana sin `_semana.json` ejecuta el análisis semanal, guarda las referencias y sigue con la diaria. Lo dice en los avisos del escáner. Cubre también el lunes feriado.
2. **La cobertura fija gana sobre las exclusiones de Tori.** USDCLP, XAUUSD, WTI.spot y COPPER reciben referencia y pieza aunque `puntuar` los excluya (sin estructura, contra la secuencia). El motivo viaja en `gates_omitidos`, se dice en los avisos del escáner y la pieza lo lleva en una línea `⚠️ Ojo, …`.
3. **El refresco del despacho pasa a la `Lectura` en S4**, con `seguir()` y `divergencia()`. Si S4 se mergeara sin eso, el despacho volvería a pisar los niveles con `s1`/`r1` y el chip con la EMA 50: dos lecturas en la misma pieza. S5 queda con el gráfico y la purga.

## Decisiones de este plan (no las fija el spec)

- **Cuándo se reemplaza la referencia.** `referencia_semanal.debe_reemplazar(referencia, actual)` compara la *firma estructural* (rol, tipo, marco y anclas de cada línea). Si `seguir()` reasignó roles (ruptura) o volvió a trazar (ruptura falsa, que devuelve `leer()`), la firma cambia. También se reemplaza si el estado pasó a `RUPTURA` desde otro. Es independiente de la estrategia: no lee textos de aviso ni métricas de Tori.
- **La nueva referencia es `leer()` con las velas de hoy y `en_curso=None`**, guardada con motivo `"ruptura"`. El spec dice "la `leer()` de ese cierre"; la diaria que la detecta corre después de ese cierre, y las velas cerradas posteriores no cambian las anclas de una tesis recién rota (la regla de "sin mirar el futuro" la cubre la batería). La pieza de ese día publica la `seguir()`, que cuenta la ruptura contra la línea del lunes.
- **Si `seguir()` no puede evaluar** (las anclas salieron de la ventana), se reemplaza la referencia por la `leer()` de hoy y se avisa.
- **Cuántos activos fija el lunes:** por categoría (`forex`, `commodity`, `indice`, `accion`, `crypto`), los fijos más los mejores no fijos con `puntos > 0` y sin exclusión, hasta `top` (3), igual que la matriz de hoy. Así los canales cubiertos nunca quedan vacíos.
- **La semanal no aplica feriado ni blackout.** Son gates del día; la referencia es de la semana.
- **Las diarias cubren solo los activos de `_semana.json`** (spec §4, "Solo los activos del lunes"). El resto del universo no se evalúa, y el escáner dice cuántos quedaron fuera.
- **El marco de la pieza es el operativo de la estrategia** (H4 con Tori). El gráfico de la pieza se pide en ese marco desde S4, para que la imagen y la línea de temporalidad digan lo mismo; sus líneas pasan a ser las de la `Lectura` en S5.
- **La "volatilidad típica" de la pieza es el ATR 14 del marco operativo**, medido por infraestructura sobre las velas que ya se pidieron (`fuente.atr`). Reemplaza al `1,5 × ATR(H1)` del modelo ADC+ATR, que sale con el escáner viejo.
- **La justificación de temporalidad va en un campo nuevo, `notas_marco: {"H4": "…"}`**, en los 8 activos del universo cubierto. `nota_volatilidad` sigue existiendo porque Avisos y el analista todavía publican en H1 (S6/S7) y una nota de 4H en una pieza de 1H se contradice; S8 la borra.
- **Transitorio hasta S6/S7, marcado en el código:** `screener_gi.evaluar_activo` y sus factores y gates, `direccion_tecnica`, `_contexto_macro`, `pipeline_carrusel.construir_payload`, `refrescar_payload`, `divergencia_editorial`, `MARCOS_CANONICOS` y `TIMEFRAME_GRAFICO`. Los usan `pipeline_avisos.py` y `analista/{foco,preparar}.py`. El carrusel deja de usarlos en S4.
- **Se borra en S4** lo que solo usaba el escáner: la sombra de 4 ejes (`_direccion_en_sombra`, `avisos_de_sombra`, `direccion_4ejes`), `scripts/direccion_gi.py`, `scripts/medir_direccion.py`, `config/direccion.json` y sus tests; el parámetro `ignorar_agotamiento` de `escanear` y `--forzar`; las categorías del suplemento de los gates que salieron.

## Review Focus

1. **Una ruptura a mitad de semana** tiene que dejar guardada una referencia nueva y, al día siguiente, `seguir()` contra esa y no contra la del lunes. Test: Task S4-3, `test_una_ruptura_reemplaza_la_referencia_y_la_siguiente_diaria_la_usa`.
2. **Dos corridas el mismo día sin `_semana.json`** (por ejemplo, `--grupo forex` y después `--grupo commodities`): la semanal corre una sola vez y cubre todos los canales cubiertos. Test: Task S4-3, `test_la_semanal_corre_una_vez_aunque_la_primera_diaria_pida_un_canal`.
3. **Un fijo excluido por Tori** sale igual, con el motivo en `gates_omitidos`, en los avisos y en la pieza. Tests: Task S4-3 `test_un_fijo_excluido_por_la_estrategia_sale_igual_y_lo_dice` y Task S4-4 `test_el_mensaje_dice_el_motivo_de_un_fijo_excluido`.
4. **Una pieza preparada antes del enchufe** (payload sin `lectura`) que llega al despacho no puede salir con el refresco viejo. Test: Task S4-5, `test_un_payload_sin_lectura_no_se_despacha`.
5. **Una lectura sin nivel por un lado del precio** (tendencia alcista sin objetivo encima) no puede romper el payload ni publicar un nivel inventado: ese lado sale `--`. Test: Task S4-4, `test_sin_nivel_sobre_el_precio_la_resistencia_sale_vacia`.

---

## Estructura de archivos

| Archivo | Responsabilidad | Sesión |
|---|---|---|
| `scripts/referencia_semanal.py` (nuevo) | Semana ISO, rutas, guardar/cargar la referencia y el manifiesto `_semana.json`, firma estructural, `lectura_del_dia` | S4 |
| `scripts/estrategia/fuente.py` | + `atr(df, n=14)`: la volatilidad típica, dato de infraestructura | S4 |
| `scripts/screener_gi.py` | `correr_semanal`, `evaluar_con_estrategia`, `escanear` sobre la estrategia; borra la sombra y `ignorar_agotamiento` | S4 |
| `scripts/pipeline_carrusel.py` | `niveles_publicados`, `marco_operativo`, `construir_payload_lectura`, `lectura_operativa` y mensaje desde la `Lectura`, `refrescar_payload_lectura`, despacho con `seguir()` | S4 |
| `scripts/suplemento_canal.py` | Categorías: salen las de agotamiento y banda, entran los motivos de Tori como no publicables | S4 |
| `config/activos.json` | + `notas_marco.H4` en los 8 activos cubiertos | S4 |
| `.claude/commands/carrusel.md` | Sin `--forzar`, con la referencia semanal | S4 |
| `CLAUDE.md` + `.agents/rules/proyecto.md` | Una nota en *El `Score_GI` y sus gates* que apunta al enchufe; se regenera AGY | S4 |
| `scripts/tradingview_grafico.py` | Dibuja `Lectura.lineas`; se borran `_canal` y `calcular_estructura` | S5 |
| `scripts/pipeline_carrusel.py` | El gráfico recibe las líneas | S5 |

---

## Sesión S4

Rama: `feat/enchufe-s4-escaner` desde `origin/master`.

### Task S4-1: Referencia semanal (almacenamiento y firma)

**Files:**
- Create: `scripts/referencia_semanal.py`
- Test: `tests/test_referencia_semanal.py`

**Interfaces:**
- Consumes: `estrategia.contrato.{Lectura, lectura_a_dict, lectura_de_dict}`.
- Produces:
  - `DIR: Path` = `data/referencias_semanales`
  - `semana_de(momento: datetime) -> str` → `"2026-W42"` (fecha de Santiago, `isocalendar`)
  - `slug(ticker: str) -> str` → `"wti"` para `"WTI.spot"`, `"usdclp"`
  - `guardar(lectura: Lectura, semana: str, motivo: str, ahora: datetime, base: Path = DIR) -> Path`
  - `cargar(semana: str, ticker: str, base: Path = DIR) -> Lectura | None`
  - `manifiesto(semana: str, base: Path = DIR) -> dict | None`
  - `guardar_manifiesto(semana: str, datos: dict, base: Path = DIR) -> Path`
  - `firma(lectura: Lectura) -> tuple`
  - `debe_reemplazar(referencia: Lectura, actual: Lectura) -> bool`

- [ ] **Step 1: Write the failing test**

```python
"""La referencia semanal: guardar, leer y cuándo reemplazarla (spec §4)."""
from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime

from estrategia.contrato import SCL, Escenario, Lectura, Linea, Referencia
import referencia_semanal as rs


def _linea(rol="seguridad", puntos=((100, 10.0), (200, 11.0))):
    return Linea(rol=rol, tipo="diagonal", puntos=puntos, marco="H4", toques=3,
                 calidad="A+", valor_actual=11.5)


def _lectura(estado="TENDENCIA", lineas=None):
    lineas = lineas if lineas is not None else (_linea(), _linea("accion", ((150, 13.0), (250, 12.0))))
    esc = tuple(Escenario(f, "c", "t") for f in ("⬆️", "↔️", "⬇️"))
    return Lectura(ticker="XAUUSD", marco="H4", precio=12.0, direccion="ALCISTA", estado=estado,
                   lineas=lineas, en_prueba=None, vigilar=Referencia(11.5, "línea alcista de seguridad"),
                   invalidacion=None, objetivo=None, escenarios=esc, salida="s", conceptos=(),
                   avisos=(), metricas={"atr": 1.0}, vela=250)


def test_la_semana_es_la_iso_de_la_fecha_de_santiago():
    # Domingo 2026-10-11 23:30 en Santiago es todavía la semana 41.
    assert rs.semana_de(datetime(2026, 10, 11, 23, 30, tzinfo=SCL)) == "2026-W41"
    assert rs.semana_de(datetime(2026, 10, 12, 0, 5, tzinfo=SCL)) == "2026-W42"


def test_el_slug_saca_sufijos_del_broker():
    assert rs.slug("WTI.spot") == "wti"
    assert rs.slug("#NVDA") == "nvda"
    assert rs.slug("USDCLP") == "usdclp"


def test_guardar_y_cargar_devuelven_la_misma_lectura(tmp_path):
    lec = _lectura()
    ruta = rs.guardar(lec, "2026-W42", "semanal", datetime(2026, 10, 12, 9, 0, tzinfo=SCL), base=tmp_path)
    assert ruta == tmp_path / "2026-W42" / "xauusd.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert datos["motivo"] == "semanal" and datos["ticker"] == "XAUUSD"
    assert rs.cargar("2026-W42", "XAUUSD", base=tmp_path) == lec


def test_sin_archivo_no_hay_referencia(tmp_path):
    assert rs.cargar("2026-W42", "XAUUSD", base=tmp_path) is None
    assert rs.manifiesto("2026-W42", base=tmp_path) is None


def test_una_referencia_en_prueba_no_se_guarda(tmp_path):
    import pytest
    from estrategia.contrato import Prueba
    lec = _lectura()
    prueba = replace(lec, estado="PRUEBA",
                     en_prueba=Prueba(_linea(), 11.6, datetime(2026, 10, 12, 13, 0, tzinfo=SCL)))
    with pytest.raises(ValueError, match="PRUEBA"):
        rs.guardar(prueba, "2026-W42", "semanal", datetime.now(SCL), base=tmp_path)


def test_el_manifiesto_se_guarda_y_se_lee(tmp_path):
    rs.guardar_manifiesto("2026-W42", {"elegidos": ["XAUUSD"]}, base=tmp_path)
    assert rs.manifiesto("2026-W42", base=tmp_path)["elegidos"] == ["XAUUSD"]


def test_la_misma_estructura_no_se_reemplaza_aunque_cambie_el_valor_de_hoy():
    ref = _lectura()
    hoy = replace(ref, lineas=tuple(replace(x, valor_actual=99.0) for x in ref.lineas), precio=13.0)
    assert not rs.debe_reemplazar(ref, hoy)


def test_tendencia_y_rebote_no_reemplazan():
    ref = _lectura()
    assert not rs.debe_reemplazar(ref, replace(ref, estado="REBOTE"))


def test_roles_reasignados_por_una_ruptura_reemplazan():
    ref = _lectura()
    rota = replace(ref, estado="RUPTURA", lineas=(replace(ref.lineas[0], rol="accion"),
                                                   replace(ref.lineas[1], rol="seguridad")))
    assert rs.debe_reemplazar(ref, rota)


def test_anclas_nuevas_reemplazan():
    ref = _lectura()
    retrazada = replace(ref, lineas=(_linea(puntos=((120, 10.0), (220, 11.0))), ref.lineas[1]))
    assert rs.debe_reemplazar(ref, retrazada)


def test_pasar_a_ruptura_reemplaza_aunque_las_lineas_no_cambien():
    ref = _lectura(estado="RANGO", lineas=())
    assert rs.debe_reemplazar(ref, replace(ref, estado="RUPTURA"))


def test_una_referencia_en_ruptura_que_sigue_igual_no_se_reemplaza():
    ref = _lectura(estado="RUPTURA")
    assert not rs.debe_reemplazar(ref, replace(ref, precio=13.5))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_referencia_semanal.py -q`
Expected: FAIL con `ModuleNotFoundError: No module named 'referencia_semanal'`.

- [ ] **Step 3: Write minimal implementation**

```python
"""La referencia semanal: lo que fijó el análisis del lunes, por activo (spec §4).

Guardarla y reemplazarla es infraestructura; la estrategia solo la lee con `seguir()`.
Es historia de lo que el cliente leyó, así que se versiona igual que
`data/historial_despachos.json`.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from estrategia.contrato import SCL, Lectura, lectura_a_dict, lectura_de_dict

RAIZ = Path(__file__).resolve().parent.parent
DIR = RAIZ / "data" / "referencias_semanales"
MANIFIESTO = "_semana.json"


def semana_de(momento: datetime) -> str:
    """La semana ISO de la fecha de Santiago: el lunes del cliente, no el de UTC."""
    año, semana, _ = momento.astimezone(SCL).date().isocalendar()
    return f"{año}-W{semana:02d}"


def slug(ticker: str) -> str:
    return ticker.lower().replace(".spot", "").replace("#", "").replace("/", "")


def ruta(semana: str, ticker: str, base: Path = DIR) -> Path:
    return base / semana / f"{slug(ticker)}.json"


def guardar(lectura: Lectura, semana: str, motivo: str, ahora: datetime, base: Path = DIR) -> Path:
    if lectura.estado == "PRUEBA":
        raise ValueError(f"{lectura.ticker}: una referencia no se guarda en PRUEBA; se lee con en_curso=None")
    destino = ruta(semana, lectura.ticker, base)
    destino.parent.mkdir(parents=True, exist_ok=True)
    datos = {"ticker": lectura.ticker, "semana": semana, "motivo": motivo,
             "guardada": ahora.astimezone(SCL).isoformat(timespec="minutes"),
             "lectura": lectura_a_dict(lectura)}
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def cargar(semana: str, ticker: str, base: Path = DIR) -> Lectura | None:
    origen = ruta(semana, ticker, base)
    if not origen.exists():
        return None
    return lectura_de_dict(json.loads(origen.read_text(encoding="utf-8"))["lectura"])


def manifiesto(semana: str, base: Path = DIR) -> dict[str, Any] | None:
    origen = base / semana / MANIFIESTO
    return json.loads(origen.read_text(encoding="utf-8")) if origen.exists() else None


def guardar_manifiesto(semana: str, datos: dict[str, Any], base: Path = DIR) -> Path:
    destino = base / semana / MANIFIESTO
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    return destino


def firma(lectura: Lectura) -> tuple:
    """La estructura de la lectura: qué línea cumple qué papel y dónde está anclada."""
    return tuple(sorted((x.rol, x.tipo, x.marco, x.puntos) for x in lectura.lineas))


def debe_reemplazar(referencia: Lectura, actual: Lectura) -> bool:
    """La tesis del lunes terminó: una línea se rompió por cierre o la estrategia volvió a trazar.

    No lee los avisos ni las métricas de la estrategia: compara la estructura, que es
    parte del contrato. Entre TENDENCIA, REBOTE y PRUEBA la estructura no cambia.
    """
    if firma(referencia) != firma(actual):
        return True
    return actual.estado == "RUPTURA" and referencia.estado != "RUPTURA"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_referencia_semanal.py -q`
Expected: PASS (12 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/referencia_semanal.py tests/test_referencia_semanal.py
git commit -m "feat(enchufe): la referencia semanal se guarda por activo y sabe cuándo caduca"
```

### Task S4-2: La lectura del día contra la referencia, y el ATR de infraestructura

**Files:**
- Modify: `scripts/referencia_semanal.py` (agrega `Diaria`, `SinReferencia`, `EXTRA`, `lectura_del_dia`)
- Modify: `scripts/estrategia/fuente.py` (agrega `atr`)
- Test: `tests/test_referencia_semanal.py`, `tests/test_estrategia_fuente.py`

**Interfaces:**
- Consumes: `referencia_semanal.{cargar, debe_reemplazar}`, `Estrategia.{leer, seguir, marcos}`.
- Produces:
  - `EXTRA = 60`
  - `class SinReferencia(LookupError)`
  - `@dataclass(frozen=True) class Diaria: lectura: Lectura; reemplazo: Lectura | None; avisos: tuple[str, ...]; velas: dict[str, DataFrame]`
  - `Lector = Callable[[str, Marcos, int], tuple[dict[str, DataFrame], VelaEnCurso | None]]`
  - `lectura_del_dia(estrategia, ticker: str, digits: int, semana: str, lector: Lector, base: Path = DIR) -> Diaria`
  - `fuente.atr(df: DataFrame, n: int = 14) -> float`

- [ ] **Step 1: Write the failing tests**

En `tests/test_referencia_semanal.py`, al final:

```python
class _Falsa:
    """Una estrategia mínima que registra con qué la llamaron."""

    def __init__(self, seguida, leida, falla_seguir=False):
        from estrategia.contrato import Etiqueta, Marcos
        self.marcos = Marcos(("D1",), "H4", {"D1": 5, "H4": 5},
                             {"D1": Etiqueta("p", "d"), "H4": Etiqueta("s", "u")})
        self.seguida, self.leida, self.falla_seguir = seguida, leida, falla_seguir
        self.llamadas: list[tuple] = []

    def seguir(self, referencia, velas, digits, en_curso=None):
        self.llamadas.append(("seguir", en_curso))
        if self.falla_seguir:
            raise ValueError("las anclas ya no caben en la ventana")
        return self.seguida

    def leer(self, ticker, velas, digits, en_curso=None):
        self.llamadas.append(("leer", en_curso))
        return self.leida


def _lector(pedidos):
    def lector(ticker, marcos, extra):
        pedidos.append(extra)
        return {"H4": "velas"}, "vela-en-curso"
    return lector


def test_sin_referencia_levanta(tmp_path):
    import pytest
    with pytest.raises(rs.SinReferencia):
        rs.lectura_del_dia(_Falsa(None, None), "XAUUSD", 2, "2026-W42", _lector([]), base=tmp_path)


def test_la_diaria_sigue_la_referencia_con_velas_extra_y_la_vela_en_curso(tmp_path):
    ref = _lectura()
    rs.guardar(ref, "2026-W42", "semanal", datetime(2026, 10, 12, 9, tzinfo=SCL), base=tmp_path)
    hoy = replace(ref, precio=13.0)
    pedidos: list[int] = []
    est = _Falsa(hoy, None)
    d = rs.lectura_del_dia(est, "XAUUSD", 2, "2026-W42", _lector(pedidos), base=tmp_path)
    assert d.lectura == hoy and d.reemplazo is None and d.avisos == ()
    assert pedidos == [rs.EXTRA] and est.llamadas == [("seguir", "vela-en-curso")]


def test_una_ruptura_trae_el_reemplazo_leido_sin_vela_en_curso(tmp_path):
    ref = _lectura()
    rs.guardar(ref, "2026-W42", "semanal", datetime(2026, 10, 12, 9, tzinfo=SCL), base=tmp_path)
    rota = replace(ref, estado="RUPTURA", lineas=(replace(ref.lineas[0], rol="accion"),))
    nueva = replace(ref, estado="RUPTURA", vela=300)
    est = _Falsa(rota, nueva)
    d = rs.lectura_del_dia(est, "XAUUSD", 2, "2026-W42", _lector([]), base=tmp_path)
    assert d.lectura == rota and d.reemplazo == nueva
    assert ("leer", None) in est.llamadas
    assert "nueva referencia" in d.avisos[0]


def test_si_seguir_no_puede_evaluar_se_lee_de_nuevo_y_se_avisa(tmp_path):
    ref = _lectura()
    rs.guardar(ref, "2026-W42", "semanal", datetime(2026, 10, 12, 9, tzinfo=SCL), base=tmp_path)
    nueva = replace(ref, vela=400)
    est = _Falsa(None, nueva, falla_seguir=True)
    d = rs.lectura_del_dia(est, "XAUUSD", 2, "2026-W42", _lector([]), base=tmp_path)
    assert d.lectura == nueva and d.reemplazo == nueva
    assert est.llamadas[-2:] == [("leer", "vela-en-curso"), ("leer", None)]
    assert "anclas" in d.avisos[0]
```

En `tests/test_estrategia_fuente.py`, al final:

```python
def test_el_atr_es_el_promedio_del_rango_verdadero():
    import pandas as pd
    from estrategia.fuente import atr
    df = pd.DataFrame({"time": [1, 2, 3], "open": [10, 11, 12], "high": [11, 13, 13],
                       "low": [9, 10, 11], "close": [10, 12, 12]})
    # Rangos verdaderos: 2, max(3, |13-10|, |10-10|)=3, max(2, |13-12|, |11-12|)=2
    assert atr(df, n=3) == (2 + 3 + 2) / 3
    assert atr(df, n=2) == (3 + 2) / 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_referencia_semanal.py tests/test_estrategia_fuente.py -q`
Expected: FAIL con `AttributeError: module 'referencia_semanal' has no attribute 'SinReferencia'` y `ImportError: cannot import name 'atr'`.

- [ ] **Step 3: Write minimal implementation**

En `scripts/estrategia/fuente.py`, después de `_epoch`:

```python
def atr(df: pd.DataFrame, n: int = 14) -> float:
    """El rango verdadero promedio de las últimas `n` velas: cuánto se mueve una vela típica.

    Es un dato de infraestructura para la pieza ("volatilidad típica"), no una decisión de
    la estrategia.
    """
    previo = df["close"].shift(1)
    rango = pd.concat([df["high"] - df["low"], (df["high"] - previo).abs(),
                       (df["low"] - previo).abs()], axis=1).max(axis=1)
    return float(rango.tail(n).mean())
```

En `scripts/referencia_semanal.py`, agregar imports y al final:

```python
from dataclasses import dataclass
from typing import Callable

import pandas as pd

from estrategia.contrato import Marcos, VelaEnCurso

EXTRA = 60  # velas de más para que las anclas del lunes sigan dentro (sesiones.md, S4)
Lector = Callable[[str, Marcos, int], tuple[dict[str, pd.DataFrame], VelaEnCurso | None]]


class SinReferencia(LookupError):
    """El activo no tiene referencia esta semana: no sale en las diarias (spec §4)."""


@dataclass(frozen=True)
class Diaria:
    lectura: Lectura  # la que se publica hoy
    reemplazo: Lectura | None  # la nueva referencia, si la del lunes caducó
    avisos: tuple[str, ...]
    velas: dict[str, pd.DataFrame]


def lectura_del_dia(estrategia, ticker: str, digits: int, semana: str, lector: Lector,
                    base: Path = DIR) -> Diaria:
    """La lectura de hoy contra la referencia de la semana, y su reemplazo si caducó.

    No guarda nada: quien publica decide si persiste el reemplazo (el escáner sí, el
    despacho no).
    """
    referencia = cargar(semana, ticker, base)
    if referencia is None:
        raise SinReferencia(f"{ticker} no tiene referencia en {semana}")
    velas, en_curso = lector(ticker, estrategia.marcos, EXTRA)
    try:
        actual = estrategia.seguir(referencia, velas, digits, en_curso)
    except ValueError as exc:
        actual = estrategia.leer(ticker, velas, digits, en_curso)
        nueva = estrategia.leer(ticker, velas, digits, None)
        return Diaria(actual, nueva, (
            f"{ticker}: la referencia de la semana no se pudo seguir ({exc}); se leyó de nuevo "
            "y esa lectura pasa a ser la nueva referencia",), velas)
    if debe_reemplazar(referencia, actual):
        nueva = estrategia.leer(ticker, velas, digits, None)
        return Diaria(actual, nueva, (
            f"{ticker}: la lectura de la semana cambió de estructura ({referencia.estado.lower()} → "
            f"{actual.estado.lower()}); la lectura de este cierre pasa a ser la nueva referencia",), velas)
    return Diaria(actual, None, (), velas)
```

(Mover los imports nuevos al bloque de imports de arriba del módulo.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_referencia_semanal.py tests/test_estrategia_fuente.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/referencia_semanal.py scripts/estrategia/fuente.py tests/test_referencia_semanal.py tests/test_estrategia_fuente.py
git commit -m "feat(enchufe): la diaria se lee contra la referencia y trae su reemplazo si caducó"
```

### Task S4-3: El escáner pasa a la estrategia (semanal y diaria)

**Files:**
- Modify: `scripts/screener_gi.py`
- Delete: `scripts/direccion_gi.py`, `scripts/medir_direccion.py`, `config/direccion.json`, `tests/test_direccion_gi.py`, `tests/test_medir_direccion.py`
- Test: `tests/test_screener_gi.py`

**Interfaces:**
- Consumes: `referencia_semanal.*` (S4-1, S4-2), `registro.activa()`, `fuente.velas_mt5`, `fuente.atr`, `lectura_a_dict`.
- Produces:
  - `CATEGORIAS = ["forex", "commodity", "indice", "accion", "crypto"]`
  - `seleccionar_por_categoria(universo, evaluados, top) -> list[dict]` (la matriz de hoy, extraída)
  - `correr_semanal(estrategia, universo, ahora_stgo, lector, top=3, base=referencia_semanal.DIR) -> dict` → `{"semana", "elegidos": [ticker], "excluidos": [...], "avisos": [...]}`; escribe las referencias y `_semana.json`.
  - `evaluar_con_estrategia(activo, estrategia, diaria: Diaria, fijo: bool) -> dict` → entrada de selección:
    `{"ticker", "nombre", "clase", "cobertura_fija", "gates_omitidos": [str], "score": float, "puntaje": {"desglose": dict, "excluido": str|None}, "direccion", "estado", "precio", "lectura": dict, "marco": str, "volatilidad_tipica": float}` o `{..., "excluido": motivo}`.
  - `escanear(tanda=None, top=3, solo_renderizables=True, ahora_ny=None, grupo=None, modo_matriz=False, estrategia=None, lector=None, base_referencias=None)`; sin `analizador` ni `ignorar_agotamiento`. El resultado conserva las claves de hoy (`tanda`, `sesion_slug`, `nombre_tanda`, `nombre_sesion`, `foco`, `ancla_ny`, `hora_chile_tanda`, `hora_real_chile`, `generado`, `eventos_del_dia`, `score_maximo_posible`, `seleccion`, `ranking_completo`, `excluidos`, `avisos`) más `"estrategia"` y `"semana"`; pierde `delta_ust_10y_bps`.
  - CLI: sale `--forzar`; entra `--semanal` (corre la semanal si falta y termina).

- [ ] **Step 1: Write the failing tests**

En `tests/test_screener_gi.py`, agregar un bloque nuevo con una estrategia y un lector falsos. Las lecturas se construyen con el helper `_lectura` copiado de `tests/test_referencia_semanal.py` (cópialo; no importes entre módulos de test).

```python
# ── Fase 2 del enchufe: el escáner es de la estrategia ─────────────────────────
from dataclasses import replace as _replace

import pandas as pd

import referencia_semanal as rs
from estrategia.contrato import SCL, Escenario, Etiqueta, Lectura, Linea, Marcos, Puntaje, Referencia

NY_LUNES = datetime(2026, 10, 12, 10, 0, tzinfo=sc.NY)  # lunes 12-10, 11:00 en Santiago


def _lec(ticker, estado="TENDENCIA", direccion="ALCISTA"):
    lin = Linea("seguridad", "diagonal", ((100, 10.0), (200, 11.0)), "H4", 3, "A+", 11.5)
    esc = tuple(Escenario(f, "c", "t") for f in ("⬆️", "↔️", "⬇️"))
    return Lectura(ticker=ticker, marco="H4", precio=12.0, direccion=direccion, estado=estado,
                   lineas=(lin,), en_prueba=None, vigilar=Referencia(11.5, "línea alcista de seguridad", lin),
                   invalidacion=Referencia(11.5, "línea alcista de seguridad", lin), objetivo=None,
                   escenarios=esc, salida="s", conceptos=(), avisos=(), metricas={}, vela=200)


class _Est:
    """Puntúa por tabla; `excluir` simula las exclusiones de Tori."""

    nombre = "falsa"
    marcos = Marcos(("D1",), "H4", {"D1": 5, "H4": 5}, {"D1": Etiqueta("p", "d"), "H4": Etiqueta("swing", "de una a dos semanas")})

    def __init__(self, puntos, excluir=None, ruptura=()):
        self.puntos, self.excluir, self.ruptura = puntos, excluir or {}, set(ruptura)
        self.lecturas = {"leer": 0, "seguir": 0}

    def leer(self, ticker, velas, digits, en_curso=None):
        self.lecturas["leer"] += 1
        return _lec(ticker)

    def seguir(self, referencia, velas, digits, en_curso=None):
        self.lecturas["seguir"] += 1
        if referencia.ticker in self.ruptura:
            return _replace(referencia, estado="RUPTURA",
                            lineas=tuple(_replace(x, rol="accion") for x in referencia.lineas))
        return referencia

    def puntuar(self, lectura, horizonte):
        motivo = self.excluir.get(lectura.ticker)
        return Puntaje(0.0 if motivo else self.puntos.get(lectura.ticker, 10.0), {}, motivo)

    def divergencia(self, preparada, actual):
        return None


def _velas():
    return pd.DataFrame({"time": [1, 2, 3], "open": [1.0, 1.1, 1.2], "high": [1.2, 1.3, 1.3],
                         "low": [0.9, 1.0, 1.1], "close": [1.1, 1.2, 1.2]})


def _lector(ticker, marcos, extra):
    return {m: _velas() for m in marcos.todos}, None


def _escanear(tmp_path, est, monkeypatch, **kw):
    monkeypatch.setattr(sc, "_contexto_macro", lambda ahora: ([], None, []))
    monkeypatch.setattr(sc, "DIR_SALIDA", tmp_path / "screener")
    return sc.escanear(ahora_ny=kw.pop("ahora_ny", NY_LUNES), estrategia=est, lector=_lector,
                       base_referencias=tmp_path / "refs", **kw)


def test_sin_semanal_la_primera_diaria_la_corre_y_lo_dice(tmp_path, monkeypatch):
    res = _escanear(tmp_path, _Est({}), monkeypatch, modo_matriz=True)
    man = rs.manifiesto("2026-W42", base=tmp_path / "refs")
    assert man is not None and set(sc.cobertura_fija()) <= set(man["elegidos"])
    assert any("análisis semanal" in a for a in res["avisos"])
    assert res["semana"] == "2026-W42" and res["estrategia"] == "falsa"


def test_la_semanal_corre_una_vez_aunque_la_primera_diaria_pida_un_canal(tmp_path, monkeypatch):
    est = _Est({})
    _escanear(tmp_path, est, monkeypatch, grupo="forex")
    elegidos = rs.manifiesto("2026-W42", base=tmp_path / "refs")["elegidos"]
    assert "XAUUSD" in elegidos  # commodities también quedó fijado
    leidas = est.lecturas["leer"]
    _escanear(tmp_path, est, monkeypatch, grupo="commodity")
    assert est.lecturas["leer"] == leidas  # la segunda corrida no volvió a correr la semanal


def test_la_semanal_elige_por_categoria_los_fijos_y_los_mejores(tmp_path, monkeypatch):
    universo = sc.solo_canales_cubiertos(sc.cargar_universo(True))[0]
    puntos = {a["ticker"]: 50.0 for a in universo}
    puntos["GBPUSD"] = 0.0
    res = sc.correr_semanal(_Est(puntos), universo, NY_LUNES.astimezone(SCL), _lector,
                            top=3, base=tmp_path)
    assert "GBPUSD" not in res["elegidos"]
    for fijo in sc.cobertura_fija():
        assert fijo in res["elegidos"]
        assert rs.cargar("2026-W42", fijo, base=tmp_path) is not None


def test_las_diarias_solo_cubren_los_activos_de_la_semana(tmp_path, monkeypatch):
    rs.guardar_manifiesto("2026-W42", {"elegidos": ["USDCLP"]}, base=tmp_path / "refs")
    rs.guardar(_lec("USDCLP"), "2026-W42", "semanal", NY_LUNES, base=tmp_path / "refs")
    res = _escanear(tmp_path, _Est({}), monkeypatch, modo_matriz=True)
    assert [s["ticker"] for s in res["ranking_completo"]] == ["USDCLP"]
    assert any("sin referencia esta semana" in a for a in res["avisos"])


def test_la_diaria_ordena_con_el_puntaje_de_sesion(tmp_path, monkeypatch):
    rs.guardar_manifiesto("2026-W42", {"elegidos": ["EURUSD", "GBPUSD"]}, base=tmp_path / "refs")
    for t in ("EURUSD", "GBPUSD"):
        rs.guardar(_lec(t), "2026-W42", "semanal", NY_LUNES, base=tmp_path / "refs")
    res = _escanear(tmp_path, _Est({"EURUSD": 30.0, "GBPUSD": 80.0}), monkeypatch)
    assert [s["ticker"] for s in res["ranking_completo"]] == ["GBPUSD", "EURUSD"]
    elegido = res["ranking_completo"][0]
    assert elegido["score"] == 80.0 and elegido["lectura"]["ticker"] == "GBPUSD"
    assert elegido["marco"] == "H4" and elegido["volatilidad_tipica"] > 0
    assert "factores" not in elegido


def test_una_ruptura_reemplaza_la_referencia_y_la_siguiente_diaria_la_usa(tmp_path, monkeypatch):
    base = tmp_path / "refs"
    rs.guardar_manifiesto("2026-W42", {"elegidos": ["EURUSD"]}, base=base)
    rs.guardar(_lec("EURUSD"), "2026-W42", "semanal", NY_LUNES, base=base)
    res = _escanear(tmp_path, _Est({}, ruptura={"EURUSD"}), monkeypatch)
    assert res["ranking_completo"][0]["estado"] == "RUPTURA"
    guardada = json.loads(rs.ruta("2026-W42", "EURUSD", base).read_text(encoding="utf-8"))
    assert guardada["motivo"] == "ruptura"
    assert any("nueva referencia" in a for a in res["avisos"])


def test_un_no_fijo_excluido_por_la_estrategia_queda_fuera_con_su_motivo(tmp_path, monkeypatch):
    rs.guardar_manifiesto("2026-W42", {"elegidos": ["EURUSD"]}, base=tmp_path / "refs")
    rs.guardar(_lec("EURUSD"), "2026-W42", "semanal", NY_LUNES, base=tmp_path / "refs")
    res = _escanear(tmp_path, _Est({}, excluir={"EURUSD": "va contra la secuencia"}), monkeypatch)
    assert res["excluidos"][0]["excluido"] == "va contra la secuencia"


def test_un_fijo_excluido_por_la_estrategia_sale_igual_y_lo_dice(tmp_path, monkeypatch):
    rs.guardar_manifiesto("2026-W42", {"elegidos": ["USDCLP"]}, base=tmp_path / "refs")
    rs.guardar(_lec("USDCLP"), "2026-W42", "semanal", NY_LUNES, base=tmp_path / "refs")
    res = _escanear(tmp_path, _Est({}, excluir={"USDCLP": "sin líneas trazables"}), monkeypatch,
                    modo_matriz=True)
    elegido = next(s for s in res["seleccion"] if s["ticker"] == "USDCLP")
    assert elegido["gates_omitidos"] == ["sin líneas trazables"]
    assert any("USDCLP: cobertura fija, sale siempre aunque sin líneas trazables" in a for a in res["avisos"])


def test_un_error_de_datos_excluye_con_su_motivo_y_no_revienta(tmp_path, monkeypatch):
    rs.guardar_manifiesto("2026-W42", {"elegidos": ["EURUSD"]}, base=tmp_path / "refs")
    rs.guardar(_lec("EURUSD"), "2026-W42", "semanal", NY_LUNES, base=tmp_path / "refs")

    def lector_roto(ticker, marcos, extra):
        raise RuntimeError("MT5 no entregó velas")

    monkeypatch.setattr(sc, "_contexto_macro", lambda ahora: ([], None, []))
    monkeypatch.setattr(sc, "DIR_SALIDA", tmp_path / "screener")
    res = sc.escanear(ahora_ny=NY_LUNES, estrategia=_Est({}), lector=lector_roto,
                      base_referencias=tmp_path / "refs")
    assert "MT5 no entregó velas" in res["excluidos"][0]["excluido"]
```

Y **reescribir o borrar** los tests de `tests/test_screener_gi.py` que fijan el escáner viejo dentro de `escanear`:
- Borrar: `test_un_gate_apagado_lo_dice_en_los_avisos`, `test_con_el_gate_encendido_no_hay_aviso_que_dar`, `test_pedir_un_grupo_ya_no_apaga_el_gate_de_agotamiento`, `test_la_zona_de_aviso_llega_a_los_avisos_del_escaner`, `test_una_banda_holgada_no_genera_aviso`, `test_la_sombra_viaja_en_el_resultado`, `test_la_sombra_es_inerte`, `test_avisos_de_sombra_solo_cuando_difieren_o_falla`, `test_escanear_reporta_la_diferencia_de_la_sombra`, `test_los_fijos_salen_aunque_hayan_agotado_el_recorrido_diario`, `test_los_fijos_saltan_el_gate_de_banda`.
- Reescribir con `_Est` y `_escanear`: `test_el_modo_matriz_cubre_cada_grupo_que_tenga_con_que`, `test_el_modo_matriz_respeta_el_tope_por_grupo`, `test_la_tanda_2_no_repite_un_activo_de_la_tanda_1`, `test_desduplicacion_continua_intradia_por_horario_de_ejecucion`, `test_un_fijo_no_se_excluye_por_haber_salido_en_otra_corrida`, `test_un_fijo_sigue_fuera_en_feriado_de_su_bolsa`, `test_un_canal_no_cubierto_sale_del_universo_antes_de_puntuar`. Cada uno conserva lo que afirma (tope por grupo, no repetir en el día, fijo en feriado fuera); solo cambia cómo se construye el mercado: con referencias guardadas en `tmp_path / "refs"` y la estrategia falsa en vez del `analizador`.
- Se conservan sin cambios los tests de `evaluar_activo`, factores, gates de agotamiento y banda y blackout que lo llaman directo: siguen cubriendo el camino que usan Avisos y el analista hasta S6/S7.

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_screener_gi.py -q`
Expected: FAIL; `escanear() got an unexpected keyword argument 'estrategia'` y `module 'screener_gi' has no attribute 'correr_semanal'`.

- [ ] **Step 3: Write the implementation**

En `scripts/screener_gi.py`:

1. Borrar `_direccion_en_sombra`, `avisos_de_sombra`, la clave `"direccion_4ejes"` de `evaluar_activo` y el import de `direccion_gi`. Borrar `scripts/direccion_gi.py`, `scripts/medir_direccion.py`, `config/direccion.json`, `tests/test_direccion_gi.py`, `tests/test_medir_direccion.py` con `git rm`.
2. Encima de `evaluar_activo`, un comentario de bloque:

```python
# ── Transitorio hasta S6/S7 del enchufe ────────────────────────────────────────
# `evaluar_activo`, sus factores y los gates de agotamiento y banda ya no deciden el
# carrusel: los usan todavía `pipeline_avisos` y `analista/foco`. Se borran cuando
# esos consumidores pasen a la `Lectura` (spec §6, §7 fase 3).
```

3. Agregar las funciones nuevas (después de `_publicados_hoy`):

```python
CATEGORIAS = ["forex", "commodity", "indice", "accion", "crypto"]


def seleccionar_por_categoria(universo: list[dict[str, Any]], evaluados: list[dict[str, Any]],
                              top: int) -> list[dict[str, Any]]:
    """Por categoría: los fijos primero y sin competir; los cupos que dejan, por puntaje."""
    seleccion: list[dict[str, Any]] = []
    for cat in CATEGORIAS:
        del_grupo = {a["ticker"] for a in filtrar_por_grupo(universo, cat)}
        fijos = [r for r in evaluados if r.get("cobertura_fija") and r["ticker"] in del_grupo]
        resto = [r for r in evaluados
                 if not r.get("cobertura_fija") and r["score"] > 0 and r["ticker"] in del_grupo]
        seleccion.extend(fijos + resto[:max(0, top - len(fijos))])
    return seleccion


def correr_semanal(estrategia, universo: list[dict[str, Any]], ahora_stgo: datetime, lector,
                   top: int = 3, base: Path | None = None) -> dict[str, Any]:
    """El análisis semanal: elige con `puntuar(leer(...), "semana")` y fija las referencias.

    Sin feriado ni blackout: son gates del día, y la referencia vale la semana. La
    cobertura fija recibe referencia aunque la estrategia la excluya (director, 2026-10-11).
    """
    base = base or rs.DIR
    semana = rs.semana_de(ahora_stgo)
    fijos = set(cobertura_fija())
    evaluados, excluidos, avisos = [], [], []
    lecturas: dict[str, Any] = {}
    for activo in universo:
        ticker = activo["ticker"]
        try:
            velas, _ = lector(ticker, estrategia.marcos, 0)
            lectura = estrategia.leer(ticker, velas, activo["digits"], None)
        except Exception as exc:  # noqa: BLE001 - un activo roto no tumba la semana
            excluidos.append({"ticker": ticker, "excluido": f"no se pudo leer: {exc}"})
            continue
        p = estrategia.puntuar(lectura, "semana")
        es_fijo = ticker in fijos
        if p.excluido and not es_fijo:
            excluidos.append({"ticker": ticker, "excluido": p.excluido})
            continue
        if p.excluido:
            avisos.append(f"{ticker}: cobertura fija, queda en la semana aunque {p.excluido}")
        lecturas[ticker] = lectura
        evaluados.append({"ticker": ticker, "score": p.puntos, "cobertura_fija": es_fijo})
    evaluados.sort(key=lambda r: (-r["score"], r["ticker"]))
    elegidos = [r["ticker"] for r in seleccionar_por_categoria(universo, evaluados, top)]
    for ticker in elegidos:
        rs.guardar(lecturas[ticker], semana, "semanal", ahora_stgo, base=base)
    rs.guardar_manifiesto(semana, {
        "semana": semana, "estrategia": estrategia.nombre,
        "generado": ahora_stgo.strftime("%Y-%m-%d %H:%M"),
        "elegidos": elegidos,
        "puntajes": {r["ticker"]: r["score"] for r in evaluados},
        "excluidos": excluidos,
    }, base=base)
    return {"semana": semana, "elegidos": elegidos, "excluidos": excluidos, "avisos": avisos}


def evaluar_con_estrategia(activo: dict[str, Any], estrategia, diaria: "rs.Diaria",
                           fijo: bool) -> dict[str, Any]:
    """La entrada del ranking diario: la lectura de hoy y su puntaje de sesión."""
    base = {"ticker": activo["ticker"], "nombre": activo["nombre"], "clase": activo["clase"]}
    lectura = diaria.lectura
    p = estrategia.puntuar(lectura, "sesion")
    if p.excluido and not fijo:
        return {**base, "excluido": p.excluido}
    op = estrategia.marcos.operativo
    return {
        **base,
        "cobertura_fija": fijo,
        "gates_omitidos": [p.excluido] if p.excluido else [],
        "score": p.puntos,
        "puntaje": {"desglose": p.desglose, "excluido": p.excluido},
        "direccion": lectura.direccion,
        "estado": lectura.estado,
        "precio": lectura.precio,
        "marco": op,
        "volatilidad_tipica": round(atr(diaria.velas[op]), activo["digits"]),
        "lectura": lectura_a_dict(lectura),
    }
```

Imports nuevos arriba del módulo (después de que `SRC`/`scripts` estén en `sys.path`):

```python
import referencia_semanal as rs
from estrategia import registro
from estrategia.contrato import lectura_a_dict
from estrategia.fuente import atr
```

4. Reemplazar `escanear` por:

```python
def escanear(
    tanda: int | None = None,
    top: int = 3,
    solo_renderizables: bool = True,
    ahora_ny: datetime | None = None,
    grupo: str | None = None,
    modo_matriz: bool = False,
    estrategia=None,
    lector=None,
    base_referencias: Path | None = None,
) -> dict[str, Any]:
    """Ordena los activos de la semana con la estrategia activa y elige la tanda.

    Las diarias cubren solo los activos con referencia (spec §4). Si la semana no
    tiene análisis, lo corre la primera diaria (director, 2026-10-11).
    """
    ahora_ny = ahora_ny or datetime.now(tz=NY)
    ahora_stgo = ahora_ny.astimezone(SANTIAGO)
    estrategia = estrategia or registro.activa()
    base = base_referencias or rs.DIR
    if lector is None:
        from estrategia.fuente import velas_mt5 as lector

    info_sesion = detectar_sesion(ahora_ny)
    n_tanda = tanda or info_sesion["tanda"]
    nombre_sesion = TANDAS[tanda]["nombre"] if tanda and tanda in TANDAS else info_sesion["nombre"]
    foco_sesion = TANDAS[tanda]["foco"] if tanda and tanda in TANDAS else info_sesion["foco"]
    sesion_slug = info_sesion["slug"] if not tanda else f"tanda{n_tanda}"

    # El calendario queda solo para el blackout, que es infraestructura (spec §3).
    eventos, _delta, avisos = _contexto_macro(ahora_stgo)

    universo_cubierto, fuera = solo_canales_cubiertos(cargar_universo(solo_renderizables))
    if fuera:
        avisos.append(f"{len(fuera)} activos fuera del universo porque su canal no se cubre "
                      "(`cubierto: false` en config/whatsapp_grupos.json)")

    semana = rs.semana_de(ahora_stgo)
    if rs.manifiesto(semana, base=base) is None:
        sem = correr_semanal(estrategia, universo_cubierto, ahora_stgo, lector, top=top, base=base)
        avisos.append(f"no había análisis semanal de {semana}: se corrió ahora, con la primera "
                      f"diaria, y fijó {len(sem['elegidos'])} activos")
        avisos.extend(sem["avisos"])
    de_la_semana = set(rs.manifiesto(semana, base=base)["elegidos"])

    universo = universo_cubierto
    if grupo:
        universo = filtrar_por_grupo(universo, grupo)
        avisos.append(f"universo filtrado exclusivamente al grupo/categoría '{grupo}' ({len(universo)} activos)")
    sin_ref = [a for a in universo if a["ticker"] not in de_la_semana]
    if sin_ref:
        avisos.append(f"{len(sin_ref)} activos sin referencia esta semana: no salen en las diarias")
    universo = [a for a in universo if a["ticker"] in de_la_semana]

    ya_usados = _publicados_hoy(ahora_stgo.date().isoformat(), tanda=tanda,
                                hora_actual=ahora_stgo.strftime("%H:%M"))
    fijos = set(cobertura_fija())
    evaluados: list[dict[str, Any]] = []
    excluidos: list[dict[str, Any]] = []
    for activo in universo:
        ticker = activo["ticker"]
        base_ex = {"ticker": ticker, "nombre": activo["nombre"], "clase": activo["clase"]}
        es_fijo = ticker in fijos
        if ticker in ya_usados and not es_fijo:
            excluidos.append({**base_ex, "excluido": "ya salio en una corrida anterior de hoy"})
            continue
        motivo = gate_feriado(ticker, ahora_stgo.date()) or gate_blackout(ticker, eventos, ahora_stgo)
        if motivo:
            excluidos.append({**base_ex, "excluido": motivo})
            continue
        try:
            diaria = rs.lectura_del_dia(estrategia, ticker, activo["digits"], semana, lector, base=base)
        except Exception as exc:  # noqa: BLE001 - un activo roto no tumba la tanda
            excluidos.append({**base_ex, "excluido": f"no se pudo leer: {exc}"})
            continue
        avisos.extend(diaria.avisos)
        if diaria.reemplazo is not None:
            rs.guardar(diaria.reemplazo, semana, "ruptura", ahora_stgo, base=base)
        res = evaluar_con_estrategia(activo, estrategia, diaria, es_fijo)
        (excluidos if "excluido" in res else evaluados).append(res)

    evaluados.sort(key=lambda r: (-r["score"], r["ticker"]))
    if modo_matriz:
        seleccion = seleccionar_por_categoria(universo, evaluados, top)
    else:
        seleccion = [r for r in evaluados if r.get("cobertura_fija")] + [
            r for r in evaluados if not r.get("cobertura_fija") and r["score"] > 0][:top]

    for elegido in seleccion:
        if elegido.get("cobertura_fija"):
            motivos = elegido.get("gates_omitidos") or []
            avisos.append(f"{elegido['ticker']}: cobertura fija, sale siempre"
                          + (f" aunque {'; '.join(motivos)}" if motivos else ""))
    if not seleccion:
        avisos.append("ningun activo puntuo sobre 0: no hay tanda que publicar. "
                      "Es un resultado valido, no una falla")

    ancla_ny_str = ("{:02d}:{:02d}".format(*TANDAS[n_tanda]["hora_ny"])
                    if n_tanda in TANDAS else ahora_ny.strftime("%H:%M"))
    return {
        "tanda": n_tanda, "sesion_slug": sesion_slug, "nombre_tanda": nombre_sesion,
        "nombre_sesion": nombre_sesion, "foco": foco_sesion, "ancla_ny": ancla_ny_str,
        "hora_chile_tanda": hora_chile_de_tanda(n_tanda, ahora_ny),
        "hora_real_chile": ahora_stgo.strftime("%H:%M"),
        "generado": ahora_stgo.strftime("%Y-%m-%d %H:%M"),
        "estrategia": estrategia.nombre, "semana": semana,
        "eventos_del_dia": len(eventos), "score_maximo_posible": 100,
        "seleccion": seleccion, "ranking_completo": evaluados, "excluidos": excluidos,
        "avisos": avisos,
    }
```

5. En `main`: borrar `--forzar` y su uso; agregar `--semanal`:

```python
    parser.add_argument("--semanal", action="store_true",
                        help="corre el análisis semanal si la semana no lo tiene y termina")
```

y antes de escanear:

```python
    if args.semanal:
        ahora_stgo = datetime.now(tz=SANTIAGO)
        semana = rs.semana_de(ahora_stgo)
        if rs.manifiesto(semana) is not None:
            print(f"La semana {semana} ya tiene análisis semanal: no se rehace.")
            return 0
        from estrategia.fuente import velas_mt5
        universo, _ = solo_canales_cubiertos(cargar_universo(not args.todos))
        res = correr_semanal(registro.activa(), universo, ahora_stgo, velas_mt5)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0
```

(`_imprimir` deja de mostrar `delta_ust_10y_bps` y `factores`: muestra `score`, `estado`, `direccion` y `gates_omitidos` por activo.)

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_screener_gi.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/screener_gi.py tests/test_screener_gi.py
git rm scripts/direccion_gi.py scripts/medir_direccion.py config/direccion.json tests/test_direccion_gi.py tests/test_medir_direccion.py
git commit -m "feat(enchufe): el escáner ordena con la estrategia contra la referencia semanal"
```

### Task S4-4: El payload y el mensaje del carrusel salen de la `Lectura`

**Files:**
- Modify: `scripts/pipeline_carrusel.py`
- Modify: `config/activos.json` (`notas_marco.H4` en USDCLP, USDJPY, EURUSD, GBPUSD, XAUUSD, XAGUSD, WTI.spot, COPPER)
- Test: `tests/test_pipeline_carrusel.py`, `tests/test_screener_gi.py` (contrato de notas)

**Interfaces:**
- Consumes: entrada de selección de S4-3 (`lectura`, `marco`, `volatilidad_tipica`, `score`, `puntaje`, `gates_omitidos`).
- Produces:
  - `marco_operativo() -> str` (lee `registro.activa().marcos.operativo`)
  - `ETIQUETA_CORTA = {"M15": "15M", "H1": "1H", "H4": "4H", "D1": "1D", "W1": "1S"}`
  - `temporalidad_de(marco: str) -> str` → `"4H · marco swing (de una a dos semanas)"`
  - `niveles_publicados(lectura: Lectura) -> tuple[float | None, float | None]` → (soporte, resistencia): el precio más cercano bajo y sobre `lectura.precio` entre `vigilar`, `invalidacion`, `objetivo` y el `valor_actual` de las líneas del marco operativo y las horizontales.
  - `construir_payload_lectura(seleccion, activo_catalogo, ahora, cierres) -> dict` con las claves de hoy más `"lectura"` (dict), `"marco"`, `"digits"`, `"aviso_lectura"` (str, vacío si no hay) y `_procedencia = {"score", "puntaje", "ticker", "estrategia", "crudos": {"precio", "soporte", "resistencia"}}`.
  - `lectura_operativa(payload)` y `construir_mensaje_alerta(payload)`: si el payload trae `"lectura"`, salen de ella; si no, el camino de hoy (Avisos y analista, hasta S6/S7).

- [ ] **Step 1: Write the failing tests**

En `tests/test_pipeline_carrusel.py`, un bloque nuevo:

```python
# ── Fase 2 del enchufe: la pieza sale de la Lectura ────────────────────────────
from estrategia.contrato import Escenario, Lectura, Linea, Referencia, lectura_a_dict


def _lectura_alcista(objetivo=True):
    seg = Linea("seguridad", "diagonal", ((100, 4000.0), (200, 4050.0)), "H4", 3, "A+", 4080.0)
    obj = Referencia(4200.0, "resistencia de D1") if objetivo else None
    esc = (Escenario("⬆️", "Sobre 4.080,00", "Mientras el precio cierre sobre 4.080,00, la tendencia alcista sigue."),
           Escenario("↔️", "Vuelta a 4.080,00", "Si el precio vuelve a 4.080,00 y la respeta, la línea suma un toque."),
           Escenario("⬇️", "Cierre bajo 4.080,00", "Si una vela de 4 horas cierra bajo 4.080,00, la línea alcista se rompe."))
    ref = Referencia(4080.0, "línea alcista de seguridad", seg)
    return Lectura(ticker="XAUUSD", marco="H4", precio=4120.0, direccion="ALCISTA", estado="TENDENCIA",
                   lineas=(seg,), en_prueba=None, vigilar=ref, invalidacion=ref, objetivo=obj,
                   escenarios=esc, salida="La posición se cierra cuando una vela de 4 horas cierra al otro lado de la línea de seguridad, hoy en 4.080,00. No hay objetivo fijo.",
                   conceptos=(), avisos=(), metricas={}, vela=200)


def _sel(lectura, **extra):
    return {"ticker": lectura.ticker, "nombre": "Oro", "clase": "forex_commodities",
            "cobertura_fija": True, "gates_omitidos": [], "score": 60.0,
            "puntaje": {"desglose": {"base": 50.0}, "excluido": None},
            "direccion": lectura.direccion, "estado": lectura.estado, "precio": lectura.precio,
            "marco": "H4", "volatilidad_tipica": 18.5, "lectura": lectura_a_dict(lectura), **extra}


ORO = {"ticker": "XAUUSD", "nombre": "Oro", "digits": 2, "unidad": "USD", "categoria": "commodity",
       "imagen": "assets/activos/oro.jpg", "notas_marco": {"H4": "el oro hace tramos de varios días: en 4H se ven las líneas que esos tramos respetan."},
       "nota_volatilidad": "nota vieja de 1H"}


def test_los_niveles_publicados_son_los_mas_cercanos_a_cada_lado():
    assert pc.niveles_publicados(_lectura_alcista()) == (4080.0, 4200.0)


def test_sin_nivel_sobre_el_precio_la_resistencia_sale_vacia():
    lec = _lectura_alcista(objetivo=False)
    assert pc.niveles_publicados(lec) == (4080.0, None)
    payload = pc.construir_payload_lectura(_sel(lec), ORO, datetime(2026, 10, 12, 11, 0, tzinfo=pc.SANTIAGO), [4119.0, 4120.0])
    assert payload["resistencia"] == "--" and payload["soporte"] == "4.080,00"


def test_el_payload_lleva_la_lectura_el_marco_y_la_nota_del_marco():
    p = pc.construir_payload_lectura(_sel(_lectura_alcista()), ORO, datetime(2026, 10, 12, 11, 0, tzinfo=pc.SANTIAGO), [4119.0, 4120.0])
    assert p["lectura"]["ticker"] == "XAUUSD" and p["marco"] == "H4" and p["digits"] == 2
    assert p["sesgo"] == "Alcista" and p["vol_pct"] == "18,50 USD"
    assert p["nota_volatilidad"] == ORO["notas_marco"]["H4"]
    assert p["_procedencia"]["puntaje"]["desglose"] == {"base": 50.0}
    assert "factores" not in p["_procedencia"]


def test_el_mensaje_sale_de_la_lectura():
    p = pc.construir_payload_lectura(_sel(_lectura_alcista()), ORO, datetime(2026, 10, 12, 11, 0, tzinfo=pc.SANTIAGO), [4119.0, 4120.0])
    p["titular"] = "El oro sigue sobre su línea"
    msg = pc.construir_mensaje_alerta(p)
    assert "📌 Nivel a vigilar: 4.080,00 (línea alcista de seguridad)" in msg
    assert "⬆️ Mientras el precio cierre sobre 4.080,00, la tendencia alcista sigue." in msg
    assert "⏱️ *Temporalidad*: 4H · marco swing (de una a dos semanas)" in msg
    assert "💡 Por qué 4H acá:" in msg
    assert "No hay objetivo fijo." in msg
    assert "falso quiebre" not in msg
    assert "—" not in msg and "–" not in msg


def test_el_mensaje_dice_el_motivo_de_un_fijo_excluido():
    p = pc.construir_payload_lectura(_sel(_lectura_alcista(), gates_omitidos=["va contra la secuencia de los marcos mayores: es donde nacen las falsas rupturas"]),
                                     ORO, datetime(2026, 10, 12, 11, 0, tzinfo=pc.SANTIAGO), [4119.0, 4120.0])
    assert "⚠️ Ojo, va contra la secuencia de los marcos mayores" in pc.construir_mensaje_alerta(p)


def test_la_temporalidad_sale_de_la_estrategia_activa():
    assert pc.marco_operativo() == "H4"
    assert pc.temporalidad_de("H4") == "4H · marco swing (de una a dos semanas)"


def test_un_payload_incoherente_con_su_serie_no_se_arma():
    import pytest
    with pytest.raises(pc.PayloadIncoherenteError):
        pc.construir_payload_lectura(_sel(_lectura_alcista()), ORO, datetime(2026, 10, 12, 11, 0, tzinfo=pc.SANTIAGO), [4000.0, 4010.0])
```

En `tests/test_screener_gi.py`, junto a los tests de notas, el contrato de `notas_marco`:

```python
def test_todo_activo_cubierto_justifica_el_marco_operativo_de_la_estrategia():
    from estrategia import registro
    op = registro.activa().marcos.operativo
    corto = {"H1": "1H", "H4": "4H", "D1": "1D"}[op]
    universo, _ = sc.solo_canales_cubiertos(sc.cargar_universo(True))
    for a in universo:
        nota = (a.get("notas_marco") or {}).get(op, "")
        assert nota, f"{a['ticker']} no trae notas_marco.{op}"
        assert corto in nota, f"{a['ticker']}: la nota de {op} no nombra {corto}"
        assert "—" not in nota and "–" not in nota
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_pipeline_carrusel.py tests/test_screener_gi.py -q -k "lectura or niveles_publicados or temporalidad or fijo_excluido or incoherente_con_su_serie or marco_operativo"`
Expected: FAIL con `AttributeError: module 'pipeline_carrusel' has no attribute 'niveles_publicados'` y la nota faltante.

- [ ] **Step 3: Write the implementation**

`config/activos.json`: en cada uno de los 8 activos, después de `nota_volatilidad`, agregar `notas_marco` con una nota que nombre "4H", hable de marcos y no lleve guion largo. Texto propuesto (el director lo revisa en las piezas de la verificación):

| Ticker | `notas_marco.H4` |
|---|---|
| USDCLP | "el dólar en Chile se mueve en tramos de varios días: en 4H se ven las líneas que esos tramos respetan, sin el ruido de cada hora." |
| USDJPY | "el yen se mueve por diferencias de tasas que tardan días en reflejarse: en 4H se ve la tendencia completa y sus líneas." |
| EURUSD | "el euro avanza en tramos de varios días entre datos y reuniones de bancos centrales: en 4H esos tramos dibujan líneas claras." |
| GBPUSD | "la libra hace movimientos amplios entre reuniones del Banco de Inglaterra: en 4H se leen las líneas sin que cada hora las ensucie." |
| XAUUSD | "el oro se mueve mucho dentro del día, pero sus tramos duran días: en 4H las líneas de tendencia se ven limpias." |
| XAGUSD | "la plata se mueve rápido y con saltos: en 4H esos saltos se ordenan y las líneas de tendencia se pueden trazar." |
| WTI.spot | "el petróleo reacciona fuerte a cada noticia, pero sus tendencias duran semanas: en 4H se separa la noticia de la tendencia." |
| COPPER | "el cobre avanza en tramos amplios que tardan días: en 4H se ven las líneas que esos tramos respetan." |

En `scripts/pipeline_carrusel.py`:

1. Comentario de bloque sobre `MARCOS_CANONICOS`, `TIMEFRAME_GRAFICO`, `construir_payload`, `divergencia_editorial` y `refrescar_payload`: "Transitorio hasta S6/S7 del enchufe: los usan `pipeline_avisos` y `analista`. El carrusel ya sale de la `Lectura`."
2. Funciones nuevas (cerca de `formatear_precio`):

```python
ETIQUETA_CORTA = {"M15": "15M", "H1": "1H", "H4": "4H", "D1": "1D", "W1": "1S"}


def _estrategia():
    from estrategia import registro

    return registro.activa()


def marco_operativo() -> str:
    """El marco de la pieza lo decide la estrategia activa (spec §8.5)."""
    return _estrategia().marcos.operativo


def temporalidad_de(marco: str) -> str:
    etiqueta = _estrategia().marcos.etiquetas[marco]
    return f"{ETIQUETA_CORTA.get(marco, marco)} · marco {etiqueta.nombre} ({etiqueta.duracion})"


def niveles_publicados(lectura) -> tuple[float | None, float | None]:
    """El soporte y la resistencia de la pieza: lo más cercano a cada lado del precio.

    Salen solo de la lectura (lo que vigila, lo que la invalida, el objetivo y las líneas
    que dibuja). Si un lado no tiene nada, queda vacío: inventar un nivel sería publicar
    una distancia con nombre de soporte (el defecto del 2026-10-02).
    """
    candidatos = [r.precio for r in (lectura.vigilar, lectura.invalidacion, lectura.objetivo) if r]
    candidatos += [x.valor_actual for x in lectura.lineas
                   if x.marco == lectura.marco or x.tipo == "horizontal"]
    abajo = [c for c in candidatos if c < lectura.precio]
    arriba = [c for c in candidatos if c > lectura.precio]
    return (max(abajo) if abajo else None, min(arriba) if arriba else None)


def _sesgo_de(direccion: str) -> str:
    return {"ALCISTA": "Alcista", "BAJISTA": "Bajista"}.get(direccion, "Lateral")
```

3. `incoherencia_del_payload`: aceptar `soporte`/`resistencia` en `None` (solo verifica el lado que existe) y leer la escala de `seleccion.get("atr_h1") or seleccion.get("volatilidad_tipica")`. Cambia el mensaje de "ATR de H1" a "la volatilidad típica".

```python
    soporte = seleccion.get("soporte")
    resistencia = seleccion.get("resistencia")
    atr = float(seleccion.get("atr_h1") or seleccion.get("volatilidad_tipica") or 0.0)
    ...
    if (soporte is not None and not float(soporte) < precio) or \
            (resistencia is not None and not precio < float(resistencia)):
        return (f"el precio ({precio}) no cae entre el soporte ({soporte}) y la "
                f"resistencia ({resistencia}): los niveles no corresponden a este precio")
```

4. `construir_payload_lectura`:

```python
def construir_payload_lectura(seleccion: dict[str, Any], activo_catalogo: dict[str, Any],
                              ahora: datetime, cierres: list[float]) -> dict[str, Any]:
    """El payload de una pieza de alerta desde la `Lectura` de la estrategia (spec §7 fase 2)."""
    from estrategia.contrato import lectura_de_dict

    lectura = lectura_de_dict(seleccion["lectura"])
    soporte, resistencia = niveles_publicados(lectura)
    motivo = incoherencia_del_payload(
        {"precio": lectura.precio, "soporte": soporte, "resistencia": resistencia,
         "volatilidad_tipica": seleccion["volatilidad_tipica"]}, cierres)
    if motivo is not None:
        raise PayloadIncoherenteError(f"{seleccion['ticker']}: {motivo}")
    digits = activo_catalogo["digits"]
    marco = seleccion["marco"]
    imagen = activo_catalogo.get("imagen") or ""
    cat_real = activo_catalogo.get("categoria", seleccion["clase"])

    def fmt(valor: float | None) -> str:
        return "--" if valor is None else formatear_precio(valor, digits)

    sesgo = _sesgo_de(lectura.direccion)
    niveles = [{"precio": r.precio, "clase": clase, "etiqueta": fmt(r.precio), "rol": rol}
               for r, clase, rol in ((lectura.objetivo, "meta", "OBJETIVO"),
                                     (lectura.vigilar, "nivel", "VIGILAR"),
                                     (lectura.invalidacion, "soporte" if lectura.direccion == "ALCISTA" else "resistencia", "INVALIDA"))
               if r is not None]
    return {
        "plantilla": "alerta",
        "titular": "", "parrafo": "",
        "activo": activo_catalogo["nombre"],
        "activo_slug": slug_del_activo(seleccion["ticker"], imagen),
        "activo_imagen": imagen,
        "rotulo_activo": f"{activo_catalogo['nombre'].upper()} · {seleccion['ticker']}",
        "chip_categoria": _chip_categoria(cat_real, activo_catalogo["nombre"]),
        "fecha_hora": ahora.strftime("%d %b %Y · %H:%M").upper(),
        "sesgo": sesgo, "tag_riesgo": sesgo.upper(),
        "precio_actual": fmt(lectura.precio),
        "soporte": fmt(soporte), "resistencia": fmt(resistencia),
        "vol_pct": f"{fmt(seleccion['volatilidad_tipica'])} {activo_catalogo['unidad']}",
        "nota_volatilidad": (activo_catalogo.get("notas_marco") or {})[marco],
        "volatilidad": activo_catalogo.get("volatilidad"),
        "marco": marco, "digits": digits,
        "lectura": seleccion["lectura"],
        "aviso_lectura": "; ".join(seleccion.get("gates_omitidos") or []),
        "rotulo_grafico": f"{seleccion['ticker']} · VELAS {ETIQUETA_CORTA.get(marco, marco)}",
        "sello_datos": f"DATOS REALES · METATRADER 5 · {ahora.strftime('%d %b %H:%M').upper()}",
        "fuente": "MT5 · GRUPO INTELIGENCIA",
        "chart_png": None,
        "recorrido": {
            "serie": cierres, "lienzo": "alto",
            "marcadores": [{"indice": len(cierres) - 1, "precio": lectura.precio, "clase": "actual",
                            "etiqueta": fmt(lectura.precio), "rol": "AHORA"}],
            "niveles": niveles,
        },
        "_procedencia": {
            "score": seleccion["score"], "puntaje": seleccion["puntaje"],
            "ticker": seleccion["ticker"], "estrategia": _estrategia().nombre,
            "crudos": {"precio": lectura.precio, "soporte": soporte, "resistencia": resistencia},
        },
        "_pendiente_editorial": list(CAMPOS_EDITORIALES),
    }
```

(`preparar` excluye al activo con un problema si `notas_marco[marco]` falta, igual que hoy con `unidad`.)

5. `lectura_operativa`: al principio,

```python
    if "lectura" in payload:
        return _lectura_operativa_estrategia(payload)
```

con

```python
def _lectura_operativa_estrategia(payload: dict[str, Any]) -> dict[str, Any]:
    from estrategia.contrato import lectura_de_dict

    lectura = lectura_de_dict(payload["lectura"])
    digits = payload["digits"]
    rotulo = payload.get("rotulo_activo", payload["activo"])
    a_favor = {"ALCISTA": "⬆️", "BAJISTA": "⬇️"}.get(lectura.direccion, "↔️")
    if lectura.estado == "PRUEBA":
        a_favor = "↔️"  # la condición se resuelve al cierre: manda la espera (spec §4)
    principal = next(e for e in lectura.escenarios if e.flecha == a_favor)
    corto = ETIQUETA_CORTA.get(lectura.marco, lectura.marco)
    nota = payload.get("nota_volatilidad")
    return {
        "ticker_visible": rotulo.split("·")[-1].strip() if "·" in rotulo else payload["activo"],
        "nivel_vigilar": f"{formatear_precio(lectura.vigilar.precio, digits)} ({lectura.vigilar.etiqueta})",
        "que_esperar": principal.texto,
        "escenarios": [f"{e.flecha} {e.texto}" for e in lectura.escenarios],
        "salida": lectura.salida,
        "temporalidad": temporalidad_de(lectura.marco),
        "por_que_temporalidad": f"Por qué {corto} acá: {nota}" if nota else "",
    }
```

6. `construir_mensaje_alerta`: después de los escenarios y antes de la temporalidad,

```python
    if lectura.get("salida"):
        lineas.append(f"⚠️ {lectura['salida']}")
    if payload.get("aviso_lectura"):
        lineas.append(f"⚠️ Ojo, {payload['aviso_lectura']}.")
```

(El bloque de `banda_estrecha` queda: solo aplica a payloads del camino viejo.)

7. `preparar`: llamar `sc.escanear(...)` sin `ignorar_agotamiento`; borrar el parámetro `forzar` y `--forzar` del CLI; usar `construir_payload_lectura(sel, activo, ahora, cierres)` y `_serie_para(sel["ticker"], sel["marco"])`. `_serie_para` recibe el marco:

```python
def _serie_para(ticker: str, marco: str = TIMEFRAME_GRAFICO) -> list[float]:
    from serie_mt5 import obtener_serie

    cierres, _tiempos = obtener_serie(ticker, marco, VELAS_GRAFICO)
    return cierres
```

8. `rendir`: el gráfico se pide en `payload.get("marco", TIMEFRAME_GRAFICO)` y el índice dice `temporalidad_de(marco_operativo())` en lugar de `MARCOS_CANONICOS[TIMEFRAME_GRAFICO][1]`.

Reescribir en `tests/test_pipeline_carrusel.py` los tests que arman la tanda con el escáner viejo (los que pasan `analizador=` o `forzar=` a `preparar`/`escanear`, y los que afirman el texto del falso quiebre en piezas del carrusel), con selecciones construidas por `_sel(...)`. Los tests de `construir_payload`, `lectura_operativa` y `construir_mensaje_alerta` sin `"lectura"` se conservan: cubren el camino de Avisos y el analista.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_pipeline_carrusel.py tests/test_screener_gi.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/pipeline_carrusel.py config/activos.json tests/test_pipeline_carrusel.py tests/test_screener_gi.py
git commit -m "feat(enchufe): la pieza del carrusel toma dirección, niveles y escenarios de la Lectura"
```

### Task S4-5: El despacho vuelve a pedir la `Lectura` y usa `divergencia()`

**Files:**
- Modify: `scripts/pipeline_carrusel.py` (`refrescar_payload_lectura`, `_refrescar_y_rendir`)
- Test: `tests/test_pipeline_carrusel.py`

**Interfaces:**
- Consumes: `referencia_semanal.{semana_de, lectura_del_dia, SinReferencia, EXTRA}`, `Estrategia.{leer, divergencia}`, `fuente.atr`.
- Produces:
  - `refrescar_payload_lectura(payload, ahora, actual: Lectura, digits: int, cierres: list[float], volatilidad: float, divergencia: Callable[[Lectura, Lectura], str | None]) -> tuple[dict, str | None]`
  - `lectura_para_despacho(estrategia, ticker, digits, lector, ahora, base=rs.DIR) -> tuple[Lectura, dict[str, DataFrame]]`

- [ ] **Step 1: Write the failing tests**

```python
def _payload_listo():
    p = pc.construir_payload_lectura(_sel(_lectura_alcista()), ORO, datetime(2026, 10, 12, 11, 0, tzinfo=pc.SANTIAGO), [4119.0, 4120.0])
    p["titular"], p["parrafo"] = "t", "p"
    p.pop("_pendiente_editorial")
    return p


def test_el_refresco_mueve_el_precio_y_los_niveles_sin_tocar_lo_editorial():
    from dataclasses import replace
    actual = replace(_lectura_alcista(), precio=4130.0)
    nuevo, motivo = pc.refrescar_payload_lectura(_payload_listo(), datetime(2026, 10, 12, 11, 30, tzinfo=pc.SANTIAGO),
                                                 actual, 2, [4129.0, 4130.0], 19.0, lambda a, b: None)
    assert motivo is None
    assert nuevo["precio_actual"] == "4.130,00" and nuevo["vol_pct"] == "19,00 USD"
    assert nuevo["lectura"]["precio"] == 4130.0
    assert nuevo["titular"] == "t" and nuevo["parrafo"] == "p"


def test_el_refresco_respeta_los_niveles_fijados_por_el_director():
    p = _payload_listo()
    p["_procedencia"]["niveles_fijados"] = {"soporte": 4090.0}
    nuevo, _ = pc.refrescar_payload_lectura(p, datetime(2026, 10, 12, 11, 30, tzinfo=pc.SANTIAGO),
                                            _lectura_alcista(), 2, [4119.0, 4120.0], 18.5, lambda a, b: None)
    assert nuevo["soporte"] == "4.090,00"


def test_la_divergencia_de_la_estrategia_frena_la_pieza():
    _, motivo = pc.refrescar_payload_lectura(_payload_listo(), datetime(2026, 10, 12, 11, 30, tzinfo=pc.SANTIAGO),
                                             _lectura_alcista(), 2, [4119.0, 4120.0], 18.5,
                                             lambda a, b: "la dirección cambió de alcista a bajista")
    assert motivo == "la dirección cambió de alcista a bajista"


def test_un_payload_sin_lectura_no_se_despacha(tmp_path, monkeypatch):
    viejo = {"plantilla": "alerta", "titular": "t", "parrafo": "p", "activo": "Oro",
             "_procedencia": {"ticker": "XAUUSD"}}
    (tmp_path / "1_xauusd.json").write_text(json.dumps(viejo), encoding="utf-8")
    monkeypatch.setattr(pc, "falta_metatrader5", lambda: False)
    avisos = pc._refrescar_y_rendir(tmp_path)
    assert (tmp_path / "1_xauusd.json.divergente").exists()
    assert any("antes del enchufe" in a for a in avisos)


def test_sin_referencia_el_despacho_lee_de_nuevo(monkeypatch, tmp_path):
    from estrategia.contrato import Etiqueta, Marcos
    lec = _lectura_alcista()

    class Est:
        marcos = Marcos(("D1",), "H4", {"D1": 5, "H4": 5}, {"D1": Etiqueta("p", "d"), "H4": Etiqueta("s", "u")})

        def leer(self, ticker, velas, digits, en_curso=None):
            return lec

    def lector(ticker, marcos, extra):
        return {"H4": "v"}, None

    lectura, velas = pc.lectura_para_despacho(Est(), "XAUUSD", 2, lector,
                                              datetime(2026, 10, 12, 11, 0, tzinfo=pc.SANTIAGO), base=tmp_path)
    assert lectura == lec and velas == {"H4": "v"}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_pipeline_carrusel.py -q -k "refresco or divergencia_de_la_estrategia or sin_lectura or despacho_lee"`
Expected: FAIL con `AttributeError: ... 'refrescar_payload_lectura'`.

- [ ] **Step 3: Write the implementation**

```python
def lectura_para_despacho(estrategia, ticker: str, digits: int, lector, ahora: datetime,
                          base: Path | None = None):
    """La lectura de ahora para la pieza que va a salir: contra la referencia, como el escáner.

    No guarda reemplazos: eso es del escáner. Si el activo no tiene referencia (una pieza
    hecha con `--todos`, o la semana se borró), lee de nuevo.
    """
    import referencia_semanal as rs

    base = base or rs.DIR
    try:
        diaria = rs.lectura_del_dia(estrategia, ticker, digits, rs.semana_de(ahora), lector, base=base)
        return diaria.lectura, diaria.velas
    except rs.SinReferencia:
        velas, en_curso = lector(ticker, estrategia.marcos, rs.EXTRA)
        return estrategia.leer(ticker, velas, digits, en_curso), velas


def refrescar_payload_lectura(payload: dict[str, Any], ahora: datetime, actual, digits: int,
                              cierres: list[float], volatilidad: float,
                              divergencia) -> tuple[dict[str, Any], str | None]:
    """Vuelve a atar la pieza al mercado de ahora con la lectura nueva (spec §4, `divergencia`).

    Se toca lo que es dato, nunca lo editorial. Si la estrategia dice que el texto ya no
    vale, la pieza no sale.
    """
    from estrategia.contrato import lectura_a_dict, lectura_de_dict

    preparada = lectura_de_dict(payload["lectura"])
    motivo = divergencia(preparada, actual)
    nuevo = json.loads(json.dumps(payload))
    soporte, resistencia = niveles_publicados(actual)
    fijados = nuevo.get("_procedencia", {}).get("niveles_fijados") or {}
    soporte = float(fijados.get("soporte", soporte)) if fijados.get("soporte") or soporte is not None else None
    resistencia = float(fijados.get("resistencia", resistencia)) if fijados.get("resistencia") or resistencia is not None else None

    def fmt(valor: float | None) -> str:
        return "--" if valor is None else formatear_precio(valor, digits)

    unidad = str(nuevo.get("vol_pct", "")).split(" ")[-1]
    nuevo.update({
        "lectura": lectura_a_dict(actual),
        "precio_actual": fmt(actual.precio), "soporte": fmt(soporte), "resistencia": fmt(resistencia),
        "vol_pct": f"{fmt(volatilidad)} {unidad}".strip(),
        "sesgo": _sesgo_de(actual.direccion), "tag_riesgo": _sesgo_de(actual.direccion).upper(),
        "fecha_hora": ahora.strftime("%d %b %Y · %H:%M").upper(),
        "sello_datos": f"DATOS REALES · METATRADER 5 · {ahora.strftime('%d %b %H:%M').upper()}",
    })
    nuevo["_procedencia"]["crudos"] = {"precio": actual.precio, "soporte": soporte, "resistencia": resistencia}
    if motivo is None:
        motivo = incoherencia_del_payload({"precio": actual.precio, "soporte": soporte,
                                           "resistencia": resistencia, "volatilidad_tipica": volatilidad}, cierres)
    recorrido = nuevo.get("recorrido", {})
    recorrido["serie"] = cierres
    recorrido["marcadores"] = [{"indice": max(len(cierres) - 1, 0), "precio": actual.precio,
                                "clase": "actual", "etiqueta": fmt(actual.precio), "rol": "AHORA"}]
    nuevo["recorrido"] = recorrido
    return nuevo, motivo
```

En `_refrescar_y_rendir`, reemplazar el cuerpo del bucle de piezas:

```python
    from estrategia.fuente import atr, velas_mt5

    estrategia = _estrategia()
    for archivo in piezas:
        payload = json.loads(archivo.read_text(encoding="utf-8"))
        ticker = payload.get("_procedencia", {}).get("ticker")
        if "lectura" not in payload:
            avisos.append(f"⚠️ {ticker or archivo.stem} NO se despacha: la pieza se preparó antes del "
                          "enchufe de estrategia y no trae la lectura; se prepara de nuevo")
            _marcar_divergente(dir_grupo, archivo)
            continue
        activo = catalogo.get(ticker)
        if not activo:
            avisos.append(f"{archivo.stem}: sin ticker en la procedencia, se despacha tal cual")
            continue
        try:
            actual, velas = lectura_para_despacho(estrategia, ticker, activo["digits"], velas_mt5, ahora)
            cierres = _serie_para(ticker, payload["marco"])
        except Exception as exc:  # noqa: BLE001
            avisos.append(f"{ticker}: no se pudo refrescar ({exc}). Sale con los datos de la "
                          "preparación, que ya no son de ahora.")
            continue
        nuevo, motivo = refrescar_payload_lectura(
            payload, ahora, actual, activo["digits"], cierres,
            round(atr(velas[payload["marco"]]), activo["digits"]), estrategia.divergencia)
        if motivo:
            avisos.append(f"⚠️ {ticker} NO se despacha: {motivo}")
            _marcar_divergente(dir_grupo, archivo)
            continue
        ...  # escribir, redibujar (timeframe=payload["marco"]) y reescribir el mensaje, como hoy
```

con el renombre a `.divergente` extraído a `_marcar_divergente(dir_grupo, archivo)` (json y png).

Borrar los tests de `tests/test_pipeline_carrusel.py` que fijan el refresco del carrusel por `s1`/`r1` y EMA 50 **a través de `_refrescar_y_rendir`**. Los que llaman `refrescar_payload` y `divergencia_editorial` directo se conservan: son el camino de Avisos hasta S6.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_pipeline_carrusel.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/pipeline_carrusel.py tests/test_pipeline_carrusel.py
git commit -m "feat(enchufe): el despacho vuelve a pedir la Lectura y frena con divergencia()"
```

### Task S4-6: Suplementos, contrato de motivos, comando y documentación

**Files:**
- Modify: `scripts/suplemento_canal.py`, `tests/test_suplemento_canal.py`, `tests/test_guardrails_contrato.py` (si fija los motivos de los gates)
- Modify: `.claude/commands/carrusel.md`, `CLAUDE.md`, `.agents/rules/proyecto.md` (regenerado)
- Modify: `.gitattributes` o nada: `data/referencias_semanales/` se versiona (verificar que `.gitignore` no lo excluya)

**Interfaces:**
- Consumes: los motivos que emite el escáner nuevo: `puntaje.SIN_ESTRUCTURA`, `puntaje.CONTRA_SECUENCIA`, `"ya salio en una corrida anterior de hoy"`, `"no se pudo leer: …"`, feriado, blackout.
- Produces: `suplemento_canal.CATEGORIAS` sin `"ATR diario consumido"`, `"la vela tipica cubre la banda"` ni `"niveles de respaldo por ATR"`; con `"sin líneas trazables"` y `"va contra la secuencia"` como `publicable: False`, y `"ya salio en una corrida anterior"` como `publicable: False`.

- [ ] **Step 1: Write the failing test**

En `tests/test_suplemento_canal.py`:

```python
def test_todo_motivo_del_escaner_nuevo_tiene_categoria_o_no_se_publica():
    from estrategia.tori import puntaje
    import suplemento_canal as su
    for motivo in (puntaje.SIN_ESTRUCTURA, puntaje.CONTRA_SECUENCIA,
                   "ya salio en una corrida anterior de hoy"):
        cat = su.categoria_de(motivo)
        assert cat is not None and cat["publicable"] is False, motivo


def test_las_categorias_de_los_gates_retirados_ya_no_existen():
    import suplemento_canal as su
    assert not any(k in su.CATEGORIAS for k in (
        "ATR diario consumido", "la vela tipica cubre la banda", "niveles de respaldo por ATR"))
```

(Si `categoria_de` no existe con ese nombre, usar la función con que el módulo ya busca el motivo; ver `grep -n "def " scripts/suplemento_canal.py`.)

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_suplemento_canal.py -q`
Expected: FAIL.

- [ ] **Step 3: Implement**

`CATEGORIAS` queda:

```python
CATEGORIAS: dict[str, dict[str, Any]] = {
    "blackout por": {"categoria": "dato_en_curso", "concepto": "precio-descontado", "publicable": True},
    "feriado de": {"categoria": "mercado_cerrado", "concepto": "temporalidades", "publicable": True},
    # Exclusiones de la estrategia (spec §5). No se publican como suplemento: la
    # cobertura fija garantiza una pieza por canal cubierto, y el texto de la exclusión
    # es un motivo técnico, no una lectura para el cliente.
    "sin líneas trazables": {"categoria": "sin_estructura", "concepto": "", "publicable": False},
    "va contra la secuencia": {"categoria": "contra_secuencia", "concepto": "", "publicable": False},
    "ya salio en una corrida anterior": {"categoria": "ya_publicado", "concepto": "", "publicable": False},
}
```

Ajustar los tests de `tests/test_suplemento_canal.py` que fijan `recorrido_agotado`, `banda_estrecha` y `sin_niveles_medidos` (spec §8.3). Ajustar `tests/test_guardrails_contrato.py` si enumera esos motivos.

`.claude/commands/carrusel.md`: quitar `--forzar` y el gate de agotamiento/banda de las instrucciones; agregar un párrafo: "Las diarias cubren los activos del análisis semanal (`data/referencias_semanales/<AAAA-Www>/`). Si la semana no lo tiene, la primera corrida lo hace sola y lo dice en los avisos. La pieza sale de la `Lectura` de la estrategia activa: los escenarios, el nivel a vigilar y la salida no se reescriben; el comando escribe solo `titular` y `parrafo`, y el párrafo no puede contradecir la `Lectura`."

`CLAUDE.md`, sección *El `Score_GI` y sus gates*, primera línea, agregar:

```markdown
> **El carrusel ya no usa este escáner** (enchufe de estrategia, fase 2, 2026-10-11): ordena con
> el puntaje de la estrategia activa contra la referencia semanal (`scripts/referencia_semanal.py`,
> spec `docs/superpowers/specs/2026-10-09-enchufe-estrategia-design.md`). Lo de abajo sigue vivo
> solo para Avisos y el analista hasta S6/S7, y se reescribe en S8.
```

Regenerar: `uv run python scripts/agy_reglas.py` y `uv run python scripts/agy_workflows.py`.

- [ ] **Step 4: Run the full suite**

Run: `uv run pytest -q`
Expected: todo verde salvo los 4 de `tests/test_despacho_avisos.py`.

- [ ] **Step 5: Commit**

```bash
git add scripts/suplemento_canal.py tests/test_suplemento_canal.py tests/test_guardrails_contrato.py .claude/commands/carrusel.md CLAUDE.md .agents/rules/proyecto.md .agents/workflows
git commit -m "chore(enchufe): suplementos, comando y CLAUDE.md siguen al escáner de la estrategia"
```

### Task S4-7: Verificación real y PR

- [ ] **Step 1:** con MT5 abierto en la cuenta de `config/cuenta_mt5.json`:
  `uv run --extra stories --with MetaTrader5 python scripts/pipeline_carrusel.py --preparar --matriz`
  Esperado: si la semana no tenía análisis, el aviso "no había análisis semanal …"; `data/referencias_semanales/<semana>/` con `_semana.json` y un JSON por activo elegido; payloads con `lectura`.
- [ ] **Step 2:** escribir `titular` y `parrafo` de cada payload (el párrafo no contradice la `Lectura`) y `--rendir`. Mirar cada PNG y cada `_mensaje.txt`: tildes, `¿ ¡ ·`, sin guion largo, niveles con `digits`.
- [ ] **Step 3:** `--despachar <tanda> --dry-run`: ninguna pieza `.divergente` salvo que el mercado se haya movido de verdad.
- [ ] **Step 4:** mostrar al director las piezas. **El envío al banco de pruebas (`--despachar --pruebas`) va solo con su aprobación explícita.**
- [ ] **Step 5:** `git add data/referencias_semanales/` (es historia de lo que el cliente leyó), push y PR contra `master`, con las piezas y los avisos del escáner en la descripción.
- [ ] **Step 6:** anotar en la memoria del proyecto y dejar escrito qué recibe S5.

### Lo que S4 le deja a S5

- El gráfico de la pieza ya se pide en el marco operativo, pero todavía dibuja el canal de regresión de `tradingview_grafico._canal` y los niveles `soporte`/`resistencia`. S5 lo cambia por `Lectura.lineas`.
- `pipeline_carrusel.construir_payload`, `refrescar_payload`, `divergencia_editorial`, `MARCOS_CANONICOS` y `TIMEFRAME_GRAFICO` siguen vivos para Avisos y el analista (S6/S7).

---

## Sesión S5 · Gráfico y despacho

Rama: `feat/enchufe-s5-grafico` desde `master` con S4 mergeada. El despacho ya usa `divergencia()` desde S4 (decisión 3); S5 hace el gráfico y la purga.

### Task S5-1: El gráfico dibuja `Lectura.lineas`

**Files:**
- Modify: `scripts/tradingview_grafico.py`, `scripts/pipeline_carrusel.py` (`rendir`, `_refrescar_y_rendir`)
- Test: `tests/test_tradingview_grafico.py`

**Interfaces:**
- Produces: `generar_grafico_tv(ticker, nombre, destino, timeframe, n_velas, digits=None, lineas: tuple[Linea, ...] = (), soporte=None, resistencia=None, ...)`. Con `lineas`, cada diagonal se dibuja desde su primer ancla y se proyecta a la derecha (doctrina 2.1), cada horizontal como nivel, con color por `rol` (la misma tabla `COLOR` de `scripts/tori_revision.py`, que pasa a vivir en `tradingview_grafico`) y su `calidad` en la leyenda. Una línea cuyas anclas no caen en la ventana dibujada se omite y se devuelve en una lista de omitidas, como en `tori_revision._panel`.
- `tori_revision.py --motor tv` usa la misma función.

Tests: una línea diagonal con anclas en la ventana produce una serie de línea con dos puntos que respetan la pendiente; una con ancla fuera se reporta omitida; sin `lineas`, el gráfico no dibuja ningún canal (prueba de que `_canal` ya no existe).

### Task S5-2: Purga de lo que solo usaban el carrusel y el gráfico

- Borrar `tradingview_grafico._canal` y `calcular_estructura` y los indicadores que el gráfico ya no muestra (spec §6), con sus tests.
- `rendir` y `_refrescar_y_rendir` pasan `lineas=lectura.lineas` y dejan de pasar `soporte`/`resistencia`.
- Verificación: `--despachar <tanda> --dry-run` y una tanda real al banco de pruebas con aprobación del director.

---

## Self-review (hecho al escribir)

- Spec §7 fase 2: referencia del lunes (S4-1, S4-3), diaria con `seguir` y `extra=60` (S4-2, S4-3), reemplazo por ruptura (S4-1, S4-2, S4-3), pieza desde la `Lectura` (S4-4), gráfico (S5-1), despacho con `divergencia` (S4-5), borrado de §6 que solo usaban (S4-3, S5-2), tests de EMA 50 y falso quiebre (S4-3, S4-4, S4-5). §8.1 marco desde la estrategia y notas (S4-4). §8.2 nada macro en el escáner (S4-3). §8.3 gates y categorías (S4-3, S4-6). §9 lunes sin correr (S4-3).
- Nombres consistentes entre tareas: `lectura_del_dia`, `Diaria`, `SinReferencia`, `EXTRA`, `correr_semanal`, `evaluar_con_estrategia`, `construir_payload_lectura`, `niveles_publicados`, `refrescar_payload_lectura`, `lectura_para_despacho`, `marco_operativo`, `temporalidad_de`.
