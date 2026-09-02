# Plantilla `oportunidad` — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promover el prototipo `templates/stories/_exploracion/oportunidad.html` a plantilla de producción, pagando las cuatro deudas técnicas que la spec identificó.

**Architecture:** La plantilla nueva convive con las diez existentes y usa el mismo motor (`story_render.py`) sin modificarlo. Tres piezas del sistema sí cambian: `story_grafico.py` gana un parámetro para que el SVG pueda llenar el lienzo, `marca.css` recibe los colores por activo como tokens, y `story.md` suma el tipo. El descubrimiento de plantillas es por `glob("*.html")` en `templates/stories/`, así que mover el archivo la incorpora automáticamente al test de contrato y a `rendir_todas.py`.

**Tech Stack:** Python 3.12 + Playwright (render), pytest, CSS puro (sin framework), `uv` para dependencias.

## Global Constraints

- Los precios respetan los `digits` de `config/activos.json`, con coma decimal y punto de miles. Nunca truncar ceros.
- `--sube` / `--baja` son semántica de mercado y no se reskinean. El color del activo es identidad y va en `--activo`.
- Ninguna plantilla puede hardcodear un color: `uv run --extra stories python scripts/marca_tokens.py --check` debe pasar.
- Toda plantilla de `templates/stories/` necesita su payload en `tests/fixtures/stories/payloads/<nombre>.json`. El test lo exige.
- La pieza invita a operar; **no** lleva entrada, TP, SL ni volumen. Eso la convertiría en señal.
- Comentarios y documentación en español.
- Trabajar sobre la branch `feat/stories-oportunidad`, que ya tiene el prototipo commiteado (`f0abc93`).

---

### Task 1: El SVG del gráfico puede llenar su caja

Hoy `construir_svg` emite siempre `preserveAspectRatio="xMidYMid meet"`, que deja bandas cuando el contenedor tiene otra proporción. El prototipo lo parchea reemplazando el string sobre el JSON ya generado — un parche que hay que borrar.

**Files:**
- Modify: `scripts/story_grafico.py`
- Create: `tests/test_story_grafico.py`

**Interfaces:**
- Consumes: nada de tareas anteriores.
- Produces: `construir_svg(serie, marcadores, niveles=None, lienzo="alto", ajuste="meet") -> str` y `enriquecer(payload)` leyendo `payload["recorrido"]["ajuste"]`. La Task 3 usa `"ajuste": "llenar"` en su fixture.

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/test_story_grafico.py`:

```python
"""Contrato de `scripts/story_grafico.py`."""
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import story_grafico  # noqa: E402

SERIE = [10.0, 12.0, 11.0, 14.0]
MARCADORES = [{"indice": 3, "precio": 14.0, "clase": "actual", "etiqueta": "14,00"}]


def test_ajuste_por_defecto_conserva_proporcion():
    svg = story_grafico.construir_svg(SERIE, MARCADORES)

    assert 'preserveAspectRatio="xMidYMid meet"' in svg


def test_ajuste_llenar_estira_al_contenedor():
    svg = story_grafico.construir_svg(SERIE, MARCADORES, ajuste="llenar")

    assert 'preserveAspectRatio="none"' in svg


def test_ajuste_desconocido_falla_con_mensaje_accionable():
    with pytest.raises(story_grafico.GraficoError) as exc:
        story_grafico.construir_svg(SERIE, MARCADORES, ajuste="cover")

    assert "cover" in str(exc.value)
    assert "llenar" in str(exc.value)


def test_enriquecer_propaga_el_ajuste_del_recorrido():
    payload = {
        "recorrido": {"serie": SERIE, "marcadores": MARCADORES, "ajuste": "llenar"}
    }

    resultado = story_grafico.enriquecer(payload)

    assert 'preserveAspectRatio="none"' in resultado["grafico"]
    assert "recorrido" not in resultado
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `uv run pytest tests/test_story_grafico.py -v`
Expected: FAIL — `TypeError: construir_svg() got an unexpected keyword argument 'ajuste'`

- [ ] **Step 3: Implementar el parámetro**

En `scripts/story_grafico.py`, junto a `LIENZOS` (cerca de la línea 54), agregar:

```python
# Cómo se comporta el SVG dentro de su caja. `meet` conserva la proporción y deja
# bandas; `llenar` estira. Se estira sólo cuando el gráfico es ESCENARIO —fondo a
# sangre de la pieza—, nunca cuando es una tarjeta con ejes que se leen: ahí
# deformar cambiaría la pendiente que el cliente está midiendo.
AJUSTES = {"meet": "xMidYMid meet", "llenar": "none"}
```

En `construir_svg`, cambiar la firma y el `<svg>`:

```python
def construir_svg(
    serie: list[float],
    marcadores: list[dict[str, Any]],
    niveles: list[dict[str, Any]] | None = None,
    lienzo: str = "alto",
    ajuste: str = "meet",
) -> str:
```

Dentro de la función, después de la validación de `lienzo`:

```python
    aspecto = AJUSTES.get(ajuste)
    if aspecto is None:
        raise GraficoError(
            f"ajuste '{ajuste}' desconocido; usa {sorted(AJUSTES)}."
        )
```

Y en la línea del `<svg>` (≈165), reemplazar el literal:

```python
        f'<svg viewBox="0 0 {vb_w} {vb_h}" preserveAspectRatio="{aspecto}">',
```

En `enriquecer`, la llamada de la rama de la serie (≈línea 401) pasa a:

```python
    payload["grafico"] = construir_svg(
        [float(p) for p in serie], marcadores, niveles,
        lienzo=recorrido.get("lienzo", "alto"),
        ajuste=recorrido.get("ajuste", "meet"),
    )
```

El único cambio es la línea de `ajuste`: el resto queda tal cual está hoy.

- [ ] **Step 4: Correr los tests y verificar que pasan**

Run: `uv run pytest tests/test_story_grafico.py -v`
Expected: 4 passed

- [ ] **Step 5: Verificar que no se rompió ninguna plantilla existente**

Run: `uv run pytest tests/test_story_render.py -q`
Expected: 66 passed

- [ ] **Step 6: Commit**

```bash
git add scripts/story_grafico.py tests/test_story_grafico.py
git commit -m "feat(stories): el gráfico puede llenar su caja además de conservar proporción

El escenario a sangre de la pieza nueva necesita que el SVG se estire; las
tarjetas con ejes legibles no, porque deformar cambia la pendiente que el
cliente está midiendo. Por eso es un parámetro y no el comportamiento nuevo
por defecto."
```

---

### Task 2: Los colores por activo viven en `marca.css`

La spec advierte que `marca_tokens.py --check` va a fallar en cuanto la plantilla entre a producción: los cuatro colores de activo están escritos a mano en el prototipo. La fuente única de paleta es `marca.css`.

**Files:**
- Modify: `templates/stories/marca.css`
- Modify: `scripts/marca_tokens.py:30-49` (el diccionario `MAPA`)

**Interfaces:**
- Consumes: nada.
- Produces: los tokens CSS `--activo-oro`, `--activo-wti`, `--activo-us100`, `--activo-usdclp` y la variable de rol `--activo`, que cascadea desde `body.activo-<slug>`. La Task 3 los consume con `var(--activo)`.

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/test_marca_tokens.py`:

```python
"""La paleta vive en marca.css y ninguna plantilla escribe un hex a mano."""
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import marca_tokens  # noqa: E402

MARCA_CSS = _REPO_ROOT / "templates" / "stories" / "marca.css"


def test_marca_css_declara_un_color_por_activo():
    css = MARCA_CSS.read_text(encoding="utf-8")

    for token in ("--activo-oro", "--activo-wti", "--activo-us100", "--activo-usdclp"):
        assert token in css, f"falta {token} en marca.css"


def test_marca_css_cascadea_el_rol_activo_por_clase():
    css = MARCA_CSS.read_text(encoding="utf-8")

    assert "body.activo-oro" in css
    assert "--activo: var(--activo-oro)" in css


def test_los_colores_de_activo_tienen_rol_en_el_mapa():
    # Sin esto, una plantilla que hardcodee #E8B44C recibiría "hex huérfano" en
    # vez de la sugerencia del token correcto.
    for hex_activo in ("#E8B44C", "#E8783C", "#4C86E8", "#C9743A"):
        assert hex_activo in marca_tokens.MAPA, f"{hex_activo} sin rol asignado"


def test_ninguna_plantilla_de_produccion_hardcodea_color():
    for plantilla in sorted((_REPO_ROOT / "templates" / "stories").glob("*.html")):
        html = plantilla.read_text(encoding="utf-8")
        _, _, huerfanos = marca_tokens._tokenizar(html)
        assert not huerfanos, f"{plantilla.name} trae hex sin token: {huerfanos}"
