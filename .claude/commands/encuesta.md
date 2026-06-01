Genera una encuesta para el grupo de WhatsApp.

## Argumentos
$ARGUMENTS — formato esperado: `[tipo] [activo?] [descripcion_evento?]`

Tipos disponibles:
- `tendencia [activo]` — encuesta de tendencia del día (alcista / bajista / lateral)
- `precio [activo]` — encuesta de precio de apertura
- `semanal` — encuesta de la semana con los 4 activos principales
- `post_evento [activo] [descripcion_evento]` — encuesta pedagógica tras noticia macro, reporte flash o niveles técnicos

Ejemplos:
- `tendencia USDCLP`
- `precio Oro`
- `semanal`
- `post_evento USDCLP "IPC USA mayo 3.2% vs esperado 3.0%"`

---

## REGLA GLOBAL DE FORMATO (todos los tipos)

> El bloque de pregunta/contexto va SIEMPRE PRIMERO.
> El call-to-action ("Voten 👇...") va inmediatamente después de la pregunta.
> Las opciones de votación van SIEMPRE AL FINAL.
>
> Límites WA poll nativo: pregunta ≤ 255 caracteres — cada opción ≤ 100 caracteres (incluyendo emoji).

---

## PASO 1 — Parsea los argumentos

**Tipo**: uno de `tendencia`, `precio`, `semanal`, `post_evento`.

**Activo** (para tendencia, precio, post_evento): normalizar con nombre legible:
- USDCLP / USD/CLP → "USD/CLP (Dólar)"
- XAUUSD / Oro / XAU/USD → "Oro (XAU/USD)"
- WTI → "WTI (Petróleo)"
- US100 → "Nasdaq 100 (US100)"
- US500 → "S&P 500 (US500)"
- US30 → "Dow Jones (US30)"
- #AAPL / AAPL → "Apple (#AAPL)"
- [resto de acciones análogo]

---

## PASO 2 — Busca contexto previo (solo para tendencia y precio)

Busca con `mcp__reporte-flash__get_market_news` o web search qué está pasando HOY con el activo:
- Precio actual / variación del día
- Evento o dato relevante de hoy
- Sesgo técnico si hay nivel clave cercano

Esto es OBLIGATORIO: el cliente debe votar con información, no por intuición.

Para `semanal` y `post_evento` el contexto viene dado por el evento o la semana — no hace falta búsqueda adicional.

---

## PASO 3 — Genera los bloques según tipo

### Tipo: `tendencia`

**Bloque A — Contexto previo**:
```
🎯 *CONTEXTO — [NOMBRE ACTIVO]*
━━━━━━━━━━━━━━━━━━━
[2-3 líneas: precio actual, movimiento del día, dato o evento relevante, sesgo]
━━━━━━━━━━━━━━━━━━━
```

**Bloque B — Encuesta**:
```
📊 *ENCUESTA DEL DÍA*

¿Cuál creen que será la tendencia del *[nombre activo]* hoy?
_Lean el análisis de arriba antes de votar_ ☝️

📈 Alcista
📉 Bajista
➡️ Lateral
```

---

### Tipo: `precio`

**Bloque A — Contexto previo** (igual que tendencia):
```
🎯 *CONTEXTO — [NOMBRE ACTIVO]*
━━━━━━━━━━━━━━━━━━━
[2-3 líneas con precio actual, movimiento del día, dato relevante]
━━━━━━━━━━━━━━━━━━━
```

**Bloque B — Encuesta**:
```
📊 *ENCUESTA DEL DÍA*

¿A qué precio crees que abrirá *[nombre activo]* mañana?
Escribe tu estimación abajo 👇

(Precio actual: [precio])
```

---

### Tipo: `semanal`

No requiere búsqueda de contexto. Usar directamente la plantilla `templates/encuesta_semanal.txt`:

**Bloque A — Contexto** (elige el activo con más catalizadores esta semana):
```
🎯 *ACTIVO A SEGUIR ESTA SEMANA*
━━━━━━━━━━━━━━━━━━━
[2-3 líneas sobre el activo más relevante: catalizadores especiales de esta semana]
━━━━━━━━━━━━━━━━━━━
```

**Bloque B — Encuesta semanal**:
```
📊 *ENCUESTA DE LA SEMANA*

¿Cuál creen que será el activo con mayor movimiento esta semana?
Voten 👇 — el viernes vemos quién acertó

🇨🇱 USD/CLP
🥇 Oro
⛽ WTI (Petróleo)
📱 US100 (Nasdaq)
```

---

### Tipo: `post_evento`

Usar la plantilla `templates/encuesta_post_evento.txt`.

El argumento `[descripcion_evento]` describe el dato/noticia que acaba de salir. Si no se especifica, leer `data/ultimo_evento.json` para el evento más reciente (lo escriben automáticamente `/dato_macro`, `/noticia`, `/chart` y `/alerta` al enviar). Nunca usar `data/ultimo_analisis.json` aquí — ese archivo guarda análisis técnico (precio, niveles, indicadores), no eventos.

Generar 3 opciones pedagógicas de causa-efecto en shorthand. Cada opción incluye:
- Letra + dirección del activo
- Flecha (→) con la razón en 1 línea simple

Ejemplo para IPC USA alto + USD/CLP:
- `A) Sube → IPC alto = Fed no baja tasas = USD se fortalece`
- `B) Baja → impacto ya estaba descontado en el precio`
- `C) Lateral → el mercado espera más datos antes de reaccionar`

**Bloque A — Contexto del evento**:
```
📰 *[NOMBRE EVENTO]*
━━━━━━━━━━━━━━━━━━━
[Dato real vs esperado — 1 línea]
[Qué significa para el activo — 1 línea simple]
━━━━━━━━━━━━━━━━━━━
```

**Bloque B — Encuesta post-evento**:
```
📊 *ENCUESTA POST-DATO*

📰 [evento]: [dato_real] (esperado: [dato_esperado])

¿Qué debería pasar con el *[activo]*?
Piensen antes de votar 👇

A) [dirección] → [razón shorthand]
B) [dirección] → [razón shorthand]
C) [dirección] → [razón shorthand]

_Mañana revelamos la respuesta correcta_ 💡
```

Después de generar, guardar en `data/historial_encuestas.json`:
```json
{
  "id": "[YYYY-MM-DD]_post_evento_[TICKER]",
  "fecha": "[YYYY-MM-DD]",
  "tipo": "post_evento",
  "trigger": {
    "tipo": "noticia_macro",
    "evento": "[nombre evento]",
    "dato": "[dato real vs esperado]"
  },
  "activo": "[ticker]",
  "pregunta": "[texto de la pregunta]",
  "opciones": ["A) ...", "B) ...", "C) ..."],
  "estado": "pendiente_revelacion"
}
```

Para revelar la respuesta al día siguiente, usar: `/encuesta revelar [id_encuesta]` — genera un mensaje explicando cuál fue la respuesta correcta y por qué.

---

## PASO 4 — Muestra al director para aprobación

Presenta ambos bloques (contexto + encuesta) al director.

Pregunta: "¿Apruebas ambos bloques? ¿Adjuntar chart de MT5? ¿Enviar al grupo WhatsApp?"

Si aprueba:
- Guardar en `data/mensajes/YYYY-MM-DD_HH-MM_encuesta.txt`
- Si MCP WhatsApp disponible: enviar automáticamente.
- Si no disponible: mostrar texto listo para copiar.

---

## REGLAS
- Sin límite de veces al día (excepto `semanal`: una por semana).
- Siempre el bloque de contexto ANTES del bloque de encuesta.
- Dentro del bloque de encuesta: pregunta+CTA primero, opciones al final.
- Lenguaje simple: el cliente entiende en 30 segundos.
- Hora en hora Chile si mencionas algún horario.
- Cada opción ≤ 100 caracteres con emoji incluido.
