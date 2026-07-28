# Parte de Post-Venta (`/postventa`) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear el comando `/postventa`, que genera un parte diario consolidado para el grupo interno de post-venta con siete bloques: consulta anticipada, preguntas frecuentes redactadas, a quién contactar por segmento, acompañamiento de posición abierta, resumen de los otros activos, rendición de cuentas de lo enviado, y límites de lo que no se promete.

**Architecture:** Es un sistema de prompts (slash commands en Markdown) + una plantilla `.txt`, no código ejecutable. No hay test runner aplicable: los tests de `tests/` cubren el MCP Python (`market_data_mcp`) y el renderer de Stories, no los prompts. La verificación es por inspección (grep/lectura) y por un dry-run real del comando contrastado contra los 10 criterios de aceptación del design doc — mismo criterio que usaron los planes de `/encuesta`, `/apertura`, `/curriculo` y `/rencuesta`.

**Tech Stack:** Slash commands de Claude Code (Markdown), plantilla `.txt` con `{{placeholders}}`, datos JSON en `data/`, helper PowerShell `scripts/ruta_mensaje.ps1`, tool MCP `mcp__market-data__get_asset_levels`. Design de referencia: `docs/design/hub-interno/2026-07-28-parte-postventa-design.md`. Rama: `feat/parte-postventa`, salida de `master`.

## Global Constraints

Estas reglas aplican a **todas** las tareas del plan. Valores copiados literalmente del design doc y de `CLAUDE.md`:

- **Banner obligatorio**: `🔒 INTERNO · NO ENVIAR AL CLIENTE` en toda salida del comando, sin excepción.
- **Flag `ejecutivo` rechazado**: si aparece en los argumentos, avisar y continuar con el flujo normal (nunca abortar, nunca generar guion). Mismo criterio que `/ventas`.
- **Hora de Chile**: siempre del reloj del sistema con `Pacific SA Standard Time`. Nunca `WebSearch` para la hora.
- **Decimales**: todo precio respeta el campo `digits` de `config/activos.json` para ese activo. Nunca truncar ceros finales.
- **Segmentos**: catálogo cerrado de cinco, sin inventar etiquetas nuevas — con exposición al activo protagonista · dormido (2+ semanas) · novato en formación · operador frecuente · con la posición en contra.
- **Sin clientes concretos**: la pieza nunca nombra un cliente. Solo segmentos.
- **Sin envío automático**: el flujo termina en texto listo para copiar.
- **Separadores**: `━━━━━━━━━━━━━━━━━━━` entre bloques.
- **Registro**: directo y profesional para audiencia interna (no exige explicar cada sigla como al cliente), manteniendo la prohibición de dramatización catastrófica de `CLAUDE.md`.

---

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `templates/parte_postventa.txt` | Plantilla del parte: los 7 bloques con sus `{{placeholders}}` | Crear |
| `.claude/commands/postventa.md` | Prompt del comando: recolección, redacción, aprobación, guardado | Crear |
| `CLAUDE.md` | Tabla de slash commands (25 → 26), lista de tipos de `data/mensajes/`, `/postventa` en los no elegibles del flag `ejecutivo` | Modificar |
| `.claude/shared/modo_ejecutivo.md` | Agregar `/postventa` a la lista de comandos no elegibles | Modificar |
| `docs/commands-reference.md` | Entrada detallada de `/postventa` | Modificar |

No se toca `templates/guion_ejecutivo.txt` ni `.claude/commands/ventas.md`: audiencias distintas, coexisten.

---

## Task 1: Plantilla del parte

**Files:**
- Create: `templates/parte_postventa.txt`

**Interfaces:**
- Consumes: nada (primera tarea).
- Produces: los placeholders que el comando de la Task 2 debe rellenar — `{{fecha_larga}}`, `{{hora}}`, `{{consulta_anticipada}}`, `{{respuesta_anticipada}}`, `{{pregunta_1..3}}`, `{{respuesta_1..3}}`, `{{bloque_segmentos}}`, `{{activo_nombre}}`, `{{escenario_vigente}}`, `{{nivel_invalidacion}}`, `{{nota_riesgo}}`, `{{bloque_otros_activos}}`, `{{bloque_rendicion}}`, `{{bloque_no_promesas}}`.

- [ ] **Step 1: Crear `templates/parte_postventa.txt`**

Contenido exacto. Los bloques `{{bloque_*}}` son multilínea: el comando los arma como una lista de líneas ya formateadas.

