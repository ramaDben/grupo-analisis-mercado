# Informe general, firmado y con plan de escenarios: plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** El informe del bot deja de personalizarse por trader, sale firmado por el director con su acreditación verificable y, en `/activo`, suma un plan de escenarios condicionado con estadística medida contra una línea base.

**Architecture:** Todo vive en el paquete `scripts/analista/` del worktree `C:\Users\bbrav\gam-bot` (rama `feat/bot-analistas-telegram`). Python calcula el plan y su estadística y los deja **sellados en `datos`**; agy sigue redactando solo los campos editoriales. El HTML lo arma `informe_html.py` con la maqueta propia.

**Tech Stack:** Python 3.12, pandas, pytest, `uv`. MT5 solo en E2E.

**Spec:** `docs/superpowers/specs/2026-10-08-informe-general-firmado-y-plan-design.md`

## Global Constraints

- Nada de texto de cliente por la consola de PowerShell; escribir con Python `encoding="utf-8"`.
- Sin guion largo ni medio en texto de cliente (lo valida `validar_textos`).
- Precios con los `digits` del activo vía `pipeline_carrusel.formatear_precio(valor, digits)`.
- Los colores solo como `var(--rol)` de `templates/stories/marca.css`; `marca_tokens.py --check` verde.
- Nunca usar los `preparar()` de producción ni tocar `data/carrusel`, `data/screener` o historiales (test existente `test_no_usa_los_preparar_de_produccion`).
- **No mencionar a la CMF** en ningún texto del informe.
- El recorrido se comunica como distancia ("1,5 veces la volatilidad típica de una hora"), **nunca sumado al precio** (comentario de `screener_gi.py` sobre `impulso_adc_atr`).
- Commits en la rama, con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Sin push.
- Desde Git Bash: `MSYS_NO_PATHCONV=1` para argumentos que empiezan con `/`.

## Desviación de la spec (aceptada al planificar)

- La spec dice "y si cabe en el ATR diario restante". `evaluar_activo` no expone `atr_restante_14`; leerlo exige otra llamada D1. **Fuera de v1**: el plan muestra la distancia y no el chequeo de espacio diario.

## Review Focus

1. **Un analista sigue escribiendo "para Juan"** por costumbre: recibe la explicación y no gasta agy ni cupo. Test en Task 1.
2. **El activo sin historia suficiente** (menos de 400 velas H1, p. ej. una acción nueva): el plan sale con "muestra insuficiente", no revienta. Test en Task 4.
3. **R1/S1 de respaldo ATR**: no hay plan y el informe lo dice en una línea. Test en Task 5.
4. **Acreditación que vence entre dos pedidos del mismo día**: la pieza reusada se re-arma con la fecha del pedido, no la de creación. Test en Task 2.
5. **Un texto de agy con "compra" legítimo** ("gerentes de compra (PMI)") pasa el candado. Test en Task 3.

---

### Task 1: Fuera la personalización por trader

**Files:**
- Modify: `scripts/analista/orden.py`, `scripts/analista/informe_html.py`, `templates/informes_analista/base.html`, `templates/informes_analista/informe.css`, `scripts/analista/bot.py`, `scripts/bot_analistas.py` (si imprime trader), `docs/bot-analistas.md`
- Test: `tests/test_analista_orden.py`, `tests/test_analista_informe_html.py`, `tests/test_analista_bot.py`

**Interfaces:**
- Produces: `Orden(pieza, args)` sin `trader`; `od.PERSONALIZACION_RETIRADA: str`; `ih.armar(pieza, dir_pedido, analista, autor, ahora) -> str` (el `autor` lo agrega Task 2; en esta tarea la firma queda `armar(pieza, dir_pedido, analista)`); `ih.guardar(pieza, dir_pedido, analista, nombre_base) -> Path` (una sola ruta).

- [ ] **Step 1: Tests que fallan**

En `tests/test_analista_orden.py` reemplazar los tests de trader por:

```python
def test_para_trader_ya_no_se_acepta():
    with pytest.raises(od.PedidoInvalido) as exc:
        od.interpretar("/activo oro para Juan Pérez", UNIVERSO)
    assert str(exc.value) == od.PERSONALIZACION_RETIRADA


def test_orden_no_tiene_trader():
    assert not hasattr(od.interpretar("/activo oro", UNIVERSO), "trader")
```

En `tests/test_analista_informe_html.py` borrar los tests de versión dedicada y agregar:

```python
def test_un_solo_html_y_sin_personalizacion(tmp_path):
    pieza = fx.pieza_activo(tmp_path)
    ruta = ih.guardar(pieza, tmp_path, fx.ANALISTA, "activo_oro_1100")
    assert ruta == tmp_path / "activo_oro_1100.html"
    html = ruta.read_text(encoding="utf-8")
    for prohibido in ("Preparado para", "Asesor asignado", "in-trader", "btn-guardar"):
        assert prohibido not in html
    assert "Compartido por" in html and fx.ANALISTA["nombre"] in html


def test_contrato_sin_trader_en_paquete_y_plantilla():
    from analista import RAIZ
    fuentes = [*(RAIZ / "scripts" / "analista").glob("*.py"),
               RAIZ / "templates" / "informes_analista" / "base.html"]
    for f in fuentes:
        texto = f.read_text(encoding="utf-8")
        # La palabra "trader" sí puede aparecer (la ayuda dice "compártelo con tu
        # trader"); lo prohibido es el mecanismo de personalización.
        for prohibido in (".trader", "trader=", "TRADER_GENERICO", "sanear_trader",
                          "Preparado para", "Asesor asignado"):
            assert prohibido not in texto, f"{f.name}: {prohibido}"
```

(`fx.pieza_activo` ya existe en `tests/analista_fixtures.py`; si el helper tiene otro nombre, usar el que arma la pieza de activo válida.)

En `tests/test_analista_bot.py`: borrar los tests de reuso "con otro trader" y agregar:

```python
def test_pedido_con_para_no_gasta_agy_ni_cupo():
    bot, llamadas = bot_de_prueba()          # helper existente del archivo
    rs = bot.recibir(update("/activo oro para Juan"))
    assert rs[0].texto == od.PERSONALIZACION_RETIRADA
    assert bot.cola.qsize() == 0 and llamadas["redactar"] == 0
```

- [ ] **Step 2: Correr y ver fallar**

Run: `uv run pytest tests/test_analista_orden.py tests/test_analista_informe_html.py tests/test_analista_bot.py -q`
Expected: FAIL (`PERSONALIZACION_RETIRADA` no existe, "Preparado para" presente).

- [ ] **Step 3: Implementar**

`orden.py`: borrar `_LETRAS_NOMBRE`, `sanear_trader`, el campo `trader` y su docstring; agregar:

```python
PERSONALIZACION_RETIRADA = (
    "Los informes ya no se personalizan: son un análisis general que puedes "
    "compartir tal cual. Pide de nuevo sin «para …», por ejemplo /activo oro."
)
```

y en `interpretar`, en lugar del bloque de `para`:

```python
    cuerpo = resto.strip()
    if re.search(r"(?:^|\s)para\s+\S", cuerpo, flags=re.IGNORECASE):
        raise PedidoInvalido(PERSONALIZACION_RETIRADA)
```

`clave_base` queda igual (ya no menciona trader en el docstring: "Identidad de la pieza para reusarla.").

`base.html`: quitar `{{barra}}` y `{{script}}`; la franja pasa a:

```html
  <section class="franja">
    <div><div class="franja-rotulo">Análisis</div><div class="franja-valor">{{autor_nombre}}</div></div>
    <div><div class="franja-rotulo">Compartido por</div><div class="franja-valor">{{compartido_por}}</div></div>
    <div><div class="franja-rotulo">{{rotulo_referencia}}</div><div class="franja-valor cotizacion">{{referencia}}</div></div>
    <div><div class="franja-rotulo">Edición</div><div class="franja-valor">{{edicion}}</div></div>
  </section>
```

y antes de `</body>` una barra mínima:

```html
<div class="barra no-imprimir"><button type="button" onclick="window.print()">Imprimir o PDF</button></div>
```

`informe.css`: borrar las reglas de `.barra input`, `.barra label` y `.franja-valor.trader` si existen; conservar `.barra` y su botón.

`informe_html.py`: borrar `TRADER_GENERICO`, `BARRA`, `SCRIPT`; `armar(pieza, dir_pedido, analista)` con tokens `autor_nombre` (temporal: `"Benjamín Ignacio Bravo Soza"` constante hasta Task 2) y `compartido_por = e(analista["nombre"])`; quitar `trader`, `asesor`, `barra`, `script`. `guardar` devuelve una `Path`:

```python
def guardar(pieza, dir_pedido, analista, nombre_base) -> Path:
    ruta = dir_pedido / f"{nombre_base}.html"
    ruta.write_text(armar(pieza, dir_pedido, analista), encoding="utf-8")
    return ruta
```

Actualizar el docstring del módulo ("HTML autocontenido, general, igual para todos").

`bot.py`: en `recibir` el `PedidoInvalido` ya responde el texto (sin cambio). En `atender`: `ruta = ih.guardar(...)`, `rutas = [ruta]`, borrar las líneas de `o.trader` y el `reversed`. `_log` sin `trader=`. Mensaje de cupo: "Las que ya existen siguen disponibles." `AYUDA`: borrar el párrafo de "para Nombre Apellido" y agregar "El informe es general: compártelo tal cual con tu trader." Docstring regla 3: "Reusar no cuesta agy: la pieza base vigente se vuelve a entregar sin redactar."

`docs/bot-analistas.md`: borrar la sección de personalización y explicar en dos líneas por qué (análisis general, nadie en GI está inscrito como asesor).

- [ ] **Step 4: Correr**

Run: `uv run pytest tests/test_analista_*.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A scripts/analista templates/informes_analista tests docs/bot-analistas.md scripts/bot_analistas.py
git commit -m "feat(analista): el informe es general, sin versión por trader"
```

---

### Task 2: Autor y bloque de firma

**Files:**
- Create: `scripts/analista/autor.py`
- Modify: `scripts/analista/informe_html.py`, `templates/informes_analista/base.html`, `templates/informes_analista/informe.css`, `scripts/analista/bot.py`, `scripts/bot_analistas.py`, `config/analistas_telegram.example.json`, `.gitignore`
- Test: `tests/test_analista_autor.py`, `tests/test_analista_informe_html.py`, `tests/analista_fixtures.py`

**Interfaces:**
- Produces:
  - `autor.AutorInvalido(ValueError)`
  - `autor.Autor` (dataclass frozen): `nombre: str, cargo: str, foto: Path | None, firma: Path | None, acreditacion: dict | None`
  - `autor.cargar(config: dict, raiz: Path) -> Autor` (lanza `AutorInvalido` si falta `autor`, `nombre` o `cargo`)
  - `autor.vigente(a: Autor, hoy: date) -> bool`
  - `autor.avisos(a: Autor, hoy: date) -> list[str]`
  - `ih.armar(pieza, dir_pedido, analista, autor: Autor, hoy: date) -> str`; `ih.guardar(pieza, dir_pedido, analista, autor, hoy, nombre_base) -> Path`
  - `ih.FRASE_GENERAL: str`
  - `fx.AUTOR` en fixtures.

- [ ] **Step 1: Tests que fallan** (`tests/test_analista_autor.py`)

```python
from datetime import date
import pytest
from analista import autor as au

BASE = {"autor": {"nombre": "Benjamín Ignacio Bravo Soza", "cargo": "Director de Análisis Técnico",
                  "foto": "config/autor/foto.png", "firma": None,
                  "acreditacion": {"entidad": "CMV", "categoria": "Operadores", "numero": "A-32915",
                                   "vigente_hasta": "2028-03-31",
                                   "url": "https://cmvsystem.cmvchile.cl/certificados/635409A1A002"}}}


def test_sin_autor_no_arranca(tmp_path):
    with pytest.raises(au.AutorInvalido):
        au.cargar({}, tmp_path)


def test_vigencia_hasta_el_ultimo_dia_inclusive(tmp_path):
    a = au.cargar(BASE, tmp_path)
    assert au.vigente(a, date(2028, 3, 31)) and not au.vigente(a, date(2028, 4, 1))


def test_foto_declarada_y_ausente_avisa(tmp_path):
    a = au.cargar(BASE, tmp_path)
    assert a.foto is None
    assert any("foto" in x for x in au.avisos(a, date(2026, 10, 8)))


def test_vencida_avisa(tmp_path):
    a = au.cargar(BASE, tmp_path)
    assert any("venció" in x for x in au.avisos(a, date(2028, 4, 1)))
```

En `tests/test_analista_informe_html.py`:

```python
def test_firma_con_acreditacion_vigente(tmp_path):
    html = ih.armar(fx.pieza_activo(tmp_path), tmp_path, fx.ANALISTA, fx.AUTOR, date(2026, 10, 8))
    assert "Acreditación CMV" in html and "A-32915" in html and "635409A1A002" in html
    assert ih.FRASE_GENERAL in html and "CMF" not in html


def test_acreditacion_vencida_no_se_imprime(tmp_path):
    html = ih.armar(fx.pieza_activo(tmp_path), tmp_path, fx.ANALISTA, fx.AUTOR, date(2028, 4, 1))
    assert "A-32915" not in html and ih.FRASE_GENERAL in html


def test_sin_foto_ni_firma_no_deja_hueco(tmp_path):
    html = ih.armar(fx.pieza_activo(tmp_path), tmp_path, fx.ANALISTA, fx.AUTOR, date(2026, 10, 8))
    assert "<img class=\"firma-" not in html   # fx.AUTOR va sin foto ni firma
```

y en `tests/test_analista_bot.py` el foco 4 de revisión:

```python
def test_pieza_reusada_usa_la_fecha_del_pedido(...):
    # crear la pieza el 2028-03-31 23:50 y pedirla de nuevo el 2028-04-01 00:05
    # (reloj inyectado): el segundo HTML no trae "A-32915".
```

