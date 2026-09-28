# Dirección técnica de cuatro ejes — Fase 1: modelo en sombra y medición

- **Fecha:** 2026-09-28 (revisión 2, tras la revisión cruzada de Gemini 3.8 Flash High)
- **Estado:** aprobado en conversación por el director; pendiente de revisión del spec escrito
- **Rama:** `feat/direccion-4-ejes`, apilada sobre `feat/retirar-playbook-v2` (aún sin PR). `direccion_tecnica` existe solo en esa rama.
- **Fase 2 (adopción):** spec aparte, que se escribe **solo si esta fase pasa la regla de adopción** y con sus números a la vista.

## 1. Problema

La dirección de toda pieza es hoy una sola línea (`scripts/screener_gi.py`, `direccion_tecnica`):
`ALCISTA si precio >= EMA 50 de H1, si no BAJISTA`. Tiene tres defectos:

1. **Nunca devuelve LATERAL**, aunque la regla de oro admite alcista / bajista / lateral. Un activo en
   rango sale "alcista" por estar un centavo sobre la media.
2. **Solo mira H1**: no distingue una tendencia de fondo de una corrección dentro de ella.
3. **No informa convicción**: pegado a la media o lejos de ella, la pieza dice lo mismo.

Además conviven **tres criterios de dirección**: `direccion_tecnica` (EMA 50 de H1), la misma función
aplicada a D1 en `pipeline_informe._frase_tecnica`, y `trend` de `analisis.py` (contra la EMA 100). Esta
fase no los unifica: lo hace la fase 2.

Todo lo que el modelo necesita **ya se calcula** en `get_asset_levels` para H1 y D1 (`ema_20`, `ema_50`,
`ema_100`, `donchian_50_high`, `donchian_50_low`, `adx_14`, `atr_14`, y en D1 `rango_hoy` y
`fecha_barra`), y el escáner ya pide los dos marcos.

## 2. Principio de diseño: ejes independientes, no votos

EMA, MACD y RSI salen del mismo cierre suavizado: si votaran juntos, "4 de 4" sería la misma señal
contada cuatro veces, la confianza inflada que hundió al Playbook V2. El modelo usa ejes que miden cosas
distintas, cada uno con un rol, combinados por un **árbol de reglas explícito** (se descartaron un
puntaje ponderado, por sus pesos mágicos, y la mayoría de votos, que pierde la corrección dentro de
tendencia). La rama del árbol **es** el motivo que lee el cliente.

| Eje | Pregunta | Con qué | Rol |
|---|---|---|---|
| 1. Fondo | ¿Hacia dónde va en días? | D1: precio vs `ema_50`, `ema_50` vs `ema_100` | Ancla |
| 2. Día | ¿Qué hace hoy? | H1: precio vs `ema_50` + posición en el Donchian 50 | Confirma o marca corrección |
| 3. Fuerza | ¿Tendencia o rango? | `adx_14` de H1 | Decide LATERAL, la convicción y el desempate de la corrección |
| 4. Espacio | ¿Le queda recorrido hoy? | consumo ATR diario (`rango_hoy / atr_14` de D1) | **Solo texto** |

**El ADX no vota dirección**: mide fuerza, sube igual en una caída que en una subida.

**El eje 4 no cambia ni la dirección ni la convicción.** El consumo de ATR ya pesa en el escáner como
`gate_agotamiento` y como `factor_espacio`; usarlo acá también lo contaría tres veces.

## 3. Las reglas

Todos los indicadores, en vivo y en la medición, son **de velas cerradas**: `analizar_activo` los calcula
sobre `df_closed = df.iloc[:-1]` (`analisis.py:223`) y compara el precio en curso contra esos valores.

Notación: `p = (precio − donchian_50_low) / (donchian_50_high − donchian_50_low)` en H1. Como el canal es
de velas cerradas, **`p` sale de [0, 1] en un quiebre**: `p > 1` es un precio sobre el máximo de 50 velas
y `p < 0` bajo el mínimo. Es un estado válido, no un error, y el árbol lo trata (§3.1). Con
`high == low`, `p` no se puede calcular y la lectura cae a `datos_incompletos`.

