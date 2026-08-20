# Calculadoras Excel

| Archivo | Función | Estado |
|---|---|---|
| `Simulador GI.xlsx` | Simular un periodo de operaciones sobre cualquiera de los 25 instrumentos del catálogo | **Vigente** |
| `Simulación_USDCLP_explicativa 1.xlsx` | Planilla original de post-venta, exclusiva para USD/CLP | Vigente, con fórmulas corregidas |

---

## Simulador GI

### Objetivo

Cuantificar, frente al cliente, el resultado real de un conjunto de operaciones: cuánto capital compromete, qué exposición controla, qué costos asume y con qué patrimonio termina.

Está diseñada para que la opere alguien sin formación en trading: **no requiere conocer el volumen en lotes, el spread vigente ni el tamaño de contrato de cada instrumento**. Esos parámetros se resuelven automáticamente a partir de las especificaciones del broker.

Al igual que la planilla original de post-venta, **cada fila es una operación independiente**, con su propia fecha, dirección y capital asignado. Se pueden combinar compras y ventas dentro del mismo periodo.

### Estructura de la hoja

Solo se completan las celdas **crema**. El resto está protegido, para impedir que una fórmula se sobrescriba por accidente.

**Bloque de contexto** (dos campos, aplican a todo el periodo):

| | Campo | Contenido |
|---|---|---|
| 1 | Instrumento | se selecciona de la lista desplegable (25 instrumentos del catálogo) |
| 2 | Capital de la cuenta | capital total disponible del cliente, en pesos |

Todas las operaciones de la tabla corresponden al **mismo instrumento**. Para simular otro, se cambia el instrumento y se actualizan los precios.

**Tabla de operaciones** (hasta 6 registros). Campos a completar:

La tabla se divide en dos bloques, como la planilla original: **SIMULACIÓN**, con la definición de la operación y su resultado bruto, y **COSTOS**, con lo que el broker descuenta y el resultado neto.

| Campo | Contenido |
|---|---|
| DIRECCIÓN | COMPRA o VENTA, desde la lista desplegable. **Una por fila** |
| VOLUMEN EN CLP | monto en pesos que se destina a esa operación |
| PRECIO DE ENTRADA | precio de apertura, tomado del gráfico de MT5 |
| PRECIO DE SALIDA | precio de cierre, efectivo o proyectado |
| DÍAS DE MANTENCIÓN | días completos que la posición permanece abierta. **0 si se abre y cierra en la misma jornada** |

### Resultados por operación

| Columna | Qué informa |
|---|---|
| **VOLUMEN EN LOTES** | gemela de VOLUMEN EN CLP: la misma magnitud en la unidad del terminal. Es el número que se ingresa en MT5. Se calcula del importe y se trunca a la baja al paso de 0,01 que exige MT5, así que un importe puede quedar levemente por sobre el volumen que financia |
| **RESULTADO BRUTO** | resultado de la operación antes de costos. Cierra el bloque SIMULACIÓN |
| **COSTO DE APERTURA (SPREAD)** | el spread, es decir la diferencia entre precio de compra y de venta que el broker cobra al abrir. Expresado en pesos |
| **COSTO DE MANTENCIÓN (SWAP)** | el cargo que aplica el broker por mantener la posición abierta de un día para otro. En blanco si son 0 días |
| **RESULTADO NETO** | resultado con ambos costos ya descontados. **Es la cifra que se comunica al cliente.** Se destaca en rojo si es negativa |
| **OBSERVACIÓN** | advierte, en rojo, cuando el precio de salida es incompatible con la dirección declarada |

### Cierre del periodo

| Indicador | Qué informa |
|---|---|
| **Exposición nocional total** | valor total de las posiciones controladas. Es la cifra que dimensiona el apalancamiento ante el cliente: compromete $1,2 millones y controla $119 millones |
| **Margen requerido (posiciones simultáneas)** | capital que quedaría bloqueado si todas las operaciones estuvieran abiertas al mismo tiempo. Se calcula sobre el volumen ya redondeado, de modo que no coincide exactamente con la suma del capital comprometido |
| **Resultado neto del periodo** | suma de los resultados netos |
| **Patrimonio final** | capital de la cuenta más el resultado neto |

### Validaciones automáticas

La franja bajo el bloque de contexto verifica, en este orden:

| Mensaje | Condición |
|---|---|
| Seleccione un instrumento de la lista | falta el instrumento |
| Hay una operación con volumen y sin precio de entrada | registro incompleto |
| Un precio de entrada difiere en más de 10% del precio de referencia | típicamente, se cambió de instrumento y quedó el precio del anterior |
| Hay una operación bajo el volumen mínimo de 0,01 lotes | el importe asignado es insuficiente. El mínimo varía por instrumento: cerca de $9.200 en USD/CLP, cerca de $186.000 en Oro |
| El margen requerido excede el capital de la cuenta | sobreapalancamiento |
| ✓ *n* operación(es) sobre *instrumento* | sin observaciones |

---

## Consideraciones previas al uso con clientes

