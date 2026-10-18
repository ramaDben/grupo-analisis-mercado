Ocurrió un segundo plano mientras corren las pruebas de analista. Esperando la finalización...
Esperando a que finalice la ejecución de las pruebas.
# Menor 17: cache de lecturas del calendario en Agendador. Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evitar hasta 30 llamadas redundantes al calendario de Investing.com durante una ventana abierta de 30 minutos en `Agendador.latido`, cacheando la ultima lectura exitosa durante 10 minutos (`LECTURA_TTL = timedelta(minutes=10)`), sin cachear lecturas caidas (`sin_calendario`) e invalidando inmediatamente la cache al cambiar el dia.

**Architecture:** En `scripts/analista/avisos_semana.py`, definir la constante de modulo `LECTURA_TTL = timedelta(minutes=10)`. En `Agendador.__init__`, agregar `self._cache_lectura: tuple[str, list[dict[str, Any]]] | None = None` y `self._cache_cuando: datetime | None = None`. Incorporar el metodo privado `Agendador._leer_con_cache(ahora: datetime) -> tuple[str, list[dict[str, Any]]]`. Si existe una lectura previa para el mismo dia calendario (`self._cache_cuando.date() == ahora.date()`) y han transcurrido menos de 10 minutos (`timedelta(0) <= ahora - self._cache_cuando < LECTURA_TTL`), se retorna la lectura guardada en memoria. Si no hay cache valida o esta expiro, se invoca `self.leer(ahora)`: si la respuesta es exitosa (`situacion != "sin_calendario"`: cubre `ok`, `vacia` o eventual `parcial`), se almacena en memoria con la marca `ahora`; si la respuesta es `sin_calendario`, la cache no se guarda (y se limpia cualquier valor previo residual). En `Agendador.latido`, invocar `self._leer_con_cache(ahora)` en lugar de `self.leer(ahora)`. Los envios fallidos siguen pendientes en el estado y se reintentan en cada minuto posterior utilizando los eventos vigentes de la cache.

**Tech Stack:** Python 3.11+, pytest via `uv run`, `ZoneInfo("America/Santiago")`, `datetime`, `timedelta`.

**Spec:** `docs/superpowers/specs/2026-10-18-alerta-semana-ejecutivos-design.md` (Regla 7 "Calendario caido", seccion "Donde vive en el codigo").

## Global Constraints

- **TDD estricto:** la tarea inicia con sus pruebas unitarias en rojo, verificacion del fallo (FAIL), implementacion minima, verificacion del paso (PASS) y corrida limpia de la suite completa.
- **Aislamiento de WhatsApp:** ningun modulo dentro de `scripts/analista/` puede importar `enviar_whatsapp`, `whatsapp_sender` ni funciones de envio a WhatsApp. El contrato existente en `test_el_agendador_no_importa_el_envio_de_whatsapp` debe mantenerse en verde.
- **Reglas de redaccion:** comunicaciones para ejecutivos y comentarios en espanol de Chile, tuteo neutro, **estrictamente sin guion largo (`—`) ni medio (`–`)**, usando unicamente guion simple ASCII (`-`).
- **Control de versiones:** trabajar en la rama `feat/alerta-semana-ejecutivos`. Nunca commitear a `master` ni ejecutar `git push`.
- **Trailer de commit obligatorio:** el commit debe terminar exactamente con la linea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- **Alcance acotado:** resolver de forma precisa el Menor 17 en una unica tarea, sin modificar firmas publicas ni tocar logica ajena al agendador. Comandos compatibles con Windows PowerShell y `uv`.

## Review Focus

1. **Reintento inmediato tras fallo del calendario:** si el lector devuelve `sin_calendario`, la respuesta jamas se guarda en cache; el siguiente latido (1 minuto despues) debe volver a invocar `self.leer(ahora)` de forma obligatoria.
2. **Expiracion por ventana de tiempo (TTL de 10 minutos):** lecturas dentro de 9 minutos usan cache (1 llamada total); a los 11 minutos exactos debe disparar la segunda llamada al lector.
3. **Invalidacion por cambio de dia:** si la hora cruza medianoche (incluso con diferencia inferior a 10 minutos), `self._cache_cuando.date() == ahora.date()` debe evaluar falso y forzar una nueva lectura.
4. **Reintento de envios con Telegram caido:** si `self.enviar` levanta excepcion en el primer minuto, el envio no se anota en el estado. En el minuto siguiente, `latido()` reintenta el envio utilizando los eventos que quedaron en cache, sin llamar nuevamente a `self.leer(ahora)`.
5. **Lecturas vacias validas:** el estado `vacia` (el calendario respondio y no hay eventos fuertes) si es una lectura valida y debe quedar cacheada durante los 10 minutos.

