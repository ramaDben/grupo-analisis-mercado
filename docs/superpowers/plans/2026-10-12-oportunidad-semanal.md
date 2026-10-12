# La oportunidad semanal: plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** que el bot de analistas quede con dos comandos: `/oportunidad`, que entrega una pieza HTML semanal con los 6 activos (el análisis de Tori firmado por el director y un panel donde el ejecutivo simula con objetivo 1:3), y `/seguimiento <activo>`, que informa el avance de un activo contra la foto del lunes.

**Architecture:** la lógica pura vive en dos módulos nuevos. `analista/oportunidad.py` pasa de `Lectura` a escenario y simula. `analista/seguimiento.py` evalúa las velas 4H contra la foto. `preparar.py` arma la foto semanal desde `data/referencias_semanales/` (sin correr el escáner), AGY redacta solo los campos sellados y `oportunidad_html.py` arma el HTML con el simulador en JS. Ese simulador vive en un archivo `.js` que el test también corre con node, para que Python y JS redondeen igual. El registro semanal (`data/semanal/registro.json`) guarda una foto por semana, que todos los ejecutivos reusan.

**Tech Stack:** Python 3.12, pytest, Playwright (`story_render`, láminas), Lightweight Charts (`tradingview_grafico`), MetaTrader5 (contrato y velas), node (solo para el test de paridad JS).

**Spec:** `docs/superpowers/specs/2026-10-12-oportunidad-semanal-design.md`

## Global Constraints

- Rama `feat/oportunidad-semanal` desde master; nunca commitear a master. `git add` con rutas explícitas.
- Objetivo de la simulación = **3 × riesgo** (`MULTIPLO = 3`). Rango: stop a **0,5 × ATR 4H** del borde (`PARAMETROS.tolerancia_horizontal_atr`). Sin simulación si el riesgo es **< 0,25 × ATR 4H** (`PARAMETROS.tolerancia_toque_atr`). Los dos se leen de `estrategia.tori.parametros.PARAMETROS` y no se escriben de nuevo.
- Volumen **redondeado hacia abajo** al paso; pérdida recalculada con el volumen real; ganancia = 3 × pérdida. Redondeo de pesos **mitad hacia arriba** (`math.floor(x + 0.5)`, igual que `Math.round`).
- Cuenta MT5 **51257**, resultados en CLP. El contrato sale de `order_calc_profit`, no de `tick_value`.
- Texto de cliente: sin guion largo ni medio, tuteo chileno, precios con los `digits` del activo (`pipeline_carrusel.formatear_precio`), horas en hora Chile. En lo que lee el cliente no aparecen «oportunidad» ni «recomendación», tampoco en el nombre del archivo que viaja.
- El aviso legal es fijo (`AVISO_PIEZA`) y no editable.
- El freno de texto del bot es `esquema.errores` (su equivalente de `exigir_texto_editorial`): con un campo `[[ESCRIBIR]]`, una cifra ajena, «oportunidad» o un `%`, la pieza no sale.
- Firma «Dirección de Análisis Técnico»; no se menciona a la CMF; sin estadística ni tasa de acierto.
- `/seguimiento` nunca informa en pesos ni dice «si hubieras entrado ganarías X».
- El bot no llama a los `preparar()` de producción ni escribe en `data/carrusel`, `data/screener` ni en los historiales de despacho.
- En `recorrido` hay una trampa: es clave reservada de los payloads de `story_render`, así que ningún payload de lámina la usa.
- Tests: `uv run pytest tests/<archivo> -q`. Suite: `uv run pytest -q`.

## Review Focus

1. **Ticker con los dos bordes del rango en diagonal (USDJPY).** El borde vigilado se identifica comparando `vigilar.precio` contra el `valor_actual` de las líneas `rango`, sin suponer que son horizontales. Test en Task 2.
2. **Precio del lunes ya del otro lado de la invalidación** (alcista con el precio bajo la línea). No hay simulación y queda un motivo, nunca un riesgo negativo. Test en Task 2.
3. **Pérdida aceptable vacía, cero o negativa en el panel.** El panel no muestra volumen ni ganancia, solo «Escribe la pérdida aceptable», y Python devuelve `None`. Test en Task 3.
4. **`/seguimiento` de un activo que se escribe distinto** («oro», «xau», «XAUUSD»). Resuelve con `orden.resolver_activo` y solo acepta los de la foto. Test en Task 8.
5. **Una foto de la semana anterior en `registro.json` un lunes temprano.** No se reusa: la clave es la semana ISO de `ahora`. Test en Task 1.

---

## Mapa de archivos

| Archivo | Responsabilidad |
|---|---|
| `scripts/analista/oportunidad.py` (nuevo) | `escenario(lectura)` y `simular(contrato, escenario, perdida, capital)`. Puro, sin I/O |
| `scripts/analista/seguimiento.py` (nuevo) | `evaluar(escenario, velas, precio_vivo)`, `texto_lectura(...)` y `mensaje(...)`. Puro |
| `scripts/analista/registro_semanal.py` (rescatado y reescrito) | Una foto por semana y los seguimientos que se le informaron |
| `scripts/analista/oportunidad_html.py` (nuevo) | El HTML de la pieza: análisis por activo, panel y correo |
| `scripts/analista/comercial.py` (rescatado y reescrito) | Láminas y textos de WhatsApp por activo y del seguimiento |
| `templates/oportunidad/simulador.js` (nuevo) | La simulación en JS, la misma del panel y del test |
| `templates/oportunidad/pieza.html` (nuevo) | La maqueta de la herramienta: análisis, panel, correo |
| `templates/stories/semanal.html`, `seguimiento.html` (rescatados) | Láminas 1920×1080 |
| `scripts/analista/preparar.py` | Queda con `preparar_oportunidad` y `preparar_seguimiento`; se borra lo demás |
| `scripts/analista/orden.py`, `bot.py`, `esquema.py` | Gramática de dos comandos, atención, campos editoriales |
| Se borran | `foco.py`, `plan.py`, `bitacora.py`, `pdf.py`, los `cuerpo_*` de `informe_html.py` y sus tests |

---

### Task 1: Rama, rescate del #254 y registro semanal

