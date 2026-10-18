I have launched the full test suite in the background to verify the baseline status of the repository. Let's wait for the results.
The test suite is running. I will wait for it to complete.
# Alerta semanal: cobertura de calendario parcial (Menor 10). Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Informar al ejecutivo cuando el calendario económico llegue incompleto (falla de una de las pestañas `thisWeek` o `nextWeek` habiendo datos en la otra). `leer_eventos` reporta la situación `"parcial"`, el `Agendador` la procesa como válida sin alarmar al director por calendario caído, y `armar_mapa` incluye una línea explícita indicando hasta qué día llega la cobertura.

**Architecture:** En `scripts/analista/avisos_semana.py`, `leer_eventos` usa `fallidas` de `agenda.ventana_cruda` para distinguir `"parcial"` (hay eventos y `fallidas > 0`) de `"ok"`. `Agendador.latido` trata `"parcial"` como entrega válida (no llama a `_calendario_caido`) y pasa `parcial=True` a `que_toca` y `_avisos_posibles`. `_avisos_posibles` calcula la fecha del último evento (`cubierto_hasta = max(fechas)`) y se la pasa a `semana.armar_mapa(eventos, ahora, cubierto_hasta=cubierto_hasta)`. `armar_mapa` agrega la advertencia antes del cuerpo. La víspera permanece inalterada.

**Tech Stack:** Python 3 (`scripts/analista/semana.py`, `scripts/analista/avisos_semana.py`), pytest vía `uv run`.

**Spec:** `docs/superpowers/specs/2026-10-18-alerta-semana-ejecutivos-design.md` (Menor 10).

## Global Constraints

- **TDD estricto:** cada cambio comienza con su test en rojo y verificación de fallo antes de implementar.
- **Sin WhatsApp:** ningún módulo en `scripts/analista/` puede importar `enviar_whatsapp`, `whatsapp_sender` ni herramientas de WhatsApp (regla de contrato verificada por test AST).
- **Texto para ejecutivos:** español de Chile, tuteo neutro, **sin guion largo (`—`) ni medio (`–`)**, sin términos de asesoría financiera (`compra`, `vende`, `oportunidad`, `cobertura`).
- **Hora y fechas:** siempre vía `zoneinfo.ZoneInfo("America/Santiago")`, sin offsets fijos.
- **Git:** nunca commitear a `master`; trabajar en `feat/alerta-semana-ejecutivos`; sin push. Cada commit termina con `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- **Suite verde:** `uv run pytest -q` debe pasar al 100% al cerrar la tarea.

## Review Focus

1. **Tupla de retorno de `leer_eventos`:** debe mantenerse estrictamente como tupla de 2 elementos `(situacion, eventos)` para preservar compatibilidad con tests y llamadores que inyectan funciones simuladas.
2. **Tratamiento en `Agendador`:** `"parcial"` no debe gatillar `_calendario_caido(ahora)` (el director no debe recibir alarma de calendario caído si hay eventos suficientes para armar el mapa).
3. **Invarianza de la víspera:** `parcial=True` solo altera el texto del `mapa`; la `vispera` no se modifica ni incluye la línea de advertencia.
4. **Formato de fecha:** `cubierto_hasta` formateado mediante `agenda.dia_corto` (`<dia_corto>`, ej: `miércoles 21/10`).

---

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `scripts/analista/semana.py` | `armar_mapa(..., cubierto_hasta=None)` añade la advertencia de calendario incompleto | Modificar |
| `scripts/analista/avisos_semana.py` | `leer_eventos` retorna `"parcial"`; `que_toca`, `_avisos_posibles` y `Agendador` propagan `parcial` | Modificar |
| `tests/test_analista_semana.py` | Test de `armar_mapa` con `cubierto_hasta` y verificación de reglas de texto editorial | Modificar |
| `tests/test_analista_avisos_semana.py` | Tests de `leer_eventos` ("parcial"), `que_toca(parcial=True)` y `Agendador` con "parcial" | Modificar |

---

### Task 1: Calendario parcial en mapa de la semana y agendador interno

**Files:**
- Modify: `scripts/analista/semana.py:19,168-183`
- Modify: `scripts/analista/avisos_semana.py:185-224,290-302`
- Test: `tests/test_analista_semana.py:144-149,176-187`
- Test: `tests/test_analista_avisos_semana.py:184-189`

**Interfaces:**
- Produces: `leer_eventos(ahora, cargar=None) -> tuple[str, list[dict[str, Any]]]`: devuelve `"parcial"` cuando `eventos` es no vacío y `fallidas > 0`.
- Produces: `que_toca(ahora, eventos, estado, ejecutivo, parcial: bool = False) -> list[Aviso]`.
- Produces: `_avisos_posibles(ahora, eventos, parcial: bool = False) -> list[Aviso]`.
- Produces: `armar_mapa(eventos, ahora, cubierto_hasta: datetime | date | str | None = None) -> str`.
- Consumes: `agenda.ventana_cruda`, `agenda._cuando`, `agenda.dia_corto`.

- [ ] **Step 1: Escribir los tests que fallan**

En `tests/test_analista_semana.py`, agrega el test de mapa incompleto después del test de semana tranquila (línea 149 aprox.):

```python
def test_mapa_con_calendario_incompleto_advierte_cobertura_parcial():
    texto = sm.armar_mapa([FOMC, CPI], LUNES, cubierto_hasta=datetime(2026, 10, 22, 9, 30, tzinfo=SCL))
    assert "Del lunes 19/10 al lunes 26/10." in texto
    assert "El calendario llegó incompleto: lo que ves llega hasta jueves 22/10; puede faltar algún dato posterior." in texto