---

## File Structure

| Archivo | Responsabilidad | Accion |
|---|---|---|
| `scripts/analista/avisos_semana.py` | Constante `LECTURA_TTL`, estado de cache en `Agendador.__init__`, metodo `_leer_con_cache` y uso en `latido` | Modificar |
| `tests/test_analista_avisos_semana.py` | Casos de prueba para verificar cache de 10 min, 3 latidos en 3 min -> 1 lectura, 11 min -> 2, caida no cacheada, cambio de dia y reintentos de envio | Modificar |

---

### Task 1: Cache de lecturas exitosas del calendario en Agendador (Menor 17)

**Files:**
- Modify: `scripts/analista/avisos_semana.py:43-45,235-250,290-300`
- Test: `tests/test_analista_avisos_semana.py:189-200`

**Interfaces:**
- Produces:
  - Constante `LECTURA_TTL = timedelta(minutes=10)` en `avisos_semana.py`.
  - Atributos `self._cache_lectura: tuple[str, list[dict[str, Any]]] | None` y `self._cache_cuando: datetime | None` en `Agendador.__init__`.
  - Metodo `Agendador._leer_con_cache(self, ahora: datetime) -> tuple[str, list[dict[str, Any]]]`.
  - En `Agendador.latido()` se sustituye `self.leer(ahora)` por `self._leer_con_cache(ahora)`.
- Consumes:
  - `self.leer(ahora: datetime) -> tuple[str, list[dict[str, Any]]]`.

- [ ] **Step 1: Escribir los tests unitarios para la cache**

Agregar en `tests/test_analista_avisos_semana.py` (justo despues de `test_semana_sin_eventos_fuertes_si_se_envia_cuando_el_calendario_respondio`):

```python
# ───────────────────────────────────────────── cache de lecturas (menor 17)


class LectorContador:
    def __init__(self, respuesta: tuple[str, list] = ("ok", [CPI])):
        self.llamadas = 0
        self.respuesta = respuesta

    def __call__(self, ahora: datetime) -> tuple[str, list]:
        self.llamadas += 1
        return self.respuesta


def test_la_cache_del_agendador_evita_releer_en_cada_latido(estado):
    envios = Envios()
    lector = LectorContador(("ok", [CPI]))
    ahora = [LUNES_0745]
    ag_ = agendador(estado, envios, ahora, lector)

    # 3 latidos en 3 minutos -> 1 lectura
    ag_.latido()
    ahora[0] = a(19, 7, 46)
    ag_.latido()
    ahora[0] = a(19, 7, 47)
    ag_.latido()
    assert lector.llamadas == 1

    # a los 11 minutos (07:45 + 11 min = 07:56, ventana del mapa abierta) -> 2
    ahora[0] = a(19, 7, 56)
    ag_.latido()
    assert lector.llamadas == 2


def test_los_envios_fallidos_se_reintentan_cada_minuto_usando_la_cache(estado):
    envios = Envios(falla=True)
    lector = LectorContador(("ok", [CPI]))
    ahora = [LUNES_0745]
    ag_ = agendador(estado, envios, ahora, lector)

    # Latido 1: Telegram falla, envio no se anota
    ag_.latido()
    assert lector.llamadas == 1
    assert envios.enviados == []

    # Latido 2: Telegram vuelve, reintenta y envia usando eventos de la cache sin llamar al lector
    ahora[0] = a(19, 7, 46)
    envios.falla = False
    ag_.latido()
    assert lector.llamadas == 1
    assert len(envios.enviados) == 2


def test_la_caida_del_calendario_no_se_cachea_y_se_reintenta_en_cada_latido(estado):
    envios = Envios()
    lector = LectorContador(("sin_calendario", []))
    ahora = [LUNES_0745]
    ag_ = agendador(estado, envios, ahora, lector)

    ag_.latido()
    assert lector.llamadas == 1

    ahora[0] = a(19, 7, 46)
    ag_.latido()
    assert lector.llamadas == 2

    ahora[0] = a(19, 7, 47)
    ag_.latido()
    assert lector.llamadas == 3


def test_la_lectura_vacia_si_se_cachea(estado):
    lector = LectorContador(("vacia", []))
    ahora = [LUNES_0745]
    ag_ = agendador(estado, Envios(), ahora, lector)

    ag_.latido()
    ahora[0] = a(19, 7, 46)
    ag_.latido()
    assert lector.llamadas == 1


def test_el_cambio_de_dia_invalida_la_cache_del_agendador(estado):
    lector = LectorContador(("ok", [CPI]))
    ahora = [LUNES_0745]
    ag_ = agendador(estado, Envios(), ahora, lector)

    # Lectura inicial en dia 19
    ag_._leer_con_cache(datetime(2026, 10, 19, 23, 58, tzinfo=SCL))
    assert lector.llamadas == 1

    # 4 minutos despues cronologicamente (< 10 min TTL), pero en dia 20: la cache se invalida
    ag_._leer_con_cache(datetime(2026, 10, 20, 0, 2, tzinfo=SCL))
    assert lector.llamadas == 2
```

