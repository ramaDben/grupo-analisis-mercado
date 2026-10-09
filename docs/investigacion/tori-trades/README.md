# Investigación: método de Tori Trades

Evidencia de la que sale `docs/metodologia-tendencias.md`.

- `seleccion.txt`: los 57 videos del canal (https://www.youtube.com/@ToriTrades/videos) que se
  documentaron, con el formato `id|tipo|duración_seg|título`.
- `prompt.md`: el prompt de análisis que se usó para todas las fichas.
- `fichas/<id>.md`: una ficha por video. La cabecera dice con qué modelo se hizo. Las de
  `gemini-2.5-flash` y las de `flash-lite` leen peor el gráfico, así que pesan menos como evidencia.
- `reglas_lote_N.json`: las reglas que se extrajeron de las fichas, por lotes, con su minuto.

Las fichas son lo que leyó un modelo, no el video. Antes de que una regla entre a la doctrina,
se verifica contra el tramo del video que cita.
