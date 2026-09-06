# El sistema inmune y la autonomía graduada

**Diseño técnico · 2026-09-05 · Grupo de Análisis de Mercado**

Diagrama de arquitectura: [`arquitectura-hooks.html`](arquitectura-hooks.html)

> **Continúa en [`cobertura-eventos-macro`](../cobertura-eventos-macro/2026-09-05-cobertura-eventos-macro-design.md).**
> Esa segunda parte enmienda tres cosas de aquí: las fases 3b y 3c quedan **después** de la
> cobertura de eventos, H13 pasa de opcional a **obligatorio**, y la ventana de Santiago se
> moverá de 17:30 a 19:30 cuando exista el disparador por evento. Este documento sigue siendo
> el piso: sin los guardrails y el gate, nada de lo que sigue puede publicar.

---

## 1. Qué problema resuelve

El repo tiene un modo de falla recurrente y documentado: **algo sale mal en silencio y llega
al cliente**. La lista no es hipotética, está escrita en `CLAUDE.md` con fecha:

| Cuándo | Qué llegó al canal |
|---|---|
| 2026-09-03 | Un mensaje al que le faltaban tres renglones (Imacec y dos de tasas), con el despacho reportando éxito |
| 2026-09-04 | Un PDF entregado como "Pendiente", invisible para el canal, y después el mismo informe duplicado |
| 2026-09-04 | Una pieza preguntando qué significaba el dato *para* un canal que no existe en WhatsApp |
| 2026-09-04 | Solana rindiéndose con titular y párrafo vacíos, y el despacho reportando dos piezas listas |
| 2026-09-03 | Tres piezas de forex con el recorrido diario consumido al 93 %, 290 % y 115 % |

Las cinco comparten forma: **el resultado se lee como correcto desde afuera**. Un mensaje al
que le faltan renglones no se ve incompleto. Un PDF "Pendiente" figura como enviado. Por eso
no basta con que el modelo tenga la regla escrita: hace falta algo determinista, siempre
encendido y fuera del criterio del modelo, que la verifique.

Eso son los hooks.

Y sobre esa base, la decisión del director del 2026-09-05: **el proyecto pasa a un enfoque de
automatización**, con envío autónomo acotado. Un envío sin ojo humano sube la exigencia sobre
los guardrails en vez de bajarla, así que las dos cosas se diseñan juntas.

## 2. La limitación que ordena todo el diseño

**Un hook solo corre mientras hay una sesión de Claude Code abierta.**

De ahí se sigue que la producción autónoma 24/7 no puede vivir en un hook: si colgara de ahí,
dejaría de salir al cerrar el terminal. Vive donde ya vive, en `scripts/reloj_gi.py` bajo el
Programador de tareas.

Entonces hay **dos mitades que ejecutan el sistema**, y el riesgo obvio es que cada una
desarrolle su propio criterio. Ese es exactamente el defecto recurrente del repo, el de los
contratos de nombres: dos módulos que se hablan sin que nada verifique que coinciden (`TPM_CHILE`
contra `TPM`, los `digits` del cobre declarados con tres valores distintos, `exigir_texto_editorial`
existiendo en una ruta de render y no en la otra).

**La respuesta es un solo módulo compartido, y tests de contrato que fallan si alguna mitad
deja de llamarlo.**

```
┌─ SESIÓN DE CLAUDE CODE (efímera) ─┐   ┌─ PROGRAMADOR DE TAREAS (24/7) ─┐
│  13 hooks sobre 7 eventos         │   │  reloj_gi.py · latido 15 min   │
└──────────────┬────────────────────┘   └───────────────┬────────────────┘
               │                                        │
               └────────► scripts/guardrails/ ◄─────────┘
                          funciones puras
                                 │
                          puede_despachar()
                                 │ solo si ok
                                 ▼
                     enviar_whatsapp.py ──► los 7 canales
```

## 3. El módulo compartido

### 3.1 Ubicación y forma

`scripts/guardrails/`, siete módulos de **funciones puras**: reciben datos, devuelven un
veredicto, no escriben nada y **nunca lanzan**.

