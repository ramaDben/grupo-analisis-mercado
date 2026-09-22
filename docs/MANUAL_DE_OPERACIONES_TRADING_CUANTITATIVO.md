# Manual de Operaciones · Trading Cuantitativo Intermercado
### De la macroeconomía real a tu plataforma MetaTrader 5
**Grupo Inteligencia · Departamento de Estudios y Research**  
*Manual formativo modular para el trader cuantitativo · Edición Pública Inicial · Versión 1.0 · Septiembre 2026*

---

> [!CAUTION]
> **Aviso de riesgo y transparencia.** Este documento es material educativo y formativo de Grupo Inteligencia. No constituye asesoría financiera personalizada ni garantiza rentabilidades futuras. El trading en Contratos por Diferencia (CFD) con apalancamiento conlleva un alto riesgo de pérdida de capital, y puedes perder la totalidad de lo que depositas.
>
> Este manual no es un robot que opera solo. Nosotros publicamos a diario el clima económico y el sesgo por activo; **la decisión, el cálculo del tamaño y la ejecución de cada orden son tuyas**, en tu plataforma y bajo tu criterio.

---

## 🧭 Cómo usar este manual

El manual está dividido en **13 módulos (M0 a M12) y 3 anexos**. Cada módulo es autocontenido: responde una pregunta concreta y no necesitas haber leído el anterior para aplicarlo.

| Si lo que quieres es… | Lee estos módulos |
|---|---|
| Entender qué estás operando y las expectativas estadísticas reales | **M0**, **M1** |
| Entender por qué se mueve el dinero en el mundo | **M2**, **M3** |
| Armar una operación concreta de principio a fin | **M4** → **M5** → **M6** → **M7** → **M8** |
| Saber cuándo NO operar y gestionar el co-riesgo de cartera | **M8**, **M9** |
| Consultar la regla y el swap de un activo puntual | **M10** |
| Repasar en 30 segundos antes de hacer clic | **M11** |
| Registrar y auditar tu disciplina operativa | **M12** |
| Buscar una sigla o un umbral maestro | **A1**, **A2** |

### Qué te damos nosotros y qué determinas tú

Esta separación es la clave del manual y conviene tenerla clara desde el principio:

| Insumo | De dónde sale | Por qué |
|---|---|---|
| **El clima** (régimen R0 a R4) y el **sesgo** por activo | Lo publicamos a diario | Requiere series oficiales de tasas, inflación y cobre que un operador particular no va a calcular a mano cada mañana |
| **El setup**, la **entrada**, el **stop**, el **objetivo**, el **tamaño** y los **filtros** | **Los determinas tú** en tu plataforma | Son reglas matemáticas que se leen del gráfico. Este manual te da todas |

El **Anexo A2** trae los umbrales exactos del clima, así que también puedes verificar por tu cuenta la clasificación que publicamos. Nada en este manual es una caja negra.

---

<div class="contenedor-diagrama">
<svg viewBox="0 0 760 140" width="100%" height="140" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Paso 1 -->
  <rect x="20" y="18" width="205" height="56" rx="6" fill="#0B1926" stroke="#38BDF8" stroke-width="1.5"/>
  <text x="122" y="42" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#38BDF8" text-anchor="middle">1. EL CLIMA MACRO (D1)</text>
  <text x="122" y="60" font-size="9.5" fill="#94A3B8" text-anchor="middle">¿Confirmado por 2 días?</text>

  <line x1="225" y1="46" x2="265" y2="46" stroke="#00DC82" stroke-width="2.5"/>
  <polygon points="265,46 257,41 257,51" fill="#00DC82"/>
  <text x="245" y="38" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#00DC82" text-anchor="middle">SÍ</text>

  <line x1="122" y1="74" x2="122" y2="98" stroke="#EF4444" stroke-width="2"/>
  <polygon points="122,98 117,90 127,90" fill="#EF4444"/>

  <!-- Paso 2 -->
  <rect x="270" y="18" width="205" height="56" rx="6" fill="#0B1926" stroke="#38BDF8" stroke-width="1.5"/>
  <text x="372" y="42" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#38BDF8" text-anchor="middle">2. TU FICHA (H1)</text>
  <text x="372" y="60" font-size="9.5" fill="#94A3B8" text-anchor="middle">¿Los 8 campos completos?</text>

  <line x1="475" y1="46" x2="515" y2="46" stroke="#00DC82" stroke-width="2.5"/>
  <polygon points="515,46 507,41 507,51" fill="#00DC82"/>
  <text x="495" y="38" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#00DC82" text-anchor="middle">SÍ</text>

  <line x1="372" y1="74" x2="372" y2="98" stroke="#EF4444" stroke-width="2"/>
  <polygon points="372,98 367,90 377,90" fill="#EF4444"/>

  <!-- Paso 3 -->
  <rect x="520" y="18" width="220" height="56" rx="6" fill="#0A231C" stroke="#00DC82" stroke-width="2"/>
  <text x="630" y="42" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#00DC82" text-anchor="middle">3. EJECUCIÓN EN MT5</text>
  <text x="630" y="60" font-size="9.5" font-weight="600" fill="#A7F3D0" text-anchor="middle">Lote 1% neto + 5 filtros</text>

  <!-- Botones Manos Quietas -->
  <rect x="42" y="98" width="160" height="26" rx="4" fill="#2A1215" stroke="#EF4444" stroke-width="1"/>
  <text x="122" y="115" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#F87171" text-anchor="middle">🛑 MANOS QUIETAS</text>

  <rect x="292" y="98" width="160" height="26" rx="4" fill="#2A1215" stroke="#EF4444" stroke-width="1"/>
  <text x="372" y="115" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#F87171" text-anchor="middle">🛑 MANOS QUIETAS</text>
</svg>
</div>

---

# 📖 MÓDULO 0 · Qué estás operando de verdad

**Pregunta que responde**: antes de arriesgar un peso, ¿qué ocurre exactamente cuando abro una operación?

---

## 0.1 · No compras el activo, compras un contrato

Cuando abres una operación en USD/CLP, Oro (XAU/USD) o Nasdaq 100 (US100), **no estás comprando lingotes en una bóveda ni acciones en Wall Street**. Estás firmando un **Contrato por Diferencia (CFD)** con tu broker: acuerdan intercambiar la diferencia entre el precio al que entras y el precio al que sales.

Consecuencia práctica: tu resultado depende del movimiento del precio y del costo del broker, no de ser dueño de nada.

## 0.2 · El apalancamiento es la parte que hace daño

Tu broker te permite mover un monto mucho mayor al que depositaste. Con apalancamiento 1:100, con $18.680 de garantía puedes mover una posición de $1.868.000 (equivalente a 0,02 lotes del contrato de USD/CLP; el contrato completo es 100.000 USD).

Eso corta para los dos lados, y de forma asimétrica en la práctica: **si tomas un tamaño demasiado grande para tu cuenta, un movimiento pequeño en contra te causa una pérdida severa muy rápido.** El **Módulo 7** existe para que eso no te pase, y es el módulo que más conviene no saltarse.

## 0.3 · Tres cosas que son tuyas y de nadie más

1. **La decisión de operar.** Nosotros publicamos el clima y el sesgo. Nada de eso es una orden de compra.
2. **El tamaño de la posición.** Nadie puede calcularlo por ti porque depende del capital de tu cuenta.
3. **El stop.** Si entras sin stop, no estás operando este método.

> [!IMPORTANT]
> **La regla que resume el manual entero**: el clima explica, tu ficha autoriza, el stop protege y el tamaño limita. Si un campo de tu ficha queda vacío, no hay orden.

---



## 0.4 · Expectativas estadísticas: qué esperar de este método

Un error común en traders principiantes es abandonar el método tras dos semanas sin señales en un activo o tras una racha de tres pérdidas consecutivas. La rentabilidad cuantitativa se basa en una **distribución estadística de esperanza matemática positiva**, no en ganar cada operación:

| Activo | Frecuencia de Señales Estimada | Tasa de Acierto (Win Rate) Esperada | Ratio Riesgo/Beneficio (R:R) Promedio | Horizonte Temporal Típico |
|---|---|---|---|---|
| **USD/CLP** | 2 a 4 señales / mes | 50 % – 55 % | 1,2 : 1 – 1,8 : 1 | 3 a 6 horas (Rueda Stgo) |
| **Oro (XAU/USD)** | 1 a 3 señales / mes | 42 % – 48 % | **2,5 : 1 – 4,0 : 1** (Trailing Exit) | 1 a 5 días hábiles |
| **WTI / Brent** | 2 a 5 señales / mes | 46 % – 52 % | 1,4 : 1 – 2,0 : 1 | 6 a 24 horas |
| **Nasdaq 100** | 3 a 6 señales / mes | 48 % – 54 % | 1,3 : 1 – 2,0 : 1 | 4 a 18 horas |

*Nota metodológica obligatoria: Estimaciones orientativas del Desk, no verificadas por backtest público reproducible. No constituyen proyección de rentabilidad.*

> [!NOTE]
> **La asimetría del Oro**: El Oro tiene una tasa de acierto más baja (~45 %), pero cuando captura una tendencia macro guiada por tasas reales y tensión geopolítica, su salida por trailing stop genera retornos de 3× a 5× el riesgo inicial, que buscan compensar las pérdidas controladas.

---

# 🕯️ MÓDULO 1 · El lenguaje del gráfico: la vela H1 cerrada

**Pregunta que responde**: ¿qué dato del gráfico es confiable y cuál me puede engañar?

---

## 1.1 · Cuerpo, mecha y cierre

Todo este método trabaja sobre velas de **1 hora (H1)**. Cada vela cuenta lo que pasó en esa hora con tres elementos:

<div class="contenedor-diagrama">
<svg viewBox="0 0 760 210" width="100%" height="210" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- LADO IZQUIERDO: Vela Alcista (Compra) -->
  <g transform="translate(40, 15)">
    <text x="120" y="18" font-family="'Goldman', sans-serif" font-size="12" font-weight="700" fill="#00DC82" text-anchor="middle">VELA ALCISTA (COMPRA)</text>
    
    <!-- Mechas y Cuerpo -->
    <line x1="120" y1="30" x2="120" y2="55" stroke="#00DC82" stroke-width="3"/>
    <rect x="85" y="55" width="70" height="85" rx="3" fill="#063223" stroke="#00DC82" stroke-width="2.5"/>
    <line x1="120" y1="140" x2="120" y2="175" stroke="#00DC82" stroke-width="3"/>

    <!-- Etiquetas a la izquierda -->
    <text x="70" y="34" font-size="10.5" font-weight="700" fill="#F8FAFC" text-anchor="end">Máximo (High)</text>
    <line x1="75" y1="30" x2="115" y2="30" stroke="#38BDF8" stroke-width="1" stroke-dasharray="2,2"/>

    <text x="70" y="62" font-size="10.5" font-weight="700" fill="#00DC82" text-anchor="end">Cierre (Close)</text>
    <line x1="75" y1="58" x2="85" y2="58" stroke="#00DC82" stroke-width="1.5"/>

    <text x="70" y="145" font-size="10.5" font-weight="700" fill="#94A3B8" text-anchor="end">Apertura (Open)</text>
    <line x1="75" y1="140" x2="85" y2="140" stroke="#94A3B8" stroke-width="1.5"/>

    <text x="70" y="179" font-size="10.5" font-weight="700" fill="#F8FAFC" text-anchor="end">Mínimo (Low)</text>
    <line x1="75" y1="175" x2="115" y2="175" stroke="#38BDF8" stroke-width="1" stroke-dasharray="2,2"/>

    <!-- Caja Explicativa de Cuerpo Verde -->
    <rect x="175" y="75" width="125" height="45" rx="4" fill="#0B1926" stroke="#1E293B" stroke-width="1"/>
    <text x="185" y="93" font-size="9" font-weight="700" fill="#00DC82">CUERPO VERDE</text>
    <text x="185" y="108" font-size="8.5" fill="#94A3B8">Cierre > Apertura</text>
  </g>

  <!-- Separador Vertical -->
  <line x1="380" y1="20" x2="380" y2="190" stroke="#1E293B" stroke-width="1.5" stroke-dasharray="4,4"/>

  <!-- LADO DERECHO: Vela Bajista (Venta) -->
  <g transform="translate(420, 15)">
    <text x="140" y="18" font-family="'Goldman', sans-serif" font-size="12" font-weight="700" fill="#F87171" text-anchor="middle">VELA BAJISTA (VENTA)</text>
    
    <!-- Caja Explicativa de Cuerpo Rojo (Simétrica a la izquierda de la vela roja) -->
    <rect x="0" y="75" width="125" height="45" rx="4" fill="#0B1926" stroke="#1E293B" stroke-width="1"/>
    <text x="10" y="93" font-size="9" font-weight="700" fill="#EF4444">CUERPO ROJO</text>
    <text x="10" y="108" font-size="8.5" fill="#94A3B8">Cierre &lt; Apertura</text>

    <!-- Mechas y Cuerpo -->
    <line x1="140" y1="30" x2="140" y2="55" stroke="#EF4444" stroke-width="3"/>
    <rect x="105" y="55" width="70" height="85" rx="3" fill="#320C10" stroke="#EF4444" stroke-width="2.5"/>
    <line x1="140" y1="140" x2="140" y2="175" stroke="#EF4444" stroke-width="3"/>

    <!-- Etiquetas a la derecha -->
    <text x="190" y="34" font-size="10.5" font-weight="700" fill="#F8FAFC" text-anchor="start">Máximo (High)</text>
    <line x1="145" y1="30" x2="185" y2="30" stroke="#38BDF8" stroke-width="1" stroke-dasharray="2,2"/>

    <text x="190" y="62" font-size="10.5" font-weight="700" fill="#94A3B8" text-anchor="start">Apertura (Open)</text>
    <line x1="175" y1="58" x2="185" y2="58" stroke="#94A3B8" stroke-width="1.5"/>

    <text x="190" y="145" font-size="10.5" font-weight="700" fill="#F87171" text-anchor="start">Cierre (Close)</text>
    <line x1="175" y1="140" x2="185" y2="140" stroke="#EF4444" stroke-width="1.5"/>

    <text x="190" y="179" font-size="10.5" font-weight="700" fill="#F8FAFC" text-anchor="start">Mínimo (Low)</text>
    <line x1="145" y1="175" x2="185" y2="175" stroke="#38BDF8" stroke-width="1" stroke-dasharray="2,2"/>
  </g>
