# Calendario macro nativo MT5 (puente MQL5→Python) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Exponer el calendario macroeconómico nativo de MT5 como una nueva tool del MCP `market-data` (`obtener_calendario_macro`), alimentada por un Service MQL5 que escribe un JSON, con WebSearch investing.com como fallback.

**Architecture:** Un Service MQL5 (`CalendarExporter.mq5`) escribe `Common/Files/calendario_macro.json` cada 1 h. La capa Python lee ese JSON (`mt5_client.leer_calendario_json`), valida frescura, engancha explicaciones novatas por `event_id` desde `data/glosario_siglas.json`, y devuelve los eventos en hora del servidor MT5 (sin conversiones). Contrato de error explícito; nunca array vacío salvo el caso legítimo "sin eventos hoy".

**Tech Stack:** Python 3.12 + fastmcp, pytest (con stub de fastmcp y fixture `collector` en `conftest.py`), MQL5 (Service).

---

## File Structure

- **Create** `market_data_mcp/tools/calendar.py` → **reemplaza** el stub `DEPRECATED`; registra `obtener_calendario_macro` + helpers de filtrado/frescura/glosario.
- **Modify** `market_data_mcp/mt5_client.py` → añade `leer_calendario_json()` (lectura + parseo del JSON, aislada para mockear).
- **Modify** `market_data_mcp/server.py` → actualiza el campo `instructions` (ya no "3 tools deprecadas").
- **Create** `data/glosario_siglas.json` → diccionario novato keyed por `event_id` de MT5.
- **Create** `market_data_mcp/tests/test_calendar.py` → tests TDD de la tool (JSON mockeado).
- **Modify** `market_data_mcp/tests/test_deprecated_tools.py` → quita el test de `get_economic_events` (deja de existir); conserva `get_market_context`.
- **Create** `mql5/CalendarExporter.mq5` → Service exportador (verificación manual, no CI).
- **Modify** `.claude/commands/dato_macro.md` y `.claude/commands/noticia.md` → MT5 primario, WebSearch fallback.
- **Modify** `CLAUDE.md`, `docs/design/websearch-calendario-noticias.design.md` → ajustes de regla horaria y rol de fuentes.

**Supuesto clave documentado:** el MCP corre en la misma máquina que el terminal MT5; por eso `datetime.now()` (hora local) == hora del servidor MT5 (broker actual en hora Chile). No se hace ninguna conversión de zona.

---

## Task 1: `leer_calendario_json()` en mt5_client

**Files:**
- Modify: `market_data_mcp/mt5_client.py`
- Test: `market_data_mcp/tests/test_calendar.py`

- [ ] **Step 1: Escribir el test que falla**

Crear `market_data_mcp/tests/test_calendar.py` con:

```python
"""Tests del calendario macro nativo MT5: lectura JSON + tool con contrato de error."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from market_data_mcp import mt5_client


def _ts(delta_min: int = 0) -> str:
    """generated_at relativo a ahora, formato del JSON."""
    return (datetime.now() + timedelta(minutes=delta_min)).strftime("%Y-%m-%d %H:%M")


def _payload(generated_delta_min: int = -10, eventos=None) -> dict:
    return {
        "generated_at": _ts(generated_delta_min),
        "server_tz_note": "hora servidor MT5 (broker actual = hora Chile)",
        "eventos": eventos if eventos is not None else [],
    }


def test_leer_calendario_json_parsea_archivo(tmp_path: Path):
    archivo = tmp_path / "calendario_macro.json"
    archivo.write_text(json.dumps(_payload(eventos=[{"event_id": 1}])), encoding="utf-8")
    data = mt5_client.leer_calendario_json(archivo)
    assert data["eventos"][0]["event_id"] == 1
    assert "generated_at" in data


def test_leer_calendario_json_archivo_ausente_lanza(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        mt5_client.leer_calendario_json(tmp_path / "no_existe.json")
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `python -m pytest market_data_mcp/tests/test_calendar.py -v`
Expected: FAIL con `AttributeError: module 'market_data_mcp.mt5_client' has no attribute 'leer_calendario_json'`.

- [ ] **Step 3: Implementar `leer_calendario_json` en `mt5_client.py`**

Añadir al final de `market_data_mcp/mt5_client.py`:

```python
import json
from pathlib import Path


