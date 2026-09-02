# Piel compartida de Stories GI — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extraer la piel visual de `oportunidad` a una hoja compartida y aplicarla a `alerta` y `recomendacion`, sin tocar la estructura ni los campos editoriales de ninguna de las tres.

**Architecture:** Nace `templates/stories/piel.css`, hermano de `marca.css`, con las capas de fondo, la tipografía, el sello y el CTA. Las tres plantillas la enlazan; `oportunidad` además pierde esas reglas de su `<style>` para no quedar como excepción. El renderer no cambia: los campos nuevos (`activo_slug`, `activo_imagen`) son claves planas que `build_context` ya copia tal cual.

**Tech Stack:** HTML + CSS estáticos, Playwright headless (`scripts/story_render.py`), pytest, `uv`.

**Spec:** `docs/superpowers/specs/2026-08-07-piel-compartida-stories-design.md`

## Global Constraints

- **Colores por rol, nunca hex a mano.** Todo color sale de `var(--rol)` de `marca.css`. `uv run python scripts/marca_tokens.py --check` debe pasar al final de cada tarea.
- **`--activo` es identidad, `--sube`/`--baja` es dirección.** Nunca se colapsan. Una pieza dorada bajista debe verse dorada y bajista a la vez.
- **El cromo no opina.** Si un color no comunica un número, va en el acento o en el color del activo. Nunca se baña la pieza en rojo por ser bajista.
- **Orden de carga fijo:** `marca.css` → `piel.css` → `<style>` de la plantilla. Cada capa puede anular la anterior.
- **Ninguna estructura cambia.** No se agregan, quitan ni reordenan bloques de contenido en `alerta` ni en `recomendacion`. La firma acreditada de `recomendacion` no se mueve ni se achica.
- **Los campos nuevos degradan sin romper:** un payload sin `activo_slug`/`activo_imagen` rinde la pieza con la piel nueva, en color de marca y sin foto.
- **Comandos de test** (desde la raíz del repo):
  - `uv run pytest tests/test_story_render.py tests/test_marca_tokens.py -v`
  - `uv run python scripts/marca_tokens.py --check`
  - `uv run --extra stories python scripts/rendir_todas.py` (y `--formato vertical`)

---

## File Structure

| Archivo | Responsabilidad |
|---|---|
| `templates/stories/piel.css` (nuevo) | Capas de fondo, `@font-face`, sello, CTA, footer. Solo lo que no depende de qué dice la pieza. |
| `templates/stories/oportunidad.html` | Pierde las reglas que se fueron a la hoja; conserva su layout de hero, cifras y evidencia. |
| `templates/stories/alerta.html` | Enlaza la hoja; conserva sus dos columnas, tarjeta de niveles y gráfico legible. |
| `templates/stories/recomendacion.html` | Enlaza la hoja; conserva tarjeta de operación, gráfico con tres niveles y firma. |
| `scripts/marca_tokens.py` | Extiende el `--check` a los `.css` de la carpeta (hoy solo mira `*.html`). |
| `tests/test_piel_compartida.py` (nuevo) | Contrato de la hoja: existe, la enlazan las tres, nadie duplica sus reglas. |
| `tests/fixtures/stories/payloads/{alerta,recomendacion}.json` | Ganan `activo_slug` y `activo_imagen`. |
| `.claude/commands/{alerta,story}.md` · `CLAUDE.md` | Documentan los campos nuevos. |

---

## Task 1: La hoja `piel.css` y su consumidor de referencia

Crea la hoja, la hace consumir por `oportunidad` (que es quien definió el estándar) y extiende el gate de color para que cubra archivos `.css`. Sin este último paso, un hex suelto en la hoja nueva pasaría inadvertido justo donde más importa.

**Files:**
- Create: `templates/stories/piel.css`
- Create: `tests/test_piel_compartida.py`
- Modify: `templates/stories/oportunidad.html` (quita reglas, agrega `<link>`)
- Modify: `scripts/marca_tokens.py`
- Modify: `tests/test_marca_tokens.py`

