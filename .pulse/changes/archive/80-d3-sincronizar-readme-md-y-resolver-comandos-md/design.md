# Diseño — D3 (#80): Sincronizar README.md y resolver COMANDOS.md

**Épico:** #66 · **Dominio:** higiene-repo · **Bump:** patch (type:chore)

## Ground truth verificado (2026-06-07)
- **21 comandos** reales en `.claude/commands/`: domingo, lunes, martes, miercoles, jueves, viernes_am, viernes_pm, encuesta, rencuesta, curriculo, apertura, dato_macro, noticia, chart, señal, alerta, concepto, pregunta, estado, accion, earnings. → El issue dice "24" (sobreconteo); README dice "18" (le faltan **apertura, curriculo, rencuesta**). Voy con **21** (coincide con `CLAUDE.md`).
- 3 agentes (`recolector`, `analista`, `redactor`). **No existe "ejecutivo"** (el issue lo menciona, pero no hay tal comando/agente) → se omite.
- `COMANDOS.md`: **0 referencias** en el repo. Huérfano.

## Cambios

### 1. `README.md` — sincronización
- **Conteo + tabla de comandos**: "18 Slash Commands" → "21 Slash Commands"; agregar las 3 filas faltantes (`/apertura`, `/curriculo`, `/rencuesta`) con su propósito; alinear descripciones con `CLAUDE.md`.
- **Árbol "Estructura del proyecto"**: reescribir a la realidad post-#86/D2:
  - `src/market_data_mcp/` (MCP, antes `market_data_mcp/` en raíz) + `tests/`.
  - `scripts/`: solo `senal_manager.py` + `hora_chile.ps1` + `ruta_mensaje.ps1` (post-D2).
  - agregar `conceptos/`, `pyproject.toml`, y los `data/` reales (`historial_senales.json`, `curriculo.json`, `mapa_conceptos.json`, etc.).
- **Sección MCP**: dejar claro que `market-data` expone **solo** `get_asset_levels`; calendario/noticias vía WebSearch (consistente con `CLAUDE.md`/`estado.md` de D1).
- **Instalación**: ajustar el snippet `pip install ...` para que no mienta (el toolchain de dev es uv+pyproject, D5; MT5 lo requiere el MCP en la máquina del director) — referencia a `docs/setup-guide.md` para el detalle.
- **Requisitos** (línea 19, ya tocada en D2): coherente con scripts reales.

### 2. `COMANDOS.md` — **eliminar** (decisión del checkpoint)
Huérfano (0 refs), legacy y contradictorio: referencia scripts borrados (`orquestador`, `setup`, `mt5_integration`, `senal_manager` vía `python scripts/...`), el pipeline de charts ajeno y "4H/1H" hardcodeado (contra #43/#44). La operativa real son los slash commands; `CLAUDE.md` (tabla de 21) y `docs/commands-reference.md` ya la cubren. **Recomendación: borrar.** Alternativa: reescribirlo a un puntero de una línea ("usa los slash commands, ver CLAUDE.md") — redundante.

## Verificación
- README: conteo = 21 y las 21 filas presentes; árbol sin rutas inexistentes; sin `market_data_mcp/` en raíz.
- `grep` post-cambio: 0 referencias a `COMANDOS.md` rotas (era 0; sigue 0 tras borrarlo).
- Gate Pulse verde (cero código tocado → linters intactos; pytest 11).

## Criterios de aceptación (#80)
- [ ] `README.md` refleja los 21 comandos y la estructura real.
- [ ] `COMANDOS.md` resuelto (eliminado), sin contradicciones con `CLAUDE.md`.
