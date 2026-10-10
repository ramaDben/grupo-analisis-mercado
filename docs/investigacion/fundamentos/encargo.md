# Encargo: verificar los fundamentos citables de la doctrina de líneas de tendencia

Rama: `docs/metodologia-tendencias`. No toques ningún otro archivo del repo.
Salida única: `docs/investigacion/fundamentos/fuentes.md` (créalo y ve escribiéndolo fila por fila,
para que el avance no se pierda si la sesión se corta).

## Para qué es
La doctrina `docs/metodologia-tendencias.md` (método de Tori Trades) va a llevar, por cada regla,
un fundamento citable: un pilar canónico (teoría clásica de análisis técnico) y un pilar empírico
(papers o investigación institucional). Abajo hay 12 afirmaciones escritas DE MEMORIA. Tu trabajo es
confirmarlas, corregirlas o descartarlas con fuentes reales que hayas abierto.

## Reglas duras
1. **Nunca inventes.** Ni autores, ni años, ni revistas, ni volúmenes, ni páginas, ni citas
   textuales. Si no lo viste en una página que abriste, no lo escribas.
2. Toda fila lleva al menos una URL que efectivamente visitaste (DOI, editorial, SSRN, NBER,
   repositorio de la institución, Internet Archive, Google Books con vista previa).
3. Cita textual: máximo 2 frases, solo si la leíste en la fuente. Si solo la viste citada por
   terceros, márcala como "vía fuente secundaria: <URL>".
4. Si un dato de la afirmación está mal (año, revista, título, lo que dice), el estado es
   **corregida** y escribes el dato correcto.
5. Si no encuentras la fuente o lo que afirma, el estado es **no encontrada**. Es una respuesta
   válida y útil; no rellenes.

## Formato de cada fila en `fuentes.md`
```
### F<n>. <título corto>
- Estado: confirmada | corregida | no encontrada
- Referencia completa: Autor(es) (año). Título. Revista/editorial, volumen(número), páginas. DOI si existe.
- Qué afirma (en español, 1-3 frases):
- Cita textual (opcional, ≤2 frases, con página o sección):
- Corrección respecto de la afirmación original (si aplica):
- URLs visitadas:
```

## Las 12 afirmaciones

**F1. Teoría de Dow.** William P. Hamilton, *The Stock Market Barometer* (1922), y Robert Rhea,
*The Dow Theory* (1932). Verificar que formulan: (a) la tendencia se define por máximos y mínimos
sucesivos crecientes (alcista) o decrecientes (bajista); (b) una tendencia se presume vigente hasta
una señal clara de giro; (c) las "líneas" (consolidaciones laterales) como fase sin tendencia.
Indicar cuál de los dos libros sostiene cada punto.

**F2. Edwards y Magee.** Robert D. Edwards y John Magee, *Technical Analysis of Stock Trends*
(1.ª ed. 1948). Verificar qué dicen sobre: cómo se traza una línea de tendencia, qué la hace más
válida (número de toques, longitud, ángulo) y qué cuenta como penetración (criterio de cierre,
porcentaje).

**F3. Murphy.** John J. Murphy, *Technical Analysis of the Financial Markets* (New York Institute of
Finance, 1999), capítulo 4 ("Basic Concepts of Trend"). Verificar: (a) se necesitan dos puntos para
trazar la línea y un tercero para confirmarla; (b) la importancia crece con la longitud, el número
de toques y disminuye con el ángulo (las líneas muy empinadas son menos confiables); (c) filtros de
penetración (cierre, regla del 3 %, regla de dos días); (d) inversión de roles: un soporte roto pasa
a ser resistencia y viceversa; (e) principio del abanico (tres líneas). Confirmar número y título
del capítulo.

**F4. Osler.** Carol L. Osler (2000), "Support for Resistance: Technical Analysis and Intraday
Exchange Rates", *Economic Policy Review* de la Fed de Nueva York. Verificar el número, qué
niveles usó (publicados por firmas) y qué encontró exactamente (¿los niveles predicen giros de
tendencia intradía?, ¿en qué monedas?).

**F5. Momentum de series de tiempo.** Moskowitz, Ooi y Pedersen (2012), "Time Series Momentum",
*Journal of Financial Economics* 104(2). Verificar referencia y hallazgo principal (persistencia
del retorno pasado de 12 meses en futuros de muchas clases de activos).

**F6. AQR, un siglo de trend following.** Hurst, Ooi y Pedersen (2017), "A Century of Evidence on
Trend-Following Investing", *Journal of Portfolio Management*. Verificar referencia, período, y
qué dicen de cuándo el trend following funciona mal (mercados sin tendencia, giros bruscos).

**F7. Man AHL / Man Institute.** Encontrar un documento de Man Group (Man AHL o Man Institute)
sobre trend following que describa sus modos de falla (mercados laterales, reversiones rápidas,
"whipsaw"). Dar título, año, URL. Si no encuentras uno específico, decirlo.

**F8. Brock, Lakonishok y LeBaron (1992)**, "Simple Technical Trading Rules and the Stochastic
Properties of Stock Returns", *Journal of Finance* 47(5). Verificar referencia y si las reglas
probadas incluyen rupturas de rango (soporte/resistencia, "trading range break") además de medias
móviles, y qué encontraron.

**F9. Lo, Mamaysky y Wang (2000)**, "Foundations of Technical Analysis: Computational Algorithms,
Statistical Inference, and Empirical Implementation", *Journal of Finance* 55(4). Verificar
referencia y qué patrones reconocieron automáticamente y qué concluyeron.

**F10. Park e Irwin (2007)**, "What Do We Know About the Profitability of Technical Analysis?",
*Journal of Economic Surveys* 21(4). Verificar referencia y la conclusión general (resultados
mixtos, problemas de data snooping, ganancias que se reducen en estudios recientes).

**F11. Evidencia sobre líneas de tendencia DIAGONALES.** Buscar estudios académicos que hayan
probado específicamente rupturas de líneas de tendencia diagonales (no medias móviles ni
horizontales). Listar lo que exista con referencia completa, o declarar que no se encontró
evidencia específica. Esta fila es la más importante: la doctrina va a decir honestamente cuán
probada está la parte diagonal.

**F12. Alpha Architect.** Encontrar un artículo de Alpha Architect sobre trend following o
momentum de series de tiempo que discuta sus fricciones de implementación o modos de falla. Dar
título, autor, año y URL.

## Al terminar
Agrega al final de `fuentes.md` una sección "Resumen" con una tabla: F, estado, una línea.
No hagas commit.
