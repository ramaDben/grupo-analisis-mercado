# Idea: `/apertura` — niveles ingresados manualmente por el director

## Problema
El comando `/apertura` (PASO 4) llama automáticamente a `mcp__market-data__get_asset_levels`
para obtener `price, s1, s2, r1, r2, rsi_14, atr_14, trend` desde MT5.

Esto no refleja el flujo real: **el director lee sus propios charts en MT5 y decide los niveles**.
El fetch automático impone niveles del MCP que pueden no coincidir con la lectura del director,
exige que MT5 esté abierto en ese instante exacto, y quita control sobre lo que se comunica al grupo.

## Solución propuesta
Reemplazar el PASO 4 (fetch automático) por un prompt interactivo donde el director ingresa
los niveles manualmente para cada activo: precio actual, R1, R2 (opcional), S1, S2 (opcional),
y el valor del indicador si eligió RSI o ATR en el PASO 3.

## Archivos afectados
- `.claude/commands/apertura.md` — solo el PASO 4

## Impacto
- **Mínimo**: la plantilla del PASO 5 y el resto del flujo quedan idénticos.
- Elimina la dependencia de que MT5 esté abierto durante la generación de apertura.
- El director gana control total sobre los niveles que se publican al grupo.

## Issue de referencia
https://github.com/bbenja11/grupo-analisis-mercado/issues/14
