Genera la operativa de la mañana del viernes pieza por pieza para aprobación.

## SETUP
1. Determina los activos del día leyendo `config/agenda_semanal.json` y `config/activos.json` según el día de la semana.
2. **NOTA VIERNES**: Los viernes cubrir 3 activos (en vez de 2). El primer viernes del mes publicación de NFP (Non-Farm Payrolls) — si es hoy, destacarlo especialmente.

---

## PIEZA 1 — Apertura de mercado (3 activos el viernes)

Ejecuta `/apertura` (ver `.claude/commands/apertura.md`). Nota: hoy son **3 activos** (en vez de 2).

**→ Por cada activo: ¿Apruebas? ¿Adjuntar chart? ¿Enviar al grupo?**

---

## PIEZA 2 — Dato macro del día

Verifica si hoy es el **primer viernes del mes** (= NFP day).

**Si es NFP day**: Genera este mensaje especial ANTES de la lista del calendario:
```
⚠️ *HOY ES DÍA DE NFP*
━━━━━━━━━━━━━━━━━━━
Non-Farm Payrolls — el dato de empleo más importante de EE.UU.

🕐 Sale hoy a las 9:30 CLT

¿Por qué importa?
El NFP mide cuántos trabajos se crearon en EE.UU. el mes pasado.
• Sale fuerte → DXY *Alcista* 🟢 · Oro *Bajista* 🔴 · USD/CLP *Alcista* 🟢 (impacto inmediato, ~1-2h)
• Sale débil  → DXY *Bajista* 🔴 · Oro *Alcista* 🟢 (impacto inmediato, ~1-2h)
• Tendencia del día (intra-day): confirmar con niveles técnicos 4H tras la primera reacción

📊 Anterior: [X]K | Consenso: [Y]K
━━━━━━━━━━━━━━━━━━━
```

**Independientemente**, obtén el calendario completo de hoy:
- Obtén el calendario de hoy con `WebSearch` sobre investing.com (Chile, EE.UU., Zona Euro, China; impacto medio y alto), como en el PASO 1 de `/dato_macro`. Convierte las horas a Chile (CLT/CLST).
- Si no hay eventos de impacto medio/alto hoy → continuar.

Lista numerada. Director elige cuál(es) desarrollar.

Genera el mensaje WhatsApp estándar para el dato elegido:
```
📅 *DATO MACRO — [INDICADOR]*
━━━━━━━━━━━━━━━━━━━
¿Qué es? [1-2 líneas]
🕐 Sale hoy a las [Hora CLT]
📊 Anterior: [X] | Esperado: [Y]
🎯 Escenarios:
• Si sale mejor → [ACTIVO] *Alcista* 🟢 (impacto inmediato, ~1-2h) | tendencia del día: [sesgo intra-day]
• Si sale peor  → [ACTIVO] *Bajista* 🔴 (impacto inmediato, ~1-2h) | tendencia del día: [sesgo intra-day]
• En línea      → [ACTIVO] *Esperar confirmación* 🟡 → observar nivel [suelo/techo] para definir sesgo
👀 Activos a observar: [lista]
━━━━━━━━━━━━━━━━━━━
```

**→ ¿Apruebas? ¿Adjuntar chart? ¿Enviar al grupo?**

---

## PIEZA 3 — Encuesta de precio de apertura del lunes

El viernes la encuesta pregunta por el precio de APERTURA DEL LUNES.

Genera 2 bloques:

**Bloque A — Contexto previo** (¿qué dejó la semana para el lunes?):
```
🎯 *CIERRE DE SEMANA — [ACTIVO]*
━━━━━━━━━━━━━━━━━━━
[2-3 líneas: qué pasó esta semana con el activo, dato clave del viernes, qué viene el lunes]
━━━━━━━━━━━━━━━━━━━
```

**Bloque B — Encuesta de precio apertura lunes**:
```
📊 *ENCUESTA DE CIERRE*
━━━━━━━━━━━━━━━━━━━
¿A qué precio crees que abrirá *[activo]* el lunes?

💬 Comenta tu precio abajo 👇

(Precio actual del viernes: [precio])
━━━━━━━━━━━━━━━━━━━
```

**→ ¿Apruebas? ¿Enviar al grupo?**

---

## REGLAS GENERALES
- Lenguaje cliente: simple, que se entienda en 30 segundos.
- Hora siempre en hora Chile (CLT/CLST).
- Un indicador por aviso.
- Los viernes 3 activos (no 2).
- Si WhatsApp MCP no está disponible: mostrar texto listo para copiar.
- **Dirección explícita**: SIEMPRE usar `*Alcista* 🟢` o `*Bajista* 🔴` en escenarios — nunca "puede subir", "podría bajar", "fuerza compradora" ni "presión vendedora".
- **Temporalidad obligatoria**: cada reacción a dato macro lleva `(impacto inmediato, ~1-2h)` o `(tendencia del día, intra-day)`. Si no hay certeza de dirección: `*Esperar confirmación* 🟡`.