**Eje 1 (D1):**
- `alcista` si `precio > ema_50` **y** `ema_50 > ema_100`
- `bajista` si `precio < ema_50` **y** `ema_50 < ema_100`
- `transicion` en cualquier otro caso

**Eje 2 (H1):** `alcista` si `precio > ema_50`, `bajista` si `precio < ema_50` (con la histéresis de §3.2).
El canal **confirma** el lado si `p ≥ 0,6` (alcista) o `p ≤ 0,4` (bajista); un quiebre (`p > 1` o `p < 0`)
confirma el lado del quiebre.

### 3.1 Árbol (gana la primera rama que calce)

| # | Condición | Dirección | Convicción | Fase |
|---|---|---|---|---|
| 0 | falta un campo o `p` no calculable | la de H1 | débil | `datos_incompletos` (nombra el campo) |
| 1 | `ADX < 20` **y** `0,3 ≤ p ≤ 0,7` | LATERAL | — | `rango` |
| 2 | D1 y H1 del mismo lado | la común | ver abajo | `tendencia_alineada` |
| 3a | D1 y H1 opuestos, `ADX ≥ 25` | la de H1 (el día) | moderada | `correccion_con_fuerza` |
| 3b | D1 y H1 opuestos, `ADX < 25` | la de D1 (el fondo) | débil | `correccion` |
| 4 | D1 en `transicion` | la de H1 | débil | `sin_ancla` |

**Convicción de la rama 2**, para que las tres clases salgan de la misma vara de fuerza:
- `fuerte`: `ADX ≥ 25` **y** el canal confirma
- `moderada`: `20 ≤ ADX < 25`, o `ADX ≥ 25` sin confirmación del canal
- `debil`: `ADX < 20` (alineación sin fuerza, con el precio fuera de la zona media del canal)

**Cobertura del árbol**: el eje 1 tiene tres estados y el eje 2 dos, así que hay seis combinaciones, más
la rama 1, que se evalúa antes y las corta a todas. `transicion` va a la 4 con cualquier H1; mismo lado
va a la 2; lados opuestos van a la 3a o a la 3b según el ADX. Un test recorre las seis combinaciones por
los dos lados de cada umbral y verifica que cada una caiga en **exactamente una** rama.

Decisión del director para la rama 3: con fuerza manda el día; sin fuerza manda el fondo, y el texto
dice que corrige dentro de la tendencia y que se vigila el soporte (o la resistencia) para retomar.

**Marca `sin_recorrido`**, encima de cualquier rama: consumo de ATR diario `≥ 0,70`. Aplica la misma
regla de `fecha_barra` que el escáner: si la vela D1 es de un día anterior, el consumo es 0.

**Empate exacto** `precio == ema_50` en H1 sin dirección previa: se resuelve alcista, igual que
`direccion_tecnica` hoy.

### 3.2 Histéresis

`leer_direccion(h1, d1, previa=None)`. `previa` es la dirección **del eje 2** (H1) de la lectura
anterior, siempre `ALCISTA` o `BAJISTA`: el eje 2 nunca es LATERAL, porque LATERAL lo decide la rama 1 y
no el eje. Con `previa`, el eje 2 solo cambia de lado si el precio cruza la EMA 50 de H1 por **más de
0,25 × ATR 14 de H1**. Sin `previa`, el eje 2 se lee sin histéresis. La función no guarda estado.

**En la sombra la histéresis no actúa**: el escáner no guarda lecturas entre corridas, así que llama con
`previa=None`. Es deliberado: la fase 1 no agrega estado al escáner. La histéresis se ejerce en la
medición (que recorre la serie en orden) y, en la fase 2, en el despacho, donde la dirección anterior ya
viaja en el payload.

### 3.3 Umbrales

Viven en `config/direccion.json`, cada uno con su nota de origen. **Fijos en esta fase: no se ajustan
mirando el resultado de la medición.**

