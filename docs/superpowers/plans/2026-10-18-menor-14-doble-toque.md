# Menor 14: Antirrebote en clics del botón 'Ver análisis' (alerta semanal). Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evitar que un doble toque del botón "Ver análisis" (`sw:ped:<id>`) infle la medición de `clics_boton` en `Estado.anotar_clic` (`scripts/analista/avisos_semana.py`), ignorando clics del mismo ejecutivo y aviso que lleguen dentro de `CLIC_REBOTE = 5` segundos del anterior, manteniendo la respuesta al usuario en `bot.py` mediante el candado de un análisis por activo.

**Architecture:** `Estado.anotar_clic` en `scripts/analista/avisos_semana.py` almacena la marca temporal del último clic en el campo opcional `"ultimo_clic"` del registro. Si llega un nuevo clic para el mismo ejecutivo y aviso con una diferencia temporal no negativa menor a `CLIC_REBOTE` (5 segundos), se ignora el incremento y se devuelve `False`. Si el campo no existe (registros anteriores) o el tiempo transcurrido es mayor o igual a 5 segundos, se incrementa `clics_boton`, se actualiza `"ultimo_clic"` y se devuelve `True`. En `scripts/analista/bot.py`, `recibir_callback` invoca `anotar_clic` sin bloquear la respuesta al ejecutivo: el candado `self.candado` / `self.generando` en `_encolar` se encarga de evitar duplicar el análisis y responder al usuario.

**Tech Stack:** Python 3 (módulos `scripts/analista/avisos_semana.py`, `scripts/analista/bot.py`), pytest vía `uv run` en Windows PowerShell, `datetime` con `zoneinfo` (`America/Santiago`).

**Spec:** `docs/superpowers/specs/2026-10-18-alerta-semana-ejecutivos-design.md` (§3, Tarea 5b del plan previo). Menor 14 documentado.

## Global Constraints

