I have launched the test suite check in the background to verify the baseline status of the repository and will inspect the result once it completes.
Esperando que termine la ejecución de la suite completa de pruebas para confirmar el estado base del repositorio.
Esperando la finalización de la corrida de pruebas en segundo plano.
# Plan de implementación: Feriados de Chile en la víspera de la alerta semanal (Menor 9)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Hacer que la víspera de la alerta semanal (16:00 a 16:30 del día hábil anterior a un evento de tier 1) respete el calendario oficial de feriados de Chile: no emitir avisos en días no laborables en Chile y adelantar la víspera al día hábil inmediatamente anterior cuando el día previo al evento sea feriado, manteniendo inalterada la salida del mapa del lunes según lo manda la especificación.

**Architecture:** Se incorpora el archivo de configuración `config/feriados_chile.json` con metadatos oficiales y fechas en formato ISO (análogo a `config/feriados_bolsa.json`). En `scripts/analista/avisos_semana.py` se añade la función `feriados_chile(ruta)` que retorna un `frozenset[date]`, y se ajustan `_habil_anterior`, `hay_ventana`, `_avisos_posibles` y `que_toca` para recibir o consultar los feriados. La ventana de víspera verifica que el día actual no sea feriado, mientras que la ventana del mapa del lunes se mantiene intacta.

**Tech Stack:** Python 3.12, pytest, uv, zoneinfo (`America/Santiago`), JSON estándar.

**Spec:** `docs/superpowers/specs/2026-10-18-alerta-semana-ejecutivos-design.md`

## Global Constraints

- Rama de trabajo: `feat/alerta-semana-ejecutivos`. Nunca commitear a `master` y no hacer push ni merge sin instrucción del director.
- TDD estricto: escribir las pruebas que fallan primero, verificar el fallo, implementar el código mínimo, verificar que pasan y correr la suite completa.
- Ningún módulo en `scripts/analista` puede importar nada relativo al envío a WhatsApp (custodiado por test AST).
- Texto en español chileno para ejecutivos, sin guion largo ni medio como incisos (usar comas, dos puntos o paréntesis).
- Comandos ejecutables en Windows PowerShell usando `uv`.
- Fechas de feriados 2026 estrictamente verificadas contra fuente oficial (`https://www.feriados.cl/` y leyes de la República de Chile: Ley 2.977, Ley 19.668, Ley 19.973, Ley 20.299), sin fechas inventadas y con la URL en `_meta.fuente`.
- El commit final debe incluir el trailer: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **Invariabilidad del mapa del lunes**: la spec establece que el mapa de la semana debe emitirse los lunes entre 07:45 y 08:15 para preparar la semana, incluso si el lunes es feriado. La validación de feriados aplica a la víspera, nunca a la ventana del mapa.
2. **Encadenamiento de feriados y fin de semana**: si un evento es un martes y el lunes previo es feriado (ej: Encuentro de Dos Mundos el 12 de octubre), `_habil_anterior` debe saltar el lunes feriado, domingo y sábado, situando la víspera el viernes hábil previo (9 de octubre).
3. **Degradación pacífica**: si `config/feriados_chile.json` falta o se corrompe, `feriados_chile()` retorna `frozenset()` vacío y no interrumpe el agendador ni bota el bot de Telegram.

---

### Task 1: Calendario de feriados de Chile y soporte en víspera de alerta semanal

**Files:**
- Create: `config/feriados_chile.json`
- Modify: `scripts/analista/avisos_semana.py`
- Test: `tests/test_analista_avisos_semana.py`

**Interfaces:**
- `feriados_chile(ruta: Path = RUTA_FERIADOS_CHILE) -> frozenset[date]`
- `_habil_anterior(dia: date, feriados: frozenset[date] | None = None) -> date`
- `hay_ventana(ahora: datetime, feriados: frozenset[date] | None = None) -> bool`
- `_avisos_posibles(ahora: datetime, eventos: list[dict[str, Any]], feriados: frozenset[date] | None = None) -> list[Aviso]`
- `que_toca(ahora: datetime, eventos: list[dict[str, Any]], estado: Estado, ejecutivo: str, feriados: frozenset[date] | None = None) -> list[Aviso]`
- `Agendador.__init__(..., feriados: frozenset[date] | None = None)`
- `RUTA_FERIADOS_CHILE = RAIZ / "config" / "feriados_chile.json"`

- [ ] **Step 1: Escribir los tests que fallan en `tests/test_analista_avisos_semana.py`**

Agregar al final de `tests/test_analista_avisos_semana.py`:

