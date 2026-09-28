# Pieza diaria de visión para Avisos · Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que el reloj prepare de martes a viernes, a las 10:30 de Nueva York, una pieza de "visión" (banco contra nuestros datos) para el grupo de Avisos, y que `/vision` la escriba, la rinda como PNG con pie y la deje lista para aprobación.

**Architecture:** Los frenos de `pipeline_linkedin` se separan en tres funciones genéricas que usan los dos pipelines. `pipeline_vision.py` elige la visión, lee el terminal, refresca y rinde con la plantilla nueva `vision.html`. El reloj aprende a correr "piezas" (`PIEZAS`) además del carrusel, y resuelve su canal por alias.

**Tech Stack:** Python 3.12 (uv), pytest, Playwright (extra `stories`), MetaTrader5 (`--with MetaTrader5`), HTML/CSS con los tokens de `templates/stories/marca.css`.

**Spec:** `docs/superpowers/specs/2026-09-28-pieza-avisos-vision-design.md`

## Global Constraints

- Rama `feat/pieza-avisos-vision`, que parte de `feat/linkedin-pipeline` (PR #241). Nunca commitear a master.
- Texto de cliente sin guion largo (U+2014) ni medio (U+2013) como inciso, sin voseo, en tuteo chileno.
- Precios con los `digits` del catálogo y en notación chilena, vía `pipeline_linkedin.formatear` (el cobre, con `digits = 0`, va sin separador de miles).
- Cero precios escritos a mano: toda cifra sale de `leer_activos` o de una visión registrada.
- Colores solo por `var(--rol)`; `uv run python scripts/marca_tokens.py --check` tiene que pasar.
- El reloj nunca envía: en `scripts/reloj_gi.py` no pueden aparecer `enviar_whatsapp`, `whatsapp_sender`, `--despachar` ni `despachar(`.
- La frescura de la pieza de WhatsApp es de 2 horas; la de LinkedIn sigue en 24.
- El historial de visiones usado es `data/historial_suplementos.json`, con `tipo: "vision"`, `canal`, `clave` (el id), `variante` y `fecha`.
- Toda escritura de texto va por Python (`Path.write_text(..., encoding="utf-8")`), nunca por la consola de PowerShell.
- Correr los tests con `uv run pytest`; los que rinden PNG, con `uv run --extra stories pytest`.

## Review Focus

1. **Un director que aprueba tarde:** tras más de 2 h, `--refrescar` conserva la visión y el texto, y `validar_cifras` marca el precio que cambió. No se vuelve a elegir visión. Lo cubre el Task 4, con `test_refrescar_conserva_vision_y_texto` y `test_tras_refrescar_la_cifra_vieja_del_texto_se_marca`.
2. **Una visión `meta_precio` sin `horizonte`:** la pieza promete el plazo, así que se detiene. Lo cubre el Task 3, con `test_meta_precio_sin_horizonte_no_se_elige`.
3. **Un activo sin soporte o resistencia del terminal:** no hay mapa, así que no hay pieza, y se detiene en vez de rendir una imagen sin niveles. Lo cubre el Task 4, con `test_sin_niveles_se_detiene`.
4. **Un lunes, un feriado de NYSE o un sábado:** código 0, "hoy no corresponde", sin payload y sin tocar el historial. Lo cubre el Task 3, con `test_preparar_lunes_no_corresponde` y `test_preparar_feriado_no_corresponde`.
5. **El nombre del momento sale al cliente** en el aviso de cambio de horario: va acentuado y sin cifras. Lo cubren los tests existentes del reloj sobre nombres y precios, que el Task 5 corre.

---

## Estructura de archivos

| Archivo | Responsabilidad |
|---|---|
| `scripts/pipeline_linkedin.py` | Expone `validar_textos`, `validar_cifras` y `validar_frescura`; `validar` las compone |
| `scripts/pipeline_vision.py` | Nuevo: días de pieza, elección de visión, payload, preparar, refrescar, validar, rendir y CLI |
| `templates/stories/vision.html` | Nueva plantilla con los bloques `FOR` `bloque_cita`, `bloque_meta` y `niveles` |
| `tests/fixtures/stories/payloads/vision.json` | Fixture de la plantilla |
| `data/visiones_expertos.json` | Campo `horizonte` en las visiones de proyección |
| `scripts/reloj_gi.py` | `PIEZAS`, `_correr_preparar(canal, pieza)`, canal por alias |
| `config/agenda_mercado.json` | Momento `vision_avisos` |
| `.claude/commands/vision.md` | Nuevo comando |
| `scripts/agy_workflows.py`, `CLAUDE.md` | Exponer `/vision` y documentar la extensión del invariante 4 |
| `.gitignore` | `data/avisos/` |
| `tests/test_pipeline_vision.py` | Nuevo |
| `tests/test_pipeline_linkedin.py`, `tests/test_reloj_gi.py`, `tests/test_agenda_mercado.py` | Casos nuevos |

---

### Task 1: Frenos compartidos en `pipeline_linkedin`

**Files:**
- Modify: `scripts/pipeline_linkedin.py`: `cifras_permitidas`, `cifras_parecidas_no_medidas`, `validar`, y agregar tres funciones nuevas.
- Test: `tests/test_pipeline_linkedin.py`

**Interfaces:**
- Produces:
  - `validar_textos(textos: list[tuple[str, str]]) -> list[str]`
  - `validar_cifras(textos: list[tuple[str, str]], activos: dict[str, dict], visiones: list[dict], cifras_citadas: dict[str, str]) -> list[str]`
  - `validar_frescura(leido: datetime, ahora: datetime, max_horas: float, remedio: str = "Vuelve a correr --preparar.") -> list[str]`
  - `cifras_permitidas(activos, visiones, cifras_citadas) -> set[str]` (cambia la firma: antes recibía el payload)
  - `cifras_parecidas_no_medidas(texto, activos, permitidas) -> list[str]` (cambia la firma)
  - `validar(payload, registro, ahora, aceptar_datos_viejos=False) -> list[str]` (misma firma y mismo comportamiento)

- [ ] **Step 1: Escribir los tests que fallan**

Agregar al final de `tests/test_pipeline_linkedin.py`:

```python
# ------------------------------------------------------------ frenos compartidos


def test_validar_textos_generico():
    errores = pl.validar_textos([("a", "Hola."), ("b", pl.MARCA_EDITORIAL), ("c", "Si tenés, sube — mucho")])
    assert any(e.startswith("b: sin escribir") for e in errores)
    assert any("c:" in e and "guion" in e for e in errores)
    assert any("c:" in e and "voseo" in e for e in errores)
    assert not any(e.startswith("a:") for e in errores)


def test_validar_cifras_generico():
    activos = {"USDCLP": dict(USDCLP)}
    textos = [("t", "Está en $971,03 y antes en $900,00; el soporte 968,00.")]
    errores = pl.validar_cifras(textos, activos, [], {})
    assert any("$900,00" in e for e in errores)
    assert any("968,00" in e for e in errores)
    assert not any("971,03" in e for e in errores)
    assert pl.validar_cifras(textos, activos, [], {"$900,00": "x", "968,00": "y"}) == []


def test_validar_frescura_generico():
    assert pl.validar_frescura(AHORA, AHORA + timedelta(hours=2, minutes=1), 2)
    assert pl.validar_frescura(AHORA, AHORA + timedelta(hours=1, minutes=59), 2) == []
    msg = pl.validar_frescura(AHORA, AHORA + timedelta(hours=3), 2, remedio="Usa --refrescar.")
    assert "--refrescar" in msg[0]
```

- [ ] **Step 2: Correr y verificar que fallan**

Run: `uv run pytest tests/test_pipeline_linkedin.py -k "generico" -v`
Expected: FAIL con `AttributeError: module 'pipeline_linkedin' has no attribute 'validar_textos'`

- [ ] **Step 3: Implementar**

En `scripts/pipeline_linkedin.py`, reemplazar `cifras_permitidas` y `cifras_parecidas_no_medidas`, y reemplazar el cuerpo de `validar` por la composición. El resto del módulo no cambia.

```python
def cifras_permitidas(activos: dict[str, dict[str, Any]], visiones: list[dict[str, Any]],
                      cifras_citadas: dict[str, str]) -> set[str]:
    permitidas: set[str] = set()
    for fila in activos.values():
        for campo in CAMPOS_PRECIO:
            if fila.get(campo) is not None:
                permitidas.add(formatear(fila[campo], fila["digits"]))
    for vision in visiones:
        permitidas.update(_PRECIO.findall(str(vision.get("cita", ""))))
    for cifra in cifras_citadas:
        permitidas.update(_PRECIO.findall(cifra) or [cifra.strip()])
    return permitidas


def cifras_parecidas_no_medidas(texto: str, activos: dict[str, dict[str, Any]], permitidas: set[str]) -> list[str]:
    """(mismo docstring que hoy)"""
    referencias = [
        float(fila[c])
        for fila in activos.values()
        for c in CAMPOS_PRECIO
        if fila.get(c) not in (None, 0)
    ]
    dudosas: list[str] = []
    for cifra in _NUMERO.findall(texto):
        if cifra in permitidas:
            continue
        valor = _a_float(cifra)
        if 1900 <= valor <= 2100 and "," not in cifra and "." not in cifra:
            continue  # un año
        if any(abs(valor - ref) / ref <= CERCANIA_PRECIO for ref in referencias):
            dudosas.append(cifra)
    return dudosas


def validar_textos(textos: list[tuple[str, str]]) -> list[str]:
    """Freno de texto de cliente, sin saber de qué pieza viene cada texto."""
    from validador_editorial import validar_texto

    errores: list[str] = []
    for donde, texto in textos:
        if MARCA_EDITORIAL in texto or not texto.strip():
            errores.append(f"{donde}: sin escribir")
            continue
        if "–" in texto or "—" in texto:
            errores.append(f"{donde}: guion largo o medio como inciso; reescribe con punto, coma o dos puntos")
        errores.extend(e for e in validar_texto(texto, campo=donde) if "guion largo" not in e)
    return errores


def validar_cifras(textos: list[tuple[str, str]], activos: dict[str, dict[str, Any]],
                   visiones: list[dict[str, Any]], cifras_citadas: dict[str, str]) -> list[str]:
    """Freno de cifras: toda cifra con $ o parecida a un precio tiene respaldo."""
    permitidas = cifras_permitidas(activos, visiones, cifras_citadas)
    errores: list[str] = []
    for donde, texto in textos:
        con_moneda = _PRECIO.findall(texto)
        for cifra in con_moneda:
            if cifra not in permitidas:
                errores.append(
                    f"{donde}: la cifra ${cifra} no sale del terminal ni de una cita registrada. "
                    "Usa la medida o declárala en `cifras_citadas` con su motivo."
                )
        for cifra in cifras_parecidas_no_medidas(texto, activos, permitidas):
            if cifra not in con_moneda:
                errores.append(
                    f"{donde}: {cifra} se parece a un precio medido pero no es ninguno. "
                    "Usa la cifra exacta del terminal o declárala en `cifras_citadas`."
                )
    return errores


def validar_frescura(leido: datetime, ahora: datetime, max_horas: float,
                     remedio: str = "Vuelve a correr --preparar.") -> list[str]:
    horas = (ahora - leido).total_seconds() / 3600
    if horas > max_horas:
        return [f"los datos se leyeron hace {horas:.1f} h (máximo {max_horas}). {remedio}"]
    return []


def validar(payload: dict[str, Any], registro: dict[str, dict[str, Any]], ahora: datetime,
            aceptar_datos_viejos: bool = False) -> list[str]:
    """Todos los motivos por los que el brief no puede salir. Vacío = puede salir.

    Compone los tres frenos compartidos con los textos de LinkedIn. `pipeline_vision`
    llama a los mismos frenos con los suyos: dos implementaciones del mismo freno
    terminan divergiendo.
    """
    editorial = payload["editorial"]
    textos = _textos(editorial)
    errores = validar_textos(textos)

    usadas: list[dict[str, Any]] = []
    aceptadas = editorial.get("aceptar_antiguas", {})
    for pagina, campos in editorial.get("paginas", {}).items():
        vid = campos.get("vision")
        if vid is None:
            continue
        if vid == MARCA_EDITORIAL or not str(vid).strip():
            errores.append(f"{pagina}.vision: sin elegir")
            continue
        if vid not in registro:
            errores.append(f"{pagina}.vision: `{vid}` no está en {REGISTRO_VISIONES.name}")
            continue
        usadas.append(registro[vid])
        errores.extend(validar_vision(registro[vid], ahora.date(), aceptadas.get(vid)))

    errores.extend(validar_cifras(textos, payload["datos"]["activos"], usadas,
                                  editorial.get("cifras_citadas", {})))
    if not aceptar_datos_viejos:
        errores.extend(validar_frescura(leido_en(payload), ahora, FRESCURA_MAX_HORAS))
    return errores
```

- [ ] **Step 4: Correr la suite de LinkedIn completa**

Run: `uv run pytest tests/test_pipeline_linkedin.py -q`
Expected: todos PASS (los 37 anteriores y los 3 nuevos). El test `test_datos_viejos_se_detienen_salvo_aceptados` busca "se leyeron hace" y sigue pasando.

- [ ] **Step 5: Commit**

```bash
git add scripts/pipeline_linkedin.py tests/test_pipeline_linkedin.py
git commit -m "refactor(linkedin): separar los frenos en validar_textos, validar_cifras y validar_frescura"
```

---

### Task 2: Plantilla `vision.html` y su fixture

**Files:**
- Create: `templates/stories/vision.html`
- Create: `tests/fixtures/stories/payloads/vision.json`
- Test: `tests/test_story_render.py`. Los tests paramétricos existentes (`test_toda_plantilla_tiene_payload_de_prueba`, `test_plantilla_resuelve_sin_huerfanos`) la cubren solos; se agrega uno de variantes.

**Interfaces:**
- Produces: tokens top-level `chip`, `sesgo_clase`, `direccion_texto`, `precio`, `hora_lectura`, `lectura`, `remate`, `firma_gi`, `aviso`; bucles `bloque_cita` (`rotulo`, `cita`, `firma`), `bloque_meta` (`meta`, `horizonte`, `firma`, `precio`, `hora`) y `niveles` (`clase`, `icono`, `texto`).

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_story_render.py`:

```python
def test_vision_resuelve_cada_variante_por_separado():
    tpl = _REPO_ROOT / "templates" / "stories" / "vision.html"
    base = json.loads((FIXTURES_DIR / "payloads" / "vision.json").read_text(encoding="utf-8"))
    solo_cita = dict(base, bloque_meta=[])
    solo_meta = dict(base, bloque_cita=[])
    html_cita = story_render.build_html(solo_cita, tpl)
    html_meta = story_render.build_html(solo_meta, tpl)
    assert "bloque-cita" in html_cita and "bloque-meta" not in html_cita
    assert "bloque-meta" in html_meta and "bloque-cita" not in html_meta
    assert "{{" not in html_cita + html_meta
```

- [ ] **Step 2: Verificar que falla**

Run: `uv run pytest tests/test_story_render.py -k vision -v`
Expected: FAIL (no existe la plantilla ni el fixture).

- [ ] **Step 3: Crear el fixture**

`tests/fixtures/stories/payloads/vision.json` (las dos variantes llenas, para que el test paramétrico las resuelva a la vez):

```json
{
  "plantilla": "vision",
  "chip": "VISIÓN · DÓLAR / PESO CHILENO",
  "sesgo_clase": "sesgo-alcista",
  "direccion_texto": "ALCISTA",
  "precio": "968,30",
  "hora_lectura": "12:30",
  "lectura": "Los bancos miran el mediano plazo; el precio de hoy lo manda la Fed.",
  "remate": "Mientras el mercado espere otra alza de tasa, la dirección de corto plazo es alcista.",
  "firma_gi": "Grupo Inteligencia · Análisis de Mercado",
  "aviso": "Análisis informativo. No constituye recomendación de inversión.",
  "bloque_cita": [
    {"rotulo": "Cita", "cita": "Los niveles sobre $960 parecen difíciles de justificar.", "firma": "Patricio Eskenazi · Conpat Global · Chócale, 2026-09-16"}
  ],
  "bloque_meta": [
    {"meta": "Base de $905 a mediano plazo", "horizonte": "mediano plazo", "firma": "Bci Estudios · Chócale, 2026-09-16", "precio": "968,30", "hora": "12:30"}
  ],
  "niveles": [
    {"clase": "resistencia", "icono": "🟢", "texto": "Sobre 974,50: fuerza compradora; siguiente nivel 977,30"},
    {"clase": "nivel", "icono": "🟡", "texto": "Entre 960,90 y 974,50: rango; si rompe un borde y vuelve a entrar, el objetivo pasa a ser el borde contrario"},
    {"clase": "soporte", "icono": "🔴", "texto": "Bajo 960,90: presión vendedora; siguiente nivel 949,60"}
  ]
}
```

- [ ] **Step 4: Crear la plantilla**

`templates/stories/vision.html`. El primer `<style>` lleva solo el marcador y el paso 5 lo rellena con `marca.css`. Solo se usan `var(--rol)` y `color-mix`: nada de hex ni `rgba` con valores.

```html
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>Visión del día</title>
<style>
  /* ════ marca.css embebido ════ */
</style>
<style>
@font-face { font-family: "Goldman"; src: url("fonts/goldman-700.woff2") format("woff2"); font-weight: 700; font-display: swap; }
@font-face { font-family: "Plus Jakarta Sans"; src: url("fonts/plus-jakarta-sans-400.woff2") format("woff2"); font-weight: 400; font-display: swap; }
@font-face { font-family: "Plus Jakarta Sans"; src: url("fonts/plus-jakarta-sans-700.woff2") format("woff2"); font-weight: 700; font-display: swap; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; width: 1920px; height: 1080px; background: var(--fondo);
  color: var(--texto-1); font-family: var(--font-sans); overflow: hidden; -webkit-font-smoothing: antialiased; }
.story { position: relative; width: 100%; height: 100%; padding: 56px 72px 40px;
  display: flex; flex-direction: column; box-shadow: inset 0 0 0 var(--filete-ancho) var(--filete); }
.velo { position: absolute; inset: 0; pointer-events: none;
  background: radial-gradient(circle at 15% 15%, color-mix(in srgb, var(--acento) 14%, transparent) 0%, transparent 55%),
              linear-gradient(180deg, var(--fondo) 0%, var(--velo-inferior) 100%); }
.cabecera { position: relative; display: flex; gap: 14px; align-items: center; }
.chip { font-family: var(--font-display); font-weight: 700; font-size: 16px; letter-spacing: 0.10em;
  padding: 8px 20px; border-radius: 999px; border: 1.5px solid var(--acento); color: var(--acento);
  background: color-mix(in srgb, var(--acento) 12%, var(--fondo)); }
.pildora { font-family: var(--font-display); font-weight: 700; font-size: 16px; letter-spacing: 0.10em;
  padding: 8px 20px; border-radius: 999px; color: var(--direccion);
  background: var(--fondo-direccion); border: 1.5px solid var(--direccion); }
.cuerpo { position: relative; flex: 1; min-height: 0; display: flex; gap: 48px; margin-top: 36px; }
.col-bancos { flex: 0 0 56%; display: flex; flex-direction: column; justify-content: center; }
.col-datos { flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 18px; }
.rotulo { font-family: var(--font-sans); font-weight: 700; font-size: 18px; letter-spacing: 0.10em;
  text-transform: uppercase; color: var(--acento); }
.cita { font-family: var(--font-display); font-weight: 700; font-size: 50px; line-height: 1.18;
  color: var(--blanco); margin: 18px 0 0; }
.firma { font-size: 20px; color: var(--texto-2); margin-top: 22px; }
.meta-grid { display: flex; gap: 28px; margin-top: 18px; }
.meta-caja { flex: 1; border-radius: 24px; padding: 30px 32px;
  background: color-mix(in srgb, var(--fondo-acento) 80%, var(--fondo));
  border: 1.5px solid color-mix(in srgb, var(--acento) 40%, transparent); }
.meta-valor { font-family: var(--font-display); font-weight: 700; font-size: 40px; line-height: 1.15; color: var(--blanco); margin-top: 10px; }
.meta-sub { font-size: 18px; color: var(--texto-2); margin-top: 10px; }
.precio { font-family: var(--font-display); font-weight: 700; font-size: 72px; color: var(--blanco); }
.hora { font-size: 18px; color: var(--texto-3); }
.nivel { display: flex; gap: 12px; font-size: 21px; line-height: 1.4; color: var(--texto-1); }
.nivel .icono { font-family: var(--font-emoji); }
.lectura { position: relative; margin-top: 20px; padding-top: 18px;
  border-top: 1px solid color-mix(in srgb, var(--acento) 35%, transparent); }
.lectura h2 { font-family: var(--font-display); font-size: 30px; margin: 0; color: var(--blanco); }
.lectura p { font-size: 21px; color: var(--texto-borde); margin: 8px 0 0; }
.pie { position: relative; display: flex; justify-content: space-between; margin-top: 16px; font-size: 14px; color: var(--texto-3); }
.pie .marca { font-family: var(--font-display); color: var(--acento); letter-spacing: 0.08em; }
</style>
</head>
<body class="{{sesgo_clase}}">
  <div class="story">
    <div class="velo"></div>
    <div class="cabecera">
      <span class="chip">{{chip}}</span>
      <span class="pildora">{{direccion_texto}}</span>
    </div>
    <div class="cuerpo">
      <div class="col-bancos">
        <span class="rotulo">Lo que dicen los bancos</span>
        <!-- FOR:bloque_cita -->
        <div class="bloque-cita">
          <span class="rotulo">{{rotulo}}</span>
          <p class="cita">“{{cita}}”</p>
          <div class="firma">{{firma}}</div>
        </div>
        <!-- ENDFOR:bloque_cita -->
        <!-- FOR:bloque_meta -->
        <div class="bloque-meta">
          <div class="meta-grid">
            <div class="meta-caja"><span class="rotulo">Meta del banco</span>
              <div class="meta-valor">{{meta}}</div><div class="meta-sub">Plazo: {{horizonte}}</div></div>
            <div class="meta-caja"><span class="rotulo">Precio hoy</span>
              <div class="meta-valor">{{precio}}</div><div class="meta-sub">Terminal, {{hora}} hora Chile</div></div>
          </div>
          <div class="firma">{{firma}}</div>
        </div>
        <!-- ENDFOR:bloque_meta -->
      </div>
      <div class="col-datos">
        <span class="rotulo">Lo que dicen nuestros datos</span>
        <div class="precio">{{precio}}</div>
        <div class="hora">Terminal MT5, {{hora_lectura}} hora Chile</div>
        <!-- FOR:niveles -->
        <div class="nivel {{clase}}"><span class="icono">{{icono}}</span><span>{{texto}}</span></div>
        <!-- ENDFOR:niveles -->
      </div>
    </div>
    <div class="lectura">
      <h2>{{lectura}}</h2>
      <p>{{remate}}</p>
    </div>
    <div class="pie"><span class="marca">{{firma_gi}}</span><span>{{aviso}}</span></div>
  </div>
</body>
</html>
```

- [ ] **Step 5: Embeber la marca y verificar los colores**

Run: `uv run python scripts/sincronizar_css_plantillas.py && uv run python scripts/sincronizar_css_plantillas.py --check && uv run python scripts/marca_tokens.py --check`
Expected: la primera corrida escribe `vision.html`; las dos verificaciones pasan. Si `marca_tokens` marca un color, cámbialo por su `var(--rol)`.

- [ ] **Step 6: Correr los tests de Stories**

Run: `uv run pytest tests/test_story_render.py -q`
Expected: PASS, incluidos `test_plantilla_resuelve_sin_huerfanos[vision]` y el test nuevo.

- [ ] **Step 7: Rendir y mirar el PNG**

Run: `uv run --extra stories python scripts/story_render.py --help` para ver la CLI; luego rendir el fixture:
`uv run --extra stories python -c "import json,sys;sys.path.insert(0,'scripts');import story_render as s;from pathlib import Path;p=json.loads(Path('tests/fixtures/stories/payloads/vision.json').read_text(encoding='utf-8'));s.render_story(p,Path('templates/stories/vision.html'),Path('.playwright-mcp/vision_fixture.png'))"`
Abrir `.playwright-mcp/vision_fixture.png` con Read y verificar tildes, comillas, los emoji y que nada se corte. Si algo desborda, ajustar los tamaños de fuente del CSS propio.

- [ ] **Step 8: Commit**

```bash
git add templates/stories/vision.html tests/fixtures/stories/payloads/vision.json tests/test_story_render.py
git commit -m "feat(stories): plantilla vision con variantes cita y meta_precio"
```

---

### Task 3: `pipeline_vision`: días, elección de visión y preparar

**Files:**
- Create: `scripts/pipeline_vision.py`
- Modify: `data/visiones_expertos.json` (agregar `horizonte` a `bci-estudios-rango-850-970`, `jpm-oro-6000-4t26` y `goldman-brent-riesgo-ormuz`)
- Modify: `.gitignore` (agregar `data/avisos/` bajo `data/linkedin/`)
- Test: `tests/test_pipeline_vision.py`

**Interfaces:**
- Consumes (Task 1): `pipeline_linkedin.leer_activos`, `cargar_visiones`, `validar_vision`, `_catalogo`, `_PRECIO`, `MARCA_EDITORIAL`, `ANTIGUEDAD_MAX_DIAS`, `SANTIAGO`.
- Produces:
  - `DIR_TRABAJO: Path` (`data/avisos`), `CANAL_ALIAS = "avisos"`, `VENTANA_VISION_DIAS = 14`, `FRESCURA_HORAS = 2`
  - `dia_de_pieza(fecha: date, feriados: list[str]) -> bool`
  - `variante_de(vision: dict) -> str` (`"cita"` | `"meta_precio"`)
  - `elegir_vision(registro: dict[str, dict], catalogo: set[str], historial: list[dict], canal: str, hoy: date, excluir: set[str] = frozenset()) -> dict | None`
  - `armar_payload(vision: dict, activos: dict, avisos: list[str], ahora: datetime) -> dict`
  - `preparar(ahora: datetime | None = None, leer=None, feriados: list[str] | None = None, ruta_historial: Path | None = None, destino: Path | None = None) -> tuple[int, str, Path | None]`

- [ ] **Step 1: Agregar `horizonte` al registro**

Con Python, para no romper las tildes: en `data/visiones_expertos.json` agregar `"horizonte": "mediano plazo"` a `bci-estudios-rango-850-970`, `"horizonte": "cuarto trimestre de 2026"` a `jpm-oro-6000-4t26` y `"horizonte": "tercer y cuarto trimestre de 2026"` a `goldman-brent-riesgo-ormuz`. Agregar a `_nota` la frase: "horizonte: plazo de la proyección, obligatorio si la cita es una parafrasis con cifra (variante meta_precio)."

- [ ] **Step 2: Escribir los tests que fallan**

`tests/test_pipeline_vision.py`:

```python
"""Tests de la pieza diaria de visión para Avisos (scripts/pipeline_vision.py)."""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "src"))

