Genera el carrusel de una tanda diaria: hasta 3 Stories de alerta con los activos que
el escáner eligió objetivamente, más el mensaje índice para el grupo.

Uso: `/carrusel` (deriva la tanda de la hora) · `/carrusel 2` (fuerza la tanda)

## PASO 1 — Escanear el universo (OBLIGATORIO, y no se hace a mano)

```bash
uv run --with MetaTrader5 python scripts/pipeline_carrusel.py --preparar
uv run --with MetaTrader5 python scripts/pipeline_carrusel.py --preparar --tanda 2
```

Esto corre `scripts/screener_gi.py`, que puntúa el universo con el `Score_GI`
(técnico 35 + catalizador 25 + espacio 20 + momentum 20 = 100), aplica los gates y deja
los payloads con **todos los datos resueltos**.

**No elijas los activos por tu cuenta ni negocies con el escáner.** La razón de que exista
es que la selección sea objetiva y auditable: si el resultado no te gusta, se discute el
criterio del escáner, no la corrida del día. Si el escáner selecciona menos de 3 activos, o
ninguno, **eso es el resultado** y así se comunica. Una tanda de 2 piezas bien elegidas es
mejor que una de 3 con un relleno.

**Lee los avisos que imprime.** Si dice que el calendario no respondió, el gate de blackout
no pudo verificarse y hay que decidir a mano si se publica. Si dice que el sesgo del
Playbook está vencido, el gate de prohibiciones está parcialmente ciego para los 5 activos
con ficha: correr `pipeline_ingesta.py` y después `macro_bias_engine.py`.

## PASO 2 — Escribir el texto de cada pieza

El escáner y el pipeline no escriben el titular ni el párrafo, porque eso es criterio
editorial. Cada payload en `data/carrusel/<fecha>_tanda<N>/` tiene los dos campos vacíos y
marcados en `_pendiente_editorial`. Por cada pieza, escribe:

- **`titular`**: qué está pasando con ese activo y hacia dónde va. Toma postura direccional:
  un titular que no dice la dirección está incompleto (regla de oro del proyecto).
- **`parrafo`**: 2 o 3 frases. Traduce a voz novata lo que dice el factor técnico del score
  (está en `_procedencia.factores`), y si el factor Espacio salió bajo, **dilo**: que el
  recorrido diario esté casi agotado es información que el cliente necesita, no un defecto
  que se esconde.

Reglas de redacción que aplican íntegras: cero guiones largos ni medios, tono profesional
con gancho pero sin dramatizar, decimales según `digits` (ya vienen formateados en el
payload, no los toques), y toda sigla explicada en voz novata.

**No inventes cifras.** Precio, soporte, resistencia e impulso ya están en el payload y
salieron del motor. Si necesitas un dato que no está, pídelo al MCP; nunca lo deduzcas.

## PASO 3 — Rendir las piezas

```bash
uv run --extra stories python scripts/pipeline_carrusel.py --rendir data/carrusel/<dir>
```

Produce 2 imágenes por pieza (horizontal y vertical) en `data/stories/`. Si algún campo
editorial quedó vacío, **se detiene**: una pieza a medias que sale sin avisar llega al
cliente.

## PASO 4 — Mensaje índice para el grupo

Un solo mensaje que acompaña los adjuntos, con las 6 reglas de formato del proyecto:

```text
📊 *[NOMBRE DE LA TANDA]* · [hora] hrs
━━━━━━━━━━━━━━━━━━━
🎯 Lo que estamos mirando ahora en [N] activos

1️⃣ *[Activo]* → [dirección en una línea]
2️⃣ *[Activo]* → [dirección en una línea]
3️⃣ *[Activo]* → [dirección en una línea]
━━━━━━━━━━━━━━━━━━━
⏱️ Temporalidad: intradía (dentro de la jornada)
[Una línea sobre el evento macro que ordena la jornada, si hubo]
━━━━━━━━━━━━━━━━━━━
Cada imagen tiene los niveles del activo. ¿Dudas? Habla con tu analista.
```

**Máximo 3 imágenes.** WhatsApp muestra 3 adjuntos con previsualización; del cuarto en
adelante aparece el botón `+2` y el cliente ya no ve lo que le mandaste.

## PASO 5 — Aprobación

Muestra el mensaje índice y las rutas de las imágenes. Pregunta: "¿Apruebas? ¿Enviar al
grupo?". Guarda el mensaje con:

```powershell
scripts\ruta_mensaje.ps1 -Fecha "<fecha>" -Tipo "alerta" -Hora "<HH-mm>"
```

Sin activo protagonista (`-Activo` omitido) porque el índice cubre varios: cae en `_general/`.

**Nunca se envía nada al grupo sin aprobación explícita del director.**

## Las 3 tandas

Ancladas a la hora de **Nueva York**, no al reloj chileno: Chile y EE.UU. cambian de
horario en sentido opuesto, así que el desfase se mueve dos veces al año. El script
imprime la hora de Chile equivalente del día en que corre.

| Tanda | Ancla (Nueva York) | Foco |
|---|---|---|
| 1 | 10:30 (apertura + 1 h) | Volatilidad y quiebres de la primera hora |
| 2 | 14:30 | Flujos vespertinos, sin repetir la tesis de la mañana |
| 3 | 16:45 (cierre + 45 min) | Balance de la sesión y preparación de Asia |

La tanda 2 excluye automáticamente los activos que ya salieron en la tanda 1 del mismo día.
