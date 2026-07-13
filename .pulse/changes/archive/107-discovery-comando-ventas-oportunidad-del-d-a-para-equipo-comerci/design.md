# Diseño técnico — Comando `/ventas`: Oportunidad del Día (#107)

> Formaliza el diseño de los requisitos fijados en `spec.md` (fases explore/propose/specify ya
> cerradas). Fija decisiones de implementación (ADR), el contrato exacto del archivo de comando,
> las plantillas y el historial, la resolución de las Preguntas 1-3 de `spec.md` y el mapeo de
> tareas a `R1..R13` / `AC1..AC8`.
>
> **Dominio Pulse:** comandos · **Bump sugerido:** minor (`type:feat`, comando nuevo, aditivo) ·
> **Gate:** las tres decisiones del gate humano `DESIGN → APPLY` (§5, D-GATE-1/2/3) están
> **pendientes de aprobación del director** — no se invoca `approve_design` hasta confirmarlas.

---

## 1. Contexto y decisión (ADR)

### Estado
Propuesto — pendiente de aprobación del director (D-GATE-1/2/3, §5).

### Contexto
El equipo de ventas interno no tiene un comando propio que traduzca la noticia/evento más
relevante del día en una pieza de venta accionable (ticket mínimo, entrada/TP/SL, temporalidad)
en dos formatos fijos (email + WhatsApp). El pipeline de 23 comandos existente está diseñado para
el cliente final del grupo educativo; `/ventas` llena ese vacío para una audiencia distinta
(comercial interno), reutilizando lógica ya probada de `/señal`, `/alerta` y `/accion` sin
tocarlos.

### Decisión
Un único archivo de comando nuevo, sin código ejecutable nuevo (Python/TS): `.claude/commands/ventas.md`,
más 2 plantillas de texto y 1 archivo de historial JSON, siguiendo exactamente el patrón ya
usado por `señal.md`/`alerta.md`/`guion_ejecutivo.txt`/`historial_senales.json`. No se crea
ningún módulo de código porque el comando es 100% un prompt orquestador de tools MCP ya
existentes (`obtener_calendario_macro`, `get_asset_levels`, `get_symbol_spec`) — mismo patrón que
todos los comandos de Capa 2 del repo.

### Consecuencias
- **Positivas**: cero código nuevo que mantener; reutiliza 100% de la lógica de cálculo CLP/R-R
  y detección de eventos ya validada en `/señal`/`/alerta`; historial propio evita mezclar
  semánticas de negocio (cupo de señales al cliente vs. oportunidades tácticas a ventas).
- **Negativas / límites aceptados**: al no delegar en tiempo de ejecución a `/señal`/`/alerta`
  (decisión ya tomada en `proposal.md` para mantener `/ventas` autónomo), cualquier cambio futuro
  a la lógica de cálculo CLP/R-R deberá replicarse manualmente en ambos comandos si diverge —
  riesgo aceptado, documentado como deuda menor (ver §6).

---

## 2. Contrato exacto de `.claude/commands/ventas.md`

Encabezado (primera línea, como el resto de comandos): descripción de una línea usada por el
listado de skills.

```
Genera la Oportunidad del Día para el equipo de ventas: noticia/evento más relevante del día
traducido en una alternativa de inversión accionable (entrada/TP/SL, ticket mínimo, temporalidad),
en dos formatos (email + WhatsApp). No genera infografías ni envía automáticamente.
```

### PASO 1 — Detectar el evento (implementa R2)
1. Llamar `obtener_calendario_macro` para el día de hoy (hora Chile).
2. Si hay un evento agendado de alto impacto (ya publicado o próximo en las próximas horas),
   usarlo como candidato principal.
