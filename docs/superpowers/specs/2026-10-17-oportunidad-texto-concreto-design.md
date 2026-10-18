# `/oportunidad`: texto concreto, fechado y con bancos

Fecha: 2026-10-17. Amplía `2026-10-16-oportunidad-por-activo-design.md` (secciones 6, 7, 8 y 9).
Lo demás de ese spec sigue igual: vigencia de 7 días, agy solo redacta y Python sella `pieza.json`,
nada invita a operar (solo a revisar en MT5), el bot no toca el envío a WhatsApp, el texto no dice
"oportunidad" ni "recomendación", y `comercial.INVITACION_ACTIVA` de `/seguimiento` no se toca.

## 1. El problema, con la corrida que lo mostró

`data/informes_analistas/2026-10-17/110748_oportunidad_xauusd/` (oro, sábado 17/10, 11:07):

- `editorial.contexto` dice "la cotización del oro responde a las tasas reales y a las decisiones de
  la Fed, donde un avance del DXY suele limitar la demanda...": ninguna cifra, ningún hecho del día.
- `editorial.fuentes` salió `[]` y `datos.agenda_semana` salió `[]`.
- `datos.drivers` es la lista fija del catálogo (`config/activos.json`): nombres, no estados.

El director pidió que ese texto se desarrolle sí o sí. El ejecutivo necesita un correo con
herramientas concretas y fechadas: qué pasa hoy con el Dollar Index, la Fed y la tasa real; los
días clave de los 7 días de vigencia, con la imagen del calendario; y la postura de 2 o 3 bancos
con el enlace a la nota.

### Causa raíz (verificada en el código)

1. **agy no tenía hechos que citar.** `preparar_oportunidad` entrega `drivers` como nombres del
   catálogo (`_drivers`), sin medir ninguno. El Dollar Index no se lee en ninguna parte del bot
   (existe en MT5 como `USDIDX`, `digits = 3`, verificado hoy en la cuenta 51257).
2. **El prompt le ordenaba ser genérico.** `.claude/commands/analista.md`, regla 2 y campo
   `contexto`: "un driver se afirma como hecho solo si está ahí; si no, se explica como mecanismo
   condicional". Con solo nombres, agy hizo exactamente eso. La curva sí traía la tasa real
   (2,78 por ciento, 6 pb abajo en el día y 14 pb en 5) y no la usó, porque nada se lo exigía.
3. **El validador solo prohíbe cifras, nunca exige ninguna.** `esquema.cifras_ajenas` rechaza lo
   inventado; un texto sin una sola cifra pasa limpio.
4. **La agenda pide solo la semana en curso.** `pipeline_linkedin.leer_agenda` llama a
   `cargar_calendario`, que pide la pestaña `thisWeek` de Investing.com (domingo a sábado). Un
   sábado a las 11:07 esa semana ya terminó: la ventana de 7 días cae entera en `nextWeek`, que
   nadie pide. Además, si Investing.com falla, `_fetch_calendario` devuelve la caché vencida sin
   avisar (hoy el `nextWeek` en disco es del 2 de octubre), así que una agenda vacía no distingue
   "no hay datos" de "no respondió".
5. **`fuentes = []` estaba permitido en todas las capas.** El prompt dice "si no encuentras nada
   atingente, deja `fuentes` como lista vacía", `esquema.errores` acepta la lista vacía, el bot
   solo agrega el aviso "Sin voces..." y el spec del 16 lo daba por válido (sección 7, último
   punto). La salida de agy no se guarda, así que no hay forma de saber si buscó: los 4 min 47 s
   de la corrida, contra los 7 a 11 min medidos con búsqueda web, sugieren que no.
6. **El correo no llevaba nada de eso.** `_bloque_correo` incluye solo `contexto`: la curva, la
   agenda y las voces viven en la ficha del ejecutivo y no viajan al cliente.

## 2. Qué mide Python: `datos.hechos`

Un módulo nuevo, `scripts/analista/hechos.py`, mide los drivers del activo antes de llamar a agy.
Qué se mide y con qué signo sale de `config/drivers.json` (la `correlacion` declarada de cada
driver), no del código:

