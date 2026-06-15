# Enfoque Direccional Operativo — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorientar la línea editorial del grupo hacia un enfoque direccional operativo (tono profesional + persuasivo, sesgo claro, niveles accionables) editando `CLAUDE.md` y 4 slash commands.

**Architecture:** Son ediciones de prompts/instrucciones en Markdown. No hay código ni tests automatizados; la verificación de cada tarea es un `grep` que confirma que el texto nuevo está y los residuos viejos no. Un commit por archivo.

**Tech Stack:** Markdown (CLAUDE.md, `.claude/commands/*.md`), helper de memoria en `~/.claude/.../memory/`.

**Spec:** `docs/superpowers/specs/2026-06-15-enfoque-direccional-operativo-design.md`

---

## Notas para el ejecutor

- Las herramientas `grep` del plan usan ripgrep (`rg`). En este entorno usa la tool **Grep** o `rg` vía Bash.
- Antes de cada `Edit`, **lee** el archivo objetivo (la herramienta Edit lo exige).
- Los bloques "ANTES" deben coincidir **exactos** con el archivo (incluida indentación). Si no coinciden por drift, ajusta el `old_string` a lo que haya en disco conservando el sentido del cambio.
- Decimales, emojis y separadores `━━━` se conservan tal cual.

---

## Task 1: `CLAUDE.md` — Principio fundamental + Regla de oro

**Files:**
- Modify: `CLAUDE.md` (sección "## Principio fundamental")

- [ ] **Step 1: Reemplazar el bloque del principio fundamental**

ANTES:
```markdown
## Principio fundamental
100% orientado al CLIENTE FINAL. Si un cliente nuevo sin experiencia no entiende el mensaje en menos de 30 segundos, hay que reescribirlo más simple. El contenido nunca se redacta para traders profesionales — se redacta para clientes que están aprendiendo.

Regla de oro: si un cliente nuevo (sin experiencia) no entiende el mensaje en menos de 30 segundos, hay que reescribirlo más simple.
```

DESPUÉS:
```markdown
## Principio fundamental
Análisis técnico simple y directo, con dirección clara, que genere interés y apetito por operar — sin caer en lo coloquial ni en lo catastrófico. El mensaje lo reciben tanto traders expertos como clientes novatos: debe ser comprensible para quien recién aprende y, a la vez, accionable para quien ya opera. Se enfatiza la tendencia y se nombra hacia dónde se dirige el activo, despertando el interés del cliente por operar el mercado.

**Regla de oro**: el cliente debe entender siempre hacia dónde se dirige el activo, para saber qué operar. Un análisis que no deja clara la dirección (alcista / bajista / lateral) está incompleto.

Criterio de claridad (subordinado a la regla de oro): si un cliente nuevo sin experiencia no entiende el mensaje en menos de 30 segundos, hay que reescribirlo más simple — pero "más simple" nunca significa "sin dirección".
```

- [ ] **Step 2: Verificar**

Run (Grep): patrón `el cliente debe entender siempre hacia dónde se dirige` en `CLAUDE.md`
Expected: 1 match (el nuevo enunciado de la regla de oro).
Run (Grep): patrón `100% orientado al CLIENTE FINAL` en `CLAUDE.md`
Expected: 0 matches.

---

## Task 2: `CLAUDE.md` — Registro y tono (relajar, no borrar)

**Files:**
- Modify: `CLAUDE.md` (sección "### Registro y tono — profesional, técnico y objetivo (OBLIGATORIO)")

- [ ] **Step 1: Reemplazar el encabezado y el párrafo de apertura de la sección de tono**

ANTES:
```markdown
### Registro y tono — profesional, técnico y objetivo (OBLIGATORIO)
Los análisis transmiten seriedad y credibilidad. **Prohibido** el lenguaje extremo, emocional o demasiado coloquial (dramatizar el movimiento, atribuir "sensaciones" al mercado, vaticinar catástrofes). Se describe el mercado con terminología financiera objetiva y comprensible para el cliente.
```