**Files:**
- Create: `scripts/analista/registro_semanal.py` (reescrito sobre el del #254)
- Create (rescatados, sin cambios todavía): `templates/stories/semanal.html`, `templates/stories/seguimiento.html`, `tests/fixtures/stories/payloads/semanal.json`, `tests/fixtures/stories/payloads/seguimiento.json`
- Test: `tests/test_analista_registro_semanal.py`

**Interfaces:**
- Produces: `registro_semanal.foto(semana: str, ruta: Path = RUTA) -> dict | None`; `registro_semanal.anotar_foto(semana: str, dir_pedido: Path, creada: datetime, tickers: list[str], ruta: Path = RUTA) -> dict`; `registro_semanal.anotar_seguimiento(semana: str, ticker: str, seguimiento: dict, ruta: Path = RUTA) -> None`; `RUTA = RAIZ / "data" / "semanal" / "registro.json"`.

- [ ] **Step 1: Crear la rama y rescatar los archivos que no dependen del método**

```bash
git checkout master && git pull --ff-only
git checkout -b feat/oportunidad-semanal
git checkout origin/feat/semanal-prototipo -- templates/stories/semanal.html templates/stories/seguimiento.html tests/fixtures/stories/payloads/semanal.json tests/fixtures/stories/payloads/seguimiento.json
```

El correo (`correo.py`, `templates/correo_semanal/`) **no** se rescata como archivo: Task 6 copia de ahí el copiado al portapapeles y los arreglos del Outlook clásico. Para leerlos: `git show origin/feat/semanal-prototipo:templates/correo_semanal/correo.html`.

- [ ] **Step 2: Escribir el test que falla**

```python
"""El registro semanal: una foto por semana, reusada por todos los ejecutivos."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import registro_semanal as rg  # noqa: E402

SCL = ZoneInfo("America/Santiago")


def _pieza(tmp_path: Path, nombre: str) -> Path:
    d = tmp_path / nombre
    d.mkdir()
    (d / "pieza.json").write_text("{}", encoding="utf-8")
    return d


def test_sin_registro_no_hay_foto(tmp_path):
    assert rg.foto("2026-W42", tmp_path / "registro.json") is None


def test_anotar_y_reusar_la_foto_de_la_semana(tmp_path):
    ruta = tmp_path / "registro.json"
    d = _pieza(tmp_path, "a")
    rg.anotar_foto("2026-W42", d, datetime(2026, 10, 12, 9, 0, tzinfo=SCL), ["XAUUSD", "USDCLP"], ruta)
    f = rg.foto("2026-W42", ruta)
    assert f["dir"] == str(d) and f["tickers"] == ["XAUUSD", "USDCLP"]
    assert f["creada"].startswith("2026-10-12T09:00")


def test_la_foto_de_la_semana_anterior_no_se_reusa(tmp_path):
    ruta = tmp_path / "registro.json"
    rg.anotar_foto("2026-W41", _pieza(tmp_path, "a"), datetime(2026, 10, 5, 9, 0, tzinfo=SCL), ["XAUUSD"], ruta)
    assert rg.foto("2026-W42", ruta) is None


def test_una_foto_cuya_carpeta_se_borro_no_se_reusa(tmp_path):
    ruta = tmp_path / "registro.json"
    d = _pieza(tmp_path, "a")
    rg.anotar_foto("2026-W42", d, datetime(2026, 10, 12, 9, 0, tzinfo=SCL), ["XAUUSD"], ruta)
    (d / "pieza.json").unlink()
    assert rg.foto("2026-W42", ruta) is None


def test_los_seguimientos_quedan_en_la_historia_de_la_foto(tmp_path):
    ruta = tmp_path / "registro.json"
    rg.anotar_foto("2026-W42", _pieza(tmp_path, "a"), datetime(2026, 10, 12, 9, 0, tzinfo=SCL), ["XAUUSD"], ruta)
    rg.anotar_seguimiento("2026-W42", "XAUUSD", {"estado": "en_curso", "ejecutivo": "111"}, ruta)
    assert rg.foto("2026-W42", ruta)["seguimientos"] == [
        {"ticker": "XAUUSD", "estado": "en_curso", "ejecutivo": "111"}]
```

- [ ] **Step 3: Correrlo y ver que falla**

Run: `uv run pytest tests/test_analista_registro_semanal.py -q`
Expected: FAIL con `ModuleNotFoundError: No module named 'analista.registro_semanal'`

- [ ] **Step 4: Implementar**

```python
"""Registro de la foto semanal: qué análisis circuló cada semana y qué seguimientos se informaron.

Se versiona, como la bitácora de despachos: es historia de lo que el equipo comercial le
mandó a sus clientes. Cumple dos funciones (spec 2026-10-12-oportunidad-semanal §5):

1. **Reúso semanal.** El estado del bot solo guarda el día en curso, y la foto vale toda la
   semana: el segundo pedido entrega la misma, para todos los ejecutivos.
2. **La foto del lunes.** `/seguimiento` mide contra los precios de esta foto, no contra una
   lectura recalculada.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from analista import RAIZ

RUTA = RAIZ / "data" / "semanal" / "registro.json"


def _leer(ruta: Path) -> list[dict[str, Any]]:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def _escribir(ruta: Path, entradas: list[dict[str, Any]]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(".tmp")
    tmp.write_text(json.dumps(entradas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(ruta)


def foto(semana: str, ruta: Path = RUTA) -> dict[str, Any] | None:
    """La foto de la semana, si su carpeta sigue en disco."""
    for e in reversed(_leer(ruta)):
        if e["semana"] == semana:
            return e if (Path(e["dir"]) / "pieza.json").exists() else None
    return None


def anotar_foto(semana: str, dir_pedido: Path, creada: datetime, tickers: list[str],
                ruta: Path = RUTA) -> dict[str, Any]:
    entradas = _leer(ruta)
    nueva = {"semana": semana, "dir": str(dir_pedido), "creada": creada.isoformat(),
             "tickers": list(tickers), "seguimientos": []}
    entradas.append(nueva)
    _escribir(ruta, entradas)
    return nueva


def anotar_seguimiento(semana: str, ticker: str, seguimiento: dict[str, Any], ruta: Path = RUTA) -> None:
    """Suma un seguimiento a la última foto de la semana: qué se informó, a quién y cuándo."""
    entradas = _leer(ruta)
    for e in reversed(entradas):
        if e["semana"] == semana:
            e.setdefault("seguimientos", []).append({"ticker": ticker, **seguimiento})
            break
    _escribir(ruta, entradas)
```

- [ ] **Step 5: Correrlo y ver que pasa**

Run: `uv run pytest tests/test_analista_registro_semanal.py -q`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add scripts/analista/registro_semanal.py tests/test_analista_registro_semanal.py templates/stories/semanal.html templates/stories/seguimiento.html tests/fixtures/stories/payloads/semanal.json tests/fixtures/stories/payloads/seguimiento.json
git commit -m "feat(semanal): registro de una foto por semana y láminas rescatadas del #254"
```

---

### Task 2: `escenario(lectura)`

**Files:**
- Create: `scripts/analista/oportunidad.py`
- Modify: `tests/analista_fixtures.py` (agregar la fábrica `lectura(...)`)
- Test: `tests/test_analista_oportunidad.py`

**Interfaces:**
- Consumes: `estrategia.contrato.Lectura`, `estrategia.tori.parametros.PARAMETROS`.
- Produces: `oportunidad.MULTIPLO = 3`; `@dataclass(frozen=True) Escenario(ticker: str, estado: str, direccion: str, entrada: float | None, stop: float | None, objetivo: float | None, entrada_pendiente: bool, dias_objetivo: float | None, motivo: str | None)` con la propiedad `simulable: bool` y el método `a_dict() -> dict`; `oportunidad.escenario(lectura: Lectura, digits: int) -> Escenario`; `oportunidad.bordes_rango(lectura) -> tuple[float, float]` (superior, inferior).

- [ ] **Step 1: Agregar la fábrica de lecturas a `tests/analista_fixtures.py`**

Al final del archivo:

```python
from datetime import datetime as _dt  # noqa: E402
from zoneinfo import ZoneInfo as _Zi  # noqa: E402

from estrategia.contrato import Escenario as _Esc  # noqa: E402
from estrategia.contrato import Lectura, Linea, Prueba, Referencia  # noqa: E402

_ESCENARIOS = (
    _Esc("⬆️", "c", "Mientras el precio cierre sobre la línea, la tendencia alcista sigue."),
    _Esc("↔️", "c", "Si el precio vuelve a la línea y la respeta, la línea gana fuerza."),
    _Esc("⬇️", "c", "Si una vela de 4 horas cierra bajo la línea, la tendencia deja de valer."),
)


def _linea(rol: str, valor: float, tipo: str = "diagonal", calidad: str = "A+") -> Linea:
    puntos = ((1790000000, valor - 1.0), (1790500000, valor)) if tipo == "diagonal" else ((1790000000, valor),)
    return Linea(rol, tipo, puntos, "H4", 3, calidad, valor)


def lectura(ticker: str = "XAUUSD", estado: str = "TENDENCIA", direccion: str = "ALCISTA",
            precio: float = 4000.0, invalidacion: float | None = 3950.0, objetivo: float | None = 4100.0,
            atr: float = 20.0, atr_d1: float = 50.0, rango: tuple[float, float] | None = None,
            vigilar: float | None = None, tipo_rango: str = "horizontal", calidad_prueba: str = "A+",
            vela: int = 1790600000) -> Lectura:
    """Una `Lectura` mínima y válida para probar el escenario sin MT5."""
    en_prueba = None
    if estado == "RANGO":
        sup, inf = rango
        l_sup, l_inf = _linea("rango", sup, tipo_rango, ""), _linea("rango", inf, tipo_rango, "")
        arriba = vigilar is None or vigilar == sup
        vig = Referencia(sup if arriba else inf, "resistencia del rango" if arriba else "soporte del rango",
                         l_sup if arriba else l_inf)
        lineas, inv, obj = (l_sup, l_inf), None, None
    else:
        seg = _linea("seguridad", invalidacion if invalidacion is not None else precio, calidad=calidad_prueba)
        lineas = (seg,)
        vig = Referencia(vigilar if vigilar is not None else seg.valor_actual, "línea de seguridad", seg)
        inv = Referencia(invalidacion, "línea de seguridad", seg) if invalidacion is not None else None
        obj = Referencia(objetivo, "resistencia diaria") if objetivo is not None else None
        if estado == "PRUEBA":
            en_prueba = Prueba(seg, seg.valor_actual, _dt(2026, 10, 12, 13, 0, tzinfo=_Zi("America/Santiago")))
    return Lectura(ticker=ticker, marco="H4", precio=precio, direccion=direccion, estado=estado,
                   lineas=lineas, en_prueba=en_prueba, vigilar=vig, invalidacion=inv, objetivo=obj,
                   escenarios=_ESCENARIOS,
                   salida="La posición se cierra con un cierre de 4 horas al otro lado de la línea de seguridad.",
                   conceptos=(), avisos=(), metricas={"atr": atr, "atr_d1": atr_d1}, vela=vela)
```

- [ ] **Step 2: Escribir los tests que fallan**

```python
"""El escenario de la simulación semanal, sacado solo de la `Lectura` de la estrategia."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import oportunidad as op  # noqa: E402


def test_tendencia_alcista_entra_al_precio_del_lunes_con_stop_en_la_invalidacion():
    e = op.escenario(fx.lectura(precio=4000.0, invalidacion=3950.0), 2)
    assert (e.direccion, e.entrada, e.stop, e.objetivo) == ("ALCISTA", 4000.0, 3950.0, 4150.0)
    assert e.simulable and not e.entrada_pendiente
    assert e.dias_objetivo == 3.0  # 150 / ATR D1 50


def test_tendencia_bajista_proyecta_hacia_abajo():
    e = op.escenario(fx.lectura(direccion="BAJISTA", precio=4186.17, invalidacion=4227.32,
                                objetivo=4149.96), 2)
    assert (e.entrada, e.stop, e.objetivo) == (4186.17, 4227.32, 4062.72)


@pytest.mark.parametrize("estado", ["REBOTE", "RUPTURA"])
def test_rebote_y_ruptura_simulan_igual_que_la_tendencia(estado):
    e = op.escenario(fx.lectura(estado=estado), 2)
    assert e.simulable and e.objetivo == 4150.0


def test_rango_con_la_resistencia_vigilada_simula_el_falso_quiebre_bajista():
    e = op.escenario(fx.lectura(ticker="COPPER", estado="RANGO", direccion="LATERAL", precio=14500.0,
                                rango=(14567.0, 14206.0), atr=85.86), 0)
    assert e.direccion == "BAJISTA" and e.entrada_pendiente
    assert (e.entrada, e.stop) == (14567.0, 14610.0)  # 14567 + 0,5 × 85,86, redondeado a digits 0
    assert e.objetivo == 14438.0  # 14567 − 3 × 43


def test_rango_con_el_soporte_vigilado_simula_el_falso_quiebre_alcista():
    e = op.escenario(fx.lectura(ticker="COPPER", estado="RANGO", direccion="LATERAL", precio=14300.0,
                                rango=(14567.0, 14206.0), vigilar=14206.0, atr=86.0), 0)
    assert e.direccion == "ALCISTA" and (e.entrada, e.stop, e.objetivo) == (14206.0, 14163.0, 14335.0)


def test_rango_con_bordes_diagonales_se_identifica_por_valor_actual():
    e = op.escenario(fx.lectura(ticker="USDJPY", estado="RANGO", direccion="LATERAL", precio=157.0,
                                rango=(158.363, 155.35), vigilar=155.35, tipo_rango="diagonal", atr=0.4), 3)
    assert e.direccion == "ALCISTA" and e.entrada == 155.35


def test_prueba_no_simula():
    e = op.escenario(fx.lectura(estado="PRUEBA"), 2)
    assert not e.simulable and "prueba" in e.motivo


def test_sin_invalidacion_no_simula():
    e = op.escenario(fx.lectura(invalidacion=None), 2)
    assert not e.simulable and "invalidación" in e.motivo


def test_riesgo_bajo_un_cuarto_de_atr_no_simula():
    e = op.escenario(fx.lectura(precio=4000.0, invalidacion=3996.0, atr=20.0), 2)  # 4 < 5
    assert not e.simulable and "sobre la línea" in e.motivo


def test_precio_del_otro_lado_de_la_invalidacion_no_simula():
    e = op.escenario(fx.lectura(precio=3940.0, invalidacion=3950.0), 2)
    assert not e.simulable and "otro lado" in e.motivo


def test_a_dict_es_serializable_y_completo():
    d = op.escenario(fx.lectura(), 2).a_dict()
    assert set(d) == {"ticker", "estado", "direccion", "entrada", "stop", "objetivo",
                      "entrada_pendiente", "dias_objetivo", "motivo"}
```

- [ ] **Step 3: Correrlos y ver que fallan**

Run: `uv run pytest tests/test_analista_oportunidad.py -q`
Expected: FAIL con `ImportError: cannot import name 'oportunidad'`

- [ ] **Step 4: Implementar `scripts/analista/oportunidad.py`**

```python
"""La simulación de la pieza semanal: entrada, stop y objetivo 1:3 sobre la lectura.

El objetivo 1:3 NO es de la estrategia (la salida de Tori no tiene objetivo fijo): es la
simulación que el ejecutivo arma para su cliente, y por eso vive acá y no en el análisis
que firma el director (spec 2026-10-12-oportunidad-semanal §1). Todo nivel sale de la
`Lectura`; nada se calcula con indicadores.
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any

from estrategia.contrato import Lectura
from estrategia.tori.parametros import PARAMETROS

MULTIPLO = 3  # objetivo = 3 × riesgo (director, 2026-10-12; la gerencia pidió 1:5 y no cabe)
SIMULAN = {"TENDENCIA", "REBOTE", "RUPTURA"}


@dataclass(frozen=True)
class Escenario:
    ticker: str
    estado: str
    direccion: str  # de la simulación: ALCISTA o BAJISTA ("" sin simulación)
    entrada: float | None
    stop: float | None
    objetivo: float | None
    entrada_pendiente: bool  # rango: el precio todavía tiene que llegar al borde
    dias_objetivo: float | None  # a cuántos ATR D1 del precio está el objetivo
    motivo: str | None  # por qué no hay simulación; None si la hay

    @property
    def simulable(self) -> bool:
        return self.motivo is None

    def a_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sin(lectura: Lectura, motivo: str) -> Escenario:
    return Escenario(lectura.ticker, lectura.estado, "", None, None, None, False, None, motivo)


def bordes_rango(lectura: Lectura) -> tuple[float, float]:
    """(superior, inferior) de las líneas `rango`, por su valor en la última vela."""
    valores = [x.valor_actual for x in lectura.lineas if x.rol == "rango"]
    if len(valores) < 2:
        raise ValueError(f"{lectura.ticker}: el rango no trae sus dos bordes")
    return max(valores), min(valores)


def _redondeo(valor: float, digits: int) -> float:
    return math.floor(valor * 10 ** digits + 0.5) / 10 ** digits


def escenario(lectura: Lectura, digits: int) -> Escenario:
    atr = float(lectura.metricas.get("atr") or 0.0)
    atr_d1 = float(lectura.metricas.get("atr_d1") or 0.0)
    if lectura.estado == "PRUEBA":
        return _sin(lectura, "el precio está en prueba sobre una línea: se espera el cierre de la vela")
    if lectura.estado == "RANGO":
        superior, inferior = bordes_rango(lectura)
        arriba = abs(lectura.vigilar.precio - superior) <= abs(lectura.vigilar.precio - inferior)
        entrada = superior if arriba else inferior
        signo = -1 if arriba else 1  # falso quiebre: desde el borde hacia adentro
        stop = entrada - signo * PARAMETROS.tolerancia_horizontal_atr * atr
        direccion, pendiente = ("BAJISTA" if arriba else "ALCISTA"), True
    elif lectura.estado in SIMULAN:
        if lectura.invalidacion is None:
            return _sin(lectura, "la lectura no trae nivel de invalidación")
        if lectura.direccion not in ("ALCISTA", "BAJISTA"):
            return _sin(lectura, "la lectura no tiene dirección")
        entrada, stop = lectura.precio, lectura.invalidacion.precio
        signo = 1 if lectura.direccion == "ALCISTA" else -1
        direccion, pendiente = lectura.direccion, False
        if (entrada - stop) * signo <= 0:
            return _sin(lectura, "el precio ya está del otro lado de la invalidación")
    else:
        return _sin(lectura, f"estado {lectura.estado} sin simulación")

    entrada, stop = _redondeo(entrada, digits), _redondeo(stop, digits)
    riesgo = abs(entrada - stop)
    if riesgo < PARAMETROS.tolerancia_toque_atr * atr:
        return _sin(lectura, "el precio está sobre la línea: el riesgo es menor que el ruido de una vela")
    objetivo = _redondeo(entrada + signo * MULTIPLO * riesgo, digits)
    dias = round(abs(objetivo - lectura.precio) / atr_d1, 1) if atr_d1 else None
    return Escenario(lectura.ticker, lectura.estado, direccion, entrada, stop, objetivo, pendiente, dias, None)
```

Nota para quien implemente: el stop del cobre es `14567 + 0,5 × 85,86 = 14609,93`, que con `digits = 0` queda en 14610. El riesgo es 43 y el objetivo `14567 − 129 = 14438`. Si algún esperado del test no calza con esta aritmética, el error está en el test: corrígelo con la cuenta a la vista, nunca ajustes el código para que dé el número.

- [ ] **Step 5: Correrlos y ver que pasan**

Run: `uv run pytest tests/test_analista_oportunidad.py -q`
Expected: 12 passed

- [ ] **Step 6: Commit**

```bash
git add scripts/analista/oportunidad.py tests/test_analista_oportunidad.py tests/analista_fixtures.py
git commit -m "feat(semanal): escenario 1:3 desde la lectura de la estrategia"
```

---

### Task 3: La simulación en Python y en JS, con el mismo redondeo

**Files:**
- Modify: `scripts/analista/oportunidad.py`
- Create: `templates/oportunidad/simulador.js`
- Test: `tests/test_analista_oportunidad.py`

**Interfaces:**
- Consumes: `Escenario.a_dict()` (Task 2).
- Produces: `oportunidad.simular(contrato: dict, esc: dict, perdida: float | None, capital: float | None = None) -> dict | None` con las claves `volumen, perdida, ganancia, bajo_minimo, perdida_pct, ganancia_pct`; `None` si la pérdida falta o es ≤ 0. `contrato` trae `clp_unidad, vol_min, vol_paso`. En JS, `function simular(c, e, perdida, capital)` con el mismo contrato y devolviendo `null` en el mismo caso. `oportunidad.SIMULADOR_JS: Path`.

- [ ] **Step 1: Escribir los tests que fallan**

Agregar a `tests/test_analista_oportunidad.py`:

```python
import json
import shutil
import subprocess

CONTRATO = {"clp_unidad": 950.0, "vol_min": 0.01, "vol_paso": 0.01}
ESC = {"entrada": 4000.0, "stop": 3950.0, "objetivo": 4150.0}


def test_simular_redondea_el_volumen_hacia_abajo_y_recalcula_la_perdida():
    s = op.simular(CONTRATO, ESC, 100_000)
    # 100.000 / (50 × 950) = 2,105… → 2,10
    assert s["volumen"] == 2.1 and s["perdida"] == 99_750 and s["ganancia"] == 299_250
    assert s["bajo_minimo"] is False and s["perdida_pct"] is None


def test_simular_bajo_el_minimo_muestra_la_perdida_del_volumen_minimo():
    s = op.simular(CONTRATO, ESC, 100)
    assert s["volumen"] == 0.01 and s["bajo_minimo"] is True and s["perdida"] == 475


def test_simular_con_capital_da_los_porcentajes():
    s = op.simular(CONTRATO, ESC, 100_000, capital=5_000_000)
    assert s["perdida_pct"] == 2.0 and s["ganancia_pct"] == 5.99


@pytest.mark.parametrize("perdida", [None, 0, -5])
def test_simular_sin_perdida_aceptable_no_calcula(perdida):
    assert op.simular(CONTRATO, ESC, perdida) is None


def test_mitad_hacia_arriba_como_math_round():
    c = {"clp_unidad": 1.0, "vol_min": 1.0, "vol_paso": 1.0}
    s = op.simular(c, {"entrada": 10.0, "stop": 9.5, "objetivo": 11.5}, 0.5)
    assert s["perdida"] == 1  # round() de Python daría 0


CASOS_JS = [
    (CONTRATO, ESC, 100_000, None),
    (CONTRATO, ESC, 100, None),
    (CONTRATO, ESC, 100_000, 5_000_000),
    ({"clp_unidad": 6.83, "vol_min": 0.1, "vol_paso": 0.1}, {"entrada": 14567.0, "stop": 14610.0,
                                                             "objetivo": 14438.0}, 37_777, 1_234_567),
    (CONTRATO, ESC, 0, None),
]


@pytest.mark.parametrize("c,e,perdida,capital", CASOS_JS)
def test_el_js_del_panel_simula_igual_que_python(c, e, perdida, capital):
    node = shutil.which("node")
    if not node:
        pytest.skip("sin node para correr el JavaScript del panel")
    js = op.SIMULADOR_JS.read_text(encoding="utf-8")
    llamada = f"console.log(JSON.stringify(simular({json.dumps(c)}, {json.dumps(e)}, {json.dumps(perdida)}, {json.dumps(capital)})));"
    salida = subprocess.run([node, "-e", js + "\n" + llamada], capture_output=True, text=True, check=True)
    assert json.loads(salida.stdout) == op.simular(c, e, perdida, capital)
```

- [ ] **Step 2: Correrlos y ver que fallan**

Run: `uv run pytest tests/test_analista_oportunidad.py -q -k "simular or js or mitad"`
Expected: FAIL con `AttributeError: module 'analista.oportunidad' has no attribute 'simular'`

- [ ] **Step 3: Implementar en Python**

Agregar a `scripts/analista/oportunidad.py`:

```python
from analista import RAIZ

SIMULADOR_JS = RAIZ / "templates" / "oportunidad" / "simulador.js"


def _pesos(valor: float) -> int:
    """Mitad hacia arriba, como `Math.round` del panel: `round` de Python va al par."""
    return math.floor(valor + 0.5)


def _volumen(crudo: float, minimo: float, paso: float) -> tuple[float, bool]:
    if crudo < minimo:
        return minimo, True
    pasos = math.floor((crudo - minimo) / paso + 1e-9)
    return math.floor((minimo + pasos * paso) * 1e8 + 0.5) / 1e8, False


def _pct(valor: float, capital: float | None) -> float | None:
    return math.floor(valor / capital * 10000 + 0.5) / 100 if capital and capital > 0 else None


def simular(contrato: dict[str, Any], esc: dict[str, Any], perdida: float | None,
            capital: float | None = None) -> dict[str, Any] | None:
    """Lo que el panel calcula: volumen para la pérdida aceptable, y la ganancia 1:3.

    `contrato["clp_unidad"]` son los pesos que mueve 1,0 de precio con 1 lote
    (`order_calc_profit`). El panel repite este cálculo en `simulador.js`, y un test los compara.
    """
    if perdida is None or perdida <= 0:
        return None
    riesgo = abs(float(esc["entrada"]) - float(esc["stop"]))
    clp = float(contrato["clp_unidad"])
    vol, bajo = _volumen(perdida / (riesgo * clp), float(contrato["vol_min"]), float(contrato["vol_paso"]))
    p = _pesos(riesgo * clp * vol)
    g = MULTIPLO * p
    return {"volumen": vol, "perdida": p, "ganancia": g, "bajo_minimo": bajo,
            "perdida_pct": _pct(p, capital), "ganancia_pct": _pct(g, capital)}
```

(Mover `from analista import RAIZ` junto a los demás imports del módulo.)

- [ ] **Step 4: Implementar `templates/oportunidad/simulador.js`**

```js
// La simulación del panel. Es la MISMA que `analista.oportunidad.simular`: un test corre este
// archivo con node y compara. Si cambias una, cambia la otra.
var MULTIPLO = 3;
function _pct(valor, capital) {
  return capital > 0 ? Math.round(valor / capital * 10000) / 100 : null;
}
function simular(c, e, perdida, capital) {
  if (perdida === null || perdida === undefined || !(perdida > 0)) return null;
  var riesgo = Math.abs(Number(e.entrada) - Number(e.stop));
  var clp = Number(c.clp_unidad), minimo = Number(c.vol_min), paso = Number(c.vol_paso);
  var crudo = perdida / (riesgo * clp);
  var bajo = crudo < minimo;
  var vol = bajo ? minimo
    : Math.round((minimo + Math.floor((crudo - minimo) / paso + 1e-9) * paso) * 1e8) / 1e8;
  var p = Math.round(riesgo * clp * vol);
  var g = MULTIPLO * p;
  return {volumen: vol, perdida: p, ganancia: g, bajo_minimo: bajo,
          perdida_pct: _pct(p, capital), ganancia_pct: _pct(g, capital)};
}
```

- [ ] **Step 5: Correrlos y ver que pasan**

Run: `uv run pytest tests/test_analista_oportunidad.py -q`
Expected: todos pasan (los 5 de JS pasan con node; sin node se saltan)

- [ ] **Step 6: Commit**

```bash
git add scripts/analista/oportunidad.py templates/oportunidad/simulador.js tests/test_analista_oportunidad.py
git commit -m "feat(semanal): simulación 1:3 en Python y en el JS del panel, con el mismo redondeo"
```

---

### Task 4: El seguimiento contra la foto (puro)

**Files:**
- Create: `scripts/analista/seguimiento.py`
- Test: `tests/test_analista_seguimiento.py`

**Interfaces:**
- Consumes: el `dict` de `Escenario.a_dict()` (Task 2).
- Produces: `seguimiento.ESTADOS = ("entrada_pendiente", "en_curso", "objetivo", "stop")`; `seguimiento.evaluar(esc: dict, velas: list[dict], precio_vivo: float) -> dict` con `{"estado": str, "avance_pct": int | None}` (`velas` son las 4H **cerradas posteriores a la foto**, en orden, con `high`, `low` y `close`); `seguimiento.texto_simulacion(esc: dict, ev: dict, precio_vivo: float, digits: int) -> str`; `seguimiento.texto_lectura(actual: Lectura, reemplazada: bool, digits: int) -> str`; `seguimiento.mensaje(nombre: str, fecha_hoy: str, fecha_foto: str, esc: dict, ev: dict, precio_vivo: float, actual: Lectura, reemplazada: bool, digits: int) -> str`.

- [ ] **Step 1: Escribir los tests que fallan**

```python
"""El seguimiento de la simulación semanal contra la foto del lunes."""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import seguimiento as sg  # noqa: E402

ALZA = {"direccion": "ALCISTA", "entrada": 4000.0, "stop": 3950.0, "objetivo": 4150.0, "entrada_pendiente": False}
RANGO = {"direccion": "BAJISTA", "entrada": 14567.0, "stop": 14610.0, "objetivo": 14438.0, "entrada_pendiente": True}


def v(alto, bajo, cierre=None):
    return {"high": alto, "low": bajo, "close": cierre if cierre is not None else (alto + bajo) / 2}


def test_en_curso_con_el_avance_hacia_el_objetivo():
    ev = sg.evaluar(ALZA, [v(4040, 3990)], 4075.0)
    assert ev == {"estado": "en_curso", "avance_pct": 50}


def test_en_curso_en_contra_da_avance_negativo():
    assert sg.evaluar(ALZA, [v(4010, 3970)], 3975.0)["avance_pct"] == -17


def test_objetivo_alcanzado():
    assert sg.evaluar(ALZA, [v(4040, 3990), v(4151, 4100)], 4120.0)["estado"] == "objetivo"


def test_stop_tocado():
    assert sg.evaluar(ALZA, [v(4010, 3949)], 3990.0)["estado"] == "stop"


def test_una_vela_que_toca_las_dos_puntas_cuenta_stop():
    assert sg.evaluar(ALZA, [v(4160, 3940)], 4100.0)["estado"] == "stop"


def test_el_precio_vivo_cuenta_aunque_la_vela_no_haya_cerrado():
    assert sg.evaluar(ALZA, [], 3949.0)["estado"] == "stop"
    assert sg.evaluar(ALZA, [], 4150.0)["estado"] == "objetivo"


def test_rango_sin_llegar_al_borde_es_entrada_pendiente():
    assert sg.evaluar(RANGO, [v(14550, 14480)], 14520.0) == {"estado": "entrada_pendiente", "avance_pct": None}


def test_rango_que_toca_el_borde_queda_en_curso():
    ev = sg.evaluar(RANGO, [v(14570, 14500)], 14524.0)
    assert ev["estado"] == "en_curso" and ev["avance_pct"] == 33


def test_el_mensaje_no_habla_en_pesos_ni_de_lo_que_se_habria_ganado():
    ev = sg.evaluar(ALZA, [v(4040, 3990)], 4075.0)
    texto = sg.mensaje("Oro", "miércoles 14-10", "lunes 12-10", ALZA, ev, 4075.0, fx.lectura(), False, 2)
    assert "$" not in texto and "CLP" not in texto and "ganarías" not in texto and "hubieras" not in texto
    assert "—" not in texto and "–" not in texto
    assert "te envío una actualización" in texto.lower()
    assert "4.075,00" in texto and "50 %" in texto


def test_la_lectura_reemplazada_se_dice():
    texto = sg.texto_lectura(fx.lectura(), True, 2)
    assert "cambió" in texto


def test_la_lectura_en_prueba_da_la_hora_del_cierre():
    texto = sg.texto_lectura(fx.lectura(estado="PRUEBA"), False, 2)
    assert "13:00" in texto
```

- [ ] **Step 2: Correrlos y ver que fallan**

Run: `uv run pytest tests/test_analista_seguimiento.py -q`
Expected: FAIL con `ImportError: cannot import name 'seguimiento'`

- [ ] **Step 3: Implementar `scripts/analista/seguimiento.py`**

```python
"""El avance de la simulación de la semana contra la foto, y la lectura de hoy, por separado.

Dos cosas distintas, con el mismo peso (spec §6): la simulación se mide contra sus precios
FIJOS del lunes; la lectura de la estrategia sigue la línea en movimiento. Nunca en pesos
(dependen del volumen de cada ejecutivo) y nunca «si hubieras entrado ganarías X».
"""
from __future__ import annotations

from typing import Any

ESTADOS = ("entrada_pendiente", "en_curso", "objetivo", "stop")
SEPARADOR = "━━━━━━━━━━━━━━━━━━━"


def _fmt(valor: float, digits: int) -> str:
    import pipeline_carrusel as pc

    return pc.formatear_precio(valor, digits)


def evaluar(esc: dict[str, Any], velas: list[dict[str, Any]], precio_vivo: float) -> dict[str, Any]:
    """Recorre las velas 4H cerradas desde la foto y termina en el precio vivo.

    Si una misma vela toca el stop y el objetivo, cuenta stop: sin datos dentro de la vela
    no se sabe qué pasó primero, y se cuenta lo prudente.
    """
    alcista = esc["direccion"] == "ALCISTA"
    entrada, stop, obj = float(esc["entrada"]), float(esc["stop"]), float(esc["objetivo"])
    activa = not esc.get("entrada_pendiente")
    tramos = [(float(x["high"]), float(x["low"])) for x in velas] + [(precio_vivo, precio_vivo)]
    for alto, bajo in tramos:
        if not activa:
            if not (bajo <= entrada if alcista else alto >= entrada):
                continue
            activa = True
        if (bajo <= stop) if alcista else (alto >= stop):
            return {"estado": "stop", "avance_pct": None}
        if (alto >= obj) if alcista else (bajo <= obj):
            return {"estado": "objetivo", "avance_pct": 100}
    if not activa:
        return {"estado": "entrada_pendiente", "avance_pct": None}
    avance = (precio_vivo - entrada) / (obj - entrada) * 100
    return {"estado": "en_curso", "avance_pct": int(avance + 0.5) if avance >= 0 else -int(-avance + 0.5)}


def texto_simulacion(esc: dict[str, Any], ev: dict[str, Any], precio_vivo: float, digits: int) -> str:
    f = lambda x: _fmt(x, digits)  # noqa: E731
    estado = ev["estado"]
    if estado == "entrada_pendiente":
        return f"El precio todavía no llega a la entrada de {f(esc['entrada'])}: va en {f(precio_vivo)}."
    if estado == "stop":
        return f"El precio tocó el stop de {f(esc['stop'])}."
    if estado == "objetivo":
        return f"El precio alcanzó el objetivo 1:3 de {f(esc['objetivo'])}."
    pct = ev["avance_pct"]
    if pct >= 0:
        return f"En curso: el precio va en {f(precio_vivo)}, un {pct} % del recorrido hacia el objetivo."
    return (f"En curso: el precio va en {f(precio_vivo)}, un {-pct} % del recorrido en contra, "
            "sin tocar el stop.")


def texto_lectura(actual, reemplazada: bool, digits: int) -> str:
    f = lambda x: _fmt(x, digits)  # noqa: E731
    if reemplazada:
        return (f"La lectura de la semana cambió: ahora se vigila {actual.vigilar.etiqueta} "
                f"en {f(actual.vigilar.precio)}.")
    if actual.estado == "PRUEBA" and actual.en_prueba is not None:
        return (f"El precio está probando {actual.vigilar.etiqueta} en {f(actual.en_prueba.valor_ahora)}: "
                f"se define al cierre de la vela de las {actual.en_prueba.cierre_vela:%H:%M}.")
    return (f"La lectura del lunes sigue en pie: {actual.estado.lower()} "
            f"{actual.direccion.lower()}, con {actual.vigilar.etiqueta} en {f(actual.vigilar.precio)}.")


def mensaje(nombre: str, fecha_hoy: str, fecha_foto: str, esc: dict[str, Any], ev: dict[str, Any],
            precio_vivo: float, actual, reemplazada: bool, digits: int) -> str:
    """El texto de WhatsApp del seguimiento: las dos cosas, con el mismo peso."""
    from analista.comercial import AVISO_PIEZA

    f = lambda x: _fmt(x, digits)  # noqa: E731
    return "\n".join([
        f"📊 *{nombre}* · actualización del {fecha_hoy}",
        "Te envío una actualización del análisis de la semana.",
        SEPARADOR,
        f"🎯 *Simulación de la semana* (precios del {fecha_foto})",
        texto_simulacion(esc, ev, precio_vivo, digits),
        f"Entrada {f(esc['entrada'])} · Stop {f(esc['stop'])} · Objetivo 1:3 {f(esc['objetivo'])}",
        SEPARADOR,
        "📈 *Lectura técnica hoy*",
        texto_lectura(actual, reemplazada, digits),
        SEPARADOR,
        AVISO_PIEZA,
    ])
```

`AVISO_PIEZA` lo define Task 5 en `comercial.py`. Para que este test corra antes, crea ya `scripts/analista/comercial.py` con solo esto (Task 5 lo completa):

```python
"""Lo que sale de la pieza semanal hacia el cliente: láminas y textos de WhatsApp."""
from __future__ import annotations

# Fijo y no editable (spec §7). Sin «recomendación» ni «oportunidad».
AVISO_PIEZA = ("Análisis técnico general, igual para todos sus destinatarios. No es una instrucción "
               "de inversión: un escenario puede cumplirse o invalidarse.")
```

- [ ] **Step 4: Correrlos y ver que pasan**

Run: `uv run pytest tests/test_analista_seguimiento.py -q`
Expected: 11 passed. Ojo con `test_rango_que_toca_el_borde_queda_en_curso`: (14524 − 14567) / (14438 − 14567) = 0,333, o sea 33.

- [ ] **Step 5: Commit**

```bash
git add scripts/analista/seguimiento.py scripts/analista/comercial.py tests/test_analista_seguimiento.py
git commit -m "feat(semanal): seguimiento de la simulación contra la foto y de la lectura de hoy"
```

---

### Task 5: Láminas y textos de WhatsApp

**Files:**
- Modify: `scripts/analista/comercial.py`
- Modify: `templates/stories/semanal.html`, `templates/stories/seguimiento.html`, `tests/fixtures/stories/payloads/semanal.json`, `tests/fixtures/stories/payloads/seguimiento.json`
- Test: `tests/test_analista_comercial.py`

**Interfaces:**
- Consumes: la entrada de un activo en `pieza["datos"]["activos"]` (forma fijada en Task 6, ver abajo); `seguimiento.evaluar`/`texto_*` (Task 4).
- Produces: `comercial.AVISO_PIEZA: str`; `comercial.firma(autor) -> str`; `comercial.payload_semanal(activo: dict, titular: str, datos_al: str, autor, chart: Path) -> dict`; `comercial.payload_seguimiento(activo: dict, ev: dict, precio_vivo: float, lectura_hoy: str, datos_al: str, autor, chart: Path) -> dict`; `comercial.texto_whatsapp_base(activo: dict, titular: str, contexto: str) -> str`; `comercial.rendir(payload: dict, plantilla: str, destino: Path, render=None) -> Path`.

**La entrada de un activo** (la escribe Task 6, y la usan Task 5, 6, 7 y 8):

```python
{
  "ticker": "XAUUSD", "nombre": "Oro", "ticker_visible": "XAU/USD", "digits": 2, "unidad": "USD",
  "puntaje": 90.0,
  "foto": {"guardada": "2026-10-12T09:05:00-03:00", "fecha": "lunes 12-10", "precio": 4186.17},
  "lectura": {...},            # lectura_a_dict de la referencia de la semana
  "escenario": {...},          # Escenario.a_dict()
  "fmt": {"precio": "4.186,17", "vigilar": "4.227,32", "invalidacion": "4.227,32",
          "objetivo_tori": "4.149,96", "entrada": "4.186,17", "stop": "4.227,32",
          "objetivo": "4.062,72", "borde_superior": "", "borde_inferior": ""},
  "contrato": {"clp_unidad": 950.0, "vol_min": 0.01, "vol_paso": 0.01},
  "temporalidad": "4H · swing (de una a dos semanas)",
  "grafico": "grafico_xauusd.png",
}
```

- [ ] **Step 1: Escribir los tests que fallan**

```python
"""Láminas y textos de WhatsApp de la pieza semanal."""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import comercial as cm  # noqa: E402


def test_la_lamina_semanal_muestra_el_analisis_y_no_la_simulacion(tmp_path):
    a = fx.activo_semanal()
    p = cm.payload_semanal(a, "El oro sigue con la línea bajista a favor", "lunes 12-10 · 09:05 CLST",
                           fx.AUTOR, tmp_path / "g.png")
    assert p["valor_1"] == "4.227,32" and p["valor_3"] == "4.149,96"  # vigilar y objetivo de Tori
    assert "4.062,72" not in json.dumps(p, ensure_ascii=False)       # el 1:3 no va en el análisis
    assert "recorrido" not in p                                        # clave reservada de story_render
    assert p["firma"].endswith("Dirección de Análisis Técnico")


def test_la_lamina_de_rango_nombra_los_bordes(tmp_path):
    a = fx.activo_semanal(rango=True)
    p = cm.payload_semanal(a, "El cobre sigue dentro de su rango", "lunes 12-10", fx.AUTOR, tmp_path / "g.png")
    assert p["rotulo_1"] == "Resistencia del rango" and p["rotulo_2"] == "Soporte del rango"


def test_el_texto_base_de_whatsapp_sigue_las_reglas_de_formato():
    t = cm.texto_whatsapp_base(fx.activo_semanal(), "El oro sigue con la línea bajista a favor",
                               "La semana trae el dato de inflación de EE.UU.")
    lineas = t.splitlines()
    assert lineas[0].startswith("🎯 Activo:") and lineas[1].startswith("📌 Nivel a vigilar:")
    assert lineas[2].startswith("⚡ Qué esperar:")
    assert "━━━━━━━━━━━━━━━━━━━" in t and "⏱️ *Temporalidad*" in t
    assert cm.AVISO_PIEZA in t
    for prohibida in ("oportunidad", "recomendaci", "—", "–"):
        assert prohibida not in t.lower()


def test_la_lamina_de_seguimiento_no_lleva_pesos(tmp_path):
    p = cm.payload_seguimiento(fx.activo_semanal(), {"estado": "en_curso", "avance_pct": 40}, 4120.0,
                               "La lectura del lunes sigue en pie.", "miércoles 14-10", fx.AUTOR,
                               tmp_path / "g.png")
    assert p["sello"] == "EN CURSO" and "$" not in json.dumps(p, ensure_ascii=False)
    assert "recorrido" not in p
```

Agregar a `tests/analista_fixtures.py` la entrada de ejemplo:

```python
def activo_semanal(rango: bool = False) -> dict:
    """Una entrada de `datos.activos` como la deja `preparar_oportunidad`."""
    from estrategia.contrato import lectura_a_dict

    from analista import oportunidad as op

    if rango:
        lec = lectura(ticker="COPPER", estado="RANGO", direccion="LATERAL", precio=14500.0,
                      rango=(14567.0, 14206.0), atr=85.86)
        fmt = {"precio": "14500", "vigilar": "14567", "invalidacion": "", "objetivo_tori": "",
               "entrada": "14567", "stop": "14610", "objetivo": "14438",
               "borde_superior": "14567", "borde_inferior": "14206"}
        nombre, visible, digits, unidad = "Cobre", "COPPER", 0, "USD/t"
    else:
        lec = lectura(direccion="BAJISTA", precio=4186.17, invalidacion=4227.32, objetivo=4149.96)
        fmt = {"precio": "4.186,17", "vigilar": "4.227,32", "invalidacion": "4.227,32",
               "objetivo_tori": "4.149,96", "entrada": "4.186,17", "stop": "4.227,32",
               "objetivo": "4.062,72", "borde_superior": "", "borde_inferior": ""}
        nombre, visible, digits, unidad = "Oro", "XAU/USD", 2, "USD"
    return {"ticker": lec.ticker, "nombre": nombre, "ticker_visible": visible, "digits": digits,
            "unidad": unidad, "puntaje": 90.0,
            "foto": {"guardada": "2026-10-12T09:05:00-03:00", "fecha": "lunes 12-10", "precio": lec.precio},
            "lectura": lectura_a_dict(lec), "escenario": op.escenario(lec, digits).a_dict(), "fmt": fmt,
            "contrato": {"clp_unidad": 950.0, "vol_min": 0.01, "vol_paso": 0.01},
            "temporalidad": "4H · swing (de una a dos semanas)", "grafico": f"grafico_{lec.ticker.lower()}.png"}
```

- [ ] **Step 2: Correrlos y ver que fallan**

Run: `uv run pytest tests/test_analista_comercial.py -q`
Expected: FAIL con `AttributeError: module 'analista.comercial' has no attribute 'payload_semanal'`

- [ ] **Step 3: Adaptar las plantillas de lámina**

En `templates/stories/semanal.html`, reemplaza los tokens del método viejo por rótulos y valores genéricos:
- `{{gatillo}}` → `{{valor_1}}`, `{{invalidacion}}` → `{{valor_2}}`, `{{distancia}}` → `{{valor_3}}`.
- El texto fijo del rótulo de cada uno ("Gatillo", "Invalidación", "Recorrido" o el que tenga) → `{{rotulo_1}}`, `{{rotulo_2}}` y `{{rotulo_3}}`. Para ubicarlos: `grep -n "valor_1\|valor_2\|valor_3" -B3 templates/stories/semanal.html`.
- Borra los usos de `{{lado}}` y `{{borde}}` (frases del método viejo) y deja la frase que los contenía como `{{frase_lectura}}`.

En `templates/stories/seguimiento.html`, haz lo mismo: `{{gatillo}}` → `{{valor_1}}` (Entrada), `{{invalidacion}}` → `{{valor_2}}` (Stop), `{{distancia}}` → `{{valor_3}}` (Objetivo 1:3), con sus rótulos `{{rotulo_1..3}}`, y `{{hoy}}` → `{{lectura_hoy}}`. `{{avance}}` y `{{sello}}` se quedan.

Actualiza los dos JSON de `tests/fixtures/stories/payloads/` con las claves nuevas (`rotulo_1..3`, `valor_1..3`, `frase_lectura` o `lectura_hoy`, sin `gatillo`, `invalidacion`, `distancia`, `lado`, `borde` ni `hoy`). La temporalidad del fixture pasa a `"4H · swing (de una a dos semanas)"`.

Run: `uv run pytest tests/test_story_render.py -q`
Expected: PASS (todas las plantillas resuelven sin tokens huérfanos)

- [ ] **Step 4: Implementar `comercial.py`**

```python
"""Lo que sale de la pieza semanal hacia el cliente: láminas y textos de WhatsApp.

Las láminas y el texto base llevan el ANÁLISIS (lo que firma el director). La simulación
1:3 del ejecutivo no va en la lámina: la agrega el panel al texto de WhatsApp, con el
nombre de quien la hizo (spec §1 y §5).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

# Fijo y no editable (spec §7). Sin «recomendación» ni «oportunidad».
AVISO_PIEZA = ("Análisis técnico general, igual para todos sus destinatarios. No es una instrucción "
               "de inversión: un escenario puede cumplirse o invalidarse.")
SEPARADOR = "━━━━━━━━━━━━━━━━━━━"
SELLOS = {"entrada_pendiente": "ENTRADA PENDIENTE", "en_curso": "EN CURSO",
          "objetivo": "OBJETIVO 1:3 ALCANZADO", "stop": "STOP TOCADO"}


def firma(autor) -> str:
    return f"Análisis: {autor.nombre} · {autor.cargo}"


def _niveles(activo: dict[str, Any]) -> list[tuple[str, str]]:
    """Los tres niveles del análisis: los de la lectura, nunca los de la simulación."""
    f, lec = activo["fmt"], activo["lectura"]
    if lec["estado"] == "RANGO":
        vig = "Resistencia" if f["vigilar"] == f["borde_superior"] else "Soporte"
        return [("Resistencia del rango", f["borde_superior"]), ("Soporte del rango", f["borde_inferior"]),
                (f"{vig} que se vigila", f["vigilar"])]
    return [("Nivel a vigilar", f["vigilar"]), ("Invalidación", f["invalidacion"] or "sin nivel"),
            ("Objetivo técnico", f["objetivo_tori"] or "sin nivel")]


def payload_semanal(activo: dict[str, Any], titular: str, datos_al: str, autor, chart: Path) -> dict[str, Any]:
    lec = activo["lectura"]
    niveles = _niveles(activo)
    return {
        "chip": "ANÁLISIS TÉCNICO DE LA SEMANA", "datos_al": datos_al,
        "activo": f"{activo['nombre']} · {activo['ticker_visible']}", "titular": titular,
        "precio": f"{activo['fmt']['precio']} {activo['unidad']}".strip(),
        "direccion": lec["direccion"], "sesgo_slug": lec["direccion"].lower(),
        "frase_lectura": lec["escenarios"][0]["texto"],
        **{f"rotulo_{i}": r for i, (r, _) in enumerate(niveles, 1)},
        **{f"valor_{i}": v for i, (_, v) in enumerate(niveles, 1)},
        "temporalidad": activo["temporalidad"],
        "pie_imagen": f"{activo['nombre']} · velas de 4 horas · MetaTrader 5",
        "firma": firma(autor), "aviso": AVISO_PIEZA, "chart_png": str(chart),
    }


def payload_seguimiento(activo: dict[str, Any], ev: dict[str, Any], precio_vivo: float, lectura_hoy: str,
                        datos_al: str, autor, chart: Path) -> dict[str, Any]:
    from analista.seguimiento import _fmt

    f, esc, d = activo["fmt"], activo["escenario"], activo["digits"]
    avance = {"en_curso": f"{ev['avance_pct']} % del camino al objetivo 1:3" if ev["avance_pct"] is not None else "",
              "entrada_pendiente": "El precio no llega a la entrada",
              "objetivo": "Objetivo 1:3 alcanzado", "stop": "Stop tocado"}[ev["estado"]]
    return {
        "chip": f"SEGUIMIENTO · {SELLOS[ev['estado']]}", "datos_al": datos_al,
        "activo": f"{activo['nombre']} · {activo['ticker_visible']}",
        "direccion": esc["direccion"].lower(), "sello": SELLOS[ev["estado"]],
        "precio_lunes": f["precio"], "precio_hoy": _fmt(precio_vivo, d), "avance": avance,
        "lectura_hoy": lectura_hoy,
        "rotulo_1": "Entrada", "valor_1": f["entrada"], "rotulo_2": "Stop", "valor_2": f["stop"],
        "rotulo_3": "Objetivo 1:3", "valor_3": f["objetivo"],
        "pie_imagen": f"{activo['nombre']} · velas de 4 horas · MetaTrader 5",
        "firma": firma(autor), "aviso": AVISO_PIEZA, "chart_png": str(chart),
    }


def texto_whatsapp_base(activo: dict[str, Any], titular: str, contexto: str) -> str:
    """El texto del análisis, con las 6 reglas de formato. El panel le agrega la simulación."""
    lec = activo["lectura"]
    return "\n".join([
        f"🎯 Activo: {activo['nombre']}",
        f"📌 Nivel a vigilar: *{activo['fmt']['vigilar']}*",
        f"⚡ Qué esperar: {titular}",
        SEPARADOR,
        contexto,
        SEPARADOR,
        *[f"{e['flecha']} {e['texto']}" for e in lec["escenarios"]],
        f"⏱️ *Temporalidad*: {activo['temporalidad']}",
        SEPARADOR,
        AVISO_PIEZA,
    ])


def rendir(payload: dict[str, Any], plantilla: str, destino: Path,
           render: Callable[..., Path] | None = None) -> Path:
    """Lámina horizontal 1920×1080 (`semanal` o `seguimiento`)."""
    import pipeline_avisos as pa

    if render is None:
        from story_render import render_story as render
    render(payload, pa.DIR_PLANTILLAS / f"{plantilla}.html", destino, formato="horizontal")
    return destino
```

Nota: si `escenarios[i]` en `lectura_a_dict` trae la flecha en otra clave, ajusta el acceso (`asdict(Escenario)` da `flecha`, `condicion` y `texto`).

- [ ] **Step 5: Correrlos y ver que pasan**

Run: `uv run pytest tests/test_analista_comercial.py tests/test_story_render.py -q`
Expected: todos pasan

- [ ] **Step 6: Commit**

```bash
git add scripts/analista/comercial.py templates/stories/semanal.html templates/stories/seguimiento.html tests/fixtures/stories/payloads/semanal.json tests/fixtures/stories/payloads/seguimiento.json tests/test_analista_comercial.py tests/analista_fixtures.py
git commit -m "feat(semanal): láminas y texto de WhatsApp con el análisis, sin la simulación"
```

---

### Task 6: La foto semanal (`preparar_oportunidad`) y su esquema

**Files:**
- Modify: `scripts/analista/preparar.py`, `scripts/analista/esquema.py`
- Test: `tests/test_analista_preparar.py` (se reemplaza el contenido de oportunidad), `tests/test_analista_esquema.py`

**Interfaces:**
- Consumes: `referencia_semanal.manifiesto`, `.cargar`, `.ruta`, `.estado_semanal`, `.semana_de`; `oportunidad.escenario`; `estrategia.registro.activa()`; `estrategia.fuente.velas_mt5`.
- Produces: excepciones `preparar.SinSemanaError(PreparacionFallida)` y `preparar.EsperaVelaError(PreparacionFallida)`; `preparar.preparar_oportunidad(orden, dir_pedido, ahora, lec) -> Preparada`, cuyo `pieza["datos"]` es `{"semana", "chip", "edicion", "activos": [entrada de Task 5], "agenda_semana": [str], "curva": [[str]]}` y su editorial `titular`, `bajada`, más los anidados `titulares.<ticker>` y `contexto.<ticker>`; el campo nuevo de `Lectores` es `contrato: Callable[[str, float], dict]`, junto a `estrategia: Callable[[], Any]` y `velas: Callable` (el lector de `referencia_semanal`). En `esquema`, `CAMPOS["oportunidad"] = ("titular", "bajada")`, `CAMPOS["seguimiento"] = ()` y `LARGO_MAXIMO_ANIDADO = {"titulares": 70}`.

- [ ] **Step 1: Escribir los tests que fallan**

Reemplaza en `tests/test_analista_preparar.py` todo lo de `preparar_oportunidad`, `foco`, `activo`, `calendario`, `dato` y `jornada` por lo siguiente (los demás tests de esas piezas se borran en Task 9):

```python
import json
from types import SimpleNamespace

import referencia_semanal as rs
from estrategia.contrato import lectura_a_dict

SEMANA = "2026-W42"
AHORA_LUNES = datetime(2026, 10, 12, 9, 30, tzinfo=SCL)


class EstrategiaFalsa:
    nombre = "tori"

    class marcos:
        operativo = "H4"
        etiquetas = {"H4": SimpleNamespace(nombre="swing", duracion="de una a dos semanas")}


def _sembrar(base, lecturas, puntajes):
    for lec in lecturas:
        rs.guardar(lec, SEMANA, "semanal", AHORA_LUNES, base=base)
    rs.guardar_manifiesto(SEMANA, {"semana": SEMANA, "elegidos": [l.ticker for l in lecturas],
                                   "puntajes": puntajes, "excluidos": []}, base=base)


def _grafico_falso(ticker, nombre, lectura, destino):
    destino.write_bytes(fx.PNG)
    return destino


def _lectores(base, filas_estado=None, **kw):
    def estado(_est, semana, _lector, _ahora, _digits, base=base):
        if filas_estado is not None:
            return filas_estado
        return [{"ticker": t, "espera_hasta": None} for t in rs.manifiesto(semana, base)["elegidos"]]
    return pr.Lectores(
        base_referencias=base, estado_semanal=estado, estrategia=lambda: EstrategiaFalsa(),
        contrato=lambda t, p: {"clp_unidad": 950.0, "vol_min": 0.01, "vol_paso": 0.01},
        grafico_lectura=_grafico_falso,
        catalogo=lambda t: {"ticker": t, "nombre": {"XAUUSD": "Oro", "COPPER": "Cobre"}[t],
                            "digits": {"XAUUSD": 2, "COPPER": 0}[t], "unidad": "USD"},
        drivers=lambda t: ["Dollar Index"], agenda=lambda a: ([], []), curva=lambda: ({}, []),
        cuenta=lambda: None, **kw)


def test_sin_analisis_semanal_no_hay_pieza(tmp_path):
    with pytest.raises(pr.SinSemanaError, match="análisis semanal"):
        pr.preparar(Orden("oportunidad"), tmp_path / "p", AHORA_LUNES, _lectores(tmp_path / "ref"))


def test_con_una_linea_a_mas_en_prueba_espera_el_cierre(tmp_path):
    base = tmp_path / "ref"
    _sembrar(base, [fx.lectura()], {"XAUUSD": 90.0})
    filas = [{"ticker": "XAUUSD", "espera_hasta": datetime(2026, 10, 12, 13, 0, tzinfo=SCL)}]
    with pytest.raises(pr.EsperaVelaError, match="13:00"):
        pr.preparar(Orden("oportunidad"), tmp_path / "p", AHORA_LUNES, _lectores(base, filas))


def test_la_foto_trae_los_activos_en_orden_de_puntaje(tmp_path):
    base = tmp_path / "ref"
    cobre = fx.lectura(ticker="COPPER", estado="RANGO", direccion="LATERAL", precio=14500.0,
                       rango=(14567.0, 14206.0), atr=85.86)
    _sembrar(base, [cobre, fx.lectura()], {"XAUUSD": 90.0, "COPPER": 5.0})
    hecha = pr.preparar(Orden("oportunidad"), tmp_path / "p", AHORA_LUNES, _lectores(base))
    activos = hecha.pieza["datos"]["activos"]
    assert [a["ticker"] for a in activos] == ["XAUUSD", "COPPER"]
    oro = activos[0]
    assert oro["escenario"]["objetivo"] == 4150.0 and oro["fmt"]["objetivo"] == "4.150,00"
    assert oro["contrato"]["clp_unidad"] == 950.0
    assert oro["temporalidad"] == "4H · swing (de una a dos semanas)"
    assert (tmp_path / "p" / oro["grafico"]).exists()
    assert hecha.pieza["anidados"] == {"titulares": ["XAUUSD", "COPPER"], "contexto": ["XAUUSD", "COPPER"]}


def test_la_foto_no_toca_los_directorios_de_produccion(tmp_path, monkeypatch):
    base = tmp_path / "ref"
    _sembrar(base, [fx.lectura()], {"XAUUSD": 90.0})
    antes = {p: p.stat().st_mtime for p in (RAIZ / "data").glob("carrusel/**/*") if p.is_file()}
    pr.preparar(Orden("oportunidad"), tmp_path / "p", AHORA_LUNES, _lectores(base))
    assert {p: p.stat().st_mtime for p in (RAIZ / "data").glob("carrusel/**/*") if p.is_file()} == antes
```

Y en `tests/test_analista_esquema.py`:

```python
def test_oportunidad_exige_titular_por_activo_de_hasta_70():
    p = es.nueva_pieza("oportunidad", {}, {"activos": []}, {},
                       extra_campos={"titulares": ["XAUUSD"], "contexto": ["XAUUSD"]})
    p["editorial"] = {"titular": "La semana técnica", "bajada": "Seis activos con su lectura.",
                      "titulares": {"XAUUSD": "x" * 71}, "contexto": {"XAUUSD": "Texto."}}
    assert any("titulares.XAUUSD" in e and "70" in e for e in es.errores(p))


def test_oportunidad_rechaza_la_palabra_oportunidad_y_porcentajes():
    p = es.nueva_pieza("oportunidad", {}, {"activos": []}, {},
                       extra_campos={"titulares": ["XAUUSD"], "contexto": ["XAUUSD"]})
    p["editorial"] = {"titular": "Una oportunidad en el oro", "bajada": "Sube 2 %",
                      "titulares": {"XAUUSD": "Oro"}, "contexto": {"XAUUSD": "Texto."}}
    errs = es.errores(p)
    assert any("oportunidad" in e for e in errs) and any("porcentaje" in e for e in errs)
```

- [ ] **Step 2: Correrlos y ver que fallan**

Run: `uv run pytest tests/test_analista_preparar.py tests/test_analista_esquema.py -q`
Expected: FAIL (`SinSemanaError` no existe; `Lectores` no acepta `base_referencias`)

- [ ] **Step 3: Esquema**

En `scripts/analista/esquema.py`:
- `CAMPOS` queda solo con `"oportunidad": ("titular", "bajada")` y `"seguimiento": ()` (el seguimiento no pasa por AGY, pero su `pieza.json` usa el mismo sello).
- Agregar `LARGO_MAXIMO_ANIDADO = {"titulares": 70}` y, en `errores`, después del bucle de `LARGO_MAXIMO`:

```python
    for campo, tope in LARGO_MAXIMO_ANIDADO.items():
        for clave, texto in (editorial.get(campo) or {}).items():
            if len(str(texto)) > tope:
                errs.append(f"{campo}.{clave}: tiene {len(str(texto))} caracteres y el máximo es {tope}")
```

- Renombrar los comentarios de `FRASES_PROHIBIDAS_FOCO` («El foco técnico…») a la pieza semanal. El chequeo `if tipo == "oportunidad"` se queda tal cual, y su mensaje cambia a «la pieza semanal describe un escenario».

- [ ] **Step 4: `preparar_oportunidad`**

En `scripts/analista/preparar.py`:

```python
class SinSemanaError(PreparacionFallida):
    """La semana no tiene análisis semanal: el bot no corre el escáner (spec §5)."""


class EsperaVelaError(PreparacionFallida):
    """Una línea A+ está en prueba: la foto espera el cierre de esa vela (spec §5)."""


def _contrato(ticker: str, precio: float) -> dict[str, Any]:
    """Lo que el panel necesita para simular, medido en la cuenta declarada.

    `order_calc_profit` y no `tick_value` (miente en los CFD de acciones). Son cálculos, no órdenes.
    """
    from market_data_mcp import mt5_client

    try:
        mt5_client.connect()
        import MetaTrader5 as mt5  # noqa: PLC0415

        mt5.symbol_select(ticker, True)
        info = mt5.symbol_info(ticker)
        clp_unidad = mt5.order_calc_profit(mt5.ORDER_TYPE_BUY, ticker, 1.0, precio, precio + 1.0)
    except Exception as exc:  # noqa: BLE001
        raise PreparacionFallida(f"no pude leer el contrato de {ticker} ({exc.__class__.__name__})") from exc
    if not info or not clp_unidad:
        raise PreparacionFallida(f"el terminal no calculó el contrato de {ticker}: sin él no hay simulación")
    return {"clp_unidad": float(clp_unidad), "vol_min": float(info.volume_min),
            "vol_paso": float(info.volume_step)}


def _grafico_lectura(ticker: str, nombre: str, lectura, destino: Path) -> Path:
    from tradingview_grafico import generar_grafico_tv

    return generar_grafico_tv(ticker=ticker, nombre=nombre, destino=destino, timeframe=lectura.marco,
                              lineas=lectura.lineas)


def _estrategia():
    from estrategia import registro

    return registro.activa()


def _estado_semanal(estrategia, semana, lector, ahora, digits, base=None):
    import referencia_semanal as rs

    return rs.estado_semanal(estrategia, semana, lector, ahora, digits, base=base or rs.DIR)


def _velas(ticker, marcos, extra=0):
    from estrategia.fuente import velas_mt5

    return velas_mt5(ticker, marcos, extra)
```

Los campos de `Lectores` quedan así (se borran los del foco, la jornada y el dato):

```python
@dataclass
class Lectores:
    contrato: Callable[[str, float], dict[str, Any]] = _contrato
    grafico_lectura: Callable[..., Path] = _grafico_lectura
    estrategia: Callable[[], Any] = _estrategia
    estado_semanal: Callable[..., list[dict[str, Any]]] = _estado_semanal
    velas: Callable[..., Any] = _velas
    agenda: Callable[[datetime], tuple[list[dict[str, Any]], list[str]]] = _agenda
    curva: Callable[[], tuple[dict[str, Any], list[str]]] = _curva
    drivers: Callable[[str], list[str]] = _drivers
    cuenta: Callable[[], str | None] = _cuenta
    catalogo: Callable[[str], dict[str, Any]] = _catalogo_de
    base_referencias: Path | None = None
```

```python
DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")


def fecha_corta(momento: datetime) -> str:
    m = momento.astimezone(SANTIAGO)
    return f"{DIAS[m.weekday()]} {m:%d-%m}"


def _entrada_activo(ticker: str, referencia, guardada: datetime, puntaje: float, dir_pedido: Path,
                    lec: Lectores, estrategia) -> dict[str, Any]:
    import pipeline_carrusel as pc
    from estrategia.contrato import lectura_a_dict

    from analista import oportunidad as op

    cat = lec.catalogo(ticker)
    d = int(cat["digits"])
    f = lambda x: pc.formatear_precio(x, d) if x is not None else ""  # noqa: E731
    esc = op.escenario(referencia, d)
    sup = inf = None
    if referencia.estado == "RANGO":
        sup, inf = op.bordes_rango(referencia)
    grafico = f"grafico_{ticker.lower().replace('.', '_')}.png"
    lec.grafico_lectura(ticker, cat["nombre"], referencia, dir_pedido / grafico)
    etiqueta = estrategia.marcos.etiquetas[referencia.marco]
    return {
        "ticker": ticker, "nombre": cat["nombre"], "ticker_visible": cat.get("ticker_visible", ticker),
        "digits": d, "unidad": cat.get("unidad") or "", "puntaje": puntaje,
        "foto": {"guardada": guardada.isoformat(), "fecha": fecha_corta(guardada), "precio": referencia.precio},
        "lectura": lectura_a_dict(referencia), "escenario": esc.a_dict(),
        "fmt": {"precio": f(referencia.precio), "vigilar": f(referencia.vigilar.precio),
                "invalidacion": f(referencia.invalidacion.precio if referencia.invalidacion else None),
                "objetivo_tori": f(referencia.objetivo.precio if referencia.objetivo else None),
                "entrada": f(esc.entrada), "stop": f(esc.stop), "objetivo": f(esc.objetivo),
                "borde_superior": f(sup), "borde_inferior": f(inf)},
        "contrato": lec.contrato(ticker, referencia.precio) if esc.simulable else None,
        "temporalidad": f"{pc.ETIQUETA_CORTA.get(referencia.marco, referencia.marco)} · "
                        f"{etiqueta.nombre} ({etiqueta.duracion})",
        "grafico": grafico,
    }


def preparar_oportunidad(orden: Orden, dir_pedido: Path, ahora: datetime, lec: Lectores) -> Preparada:
    """La foto de la semana: los elegidos del análisis semanal, con su referencia del lunes."""
    import referencia_semanal as rs

    base = lec.base_referencias or rs.DIR
    semana = rs.semana_de(ahora)
    manifiesto = rs.manifiesto(semana, base)
    if manifiesto is None:
        raise SinSemanaError(f"La semana {semana} todavía no tiene análisis semanal: la pieza sale "
                             "cuando el escáner la fije.")
    estrategia = lec.estrategia()
    digits = {t: int(lec.catalogo(t)["digits"]) for t in manifiesto["elegidos"]}
    esperas = [f["espera_hasta"] for f in lec.estado_semanal(estrategia, semana, lec.velas, ahora, digits,
                                                             base=base) if f.get("espera_hasta")]
    if esperas:
        hora = max(esperas).astimezone(SANTIAGO)
        raise EsperaVelaError(f"Una línea clave está en prueba: se publica al cierre de la vela de las "
                              f"{hora:%H:%M}.")
    puntajes = manifiesto.get("puntajes", {})
    orden_tickers = sorted(manifiesto["elegidos"], key=lambda t: (-float(puntajes.get(t, 0)), t))
    activos, avisos = [], []
    for ticker in orden_tickers:
        referencia = rs.cargar(semana, ticker, base)
        if referencia is None:
            avisos.append(f"{ticker} no tiene referencia en {semana}: queda fuera")
            continue
        guardada = datetime.fromisoformat(
            json.loads(rs.ruta(semana, ticker, base).read_text(encoding="utf-8"))["guardada"])
        activos.append(_entrada_activo(ticker, referencia, guardada, float(puntajes.get(ticker, 0)),
                                       dir_pedido, lec, estrategia))
    agenda, av = lec.agenda(ahora)
    avisos += [f"contexto sin agenda: {a}" for a in av]
    curva, av = lec.curva()
    avisos += [f"contexto sin curva de tasas: {a}" for a in av]
    datos = {"semana": semana, "chip": "ANÁLISIS TÉCNICO DE LA SEMANA",
             "edicion": fecha_corta(ahora) + f" · {ahora.astimezone(SANTIAGO):%H:%M}",
             "activos": activos, "drivers": {a["ticker"]: lec.drivers(a["ticker"]) for a in activos},
             "agenda_semana": [f"{ev.get('hora', '')} · {ev.get('nombre', ev.get('evento', ''))}" for ev in agenda]}
    tickers = [a["ticker"] for a in activos]
    pieza = es.nueva_pieza("oportunidad", {"semana": semana}, datos,
                           {a["ticker"]: a["grafico"] for a in activos},
                           extra_campos={"titulares": tickers, "contexto": tickers})
    return Preparada(pieza, avisos)
```

Antes de escribir `agenda_semana`, mira las claves que de verdad devuelve `pipeline_linkedin.leer_agenda` (`grep -n "eventos.append" -A6 scripts/pipeline_linkedin.py`) y arma la línea con esas. La curva va en `datos` sin `%` (pasa por `_contexto_sin_porcentajes`), así AGY no la cita como porcentaje.

`PREPARADORES = {"oportunidad": preparar_oportunidad, "seguimiento": preparar_seguimiento}` y `CON_TERMINAL = {"oportunidad", "seguimiento"}`. Mientras Task 8 no exista, deja `"seguimiento"` fuera.

Asegúrate de que `referencia_semanal.guardar` escribe la clave `"guardada"` (lo hace: `['ticker', 'semana', 'motivo', 'guardada', 'lectura']`).

- [ ] **Step 5: Correrlos y ver que pasan**

Run: `uv run pytest tests/test_analista_preparar.py tests/test_analista_esquema.py -q`
Expected: los tests nuevos pasan. Los viejos de las otras piezas, si quedaron, fallan por los lectores borrados, y se eliminan en Task 9.

- [ ] **Step 6: Commit**

```bash
git add scripts/analista/preparar.py scripts/analista/esquema.py tests/test_analista_preparar.py tests/test_analista_esquema.py
git commit -m "feat(semanal): la foto de la semana desde las referencias del análisis semanal"
```

---

### Task 7: El HTML de la pieza (análisis, panel y correo)

**Files:**
- Create: `scripts/analista/oportunidad_html.py`, `templates/oportunidad/pieza.html`
- Test: `tests/test_analista_oportunidad_html.py`

**Interfaces:**
- Consumes: la pieza de Task 6 ya redactada; `comercial.texto_whatsapp_base`, `comercial.AVISO_PIEZA`; `informe_html.e`, `informe_html.bloque_firma`, `informe_html._data_uri`, `informe_html.LOGO`; `oportunidad.SIMULADOR_JS`.
- Produces: `oportunidad_html.armar(pieza: dict, dir_pedido: Path, ejecutivo: dict, autor, hoy: date) -> str`; `oportunidad_html.guardar(pieza, dir_pedido, ejecutivo, autor, hoy) -> Path`, que escribe `analisis-semanal_<semana>_<slug-ejecutivo>.html`; `oportunidad_html.InformeInvalido(ValueError)`.

**La maqueta.** Una página con tres zonas:
1. **Encabezado:** logo, «Análisis técnico de la semana», semana y `edicion`, titular y bajada de AGY.
2. **Un bloque por activo**, en el orden de `datos.activos`:
   - **Análisis** (la firma del director): gráfico en base64, dirección, estado, la tabla de niveles de `comercial._niveles`, los tres escenarios ⬆️ ↔️ ⬇️, la salida, el titular y el contexto de AGY, y la temporalidad. Se rotula «Análisis: <autor> · Dirección de Análisis Técnico».
   - **Panel de simulación** (`<div class="panel" data-ticker="…">`): casilla `incluir`, pérdida aceptable en CLP (`input type=number min=0`), capital opcional y los resultados (volumen, pérdida y ganancia lado a lado y del mismo tamaño, % si hay capital). Lleva el rótulo «Objetivo de la simulación (1:3)» con entrada, stop y objetivo, y «Simulación realizada por <ejecutivo>». Si `fmt.objetivo` está lejos (`escenario.dias_objetivo` > 0), suma la línea «El objetivo está a N días de movimiento típico (ATR diario)». Si `escenario.motivo` no es nulo, el panel no tiene inputs y muestra «Sin simulación esta semana: <motivo>».
   - **Botones:** «Copiar texto de WhatsApp» (texto base + la simulación si hay pérdida escrita) y «Descargar lámina» (el PNG de la lámina en base64).
3. **El correo:** el botón «Copiar correo para Outlook» arma, con los activos marcados, un correo en tablas de 640 px (el patrón del #254) y lo copia con `ClipboardItem` `text/html`. Copia la función `copiarCorreo` y los arreglos del Outlook clásico desde `git show origin/feat/semanal-prototipo:templates/correo_semanal/correo.html` (líneas del `<script>`, `copiarCorreo` y `copiarCodigo`) y de `cuerpo.html` (tablas con estilos en línea, sin `rgba`, fuentes de respaldo).

Los datos de cada activo van incrustados como JSON (`<script id="datos" type="application/json">`): escenario, contrato, `fmt`, el texto base de WhatsApp y el HTML del bloque del correo ya escapado. El simulador se incrusta leyendo `SIMULADOR_JS`, nunca copiado a mano.

La línea de simulación que el JS agrega al texto de WhatsApp:

```
🧮 Simulación de {ejecutivo} (objetivo 1:3): con una pérdida aceptable de ${perdida}, el volumen es {volumen} y el objetivo daría ${ganancia}. Entrada {entrada} · Stop {stop} · Objetivo {objetivo}.
```

Pérdida y ganancia van en la misma frase. Si `bajo_minimo`, se agrega: «La pérdida mínima con el volumen más chico es ${perdida}.»

- [ ] **Step 1: Escribir los tests que fallan**

```python
"""El HTML de la pieza semanal: análisis firmado, panel del ejecutivo y correo."""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import esquema as es  # noqa: E402
from analista import oportunidad as op  # noqa: E402
from analista import oportunidad_html as oh  # noqa: E402

HOY = date(2026, 10, 12)
EJECUTIVO = {"nombre": "Camila Rojas", "cargo": "Ejecutiva comercial", "contacto": "+56 9 1111 2222"}


def _pieza(tmp_path):
    activos = [fx.activo_semanal(), fx.activo_semanal(rango=True)]
    for a in activos:
        (tmp_path / a["grafico"]).write_bytes(fx.PNG)
        (tmp_path / f"lamina_{a['ticker'].lower()}.png").write_bytes(fx.PNG)
    tickers = [a["ticker"] for a in activos]
    p = es.nueva_pieza("oportunidad", {"semana": "2026-W42"},
                       {"semana": "2026-W42", "chip": "ANÁLISIS TÉCNICO DE LA SEMANA", "edicion": "lunes 12-10 · 09:30",
                        "activos": activos, "drivers": {}, "agenda_semana": []},
                       {a["ticker"]: a["grafico"] for a in activos},
                       extra_campos={"titulares": tickers, "contexto": tickers})
    p["editorial"] = {"titular": "La semana técnica en seis activos", "bajada": "Lectura de cada activo.",
                      "titulares": {t: f"Titular de {t}" for t in tickers},
                      "contexto": {t: f"Contexto de {t}." for t in tickers}}
    return p


def test_el_analisis_va_firmado_y_la_simulacion_rotulada(tmp_path):
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    assert "Dirección de Análisis Técnico" in html
    assert "Objetivo de la simulación (1:3)" in html
    assert "Simulación realizada por Camila Rojas" in html


def test_el_simulador_incrustado_es_el_del_archivo(tmp_path):
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    assert op.SIMULADOR_JS.read_text(encoding="utf-8").strip() in html


def test_los_datos_incrustados_traen_contrato_y_escenario(tmp_path):
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    crudo = re.search(r'<script id="datos" type="application/json">(.*?)</script>', html, re.S).group(1)
    datos = json.loads(crudo)
    assert datos["activos"][0]["escenario"]["objetivo"] == 4062.72
    assert datos["activos"][0]["contrato"]["vol_min"] == 0.01


def test_un_activo_sin_simulacion_muestra_el_motivo_y_no_tiene_inputs(tmp_path):
    p = _pieza(tmp_path)
    p["datos"]["activos"][0]["escenario"]["motivo"] = "la lectura no trae nivel de invalidación"
    p["datos"]["activos"][0]["contrato"] = None
    p["huella"] = es._huella(p)
    html = oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    assert "Sin simulación esta semana: la lectura no trae nivel de invalidación" in html
    bloque = html.split('data-ticker="XAUUSD"')[1].split('data-ticker="COPPER"')[0]
    assert 'name="perdida"' not in bloque


def test_lo_que_lee_el_cliente_no_dice_oportunidad_ni_recomendacion(tmp_path):
    html = oh.armar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    correo = re.findall(r'<template class="correo-activo"[^>]*>(.*?)</template>', html, re.S)
    assert correo
    for bloque in correo:
        assert "oportunidad" not in bloque.lower() and "recomendaci" not in bloque.lower()
        assert "—" not in bloque and "–" not in bloque
    assert "un escenario puede cumplirse o invalidarse" in html


def test_un_texto_invalido_no_arma_la_pieza(tmp_path):
    p = _pieza(tmp_path)
    p["editorial"]["contexto"]["XAUUSD"] = es.MARCA
    with pytest.raises(oh.InformeInvalido):
        oh.armar(p, tmp_path, EJECUTIVO, fx.AUTOR, HOY)


def test_el_nombre_del_archivo_no_dice_oportunidad(tmp_path):
    ruta = oh.guardar(_pieza(tmp_path), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    assert ruta.name == "analisis-semanal_2026-W42_camila-rojas.html"
```

- [ ] **Step 2: Correrlos y ver que fallan**

Run: `uv run pytest tests/test_analista_oportunidad_html.py -q`
Expected: FAIL con `ImportError: cannot import name 'oportunidad_html'`

- [ ] **Step 3: Implementar `oportunidad_html.py`**

```python
"""La pieza semanal en HTML: el análisis firmado, el panel del ejecutivo y el correo.

Es una herramienta interna (spec §2): por eso sale en HTML y no en PDF. Lo que llega al
cliente es lo que el ejecutivo copia desde acá: el correo, el texto de WhatsApp y la lámina.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from analista import RAIZ
from analista import comercial as cm
from analista import esquema as es
from analista import informe_html as ih
from analista import oportunidad as op

PLANTILLA = RAIZ / "templates" / "oportunidad" / "pieza.html"


class InformeInvalido(ValueError):
    """La pieza no pasó los controles: no se arma."""


def _filas_niveles(a: dict[str, Any]) -> str:
    return "".join(f"<tr><th>{ih.e(r)}</th><td class=\"cifra\">{ih.e(v)}</td></tr>"
                   for r, v in cm._niveles(a))


def _panel(a: dict[str, Any], ejecutivo: str) -> str:
    esc, f = a["escenario"], a["fmt"]
    if esc["motivo"]:
        return (f'<div class="panel sin-simulacion"><p>Sin simulación esta semana: {ih.e(esc["motivo"])}</p></div>')
    lejos = (f'<p class="nota">El objetivo está a {str(esc["dias_objetivo"]).replace(".", ",")} días de '
             'movimiento típico (ATR diario).</p>' if esc["dias_objetivo"] else "")
    return (
        '<div class="panel">'
        '<h4>Objetivo de la simulación (1:3)</h4>'
        f'<p class="niveles-sim">Entrada {ih.e(f["entrada"])} · Stop {ih.e(f["stop"])} · '
        f'Objetivo {ih.e(f["objetivo"])}</p>{lejos}'
        '<label><input type="checkbox" name="incluir" checked> Incluir en el correo</label>'
        '<label>Pérdida aceptable (CLP)<input type="number" name="perdida" min="0" step="1000"></label>'
        '<label>Capital (opcional)<input type="number" name="capital" min="0" step="10000"></label>'
        '<div class="resultado"><div class="perdida"><span>Pérdida si toca el stop</span><strong data-r="perdida">'
        'Escribe la pérdida aceptable</strong></div><div class="ganancia"><span>Ganancia si llega al objetivo</span>'
        '<strong data-r="ganancia"></strong></div><p data-r="volumen"></p></div>'
        f'<p class="autor-sim">Simulación realizada por {ih.e(ejecutivo)}</p>'
        '</div>'
    )


def _bloque_correo(a: dict[str, Any], titular: str, contexto: str, dir_pedido: Path) -> str:
    """El bloque del activo en el correo: tablas de 640 px, estilos en línea (Outlook clásico)."""
    filas = "".join(
        f'<tr><td style="padding:6px 0;color:#9aa4b2;font:600 13px Segoe UI,Arial,sans-serif">{ih.e(r)}</td>'
        f'<td style="padding:6px 0;text-align:right;color:#ffffff;font:700 15px Segoe UI,Arial,sans-serif">{ih.e(v)}</td></tr>'
        for r, v in cm._niveles(a))
    return (
        '<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="width:640px;background:#16202b">'
        f'<tr><td style="padding:18px 24px;color:#50C0A8;font:700 13px Segoe UI,Arial,sans-serif">{ih.e(a["nombre"])} · {ih.e(a["ticker_visible"])}</td></tr>'
        f'<tr><td style="padding:0 24px;color:#ffffff;font:700 20px Segoe UI,Arial,sans-serif">{ih.e(titular)}</td></tr>'
        f'<tr><td style="padding:12px 24px"><img src="{ih._data_uri(dir_pedido / a["grafico"])}" width="592" style="width:592px;display:block" alt="{ih.e(a["nombre"])}"></td></tr>'
        f'<tr><td style="padding:0 24px;color:#d6dde6;font:500 15px/23px Segoe UI,Arial,sans-serif">{ih.e(contexto)}</td></tr>'
        f'<tr><td style="padding:12px 24px"><table role="presentation" width="100%">{filas}</table></td></tr>'
        '<tr><td class="sim-correo" style="padding:0 24px 18px"></td></tr>'
        '</table>'
    )


def armar(pieza: dict[str, Any], dir_pedido: Path, ejecutivo: dict[str, Any], autor, hoy: date) -> str:
    errs = es.errores(pieza)
    if errs:
        raise InformeInvalido("; ".join(errs))
    d, ed = pieza["datos"], pieza["editorial"]
    nombre_ej = ejecutivo["nombre"]
    bloques, correos, datos_js = [], [], []
    for a in d["activos"]:
        t = a["ticker"]
        lec = a["lectura"]
        escenarios = "".join(f"<li>{ih.e(x['flecha'])} {ih.e(x['texto'])}</li>" for x in lec["escenarios"])
        lamina = dir_pedido / f"lamina_{t.lower().replace('.', '_')}.png"
        bloques.append(
            f'<section class="activo" data-ticker="{ih.e(t)}">'
            f'<header><h2>{ih.e(a["nombre"])} · {ih.e(a["ticker_visible"])}</h2>{ih.pildora(lec["direccion"].capitalize())}</header>'
            f'<div class="analisis"><h3>{ih.e(ed["titulares"][t])}</h3>'
            f'<img src="{ih._data_uri(dir_pedido / a["grafico"])}" alt="Gráfico de {ih.e(a["nombre"])}">'
            f'<p>{ih.e(ed["contexto"][t])}</p><table class="niveles">{_filas_niveles(a)}</table>'
            f'<ul class="escenarios">{escenarios}</ul><p class="salida">{ih.e(lec["salida"])}</p>'
            f'<p class="temporalidad">⏱️ {ih.e(a["temporalidad"])} · Foto del {ih.e(a["foto"]["fecha"])}, '
            f'precio {ih.e(a["fmt"]["precio"])}</p>'
            f'<p class="firma-analisis">Análisis: {ih.e(autor.nombre)} · {ih.e(autor.cargo)}</p></div>'
            f'{_panel(a, nombre_ej)}'
            '<div class="acciones"><button type="button" class="copiar-wa">Copiar texto de WhatsApp</button>'
            + (f'<a class="descargar" download="{ih.e(lamina.name)}" href="{ih._data_uri(lamina)}">Descargar lámina</a>'
               if lamina.exists() else "")
            + '</div></section>')
        correos.append(f'<template class="correo-activo" data-ticker="{ih.e(t)}">'
                       f'{_bloque_correo(a, ed["titulares"][t], ed["contexto"][t], dir_pedido)}</template>')
        datos_js.append({"ticker": t, "digits": a["digits"], "escenario": a["escenario"], "contrato": a["contrato"],
                         "fmt": a["fmt"], "whatsapp": cm.texto_whatsapp_base(a, ed["titulares"][t], ed["contexto"][t])})
    tokens = {
        "titulo": ih.e(ed["titular"]), "logo": ih._data_uri(ih.LOGO), "semana": ih.e(d["semana"]),
        "edicion": ih.e(d["edicion"]), "titular": ih.e(ed["titular"]), "bajada": ih.e(ed["bajada"]),
        "activos": "".join(bloques), "correos": "".join(correos), "firma": ih.bloque_firma(autor, hoy),
        "aviso": ih.e(cm.AVISO_PIEZA), "ejecutivo": ih.e(nombre_ej),
        "datos": json.dumps({"ejecutivo": nombre_ej, "activos": datos_js}, ensure_ascii=False).replace("</", "<\\/"),
        "simulador": op.SIMULADOR_JS.read_text(encoding="utf-8").strip(),
    }
    return re.sub(r"\{\{(\w+)\}\}", lambda m: tokens[m.group(1)], PLANTILLA.read_text(encoding="utf-8"))


def guardar(pieza: dict[str, Any], dir_pedido: Path, ejecutivo: dict[str, Any], autor, hoy: date) -> Path:
    ruta = dir_pedido / f"analisis-semanal_{pieza['datos']['semana']}_{ih.slug(ejecutivo['nombre'])}.html"
    ruta.write_text(armar(pieza, dir_pedido, ejecutivo, autor, hoy), encoding="utf-8")
    return ruta
```

Verifica `ih.pildora` e `ih.slug` antes de usarlos (`informe_html.py:94` y `:47`). Si `slug` no da `camila-rojas` para «Camila Rojas», usa `re.sub(r"[^a-z0-9]+", "-", es._plano(nombre)).strip("-")`.

- [ ] **Step 4: Escribir `templates/oportunidad/pieza.html`**

Una página con los tokens `{{titulo}} {{logo}} {{semana}} {{edicion}} {{titular}} {{bajada}} {{activos}} {{correos}} {{firma}} {{aviso}} {{ejecutivo}} {{datos}} {{simulador}}`. Los estilos van en `<style>` y los colores salen de `templates/stories/marca.css`: cópialos como variables CSS con los mismos nombres de rol, sin hex sueltos fuera de `:root`. El esqueleto:

```html
<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{titulo}}</title>
<style>
  :root{--fondo:#0b1118;--tarjeta:#16202b;--texto-1:#ffffff;--texto-2:#d6dde6;--acento:#50C0A8;--sube:#2ecc71;--baja:#e74c3c;--linea:#26323f;}
  body{margin:0;background:var(--fondo);color:var(--texto-1);font:500 15px/1.5 "Segoe UI",Arial,sans-serif}
  main{max-width:1100px;margin:0 auto;padding:24px}
  .activo{background:var(--tarjeta);border:1px solid var(--linea);border-radius:16px;padding:20px;margin:20px 0;display:grid;grid-template-columns:3fr 2fr;gap:20px}
  .activo header,.activo .acciones{grid-column:1/-1}
  .analisis img{width:100%;border-radius:10px}
  .panel{background:var(--fondo);border-radius:12px;padding:16px}
  .panel label{display:block;margin:10px 0}
  .panel input[type=number]{width:100%;height:40px;font-size:16px}
  .resultado{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  .resultado .perdida strong,.resultado .ganancia strong{display:block;font-size:22px}
  .resultado .perdida strong{color:var(--baja)} .resultado .ganancia strong{color:var(--sube)}
  .aviso{color:var(--texto-2);font-size:13px}
</style></head>
<body><main>
<header class="portada"><img src="{{logo}}" alt="Grupo Inteligencia" height="40">
  <p class="chip">ANÁLISIS TÉCNICO DE LA SEMANA · {{semana}} · {{edicion}}</p>
  <h1>{{titular}}</h1><p>{{bajada}}</p></header>
{{activos}}
<section class="correo"><h2>Correo para tu cliente</h2>
  <p>Marca los activos que quieres incluir y copia el correo: se pega en Outlook con el formato.</p>
  <button type="button" id="copiar-correo">Copiar correo para Outlook</button> <span id="estado"></span>
  <div id="vista-correo"></div></section>
{{correos}}
{{firma}}
<p class="aviso">{{aviso}}</p>
</main>
<script id="datos" type="application/json">{{datos}}</script>
<script id="simulador">{{simulador}}</script>
<script>
(function(){
  var DATOS = JSON.parse(document.getElementById('datos').textContent);
  function pesos(n){ return '$' + Math.round(n).toLocaleString('es-CL'); }
  function num(v){ var x = parseFloat(v); return isNaN(x) ? null : x; }
  function estado(panel, d){
    var s = simular(d.contrato, d.escenario, num(panel.querySelector('[name=perdida]').value),
                    num(panel.querySelector('[name=capital]').value));
    var r = function(k){ return panel.querySelector('[data-r=' + k + ']'); };
    if (!s){ r('perdida').textContent = 'Escribe la pérdida aceptable'; r('ganancia').textContent = ''; r('volumen').textContent = ''; return null; }
    r('perdida').textContent = pesos(s.perdida) + (s.perdida_pct !== null ? ' (' + String(s.perdida_pct).replace('.', ',') + ' %)' : '');
    r('ganancia').textContent = pesos(s.ganancia) + (s.ganancia_pct !== null ? ' (' + String(s.ganancia_pct).replace('.', ',') + ' %)' : '');
    r('volumen').textContent = 'Volumen ' + String(s.volumen).replace('.', ',') + (s.bajo_minimo ? ': es el mínimo, la pérdida no alcanza para menos' : '');
    return s;
  }
  function lineaSim(d, s){
    if (!s) return '';
    var f = d.fmt;
    var t = '🧮 Simulación de ' + DATOS.ejecutivo + ' (objetivo 1:3): con una pérdida aceptable de ' + pesos(s.perdida) +
            ', el volumen es ' + String(s.volumen).replace('.', ',') + ' y el objetivo daría ' + pesos(s.ganancia) +
            '. Entrada ' + f.entrada + ' · Stop ' + f.stop + ' · Objetivo ' + f.objetivo + '.';
    if (s.bajo_minimo) t += ' La pérdida mínima con el volumen más chico es ' + pesos(s.perdida) + '.';
    return t;
  }
  DATOS.activos.forEach(function(d){
    var sec = document.querySelector('.activo[data-ticker="' + d.ticker + '"]');
    var panel = sec.querySelector('.panel');
    var actual = null;
    if (panel && d.contrato) panel.querySelectorAll('input[type=number]').forEach(function(i){
      i.addEventListener('input', function(){ actual = estado(panel, d); });
    });
    sec.querySelector('.copiar-wa').addEventListener('click', function(){
      var texto = d.whatsapp + (actual ? '\n' + lineaSim(d, actual) : '');
      navigator.clipboard.writeText(texto);
    });
    d._sim = function(){ return actual; };
  });
  // copiarCorreo: arma el correo con los activos marcados y lo copia como text/html.
  // Pega acá la función del #254 (templates/correo_semanal/correo.html), cambiando la fuente
  // del cuerpo por los <template class="correo-activo"> de los marcados, y en cada uno
  // escribe en .sim-correo la frase de lineaSim(d, d._sim()) si hay simulación.
})();
</script>
</body></html>
```

El comentario de `copiarCorreo` es la única pieza que se trae del #254: reemplázalo por la función real antes de cerrar el task. Las demás, como están.

- [ ] **Step 5: Correrlos y ver que pasan**

Run: `uv run pytest tests/test_analista_oportunidad_html.py -q`
Expected: 7 passed

- [ ] **Step 6: Probar el panel en un navegador**

Genera una pieza con el fixture (`uv run python -c "..."` que llame a `oh.guardar` con `_pieza`) y ábrela. Revisa: al escribir 100000 en la pérdida del oro, el volumen y la pérdida coinciden con `op.simular`; «Copiar texto de WhatsApp» trae la línea de simulación; el correo copiado se pega en Outlook con tablas y colores (si no hay Outlook a mano, pégalo en un documento de Word); los acentos y el `·` se ven bien.

- [ ] **Step 7: Commit**

```bash
git add scripts/analista/oportunidad_html.py templates/oportunidad/pieza.html tests/test_analista_oportunidad_html.py
git commit -m "feat(semanal): HTML de la pieza con el análisis firmado, el panel 1:3 y el correo"
```

---

### Task 8: `preparar_seguimiento`

**Files:**
- Modify: `scripts/analista/preparar.py`
- Test: `tests/test_analista_preparar.py`

**Interfaces:**
- Consumes: `registro_semanal.foto` (Task 1); `seguimiento.evaluar`, `.texto_lectura`, `.mensaje` (Task 4); `comercial.payload_seguimiento`, `.rendir` (Task 5); `referencia_semanal.lectura_del_dia`, `.cargar`, `.firma`, `.SinReferencia`.
- Produces: `preparar.preparar_seguimiento(orden, dir_pedido, ahora, lec) -> Preparada`, con `orden.args == {"ticker": str}` y `pieza["datos"]` = `{"semana", "ticker", "nombre", "evaluacion", "precio_vivo", "lectura_hoy", "reemplazada", "whatsapp", "edicion"}`. `pieza["orden"]["pieza"] == "seguimiento"` y sin campos editoriales. `preparar.FueraDeLaFotoError(PreparacionFallida)` y `preparar.SinFotoError(PreparacionFallida)`. Campo nuevo de `Lectores`: `registro: Path | None = None` (ruta del registro, para tests).

- [ ] **Step 1: Escribir los tests que fallan**

```python
from analista import registro_semanal as rg


def _foto(tmp_path, base, activos):
    """Una foto ya armada en el registro, como la deja /oportunidad."""
    d = tmp_path / "foto"
    d.mkdir()
    p = es.nueva_pieza("oportunidad", {"semana": SEMANA}, {"semana": SEMANA, "activos": activos}, {},
                       extra_campos={"titulares": [a["ticker"] for a in activos],
                                     "contexto": [a["ticker"] for a in activos]})
    pr.guardar_pieza(p, d)
    rg.anotar_foto(SEMANA, d, AHORA_LUNES, [a["ticker"] for a in activos], tmp_path / "registro.json")


def _lectores_seg(tmp_path, base, velas, precio):
    def lector(ticker, marcos, extra=0):
        return {"H4": velas}, None
    lec = _lectores(base, registro=tmp_path / "registro.json", velas=lector)
    lec.lectura_del_dia = lambda est, t, d, sem, lector, base=None: rs.Diaria(
        fx.lectura(precio=precio), None, (), {"H4": velas}, fx.lectura())
    return lec


def test_seguimiento_de_un_activo_fuera_de_la_foto_lista_los_que_si(tmp_path):
    base = tmp_path / "ref"
    _sembrar(base, [fx.lectura()], {"XAUUSD": 90.0})
    _foto(tmp_path, base, [fx.activo_semanal()])
    with pytest.raises(pr.FueraDeLaFotoError, match="Oro"):
        pr.preparar(Orden("seguimiento", {"ticker": "USDCLP"}), tmp_path / "s", AHORA_LUNES,
                    _lectores_seg(tmp_path, base, pd.DataFrame(), 4000.0))


def test_seguimiento_sin_foto_de_la_semana(tmp_path):
    with pytest.raises(pr.SinFotoError, match="/oportunidad"):
        pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s", AHORA_LUNES,
                    _lectores_seg(tmp_path, tmp_path / "ref", pd.DataFrame(), 4000.0))


def test_seguimiento_informa_simulacion_y_lectura_por_separado(tmp_path):
    base = tmp_path / "ref"
    _sembrar(base, [fx.lectura()], {"XAUUSD": 90.0})
    oro = fx.activo_semanal()
    _foto(tmp_path, base, [oro])
    foto_vela = oro["lectura"]["vela"]
    velas = pd.DataFrame([{"time": foto_vela, "open": 1, "high": 4300, "low": 3000, "close": 1},  # anterior: no cuenta
                          {"time": foto_vela + 14400, "open": 4180, "high": 4190, "low": 4150, "close": 4160}])
    hecha = pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s",
                        datetime(2026, 10, 14, 11, 0, tzinfo=SCL), _lectores_seg(tmp_path, base, velas, 4124.0))
    d = hecha.pieza["datos"]
    assert d["evaluacion"]["estado"] == "en_curso"
    assert "Simulación de la semana" in d["whatsapp"] and "Lectura técnica hoy" in d["whatsapp"]
    assert "$" not in d["whatsapp"]