def leer_calendario_json(path: "Path | None" = None) -> dict:
    """Lee y parsea el calendario macro exportado por el Service MQL5.

    El archivo lo escribe CalendarExporter.mq5 en Common/Files de MT5. Si `path`
    es None, se resuelve desde la variable de entorno MT5_COMMON_FILES (directorio
    Common/Files del terminal) + 'calendario_macro.json'.

    Lanza FileNotFoundError si el archivo no existe y json.JSONDecodeError si el
    contenido no es JSON válido. La validación de frescura y el contrato de error
    viven en la tool (tools/calendar.py), no aquí.
    """
    if path is None:
        common = os.environ.get("MT5_COMMON_FILES", "")
        if not common:
            raise FileNotFoundError(
                "MT5_COMMON_FILES no configurado: no se puede localizar calendario_macro.json"
            )
        path = Path(common) / "calendario_macro.json"
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el calendario MT5 en {path}")
    return json.loads(path.read_text(encoding="utf-8"))
```

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `python -m pytest market_data_mcp/tests/test_calendar.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add market_data_mcp/mt5_client.py market_data_mcp/tests/test_calendar.py
git commit -m "feat(calendario): leer_calendario_json lee el JSON nativo MT5 (#53)"
```

---

## Task 2: `data/glosario_siglas.json` (semilla keyed por event_id)

**Files:**
- Create: `data/glosario_siglas.json`

- [ ] **Step 1: Crear el archivo con estructura y semilla**

Crear `data/glosario_siglas.json`:

```json
{
  "_meta": {
    "descripcion": "Diccionario rápido novato. Explica siglas de datos macro en lenguaje cliente. Issue #46.",
    "llave": "event_id de MT5 (string). Si aparece un event_id sin entrada, añadirlo aquí.",
    "voz": "cliente nuevo sin experiencia; máximo 1-2 líneas por explicación"
  },
  "840030016": {
    "sigla": "NFP",
    "nombre_es": "Nóminas no agrícolas",
    "explicacion": "Cuántos empleos nuevos creó EE.UU. el mes pasado (sin contar el campo). Si salen muchos, la economía está fuerte y el dólar suele subir."
  },
  "840030023": {
    "sigla": "IPC",
    "nombre_es": "Índice de precios al consumidor",
    "explicacion": "Mide cuánto subieron los precios. Si sube más de lo esperado, la inflación aprieta y suele empujar las tasas y al dólar al alza."
  }
}
```

> Nota: los `event_id` de la semilla son ejemplos. Al validar contra el JSON real del Service (Task 7), reemplazar por los `event_id` verdaderos que entregue MT5.

- [ ] **Step 2: Commit**

```bash
git add data/glosario_siglas.json
git commit -m "feat(glosario): glosario_siglas.json keyed por event_id (#46/#53)"
```

---

## Task 3: tool `obtener_calendario_macro` — camino feliz + frescura

**Files:**
- Create: `market_data_mcp/tools/calendar.py` (reemplaza el stub DEPRECATED)
- Test: `market_data_mcp/tests/test_calendar.py`

- [ ] **Step 1: Escribir los tests que fallan**

Añadir a `market_data_mcp/tests/test_calendar.py`:

```python
from market_data_mcp.tools import calendar


_GLOSARIO = {
    "1": {"sigla": "NFP", "nombre_es": "Nóminas no agrícolas", "explicacion": "empleos nuevos…"},
}


def _eventos_hoy():
    hoy = datetime.now().strftime("%Y-%m-%d")
    return [
        {"event_id": 1, "nombre": "Nóminas no agrícolas", "pais": "Estados Unidos",
         "divisa": "USD", "impacto": "alto", "hora_servidor": f"{hoy} 09:30",
         "periodo": "Mayo 2026", "previo": "175K", "forecast": "190K", "actual": None},
        {"event_id": 99, "nombre": "Discurso menor", "pais": "Zona Euro",
         "divisa": "EUR", "impacto": "bajo", "hora_servidor": f"{hoy} 11:00",
         "periodo": "", "previo": "", "forecast": "", "actual": None},
    ]


