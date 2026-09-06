# Cobertura de eventos macro

**Diseño técnico · 2026-09-05 · Grupo de Análisis de Mercado**

Segunda parte de [`hooks-automatizacion`](../hooks-automatizacion/2026-09-05-hooks-automatizacion-design.md),
del que depende: los guardrails y el gate de despacho son el piso de todo lo que sigue.

---

## 1. El objetivo

**Decisión del director, 2026-09-05: el sistema debuta haciendo la cobertura total de la TPM.**

"Cobertura total" no es una pieza, es una secuencia a lo largo de varios días. Para la Reunión
de Política Monetaria del Banco Central de Chile del **martes 8 de septiembre de 2026 a las
18:00 hora de Chile**, y su Informe de Política Monetaria del día siguiente:

| Hito | Cuándo | Qué dice |
|---|---|---|
| Anticipación | T−3d | Qué es la TPM, qué se espera, qué significa cada escenario |
| Víspera | T−1d | Recordatorio con hora, consenso y qué mirar |
| Antesala | T0, 16:00 | Falta poco, esto es lo que está en juego |
| **Resultado** | **T0, 18:45** | **La decisión, el veredicto frente al consenso y la reacción del peso** |
| IPoM | T+1d, 09:15 | Las proyecciones, que es donde suele estar el movimiento |

El hito de resultado a las 18:45 no es arbitrario: `screener_gi._BLACKOUTS` aplica a la RPM
una ventana de −15/+45 minutos, así que **el blackout corre de 17:45 a 18:45** y esa pieza no
puede salir antes.

## 2. El hallazgo que cambia el plan: ya hay tres calendarios

Antes de diseñar nada, la exploración del repo encontró esto:

| Calendario | Qué es | Quién lo consume | Alcance |
|---|---|---|---|
| `config/agenda_mercado.json` | Momentos fijos del día, anclados a Nueva York | `reloj_gi.py`, el escáner | 3 momentos diarios |
| `data central/DATA AGENDA/calendario_2026.json` | **Eventos con fecha, hora y zona propia** | solo `.agents/skills/ecosistema-datos-macro/` | 11 eventos curados, hasta noviembre |
| `obtener_calendario_macro` (Investing) | Scrape de la **semana en curso** | blackouts del escáner, piezas macro | `_fetch_calendario("thisWeek")` |

Y tres cosas más que no eran obvias:

1. **La RPM ya está en el repo.** `calendario_2026.json` trae `rpm_2026_09` el 2026-09-08 a las
   18:00 en `America/Santiago`, y `ipom_2026_09` al día siguiente a las 08:30. La verificación
   independiente contra el BCCh el 2026-09-05 dio exactamente esa hora: **el dato del repo era
   correcto y nadie lo estaba usando.**
2. **`reloj_gi.py` no sabe que ese calendario existe.** Importa `agenda_mercado` y nada más.
3. **`reporte_asociado` es un campo inerte.** `rpm_2026_09` declara `flash_tpm` e `ipom_2026_09`
   declara `informe_ipom`, y el único consumidor en todo el repo es `agenda.py:116`, que lo
   **imprime en consola**. Es la semilla del disparador por evento, sembrada y nunca conectada.

**Tres calendarios sin nada que los cruce es el defecto recurrente del repo en su escala más
grande.** Y ya hay un contrato roto para probarlo: `ipom_2026_09` declara
`series_afectadas: ["PROYECCIONES_PIB", "PROYECCIONES_IPC"]`, y las series que de verdad
existen en `bcch_macro_data.json` son `TPM`, `IMACEC_TOTAL`, `DOLAR_OBSERVADO`,
`POSICION_FORWARD_EXTRANJEROS` e `IMACEC_12M_VAR`. Las dos declaradas **no existen**. Una pieza
que intentara citarlas no encontraría nada, y hoy nada avisa.

## 3. Qué calendario manda, y para qué

No se unifican en uno. Se les asigna **un rol excluyente a cada uno**, y un test impide que se
pisen:

| Rol | Fuente | Por qué esa |
|---|---|---|
| **Disparar** una campaña | `calendario_2026.json` | Mira meses adelante, tiene la zona por evento, está curado a mano con `fuente_oficial`, y para 8 decisiones al año eso es más confiable que un scrape |
| **Resolver el resultado** (`actual` vs consenso) | `obtener_calendario_macro` | Es el único que trae el valor publicado y su clasificación mejor/peor/en línea |
| **Los momentos diarios** | `config/agenda_mercado.json` | No cambia: sigue siendo el reloj de la cadencia diaria |

La regla que lo ordena:

> El calendario de eventos dice **cuándo** hay que publicar. Investing dice **qué salió**. La
> agenda de momentos no opina sobre eventos, y el calendario de eventos no opina sobre la
> cadencia diaria.

