# Refactor de /encuesta a Motor de Sentimiento Puro — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convertir `/encuesta` en un generador de encuestas de sentimiento puro (3 tipos: `posicion`, `tendencia`, `movimiento`), sin precios ni contenido educativo, con tipo obligatorio por invocación.

**Architecture:** Es un sistema de prompts (slash commands en Markdown) + plantillas `.txt`, no código ejecutable. La "implementación" es reescribir el prompt del comando y sus plantillas, más un guard defensivo en `/rencuesta` y actualización de docs. No hay test runner: la verificación es por inspección (grep), validación de plantillas contra los límites de WhatsApp, y dry-runs simulados ejecutando mentalmente el prompt contra los archivos de datos reales (`data/plan_hoy.json`, `data/ultimo_evento.json`).

**Tech Stack:** Slash commands de Claude Code (Markdown), plantillas `.txt` con `{{placeholders}}`, datos JSON en `data/`. Spec de referencia: `docs/design/encuesta-sentimiento-puro.design.md`. Rama: `feat/encuesta-sentimiento-puro`.

---

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `templates/encuesta_posicion.txt` | Plantilla del poll de posición | Crear |
| `templates/encuesta_tendencia.txt` | Plantilla del poll de tendencia (sin contexto/precio) | Modificar |
| `templates/encuesta_movimiento.txt` | Plantilla del poll de "activo con más movimiento" (diario/semanal) | Crear (renombrando `encuesta_semanal.txt`) |
| `.claude/commands/encuesta.md` | Prompt del comando: parseo, resolución de activos, generación, guardado | Reescribir |
| `.claude/commands/rencuesta.md` | Guard defensivo en modo sin-argumento | Modificar (PASO 1) |
| `CLAUDE.md` | Descripción de `/encuesta` en la tabla de comandos | Modificar |
| `docs/commands-reference.md` | Referencia detallada de `/encuesta` | Modificar |

`templates/encuesta_precio.txt` y `templates/encuesta_post_evento.txt` **no se tocan ni se borran** — quedan huérfanos para la futura migración educativa.

---

## Task 1: Plantillas de los 3 tipos

**Files:**
- Create: `templates/encuesta_posicion.txt`
- Modify: `templates/encuesta_tendencia.txt`
- Create (via rename): `templates/encuesta_movimiento.txt` (desde `templates/encuesta_semanal.txt`)

- [ ] **Step 1: Crear `templates/encuesta_posicion.txt`**

Contenido exacto (la línea `{{guino}}` se omite en runtime si no hay evento fresco):

```text
📊 *ENCUESTA DEL DÍA*

¿Qué estás operando hoy en *{{activo}}*?
{{guino}}

🟢 Compré
🔴 Vendí
⚪ No operé / mirando
```

- [ ] **Step 2: Reescribir `templates/encuesta_tendencia.txt`**

Quitar la línea `_Lean el análisis de arriba antes de votar_ ☝️` (referenciaba el bloque de contexto eliminado) y reemplazarla por el guiño cualitativo opcional. Contenido exacto final:

```text
📊 *ENCUESTA DEL DÍA*

¿Qué tendencia proyectan hoy para *{{activo}}*?
{{guino}}

📈 Alcista
📉 Bajista
➡️ Lateral
```

- [ ] **Step 3: Renombrar `encuesta_semanal.txt` → `encuesta_movimiento.txt` y parametrizarlo**

```bash
git mv templates/encuesta_semanal.txt templates/encuesta_movimiento.txt
```

Luego sobrescribir su contenido para soportar scope diario y semanal con placeholders. Contenido exacto:

```text
📊 *{{titulo}}*

¿Qué activo creen que tendrá más movimiento {{periodo}}?
Voten 👇

{{opciones}}
```

Convención de placeholders (la rellena el comando):
- Scope diario: `{{titulo}}` = `ENCUESTA DEL DÍA`, `{{periodo}}` = `hoy`.
- Scope `semana`: `{{titulo}}` = `ENCUESTA DE LA SEMANA`, `{{periodo}}` = `esta semana`.
- `{{opciones}}` = una opción por línea, cada una con emoji + nombre del activo (ej. `🇨🇱 USD/CLP`).

- [ ] **Step 4: Verificar plantillas (límites WhatsApp + sin precios)**

