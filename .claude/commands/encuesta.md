Genera una encuesta de sentimiento para el grupo de WhatsApp.

## Argumentos
$ARGUMENTS — formato esperado: `[tipo] [activo? | scope?]`

Tipos disponibles (sentimiento puro — sin precios, sin contenido educativo):
- `posicion [activo?]` — qué está operando el grupo (compré / vendí / no operé)
- `tendencia [activo?]` — qué tendencia proyectan para el día (alcista / bajista / lateral)
- `movimiento [semana?]` — qué activo tendrá más movimiento (hoy, o "semana" para la encuesta dominical)

Ejemplos:
- `posicion` (un poll por cada activo del día)
- `posicion USDCLP`
- `tendencia Oro`
- `movimiento`
- `movimiento semana`

> Si NO se entrega tipo, no asumir nada: preguntar al director cuál de los 3 quiere.

---

## REGLAS DURAS (todos los tipos)

> 1. **CERO precios y cero números.** Ningún poll menciona precios, niveles, datos macro
>    numéricos ni porcentajes. Si vas a escribir un número, detente.
> 2. **CERO contenido educativo.** No explicar conceptos, no causa-efecto, no "respuesta
>    correcta". Eso vive en la futura área educativa con comandos propios.
> 3. **Una invocación = una sola pieza del tipo pedido.** Nunca arrastrar otros tipos.
> 4. La contextualización la da el contexto macro que el carrusel publica en el canal esa mañana,
>    NO la encuesta. El poll solo hace un guiño cualitativo opcional, sin números.
> 5. Límites WhatsApp: pregunta ≤ 255 caracteres — cada opción ≤ 100 caracteres (emoji incluido) — 2 a 12 opciones.

---

## PASO 1 — Parsear argumentos

**Tipo**: uno de `posicion`, `tendencia`, `movimiento`.
- Si `$ARGUMENTS` viene **sin tipo** → preguntar al director: "¿Qué encuesta generas: posicion, tendencia o movimiento?". No continuar hasta tener tipo.

**Segundo argumento**:
- Para `posicion` / `tendencia`: es el **activo** (opcional). Normalizar a nombre legible:
  - USDCLP / USD/CLP → "USD/CLP (Dólar)"
  - XAUUSD / Oro / XAU/USD → "Oro (XAU/USD)"
  - WTI → "WTI (Petróleo)"
  - US100 → "Nasdaq 100 (US100)"
  - US500 → "S&P 500 (US500)" · US30 → "Dow Jones (US30)"
  - #AAPL / AAPL → "Apple (#AAPL)" · (resto de acciones análogo)
- Para `movimiento`: el segundo argumento solo puede ser `semana` (scope semanal). Cualquier otra cosa → scope diario.

---

## PASO 2 — Resolver los activos (desde `data/plan_hoy.json`)

Leer `data/plan_hoy.json`.

**Validar frescura**: comparar `plan_hoy.fecha` con la fecha de hoy.
- Si **no coincide** o el archivo **no existe** → avisar al director: "El plan del día (`plan_hoy.json`) está desfasado (fecha: [fecha], hoy: [hoy]). ¿Qué activos uso?" y pedir los activos manualmente. No generar polls con activos viejos.
- Si coincide → usar `activos_hoy`.

**Resolución por tipo**:
- `posicion` / `tendencia`:
  - **Con activo** → generar **un solo** poll de ese activo.
  - **Sin activo** → generar **un poll por cada** activo de `activos_hoy` (solo de ese tipo).
- `movimiento`:
  - Scope **diario** → opciones = los activos de `activos_hoy`.
    - Si `activos_hoy` tiene **menos de 2** → no se puede crear poll WhatsApp; avisar y pedir activos manualmente.
    - Si tiene **más de 12** (improbable) → tomar 12 priorizando por catalizadores del día.
  - Scope **semana** → opciones fijas: 🇨🇱 USD/CLP · 🥇 Oro · ⛽ WTI (Petróleo) · 📱 US100 (Nasdaq).

---

## PASO 3 — Contexto cualitativo opcional (sin números)

Leer `data/ultimo_evento.json`.

**Validar frescura**: usar solo si su `timestamp` es de hoy. Si está desfasado o ausente → omitir priorización y guiño (poll seco).