| Clave | Valor | Origen |
|---|---|---|
| `adx_rango` | 20 | Corte convencional de "sin tendencia"; mismo valor que el piso del gate ADX de oportunidad, que se aplica al ADX diario (acá es el de H1) |
| `adx_fuerza` | 25 | Umbral de `factor_momentum` para "expansión" |
| `p_rango` | [0,3, 0,7] | Tercio central ampliado del canal |
| `p_confirma` | 0,6 / 0,4 | Fuera de la mitad del canal por un décimo |
| `histeresis_atr` | 0,25 | Un cuarto de la vela típica de H1 |
| `consumo_sin_recorrido` | 0,70 | Corte de puntuación de `factor_espacio` (`screener_gi.py:645-651`), donde sobre 0,70 el espacio deja de valer los 20 puntos |

Si más adelante se quisiera calibrarlos, se ajustan con el 70 % más antiguo de la historia y se validan
con el 30 % más reciente. Reportar un ajuste hecho sobre toda la historia sería medir el ajuste.

## 4. Componentes

### 4.1 `scripts/direccion_gi.py` (nuevo, puro)

- `leer_direccion(h1: dict, d1: dict, previa: str | None = None) -> LecturaDireccion`
- `LecturaDireccion` (dataclass congelada): `direccion` (`ALCISTA` | `BAJISTA` | `LATERAL`),
  `conviccion` (`fuerte` | `moderada` | `debil` | `None` en rango), `fase`, `sin_recorrido: bool`,
  `eje2` (la dirección de H1 tras la histéresis, para pasarla como `previa` a la lectura siguiente),
  `motivo` (una línea en voz de cliente, sin guion largo), `ejes` (lectura cruda de cada eje, para auditar).
- Solo stdlib; los umbrales se leen de `config/direccion.json`. Sin MT5, sin red.
- Recibe los dicts con los nombres reales de `analizar_activo` (`donchian_50_high`, `donchian_50_low`,
  `adx_14`, `atr_14`, `ema_50`, `ema_100`, `rango_hoy`, `fecha_barra`, `price`).

### 4.2 Sombra en el escáner

`screener_gi.evaluar_activo` agrega `direccion_4ejes` (la lectura serializada) junto a `direccion`. **La
`direccion` actual sigue siendo la que puntúa, pinta el chip y alimenta el guardia de divergencia**:
nada de lo que sale al cliente cambia. El resumen de la tanda imprime una línea por activo cuando ambas
difieren. Si `leer_direccion` lanza, el escáner anota el aviso y sigue: **la sombra nunca tumba la tanda**.

### 4.3 `scripts/medir_direccion.py` (nuevo)

Recorre la historia y compara el modelo contra la EMA 50 sola. Detalle en §5.

## 5. La medición

### 5.1 Datos y cobertura real

Series `data central/DATA PRECIOS OHLC/<ACTIVO>_{H1,D1}.json`, medidas el 2026-09-28:

| Activo | H1 | D1 |
|---|---|---|
| XAUUSD | 10.000 desde 2025-01-14 | 6.888 desde 2004-06-11 |
| WTI | 10.000 desde 2025-01-09 | 2.711 desde 2018-01-11 |
| US100 | 10.000 desde 2024-11-26 | 749 desde 2024-05-07 |
| USDCLP | 10.000 desde 2021-08-27 | 3.233 desde 2013-06-23 |
| COPPER | 10.000 desde 2023-02-03 | 1.947 desde 2019-07-05 |
| USDIDX | 10.000 desde 2024-10-17 | 1.165 desde 2023-01-02 |
| BRENT | 5.072 desde 2025-10-05 | 307 desde 2025-10-05 |

Un instante de H1 solo es medible si en ese momento hay al menos **150 velas D1 cerradas** (el mínimo de
`analizar_activo`) y 150 velas H1 cerradas. Brent, con 307 velas D1, deja una ventana corta: se mide y se
reporta, pero con menos de 500 instantes en sesión no vota (§5.6).

### 5.2 Paridad con `analizar_activo`

