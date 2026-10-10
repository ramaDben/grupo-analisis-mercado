# Enchufe de estrategia, fase 1: contrato y Tori sin consumidores

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que exista el paquete `scripts/estrategia/` con el contrato, el registro, la batería de
conformidad y la estrategia Tori completa, que lea los 5 activos base reales y entregue un PNG por
activo para el gate del director, sin que ningún pipeline la consuma todavía.

**Architecture:** `contrato.py` fija los tipos (dataclasses inmutables, sin MT5). `registro.py`
resuelve la estrategia activa desde `config/estrategia.json`. Tori vive en `scripts/estrategia/tori/`
y se arma en capas: pivotes → líneas → calidad → horizontales (S2), y lectura → textos → puntaje
(S3). La única infraestructura nueva es `fuente.py`, que trae velas cerradas y la vela en curso
desde MT5, y la usa solo el script de revisión.

**Tech Stack:** Python 3.12, pandas, pytest, `zoneinfo`, matplotlib (extra `informe`, solo para el
PNG de revisión), MetaTrader5 (solo en la máquina del director).

**Spec:** `docs/superpowers/specs/2026-10-09-enchufe-estrategia-design.md`. Doctrina:
`docs/metodologia-tendencias.md`. Mapa de sesiones: `docs/superpowers/plans/2026-10-09-enchufe-sesiones.md`.

## Global Constraints

- **Rama propia desde master por sesión:** `feat/enchufe-s1-contrato`, `feat/enchufe-s2-trazado`,
  `feat/enchufe-s3-lectura`. Nunca se trabaja en master.
- **`git add` explícito, nunca `-a`.** El árbol trae cambios ajenos (`data central/`, bitácoras).
- **TDD:** el test va primero. La suite completa (`uv run pytest`) queda verde antes de cada PR.
- **Ningún pipeline existente cambia en esta fase.** La única excepción es la mudanza del zigzag
  (S2), que deja a `tradingview_grafico` importándolo desde su nuevo lugar, con el mismo
  comportamiento.
- **La estrategia no consume nada macro** (spec §8.2) ni importa `analisis`, `screener_gi` ni
  `get_asset_levels`.
- **Sin mirar el futuro:** `leer()` trabaja solo con las velas cerradas que recibe. La vela en
  curso llega aparte (`VelaEnCurso`) y nunca mueve una línea ni un ancla (V15).
- **Texto de cliente** (escenarios, `salida`): sin guion largo `—` ni medio `–`, tuteo chileno
  sin voseo, flechas ⬆️ ↔️ ⬇️, precios con los `digits` del activo en notación chilena.
- **Las cifras del script de revisión salen de MT5 en el momento** (Regla 1). No se escribe un
  precio a mano en ningún test que hable del mercado real; los tests usan velas sintéticas.
- **Todo umbral numérico que Tori no da es parámetro nuestro** y vive en
  `scripts/estrategia/tori/parametros.py`, declarado en la procedencia como `no_probado`.
- **Si aparece algo que el spec no cubre, se para y se pregunta.** No se decide en la sesión.
- Los tests importan con `sys.path` apuntando a `scripts/` y `src/`, igual que
  `tests/test_analista_plan.py`: `from estrategia.contrato import ...`.

## Huecos del spec que este plan cierra (requieren el visto bueno del director en S0)

El spec nombra tipos y umbrales que no define. El plan los fija así; si el director corrige alguno,
se corrige acá antes de S1.

**Revisados contra la evidencia el 2026-10-10.** AGY contrastó cada hueco con las fichas y la
verificación V1-V20, y Claude verificó las citas que sostienen los cambios (V7 gokPl [13:06], V18
qLtq7 [11:35]/[12:30], ipUbs [00:36]/[01:11], OjZ8d [01:07]). Lo que se acercó a la operativa de
Tori: la ruptura exige un cierre claro (6), la semana de datos se cuenta en velas (7), la ruptura
dura por estructura y no por un número de velas (5), sin línea de seguridad no hay setup (12), el
rebote es un estado propio (13), operar contra los marcos mayores excluye (14), el objetivo es el
horizontal de marco mayor (15) y la salida nombra la línea de seguimiento (16). Las decisiones que
Tori no resuelve están en "Decisiones del director" al final de esta sección.

1. **Tipos sin definir en el spec:** `Etiqueta`, `Marcos`, `Referencia`, `Escenario` y
   `VelaEnCurso` quedan como en la Task 1. `Marcos` lleva `contexto`, `operativo`, `velas` (cuántas
   velas cerradas pide por marco) y `etiquetas`.
2. **Dos campos nuevos en el contrato:**
   - `Linea.empinada: bool = False`. El spec dice que la calidad "marca la línea muy empinada" y
     que esa línea "no puntúa como principal", pero `Linea` no tenía dónde llevar la marca.
   - `Lectura.metricas: dict[str, float]`. `puntuar(lectura, horizonte)` necesita el ATR diario y
     las distancias a cada línea ("a menos de un ATR diario"), y la `Lectura` del spec no los trae.
     Los consumidores no lo leen: es de la estrategia para su propio puntaje.
3. **`Lectura.precio`:** el precio vivo si hay vela en curso; si no, el último cierre.
4. **Las líneas se calculan por índice de vela, no por tiempo de reloj.** Así las dibuja
   TradingView (los fines de semana no ocupan espacio). Los timestamps de `Linea.puntos` vienen en
   la misma época que las velas recibidas (la hora del servidor MT5 empaquetada como epoch). La
   conversión a hora de Chile la hace la infraestructura, solo para `VelaEnCurso.cierre`.
5. **Reglas de estado, versión 1 (se revisan en el gate):**
   - `RUPTURA`: una de las dos líneas cerró al otro lado y el último cierre sigue afuera. **No
     tiene límite de velas**: Tori no las cuenta, le importa que el precio siga cerca de la línea de
     seguridad (doctrina 2.5). La ruptura deja de serlo cuando el precio vuelve a cerrar adentro o
     cuando cambia el ancla (el precio supera el extremo desde el que se trazó la línea rota), y la
     frescura la mide el puntaje con la distancia a la línea de seguridad.
   - `TENDENCIA`: hay al menos una línea vigente y no son dos líneas B. La principal (A+ primero,
     después más toques, después más semanas) da la dirección y es la de seguridad; la contraria
     vigente, si existe, es la de acción.
   - `RANGO`: no hay línea vigente, o las dos vigentes son B. Sin diagonales, los bordes son el
     máximo y el mínimo de la última semana del marco operativo.
   - `PRUEBA`: la vela en curso está al otro lado de una línea vigente por más de la tolerancia de
     toque.
   - `REBOTE` (decisión del director, 2026-10-10): la estructura es la de `TENDENCIA` y la última
     vela cerrada tocó la línea de seguridad (dentro de la tolerancia) y cerró a favor. Dura una
     vela. `PRUEBA` le gana, porque la vela abierta manda sobre la que cerró.
6. **Ruptura por cierre y mecha:** la ruptura exige que el **cierre** quede al otro lado por más
   que la tolerancia de toque: "una mecha, un toque o un asomo leve no es ruptura" (doctrina 2.4).
   Una vela que cruza más allá de la tolerancia sin cerrar afuera por más que ella deja la línea
   sin trazar, y se busca otro Punto B (doctrina 2.3, V10). Un asomo dentro de la tolerancia es un
   toque.
7. **Umbrales provisionales** (`parametros.py`, Task S2-1). Tori no da números:
   - Pivote candidato: giro de 2 ATR del marco.
   - Tolerancia de toque: 0,25 ATR.
   - Separación entre toques: 1 ATR.
   - Pendiente mínima: 0,02 ATR por vela; bajo eso, la línea es horizontal.
   - "Muy empinada": más de 0,5 ATR por vela.
   - Punto B reciente (V16): en las últimas 6 velas.
   - Semana de datos: 5 días hábiles **contados en velas del marco** (en 4H, 30 velas; doctrina §4).
     Medirla en días de calendario dejaba que un fin de semana sumara dos días sin velas.
   - Horizontales: pivotes de 1,5 ATR, zona de 0,5 ATR, a no más de 8 ATR del precio.
   - Rango: bordes de las últimas 30 velas.
   - Velas pedidas: W1 156, D1 250, H4 180.
   - "Cerca": a 1 ATR diario o menos, que es el ejemplo del spec. "Lejos": más de 2 ATR diarios.

   El spec pide fijar los pesos "sobre una medición del universo real". Esa medición la hace el
   script de S3 (Task S3-7) antes del gate, y el director decide ahí si los umbrales se mueven.
8. **Puntaje por bandas:** cada situación tiene una banda de 25 puntos (75 / 50 / 25 / 0) y lo que
   suma dentro de ella tiene tope 24. Así el orden de situaciones del spec §5 nunca se invierte por
   los adicionales; solo una resta (precio lejos de la seguridad) puede bajar a un activo de banda.
9. **El formato de precio** se toma de `pipeline_carrusel.formatear_precio` con import perezoso,
   igual que `analista/plan.py`. Mudarlo a un módulo de infraestructura toca un pipeline y queda
   para S4.
10. **`conceptos`** usa claves nuevas (`linea-de-tendencia`, `linea-de-seguridad`,
    `ruptura-por-cierre`, `rebote`, `rango`). Su entrada en el glosario se escribe en la fase 2, con el primer
    consumidor que las publique.
11. **El reloj del servidor** se mide con la cotización de `BTCUSD`, que cotiza todos los días.
    Un activo cuya última cotización tiene más de 15 minutos no tiene vela abierta: el mercado
    está cerrado y todas sus velas cuentan como cerradas.