</svg>
</div>

* **El cuerpo** es el rectángulo central: muestra la batalla real entre compradores y vendedores entre el inicio y el fin de esa hora.
* **Las mechas** son las líneas delgadas: muestran hasta dónde llegó el precio antes de ser rechazado.
* **El cierre** es el único dato que este método considera confiable.

## 1.2 · Por qué nunca se opera a mitad de hora

A las 10:20 una vela puede parecer una subida verde y contundente. A las 10:55 puede haberse revertido por completo y cerrar como una mecha de rechazo, contando la historia exactamente contraria.

**Todas las condiciones de este manual se evalúan sobre velas ya cerradas, al minuto :00.** No es una preferencia de estilo: una condición medida sobre una vela en formación puede darse y desaparecer en la misma hora, y entonces habrías entrado por una señal que nunca existió.

## 1.3 · Los seis indicadores que necesitas en pantalla (ocho líneas en pantalla: 3 EMA)

El método completo se lee con estos seis. El **Anexo A3** trae la instalación paso a paso.

| Indicador | Para qué lo usa el método | Módulo |
|---|---|---|
| **Canal Donchian de 50** | Define compresión y ruptura | M5 |
| **EMA 20, 50 y 100** (medias exponenciales) | Define tendencia y retrocesos | M5, M10 |
| **Bandas de Bollinger (20; 2σ)** | Define el rebote en rango y su objetivo | M5, M6 |
| **ATR de 14** (rango medio real) | Define el stop, el objetivo y el tamaño | M6, M7 |
| **ADX de 14** y **RSI de 14** | Deciden qué setup aplica y filtran extremos | M5 |

---

# 🌍 MÓDULO 2 · Por qué se mueve el dinero en el mundo

**Pregunta que responde**: ¿qué hay detrás de las reglas, para no aplicarlas de memoria?

---

Detrás de cada regla de este manual hay décadas de investigación económica. Estas seis analogías te dan el **porqué**. Ojo con una cosa: el porqué te ayuda a entender, **pero no autoriza a operar**. Para eso está tu ficha del Módulo 4.

### 1. La fábula de Ricitos de Oro

* **La metáfora**: la niña prueba tres platos de sopa. Uno está muy caliente, otro muy frío y el tercero está en el punto perfecto.
* **En economía**: es el clima soñado. La economía crece a paso firme (las fábricas producen y demandan cobre), pero la inflación está tranquila y las tasas no suben.
* **Qué implica**: es el mejor escenario para las acciones tecnológicas (Nasdaq 100) y para que el peso chileno se fortalezca, o sea sesgo bajista en USD/CLP.

### 2. El dilema del Oro y las tasas reales

* **La metáfora**: el Oro es refugio histórico, pero no paga dividendos, no genera intereses ni produce arriendos.
* **En economía**: si un bono del gobierno de EE.UU. protegido contra la inflación paga una tasa real atractiva, los grandes inversionistas prefieren cobrar ese interés antes que guardar metal en una bóveda. Cuando esa tasa real baja, o cuando aparece tensión bélica, el dinero vuelve al Oro.
* **Qué implica**: en climas de inflación o tensión geopolítica, **el método prohíbe apostar a la baja en Oro**.

### 3. Los dos tipos de subida del petróleo

* **La metáfora**: no todas las subidas del combustible significan lo mismo.
* **En economía**:
  1. **Sube por demanda sana**: el comercio mundial acelera, hay más transporte y barcos consumiendo. Las bolsas y el petróleo suben juntos.
  2. **Sube por miedo**: el crudo se dispara por temor a cortes de suministro. El combustible caro encarece los costos de las empresas y frena el consumo, castigando a las bolsas.
* **Qué implica**: **el cobre es el que distingue una de otra**, y de eso depende cuánto riesgo toma el método. Si el crudo sube y el cobre lo acompaña, es demanda real y se sigue la tendencia con posición completa. Si el crudo sube solo, se opera **a la mitad del tamaño** y con el stop más ceñido. Está en el Módulo 10.

> ### ⚖️ Petróleo y Oro: ni gemelos ni enemigos
> * Si el mundo produce más, el petróleo puede subir y el oro no.
> * Si hay guerra, a menudo suben los dos.
> * Si el petróleo sube y el banco central se pone duro, el oro puede bajar el mismo día.
> * **Eso no autoriza vender oro porque el crudo subió.** Solo operas si la ficha del Oro te lo permite.

### 4. La verdulería del cobre y el dólar en Chile

* **La metáfora**: más de la mitad de las exportaciones chilenas son cobre.
* **En economía**: si el cobre sube en Londres y Nueva York, las mineras reciben más dólares. Para pagar sueldos, proveedores e impuestos en Chile traen esos dólares a Santiago y compran pesos.
* **Qué implica**: mucha oferta de dólares en Santiago baja el tipo de cambio, o sea peso fuerte. Si el cobre se derrumba, el dólar en Chile tiende a subir con fuerza.

### 5. La carretera con lluvia

* **La metáfora**: en una autopista despejada puedes ir a 120 km/h con seguridad. Con lluvia torrencial y neblina bajas a 50 km/h para mantener **el mismo** nivel de seguridad.
* **En economía**: en el trading tu velocidad es el tamaño del lote.
* **Qué implica**: cuando la volatilidad se duplica, tu lote se reduce a la mitad. Y esto no lo tienes que recordar: **sale solo de la fórmula del Módulo 7**, porque el ATR entra en el denominador.

### 6. No adivinar techos ni pisos

* **La metáfora**: las tendencias macro son trenes de carga. Demoran en frenar mucho más de lo que la intuición cree.
* **Qué implica**: el método **prohíbe** apostar contra una tendencia macro sólida solo porque el precio "ya subió mucho". Un RSI en 80 no es una señal de venta si el clima manda lo contrario.

---

# 🌦️ MÓDULO 3 · Los 5 climas del mercado

**Pregunta que responde**: ¿en qué escenario estoy hoy, y qué me habilita o me prohíbe?

---

Cada mañana el mercado se clasifica en uno de cinco climas, evaluando datos oficiales de tasas, inflación esperada, curva de bonos y cobre. **Este es el insumo que nosotros publicamos**, y el que ordena todo lo demás.

| Clima | Código técnico | Qué pasa en la economía | Qué suele ir mejor o peor | Qué te está prohibido |
|---|---|---|---|---|
| 🌪️ **Tormenta** | `R3_ESTANFLACION_SHOCK` | El petróleo y las tasas suben con fuerza por tensión geopolítica o recortes de oferta | Oro y petróleo firmes *(si las tasas reales pegan muy fuerte, el oro puede no acompañar)*; acciones bajo presión; USD/CLP al alza | **Vender Oro.** Comprar acciones sin confirmación |
| 🛒 **Inflación** | `R1_SHOCK_INFLACIONARIO` | Las expectativas de inflación suben más rápido que el crecimiento | Oro firme; dólar global firme; cautela en bolsas | Operar contra la subida de tasas |
| 📉 **Recesión** | `R4_RECESION_VUELO_CALIDAD` | El cobre se derrumba y la curva de bonos anticipa enfriamiento | Fuerte alza en USD/CLP (peso débil); materias primas en caída | **Apostar a la baja en USD/CLP** |
| ☀️ **Día bueno** | `R2_GOLDILOCKS_EXPANSION` | El cobre sube con tasas e inflación estables | Subidas en Nasdaq 100; USD/CLP a la baja (peso fuerte) | Vender acciones en tendencia |
| 🏖️ **Calma** | `R0_CALMA_RANGO` | Variables en equilibrio, sin noticias graves ni tendencias desatadas | El precio rebota ordenado entre soportes y resistencias | **Perseguir rupturas.** Solo rebotes |

## 3.1 · La regla de los dos días

El clima **no cambia por un solo día raro** ni por una noticia pasajera. El nuevo escenario tiene que repetirse **dos días hábiles seguidos** antes de confirmarse.

**La excepción**: si un dato supera el **150 % de su umbral** (por ejemplo, petróleo con Δ5d ≤ -5,25% gatilla evaluación inmediata de R4; +5,25%, de R3), el clima cambia de inmediato, sin esperar el segundo día. Es la protección ante un evento extremo.

## 3.2 · Cuando dos climas se activan a la vez

Puede pasar, y hay un orden de precedencia fijo. Gana el de mayor riesgo:

**Tormenta (R3) → Inflación (R1) → Recesión (R4) → Día bueno (R2) → Calma (R0)**

## 3.3 · El clima manda sobre el activo

Esta es la jerarquía que más cuesta respetar y la que más protege:

> Si el clima es Tormenta o Recesión, el sesgo del USD/CLP **sigue siendo alcista** aunque el cobre suba un 2 % ese día puntual. El cobre solo desempata cuando el clima es Calma.

Los umbrales numéricos exactos de cada clima están en el **Anexo A2**, para que puedas verificar la clasificación por tu cuenta.

## 3.4 · Cuando el clima no se puede leer

Dos estados en los que **no se opera**, y conviene reconocerlos:

* **`DATOS_INCOMPLETOS`**: falta un dato de entrada, así que no hay sesgo ni setups habilitados. La lista de setups permitidos viene vacía. No es un sesgo neutral: es la ausencia de lectura.
* **Confianza bajo 51,0 % (Umbral maestro A2)**: el modelo audita la frescura y la cobertura de sus propios datos. Bajo ese umbral el activo **no se comunica ni se opera** (mínimo 51,0 %, inclusive), porque significa que falta un dato o la lectura está degradada.

En los dos casos la respuesta es la misma: ese día ese activo no se opera.

---

## 3.5 · Histéresis de salida del régimen

Un clima deja de estar vigente cuando su condición principal NO se cumple durante 2 días hábiles seguidos. La entrada y la salida usan la misma regla de 2 días; solo la salida requiere ausencia (no presencia) de umbral.

---

# 🎫 MÓDULO 4 · Tu ficha de operación

**Pregunta que responde**: ¿cómo paso del clima a una orden concreta, sin improvisar?

---

Este es el módulo central del manual. Una **ficha** es una hoja con **ocho campos**. Si los ocho están completos y ninguno viola una regla, tienes una operación. Si uno queda vacío o en conflicto, no la tienes.

La armas tú, con el clima que publicamos y el gráfico que tienes en pantalla.

## 4.1 · Los ocho campos

| # | Campo | De dónde lo sacas | Módulo |
|---|---|---|---|
| 1 | **Activo** | Uno de los cinco con ficha: USD/CLP, Oro, WTI, Brent, Nasdaq 100 | M10 |
| 2 | **Clima confirmado** | Lo publicamos a diario. Verificable en el Anexo A2 | M3 |
| 3 | **Dirección permitida** | El clima define si puedes comprar, vender, o solo operar rango | M10 |
| 4 | **Setup activado** | Lo lees del gráfico sobre la vela H1 ya cerrada | M5 |
| 5 | **Precio de entrada** | Lo define el setup | M5 |
| 6 | **Stop loss** | Regla del mínimo de 20 velas o 1,5 × ATR | M6 |
| 7 | **Objetivo y relación riesgo/beneficio** | 1,0 y 1,5 × ATR, o la media central en rango | M6 |
| 8 | **Volumen en lotes** | Del 1 % de tu capital y la distancia al stop | M7 |

## 4.2 · El semáforo lo determinas tú

Al terminar de llenar la ficha, tu operación queda en uno de estos cuatro estados. **Los cuatro son resultados legítimos**, y tres de ellos significan no operar:

