# Pieza diaria de Avisos: visión de los bancos contra nuestros datos

**Fecha:** 2026-09-28 · **Rama:** `feat/pieza-avisos-vision` (parte de `feat/linkedin-pipeline`, PR #241)
**Estado:** diseño aprobado por el director en conversación, sección por sección.

## 1. Objetivo

Producir **a diario, como imagen para el grupo de Avisos** (`01_macro_y_apertura`), los formatos
de la primera versión de LinkedIn que el director encontró útiles para clientes:

- **Visión** (martes a viernes): lo que dice un banco o analista al lado de lo que dicen nuestros
  datos del terminal, con nuestra lectura. Dos variantes:
  - `cita`: una frase textual o traducida de un experto.
  - `meta_precio`: una proyección de un banco (una meta o un rango) contra el precio de hoy, con
    el plazo de cada uno a la vista.
- **Agenda** (lunes): los datos de impacto alto de la semana, en hora de Chile.

**Criterio de éxito:** cada día hábil el reloj deja preparada la pieza del día; el director corre
`/avisos`, revisa la imagen y el pie, y la aprueba o la ajusta. Nada sale sin su aprobación. Una
pieza con una cifra sin respaldo, una cita vieja o datos de más de 2 horas no se rinde.

### Decisiones del director (2026-09-28)

| Pregunta | Decisión |
|---|---|
| Canal | Solo el grupo de Avisos |
| Formato por día | Lunes agenda; martes a viernes visión, si hay una fresca |
| Quién escribe | El reloj prepara los datos; el comando busca visiones, escribe y rinde |
| Plantilla | Una nueva, `vision`, con dos variantes; la agenda reutiliza `calendario` |

## 2. Flujo

```
10:30 NY  reloj_gi ──► pipeline_avisos.py --preparar
                         ├─ lunes      → payload de calendario (agenda de la semana)
                         └─ mar a vie  → payload de vision
                              elige la visión más fresca del registro (< 45 días)
                              que no haya salido a Avisos en 14 días,
                              y lee del terminal el activo de esa visión
                              sin visión fresca → sin pieza, con aviso

director  /avisos ─► si falta, busca y registra una visión (y vuelve a preparar)
                     escribe el texto: frase de la imagen + pie de WhatsApp
                     pipeline_avisos.py --rendir → PNG + pie.txt, con frenos
                     muestra al director → aprueba → enviar_whatsapp --grupo avisos
```

## 3. Componentes

### 3.1 `templates/stories/vision.html`

- Lienzo horizontal 1920×1080, renderizado por `scripts/story_render.py` como las demás plantillas.
- Colores solo por `var(--rol)` de `marca.css`. El cromo va en el acento de marca; solo el dato
  lleva color (la píldora de dirección con `--sube` / `--baja`).
- Estructura común: chip `VISIÓN · <ACTIVO>`, bloque "Lo que dicen los bancos", bloque "Lo que
  dicen nuestros datos" (precio, dirección y el mapa de niveles 🟢🟡🔴 armado por el script) y
  "Nuestra lectura" (una frase).
- Variante `cita`: la frase va grande, entre comillas, con firma (persona · institución · fuente,
  fecha). En `traduccion` se rotula "traducción nuestra".
- Variante `meta_precio`: dos columnas, "Meta del banco" (cifra de la cita y su plazo) y "Precio
  hoy" (cifra del terminal y la hora de lectura).
- La variante se resuelve con fences sobre el campo `variante` del payload, sin duplicar plantilla.
- Fixture: `tests/fixtures/stories/payloads/vision.json`, con las dos variantes.

### 3.2 `scripts/pipeline_avisos.py`

Módulo nuevo. **Reutiliza, no copia**, de `pipeline_linkedin`: `leer_activos`, `leer_curva`,
`leer_agenda`, `cargar_visiones`, `validar_vision`, `validar` (frenos de texto y cifras),
`mapa_niveles` y `formatear`.

- `--preparar`:
  - Decide el formato por el día de la semana en Santiago.
  - Lunes: arma el payload de `calendario` con los eventos de la semana y deja en
    `[[ESCRIBIR]]` el título, el subtítulo y el pie.
  - Martes a viernes: elige la visión (sección 3.3), lee su activo del terminal y arma el payload
    de `vision`. Deja en `[[ESCRIBIR]]` la lectura, el remate y el pie.
  - Escribe en `data/avisos/<fecha>_<hora>_<formato>/payload.json`.
- `--rendir <dir>`:
  - Aplica los frenos (sección 4).
  - Construye el payload de Story, rinde el PNG con `render_story` y escribe `pie.txt`.
- `--validar <dir>`: informa qué falta, sin escribir nada.

### 3.3 Elección de la visión

Entre las visiones del registro se eligen las que cumplen tres condiciones:
- tienen menos de `ANTIGUEDAD_MAX_DIAS` (45);
- no salieron a Avisos en los últimos 14 días;
- su activo está en el catálogo.

De esas, gana la más reciente. Si empatan en fecha, la que tiene la variante menos usada en la
semana. La variante sale del tipo de la visión: `parafrasis` con una cifra de proyección da
`meta_precio`; `textual` o `traduccion` da `cita`.

Se anota en `data/historial_suplementos.json` con `tipo: "vision"`, `canal`, `id` y `fecha`
**al preparar**, igual que los conceptos del suplemento: una tanda descartada gasta la ventana,
y ese error va hacia el lado seguro.

### 3.4 Comando `/avisos`

`.claude/commands/avisos.md`, expuesto a AGY en `agy_workflows.COMANDOS`. Sus pasos:
1. Localizar la tanda que dejó el reloj, o correr `--preparar` si no la hay.
2. Si no hay visión fresca, buscar una y registrarla, con el mismo procedimiento del PASO 2 de
   `/linkedin`, y volver a preparar.
3. Escribir el texto con la herramienta de edición del runner o con Python, nunca por PowerShell.
4. Rendir y mirar el PNG.
5. Mostrar la imagen y el pie al director.
6. Al aprobar, guardar el pie con `ruta_mensaje.ps1` y enviar.

### 3.5 Momento del reloj

En `config/agenda_mercado.json`, un momento `vision_avisos` a las **10:30 de Nueva York**, con
`clases: []` y un campo nuevo, `pieza: "avisos"`, que le indica a `reloj_gi` que corra
`pipeline_avisos.py --preparar` en vez de `pipeline_carrusel.py`.

- A las 10:30 la bolsa ya abrió y los índices tienen precio del día.
- Queda a 30 minutos del momento de las 10:00, fuera de la tolerancia de 20.
- **El canal no se escribe en el momento.** El invariante 4 del reloj prohíbe una lista de
  canales por momento, así que `pieza: "avisos"` se resuelve con el mismo resolver de alias que
  usa `enviar_whatsapp` (`avisos` en `config/whatsapp_grupos.json`). Un test verifica que ese
  alias resuelve a un grupo existente.

### 3.6 Días feriados

Si el lunes es feriado de la bolsa de Nueva York (`config/feriados_bolsa.json`), la agenda sale
el primer día hábil de esa semana y la visión se salta ese día. Un día feriado de martes a viernes
no produce pieza. El día hábil se decide con el mismo calendario de feriados que usa el escáner.

## 4. Frenos de `--rendir`

**Heredados de `pipeline_linkedin.validar`, llamados y no copiados:**
- Toda cifra con `$`, o a menos de 3% de un precio medido, sale del terminal, de la cita usada o
  de `cifras_citadas` con su motivo.
- La visión tiene fecha y URL, no es futura (con un día de margen) y tiene menos de 45 días, o fue
  aceptada con un motivo.
- Sin guion largo ni medio, sin voseo, sin marcadores sin completar.

**Nuevos:**
- **Frescura de 2 horas** (`FRESCURA_WHATSAPP_HORAS = 2`) en vez de 24. La imagen se publica el
  mismo día y lleva precio.
- **El pie repite la conclusión y la dirección de la imagen.** Se valida que el pie nombre la
  dirección de la píldora (alcista o bajista), que lleve el aviso de análisis informativo, y que
  cierre con uno de los cierres de `CIERRES_ALERTA` o `CIERRES_MACRO`, estable por pieza y día.
- **Todo nivel citado va dibujado.** El mapa de niveles lo arma el script a partir de las cifras
  medidas; el payload de Story lleva sus `niveles` con `clase`, `etiqueta` y `rol`.

## 5. Errores

| Caso | Comportamiento |
|---|---|
| MT5 no conecta | `--preparar` se detiene. El momento queda pendiente para el siguiente latido, porque solo se anota si alguna corrida terminó bien |
| Sin visión fresca (martes a viernes) | Sin pieza. Aviso con el motivo en la salida del reloj y en `/avisos`. No se rellena con otra cosa |
| Calendario caído (lunes) | Sin agenda, con aviso |
| Datos de más de 2 h al rendir | Se detiene y pide volver a preparar |
| Falla de envío | La verificación de entrega de `enviar_whatsapp` manda. Si aborta, no se envió: revisar el chat antes de reintentar |

## 6. Pruebas

- Contrato de Stories: `vision` tiene fixture y rinde sin tokens huérfanos; `marca_tokens --check`
  pasa.
- `pipeline_avisos`:
  - el formato según el día; un lunes feriado mueve la agenda al martes; un feriado de martes a
    viernes no produce pieza;
  - la elección de la visión (la más fresca, la exclusión por 14 días, y ninguna fresca da
    ninguna pieza);
  - frescura de 2 h a los 121 minutos;
  - el pie sin dirección, sin aviso o sin cierre se detiene.
- Reloj:
  - el momento nuevo no cae dentro de la tolerancia de ningún otro, en las tres configuraciones
    de desfase del año;
  - `pieza: "avisos"` despacha a `pipeline_avisos --preparar`;
  - el test de que el reloj nunca envía sigue verde.
- `/avisos` documenta los formatos que existen en el código; `agy_workflows --check` pasa.
- Prueba real contra el terminal: preparar, escribir, rendir y mirar el PNG, sin enviar.

## 7. Fuera de esta etapa

- Los canales temáticos. Por ahora la pieza va solo a Avisos.
- La búsqueda automática de visiones. La hace el comando, no el reloj.
- El formato "problema → solución" como imagen. Su gancho y su llamada a la acción eran para
  captar desde LinkedIn y no aplican a un grupo de clientes.
