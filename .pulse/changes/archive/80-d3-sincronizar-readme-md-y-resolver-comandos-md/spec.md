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