| Módulo | Qué decide | Sobre qué se apoya |
|---|---|---|
| `texto_cliente.py` | guion largo, sigla sin explicar, tono catastrófico, voseo, canal inexistente | `data/glosario_siglas.json`, `config/whatsapp_grupos.json` |
| `precios.py` | decimales contra `digits`, precio literal en código (Regla 1) | `config/activos.json` |
| `nombres.py` | tickers del catálogo, marcos canónicos, alias de canal, rutas de cliente | `catalog.load_valid_tickers`, `pipeline_carrusel.MARCOS_CANONICOS` |
| `temporal.py` | anacronismos, hora canónica de Chile | envuelve `validar_consistencia_temporal.py` |
| `shell.py` | here-string con `$` que trunca precios en PowerShell | — |
| `estado.py` | frescura, broker real por activo, cupo, cadencia, sesión, momento, rama | envuelve `pipeline_datos.py --estado`, `agenda_mercado.py` |
| `despacho.py` | **`puede_despachar()`** | todos los anteriores + la política de autonomía |

Ninguno reimplementa lo que ya existe. `temporal.py` y `estado.py` son envoltorios: una
segunda regla de vencimiento o una segunda fórmula de anacronismo serían el mismo error que
tener dos fórmulas de ATR.

### 3.2 El contrato del veredicto

```python
@dataclass(frozen=True)
class Veredicto:
    ok: bool
    motivo: str            # slug estable: "guion_largo", "cupo_agotado", ...
    detalle: str           # una frase en español, para el humano
    ubicacion: str | None  # "línea 12", "USDCLP", "02_forex_divisas"
```

Un veredicto negativo **siempre** nombra su motivo, igual que las exclusiones del escáner. El
mismo slug se lee idéntico en un rechazo de hook, en el registro del reloj y en un fallo de
pytest, porque los tres leen el mismo diccionario `guardrails/motivos.py`.

Ese diccionario copia el patrón que ya funciona en `suplemento_canal.py`: cada motivo declara
su texto y su bandera `publicable`. **Un problema nuestro de datos no es contenido para el
cliente**, y esa distinción ya está resuelta ahí; no se inventa otra.

> **Test de contrato obligatorio:** todo slug que cualquier módulo pueda emitir tiene entrada
> en `motivos.py`. Sin eso, el sistema puede rechazar algo y no saber decir por qué.

### 3.3 Qué es una "ruta de cliente"

Definido en un solo lugar, `nombres.es_ruta_de_cliente(path)`:

```
data/mensajes/**                 piezas aprobadas y guardadas
data/stories/**/*.json           payloads de tanda
templates/stories/*.html         texto que viaja dentro de la pieza
```

Cualquier escritura sobre esas rutas pasa por los guardrails de texto de cliente. Cualquier
otra, no. Que la definición viva en una función y no repartida por los hooks es lo que impide
que un hook nuevo se olvide de una carpeta.

## 4. Los hooks

**13 hooks sobre 7 eventos.** Dos ya existen (`hook_ingesta_macro.py`, sin commitear en la
rama `feat/hook-ingesta-macro`); once son nuevos.

### 4.1 Mecánica que condiciona el diseño

Verificado contra la documentación vigente de Claude Code el 2026-09-05:

- **`SessionStart` y `Setup` solo admiten `command` y `mcp_tool`.** No admiten `prompt` ni
  `agent`. Por eso el brief operativo es un script, no una consulta a un modelo.
- **`FileChanged`, `SessionEnd` y `ConfigChange` tampoco admiten `prompt` ni `agent`.**
- `PermissionRequest`, `PreToolUse`, `PostToolUse` y `Stop` admiten los cinco tipos.
- **El contexto se inyecta anidado**, nunca en la raíz del JSON:
  `{"hookSpecificOutput": {"hookEventName": "...", "additionalContext": "..."}}`. En la raíz
  se ignora en silencio.
- **Un `PreToolUse` bloquea** con `permissionDecision: "deny"` más su razón, o con salida 2 y
  el motivo por stderr.
- **Un hook `prompt` devuelve `{ok, reason, impossible}`.**
- **Timeout por defecto: 600 s en casi todos los eventos y 30 s en `UserPromptSubmit`.** Ese
  límite de 30 s es un techo, no un objetivo: ese hook corre en cada mensaje.

### 4.2 Contexto vivo (no bloquean)

| ID | Evento | Tipo | Qué inyecta | Presupuesto |
|---|---|---|---|---|
| H1 | `SessionStart` | command | *(existe)* estado de la ingesta macro | < 1 s |
| H2 | `SessionStart` | command, async | *(existe)* refresco si está vencida | 600 s |
| H3 | `SessionStart` | command | **Brief operativo** | < 1 s |
| H4 | `UserPromptSubmit` | command | **Contexto del prompt** | **< 200 ms** |
| H10 | `FileChanged` | command | Aviso de datos reescritos | < 200 ms |
| H11 | `PreCompact` | command | Volcado del estado de la tanda | < 1 s |

