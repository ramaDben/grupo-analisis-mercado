# `/oportunidad`: texto concreto, fechado y con bancos. Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el análisis de `/oportunidad <activo>` deje de ser genérico: Python mide el estado de hoy de los drivers (Dollar Index, tasa real, bono a 10 años, tasa de la Fed, cobre, petróleo) y la agenda de los 7 días de vigencia (con imagen del calendario), agy los redacta citándolos y suma 2 o 3 bancos con enlace, y una pieza sin al menos un banco vigente no sale.

**Architecture:** Dos módulos nuevos de medición pura (`analista/agenda.py`, `analista/hechos.py`) alimentan `preparar_oportunidad`, que sella `datos.hechos`, `datos.agenda` y la imagen `calendario_<slug>.png`. `esquema.errores` exige que `contexto` cite hechos y que `dias_clave` (campo anidado nuevo) nombre un día de la agenda. El mínimo de un banco se impone en `bot_analistas --validar` (lo que agy corre) y en el bot, con un segundo intento solo de fuentes. La ficha y el correo muestran los hechos, los días clave y los bancos con enlace.

**Tech Stack:** Python 3 (paquete `scripts/analista/`), pytest vía `uv run`, MetaTrader5 (lectura de `USDIDX`, `COPPER`, `WTI.spot` D1), calendario de Investing.com (`market_data_mcp.tools.calendar`), `story_render` + Playwright (lámina del calendario), agy (`agy_encargo.invocar`).

**Spec:** `docs/superpowers/specs/2026-10-17-oportunidad-texto-concreto-design.md`. Los ejecutores leen spec y plan; ante una contradicción manda el spec.

## Global Constraints

- **Regla 1:** ninguna cifra se escribe a mano. Toda cifra de un texto de agy tiene que estar en `datos` (salvo la de un tercero atribuido en la misma frase). Los hechos y la agenda los mide Python; agy no busca en la web nada que no sea para `fuentes`.
- **Texto de cliente** (ficha, correo, lámina, avisos al ejecutivo, textos fijos nuevos): español de Chile con tuteo, sin voseo, **sin `—` ni `–`**, "soporte/resistencia" (nunca piso/techo/suelo), sin "oportunidad" ni "recomendación", sin `%` (se escribe "por ciento").
- **Regulación:** nada invita a operar; se invita a revisar la plataforma MT5. `comercial.INVITACION_ACTIVA` de `/seguimiento` **no se toca**.
- **agy solo redacta.** `orden`, `datos`, `imagenes`, `anidados` y `laminas` van sellados (`esquema._huella`). Python decide qué se mide, qué se muestra y si la pieza sale.
- **El bot nunca toca el envío a WhatsApp** (`tests/test_analista_bot.py::test_el_bot_no_puede_publicar_en_whatsapp`): ningún archivo de `scripts/analista/` puede contener `enviar_whatsapp`, `whatsapp_sender`, `--despachar`, `despachar(`, `bitacora_despachos`, `historial_despachos`.
- **Piezas anteriores se siguen rearmando.** Un análisis creado antes de este cambio se reusa hasta 7 días: la ficha y `esquema.errores` tienen que aceptarlo sin `hechos` ni `agenda` (tiene `agenda_semana`) y sin bancos.
- **Vigencia 7 días**, sin cambios. **Timeout:** `agy.TIMEOUT = "25m"` (redacción) y `agy.TIMEOUT_REINTENTO = "15m"` (solo fuentes); la Task 11 los revisa con una corrida real.
- **Ramas:** trabajar en `feat/oportunidad-por-activo` (no cambiar de rama). **Nunca `git add -A` ni `git add .`**: hay archivos de datos modificados ajenos a este trabajo; agrega cada archivo por su ruta. Cada commit termina con `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- **Archivos con acentos** por Write/Edit o Python (`encoding="utf-8"`), nunca `Set-Content` ni tuberías de PowerShell.
- **Suite verde entre tasks:** al cerrar cada task corre `uv run pytest tests/test_analista_*.py tests/test_calendar.py -q` y debe pasar entera.

## Review Focus

Entradas que el spec no menciona y que más probablemente muerdan (cada una con su test):

1. **Investing.com cae y devuelve la caché vieja sin avisar** (hoy el `nextWeek` en disco es del 2 de octubre): la agenda tiene que salir `sin_calendario`, no `vacia`. → Task 2.
2. **Un sábado o domingo**, el último cierre del DXY es del viernes: el hecho lleva esa fecha y `en_curso: false`, para que nadie escriba "hoy" sobre un dato de ayer. → Task 3.
3. **agy cumple el mínimo de hechos citando una cifra cualquiera de `datos`** (el precio del activo): solo cuentan las cifras del `nivel` o de los cambios de cada hecho. → Task 5.
4. **El segundo intento borra los textos ya escritos** o agy reescribe todo: Python reabre solo `fuentes` y el test verifica que el resto llegó escrito. → Task 8.
5. **Un análisis viejo reusado durante la semana** (sin `hechos`, sin bancos, con `agenda_semana`) no puede romperse al rearmar la ficha. → Task 6 y Task 8.

---

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `src/market_data_mcp/tools/calendar.py` | `cargar_calendario(..., pestanas=)`: varias pestañas, sin repetir eventos | Modificar |
| `scripts/analista/agenda.py` | Agenda de la ventana de 7 días: dos pestañas, tres estados, efecto del glosario, payload de la lámina | Crear |
| `scripts/analista/hechos.py` | Medir los drivers del día (MT5 y curva), su efecto y si acompañan nuestra lectura | Crear |
| `config/fuentes_prestigio.json` | `cuentan_como_banco` | Modificar |
| `scripts/analista/fuentes.py` | `bancos`, `falta_banco`, `guardar_intento` | Modificar |
| `scripts/analista/esquema.py` | `dias_clave`, `hechos_citados`, exigencias de desarrollo | Modificar |
| `tests/analista_fixtures.py` | Pieza de ejemplo con hechos, agenda y `dias_clave`; variante de legado | Modificar |
| `scripts/analista/oportunidad_html.py` + `templates/oportunidad/pieza.html` | Ficha y correo: hechos, días clave con imagen, bancos con enlace | Modificar |
| `scripts/analista/preparar.py` | Cablear agenda, hechos y lámina del calendario | Modificar |
| `scripts/analista/agy.py` | `timeout` por llamada y `TIMEOUT_REINTENTO` | Modificar |
| `scripts/analista/bot.py` | Mínimo de un banco, segundo intento, salida de agy guardada | Modificar |
| `scripts/bot_analistas.py` | `--validar` exige un banco | Modificar |
| `.claude/commands/analista.md` | Citar hechos, `dias_clave`, bancos obligatorios, segundo intento | Modificar |
| `docs/bot-analistas.md` | Documentación del bot | Modificar |

**Fuera de alcance (spec §9):** `pipeline_linkedin.leer_agenda` (mismo defecto de pestaña única), la curva en vivo, fechas del FOMC fuera de la ventana, el diferencial BCCh contra Fed y el texto de WhatsApp.

---

### Task 1: El calendario puede pedir varias pestañas

**Files:**
- Modify: `src/market_data_mcp/tools/calendar.py:256-297`
- Test: `tests/test_calendar.py` (agregar al final)

**Interfaces:**
- Produces: `cargar_calendario(solo_hoy=True, min_impact="medium", ahora=None, pestanas=("thisWeek",))`. Con varias pestañas junta los eventos sin repetir `(hora_servidor, pais, nombre)`; devuelve `{"error": "NO_CALENDAR_FEEDS", ...}` solo si **todas** fallan.
- Consumes (Task 2): `agenda.leer_ventana` la llama una vez por pestaña.

- [ ] **Step 1: Escribir los tests**

Agrega al final de `tests/test_calendar.py`:

```python
# ── pestañas (spec 2026-10-17 §3) ─────────────────────────────────────────────

def test_por_defecto_pide_solo_la_semana_en_curso(monkeypatch):
    pedidas = []
    monkeypatch.setattr(calendar, "_fetch_calendario", lambda tab: pedidas.append(tab) or _fila())
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: _GLOSARIO_TEST)
    calendar.cargar_calendario(solo_hoy=False, min_impact="low")
    assert pedidas == ["thisWeek"]


def test_dos_pestanas_se_juntan_sin_repetir_eventos(monkeypatch):
    def fetch(tab):
        comun = _fila(row_id=1)  # la misma fila en las dos pestañas
        extra = _fila(row_id=2, nombre="Nonfarm Payrolls", pais="United States", divisa="USD", dias_offset=3)
        return comun + (extra if tab == "nextWeek" else "")

    monkeypatch.setattr(calendar, "_fetch_calendario", fetch)
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: _GLOSARIO_TEST)
    res = calendar.cargar_calendario(solo_hoy=False, min_impact="low", pestanas=("thisWeek", "nextWeek"))
    assert sorted(e["nombre"] for e in res["eventos"]) == ["Core CPI (MoM) (May)", "Nonfarm Payrolls"]


def test_una_pestana_caida_no_tumba_la_otra(monkeypatch):
    monkeypatch.setattr(calendar, "_fetch_calendario", lambda tab: "" if tab == "thisWeek" else _fila())
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: _GLOSARIO_TEST)
    res = calendar.cargar_calendario(solo_hoy=False, min_impact="low", pestanas=("thisWeek", "nextWeek"))
    assert "error" not in res and len(res["eventos"]) == 1


def test_todas_las_pestanas_caidas_es_error(monkeypatch):
    monkeypatch.setattr(calendar, "_fetch_calendario", lambda tab: "")
    res = calendar.cargar_calendario(solo_hoy=False, pestanas=("thisWeek", "nextWeek"))
    assert res["error"] == "NO_CALENDAR_FEEDS"
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `uv run pytest tests/test_calendar.py -q`
Expected: FAIL (`cargar_calendario() got an unexpected keyword argument 'pestanas'`).

- [ ] **Step 3: Implementar**

En `src/market_data_mcp/tools/calendar.py`, cambia la firma de `cargar_calendario` agregando el parámetro al final:

```python
def cargar_calendario(
    solo_hoy: bool = True,
    min_impact: str = "medium",
    ahora: datetime | None = None,
    pestanas: tuple[str, ...] = ("thisWeek",),
) -> dict[str, Any]:
```

agrega al final del docstring:

```python
    `pestanas` elige qué semanas de Investing.com se piden (`thisWeek`, `nextWeek`). La semana va
    de domingo a sábado: un análisis de 7 días creado un sábado vive entero en `nextWeek`
    (spec 2026-10-17 §3). Una pestaña caída no tumba las otras; el error es solo si caen todas.
```

y reemplaza el bloque desde `try:` (el que llama a `_fetch_calendario("thisWeek", ahora=ahora)`) hasta `todos = _parsear_filas(html)` inclusive por:

```python
    todos: list[dict] = []
    vistos: set[tuple[str, str, str]] = set()
    respondio = False
    for tab in pestanas:
        try:
            html = _fetch_calendario(tab, ahora=ahora)
        except TypeError:
            html = _fetch_calendario(tab)
        respondio = respondio or bool(html)
        for ev in _parsear_filas(html) if html else []:
            clave = (ev["hora_servidor"], ev["pais"], ev["nombre"])
            if clave not in vistos:
                vistos.add(clave)
                todos.append(ev)
    if not respondio:
        return {
            "error": "NO_CALENDAR_FEEDS",
            "message": (
                "Investing.com no respondió y no hay caché local. "
                "Usar WebSearch investing.com como fallback."
            ),
        }
```

El resto de la función (`umbral = ...` en adelante) no cambia.

- [ ] **Step 4: Correr los tests**

Run: `uv run pytest tests/test_calendar.py tests/test_analista_macro_seguimiento.py tests/test_screener_gi.py -q`
Expected: todo `passed`.

- [ ] **Step 5: Commit**

```bash
git add src/market_data_mcp/tools/calendar.py tests/test_calendar.py
git commit -m "feat(calendario): cargar_calendario puede pedir varias pestañas

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: La agenda de la ventana de 7 días

**Files:**
- Create: `scripts/analista/agenda.py`
- Test: `tests/test_analista_agenda.py` (crear)

**Interfaces:**
- Consumes: `cargar_calendario(solo_hoy, min_impact, ahora, pestanas)` (Task 1); `macro_seguimiento.CLAVE_DEL_ACTIVO` y `_el`; `pipeline_informe._cifra_es`.
- Produces:
  - `agenda.dia_corto(momento: date | datetime) -> str` («sábado 17/10»).
  - `agenda.Agenda(desde, hasta, estado, eventos, avisos)` con `.a_dict() -> {"desde","hasta","estado","eventos","url"}`; `estado` ∈ `ok | vacia | sin_calendario`.
  - `agenda.leer_ventana(ahora, ticker, nombre, cargar=None, dias=7) -> Agenda`. Cada evento: `fecha, dia, hora, evento, fuente_nombre, pais, anterior, esperado, explicacion, efecto, mueve_al_activo`.
  - `agenda.payload_lamina(agenda: dict) -> dict` (payload de la plantilla `calendario`).
  - `agenda.texto_vacia(agenda: dict) -> str`, `agenda.URL_CALENDARIO`.

- [ ] **Step 1: Escribir los tests**

`tests/test_analista_agenda.py`:

```python
"""La agenda de la ventana de un análisis: dos pestañas, tres estados y el efecto del glosario."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import agenda as ag  # noqa: E402
from analista import preparar as pr  # noqa: E402

SCL = ZoneInfo("America/Santiago")
SABADO = datetime(2026, 10, 17, 11, 7, tzinfo=SCL)


def ev(hora, nombre="CPI (MoM) (Sep)", impacto="alto", efecto_oro="baja", forecast="0.3%", previo="0.4%"):
    dic = {"nombre_es": "Índice de precios al consumidor (IPC)", "explicacion": "Mide la inflación."}
    if efecto_oro:
        dic["si_sale_sobre_consenso"] = {"oro": efecto_oro}
    return {"nombre": nombre, "pais": "United States", "impacto": impacto, "hora_servidor": hora,
            "forecast": forecast, "previo": previo, "diccionario": dic}


def cargador(por_pestana):
    pedidas = []

    def cargar(solo_hoy, min_impact, ahora, pestanas):
        pedidas.append((pestanas, min_impact))
        res = por_pestana[pestanas[0]]
        return res if isinstance(res, dict) else {"source": "investing", "eventos": res}

    cargar.pedidas = pedidas
    return cargar


def test_un_sabado_la_ventana_sale_de_la_semana_siguiente():
    cargar = cargador({
        "thisWeek": [ev("2026-10-16 09:30"), ev("2026-10-17 08:00", impacto="bajo")],
        "nextWeek": [ev("2026-10-21 09:30"), ev("2026-10-26 09:30"), ev("2026-10-20 10:00", impacto="medio")],
    })
    a = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargar)
    assert a.estado == "ok" and (a.desde, a.hasta) == ("sábado 17/10", "sábado 24/10")
    assert [e["dia"] for e in a.eventos] == ["miércoles 21/10"]
    e = a.eventos[0]
    assert e["hora"] == "09:30 CLST" and e["evento"] == "Índice de precios al consumidor (IPC)"
    assert e["pais"] == "EE.UU." and e["anterior"] == "0,4%" and e["esperado"] == "0,3%"
    assert [p for p, _ in cargar.pedidas] == [("thisWeek",), ("nextWeek",)]
    assert all(m == "low" for _, m in cargar.pedidas)  # todo el calendario: así se detecta la copia vieja


def test_el_efecto_sale_del_glosario():
    cargar = cargador({"thisWeek": [], "nextWeek": [ev("2026-10-21 09:30"),
                                                     ev("2026-10-22 09:30", nombre="X", efecto_oro=None)]})
    a = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargar)
    con, sin = a.eventos
    assert "el oro tiende a bajar" in con["efecto"] and con["mueve_al_activo"] is True
    assert sin["efecto"] == "" and sin["mueve_al_activo"] is False


def test_sin_datos_de_alto_impacto_la_ventana_queda_vacia_con_sus_fechas():
    cargar = cargador({"thisWeek": [ev("2026-10-17 12:00", impacto="bajo")],
                       "nextWeek": [ev("2026-10-21 09:30", impacto="medio")]})
    a = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargar)
    assert a.estado == "vacia" and a.eventos == []
    texto = ag.texto_vacia(a.a_dict())
    assert "sábado 17/10" in texto and "sábado 24/10" in texto and "—" not in texto


def test_una_copia_vieja_de_la_semana_siguiente_no_cuenta():
    """`_fetch_calendario` devuelve la caché vencida sin avisar: se reconoce por sus fechas."""
    cargar = cargador({"thisWeek": [ev("2026-10-16 09:30")], "nextWeek": [ev("2026-10-07 09:30")]})
    a = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargar)
    assert a.estado == "sin_calendario" and any("copia vieja" in x for x in a.avisos)


def test_el_calendario_caido_se_dice():
    caido = {"error": "NO_CALENDAR_FEEDS", "message": "x"}
    a = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargador({"thisWeek": caido, "nextWeek": caido}))
    assert a.estado == "sin_calendario" and len(a.avisos) == 2


def test_con_una_semana_caida_y_datos_en_la_otra_sale_con_aviso():
    caido = {"error": "NO_CALENDAR_FEEDS", "message": "x"}
    a = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargador({"thisWeek": caido,
                                                                 "nextWeek": [ev("2026-10-21 09:30")]}))
    assert a.estado == "ok" and a.avisos


def test_dia_corto_es_el_formato_de_preparar():
    assert ag.dia_corto(SABADO) == pr.fecha_corta(SABADO) == "sábado 17/10"


def test_la_lamina_pone_primero_lo_que_mueve_al_activo_y_rinde_sin_huerfanos():
    from story_render import build_html

    eventos = [ev(f"2026-10-{d} 09:30", nombre=f"E{d}", efecto_oro=None) for d in range(19, 24)]
    eventos += [ev("2026-10-23 12:00", nombre="CPI A"), ev("2026-10-24 08:00", nombre="CPI B")]
    a = ag.leer_ventana(SABADO, "XAUUSD", "Oro", cargar=cargador({"thisWeek": [], "nextWeek": eventos}))
    payload = ag.payload_lamina(a.a_dict())
    # Siete eventos y caben seis: entran los dos que mueven al oro (23 y 24) y cae el último de los
    # otros (E23); después van en orden de calendario.
    assert [e["dia"] for e in payload["eventos"]] == [
        "LUNES 19/10", "MARTES 20/10", "MIÉRCOLES 21/10", "JUEVES 22/10", "VIERNES 23/10", "SÁBADO 24/10"]
    assert [e["evento"] for e in payload["eventos"]][-2:] == ["Índice de precios al consumidor (IPC)"] * 2
    html = build_html(payload, RAIZ / "templates" / "stories" / "calendario.html")
    assert "Los días clave de este análisis" in html and "{{" not in html
    for texto in (payload["titulo"], payload["subtitulo"], payload["cta"]):
        assert "—" not in texto and "oportunidad" not in texto.lower() and "operar" not in texto.lower()
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `uv run pytest tests/test_analista_agenda.py -q`
Expected: FAIL (`ModuleNotFoundError: No module named 'analista.agenda'`).

- [ ] **Step 3: Implementar**

`scripts/analista/agenda.py`:

```python
"""Los días clave de un análisis: el calendario económico de sus 7 días de vigencia.

