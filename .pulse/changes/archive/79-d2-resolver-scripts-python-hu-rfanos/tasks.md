# Tasks — D2 (#79): Resolver scripts Python huérfanos

## 1. Eliminar scripts huérfanos (7)
- [ ] 1.1 Borrar `scripts/orquestador.py`
- [ ] 1.2 Borrar `scripts/market_data.py`
- [ ] 1.3 Borrar `scripts/setup.py`
- [ ] 1.4 Borrar `scripts/_datos_entregables.py`
- [ ] 1.5 Borrar `scripts/guardar_mensaje.py`
- [ ] 1.6 Borrar `scripts/mt5_integration.py`
- [ ] 1.7 Borrar `scripts/formatter_whatsapp.py`

## 2. Sincronizar referencias vivas
- [ ] 2.1 `.claude/commands/chart.md:65` — quitar fallback al script borrado (mecanismo EA intacto → issue nuevo)
- [ ] 2.2 `CLAUDE.md` — árbol `scripts/`: dejar solo `senal_manager.py` + helpers `.ps1`
- [ ] 2.3 `README.md` (19, 86-88) — quitar `formatter` y `mt5_integration.py`
- [ ] 2.4 `docs/setup-guide.md` (8, 12, 31) — quitar refs a `formatter` y script legacy
- [ ] 2.5 `docs/design/apertura-interactiva.design.md:25` — corregir afirmación de capacidad stale

## 3. Issue de seguimiento
- [ ] 3.1 Crear issue: pipeline de charts propio (sin EA ajeno GI_ChartExporter)

## 4. Validación
- [ ] 4.1 `grep` 0 refs vivas a scripts borrados (comandos + docs usuario; COMANDOS.md diferido a D3)
- [ ] 4.2 `pytest` verde
- [ ] 4.3 Gate Pulse verde (6 linters exit 0)
