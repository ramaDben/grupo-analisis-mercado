# Modo ejecutivo de los paquetes diarios — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar un flag `ejecutivo` a los 7 comandos de día que, por cada pieza, genera el mensaje de cliente actual + un guion de venta privado para el grupo interno de ejecutivos.

**Architecture:** Estructura A (parcial compartido). Un archivo único `.claude/commands/_modo_ejecutivo.md` define el contrato del guion, el flujo por pieza, la regla de guardado interno y los guardrails. Una plantilla `templates/guion_ejecutivo.txt` fija el formato WhatsApp. Cada comando de día agrega una sección corta `## MODO EJECUTIVO` que referencia el parcial (sin duplicar lógica). Sin el flag, los comandos se comportan exactamente como hoy.

**Tech Stack:** Slash commands en Markdown (`.claude/commands/`), plantillas de texto (`templates/`), helper PowerShell existente `scripts/ruta_mensaje.ps1` (sin cambios). No hay código ejecutable nuevo ni tests automatizados; la verificación es por inspección de contenido (Grep/Read).

## Global Constraints

- **Reglas de oro intactas en el mensaje de cliente**: dirección clara (alcista/bajista/lateral), formato visual WhatsApp, decimales MT5 según `config/activos.json`, hora Chile (CLT/CLST), un indicador por aviso. El modo ejecutivo reusa el contenido de cliente tal cual; no lo altera.
- **Tono del guion**: profesional y persuasivo (énfasis direccional y gancho permitidos); prohibido lo extremo/catastrófico/coloquial (ver "Registro y tono" en `CLAUDE.md`). Toda sigla/term técnico se explica en voz novata.
- **Anti-filtración**: el guion SIEMPRE lleva el banner `🔒 INTERNO · NO ENVIAR AL CLIENTE` y se guarda en carpeta `guion_*` separada. Nunca se mezcla en el mensaje de cliente.
- **Guardado**: usar `scripts/ruta_mensaje.ps1` (nunca armar rutas a mano). Guion → tipo `guion_<tipo>`, mismo `-Activo` y `-Hora` que el mensaje de cliente.
- **Una sola fuente de verdad**: el contrato del guion vive solo en `_modo_ejecutivo.md`; los 7 comandos lo referencian, no lo copian.
- **DRY · YAGNI · commits frecuentes.**

---

### Task 1: Plantilla del guion ejecutivo

**Files:**
- Create: `templates/guion_ejecutivo.txt`

**Interfaces:**
- Consumes: nada.
- Produces: la plantilla canónica del bloque guion, referenciada por `_modo_ejecutivo.md` (Task 2). Estructura fija: banner, `🎯 Gancho`, `👥 Para quién`, `💬 Qué decir`, `🛡️ Si te dicen…`, `✅ Objetivo`.

- [ ] **Step 1: Crear el archivo de plantilla**

Crear `templates/guion_ejecutivo.txt` con exactamente este contenido:

```text
🔒 *GUION EJECUTIVO — [PIEZA]*  ·  INTERNO · NO ENVIAR AL CLIENTE
━━━━━━━━━━━━━━━━━━━
🎯 Gancho: [1 línea comercial conectada al contenido de la pieza]
👥 Para quién: [novato / activo / dormido / prospecto frío] — [por qué encaja hoy]
━━━━━━━━━━━━━━━━━━━
💬 Qué decir (copiar y adaptar):
"[1-2 frases textuales para acompañar el reenvío del mensaje]"
━━━━━━━━━━━━━━━━━━━
🛡️ Si te dicen…
• "[objeción típica 1]" → [respuesta corta]
• "[objeción típica 2]" → [respuesta corta]
━━━━━━━━━━━━━━━━━━━
✅ Objetivo: [llamado a la acción concreto: abrir cuenta / subir de plan / reactivar / agendar / invitar a operar]
```

- [ ] **Step 2: Verificar contenido**

Run (Grep): buscar `INTERNO · NO ENVIAR AL CLIENTE` en `templates/guion_ejecutivo.txt`.
Expected: 1 coincidencia. Confirmar también que aparecen las 5 etiquetas `🎯 Gancho`, `👥 Para quién`, `💬 Qué decir`, `🛡️ Si te dicen`, `✅ Objetivo`.