<div class="contenedor-diagrama">
<svg viewBox="0 0 760 175" width="100%" height="175" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Tarjeta 1: Verde -->
  <g transform="translate(15, 12)">
    <rect width="170" height="150" rx="6" fill="#0A231C" stroke="#00DC82" stroke-width="1.5"/>
    <circle cx="26" cy="26" r="10" fill="#00DC82"/>
    <text x="26" y="30" font-size="11" font-weight="800" fill="#060F19" text-anchor="middle">✓</text>
    <text x="44" y="30" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#00DC82">VERDE</text>
    <text x="14" y="56" font-size="9" font-weight="700" fill="#A7F3D0">Los 8 campos listos</text>
    <text x="14" y="74" font-size="8.2" fill="#94A3B8">Vela H1 cerrada.</text>
    <text x="14" y="88" font-size="8.2" fill="#94A3B8">Filtros aprobados.</text>
    <rect x="10" y="106" width="150" height="32" rx="4" fill="#00DC82"/>
    <text x="85" y="126" font-family="'Goldman', sans-serif" font-size="9" font-weight="800" fill="#060F19" text-anchor="middle">INGRESAR EN MT5</text>
  </g>

  <!-- Tarjeta 2: Amarillo -->
  <g transform="translate(200, 12)">
    <rect width="170" height="150" rx="6" fill="#261A08" stroke="#F59E0B" stroke-width="1.5"/>
    <circle cx="26" cy="26" r="10" fill="#F59E0B"/>
    <text x="26" y="30" font-size="10" font-weight="800" fill="#060F19" text-anchor="middle">⏳</text>
    <text x="44" y="30" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#F59E0B">AMARILLO</text>
    <text x="14" y="56" font-size="9" font-weight="700" fill="#FDE68A">Setup sin gatillo</text>
    <text x="14" y="74" font-size="8.2" fill="#94A3B8">El clima habilita,</text>
    <text x="14" y="88" font-size="8.2" fill="#94A3B8">la vela aún no gatilla.</text>
    <rect x="10" y="106" width="150" height="32" rx="4" fill="#D97706"/>
    <text x="85" y="126" font-family="'Goldman', sans-serif" font-size="9" font-weight="800" fill="#FFFFFF" text-anchor="middle">ESPERAR EL :00</text>
  </g>

  <!-- Tarjeta 3: Blanco -->
  <g transform="translate(385, 12)">
    <rect width="170" height="150" rx="6" fill="#0B1926" stroke="#475569" stroke-width="1.5"/>
    <circle cx="26" cy="26" r="10" fill="#64748B"/>
    <text x="26" y="30" font-size="10" font-weight="800" fill="#060F19" text-anchor="middle">○</text>
    <text x="44" y="30" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#94A3B8">BLANCO</text>
    <text x="14" y="56" font-size="9" font-weight="700" fill="#CBD5E1">Sin setup aplicable</text>
    <text x="14" y="74" font-size="8.2" fill="#64748B">El clima y la</text>
    <text x="14" y="88" font-size="8.2" fill="#64748B">estructura no calzan.</text>
    <rect x="10" y="106" width="150" height="32" rx="4" fill="#334155"/>
    <text x="85" y="126" font-family="'Goldman', sans-serif" font-size="8.5" font-weight="800" fill="#FFFFFF" text-anchor="middle">MERCADO NO OPERABLE</text>
  </g>

  <!-- Tarjeta 4: Rojo -->
  <g transform="translate(570, 12)">
    <rect width="170" height="150" rx="6" fill="#280D12" stroke="#EF4444" stroke-width="1.5"/>
    <circle cx="26" cy="26" r="10" fill="#EF4444"/>
    <text x="26" y="30" font-size="10" font-weight="800" fill="#FFFFFF" text-anchor="middle">✕</text>
    <text x="44" y="30" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#EF4444">ROJO</text>
    <text x="14" y="56" font-size="9" font-weight="700" fill="#FCA5A5">Filtro bloquea</text>
    <text x="14" y="74" font-size="8.2" fill="#94A3B8">Spread alto, blackout,</text>
    <text x="14" y="88" font-size="8.2" fill="#94A3B8">o contra clima macro.</text>
    <rect x="10" y="106" width="150" height="32" rx="4" fill="#DC2626"/>
    <text x="85" y="126" font-family="'Goldman', sans-serif" font-size="9" font-weight="800" fill="#FFFFFF" text-anchor="middle">PROHIBIDO OPERAR</text>
  </g>
</svg>
</div>

**La diferencia entre amarillo y blanco importa.** Amarillo significa que el setup está identificado y esperas el gatillo: te quedas mirando ese activo. Blanco significa que ningún setup aplica hoy, así que ese activo se cierra y no vuelves a mirarlo.

## 4.3 · Una ficha completa, de ejemplo

Los números son de un ejemplo didáctico, no de un día real. **Tus cifras salen siempre de tu plataforma.**

| Campo | Valor | Regla que lo produjo |
|---|---|---|
| Activo | USD/CLP | (tu elección) |
| Clima confirmado | Recesión (R4), 2º día | M3 |
| Dirección permitida | Solo compra de dólar | M10 |
| Setup activado | Ruptura por compresión | M5.1 |
| Entrada | `BUY_STOP` en 934,00 · vence en 2 velas | M5.1 |
| Stop loss | 930,48 (1,5 × ATR de 2,35) | M6.1 |
| Objetivo | TP1 936,35 · TP2 937,53 · R:R 0,67 | M6.2 |
| Volumen | **No se opera** | M6.3 |

> [!IMPORTANT]
> **El ejemplo termina en "no se opera" a propósito.** Con un stop de 3,52 pesos y un primer objetivo a 2,35 pesos, la relación riesgo/beneficio da 0,67: por debajo del mínimo de 1,0. La ficha estaba casi completa y el filtro la detuvo en el último campo.
>
> Eso ocurre seguido y es la parte del método que protege la cuenta. Una ficha que llega al campo 7 y se cae **no es trabajo perdido**: es el trabajo funcionando.

---



<div style="break-before: page;"></div>

## 4.4 · Caso de estudio: La "Pérdida Perfecta" (Trade de Libro)

Para entender la disciplina operativa, veamos un caso real de ejecución impecable donde la operación resulta en pérdida monetaria controlada.

### 1. Entorno Macro y Autorización
* **Clima**: **Tormenta (R3), 2º día confirmado**. WTI Δ5d = +4,1% (umbral 3,5%), Bono US10Y = +12 bps (umbral 10 bps). Confianza publicada: **78%** (≥ 51,0% maestro ✓).
* **Activo y Dirección**: **USD/CLP, solo compra** (M10.1 en R3 fija sesgo +0,80, dirección permitida compra ✓).

### 2. Gatillo Técnico y Filtros (H1)
* **Setup 5.1 (Ruptura Donchian)**: Canal Donchian 50 con ancho de 2,1 × ATR (máximo permitido 2,5 × ATR ✓). ATR(14) en H1 oficial: **2,41 CLP**. Vela H1 cierra en **934,20** rompiendo el techo con cuerpo del 68% ≥ 50% ✓, rango de vela 1,3 × ATR ≥ 1,0 ✓, RSI(14) en **58** (≤ 75 ✓).
* **Filtro 8.4 (Confirmación Cruzada)**: Clima R3 aprueba compras automáticamente (verde ✓).
* **Orden**: `BUY_STOP` en **934,00** (máximo de la vela de señal), vencimiento 2 velas H1. Se activa con **cero deslizamiento** (slippage cap admisible 0,2 × 2,41 = 0,482 ✓).

### 3. Geometría y Dimensionamiento Neto (M6 y M7)
* **Stop Loss (M6.1, Rama A)**: Swing estructural de 20 velas en **932,07**. Distancia = 934,00 - 932,07 = 1,93 CLP = 0,80 × ATR (dentro de la banda 0,5–1,5 × ATR ✓).
* **Objetivos**: TP1 = 934,00 + (1,0 × 2,41) = 936,41; TP2 = 934,00 + (1,5 × 2,41) = 937,62.
* **Ratio Riesgo/Beneficio**: R:R = 2,41 / 1,93 = **1,25 ≥ 1,0** ✓.
* **Presupuesto de Riesgo Neto (Cuenta $1.000.000 CLP)**:
  * Presupuesto total (1,00%): $10.000 CLP.
  * Presupuesto neto precio (90%): $9.000 CLP.
  * Lote teórico = 9.000 / (1,93 × 100.000) = 0,0466 → **Redondeo hacia abajo = 0,04 lotes**.
  * Pérdida máxima en precio stop = 0,04 × 1,93 × 100.000 = **$7.720 CLP**.

### 4. Fricción y Margen
* **Filtro de Spread (8.1)**: Tope 15% del stop = 0,29 CLP. Spread real en ejecución = 0,25 CLP ✓. Costo spread = 0,25 × 100.000 × 0,04 = $1.000 CLP. Comisión broker = $60 CLP. Fricción total = **$1.060 CLP**.
* **Margen Requerido (7.6)**: (0,04 × 100.000 × 935,60) / 100 = $37.424 CLP (3,74% del margen libre ≤ 30% ✓).

### 5. Resultado y Dictamen de Auditoría
A las 2 horas de abierta la posición, una conferencia imprevista de prensa macroeconómica aprecia temporalmente al peso chileno y el precio toca el stop en 932,07.
* **Pérdida total liquidada**: $7.720 + $1.060 = **$8.780 CLP = 0,88% de la cuenta** (estrictamente bajo el presupuesto objetivo del 1,00% ✓).
* **Dictamen**: La operación fue perdedora en dinero pero **perfecta en procedimiento**. Este proceso, aplicado con disciplina estadística, **está diseñado para** producir una curva de capital creciente en series largas; ninguna serie corta lo garantiza.

> [!TIP]
> **Verificado contra las reglas de este manual — pasa 6/6 filtros**. La pérdida quedó contenida exactamente dentro de los límites del presupuesto institucional.

---

<div style="break-before: page;"></div>

# 📐 MÓDULO 5 · Los tres setups

**Pregunta que responde**: ¿qué tiene que hacer el precio para que yo tenga permiso de entrar?

---

El método usa **tres setups y ninguno más**, todos sobre velas H1 cerradas. Son **mutuamente excluyentes**: en cada momento aplica uno solo, y hay un orden para decidir cuál.

## 5.0 · Primero decides cuál aplica: Matriz Clima × Setup

No eliges el setup que más te gusta. El **clima macroeconómico es el primer filtro jerárquico**: decide qué tipo de microestructura tenemos antes de tocar cualquier indicador técnico.

### Matriz de Permisos: Clima Macro × Setup Técnico

| Clima Macro Vigente | Ruptura por Compresión (5.1) | Retroceso al Promedio (5.2) | Rebote en Rango (5.3) |
|---|---|---|---|
| 🌪️ **Tormenta (R3)** | **Habilitado** (1º Orden) | **Habilitado** (2º Orden si ADX ≥ 20) | ⛔ **PROHIBIDO** |
| 🛒 **Inflación (R1)** | **Habilitado** (1º Orden) | **Habilitado** (2º Orden si ADX ≥ 20) | ⛔ **PROHIBIDO** |
| 📉 **Recesión (R4)** | **Habilitado** (1º Orden) | **Habilitado** (2º Orden si ADX ≥ 20) | ⛔ **PROHIBIDO** |
| ☀️ **Día bueno (R2)** | **Habilitado** (1º Orden) | **Habilitado** (2º Orden si ADX ≥ 20) | ⛔ **PROHIBIDO** |
| 🏖️ **Calma (R0)** | ⛔ **PROHIBIDO** | ⛔ **PROHIBIDO** | **Habilitado** (Único si ADX < 20) |

### Árbol de Precedencia Estricta

1. **Si el Clima es Calma (R0)**:
   * Evalúa **Rebote en Rango (5.3)**: ¿ADX < 20 y RSI extremo fuera de bandas? → Si cumple, se opera. Si ADX ≥ 20, **NO se opera** (es ruido transitorio sin tendencia macro).
2. **Si el Clima es Tendencial (R1, R2, R3, R4)**:
   * 1º **Ruptura por compresión (5.1)**: ¿Ancho Donchian 50 ≤ 2,5 × ATR y vela cerrada afuera? → Si cumple, se coloca orden STOP.
   * 2º **Retroceso al promedio (5.2)**: ¿EMAs 20/50/100 alineadas y ADX ≥ 20? → Si cumple, se coloca orden STOP en rebote.
3. **Si ninguno califica**: **Esperar con manos quietas.** Es el resultado más frecuente y protege tu capital.

<div style="break-before: page;"></div>

## 5.1 · Ruptura por compresión

*El precio estaba apretado y cerró afuera.*

* **Cuándo aplica**: Climas con tendencia (**Tormenta, Inflación, Recesión o Día bueno**). **Prohibido en Calma.**
* **Qué busca**: El precio estuvo comprimido en un rango estrecho las últimas 50 horas y una vela H1 **cierra fuera** del canal.
* **Las cuatro condiciones, todas obligatorias**:
  1. El **cierre** queda sobre el techo del canal Donchian 50 (en compras) o bajo el piso (en ventas).
  2. **Regla del cuerpo**: El cuerpo mide **al menos la mitad (50 % o más)** del total de la vela. No sirve una mecha larga con cuerpo chico.
  3. **Rango de la vela igual o mayor a 1,0 × ATR**: La vela de ruptura tiene que ser al menos de tamaño normal. Una ruptura con una vela diminuta no tiene fuerza detrás.
  4. **RSI no extremo**: En compras el RSI va en 75 o menos; en ventas, en 25 o más. Entrar en un extremo es comprar el final del movimiento.
* **Entrada**: Orden pendiente `BUY_STOP` en el **máximo de esa vela** (o `SELL_STOP` en el mínimo), con **vencimiento a 2 velas H1**. Si no se activa en dos horas, se cancela.
* **Regla de Tolerancia de Deslizamiento (Slippage Cap)**: Al activarse la orden `BUY_STOP` o `SELL_STOP`, verifica el precio real de llenado (*fill price*). Si el deslizamiento desfavorable del fill supera **0,2 × ATR**, la operación se cancela/cierra de inmediato a mercado sin abrir la posición (cuando el stop es 1,5 × ATR, 0,2 × ATR equivale aproximadamente al 13 % de la distancia al stop). Un deslizamiento excesivo distorsiona la relación riesgo/beneficio y amplifica la pérdida real fuera de presupuesto.

