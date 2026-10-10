# Enchufe de estrategia: toda la lectura técnica sale de una estrategia activa

- **Fecha:** 2026-10-09
- **Estado:** aprobado por el director el 2026-10-09, con sus decisiones en §8. El plan de la fase 1 (`docs/superpowers/plans/2026-10-09-enchufe-fase-1.md`) cierra los huecos de tipos y umbrales.
- **Rama:** `docs/metodologia-tendencias`
- **Depende de:** `docs/metodologia-tendencias.md` (la doctrina de Tori) y de su verificación pendiente

## 1. Para qué

El director decidió el 2026-10-09 tres cosas:

1. Adoptar el método de Tori Trades **de forma pura**.
2. **No poder volver** al método actual.
3. Dejar la puerta abierta a **conectar otra estrategia** más adelante, como un enchufe.

También decidió que **el escáner corresponde a la estrategia activa**: elegir qué activo sale es
parte de la estrategia.

Hoy la lectura técnica no tiene un solo dueño:
- La dirección sale del precio contra la EMA 50 (`screener_gi.direccion_tecnica`) y la consumen 8
  módulos.
- Los niveles salen de pivotes horizontales (`analisis._get_support_resistance`).
- El gráfico dibuja canales de regresión que el texto no conoce (`tradingview_grafico._canal`).
- El plan del analista sale con un stop Chandelier (`analista/estadistica.py`).
- El escáner puntúa con EMA, ADX, RSI y MACD.

Cambiar de método hoy significa tocar todo eso a mano, y cualquier parte que quede atrás publica
una lectura contradictoria. Es el defecto recurrente del repo: dos fuentes que divergen.

## 2. La idea

```
 velas MT5 ──► [ ESTRATEGIA ACTIVA ] ──► Lectura (formato fijo) ──► escáner, carrusel, informe,
 por marco      config/estrategia.json      dirección, líneas,         Avisos, analista, gráfico,
 (infra)        {"activa": "tori"}          estado, invalidación,      despacho, MCP
                                            escenarios, puntaje        (solo leen, no calculan)
```

- **La estrategia** es un paquete de Python que cumple un contrato: recibe las velas de los marcos
  que ella misma pide y devuelve una `Lectura`.
- **Los consumidores** dejan de calcular. Toman la `Lectura` y la convierten en texto, gráfico o
  puntaje.
- **El enchufe** es una línea en `config/estrategia.json`. Conectar otra estrategia significa
  escribir otro paquete que pase la misma batería de tests de conformidad y cambiar esa línea.
- **Sin vuelta atrás:** el método actual **no** se reescribe como estrategia enchufable. Se borra.
  Git conserva la historia, pero no queda ningún interruptor que lo vuelva a encender.

## 3. Qué es estrategia y qué es infraestructura

| Queda **dentro** de la estrategia | Queda **fuera** (infraestructura) |
|---|---|
| Dirección del activo | Lectura de velas de MT5 y validación de la cuenta (`mt5_client`, `guardrails/cuenta`) |
| Líneas y niveles, con su papel | Calendario, blackout, feriados (`gate_blackout`, `gate_feriado`) |
| Estado: tendencia, rebote, ruptura o rango | Sesión, reloj, agenda (`agenda_mercado`, `reloj_gi`) |
| Invalidación y regla de salida | Formato WhatsApp, decimales `digits`, tono, glosario |
| Escenarios ⬆️ ↔️ ⬇️ y su redacción técnica | Render del gráfico (HTML/Playwright) y de las Stories |
| Puntaje con que el escáner ordena y motivos de exclusión técnicos | Aprobación, despacho, bitácora, cupo y cadencia |
| Si el texto quedó invalidado entre preparar y despachar | `niveles_fijados` del director (pisa lo que la estrategia diga) |
| Marcos que necesita (contexto y operativo) | Cobertura fija de los 4 base y "sin canales vacíos" |

## 4. El contrato

Vive en `scripts/estrategia/contrato.py`. Son dataclasses inmutables y sin dependencias de MT5.

