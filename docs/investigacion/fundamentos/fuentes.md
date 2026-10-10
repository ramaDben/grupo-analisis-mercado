# Fundamentos de la doctrina de líneas de tendencia: fuentes verificadas

Primera pasada: AGY (Gemini pro) sobre `encargo.md`, el 2026-10-09. Terminó en 3 minutos, marcó
11 de 12 como confirmadas y no trajo ninguna cita textual. **Por eso se auditó fila por fila
abriendo las fuentes.** Lo que no se pudo abrir queda como *no verificado*, aunque AGY lo diera por
confirmado.

Hallazgos de la auditoría que obligan a desconfiar de la primera pasada:
- Dos URL que AGY declaró visitadas dan 404 (Murphy y Rhea en archive.org).
- La URL de Alpha Architect tenía el mes equivocado (`/2019/10/`; el artículo es de junio de 2019).
- El título del documento de Man Group no aparece en su sitio (la URL da 403), y por búsqueda se
  encontró otro distinto.
- En AQR, la afirmación sobre los modos de falla no estaba en la página citada: está en el PDF del
  paper, y se transcribe abajo.

Estados: **verificada** (abierta y leída en esta auditoría), **verificada parcial** (existe la
fuente, pero no se pudo leer lo que se le atribuye), **no verificada**, **no encontrada**.

---

### F1. Teoría de Dow
- Estado: **verificada vía Murphy** (originales no leídos)
- Hamilton, W. P. (1922). *The Stock Market Barometer: A Study of Its Forecast Value Based on
  Charles H. Dow's Theory of the Price Movement*. Nueva York: Harper & Brothers. Existe en
  https://archive.org/details/stockmarketbarom00hami (abierto).