DESPUÉS:
```markdown
### Registro y tono — profesional, técnico y con gancho operativo (OBLIGATORIO)
Los análisis transmiten seriedad y credibilidad y, a la vez, generan interés y apetito por operar. **Se permite y se busca** enfatizar la tendencia, tomar postura direccional clara y redactar con tono persuasivo que invite a operar. Lo que sigue **prohibido** es el lenguaje extremo, catastrófico o demasiado coloquial (dramatizar el movimiento, atribuir "sensaciones" al mercado, vaticinar catástrofes, jerga de barrio). En una frase: **énfasis direccional sí, dramatización no**. Se describe el mercado con terminología financiera objetiva, comprensible para el cliente y con gancho.
```

- [ ] **Step 2: Reemplazar las reglas (bullets) bajo la tabla evitar/usar**

ANTES:
```markdown
Reglas:
- Describir, no dramatizar: hablar de **sesgo, presión, volatilidad, debilidad/fortaleza, corrección**, no de emociones ni de finales catastróficos.
- Objetividad: los escenarios son condicionales (`🟢 sobre X → …`, `🔴 bajo Y → …`), nunca certezas ("se va a derrumbar").
- Esto **no** habilita jerga sin explicar: si aparece un término técnico o una sigla, sigue siendo obligatorio explicarlo en voz novata (ver [estilo mensajes WhatsApp] y "Datos macro en español + Diccionario rápido"). Profesional ≠ inaccesible.
```

DESPUÉS:
```markdown
Reglas:
- Enfatizar con dirección, sin dramatizar: hablar con fuerza de **sesgo, tendencia, momentum, presión, volatilidad, debilidad/fortaleza, corrección** y nombrar hacia dónde se dirige el activo, pero sin emociones atribuidas al mercado ni finales catastróficos.
- Tomar postura: cada análisis nombra el escenario más probable (sesgo). Los escenarios siguen siendo condicionales (`🟢 sobre X → …`, `🔴 bajo Y → …`), nunca certezas absolutas ("se va a derrumbar"), pero sí señalan claramente la dirección de mayor probabilidad.
- Profesional con gancho **≠** neutral sin dirección: un mensaje "objetivo" que no toma postura direccional está incompleto (ver Regla de oro del Principio fundamental).
- Esto **no** habilita jerga sin explicar: si aparece un término técnico o una sigla, sigue siendo obligatorio explicarlo en voz novata (ver [estilo mensajes WhatsApp] y "Datos macro en español + Diccionario rápido"). Profesional ≠ inaccesible.
```

- [ ] **Step 3: Verificar**

Run (Grep): patrón `énfasis direccional sí, dramatización no` en `CLAUDE.md`
Expected: 1 match.
Run (Grep): patrón `profesional, técnico y objetivo` en `CLAUDE.md`
Expected: 0 matches.
La tabla "❌ Evitar / ✅ Usar" se **conserva intacta** (no editarla).

---

## Task 3: `CLAUDE.md` — Activos cubiertos (rotación de acciones)

**Files:**
- Modify: `CLAUDE.md` (sección "## Activos cubiertos (rotación diaria, 2-3 por día)")

- [ ] **Step 1: Añadir bullet de acciones tras el bullet de US100**

ANTES:
```markdown
- **US100 (Nasdaq 100)**: drivers → tasas Fed, earnings tech, rendimientos Treasury
```

DESPUÉS:
```markdown
- **US100 (Nasdaq 100)**: drivers → tasas Fed, earnings tech, rendimientos Treasury
- **Acciones (rotación por análisis previo)**: además de los 4 activos base, la rotación diaria puede incluir 1-2 acciones del catálogo elegidas por análisis previo. Fuente interina: las 2 acciones destacadas por `/earnings` esa semana. Mecanismo definitivo (market screener que recorra las acciones disponibles en MT5 y elija las 2 mejores): **pendiente, issue aparte**.
```

- [ ] **Step 2: Verificar**

Run (Grep): patrón `rotación por análisis previo` en `CLAUDE.md`
Expected: 1 match.

- [ ] **Step 3: Commit (cierra los 3 cambios de CLAUDE.md)**

```bash
git add CLAUDE.md
git commit -m "docs(claude.md): enfoque direccional operativo — principio, tono y rotacion de acciones"
```

---

## Task 4: `.claude/commands/apertura.md` — Terminología Soporte/Resistencia

**Files:**
- Modify: `.claude/commands/apertura.md`

Mapeo de variables: `T1`→`R1`, `T2`→`R2`, `Su1`→`S1`, `Su2`→`S2`. Mapeo de rótulos: `Techo`→`Resistencia`, `Suelo`→`Soporte`.

