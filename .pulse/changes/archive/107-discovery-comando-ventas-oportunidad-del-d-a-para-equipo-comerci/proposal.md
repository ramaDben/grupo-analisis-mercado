# Propuesta: Comando `/ventas` — Oportunidad del Día para equipo comercial

Issue: [bbenja11/grupo-analisis-mercado#107](https://github.com/bbenja11/grupo-analisis-mercado/issues/107)

## Problema

El equipo de ventas interno no tiene un flujo que traduzca la noticia/evento
de mercado más relevante del día en una pieza de venta accionable — con
ticket mínimo ($5.000.000 CLP), niveles de entrada/TP/SL y temporalidad — en
los dos formatos que el issue #107 fija de forma literal (email formal +
WhatsApp urgente). El pipeline de 23 comandos existentes está diseñado para
el cliente final del grupo educativo; no hay un comando cuyo contenido
primario sea para el equipo comercial. Ver `idea.md` para el detalle
completo de la exploración.

## Contexto observado

Ver `idea.md` (sección "Contexto observado") para el detalle de archivos y
patrones relevados. Resumen operativo para esta propuesta:

- `/señal` aporta el cálculo entrada/TP/SL → CLP (TC USD/CLP + tamaño de
  contrato) y el gate de aprobación.
- `/alerta` aporta detección de la noticia más relevante (WebSearch + filtros
  de prioridad + dedupe 1h) y `/dato_macro` aporta la fuente de eventos
  agendados (`obtener_calendario_macro`).
- `/accion` aporta el patrón de niveles técnicos "directo, sin confirmación
  manual" vía `get_asset_levels`, coherente con el marco de urgencia de
  "Oportunidad del Día".
- `.claude/shared/modo_ejecutivo.md` es el contrato del HUB INTERNO ya
  existente, pero está diseñado para acompañar un mensaje de cliente — no
  para ser el contenido primario. `/ventas` no encaja como consumidor de ese
  contrato: ES el HUB INTERNO por sí mismo.
- `scripts/ruta_mensaje.ps1` recibe `-Tipo` como parámetro libre (no hay enum
  validado en código, solo documentado en `CLAUDE.md`) — agregar tipos nuevos
  no requiere tocar el script, solo documentarlos.
- `data/historial_senales.json` está vacío (`[]`) — no hay colisión de datos,
  pero si `/ventas` escribiera ahí mezclaría dos semánticas de negocio
  distintas (límite regulatorio/comercial de señales al cliente vs.
  oportunidades tácticas al equipo comercial).

## Hipótesis de solución

Nuevo comando Capa 2 `.claude/commands/ventas.md`, autónomo (no delega en
`/señal`/`/alerta` en tiempo de ejecución, pero **reutiliza su lógica** como
referencia de implementación), con este flujo:

1. **Detección de evento**: combinar `obtener_calendario_macro` (eventos
   agendados de hoy, prioridad si son de alto impacto) con `WebSearch`
   breaking news de las últimas ~2h (mismos filtros de prioridad de
   `/alerta`: bancos centrales → datos macro sorpresivos >0.3pts →
   geopolítica → earnings tech → OPEP+). Si no hay ningún evento con
   relevancia suficiente para una "oportunidad táctica", el comando informa
   "Sin oportunidad clara hoy" y se detiene (mismo patrón que `/alerta`
   PASO 2) — nunca fuerza una oportunidad artificial.
2. **Selección de activo protagonista**: el activo más directamente
   impactado por el evento detectado (1 activo, obligatorio).
3. **Niveles técnicos**: `mcp__market-data__get_asset_levels` (patrón
   `/accion` — extracción directa de `price/s1/s2/r1/r2/rsi_14/atr_14/trend`,
   sin paso de confirmación manual previo), coherente con el marco de
   urgencia. El director puede ajustar entrada/TP/SL en el paso de
   aprobación, igual que revisa cualquier otro borrador antes de aprobar.
4. **Cálculo CLP y R/R**: mismo mecanismo que `/señal` PASO 5 (TC USD/CLP vía
   MT5, tamaño de contrato desde `get_symbol_spec`/`config/activos.json`,
   validación R/R con el mismo umbral de alerta `< 1.5`).
5. **Formateo de precios**: `digits` de `config/activos.json`, regla
   transversal ya vigente.