(escribirlo con el helper `bot_de_prueba` y `reloj` inyectado del archivo, igual que los tests de reuso existentes; `reuso_minutos` del config de prueba ≥ 30).

- [ ] **Step 2: Ver fallar** — `uv run pytest tests/test_analista_autor.py tests/test_analista_informe_html.py -q`

- [ ] **Step 3: Implementar**

`scripts/analista/autor.py`:

```python
"""Quién firma el informe: el director, con su acreditación dicha con exactitud.

Una credencial vencida impresa es peor que ninguna, así que la vigencia se
decide con la fecha del pedido y no con la del config.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


class AutorInvalido(ValueError):
    """El config no trae quién firma; el bot no arranca así."""


@dataclass(frozen=True)
class Autor:
    nombre: str
    cargo: str
    foto: Path | None
    firma: Path | None
    acreditacion: dict[str, str] | None
    faltantes: tuple[str, ...] = ()


def _archivo(raiz: Path, valor: str | None, nombre: str, faltantes: list[str]) -> Path | None:
    if not valor:
        return None
    ruta = raiz / valor
    if ruta.exists():
        return ruta
    faltantes.append(f"la {nombre} declarada no está en {valor}: el informe sale sin ella")
    return None


def cargar(config: dict[str, Any], raiz: Path) -> Autor:
    datos = config.get("autor")
    if not datos or not datos.get("nombre") or not datos.get("cargo"):
        raise AutorInvalido("config/analistas_telegram.json no trae el bloque «autor» con nombre y cargo")
    faltantes: list[str] = []
    return Autor(
        nombre=datos["nombre"], cargo=datos["cargo"],
        foto=_archivo(raiz, datos.get("foto"), "foto", faltantes),
        firma=_archivo(raiz, datos.get("firma"), "firma", faltantes),
        acreditacion=datos.get("acreditacion"),
        faltantes=tuple(faltantes),
    )


def vigente(a: Autor, hoy: date) -> bool:
    if not a.acreditacion:
        return False
    return hoy <= date.fromisoformat(a.acreditacion["vigente_hasta"])


def avisos(a: Autor, hoy: date) -> list[str]:
    salida = list(a.faltantes)
    if a.acreditacion and not vigente(a, hoy):
        salida.append(f"la acreditación {a.acreditacion['numero']} venció el "
                      f"{a.acreditacion['vigente_hasta']}: el informe sale sin ella, renuévala")
    return salida
```

`informe_html.py`:

```python
FRASE_GENERAL = ("Análisis general de mercado, idéntico para todos sus destinatarios. "
                 "No es asesoría de inversión ni considera el perfil de quien lo lee.")


def bloque_firma(a: "Autor", hoy: date) -> str:
    from analista import autor as au

    foto = f'<img class="firma-foto" src="{_data_uri(a.foto)}" alt="{e(a.nombre)}">' if a.foto else ""
    firma = f'<img class="firma-trazo" src="{_data_uri(a.firma)}" alt="Firma">' if a.firma else ""
    cred = ""
    if au.vigente(a, hoy):
        ac = a.acreditacion
        hasta = date.fromisoformat(ac["vigente_hasta"]).strftime("%d-%m-%Y")
        cred = (f'<p class="firma-credencial">Acreditación {e(ac["entidad"])} · Categoría {e(ac["categoria"])}'
                f' · N° {e(ac["numero"])} · Vigente hasta el {hasta}</p>'
                f'<p class="firma-credencial">Verificable en <a href="{e(ac["url"])}">{e(ac["url"].split("//", 1)[-1])}</a></p>')
    return (f'<section class="firma">{foto}<div class="firma-texto">{firma}'
            f'<p class="firma-nombre">{e(a.nombre)}</p>'
            f'<p class="firma-cargo">{e(a.cargo)} · Grupo Inteligencia</p>{cred}'
            f'<p class="firma-general">{e(FRASE_GENERAL)}</p></div></section>')
```

`_data_uri` debe aceptar `.png`, `.jpg` y `.jpeg` (ya lo hace). `armar(pieza, dir_pedido, analista, autor, hoy)`: token `autor_nombre = e(autor.nombre)`, token nuevo `firma = bloque_firma(autor, hoy)`. En `base.html`, `{{firma}}` entre `</article>` y el lema. `guardar(pieza, dir_pedido, analista, autor, hoy, nombre_base)`.

`informe.css` (pt, solo roles de marca):

```css
.firma { display: flex; gap: 14pt; align-items: center; margin: 22pt 0 10pt;
  padding: 14pt 16pt; border: 1px solid var(--papel-linea); border-radius: 8pt; background: var(--papel-alt); }
.firma-foto { width: 2.5cm; height: 2.5cm; border-radius: 50%; object-fit: cover; flex: 0 0 auto; }
.firma-trazo { height: 34pt; display: block; margin-bottom: 2pt; }
.firma-nombre { font-weight: 700; font-size: 12pt; color: var(--tinta); margin: 0; }
.firma-cargo { font-size: 10.5pt; color: var(--tinta-2); margin: 0 0 4pt; }
.firma-credencial { font-size: 9.5pt; color: var(--tinta-2); margin: 0; }
.firma-credencial a { color: var(--acento-doc); }
.firma-general { font-size: 9.5pt; color: var(--tinta-3); margin: 6pt 0 0; }
@media print { .firma { break-inside: avoid; } }
```

`bot.py`: `Atendedor` gana campo `autor: Autor`; `atender` usa `hoy = ahora.date()` en `ih.guardar(...)` y suma `au.avisos(self.autor, hoy)` a las líneas `⚠️`. `scripts/bot_analistas.py`: al construir el `Atendedor`, `autor=au.cargar(config, RAIZ)`; si lanza `AutorInvalido`, imprime el motivo y sale con código 2 (vale para `--escuchar` y `--una`).

`fixtures`: `AUTOR = Autor("Benjamín Ignacio Bravo Soza", "Director de Análisis Técnico", None, None, {...los datos de BASE...})`.

`config/analistas_telegram.example.json`: agregar el bloque `autor` con marcadores (`"nombre": "Nombre Apellido"`, `"numero": "A-00000"`, `"url": "https://…"`). `.gitignore`: `config/autor/`.

Copiar la foto real al config local (no versionado), desde Python:

```bash
uv run python -c "import shutil,pathlib; d=pathlib.Path('config/autor'); d.mkdir(parents=True,exist_ok=True); shutil.copy(r'C:\Users\bbrav\AppData\Local\Temp\claude\C--Users-bbrav-grupo-analisis-mercado\c1a735a8-3bdc-4a21-bce4-4e2336e0addf\images\3.png', d/'foto.png')"
```

y el bloque `autor` real en `config/analistas_telegram.json` (gitignoreado) con los datos de la spec.

- [ ] **Step 4: Correr** — `uv run pytest tests/test_analista_*.py -q && uv run python scripts/marca_tokens.py --check` → PASS

- [ ] **Step 5: Commit** — `git commit -m "feat(analista): el informe va firmado por el director con su acreditación verificable"`

---

### Task 3: Candados de lenguaje