Un análisis vale 7 días corridos (spec 2026-10-16 §2), así que su agenda es la de esos 7 días y no
la de la semana calendario. Investing.com entrega la semana en curso y la siguiente en pestañas
distintas (`thisWeek`, `nextWeek`, de domingo a sábado): pedir solo la primera dejaba la agenda
vacía cada sábado (oro, 2026-10-17). Spec 2026-10-17 §3.

Tres estados, porque se dicen distinto: `ok` (hay datos de alto impacto en la ventana), `vacia`
(el calendario respondió y no hay ninguno) y `sin_calendario` (no respondió, o entregó una copia
vieja: su respaldo de caché no avisa, así que se reconoce por las fechas).

El efecto sobre el activo sale del glosario (`si_sale_sobre_consenso`), como en el seguimiento:
nunca de la redacción.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Callable
from zoneinfo import ZoneInfo

SANTIAGO = ZoneInfo("America/Santiago")
DIAS = ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")
VENTANA_DIAS = 7
MAXIMO_LAMINA = 6
URL_CALENDARIO = "https://es.investing.com/economic-calendar/"
PAISES = {"United States": "EE.UU.", "Chile": "Chile", "China": "China", "Euro Zone": "Zona Euro",
          "Euro Area": "Zona Euro", "Zona Euro": "Zona Euro"}


def dia_corto(momento: date | datetime) -> str:
    """«sábado 17/10», el mismo formato que `preparar.fecha_corta`."""
    if isinstance(momento, datetime):
        momento = momento.astimezone(SANTIAGO)
    return f"{DIAS[momento.weekday()]} {momento:%d/%m}"


def texto_vacia(agenda: dict[str, Any]) -> str:
    """La ventana sin datos de alto impacto, con sus fechas (decisión 2 del director, 2026-10-17)."""
    return (f"Sin datos de alto impacto entre el {agenda['desde']} y el {agenda['hasta']} en el calendario "
            "de EE.UU., Chile, China y la Zona Euro.")


def _domingo(d: date) -> date:
    """El domingo que abre la semana de Investing.com que contiene `d`."""
    return d - timedelta(days=(d.weekday() + 1) % 7)


def _cuando(ev: dict[str, Any]) -> datetime | None:
    """`cargar_calendario` ya entrega la hora en Santiago: no se reconvierte (issue #38)."""
    try:
        return datetime.strptime(ev["hora_servidor"], "%Y-%m-%d %H:%M").replace(tzinfo=SANTIAGO)
    except (KeyError, TypeError, ValueError):
        return None


def _hora(cuando: datetime) -> str:
    return f"{cuando:%H:%M} {'CLST' if cuando.dst() else 'CLT'}"


def _cifra(valor: Any) -> str:
    from pipeline_informe import _cifra_es

    return _cifra_es(str(valor or "").strip())


def _efecto(ev: dict[str, Any], ticker: str, nombre: str) -> str:
    from analista import macro_seguimiento as mac

    clave = mac.CLAVE_DEL_ACTIVO.get(ticker)
    verbo = ((ev.get("diccionario") or {}).get("si_sale_sobre_consenso") or {}).get(clave) if clave else None
    if verbo not in ("sube", "baja"):
        return ""
    return (f"Si sale sobre lo esperado, {mac._el(clave, nombre)} tiende a "
            f"{'subir' if verbo == 'sube' else 'bajar'}; si sale bajo lo esperado, lo contrario.")


def fila(ev: dict[str, Any], ticker: str, nombre: str) -> dict[str, Any]:
    cuando = _cuando(ev)
    dic = ev.get("diccionario") or {}
    efecto = _efecto(ev, ticker, nombre)
    return {"fecha": f"{cuando:%Y-%m-%d}", "dia": dia_corto(cuando), "hora": _hora(cuando),
            "evento": dic.get("nombre_es") or ev.get("nombre", ""), "fuente_nombre": ev.get("nombre", ""),
            "pais": PAISES.get(ev.get("pais", ""), ev.get("pais", "")),
            "anterior": _cifra(ev.get("previo")), "esperado": _cifra(ev.get("forecast")),
            "explicacion": dic.get("explicacion", ""), "efecto": efecto, "mueve_al_activo": bool(efecto)}


@dataclass
class Agenda:
    desde: str
    hasta: str
    estado: str  # "ok" | "vacia" | "sin_calendario"
    eventos: list[dict[str, Any]] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)

    def a_dict(self) -> dict[str, Any]:
        return {"desde": self.desde, "hasta": self.hasta, "estado": self.estado,
                "eventos": [dict(e) for e in self.eventos], "url": URL_CALENDARIO}


def leer_ventana(ahora: datetime, ticker: str, nombre: str, cargar: Callable[..., dict[str, Any]] | None = None,
                 dias: int = VENTANA_DIAS) -> Agenda:
    """Los datos de alto impacto entre `ahora` y `ahora + dias`, de las dos pestañas que la cubren."""
    if cargar is None:
        from market_data_mcp.tools.calendar import cargar_calendario as cargar
    ahora = ahora.astimezone(SANTIAGO)
    limite = ahora + timedelta(days=dias)
    domingo = _domingo(ahora.date())
    crudos: list[dict[str, Any]] = []
    avisos: list[str] = []
    fallidas = 0
    for tab, inicio in (("thisWeek", domingo), ("nextWeek", domingo + timedelta(days=7))):
        if inicio > limite.date():
            continue
        try:
            # Todo el calendario (impacto bajo en adelante): sin filas no se puede reconocer la copia vieja.
            res = cargar(solo_hoy=False, min_impact="low", ahora=ahora, pestanas=(tab,))
        except Exception as exc:  # noqa: BLE001  el calendario es un insumo: su falla se dice, no tumba la pieza
            avisos.append(f"el calendario falló ({exc.__class__.__name__})")
            fallidas += 1
            continue
        if "error" in res:
            avisos.append(f"el calendario no respondió ({res['error']})")
            fallidas += 1
            continue
        eventos = list(res.get("eventos") or [])
        fechas = [c for c in map(_cuando, eventos) if c]
        if fechas and max(fechas).date() < inicio:
            avisos.append(f"el calendario entregó una copia vieja (su último dato es del {dia_corto(max(fechas))})")
            fallidas += 1
            continue
        crudos += eventos
    filas = []
    for ev in crudos:
        cuando = _cuando(ev)
        if ev.get("impacto") == "alto" and cuando and ahora <= cuando <= limite:
            filas.append((cuando, fila(ev, ticker, nombre)))
    filas.sort(key=lambda par: par[0])
    eventos = [f for _, f in filas]
    estado = "ok" if eventos else ("sin_calendario" if fallidas else "vacia")
    return Agenda(dia_corto(ahora), dia_corto(limite), estado, eventos, avisos)


def payload_lamina(agenda: dict[str, Any]) -> dict[str, Any]:
    """La lámina del calendario (plantilla `calendario` de Stories): todo su texto es de Python.

    Hasta 6 eventos, primero los que mueven al activo según el glosario, y después en orden de reloj.
    """
    eventos = agenda["eventos"]
    elegidos = ([e for e in eventos if e.get("mueve_al_activo")]
                + [e for e in eventos if not e.get("mueve_al_activo")])[:MAXIMO_LAMINA]
    elegidos.sort(key=lambda e: (e["fecha"], e["hora"]))
    return {
        "plantilla": "calendario",
        "sello": "CALENDARIO ECONÓMICO · GI",
        "fecha_hora": f"DEL {agenda['desde'].upper()} AL {agenda['hasta'].upper()}",
        "titulo": "Los días clave de este análisis",
        "subtitulo": "Datos de alto impacto de los próximos 7 días, en hora de Chile. Fuente: calendario de Investing.com.",
        "eventos": [{"numero": f"{i:02d}", "dia": e["dia"].upper(), "hora": e["hora"], "evento": e["evento"],
                     "pais": e["pais"], "impacto": "Alto impacto", "impacto_slug": "alto",
                     "anterior": e["anterior"], "esperado": e["esperado"], "tiene_esperado": bool(e["esperado"])}
                    for i, e in enumerate(elegidos, 1)],
        "cta": "Lo revisamos juntos en la plataforma MT5",
        "cta_sub": "Grupo Inteligencia",
    }
```

- [ ] **Step 4: Correr los tests**

Run: `uv run pytest tests/test_analista_agenda.py -q`
Expected: `8 passed`.

- [ ] **Step 5: Commit**

```bash
git add scripts/analista/agenda.py tests/test_analista_agenda.py
git commit -m "feat(bot): la agenda del análisis cubre sus 7 días de vigencia

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Los hechos del día de cada driver

**Files:**
- Create: `scripts/analista/hechos.py`
- Test: `tests/test_analista_hechos.py` (crear)

**Interfaces:**
- Consumes: `config/drivers.json` (`correlacion`), `agenda.dia_corto`, `pipeline_carrusel.formatear_precio`, `macro_seguimiento.CLAVE_DEL_ACTIVO` y `_el`, la curva de `cargar_curva_tasas(serie="ALL")` (`{"series": {"DFII10": {"status","nivel_pct","fecha_dato","delta_1d_bps","delta_5d_bps"}, ...}}`), los eventos de `Agenda.eventos`.
- Produces:
  - `hechos.signos(ticker) -> dict[str, int]` (medible → +1, -1 o 0).
  - `hechos.medir(ticker, nombre, direccion, curva, eventos, leer_d1, hoy, respaldo_dxy=None) -> (list[dict], list[str])`. Cada hecho: `id, driver, fecha, en_curso, nivel, cambio_1d, cambio_5d, unidad_cambio, sentido, sentido_1d, fuente, efecto, con_la_lectura` y, en `fed`, `proxima_decision`.
  - `hechos.leer_d1_mt5(simbolo, n) -> list[tuple[date, float]]` (cierres D1, del más antiguo al más nuevo).

- [ ] **Step 1: Escribir los tests**

`tests/test_analista_hechos.py`:

```python
"""Los drivers del día, medidos por Python: nivel, fecha, cambio, efecto y si acompañan la lectura."""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts"), str(RAIZ / "tests")):
    if p not in sys.path:
        sys.path.insert(0, p)

from analista import hechos as hc  # noqa: E402

HOY = date(2026, 10, 17)  # sábado
CURVA = {"series": {
    "DFII10": {"status": "OK", "nivel_pct": 2.78, "fecha_dato": "2026-10-15", "delta_1d_bps": -6.0, "delta_5d_bps": -14.0},
    "DGS10": {"status": "OK", "nivel_pct": 5.10, "fecha_dato": "2026-10-15", "delta_1d_bps": -9.0, "delta_5d_bps": -18.0},
    "DFF": {"status": "OK", "nivel_pct": 3.88, "fecha_dato": "2026-10-15", "delta_1d_bps": 0.0, "delta_5d_bps": 0.0},
}}
DECISION = {"dia": "miércoles 21/10", "hora": "15:00 CLST", "fuente_nombre": "Fed Interest Rate Decision"}


def serie(*cierres, hasta=date(2026, 10, 16)):
    return [(hasta - timedelta(days=len(cierres) - 1 - i), c) for i, c in enumerate(cierres)]


DXY = serie(101.848, 101.9, 101.95, 101.85, 101.80, 101.753, 101.56)


def lector(series):
    return lambda simbolo, n: series.get(simbolo, [])


def medir_oro(series=None, curva=CURVA, direccion="BAJISTA", **kw):
    return hc.medir("XAUUSD", "Oro", direccion, curva, [DECISION], lector(series or {"USDIDX": DXY}), HOY, **kw)


def test_los_signos_salen_de_drivers_json():
    assert hc.signos("XAUUSD") == {"dxy": -1, "tasa_real": -1, "fed": -1}
    assert hc.signos("USDCLP") == {"cobre": -1, "dxy": 1}


def test_el_dxy_del_oro_trae_nivel_fecha_cambio_y_efecto():
    hechos, avisos = medir_oro()
    assert [h["id"] for h in hechos] == ["dxy", "tasa_real", "fed"] and avisos == []
    dxy = hechos[0]
    assert (dxy["nivel"], dxy["cambio_1d"], dxy["cambio_5d"]) == ("101,560", "0,193", "0,340")
    assert dxy["fecha"] == "viernes 16/10" and dxy["en_curso"] is False  # un sábado, el cierre es del viernes
    assert dxy["sentido"] == "bajó" and dxy["efecto"] == "juega a favor del alza del oro"
    assert dxy["con_la_lectura"] == "va en contra de nuestra lectura" and dxy["fuente"] == "MT5 (USDIDX)"


def test_la_tasa_real_va_en_por_ciento_y_puntos_base_sin_signo_porcentaje():
    tasa = medir_oro()[0][1]
    assert tasa["nivel"] == "2,78 por ciento" and tasa["cambio_5d"] == "14 pb" and tasa["fecha"] == "jueves 15/10"
    assert tasa["efecto"] == "juega a favor del alza del oro"
    assert "%" not in json.dumps(medir_oro()[0], ensure_ascii=False)


def test_la_fed_quieta_no_tiene_efecto_y_dice_su_proxima_decision():
    fed = medir_oro()[0][2]
    assert fed["sentido"] == "estable" and fed["efecto"] is None and fed["con_la_lectura"] is None
    assert fed["proxima_decision"] == "miércoles 21/10 15:00 CLST"


def test_con_lectura_alcista_el_mismo_efecto_acompana():
    assert medir_oro(direccion="ALCISTA")[0][0]["con_la_lectura"] == "acompaña nuestra lectura"


def test_con_lectura_lateral_no_se_compara():
    assert medir_oro(direccion="LATERAL")[0][0]["con_la_lectura"] is None


def test_bajo_el_umbral_es_estable_y_sin_efecto():
    quieto = serie(101.5, 101.5, 101.5, 101.5, 101.5, 101.55, 101.6)
    dxy = medir_oro({"USDIDX": quieto})[0][0]
    assert dxy["sentido"] == "estable" and dxy["efecto"] is None


def test_la_vela_de_hoy_queda_en_curso():
    hoy = serie(101.848, 101.9, 101.95, 101.85, 101.80, 101.753, 101.56, hasta=HOY)
    assert medir_oro({"USDIDX": hoy})[0][0]["en_curso"] is True


def test_sin_usdidx_el_dxy_sale_del_respaldo_y_lo_dice():
    hechos, _ = medir_oro({}, respaldo_dxy=lambda n: DXY)
    assert "yfinance" in hechos[0]["fuente"] and hechos[0]["nivel"] == "101,560"


def test_lo_que_no_se_puede_medir_se_avisa_y_no_se_inventa():
    hechos, avisos = medir_oro(curva={})
    assert [h["id"] for h in hechos] == ["dxy"]
    assert any("Tasa real" in a for a in avisos) and any("Fed" in a for a in avisos)


def test_un_activo_sin_ficha_recibe_los_generales_sin_efecto():
    hechos, _ = hc.medir("COPPER", "Cobre", "ALCISTA", CURVA, [], lector({"USDIDX": DXY}), HOY)
    assert [h["id"] for h in hechos] == ["dxy", "bono_10"]
    assert all(h["efecto"] is None and h["con_la_lectura"] is None for h in hechos)


def test_el_cobre_del_dolar_usa_los_digitos_del_simbolo():
    cobre = serie(14600.0, 14550.0, 14500.0, 14450.0, 14400.0, 14300.0, 14197.0)
    hechos, _ = hc.medir("USDCLP", "Dólar", "ALCISTA", CURVA, [], lector({"USDIDX": DXY, "COPPER": cobre}), HOY)
    c = next(h for h in hechos if h["id"] == "cobre")
    assert c["nivel"] == "14197" and c["cambio_5d"] == "353" and c["sentido"] == "bajó"
    assert c["efecto"] == "juega a favor del alza del USD/CLP" and c["con_la_lectura"] == "acompaña nuestra lectura"
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `uv run pytest tests/test_analista_hechos.py -q`
Expected: FAIL (`No module named 'analista.hechos'`).

- [ ] **Step 3: Implementar**

`scripts/analista/hechos.py`:

```python
"""Lo que pasa hoy con los drivers de un activo, medido por Python antes de llamar a agy.

La corrida del oro del 2026-10-17 salió genérica porque agy solo recibía los nombres de los
drivers del catálogo y el prompt le mandaba explicarlos como mecanismo condicional (spec
2026-10-17 §1). Acá se mide cada driver medible (Dollar Index, tasa real, bono a 10 años, tasa de
la Fed, cobre, petróleo) con su fecha, su cambio en 5 sesiones y su efecto sobre el activo.

Qué se mide y con qué signo lo dice `config/drivers.json` (la `correlacion` de cada driver), no
el código. El efecto y si acompaña nuestra lectura los calcula Python, como la discrepancia con
los bancos: un modelo tiende a alinearse con lo que lee. Un dato que no está se avisa y falta.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

from analista import RAIZ
from analista.agenda import dia_corto

DRIVERS = RAIZ / "config" / "drivers.json"
SESIONES = 5
# Bajo estos cambios a 5 sesiones el driver se dice «estable» y no se le atribuye efecto:
# puntos del DXY, puntos base de las tasas y fracción del precio en cobre y petróleo.
UMBRAL_ESTABLE = {"dxy": 0.15, "tasa_real": 3.0, "bono_10": 3.0, "fed": 3.0, "cobre": 0.005, "petroleo": 0.005}
RELATIVO = frozenset({"cobre", "petroleo"})
CLAVE_DRIVERS = {"XAUUSD": "XAU/USD", "USDCLP": "USD/CLP", "USDJPY": "USD/JPY", "EURUSD": "EUR/USD",
                 "WTI.spot": "WTI", "US100.spot": "US100"}
MEDIBLE_DE_DRIVER = {"dollar_index": "dxy", "tasas_reales": "tasa_real", "rendimientos_treasury": "bono_10",
                     "decisiones_fed": "fed", "tasas_fed": "fed", "cobre": "cobre", "precios_energia": "petroleo"}
GENERALES = ("dxy", "bono_10")
SIMBOLOS = {"dxy": ("USDIDX", 3, "puntos"), "cobre": ("COPPER", 0, "dólares por tonelada"),
            "petroleo": ("WTI.spot", 3, "dólares por barril")}
CURVA = {"tasa_real": "DFII10", "bono_10": "DGS10", "fed": "DFF"}
NOMBRES = {"dxy": "Dollar Index (DXY)", "tasa_real": "Tasa real a 10 años de EE.UU. (TIPS)",
           "bono_10": "Bono del Tesoro a 10 años", "fed": "Tasa de la Fed (fondos federales)",
           "cobre": "Cobre", "petroleo": "Petróleo WTI"}
FUENTE_CURVA = "FRED (Reserva Federal de St. Louis)"
_DECISION_FED = re.compile(r"fed interest rate decision|fomc statement", re.IGNORECASE)


def signos(ticker: str, ruta: Path = DRIVERS) -> dict[str, int]:
    """Medible -> +1 (correlación directa), -1 (inversa) o 0 (sin signo declarado), en el orden del archivo.

    Un activo sin ficha en `drivers.json` recibe los generales sin signo: se describen, no se interpretan.
    """
    clave = CLAVE_DRIVERS.get(ticker)
    datos = json.loads(ruta.read_text(encoding="utf-8")) if clave else {}
    salida: dict[str, int] = {}
    for driver, info in (datos.get(clave) or {}).get("drivers", {}).items():
        medible = MEDIBLE_DE_DRIVER.get(driver)
        if medible and medible not in salida:
            c = str(info.get("correlacion", "")).lower()
            salida[medible] = 1 if c.startswith("directa") else -1 if c.startswith("inversa") else 0
    return salida or {m: 0 for m in GENERALES}


def _fmt(valor: float, digits: int) -> str:
    from pipeline_carrusel import formatear_precio

    return formatear_precio(valor, digits)


def _sentido(medible: str, cambio: float | None, base: float | None) -> str:
    if cambio is None:
        return "sin_dato"
    medida = abs(cambio) / abs(base) if medible in RELATIVO and base else abs(cambio)
    if medida < UMBRAL_ESTABLE[medible]:
        return "estable"
    return "subió" if cambio > 0 else "bajó"


def _de_serie(medible: str, puntos: list[tuple[date, float]], fuente: str, hoy: date) -> dict[str, Any] | None:
    _, digits, unidad = SIMBOLOS[medible]
    if len(puntos) < SESIONES + 1:
        return None
    (f0, v0), (_, v1), (_, v5) = puntos[-1], puntos[-2], puntos[-(SESIONES + 1)]
    return {"id": medible, "driver": NOMBRES[medible], "fecha": dia_corto(f0), "en_curso": f0 == hoy,
            "nivel": _fmt(v0, digits), "cambio_1d": _fmt(abs(v0 - v1), digits),
            "cambio_5d": _fmt(abs(v0 - v5), digits), "unidad_cambio": unidad,
            "sentido": _sentido(medible, v0 - v5, v5), "sentido_1d": _sentido(medible, v0 - v1, v1),
            "fuente": fuente}


def _pb(valor: float | None) -> str:
    # `None` es "no se pudo calcular", no "no se movió" (CLAUDE.md, get_curva_tasas).
    return "sin dato" if valor is None else f"{abs(float(valor)):.0f} pb"


def _de_curva(medible: str, curva: dict[str, Any] | None, eventos: list[dict[str, Any]]) -> dict[str, Any] | None:
    serie = ((curva or {}).get("series") or {}).get(CURVA[medible]) or {}
    if serie.get("status") != "OK" or serie.get("nivel_pct") is None or not serie.get("fecha_dato"):
        return None
    d1, d5 = serie.get("delta_1d_bps"), serie.get("delta_5d_bps")
    h = {"id": medible, "driver": NOMBRES[medible], "fecha": dia_corto(date.fromisoformat(serie["fecha_dato"])),
         "en_curso": False, "nivel": f"{float(serie['nivel_pct']):.2f}".replace(".", ",") + " por ciento",
         "cambio_1d": _pb(d1), "cambio_5d": _pb(d5), "unidad_cambio": "puntos base",
         "sentido": _sentido(medible, d5, None), "sentido_1d": _sentido(medible, d1, None), "fuente": FUENTE_CURVA}
    if medible == "fed":
        decision = next((e for e in eventos or [] if _DECISION_FED.search(str(e.get("fuente_nombre", "")))), None)
        h["proxima_decision"] = f"{decision['dia']} {decision['hora']}" if decision else ""
    return h


def _de(el: str) -> str:
    return "del " + el[3:] if el.startswith("el ") else "de " + el


def _efecto(h: dict[str, Any], signo: int, el: str, direccion: str) -> dict[str, Any]:
    impacto = signo * {"subió": 1, "bajó": -1}.get(h["sentido"], 0)
    if not impacto:
        return {"efecto": None, "con_la_lectura": None}
    efecto = f"juega a favor del alza {_de(el)}" if impacto > 0 else f"juega a favor de la baja {_de(el)}"
    lectura = {"ALCISTA": 1, "BAJISTA": -1}.get(str(direccion).upper(), 0)
    con = None if not lectura else ("acompaña nuestra lectura" if lectura == impacto
                                    else "va en contra de nuestra lectura")
    return {"efecto": efecto, "con_la_lectura": con}


def medir(ticker: str, nombre: str, direccion: str, curva: dict[str, Any] | None, eventos: list[dict[str, Any]],
          leer_d1: Callable[[str, int], list[tuple[date, float]]], hoy: date,
          respaldo_dxy: Callable[[int], list[tuple[date, float]]] | None = None
          ) -> tuple[list[dict[str, Any]], list[str]]:
    """Los hechos del día del activo y los avisos de lo que no se pudo medir."""
    from analista import macro_seguimiento as mac

    el = mac._el(mac.CLAVE_DEL_ACTIVO.get(ticker, ""), nombre)
    hechos: list[dict[str, Any]] = []
    avisos: list[str] = []
    for medible, signo in signos(ticker).items():
        try:
            if medible in SIMBOLOS:
                simbolo = SIMBOLOS[medible][0]
                puntos, fuente = leer_d1(simbolo, SESIONES + 2), f"MT5 ({simbolo})"
                if not puntos and medible == "dxy" and respaldo_dxy is not None:
                    puntos, fuente = respaldo_dxy(SESIONES + 2), "ICE (DX-Y.NYB) vía yfinance"
                h = _de_serie(medible, puntos, fuente, hoy)
            else:
                h = _de_curva(medible, curva, eventos)
        except Exception as exc:  # noqa: BLE001  un driver que no se mide se avisa: no tumba la pieza
            avisos.append(f"no pude medir {NOMBRES[medible]} ({exc.__class__.__name__})")
            continue
        if h is None:
            avisos.append(f"sin dato de {NOMBRES[medible]}")
            continue
        h.update(_efecto(h, signo, el, direccion))
        hechos.append(h)
    return hechos, avisos


def leer_d1_mt5(simbolo: str, n: int) -> list[tuple[date, float]]:
    """Los últimos `n` cierres diarios del terminal, del más antiguo al más nuevo.

    MT5 entrega la hora del servidor empaquetada como timestamp: la fecha de la vela D1 es la del
    servidor, que es la de la sesión (CLAUDE.md, «Ojo con MT5»).
    """
    from market_data_mcp import mt5_client

    mt5_client.connect()
    import MetaTrader5 as mt5  # noqa: PLC0415

    mt5.symbol_select(simbolo, True)
    rates = mt5.copy_rates_from_pos(simbolo, mt5.TIMEFRAME_D1, 0, n)
    if rates is None or len(rates) == 0:
        return []
    return [(datetime.fromtimestamp(int(r["time"]), tz=timezone.utc).date(), float(r["close"])) for r in rates]
```

- [ ] **Step 4: Correr los tests**

Run: `uv run pytest tests/test_analista_hechos.py -q`
Expected: `12 passed`. Si `test_los_signos_salen_de_drivers_json` falla, mira `config/drivers.json`: el test refleja el archivo al 2026-10-17; si el director lo cambió, ajusta el test, no el código.

- [ ] **Step 5: Verificar contra el terminal (manual, requiere MT5 abierto)**

```bash
uv run --with MetaTrader5 python -c "
import sys; sys.path[:0] = ['src', 'scripts']
from analista import hechos as hc
print(hc.leer_d1_mt5('USDIDX', 7)[-2:])
"
```
Expected: dos tuplas `(fecha, cierre)` con el DXY cerca de 100. Si MT5 no está abierto, anótalo y sigue.

- [ ] **Step 6: Commit**

```bash
git add scripts/analista/hechos.py tests/test_analista_hechos.py
git commit -m "feat(bot): mide los drivers del día con su efecto sobre el activo

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Qué fuentes cuentan como banco

**Files:**
- Modify: `config/fuentes_prestigio.json`
- Modify: `scripts/analista/fuentes.py` (agregar al final)
- Test: `tests/test_analista_fuentes.py` (agregar al final)

**Interfaces:**
- Produces: `fuentes.bancos(fuentes, lista=None) -> list[dict]`, `fuentes.falta_banco(pieza, lista=None) -> list[str]`, `fuentes.guardar_intento(dir_pedido, validas, descartes, crudas) -> Path`, `fuentes.INTENTO = "fuentes_intento_1.json"`.
- Consumes (Task 8): el bot y `bot_analistas.validar`.

- [ ] **Step 1: Escribir los tests**

Agrega al final de `tests/test_analista_fuentes.py` (usa los imports que ya tiene el archivo; si no importa `json`, agrégalo arriba):

```python
# ───────────────────────────────────────────── bancos obligatorios (spec 2026-10-17 §5)


def test_la_lista_declara_que_grupos_cuentan_como_banco():
    assert fu.cargar_lista()["cuentan_como_banco"] == ["bancos_de_inversion", "chile"]


def test_cuentan_los_bancos_de_inversion_y_los_de_chile_y_no_los_organismos():
    fuentes = [{"entidad": "JPMorgan"}, {"entidad": "World Gold Council"}, {"entidad": "Banchile"}, "basura"]
    assert [f["entidad"] for f in fu.bancos(fuentes)] == ["JPMorgan", "Banchile"]


def test_falta_banco_lo_dice_y_calla_si_hay_uno():
    sin = {"editorial": {"fuentes": [{"entidad": "Fed"}]}}
    con = {"editorial": {"fuentes": [{"entidad": "Fed"}, {"entidad": "UBS"}]}}
    errs = fu.falta_banco(sin)
    assert errs and "falta al menos una voz de banco" in errs[0] and "14 días" in errs[0]
    assert fu.falta_banco(con) == []
    assert fu.falta_banco({"editorial": {"fuentes": "[[ESCRIBIR]]"}}) == []  # eso lo dice esquema.errores


def test_el_intento_guarda_las_validas_y_las_urls_descartadas(tmp_path):
    valida = {"entidad": "Fed", "url": "https://www.federalreserve.gov/newsevents/x.htm"}
    crudas = [valida, {"entidad": "Un Blog", "url": "https://blog.example.com/nota"}, "basura"]
    ruta = fu.guardar_intento(tmp_path, [valida], ["Un Blog: la entidad no está en la lista"], crudas)
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert ruta.name == fu.INTENTO and datos["validas"] == [valida]
    assert datos["descartadas"] == ["https://blog.example.com/nota"] and datos["motivos"]
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `uv run pytest tests/test_analista_fuentes.py -q`
Expected: FAIL (`KeyError: 'cuentan_como_banco'` y `AttributeError: ... 'bancos'`).

- [ ] **Step 3: Implementar**

En `config/fuentes_prestigio.json`, reemplaza las dos primeras claves por:

```json
  "_nota": "Lista cerrada. La edita el director. `entidad` es quien opina; `medio` es dónde se publicó. Un banco puede ser medio de sí mismo (su sitio) o publicarse en un medio de prensa. `cuentan_como_banco`: los grupos de `entidades` que cumplen el mínimo de una voz de banco por análisis (spec 2026-10-17 §5); los organismos suman, pero no lo cumplen.",
  "frescura_dias": 14,
  "cuentan_como_banco": ["bancos_de_inversion", "chile"],
```

Al final de `scripts/analista/fuentes.py`:

```python
# ───────────────────────────────────────────── mínimo de un banco (spec 2026-10-17 §5)

INTENTO = "fuentes_intento_1.json"


def _nombres_banco(lista: dict[str, Any]) -> set[str]:
    grupos = lista.get("cuentan_como_banco") or ["bancos_de_inversion"]
    return {e for g in grupos for e in lista["entidades"].get(g, [])}


def bancos(fuentes: Any, lista: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Las fuentes cuya entidad cuenta como banco (`cuentan_como_banco` de la lista cerrada)."""
    nombres = _nombres_banco(lista or cargar_lista())
    return [f for f in (fuentes if isinstance(fuentes, list) else [])
            if isinstance(f, dict) and f.get("entidad") in nombres]


