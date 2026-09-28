# Medición: dirección de cuatro ejes contra la EMA 50

Generado 2026-09-28 09:05 (hora Chile) por `scripts/medir_direccion.py`. Spec: `docs/superpowers/specs/2026-09-28-direccion-4-ejes-design.md`, §5. Umbrales fijos de `config/direccion.json`: no se ajustaron mirando este resultado.

## Adopción

**Veredicto: no se adopta** (requiere 1, 2 y 3).

| Condición | Resultado | Números |
|---|---|---|
| 1. Acierto direccional | cumple | modelo 50.4 vs EMA 50 50.4; diferencia -0.0 pts, IC [-0.9, 0.8] |
| 2. LATERAL aparta ruido | no cumple | EMA 50 en LATERAL 49.1 vs resto 50.4, IC [-4.1, 1.6]; mediana abs(m) 0.9 vs 0.9 |
| 3. Estabilidad | cumple | giros cada 100: modelo 7.8 vs EMA 50 con histéresis 10.9 |
| 4. Convicción ordena | no cumple | debil 50.9, moderada 48.3, fuerte 51.3 |

Activos disidentes (conservan la EMA 50): ninguno. Con menos de 500 instantes, reportados sin voto: ninguno.

## Por activo (instantes que votan)

| Activo | Votos | Días | Modelo | EMA 50 | Dif. (IC) | Giros modelo / EMA 50 | Paridad EMA 100 (ATR) |
|---|---|---|---|---|---|---|---|
| XAUUSD | 2560 | 433 | 51.4 | 51.9 | -0.5 [-2.6, 1.5] | 7.7 / 10.8 | 0.002 |
| WTI | 2447 | 436 | 50.3 | 51.4 | -1.2 [-3.5, 1.2] | 8.9 / 12.1 | 0.008 |
| US100 | 1792 | 451 | 55.6 | 55.6 | 0.0 [-2.1, 2.1] | 9.9 / 12.5 | 0.002 |
| USDCLP | 4142 | 1104 | 47.8 | 47.9 | -0.1 [-1.7, 1.6] | 6.0 / 9.3 | 0.005 |
| COPPER | 2670 | 833 | 49.6 | 48.2 | 1.4 [-0.9, 3.7] | 8.5 / 11.2 | 0.003 |
| USDIDX | 2437 | 493 | 49.3 | 49.0 | 0.3 [-2.2, 2.8] | 8.2 / 11.4 | 0.008 |
| BRENT | 761 | 129 | 54.7 | 55.6 | -0.9 [-4.6, 2.9] | 6.3 / 8.5 | 0.007 |

## Dónde cae la muestra

El horizonte de 4 velas tiene que ser contiguo. En los activos con pausa diaria (oro y petróleo a las 17:00 NY) o sesión corta (USD/CLP), eso descarta las velas de la tarde: **el veredicto describe sobre todo la mañana**. Por hora NY de cierre, sumando todos los activos:

| Hora NY | Votan | Descartadas por hueco |
|---|---|---|
| 08:00 | 2890 | 118 |
| 09:00 | 2955 | 161 |
| 10:00 | 3542 | 468 |
| 11:00 | 3056 | 945 |
| 12:00 | 2342 | 1553 |
| 13:00 | 1651 | 2277 |
| 14:00 | 373 | 2827 |
| 15:00 | 0 | 2651 |
| 16:00 | 0 | 1926 |

**Sensibilidad:** tolerando hasta 2 h de hueco en el horizonte votan 19158 instantes y el veredicto es **no se adopta** (1 cumple, 2 no cumple, 3 cumple, 4 no cumple).

## Fuera de sesión (no vota)

| Activo | Instantes | Modelo | EMA 50 |
|---|---|---|---|
| XAUUSD | 5542 | 50.5 | 50.7 |
| WTI | 5647 | 49.0 | 49.0 |
| US100 | 6488 | 52.0 | 51.1 |
| USDCLP | 536 | 46.0 | 44.9 |
| COPPER | 3818 | 49.3 | 49.2 |
| USDIDX | 5437 | 49.3 | 49.5 |
| BRENT | 1472 | 50.4 | 50.7 |

## Descartes

| Activo | Motivo | Instantes |
|---|---|---|
| XAUUSD | fuera_de_sesion | 5982 |
| XAUUSD | hora_ambigua | 0 |
| XAUUSD | horizonte_con_hueco | 1308 |
| WTI | fuera_de_sesion | 5966 |
| WTI | hora_ambigua | 0 |
| WTI | horizonte_con_hueco | 1437 |
| US100 | fuera_de_sesion | 6649 |
| US100 | hora_ambigua | 0 |
| US100 | horizonte_con_hueco | 64 |
| US100 | horizonte_corto | 1345 |
| USDCLP | fuera_de_sesion | 1198 |
| USDCLP | hora_ambigua | 0 |
| USDCLP | horizonte_con_hueco | 4506 |
| USDCLP | sin_futuro | 4 |
| COPPER | fuera_de_sesion | 3830 |
| COPPER | hora_ambigua | 0 |
| COPPER | horizonte_con_hueco | 3349 |
| COPPER | sin_futuro | 1 |
| USDIDX | fuera_de_sesion | 5538 |
| USDIDX | hora_ambigua | 0 |
| USDIDX | horizonte_con_hueco | 1871 |
| USDIDX | sin_futuro | 4 |
| BRENT | fuera_de_sesion | 1601 |
| BRENT | hora_ambigua | 0 |
| BRENT | horizonte_con_hueco | 391 |
| BRENT | sin_historia_d1 | 2169 |

## Verificación de la zona horaria

Las marcas se leyeron como hora de Santiago (§5.4). Las dos pruebas pasaron; si no, este informe no existiría.

- XAUUSD: aplica. ultima vela 05:00, extraccion 05:20 (Santiago)
- WTI: aplica. ultima vela 05:00, extraccion 05:20 (Santiago)
- US100: aplica. ultima vela 05:00, extraccion 05:21 (Santiago)
- USDCLP: no aplica. ultima vela 2026-09-25 15:00, extraida 2026-09-28 05:20: mercado cerrado
- COPPER: aplica. ultima vela 05:00, extraccion 05:21 (Santiago)
- USDIDX: no aplica. ultima vela 2026-09-25 16:00, extraida 2026-09-27 19:21: mercado cerrado
- BRENT: aplica. ultima vela 05:00, extraccion 05:20 (Santiago)
- Pico de volumen de US100: 10:00 NY en 23 meses.