3. Complementar con `WebSearch` de breaking news de las últimas ~2h, mismos filtros de prioridad
   que `alerta.md` PASO 1 (texto idéntico, copiado literal para no divergir):
   ```
   1. 🏛️ Bancos centrales: Fed, BCCh, BCE
   2. 📊 Datos macro sorpresivos (>0.3 pts vs consenso)
   3. 🌍 Geopolítica (Oro/WTI)
   4. 💻 Earnings tech fuera de horario normal
   5. ⛽ OPEP+ decisiones inesperadas
   ```
4. Si ninguna fuente entrega un candidato: mostrar `"📊 Sin oportunidad clara hoy."` y **DETENER**
   (no continuar a PASO 2).

### PASO 2 — Activo protagonista (implementa R3)
Determinar el único activo más directamente impactado por el evento de PASO 1. Mostrar al
director: `"🎯 Activo protagonista: [ticker] — [1 línea de por qué]"`.

### PASO 3 — Niveles técnicos (implementa R4)
Llamar `mcp__market-data__get_asset_levels(ticker, timeframe)` directamente (sin pedir
confirmación manual antes de mostrar el borrador — patrón `/accion`). `timeframe` por defecto:
`"1H"` si el evento es de alto impacto agendado (reacción rápida esperada), `"4H"` si es un
evento con inercia mayor (geopolítica, banco central) — mismo criterio de "justificar la
temporalidad por la volatilidad del activo" de `CLAUDE.md`.

### PASO 4 — Cálculo CLP y R/R (implementa R5, R6)
1. TC USD/CLP: `obtener_precio_actual("USD/CLP")` vía MT5; si falla, `WebSearch`.
2. `tamaño_contrato`: intentar `mcp__market-data__get_symbol_spec(ticker).contract_size`; si la
   tool retorna `{"error": ...}` o el campo no viene, usar la fuente histórica (dato manual /
   `config/activos.json`) — mismo fallback pattern que el resto del repo (ver D-GATE-3, §5).
3. `TP_CLP = abs(TP - Entrada) * volumen * TC_USDCLP * tamaño_contrato`
   `SL_CLP = abs(SL - Entrada) * volumen * TC_USDCLP * tamaño_contrato`
   `RR = TP_CLP / SL_CLP`
4. Formatear todo precio según `digits` de `config/activos.json` (R6).
5. Si `RR < 1.5`: mostrar `"⚠️ Ratio R/R bajo ([RR]). Considera ajustar TP o SL."` — no detiene el
   flujo (CB-2).

### PASO 5 — Ticket mínimo y temporalidad (implementa R7)
- Ticket mínimo: siempre `$5.000.000 CLP` (constante, no preguntar al director).
- Temporalidad default:
  - Evento = dato agendado de alto impacto (ya publicado, reacción inmediata esperada) →
    `"Intradía"`.
  - Evento = con inercia de 24-48h (decisión de política monetaria, geopolítica, discurso de
    banco central) → `"24-48 horas"`.
  - Empate/ambiguo → usar `volatilidad`/`nota_volatilidad` de `config/activos.json` como
    desempate (activo de alta volatilidad → sesgo a `"Intradía"`).
- Mostrar el default al director junto con el resto del borrador (no como pregunta aparte —
  se confirma/ajusta en el mismo paso de aprobación de PASO 7).

### PASO 6 — Render de las dos piezas (implementa R8, R10)
Rellenar `templates/ventas_email.txt` y `templates/ventas_whatsapp.txt` (contrato exacto en §3)
con los mismos datos de fondo. Mostrar ambas piezas rotuladas:
```
📧 EMAIL (equipo de ventas)
[contenido]

📱 WHATSAPP (equipo de ventas)
[contenido]
```

### PASO 7 — Aprobación (implementa R11)
```
¿Apruebas la Oportunidad del Día?
¿Ajustar niveles o temporalidad? (si sí, vuelve a PASO 3/PASO 5 con los nuevos valores)
¿Enviar por correo? ¿Enviar por WhatsApp? (informativo — no hay envío automático)
```
Si no aprueba: DETENER, no guardar nada (CB-4).