**Interfaces:**
- Produces: la hoja `piel.css` con las clases `.escenario`, `.foto-activo`, `.ilustracion`, `.velo`, `.grilla`, `.capa`, `.sello`, `.pulso`, `.cta`, `.cta-flecha`, `.cta-titulo`, `.cta-sub`, `.cta-marca`, `.cta-handle`, `.cta-logo`, `.disclaimer` y los `@font-face` de Space Grotesk (600/700/800) y DM Sans (400/700). Las tareas 2 y 3 consumen estos nombres exactos.
- Produces: `marca_tokens._hojas() -> list[Path]` — los `.css` de `templates/stories/` **excluyendo `marca.css`**, que es la fuente de los hex y debe quedar fuera del escaneo.

- [ ] **Step 1: Escribir el test que exige la hoja y su consumo**

Crear `tests/test_piel_compartida.py`:

```python
"""La piel visual vive en una hoja compartida, no en tres copias."""
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
DIR_STORIES = _REPO_ROOT / "templates" / "stories"
PIEL_CSS = DIR_STORIES / "piel.css"

# Las tres plantillas de la familia. Las otras siete migran en Changes aparte
# (ver §6 de la spec): una plantilla por vez, porque cada una tiene su propia
# calibración de alturas.
FAMILIA = ("oportunidad.html", "alerta.html", "recomendacion.html")

# Reglas que, por definición, viven en la hoja. Si una plantilla las redeclara,
# volvemos a tener copias desincronizadas — que es exactamente lo que la hoja
# existe para evitar.
REGLAS_DE_LA_PIEL = (".velo {", ".grilla {", ".sello {", ".pulso {", ".cta-flecha {")


def test_la_hoja_existe():
    assert PIEL_CSS.exists(), "falta templates/stories/piel.css"


def test_la_hoja_declara_las_capas_de_fondo():
    css = PIEL_CSS.read_text(encoding="utf-8")

    for clase in (".foto-activo", ".velo", ".grilla", ".sello", ".pulso", ".cta"):
        assert clase in css, f"falta {clase} en piel.css"


def test_la_hoja_declara_las_fuentes():
    css = PIEL_CSS.read_text(encoding="utf-8")

    assert css.count("@font-face") >= 5
    assert "space-grotesk-700.woff2" in css
    assert "dm-sans-400.woff2" in css


def test_la_familia_enlaza_la_hoja():
    for nombre in FAMILIA:
        html = (DIR_STORIES / nombre).read_text(encoding="utf-8")
        assert 'href="piel.css"' in html, f"{nombre} no enlaza piel.css"


def test_la_hoja_se_carga_despues_de_marca():
    # marca.css define los tokens que piel.css consume: al revés, `var(--activo)`
    # resolvería a nada.
    for nombre in FAMILIA:
        html = (DIR_STORIES / nombre).read_text(encoding="utf-8")
        assert html.index('href="marca.css"') < html.index('href="piel.css"'), (
            f"{nombre} carga piel.css antes que marca.css"
        )


def test_ninguna_plantilla_redeclara_la_piel():
    for nombre in FAMILIA:
        html = (DIR_STORIES / nombre).read_text(encoding="utf-8")
        duplicadas = [regla for regla in REGLAS_DE_LA_PIEL if regla in html]
        assert not duplicadas, f"{nombre} redeclara reglas de la piel: {duplicadas}"
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `uv run pytest tests/test_piel_compartida.py -v`
Expected: FAIL — `test_la_hoja_existe` con "falta templates/stories/piel.css".

- [ ] **Step 3: Crear `templates/stories/piel.css`**

Mover **textualmente** desde el `<style>` de `oportunidad.html` estos bloques, conservando sus comentarios (explican decisiones que costaron rondas de revisión y no deben perderse): los cinco `@font-face`, `.escenario`, `.foto-activo`, `.ilustracion`, `.velo`, `.grilla`, `.capa`, `.sello`, `.pulso`, `.cta` y sus partes, `.disclaimer`, más las reglas de esos mismos selectores dentro del `@media (max-aspect-ratio: 1/1)`.

Encabezar el archivo así:

```css
/*
  Piel de las Stories GI — la línea visual que comparten las piezas.

  Nace de `oportunidad`, la plantilla del rediseño de agosto de 2026 (ver
  docs/superpowers/specs/2026-08-07-piel-compartida-stories-design.md). Antes
  de esta hoja, adoptar esa línea en otra plantilla era copiar ~120 líneas de
  CSS; a la tercera copia, una queda atrás y sale una pieza descoordinada. Es
  la misma razón por la que existe marca.css.

  ── Qué entra acá y qué no ───────────────────────────────────────────────────
  Entra lo que NO depende de qué dice la pieza: capas de fondo, tipografía,
  sello, CTA, disclaimer. Se queda en cada plantilla el layout de columnas, los
  tamaños de cada bloque y todo lo que sea contenido.

  ── Orden de carga ───────────────────────────────────────────────────────────
  marca.css -> piel.css -> <style> de la plantilla. marca.css va primero porque
  define los tokens que esta hoja consume; el <style> va último para que una
  plantilla siempre pueda excepcionar.

  Resuelve por ruta relativa porque story_render.py escribe el HTML DENTRO de
  templates/stories/ y lo navega con file://, igual que marca.css y fonts/.

  ── Color ────────────────────────────────────────────────────────────────────
  Esta hoja usa `var(--activo)` —identidad— y nunca `--sube`/`--baja`
  —dirección—. La dirección la pintan las plantillas, donde ES el dato.
*/
```

- [ ] **Step 4: Quitar de `oportunidad.html` las reglas movidas y enlazar la hoja**

Agregar bajo el `<link>` de marca:

```html
<link rel="stylesheet" href="piel.css">
```

Borrar del `<style>` exactamente los bloques movidos en el Step 3, incluidos los del `@media`. **No tocar** `.hero`, `.activo-nombre`, `.direccion`, `.titular`, `.razon`, `.cifras`, `.precio`, `.evidencia*` ni las clases `.g-*`: son estructura y contenido de esta plantilla.

- [ ] **Step 5: Verificar que `oportunidad` rinde idéntica**

Run: `uv run --extra stories python scripts/story_render.py --template templates/stories/oportunidad.html --out /tmp/op.png < tests/fixtures/stories/payloads/oportunidad.json`

Si el payload trae `recorrido`, encadenar primero el gráfico:

Run: `uv run python scripts/story_grafico.py < tests/fixtures/stories/payloads/oportunidad.json | uv run --extra stories python scripts/story_render.py --template templates/stories/oportunidad.html --out /tmp/op.png`

Expected: PNG de 1920×1080 sin error de tokens huérfanos. Abrirlo y comparar contra el render anterior: **debe verse igual**. Si algo se movió, falta una regla por mover.

- [ ] **Step 6: Extender el gate de color a los `.css`**

En `scripts/marca_tokens.py`, junto a `_plantillas()`:

```python
def _hojas() -> list[Path]:
    """Hojas de estilo propias, EXCEPTO marca.css.

    marca.css queda fuera a propósito: es la fuente de los hex y el único
    archivo donde escribirlos es correcto. Cualquier otra hoja —hoy piel.css—
    debe consumir `var(--rol)` como lo hacen las plantillas.
    """
    return sorted(p for p in DIR_STORIES.glob("*.css") if p.name != HOJA)