**H3 · Brief operativo.** Un solo bloque con: hora canónica de Chile, sesión de mercado activa,
momento del día pendiente y su ventana de gracia, cupo de envíos restante y segundos desde el
último, rama git y si es `master`, frescura del sesgo, y **qué activos vinieron de yfinance en
vez de MT5**. Ese último dato es el que costó una hora de diagnóstico el 2026-09-02, cuando
cinco de seis activos salieron de futuros mientras la cadena reportaba `[OK] precios`.

**H4 · Contexto del prompt.** Solo stdlib, sin red, sin MT5. Si el prompt nombra un activo del
catálogo, inyecta sus `digits` y su ticker MT5 exacto. Si nombra un canal, su `nombre_oficial`
real. Si nombra hora o fecha, el reloj. Es el hook de mayor retorno por línea escrita: mata de
raíz tres contratos de nombres que ya produjeron piezas mal publicadas.

**H10 · Datos reescritos.** El refresco async de H2 reescribe `macro_bias_output.json` y los
JSON de `data central/` **bajo los pies de la conversación**. Citar una cifra leída antes de
ese punto es publicar el dato de anoche con fecha de hoy. `CLAUDE.md` ya nombra este riesgo;
esto lo hace visible en el momento en que ocurre.

**H11 · Volcado antes de compactar.** El despacho es idempotente por bitácora, pero el modelo
perdiendo contexto a mitad de tanda es un riesgo distinto: deja de saber qué canales ya
salieron. Vuelca tanda en curso y canales despachados a `data/logs/`.

### 4.3 Guardias (bloquean)

| ID | Evento · matcher | Bloquea |
|---|---|---|
| H5 | `PreToolUse` · `Write\|Edit` en rutas de cliente | guion largo, decimales ≠ `digits`, sigla sin explicar, anacronismo, canal inexistente |
| H6 | `PreToolUse` · `Bash\|PowerShell\|WebSearch` | here-string con `$` que trunca precios · `git commit`/`push` en `master` · WebSearch preguntando hora o fecha |
| H7 | `PreToolUse` · `Bash\|PowerShell` con `enviar_whatsapp.py` en el comando | **el gate**: delega en `puede_despachar()` |
| H8 | `PreToolUse` · `Write\|Edit` en `scripts/`, `src/` | precio literal junto a un ticker (Regla 1) |
| H9 | `PostToolUse` · plantillas, comandos, `activos.json` | corre los `--check` que ya existen y devuelve el error como feedback |

**H6 y H7 comparten matcher y eso está bien.** Los dos se registran sobre `Bash|PowerShell` y
Claude Code corre ambos: el matcher decide qué comandos *inspecciona* cada hook, y cada uno
decide por su cuenta si el comando le incumbe. H6 mira here-strings y `git`; H7 mira solo la
invocación del sender. Un hook al que el comando no le incumbe sale con 0 y no opina.

**El matcher tiene que nombrar los dos shells.** Este entorno expone `Bash` **y** `PowerShell`
como herramientas separadas. Un matcher que solo diga `Bash` deja la mitad de los comandos sin
guardia, y la regla del truncado de `$` es específicamente de PowerShell.

**H9 no inventa validaciones.** Llama a `marca_tokens.py --check`, `sincronizar_css_plantillas.py
--check` y `agy_workflows.py --check`, que ya existen y ya los corre la suite. Lo que agrega es
adelantar el fallo al momento de la edición en vez del momento del test.

### 4.4 Los dos caros

Nacen **apagados**, para medir si pagan antes de dejarlos fijos. El interruptor es
`config/hooks_gi.json`: un objeto de `{ "<id del hook>": true | false }` que el propio hook
consulta al arrancar y, si está en `false`, sale con 0 sin hacer nada. Va en config y no en
`settings.json` para que apagarlos no obligue a editar el registro de hooks ni a reiniciar la
sesión.

**H12 · `Stop`, tipo `agent`.** Si la sesión tocó `scripts/`, `src/` o `config/`, corre los
tests de contrato y no deja cerrar en rojo. Si quedaron piezas preparadas sin despachar ni
descartar, lo dice. Costo: una invocación por sesión, y solo cuando hubo cambios.

**H13 · `PreToolUse`, tipo `prompt`, sobre texto de cliente.** Revisa lo que ninguna expresión
regular ve: tono, jerga sin traducir, español chileno, y si la dirección del activo quedó clara
en menos de 30 segundos. Devuelve `{ok, reason}`. Costo: una llamada por pieza guardada.