- [ ] **Step 1: SETUP (línea 5) — renombrar variables**

ANTES: `Los niveles (precio, T1, T2, Su1, Su2) los ingresa el director manualmente.`
DESPUÉS: `Los niveles (precio, R1, R2, S1, S2) los ingresa el director manualmente.`

- [ ] **Step 2: PASO 4B — encabezado y bloque de ingreso**

ANTES:
```markdown
### 4B — Techos y suelos (ingreso manual del director — OBLIGATORIO)
```
DESPUÉS:
```markdown
### 4B — Soportes y resistencias (ingreso manual del director — OBLIGATORIO)
```

ANTES:
```markdown
📥 Ingresa los niveles para [NOMBRE ACTIVO] ([TEMPORALIDAD]):
  Techo 1 (T1):
  Techo 2 (T2):   ← opcional, escribe "–" para omitir
  Suelo 1 (Su1):
  Suelo 2 (Su2):  ← opcional, escribe "–" para omitir
```
DESPUÉS:
```markdown
📥 Ingresa los niveles para [NOMBRE ACTIVO] ([TEMPORALIDAD]):
  Resistencia 1 (R1):
  Resistencia 2 (R2):   ← opcional, escribe "–" para omitir
  Soporte 1 (S1):
  Soporte 2 (S2):  ← opcional, escribe "–" para omitir
```

ANTES: `- Si T2 o Su2 se dejan en blanco o contienen `"–"` / `"-"`: omitir esas líneas del mensaje final.`
DESPUÉS: `- Si R2 o S2 se dejan en blanco o contienen `"–"` / `"-"`: omitir esas líneas del mensaje final.`

- [ ] **Step 3: PASO 5 — plantilla del mensaje (bloque de niveles)**

ANTES:
```markdown
💰 Precio actual: [precio]
• Techo más próximo: [T1]
• Techo siguiente: [T2]          ← solo si el director ingresó T2; si no, omitir esta línea
• Suelo más próximo: [Su1]
• Suelo siguiente: [Su2]         ← solo si el director ingresó Su2; si no, omitir esta línea
• Zona de interés: [Su1] – [T1]
{{lectura_indicador}}
```
DESPUÉS:
```markdown
💰 Precio actual: [precio]
• Resistencia más próxima: [R1]
• Resistencia siguiente: [R2]          ← solo si el director ingresó R2; si no, omitir esta línea
• Soporte más próximo: [S1]
• Soporte siguiente: [S2]         ← solo si el director ingresó S2; si no, omitir esta línea
• Zona de interés: [S1] – [R1]
{{canal_tendencia}}
{{lectura_indicador}}
```

- [ ] **Step 4: Reglas de render (líneas ~197-198) — terminología**

ANTES:
```markdown
- **Terminología de niveles**: siempre `Techo más próximo` / `Suelo más próximo`; los segundos niveles son `Techo siguiente` / `Suelo siguiente`.
- **Orden de niveles**: primero todos los techos (más próximo → siguiente), luego todos los suelos (más próximo → siguiente), luego `Zona de interés`. La zona usa siempre los "más próximos": `[Suelo más próximo] – [Techo más próximo]`.
- **T2/Su2 opcionales**: si el director NO ingresó T2 (o Su2) en PASO 4B, se **omite por completo** esa línea (sin dejar línea en blanco).
```
DESPUÉS:
```markdown
- **Terminología de niveles**: siempre `Resistencia más próxima` / `Soporte más próximo`; los segundos niveles son `Resistencia siguiente` / `Soporte siguiente`.
- **Orden de niveles**: primero todas las resistencias (más próxima → siguiente), luego todos los soportes (más próximo → siguiente), luego `Zona de interés`. La zona usa siempre los "más próximos": `[Soporte más próximo] – [Resistencia más próxima]`.
- **R2/S2 opcionales**: si el director NO ingresó R2 (o S2) en PASO 4B, se **omite por completo** esa línea (sin dejar línea en blanco).
```

- [ ] **Step 5: Verificar terminología**

Run (Grep): patrón `Techo|Suelo|\bT1\b|\bT2\b|Su1|Su2` en `.claude/commands/apertura.md`
Expected: 0 matches **salvo** dentro de la lista PROHIBIDO (que se reescribe en Task 6). Si aparecen fuera de esa lista, corregirlos.

---