def test_camino_feliz_filtra_impacto_y_engancha_glosario(collector, monkeypatch):
    monkeypatch.setattr(mt5_client, "leer_calendario_json",
                        lambda path=None: _payload(eventos=_eventos_hoy()))
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: _GLOSARIO)

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="medium")

    assert "error" not in res, res
    # El evento de impacto bajo se filtró (min_impact=medium)
    assert len(res["eventos"]) == 1
    ev = res["eventos"][0]
    assert ev["event_id"] == 1
    assert ev["divisa"] == "USD"
    assert ev["periodo"] == "Mayo 2026"
    # Glosario enganchado por event_id (string)
    assert ev["diccionario"]["sigla"] == "NFP"
    assert res["source"] == "mt5_native"


def test_evento_sin_glosario_marca_pendiente(collector, monkeypatch):
    monkeypatch.setattr(mt5_client, "leer_calendario_json",
                        lambda path=None: _payload(eventos=_eventos_hoy()))
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: {})  # glosario vacío

    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"](min_impact="high")
    ev = res["eventos"][0]
    assert ev["glosario_pendiente"] is True
    assert "diccionario" not in ev


def test_calendario_viejo_retorna_stale(collector, monkeypatch):
    monkeypatch.setattr(mt5_client, "leer_calendario_json",
                        lambda path=None: _payload(generated_delta_min=-200))  # >3 h
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: {})
    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"]()
    assert res["error"] == "STALE_CALENDAR"
    assert isinstance(res["message"], str) and res["message"]
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `python -m pytest market_data_mcp/tests/test_calendar.py -v`
Expected: FAIL — `obtener_calendario_macro` no existe y `_cargar_glosario` no existe.

- [ ] **Step 3: Reemplazar `tools/calendar.py`**

Sobrescribir `market_data_mcp/tools/calendar.py` completo con:

```python
"""Tool obtener_calendario_macro — calendario nativo MT5 con contrato de error explícito.

Reemplaza a get_economic_events (deprecado). Lee el JSON que escribe el Service
MQL5 CalendarExporter, valida frescura, engancha el Diccionario rápido por
event_id y devuelve los eventos en hora del servidor MT5 (sin conversiones).
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from market_data_mcp import mt5_client

# Ranking de impacto. min_impact (inglés, compat con la firma anterior) → umbral.
_IMPACTO_RANK = {"bajo": 0, "medio": 1, "alto": 2}
_MIN_IMPACT_MAP = {"low": 0, "medium": 1, "high": 2}

# Frescura: el JSON se considera viejo si supera estas horas (issue #53).
_STALE_HORAS = 3

# data/glosario_siglas.json — tools/calendar.py → parent.parent.parent = raíz repo.
_GLOSARIO_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "glosario_siglas.json"


def _cargar_glosario() -> dict[str, Any]:
    """Lee el glosario keyed por event_id. Si no existe, retorna {} (no es error)."""
    if not _GLOSARIO_PATH.exists():
        return {}
    return json.loads(_GLOSARIO_PATH.read_text(encoding="utf-8"))


def register(mcp: FastMCP) -> None:

    @mcp.tool
    def obtener_calendario_macro(
        solo_hoy: bool = True,
        min_impact: str = "medium",
    ) -> dict[str, Any]:
        """Calendario macro nativo de MT5 (fuente primaria; WebSearch es fallback).

        Lee el JSON exportado por el Service MQL5, valida que esté fresco, filtra
        por impacto y (si solo_hoy) por la fecha de hoy, y engancha la explicación
        novata por event_id. Hora en el reloj del servidor MT5, sin conversiones.

        Args:
            solo_hoy: si True, solo eventos cuya fecha == hoy (default True).
            min_impact: umbral mínimo — 'low' | 'medium' | 'high' (default 'medium').

        Returns:
            {"eventos":[...], "generated_at":..., "source":"mt5_native", ...}
            o {"error": CÓDIGO, "message": "..."} si el calendario no está disponible.
        """
        try:
            data = mt5_client.leer_calendario_json()
        except FileNotFoundError as exc:
            return {"error": "NO_CALENDAR_FILE", "message": str(exc)}
        except (json.JSONDecodeError, ValueError) as exc:
            return {"error": "BAD_CALENDAR_JSON", "message": f"Calendario MT5 ilegible: {exc}"}

        # --- Frescura ---
        try:
            generado = datetime.strptime(data["generated_at"], "%Y-%m-%d %H:%M")
        except (KeyError, ValueError) as exc:
            return {"error": "BAD_CALENDAR_JSON", "message": f"generated_at inválido: {exc}"}
        if datetime.now() - generado > timedelta(hours=_STALE_HORAS):
            return {
                "error": "STALE_CALENDAR",
                "message": (
                    f"Calendario MT5 viejo (generado {data['generated_at']}, "
                    f"umbral {_STALE_HORAS} h). ¿Service CalendarExporter caído?"
                ),
            }

        # --- Filtrado ---
        umbral = _MIN_IMPACT_MAP.get(min_impact, 1)
        hoy = datetime.now().date()
        glosario = _cargar_glosario()

        eventos: list[dict[str, Any]] = []
        for ev in data.get("eventos", []):
            if _IMPACTO_RANK.get(ev.get("impacto", "bajo"), 0) < umbral:
                continue
            if solo_hoy:
                try:
                    fecha_ev = datetime.strptime(ev["hora_servidor"], "%Y-%m-%d %H:%M").date()
                except (KeyError, ValueError):
                    continue
                if fecha_ev != hoy:
                    continue
            ev = dict(ev)  # copia para no mutar el origen
            entrada = glosario.get(str(ev.get("event_id")))
            if entrada:
                ev["diccionario"] = entrada
            else:
                ev["glosario_pendiente"] = True
            eventos.append(ev)

        if not eventos:
            return {
                "eventos": [],
                "info": "sin eventos de impacto medio/alto hoy",
                "generated_at": data["generated_at"],
                "source": "mt5_native",
            }

        return {
            "eventos": eventos,
            "generated_at": data["generated_at"],
            "server_tz_note": data.get("server_tz_note", ""),
            "source": "mt5_native",
        }
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `python -m pytest market_data_mcp/tests/test_calendar.py -v`
Expected: PASS (todos).

- [ ] **Step 5: Commit**

```bash
git add market_data_mcp/tools/calendar.py market_data_mcp/tests/test_calendar.py
git commit -m "feat(calendario): tool obtener_calendario_macro nativa MT5 (#53)"
```

---

## Task 4: contrato de error de archivo ausente + sin eventos

**Files:**
- Test: `market_data_mcp/tests/test_calendar.py`

- [ ] **Step 1: Escribir los tests que fallan**

Añadir a `market_data_mcp/tests/test_calendar.py`:

```python
def test_archivo_ausente_retorna_no_calendar_file(collector, monkeypatch):
    def _raise(path=None):
        raise FileNotFoundError("No existe el calendario MT5 en X")
    monkeypatch.setattr(mt5_client, "leer_calendario_json", _raise)
    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"]()
    assert res["error"] == "NO_CALENDAR_FILE"
    assert isinstance(res["message"], str) and res["message"]


