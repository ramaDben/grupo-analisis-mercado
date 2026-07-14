# Modo ejecutivo de los paquetes diarios — Diseño

> **Fecha:** 2026-06-16
> **Estado:** aprobado, listo para plan de implementación.
> **Alcance:** agregar un modo ejecutivo (flag) a los 7 comandos de día, que por cada pieza
> produce, además del mensaje de cliente, un guion de venta privado para los ejecutivos.

---

## 1. Objetivo

Hoy los paquetes diarios (`/domingo`, `/lunes`, `/martes`, `/miercoles`, `/jueves`,
`/viernes_am`, `/viernes_pm`) generan contenido para el **cliente** en el grupo de WhatsApp.

Este diseño agrega una **versión ejecutivo** de esos mismos paquetes cuyo ángulo es que el
ejecutivo pueda **usar cada pieza para vender**: por cada pieza se generan **dos salidas**:

1. **Mensaje de cliente** — idéntico al actual, con todas las reglas de oro, listo para
   reenviar al grupo de clientes.
2. **Guion privado del ejecutivo** — destinado al **grupo interno de ejecutivos**, marcado
   `INTERNO · NO ENVIAR AL CLIENTE`, con gancho de venta, qué decir, manejo de objeciones y
   llamado a la acción.

Esto materializa el **HUB INTERNO (ejecutivos)** descrito en
`docs/design/motor-como-cerebro-hub-gi.brief.md`: la misma inteligencia, segmentada por
audiencia, alimentando a clientes y a ejecutivos desde una sola fuente.

---

## 2. Decisiones tomadas

| Decisión | Elección |
|---|---|
| Naturaleza de la versión ejecutivo | **Ambas**: mensaje listo para reenviar al cliente + guion de venta privado |
| Invocación | **Flag** en los comandos actuales (ej. `/lunes ejecutivo`) — sin comandos nuevos |
| Contenido del guion | Gancho + a quién · Qué decir (pitch) · Manejo de objeciones · Llamado a la acción (los 4) |
| Destino del guion | **Grupo interno de ejecutivos** (pieza aparte, marcada INTERNO) |
| Estructura de implementación | **A — parcial compartido**: un archivo único define el contrato; cada día lo referencia (DRY) |

---

## 3. Componentes

| Archivo | Acción | Rol |
|---|---|---|
| `.claude/commands/_modo_ejecutivo.md` | **nuevo** | Fuente única: contrato del guion, flujo por pieza, regla de guardado interno, tono y guardrail anti-filtración |
| `templates/guion_ejecutivo.txt` | **nuevo** | Plantilla WhatsApp del bloque guion (los 4 sub-bloques) |
| `.claude/commands/domingo.md` | **editar** | Agregar sección `## MODO EJECUTIVO` |
| `.claude/commands/lunes.md` | **editar** | Agregar sección `## MODO EJECUTIVO` |
| `.claude/commands/martes.md` | **editar** | Agregar sección `## MODO EJECUTIVO` |
| `.claude/commands/miercoles.md` | **editar** | Agregar sección `## MODO EJECUTIVO` |
| `.claude/commands/jueves.md` | **editar** | Agregar sección `## MODO EJECUTIVO` |
| `.claude/commands/viernes_am.md` | **editar** | Agregar sección `## MODO EJECUTIVO` |
| `.claude/commands/viernes_pm.md` | **editar** | Agregar sección `## MODO EJECUTIVO` |
| `CLAUDE.md` | **editar** | Documentar el flag `ejecutivo` y el tipo de guardado `guion_*` |

**Sin cambios** en `scripts/ruta_mensaje.ps1` ni en la lógica de cliente de los comandos.

---

## 4. Formato del guion (contrato en `_modo_ejecutivo.md` y `templates/guion_ejecutivo.txt`)

