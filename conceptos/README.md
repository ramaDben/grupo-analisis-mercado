# Conceptos — notas canónicas de la malla educativa

Cada archivo `<id>.md` es la **fuente de verdad** del contenido didáctico de un
concepto, curada y aprobada por el director. El comando `/rencuesta` la lee para
profundizar sin repetir, y la actualiza al aprobar contenido nuevo.

La estructura de relaciones (qué concepto se conecta con cuál) vive en
`data/mapa_conceptos.json`. Aquí vive el **contenido**.

## Formato de una nota

```markdown
---
id: stop-loss            # kebab-case, igual a la clave en mapa_conceptos.json
nombre: Stop loss
estado: explicado        # explicado | pendiente
encuestas: [id_encuesta] # encuestas que trataron el concepto
ancla: [atr, riesgo]     # indicadores/drivers del repo en los que se apoya
---

Contenido didáctico en voz novata. Los enlaces [[otro-concepto]] reflejan
las aristas del grafo y tejen la malla.
```
