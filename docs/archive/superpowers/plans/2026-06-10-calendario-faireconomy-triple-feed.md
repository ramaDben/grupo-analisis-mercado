# Calendario macro — Triple feed Fair Economy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reemplazar el pipeline MT5 (CalendarExporter.mq5 + leer_calendario_json) por tres feeds JSON públicos de Fair Economy que cubren los 4 activos del catálogo sin dependencia del terminal.

**Architecture:** `obtener_calendario_macro()` hace fetch a `ff_calendar_thisweek.json` (ForexFactory), `mm_calendar_thisweek.json` (MetalsMine) y `ee_calendar_thisweek.json` (Energy EXCH) desde `nfs.faireconomy.media`. Merge y dedup por `(nombre, hora_servidor)`, convierte hora ISO 8601 → America/Santiago vía `zoneinfo`, engancha el glosario por sigla literal o alias `titulos_ff`. Falla parcial → campo `feeds_fallidos`; falla total → `{"error": "NO_CALENDAR_FEEDS"}` → fallback WebSearch.

**Tech Stack:** Python ≥3.11, `urllib.request` (stdlib), `zoneinfo` (stdlib), `json` (stdlib). Sin nuevas dependencias.

---

## File Map

| Acción | Archivo |
|---|---|
| Reescritura completa | `src/market_data_mcp/tools/calendar.py` |
| Eliminar `leer_calendario_json` | `src/market_data_mcp/mt5_client.py` |
| Actualizar `instructions` | `src/market_data_mcp/server.py` |
| Agregar `titulos_ff` | `data/glosario_siglas.json` |
| Reescritura completa | `tests/test_calendar.py` |
| Archivar | `mql5/CalendarExporter.mq5` → `mql5/archive/CalendarExporter.mq5` |
| Actualizar docs | `CLAUDE.md` |

---

### Task 1: Agregar `titulos_ff` al glosario

**Files:**
- Modify: `data/glosario_siglas.json`

Cuatro entradas cuyos títulos en ForexFactory no contienen la sigla literalmente.

- [ ] **Step 1: Editar `data/glosario_siglas.json`**

Agregar el campo `titulos_ff` a estas 4 entradas (las demás ya hacen match por sigla literal):

```json
"NFP": {
  "nombre_es": "Nóminas no agrícolas",
  "explicacion": "Cuántos empleos creó EE.UU. el mes pasado (sin contar el campo); dato clave para la Fed y el dólar.",
  "titulos_ff": ["Nonfarm Payrolls"]
},
"JOLTS": {
  "nombre_es": "Encuesta de vacantes y rotación laboral",
  "explicacion": "Mide cuántos puestos de trabajo están sin cubrir en EE.UU.; muestra si el empleo está fuerte o se enfría.",
  "titulos_ff": ["Job Openings"]
},
"Jobless Claims": {
  "nombre_es": "Peticiones de subsidio por desempleo",
  "explicacion": "Cuántas personas pidieron seguro de cesantía en EE.UU. esta semana; termómetro rápido del empleo.",
  "titulos_ff": ["Unemployment Claims", "Initial Jobless Claims"]
},
"PCE": {
  "nombre_es": "Gasto en consumo personal",
  "explicacion": "La medida de inflación que más mira la Fed para decidir las tasas de interés.",
  "titulos_ff": ["Personal Consumption Expenditures"]
}
```

- [ ] **Step 2: Verificar JSON válido**

```powershell
python -c "import json; json.load(open('data/glosario_siglas.json', encoding='utf-8')); print('OK')"
```

Esperado: `OK`

- [ ] **Step 3: Commit**

```bash
git add data/glosario_siglas.json
git commit -m "feat(glosario): agregar titulos_ff para NFP, JOLTS, Jobless Claims, PCE"
```

---

### Task 2: Archivar CalendarExporter.mq5

**Files:**
- Move: `mql5/CalendarExporter.mq5` → `mql5/archive/CalendarExporter.mq5`

- [ ] **Step 1: Crear carpeta archive y mover el archivo**

```bash
mkdir -p mql5/archive
git mv mql5/CalendarExporter.mq5 mql5/archive/CalendarExporter.mq5
```

- [ ] **Step 2: Commit**

```bash
git commit -m "chore(mql5): archivar CalendarExporter.mq5 (reemplazado por triple feed Fair Economy)"
```

---

### Task 3: Escribir los tests del nuevo calendar.py (TDD — fallarán hasta Task 4)

**Files:**
- Modify: `tests/test_calendar.py`

