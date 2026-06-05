Genera piezas de habilitación comercial para ejecutivos. Produce dos artefactos: `preview.html` (para prepararse y exportar PDF) y `whatsapp.txt` (para enviar al cliente por WhatsApp).

## SETUP

Lee `config/ejecutivos.json`. Usa el campo `area_activa` para obtener la configuración del área activa (nombre, firma, activos_foco, disclaimer).

Obtén la fecha y hora de Chile:
```powershell
$tz = [System.TimeZoneInfo]::FindSystemTimeZoneById('Pacific SA Standard Time')
$now = [System.TimeZoneInfo]::ConvertTime([DateTime]::UtcNow, [System.TimeZoneInfo]::Utc, $tz)
$fecha     = $now.ToString('yyyy-MM-dd')
$fecha_es  = $now.ToString('d') + ' de ' + (Get-Culture).DateTimeFormat.GetMonthName($now.Month) + ' de ' + $now.Year
```

Parsea `$ARGUMENTS`:
- `kit`                    → flujo A
- `folleto [producto]`     → flujo B (producto es opcional; ver fallback)
- `apertura`               → flujo C
- `semana`                 → flujo D
- `mirror`                 → flujo E
- Sin argumentos o tipo inválido → mostrar:
  ```
  ¿Qué tipo de pieza necesitas?
  1. kit       — Kit de primer contacto (presentación + scripts)
  2. folleto   — Folleto de un producto específico
  3. apertura  — Niveles del día como oportunidades de inversión
  4. semana    — Calendario semanal con oportunidades de conversación
  5. mirror    — Versión ejecutivo de la última pieza enviada al cliente
  ```
  Esperar respuesta del director y continuar con el flujo elegido.

---

## FLUJO A — Kit de primer contacto (`/ejecutivo kit`)

Lee el template `templates/ejecutivo/kit.html`.

Genera el contenido de cada sección con lenguaje comercial (no técnico):

**Sección 1 — Presentación** (`{{seccion_presentacion}}`):
Redacta un párrafo que explique qué es Grupo Inteligencia, qué hace el área de trading y qué valor aporta al cliente. Tono: cercano, confiable, no financiero técnico. Incluye mención a la supervisión CMF.

**Sección 2 — Script no contesta** (`{{script_no_contesta}}`):
Mensaje corto (3-4 líneas) que el ejecutivo puede enviar por WhatsApp si el cliente no contestó la llamada. Tono: no intrusivo, deja la puerta abierta. Ejemplo base:
> "Hola [Nombre], te contacté del equipo de trading de Grupo Inteligencia. Tenía un dato del mercado que puede ser de tu interés. Cuando tengas un momento, con gusto te cuento. Saludos."

**Sección 3 — Script sí contesta** (`{{script_si_contesta}}`):
Guía de conversación en 3 pasos:
1. Apertura (presentación rápida, máx 2 líneas)
2. Gancho (mencionar un dato macro o movimiento reciente del activo más relevante del día, obtenido de `config/ejecutivos.json` campo `activos_foco[0]`)
3. Cierre (ofrecer envío de material + coordinar próxima conversación)

Reemplaza todas las `{{variables}}` en el template: `{{fecha}}` → `$fecha_es`, `{{area_nombre}}` → nombre del área, `{{ejecutivo_firma}}` → valor de `firma`, `{{disclaimer}}` → valor de `disclaimer`.

Guarda el HTML generado como `preview.html` y el TXT (script condensado de contacto) como `whatsapp.txt`.

Ruta de guardado:
```powershell
$dir = "data/mensajes/ejecutivos/$fecha/kit"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
```
Guardar `preview.html` en `$dir/preview.html` y `whatsapp.txt` en `$dir/whatsapp.txt`.

Mostrar al director para aprobación:
```
━━━━━━━━━━━━━━━━━━━
📋 KIT DE PRIMER CONTACTO — [fecha_es]
━━━━━━━━━━━━━━━━━━━
[resumen de lo generado en TXT — script condensado]
━━━━━━━━━━━━━━━━━━━
✅ Artefactos listos:
   • preview.html → data/mensajes/ejecutivos/[fecha]/kit/preview.html
     (Abre en Chrome → Ctrl+P → Guardar como PDF para distribuir)
   • whatsapp.txt → data/mensajes/ejecutivos/[fecha]/kit/whatsapp.txt

¿Aprobado? ¿Ajustar algo?
```

Al aprobar: guardar ambos archivos con Write.

---

## FLUJO B — Folleto de producto (`/ejecutivo folleto [producto]`)

Lee `config/productos.json`.

**Si `productos` está vacío** (catálogo aún no definido):
```
⚠️ El catálogo de productos aún está vacío (issue pendiente).
Puedes generar el folleto ingresando los datos manualmente:

Nombre del producto:
Tipo (ej: Fondo Mutuo / APV / Renta Fija / Acciones):
Descripción breve (1 línea):
Beneficios (escribe 1 por línea, termina con línea vacía):
¿Para quién es? (perfil del cliente objetivo):
```

