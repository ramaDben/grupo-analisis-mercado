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
- Coincide → usar `activos_hoy`, **excluyendo** al protagonista.
- No coincide o el archivo no existe → **inferir los activos de las carpetas de `data/mensajes/[FECHA]/`** (cada subcarpeta es un `activo_slug` de una pieza enviada hoy; `_general` no cuenta). Es determinista y refleja lo que realmente se cubrió en la jornada. Avisar al director qué se infirió:
  ```
  ⚠️ `plan_hoy.json` está desfasado (fecha: [fecha del archivo], hoy: [FECHA]).
  Infiero los activos de hoy desde `data/mensajes/[FECHA]/`: [lista].
  ```
  Solo si `data/mensajes/[FECHA]/` tampoco tiene carpetas de activo, pedir los activos manualmente. Nunca usar los activos viejos de `plan_hoy.json`.

Por cada uno, llamar `get_asset_levels` con `timeframe: "H1"`. Si una llamada falla, pedir ese valor manual y seguir con el resto — una fila caída no aborta la tabla.

## PASO 5 — Rendición de cuentas

Listar el contenido de `data/mensajes/[FECHA]/` (todas las carpetas de activo y tipo). Por cada pieza enviada hoy, extraer qué se afirmó y contrastarlo con el resultado real (`actual` del calendario o el precio actual del activo).

- **Hubo al menos una pieza** → armar `{{bloque_rendicion}}` con tres líneas: `Dijimos (HH:MM): …`, `Pasó: …` (con ✅ si se cumplió, ⚠️ si no), y `Cómo contarlo: …`.
- **No hubo ninguna pieza hoy** → **omitir el bloque completo**, incluyendo su encabezado `📋 *Qué dijimos vs. qué pasó*` y el separador que lo precede. No rellenar con texto vacío ni con "sin novedades".

## PASO 6 — Redactar el parte

Rellenar `templates/parte_postventa.txt`. Reglas de redacción por bloque:

- **Bloque 1 (consulta anticipada)**: UNA sola pregunta, la más probable dado el evento. La consulta más su respuesta deben caber en **102 caracteres sumados** — el encabezado (título con fecha y hora, banner y rótulo) consume 98 de los ~200 visibles de WhatsApp antes del "leer más". Si no alcanza, priorizar la respuesta sobre el detalle de la pregunta.
- **Bloque 2 (preguntas frecuentes)**: exactamente 3 preguntas distintas de la del bloque 1. Cada respuesta va **redactada en la voz del ejecutivo, lista para copiar y adaptar** — nunca un bullet de tema. Incluir niveles reales cuando la respuesta lo pida.
- **Bloque 3 (a quién contactar)**: 2 a 4 líneas, cada una con el formato `• [segmento] → [excusa de contacto y qué decir]`. Usar SOLO las cinco etiquetas del catálogo: con exposición al activo protagonista · dormido (2+ semanas) · novato en formación · operador frecuente · con la posición en contra.
- **Bloque 4 (posición abierta)**: escenario vigente con dirección explícita (alcista/bajista/lateral), el nivel exacto que lo invalida, y una línea de riesgo apoyada en el ATR (ej. "el rango típico por hora es de ~X"). Prohibido prometer dirección.
- **Bloque 5 (otros activos)**: una línea por activo, formato `• [Nombre] [valor], [estado] → [qué decir]`.
- **Bloque 6 (rendición)**: según PASO 5.
- **Bloque 7 (no se promete)**: 2 a 4 límites concretos del día, atados al evento próximo detectado en el PASO 2.

Todo precio con los `digits` de `config/activos.json`.

## PASO 7 — Aprobación

Antes de mostrar nada, verificar que el parte conserve la línea `🔒 INTERNO · NO ENVIAR AL CLIENTE` en la segunda línea, tal como viene de la plantilla. Si se perdió al rellenar, restaurarla: es el guardrail que impide que la pieza se confunda con un mensaje de cliente.

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
