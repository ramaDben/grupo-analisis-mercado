Prepara, escribe y despacha los carruseles del grupo de Avisos (`01_macro_y_apertura`): la agenda
del día, el resultado de cada dato fuerte, la cita de un banco y el balance de la tarde.

Uso: `/avisos` (retoma lo que el reloj dejó preparado hoy) · `/avisos <momento>` para preparar uno
fuera de hora: `avisos_agenda`, `avisos_resultado`, `avisos_manana`, `avisos_tarde`.

Argumentos: $ARGUMENTS

Spec: `docs/superpowers/specs/2026-09-28-carruseles-avisos-design.md`, **sección 13** (manda sobre
las anteriores donde se contradicen).

## El día de Avisos

| Momento | Hora | Formato | Láminas |
|---|---|---|---|
| `avisos_agenda` | 07:45 Santiago | `agenda_dia` si hay datos de alto impacto hasta las 18:30 Chile; si no, `agenda` (la semana) | portada · la agenda · nuestra lectura |
| `avisos_resultado` | cada latido, cuando el dato ya trae cifra | `resultado`: una pieza por hora de datos | la tabla con resultado y veredicto |
| `avisos_manana` | 10:30 Nueva York | `cita`, **solo los días sin datos fuertes** | portada · la voz del banco · nuestros datos · lectura |
| `avisos_tarde` | 14:30 Nueva York | `balance`; el lunes, la semana si no salió en la mañana | ídem |

**Nada de VIX ni de tasas en Avisos.** El carrusel temático ya no escribe en este canal; si
encuentras un `contexto_macro` en una carpeta de Avisos, es de una versión vieja y no se despacha.

## PASO 1 — Localizar o preparar la tanda

Las tandas viven en `data/carrusel/<fecha>_<hora>_avisos_<momento>/01_macro_y_apertura/`, con su
`_avisos.json`. Si el director pide un momento fuera de hora:

```bash
uv run --with MetaTrader5 python scripts/pipeline_avisos.py --preparar --momento <momento>
```

Códigos: **0** tanda lista, o "Sin tanda: ..." (resultado válido: hoy no corresponde); **1** falla de
datos (MT5 caído, o el dato todavía no trae cifra): se reintenta, no se inventa.

**La hora sale del reloj de Chile (PowerShell), nunca de `TZ=` en Git Bash**: Git Bash no reconoce
`America/Santiago` y devuelve UTC en silencio.

## PASO 2 — Escribir lo editorial

Todo campo en `[[ESCRIBIR]]` es tuyo; lo demás lo armó el script con cifras medidas y no se toca.
Escribe con Python o con la herramienta de edición, **nunca por PowerShell** (regla de escritura).

| Formato | Qué escribes |
|---|---|
| `agenda_dia` | Portada: `kicker`, `titular` (el dato que manda hoy), `parrafo`, `claves[*].texto`, `pie`. La agenda: `titular` (título) y `parrafo` (subtítulo). La lectura: `titular` y `parrafo` (conclusión). **Los `puntos` ya vienen escritos desde el glosario**; revísalos. |
| `resultado` | Solo `parrafo`: el "qué significa", en voz novata y **coherente con el movimiento medido** que ya trae la pieza. Sin cifras propias. El titular sale del veredicto y no se toca. |
| `agenda`, `cita`, `balance` | Como en la spec 3.4. Si la tanda tiene `_falta_vision`, busca una visión y corre `--completar-vision`. |

**Un punto de la lectura en `[[ESCRIBIR]]` significa que ese dato no declara su reacción** en
`data/glosario_siglas.json`. Lo correcto es clasificarlo ahí (`si_sale_sobre_consenso`, con `pais`,
`tier`, `fuente` y su test en `tests/test_clasificacion_macro.py`), no escribir la reacción a mano.

Reglas de texto de cliente íntegras: tuteo chileno, sin guion largo ni medio, siglas explicadas,
flechas ⬆️ ↔️ ⬇️ para escenarios.

## PASO 3 — Rendir y mirar

```bash
uv run --extra stories python scripts/pipeline_avisos.py --rendir <dir>
```

Se detiene ante un texto sin escribir, una cifra sin respaldo, una cita vieja o datos de más de
2 horas (`--refrescar <dir>`). Mira cada PNG: tildes, `¿`, `·` y emoji tienen que verse.

## PASO 4 — Banco de pruebas primero

```bash
uv run --extra stories --with MetaTrader5 python scripts/pipeline_carrusel.py --despachar data/carrusel/<tanda> --pruebas
```

El despacho vuelve a leer el mercado, rinde cada lámina con su plantilla y **no manda ninguna** si
el texto quedó escrito para otro mercado o si el cupo del día no alcanza para el carrusel entero.
Muestra al director las láminas y los pies, y pregunta: "¿Apruebas? ¿Enviar a Avisos?".

## PASO 5 — Envío real (solo después del sí del director)

```bash
uv run --extra stories --with MetaTrader5 python scripts/pipeline_carrusel.py --despachar data/carrusel/<tanda>
```

Si pasaron minutos desde la aprobación, el refresco actualiza las cifras; si la moneda dio vuelta,
la pieza no sale y hay que `--refrescar --reescribir` y volver a escribir el párrafo.

**Nunca se envía nada a Avisos sin aprobación explícita del director.**

## Un mensaje suelto con links (invitaciones a los grupos)

Los mensajes que no son tanda (un recordatorio para unirse a Forex y a Commodities, por ejemplo) van
por el envío directo, con el texto en un archivo escrito en UTF-8:

```bash
uv run --extra stories python scripts/enviar_whatsapp.py --grupo macro --mensaje-archivo <txt> --sin-vista-previa
```

**Con dos o más links, `--sin-vista-previa` es obligatorio.** WhatsApp Web arma la tarjeta de vista
previa solo con el **primer** link, y su botón "Ver grupo" lleva a todos al mismo grupo (medido el
2026-10-02: los dos botones iban a Forex). El flag cierra la tarjeta antes de enviar y cada link
queda como texto que se abre por separado. Va en **un solo mensaje**, para que el director lo pueda
fijar, y sin la línea `━━━` bajo el título, que se ve mal en la previsualización.
