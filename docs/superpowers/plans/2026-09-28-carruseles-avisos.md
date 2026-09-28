# Carruseles de Avisos: plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tres carruseles al día en el grupo de Avisos (`01_macro_y_apertura`) que ponen lado a lado la voz de un banco y los datos del terminal, preparados por el reloj, escritos por `/avisos` y despachados por el único camino que ya llega al cliente.

**Architecture:** Un script nuevo, `scripts/pipeline_avisos.py`, arma la tanda con el formato de carpeta que el despacho ya recorre (`data/carrusel/<tanda>/01_macro_y_apertura/N_<lamina>.{json,png,_mensaje.txt}` más `_avisos.json`). Los frenos se comparten con LinkedIn a través de tres funciones públicas nuevas de `pipeline_linkedin`. El despacho (`pipeline_carrusel.despachar`) se extiende: el refresco de una tanda de Avisos lo delega en `pipeline_avisos`, con una sola lectura del terminal, y el cupo y la divergencia se juzgan por canal. El reloj gana tres momentos con `pieza: "avisos"`.

**Tech Stack:** Python 3.12 con `uv`, pytest, Playwright (extra `stories`) para rendir, MetaTrader5 (se pasa con `--with MetaTrader5`), plantillas HTML/CSS de `templates/stories/` rendidas con `scripts/story_render.py`.

**Spec:** `docs/superpowers/specs/2026-09-28-carruseles-avisos-design.md`

El trabajo va en **dos hitos, dos PR** (spec §9). El Hito 1 no toca ningún camino hacia el cliente: produce tandas y PNG en disco. El Hito 2 conecta despacho, reloj y comando. No se empieza el Hito 2 sin el Hito 1 mergeado.

## Global Constraints

