# Configuración Global de Usuario (Gemini Added Memories)

- El usuario prefiere comunicarse siempre en español latinoamericano (Chile).
- El entorno de ejecución es Windows PowerShell (sí o sí). Evitar sintaxis de Bash como '&&' y usar comandos compatibles (ej. ';', 'Select-String', 'Get-Content').
- Para la generación de gráficos en las stories, utilizar estrictamente la temporalidad H1 y 60 velas por defecto, respetando la arquitectura de serie_mt5.py para asegurar la correcta proporción visual. Si se usan scripts alternativos (como yfinance), deben replicar este mismo rango temporal (1h) y volumen de datos.
- Para la generación de gráficos y Stories (flujo Opus), el agente debe:
  1. NO dejar archivos temporales en la raíz; usar siempre scripts\ruta_story.ps1 para guardar en data/stories/.
  2. Utilizar el pipeline encadenado por consola (serie_mt5 | story_grafico | story_render). **Para evitar corrupción de encoding (mojibake o signos '?') en Windows, NUNCA uses los pipes nativos o `Get-Content` de PowerShell para inyectar el JSON; el comando DEBE encapsularse a través de cmd.exe** (ej: `cmd.exe /c "type scratch\payload.json | uv run python scripts\serie_mt5.py ..."`).
  3. Llenar absolutamente todos los tokens del payload JSON, sin dejar strings vacíos que rompan el diseño ("espacios vacíos").
  4. Respetar estrictamente la tabla de decimales (digits) según CLAUDE.md.