```python
# ───────────────────────────────────────────── feriados de Chile (menor 9)


def test_contrato_feriados_chile_archivo_real():
    ruta = Path(__file__).resolve().parent.parent / "config" / "feriados_chile.json"
    assert ruta.exists(), "Falta crear config/feriados_chile.json"
    import json
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert "_meta" in datos
    meta = datos["_meta"]
    assert meta.get("fuente") == "https://www.feriados.cl/"
    assert "actualizado" in meta
    assert "proceso_actualizacion" in meta
    assert "feriados" in datos
    fechas = datos["feriados"]
    assert isinstance(fechas, list) and len(fechas) > 0
    # Todas las fechas deben cumplir formato ISO YYYY-MM-DD
    fechas_dt = [date.fromisoformat(f) for f in fechas]
    # Feriados oficiales confirmados del último trimestre 2026 en Chile (sin inventar)
    assert date(2026, 10, 12) in fechas_dt   # Encuentro de Dos Mundos (Lunes)
    assert date(2026, 10, 31) in fechas_dt   # Iglesias Evangélicas y Protestantes (Sábado)
    assert date(2026, 11, 1) in fechas_dt    # Todos los Santos (Domingo)
    assert date(2026, 12, 8) in fechas_dt    # Inmaculada Concepción (Martes)
    assert date(2026, 12, 25) in fechas_dt   # Navidad (Viernes)
    cargados = av.feriados_chile(ruta)
    assert isinstance(cargados, frozenset)
    assert date(2026, 12, 8) in cargados


def test_feriados_chile_archivo_temporal_y_fallback(tmp_path):
    f_json = tmp_path / "feriados.json"
    f_json.write_text('{"_meta": {}, "feriados": ["2026-12-08", "invalido"]}', encoding="utf-8")
    assert av.feriados_chile(f_json) == frozenset({date(2026, 12, 8)})
    assert av.feriados_chile(tmp_path / "inexistente.json") == frozenset()


def test_habil_anterior_salta_feriados_y_fines_de_semana():
    feriados = frozenset({date(2026, 10, 12), date(2026, 12, 8)})
    # Martes 8 dic es feriado: el día hábil anterior al miércoles 9 dic es el lunes 7 dic
    assert av._habil_anterior(date(2026, 12, 9), feriados=feriados) == date(2026, 12, 7)
    # Lunes 12 oct es feriado: el día hábil anterior al martes 13 oct salta lunes, dom y sáb, cayendo en viernes 9 oct
    assert av._habil_anterior(date(2026, 10, 13), feriados=feriados) == date(2026, 10, 9)


def test_la_ventana_de_vispera_no_abre_en_feriado():
    feriados = frozenset({date(2026, 12, 8)})
    martes_feriado_1615 = datetime(2026, 12, 8, 16, 15, tzinfo=SCL)
    assert av.hay_ventana(martes_feriado_1615, feriados=feriados) is False


def test_el_mapa_del_lunes_si_abre_en_feriado():
    # La spec manda que el mapa sale el lunes 07:45 para orientar la semana, aunque sea feriado
    feriados = frozenset({date(2026, 10, 12)})
    lunes_feriado_0745 = datetime(2026, 10, 12, 7, 45, tzinfo=SCL)
    assert av.hay_ventana(lunes_feriado_0745, feriados=feriados) is True
    avisos = av.que_toca(lunes_feriado_0745, [CPI], av.Estado(Path("x")), "1", feriados=feriados)
    assert [x.tipo for x in avisos] == ["mapa"]


def test_la_vispera_se_adelanta_al_dia_habil_anterior_cuando_hay_feriado(estado):
    feriados = frozenset({date(2026, 12, 8)})
    cpi_miercoles = ev("CPI (MoM) (Nov)", "2026-12-09 09:30")
    lunes_1600 = datetime(2026, 12, 7, 16, 0, tzinfo=SCL)
    martes_feriado_1600 = datetime(2026, 12, 8, 16, 0, tzinfo=SCL)

    # El lunes a las 16:00 se genera la víspera del dato del miércoles porque el martes es feriado
    avisos_lunes = av.que_toca(lunes_1600, [cpi_miercoles], estado, "1", feriados=feriados)
    assert [x.tipo for x in avisos_lunes] == ["vispera"]

    # El martes a las 16:00 (feriado) no se genera ningún aviso
    avisos_martes = av.que_toca(martes_feriado_1600, [cpi_miercoles], estado, "1", feriados=feriados)
    assert avisos_martes == []
```

- [ ] **Step 2: Correr los tests y verificar que fallan (FAIL)**

