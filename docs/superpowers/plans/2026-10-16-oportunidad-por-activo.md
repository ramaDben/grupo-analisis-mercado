# `/oportunidad <activo>` por activo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que `/oportunidad <activo>` entregue un análisis profundo de un solo activo del terminal MT5 (técnico de la estrategia, fundamental, voces de bancos con fuente verificada), guardado a nombre de quien lo generó, reutilizable 7 días y que invite al cliente a revisar la plataforma MT5, nunca a operar.

**Architecture:** La pieza sigue siendo un `pieza.json` sellado con huella (`esquema.py`) con `datos.activos` de largo 1, así que la ficha HTML, la lámina y el seguimiento reutilizan su estructura. El registro pasa a una entrada por activo con vigencia de 7 días y caducidad anticipada si la lectura se rompe. agy solo redacta (ahora también `editorial.fuentes[]` con búsqueda web); Python valida entidad, medio, frescura y URL, calcula la discrepancia contra nuestra lectura y escribe el bloque fijo que invita a revisar MT5.

**Tech Stack:** Python 3 (paquete `scripts/analista/`), pytest vía `uv run`, MetaTrader5 (lectura), `requests` (verificar URLs), agy (`agy_encargo.invocar`), plantillas HTML en `templates/oportunidad/`.

**Spec:** `docs/superpowers/specs/2026-10-16-oportunidad-por-activo-design.md` (aprobado por el director el 2026-10-16). Los ejecutores leen spec y plan.

## Global Constraints

- **Regla 1:** ninguna cifra se escribe a mano. El validador rechaza números con decimales o de 3+ dígitos que no estén en `datos`. Única excepción: cifra de tercero que aparece en la `tesis` de una fuente validada y se atribuye a ella en la misma frase.
- **Texto de cliente** (HTML, correo, WhatsApp, lámina, textos fijos nuevos): español de Chile con tuteo, sin voseo, **sin `—` ni `–`**, "soporte/resistencia" (nunca piso/techo/suelo), sin la palabra "oportunidad" ni "recomendación".
- **Regulación (decisión del director, 2026-10-16):** ninguna pieza de `/oportunidad` invita a operar. Invita a revisar la plataforma MT5 con el cliente. Prohibido en texto de agy: "opera", "operar", "operarlo", "operable", "compra", "vende", "entra", "aprovecha".
- **Vigencia:** 7 días corridos desde la creación (`vence = creada + 7 d`), no la semana ISO.
- **El bot nunca toca el envío a WhatsApp:** ningún archivo de `scripts/analista/` puede contener `enviar_whatsapp`, `whatsapp_sender`, `--despachar`, `despachar(`, `bitacora_despachos`, `historial_despachos` (lo impone `tests/test_analista_bot.py::test_el_bot_no_puede_publicar_en_whatsapp`).
- **Ramas:** nunca commitear a master. Rama de este trabajo: `feat/oportunidad-por-activo`. Cada commit termina con `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- **Escritura de archivos con acentos** por Write o Python (`encoding="utf-8"`), nunca `Set-Content`/pipelines de PowerShell.
- **Panel de simulación:** se mantiene y se rotula «Ejemplo ilustrativo para revisar en MT5».
- **Timeout de agy:** provisional 12 min; se fija en la Task 1 con una medición real.

## Review Focus

Entradas que el spec no menciona y que más probablemente muerdan a una persona usando el bot (cada una tiene su test en la task indicada):

1. **Símbolo con otra capitalización o inexistente** (`/oportunidad xauusd`, `us100.SPOT`, `/oportunidad orro`): se canoniza al nombre exacto del terminal o se responde «no encontré el símbolo», sin gastar cupo ni agy. → Task 2 y Task 10.
2. **Dos ejecutivos piden el mismo activo a la vez:** un solo agy; el segundo recibe «ya se está generando». → Task 10.
3. **Una fuente con URL peligrosa** (`javascript:`, `http:` plano, HTML en `tesis` o `entidad`) o con campos en formato roto (agy entrega un string o `null` en vez de lista): se descarta o se degrada a «sin voces», nunca rompe el HTML ni inyecta marcado. → Task 4, Task 5 y Task 9.
4. **Análisis vigente cuya carpeta se borró del disco, o registro con entradas del formato antiguo (por semana) mezcladas:** se rehace sin caerse y las entradas antiguas se conservan intactas. → Task 3.
5. **Terminal sin respuesta al verificar la vigencia** (reuso a las 3 a. m. con MT5 cerrado): se entrega el análisis vigente con el aviso «no pude verificar si sigue vigente», sin rehacer ni fallar. → Task 8 y Task 10.

---

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `scripts/analista/orden.py` | Gramática del pedido: `/oportunidad` y `/seguimiento` exigen activo; símbolo fuera del catálogo marcado `libre` | Modificar |
| `scripts/analista/simbolos.py` | Buscar un símbolo en el terminal MT5 (nombre exacto, `description` limpio, `digits`) | Crear |
| `scripts/analista/registro_semanal.py` | Registro por activo: vigencia 7 días, reúsos, caducidad, seguimientos; conserva el formato antiguo | Reescribir |
| `config/fuentes_prestigio.json` | Lista cerrada de entidades y medios con sus dominios | Crear |
| `scripts/analista/fuentes.py` | Validar fuentes (entidad, medio, dominio, frescura, URL, esquema), verificar URL, calcular discrepancia | Crear |
| `scripts/analista/esquema.py` | Campo `fuentes`, excepción de cifras atribuidas, prohibición de invitar a operar | Modificar |
| `scripts/analista/preparar.py` | `preparar_oportunidad` de un activo; `preparar_seguimiento` contra el análisis vigente | Modificar |
| `scripts/analista/vigencia.py` | Caducidad anticipada: `motivo_caducidad` y `verificar` | Crear |
| `scripts/analista/comercial.py` | Textos fijos: invitación a MT5, texto de acompañamiento, chip | Modificar |
| `scripts/analista/oportunidad_html.py` + `templates/oportunidad/pieza.html` | Secciones Fundamental, Lectura técnica, Voces; bloque MT5; rótulo ilustrativo | Modificar |
| `scripts/analista/bot.py` | Flujo de `/oportunidad` por activo, candado por activo, ayuda y menú | Modificar |
| `scripts/analista/agy.py` | Timeout fijado con la medición | Modificar |
| `.claude/commands/analista.md` | Instrucciones de agy: web solo para `fuentes`, discrepancia, sin invitar a operar | Reescribir |
| `docs/bot-analistas.md` | Documentación del bot | Modificar |
| `tests/analista_fixtures.py` y `tests/test_analista_*.py` | Fixtures de un activo y tests nuevos | Modificar/Crear |

**Fuera de alcance (anotado para el director):** `comercial.INVITACION_ACTIVA` («¿Te interesa operar este escenario?») y varios textos de `seguimiento.py` invitan a operar. Por el mismo criterio regulatorio conviene revisarlos, pero el spec solo cubre `/oportunidad`.

---

### Task 0: Rama de trabajo

**Files:** ninguno.

- [ ] **Step 1: Crear la rama desde la actual (conserva el spec commiteado)**

```bash
cd /c/Users/bbrav/grupo-analisis-mercado
git checkout -b feat/oportunidad-por-activo
git log --oneline -3
```
Expected: la rama nueva y `b4149a9 docs(spec): corrige numeración de secciones` entre los últimos commits. No hagas `git add -A`: hay archivos de datos modificados ajenos a este trabajo; agrega siempre archivos por nombre.

---

### Task 1: Medir agy con búsqueda web y fijar el timeout

**Files:**
- Modify: `scripts/analista/agy.py:14-16`
- Create: `tests/test_analista_agy.py`

**Interfaces:**
- Consumes: `agy_encargo.invocar(prompt, tier, timeout) -> Resultado(codigo, segundos, respuesta)`.
- Produces: `analista.agy.TIMEOUT` (str `"<N>m"`) usado por `escribir_textos`.

- [ ] **Step 1: Medir una corrida real equivalente (3 a 5 fuentes)**

Corre dos veces, con dos activos distintos, y anota los segundos:

```bash
cd /c/Users/bbrav/grupo-analisis-mercado
uv run python -c "
import sys; sys.path.insert(0, 'scripts')
from agy_encargo import invocar
for activo in ('el oro (XAUUSD)', 'el dólar peso chileno (USDCLP)'):
    r = invocar('Busca en la web de 3 a 5 notas de los últimos 14 días de bancos de inversión o fuentes de prestigio (Goldman Sachs, JPMorgan, UBS, Citi, Reuters, Bloomberg, Banco Central de Chile) sobre ' + activo + '. Por cada una escribe una línea: entidad | medio | fecha AAAA-MM-DD | url del artículo | postura (alcista, bajista o neutral) | tesis en una frase.', 'flash', '20m')
    print(activo, r.codigo, round(r.segundos), 's'); print(r.respuesta[:1500]); print('---')
"
```
Expected: dos líneas `codigo ok` con sus segundos. Si alguna da `timeout`, el techo de 20 m ya es el dato: anótalo y súbelo.

- [ ] **Step 2: Elegir el timeout con esta regla**

`TIMEOUT = max(12, ceil_a_múltiplo_de_5(2 × mayor_medición_en_minutos + 3))`. (Las mediciones previas: 192 s la consulta completa de prueba y de 5 a 7 min un encargo real de septiembre.) Anota las mediciones en el comentario de la constante.

- [ ] **Step 3: Escribir el test**

`tests/test_analista_agy.py`:

```python
"""El techo de espera de agy para redactar una pieza."""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import agy  # noqa: E402


def test_el_timeout_alcanza_para_la_busqueda_web():
    minutos = int(re.fullmatch(r"(\d+)m", agy.TIMEOUT).group(1))
    assert minutos >= 12  # nunca bajo lo que ya medía un encargo real
```

- [ ] **Step 4: Fijar la constante y correr el test**

Edita `scripts/analista/agy.py` reemplazando las líneas 14 a 16 (reemplaza `<N>` y las cifras medidas):

```python
# Un encargo real de agy tarda de 5 a 7 minutos (medido el 2026-09-06). Con búsqueda web de 3 a 5
# fuentes medimos <T1> s y <T2> s el 2026-10-16; el techo deja el doble más la validación.
TIMEOUT = "<N>m"
```

Run: `uv run pytest tests/test_analista_agy.py -q`
Expected: `1 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/analista/agy.py tests/test_analista_agy.py
git commit -m "chore(bot): fija el timeout de agy con la medición de la búsqueda web

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Pedido `/oportunidad <activo>` y símbolos del terminal

**Files:**
- Create: `scripts/analista/simbolos.py`
- Modify: `scripts/analista/orden.py:96-145`
- Test: `tests/test_analista_orden.py` (modificar), `tests/test_analista_simbolos.py` (crear)

**Interfaces:**
- Produces: `simbolos.buscar(texto: str, mt5=None) -> dict | None` con `{"ticker": str, "descripcion": str, "digits": int}`; levanta `simbolos.TerminalNoDisponible` si no hay terminal. `simbolos.limpiar(texto: str) -> str`.
- Produces: `orden.interpretar("/oportunidad oro Juan")` → `Orden("oportunidad", {"ticker": "XAUUSD"}, "Juan")`; un símbolo que no está en el catálogo → `args = {"ticker": <texto tal cual>, "libre": True}`.
- Consumes (Task 10): el bot canoniza los `libre` con `simbolos.buscar` antes de preparar.

- [ ] **Step 1: Escribir los tests de `orden`**

En `tests/test_analista_orden.py` elimina `test_oportunidad_no_lleva_argumentos` (línea 30) y `test_oportunidad_no_lleva_argumentos_ni_admite_personalizar` (línea 119) y agrega (usa el `UNIVERSO` o fixture que ya usen los tests de `/seguimiento` de ese archivo; si no hay, define uno mínimo como se muestra):

```python
UNIVERSO_MINIMO = [{"ticker": "XAUUSD", "nombre": "Oro"}, {"ticker": "USDCLP", "nombre": "Dólar"}]


def test_oportunidad_exige_activo():
    with pytest.raises(od.PedidoInvalido, match="Falta el activo"):
        od.interpretar("/oportunidad", UNIVERSO_MINIMO)


def test_oportunidad_resuelve_activo_y_saludo():
    assert od.interpretar("/oportunidad oro Juan", UNIVERSO_MINIMO) == od.Orden(
        "oportunidad", {"ticker": "XAUUSD"}, "Juan")


def test_oportunidad_con_un_simbolo_que_no_esta_en_el_catalogo_queda_para_el_terminal():
    o = od.interpretar("/oportunidad TGT.US Ana", UNIVERSO_MINIMO)
    assert o.args == {"ticker": "TGT.US", "libre": True} and o.saludo == "Ana"


def test_seguimiento_tambien_deja_los_simbolos_libres_para_el_terminal():
    o = od.interpretar("/seguimiento TGT.US", UNIVERSO_MINIMO)
    assert o.args == {"ticker": "TGT.US", "libre": True}


def test_oportunidad_rechaza_lo_que_no_parece_un_simbolo():
    with pytest.raises(od.PedidoInvalido):
        od.interpretar("/oportunidad ¿¿??", UNIVERSO_MINIMO)
```

Actualiza también `tests/test_analista_bot.py::test_pedido_invalido_responde_el_motivo` en la Task 10 (hoy `/seguimiento pizza` ya no se rechaza en el acto).

- [ ] **Step 2: Correr y ver que fallan**

Run: `uv run pytest tests/test_analista_orden.py -q`
Expected: FAIL (`Falta el activo` no se levanta; `libre` no existe).

- [ ] **Step 3: Implementar en `orden.py`**

Reemplaza `_activo_y_saludo` y el bloque de `interpretar` desde `if comando == "seguimiento":` hasta el final:

```python
_SIMBOLO = re.compile(r"^[A-Za-z#][A-Za-z0-9#._]{1,19}$")


def _activo_y_saludo(cuerpo: str, universo: list[dict[str, Any]]) -> tuple[dict[str, Any], str]:
    """El activo es el prefijo más largo que se resuelve en el catálogo; lo que sigue es el saludo.

    Un activo que el catálogo no conoce no se rechaza acá: el terminal manda (spec 2026-10-16 §3).
    La primera palabra pasa como símbolo `libre` y el bot la canoniza contra MT5 al atender, para
    no tocar el terminal desde el hilo que escucha Telegram.
    """
    palabras = cuerpo.split()
    for n in range(len(palabras), 0, -1):
        try:
            ticker = resolver_activo(" ".join(palabras[:n]), universo)
        except PedidoInvalido:
            continue
        return {"ticker": ticker}, _limpiar_saludo(" ".join(palabras[n:]))
    if _SIMBOLO.match(palabras[0]):
        return {"ticker": palabras[0], "libre": True}, _limpiar_saludo(" ".join(palabras[1:]))
    resolver_activo(cuerpo, universo)  # levanta el error de siempre
    raise PedidoInvalido(f"No encontré el activo '{cuerpo}'.")  # inalcanzable: resolver_activo levanta
```

y en `interpretar`:

```python
    if not cuerpo:
        raise PedidoInvalido(f"Falta el activo. Escribe por ejemplo: /{comando} oro")
    if universo is None:
        import screener_gi as sc

        universo = sc.cargar_universo(solo_renderizables=False)
    args, saludo = _activo_y_saludo(cuerpo, universo)
    return Orden(pieza=comando, args=args, saludo=saludo)
```

Reemplaza también el mensaje de saludo largo `Ejemplo: /seguimiento oro Juan` por `Ejemplo: /oportunidad oro Juan` solo si el test lo exige; si no, déjalo.

- [ ] **Step 4: Escribir los tests de `simbolos`**

`tests/test_analista_simbolos.py`:

```python
"""Búsqueda de un símbolo en el terminal, sin MT5 real."""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import simbolos as sm  # noqa: E402


class Mt5Falso:
    def __init__(self, simbolos):
        self._s = simbolos

    def symbols_get(self):
        return self._s


def _s(name, description, digits=2):
    return SimpleNamespace(name=name, description=description, digits=digits)


def test_busca_sin_importar_mayusculas_y_devuelve_el_nombre_exacto():
    mt5 = Mt5Falso([_s("US100.spot", "US Tech 100", 2), _s("TGT.US", "Target Corp", 2)])
    assert sm.buscar("us100.SPOT", mt5=mt5) == {"ticker": "US100.spot", "descripcion": "US Tech 100", "digits": 2}


def test_un_simbolo_que_no_existe_devuelve_none():
    assert sm.buscar("pizza", mt5=Mt5Falso([_s("XAUUSD", "Gold")])) is None


def test_el_nombre_del_terminal_se_limpia_sin_traducirlo():
    assert sm.limpiar("  Target \x00 Corp\n") == "Target Corp"
    assert sm.limpiar("x" * 200) == "x" * 60


def test_sin_terminal_se_dice():
    class Roto:
        def symbols_get(self):
            raise OSError("sin IPC")

    with pytest.raises(sm.TerminalNoDisponible):
        sm.buscar("oro", mt5=Roto())
```

- [ ] **Step 5: Implementar `simbolos.py`**