import pipeline_linkedin as pl  # noqa: E402
import pipeline_vision as pv  # noqa: E402

MARTES = datetime(2026, 9, 29, 11, 30, tzinfo=pl.SANTIAGO)
LUNES = datetime(2026, 9, 28, 11, 30, tzinfo=pl.SANTIAGO)

FILA = {"nombre": "Dólar / Peso Chileno", "digits": 2, "price": 968.30, "s2": 949.6, "s1": 960.9,
        "r1": 974.5, "r2": 977.3, "ema_50": 933.97, "donchian_50_high": 969.7,
        "donchian_50_low": 905.3, "change_pct": 0.85, "rsi_14": 63.8, "direccion": "ALCISTA"}


def _v(vid, fecha, tipo="textual", activo="USDCLP", cita="Frase.", **extra):
    return {"id": vid, "quien": "Ana", "institucion": "Banco", "activo": activo, "tipo": tipo,
            "cita": cita, "fecha": fecha, "fuente": "Medio", "url": "https://x.cl/n", **extra}


REG = {
    "nueva": _v("nueva", "2026-09-25"),
    "vieja": _v("vieja", "2026-06-01"),
    "meta": _v("meta", "2026-09-24", tipo="parafrasis", cita="Base de $905.", horizonte="mediano plazo"),
}
CATALOGO = {"USDCLP", "XAUUSD"}


