# Propuesta: ficha de acción individual + resumen semanal (Stories GI)

> Estado: **propuesta, sin código**. Origen: revisión del director del PDF `Programa de
> Bienvenida GI` (folleto de onboarding para ejecutivos) contra las piezas reales que produce
> este repo. Ver comparación completa en la conversación del 2026-08-12; este documento formaliza
> las dos brechas encontradas y propone cómo cerrarlas.

## 1. Contexto

El folleto `Programa_Bienvenida_GI.pdf` promete 6 beneficios del grupo de análisis (niveles
diarios, dato económico, drivers, señales ≤3/semana con TP/SL en CLP, resumen semanal, formación
continua). Los 6 tienen comando propio en el repo — no hay deuda de contenido ahí.

El folleto también incluye dos slides de ejemplo ("Grupo de señales — Análisis de acción" con
#AMD, y "Grupo de señales — Alerta macro" con la Fed) presentados como piezas visuales de marca.
Al contrastarlos con lo que el repo genera hoy:

- **Alerta macro** → calza con `templates/stories/alerta.html` (ya existe, Fase A).
- **Análisis de acción individual** → `/accion` genera exactamente ese contenido (niveles +
  qué la mueve + earnings + conexión con el índice, ver `.claude/commands/accion.md`), pero
  **solo como texto de WhatsApp**. No existe plantilla Story para ficha de acción.
- **Resumen semanal** → hoy es texto vía `/viernes_pm` (cierre semanal). La plantilla "Semanal"
  figura pendiente en el roadmap de Stories (issues #111-115, Fase D) y nunca se construyó.

Nota aparte (no es una brecha de producto, es una nota de diseño): las imágenes de ejemplo del
folleto usan una identidad visual distinta a la real (tarjetas blancas / header verde oscuro /
iconos planos) en vez del skin de marca real (`marca.css` + `piel.css`: fondo degradado oscuro,
imagen del activo, sello con pulso, Space Grotesk). Si el folleto se muestra a un prospecto, lo
que reciba después en el grupo se verá distinto. Vale la pena que quien preparó el folleto lo
sepa; no requiere cambios en este repo.

## 2. Brecha 1 — Ficha de acción individual (`accion`)

**Consumidor**: `/accion [TICKER]` — hoy termina en un mensaje de texto; la Story sería un paso
adicional opcional (mismo patrón que `/alerta` → `/story alerta`, y `/oportunidad` que genera su
propia imagen).

**Piel**: reusar `piel.css` (mismo criterio que `oportunidad`/`alerta`/`recomendacion`) porque la
acción SÍ tiene protagonista con color e imagen propios — cada acción del catálogo ya declara su
sector y puede heredar el color del índice relacionado (US100 → acento tech, US30 → acento
industrial/bancario) si no se justifica un color por-ticker.

**Campos propuestos** (derivados 1:1 de lo que `accion.md` PASO 5 ya redacta):

| Campo | Origen | Notas |
|---|---|---|
| `ticker` / `nombre_empresa` / `sector` | `config/activos.json` | chip superior, ej. `#AMD · Advanced Micro Devices · Sector tecnológico` |
| `precio_actual` | `get_asset_levels` | formateado con `digits` del activo |
| `soporte` / `resistencia` / `zona_interes` | `get_asset_levels` | mismo bloque de niveles que `alerta` |
| `sesgo` | `get_asset_levels` (trend) | píldora alcista/bajista/lateral, misma semántica `--sube`/`--baja` |
| `que_la_mueve` | WebSearch (PASO 4 de `accion.md`) | 2-3 líneas, mismo criterio "drivers analizados, no enumerados" |
| `earnings_bloque` | WebSearch | condicional: próximo (fecha + EPS esperado) O último reporte (EPS real vs esperado) — campo opcional vía token + CSS `:empty`, mismo mecanismo que otras plantillas |
| `conexion_indice` | WebSearch / `drivers_indices_sectores.json` | 1-2 líneas, ya lo redacta `accion.md` PASO 5 |
| `temporalidad` | fijo `4H — swing de jornada (1-3 días)` salvo que el director pida otra | una de las 4 etiquetas canónicas |

**No lleva**: entrada, TP, SL ni volumen — `/accion` es análisis, no señal. Si el director quiere
convertir una acción en operación, eso ya existe: `/señal` o `/story recomendacion`.

**Riesgo a resolver en diseño, no aquí**: el bloque de earnings es condicional (próximo vs
reciente vs ninguno) — el payload necesita decidir cuál de los dos textos mostrar, o dejarlo vacío
si no hay earnings relevantes en la ventana. Se resuelve como parte de la fase Design del Change,
no en esta propuesta.

## 3. Brecha 2 — Resumen semanal (`semanal`)

**Consumidor**: `/viernes_pm` (cierre semanal) — hoy solo texto.

**Piel**: no tiene activo protagonista (es multi-activo, como `calendario`) → cae al acento de
marca, mismo fallback que `calendario`/`alerta` sin color por-activo.

**Campos propuestos** (derivados del contenido que ya redacta `/viernes_pm`, a confirmar en fase
Design cuando se lea el comando completo):

| Campo | Notas |
|---|---|
| `rango_semana` | ej. `10 – 14 AGO 2026` |
| `titular` + `parrafo_sintesis` | balance de la semana, 1-2 líneas |
| Lista de activos cubiertos (loop `<!-- FOR:activos -->`) | activo, cierre semanal, variación, 1 línea de lectura — mismo patrón de loop que usa `flash` |
| `concepto_semana` (opcional) | si hubo concepto educativo, 1 línea de refuerzo |
| `preview_proxima_semana` | qué vigilar la semana siguiente (eventos macro clave) |

Es la plantilla con más superposición con `flash` (también multi-activo con loop) — en fase
Design conviene decidir si `semanal` es una variante de `flash` con secciones extra, o una
plantilla nueva. Esa decisión se toma con el patrón de datos real de `/viernes_pm` en la mano, no
a priori.

## 4. Cómo proceder (secuencia)

Mismo criterio que el resto de Stories GI: **una plantilla = un Change** (Fases B/C). Se proponen
dos Changes independientes, en paralelo:

1. `story-ficha-accion` — Explore → Specify → Design → Break-to-tasks → Apply → Review → Close.
2. `story-resumen-semanal` — mismo ciclo, en paralelo.

Cada Change entrega, como el resto: plantilla `.html` con CSS embebido (`marca.css` + `piel.css`
si aplica), fixture en `tests/fixtures/stories/payloads/<plantilla>.json`, entrada en
`rendir_todas.py`, y cobertura en `tests/test_story_render.py`.

**Este documento no crea las plantillas.** Antes de tocar `templates/stories/`, corresponde
abrir el issue/Change formal (Pulse SDD, `pulse:explore` → `pulse:specify` → `pulse:design`) para
cada una, con aprobación del director en cada fase — igual que el resto del roadmap de Stories.

## 5. Fuera de alcance de esta propuesta

- La discrepancia visual del folleto de onboarding (sección 1) — es una nota para quien preparó
  el material de ventas, no un Change de este repo.
- El "Guion del ejecutivo día a día" del folleto (Lunes-Viernes, cadencia de conversión de un
  lead) es un proceso de ventas que reutiliza comandos existentes; no requiere una plantilla
  Story nueva por sí mismo.