```text
🔧 *PARTE POST-VENTA — {{fecha_larga}} · {{hora}}*
🔒 INTERNO · NO ENVIAR AL CLIENTE
━━━━━━━━━━━━━━━━━━━
🚨 *La consulta que va a entrar hoy*
"{{consulta_anticipada}}"
→ {{respuesta_anticipada}}
━━━━━━━━━━━━━━━━━━━
❓ *Preguntas frecuentes de hoy*

• "{{pregunta_1}}"
→ {{respuesta_1}}

• "{{pregunta_2}}"
→ {{respuesta_2}}

• "{{pregunta_3}}"
→ {{respuesta_3}}
━━━━━━━━━━━━━━━━━━━
📞 *A quién contactar hoy*
{{bloque_segmentos}}
━━━━━━━━━━━━━━━━━━━
🧭 *Si tiene posición abierta en {{activo_nombre}}*
Escenario vigente: {{escenario_vigente}}
Se invalida si: {{nivel_invalidacion}}
Riesgo: {{nota_riesgo}}
━━━━━━━━━━━━━━━━━━━
📊 *Los otros activos, en una línea*
{{bloque_otros_activos}}
━━━━━━━━━━━━━━━━━━━
📋 *Qué dijimos vs. qué pasó*
{{bloque_rendicion}}
━━━━━━━━━━━━━━━━━━━
⚠️ *Lo que NO se promete hoy*
{{bloque_no_promesas}}
```

- [ ] **Step 2: Verificar que el bloque 1 cabe above-the-fold**

WhatsApp muestra ~200 caracteres antes del "leer más". Hay que medir cuánto consume el texto fijo del encabezado para saber qué presupuesto queda para la consulta y su respuesta.

**No usar `wc -c` ni `wc -m`**: en Git Bash de este entorno el locale no es UTF-8, así que ambos cuentan **bytes**, y con emojis (4 bytes) y separadores `━` (3 bytes) el resultado infla ~30%. Medir con Python:

**Ojo con el cálculo**: `{{fecha_larga}}` y `{{hora}}` **sí** se expanden a contenido real, así que no se pueden descontar como si fueran cero — solo `{{consulta_anticipada}}` y `{{respuesta_anticipada}}` son el presupuesto libre. Sustituir fecha y hora por valores de ejemplo antes de medir:

```bash
PYTHONIOENCODING=utf-8 python -c "
import pathlib, re
ls = pathlib.Path('templates/parte_postventa.txt').read_text(encoding='utf-8').splitlines()[:5]
real = chr(10).join(ls).replace('{{fecha_larga}}','Martes 28 jul').replace('{{hora}}','18:52')
base = re.sub(r'\{\{[a-z_0-9]*\}\}', '', real)
print('base:', len(base), 'chars')
print('presupuesto para consulta+respuesta:', 200 - len(base), 'chars')
"
```
Expected: `base: 98 chars` y `presupuesto: 102 chars`. Ese presupuesto de **102 caracteres** se documenta en el comando (Task 2, PASO 6).

El encabezado está deliberadamente comprimido (`🔧 *POST-VENTA · …*`, sin separador antes del bloque 1, rótulo corto `🚨 *La consulta de hoy*`) precisamente para liberar ese presupuesto. Un encabezado más largo dejaba solo ~61 caracteres, con los que el bloque 1 queda telegráfico e inservible.

- [ ] **Step 3: Verificar que no falte ningún placeholder del design**

Run:
```bash
grep -o '{{[a-z_0-9]*}}' templates/parte_postventa.txt | sort -u
```
Expected: exactamente estos 18 tokens, uno por línea —
`{{activo_nombre}}`, `{{bloque_no_promesas}}`, `{{bloque_otros_activos}}`, `{{bloque_rendicion}}`, `{{bloque_segmentos}}`, `{{consulta_anticipada}}`, `{{escenario_vigente}}`, `{{fecha_larga}}`, `{{hora}}`, `{{nivel_invalidacion}}`, `{{nota_riesgo}}`, `{{pregunta_1}}`, `{{pregunta_2}}`, `{{pregunta_3}}`, `{{respuesta_1}}`, `{{respuesta_2}}`, `{{respuesta_3}}`, `{{respuesta_anticipada}}`.

- [ ] **Step 4: Commit**

```bash
git add templates/parte_postventa.txt
git commit -m "feat(postventa): plantilla del parte de post-venta"
```

---

## Task 2: El comando `/postventa`

**Files:**
- Create: `.claude/commands/postventa.md`

