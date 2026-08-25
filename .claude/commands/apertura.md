Genera la Apertura de Mercado de forma interactiva: pregunta activo, temporalidad e indicador por activo. Conecta con el motor cuantitativo de sesgo macro (Playbook V2), toma postura direccional y presenta niveles accionables sin llegar a ser señal formal (sin entrada/TP/SL).

## SETUP
1. Lee `config/agenda_semanal.json` y `config/activos.json`.
2. Consulta `get_macro_bias(ticker)` o lee `data central/DATA DRIVERS USDCLP/macro_bias_output.json` para obtener el **Régimen Macro Global** (R0 a R4), el **Sesgo Score** y los drivers intermercado vigentes.
3. Los niveles (precio, R1, R2, S1, S2) los ingresa el director manualmente. Los indicadores (RSI/ATR/EMA/MACD/Bollinger) se obtienen vía `mcp__market-data__get_asset_levels` solo si aplica.

---

## PASO 1: Activos del día (rotación + override)

Determina los activos rotados de hoy según `config/agenda_semanal.json` (2-3 activos; los viernes 3). Propón al director:

```
Activos sugeridos para hoy: [ACTIVO A] · [ACTIVO B] (· [ACTIVO C])
¿Confirmas, cambias o agregas alguno?
```

El director puede confirmar, reemplazar o agregar (incluyendo USD/JPY si se solicita). Normaliza cada activo a su `ticker_mt5` consultando `config/activos.json`.

---

## PASO 2: Temporalidad por activo

Para CADA activo seleccionado, pregunta:

```
¿Qué temporalidad para [ACTIVO]?
1. 15M: scalper (minutos a 1-2 h)
2. 1H:  intradía (dentro de la jornada)
3. 4H:  swing de jornada (1-3 días)
4. 1D:  posicional (días a semanas)
```

Mapeo a timeframe MT5: 15M->`M15`, 1H->`H1`, 4H->`H4`, 1D->`D1`.

---

## PASO 3: Indicador por activo

Para CADA activo, pregunta:

```
¿Qué indicador en la lectura de [ACTIVO]?
1. RSI:        sobrecompra/sobreventa
2. ATR:        volatilidad del marco
3. EMA 50/100: tendencia por medias móviles
4. MACD:       momentum y cruces
5. Bollinger:  volatilidad y bandas de precio
6. Limpio:     solo niveles, sin indicador
```

---

## PASO 4: Precio, niveles e indicadores por activo

### 4A: Precio actual (fetch automático MT5)

Para CADA activo, llamar una sola vez:
```
mcp__market-data__get_asset_levels({"ticker": "[TICKER_MT5]", "timeframe": "[M15|H1|H4|D1]"})
```

Guardar el resultado completo. Extraer el campo `price` y mostrarlo:
```
💰 Precio actual obtenido desde MT5: [precio formateado según digits]
   ¿Correcto? (Intro para confirmar · escribe un valor para corregir)
```

Formatear siempre según `digits` de `config/activos.json` (ej: USDJPY = 3 decimales, USDCLP = 2 decimales, WTI = 3 decimales).

### 4B: Soportes y resistencias (ingreso manual del director)

Para CADA activo, solicitar los niveles:

```
📥 Ingresa los niveles para [NOMBRE ACTIVO] ([TEMPORALIDAD]):
  Resistencia 1 (R1):
  Resistencia 2 (R2):   (opcional, escribe "-" para omitir)
  Soporte 1 (S1):
  Soporte 2 (S2):       (opcional, escribe "-" para omitir)
```

Reglas de parsing:
- Formatear según el campo `digits` del activo en `config/activos.json`. Nunca truncar ceros.
- Si R2 o S2 se dejan en blanco o contienen `"-"`: omitir esas líneas del mensaje final.

### 4C: Indicador (reutiliza resultado de 4A)
Si el director eligió RSI, ATR, EMA 50/100, MACD o Bollinger en el PASO 3, extraer directamente del payload de MT5 sin hacer un segundo call.

---

## PASO 5: Render del mensaje (por activo)

Genera un mensaje por activo. El mensaje toma postura direccional vía el `🧭 Sesgo del equipo` respaldado por el motor cuantitativo de sesgo macro:

| Temporalidad | Línea `{{lectura_temporalidad}}` |
|---|---|
| 15M | `_Lectura en 15M: marco scalper (minutos a 1-2 h)_` |
| 1H  | `_Lectura en 1H: marco intradía (dentro de la jornada)_` |
| 4H  | `_Lectura en 4H: marco swing de jornada (1-3 días)_` |
| 1D  | `_Lectura en 1D: marco posicional (días a semanas)_` |

Línea `{{por_que_temporalidad}}`:
- Formato: `💡 Por qué [TEMPORALIDAD] aquí: [explicación cliente derivada de nota_volatilidad].`

Plantilla del mensaje:

```
🎯 Activo: [NOMBRE ACTIVO]
📌 Nivel a vigilar: [R1 o S1 según sesgo]
🧭 Sesgo del equipo: *[Alcista / Bajista / Lateral]*
⚡ Qué esperar: [1 línea de acción concreta y direccional]
━━━━━━━━━━━━━━━━━━━

📊 *APERTURA DE MERCADO: [D de mes de YYYY]*
━━━━━━━━━━━━━━━━━━━
📈 *[NOMBRE ACTIVO]*: Niveles en [TEMPORALIDAD]
{{lectura_temporalidad}}
{{por_que_temporalidad}}

💰 Precio actual: [precio]
• Resistencia más próxima: [R1]
• Resistencia siguiente: [R2]
• Soporte más próximo: [S1]
• Soporte siguiente: [S2]
• Zona de interés: [S1] a [R1]
{{canal_tendencia}}
{{lectura_indicador}}

🔎 ¿Qué lo mueve hoy?
[Drivers del activo y régimen macro en 2-3 líneas simples]

━━━━━━━━━━━━━━━━━━━
🟢 *Alcista*: Precio sobre [R1] -> se activa sesgo comprador (intra-day)
🟡 *Esperar*: Entre [S1] y [R1] -> sin confirmación de dirección
🔴 *Bajista*: Precio bajo [S1] -> se activa sesgo vendedor (intra-day)

🧭 *Sesgo del equipo*: *[Alcista / Bajista / Lateral]*: [1 línea: por qué es el escenario de mayor probabilidad hoy según drivers macro]
━━━━━━━━━━━━━━━━━━━
{{lectura_temporalidad}}
```

**Reglas de render:**
- **Fecha** `[D de mes de YYYY]`: hora Chile, formato `2 de junio de 2026`. NUNCA con día de la semana.
- **Cero guiones largos**: Prohibido el uso de `—` o `–` en el texto.
- **Decimales**: Respeta estrictamente `config/activos.json` (USD/JPY con 3 decimales, USD/CLP con 2).
- **Semáforo Canónico**: 🟢 Sobre (Alcista), 🟡 Entre (Rango), 🔴 Bajo (Bajista).

Al aprobar: construye la ruta con `scripts\ruta_mensaje.ps1 -Fecha [FECHA] -Activo [TICKER_MT5] -Tipo niveles -Hora [HH-MM]` y guarda ahí. Muestra el texto listo para copiar.