Si hay evento fresco:
- **Priorizar orden**: en `posicion`/`tendencia` sin activo, y en `movimiento`, poner primero el activo que coincide con `ultimo_evento.activo`.
- **Guiño**: rellenar `{{guino}}` con UNA frase fija (elegir según `ultimo_evento.tipo`):
  - `Con el dato de hoy ☝️, ¿cuál es tu jugada?`
  - `Tras la noticia de hoy ☝️, ¿qué proyectas?`

**Prohibido**: volcar `dato_real`, `dato_esperado`, precios o cualquier número al poll. Prohibido inventar frases nuevas que insinúen dirección de mercado. Si no hay evento fresco, omitir la línea `{{guino}}` por completo.

---

## PASO 4 — Generar el/los poll(s)

Usar la plantilla del tipo:
- `posicion` → `templates/encuesta_posicion.txt` (rellenar `{{activo}}`, `{{guino}}`).
- `tendencia` → `templates/encuesta_tendencia.txt` (rellenar `{{activo}}`, `{{guino}}`).
- `movimiento` → `templates/encuesta_movimiento.txt` (rellenar `{{titulo}}`, `{{periodo}}`, `{{opciones}}`).

Si se generan **varios polls** (`posicion`/`tendencia` sin activo): mostrarlos todos, separados por `━━━━━━━━━━━━━━━━━━━`.

Verificar antes de mostrar: ningún número de precio, cada opción ≤ 100 chars, pregunta ≤ 255 chars.

---

## PASO 5 — Aprobación y guardado

Presentar el/los poll(s) al director. Preguntar: "¿Apruebas? ¿Enviar al grupo WhatsApp?"

Al aprobar:
- Guardar en **un único** archivo cuya ruta da `scripts\ruta_mensaje.ps1 -Fecha [FECHA] -Activo [TICKER_MT5 o omitir si es transversal] -Tipo encuesta -Hora [HH-MM]` (si son varios polls, separados por `━━━━━━━━━━━━━━━━━━━`).
- Registrar en `data/historial_encuestas.json` **un objeto por poll** (cada activo es su propia encuesta nativa de WhatsApp), con este esquema:

```json
{
  "id": "[YYYY-MM-DD]_[tipo]_[TICKER]",
  "fecha": "[YYYY-MM-DD]",
  "tipo": "[posicion|tendencia|movimiento]",
  "activo": "[TICKER]",
  "pregunta": "[texto de la pregunta]",
  "opciones": ["...", "...", "..."],
  "contexto_ref": "[nombre del evento que contextualizó, SIN números, o null]",
  "estado": "registrada"
}
```

Para `movimiento`, usar `"activos": ["...", "..."]` en vez de `"activo"`.

> Nunca `respuesta_correcta` ni `pendiente_revelacion` en estos tipos. Estado siempre `registrada`.
- Si el MCP de WhatsApp está disponible: enviar. Si no: mostrar texto listo para copiar.

---

## Modo ejecutivo (flag `ejecutivo`)

Si `ejecutivo` aparece en `$ARGUMENTS`, además de cada poll de cliente genera su **guion de venta interno** siguiendo `.claude/shared/modo_ejecutivo.md` (formato, banner `🔒 INTERNO · NO ENVIAR AL CLIENTE`, flujo de aprobación y guardrails). El guion engancha a los ejecutivos a empujar la participación del grupo (votar como excusa de contacto). Por cada poll:
- **Tipo de guion**: `guion_encuesta`.
- **`-Activo`**: el ticker del poll (en `movimiento`/scope semanal transversal, omitir → `_general`). Un guion por poll.
- Mismo `-Hora` que el poll.

Muestra ambas salidas rotuladas `📤 MENSAJE CLIENTE` y `🔒 GUION EJECUTIVO`; al aprobar, guarda el guion con `scripts\ruta_mensaje.ps1`.

## REGLAS
- Tipo obligatorio: sin tipo, preguntar.
- Sin precios, sin números, sin educación. Nunca.
- `posicion`/`tendencia` sin activo recorren `activos_hoy`; con activo, uno solo.
- `movimiento` = una sola pieza.
- `plan_hoy.json` o `ultimo_evento.json` desfasados → manejar como se indica (pedir manual / poll seco).
- Hora en hora Chile si mencionas algún horario.
