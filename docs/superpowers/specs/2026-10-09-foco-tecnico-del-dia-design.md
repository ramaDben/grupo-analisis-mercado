# Foco técnico del día (`/oportunidad`) — diseño

Fecha: 2026-10-09 · Rama: `feat/bot-oportunidad` · Base: el bot de analistas mergeado en el PR #248
(`docs/superpowers/specs/2026-10-08-informe-general-firmado-y-plan-design.md`).

## Para qué

Los ejecutivos de ventas van a pedir "la oportunidad del día" para enviársela a un prospecto. La
pieza existe para servirles, pero **del lado del análisis general**: nadie en GI está inscrito como
asesor de inversión. Lo que la mantiene ahí no es el nombre, es el mecanismo:

- la elige una regla y no una persona, y es idéntica para todos los que la piden;
- describe un escenario condicional, nunca una instrucción;
- algunos días no hay, y el bot lo dice en vez de rellenar.

## Decisiones del director (2026-10-08)

| Tema | Decisión |
|---|---|
| Comando | `/oportunidad`, sin argumentos, para toda la allowlist |
| Título impreso | **«Foco técnico del día · <activo>»**. La palabra "oportunidad" no se imprime. |
| Universo | Propio de ventas: el forex y commodities cubierto **más** `US100.spot` y `BRENT.spot` |
| Estadística | **No va.** En su lugar, una frase fija sin cifras (ver Pieza) |
| Orden de trabajo | Esta pieza primero; los evergreen en una spec aparte |

## Por qué no `escanear()` ni el `Score_GI` tal cual

Revisado contra el código, y confirmado por una revisión adversarial de agy (Gemini 3.8 Flash High):

1. **`factor_espacio` premia lo contrario del plan** (`screener_gi.py:653-680`). Para el escáner el R1
   es el *objetivo*: da 20 puntos con el precio a 1,5 ATR o más de él y 0 si está cerca. Para el plan
   el R1 es el *gatillo*. Con el puntaje tal cual, un activo a punto de activar sale último.
2. **`factor_catalizador` no mira la dirección** (`:630-631`): la UST 10Y moviéndose 3 pb en
   cualquier sentido suma 20, así que una subida de tasas puede hacer ganar un plan alcista del oro.
3. `escanear()` **excluye lo ya publicado hoy** en el carrusel y **suma cobertura fija con puntaje 0**:
   las dos cosas son correctas para WhatsApp e incorrectas acá.
4. `evaluar_activo` **recibe el calendario como argumento**: si no se le pasa (el bot hoy le pasa
   `[]`), el gate de blackout nunca dispara.

## Universo

`solo_canales_cubiertos(cargar_universo(False))` filtrado a la clase `forex_commodities`, unido a
`US100.spot` y `BRENT.spot`. Hoy son 10 activos: COPPER, EURUSD, GBPUSD, USDCLP, USDJPY, WTI.spot,
XAGUSD, XAUUSD, US100.spot, BRENT.spot. Vive en una función `universo_ventas()` con su test: si alguien
apaga un canal en `config/whatsapp_grupos.json`, ventas lo pierde igual que el carrusel, salvo los dos
agregados a mano.

**Índices solo desde su momento.** `US100.spot` no es elegible antes de la hora del momento
`apertura_indices` de `config/agenda_mercado.json` (10:00 Nueva York), convertida en el instante con
`agenda_mercado`. Nunca una hora de Chile fija: el desfase se mueve dos veces al año.

## Selección

**Paso 0, contexto.** `_contexto_macro(ahora)` (solo lee). Si el calendario no responde, **no hay foco**:
sin calendario no se puede verificar el blackout.

**Paso 1, gates** por activo, en este orden: feriado, mercado abierto (nuevo), `evaluar_activo` con los
eventos reales (agotamiento y banda encendidos, `fijo=False`), y el de índices de arriba.

*Gate de mercado abierto (nuevo):* el último tick del símbolo tiene menos de 15 minutos. Es lo que
cubre fines de semana y el USD/CLP de madrugada, donde hoy `gate_agotamiento` deja pasar porque la vela
diaria es de ayer (`screener_gi.py:448-452`).

**Paso 2, plan elegible.** Con la **misma lectura** del paso 1 se arma el plan (`plan.armar`). Entra si:

- está **Armado** y el precio está a **1,0 ATR14 H1 o menos** del gatillo; o
- está **Activado** con la ruptura en una de las **2 últimas velas cerradas** y con **menos de la mitad**
  del recorrido típico (1,5 ATR) ya recorrido desde el gatillo.

`activacion_reciente` pasa a devolver también el índice de la vela de ruptura. Un plan Invalidado, sin
estructura, o activado hace más de 2 velas no entra: para un prospecto es llegar tarde.

**Paso 3, orden.** `factor_tecnico + factor_momentum` (sobre 55). El catalizador queda fuera porque no
sabe en qué dirección empuja; el espacio queda fuera porque mide contra el objetivo equivocado. Empates:
menor distancia al gatillo en ATR, después ticker alfabético. Es determinista: dos ejecutivos a la misma
hora reciben lo mismo.