```

(Importa `pandas as pd` al principio del archivo de tests.)

- [ ] **Step 2: Correrlos y ver que fallan**

Run: `uv run pytest tests/test_analista_preparar.py -q -k seguimiento`
Expected: FAIL (`FueraDeLaFotoError` no existe)

- [ ] **Step 3: Implementar**

En `Lectores` agrega `registro: Path | None = None` y `lectura_del_dia: Callable[..., Any] = _lectura_del_dia`, con:

```python
def _lectura_del_dia(estrategia, ticker, digits, semana, lector, base=None):
    import referencia_semanal as rs

    return rs.lectura_del_dia(estrategia, ticker, digits, semana, lector, base=base or rs.DIR)


class SinFotoError(PreparacionFallida):
    """La semana no tiene foto todavía."""


class FueraDeLaFotoError(PreparacionFallida):
    """El activo no está en la foto de esta semana."""


def preparar_seguimiento(orden: Orden, dir_pedido: Path, ahora: datetime, lec: Lectores) -> Preparada:
    """El avance de un activo contra la foto: la simulación y la lectura de hoy, por separado."""
    import referencia_semanal as rs
    from estrategia.contrato import lectura_de_dict

    from analista import comercial as cm
    from analista import registro_semanal as rg
    from analista import seguimiento as sg

    semana = rs.semana_de(ahora)
    foto = rg.foto(semana, lec.registro or rg.RUTA)
    if foto is None:
        raise SinFotoError("Esta semana todavía no hay análisis publicado: pide primero /oportunidad.")
    pieza_foto = cargar_pieza(Path(foto["dir"]))
    activos = {a["ticker"]: a for a in pieza_foto["datos"]["activos"]}
    ticker = orden.args["ticker"]
    if ticker not in activos:
        nombres = ", ".join(a["nombre"] for a in activos.values())
        raise FueraDeLaFotoError(f"Ese activo no está en el análisis de esta semana. Los de esta semana: {nombres}.")
    a = activos[ticker]
    esc = a["escenario"]
    if esc["motivo"]:
        raise PreparacionFallida(f"{a['nombre']} no tiene simulación esta semana: {esc['motivo']}.")
    referencia_foto = lectura_de_dict(a["lectura"])
    base = lec.base_referencias or rs.DIR
    estrategia = lec.estrategia()
    try:
        diaria = lec.lectura_del_dia(estrategia, ticker, a["digits"], semana, lec.velas, base=base)
    except rs.SinReferencia as exc:
        raise PreparacionFallida(f"{ticker}: {exc}") from exc
    vigente = rs.cargar(semana, ticker, base)
    reemplazada = diaria.reemplazo is not None or (vigente is not None and rs.firma(vigente) != rs.firma(referencia_foto))
    h4 = diaria.velas[referencia_foto.marco]
    posteriores = h4[h4["time"] > referencia_foto.vela].to_dict("records") if len(h4) else []
    precio = diaria.lectura.precio
    ev = sg.evaluar(esc, posteriores, precio)
    lectura_hoy = sg.texto_lectura(diaria.lectura, reemplazada, a["digits"])
    hoy = fecha_corta(ahora)
    texto = sg.mensaje(a["nombre"], hoy, a["foto"]["fecha"], esc, ev, precio, diaria.lectura, reemplazada,
                       a["digits"])
    lec.grafico_lectura(ticker, a["nombre"], diaria.lectura, dir_pedido / "grafico.png")
    datos = {"semana": semana, "ticker": ticker, "nombre": a["nombre"], "evaluacion": ev, "precio_vivo": precio,
             "lectura_hoy": lectura_hoy, "reemplazada": reemplazada, "whatsapp": texto,
             "edicion": f"{hoy} · {ahora.astimezone(SANTIAGO):%H:%M}", "activo": a}
    pieza = es.nueva_pieza("seguimiento", {"ticker": ticker}, datos, {"principal": "grafico.png"})
    return Preparada(pieza, list(diaria.avisos))