```python
class Estrategia(Protocol):
    nombre: str                      # "tori"
    marcos: Marcos                   # contexto=("W1","D1"), operativo="H4", velas y etiqueta por marco
    procedencia: Procedencia         # de dónde sale cada regla (ver "Bloque de procedencia")
    def leer(self, ticker: str, velas: dict[str, DataFrame], digits: int,
             en_curso: VelaEnCurso | None = None) -> Lectura: ...   # velas = solo cerradas
    def puntuar(self, lectura: Lectura, horizonte: Literal["sesion", "semana"]) -> Puntaje: ...
    def seguir(self, referencia: Lectura, velas: dict[str, DataFrame], digits: int,
               en_curso: VelaEnCurso | None = None) -> Lectura: ...  # contra lo fijado el lunes
    def divergencia(self, preparada: Lectura, actual: Lectura) -> str | None: ...

@dataclass(frozen=True)
class Lectura:
    ticker: str
    marco: str                       # el marco operativo de esta lectura
    precio: float
    direccion: Literal["ALCISTA", "BAJISTA", "LATERAL"]
    estado: Literal["TENDENCIA", "REBOTE", "PRUEBA", "RUPTURA", "RANGO"]
    lineas: tuple[Linea, ...]        # todo lo que se dibuja
    en_prueba: Prueba | None         # solo con estado "PRUEBA" (ver "La vela abierta")
    vigilar: Referencia              # el nivel que el cliente tiene que mirar hoy
    invalidacion: Referencia | None  # dónde la lectura deja de valer
    objetivo: Referencia | None      # el 🎯 probable (horizontal mayor)
    escenarios: tuple[Escenario, ...]  # exactamente 3: ⬆️ ↔️ ⬇️
    salida: str                      # la regla de salida, en una frase de cliente
    conceptos: tuple[str, ...]       # claves del glosario que la pieza tiene que explicar
    avisos: tuple[str, ...]          # lo que la estrategia no pudo afirmar

@dataclass(frozen=True)
class Linea:
    rol: Literal["accion", "seguridad", "seguimiento", "contexto", "objetivo", "rango"]
    tipo: Literal["diagonal", "horizontal"]
    puntos: tuple[tuple[int, float], ...]   # (timestamp, precio): 2 anclas, o 1 si es horizontal
    marco: str
    toques: int
    calidad: str                     # "A+", "B" o "" si no aplica
    valor_actual: float              # el precio de la línea en la última vela cerrada

@dataclass(frozen=True)
class Prueba:
    linea: Linea                     # la línea que el precio vivo está perforando
    valor_ahora: float               # el valor de la línea en la vela abierta
    cierre_vela: datetime            # cuándo cierra la vela del marco operativo (America/Santiago)

@dataclass(frozen=True)
class Puntaje:
    puntos: float                    # de 0 a 100
    desglose: dict[str, float]
    excluido: str | None             # motivo técnico de exclusión, en texto de motivo
```

### Bloque de procedencia

Ninguna estrategia se enchufa sin decir **de dónde sale cada regla**. Es el Gate 0 de admisión de
Genesis (un pilar académico y uno institucional) adaptado a nuestro caso. Una estrategia de
traders no siempre tiene paper, y el bloque obliga a declarar ese hueco en vez de esconderlo.

```python
@dataclass(frozen=True)
class Fundamento:
    regla: str                       # la regla, en una frase ("la ruptura se publica con el cierre")
    origen: tuple[str, ...]          # quién la usa: "Tori Trades, qLtq7 [51:00]", ...
    canonico: tuple[str, ...]        # teoría clásica: "F3 p. 56" (fila de fuentes.md + página)
    empirico: tuple[str, ...]        # evidencia medida: "F4", "F6", ...
    no_probado: str                  # lo que la evidencia no cubre; "" solo si empirico la cubre

@dataclass(frozen=True)
class Procedencia:
    fuente_doctrina: str             # "docs/metodologia-tendencias.md"
    fuente_citas: str                # "docs/investigacion/fundamentos/fuentes.md"
    fundamentos: tuple[Fundamento, ...]
    modos_de_falla: tuple[str, ...]  # cuándo pierde el método (AQR: reversiones bruscas, lateral)
```

**Qué exige la batería de conformidad:**
- **Cada regla tiene origen.** Ningún `Fundamento` puede ir con `origen` vacío.
- **Cada regla tiene respaldo o confiesa que no lo tiene.** Tiene que traer al menos un
  `canonico` o un `empirico`. Si `empirico` está vacío, `no_probado` no puede estarlo.
