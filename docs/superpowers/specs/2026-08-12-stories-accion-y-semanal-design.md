# Stories GI — ficha de acción individual + resumen semanal

> Origen: revisión del director del PDF `Programa de Bienvenida GI` contra las Stories reales.
> Ver propuesta previa en `docs/design/stories-gi/2026-08-12-propuesta-ficha-accion-resumen-semanal.md`
> (diagnóstico y campos candidatos). Este documento es el diseño detallado, listo para plan de
> implementación.

## Contexto

El folleto de onboarding muestra dos piezas de ejemplo del "grupo de señales" que hoy no existen
como Story: una ficha de análisis de acción individual (ej. #AMD) y un resumen semanal. Ambas
brechas se cierran con dos plantillas nuevas, siguiendo el patrón "una plantilla por Change" que
ya usa el resto de Stories GI (Fases A-C).

Se ejecuta **sin Pulse SDD** (decisión del director, 2026-08-12): el flujo es brainstorming →
writing-plans → implementación directa en este repo, no vía `.pulse/changes/`.

## Alcance

Dos plantillas HTML nuevas en `templates/stories/`, cada una con su fixture, su entrada en
`rendir_todas.py` y su cobertura en `test_story_render.py`. **No** se toca ningún comando
existente (`/accion`, `/viernes_pm`) más allá de dejar documentado qué payload esperaría cada
plantilla — conectar `/story accion` y `/story semanal` a los comandos reales queda fuera de esta
ronda (los comandos ya producen el contenido en texto; el payload de la Story se construye a
mano/por el director al invocar el render, igual que se hizo en las Fases A-C antes de que cada
comando generara su propio JSON).

## Diseño — `accion.html`

**Layout**: esqueleto de `alerta.html` (piel.css: sello con pulso, imagen de fondo del activo,
filete, footer estándar), con dos cambios de contenido:

- **Columna izquierda** (editorial): chips `#TICKER · Nombre empresa` + `chip_categoria` (sector).
  Tarjeta de niveles con **3 niveles** (soporte, resistencia, soporte_siguiente — folleto pide
  este tercer nivel para acciones de alta volatilidad) + píldora de sesgo, mismo patrón que
  `.tarjeta-precio`/`.tag-sesgo` de `alerta.html`.
- **Columna derecha**: reemplaza el gráfico de `alerta` por 3 bloques narrativos apilados (misma
  tipografía que `.parrafo`): `¿Qué la mueve?`, `earnings_bloque` (opcional), `Conexión con el
  índice`. Sin gráfico embebido — `/accion` no trae serie de precios hoy; agregarla es trabajo de
  otra ronda (implicaría enchufar `serie_mt5.py` a `/accion`).
- **Franja inferior** (nueva, antes del footer): "lectura práctica" de 3 colores (🟢 sobre
  resistencia / 🟡 entre niveles / 🔴 bajo soporte), como 3 celdas horizontales — visualiza lo que
  hoy el texto de WhatsApp cierra con bullets.

**Color/piel**: sin token de color propio por-acción → cae al fallback de acento de marca (mismo
criterio que piezas sin color por-activo, ej. `calendario`).

**Contrato de tokens**:

| Token | Tipo | Notas |
|---|---|---|
| `ticker` | texto | ej. `#AMD` |
| `nombre_empresa` | texto | ej. `Advanced Micro Devices` |
| `chip_categoria` | texto | sector, ej. `Sector tecnológico` |
| `rotulo_activo` | texto | igual a `alerta`: nombre visible en la tarjeta |
| `sesgo` / `sesgo_slug` | texto / slug | `alcista`/`bajista`/`lateral` — mismo mecanismo que `alerta` |
| `precio_actual` | texto ya formateado | respeta `digits` del activo |
| `soporte` / `resistencia` / `soporte_siguiente` | texto ya formateado | 3 niveles |
| `zona_interes` | texto | ej. `$523.44 – $559.02` |
| `que_la_mueve` | texto (1-3 líneas) | drivers, ya redactado por `/accion` PASO 4-5 |
| `earnings_bloque` | texto, opcional | un solo bloque ya armado (próximo con fecha+EPS esperado, o reciente con EPS real vs esperado); vacío → oculto por CSS `:empty` |
| `conexion_indice` | texto (1-2 líneas) | ya redactado por `/accion` PASO 5 |
| `temporalidad` | texto | una de las 4 etiquetas canónicas del proyecto |
| `activo_imagen` / `activo_slug` | igual a `alerta`/`oportunidad` | fallback si la acción no tiene asset propio: usar la imagen genérica de marca (a definir en fixture — ver "Riesgos") |

**No lleva**: entrada, TP, SL ni volumen — es análisis, no señal (ver `/accion.md` regla).

## Diseño — `semanal.html`

**Layout**: esqueleto centrado de `flash.html` (kicker + título + fecha, sin imagen de activo —
multi-activo, cae al acento de marca), con 3 secciones nuevas alrededor de la tabla:

1. Kicker + título + `rango_semana` (igual patrón que `flash.fecha`).
2. `parrafo_sintesis` — balance de la semana, 1-2 líneas, antes de la tabla.
3. Tabla de activos — mecanismo `<!-- FOR:filas -->` **calcado literal** de `flash.html`
   (nombre, tipo, valor, variación con flecha semántica `--alcista`/`--bajista`/`--lateral`). No
   se reinventa el loop.
4. `concepto_semana` — bloque opcional (token + CSS `:empty`), refuerzo educativo de la semana.
5. `preview_proxima_semana` — qué vigilar la semana que viene.

**Contrato de tokens**:

| Token | Tipo | Notas |
|---|---|---|
| `kicker` | texto, opcional | igual a `flash` |
| `titulo` | texto | ej. `Cierre de semana` |
| `rango_semana` | texto | ej. `10 – 14 AGO 2026` |
| `parrafo_sintesis` | texto (1-2 líneas) | |
| `filas` | loop `FOR` | cada fila: `nombre`, `tipo`, `valor`, `variacion`, `direccion` (`alcista`/`bajista`/`lateral`) — mismos nombres que `flash.html` |
| `concepto_semana` | texto, opcional | vacío → oculto por CSS `:empty` |
| `preview_proxima_semana` | texto | |

## Testing y consistencia (ambas plantillas)

- Fixture nuevo: `tests/fixtures/stories/payloads/accion.json` y `.../semanal.json`.
- Entrada nueva en `scripts/rendir_todas.py` (lista de plantillas a renderizar juntas).
- `tests/test_story_render.py` ya impone el contrato genérico (toda plantilla en
  `templates/stories/` necesita fixture y resuelve sin tokens huérfanos) — las dos plantillas
  nuevas caen bajo esa cobertura sin código de test adicional, salvo que se quiera un caso
  específico para el token opcional vacío (`earnings_bloque` / `concepto_semana`).
- `scripts/marca_tokens.py --check` no debe fallar: cero hex nuevos, todo sale de
  `marca.css`/`piel.css`.
- Ambas plantillas quedan **solo horizontal** por ahora (no se migran a responsive 9:16 en esta
  ronda) — mismo criterio que el resto de piezas no migradas a `@media (max-aspect-ratio: 1/1)`.

## Riesgos / decisiones abiertas para la fase de implementación

- **Imagen de fondo para acciones sin asset propio**: `templates/stories/assets/activos/` solo
  tiene imágenes para los 4 activos base + bitcoin. `accion.html` necesita un fallback (imagen
  genérica de marca o directamente sin `.foto-activo--fondo`, solo velo + grilla sobre fondo
  liso). Se decide al escribir el fixture, mirando qué luce mejor sin la textura fotográfica.
- **`earnings_bloque` como texto único**: ya decidido (ver pregunta de brainstorming) — el
  comando/quien arma el payload decide el texto final; la plantilla no distingue "próximo" vs
  "reciente" con CSS.
- Conectar `/accion` y `/viernes_pm` para que generen el payload JSON automáticamente queda fuera
  de esta ronda — por ahora el payload se construye a mano en el fixture y, al usarse en
  producción, el director/ejecutivo lo completa igual que se hacía en Fase A antes de que los
  comandos automatizaran su propio JSON.

## No-goals

- No se conecta `/story accion` ni `/story semanal` como subcomando invocable todavía (eso es
  responsabilidad de `.claude/commands/story.md`, fuera de esta ronda si el director no lo pide
  explícitamente en el plan).
- No se resuelve la discrepancia visual del folleto de marketing (nota aparte, no es código de
  este repo).
- No se agrega gráfico embebido a `accion.html`.