```python
"""Símbolos del terminal MT5: el universo del bot es lo que el broker ofrece.

El catálogo (`config/activos.json`) aporta nombre y `digits` de los activos de la casa; un
símbolo fuera de él se acepta con lo que dice el terminal (spec 2026-10-16 §3). El nombre es el
`description` del terminal tal como viene: traducirlo es peligroso («Target» pasa a «Blanco»)
y pedírselo a agy lo haría cambiar entre corridas.
"""
from __future__ import annotations

from typing import Any

NOMBRE_MAX = 60


class TerminalNoDisponible(RuntimeError):
    """MT5 no responde: no se puede confirmar si el símbolo existe."""


def limpiar(texto: str) -> str:
    """Solo caracteres imprimibles y espacios simples; recorta a `NOMBRE_MAX`."""
    imprimible = "".join(c if c.isprintable() else " " for c in texto)
    return " ".join(imprimible.split())[:NOMBRE_MAX]


def buscar(texto: str, mt5: Any = None) -> dict[str, Any] | None:
    """El símbolo del terminal que se llama `texto` (sin distinguir mayúsculas), o None."""
    try:
        if mt5 is None:
            from market_data_mcp import mt5_client

            mt5_client.connect()
            import MetaTrader5 as mt5  # noqa: PLC0415
        simbolos = mt5.symbols_get()
    except Exception as exc:  # noqa: BLE001
        raise TerminalNoDisponible(f"MT5 no respondió ({exc.__class__.__name__})") from exc
    quiero = texto.strip().lower()
    for s in simbolos or ():
        if s.name.lower() == quiero:
            return {"ticker": s.name, "descripcion": limpiar(s.description or s.name), "digits": int(s.digits)}
    return None
```

- [ ] **Step 6: Correr y ver que pasan**

Run: `uv run pytest tests/test_analista_orden.py tests/test_analista_simbolos.py -q`
Expected: todo en verde (corrige en `test_analista_orden.py` cualquier test existente que asuma `/oportunidad` sin argumentos o que `/seguimiento <palabra rara>` se rechace en el acto).

- [ ] **Step 7: Commit**

```bash
git add scripts/analista/orden.py scripts/analista/simbolos.py tests/test_analista_orden.py tests/test_analista_simbolos.py
git commit -m "feat(bot): /oportunidad exige activo y acepta símbolos del terminal

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Registro por activo con vigencia de 7 días

**Files:**
- Modify (reescribir): `scripts/analista/registro_semanal.py`
- Modify (reescribir): `tests/test_analista_registro_semanal.py`

**Interfaces:**
- Produces: `VIGENCIA = timedelta(days=7)`; `vigente(ticker, ahora, ruta=RUTA) -> dict | None`; `anotar(ticker, dir_pedido, creada, direccion, creado_por, ruta=RUTA) -> dict`; `anotar_reuso(ticker, quien, cuando, ruta=RUTA) -> None`; `caducar(ticker, motivo, cuando, ruta=RUTA) -> None`; `anotar_seguimiento(ticker, seguimiento, ruta=RUTA) -> None`; `RegistroDanado`. Entrada: `{ticker, dir, creada, vence, direccion, creado_por, reusos, seguimientos, caducada}`. `creado_por` es `{"nombre": str, "id": str}`.
- Consumes: nada. Las entradas del formato antiguo (con `semana` y sin `ticker`) se conservan y se ignoran.

- [ ] **Step 1: Escribir los tests**

Reemplaza todo `tests/test_analista_registro_semanal.py`:

```python
"""El registro por activo: vigencia de 7 días, reúsos, caducidad y seguimientos."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import registro_semanal as rg  # noqa: E402

SCL = ZoneInfo("America/Santiago")
CREADA = datetime(2026, 10, 12, 9, 0, tzinfo=SCL)
CAMILA = {"nombre": "Camila Rojas", "id": "111"}


def _pieza(tmp_path: Path, nombre: str = "a") -> Path:
    d = tmp_path / nombre
    d.mkdir()
    (d / "pieza.json").write_text("{}", encoding="utf-8")
    return d


def _anotar(tmp_path, ticker="XAUUSD", creada=CREADA, nombre="a"):
    ruta = tmp_path / "registro.json"
    d = _pieza(tmp_path, nombre)
    rg.anotar(ticker, d, creada, "ALCISTA", CAMILA, ruta)
    return ruta, d


def test_sin_registro_no_hay_analisis_vigente(tmp_path):
    assert rg.vigente("XAUUSD", CREADA, tmp_path / "registro.json") is None


def test_el_dia_6_se_reusa_y_el_dia_8_se_rehace(tmp_path):
    ruta, d = _anotar(tmp_path)
    assert rg.vigente("XAUUSD", CREADA + timedelta(days=6), ruta)["dir"] == str(d)
    assert rg.vigente("XAUUSD", CREADA + timedelta(days=8), ruta) is None


def test_exactamente_a_los_7_dias_ya_no_se_reusa(tmp_path):
    ruta, _ = _anotar(tmp_path)
    assert rg.vigente("XAUUSD", CREADA + rg.VIGENCIA, ruta) is None


def test_queda_a_nombre_de_quien_lo_genero(tmp_path):
    ruta, _ = _anotar(tmp_path)
    e = rg.vigente("XAUUSD", CREADA, ruta)
    assert e["creado_por"] == CAMILA and e["vence"].startswith("2026-10-19T09:00")
    assert e["reusos"] == [] and e["seguimientos"] == [] and e["caducada"] is None


def test_cada_activo_tiene_su_propia_vigencia(tmp_path):
    ruta, _ = _anotar(tmp_path)
    assert rg.vigente("USDCLP", CREADA, ruta) is None


def test_el_reuso_queda_anotado_con_quien_lo_pidio(tmp_path):
    ruta, _ = _anotar(tmp_path)
    rg.anotar_reuso("XAUUSD", {"nombre": "Pedro Soto", "id": "222"}, CREADA + timedelta(days=2), ruta)
    r = rg.vigente("XAUUSD", CREADA + timedelta(days=2), ruta)["reusos"]
    assert [x["nombre"] for x in r] == ["Pedro Soto"]


def test_un_analisis_caducado_no_se_reusa_aunque_no_hayan_pasado_7_dias(tmp_path):
    ruta, _ = _anotar(tmp_path)
    rg.caducar("XAUUSD", "el precio tocó la invalidación", CREADA + timedelta(days=2), ruta)
    assert rg.vigente("XAUUSD", CREADA + timedelta(days=3), ruta) is None
    e = json.loads(ruta.read_text(encoding="utf-8"))[0]
    assert e["caducada"]["motivo"] == "el precio tocó la invalidación"  # queda como historia


def test_el_analisis_nuevo_reemplaza_al_caducado(tmp_path):
    ruta, _ = _anotar(tmp_path)
    rg.caducar("XAUUSD", "x", CREADA + timedelta(days=2), ruta)
    nueva = _pieza(tmp_path, "b")
    rg.anotar("XAUUSD", nueva, CREADA + timedelta(days=2), "BAJISTA", CAMILA, ruta)
    assert rg.vigente("XAUUSD", CREADA + timedelta(days=3), ruta)["dir"] == str(nueva)


def test_una_carpeta_borrada_no_se_reusa(tmp_path):
    ruta, d = _anotar(tmp_path)
    (d / "pieza.json").unlink()
    assert rg.vigente("XAUUSD", CREADA, ruta) is None


def test_los_seguimientos_quedan_en_la_historia_del_analisis(tmp_path):
    ruta, _ = _anotar(tmp_path)
    rg.anotar_seguimiento("XAUUSD", {"estado": "en_curso", "ejecutivo": "111"}, ruta)
    assert rg.vigente("XAUUSD", CREADA, ruta)["seguimientos"] == [{"estado": "en_curso", "ejecutivo": "111"}]


def test_las_entradas_del_formato_antiguo_se_conservan_y_se_ignoran(tmp_path):
    ruta = tmp_path / "registro.json"
    antigua = {"semana": "2026-W41", "dir": "x", "creada": "2026-10-05T09:00:00-03:00",
               "tickers": ["XAUUSD"], "seguimientos": []}
    ruta.write_text(json.dumps([antigua]), encoding="utf-8")
    assert rg.vigente("XAUUSD", CREADA, ruta) is None
    rg.anotar("XAUUSD", _pieza(tmp_path), CREADA, "ALCISTA", CAMILA, ruta)
    entradas = json.loads(ruta.read_text(encoding="utf-8"))
    assert entradas[0] == antigua and entradas[1]["ticker"] == "XAUUSD"


def test_un_registro_corrupto_no_se_sobrescribe(tmp_path):
    ruta = tmp_path / "registro.json"
    ruta.write_text("{no es json", encoding="utf-8")
    with pytest.raises(rg.RegistroDanado):
        rg.anotar("XAUUSD", _pieza(tmp_path), CREADA, "ALCISTA", CAMILA, ruta)
    assert ruta.read_text(encoding="utf-8") == "{no es json"
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `uv run pytest tests/test_analista_registro_semanal.py -q`
Expected: FAIL (`rg.vigente` no existe).

- [ ] **Step 3: Reescribir el módulo**

Reemplaza el cuerpo de `scripts/analista/registro_semanal.py` desde la línea 1 (conserva `_leer`, `_escribir`, `RegistroDanado` y `RUTA` tal cual):

```python
"""Registro de análisis por activo: quién lo generó, cuánto vale y qué se hizo con él.

Se versiona, como la bitácora de despachos: es historia de lo que el equipo comercial le mandó a
sus clientes. Cumple dos funciones (spec 2026-10-16 §2 y §5):

1. **Reúso.** Un análisis vale 7 días corridos desde que se creó. Mientras esté vigente, cualquiera
   que pida ese activo recibe el mismo, sin gastar agy ni cupo. Puede caducar antes si la lectura
   se rompe (`caducar`); el análisis caducado queda como historia, con su motivo.
2. **El análisis contra el que se mide `/seguimiento`.**

Las entradas del formato antiguo (una por semana, con `semana` y sin `ticker`) se conservan en el
archivo y se ignoran: son historia de solo lectura.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from analista import RAIZ

RUTA = RAIZ / "data" / "semanal" / "registro.json"
VIGENCIA = timedelta(days=7)


class RegistroDanado(ValueError):
    """El registro no se puede leer: no se sigue, para no pisarlo."""


def _leer(ruta: Path) -> list[dict[str, Any]]:
    """Solo un archivo ausente es un registro vacío. Un JSON corrupto levanta: si se
    tratara como vacío, la próxima escritura borraría toda la historia."""
    try:
        texto = ruta.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    try:
        return json.loads(texto)
    except json.JSONDecodeError as e:
        raise RegistroDanado(f"registro semanal corrupto, no se sobrescribe: {ruta}") from e