```

Agrega `"seguimiento": preparar_seguimiento` a `PREPARADORES` y `"seguimiento"` a `CON_TERMINAL`. La lámina se rinde en el bot (Task 9), con `cm.payload_seguimiento` y `cm.rendir`, para que los tests de preparar no necesiten Playwright.

- [ ] **Step 4: Correrlos y ver que pasan**

Run: `uv run pytest tests/test_analista_preparar.py -q`
Expected: los de oportunidad y seguimiento pasan

- [ ] **Step 5: Commit**

```bash
git add scripts/analista/preparar.py tests/test_analista_preparar.py
git commit -m "feat(semanal): seguimiento de un activo contra la foto de la semana"
```

---

### Task 9: El bot con dos comandos, y lo retirado

**Files:**
- Modify: `scripts/analista/orden.py`, `scripts/analista/bot.py`, `scripts/analista/informe_html.py`, `scripts/bot_analistas.py`, `config/analistas_telegram.example.json`, `.claude/commands/analista.md`, `docs/bot-analistas.md`
- Delete: `scripts/analista/foco.py`, `scripts/analista/plan.py`, `scripts/analista/bitacora.py`, `scripts/analista/pdf.py`, `tests/test_analista_foco.py`, `tests/test_analista_plan.py`, `tests/test_analista_bitacora.py`, `tests/test_analista_pdf.py`, las funciones de `preparar.py` que solo usaban las piezas retiradas (`preparar_activo`, `preparar_calendario`, `preparar_dato`, `preparar_jornada`, `_pieza_de_activo`, `_plan`, `_foco`, `_terminal`, `_grafico_tv`, `_jornada`, `_movimiento`, `_activos_jornada`, `_cierres`, `_contexto`, `_filas_curva`, `_estado`, `_grupo_del_dato`, `_momento_por_hora`, `rendir_laminas`, `SinFocoError`, `MercadoIlegibleError`, `CLASES`, `MARCO_LEGIBLE`), y en `informe_html.py` todos los `cuerpo_*`, `CUERPOS`, `seccion_plan`, `_tabla_tasas`, `_estado`, `armar`, `guardar` y `templates/informes_analista/` si ya nada los lee.
- Test: `tests/test_analista_orden.py`, `tests/test_analista_bot.py`, `tests/test_analista_informe_html.py`, `tests/analista_fixtures.py`, `tests/test_guardian_estrategia.py`

**Interfaces:**
- Consumes: todo lo anterior.
- Produces: `orden.PIEZAS = ("oportunidad", "seguimiento")` y `orden.RETIRADOS = ("activo", "calendario", "dato", "jornada")`; `Atendedor.atender(pedido) -> Respuesta` con las dos piezas; `bot.AYUDA` nueva.

Antes de borrar, comprueba que nada fuera del bot importa cada símbolo: `grep -rn "<símbolo>" scripts src tests --include=*.py`. El repo no tiene consumidores externos de `scripts/analista/` aparte de `scripts/bot_analistas.py` (verificado al escribir este plan), pero repítelo al ejecutar.

- [ ] **Step 1: Escribir los tests que fallan (gramática)**

Reemplaza los tests de `tests/test_analista_orden.py` que piden `/activo`, `/calendario`, `/dato` o `/jornada` por:

```python
def test_oportunidad_no_lleva_argumentos():
    assert od.interpretar("/oportunidad") == od.Orden("oportunidad", {})


