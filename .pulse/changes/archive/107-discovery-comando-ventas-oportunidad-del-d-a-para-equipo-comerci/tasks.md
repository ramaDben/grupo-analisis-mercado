# Tasks — Comando `/ventas`: Oportunidad del Día (#107)

> Desglose de implementación de la fase **break-to-tasks**. Consolida `design.md` (§2-§4, §7) en
> tareas atómicas mapeadas a los requisitos `R1..R13` / criterios de aceptación `AC1..AC8` de
> `spec.md`.
>
> **Dominio Pulse:** comandos · **Bump sugerido:** minor (`type:feat`, comando nuevo, aditivo).
> **Gate `DESIGN → APPLY`:** design aprobado por el director el 2026-07-13T21:00:47Z
> (`design_approved_at` presente en el ledger). D-GATE-1/2/3 aceptados tal cual (design.md §5).

## Invariantes (obligatorias)

- `/ventas` es un archivo de prompt (`.claude/commands/ventas.md`), no código ejecutable — no
  requiere módulos Python/tests `pytest`. La "verificación" es inspección estructural del
  archivo + ejecución manual guiada (mismo criterio que el resto de comandos del repo).
- No modificar `señal.md`, `alerta.md`, `accion.md`, `dato_macro.md` ni
  `scripts/ruta_mensaje.ps1` (RNF2 — aditivo).
- Placeholders de plantillas en `[Corchetes]`, nunca `{{mustache}}` (design.md §3).
- Ticket mínimo `$5.000.000 CLP` como texto fijo en ambas plantillas, nunca placeholder (R7).

---

## Fase A — Archivos base (sin dependencias)

- [x] **T1 — Plantilla de email** · `templates/ventas_email.txt` (nuevo) · *(R10)*
  Copiar literal la plantilla de email del issue #107 / `design.md` §3, con placeholders
  `[Nombre del Activo/Evento]`, `[Fecha]`, `[Insertar noticia clave]`, `[Nombre]`,
  `[Compra / Venta]`, `[Precio]` (×3: entrada/TP/SL), `[ej. Intradía / 24-48 horas]`.
  **Verificación (AC2):** el texto coincide literal con el issue #107 (asunto, saludo, bloque
  "Detalle de la Estrategia", cierre).

- [x] **T2 — Plantilla de WhatsApp** · `templates/ventas_whatsapp.txt` (nuevo) · *(R10)*
  Copiar literal la plantilla de WhatsApp del issue #107 / `design.md` §3, mismos placeholders
  en formato corto con emojis (⚡📈🎯💰🛑🔹⏳).
  **Verificación (AC2):** el texto coincide literal con el issue #107.

- [x] **T3 — Historial vacío** · `data/historial_ventas.json` (nuevo) · *(R13)*
  Contenido inicial: `[]` (mismo patrón que `data/historial_senales.json`).
  **Verificación:** el archivo existe y parsea como JSON array vacío.

---

## Fase B — Comando (depende de T1-T3)

- [x] **T4 — Encabezado y PASO 1 (detección de evento)** · `.claude/commands/ventas.md` (nuevo) ·
  *(R1, R2)*
  Línea de descripción + PASO 1: `obtener_calendario_macro` → complementar con `WebSearch`
  (mismos 5 filtros de prioridad literales de `alerta.md` PASO 1) → si no hay candidato,
  `"📊 Sin oportunidad clara hoy."` y DETENER.
  **Verificación (AC1, AC3):** el paso existe y el guardrail de "sin evento" está explícito.

- [x] **T5 — PASO 2 (activo protagonista)** · `.claude/commands/ventas.md` · *(R3)*
  Determinar 1 activo obligatorio; mostrar `"🎯 Activo protagonista: [ticker] — [1 línea]"`.
  **Verificación (AC1):** el paso exige exactamente 1 activo, nunca `_general`.

- [x] **T6 — PASO 3 (niveles técnicos)** · `.claude/commands/ventas.md` · *(R4)*
  `mcp__market-data__get_asset_levels(ticker, timeframe)` directo, sin confirmación manual
  previa (patrón `accion.md`). `timeframe` default `"1H"`/`"4H"` según naturaleza del evento
  (design.md §2, PASO 3).
  **Verificación (AC1):** el paso no incluye un sub-paso de ingreso manual de niveles.

