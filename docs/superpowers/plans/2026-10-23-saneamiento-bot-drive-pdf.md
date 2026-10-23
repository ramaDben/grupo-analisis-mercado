# Saneamiento del bot de analistas: Drive por sector, PDF del correo y láminas legibles

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corregir lo que salió en la prueba de la tarea 5 del lanzamiento (2026-10-23): ordenar Drive por sector → activo → fecha, que Drive y el celular reciban un PDF del correo (no solo el HTML), que los gráficos se lean y que la espera de `/oportunidad` se diga de forma honesta.

**Architecture:** El HTML de `/oportunidad` es una herramienta con JavaScript: el correo vive en un `<template>` y lo arma `vista()` al cargar, así que el visor de Drive del celular muestra código y no el correo. El PDF se imprime con Chromium (Playwright) **después** de que corra ese JavaScript, reutilizando el `scripts/analista/pdf.py` que se retiró en `a04a3d9`. La carpeta de Drive se deriva del `segmento` que ya resuelve `analista.segmentos`. Los gráficos ganan un parámetro `escala_texto` en el motor compartido, sin cambiar su valor por defecto (el carrusel no se toca).

**Tech Stack:** Python 3.12, Playwright (Chromium), pypdf, pytest, `uv`.

**Spec:** este plan. Los hallazgos salen de la sesión del 2026-10-23 (prueba con `bot_analistas.py --una`) y de las 14 corridas de agy medidas en `data/informes_analistas/*/*/agy_salida_1.json`.

## Global Constraints

- Rama propia desde `master` (`fix/bot-drive-pdf-legible`), nunca commit directo a master; PR al final.
- Texto de cliente: sin guion largo `—` ni medio `–` como inciso; tuteo chileno; todo texto con acentos se escribe con Python o con la herramienta Write, nunca por la consola de PowerShell.
- Nada de links internos en el PDF: los visores de teléfono no los siguen (memoria `feedback_bot_drive_basta`).
- La distribución sigue siendo **solo** la carpeta de Drive: sin hosting, API de Drive ni correo automático.
- `generar_grafico_tv` conserva su salida actual con los argumentos por defecto: lo usan el carrusel y las Stories.
- Los tests del bot no lanzan Chromium ni agy: el PDF se inyecta como dependencia (`a_pdf`) igual que `rendir_lamina`.
- Los PDF se verifican con `pypdf` (ya está en el extra `informe`).

## Precondición (antes de la tarea 1)

En el árbol hay cambios **sin commit** del 2026-10-23 en `scripts/tradingview_grafico.py` (panorama 1250 px, 96-160 velas) y `templates/stories/seguimiento_dia.html` (logo a la vista, vidrio nuevo). La lámina de seguimiento que se probó ya los trae. El director decide si van a su propia rama y PR **antes** de empezar. La tarea 1 toca el mismo archivo y no debe absorberlos sin decisión.

## Review Focus

1. **Un activo sin segmento** (`USDIDX`, un símbolo exacto de MT5 fuera del catálogo): tiene que caer en `Otros/` y no romper el pedido. Test en la tarea 3.
2. **Chromium falla o tarda** al imprimir: el pedido igual se entrega con el HTML, avisa que no hubo PDF y **no** se descuenta otro cupo. Test en la tarea 4.
3. **Imágenes por URL pública** (`publicar_imagen`): el PDF tiene que esperar la red, o sale con huecos donde iban los gráficos. Test en la tarea 4 (`wait_until="networkidle"` + verificación de imágenes cargadas).
4. **Dos seguimientos del mismo activo el mismo día:** la segunda lámina no puede pisar la primera en Drive. Test en la tarea 3.
5. **Análisis reusado** (vigente de otro día): va a la carpeta de la fecha en que se **entregó**, sin duplicar el PDF si ya existe ahí. Test en la tarea 3.

---

### Task 1: Rótulo de la zona ampliada que se entienda solo

En la lámina de seguimiento, "ZONA AMPLIADA · A 3,8 % DEL PRECIO DE HOY" queda suelto sobre las velas: no dice qué nivel está lejos ni hacia dónde.

**Files:**
- Modify: `scripts/tradingview_grafico.py:375-382` (bucle de `amp_arr` / `amp_abj` en `construir_html_limpio`)
- Test: `tests/test_tradingview_grafico.py`

**Interfaces:**
- Produces: `rotulo_zona(nombres: list[str], pct: float, arriba: bool) -> str`

- [ ] **Step 1: Write the failing test**