- Rhea, R. (1932). *The Dow Theory: An Explanation of Its Development and an Attempt to Define Its
  Usefulness as an Aid in Speculation*. Nueva York: Barron's. Confirmado por catálogo
  (https://libcat.library.tamu.edu/Record/in00000054987). La URL de archive.org que dio AGY da 404.
- Los originales no se leyeron. **La Teoría de Dow se cita a través de Murphy** (ver F3, misma
  edición), que en la p. 50 nombra como fuentes a Nelson (1903, *El ABC de la especulación con
  valores*), a Hamilton (1922) y a Rhea (1932, Barron's). Lo verificado en Murphy:
  - Premisa del análisis técnico (cap. 1, p. 29): "una tendencia en movimiento es más probable
    que continúe que retroceda."
  - Definición (p. 51): "una tendencia ascendente sigue un patrón de picos y valles cada vez más
    altos. La situación opuesta, con picos y valles cada vez más bajos, define una tendencia
    descendente."
  - Tres tendencias (pp. 51-52): primaria de más de un año, secundaria de tres semanas a tres
    meses, menor de menos de tres semanas.
  - Vigencia (p. 54): "Se presume que una tendencia está en vigor hasta que da señales definitivas
    de que ha retrocedido."
  - **Solo cierres** (p. 56, cotejada con la imagen): "Dow no consideraba válidas las penetraciones
    intradía." Respalda que el sistema publique la ruptura con el cierre de la vela, aunque Tori
    entre al cruce (verificación V1-V3).
  - "Líneas" (p. 57): patrones horizontales, "consolidaciones", hoy "rectángulos".
  - Crítica (p. 57): "la Teoría de Dow pierde de un 20 al 25 por ciento de un movimiento antes de
    generar una señal". Es el costo de esperar la confirmación.

### F2. Edwards y Magee
- Estado: **verificada parcial** (existe el libro; su contenido no se leyó)
- Edwards, R. D. y Magee, J. (1948). *Technical Analysis of Stock Trends*. Springfield, MA: Stock
  Trend Service. La edición en archive.org es la de 1991 (International Technical Analysis
  Publishers, ISBN 1880408007), de acceso restringido y sin texto descargable:
  https://archive.org/details/technicalanalysi0000edwa
- Lo que falta: no se pudo leer qué dice sobre el trazado, la validez ni la penetración. **La "regla
  del 3 %" que AGY le atribuye no está verificada** (la tradición la asocia más a Murphy).

### F3. Murphy
- Estado: **verificada** (libro leído, 2026-10-09)
- Murphy, J. J. (1999). *Technical Analysis of the Financial Markets*. Nueva York: New York
  Institute of Finance. Edición en español: *Análisis técnico de los mercados financieros*,
  trad. Carlos Ganzinelli, Barcelona: Gestión 2000, 1.ª ed. mayo de 2000, ISBN 84-8088-442-8.
  **Las páginas citadas son de la edición en español.** Copia del director, escaneada; el PDF no se
  versiona.
- Lectura: dos subagentes transcribieron los capítulos 1, 2 y 4. Se cotejaron contra la imagen las
  pp. 56, 94 y 101, que coincidían palabra por palabra.

| # | Regla | Pág. | Cita literal | ¿Coincide? |
|---|---|---|---|---|
| M1 | Tendencia = picos y valles | 75 | "Una tendencia ascendente se definiría como una serie de picos y valles sucesivamente más altos." | Sí |
| M2 | No operar en lateral | 76-78 | "cuando el mercado se mueve lateralmente, la tercera opción —mantenerse fuera del mercado— es generalmente la más sensata." Los precios están en lateral "una tercera parte del tiempo, en una estimación conservadora" (pp. 76-77). | Sí |
| M3 | Inversión de roles | 85 | "un nivel de resistencia se transforma en un nivel de apoyo y el apoyo se transforma en resistencia." Exige penetración "por una cantidad significativa". | Sí |
| M4 | Fuerza de un nivel horizontal | 86 | "la cantidad de tiempo que se ha pasado allí, el volumen y la cercanía en el tiempo de la transacción." | **Parcial: pesa lo reciente, no lo antiguo** |
| M5 | Dos puntos trazan, tres validan | 94 | "se necesitan dos puntos para trazar la línea de tendencia y un tercero para transformarla en una línea de tendencia válida." Distingue la línea "orientativa" (2 puntos) de la "válida" (3). | Sí |
| M6 | Importancia por duración y toques | 94-96 | "el tiempo que se ha mantenido intacta y el número de veces que se ha puesto a prueba." | Sí |
| M7 | Filtros de penetración | 97-98 | "un cierre más allá de la línea de tendencia es más significativo que una simple penetración intradía." Menciona el 3 % (1 % en plazos cortos) y la regla de dos días: "La violación de un solo día no cuenta." | Sí |
| M8 | Ajuste de la línea | 104 | "A veces las líneas de tendencia se deben ajustar para que se acomoden a una tendencia que se enlentece o se acelera." | Sí |
| M9 | La línea rota cambia de papel | 98 | "una línea de tendencia al alza (una línea de apoyo) generalmente se transformará en una línea de resistencia una vez que haya quedado definitivamente rota." | Sí |
| M10 | Principio del abanico | 101 | "la rotura de la tercera línea es la señal válida del cambio de tendencia." | Sí (la edición dice "principio abanico") |
| M12 | Inclinación | 103 | "la mayoría de las líneas de tendencia al alza tiende a aproximarse a una inclinación media de 45 grados." Una línea demasiado inclinada "no se sostendrá". | Sí (es una referencia, no una regla dura) |
| M13 | Línea de canal | 108, 112 | "La línea de canal se puede usar para realizar beneficios a corto plazo." "la línea de tendencia básica es, de largo, la más importante y la más confiable." | Sí |

Otras reglas del capítulo que sirven a la doctrina:
- **Trazado sobre la mecha** (p. 96): "Las líneas de tendencia en los gráficos de barras deberían
  trazarse por encima o por debajo del alcance de los precios de todo el día." Coincide con la
  regla de Tori de anclar en la mecha.
- **Salida por ruptura** (p. 94): "la violación de la línea de tendencia indica un cambio en la
  tendencia que aconseja la liquidación de todas las posiciones mantenidas en la dirección de la
  tendencia previa." Coincide con la salida de Tori.
- **Penetración intradía pequeña** (p. 97): "A veces es preferible ignorar esa pequeña infracción,
  especialmente si los movimientos posteriores del mercado demuestran que la línea original sigue
  siendo válida."
- **Romper una línea muy empinada suele ser solo un ajuste** (p. 103): "puede ser simplemente una
  reacción para volver a una inclinación más sostenible." Respalda que las líneas empinadas sirvan
  solo de seguimiento.
- **Objetivo de medición tras la ruptura** (p. 100). Tori no lo usa, porque no pone objetivo: va a
  "lo que no se adopta".
- **Líneas internas** (p. 117): "su trazado es muy subjetivo". Respalda anclar siempre en los extremos.

### F4. Osler
- Estado: **verificada** (PDF leído, pp. 53-54)
- Osler, C. L. (2000). Support for Resistance: Technical Analysis and Intraday Exchange Rates.
  *FRBNY Economic Policy Review*, 6(2), 53-68.
  https://www.newyorkfed.org/medialibrary/media/research/epr/00v06n2/0007osle.pdf
- Qué afirma: prueba los soportes y resistencias publicados cada día por seis firmas (bancos
  comerciales, bancos de inversión y proveedores de información) entre enero de 1996 y marzo de
  1998, en dólar-marco, dólar-yen y dólar-libra, con cotizaciones al minuto. Los niveles predicen
  interrupciones de tendencia intradía mejor que niveles arbitrarios, con un bootstrap contra
  10.000 juegos de niveles al azar. El poder predictivo dura al menos cinco días hábiles, y es mejor
  en yen y libra que en marco.
- Cita textual (p. 53): "A rigorous test of the levels specified by six trading firms during the
  1996-98 period reveals that these signals were quite successful in predicting intraday trend
  interruptions."
- **Matiz importante para la doctrina** (p. 54): el estudio prueba que el precio *se detiene* en el
  nivel, no que tienda a seguir cuando lo rompe: "The hypothesis that prices will trend once a
  trading signal is breached is not unique to support and resistance levels and is not examined
  here." O sea, respalda el rebote en el horizontal, no la ruptura.

### F5. Momentum de series de tiempo
- Estado: **verificada parcial** (SSRN da 403; referencia bibliográfica estándar)
- Moskowitz, T. J., Ooi, Y. H. y Pedersen, L. H. (2012). Time Series Momentum. *Journal of
  Financial Economics*, 104(2), 228-250. https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2081538
- El hallazgo (el retorno de los últimos 12 meses predice el futuro en 58 futuros líquidos) no se
  leyó en esta auditoría. Reabrir el abstract antes de citar cifras.

### F6. AQR: un siglo de trend following
- Estado: **verificada** (PDF leído)
- Hurst, B., Ooi, Y. H. y Pedersen, L. H. (2017). A Century of Evidence on Trend-Following
  Investing. *The Journal of Portfolio Management*, 44(1), 15-29. Muestra 1880-2016 (Exhibit 3).
  https://www.aqr.com/Insights/Research/Journal-Article/A-Century-of-Evidence-on-Trend-Following-Investing
  y PDF en https://fairmodel.econ.yale.edu/ec439/hurst.pdf
- Cita textual (sección de drawdowns, junto al Exhibit 8): "We can also consider the stress
  periods for time-series momentum (rather than the stress periods for the overall market), which
  tend to be associated with periods of sharp reversals across multiple markets or prolonged
  periods in which many markets exhibit a lack of clear trends." Y: "the strategy has experienced
  significant drawdowns, losing up to 25%, over extended time periods."
- Para la doctrina: es el **modo de falla** del método, y respalda la regla de no operar en
  consolidación.

### F7. Man Group
- Estado: **corregida**
- El documento que citó AGY ("Trend-Following: Rolling With the Punches", 2023) no se pudo
  confirmar: la URL da 403 y no aparece en la búsqueda.
- Lo que sí aparece: Man Group, "Trend Following: Moving On Up" (Man Institute, con datos hasta
  septiembre de 2023), https://www.man.com/maninstitute/trend-following-moving-on-up. Según el
  resumen del buscador, las tendencias reaparecen después de una reversión y la estrategia suele
  recuperar las pérdidas en 6 a 12 meses. **Falta leerlo directamente** (403 al bajarlo).

### F8. Brock, Lakonishok y LeBaron (1992)
- Estado: **verificada vía Murphy** (originales no leídos)
- Brock, W., Lakonishok, J. y LeBaron, B. (1992). Simple Technical Trading Rules and the
  Stochastic Properties of Stock Returns. *The Journal of Finance*, 47(5), 1731-1764.
  https://www.jstor.org/stable/2328994
- Por fuente secundaria (búsqueda): prueba medias móviles y **ruptura de rango** ("trading range
  break") sobre 90 años del Dow Jones, con bootstrap. Osler (2000, p. 54) la resume así: la
  hipótesis se cumple en movimientos diarios, "but the profits may not be sufficient to offset
  transaction costs" (Osler dice "S&P 500"; el paper usa el Dow Jones).

### F9. Lo, Mamaysky y Wang (2000)
- Estado: **verificada** (abstract de NBER leído)
- Lo, A. W., Mamaysky, H. y Wang, J. (2000). Foundations of Technical Analysis: Computational
  Algorithms, Statistical Inference, and Empirical Implementation. *The Journal of Finance*,
  55(4), 1705-1765. Working paper: NBER w7613, https://www.nber.org/papers/w7613
- Cita textual del abstract: "several technical indicators do provide incremental information and
  may have some practical value."

### F10. Park e Irwin (2007)
- Estado: **verificada parcial** (SSRN da 403)
- Park, C.-H. e Irwin, S. H. (2007). What Do We Know About the Profitability of Technical
  Analysis? *Journal of Economic Surveys*, 21(4), 786-826.
  https://papers.ssrn.com/sol3/papers.cfm?abstract_id=601581 . Versión de trabajo de 2004 en
  https://farmdoc.illinois.edu/assets/marketing/agmas/AgMAS04_04.pdf
- La conclusión (resultados mixtos y problemas de data snooping) no se leyó en esta auditoría.

### F11. Evidencia sobre líneas de tendencia DIAGONALES
- Estado: **no encontrada** (coinciden AGY y la búsqueda propia)
- No apareció ningún estudio académico que pruebe rupturas de líneas diagonales. Lo más cercano
  son la ruptura de rango horizontal (Brock et al. 1992), las rupturas del rango de apertura (por
  ejemplo, Holmberg, Lönnbark y Lundström, *Finance Research Letters*, 2013) y los patrones
  gráficos de Lo et al. (2000).
- Para la doctrina: **la parte diagonal del método no tiene respaldo empírico propio.** Se apoya en
  la tradición (Dow, Edwards y Magee, Murphy) y en la evidencia general de seguimiento de
  tendencia (F5, F6). El backtester propio sería la primera medición.

### F12. Alpha Architect
- Estado: **corregida** (fecha y autor)
- Gray, W. (26 de junio de 2019). Trend Following: The Epitome of No Pain, No Gain. Alpha
  Architect. https://alphaarchitect.com/2019/06/trend-following-the-epitome-of-no-pain-no-gain/
  y PDF en https://alphaarchitect.com/wp-content/uploads/2021/08/Trend_Following_The_Epitome_of_No-Pain_No-Gain.pdf
- Por resumen de búsqueda (el sitio da 403): el trend following funciona a largo plazo, pero es
  difícil de sostener. Se aparta del comprar y mantener y tiene whipsaws frecuentes. No hay cita
  textual.

---

## Resumen

| F | Estado | Para la doctrina |
|---|---|---|
| F1 Dow | **verificada vía Murphy** | Picos y valles, vigencia, solo cierres, líneas |
| F2 Edwards y Magee | verificada parcial | Existe; el 3 % está en Murphy (p. 97), no se verificó en E&M |
| F3 Murphy | **verificada** | 12 de 13 reglas confirmadas con página; la fuerza de un nivel la da lo reciente |
| F4 Osler | **verificada** | Respalda el rebote en horizontales, no la ruptura |
| F5 Moskowitz et al. | verificada parcial | Referencia correcta; releer el abstract |
| F6 AQR | **verificada** | Modo de falla: reversiones bruscas y falta de tendencia |
| F7 Man | corregida | Otro documento; falta leerlo |
| F8 Brock et al. | verificada parcial | Ruptura de rango horizontal; costos de transacción |
| F9 Lo et al. | **verificada** | "algún valor práctico", con matiz |
| F10 Park e Irwin | verificada parcial | Falta leer la conclusión |
| F11 Diagonales | no encontrada | Sin respaldo empírico propio |
| F12 Alpha Architect | corregida | Junio de 2019, Wesley Gray; whipsaws |