| Medible | Fuente | Driver de `drivers.json` que lo activa |
|---|---|---|
| `dxy` (Dollar Index) | MT5 `USDIDX` D1; respaldo `indices_referencia.serie_diaria("DXY")` | `dollar_index` |
| `tasa_real` (TIPS 10 años) | curva `DFII10` (`get_curva_tasas`) | `tasas_reales` |
| `bono_10` (Tesoro 10 años) | curva `DGS10` | `rendimientos_treasury` |
| `fed` (fondos federales) | curva `DFF` + decisión de la Fed en la agenda de la ventana | `decisiones_fed`, `tasas_fed` |
| `cobre` | MT5 `COPPER` D1 | `cobre` |
| `petroleo` | MT5 `WTI.spot` D1 | `precios_energia` |

Un activo sin ficha en `drivers.json` (cobre, Brent, cripto, acciones, fuera de catálogo) recibe
los dos generales, `dxy` y `bono_10`, **sin efecto atribuido**.

Cada hecho:

```json
{"id": "dxy", "driver": "Dollar Index (DXY)", "fecha": "viernes 16/10", "en_curso": false,
 "nivel": "101,560", "cambio_1d": "0,193", "cambio_5d": "0,288", "unidad_cambio": "puntos",
 "sentido": "bajó", "sentido_1d": "bajó", "fuente": "MT5 (USDIDX)",
 "efecto": "juega a favor del alza del oro", "con_la_lectura": "va en contra de nuestra lectura"}
```

- `nivel` y cambios en notación chilena, con los `digits` del símbolo; las tasas en
  "2,78 por ciento" y "14 pb" (la pieza no muestra `%`).
- `sentido` compara contra el cierre de 5 sesiones antes. Bajo el umbral es `estable` y no lleva
  efecto: DXY 0,15 puntos; tasas 3 pb; cobre y petróleo 0,5 por ciento relativo.
- `efecto` = signo de la correlación × sentido. Solo con correlación `directa` o `inversa`; una
  `variable` o `diferencial` deja `efecto: null`.
- `con_la_lectura` compara el efecto con `lectura.direccion` (LATERAL deja `null`). Lo calcula
  Python por la misma razón que la discrepancia con los bancos: agy tiende a alinearse.
- `fed` agrega `proxima_decision` ("miércoles 28/10 15:00 CLT") si la decisión cae en la ventana.
- `fecha` es la de la vela o del dato: un sábado, el DXY es "viernes 16/10" y la curva de FRED
  "jueves 15/10". El texto dice la fecha; nunca llama "hoy" a un dato de ayer (`en_curso` dice si la
  vela es la de hoy, todavía abierta).

Lo que no se puede medir (geopolítica, coberturas de bancos centrales, earnings) no se inventa:
queda en la lista del catálogo y en lo que digan los bancos citados.

## 3. Los días clave de la ventana: `datos.agenda`

Un módulo nuevo, `scripts/analista/agenda.py`, lee la ventana completa de vigencia (`ahora` a
`ahora + 7 d`) con las dos pestañas de Investing.com. `cargar_calendario` gana el parámetro
`pestanas` (por defecto `("thisWeek",)`, así nadie más cambia).

```json
{"desde": "sábado 17/10", "hasta": "sábado 24/10", "estado": "ok",
 "url": "https://es.investing.com/economic-calendar/",
 "eventos": [{"fecha": "2026-10-21", "dia": "miércoles 21/10", "hora": "09:30 CLST",
              "evento": "Índice de precios al consumidor (IPC)", "fuente_nombre": "CPI (MoM) (Sep)",
              "pais": "EE.UU.", "anterior": "0,4 por ciento", "esperado": "0,3 por ciento",
              "explicacion": "...", "efecto": "Si sale sobre lo esperado, el oro tiende a bajar; si sale bajo lo esperado, lo contrario.",
              "mueve_al_activo": true}]}
```

