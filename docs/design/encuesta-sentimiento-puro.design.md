# Diseño — Refactor de `/encuesta` a motor de sentimiento puro

> Estado: Discovery (ciclo Pulse) · Fecha: 2026-06-02 · Autor: director de trading + Claude Code

## 1. Contexto y problema

Hoy `/encuesta` mezcla cuatro tipos con propósitos distintos: `tendencia` y `precio`
(predicción de mercado, con bloque de contexto que muestra **precios**) y `post_evento`
(encuesta **educativa** con "respuesta correcta" que se revela al día siguiente vía
`/rencuesta`). Esto hace que el comando arrastre lógica educativa y de precios que ya no
queremos en la herramienta de encuestas.

La decisión del director es **separar aguas**: `/encuesta` pasa a ser un **termómetro de
sentimiento del grupo**, sin precios y sin contenido educativo. Todo lo educativo
(revelado, lección, malla de conceptos, comparación de resultados) migra a una **futura
área educativa con comandos propios** — fuera del alcance de este cambio.

## 2. Objetivo y no-objetivos

**Objetivo:** `/encuesta` genera encuestas de sentimiento puro alrededor de tres pilares,
sin mencionar precios ni explicar conceptos. Una invocación = una pieza del tipo pedido.

**No-objetivos (fuera de alcance):**
- Contenido educativo dentro de la encuesta (explicaciones, causa-efecto, "respuesta correcta").
- Cualquier número de precio dentro del poll.
- Seguimiento/cierre con resultados ("ayer el 60% compró… así les fue").
- Rework de `/rencuesta` o construcción de la nueva área educativa.
- Migración formal de los tipos retirados (`precio`, `post_evento`) — se documentan, no se reescriben aquí.

## 3. Los tres tipos finales

| Tipo | Pregunta | Opciones | Origen de activos |
|---|---|---|---|
| `posicion` | ¿Qué estás operando hoy en *[activo]*? | 🟢 Compré · 🔴 Vendí · ⚪ No operé / mirando | `data/plan_hoy.json` |
| `tendencia` | ¿Qué tendencia proyectan hoy para *[activo]*? | 📈 Alcista · 📉 Bajista · ➡️ Lateral | `data/plan_hoy.json` |
| `movimiento` | ¿Qué activo tendrá más movimiento hoy? | los activos del día como opciones | `data/plan_hoy.json` |

- Selección **única** en los tres tipos.
- Sin bloque de contexto, sin precios, sin explicación.

## 4. Modelo de invocación

El **tipo es obligatorio y explícito**. Cada llamada genera **solo esa pieza**, nunca arrastra las otras.

```
/encuesta movimiento        → solo el poll de "qué activo se moverá más hoy"
/encuesta posicion          → un poll de posición por cada activo del día
/encuesta posicion USDCLP   → solo el poll de posición de USD/CLP
/encuesta tendencia Oro     → solo el poll de tendencia del Oro
/encuesta movimiento semana → poll con los 4 principales (encuesta dominical)
```

Reglas:
- `/encuesta` **sin tipo** → no asume nada; pregunta cuál de los 3 tipos quiere el director.
- `posicion` / `tendencia` **sin activo** → recorre `activos_hoy` y genera un poll por activo, solo de ese tipo.
- `posicion` / `tendencia` **con activo** → un único poll.
- `movimiento` → siempre una sola pieza. Scope opcional `semana` = los 4 principales (USD/CLP, Oro, WTI, US100) para la encuesta dominical de la agenda.
- `movimiento` con **menos de 2 activos** en `plan_hoy.json` → no se puede crear poll WhatsApp (mínimo 2 opciones); avisar al director y pedir activos manualmente. Con **más de 12** → tomar los 12 priorizados por catalizadores del día (caso improbable: la rotación diaria es de 2–3).

## 5. Contextualización sin precios

El flujo operativo de la mañana es:

1. Mensaje de apertura: **dato macro de hoy + noticia importante** (`/dato_macro`, `/noticia`).
2. Procesada esa info → se lanza la **encuesta contextualizada**.

La contextualización la entrega el **mensaje previo**, no la encuesta. El poll solo hace un
**guiño cualitativo** al mensaje anterior, sin números:

```
📊 ¿Qué estás operando hoy en USD/CLP?
Con el dato de hoy ☝️, ¿cuál es tu jugada?

🟢 Compré
🔴 Vendí
⚪ No operé / mirando
```

Inteligencia opcional: el comando puede leer `data/ultimo_evento.json` para **priorizar el
orden** de los activos (poner primero el más afectado por el dato del día) y para el guiño
textual. **Prohibido** volcar al poll cualquier número de `ultimo_evento.json`
(`dato_real`, `dato_esperado`, precios) — solo se usa para ordenar y para la frase
cualitativa.

**Validar la frescura de `ultimo_evento.json`:** igual que `plan_hoy.json`, solo usarlo si
su `timestamp` es de hoy. Si está desfasado o ausente, **omitir** la priorización y el guiño
(generar el poll seco) — nunca contextualizar con un evento de otro día.

**Guiño cualitativo acotado (anti-alucinación):** el guiño NO interpreta ni predice el
impacto del mercado. Se limita a una frase fija de las permitidas, sin análisis:
- `Con el dato de hoy ☝️, ¿cuál es tu jugada?`
- `Tras la noticia de hoy ☝️, ¿qué proyectas?`
- Si no hay evento fresco: omitir el guiño (poll seco).

El implementador NO debe redactar frases nuevas que insinúen dirección de mercado.

> Regla de oro de `CLAUDE.md` (el cliente vota informado): se cumple por el **mensaje
> previo** de la mañana, no por la encuesta. Documentarlo para no contradecir `CLAUDE.md`.

## 6. Fuente de activos y manejo de `plan_hoy.json` desfasado

Los activos salen de `data/plan_hoy.json → activos_hoy`, ligándolos a la rotación del día.

**Edge case crítico:** `plan_hoy.json` puede estar desactualizado (ej. su campo `fecha` no
coincide con hoy). El comando **debe validar** que `plan_hoy.fecha == fecha de hoy` antes de
usar `activos_hoy`:
- Si coincide → usa `activos_hoy`.
- Si NO coincide (o falta el archivo) → avisa al director que el plan del día está desfasado
  y pide los activos manualmente, en vez de generar polls con activos viejos.

## 7. Esquema en `data/historial_encuestas.json`

Los tipos nuevos se guardan **sin** `respuesta_correcta` ni `pendiente_revelacion`. Estado
simple `registrada`:

```json
{
  "id": "2026-06-02_posicion_USDCLP",
  "fecha": "2026-06-02",
  "tipo": "posicion",
  "activo": "USDCLP",
  "pregunta": "¿Qué estás operando hoy en USD/CLP?",
  "opciones": ["🟢 Compré", "🔴 Vendí", "⚪ No operé / mirando"],
  "contexto_ref": "JOLTS abril 2026",
  "estado": "registrada"
}
```

- `movimiento` guarda `"activos": [...]` en lugar de `"activo"`.
- `contexto_ref` es **textual, sin números** (nombre del evento que contextualizó).
- Las entradas históricas `post_evento` / `educativa` ya guardadas **se dejan intactas**
  (registro pasado, no se migran ni se borran).

## 8. Templates afectados

- **Nuevo:** `templates/encuesta_posicion.txt`.
- **Ajustar:** `templates/encuesta_tendencia.txt` → quitar el bloque de contexto con precio.
- **Renombrar/ajustar:** `templates/encuesta_semanal.txt` → sirve a `movimiento` (versión
  diaria desde `plan_hoy.json` + scope `semana`).
- **Retirar del flujo** (no se borran; quedan para migración educativa):
  `templates/encuesta_precio.txt`, `templates/encuesta_post_evento.txt`.

## 9. Reescritura del flujo del comando (`.claude/commands/encuesta.md`)

```
PASO 1 — Parsea tipo (posicion | tendencia | movimiento) + activo/scope opcional.
         Sin tipo → pregunta cuál de los 3. No asume nada.
PASO 2 — Resuelve activos desde plan_hoy.json (validando fecha == hoy):
           posicion/tendencia: activo dado → 1 poll; sin activo → loop activos_hoy.
           movimiento: activos_hoy (default) | 4 principales (scope "semana").
         plan_hoy.json desfasado → avisa y pide activos manualmente.
PASO 3 — Contexto opcional: lee ultimo_evento.json SOLO para ordenar activos y el guiño
         cualitativo. Nunca vuelca números.
PASO 4 — Genera el/los poll(s) del tipo pedido: pregunta + guiño + opciones.
         Sin precios, sin explicación. Cada opción ≤ 100 chars con emoji. Pregunta ≤ 255.
PASO 5 — Aprobación del director → guarda en data/mensajes/YYYY-MM-DD_HH-MM_encuesta.txt
         + registra en historial_encuestas.json (estado "registrada").
```