def test_seguimiento_resuelve_el_activo():
    universo = [{"ticker": "XAUUSD", "nombre": "Oro"}]
    assert od.interpretar("/seguimiento oro", universo) == od.Orden("seguimiento", {"ticker": "XAUUSD"})
    assert od.interpretar("/seguimiento xau", universo).args == {"ticker": "XAUUSD"}


def test_seguimiento_sin_activo_explica_como_pedirlo():
    with pytest.raises(od.PedidoInvalido, match="/seguimiento oro"):
        od.interpretar("/seguimiento", [])


@pytest.mark.parametrize("cmd", ["/activo oro", "/calendario hoy", "/dato ipc", "/jornada apertura"])
def test_los_comandos_retirados_responden_con_la_ayuda(cmd):
    assert od.interpretar(cmd, []).pieza == "ayuda"
```

Verifica también que `resolver_activo("xau", universo)` dé XAUUSD: `_formas` quita sufijos pero «xau» no es ni el ticker ni el nombre. Si no resuelve, agrega `"xau": "XAUUSD"` a `ALIAS` (el test de alias ya verifica que el destino exista en el catálogo). Así queda cubierta la línea 4 de Review Focus.

- [ ] **Step 2: Correrlos y ver que fallan**

Run: `uv run pytest tests/test_analista_orden.py -q`
Expected: FAIL

- [ ] **Step 3: Implementar la gramática**

En `orden.py`:

```python
PIEZAS = ("oportunidad", "seguimiento")
# Retirados el 2026-10-12 (spec oportunidad-semanal §2): responden con la ayuda.
RETIRADOS = ("activo", "calendario", "dato", "jornada")
```

En `interpretar`: `if comando in SERVICIO or comando in RETIRADOS: return Orden(pieza="ayuda" if comando in RETIRADOS else comando)`. La rama de `oportunidad` queda en `args = {}`. La de `seguimiento` es la vieja rama de `activo` con el mensaje «Falta el activo. Ejemplo: /seguimiento oro». En `resolver_activo`, el ejemplo del error pasa a `/seguimiento usdclp`. Borra `_BUSQUEDA_DATO` y las ramas de calendario, dato y jornada.

Run: `uv run pytest tests/test_analista_orden.py -q` → PASS

- [ ] **Step 4: Escribir los tests del bot**

Reescribe `preparar_falso` y `redactor` de `tests/test_analista_bot.py` para las dos piezas, y reemplaza los tests de piezas retiradas por:

```python
def test_oportunidad_arma_la_foto_una_sola_vez_por_semana(armado):
    bot, llamadas = armado.bot, armado.llamadas
    r1 = bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad")))
    r2 = bot.procesar_uno(b.Pedido(OTRO, 2, od.Orden("oportunidad")))
    assert len(llamadas) == 1                     # AGY una sola vez
    assert r1.archivos[0].name.startswith("analisis-semanal_")
    assert r2.archivos[0].name.endswith("_pedro-soto.html")  # el HTML lleva al ejecutivo que lo pidió
    assert "Ya está" in r2.texto