### 1. El spread queda fijado al generar el archivo

Se informa en el bloque de referencias como **"Spread vigente al generar"**, expuesto deliberadamente para que no opere como un supuesto oculto.

**Su variación es significativa**: en una misma tarde el spread de USD/CLP pasó de 0,40 a 1,00, y el costo de apertura de una posición idéntica subió de $21.600 a $54.000.

Si el archivo se generó en una ventana de spread ampliado (apertura, cierre, publicación de datos macroeconómicos, baja liquidez), **todas las simulaciones heredan esa condición**. Verifique ese valor antes de dar el costo por válido, y regenere el archivo si no representa una condición normal de mercado.

### 2. El costo de mantención es una estimación

El swap se calcula según el modo que declara cada instrumento en el terminal:

| Modo | Instrumentos | Cálculo |
|---|---|---|
| Puntos | forex y materias primas (USD/CLP, Oro, Plata, WTI, pares) | puntos por día, por lote |
| Interés | índices, cripto y acciones | interés anual sobre el nocional, con año bancario de 360 días |

El conteo usa **días calendario**, sin ajustes. Es lo consistente con la forma en que cobra el broker: el cargo triple que aplica un día a la semana no se suma al fin de semana, lo reemplaza, porque sábado y domingo no hay rollover. Una semana completa son 7 cargos para 7 días calendario.

Contrastado contra el historial del terminal, el cálculo queda dentro de **0,3%** del swap efectivamente cobrado. La operación de control es una compra de #AAPL de 2,98 lotes abierta el 5 de agosto y cerrada el 11, seis días calendario que incluyen un fin de semana completo: el terminal cobró $36.063,35 y la planilla calcula $36.163,34.

Tiene un límite conocido: mientras la posición sigue abierta y arrastra un fin de semana que el cargo triple todavía no compensó, la estimación queda **por sobre** el cargo real. Se regulariza cuando el cargo triple se aplica. Se prefirió ese sesgo al contrario, porque subestimar un costo frente a un cliente es el error más costoso.

Su magnitud no es marginal: **una compra de Apple con $300.000 de capital comprometido, mantenida 20 días, acumula $169.688 de costo de mantención.** Más de la mitad del capital asignado, únicamente por mantener la posición abierta.

### 3. No incorpora stop loss (exclusión deliberada)

Por decisión de la dirección, la planilla no incluye stop loss. Cuantifica el escenario declarado, no la pérdida máxima si el precio evoluciona en contra.

En consecuencia, **el límite de pérdida se comunica por separado** y esta planilla no constituye por sí sola el respaldo completo de una recomendación.

Si se necesita dimensionar el escenario adverso, la herramienta ya lo permite sin modificaciones: se registra la operación con el precio de salida en contra, y la columna RESULTADO NETO entrega la pérdida en pesos con los costos incluidos.

---

## Actualización de las especificaciones

Los parámetros de cada instrumento (tamaño de contrato, margen exigido, spread, swap) residen en la hoja **Datos** y provienen del terminal MT5. Son variables: el margen lo define el broker, el spread fluctúa durante la jornada, y el valor en pesos de los instrumentos cotizados en dólares depende del tipo de cambio.

Para actualizarlos, con **MT5 abierto y conectado**:

```bash
uv run --with MetaTrader5 --with openpyxl --with pillow --with tzdata python scripts/simulador_gi.py
```

El comando **regenera el archivo completo**, de modo que las operaciones registradas se pierden. Para conservar una simulación, guárdela previamente con otro nombre.

`MetaTrader5`, `openpyxl`, `pillow` y `tzdata` no son dependencias del proyecto: se inyectan con `uv run --with` para no alterar el `.venv`.

La hoja **Datos** no se edita manualmente. Si un valor es incorrecto, el origen está en MT5 o en el script, y ahí se corrige.

### Verificación recomendada

Antes de usar la planilla con un cliente nuevo, contraste un caso contra el terminal: ingrese ese volumen en MT5, observe el margen que reporta la caja de herramientas y compárelo con **Margen requerido**. Si no coinciden, la discrepancia está en la hoja `Datos`, no en las fórmulas.

---

## Planilla original de USD/CLP

`Simulación_USDCLP_explicativa 1.xlsx` mantiene su estructura, con tres correcciones de fórmula:

1. El **margen** se calcula al precio de entrada de cada fila, y no a un tipo de cambio fijo que quedaba desactualizado.
2. El **resultado en pesos** pasó a ser el cálculo primario, por lo que ya no arrastra residuos de coma flotante (`-999.999,99999999988`).
3. El **spread** y el **margen requerido** pasaron a ser celdas editables en el encabezado, en lugar de constantes incrustadas en las fórmulas.

Por eso la celda rotulada **TIPO DE CAMBIO** ahora indica **MARGEN (%)**: en USD/CLP el tipo de cambio y el precio del par son la misma magnitud, de modo que mantener ambos campos era la inconsistencia de origen.

Esa planilla aplica exclusivamente a USD/CLP. Para cualquier otro instrumento, corresponde usar el Simulador.