<div class="contenedor-diagrama">
<svg viewBox="0 0 760 210" width="100%" height="210" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Canales Donchian 50 (Compresión previa) -->
  <line x1="30" y1="80" x2="730" y2="80" stroke="#38BDF8" stroke-width="2" stroke-dasharray="6,4"/>
  <text x="35" y="72" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#38BDF8">TECHO DONCHIAN 50</text>

  <rect x="30" y="80" width="280" height="85" fill="rgba(56, 189, 248, 0.04)" stroke="none"/>
  <line x1="30" y1="165" x2="730" y2="165" stroke="#38BDF8" stroke-width="2" stroke-dasharray="6,4"/>
  <text x="35" y="180" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#38BDF8">PISO DONCHIAN 50</text>

  <!-- Acotación de Compresión -->
  <line x1="55" y1="83" x2="55" y2="162" stroke="#94A3B8" stroke-width="1.5"/>
  <polygon points="55,83 51,90 59,90" fill="#94A3B8"/>
  <polygon points="55,162 51,155 59,155" fill="#94A3B8"/>
  <rect x="70" y="106" width="145" height="34" rx="4" fill="#0B1926" stroke="#1E293B" stroke-width="1"/>
  <text x="78" y="121" font-size="8.5" font-weight="700" fill="#CBD5E1">Ancho ≤ 2,5 × ATR</text>
  <text x="78" y="133" font-size="7.5" font-weight="600" fill="#64748B">(Compresión previa)</text>

  <!-- Velas de Rango previo -->
  <g transform="translate(230, 95)">
    <line x1="12" y1="8" x2="12" y2="48" stroke="#64748B" stroke-width="2"/>
    <rect x="5" y="18" width="14" height="20" rx="1" fill="#1E293B" stroke="#64748B" stroke-width="1.5"/>
    <line x1="35" y1="5" x2="35" y2="52" stroke="#00DC82" stroke-width="2"/>
    <rect x="28" y="15" width="14" height="25" rx="1" fill="#063223" stroke="#00DC82" stroke-width="1.5"/>
  </g>

  <!-- Vela H1 de Ruptura Alcista -->
  <g transform="translate(315, 18)">
    <!-- Mecha superior -->
    <line x1="35" y1="12" x2="35" y2="25" stroke="#00DC82" stroke-width="3"/>
    <!-- Cuerpo de la vela (rompe sobre Techo Donchian en y=62 relativo) -->
    <rect x="18" y="25" width="34" height="85" rx="2" fill="#063223" stroke="#00DC82" stroke-width="2.5"/>
    <!-- Mecha inferior -->
    <line x1="35" y1="110" x2="35" y2="125" stroke="#00DC82" stroke-width="3"/>

    <!-- Anotaciones de la vela de ruptura -->
    <rect x="-35" y="132" width="140" height="34" rx="4" fill="#0A1624" stroke="#1E293B" stroke-width="1"/>
    <text x="35" y="145" font-size="8.5" font-weight="700" fill="#00DC82" text-anchor="middle">1. Cierre H1 SOBRE techo</text>
    <text x="35" y="158" font-size="7.8" font-weight="600" fill="#94A3B8" text-anchor="middle">2. Cuerpo ≥ 50% | Rango ≥ 1 ATR</text>
  </g>

  <!-- Orden BUY_STOP y Reglas SSOT -->
  <line x1="350" y1="30" x2="420" y2="30" stroke="#00DC82" stroke-width="2" stroke-dasharray="4,3"/>
  <rect x="420" y="16" width="310" height="28" rx="4" fill="#0A281E" stroke="#00DC82" stroke-width="1.5"/>
  <text x="430" y="34" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#00DC82">BUY_STOP en el máximo (vence 2 velas H1)</text>

  <rect x="420" y="52" width="310" height="74" rx="4" fill="#0B1926" stroke="#1E293B" stroke-width="1"/>
  <text x="430" y="70" font-size="9" font-weight="700" fill="#F8FAFC">✓ Cierre fuera con vela cerrada (:00)</text>
  <text x="430" y="88" font-size="9" font-weight="700" fill="#38BDF8">✓ RSI(14) ≤ 75 en compras (sin agotamiento)</text>
  <text x="430" y="106" font-size="9" font-weight="700" fill="#F59E0B">✓ Slippage Cap admisible ≤ 0,2 × ATR</text>
</svg>
</div>

<div style="break-before: page;"></div>

## 5.2 · Retroceso al promedio

*El precio descansó sobre su media y volvió a retomar.*

* **Cuándo aplica**: Mercados con **clima tendencial activo (R1, R2, R3 o R4)** y con **ADX en 20 o más**. **Estrictamente prohibido en clima Calma (R0)**, donde un pico transitorio de ADX suele ser un engaño de noticias sin momentum estructural.
* **Las tres condiciones, todas obligatorias**:
  1. **Las tres medias alineadas**: En compras, EMA 20 sobre EMA 50 sobre EMA 100. En ventas, al revés. Sin esa alineación no hay tendencia que respaldar.
  2. El **mínimo** de la vela toca o perfora la EMA 20 (en compras).
  3. El **cierre** queda sobre la EMA 20. El precio la perforó durante la hora, pero los compradores la recuperaron antes del cierre.
* **Entrada**: `BUY_STOP` en el **máximo de la vela de rebote**, vencimiento a 2 velas H1.
* **Retroceso a EMA 50**: El 'Retroceso a EMA 50' citado en M10 es el mismo setup 5.2 evaluado sobre la EMA 50 con las tres condiciones trasladadas (tendencia previa, rechazo en mecha y confirmación de cierre); el stop loss usa la misma regla cuantitativa de M6.1 medida desde el precio de entrada.

<div class="contenedor-diagrama">
<svg viewBox="0 0 760 210" width="100%" height="210" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Medias Móviles Exponenciales -->
  <path d="M 30 145 Q 220 115 440 70 T 720 35" fill="none" stroke="#00DC82" stroke-width="3"/>
  <text x="735" y="32" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#00DC82" text-anchor="end">EMA 20</text>

  <path d="M 30 165 Q 220 138 440 95 T 720 60" fill="none" stroke="#38BDF8" stroke-width="2.5"/>
  <text x="735" y="58" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#38BDF8" text-anchor="end">EMA 50</text>

  <path d="M 30 185 Q 220 160 440 120 T 720 85" fill="none" stroke="#94A3B8" stroke-width="2"/>
  <text x="735" y="83" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#94A3B8" text-anchor="end">EMA 100</text>

  <!-- Vela de Rebote en EMA 20 -->
  <g transform="translate(160, 15)">
    <line x1="40" y1="15" x2="40" y2="35" stroke="#00DC82" stroke-width="3"/>
    <rect x="25" y="35" width="30" height="40" rx="2" fill="#063223" stroke="#00DC82" stroke-width="2.5"/>
    <line x1="40" y1="75" x2="40" y2="105" stroke="#00DC82" stroke-width="3"/>

    <!-- Anotaciones de la vela con fondo oscuro protector -->
    <rect x="-35" y="125" width="150" height="36" rx="4" fill="#0A1624" stroke="#1E293B" stroke-width="1"/>
    <text x="40" y="139" font-size="9" font-weight="700" fill="#00DC82" text-anchor="middle">1. Mecha perfora EMA 20</text>
    <text x="40" y="153" font-size="9" font-weight="700" fill="#00DC82" text-anchor="middle">2. Cierre recupera SOBRE ella</text>

    <!-- Orden BUY_STOP -->
    <line x1="40" y1="15" x2="135" y2="15" stroke="#00DC82" stroke-width="2" stroke-dasharray="3,3"/>
    <rect x="135" y="3" width="245" height="28" rx="4" fill="#0A281E" stroke="#00DC82" stroke-width="1.5"/>
    <text x="145" y="21" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#00DC82">BUY_STOP en el máximo (vence 2h)</text>

    <!-- Reglas Obligatorias -->
    <rect x="135" y="41" width="245" height="54" rx="4" fill="#0B1926" stroke="#1E293B" stroke-width="1"/>
    <text x="145" y="61" font-size="9.5" font-weight="700" fill="#F8FAFC">✓ EMAs alineadas (20 > 50 > 100)</text>
    <text x="145" y="79" font-size="9" font-weight="700" fill="#38BDF8">✓ ADX ≥ 20 en clima tendencial</text>
  </g>
</svg>
</div>

<div style="break-before: page;"></div>

## 5.3 · Rebote en rango

*El precio se salió de la banda y volvió a entrar.*

* **Cuándo aplica**: **Exclusivamente en clima Calma (R0)**, y con **ADX menor a 20**. Prohibido en cualquier clima tendencial.
* **Las tres condiciones, todas obligatorias**:
  1. La vela **anterior** cerró **fuera** de la banda de Bollinger, bajo la inferior en compras.
  2. La vela **actual** cierra **de regreso adentro**.
  3. El **RSI** marca extremo: **bajo 35** en compras, **sobre 65** en ventas. Los dos lados tienen umbral.
* **Entrada**: `BUY_LIMIT` en el **precio de cierre** de la vela que reingresó. Es orden límite y no a mercado.
* **Vencimiento y colocabilidad en MT5**: Vencimiento: 2 velas H1. Si el nivel queda por encima del precio actual, MT5 no permite colocar la BUY_LIMIT: trátala como no colocable y espera la siguiente vela elegible.
* **Objetivo obligatorio**: La **media central de las bandas** (SMA 20). Nada más lejos. En un mercado lateral, buscar objetivos amplios es pedirle al precio algo que en rango no hace.

<div class="contenedor-diagrama">
<svg viewBox="0 0 760 200" width="100%" height="200" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Bandas de Bollinger -->
  <line x1="30" y1="35" x2="730" y2="35" stroke="#00DC82" stroke-width="2.5"/>
  <text x="730" y="28" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#00DC82" text-anchor="end">MEDIA CENTRAL (SMA 20)</text>
  <text x="730" y="48" font-size="8.5" font-weight="700" fill="#A7F3D0" text-anchor="end">Objetivo Obligatorio</text>

  <line x1="30" y1="115" x2="730" y2="115" stroke="#F59E0B" stroke-width="2" stroke-dasharray="4,4"/>
  <text x="730" y="110" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#F59E0B" text-anchor="end">BANDA INFERIOR</text>

  <!-- Vela 1: Cierra afuera -->
  <g transform="translate(120, 20)">
    <line x1="20" y1="75" x2="20" y2="90" stroke="#EF4444" stroke-width="2"/>
    <rect x="5" y="90" width="30" height="35" rx="2" fill="#320C10" stroke="#EF4444" stroke-width="2"/>
    <line x1="20" y1="125" x2="20" y2="140" stroke="#EF4444" stroke-width="2"/>
    <text x="20" y="158" font-size="9.5" font-weight="700" fill="#F87171" text-anchor="middle">1. Cierra afuera</text>
  </g>

  <!-- Vela 2: Reingresa adentro -->
  <g transform="translate(220, 20)">
    <line x1="20" y1="45" x2="20" y2="60" stroke="#00DC82" stroke-width="2.5"/>
    <rect x="5" y="60" width="30" height="45" rx="2" fill="#063223" stroke="#00DC82" stroke-width="2.5"/>
    <line x1="20" y1="105" x2="20" y2="125" stroke="#00DC82" stroke-width="2.5"/>
    <text x="20" y="158" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#00DC82" text-anchor="middle">2. Reingresa (Gatillo)</text>
  </g>

  <!-- Panel de Entrada BUY_LIMIT -->
  <g transform="translate(320, 48)">
    <rect x="0" y="0" width="260" height="82" rx="6" fill="#0B1926" stroke="#00DC82" stroke-width="1.5"/>
    <text x="16" y="25" font-family="'Goldman', sans-serif" font-size="10.5" font-weight="700" fill="#00DC82">BUY_LIMIT en el cierre</text>
    <text x="16" y="47" font-size="9" font-weight="600" fill="#94A3B8">✓ RSI en zona de sobreventa (&lt; 35)</text>
    <text x="16" y="67" font-size="9" font-weight="700" fill="#F59E0B">✓ Exige Clima Calma (R0) y ADX &lt; 20</text>
  </g>
</svg>
</div>

<div style="break-before: page;"></div>

# 🛡️ MÓDULO 6 · El stop y el objetivo

**Pregunta que responde**: ¿dónde pongo el stop y hasta dónde aspiro, sin inventar?

---

## 6.1 · El stop: dos reglas, en este orden

Aquí hay una idea que conviene entender antes que la mecánica. **El stop no se pone donde te duele menos: se pone donde la operación deja de tener sentido.** Un stop muy pegado al precio te saca por ruido normal; uno muy lejano te hace perder más de lo presupuestado.

El método resuelve esa tensión con una regla determinista de dos pasos:

<!-- TOKEN_ALGORITMO_STOP_LOSS -->

**La lógica de la banda de aceptación**: un swing real es el mejor stop posible, porque es un nivel que el mercado ya respetó. Pero solo si su distancia es razonable. Si el swing está demasiado cerca (menos de 0,5 ATR) te saca el primer movimiento aleatorio; si está demasiado lejos (más de 1,5 ATR) rompe tu presupuesto de riesgo. Cuando el swing no cae en esa banda, se usa la distancia fija por volatilidad.