H13 **complementa a H5, no lo reemplaza.** Las reglas mecánicas (guion largo, decimales) siguen
en H5, que es determinista y gratis. Un modelo no es el lugar donde verificar que `$889.60`
lleva dos decimales.

## 5. El gate de autonomía

### 5.1 La firma, y por qué lleva `origen`

```python
def puede_despachar(
    pieza: Pieza,
    canal: str,
    ahora: datetime,
    *,
    origen: Literal["director", "autonomo"],
) -> Veredicto
```

`Pieza` no es una clase nueva: es el payload que `pipeline_carrusel.py --rendir` ya produce,
tipado con un `TypedDict` para que el gate pueda leer su tipo, su canal y su texto sin
adivinar claves.

`origen` es la parte que no es obvia. Un despacho que el director lanza a mano **no** debe
quedar bloqueado por estar fuera de la ventana de autonomía: la ventana existe para acotar lo
que el sistema hace solo, no para limitar al director. Pero sí tiene que pasar por cupo,
cadencia, perfil de Chromium y guardrails de texto.

| Verificación | `director` | `autonomo` |
|---|---|---|
| Guardrails de texto de cliente | sí | sí |
| Campo editorial vacío | sí | sí |
| Cupo diario (40) y cadencia (45 s) | sí | sí |
| Un solo dueño del perfil de Chromium | sí | sí |
| Ventana horaria y días, en el ancla que corresponda (§5.4) | no | sí |
| Canal, momento y tipo autorizados | no | sí |
| Sub-cupo autónomo | no | sí |
| Interruptor de corte | no | sí |

### 5.2 La política

`config/autonomia_envio.json`, versionado, con todo cerrado al empezar:

```jsonc
{
  "habilitada": false,
  "ventanas": {
    "ancla_por_defecto": "America/New_York",
    "por_ancla": {
      "America/New_York": { "desde": "08:00", "hasta": "18:00" },
      "America/Santiago": { "desde": "08:00", "hasta": "17:30" }
    },
    "anclaje_santiago": {
      "tickers": ["USDCLP"],
      "paises_del_evento": ["chile"]
    }
  },
  "dias": ["lun", "mar", "mie", "jue", "vie"],
  "canales_autorizados": ["banco_de_pruebas"],
  "momentos_autorizados": ["premercado_fx", "cripto", "apertura_indices"],
  "tipos_autorizados": {
    "generado": ["contexto_macro", "suplemento_canal"],
    "diferido": ["niveles"]
  },
  "cupo_autonomo": 6,
  "requiere_guardrails_verdes": true
}
```

Cuatro decisiones, con su razón (qué se puede despachar solo va en §5.3 y el anclaje de la
ventana en §5.4):

1. **Todo es lista blanca, nunca lista negra.** Un tipo de pieza nuevo queda denegado por
   defecto hasta que alguien lo autorice explícitamente. Con lista negra, cada pieza nueva
   nacería autorizada y nadie se enteraría.
2. **El sub-cupo es sub-cupo.** Los 6 autónomos salen de los 40 diarios, no se suman. Los
   frenos de 45 s y 40 al día **no se tocan**: existen porque automatizar WhatsApp Web va
   contra sus términos de servicio y el número es el del negocio.
3. **Las señales y el informe en PDF quedan fuera.** No están en `tipos_autorizados` y no
   deben entrar. Son las piezas donde un error cuesta plata del cliente, y el PDF ya se
   duplicó una vez. Qué sí entra, y por qué el resto no puede, está en §5.3.
4. **Arranca solo en `GI · Banco de Pruebas`**, que ya existe desde el 2026-09-03 justamente
   para medir contra el DOM sin tocar un canal de clientes. Los canales reales entran cuando
   la bitácora muestre una semana limpia.

### 5.3 Qué se puede despachar solo, y qué la arquitectura no permite

**El primer borrador de este spec proponía `["niveles", "contexto_macro"]` y estaba mal en la
mitad que más importa.** Verificado en el código el 2026-09-05:

- `pipeline_carrusel.CAMPOS_EDITORIALES` es `("titular", "parrafo")`, y `exigir_texto_editorial`
  **detiene el render** si alguno está vacío.
- `reloj_gi._correr_preparar` corre exactamente `pipeline_carrusel.py --preparar --grupo <canal>`
  y nada más, dejando esos campos en `_pendiente_editorial`.

Es decir: **el reloj no puede rendir una pieza de niveles, y lo que no se puede rendir no se
puede despachar.** No es una restricción de política, es la arquitectura. Cualquier promesa de
"el sistema publica niveles solo" sería falsa hasta que un modelo escriba ese texto.

