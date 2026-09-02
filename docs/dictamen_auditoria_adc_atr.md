# Dictamen de Auditoría Cuantitativa Externa
## Modelo ADC + ATR — Hallazgos, veredictos y diseño multi-escenario

**Destinatario:** Área de Research & Trading — Grupo Inteligencia  
**Emisor:** Auditor Cuantitativo Externo  
**Fecha:** 28 de agosto de 2026  
**Referencia:** *Solicitud de Auditoría Cuantitativa Externa — Vulnerabilidades y Hallazgos Metodológicos en el Modelo ADC + ATR*  
**Sistema:** Motor Cuantitativo de Análisis y Señales Intermercado (`Grupo Análisis Mercado`)  
**Premisa de alcance:** el motor evalúa el espectro completo (FX onshore y G10, commodities, índices y cripto). El ADC+ATR no puede ser una fórmula única; debe especializarse por calendario de negociación, régimen de liquidez y momento de la sesión.

---

## 1. Dictamen ejecutivo

La auditoría interna es **parcialmente válida**. Los hallazgos 1, 3 y 5 se aceptan. El hallazgo 2 se acepta en el mecanismo y se corrige en el marco fáctico. El hallazgo 4 se acepta como desacople especificación/código y se **rechaza** el remedio por ADX. El hallazgo 6 se **desvalida** como vulnerabilidad crítica: es una limitación de alcance, no un error del medidor de volatilidad.

El error de diseño de fondo no está en “el ATR de USD/CLP”. Está en aplicar un mismo suavizado, un mismo multiplicador \(1.5\times\), un mismo gate de consumo y un mismo calendario 24h a universos que no comparten sesión, gap ni estacionalidad intradía. Un motor de espectro completo necesita **playbooks por escenario**, no un parche local.

| Hallazgo | Diagnóstico interno | Dictamen | Severidad real |
|---|---|---|---|
| 1. Wilder RMA vs Pandas EWMA | \(\alpha\) incorrecto | **Aceptado** | Alta (paridad MT5 y estabilidad) |
| 2. Dilución por velas fuera de sesión | Sesgo 24h en FX local | **Aceptado con corrección** | Alta en onshore; nula en 24/7 |
| 3. Consumo diario vs reloj | Confounding temporal | **Aceptado** | Alta en todo el universo |
| 4. Multiplicador \(1.5\times\) vs ADX | Spec ≠ código | **Parcial** | Media el gap; baja el remedio |
| 5. Vela en formación (`iloc[-1]`) | Contaminación / self-kill Donchian | **Aceptado** | Alta |
| 6. Espacio continuo vs liquidez | Metas que ignoran barreras | **Rechazado como crítico** | Baja; es overlay, no motor |

---

## 2. Veredicto por hallazgo

### Hallazgo 1 — Aceptado. Corregir a Wilder.

La matemática es correcta. Con `tr.ewm(span=14, adjust=False)` Pandas usa

\[
\alpha_{\text{EMA}}=\frac{2}{\text{span}+1}=\frac{2}{15}\approx 0{,}1333
\]

Wilder (ATR nativo de MT5, TradingView, Bloomberg) usa

\[
\alpha_{\text{Wilder}}=\frac{1}{14}\approx 0{,}0714
\]

El \(86{,}7\%\) adicional de peso en la vela reciente es \((\alpha_{\text{EMA}}/\alpha_{\text{Wilder}})-1\). Eso **no** implica un ATR \(87\%\) más alto. Las vidas medias son \(\ln 2/\alpha\): \(\approx 5{,}2\) velas (EMA) vs \(\approx 9{,}7\) velas (Wilder). El indicador queda más nervioso, no necesariamente más grande.

**Decisión.** Sustituir por `ewm(alpha=1.0/period, adjust=False)` o `span=2*period-1`. Semillar con SMA de los primeros `period` True Ranges; sin ese seed, Python y `iATR` de MT5 seguirán divergiendo al inicio de la serie. Esta corrección es **universal**: aplica a todo el espectro, no solo a USD/CLP.

### Hallazgo 2 — Aceptado en mecanismo. Corregido en hechos. Generalizado a calendarios.

