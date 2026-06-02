Muestra el calendario de earnings de las 12 acciones del catálogo para la semana actual.

## PASO 1 — Leer las 12 acciones del catálogo

Lee `config/activos.json` sección `acciones` y extrae las 12 acciones:
- Tecnológico (US100): #AAPL, #MSFT, #NVDA, #AMZN
- Bancario (US30): #JPM, #BAC, #GS, #MS
- Industrial (US30): #BA, #CAT, #GE, #DE

## PASO 2 — Obtener calendario de earnings

Busca qué empresas del catálogo reportan esta semana:
- Con `WebSearch` busca el calendario de earnings de las 12 acciones del catálogo para esta semana (investing.com + fuentes oficiales de cada empresa). Confirma día/hora y estimaciones de EPS.
- Si no encuentras earnings de empresas del catálogo: informar que no hay earnings confirmados esta semana.

Por empresa que reporta esta semana, obtén:
- Día y hora Chile (BMO = antes de apertura, AMC = después del cierre)
- EPS esperado por los analistas
- Ingresos esperados
- Foco del mercado (qué métrica mira el mercado este trimestre)

## PASO 3 — Evaluar si hay empresas que reportan

**Si ninguna reporta esta semana**:
```
📊 *EARNINGS DE LA SEMANA*
━━━━━━━━━━━━━━━━━━━
Esta semana no reporta ninguna de nuestras 12 acciones.

📅 Próximo earning relevante:
[Empresa más cercana] — [fecha aproximada]
━━━━━━━━━━━━━━━━━━━
```

**Si hay empresas que reportan**: genera el mensaje completo.

## PASO 4 — Generar mensaje WhatsApp

Ordena por fecha (primero los más cercanos). Destacar con ⭐ las de mayor peso (Nvidia, Apple, Microsoft, JPMorgan):

```
📊 *EARNINGS DE LA SEMANA*
━━━━━━━━━━━━━━━━━━━
💼 Empresas que reportan esta semana:

[Emoji sector] *#[TICKER]* — [Nombre empresa]
📅 [Día] [Hora CLT] ([BMO/AMC])
• EPS esperado: $[X.XX]
• Ingresos esperados: $[X]B
• Foco: [qué mira el mercado este trimestre en 1 línea]
• Afecta: [US100/US30] [sector]

[Repetir por cada empresa]

━━━━━━━━━━━━━━━━━━━
⚠️ _Los earnings pueden generar movimientos bruscos. Precaución con posiciones abiertas._
```

Emojis por sector: 💻 = tecnológico | 🏦 = bancario | 🏭 = industrial

## PASO 5 — Aprobación y envío

Pregunta al director:
1. "¿Apruebas?"
2. "¿Quieres generar análisis detallado de alguna acción? → /accion [TICKER]"
3. "¿Enviar al grupo WhatsApp?"

Si aprueba: llama MCP WhatsApp.
Si MCP no disponible: muestra texto listo para copiar.

## REGLAS
- Cubrir SOLO las 12 acciones del catálogo (no añadir otras).
- Si una empresa reporta BMO: mencionarlo porque afecta la apertura del mercado.
- Siempre conectar el earning con su índice (US100 o US30).
- Destacar las de mayor peso (Nvidia, Apple, Microsoft, JPMorgan) con ⭐.
- También usado automáticamente por /lunes (Pieza 2).