## Task 5: `.claude/commands/apertura.md` — Sesgo del equipo, señal implícita y canal

**Files:**
- Modify: `.claude/commands/apertura.md`

- [ ] **Step 1: Descripción de cabecera (línea 1)**

ANTES: `Genera la Apertura de Mercado de forma interactiva: pregunta activo, temporalidad e indicador por activo. Sin enfoque de señal.`
DESPUÉS: `Genera la Apertura de Mercado de forma interactiva: pregunta activo, temporalidad e indicador por activo. Toma postura direccional (sesgo del equipo) y presenta niveles accionables, pero NO es una señal formal (sin entrada/TP/SL).`

- [ ] **Step 2: Resumen above-the-fold de la plantilla (PASO 5)**

ANTES:
```markdown
🎯 Activo: [NOMBRE ACTIVO]
📌 Nivel a vigilar: [T1 o Su1 según sesgo]
⚡ Qué esperar: [1 línea de acción concreta]
```
DESPUÉS:
```markdown
🎯 Activo: [NOMBRE ACTIVO]
📌 Nivel a vigilar: [R1 o S1 según sesgo]
🧭 Sesgo del equipo: *[Alcista / Bajista / Lateral]*
⚡ Qué esperar: [1 línea de acción concreta y direccional]
```

- [ ] **Step 3: Definir el bloque `{{canal_tendencia}}` (insertar antes de "Plantilla del mensaje:" en PASO 5)**

Insertar tras el bloque de reglas MACD (después de la línea que termina en `*Sin señal clara* 🟡`) y antes de `Plantilla del mensaje:`:

```markdown
Línea/bloque `{{canal_tendencia}}` (OPCIONAL — solo si el activo está operando dentro de un canal claro):
- Si hay canal vigente, añadir una línea: `📈 Canal [alcista/bajista/lateral] [TF]: techo del canal [valor] · piso del canal [valor]` (formatear con `digits`).
- Si NO hay canal claro, omitir la línea por completo (no dejar línea en blanco).
- El canal refuerza la dirección: canal alcista → favorece sesgo comprador; canal bajista → favorece sesgo vendedor.
```

- [ ] **Step 4: Bloque de escenarios + sesgo del equipo en la plantilla (PASO 5)**

ANTES:
```markdown
━━━━━━━━━━━━━━━━━━━
🟢 *Alcista* — Precio sobre [T1] → tendencia compradora (intra-day)
🟡 *Esperar* — Entre [Su1] y [T1] → sin confirmación de dirección
🔴 *Bajista* — Precio bajo [Su1] → tendencia vendedora (intra-day)
━━━━━━━━━━━━━━━━━━━
{{lectura_temporalidad}}
```
DESPUÉS:
```markdown
━━━━━━━━━━━━━━━━━━━
🟢 *Alcista* — Precio sobre [R1] → se activa sesgo comprador (intra-day)
🟡 *Esperar* — Entre [S1] y [R1] → sin confirmación de dirección
🔴 *Bajista* — Precio bajo [S1] → se activa sesgo vendedor (intra-day)

🧭 *Sesgo del equipo*: *[Alcista / Bajista / Lateral]* — [1 línea: por qué es el escenario de mayor probabilidad hoy]
━━━━━━━━━━━━━━━━━━━
{{lectura_temporalidad}}
```

- [ ] **Step 5: Reglas generales (líneas ~215-216) — reemplazar "NO es una señal"**

ANTES:
```markdown
- **NO es una señal**: nunca uses "operativa recomendada", "entrada", "TP/SL" en la apertura. La etiqueta temporal es marco de lectura educativo.
- **Dirección explícita** en escenarios: usa `*Alcista* 🟢` / `*Bajista* 🔴`, nunca "fuerza compradora" ni "presión vendedora".
```
DESPUÉS:
```markdown
- **Sesgo operativo implícito, NO señal formal**: la apertura SÍ toma postura direccional (línea `🧭 Sesgo del equipo`) y presenta los niveles como zonas accionables ("sobre [R1] se activa sesgo comprador"). Pero NUNCA incluye `entrada`, `TP`, `SL` ni montos en pesos (CLP) — eso es territorio exclusivo de `/señal` — y **NO cuenta para el límite de 3 señales/semana**.
- **Dirección explícita** en escenarios y en el sesgo del equipo: usa `*Alcista* 🟢` / `*Bajista* 🔴` / `*Lateral* 🟡`. Nombra siempre el escenario de mayor probabilidad como sesgo del equipo.
```