Reemplaza los tests actuales (basados en MT5 JSON) por los del triple feed. Correr antes de implementar para confirmar que fallan.

- [ ] **Step 1: Reemplazar `tests/test_calendar.py`**

```python
"""Tests del calendario macro vía triple feed Fair Economy (ff + mm + ee)."""
from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from market_data_mcp.tools import calendar

_SANTIAGO = ZoneInfo("America/Santiago")


# ── helpers ───────────────────────────────────────────────────────────────────

def _ev(title="CPI m/m", impact="High", dias_offset=0) -> dict:
    """Evento Fair Economy con fecha en Santiago (hoy + dias_offset) al mediodía."""
    now = datetime.now(tz=_SANTIAGO).replace(
        hour=12, minute=0, second=0, microsecond=0
    ) + timedelta(days=dias_offset)
    return {
        "title": title,
        "country": "USD",
        "date": now.isoformat(),
        "impact": impact,
        "forecast": "0.3%",
        "previous": "0.4%",
    }


_GLOSARIO_TEST = {
    "_meta": {"descripcion": "test"},
    "840030016": {"sigla": "NFP", "nombre_es": "Nóminas", "explicacion": "empleos"},
    "CPI": {"nombre_es": "IPC", "explicacion": "precios al consumidor"},
    "NFP": {
        "nombre_es": "Nóminas no agrícolas",
        "explicacion": "empleos nuevos",
        "titulos_ff": ["Nonfarm Payrolls"],
    },
}


# ── unit: _iso_to_santiago ────────────────────────────────────────────────────

def test_iso_to_santiago_convierte_utc_correctamente():
    # 2026-06-10T18:30:00+00:00 UTC = 14:30 Santiago (UTC-4, invierno junio)
    result = calendar._iso_to_santiago("2026-06-10T18:30:00+00:00")
    assert result == "2026-06-10 14:30"


def test_iso_to_santiago_preserva_hora_ya_en_santiago():
    # Fecha ya con offset -04:00 (Santiago invierno)
    result = calendar._iso_to_santiago("2026-06-10T14:30:00-04:00")
    assert result == "2026-06-10 14:30"


# ── unit: _enganchar_glosario ─────────────────────────────────────────────────

def test_enganchar_por_sigla_literal():
    entry = calendar._enganchar_glosario("Core CPI m/m", _GLOSARIO_TEST)
    assert entry is not None
    assert entry["nombre_es"] == "IPC"


def test_enganchar_por_titulos_ff():
    entry = calendar._enganchar_glosario("Nonfarm Payrolls", _GLOSARIO_TEST)
    assert entry is not None
    assert entry["nombre_es"] == "Nóminas no agrícolas"


def test_enganchar_sin_match_retorna_none():
    entry = calendar._enganchar_glosario("Baker Hughes Oil Rig Count", _GLOSARIO_TEST)
    assert entry is None


def test_enganchar_ignora_meta_y_event_id_numericos():
    # _meta y "840030016" no deben producir match
    entry = calendar._enganchar_glosario("840030016 meta descripcion", _GLOSARIO_TEST)
    assert entry is None


# ── unit: _fetch_feed ─────────────────────────────────────────────────────────

def test_fetch_feed_retorna_lista_vacia_en_error(monkeypatch):
    import urllib.request as urllib_req

    def _raise(*args, **kwargs):
        raise Exception("connection refused")

    monkeypatch.setattr(urllib_req, "urlopen", _raise)
    assert calendar._fetch_feed("ff") == []


# ── integration: obtener_calendario_macro ─────────────────────────────────────

def test_camino_feliz_merge_tres_feeds(collector, monkeypatch):
    feeds = {
        "ff": [_ev("CPI m/m", "High")],
        "mm": [_ev("LME Copper Inventories", "Medium")],
        "ee": [_ev("Crude Oil Inventories", "High")],
    }
    monkeypatch.setattr(calendar, "_fetch_feed", lambda slug: feeds.get(slug, []))
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: _GLOSARIO_TEST)

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="medium")

    assert "error" not in res, res
    assert res["source"] == "faireconomy"
    nombres = [e["nombre"] for e in res["eventos"]]
    assert "CPI m/m" in nombres
    assert "LME Copper Inventories" in nombres
    assert "Crude Oil Inventories" in nombres


def test_deduplicacion_evento_en_dos_feeds(collector, monkeypatch):
    ev_opec = _ev("OPEC Meetings", "Medium")
    feeds = {
        "ff": [ev_opec],
        "mm": [],
        "ee": [ev_opec],  # mismo evento en ff y ee
    }
    monkeypatch.setattr(calendar, "_fetch_feed", lambda slug: feeds.get(slug, []))
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: {})

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="low")

    assert "error" not in res
    assert sum(1 for e in res["eventos"] if e["nombre"] == "OPEC Meetings") == 1


def test_schema_normalizado_campos_correctos(collector, monkeypatch):
    monkeypatch.setattr(calendar, "_fetch_feed",
                        lambda slug: [_ev("CPI m/m", "High")] if slug == "ff" else [])
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: _GLOSARIO_TEST)

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="medium")

    ev = res["eventos"][0]
    assert "nombre" in ev
    assert "divisa" in ev
    assert "impacto" in ev
    assert "hora_servidor" in ev
    assert "forecast" in ev
    assert "previo" in ev
    assert "fuente" in ev
    assert ev["impacto"] == "alto"  # High → alto
    assert ev["fuente"] == "ff"


def test_glosario_enganchado_por_sigla(collector, monkeypatch):
    monkeypatch.setattr(calendar, "_fetch_feed",
                        lambda slug: [_ev("CPI m/m", "High")] if slug == "ff" else [])
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: _GLOSARIO_TEST)

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="medium")

    ev = res["eventos"][0]
    assert "diccionario" in ev
    assert ev["diccionario"]["nombre_es"] == "IPC"


def test_glosario_pendiente_si_no_hay_match(collector, monkeypatch):
    monkeypatch.setattr(calendar, "_fetch_feed",
                        lambda slug: [_ev("Baker Hughes Oil Rig Count", "Medium")] if slug == "ee" else [])
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: _GLOSARIO_TEST)

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="low")

    ev = res["eventos"][0]
    assert ev.get("glosario_pendiente") is True
    assert "diccionario" not in ev


def test_filtro_min_impact_excluye_bajo(collector, monkeypatch):
    feeds = {
        "ff": [_ev("CPI m/m", "High"), _ev("Minor Release", "Low")],
        "mm": [], "ee": [],
    }
    monkeypatch.setattr(calendar, "_fetch_feed", lambda slug: feeds.get(slug, []))
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: {})

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="medium")

    assert all(e["impacto"] in ("medio", "alto") for e in res["eventos"])
    assert not any(e["nombre"] == "Minor Release" for e in res["eventos"])


def test_solo_hoy_filtra_otros_dias(collector, monkeypatch):
    feeds = {
        "ff": [_ev("CPI m/m", "High", dias_offset=0),
               _ev("PPI m/m", "High", dias_offset=2)],  # pasado mañana
        "mm": [], "ee": [],
    }
    monkeypatch.setattr(calendar, "_fetch_feed", lambda slug: feeds.get(slug, []))
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: {})

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](solo_hoy=True, min_impact="medium")

    nombres = [e["nombre"] for e in res["eventos"]]
    assert "CPI m/m" in nombres
    assert "PPI m/m" not in nombres


def test_falla_parcial_incluye_feeds_fallidos(collector, monkeypatch):
    feeds = {"ff": [_ev("CPI m/m", "High")], "mm": [], "ee": []}
    monkeypatch.setattr(calendar, "_fetch_feed", lambda slug: feeds.get(slug, []))
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: {})

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="medium")

    assert "error" not in res
    assert "feeds_fallidos" in res
    assert set(res["feeds_fallidos"]) == {"mm", "ee"}


def test_falla_total_retorna_no_calendar_feeds(collector, monkeypatch):
    monkeypatch.setattr(calendar, "_fetch_feed", lambda slug: [])

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"]()

    assert res["error"] == "NO_CALENDAR_FEEDS"
    assert isinstance(res["message"], str) and res["message"]


def test_sin_eventos_es_caso_legitimo(collector, monkeypatch):
    # Feeds responden pero todos son de bajo impacto → filtro deja vacío
    feeds = {"ff": [_ev("Minor Data", "Low")], "mm": [], "ee": []}
    monkeypatch.setattr(calendar, "_fetch_feed", lambda slug: feeds.get(slug, []))
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: {})

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="medium")

    assert "error" not in res
    assert res["eventos"] == []
    assert "info" in res


def test_min_impact_invalido_retorna_error(collector, monkeypatch):
    monkeypatch.setattr(calendar, "_fetch_feed", lambda slug: [])

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="extremo")

    assert res["error"] == "INVALID_IMPACT"
    assert isinstance(res["message"], str) and res["message"]
```

