# Stories en formato vertical (9:16) — diseño del Change fundacional

- **Fecha**: 2026-07-28
- **Dominio**: stories-gi
- **Estado**: diseño aprobado por el director, pendiente de plan de implementación
- **Origen**: el director pidió "la versión para celular" de las Stories. Formato elegido: vertical 9:16 (1080×1920). Alcance final: las 7 plantillas — pero repartido en 8 Changes.

---

## 1. Problema

Las Stories GI se producen solo en 16:9 (1920×1080). Ese formato se lee bien en escritorio y en presentaciones, pero llega comprimido a un teléfono, que es donde los ejecutivos consumen el contenido en el día a día.

El tamaño está **clavado en tres sitios a la vez**:

1. El viewport de `render_png`, fijo en `{"width": 1920, "height": 1080}`.
2. El CSS de cada snapshot: `html, body { width: 1920px; height: 1080px; }`.
3. Siete tests que afirman `_png_size(salida) == (1920, 1080)`.

Además, (1) y (2) son una **duplicación**: si divergen, el render se corta o deja franja, y nada lo detecta.

## 2. Descomposición: por qué esto son 7 Changes

Siete plantillas × un formato nuevo no cabe en un solo Change. El repo ya resolvió un caso idéntico: la **Fase A (#119)** generalizó el motor a 16:9 migrando **una sola plantilla validadora** (`alerta.html`), y recién después llegaron las demás. La regla vigente del dominio es **"una plantilla = un Change"**.

- **Change 0 (este)**: motor parametrizado + `postventa.html` como validadora.
- **Changes 1-6**: las 6 plantillas públicas, una por Change.

`postventa` es la validadora porque es la pieza que los ejecutivos leen en el teléfono mientras atienden clientes: es donde el formato móvil rinde más, y su layout de dos columnas es el caso más exigente de adaptar.

## 3. Arquitectura: un snapshot, dos formatos

**Decisión del director**: cada plantilla sigue siendo **un solo archivo** con media queries por `aspect-ratio`, en vez de un snapshot horizontal y otro vertical.

Razón: con dos archivos, cada cambio de copy o de marca hay que replicarlo, y ahí es donde nacen los desfases — la versión vertical se queda atrás y termina diciendo algo distinto que la horizontal. Con un archivo, el contenido vive en un solo lugar y el desfase es imposible por construcción.

**Verificado empíricamente antes de aprobar el diseño** (prueba con Playwright sobre un HTML de concepto):

| Viewport | PNG resultante | Layout de columnas |
|---|---|---|
| 1920×1080 | 1920×1080 | lado a lado |
| 1080×1920 | 1080×1920 | apiladas |

El mismo archivo produjo ambos. El enfoque no es una apuesta.

## 4. El formato viaja por el CLI, no por el payload

`--formato horizontal|vertical` en el CLI; **nunca** una clave del payload.

El payload es el contrato de **contenido**; el formato es **presentación**. Si el formato viviera en el payload habría que duplicarlo para sacar las dos versiones — exactamente el desfase que la arquitectura de un solo snapshot busca evitar. Con esta separación, **el mismo payload rinde ambos formatos**, que es la propiedad que hace valer todo el diseño.

## 5. Cambios en el motor

```python
render_png(html, output_path, *, template_dir, viewport=(1920, 1080)) -> Path
render_story(payload, template_path, output_path, formato="horizontal") -> Path
```

- Mapa cerrado de formatos: `_FORMATOS = {"horizontal": (1920, 1080), "vertical": (1080, 1920)}`.
- Un formato desconocido lanza `StoryRenderError` nombrando los válidos, siguiendo el contrato de errores accionables ya vigente en el módulo (nunca traceback crudo).
- **El default es `horizontal`**: todo lo existente sigue funcionando sin tocarse. Esta es la propiedad que permite migrar las 6 plantillas restantes de a una, sin romper nada mientras tanto.
- `main()` gana `--formato`, con `horizontal` por defecto.

## 6. Cambios en el snapshot validador

En `templates/stories/postventa.html`:

- `html, body`: `width: 1920px; height: 1080px` → `width: 100vw; height: 100vh`. El snapshot **deja de declarar su tamaño**; la dimensión la manda el viewport. Con esto desaparece la duplicación descrita en §1.
- Bloque nuevo `@media (max-aspect-ratio: 1/1)` con las adaptaciones verticales:
  - `.pv-cuerpo` pasa de `grid-template-columns: 1fr 1fr` a `1fr`: las dos columnas se apilan, primero "Qué responder" y debajo "Qué NO prometer".
  - La franja de niveles **se mantiene en fila** (soporte · precio · resistencia caben en 1080 px), pero con `gap` menor y valores algo más chicos que en el ancho de 1920.
  - Las tipografías suben en bloque para seguir siendo legibles en un lienzo de 1080 de ancho y 1920 de alto: título, respuesta, ítems de lista y footer.
- El chip de INTERNO y el aviso ámbar de no-reenvío se conservan en ambos formatos: son guardrails, no decoración.

## 7. Tests

Los 7 tests que afirman `(1920, 1080)` **no se tocan**: siguen pasando gracias al default `horizontal`. Se agregan:

1. `postventa` en vertical produce un PNG de `(1080, 1920)`.
2. En vertical, las dos columnas quedan apiladas (la segunda por debajo de la primera).
3. En horizontal, siguen lado a lado (no hay regresión).
4. Un formato desconocido lanza `StoryRenderError` nombrando los válidos.
5. `build_html` sigue siendo independiente del formato: el mismo payload produce el mismo HTML, porque la diferencia es puramente CSS.

## 8. Qué NO entra (YAGNI)

- Las otras 6 plantillas: un Change cada una.
- Tamaños 1:1 y 4:5 del canvas: no se piden hoy.
- Elegir formato desde `/story`: llega cuando haya más de una plantilla migrada.
- Generar ambos formatos en una sola corrida: dos invocaciones del CLI resuelven el caso hoy.

## 9. Criterios de aceptación

1. `render_story(..., formato="vertical")` produce un PNG de exactamente 1080×1920.
2. `render_story(...)` sin `formato` sigue produciendo 1920×1080 (retrocompatible).
3. `--formato vertical` en el CLI produce el PNG vertical; sin el flag, horizontal.
4. Un formato inválido lanza `StoryRenderError` que nombra `horizontal` y `vertical`.
5. En el render vertical de `postventa`, las columnas están apiladas y todo el texto cabe sin recortarse.
6. En el render horizontal de `postventa`, el resultado es visualmente idéntico al actual.
7. El chip de INTERNO y el aviso ámbar aparecen en ambos formatos.
8. La suite completa sigue en verde, con los 7 tests de dimensiones originales intactos.

## 10. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| El cambio a `100vw/100vh` altera el render horizontal | Alto — regresión visual en la pieza ya aprobada | Criterio 6: comparación visual del horizontal antes/después, además del test de dimensiones |
| Texto que desborda en vertical | Medio | Criterio 5 verificado por inspección del PNG, no solo por dimensiones |
| Las otras 6 quedan a medio camino | Bajo | El default `horizontal` las mantiene intactas hasta que llegue su Change |
| Layouts muy divergentes vuelven el CSS difícil de leer | Medio | Un solo bloque `@media` por snapshot, agrupado al final y comentado |

## 11. Relación con documentos existentes

- `docs/design/stories-gi/2026-07-14-contenido-visual-gi-16-9-design.md` — spec madre (#118) y precedente de la Fase A.
- `docs/design/stories-gi/2026-07-28-plantilla-postventa-design.md` — la plantilla validadora de este Change.
