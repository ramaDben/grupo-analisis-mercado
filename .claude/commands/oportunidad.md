## PASO 1 — Obtener Datos del Motor (OBLIGATORIO)
Siempre debes consultar los precios reales y niveles técnicos antes de armar la oportunidad.
1. Utiliza el MCP `market-data` (ej. herramienta `get_asset_levels` o similar, según esté disponible en el MCP) pasando el ticker del activo (ej. `#MELI`, `USDCLP`).
2. Usa la temporalidad `H1` y los niveles devueltos (precio actual, soporte, resistencia) para establecer el "precio ahora" y el "objetivo" o "recorrido" en el gráfico.
3. Si el MCP devuelve los niveles dibujados por el usuario (líneas horizontales), úsalos para definir el objetivo de la oportunidad y el sesgo.
4. **GUARDRAIL CRÍTICO**: NUNCA inventes, simules ni deduzcas precios o niveles si la conexión a MT5 falla o el MCP devuelve error. Si no puedes obtener el dato real, DEBES DETENERTE y pedirle al usuario que revise la conexión. Las proyecciones siempre deben salir matemáticamente del precio actual real.

## Estructura del Mensaje (Texto para WhatsApp)

El texto debe seguir estrictamente esta estructura, con un tono profesional, orientado a la acción comercial, pero sin ser una recomendación directa de inversión:

1. **¿Qué está pasando y por qué es relevante? (Contexto y Fundamental)**
   (Ej. "Mercado Libre (MELI) continúa consolidándose... Diversos analistas del mercado mantienen una visión positiva...")
2. **¿Qué vemos en el gráfico? (Análisis técnico — OPCIONAL)**
   (No es estrictamente necesario, úsalo solo si aporta valor claro, ya que la imagen ya incluye los niveles y puede ser confuso).
3. **¿Cómo puede acceder el cliente? (Llamado a la acción comercial)**
   Debe estar orientado tanto a ejecutivos (prospección) como analistas (postventa). SIEMPRE debe invitar a una reunión.
   (Ej. "Si deseas conocer cómo acceder a esta acción y revisar si se ajusta a tu perfil de inversión, contáctanos. En Grupo Inteligencia contamos con este instrumento disponible para nuestros clientes. ¿Generemos una reunión para revisar en detalle esta acción?")
4. **Fuente de la información**
   (Debe incluirse la fuente de los datos/noticia).
5. **Disclaimer de riesgo**
   "Este contenido es informativo y no constituye una recomendación personalizada de inversión. Toda inversión conlleva riesgos y el rendimiento pasado no garantiza resultados futuros."

## La Imagen — plantilla `oportunidad`

La pieza se rinde con `templates/stories/oportunidad.html`, el snapshot de marca de esta
plantilla. Diseño completo y decisiones en
`docs/superpowers/specs/2026-08-04-rediseno-stories-gi-design.md`; acá va lo que hay que saber
para generarla.

**Pipeline de tres pasos** — la serie de precios pasa por dos scripts antes del render:

```bash
uv run --with MetaTrader5 python scripts/serie_mt5.py --ticker [TICKER] --timeframe H1 --velas 72 \
  | uv run python scripts/story_grafico.py \
  | uv run --extra stories python scripts/story_render.py \
      --template templates/stories/oportunidad.html \
      --formato horizontal \
      --out "[ruta de ruta_story.ps1]"
```

`--formato vertical` produce la versión 9:16 para el estado de WhatsApp desde el **mismo payload**:
el formato viaja por el CLI y nunca por el payload.

**Campos del payload** (los precios con los `digits` de `config/activos.json`, coma decimal y punto
de miles):

El payload tiene que traer **todos** estos campos: si falta uno, el motor aborta con "tokens
huérfanos" en vez de rendir una pieza incompleta.

| Campo | Qué lleva |
|---|---|
| `sello` · `fecha_hora` | "MOTOR GI · ANÁLISIS EN VIVO" y la fecha/hora en hora Chile |
| `activo_nombre` · `activo_ticker` · `activo_slug` | "ORO", "XAU/USD", "oro" |
| `activo_imagen` · `modo_imagen` | `assets/activos/<slug>.jpg` y `foto-activo` (franja) o `ilustracion` (objeto recortado) |
| `sesgo` · `direccion_etiqueta` | `Alcista`/`Bajista`/`Lateral` y su etiqueta visible ("SUBIENDO") |
| `titular` | Nombra un **precio del motor**, no una figura técnica: "El oro sube y busca los 4.100", nunca "va por sus máximos". Sin jerga. |
| `razon` | Por qué se mueve, en voz llana |
| `precio` · `objetivo` · `objetivo_rotulo` · `nota_nivel` | Precio de ahora, hacia dónde va (con su rótulo, ej. "Hacia dónde va") y qué tiene que romper primero |
| `dato_rotulo` · `dato_lectura` · `dato_detalle` · `dato_veredicto` | La LECTURA arriba ("Menos empleos en EE.UU.") y la cifra abajo como prueba. El número solo no le sirve a nadie. |
| `cta` · `cta_sub` | El llamado a la acción de la imagen |
| `recorrido` | `{serie, marcadores, "ajuste": "llenar"}` — lo arma `serie_mt5.py`; el `ajuste` es lo que hace que el gráfico llene el lienzo como escenario |

**Si el activo no tiene su imagen** en `templates/stories/assets/activos/`, generarla con el
recetario de `docs/design/stories-gi/imagenes-por-activo.md`. Y si no tiene color propio en
`marca.css` (`--activo-<slug>`), la pieza cae al acento de marca sin romperse.

⚠️ **Límite editorial**: la pieza invita a operar pero **no lleva entrada, TP, SL ni volumen**. Eso
la convertiría en una señal, que exige firma acreditada y cuenta para el límite de 3 por semana —
para eso está `/señal` o la plantilla `recomendacion`. Hay un test que falla si esas palabras
aparecen en la plantilla.

## Instrucciones para Guardar Archivos
- **La Imagen**: en `data/stories/[YYYY-MM-DD]/[activo]/oportunidad/[HH-MM]_oportunidad.png`, con la ruta construida por `scripts/ruta_story.ps1` (nunca a mano).
- **El Texto**: el mensaje estructurado para WhatsApp se guarda obligatoriamente como `.txt` en la misma carpeta: `data/stories/[YYYY-MM-DD]/[activo]/oportunidad/[HH-MM]_oportunidad.txt`.
- Limitar a 3 documentos de calidad al día (verificar límite en historial).
