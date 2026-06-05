Genera el paquete del domingo pieza por pieza para aprobación.

## Contexto
Hoy es domingo. Los mercados bursátiles están cerrados; el foco es preparar al grupo para la semana. Ejecuta cada pieza en orden, mostrándola al director para aprobación antes de continuar.

Nota de hora: los mercados asiáticos abren el domingo ~22:00 CLT (lunes en Tokio). Obtén la hora actual de Chile con el reloj del sistema (regla canónica de CLAUDE.md, NUNCA con `WebSearch`). Si el director ejecuta este comando antes de las 21:00 CLT, omitir PIEZA 4. Si es después de las 21:30 CLT, incluirla.

---

## PIEZA 1 — Noticias del fin de semana

Busca eventos relevantes ocurridos entre el sábado y hoy domingo que puedan mover nuestros activos al inicio de semana:
- Con `WebSearch` busca noticias del fin de semana (últimas ~48 h) sobre investing.com + fuentes oficiales (Fed, BCCh, OPEP+, EIA), como en el PASO 1 de `/noticia`.
- Si no hay noticias relevantes del fin de semana: usar el mensaje "mercados tranquilos" (ver más abajo).

Filtrar por prioridad:
1. 🏛️ Bancos centrales (declaraciones, discursos)
2. 🌍 Geopolítica (conflictos, sanciones, acuerdos)
3. ⛽ OPEP+ / energía
4. 📊 Datos sorpresivos o revisiones de datos previos
5. 💻 Noticias de empresas tech relevantes

Si no hay noticias de impacto: generar el mensaje de "mercados tranquilos" (ver más abajo).

**Si hay noticias relevantes**, formato WhatsApp:
```
🌐 *NOTICIAS DEL FIN DE SEMANA*
━━━━━━━━━━━━━━━━━━━
📰 Esto pasó mientras los mercados estaban cerrados:

[Noticia 1 — 2 líneas máximo]
→ Afecta: [activo(s)]

[Noticia 2 si aplica]
→ Afecta: [activo(s)]

💡 Lo tenemos en el radar para el lunes.
━━━━━━━━━━━━━━━━━━━
```

**Si no hay noticias relevantes**:
```
🌐 *FIN DE SEMANA SIN SORPRESAS*
━━━━━━━━━━━━━━━━━━━
📰 Fin de semana tranquilo en los mercados.
No hubo eventos de alto impacto.

✅ Los activos llegan al lunes sin grandes novedades externas.
━━━━━━━━━━━━━━━━━━━
```

**→ Muestra al director. Pregunta: ¿Apruebas? ¿Enviar al grupo?**
Al aprobar: guardar con la ruta de `scripts\ruta_mensaje.ps1 -Fecha [FECHA] -Tipo noticia -Hora [HH-MM]` (transversal → `_general`).

---

## PIEZA 2 — Preview de la semana

Obtén el calendario económico de la semana que viene:
- Con `WebSearch` sobre investing.com obtén el calendario de **alto impacto** de la semana que viene (próximos 7 días). Convierte cada hora a Chile con el helper determinista `scripts\hora_chile.ps1` (según la zona de origen del dato; nunca offsets fijos) — ver PASO 1B de `/dato_macro`.
- Si no encuentras eventos de alto impacto → informar y DETENER.

Filtra los 4-6 datos más importantes. Marca con 🔴 los de máximo impacto (NFP, IPC EE.UU., decisiones de tasas). Incluir siempre la hora en CLT.

Formato WhatsApp:
```
📅 *LO QUE VIENE ESTA SEMANA*
━━━━━━━━━━━━━━━━━━━
Los datos que pueden mover el mercado:

📌 *Lunes [fecha]*
🕐 [Hora CLT] — [Dato] ([País])
→ Afecta: [activo]

📌 *Miércoles [fecha]*
🕐 [Hora CLT] — [Dato] ([País])
→ Afecta: [activo]

🔴 *Viernes [fecha] — ALTA VOLATILIDAD*
🕐 [Hora CLT] — NFP / [Dato crítico] (EE.UU.)
→ Afecta: todos los activos

_Horarios en hora Chile (CLT)_
━━━━━━━━━━━━━━━━━━━
```

**→ Muestra al director. Pregunta: ¿Apruebas? ¿Enviar al grupo?**
Al aprobar: guardar con la ruta de `scripts\ruta_mensaje.ps1 -Fecha [FECHA] -Tipo noticia -Hora [HH-MM]` (transversal → `_general`).

---

## PIEZA 3 — Sesgo de entrada al lunes

Basado en los precios de cierre del viernes y las noticias del fin de semana, genera un resumen de cómo llegan los activos principales al lunes. MT5 puede estar cerrado el domingo — usar precios de referencia del viernes via WebSearch.

