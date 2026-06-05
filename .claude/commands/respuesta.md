Responde una pregunta o comentario de cliente de forma complaciente y didáctica, lista para WhatsApp.

## PASO 1 — Recibir el input

El director pega la pregunta o comentario del cliente (el texto tal cual lo escribió en el grupo).

- Si el director no incluyó texto, pídeselo: "✍️ Pega la pregunta o comentario del cliente al que quieres responder."
- Si hay contexto útil (la encuesta del día, el concepto de la semana, un dato macro recién enviado), tómalo en cuenta para conectar la respuesta.

## PASO 2 — Generar la respuesta complaciente y didáctica

Redacta una respuesta que sea, ante todo, **cálida y validante**, y a la vez **enseñe algo**. Reglas de tono y contenido:

- **Valida al cliente primero**: reconoce lo bueno de su pregunta, su voto o su razonamiento. Que sienta que participar vale la pena (nunca lo hagas sentir tonto).
- **Lenguaje novato (regla de oro 30s)**: si un cliente sin experiencia no lo entiende en menos de 30 segundos, simplifícalo. Prohibida la jerga técnica sin explicar (nada de "hawkish/dovish", "Fed speaker", etc.); si usas un término, explícalo al vuelo en palabras simples.
- **Enseña conectando con un concepto**: refuerza una idea concreta (tendencia vs. lateralidad, soporte/resistencia, qué mide un indicador…) ligada a lo que el cliente preguntó.
- **Cierra invitando a la acción del día**: si hay encuesta, concepto o contenido vigente, invítalo a aplicar lo aprendido ahí.
- **Español chileno neutro en tuteo** ("tú vas", "fíjate", "cuéntanos"); nunca voseo argentino ("tenés", "sabés").
- **Formato WhatsApp**: `*negrita*` solo en lo clave, emojis con moderación. Sin separadores `━━━` rígidos: este mensaje es conversacional, no un reporte.
- **Siglas (issue #46)**: si mencionas un dato macro, nómbralo en español con la sigla entre paréntesis una sola vez. Si el mensaje queda con alguna sigla sin explicar, agrega una línea breve "🔤" que la aclare en voz novata (fuente: `data/glosario_siglas.json`).

Molde canónico de tono: `data/mensajes/2026-06-03/_general/respuesta/12-47_respuesta.txt`.

## PASO 3 — Aprobación y guardado

Muestra la respuesta al director y pregunta: "¿Apruebas esta respuesta? ¿Algún ajuste?"

Al aprobar:

1. Obtén la hora de Chile con el reloj del sistema (regla canónica de `CLAUDE.md`):
   ```powershell
   $tz = [System.TimeZoneInfo]::FindSystemTimeZoneById('Pacific SA Standard Time')
   $now = [System.TimeZoneInfo]::ConvertTime([DateTime]::UtcNow, [System.TimeZoneInfo]::Utc, $tz)
   $now.ToString('yyyy-MM-dd HH:mm')
   ```
2. Construye la ruta con el helper determinista (sin `-Activo`: la pieza no tiene activo protagonista → cae en `_general/`):
   ```powershell
   scripts\ruta_mensaje.ps1 -Fecha "<yyyy-MM-dd>" -Tipo "respuesta" -Hora "<HH-mm>"
   # -> data/mensajes/<fecha>/_general/respuesta/<HH-mm>_respuesta.txt
   ```
3. Usa la herramienta `Write` sobre la ruta devuelta con el texto final aprobado.
4. Muestra el texto listo para copiar. **Nunca se envía nada al grupo sin aprobación explícita del director.**

## REGLAS

- Sin límite de veces al día.
- SIEMPRE complaciente y didáctica: validar + enseñar, nunca corregir en seco.
- Conectar con contenido real del grupo (encuesta, concepto, dato del día) cuando exista.
- Lenguaje cliente: que el de menos experiencia también se sienta acompañado.