- [x] **T7 — PASO 4 (cálculo CLP y R/R)** · `.claude/commands/ventas.md` · *(R5, R6)*
  TC USD/CLP vía MT5 (fallback WebSearch) + `tamaño_contrato` vía `get_symbol_spec.contract_size`
  (fallback `config/activos.json`) + fórmulas `TP_CLP`/`SL_CLP`/`RR` (idénticas a `señal.md`
  PASO 5) + formateo por `digits` + advertencia no bloqueante si `RR < 1.5`.
  **Verificación (AC1, AC6):** el paso incluye el fallback de `tamaño_contrato` y la advertencia
  de RR bajo marcada explícitamente como no bloqueante.

- [x] **T8 — PASO 5 (ticket mínimo y temporalidad)** · `.claude/commands/ventas.md` · *(R7)*
  Ticket mínimo fijo `$5.000.000 CLP`. Temporalidad default por naturaleza del evento +
  volatilidad del activo (`config/activos.json`), confirmable en PASO 7.
  **Verificación (AC1):** el ticket mínimo aparece como constante, no como pregunta al director.

- [x] **T9 — PASO 6 (render de las dos piezas)** · `.claude/commands/ventas.md` · *(R8)*
  Rellenar `templates/ventas_email.txt` y `templates/ventas_whatsapp.txt` con los mismos datos de
  fondo; mostrar ambas rotuladas `📧 EMAIL` / `📱 WHATSAPP` (design.md §2, PASO 6).
  **Verificación (AC4):** ambas piezas se generan siempre juntas, nunca solo una.

- [x] **T10 — Rechazo del flag `ejecutivo`** · `.claude/commands/ventas.md` · *(R9)*
  Al inicio del comando: si `ejecutivo` está en los argumentos, avisar que no aplica y continuar
  normalmente (no abortar).
  **Verificación (AC5):** el aviso existe y el flujo continúa tras mostrarlo.

- [x] **T11 — PASO 7 (aprobación)** · `.claude/commands/ventas.md` · *(R11)*
  3 preguntas: aprobar / ajustar niveles-temporalidad (vuelve a T6/T8) / enviar por correo o
  WhatsApp (informativo). Sin aprobación explícita, DETENER sin guardar.
  **Verificación (AC7):** el paso bloquea el guardado si no hay aprobación explícita.

- [x] **T12 — PASO 8 (guardado)** · `.claude/commands/ventas.md` · *(R12, R13)*
  Guardar ambas piezas vía `scripts\ruta_mensaje.ps1` (`-Tipo "ventas_email"` /
  `"ventas_whatsapp"`, `-Activo` siempre presente, misma `-Hora`); agregar entrada a
  `data/historial_ventas.json` (schema de `spec.md` R13 / `design.md` §4).
  **Verificación (AC4):** se generan 2 archivos + 1 entrada de historial tras aprobar.

---

## Fase C — Documentación (puede hacerse en paralelo a Fase B)

- [x] **T13 — Documentar `/ventas` en `CLAUDE.md`** · `CLAUDE.md` · *(Alcance IN)*
  Nueva fila en la tabla de Capa 2 (`## Slash Commands disponibles`).
  **Verificación (AC8):** `/ventas` aparece en la tabla con su descripción.

