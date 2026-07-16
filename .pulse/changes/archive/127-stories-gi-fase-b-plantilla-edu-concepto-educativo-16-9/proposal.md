# Proposal — Stories GI · Fase B: plantilla `edu` (concepto educativo) 16:9

Issue: #127 · Domain: `stories-gi` · Bump: feature (minor)

## Problema

La Fase B de Stories GI 16:9 llega a su **última plantilla "Simple"**: `edu`
(concepto educativo, fila 07 del catálogo). Con ella se cierra la fase junto a
`quote` (#121), `breaking` (#123) y `encuesta` (#125), ya mergeadas. La necesidad
es una pieza visual 16:9 que soporte el criterio editorial educativo de `/concepto`
y `/rencuesta` (definición + ejemplo + puntos de aplicación), sin dato de mercado,
alineada con la Misión del proyecto: pasar de un modelo de señales a uno de
análisis + educación donde el cliente aprende a leer el mercado.

## Contexto observado

- **Motor Fase A intacto** (`scripts/story_render.py`, #119): soporta viewport
  1920×1080, tokens escalares `{{clave}}`, fences `<!-- IF:x -->…<!-- ENDIF:x -->`
  (limitados a la tupla fija `_FENCES` de Alerta) y loops
  `<!-- FOR:clave -->…<!-- ENDFOR:clave -->` vía `resolver_loops`. Ningún campo de
  `edu` está en `_FENCES`, así que **el motor no se toca** (todo es aditivo).
- **`edu` es el primer consumidor real del mecanismo `FOR`** fuera de los tests
  puros del motor. El FOR ya está implementado y validado en #119
  (`tests/test_story_render.py`: `test_resolver_loops_vacio/uno/n`, fixture
  `FIXTURE_FOR_HTML`). quote/breaking/encuesta no usan FOR.
- **Regla R4/CB del motor**: el contenedor/header de una lista debe ir **fuera** del
  bloque `FOR` para persistir; con array vacío `[]` el bloque colapsa a cadena vacía
  (0 iteraciones), sin `:empty`.
- **`bullets` es un array de objetos** `{"texto": "…"}`, no strings sueltos:
  `resolver_loops` resuelve `{{campo}}` por objeto en cada repetición (mismo criterio
  que el fixture `filas: [{"nombre": …}]` de Fase A).
- **Campo opcional `kicker`**: patrón token siempre presente + CSS
  `.clase:empty{display:none}`, ya validado 3 veces (`autor_sub` en quote,
  `kicker_tema` en breaking, campos opcionales de encuesta). No requiere fence nuevo.
- **Contrato de catálogo (fila 07, design doc línea 65)**: campos `kicker`,
  `titulo_concepto`, `definicion`, `ejemplo(valor_a, operador, valor_b)`, `bullets[]`;
  sin gráfico; fondo **oscuro** (`#0D0D1A`); fuente editorial `/concepto` · `/rencuesta`.
- **`.claude/commands/story.md`**: PASO 0 (lista dura de `[tipo]`) + bloques "Ruta
  quote/breaking/encuesta" son el molde directo para "Ruta edu", con la diferencia de
  recolectar un array de bullets.

## Hipótesis de solución (aditiva, 4 archivos + motor intacto)

1. **`templates/stories/edu.html`** (nuevo, 1920×1080): reutiliza *verbatim* el
   andamiaje de marca (4 `@font-face` locales de `templates/stories/fonts/`, fondo
   oscuro `#0D0D1A`, `.story`, footer estándar + disclaimer CFD) de
   `quote/breaking/encuesta`. Cuerpo: `kicker` (chip opcional) + `titulo_concepto`
   + `definicion` + bloque `ejemplo` (tokens escalares `{{valor_a}} {{operador}}
   {{valor_b}}`) + lista `bullets` vía `<!-- FOR:bullets -->…{{texto}}…<!-- ENDFOR:bullets -->`,
   con el header/contenedor de la lista **fuera** del bloque FOR.
2. **Campo opcional `kicker`** vía patrón `:empty` (token siempre presente, `""` si no
   aplica). Núcleo obligatorio real: `titulo_concepto` + `definicion` + `ejemplo`
   (3 escalares) + `bullets` (puede ser `[]`, colapsa nativamente por el FOR).
3. **`bullets[]` como array de objetos** `[{"texto": "…"}]` — contrato de datos
   explícito, mismo criterio del fixture de Fase A.
4. **`.claude/commands/story.md`**: agregar `edu` a la lista dura de `[tipo]` del
   PASO 0 (junto a `alerta`, `quote`, `breaking`, `encuesta`) y al mensaje CB-1;
   nuevo bloque **"Ruta `edu`"** — recolección 100% editorial (título + definición +
   ejemplo + N bullets) sin `get_asset_levels`; el preview lista los bullets antes de
   aprobar; conserva el flujo preview→aprobación→render→guardado
   (`ruta_story.ps1 -Plantilla "edu" -Activo "_general"`).
5. **`tests/test_story_render.py`**: tests de mapeo puros contra el snapshot real
   (`build_html`), incluyendo caso con N bullets, caso `bullets: []` (colapsa sin
   error) y caso `kicker: ""` (sin placeholder). Sin fixture nuevo obligatorio, sin
   tocar `tests/conftest.py`.
6. **`CLAUDE.md` § "Stories GI"**: actualizar la enumeración de `[tipo]` soportados
   para incluir `edu` (cierre de Fase B: alerta, quote, breaking, encuesta, edu).
7. **Motor y contratos de `alerta/quote/breaking/encuesta`**: no se tocan.

## Criterios de aceptación (alto nivel)

- `edu.html` renderiza 1920×1080 vía `story_render.py` sin modificar el motor.
- Sin placeholders `{{`/`}}` sin resolver, con y sin `kicker`, con `bullets` en 0/1/N.
- El bloque FOR de `bullets` colapsa limpio con array vacío; el header persiste.
- `edu` registrado como `[tipo]` válido en `story.md` (PASO 0 + "Ruta edu").
- Tests de `edu` en verde en `tests/test_story_render.py`.
- `CLAUDE.md` § "Stories GI" enumera `edu`.

## Alternativas descartadas

- **Agregar un fence `IF` nuevo al motor para `kicker`**: descartado — el patrón
  `:empty` ya resuelve el opcional sin tocar `_FENCES` ni el motor.
- **Iterar `bullets` como array de strings sueltos**: descartado — `resolver_loops`
  resuelve por objeto (`{{campo}}` dentro de cada repetición), mismo patrón que Fase A.
- **Fusionar `edu` con otra plantilla pendiente de Fase C**: descartado por la
  convención firme "1 plantilla = 1 Change".

## Referencias

- `.pulse/changes/127-…/idea.md` (idea-doc de este Change).
- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md`
  (fila 07 línea 65; nota bullets/FOR línea 76; fases líneas 91-92).
- `.pulse/specs/stories-gi/spec.md` (bloques `change:119/121/123/125`).
- Changes archivados `119/121/123/125` (`.pulse/changes/archive/`).
- `scripts/story_render.py` (regex FOR, `resolver_loops`).
- `tests/test_story_render.py` (fixture `FIXTURE_FOR_HTML`, `test_resolver_loops_*`,
  `test_quote_*`).
- `templates/stories/{quote,breaking,encuesta,alerta}.html`.
- `.claude/commands/story.md` (PASO 0; Ruta quote/breaking/encuesta).
- `.claude/commands/concepto.md`, `.claude/commands/rencuesta.md` (fuente editorial).
- `CLAUDE.md` § "Stories GI".
- Issue #127; precedentes #121/#123/#125.
