## PASO 1 — Obtener Datos del Motor (OBLIGATORIO)
Siempre debes consultar los precios reales y niveles técnicos antes de armar la oportunidad.
1. Utiliza el MCP `market-data` (ej. herramienta `get_asset_levels` o similar, según esté disponible en el MCP) pasando el ticker del activo (ej. `#MELI`, `USDCLP`).
2. Usa la temporalidad `H1` y los niveles devueltos (precio actual, soporte, resistencia) para establecer el "precio ahora" y el "objetivo" o "recorrido" en el gráfico.
3. Si el MCP devuelve los niveles dibujados por el usuario (líneas horizontales), úsalos para definir el objetivo de la oportunidad y el sesgo.
4. **GUARDRAIL CRÍTICO**: NUNCA inventes, simules ni deduzcas precios o niveles si la conexión a MT5 falla o el MCP devuelve error. Si no puedes obtener el dato real, DEBES DETENERTE y pedirle al usuario que revise la conexión. Las proyecciones siempre deben salir matemáticamente del precio actual real.
5. **Filtro y distancia mínima al objetivo, combinando ADX + ATR restante (OBLIGATORIO)**: pide `get_asset_levels` con `timeframe: D1` y lee `adx_14` y `atr_restante_14` **de esa llamada en D1, nunca de la llamada en H1/H4 del paso 2** (`adx_14` viene en la respuesta de cualquier timeframe, pero para este filtro solo cuenta el de D1; usar el de H1 subestima la tendencia real del activo). El ATR por sí solo dice qué tan grande es un movimiento normal en el día completo, pero no si hay convicción direccional detrás (eso lo da el ADX) ni cuánto de ese movimiento ya ocurrió hoy (eso lo da el ATR restante: `atr_14 - rango_hoy`, con piso del 30% de `atr_14` para que una tarde volátil no bloquee toda pieza el resto del día — ver `atr_restante_14`, ya calculado por la tool). Se combinan así:
   - **Gate de entrada**: si `adx_14` (D1) < 20, el activo **no es candidato** a `oportunidad` ese día. ADX bajo 20 es mercado en rango, sin tendencia real, sin importar qué tan lejos esté una resistencia.
   - **Distancia mínima escalada**: la distancia entre `precio` y `objetivo` debe ser ≥ N × `atr_restante_14`, donde N depende de la fuerza de la tendencia:

     | `adx_14` (D1) | N (múltiplo del ATR restante) |
     |---|---|
     | 20-25 (tendencia emergente) | 1× |
     | 25-40 (tendencia confirmada) | 1,5× |
     | > 40 (tendencia muy fuerte) | 2× |

   Si la resistencia/soporte más cercana en H1 o H4 no alcanza la distancia exigida por su N, sube de marco (H4 → D1) hasta encontrar un nivel real que sí la cumpla; nunca inventes un precio a medida. Si ningún nivel real del motor alcanza la distancia mínima, el activo no es candidato a `oportunidad` ese día.

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
| `razon` | Por qué se mueve, en voz llana. **Máximo 2 frases**: el lienzo es fijo (`overflow: hidden`) y un `razon` largo empuja el CTA y el disclaimer fuera del margen inferior. Nunca repetir ahí lo que ya dice `nota_nivel` (qué nivel hay que romper primero) |
| `precio` · `objetivo` · `objetivo_rotulo` · `nota_nivel` | Precio de ahora, hacia dónde va y qué tiene que romper primero. El rótulo canónico es **"Escenario"** (decisión del director, 2026-08-19): reemplaza al antiguo "Hacia dónde va", porque el número de la derecha es un escenario condicionado a que se rompa `nota_nivel`, y un rótulo que afirma el destino se lee como promesa de precio |
| `dato_rotulo` · `dato_lectura` · `dato_detalle` | La LECTURA arriba ("Menos empleos en EE.UU.") y la cifra abajo como prueba. El número solo no le sirve a nadie. |
| `dato_veredicto` · `dato_veredicto_slug` | El texto ("Peor de lo esperado") y su slug `mejor` / `peor` / `en-linea`, que le da el color al chip |
| `cta` · `cta_sub` | El llamado a la acción de la imagen |
| `recorrido` | `{serie, marcadores, "ajuste": "llenar"}` — lo arma `serie_mt5.py`; el `ajuste` es lo que hace que el gráfico llene el lienzo como escenario |

**Si el activo no tiene su imagen** en `templates/stories/assets/activos/`, generarla con el
recetario de `docs/design/stories-gi/imagenes-por-activo.md`. Y si no tiene color propio en
`marca.css` (`--activo-<slug>`), la pieza cae al acento de marca sin romperse.

**El veredicto del dato no sigue la dirección del activo.** Son dos cosas distintas y ambas ciertas
a la vez: un dato peor de lo esperado en EE.UU. puede impulsar al Oro hacia arriba, así que la
píldora del activo dice SUBIENDO en verde y el chip del dato dice PEOR DE LO ESPERADO en rojo. Por
eso `dato_veredicto_slug` va aparte de `sesgo`: mejor/peor es contra el consenso, no una dirección
de mercado.

⚠️ **Límite editorial**: la pieza invita a operar pero **no lleva entrada, TP, SL ni volumen**. Eso
la convertiría en una señal, que exige firma acreditada y cuenta para el límite de 3 por semana —
para eso está `/señal` o la plantilla `recomendacion`. Hay un test que falla si esas palabras
aparecen en la plantilla.

## Instrucciones para Guardar Archivos
- **La Imagen**: en `data/stories/[YYYY-MM-DD]/[activo]/oportunidad/[HH-MM]_oportunidad.png`, con la ruta construida por `scripts/ruta_story.ps1` (nunca a mano).
- **El Texto**: el mensaje estructurado para WhatsApp se guarda **siempre** como `.txt` en la misma carpeta y con el mismo nombre que el PNG: `data/stories/[YYYY-MM-DD]/[activo]/oportunidad/[HH-MM]_oportunidad.txt`. No es opcional ni depende de que el director lo pida: **imagen y texto salen juntos en la misma corrida**, porque un adjunto sin pie llega mudo al grupo y el texto suelto pierde la pieza. Si solo se guarda el PNG, la oportunidad está incompleta.
- Limitar a 3 documentos de calidad al día (verificar límite en historial).