```python
def test_rotulo_zona_nombra_el_nivel_y_la_direccion():
    assert tg.rotulo_zona(["LÍNEA DE CONTROL"], 3.84, arriba=True) == \
        "↑ ESCALA CORTADA · LÍNEA DE CONTROL A 3,8 % DEL PRECIO DE HOY"
    assert tg.rotulo_zona(["OBJETIVO", "STOP"], 5.0, arriba=False).startswith("↓ ESCALA CORTADA · OBJETIVO Y STOP A 5,0 %")
```

- [ ] **Step 2:** `uv run pytest tests/test_tradingview_grafico.py -k rotulo_zona -v`. Expected: FAIL, `rotulo_zona` no existe.
- [ ] **Step 3: Implement `rotulo_zona`** y úsala en el bucle. Los nombres salen de las etiquetas cuyo precio está en `ps_arr`/`ps_abj` (las mismas tuplas `(precio, nombre, …)` de `etiquetas`). Sube el `font-size` del rótulo de 17 a 22.
- [ ] **Step 4:** corre el archivo completo de tests. Expected: PASS. Regenera una lámina con `bot_analistas.py --una "/seguimiento oro"` y **mira el PNG**: el rótulo se lee y no tapa velas.
- [ ] **Step 5: Commit** `fix(grafico): el corte de escala nombra el nivel lejano y su dirección`

### Task 2: Etiquetas del gráfico de la oportunidad legibles

El gráfico se rinde a 1400 px con `fontSize: 12` y se muestra a unos 1040 px en la lámina y a 640 px en el correo, así que el eje y las píldoras quedan ilegibles en el celular.

**Files:**
- Modify: `scripts/tradingview_grafico.py` (`construir_html_tradingview`, `renderizar_png`, `generar_grafico_tv`)
- Modify: `scripts/analista/preparar.py:174-190` (las dos llamadas de la rama no limpia y `_grafico_dolar`)
- Test: `tests/test_tradingview_grafico.py`, `tests/test_analista_preparar.py`

**Interfaces:**
- Produces: parámetro `escala_texto: float = 1.0` en `construir_html_tradingview`, `renderizar_png` y `generar_grafico_tv`. Multiplica **todo** tamaño de texto del HTML del gráfico (`fontSize` del eje, `.tv-symbol`, `.tv-chip`, `.tv-precio`, `.tv-legend`, pie, píldoras de nivel), redondeado a entero.
- Produces: `ESCALA_TEXTO_ANALISTA = 1.7` en `analista/preparar.py`.

- [ ] **Step 1: Write the failing tests**

```python
def test_escala_texto_por_defecto_no_cambia_el_html():
    assert "fontSize: 12" in tg.construir_html_tradingview(**FIXTURE_TV)

def test_escala_texto_agranda_el_eje_y_la_leyenda():
    html = tg.construir_html_tradingview(**FIXTURE_TV, escala_texto=1.7)
    assert "fontSize: 20" in html and "font-size: 24px" in html  # 12→20, leyenda 14→24
```

En `test_analista_preparar.py`: con `generar_grafico_tv` parcheado, el gráfico del activo y el del dólar se piden con `escala_texto=prep.ESCALA_TEXTO_ANALISTA`, y el de seguimiento (`limpio=True`) **sin** ese argumento.

- [ ] **Step 2:** corre los tests. Expected: FAIL.
- [ ] **Step 3:** implementa el parámetro y pásalo desde `preparar.py`.
- [ ] **Step 4:** corre `tests/test_tradingview_grafico.py tests/test_analista_preparar.py tests/test_story_render.py`. Expected: PASS. Corre `/oportunidad` (Task 6) y **mira** `lamina_xauusd.png` y el correo: las píldoras de nivel se leen sin zoom.
- [ ] **Step 5: Commit** `fix(bot): el gráfico del análisis con letra legible en el celular`

### Task 3: Drive ordenado por sector → activo → fecha

Hoy todo cae en `GI Informes/<fecha>/`. El ejecutivo tiene que poder entrar por sector y activo.

**Files:**
- Create: `scripts/analista/drive.py`
- Modify: `scripts/analista/bot.py:350-362` (`_a_drive`) y sus dos llamadores (oportunidad `:437`, seguimiento)
- Test: `tests/test_analista_drive.py`, `tests/test_analista_bot.py:314` (reemplaza `test_oportunidad_solo_va_a_drive_el_html`)