WebSearch sugerida: "precios cierre viernes [fecha] USD/CLP oro WTI nasdaq".

Cubrir los 4 activos principales. Sesgo: alcista / bajista / lateral + razón en 1 línea.

Formato WhatsApp:
```
📊 *CÓMO LLEGAN LOS ACTIVOS AL LUNES*
━━━━━━━━━━━━━━━━━━━

🇨🇱 *USD/CLP* → [sesgo emoji] [Alcista/Bajista/Lateral]
• Cierre viernes: $[precio]
• Razón: [1 línea simple]

🥇 *Oro (XAU/USD)* → [sesgo emoji]
• Cierre viernes: $[precio]
• Razón: [1 línea simple]

⛽ *WTI (Petróleo)* → [sesgo emoji]
• Cierre viernes: $[precio]
• Razón: [1 línea simple]

📱 *US100 (Nasdaq)* → [sesgo emoji]
• Cierre viernes: [precio]
• Razón: [1 línea simple]

⚠️ _Estos sesgos pueden cambiar con la apertura asiática y los flujos del lunes._
━━━━━━━━━━━━━━━━━━━
```

**→ Muestra al director. Pregunta: ¿Apruebas? ¿Enviar al grupo?**
Al aprobar: guardar con la ruta de `scripts\ruta_mensaje.ps1 -Fecha [FECHA] -Tipo noticia -Hora [HH-MM]` (transversal → `_general`).

---

## PIEZA 4 — Apertura asiática (solo si es después de las 21:30 CLT)

Solo incluir si el director ejecuta el comando después de las 21:30 CLT (mercados de Tokio ya abrieron).

Busca la dirección inicial de los mercados asiáticos vía `WebSearch`: "apertura nikkei hang seng hoy lunes [fecha]".

Formato WhatsApp:
```
🌏 *APERTURA ASIÁTICA — LUNES*
━━━━━━━━━━━━━━━━━━━
🕐 [Hora CLT actual]

🇯🇵 Nikkei 225: [precio/variación%] → [sube/baja]
🇭🇰 Hang Seng: [precio/variación%] → [sube/baja]

[Si hay movimiento relevante:]
📌 Los mercados asiáticos [suben/bajan] impulsados por [razón en 1 línea].
→ Señal [positiva/negativa] para la apertura europea y americana.

[Si movimiento neutro:]
📌 Apertura asiática sin grandes movimientos — mercados en compás de espera.
━━━━━━━━━━━━━━━━━━━
```

**→ Muestra al director. Pregunta: ¿Apruebas? ¿Enviar al grupo?**
Al aprobar: guardar con la ruta de `scripts\ruta_mensaje.ps1 -Fecha [FECHA] -Tipo niveles -Hora [HH-MM]` (transversal → `_general`).

---

## PIEZA 5 — Encuesta de la semana

Genera 2 bloques: contexto previo + encuesta.

**Bloque A — Contexto** (elige el activo más interesante de esta semana según las noticias):
```
🎯 *ACTIVO A SEGUIR ESTA SEMANA*
━━━━━━━━━━━━━━━━━━━
[2-3 líneas sobre el activo más relevante: por qué esta semana tiene catalizadores especiales]
━━━━━━━━━━━━━━━━━━━
```

**Bloque B — Encuesta**:
```
📊 *ENCUESTA DE LA SEMANA*

¿Cuál creen que será el activo con mayor movimiento esta semana?
Voten 👇 — el viernes vemos quién acertó

🇨🇱 USD/CLP
🥇 Oro
⛽ WTI (Petróleo)
📱 US100 (Nasdaq)
```

**→ Muestra al director ambos bloques. Pregunta: ¿Apruebas? ¿Enviar al grupo?**
Al aprobar: guardar con la ruta de `scripts\ruta_mensaje.ps1 -Fecha [FECHA] -Tipo encuesta -Hora [HH-MM]` (transversal → `_general`).

---

## REGLAS GENERALES
- Lenguaje cliente: simple, que se entienda en 30 segundos.
- Hora siempre en hora Chile (CLT/CLST).
- NO usar MT5 (mercados cerrados el domingo).
- NO generar niveles técnicos (sin mercado abierto no hay niveles válidos).
- La PIEZA 4 (apertura asiática) es opcional — incluirla solo después de las 21:30 CLT.
- Al aprobar cada pieza: guardar en `data/mensajes/` (ruta vía `scripts\ruta_mensaje.ps1`, transversal → `_general`) antes de continuar con la siguiente.
- Si WhatsApp MCP disponible: enviar automáticamente tras aprobación. Si no: mostrar texto listo para copiar.
