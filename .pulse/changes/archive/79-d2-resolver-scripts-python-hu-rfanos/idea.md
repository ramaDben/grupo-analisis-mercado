# Idea — D2 (#79)

Resolver los scripts Python huérfanos de `scripts/`: código legacy que ya no invoca ningún comando (la operativa migró a los slash commands + MCP market-data + helpers PowerShell). Eliminar la deuda muerta y dejar `scripts/` con solo utilidades vigentes, sin que ningún comando ni doc apunte a un script inexistente. Bajo riesgo, alto valor de claridad. Ver `design.md` para el detalle verificado por script.