- [ ] **Step 3: Commit**

```bash
git add templates/guion_ejecutivo.txt
git commit -m "feat(ejecutivo): plantilla WhatsApp del guion de venta interno"
```

---

### Task 2: Parcial compartido `_modo_ejecutivo.md`

**Files:**
- Create: `.claude/commands/_modo_ejecutivo.md`

**Interfaces:**
- Consumes: `templates/guion_ejecutivo.txt` (Task 1); helper `scripts/ruta_mensaje.ps1`.
- Produces: el contrato `_modo_ejecutivo.md` que los 7 comandos de día referencian (Task 3). Define: formato del guion, flujo por pieza (doble salida, aprobación, guardado `guion_<tipo>`), tono y guardrail anti-filtración.

- [ ] **Step 1: Crear el parcial**

Crear `.claude/commands/_modo_ejecutivo.md` con exactamente este contenido:

````markdown
# Modo ejecutivo — contrato compartido de los comandos de día

> Este archivo NO es un comando invocable. Es el contrato único que siguen los
> 7 comandos de día (`/domingo`, `/lunes`, `/martes`, `/miercoles`, `/jueves`,
> `/viernes_am`, `/viernes_pm`) cuando se invocan con el argumento `ejecutivo`
> (ej. `/lunes ejecutivo`). Define cómo se genera, muestra y guarda el guion de
> venta privado que acompaña a cada pieza. Si cambia el formato del guion, se
> cambia AQUÍ y se propaga a todos los días.

## Qué activa el modo
El comando de día detecta `ejecutivo` en sus argumentos. Si está presente, por
CADA pieza del paquete genera DOS salidas; si no está, ignora este contrato y
produce solo el contenido de cliente, como siempre.

## Las dos salidas por pieza
1. **📤 MENSAJE CLIENTE** — idéntico al que el comando produce hoy. Conserva
   todas las reglas de oro: dirección clara (alcista/bajista/lateral), formato
   visual WhatsApp, decimales MT5 según `config/activos.json`, hora Chile
   (CLT/CLST), un indicador por aviso. El modo ejecutivo NO altera esta salida:
   la reusa tal cual.
2. **🔒 GUION EJECUTIVO** — privado, destino el grupo interno de ejecutivos.
   Sigue la plantilla `templates/guion_ejecutivo.txt`. Los 4 elementos son
   obligatorios:
   - 🎯 **Gancho** + 👥 **Para quién** (novato / activo / dormido / prospecto frío)
   - 💬 **Qué decir**: 1-2 frases textuales para acompañar el reenvío
   - 🛡️ **Manejo de objeciones**: 1-2 objeciones típicas + respuesta corta
   - ✅ **Objetivo** (llamado a la acción): abrir cuenta / subir de plan /
     reactivar / agendar / invitar a operar

   Reemplazar `[PIEZA]` por el nombre de la pieza (ej. "Dato macro",
   "Apertura USD/CLP", "Encuesta del día").

## Formato del guion
```
🔒 *GUION EJECUTIVO — [PIEZA]*  ·  INTERNO · NO ENVIAR AL CLIENTE
━━━━━━━━━━━━━━━━━━━
🎯 Gancho: [1 línea comercial conectada al contenido de la pieza]
👥 Para quién: [novato / activo / dormido / prospecto frío] — [por qué encaja hoy]
━━━━━━━━━━━━━━━━━━━
💬 Qué decir (copiar y adaptar):
"[1-2 frases textuales para acompañar el reenvío del mensaje]"
━━━━━━━━━━━━━━━━━━━
🛡️ Si te dicen…
• "[objeción típica 1]" → [respuesta corta]
• "[objeción típica 2]" → [respuesta corta]
━━━━━━━━━━━━━━━━━━━
✅ Objetivo: [llamado a la acción concreto]
```

## Flujo por pieza (modo ejecutivo activo)
1. Genera el **MENSAJE CLIENTE** igual que hoy.
2. Genera el **GUION EJECUTIVO** con el formato de arriba.
3. Muestra ambos al director, rotulados `📤 MENSAJE CLIENTE` y `🔒 GUION EJECUTIVO`.
4. Pregunta: **"¿Apruebas? ¿Enviar mensaje al grupo de clientes? ¿Enviar guion
   al grupo interno de ejecutivos?"**
