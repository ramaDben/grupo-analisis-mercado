# Modo ejecutivo — contrato compartido

> Este archivo NO es un comando invocable. Es el contrato único que siguen TODOS
> los comandos que producen un mensaje de cliente reenviable, cuando se invocan
> con el argumento `ejecutivo` (ej. `/lunes ejecutivo`, `/noticia ejecutivo`).
> Define cómo se genera, muestra y guarda el guion de venta privado que acompaña
> a cada pieza. Si cambia el formato del guion, se cambia AQUÍ y se propaga a
> todos los comandos.

## Comandos que aceptan el flag `ejecutivo`
- **7 comandos de día**: `/domingo`, `/lunes`, `/martes`, `/miercoles`,
  `/jueves`, `/viernes_am`, `/viernes_pm`. Generan DOS salidas por CADA pieza del
  paquete.
- **Comandos de tarea (Capa 2)**: `/encuesta`, `/rencuesta`, `/apertura`,
  `/actualizacion`, `/dato_macro`, `/noticia`, `/señal`, `/alerta`, `/concepto`,
  `/pregunta`, `/respuesta`. Generan un guion por cada mensaje de cliente que
  muestren (normalmente uno; `/encuesta` sin activo genera un guion por poll).
- **Comandos de acción (Capa 3)**: `/accion`, `/earnings`.

**No elegibles** (no producen un mensaje de cliente reenviable): `/estado`
(dashboard interno, no envía nada a WhatsApp), `/chart` (genera un PNG, no texto;
cuando se adjunta a otra pieza, esa pieza ya lleva su guion), `/story` (genera
una Story/imagen de marca GI, no un mensaje de texto de cliente — mismo
criterio que `/chart`; issue #109), `/curriculo` (orquestador: su contenido de
cliente sale por los delegados `/rencuesta` o `/concepto`, que ya generan su
propio guion en modo ejecutivo) y `/ventas` (su contenido primario ya es 100%
interno para el equipo de ventas — ES el HUB INTERNO por sí mismo, no un
mensaje de cliente que necesite un guion complementario). Si se invocan con
`ejecutivo`, ignoran el flag.

## Qué activa el modo
El comando detecta `ejecutivo` en sus argumentos. Si está presente, por CADA
pieza/mensaje de cliente genera DOS salidas; si no está, ignora este contrato y
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
   Piezas sin activo protagonista (concepto, pregunta, respuesta, encuesta de la
   semana, earnings, paquete dominical) omiten `-Activo` → el helper guarda en
   `_general/` y `_general/guion_<tipo>/`.

   **Comandos que hoy NO guardan el mensaje de cliente en `data/mensajes/`**
   (`/señal` → registra en `data/historial_senales.json`; `/accion` → no
   persiste): en modo ejecutivo el mensaje de cliente conserva su flujo actual
   (no se fuerza un guardado nuevo) y SOLO el guion se guarda con
   `ruta_mensaje.ps1` bajo `guion_<tipo>` (`guion_señal`, `guion_accion`), con el
   `-Activo` (ticker) y la `-Hora` de esa pieza.

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