En cambio hay dos tipos que **no tienen ningún campo editorial** y por tanto sí se generan
enteros sin nadie:

- **`contexto_macro`**: `contexto_macro_grupos.py` lleva los titulares escritos en el código en
  tres variantes (`titular_sube` / `titular_baja` / `titular_plano`) y elige según la dirección
  del dato. Las cifras salen del terminal.
- **`suplemento_canal`**: se arma de los motivos de exclusión que el escáner ya escribió, con
  su concepto elegido por el motivo. Es "solo texto, por fase" por diseño.

#### De ahí salen dos modos, y conviene nombrarlos distinto

| Modo | Qué es | Quién escribe el texto |
|---|---|---|
| **Generado** | El reloj lo produce y lo despacha. Nadie miró. | El código |
| **Diferido** | Una sesión escribió el texto y dejó la tanda aprobada; el reloj la despacha al llegar el momento. | Una sesión, antes |

El modo diferido es el que da la capacidad que de verdad se pidió: **escribís a las 08:00 y
sale a las 10:00 sin que estés**. El humano sigue en el circuito, solo que desacoplado en el
tiempo. Y cuesta casi nada, porque el pipeline ya tiene todo salvo la marca.

Esa marca es `_aprobada_para_despacho`, que una sesión escribe en el payload junto con la
**huella del texto aprobado**. `puede_despachar` exige las dos cosas y **vuelve a calcular la
huella**: si el texto cambió después de la aprobación, la pieza no sale. Sin eso, "aprobado"
sería una casilla y no una afirmación sobre un contenido concreto.

La regla que ordena todo:

> Una pieza **con** campos editoriales solo se despacha en modo diferido, con marca y huella
> válidas. Una pieza **sin** campos editoriales solo se despacha en modo generado, y solo si su
> tipo está en la lista. No hay tercera vía.

#### El sub-cupo, derivado en vez de inventado

**`cupo_autonomo: 6`.** El propósito del sub-cupo no es modular volumen (de eso ya se encargan
los momentos) sino **acotar el radio de daño** si algo entra en bucle. Con la configuración
inicial —1 canal × 3 momentos, más un suplemento eventual— el tráfico legítimo máximo es 4 al
día. Seis deja margen sin que un bucle pueda gastar el cupo del director.

**Y hay una consecuencia que conviene saber antes de expandir:** con los 7 canales autorizados,
7 × 3 momentos son **21 envíos autónomos al día**, más de la mitad del tope diario de 40. El
día de mayor tráfico medido fueron 22 envíos totales. Así que habilitar todos los canales a la
vez no es una decisión de configuración, es un cambio de escala del uso de la cuenta.

Por eso el sub-cupo **se recalcula cada vez que se agrega un canal**, y hay un test que falla
si queda por debajo del tráfico legítimo de la configuración vigente: autorizar un canal y
descubrir en producción que el cupo lo estrangula es exactamente la clase de falla silenciosa
que este diseño combate.

### 5.4 El anclaje de la ventana: Nueva York, salvo lo chileno

**Decisión del director, 2026-09-05.** La ventana se ancla a **Nueva York**, excepto para el
USD/CLP y los datos del Banco Central de Chile, que se anclan a **Santiago**.

No es una preferencia: es la misma razón por la que existe el campo `zona` en
`config/agenda_mercado.json`. Ese archivo ya declara `zona_ancla: America/New_York` y permite
que un momento se ancle a otro reloj, y `CLAUDE.md` ya anticipaba este caso exacto: *"un
premercado del USD/CLP tendría que ir anclado a Santiago, porque con el desfase en su máximo
las 08:30 de Nueva York caen hora y media después de que Santiago abrió"*. Una ventana anclada
a Nueva York autorizaría la pieza del USD/CLP cuando su propio mercado ya lleva rato operando.

**El orden de resolución es fijo y gana el primero que resuelve:**

1. El activo protagonista de la pieza está en `anclaje_santiago.tickers` → **Santiago**.
2. La pieza es de dato macro y el país de su evento está en
   `anclaje_santiago.paises_del_evento` → **Santiago**.
3. Cualquier otro caso → **`ancla_por_defecto`**, hoy Nueva York.

Que el orden sea fijo es lo que hace la decisión reproducible. Una pieza que mencione a la vez
a la Fed y al BCCh resuelve por su protagonista, no por cuál se nombró primero en el texto.

#### El vocabulario es el del escáner, y está en inglés