5. Al aprobar, guarda los DOS con `scripts/ruta_mensaje.ps1`:
   - Mensaje cliente → su tipo normal (`niveles`, `dato_macro`, `noticia`,
     `encuesta`, `concepto`, `earnings`, `cierre`, …), mismo criterio que hoy.
   - Guion → tipo `guion_<tipo>` (ej. `guion_niveles`, `guion_dato_macro`), con
     el MISMO `-Activo` y `-Hora` que el mensaje de cliente.

   Ejemplo (niveles USD/CLP a las 09:15):
   ```powershell
   scripts\ruta_mensaje.ps1 -Fecha "2026-06-16" -Activo "USDCLP" -Tipo "niveles" -Hora "09-15"
   scripts\ruta_mensaje.ps1 -Fecha "2026-06-16" -Activo "USDCLP" -Tipo "guion_niveles" -Hora "09-15"
   ```
   Piezas sin activo protagonista (concepto, encuesta de la semana, earnings,
   paquete dominical) omiten `-Activo` → el helper guarda en `_general/` y
   `_general/guion_<tipo>/`.

   Como el envío WhatsApp aún es manual, "enviar" = mostrar el texto listo para
   copiar. El guion se muestra SIEMPRE separado del mensaje de cliente.

## Reglas y guardrails
- **Reglas de oro intactas** en el mensaje de cliente (ver arriba).
- **Tono del guion**: profesional y persuasivo; prohibido lo extremo,
  catastrófico o coloquial (ver "Registro y tono" en `CLAUDE.md`).
- **Lenguaje simple**: el guion explica en voz novata cualquier sigla/term
  técnico que use; no habilita jerga sin explicar.
- **Anti-filtración**: el guion SIEMPRE lleva el banner
  `🔒 INTERNO · NO ENVIAR AL CLIENTE` y se guarda en carpeta `guion_*`. Nunca se
  mezcla en el mensaje de cliente ni se sugiere enviarlo al grupo de clientes.
- Esto materializa el HUB INTERNO (ejecutivos) de
  `docs/design/motor-como-cerebro-hub-gi.brief.md`.
````

- [ ] **Step 2: Verificar contenido**

Run (Grep) sobre `.claude/commands/_modo_ejecutivo.md`:
- `guion_<tipo>` aparece (regla de guardado).
- `NO ENVIAR AL CLIENTE` aparece (guardrail).
- `templates/guion_ejecutivo.txt` aparece (referencia a la plantilla de Task 1).
- `¿Enviar guion al grupo interno de ejecutivos?` aparece (pregunta de aprobación).

Expected: las 4 cadenas presentes.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/_modo_ejecutivo.md
git commit -m "feat(ejecutivo): contrato compartido del modo ejecutivo (parcial DRY)"
```

---

### Task 3: Cablear el flag en los 7 comandos de día

**Files:**
- Modify: `.claude/commands/domingo.md`
- Modify: `.claude/commands/lunes.md`
- Modify: `.claude/commands/martes.md`
- Modify: `.claude/commands/miercoles.md`
- Modify: `.claude/commands/jueves.md`
- Modify: `.claude/commands/viernes_am.md`
- Modify: `.claude/commands/viernes_pm.md`

**Interfaces:**
- Consumes: `.claude/commands/_modo_ejecutivo.md` (Task 2).
- Produces: cada comando de día reconoce el argumento `ejecutivo` y delega el guion al parcial.

- [ ] **Step 1: Localizar el punto de inserción en cada archivo**

Run (Grep, output_mode content, -n) en cada uno de los 7 archivos: patrón `^## PIEZA 1`.
Anotar el número de línea de la PRIMERA coincidencia por archivo. La sección nueva se inserta
INMEDIATAMENTE ANTES de esa línea `## PIEZA 1` (después del bloque SETUP / nota de orden).

Si algún archivo no tuviera `## PIEZA 1` (ej. estructura distinta en `viernes_pm.md` o
`domingo.md`), insertar la sección justo antes del primer encabezado `## ` que introduce la
primera pieza de contenido del paquete.

- [ ] **Step 2: Insertar la sección `## MODO EJECUTIVO` en cada archivo**

