# Mantenimiento del Workflow /carrusel y Corrección de Formatos e Integridad MT5

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reparar el workflow `/carrusel`, eliminar la generación de imágenes verticales degradadas para `alerta` (estandarizando a horizontal 16:9), sincronizar los precios entre el escáner y las velas MT5, blindar la conexión IPC en `analizar_activo` y dejar en verde la suite de pruebas del repositorio.

**Architecture:**
1. Ajustar `pipeline_carrusel.py` para que `rendir()` genere únicamente piezas horizontales 16:9 conforme a la especificación canónica del Brandkit (commit `de4174a` y `alerta.html`), y sincronizar `precio_actual` con `recorrido.serie[-1]`.
2. Actualizar `.claude/commands/carrusel.md` y sincronizar workflows de Antigravity.
3. Eliminar la regla `.velo` duplicada en `templates/stories/alerta.html` para cumplir con `test_piel_compartida.py`.
4. Blindar `analizar_activo()` en `src/market_data_mcp/analisis.py` llamando preventivamente a `mt5_client.connect()`.
5. Corregir `macro_bias_engine.py` / `test_ecosistema_macro.py` para la frase del forward del BCCh.
6. Verificar toda la suite con pytest y ejecutar `/carrusel`.

**Tech Stack:** Python 3.12, MetaTrader 5, Playwright, pytest.

---

### Task 1: Blindar conexión MT5 en `src/market_data_mcp/analisis.py`

**Files:**
- Modify: `src/market_data_mcp/analisis.py`
- Test: `tests/test_levels.py`

- [ ] **Step 1: Modificar `src/market_data_mcp/analisis.py`**
Asegurar que `mt5_client.connect()` se llame antes de `get_rates()`.
- [ ] **Step 2: Ejecutar tests de levels**
Run: `uv run pytest tests/test_levels.py -v`
Expected: PASS

---

### Task 2: Eliminar regla duplicada `.velo` en `templates/stories/alerta.html`

**Files:**
- Modify: `templates/stories/alerta.html`
- Test: `tests/test_piel_compartida.py`

- [ ] **Step 1: Eliminar declaración redundante `.velo {` en el CSS propio de `alerta.html`**
- [ ] **Step 2: Ejecutar test de piel compartida**
Run: `uv run pytest tests/test_piel_compartida.py -v`
Expected: PASS

---

### Task 3: Corregir `scripts/pipeline_carrusel.py` y sus tests

**Files:**
- Modify: `scripts/pipeline_carrusel.py`
- Modify: `tests/test_pipeline_carrusel.py`

- [ ] **Step 1: Modificar `pipeline_carrusel.py`**
- Cambiar el bucle de renderizado para generar únicamente `formato = "horizontal"`.
- Sincronizar el marcador `AHORA` con `cierres[-1]` si difiere del precio spot del escáner para coherencia absoluta.
- [ ] **Step 2: Actualizar `tests/test_pipeline_carrusel.py`**
- Validar que `rendir()` devuelve solo imágenes horizontales (1 imagen por payload).
- [ ] **Step 3: Ejecutar suite de pipeline carrusel**
Run: `uv run pytest tests/test_pipeline_carrusel.py -v`
Expected: PASS (18 passed)

---

### Task 4: Corregir desfase en `test_ecosistema_macro.py` / `macro_bias_engine.py`

**Files:**
- Modify: `scripts/macro_bias_engine.py`
- Test: `tests/test_ecosistema_macro.py`

- [ ] **Step 1: Ajustar la frase del forward en `macro_bias_engine.py`**
- [ ] **Step 2: Ejecutar test**
Run: `uv run pytest tests/test_ecosistema_macro.py -v`
Expected: PASS

---

### Task 5: Actualizar comando `.claude/commands/carrusel.md` y regenerar workflows AGY

**Files:**
- Modify: `.claude/commands/carrusel.md`
- Run: `scripts/agy_workflows.py`

- [ ] **Step 1: Actualizar `.claude/commands/carrusel.md`**
- [ ] **Step 2: Regenerar y verificar workflows**
Run: `uv run python scripts/agy_workflows.py --check`
Expected: PASS

---

### Task 6: Verificación Integral del Workflow `/carrusel`

- [ ] **Step 1: Ejecutar suite de tests completa (excluyendo genesis)**
Run: `uv run pytest --ignore=tests/genesis_bridge`
Expected: 391 passed, 0 failed.
- [ ] **Step 2: Ejecutar pipeline carrusel completo**
Run: `uv run --with MetaTrader5 python scripts/pipeline_carrusel.py --preparar`
- [ ] **Step 3: Escribir titulares editoriales y rendir**
Run: `uv run --extra stories python scripts/pipeline_carrusel.py --rendir <dir>`
Expected: 3 imágenes horizontales nítidas generadas sin errores.
