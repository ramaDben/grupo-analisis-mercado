Genera la operativa diaria del jueves pieza por pieza para aprobación.

## SETUP
1. Determina los activos del día leyendo `config/agenda_semanal.json` y `config/activos.json` según el día de la semana.

> **Orden del flujo**: el dato macro se genera y envía PRIMERO, para que el cliente reciba el fundamental del día mientras se cargan los niveles en MT5 (los niveles requieren input manual y tardan más).

---

## MODO EJECUTIVO
Si el argumento del comando es `ejecutivo` (ej. `/jueves ejecutivo`), activa MODO EJECUTIVO:
por CADA pieza de este paquete, además del mensaje de cliente, genera el guion de venta privado
siguiendo `.claude/commands/_modo_ejecutivo.md` (doble salida, aprobación y guardado `guion_<tipo>`).
Sin ese argumento, ignora esta sección y genera solo el contenido de cliente, como hasta ahora.

---

## PIEZA 1 — Dato macro del día

Obtén el calendario económico de hoy:
- Obtén el calendario de hoy con `WebSearch` sobre investing.com (Chile, EE.UU., Zona Euro, China; impacto medio y alto), como en el PASO 1 de `/dato_macro`. Convierte cada hora a Chile con el helper determinista `scripts\hora_chile.ps1` (según la zona de origen del dato; nunca offsets fijos) — ver PASO 1B de `/dato_macro`.
- Si no hay eventos de impacto medio/alto hoy → continuar.

**NOTA JUEVES**: Los jueves suelen publicarse solicitudes de desempleo semanal (Jobless Claims) de EE.UU. (~9:30 CLT). Si aparece, recomendarlo al director como dato para desarrollar (afecta DXY, USD/CLP, US100, US500).

Lista numerada con los datos del día. Pregunta al director cuál(es) desarrollar.

Al generar el mensaje WhatsApp:
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
• En línea      → [ACTIVO] *Esperar confirmación* 🟡 → observar nivel [suelo/techo] para definir sesgo

👀 Activos a observar: [lista]
━━━━━━━━━━━━━━━━━━━
```

Si el dato ya tiene valor "actual" (ya salió), modo resultado:
```
📊 Salió: [valor] vs Esperado: [valor] → [Sorpresa/En línea]
[Cómo reaccionó el mercado en 1-2 líneas]
[Conexión con camino a decisión de tasas si aplica]
```

**→ Muestra al director. Pregunta: ¿Apruebas? ¿Adjuntar chart? ¿Enviar al grupo?**

---

## PIEZA 2 — Apertura de mercado

Ejecuta `/apertura` (ver `.claude/commands/apertura.md`).

**→ Por cada activo: ¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo?**

---

## PIEZA 3 — Encuesta de tendencia (jueves = tendencia AM)

El jueves la encuesta es de TENDENCIA.

Genera 2 bloques:

**Bloque A — Contexto previo**:
```
🎯 *ANÁLISIS RÁPIDO — [ACTIVO]*
━━━━━━━━━━━━━━━━━━━
[2-3 líneas con precio actual, sesgo, dato clave del día o de la semana]
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