def test_sin_eventos_es_caso_legitimo_no_error(collector, monkeypatch):
    monkeypatch.setattr(mt5_client, "leer_calendario_json",
                        lambda path=None: _payload(eventos=[]))
    monkeypatch.setattr(calendar, "_cargar_glosario", lambda: {})
    calendar.register(collector)
    res = collector.tools["obtener_calendario_macro"]()
    assert "error" not in res
    assert res["eventos"] == []
    assert "info" in res
```

- [ ] **Step 2: Correr los tests**

Run: `python -m pytest market_data_mcp/tests/test_calendar.py -v`
Expected: PASS (la lógica ya está en Task 3; estos tests congelan el contrato).

- [ ] **Step 3: Commit**

```bash
git add market_data_mcp/tests/test_calendar.py
git commit -m "test(calendario): congela contrato NO_CALENDAR_FILE y sin-eventos (#53)"
```

---

## Task 5: registrar la tool y actualizar `instructions` del server

**Files:**
- Modify: `market_data_mcp/server.py:63-75`
- Modify: `market_data_mcp/tests/test_deprecated_tools.py`

- [ ] **Step 1: Quitar el test de deprecación de get_economic_events**

En `market_data_mcp/tests/test_deprecated_tools.py`, borrar la función `test_get_economic_events_esta_deprecado` completa (líneas 13-17) y ajustar el import a solo `context`:

```python
from market_data_mcp.tools import context


def test_get_market_context_esta_deprecado(collector):
    context.register(collector)
    res = collector.tools["get_market_context"]()
    assert res["error"] == "DEPRECATED"
    assert "WebSearch" in res["message"]