Run:
```bash
ls templates/encuesta_posicion.txt templates/encuesta_tendencia.txt templates/encuesta_movimiento.txt
grep -nE '[0-9]+[.,][0-9]' templates/encuesta_posicion.txt templates/encuesta_tendencia.txt templates/encuesta_movimiento.txt
```
Expected: las 3 plantillas existen; el grep de precios **no devuelve nada** (cero números con decimales). Confirmar visualmente que ninguna opción excede 100 caracteres.

- [ ] **Step 5: Commit**

```bash
git add templates/encuesta_posicion.txt templates/encuesta_tendencia.txt templates/encuesta_movimiento.txt templates/encuesta_semanal.txt
git commit -m "feat(encuesta): plantillas de sentimiento (posicion, tendencia, movimiento)"
```

---

## Task 2: Reescritura del comando `/encuesta`

**Files:**
- Modify: `.claude/commands/encuesta.md` (reescritura completa)

- [ ] **Step 1: Sobrescribir `.claude/commands/encuesta.md` con el contenido completo**

```markdown
Genera una encuesta de sentimiento para el grupo de WhatsApp.

## Argumentos
$ARGUMENTS — formato esperado: `[tipo] [activo? | scope?]`

Tipos disponibles (sentimiento puro — sin precios, sin contenido educativo):
- `posicion [activo?]` — qué está operando el grupo (compré / vendí / no operé)
- `tendencia [activo?]` — qué tendencia proyectan para el día (alcista / bajista / lateral)
- `movimiento [semana?]` — qué activo tendrá más movimiento (hoy, o "semana" para la encuesta dominical)

Ejemplos:
- `posicion` (un poll por cada activo del día)
- `posicion USDCLP`
- `tendencia Oro`
- `movimiento`
- `movimiento semana`

> Si NO se entrega tipo, no asumir nada: preguntar al director cuál de los 3 quiere.

---

## REGLAS DURAS (todos los tipos)

> 1. **CERO precios y cero números.** Ningún poll menciona precios, niveles, datos macro
>    numéricos ni porcentajes. Si vas a escribir un número, detente.
> 2. **CERO contenido educativo.** No explicar conceptos, no causa-efecto, no "respuesta
>    correcta". Eso vive en la futura área educativa con comandos propios.
> 3. **Una invocación = una sola pieza del tipo pedido.** Nunca arrastrar otros tipos.
> 4. La contextualización la da el mensaje previo de la mañana (`/dato_macro` + `/noticia`),
>    NO la encuesta. El poll solo hace un guiño cualitativo opcional, sin números.
> 5. Límites WhatsApp: pregunta ≤ 255 caracteres — cada opción ≤ 100 caracteres (emoji incluido) — 2 a 12 opciones.

---

## PASO 1 — Parsear argumentos

**Tipo**: uno de `posicion`, `tendencia`, `movimiento`.
- Si `$ARGUMENTS` viene **sin tipo** → preguntar al director: "¿Qué encuesta generas: posicion, tendencia o movimiento?". No continuar hasta tener tipo.

**Segundo argumento**:
- Para `posicion` / `tendencia`: es el **activo** (opcional). Normalizar a nombre legible:
  - USDCLP / USD/CLP → "USD/CLP (Dólar)"
  - XAUUSD / Oro / XAU/USD → "Oro (XAU/USD)"
  - WTI → "WTI (Petróleo)"
  - US100 → "Nasdaq 100 (US100)"
  - US500 → "S&P 500 (US500)" · US30 → "Dow Jones (US30)"
  - #AAPL / AAPL → "Apple (#AAPL)" · (resto de acciones análogo)
- Para `movimiento`: el segundo argumento solo puede ser `semana` (scope semanal). Cualquier otra cosa → scope diario.

---

## PASO 2 — Resolver los activos (desde `data/plan_hoy.json`)

Leer `data/plan_hoy.json`.

**Validar frescura**: comparar `plan_hoy.fecha` con la fecha de hoy.
- Si **no coincide** o el archivo **no existe** → avisar al director: "El plan del día (`plan_hoy.json`) está desfasado (fecha: [fecha], hoy: [hoy]). ¿Qué activos uso?" y pedir los activos manualmente. No generar polls con activos viejos.
- Si coincide → usar `activos_hoy`.

**Resolución por tipo**:
- `posicion` / `tendencia`:
  - **Con activo** → generar **un solo** poll de ese activo.
  - **Sin activo** → generar **un poll por cada** activo de `activos_hoy` (solo de ese tipo).
- `movimiento`:
  - Scope **diario** → opciones = los activos de `activos_hoy`.
    - Si `activos_hoy` tiene **menos de 2** → no se puede crear poll WhatsApp; avisar y pedir activos manualmente.
    - Si tiene **más de 12** (improbable) → tomar 12 priorizando por catalizadores del día.
  - Scope **semana** → opciones fijas: 🇨🇱 USD/CLP · 🥇 Oro · ⛽ WTI (Petróleo) · 📱 US100 (Nasdaq).

---

## PASO 3 — Contexto cualitativo opcional (sin números)

Leer `data/ultimo_evento.json`.

**Validar frescura**: usar solo si su `timestamp` es de hoy. Si está desfasado o ausente → omitir priorización y guiño (poll seco).

Si hay evento fresco:
- **Priorizar orden**: en `posicion`/`tendencia` sin activo, y en `movimiento`, poner primero el activo que coincide con `ultimo_evento.activo`.
- **Guiño**: rellenar `{{guino}}` con UNA frase fija (elegir según `ultimo_evento.tipo`):
  - `Con el dato de hoy ☝️, ¿cuál es tu jugada?`
  - `Tras la noticia de hoy ☝️, ¿qué proyectas?`

**Prohibido**: volcar `dato_real`, `dato_esperado`, precios o cualquier número al poll. Prohibido inventar frases nuevas que insinúen dirección de mercado. Si no hay evento fresco, omitir la línea `{{guino}}` por completo.

---

## PASO 4 — Generar el/los poll(s)

Usar la plantilla del tipo:
- `posicion` → `templates/encuesta_posicion.txt` (rellenar `{{activo}}`, `{{guino}}`).
- `tendencia` → `templates/encuesta_tendencia.txt` (rellenar `{{activo}}`, `{{guino}}`).
- `movimiento` → `templates/encuesta_movimiento.txt` (rellenar `{{titulo}}`, `{{periodo}}`, `{{opciones}}`).

Si se generan **varios polls** (`posicion`/`tendencia` sin activo): mostrarlos todos, separados por `━━━━━━━━━━━━━━━━━━━`.

Verificar antes de mostrar: ningún número de precio, cada opción ≤ 100 chars, pregunta ≤ 255 chars.

---

## PASO 5 — Aprobación y guardado

Presentar el/los poll(s) al director. Preguntar: "¿Apruebas? ¿Enviar al grupo WhatsApp?"

Al aprobar:
- Guardar en **un único** archivo `data/mensajes/YYYY-MM-DD_HH-MM_encuesta.txt` (si son varios polls, separados por `━━━━━━━━━━━━━━━━━━━`).
- Registrar en `data/historial_encuestas.json` **un objeto por poll** (cada activo es su propia encuesta nativa de WhatsApp), con este esquema:

```json
{
  "id": "[YYYY-MM-DD]_[tipo]_[TICKER]",
  "fecha": "[YYYY-MM-DD]",
  "tipo": "[posicion|tendencia|movimiento]",
  "activo": "[TICKER]",
  "pregunta": "[texto de la pregunta]",
  "opciones": ["...", "...", "..."],
  "contexto_ref": "[nombre del evento que contextualizó, SIN números, o null]",
  "estado": "registrada"
}
```

Para `movimiento`, usar `"activos": ["...", "..."]` en vez de `"activo"`.

> Nunca `respuesta_correcta` ni `pendiente_revelacion` en estos tipos. Estado siempre `registrada`.
- Si el MCP de WhatsApp está disponible: enviar. Si no: mostrar texto listo para copiar.

---

## REGLAS
- Tipo obligatorio: sin tipo, preguntar.
- Sin precios, sin números, sin educación. Nunca.
- `posicion`/`tendencia` sin activo recorren `activos_hoy`; con activo, uno solo.
- `movimiento` = una sola pieza.
- `plan_hoy.json` o `ultimo_evento.json` desfasados → manejar como se indica (pedir manual / poll seco).
- Hora en hora Chile si mencionas algún horario.
```