def _escribir(ruta: Path, entradas: list[dict[str, Any]]) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(".tmp")
    tmp.write_text(json.dumps(entradas, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    tmp.replace(ruta)


def _ultima(entradas: list[dict[str, Any]], ticker: str) -> dict[str, Any] | None:
    """La entrada más reciente del activo: la que manda. Las del formato antiguo no tienen `ticker`."""
    return next((e for e in reversed(entradas) if e.get("ticker") == ticker), None)


def vigente(ticker: str, ahora: datetime, ruta: Path = RUTA) -> dict[str, Any] | None:
    """El análisis vigente del activo, si existe, no caducó, no venció y su carpeta sigue en disco."""
    e = _ultima(_leer(ruta), ticker)
    if e is None or e.get("caducada"):
        return None
    if datetime.fromisoformat(e["vence"]) <= ahora:
        return None
    return e if (Path(e["dir"]) / "pieza.json").exists() else None


def anotar(ticker: str, dir_pedido: Path, creada: datetime, direccion: str,
           creado_por: dict[str, str], ruta: Path = RUTA) -> dict[str, Any]:
    entradas = _leer(ruta)
    nueva = {"ticker": ticker, "dir": str(dir_pedido), "creada": creada.isoformat(),
             "vence": (creada + VIGENCIA).isoformat(), "direccion": direccion,
             "creado_por": creado_por, "reusos": [], "seguimientos": [], "caducada": None}
    entradas.append(nueva)
    _escribir(ruta, entradas)
    return nueva


def _modificar(ticker: str, ruta: Path, cambio) -> None:
    entradas = _leer(ruta)
    e = _ultima(entradas, ticker)
    if e is not None:
        cambio(e)
        _escribir(ruta, entradas)


def anotar_reuso(ticker: str, quien: dict[str, str], cuando: datetime, ruta: Path = RUTA) -> None:
    _modificar(ticker, ruta, lambda e: e.setdefault("reusos", []).append({**quien, "cuando": cuando.isoformat()}))


def caducar(ticker: str, motivo: str, cuando: datetime, ruta: Path = RUTA) -> None:
    """El análisis deja de valer antes de los 7 días; queda en el registro con su motivo."""
    _modificar(ticker, ruta, lambda e: e.update(caducada={"motivo": motivo, "cuando": cuando.isoformat()}))


def anotar_seguimiento(ticker: str, seguimiento: dict[str, Any], ruta: Path = RUTA) -> None:
    """Suma un seguimiento al análisis del activo: qué se informó, a quién y cuándo."""
    _modificar(ticker, ruta, lambda e: e.setdefault("seguimientos", []).append(seguimiento))
```

- [ ] **Step 4: Correr y ver que pasan**

Run: `uv run pytest tests/test_analista_registro_semanal.py -q`
Expected: `12 passed`. (Otros módulos que usaban `rg.foto` / `rg.anotar_foto` quedan rotos hasta las Tasks 6, 7 y 10: es esperado.)

- [ ] **Step 5: Commit**

```bash
git add scripts/analista/registro_semanal.py tests/test_analista_registro_semanal.py
git commit -m "feat(bot): registro por activo con vigencia de 7 días y caducidad

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Fuentes de prestigio: lista, validación y discrepancia

**Files:**
- Create: `config/fuentes_prestigio.json`
- Create: `scripts/analista/fuentes.py`
- Test: `tests/test_analista_fuentes.py` (crear)

**Interfaces:**
- Produces: `fuentes.CAMPOS = ("entidad", "medio", "fecha", "url", "postura", "tesis")`; `fuentes.POSTURAS = ("alcista", "bajista", "neutral")`; `fuentes.cargar_lista(ruta=CONFIG) -> dict`; `fuentes.verificar_url(url) -> "ok" | "sin_verificar" | "muerta"`; `fuentes.depurar(crudas, hoy, lista=None, verificar=verificar_url) -> tuple[list[dict], list[str]]` (cada válida lleva además `verificacion`); `fuentes.depurar_pieza(pieza, hoy, lista=None, verificar=verificar_url) -> tuple[dict, list[str]]`; `fuentes.discrepa(fuente, direccion) -> bool`.
- Consumes (Task 5): `esquema.py` importa `fuentes.CAMPOS` y `fuentes.POSTURAS`.

- [ ] **Step 1: Crear la lista (la edita el director)**

`config/fuentes_prestigio.json` (cada clave de `medios` es un nombre; sirve tanto de `entidad` como de `medio`; el dominio de la URL tiene que ser uno del `medio`):

```json
{
  "_nota": "Lista cerrada. La edita el director. `entidad` es quien opina; `medio` es dónde se publicó. Un banco puede ser medio de sí mismo (su sitio) o publicarse en un medio de prensa.",
  "frescura_dias": 14,
  "entidades": {
    "bancos_de_inversion": ["Goldman Sachs", "JPMorgan", "Morgan Stanley", "Bank of America", "Citi", "UBS", "Barclays", "Standard Chartered", "Jefferies", "Deutsche Bank", "HSBC", "ING", "Commerzbank"],
    "chile": ["Banco Central de Chile", "Cochilco", "Banchile", "BCI Estudios", "Santander Chile", "Itaú Chile"],
    "organismos": ["Fed", "BCE", "EIA", "OPEP", "FMI", "BIS", "World Gold Council", "Agencia Internacional de Energía"]
  },
  "medios": {
    "Reuters": ["reuters.com"],
    "Bloomberg": ["bloomberg.com"],
    "Financial Times": ["ft.com"],
    "WSJ": ["wsj.com"],
    "CNBC": ["cnbc.com"],
    "MarketWatch": ["marketwatch.com"],
    "Kitco": ["kitco.com"],
    "FXStreet": ["fxstreet.com"],
    "Diario Financiero": ["df.cl"],
    "La Tercera": ["latercera.com"],
    "Goldman Sachs": ["goldmansachs.com"],
    "JPMorgan": ["jpmorgan.com", "jpmorganchase.com"],
    "Morgan Stanley": ["morganstanley.com"],
    "Bank of America": ["bankofamerica.com", "bofa.com"],
    "Citi": ["citigroup.com", "citi.com"],
    "UBS": ["ubs.com"],
    "Barclays": ["barclays.com"],
    "Standard Chartered": ["sc.com"],
    "Jefferies": ["jefferies.com"],
    "Deutsche Bank": ["db.com", "deutschebank.com"],
    "HSBC": ["hsbc.com"],
    "ING": ["ing.com"],
    "Commerzbank": ["commerzbank.com"],
    "Banco Central de Chile": ["bcentral.cl"],
    "Cochilco": ["cochilco.cl"],
    "Banchile": ["banchile.cl"],
    "BCI Estudios": ["bci.cl"],
    "Santander Chile": ["santander.cl"],
    "Itaú Chile": ["itau.cl"],
    "Fed": ["federalreserve.gov"],
    "BCE": ["ecb.europa.eu"],
    "EIA": ["eia.gov"],
    "OPEP": ["opec.org"],
    "FMI": ["imf.org"],
    "BIS": ["bis.org"],
    "World Gold Council": ["gold.org"],
    "Agencia Internacional de Energía": ["iea.org"]
  }
}
```

(Investing.com queda fuera a propósito: respondió 403 a bots y agy entregó solo la portada.)

- [ ] **Step 2: Escribir los tests**

`tests/test_analista_fuentes.py`:

```python
"""Validación de las fuentes que agy cita: lista cerrada, dominio, frescura, URL y discrepancia."""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import fuentes as fu  # noqa: E402

HOY = date(2026, 10, 16)


def _f(**cambios):
    base = {"entidad": "Goldman Sachs", "medio": "Reuters", "fecha": "2026-10-14",
            "url": "https://www.reuters.com/markets/commodities/oro-goldman-2026-10-14/",
            "postura": "alcista", "tesis": "Goldman Sachs mantiene su visión alcista del oro."}
    return {**base, **cambios}


def _ok(url):
    return "ok"


def test_una_fuente_valida_pasa_y_trae_su_verificacion():
    validas, descartes = fu.depurar([_f()], HOY, verificar=_ok)
    assert [v["entidad"] for v in validas] == ["Goldman Sachs"] and validas[0]["verificacion"] == "ok"
    assert descartes == []


def test_una_entidad_fuera_de_la_lista_se_descarta():
    validas, descartes = fu.depurar([_f(entidad="Un Blog Cualquiera")], HOY, verificar=_ok)
    assert validas == [] and "Un Blog Cualquiera" in descartes[0] and "lista" in descartes[0]


def test_el_dominio_tiene_que_ser_el_del_medio():
    validas, descartes = fu.depurar([_f(url="https://www.otro-sitio.com/articulo-largo")], HOY, verificar=_ok)
    assert validas == [] and "dominio" in descartes[0]


def test_un_subdominio_del_medio_vale():
    validas, _ = fu.depurar([_f(url="https://es.reuters.com/mercados/oro-2026")], HOY, verificar=_ok)
    assert len(validas) == 1


def test_una_portada_no_es_un_articulo():
    validas, descartes = fu.depurar([_f(url="https://www.reuters.com/")], HOY, verificar=_ok)
    assert validas == [] and "artículo" in descartes[0]


def test_la_fecha_vieja_futura_o_mal_escrita_se_descarta():
    for fecha in ("2026-09-20", "2026-10-30", "ayer"):
        validas, descartes = fu.depurar([_f(fecha=fecha)], HOY, verificar=_ok)
        assert validas == [] and "fecha" in descartes[0], fecha


def test_catorce_dias_justos_todavia_valen():
    validas, _ = fu.depurar([_f(fecha="2026-10-02")], HOY, verificar=_ok)
    assert len(validas) == 1


def test_una_url_muerta_se_descarta_y_una_con_muro_queda_sin_verificar():
    validas, descartes = fu.depurar([_f()], HOY, verificar=lambda u: "muerta")
    assert validas == [] and "no responde" in descartes[0]
    validas, _ = fu.depurar([_f()], HOY, verificar=lambda u: "sin_verificar")
    assert validas[0]["verificacion"] == "sin_verificar"


def test_solo_https_y_nada_de_marcado_en_los_campos():
    for malo in (_f(url="http://www.reuters.com/markets/oro-2026"), _f(url="javascript:alert(1)//reuters.com/a/b"),
                 _f(tesis="Goldman <b>ve</b> el oro alcista"), _f(entidad="<script>")):
        validas, _ = fu.depurar([malo], HOY, verificar=_ok)
        assert validas == []


def test_una_postura_fuera_del_vocabulario_se_descarta():
    validas, descartes = fu.depurar([_f(postura="muy alcista")], HOY, verificar=_ok)
    assert validas == [] and "postura" in descartes[0]


def test_falta_un_campo_o_no_es_un_diccionario():
    validas, descartes = fu.depurar([{"entidad": "UBS"}, "texto suelto", None], HOY, verificar=_ok)
    assert validas == [] and len(descartes) == 3


def test_la_misma_url_no_se_repite():
    validas, _ = fu.depurar([_f(), _f(tesis="Otra frase.")], HOY, verificar=_ok)
    assert len(validas) == 1


def test_agy_no_entrego_una_lista():
    pieza = {"editorial": {"fuentes": "[[ESCRIBIR]]"}}
    nueva, descartes = fu.depurar_pieza(pieza, HOY, verificar=_ok)
    assert nueva["editorial"]["fuentes"] == [] and descartes


def test_depurar_pieza_reemplaza_las_fuentes_por_las_validas():
    pieza = {"editorial": {"fuentes": [_f(), _f(entidad="Blog")]}}
    nueva, descartes = fu.depurar_pieza(pieza, HOY, verificar=_ok)
    assert len(nueva["editorial"]["fuentes"]) == 1 and len(descartes) == 1


def test_la_discrepancia_la_calcula_python():
    assert fu.discrepa(_f(postura="alcista"), "BAJISTA") is True
    assert fu.discrepa(_f(postura="bajista"), "BAJISTA") is False
    assert fu.discrepa(_f(postura="neutral"), "LATERAL") is False
    assert fu.discrepa(_f(postura="alcista"), "LATERAL") is True
```

- [ ] **Step 3: Correr y ver que fallan**

Run: `uv run pytest tests/test_analista_fuentes.py -q`
Expected: FAIL (`No module named analista.fuentes`).

- [ ] **Step 4: Implementar `fuentes.py`**

```python
"""Las voces de bancos y prensa que agy cita: Python valida, agy solo las encuentra.

agy busca en la web (spec 2026-10-16 §7) y escribe `editorial.fuentes[]`. Nada de lo que trae se
cree: la entidad tiene que estar en `config/fuentes_prestigio.json`, el dominio de la URL tiene
que ser el del medio, la fecha tiene que ser fresca y la URL tiene que responder. Lo que no pasa
se descarta con su motivo; ninguna fuente se inventa ni se rellena.

La discrepancia con nuestra lectura la calcula Python con la `postura`, no la declara agy: un
modelo tiende a alinearse con el titular que encontró.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from analista import RAIZ

CONFIG = RAIZ / "config" / "fuentes_prestigio.json"
CAMPOS = ("entidad", "medio", "fecha", "url", "postura", "tesis")
POSTURAS = ("alcista", "bajista", "neutral")
TESIS_MAX = 260
_MARCADO = re.compile(r"[<>]")


def cargar_lista(ruta: Path = CONFIG) -> dict[str, Any]:
    return json.loads(ruta.read_text(encoding="utf-8"))


def _entidades(lista: dict[str, Any]) -> set[str]:
    return {e for grupo in lista["entidades"].values() for e in grupo}


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def _del_dominio(host: str, dominios: list[str]) -> bool:
    return any(host == d or host.endswith("." + d) for d in dominios)


def _con_ruta_de_articulo(url: str) -> bool:
    ruta = urlparse(url).path.strip("/")
    return bool(ruta) and ruta.lower() not in {"index", "index.html", "index.php"}


def verificar_url(url: str, timeout: int = 10) -> str:
    """`ok`, `sin_verificar` (muro de pago o bloqueo a bots) o `muerta` (404 o dominio caído)."""
    import requests

    try:
        r = requests.get(url, timeout=timeout, allow_redirects=True, stream=True,
                         headers={"User-Agent": "Mozilla/5.0 (compatible; GI-analistas)"})
        r.close()
    except requests.Timeout:
        return "sin_verificar"
    except requests.RequestException:
        return "muerta"
    if r.status_code in (401, 403, 429):
        return "sin_verificar"
    return "ok" if r.status_code < 400 else "muerta"


def _motivo_de_descarte(f: Any, hoy: date, lista: dict[str, Any], verificar: Callable[[str], str]
                        ) -> tuple[str | None, str]:
    """(motivo, verificacion). Motivo None = la fuente pasa."""
    if not isinstance(f, dict) or any(not isinstance(f.get(c), str) or not f[c].strip() for c in CAMPOS):
        return "una fuente viene incompleta", ""
    nombre = f["entidad"]
    if any(_MARCADO.search(f[c]) for c in CAMPOS):
        return f"{nombre}: trae marcado en sus campos", ""
    if nombre not in _entidades(lista):
        return f"{nombre}: la entidad no está en la lista de fuentes de prestigio", ""
    if f["postura"] not in POSTURAS:
        return f"{nombre}: la postura «{f['postura']}» no es alcista, bajista ni neutral", ""
    if len(f["tesis"]) > TESIS_MAX:
        return f"{nombre}: la tesis es demasiado larga", ""
    dominios = lista["medios"].get(f["medio"])
    if dominios is None:
        return f"{nombre}: el medio {f['medio']} no está en la lista", ""
    if not f["url"].startswith("https://"):
        return f"{nombre}: la URL no es https", ""
    if not _del_dominio(_host(f["url"]), dominios):
        return f"{nombre}: el dominio de la URL no es el de {f['medio']}", ""
    if not _con_ruta_de_articulo(f["url"]):
        return f"{nombre}: la URL es una portada y no un artículo", ""
    try:
        dias = (hoy - datetime.strptime(f["fecha"], "%Y-%m-%d").date()).days
    except ValueError:
        return f"{nombre}: la fecha {f['fecha']!r} no es AAAA-MM-DD", ""
    if dias < 0 or dias > int(lista.get("frescura_dias", 14)):
        return f"{nombre}: la fecha {f['fecha']} está fuera de la ventana de {lista.get('frescura_dias', 14)} días", ""
    estado = verificar(f["url"])
    if estado == "muerta":
        return f"{nombre}: la URL no responde", ""
    return None, estado


def depurar(crudas: Any, hoy: date, lista: dict[str, Any] | None = None,
            verificar: Callable[[str], str] = verificar_url) -> tuple[list[dict[str, Any]], list[str]]:
    """Las fuentes que pasan (con su `verificacion`) y el motivo de cada descarte."""
    lista = lista or cargar_lista()
    validas: list[dict[str, Any]] = []
    descartes: list[str] = []
    vistas: set[str] = set()
    for f in crudas if isinstance(crudas, list) else []:
        motivo, estado = _motivo_de_descarte(f, hoy, lista, verificar)
        if motivo is None and f["url"] in vistas:
            motivo = f"{f['entidad']}: la URL ya estaba citada"
        if motivo:
            descartes.append(motivo)
            continue
        vistas.add(f["url"])
        validas.append({**{c: f[c].strip() for c in CAMPOS}, "verificacion": estado})
    return validas, descartes


def depurar_pieza(pieza: dict[str, Any], hoy: date, lista: dict[str, Any] | None = None,
                  verificar: Callable[[str], str] = verificar_url) -> tuple[dict[str, Any], list[str]]:
    """Deja en `editorial.fuentes` solo las válidas. Sin lista de agy, queda vacía y se avisa."""
    crudas = pieza["editorial"].get("fuentes")
    validas, descartes = depurar(crudas, hoy, lista, verificar)
    if not isinstance(crudas, list):
        descartes.append("agy no entregó la lista de fuentes")
    pieza["editorial"]["fuentes"] = validas
    return pieza, descartes


_OPUESTA = {"ALCISTA": "alcista", "BAJISTA": "bajista", "LATERAL": "neutral"}


def discrepa(fuente: dict[str, Any], direccion: str) -> bool:
    """La fuente ve distinto que nuestra lectura (alcista/bajista/lateral contra su postura)."""
    return _OPUESTA.get(direccion.upper(), "neutral") != fuente["postura"]
```

(Corrige el nombre `_OPUESTA` a `_POSTURA_DE_LA_LECTURA` si prefieres: el mapa dice qué postura equivale a cada dirección de nuestra lectura.)

- [ ] **Step 5: Correr y ver que pasan**

Run: `uv run pytest tests/test_analista_fuentes.py -q`
Expected: todo en verde.

- [ ] **Step 6: Commit**

```bash
git add config/fuentes_prestigio.json scripts/analista/fuentes.py tests/test_analista_fuentes.py
git commit -m "feat(bot): validación de fuentes de bancos y prensa con lista cerrada

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Esquema: campo `fuentes`, cifras atribuidas y sin invitar a operar

**Files:**
- Modify: `scripts/analista/esquema.py`
- Modify: `tests/analista_fixtures.py` (`pieza_oportunidad` pasa a un activo con `fuentes`)
- Modify: `tests/test_analista_esquema.py`

**Interfaces:**
- Consumes: `fuentes.CAMPOS`, `fuentes.POSTURAS` (Task 4).
- Produces: `es.CAMPOS["oportunidad"] == ("titular", "bajada", "fuentes")`; `es.cifras_ajenas(texto, datos, fuentes=())`; fixture `fx.pieza_oportunidad(dir_pedido, laminas=False, wti=False, rango=False, fuentes=None)` que arma **un** activo, y `fx.FUENTES_EJEMPLO`.

- [ ] **Step 1: Actualizar el fixture**

En `tests/analista_fixtures.py` reemplaza `pieza_oportunidad` completa:

```python
FUENTES_EJEMPLO = [{
    "entidad": "Goldman Sachs", "medio": "Reuters", "fecha": "2026-10-14",
    "url": "https://www.reuters.com/markets/commodities/oro-goldman-2026-10-14/",
    "postura": "alcista", "tesis": "Goldman Sachs ve el oro en 4.800 dólares por la demanda de bancos centrales.",
    "verificacion": "ok"}]


def pieza_oportunidad(dir_pedido: Path, laminas: bool = False, wti: bool = False, rango: bool = False,
                      fuentes: list | None = None) -> dict:
    """El análisis de un activo con su texto ya escrito (por defecto el oro; `rango` es el cobre).

    Escribe el gráfico en `dir_pedido`; con `laminas=True` también la lámina, que en el bot se
    rinde antes del HTML (así el botón «Descargar lámina» aparece).
    """
    a = activo_semanal(rango=rango, ticker="WTI.spot" if wti else None)
    _imagen(dir_pedido, a["grafico"])
    if laminas:
        _imagen(dir_pedido, {"WTI.spot": "lamina_wti_spot.png"}.get(a["ticker"], f"lamina_{a['ticker'].lower()}.png"))
    t = a["ticker"]
    p = es.nueva_pieza("oportunidad", {"ticker": t},
                       {"ticker": t, "chip": "ANÁLISIS TÉCNICO Y FUNDAMENTAL", "edicion": "lunes 12/10 · 09:30",
                        "vigencia": {"desde": "lunes 12/10", "hasta": "lunes 19/10"},
                        "activos": [a], "drivers": {t: ["Dollar Index"]}, "agenda_semana": [], "curva": [],
                        "fundamental": {"fuera_catalogo": False, "sin_drivers": False, "referencia": "semanal"}},
                       {t: a["grafico"]}, extra_campos={"titulares": [t], "contexto": [t]})
    p["editorial"] = {"titular": f"{a['nombre']}: lectura técnica y fundamental",
                      "bajada": "Lectura de nuestros sistemas, drivers y voces de bancos.",
                      "titulares": {t: f"Titular de {t}"},
                      "contexto": {t: f"Contexto de {t}. La lectura se mantiene mientras el precio respete la línea."},
                      "fuentes": [dict(f) for f in (FUENTES_EJEMPLO if fuentes is None else fuentes)]}
    return p
```

Elimina el `p["editorial"]` y los parámetros viejos (`fuera`). Revisa que `fx.activo_semanal` sigue intacto.

- [ ] **Step 2: Escribir los tests nuevos en `tests/test_analista_esquema.py`**

Reemplaza `test_el_contexto_semanal_tiene_que_invitar_a_operar` (línea 212) y `test_la_invitacion_a_operar_pasa` (línea 221) y agrega:

```python
def test_el_contexto_no_puede_invitar_a_operar(tmp_path):
    p = fx.pieza_oportunidad(tmp_path)
    for frase in ("El escenario se puede operar si el precio respeta la línea.", "Conviene operarlo con stop.",
                  "Es un nivel operable.", "Opera el rebote."):
        p["editorial"]["contexto"]["XAUUSD"] = f"Contexto. {frase}"
        errs = es.errores(p)
        assert any("invita a operar" in e for e in errs), frase


def test_el_contexto_sin_invitacion_pasa(tmp_path):
    assert es.errores(fx.pieza_oportunidad(tmp_path)) == []


def test_las_fuentes_se_exigen_como_lista(tmp_path):
    p = fx.pieza_oportunidad(tmp_path)
    p["editorial"]["fuentes"] = "texto suelto"
    assert any("fuentes" in e for e in es.errores(p))
    p["editorial"]["fuentes"] = es.MARCA
    assert any("sin escribir" in e.lower() or "fuentes" in e for e in es.errores(p))
    p["editorial"]["fuentes"] = []  # sin voces es válido: se avisa, no se rellena
    assert es.errores(p) == []


def test_una_fuente_con_postura_o_campos_rotos_se_rechaza(tmp_path):
    p = fx.pieza_oportunidad(tmp_path)
    p["editorial"]["fuentes"] = [{**fx.FUENTES_EJEMPLO[0], "postura": "muy alcista"}]
    assert any("fuentes.0" in e for e in es.errores(p))
    p["editorial"]["fuentes"] = [{"entidad": "UBS"}]
    assert any("fuentes.0" in e for e in es.errores(p))


def test_la_tesis_de_una_fuente_pasa_por_los_mismos_candados_de_texto(tmp_path):
    p = fx.pieza_oportunidad(tmp_path)
    p["editorial"]["fuentes"][0]["tesis"] = "Goldman — ve el oro alcista."
    assert any("fuentes.0.tesis" in e for e in es.errores(p))


def test_una_cifra_de_tercero_atribuida_en_la_misma_frase_pasa(tmp_path):
    p = fx.pieza_oportunidad(tmp_path)
    p["editorial"]["contexto"]["XAUUSD"] = "Contexto. Goldman Sachs ve el oro en 4.800 dólares, y nuestra lectura es distinta."
    assert es.errores(p) == []


def test_una_cifra_de_tercero_sin_atribucion_se_rechaza(tmp_path):
    p = fx.pieza_oportunidad(tmp_path)
    p["editorial"]["contexto"]["XAUUSD"] = "Contexto. El oro llegaría a 4.800 dólares."
    assert any("4.800" in e for e in es.errores(p))


def test_la_cifra_atribuida_a_otra_entidad_se_rechaza(tmp_path):
    p = fx.pieza_oportunidad(tmp_path)
    p["editorial"]["contexto"]["XAUUSD"] = "Contexto. UBS ve el oro en 4.800 dólares."
    assert any("4.800" in e for e in es.errores(p))


def test_una_cifra_inventada_nunca_pasa_aunque_se_atribuya(tmp_path):
    p = fx.pieza_oportunidad(tmp_path)
    p["editorial"]["contexto"]["XAUUSD"] = "Contexto. Goldman Sachs ve el oro en 9.999 dólares."
    assert any("9.999" in e for e in es.errores(p))
```

Actualiza los demás tests de este archivo que usan `fx.pieza_oportunidad`, `es.CAMPOS["oportunidad"]` o el titular de seis activos para el nuevo fixture de un activo (`set(es.CAMPOS) == {"oportunidad", "seguimiento"}` sigue igual; los que listan `CAMPOS["oportunidad"]` ahora incluyen `fuentes`).

- [ ] **Step 3: Correr y ver que fallan**

Run: `uv run pytest tests/test_analista_esquema.py -q`
Expected: FAIL en los tests nuevos.

- [ ] **Step 4: Implementar en `esquema.py`**

a) `CAMPOS` y la importación:

```python
from analista import fuentes as fu

CAMPOS: dict[str, tuple[str, ...]] = {
    # El análisis de un activo: portada, un titular y un contexto anidados por activo, y las voces
    # de bancos y prensa que agy encontró en la web (lista de objetos, ver `fuentes.py`).
    "oportunidad": ("titular", "bajada", "fuentes"),
    "seguimiento": (),
}
```

b) Reemplaza `_INVITA` por la prohibición:

```python
# La pieza no invita a operar: por regulación invita a revisar la plataforma (director, 2026-10-16).
# Reemplaza la regla del 2026-10-12, que exigía invitar a operar el escenario.
_OPERAR = re.compile(r"\bopera(s|r|rlo|rla|rse|ble|bles|mos)?\b|\boperes\b")
```

c) `textos()` (maneja la lista de fuentes):

```python
def textos(pieza: dict[str, Any]) -> list[tuple[str, str]]:
    salida: list[tuple[str, str]] = []
    for campo, valor in pieza.get("editorial", {}).items():
        if isinstance(valor, dict):
            salida.extend((f"{campo}.{k}", str(v)) for k, v in valor.items())
        elif isinstance(valor, list):  # `fuentes`: solo la tesis es texto de agy; lo demás lo valida `fuentes.py`
            salida.extend((f"{campo}.{i}.tesis", str(f.get("tesis", ""))) for i, f in enumerate(valor)
                          if isinstance(f, dict))
        else:
            salida.append((campo, str(valor)))
    return salida
```

d) `cifras_ajenas` con atribución:

```python
def cifras_ajenas(texto: str, datos: Any, fuentes: list[dict[str, Any]] | tuple = ()) -> list[str]:
    """Las cifras del texto que no están en `datos`.

    Única excepción (spec 2026-10-16 §7): la cifra de un tercero que aparece en la `tesis` de una
    fuente validada y se atribuye a ella en la misma frase («Goldman Sachs ve el oro en 4.800»).
    """
    volcado = json.dumps(datos, ensure_ascii=False)
    permitidas = {_plano_numero(t) for t in _NUMERO.findall(volcado)}
    ajenas: list[str] = []
    for frase in re.split(r"(?<=[.!?])\s+|\n+", texto):
        plano = _plano(frase)
        de_terceros = {_plano_numero(t) for f in fuentes if _plano(f["entidad"]) in plano
                       for t in _NUMERO.findall(f["tesis"])}
        ajenas += [t for t in _NUMERO.findall(frase)
                   if _significativo(t) and _plano_numero(t) not in permitidas
                   and _plano_numero(t) not in de_terceros]
    return ajenas
```

e) En `errores()`: valida la estructura de `fuentes` antes de `pares = textos(pieza)` y pasa las fuentes a `cifras_ajenas`; la tesis no se revisa por cifras (son del tercero):

```python
    fuentes = editorial.get("fuentes") if tipo == "oportunidad" else None
    if tipo == "oportunidad" and fuentes != MARCA:
        if not isinstance(fuentes, list):
            errs.append("fuentes: tiene que ser una lista (vacía si no hay voces atingentes)")
            fuentes = []
        else:
            for i, f in enumerate(fuentes):
                if not isinstance(f, dict) or any(not isinstance(f.get(c), str) or not f[c].strip() for c in fu.CAMPOS):
                    errs.append(f"fuentes.{i}: le faltan campos ({', '.join(fu.CAMPOS)})")
                elif f["postura"] not in fu.POSTURAS:
                    errs.append(f"fuentes.{i}: la postura {f['postura']!r} no es alcista, bajista ni neutral")
    fuentes_ok = [f for f in (fuentes or []) if isinstance(f, dict) and all(isinstance(f.get(c), str) for c in fu.CAMPOS)]
```

y en el bucle `for donde, texto in pares:` cambia la línea de cifras por:

```python
        if not donde.endswith(".tesis"):  # la cifra de la tesis es del tercero citado
            for cifra in cifras_ajenas(texto, pieza.get("datos"), fuentes_ok):
                errs.append(f"{donde}: la cifra {cifra} no está en los datos del terminal")
```

f) Reemplaza el bloque final `if tipo == "oportunidad":` (el que exige invitar a operar) por:

```python
    if tipo == "oportunidad":
        for donde, texto in pares:
            if _OPERAR.search(_plano(texto)):
                errs.append(f"{donde}: invita a operar; por regulación la pieza invita a revisar la plataforma, "
                            "no a operar")
```

Si `fuentes == MARCA`, el texto `[[ESCRIBIR]]` ya lo marca `validar_textos` («sin escribir»), no agregues otro error.

- [ ] **Step 5: Correr y ver que pasan**

Run: `uv run pytest tests/test_analista_esquema.py -q`
Expected: todo en verde. (Los tests de HTML, preparar y bot siguen rotos hasta las tasks 6, 9 y 10.)

- [ ] **Step 6: Commit**

```bash
git add scripts/analista/esquema.py tests/analista_fixtures.py tests/test_analista_esquema.py
git commit -m "feat(bot): esquema con fuentes citadas, cifras atribuidas y sin invitar a operar

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 6: `preparar_oportunidad` de un solo activo

**Files:**
- Modify: `scripts/analista/preparar.py` (líneas 27-50 excepciones; 54-208 lectores; 280-354 preparación)
- Modify: `tests/test_analista_preparar.py` (la sección «la foto semanal», líneas 41-175)

**Interfaces:**
- Consumes: `simbolos.buscar` (Task 2), `rg.RUTA` (Task 3), `es.nueva_pieza` (Task 5).
- Produces: `pr.SinAnalisisError(PreparacionFallida)` (reemplaza a `SinSemanaError`, `SinFotoError`, `FueraDeLaFotoError`, `FotoVaciaError`, `EsperaVelaError`, que se eliminan); `Lectores.referencia`, `Lectores.lectura_actual`; `pr.preparar_oportunidad(orden, dir_pedido, ahora, lec)` arma `datos.activos` de largo 1, `datos.vigencia`, `datos.fundamental`, `orden.args = {"ticker": t}`; `pr.fuera_con_referencia` se elimina.
- `Lectores.referencia(estrategia, ticker, digits, semana, ahora, base) -> (Lectura, datetime, str)`: la referencia, cuándo se guardó y su origen (`"semanal"` o `"propia"`).
- `Lectores.lectura_actual(estrategia, ticker, digits, lector, ahora, referencia=None) -> (Lectura, dict[str, DataFrame])`.

- [ ] **Step 1: Escribir los tests**

En `tests/test_analista_preparar.py` elimina los tests de la foto semanal (`test_sin_analisis_semanal_no_hay_pieza`, `test_con_una_linea_a_mas_en_prueba_espera_el_cierre`, `test_la_foto_trae_los_activos_en_orden_de_puntaje`, `test_una_foto_sin_activos_no_se_arma`, `test_un_elegido_sin_referencia_queda_fuera_y_se_anota`, `test_rehacer_la_foto_...`) y `_sembrar`/`EstrategiaFalsa` si ya no se usan. Cambia `_lectores` para que ofrezca los dos lectores nuevos y agrega:

```python
def _lectores(base, **kw):
    por_defecto = dict(
        base_referencias=base, estrategia=lambda: EstrategiaFalsa(),
        referencia=lambda est, t, d, semana, ahora, b: (fx.lectura(ticker=t), AHORA_LUNES, "semanal"),
        contrato=lambda t, p: {"clp_unidad": 950.0, "vol_min": 0.01, "vol_paso": 0.01},
        grafico_lectura=_grafico_falso,
        catalogo=lambda t: {"ticker": t, "nombre": {"XAUUSD": "Oro", "COPPER": "Cobre"}[t],
                            "digits": {"XAUUSD": 2, "COPPER": 0}[t], "unidad": "USD"},
        drivers=lambda t: ["Dollar Index"], agenda=lambda a: ([], []), curva=lambda: ({}, []),
        cuenta=lambda: None, registro=base.parent / "registro_no_usado.json")
    return pr.Lectores(**{**por_defecto, **kw})


def test_el_analisis_trae_un_solo_activo_con_su_vigencia(tmp_path):
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES,
                        _lectores(tmp_path / "ref"))
    d = hecha.pieza["datos"]
    assert [a["ticker"] for a in d["activos"]] == ["XAUUSD"] and hecha.pieza["orden"]["args"] == {"ticker": "XAUUSD"}
    assert d["vigencia"] == {"desde": "lunes 12/10", "hasta": "lunes 19/10"}
    assert d["fundamental"] == {"fuera_catalogo": False, "sin_drivers": False, "referencia": "semanal"}
    assert set(hecha.pieza["editorial"]) == {"titular", "bajada", "titulares", "contexto", "fuentes"}


def test_sin_referencia_semanal_se_lee_de_nuevo_y_se_anota_como_propia(tmp_path):
    lec = _lectores(tmp_path / "ref", referencia=lambda est, t, d, s, a, b: (fx.lectura(ticker=t), a, "propia"))
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES, lec)
    assert hecha.pieza["datos"]["fundamental"]["referencia"] == "propia"


def test_un_simbolo_fuera_del_catalogo_usa_el_nombre_del_terminal_y_lo_avisa(tmp_path):
    fuera = {"ticker": "TGT.US", "nombre": "Target Corp", "ticker_visible": "TGT.US", "digits": 2,
             "unidad": "", "notas_marco": {}, "fuera_catalogo": True}
    lec = _lectores(tmp_path / "ref", catalogo=lambda t: fuera, drivers=lambda t: [])
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "TGT.US"}), tmp_path / "p", AHORA_LUNES, lec)
    d = hecha.pieza["datos"]
    assert d["activos"][0]["nombre"] == "Target Corp"
    assert d["fundamental"]["fuera_catalogo"] is True and d["fundamental"]["sin_drivers"] is True
    assert any("fuera del catálogo" in a for a in hecha.avisos)


def test_el_analisis_no_escribe_en_las_referencias_semanales(tmp_path):
    base = tmp_path / "ref"
    pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES, _lectores(base))
    assert not base.exists()


def test_la_curva_va_sin_porcentajes(tmp_path):
    curva = {"series": {"US10Y": {"nivel_pct": 4.2, "delta_1d_bps": 3, "delta_5d_bps": -2}}}
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES,
                        _lectores(tmp_path / "ref", curva=lambda: (curva, [])))
    assert "%" not in json.dumps(hecha.pieza["datos"]["curva"], ensure_ascii=False)
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `uv run pytest tests/test_analista_preparar.py -q -k "analisis or simbolo or curva or referencia"`
Expected: FAIL (`Lectores` no acepta `referencia`).

- [ ] **Step 3: Implementar**

a) Excepciones: reemplaza las clases de las líneas 31-49 por:

```python
class SinAnalisisError(PreparacionFallida):
    """El activo no tiene un análisis vigente: `/seguimiento` mide contra él (spec 2026-10-16 §2)."""
```

b) Lectores reales (junto a `_lectura_del_dia`, que se elimina) y el catálogo con respaldo del terminal:

```python
def _catalogo_o_terminal(ticker: str) -> dict[str, Any]:
    """El catálogo de la casa; un símbolo que no está se arma con lo que dice el terminal."""
    try:
        return _catalogo_de(ticker)
    except KeyError:
        from analista import simbolos

        info = simbolos.buscar(ticker)
        if info is None:
            raise PreparacionFallida(f"{ticker} no existe en el terminal") from None
        return {"ticker": info["ticker"], "nombre": info["descripcion"], "ticker_visible": info["ticker"],
                "digits": info["digits"], "unidad": "", "notas_marco": {}, "fuera_catalogo": True}


def _referencia(estrategia, ticker, digits, semana, ahora, base):
    """La referencia semanal si existe (la que ya circuló); si no, se lee de nuevo sin vela en curso,
    así nunca queda en PRUEBA. No escribe en `referencias_semanales/`: el escáner es su dueño."""
    import referencia_semanal as rs

    guardada = rs.cargar(semana, ticker, base)
    if guardada is not None:
        crudo = json.loads(rs.ruta(semana, ticker, base).read_text(encoding="utf-8"))
        return guardada, datetime.fromisoformat(crudo["guardada"]), "semanal"
    velas, _ = _velas(ticker, estrategia.marcos, rs.EXTRA)
    return estrategia.leer(ticker, velas, digits, None), ahora, "propia"


def _lectura_actual(estrategia, ticker, digits, lector, ahora, referencia=None):
    import referencia_semanal as rs

    return rs.lectura_actual(estrategia, ticker, digits, lector, ahora, referencia=referencia)
```

En `Lectores` cambia `catalogo` a `_catalogo_o_terminal`, elimina `estado_semanal` y `lectura_del_dia` y agrega:

```python
    referencia: Callable[..., tuple[Any, datetime, str]] = _referencia
    lectura_actual: Callable[..., tuple[Any, dict[str, pd.DataFrame]]] = _lectura_actual
```

(Importa `pandas as pd` en `preparar.py` con `from __future__ import annotations` solo para la anotación, o usa `Any`.) Elimina `_estado_semanal` y `_lectura_del_dia`.

c) Reemplaza `preparar_oportunidad` y elimina `fuera_con_referencia`:

```python
def preparar_oportunidad(orden: Orden, dir_pedido: Path, ahora: datetime, lec: Lectores) -> Preparada:
    """El análisis de UN activo: la lectura de nuestros sistemas, sus drivers y la agenda.

    La referencia es la semanal si el activo la tiene; si no, se lee de nuevo (spec 2026-10-16 §4).
    Las voces de bancos las agrega agy después; Python las valida (`fuentes.py`).
    """
    import referencia_semanal as rs

    ticker = orden.args["ticker"]
    estrategia = lec.estrategia()
    cat = lec.catalogo(ticker)
    digits = int(cat["digits"])
    base = lec.base_referencias or rs.DIR
    referencia, guardada, origen = lec.referencia(estrategia, ticker, digits, rs.semana_de(ahora), ahora, base)
    activo = _entrada_activo(ticker, referencia, guardada, 0.0, dir_pedido, lec, estrategia)
    avisos: list[str] = []
    if cat.get("fuera_catalogo"):
        avisos.append(f"{ticker} no está en el catálogo (activo fuera del catálogo): usé el nombre del terminal y "
                      "un marco genérico, sin drivers declarados.")
    agenda, av = lec.agenda(ahora)
    avisos += [f"contexto sin agenda: {a}" for a in av]
    curva, av = lec.curva()
    avisos += [f"contexto sin curva de tasas: {a}" for a in av]
    drivers = lec.drivers(ticker)
    sin_pct = _contexto_sin_porcentajes({"curva": _filas_curva(curva)})
    datos = {"ticker": ticker, "chip": "ANÁLISIS TÉCNICO Y FUNDAMENTAL",
             "edicion": fecha_corta(ahora) + f" · {ahora.astimezone(SANTIAGO):%H:%M}",
             "vigencia": {"desde": fecha_corta(ahora), "hasta": fecha_corta(ahora + rg.VIGENCIA)},
             "activos": [activo], "drivers": {ticker: drivers},
             "agenda_semana": [f"{ev.get('hora', '')} · {ev.get('nombre_es') or ev.get('evento', '')}" for ev in agenda],
             "curva": sin_pct["curva"],
             "fundamental": {"fuera_catalogo": bool(cat.get("fuera_catalogo")), "sin_drivers": not drivers,
                             "referencia": origen}}
    pieza = es.nueva_pieza("oportunidad", {"ticker": ticker}, datos, {ticker: activo["grafico"]},
                           extra_campos={"titulares": [ticker], "contexto": [ticker]})
    return Preparada(pieza, avisos)
```

Agrega al inicio del módulo `from analista import registro_semanal as rg` (ya no hay import circular: el registro no importa `preparar`). Elimina `niveles_lamina_semanal` solo si queda sin usos (no: `_entrada_activo` lo usa; déjalo).

d) `PREPARADORES` y `CON_TERMINAL` no cambian.

- [ ] **Step 4: Correr**

Run: `uv run pytest tests/test_analista_preparar.py -q -k "analisis or simbolo or curva or referencia or no_usa"`
Expected: verde (los tests de seguimiento se arreglan en la Task 7).

- [ ] **Step 5: Commit**

```bash
git add scripts/analista/preparar.py tests/test_analista_preparar.py
git commit -m "feat(bot): preparar el análisis de un solo activo, con referencia propia y símbolos del terminal

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 7: `/seguimiento` mide contra el análisis vigente del activo

**Files:**
- Modify: `scripts/analista/preparar.py` (`preparar_seguimiento`, línea ~357 en adelante)
- Modify: `tests/test_analista_preparar.py` (`_foto`, `_lectores_seg` y los tests de seguimiento, líneas 177-260)

**Interfaces:**
- Consumes: `rg.vigente(ticker, ahora, ruta)` (Task 3), `Lectores.lectura_actual` (Task 6), `rs.debe_reemplazar`.
- Produces: `preparar_seguimiento` lanza `SinAnalisisError("No hay un análisis vigente de <ticker>: pide primero /oportunidad <ticker>.")` sin análisis vigente.

- [ ] **Step 1: Reescribir los tests de seguimiento**

Reemplaza `_foto` y `_lectores_seg` (el resto de los tests del bloque mantiene su cuerpo, cambiando solo lo indicado):

```python
def _foto(tmp_path, activos):
    """Un análisis vigente en el registro, como lo deja /oportunidad."""
    d = tmp_path / "foto"
    d.mkdir()
    a = activos[0]
    p = es.nueva_pieza("oportunidad", {"ticker": a["ticker"]}, {"ticker": a["ticker"], "activos": activos}, {},
                       extra_campos={"titulares": [a["ticker"]], "contexto": [a["ticker"]]})
    pr.guardar_pieza(p, d)
    rg.anotar(a["ticker"], d, AHORA_LUNES, "BAJISTA", {"nombre": "Camila Rojas", "id": "111"},
              tmp_path / "registro.json")


def _lectores_seg(tmp_path, velas, precio, hoy=None):
    def lector(ticker, marcos, extra=0):
        return {"H4": velas}, None
    lec = _lectores(tmp_path / "ref", registro=tmp_path / "registro.json", velas=lector)
    lec.lectura_actual = lambda est, t, d, lector, ahora, referencia=None: (hoy or fx.lectura(precio=precio),
                                                                           {"H4": velas})
    return lec
```

Ajusta cada llamada: `_foto(tmp_path, [fx.activo_semanal()])` (sin `base`) y `_lectores_seg(tmp_path, velas, precio)`; quita `_sembrar`. Reemplaza los dos tests de «foto»:

```python
def test_seguimiento_sin_analisis_vigente_dice_que_pida_oportunidad(tmp_path):
    with pytest.raises(pr.SinAnalisisError, match=r"/oportunidad XAUUSD"):
        pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s", AHORA_LUNES,
                    _lectores_seg(tmp_path, pd.DataFrame(), 4000.0))


def test_seguimiento_de_otro_activo_no_usa_el_analisis_de_uno_vigente(tmp_path):
    _foto(tmp_path, [fx.activo_semanal()])
    with pytest.raises(pr.SinAnalisisError, match="USDCLP"):
        pr.preparar(Orden("seguimiento", {"ticker": "USDCLP"}), tmp_path / "s", AHORA_LUNES,
                    _lectores_seg(tmp_path, pd.DataFrame(), 4000.0))


def test_seguimiento_con_el_analisis_vencido_pide_uno_nuevo(tmp_path):
    _foto(tmp_path, [fx.activo_semanal()])
    with pytest.raises(pr.SinAnalisisError):
        pr.preparar(Orden("seguimiento", {"ticker": "XAUUSD"}), tmp_path / "s",
                    AHORA_LUNES + rg.VIGENCIA + timedelta(minutes=1), _lectores_seg(tmp_path, pd.DataFrame(), 4000.0))
```

(importa `timedelta`). En `test_seguimiento_informa_simulacion_y_lectura_por_separado` la lectura de hoy debe tener otra estructura que la de la foto para que `reemplazada` sea verdadera: pasa `hoy=fx.lectura(precio=4124.0, invalidacion=4300.0)` a `_lectores_seg` (la firma incluye el valor de la línea de seguridad, así que `debe_reemplazar` da `True` y el texto trae «La lectura de la semana cambió»).

- [ ] **Step 2: Correr y ver que fallan**

Run: `uv run pytest tests/test_analista_preparar.py -q -k seguimiento`
Expected: FAIL (`rg.foto` ya no existe).

- [ ] **Step 3: Reescribir el arranque de `preparar_seguimiento`**

Reemplaza desde la línea `semana = rs.semana_de(ahora)` hasta `reemplazada = ...` (incluye el cálculo de `diaria`, `vigente` y `reemplazada`) por:

```python
    ticker = orden.args["ticker"]
    vig = rg.vigente(ticker, ahora, lec.registro or rg.RUTA)  # un registro corrupto levanta: no es "sin análisis"
    if vig is None:
        raise SinAnalisisError(f"No hay un análisis vigente de {ticker}: pide primero /oportunidad {ticker}.")
    a = cargar_pieza(Path(vig["dir"]))["datos"]["activos"][0]
    esc = a["escenario"]
    motivo = op.motivo_sin_simulacion(a)
    referencia_foto = lectura_de_dict(a["lectura"])
    estrategia = lec.estrategia()
    lectura, velas = lec.lectura_actual(estrategia, ticker, a["digits"], lec.velas, ahora, referencia=referencia_foto)
    reemplazada = rs.debe_reemplazar(referencia_foto, lectura)
    h4 = velas[referencia_foto.marco]
```

y en el resto de la función: `diaria.lectura` → `lectura` (precio, `sg.texto_lectura`, `sg.mensaje`, `_sin_segundo_objetivo`, `niveles_lamina_seguimiento`), `diaria.velas[...]` ya quedó como `velas[...]`, `list(diaria.avisos)` → `[]`, `"semana": semana` → `"semana": rs.semana_de(ahora)` (el seguimiento conserva el campo por compatibilidad con `macro_seguimiento`), y elimina los imports `registro_semanal as rg` locales duplicados (ya hay uno global). Borra las variables `semana`, `base`, `pieza_foto`, `activos`, `nombres` que ya no se usan.

- [ ] **Step 4: Correr**

Run: `uv run pytest tests/test_analista_preparar.py -q`
Expected: todo verde.

- [ ] **Step 5: Commit**

```bash
git add scripts/analista/preparar.py tests/test_analista_preparar.py
git commit -m "feat(bot): /seguimiento mide contra el análisis vigente del activo

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Caducidad anticipada de la vigencia

**Files:**
- Create: `scripts/analista/vigencia.py`
- Test: `tests/test_analista_vigencia.py` (crear)

**Interfaces:**
- Consumes: `pr.Lectores` (Task 6: `estrategia`, `lectura_actual`, `velas`), `rs.debe_reemplazar`.
- Produces: `vigencia.motivo_caducidad(referencia, actual, velas) -> str | None`; `vigencia.verificar(pieza, ahora, lectores=None) -> tuple[str | None, str | None]` = `(motivo_de_caducidad, aviso_si_no_se_pudo_verificar)`.

- [ ] **Step 1: Escribir los tests**

```python
"""La caducidad anticipada: un análisis con la invalidación rota no se reusa (spec 2026-10-16 §2)."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

import analista_fixtures as fx  # noqa: E402
from analista import preparar as pr  # noqa: E402
from analista import vigencia as vg  # noqa: E402

SCL = ZoneInfo("America/Santiago")
AHORA = datetime(2026, 10, 14, 11, 0, tzinfo=SCL)
VELA = fx.lectura().vela


def _velas(altos_bajos):
    return pd.DataFrame([{"time": VELA + 14400 * (i + 1), "high": h, "low": l} for i, (h, l) in enumerate(altos_bajos)])


def test_sin_novedad_el_analisis_sigue_vigente():
    ref = fx.lectura(direccion="ALCISTA", precio=4000.0, invalidacion=3950.0, objetivo=4100.0)
    assert vg.motivo_caducidad(ref, fx.lectura(precio=4020.0), _velas([(4030, 3990)])) is None


def test_el_precio_que_toca_la_invalidacion_caduca_alcista():
    ref = fx.lectura(direccion="ALCISTA", invalidacion=3950.0, objetivo=4100.0)
    assert "invalidación" in vg.motivo_caducidad(ref, fx.lectura(precio=3990.0), _velas([(4030, 3949)]))


def test_el_objetivo_alcanzado_caduca():
    ref = fx.lectura(direccion="ALCISTA", invalidacion=3950.0, objetivo=4100.0)
    assert "objetivo" in vg.motivo_caducidad(ref, fx.lectura(precio=4090.0), _velas([(4101, 4000)]))


def test_bajista_es_el_espejo():
    ref = fx.lectura(direccion="BAJISTA", precio=4000.0, invalidacion=4050.0, objetivo=3900.0)
    assert "invalidación" in vg.motivo_caducidad(ref, fx.lectura(precio=4010.0), _velas([(4051, 3990)]))
    assert "objetivo" in vg.motivo_caducidad(ref, fx.lectura(precio=3950.0), _velas([(4010, 3899)]))


def test_el_precio_actual_cuenta_aunque_no_haya_velas_nuevas():
    ref = fx.lectura(direccion="ALCISTA", invalidacion=3950.0, objetivo=4100.0)
    assert vg.motivo_caducidad(ref, fx.lectura(precio=3940.0), pd.DataFrame(columns=["time", "high", "low"]))


def test_un_cambio_de_estructura_caduca():
    ref = fx.lectura(invalidacion=3950.0)
    assert "estructura" in vg.motivo_caducidad(ref, fx.lectura(invalidacion=3900.0), _velas([(4010, 3990)]))


def _pieza():
    return {"datos": {"activos": [fx.activo_semanal()]}}


def _lectores(actual, velas, falla=False):
    def lectura(est, t, d, lector, ahora, referencia=None):
        if falla:
            raise OSError("MT5 cerrado")
        return actual, {"H4": velas}
    return pr.Lectores(estrategia=lambda: object(), lectura_actual=lectura)


def test_verificar_devuelve_el_motivo_para_caducar():
    ref_activo = fx.activo_semanal()["lectura"]
    from estrategia.contrato import lectura_de_dict

    ref = lectura_de_dict(ref_activo)  # bajista, invalidación 4227,32
    motivo, aviso = vg.verificar(_pieza(), AHORA, _lectores(fx.lectura(direccion="BAJISTA", precio=4230.0,
                                                                       invalidacion=4227.32), _velas([(4231, 4180)])))
    assert motivo and aviso is None


def test_con_el_terminal_caido_se_entrega_con_aviso_y_sin_rehacer():
    motivo, aviso = vg.verificar(_pieza(), AHORA, _lectores(None, None, falla=True))
    assert motivo is None and "no pude verificar si sigue vigente" in aviso.lower()
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `uv run pytest tests/test_analista_vigencia.py -q`
Expected: FAIL (`No module named analista.vigencia`).

- [ ] **Step 3: Implementar `vigencia.py`**

```python
"""Caducidad anticipada: un análisis vigente deja de valer si la lectura se rompió.

Con vigencia fija de 7 días, un análisis del lunes cuya invalidación se rompió el martes seguiría
circulando el jueves (spec 2026-10-16 §2). Al reutilizarlo, Python vuelve a seguir su referencia
contra el mercado de hoy: si cambió la estructura, el precio tocó la invalidación o alcanzó el
objetivo, caduca y se rehace aunque no hayan pasado los 7 días.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from estrategia.contrato import Lectura, lectura_de_dict


def motivo_caducidad(referencia: Lectura, actual: Lectura, velas: Any) -> str | None:
    """Por qué el análisis ya no vale, o None. `velas` son las del marco operativo, con `time/high/low`."""
    import referencia_semanal as rs

    if rs.debe_reemplazar(referencia, actual):
        return "la estructura de la lectura cambió: una línea se rompió por cierre"
    desde = velas[velas["time"] > referencia.vela] if len(velas) else velas
    altos = [actual.precio] + ([float(desde["high"].max())] if len(desde) else [])
    bajos = [actual.precio] + ([float(desde["low"].min())] if len(desde) else [])
    inv, obj = referencia.invalidacion, referencia.objetivo
    if referencia.direccion == "ALCISTA":
        if inv and min(bajos) <= inv.precio:
            return "el precio tocó la invalidación"
        if obj and max(altos) >= obj.precio:
            return "el precio alcanzó el objetivo técnico"
    elif referencia.direccion == "BAJISTA":
        if inv and max(altos) >= inv.precio:
            return "el precio tocó la invalidación"
        if obj and min(bajos) <= obj.precio:
            return "el precio alcanzó el objetivo técnico"
    return None


def verificar(pieza: dict[str, Any], ahora: datetime, lectores=None) -> tuple[str | None, str | None]:
    """(motivo de caducidad, aviso). Con el terminal caído no se rehace: se entrega con el aviso."""
    from analista import preparar as pr

    lec = lectores or pr.Lectores()
    a = pieza["datos"]["activos"][0]
    referencia = lectura_de_dict(a["lectura"])
    try:
        actual, velas = lec.lectura_actual(lec.estrategia(), a["ticker"], a["digits"], lec.velas, ahora,
                                           referencia=referencia)
        return motivo_caducidad(referencia, actual, velas[referencia.marco]), None
    except Exception:  # noqa: BLE001  el terminal es un extra de esta verificación
        return None, "No pude verificar si sigue vigente (el terminal no respondió): te lo entrego tal cual."
```

- [ ] **Step 4: Correr y ver que pasan**

Run: `uv run pytest tests/test_analista_vigencia.py -q`
Expected: `9 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/analista/vigencia.py tests/test_analista_vigencia.py
git commit -m "feat(bot): caducidad anticipada del análisis cuando la lectura se rompe

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Ficha HTML: secciones, bloque MT5 y rótulo ilustrativo

**Files:**
- Modify: `scripts/analista/comercial.py` (constantes, `payload_semanal`, `texto_whatsapp_base`)
- Modify: `scripts/analista/oportunidad_html.py` (`_panel`, `_simulacion_correo`, `_marco_correo`, `armar`, `guardar`)
- Modify: `templates/oportunidad/pieza.html` (línea 78, CSS)
- Modify: `tests/test_analista_oportunidad_html.py`, `tests/test_analista_comercial.py`

**Interfaces:**
- Consumes: `fu.discrepa` (Task 4), fixture de un activo con `fuentes` (Task 5).
- Produces: `cm.REVISION_MT5_TITULO`, `cm.REVISION_MT5_PUNTOS`, `cm.ROTULO_ILUSTRATIVO = "Ejemplo ilustrativo para revisar en MT5"`, `cm.texto_acompanamiento(nombre_activo: str, saludo: str) -> str`; `oh.guardar` escribe `analisis_<ticker>_<ejecutivo>.html`.

- [ ] **Step 1: Escribir los tests**

En `tests/test_analista_oportunidad_html.py` (usa los `EJECUTIVO` y `HOY` que ya define el archivo) agrega y adapta:

```python
def _html(tmp_path, **kw):
    return oh.armar(fx.pieza_oportunidad(tmp_path, laminas=True, **kw), tmp_path, EJECUTIVO, fx.AUTOR, HOY)


def test_la_ficha_tiene_las_tres_secciones(tmp_path):
    h = _html(tmp_path)
    for titulo in ("Lectura técnica", "Fundamental", "Voces de bancos y prensa"):
        assert titulo in h


def test_cada_voz_lleva_entidad_medio_fecha_y_enlace(tmp_path):
    h = _html(tmp_path)
    assert "Goldman Sachs" in h and "Reuters" in h and "2026-10-14" in h
    assert 'href="https://www.reuters.com/markets/commodities/oro-goldman-2026-10-14/"' in h and 'rel="noopener' in h


def test_la_discrepancia_con_los_bancos_se_marca(tmp_path):
    h = _html(tmp_path)  # lectura bajista del oro, Goldman alcista
    assert "Discrepa de nuestra lectura" in h and "la nuestra es la que manda" in h.lower()


def test_una_voz_que_coincide_no_lleva_marca_de_discrepancia(tmp_path):
    f = dict(fx.FUENTES_EJEMPLO[0], postura="bajista")
    assert "Discrepa de nuestra lectura" not in _html(tmp_path, fuentes=[f])


def test_una_url_sin_verificar_se_dice(tmp_path):
    f = dict(fx.FUENTES_EJEMPLO[0], verificacion="sin_verificar")
    assert "sin verificar" in _html(tmp_path, fuentes=[f]).lower()


def test_sin_fuentes_avisa_y_no_rellena(tmp_path):
    h = _html(tmp_path, fuentes=[])
    assert "Sin voces de bancos o prensa atingentes esta vez" in h and "Goldman" not in h


def test_el_html_no_deja_pasar_marcado_de_las_fuentes(tmp_path):
    f = dict(fx.FUENTES_EJEMPLO[0], tesis='Ve el oro <img src=x onerror=alert(1)> alcista.')
    assert "<img src=x" not in _html(tmp_path, fuentes=[f])


def test_la_ficha_cierra_con_el_bloque_de_revision_en_mt5(tmp_path):
    h = _html(tmp_path)
    assert h.count(cm.REVISION_MT5_TITULO) >= 2  # en la ficha y en el correo
    for punto in cm.REVISION_MT5_PUNTOS:
        assert punto in h


def test_la_simulacion_se_rotula_como_ejemplo_ilustrativo(tmp_path):
    h = _html(tmp_path)
    assert h.count(cm.ROTULO_ILUSTRATIVO) >= 2  # panel del ejecutivo y correo


def test_el_correo_no_invita_a_operar(tmp_path):
    h = _html(tmp_path).lower()
    assert "evaluar tus próximas operaciones" not in h and "se puede operar" not in h


def test_el_archivo_lleva_el_activo_y_el_ejecutivo(tmp_path):
    ruta = oh.guardar(fx.pieza_oportunidad(tmp_path, laminas=True), tmp_path, EJECUTIVO, fx.AUTOR, HOY)
    assert ruta.name.startswith("analisis_xauusd_") and "oportunidad" not in ruta.name


def test_la_cabecera_muestra_hasta_cuando_vale(tmp_path):
    assert "lunes 19/10" in _html(tmp_path)
```

Agrega `from analista import comercial as cm` al archivo si no está. En `tests/test_analista_comercial.py` agrega:

```python
def test_el_texto_de_acompanamiento_invita_a_revisar_mt5_y_no_a_operar():
    t = cm.texto_acompanamiento("Oro", "Juan")
    assert t.startswith("Hola Juan, ") and "MT5" in t
    for malo in ("operar", "oportunidad", "—", "–", "compra", "vende"):
        assert malo not in t.lower()


def test_el_texto_de_whatsapp_cierra_invitando_a_revisar_mt5():
    from analista_fixtures import activo_semanal
    t = cm.texto_whatsapp_base(activo_semanal(), "Titular", "Contexto.")
    assert "MT5" in t and "operar" not in t.lower()
```

Elimina o adapta los tests existentes que asumían varios activos o `datos["semana"]` (`test_analista_oportunidad_html.py` líneas ~61-136: `wti=True` con tres activos pasa a un activo WTI; el que cuenta `Descargar lámina >= 2` pasa a `>= 1`).

- [ ] **Step 2: Correr y ver que fallan**

Run: `uv run pytest tests/test_analista_oportunidad_html.py tests/test_analista_comercial.py -q`
Expected: FAIL.

- [ ] **Step 3: Implementar en `comercial.py`**

Agrega tras `INVITACION_CERRADA`:

```python
# La pieza no invita a operar (regulación, director 2026-10-16): invita a revisar la plataforma MT5.
REVISION_MT5_TITULO = "Para revisar con tu cliente en MT5"
REVISION_MT5_PUNTOS = (
    "Abrir el gráfico del activo en MT5 y ver las líneas de la lectura.",
    "Repasar los tres escenarios y qué los invalida.",
    "Conversar la estrategia y cómo seguirla en la plataforma.",
)
ROTULO_ILUSTRATIVO = "Ejemplo ilustrativo para revisar en MT5"
INVITACION_MT5 = "Si quieres, lo revisamos juntos en la plataforma MT5."


def texto_acompanamiento(nombre_activo: str, saludo: str) -> str:
    """El mensaje breve que el ejecutivo reenvía junto al análisis: siempre invita a revisar MT5."""
    hola = f"Hola {saludo}, " if saludo else "Hola, "
    return (f"{hola}te comparto el análisis técnico y fundamental de {nombre_activo}. "
            f"Me gustaría revisarlo contigo en la plataforma MT5: miramos el gráfico, los escenarios y la "
            f"estrategia juntos. ¿Cuándo te acomoda?")
```

En `payload_semanal` cambia `"chip": "ANÁLISIS TÉCNICO DE LA SEMANA"` por `"chip": "ANÁLISIS TÉCNICO"`. En `texto_whatsapp_base` agrega `INVITACION_MT5,` antes de `SEPARADOR, AVISO_PIEZA` (la última línea del `join`):

```python
        f"⏱️ *Temporalidad*: {activo['temporalidad']}",
        SEPARADOR,
        INVITACION_MT5,
        AVISO_PIEZA,
```

- [ ] **Step 4: Implementar en `oportunidad_html.py`**

a) Imports: `from analista import fuentes as fu`.

b) Constante y helpers (junto a `_filas_niveles`):