**Files:**
- Modify: `scripts/analista/esquema.py`, `.claude/commands/analista.md`; regenerar `.agents/workflows/analista.md`
- Test: `tests/test_analista_esquema.py`

**Interfaces:**
- Produces: `es.FRASES_PROHIBIDAS: tuple[str, ...]`; `es.frases_prohibidas(texto: str) -> list[str]` (devuelve las frases encontradas, en su forma de la lista). `errores()` las reporta como `"{campo}: «{frase}» es una instrucción de operar o una recomendación; el informe es análisis general"`.

- [ ] **Step 1: Tests**

```python
@pytest.mark.parametrize("texto", [
    "Es momento de comprar oro.", "Te recomiendo vender.", "Abre una posición larga.",
    "Toma ganancias en la resistencia.", "Usa 2 lotes.", "Recomendamos esperar.",
    "Señal de compra clara.", "Deberías vender ya.", "No arriesgues más del 2 % de tu capital.",
])
def test_frases_prohibidas_caen(texto):
    assert es.frases_prohibidas(texto)


@pytest.mark.parametrize("texto", [
    "El índice de gerentes de compra (PMI) sube.", "Si rompe un borde y vuelve a entrar, es falso quiebre.",
    "El escenario alcista se activa sobre la resistencia.", "Hay presión compradora.",
    "Los vendedores dominan la sesión.",
])
def test_formas_impersonales_pasan(texto):
    assert es.frases_prohibidas(texto) == []


def test_errores_reporta_la_frase(tmp_path):
    p = fx.pieza_activo(tmp_path)
    p["editorial"]["que_no_hacer"] = "Te recomiendo no entrar tarde."
    assert any("te recomiendo" in x for x in es.errores(p))
```

- [ ] **Step 2: Ver fallar**

- [ ] **Step 3: Implementar** en `esquema.py`:

```python
# Frases y no palabras sueltas: "compra" o "entrar" aparecen en texto legítimo
# ("gerentes de compra (PMI)", "vuelve a entrar") y un candado que bloquea eso
# termina desactivado. Se comparan sin tildes y en minúsculas.
FRASES_PROHIBIDAS: tuple[str, ...] = (
    "compra ya", "vende ya", "es momento de comprar", "es momento de vender",
    "entra al mercado", "abre una posicion", "cierra tu posicion", "toma ganancias",
    "debes comprar", "debes vender", "deberias comprar", "deberias vender",
    "recomendamos", "te recomiendo", "te conviene", "senal de compra", "senal de venta",
    "lote", "lotes", "apalanca", "de tu capital", "arriesga",
)


def _plano(texto: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def frases_prohibidas(texto: str) -> list[str]:
    plano = _plano(texto)
    return [f for f in FRASES_PROHIBIDAS if re.search(rf"\b{re.escape(f)}", plano)]
```

Nota: `\b` al inicio y sin `\b` al final deja que "arriesga" atrape "arriesgues" y "apalanca" atrape "apalancamiento"; "lote" sin borde final atraparía "lotería": usar `rf"\b{re.escape(f)}\b"` para `lote`/`lotes` y prefijo para el resto. Implementarlo con un conjunto `_PALABRA_EXACTA = {"lote", "lotes"}`.

En `errores`, dentro del bucle `for donde, texto in pares:` agregar el reporte.

`analista.md`, al final de las reglas:

```
10. **Análisis general, nunca una instrucción.** Escribe en impersonal y condicional ("el
    escenario se activa si…", "la presión compradora"). Nunca le digas al lector que compre,
    venda, entre, cierre ni cuánto arriesgar, y no recomiendes. El bot rechaza esas frases.
```

Regenerar: `uv run python scripts/agy_workflows.py` y verificar `--check`.

- [ ] **Step 4: Correr** — `uv run pytest tests/test_analista_esquema.py tests/test_agy_workflows.py -q` → PASS

- [ ] **Step 5: Commit** — `git commit -m "feat(analista): candados de lenguaje contra instrucciones de operar"`

---

### Task 4: Estadística del plan (módulo puro)

**Files:**
- Create: `scripts/analista/estadistica.py`
- Test: `tests/test_analista_estadistica.py`

**Interfaces:**
- Consumes: `market_data_mcp.analisis._get_support_resistance(df, current, atr14, digits)`, `market_data_mcp.mt5_client.ema`, `.atr`.
- Produces:
  - `VENTANA = 300`, `HORIZONTE = 24`, `MULT_RECORRIDO = 1.5`, `CHANDELIER_N = 22`, `CHANDELIER_K = 3.0`, `MUESTRA_MINIMA = 30`, `VENTAJA_MINIMA = 5`
  - `Desenlace = Literal["recorrido", "invalidacion", "sin_definicion"]`
  - `desenlace(df, i, alcista: bool) -> Desenlace` (entrada = cierre de la vela `i`)
  - `eventos(df, digits, alcista: bool) -> list[int]` (índices de vela del evento)
  - `@dataclass Estadistica: casos: int, pct_condicion: int | None, pct_base: int | None, desde: str, hasta: str`
  - `medir(df, digits, alcista: bool) -> Estadistica`

`df` es un DataFrame con columnas `time, open, high, low, close` y solo velas **cerradas**, en orden.

- [ ] **Step 1: Tests**

```python
import pandas as pd
import pytest
from analista import estadistica as est


def serie(cierres, rango=1.0):
    return pd.DataFrame({
        "time": pd.date_range("2025-01-01", periods=len(cierres), freq="h"),
        "open": cierres, "close": cierres,
        "high": [c + rango / 2 for c in cierres], "low": [c - rango / 2 for c in cierres],
    })


def test_desenlace_recorrido():
    df = serie([100.0] * 60 + [100.0] + [100.0 + k for k in range(1, 25)])
    assert est.desenlace(df, 60, alcista=True) == "recorrido"


def test_desenlace_invalidacion():
    df = serie([100.0] * 60 + [100.0] + [100.0 - 2 * k for k in range(1, 25)])
    assert est.desenlace(df, 60, alcista=True) == "invalidacion"


def test_empate_en_la_misma_vela_es_invalidacion():
    df = serie([100.0] * 61 + [100.0] * 24)
    df.loc[61, "high"], df.loc[61, "low"] = 200.0, 0.0
    assert est.desenlace(df, 60, alcista=True) == "invalidacion"


def test_sin_definicion():
    df = serie([100.0] * 85, rango=1.0)
    assert est.desenlace(df, 60, alcista=True) == "sin_definicion"


def test_no_mira_el_futuro():
    import numpy as np
    rng = np.random.default_rng(1)
    base = list(100 + rng.standard_normal(900).cumsum())
    a = est.eventos(serie(base), 2, alcista=True)
    cambiado = base[:600] + [b * 3 for b in base[600:]]
    b = est.eventos(serie(cambiado), 2, alcista=True)
    assert [i for i in a if i < 600] == [i for i in b if i < 600]


def test_muestra_insuficiente():
    r = est.medir(serie([100.0] * 400), 2, alcista=True)
    assert r.casos < est.MUESTRA_MINIMA and r.pct_condicion is None


def test_serie_corta_no_revienta():
    r = est.medir(serie([100.0] * 50), 2, alcista=True)
    assert r.casos == 0 and r.pct_base is None
```