- [ ] **Step 2: Correr y ver que fallan los tests**

Ejecutar en Windows PowerShell:
```powershell
uv run pytest tests/test_analista_avisos_semana.py -k "cache or caida_del_calendario or releer" -q
```

Salida esperada:
FAIL (`AssertionError: assert 3 == 1` en `test_la_cache_del_agendador_evita_releer_en_cada_latido` y `AttributeError: 'Agendador' object has no attribute '_leer_con_cache'`).

- [ ] **Step 3: Implementar la cache en `avisos_semana.py`**

1. En `scripts/analista/avisos_semana.py`, agregar la constante de modulo junto al resto de constantes (alrededor de linea 44):
```python
LECTURA_TTL = timedelta(minutes=10)
```

2. En `Agendador.__init__` (alrededor de linea 245), inicializar los campos de cache:
```python
        self._hechos: set[tuple[str, str]] = set()   # enviados en este proceso, anotados o no
        self._cache_lectura: tuple[str, list[dict[str, Any]]] | None = None
        self._cache_cuando: datetime | None = None
```

3. En la clase `Agendador`, agregar el metodo `_leer_con_cache`:
```python
    def _leer_con_cache(self, ahora: datetime) -> tuple[str, list[dict[str, Any]]]:
        if (self._cache_cuando is not None and self._cache_lectura is not None
                and self._cache_cuando.date() == ahora.date()
                and timedelta(0) <= ahora - self._cache_cuando < LECTURA_TTL):
            return self._cache_lectura
        situacion, eventos = self.leer(ahora)
        if situacion != "sin_calendario":
            self._cache_cuando = ahora
            self._cache_lectura = (situacion, eventos)
        else:
            self._cache_cuando = None
            self._cache_lectura = None
        return situacion, eventos
```

4. En `Agendador.latido()` (alrededor de linea 295), reemplazar la llamada directa:
```python
        situacion, eventos = self._leer_con_cache(ahora)
        if situacion == "sin_calendario":
            self._calendario_caido(ahora)
            return
```

- [ ] **Step 4: Correr y verificar que pasen los nuevos tests**

Ejecutar en Windows PowerShell:
```powershell
uv run pytest tests/test_analista_avisos_semana.py -k "cache or caida_del_calendario or releer" -q
```

Salida esperada:
PASS (`5 passed`).

- [ ] **Step 5: Correr la suite completa del modulo y del proyecto**

Ejecutar en Windows PowerShell:
```powershell
uv run pytest tests/test_analista_avisos_semana.py -q
```
Salida esperada:
PASS (`40 passed`).

Verificar que se preserve la regla de aislamiento de WhatsApp:
```powershell
uv run pytest tests/test_analista_avisos_semana.py -k "whatsapp" -q
```
Salida esperada:
PASS (`1 passed`).

Ejecutar la suite general:
```powershell
uv run pytest -q
```
Salida esperada:
Todos los tests pasando (sin regresiones).

- [ ] **Step 6: Commit en rama `feat/alerta-semana-ejecutivos`**

Verificar rama y cambios:
```powershell
git branch --show-current
git status
```

Confirmar cambios y commitear:
```powershell
git add scripts/analista/avisos_semana.py tests/test_analista_avisos_semana.py
git commit -m "fix(analista): cache de 10 minutos para lecturas de calendario en agendador

Evita hasta 30 llamadas redundantes por ventana abierta cacheando lecturas exitosas
por 10 minutos (LECTURA_TTL). Una caida del calendario (sin_calendario) nunca se cachea
y se reintenta en cada latido. El cambio de dia invalida la cache.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```