- [ ] **Step 2: Correr tests para confirmar que fallan**

```bash
python -m pytest tests/test_calendar.py -v 2>&1 | head -40
```

Esperado: errores de importación o assertion (`AttributeError: module has no attribute '_fetch_feed'`) — confirma que los tests apuntan a la nueva implementación que aún no existe.

- [ ] **Step 3: Commit**

```bash
git add tests/test_calendar.py
git commit -m "test(calendar): tests triple feed Fair Economy (TDD — fallan hasta implementar)"
```

---

### Task 4: Implementar el nuevo `calendar.py`

**Files:**
- Modify: `src/market_data_mcp/tools/calendar.py`

- [ ] **Step 1: Reemplazar `src/market_data_mcp/tools/calendar.py`**

```python
"""Tool obtener_calendario_macro — calendario vía triple feed Fair Economy.

ForexFactory (ff) + MetalsMine (mm) + Energy EXCH (ee) desde nfs.faireconomy.media.
Reemplaza el pipeline MT5 (CalendarExporter.mq5 + leer_calendario_json).
MT5 queda exclusivamente para precios y niveles técnicos (get_asset_levels).
"""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastmcp import FastMCP

_CDN = "https://nfs.faireconomy.media"
_FEEDS = ("ff", "mm", "ee")
_SANTIAGO = ZoneInfo("America/Santiago")

_IMPACTO_EN_ES: dict[str, str] = {
    "High": "alto",
    "Medium": "medio",
    "Low": "bajo",
    "Holiday": "festivo",
}
_IMPACTO_RANK_EN: dict[str, int] = {"low": 0, "medium": 1, "high": 2}
_IMPACTO_RANK_ES: dict[str, int] = {"bajo": 0, "medio": 1, "alto": 2, "festivo": -1}

_GLOSARIO_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent / "data" / "glosario_siglas.json"
)


def _cargar_glosario() -> dict[str, Any]:
    if not _GLOSARIO_PATH.exists():
        return {}
    return json.loads(_GLOSARIO_PATH.read_text(encoding="utf-8"))


def _fetch_feed(slug: str) -> list[dict]:
    """GET {CDN}/{slug}_calendar_thisweek.json. Retorna [] ante cualquier falla."""
    url = f"{_CDN}/{slug}_calendar_thisweek.json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []


def _iso_to_santiago(date_str: str) -> str:
    """Convierte fecha ISO 8601 con offset a America/Santiago, formato 'YYYY-MM-DD HH:MM'."""
    dt = datetime.fromisoformat(date_str)
    return dt.astimezone(_SANTIAGO).strftime("%Y-%m-%d %H:%M")


def _normalizar_evento(ev: dict, slug: str) -> dict:
    """Mapea campos Fair Economy al schema canónico del proyecto."""
    return {
        "nombre": ev["title"],
        "divisa": ev.get("country", ""),
        "impacto": _IMPACTO_EN_ES.get(ev.get("impact", ""), "bajo"),
        "hora_servidor": _iso_to_santiago(ev["date"]),
        "forecast": ev.get("forecast", ""),
        "previo": ev.get("previous", ""),
        "fuente": slug,
    }


def _enganchar_glosario(nombre: str, glosario: dict) -> dict | None:
    """Busca entrada del glosario para un nombre de evento Fair Economy.

    Paso 1: sigla como palabra en el título (case-insensitive).
    Paso 2: alias en titulos_ff.
    Retorna None si no hay match.
    """
    nombre_upper = nombre.upper()
    for key, entry in glosario.items():
        if key.startswith("_") or key.isdigit():
            continue
        if key.upper() in nombre_upper:
            return entry
        for alias in entry.get("titulos_ff", []):
            if alias.upper() in nombre_upper:
                return entry
    return None


def _merge_feeds() -> tuple[list[dict], list[str]]:
    """Fetch ff+mm+ee, normaliza y deduplica por (nombre, hora_servidor)."""
    todos: list[dict] = []
    fallidos: list[str] = []
    seen: set[tuple[str, str]] = set()

    for slug in _FEEDS:
        raw = _fetch_feed(slug)
        if not raw:
            fallidos.append(slug)
            continue
        for ev in raw:
            try:
                norm = _normalizar_evento(ev, slug)
            except (KeyError, ValueError):
                continue
            key = (norm["nombre"], norm["hora_servidor"])
            if key not in seen:
                seen.add(key)
                todos.append(norm)

    return todos, fallidos


def register(mcp: FastMCP) -> None:

    @mcp.tool
    def obtener_calendario_macro(
        solo_hoy: bool = True,
        min_impact: str = "medium",
    ) -> dict[str, Any]:
        """Calendario macro vía triple feed Fair Economy (ForexFactory + MetalsMine + Energy EXCH).

        Cubre los 4 activos del catálogo: USD/CLP · XAU/USD · US100 (ff),
        COPPER (mm), WTI/energía (ee). Hora en America/Santiago.
        Si los 3 feeds fallan, retorna error NO_CALENDAR_FEEDS → el comando
        debe caer a WebSearch investing.com como fallback.

        Args:
            solo_hoy: si True, solo eventos cuya fecha == hoy en Santiago (default True).
            min_impact: umbral mínimo — 'low' | 'medium' | 'high' (default 'medium').

        Returns:
            {"eventos": [...], "source": "faireconomy", ...}
            o {"error": CÓDIGO, "message": "..."} si todos los feeds fallan.
        """
        if min_impact not in _IMPACTO_RANK_EN:
            return {
                "error": "INVALID_IMPACT",
                "message": (
                    f"min_impact '{min_impact}' inválido. "
                    f"Opciones: {list(_IMPACTO_RANK_EN)}"
                ),
            }

        todos, fallidos = _merge_feeds()

        if len(fallidos) == len(_FEEDS):
            return {
                "error": "NO_CALENDAR_FEEDS",
                "message": (
                    "Los 3 feeds de Fair Economy fallaron (ff, mm, ee). "
                    "Usar WebSearch investing.com como fallback."
                ),
            }

        umbral = _IMPACTO_RANK_EN[min_impact]
        hoy = datetime.now(tz=_SANTIAGO).date()
        glosario = _cargar_glosario()

        eventos: list[dict[str, Any]] = []
        for ev in todos:
            if _IMPACTO_RANK_ES.get(ev.get("impacto", "bajo"), 0) < umbral:
                continue
            if solo_hoy:
                try:
                    fecha_ev = datetime.strptime(
                        ev["hora_servidor"], "%Y-%m-%d %H:%M"
                    ).date()
                except (KeyError, ValueError):
                    continue
                if fecha_ev != hoy:
                    continue
            ev = dict(ev)
            entrada = _enganchar_glosario(ev["nombre"], glosario)
            if entrada:
                ev["diccionario"] = entrada
            else:
                ev["glosario_pendiente"] = True
            eventos.append(ev)

        resultado: dict[str, Any] = {"source": "faireconomy"}
        if fallidos:
            resultado["feeds_fallidos"] = fallidos

        if not eventos:
            resultado["eventos"] = []
            resultado["info"] = "sin eventos de impacto medio/alto hoy"
            return resultado

        resultado["eventos"] = eventos
        return resultado
```