```

- [ ] **Step 2: Correr la suite — confirmar que no quedó referencia rota**

Run: `python -m pytest market_data_mcp/tests/ -v`
Expected: PASS — ya no se referencia `get_economic_events`; `calendar.register` ahora expone `obtener_calendario_macro`.

- [ ] **Step 3: Actualizar `instructions` en `server.py`**

En `market_data_mcp/server.py`, reemplazar el bloque `instructions=(...)` (líneas ~65-71) por:

```python
    instructions=(
        "Capa de datos confiable para Grupo de Análisis de Mercado. "
        "Tools: get_asset_levels (técnico MT5), obtener_calendario_macro (calendario "
        "macro nativo MT5, fuente primaria; WebSearch investing.com es fallback). "
        "Hora en reloj del servidor MT5, sin conversiones. "
        "Contrato de error: si el dato no está disponible retorna {'error': 'CÓDIGO', 'message': '...'} "
        "— nunca array vacío, nunca None silencioso."
    ),
```

- [ ] **Step 4: Correr la suite completa**

Run: `python -m pytest market_data_mcp/tests/ -v`
Expected: PASS (todos).

- [ ] **Step 5: Commit**

```bash
git add market_data_mcp/server.py market_data_mcp/tests/test_deprecated_tools.py
git commit -m "feat(calendario): registra obtener_calendario_macro y retira deprecación de events (#53)"
```

---

## Task 6: Service MQL5 `CalendarExporter.mq5`

**Files:**
- Create: `mql5/CalendarExporter.mq5`

> El Service MQL5 **no** se prueba en CI (requiere terminal MT5). Verificación manual al final.

- [ ] **Step 1: Crear el Service**

Crear `mql5/CalendarExporter.mq5`:

```mql5
//+------------------------------------------------------------------+
//| CalendarExporter.mq5                                             |
//| Service: exporta el calendario macro nativo de MT5 a un JSON    |
//| en Common/Files cada hora. Lo consume el MCP market-data.       |
//| Issue #53.                                                       |
//+------------------------------------------------------------------+
#property service
#property strict

input int RefrescoSegundos = 3600;   // refresh cada 1 h (issue #53)

//--- mapea importancia MT5 a etiqueta del proyecto
string ImpactoStr(ENUM_CALENDAR_EVENT_IMPORTANCE imp)
{
   if(imp == CALENDAR_IMPORTANCE_HIGH)     return("alto");
   if(imp == CALENDAR_IMPORTANCE_MODERATE) return("medio");
   return("bajo");
}

//--- escapa comillas/backslash para JSON
string JsonEscape(string s)
{
   StringReplace(s, "\\", "\\\\");
   StringReplace(s, "\"", "\\\"");
   return(s);
}

