I am running the full test suite (`uv run pytest -q`) to verify baseline health before designing the implementation plan. I will wait for it to complete.
# `Bot.recibir_callback`: responder siempre a los callbacks de la alerta semanal (Menor 13). Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolver el defecto Menor 13 en `Bot.recibir_callback` (`scripts/analista/bot.py`): asegurar que toda interacción con botones en línea de la alerta semanal (prefijo `sw:`) que contenga un `callback_query.id` reciba exactamente una respuesta (`_responder_callback`), evitando que Telegram deje el botón con el spinner girando indefinidamente en salidas tempranas (usuario no autorizado, registro inexistente o expirado, botón `ped` sin activo o subsistema de avisos desactivado).

**Architecture:** Separación estructural en `Bot`: `recibir_callback` filtra inmediatamente si la actualización no tiene `id` o no pertenece al espacio de nombres de la alerta (`data` no inicia con `"sw:"`), en cuyo caso devuelve `[]` sin tocar el callback. Para todo callback `sw:` con `id`, delega a un método auxiliar privado `_procesar_callback_sw(cb) -> tuple[str, list[Respuesta]]`, el cual evalúa autorizaciones, estado del agendador, vigencia del registro y acciones de voto o pedido, retornando el texto de retroalimentación para Telegram y la lista de respuestas de mensajes a entregar. `recibir_callback` despacha `self._responder_callback(cb_id, texto_cb)` en un punto único e ineludible, garantizando exactamente una respuesta por callback.

**Tech Stack:** Python 3 (módulos `scripts/analista/bot.py`, `scripts/analista/avisos_semana.py`), pytest vía `uv run` en Windows PowerShell, API de Telegram Bot (`answerCallbackQuery`).

**Spec:** `docs/superpowers/specs/2026-10-18-alerta-semana-ejecutivos-design.md`, plan previo `docs/superpowers/plans/2026-10-18-alerta-semana-ejecutivos.md` y especificación del defecto Menor 13.

## Global Constraints

