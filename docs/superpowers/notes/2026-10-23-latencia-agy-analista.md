# Latencia de agy en el análisis del bot (2026-10-23)

## Qué se midió
Tiempo de redacción de agy para `/oportunidad`, con el tier `flash` (Gemini 3.8 Flash High) y `flash-lo`/`md` como alternativas. Medición del 2026-10-23 con tres activos (oro, USD/CLP y GBP/USD) sobre copias de `pieza.json`.

## Tiempos (segundos)

| Activo  | High  | Medium |
|---------|-------|--------|
| Oro     | 488   | 393    |
| USD/CLP | 403   | 431    |
| GBP/USD | 660   | 495    |

Promedio: Medium unos 15 % más rápido que High, dentro de la variación normal de High. El rango medido en las 14 corridas reales del 19 al 23-10 es de 270 a 927 s, con mediana cercana a 570 s.

## Low descartado
Flash Low copió el texto de los originales en 2 de 3 pedidos, y el tercero salió sin fuente. No sirve para redactar.

## Medium
Se midió en una corrida aislada, con los originales apartados. Redactó las 3 piezas de verdad y las 3 pasaron `bot_analistas.py --validar`. La calidad se leyó como equivalente a High.

## Duración total registrada por agy
Los `agy_salida_1.json` de `data/informes_analistas/2026-10-19/` (oportunidad de SOXX.US, XAUUSD y XAUUSD) registran solo el total en `segundos`: 526, 659 y 270. No separan búsqueda de fuentes, redacción ni validación; esa separación no se pudo hacer con la bitácora disponible.

## Decisión del director (2026-10-23)
Se queda Flash High. No se cambia el tier por defecto (`scripts/agy_encargo.py`).

## Consecuencia en el bot
El mensaje de `/oportunidad` dice "demora unos 10 minutos", cifra que resume la mediana medida y no una promesa.