```

Y dentro del bucle de `main`, después de recorrer las plantillas, solo en modo `--check`:

```python
    if args.check:
        for ruta in _hojas():
            css = ruta.read_text(encoding="utf-8")
            _, n, huerfanos = _tokenizar(css)
            if n or huerfanos:
                problemas += 1
                detalle = []
                if n:
                    detalle.append(f"{n} color(es) hardcodeado(s)")
                if huerfanos:
                    detalle.append(f"sin rol: {sorted(set(huerfanos))}")
                print(f"FALLA {ruta.name}: {'; '.join(detalle)}")
            else:
                print(f"ok    {ruta.name}")
```

- [ ] **Step 7: Escribir el test del gate extendido**

Agregar a `tests/test_marca_tokens.py`:

```python
def test_el_gate_cubre_las_hojas_propias():
    hojas = [p.name for p in marca_tokens._hojas()]

    assert "piel.css" in hojas, "el gate no está escaneando piel.css"
    # marca.css es la fuente de los hex: escanearla la reportaría entera como
    # infracción.
    assert "marca.css" not in hojas


def test_ninguna_hoja_propia_hardcodea_color():
    for hoja in marca_tokens._hojas():
        css = hoja.read_text(encoding="utf-8")
        _, n, huerfanos = marca_tokens._tokenizar(css)
        assert not n and not huerfanos, f"{hoja.name} trae color a mano: {huerfanos or n}"
