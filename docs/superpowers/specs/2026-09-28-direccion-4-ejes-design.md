# Dirección técnica de cuatro ejes — Fase 1: modelo en sombra y medición

- **Fecha:** 2026-09-28
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

Todo lo que el modelo necesita **ya se calcula** en `get_asset_levels` para H1 y D1 (EMA 20/50/100,
Donchian 50, ADX 14, ATR 14, `rango_hoy`, `atr_restante_14`), y el escáner ya pide los dos marcos.

## 2. Principio de diseño: ejes independientes, no votos

EMA, MACD y RSI salen del mismo cierre suavizado: si votaran juntos, "4 de 4" sería la misma señal
contada cuatro veces, la confianza inflada que hundió al Playbook V2. El modelo usa ejes que miden cosas
distintas, cada uno con un rol, combinados por un **árbol de reglas explícito** (se descartaron un
puntaje ponderado, por sus pesos mágicos, y la mayoría de votos, que pierde la corrección dentro de
tendencia). La rama del árbol **es** el motivo que lee el cliente.

| Eje | Pregunta | Con qué | Rol |
|---|---|---|---|
| 1. Fondo | ¿Hacia dónde va en días? | D1: precio vs EMA 50, EMA 50 vs EMA 100 | Ancla |
| 2. Día | ¿Qué hace hoy? | H1: precio vs EMA 50 + posición en Donchian 50 | Confirma o marca corrección |
| 3. Fuerza | ¿Tendencia o rango? | ADX 14 de H1 | Decide LATERAL y el desempate de la corrección |
| 4. Espacio | ¿Le queda recorrido hoy? | consumo ATR diario (`rango_hoy / ATR`) | **Solo texto** |

**El ADX no vota dirección**: mide fuerza, sube igual en una caída que en una subida.

**El eje 4 no cambia ni la dirección ni la convicción.** El consumo de ATR ya pesa en el escáner como
`gate_agotamiento` y como `factor_espacio`; usarlo acá también lo contaría tres veces.

## 3. Las reglas

Notación: `p = (precio − donchian_low) / (donchian_high − donchian_low)` en H1, de 0 (mínimo del canal)
a 1 (máximo). Con `high == low`, `p` no se puede calcular y la lectura cae a `datos_incompletos`.

**Eje 1 (D1):**
- `alcista` si `precio > ema_50` **y** `ema_50 > ema_100`
- `bajista` si `precio < ema_50` **y** `ema_50 < ema_100`
- `transicion` en cualquier otro caso

**Eje 2 (H1):** `alcista` si `precio > ema_50`, `bajista` si `precio < ema_50` (con la histéresis de §3.2).
El canal **confirma** el lado si `p ≥ 0,6` (alcista) o `p ≤ 0,4` (bajista).

### 3.1 Árbol (gana la primera rama que calce)

| # | Condición | Dirección | Convicción | Fase |
|---|---|---|---|---|
| 0 | falta un campo o `p` no calculable | la de H1 | débil | `datos_incompletos` (nombra el campo) |
| 1 | `ADX < 20` **y** `0,3 ≤ p ≤ 0,7` | LATERAL | — | `rango` |
| 2 | D1 y H1 del mismo lado | la común | fuerte si `ADX ≥ 25` **y** el canal confirma; si no, moderada | `tendencia_alineada` |
| 3a | D1 y H1 opuestos, `ADX ≥ 25` | la de H1 (el día) | moderada | `correccion_con_fuerza` |
| 3b | D1 y H1 opuestos, `ADX < 25` | la de D1 (el fondo) | débil | `correccion` |
| 4 | D1 en `transicion` | la de H1 | débil | `sin_ancla` |

Decisión del director para la rama 3: con fuerza manda el día; sin fuerza manda el fondo, y el texto
dice que corrige dentro de la tendencia y que se vigila el soporte (o la resistencia) para retomar.

**Marca `sin_recorrido`**, encima de cualquier rama: consumo de ATR diario `≥ 0,70` (el umbral de aviso de
`factor_espacio`). Aplica la misma regla de `fecha_barra` que el escáner: si la vela D1 es de un día
anterior, el consumo es 0.

**Empate exacto** `precio == ema_50` en H1 sin dirección previa: se resuelve alcista, igual que
`direccion_tecnica` hoy.

### 3.2 Histéresis