**Si hay productos** y se pasó nombre en `$ARGUMENTS`: buscar por nombre (case-insensitive). Si no se pasó nombre o no se encontró, mostrar lista y pedir elección.

Lee el template `templates/ejecutivo/folleto.html`. Reemplaza:
- `{{producto_nombre}}` → nombre del producto
- `{{producto_tipo}}` → tipo
- `{{producto_descripcion}}` → descripción
- `{{producto_beneficios}}` → lista HTML: cada beneficio como `<li>texto</li>`
- `{{producto_para_quien}}` → texto del perfil del cliente
- `{{fecha}}` → `$fecha_es`
- `{{area_nombre}}` → nombre del área
- `{{ejecutivo_firma}}` → valor `firma`
- `{{disclaimer}}` → valor `disclaimer`

Ruta de guardado:
```powershell
$slug_producto = "[nombre-producto-lowercase-sin-espacios]"
$dir = "data/mensajes/ejecutivos/$fecha/folleto-$slug_producto"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
```

El `whatsapp.txt` contiene 3 bullets del producto en formato WhatsApp:
```
📄 *[Nombre del producto]*

• [Beneficio 1]
• [Beneficio 2]
• [Beneficio 3]

¿Te interesa que te cuente más? 😊
```

Mostrar para aprobación con la misma estructura del FLUJO A (adaptando el tipo a "FOLLETO · [nombre producto]").

---

## FLUJO C — Apertura ejecutivo (`/ejecutivo apertura`)

Obtén los activos del día desde `config/ejecutivos.json` campo `activos_foco`.

Para **CADA activo** en `activos_foco`, llama:
```
mcp__market-data__get_asset_levels({"ticker": "[TICKER_MT5]", "timeframe": "H1"})
```

Con los datos obtenidos (precio, soportes, resistencias), genera el encuadre comercial:
- `{{activo_nombre}}` → nombre amigable del activo (consultar `config/activos.json`)
- `{{zona_entrada}}` → rango entre soporte más cercano y precio actual, en formato precio (ej: "889.60 – 895.00")
- `{{precio_actual}}` → precio actual del MCP
- `{{argumento_comercial}}` → 2-3 líneas en lenguaje novato explicando por qué es momento de conversar con clientes sobre este activo. Sin jerga técnica. Conectar con drivers de `config/drivers.json`.
- `{{clientes_objetivo}}` → tipo de cliente que tiene sentido contactar hoy (ej: "Clientes con inversiones en dólares")

Si el MCP devuelve error para un activo: omitir ese activo del HTML y anotarlo en el TXT como "⚠️ Sin datos para [activo] hoy".

Lee el template `templates/ejecutivo/apertura.html`. Construye el bloque `{{cards_activos}}` concatenando una card por activo, usando esta estructura exacta (clases reales de `apertura.html`):

```html
<div class="asset-card">
  <div class="asset-header">
    <div class="asset-name">{{activo_nombre}}</div>
    <div class="zona-label">Zona de entrada interesante</div>
    <div class="zona-value">{{zona_entrada}}</div>
    <div class="precio-row">Precio actual: {{precio_actual}}</div>
  </div>
  <div class="asset-body">
    <div class="body-label">Argumento comercial</div>
    <div class="argumento">{{argumento_comercial}}</div>
    <div class="body-label">Clientes a contactar</div>
    <div class="clientes-tag">{{clientes_objetivo}}</div>
  </div>
</div>
```

Se concatena una de estas cards por cada activo, reemplazando las sub-variables, y el resultado va en `{{cards_activos}}`.

Ruta de guardado:
```powershell
$dir = "data/mensajes/ejecutivos/$fecha/apertura"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
```

El `whatsapp.txt` contiene un argumento por activo, en formato:
```
📊 *Oportunidades del día — [fecha_es]*

💰 *[Activo A]*
[argumento_comercial en 2 líneas]
→ Llama a: [clientes_objetivo]

💰 *[Activo B]*
[...]
```

---

## FLUJO D — Semana ejecutivo (`/ejecutivo semana`)

Llama `mcp__market-data__obtener_calendario_macro({"min_impact": "medium"})`.

Si devuelve error: usar WebSearch como fallback (query: `investing.com calendario económico semana [fecha] Chile Estados Unidos impacto alto`).

Para cada evento del calendario, determina:
- `{{producto_relevante}}` → qué producto de banca inversiones puede conectarse con ese dato macro. Lógica:
  - Datos de empleo/inflación USA → "Acciones / Renta Fija"
  - Datos de tasas Fed/BCCh → "APV / Fondos Mutuos"
  - Datos de inventarios petróleo → mencionar solo si aplica
  - Datos de China → "Acciones internacionales"
  - Default → "Portafolio diversificado"