```

Y en `tests/test_analista_semana.py`, actualiza la lista de textos en `test_ningun_texto_trae_guion_largo_ni_palabras_de_asesoria` para incluir la variante con `cubierto_hasta`:

```python
@pytest.mark.parametrize("texto", [
    sm.armar_mapa([FOMC, CPI, NFP, PMI, CRUDO], LUNES), sm.armar_mapa([], LUNES),
    sm.armar_mapa([FOMC, CPI], LUNES, cubierto_hasta=datetime(2026, 10, 22, 9, 30, tzinfo=SCL)),
    sm.armar_vispera(FOMC, datetime(2026, 10, 20, 16, 0, tzinfo=SCL)),
    sm.armar_vispera(CRUDO, datetime(2026, 10, 20, 16, 0, tzinfo=SCL)),
])
def test_ningun_texto_trae_guion_largo_ni_palabras_de_asesoria(texto):
```

En `tests/test_analista_avisos_semana.py`, agrega los tres tests para `leer_eventos`, `que_toca` y `Agendador` al final de la sección `# el agendador` (después de la línea 188 aprox.):

```python
def test_leer_eventos_distingue_ok_parcial_sin_calendario_y_vacia():
    def cargar_ok(solo_hoy=False, min_impact="low", ahora=None, pestanas=("thisWeek",)):
        return {"eventos": [CPI]}
    assert av.leer_eventos(LUNES_0745, cargar_ok) == ("ok", [CPI])

    def cargar_parcial(solo_hoy=False, min_impact="low", ahora=None, pestanas=("thisWeek",)):
        if "nextWeek" in pestanas:
            return {"error": "NO_CALENDAR_FEEDS"}
        return {"eventos": [CPI]}
    sit, evs = av.leer_eventos(LUNES_0745, cargar_parcial)
    assert sit == "parcial" and evs == [CPI]

    def cargar_caido(solo_hoy=False, min_impact="low", ahora=None, pestanas=("thisWeek",)):
        return {"error": "NO_CALENDAR_FEEDS"}
    assert av.leer_eventos(LUNES_0745, cargar_caido) == ("sin_calendario", [])

    def cargar_vacio(solo_hoy=False, min_impact="low", ahora=None, pestanas=("thisWeek",)):
        return {"eventos": []}
    assert av.leer_eventos(LUNES_0745, cargar_vacio) == ("vacia", [])


def test_que_toca_mapa_con_parcial_advierte_cobertura_y_vispera_no_cambia(estado):
    avisos_parcial = av.que_toca(LUNES_0745, [CPI], estado, "1", parcial=True)
    assert len(avisos_parcial) == 1
    assert "El calendario llegó incompleto: lo que ves llega hasta miércoles 21/10; puede faltar algún dato posterior." in avisos_parcial[0].texto

    avisos_normal = av.que_toca(LUNES_0745, [CPI], estado, "1", parcial=False)
    assert "El calendario llegó incompleto" not in avisos_normal[0].texto

    vispera = av.que_toca(MARTES_1600, [CPI], estado, "1", parcial=True)[0]
    assert "El calendario llegó incompleto" not in vispera.texto


def test_el_agendador_trata_parcial_como_ok_sin_alertar_al_director_y_agrega_advertencia(estado):
    envios, ahora = Envios(), [LUNES_0745]
    ag_ = agendador(estado, envios, ahora, lambda t: ("parcial", [CPI]))
    ag_.latido()
    assert [e for e in envios.enviados if e[1].startswith("director")] == []
    assert sorted(e for e in envios.enviados if e[1] == "mapa") == [("10", "mapa"), ("20", "mapa")]
```

