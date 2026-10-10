# Enchufe de estrategia: toda la lectura técnica sale de una estrategia activa

- **Fecha:** 2026-10-09
- **Estado:** borrador con las decisiones del director del 2026-10-09 (§8)
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
| Estado: tendencia, ruptura o rango | Sesión, reloj, agenda (`agenda_mercado`, `reloj_gi`) |
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
    def leer(self, ticker: str, velas: dict[str, DataFrame], digits: int) -> Lectura: ...
    def puntuar(self, lectura: Lectura) -> Puntaje: ...
    def divergencia(self, preparada: Lectura, actual: Lectura) -> str | None: ...

@dataclass(frozen=True)
class Lectura:
    ticker: str
    marco: str                       # el marco operativo de esta lectura
    precio: float
    direccion: Literal["ALCISTA", "BAJISTA", "LATERAL"]
    estado: Literal["TENDENCIA", "RUPTURA", "RANGO"]
    lineas: tuple[Linea, ...]        # todo lo que se dibuja
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
- **Le dice al backtester qué medir.** Lo que está en `no_probado` es justamente lo que conviene
  medir primero.
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
| `lectura.py` | Línea de acción y de seguridad, ruptura por **cierre de vela** (de las dos formas que ella valida, la única publicable: doctrina 2.4), estado (consolidación si oscila entre las dos líneas o entre horizontales sin romper), dirección, `vigilar`, `invalidacion`, `objetivo` (el horizontal mayor más cercano en la dirección), escenarios. |
| `puntaje.py` | El escáner de Tori (ver abajo). |
| `textos.py` | Redacción de escenarios y `salida`, con las reglas de texto de cliente (sin guion largo, tuteo chileno, flechas). |

**Marcos:** el contexto es W1 y D1 y el operativo es H4. La bajada a H1 por alta volatilidad
queda **fuera de la v1**, porque Tori no da un umbral y ponerle uno sería inventarlo.

**Horizontales:** salen de un detector propio de la estrategia, que busca el nivel con más toques
y cercano al precio, según la doctrina §2.10. Hace lo mismo que `_get_support_resistance`, pero
ahora es **parte de Tori**: la otra estrategia trae los suyos.

**El escáner de Tori** puntúa sobre 100, en este orden de prioridad:
1. La ruptura **reciente** de una línea A+ con el precio cerca de la línea de seguridad, que es el
   setup de bajo riesgo.
2. El precio a punto de tocar una línea A+ sin romperla todavía.
3. La tendencia vigente sin evento.
4. El rango.

El rango no se excluye, porque el criterio "sin canales vacíos" del director exige publicar algo,
y la pieza de rango enseña a esperar la ruptura. Lo que sí se excluye es el activo que no tiene
ninguna línea trazable: sin estructura no hay lectura.

Los pesos exactos se fijan en el plan, sobre una medición del universo real.

## 6. Qué se borra (sin vuelta atrás)

- `screener_gi`:
  - `direccion_tecnica`, `factor_tecnico`, `factor_momentum`, `factor_espacio`,
    `factor_catalizador` y `_contexto_macro`.
  - `gate_agotamiento`, `gate_banda`, `banda_estrecha`.
  - La sombra de 4 ejes, con `direccion_gi.py` y `medir_direccion.py`.
- `analista/estadistica.py`, el Chandelier y el backtest de 1,5 × ATR. La pieza del analista
  sale sin estadística hasta que exista el backtester (§8.4). `plan.armar` pasa a leer
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
     rango.
   - Una corrida sobre los 5 activos base reales que devuelva las líneas en PNG para que el
     director las mire.
   - La `Procedencia` de Tori, con la batería que la valida contra `fuentes.md`.
   - **Requisito previo, cumplido el 2026-10-09:** volvió la verificación [V1]-[V20] de la
     doctrina, y los fundamentos se verificaron contra Murphy y los papers.
2. **Escáner, carrusel y despacho.**
   - El escáner ordena con `puntuar`.
   - La pieza toma dirección, niveles y escenarios de la `Lectura`.
   - El gráfico dibuja las líneas.
   - El despacho usa `divergencia`.
   - Se borra lo de la §6 que solo usaban ellos.
   - Se actualizan los tests que fijan la EMA 50 y el falso quiebre (el mapa está en el anexo).
3. **Informe, Avisos, analista, LinkedIn, cierre semanal y `/story`.**
   - Pasan a la `Lectura`.
   - El plan del analista se queda sin Chandelier.
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
4. **La estadística es tarea de un backtester**, que hoy no existe:
   - `analista/estadistica.py` es un mini-backtester amarrado al Chandelier, y se borra.
   - El backtester es **un subproyecto aparte**, y tiene que servir para **cualquier**
     estrategia enchufada.
   - Hasta que exista, la pieza del analista sale **sin estadística** y no la inventa.
   - Para que el backtester sea posible, este spec agrega la regla de "sin mirar el futuro" (ver
     abajo).
5. **El marco del carrusel lo decide la estrategia.** Esto se deduce de la decisión 1. Con Tori, el
   marco operativo es 4H.

**La regla que habilita el backtester.**
- **La exigencia:** `leer()` tiene que dar **el mismo resultado** si se le pasan las velas hasta
  un instante del pasado que si ese instante fuera "ahora". Es decir, nunca mira velas
  posteriores a la última cerrada.
- **Cómo se verifica:** la batería de conformidad lo comprueba recortando una serie y comparando.
- **Lo que permite:** un backtester genérico puede reproducir la historia vela a vela y abrir y
  cerrar operaciones solo con la `Lectura`:
  - Se entra cuando `estado` pasa a `RUPTURA`.
  - Se sale cuando una vela cierra al otro lado de `invalidacion`, que en Tori es la línea de
    seguridad arrastrada.
  - No hace falta ningún método extra por estrategia.

## 9. Riesgos

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
