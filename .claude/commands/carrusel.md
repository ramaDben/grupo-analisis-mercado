Genera el carrusel responsivo de alertas de mercado: hasta 3 Stories de alerta con los activos que
el escáner eligió objetivamente según la sesión activa y la hora real, más el mensaje índice para el grupo.

Uso:
- `/carrusel` (Modo multiactivo global de sesión, detecta automáticamente la sesión activa y la hora real)
- `/carrusel --grupo <forex|commodities|indices|acciones|crypto>` (Modo granular por canal temático)
- `/carrusel --matriz` (Modo cobertura total: 1 pieza para cada uno de los 5 grupos de mercado)

## PASO 1 — Escanear el universo y preparar carpetas modulares

```bash
uv run --with MetaTrader5 python scripts/pipeline_carrusel.py --preparar
# O si se ejecuta para un grupo específico:
uv run --with MetaTrader5 python scripts/pipeline_carrusel.py --preparar --grupo forex
# O para cobertura completa de todos los canales:
uv run --with MetaTrader5 python scripts/pipeline_carrusel.py --preparar --matriz
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

**Si la preparación aborta con `DatosMacroNoDisponiblesError`, es a propósito.** Significa que
falta la serie oficial que alimenta el contexto macro de ese grupo (Imacec o TPM del BCCh, o una
serie del Tesoro en `data central/`). El módulo se detiene en vez de rellenar con una serie
escrita a mano, porque una cifra inventada bajo el sello del BCCh o de FRED es peor que no
publicar. La salida es correr la ingesta, **nunca** editar el JSON de datos ni pegar números a
mano en el script.

## PASO 2 — Cobertura macro diaria y texto editorial en cada carpeta de grupo

El pipeline organiza automáticamente las piezas en **subcarpetas según el grupo de WhatsApp de destino**:
- `02_forex_divisas/` (USD/CLP, EUR/USD, USD/JPY, GBP/USD)
- `03_commodities_materias_primas/` (Oro, Plata, WTI, Cobre)
- `04_indices_bursatiles/` (Nasdaq 100, S&P 500, Dow Jones, DAX 40)
- `05_acciones_etfs/` (Mega-caps, Bancos, ETFs sectoriales)
- `06_criptoactivos/` (Bitcoin, Ethereum, Solana)

### 🏛️ Cobertura Macro Diaria Automática por Canal (Imagen Story + Texto)
Al preparar la tanda, el pipeline genera automáticamente en cada subcarpeta activa:
1. **`0_contexto_macro.png`**: Story visual en 16:9 con diseño de marca, tarjeta macro con cifras oficiales y gráfico de serie histórica (ej. Imacec en Forex con barras reales del Banco Central de Chile).
2. **`contexto_macro.txt`**: Mensaje de WhatsApp estructurado y pedagógico. En **Forex & Divisas**, prioriza siempre datos de Chile (**Imacec, IPC, TPM/BCCh, Balanza Comercial**) en primer lugar, seguido de la curva soberana del Tesoro EE.UU. (2Y/10Y) y la interpretación cambiaria sin redundancias de viñetas.

### ✍️ Texto Editorial de las Alertas Técnicas
Cada payload `.json` dentro de su subcarpeta tiene `titular` y `parrafo` marcados en `_pendiente_editorial`. Por cada pieza, escribe:

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

## PASO 3 — Rendir las piezas y generar mensajes modulares

```bash
uv run --extra stories python scripts/pipeline_carrusel.py --rendir data/carrusel/<directorio>
```

Esto ejecuta el renderizado automático y produce:
1. Las imágenes horizontales (16:9) en `data/stories/` y una copia directa `.png` en cada subcarpeta modular del grupo.
2. El archivo `mensaje.txt` listo para copiar y pegar en cada grupo temático de WhatsApp, con el resumen al inicio, niveles, emojis de escenarios y cierre pedagógico.
3. El archivo `mensaje_indice.txt` en la raíz de la tanda para el canal general/macro.
4. El archivo `contexto_macro.txt` institucional verificado y listo para publicación en cada grupo.

## PASO 4 — Mensajes para cada canal y canal índice

- **Para cada grupo temático**: Usar la imagen `.png` y el texto de `mensaje.txt` generados dentro de la carpeta del grupo (`02_forex_divisas/`, `03_commodities_materias_primas/`, etc.).
- **Para el canal central / macro (`01_macro_y_apertura`)**: Usar el `mensaje_indice.txt` generado en la raíz del directorio de la tanda:

```text
📊 *ALERTA DE MERCADO · [NOMBRE DE LA SESIÓN]* · [HH:MM] hrs
━━━━━━━━━━━━━━━━━━━
🎯 Lo que estamos mirando ahora en [N] activos:

1️⃣ *[Activo]* → [titular o dirección]
2️⃣ *[Activo]* → [titular o dirección]
3️⃣ *[Activo]* → [titular o dirección]
━━━━━━━━━━━━━━━━━━━
⏱️ Temporalidad: intradía (dentro de la jornada)
━━━━━━━━━━━━━━━━━━━
Cada imagen y mensaje detallado han sido modularizados en su canal correspondiente.
```

## PASO 5 — Aprobación

Muestra el mensaje índice y las rutas de las piezas modularizadas. Pregunta: "¿Apruebas? ¿Enviar a los canales de WhatsApp?".

**Nunca se envía nada a ningún grupo sin aprobación explícita del director.**

## PASO 6 — Envío (solo después del "sí" del director)

El envío **no** es parte de la generación y nunca se encadena solo. Una vez que el
director aprueba, cada canal se manda con su imagen y su texto:

```bash
uv run --extra stories python scripts/enviar_whatsapp.py \
  --grupo metales \
  --adjunto "data/carrusel/<tanda>/03_commodities_materias_primas/0_contexto_macro.png" \
  --mensaje-archivo "data/carrusel/<tanda>/03_commodities_materias_primas/contexto_macro.txt"
```

Tres cosas que conviene no volver a averiguar:

- **`--grupo` acepta los alias de `config/whatsapp_grupos.json`** (`metales`, `oro`,
  `forex`, `indices`, `acciones`, `cripto`, `senales`, `macro`, y también el nombre
  literal del canal). Un alias que no se reconoce **aborta**: antes caía en silencio
  al canal macro y publicaba en el grupo equivocado.
- **El comando verifica que el mensaje aparezca en la conversación** antes de decir
  "enviado", y compara la cabecera del chat abierto contra el destinatario de forma
  exacta. Si aborta, no se envió: no lo des por bueno ni lo repitas a ciegas, revisa
  primero si llegó.
- **Un envío por canal, y máximo 3 imágenes por canal.** Del cuarto adjunto en
  adelante WhatsApp muestra el botón `+2` y el cliente ya no ve la pieza.

Comprobar la sesión antes de una tanda: `python scripts/enviar_whatsapp.py --status`.
Si pide vinculación: `--login` y escanear el QR.

### El ritmo no es negociable

Automatizar WhatsApp Web va **contra sus términos de servicio**, y el número es el
del negocio. El comando impone dos frenos por su cuenta, leídos de `seguridad` en
`config/whatsapp_grupos.json`:

- **45 segundos mínimos entre envíos.** Si llamas antes, el comando **espera** y lo
  dice. Mandar siete canales en ráfaga es el patrón que marca una cuenta.
- **Cupo de 40 envíos al día.** Superado, se detiene con `LimiteEnviosError`. El
  contador vive en `data/.whatsapp_envios.json`.

Nunca subas esos límites para "salir del paso", y **nunca metas el envío en un bucle
sin supervisión**. Si un envío aborta, revisa si el mensaje llegó antes de reintentar:
repetir a ciegas duplica la pieza en el grupo y suma un envío al cupo.

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