**El calendario de eventos no puede quedarse sin mantención.** Hoy son 11 eventos con
`ultima_verificacion` del 2026-08-24 y varios ya pasados. Una campaña que se dispara de un
calendario vencido no se dispara y nadie se entera, así que el brief operativo (H3 de la spec
anterior) pasa a informar **cuántos días de cobertura futura quedan** y avisa bajo un umbral.

## 4. El disparador por evento

### 4.1 Los hitos son una plantilla de campaña, no fechas sueltas

`config/campanas_evento.json` declara, por `reporte_asociado`, qué hitos tiene esa clase de
evento y a qué distancia del instante:

```jsonc
{
  "flash_tpm": {
    "canales": ["02_forex_divisas", "01_macro_y_apertura"],
    "hitos": [
      { "slug": "anticipacion", "offset": "-3d", "en_momento": "premercado_fx", "modo": "diferido" },
      { "slug": "vispera",      "offset": "-1d", "en_momento": "premercado_fx", "modo": "diferido" },
      { "slug": "antesala",     "offset": "-2h",                                "modo": "diferido" },
      { "slug": "resultado",    "offset": "+45m",                               "modo": "asistido" },
      { "slug": "ipom",         "ancla_en_reporte": "informe_ipom", "offset": "+45m", "modo": "asistido" }
    ]
  }
}
```

**Los tres modos, para no confundirlos.** La spec anterior definió dos y ésta agrega el tercero:

| Modo | Quién escribe el texto |
|---|---|
| `generado` | El código, con plantillas por dirección del dato |
| `diferido` | Una persona, antes, y el sistema despacha en el minuto exacto |
| **`asistido`** | **Un modelo, en el momento, sin sesión abierta** |

**El hito del IPoM se ancla a otro evento a propósito.** El IPoM es un evento propio del
calendario con su propio `reporte_asociado`, pero editorialmente es el cierre de la cobertura
de la TPM, no una campaña aparte: `ancla_en_reporte` dice que ese hito se cuelga del instante
de aquel evento en vez del de la RPM. Modelarlo como campaña separada partiría en dos algo que
el cliente lee como una sola historia.

Tres decisiones:

- **El offset se resuelve en la zona del evento**, que el calendario ya declara por evento
  (`America/Santiago` para la RPM). Sin eso volvemos al error de ±1 h del issue #38.
- **Un hito con `en_momento` se ancla al momento diario más cercano** en vez de a una hora
  suelta, para que la pieza de anticipación viaje con la tanda de su canal y no llegue sola a
  una hora rara.
- **`+45m` en el hito de resultado no es un número mágico**: es el `despues_min` que
  `_BLACKOUTS` ya declara para la RPM. Se **lee de ahí**, no se copia. Si alguien cambia el
  blackout, el hito se mueve con él.

### 4.2 `reporte_asociado` deja de ser inerte

El campo pasa de imprimirse a ser **la clave que une el evento con su campaña**. Y como es un
contrato por nombre entre dos archivos, lleva su test: **todo `reporte_asociado` del calendario
tiene entrada en `campanas_evento.json`, y toda entrada corresponde a algún evento**. Ese test
es también el que habría detectado el `series_afectadas` roto del IPoM, así que se extiende a
verificar que las series declaradas existan en `data central/`.

### 4.3 Idempotencia

`reloj_gi` ya tiene `data/.reloj_disparos.json`, con clave por momento y día. Se extiende con
clave por **`(evento_id, hito_slug)`**, por ejemplo `rpm_2026_09:resultado`. No lleva la fecha:
un evento ocurre una vez, y su hito se publica una vez.

Se conserva la regla que ya existe y es la correcta: **un hito que falló sigue pendiente**. Solo
se anota cuando la pieza salió.

## 5. La cadena de datos en su propio reloj

**El script ya existe y la tarea no.** `scripts/ejecutar_agenda_macro.ps1` está escrito como
orquestador para el Programador de tareas (corre `agenda.py` y después `pipeline_ingesta.py`),
y `Get-ScheduledTask` el 2026-09-05 devuelve **una sola tarea del proyecto: `GI-CalculadoraLotaje`**.
Ni la ingesta ni el reloj están registrados.

Eso hoy no se nota porque la ingesta se refresca en `SessionStart` (H2). Pero **a las 18:45 de
un martes puede no haber ninguna sesión abierta**, y la pieza saldría con el estado de la
mañana.

Lo que entra:

1. **Registrar la ingesta como tarea**, reusando el script que ya existe, con el mismo lock y
   el mismo umbral de 6 h que usa el hook. Una sola regla de vencimiento, en `esta_vencida`.
