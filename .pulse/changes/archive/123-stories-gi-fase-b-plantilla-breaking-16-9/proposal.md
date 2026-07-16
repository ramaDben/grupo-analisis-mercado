# Proposal: Stories GI · Fase B — plantilla Breaking 16:9

## Problema

El catálogo GI de 12 plantillas 16:9 tiene hoy dos plantillas reales en `master`: `alerta`
(Fase A, #119) y `quote` (Fase B, #121, cerrada, PR #122 pendiente de merge). Este Change agrega
la tercera: **`breaking`** (#12 del catálogo) — una pieza de última hora con cifra (kicker +
titular + valor + contexto + reacción), fondo oscuro/rojo, **sin gráfico y sin listas**,
alimentada por el criterio editorial de `/noticia` · `/alerta` (a diferencia de `quote`, 100%
editorial manual sin fuente de mercado, y de `alerta`, que sí trae datos en vivo de
`get_asset_levels`). Sigue el patrón "1 plantilla = 1 Change": no reabre el motor ni `quote`,
solo agrega el tercer snapshot + su `[tipo]` en `/story` + sus tests de mapeo.

## Contexto observado

**Mecanismo de fences del motor** (`scripts/story_render.py`, verificado en código, no se
modifica en este Change): `_resolver_fences`/`_fence_presente` recorren una tupla **fija**
`_FENCES = ("variacion", "vol", "chart_img", "chart_svg")` — los 4 nombres de Alerta. Ninguno
aplica a `breaking`, y el catálogo no le asigna ningún campo array, así que `resolver_loops`
(`<!-- FOR -->`) tampoco aplica. Esto confirma que, igual que `quote`, **ningún campo de
`breaking` puede condicionarse vía fence sin tocar el motor** (fuera de alcance) — todos sus
tokens son escalares incondicionales.

**Precedente inmediato `quote`** (Change #121, ya cerrado — molde directo de este documento):
`quote.html` resolvió su único campo potencialmente vacío (`autor_sub`) con **token siempre
presente en el payload + CSS `:empty { display: none; }`**, nunca con una fence nueva en el
motor. Es el patrón ya validado y confirmado como la vía correcta para "campo opcional" en
plantillas nuevas.

**Contrato de `breaking`** (catálogo, fila 12, línea 70 del design doc de 2026-07-14): payload
`kicker_tema`, `titular`, `valor`, `contexto`, `parrafo_reaccion` — sin campos array, sin
`chart_png`; sin gráfico; fondo oscuro/rojo (misma familia visual que `alerta`, a diferencia de
`quote` — oscuro sin rojo — y de `macro` — el único fondo claro del catálogo, fuera de esta
Fase); fuente editorial `/noticia` · `/alerta`: nace de un evento/noticia real, pero no delega en
`get_asset_levels` ni en ningún dato en vivo del motor. `valor` es la cifra editorial de la
noticia (dato macro, porcentaje, nivel mencionado en la nota), no un precio de mercado.

**Convenciones heredadas sin cambios** (ya citadas en `idea.md`): regla "solo lectura" del canvas
GI; `/story` fuera del flag `ejecutivo`; flujo de aprobación (preview antes de render/guardado);
`ruta_story.ps1` ya acepta `-Plantilla` genérico; "1 plantilla = 1 Change" (`breaking` no arrastra
`encuesta` ni `edu`).

## Hipótesis de solución

Alcance 100% aditivo, motor sin cambios, contrato de `alerta`/`quote` sin cambios:

1. **`templates/stories/breaking.html`** (nuevo, snapshot 1920×1080): esqueleto de marca GI
   equivalente al de `alerta.html`/`quote.html` (fuentes locales, footer estándar), paleta
   oscura/rojiza reutilizando los acentos ya usados en `alerta.html` (`#0D0D1A` de fondo,
   `#E84040` de acento, mismo degradado rojizo de `alerta.html:52-54`). Cuerpo:
   `kicker_tema` (chip/etiqueta) + `titular` + `valor` (cifra destacada, con rotulado propio que
   la distingue explícitamente de un precio en vivo — ej. etiqueta fija tipo "CIFRA CLAVE" junto
   al token, nunca el mismo tratamiento de tarjeta de precio con variación %/soporte/resistencia
   de `alerta`, para no sugerir dato de mercado en tiempo real) + `contexto` +
   `parrafo_reaccion`. Todos los tokens escalares incondicionales (ningún fence `IF`/`FOR`,
   mismo criterio que `quote`).
2. **Campos opcionales vía patrón `quote` (resuelve la pregunta abierta 1 de `idea.md`)**: por
   defecto, los 5 campos del contrato son obligatorios en el payload (siempre presentes), pero
   cualquiera que el criterio editorial de `/noticia`/`/alerta` determine que puede venir vacío
   en algún caso real (candidato más probable: `kicker_tema`, cuando la noticia no cae en una
   categoría clara) se resuelve como **token siempre presente que admite `""`** + CSS
   `:empty { display: none; }` sobre su contenedor — nunca una fence nueva en `_FENCES`. La
   decisión de *cuáles* campos concretos activan este patrón (uno, varios, o ninguno) queda para
   `specify`, con el mecanismo ya fijado aquí como único camino válido.
3. **`.claude/commands/story.md`**: agregar `breaking` a la lista dura de `[tipo]` en PASO 0
   (junto a `alerta`, `quote`) y un nuevo bloque "Ruta `breaking`". Resuelve la pregunta abierta
   4 de `idea.md`: **el bloque no ejecuta su propia búsqueda de evento** (no reusa el mecanismo
   WebSearch de `/alerta` PASO 1) — `breaking` estructura la cifra/evento que el director ya
   dictó o que ya salió de una corrida previa de `/noticia`/`/alerta` en la misma sesión; el
   comando pregunta y valida (dirección explícita, registro profesional) pero no investiga por
   cuenta propia. Esto mantiene `breaking` sin acoplarse a lógica de detección que ya vive en
   otros comandos y evita duplicar el criterio editorial. Conserva el flujo preview → aprobación
   → render → guardado (`ruta_story.ps1 -Plantilla "breaking"`).
4. **Guardado con o sin `-Activo` (resuelve la pregunta abierta 5 de `idea.md`)**: a diferencia de
   `quote` (siempre `_general`), `breaking` permite ambos casos — si la noticia tiene un activo
   protagonista claro (ej. dato de la Fed que mueve XAUUSD), el bloque de recolección pregunta el
   activo y lo pasa a `ruta_story.ps1 -Activo`; si es una cifra macro sin activo protagonista
   único (ej. IPC general), se guarda bajo `_general`, igual que `quote`. El criterio de decisión
   es editorial (lo decide el director al aprobar), no una regla automática nueva del motor.
5. **`tests/test_story_render.py`**: tests de mapeo puros para `breaking.html`
   (`build_context`/`build_html` contra el snapshot real, incluyendo el/los caso(s) de campo
   vacío que `specify` determine), análogos a los de `quote.html`. Sin fixture nuevo, sin tocar
   `conftest.py`.
6. **`CLAUDE.md`** § "Stories GI": actualizar la enumeración de `[tipo]` soportados (hoy
   `alerta`, `quote` tras el merge de #122) para incluir `breaking`.
7. **Documentación de mapeo campo-por-campo** (resuelve la pregunta abierta 2 de `idea.md`):
   queda **fuera de alcance** de este Change agregar una sección dedicada a `breaking` en
   `docs/design/stories-gi/plantillas-stories-gi.md` — el alcance fijado del Change enumera
   explícitamente `templates/stories/breaking.html` + `story.md` + tests + `CLAUDE.md`, sin ese
   documento. El contrato de campos vive en el design doc de 2026-07-14 (fila 12) y en el
   `design.md` que se produzca en `specify`/`design`, igual que ya ocurrió con `quote` (su
   `proposal.md`/`spec.md` tampoco tocó `plantillas-stories-gi.md`).
8. Motor (`build_context`, `resolver_loops`, `_FENCES`, `render_png`) y contratos de `alerta`/
   `quote` **no se tocan**.

## Preguntas abiertas

- Cuáles de los 5 campos (`kicker_tema`, `titular`, `valor`, `contexto`, `parrafo_reaccion`)
  activan en la práctica el patrón "token + `:empty`" (punto 2 de la hipótesis) — a confirmar en
  `specify` contra casos reales de `/noticia`/`/alerta`; el mecanismo ya está fijado, falta solo
  el inventario exacto de campos.
- Tratamiento tipográfico/rotulado exacto de `valor` para distinguirlo visualmente de un precio
  de mercado (punto 1 de la hipótesis apunta una dirección — etiqueta fija tipo "CIFRA CLAVE" —
  pero el detalle CSS/copy se resuelve al autorar el HTML en `apply`, no bloquea `specify`).
- Redacción exacta de las preguntas de recolección del bloque "Ruta `breaking`" en `story.md`
  (cómo pregunta el director si ya corrió `/noticia`/`/alerta` antes, o si dicta la cifra desde
  cero) — detalle de UX del comando, a definir en `specify`.
- Límite recomendado de longitud de `titular`/`parrafo_reaccion` para no desbordar el layout
  1920×1080 (mismo tipo de guía que `quote` dejó pendiente para `cita`) — a fijar en `specify`
  con prueba visual del snapshot.

## Referencias

- `.pulse/changes/123-stories-gi-fase-b-plantilla-breaking-16-9/idea.md` — idea-doc base de esta
  propuesta (contexto completo, 5 preguntas originales).
- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — fila 12 `breaking`:
  payload `kicker_tema, titular, valor, contexto, parrafo_reaccion`, sin gráfico, fondo
  oscuro/rojo, fuente `/noticia` · `/alerta`.
- `.pulse/specs/stories-gi/spec.md` — spec del dominio; contratos ya formalizados de
  `story_alerta` (#109/#119) y `story_quote` (#121) como precedente directo de formato.
- `.pulse/changes/archive/121-stories-gi-fase-b-plantilla-quote-16-9/idea.md`, `proposal.md`,
  `design.md`, `spec.md` — Change antecedente inmediato (misma Fase B): confirma el patrón
  "1 snapshot + 1 bloque de recolección + tests de mapeo puros + `CLAUDE.md`", el patrón de campo
  opcional (token + `:empty`) y la convención "1 plantilla = 1 Change".
- `.pulse/changes/archive/119-stories-gi-fase-a-motor-de-render-16-9-migrar-plantilla-alerta/` —
  Change fundacional del motor (no se reabre).
- `scripts/story_render.py` — motor 16:9 generalizado, no se modifica.
- `templates/stories/alerta.html` — referencia de paleta oscura/rojiza que `breaking` reutiliza.
- `templates/stories/quote.html` — molde más cercano: plantilla simple sin fences/loops, con
  campo opcional resuelto vía `:empty` CSS.
- `.claude/commands/story.md` — comando a extender (PASO 0 + nuevo bloque "Ruta `breaking`").
- `tests/test_story_render.py` — suite a extender con tests de mapeo puros para `breaking`.
- `CLAUDE.md` § "Stories GI" — actualizar la enumeración de tipos soportados.
- `.claude/shared/modo_ejecutivo.md` — confirma `/story` en "No elegibles", sin cambios.
- Issue #123 (GitHub, `bbenja11/grupo-analisis-mercado`) — issue madre de esta Fase B ·
  `breaking`; issues #121 (quote, precedente cerrado) y #119 (motor, fundacional).