def test_dia_de_pieza_martes_a_viernes_habiles():
    assert pv.dia_de_pieza(date(2026, 9, 29), [])          # martes
    assert not pv.dia_de_pieza(date(2026, 9, 28), [])      # lunes
    assert not pv.dia_de_pieza(date(2026, 10, 3), [])      # sábado
    assert not pv.dia_de_pieza(date(2026, 11, 26), ["2026-11-26"])  # feriado NYSE, jueves


def test_variante_segun_tipo():
    assert pv.variante_de(REG["meta"]) == "meta_precio"
    assert pv.variante_de(REG["nueva"]) == "cita"
    assert pv.variante_de(_v("p", "2026-09-25", tipo="parafrasis", cita="Sin cifra.")) == "cita"


def test_elige_la_mas_fresca_y_descarta_la_vieja():
    assert pv.elegir_vision(REG, CATALOGO, [], "01", MARTES.date())["id"] == "nueva"


def test_excluye_la_usada_en_14_dias():
    hist = [{"fecha": "2026-09-20", "canal": "01", "tipo": "vision", "clave": "nueva", "variante": "cita"}]
    assert pv.elegir_vision(REG, CATALOGO, hist, "01", MARTES.date())["id"] == "meta"
    hist_viejo = [dict(hist[0], fecha="2026-09-10")]
    assert pv.elegir_vision(REG, CATALOGO, hist_viejo, "01", MARTES.date())["id"] == "nueva"