- [ ] **Step 2: Correr los tests**

```bash
python -m pytest tests/test_calendar.py -v
```

Esperado: todos los tests pasan (`PASSED`).

- [ ] **Step 3: Correr el suite completo para detectar regresiones**

```bash
python -m pytest -v
```

Esperado: todos los tests pasan (incluyendo `test_levels.py` y `test_server.py`).

- [ ] **Step 4: Commit**

```bash
git add src/market_data_mcp/tools/calendar.py
git commit -m "feat(calendar): triple feed Fair Economy (ff+mm+ee) reemplaza pipeline MT5"
```

---

### Task 5: Eliminar `leer_calendario_json` de `mt5_client.py`

**Files:**
- Modify: `src/market_data_mcp/mt5_client.py`

- [ ] **Step 1: Eliminar el método `leer_calendario_json` y sus imports asociados**

En `src/market_data_mcp/mt5_client.py`, borrar desde la línea de `def leer_calendario_json` hasta el final del archivo (la función es la última del módulo). También borrar `import json` si queda sin usos — verificar primero.

El archivo debe quedar terminando en `bollinger()`. Eliminar además el import de `json` y `Path` en la cabecera si no los usa ninguna otra función:

Verificar usos de `json` y `Path` en el archivo (solo los usa `leer_calendario_json`), luego eliminar esas líneas del bloque de imports:

```python
# Eliminar estas dos líneas del bloque de imports:
import json
from pathlib import Path
```

Y eliminar la función completa `leer_calendario_json` (líneas 148–173 en la versión actual).

- [ ] **Step 2: Correr el suite completo**

```bash
python -m pytest -v
```

Esperado: todos los tests pasan. (`test_calendar.py` ya no referencia `leer_calendario_json`.)

- [ ] **Step 3: Verificar que ruff no reporta errores**

```bash
python -m ruff check src/
```

Esperado: sin output (sin errores).

- [ ] **Step 4: Commit**

```bash
git add src/market_data_mcp/mt5_client.py
git commit -m "chore(mt5_client): eliminar leer_calendario_json (reemplazado por fair economy)"
```

---

### Task 6: Actualizar `instructions` del servidor MCP

**Files:**
- Modify: `src/market_data_mcp/server.py`

- [ ] **Step 1: Actualizar el campo `instructions` en `server.py`**

Reemplazar el valor del argumento `instructions` en la llamada a `FastMCP(...)`:

```python
mcp = FastMCP(
    name="market-data",
    instructions=(
        "Capa de datos confiable para Grupo de Análisis de Mercado. "
        "Tools: get_asset_levels (técnico MT5), obtener_calendario_macro (calendario "
        "macro vía triple feed Fair Economy — ForexFactory + MetalsMine + Energy EXCH; "
        "WebSearch investing.com es fallback si los 3 feeds fallan). "
        "Hora en America/Santiago. Noticias vía WebSearch. "
        "Contrato de error: si el dato no está disponible retorna {'error': 'CÓDIGO', 'message': '...'} "
        "— nunca array vacío, nunca None silencioso."
    ),
    version="1.0.0",
    lifespan=lifespan,
    mask_error_details=False,
)
```