El mecanismo es válido: si se toman las últimas 14/60 velas H1 de un par onshore cotizado 24h en MT5, la muestra matutina está dominada por barras de liquidez residual y el ATR táctico queda subdimensionado. Eso sesga stops, impulso ADC y el ratio `espacio`.

Tres correcciones al informe interno:

1. El interbancario USD/CLP no opera de 09:00 a 16:00. La ventana onshore relevante está en torno a **09:00–14:00 CLT**. Las 16:00 son más propias de renta variable. Un filtro 09:00–16:00 sigue mezclando sesión y cola.
2. Los niveles \(1{,}75\) vs \(3{,}50\)–\(5{,}00\) CLP y el “70–80% de la muestra” no están evidenciados. Deben medirse sobre un mes de H1, no afirmarse.
3. El problema no es “USD/CLP”. Es **calendario heterogéneo**. Oro, WTI, índices cash, futuros y cripto no pueden heredar el filtro local, ni USD/CLP puede heredar el ATR 24h de XAUUSD.

Ponderar por tick volume de MT5 **no** se aprueba como solución primaria: en FX/CFD ese volumen es del broker, no del mercado.

**Decisión.** Introducir un `CalendarSpec` por activo (ver sección 3). Dos ATR, no uno: ATR de sesión para impulso/stops tácticos; ATR D1 para presupuesto diario. El True Range de la primera barra hábil **debe incluir el gap** si el escritorio asume riesgo overnight.

### Hallazgo 3 — Aceptado. El gate de consumo es un reloj, no un validador.

Premiar `consumo = rango_hoy / ATR_D1 < 0.70` a las 10:30 CLT (o a la apertura de NY) es un falso positivo estructural: casi cualquier activo pasa el umbral porque el día recién empieza. Combinado con un ATR H1 deprimido (hallazgos 1 y 2), `espacio` se infla y el factor llega a 20/20 sin impulso ni quiebre.

La fórmula propuesta

\[
\text{Consumo Ajustado}(t)=\frac{\text{Rango}(t)}{\text{ATR}_{D1}\times\sqrt{t/T}}
\]

es un parche browniano. Asume varianza intradía constante, explota cuando \(t\to 0\) y no captura la curva en U de índices, el solape Londres/NY de FX ni la concentración 09:00–14:00 de USD/CLP.

**Decisión.** Reemplazar el umbral fijo por un umbral condicionado a la fracción de varianza intradía ya realizada, \(F_i(t)\), estimada por activo \(i\):

\[
\text{consumo válido si}\quad \frac{\text{rango}(t)}{\text{ATR}_{D1}} < c\cdot F_i(t),\qquad c\in[0{,}6,\,0{,}8]
\]

Piso operativo: no otorgar el bonus de 20 puntos hasta que \(t\) cubra al menos 30–60 minutos de sesión relevante, o \(F_i(t)\ge 0{,}15\). Hasta no tener \(F_i\), **desactivar** el tramo de puntaje por consumo en la primera tanda.

### Hallazgo 4 — Gap de especificación aceptado. Remedio ADX rechazado.

Que `CLAUDE.md` hable de calibrar con ADX y el código fije `1.5 * atr_14` es un defecto de consistencia. Eso no autoriza

\[
k=1+\min\bigl(1,\;\text{ADX}_{14}/50\bigr)
\]

El ADC está diseñado para detectar **compresión**. En compresión el ADX suele ser bajo. Reducir \(k\) cuando ADX \(=14\) recorta el impulso exactamente en el setup del modelo. Subirlo cuando ADX \(=58\) proyecta más recorrido cuando el tramo ya ocurrió. ATR ya mide amplitud; ADX no es un pronóstico de expansión futura.

**Decisión.** Mantener \(k\) como parámetro de playbook, no como función continua del ADX. Calibrar \(k\) por clase de activo y régimen \(R_0\)–\(R_4\) como cuantiles del recorrido realizado *después* de eventos de compresión ADC (p. ej. \(k_{50}\) y \(k_{80}\) históricos). El ADX, si se usa, es filtro de régimen (“operar ruptura solo si ADX supera umbral *después* del quiebre”), no escalar del target.