El guion se entrega en formato WhatsApp porque su destino es el grupo interno de ejecutivos.
Registro profesional y persuasivo; prohibido lo extremo/catastrófico/coloquial.

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
✅ Objetivo: [llamado a la acción concreto: abrir cuenta / subir de plan / reactivar / agendar / invitar a operar]
```

Los 4 elementos son **obligatorios**. El placeholder `[PIEZA]` se reemplaza por el nombre de
la pieza (ej. "Dato macro", "Apertura USD/CLP", "Encuesta del día").

---

## 5. Flujo por pieza (modo ejecutivo activo)

Por **cada** pieza del paquete del día:

1. Genera el **mensaje de cliente** igual que hoy — todas las reglas de oro: dirección clara
   (alcista/bajista/lateral), formato visual WhatsApp, decimales MT5 según `config/activos.json`,
   hora Chile (CLT/CLST), un indicador por aviso.
2. Genera el **guion** con el formato de la §4.
3. Muestra ambos al director, etiquetados `📤 MENSAJE CLIENTE` y `🔒 GUION EJECUTIVO`.
4. Pregunta: **"¿Apruebas? ¿Enviar mensaje al grupo de clientes? ¿Enviar guion al grupo
   interno de ejecutivos?"**
5. Al aprobar, **guarda los dos** con `scripts/ruta_mensaje.ps1`:
   - Mensaje cliente → tipo normal de la pieza (`niveles`, `dato_macro`, `noticia`, `encuesta`,
     `concepto`, `earnings`, `cierre`, …), mismo criterio que hoy.
   - Guion → tipo `guion_<tipo>` (ej. `guion_niveles`, `guion_dato_macro`), con el **mismo**
     `-Activo` y `-Hora` que el mensaje de cliente.

   Ejemplo de rutas resultantes para una pieza de niveles de USD/CLP a las 09:15:
   ```
   data/mensajes/2026-06-16/usdclp/niveles/09-15_niveles.txt
   data/mensajes/2026-06-16/usdclp/guion_niveles/09-15_guion_niveles.txt
   ```
   Piezas sin activo protagonista (concepto, encuesta de la semana, earnings, paquete
   dominical) omiten `-Activo` → el helper las guarda en `_general/` y `_general/guion_<tipo>/`.

Como el envío WhatsApp aún es manual, "enviar" significa mostrar el texto listo para copiar.
El guion se muestra por separado del mensaje de cliente y siempre lleva su banner.

**Sin el flag**, los 7 comandos se comportan exactamente como hoy (cero regresión).

---

## 6. Activación del flag (wiring en cada comando de día)

A cada comando de día se le agrega, cerca del inicio (antes de la PIEZA 1), esta sección:

```markdown
## MODO EJECUTIVO
Si el argumento del comando es `ejecutivo` (ej. `/lunes ejecutivo`), activa MODO EJECUTIVO:
por CADA pieza de este paquete, además del mensaje de cliente, genera el guion privado
siguiendo `.claude/commands/_modo_ejecutivo.md`. Sin ese argumento, ignora esta sección y
genera solo el contenido de cliente como hasta ahora.
```

El comando detecta el modo leyendo sus argumentos (`$ARGUMENTS` contiene `ejecutivo`).

---

## 7. Reglas y guardrails (en `_modo_ejecutivo.md`)

- **Reglas de oro intactas en el mensaje de cliente**: dirección clara, formato visual,
  decimales MT5, hora Chile, un indicador por aviso. El modo ejecutivo **no** altera el
  contenido de cliente: lo reusa tal cual.
- **Tono del guion**: profesional y persuasivo (énfasis direccional y gancho operativo
  permitidos); **prohibido** el lenguaje extremo, catastrófico o coloquial
  (ver "Registro y tono" en `CLAUDE.md`).
- **Lenguaje simple**: el guion también explica en voz novata cualquier sigla/term técnico que
  use, igual que las reglas de cliente (no habilita jerga sin explicar).
- **Anti-filtración**: el guion SIEMPRE lleva el banner `🔒 INTERNO · NO ENVIAR AL CLIENTE` y
  se guarda en carpeta `guion_*` separada. Nunca se mezcla en el mensaje de cliente ni se
  sugiere enviarlo al grupo de clientes.

---

## 8. Fuera de alcance (YAGNI)

- **Métricas de cuenta MT5 del cliente** (balance, P/L) en el guion: dependen de la Manager API
  del bróker (bloqueante externo del brief). El guion usa solo el contenido de análisis.
- **Envío automático a WhatsApp** (cliente o interno): sigue manual hasta que Evolution API esté
  conectada. Este diseño no cambia ese flujo.
- **Comando único `/ejecutivo [dia]`** y **comandos nuevos `*_eje`**: descartados a favor del flag.
- **Modo ejecutivo en comandos de tarea ad hoc** (`/dato_macro`, `/noticia`, `/apertura`
  invocados sueltos): fuera de alcance; el flag vive en los comandos de día. (Posible extensión
  futura, no ahora.)

---

## 9. Criterios de aceptación

1. `/lunes ejecutivo` (y los otros 6 días con `ejecutivo`) producen, por cada pieza, el mensaje
   de cliente + el guion con sus 4 bloques.
2. Los mismos comandos **sin** argumento producen exactamente la salida actual (sin guion).
3. Al aprobar una pieza en modo ejecutivo, se guardan dos archivos: el del cliente con su tipo
   normal y el guion bajo `guion_<tipo>`, mismo activo/hora.
4. El guion siempre lleva el banner `🔒 INTERNO · NO ENVIAR AL CLIENTE`.
5. El contrato del guion vive en un solo archivo (`_modo_ejecutivo.md`); los 7 comandos lo
   referencian, no lo duplican.
6. El mensaje de cliente conserva todas las reglas de oro (dirección, formato, decimales, hora).