- [ ] **Step 2: Correr el suite completo**

```bash
python -m pytest -v
```

Esperado: todos los tests pasan.

- [ ] **Step 3: Commit**

```bash
git add src/market_data_mcp/server.py
git commit -m "chore(server): actualizar instructions MCP — calendario ahora es Fair Economy"
```

---

### Task 7: Actualizar `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Actualizar la tabla de MCP Servers en `CLAUDE.md`**

Localizar la sección `## MCP Servers integrados` y actualizar la fila de `market-data`:

```markdown
| **market-data** | ✅ Activo | Análisis técnico MT5 (`get_asset_levels`) + calendario macro triple feed Fair Economy (`obtener_calendario_macro`): ForexFactory (ff) + MetalsMine (mm) + Energy EXCH (ee). WebSearch investing.com es fallback si los 3 feeds fallan. | Comandos de niveles técnicos y calendario |
```

- [ ] **Step 2: Actualizar la nota sobre `obtener_calendario_macro` en la sección de MCP**

Localizar el texto que dice:
```
la antigua `get_economic_events` fue reemplazada por la tool nativa (#53)
```
y actualizar para reflejar el nuevo origen:
```
`obtener_calendario_macro` usa triple feed Fair Economy (ff+mm+ee); el pipeline MT5 (`CalendarExporter.mq5`) fue retirado.
```

- [ ] **Step 3: Actualizar la regla canónica de hora en `CLAUDE.md`**

En la sección `## Fecha y hora actual — regla canónica`, el párrafo sobre `obtener_calendario_macro` ya no aplica la regla de hora del servidor MT5. Actualizar la nota al pie:

Cambiar:
```
**Calendario macro nativo MT5 (fuente primaria)**: la hora del evento ya viene en el reloj del servidor MT5 (broker actual = hora Chile) — se muestra **tal cual, sin conversión**.
```

Por:
```
**Calendario macro Fair Economy (fuente primaria)**: la hora del evento viene en ISO 8601 con offset y se convierte automáticamente a `America/Santiago` dentro de `obtener_calendario_macro`. El resultado ya está en hora Chile — no se necesita conversión adicional.
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(claude.md): actualizar fuente calendario — Fair Economy reemplaza MT5 nativo"
```

---

### Task 8: Verificación final

- [ ] **Step 1: Correr suite completo con coverage**

```bash
python -m pytest -v --tb=short
```

Esperado: todos los tests pasan, sin warnings relevantes.

- [ ] **Step 2: Verificar linters**

```bash
python -m ruff check src/ tests/
```

Esperado: sin output.

- [ ] **Step 3: Confirmar que el glosario sigue siendo JSON válido**

```bash
python -c "import json; data = json.load(open('data/glosario_siglas.json', encoding='utf-8')); print(f'Entradas: {len(data)}')"
```

Esperado: `Entradas: N` (sin error).

- [ ] **Step 4: Confirmar estructura del repo**

```bash
git log --oneline -8
```

Esperado: 7 commits de este plan visibles en el historial.