```

- [ ] **Step 8: Correr toda la verificación**

Run: `uv run pytest tests/test_piel_compartida.py tests/test_marca_tokens.py tests/test_story_render.py -v`
Expected: PASS.

Run: `uv run python scripts/marca_tokens.py --check`
Expected: exit 0, con una línea `ok piel.css`.

- [ ] **Step 9: Commit**

```bash
git add templates/stories/piel.css templates/stories/oportunidad.html scripts/marca_tokens.py tests/test_piel_compartida.py tests/test_marca_tokens.py
git commit -m "feat(stories): la piel visual sale a piel.css, hermano de marca.css

Adoptar la línea de `oportunidad` en otra plantilla era copiar ~120 líneas
de CSS. A la tercera copia una queda atrás y sale una pieza descoordinada,
que es la razón por la que ya existía marca.css.

`oportunidad` es la primera en consumirla y pierde esas reglas de su
<style>: si la plantilla que definió el estándar no lo consume, la hoja se
desincroniza de ella al primer ajuste.

El gate de color pasa a escanear los .css de la carpeta —marca.css queda
fuera, que es donde los hex sí van—. Sin esto, un color a mano en la hoja
nueva pasaba inadvertido justo donde más importa."
```

---

## Task 2: `alerta` adopta la piel

**Files:**
- Modify: `templates/stories/alerta.html`
- Modify: `tests/fixtures/stories/payloads/alerta.json`
- Modify: `tests/test_story_render.py`

**Interfaces:**
- Consumes: las clases de `piel.css` de la Tarea 1 y los tokens `--activo` / `body.activo-<slug>` que ya viven en `marca.css`.
- Produces: el par de campos `activo_slug` / `activo_imagen` como convención de payload, que la Tarea 3 repite y la Tarea 4 documenta.

- [ ] **Step 1: Escribir los tests de la piel en alerta**

Agregar a `tests/test_story_render.py`, junto a los demás tests de alerta:

```python
def test_alerta_pinta_el_color_del_activo():
    payload = json.loads((FIXTURES_DIR / "payloads" / "alerta.json").read_text(encoding="utf-8"))
    payload["chart_png"] = None

    html = story_render.build_html(payload, ALERTA_TEMPLATE)

    # La clase en <body> es lo que hace cascadear `--activo` desde marca.css.
    assert 'activo-oro' in html


def test_alerta_sin_activo_slug_no_rompe():
    # Degradación deliberada: no todo activo tiene color asignado, y la pieza
    # tiene que salir igual —en el acento de marca, que es el neutro definido
    # en marca.css—.
    payload = json.loads((FIXTURES_DIR / "payloads" / "alerta.json").read_text(encoding="utf-8"))
    payload["chart_png"] = None
    payload["activo_slug"] = ""
    payload["activo_imagen"] = ""

    html = story_render.build_html(payload, ALERTA_TEMPLATE)

    assert "{{" not in _body(html)


def test_alerta_conserva_sus_niveles_visibles():
    # El gráfico de alerta es CONTENIDO, no atmósfera: sus niveles de soporte y
    # resistencia son el dato que el cliente busca. Si alguien lo convierte en
    # escenario a sangre, este test cae.
    html = ALERTA_TEMPLATE.read_text(encoding="utf-8")

    assert ".g-nivel-soporte" in html
    assert ".g-nivel-resistencia" in html
    assert ".g-precio" in html
```

`ALERTA_TEMPLATE` ya está declarada en la línea 29 del archivo y la usan los tests
de alerta existentes. `_body()` (línea 742) y `json` también están disponibles.

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `uv run pytest tests/test_story_render.py -k alerta -v`
Expected: FAIL en `test_alerta_pinta_el_color_del_activo` — el `<body>` de alerta no lleva clase de activo.

- [ ] **Step 3: Agregar los campos a la fixture**

En `tests/fixtures/stories/payloads/alerta.json`, junto a `chip_categoria`:

```json
 "activo_slug": "oro",
 "activo_imagen": "assets/activos/oro.jpg",
