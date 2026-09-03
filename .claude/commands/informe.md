Genera el informe de la jornada: PDF institucional en la apertura, mensaje con gráfico
al cierre.

Uso: `/informe apertura` · `/informe cierre`

## Por qué un PDF al día y no dos

El plan de producción pedía informe en apertura y en cierre, los dos en PDF. La skill
`generar-reporte-editorial` reserva el PDF **"estrictamente"** para hitos de alta densidad
y manda formato chat-first para piezas tácticas, por fatiga de descargas en el grupo.
Decisión del director: la apertura sí va en PDF, porque es densa y se lee antes de operar;
el cierre pasa a mensaje con gráfico adjunto.

## PASO 1 — Armar los datos

```bash
uv run python scripts/pipeline_informe.py --tipo apertura --preparar
uv run python scripts/pipeline_informe.py --tipo cierre --preparar
```

Deja en `data/informes/<fecha>_<tipo>/informe_<tipo>.md` las tablas ya resueltas: curva
soberana de EE.UU. con su variación en puntos base y la fecha de cada dato, agenda macro del
día en hora de Chile con los indicadores nombrados en español, y régimen macro más sesgo por
activo del Motor GI.

La agenda trae seis columnas: **Estado**, hora, país, indicador, impacto y **Cifras**. Tres
cosas que conviene saber antes de editarla a mano:

- **El estado lo decide la cifra publicada, no el reloj.** `Publicado` es que la fuente ya
  entregó el valor; `Pendiente`, que falta; `Sin cifra`, que pasó la hora y el evento no
  entrega número (subastas, intervenciones, feriados). El informe de apertura se emite justo
  a las 08:30 de Nueva York, que es la hora en que EE.UU. publica: la mitad de la tabla
  cambia de estado en esos minutos.
- **La columna Cifras nunca lleva tres números.** Antes de publicarse informa el consenso;
  después, el valor real sobre el consenso; y solo cuando no hay consenso publicado cae al
  anterior. Con una columna más por número, el nombre del indicador se va a cuatro líneas y
  la tabla no cabe en la página.
- **`(general)`, `(Cushing)` o `(manufacturero)` al final de un indicador no es un error.**
  El glosario engancha por sigla, así que "Core PCE" y "PCE" caen en la misma entrada y sin
  esa marca la tabla mostraría dos filas idénticas con cifras distintas. La tabla garantiza
  que ninguna fila se lea igual que otra, y cita solo la palabra que las diferencia.

**Si la apertura se niega a generarse, no la fuerces sin leer por qué.** El informe de
apertura depende de `macro_bias_output.json`; si está vencido, el script se detiene y nombra
el remedio: correr `pipeline_ingesta.py` y después `macro_bias_engine.py`. Refrescar el dato
es siempre la primera opción.

`--con-datos-viejos` existe para cuando el director decide publicar igual. En ese caso el
informe **estampa el aviso en la primera página** diciendo que va sin el sesgo del motor y
que ninguna cifra debe leerse como lectura suya. La decisión de publicar con datos vencidos
es del director; que el lector lo sepa, no.

### Los gráficos salen solos

`--preparar` dibuja un gráfico por activo del Playbook y lo referencia bajo su bloque en
la sección 02. Sale del terminal, no de un archivo aparte: la serie de cierres la trae
`scripts/serie_mt5.py` y los niveles `analizar_activo`, así que si MT5 está cerrado el
informe se emite **sin imágenes** y lo dice en los avisos, en vez de caerse o dibujar algo
plausible.

Requiere `matplotlib`, que es dependencia opcional:

```bash
uv sync --extra informe        # una vez
```

Dos cosas que conviene saber antes de que llamen la atención:

- **Brent no lleva gráfico.** El broker no ofrece el símbolo, así que no hay serie que
  pedir. Como comparte lectura con el WTI, el bloque agrupado se queda con el del WTI y el
  aviso lo dice con esas palabras.
