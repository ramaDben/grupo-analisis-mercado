# Spec — Comando `/ventas`: Oportunidad del Día para equipo comercial (#107)

> Formaliza `idea.md` y `proposal.md` (fases explore/propose ya aprobadas). Esta spec fija el
> comportamiento observable del nuevo slash command `/ventas`, sus dos plantillas de salida y su
> historial propio. No decide implementación interna de detalle (redacción exacta de prompts
> internos del comando, orden fino de los pasos dentro del PASO 1): esas decisiones quedan para
> `design.md`.

## Objetivo

Dar al equipo de ventas interno un flujo propio, `/ventas`, que convierta la noticia/evento de
mercado más relevante del día en una "Oportunidad del Día" — con ticket mínimo, niveles de
entrada/TP/SL y temporalidad — lista para usar en dos formatos (email formal + WhatsApp urgente),
sin generar infografías y sin envío automático (issue #107).

## Alcance

### IN
- Nuevo archivo `.claude/commands/ventas.md` (Capa 2), invocable con `/ventas`, siguiendo la
  estructura de PASOS de los comandos existentes (`.claude/commands/señal.md`, `alerta.md`).
- Dos plantillas nuevas: `templates/ventas_email.txt`, `templates/ventas_whatsapp.txt`, calcadas
  literalmente de las plantillas fijadas en el issue #107.
- Archivo nuevo `data/historial_ventas.json` (historial propio, independiente de
  `data/historial_senales.json`), inicializado como `[]`.
- Actualización de `CLAUDE.md`: nueva fila en la tabla de Capa 2 (`## Slash Commands disponibles`)
  documentando `/ventas`.
- Actualización de `.claude/shared/modo_ejecutivo.md`: agregar `/ventas` a la lista de comandos
  **no elegibles** para el flag `ejecutivo`, con la razón ("su contenido primario ya es 100%
  interno — es el HUB INTERNO por sí mismo, no un mensaje de cliente que necesite un guion
  complementario").
- Reutilización (sin refactor) de la lógica ya existente en el repo: detección de evento
  (`obtener_calendario_macro` + `WebSearch`, patrón `/alerta`), niveles técnicos
  (`mcp__market-data__get_asset_levels`, patrón `/accion`), cálculo CLP/R-R (patrón `/señal`
  PASO 5), regla de `digits` (`config/activos.json`), guardado vía `scripts/ruta_mensaje.ps1`
  (sin cambios de código en el script — `-Tipo` ya es un parámetro libre).

### OUT (explícitamente diferido)
- Generación de infografías (issue #107: la entrega y conecta otro equipo).
- Envío automático a canales de ventas (email o WhatsApp) — el comando entrega texto listo para
  copiar, igual que el resto del pipeline hasta que Evolution API esté conectada.
- Soporte del flag `ejecutivo` (`.claude/shared/modo_ejecutivo.md`) — ver decisión Pregunta 2 de
  `proposal.md`.
- Cambios de código en `scripts/ruta_mensaje.ps1` (el enum de `Tipo` es documental, no validado
  en código).
- Cualquier integración con `data/historial_senales.json` o el límite de 3 señales/semana.
- Un mecanismo determinista de "relevancia" del evento más allá de reutilizar los filtros de
  prioridad ya vigentes en `/alerta` — no se inventa un scoring nuevo en este Change.

## Requisitos funcionales

### R1 — Registro e invocación del comando
`.claude/commands/ventas.md` existe y sigue el mismo formato de encabezado + `## PASO N` que
`señal.md`/`alerta.md`/`accion.md`. Acepta el argumento opcional `ejecutivo`, que el comando debe
**rechazar explícitamente** (ver R9) en vez de ignorarlo silenciosamente.

### R2 — Detección del evento (PASO 1)
1. Consulta `obtener_calendario_macro` para eventos agendados de hoy. Si existe un evento de alto
   impacto ya publicado o próximo en las próximas horas, es candidato prioritario.
2. Complementa con `WebSearch` de breaking news de las últimas ~2 horas, con el mismo orden de
   filtros de prioridad que `alerta.md` PASO 1 (bancos centrales → datos macro sorpresivos >0.3pts
   → geopolítica → earnings tech → OPEP+).
3. Si ninguna fuente entrega un evento con relevancia suficiente, el comando informa
   `"Sin oportunidad clara hoy"` y **DETIENE** — mismo guardrail que `alerta.md` PASO 2. Nunca
   fuerza una oportunidad artificial.

### R3 — Activo protagonista (PASO 2)
El comando identifica exactamente **1 activo** como protagonista de la oportunidad (el más
directamente impactado por el evento detectado en R2). Es un campo obligatorio en toda la salida
— nunca se genera una "Oportunidad del Día" sin activo asociado.

### R4 — Niveles técnicos (PASO 3)
Obtiene `price, s1, s2, r1, r2, rsi_14, atr_14, trend` vía
`mcp__market-data__get_asset_levels(ticker, timeframe)` de forma **directa, sin paso de
confirmación manual previo** (patrón `.claude/commands/accion.md`, no el patrón de ingreso manual
de `/apertura`). El director puede ajustar los niveles propuestos en el paso de aprobación (R11).

### R5 — Cálculo de CLP y R/R (PASO 4)
Mismo mecanismo que `señal.md` PASO 5:
- Obtiene TC USD/CLP desde MT5 (`obtener_precio_actual("USD/CLP")`, fallback WebSearch si MT5 no
  conecta).
- `TP_CLP = abs(TP - Entrada) * volumen * TC_USDCLP * tamaño_contrato`
- `SL_CLP = abs(SL - Entrada) * volumen * TC_USDCLP * tamaño_contrato`
- `RR = TP_CLP / SL_CLP`
- El `tamaño_contrato` se obtiene preferentemente de `mcp__market-data__get_symbol_spec` (campo
  `contract_size`); si la tool no está disponible o el ticker no la soporta, cae a la fuente
  histórica (dato manual/`config/activos.json`), igual que hoy hace `/señal`.
- Si `RR < 1.5`: alertar `"⚠️ Ratio R/R bajo ([RR]). Considera ajustar TP o SL."` — mismo umbral
  que `señal.md` PASO 7. Esto **no detiene** el comando (a diferencia de R2); es una advertencia
  informativa en el paso de aprobación.

### R6 — Formateo de precios (transversal)
Todo precio mostrado (entrada, TP, SL, soportes/resistencias) respeta los decimales `digits` de
`config/activos.json` para ese activo — misma regla MT5 transversal del resto del repo
(`CLAUDE.md`, sección "Formato de precios").

### R7 — Ticket mínimo y temporalidad (PASO 5)
- **Ticket mínimo**: constante fija `$5.000.000 CLP` en las dos plantillas, en todas las
  corridas — no varía por activo ni por corrida.
- **Temporalidad**: el comando propone un default calculado a partir de (a) la `volatilidad` /
  `nota_volatilidad` del activo en `config/activos.json` y (b) la naturaleza del evento detectado
  en R2 (dato agendado de alto impacto → `"Intradía"`; evento con inercia de 24-48h, como
  decisión de política monetaria o geopolítica → `"24-48 horas"`). El director confirma o ajusta
  este default en el paso de aprobación (R11) — igual que `señal.md` PASO 6 pregunta
  temporalidad/tipo operativa.

### R8 — Render de las dos piezas obligatorias (PASO 6)
El comando genera **siempre ambas** piezas por corrida (nunca solo una):
1. Email formal, usando `templates/ventas_email.txt` (ver R10).
2. WhatsApp urgente, usando `templates/ventas_whatsapp.txt` (ver R10).

Ambas comparten los mismos datos de fondo (activo, evento, dirección, entrada/TP/SL en precio y
CLP, ticket mínimo, temporalidad) — sin discrepancias entre sí.

### R9 — Rechazo explícito del flag `ejecutivo`
Si el comando se invoca como `/ventas ejecutivo`, responde indicando que `/ventas` no soporta el
flag `ejecutivo` porque su contenido primario ya es 100% interno (no requiere un guion
complementario), y continúa generando la Oportunidad del Día normalmente (el flag se ignora tras
avisar, no aborta el comando).

### R10 — Contrato de las plantillas nuevas
`templates/ventas_email.txt` y `templates/ventas_whatsapp.txt` reproducen **literalmente** el
texto fijado en el issue #107 (asunto, saludo, bloque "Detalle de la Estrategia", cierre para el
email; encabezado ⚡, bloque de datos con emojis, cierre para WhatsApp), con placeholders
consistentes con el resto de `templates/*.txt` (ej. `{{activo}}`, `{{fecha}}`, `{{entrada}}`,
`{{take_profit}}`, `{{stop_loss}}`, `{{temporalidad}}`, `{{noticia_clave}}`,
`{{sentido_operacion}}`). El ticket mínimo puede ir como texto fijo o placeholder con default
`$5.000.000 CLP` — a decidir en Design (no cambia el contrato observable para el director).

### R11 — Aprobación manual (PASO 7)
Antes de cualquier guardado, el comando pregunta al director:
1. "¿Apruebas la Oportunidad del Día?"
2. "¿Ajustar niveles o temporalidad?" (si el director pide ajuste, vuelve a R4/R7 con los nuevos
   valores antes de continuar)
3. "¿Enviar por correo?" / "¿Enviar por WhatsApp?" (informativo — no dispara envío automático,
   ver Alcance/OUT)

Sin aprobación explícita, el comando no guarda nada (mismo principio de `CLAUDE.md`: "Nunca se
envía nada al grupo sin aprobación explícita del director").

### R12 — Guardado (PASO 8)
Tras aprobar, guarda **ambas** piezas con `scripts/ruta_mensaje.ps1`, dos tipos nuevos
documentados en `CLAUDE.md` (`ventas_email`, `ventas_whatsapp`), con `-Activo` siempre presente
(nunca `_general` — R3 ya obliga un activo protagonista) y la misma `-Hora` para ambas piezas de
la misma corrida.

### R13 — Registro en historial propio
Tras aprobar, agrega una entrada a `data/historial_ventas.json` con, como mínimo:

```json
{
  "id": "[timestamp]",
  "fecha_hora": "[datetime ISO, hora Chile]",
  "activo": "[ticker]",
  "evento": "[1 frase de la noticia/evento detectado]",
  "sentido_operacion": "COMPRA/VENTA",
  "entrada": "[precio]",
  "take_profit": "[precio]",
  "stop_loss": "[precio]",
  "ticket_minimo_clp": 5000000,
  "temporalidad": "[texto confirmado por el director]",
  "email_generado": true,
  "whatsapp_generado": true
}
```

No hay límite semanal sobre este historial (a diferencia de `historial_senales.json`) — es un
registro de trazabilidad, no un control de cupo.

## Requisitos no funcionales

### RNF1 — Consistencia de tono
El registro de las dos piezas es directo y profesional, dirigido a una audiencia comercial
interna — no aplica la regla de "lenguaje novato explicado" del cliente final, pero sí se
mantiene la norma general de `CLAUDE.md` de evitar dramatización catastrófica (ver Pregunta 7 de
`proposal.md`).

### RNF2 — No rompe comandos existentes
`/ventas` es aditivo: no modifica `señal.md`, `alerta.md`, `accion.md`, `dato_macro.md` ni
`scripts/ruta_mensaje.ps1`. Solo se documenta (no se valida en código) el nuevo enum de `Tipo`.

### RNF3 — Idioma
Todo el contenido del comando, plantillas y mensajes de guardrail en español, consistente con el
resto del repo.

### RNF4 — Formato de precios consistente
Ver R6 — ningún precio se muestra sin respetar `digits` de `config/activos.json`.

## Casos borde

- **CB-1 (sin evento relevante)**: no hay ningún dato agendado de alto impacto ni breaking news
  en las últimas 2h → el comando informa `"Sin oportunidad clara hoy"` y se detiene (R2).
- **CB-2 (RR bajo)**: `RR < 1.5` → se muestra la advertencia pero el comando continúa hasta la
  aprobación (R5) — no es un guardrail duro como CB-1.
- **CB-3 (flag `ejecutivo` presente)**: `/ventas ejecutivo` → se avisa que no aplica y se
  continúa igual (R9), nunca se genera un guion ejecutivo adicional.
- **CB-4 (director rechaza la aprobación)**: el director responde que no aprueba → no se guarda
  nada en `data/historial_ventas.json` ni en `data/mensajes/` (R11).
- **CB-5 (director pide ajustar niveles/temporalidad)**: se recalculan R4/R7 con los nuevos
  valores provistos por el director antes de re-presentar para aprobación.
- **CB-6 (MT5 no disponible para TC USD/CLP o niveles)**: cae a `WebSearch` como fallback, mismo
  patrón que `señal.md` PASO 5 y el resto del repo.
- **CB-7 (`get_symbol_spec` no cubre el ticket)**: cae a la fuente histórica de `tamaño_contrato`
  (dato manual/`config/activos.json`), sin bloquear el comando (R5).

## Criterios de aceptación

`.claude/commands/ventas.md` es un prompt de instrucciones para Claude Code (no código
ejecutable con pytest), por lo que los criterios de aceptación se verifican por **inspección
estructural del archivo** y por **ejecución manual guiada** del comando contra un escenario de
ejemplo — mismo criterio usado para el resto de comandos del repo.

**AC1 — estructura del comando (estructural)**
DADO el repo tras aplicar el Change,
CUANDO se inspecciona `.claude/commands/ventas.md`,
ENTONCES contiene, en orden, pasos equivalentes a R2 (detección), R3 (activo), R4 (niveles), R5
(CLP/RR), R7 (ticket/temporalidad), R8 (render dos piezas), R11 (aprobación) y R12 (guardado); y
menciona explícitamente que NO genera infografías ni envía automáticamente.

**AC2 — plantillas literales (estructural)**
DADO `templates/ventas_email.txt` y `templates/ventas_whatsapp.txt`,
CUANDO se comparan contra el texto del issue #107,
ENTONCES conservan el asunto, los bloques y el orden literal de ambas plantillas, solo con
placeholders en los campos variables.

**AC3 — sin evento relevante (ejecución guiada)**
DADO un escenario simulado sin datos agendados de alto impacto ni breaking news reciente,
CUANDO se ejecuta `/ventas`,
ENTONCES el comando responde `"Sin oportunidad clara hoy"` y no produce ninguna pieza ni
guardado.

**AC4 — camino feliz (ejecución guiada)**
DADO un escenario simulado con un evento de alto impacto (ej. sorpresa de IPC) y un activo con
niveles técnicos disponibles vía `get_asset_levels`,
CUANDO se ejecuta `/ventas` y el director aprueba sin ajustes,
ENTONCES se generan ambas piezas (email + WhatsApp) con el mismo activo/evento/niveles, el
ticket mínimo `$5.000.000 CLP` en ambas, precios formateados según `digits`, y se guardan dos
archivos (`ventas_email`, `ventas_whatsapp`) vía `ruta_mensaje.ps1` más una entrada en
`data/historial_ventas.json`.

**AC5 — flag `ejecutivo` rechazado (ejecución guiada)**
CUANDO se ejecuta `/ventas ejecutivo`,
ENTONCES el comando avisa que el flag no aplica y genera la Oportunidad del Día normal, sin
producir ningún guion ejecutivo adicional.

**AC6 — RR bajo no bloquea (ejecución guiada)**
DADO un escenario con `RR < 1.5`,
CUANDO se ejecuta `/ventas`,
ENTONCES se muestra la advertencia de RR bajo pero el flujo continúa hasta el paso de aprobación.

**AC7 — rechazo de aprobación (ejecución guiada)**
CUANDO el director responde que no aprueba la Oportunidad del Día,
ENTONCES no se crea ninguna entrada nueva en `data/historial_ventas.json` ni ningún archivo en
`data/mensajes/`.

**AC8 — documentación actualizada (estructural)**
DADO el repo tras aplicar el Change,
CUANDO se inspecciona `CLAUDE.md` y `.claude/shared/modo_ejecutivo.md`,
ENTONCES `/ventas` aparece documentado en la tabla de Capa 2 de `CLAUDE.md`, y aparece en la
lista de "No elegibles" de `modo_ejecutivo.md` con su razón.

## Riesgos

- **R-1 (registro de tono sin confirmar)**: la Pregunta 7 de `proposal.md` (registro directo sin
  explicar siglas) se toma como default razonable pero el propio issue #107 la deja
  explícitamente abierta. Recomendado confirmar con el director en el gate `DESIGN` antes de
  Apply — no bloquea Specify.
- **R-2 (ticket mínimo fijo vs. variable)**: la Pregunta 6 de `proposal.md` fija $5.000.000 CLP
  como constante única; si en el futuro debiera variar por activo/segmento, requeriría un Change
  aparte (fuera de alcance de este).
- **R-3 (mapeo de `get_symbol_spec` a `tamaño_contrato`)**: R5 prefiere `get_symbol_spec` sobre
  la fuente histórica, pero el mapeo exacto de campos (`contract_size` → `tamaño_contrato`) no se
  ha verificado contra los 21 activos del catálogo — verificar en Design/Apply.

## Preguntas abiertas (para Design)

1. Confirmar con el director el registro de tono (Riesgo R-1) antes de redactar el prompt final
   de `.claude/commands/ventas.md`.
2. Definir el nombre exacto de los placeholders de las plantillas (`{{...}}` vs. `[...]` como en
   el issue original) — mantener consistencia con el patrón de otros `templates/*.txt` del repo.
3. Confirmar si `get_symbol_spec` cubre `contract_size` para los 21 activos o si hay excepciones
   que sigan requiriendo `config/activos.json` como fuente (Riesgo R-3).

## Referencias

- Issue #107 (bbenja11/grupo-analisis-mercado)
- `.pulse/changes/107-discovery-comando-ventas-oportunidad-del-d-a-para-equipo-comerci/idea.md`
- `.pulse/changes/107-discovery-comando-ventas-oportunidad-del-d-a-para-equipo-comerci/proposal.md`
- `CLAUDE.md`
- `.claude/commands/señal.md`, `alerta.md`, `accion.md`, `apertura.md`, `dato_macro.md`
- `.claude/shared/modo_ejecutivo.md`
- `scripts/ruta_mensaje.ps1`
- `config/activos.json`
- `data/historial_senales.json`
- `templates/guion_ejecutivo.txt`