**Interfaces:**
- Produces:
  - `SECTORES = {"fx": "Divisas", "commodities": "Commodities", "indices": "Índices", "acciones": "Acciones", "etfs": "ETF", "cripto": "Cripto"}`, con `"Otros"` para lo que no resuelve.
  - `carpeta(raiz: Path, ticker: str, nombre: str, dia: date) -> Path` → `raiz / "GI Informes" / <Sector> / f"{nombre} ({ticker})" / dia.isoformat()`. El sector sale de `segmentos.segmento_y_ancla(ticker)`; si devuelve `None` o lanza, `"Otros"`. Saca de `nombre` y `ticker` los caracteres que Windows prohíbe en carpetas (`<>:"/\|?*`).
  - `copiar(rutas: list[tuple[Path, str]], destino: Path) -> None`: cada tupla es (origen, nombre en Drive). Si el nombre ya existe con el mismo tamaño no copia; si existe distinto, agrega sufijo `_2`, `_3`.
  - `Atendedor._a_drive(self, rutas: list[tuple[Path, str]], ahora: datetime, ticker: str, nombre: str) -> str`. Su mensaje dice la ruta relativa: `Guardado en Drive: GI Informes/Commodities/Oro (XAUUSD)/2026-10-23`.

- [ ] **Step 1: Write the failing tests** (`tests/test_analista_drive.py`)

```python
def test_carpeta_por_sector_activo_y_fecha(tmp_path):
    assert dr.carpeta(tmp_path, "XAUUSD", "Oro", date(2026, 10, 23)) == \
        tmp_path / "GI Informes" / "Commodities" / "Oro (XAUUSD)" / "2026-10-23"

def test_par_fuera_del_catalogo_va_a_divisas(tmp_path):
    assert dr.carpeta(tmp_path, "USDCHF", "USD/CHF", date(2026, 10, 23)).parts[-3] == "Divisas"

def test_activo_sin_segmento_va_a_otros(tmp_path):
    assert dr.carpeta(tmp_path, "USDIDX", "Dollar Index", date(2026, 10, 23)).parts[-3] == "Otros"

def test_nombre_con_barra_no_crea_subcarpeta(tmp_path):
    assert dr.carpeta(tmp_path, "USDCLP", "USD/CLP", date(2026, 10, 23)).parts[-2] == "USDCLP (USDCLP)"

def test_dos_laminas_del_mismo_nombre_no_se_pisan(tmp_path):
    a, b = tmp_path / "a.png", tmp_path / "b.png"; a.write_bytes(b"1"); b.write_bytes(b"22")
    dr.copiar([(a, "seguimiento.png")], tmp_path / "d"); dr.copiar([(b, "seguimiento.png")], tmp_path / "d")
    assert sorted(p.name for p in (tmp_path / "d").iterdir()) == ["seguimiento.png", "seguimiento_2.png"]

def test_recopiar_el_mismo_archivo_no_duplica(tmp_path):
    a = tmp_path / "a.png"; a.write_bytes(b"1")
    dr.copiar([(a, "x.png")], tmp_path / "d"); dr.copiar([(a, "x.png")], tmp_path / "d")
    assert [p.name for p in (tmp_path / "d").iterdir()] == ["x.png"]
```

Para el nombre `USD/CLP`, la regla es que los prohibidos se **quitan**, así que el test espera `"USDCLP (USDCLP)"`.

En `test_analista_bot.py`, reemplaza `test_oportunidad_solo_va_a_drive_el_html` por:

```python
def test_oportunidad_va_a_drive_por_sector_activo_y_fecha(armado):
    armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    dia = armado.tmp / "drive" / "GI Informes" / "Commodities" / "Oro (XAUUSD)" / AHORA.date().isoformat()
    assert sorted(p.suffix for p in dia.iterdir()) == [".html", ".pdf"]

def test_seguimiento_deja_su_lamina_en_drive(armado):
    ...  # tras el /oportunidad, un /seguimiento oro deja seguimiento_xauusd_HHMM.png en la misma carpeta
```

(El `.pdf` de este test depende de la tarea 4: escríbelo aquí esperando solo `.html` y la tarea 4 lo amplía.)

- [ ] **Step 2:** `uv run pytest tests/test_analista_drive.py tests/test_analista_bot.py -v`. Expected: FAIL.
- [ ] **Step 3:** implementa `drive.py` y adapta `_a_drive`. Oportunidad copia `(html, html.name)`. Seguimiento copia `(lamina.png, f"seguimiento_{slug(ticker)}_{ahora:%H%M}.png")`; hoy el seguimiento no va a Drive.
- [ ] **Step 4:** corre `tests/test_analista_*.py`. Expected: PASS (salvo el test que la memoria ya conoce por consultar MT5 real, `test_seguimiento_mide_la_simulacion_y_entrega_el_suceso`).
- [ ] **Step 5:** actualiza en `docs/bot-analistas.md` la sección de Drive con el árbol nuevo. Las carpetas viejas `GI Informes/<fecha>/` se dejan como están: no se migran.
- [ ] **Step 6: Commit** `feat(bot): Drive ordenado por sector, activo y fecha`