`leer_direccion(h1, d1, previa=None)`. Con `previa` (la dirección de H1 que ya viaja en el payload), el
eje 2 solo cambia de lado si el precio cruza la EMA 50 de H1 por **más de 0,25 × ATR 14 de H1**. La
función no guarda estado.

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
| `consumo_sin_recorrido` | 0,70 | Umbral de aviso de `factor_espacio` |

Si más adelante se quisiera calibrarlos, se ajustan con el 70 % más antiguo de la historia y se validan
con el 30 % más reciente. Reportar un ajuste hecho sobre toda la historia sería medir el ajuste.

## 4. Componentes

### 4.1 `scripts/direccion_gi.py` (nuevo, puro)

- `leer_direccion(h1: dict, d1: dict, previa: str | None = None) -> LecturaDireccion`
- `LecturaDireccion` (dataclass congelada): `direccion` (`ALCISTA` | `BAJISTA` | `LATERAL`),
  `conviccion` (`fuerte` | `moderada` | `debil` | `None` en rango), `fase`, `sin_recorrido: bool`,
  `motivo` (una línea en voz de cliente, sin guion largo), `ejes` (lectura cruda de cada eje, para auditar).
- Solo stdlib; los umbrales se leen de `config/direccion.json`. Sin MT5, sin red.

### 4.2 Sombra en el escáner

`screener_gi.evaluar_activo` agrega `direccion_4ejes` (la lectura serializada) junto a `direccion`. **La
`direccion` actual sigue siendo la que puntúa, pinta el chip y alimenta el guardia de divergencia**:
nada de lo que sale al cliente cambia. El resumen de la tanda imprime una línea por activo cuando ambas
difieren. Si `leer_direccion` lanza, el escáner anota el aviso y sigue: **la sombra nunca tumba la tanda**.

### 4.3 `scripts/medir_direccion.py` (nuevo)

Recorre la historia y compara el modelo contra la EMA 50 sola. Detalle en §5.

## 5. La medición

### 5.1 Datos y paridad

- Series `data central/DATA PRECIOS OHLC/<ACTIVO>_{H1,D1}.json` de XAUUSD, WTI, BRENT, US100, USDCLP,
  COPPER y USDIDX (H1: 10.000 velas desde enero de 2025; D1: desde 2004).
- Los indicadores se **recalculan desde el OHLC con las funciones de `market_data_mcp.mt5_client`**
  (`ema`, `atr`, `adx`), importables sin MT5. No se usan las columnas precalculadas: no traen EMA 100 ni
  ADX, y otra fórmula sería otro modelo. El Donchian usa la misma fórmula rodante que
  `mt5_client.donchian`.
- `ema`, `atr` y `adx` son recursivas (`adjust=False`): se calculan una vez sobre la serie completa y se
  leen por vela, sin fuga del futuro. Un test lo verifica (§7).
- **Límite de la paridad:** en vivo, `analizar_activo` pide una ventana finita de velas y su EMA 100
  arranca con menos historia. El informe mide la diferencia en las últimas velas en vez de suponerla.

### 5.2 Punto en el tiempo

En cada vela H1 cerrada `t`, la lectura D1 usa solo los días ya cerrados antes del día de `t`, con el
precio igual al cierre de H1 en `t`, igual que `analizar_activo`.

### 5.3 Hora: el desfase del servidor se deriva, no se supone

Las marcas de MT5 están en **hora del servidor**, aunque los JSON digan `"timezone": "UTC"`. Antes de
medir, el script deriva el desfase servidor → Nueva York **de los propios datos**: en cada día hábil, la
vela H1 de mayor `tick_volume` del US100 es la de la apertura de las 09:30 NY. Verifica que el desfase
sea **constante durante todo el período**, incluidas las semanas de marzo y noviembre en que EE.UU. y
Europa cambian de horario en fechas distintas. **Si no es estable, la medición aborta y lo reporta.**

Hallazgo que se anota sin arreglarlo en esta fase: si el sello `"timezone": "UTC"` es falso, todo
consumidor que filtre las series por hora está expuesto al mismo error.

### 5.4 Qué instantes votan

- Las ventanas salen de `config/agenda_mercado.json` (sesiones `apertura_ny` y `tarde_ny`, más la tanda
  de pre-cierre de las 16:45). **Ninguna hora se escribe en el script.**