**Interfaces:**
- Consumes: `templates/parte_postventa.txt` y sus 16 placeholders (Task 1).
- Produces: el comando `/postventa`, que la Task 3 referencia en la documentación y la Task 4 ejecuta como dry-run.

- [ ] **Step 1: Crear `.claude/commands/postventa.md` con el contenido completo**

```markdown
Genera el Parte de Post-Venta: un informe diario consolidado para el grupo interno de post-venta, con las consultas que va a generar el evento del día, las respuestas redactadas, a quién contactar y qué no prometer. No es un mensaje de cliente: nunca se reenvía.

## Rechazo del flag `ejecutivo`

Si los argumentos incluyen `ejecutivo`:
```
ℹ️ /postventa no soporta el modo ejecutivo — su contenido ya es 100% interno para el
equipo de post-venta, no necesita un guion adicional. Continuando con el parte normal.
```
Continuar normalmente con el PASO 1 (no abortar).

## PASO 1 — Hora de Chile

Obtener el timestamp actual con el reloj del sistema (regla canónica de `CLAUDE.md`, NUNCA con `WebSearch`):
```powershell
$tz = [System.TimeZoneInfo]::FindSystemTimeZoneById('Pacific SA Standard Time')
([System.TimeZoneInfo]::ConvertTime([DateTime]::UtcNow, [System.TimeZoneInfo]::Utc, $tz)).ToString('yyyy-MM-dd HH:mm')
```
Guardar la fecha como `[FECHA]` (`yyyy-MM-dd`), la hora como `[HORA]` (`HH:mm`) y su forma de archivo `[HORA_ARCHIVO]` (`HH-mm`). `{{fecha_larga}}` es la fecha en formato legible (ej. "Martes 28 jul").

## PASO 2 — Evento del día

Leer `data/ultimo_evento.json`.

**Validar frescura**: comparar su `timestamp` con `[FECHA]`.
- **Fresco (de hoy)** → ese es el evento del día. Extraer `evento`, `activo`, `dato_real`, `dato_esperado`.
- **Desfasado o ausente** → preguntar al director:
  ```
  ⚠️ `ultimo_evento.json` está desfasado (fecha: [fecha del archivo], hoy: [FECHA]).
  ¿Cuál es el evento del día que debe cubrir el parte?
  ```
  No continuar hasta tener respuesta. **Nunca inventar el evento ni usar el viejo.**

Complementar con `mcp__market-data__obtener_calendario_macro` para saber qué eventos ya salieron hoy y cuáles vienen en las próximas horas o mañana — el bloque 7 (lo que no se promete) suele apoyarse en un evento próximo.

## PASO 3 — Activo protagonista y sus niveles

El activo protagonista es `ultimo_evento.activo`.

Llamar una vez:
```
mcp__market-data__get_asset_levels({"ticker": "[TICKER_MT5]", "timeframe": "H1"})
```
Extraer `price`, el soporte y la resistencia más próximos, y `atr_14` (alimenta la línea de riesgo del bloque 4).

Si retorna `{"error": ...}` (mismo patrón que `apertura.md` PASO 4A), pedir manualmente precio actual, soporte y resistencia más próximos. No abortar.

## PASO 4 — Los otros activos de la rotación

Leer `data/plan_hoy.json`.

**Validar frescura**: comparar `plan_hoy.fecha` con `[FECHA]`.
- No coincide o el archivo no existe → avisar al director y pedir los activos manualmente. No usar activos viejos.
- Coincide → usar `activos_hoy`, **excluyendo** al protagonista.

Por cada uno, llamar `get_asset_levels` con `timeframe: "H1"`. Si una llamada falla, pedir ese valor manual y seguir con el resto — una fila caída no aborta la tabla.

## PASO 5 — Rendición de cuentas

Listar el contenido de `data/mensajes/[FECHA]/` (todas las carpetas de activo y tipo). Por cada pieza enviada hoy, extraer qué se afirmó y contrastarlo con el resultado real (`actual` del calendario o el precio actual del activo).

- **Hubo al menos una pieza** → armar `{{bloque_rendicion}}` con tres líneas: `Dijimos (HH:MM): …`, `Pasó: …` (con ✅ si se cumplió, ⚠️ si no), y `Cómo contarlo: …`.
- **No hubo ninguna pieza hoy** → **omitir el bloque 7 completo**, incluyendo su encabezado `📋 *Qué dijimos vs. qué pasó*` y el separador que lo precede. No rellenar con texto vacío ni con "sin novedades".

## PASO 6 — Redactar el parte

Rellenar `templates/parte_postventa.txt`. Reglas de redacción por bloque:

- **Bloque 1 (consulta anticipada)**: UNA sola pregunta, la más probable dado el evento. La consulta más su respuesta deben caber en **79 caracteres sumados** — el texto fijo del encabezado consume 121 de los ~200 visibles de WhatsApp antes del "leer más". Si no alcanza, priorizar la respuesta sobre el detalle de la pregunta.
- **Bloque 2 (preguntas frecuentes)**: exactamente 3 preguntas distintas de la del bloque 1. Cada respuesta va **redactada en la voz del ejecutivo, lista para copiar y adaptar** — nunca un bullet de tema. Incluir niveles reales cuando la respuesta lo pida.
- **Bloque 3 (a quién contactar)**: 2 a 4 líneas, cada una con el formato `• [segmento] → [excusa de contacto y qué decir]`. Usar SOLO las cinco etiquetas del catálogo: con exposición al activo protagonista · dormido (2+ semanas) · novato en formación · operador frecuente · con la posición en contra.
- **Bloque 4 (posición abierta)**: escenario vigente con dirección explícita (alcista/bajista/lateral), el nivel exacto que lo invalida, y una línea de riesgo apoyada en el ATR (ej. "el rango típico por hora es de ~X"). Prohibido prometer dirección.
- **Bloque 5 (otros activos)**: una línea por activo, formato `• [Nombre] [valor], [estado] → [qué decir]`.
- **Bloque 6 (rendición)**: según PASO 5.
- **Bloque 7 (no se promete)**: 2 a 4 límites concretos del día, atados al evento próximo detectado en el PASO 2.

Todo precio con los `digits` de `config/activos.json`.

## PASO 7 — Aprobación

Mostrar el parte completo al director y preguntar:
```
¿Apruebas el parte de post-venta? ¿Enviar al grupo interno?
```

Si el director **no** aprueba: **DETENER. No guardar nada.**

## PASO 8 — Guardado

Tras aprobar, construir la ruta con el helper determinista (NUNCA a mano):
```powershell
scripts\ruta_mensaje.ps1 -Fecha "[FECHA]" -Activo "[TICKER_MT5]" -Tipo "postventa" -Hora "[HORA_ARCHIVO]"
# -> data/mensajes/2026-07-28/usdclp/postventa/18-20_postventa.txt
```
Escribir el parte en la ruta devuelta y mostrar el texto listo para copiar.

## REGLAS

- Una corrida al día es lo normal (al cierre de la jornada o tras el evento principal); sin límite duro.
- Banner `🔒 INTERNO · NO ENVIAR AL CLIENTE` siempre presente. Nunca sugerir enviarlo al grupo de clientes.
- Nunca nombrar clientes concretos — solo las cinco etiquetas de segmento. El comando no lee CRM ni ve posiciones reales (la Manager API del bróker no está disponible).
- Hora en hora Chile (CLT/CLST); precios con los `digits` de `config/activos.json`.
- Registro directo y profesional para audiencia interna, sin dramatización catastrófica (ver "Registro y tono" en `CLAUDE.md`).
- Sin envío automático: el flujo termina en texto listo para copiar, igual que el resto del pipeline.
- `/postventa` no soporta el flag `ejecutivo`.
```

