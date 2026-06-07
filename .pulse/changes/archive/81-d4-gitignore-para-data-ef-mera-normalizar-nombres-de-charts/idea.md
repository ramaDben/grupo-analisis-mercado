# Idea — D4 (#81)

Cerrar la higiene de `data/`: asegurar que el estado efímero (JSON de runtime + PNGs de charts) esté gitignored y fuera del índice, y definir una **convención única de nombres de chart** (hoy hay 3+ estilos inconsistentes). Reusar la misma regla de slug de activo que `ruta_mensaje.ps1` (#45) para consistencia sistémica. Bajo riesgo, cero código tocado. Ver `design.md`.