> [!CAUTION]
> **No uses el mínimo de la vela de señal.** Es un error frecuente y caro. Ese mínimo suele estar mucho más cerca que 1,5 × ATR, y eso produce dos daños a la vez: te saca del trade por ruido normal **y** te hace calcular un lote mucho más grande del que corresponde, porque el lote es inversamente proporcional a la distancia al stop (Módulo 7).
>
> El stop de este método es el de las 20 velas o el de 1,5 × ATR. Nada más.

## 6.2 · El objetivo depende del tipo de mercado

| Tipo de operación | Primer objetivo | Segundo objetivo |
|---|---|---|
| **Tendencia** (ruptura y retroceso) | entrada + **1,0 × ATR** | entrada + **1,5 × ATR** |
| **Rango** (rebote en calma) | la **media central** de las bandas | no lleva |
| **Tendencia sostenida** (ver 6.4) | **sin objetivo fijo** | se arrastra el stop |

En ventas se resta en vez de sumar. El ATR es siempre el de 14 períodos en H1, el mismo con el que calculaste el stop.

## 6.3 · El filtro que cierra el módulo: riesgo/beneficio mínimo 1,0

Con el stop y el primer objetivo ya puestos, calculas:

<div class="caja-formula" style="border-left-color: #38BDF8;">
  <div class="caja-formula-titulo">📐 Cálculo de la Relación Riesgo / Beneficio (R:R)</div>
  <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; text-align: center; margin-top: 1mm;">
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:1.5mm; border-radius:4px;">
      <div style="font-size:7.5pt; color:#64748B; font-weight:700;">RIESGO INICIAL</div>
      <div style="font-family:'Space Grotesk', monospace; font-weight:700; color:#EF4444; font-size:8.5pt;">| Entrada − Stop |</div>
    </div>
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:1.5mm; border-radius:4px;">
      <div style="font-size:7.5pt; color:#64748B; font-weight:700;">BENEFICIO ESPERADO</div>
      <div style="font-family:'Space Grotesk', monospace; font-weight:700; color:#00DC82; font-size:8.5pt;">| Objetivo − Entrada |</div>
    </div>
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:1.5mm; border-radius:4px;">
      <div style="font-size:7.5pt; color:#64748B; font-weight:700;">RATIO MÍNIMO</div>
      <div style="font-family:'Space Grotesk', monospace; font-weight:700; color:#0F172A; font-size:8.5pt;">Beneficio / Riesgo ≥ 1,0</div>
    </div>
  </div>
</div>

**Si la relación queda bajo 1,0, la operación no se toma.** Sin excepciones, sin "pero el setup estaba lindo".

**Y esto ocurre más seguido de lo que parece.** Fíjate en la aritmética: cuando el stop cae en la rama de 1,5 × ATR y el primer objetivo está a 1,0 × ATR, la relación es 1,0 / 1,5 = **0,67**, y la operación se cae sola. Es el caso del ejemplo del Módulo 4.3.

Dicho de otro modo: **este método solo autoriza la operación cuando el stop pudo apoyarse en un swing cercano**, porque solo entonces el riesgo es menor que el objetivo. Ese es el filtro trabajando, no una falla.

> [!WARNING]
> **Incompatibilidad de Rama B con TP1 de 1,0×ATR**: Si el stop loss cae en Rama B (1,5 × ATR) y el objetivo TP1 es 1,0 × ATR, el ratio riesgo/beneficio es $1,0 / 1,5 = 0,67 < 1,0$ y la operación se **rechaza obligatoriamente**. Cualquier ejemplo del manual que ejecute esa estructura está en error — verifícalo siempre antes de colocar la orden.

## 6.4 · La salida asimétrica: cuando no hay objetivo fijo

En materias primas con sesgo tendencial pronunciado (Oro, WTI y Brent), el método **prohíbe el objetivo rígido**.

**Alcance estricto por activo**: El Chandelier Trailing Stop aplica a **Oro (siempre)** y a **WTI/Brent** (condicionado a la confirmación de cobre, M10.3). **USD/CLP y Nasdaq 100 operan exclusivamente con TP1 y TP2 fijos**; no existe criterio dinámico intra-operación para divisas ni índices en este manual. La razón es del Módulo 2.6: cerrar en un objetivo fijo te saca de la tendencia que justamente querías acompañar.

Se reemplaza por un **stop que persigue al precio**:

<div class="caja-formula" style="border-left-color: #F59E0B;">
  <div class="caja-formula-titulo">🏹 Stop Dinámico Asimétrico (Chandelier Trailing Exit)</div>
  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 1mm;">
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:2mm; border-radius:4px;">
      <strong style="color:#00DC82;">En Compras (Long):</strong><br>
      <code>Stop = Máximo(últimas 22 velas) − 3,0 × ATR(14)</code>
    </div>
    <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:2mm; border-radius:4px;">
      <strong style="color:#EF4444;">En Ventas (Short):</strong><br>
      <code>Stop = Mínimo(últimas 22 velas) + 3,0 × ATR(14)</code>
    </div>
  </div>
</div>

**Dos cosas que no se cambian:**

1. **El stop solo se mueve a favor.** Si el cálculo da un nivel peor que el actual, se ignora y el stop se queda donde está. Nunca se afloja.
2. **Las 22 velas y el 3,0 van juntos.** Son un par calibrado y separarlos deja el nivel indeterminado. Con 22 velas el nivel es utilizable; con 50, el "stop" puede quedar por encima del precio en una tendencia alcista normal, que es una contradicción y no un stop ceñido.

Contra la intuición: **una ventana más larga aprieta el stop, no lo suelta**, porque el máximo de más velas es más alto y el nivel resultante sube.

> [!IMPORTANT]
> **Costo de Acarreo (Swap Overnight) en operaciones multi-jornada**:
> Cuando una operación en Oro o Nasdaq utiliza el stop que persigue al precio y permanece abierta durante varias sesiones (cruzando el corte diario de las 17:00 NY), el broker cobra o abona el *swap* o *rollover*.
> 
> En contratos con swap negativo relevante, un mantenimiento de 3 a 5 días puede restar entre un 0,10 % y 0,25 % de la cuenta. Por esta razón, el **Módulo 7.1** establece el **Presupuesto de Riesgo Neto (buffer 90/10)**, diseñado para que los costos acumulados queden cubiertos por el margen de reserva sin sobrepasar el presupuesto total del 1,00 %.

## 6.5 · Cuando la operación ya va ganando (Break-Even)

**Gatillo cuantitativo único**: En el instante exacto en que el precio de mercado alcanza Entrada + 0,5 × (TP1 - Entrada) (o su equivalente restando en ventas), **el stop se mueve inmediatamente al precio de entrada (Break-Even)**. Se elimina cualquier ambigüedad por cierre de vela. A partir de ese punto, la operación no puede generar pérdida monetaria de capital.

Es opcional y conservador: reduce tanto la pérdida posible como la probabilidad de aguantar hasta el segundo objetivo. Decídelo antes de entrar, no en el momento.

---

# 💰 MÓDULO 7 · El tamaño de la posición

**Pregunta que responde**: ¿cuántos lotes pongo para que una pérdida no me haga daño?

---

Este es el módulo que decide si sobrevives. Un método con buenas señales y mal tamaño quiebra la cuenta; un método con señales mediocres y buen tamaño aguanta.

## 7.1 · La regla: el 1 % es un presupuesto neto, no una meta

Tu cuenta no debe arriesgar más del **1,0 % del capital total** en una sola operación. Se calcula con una fórmula matemática para un **presupuesto objetivo de riesgo monetario del 1,00 % de tu capital disponible**, descontando de antemano el costo del spread y la comisión mediante el **Presupuesto de Riesgo Neto (buffer 90/10)**:

* **Presupuesto Neto de Precio**: Capital × 0,01 × 0,90 = **0,90 % de la cuenta**.
* **Buffer de Fricción Reservado**: Capital × 0,01 × 0,10 = **0,10 % de la cuenta**.

### Lo que este presupuesto NO acota
El dimensionamiento cuantitativo acota la pérdida por movimiento normal de precios, pero existen tres riesgos residuales inherentes al mercado que este presupuesto no puede eliminar:
1. **Gaps de apertura**: saltos de precios por noticias de fin de semana o feriados sobre el nivel del stop.
2. **Slippage de ejecución del propio stop**: deslizamientos en momentos de volatilidad extrema o baja liquidez súbita.
3. **Swap extremo acumulado**: financiamiento nocturno si una posición swing se prolonga más allá del horizonte previsto.

La matemática de redondeo de lotes hacia abajo asegura que, bajo condiciones normales de liquidez, la pérdida en precio se mantenga estrictamente contenida dentro del presupuesto asignado.

## 7.2 · La trampa de las unidades, y cómo no caer en ella

Esta es la parte del manual que más cuidado necesita, porque un error acá **multiplica tu riesgo por cien**.

La distancia al stop se puede expresar de dos formas y **no son lo mismo**:

| | USD/CLP | Qué es |
|---|---|---|
| **Unidad de cotización** | 1,00 peso | Un peso completo de movimiento |
| **Punto** | 0,01 peso | El último decimal que cotiza el activo |

Un stop de 3,62 **pesos** son 362 **puntos**. Y el valor por lote es distinto en cada unidad: 1 peso vale $100.000 CLP por lote, y 1 punto vale $1.000 CLP por lote.

> [!CAUTION]
> **Nunca mezcles las dos.** Si tomas la distancia en pesos (3,62) y la multiplicas por el valor del **punto** ($1.000), obtienes un lote **100 veces mayor** que el correcto. Con una cuenta de $1.000.000 eso significa arriesgar la cuenta entera en una sola operación en vez del 1 %.
>
> **La regla segura**: trabaja siempre en la **unidad de cotización** (pesos para el USD/CLP, dólares para el Oro y el petróleo, puntos de índice para el Nasdaq) y usa la columna "valor de 1 unidad" de la tabla siguiente. Si las dos cifras están en la misma unidad, no hay error posible.

## 7.3 · Valor de una unidad por lote, por activo

Medido contra una cuenta en pesos chilenos con tipo de cambio de referencia de **935,60 CLP/USD** (snapshot del 2026-09-04):

| Activo | Contrato | Decimales típicos de cotización | Valor de 1 último decimal por lote (CLP) | Valor de 1 unidad entera por lote (CLP) |
|---|---|---|---|---|
| **USD/CLP** | 100.000 USD | 2 decimales (0,01 CLP) | $1.000 CLP | **$100.000 CLP** |
| **Oro (XAU/USD)** | 100 onzas troy | 2 decimales (0,01 USD) | $935,60 CLP | **$93.560 CLP** |
| **WTI** | 1.000 barriles (o 100 según broker) | 3 decimales (0,001 USD) | $94 CLP (con 2 dec: $936 CLP) | **$935.600 CLP** (o $93.560 CLP) |
| **Brent** | 1.000 barriles (o 100 según broker) | 3 decimales (0,001 USD) | $94 CLP (con 2 dec: $936 CLP) | **$935.600 CLP** (o $93.560 CLP) |
| **Nasdaq 100** | Multiplicador 1 | 2 decimales (0,01 pts) | $9,36 CLP | **$935,60 CLP** |

*Nota obligatoria de verificación de dígitos y tamaño de contrato*: Estos valores asumen 2 decimales en USD/CLP y Oro, 3 en WTI/Brent y 2 en Nasdaq 100. Los ejemplos de 7.4 y 4.4 asumen contrato de 100 barriles por lote; con contrato de 1.000 los valores se multiplican ×10 — verifícalo en MT5 → Especificación → Volumen y Dígitos, y recalcula. Un dígito de diferencia cambia el valor por factor 10.

## 7.4 · Los cuatro pasos, con casos reales y costos de fricción

Cuenta de **$1.000.000 CLP**, presupuesto total del 1 % = **$10.000 CLP** (Presupuesto neto de precio: **$9.000 CLP**, Reserva de fricción: **$1.000 CLP**). Los ATR son los medidos en H1 en el snapshot oficial de MT5.

| Activo | ATR H1 | Stop (1,5 × ATR) | Lote teórico neto | **Lote real** | Pérdida en el stop (Precio) | Costo Spread + Comisión | **Pérdida Total Real** | % Real de la Cuenta |
|---|---|---|---|---|---|---|---|---|
| **USD/CLP** | 2,41 | 3,62 pesos | 0,0248 | **0,02** | $7.240 | $700 | **$7.940** | **0,79 %** ✓ |
| **WTI** | 0,771 | 1,157 dólares | 0,0832 | **0,08** | $8.660 | $920 | **$9.580** | **0,96 %** ✓ |
| **Nasdaq 100** | 84,47 | 126,70 puntos | 0,0760 | **0,07** | $8.298 | $980 | **$9.278** | **0,93 %** ✓ |
| **Oro** | 22,54 | 33,81 dólares | 0,0028 | **no operable** | no aplica | no aplica | **no aplica** | no aplica |

**Siempre se redondea hacia abajo y con buffer de fricción.** Todos los ejemplos de pérdida del manual usan lote post-redondeo (ver Caso M4.4). 0,0832 baja a 0,08. Al incluir la columna de spread y comisiones reales de MT5, la pérdida total de WTI queda en **0,96 %** y Nasdaq en **0,93 %**, estrictamente contenidas bajo el presupuesto máximo del 1,00 %.