- [ ] **Step 2: Verificar que el comando cubre los 8 pasos y las reglas duras**

Run:
```bash
grep -c '^## PASO' .claude/commands/postventa.md
```
Expected: `8`

Run:
```bash
grep -c 'NO ENVIAR AL CLIENTE' .claude/commands/postventa.md
```
Expected: al menos `2` — la verificación defensiva del PASO 7 (antes de mostrar el parte al director) y la regla final. El banner en sí vive en `templates/parte_postventa.txt`, no en el comando; el comando solo exige conservarlo.

- [ ] **Step 3: Verificar que los placeholders del comando calzan con la plantilla**

Los nombres de bloque citados en el PASO 6 deben existir en `templates/parte_postventa.txt`.

Run:
```bash
for t in consulta_anticipada respuesta_anticipada bloque_segmentos bloque_otros_activos bloque_rendicion bloque_no_promesas escenario_vigente nivel_invalidacion nota_riesgo; do grep -q "{{$t}}" templates/parte_postventa.txt && echo "OK $t" || echo "FALTA $t"; done
```
Expected: nueve líneas `OK`, ninguna `FALTA`.

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/postventa.md
git commit -m "feat(postventa): comando /postventa con los 7 bloques del parte"
```

---

## Task 3: Integración en la documentación

**Files:**
- Modify: `CLAUDE.md`
- Modify: `.claude/shared/modo_ejecutivo.md`
- Modify: `docs/commands-reference.md`

**Interfaces:**
- Consumes: el comando `/postventa` (Task 2).
- Produces: nada que otra tarea consuma; cierra la coherencia documental.

- [ ] **Step 1: Agregar `/postventa` a la tabla de Capa 2 de `CLAUDE.md`**

En la tabla "Capa 2 — Comandos de tarea (ad hoc)", inmediatamente después de la fila de `/ventas`, insertar:

```markdown
| `/postventa` | Parte diario para el equipo interno de post-venta: consultas que va a generar el evento del día con respuestas redactadas, a quién contactar por segmento, acompañamiento de posiciones abiertas, rendición de lo dicho y límites de lo que no se promete. 100% interno, no se reenvía al cliente. |
```

- [ ] **Step 2: Actualizar el conteo de comandos en `CLAUDE.md`**

El encabezado dice `## Slash Commands disponibles (25)`. Cambiar a `(26)`.