- **TDD estricto:** primero se escriben los tests unitarios que reproducen cada salida temprana sin responder, se verifica su fallo (`FAIL`), luego se implementa el código mínimo y se valida su pase (`PASS`).
- **Sin envíos a WhatsApp:** ningún módulo de `scripts/analista/` puede importar ni referenciar `enviar_whatsapp`, `whatsapp_sender`, `--despachar`, `despachar(`, `bitacora_despachos` ni `historial_despachos` (`tests/test_analista_bot.py::test_el_bot_no_puede_publicar_en_whatsapp`).
- **Texto para ejecutivos:** español de Chile, tuteo neutro, con tildes correctas, sin guion largo (`—`) ni guion medio (`–`) como inciso.
- **Idempotencia y unicidad:** todo callback con prefijo `sw:` y con `id` se responde exactamente una vez. Callbacks de otros prefijos no se tocan. Para usuarios no autorizados se responde con texto vacío sin registrar votos ni clics. Para registros inexistentes se responde `"Ese aviso ya no está disponible"`.
- **Ramas y git:** trabajar estrictamente en la rama `feat/alerta-semana-ejecutivos`. Nunca commitear a `master`, nunca hacer `push`. Todo commit debe finalizar con el trailer obligatorio `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- **Suite completa:** al terminar la tarea, verificar que toda la suite de pruebas pase (`uv run pytest -q`).

## Review Focus

1. **Garantía de respuesta única:** verificar que `_responder_callback` no se invoque múltiples veces ni se omita en ninguna rama condicional de `sw:`.
2. **Aislamiento de prefijos ajenos:** comprobar que callbacks que no inicien con `"sw:"` (e.g. `"otra:cosa"`) no llamen a `_responder_callback` y devuelvan `[]` de inmediato.
3. **No autorizados sin efectos colaterales:** asegurar que un toque de un usuario desconocido detenga el spinner en Telegram (`_responder_callback(cb_id, "")`) pero no registre votos ni clics en `avisos.json`.
4. **Respuesta en aviso inexistente:** comprobar que un callback hacia un ID inexistente informe `"Ese aviso ya no está disponible"` en Telegram y devuelva `[]` sin lanzar excepciones.

---

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `scripts/analista/bot.py` | Métodos `recibir_callback` y `_procesar_callback_sw` para garantizar respuesta única a callbacks `sw:` | Modificar |
| `tests/test_analista_bot_avisos.py` | Pruebas unitarias para todas las salidas de callbacks de alerta semanal | Modificar |

---

### Task 1: Responder exactamente una vez a todos los callbacks de la alerta semanal (Menor 13)

**Files:**
- Modify: `scripts/analista/bot.py:642-673`
- Modify: `tests/test_analista_bot_avisos.py:135-146`

**Interfaces:**
- Produces: `Bot.recibir_callback(update: dict[str, Any]) -> list[Respuesta]` responde mediante `_responder_callback(cb_id, texto)` exactamente una vez si `update["callback_query"]["data"]` inicia con `"sw:"` y tiene `id`. Devuelve `[Respuesta]` si corresponde encolar un pedido, o `[]` en caso contrario.
- Produces: `Bot._procesar_callback_sw(cb: dict[str, Any]) -> tuple[str, list[Respuesta]]` procesa la autorización, estado de avisos, registro en base y acción (`ped`, `util`, `no`), retornando la tupla `(texto_callback, respuestas)`.
- Consumes: `self._responder_callback(cb_id, texto)`, `self.avisos.registro(usuario, id_)`, `self.avisos.anotar_clic(...)`, `self.avisos.anotar_voto(...)`, `self.tg.quitar_teclado(...)`.

- [ ] **Step 1: Escribir los tests que fallan (código real)**

En `tests/test_analista_bot_avisos.py`, reemplazar las funciones existentes `test_un_callback_de_alguien_no_autorizado_se_ignora` y `test_un_callback_ajeno_o_viejo_no_rompe` (líneas 135 a 146) por las versiones con aserciones de respuesta y los nuevos casos de prueba:

```python
def test_un_callback_de_alguien_no_autorizado_se_ignora(con_avisos):
    a = aviso("mapa")
    con_avisos.bot.avisos.anotar_envio(CAMILA, a, LUNES, 901)
    assert con_avisos.bot.recibir_callback(callback(f"sw:util:{a.id}", usuario="999")) == []
    assert con_avisos.bot.avisos.registro(CAMILA, a.id)["votos"] == []
    assert con_avisos.bot.tg.callbacks == [("cb1", "")]


def test_un_callback_ajeno_o_viejo_no_rompe(con_avisos):
    assert con_avisos.bot.recibir_callback(callback("otra:cosa")) == []
    assert con_avisos.bot.tg.callbacks == []
    assert con_avisos.bot.recibir_callback(callback("sw:util:inexistente")) == []
    assert con_avisos.bot.tg.callbacks == [("cb1", "Ese aviso ya no está disponible")]


def test_un_callback_ped_sin_activo_responde_vacio(con_avisos):
    a = aviso("vispera", fecha="2026-10-20", activo=None)
    con_avisos.bot.avisos.anotar_envio(CAMILA, a, MARTES, 901)
    assert con_avisos.bot.recibir_callback(callback(f"sw:ped:{a.id}")) == []
    assert con_avisos.bot.tg.callbacks == [("cb1", "")]
    assert con_avisos.bot.cola.qsize() == 0


def test_un_callback_con_avisos_desactivados_responde_vacio(con_avisos):
    con_avisos.bot.avisos = None
    assert con_avisos.bot.recibir_callback(callback("sw:util:inexistente")) == []
    assert con_avisos.bot.tg.callbacks == [("cb1", "")]


def test_un_callback_sw_malformado_responde_vacio(con_avisos):
    assert con_avisos.bot.recibir_callback(callback("sw:invalido")) == []
    assert con_avisos.bot.tg.callbacks == [("cb1", "")]


def test_un_callback_sin_id_o_prefijo_ajeno_no_responde(con_avisos):
    sin_id = {"update_id": 2, "callback_query": {"from": {"id": int(CAMILA)}, "data": "sw:util:123"}}
    assert con_avisos.bot.recibir_callback(sin_id) == []
    assert con_avisos.bot.tg.callbacks == []
