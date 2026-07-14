# Idea: Conectar motor GAM con plantillas visuales Stories GI (render 1080×1920)

Issue: [bbenja11/grupo-analisis-mercado#109](https://github.com/bbenja11/grupo-analisis-mercado/issues/109)

## Problema

El equipo de diseño de GI entregó 6 plantillas visuales de Stories (formato
Instagram/WhatsApp, 1080×1920) documentadas en
`docs/design/stories-gi/plantillas-stories-gi.md`, pero el propio documento
señala que **conectar datos reales del motor GAM a esas plantillas es trabajo
diferido**: hoy el pipeline completo de 24 slash commands produce únicamente
texto (WhatsApp) y PNGs de charts MT5 crudos (`/chart`), nunca una pieza
visual de marca con contenido real inyectado. El antecedente directo es el
issue #107 (`/ventas`), que excluyó explícitamente la generación de
infografías de su alcance ("la plantilla de infografía la entregará otro
equipo posteriormente y se conectará después"). Sin este mecanismo, el
director no puede ofrecer al cliente final una Story reenviable con la
identidad visual de GI y datos reales (niveles, calendario, alertas,
señales) — solo texto plano o un screenshot de MT5 sin la capa de marca.

Restricciones duras ya declaradas por el propio issue y por el doc de
plantillas: (1) nunca se genera/envía sin aprobación explícita del director
(mismo principio que el resto del repo); (2) el proyecto Claude Design
compartido (dueño: Rodrigo, GI) es **solo lectura** — este repo nunca sube
datos ni lógica propia hacia allá.

## Contexto observado

- **`docs/design/stories-gi/plantillas-stories-gi.md`** (doc de referencia,
  ya en el repo): documenta las 6 plantillas del selector (Market Update,
  Indicador Macro, Alerta, Trading Idea, Reporte Flash, Calendario) con un
  mapeo probable a comandos ya existentes (`/apertura`, `/dato_macro`,
  `/alerta`, `/señal`); la plantilla "Calendario" tiene además un carrusel
  interno de 4 slides ("1/4 Portada", "2/4 WTI", "3/4 Bancos", "4/4 sin
  confirmar"). El propio documento deja explícito que **no** se extrajeron
  los campos completos de las 6 plantillas (extracción liviana con grep
  dirigido, ~90 KB de HTML sin re-leer completo) — solo se detectaron
  parcialmente: `Anterior`/`Consenso` (Indicador Macro), `Soporte`/
  `Resistencia` (Niveles técnicos) y un chip de selector de activo con
  precio inline (`USDCLP · 933,03`). El mapeo campo-por-campo íntegro queda
  pendiente — coincide con lo que el propio issue #109 marca fuera de
  alcance más allá de una plantilla piloto.
- **Regla "solo lectura"** sobre el proyecto Claude Design compartido: hoy
  vive **únicamente** en `plantillas-stories-gi.md` (no está en `CLAUDE.md`
  ni en ninguna regla formal del repo) — es la única mención encontrada en
  todo el repositorio (`Grep` sobre "Claude Design"/"solo lectura" solo
  matcheó ese archivo).
- **`docs/design/motor-como-cerebro-hub-gi.brief.md` / `.propuesta.md`**:
  confirmado como fuera de alcance de este issue. Es la visión más amplia
  ("un cerebro, dos hubs" — HUB INTERNO ejecutivos / HUB EXTERNO clientes),
  en fase preliminar, sin confirmación de GI, y con un bloqueante externo
  real (Manager API del bróker) documentado en su Anexo interno. El propio
  brief aclara que el director "no es el arquitecto" — une visión, no
  construye. Este Change de Stories es trabajo técnico concreto que el
  director delega, independiente de si esa visión más amplia avanza.
  Coherente con memoria del proyecto (`project_posicion_visionario_motor`).
- **`.claude/commands/apertura.md`** (PASO 5): plantilla de mensaje de
  "Niveles" ya madura — campos `precio actual`, `Resistencia más próxima/
  siguiente`, `Soporte más próximo/siguiente`, `Zona de interés`, `sesgo del
  equipo`, indicador (RSI/ATR/EMA/MACD/Bollinger), justificación de
  temporalidad por volatilidad. Candidato natural de piloto para "Market
  Update" o "Indicador Macro" — sus campos ya calzan con lo detectado en
  el canvas (`Soporte`/`Resistencia`, chip de activo+precio).
- **`.claude/commands/dato_macro.md`**: modos "anticipación"/"resultado"
  con campos `Anterior`/`Consenso`/`actual` — coincide literalmente con los
  campos `Anterior`, `Consenso` detectados en la plantilla "Indicador
  Macro" del canvas. Otro candidato fuerte de piloto.
- **`.claude/commands/alerta.md`** y **`.claude/commands/señal.md`**:
  mapeos probables a "Alerta" y "Trading Idea" respectivamente, sin campos
  del canvas todavía verificados para estas dos.
- **`.claude/commands/chart.md`** (precedente clave de generación de PNG):
  ya existe un pipeline de imagen binaria end-to-end en el repo, aunque para
  charts crudos de MT5, no para Stories de marca. Protocolo: el comando
  escribe `data/mt5_command.json`, el EA MT5 (`GI_ChartExporter`) genera el
  screenshot y responde en `data/mt5_response.json`, y el PNG final se
  guarda en `data/charts/` con nombre canónico
  `<activo_slug>_<TF>_<YYYY-MM-DD_HH-MM>.png` (issue #81). Aprobación antes
  de "enviar" el PNG standalone o adjuntarlo a otra pieza — mismo principio
  que se pide para Stories.
- **`src/market_data_mcp/tools/chart_objects.py`** (`get_chart_objects`):
  segundo precedente de "recibir" un binario generado externamente — el
  Service MQL5 `ChartObjectsExporter` escribe en el sandbox `Common/Files`
  de MT5, y la tool copia el PNG vigente a `data/charts/` (`_recibir_screenshot`).
  Ambos precedentes (`/chart` y `get_chart_objects`) validan el patrón
  "proceso externo genera → función del repo copia/recibe con nombre
  canónico" que podría reutilizarse para un renderer headless de Stories.
- **Sin stack de render instalado hoy**: `pyproject.toml` solo declara
  `fastmcp` y `pandas` como dependencias runtime (más `ruff`/`ty`/`pytest`/
  `numpy` de dev). No hay `Pillow`, `Playwright`, ni ninguna librería de
  HTML-to-image. La decisión de mecanismo de render que plantea el issue
  (headless de una copia adaptada del template vs. reimplementación nativa)
  está completamente abierta — ninguna dependencia previa la inclina.
- **`scripts/ruta_mensaje.ps1`**: convención determinista para **texto**
  (`data/mensajes/<Fecha>/<activo>/<Tipo>/<Hora>_<Tipo>.txt`); no tiene
  noción de binarios/PNG. Los PNG de chart usan una convención hermana pero
  distinta (`data/charts/`, issue #81). Una Story PNG tendría que decidir a
  cuál de las dos convenciones se afilia, o crear una tercera (con nombre de
  plantilla y, para "Calendario", número de slide del carrusel).
- **`.gitignore`**: ya ignora `data/charts/*.png` y `data/mensajes/` — un
  nuevo artefacto binario de Stories previsiblemente entra en el mismo
  régimen de datos generados no versionados.
- **`config/activos.json`**: `ticker_mt5`, `digits`, `volatilidad`,
  `nota_volatilidad`, `drivers` por activo — insumo necesario para formatear
  el chip de activo+precio y justificar temporalidad dentro de la Story,
  igual que hoy en los mensajes de texto.
- **`.claude/shared/modo_ejecutivo.md`**: contrato ya maduro para "dos
  salidas por pieza" (mensaje cliente + guion interno). El issue #109 fija
  el público objetivo del output en "Clientes del grupo de WhatsApp" — no
  queda claro si el flujo de Stories necesita adherirse a este contrato
  (como hacen `/apertura`, `/dato_macro`, `/alerta`, `/señal`) o si, como
  `/chart` ("genera un PNG, no texto"), queda fuera de la lista de
  elegibles del flag `ejecutivo`.
- **`docs/design/stories-gi/Manual Plantilla Stories - Grupo Inteligencia.pdf`**:
  guía de marca (colores, tipografías, layout) provista por GI, en la misma
  carpeta que el doc de referencia — insumo de diseño visual, no revisado
  campo a campo en esta exploración (PDF).

## Hipótesis de solución

Dirección técnica de alto nivel — todas las decisiones de detalle quedan
para Specify:

1. **Comando dedicado de Capa 2** (ej. `/story [tipo]`) en lugar de un flag
   adicional dentro de `/apertura`/`/dato_macro`/`/alerta`/`/señal`, dado
   que el output final es un artefacto **binario** (imagen 1080×1920)
   fundamentalmente distinto del mensaje de texto WhatsApp que producen
   esos comandos hoy — el repo ya trata "texto" (`ruta_mensaje.ps1`) e
   "imagen" (`chart.md`/`data/charts/`) como dos pipelines paralelos, y un
   comando dedicado podría reutilizar (no duplicar) la lógica de datos de
   los comandos de origen. Alternativa a validar en Specify: un paso final
   opcional dentro de cada comando existente ("¿generar también la Story?"),
   simétrico al patrón ya usado por "¿Adjuntar chart de MT5?" en
   `/apertura`.
2. **Plantilla piloto única primero**: elegir 1 de las 6 (candidatas más
   fuertes por madurez de campos ya mapeados: "Indicador Macro" ↔
   `/dato_macro`, o "Market Update" ↔ `/apertura`) antes de abordar el
   mapeo campo-por-campo de las 6 — coincide con el alcance explícito del
   issue.
3. **Mecanismo de render** (decisión abierta, sin infraestructura previa
   que la incline): (a) render headless (ej. Playwright) de una copia
   adaptada del template fuera del runtime del canvas de Claude Design
   (`support.js`) — mayor fidelidad visual, nueva dependencia pesada; vs.
   (b) reimplementación nativa (Pillow / HTML-to-image) del layout de marca
   — menos dependencias, riesgo de drift respecto al manual de marca PDF si
   GI actualiza las plantillas.
4. **Reutilizar el patrón ya validado del repo** para "recibir" un binario
   generado externamente (ver `chart.md` / `chart_objects.py`): el comando
   prepara el payload de datos → el renderer (headless o script) produce el
   PNG → una función lo copia al repo con nombre canónico, análogo a
   `<activo_slug>_<TF>_<fecha_hora>.png` pero adaptado a Stories (plantilla
   + slide si aplica el carrusel de "Calendario").
5. **Flujo de aprobación** idéntico al resto del repo: preview (texto y/o
   thumbnail) → "¿Apruebas? ¿Enviar Story?" → solo tras aprobación
   explícita se genera/guarda el PNG final, sin envío automático (Evolution
   API sigue sin conectar).
6. **Regla de una sola vía** (formalizar, no solo documentar): ningún dato
   real ni lógica propia del motor se sube al proyecto Claude Design
   compartido; el render final se produce y aprueba enteramente dentro de
   este repo. Candidato a promover esta regla desde
   `plantillas-stories-gi.md` hacia `CLAUDE.md`/reglas formales del proyecto
   en la fase Design.

## Preguntas abiertas

1. Punto de entrada: ¿comando nuevo dedicado (`/story`) vs. paso/flag
   adicional dentro de los comandos existentes (`/apertura`, `/dato_macro`,
   `/alerta`, `/señal`)? El issue lo deja explícitamente abierto.
2. Mecanismo de render definitivo: Playwright headless vs. Pillow/
   HTML-to-image nativo — sin dependencias instaladas hoy, decisión 100%
   abierta y con impacto directo en `pyproject.toml` (nueva dependencia
   pesada vs. reimplementación de layout a mano).
3. ¿Qué plantilla piloto se elige primero de las 6? El issue marca el mapeo
   campo-por-campo completo como fuera de alcance de Discovery; Specify
   debe fijar la piloto y su contrato de campos exacto (ninguna de las 6
   tiene hoy el mapeo completo, solo fragmentos parciales de 3).
4. Convención de guardado del PNG resultante: ¿extender el patrón de
   `data/charts/` (issue #81, `<activo_slug>_<TF>_<fecha>.png`, PNGs
   gitignored) o crear una convención propia para Stories (con nombre de
   plantilla y, para "Calendario", número de slide del carrusel de 4)?
5. ¿Cómo se maneja el carrusel de 4 slides de la plantilla "Calendario"
   (¿una imagen por slide, generadas y aprobadas juntas, o una sola pieza
   compuesta?) — el 4º slide del canvas ni siquiera se llegó a leer/
   confirmar en la exploración previa documentada.
6. ¿El flujo de Stories necesita variante "ejecutivo" (guion interno) bajo
   el contrato `.claude/shared/modo_ejecutivo.md`, o queda fuera de la
   lista de elegibles (como `/chart`, que "genera un PNG, no texto") dado
   que su output primario ya es 100% visual para cliente?
7. ¿Dónde se formaliza la regla "solo lectura" sobre el proyecto Claude
   Design compartido? Hoy vive solo en `plantillas-stories-gi.md`; no está
   en `CLAUDE.md` ni en ninguna regla de repo — riesgo de que un agente
   futuro sin ese contexto puntual la desconozca.
8. Proceso de sincronización si GI actualiza las plantillas o el manual de
   marca (`Manual Plantilla Stories - Grupo Inteligencia.pdf`): ¿snapshot
   único versionado en este repo, o hay que prever un mecanismo de refresco
   periódico dado que el proyecto Claude Design es de otro equipo?
9. Confirmar con el director que esta Discovery, al ser trabajo técnico
   concreto que él delega (ver memoria `project_posicion_visionario_motor`
   — "no es arquitecto"), no está adelantando ninguna decisión de negocio
   de la visión más amplia (`motor-como-cerebro-hub-gi`) todavía sin
   confirmar por GI (hub en la nube, Manager API del bróker, etc.) — este
   Change debe poder avanzar y entregar valor de forma independiente de si
   esa visión mayor se aprueba o no.

## Referencias

- `docs/design/stories-gi/plantillas-stories-gi.md`
- `docs/design/stories-gi/Manual Plantilla Stories - Grupo Inteligencia.pdf`
- `docs/design/motor-como-cerebro-hub-gi.brief.md`
- `docs/design/motor-como-cerebro-hub-gi.propuesta.md`
- `.claude/commands/apertura.md`
- `.claude/commands/dato_macro.md`
- `.claude/commands/alerta.md`
- `.claude/commands/señal.md`
- `.claude/commands/chart.md`
- `.claude/shared/modo_ejecutivo.md`
- `src/market_data_mcp/tools/chart_objects.py`
- `scripts/ruta_mensaje.ps1`
- `config/activos.json`
- `pyproject.toml`
- `.gitignore`
- `.pulse/changes/archive/107-discovery-comando-ventas-oportunidad-del-d-a-para-equipo-comerci/idea.md`
  (Change precedente que diferió explícitamente este trabajo)
- GitHub issue: `bbenja11/grupo-analisis-mercado#109`
- GitHub issue relacionado: `bbenja11/grupo-analisis-mercado#107` (excluyó
  infografías de su alcance)