- [ ] **Step 6: PASO 5 — nota de marco temporal (línea ~126)**

ANTES: `Genera un mensaje por activo. La etiqueta de marco temporal es **neutral** (lectura educativa, no operativa recomendada):`
DESPUÉS: `Genera un mensaje por activo. La etiqueta de marco temporal indica el horizonte de la lectura; el mensaje toma postura direccional vía el `🧭 Sesgo del equipo` (sesgo de mayor probabilidad), sin llegar a ser señal formal:`

- [ ] **Step 7: Verificar**

Run (Grep): patrón `Sesgo del equipo` en `.claude/commands/apertura.md`
Expected: ≥3 matches (resumen, plantilla escenarios, reglas).
Run (Grep): patrón `NO es una señal` en `.claude/commands/apertura.md`
Expected: 0 matches.

---

## Task 6: `.claude/commands/apertura.md` — Invertir lista PROHIBIDO (#35)

**Files:**
- Modify: `.claude/commands/apertura.md` (sección "## PROHIBIDO")

- [ ] **Step 1: Reescribir las viñetas de la lista PROHIBIDO**

ANTES:
```markdown
- ❌ `Resistencia 1/2` · `Soporte 1/2` → usa `Techo/Suelo más próximo` y `siguiente`.
- ❌ `Techo objetivo` · `Techo inmediato` · `Suelo fuerte` → usa `más próximo` / `siguiente`.
- ❌ `📊 *Precio actual*` · `📌 Precio actual` como rótulo de precio → usa `💰 Precio actual`.
- ❌ `⚠️ *RSI 1H*: ...` · `• RSI: ...` inline → usa `📐 RSI/ATR/EMA/MACD/Bollinger [TF]:` (línea `{{lectura_indicador}}`).
- ❌ Día de la semana en la fecha (`martes 2 de junio`) → usa `2 de junio de 2026`.
- ❌ Línea extra `Sesgo: ...` o `🟢 *Sesgo del día*` → el sesgo va implícito en el bloque de escenarios `🟢/🟡/🔴`.
- ❌ Bloque de escenarios con orden invertido o emoji duplicado (`🟢 Sobre X → *Alcista* 🟢 → siguiente objetivo`) → orden canónico: `🟢 *Alcista* — Precio sobre X → tendencia compradora (intra-day)`.
- ❌ `🔎 *¿Qué lo está moviendo?*` (en negrita / otra redacción) → usa `🔎 ¿Qué lo mueve hoy?` sin negrita.
```
DESPUÉS:
```markdown
- ❌ `Techo 1/2` · `Suelo 1/2` · `Techo/Suelo más próximo` → usa `Resistencia/Soporte más próxima/o` y `siguiente`.
- ❌ `Resistencia objetivo` · `Resistencia inmediata` · `Soporte fuerte` → usa `más próxima/o` / `siguiente`.
- ❌ `📊 *Precio actual*` · `📌 Precio actual` como rótulo de precio → usa `💰 Precio actual`.
- ❌ `⚠️ *RSI 1H*: ...` · `• RSI: ...` inline → usa `📐 RSI/ATR/EMA/MACD/Bollinger [TF]:` (línea `{{lectura_indicador}}`).
- ❌ Día de la semana en la fecha (`martes 2 de junio`) → usa `2 de junio de 2026`.
- ❌ Omitir la línea `🧭 Sesgo del equipo` → es OBLIGATORIA: el mensaje siempre nombra el escenario de mayor probabilidad (Alcista/Bajista/Lateral).
- ❌ Incluir `entrada`, `TP`, `SL` o montos en pesos en la apertura → eso es `/señal`. La apertura solo da sesgo + niveles accionables.
- ❌ Bloque de escenarios con orden invertido o emoji duplicado (`🟢 Sobre X → *Alcista* 🟢 → siguiente objetivo`) → orden canónico: `🟢 *Alcista* — Precio sobre X → se activa sesgo comprador (intra-day)`.
- ❌ `🔎 *¿Qué lo está moviendo?*` (en negrita / otra redacción) → usa `🔎 ¿Qué lo mueve hoy?` sin negrita.
```