- [ ] **Step 2: Ver fallar**

- [ ] **Step 3: Implementar**

```python
"""Qué tan seguido se cumplió, en el pasado del mismo activo, el plan que el informe arma hoy.

Dos decisiones que no conviene revertir:

1. **Los niveles históricos salen de la misma función que los de hoy**
   (`_get_support_resistance` sobre las 300 velas previas). Una segunda
   definición de "resistencia" para la estadística mediría otra cosa.
2. **Siempre contra una línea base.** La invalidación queda a ~3 ATR y el
   recorrido a 1,5 ATR, así que el recorrido sale primero muchas veces por pura
   geometría. "Lo logró el 70 %" sin la cifra de una hora cualquiera engaña.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from market_data_mcp.analisis import _get_support_resistance
from market_data_mcp.mt5_client import atr, ema

VENTANA, HORIZONTE = 300, 24
MULT_RECORRIDO, CHANDELIER_N, CHANDELIER_K = 1.5, 22, 3.0
MUESTRA_MINIMA, VENTAJA_MINIMA = 30, 5

Desenlace = Literal["recorrido", "invalidacion", "sin_definicion"]


@dataclass(frozen=True)
class Estadistica:
    casos: int
    pct_condicion: int | None
    pct_base: int | None
    desde: str
    hasta: str


def _indicadores(df: pd.DataFrame) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)
    out["atr14"] = atr(df, 14)
    out["atr22"] = atr(df, CHANDELIER_N)
    out["ema50"] = ema(df["close"], 50)
    out["hh"] = df["high"].rolling(CHANDELIER_N, min_periods=1).max()
    out["ll"] = df["low"].rolling(CHANDELIER_N, min_periods=1).min()
    return out


def desenlace(df: pd.DataFrame, i: int, alcista: bool, ind: pd.DataFrame | None = None) -> Desenlace:
    ind = _indicadores(df) if ind is None else ind
    entrada = float(df["close"].iat[i])
    paso = MULT_RECORRIDO * float(ind["atr14"].iat[i])
    signo = 1 if alcista else -1
    objetivo = entrada + signo * paso
    stop = (float(ind["hh"].iat[i]) - CHANDELIER_K * float(ind["atr22"].iat[i]) if alcista
            else float(ind["ll"].iat[i]) + CHANDELIER_K * float(ind["atr22"].iat[i]))
    for j in range(i + 1, min(i + 1 + HORIZONTE, len(df))):
        alto, bajo = float(df["high"].iat[j]), float(df["low"].iat[j])
        toca_stop = bajo <= stop if alcista else alto >= stop
        toca_obj = alto >= objetivo if alcista else bajo <= objetivo
        if toca_stop:            # empate en la misma vela: conservador
            return "invalidacion"
        if toca_obj:
            return "recorrido"
        # Chandelier arrastrado: solo se mueve a favor.
        nuevo = (float(ind["hh"].iat[j]) - CHANDELIER_K * float(ind["atr22"].iat[j]) if alcista
                 else float(ind["ll"].iat[j]) + CHANDELIER_K * float(ind["atr22"].iat[j]))
        stop = max(stop, nuevo) if alcista else min(stop, nuevo)
    return "sin_definicion"


def eventos(df: pd.DataFrame, digits: int, alcista: bool, ind: pd.DataFrame | None = None) -> list[int]:
    ind = _indicadores(df) if ind is None else ind
    salida: list[int] = []
    ultimo_nivel: float | None = None
    for i in range(VENTANA, len(df)):
        ventana = df.iloc[i - VENTANA:i]
        previo = float(df["close"].iat[i - 1])
        niveles = _get_support_resistance(ventana, previo, float(ind["atr14"].iat[i - 1]), digits)
        clave, lado = ("r1", 1) if alcista else ("s1", -1)
        if niveles["origen"][clave] != "swing":
            continue
        nivel = niveles[clave]
        cierre = float(df["close"].iat[i])
        cruza = (cierre > nivel >= previo) if alcista else (cierre < nivel <= previo)
        a_favor = (cierre > float(ind["ema50"].iat[i])) if alcista else (cierre < float(ind["ema50"].iat[i]))
        if cruza and a_favor and nivel != ultimo_nivel:
            salida.append(i)
            ultimo_nivel = nivel
    return salida


def _pct(resultados: list[Desenlace]) -> int | None:
    return round(100 * resultados.count("recorrido") / len(resultados)) if resultados else None


def medir(df: pd.DataFrame, digits: int, alcista: bool) -> Estadistica:
    desde = str(df["time"].iat[0])[:10] if len(df) else ""
    hasta = str(df["time"].iat[-1])[:10] if len(df) else ""
    if len(df) <= VENTANA + HORIZONTE:
        return Estadistica(0, None, None, desde, hasta)
    ind = _indicadores(df)
    limite = len(df) - HORIZONTE          # sin horizonte completo, el caso no cuenta
    idx = [i for i in eventos(df, digits, alcista, ind) if i < limite]
    base = [desenlace(df, i, alcista, ind) for i in range(VENTANA, limite)]
    cond = [desenlace(df, i, alcista, ind) for i in idx]
    pct_c = _pct(cond) if len(cond) >= MUESTRA_MINIMA else None
    return Estadistica(len(cond), pct_c, _pct(base), desde, hasta)
```

Nota para quien implementa: la línea base recorre ~9.700 velas con hasta 24 pasos cada una (~230 mil iteraciones, < 2 s). El costo fuerte es `eventos` (9.700 llamadas a `_get_support_resistance`). Medirlo en Step 4 con la serie real de `data central/DATA PRECIOS OHLC/XAUUSD_H1.json` (`rows`); si pasa de 20 s, cachear el resultado de `medir` por `(ticker, alcista, hasta)` en `data/informes_analistas/.cache_estadistica.json` (la serie no cambia dentro de la hora).

- [ ] **Step 4: Correr y medir**

```bash
uv run pytest tests/test_analista_estadistica.py -q
uv run python -c "import json,time,pandas as pd,sys; sys.path[:0]=['src','scripts']; from analista import estadistica as e; d=json.load(open(r'C:/Users/bbrav/grupo-analisis-mercado/data central/DATA PRECIOS OHLC/XAUUSD_H1.json',encoding='utf-8')); df=pd.DataFrame(d['rows']); t=time.time(); print(e.medir(df,2,True), round(time.time()-t,1),'s')"
```

Expected: tests PASS; anotar el tiempo en el commit.

- [ ] **Step 5: Commit** — `git commit -m "feat(analista): estadística del plan contra una línea base, sin mirar el futuro"`

---

### Task 5: El plan en la pieza de activo

**Files:**
- Create: `scripts/analista/plan.py`
- Modify: `scripts/analista/preparar.py`, `scripts/analista/informe_html.py`, `templates/informes_analista/informe.css`, `.claude/commands/analista.md` (+ regenerar)
- Test: `tests/test_analista_plan.py`, `tests/test_analista_preparar.py`, `tests/test_analista_informe_html.py`