- **TDD estricto:** cada tarea empieza con su test en rojo antes de tocar el código de producción.
- **Sin envíos a WhatsApp:** ningún módulo de `scripts/analista/` puede importar `enviar_whatsapp`, `whatsapp_sender` ni herramientas de despacho a WhatsApp (`test_el_agendador_no_importa_el_envio_de_whatsapp`).
- **Texto para ejecutivos:** español de Chile, sin guion largo (`—`) ni medio (`–`) como inciso.
- **Ramas y control de versiones:** trabajar en la rama `feat/alerta-semana-ejecutivos`. Nunca commitear a `master`, sin push. Cada commit debe terminar con la línea `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- **Compatibilidad hacia atrás:** registros existentes en `data/semanal/avisos_semana.json` sin el campo `"ultimo_clic"` deben leerse sin fallar usando `.get("ultimo_clic")`.
- **Comandos del entorno:** Windows PowerShell con `uv run pytest`.

## Review Focus

1. **Doble toque rápido (< 5 s):** dos clics a 2 segundos cuentan exactamente 1 en `clics_boton`. El segundo llamado a `anotar_clic` retorna `False`.
2. **Clic legítimo posterior (>= 5 s):** un clic a 6 segundos del anterior sí incrementa el contador a 2 y retorna `True`.
3. **Compatibilidad de registros históricos:** registros que no tienen el campo `"ultimo_clic"` no lanzan `KeyError` al llamar a `anotar_clic` y se actualizan correctamente.
4. **Resumen de interacción intacto:** `resumen_interaccion(desde, hasta, estado)` continúa calculando las métricas de clics sin desviaciones.
5. **Experiencia del usuario en Telegram:** en `bot.py`, el segundo toque rápido sigue recibiendo respuesta ("Armando el análisis" / "Ya se está generando...") sin duplicar tareas de encolado ni romper el flujo.

---

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `scripts/analista/avisos_semana.py` | Constante `CLIC_REBOTE = 5`, campo `"ultimo_clic"` en `anotar_envio` y validación de ventana temporal en `anotar_clic` | Modificar |
| `tests/test_analista_avisos_semana.py` | Pruebas de 2 s (1 clic), 6 s (2 clics), compatibilidad sin `"ultimo_clic"` e integridad de `resumen_interaccion` | Modificar |
| `tests/test_analista_bot_avisos.py` | Prueba de doble callback `sw:ped:<id>` en `bot.py`: respuesta al usuario y medición sin inflar | Modificar |

---

### Task 1: Antirrebote de 5 segundos en `anotar_clic` y protección de doble toque

**Files:**
- Modify: `scripts/analista/avisos_semana.py:36-45,123-138`
- Test: `tests/test_analista_avisos_semana.py:209-215`
- Test: `tests/test_analista_bot_avisos.py:169-178`

**Interfaces:**
- Produces:
  - `CLIC_REBOTE = 5` en `scripts/analista/avisos_semana.py`.
  - `Estado.anotar_clic(ejecutivo: str, id_: str, cuando: datetime) -> bool`: devuelve `True` si anotó el clic, `False` si fue ignorado por rebote (< 5 s) o si no encontró el registro.
  - Campo `"ultimo_clic": str | None` en cada registro de `enviados`.
- Consumes:
  - `bot.recibir_callback`: gestiona el callback `sw:ped:<id>` invocando `anotar_clic` y encolando el pedido bajo candado.

- [ ] **Step 1: Escribir los tests que fallan**

En `tests/test_analista_avisos_semana.py`, agregar las pruebas de rebote y compatibilidad de registros anteriores:

```python
def test_dos_clics_a_2_s_cuentan_uno_y_a_6_s_cuentan_dos(estado):
    from datetime import timedelta
    _, vispera = _enviar_mapa_y_vispera(estado)
    t0 = a(20, 16, 5)
    # Primer clic: cuenta y devuelve True
    assert estado.anotar_clic("1", vispera.id, t0) is True
    # Segundo clic a 2 segundos: rebote ignorado, devuelve False
    assert estado.anotar_clic("1", vispera.id, t0 + timedelta(seconds=2)) is False
    assert estado.registro("1", vispera.id)["clics_boton"] == 1
    # Tercer clic a 6 segundos del primero: cuenta y devuelve True
    assert estado.anotar_clic("1", vispera.id, t0 + timedelta(seconds=6)) is True
    assert estado.registro("1", vispera.id)["clics_boton"] == 2


def test_anotar_clic_con_registro_antiguo_sin_ultimo_clic_no_rompe(estado):
    _, vispera = _enviar_mapa_y_vispera(estado)
    # Simular registro previo en disco sin la clave opcional "ultimo_clic"
    with estado.lock:
        reg = estado.registro("1", vispera.id)
        reg.pop("ultimo_clic", None)
        import analista.registro_semanal as rg
        rg._escribir(estado.ruta, estado.datos)

    t0 = a(20, 16, 5)
    assert estado.anotar_clic("1", vispera.id, t0) is True
    assert estado.registro("1", vispera.id)["clics_boton"] == 1
    assert estado.registro("1", vispera.id)["ultimo_clic"] == t0.isoformat()
```

En `tests/test_analista_bot_avisos.py`, agregar la prueba de doble toque en `bot.recibir_callback`:

```python
def test_el_doble_toque_del_boton_responde_al_usuario_y_no_infla_clics(con_avisos):
    a = aviso("vispera", fecha="2026-10-20", activo="USDCLP")
    con_avisos.bot.avisos.anotar_envio(CAMILA, a, MARTES, 901)

    # Primer toque: se encola y cuenta 1 clic
    resp1 = con_avisos.bot.recibir_callback(callback(f"sw:ped:{a.id}"))
    assert "Recibido" in resp1[0].texto
    assert con_avisos.bot.cola.qsize() == 1

    # Segundo toque inmediato (mismo segundo): bot responde informando que ya se genera
    resp2 = con_avisos.bot.recibir_callback(callback(f"sw:ped:{a.id}"))
    assert "Ya se está generando" in resp2[0].texto
    assert con_avisos.bot.cola.qsize() == 1

    # La medición solo cuenta 1 clic
    reg = con_avisos.bot.avisos.registro(CAMILA, a.id)
    assert reg["clics_boton"] == 1