- [ ] **Step 2: Correr y ver que fallan los tests**

Ejecuta:
```powershell
uv run pytest tests/test_analista_semana.py tests/test_analista_avisos_semana.py -k "parcial" -q
```
Resultado esperado: FAIL con errores:
- `TypeError: armar_mapa() got an unexpected keyword argument 'cubierto_hasta'`
- `assert ('ok', [CPI]) == ('parcial', [CPI])` en `test_leer_eventos_distingue_ok_parcial_sin_calendario_y_vacia`
- `TypeError: que_toca() got an unexpected keyword argument 'parcial'`

- [ ] **Step 3: Implementar la solución mínima**

1. En `scripts/analista/semana.py`, importa `date` en la línea 19:
```python
from datetime import date, datetime, timedelta
```

Y reemplaza la función `armar_mapa` (líneas 168-182 aprox.) por:
```python
def armar_mapa(eventos: list[dict[str, Any]], ahora: datetime,
               cubierto_hasta: datetime | date | str | None = None) -> str:
    """El mensaje del lunes: el tema, los datos fuertes con su hora de Chile y una línea para conversar."""
    ahora = ahora.astimezone(ag.SANTIAGO)
    tema = tema_de_la_semana(eventos)
    if tema["tranquila"]:
        cuerpo = ["Ningún dato de los próximos 7 días marca la semana con claridad (calendario de EE.UU., "
                  "Chile, China y la Zona Euro).", "",
                  "💬 Qué conversar: es una buena semana para ponerte al día con tus clientes y revisar cómo "
                  "viene su cartera."]
    else:
        cuerpo = ["Lo que viene, en hora de Chile:", *[_linea(e) for e in _elegidos(eventos)], "",
                  f"💬 Qué conversar: {guia()[tema['tipo']]['conversar']}"]
    desde, hasta = ag.dia_corto(ahora), ag.dia_corto(ahora + timedelta(days=ag.VENTANA_DIAS))
    encabezado = [f"📅 {tema['titular']}", f"Del {desde} al {hasta}."]
    if cubierto_hasta is not None:
        dia = ag.dia_corto(cubierto_hasta) if isinstance(cubierto_hasta, (date, datetime)) else str(cubierto_hasta)
        encabezado.append(f"El calendario llegó incompleto: lo que ves llega hasta {dia}; puede faltar algún dato posterior.")
    return "\n".join([*encabezado, "", *cuerpo, "", AVISO_RIESGO])
```

2. En `scripts/analista/avisos_semana.py`, modifica `_avisos_posibles` (líneas 185-204 aprox.) para aceptar `parcial: bool = False` y calcular `cubierto_hasta`:
```python
def _avisos_posibles(ahora: datetime, eventos: list[dict[str, Any]], parcial: bool = False) -> list[Aviso]:
    fecha = ahora.date().isoformat()
    avisos: list[Aviso] = []
    if ahora.weekday() == 0 and _en_ventana(ahora, MAPA):
        cubierto_hasta = None
        if parcial and eventos:
            fechas = [ag._cuando(e) for e in eventos if ag._cuando(e)]
            cubierto_hasta = max(fechas) if fechas else None
        avisos.append(Aviso("mapa", fecha, "mapa", 0, sm.armar_mapa(eventos, ahora, cubierto_hasta=cubierto_hasta), None, _id("mapa", fecha, "mapa")))
    if ahora.weekday() < 5 and _en_ventana(ahora, VISPERA):
        vistos: set[tuple] = set()
        del_tema = [e for e in eventos if sm.tipo_de_evento(e) and sm._tier(e) <= TIER_VISPERA and ag._cuando(e)]
        for ev in sorted(del_tema, key=sm._clave_de_tema):
            cuando = ag._cuando(ev)
            if cuando <= ahora or _habil_anterior(cuando.date()) != ahora.date():
                continue
            if sm.momento(ev) in vistos:   # un informe es una sola víspera: no se gasta el cupo en dos
                continue
            vistos.add(sm.momento(ev))
            tipo, pais, dia = sm.momento(ev)
            clave = f"{tipo}|{pais}|{dia.isoformat()}"
            avisos.append(Aviso("vispera", fecha, clave, sm._tier(ev), sm.armar_vispera(ev, ahora),
                                sm.activo_mas_afectado(ev), _id("vispera", fecha, clave)))
    return avisos
```