- **El método declara cómo falla.** `modos_de_falla` no puede ir vacío.
- **Toda cita apunta a una fuente verificada.** Cada entrada de `canonico` y de `empirico` empieza
  con el id de una fila de `fuente_citas` (`F1`, `F3`...). El test comprueba que esa fila existe y
  que su estado es "verificada" o "verificada vía". Una fila "no verificada", "parcial" o "no
  encontrada" no sirve de respaldo. Así nadie puede agregar una referencia de memoria.

**Para qué sirve más allá del test:**
- **Le da la fuente a la pieza.** `Lectura.conceptos` puede apuntar a un `Fundamento`, y el texto
  educativo puede decir "según la Teoría de Dow..." con la cita exacta.
- **Dice lo que no se sabe.** `no_probado` deja escrito qué parte del método no tiene evidencia,
  para que ninguna pieza lo presente como probado.
- **Prepara la salida a Genesis.** Es la misma ficha que su roadmap prevé para admitir estrategias
  de traders (A.2).

Para Tori, los fundamentos son la tabla de §7 de `metodologia-tendencias.md`, uno por cada una de
las diez reglas más los horizontales. La parte diagonal declara en `no_probado` que no tiene
evidencia académica propia. Hoy Moskowitz et al. (F5) y Brock et al. (F8) figuran solo como
"verificada parcial". Hasta releerlos, quedan fuera de `empirico`, y las reglas 5 y 6 se sostienen
con su pilar canónico.

**Por qué `valor_actual`:** una línea diagonal **cambia de precio con cada vela**. El número que se
publica es el valor de la línea en la última vela cerrada. El despacho tiene que volver a pedir
la `Lectura` para saber dónde está hoy, en vez de comparar contra un número congelado. Esto
reemplaza al guardia de divergencia actual, que compara contra el soporte y la resistencia
horizontales.

### El rebote: el estado `REBOTE`

**Decisión del director (2026-10-10).** Tori tiene dos setups a favor de la tendencia: la ruptura
de la línea de acción y el rebote en la línea de seguridad, cuando el precio la toca y la rechaza
sin cerrar al otro lado (doctrina 2.5, V7). El rebote tiene estado propio para que la pieza lo
cuente como lo que es: un hecho de la vela que cerró.

**Cómo se calcula:**
- **La estructura es la de `TENDENCIA`.** Mismas líneas, misma dirección, misma línea de
  seguridad. `REBOTE` no mueve ninguna línea ni ninguna ancla.
- **La condición:** la última vela cerrada tocó la línea de seguridad (dentro de la tolerancia de
  toque) y cerró a favor de la tendencia.
- **Dura una vela.** Si la siguiente vela cerrada no vuelve a tocar la línea, el estado vuelve a
  `TENDENCIA`.
- **`PRUEBA` le gana.** Si la vela abierta ya está al otro lado de una línea, manda el precio vivo.
- **No convive con `RUPTURA`.** Una vela que cerró a favor no cerró al otro lado.

**Cómo se comunica:** como hecho, porque la vela ya cerró: "la vela de 4 horas tocó la línea
alcista y cerró sobre ella". `vigilar` es la línea de seguridad que sostuvo el rebote.

**Cómo puntúa:** con una línea de seguridad A+, es la situación "a punto" de los dos horizontes
(§5). Con una línea B, es una tendencia sin evento.

**Para el despacho:** pasar de `TENDENCIA` a `REBOTE`, o al revés, no es divergencia. La
estructura es la misma y la frase del rebote habla de una vela que ya cerró.

### La vela abierta: el estado `PRUEBA`

**El caso:** la vela del marco operativo todavía no cerró, pero el precio vivo ya está al otro
lado de una línea vigente.

- **Sin este estado, la pieza se contradice.** La lectura de velas cerradas diría "la tendencia
  sigue mientras esté sobre la línea" mientras el precio que muestra la misma pieza ya está debajo.
- **Callarlo tampoco sirve.** Tori entra al cruce (doctrina 2.4), así que quien siga el método
  puede estar ya adentro.