def test_oportunidad_sin_semana_responde_claro_y_no_gasta_cupo(armado):
    armado.atendedor.preparar = lambda o, d, a: (_ for _ in ()).throw(pr.SinSemanaError("La semana 2026-W42 todavía no tiene análisis semanal"))
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad")))
    assert r.texto.startswith("❌ La semana") and armado.estado.usados(CAMILA, AHORA) == 0


def test_oportunidad_en_espera_da_la_hora_del_cierre(armado):
    armado.atendedor.preparar = lambda o, d, a: (_ for _ in ()).throw(pr.EsperaVelaError("se publica al cierre de la vela de las 13:00"))
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad")))
    assert "13:00" in r.texto


def test_agy_sin_responder_no_gasta_cupo(armado):
    armado.atendedor.redactar = redactor([], codigo="timeout")
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad")))
    assert "No gasté tu cupo" in r.texto


def test_seguimiento_entrega_lamina_y_texto_sin_agy(armado):
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    assert armado.llamadas == [] and "Te envío una actualización" in r.texto
    assert r.archivos[0].suffix == ".png"


def test_seguimiento_se_reusa_30_minutos(armado):
    o = od.Orden("seguimiento", {"ticker": "XAUUSD"})
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, o))
    armado.reloj.ahora += timedelta(minutes=20)
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, o))
    assert armado.preparaciones == 1
    armado.reloj.ahora += timedelta(minutes=15)
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, o))
    assert armado.preparaciones == 2