```

- [ ] **Step 2: Correr el test y verificar que falla**

Run: `uv run pytest tests/test_marca_tokens.py -v`
Expected: FAIL en los tres primeros — `falta --activo-oro en marca.css`

- [ ] **Step 3: Declarar los tokens en `marca.css`**

Añadir dentro del bloque `:root`, después de la sección del acento:

```css
  /* ── Identidad por activo ───────────────────────────────────────────────── */
  /* Un color por activo, para que el cliente distinga la pieza antes de leerla.
     Es identidad, NO dirección: pinta el escenario —halo, imagen, nombre del
     activo— y nunca la píldora ni el resultado. Si se colapsara con `--sube` /
     `--baja`, una pieza dorada bajista se leería como alcista dorada. */
  --activo-oro:    #E8B44C;
  --activo-wti:    #E8783C;
  --activo-us100:  #4C86E8;
  --activo-usdclp: #C9743A;
```

Y después del bloque `body.sesgo-*`, la cascada por clase:

```css
/*
  El rol `--activo` lo fija la clase que el snapshot pone en <body>
  (`activo-{{activo_slug}}`), igual que `sesgo-*` fija la dirección. Sin clase,
  el neutro es el acento de marca: una pieza sin activo definido debe verse de
  la marca, no apagada.
*/
body                { --activo: var(--acento); }
body.activo-oro     { --activo: var(--activo-oro); }
body.activo-wti     { --activo: var(--activo-wti); }
body.activo-us100   { --activo: var(--activo-us100); }
body.activo-usdclp  { --activo: var(--activo-usdclp); }
```

- [ ] **Step 4: Registrar los hex en el `MAPA` de `marca_tokens.py`**

En el diccionario `MAPA` (≈línea 30-49), añadir después de la entrada `"#FFFFFF": "blanco",`:

```python
    # Identidad por activo (ver marca.css). Van en el MAPA para que, si una
    # plantilla los escribe a mano, el check sugiera el token en vez de
    # reportarlos como huérfanos sin salida.
    "#E8B44C": "activo-oro",
    "#E8783C": "activo-wti",
    "#4C86E8": "activo-us100",
    "#C9743A": "activo-usdclp",
```

- [ ] **Step 5: Correr los tests y verificar que pasan**

Run: `uv run pytest tests/test_marca_tokens.py -v`
Expected: 4 passed

- [ ] **Step 6: Verificar el check real y las plantillas existentes**

Run: `uv run --extra stories python scripts/marca_tokens.py --check`
Expected: `ok` por plantilla y `Paleta centralizada en templates/stories/marca.css`

Run: `uv run pytest tests/test_story_render.py -q`
Expected: 66 passed

- [ ] **Step 7: Commit**

```bash
git add templates/stories/marca.css scripts/marca_tokens.py tests/test_marca_tokens.py
git commit -m "feat(stories): la identidad cromática por activo entra a marca.css