```

- [ ] **Step 2: Correr los tests y verificar FAIL**

Ejecutar en Windows PowerShell:
```powershell
uv run pytest tests/test_analista_avisos_semana.py tests/test_analista_bot_avisos.py -k "cuentan_uno or sin_ultimo_clic or infla_clics" -v
```

Verificación esperada:
Falla `test_dos_clics_a_2_s_cuentan_uno_y_a_6_s_cuentan_dos` porque `anotar_clic` devuelve `True` en el segundo clic y acumula `clics_boton == 2`.
Falla `test_el_doble_toque_del_boton_responde_al_usuario_y_no_infla_clics` con `assert 2 == 1`.

- [ ] **Step 3: Implementación mínima en `scripts/analista/avisos_semana.py`**

1. Definir constante `CLIC_REBOTE = 5` en `scripts/analista/avisos_semana.py`:
```python
CLIC_REBOTE = 5            # segundos: toques repetidos del botón dentro de esta ventana se consideran rebote
```

2. Inicializar el campo `"ultimo_clic"` en `anotar_envio`:
```python
    def anotar_envio(self, ejecutivo: str, aviso: Aviso, cuando: datetime, message_id: int | None) -> None:
        reg = {"id": aviso.id, "ejecutivo": ejecutivo, "tipo": aviso.tipo, "fecha": aviso.fecha,
               "evento": aviso.evento, "activo": aviso.activo, "cuando": cuando.isoformat(),
               "message_id": message_id, "clics_boton": 0, "votos": [], "oportunidad_24h": False,
               "ultimo_clic": None}
        self._mutar(lambda d: d["enviados"].append(reg))
```

3. Modificar `anotar_clic` para filtrar rebotes con `.get("ultimo_clic")`:
```python
    def anotar_clic(self, ejecutivo: str, id_: str, cuando: datetime) -> bool:
        def cambio(d):
            reg = next((r for r in d["enviados"] if r["ejecutivo"] == ejecutivo and r["id"] == id_), None)
            if reg is None:
                return False
            previo = reg.get("ultimo_clic")
            if previo is not None:
                dt = cuando - datetime.fromisoformat(previo)
                if timedelta(0) <= dt < timedelta(seconds=CLIC_REBOTE):
                    return False
            reg["clics_boton"] += 1
            reg["ultimo_clic"] = cuando.isoformat()
            return True
        return bool(self._mutar(cambio))
```

- [ ] **Step 4: Correr los tests y verificar PASS**

Ejecutar en Windows PowerShell:
```powershell
uv run pytest tests/test_analista_avisos_semana.py tests/test_analista_bot_avisos.py -k "cuentan_uno or sin_ultimo_clic or infla_clics" -v
```

Verificación esperada:
Los 3 tests pasan en verde.

- [ ] **Step 5: Correr la suite completa y contrato**

Ejecutar en Windows PowerShell:
```powershell
uv run pytest tests/test_analista_avisos_semana.py tests/test_analista_bot_avisos.py tests/test_analista_semana.py -q
uv run pytest tests/test_analista_avisos_semana.py -k "test_el_agendador_no_importa_el_envio_de_whatsapp" -v
uv run pytest -q
```

Verificación esperada:
Suite completa pasando en verde sin regresiones, y contrato de aislamiento respecto a WhatsApp validado.

- [ ] **Step 6: Commit**

Ejecutar en Windows PowerShell:
```powershell
git add scripts/analista/avisos_semana.py tests/test_analista_avisos_semana.py tests/test_analista_bot_avisos.py
git commit -m "fix(analista): ignorar rebote de clics del boton en menos de 5 segundos

Evita inflar la medicion de clics_boton si el ejecutivo presiona dos veces seguidas
el boton 'Ver analisis' dentro de la ventana de 5 segundos.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```
