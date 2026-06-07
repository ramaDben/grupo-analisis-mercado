
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

<!-- change:80-d3-sincronizar-readme-md-y-resolver-comandos-md -->
# Spec — D3 (#80): Sincronizar README.md y resolver COMANDOS.md

## Requirements
- `README.md` refleja el conteo real de comandos (**21**) y los lista todos.
- `README.md` muestra la estructura real del proyecto (post-#86 y post-D2).
- `README.md` describe el MCP `market-data` (`get_asset_levels`) como capa de datos.
- `COMANDOS.md` resuelto: eliminado (o actualizado) sin contradicciones con `CLAUDE.md`.

## Criterios de aceptación (issue #80)
- [ ] `README.md` refleja los 21 comandos y la estructura real.
- [ ] `COMANDOS.md` actualizado o eliminado (sin contradicciones con `CLAUDE.md`).

## Ground truth verificado (2026-06-07)
- `.claude/commands/*.md` = **21** archivos (no 18 ni 24).
- `agents/*.md` = 3 (`recolector`, `analista`, `redactor`). **No existe "ejecutivo"**.
- `COMANDOS.md`: **0 referencias** en el repo (huérfano).

## Fuera de alcance
- `docs/commands-reference.md`, `CLAUDE.md` (su tabla de 21 ya es correcta): no es D3.
- Reescribir el contenido educativo/operativo (solo docs de entrada).

<!-- change:81-d4-gitignore-para-data-ef-mera-normalizar-nombres-de-charts -->
# Spec — D4 (#81): .gitignore efímera + convención de charts

## Requirements
- `.gitignore` cubre todos los JSON de estado efímero de `data/` (incl. `mt5_response.json`).
- Ningún archivo efímero queda trackeado (ya cumplido para `data/`; verificar).
- Convención única de nombres de chart **documentada** y especificada para el generador.

## Criterios de aceptación (issue #81)
- [ ] `.gitignore` cubre los JSON efímeros de estado.
- [ ] Esos archivos dejan de estar trackeados (ya están fuera del índice).
- [ ] Convención de nombres de chart documentada y aplicada (especificada).

## Ground truth verificado (2026-06-07)
- Trackeado en `data/`: solo persistentes (`curriculo`, `entregas_educativas`, `historial_encuestas`, `historial_senales`, `mapa_conceptos`, `metricas_educativas`).
- Efímeros (`plan_hoy`, `datos_entregables`, `ultimo_analisis`, `ultimo_evento`, `mt5_command`): gitignored y **no trackeados**.
- Falta en `.gitignore`: `data/mt5_response.json`.
- Slug canónico de activo (`ruta_mensaje.ps1`): `lowercase(ticker_mt5)` sin `.spot`, `#`, `/`.

## Fuera de alcance
- Borrar PNGs locales inconsistentes de `data/charts/` (son local-only/gitignored, del director).
- Implementar el generador de charts (vive en #87); aquí solo se especifica la convención.
