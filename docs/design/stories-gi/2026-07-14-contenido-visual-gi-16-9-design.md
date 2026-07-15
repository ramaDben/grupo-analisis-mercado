# Contenido visual GI en 16:9 — las 12 plantillas del canvas producidas desde el repo

> **Estado**: diseño aprobado (brainstorming) — pendiente plan de implementación.
> **Fecha**: 2026-07-14.
> **Autor**: director de trading + Claude Code.
> **Relacionado**: [`plantillas-stories-gi.md`](./plantillas-stories-gi.md) (mapeo campo-por-campo del piloto #109), roadmap #111-#115, `CLAUDE.md` sección "Stories GI".

## Contexto

Hoy el repo genera **una** plantilla visual de marca (`/story alerta`) en formato vertical **9:16 (1080×1920)**, vía `templates/stories/alerta.html` + `scripts/story_render.py` (Playwright headless). El proyecto Claude Design compartido de Grupo Inteligencia (dueño: Rodrigo, GI) contiene una **plantilla maestra** con **12 formatos** de contenido de marca, cada uno formateable en 4 tamaños de red social — incluido **Horizontal 16:9 (1920×1080)**.

El director quiere **producir todo ese contenido desde este repo**, en **16:9**, como material para el **equipo de ejecutivos** (presentaciones, pantallas, feed interno; encaja con el "modo ejecutivo" y la visión del hub GI). Esto implica: (1) migrar el pipeline de Stories de 9:16 a 16:9, y (2) generalizar el renderer para soportar las 12 plantillas, cada una alimentada por las fuentes de datos que el repo ya tiene.

### Decisiones tomadas (brainstorming)

1. **Formato**: migrar **todo** el pipeline de Stories a **16:9 (1920×1080)**, incluida la Alerta ya implementada. Se abandona 9:16.
2. **Alcance**: las **12 plantillas** (incluida "05 Reporte Flash", alimentada con datos del propio repo, no del proyecto ajeno `flash_mcp`).
3. **Gráficos**: los 4 formatos con gráfico (Market, Macro, Alerta, Idea) usan **chart de MT5 embebido** (toggle `image-slot`, reusa el PNG de `/chart`). No se replica el SVG dibujado del canvas.
4. **Comandos**: **extender `/story [tipo]`** a 12 tipos (un solo comando), coherente con el diseño #109/#111-#115.
5. **Regla "solo lectura"** (OBLIGATORIA, sin cambios): los snapshots HTML se sincronizan a mano desde el canvas; el repo **nunca** sube datos, lógica ni configuración al proyecto Claude Design.

## Objetivo y no-objetivos

**Objetivo**: que `/story [tipo]` produzca, para cualquiera de las 12 plantillas, un PNG 1920×1080 de marca GI con datos reales del repo, listo para que un ejecutivo lo use.

**No-objetivos**:
- No se replica el motor DesignCode del canvas (`support.js`, bindings reactivos). Se convierte cada plantilla a un **snapshot HTML estático parametrizado**.
- No se sube nada al canvas (solo lectura).
- No se generan gráficos SVG con datos reales (se usa el chart de MT5 embebido).
- No se automatiza el envío (el flujo termina en "PNG aprobado, listo para adjuntar", igual que hoy).

## Arquitectura — generalizar `scripts/story_render.py`

El renderer actual ya hace `payload JSON → HTML → PNG` con un motor de plantillas mínimo (`build_context`, `build_html`, `render_png`), pero está atado a la plantilla Alerta. Cambios:

| Aspecto | Hoy (Alerta 9:16) | Generalizado (12 plantillas 16:9) |
|---|---|---|
| Viewport Playwright | `1080×1920` (hardcodeado) | **`1920×1080`** |
| Tokens escalares | lista fija `_TOKENS_ESCALARES` (campos de Alerta) | **derivados dinámicamente** de las claves escalares del payload |
| Fences condicionales | `<!-- IF:x -->…<!-- ENDIF:x -->` | se conservan tal cual |
| Repetición de filas | — (Alerta no tiene listas) | **NUEVO: `<!-- FOR:clave -->…<!-- ENDFOR:clave -->`** — itera un array de objetos del payload (cada objeto expone sus claves como tokens dentro del bloque) |
| Derivaciones | `variacion_flecha`, `sesgo_slug`, `chart_src` inline | **helpers reutilizables**: flecha `▲/▼` por `direccion`, clase de color verde/rojo por dirección/sesgo, badge `ALTO/MEDIO` por impacto |
| Snapshots | 1 (`alerta.html`) | **12** en `templates/stories/<tipo>.html` |
| Contrato de payload | 1 (Alerta) | 1 por plantilla (documentado en cada snapshot y en `plantillas-stories-gi.md`) |

**Componentes** (mantener la separación actual, testeable sin Playwright):
- `build_context(payload)` → dict de tokens escalares + derivaciones. Genérico: recorre todas las claves escalares del payload; aplica helpers de derivación cuando detecta las claves conocidas (`direccion`, `impacto`, `sesgo`, `chart_png`).
- `resolver_loops(html, payload)` → **nuevo**: expande cada `<!-- FOR:clave -->` repitiendo el bloque por cada objeto del array `payload[clave]`.
- `resolver_fences`, `sustituir_tokens`, `validar_sin_huerfanos` → como hoy (orden: loops → fences → tokens → guardia).
- `render_png(html, out, template_dir)` → viewport `1920×1080`.
- CLI: `--template`, `--out`, payload por stdin (sin cambios de interfaz).

## Catálogo de las 12 plantillas — contrato de datos y fuente

Cada plantilla comparte el esqueleto GI: chips (categoría + subcategoría + fecha/hora) → titular → bajada → bloque de datos → [gráfico] → pie (@grupointeligencia + fuente + disclaimer CFD). Campos derivados del canvas maestro.

| # / tipo | Propósito | Campos principales (payload) | Gráfico | Fondo | Fuente de datos en el repo |
|---|---|---|---|---|---|
| 01 `market` | Update de un activo en sesión | activo, clase_activo, precio, variacion(pct+direccion), maximo, minimo, volumen | chart | oscuro | `get_asset_levels` / `/apertura` |
| 02 `macro` | Publicación de dato macro | indicador, organismo, valor, valor_secundario, esperado, anterior, meta | chart | **claro** | `obtener_calendario_macro` / `/dato_macro` |
| 03 `alerta` | Aviso urgente de nivel/evento | activo, nivel_riesgo, precio, variacion, soporte, resistencia, volumen | chart | oscuro/rojo | `/alerta` (**ya existe** — migrar a 16:9) |
| 04 `idea` | Setup operativo | entrada, objetivo, stop, riesgo_beneficio, horizonte | chart | oscuro/azul | `/señal` |
| 05 `flash` | Cierre multi-activo | **filas[]**: nombre, tipo, valor, variacion(pct+direccion) | no (tabla 5) | oscuro | `get_asset_levels` × N activos |
| 06 `calendario` | Agenda semanal macro | rango_fechas, **filas[]**: dia, hora_pais, evento, impacto | no (lista 5) | oscuro | `obtener_calendario_macro` / `/dato_macro` |
| 07 `edu` | Concepto educativo | kicker, titulo_concepto, definicion, ejemplo(valor_a, operador, valor_b), **bullets[]** | no | oscuro | `/concepto` · `/rencuesta` |
| 08 `earnings` | Resultados trimestrales | ticker_trimestre, veredicto, eps_reportado, eps_esperado, ingresos, ingresos_esperado, reaccion, guia, comentario | no (métricas) | oscuro | `/earnings` |
| 09 `encuesta` | Sentimiento binario | kicker, pregunta, opcion_a, opcion_b, nota_cierre | no | oscuro/azul | `/encuesta` |
| 10 `quote` | Cita / visión de marca | cita, autor, autor_sub | no | oscuro | **editorial manual** (input del director) |
| 11 `semanal` | Ganadores/perdedores | rango_fechas, **ganadores[]** + **perdedores[]**: nombre, motivo, variacion_pct | no (2 listas) | oscuro | `/viernes_pm` |
| 12 `breaking` | Última hora con cifra | kicker_tema, titular, valor, contexto, parrafo_reaccion | no | oscuro/rojo | `/noticia` · `/alerta` |

Notas:
- **05 `flash`**: reusa solo el *layout* de "Reporte Flash GI". Los datos salen de `get_asset_levels` sobre varios activos (cierre de mercado multi-activo). No depende del proyecto ajeno `flash_mcp`.
- **10 `quote`**: sin datos del motor; el analista redacta la cita. El payload es editorial.
- **02 `macro`** es el único de fondo **claro** (#E8F5F0) — el renderer no asume fondo oscuro.
- Plantillas con `filas[]`/`ganadores[]`/`perdedores[]`/`bullets[]` requieren el nuevo mecanismo `<!-- FOR -->`.

## Interfaz de comandos

Extender `.claude/commands/story.md`: `[tipo]` acepta los 12 valores (`alerta` ya soportado). Por cada tipo, el comando:
1. Pregunta/recolecta los datos de la fuente correspondiente (tabla anterior), respetando las reglas de oro del repo (dirección clara, decimales MT5 por `config/activos.json`, hora Chile, español chileno).
2. Arma el payload JSON del tipo.
3. Muestra preview de texto y pide aprobación (nunca renderiza antes de aprobar — CB-3 del #109).
4. Al aprobar: construye la ruta con `scripts\ruta_story.ps1` (ya soporta `-Plantilla`), renderiza con `story_render.py` y muestra la ruta del PNG.

El flag `ejecutivo` sigue sin aplicar a `/story` (genera imagen, no mensaje de cliente) — igual que hoy.

## Plan de fases (implementación incremental)

- **Fase A — Motor + Alerta 16:9**: generalizar `story_render.py` (viewport 16:9, tokens dinámicos, `<!-- FOR -->`, helpers de derivación); migrar `alerta.html` a 16:9 como plantilla validadora end-to-end; actualizar `story.md`, `CLAUDE.md` (sección Stories GI: 1920×1080) y docs. Tests de mapeo puros.
- **Fase B — Simples** (sin gráfico ni listas): `quote`, `breaking`, `encuesta`, `edu`.
- **Fase C — Con listas** (`<!-- FOR -->`): `flash`, `calendario`, `semanal`, `earnings`.
- **Fase D — Con gráfico + mercado**: `market`, `idea`, `macro` (chart de MT5 embebido).

Cada plantilla nueva = 1 snapshot HTML 16:9 en `templates/stories/` + su contrato de payload documentado + su recolección de datos en `story.md` + tests de mapeo. Cada fase puede ser su propio Change/PR.

## Consideraciones

- **Regla "solo lectura"** (OBLIGATORIA): los snapshots se derivan del canvas por sincronización manual. Cuando GI actualice la plantilla maestra o el manual de marca, se re-sincronizan los snapshots afectados. El repo nunca sube nada al canvas.
- **Sincronización de marca**: documentar en `plantillas-stories-gi.md` el mapeo campo-por-campo de cada plantilla (como ya existe para Alerta) para facilitar la re-sincronización.
- **Guardado**: `data/stories/<Fecha>/<activo_slug>/<plantilla>/<Hora>_<plantilla>.png` vía `scripts\ruta_story.ps1` (sin cambios). Los `data/stories/**/*.png` siguen gitignored.
- **Playwright**: dependencia opcional (`[project.optional-dependencies] stories`), sin cambios.
- **Testing**: `build_context`/`build_html`/`resolver_loops` puros, testeables sin Chromium (patrón actual). Un test de mapeo por plantilla + un test del render (con `skipif` sin Chromium).
- **Fuente única de render**: `scripts/story_render.py` sigue siendo el único renderer; las 12 plantillas reutilizan el mismo motor.

## Decisiones de implementación

- **Recolección de datos en el prompt de `/story`** (no un helper Python). El renderer (`story_render.py`) sigue siendo un motor "tonto" (`payload → HTML → PNG`) sin lógica de negocio. Cada tipo recolecta sus datos **delegando explícitamente** en la lógica del comando fuente correspondiente (ej. "recolectá los niveles como `/apertura` PASO 4", "armá el dato como `/dato_macro` modo resultado"), en vez de reescribirla — igual que hoy `/story alerta` reusa `/alerta` y `/chart`. Motivo: gran parte del contenido es editorial/generativo (titulares, narrativa, cita, comentario) — lo produce el modelo con criterio, no un helper determinista; y los datos numéricos ya los recolectan los comandos existentes.
- **Granularidad en el ciclo Pulse**: la **Fase A** (motor generalizado + `<!-- FOR -->` + viewport 16:9 + migración de Alerta) es **un Change propio** — es el cambio arquitectónico del que dependen las otras 11 plantillas y merece un PR aislado y bien revisado. Cada **plantilla restante = su propio Change pequeño** (1 snapshot + 1 contrato + recolección + tests); no se agrupan varias por Change (PRs más chicos y revisables, sin bloqueos cruzados).
- **Orden**: complejidad creciente (Fase B simples → C con listas → D con gráfico), para no combinar `FOR` + gráfico temprano. El orden fino dentro de cada grupo se ajusta sobre la marcha.