def falta_banco(pieza: dict[str, Any], lista: dict[str, Any] | None = None) -> list[str]:
    """El error de `--validar` cuando `fuentes` no trae ningún banco; vacío si lo trae o si aún no es lista."""
    fuentes = (pieza.get("editorial") or {}).get("fuentes")
    if not isinstance(fuentes, list):
        return []  # `esquema.errores` ya dice que falta la lista
    lista = lista or cargar_lista()
    if bancos(fuentes, lista):
        return []
    return [f"fuentes: falta al menos una voz de banco ({', '.join(sorted(_nombres_banco(lista)))}) con su nota "
            f"de los últimos {lista.get('frescura_dias', 14)} días; los organismos suman, pero no la reemplazan"]


def guardar_intento(dir_pedido: Path, validas: list[dict[str, Any]], descartes: list[str], crudas: Any) -> Path:
    """Lo que dejó el primer intento, para que el segundo no repita URLs caídas (spec 2026-10-17 §5)."""
    urls_validas = {f.get("url") for f in validas if isinstance(f, dict)}
    descartadas = [f["url"] for f in (crudas if isinstance(crudas, list) else [])
                   if isinstance(f, dict) and isinstance(f.get("url"), str) and f["url"] not in urls_validas]
    ruta = Path(dir_pedido) / INTENTO
    ruta.write_text(json.dumps({"validas": list(validas), "descartadas": descartadas, "motivos": list(descartes)},
                               ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta
```

- [ ] **Step 4: Correr los tests**

Run: `uv run pytest tests/test_analista_fuentes.py tests/test_analista_instrucciones.py -q`
Expected: todo `passed`.

- [ ] **Step 5: Commit**

```bash
git add config/fuentes_prestigio.json scripts/analista/fuentes.py tests/test_analista_fuentes.py
git commit -m "feat(bot): declara qué fuentes cuentan como banco

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 5: El esquema exige citar los hechos y nombrar los días clave

**Files:**
- Modify: `scripts/analista/esquema.py`
- Test: `tests/test_analista_esquema.py` (agregar al final)

**Interfaces:**
- Produces: `esquema.hechos_citados(texto, hechos) -> list[str]`, `esquema.MINIMO_HECHOS = 2`, `LARGO_MAXIMO_ANIDADO["dias_clave"] = 420`. `esquema.errores` agrega (solo en `oportunidad`) los errores de `contexto` sin hechos y de `dias_clave` sin día. Con `datos.hechos` ausente o vacío, y sin `datos.agenda`, no exige nada (piezas anteriores).
- Consumes (Tasks 6 a 8): fixtures, ficha y bot.

- [ ] **Step 1: Escribir los tests**

Agrega al final de `tests/test_analista_esquema.py`:

```python
# ───────────────────────────────────────────── desarrollo del texto (spec 2026-10-17 §5)

HECHOS = [
    {"id": "dxy", "driver": "Dollar Index (DXY)", "fecha": "viernes 16/10", "nivel": "101,560",
     "cambio_1d": "0,193", "cambio_5d": "0,288", "unidad_cambio": "puntos", "sentido": "bajó"},
    {"id": "tasa_real", "driver": "Tasa real a 10 años de EE.UU. (TIPS)", "fecha": "jueves 15/10",
     "nivel": "2,78 por ciento", "cambio_1d": "6 pb", "cambio_5d": "14 pb", "unidad_cambio": "puntos base",
     "sentido": "bajó"},
]
EVENTO = {"dia": "miércoles 21/10", "hora": "09:30 CLST", "evento": "IPC", "esperado": "0,3 por ciento"}


def pieza_desarrollada(contexto, hechos=HECHOS, eventos=(), dias=None):
    datos = {**DATOS, "hechos": hechos,
             "agenda": {"desde": "sábado 17/10", "hasta": "sábado 24/10", "estado": "ok" if eventos else "vacia",
                        "eventos": list(eventos)}}
    extra = {"titulares": ["XAUUSD"], "contexto": ["XAUUSD"], **({"dias_clave": ["XAUUSD"]} if eventos else {})}
    p = es.nueva_pieza("oportunidad", {"ticker": "XAUUSD"}, datos, {}, extra_campos=extra)
    p["editorial"] = {"titular": "El oro mantiene presión compradora", "bajada": "Lectura de nuestros sistemas.",
                      "titulares": {"XAUUSD": "El oro sigue firme"}, "contexto": {"XAUUSD": contexto},
                      "fuentes": []}
    if eventos:
        p["editorial"]["dias_clave"] = {"XAUUSD": dias}
    return p


CITA_LOS_DOS = ("El Dollar Index (DXY) cerró el viernes 16/10 en 101,560, y la tasa real a 10 años quedó en "
                "2,78 por ciento. La lectura sigue mientras el precio respete la línea.")


def test_un_contexto_que_cita_dos_hechos_pasa():
    assert es.errores(pieza_desarrollada(CITA_LOS_DOS)) == []


def test_un_contexto_generico_no_pasa():
    errs = es.errores(pieza_desarrollada("El oro responde a las tasas reales y al dólar global."))
    assert any("contexto.XAUUSD" in e and "datos.hechos" in e and "101,560" in e for e in errs)


def test_citar_uno_de_dos_no_alcanza():
    errs = es.errores(pieza_desarrollada("El Dollar Index cerró en 101,560. La lectura sigue."))
    assert any("contexto.XAUUSD" in e for e in errs)


def test_con_un_solo_hecho_basta_citarlo():
    assert es.errores(pieza_desarrollada("El Dollar Index cerró en 101,560.", hechos=HECHOS[:1])) == []


def test_un_cambio_tambien_cuenta_como_cita():
    texto = "El Dollar Index bajó 0,288 puntos en cinco sesiones y la tasa real está en 2,78 por ciento."
    assert es.hechos_citados(texto, HECHOS) == ["dxy", "tasa_real"]


def test_sin_hechos_no_se_exige_nada():
    """Una pieza anterior al 2026-10-17 se rearma al reusarla: no puede caer por esta regla."""
    assert es.errores(pieza_desarrollada("Texto sin cifras.", hechos=[])) == []
    assert es.errores(pieza_llena()) == []


def test_dias_clave_nombra_un_dia_de_la_agenda():
    ok = pieza_desarrollada(CITA_LOS_DOS, eventos=[EVENTO],
                            dias="El miércoles 21/10 a las 09:30 se conoce el IPC de EE.UU. (índice de precios al consumidor).")
    assert es.errores(ok) == []
    mal = pieza_desarrollada(CITA_LOS_DOS, eventos=[EVENTO], dias="Esta semana viene el IPC de EE.UU.")
    assert any("dias_clave.XAUUSD" in e and "miércoles 21/10" in e for e in es.errores(mal))


def test_dias_clave_tiene_tope_de_largo():
    largo = "El miércoles 21/10 se conoce el IPC. " + "Más contexto sin cifras. " * 20
    errs = es.errores(pieza_desarrollada(CITA_LOS_DOS, eventos=[EVENTO], dias=largo))
    assert any("dias_clave.XAUUSD" in e and "420" in e for e in errs)


def test_dias_clave_pasa_por_los_candados_de_texto():
    p = pieza_desarrollada(CITA_LOS_DOS, eventos=[EVENTO], dias="El miércoles 21/10 sale el IPC — ojo.")
    assert es.errores(p)
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `uv run pytest tests/test_analista_esquema.py -q`
Expected: FAIL en `test_un_contexto_generico_no_pasa`, `test_citar_uno_de_dos_no_alcanza`, `test_un_cambio_tambien_cuenta_como_cita`, `test_dias_clave_nombra...` y `test_dias_clave_tiene_tope...`.

- [ ] **Step 3: Implementar**

En `scripts/analista/esquema.py`:

1. Reemplaza `LARGO_MAXIMO_ANIDADO = {"titulares": 70}` por:

```python
LARGO_MAXIMO_ANIDADO = {"titulares": 70, "dias_clave": 420}
# El contexto nombra el estado real de al menos dos drivers medidos (o del único que haya), con su
# cifra tal como viene en `datos.hechos` (spec 2026-10-17 §5). La corrida del oro del 17/10 pasaba
# todos los controles sin una sola cifra: el validador prohibía inventar, pero no exigía citar.
MINIMO_HECHOS = 2
```

2. Después de `cifras_ajenas`, agrega:

```python
def hechos_citados(texto: str, hechos: list[dict[str, Any]]) -> list[str]:
    """Los `id` de los hechos medidos cuya cifra (nivel o cambio) aparece en el texto.

    Solo cuentan las cifras significativas del propio hecho: citar el precio del activo u otra cifra
    de `datos` no cumple, y "14 pb" (dos dígitos) no alcanza a distinguirse de una fecha.
    """
    del_texto = {_plano_numero(t) for t in _NUMERO.findall(texto) if _significativo(t)}
    citados: list[str] = []
    for h in hechos:
        propias = {_plano_numero(t) for campo in ("nivel", "cambio_1d", "cambio_5d")
                   for t in _NUMERO.findall(str(h.get(campo) or "")) if _significativo(t)}
        if propias & del_texto:
            citados.append(str(h.get("id")))
    return citados


def _errores_de_desarrollo(pieza: dict[str, Any]) -> list[str]:
    """El contexto cita los hechos del día y los días clave nombran un día de la agenda."""
    datos = pieza.get("datos") or {}
    editorial = pieza.get("editorial") or {}
    errs: list[str] = []
    hechos = [h for h in datos.get("hechos") or [] if isinstance(h, dict)]
    exigidos = min(MINIMO_HECHOS, len(hechos))
    contexto = editorial.get("contexto")
    for t, texto in (contexto.items() if isinstance(contexto, dict) else []):
        if exigidos and texto != MARCA and len(hechos_citados(str(texto), hechos)) < exigidos:
            ejemplos = ", ".join(f"{h.get('driver')} {h.get('nivel')}" for h in hechos[:4])
            errs.append(f"contexto.{t}: tiene que nombrar el estado de hoy de al menos {exigidos} de los drivers "
                        f"medidos (datos.hechos), citando su cifra tal como viene: {ejemplos}")
    agenda = datos.get("agenda") if isinstance(datos.get("agenda"), dict) else {}
    dias = [str(e["dia"]) for e in agenda.get("eventos") or [] if isinstance(e, dict) and e.get("dia")]
    dias_clave = editorial.get("dias_clave")
    for t, texto in (dias_clave.items() if isinstance(dias_clave, dict) else []):
        if dias and texto != MARCA and not any(d in str(texto) for d in dias):
            errs.append(f"dias_clave.{t}: tiene que nombrar al menos un día de la agenda tal como viene en "
                        f"datos.agenda ({', '.join(dict.fromkeys(dias[:4]))})")
    return errs
```

3. En `errores`, justo antes de `return errs`, agrega:

```python
    if tipo == "oportunidad":
        errs.extend(_errores_de_desarrollo(pieza))
```

- [ ] **Step 4: Correr los tests**

Run: `uv run pytest tests/test_analista_*.py -q`
Expected: todo `passed` (las fixtures actuales no traen `hechos` ni `agenda`, así que nada cambia para ellas).

- [ ] **Step 5: Commit**

```bash
git add scripts/analista/esquema.py tests/test_analista_esquema.py
git commit -m "feat(bot): el contexto tiene que citar los drivers medidos del día

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Fixtures, ficha y correo con hechos, días clave y bancos

**Files:**
- Modify: `tests/analista_fixtures.py:113-143`
- Modify: `scripts/analista/oportunidad_html.py`
- Modify: `templates/oportunidad/pieza.html:81`
- Test: `tests/test_analista_oportunidad_html.py` (agregar al final)

**Interfaces:**
- Consumes: `agenda.URL_CALENDARIO`, `agenda.texto_vacia` (Task 2), `fuentes.discrepa`, `datos.hechos`, `datos.agenda`, `editorial.dias_clave`, `imagenes.calendario`.
- Produces: `fx.HECHOS_EJEMPLO`, `fx.EVENTO_EJEMPLO`, `fx.agenda_ejemplo(estado)`, `fx.pieza_oportunidad(..., agenda="ok", hechos=True, legado=False)`. La ficha muestra *Lo que pasa hoy con sus drivers* y *Días clave del … al …*; el correo, *Lo que pasa hoy*, *Días clave hasta el …* y *Qué dicen los bancos*.

- [ ] **Step 1: Actualizar las fixtures**

En `tests/analista_fixtures.py`, después de `FUENTES_EJEMPLO` agrega:

```python
HECHOS_EJEMPLO = [
    {"id": "dxy", "driver": "Dollar Index (DXY)", "fecha": "viernes 09/10", "en_curso": False, "nivel": "101,560",
     "cambio_1d": "0,193", "cambio_5d": "0,288", "unidad_cambio": "puntos", "sentido": "bajó", "sentido_1d": "bajó",
     "fuente": "MT5 (USDIDX)", "efecto": "juega a favor del alza del oro",
     "con_la_lectura": "va en contra de nuestra lectura"},
    {"id": "tasa_real", "driver": "Tasa real a 10 años de EE.UU. (TIPS)", "fecha": "jueves 08/10", "en_curso": False,
     "nivel": "2,78 por ciento", "cambio_1d": "6 pb", "cambio_5d": "14 pb", "unidad_cambio": "puntos base",
     "sentido": "bajó", "sentido_1d": "bajó", "fuente": "FRED (Reserva Federal de St. Louis)",
     "efecto": "juega a favor del alza del oro", "con_la_lectura": "va en contra de nuestra lectura"},
]

EVENTO_EJEMPLO = {
    "fecha": "2026-10-14", "dia": "miércoles 14/10", "hora": "09:30 CLST",
    "evento": "Índice de precios al consumidor (IPC)", "fuente_nombre": "CPI (MoM) (Sep)", "pais": "EE.UU.",
    "anterior": "0,4 por ciento", "esperado": "0,3 por ciento", "explicacion": "Mide la inflación.",
    "efecto": "Si sale sobre lo esperado, el oro tiende a bajar; si sale bajo lo esperado, lo contrario.",
    "mueve_al_activo": True}


def agenda_ejemplo(estado: str = "ok") -> dict:
    return {"desde": "lunes 12/10", "hasta": "lunes 19/10", "estado": estado,
            "eventos": [dict(EVENTO_EJEMPLO)] if estado == "ok" else [],
            "url": "https://es.investing.com/economic-calendar/"}
```

y reemplaza `pieza_oportunidad` entera por:

```python
def pieza_oportunidad(dir_pedido: Path, laminas: bool = False, wti: bool = False, rango: bool = False,
                      fuentes: list | None = None, agenda: str = "ok", hechos: bool = True,
                      legado: bool = False) -> dict:
    """El análisis de un activo con su texto ya escrito (por defecto el oro; `rango` es el cobre).

    Escribe el gráfico en `dir_pedido`; con `laminas=True` también la lámina, que en el bot se
    rinde antes del HTML (así el botón «Descargar lámina» aparece). Por defecto trae los hechos
    del día y una agenda con un evento (spec 2026-10-17); `agenda` puede ser `vacia` o
    `sin_calendario`, y `legado=True` arma una pieza anterior a ese spec (`agenda_semana`, sin hechos).
    """
    a = activo_semanal(rango=rango, ticker="WTI.spot" if wti else None)
    _imagen(dir_pedido, a["grafico"])
    if laminas:
        _imagen(dir_pedido, {"WTI.spot": "lamina_wti_spot.png"}.get(a["ticker"], f"lamina_{a['ticker'].lower()}.png"))
    t = a["ticker"]
    datos = {"ticker": t, "chip": "ANÁLISIS TÉCNICO Y FUNDAMENTAL", "edicion": "lunes 12/10 · 09:30",
             "vigencia": {"desde": "lunes 12/10", "hasta": "lunes 19/10"},
             "activos": [a], "drivers": {t: ["Dollar Index"]}, "curva": [],
             "fundamental": {"fuera_catalogo": False, "sin_drivers": False, "referencia": "semanal"}}
    imagenes = {t: a["grafico"]}
    extra = {"titulares": [t], "contexto": [t]}
    if legado:
        datos["agenda_semana"] = []
    else:
        datos["hechos"] = [dict(h) for h in HECHOS_EJEMPLO] if hechos else []
        datos["agenda"] = agenda_ejemplo(agenda)
        if agenda == "ok":
            imagenes["calendario"] = _imagen(dir_pedido, f"calendario_{t.lower().replace('.', '_')}.png")
            extra["dias_clave"] = [t]
    p = es.nueva_pieza("oportunidad", {"ticker": t}, datos, imagenes, extra_campos=extra)
    p["editorial"] = {"titular": f"{a['nombre']}: lectura técnica y fundamental",
                      "bajada": "Lectura de nuestros sistemas, drivers y voces de bancos.",
                      "titulares": {t: f"Titular de {t}"},
                      "contexto": {t: f"Contexto de {t}. El Dollar Index (DXY) cerró en 101,560 y la tasa real a "
                                      "10 años quedó en 2,78 por ciento. La lectura se mantiene mientras el precio "
                                      "respete la línea."},
                      "fuentes": [dict(f) for f in (FUENTES_EJEMPLO if fuentes is None else fuentes)]}
    if "dias_clave" in extra:
        p["editorial"]["dias_clave"] = {t: "El día clave es el miércoles 14/10, cuando se conoce el IPC de EE.UU. "
                                           "(índice de precios al consumidor)."}
    return p
```

Run: `uv run pytest tests/test_analista_*.py -q`
Expected: todo `passed` salvo, si aparece, algún test que compare el conjunto exacto de `editorial` de una pieza de fixture: agrégale `dias_clave` al conjunto esperado (la fixture ahora trae agenda con un evento).

- [ ] **Step 2: Escribir los tests de la ficha y el correo**

Agrega al final de `tests/test_analista_oportunidad_html.py`:

```python
# ───────────────────────────────────────────── texto concreto (spec 2026-10-17 §6)


def _correo(html):
    return re.search(r'<template class="correo-activo" data-ticker="XAUUSD">(.*?)</template>', html, re.S).group(1)


def test_la_ficha_trae_la_tabla_de_hechos(tmp_path):
    h = _html(tmp_path)
    assert "Lo que pasa hoy con sus drivers" in h and "101,560" in h and "viernes 09/10" in h
    assert "bajó 0,288 puntos en 5 sesiones" in h and "va en contra de nuestra lectura" in h
    assert "bajó 14 pb en 5 sesiones" in h  # las tasas no repiten la unidad


def test_la_ficha_trae_los_dias_clave_con_imagen_tabla_y_enlace(tmp_path):
    h = _html(tmp_path)
    assert "Días clave del lunes 12/10 al lunes 19/10" in h
    assert "El día clave es el miércoles 14/10" in h and 'alt="Calendario económico del lunes 12/10' in h
    assert "Índice de precios al consumidor (IPC)" in h and "el oro tiende a bajar" in h
    assert 'href="https://es.investing.com/economic-calendar/"' in h


def test_una_ventana_vacia_dice_sus_fechas_en_la_ficha_y_en_el_correo(tmp_path):
    h = _html(tmp_path, agenda="vacia")
    frase = "Sin datos de alto impacto entre el lunes 12/10 y el lunes 19/10"
    assert h.count(frase) >= 2 and frase in _correo(h)  # en la ficha y en el correo


def test_sin_calendario_avisa_al_ejecutivo_y_el_correo_lo_omite(tmp_path):
    h = _html(tmp_path, agenda="sin_calendario")
    assert "No pude leer el calendario económico" in h
    assert "No pude leer" not in _correo(h) and "Días clave" not in _correo(h)


def test_el_correo_lleva_hechos_dias_clave_imagen_y_bancos_con_enlace(tmp_path):
    correo = _correo(_html(tmp_path))
    assert "Lo que pasa hoy" in correo and "101,560" in correo and "Juega a favor del alza del oro" in correo
    assert "Días clave hasta el lunes 19/10" in correo and "El día clave es el miércoles 14/10" in correo
    assert len(re.findall(r'<img src="data:image/png;base64,[^"]+" width="558" height="\d+"', correo)) == 2
    assert "Qué dicen los bancos" in correo and "Goldman Sachs" in correo and "14/10/2026" in correo
    assert 'href="https://www.reuters.com/markets/commodities/oro-goldman-2026-10-14/"' in correo
    assert "ve distinto que nuestra lectura" in correo  # Goldman alcista contra nuestra lectura bajista
    assert "var(" not in correo and "rgba(" not in correo and "—" not in correo


def test_una_pieza_anterior_se_rearma_sin_los_bloques_nuevos(tmp_path):
    """Un análisis creado antes del 2026-10-17 se reusa hasta 7 días: no puede romperse."""
    h = oh.armar(fx.pieza_oportunidad(tmp_path, laminas=True, legado=True, fuentes=[]), tmp_path, EJECUTIVO,
                 fx.AUTOR, HOY)
    assert "Lo que pasa hoy" not in h and "Días clave" not in h and "Qué dicen los bancos" not in h
```

- [ ] **Step 3: Correr y ver que fallan**

Run: `uv run pytest tests/test_analista_oportunidad_html.py -q`
Expected: FAIL en los tests nuevos (no existe "Lo que pasa hoy").

- [ ] **Step 4: Implementar en `oportunidad_html.py`**

1. Imports: cambia `from datetime import date` por `from datetime import date, datetime` y agrega `from analista import agenda as ag` junto a los demás imports de `analista`.

2. Después de `_seccion_voces`, agrega:

```python
def _cambio(h: dict[str, Any]) -> str:
    """«bajó 0,288 puntos en 5 sesiones»; las tasas ya traen «pb» y no repiten la unidad."""
    if h.get("sentido") == "estable":
        return "estable en 5 sesiones"
    if h.get("sentido") not in ("subió", "bajó"):
        return "sin dato a 5 sesiones"
    unidad = "" if str(h["cambio_5d"]).endswith(" pb") else f" {h['unidad_cambio']}"
    return f"{h['sentido']} {h['cambio_5d']}{unidad} en 5 sesiones"


def _efecto_hecho(h: dict[str, Any]) -> str:
    partes = [h.get("efecto") or "sin efecto atribuido"]
    if h.get("con_la_lectura"):
        partes.append(h["con_la_lectura"])
    if h.get("proxima_decision"):
        partes.append(f"próxima decisión: {h['proxima_decision']}")
    return " · ".join(partes)


def _tabla_hechos(hechos: list[dict[str, Any]]) -> str:
    if not hechos:
        return ""
    filas = "".join(
        f'<tr><th>{ih.e(h["driver"])}</th><td>{ih.e(h["nivel"])}<br><span class="nota">{ih.e(h["fecha"])} · '
        f'{ih.e(h["fuente"])}</span></td><td>{ih.e(_cambio(h))}</td><td>{ih.e(_efecto_hecho(h))}</td></tr>'
        for h in hechos)
    return ('<p class="rotulo-chico">Lo que pasa hoy con sus drivers</p><table class="hechos"><tr><th>Driver</th>'
            f'<th>Dato</th><th>Cambio</th><th>Qué hace con el activo</th></tr>{filas}</table>')


def _enlace_calendario(texto: str) -> str:
    return f'<a href="{ih.e(ag.URL_CALENDARIO)}" target="_blank" rel="noopener noreferrer">{ih.e(texto)}</a>'


def _agenda_ficha(d: dict[str, Any], dias_clave: str, dir_pedido: Path | None, imagen: str) -> str:
    agenda = d.get("agenda")
    if agenda is None:  # pieza anterior al 2026-10-17: la agenda venía en texto
        lista = d.get("agenda_semana") or []
        return ('<p class="rotulo-chico">Agenda de la semana</p><ul>' + "".join(f"<li>{ih.e(x)}</li>" for x in lista)
                + '</ul>') if lista else ""
    cuerpo = f'<p class="rotulo-chico">Días clave del {ih.e(agenda["desde"])} al {ih.e(agenda["hasta"])}</p>'
    if agenda["estado"] == "sin_calendario":
        return cuerpo + ('<p class="nota">No pude leer el calendario económico para esta ventana: revisa los días '
                         f'clave en el {_enlace_calendario("calendario de Investing.com")} antes de enviar el correo.</p>')
    if not agenda["eventos"]:
        return cuerpo + f'<p>{ih.e(ag.texto_vacia(agenda))}</p>'
    if dias_clave:
        cuerpo += f'<p>{ih.e(dias_clave)}</p>'
    if imagen and dir_pedido is not None and (dir_pedido / imagen).exists():
        cuerpo += (f'<img class="calendario-img" src="{ih._data_uri(dir_pedido / imagen)}" '
                   f'alt="Calendario económico del {ih.e(agenda["desde"])} al {ih.e(agenda["hasta"])}">')
    filas = "".join(
        f'<tr><td>{ih.e(e["dia"])}<br>{ih.e(e["hora"])}</td><td>{ih.e(e["evento"])} · {ih.e(e["pais"])}</td>'
        f'<td>{ih.e(e["anterior"] or "sin dato")}</td><td>{ih.e(e["esperado"] or "sin dato")}</td>'
        f'<td>{ih.e(e["efecto"] or "sin efecto declarado")}</td></tr>' for e in agenda["eventos"])
    return (cuerpo + '<table class="agenda"><tr><th>Cuándo</th><th>Dato</th><th>Previo</th><th>Esperado</th>'
            f'<th>Qué hace con el activo</th></tr>{filas}</table>'
            f'<p class="nota">Fuente: {_enlace_calendario("calendario completo de Investing.com")}.</p>')
```

3. Reemplaza `_seccion_fundamental` entera por:

```python
def _seccion_fundamental(d: dict[str, Any], a: dict[str, Any], contexto: str, dias_clave: str = "",
                         dir_pedido: Path | None = None, imagen: str = "") -> str:
    t = a["ticker"]
    drivers = d["drivers"].get(t, [])
    cuerpo = f'<p>{ih.e(contexto)}</p>' + _tabla_hechos(d.get("hechos") or [])
    if drivers:
        cuerpo += '<p class="rotulo-chico">Drivers del activo</p><ul>' + "".join(f"<li>{ih.e(x)}</li>" for x in drivers) + '</ul>'
    if d["curva"]:
        filas = "".join("<tr>" + "".join(f"<td>{ih.e(c)}</td>" for c in fila) + "</tr>" for fila in d["curva"])
        cuerpo += f'<p class="rotulo-chico">Curva de tasas de EE.UU.</p><table class="curva">{filas}</table>'
    cuerpo += _agenda_ficha(d, dias_clave, dir_pedido, imagen)
    if d["fundamental"]["sin_drivers"]:
        cuerpo += '<p class="nota">Este activo no tiene drivers declarados en el catálogo de la casa.</p>'
    return _seccion("Fundamental", cuerpo)
```

4. Después de `_simulacion_correo` (y antes de `_alto_png`, o después: `_alto_png` es una función del módulo, el orden no importa en tiempo de llamada), agrega:

```python
def _hechos_correo(hechos: list[dict[str, Any]], c: dict[str, str]) -> str:
    if not hechos:
        return ""
    lineas = []
    for h in hechos:
        cola = ""
        if h.get("efecto"):
            efecto = h["efecto"][:1].upper() + h["efecto"][1:]
            cola = f" {ih.e(efecto)}" + (f", {ih.e(h['con_la_lectura'])}" if h.get("con_la_lectura") else "") + "."
        lineas.append(_p(f'<strong style="color:{c["texto_1"]};">{ih.e(h["driver"])}:</strong> {ih.e(h["nivel"])} al '
                         f'{ih.e(h["fecha"])}, {ih.e(_cambio(h))}.{cola}', c, tam=15, margen="0 0 6px 0"))
    return _rotulo("Lo que pasa hoy", c, margen="10px 0 8px 0") + "".join(lineas)


def _dias_clave_correo(d: dict[str, Any], dias_clave: str, dir_pedido: Path, imagen: str, c: dict[str, str]) -> str:
    """Sin calendario el bloque no va: «no pude leer» no es texto de cliente."""
    agenda = d.get("agenda")
    if not agenda or agenda["estado"] == "sin_calendario":
        return ""
    cuerpo = _rotulo(f'Días clave hasta el {ih.e(agenda["hasta"])}', c, margen="14px 0 8px 0")
    if not agenda["eventos"]:
        return cuerpo + _p(ih.e(ag.texto_vacia(agenda)), c, tam=15)
    if dias_clave:
        cuerpo += _p(ih.e(dias_clave), c, tam=15)
    ruta = dir_pedido / imagen if imagen else None
    if ruta is not None and ruta.exists():
        cuerpo += _tabla(
            f'<tr><td style="padding:0;"><img src="{ih._data_uri(ruta)}" width="558" height="{_alto_png(ruta, 558)}" '
            f'alt="Calendario económico del {ih.e(agenda["desde"])} al {ih.e(agenda["hasta"])}" '
            'style="display:block;border:0;width:558px;max-width:100%;height:auto;border-radius:11px;"></td></tr>',
            estilo=f'border:1px solid {c["linea"]};border-radius:12px;') + _separador(8)
    return cuerpo + _p(f'<a href="{ih.e(ag.URL_CALENDARIO)}" style="color:{c["acento"]};">Ver el calendario '
                       'económico completo</a>', c, tam=14)


def _fecha_es(iso: str) -> str:
    try:
        return datetime.strptime(iso, "%Y-%m-%d").strftime("%d/%m/%Y")
    except ValueError:
        return iso


def _voces_correo(fuentes: list[dict[str, Any]], direccion: str, c: dict[str, str]) -> str:
    if not fuentes:
        return ""
    items, hay_discrepancia = [], False
    for f in fuentes:
        discrepa = fu.discrepa(f, direccion)
        hay_discrepancia |= discrepa
        marca = (f' <span style="color:{c["baja"]};font-weight:700;">(ve distinto que nuestra lectura)</span>'
                 if discrepa else "")
        items.append(_p(f'<strong style="color:{c["texto_1"]};">{ih.e(f["entidad"])}</strong> · {ih.e(f["medio"])} · '
                        f'{ih.e(_fecha_es(f["fecha"]))}{marca}<br>{ih.e(f["tesis"])} '
                        f'<a href="{ih.e(f["url"])}" style="color:{c["acento"]};">Ver nota</a>', c, tam=15,
                        margen="0 0 10px 0"))
    nota = (_p("Cuando un banco ve distinto, lo decimos: la lectura que manda es la nuestra.", c, tam=14,
               color="texto_2") if hay_discrepancia else "")
    return _rotulo("Qué dicen los bancos", c, margen="14px 0 8px 0") + "".join(items) + nota
```

5. En `_bloque_correo`, cambia la firma a:

```python
def _bloque_correo(a: dict[str, Any], titular: str, contexto: str, dir_pedido: Path, ejecutivo: str,
                   c: dict[str, str], d: dict[str, Any] | None = None, dias_clave: str = "",
                   fuentes: list[dict[str, Any]] | tuple = (), imagen_calendario: str = "") -> str:
```

y reemplaza la línea `+ _p(ih.e(contexto), c)` por:

```python
        + _p(ih.e(contexto), c)
        + _hechos_correo((d or {}).get("hechos") or [], c)
        + _dias_clave_correo(d or {}, dias_clave, dir_pedido, imagen_calendario, c)
        + _voces_correo(list(fuentes), lec["direccion"], c)
```

6. En `armar`, dentro del `for a in d["activos"]:` y después de `lamina = ...`, agrega:

```python
        dias = (ed.get("dias_clave") or {}).get(t, "")
        imagen_cal = (pieza.get("imagenes") or {}).get("calendario", "")
```

reemplaza `+ _seccion_fundamental(d, a, ed["contexto"][t])` por `+ _seccion_fundamental(d, a, ed["contexto"][t], dias, dir_pedido, imagen_cal)`, y reemplaza `f'{_bloque_correo(a, ed["titulares"][t], ed["contexto"][t], dir_pedido, nombre_ej, c)}</template>'` por:

```python
                       f'{_bloque_correo(a, ed["titulares"][t], ed["contexto"][t], dir_pedido, nombre_ej, c, d=d, dias_clave=dias, fuentes=ed["fuentes"], imagen_calendario=imagen_cal)}</template>'
```

7. En `templates/oportunidad/pieza.html`, después de la línea `.voces a{color:var(--acento)}` agrega:

```css
  table.hechos,table.agenda,table.curva{width:100%;border-collapse:collapse;margin:8px 0 12px;font-size:14px}
  table.hechos th,table.hechos td,table.agenda th,table.agenda td,table.curva td{padding:8px 10px;border-bottom:1px solid var(--linea);text-align:left;vertical-align:top}
  .calendario-img{display:block;width:100%;border-radius:12px;margin:8px 0}
```

- [ ] **Step 5: Correr los tests**

Run: `uv run pytest tests/test_analista_*.py -q`
Expected: todo `passed`. Los tests que hacen `re.search` del primer `<img ... width="558"` siguen pasando porque el gráfico va antes del calendario.

- [ ] **Step 6: Mirar la ficha (manual)**

```bash
uv run python -c "
import sys; sys.path[:0] = ['src', 'scripts', 'tests']
from datetime import date; from pathlib import Path
import analista_fixtures as fx; from analista import oportunidad_html as oh
d = Path('data/informes_analistas/_revision_texto_concreto'); d.mkdir(parents=True, exist_ok=True)
print(oh.guardar(fx.pieza_oportunidad(d, laminas=True), d, {'nombre': 'Camila Rojas', 'cargo': 'x', 'contacto': ''}, fx.AUTOR, date(2026, 10, 12)))
"
```
Ábrela en el navegador: la tabla de hechos y la de días clave se leen sin desbordarse, y el correo (botón de vista previa) muestra los tres bloques. Borra la carpeta `_revision_texto_concreto` después (está bajo `data/informes_analistas/`, que es gitignorado).

- [ ] **Step 7: Commit**

```bash
git add tests/analista_fixtures.py scripts/analista/oportunidad_html.py templates/oportunidad/pieza.html tests/test_analista_oportunidad_html.py
git commit -m "feat(bot): la ficha y el correo llevan hechos, días clave y bancos con enlace

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Preparar mide, arma la agenda y rinde el calendario

**Files:**
- Modify: `scripts/analista/preparar.py:37-47` (lectores reales), `:222-237` (`Lectores`), `:305-348` (`preparar_oportunidad`)
- Test: `tests/test_analista_preparar.py` (modificar `_lectores` y agregar)

**Interfaces:**
- Consumes: `agenda.leer_ventana`, `agenda.payload_lamina`, `agenda.texto_vacia`, `agenda.URL_CALENDARIO` (Task 2); `hechos.medir`, `hechos.leer_d1_mt5` (Task 3); `indices_referencia.serie_diaria`; `story_render.render_story`.
- Produces: `Lectores.agenda(ahora, ticker, nombre) -> agenda.Agenda`, `Lectores.hechos(ticker, nombre, direccion, curva, eventos, ahora) -> (hechos, avisos)`, `Lectores.rendir_calendario(payload, destino) -> Path`. `datos.hechos`, `datos.agenda` (sin `%`), `imagenes.calendario` y `anidados.dias_clave` cuando hay eventos. `datos.agenda_semana` deja de existir en piezas nuevas.

- [ ] **Step 1: Ajustar el lector falso y escribir los tests**

En `tests/test_analista_preparar.py`:

1. Agrega a los imports `from analista import agenda as ag  # noqa: E402`.
2. En `_lectores`, reemplaza `agenda=lambda a: ([], [])` por:

```python
        agenda=lambda ahora, t, n: ag.Agenda("lunes 12/10", "lunes 19/10", "vacia"),
        hechos=lambda t, n, direccion, curva, eventos, ahora: ([], []),
        rendir_calendario=_calendario_falso,
```

3. Antes de `_lectores`, agrega:

```python
CALENDARIOS: list[dict] = []


def _calendario_falso(payload, destino):
    CALENDARIOS.append(payload)
    destino.write_bytes(fx.PNG)
    return destino


EVENTO = {"fecha": "2026-10-14", "dia": "miércoles 14/10", "hora": "09:30 CLST", "evento": "IPC",
          "fuente_nombre": "CPI (MoM) (Sep)", "pais": "EE.UU.", "anterior": "0,4%", "esperado": "0,3%",
          "explicacion": "", "efecto": "Si sale sobre lo esperado, el oro tiende a bajar; si sale bajo lo esperado, lo contrario.",
          "mueve_al_activo": True}
HECHO = {"id": "dxy", "driver": "Dollar Index (DXY)", "fecha": "viernes 09/10", "en_curso": False, "nivel": "101,560",
         "cambio_1d": "0,193", "cambio_5d": "0,288", "unidad_cambio": "puntos", "sentido": "bajó",
         "sentido_1d": "bajó", "fuente": "MT5 (USDIDX)", "efecto": "juega a favor del alza del oro",
         "con_la_lectura": "va en contra de nuestra lectura"}
```

4. Agrega al final de la sección del análisis (antes de `# ─── seguimiento`):

```python
def _con_agenda(estado, eventos=()):
    return lambda ahora, t, n: ag.Agenda("lunes 12/10", "lunes 19/10", estado, [dict(e) for e in eventos],
                                         ["el calendario no respondió (X)"] if estado == "sin_calendario" else [])


def test_con_eventos_rinde_el_calendario_y_pide_dias_clave(tmp_path):
    CALENDARIOS.clear()
    lec = _lectores(tmp_path / "ref", agenda=_con_agenda("ok", [EVENTO]))
    p = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES, lec).pieza
    assert p["imagenes"]["calendario"] == "calendario_xauusd.png" and (tmp_path / "p" / "calendario_xauusd.png").exists()
    assert p["anidados"]["dias_clave"] == ["XAUUSD"] and p["editorial"]["dias_clave"] == {"XAUUSD": es.MARCA}
    assert "%" not in json.dumps(p["datos"]["agenda"], ensure_ascii=False)
    assert p["datos"]["agenda"]["eventos"][0]["esperado"] == "0,3 por ciento"
    assert CALENDARIOS[-1]["eventos"][0]["dia"] == "MIÉRCOLES 14/10" and "agenda_semana" not in p["datos"]


def test_la_ventana_vacia_avisa_sus_fechas_y_no_pide_dias_clave(tmp_path):
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES,
                        _lectores(tmp_path / "ref"))
    assert "dias_clave" not in hecha.pieza["anidados"] and "calendario" not in hecha.pieza["imagenes"]
    assert any("lunes 12/10" in a and "lunes 19/10" in a for a in hecha.avisos)


def test_sin_calendario_avisa_con_el_enlace(tmp_path):
    lec = _lectores(tmp_path / "ref", agenda=_con_agenda("sin_calendario"))
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES, lec)
    assert any("investing.com/economic-calendar" in a for a in hecha.avisos)
    assert any("no respondió" in a for a in hecha.avisos)


def test_los_hechos_se_miden_con_la_direccion_y_la_agenda_y_quedan_sellados(tmp_path):
    llamadas = []

    def hechos(t, n, direccion, curva, eventos, ahora):
        llamadas.append((t, n, direccion, eventos))
        return [dict(HECHO)], ["sin dato de Tasa real"]

    lec = _lectores(tmp_path / "ref", agenda=_con_agenda("ok", [EVENTO]), hechos=hechos)
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES, lec)
    assert hecha.pieza["datos"]["hechos"] == [HECHO]
    assert llamadas[0][:3] == ("XAUUSD", "Oro", "ALCISTA") and llamadas[0][3][0]["dia"] == "miércoles 14/10"
    assert any("Tasa real" in a for a in hecha.avisos)


def test_sin_ningun_hecho_se_avisa(tmp_path):
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES,
                        _lectores(tmp_path / "ref"))
    assert hecha.pieza["datos"]["hechos"] == [] and any("No medí ningún driver" in a for a in hecha.avisos)


def test_si_el_calendario_no_rinde_la_pieza_sale_con_la_tabla(tmp_path):
    def roto(payload, destino):
        raise RuntimeError("sin chromium")

    lec = _lectores(tmp_path / "ref", agenda=_con_agenda("ok", [EVENTO]), rendir_calendario=roto)
    hecha = pr.preparar(Orden("oportunidad", {"ticker": "XAUUSD"}), tmp_path / "p", AHORA_LUNES, lec)
    assert "calendario" not in hecha.pieza["imagenes"] and hecha.pieza["datos"]["agenda"]["eventos"]
    assert any("imagen del calendario" in a for a in hecha.avisos)
```

- [ ] **Step 2: Correr y ver que fallan**

Run: `uv run pytest tests/test_analista_preparar.py -q`
Expected: FAIL (`Lectores.__init__() got an unexpected keyword argument 'hechos'`).

- [ ] **Step 3: Implementar**

En `scripts/analista/preparar.py`:

1. Reemplaza `_agenda` por:

```python
def _agenda(ahora: datetime, ticker: str, nombre: str):
    """Los datos de alto impacto de los 7 días de vigencia (spec 2026-10-17 §3)."""
    from analista import agenda as ag

    return ag.leer_ventana(ahora, ticker, nombre)


def _hechos(ticker: str, nombre: str, direccion: str, curva: dict[str, Any], eventos: list[dict[str, Any]],
            ahora: datetime) -> tuple[list[dict[str, Any]], list[str]]:
    """Los drivers del día medidos en el terminal y la curva (spec 2026-10-17 §2)."""
    from market_data_mcp.indices_referencia import serie_diaria

    from analista import hechos as hc

    return hc.medir(ticker, nombre, direccion, curva, eventos, hc.leer_d1_mt5, ahora.astimezone(SANTIAGO).date(),
                    respaldo_dxy=lambda n: serie_diaria("DXY", n))


def _rendir_calendario(payload: dict[str, Any], destino: Path) -> Path:
    """La lámina del calendario con la plantilla `calendario` de Stories (1920×1080)."""
    import pipeline_avisos as pa
    from story_render import render_story

    render_story(payload, pa.DIR_PLANTILLAS / "calendario.html", destino, formato="horizontal")
    return destino
```

2. En `Lectores`, reemplaza la línea `agenda: Callable[[datetime], tuple[list[dict[str, Any]], list[str]]] = _agenda` por:

```python
    agenda: Callable[[datetime, str, str], Any] = _agenda
    hechos: Callable[..., tuple[list[dict[str, Any]], list[str]]] = _hechos
    rendir_calendario: Callable[[dict[str, Any], Path], Path] = _rendir_calendario
```

3. En `preparar_oportunidad`, reemplaza desde `agenda, av = lec.agenda(ahora)` hasta el `return Preparada(pieza, avisos)` final por:

```python
    from analista import agenda as ag

    nombre = activo["nombre"]
    agenda = lec.agenda(ahora, ticker, nombre)
    avisos += [f"agenda: {a}" for a in agenda.avisos]
    if agenda.estado == "sin_calendario":
        avisos.append(f"No pude leer el calendario económico: revisa los días clave en {ag.URL_CALENDARIO} "
                      "antes de enviar el correo.")
    elif agenda.estado == "vacia":
        avisos.append(ag.texto_vacia(agenda.a_dict()) + " La ficha muestra la ventana completa.")
    curva, av = lec.curva()
    avisos += [f"contexto sin curva de tasas: {a}" for a in av]
    hechos, av = lec.hechos(ticker, nombre, referencia.direccion, curva, agenda.eventos, ahora)
    avisos += [f"drivers del día: {a}" for a in av]
    if not hechos:
        avisos.append("No medí ningún driver del día: el contexto sale sin cifras propias.")
    drivers = lec.drivers(ticker)
    # Sin "%": la pieza no muestra porcentajes y una cifra con "%" en los datos invitaría a agy a citarla.
    limpio = _contexto_sin_porcentajes({"curva": _filas_curva(curva), "agenda": agenda.a_dict(), "hechos": hechos})
    imagenes = {ticker: activo["grafico"]}
    extra = {"titulares": [ticker], "contexto": [ticker]}
    if limpio["agenda"]["eventos"]:
        extra["dias_clave"] = [ticker]
        nombre_cal = f"calendario_{ticker.lower().replace('.', '_')}.png"
        try:
            lec.rendir_calendario(ag.payload_lamina(limpio["agenda"]), dir_pedido / nombre_cal)
            imagenes["calendario"] = nombre_cal
        except Exception as exc:  # noqa: BLE001  la tabla de la ficha sigue: la imagen es un extra
            avisos.append(f"No pude rendir la imagen del calendario ({exc.__class__.__name__}): la ficha lleva la tabla.")
    datos = {"ticker": ticker, "chip": "ANÁLISIS TÉCNICO Y FUNDAMENTAL",
             "edicion": fecha_corta(ahora) + f" · {ahora.astimezone(SANTIAGO):%H:%M}",
             "vigencia": {"desde": fecha_corta(ahora), "hasta": fecha_corta(ahora + rg.VIGENCIA)},
             "activos": [activo], "drivers": {ticker: drivers}, "hechos": limpio["hechos"],
             "agenda": limpio["agenda"], "curva": limpio["curva"],
             "fundamental": {"fuera_catalogo": bool(cat.get("fuera_catalogo")), "sin_drivers": not drivers,
                             "referencia": origen}}
    pieza = es.nueva_pieza("oportunidad", {"ticker": ticker}, datos, imagenes, extra_campos=extra)
    return Preparada(pieza, avisos)
```

(La línea `sin_pct = _contexto_sin_porcentajes({"curva": _filas_curva(curva)})` y el `datos = {...}` anterior desaparecen: los reemplaza este bloque.)

- [ ] **Step 4: Correr los tests**

Run: `uv run pytest tests/test_analista_*.py -q`
Expected: todo `passed`. `test_la_curva_va_sin_porcentajes` sigue pasando (la curva pasa por el mismo `_contexto_sin_porcentajes`).

- [ ] **Step 5: Probar la preparación real (manual, requiere MT5 abierto y red)**

```bash
uv run --with MetaTrader5 --extra stories python -c "
import sys, json; sys.path[:0] = ['src', 'scripts']
from pathlib import Path
from analista import preparar as pr
from analista.orden import Orden
d = Path('data/informes_analistas/_medicion/oro_preparar')
h = pr.preparar(Orden('oportunidad', {'ticker': 'XAUUSD'}), d)
print('\n'.join(h.avisos))
print(json.dumps(h.pieza['datos']['hechos'], ensure_ascii=False, indent=1)[:1500])
print(h.pieza['datos']['agenda']['estado'], len(h.pieza['datos']['agenda']['eventos']), h.pieza['imagenes'])
"
```
Expected: hechos `dxy`, `tasa_real` y `fed` con fecha y efecto; agenda `ok` con eventos de los próximos 7 días (o `sin_calendario` con el aviso si Investing.com responde 403: el 2026-10-17 a las 13 h respondió 403 a una consulta directa). Abre `calendario_xauusd.png` con la herramienta de lectura de imágenes y verifica que las tildes, el `·` y "por ciento" se vean bien y que nada se desborde. Si "0,3 por ciento" no cabe en su casilla, anótalo para el director (spec §3) y no cambies la plantilla de Stories en esta task.

- [ ] **Step 6: Commit**

```bash
git add scripts/analista/preparar.py tests/test_analista_preparar.py
git commit -m "feat(bot): preparar sella los hechos del día, la agenda de la ventana y su calendario

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Sin banco no sale: segundo intento y validación

**Files:**
- Modify: `scripts/analista/agy.py`
- Modify: `scripts/analista/bot.py:195-266` (`_agy_real`, `Atendedor`, `_redactar_y_validar`) y `:316-329` (`_oportunidad`)
- Modify: `scripts/bot_analistas.py:41-52` (`validar`)
- Test: `tests/test_analista_agy.py`, `tests/test_analista_bot.py`

**Interfaces:**
- Consumes: `fuentes.bancos`, `fuentes.falta_banco`, `fuentes.guardar_intento`, `fuentes.INTENTO` (Task 4); `esquema.MARCA`.
- Produces: `agy.escribir_textos(ruta, tier="flash", timeout=TIMEOUT)`, `agy.TIMEOUT_REINTENTO = "15m"`; `Atendedor.redactar_fuentes: Callable[[Path, str], Any]`; `bot.SIN_BANCO`; `agy_salida_<n>.json` en la carpeta del pedido; `bot_analistas.validar` falla sin banco.

- [ ] **Step 1: Escribir los tests de `agy`**

Agrega a `tests/test_analista_agy.py`:

```python
def _minutos(t):
    return int(re.fullmatch(r"(\d+)m", t).group(1))


def test_el_reintento_de_fuentes_tiene_su_propio_techo_menor():
    assert 10 <= _minutos(agy.TIMEOUT_REINTENTO) < _minutos(agy.TIMEOUT)


def test_escribir_textos_pasa_el_timeout_pedido(monkeypatch, tmp_path):
    import agy_encargo

    pedidos = tmp_path / "data" / "informes_analistas"
    (pedidos / "p").mkdir(parents=True)
    (pedidos / "p" / "pieza.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(agy, "RAIZ", tmp_path)
    monkeypatch.setattr(agy, "DIR_PEDIDOS", pedidos)
    vistos = []
    monkeypatch.setattr(agy_encargo, "invocar", lambda prompt, tier, timeout: vistos.append((prompt, timeout)))
    agy.escribir_textos(pedidos / "p" / "pieza.json", "flash", agy.TIMEOUT_REINTENTO)
    agy.escribir_textos(pedidos / "p" / "pieza.json")
    assert vistos == [("/analista data/informes_analistas/p/pieza.json", agy.TIMEOUT_REINTENTO),
                      ("/analista data/informes_analistas/p/pieza.json", agy.TIMEOUT)]
```

- [ ] **Step 2: Implementar `agy.py`**

Reemplaza desde `# Un encargo real de agy tarda...` hasta el final del archivo por:

```python
# Un encargo real de agy tarda de 5 a 7 minutos (medido el 2026-09-06). Con búsqueda web de 3 a 5
# fuentes medimos 424 s y 652 s el 2026-10-16; el techo deja el doble más la validación. Los hechos
# del día no suman búsquedas: los mide Python (spec 2026-10-17 §8).
TIMEOUT = "25m"
# El segundo intento solo busca fuentes de bancos (spec 2026-10-17 §5).
TIMEOUT_REINTENTO = "15m"


class RutaFueraDePedidos(ValueError):
    pass


def escribir_textos(ruta_pieza: Path, tier: str = "flash", timeout: str = TIMEOUT):
    """Lanza `/analista <ruta>` y devuelve el `Resultado` de `agy_encargo`."""
    from agy_encargo import invocar

    ruta = Path(ruta_pieza).resolve()
    if DIR_PEDIDOS.resolve() not in ruta.parents or ruta.name != "pieza.json":
        raise RutaFueraDePedidos(f"{ruta} no es una pieza de data/informes_analistas/")
    relativa = ruta.relative_to(RAIZ.resolve()).as_posix()
    return invocar(f"/analista {relativa}", tier, timeout)
```

Run: `uv run pytest tests/test_analista_agy.py -q`
Expected: `3 passed`.

- [ ] **Step 3: Escribir los tests del bot**

En `tests/test_analista_bot.py`:

1. Agrega a los imports `from analista import fuentes as fu  # noqa: E402`.
2. En `redactor`, después de `pieza["editorial"].update(fx.pieza_oportunidad(dir_pedido)["editorial"])` agrega:

```python
        # La fuente del ejemplo es posterior al reloj de estas pruebas: con su fecha, depurar la descarta.
        pieza["editorial"]["fuentes"] = [{**fx.FUENTES_EJEMPLO[0], "fecha": "2026-10-06"}]
```

3. En `Armado.__init__`, agrega `self.reintentos: list = []` antes de crear el `Atendedor`, pasa `redactar_fuentes=self.redactar_fuentes_falso` al `b.Atendedor(...)`, y agrega el método:

```python
    def redactar_fuentes_falso(self, ruta, tier):
        """Por defecto el segundo intento no escribe nada: cada prueba que lo usa lo reemplaza."""
        self.reintentos.append(ruta)
        return SimpleNamespace(codigo="ok", detalle="")
```

4. Reemplaza `test_sin_voces_validas_la_pieza_sale_y_lo_dice` entero por:

```python
def test_sin_voces_validas_ni_en_el_reintento_no_sale_ni_gasta_cupo(armado):
    def redactar(ruta, tier):
        pieza = pr.cargar_pieza(ruta.parent)
        pieza["editorial"].update(fx.pieza_oportunidad(ruta.parent)["editorial"])
        pieza["editorial"]["fuentes"] = "no sé"
        pr.guardar_pieza(pieza, ruta.parent)
        return SimpleNamespace(codigo="ok", detalle="")

    armado.atendedor.redactar = redactar
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert not r.archivos and "ninguna voz de banco" in r.texto and "No gasté tu cupo" in r.texto
    assert armado.estado.usados(CAMILA, AHORA) == 0 and rg.vigente("XAUUSD", AHORA, armado.registro) is None
    assert len(armado.reintentos) == 1
```

5. Agrega al final del archivo:

```python
# ───────────────────────────────────────────── un banco o nada (spec 2026-10-17 §5)

BANCO = {**fx.FUENTES_EJEMPLO[0], "fecha": "2026-10-06"}
WGC = {"entidad": "World Gold Council", "medio": "World Gold Council", "fecha": "2026-10-06",
       "url": "https://www.gold.org/goldhub/research/demanda-octubre", "postura": "alcista",
       "tesis": "World Gold Council ve demanda firme de los bancos centrales.", "verificacion": "ok"}


def test_con_banco_al_primer_intento_no_hay_reintento(armado):
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert r.archivos and armado.reintentos == [] and "segundo intento" not in r.aparte
    carpeta = next((armado.tmp / "pedidos").rglob("pieza.json")).parent
    assert (carpeta / "agy_salida_1.json").exists() and not (carpeta / fu.INTENTO).exists()


def test_sin_banco_el_reintento_solo_reabre_las_fuentes_y_la_pieza_sale(armado):
    vistos = []

    def fuentes_falso(ruta, tier):
        pieza = pr.cargar_pieza(ruta.parent)
        vistos.append(json.loads(json.dumps(pieza["editorial"])))
        pieza["editorial"]["fuentes"] = [WGC, BANCO]
        pr.guardar_pieza(pieza, ruta.parent)
        return SimpleNamespace(codigo="ok", detalle="", respuesta="OK", segundos=61.0)

    armado.atendedor.redactar = _redactor_con_fuentes([WGC])
    armado.atendedor.redactar_fuentes = fuentes_falso
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert r.archivos and "segundo intento" in r.aparte
    assert vistos[0]["fuentes"] == es.MARCA and vistos[0]["contexto"]["XAUUSD"] != es.MARCA
    carpeta = next((armado.tmp / "pedidos").rglob("pieza.json")).parent
    intento = json.loads((carpeta / fu.INTENTO).read_text(encoding="utf-8"))
    assert [f["entidad"] for f in intento["validas"]] == ["World Gold Council"]
    salida = json.loads((carpeta / "agy_salida_2.json").read_text(encoding="utf-8"))
    assert salida["segundos"] == 61.0 and salida["respuesta"] == "OK"
    assert [f["entidad"] for f in pr.cargar_pieza(carpeta)["editorial"]["fuentes"]] == ["World Gold Council", "Goldman Sachs"]


def test_sin_banco_en_dos_intentos_dice_los_descartes(armado):
    roto = {**BANCO, "url": "https://blog.example.com/oro"}  # dominio que no es de Reuters
    armado.atendedor.redactar = _redactor_con_fuentes([WGC, roto])
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert "ninguna voz de banco" in r.texto and "Goldman Sachs: el dominio" in r.texto
    assert armado.estado.usados(CAMILA, AHORA) == 0


def test_validar_exige_una_voz_de_banco(tmp_path, capsys):
    import bot_analistas

    pr.guardar_pieza(fx.pieza_oportunidad(tmp_path, fuentes=[WGC]), tmp_path)
    assert bot_analistas.validar(tmp_path / "pieza.json") == 1
    assert "voz de banco" in capsys.readouterr().out
    pr.guardar_pieza(fx.pieza_oportunidad(tmp_path), tmp_path)
    assert bot_analistas.validar(tmp_path / "pieza.json") == 0
```

- [ ] **Step 4: Correr y ver que fallan**

Run: `uv run pytest tests/test_analista_bot.py -q`
Expected: FAIL (`Atendedor.__init__() got an unexpected keyword argument 'redactar_fuentes'`).

- [ ] **Step 5: Implementar en `bot.py`**

1. Después de `_agy_real`, agrega:

```python
def _agy_fuentes_real(ruta_pieza: Path, tier: str):
    """El segundo intento: solo `fuentes` sigue por escribir, con un techo menor (spec 2026-10-17 §5)."""
    from analista.agy import TIMEOUT_REINTENTO, escribir_textos

    return escribir_textos(ruta_pieza, tier, TIMEOUT_REINTENTO)


SIN_BANCO = ("No encontré ninguna voz de banco con su nota vigente (de los últimos {dias} días) sobre {nombre}, "
             "ni en un segundo intento, y sin ella el análisis no sale. No gasté tu cupo: vuelve a pedirlo más "
             "tarde, cada pedido hace una búsqueda nueva.")


def _guardar_salida_agy(dir_pedido: Path, res: Any, intento: int) -> None:
    """Lo que respondió agy, para auditar si buscó (spec 2026-10-17 §5.4). Nunca bota el pedido."""
    datos = {"intento": intento, "codigo": getattr(res, "codigo", "ok"), "segundos": getattr(res, "segundos", None),
             "respuesta": str(getattr(res, "respuesta", "") or "")[:20000]}
    try:
        (dir_pedido / f"agy_salida_{intento}.json").write_text(json.dumps(datos, ensure_ascii=False, indent=2),
                                                                encoding="utf-8")
    except OSError:
        pass
```

2. En `Atendedor`, después de `redactar: Callable[[Path, str], Any] = _agy_real`, agrega:

```python
    redactar_fuentes: Callable[[Path, str], Any] = _agy_fuentes_real
```

3. Reemplaza `_redactar_y_validar` entero por:

```python
    def _redactar_y_validar(self, dir_pedido: Path, hoy, redactar: Callable[[Path, str], Any] | None = None,
                            intento: int = 1) -> tuple[dict[str, Any], list[str], list[Any]]:
        res = (redactar or self.redactar)(dir_pedido / "pieza.json", self.config["tier"])
        _guardar_salida_agy(dir_pedido, res, intento)
        if getattr(res, "codigo", "ok") != "ok":
            raise FalloPedido(f"La redacción no terminó ({res.codigo}: {res.detalle}). No gasté tu cupo.")
        pieza = pr.cargar_pieza(dir_pedido)
        crudas = pieza["editorial"].get("fuentes")
        crudas = list(crudas) if isinstance(crudas, list) else []
        pieza, descartes = fu.depurar_pieza(pieza, hoy, verificar=self.verificar_url)
        # Una tesis con un defecto de texto descarta solo esa voz, no la pieza (spec §9).
        pieza, rotas = es.descartar_tesis_rotas(pieza)
        descartes += rotas
        pr.guardar_pieza(pieza, dir_pedido)
        errores = es.errores(pieza)
        if errores:
            raise FalloPedido("El texto no pasó los controles y no lo entrego así:\n• " + "\n• ".join(errores[:6]))
        return pieza, descartes, crudas

    def _con_banco(self, dir_pedido: Path, hoy) -> tuple[dict[str, Any], list[str], bool]:
        """La pieza con al menos una voz de banco válida; si el primer intento no la trae, un segundo solo de fuentes.

        Spec 2026-10-17 §5: un análisis sin banco vigente no se publica. El segundo intento reabre
        solo `fuentes` (los demás textos ya pasaron los controles) y deja escrito qué se descartó.
        """
        pieza, descartes, crudas = self._redactar_y_validar(dir_pedido, hoy)
        if fu.bancos(pieza["editorial"]["fuentes"]):
            return pieza, descartes, False
        fu.guardar_intento(dir_pedido, pieza["editorial"]["fuentes"], descartes, crudas)
        pieza["editorial"]["fuentes"] = es.MARCA
        pr.guardar_pieza(pieza, dir_pedido)
        pieza, descartes2, _ = self._redactar_y_validar(dir_pedido, hoy, self.redactar_fuentes, intento=2)
        if fu.bancos(pieza["editorial"]["fuentes"]):
            return pieza, descartes + descartes2, True
        motivos = [*descartes, *descartes2][:4]
        texto = SIN_BANCO.format(dias=fu.cargar_lista().get("frescura_dias", 14),
                                 nombre=pieza["datos"]["activos"][0]["nombre"])
        raise FalloPedido(texto + ("\nLo que descarté:\n• " + "\n• ".join(motivos) if motivos else ""))
```

4. En `_oportunidad`, reemplaza `pieza, descartes = self._redactar_y_validar(dir_pedido, ahora.date())` por:

```python
            pieza, descartes, reintento = self._con_banco(dir_pedido, ahora.date())
```

y reemplaza:

```python
            if not pieza["editorial"]["fuentes"]:
                avisos.append("Sin voces de bancos o prensa atingentes esta vez: el análisis sale con nuestra lectura.")
```

por:

```python
            if reintento:
                avisos.append("La primera búsqueda no trajo ninguna voz de banco: hice un segundo intento y ese sí la trajo.")
```

5. En `scripts/bot_analistas.py`, reemplaza `validar` por:

```python
def validar(ruta: Path) -> int:
    from analista import esquema as es
    from analista import fuentes as fu
    from analista.preparar import cargar_pieza

    pieza = cargar_pieza(ruta.parent)
    errores = es.errores(pieza)
    # El mínimo de un banco va acá y en el bot, no en `esquema.errores`: así una pieza anterior sin
    # bancos se sigue rearmando al reusarla (spec 2026-10-17 §5).
    if pieza.get("orden", {}).get("pieza") == "oportunidad":
        errores += fu.falta_banco(pieza)
    if errores:
        for e in errores:
            print(f"ERROR: {e}")
        return 1
    print("OK")
    return 0
```

- [ ] **Step 6: Correr los tests**

Run: `uv run pytest tests/test_analista_*.py -q`
Expected: todo `passed`, incluido `test_el_bot_no_puede_publicar_en_whatsapp`.

- [ ] **Step 7: Commit**

```bash
git add scripts/analista/agy.py scripts/analista/bot.py scripts/bot_analistas.py tests/test_analista_agy.py tests/test_analista_bot.py
git commit -m "feat(bot): un análisis sin voz de banco no sale; segundo intento solo de fuentes

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Las instrucciones de agy

**Files:**
- Modify: `.claude/commands/analista.md`
- Test: `tests/test_analista_instrucciones.py` (agregar)

**Interfaces:**
- Consumes: los campos de `datos.hechos`, `datos.agenda`, `editorial.dias_clave`, `fuentes_intento_1.json` y el error de `--validar` (Tasks 3 a 8).
- `.agents/workflows/analista.md` es un puntero a este archivo: no se regenera.

- [ ] **Step 1: Escribir los tests**

Agrega a `tests/test_analista_instrucciones.py`:

```python
def test_manda_citar_los_hechos_del_dia_y_ya_no_el_mecanismo_condicional():
    assert "datos.hechos" in TEXTO and "con_la_lectura" in TEXTO and "en_curso" in TEXTO
    assert "como mecanismo condicional si no hay un hecho medido" not in TEXTO


def test_explica_los_dias_clave():
    assert "dias_clave" in TEXTO and "datos.agenda" in TEXTO and "420" in TEXTO


def test_exige_un_banco_y_explica_el_segundo_intento():
    bajo = TEXTO.lower()
    assert "al menos una de un banco" in bajo and "fuentes_intento_1.json" in TEXTO
    assert "lista vacía" not in bajo  # ya no se permite entregar fuentes vacías
```

Run: `uv run pytest tests/test_analista_instrucciones.py -q`
Expected: FAIL en los tres tests nuevos.

- [ ] **Step 2: Editar `.claude/commands/analista.md`**

1. En «Qué puedes tocar», reemplaza el primer punto por:

```markdown
- **Solo** los valores de `editorial` que hoy dicen exactamente `[[ESCRIBIR]]`, incluidos los
  de `editorial.titulares`, `editorial.contexto` y `editorial.dias_clave` (uno por ticker; `dias_clave`
  existe solo si la agenda trae datos) y `editorial.fuentes`.
- **Segundo intento.** Si `editorial.fuentes` es lo único que dice `[[ESCRIBIR]]` y junto a la pieza
  existe `fuentes_intento_1.json`, el primer intento no trajo ninguna voz de banco. Vuelve a incluir
  tal cual las fuentes de `validas`, no repitas ninguna URL de `descartadas` (sus `motivos` dicen por
  qué cayeron) y agrega al menos una de un banco. No toques los demás textos: ya pasaron los controles.
```

2. Reemplaza la regla 2 por:

```markdown
2. **Solo afirmas lo medido, y lo medido se cita.** `datos.hechos` trae el estado real de los drivers
   del activo, ya medido por el bot: `driver`, `nivel`, `fecha`, `sentido` y `cambio_5d` (cinco
   sesiones), `efecto` sobre el activo y `con_la_lectura` (si acompaña o va en contra de nuestra
   lectura). `datos.agenda` trae los datos de alto impacto de los 7 días de vigencia, con `dia`, `hora`,
   `esperado`, `anterior` y su `efecto` sobre el activo. `datos.curva` trae la curva de tasas.
   `datos.drivers.<ticker>` es la lista del catálogo: un driver que no está en `datos.hechos` no se
   afirma como hecho. Nunca inventes que el dólar, una tasa o cualquier otro activo "sube" o "baja": el
   `sentido` y el `efecto` ya vienen calculados, úsalos con sus palabras. Di la `fecha` de cada dato: si
   `en_curso` es falso, el dato es de ese día y no de hoy (un sábado, el último cierre es del viernes).
```

3. En «Qué va en cada campo», reemplaza el punto de `contexto.<ticker>` por:

```markdown
- `contexto.<ticker>`: de 3 a 5 frases, en este orden.
  1. Una frase por cada hecho de `datos.hechos`, con su cifra tal como viene (`nivel` o `cambio_5d`),
     su fecha y su efecto. Ejemplo: «El Dollar Index (DXY) cerró el viernes 16/10 en 101,560, 0,288
     puntos bajo su nivel de cinco sesiones antes, y eso juega a favor del alza del oro.» Si `efecto` es
     `null`, describe el dato sin atribuirle dirección sobre el activo. Si `con_la_lectura` dice que va
     en contra de nuestra lectura, dilo.
  2. Una frase que jerarquice cuál de esos drivers pesa más hoy y por qué.
  3. Una frase final que cierre con la lectura: qué se vigila y qué la invalida (están en
     `datos.activos[0].lectura`).
  El bot rechaza un `contexto` que no cite la cifra de al menos dos hechos de `datos.hechos` (o del único,
  si hay uno). Sin `%` (las tasas se escriben "2,78 por ciento") y sin repetir los niveles técnicos (los
  pone la maqueta).
- `dias_clave.<ticker>` (solo si existe): de 1 a 3 frases en modo anticipación con los días clave de la
  ventana de `datos.agenda`. Nombra cada día exactamente como viene en `dia` ("miércoles 21/10"), con la
  hora, qué se publica y qué hace con el activo según su `efecto`. Si hay una decisión de tasas, va
  primera; después los que tienen `mueve_al_activo`. Hasta 420 caracteres. El bot rechaza un
  `dias_clave` que no nombre ningún `dia` de la agenda.
```

4. En el punto de `fuentes`, reemplaza la primera línea («`fuentes`: **una lista** (puede ir vacía) de 3 a 5 voces...») por:

```markdown
- `fuentes`: **una lista** de 2 a 5 voces sobre este activo, **con al menos una de un banco** (los bancos
  de inversión o los de Chile de la lista: Goldman Sachs, JPMorgan, Morgan Stanley, Bank of America, Citi,
  UBS, Barclays, Standard Chartered, Jefferies, Deutsche Bank, HSBC, ING, Commerzbank, Banco Central de
  Chile, Cochilco, Banchile, BCI Estudios, Santander Chile, Itaú Chile). Los organismos suman, pero no
  reemplazan al banco. Búscalas en la web. Cada elemento es un objeto con estos campos de texto:
```

y reemplaza el cierre del punto («No inventes URLs ni fuentes: ... deja `fuentes` como lista vacía `[]`. No rellenes.») por:

```markdown
  No inventes URLs ni fuentes: el bot abre cada URL y descarta lo que no responde. Sin ninguna voz de
  banco válida el análisis no sale, así que busca hasta encontrarla (notas de los últimos 14 días en los
  medios de la lista). No rellenes con voces que no hablan de este activo.
```

5. En «Antes de terminar», agrega después del bloque de código:

```markdown
La validación también falla si `fuentes` no trae ninguna voz de banco: sigue buscando hasta que diga `OK`.
```

- [ ] **Step 3: Correr los tests**

Run: `uv run pytest tests/test_analista_instrucciones.py tests/test_analista_*.py -q`
Expected: todo `passed`. Verifica a mano que el archivo no tenga `—` ni `–` nuevos en texto que vaya a un cliente (las instrucciones son internas, pero sus ejemplos se copian).

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/analista.md tests/test_analista_instrucciones.py
git commit -m "docs(bot): /analista cita los hechos del día, los días clave y exige un banco

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 10: Documentación del bot

**Files:**
- Modify: `docs/bot-analistas.md`

- [ ] **Step 1: Editar**

1. En el diagrama de «Cómo funciona», reemplaza las líneas de `preparar.py` y `agy /analista` por:

```
      si no     -> preparar.py (lectura, hechos del día, agenda de 7 días + calendario PNG, curva, gráficos)
                -> agy /analista (redacta pieza.json citando los hechos y busca los bancos)
                -> fuentes.depurar + esquema.py (validan) -> sin banco: segundo intento solo de fuentes
                -> lámina PNG -> oportunidad_html.py
```

2. Reemplaza «Qué lleva el análisis» por:

```markdown
### Qué lleva el análisis

- **Técnico:** la lectura de la estrategia activa (dirección, líneas, invalidación, objetivo).
- **Lo que pasa hoy** (`hechos.py`): el estado real de los drivers medibles del activo (Dollar Index
  de MT5 `USDIDX`, tasa real, bono a 10 años y tasa de la Fed de la curva, cobre y petróleo de MT5), con
  su fecha, su cambio en 5 sesiones, su efecto sobre el activo y si acompaña nuestra lectura. Qué se mide
  y con qué signo lo dice `config/drivers.json`.
- **Días clave** (`agenda.py`): los datos de alto impacto de los 7 días de vigencia (las pestañas
  `thisWeek` y `nextWeek` de Investing.com), con la lámina del calendario. Sin datos, la ficha dice la
  ventana completa con sus fechas; con el calendario caído, se avisa al ejecutivo y el correo omite el
  bloque.
- **Voces:** 2 o 3 bancos y prensa con entidad, medio, fecha y enlace. **Sin al menos un banco vigente el
  análisis no sale.**
- **Panel de simulación** para que el ejecutivo trabaje con su cliente.

El correo que copia el ejecutivo lleva todo eso: lo que pasa hoy, los días clave con la imagen del
calendario y lo que dicen los bancos con el enlace a cada nota.
```

3. En «Fuentes de prestigio», agrega al final:

```markdown
- **Un banco o nada** (spec 2026-10-17 §5). `cuentan_como_banco` de la lista dice qué grupos cumplen
  (hoy los bancos de inversión y los de Chile; los organismos suman pero no cumplen). `--validar` falla
  sin banco, así que agy sigue buscando. Si igual no llega, el bot hace **un segundo intento solo de
  fuentes** (reabre `fuentes`, deja `fuentes_intento_1.json` con lo válido y lo descartado) y, si tampoco,
  responde que no encontró ninguna voz de banco, sin gastar cupo ni registrar el análisis.
- Cada llamada a agy deja `agy_salida_<n>.json` (código, segundos y respuesta) en la carpeta del pedido.
```

4. En «Candado por activo y timeout», reemplaza el punto del timeout por:

```markdown
- agy tiene **25 minutos** para redactar (`agy.TIMEOUT`) y **15** para el segundo intento de fuentes
  (`agy.TIMEOUT_REINTENTO`). Un encargo con búsqueda web de 3 a 5 fuentes se midió en 424 s y 652 s el
  2026-10-16; los hechos del día no suman búsquedas porque los mide Python.
```

5. En «Cuando algo falla», agrega un punto:

```markdown
- **«No encontré ninguna voz de banco…»**: dos búsquedas seguidas no trajeron un banco con nota de los
  últimos 14 días. No se gastó cupo; se puede volver a pedir. La carpeta del pedido guarda
  `fuentes_intento_1.json` y las salidas de agy para ver qué se descartó.
```

- [ ] **Step 2: Revisar y commitear**

Busca `—` y `–` en lo que agregaste y reemplázalos. Luego:

```bash
git add docs/bot-analistas.md
git commit -m "docs(bot): hechos del día, días clave y el mínimo de un banco

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 11: Corrida real y ajuste del timeout

**Files:**
- Modify (solo si la medición lo pide): `scripts/analista/agy.py`

Requiere MT5 abierto en la cuenta declarada, red y agy autenticado. No usa Telegram ni toca el registro.

- [ ] **Step 1: Correr el ciclo completo de una pieza fuera del bot**

```bash
uv run --with MetaTrader5 --extra stories python -c "
import sys, json; sys.path[:0] = ['src', 'scripts']
from datetime import datetime; from pathlib import Path; from zoneinfo import ZoneInfo
from analista import preparar as pr, agy, fuentes as fu, esquema as es
from analista.orden import Orden
d = Path('data/informes_analistas/_medicion') / datetime.now(ZoneInfo('America/Santiago')).strftime('%Y-%m-%d_%H%M') / 'oro'
h = pr.preparar(Orden('oportunidad', {'ticker': 'XAUUSD'}), d)
print('avisos:', *h.avisos, sep='\n  ')
r = agy.escribir_textos(d / 'pieza.json', 'flash')
print('agy', r.codigo, round(r.segundos), 's')
p = pr.cargar_pieza(d)
p, desc = fu.depurar_pieza(p, datetime.now(ZoneInfo('America/Santiago')).date())
print('descartes:', desc); print('bancos:', [f['entidad'] for f in fu.bancos(p['editorial']['fuentes'])])
print('errores:', es.errores(p))
print(p['editorial']['contexto']['XAUUSD']); print(p['editorial'].get('dias_clave'))
"
```

Expected: `agy ok` con sus segundos, al menos un banco, `errores: []`, y un `contexto` que nombra el DXY y la tasa real con cifra y fecha. Pega en el reporte final el `contexto` y los segundos.

- [ ] **Step 2: Decidir el timeout con esta regla**

`TIMEOUT = max(25, ceil_a_múltiplo_de_5(2 × segundos_medidos / 60 + 3))` en minutos. Si cambia, edita `agy.py` (comentario con la medición y la fecha) y corre `uv run pytest tests/test_analista_agy.py -q`.

- [ ] **Step 3: Mirar las imágenes**

Abre `calendario_xauusd.png` de la carpeta de medición con la herramienta de lectura de imágenes: tildes, `·`, "por ciento" sin desbordar, días en orden. Anota lo que haya que corregir para el director; no cambies la plantilla de Stories en esta task.

- [ ] **Step 4: Commit (solo si cambió el timeout)**

```bash
git add scripts/analista/agy.py
git commit -m "chore(bot): ajusta el timeout de agy con la corrida real del texto concreto

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

Borra `data/informes_analistas/_medicion/` al terminar (es gitignorado, pero no es una pieza real).

---

## Verificación final

- [ ] `uv run pytest tests/test_analista_*.py tests/test_calendar.py tests/test_screener_gi.py -q` en verde.
- [ ] `git log --oneline -12` muestra un commit por task, todos en `feat/oportunidad-por-activo`.
- [ ] `git status` no muestra archivos de este plan sin commitear (los de datos ajenos siguen modificados y fuera de los commits).