```python
def _seccion(titulo: str, cuerpo: str) -> str:
    return f'<h4 class="seccion">{ih.e(titulo)}</h4>{cuerpo}'


def _bloque_revision() -> str:
    puntos = "".join(f"<li>{ih.e(p)}</li>" for p in cm.REVISION_MT5_PUNTOS)
    return f'<div class="revision-mt5"><h4>{ih.e(cm.REVISION_MT5_TITULO)}</h4><ul>{puntos}</ul></div>'


def _seccion_voces(fuentes: list[dict[str, Any]], direccion: str) -> str:
    if not fuentes:
        return _seccion("Voces de bancos y prensa",
                        '<p class="sin-voces">Sin voces de bancos o prensa atingentes esta vez.</p>')
    items, hay_discrepancia = [], False
    for f in fuentes:
        discrepa = fu.discrepa(f, direccion)
        hay_discrepancia |= discrepa
        marcas = ((' <span class="marca-discrepa">Discrepa de nuestra lectura</span>' if discrepa else "")
                  + (' <span class="marca-sin-verificar">enlace sin verificar</span>'
                     if f.get("verificacion") == "sin_verificar" else ""))
        items.append(f'<li><strong>{ih.e(f["entidad"])}</strong> · {ih.e(f["medio"])} · {ih.e(f["fecha"])}{marcas}'
                     f'<br>{ih.e(f["tesis"])} <a href="{ih.e(f["url"])}" target="_blank" rel="noopener noreferrer">'
                     'Ver nota</a></li>')
    nota = ('<p class="nota">Estas voces ven distinto que nuestra lectura: la nuestra es la que manda.</p>'
            if hay_discrepancia else "")
    return _seccion("Voces de bancos y prensa", f'<ul class="voces">{"".join(items)}</ul>{nota}')


def _seccion_fundamental(d: dict[str, Any], a: dict[str, Any], contexto: str) -> str:
    t = a["ticker"]
    drivers = d["drivers"].get(t, [])
    cuerpo = f'<p>{ih.e(contexto)}</p>'
    if drivers:
        cuerpo += '<p class="rotulo-chico">Drivers del activo</p><ul>' + "".join(f"<li>{ih.e(x)}</li>" for x in drivers) + '</ul>'
    if d["agenda_semana"]:
        cuerpo += '<p class="rotulo-chico">Agenda de la semana</p><ul>' + "".join(f"<li>{ih.e(x)}</li>" for x in d["agenda_semana"]) + '</ul>'
    if d["curva"]:
        filas = "".join("<tr>" + "".join(f"<td>{ih.e(c)}</td>" for c in fila) + "</tr>" for fila in d["curva"])
        cuerpo += f'<p class="rotulo-chico">Curva de tasas de EE.UU.</p><table class="curva">{filas}</table>'
    if d["fundamental"]["sin_drivers"]:
        cuerpo += '<p class="nota">Este activo no tiene drivers declarados en el catálogo de la casa.</p>'
    return _seccion("Fundamental", cuerpo)
```