- Rama: `feat/pieza-avisos-vision`, que parte de `feat/linkedin-pipeline` (PR #241 se mergea primero). Nunca commitear a `master`.
- CERO HARDCODING DE PRECIOS: toda cifra de precio sale del terminal (MT5) en tiempo de ejecución; en los tests se usan valores de fixture, nunca en scripts ni plantillas.
- Texto de cliente escrito con `Path.write_text(..., encoding="utf-8")` o con la herramienta de edición, **nunca** por PowerShell ni por tuberías.
- Sin guion largo `—` ni medio `–` en texto de cliente. El punto medio `·` sí.
- Tuteo chileno, sin voseo.
- Colores de plantilla solo por `var(--rol)` de `marca.css`; `uv run python scripts/marca_tokens.py --check` debe pasar.
- Láminas en horizontal 1920×1080.
- Frescura de los datos al rendir y al despachar: **2 horas** (`FRESCURA_MAX_HORAS = 2`).
- Visión: menos de 45 días (`pl.ANTIGUEDAD_MAX_DIAS`), no repetida en Avisos antes de 14 días.
- Cobertura: el activo menos cubierto en Avisos en 7 días.
- Máximo 9 láminas por carrusel (el orden lo da `sorted(glob("*.png"))`, que ordena como texto).
- Aviso legal literal: `Análisis informativo. No constituye recomendación de inversión.`
- El reloj nunca envía: `test_el_reloj_no_puede_enviar_nada_a_whatsapp` sigue verde.
- Nada sale al grupo sin aprobación explícita del director. La prueba real termina en `--dry-run`.
- No subir `max_envios_dia` (40) ni la cadencia (45 s); no meter el envío en un bucle ni en paralelo.
- Commits terminan con `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`; el cuerpo del PR termina con `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

## Review Focus

1. **Dos `--preparar` del mismo momento el mismo día** (el director pide uno fuera de hora cuando el reloj ya lo hizo): se espera que el segundo no escriba nada ni gaste historial, y que diga dónde está la tanda existente. Test: `test_preparar_dos_veces_el_mismo_momento_no_duplica` (Tarea 8).
2. **Una visión de meta cuya cifra no aparece en su propia cita** (registro cargado a mano con un error de tipeo): no califica, así la lámina nunca muestra una meta sin respaldo. Test: `test_meta_que_no_figura_en_la_cita_no_califica` (Tarea 3).
3. **El balance cuando la mañana no tuvo tanda** (MT5 caído a las 10:30): cae al mediodía y, si tampoco, elige fresco y sale sin voz. Tests: `test_balance_cae_a_mediodia` y `test_balance_sin_manana_ni_mediodia_sale_sin_voz` (Tarea 3).
4. **Un `_avisos.json` editado a mano que pierde la zona horaria** (`2026-09-29T11:30`): la frescura se juzga en hora de Santiago y no lanza `TypeError`. Test: `test_validar_frescura_acepta_hora_sin_zona` (Tarea 1).
5. **El cobre, con `digits = 0`**: el precio de la portada y el de la alerta se escriben igual (entero, sin separador), o el cliente ve dos cifras distintas para el mismo precio. Test: `test_portada_del_cobre_escribe_el_precio_como_la_alerta` (Tarea 6).

---

## Estructura de archivos

| Archivo | Responsabilidad | Hito |
|---|---|---|
| `scripts/pipeline_linkedin.py` | `validar_textos`, `validar_cifras`, `validar_frescura` públicas; `validar` las compone | 1 |
| `scripts/pipeline_avisos.py` | Nuevo. Calendario del día, elección, armado de láminas, frenos, render, refresco, CLI | 1 (+ `refrescar_para_despacho` en 2) |
| `templates/stories/vision.html` | Nueva. Variantes `cita` y `meta` por `FOR` | 1 |
| `templates/stories/avisos_portada.html`, `avisos_lectura.html` | Ya existen (creadas el 2026-09-28 para la tanda manual). Se alinean al contrato | 1 |
| `tests/fixtures/stories/payloads/vision.json` (+ ajustes de los otros dos) | Fixtures | 1 |
| `data/visiones_expertos.json` | `horizonte` y `meta` en la visión de meta | 1 |
| `tests/test_pipeline_avisos.py` | Nuevo | 1 y 2 |
| `tests/test_pipeline_linkedin.py`, `tests/test_story_render.py` | Casos nuevos | 1 |
| `src/whatsapp_sender.py` | `cupo_restante()` | 2 |
| `scripts/pipeline_carrusel.py` | `CanalDetenidoError`, delegación de tandas de Avisos, cupo por canal | 2 |
| `config/agenda_mercado.json`, `scripts/reloj_gi.py` | Tres momentos, `PIEZAS`, canal por alias | 2 |
| `.claude/commands/avisos.md`, `scripts/agy_workflows.py`, `CLAUDE.md` (+ regenerados) | Comando y documentación | 2 |

**Contrato de láminas** (fijado acá, lo usan todas las tareas):

| Clave | `_plantilla` | Archivo de plantilla | Nombre en el pie |
|---|---|---|---|
| `portada` | `avisos_portada` | `avisos_portada.html` | Portada |
| `voz` | `vision` | `vision.html` | La voz del banco |
| `datos` | `avisos_datos` | `alerta.html` | Nuestros datos |
| `semana` | `avisos_agenda` | `calendario.html` | La semana |
| `lectura` | `avisos_lectura` | `avisos_lectura.html` | Nuestra lectura |

Secuencias: `cita`, `meta` y `balance` → `portada · voz · datos · lectura`; `agenda` → `portada · semana · lectura`. Sin visión se quita `voz` y se renumera.

**Desvío deliberado del spec, a revisar:** la lámina 3 declara `_plantilla: "avisos_datos"` y no `"alerta"`. Motivo verificado en `_refrescar_y_rendir` (`scripts/pipeline_carrusel.py:1355`): el camino de la alerta temática reescribe `<stem>_mensaje.txt` con `construir_mensaje_alerta`, lo que borraría el pie de posición (*"3/4 · Nuestros datos"*) que el spec exige en toda lámina. Con un nombre propio, el camino temático queda intacto y la lámina se rinde igual con `alerta.html`.

**Todo payload de Avisos lleva `titular` y `parrafo`**, aunque su plantilla los llame distinto (`bajada`, `titulo`, `conclusion`, `subtitulo`, `remate`). Motivo verificado: `pc.exigir_texto_editorial` y `validador_editorial.validar_payload_editorial` exigen esos dos campos en toda pieza numerada, y el spec pide que sigan corriendo en las dos rutas. `tokens_de` (Tarea 7) hace la traducción al rendir.

---

# HITO 1: frenos, láminas y `pipeline_avisos` (sin camino al cliente)

### Task 1: Frenos compartidos en `pipeline_linkedin`

**Files:**
- Modify: `scripts/pipeline_linkedin.py:404-524` (`_a_float` a `validar`)
- Test: `tests/test_pipeline_linkedin.py`

**Interfaces:**
- Consumes: `validador_editorial.validar_texto(texto, campo=...)`, `formatear`, `_PRECIO`, `_NUMERO`, `CERCANIA_PRECIO`, `CAMPOS_PRECIO`, `MARCA_EDITORIAL`, `SANTIAGO`.
- Produces:
  - `validar_textos(textos: list[tuple[str, str]]) -> list[str]`
  - `validar_cifras(textos: list[tuple[str, str]], activos: dict[str, dict], visiones: list[dict], cifras_citadas: dict[str, str], campos: tuple[str, ...] = CAMPOS_PRECIO) -> list[str]`
  - `validar_frescura(leido: datetime, ahora: datetime, max_horas: float, remedio: str = "Vuelve a correr --preparar.") -> list[str]`

- [ ] **Step 1: Write the failing tests** (al final de `tests/test_pipeline_linkedin.py`)

```python
# ─────────────────────────────────────────────────────────────────────────────
# Frenos públicos (los comparte pipeline_avisos)
# ─────────────────────────────────────────────────────────────────────────────
ACTIVOS_FRENO = {"USDCLP": {"nombre": "Dólar", "digits": 2, "price": 936.32, "s1": 930.0, "r1": 942.5}}


def test_validar_textos_marca_vacio_y_guion():
    err = pl.validar_textos([("a", "[[ESCRIBIR]]"), ("b", "  "), ("c", "El dólar sube — fuerte")])
    assert "a: sin escribir" in err
    assert "b: sin escribir" in err
    assert any(e.startswith("c: guion largo") for e in err)


def test_validar_textos_texto_sano_pasa():
    assert pl.validar_textos([("a", "El dólar mantiene su sesgo alcista sobre su promedio de 50 horas.")]) == []


def test_validar_cifras_con_moneda_sin_respaldo():
    err = pl.validar_cifras([("t", "El dólar va a $951,00 hoy.")], ACTIVOS_FRENO, [], {})
    assert any("$951,00" in e for e in err)


def test_validar_cifras_medidas_pasan():
    texto = "El soporte está en $930,00 y el precio en $936,32."
    assert pl.validar_cifras([("t", texto)], ACTIVOS_FRENO, [], {}) == []


def test_validar_cifras_parecida_no_medida():
    err = pl.validar_cifras([("t", "Cotiza cerca de 935,10.")], ACTIVOS_FRENO, [], {})
    assert any("935,10" in e for e in err)


def test_validar_cifras_acepta_campos_extra():
    activos = {"USDCLP": {**ACTIVOS_FRENO["USDCLP"], "soporte_publicado": 928.4}}
    campos = pl.CAMPOS_PRECIO + ("soporte_publicado",)
    assert pl.validar_cifras([("t", "Soporte en $928,40.")], activos, [], {}, campos=campos) == []


def test_validar_cifras_vision_y_citadas():
    vision = {"cita": "El dólar llegaría a $970."}
    assert pl.validar_cifras([("t", "El banco ve $970 al cierre.")], ACTIVOS_FRENO, [vision], {}) == []
    citadas = {"$955": "máximo de ayer"}
    assert pl.validar_cifras([("t", "Ayer tocó $955.")], ACTIVOS_FRENO, [], citadas) == []


def test_validar_frescura_en_el_borde():
    ahora = datetime(2026, 9, 29, 12, 0, tzinfo=pl.SANTIAGO)
    assert pl.validar_frescura(ahora - timedelta(minutes=119), ahora, 2) == []
    err = pl.validar_frescura(ahora - timedelta(minutes=121), ahora, 2, remedio="Corre --refrescar.")
    assert err and "se leyeron hace 121 min" in err[0] and "Corre --refrescar." in err[0]


def test_validar_frescura_acepta_hora_sin_zona():
    ahora = datetime(2026, 9, 29, 12, 0, tzinfo=pl.SANTIAGO)
    assert pl.validar_frescura(datetime(2026, 9, 29, 11, 30), ahora, 2) == []
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_pipeline_linkedin.py -k "validar_textos or validar_cifras or validar_frescura" -v`
Expected: FAIL con `AttributeError: module 'pipeline_linkedin' has no attribute 'validar_textos'`.

- [ ] **Step 3: Implement.** Reemplazar en `scripts/pipeline_linkedin.py` desde `def cifras_parecidas_no_medidas` hasta el final de `def validar` por:

```python
def _referencias(activos: dict[str, dict[str, Any]], campos: tuple[str, ...]) -> list[float]:
    return [
        float(fila[c])
        for fila in activos.values()
        for c in campos
        if fila.get(c) not in (None, 0)
    ]


def _parecidas(texto: str, referencias: list[float], permitidas: set[str]) -> list[str]:
    """Cifras sin `$` que se parecen a un precio medido pero no son ese precio.

    `_PRECIO` solo ve lo que lleva `$`, y un nivel de índice nunca lo lleva
    (30.379,37), ni un "USD 971". Exigir que toda cifra del texto calce fallaría
    con "50 días" o "0,24 puntos". Así que se busca el caso que de verdad se
    escapa: una cifra a menos de `CERCANIA_PRECIO` de un precio del terminal que
    no coincide con ninguno. Es la cifra de ayer copiada, o un nivel redondeado.
    """
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


def _permitidas(activos: dict[str, dict[str, Any]], visiones: list[dict[str, Any]],
                cifras_citadas: dict[str, str], campos: tuple[str, ...]) -> set[str]:
    permitidas: set[str] = set()
    for fila in activos.values():
        for campo in campos:
            if fila.get(campo) is not None:
                permitidas.add(formatear(fila[campo], fila["digits"]))
    for vision in visiones:
        permitidas.update(_PRECIO.findall(str(vision.get("cita", ""))))
    for cifra in cifras_citadas:
        permitidas.update(_PRECIO.findall(cifra) or [cifra.strip()])
    return permitidas


def cifras_parecidas_no_medidas(texto: str, payload: dict[str, Any], permitidas: set[str]) -> list[str]:
    """Compatibilidad: la versión que recibe el payload de LinkedIn."""
    return _parecidas(texto, _referencias(payload["datos"]["activos"], CAMPOS_PRECIO), permitidas)


def cifras_permitidas(payload: dict[str, Any], visiones: list[dict[str, Any]]) -> set[str]:
    """Compatibilidad: la versión que recibe el payload de LinkedIn."""
    return _permitidas(payload["datos"]["activos"], visiones,
                       payload["editorial"].get("cifras_citadas", {}), CAMPOS_PRECIO)


def _textos(editorial: dict[str, Any]) -> list[tuple[str, str]]:
    """Todo texto de cliente del payload, con su ubicación para el mensaje de error."""
    salida: list[tuple[str, str]] = []
    for pagina, campos in editorial.get("paginas", {}).items():
        for campo, valor in campos.items():
            if campo != "vision":
                salida.append((f"{pagina}.{campo}", str(valor)))
    for fecha, valor in editorial.get("remates_dia", {}).items():
        salida.append((f"remate {fecha}", str(valor)))
    salida.append(("copy", str(editorial.get("copy", ""))))
    salida.append(("hashtags", str(editorial.get("hashtags", ""))))
    return salida


def validar_textos(textos: list[tuple[str, str]]) -> list[str]:
    """Huecos sin escribir, guion largo o medio, voseo y marcadores temporales.

    Freno genérico: recibe pares `(donde, texto)` y no sabe de qué estructura
    salieron. Lo comparten LinkedIn y los carruseles de Avisos.
    """
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


def validar_cifras(
    textos: list[tuple[str, str]],
    activos: dict[str, dict[str, Any]],
    visiones: list[dict[str, Any]],
    cifras_citadas: dict[str, str],
    campos: tuple[str, ...] = CAMPOS_PRECIO,
) -> list[str]:
    """Cifras con `$` sin respaldo y cifras parecidas a un precio que no son ninguno.

    `activos` son filas medidas `{ticker: {digits, <campo>: valor}}`; `campos`
    dice cuáles de sus valores cuentan como precio publicable.
    """
    permitidas = _permitidas(activos, visiones, cifras_citadas, campos)
    referencias = _referencias(activos, campos)
    errores: list[str] = []
    for donde, texto in textos:
        con_moneda = _PRECIO.findall(texto)
        for cifra in con_moneda:
            if cifra not in permitidas:
                errores.append(
                    f"{donde}: la cifra ${cifra} no sale del terminal ni de una cita registrada. "
                    "Usa la medida o declárala en `cifras_citadas` con su motivo."
                )
        for cifra in _parecidas(texto, referencias, permitidas):
            if cifra not in con_moneda:
                errores.append(
                    f"{donde}: {cifra} se parece a un precio medido pero no es ninguno. "
                    "Usa la cifra exacta del terminal o declárala en `cifras_citadas`."
                )
    return errores


def validar_frescura(leido: datetime, ahora: datetime, max_horas: float,
                     remedio: str = "Vuelve a correr --preparar.") -> list[str]:
    """Datos vencidos. Una hora sin zona se lee en Santiago, como `leido_en`."""
    leido = leido if leido.tzinfo else leido.replace(tzinfo=SANTIAGO)
    minutos = (ahora - leido).total_seconds() / 60
    if minutos > max_horas * 60:
        return [f"los datos se leyeron hace {minutos:.0f} min (máximo {max_horas:g} h). {remedio}"]
    return []


def validar(payload: dict[str, Any], registro: dict[str, dict[str, Any]], ahora: datetime,
            aceptar_datos_viejos: bool = False) -> list[str]:
    """Todos los motivos por los que el brief no puede salir. Vacío = puede salir.

    Junta todos los errores en vez de cortar al primero: el comando corrige de una
    vez en vez de ir descubriendo los huecos uno por uno. Compone los tres frenos
    públicos, que son los mismos que usa `pipeline_avisos`.
    """
    editorial = payload["editorial"]
    textos = _textos(editorial)
    errores = validar_textos(textos)

    usadas: list[dict[str, Any]] = []
    aceptadas = editorial.get("aceptar_antiguas", {})
    hoy = ahora.date()
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
        errores.extend(validar_vision(registro[vid], hoy, aceptadas.get(vid)))

    errores.extend(validar_cifras(textos, payload["datos"]["activos"], usadas,
                                  editorial.get("cifras_citadas", {})))
    if not aceptar_datos_viejos:
        errores.extend(validar_frescura(leido_en(payload), ahora, FRESCURA_MAX_HORAS))
    return errores
```

- [ ] **Step 4: Run the whole LinkedIn suite**

Run: `uv run pytest tests/test_pipeline_linkedin.py -v`
Expected: PASS, incluidos los tests que ya existían (su comportamiento no cambia).

- [ ] **Step 5: Commit**

```bash
git add scripts/pipeline_linkedin.py tests/test_pipeline_linkedin.py
git commit -m "refactor(linkedin): frenos de textos, cifras y frescura como funciones públicas"
```

---

### Task 2: Esqueleto de `pipeline_avisos`: días hábiles, formatos y láminas

**Files:**
- Create: `scripts/pipeline_avisos.py`
- Test: `tests/test_pipeline_avisos.py`

**Interfaces:**
- Consumes: `pipeline_carrusel.CANAL_AVISOS`, `pipeline_carrusel.DIR_TRABAJO`, `pipeline_linkedin.MARCA_EDITORIAL`, `market_data_mcp.tools.symbol_spec._cargar_feriados()`.
- Produces: constantes `CANAL`, `MOMENTOS`, `LAMINAS`, `SECUENCIAS`, `PLANTILLAS`, `MAX_LAMINAS`, `FRESCURA_MAX_HORAS`, `AVISO_LEGAL`, `FIRMA`; `es_dia_habil(fecha: date) -> bool`; `formato_del_momento(momento: str, fecha: date) -> str`; `laminas_de(formato: str, con_voz: bool) -> list[dict[str, str]]` con claves `clave`, `stem`, `plantilla`, `posicion`; `etiqueta_hora(ahora: datetime) -> str`; `fecha_hora(ahora: datetime) -> str`.

- [ ] **Step 1: Write the failing tests** (`tests/test_pipeline_avisos.py`)

```python
"""Carruseles de Avisos (spec 2026-09-28-carruseles-avisos-design.md)."""
from __future__ import annotations

import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
for p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import pipeline_avisos as pa  # noqa: E402

LUNES = date(2026, 9, 28)
MARTES = date(2026, 9, 29)


def test_feriado_nyse_no_es_habil():
    assert pa.es_dia_habil(date(2026, 11, 26)) is False  # Acción de Gracias


def test_sabado_no_es_habil_y_martes_si():
    assert pa.es_dia_habil(date(2026, 10, 3)) is False
    assert pa.es_dia_habil(MARTES) is True


def test_la_tarde_es_agenda_el_lunes_y_balance_el_resto():
    assert pa.formato_del_momento("avisos_tarde", LUNES) == "agenda"
    assert pa.formato_del_momento("avisos_tarde", MARTES) == "balance"
    assert pa.formato_del_momento("avisos_manana", MARTES) == "cita"
    assert pa.formato_del_momento("avisos_mediodia", MARTES) == "meta"


def test_momento_desconocido_se_detiene_nombrando_las_opciones():
    with pytest.raises(SystemExit, match="avisos_manana"):
        pa.formato_del_momento("avisos_noche", MARTES)


def test_laminas_con_voz_numeran_sobre_cuatro():
    laminas = pa.laminas_de("cita", con_voz=True)
    assert [l["stem"] for l in laminas] == ["1_portada", "2_voz", "3_datos", "4_lectura"]
    assert laminas[1]["posicion"] == "2/4 · La voz del banco"
    assert laminas[2]["plantilla"] == "avisos_datos"


def test_laminas_sin_voz_renumeran_sobre_tres():
    laminas = pa.laminas_de("meta", con_voz=False)
    assert [l["stem"] for l in laminas] == ["1_portada", "2_datos", "3_lectura"]
    assert laminas[2]["posicion"] == "3/3 · Nuestra lectura"


def test_la_agenda_no_lleva_voz_ni_alerta():
    assert [l["clave"] for l in pa.laminas_de("agenda", con_voz=True)] == ["portada", "semana", "lectura"]


def test_toda_plantilla_de_lamina_existe_en_disco():
    for plantilla, archivo in pa.PLANTILLAS.items():
        assert (pa.DIR_PLANTILLAS / archivo).exists(), f"{plantilla}: falta {archivo}"


def test_ninguna_secuencia_pasa_del_tope():
    assert all(len(s) <= pa.MAX_LAMINAS for s in pa.SECUENCIAS.values())


def test_etiqueta_hora_nombra_el_horario_chileno():
    verano = datetime(2026, 9, 29, 11, 30, tzinfo=pa.SANTIAGO)
    invierno = datetime(2026, 7, 1, 11, 30, tzinfo=pa.SANTIAGO)
    assert pa.etiqueta_hora(verano) == "11:30 CLST"
    assert pa.etiqueta_hora(invierno) == "11:30 CLT"
    assert pa.fecha_hora(verano) == "MARTES 29 SEP · 11:30 CLST"
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_pipeline_avisos.py -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'pipeline_avisos'`.

- [ ] **Step 3: Implement** `scripts/pipeline_avisos.py`

```python
"""Carruseles de Avisos: la voz de los bancos contra nuestros datos, tres veces al día.

Spec: docs/superpowers/specs/2026-09-28-carruseles-avisos-design.md

El reparto es el mismo de `pipeline_carrusel`: el script prepara los datos y
deja los huecos en `[[ESCRIBIR]]`; el texto lo escribe el comando `/avisos`, y
`--rendir` se detiene ante un hueco, una cifra sin respaldo, una cita vieja o
datos de más de 2 horas.

La tanda se escribe con la carpeta que el despacho ya recorre
(`data/carrusel/<tanda>/01_macro_y_apertura/N_<lamina>.*`), así el único camino
al cliente sigue siendo `pipeline_carrusel.py --despachar`.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable
from zoneinfo import ZoneInfo

RAIZ = Path(__file__).resolve().parent.parent
for _p in (str(RAIZ / "src"), str(RAIZ / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import pipeline_carrusel as pc  # noqa: E402
import pipeline_linkedin as pl  # noqa: E402

SANTIAGO = ZoneInfo("America/Santiago")
CANAL = pc.CANAL_AVISOS
MARCA = pl.MARCA_EDITORIAL
DIR_PLANTILLAS = RAIZ / "templates" / "stories"

FRESCURA_MAX_HORAS = 2
VENTANA_VISION_DIAS = 14
VENTANA_COBERTURA_DIAS = 7
MAX_LAMINAS = 9
AVISO_LEGAL = "Análisis informativo. No constituye recomendación de inversión."
FIRMA = "Grupo Inteligencia · Equipo de análisis"

# Momento del reloj -> formato. "tarde" se resuelve por día de la semana.
MOMENTOS = {"avisos_manana": "cita", "avisos_mediodia": "meta", "avisos_tarde": "tarde"}

# clave -> (_plantilla, nombre que ve el cliente en el pie de posición)
LAMINAS = {
    "portada": ("avisos_portada", "Portada"),
    "voz": ("vision", "La voz del banco"),
    "datos": ("avisos_datos", "Nuestros datos"),
    "semana": ("avisos_agenda", "La semana"),
    "lectura": ("avisos_lectura", "Nuestra lectura"),
}

SECUENCIAS = {
    "cita": ("portada", "voz", "datos", "lectura"),
    "meta": ("portada", "voz", "datos", "lectura"),
    "balance": ("portada", "voz", "datos", "lectura"),
    "agenda": ("portada", "semana", "lectura"),
}

# _plantilla -> archivo en templates/stories/. La lámina de datos se llama
# `avisos_datos` y no `alerta`: el refresco temático reescribe el mensaje con
# `construir_mensaje_alerta` y borraría el pie de posición.
PLANTILLAS = {
    "avisos_portada": "avisos_portada.html",
    "vision": "vision.html",
    "avisos_datos": "alerta.html",
    "avisos_agenda": "calendario.html",
    "avisos_lectura": "avisos_lectura.html",
}

_DIAS = ("LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO")
_MESES = ("ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC")


# ---------------------------------------------------------------- calendario


def es_dia_habil(fecha: date) -> bool:
    """Lunes a viernes y hábil en la bolsa de Nueva York (el calendario del escáner)."""
    from market_data_mcp.tools.symbol_spec import _cargar_feriados

    if fecha.weekday() >= 5:
        return False
    return fecha.isoformat() not in _cargar_feriados().get("NYSE", [])


def formato_del_momento(momento: str, fecha: date) -> str:
    if momento not in MOMENTOS:
        raise SystemExit(f"Momento desconocido: {momento}. Opciones: {', '.join(MOMENTOS)}")
    formato = MOMENTOS[momento]
    if formato == "tarde":
        return "agenda" if fecha.weekday() == 0 else "balance"
    return formato


def laminas_de(formato: str, con_voz: bool) -> list[dict[str, str]]:
    """Las láminas del carrusel en orden, con su archivo y su pie de posición.

    El pie es obligatorio en toda lámina: si un envío se corta y se retoma, las
    que faltan pueden llegar separadas de las primeras y el pie le conserva el
    orden al lector.
    """
    claves = [c for c in SECUENCIAS[formato] if con_voz or c != "voz"]
    if len(claves) > MAX_LAMINAS:
        raise ValueError(
            f"{len(claves)} láminas: el despacho ordena como texto y desde 10 la `10_` "
            f"saldría antes que la `2_`. Máximo {MAX_LAMINAS}."
        )
    total = len(claves)
    return [
        {
            "clave": c,
            "stem": f"{i}_{c}",
            "plantilla": LAMINAS[c][0],
            "posicion": f"{i}/{total} · {LAMINAS[c][1]}",
        }
        for i, c in enumerate(claves, 1)
    ]


def etiqueta_hora(ahora: datetime) -> str:
    """HH:MM con CLT o CLST, del horario que de verdad rige ese instante."""
    local = ahora.astimezone(SANTIAGO)
    return f"{local:%H:%M} {'CLST' if local.dst() else 'CLT'}"


def fecha_hora(ahora: datetime) -> str:
    local = ahora.astimezone(SANTIAGO)
    return f"{_DIAS[local.weekday()]} {local.day} {_MESES[local.month - 1]} · {etiqueta_hora(local)}"
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_pipeline_avisos.py -v`
Expected: PASS. (`test_toda_plantilla_de_lamina_existe_en_disco` falla hasta la Tarea 4 porque `vision.html` no existe: márcalo con `@pytest.mark.xfail(strict=True, reason="vision.html llega en la Tarea 4")` y quita la marca en la Tarea 4.)

- [ ] **Step 5: Commit**

```bash
git add scripts/pipeline_avisos.py tests/test_pipeline_avisos.py
git commit -m "feat(avisos): días hábiles, formatos por momento y láminas numeradas"
```

---

### Task 3: Elección del activo y de la visión, historial y registro

**Files:**
- Modify: `scripts/pipeline_avisos.py` (append)
- Modify: `data/visiones_expertos.json` (visión `jpm-oro-6000-4t26`)
- Test: `tests/test_pipeline_avisos.py`

**Interfaces:**
- Consumes: `pl.validar_vision(vision, hoy, motivo)`, `pl._PRECIO`, `screener_gi.gate_feriado(ticker, fecha)`, `screener_gi.cobertura_fija()`, `pipeline_informe.ACTIVOS_INFORME`, `suplemento_canal.HISTORIAL`, `suplemento_canal.cargar_historial(ruta)`.
- Produces:
  - `variante_de(vision: dict) -> str` (`"meta"` o `"cita"`)
  - `vision_califica(vision: dict, variante: str, hoy: date, historial: list[dict]) -> bool`
  - `coberturas(historial, hoy, dias) -> dict[str, int]`, `cubiertos_hoy(historial, hoy) -> set[str]`
  - `candidatos(hoy, historial, universo: list[str] | None = None) -> list[str]`
  - `elegir(variante, hoy, visiones: dict[str, dict], historial, universo=None) -> tuple[str, str | None]`
  - `activo_del_balance(historial, hoy) -> tuple[str | None, str | None]`
  - `registrar_uso(hoy, momento, activo, vision_id, gastar_vision: bool, ruta: Path | None = None) -> None`
  - Excepción `SinCandidatosError(RuntimeError)`

Formato del historial (`data/historial_suplementos.json`, lista compartida con el suplemento): `{"fecha", "canal", "tipo": "vision", "clave": <id>}` y `{"fecha", "canal", "tipo": "avisos", "clave": <ticker>, "momento", "vision": <id|null>}`. Se usa `clave` como las entradas existentes; el campo `vision` en la entrada `avisos` es lo que permite que el balance retome la visión de la mañana (el spec no lo nombra; es necesario para §3.4).

- [ ] **Step 1: Write the failing tests**

```python
def vision(id_, activo="USDCLP", tipo="textual", cita="El dólar se mueve por datos.", fecha="2026-09-20", **extra):
    return {"id": id_, "quien": "Ana Pérez", "institucion": "Banco X", "activo": activo, "tipo": tipo,
            "cita": cita, "fecha": fecha, "fuente": "Diario", "url": "https://ejemplo.cl/nota", **extra}


def uso(fecha, activo, momento="avisos_manana", vid=None):
    return {"fecha": fecha, "canal": pa.CANAL, "tipo": "avisos", "clave": activo, "momento": momento, "vision": vid}


UNIVERSO = ["USDCLP", "XAUUSD", "WTI.spot"]


def test_variante_por_tipo_y_cifra():
    assert pa.variante_de(vision("a")) == "cita"
    assert pa.variante_de(vision("b", tipo="traduccion")) == "cita"
    assert pa.variante_de(vision("c", tipo="parafrasis", cita="Sin cifras, postura prudente.")) == "cita"
    assert pa.variante_de(vision("d", tipo="parafrasis", cita="Proyecta US$6.000 al cierre.")) == "meta"


def test_meta_exige_horizonte():
    v = vision("m", tipo="parafrasis", cita="Proyecta US$6.000 al cierre.", meta="US$6.000")
    assert not pa.vision_califica(v, "meta", MARTES, [])
    assert pa.vision_califica({**v, "horizonte": "promedio del 4T 2026"}, "meta", MARTES, [])


def test_meta_que_no_figura_en_la_cita_no_califica():
    v = vision("m", tipo="parafrasis", cita="Proyecta US$6.000 al cierre.", meta="US$6.500", horizonte="4T 2026")
    assert not pa.vision_califica(v, "meta", MARTES, [])


def test_vision_vieja_o_reciente_en_avisos_no_califica():
    assert not pa.vision_califica(vision("v", fecha="2026-08-01"), "cita", MARTES, [])
    hist = [{"fecha": "2026-09-20", "canal": pa.CANAL, "tipo": "vision", "clave": "v"}]
    assert not pa.vision_califica(vision("v"), "cita", MARTES, hist)
    hist_viejo = [{"fecha": "2026-09-10", "canal": pa.CANAL, "tipo": "vision", "clave": "v"}]
    assert pa.vision_califica(vision("v"), "cita", MARTES, hist_viejo)


def test_candidatos_sacan_lo_cubierto_hoy_y_los_feriados(monkeypatch):
    monkeypatch.setattr("screener_gi.gate_feriado", lambda t, f: "feriado de NYSE" if t == "WTI.spot" else None)
    hist = [uso(MARTES.isoformat(), "USDCLP")]
    assert pa.candidatos(MARTES, hist, UNIVERSO) == ["XAUUSD"]


def test_primero_el_activo_con_vision_fresca():
    visiones = {"v": vision("v", activo="XAUUSD")}
    hist = [uso("2026-09-25", "XAUUSD"), uso("2026-09-26", "XAUUSD")]
    assert pa.elegir("cita", MARTES, visiones, hist, UNIVERSO) == ("XAUUSD", "v")


def test_entre_iguales_el_menos_cubierto_y_luego_alfabetico():
    visiones = {"a": vision("a", activo="XAUUSD"), "b": vision("b", activo="USDCLP")}
    assert pa.elegir("cita", MARTES, visiones, [uso("2026-09-25", "USDCLP")], UNIVERSO) == ("XAUUSD", "a")
    assert pa.elegir("cita", MARTES, visiones, [], UNIVERSO) == ("USDCLP", "b")


def test_sin_vision_gana_el_menos_cubierto_sin_voz():
    hist = [uso("2026-09-25", "USDCLP"), uso("2026-09-26", "WTI.spot")]
    assert pa.elegir("cita", MARTES, {}, hist, UNIVERSO) == ("XAUUSD", None)


def test_sin_candidatos_se_informa():
    hist = [uso(MARTES.isoformat(), t) for t in UNIVERSO]
    with pytest.raises(pa.SinCandidatosError):
        pa.elegir("cita", MARTES, {}, hist, UNIVERSO)


def test_balance_retoma_la_manana():
    hist = [uso(MARTES.isoformat(), "XAUUSD", "avisos_manana", "v"), uso(MARTES.isoformat(), "USDCLP", "avisos_mediodia")]
    assert pa.activo_del_balance(hist, MARTES) == ("XAUUSD", "v")


def test_balance_cae_a_mediodia():
    hist = [uso(MARTES.isoformat(), "USDCLP", "avisos_mediodia", "m")]
    assert pa.activo_del_balance(hist, MARTES) == ("USDCLP", "m")


def test_balance_sin_manana_ni_mediodia_sale_sin_voz():
    assert pa.activo_del_balance([uso("2026-09-28", "USDCLP")], MARTES) == (None, None)


def test_registrar_uso_anota_al_preparar(tmp_path):
    ruta = tmp_path / "hist.json"
    ruta.write_text("[]", encoding="utf-8")
    pa.registrar_uso(MARTES, "avisos_manana", "USDCLP", "v", gastar_vision=True, ruta=ruta)
    pa.registrar_uso(MARTES, "avisos_tarde", "USDCLP", "v", gastar_vision=False, ruta=ruta)
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert [e["tipo"] for e in datos] == ["vision", "avisos", "avisos"]
    assert datos[2]["momento"] == "avisos_tarde"
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_pipeline_avisos.py -v`
Expected: FAIL con `AttributeError: module 'pipeline_avisos' has no attribute 'variante_de'`.

- [ ] **Step 3: Implement** (append en `scripts/pipeline_avisos.py`)

```python
# ---------------------------------------------------------------- elección


class SinCandidatosError(RuntimeError):
    """Ningún activo disponible para el momento: no hay carrusel que preparar."""


def variante_de(vision: dict[str, Any]) -> str:
    """Una paráfrasis con cifra de proyección es una meta; lo demás, una cita."""
    if vision.get("tipo") == "parafrasis" and pl._PRECIO.search(str(vision.get("cita", ""))):
        return "meta"
    return "cita"


def _edad_dias(entrada: dict[str, Any], hoy: date) -> int | None:
    try:
        return (hoy - date.fromisoformat(str(entrada.get("fecha")))).days
    except ValueError:
        return None


def _entradas(historial: list[dict[str, Any]], tipo: str) -> list[dict[str, Any]]:
    return [e for e in historial if e.get("tipo") == tipo and e.get("canal") == CANAL]


def vision_califica(vision: dict[str, Any], variante: str, hoy: date,
                    historial: list[dict[str, Any]]) -> bool:
    if variante_de(vision) != variante:
        return False
    if variante == "meta":
        meta = str(vision.get("meta", "")).strip()
        if not str(vision.get("horizonte", "")).strip() or not meta:
            return False
        if meta not in str(vision.get("cita", "")):
            return False  # la lámina mostraría una meta que la cita no respalda
    if pl.validar_vision(vision, hoy, None):
        return False
    for e in _entradas(historial, "vision"):
        edad = _edad_dias(e, hoy)
        if e.get("clave") == vision.get("id") and edad is not None and edad < VENTANA_VISION_DIAS:
            return False
    return True


def coberturas(historial: list[dict[str, Any]], hoy: date, dias: int) -> dict[str, int]:
    cuenta: dict[str, int] = {}
    for e in _entradas(historial, "avisos"):
        edad = _edad_dias(e, hoy)
        if edad is not None and 0 <= edad < dias:
            cuenta[e["clave"]] = cuenta.get(e["clave"], 0) + 1
    return cuenta


def cubiertos_hoy(historial: list[dict[str, Any]], hoy: date) -> set[str]:
    return {e["clave"] for e in _entradas(historial, "avisos") if e.get("fecha") == hoy.isoformat()}


def candidatos(hoy: date, historial: list[dict[str, Any]], universo: list[str] | None = None) -> list[str]:
    import screener_gi as sc

    if universo is None:
        from pipeline_informe import ACTIVOS_INFORME

        universo = list(dict.fromkeys([*ACTIVOS_INFORME, *sc.cobertura_fija()]))
    hechos = cubiertos_hoy(historial, hoy)
    return [t for t in universo if t not in hechos and sc.gate_feriado(t, hoy) is None]


def elegir(variante: str, hoy: date, visiones: dict[str, dict[str, Any]],
           historial: list[dict[str, Any]], universo: list[str] | None = None) -> tuple[str, str | None]:
    """El activo del carrusel y su visión (o `None`, que es `_falta_vision`).

    No usa el `Score_GI`: el score mide espacio para operar en el día, y lo que
    hace valer un carrusel de Avisos es que haya una voz de banco que contrastar.
    """
    cands = candidatos(hoy, historial, universo)
    if not cands:
        raise SinCandidatosError("Avisos ya cubrió hoy todos los activos disponibles.")
    cobertura = coberturas(historial, hoy, VENTANA_COBERTURA_DIAS)
    mejor: dict[str, dict[str, Any]] = {}
    for v in visiones.values():
        t = v.get("activo")
        if t in cands and vision_califica(v, variante, hoy, historial):
            actual = mejor.get(t)
            if actual is None or (v["fecha"], v["id"]) > (actual["fecha"], actual["id"]):
                mejor[t] = v

    def orden(t: str) -> tuple[int, str]:
        return (cobertura.get(t, 0), t)

    if mejor:
        t = min(mejor, key=orden)
        return t, mejor[t]["id"]
    return min(cands, key=orden), None


def activo_del_balance(historial: list[dict[str, Any]], hoy: date) -> tuple[str | None, str | None]:
    """El activo y la visión de la mañana; si no hubo, los del mediodía."""
    usos = [e for e in _entradas(historial, "avisos") if e.get("fecha") == hoy.isoformat()]
    for momento in ("avisos_manana", "avisos_mediodia"):
        for e in reversed(usos):
            if e.get("momento") == momento:
                return e["clave"], e.get("vision")
    return None, None


def _ruta_historial(ruta: Path | None) -> Path:
    from suplemento_canal import HISTORIAL

    return ruta or HISTORIAL


def cargar_historial(ruta: Path | None = None) -> list[dict[str, Any]]:
    from suplemento_canal import cargar_historial as _cargar

    return _cargar(_ruta_historial(ruta))


def registrar_uso(hoy: date, momento: str, activo: str | None, vision_id: str | None,
                  gastar_vision: bool, ruta: Path | None = None) -> None:
    """Se anota al PREPARAR: una tanda descartada gasta la ventana, hacia el lado seguro."""
    destino = _ruta_historial(ruta)
    historial = cargar_historial(destino)
    if vision_id and gastar_vision:
        historial.append({"fecha": hoy.isoformat(), "canal": CANAL, "tipo": "vision", "clave": vision_id})
    if activo:
        historial.append({"fecha": hoy.isoformat(), "canal": CANAL, "tipo": "avisos",
                          "clave": activo, "momento": momento, "vision": vision_id})
    destino.write_text(json.dumps(historial, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Agregar `horizonte` y `meta` a la visión de meta** en `data/visiones_expertos.json`, entrada `jpm-oro-6000-4t26` (editar con la herramienta de edición, no por consola):

```json
      "meta": "US$6.000",
      "horizonte": "promedio del cuarto trimestre de 2026",
```

Y en la `_nota` del archivo, al final: ` meta y horizonte: solo en las paráfrasis de proyección; meta es la cifra tal como figura en la cita.`

- [ ] **Step 5: Run tests**

Run: `uv run pytest tests/test_pipeline_avisos.py tests/test_pipeline_linkedin.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/pipeline_avisos.py tests/test_pipeline_avisos.py data/visiones_expertos.json
git commit -m "feat(avisos): elección por visión fresca y cobertura, historial al preparar"
```

---

### Task 4: Plantilla `vision.html` (variantes `cita` y `meta`)

**Files:**
- Create: `templates/stories/vision.html`
- Create: `tests/fixtures/stories/payloads/vision.json`
- Test: `tests/test_story_render.py`, quitar el `xfail` de `tests/test_pipeline_avisos.py`

**Interfaces:**
- Produces (tokens de la plantilla): `sello`, `fecha_hora`, `posicion`, `titular`, `remate`; `FOR:bloque_cita` con `etiqueta`, `cita`, `firma`, `fuente_fecha`; `FOR:bloque_meta` con `meta`, `horizonte`, `firma`, `precio_hoy`, `hora_precio`, `fuente_fecha`.

- [ ] **Step 1: Write the failing tests** (en `tests/test_story_render.py`, junto a los de calendario)

```python
VISION_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "vision.html"


def _payload_vision():
    return json.loads((FIXTURES_DIR / "payloads" / "vision.json").read_text(encoding="utf-8"))


def test_vision_variante_cita_no_deja_huerfanos_ni_la_meta():
    p = _payload_vision()
    html = story_render.build_html(p, VISION_TEMPLATE)
    assert p["bloque_cita"][0]["cita"] in html
    assert "Meta del banco" not in html
    assert "{{" not in html


def test_vision_variante_meta_muestra_meta_y_precio_hoy():
    p = _payload_vision()
    p["bloque_cita"] = []
    p["bloque_meta"] = [{"meta": "US$6.000", "horizonte": "promedio del 4T 2026", "firma": "Analista · JPMorgan",
                         "precio_hoy": "4.539,72", "hora_precio": "12:30 CLST", "fuente_fecha": "Reuters · 9 JUN 2026"}]
    html = story_render.build_html(p, VISION_TEMPLATE)
    assert "Meta del banco" in html and "US$6.000" in html and "4.539,72" in html
    assert "{{" not in html


def test_vision_render_dimensiones(tmp_path):
    pytest.importorskip("playwright")
    salida = story_render.render_story(_payload_vision(), VISION_TEMPLATE, tmp_path / "v.png")
    from PIL import Image
    assert Image.open(salida).size == (1920, 1080)
```

(Si `json` no está importado en `tests/test_story_render.py`, agrégalo arriba. `test_calendario_render_dimensiones` en el mismo archivo muestra cómo mide dimensiones hoy; si usa otra lib que PIL, copia esa forma.)

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --extra stories pytest tests/test_story_render.py -k vision -v`
Expected: FAIL, falta `vision.json` / `vision.html`.

- [ ] **Step 3: Create the fixture** `tests/fixtures/stories/payloads/vision.json`

```json
{
  "plantilla": "vision",
  "sello": "AVISOS · LA VOZ DEL BANCO",
  "fecha_hora": "MARTES 29 SEP · 11:30 CLST",
  "posicion": "2/4 · La voz del banco",
  "titular": "Lo que dice el banco sobre el dólar",
  "remate": "El banco pone el foco en los datos locales. Nuestra lectura la ves en la lámina siguiente.",
  "bloque_cita": [
    {
      "etiqueta": "",
      "cita": "“Los inversionistas se guían por datos y por ahora ven un país que crece poco.”",
      "firma": "Juan Pérez · Banco X",
      "fuente_fecha": "Diario Financiero · 14 SEP 2026"
    }
  ],
  "bloque_meta": []
}
```

- [ ] **Step 4: Create the template.** Copiar `templates/stories/avisos_portada.html` a `templates/stories/vision.html` **tal cual** (trae el bloque `marca.css embebido`, las `@font-face`, `.story`, `.velo`, `.grilla`, `.contenido`, `.cabecera`, `.sello`, `.fecha` y `.footer`). Cambiar `<title>` a `La voz del banco`. Reemplazar las reglas CSS desde `.centro` hasta `.clave { … }` inclusive por:

```css
.centro { flex: 1; display: flex; flex-direction: column; justify-content: center; max-width: 1600px; }
.etiqueta { font-weight: 700; font-size: 18px; letter-spacing: 0.10em; text-transform: uppercase; color: var(--acento); margin: 0 0 14px; }
.etiqueta:empty { display: none; }
.cita { font-family: var(--font-display); font-weight: 700; font-size: 58px; line-height: 1.18; color: var(--blanco); margin: 0; }
.firma { font-weight: 700; font-size: 26px; color: var(--texto-1); margin: 26px 0 0; }
.fuente { font-size: 20px; color: var(--texto-2); margin: 6px 0 0; }
.duelo { display: flex; gap: 40px; }
.lado { flex: 1; padding: 36px 40px; border-radius: 18px; border: 1.5px solid color-mix(in srgb, var(--acento) 45%, transparent);
  background: color-mix(in srgb, var(--fondo-acento) 80%, var(--fondo)); }
.lado-hoy { border-color: var(--acento); }
.rotulo { font-weight: 700; font-size: 20px; letter-spacing: 0.10em; text-transform: uppercase; color: var(--acento); margin: 0; }
.cifra { font-family: var(--font-display); font-weight: 700; font-size: 104px; line-height: 1; color: var(--blanco); margin: 18px 0 0; }
.detalle { font-size: 22px; color: var(--texto-borde); margin: 14px 0 0; }
.titular { font-family: var(--font-display); font-weight: 700; font-size: 40px; color: var(--blanco); margin: 44px 0 0; }
.remate { font-size: 26px; line-height: 1.4; color: var(--texto-borde); margin: 12px 0 0; max-width: 1400px; }
```

Y reemplazar el `<div class="centro">…</div>` del body por:

```html
      <div class="centro">
        <!-- FOR:bloque_cita -->
        <p class="etiqueta">{{etiqueta}}</p>
        <blockquote class="cita">{{cita}}</blockquote>
        <p class="firma">{{firma}}</p>
        <p class="fuente">{{fuente_fecha}}</p>
        <!-- ENDFOR:bloque_cita -->
        <!-- FOR:bloque_meta -->
        <div class="duelo">
          <div class="lado">
            <p class="rotulo">Meta del banco</p>
            <p class="cifra">{{meta}}</p>
            <p class="detalle">{{horizonte}}</p>
            <p class="detalle">{{firma}}</p>
          </div>
          <div class="lado lado-hoy">
            <p class="rotulo">Precio hoy</p>
            <p class="cifra">{{precio_hoy}}</p>
            <p class="detalle">{{hora_precio}} · MetaTrader 5</p>
          </div>
        </div>
        <p class="fuente">{{fuente_fecha}}</p>
        <!-- ENDFOR:bloque_meta -->
        <h2 class="titular">{{titular}}</h2>
        <p class="remate">{{remate}}</p>
      </div>
```

- [ ] **Step 5: Run checks**

Run: `uv run python scripts/sincronizar_css_plantillas.py --check && uv run python scripts/marca_tokens.py --check && uv run --extra stories pytest tests/test_story_render.py tests/test_marca_tokens.py -v`
Expected: PASS (incluye `test_plantilla_resuelve_sin_huerfanos[vision]` y el conteo plantillas = fixtures). Quita el `xfail` de `test_toda_plantilla_de_lamina_existe_en_disco` y corre `uv run pytest tests/test_pipeline_avisos.py -v`: PASS.

- [ ] **Step 6: Mira el PNG.** `uv run --extra stories python scripts/rendir_todas.py` y abre el PNG de `vision`: comillas “ ”, tildes y `·` visibles, nada cortado.

- [ ] **Step 7: Commit**

```bash
git add templates/stories/vision.html tests/fixtures/stories/payloads/vision.json tests/test_story_render.py tests/test_pipeline_avisos.py
git commit -m "feat(stories): plantilla vision con variantes cita y meta"
```

---

### Task 5: Alinear `avisos_portada` y `avisos_lectura` al contrato

Estas plantillas **ya existen** (el hilo principal las creó el 2026-09-28 para sacar a mano la tanda de la tarde con `produccion_adhoc.py`). Hoy la portada trae `sello`, `fecha_hora`, `kicker`, `titular`, `bajada`, `FOR:claves{texto}`, `posicion`; la lectura trae `sello`, `fecha_hora`, `titulo`, `FOR:puntos{icono,titulo_punto,texto}`, `conclusion`, `posicion`. Les falta lo que el spec §3.2 exige: en la portada, el precio del terminal, la hora de lectura y el número de láminas; en la lectura, la firma de GI y el aviso legal. **Lee cada archivo antes de tocarlo**: si ya trae alguno de estos tokens, no lo dupliques.

**Files:**
- Modify: `templates/stories/avisos_portada.html`, `templates/stories/avisos_lectura.html`
- Modify: `tests/fixtures/stories/payloads/avisos_portada.json`, `avisos_lectura.json`
- Test: `tests/test_story_render.py`

**Interfaces:**
- Produces: portada gana `dato_precio`, `dato_hora`, `total_laminas` (vacíos se ocultan con `:empty`); lectura gana `firma`, `aviso_legal`.

- [ ] **Step 1: Write the failing tests**

```python
PORTADA_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "avisos_portada.html"
LECTURA_TEMPLATE = _REPO_ROOT / "templates" / "stories" / "avisos_lectura.html"


def _fixture(nombre):
    return json.loads((FIXTURES_DIR / "payloads" / f"{nombre}.json").read_text(encoding="utf-8"))


def test_portada_muestra_precio_hora_y_laminas():
    p = {**_fixture("avisos_portada"), "dato_precio": "USD/CLP 936,32", "dato_hora": "LEÍDO 11:28 CLST",
         "total_laminas": "4 LÁMINAS"}
    html = story_render.build_html(p, PORTADA_TEMPLATE)
    for valor in ("USD/CLP 936,32", "LEÍDO 11:28 CLST", "4 LÁMINAS"):
        assert valor in html
    assert "{{" not in html


def test_portada_de_agenda_sin_precio_no_deja_huerfanos():
    html = story_render.build_html(_fixture("avisos_portada"), PORTADA_TEMPLATE)
    assert "{{" not in html


def test_lectura_firma_y_aviso_legal():
    html = story_render.build_html(_fixture("avisos_lectura"), LECTURA_TEMPLATE)
    assert "Grupo Inteligencia · Equipo de análisis" in html
    assert "Análisis informativo. No constituye recomendación de inversión." in html
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run --extra stories pytest tests/test_story_render.py -k "portada or lectura" -v`
Expected: FAIL (tokens ausentes en las plantillas o en las fixtures).

- [ ] **Step 3: Fixtures.** En `avisos_portada.json` agregar `"dato_precio": "", "dato_hora": "", "total_laminas": "3 LÁMINAS"`. En `avisos_lectura.json` agregar `"firma": "Grupo Inteligencia · Equipo de análisis", "aviso_legal": "Análisis informativo. No constituye recomendación de inversión."`.

- [ ] **Step 4: Portada.** CSS nuevo (antes de `.footer`):

```css
.dato { display: flex; gap: 22px; align-items: baseline; margin-top: 34px; }
.dato-precio { font-family: var(--font-display); font-weight: 700; font-size: 48px; color: var(--blanco); }
.dato-hora { font-size: 20px; font-weight: 600; letter-spacing: 0.06em; color: var(--texto-2); }
.dato-precio:empty, .dato-hora:empty { display: none; }
.footer-laminas { font-family: var(--font-sans); font-weight: 600; font-size: 15px; color: var(--texto-2); margin: 0 24px 0 auto; }
.footer-laminas:empty { display: none; }
```

HTML: después del `<div class="claves">…</div>` dentro de `.centro`:

```html
        <div class="dato">
          <span class="dato-precio">{{dato_precio}}</span>
          <span class="dato-hora">{{dato_hora}}</span>
        </div>
```

Y en `.footer`, antes de `<p class="footer-pos">`: `<span class="footer-laminas">{{total_laminas}}</span>`.

- [ ] **Step 5: Lectura.** CSS nuevo:

```css
.cierre { margin-top: 26px; }
.firma { font-weight: 700; font-size: 20px; color: var(--acento); margin: 0; }
.aviso-legal { font-size: 16px; color: var(--texto-3); margin: 6px 0 0; }
```

HTML: al final de `.contenido`, después de la conclusión:

```html
      <div class="cierre">
        <p class="firma">{{firma}}</p>
        <p class="aviso-legal">{{aviso_legal}}</p>
      </div>
```

- [ ] **Step 6: Run checks**

Run: `uv run python scripts/sincronizar_css_plantillas.py --check && uv run python scripts/marca_tokens.py --check && uv run --extra stories pytest tests/test_story_render.py -v`
Expected: PASS. Rinde con `scripts/rendir_todas.py` y mira que nada se salga del lienzo.

- [ ] **Step 7: Commit**

```bash
git add templates/stories/avisos_portada.html templates/stories/avisos_lectura.html tests/fixtures/stories/payloads/avisos_portada.json tests/fixtures/stories/payloads/avisos_lectura.json tests/test_story_render.py
git commit -m "feat(stories): portada con precio y hora de lectura, lectura con firma y aviso legal"
```

---

### Task 6: Armar las láminas (datos puros, sin disco ni terminal)

**Files:**
- Modify: `scripts/pipeline_avisos.py` (append)
- Test: `tests/test_pipeline_avisos.py`

**Interfaces:**
- Consumes: `pc.construir_payload(seleccion, activo_catalogo, ahora, cierres)`, `pc.formatear_precio(valor, digits)`, `pc.direccion_publicada(dir)`, `pl.CAMPOS_PRECIO`, `laminas_de`, `fecha_hora`, `etiqueta_hora`, `variante_de`.
- Produces:
  - `lectura` (dict que devuelve el lector del terminal): `{"ticker", "activo": <fila de catálogo>, "seleccion": <evaluar_activo>, "h1": <analizar_activo H1>, "cierres": list[float]}`
  - `CAMPOS_AVISOS = pl.CAMPOS_PRECIO + ("soporte_publicado", "resistencia_publicada")`
  - `fila_medida(lectura, payload_datos) -> dict`
  - `lamina_portada(activo_nombre: str | None, precio: str, leido: datetime, ahora: datetime, agenda: bool) -> dict`
  - `lamina_voz(vision, variante, fila, leido, ahora) -> dict`
  - `lamina_datos(lectura, ahora) -> dict`
  - `lamina_semana(agenda: list[dict], ahora) -> dict` y `eventos_calendario(agenda, ahora, maximo=6) -> list[dict]`
  - `lamina_lectura(ahora) -> dict`
  - `armar_tanda(momento, formato, ahora, lectura: dict | None, vision: dict | None, agenda: list[dict]) -> tuple[dict, dict[str, dict]]` → `(meta, {clave: payload})`

`meta` (`_avisos.json`): `{"version": 1, "momento", "formato", "fecha", "activo", "vision", "vision_variante", "_falta_vision", "leido_en", "direccion", "activos": {ticker: fila}, "activos_preparacion": {ticker: fila}, "cifras_citadas": {}, "aceptar_antiguas": {}}`.

- [ ] **Step 1: Write the failing tests**

```python
AHORA = datetime(2026, 9, 29, 11, 30, tzinfo=pa.SANTIAGO)


def lectura_falsa(ticker="USDCLP", precio=936.32, digits=2, nombre="Dólar / Peso chileno"):
    activo = {"ticker": ticker, "nombre": nombre, "clase": "forex_commodities", "categoria": "forex",
              "digits": digits, "unidad": "CLP", "imagen": "assets/activos/usdclp.jpg", "volatilidad": "media",
              "nota_volatilidad": "en 1H se lee el movimiento del día sin el ruido de 15M; 4H confirma la tendencia"}
    sel = {"ticker": ticker, "nombre": nombre, "clase": "forex_commodities", "direccion": "ALCISTA", "score": 60,
           "precio": precio, "soporte": precio - 3, "resistencia": precio + 3, "atr_h1": 1.2, "atr_d1": 6.0,
           "impulso_adc_atr": 1.8, "banda_estrecha": None, "factores": {}}
    h1 = {"price": precio, "s1": precio - 3, "r1": precio + 3, "s2": precio - 6, "r2": precio + 6,
          "ema_50": precio - 1, "donchian_50_high": precio + 8, "donchian_50_low": precio - 8, "atr_14": 1.2}
    cierres = [round(precio - (59 - i) * 0.01, 6) for i in range(60)]
    return {"ticker": ticker, "activo": activo, "seleccion": sel, "h1": h1, "cierres": cierres}


def test_tanda_de_cita_con_voz_tiene_cuatro_laminas_y_todas_con_titular_y_parrafo():
    meta, laminas = pa.armar_tanda("avisos_manana", "cita", AHORA, lectura_falsa(), vision("v"), [])
    assert list(laminas) == ["portada", "voz", "datos", "lectura"]
    for payload in laminas.values():
        assert "titular" in payload and "parrafo" in payload
        assert payload["_plantilla"] in pa.PLANTILLAS
    assert meta["activo"] == "USDCLP" and meta["vision"] == "v" and meta["_falta_vision"] is False
    assert meta["direccion"] == "Alcista"


def test_tanda_sin_vision_queda_marcada_y_sin_voz():
    meta, laminas = pa.armar_tanda("avisos_manana", "cita", AHORA, lectura_falsa(), None, [])
    assert meta["_falta_vision"] is True
    assert "voz" not in laminas


def test_la_portada_trae_el_precio_del_terminal_y_la_hora():
    _, laminas = pa.armar_tanda("avisos_manana", "cita", AHORA, lectura_falsa(), None, [])
    assert laminas["portada"]["dato_precio"].endswith("936,32")
    assert laminas["portada"]["dato_hora"] == "LEÍDO 11:30 CLST"
    assert laminas["portada"]["sello"] == "AVISOS · DÓLAR / PESO CHILENO"


def test_portada_del_cobre_escribe_el_precio_como_la_alerta():
    lec = lectura_falsa("COPPER", 14197.0, 0, "Cobre")
    _, laminas = pa.armar_tanda("avisos_manana", "cita", AHORA, lec, None, [])
    assert laminas["portada"]["dato_precio"].endswith(laminas["datos"]["precio_actual"])
    assert laminas["datos"]["precio_actual"] == "14197"


def test_la_voz_meta_muestra_la_meta_y_el_precio_de_hoy():
    v = vision("m", tipo="parafrasis", cita="Proyecta $980 a fin de año.", meta="$980", horizonte="fin de 2026")
    _, laminas = pa.armar_tanda("avisos_mediodia", "meta", AHORA, lectura_falsa(), v, [])
    voz = laminas["voz"]
    assert voz["bloque_cita"] == []
    assert voz["bloque_meta"][0]["meta"] == "$980"
    assert voz["bloque_meta"][0]["precio_hoy"] == "936,32"


def test_la_voz_de_una_traduccion_lo_dice():
    _, laminas = pa.armar_tanda("avisos_manana", "cita", AHORA, lectura_falsa(), vision("t", tipo="traduccion"), [])
    assert laminas["voz"]["bloque_cita"][0]["etiqueta"] == "Traducción nuestra"


def test_la_fila_medida_incluye_los_niveles_publicados():
    meta, laminas = pa.armar_tanda("avisos_manana", "cita", AHORA, lectura_falsa(), None, [])
    fila = meta["activos"]["USDCLP"]
    niveles = {n["rol"]: n["precio"] for n in laminas["datos"]["recorrido"]["niveles"]}
    assert fila["soporte_publicado"] == niveles["SOPORTE"]
    assert fila["price"] == 936.32 and fila["digits"] == 2


AGENDA = [
    {"fecha": "2026-10-02", "hora": "08:30", "pais": "United States", "evento": "Nonfarm Payrolls",
     "nombre_es": "Nóminas no agrícolas", "consenso": "98K", "anterior": "162K"},
    {"fecha": "2026-09-30", "hora": "10:30", "pais": "United States", "evento": "Crude Oil Inventories",
     "nombre_es": "", "consenso": "", "anterior": "-1.2M"},
    {"fecha": "2026-10-05", "hora": "09:00", "pais": "Chile", "evento": "Imacec", "nombre_es": "Imacec",
     "consenso": "", "anterior": "0,5%"},
]


def test_la_agenda_arma_los_tokens_de_calendario_en_orden_y_solo_esta_semana():
    lunes = datetime(2026, 9, 28, 15, 30, tzinfo=pa.SANTIAGO)
    eventos = pa.eventos_calendario(AGENDA, lunes)
    assert [e["numero"] for e in eventos] == ["01", "02"]
    assert eventos[0]["dia"] == "MIÉRCOLES 30" and eventos[0]["evento"] == "Crude Oil Inventories"
    assert eventos[1]["evento"] == "Nóminas no agrícolas" and eventos[1]["pais"] == "EE.UU."
    assert eventos[1]["esperado"] == "98K" and eventos[1]["tiene_esperado"] is True
    assert eventos[0]["tiene_esperado"] is False
    assert eventos[0]["hora"] == "10:30 CLST" and eventos[0]["impacto_slug"] == "alto"


def test_la_tanda_de_agenda_no_tiene_activo_ni_alerta():
    lunes = datetime(2026, 9, 28, 15, 30, tzinfo=pa.SANTIAGO)
    meta, laminas = pa.armar_tanda("avisos_tarde", "agenda", lunes, None, None, AGENDA)
    assert list(laminas) == ["portada", "semana", "lectura"]
    assert meta["activo"] is None and meta["_falta_vision"] is False
    assert laminas["portada"]["dato_precio"] == ""
    assert laminas["portada"]["sello"] == "AVISOS · AGENDA DE LA SEMANA"
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_pipeline_avisos.py -v`
Expected: FAIL con `AttributeError: … 'armar_tanda'`.

- [ ] **Step 3: Implement** (append)

```python
# ---------------------------------------------------------------- láminas

CAMPOS_AVISOS = pl.CAMPOS_PRECIO + ("soporte_publicado", "resistencia_publicada")

_PAISES = {"United States": "EE.UU.", "Chile": "Chile", "China": "China",
           "Euro Zone": "Zona Euro", "Euro Area": "Zona Euro", "Zona Euro": "Zona Euro"}
_ETIQUETA_TIPO = {"textual": "", "traduccion": "Traducción nuestra", "parafrasis": "En palabras nuestras"}
CTA_AGENDA = ("¿Quieres seguir esta semana en detalle?", "Habla hoy con tu analista")


def _fmt(valor: float, digits: int) -> str:
    return pc.formatear_precio(float(valor), digits)


def _fecha_corta(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day} {_MESES[d.month - 1]} {d.year}"


def fila_medida(lectura: dict[str, Any], payload_datos: dict[str, Any]) -> dict[str, Any]:
    """Lo que el texto puede citar: los niveles del terminal y los publicados en la alerta.

    La alerta acota sus niveles (`acotar_niveles_intradia`), así que el soporte
    que ve el cliente puede no ser el `s1` crudo: los dos cuentan como medidos.
    """
    niveles = {n["rol"]: n["precio"] for n in payload_datos["recorrido"]["niveles"]}
    fila: dict[str, Any] = {"nombre": lectura["activo"]["nombre"], "digits": lectura["activo"]["digits"]}
    fila.update({c: lectura["h1"].get(c) for c in pl.CAMPOS_PRECIO})
    fila["soporte_publicado"] = niveles.get("SOPORTE")
    fila["resistencia_publicada"] = niveles.get("RESISTENCIA")
    return fila


def lamina_portada(activo_nombre: str | None, precio: str, leido: datetime, ahora: datetime,
                   agenda: bool) -> dict[str, Any]:
    return {
        "_plantilla": "avisos_portada", "plantilla": "avisos_portada",
        "sello": "AVISOS · AGENDA DE LA SEMANA" if agenda else f"AVISOS · {str(activo_nombre).upper()}",
        "fecha_hora": fecha_hora(ahora),
        "kicker": MARCA, "titular": MARCA, "parrafo": MARCA,
        "claves": [{"texto": MARCA} for _ in range(3)],
        "pie": MARCA,
        "dato_precio": "" if agenda else f"{activo_nombre} {precio}",
        "dato_hora": "" if agenda else f"LEÍDO {etiqueta_hora(leido)}",
        "total_laminas": "", "posicion": "",
    }


def lamina_voz(vision: dict[str, Any], variante: str, fila: dict[str, Any], leido: datetime,
               ahora: datetime) -> dict[str, Any]:
    firma = f"{vision['quien']} · {vision['institucion']}"
    fuente_fecha = f"{vision.get('fuente') or vision['institucion']} · {_fecha_corta(vision['fecha'])}"
    if variante == "meta":
        bloque_cita: list[dict[str, str]] = []
        bloque_meta = [{
            "meta": vision["meta"], "horizonte": vision["horizonte"], "firma": firma,
            "precio_hoy": _fmt(fila["price"], fila["digits"]), "hora_precio": etiqueta_hora(leido),
            "fuente_fecha": fuente_fecha,
        }]
    else:
        tipo = vision.get("tipo", "textual")
        cita = vision["cita"] if tipo == "parafrasis" else f"“{vision['cita']}”"
        bloque_cita = [{"etiqueta": _ETIQUETA_TIPO.get(tipo, ""), "cita": cita, "firma": firma,
                        "fuente_fecha": fuente_fecha}]
        bloque_meta = []
    return {
        "_plantilla": "vision", "plantilla": "vision",
        "_procedencia": {"vision": vision["id"], "ticker": vision.get("activo")},
        "sello": "AVISOS · LA VOZ DEL BANCO", "fecha_hora": fecha_hora(ahora),
        "titular": MARCA, "parrafo": MARCA,
        "bloque_cita": bloque_cita, "bloque_meta": bloque_meta, "posicion": "",
    }


def lamina_datos(lectura: dict[str, Any], ahora: datetime) -> dict[str, Any]:
    payload = pc.construir_payload(lectura["seleccion"], lectura["activo"], ahora, lectura["cierres"])
    payload.update({"_plantilla": "avisos_datos", "titular": MARCA, "parrafo": MARCA})
    return payload


def eventos_calendario(agenda: list[dict[str, Any]], ahora: datetime, maximo: int = 6) -> list[dict[str, Any]]:
    """Los tokens que espera `calendario.html`, que antes nadie armaba.

    Solo los días hábiles de la semana de `ahora` (lunes a viernes), en orden de
    reloj. `leer_agenda` ya entrega la hora en Santiago: no se vuelve a convertir.
    """
    local = ahora.astimezone(SANTIAGO)
    lunes = local.date() - timedelta(days=local.weekday())
    viernes = lunes + timedelta(days=4)
    elegidos = []
    for ev in agenda:
        cuando = datetime.strptime(f"{ev['fecha']} {ev['hora']}", "%Y-%m-%d %H:%M").replace(tzinfo=SANTIAGO)
        if lunes <= cuando.date() <= viernes:
            elegidos.append((cuando, ev))
    elegidos.sort(key=lambda par: par[0])
    salida = []
    for i, (cuando, ev) in enumerate(elegidos[:maximo], 1):
        esperado = str(ev.get("consenso") or "").strip()
        salida.append({
            "numero": f"{i:02d}",
            "dia": f"{_DIAS[cuando.weekday()]} {cuando.day}",
            "hora": etiqueta_hora(cuando),
            "evento": ev.get("nombre_es") or ev.get("evento", ""),
            "pais": _PAISES.get(ev.get("pais", ""), ev.get("pais", "")),
            "impacto": "Alto impacto", "impacto_slug": "alto",
            "anterior": str(ev.get("anterior") or ""),
            "esperado": esperado, "tiene_esperado": bool(esperado),
        })
    return salida


def lamina_semana(agenda: list[dict[str, Any]], ahora: datetime) -> dict[str, Any]:
    return {
        "_plantilla": "avisos_agenda", "plantilla": "calendario",
        "sello": "AVISOS · AGENDA DE LA SEMANA", "fecha_hora": fecha_hora(ahora),
        "titular": MARCA, "parrafo": MARCA,
        "eventos": eventos_calendario(agenda, ahora),
        "cta": CTA_AGENDA[0], "cta_sub": CTA_AGENDA[1], "posicion": "",
    }


def lamina_lectura(ahora: datetime) -> dict[str, Any]:
    return {
        "_plantilla": "avisos_lectura", "plantilla": "avisos_lectura",
        "sello": "AVISOS · NUESTRA LECTURA", "fecha_hora": fecha_hora(ahora),
        "titular": MARCA, "parrafo": MARCA,
        "puntos": [{"icono": "🔎", "titulo_punto": MARCA, "texto": MARCA} for _ in range(3)],
        "firma": FIRMA, "aviso_legal": AVISO_LEGAL, "posicion": "",
    }


def armar_tanda(momento: str, formato: str, ahora: datetime, lectura: dict[str, Any] | None,
                vision: dict[str, Any] | None, agenda: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    agenda_semana = formato == "agenda"
    laminas: dict[str, dict[str, Any]] = {}
    activos: dict[str, dict[str, Any]] = {}
    direccion = None
    if agenda_semana:
        laminas["portada"] = lamina_portada(None, "", ahora, ahora, agenda=True)
        laminas["semana"] = lamina_semana(agenda, ahora)
    else:
        datos = lamina_datos(lectura, ahora)
        fila = fila_medida(lectura, datos)
        activos[lectura["ticker"]] = fila
        direccion = pc.direccion_publicada(lectura["seleccion"]["direccion"])
        laminas["portada"] = lamina_portada(lectura["activo"]["nombre"], datos["precio_actual"],
                                            ahora, ahora, agenda=False)
        if vision is not None:
            variante = variante_de(vision)
            laminas["voz"] = lamina_voz(vision, variante, fila, ahora, ahora)
        laminas["datos"] = datos
    laminas["lectura"] = lamina_lectura(ahora)
    meta = {
        "version": 1, "momento": momento, "formato": formato, "fecha": ahora.date().isoformat(),
        "activo": None if agenda_semana else lectura["ticker"],
        "vision": vision["id"] if vision else None,
        "vision_variante": variante_de(vision) if vision else None,
        "_falta_vision": (not agenda_semana) and vision is None,
        "leido_en": ahora.isoformat(timespec="minutes"),
        "direccion": direccion,
        "activos": activos,
        "activos_preparacion": json.loads(json.dumps(activos)),
        "cifras_citadas": {}, "aceptar_antiguas": {},
    }
    return meta, laminas
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_pipeline_avisos.py -v`
Expected: PASS. Si `construir_payload` lanza `PayloadIncoherenteError` con `lectura_falsa`, revisa que la serie termine en el precio (`cierres[-1] == precio`) y que `soporte < precio < resistencia`.

- [ ] **Step 5: Commit**

```bash
git add scripts/pipeline_avisos.py tests/test_pipeline_avisos.py
git commit -m "feat(avisos): armado de láminas y tokens del calendario de la semana"
```

---

### Task 7: Escribir la tanda, frenos de `--rendir` y render

**Files:**
- Modify: `scripts/pipeline_avisos.py` (append)
- Test: `tests/test_pipeline_avisos.py`

**Interfaces:**
- Consumes: `pl.validar_textos`, `pl.validar_cifras`, `pl.validar_frescura`, `pl.validar_vision`, `pl.cargar_visiones`, `pc.exigir_texto_editorial`, `pc.elegir_variante`, `pc.CIERRES_ALERTA`, `story_render.render_story`, `story_grafico.enriquecer`.
- Produces:
  - `escribir_laminas(dir_canal: Path, formato: str, laminas: dict[str, dict]) -> None` (borra `N_*` y renumera)
  - `escribir_meta(dir_canal, meta)`, `leer_meta(dir_canal) -> dict`, `leer_laminas(dir_canal) -> list[tuple[str, dict]]` (stem, payload) en orden
  - `textos_de(laminas) -> list[tuple[str, str]]`
  - `mensaje_de(payload: dict, meta: dict) -> str`
  - `validar_tanda(dir_canal, ahora, visiones: dict, activos_extra: dict | None = None) -> list[str]`
  - `tokens_de(payload) -> dict`
  - `rendir_tanda(dir_canal, ahora=None, visiones=None, render: Callable | None = None) -> list[Path]`

- [ ] **Step 1: Write the failing tests**

```python
def _tanda(tmp_path, formato="cita", con_vision=True, lec=None):
    momento = {"cita": "avisos_manana", "meta": "avisos_mediodia", "balance": "avisos_tarde"}.get(formato, "avisos_tarde")
    v = vision("v") if con_vision else None
    meta, laminas = pa.armar_tanda(momento, formato, AHORA, lec or lectura_falsa(), v, [])
    dir_canal = tmp_path / "2026-09-29_11-30_avisos_x" / pa.CANAL
    dir_canal.mkdir(parents=True)
    pa.escribir_meta(dir_canal, meta)
    pa.escribir_laminas(dir_canal, formato, laminas)
    return dir_canal, {"v": v} if v else {}


def _escribir_todo(dir_canal, pie="El dólar mantiene un sesgo alcista sobre su promedio de 50 horas."):
    for stem, payload in pa.leer_laminas(dir_canal):
        for campo in ("kicker", "titular", "parrafo"):
            if campo in payload:
                payload[campo] = "Texto de prueba suficientemente largo para el freno"
        if "pie" in payload:
            payload["pie"] = pie
        for lista in ("claves", "puntos"):
            for item in payload.get(lista, []):
                for k in ("texto", "titulo_punto"):
                    if k in item:
                        item[k] = "Punto de prueba"
        (dir_canal / f"{stem}.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_escribir_laminas_numera_y_pone_el_pie_de_posicion(tmp_path):
    dir_canal, _ = _tanda(tmp_path)
    stems = [s for s, _ in pa.leer_laminas(dir_canal)]
    assert stems == ["1_portada", "2_voz", "3_datos", "4_lectura"]
    portada = dict(pa.leer_laminas(dir_canal))["1_portada"]
    assert portada["posicion"] == "1/4 · Portada" and portada["total_laminas"] == "4 LÁMINAS"


def test_una_tanda_sin_escribir_no_se_rinde(tmp_path):
    dir_canal, visiones = _tanda(tmp_path)
    errores = pa.validar_tanda(dir_canal, AHORA, visiones)
    assert any("sin escribir" in e for e in errores)


def test_una_tanda_escrita_pasa_los_frenos(tmp_path):
    dir_canal, visiones = _tanda(tmp_path)
    _escribir_todo(dir_canal)
    assert pa.validar_tanda(dir_canal, AHORA, visiones) == []


def test_el_pie_sin_direccion_se_detiene(tmp_path):
    dir_canal, visiones = _tanda(tmp_path)
    _escribir_todo(dir_canal, pie="El dólar se mueve hoy entre dos niveles claros del día.")
    assert any("dirección" in e for e in pa.validar_tanda(dir_canal, AHORA, visiones))


def test_una_cifra_sin_respaldo_se_detiene(tmp_path):
    dir_canal, visiones = _tanda(tmp_path)
    _escribir_todo(dir_canal, pie="El dólar tiene sesgo alcista y apunta a $951,00 hoy.")
    assert any("$951,00" in e for e in pa.validar_tanda(dir_canal, AHORA, visiones))


def test_la_frescura_vence_a_los_121_minutos(tmp_path):
    dir_canal, visiones = _tanda(tmp_path)
    _escribir_todo(dir_canal)
    assert pa.validar_tanda(dir_canal, AHORA + timedelta(minutes=119), visiones) == []
    assert any("--refrescar" in e for e in pa.validar_tanda(dir_canal, AHORA + timedelta(minutes=121), visiones))


def test_una_vision_que_ya_no_esta_en_el_registro_se_detiene(tmp_path):
    dir_canal, _ = _tanda(tmp_path)
    _escribir_todo(dir_canal)
    assert any("registro" in e for e in pa.validar_tanda(dir_canal, AHORA, {}))


def test_el_pie_de_la_portada_lleva_cierre_y_aviso_y_es_estable(tmp_path):
    dir_canal, _ = _tanda(tmp_path)
    _escribir_todo(dir_canal)
    meta = pa.leer_meta(dir_canal)
    portada = dict(pa.leer_laminas(dir_canal))["1_portada"]
    msg = pa.mensaje_de(portada, meta)
    assert msg.startswith("El dólar mantiene un sesgo alcista")
    assert pa.AVISO_LEGAL in msg and msg.rstrip().endswith("1/4 · Portada")
    assert any(c in msg for c in pa.pc.CIERRES_ALERTA)
    assert pa.mensaje_de(portada, meta) == msg


def test_las_demas_laminas_llevan_solo_su_posicion(tmp_path):
    dir_canal, _ = _tanda(tmp_path)
    voz = dict(pa.leer_laminas(dir_canal))["2_voz"]
    assert pa.mensaje_de(voz, pa.leer_meta(dir_canal)) == "2/4 · La voz del banco"


def test_rendir_escribe_png_y_mensaje_por_lamina_y_usa_el_freno_del_despacho(tmp_path, monkeypatch):
    dir_canal, visiones = _tanda(tmp_path)
    _escribir_todo(dir_canal)
    llamadas = []
    monkeypatch.setattr(pa.pc, "exigir_texto_editorial", lambda pares: llamadas.append(len(pares)))

    def render_falso(tokens, plantilla, salida, formato="horizontal"):
        assert "{{" not in json.dumps(tokens)
        salida.write_bytes(b"png")
        return salida

    pngs = pa.rendir_tanda(dir_canal, AHORA, visiones, render=render_falso)
    assert [p.name for p in pngs] == ["1_portada.png", "2_voz.png", "3_datos.png", "4_lectura.png"]
    assert all((dir_canal / f"{p.stem}_mensaje.txt").exists() for p in pngs)
    assert llamadas == [4]


def test_tokens_de_traduce_titular_y_parrafo_por_plantilla(tmp_path):
    dir_canal, _ = _tanda(tmp_path)
    laminas = dict(pa.leer_laminas(dir_canal))
    assert "bajada" in pa.tokens_de(laminas["1_portada"])
    assert "remate" in pa.tokens_de(laminas["2_voz"])
    t = pa.tokens_de(laminas["4_lectura"])
    assert "titulo" in t and "conclusion" in t
    assert not any(k.startswith("_") for k in t)
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_pipeline_avisos.py -v`
Expected: FAIL con `AttributeError: … 'escribir_meta'`.

- [ ] **Step 3: Implement** (append)

```python
# ---------------------------------------------------------------- disco


def escribir_meta(dir_canal: Path, meta: dict[str, Any]) -> None:
    (dir_canal / "_avisos.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def leer_meta(dir_canal: Path) -> dict[str, Any]:
    return json.loads((dir_canal / "_avisos.json").read_text(encoding="utf-8"))


def _archivos_de_lamina(dir_canal: Path) -> list[Path]:
    return [p for p in dir_canal.iterdir() if p.is_file() and p.name[:1].isdigit()]


def escribir_laminas(dir_canal: Path, formato: str, laminas: dict[str, dict[str, Any]]) -> None:
    """Escribe las láminas numeradas desde cero. Renumerar es borrar y volver a escribir."""
    for viejo in _archivos_de_lamina(dir_canal):
        viejo.unlink()
    orden = laminas_de(formato, con_voz="voz" in laminas)
    total = f"{len(orden)} LÁMINAS"
    for lamina in orden:
        payload = laminas[lamina["clave"]]
        payload["_clave"] = lamina["clave"]
        payload["posicion"] = lamina["posicion"]
        if lamina["clave"] == "portada":
            payload["total_laminas"] = total
        (dir_canal / f"{lamina['stem']}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def leer_laminas(dir_canal: Path) -> list[tuple[str, dict[str, Any]]]:
    return [
        (p.stem, json.loads(p.read_text(encoding="utf-8")))
        for p in sorted(dir_canal.glob("*.json"))
        if p.stem[:1].isdigit()
    ]


# ---------------------------------------------------------------- frenos

_CAMPOS_TEXTO = ("kicker", "titular", "parrafo", "pie")
_CAMPOS_ITEM = ("texto", "titulo_punto")


def textos_de(laminas: list[tuple[str, dict[str, Any]]]) -> list[tuple[str, str]]:
    """Todo texto editorial de las láminas. Las citas no: salen del registro."""
    salida: list[tuple[str, str]] = []
    for stem, payload in laminas:
        for campo in _CAMPOS_TEXTO:
            if campo in payload:
                salida.append((f"{stem}.{campo}", str(payload[campo])))
        for lista in ("claves", "puntos"):
            for i, item in enumerate(payload.get(lista, []), 1):
                for campo in _CAMPOS_ITEM:
                    if campo in item:
                        salida.append((f"{stem}.{lista}[{i}].{campo}", str(item[campo])))
    return salida


def mensaje_de(payload: dict[str, Any], meta: dict[str, Any]) -> str:
    """El texto de la lámina. La portada lleva el pie completo; las demás, su posición.

    El cierre y el aviso los agrega el script, estables por tanda: el despacho
    vuelve a rendir y un texto distinto al aprobado no puede salir.
    """
    if payload.get("_clave") != "portada":
        return payload["posicion"]
    cierre = pc.elegir_variante(pc.CIERRES_ALERTA, meta.get("activo") or "agenda", meta["momento"], meta["fecha"])
    return "\n\n".join([str(payload["pie"]).strip(), cierre, AVISO_LEGAL, payload["posicion"]])


def validar_tanda(dir_canal: Path, ahora: datetime, visiones: dict[str, dict[str, Any]],
                  activos_extra: dict[str, dict[str, Any]] | None = None) -> list[str]:
    """Todos los motivos por los que el carrusel no puede rendirse. Vacío = puede."""
    meta = leer_meta(dir_canal)
    laminas = leer_laminas(dir_canal)
    textos = textos_de(laminas)
    errores = pl.validar_textos(textos)

    if len(laminas) > MAX_LAMINAS:
        errores.append(f"{len(laminas)} láminas: máximo {MAX_LAMINAS}")

    usadas: list[dict[str, Any]] = []
    vid = meta.get("vision")
    if vid:
        if vid not in visiones:
            errores.append(f"visión `{vid}`: no está en el registro {pl.REGISTRO_VISIONES.name}")
        else:
            usadas.append(visiones[vid])
            errores.extend(pl.validar_vision(visiones[vid], ahora.date(), meta.get("aceptar_antiguas", {}).get(vid)))

    activos = dict(meta.get("activos", {}))
    for ticker, fila in (activos_extra or {}).items():
        activos[f"{ticker}#preparacion"] = fila
    errores.extend(pl.validar_cifras(textos, activos, usadas, meta.get("cifras_citadas", {}), campos=CAMPOS_AVISOS))

    leido = datetime.fromisoformat(meta["leido_en"])
    errores.extend(pl.validar_frescura(leido, ahora, FRESCURA_MAX_HORAS, remedio="Corre --refrescar."))

    if meta["formato"] != "agenda" and meta.get("direccion"):
        pie = next((str(p.get("pie", "")) for _, p in laminas if p.get("_clave") == "portada"), "")
        if MARCA not in pie and meta["direccion"].lower() not in pie.lower():
            errores.append(
                f"1_portada.pie: no nombra la dirección ({meta['direccion'].lower()}). "
                "El cliente tiene que saber hacia dónde va el activo."
            )
    return errores


# ---------------------------------------------------------------- render


def tokens_de(payload: dict[str, Any]) -> dict[str, Any]:
    """Del contrato del despacho (`titular`, `parrafo`) a los tokens de cada plantilla."""
    tokens = {k: v for k, v in payload.items() if not k.startswith("_")}
    tokens.pop("pie", None)
    plantilla = payload["_plantilla"]
    if plantilla == "avisos_portada":
        tokens["bajada"] = tokens.pop("parrafo")
    elif plantilla == "vision":
        tokens["remate"] = tokens.pop("parrafo")
    elif plantilla == "avisos_lectura":
        tokens["titulo"] = tokens.pop("titular")
        tokens["conclusion"] = tokens.pop("parrafo")
    elif plantilla == "avisos_agenda":
        tokens["titulo"] = tokens.pop("titular")
        tokens["subtitulo"] = tokens.pop("parrafo")
    elif plantilla == "avisos_datos":
        from story_grafico import enriquecer

        tokens = enriquecer(tokens)
    return tokens


def rendir_tanda(dir_canal: Path, ahora: datetime | None = None,
                 visiones: dict[str, dict[str, Any]] | None = None,
                 render: Callable[..., Path] | None = None) -> list[Path]:
    ahora = ahora or datetime.now(SANTIAGO)
    visiones = visiones if visiones is not None else pl.cargar_visiones()
    errores = validar_tanda(dir_canal, ahora, visiones)
    if errores:
        raise SystemExit("El carrusel no se rinde:\n  " + "\n  ".join(errores))
    laminas = leer_laminas(dir_canal)
    # El mismo freno de las dos rutas de render del carrusel (su test de contrato).
    pc.exigir_texto_editorial(laminas)
    if render is None:
        from story_render import render_story as render
    meta = leer_meta(dir_canal)
    salidas: list[Path] = []
    for stem, payload in laminas:
        png = dir_canal / f"{stem}.png"
        render(tokens_de(payload), DIR_PLANTILLAS / PLANTILLAS[payload["_plantilla"]], png, formato="horizontal")
        (dir_canal / f"{stem}_mensaje.txt").write_text(mensaje_de(payload, meta), encoding="utf-8")
        salidas.append(png)
    return salidas
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_pipeline_avisos.py -v`
Expected: PASS. Si `pl.validar_textos` marca "Punto de prueba" por algún linter de `validar_texto`, cambia el texto de prueba a una frase normal más larga; no relajes el freno.

- [ ] **Step 5: Commit**

```bash
git add scripts/pipeline_avisos.py tests/test_pipeline_avisos.py
git commit -m "feat(avisos): frenos del carrusel, pie con cierre estable y render por plantilla"
```

---

### Task 8: `--preparar`, `--refrescar`, `--completar-vision`, `--validar` y CLI

**Files:**
- Modify: `scripts/pipeline_avisos.py` (append)
- Test: `tests/test_pipeline_avisos.py`

**Interfaces:**
- Consumes: `pl.leer_agenda(ahora)`, `pl._catalogo()`, `screener_gi.evaluar_activo(activo, eventos, delta, ahora, fijo=True, ignorar_agotamiento=True)`, `market_data_mcp.analisis.analizar_activo`, `pc._serie_para`, `pc.refrescar_payload(payload, ahora, h1, digits, cierres)`.
- Produces:
  - `LecturaFallidaError(RuntimeError)`
  - `leer_terminal(ticker: str, ahora: datetime) -> dict` (el `lectura` de la Tarea 6)
  - `preparar(momento, ahora=None, *, lector=None, lector_agenda=None, visiones=None, historial_ruta=None, dir_base=None) -> Path | None`
  - `REFRESCOS: dict[str, Callable[[dict, dict, datetime], tuple[dict, str | None]] | None]`
  - `refrescar_tanda(dir_canal, ahora=None, lector=None, reescribir=False) -> list[str]`
  - `completar_vision(dir_canal, vid, ahora=None, visiones=None, historial_ruta=None) -> None`
  - `main(argv) -> int` con `--preparar --momento`, `--refrescar DIR [--reescribir]`, `--rendir DIR`, `--validar DIR`, `--completar-vision DIR ID`

Códigos: 0 = tanda preparada, tanda con `_falta_vision`, tanda ya existente o "hoy no corresponde"; 1 = falla de datos (`LecturaFallidaError`, calendario caído); 2 = uso incorrecto.

- [ ] **Step 1: Write the failing tests**

```python
def _preparar(tmp_path, momento="avisos_manana", ahora=AHORA, visiones=None, lector=None, agenda=None):
    hist = tmp_path / "hist.json"
    if not hist.exists():
        hist.write_text("[]", encoding="utf-8")
    return pa.preparar(
        momento, ahora,
        lector=lector or (lambda t, a: lectura_falsa(t)),
        lector_agenda=lambda a: (agenda or AGENDA, []),
        visiones=visiones if visiones is not None else {"v": vision("v")},
        historial_ruta=hist, dir_base=tmp_path / "carrusel",
    ), hist


def test_feriado_no_prepara_nada(tmp_path):
    feriado = datetime(2026, 11, 26, 10, 30, tzinfo=pa.SANTIAGO)
    ruta, hist = _preparar(tmp_path, ahora=feriado)
    assert ruta is None and json.loads(hist.read_text(encoding="utf-8")) == []


def test_preparar_escribe_la_tanda_y_anota_el_historial(tmp_path):
    ruta, hist = _preparar(tmp_path)
    assert ruta.name == pa.CANAL and ruta.parent.name.endswith("_avisos_avisos_manana")
    assert (ruta / "_avisos.json").exists() and (ruta / "2_voz.json").exists()
    tipos = [e["tipo"] for e in json.loads(hist.read_text(encoding="utf-8"))]
    assert tipos == ["vision", "avisos"]


def test_preparar_dos_veces_el_mismo_momento_no_duplica(tmp_path):
    primera, hist = _preparar(tmp_path)
    antes = hist.read_text(encoding="utf-8")
    segunda, _ = _preparar(tmp_path, ahora=AHORA + timedelta(minutes=10))
    assert segunda == primera
    assert hist.read_text(encoding="utf-8") == antes


def test_sin_vision_la_tanda_sale_marcada(tmp_path):
    ruta, _ = _preparar(tmp_path, visiones={})
    assert pa.leer_meta(ruta)["_falta_vision"] is True
    assert not (ruta / "2_voz.json").exists()


def test_una_falla_de_terminal_es_falla_de_datos(tmp_path):
    def roto(t, a):
        raise pa.LecturaFallidaError("MT5 no conectó")
    with pytest.raises(pa.LecturaFallidaError):
        _preparar(tmp_path, lector=roto)


def test_el_balance_retoma_el_activo_y_la_voz_de_la_manana_sin_gastarla(tmp_path):
    _preparar(tmp_path, momento="avisos_manana")
    tarde = datetime(2026, 9, 29, 15, 30, tzinfo=pa.SANTIAGO)
    ruta, hist = _preparar(tmp_path, momento="avisos_tarde", ahora=tarde)
    meta = pa.leer_meta(ruta)
    assert meta["formato"] == "balance" and meta["activo"] == "USDCLP" and meta["vision"] == "v"
    visiones_gastadas = [e for e in json.loads(hist.read_text(encoding="utf-8")) if e["tipo"] == "vision"]
    assert len(visiones_gastadas) == 1


def test_la_agenda_del_lunes_no_lee_el_terminal(tmp_path):
    def no_llamar(t, a):
        raise AssertionError("la agenda no tiene activo")
    lunes = datetime(2026, 9, 28, 15, 30, tzinfo=pa.SANTIAGO)
    ruta, _ = _preparar(tmp_path, momento="avisos_tarde", ahora=lunes, lector=no_llamar)
    assert [s for s, _ in pa.leer_laminas(ruta)] == ["1_portada", "2_semana", "3_lectura"]


def test_completar_vision_arma_la_voz_sin_cambiar_el_activo(tmp_path):
    ruta, hist = _preparar(tmp_path, visiones={})
    visiones = {"n": vision("n", fecha="2026-09-27")}
    pa.completar_vision(ruta, "n", AHORA, visiones=visiones, historial_ruta=hist)
    meta = pa.leer_meta(ruta)
    assert meta["activo"] == "USDCLP" and meta["vision"] == "n" and meta["_falta_vision"] is False
    assert [s for s, _ in pa.leer_laminas(ruta)] == ["1_portada", "2_voz", "3_datos", "4_lectura"]
    assert any(e["tipo"] == "vision" and e["clave"] == "n" for e in json.loads(hist.read_text(encoding="utf-8")))


def test_completar_vision_de_otro_activo_se_niega(tmp_path):
    ruta, hist = _preparar(tmp_path, visiones={})
    with pytest.raises(SystemExit, match="activo"):
        pa.completar_vision(ruta, "x", AHORA, visiones={"x": vision("x", activo="XAUUSD")}, historial_ruta=hist)


def test_refrescar_conserva_texto_y_vision_y_mueve_la_hora(tmp_path):
    ruta, _ = _preparar(tmp_path)
    _escribir_todo(ruta)
    despues = AHORA + timedelta(minutes=40)
    pa.refrescar_tanda(ruta, despues, lector=lambda t, a: lectura_falsa(t, precio=936.80))
    meta = pa.leer_meta(ruta)
    laminas = dict(pa.leer_laminas(ruta))
    assert meta["leido_en"].startswith("2026-09-29T12:10") and meta["vision"] == "v"
    assert laminas["1_portada"]["pie"].startswith("El dólar mantiene")
    assert laminas["1_portada"]["dato_precio"].endswith("936,80")
    assert laminas["3_datos"]["precio_actual"] == "936,80"


def test_refrescar_con_divergencia_no_escribe_sin_reescribir(tmp_path):
    ruta, _ = _preparar(tmp_path)
    _escribir_todo(ruta)
    antes = (ruta / "3_datos.json").read_text(encoding="utf-8")
    with pytest.raises(SystemExit, match="reescribir"):
        pa.refrescar_tanda(ruta, AHORA, lector=lambda t, a: lectura_falsa(t, precio=945.0))
    assert (ruta / "3_datos.json").read_text(encoding="utf-8") == antes


def test_la_tabla_de_refresco_cubre_toda_plantilla_que_se_escribe():
    assert set(pa.REFRESCOS) == set(pa.PLANTILLAS)
    assert pa.REFRESCOS["avisos_lectura"] is None and pa.REFRESCOS["avisos_agenda"] is None


def test_pipeline_avisos_usa_los_tres_frenos_compartidos():
    import inspect
    fuente = inspect.getsource(pa.validar_tanda)
    for freno in ("validar_textos", "validar_cifras", "validar_frescura"):
        assert f"pl.{freno}" in fuente
    assert "exigir_texto_editorial" in inspect.getsource(pa.rendir_tanda)
```

(En `test_refrescar_con_divergencia…`, 945,0 cruza la resistencia de la preparación, 939,32, y `divergencia_editorial` lo detecta.)

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_pipeline_avisos.py -v`
Expected: FAIL con `AttributeError: … 'preparar'`.

- [ ] **Step 3: Implement** (append)

```python
# ---------------------------------------------------------------- terminal


class LecturaFallidaError(RuntimeError):
    """El terminal no entregó el activo: falla de datos, el momento queda pendiente."""


def leer_terminal(ticker: str, ahora: datetime) -> dict[str, Any]:
    """Una lectura del activo, con la misma vara que el escáner (cobertura fija)."""
    import screener_gi as sc
    from market_data_mcp import mt5_client
    from market_data_mcp.analisis import analizar_activo

    try:
        mt5_client.connect()
    except Exception as exc:  # noqa: BLE001
        raise LecturaFallidaError(f"MT5 no conectó ({exc.__class__.__name__})") from exc
    catalogo = pl._catalogo()
    if ticker not in catalogo:
        raise LecturaFallidaError(f"{ticker} no está en el catálogo")
    activo = catalogo[ticker]
    sel = sc.evaluar_activo(activo, [], None, ahora, fijo=True, ignorar_agotamiento=True)
    if "excluido" in sel:
        raise LecturaFallidaError(f"{ticker}: {sel['excluido']}")
    h1 = analizar_activo(ticker, "H1")
    if "error" in h1:
        raise LecturaFallidaError(f"{ticker}: {h1['error']}")
    try:
        cierres = pc._serie_para(ticker)
    except Exception as exc:  # noqa: BLE001
        raise LecturaFallidaError(f"{ticker}: sin serie ({exc})") from exc
    return {"ticker": ticker, "activo": activo, "seleccion": sel, "h1": h1, "cierres": cierres}


def _leer_agenda(ahora: datetime) -> tuple[list[dict[str, Any]], list[str]]:
    return pl.leer_agenda(ahora)


# ---------------------------------------------------------------- preparar


def _tanda_existente(dir_base: Path, fecha: date, momento: str) -> Path | None:
    for d in sorted(dir_base.glob(f"{fecha.isoformat()}_*_avisos_{momento}")):
        canal = d / CANAL
        if (canal / "_avisos.json").exists():
            return canal
    return None


def preparar(momento: str, ahora: datetime | None = None, *,
             lector: Callable[[str, datetime], dict[str, Any]] | None = None,
             lector_agenda: Callable[[datetime], tuple[list[dict[str, Any]], list[str]]] | None = None,
             visiones: dict[str, dict[str, Any]] | None = None,
             historial_ruta: Path | None = None, dir_base: Path | None = None) -> Path | None:
    """La tanda del momento, o `None` si hoy no corresponde.

    Una segunda corrida del mismo momento el mismo día devuelve la tanda que ya
    existe sin escribir nada: volver a elegir quemaría otra visión.
    """
    ahora = (ahora or datetime.now(SANTIAGO)).astimezone(SANTIAGO)
    hoy = ahora.date()
    formato = formato_del_momento(momento, hoy)
    if not es_dia_habil(hoy):
        return None
    dir_base = dir_base or pc.DIR_TRABAJO
    existente = _tanda_existente(dir_base, hoy, momento)
    if existente is not None:
        return existente

    lector = lector or leer_terminal
    visiones = visiones if visiones is not None else pl.cargar_visiones()
    historial = cargar_historial(historial_ruta)

    lectura: dict[str, Any] | None = None
    vision: dict[str, Any] | None = None
    agenda: list[dict[str, Any]] = []
    gastar_vision = True
    if formato == "agenda":
        agenda, avisos = (lector_agenda or _leer_agenda)(ahora)
        if avisos and not agenda:
            raise LecturaFallidaError("; ".join(avisos))
        activo = None
    else:
        if formato == "balance":
            activo, vid = activo_del_balance(historial, hoy)
            gastar_vision = False
            if activo is None:
                activo, vid = elegir("cita", hoy, {}, historial)
        else:
            activo, vid = elegir(formato, hoy, visiones, historial)
        vision = visiones.get(vid) if vid else None
        lectura = lector(activo, ahora)

    meta, laminas = armar_tanda(momento, formato, ahora, lectura, vision, agenda)
    dir_canal = dir_base / f"{ahora:%Y-%m-%d_%H-%M}_avisos_{momento}" / CANAL
    dir_canal.mkdir(parents=True, exist_ok=True)
    escribir_meta(dir_canal, meta)
    escribir_laminas(dir_canal, formato, laminas)
    registrar_uso(hoy, momento, activo, meta["vision"], gastar_vision=gastar_vision, ruta=historial_ruta)
    return dir_canal


# ---------------------------------------------------------------- refrescar


def refrescar_portada(payload: dict[str, Any], lectura: dict[str, Any], ahora: datetime) -> tuple[dict[str, Any], str | None]:
    nuevo = json.loads(json.dumps(payload))
    precio = _fmt(lectura["h1"]["price"], lectura["activo"]["digits"])
    nuevo["dato_precio"] = f"{lectura['activo']['nombre']} {precio}"
    nuevo["dato_hora"] = f"LEÍDO {etiqueta_hora(ahora)}"
    nuevo["fecha_hora"] = fecha_hora(ahora)
    return nuevo, None


def refrescar_voz(payload: dict[str, Any], lectura: dict[str, Any], ahora: datetime) -> tuple[dict[str, Any], str | None]:
    nuevo = json.loads(json.dumps(payload))
    for bloque in nuevo.get("bloque_meta", []):
        bloque["precio_hoy"] = _fmt(lectura["h1"]["price"], lectura["activo"]["digits"])
        bloque["hora_precio"] = etiqueta_hora(ahora)
    nuevo["fecha_hora"] = fecha_hora(ahora)
    return nuevo, None


def refrescar_datos(payload: dict[str, Any], lectura: dict[str, Any], ahora: datetime) -> tuple[dict[str, Any], str | None]:
    return pc.refrescar_payload(payload, ahora=ahora, h1=lectura["h1"],
                                digits=lectura["activo"]["digits"], cierres=lectura["cierres"])


# Toda `_plantilla` que este script escribe tiene entrada. `None` es una
# decisión explícita (la lámina no lleva precio), no una ausencia: así ninguna
# lámina cae en el camino "se despacha tal cual" sin que alguien lo haya decidido.
REFRESCOS: dict[str, Callable[[dict[str, Any], dict[str, Any], datetime], tuple[dict[str, Any], str | None]] | None] = {
    "avisos_portada": refrescar_portada,
    "vision": refrescar_voz,
    "avisos_datos": refrescar_datos,
    "avisos_agenda": None,
    "avisos_lectura": None,
}


def _aplicar_refresco(dir_canal: Path, lectura: dict[str, Any], ahora: datetime) -> tuple[dict[str, dict[str, Any]], list[str]]:
    """Las láminas refrescadas en memoria y los motivos de divergencia. No escribe."""
    nuevas: dict[str, dict[str, Any]] = {}
    motivos: list[str] = []
    for stem, payload in leer_laminas(dir_canal):
        funcion = REFRESCOS[payload["_plantilla"]]
        if funcion is None:
            continue
        nuevo, motivo = funcion(payload, lectura, ahora)
        if motivo:
            motivos.append(f"{stem}: {motivo}")
        nuevas[stem] = nuevo
    return nuevas, motivos


def _guardar_refresco(dir_canal: Path, meta: dict[str, Any], nuevas: dict[str, dict[str, Any]],
                      lectura: dict[str, Any], ahora: datetime) -> None:
    for stem, payload in nuevas.items():
        (dir_canal / f"{stem}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    datos = next(p for p in nuevas.values() if p["_plantilla"] == "avisos_datos")
    meta["activos"] = {lectura["ticker"]: fila_medida(lectura, datos)}
    meta["leido_en"] = ahora.isoformat(timespec="minutes")
    meta["direccion"] = datos.get("sesgo", meta.get("direccion"))
    escribir_meta(dir_canal, meta)


def refrescar_tanda(dir_canal: Path, ahora: datetime | None = None,
                    lector: Callable[[str, datetime], dict[str, Any]] | None = None,
                    reescribir: bool = False) -> list[str]:
    """Relee el terminal para el mismo activo. Conserva la visión y todo el texto.

    Si el precio cruzó un nivel o la lectura dio vuelta, el texto quedó escrito
    para otro mercado: sin `reescribir` no se toca nada; con `reescribir` se
    guardan los datos nuevos y los textos vuelven a `[[ESCRIBIR]]`.
    """
    ahora = (ahora or datetime.now(SANTIAGO)).astimezone(SANTIAGO)
    meta = leer_meta(dir_canal)
    if not meta.get("activo"):
        meta["leido_en"] = ahora.isoformat(timespec="minutes")
        escribir_meta(dir_canal, meta)
        return ["agenda: sin precio que refrescar, se renovó la hora de lectura"]
    lectura = (lector or leer_terminal)(meta["activo"], ahora)
    nuevas, motivos = _aplicar_refresco(dir_canal, lectura, ahora)
    if motivos and not reescribir:
        raise SystemExit(
            "El mercado invalidó el texto:\n  " + "\n  ".join(motivos)
            + "\nCorre --refrescar con --reescribir y vuelve a escribir las láminas."
        )
    _guardar_refresco(dir_canal, meta, nuevas, lectura, ahora)
    if motivos:
        for stem, payload in leer_laminas(dir_canal):
            for campo in _CAMPOS_TEXTO:
                if campo in payload:
                    payload[campo] = MARCA
            (dir_canal / f"{stem}.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return motivos + ["textos vueltos a [[ESCRIBIR]]"]
    return [f"refrescado a las {etiqueta_hora(ahora)}"]


# ---------------------------------------------------------------- completar visión


def completar_vision(dir_canal: Path, vid: str, ahora: datetime | None = None,
                     visiones: dict[str, dict[str, Any]] | None = None,
                     historial_ruta: Path | None = None) -> None:
    """Arma la lámina de la voz en una tanda que salió sin visión. No cambia el activo."""
    ahora = (ahora or datetime.now(SANTIAGO)).astimezone(SANTIAGO)
    meta = leer_meta(dir_canal)
    if not meta.get("_falta_vision"):
        raise SystemExit("La tanda ya tiene visión o no la necesita (agenda).")
    visiones = visiones if visiones is not None else pl.cargar_visiones()
    vision = visiones.get(vid)
    if vision is None:
        raise SystemExit(f"`{vid}` no está en el registro {pl.REGISTRO_VISIONES.name}.")
    if vision.get("activo") != meta["activo"]:
        raise SystemExit(f"La visión `{vid}` es de {vision.get('activo')} y el activo de la tanda es {meta['activo']}.")
    variante = meta["formato"] if meta["formato"] in ("cita", "meta") else variante_de(vision)
    if not vision_califica(vision, variante, ahora.date(), cargar_historial(historial_ruta)):
        raise SystemExit(
            f"La visión `{vid}` no sirve para la variante {variante}: revisa fecha (máximo "
            f"{pl.ANTIGUEDAD_MAX_DIAS} días), uso en Avisos (14 días) y, si es meta, `meta` y `horizonte`."
        )
    laminas = {p["_clave"]: p for _, p in leer_laminas(dir_canal)}
    fila = meta["activos"][meta["activo"]]
    leido = datetime.fromisoformat(meta["leido_en"])
    laminas["voz"] = lamina_voz(vision, variante, fila, leido, ahora)
    ordenadas = {c: laminas[c] for c in SECUENCIAS[meta["formato"]] if c in laminas}
    escribir_laminas(dir_canal, meta["formato"], ordenadas)
    meta.update(vision=vid, vision_variante=variante, _falta_vision=False)
    escribir_meta(dir_canal, meta)
    registrar_uso(ahora.date(), meta["momento"], None, vid, gastar_vision=True, ruta=historial_ruta)


# ---------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Carruseles de Avisos: la voz de los bancos contra nuestros datos")
    modo = parser.add_mutually_exclusive_group(required=True)
    modo.add_argument("--preparar", action="store_true", help="prepara la tanda del momento (--momento)")
    modo.add_argument("--refrescar", type=Path, metavar="DIR", help="relee el terminal y conserva el texto")
    modo.add_argument("--rendir", type=Path, metavar="DIR", help="aplica los frenos y rinde las láminas")
    modo.add_argument("--validar", type=Path, metavar="DIR", help="informa qué falta, sin escribir")
    modo.add_argument("--completar-vision", nargs=2, metavar=("DIR", "ID"), help="arma la voz con una visión nueva")
    parser.add_argument("--momento", choices=sorted(MOMENTOS))
    parser.add_argument("--reescribir", action="store_true", help="con --refrescar: acepta la divergencia y vacía los textos")
    args = parser.parse_args(argv)

    if args.preparar:
        if not args.momento:
            print("ERROR: --preparar necesita --momento", file=sys.stderr)
            return 2
        try:
            ruta = preparar(args.momento)
        except LecturaFallidaError as exc:
            print(f"FALLA DE DATOS: {exc}. El momento queda pendiente.", file=sys.stderr)
            return 1
        except SinCandidatosError as exc:
            print(f"Sin tanda: {exc} Es un resultado válido, no una falla.")
            return 0
        if ruta is None:
            print("Hoy no corresponde: no es día hábil en la bolsa de Nueva York.")
            return 0
        meta = leer_meta(ruta)
        print(f"Tanda: {ruta.parent}\nActivo: {meta['activo'] or 'agenda de la semana'} · formato {meta['formato']}")
        if meta["_falta_vision"]:
            print("_falta_vision: el comando busca una visión y corre --completar-vision.")
        return 0
    if args.refrescar:
        try:
            for linea in refrescar_tanda(args.refrescar, reescribir=args.reescribir):
                print(linea)
        except LecturaFallidaError as exc:
            print(f"FALLA DE DATOS: {exc}", file=sys.stderr)
            return 1
        return 0
    if args.rendir:
        for png in rendir_tanda(args.rendir):
            print(png)
        return 0
    if args.validar:
        errores = validar_tanda(args.validar, datetime.now(SANTIAGO), pl.cargar_visiones())
        print("Lista para rendir." if not errores else "\n".join(errores))
        return 0 if not errores else 1
    directorio, vid = args.completar_vision
    completar_vision(Path(directorio), vid)
    print(f"Voz armada con `{vid}`. Escribe su titular y su párrafo y corre --rendir.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests**

Run: `uv run pytest tests/test_pipeline_avisos.py tests/test_pipeline_linkedin.py tests/test_pipeline_carrusel.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/pipeline_avisos.py tests/test_pipeline_avisos.py
git commit -m "feat(avisos): preparar, refrescar, completar visión y CLI del pipeline"
```

---

### Task 9: Prueba real del Hito 1 y PR

Sin camino al cliente: nada de `--despachar`.

- [ ] **Step 1: Suite completa.** `uv run --extra stories pytest -q` → PASS. `uv run python scripts/marca_tokens.py --check` y `uv run python scripts/sincronizar_css_plantillas.py --check` → OK.
- [ ] **Step 2: Preparar contra el terminal** (MT5 abierto en la cuenta 51492), un momento por vez:

```bash
uv run --extra stories --with MetaTrader5 python scripts/pipeline_avisos.py --preparar --momento avisos_manana
uv run --extra stories --with MetaTrader5 python scripts/pipeline_avisos.py --preparar --momento avisos_mediodia
uv run --extra stories --with MetaTrader5 python scripts/pipeline_avisos.py --preparar --momento avisos_tarde
```

Ojo: esto **anota en `data/historial_suplementos.json`**. Al terminar la prueba, revierte ese archivo con `git checkout data/historial_suplementos.json` para no gastar visiones ni cobertura reales, y borra las tandas de prueba de `data/carrusel/`.

- [ ] **Step 3: Completar textos** en una tanda con la herramienta de edición (nunca por PowerShell), `--validar` hasta que diga "Lista para rendir.", y `--rendir`.
- [ ] **Step 4: Mirar cada PNG**: tildes, `¿`, `·`, emoji, nada cortado, el precio de la portada igual al de la alerta.
- [ ] **Step 5: PR** del Hito 1 contra la rama base del stack (o `master` si #241 ya se mergeó), con cuerpo que diga que no toca el camino al cliente y liste la prueba real. Cuerpo termina con `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.

---

# HITO 2: despacho, reloj y comando

Empieza con el Hito 1 mergeado.

### Task 10: `cupo_restante()` en el sender

**Files:**
- Modify: `src/whatsapp_sender.py` (clase `WhatsAppSender`, junto a `_esperar_turno`, línea ~588)
- Test: `tests/test_whatsapp_sender.py`

**Interfaces:**
- Produces: `WhatsAppSender.cupo_restante(self) -> int`

- [ ] **Step 1: Write the failing test**

```python
def test_cupo_restante_lee_el_contador_sin_tocarlo(tmp_path, monkeypatch):
    import json as _json
    from datetime import date as _date
    import whatsapp_sender as ws

    estado = tmp_path / "envios.json"
    estado.write_text(_json.dumps({"fecha": _date.today().isoformat(), "enviados": 37, "ultimo_ts": 0.0}), encoding="utf-8")
    monkeypatch.setattr(ws, "ESTADO_ENVIOS_PATH", estado)
    sender = WhatsAppSender()
    antes = estado.read_text(encoding="utf-8")
    assert sender.cupo_restante() == sender.max_envios_dia - 37
    assert estado.read_text(encoding="utf-8") == antes


def test_cupo_restante_nunca_es_negativo(tmp_path, monkeypatch):
    import json as _json
    from datetime import date as _date
    import whatsapp_sender as ws

    estado = tmp_path / "envios.json"
    estado.write_text(_json.dumps({"fecha": _date.today().isoformat(), "enviados": 99, "ultimo_ts": 0.0}), encoding="utf-8")
    monkeypatch.setattr(ws, "ESTADO_ENVIOS_PATH", estado)
    assert WhatsAppSender().cupo_restante() == 0
```

- [ ] **Step 2: Run** `uv run pytest tests/test_whatsapp_sender.py -k cupo_restante -v` → FAIL (`AttributeError`).
- [ ] **Step 3: Implement** (método de `WhatsAppSender`, antes de `_esperar_turno`)

```python
    def cupo_restante(self) -> int:
        """Mensajes que todavía caben hoy. Solo lectura: no reserva ni espera.

        Lee el mismo contador que `_esperar_turno`, para que el despacho pueda
        decidir antes de empezar un carrusel si lo alcanza a mandar entero. El
        freno por acción de `_esperar_turno` sigue intacto: este se suma.
        """
        estado = self._leer_estado_envios()
        return max(self.max_envios_dia - estado["enviados"], 0)
```

- [ ] **Step 4: Run** `uv run pytest tests/test_whatsapp_sender.py -v` → PASS.
- [ ] **Step 5: Commit** `git add src/whatsapp_sender.py tests/test_whatsapp_sender.py && git commit -m "feat(sender): cupo_restante de solo lectura"`

---

### Task 11: El despacho delega las tandas de Avisos y frena por canal

**Files:**
- Modify: `scripts/pipeline_carrusel.py` (`_refrescar_y_rendir` línea ~1355, `despachar` línea ~1457; nueva clase `CanalDetenidoError` junto a `PiezaSinMensajeError`)
- Modify: `scripts/pipeline_avisos.py` (append `refrescar_para_despacho`, `detener_canal`)
- Test: `tests/test_pipeline_avisos.py`, `tests/test_pipeline_carrusel.py`

**Interfaces:**
- Consumes: `pa.REFRESCOS`, `pa._aplicar_refresco`, `pa._guardar_refresco`, `pa.validar_tanda`, `pa.rendir_tanda`, `pa.leer_meta`, `WhatsAppSender.cupo_restante()`.
- Produces:
  - `pc.CanalDetenidoError(RuntimeError)`
  - `pa.detener_canal(dir_canal: Path, motivo: str) -> NoReturn` (renombra `N_*.json`/`N_*.png` a `.divergente` y lanza)
  - `pa.refrescar_para_despacho(dir_canal, sin_mt5: bool, ahora=None, lector=None, visiones=None, render=None) -> list[str]`

Reglas (spec §3.7): una pieza sin `_plantilla` (o con `"alerta"`) en un canal sin `_avisos.json` sigue exactamente el camino de hoy; una `_plantilla` desconocida sin `_avisos.json` detiene el despacho; una divergencia, una cifra que dejó de coincidir, o un refresco fallido con lectura de más de 2 h detienen **el canal entero**; el cupo se verifica para todas las láminas pendientes antes del primer envío.

**Decisión a revisar:** al despachar, `validar_cifras` acepta además los niveles de la preparación (`activos_preparacion` sin `price`). Si no, cualquier tick detendría un carrusel cuyo texto cita el soporte de la preparación, y el cruce de niveles ya lo vigila `divergencia_editorial`. El precio spot de la preparación **no** se acepta: un texto que cita el spot se frena si el precio se movió. El comando lo advierte (Tarea 13): el spot va dibujado, no escrito.

- [ ] **Step 1: Write the failing tests** (`tests/test_pipeline_avisos.py`)

```python
def _tanda_escrita(tmp_path):
    ruta, _ = _preparar(tmp_path)
    _escribir_todo(ruta)
    return ruta


def _render_falso(tokens, plantilla, salida, formato="horizontal"):
    salida.write_bytes(b"png")
    return salida


def test_despacho_refresca_una_vez_y_rinde_todo(tmp_path):
    ruta = _tanda_escrita(tmp_path)
    lecturas = []

    def lector(t, a):
        lecturas.append(t)
        return lectura_falsa(t, precio=936.50)

    avisos = pa.refrescar_para_despacho(ruta, sin_mt5=False, ahora=AHORA + timedelta(minutes=5), lector=lector,
                                        visiones={"v": vision("v")}, render=_render_falso)
    assert lecturas == ["USDCLP"]
    assert len(list(ruta.glob("[0-9]_*.png"))) == 4
    assert any("refrescado" in a for a in avisos)


def test_una_divergencia_en_la_alerta_frena_las_cuatro(tmp_path):
    ruta = _tanda_escrita(tmp_path)
    with pytest.raises(pa.pc.CanalDetenidoError, match="3_datos"):
        pa.refrescar_para_despacho(ruta, sin_mt5=False, ahora=AHORA, lector=lambda t, a: lectura_falsa(t, precio=945.0),
                                   visiones={"v": vision("v")}, render=_render_falso)
    assert not list(ruta.glob("[0-9]_*.json"))
    assert len(list(ruta.glob("*.json.divergente"))) == 4


def test_refresco_fallido_con_lectura_vieja_frena_el_canal(tmp_path):
    ruta = _tanda_escrita(tmp_path)

    def roto(t, a):
        raise pa.LecturaFallidaError("MT5 no conectó")

    with pytest.raises(pa.pc.CanalDetenidoError, match="2 h"):
        pa.refrescar_para_despacho(ruta, sin_mt5=False, ahora=AHORA + timedelta(hours=3), lector=roto,
                                   visiones={"v": vision("v")}, render=_render_falso)


def test_refresco_fallido_con_lectura_reciente_sale_y_lo_dice(tmp_path):
    ruta = _tanda_escrita(tmp_path)

    def roto(t, a):
        raise pa.LecturaFallidaError("MT5 no conectó")

    avisos = pa.refrescar_para_despacho(ruta, sin_mt5=False, ahora=AHORA + timedelta(minutes=30), lector=roto,
                                        visiones={"v": vision("v")}, render=_render_falso)
    assert any("hace 30 min" in a for a in avisos)


def test_sin_metatrader5_se_trata_como_refresco_fallido(tmp_path):
    ruta = _tanda_escrita(tmp_path)
    with pytest.raises(pa.pc.CanalDetenidoError):
        pa.refrescar_para_despacho(ruta, sin_mt5=True, ahora=AHORA + timedelta(hours=3),
                                   visiones={"v": vision("v")}, render=_render_falso)
```

Y en `tests/test_pipeline_carrusel.py`:

```python
def test_una_plantilla_desconocida_sin_tanda_de_avisos_detiene_el_despacho(tmp_path):
    payload = payload_de_prueba()
    payload.update({"titular": "Titular de prueba largo", "parrafo": "Párrafo de prueba suficientemente largo.",
                    "_plantilla": "portada_inventada"})
    (tmp_path / "1_x.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(SystemExit, match="portada_inventada"):
        pc._refrescar_y_rendir(tmp_path)


def test_el_cupo_que_no_alcanza_no_envia_ninguna_lamina(tmp_path, monkeypatch):
    canal = tmp_path / "01_macro_y_apertura"
    canal.mkdir()
    (canal / "_avisos.json").write_text("{}", encoding="utf-8")
    for i in range(1, 4):
        (canal / f"{i}_l.png").write_bytes(b"png")
        (canal / f"{i}_l_mensaje.txt").write_text(f"{i}/3 · x", encoding="utf-8")
    enviados = []

    class MockSender:
        def __init__(self, headless=True):
            self.config = type("C", (), {"destino_de_pruebas": "GI · Banco de Pruebas"})()

        def cupo_restante(self):
            return 2

        def enviar_lote(self, *a, **k):
            enviados.append(a)
            return {}

    monkeypatch.setattr("whatsapp_sender.WhatsAppSender", MockSender)
    monkeypatch.setattr(pc, "_refrescar_y_rendir", lambda _d: [])
    monkeypatch.setattr("bitacora_despachos.cargar", lambda *a, **k: [])
    res = pc.despachar(tmp_path)
    assert enviados == []
    assert res["grupos"][0]["status"] == "sin_cupo"


def test_un_canal_detenido_no_envia_y_sigue_con_los_demas(tmp_path, monkeypatch):
    canal = tmp_path / "01_macro_y_apertura"
    canal.mkdir()

    class MockSender:
        def __init__(self, headless=True):
            self.config = type("C", (), {"destino_de_pruebas": "x"})()

        def enviar_lote(self, *a, **k):
            raise AssertionError("no debía enviar")

    def detener(_d):
        raise pc.CanalDetenidoError("3_datos: el precio quebró la resistencia")

    monkeypatch.setattr("whatsapp_sender.WhatsAppSender", MockSender)
    monkeypatch.setattr(pc, "_refrescar_y_rendir", detener)
    res = pc.despachar(tmp_path)
    assert res["grupos"][0]["status"] == "detenido"
```

- [ ] **Step 2: Run** `uv run pytest tests/test_pipeline_avisos.py tests/test_pipeline_carrusel.py -v` → FAIL.
- [ ] **Step 3: Implement en `pipeline_carrusel.py`.**

Junto a `PiezaSinMensajeError`:

```python
class CanalDetenidoError(RuntimeError):
    """El carrusel de un canal no sale entero, así que no sale ninguna lámina.

    Lo lanza el refresco de una tanda de Avisos: la portada y la lectura citan el
    mismo precio que la alerta, y una lámina que cae arrastra a las demás.
    """
```

En `_refrescar_y_rendir`, justo después de la llamada a `exigir_texto_editorial([...])` y **antes** de `if falta_metatrader5():`:

```python
    # Una tanda de Avisos se refresca entera con una sola lectura del terminal y
    # se juzga por canal. `pipeline_avisos` se importa acá y no arriba: él
    # importa este módulo, y arriba sería una importación circular.
    if (dir_grupo / "_avisos.json").exists():
        import pipeline_avisos as pa

        return pa.refrescar_para_despacho(dir_grupo, sin_mt5=falta_metatrader5())

    # Fuera de Avisos solo existe la alerta temática. Una `_plantilla` que nadie
    # declaró caería en el camino de la alerta y saldría dibujada como tal.
    desconocidas = sorted({
        str(json.loads(p.read_text(encoding="utf-8")).get("_plantilla"))
        for p in piezas
        if json.loads(p.read_text(encoding="utf-8")).get("_plantilla") not in (None, "alerta")
    })
    if desconocidas:
        raise SystemExit(
            f"Piezas con plantilla sin refresco declarado: {', '.join(desconocidas)}. "
            "Solo una tanda de Avisos (con `_avisos.json`) sabe refrescarlas."
        )
```

En `despachar`, reemplazar:

```python
        for aviso in _refrescar_y_rendir(dir_grupo):
            print(f"    {aviso}", flush=True)
```

por:

```python
        try:
            avisos_refresco = _refrescar_y_rendir(dir_grupo)
        except CanalDetenidoError as exc:
            print(f"    ⚠️ el carrusel de {canal} NO sale, ninguna lámina: {exc}", flush=True)
            resultados.append({"grupo": canal, "status": "detenido", "motivo": str(exc)})
            continue
        for aviso in avisos_refresco:
            print(f"    {aviso}", flush=True)
```

Y después del bloque que imprime `"… pieza(s) ya despachada(s): se retoma en la que falta"` (antes de `def anotar`):

```python
        # Un carrusel a medias es peor que ninguno: si el cupo del día no alcanza
        # para todas sus láminas pendientes, no sale ninguna. El freno por acción
        # del sender sigue corriendo igual dentro de `enviar_lote`.
        if (dir_grupo / "_avisos.json").exists() and not dry_run:
            cupo = sender.cupo_restante()
            if len(pendientes) > cupo:
                print(
                    f"    el carrusel necesita {len(pendientes)} envíos y el cupo de hoy deja {cupo}: "
                    "no sale ninguna lámina", flush=True,
                )
                resultados.append({"grupo": canal, "status": "sin_cupo",
                                   "piezas": len(pendientes), "cupo": cupo})
                continue
```

- [ ] **Step 4: Implement en `pipeline_avisos.py`** (append)

```python
# ---------------------------------------------------------------- despacho


def detener_canal(dir_canal: Path, motivo: str):
    """Ninguna lámina sale: se renombran todas a `.divergente` y se detiene el canal."""
    for archivo in _archivos_de_lamina(dir_canal):
        if archivo.suffix in (".json", ".png"):
            archivo.rename(archivo.with_name(archivo.name + ".divergente"))
    raise pc.CanalDetenidoError(motivo)


def refrescar_para_despacho(dir_canal: Path, sin_mt5: bool, ahora: datetime | None = None,
                            lector: Callable[[str, datetime], dict[str, Any]] | None = None,
                            visiones: dict[str, dict[str, Any]] | None = None,
                            render: Callable[..., Path] | None = None) -> list[str]:
    """El refresco del despacho para una tanda de Avisos: una lectura, juicio por canal."""
    ahora = (ahora or datetime.now(SANTIAGO)).astimezone(SANTIAGO)
    visiones = visiones if visiones is not None else pl.cargar_visiones()
    meta = leer_meta(dir_canal)
    avisos: list[str] = []
    con_precio = any(REFRESCOS[p["_plantilla"]] for _, p in leer_laminas(dir_canal))
    if meta.get("activo") and con_precio:
        try:
            if sin_mt5:
                raise LecturaFallidaError("MetaTrader5 no está instalado en este entorno")
            lectura = (lector or leer_terminal)(meta["activo"], ahora)
        except Exception as exc:  # noqa: BLE001
            leido = datetime.fromisoformat(meta["leido_en"])
            leido = leido if leido.tzinfo else leido.replace(tzinfo=SANTIAGO)
            minutos = int((ahora - leido).total_seconds() // 60)
            if minutos > FRESCURA_MAX_HORAS * 60:
                detener_canal(dir_canal, f"no se pudo refrescar ({exc}) y la lectura tiene {minutos} min, "
                                         f"más de {FRESCURA_MAX_HORAS} h")
            avisos.append(f"no se pudo refrescar ({exc}): sale con la lectura de hace {minutos} min, "
                          f"dentro de las {FRESCURA_MAX_HORAS} h")
        else:
            nuevas, motivos = _aplicar_refresco(dir_canal, lectura, ahora)
            if motivos:
                detener_canal(dir_canal, "; ".join(motivos))
            _guardar_refresco(dir_canal, meta, nuevas, lectura, ahora)
            avisos.append(f"✅ carrusel de Avisos refrescado a las {etiqueta_hora(ahora)}")
    extra = {t: {k: v for k, v in fila.items() if k != "price"}
             for t, fila in leer_meta(dir_canal).get("activos_preparacion", {}).items()}
    errores = validar_tanda(dir_canal, ahora, visiones, activos_extra=extra)
    if errores:
        detener_canal(dir_canal, "; ".join(errores))
    rendir_tanda(dir_canal, ahora, visiones, render=render)
    return avisos
```

(`rendir_tanda` vuelve a correr `validar_tanda` sin `activos_extra`. Para que no frene lo que el despacho ya aceptó, agrega a `rendir_tanda` un parámetro `activos_extra: dict | None = None` que pasa a `validar_tanda`, y aquí llama `rendir_tanda(dir_canal, ahora, visiones, render=render, activos_extra=extra)`. Actualiza la firma en la sección Interfaces de la Tarea 7 al implementarlo.)

- [ ] **Step 5: Run** `uv run pytest tests/test_pipeline_avisos.py tests/test_pipeline_carrusel.py tests/test_whatsapp_sender.py -v` → PASS, incluidos **todos** los tests previos del carrusel temático (pieza a pieza, bitácora, modo pruebas, contexto macro sin editorial, guardia antes de leer el mercado).
- [ ] **Step 6: Commit** `git add scripts/pipeline_carrusel.py scripts/pipeline_avisos.py tests/ && git commit -m "feat(despacho): tandas de Avisos por plantilla, cupo y divergencia por canal"`

---

### Task 12: Los tres momentos en el reloj

**Files:**
- Modify: `config/agenda_mercado.json` (`momentos`)
- Modify: `scripts/reloj_gi.py` (`canales_del_momento` línea 166, `_correr_preparar` línea 286, `ejecutar` línea 301)
- Test: `tests/test_reloj_gi.py`, `tests/test_agenda_mercado.py`

**Interfaces:**
- Consumes: `pipeline_carrusel.resolver_grupo_solicitado(alias)`, `agenda_mercado.momento(slug)`.
- Produces: `reloj_gi.PIEZAS: dict[str, dict[str, str]]`; `_correr_preparar(canal: str, momento: dict | None = None) -> dict`.

- [ ] **Step 1: Write the failing tests** (`tests/test_reloj_gi.py`)

```python
def test_los_momentos_de_avisos_van_al_grupo_de_avisos():
    for slug in ("avisos_manana", "avisos_mediodia", "avisos_tarde"):
        assert reloj.canales_del_momento(ag.momento(slug)) == ["01_macro_y_apertura"]


def test_piezas_y_agenda_coinciden():
    for m in ag.momentos():
        if m.get("pieza"):
            assert m["pieza"] in reloj.PIEZAS, f"{m['slug']} declara una pieza que el reloj no conoce"
    for pieza, cfg in reloj.PIEZAS.items():
        assert (reloj.RAIZ / "scripts" / cfg["script"]).exists()


def test_un_momento_con_pieza_corre_su_script_con_el_momento(monkeypatch):
    llamadas = []

    class R:
        returncode, stdout, stderr = 0, "ok", ""

    monkeypatch.setattr(reloj.subprocess, "run", lambda cmd, **k: llamadas.append(cmd) or R())
    reloj._correr_preparar("01_macro_y_apertura", ag.momento("avisos_manana"))
    cmd = llamadas[0]
    assert cmd[1].endswith("pipeline_avisos.py") and cmd[2:] == ["--preparar", "--momento", "avisos_manana"]


def test_un_momento_sin_pieza_sigue_corriendo_el_carrusel(monkeypatch):
    llamadas = []

    class R:
        returncode, stdout, stderr = 0, "ok", ""

    monkeypatch.setattr(reloj.subprocess, "run", lambda cmd, **k: llamadas.append(cmd) or R())
    reloj._correr_preparar("02_forex_divisas")
    assert llamadas[0][1].endswith("pipeline_carrusel.py") and llamadas[0][2:] == ["--preparar", "--grupo", "02_forex_divisas"]


def test_ejecutar_le_pasa_el_momento_a_la_corrida(tmp_path, monkeypatch):
    vistos = []
    monkeypatch.setattr(reloj, "_correr_preparar",
                        lambda canal, momento=None: vistos.append((canal, (momento or {}).get("slug")))
                        or {"canal": canal, "codigo": 0, "salida": "", "error": ""})
    reloj.ejecutar(DESFASE_0.replace(hour=10, minute=32), ruta_libro=tmp_path / "libro.json")
    assert vistos == [("01_macro_y_apertura", "avisos_manana")]
```

- [ ] **Step 2: Run** `uv run pytest tests/test_reloj_gi.py tests/test_agenda_mercado.py -v` → FAIL (`ag.momento("avisos_manana")` no existe).
- [ ] **Step 3: Agenda.** Agregar al final de `momentos` en `config/agenda_mercado.json` (con la herramienta de edición; los nombres van acentuados porque salen en el aviso de cambio de horario):

```json
    {
      "slug": "avisos_manana",
      "nombre": "Carrusel de Avisos de la mañana",
      "hora": "10:30",
      "sesion": "apertura_ny",
      "clases": [],
      "pieza": "avisos",
      "formato": "cita",
      "por_que": "A las 10:30 la bolsa ya abrió y los índices tienen precio del día. Queda a 30 minutos del momento de índices, fuera de la tolerancia de 20, así que cada uno produce su tanda."
    },
    {
      "slug": "avisos_mediodia",
      "nombre": "Carrusel de Avisos del mediodía",
      "hora": "12:30",
      "sesion": "tarde_ny",
      "clases": [],
      "pieza": "avisos",
      "formato": "meta",
      "por_que": "A mitad de la jornada americana el precio ya recorrió buena parte del día: es el momento de contrastar la meta de un banco con lo que el mercado está haciendo."
    },
    {
      "slug": "avisos_tarde",
      "nombre": "Carrusel de Avisos de la tarde",
      "hora": "14:30",
      "sesion": "tarde_ny",
      "clases": [],
      "pieza": "avisos",
      "formato": "tarde",
      "por_que": "Va antes del cierre de la bolsa (16:00) y del informe de cierre (16:45). El lunes cuenta la agenda de la semana; de martes a viernes, el balance del activo de la mañana."
    }
```

Si `test_cada_momento_cae_dentro_de_la_sesion_que_declara` falla para `avisos_mediodia`, la frontera de `tarde_ny` (desde 12:30) se evalúa distinto de lo supuesto: pon la sesión que el test reporte, no muevas la hora.

- [ ] **Step 4: Reloj.** En `scripts/reloj_gi.py`, después de `DIAS_DE_LIBRO`:

```python
# Momentos que no son el carrusel por clase: una pieza propia con su script y
# su canal, resuelto por alias con el mismo índice que usa el despacho.
PIEZAS: dict[str, dict[str, str]] = {
    "avisos": {"script": "pipeline_avisos.py", "canal_alias": "avisos"},
}
```

`canales_del_momento`, al principio del cuerpo:

```python
    pieza = m.get("pieza")
    if pieza:
        # Un momento con pieza no tiene activos: su canal sale del mapeo real de
        # alias a grupo (extensión documentada del invariante 4).
        from pipeline_carrusel import resolver_grupo_solicitado

        return [resolver_grupo_solicitado(PIEZAS[pieza]["canal_alias"])]
```

`_correr_preparar` completo:

```python
def _correr_preparar(canal: str, momento: dict[str, Any] | None = None) -> dict[str, Any]:
    """Una corrida de preparación: la pieza del momento, o el carrusel del canal."""
    pieza = (momento or {}).get("pieza")
    if pieza:
        cmd = [
            sys.executable, str(RAIZ / "scripts" / PIEZAS[pieza]["script"]),
            "--preparar", "--momento", momento["slug"],
        ]
    else:
        cmd = [
            sys.executable, str(RAIZ / "scripts" / "pipeline_carrusel.py"),
            "--preparar", "--grupo", canal,
        ]
    r = subprocess.run(cmd, cwd=str(RAIZ), capture_output=True, text=True)
    return {
        "canal": canal,
        "codigo": r.returncode,
        "salida": (r.stdout or "")[-1500:],
        "error": (r.stderr or "")[-500:],
    }
```

En `ejecutar`, reemplazar `hacer = correr or _correr_preparar` por:

```python
    m = agenda.momento(est["momento"])
    hacer = correr or (lambda canal: _correr_preparar(canal, m))
```

- [ ] **Step 5: Run** `uv run pytest tests/test_reloj_gi.py tests/test_agenda_mercado.py -v` → PASS, incluidos `test_el_reloj_no_puede_enviar_nada_a_whatsapp`, `test_el_reloj_solo_prepara`, `test_ningun_par_de_momentos_se_pisa_en_ningun_desfase_del_ano`, `test_todo_momento_llega_a_algun_canal` y `test_los_nombres_de_momento_van_acentuados_porque_los_lee_el_cliente`. Verifica también `uv run python scripts/reloj_gi.py` (sin efectos) si su `main` tiene modo de consulta.
- [ ] **Step 6: Commit** `git add config/agenda_mercado.json scripts/reloj_gi.py tests/test_reloj_gi.py tests/test_agenda_mercado.py && git commit -m "feat(reloj): tres momentos de Avisos con pieza propia y canal por alias"`

---

### Task 13: Comando `/avisos`, exposición a AGY y documentación

**Files:**
- Create: `.claude/commands/avisos.md`
- Modify: `scripts/agy_workflows.py` (`COMANDOS`)
- Modify: `CLAUDE.md`
- Regenerate: `.agents/workflows/avisos.md`, `.agents/rules/proyecto.md`
- Test: el `--check` de ambos generadores y la suite

- [ ] **Step 1: Test del comando** (en `tests/test_pipeline_avisos.py`)

```python
def test_el_comando_documenta_solo_modos_que_existen():
    texto = (RAIZ / ".claude" / "commands" / "avisos.md").read_text(encoding="utf-8")
    for modo in ("--preparar", "--refrescar", "--rendir", "--validar", "--completar-vision"):
        assert modo in texto
    assert "pipeline_carrusel.py --despachar" in texto and "--with MetaTrader5" in texto
    assert "—" not in texto and "–" not in texto
```

Run: `uv run pytest tests/test_pipeline_avisos.py -k comando -v` → FAIL.

- [ ] **Step 2: Escribir `.claude/commands/avisos.md`**

```markdown
---
description: Carrusel de Avisos: la voz de un banco contra nuestros datos del terminal. Completa la visión si falta, escribe, rinde, muestra al director y despacha al aprobar.
---

# /avisos [momento]

Tres carruseles al día en el grupo de Avisos (`01_macro_y_apertura`): mañana
(cita del experto contra nuestro dato), mediodía (meta del banco contra el
precio) y tarde (agenda de la semana el lunes, balance de la mañana el resto).
El reloj los prepara a su hora; este comando los termina. Spec:
`docs/superpowers/specs/2026-09-28-carruseles-avisos-design.md`.

Todas las corridas van con `uv run --extra stories --with MetaTrader5 python scripts/pipeline_avisos.py`.

## 1. Localizar la tanda

Busca en `data/carrusel/` las carpetas de hoy `AAAA-MM-DD_HH-MM_avisos_<momento>/01_macro_y_apertura/`
que no figuren en `data/historial_despachos.json`. Si el director pide una fuera
de hora, corre `--preparar --momento avisos_manana|avisos_mediodia|avisos_tarde`.
Código 0 con "hoy no corresponde" es un resultado válido; código 1 es falla de
datos: abre MT5 y reintenta.

## 2. Si `_avisos.json` trae `_falta_vision: true`

1. Busca una visión reciente del activo (menos de 45 días) de un banco, corredora
   o analista con nombre. Búsqueda web, lectura de la nota, y Playwright solo si
   la fuente bloquea la lectura directa. **Nunca recorras LinkedIn.** Ante un muro
   de pago, usa solo lo que la fuente muestra abierto.
2. Regístrala en `data/visiones_expertos.json` después de ABRIR la fuente, nunca
   desde un snippet: `id`, `quien`, `institucion`, `activo` (ticker del catálogo),
   `tipo` (`textual`, `traduccion`, `parafrasis`), `cita`, `fecha` de publicación,
   `fuente`, `url`. Si es una meta (mediodía): `tipo: parafrasis`, `meta` con la
   cifra tal como figura en la cita, y `horizonte`.
3. `--completar-vision <DIR> <id>`. Si no encuentras ninguna, sigue sin la lámina:
   el carrusel sale en 3.

## 3. Escribir

Llena cada `[[ESCRIBIR]]` de los `N_*.json` con la herramienta de edición o con
Python (`Path.write_text(..., encoding="utf-8")`). **Nunca por PowerShell**: trunca
los `$` y rompe los acentos.

- Portada: `kicker`, `titular`, `parrafo` (la bajada), `claves` y `pie`. El `pie`
  es el mensaje de WhatsApp y **nombra la dirección** (alcista o bajista), salvo en
  la agenda. El cierre y el aviso legal los agrega el script: no los escribas.
- Voz: `titular` y `parrafo` (nuestro remate de la cita). La cita no se toca: sale del registro.
- Datos: `titular` y `parrafo` de la alerta, como en `/carrusel`.
- Lectura: `titular`, `puntos` y `parrafo` (la conclusión), con dirección clara.
- **No escribas el precio spot en el texto**: va dibujado en las láminas y se
  refresca al despachar. Si el texto lo cita y el precio se mueve, el carrusel no
  sale. Los niveles sí se pueden citar, con la cifra exacta del terminal.
- Una cifra que no sale del terminal ni de la cita se declara en
  `_avisos.json` → `cifras_citadas` con su motivo.
- Tuteo chileno, sin guion largo, siglas explicadas en línea.

## 4. Rendir y mirar

`--validar <DIR>` hasta "Lista para rendir.", después `--rendir <DIR>`. Abre cada
PNG y verifica `¿`, `¡`, `·`, tildes y emoji. Si la frescura venció (más de 2 h),
`--refrescar <DIR>`; si responde que el mercado invalidó el texto,
`--refrescar <DIR> --reescribir` y vuelve al paso 3.

## 5. Mostrar al director

Las láminas en orden y el pie de la portada completo. Espera su aprobación
explícita. **Nada sale sin ella.**

## 6. Despachar, solo al aprobar

`uv run --extra stories --with MetaTrader5 python scripts/pipeline_carrusel.py --despachar data/carrusel/<tanda>`

Sin `--with MetaTrader5` el refresco no corre y, con datos de más de 2 h, el
carrusel no sale. Si el cupo del día no alcanza para todas las láminas, no sale
ninguna: dilo al director. Si una lámina diverge, quedan todas `.divergente`.
```

- [ ] **Step 3: AGY.** En `scripts/agy_workflows.py`, agregar a `COMANDOS`:

```python
    "avisos": "Carrusel de Avisos: la voz de un banco contra nuestros datos del terminal, tres veces al día, con frenos de cifra, cita, frescura y cupo.",
```

- [ ] **Step 4: `CLAUDE.md`** (con la herramienta de edición):
  - En *El reloj de sucesos*, invariante 4, agregar al final: `Un momento con `pieza` (los tres de Avisos) no tiene activos: su canal se deriva del alias de la pieza en `reloj_gi.PIEZAS`, resuelto con `pipeline_carrusel.resolver_grupo_solicitado`, el mismo índice que usa el despacho.`
  - En la tabla de *Los momentos separan por clase de activo*, agregar las tres filas `avisos_manana` 10:30, `avisos_mediodia` 12:30, `avisos_tarde` 14:30, clases `—`, con su porqué corto.
  - En *El despacho*, un párrafo nuevo: `**Una tanda de Avisos se refresca y se juzga por canal.** Si el canal trae `_avisos.json`, `_refrescar_y_rendir` delega en `pipeline_avisos.refrescar_para_despacho`: una lectura del terminal, refresco por `_plantilla` según `pipeline_avisos.REFRESCOS` (`None` es una decisión explícita, no una ausencia), y una divergencia, una cifra que dejó de coincidir o un refresco fallido con datos de más de 2 h detienen el canal entero. Antes del primer envío se compara el cupo (`cupo_restante()`) con las láminas pendientes: un carrusel a medias es peor que ninguno. Una pieza sin `_plantilla` sigue exactamente el camino de antes.`
  - `## Slash Commands disponibles (7)` → `(8)`, y agregar la fila `| `/avisos [momento]` | Carrusel de Avisos: la voz de un banco contra nuestros datos, tres veces al día. Busca la visión si falta, escribe, rinde y despacha al aprobar. |`
  - En *Antigravity*, "Los siete comandos" → "Los ocho comandos" y agregar `/avisos` a la lista.
- [ ] **Step 5: Regenerar y verificar**

```bash
uv run python scripts/agy_reglas.py
uv run python scripts/agy_workflows.py
uv run python scripts/agy_workflows.py --check
uv run --extra stories pytest -q
```

Expected: todo PASS. Si algún test cuenta los comandos del `CLAUDE.md` o de `.claude/commands/`, ajústalo al nuevo total en vez de desactivarlo.

- [ ] **Step 6: Commit** `git add .claude/commands/avisos.md scripts/agy_workflows.py CLAUDE.md .agents/ tests/test_pipeline_avisos.py && git commit -m "feat(avisos): comando /avisos, expuesto a AGY, y documentación"`

---

### Task 14: Prueba real del Hito 2 y PR

- [ ] **Step 1:** `uv run --extra stories pytest -q` → PASS.
- [ ] **Step 2:** Preparar un momento contra el terminal, completar, escribir y rendir (Tarea 9, pasos 2 a 4).
- [ ] **Step 3: Despacho en seco:** `uv run --extra stories --with MetaTrader5 python scripts/pipeline_carrusel.py --despachar data/carrusel/<tanda> --dry-run`. Verifica en la salida: una sola lectura, "carrusel de Avisos refrescado", 3 o 4 piezas en orden, ningún envío real.
- [ ] **Step 4: Frenos en seco:** copia la tanda, edita a mano `leido_en` en `_avisos.json` a 3 horas atrás y corre el `--dry-run` con MT5 cerrado → "NO sale, ninguna lámina". Borra la copia.
- [ ] **Step 5:** Revertir `data/historial_suplementos.json` y borrar las tandas de prueba (Tarea 9, paso 2).
- [ ] **Step 6:** No instalar nada en el Programador de tareas: el latido `GI-Reloj` ya existe y toma los momentos nuevos del JSON. Confirmar con `uv run python scripts/reloj_gi.py` (consulta sin efectos) a una hora de momento, si su CLI lo permite.
- [ ] **Step 7: PR** del Hito 2, con la advertencia de que toca el único camino al cliente, los tres puntos de contención del spec §10 y la prueba en seco. El envío real queda para el director.
