Genera un análisis completo de una acción individual para el grupo.

## Argumentos
$ARGUMENTS — ticker de la acción.
Acepta con o sin #: `AAPL` o `#AAPL` · `JPM` · `NVDA` · `Boeing` · `BA`, etc.

## PASO 1 — Identificar ticker y sector

Normaliza el input a formato MT5 (#AAPL, #MSFT, etc.) y busca en `config/activos.json`:
- Nombre completo de la empresa
- Sector (tecnológico, bancario, industrial)
- Índice relacionado (US100 para tech, US30 para bancario/industrial)
- Drivers específicos de la acción

Si el ticker NO está en `config/activos.json`:
```
❌ Ticker no encontrado. Acciones disponibles:

Tecnológico (US100): #AAPL, #MSFT, #NVDA, #AMZN
Bancario (US30): #JPM, #BAC, #GS, #MS
Industrial (US30): #BA, #CAT, #GE, #DE
```

## PASO 2 — Cargar drivers

Lee `config/drivers_indices_sectores.json` para obtener:
- Drivers del sector completo
- Drivers específicos de la acción

## PASO 3 — Análisis técnico

Llama `mcp__reporte-flash__analyze_ticker` con `{"ticker": "#TICKER", "timeframe": "H4"}`:
- Extrae: precio actual, soportes (S1, S2), resistencias (R1, R2), sesgo, RSI, ATR
- Si el MCP no responde: usar web search para precio actual + análisis manual con los drivers de `config/activos.json`

## PASO 4 — Contexto fundamental

Busca información actual de la empresa:
- **Preferencia**: Llama `mcp__reporte-flash__get_market_news` con `{"category": "earnings", "min_hours_old": 48}` y filtra por el ticker. Complementa con `{"category": "general"}` para noticias de sector.
- **Fallback**: Usa web search buscando "[empresa] earnings [año] noticias hoy".

Obtén:
- ¿Hay earnings próximos? (en los próximos 7 días) → si sí, DESTACAR como evento clave
- ¿Earnings recientes? (últimas 2 semanas) → EPS reportado vs esperado
- Noticia más relevante de la empresa hoy
- Estado general del sector

## PASO 5 — Generar mensaje WhatsApp

```
📊 *ANÁLISIS DE ACCIÓN*
━━━━━━━━━━━━━━━━━━━
*#[TICKER] · [Nombre empresa]*
Sector: [tecnológico/bancario/industrial]

💰 *Precio actual*: $[precio]
📈 Niveles en 4H — operativa [intradía/swing]
• Resistencia: $[R1]
• Soporte: $[S1]
• Zona de interés: $[S1] – $[R1]
• Sesgo: [alcista/bajista/lateral]

🔎 *¿Qué la está moviendo?*
[Drivers de la acción en 2-3 líneas simples. Conectar con algo real de hoy.]

[Si hay earnings próximos:]
📅 *⚠️ Earnings en [N] días*
[Fecha hora Chile] (BMO/AMC) | EPS esperado: $[X]
_Los earnings pueden mover fuerte. Alta volatilidad esperada._

[Si hay earnings recientes:]
📅 *Último reporte* ([fecha])
EPS: $[real] vs $[esperado] → [Sorpresa positiva/negativa/en línea]

🔗 *Conexión con el índice*
[Cómo #TICKER afecta o es afectado por US100/US30. 1-2 líneas.]
━━━━━━━━━━━━━━━━━━━
_Temporalidad: 4H — Operativa [tipo]_
```

## PASO 6 — Aprobación, chart y envío

Muestra el mensaje al director. Pregunta:
1. "¿Apruebas?"
2. "¿Adjuntar chart de MT5?"
3. "¿Enviar al grupo WhatsApp?"

Si aprueba: llama MCP WhatsApp (con imagen si hay chart).
Si MCP no disponible: muestra texto listo para copiar + ruta imagen.

## REGLAS
- Lenguaje cliente: explicar qué hace la empresa si el cliente no lo sabe (1 línea).
- SIEMPRE conectar con el índice relacionado.
- Si hay earnings en los próximos 7 días: siempre destacarlos.
- Un indicador por aviso (regla del grupo).
- Puede ejecutarse N veces al día con diferentes acciones.
