# Propuesta: producción diaria con escaneo del universo

Material para presentarle a Hari el sistema de tandas diarias. **No es una pieza de
cliente**: es un documento interno de propuesta, y su público es el equipo.

## Qué hay acá

| Archivo | Qué es |
|---|---|
| `propuesta.md` | Fuente del documento. Se edita acá y se recompila |
| `Produccion Diaria GI - Propuesta.pdf` | El documento, 5 páginas A4 |
| `correo-hari-propuesta.txt` | El correo con el que va, con los 7 adjuntos listados |
| `generar_piezas.py` | Arma los payloads de las 6 piezas de activo, una por clase |
| `generar_pieza_macro.py` | Arma la pieza `calendario` de la séptima clase |

## Cómo se regenera

```bash
# 1. Refrescar los datos macro (sin esto el informe no se emite)
uv run --with requests --with tenacity --with python-dotenv --with yfinance \
  python ".agents/skills/ecosistema-datos-macro/scripts/pipeline_ingesta.py"

# 2. Payloads de las 6 piezas de activo + los eventos del día
uv run --with MetaTrader5 python docs/propuesta-produccion-diaria/generar_piezas.py

# 3. Payload de la pieza macro
uv run python docs/propuesta-produccion-diaria/generar_pieza_macro.py

# 4. Escribir titular y parrafo en cada payload de data/stories/_propuesta/,
#    y rendir cada uno:
uv run --extra stories python scripts/story_grafico.py < <payload>.json \
  | uv run --extra stories python scripts/story_render.py \
      --template templates/stories/alerta.html --out <destino>.png

# 5. Recompilar el PDF
uv run --extra stories --with markdown --with pypdf \
  python ".agents/skills/generar-reporte-editorial/scripts/generar_pdf.py" \
  --md docs/propuesta-produccion-diaria/propuesta.md \
  --pdf "docs/propuesta-produccion-diaria/Produccion Diaria GI - Propuesta.pdf" \
  --title "Producción Diaria" --tag "PROPUESTA DE TRABAJO" --theme verde
```

Los PNG salen a `data/stories/_propuesta/`, que está gitignored: son salida
regenerable, no fuente.

## Por qué los scripts viven acá y no en `scripts/`

El flujo de producción elige los activos por `Score_GI` y no por clase. Estos dos
scripts hacen lo contrario a propósito: fuerzan un activo por clase para mostrar el
alcance del sistema. Es una vitrina, no una tanda. Ponerlos en `scripts/` sería
ofrecer un atajo para saltarse al escáner, que es justamente lo que el escáner
existe para evitar.

## La restricción de horario, que conviene no olvidar

Tres de las seis clases dependen de un solo activo con material visual: divisas
(USD/CLP), criptomonedas (BTCUSD) y acciones (#MELI). Si el gate de agotamiento los
excluye, **esa clase no tiene sustituto** y la pieza no se puede producir ese día.

Pasó al armar esta propuesta: a las 17:40 de Chile los tres estaban excluidos por
haber consumido su recorrido diario. **El momento natural de la corrida es la
mañana**, entre las 10:30 y las 11:00 de Nueva York, con el recorrido del día por
delante.

Las otras once imágenes de activo (con sus prompts) están en
`docs/design/stories-gi/imagenes-por-activo.md`. Cuando existan, cada clase tendrá
más de un candidato y esta restricción desaparece.