Run:
```bash
grep -n 'Slash Commands disponibles' CLAUDE.md
```
Expected: la línea ya dice `(26)`.

- [ ] **Step 3: Agregar `postventa` a la lista de tipos de archivo en `CLAUDE.md`**

En la sección "Flujo de aprobación → WhatsApp", la línea que enumera los tipos dice:

```
**Tipos de archivo** (carpeta `<tipo>`): niveles, dato_macro, noticia, alerta, encuesta, señal, concepto, pregunta, respuesta, cierre, earnings.
```

Agregar `postventa` al final de la enumeración, antes del punto.

- [ ] **Step 4: Agregar `/postventa` a los no elegibles del flag `ejecutivo`**

Dos archivos dicen lo mismo y deben quedar consistentes:

1. En `CLAUDE.md`, párrafo "Modo ejecutivo (flag `ejecutivo`)", la lista de **No elegibles** menciona `/estado`, `/chart`, `/curriculo` y `/ventas`. Agregar `/postventa` con la razón: "su contenido ya es 100% interno para el equipo de post-venta — mismo criterio que `/ventas`".
2. En `.claude/shared/modo_ejecutivo.md`, sección "No elegibles", agregar la misma entrada con la misma razón.

Run:
```bash
grep -c 'postventa' .claude/shared/modo_ejecutivo.md
```
Expected: al menos `1`

- [ ] **Step 5: Agregar la entrada detallada en `docs/commands-reference.md`**

El archivo usa el formato `### \`/comando\`` + párrafo descriptivo + `---` como separador. Insertar en la sección "Capa 2 — Comandos de tarea (ad hoc)", después de la entrada de `/estado`:

```markdown
### `/postventa`
Genera el Parte de Post-Venta: un informe diario para el grupo interno de post-venta (no es un mensaje de cliente, nunca se reenvía). Siete bloques: la consulta que va a entrar hoy con su respuesta, tres preguntas frecuentes redactadas para copiar, a quién contactar por segmento, cómo acompañar una posición abierta en el activo protagonista, los otros activos del día en una línea, qué dijimos vs. qué pasó, y los límites de lo que no se promete. Toma el evento de `data/ultimo_evento.json`, los niveles de `get_asset_levels` y la rendición de cuentas de `data/mensajes/<fecha>/`. Usa un catálogo cerrado de cinco segmentos: con exposición al activo protagonista, dormido (2+ semanas), novato en formación, operador frecuente, y con la posición en contra. No lee CRM ni ve posiciones reales. Rechaza el flag `ejecutivo` (su contenido ya es 100% interno).

---
```

- [ ] **Step 5b: Agregar `postventa` a la tabla "Tipos de archivo guardado"**

El mismo archivo cierra con una tabla `| Tipo | Descripción |`. Agregar la fila:

```markdown
| `postventa` | Parte diario para el equipo interno de post-venta |
```

- [ ] **Step 6: Verificar coherencia global de la documentación**

Run:
```bash
grep -rn 'postventa' CLAUDE.md .claude/shared/modo_ejecutivo.md docs/commands-reference.md | wc -l
```
Expected: al menos `5` coincidencias (tabla de comandos, tipos de archivo, no elegibles en dos archivos, entrada de referencia).

- [ ] **Step 7: Commit**