**Cómo se calcula:**
- **Las velas cerradas siguen mandando.** Líneas, toques, calidad, dirección y el estado
  `RUPTURA` salen solo de velas cerradas, como exige la regla de "sin mirar el futuro".
- **El precio vivo solo pone un aviso encima.** `leer()` recibe la vela en curso, si existe, por
  separado de las cerradas. Si su último precio está al otro lado de una línea de acción vigente,
  el estado pasa a `PRUEBA` y `en_prueba` dice qué línea es, cuánto vale en la vela abierta y a
  qué hora cierra esa vela. Una mecha que ya volvió no lo activa: cuenta el precio vivo, no el
  extremo de la vela.
- **No cambia nada estructural.** `PRUEBA` no mueve ninguna línea ni ninguna ancla (doctrina
  2.1, V15).
- **No rompe la regla de "sin mirar el futuro".** La vela abierta llega aparte de las cerradas, y
  sin ella `PRUEBA` no aparece nunca.

**Cómo se comunica:** siempre como condición, nunca como hecho. La pieza dice cuándo cierra la
vela y qué pasa en cada caso: "si la vela de 4 horas cierra bajo X, la línea se considera rota;
si vuelve a cerrar sobre ella, fue solo una mecha y la tendencia sigue". Los tres escenarios se
ordenan alrededor de ese cierre.

**Qué hace cada producto:**
- **Las piezas del día** (carrusel, Avisos, `/story`): se publican con `PRUEBA`, porque viven
  pocas horas.
- **El informe semanal:** **no se genera con una línea A+ en `PRUEBA`.** Espera el cierre de esa
  vela, que en 4H tarda como máximo 4 horas, y sale con la lectura confirmada. Un informe que se lee
  durante días no puede quedar condicionado a algo que se resuelve en pocas horas.
- **El despacho:** `divergencia()` devuelve motivo si la pieza se preparó en `PRUEBA` y la vela
  cerró antes de enviarla, en cualquiera de los dos sentidos. El texto se escribió para una
  condición que ya se resolvió, así que la pieza no sale.

### La referencia semanal: `seguir()`

**Decisión del director (2026-10-10):** el análisis semanal fija los niveles y la tendencia, y las
actualizaciones diarias se comparan contra ese nivel. Es la regla de Tori de no mover las líneas
mientras la tesis está viva y volver a trazar cuando termina (OjZ8d [01:07], [08:48]).

**Qué fija el análisis semanal:** todo. La `Lectura` que publica el lunes queda guardada por
activo como **referencia de la semana**: líneas con sus anclas, horizontales, `vigilar`,
`invalidacion`, `objetivo` y dirección.

**Qué hace `seguir(referencia, velas, ...)`:**
- **No vuelve a trazar.** Toma las líneas de la referencia y las evalúa sobre las velas de hoy.
- **Las anclas no se mueven.** Una diagonal recalcula su `valor_actual` a lo largo de su pendiente,
  contado en velas desde sus anclas. Un horizontal vale lo mismo toda la semana.
- **El estado se mide contra esas líneas.** Si el precio las respeta, el estado sigue siendo el
  del lunes, con una salvedad: entre `TENDENCIA` y `REBOTE` decide la última vela cerrada contra
  la línea de seguridad del lunes. Si la vela en curso cruza una, el estado es `PRUEBA`. Si una vela cerró al otro lado
  por más que la tolerancia, el estado es `RUPTURA` y la dirección es la de la ruptura.
- **Devuelve una `Lectura`** con las líneas de la referencia, los escenarios redactados para hoy y
  las métricas recalculadas. Los consumidores no distinguen si salió de `leer()` o de `seguir()`.

**Cuando una línea de la referencia se rompe por cierre a mitad de semana**, la diaria informa la
ruptura contra la línea del lunes. Desde ese cierre, la **nueva referencia** es la `leer()` de ese
momento, y queda fija hasta el lunes siguiente. Con la tesis cerrada se vuelve a trazar, como
hace ella.

**Solo los activos del lunes.** Las actualizaciones diarias cubren únicamente los activos que
tienen referencia esa semana. Un activo sin análisis semanal no sale en las diarias.

