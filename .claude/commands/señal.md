Genera una señal operativa para el grupo. Máximo 3 señales por semana (hard limit global).

## PASO 1 — Verificar límite semanal

Lee `data/historial_senales.json` y cuenta las señales con estado "abierta" o "cerrada" de esta semana ISO actual.

Si ya hay 3 señales esta semana:
```
⛔ Límite semanal alcanzado: ya se enviaron 3 señales esta semana.
El límite es 3 por semana. Próxima señal disponible el lunes.
```
**→ DETENER. No continuar.**

Si hay menos de 3:
```
✅ Señales esta semana: [N]/3. Podemos generar [3-N] más.
```

## PASO 2 — Preguntar activo

```
¿En qué activo quieres generar la señal?
- Forex: USD/CLP
- Commodities: Oro (XAU/USD), WTI
- Índices: US100, US500, US30
- Acciones tech: #AAPL, #MSFT, #NVDA, #AMZN
- Acciones bancarias: #JPM, #BAC, #GS, #MS
- Acciones industriales: #BA, #CAT, #GE, #DE
```

## PASO 3 — Preguntar dirección

`¿BUY o SELL?`

## PASO 4 — Preguntar niveles

Solicita al director que defina los niveles:
```
Por favor define los niveles de la señal:
• Entrada: [precio de entrada]
• TP (Take Profit): [precio objetivo]
• SL (Stop Loss): [precio de stop]
• Volumen: [tamaño de lote]
• Acciones: [cantidad de acciones si es acción individual]
```

## PASO 5 — Obtener TC USD/CLP y calcular CLP

Obtén el tipo de cambio USD/CLP actual desde MT5: `obtener_precio_actual("USD/CLP")`.
Calcula:
- `TP_CLP = abs(TP - Entrada) * volumen * TC_USDCLP * [tamaño_contrato]`
- `SL_CLP = abs(SL - Entrada) * volumen * TC_USDCLP * [tamaño_contrato]`
- `RR = TP_CLP / SL_CLP` (ratio Riesgo/Beneficio)

Para acciones: `TP_CLP = (TP - Entrada) * acciones * TC_USDCLP`

Si no puede conectar MT5: usar web search para el precio actual del USD/CLP.

## PASO 6 — Pedir 3 bullets de análisis

```
Por favor provee hasta 3 bullets de análisis para la señal:
• Bullet 1 (técnico): [soporte/resistencia/nivel clave]
• Bullet 2 (fundamental): [driver o catalizador]
• Bullet 3 (contexto): [contexto macro o de sector]
```

También pregunta:
- Temporalidad: 15M / 1H / 4H / 1D
- Tipo operativa: scalper / intradía / swing

## PASO 7 — Validar calidad

Verifica:
- Si `RR < 1.5`: alertar "⚠️ Ratio R/R bajo ([RR]). Considera ajustar TP o SL."
- Si TP muy cercano a entrada (< 0.5% de distancia): alertar sobre riesgo de ejecución.
- Si hay 3 bullets, continuar.

## PASO 8 — Generar la señal completa

Determina el número de señal de la semana (N = señales_esta_semana + 1).

```
🎯 *SEÑAL OPERATIVA — Señal [N] de 3*
━━━━━━━━━━━━━━━━━━━
📊 *[TICKER] · [Nombre completo del activo]*
Sector: [tecnológico/bancario/industrial/forex/commodity/índice]

[🟢 BUY / 🔴 SELL]

💰 *Entrada*: [precio]
📦 Volumen: [volumen] | Acciones: [cantidad]

🎯 *Take Profit*: [precio TP] (+$[TP_CLP] CLP)
🛑 *Stop Loss*: [precio SL] (-$[SL_CLP] CLP)

📐 R/R: [RR]:1

📌 *Análisis*:
• [Bullet 1 técnico]
• [Bullet 2 fundamental]
• [Bullet 3 contexto]

⏱️ Temporalidad: [temp] — Operativa [tipo]
━━━━━━━━━━━━━━━━━━━
_El cliente ve directamente cuánto gana y cuánto pierde en pesos chilenos._
```

## PASO 9 — Aprobación, chart y envío

Muestra la señal al director. Pregunta:
1. "¿Apruebas la señal?"
2. "¿Adjuntar chart de MT5?"
3. "¿Enviar al grupo WhatsApp?"

Si aprueba TODO:
- Llama MCP WhatsApp (con imagen si hay chart).
- Si MCP no disponible: muestra texto + ruta imagen.
- **Registra en `data/historial_senales.json`**:
```json
{
  "id": "[timestamp]",
  "semana_iso": "[año-semana]",
  "ticker": "[ticker]",
  "nombre": "[nombre activo]",
  "direccion": "BUY/SELL",
  "entrada": "[precio]",
  "tp": "[precio]",
  "sl": "[precio]",
  "volumen": "[vol]",
  "estado": "abierta",
  "fecha_hora": "[datetime ISO]"
}
```

## REGLAS
- STOP inmediato si ya hay 3 señales la semana.
- TP y SL SIEMPRE en CLP para el cliente.
- Las señales son complementarias — NO el foco principal del grupo.
- Para acciones: conectar SIEMPRE con el índice relacionado en los bullets.