`obtener_calendario_macro` devuelve el país en **inglés** (`Chile`, `United States`), y
`screener_gi._BLACKOUTS` ya lo consume así: `paises: ("chile",)` en minúscula, con
`alcance: "USDCLP"` para la reunión de política monetaria del BCCh.

El gate usa **esa misma normalización**, no una propia. Escribir el patrón en español dejaría
el filtro inerte sin que nada avise, que es un error que este repo ya cometió. Y como esto crea
un cruce nuevo entre dos módulos que se hablan por nombre, **lleva su test de contrato** (§8).

#### El desfase no se escribe en ninguna parte

Las horas se guardan como hora de pared en su zona y se convierten **en el instante de
evaluar**. Chile y Estados Unidos cambian de horario en sentido opuesto, así que el desfase se
mueve dos veces al año. Un offset fijo es el error de ±1 h del issue #38.

#### La consecuencia práctica, que parece un bug y no lo es

Durante buena parte del año las dos ventanas no coinciden vistas desde Chile:

| Desfase | Ventana de Nueva York, en hora Chile | Ventana de Santiago | Franjas asimétricas |
|---|---|---|---|
| NY+0 (hasta el 5 sep 2026) | 08:00–18:00 | 08:00–18:00 | ninguna |
| NY+1 (desde el 6 sep 2026) | 09:00–19:00 | 08:00–18:00 | 08–09 solo chileno · 18–19 solo NY |
| NY+2 (desde el 1 nov 2026) | 10:00–20:00 | 08:00–18:00 | 08–10 solo chileno · 18–20 solo NY |

En noviembre, entre las 08:00 y las 10:00 de Chile el sistema podrá despachar el USD/CLP y no
el oro. Eso es correcto y es el punto de la decisión, pero visto en vivo se lee como una falla,
así que el motivo de la denegación lo dice con todas sus letras: `fuera_de_ventana`, nombrando
el ancla que se aplicó y su horario local.

#### La ventana de Santiago cierra 17:30, y ese número no es simétrico por casualidad

El borrador tenía 18:00 por simetría con Nueva York. **Verificado el 2026-09-05 contra el
Banco Central de Chile: el comunicado de la RPM se publica a las 18:00 hora de Chile**, y la
próxima reunión es el **martes 8 de septiembre de 2026**. La ventana simétrica cerraba exacto
en el instante del dato más importante del trimestre para el USD/CLP.

`screener_gi._BLACKOUTS` aplica a la RPM una ventana de **−15 / +45 minutos**, así que el
blackout corre de **17:45 a 18:45** y la pieza de reacción no podría salir antes de las 18:45.

Había dos salidas y se toma la conservadora:

| Opción | Efecto |
|---|---|
| `hasta: "19:30"` | El sistema publica solo la reacción a la RPM |
| **`hasta: "17:30"`** | **La ventana cierra antes del blackout; la RPM la publica el director** |

**Se elige 17:30.** La RPM es el evento chileno de mayor consecuencia del trimestre y no puede
ser el debut autónomo del sistema. Ocho veces al año, esa pieza la escribe y la manda una
persona.

Y como "17:30 cae antes de 17:45" es una coincidencia que un futuro ajuste podría romper sin
darse cuenta, **queda fijado por un test**:
`test_la_ventana_de_santiago_cierra_antes_del_blackout_de_la_rpm`. Si alguien extiende la
ventana, el test le dice que está autorizando la RPM en automático. Eso pasa a ser una
decisión, y no un descuido.

El resto de la agenda chilena no se ve afectada: el Imacec sale **08:30** hora de Chile, según
el propio calendario del 2026-09-01, bien dentro de la ventana.

#### El día se evalúa en la misma zona que la hora

`dias` se comprueba contra la fecha **en la zona que resolvió el anclaje**, no en una fija. Con
dos anclas y una sola zona para el día, un viernes por la tarde podría contarse como sábado
para una mitad del sistema y no para la otra.

### 5.5 El interruptor de corte

`data/.autonomia_off`. Si el archivo existe, todo despacho con `origen="autonomo"` queda
denegado. El director no se ve afectado.

Es un archivo y no un campo del config a propósito: cortar tiene que ser una acción de un
segundo, sin editar JSON, sin reiniciar nada y sin riesgo de dejar el config mal formado
justo en el momento en que hay un problema.

Se consulta en **dos puntos**: el reloj lo mira en cada latido (efecto en ≤ 15 min) y el gate
lo mira en el instante del despacho (efecto inmediato sobre lo que ya está en vuelo).

Gitignoreado, mismo criterio que `data/.reloj_disparos.json`: es estado generado, no historia
editorial.