void ExportarCalendario()
{
   datetime ahora = TimeTradeServer();
   datetime inicio = ahora - 12*3600;   // ventana: hoy +/- margen
   datetime fin    = ahora + 36*3600;

   MqlCalendarValue values[];
   int n = CalendarValueHistory(values, inicio, fin);

   string eventos = "";
   for(int i = 0; i < n; i++)
   {
      MqlCalendarEvent ev;
      if(!CalendarEventById(values[i].event_id, ev)) continue;
      if(ev.importance == CALENDAR_IMPORTANCE_NONE) continue;  // filtra ruido

      MqlCalendarCountry pais;
      CalendarCountryById(ev.country_id, pais);

      string nombre  = JsonEscape(ev.name);          // ya localizado al idioma del terminal
      string paisStr = JsonEscape(pais.name);
      string divisa  = JsonEscape(pais.currency);
      string periodo = JsonEscape(TimeToString(values[i].period, TIME_DATE));
      string hora    = TimeToString(values[i].time, TIME_DATE|TIME_MINUTES);

      string previo   = values[i].HasPreviousValue() ? DoubleToString(values[i].GetPreviousValue(), 2) : "";
      string forecast = values[i].HasForecastValue() ? DoubleToString(values[i].GetForecastValue(), 2) : "";
      string actual   = values[i].HasActualValue()   ? DoubleToString(values[i].GetActualValue(), 2)   : "null";

      if(eventos != "") eventos += ",\n";
      eventos += StringFormat(
         "    {\"event_id\": %I64u, \"nombre\": \"%s\", \"pais\": \"%s\", \"divisa\": \"%s\", "
         "\"impacto\": \"%s\", \"hora_servidor\": \"%s\", \"periodo\": \"%s\", "
         "\"previo\": \"%s\", \"forecast\": \"%s\", \"actual\": %s}",
         ev.id, nombre, paisStr, divisa, ImpactoStr(ev.importance), hora, periodo,
         previo, forecast, (actual == "null" ? "null" : "\"" + actual + "\""));
   }

   string generado = TimeToString(ahora, TIME_DATE|TIME_MINUTES);
   string json = StringFormat(
      "{\n  \"generated_at\": \"%s\",\n"
      "  \"server_tz_note\": \"hora servidor MT5 (broker actual = hora Chile)\",\n"
      "  \"eventos\": [\n%s\n  ]\n}\n", generado, eventos);

   //--- FILE_COMMON => Common/Files, accesible por el MCP
   int h = FileOpen("calendario_macro.json", FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
   if(h != INVALID_HANDLE)
   {
      FileWriteString(h, json);
      FileClose(h);
      Print("CalendarExporter: calendario_macro.json escrito (", n, " valores).");
   }
   else
      Print("CalendarExporter: error abriendo archivo: ", GetLastError());
}

void OnStart()
{
   while(!IsStopped())
   {
      ExportarCalendario();
      Sleep(RefrescoSegundos * 1000);
   }
}
```

> Nota MQL5: `values[i].period` da el período del dato; verificar el tipo exacto en tu build (algunos exponen `period` como datetime). Ajustar `TimeToString` si el período viene como mes/año. Los nombres `ev.name` salen en el idioma del terminal (español).

- [ ] **Step 2: Commit**

```bash
git add mql5/CalendarExporter.mq5
git commit -m "feat(calendario): Service MQL5 CalendarExporter exporta JSON nativo (#53)"
```

- [ ] **Step 3: Verificación manual (documentar resultado, no en CI)**

1. Copiar `CalendarExporter.mq5` a `MQL5/Services/` del terminal, compilar en MetaEditor.
2. Arrastrar el Service y arrancarlo; confirmar en el log "calendario_macro.json escrito".
3. Localizar el archivo en `Common/Files` (menú *Abrir carpeta de datos común*) y validar que es JSON parseable con los campos `event_id, nombre, pais, divisa, impacto, hora_servidor, periodo, previo, forecast, actual`.
4. Anotar la ruta absoluta de `Common/Files` → es el valor de `MT5_COMMON_FILES` en el `.env` del MCP.

---

## Task 7: ajustar comandos `/dato_macro` y `/noticia` (MT5 primario, WebSearch fallback)

**Files:**
- Modify: `.claude/commands/dato_macro.md`
- Modify: `.claude/commands/noticia.md`

- [ ] **Step 1: Reescribir PASO 1B de `dato_macro.md`**

En `.claude/commands/dato_macro.md`, reemplazar el bloque **1B — Calendario económico** (líneas 13-31) por:

```markdown
**1B — Calendario económico (MT5 nativo primero, WebSearch fallback)**:

1. **Fuente primaria — MT5 nativo**: invoca la tool MCP `obtener_calendario_macro(min_impact="medium")`.
   - Si devuelve `{"eventos": [...]}`: usa esos eventos. La hora ya viene en **hora del servidor MT5** (broker actual = hora Chile) — **no conviertas nada**.
   - Cada evento trae `nombre` (ya en español), `pais`, `divisa`, `impacto`, `hora_servidor`, `periodo`, `previo`, `forecast`, `actual`. Si trae `diccionario`, úsalo para el bloque Diccionario rápido; si trae `glosario_pendiente: true`, explica la sigla al vuelo y añádela a `data/glosario_siglas.json` por su `event_id`.
   - Si devuelve `{"eventos": []}` con `info`: es fin de semana/feriado → muestra "📅 Sin datos macro de impacto medio/alto hoy" y DETÉN.

2. **Fallback — WebSearch**: solo si la tool devuelve `{"error": ...}` (NO_CALENDAR_FILE / STALE_CALENDAR / BAD_CALENDAR_JSON), avisa al director ("⚠️ calendario nativo MT5 no disponible, uso WebSearch") y usa el flujo WebSearch sobre investing.com:
   - Query: `investing.com calendario económico hoy [FECHA] Chile Estados Unidos "Zona Euro" China impacto alto`.
   - En este fallback (origen extranjero) sí conviertes la hora con `scripts\hora_chile.ps1` desde la zona del organismo emisor.
```

- [ ] **Step 2: Ajustar la regla de hora en `dato_macro.md`**

En `.claude/commands/dato_macro.md`, en PASO 2 y REGLAS donde dice "Hora siempre en hora Chile (CLT/CLST)", añadir la aclaración:

```markdown
- Hora: en fuente MT5 nativa, la hora es la del servidor MT5 (broker actual = hora Chile, se muestra tal cual). En fallback WebSearch, convertir a hora Chile con `scripts\hora_chile.ps1`.
```

- [ ] **Step 3: Replicar el orden de fuentes en `noticia.md`**

En `.claude/commands/noticia.md`, donde se obtiene el calendario/contexto, añadir al inicio del paso de búsqueda:

```markdown
**Fuente de calendario**: si la noticia requiere un dato del calendario, consulta primero `obtener_calendario_macro` (MT5 nativo, hora del servidor sin conversión). Solo si devuelve `{"error": ...}`, cae a WebSearch investing.com.
```

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/dato_macro.md .claude/commands/noticia.md
git commit -m "feat(calendario): /dato_macro y /noticia usan MT5 nativo primario, WebSearch fallback (#53)"
```

---

## Task 8: actualizar documentación de reglas (CLAUDE.md + design doc)

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/design/websearch-calendario-noticias.design.md`

- [ ] **Step 1: Actualizar la tabla de MCP y la nota de tools en `CLAUDE.md`**

En `CLAUDE.md`, sección "## MCP Servers integrados":
- En la fila `market-data`, cambiar el propósito a: `Análisis técnico MT5 (get_asset_levels) + calendario macro nativo MT5 (obtener_calendario_macro). Noticias siguen por WebSearch.`
- En la **Nota** que dice que `get_economic_events` y `get_market_context` están deprecadas, ajustar a: `get_market_context sigue deprecada (noticias vía WebSearch). El calendario económico pasó de WebSearch a la tool nativa obtener_calendario_macro (MT5), con WebSearch investing.com como fallback. Ver docs/superpowers/specs/2026-06-05-calendario-macro-nativo-mt5-design.md.`

- [ ] **Step 2: Ajustar la regla canónica de hora en `CLAUDE.md`**

En `CLAUDE.md`, sección "## Fecha y hora actual — regla canónica", en el bloque "Hora de los datos económicos", añadir al inicio:

```markdown
**Calendario macro nativo MT5 (fuente primaria)**: la hora del evento ya viene en el reloj del servidor MT5 (broker actual = hora Chile) — se muestra **tal cual, sin conversión**. Esto hace el sistema multi-broker/multi-país (la hora sigue al terminal). El helper `scripts\hora_chile.ps1` y la conversión por zona del organismo emisor **solo** aplican al fallback WebSearch (cuando la tool nativa devuelve `{error:...}`).
```

- [ ] **Step 3: Anotar el cambio de rol en el design doc de WebSearch**

En `docs/design/websearch-calendario-noticias.design.md`, añadir una nota al inicio:

```markdown
> **Actualización (issue #53, 2026-06-05):** para el **calendario** económico, WebSearch pasó de fuente primaria a **fallback**. La fuente primaria es ahora la tool nativa `obtener_calendario_macro` (MT5). Las **noticias** siguen 100% por WebSearch como describe este documento. Ver `docs/superpowers/specs/2026-06-05-calendario-macro-nativo-mt5-design.md`.
```

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md docs/design/websearch-calendario-noticias.design.md
git commit -m "docs(calendario): regla de hora MT5 nativa y rol de WebSearch como fallback (#53)"
```

---

## Task 9: verificación final de la suite

- [ ] **Step 1: Correr toda la suite del MCP**

Run: `python -m pytest market_data_mcp/tests/ -v`
Expected: PASS (todos: levels, calendar, deprecated/context).

- [ ] **Step 2: Confirmar import limpio del server (sin MT5 instalado)**

Run: `python -c "import market_data_mcp.tools.calendar as c; print('ok')"`
Expected: imprime `ok` sin traceback (la tool importa de forma perezosa MT5 vía mt5_client).