2. **Una ingesta previa a cada hito**, disparada por el propio reloj: antes de una pieza de
   campaña, los datos se refrescan sí o sí. Es más barato que descubrir a las 18:45 que están
   viejos.
3. **El fallback a yfinance pasa a ser bloqueante para lo autónomo.** `pipeline_datos --estado`
   ya lo detecta y hoy solo lo reporta. El 2026-09-02 cinco de seis activos salieron de futuros
   mientras la cadena decía `[OK] precios`; con nadie mirando a las 18:45, eso publicaría el
   precio de un instrumento distinto. Pasa a ser un motivo de denegación del gate.

## 6. El tercer modo: el modelo escribe sin sesión

### 6.1 Por qué hace falta

La pieza de resultado **no se puede pre-escribir** —nadie sabe el número hasta las 18:00— **ni
generar con plantillas**, porque el veredicto y la implicancia son juicio y no una variante
`titular_sube`. La spec anterior dejó este modo fuera a propósito; con el objetivo del director
pasa de lujo posterior a cimiento.

### 6.2 El diseño, y por qué es más pequeño de lo que parece

El payload de `dato_macro` ya separa lo derivable de lo editorial. De sus catorce campos:

| Salen del dato | Los escribe quien redacta |
|---|---|
| `chip_pais`, `fecha_hora`, `indicador`, `periodo` | **`titular`** |
| `actual`, `esperado`, `anterior` | **`significado`** |
| `veredicto`, `veredicto_slug` | **`activos[].porque`** y su `direccion` |
| `recorrido`, `sello_datos` | |

**Son tres campos.** Todo lo demás lo llena el pipeline con datos del calendario y del terminal.

De ahí sale la forma del modo asistido:

> El modelo es **un escritor más de campos editoriales**. Recibe el payload con lo derivable ya
> lleno, devuelve esos tres campos, y **todo aguas abajo no cambia**: `exigir_texto_editorial`,
> los guardrails de texto de cliente, la revisión editorial, el gate y el sender son
> exactamente los mismos que usa una sesión.

Eso es lo que hace este modo implementable sin rehacer nada. No se le da al modelo acceso al
sender, ni al gate, ni a la decisión de publicar. Escribe tres campos en un JSON.

### 6.3 El runner es intercambiable, el contrato no

El runner se declara en config (`claude -p` o `agy -p`, ambos corren headless en Windows). Lo
que se fija es el contrato: entra un payload, sale un JSON con tres claves. Un runner que
devuelva otra cosa se trata como fallo.

Dos cosas medidas que conviene no volver a averiguar, ya documentadas para `agy`: hay que
invocarlo desde Bash porque PowerShell parte el argumento de `-p`, `--print` no lee de stdin, y
el `--print-timeout` por defecto de 5 minutos mata el trabajo antes de tiempo.

### 6.4 Las tres consecuencias de seguridad

1. **Falla hacia cerrado.** Si el runner no responde, devuelve basura, o su texto no pasa los
   guardrails, **la pieza no sale**. Nunca se publica un texto que no pasó.
2. **La revisión editorial deja de ser opcional.** En la spec anterior, H13 nace apagado y se
   mide si paga. Acá **es obligatoria y siempre encendida**: cuando nadie lee el texto antes que
   el cliente, esa revisión es lo único que lo lee. Ese cambio de estatus se refleja en la spec
   anterior.
3. **Un hito bloqueado se avisa, no se omite.** Es el punto más importante de este documento.

### 6.5 La cobertura incompleta en silencio es el modo de falla de este sistema

Todo el diseño anterior existe porque en este repo las cosas fallan pareciendo correctas. Una
campaña tiene la misma trampa en su propia forma: **si el hito de resultado no sale, el cliente
ve la anticipación y la víspera, y después nada.** Queda esperando un dato que prometimos, y
desde afuera no hay diferencia entre "no pasó nada" y "el sistema se cayó".

Por eso el objeto de campaña (§7) no es contabilidad interna: es lo que permite que el sistema
**sepa que le falta algo y lo diga a tiempo**, con margen para que una persona escriba la pieza
a mano.

## 7. La campaña como objeto

`data/campanas/<evento_id>.json`, versionado igual que los otros historiales editoriales:

```jsonc
{
  "evento_id": "rpm_2026_09",
  "reporte": "flash_tpm",
  "instante": "2026-09-08T18:00:00-04:00",
  "hitos": {
    "anticipacion": { "estado": "entregado", "cuando": "...", "piezas": ["..."] },
    "vispera":      { "estado": "entregado", "cuando": "..." },
    "antesala":     { "estado": "pendiente" },
    "resultado":    { "estado": "bloqueado", "motivo": "precio_no_es_del_broker" },
    "ipom":         { "estado": "pendiente" }
  }
}
```