- [ ] **Step 2: Verificar que el comando no conserva tipos/lógica retirados**

Las palabras `precio`, `respuesta_correcta` y `pendiente_revelacion` SÍ aparecen
legítimamente dentro de reglas/prohibiciones — eso es correcto. Lo que se verifica acá es
que **no queden como elementos funcionales**: ni `post_evento` como tipo, ni handoff a
`/rencuesta`.

Run:
```bash
grep -niE 'post_evento|rencuesta' .claude/commands/encuesta.md
```
Expected: **sin coincidencias** (no queda el tipo `post_evento` ni ninguna referencia a `/rencuesta`).

Luego confirmar visualmente que la lista de tipos en PASO 1 contiene **exactamente** `posicion`, `tendencia`, `movimiento` — y que `precio` NO figura como tipo (solo dentro de la regla "CERO precios").

- [ ] **Step 3: Dry-run simulado — `posicion` sin activo con plan_hoy desfasado**

`data/plan_hoy.json` hoy tiene `fecha: 2026-05-29` (desfasado vs hoy). Ejecutar mentalmente el PASO 2:
Expected: el comando detecta el desfase y **pide activos manualmente** en vez de usar activos viejos. Confirmar que el prompt instruye exactamente eso.

- [ ] **Step 4: Dry-run simulado — `movimiento semana`**