### Hallazgo 5 — Aceptado. Indicadores de estado sobre vela cerrada.

Incluir la barra abierta en un Donchian hace que un máximo nuevo entre al canal en el mismo tick: `precio > donchian_high` se autoanula. En ATR, una barra de pocos minutos con rango estrecho deprime la media; el EWMA rápido del hallazgo 1 amplifica el efecto.

**Decisión.**

- Canal, ATR, ADX, ADC: `df.iloc[:-1]` (velas cerradas).
- Precio de evaluación: spot vs niveles congelados de la última vela cerrada.
- Excepción: `rango_hoy` **debe** usar la vela diaria en formación. Recortarla subestima el consumo.
- En cripto e índices futuros casi 24h la barra “en formación” siempre existe; la regla de cierre no es opcional.

### Hallazgo 6 — Rechazado como hallazgo crítico.

\(P + k\cdot\text{ATR}\) es un **presupuesto de volatilidad**, no un path de ejecución ni una meta de liquidez. Bandas de Bollinger y \(R_1\) no son zonas de absorción institucional: son un envelope estadístico y un pivote aritmético. En el book sintético de un CFD de MT5 no hay evidencia de que el volumen medio “absorba oferta pasiva”.

**Decisión.** No mezclar estructura de mercado dentro del motor ADC+ATR. El impulso se reporta como presupuesto. Un módulo aparte (S/R, VWAP, máximos de sesión, pivotes) puede *censurar* o anotar el presupuesto. Eso es diseño de producto, no un bug matemático.

---

## 3. Playbooks por escenario

El motor cubre el espectro completo. La unidad de configuración no es “el ATR”, es el **escenario** `{clase, calendario, momento_de_sesión, régimen}`.

| Escenario | Calendario | ATR táctico (impulso / SL) | ATR de espacio (D1) | Consumo \(F(t)\) | Gap overnight en TR | \(k\) inicial |
|---|---|---|---|---|---|---|
| FX onshore (USD/CLP) | ~09:00–14:00 CLT | H1 solo sesión hábil | D1 (incluye gap) | Curva local, pico matinal | Sí, primera H1 hábil | Calibrar aparte; no copiar G10 |
| FX G10 | 24h, 5 días | H1 24h Wilder | D1 | Solape Londres/NY | Fin de semana / rollover | Base \(1.5\times\); ajustar por régimen |
| Índices cash (IPSA, etc.) | RTH bursátil | H1 RTH | D1 cash | Curva en U (apertura/cierre) | Sí, gap de apertura | Distinto de futuros |
| Índices futuros | Casi 23h | H1 globex/sesión según producto | D1 del futuro | Overnight + cash open | Según contrato | No mezclar con cash |
| Commodities (XAU, WTI) | Sesión COMEX/NYMEX + cola | H1 24h o sesión del contrato | D1 | Apertura US + inventario | Fin de semana; roll | Cuidar roll y gaps |
| Cripto | 24/7 | H1 24h, sin filtro de sesión | D1 00:00 UTC o 21:00 CLT, fijo | Relativamente plano; picos US | No hay close; no filtrar | \(k\) propio; no heredar FX |

Reglas que no se negocian:

1. Un activo sin `CalendarSpec` no publica `impulso_adc_atr` ni score de espacio.
2. No se reutiliza el filtro 09:00–14:00 CLT fuera de FX onshore.
3. El ADC (compresión de canal) se calcula en el **mismo calendario** que el ATR táctico. Mezclar Donchian 24h con ATR de sesión produce quiebres fantasmas.
4. El momento de la tanda (apertura local, apertura NY, close) es un input del score, no un comentario en el log.

---

## 4. Respuestas a las preguntas del informe

### 4.1 Series discontinuas (USD/CLP y análogos)

Mejor práctica: **no borrar el overnight del riesgo; sí sacarlo de la muestra de volatilidad táctica**.