- Los indicadores se **recalculan desde el OHLC con las funciones de `market_data_mcp.mt5_client`**
  (`ema`, `atr`, `adx`), importables sin MT5. No se usan las columnas precalculadas de los JSON: no traen
  `ema_100` ni ADX, y otra fórmula sería otro modelo.
- El Donchian no tiene versión en serie (`mt5_client.donchian` devuelve solo el último valor): se calcula
  con `rolling(50)` sobre `high` y `low`, la misma fórmula, y un test compara ambas en el último valor.
- `ema`, `atr` y `adx` son recursivas (`adjust=False`): se calculan una vez sobre la serie completa y se
  leen en la posición que corresponda, sin fuga del futuro.
- **En el instante `t` (una vela H1), los indicadores de H1 se leen en la vela `t−1`**, que es la última
  cerrada, y el precio es el cierre de `t`. Así replica a `analizar_activo`, que evalúa el precio en curso
  contra niveles de velas ya cerradas. Leerlos en `t` metería el cierre de `t` dentro de sus propios
  indicadores.
- **Límite de la paridad:** en vivo, `analizar_activo` pide una ventana finita de velas y su EMA 100
  arranca con menos historia. El informe mide la diferencia en las últimas velas en vez de suponerla.

### 5.3 Punto en el tiempo del marco diario

- Los indicadores de D1 se leen en el **último día cerrado antes del día de `t`**, igual que
  `analizar_activo` con `df_closed` en D1.
- **`rango_hoy` no se lee de la vela D1 del día de `t`**: esa vela ya contiene el día completo y sería una
  fuga del futuro. Se reconstruye como `max(high) − min(low)` de las velas H1 del mismo día de `t`, desde
  la primera hasta `t` inclusive, que es lo que en vivo vería la vela D1 en curso a esa hora.

### 5.4 Hora: las marcas son hora de Santiago, no UTC

**Medido el 2026-09-28**: las series declaran `"timezone": "UTC"`, pero sus marcas son **hora local de
Santiago**. La última vela de cada serie, rotulada 05:00, se extrajo a las 05:20 de Santiago (08:20 UTC).
Y la vela de mayor `tick_volume` del US100, que es la de las 10:00 de Nueva York (la primera hora completa
tras la apertura), cae en la hora 12 de noviembre a febrero, en la 11 en marzo y en septiembre-octubre, y
en la 10 de abril a agosto: exactamente los tres regímenes que producen los cambios de horario de Chile y
de EE.UU. combinados.

Por eso la medición **no deriva un desfase constante** (un solo número no existe: se mueve dos horas en el
año). Hace esto:

1. **Interpreta cada marca como `America/Santiago`** y la convierte a `America/New_York` con `zoneinfo`.
2. **Verifica la hipótesis antes de medir**, con dos pruebas independientes, y **aborta si alguna falla**:
   - en las series **cuyo mercado estaba abierto al extraer** (última vela del mismo día que `as_of_utc`),
     esa última vela cae dentro de la hora de extracción convertida a Santiago. Las que terminan en un día
     anterior (USDCLP y USDIDX el lunes 28, cuyo último dato es el viernes) no entran en esta prueba: su
     mercado estaba cerrado y no dicen nada de la zona;
   - convertida a Nueva York, la moda mensual de la vela de mayor volumen del US100 es **la misma hora NY
     todos los meses**. Se usa la moda del mes y no cada día, porque los días de dato de las 08:30 o de la
     Fed desplazan el pico sin que cambie la zona. **Verificado el 2026-09-28: las 10:00 NY en los 23 meses
     disponibles, sin excepción**, transiciones de horario incluidas.
3. **Las horas ambiguas del cambio de horario de Chile** (la hora que se repite en abril y la que no existe
   en septiembre) se descartan de la medición, con el conteo en el informe. Resolverlas por el orden de las
   filas sería suponer algo que el archivo no dice.

**Hallazgo fuera del alcance, que se registra como issue aparte:** el sello `"timezone": "UTC"` es falso, y
todo consumidor que filtre estas series por hora lo lee corrido entre 3 y 4 horas.

### 5.5 Qué instantes votan