## 7.5 · Cuando un activo no alcanza para tu cuenta

Mira la última fila. El Oro pide un lote teórico de **0,0028**, y el volumen mínimo que acepta la plataforma es **0,01**. Ese mínimo, con un stop de 33,81 dólares, arriesga **$31.633 CLP**, o sea **3,16 %** de la cuenta: más del triple del presupuesto.

**La conclusión honesta es que hoy el Oro no es operable con una cuenta de $1.000.000 bajo la regla del 1 %.** Para que el lote mínimo represente el 1 % harían falta cerca de **$3.514.778 CLP** (calculado como $31.633 / 0,0090 bajo presupuesto neto).

Esto no es una limitación del método, es aritmética del tamaño del contrato. Y responde una pregunta que casi todos se hacen alguna vez:

> [!IMPORTANT]
> **Si el lote que te sale es menor al mínimo, ese activo no es para tu cuenta todavía.** No se opera con el mínimo "porque es lo más chico que se puede". La alternativa correcta es elegir otro de los cinco activos, cuyo lote sí quepa, y volver al Oro cuando la cuenta lo permita.

## 7.6 · Comprueba que el margen entra

Un último filtro de solvencia antes de enviar la orden a MetaTrader 5. El **margen** es la garantía retenida por el broker para sostener el apalancamiento:

<!-- TOKEN_COMPROBACION_MARGEN -->

**Regla de Seguridad de la Mesa**: Si el margen requerido supera el **30 % del margen libre disponible** de tu cuenta, la operación queda **estrictamente rechazada**, incluso si el cálculo monetario del 1 % neto daba luz verde. Esto previene llamadas de margen (*margin calls*) provocadas por la volatilidad intra-hora.

---

# 🛑 MÓDULO 8 · Los cinco filtros que bloquean

**Pregunta que responde**: tengo la ficha lista, ¿hay algo que igual me impida entrar?

---

Sí, cinco cosas. Se revisan **después** de armar la ficha y **antes** de hacer clic. Cualquiera de las cinco deja la operación en rojo.

## 8.1 · Filtro de spread, y el tope cambia por activo

El spread es la diferencia entre el precio de compra y el de venta: es el costo del broker y lo pagas al entrar.

**Si el spread se come una fracción grande de tu stop, la operación es inviable** aunque la señal sea perfecta: partes perdiendo una parte del riesgo antes de que el precio se mueva.

| Activo | Tope de spread sobre la distancia al stop |
|---|---|
| **USD/CLP** | 15 % |
| **Nasdaq 100** | 12 % |
| **Oro, WTI y Brent** | **10 %** |

> [!CAUTION]
> **El 15 % es solo el del dólar.** Aplicar ese tope al Oro o al petróleo deja pasar operaciones que el método rechaza, y en la dirección peligrosa: entras a un costo que el sistema considera excesivo. Los topes son tres cifras distintas y hay que usar la del activo.

*Ejemplo con el USD/CLP*: stop a 3,62 pesos, tope 15 %, así que el spread máximo tolerable es 0,54 pesos. Con el spread en 0,40 pesos la operación pasa; en 0,80 pesos queda bloqueada.

## 8.2 · Filtro de horario, y el caso especial del dólar

El **USD/CLP tiene liquidez institucional profunda solo durante la rueda bancaria de Santiago, de 09:00 a 14:00 de Chile.** Fuera de esa ventana los spreads se abren y el precio se mueve con poco volumen detrás.

Eso deja **cuatro velas H1 utilizables al día**: las que cierran a las 10:00, 11:00, 12:00 y 13:00. La vela que cierra a las 14:00 se puede analizar pero no operar, porque la rueda termina ahí.

**Al cierre de la rueda se cancelan todas las órdenes pendientes** que no se hayan activado.

Los otros cuatro activos cotizan con liquidez amplia durante la sesión de Nueva York, que es la referencia natural para ellos.

## 8.3 · Filtro de noticias (blackout)

Cuando se publica un dato macro grande, el spread se abre y el precio salta. Una orden pendiente en esa ventana se ejecuta a un precio que no elegiste.

<div class="contenedor-diagrama">
<svg viewBox="0 0 760 120" width="100%" height="120" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <line x1="40" y1="60" x2="720" y2="60" stroke="#1E3A5F" stroke-width="3"/>

  <!-- Sesión Normal -->
  <circle cx="110" cy="60" r="10" fill="#00DC82"/>
  <text x="110" y="38" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#00DC82" text-anchor="middle">SESIÓN NORMAL</text>

  <!-- Antes del Dato -->
  <rect x="210" y="28" width="150" height="64" rx="6" fill="#280D12" stroke="#EF4444" stroke-width="1.5"/>
  <text x="285" y="52" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#F87171" text-anchor="middle">ANTES DEL DATO</text>
  <text x="285" y="72" font-size="8.5" font-weight="600" fill="#FCA5A5" text-anchor="middle">Cancelar pendientes</text>

  <!-- Dato Macro (!) -->
  <circle cx="430" cy="60" r="18" fill="#EF4444"/>
  <text x="430" y="67" font-family="'Goldman', sans-serif" font-size="15" font-weight="800" fill="#FFFFFF" text-anchor="middle">!</text>
  <text x="430" y="22" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#F87171" text-anchor="middle">DATO MACRO</text>

  <!-- Después del Dato -->
  <rect x="500" y="28" width="170" height="64" rx="6" fill="#280D12" stroke="#EF4444" stroke-width="1.5"/>
  <text x="585" y="52" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#F87171" text-anchor="middle">DESPUÉS DEL DATO</text>
  <text x="585" y="72" font-size="8.5" font-weight="600" fill="#FCA5A5" text-anchor="middle">Esperar vela cerrada</text>
</svg>
</div>

| Evento Macroeconómico | Antes del dato | Después del dato | Activos bloqueados |
|---|---|---|---|
| **Decisión de tasas de la Fed (FOMC)** | 30 minutos | 75 minutos (post rueda de prensa) | **TODOS los activos del manual** |
| **Non-Farm Payrolls (NFP, empleo EE.UU.)** | 15 minutos | 30 minutos | **Oro, WTI, Brent y Nasdaq 100** |
| **IPC de Estados Unidos** | 15 minutos | 30 minutos | **Oro, WTI, Brent y Nasdaq 100** |
| **Reunión de Política Monetaria BCCh / IPoM** | 15 minutos | 30 minutos | **USD/CLP** |
| **Imacec (Chile)** | 15 minutos | 30 minutos | **USD/CLP** |

La ventana más larga es la de la Reserva Federal, y con razón: después del comunicado viene la conferencia de prensa, y el movimiento grande suele estar ahí y no en el número.

## 8.4 · Filtro de confirmación cruzada

Este filtro es el que le da el nombre al método, y es el que más se olvida. **La señal técnica de un activo tiene que estar respaldada por el mercado que lo mueve.** Todos los umbrales maestros provienen del punto único de verdad en el **Anexo A2**.

| Activo | Driver que se Confirma | Se aprueba la compra si… | Referencia Anexo A2 |
|---|---|---|---|
| **USD/CLP** | Cobre (COMEX/LME) | El cobre cae o está plano en 5 días (Δ 5d ≤ 0,00 %), **o** el clima es Tormenta o Recesión | Umbral R3/R4 |
| **Oro** | Tasa real TIPS 10Y EE.UU. | El clima es Tormenta o Inflación, **o** la tasa real está en **2,20 % o menos** | Umbral TIPS A2 |
| **WTI y Brent** | Crudo Físico / WTI | Petróleo Δ 5d ≥ +1,00 % (tendencia material, no ruido), **o** el clima es Tormenta (R3) | Umbral R3 |
| **Nasdaq 100** | Bono US10Y Nominal | La tasa está en **4,70 % o menos** **y** el clima no es Tormenta ni Inflación | Umbral Tasa A2 |

**La lógica fundamental de la tasa real del Oro en 2,20 %**: Las tasas reales de los bonos protegidos contra la inflación (TIPS a 10 años) representan el costo de oportunidad de mantener metales preciosos (que no pagan rendimiento por cupón). Un nivel sobre 2,20 % señala una política monetaria de la Fed fuertemente restrictiva que absorbe liquidez hacia la renta fija soberana. Bajo 2,20 %, o en entornos de shock geopolítico/inflacionario, el Oro recupera su tracción alcista como reserva soberana de valor.

Si el respaldo macro no está presente, la operación queda en rojo aunque los ocho campos técnicos de la ficha estén completos.

## 8.5 · Filtro de riesgo/beneficio

Ya está explicado en el Módulo 6.3 y se repite acá porque forma parte de la revisión final: **bajo 1,0 no se opera.**

---

# 📉 MÓDULO 9 · Gestión de rachas y límites de la cuenta

**Pregunta que responde**: ¿qué hago cuando vengo perdiendo?

---

> [!NOTE]
> **Este módulo es criterio de mesa del desk, no salida del modelo.** Los demás módulos describen reglas que el motor calcula. Estos límites son política de gestión de riesgo que adoptamos y te recomendamos: no salen de un cálculo, salen de la experiencia de que una racha mal administrada hace más daño que cualquier operación individual.
>
> Lo decimos explícitamente para que sepas cuál es cuál.

## 9.1 · Los cuatro límites cuantitativos

| Límite | Umbral | Qué haces cuando se toca |
|---|---|---|
| **Riesgo simultáneo global** | 2,5 % del capital en posiciones abiertas a la vez | No abres una más hasta cerrar alguna |
| **Co-Riesgo en activos correlacionados** | 1,0 % máximo conjunto en activos gemelos | Ver regla 9.4 |
| **Pérdida diaria** | 2 operaciones perdedoras en el día (unos 2,0 %) | **Cierras la plataforma** y no operas más hoy |
| **Pérdida semanal** | 4,0 % acumulado en la semana | Suspendes hasta el lunes siguiente |
| **Racha adversa** | 3 pérdidas consecutivas | Bajas el riesgo por operación al **0,5 %** (es presupuesto total; mantiene el buffer: 0,45 % precio + 0,05 % fricción) hasta encadenar 2 ganadoras |

## 9.2 · Por qué el límite diario es de operaciones y no de porcentaje

Podría estar escrito como "para cuando pierdas el 2 %". Está escrito como **dos operaciones** a propósito: es un número que no admite interpretación en el momento en que menos ganas tienes de ser objetivo.

Dos pérdidas seguidas suelen significar que el mercado no está haciendo lo que tu lectura decía. La tercera operación de ese día casi nunca es análisis: es querer recuperar.

## 9.3 · La regla que evita el daño mayor

**Después de una pérdida, el tamaño no sube.** Ni "para recuperar lo de antes", ni porque la próxima señal se ve mejor. El presupuesto del 1 % se calcula sobre el capital **actual**, así que después de perder, el monto arriesgado baja solo. Eso es correcto y hay que dejarlo trabajar.

## 9.4 · Mapa de correlación intermercado y regla de co-riesgo

El límite de 2,5 % global presupone diversificación. Pero en los mercados financieros, **varios activos se mueven juntos porque comparten los mismos motores macro**. Tratar cada posición como estadísticamente independiente es un error severo de gestión de riesgo.

### Matriz de Correlación Intermercado Histórica (Ventana 60 días)

| Activo | USD/CLP | Oro (XAU) | WTI | Brent | Nasdaq 100 | Driver Compartido Dominante |
|---|---|---|---|---|---|---|
| **USD/CLP** | 1,00 | −0,25 | +0,15 | +0,12 | −0,35 | Cobre (−0,75) y Dólar Global (DXY) |
| **Oro (XAU)** | −0,25 | 1,00 | +0,30 | +0,28 | +0,40 | Tasa Real TIPS y Tensión Geopolítica |
| **WTI** | +0,15 | +0,30 | 1,00 | **+0,92** | +0,20 | Shock de Oferta / OPEP y Fletes |
| **Brent** | +0,12 | +0,28 | **+0,92** | 1,00 | +0,22 | Shock de Oferta / OPEP y Fletes |
| **Nasdaq 100** | −0,35 | +0,40 | +0,20 | +0,22 | 1,00 | Tasa Bono 10Y y Curva de Rendimientos |

### Las Dos Reglas de Co-Riesgo de Portafolio

1. **Regla de Activos Gemelos (WTI + Brent)**: Con una correlación de +0,92, abrir un largo en WTI y un largo en Brent no es diversificar: es duplicar el riesgo en el mismo vector petrolero. **Ambos activos comparten un cupo conjunto máximo del 1,0 % de riesgo** (ej. 0,50 % en cada uno, o elegir el contrato con la compresión técnica más limpia).
2. **Límite de Exposición Agregada al Dólar / Tasas**: No se permite mantener más de **dos posiciones simultáneas** cuya dirección dependa directamente de la tasa de interés de EE.UU. (ej. Largo en Nasdaq + Largo en Oro + Corto en USD/CLP).

---

### Exposición agregada a tasas de interés (Límite de Co-Riesgo)

Para evitar sobreexposición direccional a la curva de rendimientos de EE.UU., se aplica la siguiente regla estricta:

| Apuesta Macroeconómica | Activos Alineados (Misma Dirección de Tasa) | Límite Simultáneo Permitido |
|---|---|---|
| **Tasas a la baja** (Expansión monetaria / Caída de yields) | **Largo Oro** + **Largo Nasdaq** + **Corto USD/CLP** | Máximo **2 posiciones** en esta dirección |
| **Tasas al alza** (Apretón monetario / Alza de yields) | **Corto Oro** + **Corto Nasdaq** + **Largo USD/CLP** | Máximo **2 posiciones** en esta dirección |

---

# 🗂️ MÓDULO 10 · Fichas por activo

**Pregunta que responde**: para el activo que quiero operar hoy, ¿qué me habilita el clima?

---

Este módulo es de consulta. Busca tu activo, cruza con el clima del día y lee qué dirección tienes permitida y qué está prohibido.

## 10.1 · USD/CLP · Dólar contra peso chileno

**Qué lo mueve**: el cobre (cuando sube, el dólar en Chile baja), la diferencia entre las tasas de Chile y de EE.UU., y el flujo de inversionistas extranjeros.

| Clima | Sesgo | Dirección permitida | Prohibido |
|---|---|---|---|
| 📉 **Recesión** | +1,20 alcista dólar | Solo compra | Operar rango, apostar a la baja |
| 🌪️ **Tormenta** | +0,80 alcista dólar | Solo compra | Operar rango |
| 🛒 **Inflación** | +0,60 alcista dólar | Solo compra | Vender en resistencia |
| ☀️ **Día bueno** | −1,20 bajista dólar | Solo venta | Perseguir rupturas al alza |
| 🏖️ **Calma**, cobre cayendo 2,5 % o más | +1,00 alcista | Solo compra | Operar rango |
| 🏖️ **Calma**, cobre subiendo 1,5 % o más | −1,00 bajista | Solo venta | Perseguir rupturas al alza |
| 🏖️ **Calma**, cobre plano | 0,00 neutral | **Rango**: compra en soporte, venta en resistencia | Perseguir rupturas |

**Recuerda el horario**: solo 09:00 a 14:00 de Chile (Módulo 8.2).

## 10.2 · Oro · XAU/USD

**Qué lo mueve**: La tasa real de EE.UU. (es el driver dominante y va en contra: si la tasa real sube sobre el umbral del Anexo A2, el oro sufre), la inflación esperada y la tensión geopolítica.

| Condición | Sesgo | Dirección permitida | Prohibido |
|---|---|---|---|
| Clima Tormenta o Inflación, **o** tasa real bajo **2,20 %** | +1,80 **fuerte alcista** | Solo compra: retroceso a EMA 20 o ruptura | **Vender, incluso con RSI en 80** |
| Resto de condiciones | +0,40 alcista moderado | Compra: retroceso a EMA 50 o ruptura | Venta agresiva |

> [!IMPORTANT]
> **El Oro no lleva objetivo fijo y vigila el swap multi-día.**
> 
> 1. Su salida es siempre el stop que persigue al precio del Módulo 6.4 (máximo 22 velas − 3,0 × ATR). Poner un objetivo rígido en Oro contradice el método.
> 2. Si la posición cruza más de 48 horas, verifica el costo de swap en MT5.
> 3. Y ojo con el Módulo 7.5: el Oro es el activo con el contrato más pesado de los cinco, así que suele ser el primero que queda fuera del alcance de una cuenta chica (< $3.514.778 CLP bajo presupuesto neto).

## 10.3 · WTI y Brent · Petróleo

**Qué lo mueve**: la demanda mundial, las decisiones de la OPEP y la geopolítica. Pero lo que decide **cuánto riesgo tomas** es el cobre.

| Condición | Sesgo | Stop que persigue | Tamaño de la posición |
|---|---|---|---|
| Crudo al alza **con** el cobre subiendo 1,5 % o más | +1,50 alcista | 3,0 × ATR | **Completo** |
| Crudo al alza **sin** respaldo del cobre | +1,50 alcista | **2,0 × ATR** (más ceñido) | **La mitad** |
| Resto | 0,00 neutral | no aplica | Solo rango |

**Esta es la aplicación práctica del Módulo 2.3.** Si el crudo sube y el cobre lo acompaña, es demanda industrial real y la tendencia tiene respaldo. Si el crudo se dispara solo, es miedo a faltantes: el movimiento es más frágil y se puede dar vuelta rápido, así que se opera con la mitad del tamaño y el stop más cerca.

En los dos casos de alza está **prohibido vender en resistencia**.

## 10.4 · Nasdaq 100 · US100

**Qué lo mueve**: la tasa del bono de EE.UU. a 10 años, que es con la que se descuentan las ganancias futuras de las empresas tecnológicas. Cuando sube, esas empresas valen menos hoy.

| Condición | Sesgo | Dirección permitida | Prohibido |
|---|---|---|---|
| Tasa a 10 años sobre 4,70 %, **o** clima Tormenta o Inflación | −1,20 bajista | Solo venta: retroceso a EMA 50 o ruptura a la baja | **Comprar la caída. Comprar sin confirmación** |
| Resto | +0,80 alcista | Compra: retroceso a EMA 20 o ruptura | Vender en tendencia |

El umbral de 4,70 % es el mismo que aparece en el filtro de confirmación cruzada del Módulo 8.4, y no es casual: es el nivel donde el costo del dinero empieza a pesar más que el crecimiento.

---

# 📋 MÓDULO 11 · Checklist de ejecución

**Pregunta que responde**: ¿puedo hacer clic?

---

Recorre esto **completo** antes de cada orden. Si algo falla, no hay operación.

<div class="contenedor-diagrama">
<svg viewBox="0 0 760 250" width="100%" height="250" xmlns="http://www.w3.org/2000/svg" style="background:#060F19; border:1px solid #1E293B; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <rect x="0" y="0" width="760" height="34" fill="#0B1926" rx="8 8 0 0"/>
  <text x="24" y="22" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#38BDF8">CHECKLIST ANTES DEL CLIC · 30 SEGUNDOS</text>

  <circle cx="35" cy="60" r="10" fill="#00DC82"/>
  <text x="35" y="64" font-family="'Goldman', sans-serif" font-size="10" font-weight="800" fill="#060F19" text-anchor="middle">1</text>
  <text x="58" y="64" font-size="9.8" font-weight="600" fill="#F8FAFC">¿El clima está confirmado por 2 días y confianza de 51,0 % o más (mínimo de Anexo A2, inclusive)?</text>

  <circle cx="35" cy="94" r="10" fill="#00DC82"/>
  <text x="35" y="98" font-family="'Goldman', sans-serif" font-size="10" font-weight="800" fill="#060F19" text-anchor="middle">2</text>
  <text x="58" y="98" font-size="9.8" font-weight="600" fill="#F8FAFC">¿La dirección que quiero tomar es la que el clima permite en el Módulo 10?</text>

  <circle cx="35" cy="128" r="10" fill="#00DC82"/>
  <text x="35" y="132" font-family="'Goldman', sans-serif" font-size="10" font-weight="800" fill="#060F19" text-anchor="middle">3</text>
  <text x="58" y="132" font-size="9.8" font-weight="600" fill="#F8FAFC">¿El setup calificó sobre una vela H1 CERRADA, con todas sus condiciones?</text>

  <circle cx="35" cy="162" r="10" fill="#00DC82"/>
  <text x="35" y="166" font-family="'Goldman', sans-serif" font-size="10" font-weight="800" fill="#060F19" text-anchor="middle">4</text>
  <text x="58" y="166" font-size="9.8" font-weight="600" fill="#F8FAFC">¿El stop sale de las 20 velas o de 1,5 × ATR, y el R:R llega al menos a 1,0?</text>

  <circle cx="35" cy="196" r="10" fill="#00DC82"/>
  <text x="35" y="200" font-family="'Goldman', sans-serif" font-size="10" font-weight="800" fill="#060F19" text-anchor="middle">5</text>
  <text x="58" y="200" font-size="9.8" font-weight="600" fill="#F8FAFC">¿El lote es del 1 % NETO (0,90% precio + 0,10% fricción), redondeado hacia abajo?</text>

  <circle cx="35" cy="230" r="10" fill="#00DC82"/>
  <text x="35" y="234" font-family="'Goldman', sans-serif" font-size="10" font-weight="800" fill="#060F19" text-anchor="middle">6</text>
  <text x="58" y="234" font-size="9.8" font-weight="600" fill="#F8FAFC">¿Spread bajo el tope del activo, horario válido, sin blackout, con confirmación cruzada?</text>
</svg>
</div>

Y una última pregunta que no está en el diagrama y conviene hacerse:

> **¿Estoy tomando esta operación porque calificó, o porque quiero recuperar la anterior?** Si la respuesta honesta es la segunda, revisa el Módulo 9.

---

# 📓 MÓDULO 12 · La Bitácora de Auditoría Operativa

**Pregunta que responde**: ¿cómo demuestro que mis resultados vienen de mi disciplina y no de la suerte?

---

> [!NOTE]
> **La regla de gobernanza del Desk**: Ninguna operación se considera terminada hasta que queda registrada en la bitácora. Una operación perdedora con checklist 100 % cumplido es una victoria del proceso; una operación ganadora sin checklist ni bitácora es una falta grave de indisciplina.

La bitácora permite alimentar los límites del Módulo 9: si entras en una racha de 3 pérdidas consecutivas, la bitácora te dirá de inmediato si estás ante varianza estadística normal (mercado difícil) o ante errores humanos de ejecución (sobre-apalancamiento o saltarse filtros).

### Estructura Estándar del Registro (Journaling Cuantitativo)

Para cada operación, registra estos 8 campos en tu hoja de control o cuaderno de trading:

| Campo | Descripción | Ejemplo Ilustrativo (Caso M4.4) |
|---|---|---|
| **1. Fecha y Hora MT5** | Momento exacto de la señal H1 | AAAA-MM-DD 11:00 CLT |
| **2. Activo y Ticket** | Ticker y número de ticket en MT5 | USD/CLP · Ticket #5149201 |
| **3. Clima Macro** | Régimen R0 a R4 publicado en el día | Clima R3 (Tormenta) · Confianza 78 % |
| **4. Setup Ejecutado** | Setup 5.1, 5.2 o 5.3 con dirección | 5.1 Ruptura Donchian · Compra |
| **5. R:R Teórico** | Relación calculada antes de entrar | 1,25 : 1 (TP1: 2,41 / SL: 1,93 swing) |
| **6. Fricción Real** | Spread pagado + Comisión broker | Spread: 0,25 CLP · Comisión: $60 CLP |
| **7a. Resultado (Caso M4.4 Pérdida)** | PnL liquidado en dinero y % cuenta | −$8.780 CLP (−0,88 % de la cuenta) |
| **7b. Resultado (Ejemplo Ganador)** | PnL liquidado neto en dinero y % cuenta | +$8.580 CLP (+0,86 % de la cuenta; neto de $1.060 CLP de fricción) |
| **8. Auditoría Checklist** | ¿Cumplió el 100 % de las reglas (M11)? | **SÍ (6/6 Reglas en VERDE)** |

---

# 📚 ANEXO A1 · Glosario

---

### Del gráfico y los indicadores

* **Vela H1 cerrada**: una vela de una hora cuyo tiempo terminó, al minuto :00. Es el único dato que este método considera confiable.
* **Cuerpo y mecha**: el cuerpo es el rectángulo (de apertura a cierre); las mechas son las líneas finas que marcan los extremos rechazados.
* **ATR (rango medio real)**: cuánto se mueve típicamente un activo en un período. Es la medida de volatilidad que usa este método para el stop, el objetivo y el tamaño. Acá siempre se usa el de 14 períodos en H1.
* **EMA (media móvil exponencial)**: el promedio del precio de las últimas N velas, dando más peso a las recientes. Este método usa las de 20, 50 y 100.
* **SMA (media móvil simple)**: el mismo promedio pero sin dar más peso a las recientes. Es la línea central de las Bandas de Bollinger y el objetivo del rebote en rango. **No es lo mismo que la EMA 20**, aunque las dos usen 20 períodos.
* **Canal Donchian de 50**: el techo y el piso de las últimas 50 velas. Define la compresión y la ruptura.
* **Bandas de Bollinger (20; 2σ)**: una media simple de 20 con dos bandas a dos desviaciones típicas. Marcan el rango habitual del precio.
* **RSI (índice de fuerza relativa)**: mide si un activo viene subiendo o bajando con demasiada insistencia. Va de 0 a 100; bajo 35 es sobreventa y sobre 65 es sobrecompra.
* **ADX**: mide si hay tendencia, sin decir en qué dirección. Bajo 20 el mercado está lateral; en 20 o más hay tendencia.
* **Swing**: un máximo o mínimo relevante que el precio ya respetó antes.

### De la operación