- Serie táctica: H1 de sesión hábil. `prev_close` de la 09:00 = cierre de la última H1 hábil previa, de modo que el gap entra en un solo True Range.
- Serie de presupuesto: ATR D1 estándar Wilder, que ya incorpora el día completo.
- Prohibido: ATR H1 24h para stops intradía en onshore; tick-volume como ponderador primario; copiar este filtro a XAU/WTI/cripto.

Para G10, oro y cripto la “discontinuidad” relevante es el fin de semana o el roll, no la noche chilena. Tratarlos como USD/CLP es un error simétrico al actual.

### 4.2 Calibración del multiplicador

Es preferible **multiplicadores discretos por régimen y clase de activo**, no una función continua de ADX ni de RSI.

- ADX/RSI continuos mezclan fuerza de tendencia *ya realizada* con expansión *por realizar*. En el ADC eso es adverso.
- \(R_0\)–\(R_4\) ya es el lugar correcto para \(k\), a condición de que cada régimen tenga \(k\) estimado con datos (cuantil del move post-compresión), no un número escrito a mano.
- Un solo \(1.5\times\) para IPSA, USD/CLP, WTI y BTC no es parsimonia: es especificación incompleta.

### 4.3 Normalización del gate de consumo

No se recomienda \(\sqrt{t/T}\) en producción. Se recomienda una **curva empírica de varianza intradía** \(F_i(t)\) por escenario:

- FX onshore: masa de varianza en la mañana local.
- FX G10: pico en solape Londres/NY.
- Índices cash: U (apertura y cierre).
- Cripto: casi plana, con leve pico US.

Hasta no estimar \(F_i\), el validador de consumo no puntúa en las primeras 60 minutos de la sesión *relevante de ese activo* (para USD/CLP, sesión local; para un índice US, cash open; para cripto, no hay “apertura” que justifique el mismo gate).

---

## 5. Plan de corrección

| Prioridad | Cambio | Universo | Criterio de aceptación |
|---|---|---|---|
| P0 | Indicadores sobre vela cerrada; spot vs niveles congelados | Todos | Donchian no se autoanula; ATR no cae al abrir la barra |
| P0 | Desactivar bonus de consumo en la primera hora de sesión relevante | Todos | Ningún activo recibe 20/20 solo por reloj |
| P1 | ATR Wilder (`alpha=1/period` + seed SMA) | Todos | Paridad con `iATR` MT5 en velas cerradas, tolerancia de redondeo |
| P2 | `CalendarSpec` y doble ATR (sesión vs D1) | Por escenario | USD/CLP usa sesión; XAU/BTC no heredan el filtro |
| P2 | ADC y Donchian en el mismo calendario que el ATR táctico | Todos | Sin quiebres por barras nocturnas en onshore |
| P3 | \(k\) por clase × régimen, estimado en eventos de compresión | Todos | Documentar cuantiles; retirar la frase “calibrado con ADX” o implementarla como filtro, no como \(k(ADX)\) |
| P4 | Overlay de estructura separado del presupuesto ADC | Producto | El informe muestra “presupuesto” y “obstáculo” como campos distintos |

Lo que **no** se implementa:

- \(k=1+\min(1,\text{ADX}/50)\)
- Consumo ajustado por \(\sqrt{t/T}\) sin piso ni curva \(F(t)\)
- ATR ponderado por tick volume de MT5 como corrección principal
- Tratar Bollinger / \(R_1\) como liquidez institucional
- Un único horario 09:00–16:00 CLT para todo el espectro

---

## 6. Conclusión para el área

Tres de seis hallazgos son defectos reales de señal en vivo (vela abierta, gate de consumo, suavizado). Uno es un problema de **universo** mal especificado (calendario), no de un par. Uno es deuda de documentación. Uno está mal clasificado.

El modelo ADC+ATR puede seguir siendo el medidor de compresión y presupuesto de recorrido del motor, a condición de que deje de comportarse como un indicador de un solo mercado. En un motor de espectro completo, la unidad de diseño es el escenario. Sin `CalendarSpec`, sin \(F_i(t)\) y sin \(k\) por clase y régimen, cualquier score de “espacio” en la tanda de las 10:30 seguirá midiendo el reloj, no el mercado.

---

*Fin del dictamen.*