**La pieza se arma con la lectura que la eligió.** Una segunda lectura del terminal puede encontrar el
precio del otro lado de la EMA 50 y sacar la pieza con la dirección contraria. Se garantiza inyectando
en `evaluar_activo` un analizador con memoria (`(ticker, marco) → lectura`, por pedido) y pasándole
esas mismas lecturas y la misma serie H1 a la preparación de la pieza. Los puntos salen de
`resultado["factores"]["tecnico"|"momentum"]["puntos"]`.

## Pieza

Tipo nuevo `oportunidad` en `esquema.CAMPOS`, con los mismos campos editoriales que `activo`. Reusa la
maqueta del `/activo` con estas diferencias:

- **Título** «Foco técnico del día · Oro».
- **Línea de transparencia** bajo el título: *"Elegido por el escáner de Grupo Inteligencia entre 10
  activos, el 09-10-2026 a las 10:40 (hora de Chile)"*. El número es el de activos evaluados.
- **Plan de escenarios sin estadística.** `datos.plan` se sella **sin** el bloque `estadistica`: si los
  números quedaran en los datos, `cifras_ajenas` los aceptaría en el texto de agy.
- **Frase fija** en lugar de la estadística: *"Un escenario técnico no anticipa el resultado: puede
  cumplirse o invalidarse, y por eso siempre trae su nivel de invalidación."*
- **Texto para un prospecto novato.** La instrucción a agy (`/analista`) lo pide más simple que el del
  analista; el resto de las reglas no cambia.
- Firma, franja ("Compartido por" con el nombre de quien la pidió) y pie, iguales al informe. El nombre
  identifica quién la compartió, no personaliza el contenido; quitarlo escondería quién responde por el
  envío.

## Candados extra (solo para `oportunidad`)

Además de los del informe (`FRASES_PROHIBIDAS`, CMF, HTML, cifras ajenas):

- **Captación:** "no te lo pierdas", "ultima oportunidad", "aprovecha", "asegurad", "ganancia segura",
  "oportunidad unica".
- **Estadística:** "acierta", "efectividad", "de las veces", "tasa de exito", y cualquier `%` en el texto.
- **Contrato:** la pieza renderizada no contiene la sección de estadística ni la palabra "oportunidad".

## Respuestas del bot

| Caso | Respuesta | agy | Cupo |
|---|---|---|---|
| Hay foco | El HTML, la línea de Drive y *"Compártelo tal cual: es análisis general, no una instrucción."* | sí | sí |
| Reuso válido | *"Ya está: es el de las 10:40"* + el mismo archivo | no | no |
| Ningún elegible | *"El escáner no encontró una configuración clara entre los 10 activos"* + motivos agrupados (p. ej. "4 sin recorrido, 2 por el dato de empleo, 3 lejos del gatillo") | no | no |
| MT5 o calendario caídos | *"No puedo leer el mercado ahora, prueba en unos minutos"* | no | no |

"MT5 caído" se distingue de "sin elegibles": si `_conectar_terminal()` avisa o **todos** los activos
salen excluidos por error del analizador, es infraestructura, no mercado.

## Reuso

Lo decide el estado local del bot (`Estado`, atómico), no Drive: Drive es solo la copia. Ventana
`reuso_minutos.oportunidad = 60`. **Antes de reusar se vuelve a leer** el H1 del activo elegido y se
comprueba que el plan sigue en el mismo estado, con el mismo gatillo, y que ningún blackout nuevo lo
cubre. Si algo cambió, se rehace la selección completa.

## Bitácora

Cada foco entregado se anota en `data/bitacora_planes_analistas.json` con `"tipo": "oportunidad"` (las
entradas existentes se leen como `"activo"`). Uso interno: en unos meses dice cómo le fue al foco del
día. El desenlace se mide desde la vela siguiente a la entrega, no desde la ruptura: es lo que le habría
pasado a quien lo recibió.

## Pauta para ventas

`docs/pauta-ventas-foco-tecnico.md`, una página: se comparte tal cual; no se agregan precios objetivo,
"entra hoy" ni promesas; si el prospecto pregunta cuánto invertir, se deriva a su ejecutivo de cuenta
con perfilamiento. El bot recuerda la regla en una línea en cada entrega.

## Fuera de alcance

Los evergreen (spec aparte), PDF, y cualquier envío automático a prospectos: el bot entrega al
ejecutivo, nunca al prospecto.

## Pruebas

- Selección con lecturas dobles: Armado cerca del gatillo gana a uno lejos aunque este tenga más
  puntaje de espacio; Activado de hace 3 velas no entra; Activado con 60 % del recorrido no entra;
  empate determinista.
- Calendario caído → sin foco; MT5 caído → mensaje de infraestructura; ningún elegible → motivos
  agrupados; ninguno de los tres gasta agy ni cupo.
- Gate de mercado abierto con tick viejo; US100 antes y después de `apertura_indices` en las tres
  configuraciones de desfase del año.
- `universo_ventas()`: incluye US100 y Brent, respeta `cubierto: false` del resto.
- La pieza sellada no trae `estadistica`; el render no trae la sección ni "oportunidad"; cada candado
  extra bloquea su frase y deja pasar el texto legítimo del `/activo`.
- Reuso: dentro de la ventana con el plan igual reusa sin agy; con el plan invalidado rehace.
- Bitácora con `tipo`; las entradas viejas siguen leyéndose.
- Prueba real con MT5: `--una "/oportunidad"` en horario de mercado y fuera de él.