- Las ventanas salen de `config/agenda_mercado.json` (sesiones `apertura_ny` y `tarde_ny`, más la tanda
  de pre-cierre de las 16:45). **Ninguna hora se escribe en el script.** Como las velas H1 cierran en
  punto, cada ventana se lleva a las velas H1 cerradas que tiene a la vista una pieza preparada en ella:
  las que cierran entre las **08:00 y las 16:00 NY**, días hábiles.
- **Por clase**, igual que los momentos: divisas, metales, energía y USDIDX desde la vela de las 08:00;
  **US100 desde la de las 10:00**, con el horizonte cortado al cierre de las 16:00.
- **Horizonte mínimo de 3 horas para votar.** Un instante del US100 con 1 o 2 horas hasta el cierre casi
  no puede moverse, y eso infla cualquier medida de "se quedó quieto". Se reporta, no vota.
- **Fuera de sesión se mide y se reporta aparte, sin votar en la adopción.**

### 5.6 Qué se mide

Sea `m = (close[t+h] − close[t]) / ATR14_H1[t−1]`, con `h = 4` velas (o hasta el cierre en US100, con
`h ≥ 3`).

**Acierto direccional.** Una lectura ALCISTA acierta si `m > 0`; BAJISTA si `m < 0`.

**LATERAL no compite por acertar una dirección: compite por apartar las velas donde dar dirección no
sirve** (decisión del director). Se mide con dos cosas, ninguna de las cuales es un "acierto de LATERAL":
- el acierto direccional de la EMA 50 **en las velas que el modelo marcó LATERAL**, contra su acierto en el
  resto de las velas;
- la mediana de `|m|` en las velas LATERAL, contra la mediana de `|m|` en las velas con dirección.

**Giro.** Solo cuenta como giro el paso de ALCISTA a BAJISTA o de BAJISTA a ALCISTA, entre dos lecturas
direccionales consecutivas (ignorando las LATERAL intermedias). Entrar o salir de LATERAL no es un giro:
es justamente lo que evita que el chip dé vuelta en un rango.

**Incertidumbre.** Toda diferencia se reporta con su intervalo de confianza del 95 % por bootstrap
**agrupado por día** (las velas de un mismo día no son independientes, y remuestrearlas sueltas achica el
intervalo en falso).

### 5.7 Regla de adopción (fijada antes de ver números)

Se evalúa por activo y en total, solo con los instantes que votan (§5.5). El modelo se adopta en el total
si se cumplen **1, 2 y 3**:

1. **Acierto direccional:** en las velas donde el modelo da dirección, su acierto es mayor o igual al de la
   EMA 50 en esas mismas velas. "Mayor o igual" significa que el límite inferior del intervalo de la
   diferencia (modelo menos EMA 50) es mayor o igual a −1 punto.
2. **LATERAL aparta ruido:** en las velas LATERAL, la EMA 50 acierta **menos** que en el resto (el límite
   superior del intervalo de esa diferencia es menor que 0), **y** la mediana de `|m|` es menor que en las
   velas con dirección.
3. **Estabilidad:** el modelo tiene menos giros cada 100 velas que la EMA 50 **con la misma histéresis de
   0,25 ATR**, para que no gane por la histéresis sino por los ejes.

Y aparte:

4. **Convicción:** se publica en la fase 2 solo si el acierto direccional es monótono
   (`debil < moderada < fuerte`). Si no ordena el acierto, es decoración: la dirección puede adoptarse
   sin ella.
5. **Activos disidentes** (decisión del director): decide el total. Un activo con **al menos 500 instantes
   que votan** cuyo acierto direccional quede **más de 2 puntos bajo** el de la EMA 50 se excluye de la
   fase 2 y conserva la EMA 50. Un activo con menos de 500 instantes se reporta y no vota, ni en el total
   ni en su propia exclusión.

### 5.8 Salida

`docs/mediciones/direccion-4-ejes.md` (informe por activo y total, dentro y fuera de sesión, verificación
de la zona horaria, instantes descartados por hora ambigua o por horizonte corto, paridad de la EMA 100,
y el veredicto de cada condición de §5.7) y el JSON crudo al lado.

