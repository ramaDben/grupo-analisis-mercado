Genera la operativa diaria del miércoles pieza por pieza para aprobación.

## SETUP
1. Determina los activos del día leyendo `config/agenda_semanal.json` y `config/activos.json` según el día de la semana.
2. Los datos técnicos se obtienen via `mcp__market-data__get_asset_levels` en cada pieza.
3. **NOTA MIÉRCOLES**: Si hoy hay publicación de inventarios EIA de petróleo, priorizarlo en la pieza de dato macro.

---

## PIEZA 1 — Apertura de mercado

Ejecuta la lógica de `/apertura` (ver `.claude/commands/apertura.md`):
- Activos sugeridos hoy según `config/agenda_semanal.json` (2 activos el miércoles). El director confirma/cambia/agrega (rotación + override).
- Por CADA activo: pregunta temporalidad (PASO 2) e indicador RSI/ATR/Limpio (PASO 3), llama `get_asset_levels` con el timeframe mapeado (PASO 4) y renderiza el mensaje con la etiqueta de marco temporal neutral (PASO 5).
- Si `get_asset_levels` devuelve `"error"`: muestra `⚠️ [message] — Verificar que MT5 esté abierto.` y omite ese activo (no abortes la apertura).

**→ Por cada activo: ¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo?**

---

## PIEZA 2 — Dato macro del día (con prioridad EIA si corresponde)

Verifica si hoy es miércoles con publicación de inventarios EIA de petróleo (normalmente cada miércoles ~10:30 CLT durante sesión NY).

Obtén el calendario de hoy con `WebSearch` sobre investing.com (Chile, EE.UU., Zona Euro, China; impacto medio y alto), como en el PASO 1 de `/dato_macro`. Convierte las horas a Chile (CLT/CLST).
Si no hay eventos de impacto medio/alto hoy → continuar (sin eventos hoy es esperado).

Lista numerada con los datos del día. Si hay EIA marcarlo con ⛽ al inicio.

Cuando el director elige el dato a desarrollar, genera:
```
📅 *DATO MACRO — [INDICADOR]*
━━━━━━━━━━━━━━━━━━━
¿Qué es?
[Explicación simple en 1-2 líneas]

🕐 Sale hoy a las [Hora CLT]

📊 Qué se espera:
• Anterior: [valor]
• Consenso: [valor esperado]

🎯 Escenarios:
• Si sale mejor → [ACTIVO] *Alcista* 🟢 (impacto inmediato, ~1-2h) | tendencia del día: [sesgo intra-day]
• Si sale peor  → [ACTIVO] *Bajista* 🔴 (impacto inmediato, ~1-2h) | tendencia del día: [sesgo intra-day]
• En línea      → [ACTIVO] *Esperar confirmación* 🟡 → observar nivel [S1/R1] para definir sesgo

👀 Activos a observar: [lista]
━━━━━━━━━━━━━━━━━━━
```

Si los inventarios EIA están en el calendario, generar también este mensaje específico:
```
⛽ *INVENTARIOS EIA — Petróleo*
━━━━━━━━━━━━━━━━━━━
¿Qué mide? Cuánto petróleo tienen almacenado en EE.UU. esta semana.

🕐 Sale hoy a las ~10:30 CLT

📊 Anterior: [X] millones de barriles
• Baja → WTI *Alcista* 🟢 (impacto inmediato, ~1-2h)
• Sube → WTI *Bajista* 🔴 (impacto inmediato, ~1-2h)
• Tendencia del día: depende de la magnitud de la sorpresa y el sesgo técnico 4H

👀 Activo clave: *WTI* (Petróleo)
━━━━━━━━━━━━━━━━━━━
```

**→ Muestra al director. Pregunta: ¿Apruebas? ¿Adjuntar chart (ej: WTI si es EIA)? ¿Enviar al grupo?**

---

## PIEZA 3 — Encuesta de tendencia (miércoles = tendencia AM)

El miércoles la encuesta es de TENDENCIA.

Genera 2 bloques:

**Bloque A — Contexto previo**:
```
🎯 *ANÁLISIS RÁPIDO — [ACTIVO]*
━━━━━━━━━━━━━━━━━━━
[2-3 líneas con precio actual, sesgo, dato clave del día]
━━━━━━━━━━━━━━━━━━━
```

**Bloque B — Encuesta de tendencia**:
```
📊 *ENCUESTA DEL DÍA*
━━━━━━━━━━━━━━━━━━━
¿Cuál creen que será la tendencia del *[activo]* hoy?

📈 Alcista
📉 Bajista
➡️ Lateral

Voten y veamos si acertamos 👇
━━━━━━━━━━━━━━━━━━━
```

**→ Muestra al director ambos bloques. Pregunta: ¿Apruebas? ¿Enviar al grupo?**

---

## REGLAS GENERALES
- Lenguaje cliente: simple, que se entienda en 30 segundos.
- Hora siempre en hora Chile (CLT/CLST).
- Un indicador por aviso (nunca mezclar en el mismo mensaje).
- Si WhatsApp MCP no está disponible: mostrar texto listo para copiar.
- **Dirección explícita**: SIEMPRE usar `*Alcista* 🟢` o `*Bajista* 🔴` en escenarios — nunca "puede subir", "podría bajar", "fuerza compradora" ni "presión vendedora".
- **Temporalidad obligatoria**: cada reacción a dato macro lleva `(impacto inmediato, ~1-2h)` o `(tendencia del día, intra-day)`. Si no hay certeza de dirección: `*Esperar confirmación* 🟡`.