3. En `scripts/analista/avisos_semana.py`, modifica `que_toca` (líneas 207-212 aprox.) para aceptar y propagar `parcial`:
```python
def que_toca(ahora: datetime, eventos: list[dict[str, Any]], estado: Estado, ejecutivo: str,
             parcial: bool = False) -> list[Aviso]:
    """Los avisos que le corresponden ahora a este ejecutivo: sin repetir y con el tope diario."""
    ahora = ahora.astimezone(ag.SANTIAGO)
    pendientes = [a for a in _avisos_posibles(ahora, eventos, parcial=parcial) if not estado.enviado(ejecutivo, a)]
    cupo = max(TOPE_DIARIO - estado.enviados_hoy(ejecutivo, ahora.date()), 0)
    return pendientes[:cupo]   # el mapa va primero (tier 0), luego los de menor tier
```

4. En `scripts/analista/avisos_semana.py`, modifica `leer_eventos` (líneas 215-221 aprox.) para distinguir `"parcial"` cuando `eventos` no está vacío y `fallidas > 0`:
```python
def leer_eventos(ahora: datetime, cargar: Callable[..., dict[str, Any]] | None = None) -> tuple[str, list[dict[str, Any]]]:
    """`("ok"|"parcial"|"vacia"|"sin_calendario", eventos)`: la misma distinción que `agenda.py`."""
    altos, _avisos, fallidas, _limite = ag.ventana_cruda(ahora, cargar)
    eventos = [ev for _, ev in altos]
    if eventos:
        return ("parcial" if fallidas > 0 else "ok"), eventos
    return ("sin_calendario" if fallidas else "vacia"), []
```

5. En `scripts/analista/avisos_semana.py`, dentro de `Agendador.latido` (líneas 290-302 aprox.), propaga `parcial=(situacion == "parcial")` al llamar a `que_toca`:
```python
    def latido(self) -> None:
        ahora = self.reloj().astimezone(ag.SANTIAGO)
        self._mapa_perdido(ahora)
        if not hay_ventana(ahora):
            return
        situacion, eventos = self.leer(ahora)
        if situacion == "sin_calendario":
            self._calendario_caido(ahora)
            return
        for ejecutivo in destinatarios(self.config):
            for aviso in que_toca(ahora, eventos, self.estado, ejecutivo, parcial=(situacion == "parcial")):
                if (ejecutivo, aviso.id) in self._hechos:
                    continue   # salió pero no se pudo anotar: reenviarlo cada minuto sería peor que perder el registro
```

- [ ] **Step 4: Correr y ver que pasan los tests del módulo**

Ejecuta:
```powershell
uv run pytest tests/test_analista_semana.py tests/test_analista_avisos_semana.py tests/test_analista_bot_avisos.py -q
```
Resultado esperado: `102 passed` en ~4s.

- [ ] **Step 5: Correr la suite completa**

Ejecuta:
```powershell
uv run pytest -q
```
Resultado esperado: `2132 passed, 44 skipped` sin fallos.

- [ ] **Step 6: Commit**

Ejecuta:
```powershell
git add scripts/analista/semana.py scripts/analista/avisos_semana.py tests/test_analista_semana.py tests/test_analista_avisos_semana.py
git commit -m "fix(analista): advertir cobertura parcial en mapa semanal si falla pestaña del calendario

Menor 10: cuando una de las pestañas del calendario económico falla
pero la otra aporta datos, leer_eventos reporta situación 'parcial'.
El agendador lo procesa como válido y armar_mapa explicita hasta qué
día alcanza la información disponible.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```