### Task 4: El PDF del correo, en Drive y en Telegram

Desde el PC el PDF no queda en Drive (no se genera desde `a04a3d9`), y en el celular el HTML no muestra el correo ni sus gráficos.

**Files:**
- Create: `scripts/analista/pdf.py` (base: `git show a04a3d9^:scripts/analista/pdf.py`)
- Modify: `templates/oportunidad/pieza.html:142-148` (`@media print`)
- Modify: `scripts/analista/bot.py` (`Atendedor`: campo `a_pdf`, uso en `_oportunidad`)
- Modify: `scripts/analista/bot.py:53-58` (`AYUDA`: "te llega el correo en PDF para verlo en el celular y el archivo para editarlo en el navegador")
- Test: `tests/test_analista_pdf.py`, `tests/test_analista_bot.py`

**Interfaces:**
- Produces: `PdfFallido(RuntimeError)`, `verificar(ruta: Path) -> Path`, `rendir(html: Path) -> Path` (escribe `html.with_suffix(".pdf")`).
- Produces: `Atendedor.a_pdf: Callable[[Path], Path] = pdf.rendir`. En los fixtures `armado` se reemplaza por un fake que escribe un PDF mínimo, sin Chromium.

Diferencias con el `pdf.py` retirado, que imprimía un HTML estático:
1. `pagina.goto(html.as_uri(), wait_until="networkidle")` en vez de `set_content`, para que carguen las imágenes publicadas por URL.
2. Espera a que el JavaScript arme el correo: `pagina.wait_for_function("(document.getElementById('vista-correo')||{}).innerHTML?.length > 200", timeout=20_000)`, y luego a que todas las `<img>` de `#vista-correo` tengan `complete && naturalWidth > 0`. Si una no carga, lanza `PdfFallido("una imagen del correo no cargó")`.
3. El PDF muestra **solo el correo**: en `@media print` se ocultan además `section.activo` y `.acciones`, junto con lo que ya se ocultaba (`.editor`, `.simulaciones`, `.banda`, …).

- [ ] **Step 1: Write the failing tests**

`tests/test_analista_pdf.py` (con `pytest.importorskip("playwright")` y `pypdf`): arma el HTML con la fixture de `test_analista_oportunidad_html.py` (`oh.guardar` sobre `tmp_path`, imágenes embebidas), llama `pdf.rendir`, y:

```python
texto = "".join(p.extract_text() for p in PdfReader(ruta).pages)
assert titular_correo_esperado in texto            # el correo se armó con JS antes de imprimir
assert "Preparar correo para tu cliente" not in texto  # el editor no sale
assert "Copiar texto de WhatsApp" not in texto
assert len(PdfReader(ruta).pages) >= 1
```

y `test_pdf_vacio_no_se_entrega`: `verificar` sobre un archivo de 0 bytes lanza `PdfFallido`.

En `test_analista_bot.py`:

```python
def test_oportunidad_entrega_html_y_pdf(armado):
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert sorted(p.suffix for p in r.archivos) == [".html", ".pdf"]

def test_sin_pdf_igual_entrega_el_html_y_avisa(armado):
    armado.atendedor.a_pdf = lambda html: (_ for _ in ()).throw(pdf.PdfFallido("Chromium no generó el PDF"))
    r = armado.bot.procesar_uno(b.Pedido(CAMILA, 1, ORO))
    assert [p.suffix for p in r.archivos] == [".html"] and "No pude generar el PDF" in r.texto
    assert armado.estado.usados(CAMILA, AHORA) == 1  # el cupo se gasta una sola vez
```

Amplía `test_oportunidad_va_a_drive_por_sector_activo_y_fecha` para esperar `[".html", ".pdf"]`.

- [ ] **Step 2:** corre los tests. Expected: FAIL.
- [ ] **Step 3:** implementa. Orden en `_oportunidad`: `oh.guardar` → `self.a_pdf(ruta)` (si lanza `PdfFallido`, aviso `"No pude generar el PDF ({exc}): va solo el archivo para el navegador."`) → `_a_drive` con ambos → `Respuesta(..., [pdf, html] o [html], ...)`. El PDF va **primero**: es el que se abre en el celular.
- [ ] **Step 4:** corre `tests/test_analista_*.py`. Expected: PASS. Revisa el envío por Telegram en `bot.py:522`: el tipo `.pdf` ya está mapeado.
- [ ] **Step 5: Commit** `feat(bot): el correo llega también en PDF, a Telegram y a Drive`