c) En `_panel`, antepón el rótulo en el caso con simulación (`cabeza`): cambia `'<h4>Objetivo de la simulación (1:3)</h4>'` por

```python
        f'<p class="rotulo-ilustrativo">{ih.e(cm.ROTULO_ILUSTRATIVO)}</p><h4>Objetivo de la simulación (1:3)</h4>'
```

En `_simulacion_correo`, después de `_rotulo(f"Simulación realizada por {ih.e(ejecutivo)}", c)` suma `+ _p(ih.e(cm.ROTULO_ILUSTRATIVO), c, tam=14, color="texto_2", margen="0 0 8px 0")`.

d) En `_marco_correo`: reemplaza el segundo párrafo de la portada (el que dice «para que los tengas en el radar al evaluar tus próximas operaciones») por:

```python
        + _p("Te escribo para compartirte el análisis técnico y fundamental de esta semana, preparado por la "
             "Dirección de Análisis Técnico de Grupo Inteligencia: la lectura del activo, sus niveles, lo que "
             "puede mover su precio y qué dicen los bancos. Me gustaría revisarlo contigo en la plataforma MT5.",
             c, tam=17, margen="0")
```

Cambia `{ih.e(cm.semana_visible(d["semana"]))}` de la cabecera por `{ih.e(d["vigencia"]["desde"])}` y el rótulo «Análisis de la» por «Análisis del». Inserta el bloque MT5 antes de las firmas (dentro de `firmas = (` como primera fila):

