# Historia forense: las mediciones detrás de las reglas

`CLAUDE.md` conserva cada regla **con su razón en una frase**, porque una regla sin su porqué se
revierte: la próxima vez que alguien optimice el despacho va a poner el pie en el editor porque
es más directo, y el canal va a recibir un mensaje al que le faltan renglones sin que nadie lo
note.

Lo que vive acá es la otra mitad: **la medición, la tabla y la fecha.** Se consulta cuando hace
falta el número exacto, cuando alguien quiere volver a discutir una decisión, o cuando conviene
saber si una hipótesis ya se probó y salió falsa.

Cada sección corresponde a una de `CLAUDE.md`, con el mismo nombre.

---

## Un solo reloj: `config/agenda_mercado.json`

### La cripto se mueve en la mañana americana, no en Asia

Medido el 2026-09-04 sobre 90 días de velas H1 en BTC, ETH, SOL y LTC. La cifra es la mediana
del rango por hora contra la mediana diaria, solo días hábiles.

| Bloque (hora NY) | BTC | ETH | SOL | LTC |
|---|---|---|---|---|
| Asia 18–02 | 1,01x | 0,98x | 0,94x | 0,97x |
| Europa 03–08 | 0,98x | 0,96x | 0,90x | 0,98x |
| **NY mañana 08–12** | **1,80x** | **1,65x** | **1,52x** | **1,49x** |
| NY tarde 12–16 | 1,23x | 1,17x | 1,16x | 1,14x |

El máximo está en 09:00–10:00, donde BTC llega a **2,09x** su mediana diaria. La sesión asiática
está plana y Europa también: **la hipótesis del rollover asiático era falsa.** El momento va a
las 09:00 y no a las 10:00 solo para no chocar con el de los índices, porque cada momento
produce su propia tanda.

**El fin de semana la cripto está más quieta, no más activa**: 0,76x a 0,85x del día hábil. La
sesión `fin_de_semana` existía en parte pensando en lo contrario, y el dato no respalda esa idea.

### El offset del servidor de MT5, medido

La primera corrida de esa medición dio el máximo en las 06:00 de Nueva York, que habría apuntado
a la apertura de Londres y a una conclusión distinta. El servidor del broker corre en **UTC−4**,
así que el máximo real estaba cuatro horas después. Es el mismo error de interpretar la marca de
tiempo de MT5 como UTC cuando viene en hora del servidor.

## El reloj de sucesos: el desfase con Chile, año por año

| Fecha | Desfase | premercado_fx | cripto | índices |
|---|---|---|---|---|
| hasta el 5 sep 2026 | NY+0 | 08:30 CL | 09:00 CL | 10:00 CL |
| 6 sep 2026 | NY+1 | 09:30 CL | 10:00 CL | 11:00 CL |
| 1 nov 2026 | NY+2 | 10:30 CL | 11:00 CL | 12:00 CL |
| mar 2027 | NY+1 | 09:30 CL | 10:00 CL | 11:00 CL |
| abr 2027 | NY+0 | 08:30 CL | 09:00 CL | 10:00 CL |

Anclar a hora chilena fija se descartó midiendo esta tabla: con el desfase en NY+2, la pieza de
índices habría salido a las 08:00 de Nueva York, hora y media antes de la campana, publicando el
cierre de ayer con fecha de hoy.

## El `Score_GI`: las cifras que fijaron el gate de banda

El 2026-09-04 hubo que aplicar a mano el criterio de banda contra vela típica cuatro veces:

| Activo | Banda cubierta por la vela típica |
|---|---|
| Litecoin | **3,2 veces** |
| Dogecoin | 1,8 veces |
| S&P 500 | 1,03 veces (banda de 16,54 puntos contra una vela típica de 17,00) |

De ahí salieron los umbrales de excluir desde 1,00x y avisar desde 0,70x.

### Y las que mostraron que `--grupo` apagaba un gate en silencio

Hasta el 2026-09-03, `--grupo` también desactivaba el gate de agotamiento sin decirlo. Por eso el
canal de forex salió con tres piezas cuyo recorrido diario estaba consumido al **93 %, 290 % y
115 %**, con el escáner reportando cero exclusiones porque no las hubo.

## Un canal vacío: las cifras del día que lo motivó

El 2026-09-03 el canal de divisas quedó en cero porque sus cuatro activos habían consumido su
recorrido del día, con el USD/JPY al **290 %**. A las 10:24 había 4 activos de forex entre 93 % y
290 %; a las 12:11 había **15 excluidos en todo el universo**. Es la demostración de que
`ATR − rango_hoy` solo baja: el sistema tiene su mejor momento al abrir y se apaga solo.