### Task 5: La espera de `/oportunidad` dicha con la cifra medida

agy tarda entre 270 y 927 s en las 14 corridas medidas del 19 al 23-10 (mediana ~570 s, unos 9,5 min). Hoy el bot dice "demora unos minutos".

**Files:**
- Modify: `scripts/analista/bot.py:58` (`AYUDA`) y `:665` (mensaje "Recibido. Armando el análisis…")
- Create: `docs/superpowers/notes/2026-10-23-latencia-agy-analista.md`
- Test: `tests/test_analista_bot.py`

- [ ] **Step 1: Write the failing test**

```python
def test_el_recibido_dice_cuanto_demora(armado):
    r = armado.bot.recibir(update("/oportunidad oro"))
    assert "unos 10 minutos" in r[0].texto
```

- [ ] **Step 2:** corre. Expected: FAIL.
- [ ] **Step 3:** textos: en `AYUDA`, "El primero de un activo demora unos 10 minutos (lo redacta con noticias del día)."; en el recibido, agrega "Demora unos 10 minutos: te aviso cuando esté." (sin guion largo).
- [ ] **Step 4:** corre `tests/test_analista_bot.py`. Expected: PASS. Commit `fix(bot): avisa cuánto demora el primer análisis`.
- [ ] **Step 5: Spike de latencia, sin cambiar código.** Mide en qué se van los ~9 minutos: lee la bitácora de agy de 3 corridas (`data/logs/agy/`) y separa búsqueda de fuentes, redacción y validación. Hoy el bot redacta con `tier="flash"` = **Gemini 3.8 Flash High** (`scripts/agy_encargo.py:100`). Corre **tres** pedidos con `tier="flash-lo"` = **Gemini 3.8 Flash Low** (`:101`) sobre copias de `pieza.json` de activos distintos (oro, USD/CLP, un par FX), dentro de `data/informes_analistas/` (agy.py rechaza rutas fuera de ahí) y no en pedidos reales. Anota, para cada una, el tiempo, si pasa `bot_analistas.py --validar`, si trajo fuente directa sin reintento y una lectura del texto contra el de High del mismo activo. **Lanzada el 2026-10-23** fuera del plan, con un script de la sesión: los resultados quedan en `data/informes_analistas/_medicion_flash_lo/comparacion.md` y `resumen.json`. La nota resume esa tabla y la decisión del director. Commit `docs(bot): medición de la latencia de agy`.
  **Resultado (2026-10-23):** Low quedó descartado: copió el texto de los originales en 2 de 3 pedidos y el tercero salió sin fuente. Medium, en una corrida aislada (con los originales apartados), redactó las 3 de verdad y las 3 pasaron el validador. Tiempos High/Medium: oro 488/393 s, USD/CLP 403/431 s, GBP/USD 660/495 s, es decir, unos 15 % menos en promedio, dentro de la variación normal de High. La calidad es equivalente. Detalle en `data/informes_analistas/_medicion_flash_md/comparacion.md`. **Decisión del director (2026-10-23): se queda Flash High.** El paso 5 se cierra con la nota y su commit; no se cambia el tier.
- ~~Step 6: cambiar el tier por defecto.~~ No aplica: el director eligió seguir con Flash High.

### Task 6: Integración, reinicio y prueba punta a punta

- [ ] **Step 1:** `uv run pytest tests/test_analista_*.py tests/test_tradingview_grafico.py tests/test_story_render.py`. Expected: PASS. Anota los fallos que vienen de antes (CI roja de master), sin mezclarlos.
- [ ] **Step 2:** PR a `master` con el resumen; merge cuando el director lo apruebe.
- [ ] **Step 3:** con master al día en el repo principal: `scripts\instalar_bot_telegram.ps1 -Reiniciar`, y confirma que el proceso nuevo arrancó después del merge (`Get-ScheduledTaskInfo GI-BotTelegram`).
- [ ] **Step 4:** el director, desde Telegram: `/recrear oro` (ignora el vigente, no gasta cupo) y `/seguimiento oro`. Verifica:
  - llegan PDF + HTML y la lámina;
  - Drive tiene `GI Informes/Commodities/Oro (XAUUSD)/<hoy>/` con `.html`, `.pdf` y `seguimiento_xauusd_HHMM.png`;
  - **en el celular**, el PDF desde Drive muestra el correo con sus gráficos, y las etiquetas del gráfico se leen sin zoom;
  - el rótulo de la zona ampliada nombra el nivel.
- [ ] **Step 5:** actualiza la memoria del lanzamiento (`project_lanzamiento_bot_analistas_2026_10_22.md`): T5 cerrada o lo que haya quedado.
