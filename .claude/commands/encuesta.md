Genera una encuesta para el grupo de WhatsApp.

## Argumentos
$ARGUMENTS — formato esperado: `[tipo] [activo]`
Ejemplos: `tendencia USDCLP` · `precio Oro` · `tendencia AAPL` · `precio US100`

## PASOS

### 1. Parsea los argumentos
- **tipo**: `tendencia` o `precio`
- **activo**: nombre o ticker (USDCLP, Oro, XAU/USD, WTI, US100, US500, US30, #AAPL, AAPL, etc.)

Normaliza el activo para mostrarlo con su nombre legible:
- USDCLP / USD/CLP → "USD/CLP (Dólar)"
- XAUUSD / Oro / XAU/USD → "Oro (XAU/USD)"
- WTI → "WTI (Petróleo)"
- US100 → "Nasdaq 100 (US100)"
- US500 → "S&P 500 (US500)"
- US30 → "Dow Jones (US30)"
- #AAPL / AAPL → "Apple (#AAPL)"
- [resto de acciones análogo]

### 2. Busca contexto previo del activo
Busca con web search qué está pasando HOY con el activo elegido:
- Precio actual / variación del día
- Evento o dato relevante de hoy o reciente
- Sesgo técnico si hay nivel clave cercano

Esto es OBLIGATORIO antes de la encuesta: el cliente debe votar con información, no por intuición.

### 3. Genera 2 bloques consecutivos

**Bloque A — Contexto previo**:

```
🎯 *CONTEXTO — [NOMBRE ACTIVO]*
━━━━━━━━━━━━━━━━━━━
[2-3 líneas con precio actual, movimiento del día, dato o evento relevante, sesgo]
━━━━━━━━━━━━━━━━━━━
```

**Bloque B — Encuesta de tendencia** (si tipo = "tendencia"):
```
📊 *ENCUESTA DEL DÍA*
━━━━━━━━━━━━━━━━━━━
¿Cuál creen que será la tendencia del *[nombre activo]* hoy?

📈 Alcista
📉 Bajista
➡️ Lateral

Voten y veamos si acertamos 👇
━━━━━━━━━━━━━━━━━━━
```

**Bloque B — Encuesta de precio** (si tipo = "precio"):
```
📊 *ENCUESTA DEL DÍA*
━━━━━━━━━━━━━━━━━━━
¿A qué precio crees que abrirá *[nombre activo]* mañana?

💬 Comenta tu precio abajo 👇

(Precio actual: [precio])
━━━━━━━━━━━━━━━━━━━
```

### 4. Muestra al director para aprobación

Pregunta: "¿Apruebas ambos bloques? ¿Adjuntar chart de MT5? ¿Enviar al grupo WhatsApp?"

Si aprueba: llama MCP WhatsApp con ambos bloques.
Si MCP WhatsApp no disponible: muestra el texto listo para copiar.

## REGLAS
- Sin límite de veces al día.
- Siempre el bloque de contexto ANTES de la encuesta.
- Lenguaje simple: el cliente entiende en 30 segundos.
- Hora en hora Chile si mencionas algún horario.
