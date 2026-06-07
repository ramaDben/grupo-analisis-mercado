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