```

- [ ] **Step 4: Aplicar la piel a `alerta.html`**

1. Enlazar la hoja bajo el `<link>` de marca: `<link rel="stylesheet" href="piel.css">`.
2. Cambiar el `<body>` a: `<body class="sesgo-{{sesgo_slug}} activo-{{activo_slug}}">`.
3. Agregar, como primeros hijos de `.story`, las capas de fondo:

```html
    <img class="foto-activo" src="{{activo_imagen}}" alt="">
    <div class="velo"></div>
    <div class="grilla"></div>
```

4. Borrar el `@font-face` de Syne: está declarado y **ninguna regla lo usa** (verificado sobre el archivo completo). Es peso muerto. Borrar también los de DM Sans y Space Grotesk, que ahora vienen de la hoja.
5. Reemplazar el bloque `.chips` por el sello de la piel, conservando el texto:

```html
        <div class="chips">
          <span class="sello"><span class="pulso"></span>Alerta de mercado</span>
          <span class="chip chip-categoria">{{chip_categoria}}</span>
        </div>
```

6. En el CSS propio de la plantilla, cambiar a `var(--activo)` el cromo que hoy va en `var(--acento)`: `.chip-categoria`, el borde de `.tarjeta-precio`, `.sello-datos` y las clases del gráfico `.g-area-alto`, `.g-area-bajo`, `.g-linea`.
7. Subir el `z-index` del contenido sobre las capas: agregar `position: relative; z-index: 2;` a `.contenido` y a `.footer`.
8. Cambiar `.titular` a `font-family: "Space Grotesk", sans-serif; font-weight: 800;`.

**No tocar:** `.tag-sesgo--*`, `.variacion`, `.g-nivel-soporte`, `.g-nivel-resistencia`, `.g-precio-soporte`, `.g-precio-resistencia`. Ahí el verde y el rojo **son** el dato.

- [ ] **Step 5: Correr los tests**

Run: `uv run pytest tests/test_story_render.py -k alerta -v`
Expected: PASS.

- [ ] **Step 6: Verificar el render en ambos formatos**

Run:
```bash
uv run python scripts/story_grafico.py < tests/fixtures/stories/payloads/alerta.json \
  | uv run --extra stories python scripts/story_render.py --template templates/stories/alerta.html --out /tmp/alerta_h.png
uv run python scripts/story_grafico.py < tests/fixtures/stories/payloads/alerta.json \
  | uv run --extra stories python scripts/story_render.py --template templates/stories/alerta.html --out /tmp/alerta_v.png --formato vertical
```

Expected: 1920×1080 y 1080×1920. Abrir ambos y confirmar tres cosas: la foto del oro se ve **detrás** del texto y no lo tapa; los niveles del gráfico siguen legibles; nada desborda sobre el footer.

- [ ] **Step 7: Verificar el gate y el suite completo**

Run: `uv run python scripts/marca_tokens.py --check && uv run pytest tests/ -v`
Expected: exit 0 y toda la suite verde.

- [ ] **Step 8: Commit**

```bash
git add templates/stories/alerta.html tests/fixtures/stories/payloads/alerta.json tests/test_story_render.py
git commit -m "feat(stories): alerta adopta la piel compartida

Gana las capas de fondo, el sello con pulso y el color del activo en el
cromo. Conserva su estructura completa: las dos columnas, la tarjeta de
niveles y el gráfico legible con soporte y resistencia rotulados —ahí los
niveles son el dato que el cliente busca, no atmósfera—.

El @font-face de Syne se va porque ninguna regla lo usaba: las dos
plantillas de esta familia ya escribían todo en DM Sans y Space Grotesk.

activo_slug y activo_imagen degradan sin romper: sin ellos la pieza sale en
el acento de marca y sin foto, que es lo que corresponde para un activo sin
identidad asignada."
```

---

## Task 3: `recomendacion` adopta la piel, con la firma protegida

**Files:**
- Modify: `templates/stories/recomendacion.html`
- Modify: `tests/fixtures/stories/payloads/recomendacion.json`
- Modify: `tests/test_story_render.py`

**Interfaces:**
- Consumes: `piel.css` (Tarea 1) y la convención `activo_slug` / `activo_imagen` (Tarea 2).

- [ ] **Step 1: Escribir los tests**

Agregar a `tests/test_story_render.py`:

```python
def test_recomendacion_pinta_el_color_del_activo():
    payload = json.loads(
        (FIXTURES_DIR / "payloads" / "recomendacion.json").read_text(encoding="utf-8")
    )

    html = story_render.build_html(payload, RECOMENDACION_TEMPLATE)

    assert "activo-eurusd" in html