```python
    revision = (
        '<tr><td class="pad" style="padding:6px 40px 0 40px;">'
        + _rotulo(ih.e(cm.REVISION_MT5_TITULO), c)
        + "".join(_p("• " + ih.e(p), c, margen="0 0 6px 0") for p in cm.REVISION_MT5_PUNTOS)
        + '</td></tr>')
```
y concatena `revision` justo antes de `firmas` en el `return` (`cabecera + portada + '<!--ACTIVOS-->' + revision + firmas`).

e) En `armar`: construye la ficha de un activo (el bucle sigue funcionando con la lista de largo 1). Reemplaza el bloque `analisis` (la cadena `f'<div class="analisis"><h3>…</div>'`) por:

```python
            f'<div class="analisis"><h3>{ih.e(ed["titulares"][t])}</h3>'
            + _seccion("Lectura técnica",
                       f'<img src="{ih._data_uri(dir_pedido / a["grafico"])}" alt="Gráfico de {ih.e(a["nombre"])}">'
                       f'<table class="niveles">{_filas_niveles(a)}</table><ul class="escenarios">{escenarios}</ul>'
                       f'<p class="salida">{ih.e(lec["salida"])}</p>'
                       f'<p class="temporalidad">⏱️ {ih.e(a["temporalidad"])} · Foto del {ih.e(a["foto"]["fecha"])}, '
                       f'precio {ih.e(a["fmt"]["precio"])}</p>')
            + _seccion_fundamental(d, a, ed["contexto"][t])
            + _seccion_voces(ed["fuentes"], lec["direccion"])
            + f'<p class="firma-analisis">Análisis: {ih.e(autor.nombre)} · {ih.e(autor.cargo)}</p></div>'
            f'{_panel(a, nombre_ej)}{_bloque_revision()}'
```
(ajusta las comillas/concatenación al estilo del archivo; el `section` abre y cierra como antes).

En `tokens`: `"semana": ih.e(f"Vigente hasta el {d['vigencia']['hasta']}")`. En `guardar`: 

```python
    ruta = dir_pedido / f"analisis_{_slug(pieza['datos']['ticker'])}_{_slug(ejecutivo['nombre'])}.html"
```

f) `templates/oportunidad/pieza.html` línea 78: `<strong>Foto del {{edicion}}</strong>` → `<strong>Análisis del {{edicion}}</strong>`; y agrega al `<style>` (usa los tokens de color existentes):

```css
  .seccion{margin:22px 0 8px;font-size:13px;letter-spacing:1.4px;text-transform:uppercase;color:var(--acento)}
  .voces{list-style:none;margin:0;padding:0}.voces li{margin:0 0 12px;padding:10px 12px;border:1px solid var(--linea);border-radius:10px}
  .marca-discrepa{display:inline-block;margin-left:6px;padding:1px 8px;border-radius:999px;background:var(--fondo-baja);color:var(--baja);font-size:12px;font-weight:700}
  .marca-sin-verificar{margin-left:6px;color:var(--texto-2);font-size:12px}
  .revision-mt5{margin:18px 0 0;padding:14px 16px;border:2px solid var(--acento);border-radius:12px}
  .rotulo-ilustrativo,.rotulo-chico{margin:0 0 6px;color:var(--texto-2);font-size:13px;font-weight:700}
  .sin-voces,.nota{color:var(--texto-2)}
```

- [ ] **Step 5: Correr**

Run: `uv run pytest tests/test_analista_oportunidad_html.py tests/test_analista_comercial.py -q`
Expected: verde. Revisa también que ningún texto nuevo traiga `—`, `–`, «oportunidad» ni «recomendación».

- [ ] **Step 6: Verificación visual**

Genera un HTML con `fx.pieza_oportunidad` en un directorio temporal, ábrelo en el navegador y confirma: las tres secciones, la marca de discrepancia, el rótulo «Ejemplo ilustrativo» y el bloque MT5 al final de la ficha.

- [ ] **Step 7: Commit**

```bash
git add scripts/analista/comercial.py scripts/analista/oportunidad_html.py templates/oportunidad/pieza.html tests/test_analista_oportunidad_html.py tests/test_analista_comercial.py
git commit -m "feat(bot): ficha con secciones fundamental, técnica y voces, e invitación a revisar MT5

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 10: Bot: flujo por activo, reúso, caducidad, candado y ayuda

**Files:**
- Modify: `scripts/analista/bot.py`
- Modify: `tests/test_analista_bot.py`

**Interfaces:**
- Consumes: `rg.vigente/anotar/anotar_reuso/caducar/anotar_seguimiento` (Task 3), `fu.depurar_pieza` (Task 4), `vg.verificar` (Task 8), `sm.buscar` (Task 2), `cm.texto_acompanamiento` (Task 9), `pr.SinAnalisisError` (Task 6).
- Produces: `Atendedor(..., verificar_vigencia=vg.verificar, simbolo=sm.buscar, verificar_url=fu.verificar_url)`; `Bot.generando`; respuesta de `/oportunidad` con `texto` = acompañamiento reenviable y `aparte` = aviso del ejecutivo (quién creó, vigencia, avisos, Drive).

- [ ] **Step 1: Reescribir los tests de `/oportunidad` en `tests/test_analista_bot.py`**

Cambia el `Armado` y los tests (elimina `fuera`, `test_la_foto_reusada_...`, `test_la_foto_se_rehace_...`, `test_oportunidad_rinde_las_laminas_antes_del_html`→adaptar, `test_la_lamina_del_wti...`→adaptar, `test_oportunidad_sin_semana...`, `test_oportunidad_en_espera...`, `test_foto_vacia...`, `test_seguimiento_queda_anotado_...`→adaptar, `test_el_primer_pedido_a_mitad_de_semana...`):

En `Armado.__init__` quita `self.fuera` y agrega los inyectables (todos sin red ni MT5):

```python
        self.caduca: str | None = None
        self.aviso_vigencia: str | None = None
        self.atendedor = b.Atendedor(
            config, b.Estado.cargar(tmp_path / "estado.json"), autor=fx.AUTOR, preparar=self.preparar_falso,
            redactar=redactor(self.llamadas), rendir_lamina=self.rendir_falso, reloj=self.reloj,
            dir_pedidos=tmp_path / "pedidos", registro=self.registro,
            calendario=lambda ahora: self.eventos,
            verificar_vigencia=lambda pieza, ahora: (self.caduca, self.aviso_vigencia),
            simbolo=lambda t: {"ticker": "XAUUSD", "descripcion": "Gold", "digits": 2} if t.lower() == "xauusd" else None,
            verificar_url=lambda url: "ok")