Ejecutar en PowerShell:
```powershell
uv run pytest tests/test_analista_avisos_semana.py -k "feriado" -q
```
Salida esperada:
```text
FAILED tests/test_analista_avisos_semana.py::test_contrato_feriados_chile_archivo_real - AssertionError: Falta crear config/feriados_chile.json
FAILED tests/test_analista_avisos_semana.py::test_feriados_chile_archivo_temporal_y_fallback - AttributeError: module 'analista.avisos_semana' has no attribute 'feriados_chile'
FAILED tests/test_analista_avisos_semana.py::test_habil_anterior_salta_feriados_y_fines_de_semana - TypeError: _habil_anterior() got an unexpected keyword argument 'feriados'
FAILED tests/test_analista_avisos_semana.py::test_la_ventana_de_vispera_no_abre_en_feriado - TypeError: hay_ventana() got an unexpected keyword argument 'feriados'
FAILED tests/test_analista_avisos_semana.py::test_el_mapa_del_lunes_si_abre_en_feriado - TypeError: hay_ventana() got an unexpected keyword argument 'feriados'
FAILED tests/test_analista_avisos_semana.py::test_la_vispera_se_adelanta_al_dia_habil_anterior_cuando_hay_feriado - TypeError: que_toca() got an unexpected keyword argument 'feriados'
6 failed in ...
```

- [ ] **Step 3: Crear el archivo de configuración `config/feriados_chile.json`**

Crear `config/feriados_chile.json` con los feriados nacionales oficiales de Chile para 2026:

```json
{
  "_meta": {
    "actualizado": "2026-10-18",
    "fuente": "https://www.feriados.cl/",
    "proceso_actualizacion": "manual, una vez al año, por quien mantenga el repo"
  },
  "feriados": [
    "2026-01-01",
    "2026-04-03",
    "2026-04-04",
    "2026-05-01",
    "2026-05-21",
    "2026-06-21",
    "2026-06-29",
    "2026-07-16",
    "2026-08-15",
    "2026-09-18",
    "2026-09-19",
    "2026-10-12",
    "2026-10-31",
    "2026-11-01",
    "2026-12-08",
    "2026-12-25"
  ]
}
```

- [ ] **Step 4: Implementar el cargador y la lógica de feriados en `scripts/analista/avisos_semana.py`**

Modificar `scripts/analista/avisos_semana.py`:

1. Añadir importación de `json` al inicio:
```python
import hashlib
import json
import threading
import traceback
```

2. Definir constante de ruta y la función `feriados_chile`:
```python
RUTA = RAIZ / "data" / "semanal" / "avisos_semana.json"
RUTA_FERIADOS_CHILE = RAIZ / "config" / "feriados_chile.json"
TOPE_DIARIO = 2
```

```python
def feriados_chile(ruta: Path = RUTA_FERIADOS_CHILE) -> frozenset[date]:
    """Carga los feriados oficiales de Chile desde el archivo de configuración.

    Devuelve un conjunto inmutable de fechas. Si el archivo no existe o está dañado,
    devuelve un frozenset vacío para no interrumpir el agendador.
    """
    if not ruta.exists():
        return frozenset()
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except Exception:
        return frozenset()
    fechas = datos.get("feriados") or datos.get("chile") or []
    resultado = set()
    for f in fechas:
        try:
            resultado.add(date.fromisoformat(f))
        except (ValueError, TypeError):
            continue
    return frozenset(resultado)
```

3. Actualizar `hay_ventana` y `_habil_anterior`:
```python
def hay_ventana(ahora: datetime, feriados: frozenset[date] | None = None) -> bool:
    """¿Alguna ventana está abierta? Fuera de ellas no se gasta una lectura del calendario."""
    ahora = ahora.astimezone(ag.SANTIAGO)
    feriados = feriados if feriados is not None else feriados_chile()
    mapa_abierto = ahora.weekday() == 0 and _en_ventana(ahora, MAPA)
    vispera_abierta = ahora.weekday() < 5 and ahora.date() not in feriados and _en_ventana(ahora, VISPERA)
    return mapa_abierto or vispera_abierta


def _habil_anterior(dia: date, feriados: frozenset[date] | None = None) -> date:
    feriados = feriados if feriados is not None else feriados_chile()
    previo = dia - timedelta(days=1)
    while previo.weekday() >= 5 or previo in feriados:
        previo -= timedelta(days=1)
    return previo
```