Tres reglas:

1. **Un hito bloqueado o vencido levanta un aviso al director**, con el tiempo que queda para
   escribirlo a mano. El aviso viaja por el brief de sesión (H3) y por la salida del reloj.
2. **Una campaña con hitos entregados y uno vencido queda marcada como incompleta**, y eso se
   ve en `/estado`. Media cobertura publicada es peor que ninguna.
3. **El estado no lo escribe el modelo.** Lo escribe el despacho, contra la entrega confirmada,
   igual que `historial_despachos.json`.

## 8. Manejo de errores

Hereda la asimetría de la spec anterior y agrega una capa:

| Falla | Qué pasa |
|---|---|
| El calendario de eventos está vencido | No se dispara nada. **Aviso fuerte**: es el fallo que se nota menos |
| La ingesta previa al hito falla | El hito no sale, queda pendiente, se reintenta al siguiente latido |
| Los precios no vienen del broker | El hito se **bloquea** y se avisa. No se publica un precio de otro instrumento |
| El runner no responde o devuelve basura | El hito se bloquea y se avisa |
| El texto no pasa los guardrails | El hito se bloquea, con el motivo del veredicto |
| El gate deniega | Lo que ya define la spec anterior |

**Ninguna de esas rutas publica algo a medias.** Todas terminan en "no sale y alguien se
entera", que es la única forma correcta de fallar cuando nadie está mirando.

## 9. Qué cambia en la spec anterior

Tres enmiendas, que se aplican al cerrar ésta:

1. **Las fases 3b y 3c quedan después de este trabajo.** El despacho autónomo generado y el
   diferido son optimizaciones de la cadencia diaria; la cobertura de eventos es el objetivo.
2. **H13 pasa de opcional a obligatorio** en cuanto exista el modo asistido (§6.4).
3. **La ventana de Santiago se mueve de 17:30 a 19:30**, y solo entonces. Hoy 17:30 es correcto
   porque cerrar más tarde autorizaría un horario en el que el sistema no tiene ni disparador ni
   texto. El test `test_la_ventana_de_santiago_cierra_antes_del_blackout_de_la_rpm` se
   reemplaza por su inverso: **la ventana tiene que cubrir el hito de resultado**, calculado del
   mismo `despues_min` del blackout.

## 10. Fases

| Fase | Qué entra | Depende de |
|---|---|---|
| **A** | Rol de cada calendario + tests de contrato (`reporte_asociado`, `series_afectadas`) + aviso de calendario vencido | — |
| **B** | Registrar la ingesta como tarea + ingesta previa al hito + yfinance como motivo de denegación | spec anterior, fase 3a |
| **C** | Disparador por evento en `reloj_gi` + `campanas_evento.json` + idempotencia por hito | A |
| **D** | Objeto de campaña + avisos de hito bloqueado o vencido | C |
| **E** | Modo asistido: runner, contrato de tres campos, H13 obligatorio | B, D |
| **F** | La campaña de la TPM extremo a extremo, en el banco de pruebas | todas |

**A y B se pueden hacer en paralelo** y ninguna toca el envío. C y D construyen la cobertura
sin que ningún modelo escriba nada: con esas cuatro, la campaña ya funciona en modo **diferido**
—una persona escribe los tres campos y el sistema publica en el minuto exacto—. **E es el único
paso donde algo sale sin que nadie lo haya leído**, y va último a propósito.

## 11. Lo que no alcanza para el 8 de septiembre

**La RPM del martes 8 llega en tres días y las fases A a E no se construyen en tres días.** Esa
cobertura se hace a mano, con el sistema actual, y sirve de referencia: es la primera vez que
se produce la secuencia completa y conviene tenerla escrita antes de pedirle a un sistema que
la repita.

El caso de prueba real es **la RPM siguiente**, con la campaña corriendo en el banco de pruebas
y el director comparando lo que el sistema habría publicado contra lo que publicó una persona.

## 12. Riesgos aceptados

1. **Un modelo escribiendo texto que llega al cliente sin lectura humana previa.** Se acota con
   el fallo hacia cerrado, la revisión editorial obligatoria, los tres campos como única
   superficie de escritura y el arranque en el banco de pruebas. No se elimina.
2. **La campaña crea una expectativa.** Anunciar la anticipación compromete el resultado. Por
   eso el aviso de hito bloqueado es parte del diseño y no un extra: es lo que permite cumplir
   a mano lo que el sistema no pudo.
3. **El calendario curado a mano es un punto único de falla silenciosa.** Once eventos y una
   verificación del 2026-08-24. Se mitiga con el aviso de cobertura futura, no con automatizar
   su llenado: para 8 decisiones al año, una persona verificando contra la fuente oficial es
   más confiable que un scrape.