- [ ] **Step 2: Verificar (toda la terminología vieja erradicada)**

Run (Grep): patrón `Techo más próximo|Suelo más próximo|\[T1\]|\[T2\]|\[Su1\]|\[Su2\]` en `.claude/commands/apertura.md`
Expected: 0 matches.
Run (Grep): patrón `el sesgo va implícito` en `.claude/commands/apertura.md`
Expected: 0 matches.

- [ ] **Step 3: Commit (cierra todos los cambios de apertura.md)**

```bash
git add .claude/commands/apertura.md
git commit -m "feat(apertura): soporte/resistencia, sesgo del equipo, niveles accionables y canal de tendencia"
```

---

## Task 7: `.claude/commands/dato_macro.md` — Filtro por país + temporalidad + alto impacto

**Files:**
- Modify: `.claude/commands/dato_macro.md`

- [ ] **Step 1: Insertar PASO 1C de filtrado por país (tras el "Contrato sin-resultados" de PASO 1, antes de "## PASO 2")**

Insertar este bloque nuevo justo antes de `## PASO 2 — Presentar lista al director`:

```markdown
## PASO 1C — Filtrado por país (OBLIGATORIO, antes de presentar la lista)

Aplica estos filtros al set de eventos obtenido. El filtro aplica **tanto a la lista del PASO 2 como al desarrollo del PASO 3**:

- **Zona Euro**: conservar **solo la decisión de tasas del BCE**. Descartar el resto de datos de la Zona Euro (IPC euro, PMI euro, etc.).
- **Estados Unidos**: conservar **solo eventos de 3 estrellas (★★★, alto impacto)**. Descartar los de 2★. Cada evento de EE.UU. se enmarca en la narrativa de la **decisión de tasas de la Fed** (¿el dato empuja las tasas al alza o a la baja?) y se traduce a impacto en **índices bursátiles** (US100 / US30 suben o bajan).
- **Chile**: conservar **solo la balanza comercial**. Descartar exportaciones de cobre, producción manufacturera y ventas minoristas.
- **Otros países** (ej. China): sin cambios respecto al filtro de impacto medio/alto ya aplicado.

Si tras el filtrado no queda ningún evento → muestra "📅 Sin datos macro relevantes para hoy (según filtros de cobertura)" y DETÉN.
```

- [ ] **Step 2: Modo anticipación — añadir temporalidad del impacto**

ANTES:
```markdown
👀 Activos a observar: [lista de activos impactados]
━━━━━━━━━━━━━━━━━━━
🔤 Diccionario rápido
```
DESPUÉS:
```markdown
👀 Activos a observar: [lista de activos impactados]
⏱️ Temporalidad del impacto: [scalper (minutos a 1-2 h) / intradía (la jornada) / swing de jornada (1-3 días) / posicional (días a semanas)]
━━━━━━━━━━━━━━━━━━━
🔤 Diccionario rápido
```

- [ ] **Step 3: Modo resultado — añadir temporalidad del impacto tras el bloque de impacto por activo**

ANTES:
```markdown
📌 *Resumen simple*: [1-2 líneas de conclusión práctica que amarran el dato general + la sorpresa parcial si la hubo]
```
DESPUÉS:
```markdown
⏱️ Temporalidad del impacto: [scalper (minutos a 1-2 h) / intradía (la jornada) / swing de jornada (1-3 días) / posicional (días a semanas)]

📌 *Resumen simple*: [1-2 líneas de conclusión práctica que amarran el dato general + la sorpresa parcial si la hubo]
```

- [ ] **Step 4: Modo resultado — limitar sub-lecturas de alto impacto**

ANTES:
```markdown
[una línea por cada sub-lectura publicada del indicador (ej. IPC mensual / anual / subyacente). Si el indicador tiene una sola lectura, una única línea: actual (esperado X | anterior Y)]
```
DESPUÉS:
```markdown
[En datos de alto impacto: mostrar SOLO las sub-lecturas anual y mensual, y normal y subyacente según corresponda al indicador. NO incluir otras sub-lecturas. Si el indicador tiene una sola lectura, una única línea: actual (esperado X | anterior Y)]
```

- [ ] **Step 5: Añadir reglas al bloque REGLAS (al final del archivo)**

