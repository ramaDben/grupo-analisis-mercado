# Tasks — D4 (#81): .gitignore efímera + convención de charts

## 1. .gitignore
- [ ] 1.1 Agregar `data/mt5_response.json`
- [ ] 1.2 Agregar runtime Pulse: `.pulse/state.sqlite`, `.pulse/state.sqlite-shm`, `.pulse/state.sqlite-wal`, `.pulse/audit.jsonl`

## 2. Convención de nombres de chart
- [ ] 2.1 Documentar en `chart.md` (PASO 4): `<activo_slug>_<TF>_<YYYY-MM-DD_HH-MM>.png`
- [ ] 2.2 Agregar regla en `CLAUDE.md` (junto a la convención de rutas de mensaje #45)

## 3. Validación
- [ ] 3.1 `git status` limpio (sin `.pulse/state.sqlite*`/`audit.jsonl`)
- [ ] 3.2 Convención documentada en chart.md + CLAUDE.md
- [ ] 3.3 Gate Pulse verde (cero código; pytest 11)