- `{{tipo_cliente}}` → perfil del cliente al que tiene sentido llamar ese día (ej: "Clientes conservadores", "Clientes con dólares")
- Impacto: clase CSS `impact-high` para alto (★★★), `impact-med` para medio (★★)

Construye `{{filas_semana}}` con una fila HTML por evento, usando esta estructura exacta (clases reales de `semana.html`). Para la celda de impacto, usa `impact-high` si el impacto es alto (★★★) o `impact-med` si es medio (★★):

```html
<tr>
  <td class="dia-cell">{{dia}}<br><span style="font-weight:400;color:var(--muted);font-size:12px;">{{hora_clst}}</span></td>
  <td>{{evento_nombre}}<br><span style="color:var(--muted);font-size:12px;">{{evento_pais}} · {{evento_periodo}}</span></td>
  <td class="impact-high">{{impacto_emoji}} {{impacto_label}}</td>
  <td><span class="producto-tag">{{producto_relevante}}</span></td>
  <td style="color:var(--muted)">{{tipo_cliente}}</td>
</tr>
```

Se concatena una fila por evento y el resultado va en `{{filas_semana}}`.

Antes de renderizar, calcula el rango de la semana (lunes a viernes de la semana actual):
```powershell
$inicio = $now.Date.AddDays(-([int]$now.DayOfWeek - 1))   # lunes
$fin    = $inicio.AddDays(4)                                # viernes
$fecha_inicio = $inicio.ToString('d') + ' de ' + (Get-Culture).DateTimeFormat.GetMonthName($inicio.Month)
$fecha_fin    = $fin.ToString('d') + ' de ' + (Get-Culture).DateTimeFormat.GetMonthName($fin.Month) + ' de ' + $fin.Year
```

Reemplaza en el template: `{{fecha_inicio}}` → `$fecha_inicio`, `{{fecha_fin}}` → `$fecha_fin`, `{{area_nombre}}` → nombre del área, `{{ejecutivo_firma}}` → valor de `firma`, `{{disclaimer}}` → valor de `disclaimer`.

Ruta de guardado:
```powershell
$dir = "data/mensajes/ejecutivos/$fecha/semana"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
```

El `whatsapp.txt`:
```
📅 *Oportunidades de la semana — [fecha_inicio] al [fecha_fin]*

[Por día:]
*[DÍA]*
• [Hora CLT] — [Evento] → Hablar de: [producto_relevante] con [tipo_cliente]
```

---

## FLUJO E — Mirror ejecutivo (`/ejecutivo mirror`)

Lee el directorio `data/mensajes/` buscando piezas del CLIENTE (excluye la subcarpeta `data/mensajes/ejecutivos/` para no espejar una pieza de ejecutivo previa). Busca la última pieza guardada del día de hoy (la más reciente por timestamp en el nombre de archivo).

Si no hay piezas del día de hoy: mostrar
```
⚠️ No hay piezas del cliente guardadas hoy todavía.
¿Quieres que genere el mirror de ayer? (s/n)
```

Con la pieza encontrada, lee su contenido. Determina el tipo (`{{tipo_pieza_cliente}}`): niveles / dato_macro / noticia / señal / concepto / etc.

Genera las 3 secciones:
- `{{resumen_cliente}}` → resumen en 3-4 líneas de qué información recibió el cliente. Lenguaje simple.
- `{{como_usarlo}}` → 2-3 sugerencias concretas de cómo el ejecutivo puede usar esa información en una conversación de hoy. Formato de lista `<ul><li>`.
- `{{que_hacer}}` → 2-3 acciones concretas: a quién llamar, qué decir, qué enviar. Formato de lista `<ul><li>`.

Lee el template `templates/ejecutivo/mirror.html`. Reemplaza todas las `{{variables}}`.

Ruta de guardado:
```powershell
$dir = "data/mensajes/ejecutivos/$fecha/mirror"
New-Item -ItemType Directory -Force -Path $dir | Out-Null
```

El `whatsapp.txt`:
```
🔁 *Habilitación del ejecutivo — [fecha_es]*
Pieza cliente: [tipo_pieza_cliente]

📌 Qué recibió el cliente:
[resumen en 2 líneas]

💬 Cómo usarlo:
• [sugerencia 1]
• [sugerencia 2]

✅ Qué hacer:
• [acción 1]
• [acción 2]
```

---

## REGLAS GENERALES (todos los flujos)

- Lenguaje: comercial, simple, en tuteo chileno neutro. NUNCA jerga técnica sin explicar.
- El HTML generado siempre es el contenido del template con `{{variables}}` reemplazadas — nunca inventar estructura HTML nueva.
- Al guardar: usar Write con la ruta completa. Crear el directorio antes si no existe (ver PowerShell en cada flujo).
- Siempre mostrar para aprobación antes de guardar. Al aprobar: guardar ambos archivos.
- Instrucción PDF siempre visible al mostrar para aprobación:
  `(Abre preview.html en Chrome → Ctrl+P → Guardar como PDF para distribuir al cliente)`