### PASO 8 — Guardado (implementa R12, R13)
1. Guardar email: `scripts\ruta_mensaje.ps1 -Fecha <hoy> -Activo <ticker> -Tipo "ventas_email" -Hora <HH-mm>`.
2. Guardar WhatsApp: mismo comando con `-Tipo "ventas_whatsapp"`, misma `-Hora`.
3. Agregar entrada a `data/historial_ventas.json` (schema exacto en §4).

### Rechazo del flag `ejecutivo` (implementa R9)
Al inicio del comando (antes de PASO 1), si los argumentos incluyen `ejecutivo`:
```
ℹ️ /ventas no soporta el modo ejecutivo — su contenido ya es 100% interno para el equipo
comercial, no necesita un guion adicional. Continuando con la Oportunidad del Día normal.
```
Continuar con PASO 1 normalmente (no abortar).

---

## 3. Contrato de las plantillas (implementa R10 — resuelve Pregunta 2 de spec.md)

**Decisión de sintaxis de placeholders**: `[Corchetes]`, no `{{mustache}}` — consistente con el
único precedente real de plantilla para audiencia interna (`templates/guion_ejecutivo.txt`) y con
las plantillas literales del propio issue #107, que ya vienen en formato `[Corchetes]`. Se
descarta `{{mustache}}` propuesto en `spec.md` R10 por no tener ningún precedente en `templates/`.

### `templates/ventas_email.txt`
```
Asunto: Oportunidad de Inversión - [Nombre del Activo/Evento] - [Fecha]

Estimado equipo de ventas,

La noticia más relevante de la jornada es [Insertar noticia clave]. Ante este escenario, el departamento de estudios ha detectado una oportunidad táctica con sentido de urgencia para nuestros clientes.

Detalle de la Estrategia:

Activo: [Nombre]
Sentido de la operación: [Compra / Venta]
Nivel de Entrada: $[Precio]
Take Profit: $[Precio]
Stop Loss: $[Precio]
Ticket Mínimo de ingreso: $5.000.000 CLP
Temporalidad sugerida: [ej. Intradía / 24-48 horas]

Esta estrategia debe ser comunicada con prioridad, haciendo énfasis en los niveles técnicos definidos para gestionar el riesgo de manera profesional.

Quedo a disposición por cualquier duda técnica.
```

### `templates/ventas_whatsapp.txt`
```
⚡ OPORTUNIDAD DEL DÍA: [Nombre del Activo] ⚡

Debido a [Breve resumen de la noticia], vemos una oportunidad táctica inmediata:

📈 Operación: [Compra/Venta]
🎯 Entrada: $[Precio]
💰 Take Profit: $[Precio]
🛑 Stop Loss: $[Precio]

🔹 Condición: Ticket mínimo de $5.000.000 CLP.
⏳ Temporalidad: [ej. Operación rápida / intradía]

¡Priorizar comunicación con clientes clave! Consultas técnicas, al equipo de estudios.
```

Ambas son texto literal del issue #107, sin modificar estructura ni emojis — el comando solo
sustituye los `[Placeholders]` por los valores calculados en PASO 1-5. El ticket mínimo queda
como **texto fijo** `$5.000.000 CLP` (no placeholder) en ambas plantillas, consistente con R7
("constante, no varía por corrida").

---

## 4. Modelo de datos — `data/historial_ventas.json`

Archivo nuevo, inicializado como `[]`. Cada entrada (agregada en PASO 8):

```json
{
  "id": "20260713-1732",
  "fecha_hora": "2026-07-13T17:32:00-04:00",
  "activo": "XAUUSD",
  "evento": "Sorpresa al alza en IPC de EE.UU.",
  "sentido_operacion": "COMPRA",
  "entrada": 4539.72,
  "take_profit": 4560.00,
  "stop_loss": 4525.00,
  "ticket_minimo_clp": 5000000,
  "temporalidad": "Intradía",
  "email_generado": true,
  "whatsapp_generado": true
}
```