**Interfaces:**
- Consumes: `estadistica.medir`, `estadistica.Estadistica`, `pc.formatear_precio(valor, digits)`, la lectura del terminal (`lectura["h1"]` de `pa.leer_terminal`: `s1, r1, niveles_origen, atr_14, ema_50, price`).
- Produces:
  - `plan.armar(h1: dict, digits: int, sesgo: str, nombre: str, est: Estadistica | None, ultima_vela: dict) -> dict` con claves `hay_plan: bool`, `motivo: str` (si no hay), `sesgo`, `gatillo`, `invalidacion`, `recorrido`, `estadistica`, `estado`, `niveles: {"gatillo": float, "invalidacion": float}` (crudos, para la bitácora).
  - `Lectores.serie_h1: Callable[[str], pd.DataFrame]` (real: `mt5_client.get_rates(ticker, "H1", 10000).iloc[:-1]`).
  - `datos["plan"]` en la pieza de activo (sellado por la huella).
  - `ih.seccion_plan(plan: dict) -> str`.

- [ ] **Step 1: Tests** (`tests/test_analista_plan.py`)

```python
from analista import plan as pl
from analista.estadistica import Estadistica

H1 = {"price": 4010.0, "s1": 3990.0, "r1": 4020.0, "atr_14": 8.0, "ema_50": 4000.0,
      "niveles_origen": {"s1": "swing", "r1": "swing", "s2": "atr", "r2": "atr"}}
VELA = {"close": 4012.0, "hh22": 4030.0, "ll22": 3970.0, "atr22": 9.0, "vela": "2026-10-08 10:00:00"}


def test_plan_alcista_con_ventaja():
    p = pl.armar(H1, 2, "Alcista", "Oro", Estadistica(42, 64, 55, "2025-01-27", "2026-10-08"), VELA)
    assert p["hay_plan"] and "4.020,00" in p["gatillo"] and "cierre de vela de 1 hora sobre" in p["gatillo"]
    assert "4.003,00" in p["invalidacion"]          # 4030 - 3 * 9
    assert "12,00" in p["recorrido"] and "4.032" not in p["recorrido"]   # distancia, nunca precio
    assert "42 veces" in p["estadistica"] and "64 %" in p["estadistica"] and "55 %" in p["estadistica"]
    assert p["estado"].startswith("Armado")


def test_sin_ventaja_lo_dice():
    p = pl.armar(H1, 2, "Alcista", "Oro", Estadistica(42, 57, 55, "2025-01-27", "2026-10-08"), VELA)
    assert "no ha mostrado ventaja" in p["estadistica"]


def test_muestra_insuficiente_sin_porcentaje():
    p = pl.armar(H1, 2, "Alcista", "Oro", Estadistica(12, None, 55, "2025-01-27", "2026-10-08"), VELA)
    assert "Muestra insuficiente" in p["estadistica"] and "%" not in p["estadistica"]


def test_nivel_de_respaldo_atr_no_tiene_plan():
    h1 = {**H1, "niveles_origen": {**H1["niveles_origen"], "r1": "atr"}}
    p = pl.armar(h1, 2, "Alcista", "Oro", None, VELA)
    assert not p["hay_plan"] and "estructura" in p["motivo"]


def test_bajista_es_espejo():
    p = pl.armar(H1, 2, "Bajista", "Oro", Estadistica(35, 60, 50, "a", "b"), VELA)
    assert "bajo 3.990,00" in p["gatillo"] and "3.997,00" in p["invalidacion"]   # 3970 + 27


def test_estado_activado():
    p = pl.armar(H1, 2, "Alcista", "Oro", None, {**VELA, "close": 4025.0})
    assert p["estado"].startswith("Activado")


def test_textos_del_plan_pasan_los_candados():
    from analista import esquema as es
    p = pl.armar(H1, 2, "Alcista", "Oro", Estadistica(42, 64, 55, "a", "b"), VELA)
    for k in ("gatillo", "invalidacion", "recorrido", "estadistica", "estado"):
        assert es.frases_prohibidas(p[k]) == [] and "—" not in p[k]
```

En `tests/test_analista_preparar.py`, en `lectores()` agregar `serie_h1=lambda t: _serie_plana(400)` (helper que arma un DataFrame `time/open/high/low/close` de 400 velas) y en el `terminal` del doble agregar `"h1": {**H1 del test_plan}`; luego:

```python
def test_activo_trae_el_plan_sellado(tmp_path):
    hecha = pr.preparar(Orden("activo", {"ticker": "XAGUSD"}), tmp_path, AHORA, lectores())
    plan = hecha.pieza["datos"]["plan"]
    assert "hay_plan" in plan
    hecha.pieza["datos"]["plan"]["gatillo"] = "otra cosa"
    assert any("cambiaron" in x for x in es.errores(hecha.pieza))
```

En `tests/test_analista_informe_html.py`:

```python
def test_seccion_plan_y_sin_plan(tmp_path):
    con = ih.seccion_plan({"hay_plan": True, "sesgo": "Alcista", "gatillo": "G", "invalidacion": "I",
                           "recorrido": "R", "estadistica": "E", "estado": "Armado"})
    assert "Plan de escenarios" in con and "G" in con and "E" in con
    sin = ih.seccion_plan({"hay_plan": False, "motivo": "M"})
    assert "M" in sin and "Gatillo" not in sin
```

- [ ] **Step 2: Ver fallar**

- [ ] **Step 3: Implementar**

`scripts/analista/plan.py`:

```python
"""El plan de escenarios del informe de activo, escrito por Python y no por agy.

Es lo que el informe trae y WhatsApp no: la condición, dónde se anula y qué tan
seguido funcionó antes, siempre contra una hora cualquiera. Habla en
condicional e impersonal: describe un escenario, no le dice a nadie qué hacer.
"""
from __future__ import annotations

from typing import Any

from analista.estadistica import CHANDELIER_K, MULT_RECORRIDO, VENTAJA_MINIMA, Estadistica


def _fmt(valor: float, digits: int) -> str:
    import pipeline_carrusel as pc

    return pc.formatear_precio(valor, digits)


def _frase_estadistica(est: Estadistica | None, nombre: str) -> str:
    if est is None or est.pct_base is None:
        return "Sin historia suficiente del activo para medir esta condición."
    if est.pct_condicion is None:
        return f"Muestra insuficiente para una estadística ({est.casos} casos desde {est.desde})."
    texto = (f"Desde el {est.desde}, esta condición se dio {est.casos} veces en {nombre}. "
             f"El precio recorrió 1,5 veces la volatilidad típica de una hora antes de tocar la "
             f"invalidación en el {est.pct_condicion} % de los casos. Desde una hora cualquiera del "
             f"mismo período, la misma regla se cumplió en el {est.pct_base} %.")
    if est.pct_condicion - est.pct_base < VENTAJA_MINIMA:
        texto += " En este activo la condición no ha mostrado ventaja frente a una hora cualquiera."
    return texto


def armar(h1: dict[str, Any], digits: int, sesgo: str, nombre: str,
          est: Estadistica | None, ultima_vela: dict[str, float]) -> dict[str, Any]:
    alcista = sesgo == "Alcista"
    clave = "r1" if alcista else "s1"
    if h1.get("niveles_origen", {}).get(clave) != "swing":
        return {"hay_plan": False, "sesgo": sesgo,
                "motivo": "Hoy el activo no tiene una estructura de precio medible a favor de su "
                          "tendencia: sin ese nivel no hay plan que proponer."}
    gatillo = float(h1[clave])
    if alcista:
        invalidacion = ultima_vela["hh22"] - CHANDELIER_K * ultima_vela["atr22"]
    else:
        invalidacion = ultima_vela["ll22"] + CHANDELIER_K * ultima_vela["atr22"]
    recorrido = MULT_RECORRIDO * float(h1["atr_14"])
    lado, borde = ("sobre", "bajo") if alcista else ("bajo", "sobre")
    cierre = ultima_vela["close"]
    activado = cierre > gatillo if alcista else cierre < gatillo
    anulado = cierre < invalidacion if alcista else cierre > invalidacion
    estado = ("Invalidado: el último cierre quedó del otro lado de la invalidación." if anulado
              else "Activado: el último cierre de 1 hora ya está " + lado + " el gatillo." if activado
              else "Armado: el precio todavía no cruza el gatillo.")
    return {
        "hay_plan": True,
        "sesgo": sesgo,
        "gatillo": f"El escenario {sesgo.lower()} se activa con un cierre de vela de 1 hora {lado} {_fmt(gatillo, digits)}.",
        "invalidacion": f"El escenario se anula {borde} {_fmt(invalidacion, digits)} (salida por volatilidad, que se ajusta a favor a medida que el precio avanza).",
        "recorrido": f"Recorrido de referencia: 1,5 veces la volatilidad típica de una hora, unos {_fmt(recorrido, digits)}. Es una distancia, no un objetivo de precio.",
        "estadistica": _frase_estadistica(est, nombre),
        "estado": estado,
        "niveles": {"gatillo": gatillo, "invalidacion": round(invalidacion, digits)},
    }
```

Verificar contra los tests los números esperados de `_fmt` (4.020,00 / 4.003,00 / 12,00 / 3.997,00).

`preparar.py`:

```python
def _serie_h1(ticker: str):
    from market_data_mcp import mt5_client

    try:
        df = mt5_client.get_rates(ticker, "H1", 10000)
    except Exception as exc:  # noqa: BLE001
        raise PreparacionFallida(f"sin serie H1 de {ticker} para el plan ({exc})") from exc
    return df.iloc[:-1].reset_index(drop=True)   # solo velas cerradas
```

`Lectores` gana `serie_h1: Callable[[str], Any] = _serie_h1`. En `preparar_activo`, después de `op = ...`:

```python
    from analista import estadistica as est_mod
    from analista import plan as plan_mod

    df = lec.serie_h1(orden.args["ticker"])
    ind = est_mod._indicadores(df)
    ultima = {"close": float(df["close"].iat[-1]), "hh22": float(ind["hh"].iat[-1]),
              "ll22": float(ind["ll"].iat[-1]), "atr22": float(ind["atr22"].iat[-1])}
    alcista = payload["sesgo"] == "Alcista"
    estad = est_mod.medir(df, int(activo["digits"]), alcista) if len(df) > est_mod.VENTANA else None
    plan = plan_mod.armar(lectura["h1"], int(activo["digits"]), payload["sesgo"], activo["nombre"], estad, ultima)
```

y `"plan": plan` dentro de `datos`. Si `lectura` no trae `"h1"` (doble antiguo), `PreparacionFallida("la lectura del terminal no trae H1")`.

Exponer `_indicadores` como `indicadores` (sin guion bajo) en `estadistica.py` y usarlo así en ambos lados.

`informe_html.py`:

```python
def seccion_plan(plan: dict[str, Any]) -> str:
    if not plan.get("hay_plan"):
        return f'<div class="plan plan-vacio"><p>{e(plan.get("motivo", ""))}</p></div>'
    filas = [("Gatillo", plan["gatillo"]), ("Invalidación", plan["invalidacion"]),
             ("Recorrido", plan["recorrido"]), ("Qué dice la historia", plan["estadistica"]),
             ("Estado", plan["estado"])]
    cuerpo = "".join(f'<div class="plan-fila"><div class="plan-rotulo">{e(r)}</div><p>{e(t)}</p></div>'
                     for r, t in filas)
    return f'<div class="plan">{pildora(plan["sesgo"])}{cuerpo}</div>'
```

En `cuerpo_activo`, después de "Escenarios" y temporalidad, antes de "Qué NO hacer": `h2(4, "Plan de escenarios")`, `seccion_plan(d["plan"])`; la tabla de tasas pasa a número 5.

`informe.css`:

```css
.plan { border: 1px solid var(--papel-linea); border-radius: 8pt; padding: 12pt 14pt; margin: 8pt 0 12pt; }
.plan-fila { display: grid; grid-template-columns: 9.5em 1fr; gap: 10pt; padding: 6pt 0; border-top: 1px solid var(--papel-linea); }
.plan-fila:first-of-type { border-top: 0; }
.plan-rotulo { font-weight: 700; color: var(--tinta-2); font-size: 10.5pt; }
.plan-fila p { margin: 0; }
.plan-vacio p { color: var(--tinta-2); }
@media (max-width: 560px) { .plan-fila { grid-template-columns: 1fr; gap: 2pt; } }
```

`analista.md`, en "Activo": "`datos.plan` lo escribió el bot: no lo repitas. En `lectura` puedes nombrarlo en una frase ("el plan de escenarios marca el gatillo en…") con sus mismas cifras." Regenerar workflows.

- [ ] **Step 4: Correr** — `uv run pytest tests/test_analista_*.py -q && uv run python scripts/marca_tokens.py --check` → PASS

- [ ] **Step 5: Commit** — `git commit -m "feat(analista): plan de escenarios con gatillo, invalidación Chandelier y estadística"`

---

### Task 6: Bitácora de planes y desenlaces

**Files:**
- Create: `scripts/analista/bitacora.py`, `data/bitacora_planes_analistas.json` (con `[]`)
- Modify: `scripts/analista/bot.py`, `scripts/bot_analistas.py`
- Test: `tests/test_analista_bitacora.py`

**Interfaces:**
- Produces:
  - `bitacora.RUTA = RAIZ / "data" / "bitacora_planes_analistas.json"`
  - `bitacora.anotar(pieza: dict, html: Path, analista: str, ahora: datetime, ruta: Path = RUTA) -> bool` (False si la pieza no tiene plan)
  - `bitacora.completar(serie: Callable[[str], pd.DataFrame], ahora: datetime, ruta: Path = RUTA) -> int` (entradas completadas)

- [ ] **Step 1: Tests**