En cada uno de los 7 archivos, insertar este bloque EXACTO inmediatamente antes del encabezado
de la primera pieza localizado en Step 1 (dejando una línea en blanco antes y después):

```markdown
## MODO EJECUTIVO
Si el argumento del comando es `ejecutivo` (ej. `/lunes ejecutivo`), activa MODO EJECUTIVO:
por CADA pieza de este paquete, además del mensaje de cliente, genera el guion de venta privado
siguiendo `.claude/commands/_modo_ejecutivo.md` (doble salida, aprobación y guardado `guion_<tipo>`).
Sin ese argumento, ignora esta sección y genera solo el contenido de cliente, como hasta ahora.

---
```

Nota: ajustar el ejemplo `/lunes ejecutivo` al comando correspondiente en cada archivo
(`/domingo ejecutivo`, `/martes ejecutivo`, `/miercoles ejecutivo`, `/jueves ejecutivo`,
`/viernes_am ejecutivo`, `/viernes_pm ejecutivo`).

- [ ] **Step 3: Verificar que los 7 archivos referencian el parcial**

Run (Grep, output_mode files_with_matches) patrón `_modo_ejecutivo.md` en `.claude/commands/`.
Expected: exactamente 8 archivos coinciden — los 7 comandos de día + `_modo_ejecutivo.md` mismo.

Run (Grep, output_mode files_with_matches) patrón `^## MODO EJECUTIVO` en `.claude/commands/`.
Expected: 7 archivos (los comandos de día).

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/domingo.md .claude/commands/lunes.md .claude/commands/martes.md .claude/commands/miercoles.md .claude/commands/jueves.md .claude/commands/viernes_am.md .claude/commands/viernes_pm.md
git commit -m "feat(ejecutivo): activar flag ejecutivo en los 7 comandos de dia"
```

---

### Task 4: Documentar el modo ejecutivo en `CLAUDE.md`

**Files:**
- Modify: `C:\Users\bbrav\grupo-analisis-mercado\CLAUDE.md` (sección "Flujo de aprobación → WhatsApp")

**Interfaces:**
- Consumes: el comportamiento definido en Tasks 1-3.
- Produces: documentación del flag `ejecutivo` y del tipo de guardado `guion_*` para futuras sesiones.

- [ ] **Step 1: Añadir el tipo `guion_<tipo>` a la lista de tipos de archivo**

Localizar en `CLAUDE.md` la línea que empieza con `**Tipos de archivo** (carpeta` y, justo
después de esa línea, insertar:

```markdown

**Modo ejecutivo (flag `ejecutivo`)**: los 7 comandos de día aceptan el argumento `ejecutivo` (ej. `/lunes ejecutivo`). Por cada pieza generan, además del mensaje de cliente (idéntico, con todas las reglas de oro), un **guion de venta privado** para el grupo interno de ejecutivos (gancho + a quién, qué decir, manejo de objeciones, llamado a la acción), marcado `🔒 INTERNO · NO ENVIAR AL CLIENTE`. El guion se guarda con `ruta_mensaje.ps1` bajo el tipo `guion_<tipo>` (ej. `guion_niveles`), mismo activo y hora que el mensaje de cliente. Contrato único en `.claude/commands/_modo_ejecutivo.md`.
```

- [ ] **Step 2: Verificar**

Run (Grep) patrón `Modo ejecutivo \(flag` en `CLAUDE.md`.
Expected: 1 coincidencia, ubicada dentro de la sección "Flujo de aprobación → WhatsApp".

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(claude.md): documentar el flag ejecutivo y el tipo guion_*"
```

---

## Verificación final (tras Task 4)

- [ ] `templates/guion_ejecutivo.txt` existe con los 4 bloques + banner.
- [ ] `.claude/commands/_modo_ejecutivo.md` existe y define formato, flujo, guardado y guardrails.
- [ ] Los 7 comandos de día tienen `## MODO EJECUTIVO` y referencian el parcial.
- [ ] `CLAUDE.md` documenta el flag y el tipo `guion_*`.
- [ ] Ningún comando de día duplica el contrato del guion (solo lo referencian).
- [ ] El contenido de cliente de cada comando quedó sin cambios (diff de Task 3 solo agrega la sección nueva, no toca las PIEZAS).