12. **Sin línea de seguridad no hay setup** (V18: "the safety line is the opposite line... this
    line tells us how long to stay in our trade"). La lectura sigue diciendo `RUPTURA`, porque es
    un hecho, pero el puntaje no la cuenta como situación de ruptura y la lectura lo avisa. Lo mismo
    vale para una `PRUEBA`: solo es setup si la otra línea existe.
13. **El rebote es un estado propio, `REBOTE`** (decisión del director, 2026-10-10; doctrina 2.5,
    setup secundario, V7; spec §4, "El rebote"). La última vela cerrada tocó la línea de seguridad
    y cerró a favor. La estructura es la de `TENDENCIA`, así que el estado no mueve líneas, y dura
    una vela. Los textos lo cuentan como hecho, `vigilar` es la línea de seguridad, y con una
    seguridad A+ el puntaje lo trata como "a punto". `divergencia` no separa `TENDENCIA` de
    `REBOTE`: la estructura es la misma.
14. **Contra la secuencia de los marcos mayores, el activo se excluye** (decisión del director,
    2026-10-10; ipUbs [00:36], [01:11]: las falsas rupturas vienen de operar contra la estructura
    mayor). Se activa cuando la línea principal de **todos** los marcos de contexto va contra la
    dirección, en los dos horizontes, y la lectura lo avisa. Puede dejar un canal sin activos: lo
    que se publique entonces se decide en la fase 2, junto con el lunes sin análisis.
15. **El objetivo es el horizontal de marco mayor**, confirmado por el director el 2026-10-10
    (doctrina 2.8: "soporte o resistencia
    horizontal mayor"). Se busca primero entre los horizontales de D1 y W1, y solo si no hay
    ninguno en la dirección se usa uno de 4H.
16. **La salida nombra la línea de seguimiento** cuando existe (doctrina 2.8: "o de la línea de
    seguimiento más empinada").
17. **La referencia semanal** (decisión del director, 2026-10-10; spec §4 y §8.9). El análisis
    del lunes fija todo y las diarias se miden contra eso. El contrato suma tres cosas:
    - `Lectura.vela`: el timestamp de la última vela cerrada del marco operativo. Es desde dónde
      `seguir()` busca rupturas.
    - `Estrategia.seguir(referencia, velas, digits, en_curso)`: no vuelve a trazar; evalúa las
      líneas de la referencia sobre las velas de hoy.
    - `lectura_a_dict` / `lectura_de_dict`: la referencia se guarda en JSON.

    `seguir()` usa **todas** las velas que recibe, no la ventana de `leer()`, porque las anclas
    del lunes tienen que seguir dentro aunque la ventana avance. La infraestructura pide velas de
    más (`velas_mt5(..., extra=60)`, dos semanas de 4H), y si un ancla igual queda fuera,
    `seguir()` falla con un mensaje que lo dice. Guardar y reemplazar la referencia es fase 2.

### Decisiones del director (Tori no las resuelve)

- ~~Líneas congeladas con la operación abierta~~ **Resuelto por el director (2026-10-10).** El
  sistema no opera, pero el análisis semanal fija niveles y tendencia y las diarias se comparan
  contra ese nivel. Es la regla de Tori de no mover las líneas mientras la tesis vive
  (OjZ8d [01:07]) y queda resuelta con `seguir()` (hueco 17). No habrá backtesting (director,
  2026-10-10): lo que la procedencia declara `no_probado` queda declarado.
- ~~Rebote como situación o como estado~~ **Resuelto (2026-10-10): estado `REBOTE` propio**,
  con su cambio de spec (13).
- ~~Contra la secuencia mayor: resta o exclusión~~ **Resuelto (2026-10-10): se excluye** (14).
- ~~Objetivo mayor lejano frente a uno de 4H cercano~~ **Resuelto (2026-10-10): siempre el
  horizontal de D1 o W1**; el de 4H se dibuja y solo es objetivo si no hay uno mayor (15).

## Review Focus

1. **Velas sin rango** (feriado, símbolo recién agregado, todas las velas iguales): `leer()` tiene
   que fallar con un `ValueError` que nombre el activo y el marco, nunca con `ZeroDivisionError`.
   Test en Task S3-1.
2. **Menos velas que las pedidas** (MT5 devuelve 20 donde se pidieron 180): Tori lee lo que hay y
   cae en `RANGO` si no hay estructura, sin romperse. Test en Task S3-1.
3. **El extremo es la última vela** (el mínimo de la ventana es la vela recién cerrada): no hay
   segundo punto posible y `trazar` devuelve `None`, no una línea de un punto. Test en Task S2-2.
4. **El cambio de horario de Chile** en la hora de cierre de la vela (primer sábado de septiembre,
   primer sábado de abril): `cierre_santiago` tiene que dar la hora de pared correcta a ambos
   lados del cambio. Test en Task S3-7.
5. **Precio vivo dentro de la tolerancia de la línea:** es un toque, no una `PRUEBA`. Test en Task
   S3-2.

---

# Sesión S1 · Contrato, registro y conformidad

Rama: `git checkout master && git pull && git checkout -b feat/enchufe-s1-contrato`.

### Task S1-1: El contrato

**Files:**
- Create: `scripts/estrategia/__init__.py`
- Create: `scripts/estrategia/contrato.py`
- Test: `tests/test_estrategia_contrato.py`

**Interfaces:**
- Produces: `Etiqueta`, `Marcos`, `Linea`, `Referencia`, `Escenario`, `VelaEnCurso`, `Prueba`,
  `Lectura` (con `vela: int = 0`), `Puntaje`, `Fundamento`, `Procedencia`, `Estrategia`
  (Protocol, con `seguir`), `exigir_velas(velas, marcos) -> None`, `lectura_a_dict(lectura) ->
  dict`, `lectura_de_dict(dict) -> Lectura`, constantes `FLECHAS`, `CALIDADES`, `COLUMNAS_VELAS`.

- [ ] **Step 1: Escribir el test que falla**

```python
"""Contrato del enchufe: los tipos rechazan una lectura mal formada al construirse."""
from __future__ import annotations

import json
import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from estrategia.contrato import (  # noqa: E402
    Escenario, Etiqueta, Lectura, Linea, Marcos, Prueba, Puntaje, Referencia, VelaEnCurso,
    exigir_velas, lectura_a_dict, lectura_de_dict,
)

SCL = ZoneInfo("America/Santiago")
LINEA = Linea("seguridad", "diagonal", ((1, 100.0), (2, 101.0)), "H4", 3, "A+", 105.0)
TRES = (Escenario("⬆️", "Sobre 105", "sube"), Escenario("↔️", "Entre", "espera"),
        Escenario("⬇️", "Bajo 105", "baja"))


def _lectura(**cambios) -> Lectura:
    base = Lectura(
        ticker="XAUUSD", marco="H4", precio=106.0, direccion="ALCISTA", estado="TENDENCIA",
        lineas=(LINEA,), en_prueba=None, vigilar=Referencia(105.0, "línea alcista", LINEA),
        invalidacion=Referencia(105.0, "línea alcista de seguridad", LINEA), objetivo=None,
        escenarios=TRES, salida="sale", conceptos=(), avisos=(),
    )
    return replace(base, **cambios)


def test_una_lectura_bien_formada_se_construye():
    assert _lectura().estado == "TENDENCIA"


def test_exige_exactamente_un_escenario_por_flecha():
    with pytest.raises(ValueError, match="escenario"):
        _lectura(escenarios=TRES[:2])
    with pytest.raises(ValueError, match="escenario"):
        _lectura(escenarios=(TRES[0], TRES[0], TRES[2]))


def test_prueba_va_solo_y_siempre_con_el_estado_prueba():
    prueba = Prueba(LINEA, 105.2, datetime(2026, 10, 9, 13, 0, tzinfo=SCL))
    with pytest.raises(ValueError, match="en_prueba"):
        _lectura(estado="PRUEBA")
    with pytest.raises(ValueError, match="en_prueba"):
        _lectura(en_prueba=prueba)
    assert _lectura(estado="PRUEBA", en_prueba=prueba).en_prueba is prueba


def test_la_hora_de_cierre_exige_zona_horaria():
    with pytest.raises(ValueError, match="zona"):
        Prueba(LINEA, 105.2, datetime(2026, 10, 9, 13, 0))
    with pytest.raises(ValueError, match="zona"):
        VelaEnCurso(10, 100.0, datetime(2026, 10, 9, 13, 0))


def test_una_diagonal_lleva_dos_anclas_y_una_horizontal_una():
    with pytest.raises(ValueError, match="anclas"):
        Linea("accion", "diagonal", ((1, 100.0),), "H4", 2, "B", 100.0)
    with pytest.raises(ValueError, match="anclas"):
        Linea("objetivo", "horizontal", ((1, 100.0), (2, 100.0)), "H4", 2, "", 100.0)


def test_la_calidad_es_a_mas_b_o_vacia():
    with pytest.raises(ValueError, match="calidad"):
        Linea("accion", "diagonal", ((1, 100.0), (2, 101.0)), "H4", 2, "C", 100.0)


def test_el_puntaje_va_de_0_a_100():
    with pytest.raises(ValueError, match="0 y 100"):
        Puntaje(101.0, {}, None)
    assert Puntaje(0.0, {}, "sin líneas").excluido == "sin líneas"


def test_marcos_exige_velas_y_etiqueta_por_marco():
    with pytest.raises(ValueError, match="D1"):
        Marcos(("D1",), "H4", {"H4": 10}, {"H4": Etiqueta("swing", "de una a dos semanas")})


def test_exigir_velas_nombra_lo_que_falta():
    marcos = Marcos((), "H4", {"H4": 10}, {"H4": Etiqueta("swing", "de una a dos semanas")})
    with pytest.raises(ValueError, match="H4"):
        exigir_velas({}, marcos)
    sin_close = pd.DataFrame({"time": [1, 2], "open": [1, 1], "high": [1, 1], "low": [1, 1]})
    with pytest.raises(ValueError, match="close"):
        exigir_velas({"H4": sin_close}, marcos)
    desordenadas = pd.DataFrame({"time": [2, 1], "open": [1, 1], "high": [1, 1], "low": [1, 1],
                                 "close": [1, 1]})
    with pytest.raises(ValueError, match="orden"):
        exigir_velas({"H4": desordenadas}, marcos)


def test_la_lectura_sobrevive_ida_y_vuelta_por_json():
    """Así se guarda la referencia semanal (spec §4)."""
    prueba = Prueba(LINEA, 105.2, datetime(2026, 10, 9, 13, 0, tzinfo=SCL))
    lectura = _lectura(estado="PRUEBA", en_prueba=prueba, vela=1_760_000_000, metricas={"atr": 1.5})
    texto = json.dumps(lectura_a_dict(lectura), ensure_ascii=False)
    assert lectura_de_dict(json.loads(texto)) == lectura
```

- [ ] **Step 2: Correrlo y verificar que falla**

Run: `uv run pytest tests/test_estrategia_contrato.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'estrategia'`.

- [ ] **Step 3: Implementar el contrato**

`scripts/estrategia/__init__.py`:

```python
"""Enchufe de estrategia: toda la lectura técnica sale de UNA estrategia activa.

Spec: docs/superpowers/specs/2026-10-09-enchufe-estrategia-design.md.
"""
```

`scripts/estrategia/contrato.py`:

```python
"""Contrato del enchufe de estrategia: lo que toda estrategia recibe y devuelve.

Spec §4. No importa MT5 ni ningún pipeline: los tipos se construyen igual en un
test y en producción. Las validaciones de `__post_init__`
hacen imposible construir una lectura mal formada, y la batería de conformidad
(`tests/estrategia_conformidad.py`) verifica lo que no se puede ver al
construir, como no mirar el futuro.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Literal, Protocol

import pandas as pd

Direccion = Literal["ALCISTA", "BAJISTA", "LATERAL"]
Estado = Literal["TENDENCIA", "REBOTE", "PRUEBA", "RUPTURA", "RANGO"]
Rol = Literal["accion", "seguridad", "seguimiento", "contexto", "objetivo", "rango"]
Horizonte = Literal["sesion", "semana"]

FLECHAS = ("⬆️", "↔️", "⬇️")
CALIDADES = ("A+", "B", "")
COLUMNAS_VELAS = ("time", "open", "high", "low", "close")


def _exigir_zona(momento: datetime, campo: str) -> None:
    if momento.tzinfo is None:
        raise ValueError(f"`{campo}` tiene que venir con zona horaria (America/Santiago)")


@dataclass(frozen=True)
class Etiqueta:
    """Cómo se le nombra un marco al cliente: "swing", "de una a dos semanas" (spec §8.1)."""

    nombre: str
    duracion: str


@dataclass(frozen=True)
class Marcos:
    """Los marcos que la estrategia pide: los de contexto y el operativo."""

    contexto: tuple[str, ...]
    operativo: str
    velas: dict[str, int]  # cuántas velas cerradas pide por marco
    etiquetas: dict[str, Etiqueta]

    def __post_init__(self) -> None:
        faltan = [m for m in self.todos if m not in self.velas or m not in self.etiquetas]
        if faltan:
            raise ValueError(f"Marcos sin velas o sin etiqueta: {faltan}")

    @property
    def todos(self) -> tuple[str, ...]:
        return (*self.contexto, self.operativo)


@dataclass(frozen=True)
class Linea:
    rol: Rol
    tipo: Literal["diagonal", "horizontal"]
    puntos: tuple[tuple[int, float], ...]  # (timestamp de la vela, precio)
    marco: str
    toques: int
    calidad: str  # "A+", "B" o ""
    valor_actual: float  # el precio de la línea en la última vela cerrada
    empinada: bool = False

    def __post_init__(self) -> None:
        esperadas = 2 if self.tipo == "diagonal" else 1
        if len(self.puntos) != esperadas:
            raise ValueError(
                f"Una línea {self.tipo} lleva {esperadas} anclas; trae {len(self.puntos)}"
            )
        if self.calidad not in CALIDADES:
            raise ValueError(f"La calidad tiene que ser una de {CALIDADES}; trae {self.calidad!r}")


@dataclass(frozen=True)
class Referencia:
    """Un nivel que la pieza nombra: el que se vigila, el que invalida o el objetivo."""

    precio: float
    etiqueta: str
    linea: Linea | None = None


@dataclass(frozen=True)
class Escenario:
    flecha: str  # "⬆️", "↔️" o "⬇️"
    condicion: str  # la condición corta: "Cierre de 4 horas sobre 4.020,00"
    texto: str  # la frase de cliente

    def __post_init__(self) -> None:
        if self.flecha not in FLECHAS:
            raise ValueError(f"La flecha tiene que ser una de {FLECHAS}; trae {self.flecha!r}")


@dataclass(frozen=True)
class VelaEnCurso:
    """La vela del marco operativo que todavía no cerró. Llega aparte de las cerradas."""

    apertura: int  # timestamp de apertura, en la misma época que las velas cerradas
    precio: float  # el último precio de esa vela
    cierre: datetime  # cuándo cierra, en America/Santiago

    def __post_init__(self) -> None:
        _exigir_zona(self.cierre, "cierre")


@dataclass(frozen=True)
class Prueba:
    linea: Linea  # la línea que el precio vivo está perforando
    valor_ahora: float  # el valor de la línea en la vela abierta
    cierre_vela: datetime  # cuándo cierra la vela del marco operativo (America/Santiago)

    def __post_init__(self) -> None:
        _exigir_zona(self.cierre_vela, "cierre_vela")


@dataclass(frozen=True)
class Lectura:
    ticker: str
    marco: str
    precio: float  # el precio vivo si hay vela en curso; si no, el último cierre
    direccion: Direccion
    estado: Estado
    lineas: tuple[Linea, ...]
    en_prueba: Prueba | None
    vigilar: Referencia
    invalidacion: Referencia | None
    objetivo: Referencia | None
    escenarios: tuple[Escenario, ...]
    salida: str
    conceptos: tuple[str, ...]
    avisos: tuple[str, ...]
    metricas: dict[str, float] = field(default_factory=dict)  # de la estrategia, para puntuar
    vela: int = 0  # timestamp de la última vela cerrada del marco operativo

    def __post_init__(self) -> None:
        flechas = [e.flecha for e in self.escenarios]
        if len(flechas) != 3 or sorted(flechas) != sorted(FLECHAS):
            raise ValueError(
                f"La lectura necesita exactamente un escenario por flecha {FLECHAS}; trae {flechas}"
            )
        if (self.estado == "PRUEBA") != (self.en_prueba is not None):
            raise ValueError("`en_prueba` va solo, y siempre, con el estado PRUEBA")


@dataclass(frozen=True)
class Puntaje:
    puntos: float
    desglose: dict[str, float]
    excluido: str | None  # motivo técnico de exclusión, en texto de motivo

    def __post_init__(self) -> None:
        if not 0.0 <= self.puntos <= 100.0:
            raise ValueError(f"El puntaje va entre 0 y 100; trae {self.puntos}")


@dataclass(frozen=True)
class Fundamento:
    regla: str
    origen: tuple[str, ...]  # quién la usa: "Tori Trades, qLtq7 [51:00]"
    canonico: tuple[str, ...]  # teoría clásica: "F3 p. 56"
    empirico: tuple[str, ...]  # evidencia medida: "F4", "F6"
    no_probado: str  # lo que la evidencia no cubre; "" solo si empirico la cubre


@dataclass(frozen=True)
class Procedencia:
    fuente_doctrina: str  # ruta relativa a la raíz del repo
    fuente_citas: str  # ruta relativa a la raíz del repo
    fundamentos: tuple[Fundamento, ...]
    modos_de_falla: tuple[str, ...]


class Estrategia(Protocol):
    nombre: str
    marcos: Marcos
    procedencia: Procedencia

    def leer(self, ticker: str, velas: dict[str, pd.DataFrame], digits: int,
             en_curso: VelaEnCurso | None = None) -> Lectura: ...

    def puntuar(self, lectura: Lectura, horizonte: Horizonte) -> Puntaje: ...

    def seguir(self, referencia: Lectura, velas: dict[str, pd.DataFrame], digits: int,
               en_curso: VelaEnCurso | None = None) -> Lectura: ...

    def divergencia(self, preparada: Lectura, actual: Lectura) -> str | None: ...


def lectura_a_dict(lectura: Lectura) -> dict[str, Any]:
    """La lectura en JSON plano: así se guarda la referencia semanal (spec §4)."""
    datos = asdict(lectura)
    if lectura.en_prueba is not None:
        datos["en_prueba"]["cierre_vela"] = lectura.en_prueba.cierre_vela.isoformat()
    return datos


def _linea_de(d: dict[str, Any]) -> Linea:
    return Linea(**{**d, "puntos": tuple((int(ts), float(pr)) for ts, pr in d["puntos"])})


def _referencia_de(d: dict[str, Any] | None) -> Referencia | None:
    if d is None:
        return None
    return Referencia(d["precio"], d["etiqueta"], _linea_de(d["linea"]) if d["linea"] else None)


def lectura_de_dict(d: dict[str, Any]) -> Lectura:
    prueba = d["en_prueba"]
    return Lectura(
        ticker=d["ticker"], marco=d["marco"], precio=d["precio"], direccion=d["direccion"],
        estado=d["estado"], lineas=tuple(_linea_de(x) for x in d["lineas"]),
        en_prueba=None if prueba is None else Prueba(
            _linea_de(prueba["linea"]), prueba["valor_ahora"],
            datetime.fromisoformat(prueba["cierre_vela"])),
        vigilar=_referencia_de(d["vigilar"]), invalidacion=_referencia_de(d["invalidacion"]),
        objetivo=_referencia_de(d["objetivo"]),
        escenarios=tuple(Escenario(**e) for e in d["escenarios"]), salida=d["salida"],
        conceptos=tuple(d["conceptos"]), avisos=tuple(d["avisos"]),
        metricas=dict(d["metricas"]), vela=int(d["vela"]),
    )


def exigir_velas(velas: dict[str, pd.DataFrame], marcos: Marcos) -> None:
    """Falla con un mensaje accionable si falta un marco, una columna o el orden."""
    for marco in marcos.todos:
        df = velas.get(marco)
        if df is None or df.empty:
            raise ValueError(f"Faltan las velas de {marco}")
        faltan = [c for c in COLUMNAS_VELAS if c not in df.columns]
        if faltan:
            raise ValueError(f"Las velas de {marco} no traen las columnas {faltan}")
        if not df["time"].is_monotonic_increasing:
            raise ValueError(f"Las velas de {marco} no vienen en orden cronológico")
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `uv run pytest tests/test_estrategia_contrato.py -v`
Expected: PASS (11 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/estrategia/__init__.py scripts/estrategia/contrato.py tests/test_estrategia_contrato.py
git commit -m "feat(estrategia): contrato del enchufe con validación al construir"
```

### Task S1-2: La procedencia, validada contra `fuentes.md`

**Files:**
- Create: `scripts/estrategia/procedencia.py`
- Test: `tests/test_estrategia_procedencia.py`

**Interfaces:**
- Consumes: `Fundamento`, `Procedencia` (Task S1-1).
- Produces: `leer_estados(ruta: Path) -> dict[str, str]`, `validar(proc: Procedencia, raiz: Path =
  RAIZ) -> list[str]` (lista vacía = válida), `RAIZ: Path`.

- [ ] **Step 1: Escribir el test que falla**

```python
"""La procedencia solo se apoya en filas verificadas de fuentes.md (spec §4)."""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from estrategia.contrato import Fundamento, Procedencia  # noqa: E402
from estrategia.procedencia import leer_estados, validar  # noqa: E402

FUENTES = "docs/investigacion/fundamentos/fuentes.md"
BUENO = Fundamento("en lateral no se opera", ("Tori Trades, E6dUU [02:52]",), ("F3 p. 78",),
                   ("F6",), "")
PROC = Procedencia("docs/metodologia-tendencias.md", FUENTES, (BUENO,), ("reversiones bruscas",))


def test_lee_el_estado_de_cada_fila_del_resumen():
    estados = leer_estados(RAIZ / FUENTES)
    assert estados["F3"] == "verificada"
    assert estados["F1"].startswith("verificada vía")
    assert estados["F5"] == "verificada parcial"
    assert estados["F11"] == "no encontrada"


def test_una_procedencia_completa_es_valida():
    assert validar(PROC) == []


def test_una_regla_sin_origen_no_pasa():
    errores = validar(replace(PROC, fundamentos=(replace(BUENO, origen=()),)))
    assert any("sin origen" in e for e in errores)


def test_una_regla_sin_respaldo_no_pasa():
    errores = validar(replace(PROC, fundamentos=(replace(BUENO, canonico=(), empirico=()),)))
    assert any("sin respaldo" in e for e in errores)


def test_sin_evidencia_empirica_tiene_que_confesar_lo_no_probado():
    sin_emp = replace(BUENO, empirico=(), no_probado="")
    errores = validar(replace(PROC, fundamentos=(sin_emp,)))
    assert any("no_probado" in e for e in errores)


def test_una_cita_a_fila_parcial_o_inexistente_no_sirve_de_respaldo():
    parcial = replace(BUENO, empirico=("F5",))
    inexistente = replace(BUENO, canonico=("F99 p. 1",))
    errores = validar(replace(PROC, fundamentos=(parcial, inexistente)))
    assert any("F5" in e and "verificada parcial" in e for e in errores)
    assert any("F99" in e for e in errores)


def test_el_metodo_declara_como_falla():
    assert any("modos_de_falla" in e for e in validar(replace(PROC, modos_de_falla=())))
```

- [ ] **Step 2: Correrlo y verificar que falla**

Run: `uv run pytest tests/test_estrategia_procedencia.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'estrategia.procedencia'`.

- [ ] **Step 3: Implementar**

```python
"""Valida el bloque de procedencia de una estrategia contra `fuentes.md` (spec §4).

Cada cita de `canonico` y `empirico` empieza con el id de una fila del resumen de
`fuentes.md` (`F1`, `F3`...). Solo sirven de respaldo las filas "verificada" o
"verificada vía": una "verificada parcial", "corregida" o "no encontrada" no
alcanza. Así nadie puede agregar una referencia de memoria.
"""
from __future__ import annotations

import re
from pathlib import Path

from estrategia.contrato import Procedencia

RAIZ = Path(__file__).resolve().parents[2]
_FILA = re.compile(r"^\|\s*(F\d+)\b[^|]*\|\s*([^|]+?)\s*\|")


def leer_estados(ruta: Path) -> dict[str, str]:
    """`{"F1": "verificada vía murphy", "F3": "verificada", ...}` desde la tabla de resumen."""
    estados: dict[str, str] = {}
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        m = _FILA.match(linea)
        if m:
            estados[m.group(1)] = m.group(2).replace("*", "").strip().lower()
    return estados


def _verificada(estado: str) -> bool:
    return estado == "verificada" or estado.startswith("verificada vía")


def validar(proc: Procedencia, raiz: Path = RAIZ) -> list[str]:
    """Errores de la procedencia, en texto. Lista vacía si está completa."""
    errores: list[str] = []
    if not (raiz / proc.fuente_doctrina).exists():
        errores.append(f"la doctrina {proc.fuente_doctrina} no existe")
    ruta_citas = raiz / proc.fuente_citas
    if not ruta_citas.exists():
        return [*errores, f"el archivo de citas {proc.fuente_citas} no existe"]
    estados = leer_estados(ruta_citas)
    if not proc.fundamentos:
        errores.append("la procedencia no trae fundamentos")
    if not proc.modos_de_falla:
        errores.append("modos_de_falla vacío: el método tiene que declarar cómo falla")
    for f in proc.fundamentos:
        if not f.origen:
            errores.append(f"«{f.regla}»: sin origen")
        if not f.canonico and not f.empirico:
            errores.append(f"«{f.regla}»: sin respaldo canónico ni empírico")
        if not f.empirico and not f.no_probado.strip():
            errores.append(f"«{f.regla}»: sin evidencia empírica y con no_probado vacío")
        for cita in (*f.canonico, *f.empirico):
            fid = cita.split()[0] if cita.split() else ""
            estado = estados.get(fid)
            if estado is None:
                errores.append(f"«{f.regla}»: la cita «{cita}» no apunta a una fila de {proc.fuente_citas}")
            elif not _verificada(estado):
                errores.append(f"«{f.regla}»: la cita «{cita}» apunta a {fid}, que está «{estado}»")
    return errores
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `uv run pytest tests/test_estrategia_procedencia.py -v`
Expected: PASS (7 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/estrategia/procedencia.py tests/test_estrategia_procedencia.py
git commit -m "feat(estrategia): procedencia validada contra las filas verificadas de fuentes.md"
```

### Task S1-3: El registro y `config/estrategia.json`

**Files:**
- Create: `scripts/estrategia/registro.py`
- Create: `config/estrategia.json`
- Test: `tests/test_estrategia_registro.py`

**Interfaces:**
- Produces: `FABRICAS: dict[str, str]` (nombre → `"modulo:funcion"`), `EstrategiaDesconocida`,
  `cargar(nombre, fabricas=None) -> Estrategia`, `nombre_activo(ruta=CONFIG) -> str`,
  `activa(ruta=CONFIG) -> Estrategia`.

- [ ] **Step 1: Escribir el test que falla**

```python
"""El enchufe es una línea en config/estrategia.json (spec §2)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from estrategia import registro  # noqa: E402


def test_la_estrategia_activa_esta_registrada():
    assert registro.nombre_activo() in registro.FABRICAS


def test_una_estrategia_desconocida_dice_cuales_hay():
    with pytest.raises(registro.EstrategiaDesconocida, match="tori"):
        registro.cargar("ema50")


def test_carga_desde_una_fabrica_por_nombre():
    e = registro.cargar("json", {"json": "json:JSONDecoder"})
    assert type(e).__name__ == "JSONDecoder"


def test_una_config_sin_activa_falla_con_mensaje(tmp_path):
    ruta = tmp_path / "estrategia.json"
    ruta.write_text(json.dumps({"_meta": "x"}), encoding="utf-8")
    with pytest.raises(ValueError, match="activa"):
        registro.nombre_activo(ruta)
```

- [ ] **Step 2: Correrlo y verificar que falla**

Run: `uv run pytest tests/test_estrategia_registro.py -v`
Expected: FAIL con `ImportError: cannot import name 'registro'`.

- [ ] **Step 3: Implementar**

`config/estrategia.json` (escribir con Write, UTF-8 sin BOM):

```json
{
  "_meta": "El enchufe de estrategia: toda la lectura técnica sale de la estrategia nombrada en 'activa'. Spec: docs/superpowers/specs/2026-10-09-enchufe-estrategia-design.md. Para conectar otra, se escribe su paquete, pasa la batería de conformidad y se registra en scripts/estrategia/registro.py.",
  "activa": "tori"
}
```

`scripts/estrategia/registro.py`:

```python
"""Registro de estrategias y lectura de la activa (spec §2).

Las fábricas se nombran como texto ("modulo:funcion") y se importan recién al
cargarlas: así este módulo no arrastra el código de todas las estrategias, y la
estrategia de juguete de los tests nunca queda registrada en producción.
"""
from __future__ import annotations

import importlib
import json
from pathlib import Path

from estrategia.contrato import Estrategia

RAIZ = Path(__file__).resolve().parents[2]
CONFIG = RAIZ / "config" / "estrategia.json"
FABRICAS: dict[str, str] = {"tori": "estrategia.tori:crear"}


class EstrategiaDesconocida(LookupError):
    """La config nombra una estrategia que no está registrada."""


def cargar(nombre: str, fabricas: dict[str, str] | None = None) -> Estrategia:
    fabricas = FABRICAS if fabricas is None else fabricas
    if nombre not in fabricas:
        raise EstrategiaDesconocida(
            f"La estrategia «{nombre}» no está registrada. Registradas: {sorted(fabricas)}"
        )
    modulo, funcion = fabricas[nombre].split(":")
    return getattr(importlib.import_module(modulo), funcion)()


def nombre_activo(ruta: Path = CONFIG) -> str:
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    nombre = datos.get("activa")
    if not isinstance(nombre, str) or not nombre:
        raise ValueError(f"{ruta} no declara la estrategia 'activa'")
    return nombre


def activa(ruta: Path = CONFIG) -> Estrategia:
    return cargar(nombre_activo(ruta))
```

- [ ] **Step 4: Correr el test y verificar que pasa**

Run: `uv run pytest tests/test_estrategia_registro.py -v`
Expected: PASS (4 tests). `activa()` todavía no se prueba: Tori no existe hasta S3 (Task S3-4).

- [ ] **Step 5: Commit**

```bash
git add scripts/estrategia/registro.py config/estrategia.json tests/test_estrategia_registro.py
git commit -m "feat(estrategia): registro y config/estrategia.json con Tori como activa"
```

### Task S1-4: La estrategia de juguete y la batería de conformidad

**Files:**
- Create: `tests/estrategia_juguete.py`
- Create: `tests/estrategia_conformidad.py`
- Test: `tests/test_estrategia_conformidad.py`

**Interfaces:**
- Consumes: todo el contrato (S1-1), `validar` (S1-2).
- Produces (para S3-4): `estrategia_conformidad.verificar_sin_futuro(fabrica)`,
  `verificar_escenarios(fabrica)`, `verificar_prueba_solo_con_vela_en_curso(fabrica)`,
  `verificar_procedencia(fabrica)`, `verificar_marco_y_puntaje(fabrica)`,
  `verificar_divergencia_propia(fabrica)`, `verificar_seguir_misma_lectura(fabrica)`,
  `verificar_seguir_sin_futuro(fabrica)`, `verificar_seguir_anclas_fijas(fabrica)`,
  `velas_de(estrategia, semilla=11, extra=40)`, `PASO`. Y en el test, `FABRICAS` (S3-4 le agrega
  `"tori"`) y `CON_SEGUIR` (S3-6 le agrega `"tori"`).

- [ ] **Step 1: Escribir la batería y el test que la usa**

`tests/estrategia_conformidad.py`:

```python
"""Batería de conformidad del enchufe (spec §4 y §8).

Toda estrategia que se enchufe pasa estas verificaciones. Reciben una FÁBRICA y
no una instancia, porque la de "sin mirar el futuro" necesita instancias nuevas
para detectar una estrategia que guarda memoria entre lecturas.
"""
from __future__ import annotations

import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from estrategia.contrato import FLECHAS, Estrategia, Puntaje, VelaEnCurso  # noqa: E402
from estrategia.procedencia import validar  # noqa: E402

Fabrica = Callable[[], Estrategia]
PASO = {"H1": 3600, "H4": 4 * 3600, "D1": 86400, "W1": 7 * 86400}
T0 = 1_735_689_600  # 2025-01-01 00:00 UTC; las velas son sintéticas
CORTES = (0, 5, 17, 33)
SCL = ZoneInfo("America/Santiago")
TICKER = "SINTETICO"


def serie(n: int, paso: int, semilla: int) -> pd.DataFrame:
    """Caminata con tramos de tendencia: tiene líneas que trazar y rangos."""
    rng = random.Random(semilla)
    precio, tendencia, filas = 100.0, 0.0, []
    for i in range(n):
        if i % 40 == 0:
            tendencia = rng.uniform(-0.6, 0.6)
        apertura = precio
        cierre = max(1.0, apertura + tendencia + rng.gauss(0, 0.8))
        filas.append({
            "time": T0 + i * paso, "open": apertura, "close": cierre,
            "high": max(apertura, cierre) + abs(rng.gauss(0, 0.4)),
            "low": min(apertura, cierre) - abs(rng.gauss(0, 0.4)),
        })
        precio = cierre
    return pd.DataFrame(filas)


def velas_de(estrategia: Estrategia, semilla: int = 11, extra: int = 40) -> dict[str, pd.DataFrame]:
    m = estrategia.marcos
    return {marco: serie(m.velas[marco] + extra, PASO[marco], semilla + k)
            for k, marco in enumerate(m.todos)}


def recortar(velas: dict[str, pd.DataFrame], k: int) -> dict[str, pd.DataFrame]:
    return {m: df.iloc[: len(df) - k].reset_index(drop=True) for m, df in velas.items()}


def verificar_sin_futuro(fabrica: Fabrica) -> None:
    """La lectura del instante t es la misma aunque la estrategia haya visto después."""
    velas = velas_de(fabrica())
    for k in CORTES:
        recorte = recortar(velas, k)
        limpia = fabrica().leer(TICKER, recorte, 2)
        usada = fabrica()
        usada.leer(TICKER, velas, 2)
        assert usada.leer(TICKER, recorte, 2) == limpia, (
            f"recortando {k} velas, la lectura cambia si la estrategia ya vio el futuro"
        )
        for linea in limpia.lineas:
            ultima = int(recorte[linea.marco]["time"].iloc[-1])
            assert all(t <= ultima for t, _ in linea.puntos), (
                f"una línea {linea.rol} de {linea.marco} se ancla después de la última vela cerrada"
            )


def verificar_escenarios(fabrica: Fabrica) -> None:
    e = fabrica()
    velas = velas_de(e)
    for k in CORTES:
        flechas = [x.flecha for x in e.leer(TICKER, recortar(velas, k), 2).escenarios]
        assert sorted(flechas) == sorted(FLECHAS), f"escenarios {flechas} con {k} velas recortadas"


def verificar_prueba_solo_con_vela_en_curso(fabrica: Fabrica) -> None:
    e = fabrica()
    op = e.marcos.operativo
    velas = velas_de(e)
    for k in CORTES:
        recorte = recortar(velas, k)
        sin = e.leer(TICKER, recorte, 2)
        assert sin.estado != "PRUEBA" and sin.en_prueba is None, "PRUEBA sin vela en curso"
        df = recorte[op]
        apertura = int(df["time"].iloc[-1]) + PASO[op]
        cierre = datetime.fromtimestamp(apertura + PASO[op], tz=SCL)
        for precio in (float(df["high"].max()) * 1.5, float(df["low"].min()) * 0.5):
            con = e.leer(TICKER, recorte, 2, VelaEnCurso(apertura, precio, cierre))
            estructurales = lambda l: [x for x in l.lineas if x.rol != "objetivo"]  # noqa: E731
            assert estructurales(con) == estructurales(sin), "la vela abierta movió una línea"
            assert con.direccion == sin.direccion, "la vela abierta cambió la dirección"
            if con.estado == "PRUEBA":
                assert con.en_prueba.cierre_vela == cierre


def verificar_procedencia(fabrica: Fabrica) -> None:
    errores = validar(fabrica().procedencia)
    assert errores == [], "procedencia incompleta:\n" + "\n".join(errores)


def verificar_marco_y_puntaje(fabrica: Fabrica) -> None:
    e = fabrica()
    lectura = e.leer(TICKER, velas_de(e), 2)
    assert lectura.marco == e.marcos.operativo
    for horizonte in ("sesion", "semana"):
        assert isinstance(e.puntuar(lectura, horizonte), Puntaje)


def verificar_divergencia_propia(fabrica: Fabrica) -> None:
    e = fabrica()
    lectura = e.leer(TICKER, velas_de(e), 2)
    assert e.divergencia(lectura, lectura) is None, "una lectura diverge de sí misma"


def verificar_seguir_misma_lectura(fabrica: Fabrica) -> None:
    """Con las mismas velas, seguir() no cambia la lectura ni mueve un ancla."""
    e = fabrica()
    velas = velas_de(e)
    ref = e.leer(TICKER, velas, 2)
    misma = e.seguir(ref, velas, 2)
    assert (misma.estado, misma.direccion) == (ref.estado, ref.direccion), (
        "seguir() con las mismas velas cambia la lectura"
    )
    assert [(x.rol, x.puntos) for x in misma.lineas] == [(x.rol, x.puntos) for x in ref.lineas], (
        "seguir() movió un ancla"
    )
    assert misma.vela == ref.vela


def verificar_seguir_sin_futuro(fabrica: Fabrica) -> None:
    """seguir() cumple la misma regla que leer(): lo que vio después no cambia el pasado."""
    e = fabrica()
    op = e.marcos.operativo
    velas = velas_de(e)
    ref = e.leer(TICKER, recortar(velas, 33), 2)
    for k in (0, 5, 17):
        recorte = recortar(velas, k)
        limpia = fabrica().seguir(ref, recorte, 2)
        usada = fabrica()
        usada.seguir(ref, velas, 2)
        assert usada.seguir(ref, recorte, 2) == limpia, (
            f"recortando {k} velas, seguir() cambia si la estrategia ya vio el futuro"
        )
        assert limpia.vela == int(recorte[op]["time"].iloc[-1])


def verificar_seguir_anclas_fijas(fabrica: Fabrica) -> None:
    """Con velas nuevas, las anclas siguen siendo las del lunes (OjZ8d [01:07])."""
    e = fabrica()
    velas = velas_de(e)
    ref = e.leer(TICKER, recortar(velas, 33), 2)
    hoy = e.seguir(ref, velas, 2)
    assert sorted(x.puntos for x in hoy.lineas) == sorted(x.puntos for x in ref.lineas), (
        "seguir() volvió a trazar: las anclas no son las de la referencia"
    )
```

`tests/estrategia_juguete.py`:

```python
"""Estrategia de juguete: solo horizontales. Prueba que el contrato no tiene la forma de Tori.

Vive en tests/ y no se registra en producción (spec §4).
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from dataclasses import replace  # noqa: E402

from estrategia.contrato import (  # noqa: E402
    Escenario, Etiqueta, Fundamento, Lectura, Linea, Marcos, Procedencia, Prueba, Puntaje,
    Referencia, exigir_velas,
)


class Juguete:
    nombre = "juguete"
    marcos = Marcos((), "H4", {"H4": 40}, {"H4": Etiqueta("swing", "de una a dos semanas")})
    procedencia = Procedencia(
        "docs/metodologia-tendencias.md", "docs/investigacion/fundamentos/fuentes.md",
        (Fundamento("en lateral no se opera", ("estrategia de juguete de los tests",),
                    ("F3 p. 78",), (), "es un juguete: no mide nada"),),
        ("cualquier tendencia: solo mira el rango",),
    )

    def leer(self, ticker, velas, digits, en_curso=None):
        exigir_velas(velas, self.marcos)
        df = velas["H4"].tail(20)
        alto, bajo = round(float(df["high"].max()), digits), round(float(df["low"].min()), digits)
        t0 = int(df["time"].iloc[0])
        techo = Linea("rango", "horizontal", ((t0, alto),), "H4", 1, "", alto)
        piso = Linea("rango", "horizontal", ((t0, bajo),), "H4", 1, "", bajo)
        cierre = float(df["close"].iloc[-1])
        medio = (alto + bajo) / 2
        direccion = "ALCISTA" if cierre > medio else "BAJISTA" if cierre < medio else "LATERAL"
        estado, prueba = "RANGO", None
        if en_curso is not None and not bajo <= en_curso.precio <= alto:
            linea = techo if en_curso.precio > alto else piso
            estado, prueba = "PRUEBA", Prueba(linea, linea.valor_actual, en_curso.cierre)
        return Lectura(
            ticker=ticker, marco="H4", precio=en_curso.precio if en_curso else cierre,
            direccion=direccion, estado=estado, lineas=(techo, piso), en_prueba=prueba,
            vigilar=Referencia(alto, "techo del rango", techo), invalidacion=None, objetivo=None,
            escenarios=(Escenario("⬆️", f"Sobre {alto}", "sale por arriba"),
                        Escenario("↔️", "Dentro", "espera"),
                        Escenario("⬇️", f"Bajo {bajo}", "sale por abajo")),
            salida="dentro del rango no hay posición", conceptos=("rango",), avisos=(),
            vela=int(df["time"].iloc[-1]),
        )

    def seguir(self, referencia, velas, digits, en_curso=None):
        """Mide las velas de hoy contra el techo y el piso de la referencia, sin recalcularlos."""
        exigir_velas(velas, self.marcos)
        if referencia.estado == "PRUEBA":
            raise ValueError("una referencia no puede quedar en PRUEBA")
        techo, piso = referencia.lineas
        df = velas["H4"]
        despues = df[df["time"] > referencia.vela]
        rompio = bool(((despues["close"] > techo.valor_actual)
                       | (despues["close"] < piso.valor_actual)).any())
        cierre = float(df["close"].iloc[-1])
        estado, prueba = ("RUPTURA" if rompio else referencia.estado), None
        if en_curso is not None and not rompio and \
                not piso.valor_actual <= en_curso.precio <= techo.valor_actual:
            linea = techo if en_curso.precio > techo.valor_actual else piso
            estado, prueba = "PRUEBA", Prueba(linea, linea.valor_actual, en_curso.cierre)
        return replace(referencia, estado=estado, en_prueba=prueba,
                       precio=en_curso.precio if en_curso else cierre,
                       vela=int(df["time"].iloc[-1]))

    def puntuar(self, lectura, horizonte):
        return Puntaje(50.0, {"base": 50.0}, None)

    def divergencia(self, preparada, actual):
        return None if preparada.direccion == actual.direccion else "cambió la dirección"


class ConMemoria(Juguete):
    """Tramposa: devuelve la primera lectura de cada activo. La batería tiene que pillarla."""

    def __init__(self):
        self._vistas = {}

    def leer(self, ticker, velas, digits, en_curso=None):
        return self._vistas.setdefault(ticker, super().leer(ticker, velas, digits, en_curso))


def crear() -> Juguete:
    return Juguete()


def crear_con_memoria() -> ConMemoria:
    return ConMemoria()
```

`tests/test_estrategia_conformidad.py`:

```python
"""Toda estrategia registrable pasa la batería de conformidad (spec §4)."""
from __future__ import annotations

import pytest

import estrategia_conformidad as conf
import estrategia_juguete

FABRICAS = {"juguete": estrategia_juguete.crear}
CON_SEGUIR = {"juguete"}  # S3-6 agrega "tori" cuando Tori implementa seguir()

VERIFICACIONES = (
    conf.verificar_sin_futuro, conf.verificar_escenarios,
    conf.verificar_prueba_solo_con_vela_en_curso, conf.verificar_procedencia,
    conf.verificar_marco_y_puntaje, conf.verificar_divergencia_propia,
)
VERIFICACIONES_SEGUIR = (
    conf.verificar_seguir_misma_lectura, conf.verificar_seguir_sin_futuro,
    conf.verificar_seguir_anclas_fijas,
)


@pytest.mark.parametrize("nombre", sorted(FABRICAS))
@pytest.mark.parametrize("verificar", VERIFICACIONES, ids=lambda f: f.__name__)
def test_conformidad(nombre, verificar):
    verificar(FABRICAS[nombre])


@pytest.mark.parametrize("nombre", sorted(CON_SEGUIR))
@pytest.mark.parametrize("verificar", VERIFICACIONES_SEGUIR, ids=lambda f: f.__name__)
def test_conformidad_seguir(nombre, verificar):
    verificar(FABRICAS[nombre])


def test_la_bateria_pilla_una_estrategia_con_memoria():
    with pytest.raises(AssertionError, match="futuro"):
        conf.verificar_sin_futuro(estrategia_juguete.crear_con_memoria)


def test_el_juguete_entra_en_prueba_con_la_vela_fuera_del_rango():
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from estrategia.contrato import VelaEnCurso

    e = estrategia_juguete.crear()
    velas = conf.velas_de(e)
    cierre = datetime(2026, 10, 9, 13, 0, tzinfo=ZoneInfo("America/Santiago"))
    lectura = e.leer("X", velas, 2, VelaEnCurso(0, 10_000.0, cierre))
    assert lectura.estado == "PRUEBA" and lectura.en_prueba.linea.valor_actual == lectura.vigilar.precio
```

- [ ] **Step 2: Correr y verificar**

Run: `uv run pytest tests/test_estrategia_conformidad.py -v`
Expected: PASS (9 verificaciones del juguete + 2). Si `test_la_bateria_pilla_una_estrategia_con_memoria`
no levanta `AssertionError`, la batería no está detectando memoria: revisar que `verificar_sin_futuro`
use una instancia nueva para `limpia` y la misma instancia para las dos llamadas de `usada`.

- [ ] **Step 3: Suite completa**

Run: `uv run pytest`
Expected: todo verde (nada fuera de `estrategia` cambió).

- [ ] **Step 4: Commit**

```bash
git add tests/estrategia_conformidad.py tests/estrategia_juguete.py tests/test_estrategia_conformidad.py
git commit -m "test(estrategia): batería de conformidad y estrategia de juguete"
```

### Task S1-5: Cierre de la sesión S1

- [ ] **Step 1:** `git push -u origin feat/enchufe-s1-contrato` y abrir el PR contra master
  ("feat(estrategia): contrato, registro y batería de conformidad (enchufe S1)"), con el cuerpo:
  qué entra y que ningún pipeline cambia.
- [ ] **Step 2:** Anotar en OMEGA (`omega_store`, tipo `decision`) y en la memoria del proyecto
  (`project_enchufe_estrategia_tori.md`): S1 abierta en el PR N, contrato estable.
- [ ] **Step 3:** S2 empieza cuando el PR de S1 está mergeado.

---

# Sesión S2 · Tori: trazado y calidad

Rama: `git checkout master && git pull && git checkout -b feat/enchufe-s2-trazado`.

### Task S2-1: Parámetros, velas sintéticas y la mudanza del zigzag

**Files:**
- Create: `scripts/estrategia/tori/__init__.py` (vacío por ahora, solo docstring)
- Create: `scripts/estrategia/tori/parametros.py`
- Create: `scripts/estrategia/tori/pivotes.py`
- Modify: `scripts/tradingview_grafico.py:234-268` (la función `_zigzag` se reemplaza por un import)
- Create: `tests/velas_sinteticas.py`
- Test: `tests/test_tori_pivotes.py`

**Interfaces:**
- Produces: `Parametros` (dataclass, campos de abajo), `PARAMETROS = Parametros()`;
  `Serie(filas, times, highs, lows, closes, atr)` con `len()`; `serie_de(df, periodo_atr=14) ->
  Serie`; `zigzag(rows: list[dict], umbral: float) -> list[tuple[int, float, str]]`.
  En tests: `velas_sinteticas.desde_vertices(vertices, velas_por_tramo, paso=4*3600, mecha=0.2,
  t0=1_735_689_600) -> DataFrame` y `velas_sinteticas.agregar(df, cada) -> DataFrame`.

- [ ] **Step 1: Escribir el test que falla**

`tests/velas_sinteticas.py`:

```python
"""Velas sintéticas para probar el trazado de Tori con geometría conocida."""
from __future__ import annotations

import pandas as pd

T0 = 1_735_689_600  # 2025-01-01 00:00 UTC


def desde_vertices(vertices: list[float], velas_por_tramo: int, paso: int = 4 * 3600,
                   mecha: float = 0.2, t0: int = T0) -> pd.DataFrame:
    """Une los vértices con tramos rectos. La vela i abre en p_i y cierra en p_{i+1}."""
    camino = [vertices[0]]
    for a, b in zip(vertices, vertices[1:]):
        camino += [a + (b - a) * (k + 1) / velas_por_tramo for k in range(velas_por_tramo)]
    filas = []
    for i, (o, c) in enumerate(zip(camino, camino[1:])):
        filas.append({"time": t0 + i * paso, "open": o, "close": c,
                      "high": max(o, c) + mecha, "low": min(o, c) - mecha})
    return pd.DataFrame(filas)


def agregar(df: pd.DataFrame, cada: int) -> pd.DataFrame:
    """Junta `cada` velas en una (de H4 a D1 con 6, de H4 a W1 con 30)."""
    grupos = df.groupby(df.index // cada)
    return pd.DataFrame({
        "time": grupos["time"].first(), "open": grupos["open"].first(),
        "high": grupos["high"].max(), "low": grupos["low"].min(), "close": grupos["close"].last(),
    }).reset_index(drop=True)
```

`tests/test_tori_pivotes.py`:

```python
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import velas_sinteticas as vs  # noqa: E402
from estrategia.tori.pivotes import serie_de, zigzag  # noqa: E402


def test_zigzag_marca_los_giros_mayores_en_orden():
    df = vs.desde_vertices([100, 112, 106, 118], 12)
    giros = zigzag(df.to_dict("records"), 3.0)
    # El primer giro confirma también el mínimo de partida.
    assert [t for _, _, t in giros] == ["L", "H", "L"]
    assert [round(p, 1) for _, p, _ in giros] == [99.8, 112.2, 105.8]


def test_el_grafico_usa_el_mismo_zigzag():
    import tradingview_grafico

    assert tradingview_grafico._zigzag is zigzag


def test_serie_de_calcula_el_atr_como_media_simple_del_rango_verdadero():
    df = vs.desde_vertices([100, 112], 12)  # cada vela sube 1 y tiene 0,2 de mecha a cada lado
    s = serie_de(df)
    assert len(s) == 12
    assert abs(s.atr - 1.4) < 1e-9
```

- [ ] **Step 2: Correrlo y verificar que falla**

Run: `uv run pytest tests/test_tori_pivotes.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'estrategia.tori'`.

- [ ] **Step 3: Implementar**

`scripts/estrategia/tori/__init__.py`:

```python
"""La estrategia de Tori Trades (doctrina: docs/metodologia-tendencias.md)."""
```

`scripts/estrategia/tori/parametros.py`:

```python
"""Umbrales que Tori no da en números. Todos son NUESTROS (doctrina §2, §4).

Quedan declarados en la procedencia como `no_probado`: no habrá backtesting que
los mida. Los valores son provisionales y se revisan en el gate del director con
la medición del universo real (scripts/tori_revision.py).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Parametros:
    zigzag_atr: float = 2.0  # pivote candidato al segundo punto: giro de 2 ATR del marco
    tolerancia_toque_atr: float = 0.25  # la línea se traza "a ojo, con grosor" (Kffx9 [14:40])
    separacion_toque_atr: float = 1.0  # entre toques el precio "se aleja con claridad" (OjZ8d [06:13])
    pendiente_min_atr: float = 0.02  # bajo esto la línea es horizontal (OjZ8d [03:52])
    pendiente_empinada_atr: float = 0.5  # "muy empinada" (Murphy p. 103)
    velas_punto_b_reciente: int = 6  # V16: Punto B dentro del último día de 4H
    zigzag_horizontal_atr: float = 1.5
    tolerancia_horizontal_atr: float = 0.5  # el horizontal es una zona (qsjLm [08:52])
    horizontal_max_atr: float = 8.0  # "solo los cercanos" (qsjLm [03:27])
    velas_rango: int = 30  # bordes del rango sin diagonales: una semana de 4H
    cerca_atr_d1: float = 1.0  # spec §5: "a menos de un ATR diario"
    lejos_atr_d1: float = 2.0  # precio lejos de la línea de seguridad (doctrina 2.5)
    tope_adicionales: float = 24.0  # lo que suma dentro de una banda de situación


PARAMETROS = Parametros()
```

`scripts/estrategia/tori/pivotes.py`:

```python
"""Pivotes candidatos y ATR del marco (doctrina §4, regla 1).

El zigzag se mudó acá desde `tradingview_grafico._zigzag` (spec §5): es parte
de la estrategia, y el gráfico lo importa de este módulo mientras siga
dibujando su canal (hasta S5).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from estrategia.contrato import COLUMNAS_VELAS


@dataclass(frozen=True)
class Serie:
    filas: tuple[dict[str, Any], ...]
    times: tuple[int, ...]
    highs: tuple[float, ...]
    lows: tuple[float, ...]
    closes: tuple[float, ...]
    atr: float

    def __len__(self) -> int:
        return len(self.times)


def _atr(highs, lows, closes, periodo: int) -> float:
    """Media simple del rango verdadero de las últimas `periodo` velas."""
    if not highs:
        return 0.0
    rangos = [highs[0] - lows[0]] + [
        max(h - lo, abs(h - c0), abs(lo - c0))
        for h, lo, c0 in zip(highs[1:], lows[1:], closes[:-1])
    ]
    ultimos = rangos[-periodo:]
    return sum(ultimos) / len(ultimos)


def serie_de(df: pd.DataFrame, periodo_atr: int = 14) -> Serie:
    filas = tuple(df[list(COLUMNAS_VELAS)].to_dict("records"))
    times = tuple(int(f["time"]) for f in filas)
    highs = tuple(float(f["high"]) for f in filas)
    lows = tuple(float(f["low"]) for f in filas)
    closes = tuple(float(f["close"]) for f in filas)
    return Serie(filas, times, highs, lows, closes, _atr(highs, lows, closes, periodo_atr))
```

Y a continuación, en el mismo archivo, **la función `_zigzag` copiada tal cual** desde
`scripts/tradingview_grafico.py:234-268`, renombrada a `zigzag` (mismo cuerpo, misma docstring).

En `scripts/tradingview_grafico.py`, borrar las líneas 234-268 (la definición de `_zigzag`) y poner
en su lugar:

```python
# El zigzag se mudó a la estrategia (enchufe S2): los pivotes son parte de Tori.
from estrategia.tori.pivotes import zigzag as _zigzag  # noqa: E402
```

- [ ] **Step 4: Correr los tests**

Run: `uv run pytest tests/test_tori_pivotes.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Suite completa** (la mudanza toca el gráfico)

Run: `uv run pytest`
Expected: todo verde.

- [ ] **Step 6: Commit**

```bash
git add scripts/estrategia/tori/__init__.py scripts/estrategia/tori/parametros.py scripts/estrategia/tori/pivotes.py scripts/tradingview_grafico.py tests/velas_sinteticas.py tests/test_tori_pivotes.py
git commit -m "feat(tori): parámetros, serie con ATR y el zigzag mudado a la estrategia"
```

### Task S2-2: El trazado de la línea

**Files:**
- Create: `scripts/estrategia/tori/lineas.py`
- Test: `tests/test_tori_lineas.py`

**Interfaces:**
- Consumes: `Serie`, `zigzag` (S2-1), `Parametros`.
- Produces: `Trazo(sentido, i_a, p_a, i_b, p_b, toques: tuple[int, ...], i_ruptura: int | None)`
  con `.pendiente`, `.valor(i)`, `.vigente`; `trazar(s, sentido, p, ancla=None) -> Trazo | None`;
  `seguimiento(s, principal, p) -> Trazo | None` (lo implementa S2-4).

- [ ] **Step 1: Escribir el test que falla**

```python
"""Trazado de Tori (doctrina §2.1 y §4, reglas 2, 3 y 6)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import velas_sinteticas as vs  # noqa: E402
from estrategia.tori.lineas import trazar  # noqa: E402
from estrategia.tori.parametros import PARAMETROS as P  # noqa: E402
from estrategia.tori.pivotes import serie_de  # noqa: E402

# Mínimos 100, 106 y 112 alineados (pendiente 0,25 por vela), y un retroceso al final.
ALCISTA = [100, 112, 106, 118, 112, 124, 119]
# Espejo: máximos 124, 118 y 112 alineados, y un tramo final que rompe hacia arriba.
BAJISTA_ROTA = [124, 112, 118, 106, 112, 100]


def _respeta(s, t, tol):
    fin = t.i_ruptura if t.i_ruptura is not None else len(s)
    for i in range(t.i_a, fin):
        if t.sentido == "alcista":
            assert s.lows[i] >= t.valor(i) - tol - 1e-9, f"la vela {i} cruza la línea"
        else:
            assert s.highs[i] <= t.valor(i) + tol + 1e-9, f"la vela {i} cruza la línea"


def test_la_alcista_se_ancla_en_el_minimo_y_junta_los_tres_toques():
    s = serie_de(vs.desde_vertices(ALCISTA, 12))
    t = trazar(s, "alcista", P)
    assert t is not None and t.i_a == 0 and abs(t.p_a - 99.8) < 1e-9
    assert len(t.toques) >= 3 and t.vigente
    assert abs(t.pendiente - 0.25) < 1e-9
    _respeta(s, t, P.tolerancia_toque_atr * s.atr)


def test_ninguna_vela_cruza_la_linea_elegida_ni_con_una_mecha_suelta():
    df = vs.desde_vertices(ALCISTA, 12)
    df.loc[60, "low"] = df.loc[60, "low"] - 4.0  # una mecha que perfora y vuelve
    s = serie_de(df)
    t = trazar(s, "alcista", P)
    if t is not None:
        _respeta(s, t, P.tolerancia_toque_atr * s.atr)
        assert t.vigente, "una mecha no es ruptura"


def test_el_cierre_al_otro_lado_es_ruptura():
    df = vs.desde_vertices(BAJISTA_ROTA, 12)
    subida = vs.desde_vertices([100, 118], 6, t0=int(df["time"].iloc[-1]) + 4 * 3600)
    s = serie_de(pd.concat([df, subida], ignore_index=True))
    t = trazar(s, "bajista", P)
    assert t is not None and t.i_a == 0 and t.i_ruptura is not None
    assert s.closes[t.i_ruptura] > t.valor(t.i_ruptura)
    _respeta(s, t, P.tolerancia_toque_atr * s.atr)


def test_sin_segundo_punto_no_hay_linea():
    s = serie_de(vs.desde_vertices([120, 100], 24))  # el mínimo es la última vela
    assert trazar(s, "alcista", P) is None


def test_una_linea_plana_no_es_diagonal():
    s = serie_de(vs.desde_vertices([100, 110, 100, 110, 100, 110], 10))
    assert trazar(s, "alcista", P) is None
    assert trazar(s, "bajista", P) is None
```

- [ ] **Step 2: Correrlo y verificar que falla**

Run: `uv run pytest tests/test_tori_lineas.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'estrategia.tori.lineas'`.

- [ ] **Step 3: Implementar**

```python
"""Trazado de Tori: semirrecta desde el extremo visible, sin que ninguna vela la cruce.

Doctrina §2.1 y §4, reglas 2, 3, 6, 9 y 10. Las líneas se calculan por índice de
vela, como las dibuja TradingView: los fines de semana no ocupan espacio.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from estrategia.tori.parametros import Parametros
from estrategia.tori.pivotes import Serie, zigzag

Sentido = Literal["alcista", "bajista"]


@dataclass(frozen=True)
class Trazo:
    sentido: Sentido
    i_a: int
    p_a: float
    i_b: int
    p_b: float
    toques: tuple[int, ...]  # índices de las velas que tocan, A incluido
    i_ruptura: int | None  # primera vela que cerró al otro lado

    @property
    def pendiente(self) -> float:
        return (self.p_b - self.p_a) / (self.i_b - self.i_a)

    def valor(self, i: float) -> float:
        return self.p_a + self.pendiente * (i - self.i_a)

    @property
    def vigente(self) -> bool:
        return self.i_ruptura is None


def trazar(s: Serie, sentido: Sentido, p: Parametros, ancla: int | None = None) -> Trazo | None:
    """La mejor línea desde `ancla` (por defecto, el extremo de la ventana).

    El segundo punto es el pivote que junta más toques sin que ninguna vela cruce
    la línea; a igualdad de toques, la más ceñida al precio.
    """
    alcista = sentido == "alcista"
    extremos = s.lows if alcista else s.highs
    if len(s) < 3:
        return None
    if ancla is None:
        ancla = extremos.index(min(extremos) if alcista else max(extremos))
    tipo = "L" if alcista else "H"
    candidatos = [i for i, _, t in zigzag(list(s.filas), p.zigzag_atr * s.atr)
                  if t == tipo and i > ancla]
    mejor: Trazo | None = None
    for b in candidatos:
        pendiente = (extremos[b] - extremos[ancla]) / (b - ancla)
        if (pendiente <= 0) if alcista else (pendiente >= 0):
            continue  # pendiente invertida: se elimina (OjZ8d [04:22])
        if abs(pendiente) < p.pendiente_min_atr * s.atr:
            continue  # plana: se lee como horizontal, no como línea (OjZ8d [03:52])
        trazo = _recorrer(s, sentido, ancla, b, p)
        if trazo is not None and (mejor is None or _orden(trazo) > _orden(mejor)):
            mejor = trazo
    return mejor


def _orden(t: Trazo) -> tuple[int, float]:
    return (len(t.toques), abs(t.pendiente))


def _recorrer(s: Serie, sentido: Sentido, a: int, b: int, p: Parametros) -> Trazo | None:
    """Recorre de A al final. Devuelve None si una vela cruza sin cerrar al otro lado (V10)."""
    alcista = sentido == "alcista"
    extremos = s.lows if alcista else s.highs
    pendiente = (extremos[b] - extremos[a]) / (b - a)
    tol = p.tolerancia_toque_atr * s.atr
    lejos = p.separacion_toque_atr * s.atr
    toques: list[int] = []
    alejado = True
    ruptura = None
    for i in range(a, len(s)):
        linea = extremos[a] + pendiente * (i - a)
        holgura = (s.lows[i] - linea) if alcista else (linea - s.highs[i])
        if holgura < -tol:
            cierre = (s.closes[i] - linea) if alcista else (linea - s.closes[i])
            if i > b and cierre < -tol:
                ruptura = i  # cerró afuera por más que un asomo: ruptura por cierre (doctrina 2.4)
                break
            return None  # cruza y vuelve, o cruza antes de B: la línea no se traza (V10)
        if holgura <= tol:
            if alejado:
                toques.append(i)
                alejado = False
        elif holgura >= lejos:
            alejado = True
    if len(toques) < 2:
        return None  # A y B son el mismo toque: no hay línea
    return Trazo(sentido, a, extremos[a], b, extremos[b], tuple(toques), ruptura)


def seguimiento(s: Serie, principal: Trazo, p: Parametros) -> Trazo | None:
    """Abanico y encadenamiento: lo implementa la Task S2-4."""
    return None
```

- [ ] **Step 4: Correr los tests**

Run: `uv run pytest tests/test_tori_lineas.py -v`
Expected: PASS (5 tests). Si `test_el_cierre_al_otro_lado_es_ruptura` falla porque `trazar`
devuelve `None`, es que una vela del tramo de subida cruzó con la mecha y cerró dentro: imprimir
`[(i, s.highs[i], s.closes[i], t.valor(i)) for i in range(60, len(s))]` con un trazo forzado
(`_recorrer(s, "bajista", 0, 24, P)`) y revisar la geometría antes de tocar el algoritmo.

- [ ] **Step 5: Commit**

```bash
git add scripts/estrategia/tori/lineas.py tests/test_tori_lineas.py
git commit -m "feat(tori): trazado desde el extremo, sin cruzar velas y con ruptura por cierre"
```

### Task S2-3: La calidad de la línea

**Files:**
- Create: `scripts/estrategia/tori/calidad.py`
- Test: `tests/test_tori_calidad.py`

**Interfaces:**
- Consumes: `Trazo`, `trazar` (S2-2), `Serie`.
- Produces: `Calidad(calidad: str, semanas: float, punto_b_reciente: bool, empinada: bool)`,
  `calificar(t, s, p) -> Calidad`, `velas_por_semana(s) -> int`.

- [ ] **Step 1: Escribir el test que falla**

```python
"""Calidad de la línea (doctrina §2.2): A+ con 3 toques y una semana; B con 2."""
from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import velas_sinteticas as vs  # noqa: E402
from estrategia.tori.calidad import calificar  # noqa: E402
from estrategia.tori.lineas import trazar  # noqa: E402
from estrategia.tori.parametros import PARAMETROS as P  # noqa: E402
from estrategia.tori.pivotes import serie_de  # noqa: E402

ALCISTA = [100, 112, 106, 118, 112, 124, 119]


def test_tres_toques_en_mas_de_una_semana_es_a_mas():
    s = serie_de(vs.desde_vertices(ALCISTA, 12))  # 4H: unas 47 velas entre toques; la semana son 30
    c = calificar(trazar(s, "alcista", P), s, P)
    assert c.calidad == "A+" and c.semanas >= 1


def test_tres_toques_en_menos_de_una_semana_es_b():
    s = serie_de(vs.desde_vertices(ALCISTA, 12, paso=3600))  # 1H: la semana son 120 velas
    c = calificar(trazar(s, "alcista", P), s, P)
    assert c.calidad == "B" and c.semanas < 1


def test_dos_toques_es_b():
    s = serie_de(vs.desde_vertices([100, 112, 106, 124, 120], 12))
    t = trazar(s, "alcista", P)
    assert len(t.toques) == 2 and calificar(t, s, P).calidad == "B"


def test_un_punto_b_reciente_baja_la_calidad():
    s = serie_de(vs.desde_vertices(ALCISTA, 12))
    t = trazar(s, "alcista", P)
    reciente = replace(t, i_b=len(s) - 2)
    assert calificar(reciente, s, P).punto_b_reciente
    assert calificar(reciente, s, P).calidad == "B"


def test_marca_la_linea_muy_empinada():
    s = serie_de(vs.desde_vertices([100, 140, 130, 170, 160, 200, 195], 6))
    t = trazar(s, "alcista", P)
    assert calificar(t, s, P).empinada
```

- [ ] **Step 2: Correrlo y verificar que falla**

Run: `uv run pytest tests/test_tori_calidad.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'estrategia.tori.calidad'`.

- [ ] **Step 3: Implementar**

```python
"""Calidad de una línea (doctrina §2.2 y §4, reglas 4 y 5)."""
from __future__ import annotations

from dataclasses import dataclass

from estrategia.tori.lineas import Trazo
from estrategia.tori.parametros import Parametros
from estrategia.tori.pivotes import Serie

DIAS_HABILES = 5


@dataclass(frozen=True)
class Calidad:
    calidad: str  # "A+" o "B"
    semanas: float  # del primer al último toque, en semanas de velas del marco
    punto_b_reciente: bool  # V16
    empinada: bool


def velas_por_semana(s: Serie) -> int:
    """Una semana de datos son 5 días hábiles del marco: en 4H, 30 velas (doctrina §4).

    Se cuenta en velas y no en días de calendario, porque el fin de semana no tiene
    velas y en el gráfico de Tori no ocupa espacio. El paso es la mediana entre
    velas, que no se mueve por los huecos del fin de semana.
    """
    pasos = sorted(b - a for a, b in zip(s.times, s.times[1:]))
    if not pasos:
        return 1
    return max(1, round(DIAS_HABILES * 86400 / pasos[len(pasos) // 2]))


def calificar(t: Trazo, s: Serie, p: Parametros) -> Calidad:
    semanas = (t.toques[-1] - t.toques[0]) / velas_por_semana(s)
    reciente = t.i_b >= len(s) - p.velas_punto_b_reciente
    empinada = abs(t.pendiente) > p.pendiente_empinada_atr * s.atr
    a_mas = len(t.toques) >= 3 and semanas >= 1.0 and not reciente
    return Calidad("A+" if a_mas else "B", semanas, reciente, empinada)
```

- [ ] **Step 4: Correr los tests**

Run: `uv run pytest tests/test_tori_calidad.py -v`
Expected: PASS (5 tests). Si `test_dos_toques_es_b` encuentra 3 toques, la serie tocó la línea en
el último retroceso: subir el vértice final (por ejemplo 122) hasta que el retroceso quede sobre
la línea, y verificar que la aserción sigue hablando de 2 toques.

- [ ] **Step 5: Commit**

```bash
git add scripts/estrategia/tori/calidad.py tests/test_tori_calidad.py
git commit -m "feat(tori): calidad A+ o B, semana de datos, Punto B reciente y pendiente"
```

### Task S2-4: Abanico y encadenamiento

**Files:**
- Modify: `scripts/estrategia/tori/lineas.py` (reemplazar el cuerpo de `seguimiento`)
- Test: `tests/test_tori_lineas.py` (agregar dos tests)

- [ ] **Step 1: Agregar los tests que fallan**

```python
from estrategia.tori.lineas import seguimiento  # noqa: E402

ACELERA = [100, 112, 104, 116, 108, 128, 116, 136, 124]  # mínimos 100-104-108, después 116-124


def test_el_abanico_arranca_en_el_ultimo_toque_y_es_mas_empinado():
    s = serie_de(vs.desde_vertices(ACELERA, 12))
    principal = trazar(s, "alcista", P)
    seg = seguimiento(s, principal, P)
    assert seg is not None
    assert seg.i_a == principal.toques[-1]  # encadenar: el último toque es el nuevo Punto A
    assert seg.pendiente > principal.pendiente and seg.vigente


def test_sin_aceleracion_no_hay_linea_de_seguimiento():
    s = serie_de(vs.desde_vertices(ALCISTA, 12))
    assert seguimiento(s, trazar(s, "alcista", P), P) is None
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_tori_lineas.py -v`
Expected: FAIL en `test_el_abanico_arranca_en_el_ultimo_toque_y_es_mas_empinado` (`seg is None`).

- [ ] **Step 3: Implementar**

```python
def seguimiento(s: Serie, principal: Trazo, p: Parametros) -> Trazo | None:
    """Abanico y encadenamiento (doctrina §2.3, reglas 9 y 10).

    Desde el último toque de la principal se busca una línea más empinada. Si ya
    está rota, no se devuelve: la secundaria rota se borra (V13).
    """
    if not principal.vigente:
        return None
    t = trazar(s, principal.sentido, p, ancla=principal.toques[-1])
    if t is None or not t.vigente or abs(t.pendiente) <= abs(principal.pendiente):
        return None
    return t
```

- [ ] **Step 4: Correr los tests**

Run: `uv run pytest tests/test_tori_lineas.py -v`
Expected: PASS (7 tests). Si `trazar` de la principal elige otra línea (por ejemplo, de 100 a
116), revisar con `principal.toques` qué juntó: la serie `ACELERA` está pensada para que la línea
100-104-108 tenga 3 toques y la que pasa por 116 corte velas.

- [ ] **Step 5: Commit**

```bash
git add scripts/estrategia/tori/lineas.py tests/test_tori_lineas.py
git commit -m "feat(tori): línea de seguimiento por abanico, encadenada al último toque"
```

### Task S2-5: Horizontales

**Files:**
- Create: `scripts/estrategia/tori/horizontales.py`
- Test: `tests/test_tori_horizontales.py`

**Interfaces:**
- Produces: `Horizontal(precio, toques, i_primero)`, `detectar(s, p) -> list[Horizontal]`
  (ordenados por cercanía al último cierre), `bordes_rango(s, p) -> tuple[Horizontal, Horizontal]`
  (techo, piso).

- [ ] **Step 1: Escribir el test que falla**

```python
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import velas_sinteticas as vs  # noqa: E402
from estrategia.tori.horizontales import bordes_rango, detectar  # noqa: E402
from estrategia.tori.parametros import PARAMETROS as P  # noqa: E402
from estrategia.tori.pivotes import serie_de  # noqa: E402

RANGO = [100, 110, 100, 110, 100, 110, 100, 105]


def test_detecta_el_techo_y_el_piso_con_sus_toques():
    s = serie_de(vs.desde_vertices(RANGO, 10))
    niveles = detectar(s, P)
    assert any(abs(h.precio - 110.2) < 0.3 and h.toques >= 3 for h in niveles)
    assert any(abs(h.precio - 99.8) < 0.3 and h.toques >= 3 for h in niveles)


def test_los_mas_cercanos_al_precio_van_primero():
    s = serie_de(vs.desde_vertices(RANGO, 10))
    niveles = detectar(s, P)
    distancias = [abs(h.precio - s.closes[-1]) for h in niveles]
    assert distancias == sorted(distancias)


def test_los_bordes_del_rango_cuentan_sus_toques():
    s = serie_de(vs.desde_vertices(RANGO, 10))
    techo, piso = bordes_rango(s, P)
    assert abs(techo.precio - 110.2) < 1e-9 and abs(piso.precio - 99.8) < 1e-9
    assert techo.toques >= 2 and piso.toques >= 2
```

- [ ] **Step 2: Verificar que falla**

Run: `uv run pytest tests/test_tori_horizontales.py -v`
Expected: FAIL con `ModuleNotFoundError`.

- [ ] **Step 3: Implementar**

```python
"""Soportes y resistencias horizontales de Tori (doctrina §2.10).

Son confluencia, objetivo y borde del rango, nunca entrada. Hacen lo mismo que
`analisis._get_support_resistance`, pero son de la estrategia (spec §5).
"""
from __future__ import annotations

from dataclasses import dataclass

from estrategia.tori.parametros import Parametros
from estrategia.tori.pivotes import Serie, zigzag


@dataclass(frozen=True)
class Horizontal:
    precio: float
    toques: int
    i_primero: int


def _contar_toques(valores: tuple[float, ...], nivel: float, tol: float, lejos: float) -> int:
    toques, alejado = 0, True
    for v in valores:
        distancia = abs(v - nivel)
        if distancia <= tol:
            if alejado:
                toques += 1
                alejado = False
        elif distancia >= lejos:
            alejado = True
    return toques


def detectar(s: Serie, p: Parametros) -> list[Horizontal]:
    """Niveles con 2 toques o más, cercanos al precio, el más cercano primero."""
    if s.atr <= 0:
        return []
    pivotes = sorted((precio, i) for i, precio, _ in zigzag(list(s.filas), p.zigzag_horizontal_atr * s.atr))
    tol = p.tolerancia_horizontal_atr * s.atr
    grupos: list[list[tuple[float, int]]] = []
    for precio, i in pivotes:
        if grupos and precio - grupos[-1][0][0] <= tol:
            grupos[-1].append((precio, i))
        else:
            grupos.append([(precio, i)])
    actual = s.closes[-1]
    niveles = [Horizontal(sum(x for x, _ in g) / len(g), len(g), min(i for _, i in g))
               for g in grupos if len(g) >= 2]
    cercanos = [h for h in niveles if abs(h.precio - actual) <= p.horizontal_max_atr * s.atr]
    return sorted(cercanos, key=lambda h: abs(h.precio - actual))


def bordes_rango(s: Serie, p: Parametros) -> tuple[Horizontal, Horizontal]:
    """Máximo y mínimo de la última semana del marco (doctrina 2.10, xMNO4 [08:52])."""
    ini = max(0, len(s) - p.velas_rango)
    altos, bajos = s.highs[ini:], s.lows[ini:]
    techo, piso = max(altos), min(bajos)
    tol = p.tolerancia_horizontal_atr * s.atr
    lejos = p.separacion_toque_atr * s.atr
    return (
        Horizontal(techo, _contar_toques(altos, techo, tol, lejos), ini + altos.index(techo)),
        Horizontal(piso, _contar_toques(bajos, piso, tol, lejos), ini + bajos.index(piso)),
    )
```

- [ ] **Step 4: Correr los tests y la suite**

Run: `uv run pytest tests/test_tori_horizontales.py -v && uv run pytest`
Expected: PASS y suite verde.

- [ ] **Step 5: Commit**

```bash
git add scripts/estrategia/tori/horizontales.py tests/test_tori_horizontales.py
git commit -m "feat(tori): horizontales cercanos con toques y bordes del rango"
```

### Task S2-6: Cierre de la sesión S2

- [ ] **Step 1:** Push y PR ("feat(tori): trazado y calidad de líneas (enchufe S2)"). En el cuerpo:
  Tori traza pero todavía no lee; el zigzag se mudó y el gráfico lo importa desde la estrategia.
- [ ] **Step 2:** Memoria (OMEGA y `project_enchufe_estrategia_tori.md`): S2 en el PR N.
- [ ] **Step 3:** S3 empieza con S2 mergeada.

---

# Sesión S3 · Tori: lectura, puntaje y textos

Rama: `git checkout master && git pull && git checkout -b feat/enchufe-s3-lectura`.

### Task S3-1: La lectura sin vela en curso

**Files:**
- Create: `scripts/estrategia/tori/textos.py` (versión mínima en este paso; S3-3 la completa)
- Create: `scripts/estrategia/tori/lectura.py`
- Test: `tests/test_tori_lectura.py`

**Interfaces:**
- Consumes: `trazar`, `seguimiento`, `Trazo` (S2), `calificar`, `detectar`, `bordes_rango`,
  `serie_de`, contrato.
- Produces: `lectura.leer(ticker, velas, digits, en_curso, marcos, p) -> Lectura`,
  `lectura.divergencia(preparada, actual) -> str | None` (S3-4), y en `textos`:
  `sentido(linea) -> str`, `escenarios(...)`, `salida(...)`, `conceptos(estado)`.
  Claves de `Lectura.metricas`: `atr`, `atr_d1`, `confluencia`, `dist_seguridad_atr_d1`,
  `dist_accion_atr_d1`, `dist_objetivo_atr_d1`, `dist_vigilar_atr_d1`, `velas_desde_ruptura`,
  `doble_confirmacion`, `semanas_principal`, `contra_secuencia` (las que no aplican, no van).
  El rebote no es una métrica: es el estado `REBOTE` (hueco 13).

- [ ] **Step 1: Escribir el test que falla**

```python
"""Lectura de Tori sobre velas sintéticas (spec §5, doctrina §1)."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import velas_sinteticas as vs  # noqa: E402
from estrategia.contrato import Etiqueta, Marcos  # noqa: E402
from estrategia.tori import lectura as lt  # noqa: E402
from estrategia.tori.parametros import PARAMETROS as P  # noqa: E402

MARCOS = Marcos(("W1", "D1"), "H4", {"W1": 156, "D1": 250, "H4": 180},
                {"W1": Etiqueta("contexto", "de meses"), "D1": Etiqueta("posicional", "de semanas"),
                 "H4": Etiqueta("swing", "de una a dos semanas")})
ALCISTA = [100, 112, 106, 118, 112, 124, 119]
BAJISTA = [124, 112, 118, 106, 112, 100, 105]  # espejo de ALCISTA
BAJISTA_ROTA = [124, 112, 118, 106, 112, 100]
RANGO = [100, 110, 100, 110, 100, 110, 100, 105]
# Sigue a ALCISTA hasta 130 y vuelve a la línea alcista. La línea pasa por las mechas
# (99,8 + 0,25 por vela) y en la última vela (la 95) vale 123,55: esa vela baja a 123,65
# (mecha de 0,2) y cierra en 123,85, sobre la línea.
REBOTE = ALCISTA + [130, 123.85]


def velas(h4: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {"H4": h4, "D1": vs.agregar(h4, 6), "W1": vs.agregar(h4, 30)}


def rota() -> pd.DataFrame:
    df = vs.desde_vertices(BAJISTA_ROTA, 12)
    subida = vs.desde_vertices([100, 118], 6, t0=int(df["time"].iloc[-1]) + 4 * 3600)
    return pd.concat([df, subida], ignore_index=True)


def leer(h4, en_curso=None):
    return lt.leer("XAUUSD", velas(h4), 2, en_curso, MARCOS, P)


def test_tendencia_alcista_con_la_linea_de_seguridad_a_mas():
    lec = leer(vs.desde_vertices(ALCISTA, 12))
    assert (lec.estado, lec.direccion) == ("TENDENCIA", "ALCISTA")
    seguridad = next(x for x in lec.lineas if x.rol == "seguridad")
    assert seguridad.calidad == "A+" and seguridad.tipo == "diagonal"
    assert lec.invalidacion.linea == seguridad
    assert lec.precio > seguridad.valor_actual


def test_ruptura_por_cierre_de_la_bajista():
    lec = leer(rota())
    assert (lec.estado, lec.direccion) == ("RUPTURA", "ALCISTA")
    accion = next(x for x in lec.lineas if x.rol == "accion")
    assert lec.vigilar.linea == accion
    assert "velas_desde_ruptura" in lec.metricas
    assert any("seguridad" in a for a in lec.avisos)  # la serie no tiene alcista que la sostenga


def test_tocar_la_seguridad_y_cerrar_a_favor_es_rebote():
    lec = leer(vs.desde_vertices(REBOTE, 12))
    assert (lec.estado, lec.direccion) == ("REBOTE", "ALCISTA")
    seguridad = next(x for x in lec.lineas if x.rol == "seguridad")
    assert lec.vigilar.linea == seguridad and lec.invalidacion.linea == seguridad
    assert "rebote" in lec.conceptos and any("rebotó" in e.texto for e in lec.escenarios)


def test_rango_sin_diagonales():
    lec = leer(vs.desde_vertices(RANGO, 10))
    assert (lec.estado, lec.direccion) == ("RANGO", "LATERAL")
    bordes = [x for x in lec.lineas if x.rol == "rango"]
    assert len(bordes) == 2 and all(x.tipo == "horizontal" for x in bordes)


def test_sin_vela_en_curso_el_precio_es_el_ultimo_cierre():
    h4 = vs.desde_vertices(ALCISTA, 12)
    assert leer(h4).precio == float(h4["close"].iloc[-1])


def test_velas_sin_rango_fallan_con_mensaje():
    plano = pd.DataFrame({"time": [i * 14400 for i in range(40)], "open": [1.0] * 40,
                          "high": [1.0] * 40, "low": [1.0] * 40, "close": [1.0] * 40})
    with pytest.raises(ValueError, match="XAUUSD.*H4"):
        leer(plano)


def test_con_pocas_velas_lee_lo_que_hay():
    lec = leer(vs.desde_vertices([100, 104, 101], 10))
    assert lec.estado in ("RANGO", "TENDENCIA")
```

- [ ] **Step 2: Verificar que falla**

Run: `uv run pytest tests/test_tori_lectura.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'estrategia.tori.lectura'`.

- [ ] **Step 3: Implementar `textos.py` (completo; S3-3 solo le agrega tests)**

```python
"""Textos de cliente de Tori: escenarios, salida y conceptos (spec §5, textos.py).

Reglas de texto de cliente: sin guion largo, tuteo chileno sin voseo, flechas,
precios con los digits del activo. La ruptura se describe como "cerró al otro
lado de la línea" (doctrina 2.4).
"""
from __future__ import annotations

from estrategia.contrato import Escenario, Linea, Prueba, Referencia

VELA = {"H1": "una vela de 1 hora", "H4": "una vela de 4 horas", "D1": "una vela diaria",
        "W1": "una vela semanal"}
LA_VELA = {"H1": "la vela de 1 hora", "H4": "la vela de 4 horas", "D1": "la vela diaria",
           "W1": "la vela semanal"}


def _p(valor: float, digits: int) -> str:
    import pipeline_carrusel as pc  # el formato de precio es infraestructura (spec §3)

    return pc.formatear_precio(valor, digits)


def sentido(linea: Linea) -> str:
    if linea.tipo == "horizontal":
        return "horizontal"
    return "alcista" if linea.puntos[1][1] > linea.puntos[0][1] else "bajista"


def conceptos(estado: str) -> tuple[str, ...]:
    return {
        "TENDENCIA": ("linea-de-tendencia", "linea-de-seguridad"),
        "REBOTE": ("linea-de-tendencia", "linea-de-seguridad", "rebote"),
        "RUPTURA": ("linea-de-tendencia", "ruptura-por-cierre", "linea-de-seguridad"),
        "PRUEBA": ("linea-de-tendencia", "ruptura-por-cierre"),
        "RANGO": ("rango",),
    }[estado]


def salida(estado: str, marco: str, invalidacion: Referencia | None, digits: int,
           seguimiento: Linea | None = None) -> str:
    """La regla de salida de Tori (doctrina 2.8): vela que cierra al otro lado de la línea."""
    if estado == "RANGO":
        return "Dentro del rango no hay posición que gestionar: se espera la ruptura."
    if invalidacion is None:
        return "Todavía no hay línea de seguridad trazada, así que no hay salida que medir."
    texto = (f"La posición se cierra cuando {VELA.get(marco, marco)} cierra al otro lado de la "
             f"línea de seguridad, hoy en {_p(invalidacion.precio, digits)}. No hay objetivo fijo.")
    if seguimiento is not None:
        texto += (f" Como el precio aceleró, también vale cerrar cuando una vela cierre al otro lado "
                  f"de la línea de seguimiento, hoy en {_p(seguimiento.valor_actual, digits)}.")
    return texto


def escenarios(estado: str, direccion: str, marco: str, digits: int, precio: float,
               vigilar: Referencia, invalidacion: Referencia | None,
               objetivo: Referencia | None, prueba: Prueba | None,
               rango: list[Linea]) -> tuple[Escenario, Escenario, Escenario]:
    vela = VELA.get(marco, marco)
    if prueba is not None:
        return _en_prueba(prueba, precio, marco, digits)
    if estado == "RANGO":
        techo = max(x.valor_actual for x in rango)
        piso = min(x.valor_actual for x in rango)
        t, b = _p(techo, digits), _p(piso, digits)
        return (Escenario("⬆️", f"Cierre sobre {t}", f"Si {vela} cierra sobre {t}, el precio sale del rango hacia arriba."),
                Escenario("↔️", f"Entre {b} y {t}", "Dentro del rango no hay operación: se espera que una vela cierre fuera de uno de los bordes."),
                Escenario("⬇️", f"Cierre bajo {b}", f"Si {vela} cierra bajo {b}, el precio sale del rango hacia abajo."))
    sube = direccion == "ALCISTA"
    a_favor, en_contra = ("sobre", "bajo") if sube else ("bajo", "sobre")
    x = _p(vigilar.precio, digits)
    z = f" con objetivo en {_p(objetivo.precio, digits)}" if objetivo else ""
    if estado == "RUPTURA":
        rota = "bajista" if sube else "alcista"
        primero = Escenario("⬆️" if sube else "⬇️", f"{a_favor.capitalize()} {x}",
                            f"{LA_VELA.get(marco, marco).capitalize()} ya cerró {a_favor} la línea {rota}: mientras siga {a_favor} {x}, la ruptura sigue vigente{z}.")
        medio = Escenario("↔️", f"Vuelta a {x}",
                          f"Si el precio vuelve a {x} y la respeta, es un retesteo y la ruptura se confirma.")
        if invalidacion is not None:
            y = _p(invalidacion.precio, digits)
            ultimo = Escenario("⬇️" if sube else "⬆️", f"Cierre {en_contra} {y}",
                               f"Si {vela} cierra {en_contra} {y}, la línea de seguridad se rompe y la lectura deja de valer.")
        else:
            ultimo = Escenario("⬇️" if sube else "⬆️", f"Cierre {en_contra} {x}",
                               f"Si {vela} vuelve a cerrar {en_contra} {x}, la ruptura fue falsa.")
        return (primero, medio, ultimo) if sube else (ultimo, medio, primero)
    # TENDENCIA y REBOTE
    tendencia = "alcista" if sube else "bajista"
    y = _p(invalidacion.precio, digits)
    rompe = Escenario("⬇️" if sube else "⬆️", f"Cierre {en_contra} {y}",
                      f"Si {vela} cierra {en_contra} {y}, la línea {tendencia} se rompe y la tendencia deja de valer.")
    if estado == "REBOTE":
        # Es un hecho de la vela que cerró (doctrina 2.5, V7): se cuenta en pasado.
        sigue = Escenario("⬆️" if sube else "⬇️", f"{a_favor.capitalize()} {y}",
                          f"{LA_VELA.get(marco, marco).capitalize()} tocó la línea {tendencia} y cerró {a_favor} {y}: "
                          f"rebotó, y mientras el precio cierre {a_favor} {y}, la tendencia sigue{z}.")
        medio = Escenario("↔️", f"Vuelta a {y}",
                          f"Si el precio vuelve a {y}, la línea se pone a prueba otra vez: otro cierre {a_favor} confirma el rebote.")
        return (sigue, medio, rompe) if sube else (rompe, medio, sigue)
    if vigilar.linea is not None and vigilar.linea.rol == "accion":
        contraria = "bajista" if sube else "alcista"
        sigue = Escenario("⬆️" if sube else "⬇️", f"Cierre {a_favor} {x}",
                          f"Si {vela} cierra {a_favor} {x}, se rompe la línea {contraria} del retroceso y la tendencia retoma{z}.")
        medio = Escenario("↔️", f"Entre {y} y {x}" if sube else f"Entre {x} y {y}",
                          f"Mientras el precio siga entre las dos líneas, la tendencia {tendencia} sigue en pie, pero todavía no hay ruptura que operar.")
    else:
        sigue = Escenario("⬆️" if sube else "⬇️", f"{a_favor.capitalize()} {y}",
                          f"Mientras el precio cierre {a_favor} {y}, la tendencia {tendencia} sigue{z}.")
        medio = Escenario("↔️", f"Vuelta a {y}",
                          f"Si el precio vuelve a {y} y la respeta, la línea suma un toque y gana fuerza.")
    return (sigue, medio, rompe) if sube else (rompe, medio, sigue)


def _en_prueba(prueba: Prueba, precio: float, marco: str, digits: int) -> tuple[Escenario, Escenario, Escenario]:
    """Siempre como condición, nunca como hecho (spec §4, "Cómo se comunica")."""
    x = _p(prueba.valor_ahora, digits)
    hora = prueba.cierre_vela.strftime("%H:%M")
    la_vela = LA_VELA.get(marco, marco)
    abajo = precio < prueba.valor_ahora
    rompe = Escenario("⬇️" if abajo else "⬆️", f"Cierre {'bajo' if abajo else 'sobre'} {x} a las {hora}",
                      f"Si {la_vela} cierra {'bajo' if abajo else 'sobre'} {x} a las {hora}, la línea se considera rota y la lectura pasa a {'bajista' if abajo else 'alcista'}.")
    espera = Escenario("↔️", f"Hasta las {hora}",
                       f"Hasta el cierre de las {hora} (hora de Chile) es una prueba, no una ruptura: la vela todavía puede volver.")
    vuelve = Escenario("⬆️" if abajo else "⬇️", f"Cierre {'sobre' if abajo else 'bajo'} {x}",
                       f"Si vuelve a cerrar {'sobre' if abajo else 'bajo'} {x}, fue solo una mecha y la lectura no cambia.")
    return (vuelve, espera, rompe) if abajo else (rompe, espera, vuelve)
```

- [ ] **Step 4: Implementar `lectura.py`**

```python
"""Lectura de Tori: de las líneas trazadas a la Lectura del contrato (spec §5, lectura.py).

Las velas cerradas mandan: líneas, toques, calidad, dirección y RUPTURA salen
solo de ellas. La vela en curso, si llega, solo puede poner el estado PRUEBA
encima (spec §4, "La vela abierta"); lo agrega la Task S3-2.
"""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from estrategia.contrato import Lectura, Linea, Marcos, Prueba, Referencia, VelaEnCurso, exigir_velas
from estrategia.tori import textos
from estrategia.tori.calidad import calificar
from estrategia.tori.horizontales import Horizontal, bordes_rango, detectar
from estrategia.tori.lineas import Trazo, seguimiento, trazar
from estrategia.tori.parametros import Parametros
from estrategia.tori.pivotes import Serie, serie_de


@dataclass(frozen=True)
class _Estructura:
    estado: str
    direccion: str
    accion: Trazo | None
    seguridad: Trazo | None
    rango: tuple[Trazo, ...]
    velas_desde_ruptura: int | None


def _serie(velas: dict[str, pd.DataFrame], marco: str, marcos: Marcos) -> Serie:
    return serie_de(velas[marco].tail(marcos.velas[marco]).reset_index(drop=True))


def _peso(t: Trazo, s: Serie, p: Parametros) -> tuple[bool, int, float]:
    c = calificar(t, s, p)
    return (c.calidad == "A+", len(t.toques), c.semanas)


def _sigue_afuera(s: Serie, t: Trazo) -> bool:
    ultimo = len(s) - 1
    linea = t.valor(ultimo)
    return s.closes[ultimo] < linea if t.sentido == "alcista" else s.closes[ultimo] > linea


def _estructura(s: Serie, alc: Trazo | None, baj: Trazo | None, p: Parametros) -> _Estructura:
    ultimo = len(s) - 1
    rotas = [t for t in (alc, baj) if t is not None and not t.vigente]
    vigentes = [t for t in (alc, baj) if t is not None and t.vigente]
    reciente = max(rotas, key=lambda t: t.i_ruptura, default=None)
    desde = None if reciente is None else ultimo - reciente.i_ruptura
    # Sin límite de velas: la ruptura dura mientras el cierre siga afuera (huecos, punto 5).
    if reciente is not None and _sigue_afuera(s, reciente):
        direccion = "BAJISTA" if reciente.sentido == "alcista" else "ALCISTA"
        opuesta = next((t for t in vigentes if t.sentido != reciente.sentido), None)
        return _Estructura("RUPTURA", direccion, reciente, opuesta, (), desde)
    if not vigentes:
        return _Estructura("RANGO", "LATERAL", None, None, (), desde)
    if len(vigentes) == 2 and all(calificar(t, s, p).calidad != "A+" for t in vigentes):
        return _Estructura("RANGO", "LATERAL", None, None, tuple(vigentes), desde)
    principal = max(vigentes, key=lambda t: _peso(t, s, p))
    contraria = next((t for t in vigentes if t is not principal), None)
    direccion = "ALCISTA" if principal.sentido == "alcista" else "BAJISTA"
    return _Estructura("TENDENCIA", direccion, contraria, principal, (), desde)


def _linea(t: Trazo, s: Serie, rol: str, marco: str, p: Parametros, digits: int) -> Linea:
    c = calificar(t, s, p)
    return Linea(rol=rol, tipo="diagonal",
                 puntos=((s.times[t.i_a], round(t.p_a, digits)), (s.times[t.i_b], round(t.p_b, digits))),
                 marco=marco, toques=len(t.toques), calidad=c.calidad,
                 valor_actual=round(t.valor(len(s) - 1), digits), empinada=c.empinada)


def _horizontal(h: Horizontal, s: Serie, rol: str, marco: str, digits: int) -> Linea:
    return Linea(rol=rol, tipo="horizontal", puntos=((s.times[h.i_primero], round(h.precio, digits)),),
                 marco=marco, toques=h.toques, calidad="", valor_actual=round(h.precio, digits))


def _contexto(velas, marcos: Marcos, direccion: str, p: Parametros,
              digits: int) -> tuple[list[Linea], float, bool]:
    """Líneas vigentes de los marcos de contexto, qué parte va a favor y si todos van en contra.

    Doctrina 2.9 y 2.11: las falsas rupturas vienen de operar contra la secuencia de los
    marcos mayores (ipUbs [00:36], [01:11]).
    """
    lineas: list[Linea] = []
    votos: list[float] = []
    for marco in marcos.contexto:
        sc = _serie(velas, marco, marcos)
        if sc.atr <= 0:
            continue
        vigentes = [t for t in (trazar(sc, "alcista", p), trazar(sc, "bajista", p))
                    if t is not None and t.vigente]
        lineas += [_linea(t, sc, "contexto", marco, p, digits) for t in vigentes]
        if vigentes and direccion != "LATERAL":
            principal = max(vigentes, key=lambda t: _peso(t, sc, p))
            votos.append(1.0 if (principal.sentido == "alcista") == (direccion == "ALCISTA") else 0.0)
    a_favor = sum(votos) / len(votos) if votos else 0.0
    return lineas, a_favor, bool(votos) and a_favor == 0.0


def _horizontales(velas, marcos: Marcos, p: Parametros) -> list[tuple[Horizontal, Serie, str]]:
    salida = []
    for marco in (marcos.operativo, *marcos.contexto):
        sm = _serie(velas, marco, marcos)
        salida += [(h, sm, marco) for h in detectar(sm, p)]
    return salida


def _objetivo(horizontales, direccion: str, precio: float, tol: float, digits: int,
              operativo: str) -> Linea | None:
    """El horizontal MAYOR más cercano en la dirección (doctrina 2.8, V11).

    Primero los de los marcos de contexto; los del marco operativo solo si no hay
    ninguno mayor en la dirección.
    """
    if direccion == "LATERAL":
        return None
    mayores = [x for x in horizontales if x[2] != operativo]
    menores = [x for x in horizontales if x[2] == operativo]
    for grupo in (mayores, menores):
        if direccion == "ALCISTA":
            cand = [x for x in grupo if x[0].precio > precio + tol]
            elegido = min(cand, key=lambda x: x[0].precio, default=None)
        else:
            cand = [x for x in grupo if x[0].precio < precio - tol]
            elegido = max(cand, key=lambda x: x[0].precio, default=None)
        if elegido is not None:
            h, sm, marco = elegido
            return _horizontal(h, sm, "objetivo", marco, digits)
    return None


def _prueba(vivas: list[tuple[Linea, float]], cierre: float, en_curso: VelaEnCurso | None,
            tol: float, digits: int) -> Prueba | None:
    """Lo completa la Task S3-2."""
    return None


def _rebote(s, valor: float, sentido: str, tol: float) -> bool:
    """La última vela cerrada tocó la línea de seguridad y cerró a favor (doctrina 2.5, V7)."""
    i = len(s) - 1
    if sentido == "alcista":
        return s.lows[i] - valor <= tol and s.closes[i] > valor
    return valor - s.highs[i] <= tol and s.closes[i] < valor


def _vigilar(prueba, estado, accion, seguridad, rango, precio) -> Referencia:
    if prueba is not None:
        return Referencia(prueba.valor_ahora, f"línea {textos.sentido(prueba.linea)} en prueba", prueba.linea)
    if estado == "REBOTE":
        # Lo que se mira es la línea que sostuvo el rebote.
        return Referencia(seguridad.valor_actual, f"línea {textos.sentido(seguridad)} de seguridad", seguridad)
    if estado in ("RUPTURA", "TENDENCIA"):
        x = accion if accion is not None else seguridad
        return Referencia(x.valor_actual, f"línea {textos.sentido(x)}", x)
    cercana = min(rango, key=lambda x: abs(x.valor_actual - precio))
    techo = max(x.valor_actual for x in rango)
    etiqueta = "techo del rango" if cercana.valor_actual == techo else "piso del rango"
    return Referencia(cercana.valor_actual, etiqueta, cercana)


def leer(ticker: str, velas: dict[str, pd.DataFrame], digits: int,
         en_curso: VelaEnCurso | None, marcos: Marcos, p: Parametros) -> Lectura:
    exigir_velas(velas, marcos)
    op = marcos.operativo
    s = _serie(velas, op, marcos)
    if s.atr <= 0:
        raise ValueError(f"{ticker}: las velas de {op} no tienen rango (ATR 0); no hay nada que leer")
    e = _estructura(s, trazar(s, "alcista", p), trazar(s, "bajista", p), p)
    avisos: list[str] = []
    siguiente = len(s)  # índice de la vela abierta

    accion = _linea(e.accion, s, "accion", op, p, digits) if e.accion else None
    seguridad = _linea(e.seguridad, s, "seguridad", op, p, digits) if e.seguridad else None
    lineas: list[Linea] = [x for x in (accion, seguridad) if x is not None]
    vivas: list[tuple[Linea, float]] = []
    if accion is not None and e.accion.vigente:
        vivas.append((accion, e.accion.valor(siguiente)))
    linea_seguimiento: Linea | None = None
    if seguridad is not None:
        vivas.append((seguridad, e.seguridad.valor(siguiente)))
        seg = seguimiento(s, e.seguridad, p)
        if seg is not None:
            linea_seguimiento = _linea(seg, s, "seguimiento", op, p, digits)
            lineas.append(linea_seguimiento)
    rango: list[Linea] = []
    for t in e.rango:
        x = _linea(t, s, "rango", op, p, digits)
        rango.append(x)
        vivas.append((x, t.valor(siguiente)))
    if e.estado == "RANGO" and not rango:
        for h in bordes_rango(s, p):
            x = _horizontal(h, s, "rango", op, digits)
            rango.append(x)
            vivas.append((x, x.valor_actual))
        avisos.append("sin línea diagonal vigente: se lee como rango entre el máximo y el mínimo de la última semana")
    lineas += rango

    contexto, a_favor, contra = _contexto(velas, marcos, e.direccion, p, digits)
    lineas += contexto
    if contra:
        avisos.append("la lectura va contra la secuencia de los marcos mayores: es donde nacen las falsas rupturas")

    cierre = s.closes[-1]
    precio = en_curso.precio if en_curso is not None else cierre
    tol = p.tolerancia_toque_atr * s.atr
    prueba = _prueba(vivas, cierre, en_curso, tol, digits)
    rebote = e.estado == "TENDENCIA" and e.seguridad is not None and \
        _rebote(s, e.seguridad.valor(len(s) - 1), e.seguridad.sentido, tol)
    base = "REBOTE" if rebote else e.estado
    estado = "PRUEBA" if prueba is not None else base

    horizontales = _horizontales(velas, marcos, p)
    objetivo_linea = _objetivo(horizontales, e.direccion, precio, tol, digits, op)
    if objetivo_linea is not None:
        lineas.append(objetivo_linea)

    vigilar = _vigilar(prueba, base, accion, seguridad, rango, precio)
    invalidacion = (Referencia(seguridad.valor_actual, f"línea {textos.sentido(seguridad)} de seguridad", seguridad)
                    if seguridad is not None else None)
    objetivo = Referencia(objetivo_linea.valor_actual, "objetivo", objetivo_linea) if objetivo_linea else None
    if e.estado == "RUPTURA" and seguridad is None:
        avisos.append("la ruptura no tiene línea de seguridad trazable: el riesgo no se puede medir")
    if seguridad is not None and seguridad.empinada:
        avisos.append("la línea de seguridad es muy empinada: una vela de noticias puede cruzarla sin que cambie la tendencia")

    atr_d1 = _serie(velas, "D1", marcos).atr if "D1" in marcos.todos else 0.0
    atr_d1 = atr_d1 if atr_d1 > 0 else s.atr
    metricas = {"atr": s.atr, "atr_d1": atr_d1, "confluencia": a_favor,
                "dist_vigilar_atr_d1": abs(precio - vigilar.precio) / atr_d1}
    if seguridad is not None:
        metricas["dist_seguridad_atr_d1"] = abs(precio - seguridad.valor_actual) / atr_d1
        metricas["semanas_principal"] = calificar(e.seguridad, s, p).semanas
    if accion is not None:
        metricas["dist_accion_atr_d1"] = abs(precio - accion.valor_actual) / atr_d1
    if objetivo is not None:
        metricas["dist_objetivo_atr_d1"] = abs(precio - objetivo.precio) / atr_d1
    if e.velas_desde_ruptura is not None:
        metricas["velas_desde_ruptura"] = float(e.velas_desde_ruptura)
    zona = p.tolerancia_horizontal_atr * s.atr
    metricas["doble_confirmacion"] = 1.0 if any(abs(h.precio - vigilar.precio) <= zona
                                                for h, _, _ in horizontales) else 0.0
    metricas["contra_secuencia"] = 1.0 if contra else 0.0

    return Lectura(
        ticker=ticker, marco=op, precio=precio, direccion=e.direccion, estado=estado,
        lineas=tuple(lineas), en_prueba=prueba, vigilar=vigilar, invalidacion=invalidacion,
        objetivo=objetivo,
        escenarios=textos.escenarios(estado, e.direccion, op, digits, precio, vigilar,
                                     invalidacion, objetivo, prueba, rango),
        salida=textos.salida(estado, op, invalidacion, digits, linea_seguimiento),
        conceptos=textos.conceptos(estado), avisos=tuple(avisos), metricas=metricas,
        vela=s.times[-1],
    )
```

- [ ] **Step 5: Correr los tests**

Run: `uv run pytest tests/test_tori_lectura.py -v`
Expected: PASS (7 tests). Si `test_velas_sin_rango_fallan_con_mensaje` falla antes del `ValueError`
de ATR, es que `exigir_velas` rechazó algo antes: revisar que las velas planas traen las 5
columnas. Si falla el del rebote, mirar primero la serie: la línea alcista tiene que valer
123,55 en la última vela y la tolerancia (0,25 ATR) tiene que cubrir los 0,1 de distancia a la mecha. Se
corrige la serie, nunca la regla.

- [ ] **Step 6: Commit**

```bash
git add scripts/estrategia/tori/textos.py scripts/estrategia/tori/lectura.py tests/test_tori_lectura.py
git commit -m "feat(tori): lectura de tendencia, ruptura y rango sobre velas cerradas"
```

### Task S3-2: El estado `PRUEBA`

**Files:**
- Modify: `scripts/estrategia/tori/lectura.py` (cuerpo de `_prueba`)
- Test: `tests/test_tori_lectura.py` (agregar tests)

- [ ] **Step 1: Agregar los tests que fallan**

```python
from datetime import datetime  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

from estrategia.contrato import VelaEnCurso  # noqa: E402

CIERRE = datetime(2026, 10, 9, 13, 0, tzinfo=ZoneInfo("America/Santiago"))


def _vela(h4, precio):
    return VelaEnCurso(int(h4["time"].iloc[-1]) + 4 * 3600, precio, CIERRE)


def test_el_precio_vivo_bajo_la_seguridad_es_prueba_y_no_ruptura():
    h4 = vs.desde_vertices(ALCISTA, 12)
    base = leer(h4)
    seguridad = next(x for x in base.lineas if x.rol == "seguridad")
    lec = leer(h4, _vela(h4, seguridad.valor_actual - 5))
    assert lec.estado == "PRUEBA" and lec.direccion == "ALCISTA"
    assert lec.en_prueba.linea == seguridad and lec.en_prueba.cierre_vela == CIERRE
    assert any("13:00" in e.texto for e in lec.escenarios)


def test_un_precio_vivo_dentro_de_la_tolerancia_es_toque_no_prueba():
    h4 = vs.desde_vertices(ALCISTA, 12)
    seguridad = next(x for x in leer(h4).lineas if x.rol == "seguridad")
    lec = leer(h4, _vela(h4, seguridad.valor_actual + 0.25))  # la línea sube 0,25 en la vela abierta
    assert lec.estado == "TENDENCIA"


def test_la_vela_abierta_no_mueve_ninguna_linea():
    h4 = vs.desde_vertices(ALCISTA, 12)
    base = leer(h4)
    lec = leer(h4, _vela(h4, 90.0))
    sin_objetivo = lambda l: [x for x in l.lineas if x.rol != "objetivo"]  # noqa: E731
    assert sin_objetivo(lec) == sin_objetivo(base)


def test_en_rango_salir_del_borde_en_vivo_es_prueba():
    h4 = vs.desde_vertices(RANGO, 10)
    lec = leer(h4, _vela(h4, 125.0))
    assert lec.estado == "PRUEBA" and lec.en_prueba.linea.rol == "rango"
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_tori_lectura.py -v`
Expected: FAIL en los dos tests que esperan `PRUEBA`.

- [ ] **Step 3: Implementar `_prueba`**

```python
def _prueba(vivas: list[tuple[Linea, float]], cierre: float, en_curso: VelaEnCurso | None,
            tol: float, digits: int) -> Prueba | None:
    """El precio vivo al otro lado de una línea vigente, por más que la tolerancia.

    Cuenta el precio vivo y no el extremo de la vela: una mecha que ya volvió no
    activa la prueba (spec §4). El orden de `vivas` (acción, seguridad, rango) es
    la prioridad.
    """
    if en_curso is None:
        return None
    for linea, valor_ahora in vivas:
        antes = cierre - linea.valor_actual
        ahora = en_curso.precio - valor_ahora
        if antes * ahora < 0 and abs(ahora) > tol:
            return Prueba(linea, round(valor_ahora, digits), en_curso.cierre)
    return None
```

- [ ] **Step 4: Correr los tests**

Run: `uv run pytest tests/test_tori_lectura.py -v`
Expected: PASS (11 tests).

- [ ] **Step 5: Commit**

```bash
git add scripts/estrategia/tori/lectura.py tests/test_tori_lectura.py
git commit -m "feat(tori): estado PRUEBA con la vela en curso, sin mover ninguna línea"
```

### Task S3-3: Textos de cliente

**Files:**
- Test: `tests/test_tori_textos.py` (el código ya está desde S3-1)

- [ ] **Step 1: Escribir los tests**

```python
"""Los textos de Tori cumplen las reglas de texto de cliente (CLAUDE.md)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import test_tori_lectura as tl  # noqa: E402

VOSEO = re.compile(r"\b(ten[ée]s|pod[ée]s|sab[ée]s|mir[áa]|fijate|and[áa])\b", re.IGNORECASE)
CASOS = {
    "tendencia": lambda: tl.leer(tl.vs.desde_vertices(tl.ALCISTA, 12)),
    "ruptura": lambda: tl.leer(tl.rota()),
    "rango": lambda: tl.leer(tl.vs.desde_vertices(tl.RANGO, 10)),
    "rebote": lambda: tl.leer(tl.vs.desde_vertices(tl.REBOTE, 12)),
    "prueba": lambda: tl.leer(tl.vs.desde_vertices(tl.ALCISTA, 12),
                              tl._vela(tl.vs.desde_vertices(tl.ALCISTA, 12), 90.0)),
}


@pytest.mark.parametrize("caso", sorted(CASOS))
def test_sin_guion_largo_ni_voseo(caso):
    lec = CASOS[caso]()
    textos = [lec.salida] + [e.texto for e in lec.escenarios] + [e.condicion for e in lec.escenarios]
    for t in textos:
        assert "—" not in t and "–" not in t, t
        assert not VOSEO.search(t), t


@pytest.mark.parametrize("caso", sorted(CASOS))
def test_cada_escenario_nombra_un_precio_en_notacion_chilena(caso):
    lec = CASOS[caso]()
    for e in lec.escenarios:
        assert re.search(r"\d+,\d{2}", e.condicion + e.texto), e


def test_la_ruptura_se_describe_como_cierre():
    lec = CASOS["ruptura"]()
    assert any("cerró" in e.texto for e in lec.escenarios)
```

- [ ] **Step 2: Correr**

Run: `uv run pytest tests/test_tori_textos.py -v`
Expected: PASS (11 tests). Si uno falla, el defecto está en `textos.py`: corregir la frase, nunca
relajar el test.

- [ ] **Step 3: Commit**

```bash
git add tests/test_tori_textos.py
git commit -m "test(tori): textos de cliente sin guion largo, sin voseo y con precios"
```

### Task S3-4: Tori enchufable: procedencia, divergencia, registro y conformidad

**Files:**
- Create: `scripts/estrategia/tori/procedencia.py`
- Modify: `scripts/estrategia/tori/__init__.py`
- Modify: `scripts/estrategia/tori/lectura.py` (agregar `divergencia`)
- Modify: `tests/test_estrategia_conformidad.py` (agregar `"tori"` a `FABRICAS`)
- Modify: `tests/test_estrategia_registro.py` (agregar el test de `activa()`)
- Test: `tests/test_tori_divergencia.py`

**Interfaces:**
- Produces: `estrategia.tori.crear() -> Tori`, `Tori.nombre == "tori"`, `Tori.marcos`
  (`MARCOS`), `Tori.procedencia` (`PROCEDENCIA`), `Tori.leer`, `Tori.puntuar` (S3-5),
  `Tori.divergencia`.

- [ ] **Step 1: Escribir los tests que fallan**

En `tests/test_estrategia_conformidad.py`, cambiar la definición:

```python
from estrategia import tori  # noqa: E402

FABRICAS = {"juguete": estrategia_juguete.crear, "tori": tori.crear}
```

(con el bloque de `sys.path` de los otros tests antes del import).

En `tests/test_estrategia_registro.py`, agregar:

```python
def test_la_activa_es_tori_y_carga():
    e = registro.activa()
    assert e.nombre == "tori" and e.marcos.operativo == "H4"
```

`tests/test_tori_divergencia.py`:

```python
"""divergencia(): la pieza no sale si el texto quedó escrito para otra lectura (spec §4)."""
from __future__ import annotations

from dataclasses import replace

import test_tori_lectura as tl

from estrategia.tori.lectura import divergencia


def test_la_misma_lectura_no_diverge():
    lec = tl.leer(tl.vs.desde_vertices(tl.ALCISTA, 12))
    assert divergencia(lec, lec) is None


def test_una_prueba_que_ya_cerro_diverge():
    h4 = tl.vs.desde_vertices(tl.ALCISTA, 12)
    preparada = tl.leer(h4, tl._vela(h4, 90.0))
    actual = tl.leer(h4)
    assert preparada.estado == "PRUEBA"
    assert "cerró" in divergencia(preparada, actual)


def test_el_precio_que_cruza_la_referencia_diverge():
    lec = tl.leer(tl.vs.desde_vertices(tl.ALCISTA, 12))
    cruzada = replace(lec, precio=lec.invalidacion.precio - 10)
    assert divergencia(lec, cruzada) is not None


def test_pasar_de_tendencia_a_rebote_no_diverge():
    lec = tl.leer(tl.vs.desde_vertices(tl.ALCISTA, 12))
    assert divergencia(lec, replace(lec, estado="REBOTE")) is None
    assert divergencia(replace(lec, estado="REBOTE"), lec) is None


def test_un_cambio_de_direccion_diverge():
    lec = tl.leer(tl.vs.desde_vertices(tl.ALCISTA, 12))
    bajista = tl.leer(tl.vs.desde_vertices(tl.BAJISTA, 12))
    assert bajista.direccion == "BAJISTA"
    assert "dirección" in divergencia(lec, bajista)
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_estrategia_conformidad.py tests/test_estrategia_registro.py tests/test_tori_divergencia.py -v`
Expected: FAIL con `ImportError: cannot import name 'crear'` / `'divergencia'`.

- [ ] **Step 3: Implementar la procedencia de Tori**

`scripts/estrategia/tori/procedencia.py` (sale de la doctrina §7; F5 y F8 quedan fuera de
`empirico` porque están "verificada parcial", spec §4):

```python
"""Procedencia de Tori: la tabla de §7 de docs/metodologia-tendencias.md."""
from __future__ import annotations

from estrategia.contrato import Fundamento, Procedencia

DIAGONAL = "La parte diagonal no tiene evidencia académica propia (F11)."

PROCEDENCIA = Procedencia(
    fuente_doctrina="docs/metodologia-tendencias.md",
    fuente_citas="docs/investigacion/fundamentos/fuentes.md",
    fundamentos=(
        Fundamento("Solo precio y líneas, sin indicadores",
                   ("Tori Trades, lg0pb [07:27]", "Tori Trades, qLtq7 [13:25]"),
                   ("F3 p. 28",), ("F9",),
                   f"Que las líneas diagonales en sí predigan algo. {DIAGONAL}"),
        Fundamento("La línea se ancla en la mecha y ninguna vela la cruza",
                   ("Tori Trades, qLtq7 [04:00]", "Tori Trades, qLtq7 [01:33] (V10)"),
                   ("F3 p. 96", "F3 p. 117"), (),
                   "Es una convención de trazado; la tolerancia de toque es parámetro nuestro."),
        Fundamento("Con 3 toques y una semana de datos la línea es A+; con 2, setup menor",
                   ("Tori Trades, E6dUU [02:28]", "Tori Trades, xRxUo [00:52] (V4-V6)",
                    "Tori Trades, E6dUU [03:13] (V14)", "Tori Trades, xRxUo [05:28] (V16)"),
                   ("F3 p. 94",), (),
                   "Que una A+ rinda más que una de 2 toques; el umbral de Punto B reciente es nuestro."),
        Fundamento("Las líneas se encadenan y se abren en abanico cuando el precio acelera",
                   ("Tori Trades, ipUbs [05:14]", "Tori Trades, Y8efW [32:44]",
                    "Tori Trades, qsjLm [14:43] (V13)"),
                   ("F3 p. 104",), (),
                   "El principio abanico de Murphy (p. 101) son líneas más planas; el de Tori, más empinadas."),
        Fundamento("El contexto va de arriba hacia abajo y el marco operativo es 4H",
                   ("Tori Trades, ipUbs [02:53]", "Tori Trades, q4t71 [17:47] (V20)"),
                   ("F1 vía F3 pp. 51-52", "F3 pp. 105-106"), (),
                   "Que 4H sea el marco óptimo. La evidencia de momentum (F5) es mensual y está verificada solo en parte."),
        Fundamento("La ruptura se publica con el cierre de la vela del marco operativo",
                   ("Tori Trades, cTecm [07:19] (V3)", "Tori Trades, qLtq7 [51:00] (V1)"),
                   ("F1 vía F3 p. 56", "F3 p. 97"), (),
                   f"La ruptura de una diagonal. Esperar el cierre pierde parte del movimiento (F3 p. 57). F8 queda fuera hasta releerlo. {DIAGONAL}"),
        Fundamento("Se entra a favor de la ruptura y la línea opuesta es la de seguridad",
                   ("Tori Trades, E6dUU [05:32]", "Tori Trades, qLtq7 [12:00] (V18)"),
                   ("F3 p. 54", "F3 p. 29"), ("F6",),
                   "Que la ruptura de una línea sea el mejor disparador."),
        Fundamento("El stop va al otro lado de la línea de seguridad, con margen",
                   ("Tori Trades, E6dUU [05:58]", "Tori Trades, pasWN [14:48]"),
                   ("F3 p. 94",), (),
                   "El margen del stop es parámetro nuestro (doctrina 2.6)."),
        Fundamento("Se sale cuando una vela cierra al otro lado de la línea de seguridad",
                   ("Tori Trades, LpXZB [04:45]", "Tori Trades, Y_Ney [12:49] (V11)"),
                   ("F3 p. 94",), (),
                   "Que salir por la línea rinda más que salir en el horizontal (V11)."),
        Fundamento("En consolidación no se opera",
                   ("Tori Trades, E6dUU [02:52]", "Tori Trades, qLtq7 [41:13]"),
                   ("F3 p. 78", "F3 pp. 76-77"), ("F6",),
                   "Una definición numérica de consolidación: la nuestra es parámetro."),
        Fundamento("Los horizontales son objetivo, doble confirmación y borde del rango",
                   ("Tori Trades, qsjLm [10:30]", "Tori Trades, qsjLm [02:00] (V17)"),
                   ("F3 p. 85", "F3 p. 86"), ("F4",),
                   "Osler no examina si el precio sigue al romper el nivel: respalda el horizontal como objetivo."),
        Fundamento("Los umbrales numéricos del trazado y del puntaje",
                   ("Parámetros nuestros: scripts/estrategia/tori/parametros.py",),
                   ("F3 p. 103",), (),
                   "Ninguno de los umbrales viene de Tori; se fijaron mirando el universo real y no se midió su resultado."),
    ),
    modos_de_falla=(
        "Reversiones bruscas en varios mercados a la vez (F6).",
        "Periodos largos sin tendencia clara: el precio pasa en lateral cerca de un tercio del tiempo (F6, F3 pp. 76-77).",
        "Líneas muy empinadas que se cruzan sin que cambie la tendencia (F3 p. 103).",
        "Esperar el cierre de la vela pierde parte del movimiento (F3 p. 57).",
    ),
)
```

- [ ] **Step 4: Implementar `divergencia` en `lectura.py`**

```python
def divergencia(preparada: Lectura, actual: Lectura) -> str | None:
    """Motivo por el que el texto preparado ya no vale, o None (spec §4)."""
    if preparada.estado == "PRUEBA" and (
        actual.estado != "PRUEBA" or actual.en_prueba.cierre_vela != preparada.en_prueba.cierre_vela
    ):
        return "la vela que estaba en prueba ya cerró: el texto se escribió para una condición que se resolvió"
    if actual.direccion != preparada.direccion:
        return f"la dirección cambió de {preparada.direccion.lower()} a {actual.direccion.lower()}"
    # Entre TENDENCIA y REBOTE la estructura es la misma: el texto sigue valiendo (hueco 13).
    if actual.estado != preparada.estado and {actual.estado, preparada.estado} != {"TENDENCIA", "REBOTE"}:
        return f"el estado cambió de {preparada.estado.lower()} a {actual.estado.lower()}"
    for campo in ("vigilar", "invalidacion"):
        antes, ahora = getattr(preparada, campo), getattr(actual, campo)
        if antes is not None and ahora is not None and \
                (preparada.precio - antes.precio) * (actual.precio - ahora.precio) < 0:
            return f"el precio cruzó la {ahora.etiqueta}, que hoy está en {ahora.precio}"
    return None
```

Nota: `ahora.precio` es el valor de la línea **en la lectura actual**, así que una diagonal que se
movió se compara donde está hoy, no donde estaba al preparar (spec §4, "Por qué `valor_actual`").

- [ ] **Step 5: Implementar la clase `Tori`**

`scripts/estrategia/tori/__init__.py`:

```python
"""La estrategia de Tori Trades (doctrina: docs/metodologia-tendencias.md)."""
from __future__ import annotations

from estrategia.contrato import Etiqueta, Marcos
from estrategia.tori import lectura as _lectura
from estrategia.tori import puntaje as _puntaje
from estrategia.tori.parametros import PARAMETROS, Parametros
from estrategia.tori.procedencia import PROCEDENCIA

MARCOS = Marcos(
    contexto=("W1", "D1"), operativo="H4",
    velas={"W1": 156, "D1": 250, "H4": 180},
    etiquetas={
        "W1": Etiqueta("contexto", "de meses"),
        "D1": Etiqueta("posicional", "de semanas"),
        "H4": Etiqueta("swing", "de una a dos semanas"),
    },
)


class Tori:
    nombre = "tori"
    marcos = MARCOS
    procedencia = PROCEDENCIA

    def __init__(self, parametros: Parametros = PARAMETROS) -> None:
        self.p = parametros

    def leer(self, ticker, velas, digits, en_curso=None):
        return _lectura.leer(ticker, velas, digits, en_curso, self.marcos, self.p)

    def seguir(self, referencia, velas, digits, en_curso=None):
        return _lectura.seguir(referencia.ticker, referencia, velas, digits, en_curso,
                               self.marcos, self.p)  # lo implementa la Task S3-6

    def puntuar(self, lectura, horizonte):
        return _puntaje.puntuar(lectura, horizonte, self.p)

    def divergencia(self, preparada, actual):
        return _lectura.divergencia(preparada, actual)


def crear() -> Tori:
    return Tori()
```

Como `puntaje.py` llega en S3-5, crear ahora `scripts/estrategia/tori/puntaje.py` con un esqueleto
que la Task S3-5 reemplaza entero:

```python
"""El escáner de Tori: lo completa la Task S3-5."""
from __future__ import annotations

from estrategia.contrato import Lectura, Puntaje
from estrategia.tori.parametros import Parametros


def puntuar(lectura: Lectura, horizonte: str, p: Parametros) -> Puntaje:
    return Puntaje(0.0, {}, None)
```

- [ ] **Step 6: Correr los tests**

Run: `uv run pytest tests/test_estrategia_conformidad.py tests/test_estrategia_registro.py tests/test_tori_divergencia.py -v`
Expected: PASS. Si `verificar_procedencia` falla para Tori, el mensaje dice qué fundamento y qué
cita: corregir la cita contra `fuentes.md`, nunca agregar una fila nueva sin verificarla.

- [ ] **Step 7: Commit**

```bash
git add scripts/estrategia/tori/__init__.py scripts/estrategia/tori/procedencia.py scripts/estrategia/tori/puntaje.py scripts/estrategia/tori/lectura.py tests/test_estrategia_conformidad.py tests/test_estrategia_registro.py tests/test_tori_divergencia.py
git commit -m "feat(tori): estrategia enchufable con procedencia, divergencia y conformidad"
```

### Task S3-5: El puntaje por horizonte

**Files:**
- Modify: `scripts/estrategia/tori/puntaje.py` (reemplazo completo)
- Test: `tests/test_tori_puntaje.py`

**Interfaces:**
- Produces: `puntuar(lectura, horizonte, p) -> Puntaje`, `situacion(lectura, p) -> str` (una de
  `"ruptura"`, `"a_punto"`, `"tendencia"`, `"rango"`), `BANDAS`.

- [ ] **Step 1: Escribir el test que falla**

```python
"""El escáner de Tori ordena por situación y horizonte (spec §5)."""
from __future__ import annotations

import sys
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from estrategia.contrato import Escenario, Lectura, Linea, Prueba, Referencia  # noqa: E402
from estrategia.tori.parametros import PARAMETROS as P  # noqa: E402
from estrategia.tori.puntaje import CONTRA_SECUENCIA, puntuar, situacion  # noqa: E402

TRES = (Escenario("⬆️", "a", "a"), Escenario("↔️", "b", "b"), Escenario("⬇️", "c", "c"))


def _diag(rol, calidad="A+", toques=3, empinada=False, valor=100.0):
    return Linea(rol, "diagonal", ((1, 90.0), (2, 95.0)), "H4", toques, calidad, valor, empinada)


def _lectura(estado, lineas, metricas, prueba=None, direccion="ALCISTA"):
    ref = Referencia(100.0, "línea", lineas[0] if lineas else None)
    return Lectura("X", "H4", 101.0, direccion, estado, tuple(lineas), prueba, ref,
                   ref if lineas else None, None, TRES, "s", (), (), metricas)


RUPTURA = _lectura("RUPTURA", [_diag("accion"), _diag("seguridad")],
                   {"dist_seguridad_atr_d1": 0.5, "velas_desde_ruptura": 2.0})
A_PUNTO = _lectura("TENDENCIA", [_diag("accion"), _diag("seguridad")],
                   {"dist_accion_atr_d1": 0.4, "dist_seguridad_atr_d1": 1.5})
TENDENCIA = _lectura("TENDENCIA", [_diag("seguridad")], {"dist_seguridad_atr_d1": 1.5})
RANGO = _lectura("RANGO", [Linea("rango", "horizontal", ((1, 110.0),), "H4", 3, "", 110.0),
                           Linea("rango", "horizontal", ((1, 100.0),), "H4", 3, "", 100.0)],
                 {}, direccion="LATERAL")


def _orden(horizonte, *lecturas):
    return [situacion(l, P) for l in sorted(lecturas, key=lambda l: -puntuar(l, horizonte, P).puntos)]


def test_sesion_premia_la_ruptura_reciente():
    assert _orden("sesion", RANGO, TENDENCIA, A_PUNTO, RUPTURA) == ["ruptura", "a_punto", "tendencia", "rango"]


def test_semana_premia_la_linea_a_mas_cerca_y_sin_romper():
    assert _orden("semana", RANGO, TENDENCIA, RUPTURA, A_PUNTO) == ["a_punto", "ruptura", "tendencia", "rango"]


def test_los_adicionales_no_invierten_las_situaciones():
    cargada = replace(TENDENCIA, metricas={**TENDENCIA.metricas, "confluencia": 1.0,
                                           "doble_confirmacion": 1.0, "semanas_principal": 6.0})
    for h in ("sesion", "semana"):
        assert puntuar(cargada, h, P).puntos < puntuar(A_PUNTO, h, P).puntos


def test_lejos_de_la_seguridad_resta():
    lejos = replace(RUPTURA, metricas={**RUPTURA.metricas, "dist_seguridad_atr_d1": 3.0})
    assert puntuar(lejos, "sesion", P).puntos < puntuar(RUPTURA, "sesion", P).puntos
    assert puntuar(lejos, "sesion", P).desglose["lejos_de_seguridad"] < 0


def test_una_linea_empinada_o_de_dos_toques_no_es_principal():
    empinada = replace(RUPTURA, lineas=(_diag("accion", empinada=True), _diag("seguridad")))
    b = replace(RUPTURA, lineas=(_diag("accion", calidad="B", toques=2), _diag("seguridad")))
    assert situacion(empinada, P) != "ruptura" and situacion(b, P) != "ruptura"


def test_en_semana_una_a_mas_en_prueba_espera_el_cierre():
    cierre = datetime(2026, 10, 9, 13, 0, tzinfo=ZoneInfo("America/Santiago"))
    prueba = _lectura("PRUEBA", [_diag("seguridad")], {"dist_seguridad_atr_d1": 0.2},
                      prueba=Prueba(_diag("seguridad"), 100.0, cierre))
    assert puntuar(prueba, "semana", P).excluido is not None
    assert puntuar(prueba, "sesion", P).excluido is None


def test_sin_estructura_se_excluye():
    vacia = replace(RANGO, lineas=(Linea("rango", "horizontal", ((1, 110.0),), "H4", 1, "", 110.0),
                                   Linea("rango", "horizontal", ((1, 100.0),), "H4", 1, "", 100.0)))
    for h in ("sesion", "semana"):
        assert puntuar(vacia, h, P).excluido == "sin líneas trazables: no hay estructura que leer"


def test_el_rango_no_se_excluye_en_sesion():
    assert puntuar(RANGO, "sesion", P).excluido is None


def test_sin_linea_de_seguridad_la_ruptura_no_es_setup():
    assert situacion(replace(RUPTURA, lineas=(_diag("accion"),)), P) != "ruptura"


def test_contra_la_secuencia_mayor_se_excluye():
    contra = replace(RUPTURA, metricas={**RUPTURA.metricas, "contra_secuencia": 1.0})
    for h in ("sesion", "semana"):
        assert puntuar(contra, h, P).excluido == CONTRA_SECUENCIA


def test_el_rebote_en_la_seguridad_a_mas_es_a_punto():
    assert situacion(replace(TENDENCIA, estado="REBOTE"), P) == "a_punto"


def test_el_rebote_en_una_seguridad_b_es_tendencia():
    b = replace(TENDENCIA, estado="REBOTE", lineas=(_diag("seguridad", calidad="B", toques=2),))
    assert situacion(b, P) == "tendencia"
```

- [ ] **Step 2: Verificar que falla**

Run: `uv run pytest tests/test_tori_puntaje.py -v`
Expected: FAIL con `ImportError: cannot import name 'situacion'`.

- [ ] **Step 3: Implementar**

```python
"""El escáner de Tori (spec §5): situación por horizonte, adicionales y exclusiones.

Cada situación tiene una banda de 25 puntos y lo que suma dentro de ella tiene
tope `tope_adicionales` (24), así el orden de situaciones del spec no se invierte
por los adicionales. Solo la resta por precio lejos de la seguridad baja de banda.
Nada macro: la agenda no mueve el ranking (spec §8.2).
"""
from __future__ import annotations

from estrategia.contrato import Lectura, Linea, Puntaje
from estrategia.tori.parametros import Parametros

BANDAS = {
    "sesion": {"ruptura": 75.0, "a_punto": 50.0, "tendencia": 25.0, "rango": 0.0},
    "semana": {"a_punto": 75.0, "ruptura": 50.0, "tendencia": 25.0, "rango": 0.0},
}
SIN_ESTRUCTURA = "sin líneas trazables: no hay estructura que leer"
PRUEBA_SEMANAL = "una línea A+ está en prueba: el análisis semanal espera el cierre de la vela"
CONTRA_SECUENCIA = "va contra la secuencia de los marcos mayores: es donde nacen las falsas rupturas"


def _rol(lectura: Lectura, rol: str) -> Linea | None:
    return next((x for x in lectura.lineas if x.rol == rol and x.marco == lectura.marco), None)


def _principal(x: Linea | None) -> bool:
    """Una línea puntúa como principal si es A+ y no es muy empinada (doctrina 2.2)."""
    return x is not None and x.calidad == "A+" and not x.empinada


def situacion(lectura: Lectura, p: Parametros) -> str:
    m = lectura.metricas
    accion, seguridad = _rol(lectura, "accion"), _rol(lectura, "seguridad")
    cerca = lambda clave: m.get(clave, float("inf")) <= p.cerca_atr_d1  # noqa: E731
    if lectura.estado == "PRUEBA":
        # Solo es setup si la otra línea existe: será la de seguridad tras la ruptura (V18).
        otra = seguridad if lectura.en_prueba.linea.rol == "accion" else accion
        return "ruptura" if _principal(lectura.en_prueba.linea) and otra is not None else "tendencia"
    if lectura.estado == "RUPTURA":
        # Sin línea de seguridad trazada no hay setup de Tori (V18), y lejos de ella el riesgo
        # es alto y se pasa (doctrina 2.5): la frescura de la ruptura es esta distancia.
        es_setup = _principal(accion) and seguridad is not None and cerca("dist_seguridad_atr_d1")
        return "ruptura" if es_setup else "tendencia"
    if lectura.estado == "REBOTE":
        # El rebote es setup si la línea que lo sostuvo es A+ (doctrina 2.5, V7).
        return "a_punto" if _principal(seguridad) else "tendencia"
    if lectura.estado == "TENDENCIA":
        if (_principal(accion) and cerca("dist_accion_atr_d1")) or \
                (_principal(seguridad) and cerca("dist_seguridad_atr_d1")):
            return "a_punto"
        return "tendencia"
    return "rango"


def _sin_estructura(lectura: Lectura) -> bool:
    diagonales = [x for x in lectura.lineas if x.tipo == "diagonal" and x.marco == lectura.marco]
    bordes = [x for x in lectura.lineas if x.rol == "rango" and x.toques >= 2]
    return not diagonales and not bordes


def puntuar(lectura: Lectura, horizonte: str, p: Parametros) -> Puntaje:
    if _sin_estructura(lectura):
        return Puntaje(0.0, {}, SIN_ESTRUCTURA)
    if horizonte == "semana" and lectura.estado == "PRUEBA" and lectura.en_prueba.linea.calidad == "A+":
        return Puntaje(0.0, {}, PRUEBA_SEMANAL)
    if lectura.metricas.get("contra_secuencia", 0.0) == 1.0:
        return Puntaje(0.0, {}, CONTRA_SECUENCIA)  # ipUbs [00:36], [01:11]; director, 2026-10-10
    m = lectura.metricas
    sit = situacion(lectura, p)
    base = BANDAS[horizonte][sit]
    principal = _rol(lectura, "accion") if sit == "ruptura" else _rol(lectura, "seguridad")
    suma: dict[str, float] = {}
    if principal is not None and principal.toques >= 4:
        suma["calidad_toques"] = 5.0
    if m.get("semanas_principal", 0.0) >= 3.0:
        suma["calidad_semanas"] = 5.0
    suma["confluencia"] = m.get("confluencia", 0.0) * (10.0 if horizonte == "semana" else 5.0)
    suma["doble_confirmacion"] = 5.0 * m.get("doble_confirmacion", 0.0)
    seg, obj = m.get("dist_seguridad_atr_d1"), m.get("dist_objetivo_atr_d1")
    if seg is not None and obj is not None and obj >= 2.0 * seg:
        suma["espacio"] = 5.0
    adicionales = min(sum(suma.values()), p.tope_adicionales)
    restas: dict[str, float] = {}
    if seg is not None and seg > p.lejos_atr_d1:
        restas["lejos_de_seguridad"] = -30.0  # Tori pasa esa operación (doctrina 2.5)
    puntos = max(0.0, min(100.0, base + adicionales + sum(restas.values())))
    return Puntaje(puntos, {"base": base, **suma, "adicionales": adicionales, **restas}, None)
```

- [ ] **Step 4: Correr los tests y la suite**

Run: `uv run pytest tests/test_tori_puntaje.py -v && uv run pytest`
Expected: PASS y suite verde (la conformidad de Tori ahora puntúa de verdad).

- [ ] **Step 5: Commit**

```bash
git add scripts/estrategia/tori/puntaje.py tests/test_tori_puntaje.py
git commit -m "feat(tori): escáner por horizonte con bandas por situación"
```

### Task S3-6: La referencia semanal: `seguir()` de Tori

**Files:**
- Modify: `scripts/estrategia/tori/lectura.py` (agregar `_valorador` y `seguir`; `replace` al import de dataclasses)
- Modify: `tests/test_estrategia_conformidad.py` (`CON_SEGUIR = {"juguete", "tori"}`)
- Test: `tests/test_tori_seguir.py`

**Interfaces:**
- Consumes: `_prueba`, `_vigilar`, `serie_de`, `textos` (S3-1 a S3-3), `Tori.seguir` (S3-4).
- Produces: `lectura.seguir(ticker, referencia, velas, digits, en_curso, marcos, p) -> Lectura`.

- [ ] **Step 1: Escribir el test que falla**

```python
"""seguir(): la lectura de hoy contra la referencia del lunes (spec §4, "La referencia semanal")."""
from __future__ import annotations

import pandas as pd
import pytest

import test_tori_lectura as tl

from estrategia.tori.lectura import seguir as _seguir
from estrategia.tori.parametros import PARAMETROS as P

LUNES = tl.vs.desde_vertices(tl.ALCISTA, 12)


def seguir(ref, h4, en_curso=None):
    return _seguir("XAUUSD", ref, tl.velas(h4), 2, en_curso, tl.MARCOS, P)


def extender(h4, vertices, n=6):
    nuevas = tl.vs.desde_vertices(vertices, n, t0=int(h4["time"].iloc[-1]) + 4 * 3600)
    return pd.concat([h4, nuevas], ignore_index=True)


def _rol(lectura, rol):
    return next(x for x in lectura.lineas if x.rol == rol)


def test_con_las_mismas_velas_la_lectura_no_cambia():
    ref = tl.leer(LUNES)
    hoy = seguir(ref, LUNES)
    assert (hoy.estado, hoy.direccion) == (ref.estado, ref.direccion)
    assert [x.valor_actual for x in hoy.lineas] == [x.valor_actual for x in ref.lineas]


def test_las_anclas_no_se_mueven_y_la_diagonal_avanza_por_su_pendiente():
    ref = tl.leer(LUNES)
    h4 = extender(LUNES, [119, 124, 122])  # doce velas que siguen sobre la línea alcista
    hoy = seguir(ref, h4)
    assert _rol(hoy, "seguridad").puntos == _rol(ref, "seguridad").puntos
    assert abs(_rol(hoy, "seguridad").valor_actual - (_rol(ref, "seguridad").valor_actual + 0.25 * 12)) < 0.01
    assert hoy.estado == "TENDENCIA" and hoy.vela == int(h4["time"].iloc[-1])


def test_un_cierre_al_otro_lado_de_la_linea_del_lunes_es_ruptura():
    ref = tl.leer(LUNES)
    hoy = seguir(ref, extender(LUNES, [119, 100]))
    assert (hoy.estado, hoy.direccion) == ("RUPTURA", "BAJISTA")
    assert _rol(hoy, "accion").puntos == _rol(ref, "seguridad").puntos
    assert hoy.objetivo is None  # el objetivo del lunes era para la otra dirección
    assert any("nueva referencia" in a for a in hoy.avisos)


def test_la_vela_en_curso_contra_la_linea_del_lunes_es_prueba():
    ref = tl.leer(LUNES)
    h4 = extender(LUNES, [119, 124, 122])
    hoy = seguir(ref, h4, tl._vela(h4, 100.0))
    assert hoy.estado == "PRUEBA" and hoy.en_prueba.linea.rol == "seguridad"


def test_tocar_la_linea_del_lunes_y_cerrar_a_favor_es_rebote():
    ref = tl.leer(LUNES)
    # En la vela 83 la línea del lunes vale 120,55: la mecha baja a 120,65 y cierra en 120,85.
    hoy = seguir(ref, extender(LUNES, [119, 124, 120.85]))
    assert (hoy.estado, hoy.direccion) == ("REBOTE", "ALCISTA")
    assert _rol(hoy, "seguridad").puntos == _rol(ref, "seguridad").puntos


def test_una_referencia_que_ya_no_cabe_falla_con_mensaje():
    ref = tl.leer(LUNES)
    with pytest.raises(ValueError, match="ventana"):
        seguir(ref, LUNES.iloc[5:].reset_index(drop=True))


def test_una_referencia_en_prueba_no_se_sigue():
    ref = tl.leer(LUNES, tl._vela(LUNES, 90.0))
    with pytest.raises(ValueError, match="PRUEBA"):
        seguir(ref, LUNES)
```

- [ ] **Step 2: Verificar que falla**

Run: `uv run pytest tests/test_tori_seguir.py -v`
Expected: FAIL con `ImportError: cannot import name 'seguir'`.

- [ ] **Step 3: Implementar en `lectura.py`**

Cambiar el import a `from dataclasses import dataclass, replace` y agregar al final del módulo:

```python
def _valorador(velas: dict[str, pd.DataFrame], marcos: Marcos, ticker: str):
    """Valor de una línea fija en cualquier vela de su marco, contado en velas desde sus anclas.

    Usa todas las velas recibidas y no la ventana de `leer()`: las anclas del lunes tienen
    que seguir dentro aunque la ventana haya avanzado.
    """
    indices = {m: {int(ts): i for i, ts in enumerate(velas[m]["time"])} for m in marcos.todos}

    def valor(linea: Linea, i: float) -> float:
        if linea.tipo == "horizontal":
            return linea.puntos[0][1]
        (t1, p1), (t2, p2) = linea.puntos
        try:
            i1, i2 = indices[linea.marco][t1], indices[linea.marco][t2]
        except KeyError:
            raise ValueError(
                f"{ticker}: las anclas de una línea {linea.rol} de {linea.marco} ya no caben en la "
                "ventana de velas; hay que pedir velas desde la referencia"
            ) from None
        return p1 + (p2 - p1) / (i2 - i1) * (i - i1)

    return valor, indices


def seguir(ticker: str, referencia: Lectura, velas: dict[str, pd.DataFrame], digits: int,
           en_curso: VelaEnCurso | None, marcos: Marcos, p: Parametros) -> Lectura:
    """La lectura de hoy contra la referencia del lunes, sin volver a trazar (spec §4).

    Las anclas no se mueven: una diagonal avanza por su pendiente y un horizontal vale lo
    mismo toda la semana. Una línea que cerró al otro lado por más que la tolerancia deja el
    estado en RUPTURA; el consumidor reemplaza entonces la referencia por la `leer()` de ese
    cierre (decisión del director, 2026-10-10).
    """
    exigir_velas(velas, marcos)
    if referencia.estado == "PRUEBA":
        raise ValueError(f"{ticker}: una referencia no puede quedar en PRUEBA; se guarda con la vela cerrada")
    op = marcos.operativo
    s = serie_de(velas[op].reset_index(drop=True))
    if s.atr <= 0:
        raise ValueError(f"{ticker}: las velas de {op} no tienen rango (ATR 0); no hay nada que leer")
    valor, indices = _valorador(velas, marcos, ticker)
    if referencia.vela not in indices[op]:
        raise ValueError(f"{ticker}: la vela de la referencia ya no cabe en la ventana de {op}")
    i_ref = indices[op][referencia.vela]
    ultimo = len(s) - 1
    tol = p.tolerancia_toque_atr * s.atr
    lineas = [replace(x, valor_actual=round(valor(x, len(indices[x.marco]) - 1), digits))
              for x in referencia.lineas]

    def sostiene(x: Linea) -> bool:
        return x.marco == op and x.rol in ("accion", "seguridad", "rango")

    ruptura: tuple[int, Linea] | None = None
    for x in lineas:
        if not sostiene(x):
            continue
        lado = s.closes[i_ref] - valor(x, i_ref)
        for i in range(i_ref + 1, len(s)):
            ahora = s.closes[i] - valor(x, i)
            if lado * ahora < 0 and abs(ahora) > tol:
                if ruptura is None or i < ruptura[0]:
                    ruptura = (i, x)
                break

    # El rebote se vuelve a medir con la última vela de hoy: dura una vela (hueco 13).
    estado = "TENDENCIA" if referencia.estado == "REBOTE" else referencia.estado
    direccion = referencia.direccion
    avisos = list(referencia.avisos)
    objetivo = referencia.objetivo
    if ruptura is not None:
        i, rota = ruptura
        estado = "RUPTURA"
        direccion = "ALCISTA" if s.closes[i] > valor(rota, i) else "BAJISTA"
        if direccion != referencia.direccion:
            objetivo = None  # el objetivo del lunes era para la otra dirección
        sube = direccion == "ALCISTA"
        nuevas = []
        for x in lineas:
            if x is rota:
                nuevas.append(replace(x, rol="accion"))
            elif sostiene(x) and x.tipo == "diagonal":
                # La opuesta queda a favor de la operación: bajo el precio en una compra (V18).
                a_favor = x.valor_actual < s.closes[ultimo] if sube else x.valor_actual > s.closes[ultimo]
                nuevas.append(replace(x, rol="seguridad" if a_favor else "contexto"))
            else:
                nuevas.append(x)
        lineas = nuevas
        avisos.append(f"la línea {textos.sentido(rota)} del análisis semanal se rompió por cierre: "
                      "la lectura de este cierre pasa a ser la nueva referencia")

    accion = next((x for x in lineas if x.rol == "accion" and x.marco == op), None)
    seguridad = next((x for x in lineas if x.rol == "seguridad" and x.marco == op), None)
    rango = [x for x in lineas if x.rol == "rango"]
    linea_seguimiento = next((x for x in lineas if x.rol == "seguimiento"), None)
    cierre = s.closes[-1]
    precio = en_curso.precio if en_curso is not None else cierre
    if estado == "TENDENCIA" and seguridad is not None and \
            _rebote(s, valor(seguridad, ultimo), textos.sentido(seguridad), tol):
        estado = "REBOTE"
    vivas = [(x, valor(x, len(s))) for x in lineas
             if sostiene(x) and not (estado == "RUPTURA" and x.rol == "accion")]
    prueba = _prueba(vivas, cierre, en_curso, tol, digits)
    vigilar = _vigilar(prueba, estado, accion, seguridad, rango, precio)
    invalidacion = (Referencia(seguridad.valor_actual, f"línea {textos.sentido(seguridad)} de seguridad", seguridad)
                    if seguridad is not None else None)

    atr_d1 = serie_de(velas["D1"]).atr if "D1" in marcos.todos else 0.0
    atr_d1 = atr_d1 if atr_d1 > 0 else s.atr
    fijas = ("confluencia", "contra_secuencia", "doble_confirmacion", "semanas_principal")
    metricas = {k: v for k, v in referencia.metricas.items() if k in fijas}
    metricas.update({"atr": s.atr, "atr_d1": atr_d1,
                     "dist_vigilar_atr_d1": abs(precio - vigilar.precio) / atr_d1})
    if seguridad is not None:
        metricas["dist_seguridad_atr_d1"] = abs(precio - seguridad.valor_actual) / atr_d1
    if accion is not None:
        metricas["dist_accion_atr_d1"] = abs(precio - accion.valor_actual) / atr_d1
    if objetivo is not None:
        metricas["dist_objetivo_atr_d1"] = abs(precio - objetivo.precio) / atr_d1
    if ruptura is not None:
        metricas["velas_desde_ruptura"] = float(ultimo - ruptura[0])

    final = "PRUEBA" if prueba is not None else estado
    return Lectura(
        ticker=ticker, marco=op, precio=precio, direccion=direccion, estado=final,
        lineas=tuple(lineas), en_prueba=prueba, vigilar=vigilar, invalidacion=invalidacion,
        objetivo=objetivo,
        escenarios=textos.escenarios(final, direccion, op, digits, precio, vigilar, invalidacion,
                                     objetivo, prueba, rango),
        salida=textos.salida(final, op, invalidacion, digits, linea_seguimiento),
        conceptos=textos.conceptos(final), avisos=tuple(avisos), metricas=metricas,
        vela=s.times[-1],
    )
```

En `tests/test_estrategia_conformidad.py`: `CON_SEGUIR = {"juguete", "tori"}`.

- [ ] **Step 4: Correr los tests y la suite**

Run: `uv run pytest tests/test_tori_seguir.py tests/test_estrategia_conformidad.py -v && uv run pytest`
Expected: PASS y suite verde. Si `verificar_seguir_misma_lectura` falla para Tori por el estado,
revisar que `seguir()` no encuentre una "ruptura" con las mismas velas: el bucle arranca en
`i_ref + 1`, así que sin velas nuevas no hay nada que recorrer.

- [ ] **Step 5: Commit**

```bash
git add scripts/estrategia/tori/lectura.py tests/test_tori_seguir.py tests/test_estrategia_conformidad.py
git commit -m "feat(tori): seguir() mide las velas de hoy contra la referencia del lunes"
```

### Task S3-7: Velas de MT5, PNG de revisión y medición del universo

**Files:**
- Create: `scripts/estrategia/fuente.py`
- Create: `scripts/tori_revision.py`
- Modify: `.gitignore` (agregar `data/charts/tori/`)
- Test: `tests/test_estrategia_fuente.py`

**Interfaces:**
- Produces: `offset_servidor(tick_servidor, ahora_utc) -> int`, `separar_vela_abierta(df, marco,
  ahora_servidor) -> tuple[DataFrame, Series | None]`, `cierre_santiago(apertura, marco, offset)
  -> datetime`, `velas_mt5(ticker, marcos, extra=0) -> tuple[dict[str, DataFrame], VelaEnCurso |
  None]`. Esta es la función que el escáner y el carrusel usarán en S4; para `seguir()` se llama
  con `extra=60` (dos semanas de 4H), así las anclas del lunes quedan dentro.

- [ ] **Step 1: Escribir el test que falla**

```python
"""Infraestructura de velas: vela abierta y hora de cierre en Chile."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from estrategia.fuente import cierre_santiago, offset_servidor, separar_vela_abierta  # noqa: E402

H4 = 4 * 3600


def _ts(*args) -> int:
    return int(datetime(*args, tzinfo=timezone.utc).timestamp())


def test_offset_del_servidor_en_la_grilla_de_media_hora():
    assert offset_servidor(_ts(2026, 10, 9, 15, 2), _ts(2026, 10, 9, 12, 0)) == 3 * 3600


def test_la_ultima_vela_esta_abierta_si_no_termino_su_duracion():
    df = pd.DataFrame({"time": [0, H4, 2 * H4], "open": [1] * 3, "high": [1] * 3, "low": [1] * 3,
                       "close": [1] * 3})
    cerradas, abierta = separar_vela_abierta(df, "H4", ahora_servidor=2 * H4 + 60)
    assert len(cerradas) == 2 and int(abierta["time"]) == 2 * H4
    cerradas, abierta = separar_vela_abierta(df, "H4", ahora_servidor=3 * H4)
    assert len(cerradas) == 3 and abierta is None


def test_la_hora_de_cierre_respeta_el_cambio_de_horario_de_chile():
    # Servidor en UTC+3. Vela de 4H que abre 12:00 del servidor = 09:00 UTC y cierra 13:00 UTC.
    antes = cierre_santiago(_ts(2026, 9, 5, 12, 0), "H4", 3 * 3600)  # Chile en UTC-4
    despues = cierre_santiago(_ts(2026, 9, 7, 12, 0), "H4", 3 * 3600)  # Chile en UTC-3
    assert antes.strftime("%H:%M") == "09:00"
    assert despues.strftime("%H:%M") == "10:00"
```

- [ ] **Step 2: Verificar que falla**

Run: `uv run pytest tests/test_estrategia_fuente.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'estrategia.fuente'`.

- [ ] **Step 3: Implementar `fuente.py`**

```python
"""Infraestructura: las velas de MT5 que pide la estrategia activa (spec §3, lado derecho).

MT5 entrega las marcas en hora del SERVIDOR empaquetadas como epoch (CLAUDE.md).
Las velas se pasan a la estrategia en esa misma época, porque ella solo mide
diferencias. Lo único que se convierte es la hora de cierre de la vela abierta,
que la pieza le dice al cliente en hora de Chile.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pandas as pd

from estrategia.contrato import COLUMNAS_VELAS, Marcos, VelaEnCurso

SANTIAGO = ZoneInfo("America/Santiago")
DURACION = {"H1": 3600, "H4": 4 * 3600, "D1": 86400, "W1": 7 * 86400}
RELOJ = "BTCUSD"  # cotiza todos los días: su último tick es la hora del servidor
COTIZANDO_S = 15 * 60


def offset_servidor(tick_servidor: int, ahora_utc: float) -> int:
    """Segundos que el servidor va adelante de UTC, en la grilla de media hora."""
    return round((tick_servidor - ahora_utc) / 1800) * 1800


def separar_vela_abierta(df: pd.DataFrame, marco: str,
                         ahora_servidor: int) -> tuple[pd.DataFrame, pd.Series | None]:
    ultima = df.iloc[-1]
    if int(ultima["time"]) + DURACION[marco] > ahora_servidor:
        return df.iloc[:-1].reset_index(drop=True), ultima
    return df.reset_index(drop=True), None


def cierre_santiago(apertura_servidor: int, marco: str, offset: int) -> datetime:
    utc = apertura_servidor + DURACION[marco] - offset
    return datetime.fromtimestamp(utc, tz=timezone.utc).astimezone(SANTIAGO)


def _epoch(columna: pd.Series) -> pd.Series:
    """`get_rates` convierte `time` a datetime; acá vuelve a segundos."""
    return (columna - pd.Timestamp("1970-01-01")) // pd.Timedelta(seconds=1)


def velas_mt5(ticker: str, marcos: Marcos,
              extra: int = 0) -> tuple[dict[str, pd.DataFrame], VelaEnCurso | None]:
    """Velas cerradas por marco y la vela en curso del operativo, si el mercado cotiza.

    `extra` pide velas de más para `seguir()`: las anclas de la referencia del lunes tienen que
    quedar dentro aunque la ventana de `leer()` haya avanzado.
    """
    import MetaTrader5 as mt5

    from market_data_mcp import mt5_client

    mt5_client.connect()
    ahora = time.time()
    tick = mt5.symbol_info_tick(ticker)
    reloj = mt5.symbol_info_tick(RELOJ) or tick
    if reloj is None:
        raise RuntimeError(f"MT5 no entregó cotización de {RELOJ} ni de {ticker}: no hay reloj del servidor")
    offset = offset_servidor(int(reloj.time), ahora)
    ahora_servidor = int(ahora) + offset
    cotizando = tick is not None and ahora_servidor - int(tick.time) < COTIZANDO_S
    velas: dict[str, pd.DataFrame] = {}
    en_curso: VelaEnCurso | None = None
    for marco in marcos.todos:
        n = marcos.velas[marco] + extra
        df = mt5_client.get_rates(ticker, marco, n + 1)[list(COLUMNAS_VELAS)].copy()
        df["time"] = _epoch(df["time"]).astype("int64")
        if not cotizando:
            velas[marco] = df.tail(n).reset_index(drop=True)
            continue
        cerradas, abierta = separar_vela_abierta(df, marco, ahora_servidor)
        velas[marco] = cerradas.tail(n).reset_index(drop=True)
        if marco == marcos.operativo and abierta is not None:
            en_curso = VelaEnCurso(int(abierta["time"]), float(abierta["close"]),
                                   cierre_santiago(int(abierta["time"]), marco, offset))
    return velas, en_curso
```

- [ ] **Step 4: Correr los tests de fuente**

Run: `uv run pytest tests/test_estrategia_fuente.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Escribir `scripts/tori_revision.py`**

```python
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


def _panel(ax, df, lineas, titulo):
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
    ax.legend(loc="upper left", fontsize=7)


def dibujar(destino: Path, lectura, velas, marcos) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    op = marcos.operativo
    fig, (ax_op, ax_d1) = plt.subplots(2, 1, figsize=(16, 11), gridspec_kw={"height_ratios": (3, 2)})
    _panel(ax_op, velas[op], [x for x in lectura.lineas if x.marco == op],
           f"{lectura.ticker} {op} · {lectura.estado} · {lectura.direccion} · vigilar {lectura.vigilar.precio}")
    _panel(ax_d1, velas["D1"].tail(120).reset_index(drop=True),
           [x for x in lectura.lineas if x.marco == "D1"], f"{lectura.ticker} D1 · contexto")
    fig.tight_layout()
    fig.savefig(destino, dpi=110)
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    from market_data_mcp.catalog import VALID_TICKERS
    from pipeline_informe import ACTIVOS_INFORME

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tickers", nargs="*", default=list(ACTIVOS_INFORME))
    args = ap.parse_args(argv)

    estrategia = registro.activa()
    sello = datetime.now(ZoneInfo("America/Santiago")).strftime("%Y-%m-%d_%H-%M")
    carpeta = RAIZ / "data" / "charts" / "tori" / sello
    carpeta.mkdir(parents=True, exist_ok=True)
    resumen = []
    for ticker in args.tickers:
        velas, en_curso = velas_mt5(ticker, estrategia.marcos)
        lectura = estrategia.leer(ticker, velas, VALID_TICKERS.get(ticker, 2), en_curso)
        sesion, semana = estrategia.puntuar(lectura, "sesion"), estrategia.puntuar(lectura, "semana")
        dibujar(carpeta / f"{_slug(ticker)}.png", lectura, velas, estrategia.marcos)
        resumen.append({
            "ticker": ticker, "estado": lectura.estado, "direccion": lectura.direccion,
            "precio": lectura.precio, "vigilar": lectura.vigilar.precio,
            "invalidacion": lectura.invalidacion.precio if lectura.invalidacion else None,
            "objetivo": lectura.objetivo.precio if lectura.objetivo else None,
            "metricas": lectura.metricas, "avisos": list(lectura.avisos),
            "sesion": {"puntos": sesion.puntos, "excluido": sesion.excluido, "desglose": sesion.desglose},
            "semana": {"puntos": semana.puntos, "excluido": semana.excluido, "desglose": semana.desglose},
            "escenarios": [f"{e.flecha} {e.texto}" for e in lectura.escenarios],
        })
        print(f"{ticker:12} {lectura.estado:9} {lectura.direccion:8} "
              f"sesion={sesion.puntos:5.1f} semana={semana.puntos:5.1f} "
              f"dist_seg={lectura.metricas.get('dist_seguridad_atr_d1', float('nan')):.2f}")
    (carpeta / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"PNG y resumen en {carpeta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Agregar a `.gitignore`, junto a `data/charts/*.png`:

```
data/charts/tori/
```

- [ ] **Step 6: Correrlo contra MT5 real**

Run: `uv run --extra informe --with MetaTrader5 python scripts/tori_revision.py`
Expected: una línea por activo de los 5 base y `PNG y resumen en data/charts/tori/<sello>`.
Abrir cada PNG con Read y verificar que las líneas se dibujan sobre las velas, que ninguna
diagonal cruza velas antes de su ruptura y que el título coincide con el `resumen.json`. Si MT5 no
responde o la cuenta no es la declarada en `config/cuenta_mt5.json`, parar y avisar: no se
inventan velas.

- [ ] **Step 7: Medición del universo**

Correr también sobre los activos cubiertos de Forex y Commodities:
`uv run --extra informe --with MetaTrader5 python scripts/tori_revision.py --tickers <los tickers con rotacion en config/activos.json de esos dos canales>`.
Con los dos `resumen.json`, armar para el director una tabla: cuántos activos caen en cada
situación por horizonte, la distribución de `dist_seguridad_atr_d1` y `dist_accion_atr_d1`, y
cuántos quedan "cerca" con el umbral de 1 ATR diario. **No se cambian umbrales en esta tarea**:
la tabla va al gate.

- [ ] **Step 8: Suite completa y commit**

Run: `uv run pytest`
Expected: verde.

```bash
git add scripts/estrategia/fuente.py scripts/tori_revision.py tests/test_estrategia_fuente.py .gitignore
git commit -m "feat(tori): velas de MT5 con vela en curso y PNG de revisión para el gate"
```

### Task S3-8: Cierre de la fase 1 y gate del director

- [ ] **Step 1:** Push y PR ("feat(tori): lectura, puntaje y textos (enchufe S3)"). En el cuerpo:
  la tabla de la medición del universo, la ruta de los PNG (no se versionan) y la pregunta del
  gate: ¿las líneas se parecen a las que trazaría Tori?
- [ ] **Step 2:** Memoria (OMEGA y `project_enchufe_estrategia_tori.md`): fase 1 completa,
  esperando el gate; anotar los umbrales vigentes y la medición.
- [ ] **Step 3:** Mostrar al director los PNG y la tabla. Si corrige el trazado, se vuelve a S2
  con las correcciones anotadas. Si aprueba, la siguiente sesión escribe el plan de la fase 2.