* **CFD (contrato por diferencia)**: el instrumento que operas. No compras el activo, acuerdas con el broker intercambiar la diferencia de precio.
* **Apalancamiento**: la proporción entre el monto que mueves y la garantía que aportas. Con 1:100, $18.712 mueven $1.871.200.
* **Lote**: la unidad de volumen. Su valor en dinero depende del contrato de cada activo (Módulo 7.3).
* **Punto**: el último decimal que cotiza el activo. En el USD/CLP es 0,01 peso. **No confundir con la unidad de cotización completa**, que es un peso: es la confusión del Módulo 7.2 y multiplica el riesgo por cien.
* **Spread**: la diferencia entre el precio de compra y el de venta. Es el costo del broker y lo pagas al entrar.
* **Stop loss (SL)**: el nivel donde asumes una pérdida controlada y sales. Sin él no estás operando este método.
* **Take profit (TP)**: el nivel donde recoges la ganancia planificada.
* **Relación riesgo/beneficio (R:R)**: cuánto aspiras a ganar dividido por cuánto arriesgas. Este método exige 1,0 o más.
* **Break-even**: mover el stop al precio de entrada, de modo que la operación ya no pueda costarte dinero.
* **Stop que persigue al precio (Chandelier)**: un stop que se mueve a favor de la posición y nunca en contra, calculado como el máximo de 22 velas menos 3 ATR. Reemplaza al objetivo fijo en tendencias sostenidas.
* **Orden pendiente**: una orden que espera a que el precio llegue a un nivel. `BUY_STOP` se activa si el precio sube hasta el nivel; `BUY_LIMIT`, si baja hasta él.
* **Racha**: secuencia consecutiva de operaciones con el mismo resultado (positivas o negativas). El manual activa la reducción preventiva de riesgo tras 3 pérdidas consecutivas.
* **Drawdown**: la caída porcentual acumulada del capital de la cuenta desde su punto máximo histórico hasta el mínimo posterior. El límite institucional semanal del manual es 4,00 %.

### De la macroeconomía

* **Clima o régimen**: la clasificación del escenario económico en uno de cinco estados, de R0 a R4 (Módulo 3).
* **Puntos base (bps)**: centésimas de punto porcentual. 100 bps es 1,00 %, así que 10 bps es 0,10 %.
* **Curva de tasas 2s10s**: la diferencia entre el interés que paga el bono de EE.UU. a 10 años y el de 2 años.
* **Curva invertida**: cuando el bono a 2 años paga más que el de 10. Señal clásica de que el mercado espera recesión.
* **Empinamiento con tasas cortas cayendo (bull steepener)**: cuando la tasa corta cae con fuerza porque se espera que el banco central baje tasas con urgencia para reactivar la economía.
* **Tasa real (TIPS)**: el interés que paga un bono de EE.UU. ya descontada la inflación. Es el principal competidor del Oro.
* **Inflación esperada (breakeven)**: la inflación que el mercado descuenta para los próximos 10 años, leída de los bonos.
* **Reserva Federal (Fed) y su comité (FOMC)**: el banco central de EE.UU. y el comité que decide sus tasas.
* **Nóminas no agrícolas (NFP)**: el dato mensual de empleo de EE.UU. Uno de los que más mueve el mercado.
* **IPC (índice de precios al consumidor)**: la medida de inflación.
* **RPM e Imacec**: la reunión de política monetaria del Banco Central de Chile, donde decide la tasa, y el indicador mensual de actividad económica chilena.
* **Bono a 10 años de EE.UU.**: la tasa de referencia del precio del dinero en el mundo. Sobre 4,70 % presiona a las acciones tecnológicas.
* **Bloqueo por noticia (blackout)**: la ventana alrededor de un dato grande en la que no se opera (Módulo 8.3).

---

# 📊 ANEXO A2 · Umbrales exactos del clima y parámetros maestros (SSOT)

> [!IMPORTANT]
> **Fuente Única de Verdad (SSOT)**: Este anexo se genera directamente desde `params.yaml`. Todos los parámetros maestros, umbrales y reglas numéricas del manual están centralizados aquí. No editar a mano.

---

Con esta tabla puedes verificar por tu cuenta la clasificación macroeconómica que publicamos. Todas las variaciones son a **5 días**.

| Clima | Se activa cuando… |
|---|---|
| 🌪️ **Tormenta (R3)** | El petróleo (WTI o Brent) se mueve **3,5 % o más** **Y** (el bono a 10 años sube **10 bps o más** **O** la tasa real sube **8 bps o más**) |
| 🛒 **Inflación (R1)** | La inflación esperada sube **10 bps o más** **Y** (la curva 2s10s está bajo **0,20 %** **O** el bono a 10 años sube **más de 5 bps**) |
| 📉 **Recesión (R4)** | El cobre cae **2,5 % o más** **Y** (la curva está invertida, bajo **0,0 %**, **O** el bono a 2 años cae **15 bps o más** con la curva empinándose **10 bps o más**) |
| ☀️ **Día bueno (R2)** | El cobre sube **1,5 % o más** **Y** el bono a 10 años se mueve dentro de **± 6 bps** **Y** la tasa real no sube |
| 🏖️ **Calma (R0)** | Ningún umbral anterior se cumple |

**Precedencia si dos se activan a la vez**: Tormenta → Inflación → Recesión → Día bueno → Calma.

**Confirmación**: 2 días hábiles seguidos, salvo shock extremo.

**Shock extremo (cambio inmediato)**: cuando una variable supera el 150 % de su umbral. Petróleo **5,25 % o más**, bono a 10 años **15 bps o más**, cobre **−3,75 % o menos**, inflación esperada **15 bps o más**.

---

### Umbrales Maestros de Confirmación Intermercado (Single Source of Truth)

Estos son los valores canónicos que alimentan los Módulos 8.4 y 10. Cualquier referencia en el manual se deriva de esta tabla:

| Activo | Driver Cuantitativo | Umbral Maestro de Aprobación | Condición Alternativa |
|---|---|---|---|
| **USD/CLP** | Cobre COMEX / LME | Cobre Δ 5d ≤ 0,00 % (plano o cayendo) | Clima Tormenta (R3) o Recesión (R4) |
| **Oro (XAU/USD)** | Tasa Real TIPS 10Y EE.UU. | **Tasa Real ≤ 2,20 %** | Clima Tormenta (R3) o Inflación (R1) |
| **WTI y Brent** | Crudo Físico WTI | Petróleo Δ 5d ≥ +1,00 % (tendencia material confirmada; un umbral > 0 es tautológico al auto-confirmar la señal) | Clima Tormenta (R3) |
| **Nasdaq 100** | Bono US10Y Nominal | **Tasa 10Y ≤ 4,70 %** | Clima NO Tormenta (R3) ni Inflación (R1) |

---

### Parámetros de Riesgo y Microestructura H1

| Parámetro | Valor Oficial | Justificación Técnica |
|---|---|---|
| **Riesgo total por operación** | **1,0 % del capital** | Presupuesto máximo absoluto (0,90% precio + 0,10% fricción) |
| **Stop loss inicial intradía** | **1,5 × ATR de 14 en H1** | Distancia fija de volatilidad si swing no califica |
| **Banda de swing para stop** | **0,5 a 1,5 × ATR de 14** | Rango de distancia para adoptar el mínimo/máximo de 20 velas |
| **Stop que persigue (Chandelier)** | **Máximo(22 velas H1) − 3,0 × ATR** | Salida asimétrica para tendencias macro (constante de LeBeau) |
| **Stop crudo sin respaldo de cobre** | **Máximo(22 velas H1) − 2,0 × ATR** | Salida ceñida ante shock puramente precautorio (Kilian AER 2009) |
| **Canal Donchian de compresión** | **50 períodos H1, ancho ≤ 2,5 × ATR** | Umbral matemático de compresión previa a quiebre |
| **Tolerancia máxima de slippage** | **0,2 × ATR** | Límite de deslizamiento en órdenes pendientes; cancelar de inmediato si se supera (equivale a ~13 % de un stop de 1,5×ATR) |
| **Vencimiento de orden pendiente** | **2 velas H1 (2 horas)** | Si el precio no rompe en la ventana, la compresión muta |
| **Relación riesgo/beneficio mínima** | **1,0 : 1** | Filtro obligatorio de esperanza matemática positiva |
| **Tope de spread tolerable** | **15 % USD/CLP · 12 % Nasdaq · 10 % Oro/Petróleo** | Límite de costo de entrada sobre la distancia al stop |
| **Límite de riesgo simultáneo global** | **2,5 % del capital** | Exposición total agregada máxima de la cuenta |
| **Límite de co-riesgo activos gemelos** | **1,0 % del capital conjunto (WTI+Brent)** | Evita duplicar riesgo en activos con correlación ρ > 0,90 |
| **Índice de Confianza mínimo** | **51,0 %** | Piso algebraico de frescura y cobertura de drivers |

> [!NOTE]
> **Nota sobre operativa Swing diaria (D1)**: En sistemas automatizados institucionales que operan velas diarias (D1), el stop loss utiliza 2,5 × ATR(20) en D1. Toda la operativa formativa e intradía descrita en este manual para el trader se rige estrictamente por la columna H1 arriba descrita.

---

---

## Parámetros de gatillo de setups (SSOT)

| Setup | Parámetro Maestro | Umbral / Condición Cuantitativa | Acción ante Incumplimiento |
|---|---|---|---|
| **5.1 Ruptura** | Ancho del Canal Donchian 50 | ≤ 2,5 × ATR en H1 | Rechazar setup (mercado expandido) |
| **5.1 Ruptura** | Tamaño de Cuerpo de Vela | ≥ 50 % del rango total | Rechazar orden (mecha dominante) |
| **5.1 Ruptura** | Rango Total de la Vela | ≥ 1,0 × ATR en H1 | Rechazar orden (falta de momentum) |
| **5.1 Ruptura** | RSI(14) en H1 | ≤ 75 (compra) / ≥ 25 (venta) | Rechazar orden (agotamiento extremo) |
| **5.1 Ruptura** | Slippage Cap Admisible | ≤ 0,2 × ATR | Cancelar orden pendiente de inmediato |
| **5.2 Retroceso** | Alineación de Medias | EMA 20 > EMA 50 > EMA 100 (compra) | Rechazar setup (tendencia no alineada) |
| **5.2 Retroceso** | Filtro de Fuerza ADX(14) | ≥ 20 en H1 | Rechazar setup (mercado lateral) |
| **5.2 / 10.2** | Variante Retroceso EMA 50 | Aplica idénticas 3 condiciones en EMA 50 | Medir stop siempre desde la entrada |
| **5.3 Rango** | RSI(14) en H1 | < 35 (compra) / > 65 (venta) | Rechazar orden (fuera de zona extrema) |
| **5.3 Rango** | Expiración de Orden y MT5 | 2 velas H1 (BUY_LIMIT colocable) | Cancelar orden si no se activa |
| **WTI / Cobre** | Multiplicador Tamaño Petróleo | Cobre Δ5d ≥ +1,5% → 100% / < +1,5% → 50% | Reducir lote a la mitad si no hay cobre |

---

<div style="break-before: page;"></div>

# 🛠️ ANEXO A3 · Instalar los indicadores en MT5

---

Para ver en tu gráfico H1 exactamente lo que este manual describe:

1. **Medias exponenciales (EMA 20, 50 y 100)**
   *Insertar → Indicadores → Tendencia → Media Móvil*. Repite tres veces: período 20, 50 y 100, y en las tres elige **Método: Exponencial** aplicado al **Cierre**. Dales colores distintos, porque su orden es una condición del Módulo 5.2.

2. **Bandas de Bollinger**
   *Insertar → Indicadores → Tendencia → Bandas de Bollinger*. Período **20**, desviaciones **2,000**, aplicado al **Cierre**.

3. **ATR de 14**
   *Insertar → Indicadores → Osciladores → Rango Medio Real*. Período **14**. Aparece en una ventana aparte y es el número que usarás para el stop y el lote.

4. **ADX de 14**
   *Insertar → Indicadores → Osciladores → Índice de Movimiento Direccional Promedio*. Período **14**. Solo necesitas la línea principal, que decide qué setup aplica.

5. **RSI de 14**
   *Insertar → Indicadores → Osciladores → Índice de Fuerza Relativa*. Período **14**, aplicado al **Cierre**.

6. **Canal Donchian de 50**
   > [!CAUTION]
   > **MetaTrader 5 no trae este indicador de fábrica.** Los cinco anteriores están en el menú estándar; este no. Tienes dos caminos, y conviene saberlo antes de buscarlo diez minutos:
   >
   > * **Instalarlo**: busca "Donchian Channel" o "Price Channel" en el Mercado de MT5 (*Ver → Terminal → Mercado*), en la sección de indicadores gratuitos. Configúralo en **50** períodos.
   > * **Leerlo a mano**: el canal es simplemente el **máximo y el mínimo de las últimas 50 velas**. Con la herramienta de líneas horizontales puedes marcar los dos niveles y actualizarlos cuando cambien. Es más trabajo, pero no depende de instalar nada.

**Guarda la plantilla.** Con todo puesto, *clic derecho en el gráfico → Plantilla → Guardar plantilla*. Así la aplicas a cualquier activo en dos clics y no repites el armado.

---

## 🎓 Cierre

El trading con método no consiste en adivinar el futuro. Consiste en repetir un proceso: entender el clima, esperar a que una vela cerrada cumpla condiciones, calcular el tamaño con la calculadora y no con la intuición, y respetar los límites cuando la racha va en contra.

La mayoría de los días este proceso te va a decir que no hay operación. **Ese es el resultado más frecuente y no es una falla del método: es el método.** Las cuentas se cuidan mucho más con las operaciones que no se toman que con las que se ganan.

*Buena disciplina, y respeto estricto a tu capital.*

---

**Grupo Inteligencia · Departamento de Estudios y Research**
*Material formativo. No constituye asesoría de inversión. Los valores de contrato, ATR y tipo de cambio citados fueron medidos el 2026-09-04 y son referencias: lee siempre los de tu propia plataforma.*