def test_otro_canal_no_cuenta_para_la_ventana():
    hist = [{"fecha": "2026-09-28", "canal": "02", "tipo": "vision", "clave": "nueva", "variante": "cita"}]
    assert pv.elegir_vision(REG, CATALOGO, hist, "01", MARTES.date())["id"] == "nueva"


def test_empate_por_fecha_gana_la_variante_menos_usada_y_luego_el_id():
    reg = {"b": _v("b", "2026-09-25"),
           "a": _v("a", "2026-09-25", tipo="parafrasis", cita="Meta $900.", horizonte="4T")}
    hist = [{"fecha": "2026-09-27", "canal": "01", "tipo": "vision", "clave": "z", "variante": "cita"}]
    assert pv.elegir_vision(reg, CATALOGO, hist, "01", MARTES.date())["id"] == "a"
    reg2 = {"b": _v("b", "2026-09-25"), "a": _v("a", "2026-09-25")}
    assert pv.elegir_vision(reg2, CATALOGO, [], "01", MARTES.date())["id"] == "a"


def test_meta_precio_sin_horizonte_no_se_elige():
    reg = {"m": _v("m", "2026-09-27", tipo="parafrasis", cita="Meta $900.")}
    assert pv.elegir_vision(reg, CATALOGO, [], "01", MARTES.date()) is None


def test_activo_fuera_del_catalogo_no_se_elige():
    reg = {"x": _v("x", "2026-09-27", activo="TLT")}
    assert pv.elegir_vision(reg, CATALOGO, [], "01", MARTES.date()) is None


def test_ninguna_fresca_da_none():
    assert pv.elegir_vision({"vieja": REG["vieja"]}, CATALOGO, [], "01", MARTES.date()) is None


def _preparar(ahora, tmp_path, leer=None, registro=REG):
    return pv.preparar(
        ahora=ahora,
        leer=leer or (lambda tickers: ({t: dict(FILA) for t in tickers}, [])),
        feriados=[],
        ruta_historial=tmp_path / "hist.json",
        destino=tmp_path / "avisos",
        registro=registro,
        catalogo=CATALOGO,
    )


def test_preparar_lunes_no_corresponde(tmp_path):
    codigo, mensaje, ruta = _preparar(LUNES, tmp_path)
    assert codigo == 0 and ruta is None and "no corresponde" in mensaje
    assert not (tmp_path / "hist.json").exists()


def test_preparar_feriado_no_corresponde(tmp_path):
    codigo, _, ruta = pv.preparar(ahora=MARTES, leer=lambda t: ({}, []), feriados=["2026-09-29"],
                                  ruta_historial=tmp_path / "h.json", destino=tmp_path,
                                  registro=REG, catalogo=CATALOGO)
    assert codigo == 0 and ruta is None


def test_preparar_sin_vision_fresca_es_resultado_valido(tmp_path):
    codigo, mensaje, ruta = _preparar(MARTES, tmp_path, registro={"vieja": REG["vieja"]})
    assert codigo == 0 and ruta is None and "no hay visión fresca" in mensaje


def test_preparar_falla_de_mt5_da_codigo_1(tmp_path):
    def falla(tickers):
        raise SystemExit("MT5 no conectó")
    codigo, mensaje, ruta = _preparar(MARTES, tmp_path, leer=falla)
    assert codigo == 1 and ruta is None and "MT5" in mensaje
    assert not (tmp_path / "hist.json").exists()


def test_preparar_escribe_payload_y_anota_historial(tmp_path):
    codigo, _, ruta = _preparar(MARTES, tmp_path)
    assert codigo == 0 and ruta and ruta.exists()
    p = json.loads(ruta.read_text(encoding="utf-8"))
    assert p["vision_id"] == "nueva" and p["variante"] == "cita" and p["activo"] == "USDCLP"
    assert p["editorial"]["pie"] == pl.MARCA_EDITORIAL and p["_pendiente_editorial"] is True
    hist = json.loads((tmp_path / "hist.json").read_text(encoding="utf-8"))
    assert hist[-1] == {"fecha": "2026-09-29", "canal": pv.canal_avisos(), "tipo": "vision",
                        "clave": "nueva", "variante": "cita"}