```python
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
from analista import bitacora as bt

SCL = ZoneInfo("America/Santiago")


def test_anota_una_entrada(tmp_path, pieza_con_plan):   # fixture: pieza de activo con datos.plan.hay_plan
    html = tmp_path / "x.html"; html.write_text("<html>", encoding="utf-8")
    ruta = tmp_path / "b.json"
    assert bt.anotar(pieza_con_plan, html, "director", datetime(2026, 10, 8, 11, tzinfo=SCL), ruta)
    [e] = json.loads(ruta.read_text(encoding="utf-8"))
    assert e["ticker"] == "XAGUSD" and e["desenlace"] is None and len(e["huella_html"]) == 64


def test_sin_plan_no_anota(tmp_path, pieza_sin_plan):
    assert not bt.anotar(pieza_sin_plan, tmp_path / "x.html", "d", datetime.now(SCL), tmp_path / "b.json")


def test_completar_solo_las_de_mas_de_24_h(tmp_path):
    # dos entradas: una de hace 30 h, otra de hace 2 h; serie sintética donde el precio
    # cruza el gatillo y recorre 1,5 ATR -> la primera queda "activado_recorrido", la otra sigue en None
```

(escribir el tercer test completo con `serie` del Task 4 y entradas armadas a mano: `{"creada": iso, "ticker": "T", "alcista": True, "gatillo": 100.5, "invalidacion": 97.0, "desenlace": None}`).

- [ ] **Step 2: Ver fallar**

- [ ] **Step 3: Implementar**

```python
"""Bitácora de los planes entregados: rastro ante un reclamo y base de un historial honesto.

Se versiona, igual que `historial_despachos.json`: es historia de lo que se
entregó, no estado generado.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from analista import RAIZ

RUTA = RAIZ / "data" / "bitacora_planes_analistas.json"


def _leer(ruta: Path) -> list[dict[str, Any]]:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def _escribir(ruta: Path, entradas: list[dict[str, Any]]) -> None:
    tmp = ruta.with_suffix(".tmp")
    tmp.write_text(json.dumps(entradas, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(ruta)


def anotar(pieza: dict[str, Any], html: Path, analista: str, ahora: datetime, ruta: Path = RUTA) -> bool:
    plan = pieza["datos"].get("plan") or {}
    if not plan.get("hay_plan"):
        return False
    entradas = _leer(ruta)
    entradas.append({
        "creada": ahora.isoformat(), "ticker": pieza["datos"]["ticker"],
        "alcista": plan["sesgo"] == "Alcista",
        "gatillo": plan["niveles"]["gatillo"], "invalidacion": plan["niveles"]["invalidacion"],
        "estadistica": plan["estadistica"], "analista": analista,
        "huella_html": hashlib.sha256(html.read_bytes()).hexdigest(), "desenlace": None,
    })
    _escribir(ruta, entradas)
    return True


def _evaluar(e: dict[str, Any], df) -> str:
    """Desde la vela posterior a la entrega: ¿cruzó el gatillo?, y si cruzó, ¿qué tocó primero?"""
    from analista.estadistica import desenlace, indicadores

    desde = datetime.fromisoformat(e["creada"]).replace(tzinfo=None)
    tiempos = df["time"].astype("datetime64[ns]")
    posteriores = df.index[tiempos > desde]
    ind = indicadores(df)
    for i in posteriores[:24]:
        c = float(df["close"].iat[i])
        if (c > e["gatillo"]) if e["alcista"] else (c < e["gatillo"]):
            return "activado_" + desenlace(df, int(i), e["alcista"], ind)
    return "no_se_activo"


def completar(serie: Callable[[str], Any], ahora: datetime, ruta: Path = RUTA) -> int:
    entradas, n = _leer(ruta), 0
    for e in entradas:
        if e["desenlace"] is None and ahora - datetime.fromisoformat(e["creada"]) > timedelta(hours=24):
            e["desenlace"] = _evaluar(e, serie(e["ticker"]))
            n += 1
    if n:
        _escribir(ruta, entradas)
    return n
```

Ojo de zona horaria (CLAUDE.md, *Series OHLC en hora de Santiago*): las marcas de `get_rates` vienen en hora del servidor. Comparar `creada` convertida a la misma referencia: usar el offset medido como en `tools/symbol_spec.py` (`server_naive`) o, más simple y suficiente, comparar contra el `time` de la última vela cerrada al momento de anotar (guardar `"vela_entrega": str(df.time.iat[-1])` en `anotar` vía `pieza["datos"]["plan"]["vela"]`, que `preparar_activo` agrega como `str(df["time"].iat[-1])`). **Usar esta segunda vía**: `_evaluar` busca `tiempos > vela_entrega`. Ajustar el test y `plan.armar` (recibe `vela: str` dentro de `ultima_vela`, lo devuelve en `niveles["vela"]`).

`bot.py` (`atender`): tras `ih.guardar`, si `o.pieza == "activo"` y la pieza no es reusada, `bitacora.anotar(pieza, ruta, pedido.usuario, ahora)`. Una reusada no se re-anota (es el mismo plan).

`bot_analistas.py`: flag `--desenlaces` → `bitacora.completar(pr._serie_h1, datetime.now(SANTIAGO))` e imprime cuántas completó.

- [ ] **Step 4: Correr** — `uv run pytest tests/test_analista_*.py -q` → PASS

- [ ] **Step 5: Commit** — `git add data/bitacora_planes_analistas.json ...` y `git commit -m "feat(analista): bitácora versionada de planes con su desenlace"`

---

### Task 7: Documentación, suite completa y prueba real

**Files:**
- Modify: `docs/bot-analistas.md`, memoria `project_bot_analistas_telegram.md` (fuera del repo)

- [ ] **Step 1:** `docs/bot-analistas.md`: secciones "Firma y acreditación" (dónde está el bloque `autor`, que la vigencia se decide por la fecha del pedido, `config/autor/` fuera de git), "Plan de escenarios" (qué es cada fila, por qué siempre contra la línea base, por qué sin objetivo fijo) y "Bitácora" (`--desenlaces`).

- [ ] **Step 2: Suite y gates**

```bash
uv run pytest -q
uv run python scripts/marca_tokens.py --check
uv run python scripts/agy_workflows.py --check
```

Expected: todo verde.

- [ ] **Step 3: E2E real** (desde Git Bash, con MT5 abierto en la cuenta 51257):

```bash
MSYS_NO_PATHCONV=1 uv run --with MetaTrader5 --extra stories --extra informe python scripts/bot_analistas.py --una "/activo oro" --usuario director
MSYS_NO_PATHCONV=1 uv run --with MetaTrader5 --extra stories --extra informe python scripts/bot_analistas.py --una "/activo usdclp" --usuario director
MSYS_NO_PATHCONV=1 uv run python scripts/bot_analistas.py --una "/activo oro para Juan" --usuario director
```

Abrir los dos HTML en Chrome (Playwright, 100 % y ancho de teléfono): franja con "Análisis" y "Compartido por", firma con foto y credencial con link, plan con sus cinco filas y las dos cifras, cifras del plan con los `digits` del activo, sin "CMF", sin "Preparado para", acentos `¿ ¡ ·` bien. El tercer pedido responde el mensaje de personalización retirada. Revisar que `data/bitacora_planes_analistas.json` tenga dos entradas.

- [ ] **Step 4: Commit** — `git commit -m "docs(analista): firma, plan de escenarios y bitácora"`
