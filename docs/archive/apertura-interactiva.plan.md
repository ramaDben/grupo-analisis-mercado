# Apertura de Mercado interactiva (/apertura) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir la "Apertura de mercado" de los comandos de día en un flujo interactivo (`/apertura`) que siempre pregunta activo, temporalidad e indicador, eliminando el `timeframe: H4` y la etiqueta `swing corto` hardcodeados.

**Architecture:** Nuevo comando reusable `.claude/commands/apertura.md` (estilo `/chart`) que centraliza la selección interactiva y el render. Los comandos de día (`martes`, `miercoles`, `jueves`, `viernes_am`, bloque de apertura de `lunes`) reemplazan su PIEZA de apertura por una **delegación** a `/apertura`. El template `apertura_mercado.txt` pasa a usar placeholders neutrales.

**Tech Stack:** Archivos markdown de slash commands de Claude Code + template de texto WhatsApp. Fuente de datos técnicos: `mcp__market-data__get_asset_levels` (devuelve `price, s1, s2, r1, r2, rsi_14, atr_14, trend`). Sin framework de tests automatizados: la verificación es por `Grep`/lectura del contenido generado y smoke manual.

**Referencia de diseño:** `docs/design/apertura-interactiva.design.md` · Issue [#12](https://github.com/bbenja11/grupo-analisis-mercado/issues/12)

---

### Task 1: Crear el comando reusable `/apertura`

**Files:**
- Create: `.claude/commands/apertura.md`

- [ ] **Step 1: Crear el archivo con el contenido completo**

Crear `.claude/commands/apertura.md` con exactamente este contenido:

````markdown
Genera la Apertura de Mercado de forma interactiva: pregunta activo, temporalidad e indicador por activo. Sin enfoque de señal.

## SETUP
1. Lee `config/agenda_semanal.json` y `config/activos.json`.
2. Los datos técnicos se obtienen vía `mcp__market-data__get_asset_levels`.

---

## PASO 1 — Activos del día (rotación + override)

Determina los activos rotados de hoy según `config/agenda_semanal.json` (2-3 activos; los viernes 3). Propón al director:

```
Activos sugeridos para hoy: [ACTIVO A] · [ACTIVO B] (· [ACTIVO C])
¿Confirmas, cambias o agregas alguno?
```

El director puede confirmar, reemplazar o agregar. Normaliza cada activo a su `ticker_mt5` consultando `config/activos.json`. Si un activo no está en el catálogo, muestra la lista de activos válidos y vuelve a preguntar.

---

## PASO 2 — Temporalidad por activo

Para CADA activo seleccionado, pregunta:

```
¿Qué temporalidad para [ACTIVO]?
1. 15M — scalper / muy rápida
2. 1H  — intradía corto
3. 4H  — intradía / swing corto
4. 1D  — lectura general
```

Mapeo a timeframe MT5: 15M→`M15`, 1H→`H1`, 4H→`H4`, 1D→`D1`.

---

## PASO 3 — Indicador por activo

Para CADA activo, pregunta:

```
¿Qué indicador en la lectura de [ACTIVO]?
1. RSI    — sobrecompra/sobreventa
2. ATR    — volatilidad (útil en USD/CLP)
3. Limpio — solo niveles, sin indicador
— Próximamente (requiere ampliar el MCP): MACD · SMA 50+200 · Bollinger
```

Si el director elige una opción "Próximamente" (MACD/SMA/Bollinger), responde:
`Ese indicador aún no está en el MCP. Por ahora elige RSI, ATR o Limpio.` y vuelve a preguntar. No falles.

---

## PASO 4 — Datos técnicos por activo

Para cada activo, llama `mcp__market-data__get_asset_levels` con `{"ticker": "[TICKER_MT5]", "timeframe": "[M15|H1|H4|D1]"}` (el timeframe mapeado en el PASO 2).

- Extrae: `price, s1, s2, r1, r2, rsi_14, atr_14, trend`.
- Si el resultado contiene `"error"`: muestra `⚠️ [message] — Verificar que MT5 esté abierto.` y **omite ese activo** (continúa con el resto; NO abortes toda la apertura).

---

## PASO 5 — Render del mensaje (por activo)

Genera un mensaje por activo. La etiqueta de marco temporal es **neutral** (lectura educativa, no operativa recomendada):

| Temporalidad | Línea `{{lectura_temporalidad}}` |
|---|---|
| 15M | `_Lectura en 15M — marco scalper (movimientos rápidos del día)_` |
| 1H  | `_Lectura en 1H — marco intradía corto_` |
| 4H  | `_Lectura en 4H — marco intradía / swing corto_` |
| 1D  | `_Lectura en 1D — lectura general del activo_` |

Línea de indicador `{{lectura_indicador}}` (omitir si "Limpio"):
- RSI → `📐 RSI [TF]: [rsi_14] — [sobrecompra >70 / sobreventa <30 / neutro]`
- ATR → `📐 ATR [TF]: [atr_14] — volatilidad de referencia del marco`

Plantilla del mensaje:

```
🎯 Activo: [NOMBRE ACTIVO]
📌 Nivel a vigilar: [R1 o S1 según sesgo]
⚡ Qué esperar: [1 línea de acción concreta]
━━━━━━━━━━━━━━━━━━━

📊 *APERTURA DE MERCADO — [FECHA]*
━━━━━━━━━━━━━━━━━━━
📈 *[NOMBRE ACTIVO]* — Niveles en [TEMPORALIDAD]
{{lectura_temporalidad}}

💰 Precio actual: [precio]
• Resistencia 1: [R1]
• Soporte 1: [S1]
• Zona de interés: [S1] – [R1]
{{lectura_indicador}}

🔎 ¿Qué lo mueve hoy?
[Drivers del activo en 2-3 líneas simples, consulta config/drivers.json]

━━━━━━━━━━━━━━━━━━━
🟢 *Alcista* — Precio sobre [R1] → tendencia compradora (intra-day)
🟡 *Esperar* — Entre [S1] y [R1] → sin confirmación de dirección
🔴 *Bajista* — Precio bajo [S1] → tendencia vendedora (intra-day)
━━━━━━━━━━━━━━━━━━━
{{lectura_temporalidad}}
```

**Decimales**: respeta el campo `digits` de `config/activos.json` por activo (regla MT5 de CLAUDE.md). Nunca truncar ceros.

**→ Por cada activo: ¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo?**
Al aprobar: guarda en `data/mensajes/YYYY-MM-DD_HH-MM_niveles.txt` (usar Write) y muestra el texto listo para copiar. Si WhatsApp MCP no disponible: solo texto + ruta de imagen.

---

## REGLAS GENERALES
- Lenguaje cliente: simple, que se entienda en 30 segundos.
- Hora siempre en hora Chile (CLT/CLST).
- Un indicador por aviso (nunca mezclar en el mismo mensaje).
- **NO es una señal**: nunca uses "operativa recomendada", "entrada", "TP/SL" en la apertura. La etiqueta temporal es marco de lectura educativo.
- **Dirección explícita** en escenarios: usa `*Alcista* 🟢` / `*Bajista* 🔴`, nunca "fuerza compradora" ni "presión vendedora".
- Si WhatsApp MCP no disponible: mostrar texto listo para copiar.
````

- [ ] **Step 2: Verificar que el archivo existe y no contiene rastros de señal hardcodeada**

Run (Grep): buscar `Operativa intradía / swing corto` en `.claude/commands/apertura.md`
Expected: **0 coincidencias** (la etiqueta es dinámica, no fija).

Run (Grep): buscar `Próximamente` en `.claude/commands/apertura.md`
Expected: ≥1 coincidencia (selector preparado para MACD/SMA/Bollinger).

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/apertura.md
git commit -m "feat: comando reusable /apertura interactivo (activo+temporalidad+indicador)"
```

---

### Task 2: Actualizar el template `apertura_mercado.txt`

**Files:**
- Modify: `templates/apertura_mercado.txt`

- [ ] **Step 1: Reemplazar la línea de operativa fija por placeholders neutrales**

En `templates/apertura_mercado.txt`, dentro del bloque `{{seccion_niveles}}`, asegúrate de que la línea de marco temporal use `{{lectura_temporalidad}}` y agrega la línea opcional `{{lectura_indicador}}` justo después de la zona de interés. El bloque debe quedar:

```
{{seccion_niveles}}
{{lectura_temporalidad}}
{{lectura_indicador}}
Sesgo: {{sesgo_emoji}} {{sesgo}}
```

NO debe quedar ninguna línea con el texto literal `Operativa intradía / swing corto`.

- [ ] **Step 2: Verificar**

Run (Grep): buscar `swing corto` en `templates/apertura_mercado.txt`
Expected: **0 coincidencias**.

Run (Grep): buscar `lectura_temporalidad` en `templates/apertura_mercado.txt`
Expected: ≥1 coincidencia.

- [ ] **Step 3: Commit**

```bash
git add templates/apertura_mercado.txt
git commit -m "feat: template apertura con placeholders de lectura temporal/indicador neutrales"
```

---

### Task 3: Delegar la PIEZA 1 de `martes.md` en `/apertura`

**Files:**
- Modify: `.claude/commands/martes.md` (líneas 9-46, bloque `## PIEZA 1 — Apertura de mercado`)

- [ ] **Step 1: Reemplazar todo el bloque de la PIEZA 1**

Reemplaza desde `## PIEZA 1 — Apertura de mercado` hasta justo antes de `## PIEZA 2 — Dato macro del día` por:

```markdown
## PIEZA 1 — Apertura de mercado

Ejecuta la lógica de `/apertura` (ver `.claude/commands/apertura.md`):
- Activos sugeridos hoy según `config/agenda_semanal.json` (2 activos el martes). El director confirma/cambia/agrega (rotación + override).
- Por CADA activo: pregunta temporalidad (PASO 2) e indicador RSI/ATR/Limpio (PASO 3), llama `get_asset_levels` con el timeframe mapeado (PASO 4) y renderiza el mensaje con la etiqueta de marco temporal neutral (PASO 5).
- Si `get_asset_levels` devuelve `"error"`: muestra `⚠️ [message] — Verificar que MT5 esté abierto.` y omite ese activo (no abortes la apertura).

**→ Por cada activo: ¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo?**
```

- [ ] **Step 2: Verificar que ya no hay hardcode de H4/swing en la PIEZA 1**

Run (Grep): buscar `"timeframe": "H4"` en `.claude/commands/martes.md`
Expected: **0 coincidencias**.

Run (Grep): buscar `swing corto` en `.claude/commands/martes.md`
Expected: **0 coincidencias**.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/martes.md
git commit -m "refactor: martes PIEZA 1 delega en /apertura"
```

---

### Task 4: Delegar la PIEZA 1 de `miercoles.md` en `/apertura`

**Files:**
- Modify: `.claude/commands/miercoles.md` (bloque `## PIEZA 1 — Apertura de mercado`)

- [ ] **Step 1: Reemplazar el bloque de la PIEZA 1**

Reemplaza el bloque `## PIEZA 1 — Apertura de mercado` (hasta antes de la `## PIEZA 2`) por el mismo bloque de delegación de la Task 3, ajustando solo la cantidad de activos:

```markdown
## PIEZA 1 — Apertura de mercado

Ejecuta la lógica de `/apertura` (ver `.claude/commands/apertura.md`):
- Activos sugeridos hoy según `config/agenda_semanal.json` (2 activos el miércoles). El director confirma/cambia/agrega (rotación + override).
- Por CADA activo: pregunta temporalidad (PASO 2) e indicador RSI/ATR/Limpio (PASO 3), llama `get_asset_levels` con el timeframe mapeado (PASO 4) y renderiza el mensaje con la etiqueta de marco temporal neutral (PASO 5).
- Si `get_asset_levels` devuelve `"error"`: muestra `⚠️ [message] — Verificar que MT5 esté abierto.` y omite ese activo (no abortes la apertura).

**→ Por cada activo: ¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo?**
```

- [ ] **Step 2: Verificar**

Run (Grep): buscar `"timeframe": "H4"` y `swing corto` en `.claude/commands/miercoles.md`
Expected: **0 coincidencias** de cada uno.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/miercoles.md
git commit -m "refactor: miercoles PIEZA 1 delega en /apertura"
```

---

### Task 5: Delegar la PIEZA 1 de `jueves.md` en `/apertura`

**Files:**
- Modify: `.claude/commands/jueves.md` (bloque `## PIEZA 1 — Apertura de mercado`)

- [ ] **Step 1: Reemplazar el bloque de la PIEZA 1**

Reemplaza el bloque `## PIEZA 1 — Apertura de mercado` (hasta antes de la `## PIEZA 2`) por:

```markdown
## PIEZA 1 — Apertura de mercado

Ejecuta la lógica de `/apertura` (ver `.claude/commands/apertura.md`):
- Activos sugeridos hoy según `config/agenda_semanal.json` (2 activos el jueves). El director confirma/cambia/agrega (rotación + override).
- Por CADA activo: pregunta temporalidad (PASO 2) e indicador RSI/ATR/Limpio (PASO 3), llama `get_asset_levels` con el timeframe mapeado (PASO 4) y renderiza el mensaje con la etiqueta de marco temporal neutral (PASO 5).
- Si `get_asset_levels` devuelve `"error"`: muestra `⚠️ [message] — Verificar que MT5 esté abierto.` y omite ese activo (no abortes la apertura).

**→ Por cada activo: ¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo?**
```

- [ ] **Step 2: Verificar**

Run (Grep): buscar `"timeframe": "H4"` y `swing corto` en `.claude/commands/jueves.md`
Expected: **0 coincidencias** de cada uno.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/jueves.md
git commit -m "refactor: jueves PIEZA 1 delega en /apertura"
```

---

### Task 6: Delegar la PIEZA 1 de `viernes_am.md` en `/apertura` (3 activos)

**Files:**
- Modify: `.claude/commands/viernes_am.md` (bloque `## PIEZA 1 — Apertura de mercado (3 activos el viernes)`)

- [ ] **Step 1: Reemplazar el bloque de la PIEZA 1**

Reemplaza el bloque `## PIEZA 1 — Apertura de mercado (3 activos el viernes)` (hasta antes de `## PIEZA 2`) por:

```markdown
## PIEZA 1 — Apertura de mercado (3 activos el viernes)

Ejecuta la lógica de `/apertura` (ver `.claude/commands/apertura.md`):
- Activos sugeridos hoy según `config/agenda_semanal.json` (**3 activos** el viernes). El director confirma/cambia/agrega (rotación + override).
- Por CADA activo: pregunta temporalidad (PASO 2) e indicador RSI/ATR/Limpio (PASO 3), llama `get_asset_levels` con el timeframe mapeado (PASO 4) y renderiza el mensaje con la etiqueta de marco temporal neutral (PASO 5).
- Si `get_asset_levels` devuelve `"error"`: muestra `⚠️ [message] — Verificar que MT5 esté abierto.` y omite ese activo (no abortes la apertura).

**→ Por cada activo: ¿Apruebas? ¿Adjuntar chart? ¿Enviar al grupo?**
```

- [ ] **Step 2: Verificar**

Run (Grep): buscar `"timeframe": "H4"` y `swing corto` en `.claude/commands/viernes_am.md`
Expected: **0 coincidencias** de cada uno.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/viernes_am.md
git commit -m "refactor: viernes_am PIEZA 1 delega en /apertura (3 activos)"
```

---

### Task 7: Delegar el bloque de apertura de `lunes.md` (PIEZA 4) en `/apertura`

**Files:**
- Modify: `.claude/commands/lunes.md` (bloque `## PIEZA 4 — Apertura de mercado`, líneas ~113-149)

Nota: este bloque además usa el wording viejo `fuerza compradora / presión vendedora`; al delegar en `/apertura` queda unificado a `*Alcista*/*Bajista*` explícito.

- [ ] **Step 1: Reemplazar el bloque de la PIEZA 4**

Reemplaza el bloque `## PIEZA 4 — Apertura de mercado` (hasta antes de `## PIEZA 5`) por:

```markdown
## PIEZA 4 — Apertura de mercado

Ejecuta la lógica de `/apertura` (ver `.claude/commands/apertura.md`):
- Activos asignados hoy según el plan / `config/agenda_semanal.json`. El director confirma/cambia/agrega (rotación + override).
- Por CADA activo: pregunta temporalidad (PASO 2) e indicador RSI/ATR/Limpio (PASO 3), llama `get_asset_levels` con el timeframe mapeado (PASO 4) y renderiza el mensaje con la etiqueta de marco temporal neutral (PASO 5).
- Si `get_asset_levels` devuelve `"error"`: muestra `⚠️ [message] — Verificar que MT5 esté abierto.` y omite ese activo (no abortes la apertura).

**→ Por cada activo: ¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo?**
```

- [ ] **Step 2: Verificar**

Run (Grep): buscar `"timeframe": "H4"`, `swing corto` y `fuerza compradora` en `.claude/commands/lunes.md`
Expected: **0 coincidencias** de cada uno.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/lunes.md
git commit -m "refactor: lunes PIEZA 4 delega en /apertura (unifica direccion explicita)"
```

---

### Task 8: Documentar `/apertura` en `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md` (tabla "Capa 2 — Comandos de tarea" y sección "Estructura diaria obligatoria")

- [ ] **Step 1: Agregar `/apertura` a la tabla de slash commands**

En `CLAUDE.md`, en la tabla "Capa 2 — Comandos de tarea (ad hoc)", agrega una fila (antes de `/dato_macro`):

```markdown
| `/apertura` | Niveles técnicos interactivos: pregunta activo, temporalidad e indicador (RSI/ATR) por activo. Lo invocan los comandos de día en su PIEZA de apertura. |
```

Además, actualiza el encabezado "## Slash Commands disponibles (18)" → "(19)".

- [ ] **Step 2: Anotar la selección interactiva en "Estructura diaria obligatoria"**

En la sección "### 1. Niveles técnicos del día", añade al final una línea:

```markdown
- La temporalidad y el indicador se eligen por activo vía `/apertura` (nunca se asume 4H fijo). Los niveles se presentan como **lectura/marco temporal**, no como señal de operativa.
```

- [ ] **Step 3: Verificar**

Run (Grep): buscar `/apertura` en `CLAUDE.md`
Expected: ≥2 coincidencias.

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: documentar /apertura en CLAUDE.md (19 comandos)"
```

---

### Task 9: Verificación final (smoke + barrido global)

**Files:**
- (sin cambios — solo verificación)

- [ ] **Step 1: Barrido global de hardcode residual en comandos de día**

Run (Grep): buscar `_Operativa intradía / swing corto_` en `.claude/commands/*.md`
Expected: **0 coincidencias** (ninguna apertura de día conserva la etiqueta fija).

Run (Grep): buscar `Niveles en 4H — operativa intradía/swing corto` en `.claude/commands/*.md`
Expected: **0 coincidencias**.

- [ ] **Step 2: Smoke manual de `/apertura`**

Con MT5 abierto, invocar `/apertura`:
- Elegir 2 activos en temporalidades distintas (ej. Oro 4H, WTI 15M) e indicadores distintos (RSI y ATR).
- Confirmar que el texto generado: (a) NO contiene "señal" ni `swing corto` fijo; (b) la línea de marco temporal coincide con la temporalidad elegida por activo; (c) la lectura del indicador muestra el valor real con los decimales del activo.
- Elegir un indicador "Próximamente" (MACD) → confirmar que re-pregunta sin fallar.
- Cerrar MT5 y reintentar un activo → confirmar que muestra el aviso y omite el activo sin abortar.

- [ ] **Step 3: Smoke de integración desde un comando de día**

Invocar `/martes` → confirmar que su PIEZA 1 ahora pregunta activo/temporalidad/indicador en vez de asumir H4.

- [ ] **Step 4: Commit de cierre (si hubo ajustes del smoke)**

```bash
git add -A
git commit -m "test: verificacion manual de /apertura interactiva"
```

Si no hubo cambios, omitir este commit.