```

- [ ] **Step 2: Correr y ver que fallan (FAIL)**

Ejecutar:
```powershell
uv run pytest tests/test_analista_bot_avisos.py -q
```
Resultado esperado: FAIL (5 pruebas fallan debido a que `con_avisos.bot.tg.callbacks` queda vacío `[]`).

- [ ] **Step 3: Implementación mínima (código real)**

En `scripts/analista/bot.py`, reemplazar `recibir_callback` (líneas 642 a 673) por la estructura que garantiza respuesta única y el método auxiliar de procesamiento:

```python
    def recibir_callback(self, update: dict[str, Any]) -> list[Respuesta]:
        """Los toques de los botones de la alerta: voto Útil / No me sirve y el pedido de la víspera.

        Garantiza que todo callback_query con id y prefijo 'sw:' se responda exactamente una vez
        para que Telegram no deje el botón girando (Menor 13). Callbacks de otro prefijo no se tocan.
        """
        cb = update.get("callback_query") or {}
        cb_id = cb.get("id")
        data = str(cb.get("data") or "")
        if not cb_id or not data.startswith("sw:"):
            return []
        texto_cb, respuestas = self._procesar_callback_sw(cb)
        self._responder_callback(cb_id, texto_cb)
        return respuestas

    def _procesar_callback_sw(self, cb: dict[str, Any]) -> tuple[str, list[Respuesta]]:
        """Procesa la lógica de negocio del callback 'sw:' y devuelve (texto_a_responder, respuestas)."""
        usuario = str((cb.get("from") or {}).get("id", ""))
        if self.avisos is None or usuario not in self.config["analistas"]:
            return "", []

        msg = cb.get("message") or {}
        chat, message_id = (msg.get("chat") or {}).get("id"), msg.get("message_id")
        if not chat:
            return "", []

        partes = str(cb.get("data", "")).split(":")
        if len(partes) != 3 or partes[0] != "sw" or partes[1] not in ("util", "no", "ped"):
            return "", []

        _, accion, id_ = partes
        registro = self.avisos.registro(usuario, id_)
        if registro is None:
            return "Ese aviso ya no está disponible", []

        ahora = self.atendedor.reloj()
        if accion == "ped":
            if not registro.get("activo"):
                return "", []
            self.avisos.anotar_clic(usuario, id_, ahora)
            # El pedido del botón no pasa por `recibir`: ya cuenta como clic y no como pedido propio.
            return "Armando el análisis", self._encolar(
                usuario, chat, od.Orden("oportunidad", {"ticker": registro["activo"]})
            )

        voto = "util" if accion == "util" else "no_sirve"
        if self.avisos.anotar_voto(usuario, id_, voto, ahora):
            try:
                self.tg.quitar_teclado(chat, message_id)
            except Exception:  # noqa: BLE001  el teclado que queda no daña: el voto ya está anotado
                _log(f"no pude quitar el teclado: {traceback.format_exc()}")
            return "¡Gracias!", []

        return "Ya votaste este aviso", []
```

- [ ] **Step 4: Correr y ver que pasan (PASS)**

Ejecutar:
```powershell
uv run pytest tests/test_analista_bot_avisos.py -q
```
Resultado esperado: PASS (todas las 21 pruebas de `test_analista_bot_avisos.py` pasan en verde).

- [ ] **Step 5: Correr la suite completa y contrato de WhatsApp**

Ejecutar:
```powershell
uv run pytest tests/test_analista_bot.py tests/test_analista_bot_avisos.py -q
uv run pytest -q
```
Resultado esperado: PASS (suite completa en verde, verificando que ningún módulo importe el envío a WhatsApp).

- [ ] **Step 6: Commit**

Ejecutar:
```powershell
git status
git add scripts/analista/bot.py tests/test_analista_bot_avisos.py
git commit -m "fix(analista): responder exactamente una vez a callbacks de la alerta semanal (Menor 13)

Garantiza que todo callback_query con id y prefijo 'sw:' invoque _responder_callback
evitando que Telegram deje el boton girando en salidas tempranas (no autorizado,
aviso viejo o inexistente, boton ped sin activo o avisos desactivados).

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```