**Dónde vive:** la referencia es historia de lo que el cliente leyó, así que se versiona en
`data/referencias_semanales/<AAAA-Www>/<ticker>.json`, con el mismo criterio que
`data/historial_despachos.json`. Guardarla y reemplazarla es infraestructura; la estrategia solo
la lee.

**Por qué el contrato no queda con la forma de Tori.** Una estrategia que solo use horizontales
devuelve líneas de `tipo="horizontal"` y deja vacías `seguridad` y `seguimiento`. Para probarlo,
la batería de conformidad corre también contra una **estrategia de juguete** que vive en
`tests/` y no se registra en producción.

## 5. La estrategia Tori

Paquete `scripts/estrategia/tori/`, que implementa las 12 reglas programables de la doctrina
(§4 de `metodologia-tendencias.md`):

| Módulo | Hace |
|---|---|
| `pivotes.py` | Pivotes candidatos con el extremo de mecha. Reutiliza el zigzag de `tradingview_grafico._zigzag`, que se muda acá. |
| `lineas.py` | **Trazado:** el primer punto en el extremo visible y el segundo en el pivote que maximiza toques **sin que ninguna vela cruce la línea**, con tolerancia de toque. Encadenamiento y abanico. |
| `calidad.py` | Toques, semanas de datos y marco. A+ = 3 toques o más y al menos 1 semana. B = 2 toques. Marca la línea "muy empinada". |
| `lectura.py` | Línea de acción y de seguridad, ruptura por **cierre de vela** (de las dos formas que ella valida, la única publicable: doctrina 2.4), rebote en la línea de seguridad (doctrina 2.5), estado (consolidación si oscila entre las dos líneas o entre horizontales sin romper), dirección, `vigilar`, `invalidacion`, `objetivo` (el horizontal mayor más cercano en la dirección), escenarios. |
| `puntaje.py` | El escáner de Tori (ver abajo). |
| `textos.py` | Redacción de escenarios y `salida`, con las reglas de texto de cliente (sin guion largo, tuteo chileno, flechas). |

**Marcos:** el contexto es W1 y D1 y el operativo es H4. La bajada a H1 por alta volatilidad
queda **fuera de la v1**, porque Tori no da un umbral y ponerle uno sería inventarlo.

**Horizontales:** salen de un detector propio de la estrategia, que busca el nivel con más toques
y cercano al precio, según la doctrina §2.10. Hace lo mismo que `_get_support_resistance`, pero
ahora es **parte de Tori**: la otra estrategia trae los suyos.

**El escáner de Tori** puntúa sobre 100, y el orden depende del `horizonte` de la pieza. El
carrusel vive horas y el informe del lunes vive la semana, así que premian cosas distintas.

**Horizonte `"sesion"`** (carrusel, Avisos, `/story`):
1. La ruptura **reciente** de una línea A+ con el precio cerca de la línea de seguridad, que es el
   setup de bajo riesgo. Con la vela abierta, entra acá como `PRUEBA`.
2. El precio a punto de tocar una línea A+ sin romperla todavía, o que acaba de rebotar en ella
   (`REBOTE`).
3. La tendencia vigente sin evento.
4. El rango.

**Horizonte `"semana"`** (el análisis semanal del lunes; decisión del director, 2026-10-09):
1. **El precio cerca de una línea A+ que todavía no se rompe** (por ejemplo, a menos de un ATR
   diario). La semana casi seguro la pone a prueba, y la pieza deja un nivel concreto que vigilar
   con dos escenarios: si cierra al otro lado en 4H, se rompe; si rebota, la tendencia sigue.
   Enseña a mirar la línea y no a perseguir el precio. El `REBOTE` en una línea A+ entra acá.
2. **Ruptura confirmada el viernes o el fin de semana, con el precio todavía cerca de la línea de
   seguridad.** El setup en 4H dura de una a dos semanas (doctrina 2.9), así que le alcanza la
   semana.
3. **Tendencia vigente con una línea A+ larga y confluencia de temporalidad mayor.** Es la lectura
   más estable: no envejece durante la semana.
4. **Rango con los bordes bien marcados.** Solo si no hay nada mejor, como pieza educativa sobre
   esperar la ruptura.