- Solo impacto alto, en hora de Chile tal como la entrega la fuente (issue #38: no se reconvierte).
- `efecto` sale del glosario (`si_sale_sobre_consenso`), como en el seguimiento; sin efecto
  declarado queda vacío y `mueve_al_activo: false`.
- **Tres estados**: `ok`; `vacia` (respondió y no hay datos de alto impacto); `sin_calendario` (no
  respondió o entregó una copia vieja). La copia vieja se detecta porque la caché de respaldo no
  avisa: si el último evento de una pestaña es anterior al domingo que la abre, esa pestaña no
  cuenta. Para eso se pide con `min_impact="low"` y se filtra el alto acá.
- **Imagen**: con eventos, Python rinde `calendario_<slug>.png` con la plantilla `calendario` de
  Stories (`story_render.render_story`, 1920×1080), hasta 6 eventos, primero los que mueven al
  activo. Todo su texto es fijo y de Python. Queda en `imagenes.calendario` (sellada). Si el render
  falla, la pieza sale con la tabla y el ejecutivo recibe el aviso.
- **Ventana vacía** (decisión 2 del director): la ficha y el correo dicen "Sin datos de alto
  impacto entre el sábado 17/10 y el sábado 24/10 en el calendario de EE.UU., Chile, China y la
  Zona Euro". Con `sin_calendario`, la ficha lo dice al ejecutivo con el enlace al calendario y el
  correo omite el bloque: "no pude leer" no es texto de cliente.

`datos.agenda_semana` (lista de strings) se reemplaza por `datos.agenda`. La ficha sigue leyendo
`agenda_semana` en las piezas anteriores, que se reusan hasta 7 días.

## 4. Qué redacta agy

- `contexto.<ticker>`: una frase por driver medido con su estado real, su fecha y su efecto
  (con las palabras de `efecto` y `con_la_lectura`), una línea que jerarquice cuál pesa más hoy
  (memoria `feedback_drivers_analizados_no_enumerados`) y la frase de cierre con la lectura (qué se
  vigila y qué la invalida). Sin `%`.
- `dias_clave.<ticker>` (**nuevo**, anidado, solo si `datos.agenda.eventos` no está vacío): 1 a 3
  frases en modo anticipación con los días clave de la ventana, nombrando cada día como viene en
  `dia` ("miércoles 21/10"), qué se publica y qué hace con el activo (`efecto`). Máximo 420
  caracteres.
- `fuentes`: **2 o 3 bancos** con su postura sobre el activo; al menos uno de
  `cuentan_como_banco` (sección 5). Los organismos de la lista pueden sumarse, no reemplazarlos.
- `titular`, `bajada`, `titulares`: sin cambios.

agy no escribe cifras fuera de `datos` (Regla 1, sin cambios) y no busca en la web nada que no sea
para `fuentes`: los hechos del día ya se los da Python.

## 5. Qué valida Python

Sin cambios: huella, cifras ajenas, HTML, guion largo, voseo, `%`, "oportunidad", invitar a operar.
Nuevo:

1. **`contexto` cita los hechos** (`esquema.errores`). Tiene que contener la cifra (`nivel` o un
   cambio, como viene) de al menos `min(2, len(datos.hechos))` hechos distintos. Con `hechos`
   vacío no exige nada: así las piezas anteriores, que se rearman al reusarlas, siguen pasando.
   Como toda cifra del texto ya tiene que estar en `datos`, agy no puede cumplir inventando.
2. **`dias_clave` nombra un día de la agenda**: contiene el `dia` exacto de al menos un evento.
3. **Al menos una voz de banco.** `config/fuentes_prestigio.json` gana `cuentan_como_banco:
   ["bancos_de_inversion", "chile"]` (lo edita el director). Se aplica en dos lugares, y no en
   `esquema.errores` para no tumbar al reusar las piezas anteriores sin bancos:
   - `bot_analistas.py --validar`, que agy corre hasta que dice `OK`: si `fuentes` no trae ninguna
     entidad que cuente como banco, falla con "fuentes: falta al menos una voz de banco".
   - El bot, después de depurar (fecha, dominio, URL viva): sin banco válido, **un segundo intento**
     solo de fuentes. Python deja `editorial.fuentes` en `[[ESCRIBIR]]` (los demás textos quedan
     escritos, así agy solo busca), escribe `fuentes_intento_1.json` con las válidas y las URLs
     descartadas, y llama a agy con timeout `TIMEOUT_REINTENTO`. El prompt manda reincluir las
     válidas y no repetir las descartadas.
   - Sin banco tampoco en el segundo intento, el pedido falla y **no gasta cupo**:
     > No encontré ninguna voz de banco con su nota vigente (de los últimos 14 días) sobre Oro, ni
     > en un segundo intento, y sin ella el análisis no sale. No gasté tu cupo: vuelve a pedirlo más
     > tarde, cada pedido hace una búsqueda nueva.

     Seguido de hasta 4 motivos de descarte. La carpeta queda en disco para auditar; no entra al
     registro, así que el próximo pedido parte de cero.
   - Una fuente `sin_verificar` (muro de pago, 403) cuenta: su dominio y su ruta de artículo ya se
     validaron, y exigir `ok` dejaría fuera casi todo Reuters, Bloomberg y FT.
4. **Auditoría**: cada llamada a agy deja `agy_salida_<intento>.json` (código, segundos y respuesta)
   en la carpeta del pedido. Hoy no se puede saber si agy buscó.

## 6. Salida

**Ficha del ejecutivo** (sección *Fundamental*): el `contexto`; la tabla *Lo que pasa hoy con
sus drivers* (driver, dato con fecha y fuente, cambio en 5 sesiones, efecto y si acompaña nuestra
lectura, próxima decisión de la Fed); la lista de drivers del catálogo; la curva; y *Días clave del
<desde> al <hasta>* con `dias_clave`, la imagen del calendario, la tabla de eventos y el enlace al
calendario completo. *Voces de bancos y prensa* sigue igual.

**Correo** (lo que llega al cliente), después del `contexto`:

1. *Lo que pasa hoy*: una línea por hecho ("Dollar Index (DXY): 101,560 al viernes 16/10, bajó
   0,288 puntos en 5 sesiones").
2. *Días clave hasta el <hasta>*: `dias_clave`, la imagen del calendario (base64, con ancho y alto
   para Outlook) y el enlace al calendario de Investing.com; o la frase de ventana vacía.
3. *Qué dicen los bancos*: entidad, medio y fecha (dd/mm/aaaa), la tesis y "Ver nota" con el
   enlace; las que discrepan con la marca "ve distinto que nuestra lectura" y la nota de que la
   nuestra manda.

Todo con estilos en línea y colores hex de `marca.css`, como el resto del correo.

## 7. Casos de borde

| Caso | Qué pasa |
|---|---|
| Sin terminal | Igual que hoy: `/oportunidad` no prepara sin la cuenta declarada. |
| MT5 responde pero un símbolo no (`USDIDX`) | El DXY sale de yfinance con la fuente dicha; si tampoco, ese hecho falta y el ejecutivo recibe el aviso. |
| Curva sin dato o con `status` distinto de OK | Esos hechos faltan, con aviso. |
| Ningún hecho medible | `contexto` no exige cifras; el banco sigue siendo obligatorio. Aviso al ejecutivo. |
| Agenda vacía | Ventana completa con sus fechas, sin `dias_clave` ni imagen. |
| Calendario caído o caché vieja | `sin_calendario`: aviso, nota con enlace en la ficha, el correo omite el bloque. |
| Render del calendario falla | Tabla sin imagen, aviso. |
| Sin banco en dos intentos | Falla con el mensaje de la sección 5, sin cupo ni registro. |
| Activo fuera de catálogo | Hechos generales (`dxy`, `bono_10`) sin efecto; agenda sin efectos por activo; banco obligatorio. |
| Pieza anterior reusada (sin `hechos`/`agenda`) | Se rearma igual: la ficha cae a `agenda_semana` y no hay bloques nuevos. |

## 8. Timeout

Se mantiene `TIMEOUT = "25m"` para la redacción: la búsqueda web medida fue de 7 a 11 min y los
hechos no agregan búsquedas (Python los entrega). El segundo intento, que solo busca fuentes, usa
`TIMEOUT_REINTENTO = "15m"`. Peor caso de un pedido: 40 min con la cola detenida, y solo cuando el
primer intento no trajo bancos. La última tarea del plan mide una corrida real y ajusta.

## 9. Fuera de alcance (anotado)

- `pipeline_linkedin.leer_agenda` tiene el mismo defecto de la pestaña única; con `pestanas` el
  arreglo es de una línea, pero LinkedIn tiene sus propios tests y no se toca acá.
- La curva sale del archivo de FRED (rezago de un día hábil, con fecha). `tasas_en_vivo` daría el
  10 años del día; queda para después.
- Las fechas del FOMC fuera de la ventana no se conocen (no hay calendario de la Fed en `config/`).
- El diferencial BCCh contra Fed del USD/CLP (`correlacion: diferencial`) no se mide.
- El texto de WhatsApp (`comercial.texto_whatsapp_base`) no cambia.