- **El subtítulo del gráfico es el sesgo del activo**, tomado de la misma frase que ya está
  en el texto. Si cambia la traducción de un matiz, cambian los dos a la vez: imagen y
  párrafo no pueden decir cosas distintas del mismo activo en la misma página.

## PASO 2 — Escribir el análisis

El markdown trae 4 secciones marcadas con `[[ESCRIBIR]]`. Las tablas son datos; el análisis
es tuyo:

1. **Marco de la jornada**: dos párrafos. Qué deja la sesión anterior y con qué abre esta.
2. **Régimen y sesgo**: qué significa el régimen vigente para operar hoy. Los `setups_prohibidos`
   de la tabla son prohibiciones, no sugerencias: nómbralas como tales. El bloque **"Hasta
   dónde vale esta lectura"** de cada activo ya viene escrito y sale del Playbook: no lo
   repitas ni lo contradigas, y si alguno dice *"la lectura ya no vale"*, ese activo no puede
   aparecer en tu análisis como si su dirección siguiera en pie.
3. **Curva soberana**: qué dice el movimiento de tasas sobre el dólar, el oro y el Nasdaq.
   El umbral del Playbook es explícito: sobre 4,70% en la de 10 años se comprimen los
   múltiplos del US100.
4. **Agenda del día**: cuál de esos eventos puede mover la jornada y por qué.

Reglas que aplican íntegras: cero guiones largos, siglas explicadas una sola vez, y **cada
cifra con su fecha** cuando el dato tiene rezago. La sección "05. Fuentes consultadas" ya
viene armada y hay que dejarla: un número sin decir de dónde salió no es auditable.

Si un indicador de la agenda aparece con su nombre en inglés, es porque no está en
`data/glosario_siglas.json`. Agrégalo ahí con su `nombre_es` y su explicación en voz novata,
y vuelve a correr `--preparar`.

El pie de la agenda cierra con el link al calendario económico completo. La tabla trae solo
los eventos de impacto medio y alto de cuatro países: no es el calendario del día, y el
lector tiene que poder llegar al resto.

## PASO 3 — Compilar

```bash
uv run --extra stories --extra informe --with markdown --with pypdf \
  python scripts/pipeline_informe.py --tipo apertura --rendir data/informes/<dir>
```

Produce el PDF A4 con la maqueta institucional. Si queda una sola marca `[[ESCRIBIR]]`, se
detiene.

Para el cierre, `--rendir` no genera archivo: devuelve el markdown como guion del mensaje,
que es lo que corresponde al canal.

## PASO 4 — El mensaje que acompaña

El PDF nunca va solo. Un mensaje corto con las 6 reglas de formato:

```text
📄 *Marco de apertura* · [fecha]
━━━━━━━━━━━━━━━━━━━
🎯 [Lo esencial de la jornada en una línea]
📌 [El nivel o dato a vigilar hoy]
⚡ [Qué esperar]
━━━━━━━━━━━━━━━━━━━
⏱️ Temporalidad: swing de jornada (1 a 3 días)
El informe completo va adjunto, con la curva de tasas, la agenda del día y el sesgo por
activo.
```

**El pie repite lo esencial a propósito**: es lo único que el cliente ve en la notificación
si no descarga el PDF. Un adjunto sin pie llega mudo.

## PASO 5 — Aprobación

Muestra el mensaje y la ruta del PDF. Pregunta: "¿Apruebas? ¿Enviar al grupo?". Guarda el
mensaje con:

```powershell
scripts\ruta_mensaje.ps1 -Fecha "<fecha>" -Tipo "cierre" -Hora "<HH-mm>"
```

Usa tipo `cierre` para el informe de cierre. Para la apertura, el tipo es `niveles` si el
foco fue técnico o `dato_macro` si lo fue el calendario; en ambos casos sin `-Activo`,
porque el informe cubre varios y cae en `_general/`.

**Nunca se envía nada al grupo sin aprobación explícita del director.**