**Lo que suma dentro de cada situación, en los dos horizontes** (todo de la doctrina):
- **Calidad de la línea:** 3 toques o más, varias semanas de datos entre toques (V14), y un
  segundo punto que no sea demasiado reciente (V16).
- **Confluencia de temporalidades:** que la línea de 4H calce con una de D1 o W1, o vaya a favor
  de su secuencia (doctrina 2.9). En `"semana"` pesa más que en `"sesion"`.
- **Doble confirmación disponible:** un horizontal cerca de la línea, para que la ruptura rompa
  los dos a la vez (doctrina 2.4, V17).
- **Espacio hasta el objetivo:** la distancia al horizontal mayor (🎯) bastante mayor que la
  distancia a la línea de seguridad (⚠️). No es un take profit fijo: mide si el movimiento vale
  la pena.

**Lo que resta o excluye:**
- **El precio lejos de la línea de seguridad** resta mucho en los dos horizontes, porque Tori pasa
  esa operación (doctrina 2.5). En `"semana"` también resta la ruptura vieja que ya recorrió.
- **Una línea muy empinada o de solo 2 toques** se puede dibujar, pero no puntúa como línea
  principal.
- **En `"semana"`, una línea A+ en `PRUEBA`** no puntúa: el informe espera el cierre (ver "La
  vela abierta").
- **Un activo sin ninguna línea trazable** se excluye: sin estructura no hay lectura.
- **Un activo que va contra la secuencia de los marcos mayores** se excluye, en los dos
  horizontes (decisión del director, 2026-10-10; ipUbs [00:36], [01:11]: las falsas rupturas
  vienen de operar contra la estructura mayor).
- **Nada macro.** La agenda va en el informe complementario de los viernes (§8.2) y no mueve el
  ranking.

El rango no se excluye en `"sesion"`, porque el criterio "sin canales vacíos" del director exige
publicar algo y la pieza de rango enseña a esperar la ruptura.

Los pesos exactos y el umbral de "cerca" se fijan en el plan, sobre una medición del universo real.

## 6. Qué se borra (sin vuelta atrás)

- `screener_gi`:
  - `direccion_tecnica`, `factor_tecnico`, `factor_momentum`, `factor_espacio`,
    `factor_catalizador` y `_contexto_macro`.
  - `gate_agotamiento`, `gate_banda`, `banda_estrecha`.
  - La sombra de 4 ejes, con `direccion_gi.py` y `medir_direccion.py`.
- `analista/estadistica.py`, el Chandelier y el backtest de 1,5 × ATR. La pieza del analista
  sale sin estadística (§8.4). `plan.armar` pasa a leer
  la `Lectura`: el gatillo es la línea de acción, la invalidación es la de seguridad y no hay
  objetivo fijo.
- `tradingview_grafico`:
  - `_canal` y `calcular_estructura`. El gráfico dibuja `Lectura.lineas`.
  - Los indicadores duplicados que el gráfico ya no muestra.
- `pipeline_carrusel.lectura_operativa`: los escenarios, el "qué esperar" y el texto del falso
  quiebre pasan a salir de `Lectura.escenarios`.
- En CLAUDE.md:
  - La sección **Indicadores técnicos**, con el modelo ADC + ATR y los avisos de RSI, MACD y
    medias.
  - Las partes de **El Score_GI y sus gates** y **El Playbook V2 se retiró** que fijan la EMA 50.
  - El cierre canónico de la regla de formato 6.

  Se reescriben apuntando a la doctrina, y `.agents/rules/proyecto.md` se regenera.

**`get_asset_levels` se queda en el MCP como dato crudo** (indicadores y pivotes), para auditoría y
para AGY. Ningún pipeline de producción decide con ella. Se agrega la tool **`get_lectura`**, que
devuelve la `Lectura` de la estrategia activa, y la ruta `alerta` de `/story` pasa a usarla.

**Guardián contra la vuelta atrás:** se agrega un test de contrato con el estilo de los que ya
tiene el repo. El test lee la fuente de `scripts/` y falla si fuera de `scripts/estrategia/`
aparece una decisión técnica: `ema_50` usada para dirigir, `direccion_tecnica`, `s1`/`r1` de
`analizar_activo` en un pipeline, o el import de `_get_support_resistance`. Sin ese test, la
próxima pieza urgente vuelve a calcular la dirección por su cuenta.

## 7. Fases

Va un plan y un PR por fase. Ninguna fase deja el sistema con dos lecturas a la vez.

1. **Contrato y estrategia Tori, sin consumidores.**
   - El paquete `scripts/estrategia/`, el registro, `config/estrategia.json` y la batería de
     conformidad, con la estrategia de juguete.
   - Tests de Tori sobre velas sintéticas: trazado, no intersección, toques, ruptura por cierre,
     rango, `PRUEBA` con vela en curso (y su ausencia sin ella), y el orden de `puntuar` en los dos
     horizontes.
   - Una corrida sobre los 5 activos base reales que devuelva las líneas en PNG para que el
     director las mire.
   - La `Procedencia` de Tori, con la batería que la valida contra `fuentes.md`.
   - **Requisito previo, cumplido el 2026-10-09:** volvió la verificación [V1]-[V20] de la
     doctrina, y los fundamentos se verificaron contra Murphy y los papers.
2. **Referencia semanal, escáner, carrusel y despacho.**
   - El lunes, el escáner elige con `puntuar(lectura, "semana")` y guarda la referencia de cada
     activo elegido. Esto va en esta fase y no en la 3 porque las diarias solo cubren los activos
     del lunes: sin referencia no hay carrusel.
   - El escáner diario ordena los activos con referencia con `puntuar(seguir(...), "sesion")`.
   - Una ruptura por cierre de una línea de la referencia la reemplaza por la `leer()` de ese
     momento.
   - La pieza toma dirección, niveles y escenarios de la `Lectura`.
   - El gráfico dibuja las líneas.
   - El despacho usa `divergencia`.
   - Se borra lo de la §6 que solo usaban ellos.
   - Se actualizan los tests que fijan la EMA 50 y el falso quiebre (el mapa está en el anexo).
3. **Informe, Avisos, analista, LinkedIn, cierre semanal y `/story`.**
   - Pasan a la `Lectura`.
   - El plan del analista se queda sin Chandelier.
   - La pieza del análisis semanal del lunes se publica desde la referencia guardada en la fase 2,
     y espera el cierre de la vela si hay una línea A+ en `PRUEBA`.
   - Se agrega la tool `get_lectura`.
4. **Purga y documentación.**
   - Se borra el resto de la §6.
   - Entra el test guardián.
   - Se reescriben CLAUDE.md, `.claude/commands/*.md` y las reglas de AGY.

## 8. Decisiones del director (2026-10-09)

1. **La etiqueta del marco depende de la estrategia.**
   - `Marcos` lleva, para cada marco, su etiqueta y su rango de duración. Para Tori, 4H es
     "swing, de una a dos semanas".
   - `MARCOS_CANONICOS` deja de ser una tabla fija de `pipeline_carrusel`: se lee de la
     estrategia activa.
   - Las notas `nota_volatilidad` de `config/activos.json` y su test se ajustan en la fase 2.
2. **El catalizador macro sale del escáner.**
   - El factor de 25 puntos y `_contexto_macro` dejan de influir en la selección.
   - El contexto macro pasa a ser un **informe complementario** que **informa y no decide**: no
     toca la dirección, los niveles ni el ranking.
   - Se envía también los viernes.
   - Es un trabajo con su propio spec y queda **fuera de este**. Lo único que este spec garantiza
     es que la estrategia no consuma nada macro.
3. **Los gates de agotamiento y de banda salen.** Con ellos desaparecen la categoría
   `recorrido_agotado` del suplemento y sus motivos en el contrato de nombres.
4. **No habrá backtesting** (decisión del director, 2026-10-10; reemplaza la del 2026-10-09 que
   lo dejaba como subproyecto):
   - `analista/estadistica.py` es un mini-backtester amarrado al Chandelier, y se borra.
   - La pieza del analista sale **sin estadística** y no la inventa. Ninguna pieza da una tasa de
     acierto.
   - Lo que la procedencia declara `no_probado` queda así, declarado: el sistema enseña el método
     con su fuente y no afirma que esté probado.
5. **El marco del carrusel lo decide la estrategia.** Esto se deduce de la decisión 1. Con Tori, el
   marco operativo es 4H.
6. **La vela abierta se comunica como `PRUEBA`, no como ruptura.** Las piezas del día la publican
   como condición; el informe semanal espera el cierre de esa vela (§4, "La vela abierta").
7. **El escáner puntúa por horizonte.** El lunes premia primero el precio cerca de una línea A+
   todavía sin romper, y después la ruptura confirmada con el precio cerca de la línea de
   seguridad (§5).
8. **La alta volatilidad queda fuera de la v1.** Tori la reconoce en parte por las noticias, y la
   estrategia no consume nada macro (decisión 2). Si se agrega después, entra como parámetro
   declarado nuestro (por ejemplo, el ATR en percentil alto), con su `no_probado` en la
   procedencia.

9. **Las diarias se comparan contra el análisis semanal** (2026-10-10). El lunes fija todo; las
   diarias solo cubren esos activos y miden el precio contra esas líneas con `seguir()`; una
   ruptura por cierre a mitad de semana deja como nueva referencia la lectura de ese momento
   (§4, "La referencia semanal").

**La regla de "sin mirar el futuro".**
- **La exigencia:** `leer()` y `seguir()` tienen que dar **el mismo resultado** si se les pasan
  las velas hasta un instante del pasado que si ese instante fuera "ahora". Nunca miran velas
  posteriores a la última cerrada ni guardan memoria entre lecturas.
- **Por qué se mantiene sin backtesting:** el despacho vuelve a leer justo antes de enviar y la
  diaria se compara contra la referencia del lunes. Las dos cosas necesitan que la misma entrada
  dé siempre la misma lectura; una estrategia con memoria o que mire de más publicaría una
  lectura que nadie puede reproducir.
- **Cómo se verifica:** la batería de conformidad lo comprueba recortando una serie y comparando.

## 9. Riesgos

- **Sin análisis del lunes no hay diarias.** Si la corrida semanal no sale, ningún activo tiene
  referencia y el carrusel queda vacío, contra el criterio de "sin canales vacíos". La fase 2
  tiene que decir qué pasa ese lunes (correr la semanal en la primera diaria, o avisar y parar).

- **El trazado automático puede no parecerse al de ella.** Por eso la fase 1 termina con PNG
  revisados por el director antes de enchufar a nadie.
- **Un precio que se mueve sobre una diagonal:** el texto publicado envejece aunque el precio no
  se mueva. Lo cubre `valor_actual` más el refresco del despacho.
- **Tests que se reescriben en bloque** (unos 60 entre carrusel, escáner, analista y levels).
  Cada fase los actualiza junto con el código que cambia, nunca después.

## Anexo: consumidores mapeados el 2026-10-09

**Usan la EMA 50 o `direccion_tecnica`:**
- `screener_gi.py:567`
- `pipeline_carrusel.py:128, :1163`
- `pipeline_informe.py:514` (D1)
- `pipeline_avisos.py:872`
- `analista/foco.py:343, :367`
- `analista/preparar.py:513`
- `pipeline_linkedin.py:193`

**Llaman a `analizar_activo`:**
- `screener_gi.py:744`
- `pipeline_carrusel.py:787, :1438`
- `pipeline_avisos.py:1210`
- `pipeline_informe.py:566`
- `pipeline_linkedin.py:185`
- `cierre_semanal_datos.py:140`
- `analista/foco.py:195`

**Llaman al gráfico:**
- `pipeline_carrusel.py:1321, :1466`
- `pipeline_avisos.py:1126`
- `analista/preparar.py:54`
- `produccion_adhoc.py:97`

**Tests que fijan el comportamiento actual:**
- `test_pipeline_carrusel.py`: EMA 50, falso quiebre y divergencia.
- `test_screener_gi.py`: factores, banda y agotamiento.
- `test_direccion_gi.py` y `test_medir_direccion.py`.
- `test_analista_{estadistica,plan,foco,preparar,esquema}.py`.
- `test_levels.py`.
- `test_voz_cliente_informe.py`.
- `test_pipeline_avisos.py`.
- `test_suplemento_canal.py` y `test_guardrails_contrato.py`: los motivos de los gates.
- `test_guardrails_nombres.py`: `MARCOS_CANONICOS`.