6. **Ticket mínimo y temporalidad**: ticket mínimo $5.000.000 CLP como
   constante fija del comando (regla de negocio, no varía por corrida —
   mismo tipo de constante que el límite "3 señales/semana"). Temporalidad
   calculada por defecto a partir de la volatilidad del activo
   (`config/activos.json`) y el patrón del evento (dato agendado de alto
   impacto → "Intradía"; evento con inercia de 24-48h como decisión de
   política monetaria o geopolítica → "24-48 horas"), mostrada al director
   en el paso de aprobación para confirmar o ajustar — igual que `/señal`
   PASO 6 pregunta temporalidad/tipo operativa.
7. **Render de dos piezas obligatorias por corrida**: dos templates nuevos,
   `templates/ventas_email.txt` y `templates/ventas_whatsapp.txt`, calcados
   literalmente de las plantillas del issue #107 (asunto, saludo, bloque
   "Detalle de la Estrategia", cierre) con placeholders `[Nombre del
   Activo/Evento]`, `[Fecha]`, `[Precio]`, etc.
8. **Registro propio**: `data/historial_ventas.json`, independiente de
   `data/historial_senales.json` (ver Pregunta 1).
9. **Aprobación manual del director** (mismo gate que el resto): "¿Apruebas
   la oportunidad? ¿Ajustar niveles/temporalidad? ¿Enviar por correo?
   ¿Enviar por WhatsApp?" — sin envío automático (Evolution API para
   WhatsApp; el email queda fuera del alcance de envío automático por
   completo, ya que no existe integración de correo en el proyecto).
10. **Guardado**: `scripts/ruta_mensaje.ps1` con dos tipos nuevos
    (`ventas_email`, `ventas_whatsapp`) y `-Activo` siempre presente (ver
    Pregunta 5).

Explícitamente NO se construye en este Change: generación de infografías ni
el flujo de envío automático (confirmado fuera de alcance por el issue).

### Resolución de las 8 preguntas abiertas

**1. ¿Cuenta contra el límite de 3 señales/semana o usa historial
independiente?**
Decisión: **historial independiente**, `data/historial_ventas.json`. La
sección "Señales operativas" de `CLAUDE.md` y el límite de 3/semana están
scoped explícitamente al flujo cliente-final del grupo educativo (mismo
`/señal`). `/ventas` tiene otra audiencia (equipo comercial interno), otra
mecánica de negocio (ticket mínimo institucional, no señal minorista) y otro
objetivo (venta directa, no educación + señal complementaria). Mezclarlos en
el mismo archivo/límite confundiría dos controles de negocio distintos sin
que el issue lo pida.