```

y `preparar_falso` para `oportunidad`:

```python
        if orden.pieza == "oportunidad":
            pieza = fx.pieza_oportunidad(dir_pedido)
            pieza["editorial"] = {k: ({t: es.MARCA for t in v} if isinstance(v, dict) else es.MARCA)
                                  for k, v in pieza["editorial"].items()}
```
(el `redactor` ya rellena el editorial con `fx.pieza_oportunidad(...)["editorial"]`, que trae `fuentes`). Define `ORO = od.Orden("oportunidad", {"ticker": "XAUUSD"})` y reemplaza los tests:

```python
def test_oportunidad_se_arma_una_vez_y_el_segundo_ejecutivo_lo_reusa(armado):
    r1 = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    r2 = armado.bot.procesar_uno(b.Pedido(OTRO, 2, ORO))
    assert len(armado.llamadas) == 1 and armado.preparaciones == 1  # agy una sola vez
    assert r1.archivos[0].name.startswith("analisis_xauusd_")
    assert r2.archivos[0].name.endswith("_pedro-soto.html")  # el HTML lleva al ejecutivo que lo pidió
    assert "Camila Rojas" in r2.aparte and "Ya existía" in r2.aparte
    assert armado.estado.usados(CAMILA, AHORA) == 1 and armado.estado.usados(OTRO, AHORA) == 0


