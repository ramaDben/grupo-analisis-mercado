
<!-- change:79-d2-resolver-scripts-python-hu-rfanos -->
# Spec — D2 (#79): Resolver scripts Python huérfanos

## Requirements
- Cada script huérfano de `scripts/` queda **resuelto**: eliminado, o reubicado/refactorizado con justificación.
- Ninguna referencia viva (comando o doc de usuario) apunta a un script inexistente.
- Las utilidades vigentes quedan **autocontenidas** (sin imports a código borrado).

## Criterios de aceptación (issue #79)
- [ ] Cada script huérfano resuelto (eliminado o reubicado con nota).
- [ ] Ningún comando ni doc (de usuario) apunta a un script inexistente.

## Fuera de alcance
- `COMANDOS.md`: sus referencias a scripts legacy se resuelven en **D3 (#80)** (el issue pide coordinar con D3). Aquí solo se deja constancia.
- Design docs históricos (`docs/design/*.design.md`): registro de auditorías pasadas, no punteros vivos; se ajustan solo donde afirman una capacidad actual (no se reescribe historia).
- Traer los scripts supervivientes a la cobertura de `ruff` (hoy `scripts/` está en `extend-exclude`): follow-up fuera de D2.

## Verificación
- `grep` confirma 0 referencias vivas a scripts borrados en `.claude/commands/` y docs de usuario.
- Gate de cierre Pulse verde (6 linters exit 0).
- `pytest` verde (los tests viven en `tests/` y no importan `scripts/`).