`id`: `yyyyMMdd-HHmm` (hora Chile), igual de legible que el `id` timestamp de
`historial_senales.json` pero sin colisión de formato entre ambos archivos (son historiales
independientes, R13). Sin límite de cupo — es trazabilidad, no control semanal.

---

## 5. Gate humano `DESIGN → APPLY` — decisiones a confirmar

**D-GATE-1 (Riesgo R-1 de spec.md — registro de tono)**: se diseña con registro directo,
profesional, sin explicar siglas (audiencia comercial interna), manteniendo solo la norma general
anti-dramatización de `CLAUDE.md`. *Recomendación del diseñador: aceptar tal cual — el issue #107
ya trae las plantillas en ese registro y no hay señal de que el equipo de ventas necesite lenguaje
novato.*

**D-GATE-2 (Riesgo R-2 de spec.md — ticket mínimo fijo)**: se diseña como constante única
`$5.000.000 CLP`, no editable por corrida ni por activo. *Recomendación del diseñador: aceptar —
es literalmente lo que pide el issue; variarlo por activo/segmento es una decisión de política
comercial fuera del alcance técnico de este Change, y puede resolverse en un Change de seguimiento
si el negocio lo requiere.*

**D-GATE-3 (Riesgo R-3 de spec.md — `get_symbol_spec` como fuente de `tamaño_contrato`)**: se
diseña con `get_symbol_spec` como fuente preferida y `config/activos.json`/dato manual como
fallback silencioso (mismo patrón de fallback ya usado en todo el repo — MT5 → WebSearch). *No
requiere verificar los 21 activos uno por uno antes de Apply: el fallback ya cubre el caso de que
`get_symbol_spec` no soporte un ticker específico, así que el riesgo queda mitigado por diseño, no
por verificación previa.*

Si el director prefiere una postura distinta en cualquiera de las 3, se ajusta este documento
antes de `approve_design`.

---

## 6. Deuda aceptada (no bloquea Apply)

- Si la lógica de cálculo CLP/R-R de `/señal` cambia en el futuro, `/ventas` no se actualiza
  automáticamente (comandos independientes, sin código compartido) — aceptado en `proposal.md`
  como parte de mantener `/ventas` autónomo y simple.
- `templates/guion_ejecutivo.txt` sigue siendo la única referencia de plantilla "interna"; no se
  generaliza a un helper de rendering compartido — cada comando sigue renderizando su plantilla
  inline, mismo patrón ya establecido.

---

## 7. Mapeo tareas → requisitos (para Break-to-Tasks)

| Tarea | Requisitos (spec.md) | Criterios de aceptación |
|---|---|---|
| Crear `.claude/commands/ventas.md` con PASOS 1-8 + rechazo `ejecutivo` | R1-R9, R11, R12 | AC1, AC3-AC7 |
| Crear `templates/ventas_email.txt` | R10 | AC2 |
| Crear `templates/ventas_whatsapp.txt` | R10 | AC2 |
| Crear `data/historial_ventas.json` (`[]`) | R13 | AC4, AC7 |
| Documentar `/ventas` en `CLAUDE.md` (tabla Capa 2) | Alcance IN | AC8 |
| Agregar `/ventas` a "No elegibles" de `.claude/shared/modo_ejecutivo.md` con razón | R9 | AC8 |
| Verificación end-to-end manual (escenario simulado, camino feliz + CB-1/CB-3/CB-4) | — | AC3-AC7 |

---

## 8. Referencias

- Issue #107 (bbenja11/grupo-analisis-mercado)
- `.pulse/changes/107-.../idea.md`, `proposal.md`, `spec.md`
- `.claude/commands/señal.md`, `alerta.md`, `accion.md`
- `.claude/shared/modo_ejecutivo.md`
- `templates/guion_ejecutivo.txt`
- `scripts/ruta_mensaje.ps1`
- `config/activos.json`
- `data/historial_senales.json`