Cuatro colores, uno por activo, como tokens de la fuente única. Cascadean desde
la clase de <body> igual que el sesgo, y el neutro es el acento de marca.
Quedan registrados en el MAPA de marca_tokens para que un hex escrito a mano
reciba la sugerencia del token correcto y no un 'huérfano' sin salida."
```

---

### Task 3: La plantilla entra a producción con su fixture

**Files:**
- Create: `templates/stories/oportunidad.html` (desde `templates/stories/_exploracion/oportunidad.html`)
- Delete: `templates/stories/_exploracion/oportunidad.html` (y el directorio, que queda vacío)
- Create: `tests/fixtures/stories/payloads/oportunidad.json`
- Modify: `tests/test_story_render.py` (añadir constante y bloque de tests al final, antes del bloque "Contrato de TODAS las plantillas" de la línea ≈1056)

**Interfaces:**
- Consumes: `--activo` y `body.activo-<slug>` de la Task 2; `"ajuste": "llenar"` de la Task 1.
- Produces: la plantilla `oportunidad` y su fixture. La Task 4 la referencia por nombre desde `/story`.

- [ ] **Step 1: Mover el archivo y corregir las rutas relativas**

```bash
git mv templates/stories/_exploracion/oportunidad.html templates/stories/oportunidad.html
rmdir templates/stories/_exploracion
```

En el archivo movido, las rutas suben un nivel de más. Reemplazar:

- `href="../marca.css"` → `href="marca.css"`
- `url("../fonts/` → `url("fonts/` (todas las ocurrencias)
- `src="../assets/` → `src="assets/` (el logo del CTA)

Borrar los tres `@font-face` de fuentes que ya no están en el repo (Sora, Outfit, Manrope): sus archivos se eliminaron y dejar la declaración induce a error sobre qué usa el sistema.

Borrar el bloque CSS `body.activo-*` de la plantilla: esos colores ahora los sirve `marca.css` (Task 2). Conservar el uso de `var(--activo)`.

Actualizar el comentario de cabecera: ya no es un prototipo ni vive en `_exploracion/`. Dejar explicado el porqué de las decisiones (activo protagonista, lectura sobre cifra, gráfico como escenario, identidad vs dirección).

- [ ] **Step 2: Escribir la fixture**

Crear `tests/fixtures/stories/payloads/oportunidad.json`:

```json
{
  "plantilla": "oportunidad",
  "sello": "MOTOR GI · ANÁLISIS EN VIVO",
  "fecha_hora": "4 AGO 2026 · 11:26 CLT",
  "activo_nombre": "ORO",
  "activo_ticker": "XAU/USD",
  "activo_slug": "oro",
  "activo_imagen": "assets/activos/oro.jpg",
  "modo_imagen": "foto-activo",
  "sesgo": "Alcista",
  "direccion_etiqueta": "SUBIENDO",
  "titular": "El oro sube y busca los 4.100",
  "razon": "En Estados Unidos se están abriendo menos empleos. Eso acerca la baja de tasas, el dólar pierde fuerza y el oro sube.",
  "precio": "4.076,92",
  "objetivo_rotulo": "Hacia dónde va",
  "objetivo": "4.115,90",
  "nota_nivel": "Primero tiene que romper 4.078,77",
  "dato_rotulo": "Por qué sube",
  "dato_lectura": "Menos empleos en EE.UU.",
  "dato_detalle": "7,36 millones de puestos sin cubrir · se esperaban 7,44 M",
  "dato_veredicto": "Peor de lo esperado",
  "cta": "¿Quieres aprovechar este movimiento?",
  "cta_sub": "Habla hoy con tu analista",
  "recorrido": {
    "ajuste": "llenar",
    "serie": [
      4048.1, 4052.4, 4061.9, 4057.3, 4066.8, 4072.2, 4064.5, 4070.1,
      4079.6, 4085.2, 4077.4, 4069.8, 4074.3, 4081.7, 4088.4, 4092.6,
      4084.1, 4076.5, 4069.2, 4073.8, 4080.4, 4086.9, 4079.3, 4071.6,
      4066.2, 4072.9, 4081.1, 4087.5, 4082.3, 4076.92
    ],
    "marcadores": [
      { "indice": 29, "precio": 4076.92, "clase": "actual", "etiqueta": "4.076,92", "rol": "AHORA" }
    ]
  }
}
```

- [ ] **Step 3: Escribir los tests que fallan**

En `tests/test_story_render.py`, añadir la constante junto a las demás (después de `POSTVENTA_TEMPLATE`, ≈línea 35):

```python
OPORTUNIDAD_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "oportunidad.html"
```

Y este bloque **antes** de la sección "Contrato de TODAS las plantillas" (≈línea 1056):

```python
# ---------------------------------------------------------------------------
# snapshot templates/stories/oportunidad.html — la pieza que invita a operar.
# El activo es el protagonista y el dato macro baja a evidencia; ver
# docs/superpowers/specs/2026-08-04-rediseno-stories-gi-design.md
# ---------------------------------------------------------------------------

PAYLOAD_OPORTUNIDAD = json.loads(
    (FIXTURES_DIR / "payloads" / "oportunidad.json").read_text(encoding="utf-8")
)


def _html_oportunidad(payload: dict) -> str:
    from story_grafico import enriquecer

    return story_render.build_html(enriquecer(dict(payload)), OPORTUNIDAD_TEMPLATE)


def test_oportunidad_no_placeholders():
    html = _html_oportunidad(PAYLOAD_OPORTUNIDAD)

    for clave in ("titular", "precio", "objetivo", "dato_lectura", "cta"):
        assert PAYLOAD_OPORTUNIDAD[clave] in html
    assert "{{" not in html
    assert "}}" not in html


def test_oportunidad_identidad_y_direccion_son_clases_distintas():
    # El color del activo y la dirección de mercado son roles separados: si se
    # colapsaran, una pieza dorada bajista se leería como alcista dorada.
    html = _html_oportunidad(PAYLOAD_OPORTUNIDAD)

    assert "activo-oro" in html
    assert "sesgo-alcista" in html


def test_oportunidad_sesgo_bajista_cambia_la_clase_no_el_activo():
    payload = {**PAYLOAD_OPORTUNIDAD, "sesgo": "Bajista"}

    html = _html_oportunidad(payload)

    assert "sesgo-bajista" in html
    assert "activo-oro" in html


def test_oportunidad_modo_imagen_elige_el_tratamiento():
    html = _html_oportunidad({**PAYLOAD_OPORTUNIDAD, "modo_imagen": "ilustracion"})

    assert 'class="ilustracion"' in html
    assert "{{" not in html


def test_oportunidad_no_promete_una_operacion():
    # La pieza invita a operar pero no es una señal: sin entrada, TP, SL ni
    # volumen. Eso exigiría firma acreditada y contaría para el límite semanal.
    html = _html_oportunidad(PAYLOAD_OPORTUNIDAD).lower()

    for prohibido in ("take profit", "stop loss", "volumen", "lotaje"):
        assert prohibido not in html


def test_oportunidad_el_grafico_llena_el_lienzo():
    html = _html_oportunidad(PAYLOAD_OPORTUNIDAD)

    assert 'preserveAspectRatio="none"' in html
```

- [ ] **Step 4: Correr los tests y verificar que fallan**

Run: `uv run pytest tests/test_story_render.py -k oportunidad -v`
Expected: FAIL — la plantilla todavía tiene rutas `../` o tokens sin resolver, según lo que falte del Step 1.

- [ ] **Step 5: Ajustar la plantilla hasta que pasen**

Los fallos esperables y su causa:
- `{{` en el HTML → un token del payload cambió de nombre; alinear plantilla y fixture.
- `assert 'class="ilustracion"'` falla → el `<img>` debe usar `class="{{modo_imagen}}"`, no una clase fija.
- `preserveAspectRatio="none"` ausente → falta `"ajuste": "llenar"` en el `recorrido` de la fixture o la Task 1 no está aplicada.

- [ ] **Step 6: Correr la suite completa**

Run: `uv run pytest tests/test_story_render.py tests/test_story_grafico.py tests/test_marca_tokens.py -q`
Expected: todo verde. El test `test_toda_plantilla_tiene_payload_de_prueba` ahora incluye `oportunidad` y pasa porque la fixture existe.

- [ ] **Step 7: Revisión visual de las once piezas, en los dos formatos**

Run:
```bash
uv run --extra stories python scripts/rendir_todas.py
uv run --extra stories python scripts/rendir_todas.py --formato vertical
```
Expected: once PNG por formato en `data/stories/_revision/<formato>/`. Abrir `oportunidad.png` de cada uno y verificar contra la spec §2.9: en vertical, el CTA y el disclaimer dentro del lienzo, la imagen a la derecha y a media escala, y la lista de precios legible sobre el gráfico.

- [ ] **Step 8: Commit**

```bash
git add templates/stories/oportunidad.html tests/fixtures/stories/payloads/oportunidad.json tests/test_story_render.py
git commit -m "feat(stories): la plantilla oportunidad entra a producción

Sale de _exploracion/ y con eso entra al glob del test de contrato y a
rendir_todas.py, que es todo lo que hacía falta para que nadie la pueda cambiar
sin que alguien la revise. Los colores de activo salen de marca.css y el
gráfico llena el lienzo por parámetro, no por parche sobre el JSON."
```

---

### Task 4: `/story oportunidad`

**Files:**
- Modify: `.claude/commands/story.md`
- Modify: `CLAUDE.md` (sección "Stories GI" y la tabla de slash commands)

**Interfaces:**
- Consumes: la plantilla `oportunidad` de la Task 3.
- Produces: el tipo `oportunidad` invocable desde `/story`.

- [ ] **Step 1: Añadir la ruta al comando**

En `.claude/commands/story.md`, sumar `oportunidad` a la lista de tipos soportados del PASO 0 y agregar su bloque de recolección después de la ruta `recomendacion`:

```markdown
---

## Ruta `oportunidad` — el activo protagonista, el dato como evidencia

Es la pieza que **invita a operar**: nombra un activo, su dirección, el precio de ahora y hacia
dónde va, y cierra en un llamado al analista. El dato macro que la origina baja a evidencia
lateral.

⚠️ **No es una señal y no debe convertirse en una.** No lleva entrada, TP, SL ni volumen: eso
exigiría firma acreditada y contaría para el límite de 3 por semana. Si el director quiere llegar
al precio de entrada, la plantilla es `recomendacion`.

1. **Activo y datos del motor**: pedir el activo (normalizado contra `config/activos.json`) y
   llamar una vez a `mcp__market-data__get_asset_levels({"ticker": "[TICKER]", "timeframe": "H1"})`.
   De ahí salen `precio` (precio actual), `nota_nivel` (la resistencia o soporte más próximo) y
   `objetivo` (el siguiente nivel en la dirección del sesgo). Si retorna `{"error": ...}`, pedirlos
   manualmente (mismo patrón que `apertura.md` PASO 4A). Formatear con los `digits` del activo.

2. **Serie del gráfico**: encadenar `scripts/serie_mt5.py` antes del render, igual que `operacion`:
   ```bash
   uv run --with MetaTrader5 python scripts/serie_mt5.py --ticker [TICKER] --timeframe H1 --velas 72
   ```
   El `recorrido` resultante lleva `"ajuste": "llenar"`: en esta pieza el gráfico es escenario a
   sangre, no una tarjeta con ejes.

3. **El titular nombra un precio del motor**, no una figura técnica: "El oro sube y busca los
   4.100", nunca "va por sus máximos". Sin jerga: la explicación también va en voz llana.

4. **La tarjeta del dato dice la lectura, no la cifra**: `dato_lectura` es "Menos empleos en
   EE.UU." y `dato_detalle` es "7,36 millones de puestos sin cubrir · se esperaban 7,44 M". El
   número solo no le sirve a nadie.

5. **Imagen del activo**: `templates/stories/assets/activos/<slug>.jpg`. Si el activo no tiene la
   suya, generarla con el recetario de `docs/design/stories-gi/imagenes-por-activo.md`.

6. **Payload** → `templates/stories/oportunidad.html`. Seguir con PASO 6 (aprobación) y PASO 7
   (render), con `-Activo [TICKER_MT5]`.
```

- [ ] **Step 2: Documentar en `CLAUDE.md`**

En la sección "Stories GI", sumar `oportunidad` a la lista de tipos soportados y agregar el párrafo que la describe, junto a las otras plantillas: qué comunica, que el activo es el protagonista, que el color de activo es identidad y no dirección, y que **no** es una señal.

En la tabla de slash commands, actualizar la línea de `/story` para incluir el tipo nuevo.

- [ ] **Step 3: Verificar que la documentación no contradice al código**

Run: `uv run pytest tests/test_story_render.py -q`
Expected: 72+ passed (los 66 previos más los seis de `oportunidad`)

Revisar a mano que la lista de tipos de `story.md`, la de `CLAUDE.md` y los archivos reales de `templates/stories/*.html` coincidan. Una lista desactualizada es la forma más común de que el comando ofrezca un tipo que no existe.

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/story.md CLAUDE.md
git commit -m "docs(stories): /story oportunidad queda documentado

Incluye el límite editorial en el propio comando: la pieza invita a operar y no
lleva entrada, TP ni SL. Escrito donde se va a leer en el momento de generarla,
no sólo en la spec."
```

---

## Cierre

Al terminar las cuatro tareas:

```bash
uv run pytest tests/ -q
uv run --extra stories python scripts/marca_tokens.py --check
uv run --extra stories python scripts/rendir_todas.py
uv run --extra stories python scripts/rendir_todas.py --formato vertical
```

Y abrir un PR contra `master` desde `feat/stories-oportunidad` que enlace la spec.

## Fuera de alcance

Estas quedan para Changes posteriores, y conviene no colarlas acá:

- Migrar `alerta` y `dato_macro` de producción al lenguaje visual nuevo.
- Las imágenes de los activos que todavía no tienen la suya.
- Las tres decisiones pendientes del director (spec §8): el par de precios en dos verdes casi
  iguales, si el titular usa el número redondo o el exacto, y si esta plantilla reemplaza a
  `dato_macro` como pieza 1 de la agenda diaria.