ANTES:
```markdown
- Cuando aplique, conectar el dato con la narrativa de tasas de interés.
```
DESPUÉS:
```markdown
- Cuando aplique, conectar el dato con la narrativa de tasas de interés.
- **Filtro de cobertura por país (PASO 1C)**: Zona Euro = solo decisión de tasas BCE; EE.UU. = solo 3★ enmarcados en la narrativa de tasas Fed e impacto en índices bursátiles (US100/US30); Chile = solo balanza comercial.
- **Temporalidad del impacto obligatoria**: todo mensaje indica si el efecto es scalper / intradía / swing de jornada / posicional (alineado con las 4 etiquetas canónicas de temporalidad de CLAUDE.md).
- **Alto impacto**: en modo resultado, las sub-lecturas se limitan a anual + mensual y normal + subyacente según corresponda; las demás no se incluyen.
```

- [ ] **Step 6: Verificar**

Run (Grep): patrón `PASO 1C — Filtrado por país` en `.claude/commands/dato_macro.md`
Expected: 1 match.
Run (Grep): patrón `Temporalidad del impacto` en `.claude/commands/dato_macro.md`
Expected: ≥3 matches (anticipación, resultado, reglas).

- [ ] **Step 7: Commit**

```bash
git add .claude/commands/dato_macro.md
git commit -m "feat(dato_macro): filtro por pais (euro/eeuu/chile), temporalidad de impacto y limite de sublecturas"
```

---

## Task 8: `.claude/commands/earnings.md` — 2 acciones más atractivas

**Files:**
- Modify: `.claude/commands/earnings.md`

- [ ] **Step 1: Añadir bloque "2 más atractivas" en la plantilla del PASO 4**

ANTES:
```markdown
━━━━━━━━━━━━━━━━━━━
⚠️ _Los earnings pueden generar movimientos bruscos. Precaución con posiciones abiertas._
```
DESPUÉS:
```markdown
━━━━━━━━━━━━━━━━━━━
⭐ *Las 2 más atractivas de la semana*
1. *#[TICKER]* — [por qué es atractiva: catalizador / foco del trimestre / peso en el índice, 1 línea direccional]
2. *#[TICKER]* — [por qué es atractiva, 1 línea direccional]
_Estas 2 son las candidatas a entrar en la rotación diaria de activos esta semana._
━━━━━━━━━━━━━━━━━━━
⚠️ _Los earnings pueden generar movimientos bruscos. Precaución con posiciones abiertas._
```

- [ ] **Step 2: Añadir regla**

ANTES:
```markdown
- Destacar las de mayor peso (Nvidia, Apple, Microsoft, JPMorgan) con ⭐.
- También usado automáticamente por /lunes (Pieza 2).
```
DESPUÉS:
```markdown
- Destacar las de mayor peso (Nvidia, Apple, Microsoft, JPMorgan) con ⭐.
- **Siempre** señalar las **2 acciones más atractivas de la semana** con un "por qué" direccional; son la fuente interina de la rotación de acciones (ver "Activos cubiertos" en CLAUDE.md). Si no reporta ninguna del catálogo, elegir las 2 con mejor setup técnico/fundamental aunque no tengan earnings esta semana.
- También usado automáticamente por /lunes (Pieza 2).
```

- [ ] **Step 3: Verificar**

Run (Grep): patrón `Las 2 más atractivas de la semana` en `.claude/commands/earnings.md`
Expected: 1 match.

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/earnings.md
git commit -m "feat(earnings): destacar las 2 acciones mas atractivas de la semana"
```

---

## Task 9: `.claude/commands/concepto.md` — Anclar en datos macro de la semana

**Files:**
- Modify: `.claude/commands/concepto.md`

- [ ] **Step 1: PASO 1 — priorizar macro**

ANTES:
```markdown
## PASO 1 — Analizar qué pasó esta semana

Recopila contexto de la semana para elegir un concepto relevante:
- Con `WebSearch` obtén un resumen de los eventos macro de esta semana (últimos ~5 días) sobre investing.com + fuentes oficiales.
- Si no hay resultados relevantes: continuar con análisis basado en config/drivers.json.
```
DESPUÉS:
```markdown
## PASO 1 — Analizar qué pasó esta semana