def test_el_analisis_queda_a_nombre_de_quien_lo_genero_y_anota_el_reuso(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    armado.bot.procesar_uno(b.Pedido(OTRO, 2, ORO))
    e = rg.vigente("XAUUSD", AHORA, armado.registro)
    assert e["creado_por"] == {"nombre": "Camila Rojas", "id": CAMILA}
    assert [x["nombre"] for x in e["reusos"]] == ["Pedro Soto"]


def test_a_los_8_dias_se_rehace(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    armado.reloj.ahora += timedelta(days=8)
    armado.bot.procesar_uno(b.Pedido(OTRO, 2, ORO))
    assert armado.preparaciones == 2 and len(armado.llamadas) == 2


def test_a_los_6_dias_se_reusa(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    armado.reloj.ahora += timedelta(days=6)
    armado.bot.procesar_uno(b.Pedido(OTRO, 2, ORO))
    assert armado.preparaciones == 1


def test_una_lectura_rota_caduca_el_analisis_y_se_rehace_con_el_motivo(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    armado.caduca = "el precio tocó la invalidación"
    r = armado.bot.procesar_uno(b.Pedido(OTRO, 2, ORO))
    assert armado.preparaciones == 2 and "caducó" in r.aparte and "invalidación" in r.aparte
    assert json.loads(armado.registro.read_text(encoding="utf-8"))[0]["caducada"]["motivo"]


def test_con_el_terminal_caido_se_entrega_el_vigente_con_aviso(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    armado.aviso_vigencia = "No pude verificar si sigue vigente (el terminal no respondió): te lo entrego tal cual."
    r = armado.bot.procesar_uno(b.Pedido(OTRO, 2, ORO))
    assert armado.preparaciones == 1 and "No pude verificar si sigue vigente" in r.aparte


def test_el_texto_reenviable_invita_a_revisar_mt5_con_el_saludo(armado):
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad", {"ticker": "XAUUSD"}, "Juan")))
    assert r.texto.startswith("Hola Juan, ") and "MT5" in r.texto and "operar" not in r.texto.lower()


def test_las_fuentes_malas_se_descartan_y_se_avisan_sin_botar_la_pieza(armado):
    def redactar(ruta, tier):
        pieza = pr.cargar_pieza(ruta.parent)
        pieza["editorial"].update(fx.pieza_oportunidad(ruta.parent)["editorial"])
        pieza["editorial"]["fuentes"] = [fx.FUENTES_EJEMPLO[0], {**fx.FUENTES_EJEMPLO[0], "entidad": "Un Blog",
                                                                 "url": "https://www.reuters.com/otra/nota-larga"}]
        pr.guardar_pieza(pieza, ruta.parent)
        return SimpleNamespace(codigo="ok", detalle="")

    armado.atendedor.redactar = redactar
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert "Un Blog" in r.aparte and r.archivos
    assert len(pr.cargar_pieza(next((armado.tmp / "pedidos").rglob("pieza.json")).parent)["editorial"]["fuentes"]) == 1


def test_sin_voces_validas_la_pieza_sale_y_lo_dice(armado):
    def redactar(ruta, tier):
        pieza = pr.cargar_pieza(ruta.parent)
        pieza["editorial"].update(fx.pieza_oportunidad(ruta.parent)["editorial"])
        pieza["editorial"]["fuentes"] = "no sé"
        pr.guardar_pieza(pieza, ruta.parent)
        return SimpleNamespace(codigo="ok", detalle="")

    armado.atendedor.redactar = redactar
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert r.archivos and "Sin voces" in r.aparte


def test_un_simbolo_libre_se_canoniza_contra_el_terminal(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad", {"ticker": "xauusd", "libre": True})))
    assert rg.vigente("XAUUSD", AHORA, armado.registro) is not None


def test_un_simbolo_que_no_existe_no_gasta_cupo_ni_agy(armado):
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, od.Orden("oportunidad", {"ticker": "orro", "libre": True})))
    assert "orro" in r.texto and armado.llamadas == [] and armado.estado.usados(CAMILA, AHORA) == 0


def test_el_mismo_activo_pedido_dos_veces_a_la_vez_dice_que_ya_se_esta_generando(armado):
    r1 = armado.bot.recibir(update("/oportunidad oro"))
    r2 = armado.bot.recibir(update("/oportunidad oro", usuario=OTRO))
    assert "Armando el análisis" in r1[0].texto and "ya se está generando" in r2[0].texto.lower()
    assert armado.bot.cola.qsize() == 1
    armado.bot.procesar_uno(armado.bot.cola.get())  # al terminar, el candado se suelta
    assert "ya se está generando" not in armado.bot.recibir(update("/oportunidad oro"))[0].texto.lower()


def test_oportunidad_solo_va_a_drive_el_html(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert [p.suffix for p in (armado.tmp / "drive" / "GI Informes").rglob("*.*")] == [".html"]


def test_oportunidad_sin_analisis_de_datos_no_gasta_agy(armado):
    armado.atendedor.preparar = lambda o, d, a, **kw: (_ for _ in ()).throw(
        pr.PreparacionFallida("el terminal no entregó XAUUSD"))
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert "XAUUSD" in r.texto and armado.llamadas == []


def test_seguimiento_queda_anotado_en_el_analisis_vigente(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    armado.bot.procesar_uno(b.Pedido(OTRO, 2, od.Orden("seguimiento", {"ticker": "XAUUSD"})))
    seg = rg.vigente("XAUUSD", AHORA, armado.registro)["seguimientos"]
    assert [(s["ticker"], s["estado"], s["ejecutivo"]) for s in seg] == [("XAUUSD", "en_curso", OTRO)]
```

Adapta también:
- `test_pedido_invalido_responde_el_motivo`: `/seguimiento pizza` ahora responde «Recibido» y el trabajador contesta «No encontré el símbolo»; cambia la aserción a `final.texto` conteniendo "pizza" (con el `simbolo` falso devolviendo `None`) o usa un comando realmente inválido como `/seguimiento` sin activo.
- `test_cupo_diario`: usa `ORO` y dos seguimientos del mismo activo (cambia el segundo a un activo distinto solo si el `preparar_falso` lo acepta).
- `test_preparar_usa_el_registro_del_bot`: parametriza con `ORO` y el seguimiento.
- `test_la_ayuda_*`: la nueva ayuda debe seguir ≤ 14 líneas y traer `/oportunidad oro`, `/seguimiento oro` y `/seguimiento oro Juan`.
- `test_seguimiento_sin_foto_o_fuera_de_ella_...`: parametriza solo con `pr.SinAnalisisError("No hay un análisis vigente de XAUUSD: pide primero /oportunidad XAUUSD.")`.

- [ ] **Step 2: Correr y ver que fallan**

Run: `uv run pytest tests/test_analista_bot.py -q`
Expected: FAIL.

- [ ] **Step 3: Implementar en `bot.py`**

a) Docstring: actualiza «la foto de la semana» a «el análisis de un activo, vigente 7 días». Imports: agrega `from analista import fuentes as fu`, `from analista import simbolos as sm`, `from analista import vigencia as vg` y quita `rs` donde ya no se use.

b) `AYUDA` y `MENU`:

```python
AYUDA = """Bot de análisis · Grupo Inteligencia

1) Análisis completo de un activo (técnico, fundamental y voces de bancos), para abrir en tu navegador:
/oportunidad oro
Con el nombre de tu cliente: /oportunidad oro Juan
Vale 7 días: si ya existe uno vigente, te lo entrego al tiro.

2) Cómo va un activo, con lámina y texto listos para WhatsApp:
/seguimiento oro
Activos: oro, dolar, cobre, petroleo, brent, nasdaq, bitcoin o el símbolo exacto de MT5
Tus pedidos de hoy: /estado"""

MENU = [
    ("oportunidad", "Análisis de un activo (ej: /oportunidad oro)"),
    ("seguimiento", "Cómo va un activo (ej: /seguimiento oro)"),
    ("estado", "Tus pedidos de hoy"),
    ("ayuda", "Cómo se usa"),
]
```
(Revisa que la ayuda no supere 14 líneas; quita la línea «Con el nombre…» de seguimiento solo si hace falta, pero el test exige `/seguimiento oro Juan` en `AYUDA`: añade ese ejemplo en una sola línea.)

c) `Atendedor`: reemplaza `fuera_con_referencia` por los inyectables y agrega la canonización:

```python
    verificar_vigencia: Callable[[dict[str, Any], datetime], tuple[str | None, str | None]] = vg.verificar
    simbolo: Callable[[str], dict[str, Any] | None] = sm.buscar
    verificar_url: Callable[[str], str] = fu.verificar_url
```

```python
    def _canonica(self, orden: od.Orden) -> od.Orden:
        """Un símbolo `libre` se confirma contra el terminal y queda con su nombre exacto."""
        if not orden.args.get("libre"):
            return orden
        crudo = orden.args["ticker"]
        try:
            info = self.simbolo(crudo)
        except sm.TerminalNoDisponible as exc:
            raise FalloPedido(f"No pude consultar el terminal para confirmar «{crudo}»: {exc}. Intenta de nuevo.") from exc
        if info is None:
            raise FalloPedido(f"No encontré el símbolo «{crudo}» en el terminal MT5. Revisa el nombre exacto, "
                              "por ejemplo oro, dolar, cobre o AAPL.US.")
        return od.Orden(orden.pieza, {"ticker": info["ticker"]}, orden.saludo)
```

d) `_preparar`: la tupla de excepciones pasa a `(pr.SinAnalisisError,)`.

e) `_redactar_y_validar` devuelve `(pieza, descartes)`:

```python
    def _redactar_y_validar(self, dir_pedido: Path, hoy) -> tuple[dict[str, Any], list[str]]:
        res = self.redactar(dir_pedido / "pieza.json", self.config["tier"])
        if getattr(res, "codigo", "ok") != "ok":
            raise FalloPedido(f"La redacción no terminó ({res.codigo}: {res.detalle}). No gasté tu cupo.")
        pieza = pr.cargar_pieza(dir_pedido)
        pieza, descartes = fu.depurar_pieza(pieza, hoy, verificar=self.verificar_url)
        pr.guardar_pieza(pieza, dir_pedido)
        errores = es.errores(pieza)
        if errores:
            raise FalloPedido("El texto no pasó los controles y no lo entrego así:\n• " + "\n• ".join(errores[:6]))
        return pieza, descartes
```

f) `atender`: canoniza antes de despachar:

```python
            orden = self._canonica(pedido.orden)
            pedido = replace(pedido, orden=orden)  # from dataclasses import replace
            if orden.pieza == "oportunidad":
                return self._oportunidad(pedido, ahora)
            return self._seguimiento(pedido, ahora)
        except rg.RegistroDanado as exc:
            raise FalloPedido("El registro de análisis está dañado y no sigo para no pisarlo: "
                              "avisa al director.") from exc
```
(ajusta el test `test_un_registro_danado_se_dice_claro` al nuevo texto «registro de análisis está dañado».)

g) Reemplaza `_oportunidad` completo:

```python
    def _oportunidad(self, pedido: Pedido, ahora: datetime) -> Respuesta:
        ticker = pedido.orden.args["ticker"]
        ejecutivo = self.analista(pedido.usuario)
        quien = {"nombre": ejecutivo["nombre"], "id": pedido.usuario}
        previa = rg.vigente(ticker, ahora, self.registro)  # un registro corrupto levanta: no es "sin análisis"
        avisos: list[str] = []
        if previa is not None:
            motivo, aviso = self.verificar_vigencia(pr.cargar_pieza(Path(previa["dir"])), ahora)
            if motivo:
                rg.caducar(ticker, motivo, ahora, self.registro)
                avisos.append(f"El análisis anterior de {ticker} caducó ({motivo}): rehíce uno con la lectura de hoy.")
                previa = None
            elif aviso:
                avisos.append(aviso)
        reusada = previa is not None
        if reusada:
            dir_pedido, pieza = Path(previa["dir"]), pr.cargar_pieza(Path(previa["dir"]))
            rg.anotar_reuso(ticker, quien, ahora, self.registro)
        else:
            self._exigir_cupo(pedido.usuario, ahora)
            dir_pedido = self.dir_pedidos / ahora.strftime("%Y-%m-%d") / f"{ahora:%H%M%S}_oportunidad_{ih.slug(ticker)}"
            hecha = self._preparar(pedido.orden, dir_pedido, ahora)
            pieza, descartes = self._redactar_y_validar(dir_pedido, ahora.date())
            a = pieza["datos"]["activos"][0]
            # La lámina se rinde antes del HTML: sin ella no hay botón «Descargar lámina».
            self.rendir_lamina(
                cm.payload_semanal(a, pieza["editorial"]["titulares"][ticker], pieza["datos"]["edicion"],
                                   self.autor, dir_pedido / a["grafico"]),
                "semanal", dir_pedido / cm.nombre_lamina(ticker))
            rg.anotar(ticker, dir_pedido, ahora, a["lectura"]["direccion"], quien, self.registro)
            self.estado.consumir(pedido.usuario, ahora)
            self.estado.guardar()
            avisos += [*hecha.avisos, *[f"Descarté una fuente: {d}" for d in descartes]]
            if not pieza["editorial"]["fuentes"]:
                avisos.append("Sin voces de bancos o prensa atingentes esta vez: el análisis sale con nuestra lectura.")
        try:
            ruta = oh.guardar(pieza, dir_pedido, ejecutivo, self.autor, ahora.date())
        except oh.InformeInvalido as exc:
            raise FalloPedido(f"No pude armar la pieza: {exc}") from exc
        entrada = rg.vigente(ticker, ahora, self.registro) or {}
        creador = (entrada.get("creado_por") or quien)["nombre"]
        nombre = pieza["datos"]["activos"][0]["nombre"]
        aparte = [f"✅ {pieza['editorial']['titular']}",
                  f"Análisis de {nombre} creado por {creador} · vigente hasta el {pieza['datos']['vigencia']['hasta']}"]
        if reusada:
            aparte.append("Ya existía uno vigente: te lo entrego tal cual, sin gastar tu cupo.")
        aparte.append("Ábrelo en el navegador: marca lo que quieres incluir, escribe la pérdida aceptable y copia el correo.")
        aparte += [f"⚠️ {x}" for x in [*avisos, *au.avisos(self.autor, ahora.date())]]
        aparte.append(self._a_drive([ruta], ahora))
        return Respuesta(pedido.chat, cm.texto_acompanamiento(nombre, pedido.orden.saludo), [ruta], "\n".join(aparte))
```

h) `_seguimiento`: reemplaza el bloque de anotación semanal (`semana = rs.semana_de(ahora)` … `rg.anotar_seguimiento`) por:

```python
            if rg.vigente(o.args["ticker"], ahora, self.registro) is not None:
                rg.anotar_seguimiento(o.args["ticker"],
                                      {"ticker": o.args["ticker"], "estado": d["evaluacion"]["estado"],
                                       "ejecutivo": pedido.usuario, "cuando": ahora.isoformat()}, self.registro)
```
y quita `import referencia_semanal as rs`.

i) `Bot`: candado por activo.

```python
    generando: set[str] = field(default_factory=set)
    candado: threading.Lock = field(default_factory=threading.Lock, repr=False)
```
En `recibir`, antes de `en_cola = ...`:

```python
        if orden.pieza == "oportunidad":
            clave = orden.clave_base().lower()
            with self.candado:
                if clave in self.generando:
                    return [Respuesta(chat, f"Ya se está generando el análisis de {orden.args['ticker']}. Pídelo de "
                                            "nuevo en unos minutos y te llega al tiro.")]
                self.generando.add(clave)
```
y cambia el mensaje final para oportunidad: `"Recibido. Armando el análisis de {ticker}: si ya hay uno vigente te lo entrego al tiro; si no, tarda unos minutos."`. En `procesar_uno`, dentro del `finally`:

```python
            self.ocupado.clear()
            if pedido.orden.pieza == "oportunidad":
                with self.candado:
                    self.generando.discard(pedido.orden.clave_base().lower())
```

- [ ] **Step 4: Correr**

Run: `uv run pytest tests/test_analista_bot.py -q`
Expected: todo en verde, incluido `test_el_bot_no_puede_publicar_en_whatsapp`.

- [ ] **Step 5: Commit**

```bash
git add scripts/analista/bot.py tests/test_analista_bot.py
git commit -m "feat(bot): /oportunidad por activo con reúso de 7 días, caducidad y candado

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 11: Instrucciones de agy (`/analista`) con búsqueda web y sin invitar a operar

**Files:**
- Modify (reescribir): `.claude/commands/analista.md`
- Create: `tests/test_analista_instrucciones.py`

**Interfaces:**
- Consumes: campos de `editorial` (Task 5) y la lista de fuentes (Task 4).

- [ ] **Step 1: Escribir el test de contrato**

```python
"""Las instrucciones de agy dicen lo que el validador exige: un test que los ata."""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import fuentes as fu  # noqa: E402

TEXTO = (RAIZ / ".claude" / "commands" / "analista.md").read_text(encoding="utf-8")


def test_nombra_cada_campo_de_la_fuente():
    for campo in fu.CAMPOS:
        assert f"`{campo}`" in TEXTO


def test_permite_la_web_solo_para_las_fuentes():
    assert "búsqueda web" in TEXTO.lower() or "busca en la web" in TEXTO.lower()
    assert "no uses la web" not in TEXTO.lower()


def test_ya_no_manda_invitar_a_operar_y_lo_prohibe():
    bajo = TEXTO.lower()
    assert "invita a operar el escenario" not in bajo
    assert "nunca invites a operar" in bajo


def test_pide_revisar_la_plataforma_y_no_pone_cifras_de_bancos_sin_atribucion():
    assert "revisar" in TEXTO.lower() and "atribu" in TEXTO.lower()


def test_enumera_las_entidades_de_la_lista_cerrada():
    lista = fu.cargar_lista()
    assert all(e in TEXTO for e in ("Goldman Sachs", "Banco Central de Chile", "Fed"))
    assert len(lista["medios"]) > 10  # la lista real vive en config/fuentes_prestigio.json
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `uv run pytest tests/test_analista_instrucciones.py -q`
Expected: FAIL.

- [ ] **Step 3: Reescribir `.claude/commands/analista.md`**

Contenido completo del archivo:

````markdown
Redacta los textos del análisis de un activo del bot de analistas. Escribe texto en `pieza.json`: no ejecuta pipelines, no rinde imágenes y no envía nada. La única herramienta externa que usas es la búsqueda web, solo para encontrar las fuentes de `fuentes`.

## /analista — textos del análisis de un activo

**Argumento:** `$ARGUMENTS` es la ruta de un `pieza.json` dentro de `data/informes_analistas/`.
Si no es una ruta así, detente y responde `ERROR: ruta inválida`.

Lo invoca el bot de Telegram (`scripts/bot_analistas.py`). El bot ya leyó el terminal, armó los
datos y rindió el gráfico; tu tarea es redactar y encontrar voces de prestigio. La maqueta es fija
y la pone el bot: tú no decides nada visual.

### Qué puedes tocar

- **Solo** los valores de `editorial` que hoy dicen exactamente `[[ESCRIBIR]]`, incluidos los
  de `editorial.titulares` y `editorial.contexto` (uno por ticker) y `editorial.fuentes`.
- **Nunca** `orden`, `datos`, `imagenes`, `anidados`, `laminas` ni `huella`. Están sellados: si
  cambian, la pieza se descarta entera.
- **Nunca** agregues ni quites claves de `editorial`.
- **Ningún otro archivo** del repo. No corras pipelines ni llames al MCP. Usa la web solo para `fuentes`.

### Reglas del texto (de `.agents/rules/proyecto.md`, que manda ante cualquier duda)

1. **Cada cifra sale de `datos`.** No escribas un precio, nivel, porcentaje o dato que no esté en
   `datos`, ni lo redondees a otro valor. El bot rechaza cualquier número con decimales o de tres o
   más dígitos que no encuentre ahí. **Única excepción:** una cifra de un banco o medio que
   aparezca en la `tesis` de una de tus fuentes y que atribuyas a esa entidad en la misma frase
   («Goldman Sachs ve el oro en 4.800 dólares»). Una cifra de tercero sin atribución se rechaza.
2. **Solo afirmas lo medido.** `datos.drivers.<ticker>` trae los drivers del catálogo, `datos.agenda_semana`
   la agenda y `datos.curva` la curva de tasas con sus cambios en puntos base. Un driver se afirma
   como hecho solo si está ahí; si no, se explica como mecanismo condicional. Nunca inventes que el
   dólar, el petróleo o cualquier otro activo "sube" o "se debilita".
3. **Nuestra lectura manda.** La dirección sale de `datos.activos[0].lectura.direccion` (ALCISTA, BAJISTA
   o LATERAL) y el texto la sostiene. Si un banco ve distinto, lo dices abiertamente ("Goldman Sachs ve
   alza; nuestra lectura de los gráficos apunta a la baja"), sin ablandar nuestra lectura.
4. **Español de Chile, tuteo neutro.** Nada de voseo. Tono cercano y pedagógico, sin dramatizar.
5. **Sin guion largo ni medio** (`—`, `–`) como inciso: usa punto, coma o dos puntos.
6. **Sin HTML, sin Markdown, sin asteriscos.** Texto plano. Listas con `• `, párrafos separados por una línea en blanco.
7. **Siglas explicadas en línea** la primera vez.
8. **Largos:** `titular` hasta 70 caracteres; `bajada` hasta 160; `titulares.<ticker>` hasta 70.
9. **Eventos futuros en modo anticipación** ("el mercado espera"), nunca en pasado.
10. **Nunca invites a operar.** Por regulación, nadie en GI está inscrito como asesor de inversión.
    No escribas "opera", "operar", "operable", "compra", "vende", "entra" ni "aprovecha", ni ninguna
    instrucción personal ni cuánto arriesgar. El bot rechaza esas formas. El cierre comercial
    (revisar la plataforma MT5 con el cliente) lo agrega el bot; tú no lo escribes.
11. **Soporte y resistencia**, nunca "piso", "suelo" ni "techo" para un nivel de precio.

### Qué va en cada campo

`orden.pieza` dice qué pieza es. Solo `oportunidad` pasa por ti: el seguimiento lo escribe Python.

- `titular` y `bajada`: el activo, su dirección y la idea central, sin prometer resultados ni la
  palabra "oportunidad".
- `titulares.<ticker>`: la idea del activo con su dirección.
- `contexto.<ticker>`: 2 o 3 frases con los drivers (`datos.drivers`, `datos.agenda_semana`), como
  mecanismo condicional si no hay un hecho medido, y una frase final que cierre con la lectura:
  qué se vigila y qué la invalida (están en `datos.activos[0].lectura`). Sin `%`, sin repetir los
  niveles (los pone la maqueta).
- `fuentes`: **una lista** (puede ir vacía) de 3 a 5 voces de prestigio sobre este activo. Búscalas en
  la web. Cada elemento es un objeto con estos campos de texto:
  - `entidad`: quién opina. **Solo** de la lista cerrada: Goldman Sachs, JPMorgan, Morgan Stanley, Bank of America,
    Citi, UBS, Barclays, Standard Chartered, Jefferies, Deutsche Bank, HSBC, ING, Commerzbank, Banco Central de
    Chile, Cochilco, Banchile, BCI Estudios, Santander Chile, Itaú Chile, Fed, BCE, EIA, OPEP, FMI, BIS,
    World Gold Council, Agencia Internacional de Energía.
  - `medio`: dónde se publicó. Reuters, Bloomberg, Financial Times, WSJ, CNBC, MarketWatch, Kitco, FXStreet,
    Diario Financiero, La Tercera, o el nombre de la propia entidad si es su sitio. Investing.com no vale.
  - `fecha`: AAAA-MM-DD, de los últimos 14 días.
  - `url`: https y de un artículo concreto (no una portada), del dominio del `medio`.
  - `postura`: `alcista`, `bajista` o `neutral`, la de la entidad frente al activo.
  - `tesis`: una frase en español con lo que la entidad sostiene.
  No inventes URLs ni fuentes: el bot abre cada URL y descarta lo que no responde. Si no encuentras nada
  atingente, deja `fuentes` como lista vacía `[]`. No rellenes.

### Antes de terminar

Corre la validación y corrige hasta que diga `OK`:

```bash
uv run python scripts/bot_analistas.py --validar $ARGUMENTS
```

Responde solo `OK` o `ERROR: <motivo>`.
````

(La `--validar` revisa estructura y cifras; la verificación de URLs la hace el bot después, sin red en `--validar`.)

- [ ] **Step 4: Correr**

Run: `uv run pytest tests/test_analista_instrucciones.py -q && uv run python scripts/agy_workflows.py --check`
Expected: verde; el `--check` no cambia (`/analista` no se expone a AGY).

- [ ] **Step 5: Commit**

```bash
git add .claude/commands/analista.md tests/test_analista_instrucciones.py
git commit -m "feat(bot): instrucciones de agy con búsqueda web de fuentes y sin invitar a operar

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 12: Documentación

**Files:**
- Modify: `docs/bot-analistas.md`

- [ ] **Step 1: Leer el documento y actualizar lo que cambió**

Lee `docs/bot-analistas.md` completo. Reescribe las secciones que describen la foto semanal de seis activos para que digan, con los mismos títulos si existen:

- `/oportunidad <activo>`: análisis de un activo del terminal MT5; técnico (estrategia activa), fundamental (drivers, agenda, curva) y voces de bancos y prensa citadas con entidad, medio, fecha y enlace.
- **Vigencia y reúso:** 7 días corridos, a nombre de quien lo generó, reusado por cualquiera sin gastar agy ni cupo; caducidad anticipada si la lectura se rompe (estructura, invalidación u objetivo); el análisis caducado queda en `data/semanal/registro.json` con su motivo.
- **Fuentes:** `config/fuentes_prestigio.json` (lista cerrada que edita el director), validaciones (entidad, dominio del medio, 14 días, https con ruta de artículo, GET de la URL) y la regla de cifras de terceros atribuidas.
- **Invitación comercial:** la pieza invita a revisar la plataforma MT5 con el cliente y no a operar (regulación, 2026-10-16); panel de simulación rotulado «Ejemplo ilustrativo para revisar en MT5».
- **Símbolos:** cualquier símbolo del terminal; fuera del catálogo se usa el `description` de MT5 y un marco genérico.
- **Seguimiento:** mide contra el análisis vigente del activo; sin él, «pide primero /oportunidad <activo>».
- **Candado por activo y timeout** (valor medido en la Task 1).

- [ ] **Step 2: Verificar que el doc no promete lo que no existe**

Run: `uv run pytest tests -q -k "analista" 2>&1 | tail -5`
Expected: verde.

- [ ] **Step 3: Commit**

```bash
git add docs/bot-analistas.md
git commit -m "docs(bot): /oportunidad por activo, vigencia, fuentes e invitación a MT5

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 13: Verificación completa y corrida real

**Files:** ninguno (solo verificación).

- [ ] **Step 1: Suite completa del bot y contratos del repo**

```bash
uv run pytest tests -q -x 2>&1 | tail -15
```
Expected: verde. Si falla un test ajeno (guardianes de nombres, `test_extras_declarados`, `agy_workflows --check`), léelo antes de tocar nada: puede ser un contrato legítimo que este cambio rompió (por ejemplo un barrido que busca «oportunidad» o guiones largos en textos nuevos).

- [ ] **Step 2: Barrido de texto de cliente**

```bash
grep -rnP "[—–]" scripts/analista/comercial.py scripts/analista/oportunidad_html.py scripts/analista/fuentes.py templates/oportunidad/pieza.html || echo "sin guiones largos"
grep -rni "oportunidad" scripts/analista/comercial.py templates/oportunidad/pieza.html | grep -v "^.*#" | head
```
Expected: «sin guiones largos» (usa `grep -P` con locale UTF-8 si Git Bash se queja) y ninguna aparición de «oportunidad» en texto que lee el cliente.

- [ ] **Step 3: Corrida real de extremo a extremo (con MT5 abierto y la cuenta declarada)**

```bash
MSYS_NO_PATHCONV=1 uv run --with MetaTrader5 --extra stories --extra informe python scripts/bot_analistas.py --una "/oportunidad oro" --usuario <id del director>
```
Mide el tiempo total. Revisa el HTML generado: las tres secciones, cada enlace de las voces abre un artículo real, la discrepancia está marcada si la hay, el bloque MT5 cierra la ficha y el correo, y el panel dice «Ejemplo ilustrativo para revisar en MT5». Repite el mismo pedido: debe devolver el mismo análisis al instante, con «Ya existía uno vigente». Corre también `--una "/oportunidad <un símbolo fuera del catálogo>"`.
Si el tiempo total se acerca al `TIMEOUT` de la Task 1 (más del 70 %), súbelo y repite el commit de esa task.

- [ ] **Step 4: Revisión del director**

Muéstrale al director la ficha generada (ruta del HTML) y pídele el visto bueno antes del PR.

- [ ] **Step 5: PR**

```bash
git push -u origin feat/oportunidad-por-activo
gh pr create --title "feat(bot): /oportunidad por activo con vigencia de 7 días y voces de bancos" --body "$(cat <<'EOF'
## Qué cambia
- `/oportunidad <activo>` analiza un activo del terminal MT5 (técnico, fundamental y voces citadas), guardado a nombre de quien lo generó y reutilizable 7 días.
- Caducidad anticipada si la lectura se rompe; candado por activo; símbolos fuera del catálogo con el nombre del terminal.
- Fuentes de bancos y prensa validadas por Python (lista cerrada, dominio, frescura, URL).
- La pieza invita a revisar la plataforma MT5 con el cliente, no a operar (regulación).

Spec: docs/superpowers/specs/2026-10-16-oportunidad-por-activo-design.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

---

## Self-Review

**Cobertura del spec**

| Sección del spec | Task |
|---|---|
| §1 Qué se pide (técnico, fundamental, voces; nuestra lectura manda) | 6, 9, 11 |
| §2 Vigencia 7 días, reúso, `creado_por`, reúsos anotados | 3, 10 |
| §2 Caducidad anticipada y aviso con terminal caído | 8, 10 |
| §2 `/seguimiento` contra el análisis vigente | 7 |
| §3 Pedido con activo, universo del terminal, nombre de `description` | 2, 6 |
| §4 Referencia semanal o lectura propia sin escribir en `referencias_semanales/` | 6 |
| §5 Registro por activo, legado de solo lectura, `RegistroDanado` | 3 |
| §6 Datos sellados (`fundamental`) | 6 (nota: el bloque `fundamental` guarda solo `fuera_catalogo`/`sin_drivers`/`referencia`; drivers, agenda y curva ya viven en `datos` y no se duplican) |
| §7 Fuentes: entidad/medio, lista, frescura, URL, cifras atribuidas, postura y discrepancia, sin fuentes | 4, 5, 9, 11 |
| §8 Salida: secciones, panel ilustrativo | 9 |
| §9 Fallas, timeout, mensaje inmediato, candado | 1, 10 |
| §10 Pruebas de contrato | dentro de cada task |
| §11 Cierre regulatorio: bloque fijo, texto de acompañamiento, prohibición a agy, panel | 5, 9, 10, 11 |

**Escaneo de placeholders:** los únicos marcadores a completar son `<N>`, `<T1>`, `<T2>` (Task 1, salen de la medición real) e `<id del director>` (Task 13).

**Consistencia de tipos:** `rg.vigente/anotar/anotar_reuso/caducar/anotar_seguimiento(ticker, ...)`, `fu.depurar_pieza -> (pieza, descartes)`, `vg.verificar -> (motivo, aviso)`, `Atendedor.verificar_vigencia(pieza, ahora)`, `Lectores.lectura_actual(...) -> (lectura, velas)` y `Lectores.referencia(...) -> (lectura, guardada, origen)` se usan con la misma firma en las Tasks 3, 4, 6, 7, 8 y 10. `SinAnalisisError` reemplaza a todas las excepciones de la foto en las Tasks 6, 7 y 10.

**Riesgos conocidos** (para quien ejecute): (1) varios tests existentes de HTML y bot asumen seis activos; las tasks 5, 9 y 10 dicen cuáles reemplazar, pero el ejecutor debe correr la suite completa y adaptar los que queden; (2) la verificación de URL hace red real en producción, así que todos los tests inyectan `verificar`; (3) la `tesis` no se contrasta contra el contenido de la página (solo la URL): una cifra inventada dentro de una `tesis` pasa; mitiga la regla de que la cifra se rechaza fuera de la `tesis` y que el director edita la lista de entidades.