**Salida cuando se generan varios polls** (`posicion`/`tendencia` sin activo): **un único
archivo** `data/mensajes/YYYY-MM-DD_HH-MM_encuesta.txt` con los polls separados por
`━━━━━━━━━━━━━━━━━━━`, y **un registro por poll** en `historial_encuestas.json` (cada activo
es su propia encuesta nativa de WhatsApp).

## 10. Desacople de `/rencuesta`

- Hoy `/encuesta post_evento` alimenta a `/rencuesta` (revelado + malla de conceptos).
- Tras este cambio, `/encuesta` **deja de producir** `post_evento` / `educativa`, por lo que
  **deja de alimentar** a `/rencuesta`.
- **Guard defensivo mínimo en `rencuesta.md`:** hoy `/rencuesta` sin argumento toma la
  "última encuesta" del historial esperando `post_evento`/`educativa`. Con los tipos nuevos
  (`posicion`/`tendencia`/`movimiento`, estado `registrada`), su modo no-arg podría tomar un
  registro de sentimiento sin `respuesta_correcta` y fallar. Se agrega una regla defensiva:
  `/rencuesta` sin argumento **ignora** los tipos de sentimiento y busca la última encuesta
  educativa; si no hay ninguna, avisa que no hay tema pendiente y sugiere `/rencuesta [tema]`.
  Este es el **único** cambio en `rencuesta.md` (defensivo, no rework).
- `/rencuesta` sigue funcional vía su argumento `[tema]` y `mapa`. La reconstrucción del
  revelado automático post-evento pertenece a la futura área educativa.
- Se elimina de `encuesta.md` toda referencia que dirija el revelado hacia `/rencuesta`.

## 11. Edge cases y reglas

- **Tipo faltante:** preguntar, nunca asumir.
- **`plan_hoy.json` desfasado o ausente:** avisar y pedir activos manualmente.
- **`ultimo_evento.json` desfasado o ausente:** omitir priorización y guiño (poll seco).
- **`movimiento` con <2 activos:** no se puede crear poll; pedir activos manualmente.
- **Cero números de precio** en el poll ni en `contexto_ref`.
- **Regla de oro (votar informado):** la cumple el mensaje previo, no la encuesta.
- **Límites WhatsApp:** pregunta ≤ 255 chars, cada opción ≤ 100 chars (emoji incluido), 2–12 opciones.
- **`movimiento`:** las opciones son nombres de activos; no exceder 12.

## 12. Archivos tocados

- `.claude/commands/encuesta.md` — reescritura del flujo y los tipos.
- `.claude/commands/rencuesta.md` — solo el guard defensivo del modo sin-argumento (ver §10).
- `templates/encuesta_posicion.txt` — nuevo.
- `templates/encuesta_tendencia.txt` — quitar contexto/precio.
- `templates/encuesta_semanal.txt` — ajustar a `movimiento`.
- `CLAUDE.md` — actualizar descripción de `/encuesta` (3 tipos, sin precios/educación) y nota de migración educativa.
- `docs/commands-reference.md` — actualizar la referencia de `/encuesta`.

## 13. Criterios de aceptación

- `/encuesta posicion`, `/encuesta tendencia`, `/encuesta movimiento` generan **solo** su pieza.
- Ningún poll contiene precios ni números de datos macro.
- `posicion`/`tendencia` sin activo recorren los activos del día; con activo generan uno solo.
- `/encuesta` sin tipo pregunta cuál usar.
- `plan_hoy.json` desfasado dispara aviso y pedido manual, no polls con activos viejos.
- Los tipos `precio` y `post_evento` ya no existen en `/encuesta`.
- `historial_encuestas.json` registra los nuevos tipos con estado `registrada`, sin `respuesta_correcta`.
- `/rencuesta` solo recibe el guard defensivo: su modo sin-argumento ignora tipos de sentimiento y sigue operable por `[tema]` y `mapa`.
