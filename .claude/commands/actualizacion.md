Genera la Actualización de Mercado (issue #58): informa al cliente sobre la evolución del precio del activo durante la jornada, comparándolo con los niveles enviados en la apertura.

## SETUP
1. Lee `config/activos.json`.

---

## PASO 1 — Selección del activo
Pregunta al director de qué activo quiere generar la actualización hoy.
Normaliza a `ticker_mt5` según `config/activos.json`.

---

## PASO 2 — Obtención de niveles previos
Busca el último archivo de tipo `niveles` para este activo en la carpeta `data/mensajes/` (generalmente dentro de la carpeta con la fecha de hoy).
Extrae automáticamente los niveles (Techos y Suelos) previamente informados.
Si no se encuentra el archivo o no se puede extraer la información, solicita al director que ingrese los niveles previos manualmente.
Muestra los niveles extraídos al director para su confirmación o corrección.

---

## PASO 3 — Precio actual (fetch automático MT5)
Llama **una sola vez**:
```
mcp__market-data__get_asset_levels({"ticker": "[TICKER_MT5]", "timeframe": "H1"})
```
Extrae el campo `price` y formatea según el campo `digits` de `config/activos.json`. Nunca truncar ceros.
Si devuelve `"error"`, solicita al director que ingrese el precio actual manualmente:
`⚠️ No se pudo obtener el precio desde MT5. Ingresa el precio actual manualmente:`

---

## PASO 4 — Análisis y Reacción del Mercado
Muestra al director el precio actual y los niveles previos, y solicita la siguiente información:

1. **Nivel a vigilar ahora** (para el bloque inicial de resumen).
2. **Qué esperar** (1 línea de acción concreta para el bloque inicial).
3. **Reacción del mercado**:
   ```
   📥 Ingresa la explicación de la reacción del mercado:
   (Ejemplo: Por qué rebotó en el soporte o rompió la resistencia. Usa lenguaje para novatos, explicativo en menos de 30 segundos)
   ```
4. **Escenarios de cierre**:
   Condiciones y acciones para los escenarios de la jornada:
   - Alcista 🟢: Condición y acción
   - Esperar 🟡: Condición y acción
   - Bajista 🔴: Condición y acción

---

## PASO 5 — Render del mensaje
Plantilla oficial:

```
🎯 Activo: [NOMBRE ACTIVO]
📌 Nivel a vigilar: [Nivel más relevante ahora]
⚡ Qué esperar: [1 línea de acción concreta]
━━━━━━━━━━━━━━━━━━━

📊 *ACTUALIZACIÓN DE MERCADO — [HH:mm] CLT*
━━━━━━━━━━━━━━━━━━━
📈 *[NOMBRE ACTIVO]*

💰 Precio actual: [precio formateado según digits]
📌 Niveles previos vigentes:
• Techo más próximo: [T1]
• Suelo más próximo: [Su1]
(Añadir T2/Su2 solo si fueron informados previamente y siguen relevantes. Si no, omitir estas líneas)

🔎 Reacción del mercado:
[Análisis didáctico ingresado por el director]

━━━━━━━━━━━━━━━━━━━
🟢 *Alcista* — [Condición] → [Acción]
🟡 *Esperar* — [Condición] → [Acción]
🔴 *Bajista* — [Condición] → [Acción]
━━━━━━━━━━━━━━━━━━━
```

**Reglas de render (OBLIGATORIAS):**
- **Hora**: Usa el reloj del sistema para obtener la hora actual en Chile (CLT/CLST) tal como se indica en CLAUDE.md. El formato de la hora es `HH:mm`.
- **Decimales**: Respeta estrictamente los decimales según `digits` en `config/activos.json` al mostrar el precio actual y los niveles. Nunca truncar ceros.
- **Lenguaje**: Español de Chile, amigable, no hiper-técnico. Uso estricto de viñetas y emojis.

**→ ¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo?**
Al aprobar: construye la ruta con `scripts\ruta_mensaje.ps1 -Fecha [FECHA] -Activo [TICKER_MT5] -Tipo actualizacion -Hora [HH-MM]` y guarda el mensaje usando Write. Muestra el texto listo para copiar.