def test_mt5_caido_en_seguimiento_lo_dice(armado):
    armado.atendedor.preparar = lambda o, d, a: (_ for _ in ()).throw(pr.PreparacionFallida("no uso el terminal: MT5 no conectó"))
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    assert "MT5" in r.texto


def test_la_ayuda_nombra_solo_los_dos_comandos():
    assert "/oportunidad" in b.AYUDA and "/seguimiento" in b.AYUDA
    for retirado in ("/activo", "/calendario", "/dato", "/jornada"):
        assert retirado not in b.AYUDA
```

La fixture `armado` gana: un segundo analista `OTRO = "222"` con nombre «Pedro Soto»; un contador `preparaciones`; `registro=tmp_path / "registro.json"` inyectado en el `Atendedor`; un `preparar_falso` que para `oportunidad` escriba una pieza como la de `test_analista_oportunidad_html._pieza` (muévela a `analista_fixtures.pieza_oportunidad(dir_pedido)`) y la anote con `rg.anotar_foto`, y que para `seguimiento` escriba una pieza `seguimiento` con `datos.whatsapp`; un `rendir_lamina` falso que escriba `fx.PNG`. Los tests de cupo, autorización, `/id`, `/estado`, cola y candado de instancia se conservan sin cambios.

- [ ] **Step 5: Implementar el `Atendedor`**

En `bot.py`:

```python
AYUDA = """Bot de análisis · Grupo Inteligencia

/oportunidad          el análisis técnico de la semana, con los 6 activos y tu panel de simulación
/seguimiento oro      cómo va un activo de la semana: la simulación y la lectura de hoy

/estado muestra tu cupo del día. /id muestra tu número de usuario."""