Ejecutar mentalmente: scope `semana` → opciones fijas de 4 principales, `{{titulo}}` = ENCUESTA DE LA SEMANA, `{{periodo}}` = esta semana. Expected: poll válido, sin números, 4 opciones.

- [ ] **Step 5: Commit**

```bash
git add .claude/commands/encuesta.md
git commit -m "feat(encuesta): reescribe el comando a 3 tipos de sentimiento sin precios ni educacion"
```

---

## Task 3: Guard defensivo en `/rencuesta`

**Files:**
- Modify: `.claude/commands/rencuesta.md` (bloque "Si `$ARGUMENTS` está vacío", líneas ~18-22)

- [ ] **Step 1: Editar el bloque de modo sin-argumento**

Reemplazar el bloque actual:

```markdown
**Si `$ARGUMENTS` está vacío**:
1. Leer `data/historial_encuestas.json`, tomar la encuesta con `fecha` más reciente.
2. Identificar el/los concepto(s) que trató (de `pregunta`/`opciones`/`trigger`). Normalizar a `id` kebab-case (ej. "stop loss" → `stop-loss`).
3. Si trató varios conceptos, listarlos al director y pedir que elija el central.
```

por:

```markdown
**Si `$ARGUMENTS` está vacío**:
1. Leer `data/historial_encuestas.json`. **Ignorar los tipos de sentimiento**
   (`posicion`, `tendencia`, `movimiento`, estado `registrada`): no tienen concepto
   educativo que desarrollar. Considerar solo encuestas educativas (las que tienen
   `respuesta_correcta` o trigger educativo, ej. `post_evento`/`educativa`).
2. Tomar la encuesta **educativa** con `fecha` más reciente.
3. Si no hay ninguna encuesta educativa → avisar: "No hay tema educativo pendiente. Usa
   `/rencuesta [tema]` para desarrollar un concepto puntual." y detener.
4. Identificar el/los concepto(s) que trató (de `pregunta`/`opciones`/`trigger`). Normalizar a `id` kebab-case (ej. "stop loss" → `stop-loss`).
5. Si trató varios conceptos, listarlos al director y pedir que elija el central.
```

- [ ] **Step 2: Verificar el guard**

Run:
```bash
grep -nE 'Ignorar los tipos de sentimiento|No hay tema educativo pendiente' .claude/commands/rencuesta.md
```
Expected: ambas frases presentes (guard instalado).

- [ ] **Step 3: Dry-run simulado contra el historial actual**

`data/historial_encuestas.json` tiene hoy una entrada `educativa` (`2026-06-02_educativa_USDCLP_stoploss`) y una `post_evento`. Ejecutar mentalmente `/rencuesta` sin argumento tras agregar una entrada `posicion` más nueva:
Expected: el guard **salta** la entrada `posicion` y toma la `educativa`/`post_evento` más reciente; no falla por falta de `respuesta_correcta`.

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/rencuesta.md
git commit -m "fix(rencuesta): ignora encuestas de sentimiento en el modo sin-argumento"
```

---

## Task 4: Actualizar documentación (`CLAUDE.md` + `commands-reference.md`)

**Files:**
- Modify: `CLAUDE.md` (fila de `/encuesta` en la tabla de Slash Commands, sección Capa 2)
- Modify: `docs/commands-reference.md` (sección `### /encuesta [tipo] [activo]`, líneas ~102-107)

- [ ] **Step 1: Actualizar la fila de `/encuesta` en `CLAUDE.md`**

Buscar la fila actual:

```markdown
| `/encuesta [tipo] [activo]` | Encuesta de tendencia o precio para cualquier activo |
```

Reemplazar por:

```markdown
| `/encuesta [tipo] [activo]` | Encuesta de sentimiento puro (sin precios ni educación). 3 tipos: `posicion`, `tendencia`, `movimiento`. Lo educativo migró fuera de `/encuesta`. |
```

- [ ] **Step 2: Actualizar la referencia detallada en `docs/commands-reference.md`**

Reemplazar el bloque (líneas ~102-107):

```markdown
### `/encuesta [tipo] [activo]`
Genera una encuesta de tendencia o precio para el activo especificado. Siempre incluye un bloque de contexto previo para que el cliente vote con información, no en intuición.
```

por:

```markdown
### `/encuesta [tipo] [activo]`
Genera una encuesta de **sentimiento puro** para el grupo. Sin precios, sin números y sin contenido educativo. Tres tipos:
- `posicion [activo?]` — qué está operando el grupo (🟢 Compré / 🔴 Vendí / ⚪ No operé). Sin activo, un poll por cada activo del día.
- `tendencia [activo?]` — qué tendencia proyectan (📈 Alcista / 📉 Bajista / ➡️ Lateral).
- `movimiento [semana?]` — qué activo tendrá más movimiento (hoy, o `semana` para la dominical).

El tipo es obligatorio (sin tipo, el comando pregunta). Los activos salen de `data/plan_hoy.json`. La contextualización la da el mensaje previo de la mañana, no la encuesta. Lo educativo (revelado, lección) vive en `/rencuesta` y futuros comandos.

**Ejemplo**: `/encuesta posicion USDCLP`
```

- [ ] **Step 3: Verificar que la doc no promete precios/educación en `/encuesta`**

Run:
```bash
grep -nE 'tendencia o precio|bloque de contexto previo' CLAUDE.md docs/commands-reference.md
```
Expected: sin coincidencias (la descripción vieja fue reemplazada).

- [ ] **Step 4: Commit**

```bash
git add CLAUDE.md docs/commands-reference.md
git commit -m "docs(encuesta): actualiza descripcion a 3 tipos de sentimiento sin precios"
```

---

## Task 5: Verificación de aceptación end-to-end

**Files:** (ninguno — solo verificación contra §13 del spec)

- [ ] **Step 1: Checklist de criterios de aceptación del spec**

Recorrer `docs/design/encuesta-sentimiento-puro.design.md` §13 y confirmar uno por uno:
- [ ] `posicion`/`tendencia`/`movimiento` generan solo su pieza (Task 2, PASO 1/4).
- [ ] Ningún poll contiene precios ni números (Task 1 Step 4 + Task 2 Step 2 + plantillas).
- [ ] `posicion`/`tendencia` sin activo recorren activos del día; con activo, uno solo (Task 2 PASO 2).
- [ ] `/encuesta` sin tipo pregunta cuál usar (Task 2 PASO 1).
- [ ] `plan_hoy.json` desfasado → aviso + pedido manual (Task 2 PASO 2).
- [ ] Tipos `precio` y `post_evento` ya no existen en `/encuesta` (Task 2 Step 2 grep).
- [ ] `historial_encuestas.json` registra los nuevos tipos con estado `registrada`, sin `respuesta_correcta` (Task 2 PASO 5).
- [ ] `/rencuesta` no se rompe en modo sin-argumento (Task 3).

- [ ] **Step 2: Grep global anti-regresión**

Run:
```bash
grep -rniE 'encuesta.*(de )?precio|post_evento' .claude/commands/encuesta.md templates/encuesta_posicion.txt templates/encuesta_tendencia.txt templates/encuesta_movimiento.txt
```
Expected: sin coincidencias en los archivos nuevos/reescritos.

- [ ] **Step 3: Abrir PR**

```bash
git push -u origin feat/encuesta-sentimiento-puro
gh pr create --base master --title "feat(encuesta): motor de sentimiento puro (3 tipos, sin precios ni educacion)" --body "Implementa el spec docs/design/encuesta-sentimiento-puro.design.md. Cierra #21."
```

---

## Notas de scope (fuera de este plan)
- Construcción de la futura **área educativa** (revelado, seguimiento de resultados, malla alimentada por eventos).
- Migración formal de los tipos retirados `precio` y `post_evento`.
- `templates/encuesta_precio.txt` y `templates/encuesta_post_evento.txt` quedan huérfanos a propósito.