Recopila contexto de la semana para elegir un concepto relevante. **Por defecto, el concepto se ancla en los datos macro de la semana** (es el foco prioritario); lo técnico queda como alternativa cuando no hubo macro relevante.
- Con `WebSearch` obtén un resumen de los **datos macro** de esta semana (últimos ~5 días) sobre investing.com + fuentes oficiales: qué se publicó, qué sorprendió y cómo movió a los activos.
- Si no hubo macro relevante esta semana: recién entonces elegir un concepto técnico, con análisis basado en config/drivers.json.
```

- [ ] **Step 2: PASO 2 — reordenar sugerencias (macro primero)**

ANTES:
```markdown
Tipos disponibles: macro / técnico / conceptual
```
DESPUÉS:
```markdown
Tipos disponibles: macro / técnico / conceptual

**Orden de prioridad de las sugerencias**: presentar primero la(s) opción(es) **macro** ancladas en los datos de la semana; las técnicas van después como alternativa.
```

- [ ] **Step 3: Añadir regla**

ANTES:
```markdown
- SIEMPRE conectar con algo real de la semana — no explicar en abstracto.
- Un aviso = un concepto (nunca mezclar RSI + MACD en el mismo mensaje).
```
DESPUÉS:
```markdown
- SIEMPRE conectar con algo real de la semana — no explicar en abstracto.
- **Foco por defecto en los datos macro de la semana**; lo técnico es alternativa solo si no hubo macro relevante.
- Un aviso = un concepto (nunca mezclar RSI + MACD en el mismo mensaje).
```

- [ ] **Step 4: Verificar**

Run (Grep): patrón `el concepto se ancla en los datos macro de la semana` en `.claude/commands/concepto.md`
Expected: 1 match.

- [ ] **Step 5: Commit**

```bash
git add .claude/commands/concepto.md
git commit -m "feat(concepto): anclar el concepto de la semana en los datos macro"
```

---

## Task 10: Actualizar memoria de tono profesional

**Files:**
- Modify: `C:/Users/bbrav/.claude/projects/C--Users-bbrav-grupo-analisis-mercado/memory/feedback_registro_tono_profesional.md`

- [ ] **Step 1: Leer el archivo de memoria actual**

Read: `C:/Users/bbrav/.claude/projects/C--Users-bbrav-grupo-analisis-mercado/memory/feedback_registro_tono_profesional.md`

- [ ] **Step 2: Actualizar el cuerpo al nuevo equilibrio**

Reemplazar la regla "prohibido lenguaje emocional" por el matiz nuevo: sigue prohibido lo **extremo/catastrófico/coloquial**, pero ahora **se permite y se busca** el énfasis direccional persuasivo que invite a operar (equilibrio profesional + persuasivo). Conservar el frontmatter (`name`, `description`, `metadata`). Actualizar la `description` para reflejar el equilibrio. Mantener los enlaces `[[...]]` existentes y, si aplica, enlazar `[[project_vision_plataforma_educativa]]`.

- [ ] **Step 3: Actualizar el puntero en MEMORY.md**

Read y Edit: `C:/Users/bbrav/.claude/projects/C--Users-bbrav-grupo-analisis-mercado/memory/MEMORY.md`
Actualizar la línea de "Registro y tono profesional" para que el hook mencione el equilibrio (profesional + persuasivo / énfasis direccional permitido), sin perder el formato `- [Title](file.md) — hook`.

- [ ] **Step 4: Verificar**

Run (Grep): patrón `persuasivo|énfasis direccional` en `feedback_registro_tono_profesional.md`
Expected: ≥1 match.
(Los archivos de memoria no se commitean al repo del proyecto — viven fuera del working tree.)

---

## Self-Review (cobertura del spec)

- Spec §1 Principio + Regla de oro → Task 1 ✅
- Spec §2 Tono relajado → Task 2 ✅; memoria → Task 10 ✅
- Spec §3 Activos cubiertos / rotación acciones → Task 3 ✅
- Spec §4 apertura: soporte/resistencia → Task 4; sesgo/señal implícita/canal → Task 5; PROHIBIDO invertido → Task 6 ✅
- Spec §5 dato_macro: filtro país + temporalidad + alto impacto → Task 7 ✅
- Spec §6 earnings 2 atractivas → Task 8 ✅
- Spec §7 concepto macro → Task 9 ✅
- Fuera de alcance (market screener) → documentado como pendiente en Task 3, sin construir ✅

Sin placeholders. Variables consistentes (R1/R2/S1/S2 en todo apertura.md). Cada archivo cierra con su commit.