REUSO_MINUTOS = {"seguimiento": 30}
```

`Atendedor` pierde `vigencia`, `a_pdf` y `bitacora`, y gana `registro: Path = rg.RUTA` y `rendir_lamina: Callable[..., Path] = cm.rendir`. `atender` decide por pieza:

```python
    def atender(self, pedido: Pedido) -> Respuesta:
        ahora = self.reloj()
        if pedido.orden.pieza == "oportunidad":
            return self._oportunidad(pedido, ahora)
        return self._seguimiento(pedido, ahora)

    def _oportunidad(self, pedido: Pedido, ahora: datetime) -> Respuesta:
        import referencia_semanal as rs

        semana = rs.semana_de(ahora)
        previa = rg.foto(semana, self.registro)
        reusada = previa is not None
        if reusada:
            dir_pedido, avisos = Path(previa["dir"]), []
            pieza = pr.cargar_pieza(dir_pedido)
        else:
            self._exigir_cupo(pedido.usuario, ahora)
            dir_pedido = self.dir_pedidos / ahora.strftime("%Y-%m-%d") / f"{ahora:%H%M%S}_semanal_{semana}"
            hecha = self._preparar(pedido.orden, dir_pedido, ahora)
            pieza = self._redactar_y_validar(dir_pedido)
            for a in pieza["datos"]["activos"]:
                t = a["ticker"]
                self.rendir_lamina(cm.payload_semanal(a, pieza["editorial"]["titulares"][t], pieza["datos"]["edicion"],
                                                      self.autor, dir_pedido / a["grafico"]),
                                   "semanal", dir_pedido / f"lamina_{t.lower().replace('.', '_')}.png")
            rg.anotar_foto(semana, dir_pedido, ahora, [a["ticker"] for a in pieza["datos"]["activos"]], self.registro)
            self.estado.consumir(pedido.usuario, ahora)
            self.estado.guardar()
            avisos = hecha.avisos
        try:
            ruta = oh.guardar(pieza, dir_pedido, self.analista(pedido.usuario), self.autor, ahora.date())
        except oh.InformeInvalido as exc:
            raise FalloPedido(f"No pude armar la pieza: {exc}") from exc
        lineas = [f"✅ {pieza['editorial']['titular']}", f"Semana {pieza['datos']['semana']} · foto del {pieza['datos']['edicion']}"]
        if reusada:
            lineas.append("Ya está: es la foto de esta semana. Para ver cómo va un activo, usa /seguimiento <activo>.")
        lineas.append("Ábrelo en el navegador: marca los activos, escribe la pérdida aceptable y copia el correo.")
        lineas += [f"⚠️ {a}" for a in [*avisos, *au.avisos(self.autor, ahora.date())]]
        lineas.append(self._a_drive([ruta], ahora))
        return Respuesta(pedido.chat, "\n".join(lineas), [ruta])

    def _seguimiento(self, pedido: Pedido, ahora: datetime) -> Respuesta:
        o = pedido.orden
        minutos = int(self.config["reuso_minutos"].get("seguimiento", 30))
        dir_pedido = self.estado.vigente(o.clave_base(), ahora, minutos)
        if dir_pedido is None:
            self._exigir_cupo(pedido.usuario, ahora)
            dir_pedido = self.dir_pedidos / ahora.strftime("%Y-%m-%d") / f"{ahora:%H%M%S}_seguimiento_{ih.slug(o.args['ticker'])}"
            self._preparar(o, dir_pedido, ahora)
            pieza = pr.cargar_pieza(dir_pedido)
            d = pieza["datos"]
            self.rendir_lamina(cm.payload_seguimiento(d["activo"], d["evaluacion"], d["precio_vivo"], d["lectura_hoy"],
                                                      d["edicion"], self.autor, dir_pedido / "grafico.png"),
                               "seguimiento", dir_pedido / "lamina.png")
            import referencia_semanal as rs
            rg.anotar_seguimiento(rs.semana_de(ahora), o.args["ticker"],
                                  {"estado": d["evaluacion"]["estado"], "ejecutivo": pedido.usuario,
                                   "cuando": ahora.isoformat()}, self.registro)
            self.estado.registrar_pieza(o.clave_base(), dir_pedido, ahora, fija=False)
            self.estado.consumir(pedido.usuario, ahora)
            self.estado.guardar()
        pieza = pr.cargar_pieza(dir_pedido)
        return Respuesta(pedido.chat, pieza["datos"]["whatsapp"], [dir_pedido / "lamina.png"])
```

Con los ayudantes:

```python
    def _exigir_cupo(self, usuario: str, ahora: datetime) -> None:
        cupo = int(self.analista(usuario).get("cupo_diario", 10))
        if self.estado.usados(usuario, ahora) >= cupo:
            raise FalloPedido(f"Completaste tu cupo de {cupo} piezas nuevas por hoy. "
                              "Las que ya existen siguen disponibles.")

    def _preparar(self, orden, dir_pedido: Path, ahora: datetime) -> pr.Preparada:
        try:
            return self.preparar(orden, dir_pedido, ahora)
        except (pr.SinSemanaError, pr.EsperaVelaError, pr.SinFotoError, pr.FueraDeLaFotoError) as exc:
            raise FalloPedido(str(exc)) from exc  # es la respuesta, no una falla
        except pr.PreparacionFallida as exc:
            raise FalloPedido(f"No pude leer los datos: {exc}") from exc

    def _redactar_y_validar(self, dir_pedido: Path) -> dict[str, Any]:
        res = self.redactar(dir_pedido / "pieza.json", self.config["tier"])
        if getattr(res, "codigo", "ok") != "ok":
            raise FalloPedido(f"La redacción no terminó ({res.codigo}: {res.detalle}). No gasté tu cupo.")
        pieza = pr.cargar_pieza(dir_pedido)
        errores = es.errores(pieza)
        if errores:
            raise FalloPedido("El texto no pasó los controles y no lo entrego así:\n• " + "\n• ".join(errores[:6]))
        return pieza
```

`Telegram.documento` toma el MIME por sufijo: `{".pdf": "application/pdf", ".png": "image/png"}.get(ruta.suffix, "text/html")`. Imports nuevos de `bot.py`: `from analista import comercial as cm`, `from analista import oportunidad_html as oh`, `from analista import registro_semanal as rg`. Se van `bitacora`, `pdf`, `COMPARTIR_FOCO`, `_vigencia_real` y `_pieza_base`.

En `scripts/bot_analistas.py`, quita lo que construya el `Atendedor` con `vigencia`, `a_pdf` o `bitacora`. En `config/analistas_telegram.example.json`, `reuso_minutos` queda en `{"seguimiento": 30}`.

- [ ] **Step 6: Borrar lo retirado y su fixture**

```bash
git rm scripts/analista/foco.py scripts/analista/plan.py scripts/analista/bitacora.py scripts/analista/pdf.py tests/test_analista_foco.py tests/test_analista_plan.py tests/test_analista_bitacora.py tests/test_analista_pdf.py
```

Borra de `preparar.py` y de `informe_html.py` las funciones de la lista de **Files**. `informe_html.py` queda con `e`, `slug`, `_data_uri`, `pildora`, `bloque_firma`, `FRASE_GENERAL`, `LOGO` y `MARCA_CSS`. Si `templates/informes_analista/` ya no lo lee nadie (`grep -rn informes_analista scripts`), bórralo con `git rm -r`. En `tests/test_analista_informe_html.py` quedan solo los tests de `bloque_firma` y `slug`. En `tests/analista_fixtures.py` se borran `PLAN`, `activo`, `oportunidad`, `calendario`, `dato` y `jornada`. `data/bitacora_planes_analistas.json` **no se borra**: es historia versionada.

- [ ] **Step 7: El guardián cubre lo que el método viejo dejó**

Agrega a `tests/test_guardian_estrategia.py`:

```python
def test_el_bot_de_analistas_no_trae_el_metodo_viejo():
    """La pieza semanal del #254 decidía con la EMA 50 D1 y salía con el Chandelier (spec
    oportunidad-semanal §3). Ninguna de las dos puede volver al bot."""
    hallazgos = []
    for ruta in sorted((SCRIPTS / "analista").glob("*.py")):
        texto = ruta.read_text(encoding="utf-8").lower()
        for prohibido in ("chandelier", "ema_50", "ema50", "ema 50"):
            if prohibido in texto:
                hallazgos.append(f"{ruta.name}: {prohibido}")
    assert hallazgos == []
```

- [ ] **Step 8: Docs del comando y del bot**

- `.claude/commands/analista.md`: la sección «Qué va en cada campo» queda con una sola pieza, **Análisis técnico de la semana** (`datos.chip`):
  - `titular` (≤ 70) y `bajada` (≤ 160) sobre la semana de los seis activos.
  - `titulares.<ticker>` (≤ 70): la idea del activo con su dirección, sacada de `datos.activos[i].lectura`.
  - `contexto.<ticker>`: 2 o 3 frases con los drivers de la semana (`datos.drivers.<ticker>`, `datos.agenda_semana`), como mecanismo condicional si no hay un hecho medido. Sin `%`, sin la palabra «oportunidad», sin repetir los niveles (los pone la maqueta).
  - Los niveles, el escenario 1:3 y la simulación los escribió Python: no los repitas ni los comentes.
  - Borra las secciones de Activo, Foco técnico, Calendario, Dato y Jornada.
- Regenera los workflows de AGY: `uv run python scripts/agy_workflows.py` y luego `--check`.
- `docs/bot-analistas.md`: reemplaza la lista de comandos por los dos nuevos, y agrega «La pieza semanal sale en HTML (herramienta interna con panel); /seguimiento entrega lámina PNG y el texto de WhatsApp en el mensaje».

- [ ] **Step 9: Correr las pruebas del bot y la suite**

Run: `uv run pytest tests/test_analista_*.py tests/test_guardian_estrategia.py tests/test_story_render.py -q`
Expected: todos pasan

Run: `uv run pytest -q`
Expected: verde. Si algo de fuera del bot falla por un símbolo borrado, es un consumidor que se escapó: restaura ese símbolo y anótalo en el PR.

- [ ] **Step 10: Commit**

```bash
git add -u scripts/analista scripts/bot_analistas.py tests config/analistas_telegram.example.json .claude/commands/analista.md .agents/workflows docs/bot-analistas.md
git add tests/test_guardian_estrategia.py
git commit -m "feat(bot): solo /oportunidad y /seguimiento; se retiran foco, activo, calendario, dato y jornada"
```

---

### Task 10: Verificación real, PR y cierre del #254

**Files:** ninguno nuevo.

- [ ] **Step 1: Prueba real con MT5, sin tocar las referencias reales**

Con el terminal en la cuenta 51257, corre en un directorio de pedidos del scratchpad. El `Atendedor` usa `dir_pedidos=<scratchpad>` y `registro=<scratchpad>/registro.json`, con las referencias reales de la semana en curso (si la semana no tiene `_semana.json`, corre la prueba contra la W41 con `ahora` en esa semana). Pide `/oportunidad` con AGY real y luego `/seguimiento oro` y `/seguimiento cobre`.

Mira:
- el HTML en el navegador: los seis activos en orden de puntaje, el panel del rango del cobre y el correo pegado en Outlook o Word;
- las láminas PNG: que `¿`, `¡`, `·` y las tildes se vean;
- el texto de WhatsApp: sin guion largo y sin «oportunidad».

- [ ] **Step 2: Suite completa**

Run: `uv run pytest -q`
Expected: verde

- [ ] **Step 3: PR**

```bash
git push -u origin feat/oportunidad-semanal
gh pr create --title "Bot: /oportunidad semanal con simulación 1:3 y /seguimiento" --body "$(cat <<'EOF'
Implementa docs/superpowers/specs/2026-10-12-oportunidad-semanal-design.md.

- /oportunidad: HTML con los 6 activos del análisis semanal (Tori, firma de la Dirección de Análisis Técnico) y panel de simulación del ejecutivo con objetivo 1:3; una foto por semana reusada por todos.
- /seguimiento <activo>: simulación contra la foto y lectura de hoy, por separado; lámina + texto de WhatsApp, sin pesos.
- Se retiran /activo, /calendario, /dato, /jornada y el foco técnico.
- Reemplaza al #254 (decidía con EMA 50 D1 y Chandelier, borrados por el enchufe): se rescataron las láminas y el patrón del correo para Outlook.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 4: Cerrar el #254 sin mergear (pedir confirmación al director antes)**

```bash
gh pr close 254 --comment "Reemplazado por la oportunidad semanal sobre la lectura de Tori (spec 2026-10-12-oportunidad-semanal). Se rescataron las láminas y el correo para Outlook; el método EMA 50 D1 + Chandelier quedó fuera con el enchufe."
```

El merge del PR nuevo lo hace el director.