def test_recomendacion_conserva_la_firma_acreditada():
    # La firma es lo que separa una pieza del área de una imagen anónima
    # circulando por WhatsApp. La piel no la puede desplazar ni tapar.
    payload = json.loads(
        (FIXTURES_DIR / "payloads" / "recomendacion.json").read_text(encoding="utf-8")
    )

    html = story_render.build_html(payload, RECOMENDACION_TEMPLATE)

    assert payload["firma_nombre"] in html
    assert payload["firma_credencial"] in html
    assert payload["firma_area"] in html


def test_recomendacion_conserva_los_tres_niveles_del_grafico():
    # Entrada, objetivo y stop son donde se lee el riesgo/beneficio sin hacer
    # la división. A sangre y sin rótulos esa lectura desaparece.
    html = RECOMENDACION_TEMPLATE.read_text(encoding="utf-8")

    for clase in (".g-nivel-entrada", ".g-nivel-meta", ".g-nivel-stop"):
        assert clase in html, f"falta {clase}"


def test_recomendacion_sin_activo_slug_no_rompe():
    payload = json.loads(
        (FIXTURES_DIR / "payloads" / "recomendacion.json").read_text(encoding="utf-8")
    )
    payload["activo_slug"] = ""
    payload["activo_imagen"] = ""

    html = story_render.build_html(payload, RECOMENDACION_TEMPLATE)

    assert "{{" not in _body(html)
```

`RECOMENDACION_TEMPLATE` **no existe todavía**: `recomendacion` solo estaba cubierta
por el barrido genérico `PLANTILLAS` (línea 1176), sin constante propia. Declararla
junto a `ALERTA_TEMPLATE`, en la línea 30:

```python
RECOMENDACION_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "recomendacion.html"
```

- [ ] **Step 2: Correr los tests y verificar que fallan**

Run: `uv run pytest tests/test_story_render.py -k recomendacion -v`
Expected: FAIL en `test_recomendacion_pinta_el_color_del_activo`.

- [ ] **Step 3: Agregar los campos a la fixture**

En `tests/fixtures/stories/payloads/recomendacion.json`, junto a `chip_categoria`:

```json
 "activo_slug": "eurusd",
 "activo_imagen": "",
```

`activo_imagen` va vacío a propósito: no hay foto de EUR/USD en `assets/activos/`, y la fixture debe ejercitar el caso de degradación, que es el más frecuente hoy. `eurusd` tampoco tiene color en `marca.css`, así que la pieza cae al acento de marca — que es justo el comportamiento neutro que hay que poder ver renderizado.

- [ ] **Step 4: Aplicar la piel a `recomendacion.html`**

Mismos seis movimientos que en `alerta`:

1. `<link rel="stylesheet" href="piel.css">` bajo el de marca.
2. `<body class="sesgo-{{sesgo_slug}} activo-{{activo_slug}}">`.
3. Capas de fondo como primeros hijos de `.story`:

```html
    <img class="foto-activo" src="{{activo_imagen}}" alt="">
    <div class="velo"></div>
    <div class="grilla"></div>
```

4. Borrar los cuatro `@font-face` (Syne incluido, sin uso).
5. Sello en lugar del chip plano, conservando el texto:

```html
      <div class="chips">
      <span class="sello"><span class="pulso"></span>Recomendación</span>
      <span class="chip chip-categoria">{{chip_categoria}}</span>
      </div>