## La noticia oficial: el descarte que la justifica

El 2026-09-03 la nota más fresca de la EIA era *"Weekly average load in ERCOT continues near
record high"*: carga eléctrica en Texas. Oficial, del día, y sin ninguna relación con el petróleo.
Un filtro de frescura sin filtro de relevancia la habría mandado al canal de metales y energía
justo el día en que ese canal quedó vacío.

**Cadencias medidas** el 2026-09-03: EIA ~3 por semana, de las cuales 3 de 12 tocan crudo; BCE ~4
por semana contando discursos del directorio; Fed ~2 por mes.

**Tres fuentes no se pueden leer:** el Tesoro de EE.UU. responde 404, la BLS y la OPEP responden
403 al bot, y el Banco Central de Chile devuelve HTML en la ruta de su RSS.

## El despacho: el pie de foto, medido contra el DOM real

El 2026-09-03, con un texto de 2.016 caracteres:

| Orden | Pie resultante |
|---|---|
| adjuntar primero, pie en el editor | **1.029** de 2.016 |
| texto en el cuadro, adjuntar después | **2.042** de 2.016 (completo) |

Ese día el canal recibió el contexto macro **sin la línea del Imacec ni las dos de tasas**, pero
con el link del BCCh que iba en medio, y con las líneas cortas posteriores intactas porque todavía
cabían. El despacho reportó éxito.

El 2026-09-04, `limpiar_payloads` hacía `rglob` sobre la tanda entera y una segunda corrida en el
mismo minuto se llevó los payloads de la primera: doce de commodities, con el escáner reportando
"barridos 12 payload(s)" sin que eso se leyera como un problema.

## El refresco del despacho: el freno que nunca pudo dispararse

El 2026-09-07 se despachó una tanda de 10 piezas a 6 canales con el comando documentado,
`uv run --extra stories python scripts/pipeline_carrusel.py --despachar`. Las cuatro piezas de
activo avisaron lo mismo:

```
EURUSD: no se pudo refrescar (No module named 'MetaTrader5').
        Sale con los datos de la preparación, que ya no son de ahora.
```

El extra `stories` declara `playwright` y nada más, y MetaTrader5 no está en las dependencias
base. O sea que el refresco previo al envío **no podía ocurrir nunca** por el camino canónico, y
con él quedaba inerte el guardia que detiene la pieza cuyo precio invalidó el texto: la pieza
`.divergente` que describe el diseño era inalcanzable desde la documentación.

Nada de esto se vio desde afuera. El despacho terminó con código 0, la bitácora anotó las diez
piezas y el resumen las reportó entregadas.

Las piezas salieron con precios de 11 a 14 minutos antes. Medido contra el terminal al cierre de
la tanda, ninguna había quedado inválida:

| Activo | Publicado | Al cierre | Diferencia | Estado |
|---|---|---|---|---|
| EURUSD | 1,16257 | 1,16275 | +0,00018 | dentro de la banda |
| GBPUSD | 1,35351 | 1,35342 | −0,00009 | dentro de la banda |
| WTI.spot | 92,597 | 92,848 | +0,251 | dentro de la banda |
| XAGUSD | 65,965 | 65,981 | +0,016 | dentro de la banda |

**El resultado fue correcto y el freno no tuvo nada que ver.** Fue un lunes de Labor Day, con
índices y acciones cerrados y el mercado quieto. Con un dato de empleo en el medio, esos mismos
14 minutos son otra cosa, y el despacho habría publicado niveles ya cruzados informando éxito.

Es el mismo modo de falla del extra `informe` del 2026-09-06: funciona donde el paquete ya está
y se rompe en otro lado. La diferencia es que aquel gritaba con un `ModuleNotFoundError` y este
degradaba en silencio, que es peor.

## Un PDF adjunto: las mediciones

Medido el 2026-09-04: se envió un pie de **1.222 caracteres** con un PDF de **2 MB** y llegó
entero. El editor mostraba un contador en **−197** y el envío funcionó igual.

## El sesgo: los casos que fijaron las reglas

Brent el 2026-09-02 llevaba sesgo **+1,50** con el precio ya bajo su Chandelier, y el USD/CLP
estaba en la misma situación el 2026-09-03. Publicar "sigue vigente" en cualquiera de los dos
habría dicho lo contrario de lo que pasaba.