4. Actualizar `_avisos_posibles` y `que_toca`:
```python
def _avisos_posibles(ahora: datetime, eventos: list[dict[str, Any]],
                     feriados: frozenset[date] | None = None) -> list[Aviso]:
    feriados = feriados if feriados is not None else feriados_chile()
    fecha = ahora.date().isoformat()
    avisos: list[Aviso] = []
    if ahora.weekday() == 0 and _en_ventana(ahora, MAPA):
        avisos.append(Aviso("mapa", fecha, "mapa", 0, sm.armar_mapa(eventos, ahora), None, _id("mapa", fecha, "mapa")))
    if ahora.weekday() < 5 and ahora.date() not in feriados and _en_ventana(ahora, VISPERA):
        vistos: set[tuple] = set()
        del_tema = [e for e in eventos if sm.tipo_de_evento(e) and sm._tier(e) <= TIER_VISPERA and ag._cuando(e)]
        for ev in sorted(del_tema, key=sm._clave_de_tema):
            cuando = ag._cuando(ev)
            if cuando <= ahora or _habil_anterior(cuando.date(), feriados=feriados) != ahora.date():
                continue
            if sm.momento(ev) in vistos:   # un informe es una sola víspera: no se gasta el cupo en dos
                continue
            vistos.add(sm.momento(ev))
            tipo, pais, dia = sm.momento(ev)
            clave = f"{tipo}|{pais}|{dia.isoformat()}"
            avisos.append(Aviso("vispera", fecha, clave, sm._tier(ev), sm.armar_vispera(ev, ahora),
                                sm.activo_mas_afectado(ev), _id("vispera", fecha, clave)))
    return avisos


def que_toca(ahora: datetime, eventos: list[dict[str, Any]], estado: Estado, ejecutivo: str,
             feriados: frozenset[date] | None = None) -> list[Aviso]:
    """Los avisos que le corresponden ahora a este ejecutivo: sin repetir y con el tope diario."""
    ahora = ahora.astimezone(ag.SANTIAGO)
    pendientes = [a for a in _avisos_posibles(ahora, eventos, feriados=feriados) if not estado.enviado(ejecutivo, a)]
    cupo = max(TOPE_DIARIO - estado.enviados_hoy(ejecutivo, ahora.date()), 0)
    return pendientes[:cupo]   # el mapa va primero (tier 0), luego los de menor tier
```

5. Permitir inyección opcional de `feriados` en `Agendador`:
```python
class Agendador:
    """`enviar(chat, aviso) -> message_id` y `avisar_director(chat, texto)` los pone el bot."""

    def __init__(self, config: dict[str, Any], estado: Estado, enviar: Callable[[str, Aviso], int | None],
                 avisar_director: Callable[[str, str], None], reloj: Callable[[], datetime],
                 leer: Callable[[datetime], tuple[str, list[dict[str, Any]]]] = leer_eventos,
                 log: Callable[[str], None] = lambda texto: None,
                 feriados: frozenset[date] | None = None):
        self.config, self.estado, self.enviar = config, estado, enviar
        self.avisar_director, self.reloj, self.leer, self.log = avisar_director, reloj, leer, log
        self.feriados = feriados
        self._hechos: set[tuple[str, str]] = set()   # enviados en este proceso, anotados o no
```
Y en `Agendador.latido`:
```python
    def latido(self) -> None:
        ahora = self.reloj().astimezone(ag.SANTIAGO)
        self._mapa_perdido(ahora)
        fer = self.feriados if self.feriados is not None else feriados_chile()
        if not hay_ventana(ahora, feriados=fer):
            return
        situacion, eventos = self.leer(ahora)
        if situacion == "sin_calendario":
            self._calendario_caido(ahora)
            return
        for ejecutivo in destinatarios(self.config):
            for aviso in que_toca(ahora, eventos, self.estado, ejecutivo, feriados=fer):
                if (ejecutivo, aviso.id) in self._hechos:
                    continue   # salió pero no se pudo anotar: reenviarlo cada minuto sería peor que perder el registro
                try:
                    message_id = self.enviar(ejecutivo, aviso)
                except Exception:  # noqa: BLE001  un envío caído sigue pendiente: no se anota
                    self.log(f"aviso {aviso.tipo} a {ejecutivo} falló: {traceback.format_exc()}")
                    continue
                self._hechos.add((ejecutivo, aviso.id))
                try:
                    self.estado.anotar_envio(ejecutivo, aviso, ahora, message_id)
                except Exception:  # noqa: BLE001  no debe cortar a los ejecutivos que faltan
                    self.log(f"aviso {aviso.tipo} a {ejecutivo} salió pero no se anotó: {traceback.format_exc()}")
```

- [ ] **Step 5: Correr los tests nuevos y verificar que pasan (PASS)**

Ejecutar en PowerShell:
```powershell
uv run pytest tests/test_analista_avisos_semana.py -k "feriado" -q
```
Salida esperada:
```text
......                                                                   [100%]
6 passed in ...
```

- [ ] **Step 6: Correr la suite completa de tests**

Ejecutar en PowerShell:
```powershell
uv run pytest -q
```
Salida esperada:
```text
2134 passed, 44 skipped in ...
```

- [ ] **Step 7: Commitear los cambios a la rama de trabajo**

Ejecutar en PowerShell:
```powershell
git add config/feriados_chile.json scripts/analista/avisos_semana.py tests/test_analista_avisos_semana.py
git commit -m "fix(analista): considerar feriados de Chile en la vispera de la alerta semanal" -m "La vispera ahora salta feriados chilenos hacia el dia habil anterior y la ventana de vispera no abre en feriado, respetando que el mapa del lunes sale siempre.`n`nCo-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```