```

6. `.titular` a Space Grotesk 800. Cromo a `var(--activo)` en `.chip-categoria`, el borde de `.tarjeta`, `.sello-datos`, `.tesis-rotulo`, `.firma-rotulo`, el `border-top` de `.firma` y las clases `.g-area-alto`, `.g-area-bajo`, `.g-linea`.
7. `position: relative; z-index: 2;` en `.cabecera`, `.contenido` y `.footer`.

**No tocar:** `.tag-direccion`, `.objetivo--tp`, `.objetivo--sl`, `.g-nivel-meta`, `.g-nivel-stop`, `.g-precio-meta`, `.g-precio-stop`. El objetivo es siempre la ganancia y el stop siempre la pérdida, en compra y en venta.

- [ ] **Step 5: Proteger la legibilidad de la firma**

Agregar al `<style>` propio de la plantilla, después de las reglas de `.firma`:

```css
  /* La piel se subordina a la firma (§D2 de la spec). El bloque de firma lleva
     su propio fondo opaco: es lo que hace responsable a esta pieza, y una foto
     de fondo detrás de un nombre y una credencial las vuelve dudosas de leer
     justo donde no se puede dudar. */
  .firma {
    position: relative;
    z-index: 3;
    background: rgba(8, 8, 12, 0.86);
    border-radius: 16px;
    padding: 22px 24px;
    margin-left: -24px;
    margin-right: -24px;
  }
```

- [ ] **Step 6: Correr los tests**

Run: `uv run pytest tests/test_story_render.py -k recomendacion -v`
Expected: PASS.

- [ ] **Step 7: Verificar el render y medir la legibilidad**

Run:
```bash
uv run python scripts/story_grafico.py < tests/fixtures/stories/payloads/recomendacion.json \
  | uv run --extra stories python scripts/story_render.py --template templates/stories/recomendacion.html --out /tmp/reco_h.png
uv run python scripts/story_grafico.py < tests/fixtures/stories/payloads/recomendacion.json \
  | uv run --extra stories python scripts/story_render.py --template templates/stories/recomendacion.html --out /tmp/reco_v.png --formato vertical
```

Expected: 1920×1080 y 1080×1920. Abrir ambos y confirmar: la firma se lee sin esfuerzo con su fondo propio; el gráfico conserva las tres líneas rotuladas; el disclaimer del footer sigue legible; nada desborda.

Con una fixture de activo con foto (cambiar `activo_slug` a `oro` y `activo_imagen` a `assets/activos/oro.jpg` en una copia temporal), repetir la verificación: es el caso donde el fondo puede comprometer la firma.

- [ ] **Step 8: Verificar el gate y el suite completo**

Run: `uv run python scripts/marca_tokens.py --check && uv run pytest tests/ -v`
Expected: exit 0 y suite verde.

- [ ] **Step 9: Revisión visual de la familia completa**

Run:
```bash
uv run --extra stories python scripts/rendir_todas.py
uv run --extra stories python scripts/rendir_todas.py --formato vertical
```

Expected: las 11 piezas rinden. Mirar las tres de la familia juntas: **deben leerse como la misma casa**. Los defectos de consistencia no se ven revisando de a una.

- [ ] **Step 10: Commit**

```bash
git add templates/stories/recomendacion.html tests/fixtures/stories/payloads/recomendacion.json tests/test_story_render.py
git commit -m "feat(stories): recomendacion adopta la piel, con la firma protegida

Mismo tratamiento que alerta, con una excepción explícita: el bloque de
firma lleva fondo propio y sube sobre las capas. Una foto de fondo detrás de
un nombre y una credencial las vuelve dudosas de leer, y la firma es
justamente lo que separa una pieza del área de una imagen anónima circulando
por WhatsApp. La piel se subordina a ella, no al revés.

Conserva el gráfico con entrada, objetivo y stop rotulados: ahí se lee el
riesgo/beneficio sin hacer la división.

