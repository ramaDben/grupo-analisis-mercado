# Plantilla de Story "Post-Venta" — diseño

- **Fecha**: 2026-07-28
- **Dominio**: stories-gi (Fase C — plantillas con listas)
- **Estado**: diseño aprobado por el director, pendiente de plan de implementación
- **Origen**: al generar la Story de post-venta con la plantilla `edu` aparecieron tres problemas concretos; el director pidió una plantilla propia que los resuelva.

---

## 1. Problema

El parte de post-venta (`/postventa`, PR #143) se llevó a imagen reusando `templates/stories/edu.html`. El render funcionó, pero dejó tres defectos:

1. **Footer público en una pieza interna.** `edu.html` cierra con `@grupointeligencia`, `grupointeligencia.com` y el disclaimer de CFD — texto dirigido a clientes. La pieza *parece* publicable aunque diga INTERNO arriba, y una imagen se reenvía mucho más fácil que un texto con banner.
2. **Verde decorativo donde el color debería ser semántico.** En la paleta GI el verde `#00DC82` significa alcista y el rojo `#E84040` bajista. `edu` pinta de verde los dos recuadros del ejemplo comparativo, así que soporte y resistencia salieron del mismo color cuando deberían leerse opuestos.
3. **Techo de cuatro puntos.** El bloque de aplicación de `edu` está pensado para 2-4 bullets. El parte de post-venta necesita más: las respuestas frecuentes y, por separado, los límites de lo que no se promete.

`edu` no está mal — está diseñada para un concepto educativo, no para un guion operativo interno.

## 2. Qué se construye

Un snapshot de marca nuevo, `templates/stories/postventa.html`, más su tipo en `/story`.

Se sigue la regla del repo **una plantilla = un snapshot** (no se parametriza `edu` con variantes). El motor `scripts/story_render.py` **no se modifica**: ya soporta varios bloques `<!-- FOR -->` por archivo (el patrón ancla FOR/ENDFOR con backreference por clave) y ya deriva `sesgo_slug` desde la clave `sesgo` del payload.

## 3. Estructura visual

Cinco zonas, de arriba a abajo, en 1920×1080:

| Zona | Contenido | Origen |
|---|---|---|
| Chip superior | `🔒 INTERNO · POST-VENTA` | **literal en el HTML, sin token** |
| Fecha | fecha y hora Chile | `{{fecha_hora}}` |
| Consulta | la pregunta del día y su respuesta | `{{consulta}}`, `{{respuesta}}` |
| Franja de niveles | soporte · activo con precio y sesgo · resistencia | `{{soporte}}`, `{{activo_nombre}}`, `{{precio}}`, `{{sesgo}}`, `{{resistencia}}` |
| Dos columnas | ✅ Qué responder / ⚠️ Qué NO prometer | `<!-- FOR:respuestas -->`, `<!-- FOR:no_promesas -->` |
| Footer | uso interno + fuente | `{{fuente}}` |

**El chip de INTERNO va escrito en el HTML, no como token.** Si fuera `{{kicker}}`, un payload podría dejarlo vacío y la pieza saldría indistinguible de una publicable. Fijándolo en el snapshot, no existe forma de generar esta plantilla sin la marca de interno. Es el guardrail central del diseño.

Los rótulos de columna (`✅ QUÉ RESPONDER`, `⚠️ QUÉ NO PROMETER`) viven **fuera** de las marcas `FOR`/`ENDFOR`, siguiendo la convención de Fase C, para que persistan si una lista llega vacía.

## 4. Color semántico

Se reutiliza el patrón ya resuelto en `templates/stories/resumen.html`:

- `soporte` → verde `#00DC82` · `resistencia` → rojo `#E84040`. Fijos por CSS: son roles, no dato variable.
- `sesgo` → clase `pv-sesgo--{{sesgo_slug}}` con `--alcista` (verde, ▲), `--bajista` (rojo, ▼), `--lateral` (gris `#A9A5B4`, →). La flecha se inyecta por CSS `::before`, no por texto del payload.
- `sesgo_slug` lo deriva el motor desde la clave `sesgo` (helper 2 del catálogo). Cero código nuevo.
- Acento estructural: teal `#3E91AF` para chip y rótulos — en la paleta GI no compite con el par verde/rojo.

Regla: **ningún verde decorativo**. El color aparece solo donde significa algo.

Fondo y familia tipográfica heredados del resto de los snapshots: DM Sans 400/700, Space Grotesk 600; fondo `#0D0D1A`, texto `#F5F3F7`.

**Excepción deliberada — el título no usa Syne 800.** Es la única plantilla del catálogo que se aparta en esto. Syne es ancho por diseño (no hay estiramiento: cero `scaleX`, cero `font-stretch`), y a tamaño de titular esa anchura se lee como grito en una pieza cuyo trabajo es que un ejecutivo lea rápido bajo presión. Como ésta es la **única pieza interna** — no representa a GI ante ningún cliente — la legibilidad operativa pesa más que la consistencia de marca. Se usa **Space Grotesk 600**, que además ya es la fuente dominante del snapshot (chip, fecha, rótulos y precios): el título pasa a hablar el mismo idioma que los datos, en vez de ser el único elemento en otra familia. Sigue dentro del kit GI, sin sumar archivos ni licencias.

## 5. Footer interno

Reemplaza al footer público. Sale el handle, sale el dominio, sale el disclaimer de CFD (es texto para clientes; no aplica a una pieza interna y su presencia es justamente lo que la hace parecer publicable).

Queda: `⚠️ USO INTERNO · NO REENVIAR AL CLIENTE` a la izquierda y `Fuente: {{fuente}}` a la derecha.

**El aviso de no-reenvío no es una nota al pie, es una regla de compliance**, y se pinta como tal: ámbar `#FFB020` a 19px sobre fondo tenue con borde, **10,54:1** de contraste. La primera versión lo puso en el gris apagado `#6E6A7A` del resto del footer — **3,68:1**, por debajo del mínimo WCAG AA de 4,5:1 — lo que contradecía la propia mitigación del riesgo "se reenvía igual" (§10): un ejecutivo apurado podía no verlo antes de sacar un pantallazo. El dato de fuente sí queda en gris apagado: es metadato, no compliance.

Con esto la pieza lleva **doble marca de interno**: el chip teal arriba y el aviso ámbar abajo.

## 6. Contrato de datos

```json
{
  "plantilla": "postventa",
  "fecha_hora": "28 JUL 2026 · 19:23",
  "consulta": "¿Me afecta que no bajen la tasa?",
  "respuesta": "No, ya estaba en el precio. Mañana manda la Fed.",
  "activo_nombre": "USD/CLP",
  "soporte": "$923.90",
  "precio": "$930.50",
  "resistencia": "$930.80",
  "sesgo": "Bajista",
  "respuestas": [
    { "texto": "¿Cierro? → Depende del plazo, no del dato de hoy" }
  ],
  "no_promesas": [
    { "texto": "Que el dólar siga bajando: mañana define la Fed" }
  ],
  "fuente": "MT5 · GRUPO INTELIGENCIA"
}
```

Límites editoriales (guía de redacción del comando — el motor no valida longitud ni trunca): `fecha_hora` ≤ 28 · `consulta` ≤ 60 · `respuesta` ≤ 90 · `activo_nombre` ≤ 14 · `soporte`/`precio`/`resistencia` ≤ 12 cada uno · `sesgo` ≤ 10 · cada `respuestas[].texto` ≤ 62 (4 a 6 entradas) · cada `no_promesas[].texto` ≤ 62 (2 a 3 entradas) · `fuente` ≤ 30.

Precios formateados con los `digits` de `config/activos.json`.

## 7. Integración

- **`/story`**: se agrega `postventa` a los tipos soportados, con su propia ruta de recolección. Sigue el patrón de **atajo opcional** ya usado por `breaking`, `encuesta` y `edu` — la ruta abre preguntando:
  ```
  ¿Ya corriste /postventa hoy? Si sí, reuso la consulta, los niveles y los puntos
  de ese parte. Si no, dime el activo y los recolecto del motor.
  ```
  - **Con parte previo** → reusa consulta, respuesta, niveles y puntos ya redactados; no vuelve a llamar a `get_asset_levels`.
  - **En frío** → pide el activo (normalizado contra `config/activos.json`, mismo criterio que `/chart` PASO 1) y toma precio/soporte/resistencia de `get_asset_levels` con `timeframe: "H1"`, igual que `alerta`; si retorna `{"error": ...}`, los pide manualmente.

  El atajo no bloquea ni exige corrida previa.
- **`/postventa`**: al final de su PASO 8 (tras guardar el parte), ofrece generar la Story pasando los datos que ya tiene en memoria. Es un ofrecimiento, no un paso obligatorio.
- **Guardado**: `scripts\ruta_story.ps1 -Activo [TICKER] -Plantilla "postventa"` → `data/stories/<fecha>/<activo>/postventa/<hora>_postventa.png`. Lleva activo protagonista (a diferencia de `edu`, que va a `_general`).

## 8. Qué NO hace (YAGNI)

- No embebe gráfico de MT5 — Fase D sigue bloqueada por el issue #87.
- No consume datos de mercado por su cuenta cuando viene encadenada desde `/postventa`.
- No se sube al canvas de Rodrigo salvo pedido explícito del director.
- No reemplaza a `edu`: son piezas distintas y ambas quedan.

## 9. Criterios de aceptación

1. El chip `🔒 INTERNO · POST-VENTA` aparece en el render sin estar en el payload, y no hay forma de suprimirlo desde el JSON.
2. `soporte` se pinta verde y `resistencia` roja en el mismo render.
3. `sesgo: "Bajista"` produce texto rojo con ▼; `"Alcista"` verde con ▲; `"Lateral"` gris con →.
4. Las dos listas expanden N elementos cada una, de forma independiente.
5. Con `respuestas: []` o `no_promesas: []`, la columna colapsa sin dejar marcas `FOR`/`ENDFOR` y su rótulo persiste.
6. El footer no contiene `@grupointeligencia`, ni `grupointeligencia.com`, ni el disclaimer de CFD.
7. El render produce un PNG 1920×1080 sin lanzar `StoryRenderError` por tokens huérfanos.
8. `/story postventa` genera y guarda en `data/stories/<fecha>/<activo>/postventa/`.

## 10. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| La pieza interna se reenvía a un cliente igual | Alto | Chip fijo no suprimible + footer explícito "NO REENVIAR" + carpeta `postventa/` separada |
| Las dos columnas se desbalancean (6 vs 2 puntos) | Bajo | Columnas de alto independiente, alineadas arriba; el desbalance es visualmente aceptable |
| Los precios envejecen en la imagen | Medio | `fecha_hora` visible en el encabezado deja claro a qué momento corresponde |
| Divergencia con el canvas de Rodrigo | Bajo | Se hereda el andamiaje verbatim de los snapshots existentes (fuentes, fondo, paleta) |

## 11. Relación con documentos existentes

- `docs/design/hub-interno/2026-07-28-parte-postventa-design.md` — el comando que produce el contenido de esta Story.
- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — spec madre de Stories GI 16:9 (#118).
- `templates/stories/resumen.html` — origen del patrón de color semántico reutilizado aquí.