```bash
git add CLAUDE.md .claude/shared/modo_ejecutivo.md docs/commands-reference.md
git commit -m "docs(postventa): integra /postventa en CLAUDE.md, modo ejecutivo y referencia"
```

---

## Task 4: Dry-run contra los criterios de aceptación

**Files:**
- Test (manual): ejecutar `/postventa` en una sesión real
- Modify (si el dry-run lo exige): `templates/parte_postventa.txt`, `.claude/commands/postventa.md`

**Interfaces:**
- Consumes: todo lo anterior.
- Produces: el parte validado y, si hubo ajustes, las correcciones a plantilla y comando.

- [ ] **Step 1: Ejecutar el comando con datos reales**

Ejecutar `/postventa` en una jornada que tenga un evento fresco en `data/ultimo_evento.json` y al menos una pieza en `data/mensajes/<hoy>/`. Guardar la salida sin aprobar todavía.

- [ ] **Step 2: Contrastar contra los 10 criterios de aceptación del design doc**

Verificar uno por uno, marcando cada resultado:

1. Los siete bloques aparecen en el orden especificado.
2. El bloque 1 (consulta + respuesta) cabe en ~200 caracteres.
3. Las respuestas de los bloques 1 y 2 están redactadas para copiar, no son bullets de tema.
4. El bloque 3 usa exclusivamente las cinco etiquetas del catálogo.
5. El bloque 5 tiene una línea por cada activo de `plan_hoy.json` distinto del protagonista.
6. Con al menos una pieza enviada ese día, el bloque 6 la cita con su hora; sin piezas, el bloque se omite entero.
7. Con `ultimo_evento.json` desfasado, el comando pregunta en vez de inventar el evento.
8. Con el flag `ejecutivo`, avisa que no aplica y continúa.
9. Al aprobar, el archivo queda en `data/mensajes/<fecha>/<activo>/postventa/<hora>_postventa.txt`.
10. Si el director no aprueba, no se escribe nada.

Los criterios 7, 8 y 10 requieren corridas dedicadas: renombrar temporalmente `ultimo_evento.json` para el 7, invocar `/postventa ejecutivo` para el 8, y responder que no en el paso de aprobación para el 10.

- [ ] **Step 3: Medir el largo real del bloque above-the-fold**

Guardar el parte generado en el directorio de scratchpad de la sesión (nunca en `/tmp`, nunca en el repo) y medir en **caracteres**, no en bytes (ver Task 1 Step 2 — `wc` cuenta bytes en este entorno):

```bash
PYTHONIOENCODING=utf-8 python -c "
import pathlib, sys
ls = pathlib.Path(sys.argv[1]).read_text(encoding='utf-8').splitlines()[:6]
print(len(chr(10).join(ls)), 'chars')
" "$SCRATCHPAD/parte_dryrun.txt"
```
Expected: ≤ 200. Si excede, acortar la respuesta del bloque 1 en el PASO 6 del comando (no la plantilla) y repetir.

- [ ] **Step 4: Corregir lo que el dry-run haya revelado**

Ajustar `templates/parte_postventa.txt` o `.claude/commands/postventa.md` según los hallazgos. Repetir el Step 1 hasta que los 10 criterios pasen.

- [ ] **Step 5: Commit**

```bash
git add templates/parte_postventa.txt .claude/commands/postventa.md
git commit -m "fix(postventa): ajustes del dry-run contra los criterios de aceptación"
```

(Si el dry-run no exigió cambios, saltar este commit.)

- [ ] **Step 6: Abrir el PR**

```bash
git push -u origin feat/parte-postventa
gh pr create --title "feat(postventa): comando /postventa para el equipo interno de post-venta" --body "Implementa el parte diario de post-venta según docs/design/hub-interno/2026-07-28-parte-postventa-design.md"
```

---

## Notas de ejecución

- **Rama**: crear `feat/parte-postventa` desde `master`, no desde `feat/story-resumen-dia` (esa rama es de otro trabajo y mezclarlas ensuciaría su PR).
- **Working tree**: al empezar hay cambios sin commitear en `data/historial_encuestas.json` y `uv.lock` que **no pertenecen a este trabajo**. No incluirlos en ningún commit de este plan — los `git add` de cada tarea son explícitos por archivo, precisamente por eso.
- **Sin tests automáticos**: no agregar tests a `tests/` — esa suite cubre el MCP Python y el renderer de Stories, no los prompts. Correr `uv run pytest` igual antes del PR para confirmar que nada se rompió: debe seguir en verde sin cambios.