```

- [ ] **Step 3: Verificar que fallan**

Run: `uv run pytest tests/test_pipeline_vision.py -q`
Expected: FAIL con `ModuleNotFoundError: No module named 'pipeline_vision'`

- [ ] **Step 4: Implementar la primera mitad de `scripts/pipeline_vision.py`**

```python
"""Pieza diaria de visión para el grupo de Avisos: lo que dice un banco contra nuestros datos.

Mismo reparto que el carrusel: el script produce los datos, `/vision` escribe el texto.

    uv run --with MetaTrader5 python scripts/pipeline_vision.py --preparar
    uv run --with MetaTrader5 python scripts/pipeline_vision.py --refrescar data/avisos/<tanda>
    uv run --extra stories python scripts/pipeline_vision.py --rendir data/avisos/<tanda>

Los frenos son los de `pipeline_linkedin` (`validar_textos`, `validar_cifras`,
`validar_frescura`), llamados y no copiados. Lo propio de esta pieza: el día (martes a
viernes hábil), la visión que no se repite en 14 días, la frescura de 2 horas y el pie
con el cierre estable. Spec: docs/superpowers/specs/2026-09-28-pieza-avisos-vision-design.md
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import pipeline_linkedin as pl  # noqa: E402

DIR_TRABAJO = RAIZ / "data" / "avisos"
PLANTILLA = RAIZ / "templates" / "stories" / "vision.html"
HISTORIAL = RAIZ / "data" / "historial_suplementos.json"
CANAL_ALIAS = "avisos"
VENTANA_VISION_DIAS = 14
FRESCURA_HORAS = 2
DIAS_PIEZA = {1, 2, 3, 4}  # martes a viernes; el lunes es de la agenda
AVISO = "Análisis informativo. No constituye recomendación de inversión."


def canal_avisos() -> str:
    """El canal de Avisos por el mismo índice de alias que usa el despacho."""
    from pipeline_carrusel import resolver_grupo_solicitado

    return resolver_grupo_solicitado(CANAL_ALIAS)


def feriados_nyse() -> list[str]:
    from market_data_mcp.tools.symbol_spec import _cargar_feriados

    return list(_cargar_feriados().get("NYSE", []))


def dia_de_pieza(fecha: date, feriados: list[str]) -> bool:
    return fecha.weekday() in DIAS_PIEZA and fecha.isoformat() not in feriados


def variante_de(vision: dict[str, Any]) -> str:
    if vision.get("tipo") == "parafrasis" and pl._PRECIO.search(str(vision.get("cita", ""))):
        return "meta_precio"
    return "cita"


def _cargar_historial(ruta: Path) -> list[dict[str, Any]]:
    if not ruta.exists():
        return []
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return datos if isinstance(datos, list) else []


def _usos(historial: list[dict[str, Any]], canal: str, hoy: date, dias: int) -> list[dict[str, Any]]:
    salida = []
    for e in historial:
        if e.get("tipo") != "vision" or e.get("canal") != canal:
            continue
        try:
            cuando = date.fromisoformat(str(e.get("fecha")))
        except ValueError:
            continue
        if (hoy - cuando).days < dias:
            salida.append(e)
    return salida


def elegir_vision(registro: dict[str, dict[str, Any]], catalogo: set[str], historial: list[dict[str, Any]],
                  canal: str, hoy: date, excluir: set[str] = frozenset()) -> dict[str, Any] | None:
    """La visión del día: fresca, del catálogo, no repetida en 14 días, más reciente primero."""
    usadas = {e.get("clave") for e in _usos(historial, canal, hoy, VENTANA_VISION_DIAS)}
    semana = [e.get("variante") for e in _usos(historial, canal, hoy, 7)]
    candidatas = []
    for v in registro.values():
        if v["id"] in usadas or v["id"] in excluir or v.get("activo") not in catalogo:
            continue
        if pl.validar_vision(v, hoy, None):
            continue  # vieja, sin URL o sin fecha legible
        variante = variante_de(v)
        if variante == "meta_precio" and not str(v.get("horizonte", "")).strip():
            continue  # la pieza promete el plazo: sin él no se puede armar
        candidatas.append(((-date.fromisoformat(v["fecha"]).toordinal(), semana.count(variante), v["id"]), v))
    return min(candidatas, key=lambda par: par[0])[1] if candidatas else None


def armar_payload(vision: dict[str, Any], activos: dict[str, dict[str, Any]], avisos: list[str],
                  ahora: datetime) -> dict[str, Any]:
    return {
        "version": 1,
        "pieza": "vision",
        "vision_id": vision["id"],
        "variante": variante_de(vision),
        "activo": vision["activo"],
        "datos": {"leido_en": ahora.isoformat(timespec="minutes"), "activos": activos, "avisos": avisos},
        "editorial": {
            "lectura": pl.MARCA_EDITORIAL,
            "remate": pl.MARCA_EDITORIAL,
            "pie": pl.MARCA_EDITORIAL,
            "cifras_citadas": {},
            "aceptar_antiguas": {},
        },
        "_pendiente_editorial": True,
    }


def _registrar(vision: dict[str, Any], canal: str, hoy: date, ruta: Path) -> None:
    """Se anota al preparar, como los conceptos: una tanda descartada gasta la ventana igual."""
    historial = _cargar_historial(ruta)
    historial.append({"fecha": hoy.isoformat(), "canal": canal, "tipo": "vision",
                      "clave": vision["id"], "variante": variante_de(vision)})
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(historial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def preparar(ahora: datetime | None = None, leer: Callable | None = None, feriados: list[str] | None = None,
             ruta_historial: Path | None = None, destino: Path | None = None,
             registro: dict[str, dict[str, Any]] | None = None,
             catalogo: set[str] | None = None) -> tuple[int, str, Path | None]:
    """Código 0: pieza preparada, o un resultado válido sin pieza. Código 1: falla de datos."""
    import screener_gi as sc

    ahora = ahora or datetime.now(pl.SANTIAGO)
    hoy = ahora.date()
    feriados = feriados_nyse() if feriados is None else feriados
    if not dia_de_pieza(hoy, feriados):
        return 0, "hoy no corresponde: la visión sale de martes a viernes hábil.", None

    registro = registro if registro is not None else pl.cargar_visiones()
    catalogo = catalogo if catalogo is not None else set(pl._catalogo())
    ruta_historial = ruta_historial or HISTORIAL
    canal = canal_avisos()
    historial = _cargar_historial(ruta_historial)

    excluir: set[str] = set()
    while True:
        vision = elegir_vision(registro, catalogo, historial, canal, hoy, excluir)
        if vision is None:
            return 0, ("no hay visión fresca para Avisos: registra una en "
                       "data/visiones_expertos.json y vuelve a preparar."), None
        if sc.gate_feriado(vision["activo"], hoy):
            excluir.add(vision["id"])  # su bolsa no cotiza hoy: la siguiente
            continue
        break

    try:
        activos, avisos = (leer or pl.leer_activos)([vision["activo"]])
    except SystemExit as exc:
        return 1, f"falla de datos: {exc}", None

    payload = armar_payload(vision, activos, avisos, ahora)
    carpeta = (destino or DIR_TRABAJO) / f"{ahora:%Y-%m-%d_%H-%M}_vision"
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / "payload.json"
    ruta.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    _registrar(vision, canal, hoy, ruta_historial)
    return 0, str(ruta), ruta
```

- [ ] **Step 5: Correr los tests**

Run: `uv run pytest tests/test_pipeline_vision.py -q`
Expected: PASS. Si `test_preparar_feriado_no_corresponde` falla por la firma de `preparar`, revisar que `registro` y `catalogo` sean parámetros con default `None`, como arriba.

- [ ] **Step 6: Agregar `data/avisos/` al `.gitignore` y hacer commit**

Con Python, insertar `data/avisos/` debajo de la línea `data/linkedin/` de `.gitignore`.

```bash
git add scripts/pipeline_vision.py tests/test_pipeline_vision.py data/visiones_expertos.json .gitignore
git commit -m "feat(vision): elegir la visión del día y preparar la pieza de Avisos"
```

---

### Task 4: `pipeline_vision`: refrescar, validar, rendir y CLI

**Files:**
- Modify: `scripts/pipeline_vision.py`
- Test: `tests/test_pipeline_vision.py`

**Interfaces:**
- Consumes: Task 1 (`validar_textos`, `validar_cifras`, `validar_frescura`, `leido_en`, `formatear`, `validar_vision`), Task 2 (tokens de `vision.html`), Task 3 (`armar_payload`, `preparar`, `canal_avisos`) y `pipeline_carrusel.elegir_variante` / `CIERRES_ALERTA`.
- Produces:
  - `refrescar(directorio: Path, leer: Callable | None = None, ahora: datetime | None = None) -> Path`
  - `validar_pieza(payload: dict, registro: dict, ahora: datetime) -> list[str]`
  - `niveles_de(fila: dict) -> list[dict]`
  - `payload_story(payload: dict, registro: dict) -> dict`
  - `componer_pie(payload: dict) -> str`
  - `rendir(directorio: Path, ahora: datetime | None = None, registro: dict | None = None, render: Callable | None = None) -> Path`
  - `main(argv) -> int` (los códigos de `preparar`; 1 si `--rendir` o `--validar` encuentran errores)

- [ ] **Step 1: Escribir los tests que fallan**

Agregar a `tests/test_pipeline_vision.py`:

```python
def _escrito(tmp_path, pie="El dólar sigue alcista mientras la Fed no cambie de tono.", ahora=MARTES):
    codigo, _, ruta = _preparar(ahora, tmp_path)
    p = json.loads(ruta.read_text(encoding="utf-8"))
    p["editorial"].update(lectura="Los bancos miran meses; el precio de hoy lo manda la Fed.",
                          remate="Hoy el dólar está en $968,30.", pie=pie)
    ruta.write_text(json.dumps(p, ensure_ascii=False), encoding="utf-8")
    return ruta.parent


def test_validar_pieza_completa_pasa(tmp_path):
    carpeta = _escrito(tmp_path)
    p = json.loads((carpeta / "payload.json").read_text(encoding="utf-8"))
    assert pv.validar_pieza(p, REG, MARTES) == []


def test_pie_sin_direccion_se_detiene(tmp_path):
    carpeta = _escrito(tmp_path, pie="El dólar se mueve mientras la Fed decide.")
    p = json.loads((carpeta / "payload.json").read_text(encoding="utf-8"))
    assert any("dirección" in e for e in pv.validar_pieza(p, REG, MARTES))


def test_frescura_de_2_horas(tmp_path):
    carpeta = _escrito(tmp_path)
    p = json.loads((carpeta / "payload.json").read_text(encoding="utf-8"))
    tarde = MARTES + timedelta(hours=2, minutes=1)
    assert any("--refrescar" in e for e in pv.validar_pieza(p, REG, tarde))


def test_sin_niveles_se_detiene(tmp_path):
    carpeta = _escrito(tmp_path)
    p = json.loads((carpeta / "payload.json").read_text(encoding="utf-8"))
    p["datos"]["activos"]["USDCLP"]["s1"] = None
    assert any("niveles" in e for e in pv.validar_pieza(p, REG, MARTES))


def test_refrescar_conserva_vision_y_texto(tmp_path):
    carpeta = _escrito(tmp_path)
    hist_antes = (tmp_path / "hist.json").read_text(encoding="utf-8")
    nueva = dict(FILA, price=970.10)
    pv.refrescar(carpeta, leer=lambda t: ({"USDCLP": nueva}, []), ahora=MARTES + timedelta(hours=3))
    p = json.loads((carpeta / "payload.json").read_text(encoding="utf-8"))
    assert p["vision_id"] == "nueva" and p["editorial"]["pie"].startswith("El dólar sigue")
    assert p["datos"]["activos"]["USDCLP"]["price"] == 970.10
    assert (tmp_path / "hist.json").read_text(encoding="utf-8") == hist_antes


def test_tras_refrescar_la_cifra_vieja_del_texto_se_marca(tmp_path):
    carpeta = _escrito(tmp_path)
    pv.refrescar(carpeta, leer=lambda t: ({"USDCLP": dict(FILA, price=970.10)}, []),
                 ahora=MARTES + timedelta(hours=3))
    p = json.loads((carpeta / "payload.json").read_text(encoding="utf-8"))
    errores = pv.validar_pieza(p, REG, MARTES + timedelta(hours=3))
    assert any("968,30" in e for e in errores)


def test_payload_story_llena_una_sola_variante(tmp_path):
    carpeta = _escrito(tmp_path)
    p = json.loads((carpeta / "payload.json").read_text(encoding="utf-8"))
    s = pv.payload_story(p, REG)
    assert len(s["bloque_cita"]) == 1 and s["bloque_meta"] == []
    assert s["precio"] == "968,30" and s["sesgo_clase"] == "sesgo-alcista"
    assert [n["icono"] for n in s["niveles"]] == ["🟢", "🟡", "🔴"]
    assert "974,50" in s["niveles"][0]["texto"]


def test_payload_story_meta_precio_trae_horizonte():
    p = pv.armar_payload(REG["meta"], {"USDCLP": dict(FILA)}, [], MARTES)
    s = pv.payload_story(p, REG)
    assert s["bloque_cita"] == [] and s["bloque_meta"][0]["horizonte"] == "mediano plazo"


def test_pie_trae_cierre_estable_y_aviso(tmp_path):
    carpeta = _escrito(tmp_path)
    p = json.loads((carpeta / "payload.json").read_text(encoding="utf-8"))
    pie = pv.componer_pie(p)
    assert pie == pv.componer_pie(p)
    assert pv.AVISO in pie
    from pipeline_carrusel import CIERRES_ALERTA
    assert any(c in pie for c in CIERRES_ALERTA)


def test_rendir_escribe_png_y_pie(tmp_path):
    carpeta = _escrito(tmp_path)
    llamado = {}

    def falso_render(story, salida):
        llamado["story"] = story
        salida.write_bytes(b"png")

    png = pv.rendir(carpeta, ahora=MARTES, registro=REG, render=falso_render)
    assert png.exists() and (carpeta / "pie.txt").exists()
    assert "_pendiente_editorial" not in json.loads((carpeta / "payload.json").read_text(encoding="utf-8"))
    assert llamado["story"]["plantilla"] == "vision"


def test_rendir_con_errores_no_escribe(tmp_path):
    codigo, _, ruta = _preparar(MARTES, tmp_path)
    with pytest.raises(SystemExit):
        pv.rendir(ruta.parent, ahora=MARTES, registro=REG, render=lambda s, o: None)
    assert not (ruta.parent / "pie.txt").exists()


def test_pipeline_vision_usa_los_frenos_compartidos():
    fuente = (RAIZ / "scripts" / "pipeline_vision.py").read_text(encoding="utf-8")
    for freno in ("pl.validar_textos(", "pl.validar_cifras(", "pl.validar_frescura(", "pl.validar_vision("):
        assert freno in fuente, f"pipeline_vision no llama a {freno}"
```

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_pipeline_vision.py -q`
Expected: FAIL con `AttributeError: ... has no attribute 'validar_pieza'` (y parecidos).

- [ ] **Step 3: Implementar la segunda mitad de `scripts/pipeline_vision.py`**

```python
def refrescar(directorio: Path, leer: Callable | None = None, ahora: datetime | None = None) -> Path:
    """Relee el terminal sobre la misma tanda. Conserva la visión y el texto, y no toca el historial."""
    ruta = directorio / "payload.json"
    payload = json.loads(ruta.read_text(encoding="utf-8"))
    activos, avisos = (leer or pl.leer_activos)([payload["activo"]])
    payload["datos"]["activos"] = activos
    payload["datos"]["avisos"] = avisos
    payload["datos"]["leido_en"] = (ahora or datetime.now(pl.SANTIAGO)).isoformat(timespec="minutes")
    ruta.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return ruta


def _textos(payload: dict[str, Any]) -> list[tuple[str, str]]:
    ed = payload["editorial"]
    return [(campo, str(ed.get(campo, ""))) for campo in ("lectura", "remate", "pie")]


def niveles_de(fila: dict[str, Any]) -> list[dict[str, str]]:
    """El mapa de niveles como filas de la plantilla, con cifras del terminal."""
    if any(fila.get(c) is None for c in ("s1", "r1", "r2", "s2")):
        return []
    s1, r1, r2, s2 = (pl._nivel(fila, c) for c in ("s1", "r1", "r2", "s2"))
    return [
        {"clase": "resistencia", "icono": "🟢", "texto": f"Sobre {r1}: fuerza compradora; siguiente nivel {r2}"},
        {"clase": "nivel", "icono": "🟡", "texto": (f"Entre {s1} y {r1}: rango; si rompe un borde y vuelve a "
                                                  "entrar, el objetivo pasa a ser el borde contrario")},
        {"clase": "soporte", "icono": "🔴", "texto": f"Bajo {s1}: presión vendedora; siguiente nivel {s2}"},
    ]


def validar_pieza(payload: dict[str, Any], registro: dict[str, dict[str, Any]], ahora: datetime) -> list[str]:
    """Todo lo que impide rendir. Los frenos de texto, cifra, cita y frescura son los compartidos."""
    textos = _textos(payload)
    ed = payload["editorial"]
    errores = pl.validar_textos(textos)
    vid = payload["vision_id"]
    vision = registro.get(vid)
    if vision is None:
        errores.append(f"la visión `{vid}` ya no está en el registro")
    else:
        errores.extend(pl.validar_vision(vision, ahora.date(), ed.get("aceptar_antiguas", {}).get(vid)))
    activos = payload["datos"]["activos"]
    errores.extend(pl.validar_cifras(textos, activos, [vision] if vision else [], ed.get("cifras_citadas", {})))
    errores.extend(pl.validar_frescura(pl.leido_en(payload), ahora, FRESCURA_HORAS,
                                       remedio="Corre --refrescar y vuelve a rendir."))
    fila = activos.get(payload["activo"], {})
    if not niveles_de(fila):
        errores.append("sin niveles del terminal no hay pieza: la imagen promete soporte y resistencia")
    palabra = "alcista" if fila.get("direccion") == "ALCISTA" else "bajista"
    pie = str(ed.get("pie", ""))
    if pl.MARCA_EDITORIAL not in pie and palabra not in pie.lower():
        errores.append(f"pie: tiene que nombrar la dirección de la imagen ({palabra})")
    return errores


def _firma(vision: dict[str, Any]) -> str:
    return f"{vision['quien']} · {vision['institucion']} · {vision.get('fuente', '')}, {vision['fecha']}"


def payload_story(payload: dict[str, Any], registro: dict[str, dict[str, Any]]) -> dict[str, Any]:
    vision = registro[payload["vision_id"]]
    fila = payload["datos"]["activos"][payload["activo"]]
    leido = pl.leido_en(payload)
    precio = pl._nivel(fila, "price")
    alcista = fila["direccion"] == "ALCISTA"
    rotulo = "Cita (traducción nuestra)" if vision.get("tipo") == "traduccion" else "Cita"
    es_meta = payload["variante"] == "meta_precio"
    return {
        "plantilla": "vision",
        "chip": f"VISIÓN · {fila['nombre'].upper()}",
        "sesgo_clase": "sesgo-alcista" if alcista else "sesgo-bajista",
        "direccion_texto": "ALCISTA" if alcista else "BAJISTA",
        "precio": precio,
        "hora_lectura": f"{leido:%H:%M}",
        "lectura": payload["editorial"]["lectura"],
        "remate": payload["editorial"]["remate"],
        "firma_gi": "Grupo Inteligencia · Análisis de Mercado",
        "aviso": AVISO,
        "bloque_cita": [] if es_meta else [{"rotulo": rotulo, "cita": vision["cita"], "firma": _firma(vision)}],
        "bloque_meta": [{"meta": vision["cita"], "horizonte": vision.get("horizonte", ""),
                         "firma": _firma(vision), "precio": precio, "hora": f"{leido:%H:%M}"}] if es_meta else [],
        "niveles": niveles_de(fila),
    }


def componer_pie(payload: dict[str, Any]) -> str:
    """El pie escrito, un cierre estable por pieza y día, y el aviso."""
    from pipeline_carrusel import CIERRES_ALERTA, elegir_variante

    fecha = pl.leido_en(payload).date().isoformat()
    cierre = elegir_variante(CIERRES_ALERTA, payload["vision_id"], fecha)
    return f"{payload['editorial']['pie'].strip()}\n\n{cierre}\n\n{AVISO}"


def _render_real(story: dict[str, Any], salida: Path) -> None:
    from story_render import render_story

    render_story(story, PLANTILLA, salida)


def rendir(directorio: Path, ahora: datetime | None = None, registro: dict[str, dict[str, Any]] | None = None,
           render: Callable | None = None) -> Path:
    ruta = directorio / "payload.json"
    payload = json.loads(ruta.read_text(encoding="utf-8"))
    registro = registro if registro is not None else pl.cargar_visiones()
    errores = validar_pieza(payload, registro, ahora or datetime.now(pl.SANTIAGO))
    if errores:
        raise SystemExit("La pieza no sale:\n  " + "\n  ".join(errores))
    salida = directorio / "vision.png"
    (render or _render_real)(payload_story(payload, registro), salida)
    (directorio / "pie.txt").write_text(componer_pie(payload), encoding="utf-8")
    payload.pop("_pendiente_editorial", None)
    ruta.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return salida


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument("--preparar", action="store_true")
    modo.add_argument("--refrescar", type=Path, metavar="DIR")
    modo.add_argument("--rendir", type=Path, metavar="DIR")
    modo.add_argument("--validar", type=Path, metavar="DIR")
    args = parser.parse_args(argv)

    if args.preparar:
        codigo, mensaje, _ = preparar()
        print(mensaje)
        return codigo
    if args.refrescar:
        print(refrescar(args.refrescar))
        return 0
    if args.validar:
        payload = json.loads((args.validar / "payload.json").read_text(encoding="utf-8"))
        errores = validar_pieza(payload, pl.cargar_visiones(), datetime.now(pl.SANTIAGO))
        print("\n".join(errores) if errores else "ok: la pieza puede rendirse")
        return 1 if errores else 0
    print(rendir(args.rendir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Correr los tests**

Run: `uv run pytest tests/test_pipeline_vision.py -q && uv run ruff check scripts/pipeline_vision.py tests/test_pipeline_vision.py`
Expected: PASS y lint sin errores.

- [ ] **Step 5: Commit**

```bash
git add scripts/pipeline_vision.py tests/test_pipeline_vision.py
git commit -m "feat(vision): refrescar, validar con los frenos compartidos y rendir la pieza"
```

---

### Task 5: El reloj corre piezas y el momento de las 10:30

**Files:**
- Modify: `scripts/reloj_gi.py`: `canales_del_momento` (líneas 166-182), `_correr_preparar` (287-300) y `ejecutar` (300-330).
- Modify: `config/agenda_mercado.json`: agregar el momento a `momentos`.
- Test: `tests/test_reloj_gi.py`, `tests/test_agenda_mercado.py`

**Interfaces:**
- Consumes: `pipeline_carrusel.resolver_grupo_solicitado` y el script `pipeline_vision.py` (Task 3).
- Produces: `PIEZAS: dict[str, dict[str, str]]`, `_correr_preparar(canal: str, pieza: str | None = None) -> dict`.

- [ ] **Step 1: Escribir los tests que fallan**

En `tests/test_reloj_gi.py`:

```python
def test_toda_pieza_de_la_agenda_esta_en_piezas_y_viceversa():
    en_agenda = {m["pieza"] for m in ag.momentos() if m.get("pieza")}
    assert en_agenda == set(reloj.PIEZAS)


def test_el_momento_de_vision_va_a_avisos_por_alias():
    from pipeline_carrusel import resolver_grupo_solicitado

    assert reloj.canales_del_momento(ag.momento("vision_avisos")) == [resolver_grupo_solicitado("avisos")]


def test_un_momento_con_pieza_corre_su_script(monkeypatch):
    llamados = []

    class R:
        returncode, stdout, stderr = 0, "ok", ""

    monkeypatch.setattr(reloj.subprocess, "run", lambda cmd, **kw: llamados.append(cmd) or R())
    reloj._correr_preparar("01_macro_y_apertura", pieza="vision")
    reloj._correr_preparar("02_forex_divisas")
    assert llamados[0][1].endswith("pipeline_vision.py") and llamados[0][2:] == ["--preparar"]
    assert llamados[1][1].endswith("pipeline_carrusel.py") and llamados[1][2:] == ["--preparar", "--grupo", "02_forex_divisas"]


def test_ejecutar_pasa_la_pieza_al_preparar(tmp_path):
    cuando = DESFASE_1.replace(hour=10, minute=35)  # 2026-09-08 es martes
    vistos = []
    res = reloj.ejecutar(cuando=cuando, correr=lambda canal, pieza=None: vistos.append((canal, pieza))
                         or {"canal": canal, "codigo": 0, "salida": "", "error": ""},
                         ruta_libro=tmp_path / "libro.json")
    assert res["momento"] == "vision_avisos" and vistos and vistos[0][1] == "vision"
```

(`DESFASE_1` ya existe en el archivo: `datetime(2026, 9, 8, tzinfo=NY)`, un martes.)

- [ ] **Step 2: Verificar que fallan**

Run: `uv run pytest tests/test_reloj_gi.py -q -k "pieza or vision"`
Expected: FAIL (`AttributeError: module 'reloj_gi' has no attribute 'PIEZAS'`).

- [ ] **Step 3: Agregar el momento a la agenda**

Con Python, agregar a la lista `momentos` de `config/agenda_mercado.json`:

```json
{
  "slug": "vision_avisos",
  "nombre": "Visión del día en Avisos",
  "hora": "10:30",
  "sesion": "apertura_ny",
  "clases": [],
  "pieza": "vision",
  "por_que": "La bolsa ya abrio a las 09:30 y a las 10:30 los indices tienen precio del dia, asi que la pieza puede leer cualquier activo del registro de visiones. Queda a 30 minutos del momento de las 10:00, fuera de la tolerancia de 20: si se pisaran, el reloj dispararia uno y perderia el otro."
}
```

- [ ] **Step 4: Implementar en `scripts/reloj_gi.py`**

Arriba de `canales_del_momento`:

```python
# Las piezas que el reloj prepara además del carrusel, con su script y el alias de
# su canal. Un momento con `pieza` no tiene activos, así que su canal no se deriva
# del mapeo de activo a canal sino del mapeo real de alias a grupo, el mismo que
# usa el despacho (extensión del invariante 4, 2026-09-28).
PIEZAS: dict[str, dict[str, str]] = {
    "vision": {"script": "pipeline_vision.py", "canal_alias": "avisos"},
}
```

En `canales_del_momento`, al inicio del cuerpo:

```python
    if m.get("pieza"):
        from pipeline_carrusel import resolver_grupo_solicitado

        return [resolver_grupo_solicitado(PIEZAS[m["pieza"]]["canal_alias"])]
```

Reemplazar `_correr_preparar`:

```python
def _correr_preparar(canal: str, pieza: str | None = None) -> dict[str, Any]:
    """Una corrida de preparación: el carrusel del canal, o el script de la pieza."""
    if pieza:
        cmd = [sys.executable, str(RAIZ / "scripts" / PIEZAS[pieza]["script"]), "--preparar"]
    else:
        cmd = [sys.executable, str(RAIZ / "scripts" / "pipeline_carrusel.py"),
               "--preparar", "--grupo", canal]
    r = subprocess.run(cmd, cwd=str(RAIZ), capture_output=True, text=True)
    return {
        "canal": canal,
        "codigo": r.returncode,
        "salida": (r.stdout or "")[-1500:],
        "error": (r.stderr or "")[-500:],
    }
```

En `ejecutar`, reemplazar `corridas = [hacer(canal) for canal in est["canales"]]` por:

```python
    pieza = agenda.momento(est["momento"]).get("pieza")
    corridas = [hacer(canal, pieza=pieza) if pieza else hacer(canal) for canal in est["canales"]]
```

(Se mantiene `hacer(canal)` sin `pieza` para los momentos del carrusel: los tests existentes pasan un `correr` que recibe un solo argumento.)

- [ ] **Step 5: Correr los tests del reloj y de la agenda**

Run: `uv run pytest tests/test_reloj_gi.py tests/test_agenda_mercado.py -q`
Expected: PASS. En particular, siguen verdes:
- `test_ningun_par_de_momentos_se_pisa_en_ningun_desfase_del_ano`: 10:30 contra 10:00 da 30 minutos, más que la tolerancia de 20.
- `test_cada_momento_cae_dentro_de_la_sesion_que_declara`: 10:30 está en `apertura_ny`, que va de 08:30 a 12:30.
- `test_todo_momento_llega_a_algun_canal`: el canal sale por el alias.
- `test_el_reloj_no_puede_enviar_nada_a_whatsapp`.
- `test_los_nombres_de_momento_van_acentuados_porque_los_lee_el_cliente`.

Si `test_toda_clase_del_universo_esta_asignada_o_declarada_pendiente` o `medir_direccion` fallan por `clases: []`, revisar que iteren con `m.get("clases", [])`.

- [ ] **Step 6: Commit**

```bash
git add scripts/reloj_gi.py config/agenda_mercado.json tests/test_reloj_gi.py tests/test_agenda_mercado.py
git commit -m "feat(reloj): preparar piezas con su script y el momento de visión a las 10:30 NY"
```

---

### Task 6: Comando `/vision`, AGY y documentación

**Files:**
- Create: `.claude/commands/vision.md`
- Modify: `scripts/agy_workflows.py` (`COMANDOS`) y `CLAUDE.md` (secciones "El reloj de sucesos", "Antigravity (AGY)" y "Slash Commands disponibles")
- Regenerate: `.agents/workflows/vision.md` y `.agents/rules/proyecto.md`
- Test: `tests/test_pipeline_vision.py`

- [ ] **Step 1: Escribir el test que falla**

```python
def test_el_comando_documenta_los_modos_del_script():
    comando = (RAIZ / ".claude" / "commands" / "vision.md").read_text(encoding="utf-8")
    for modo in ("--preparar", "--refrescar", "--rendir", "--validar"):
        assert modo in comando, f"vision.md no documenta {modo}"
    assert "enviar_whatsapp.py --grupo avisos" in comando
```

Run: `uv run pytest tests/test_pipeline_vision.py -k comando -v` → Expected: FAIL (el archivo no existe).

- [ ] **Step 2: Escribir `.claude/commands/vision.md`**

```markdown
Genera la pieza diaria de visión para el grupo de Avisos: lo que dice un banco o analista al
lado de lo que dicen nuestros datos del terminal, como imagen con su pie de WhatsApp.

Uso: `/vision` (sin argumentos). Argumentos: $ARGUMENTS

Spec: `docs/superpowers/specs/2026-09-28-pieza-avisos-vision-design.md`.

## Cuándo sale

De martes a viernes hábil (feriados de NYSE excluidos). El reloj la prepara a las 10:30 de
Nueva York. El lunes es de la agenda de la semana (`/story calendario`), no de esta pieza.

## PASO 1: la tanda del día

Busca en `data/avisos/` la carpeta de hoy (`<fecha>_<hora>_vision`). Si no está, prepárala:

```bash
uv run --with MetaTrader5 python scripts/pipeline_vision.py --preparar
```

La salida es la ruta del `payload.json` o una de dos respuestas válidas sin pieza:
- "hoy no corresponde": es lunes o feriado. No hay nada que hacer.
- "no hay visión fresca para Avisos": sigue con el PASO 2.

Código 1 es falla de datos (MT5): avísale al director.

## PASO 2: si no hay visión fresca

Busca una y regístrala en `data/visiones_expertos.json` con el procedimiento del PASO 2 de
`.claude/commands/linkedin.md` (búsqueda, lectura de la fuente, navegador solo si bloquea, nunca
recorrer LinkedIn). Una proyección con cifra (`parafrasis`) necesita `horizonte`. Después vuelve
a correr `--preparar`.

## PASO 3: escribir

Rellena `editorial` del `payload.json` con la herramienta de edición de archivos del runner o
con Python (`Path.write_text(..., encoding="utf-8")`), nunca por la consola de PowerShell:
- `lectura`: una frase, la conclusión híbrida (qué plazo mira el banco y qué dice el precio hoy).
- `remate`: una frase de apoyo, con la cifra del terminal si la nombras.
- `pie`: el mensaje de WhatsApp sin cierre ni aviso (los agrega el script). Tiene que nombrar la
  dirección de la imagen ("alcista" o "bajista"). Tuteo chileno, sin guion largo, sin voseo.
- `cifras_citadas`: cifras con `$` que no son del terminal ni de la cita, con su motivo.

## PASO 4: rendir

```bash
uv run python scripts/pipeline_vision.py --validar data/avisos/<tanda>
uv run --extra stories python scripts/pipeline_vision.py --rendir data/avisos/<tanda>
```

`<tanda>` es la carpeta del PASO 1. Si el freno dice que los datos tienen más de 2 horas:

```bash
uv run --with MetaTrader5 python scripts/pipeline_vision.py --refrescar data/avisos/<tanda>
```

Conserva la visión y el texto. El freno de cifras marca el precio del texto que cambió:
corrígelo y vuelve a rendir. Mira `vision.png` (tildes, ¿, ·, emoji) antes de mostrarlo.

## PASO 5: aprobación y envío

Muestra la imagen y `pie.txt` al director. Nada sale sin su aprobación. Al aprobar, guarda el
pie con `scripts\ruta_mensaje.ps1 -Tipo alerta` (sin `-Activo` si no aplica) y envía:

```bash
uv run python scripts/enviar_whatsapp.py --grupo avisos --adjunto data/avisos/<tanda>/vision.png --mensaje-archivo <ruta del pie guardado>
```

Si el envío aborta, no se envió: revisa el chat antes de reintentar.
```

- [ ] **Step 3: Exponer a AGY y documentar**

Con Python:
- En `scripts/agy_workflows.py`, agregar a `COMANDOS`: `"vision": "Pieza diaria de visión para Avisos: la visión de un banco contra nuestros datos del terminal, con frenos de cifra, cita y frescura de 2 horas.",`
- En `CLAUDE.md`:
  - "Los siete comandos" → "Los ocho comandos", sumando `/vision` a la lista.
  - "## Slash Commands disponibles (7)" → "(8)".
  - Una fila en la tabla de comandos: `| /vision | Pieza diaria de visión para el grupo de Avisos (martes a viernes, el reloj la prepara a las 10:30 NY): la visión de un banco contra nuestros datos, en imagen con pie. Frescura de 2 h y --refrescar para el director que aprueba tarde. |`
  - Al final de la sección "El reloj de sucesos", un párrafo: "**Piezas además del carrusel (2026-09-28).** Un momento con `pieza` corre su script de `PIEZAS` en vez del carrusel, y su canal sale del mapeo de alias a grupo (`pipeline_carrusel.resolver_grupo_solicitado`), no de una lista escrita: es la extensión del invariante 4 para momentos sin activos. El primero es `vision_avisos`, a las 10:30 NY."

Run: `uv run python scripts/agy_workflows.py && uv run python scripts/agy_reglas.py`
Expected: escribe `vision.md` y regenera `proyecto.md`.

- [ ] **Step 4: Verificar**

Run: `uv run pytest tests/test_pipeline_vision.py tests/test_agy_workflows.py tests/test_agy_reglas.py -q && uv run python scripts/agy_workflows.py --check`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .claude/commands/vision.md scripts/agy_workflows.py CLAUDE.md .agents/rules/proyecto.md .agents/workflows/vision.md tests/test_pipeline_vision.py
git commit -m "feat(vision): comando /vision expuesto a AGY y documentado"
```

---

### Task 7: Verificación de punta a punta

**Files:** ninguno nuevo; es verificación.

- [ ] **Step 1: Suite completa y lint**

Run: `uv run pytest -q --ignore=tests/genesis_bridge && uv run ruff check scripts/pipeline_vision.py scripts/pipeline_linkedin.py scripts/reloj_gi.py`
Expected: todo PASS.

- [ ] **Step 2: El reloj sin efectos**

Run: `uv run python scripts/reloj_gi.py --verificar`
Expected: imprime sesión y momento sin error. A las 10:30-10:50 NY de un martes a viernes muestra `vision_avisos -> canales 01_macro_y_apertura`.

- [ ] **Step 3: Corrida real contra el terminal, sin enviar**

Si hoy no es martes a viernes, pasar `ahora` con un martes desde Python: `preparar(ahora=datetime(<martes>, 11, 30, tzinfo=SANTIAGO), ruta_historial=<ruta temporal>)`, para no ensuciar el historial real. Luego escribir el texto con Python, correr `--validar` y `--rendir`, y abrir `vision.png` con Read. Verificar tildes, comillas, ¿, · y emoji, y que el precio y los niveles coincidan con el `payload.json`.

- [ ] **Step 4: Push y PR**

```bash
git push -u origin feat/pieza-avisos-vision
gh pr create --base feat/linkedin-pipeline --title "feat(vision): pieza diaria de visión para Avisos" --body "<resumen con el spec, los tests y la prueba real>"
```

(Base `feat/linkedin-pipeline` mientras el PR #241 no esté mergeado; después se rebasa a master.)