**2. ¿Debe soportar el flag `ejecutivo` de `modo_ejecutivo.md`? ¿Cómo se
relaciona con el guion ejecutivo existente?**
Decisión: **NO** soporta el flag `ejecutivo`. `/ventas` no es un comando que
produzca un "mensaje de cliente reenviable" que necesite un guion interno
complementario — su contenido primario YA ES 100% interno (equipo
comercial). Se agrega explícitamente a la lista de "No elegibles" de
`.claude/shared/modo_ejecutivo.md` junto a `/estado`, `/chart` y
`/curriculo`, documentando la razón ("ya es el HUB INTERNO, no necesita un
guion adicional que lo envuelva"). Esto evita duplicar el mismo HUB INTERNO
dos veces, tal como el `idea.md` anticipaba como riesgo.

**3. ¿Niveles automáticos (`/accion`) o con confirmación manual
(`/apertura`/`/señal`)?**
Decisión: **automáticos**, patrón `/accion` — extracción directa de
`get_asset_levels` sin paso de ingreso manual previo, porque el marco de
"Oportunidad del Día" es de urgencia (issue: "oportunidad táctica inmediata",
"prioridad"). El director conserva control de calidad en el paso de
aprobación (puede pedir ajustar antes de aprobar), igual que en `/señal`.

**4. ¿Qué mecanismo de detección de noticia reutilizar?**
Decisión: **ambos, combinados**, con el mismo orden de prioridad que
`/alerta` (bancos centrales → datos macro sorpresivos → geopolítica →
earnings tech → OPEP+): primero se revisa `obtener_calendario_macro` para
eventos agendados de alto impacto de hoy; si no hay uno claramente dominante,
se complementa con `WebSearch` de breaking news de las últimas ~2h (mismo
filtro que `/alerta`). Si ninguna fuente entrega un evento con relevancia
suficiente, el comando se detiene sin forzar una oportunidad — mismo
guardrail que `/alerta` PASO 2.

**5. Convención de guardado y activo obligatorio.**
Decisión: **dos tipos separados**, `ventas_email` y `ventas_whatsapp` (no un
tipo único con dos archivos), porque `ruta_mensaje.ps1` ya modela "un archivo
por `-Tipo`" y el precedente `guion_<tipo>` establece que variantes de una
misma pieza se distinguen por tipo, no por convención ad hoc dentro del
mismo tipo. **`-Activo` es obligatorio** (nunca `_general`): el issue liga
cada "Oportunidad del Día" a un activo/evento protagonista único por
construcción de la plantilla ("[Nombre del Activo/Evento]").

**6. ¿Ticket mínimo y temporalidad fijos o derivados?**
Decisión: **ticket mínimo fijo** ($5.000.000 CLP, constante del comando, no
editable por corrida — es política comercial, no un cálculo de mercado).
**Temporalidad con default calculado** (volatilidad del activo + naturaleza
del evento, ver Hipótesis punto 6) pero **confirmable/ajustable por el
director** en el paso de aprobación, igual que `/señal`. *Pendiente de
confirmar con el director*: si el ticket mínimo de $5.000.000 CLP es
realmente un valor fijo institucional o si en algún escenario debe variar
(ej. por activo o por segmento de cliente) — se toma fijo como default de
Specify por ser lo que dicta literalmente el issue, pero es una decisión de
política comercial que excede el precedente técnico del repo.

**7. ¿Aplican las reglas de tono/formato del cliente final (lenguaje
novato, no catastrofismo, 6 reglas visuales WhatsApp) al equipo de ventas?**
Decisión: **registro propio, más directo y técnico, sin obligación de
explicar siglas** — la audiencia es un equipo comercial profesional, no el
cliente novato del grupo educativo; forzar explicaciones novatas ahí
diluiría la urgencia y el profesionalismo que pide el issue. Se **mantiene**
sin embargo la norma general de `CLAUDE.md` de evitar dramatización
catastrófica (esa norma es de casa/reputacional, no específica del cliente
novato). Las plantillas literales del issue (email + WhatsApp con ⚡/📈/🎯)
se usan tal cual, sin forzar las 6 reglas de formato visual del cliente
(separadores `━━━`, bloque de cierre 🟢🟡🔴) porque el issue ya define su
propia estructura "above the fold" equivalente (encabezado ⚡ + veredicto
+ bloque de estrategia). *Pendiente de confirmar con el director*: si el
registro "sin explicar siglas" es aceptable dado que el propio issue lo deja
abierto explícitamente — se toma esta postura como default razonable por
precedente (audiencia profesional interna vs. cliente novato), pero es una
decisión de tono que el director puede querer revisar en Specify o Design.

**8. ¿Requiere limpieza aparte el directorio
`.pulse/changes/78-d1-purgar-c-digo-docs-tools-ajenos-y-muertos/`?**
Decisión: **fuera de alcance de este Change**. Es deuda de housekeeping
(Change #78 con `design.md`/`tasks.md` sin archivar) que no bloquea ni se
relaciona funcionalmente con `/ventas`. Se deja constancia aquí para que se
registre como issue de housekeeping aparte, sin gate sobre esta propuesta.

## Preguntas abiertas (para Specify)

- Confirmar con el director el valor fijo del ticket mínimo (Pregunta 6) y
  el registro de tono sin explicación de siglas (Pregunta 7) antes de cerrar
  Specify — ambas quedan con una postura tomada en esta propuesta, pero son
  decisiones de negocio/tono que el director puede ajustar.
- Definir en Specify el nombre exacto de los dos templates nuevos y su
  contrato de placeholders (`templates/ventas_email.txt`,
  `templates/ventas_whatsapp.txt`), y el shape exacto de
  `data/historial_ventas.json` (campos análogos a
  `data/historial_senales.json` + campo de "email"/"whatsapp" enviado).
- Definir si `get_symbol_spec` (tool ya disponible) reemplaza la lectura
  manual de `tamaño_contrato` desde `config/activos.json` en el cálculo CLP,
  dado que ya expone esa especificación de forma determinista.

## Referencias

- `.pulse/changes/107-discovery-comando-ventas-oportunidad-del-d-a-para-equipo-comerci/idea.md`
- `CLAUDE.md`
- `.claude/commands/señal.md`
- `.claude/commands/alerta.md`
- `.claude/commands/dato_macro.md`
- `.claude/commands/apertura.md`
- `.claude/commands/accion.md`
- `.claude/shared/modo_ejecutivo.md`
- `templates/guion_ejecutivo.txt`
- `scripts/ruta_mensaje.ps1`
- `config/activos.json`
- `data/historial_senales.json`
- `docs/design/motor-como-cerebro-hub-gi.brief.md`
- `docs/design/motor-como-cerebro-hub-gi.propuesta.md`
- GitHub issue: `bbenja11/grupo-analisis-mercado#107`