## 6. Manejo de errores: la asimetría es el diseño

**Los hooks de contexto fallan hacia abierto.** Un error de red del BCCh no puede impedir abrir
Claude Code. Todo error se traga y se reporta como texto, igual que hoy hace
`hook_ingesta_macro.py`.

**Los guardias de escritura fallan hacia abierto, pero ruidosamente.** Si `texto_cliente.py`
revienta, bloquear toda escritura dejaría la sesión inutilizable. Se permite la escritura y se
inyecta un aviso visible de que el guardia **no corrió**. Un guardia caído en silencio es peor
que no tenerlo, porque genera confianza falsa.

**El gate de despacho falla hacia CERRADO.** Si `puede_despachar()` lanza, no sale nada.

Esa asimetría es deliberada y es el corazón del diseño: **un error en el mecanismo que protege
al cliente no puede abrir la puerta.** Y es también la razón por la que `puede_despachar` es la
única función del módulo que tiene permitido propagar una excepción hacia arriba: quien la
llama debe tratarla como denegación.

## 7. Qué cambia en lo que ya existe

### 7.1 El test del reloj se reescribe, no se borra

Hoy `tests/test_reloj_gi.py:151` prohíbe que `reloj_gi.py` mencione `enviar_whatsapp`,
`whatsapp_sender`, `--despachar` o `despachar(`. Bajo el nuevo enfoque ese invariante ya no
corresponde, pero **borrarlo dejaría el envío sin ninguna protección estructural**.

Pasa a ser dos invariantes:

```python
def test_el_reloj_no_llama_al_sender_directo():
    """reloj_gi.py no puede nombrar whatsapp_sender ni enviar_whatsapp."""

def test_todo_despacho_pasa_por_el_gate():
    """Toda llamada al sender vive en un sitio que llama antes a puede_despachar."""
```

El segundo es el que de verdad protege, y es el mismo patrón que ya existe para
`exigir_texto_editorial`: hay un test que falla si alguna de las dos rutas de render deja de
llamarla, porque se descubrió que **el único camino sin freno era justamente el que llegaba al
cliente**.

### 7.2 `CLAUDE.md`

Tres cambios, y son reescritura, no parche:

- La sección *"Flujo de aprobación → WhatsApp (modo semi-automático activo)"* pasa a
  **"Autonomía graduada de despacho"**. La regla deja de ser *"nunca se envía sin aprobación"*
  y pasa a *"fuera de la ventana, los canales, los momentos y los tipos autorizados, nunca se
  envía sin aprobación"*, con el interruptor de corte nombrado.
- Sección nueva **"El sistema inmune: los hooks"**, con los 13 y la razón de cada uno.
- El párrafo del reloj deja de afirmar que solo prepara, y pasa a describir el gate.

### 7.3 El hook de ingesta se mueve

De `scripts/hook_ingesta_macro.py` a `scripts/hooks/hook_ingesta_macro.py`, con los demás. Se
actualizan `.claude/settings.json` y el párrafo de `CLAUDE.md`. Es barato ahora, porque ese
trabajo todavía está sin commitear.

## 8. Pruebas

Cada módulo de `guardrails/` lleva su test unitario. Además, **diez tests de contrato**, que
son los que impiden que el sistema se desarme con el tiempo:

| Test | Qué impide |
|---|---|
| `test_todo_motivo_tiene_entrada` | rechazar algo sin saber decir por qué |
| `test_todo_despacho_pasa_por_el_gate` | una segunda ruta al sender sin freno |
| `test_el_reloj_no_llama_al_sender_directo` | saltarse el gate desde el reloj |
| `test_hooks_registrados_existen` | un `settings.json` que apunta a un script borrado |
| `test_matchers_cubren_los_dos_shells` | un guardia que solo mira `Bash` y deja pasar PowerShell |
| `test_ancla_usa_el_vocabulario_del_escaner` | escribir "Chile" donde el calendario dice `chile`, y dejar el anclaje inerte |
| `test_las_dos_ventanas_en_los_tres_desfases` | que el USD/CLP se juzgue con el reloj de Nueva York |
| `test_la_ventana_de_santiago_cierra_antes_del_blackout_de_la_rpm` | autorizar la RPM en automático sin darse cuenta |
| `test_todo_tipo_generado_no_tiene_campos_editoriales` | prometer despacho autónomo de una pieza que el reloj no puede rendir |
| `test_el_subcupo_alcanza_para_los_canales_autorizados` | autorizar un canal y descubrir en producción que el cupo lo estrangula |

