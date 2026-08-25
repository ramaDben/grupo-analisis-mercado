Genera la Actualización de Mercado: informa al cliente sobre la evolución del precio del activo durante la jornada, comparándolo con los niveles enviados en la apertura y conectando con el motor de sesgo macro.

## SETUP
1. Lee `config/activos.json`.

---

## PASO 1: Selección del activo
Pregunta al director de qué activo quiere generar la actualización hoy.
Normaliza a `ticker_mt5` según `config/activos.json` (incluyendo USD/JPY, USD/CLP, Oro, Petróleo, US100).

---

## PASO 2: Obtención de niveles previos
Busca el último archivo de tipo `niveles` para este activo en la carpeta `data/mensajes/` (o pídelos al director si no existe).
Muestra los niveles extraídos al director para su confirmación o corrección.

---

## PASO 3: Precio actual (fetch automático MT5)
Llama una sola vez:
```
mcp__market-data__get_asset_levels({"ticker": "[TICKER_MT5]", "timeframe": "H1"})
```
Extrae el campo `price` y formatea según el campo `digits` de `config/activos.json` (USD/JPY: 3 decimales, USD/CLP: 2 decimales). Nunca truncar ceros.

---

## PASO 4: Análisis y Reacción del Mercado
Muestra al director el precio actual y los niveles previos, y solicita:
1. **Nivel a vigilar ahora** (para el bloque inicial de resumen).
2. **Qué esperar** (1 línea de acción concreta).
3. **Reacción del mercado**: análisis didáctico de por qué rebotó o rompió niveles.
4. **Escenarios de cierre**:
   - 🟢 Sobre [Resistencia]: impulso comprador
   - 🟡 Entre [Soporte] y [Resistencia]: zona de espera
   - 🔴 Bajo [Soporte]: confirmación de presión vendedora

---

## PASO 5: Render del mensaje
Plantilla oficial:

```
🎯 Activo: [NOMBRE ACTIVO]
📌 Nivel a vigilar: [Nivel más relevante ahora]
⚡ Qué esperar: [1 línea de acción concreta]
━━━━━━━━━━━━━━━━━━━

📊 *ACTUALIZACIÓN DE MERCADO: [HH:mm] CLT*
━━━━━━━━━━━━━━━━━━━
📈 *[NOMBRE ACTIVO]*

💰 Precio actual: [precio formateado según digits]
📌 Niveles previos vigentes:
• Resistencia más próxima: [R1]
• Soporte más próximo: [S1]
(Añadir R2/S2 solo si fueron informados previamente y siguen relevantes. Si no, omitir)

🔎 Reacción del mercado:
[Análisis didáctico ingresado por el director]

━━━━━━━━━━━━━━━━━━━
🟢 *Alcista*: Sobre [R1] -> [Objetivo / Acción]
🟡 *Esperar*: Entre [S1] y [R1] -> [Zona de consolidación]
🔴 *Bajista*: Bajo [S1] -> [Objetivo / Acción]
━━━━━━━━━━━━━━━━━━━
```

**Reglas de render:**
- **Cero guiones largos**: Prohibido el uso de `—` o `–` en el texto.
- **Decimales**: Respeta estrictamente los decimales según `digits` en `config/activos.json` (USD/JPY con 3 decimales, USD/CLP con 2).
- **Semáforo Canónico de Precios**: 🟢 Sobre (Alcista), 🟡 Entre (Rango), 🔴 Bajo (Bajista).

Al aprobar: construye la ruta con `scripts\ruta_mensaje.ps1 -Fecha [FECHA] -Activo [TICKER_MT5] -Tipo actualizacion -Hora [HH-MM]` y guarda el mensaje. Muestra el texto listo para copiar.