La fixture usa un activo sin color ni foto asignados a propósito —es el caso
de degradación y hoy el más frecuente—."
```

---

## Task 4: Documentar la convención

Sin este paso, los comandos siguen emitiendo payloads sin los campos nuevos y las piezas salen en gris pese a todo el trabajo anterior.

**Files:**
- Modify: `.claude/commands/alerta.md`
- Modify: `.claude/commands/story.md`
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: la convención `activo_slug` / `activo_imagen` de las Tareas 2 y 3.

- [ ] **Step 1: Documentar los campos en `/alerta`**

Agregar a la tabla de campos del payload de `.claude/commands/alerta.md`:

```markdown
| `activo_slug` | Identidad cromática: `oro`, `wti`, `us100`, `usdclp`. Sale de `lowercase(ticker_mt5)` sin `.spot`/`#`/`/`, igual que el slug de `ruta_mensaje.ps1`. Un activo sin color asignado va vacío y la pieza sale en el acento de marca. |
| `activo_imagen` | `assets/activos/<slug>.jpg` si existe la imagen; cadena vacía si no. Nunca inventar una ruta: un `src` roto deja un ícono de imagen rota en la pieza. |
```

- [ ] **Step 2: Documentar los campos en `/story`**

En la sección de `.claude/commands/story.md` que arma los payloads de `alerta` y `recomendacion`, agregar las dos mismas filas, más esta nota:

```markdown
**Identidad del activo (plantillas `alerta`, `recomendacion` y `oportunidad`)**:
`activo_slug` pinta el escenario y `activo_imagen` lo ilustra. Son identidad, no
dirección — el sesgo lo sigue pintando `sesgo_slug` con `--sube`/`--baja`. Si se
colapsaran, una pieza dorada bajista se leería como alcista dorada.
```

- [ ] **Step 3: Documentar la piel en `CLAUDE.md`**

En la sección "Stories GI", después del párrafo de paleta y color, agregar:

```markdown
**Piel compartida.** La línea visual de `oportunidad` —capas de fondo, imagen y
color por activo, sello con pulso, tipografía de titulares en Space Grotesk 800,
CTA y footer— vive en `templates/stories/piel.css`, hermano de `marca.css`. La
consumen `oportunidad`, `alerta` y `recomendacion`; las otras siete plantillas
migran de a una (misma regla que las Fases B y C: una plantilla por Change).

Se estandariza la **piel**, no la **estructura**. `recomendacion` conserva
entrada, TP, SL, volumen y firma acreditada; `alerta` conserva su tarjeta de
niveles; ambas conservan el gráfico como tarjeta legible, porque ahí los niveles
son contenido y no atmósfera. Con el layout de `oportunidad` esos campos bajarían
a letra chica y se borraría la distinción entre **invitar a operar** y
**recomendar una operación** — la segunda lleva firma y cuenta para el límite de
3 señales por semana.

El orden de carga es `marca.css` → `piel.css` → `<style>` de la plantilla, y
`scripts/marca_tokens.py --check` escanea las hojas propias además de las
plantillas (`marca.css` queda fuera: es donde los hex sí van).
```

- [ ] **Step 4: Verificar que la documentación no se contradice con el código**

Run: `uv run pytest tests/ -v && uv run python scripts/marca_tokens.py --check`
Expected: suite verde y gate en 0.

Revisar a ojo que los nombres de campo del `.md` coincidan **exactamente** con las claves de las fixtures: un campo documentado con otro nombre es peor que no documentarlo.

- [ ] **Step 5: Commit**

```bash
git add .claude/commands/alerta.md .claude/commands/story.md CLAUDE.md
git commit -m "docs(stories): la convención de identidad por activo y la piel compartida

Sin esto los comandos siguen emitiendo payloads sin activo_slug ni
activo_imagen, y las piezas salen en gris pese a la piel nueva.

Deja escrito en CLAUDE.md por qué se estandariza la piel y no la estructura:
con el layout de oportunidad, los campos de recomendacion bajan a letra
chica y se borra la distinción entre invitar a operar y recomendar una
operación."
```

---

## Notas para quien ejecute

- **Si un render falla con "Tokens huérfanos"**, el payload no trae una clave que el HTML referencia. El mensaje nombra los tokens exactos. Agregar la clave a la fixture, aunque sea con cadena vacía — la convención del repo es token siempre presente + CSS `:empty` para ocultarlo.
- **Si el gráfico sale negro**, la plantilla está estilando clases `.g-*` que el generador no emite. Los nombres reales salen de `scripts/story_grafico.py`; verificar contra el generador, no contra otra plantilla.
- **En Windows**, encadenar con `|` funciona en el Bash tool; en PowerShell la tubería pasa objetos y rompe el JSON. Usar el Bash tool para los encadenamientos.
- **No migrar `dato_macro` ni las otras seis plantillas** en este trabajo. Está fuera de alcance por decisión de la spec (§6).