- [x] **T14 — Agregar `/ventas` a "No elegibles" del modo ejecutivo** ·
  `.claude/shared/modo_ejecutivo.md` · *(R9)*
  Agregar `/ventas` a la lista junto a `/estado`, `/chart`, `/curriculo`, con la razón ("ya es el
  HUB INTERNO por sí mismo, no necesita un guion adicional que lo envuelva").
  **Verificación (AC8):** `/ventas` aparece en la lista con su razón.

---

## Fase D — Verificación end-to-end (depende de A, B, C)

> **Método usado en esta fase**: revisión estructural directa del texto de `.claude/commands/ventas.md`
> contra cada AC/CB de `spec.md` — **no** se ejecutó el comando en vivo, para no escribir
> entradas de prueba en `data/historial_ventas.json` ni archivos falsos en `data/mensajes/`
> (ensuciaría datos reales) y para no gastar tokens en llamadas reales a `WebSearch`/MT5 solo
> para un dry-run. Pendiente: una corrida real única por el director antes de uso en producción.

- [x] **T15 — Ejecución guiada: sin evento relevante** · *(CB-1, AC3)*
  Verificado por lectura: PASO 1 punto 3 muestra `"📊 Sin oportunidad clara hoy."` y ordena
  DETENER antes de PASO 2 — nunca fuerza una oportunidad.

- [x] **T16 — Ejecución guiada: camino feliz** · *(CB-4 implícito, AC4)*
  Verificado por lectura: PASO 6 exige mostrar "ambas piezas, siempre juntas (nunca solo una)";
  PASO 4 punto 4 formatea por `digits`; PASO 8 guarda 2 archivos vía `ruta_mensaje.ps1` + 1
  entrada en `data/historial_ventas.json` con `ticket_minimo_clp` fijo.

- [x] **T17 — Ejecución guiada: flag `ejecutivo`** · *(CB-3, AC5)*
  Verificado por lectura: el bloque "Rechazo del flag `ejecutivo`" está antes de PASO 1, muestra
  el aviso y ordena "Continuar normalmente con el PASO 1 (no abortar)".

- [x] **T18 — Ejecución guiada: RR bajo** · *(CB-2, AC6)*
  Verificado por lectura: PASO 4 punto 5 muestra la advertencia y aclara explícitamente "Esto no
  detiene el comando".

- [x] **T19 — Ejecución guiada: rechazo de aprobación** · *(CB-4, AC7)*
  Verificado por lectura: PASO 7 ordena "DETENER. No guardar nada (ni en
  `data/historial_ventas.json` ni en `data/mensajes/`)" si el director no aprueba.

- [ ] **T20 — Corrida real única (pendiente, recomendada antes de uso diario)**
  El director ejecuta `/ventas` una vez con un evento real del día, revisa ambas piezas y
  confirma que el guardado y el historial quedan correctos. No bloquea el cierre de este Change
  (T15-T19 ya cubren la lógica), pero se recomienda antes de incorporarlo a la operativa diaria.

---

## Orden de ejecución recomendado

`T1, T2, T3` (base, en paralelo) → `T4 → T5 → T6 → T7 → T8 → T9 → T10 → T11 → T12` (comando,
secuencial por PASO) → `T13, T14` (docs, en paralelo a Fase B) → `T15..T19` (verificación
end-to-end, tras Fase B+C).

## Verificación global (Definition of Done)

- [x] `.claude/commands/ventas.md` contiene los 8 PASOS + rechazo de `ejecutivo`, en el orden de
  `design.md` §2 (AC1).
- [x] `templates/ventas_email.txt` y `templates/ventas_whatsapp.txt` coinciden literal con el
  issue #107 (AC2).
- [x] `data/historial_ventas.json` existe como `[]` antes de la primera corrida real.
- [x] `CLAUDE.md` y `.claude/shared/modo_ejecutivo.md` documentan `/ventas` (AC8).
- [x] Los 5 escenarios (T15-T19) se verificaron por revisión estructural del comando contra
  `spec.md` (no por ejecución en vivo — ver nota de Fase D). T20 (corrida real) queda pendiente,
  no bloqueante.
- [x] Ningún comando existente (`señal.md`, `alerta.md`, `accion.md`, `dato_macro.md`,
  `ruta_mensaje.ps1`) fue modificado (RNF2) — confirmado por `git status` (ver Change).

## Pendiente de confirmación en Apply (no bloquea la transición a Apply)

- Verificar que `get_symbol_spec` efectivamente expone `contract_size` para los activos que se
  usen en las ejecuciones guiadas de T16/T18 (Riesgo R-3 de `spec.md`) — si no, confirmar que el
  fallback a `config/activos.json` funciona sin bloquear el comando.
