Genera un chart/gráfico desde MT5 para adjuntar al grupo de WhatsApp.

## PASO 1 — Preguntar activo

Pregunta al director qué activo quiere graficar. Acepta cualquier formato:
- Forex/commodity: USD/CLP, Oro, XAUUSD, WTI, etc.
- Índices: US100, US500, US30, Nasdaq, S&P, Dow
- Acciones: AAPL, #AAPL, Apple, JPM, BA, etc.

Normaliza al ticker_mt5 consultando config/activos.json.
Si no reconoces el activo, muestra la lista de activos disponibles:
```
Forex: USD/CLP · Oro · WTI
Índices: US100 · US500 · US30
Acciones tech: #AAPL · #MSFT · #NVDA · #AMZN
Acciones bancarias: #JPM · #BAC · #GS · #MS
Acciones industriales: #BA · #CAT · #GE · #DE
```

## PASO 2 — Preguntar indicador

Pregunta qué indicador incluir (regla: UN solo indicador por gráfico):

```
¿Qué indicador quieres en el chart?

1. SMA 50 + SMA 200 (medias móviles — excepción: pueden ir juntas)
2. RSI (sobrecompra/sobreventa)
3. MACD (cruces y momentum)
4. ATR (volatilidad — especialmente útil en USD/CLP)
5. Bollinger Bands
6. Limpio (solo velas y niveles de soporte/resistencia)
7. Otro — especifica cuál
```

## PASO 3 — Preguntar temporalidad

```
¿Qué temporalidad?

1. 15M — scalper / muy rápida
2. 1H — intradía corto
3. 4H — intradía / swing corto (recomendado para apertura)
4. 1D — swing / lectura general
```

## PASO 4 — Generar el chart desde MT5

Escribe el archivo `data/mt5_command.json`:
```json
{
  "action": "screenshot",
  "symbol": "[ticker_mt5]",
  "timeframe": "[15M|1H|4H|1D]",
  "indicators": ["[indicador elegido]"],
  "timestamp": "[datetime actual ISO]"
}
```

Luego:
1. El EA MT5 (GI_ChartExporter) monitorea `data/mt5_command.json`, cambia el símbolo y temporalidad, carga el indicador, espera render, captura screenshot 1920×1080 y guarda el PNG en `data/charts/` con el nombre canónico `<activo_slug>_<TF>_<YYYY-MM-DD_HH-MM>.png` (ver NOTAS).
2. Lee `data/mt5_response.json` para confirmar que el EA generó el archivo.
3. Muestra la ruta del PNG generado al director.

**Si el EA no responde en 10 segundos**: avisa al director que MT5 debe estar abierto con el EA activo y reintenta. _No hay fallback automático de generación de charts (ver #87 — pipeline de charts propio)._

## PASO 5 — Mostrar preview y preguntar envío

Muestra la ruta del PNG y pregunta:
"¿Enviar este chart al grupo de WhatsApp (sin texto adicional)? ¿O usarlo para adjuntar a otro mensaje?"

Si envío standalone: llama MCP WhatsApp con la imagen.
Si MCP no disponible: muestra la ruta para adjuntar manualmente.

## PASO 6 — Encadenar encuesta post-evento (reactivo)

Cuando el chart se envía como actualización de niveles técnicos, ofrecer la encuesta de tendencia/causa-efecto sobre ese activo.

1. Escribir/actualizar `data/ultimo_evento.json` con la actualización de niveles:
```json
{
  "tipo": "niveles",
  "activo": "[ticker_mt5 graficado]",
  "evento": "Actualización de niveles [temporalidad] — [activo]",
  "dato_real": null,
  "dato_esperado": null,
  "timestamp": "[datetime actual ISO]"
}
```
2. Preguntar al director:
   > "📊 Niveles de *[activo]* enviados. ¿Lanzo la encuesta post-evento para que el grupo razone hacia dónde puede ir desde estos niveles? (s/n)"
3. Si responde que sí → ejecutar el flujo de `/encuesta post_evento [activo] "Actualización de niveles [temporalidad]"`. Para niveles, las 3 opciones causa-efecto se construyen sobre el sesgo técnico y las zonas de soporte/resistencia del análisis, no sobre un dato_real/esperado.
4. Si responde que no → terminar sin generar encuesta.

## NOTAS
- **Nombre de archivo — convención única (#81)**: `data/charts/<activo_slug>_<TF>_<YYYY-MM-DD_HH-MM>.png`. El `<activo_slug>` es el mismo de `ruta_mensaje.ps1` (#45): `lowercase(ticker_mt5)` sin `.spot`/`#`/`/` (ej: `usdclp`, `xauusd`, `wti`, `aapl`, `us100`, `copper`). `<TF>` en mayúscula MT5 (`M15`/`H1`/`H4`/`D1`). La fecha-hora sale del reloj de Chile. Ejemplo: `usdclp_H4_2026-06-07_11-45.png`.
- El chart queda guardado en `data/charts/` y puede reutilizarse en otros comandos del día.
- Siempre incluir soportes y resistencias calculados automáticamente con `identificar_niveles()`.
- Un indicador por gráfico (SMA 50+200 es la única excepción permitida).
