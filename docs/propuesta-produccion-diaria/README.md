# Presentación del sistema de producción diaria a Hari

**El entregable es el producto, no una presentación sobre el producto.** Lo que se le
manda a Hari es el informe de apertura tal cual sale del sistema, más las siete piezas
del día, una por clase de activo. Un documento que describa el sistema diría lo mismo
con menos evidencia.

## Qué hay acá

| Archivo | Qué es |
|---|---|
| `correo-hari-propuesta.txt` | El correo, con los 8 adjuntos listados |
| `Marco de Apertura - GI (muestra).pdf` | Muestra del informe, generada el 2026-08-25 |
| `informe-apertura-muestra.md` | Su fuente, con el análisis escrito |
| `generar_piezas.py` | Payloads de las 6 piezas de activo, una por clase |
| `generar_pieza_macro.py` | Payload de la pieza `calendario`, la séptima clase |

La muestra del informe está acá para revisar formato y tono. **El que se envía se
genera la mañana del envío**, junto con las siete piezas, para que todo lleve la misma
fecha.

## La secuencia completa

```bash
# 1. Refrescar los datos macro. Sin esto el informe no se emite.
uv run --with requests --with tenacity --with python-dotenv --with yfinance \
  python ".agents/skills/ecosistema-datos-macro/scripts/pipeline_ingesta.py"

# 2. El informe: tablas resueltas, análisis marcado [[ESCRIBIR]]
uv run python scripts/pipeline_informe.py --tipo apertura --preparar
#    ... escribir las 4 secciones ...
uv run --extra stories --with markdown --with pypdf \
  python scripts/pipeline_informe.py --tipo apertura --rendir data/informes/<dir>

# 3. Las piezas: 6 de activo + 1 macro
uv run --with MetaTrader5 python docs/propuesta-produccion-diaria/generar_piezas.py
uv run python docs/propuesta-produccion-diaria/generar_pieza_macro.py
#    ... escribir titular y parrafo en cada payload ...
uv run --extra stories python scripts/story_grafico.py < <payload>.json \
  | uv run --extra stories python scripts/story_render.py \
      --template templates/stories/alerta.html --out <destino>.png
```

Los PNG salen a `data/stories/_propuesta/`, que está gitignored: son salida
regenerable, no fuente.

## Por qué los scripts viven acá y no en `scripts/`

El flujo de producción elige los activos por `Score_GI` y no por clase. Estos dos hacen
lo contrario a propósito: fuerzan un activo por clase para mostrar el alcance del
sistema. Es una vitrina, no una tanda. Ponerlos en `scripts/` sería ofrecer un atajo
para saltarse al escáner, que es justamente lo que el escáner existe para evitar.

## La restricción de horario, que conviene no olvidar

Tres de las seis clases dependen de un solo activo con material visual: divisas
(USD/CLP), criptomonedas (BTCUSD) y acciones (#MELI). Si el gate de agotamiento los
excluye, **esa clase no tiene sustituto** y su pieza no se puede producir ese día.

Pasó al armar esto: a las 17:40 de Chile los tres estaban excluidos por haber consumido
su recorrido diario. **El momento de la corrida es la mañana**, entre las 10:30 y las
11:00 de Nueva York, con el recorrido del día por delante.

Los prompts de las once imágenes que faltan están en
`docs/design/stories-gi/imagenes-por-activo.md`. Cuando existan, cada clase tendrá más
de un candidato y esta restricción desaparece.
