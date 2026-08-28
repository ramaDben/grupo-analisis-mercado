Genera el carrusel responsivo de alertas de mercado: hasta 3 Stories de alerta con los activos que
el escáner eligió objetivamente según la sesión activa y la hora real, más el mensaje índice para el grupo.

Uso: `/carrusel` (detecta automáticamente la sesión activa y la hora real)

## PASO 1 — Escanear el universo (OBLIGATORIO, y no se hace a mano)

```bash
uv run --with MetaTrader5 python scripts/pipeline_carrusel.py --preparar
```

Esto corre `scripts/screener_gi.py`, que detecta dinámicamente la sesión de mercado (Asiática, Europea, Apertura Wall Street, Rotación de Tarde o Cierre), puntúa el universo con el `Score_GI` (técnico 35 + catalizador 25 + espacio 20 + momentum 20 = 100), aplica los gates, excluye activos ya publicados en corridas previas de hoy y deja los payloads con **todos los datos resueltos**.

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
editorial. Cada payload en `data/carrusel/<fecha>_<hora>_<sesion>/` tiene los dos campos vacíos y
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
uv run --extra stories python scripts/pipeline_carrusel.py --rendir data/carrusel/<directorio>
```

Produce 2 imágenes por pieza (horizontal y vertical) en `data/stories/`. Si algún campo
editorial quedó vacío, **se detiene**: una pieza a medias que sale sin avisar llega al
cliente.

## PASO 4 — Mensaje índice para el grupo

Un solo mensaje que acompaña los adjuntos, con las 6 reglas de formato del proyecto y la **hora real** de ejecución:

```text
📊 *ALERTA DE MERCADO · [NOMBRE DE LA SESIÓN]* · [HH:MM] hrs
━━━━━━━━━━━━━━━━━━━
🎯 Lo que estamos mirando ahora en [N] activos

1️⃣ *[Activo]* → [dirección en una línea]
2️⃣ *[Activo]* → [dirección en una línea]
3️⃣ *[Activo]* → [dirección en una línea]
━━━━━━━━━━━━━━━━━━━
⏱️ Temporalidad: intradía (dentro de la jornada)
[Una línea sobre el evento macro o driver que ordena el mercado, si hubo]
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

## Sesiones de mercado continuas (24 horas)

El ciclo global de mercado está anclado a la hora de **Nueva York**, informando la hora equivalente de **Chile** en tiempo real:

| Sesión | Ventana (Nueva York) | Ventana (Chile / CLT aprox.) | Foco Operativo |
|---|---|---|---|
| **Sesión Asiática / Pacífico** | 18:00 – 02:00 | 19:00 – 03:00 | Activos de Asia, JPY, Oro, Cobre, Cripto y materias primas |
| **Sesión Europea / Londres** | 02:00 – 08:30 | 03:00 – 09:30 | Quiebres de apertura europea, EUR, GBP, DAX y pre-mercado EE.UU. |
| **Apertura Wall Street** | 08:30 – 12:30 | 09:30 – 13:30 | Volatilidad de primera hora, quiebres intradía y catalizadores macro |
| **Rotación de Tarde Wall Street** | 12:30 – 15:30 | 13:30 – 16:30 | Flujos vespertinos, rebalanceo institucional y continuidad de tendencia |
| **Cierre Wall Street / Post-Mercado** | 15:30 – 18:00 | 16:30 – 19:00 | Balance de sesión americana, earnings y preparación para Asia |
| **Fin de Semana** | Sábado / Domingo | Sábado / Domingo | Activos Cripto y preparación estratégica para la apertura semanal |

El escáner excluye automáticamente los activos que ya salieron en cualquier corrida anterior del mismo día, permitiendo ejecutar `/carrusel` en cualquier momento sin repetir activos.