## 6. Errores

| Situación | Comportamiento |
|---|---|
| Falta un campo en h1/d1, o `p` no calculable | Fase `datos_incompletos`, nombra el campo; nunca una lectura completa inventada |
| `leer_direccion` lanza dentro del escáner | Aviso en la tanda, sigue con la dirección actual |
| Falla alguna de las dos pruebas de zona horaria (§5.4) | La medición aborta con el detalle |
| Serie que no salió de MT5 o de la cuenta declarada | La medición aborta (mismo criterio que `pipeline_datos --estado`) |
| Menos de 150 velas D1 o H1 cerradas en un instante | Ese instante no se mide; el conteo va al informe |

## 7. Pruebas

- **Cobertura del árbol:** las seis combinaciones de ejes 1 × 2, por los dos lados de cada umbral de ADX y
  de `p`, caen cada una en exactamente una rama; la rama 1 corta antes a todas.
- **Una por rama** (0, 1, 2 fuerte/moderada/débil, 3a, 3b, 4) con dicts construidos a mano usando los
  nombres reales de `analizar_activo`, y la marca `sin_recorrido` incluida la regla de `fecha_barra`.
- **Bordes exactos:** ADX en 20 y 25; `p` en 0,3 / 0,4 / 0,6 / 0,7; quiebre con `p > 1` y `p < 0`;
  histéresis a ±0,25 ATR; empate `precio == ema_50`; `previa=None`.
- **Paridad sin fuga:** leer `ema`/`atr`/`adx` en `t−1` de la serie completa da lo mismo que
  `analizar_activo` sobre el tramo que termina en `t` (con `df_closed`); el Donchian rodante coincide con
  `mt5_client.donchian`.
- **`rango_hoy` sin fuga:** en una serie sintética, el rango reconstruido a una hora dada no ve las velas
  posteriores del mismo día.
- **Zona horaria:** una serie sintética rotulada en Santiago pasa las dos pruebas de §5.4; la misma serie
  rotulada en UTC falla y aborta; las horas ambiguas de abril y septiembre se descartan.
- **Giros:** `A, L, A` son cero giros; `A, L, B` es uno; `A, B, A` son dos.
- **Contrato de config:** todo umbral que usa `direccion_gi` existe en `config/direccion.json` con nota
  de origen, y ningún número del árbol aparece escrito en el código.
- **Anti fuga de la medición:** sobre una serie sintética de futuro conocido, las métricas dan exactamente
  el valor esperado.
- **Sombra inerte:** con la lectura nueva en sombra, `direccion`, `score` y el payload del carrusel son
  idénticos a los de antes.
- **Motivo de cliente:** ningún `motivo` contiene `—` ni `–`.

## 8. Fuera de alcance (fase 2 o después)

- Que el chip, el guardia de divergencia, el informe o el `Score_GI` consuman la lectura nueva.
- Puntuación y pieza de rango para LATERAL (decisión ya tomada: LATERAL compite y se publica como rango).
- Unificar `trend` de `analisis.py` con la dirección.
- Guardar estado en el escáner para que la histéresis actúe en la tanda.
- La capa de opinión experta (COT, bancos, medios), que se compara contra el eje 1 y va en su propio spec.
- Corregir el sello `"timezone"` de las series (issue aparte, §5.4).

## 9. Historial de revisión

- **Revisión 2 (2026-09-28)**, tras la revisión cruzada de Gemini 3.8 Flash High, verificada contra el
  código y los datos: indicadores de velas cerradas (`t−1`); `rango_hoy` reconstruido desde H1; LATERAL
  medido como separador de ruido y no con `|m| < 1`; zona horaria de Santiago medida en vez de un desfase
  constante; cobertura real de las series; origen correcto del 0,70; convicción débil en la rama 2;
  definición de giro; histéresis inerte en la sombra; horizonte mínimo de 3 horas; `p` fuera de [0, 1] en
  quiebres; regla para activos disidentes; intervalos por bootstrap agrupado por día.
