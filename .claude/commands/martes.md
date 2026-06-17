Genera la operativa diaria del martes pieza por pieza para aprobación.

## SETUP
1. Determina los activos del día leyendo `config/agenda_semanal.json` y `config/activos.json` según el día de la semana.

> **Orden del flujo**: el dato macro se genera y envía PRIMERO, para que el cliente reciba el fundamental del día mientras se cargan los niveles en MT5 (los niveles requieren input manual y tardan más).

---

## MODO EJECUTIVO
Si el argumento del comando es `ejecutivo` (ej. `/martes ejecutivo`), activa MODO EJECUTIVO:
por CADA pieza de este paquete, además del mensaje de cliente, genera el guion de venta privado
siguiendo `.claude/commands/_modo_ejecutivo.md` (doble salida, aprobación y guardado `guion_<tipo>`).
Sin ese argumento, ignora esta sección y genera solo el contenido de cliente, como hasta ahora.

---

## PIEZA 1 — Dato macro del día

Ejecuta la lógica de /dato_macro:
- Obtén el calendario de hoy con `WebSearch` sobre investing.com (Chile, EE.UU., Zona Euro, China; impacto medio y alto), como en el PASO 1 de `/dato_macro`. Convierte cada hora a Chile con el helper determinista `scripts\hora_chile.ps1` (según la zona de origen del dato; nunca offsets fijos) — ver PASO 1B de `/dato_macro`.
- Si no hay eventos de impacto medio/alto hoy → continuar (domingo/feriado es esperado).

Lista numerada con los datos del día:
```
1. 🔴 [Hora CLT] — [Indicador] ([País], ★★★) | Prev: X | Esp: Y
2. 🟡 [Hora CLT] — [Indicador] ([País], ★★) | Prev: X | Esp: Y
...
```

Pregunta al director: "¿Cuál(es) quieres desarrollar? (escribe el número o números separados por coma)"

Cuando el director elige, genera el mensaje WhatsApp:
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

Si el dato ya salió (tiene valor "actual"), usar modo resultado:
```
📊 Salió: [valor actual] vs Esperado: [valor] → [Sorpresa positiva/negativa/en línea]
[Cómo reaccionó el mercado en 1-2 líneas]
```

**→ Muestra al director. Pregunta: ¿Apruebas? ¿Adjuntar chart? ¿Enviar al grupo?**

---

## PIEZA 2 — Apertura de mercado

Ejecuta `/apertura` (ver `.claude/commands/apertura.md`).

**→ Por cada activo: ¿Apruebas? ¿Adjuntar chart de MT5? ¿Enviar al grupo?**

---

## PIEZA 3 — Encuesta de precio de apertura (martes = precio)

El martes la encuesta es de PRECIO, no tendencia.

Genera 2 bloques consecutivos:

**Bloque A — Contexto previo**:
```
🎯 *CONTEXTO — [ACTIVO]*
━━━━━━━━━━━━━━━━━━━
[2-3 líneas con precio actual, sesgo, evento relevante del día]
━━━━━━━━━━━━━━━━━━━
```

**Bloque B — Encuesta de precio**:
```
📊 *ENCUESTA DEL DÍA*
━━━━━━━━━━━━━━━━━━━
¿A qué precio crees que abrirá *[activo]* mañana?

💬 Comenta tu precio abajo 👇

(Precio actual: [precio])
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