**`test_las_dos_ventanas_en_los_tres_desfases`** recorre las tres configuraciones del año
(NY+0, NY+1, NY+2) y verifica las franjas asimétricas de la tabla de §5.4. Es el mismo patrón
que ya usa el test de momentos que no se pueden pisar, y por la misma razón: un error de
anclaje **solo aparece medio año después**, cuando ya nadie recuerda que se tocó esto.

**`test_todo_tipo_generado_no_tiene_campos_editoriales`** es el que habría atajado el error de
la primera versión de este spec, que prometía despacho autónomo de las piezas de niveles sin
notar que `exigir_texto_editorial` las detiene. Compara `tipos_autorizados.generado` contra los
campos que cada tipo declara, y falla si alguno pide texto que nadie va a escribir.

`test_hooks_registrados_existen` merece una nota: un hook mal referenciado **no rompe nada
visiblemente**. La sesión abre igual y el guardia simplemente no corre. Es el mismo modo de
falla silenciosa que motiva todo este diseño, aplicado al diseño mismo.

## 9. Fases de construcción

Una rama y un PR por fase, en orden de retorno.

| Fase | Qué entra | Por qué va ahí |
|---|---|---|
| **0** | Commitear el hook de ingesta pendiente | Está terminado y documentado, y bloquea el resto |
| **1** | `guardrails/` + H5, H6, H8 | Máximo retorno: cubre las fallas que ya llegaron al cliente |
| **2** | H3, H4 | Barato, y elimina el error de nombres de raíz |
| **3a** | `despacho.py` + H7 + política + tests reescritos + `CLAUDE.md` | El gate. Depende de la fase 1 |
| **3b** | Despacho autónomo **generado** (`contexto_macro`, `suplemento_canal`) en el banco de pruebas | Lo único que el reloj puede producir entero hoy |
| **3c** | Despacho autónomo **diferido**: marca `_aprobada_para_despacho` y su huella | Da el "escribo a las 08:00 y sale a las 10:00" sin sacar al humano |
| **4** | H9, H12, H13 | Los caros, medibles y apagables |
| **5** | H10, H11 | Cierre |

La fase 3 se parte en tres porque **3b es la primera vez que algo sale al mundo sin que nadie
lo mire**. Merece su propio PR, su propia semana de observación en el banco de pruebas y su
propia decisión de seguir, en vez de viajar dentro del PR que construye el gate.

## 10. Lo que queda fuera, a propósito

- **`SessionEnd`**: iba a liberar el lock de ingesta huérfano, pero ese lock **ya expira solo a
  los 15 minutos**. Un hook que duplica un mecanismo existente es fricción.
- **`Notification` con aviso de escritorio**: cómodo, pero no previene ninguna falla
  documentada.
- **`TaskCreated`, `TaskCompleted`, `ConfigChange`, `TeammateIdle` y los hooks `http`**: ningún
  problema real del repo los pide hoy.
- **Un modelo dentro del reloj.** Sería el tercer modo: el reloj invoca a Claude Code headless
  o a Antigravity para que escriba el titular y el párrafo, y despacha piezas de niveles sin
  que nadie las haya leído. Es técnicamente alcanzable (la invocación de `agy` está medida y
  documentada) y queda **fuera de este diseño a propósito**: el modo diferido de §5.3 entrega
  la mayor parte del valor —la pieza sale a la hora exacta sin que estés— conservando a una
  persona en el circuito. Meter un modelo ahí es una decisión de otra magnitud y merece su
  propio spec, tomada mirando cómo se comportó lo anterior.

El criterio es uniforme: **un hook que no previene una falla documentada es fricción**, y la
fricción diaria es lo que hace que la gente termine desactivando el sistema entero.

## 11. Riesgos aceptados

Dos, y el director los conoce:

1. **Automatizar WhatsApp Web va contra sus términos de servicio**, y el número es el del
   negocio. Más volumen autónomo es más riesgo de que la cuenta sea marcada. Se mitiga con el
   sub-cupo de 6, los frenos intactos de 45 s y 40 al día, y el arranque solo en el banco de
   pruebas. No se elimina.
2. **Un envío sin ojo humano puede publicar un error que nadie vio.** El 2026-09-04 un falso
   negativo de confirmación duplicó un informe, y el falso positivo del mismo día lo dio por
   entregado cuando había quedado "Pendiente". Se mitiga con la lista blanca de tipos (sin
   señales, sin PDF), el interruptor de corte y la bitácora por pieza. No se elimina.

Ninguno de los dos es razón para no hacerlo. Los dos son razón para que la autonomía crezca
midiendo, y no de una vez.
