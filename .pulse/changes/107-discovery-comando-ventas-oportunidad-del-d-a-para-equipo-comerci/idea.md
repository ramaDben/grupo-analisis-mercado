# Idea: Comando `/ventas` — Oportunidad del Día para equipo comercial

Issue: [bbenja11/grupo-analisis-mercado#107](https://github.com/bbenja11/grupo-analisis-mercado/issues/107)

## Problema

El equipo de ventas interno de Grupo de Análisis de Mercado no tiene hoy
ningún flujo que traduzca la noticia/evento de mercado más relevante del día
en una "Oportunidad del Día" accionable, con ticket mínimo ($5.000.000 CLP),
gestión de riesgo explícita (entrada/TP/SL) y temporalidad, lista para que
ventas la use con sus clientes — en dos formatos (email formal + WhatsApp
urgente). Todo el pipeline de 23 slash commands existente está diseñado para
el **cliente final** del grupo educativo de WhatsApp (lenguaje novato, tono no
catastrófico, formato visual de 6 reglas); no hay un comando cuyo público
objetivo primario sea el equipo comercial interno con una pieza de venta
completa (no solo un "guion" complementario). El issue #107 pide llenar ese
vacío sin construir generación de infografías (de otro equipo) ni envío
automático (fuera del flujo de aprobación manual existente).

## Contexto observado

- **`CLAUDE.md`** documenta 22 comandos (Capa 1/2/3), el flujo de aprobación
  manual → `data/mensajes/` vía `scripts/ruta_mensaje.ps1`, el formato de
  6 reglas WhatsApp, la regla de decimales por `digits` (`config/activos.json`)
  y el límite duro de 3 señales/semana en `data/historial_senales.json`
  (hoy vacío `[]` — no hay señales registradas este ciclo, sin colisión
  inmediata pero la semántica de "cuenta o no" queda abierta).
- **`.claude/commands/señal.md`**: precedente más cercano en estructura
  (entrada/TP/SL/volumen, conversión a CLP vía TC USD/CLP y tamaño de
  contrato, validación R/R, aprobación → registro en
  `data/historial_senales.json`). No genera dos formatos de salida ni tiene
  noción de "ticket mínimo".
- **`.claude/commands/alerta.md`**: precedente de detección de la noticia
  más relevante — `WebSearch` de breaking news de las últimas ~2h con
  filtros de prioridad (bancos centrales → datos macro sorpresivos >0.3pts →
  geopolítica → earnings tech → OPEP+), dedupe de 1h, tono "urgente pero no
  alarmista", y encadena `data/ultimo_evento.json` + encuesta post-evento.
- **`.claude/commands/dato_macro.md`**: precedente de calendario económico
  (`obtener_calendario_macro` nativo MT5, fallback WebSearch), reglas de
  `digits`, y estructura "modo anticipación / modo resultado".
- **`.claude/commands/apertura.md`**: precedente de uso de
  `mcp__market-data__get_asset_levels({"ticker","timeframe"})` — pero con
  filosofía de ingreso manual de soportes/resistencias por el director
  (ignora S/R del MCP, solo usa `price` + indicador).
- **`.claude/commands/accion.md`**: precedente contrastante — extrae
  `price, s1, s2, r1, r2, rsi_14, atr_14, trend` directamente del MCP sin
  pedir confirmación manual, flujo más liviano/rápido — encaja mejor con el
  marco de urgencia de "Oportunidad del Día".
- **`.claude/shared/modo_ejecutivo.md`** (hallazgo clave): ya existe un
  contrato completo para contenido dirigido al equipo interno de ejecutivos
  — el "guion ejecutivo" (banner `🔒 INTERNO · NO ENVIAR AL CLIENTE`,
  plantilla `templates/guion_ejecutivo.txt`, guardado como `guion_<tipo>` vía
  `ruta_mensaje.ps1`). El propio archivo declara que materializa el
  "HUB INTERNO (ejecutivos)" de `docs/design/motor-como-cerebro-hub-gi.brief.md`.
  `/ventas` es conceptualmente una instancia de ese mismo HUB INTERNO, pero el
  issue #107 lo pide como comando propio con su propio contenido primario
  (no un guion complementario a un mensaje de cliente) — hay que decidir en
  Specify cómo se relaciona con este contrato existente sin duplicarlo.
- **`docs/design/motor-como-cerebro-hub-gi.brief.md` / `.propuesta.md`**
  (untracked en git status): framing estratégico del propio director —
  "un cerebro, dos hubs" (HUB INTERNO ejecutivos vs HUB EXTERNO clientes).
  Confirma que `/ventas` encaja en un bucket ya articulado a nivel de visión,
  no es un one-off.
- **`scripts/ruta_mensaje.ps1`**: convención determinista
  `data/mensajes/<Fecha>/<activo>/<Tipo>/<Hora>_<Tipo>.txt`; el enum de
  `Tipo` documentado en `CLAUDE.md` (niveles, dato_macro, noticia, alerta,
  encuesta, señal, concepto, pregunta, respuesta, cierre, earnings) no
  incluye aún nada para `/ventas` ni para un formato "email".
- **`config/activos.json`**: `digits`, `volatilidad`, `nota_volatilidad`,
  `drivers`, `ticker_mt5` por activo — necesario para formatear precios y
  justificar temporalidad.
- **`templates/`**: no existe plantilla de email en todo el repo; el sibling
  más cercano es `templates/guion_ejecutivo.txt`. Los dos formatos literales
  (email + WhatsApp) del issue #107 tendrían que convertirse en 1-2 archivos
  nuevos siguiendo el patrón `templates/*.txt` existente.
- Las reglas de "lenguaje novato" y "tono no catastrófico" de `CLAUDE.md`
  están explícitamente scoped al cliente final; el propio issue #107 marca
  como abierto si aplican igual a una audiencia profesional de ventas.

## Hipótesis de solución

Nuevo comando Capa 2 `.claude/commands/ventas.md` con estructura de pasos
análoga a los comandos existentes:

1. Detección de la noticia/evento más relevante (reutilizar filtros de
   prioridad y dedupe de `/alerta`, posiblemente combinado con
   `obtener_calendario_macro` de `/dato_macro` cuando el evento es un dato
   agendado).
2. Niveles técnicos vía `mcp__market-data__get_asset_levels`
   (`s1/s2/r1/r2/rsi_14/atr_14/trend`), con filosofía tipo `/accion`
   (extracción directa, sin el paso manual de `/apertura`) dado el marco
   de urgencia — a confirmar/ajustar en Specify.
3. Cálculo de entrada/TP/SL + traducción a CLP reutilizando la lógica de
   `/señal` (TC USD/CLP, tamaño de contrato, validación R/R).
4. Formateo de todos los precios según `digits` de `config/activos.json`
   (regla MT5 transversal a todo el repo).
5. Render de dos piezas obligatorias por corrida usando las plantillas
   literales del issue #107 (email formal + WhatsApp urgente) — probablemente
   como dos archivos nuevos en `templates/`.
6. Aprobación manual del director (mismo gate que el resto: "¿Apruebas?
   ¿Enviar por correo? ¿Enviar por WhatsApp?"), sin envío automático.
7. Guardado con `scripts/ruta_mensaje.ps1` extendiendo el enum de `Tipo`
   (p. ej. `ventas_email` / `ventas_whatsapp`, o un solo tipo `ventas` con
   dos archivos) — a decidir en Specify.
8. Registro en un historial propio (p. ej. `data/historial_ventas.json`),
   independiente de `data/historial_senales.json`, dado que el público
   y la mecánica de negocio (ticket mínimo, audiencia ventas) son
   disjuntos del límite de 3 señales/semana orientado al cliente final —
   hipótesis a validar en Specify.

Explícitamente NO se construye en este Change: generación de infografías ni
el flujo de envío automático (fuera de alcance confirmado por el issue).

## Preguntas abiertas

1. ¿`/ventas` cuenta contra el límite de 3 señales/semana
   (`data/historial_senales.json`) o usa un historial independiente
   (`data/historial_ventas.json`)?
2. ¿`/ventas` debe soportar el flag `ejecutivo` del contrato
   `.claude/shared/modo_ejecutivo.md`, o queda explícitamente fuera de esa
   lista (como `/estado`, `/chart`, `/curriculo`) por no producir un
   "mensaje de cliente reenviable"? ¿Cómo se relaciona conceptualmente con
   el "guion ejecutivo" ya existente para no duplicar el mismo HUB INTERNO
   dos veces?
3. ¿Los niveles (entrada/TP/SL) se derivan automáticamente de
   `get_asset_levels` (patrón `/accion`, más rápido/urgente) o requieren
   confirmación/ingreso manual del director (patrón `/apertura`/`/señal`,
   más preciso)?
4. ¿Qué mecanismo de detección de "noticia más relevante" reutilizar:
   el de `/alerta` (WebSearch + filtros de prioridad + dedupe 1h), el de
   `/dato_macro` (`obtener_calendario_macro` nativo MT5), o ambos como
   fuentes combinadas según el tipo de evento?
5. Convención de guardado exacta vía `ruta_mensaje.ps1`: ¿un tipo `ventas`
   con dos archivos (email/whatsapp) o dos tipos separados
   (`ventas_email`/`ventas_whatsapp`)? ¿Activo obligatorio (el issue liga
   la oportunidad a 1 activo protagonista)?
6. ¿El ticket mínimo ($5.000.000 CLP) y la temporalidad (intradía/24-48h)
   son texto fijo/elegido por el director, o se derivan de algo (RR,
   volatilidad del activo, tamaño de posición sugerido)?
7. ¿Aplican las 6 reglas de formato visual WhatsApp y las reglas de tono/
   registro de `CLAUDE.md` (lenguaje novato, no catastrofismo) al público de
   ventas, o se define un registro propio más directo/profesional sin
   explicar siglas? El propio issue lo deja abierto.
8. ¿El directorio `.pulse/changes/78-d1-purgar-c-digo-docs-tools-ajenos-y-muertos/`
   (con `design.md`/`tasks.md` presentes pero sin mover a `archive/`) requiere
   limpieza aparte? No bloquea este Change (`list_active_changes` confirma
   que no hay Change activo en conflicto), pero queda como deuda de housekeeping
   fuera de este alcance.

## Referencias

- `CLAUDE.md`
- `.claude/commands/señal.md`
- `.claude/commands/alerta.md`
- `.claude/commands/dato_macro.md`
- `.claude/commands/apertura.md`
- `.claude/commands/accion.md`
- `.claude/shared/modo_ejecutivo.md`
- `scripts/ruta_mensaje.ps1`
- `config/activos.json`
- `data/historial_senales.json`
- `templates/guion_ejecutivo.txt`
- `docs/design/motor-como-cerebro-hub-gi.brief.md`
- `docs/design/motor-como-cerebro-hub-gi.propuesta.md`
- GitHub issue: `bbenja11/grupo-analisis-mercado#107`
