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

**Si la apertura se niega a generarse, no la fuerces sin leer por qué.** El informe de
apertura depende de `macro_bias_output.json`; si está vencido, el script se detiene y nombra
el remedio: correr `pipeline_ingesta.py` y después `macro_bias_engine.py`. Refrescar el dato
es siempre la primera opción.

`--con-datos-viejos` existe para cuando el director decide publicar igual. En ese caso el
informe **estampa el aviso en la primera página** diciendo que va sin el sesgo del motor y
que ninguna cifra debe leerse como lectura suya. La decisión de publicar con datos vencidos
es del director; que el lector lo sepa, no.

## PASO 2 — Escribir el análisis

El markdown trae 4 secciones marcadas con `[[ESCRIBIR]]`. Las tablas son datos; el análisis
es tuyo:

1. **Marco de la jornada**: dos párrafos. Qué deja la sesión anterior y con qué abre esta.
2. **Régimen y sesgo**: qué significa el régimen vigente para operar hoy. Los `setups_prohibidos`
   de la tabla son prohibiciones, no sugerencias: nómbralas como tales.
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

## PASO 3 — Compilar

```bash
uv run --extra stories --with markdown --with pypdf python scripts/pipeline_informe.py \
  --tipo apertura --rendir data/informes/<dir>
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