- Instantes de decisión: velas H1 que cierran entre las **08:00 y las 16:00 NY**, días hábiles.
- **Por clase**, igual que los momentos: divisas, metales, energía y USDIDX desde la vela de las 08:00;
  **US100 desde la de las 10:00**, con el horizonte cortado al cierre de las 16:00. El informe dice
  cuántos instantes quedaron con horizonte recortado.
- **Fuera de sesión se mide y se reporta aparte, sin votar en la adopción.**

### 5.5 Acierto (horizonte: 4 velas H1)

`m = (close[t+4] − close[t]) / ATR14_H1[t]` (o hasta el cierre, en US100).

- ALCISTA acierta si `m > 0`; BAJISTA si `m < 0`.
- LATERAL acierta si `|m| < 1`.

### 5.6 Regla de adopción (fijada antes de ver números)

El modelo se adopta, y habilita el spec de la fase 2, si en la sesión americana se cumplen **1 y 2**:

1. **Acierto:** en las velas donde el modelo da dirección, acierta **≥** la EMA 50 en esas mismas velas;
   y en las velas que marca LATERAL, su acierto es **≥** el de la EMA 50 en esas velas.
2. **Estabilidad:** da vuelta **menos** veces cada 100 velas que la EMA 50, **a la que se le aplica la misma
   histéresis de 0,25 ATR**, para que el modelo no gane por la histéresis sino por los ejes.

Y aparte:

3. **Convicción:** se publica en la fase 2 solo si el acierto es monótono (débil < moderada < fuerte). Si
   no ordena el acierto, es decoración: la dirección puede adoptarse sin ella.

Un activo que contradiga el total se reporta; no se promedia para esconderlo.

### 5.7 Salida

`docs/mediciones/direccion-4-ejes.md` (informe por activo y total, dentro y fuera de sesión, desfase
derivado, instantes recortados, paridad de la EMA 100) y el JSON crudo al lado.

## 6. Errores

| Situación | Comportamiento |
|---|---|
| Falta un campo en h1/d1, o `p` no calculable | Fase `datos_incompletos`, nombra el campo; nunca una lectura completa inventada |
| `leer_direccion` lanza dentro del escáner | Aviso en la tanda, sigue con la dirección actual |
| Desfase del servidor no estable | La medición aborta con el detalle |
| Serie que no salió de MT5 o de la cuenta declarada | La medición aborta (mismo criterio que `pipeline_datos --estado`) |
| Historia insuficiente para calentar la EMA 100 de D1 | Ese activo se excluye con motivo |

## 7. Pruebas

- **Una por rama del árbol** (0, 1, 2 fuerte/moderada, 3a, 3b, 4) con dicts construidos a mano, y la
  marca `sin_recorrido` incluida la regla de `fecha_barra`.
- **Bordes exactos:** ADX en 20 y 25; `p` en 0,3 / 0,4 / 0,6 / 0,7; histéresis a ±0,25 ATR; empate
  `precio == ema_50`.
- **Paridad sin fuga:** el valor de `ema`/`atr`/`adx` en `t` calculado sobre la serie completa es igual al
  de recalcular sobre el tramo que termina en `t`; el Donchian rodante coincide con `mt5_client.donchian`.
- **Contrato de config:** todo umbral que usa `direccion_gi` existe en `config/direccion.json` con nota
  de origen, y ningún número del árbol aparece escrito en el código.
- **Anti fuga de la medición:** sobre una serie sintética de futuro conocido, el acierto da exactamente el
  valor esperado.
- **Desfase:** una serie sintética con desfase constante se deriva bien; una con un salto a mitad de año
  hace abortar.
- **Sombra inerte:** con la lectura nueva en sombra, `direccion`, `score` y el payload del carrusel son
  idénticos a los de antes.
- **Motivo de cliente:** ningún `motivo` contiene `—` ni `–`.

## 8. Fuera de alcance (fase 2 o después)

- Que el chip, el guardia de divergencia, el informe o el `Score_GI` consuman la lectura nueva.
- Puntuación y pieza de rango para LATERAL (decisión ya tomada: LATERAL compite y se publica como rango).
- Unificar `trend` de `analisis.py` con la dirección.
- La capa de opinión experta (COT, bancos, medios), que se compara contra el eje 1 y va en su propio spec.
- Corregir el sello `"timezone"` de las series.
