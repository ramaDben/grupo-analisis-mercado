# Manual de Operaciones · Trading Cuantitativo Intermercado
### De la macroeconomía real a tu plataforma MetaTrader 5
**Grupo Inteligencia · Departamento de Estudios y Research**
*Manual formativo modular para el trader. Cada módulo se puede estudiar por separado y consultar de forma puntual.*

---

> [!CAUTION]
> **Aviso de riesgo y transparencia.** Este documento es material educativo y formativo de Grupo Inteligencia. No constituye asesoría financiera personalizada ni garantiza rentabilidades futuras. El trading en Contratos por Diferencia (CFD) con apalancamiento conlleva un alto riesgo de pérdida de capital, y puedes perder la totalidad de lo que depositas.
>
> Este manual no es un robot que opera solo. Nosotros publicamos a diario el clima económico y el sesgo por activo; **la decisión, el cálculo del tamaño y la ejecución de cada orden son tuyas**, en tu plataforma y bajo tu criterio.

---

## 🧭 Cómo usar este manual

El manual está dividido en **12 módulos y 3 anexos**. Cada módulo es autocontenido: responde una pregunta concreta y no necesitas haber leído el anterior para aplicarlo.

| Si lo que quieres es… | Lee estos módulos |
|---|---|
| Entender qué estás operando antes de arriesgar un peso | **M0**, **M1** |
| Entender por qué se mueve el dinero en el mundo | **M2**, **M3** |
| Armar una operación concreta de principio a fin | **M4** → **M5** → **M6** → **M7** → **M8** |
| Saber cuándo NO operar | **M8**, **M9** |
| Consultar la regla de un activo puntual | **M10** |
| Repasar en 30 segundos antes de hacer clic | **M11** |
| Buscar una sigla o un umbral | **A1**, **A2** |

**Ruta recomendada la primera vez**: M0 → M1 → M2 → M3 → M4, y recién después el bloque de ejecución. **Ruta de consulta diaria**: M11, y desde ahí salta al módulo que necesites.

### Qué te damos nosotros y qué determinas tú

Esta separación es la clave del manual y conviene tenerla clara desde el principio:

| Insumo | De dónde sale | Por qué |
|---|---|---|
| **El clima** (régimen R0 a R4) y el **sesgo** por activo | Lo publicamos a diario | Requiere series oficiales de tasas, inflación y cobre que un operador particular no va a calcular a mano cada mañana |
| **El setup**, la **entrada**, el **stop**, el **objetivo**, el **tamaño** y los **filtros** | **Los determinas tú** en tu plataforma | Son reglas matemáticas que se leen del gráfico. Este manual te da todas |

El **Anexo A2** trae los umbrales exactos del clima, así que también puedes verificar por tu cuenta la clasificación que publicamos. Nada en este manual es una caja negra.

---

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 150" width="100%" height="150" xmlns="http://www.w3.org/2000/svg" style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <rect x="25" y="20" width="185" height="55" rx="6" fill="#FFFFFF" stroke="#0B1916" stroke-width="1.5"/>
  <text x="117" y="42" font-family="'Goldman', sans-serif" font-size="10.5" font-weight="700" fill="#0B1916" text-anchor="middle">1. EL CLIMA (D1)</text>
  <text x="117" y="58" font-size="9" fill="#64748B" text-anchor="middle">¿Confirmado por 2 días?</text>

  <line x1="210" y1="47" x2="255" y2="47" stroke="#50C0A8" stroke-width="2"/>
  <polygon points="255,47 248,43 248,51" fill="#50C0A8"/>
  <text x="232" y="40" font-family="'Goldman', sans-serif" font-size="8.5" font-weight="700" fill="#065F46" text-anchor="middle">SÍ</text>

  <line x1="117" y1="75" x2="117" y2="105" stroke="#E84040" stroke-width="1.5"/>
  <polygon points="117,105 113,98 121,98" fill="#E84040"/>
  <text x="127" y="93" font-family="'Goldman', sans-serif" font-size="8" font-weight="700" fill="#991B1B">NO</text>

  <rect x="260" y="20" width="185" height="55" rx="6" fill="#FFFFFF" stroke="#0B1916" stroke-width="1.5"/>
  <text x="352" y="42" font-family="'Goldman', sans-serif" font-size="10.5" font-weight="700" fill="#0B1916" text-anchor="middle">2. TU FICHA (H1)</text>
  <text x="352" y="58" font-size="9" fill="#64748B" text-anchor="middle">¿Los 8 campos completos?</text>

  <line x1="445" y1="47" x2="490" y2="47" stroke="#50C0A8" stroke-width="2"/>
  <polygon points="490,47 483,43 483,51" fill="#50C0A8"/>
  <text x="467" y="40" font-family="'Goldman', sans-serif" font-size="8.5" font-weight="700" fill="#065F46" text-anchor="middle">SÍ</text>

  <line x1="352" y1="75" x2="352" y2="105" stroke="#E84040" stroke-width="1.5"/>
  <polygon points="352,105 348,98 356,98" fill="#E84040"/>
  <text x="362" y="93" font-family="'Goldman', sans-serif" font-size="8" font-weight="700" fill="#991B1B">NO</text>

  <rect x="495" y="20" width="200" height="55" rx="6" fill="#F0FDF4" stroke="#50C0A8" stroke-width="2"/>
  <text x="595" y="42" font-family="'Goldman', sans-serif" font-size="10.5" font-weight="700" fill="#065F46" text-anchor="middle">3. EJECUCIÓN EN MT5</text>
  <text x="595" y="58" font-size="9" font-weight="600" fill="#047857" text-anchor="middle">Lote 1% + los 5 filtros</text>

  <rect x="45" y="105" width="145" height="28" rx="4" fill="#FEF2F2" stroke="#FCA5A5" stroke-width="1"/>
  <text x="117" y="123" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#991B1B" text-anchor="middle">🛑 MANOS QUIETAS</text>

  <rect x="280" y="105" width="145" height="28" rx="4" fill="#FEF2F2" stroke="#FCA5A5" stroke-width="1"/>
  <text x="352" y="123" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#991B1B" text-anchor="middle">🛑 MANOS QUIETAS</text>
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

Tu broker te permite mover un monto mucho mayor al que depositaste. Con apalancamiento 1:100, con $18.680 de garantía puedes mover un contrato de $1.868.000.

Eso corta para los dos lados, y de forma asimétrica en la práctica: **si tomas un tamaño demasiado grande para tu cuenta, un movimiento pequeño en contra te causa una pérdida severa muy rápido.** El **Módulo 7** existe para que eso no te pase, y es el módulo que más conviene no saltarse.

## 0.3 · Tres cosas que son tuyas y de nadie más

1. **La decisión de operar.** Nosotros publicamos el clima y el sesgo. Nada de eso es una orden de compra.
2. **El tamaño de la posición.** Nadie puede calcularlo por ti porque depende del capital de tu cuenta.
3. **El stop.** Si entras sin stop, no estás operando este método.

> [!IMPORTANT]
> **La regla que resume el manual entero**: el clima explica, tu ficha autoriza, el stop protege y el tamaño limita. Si un campo de tu ficha queda vacío, no hay orden.

---

# 🕯️ MÓDULO 1 · El lenguaje del gráfico: la vela H1 cerrada

**Pregunta que responde**: ¿qué dato del gráfico es confiable y cuál me puede engañar?

---

## 1.1 · Cuerpo, mecha y cierre

Todo este método trabaja sobre velas de **1 hora (H1)**. Cada vela cuenta lo que pasó en esa hora con tres elementos:

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 220" width="100%" height="220" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <line x1="220" y1="20" x2="220" y2="60" stroke="#0B1916" stroke-width="2"/>
  <rect x="207" y="60" width="26" height="100" rx="2" fill="#DCFCE7" stroke="#10B981" stroke-width="2"/>
  <line x1="220" y1="160" x2="220" y2="200" stroke="#0B1916" stroke-width="2"/>

  <text x="155" y="25" font-size="11" font-weight="700" fill="#0B1916" text-anchor="end">Máximo (High)</text>
  <line x1="160" y1="20" x2="210" y2="20" stroke="#94A3B8" stroke-width="1" stroke-dasharray="2,2"/>

  <text x="155" y="65" font-size="11" font-weight="700" fill="#065F46" text-anchor="end">Cierre (Close)</text>
  <line x1="160" y1="60" x2="207" y2="60" stroke="#059669" stroke-width="1.5"/>

  <text x="155" y="165" font-size="11" font-weight="700" fill="#0B1916" text-anchor="end">Apertura (Open)</text>
  <line x1="160" y1="160" x2="207" y2="160" stroke="#94A3B8" stroke-width="1.5"/>

  <text x="155" y="205" font-size="11" font-weight="700" fill="#0B1916" text-anchor="end">Mínimo (Low)</text>
  <line x1="160" y1="200" x2="210" y2="200" stroke="#94A3B8" stroke-width="1" stroke-dasharray="2,2"/>

  <rect x="310" y="25" width="380" height="170" rx="6" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="1"/>
  <text x="330" y="52" font-family="'Goldman', sans-serif" font-size="12" font-weight="700" fill="#0B1916">ANATOMÍA CLAVE</text>

  <circle cx="338" cy="78" r="4" fill="#50C0A8"/>
  <text x="350" y="82" font-size="10.5" font-weight="600" fill="#334155">1. Cuerpo: la batalla neta ganada en esa hora.</text>

  <circle cx="338" cy="110" r="4" fill="#3C8CAA"/>
  <text x="350" y="114" font-size="10.5" font-weight="600" fill="#334155">2. Mechas: precios extremos que fueron rechazados.</text>

  <rect x="325" y="138" width="350" height="42" rx="4" fill="#F0FDF4" stroke="#50C0A8" stroke-width="1"/>
  <text x="340" y="156" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#065F46">3. EL CIERRE: SE DECIDE AL MINUTO :00</text>
  <text x="340" y="170" font-size="9" font-weight="600" fill="#047857">Nunca a mitad de hora. La vela tiene que cerrar completa.</text>
</svg>
</div>

* **El cuerpo** es el rectángulo central: muestra la batalla real entre compradores y vendedores entre el inicio y el fin de esa hora.
* **Las mechas** son las líneas delgadas: muestran hasta dónde llegó el precio antes de ser rechazado.
* **El cierre** es el único dato que este método considera confiable.

## 1.2 · Por qué nunca se opera a mitad de hora

A las 10:20 una vela puede parecer una subida verde y contundente. A las 10:55 puede haberse revertido por completo y cerrar como una mecha de rechazo, contando la historia exactamente contraria.

**Todas las condiciones de este manual se evalúan sobre velas ya cerradas, al minuto :00.** No es una preferencia de estilo: una condición medida sobre una vela en formación puede darse y desaparecer en la misma hora, y entonces habrías entrado por una señal que nunca existió.

## 1.3 · Los cinco indicadores que necesitas en pantalla

El método completo se lee con estos cinco. El **Anexo A3** trae la instalación paso a paso.

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

#### Por qué se compra Oro cuando la inflación de EE.UU. sube

Esta es la pregunta que más se repite, y la respuesta tiene una vuelta que conviene entender, porque si te la salteas el método parece contradecirse.

El Oro no paga intereses. Un bono del Tesoro sí. Así que cuando eliges entre los dos, lo que comparas no es la inflación: es **lo que te queda del bono después de descontarle la inflación**. Eso es la tasa real, y es el número que manda.

Con eso claro, una inflación que sube puede terminar en dos lugares distintos:

* 🟢 Si la inflación sube **más rápido** de lo que la Reserva Federal sube su tasa, lo que le queda al bono se encoge. La tasa real baja, guardar metal deja de costarte rendimiento, y el Oro sube. Ese es el clima Inflación de este manual.
* 🔴 Si la Reserva Federal responde subiendo su tasa **más rápido** que la inflación, lo que le queda al bono crece. La tasa real sube y el Oro queda presionado a la baja, con la inflación igual de alta.

Por eso el filtro del Módulo 8.4 no mira la inflación: mira la tasa real, y el número concreto que revisas es el bono protegido contra inflación a 10 años. **La inflación sola no te dice hacia dónde va el Oro. Te dice que mires la tasa real.**

> [!NOTE]
> **Por qué el clima Inflación habilita la compra sin consultar la tasa real.** En un
> shock inflacionario la inflación esperada se mueve primero y la respuesta del banco
> central llega después, así que en esos días la tasa real tiende a quedarse quieta o a
> caer. El episodio de octubre de 2022 de la sección 3.5 es justamente eso: la inflación
> esperada subió 19 puntos base en cinco días, la tasa real bajó 2, y el Oro cerró el
> episodio al alza. Cuando la Reserva Federal ya reaccionó y la tasa real está subiendo,
> el clima deja de ser Inflación.

### 3. Los dos tipos de subida del petróleo

* **La metáfora**: no todas las subidas del combustible significan lo mismo.
* **En economía**:
  1. **Sube por demanda sana**: el comercio mundial acelera, hay más transporte y barcos consumiendo. Las bolsas y el petróleo suben juntos.
  2. **Sube por riesgo de suministro**: el crudo sube con fuerza por temor a cortes de oferta. El combustible caro encarece los costos de las empresas y frena el consumo, castigando a las bolsas.
* **Qué implica**: **el cobre es el que distingue una de otra**, y de eso depende cuánto riesgo toma el método. Si el crudo sube y el cobre lo acompaña, es demanda real y se sigue la tendencia con posición completa. Si el crudo sube solo, se opera **a la mitad del tamaño** y con el stop más ceñido. Está en el Módulo 10.

> ### ⚖️ Petróleo y Oro: ni gemelos ni enemigos
> * Si el mundo produce más, el petróleo puede subir y el oro no.
> * Si hay guerra, a menudo suben los dos.
> * Si el petróleo sube y el banco central se pone duro, el oro puede bajar el mismo día.
> * **Eso no autoriza vender oro porque el crudo subió.** Solo operas si la ficha del Oro te lo permite.

### 4. La verdulería del cobre y el dólar en Chile

* **La metáfora**: más de la mitad de las exportaciones chilenas son cobre.
* **En economía**: si el cobre sube en Londres y Nueva York, las mineras reciben más dólares. Para pagar sueldos, proveedores e impuestos en Chile traen esos dólares a Santiago y compran pesos.
* **Qué implica**: mucha oferta de dólares en Santiago baja el tipo de cambio, o sea peso fuerte. Si el cobre cae con fuerza, el dólar en Chile tiende a subir.

### 5. La carretera con lluvia

* **La metáfora**: en una autopista despejada puedes ir a 120 km/h con seguridad. Con lluvia torrencial y neblina bajas a 50 km/h para mantener **el mismo** nivel de seguridad.
* **En economía**: en el trading tu velocidad es el tamaño del lote.
* **Qué implica**: cuando la volatilidad se duplica, tu lote se reduce a la mitad. Y esto no lo tienes que recordar: **sale solo de la fórmula del Módulo 7**, porque el ATR entra en el denominador.

### 6. No adivinar soportes ni resistencias

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
| 📉 **Recesión** | `R4_RECESION_VUELO_CALIDAD` | El cobre cae con fuerza y la curva de bonos anticipa enfriamiento | Fuerte alza en USD/CLP (peso débil); materias primas en caída | **Apostar a la baja en USD/CLP** |
| ☀️ **Día bueno** | `R2_GOLDILOCKS_EXPANSION` | El cobre sube con tasas e inflación estables | Subidas en Nasdaq 100; USD/CLP a la baja (peso fuerte) | Vender acciones en tendencia |
| 🏖️ **Calma** | `R0_CALMA_RANGO` | Variables en equilibrio, sin noticias graves ni tendencias desatadas | El precio rebota ordenado entre soportes y resistencias | **Perseguir rupturas.** Solo rebotes |

## 3.0 · La cadena de cada clima, paso a paso

La tabla de arriba dice **qué** habilita cada clima. Esta sección dice **por qué**, y es la parte que conviene entender: si sigues la cadena, no necesitas memorizar la tabla. Los umbrales exactos están en el Anexo A2 y las siglas en el A1.

Antes de empezar, tres cosas que se repiten en las cinco cadenas:

* **El bono a 10 años de EE.UU.** es el interés que paga el gobierno estadounidense por endeudarse a diez años. Funciona como el precio base del dinero en el mundo: cuando sube, endeudarse sale más caro en todas partes.
* **La tasa real** es ese mismo interés ya descontada la inflación, o sea lo que de verdad le queda a quien presta. Es el competidor directo del Oro, y está explicado en el Módulo 2.2.
* **El cobre** cumple dos papeles a la vez y no hay que confundirlos: es el termómetro de la industria del mundo, y es además la principal exportación de Chile.

### 🌪️ Tormenta, paso a paso

1. Se corta o se encarece la oferta de energía, por un conflicto o por un recorte de producción. El petróleo sube con fuerza.
2. La energía más cara encarece el transporte, la electricidad y la fabricación. El mercado asume que los costos van a seguir subiendo.
3. Quien presta plata a diez años pide más interés para compensar esa inflación. **El bono a 10 años sube.**
4. Con el dinero más caro, las empresas que valen sobre todo por sus ganancias futuras valen menos hoy. El Nasdaq 100 queda bajo presión vendedora.
5. El capital sale de las economías emergentes y busca refugio en dólares. El USD/CLP sube.
6. Y el Oro sube **igual**, aunque las tasas hayan subido. Acá pesa más la búsqueda de refugio que el costo de oportunidad, y por eso el método prohíbe apostar a su baja.

**En tu pantalla**: en petróleo y Oro vas a ver velas H1 de rango amplio y cuerpos grandes, con el ATR marcando lecturas cada vez mayores. En el Nasdaq 100, cierres seguidos por debajo de la EMA 20 y alejándose de la EMA 50.

**Lo que te puede engañar**: petróleo subiendo con el cobre también subiendo y las bolsas en alza **no es Tormenta**, es demanda sana (Módulo 2.3). La Tormenta pide el crudo arriba, las tasas tensas y las bolsas bajo presión, las tres cosas juntas.

### 🛒 Inflación, paso a paso

1. Los precios esperados empiezan a subir, por energía, por salarios o por expectativas.
2. Quien compra bonos exige que le compensen esa pérdida de poder de compra. **La inflación esperada sube**, y se lee de los propios bonos.
3. El banco central todavía no responde, así que la tasa real se queda donde está o baja.
4. Con la tasa real quieta, guardar Oro deja de costarte rendimiento. El Oro queda firme.
5. Al mismo tiempo el mercado anticipa tasas más altas en EE.UU., y eso fortalece al dólar global. El USD/CLP sube.

**En tu pantalla**: el Oro sostenido sobre su EMA 20 en H1, con retrocesos cortos que no la pierden. El USD/CLP con sesgo alcista moderado.

**Lo que te puede engañar**: confundir "hay inflación alta en las noticias" con este clima. Si la Reserva Federal ya respondió y la tasa real está subiendo, el Oro sufre y el clima ya **no** es este. Lo que define a Inflación es que las expectativas le ganen a la tasa real, no el nivel de la inflación.

### 📉 Recesión, paso a paso

1. Las fábricas del mundo compran menos cobre, porque esperan producir menos.
2. **El cobre cae.**
3. La curva de bonos se da vuelta, o las tasas cortas caen con fuerza: el mercado empieza a descontar que el banco central va a tener que bajar tasas para reactivar.
4. Chile exporta cobre. Con el cobre más barato, **entran menos dólares al país.**
5. Con menos dólares ofrecidos en Santiago, el dólar sube contra el peso. El USD/CLP tiene sesgo alcista, y es el clima donde apostar a su baja está prohibido.

**En tu pantalla**: el USD/CLP con velas alcistas que van dejando mínimos cada vez más altos. El cobre y el Nasdaq 100 bajando en paralelo.

**Lo que te puede engañar**: un día de cobre cayendo no es Recesión. Hace falta que la curva de bonos acompañe (Anexo A2) y que el clima se confirme dos días seguidos. Un solo día raro no cambia nada.

### ☀️ Día bueno, paso a paso

1. Las fábricas compran **más** cobre: la economía del mundo está creciendo.
2. Y las tasas se quedan quietas. Eso es lo que distingue este clima: la economía crece **sin** que la inflación se descontrole.
3. Con el costo del dinero estable y las ganancias creciendo, las acciones de crecimiento suben. El Nasdaq 100 es el que mejor lo refleja.
4. A Chile entran más dólares por el cobre, así que el dólar baja contra el peso. **Es el único clima donde el sesgo del USD/CLP es a la baja.**

**En tu pantalla**: el Nasdaq 100 con las tres medias alineadas (EMA 20 sobre 50 sobre 100) y retrocesos que respetan la EMA 20. El USD/CLP haciendo lo contrario, con máximos cada vez más bajos.

**Lo que te puede engañar**: el cobre subiendo con las tasas disparadas **no** es Día bueno. La quietud de las tasas es una condición del clima, no un detalle de la tabla.

### 🏖️ Calma, paso a paso

1. Acá no hay cadena que seguir, y eso es justamente lo que hay que entender: **ningún umbral se cumple.** La Calma no se activa, es donde queda el mercado cuando ningún otro clima califica.
2. Sin una fuerza dominante que empuje en una dirección, el precio va y vuelve entre dos niveles.

**En tu pantalla**: las Bandas de Bollinger angostas, el ADX por debajo de 20, y el precio tocando una banda y volviendo al medio.

**Lo que te puede engañar**: aburrirte. La Calma es el clima más frecuente de todos, y la tentación es forzar una operación de tendencia donde no hay tendencia. Este clima habilita **solo** el rebote en rango del Módulo 5.3, y prohíbe perseguir rupturas.

## 3.1 · La regla de los dos días

El clima **no cambia por un solo día raro** ni por una noticia pasajera. El nuevo escenario tiene que repetirse **dos días hábiles seguidos** antes de confirmarse.

**La excepción**: si un dato supera el **150 % de su umbral** (por ejemplo el petróleo sobre +5,25 % en 5 días), el clima cambia de inmediato, sin esperar el segundo día. Es la protección ante un evento extremo.

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
* **Confianza bajo 65 %**: el modelo audita la frescura y la cobertura de sus propios datos. Bajo ese umbral el activo **no se comunica**, porque significa que falta un dato o está roto.

En los dos casos la respuesta es la misma: ese día ese activo no se opera.

<!-- INICIO graficos-regimenes (generado por scripts/grafico_regimen_svg.py) -->

## 3.5 · Cuándo pasó cada clima, de verdad

Los cinco climas no son categorías teóricas. Se pueden fechar, porque el mismo clasificador que corre hoy se puede aplicar a la historia. Abajo hay un episodio real de cada uno, con las cifras que lo activaron y lo que hicieron los activos en esos días.

**Cómo leer los gráficos**: cada uno tiene dos líneas, el driver arriba en verde y el activo abajo en gris, y la franja sombreada marca los días en que el clima estuvo confirmado. Cada línea tiene su propia escala y lleva su valor real en las dos puntas: lo que se compara es la forma, no la altura.

> **De dónde salen estos números.** El clasificador del motor se corrió sobre 5.951 días hábiles
> (de 3 de enero de 2003 a 7 de septiembre de 2026), con las mismas series que alimentan la clasificación de hoy. El límite es la tasa real de EE.UU., que se publica desde 2003. Ninguna cifra de esta sección está escrita a mano.

### 🌪️ Tormenta · del 1 al 10 de junio de 2022

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 200" width="100%" height="200" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
<rect x="321.2" y="42" width="101.1" height="118" fill="#50C0A8" opacity="0.12"/>
<text x="371.8" y="36" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#065F46" text-anchor="middle">CLIMA TORMENTA: 7 DÍAS</text>
<path d="M 148.0 85.9 L 162.4 75.3 L 176.9 80.6 L 191.3 88.4 L 205.8 80.8 L 220.2 79.6 L 234.6 86.5 L 249.1 79.8 L 263.5 78.9 L 277.9 69.0 L 292.4 72.7 L 306.8 74.4 L 321.2 71.8 L 335.7 67.0 L 350.1 60.8 L 364.6 62.5 L 379.0 59.1 L 393.4 52.0 L 407.9 53.2 L 422.3 55.6 L 436.8 55.0 L 451.2 61.0 L 465.6 71.6 L 480.1 65.0 L 494.5 88.7 L 508.9 85.9 L 523.4 98.6 L 537.8 100.0 L 552.2 90.2 L 566.7 83.1 L 581.1 76.5 L 595.6 82.5 L 610.0 94.0" stroke="#50C0A8" stroke-width="2.5" fill="none"/>
<path d="M 148.0 150.8 L 159.3 150.6 L 170.5 141.4 L 181.8 150.2 L 193.1 147.9 L 204.3 131.4 L 215.6 126.5 L 226.9 121.6 L 238.1 122.8 L 249.4 115.5 L 260.7 121.9 L 272.0 120.7 L 283.2 121.3 L 294.5 117.0 L 305.8 122.4 L 317.0 132.7 L 328.3 127.4 L 339.6 108.9 L 350.8 122.6 L 362.1 120.1 L 373.4 129.5 L 384.6 124.0 L 395.9 121.3 L 407.2 126.2 L 418.4 108.0 L 429.7 113.7 L 441.0 139.9 L 452.2 146.7 L 463.5 136.4 L 474.8 127.8 L 486.0 130.3 L 497.3 128.9 L 508.6 130.5 L 519.9 139.1 L 531.1 135.2 L 542.4 140.4 L 553.7 139.5 L 564.9 133.7 L 576.2 141.7 L 587.5 144.0 L 598.7 144.9 L 610.0 156.0" stroke="#64748B" stroke-width="2.5" fill="none"/>
<text x="138" y="70" font-size="9.5" font-weight="700" fill="#065F46" text-anchor="end">Petróleo WTI</text>
<text x="138" y="83" font-size="9" font-weight="600" fill="#64748B" text-anchor="end">110,52 US$/barril</text>
<text x="620" y="78" font-size="9" font-weight="700" fill="#065F46" text-anchor="start">107,76 US$/barril</text>
<text x="138" y="126" font-size="9.5" font-weight="700" fill="#0B1916" text-anchor="end">Oro</text>
<text x="138" y="139" font-size="9" font-weight="600" fill="#64748B" text-anchor="end">1.811,66 US$/onza</text>
<text x="620" y="134" font-size="9" font-weight="700" fill="#0B1916" text-anchor="start">1.804,37 US$/onza</text>
<line x1="148" y1="168" x2="610" y2="168" stroke="#E2E8F0" stroke-width="1"/>
<text x="148" y="182" font-size="8.5" font-weight="600" fill="#64748B">13 may 2022</text>
<text x="610" y="182" font-size="8.5" font-weight="600" fill="#64748B" text-anchor="end">30 jun 2022</text>
<text x="138" y="26" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#0B1916" text-anchor="end">🌪️ Tormenta</text>
</svg>
</div>

**Cómo leer este gráfico, en orden:**

**1. Empieza por el tramo verde a la izquierda de la franja.** Ahí está el gatillo: en los cinco días previos el petróleo subió +4,97 % y el bono a 10 años sumó +18 pb. Las dos cosas juntas son lo que define este clima, y los umbrales están en el Anexo A2.

**2. Ahora la franja.** El crudo entra en 115,26 US$/barril y sale en 120,73 US$/barril, tocando 121,94 en el camino. El shock no se agotó al confirmarse el clima: siguió.

**3. Recién ahora mira la línea gris de abajo, el Oro.** Va de 1.844,44 a 1.871,57 US$/onza. Fíjate en lo raro: las tasas de los bonos subieron, y por el Módulo 2.2 eso debería castigar al Oro. No lo castigó.


**La conclusión, en una frase.** En Tormenta el Oro aguanta aunque las tasas suban, porque lo que lo mueve en ese momento no es el costo de oportunidad sino la búsqueda de refugio. Por eso el método prohíbe apostar a su baja en este clima.

**Qué es la franja sombreada.** Son los 7 días hábiles en que el clima estuvo confirmado por la regla de los dos días. Lo que pasa **antes** de la franja es lo que lo activó; lo que pasa **dentro** es lo que tenías permitido y prohibido operar.

**Lo que lo activó** (variación en los 5 días previos al primero): cobre +0,10 %, petróleo +4,97 %, bono a 10 años +18 pb, tasa real +8 pb, inflación esperada +10 pb.

**Los activos en esos 7 días hábiles**: Oro +1,47 %, USD/CLP +2,47 %, WTI +6,43 %.

### 🛒 Inflación · del 14 al 25 de octubre de 2022

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 200" width="100%" height="200" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
<rect x="317.4" y="42" width="107.8" height="118" fill="#50C0A8" opacity="0.12"/>
<text x="371.3" y="36" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#065F46" text-anchor="middle">CLIMA INFLACIÓN: 8 DÍAS</text>
<path d="M 148.0 80.4 L 163.4 95.6 L 178.8 100.0 L 194.2 90.2 L 209.6 90.2 L 225.0 92.4 L 240.4 92.4 L 255.8 86.9 L 271.2 82.5 L 286.6 84.7 L 302.0 79.3 L 317.4 71.6 L 332.8 67.3 L 348.2 71.6 L 363.6 70.5 L 379.0 60.7 L 394.4 59.6 L 409.8 52.0 L 425.2 60.7 L 440.6 68.4 L 456.0 67.3 L 471.4 60.7 L 486.8 59.6 L 502.2 60.7 L 517.6 58.5 L 533.0 72.7 L 548.4 64.0 L 563.8 58.5 L 579.2 61.8 L 594.6 70.5 L 610.0 73.8" stroke="#50C0A8" stroke-width="2.5" fill="none"/>
<path d="M 148.0 146.8 L 160.2 143.5 L 172.3 144.3 L 184.5 143.4 L 196.6 132.5 L 208.8 124.7 L 220.9 124.0 L 233.1 127.4 L 245.3 133.0 L 257.4 134.1 L 269.6 142.8 L 281.7 142.9 L 293.9 141.3 L 306.1 141.8 L 318.2 149.8 L 330.4 147.8 L 342.5 148.1 L 354.7 148.0 L 366.8 155.7 L 379.0 156.0 L 391.2 145.5 L 403.3 146.0 L 415.5 148.1 L 427.6 145.8 L 439.8 142.9 L 451.9 142.8 L 464.1 149.7 L 476.3 149.8 L 488.4 152.0 L 500.6 147.6 L 512.7 152.0 L 524.9 151.5 L 537.1 137.7 L 549.2 140.1 L 561.4 140.3 L 573.5 128.2 L 585.7 128.2 L 597.8 114.2 L 610.0 108.0" stroke="#64748B" stroke-width="2.5" fill="none"/>
<text x="138" y="70" font-size="9.5" font-weight="700" fill="#065F46" text-anchor="end">Inflación esperada a 10 años</text>
<text x="138" y="83" font-size="9" font-weight="600" fill="#64748B" text-anchor="end">2,33 %</text>
<text x="620" y="78" font-size="9" font-weight="700" fill="#065F46" text-anchor="start">2,39 %</text>
<text x="138" y="126" font-size="9.5" font-weight="700" fill="#0B1916" text-anchor="end">Oro</text>
<text x="138" y="139" font-size="9" font-weight="600" fill="#64748B" text-anchor="end">1.653,45 US$/onza</text>
<text x="620" y="134" font-size="9" font-weight="700" fill="#0B1916" text-anchor="start">1.770,15 US$/onza</text>
<line x1="148" y1="168" x2="610" y2="168" stroke="#E2E8F0" stroke-width="1"/>
<text x="148" y="182" font-size="8.5" font-weight="600" fill="#64748B">28 sep 2022</text>
<text x="610" y="182" font-size="8.5" font-weight="600" fill="#64748B" text-anchor="end">11 nov 2022</text>
<text x="138" y="26" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#0B1916" text-anchor="end">🛒 Inflación</text>
</svg>
</div>

**Cómo leer este gráfico, en orden:**

**1. Mira la línea verde antes de la franja.** Es la inflación que el mercado descuenta para los próximos 10 años, leída de los bonos. En los cinco días previos subió +19 pb. Y en los mismos días la tasa real se movió -2 pb: prácticamente nada.

**2. Esa diferencia es todo el caso.** Los precios esperados subieron y lo que paga el bono descontada la inflación no las siguió. Es exactamente la rama verde del Módulo 2.2: la Reserva Federal todavía no había respondido.

**3. Ahora la línea gris, el Oro.** Entra en 1.644,29 y sale en 1.656,30 US$/onza, con un mínimo de 1.625,62 dentro del tramo. Venía de meses de caídas y acá se dio vuelta.


**La conclusión, en una frase.** El Oro no sube porque suba la inflación: sube cuando la inflación esperada le gana a la tasa real. Si la Reserva Federal hubiera subido su tasa más rápido, este mismo gráfico se vería al revés.

**Qué es la franja sombreada.** Son los 8 días hábiles en que el clima estuvo confirmado por la regla de los dos días. Lo que pasa **antes** de la franja es lo que lo activó; lo que pasa **dentro** es lo que tenías permitido y prohibido operar.

**Lo que lo activó** (variación en los 5 días previos al primero): cobre +1,11 %, petróleo -7,49 %, bono a 10 años +17 pb, tasa real -2 pb, inflación esperada +19 pb.

**Los activos en esos 8 días hábiles**: Oro +0,73 %, USD/CLP +0,37 %, WTI -0,37 %.

### 📉 Recesión · del 17 al 30 de julio de 2024

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 200" width="100%" height="200" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
<rect x="311.1" y="42" width="122.3" height="118" fill="#50C0A8" opacity="0.12"/>
<text x="372.2" y="36" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#065F46" text-anchor="middle">CLIMA RECESIÓN: 10 DÍAS</text>
<path d="M 148.0 69.8 L 161.6 67.4 L 175.2 67.2 L 188.8 59.8 L 202.4 52.0 L 215.9 54.4 L 229.5 57.4 L 243.1 55.4 L 256.7 62.0 L 270.3 56.0 L 283.9 60.6 L 297.5 66.3 L 311.1 69.3 L 324.6 78.1 L 338.2 81.3 L 351.8 83.8 L 365.4 86.1 L 379.0 89.2 L 392.6 88.3 L 406.2 88.9 L 419.8 91.7 L 433.4 91.6 L 446.9 85.2 L 460.5 91.4 L 474.1 90.2 L 487.7 96.9 L 501.3 95.1 L 514.9 100.0 L 528.5 99.5 L 542.1 97.2 L 555.6 92.2 L 569.2 93.4 L 582.8 94.2 L 596.4 86.6 L 610.0 87.4" stroke="#50C0A8" stroke-width="2.5" fill="none"/>
<path d="M 148.0 125.1 L 159.0 123.9 L 170.0 124.1 L 181.0 119.6 L 192.0 116.7 L 203.0 116.5 L 214.0 112.8 L 225.0 113.1 L 236.0 110.7 L 247.0 111.1 L 258.0 108.0 L 269.0 116.0 L 280.0 113.8 L 291.0 113.1 L 302.0 111.8 L 313.0 113.7 L 324.0 122.0 L 335.0 123.6 L 346.0 127.8 L 357.0 126.5 L 368.0 123.7 L 379.0 126.0 L 390.0 135.1 L 401.0 138.5 L 412.0 136.7 L 423.0 134.3 L 434.0 137.2 L 445.0 137.1 L 456.0 127.6 L 467.0 143.0 L 478.0 146.9 L 489.0 156.0 L 500.0 149.6 L 511.0 149.7 L 522.0 156.0 L 533.0 146.5 L 544.0 145.7 L 555.0 145.1 L 566.0 144.5 L 577.0 136.8 L 588.0 135.0 L 599.0 127.7 L 610.0 128.2" stroke="#64748B" stroke-width="2.5" fill="none"/>
<text x="138" y="70" font-size="9.5" font-weight="700" fill="#065F46" text-anchor="end">Cobre</text>
<text x="138" y="83" font-size="9" font-weight="600" fill="#64748B" text-anchor="end">4,3905 US$/libra</text>
<text x="620" y="78" font-size="9" font-weight="700" fill="#065F46" text-anchor="start">4,1275 US$/libra</text>
<text x="138" y="126" font-size="9.5" font-weight="700" fill="#0B1916" text-anchor="end">Nasdaq 100</text>
<text x="138" y="139" font-size="9" font-weight="600" fill="#64748B" text-anchor="end">19.679,48 puntos</text>
<text x="620" y="134" font-size="9" font-weight="700" fill="#0B1916" text-anchor="start">19.500,17 puntos</text>
<line x1="148" y1="168" x2="610" y2="168" stroke="#E2E8F0" stroke-width="1"/>
<text x="148" y="182" font-size="8.5" font-weight="600" fill="#64748B">28 jun 2024</text>
<text x="610" y="182" font-size="8.5" font-weight="600" fill="#64748B" text-anchor="end">16 ago 2024</text>
<text x="138" y="26" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#0B1916" text-anchor="end">📉 Recesión</text>
</svg>
</div>

**Cómo leer este gráfico, en orden:**

**1. El gatillo está en el cobre, la línea verde antes de la franja.** Cayó -4,53 % en cinco días. El cobre es el termómetro de la industria del mundo: si las fábricas compran menos cobre, es porque esperan producir menos.

**2. Dentro de la franja el cobre sigue.** De 4,3990 a 4,0630 US$/libra. No fue un día raro: fueron 10 días hábiles en la misma dirección.

**3. Ahora la línea gris, el Nasdaq 100.** De 19.860,35 a 18.987,84 puntos, un -4,39 %. La bolsa está descontando las mismas ganancias más chicas que anticipa el cobre.


**La conclusión, en una frase.** En Recesión el cobre avisa antes que la bolsa, y a Chile le llega por el bolsillo: si el mundo compra menos cobre, entran menos dólares al país y el dólar sube. En estos días el USD/CLP hizo +3,14 %.

**Qué es la franja sombreada.** Son los 10 días hábiles en que el clima estuvo confirmado por la regla de los dos días. Lo que pasa **antes** de la franja es lo que lo activó; lo que pasa **dentro** es lo que tenías permitido y prohibido operar.

**Lo que lo activó** (variación en los 5 días previos al primero): cobre -4,53 %, petróleo +0,92 %, bono a 10 años -12 pb, tasa real -11 pb, inflación esperada -1 pb.

**Los activos en esos 10 días hábiles**: Oro -2,36 %, USD/CLP +3,14 %, WTI -7,89 %, Nasdaq 100 -4,39 %.

### ☀️ Día bueno · del 19 de diciembre de 2025 al 9 de enero de 2026

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 200" width="100%" height="200" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
<rect x="293.9" y="42" width="158.1" height="118" fill="#50C0A8" opacity="0.12"/>
<text x="372.9" y="36" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#065F46" text-anchor="middle">CLIMA DÍA BUENO: 12 DÍAS</text>
<path d="M 148.0 96.5 L 160.2 97.4 L 172.3 92.7 L 184.5 93.6 L 196.6 100.0 L 208.8 98.2 L 220.9 90.4 L 233.1 97.8 L 245.3 95.0 L 257.4 97.6 L 269.6 93.7 L 281.7 93.5 L 293.9 89.8 L 306.1 89.9 L 318.2 87.9 L 330.4 86.8 L 342.5 73.0 L 354.7 87.2 L 366.8 75.0 L 379.0 80.0 L 391.2 79.5 L 403.3 64.9 L 415.5 60.5 L 427.6 70.8 L 439.8 74.0 L 451.9 68.4 L 464.1 61.8 L 476.3 62.5 L 488.4 60.5 L 500.6 63.7 L 512.7 71.9 L 524.9 72.7 L 537.1 74.9 L 549.2 74.2 L 561.4 65.6 L 573.5 61.8 L 585.7 69.8 L 597.8 66.5 L 610.0 52.0" stroke="#50C0A8" stroke-width="2.5" fill="none"/>
<path d="M 148.0 112.5 L 160.5 114.0 L 173.0 109.7 L 185.5 108.0 L 197.9 110.6 L 210.4 117.0 L 222.9 120.4 L 235.4 115.4 L 247.9 115.8 L 260.4 113.7 L 272.9 118.7 L 285.4 119.0 L 297.8 119.7 L 310.3 120.8 L 322.8 123.3 L 335.3 121.5 L 347.8 115.7 L 360.3 124.2 L 372.8 121.9 L 385.2 123.7 L 397.7 131.2 L 410.2 129.4 L 422.7 128.0 L 435.2 130.9 L 447.7 137.7 L 460.2 136.2 L 472.6 139.5 L 485.1 138.5 L 497.6 136.2 L 510.1 134.5 L 522.6 137.3 L 535.1 145.1 L 547.6 148.8 L 560.1 151.0 L 572.5 151.7 L 585.0 156.0 L 597.5 150.5 L 610.0 155.3" stroke="#64748B" stroke-width="2.5" fill="none"/>
<text x="138" y="70" font-size="9.5" font-weight="700" fill="#065F46" text-anchor="end">Cobre</text>
<text x="138" y="83" font-size="9" font-weight="600" fill="#64748B" text-anchor="end">5,3080 US$/libra</text>
<text x="620" y="78" font-size="9" font-weight="700" fill="#065F46" text-anchor="start">6,1755 US$/libra</text>
<text x="138" y="126" font-size="9.5" font-weight="700" fill="#0B1916" text-anchor="end">USD/CLP</text>
<text x="138" y="139" font-size="9" font-weight="600" fill="#64748B" text-anchor="end">919,00 pesos</text>
<text x="620" y="134" font-size="9" font-weight="700" fill="#0B1916" text-anchor="start">859,50 pesos</text>
<line x1="148" y1="168" x2="610" y2="168" stroke="#E2E8F0" stroke-width="1"/>
<text x="148" y="182" font-size="8.5" font-weight="600" fill="#64748B">3 dic 2025</text>
<text x="610" y="182" font-size="8.5" font-weight="600" fill="#64748B" text-anchor="end">29 ene 2026</text>
<text x="138" y="26" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#0B1916" text-anchor="end">☀️ Día bueno</text>
</svg>
</div>

**Cómo leer este gráfico, en orden:**

**1. El gatillo, en el cobre antes de la franja.** Subió +2,95 % en cinco días, y esta vez con las tasas quietas: el bono a 10 años se movió -3 pb. Esa quietud es la condición que separa este clima de los dos anteriores.

**2. Fíjate en que las dos líneas van al revés.** El cobre va de 5,4395 a 5,8555 US$/libra mientras el USD/CLP baja de 910,00 a 893,40 pesos. No es casualidad ni coincidencia: es el mismo hecho visto de dos lados.

**3. La cadena, en una línea.** El cobre sube, Chile lo exporta, entran más dólares al país, y con más dólares ofrecidos el dólar vale menos pesos. Es la verdulería del Módulo 2.4.


**La conclusión, en una frase.** Cuando el cobre sube con las tasas tranquilas, el peso chileno se fortalece y el dólar baja. Es el único clima donde el sesgo del USD/CLP es a la baja.

**Qué es la franja sombreada.** Son los 12 días hábiles en que el clima estuvo confirmado por la regla de los dos días. Lo que pasa **antes** de la franja es lo que lo activó; lo que pasa **dentro** es lo que tenías permitido y prohibido operar.

**Lo que lo activó** (variación en los 5 días previos al primero): cobre +2,95 %, petróleo -1,41 %, bono a 10 años -3 pb, tasa real -1 pb, inflación esperada -2 pb.

**Los activos en esos 12 días hábiles**: Oro +3,55 %, USD/CLP -1,82 %, WTI +4,14 %, Nasdaq 100 +1,61 %.

### 🏖️ Calma · del 11 de noviembre al 6 de diciembre de 2024

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 200" width="100%" height="200" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
<rect x="276.9" y="42" width="193.4" height="118" fill="#50C0A8" opacity="0.12"/>
<text x="373.6" y="36" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#065F46" text-anchor="middle">CLIMA CALMA: 19 DÍAS</text>
<path d="M 148.0 66.6 L 158.7 64.4 L 169.5 65.2 L 180.2 65.2 L 191.0 65.7 L 201.7 67.3 L 212.5 63.5 L 223.2 56.9 L 234.0 52.0 L 244.7 77.5 L 255.4 56.5 L 266.2 70.3 L 276.9 78.7 L 287.7 88.9 L 298.4 94.9 L 309.2 94.1 L 319.9 96.6 L 330.7 90.2 L 341.4 87.8 L 352.1 86.3 L 362.9 89.7 L 373.6 94.0 L 384.4 92.1 L 395.1 97.9 L 405.9 94.8 L 416.6 93.3 L 427.3 93.9 L 438.1 86.0 L 448.8 86.4 L 459.6 87.2 L 470.3 86.8 L 481.1 77.3 L 491.8 77.3 L 502.6 78.4 L 513.3 80.5 L 524.0 85.7 L 534.8 86.3 L 545.5 92.1 L 556.3 91.1 L 567.0 100.0 L 577.8 97.7 L 588.5 99.7 L 599.3 96.8 L 610.0 94.3" stroke="#50C0A8" stroke-width="2.5" fill="none"/>
<path d="M 148.0 155.4 L 159.0 153.6 L 170.0 156.0 L 181.0 147.7 L 192.0 144.2 L 203.0 149.2 L 214.0 146.6 L 225.0 140.4 L 236.0 152.1 L 247.0 133.5 L 258.0 124.1 L 269.0 119.0 L 280.0 125.4 L 291.0 128.7 L 302.0 124.7 L 313.0 131.0 L 324.0 131.3 L 335.0 130.6 L 346.0 130.5 L 357.0 118.3 L 368.0 127.7 L 379.0 125.8 L 390.0 126.6 L 401.0 126.3 L 412.0 129.7 L 423.0 125.8 L 434.0 131.5 L 445.0 128.7 L 456.0 132.9 L 467.0 128.5 L 478.0 134.3 L 489.0 129.0 L 500.0 128.9 L 511.0 125.4 L 522.0 118.2 L 533.0 114.6 L 544.0 116.9 L 555.0 108.0 L 566.0 113.1 L 577.0 114.1 L 588.0 114.1 L 599.0 115.1 L 610.0 114.1" stroke="#64748B" stroke-width="2.5" fill="none"/>
<text x="138" y="70" font-size="9.5" font-weight="700" fill="#065F46" text-anchor="end">Cobre</text>
<text x="138" y="83" font-size="9" font-weight="600" fill="#64748B" text-anchor="end">4,3195 US$/libra</text>
<text x="620" y="78" font-size="9" font-weight="700" fill="#065F46" text-anchor="start">4,0720 US$/libra</text>
<text x="138" y="126" font-size="9.5" font-weight="700" fill="#0B1916" text-anchor="end">USD/CLP</text>
<text x="138" y="139" font-size="9" font-weight="600" fill="#64748B" text-anchor="end">945,85 pesos</text>
<text x="620" y="134" font-size="9" font-weight="700" fill="#0B1916" text-anchor="start">989,85 pesos</text>
<line x1="148" y1="168" x2="610" y2="168" stroke="#E2E8F0" stroke-width="1"/>
<text x="148" y="182" font-size="8.5" font-weight="600" fill="#64748B">24 oct 2024</text>
<text x="610" y="182" font-size="8.5" font-weight="600" fill="#64748B" text-anchor="end">26 dic 2024</text>
<text x="138" y="26" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#0B1916" text-anchor="end">🏖️ Calma</text>
</svg>
</div>

**Cómo leer este gráfico, en orden:**

**1. Acá no hay gatillo que buscar, y eso es lo que hay que ver.** A la Calma no la activa ningún umbral: es donde queda el mercado cuando ningún otro clima califica. El cobre venía cayendo -4,45 %, pero la curva de bonos no acompañó, así que no llegó a ser Recesión.

**2. Mira la línea gris dentro de la franja.** El USD/CLP entra en 979,20 y sale en 974,50 pesos, un -0,48 % en 19 días hábiles. Entremedio se movió entre 969,85 y 985,35.

**3. Eso es un rango, no una tendencia.** El precio va y vuelve entre dos niveles. Perseguir una ruptura acá es comprar arriba justo antes de que el precio vuelva al medio, y por eso este clima lo prohíbe.


**La conclusión, en una frase.** La Calma es el clima más frecuente: son 6 de cada 10 días. No es un clima de espera sin nada que hacer, es el único donde se opera el rebote entre soporte y resistencia, que es el setup del Módulo 5.3.

**Qué es la franja sombreada.** Son los 19 días hábiles en que el clima estuvo confirmado por la regla de los dos días. Lo que pasa **antes** de la franja es lo que lo activó; lo que pasa **dentro** es lo que tenías permitido y prohibido operar.

**Los drivers de esos días** (variación en los 5 previos al primero): cobre -4,45 %, petróleo -3,60 %, bono a 10 años -7 pb, tasa real -9 pb, inflación esperada +2 pb.

**Los activos en esos 19 días hábiles**: Oro +0,52 %, USD/CLP -0,48 %, WTI -1,15 %, Nasdaq 100 +2,42 %.

> [!NOTE]
> **Un episodio no es una promesa.** Estos son casos de un clima, no el comportamiento garantizado de todos. Sirven para reconocer la forma del escenario, no para esperar el mismo porcentaje. El clima te dice qué dirección tienes permitida; el tamaño del movimiento no lo decide nadie.

<!-- FIN graficos-regimenes -->
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

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 180" width="100%" height="180" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <g transform="translate(10, 10)">
    <rect width="165" height="160" rx="6" fill="#F0FDF4" stroke="#50C0A8" stroke-width="1.5"/>
    <circle cx="28" cy="30" r="12" fill="#50C0A8"/>
    <text x="28" y="34" font-size="11" font-weight="700" fill="#04100D" text-anchor="middle">✓</text>
    <text x="48" y="34" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#065F46">VERDE</text>
    <text x="14" y="62" font-size="9" font-weight="700" fill="#047857">Los 8 campos listos</text>
    <text x="14" y="80" font-size="8" fill="#334155">Vela H1 cerrada.</text>
    <text x="14" y="93" font-size="8" fill="#334155">Filtros aprobados.</text>
    <rect x="10" y="115" width="145" height="32" rx="4" fill="#50C0A8"/>
    <text x="82" y="135" font-family="'Goldman', sans-serif" font-size="8.5" font-weight="700" fill="#04100D" text-anchor="middle">INGRESAR EN MT5</text>
  </g>

  <g transform="translate(185, 10)">
    <rect width="165" height="160" rx="6" fill="#FEFCE8" stroke="#F59E0B" stroke-width="1.5"/>
    <circle cx="28" cy="30" r="12" fill="#F59E0B"/>
    <text x="28" y="34" font-size="11" font-weight="700" fill="#FFFFFF" text-anchor="middle">⏳</text>
    <text x="48" y="34" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#92400E">AMARILLO</text>
    <text x="14" y="62" font-size="9" font-weight="700" fill="#B45309">Setup sin gatillo</text>
    <text x="14" y="80" font-size="8" fill="#334155">El clima habilita,</text>
    <text x="14" y="93" font-size="8" fill="#334155">la vela aún no gatilla.</text>
    <rect x="10" y="115" width="145" height="32" rx="4" fill="#D97706"/>
    <text x="82" y="135" font-family="'Goldman', sans-serif" font-size="8.5" font-weight="700" fill="#FFFFFF" text-anchor="middle">ESPERAR EL :00</text>
  </g>

  <g transform="translate(360, 10)">
    <rect width="165" height="160" rx="6" fill="#F8FAFC" stroke="#CBD5E1" stroke-width="1.5"/>
    <circle cx="28" cy="30" r="12" fill="#94A3B8"/>
    <text x="28" y="34" font-size="11" font-weight="700" fill="#FFFFFF" text-anchor="middle">○</text>
    <text x="48" y="34" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#334155">BLANCO</text>
    <text x="14" y="62" font-size="9" font-weight="700" fill="#475569">Ningún setup aplica</text>
    <text x="14" y="80" font-size="8" fill="#64748B">El clima y la</text>
    <text x="14" y="93" font-size="8" fill="#64748B">estructura no calzan.</text>
    <rect x="10" y="115" width="145" height="32" rx="4" fill="#64748B"/>
    <text x="82" y="135" font-family="'Goldman', sans-serif" font-size="8.5" font-weight="700" fill="#FFFFFF" text-anchor="middle">CERO ÓRDENES</text>
  </g>

  <g transform="translate(535, 10)">
    <rect width="175" height="160" rx="6" fill="#FEF2F2" stroke="#E84040" stroke-width="1.5"/>
    <circle cx="28" cy="30" r="12" fill="#E84040"/>
    <text x="28" y="34" font-size="11" font-weight="700" fill="#FFFFFF" text-anchor="middle">✕</text>
    <text x="48" y="34" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#991B1B">ROJO</text>
    <text x="14" y="62" font-size="9" font-weight="700" fill="#B91C1C">Un filtro bloquea</text>
    <text x="14" y="80" font-size="8" fill="#334155">Spread, horario, noticia,</text>
    <text x="14" y="93" font-size="8" fill="#334155">R:R o confirmación.</text>
    <rect x="10" y="115" width="155" height="32" rx="4" fill="#DC2626"/>
    <text x="87" y="135" font-family="'Goldman', sans-serif" font-size="8.5" font-weight="700" fill="#FFFFFF" text-anchor="middle">PROHIBIDO OPERAR</text>
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

# 📐 MÓDULO 5 · Los tres setups

**Pregunta que responde**: ¿qué tiene que hacer el precio para que yo tenga permiso de entrar?

---

El método usa **tres setups y ninguno más**, todos sobre velas H1 cerradas. Son **mutuamente excluyentes**: en cada momento aplica uno solo, y hay un orden para decidir cuál.

## 5.0 · Primero decides cuál aplica, y hay precedencia

No eliges el setup que más te gusta. Recorres este orden y te quedas con el primero que califique:

| Orden | Setup | Condición para que aplique |
|---|---|---|
| 1º | **Rebote en rango** (5.3) | Clima Calma **y** ADX menor a 20 |
| 2º | **Ruptura por compresión** (5.1) | Ancho del canal Donchian 50 **menor o igual a 2,5 × ATR** |
| 3º | **Retroceso al promedio** (5.2) | ADX **20 o más** **y** EMA 20 / 50 / 100 alineadas |
| 4º | **Ninguno** | Esperar. Es el resultado más frecuente |

> [!NOTE]
> **Dos condiciones que suelen pasarse por alto y que descartan la mayoría de los intentos.**
>
> El **ancho del canal** del segundo setup separa una compresión real de un canal ancho donde una ruptura no significa nada. Si el canal mide más de 2,5 veces el ATR, no hay compresión que romper.
>
> El **ADX** decide entre el primero y el tercero. Bajo 20 el mercado no tiene tendencia y el precio vuelve a su media; en 20 o más la tiene y los retrocesos se compran. Aplicar el setup de rango en un mercado con tendencia es operar contra el tren del Módulo 2.6.

## 5.1 · Ruptura por compresión

*El precio estaba apretado y cerró afuera.*

* **Cuándo aplica**: climas con tendencia (Recesión, Tormenta, Inflación o Día bueno).
* **Qué busca**: el precio estuvo comprimido en un rango estrecho las últimas 50 horas y una vela H1 **cierra fuera** del canal.
* **Las cuatro condiciones, todas obligatorias**:
  1. El **cierre** queda sobre el borde superior del canal Donchian 50 (en compras) o bajo el borde inferior (en ventas).
  2. **Regla del cuerpo**: el cuerpo mide **al menos la mitad (50 % o más)** del total de la vela. No sirve una mecha larga con cuerpo chico.
  3. **Rango de la vela igual o mayor a 1,0 × ATR**: la vela de ruptura tiene que ser al menos de tamaño normal. Una ruptura con una vela diminuta no tiene fuerza detrás.
  4. **RSI no extremo**: en compras el RSI va en 75 o menos; en ventas, en 25 o más. Entrar en un extremo es comprar el final del movimiento.
* **Entrada**: orden pendiente `BUY_STOP` en el **máximo de esa vela** (o `SELL_STOP` en el mínimo), con **vencimiento a 2 velas H1**. Si no se activa en dos horas, se cancela.

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 180" width="100%" height="180" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <rect x="20" y="15" width="220" height="150" rx="4" fill="#F8FAFC" stroke="#CBD5E1" stroke-dasharray="3,3"/>
  <text x="130" y="35" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#64748B" text-anchor="middle">50 HORAS COMPRIMIDAS</text>
  <line x1="30" y1="55" x2="230" y2="55" stroke="#CBD5E1" stroke-width="1.5"/>
  <line x1="30" y1="135" x2="230" y2="135" stroke="#CBD5E1" stroke-width="1.5"/>
  <text x="130" y="98" font-size="9" font-weight="600" fill="#64748B" text-anchor="middle">Canal Donchian 50</text>
  <text x="130" y="112" font-family="'Goldman', sans-serif" font-size="8.5" font-weight="700" fill="#065F46" text-anchor="middle">Ancho 2,1 × ATR (máx 2,5) ✓</text>

  <line x1="310" y1="20" x2="310" y2="40" stroke="#0B1916" stroke-width="2"/>
  <rect x="297" y="40" width="26" height="90" rx="2" fill="#DCFCE7" stroke="#10B981" stroke-width="2"/>
  <line x1="310" y1="130" x2="310" y2="160" stroke="#0B1916" stroke-width="2"/>

  <line x1="310" y1="20" x2="480" y2="20" stroke="#50C0A8" stroke-width="1.5" stroke-dasharray="3,3"/>
  <rect x="483" y="8" width="230" height="26" rx="4" fill="#F0FDF4" stroke="#50C0A8" stroke-width="1"/>
  <text x="493" y="25" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#065F46">BUY_STOP en el máximo · vence 2 velas</text>

  <text x="338" y="58" font-size="9" font-weight="700" fill="#065F46">Cierra fuera del canal</text>
  <text x="338" y="74" font-size="8.5" font-weight="700" fill="#047857">Cuerpo 71 % (mín 50 %)</text>
  <text x="338" y="90" font-size="8.5" font-weight="700" fill="#047857">Rango 1,3 × ATR (mín 1,0)</text>
  <text x="338" y="106" font-size="8.5" font-weight="700" fill="#047857">RSI 62 (máx 75)</text>

  <line x1="310" y1="160" x2="480" y2="160" stroke="#E84040" stroke-width="1.5" stroke-dasharray="3,3"/>
  <rect x="483" y="148" width="230" height="26" rx="4" fill="#FEF2F2" stroke="#FCA5A5" stroke-width="1"/>
  <text x="493" y="165" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#991B1B">STOP: ver Módulo 6, no el mínimo</text>
</svg>
</div>

## 5.2 · Retroceso al promedio

*El precio descansó sobre su media y volvió a retomar.*

* **Cuándo aplica**: mercados con tendencia direccional activa, con **ADX en 20 o más**.
* **Las tres condiciones, todas obligatorias**:
  1. **Las tres medias alineadas**: en compras, EMA 20 sobre EMA 50 sobre EMA 100. En ventas, al revés. Sin esa alineación no hay tendencia que respaldar, y es la condición que más se olvida.
  2. El **mínimo** de la vela toca o perfora la EMA 20 (en compras). En ventas es el **máximo** el que la toca o la perfora.
  3. El **cierre** queda sobre la EMA 20. El precio la perforó durante la hora, pero los compradores la recuperaron antes del cierre.
* **Entrada**: `BUY_STOP` en el **máximo de la vela de rebote** (en ventas, `SELL_STOP` en el mínimo), vencimiento a 2 velas H1.

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 180" width="100%" height="180" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <path d="M 40 130 Q 250 110 660 70" stroke="#3C8CAA" stroke-width="2.5" fill="none"/>
  <text x="672" y="66" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#3C8CAA" text-anchor="start">EMA 20</text>
  <path d="M 40 150 Q 250 133 660 96" stroke="#E8B44C" stroke-width="2" fill="none"/>
  <text x="672" y="99" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#854D0E" text-anchor="start">EMA 50</text>
  <path d="M 40 168 Q 250 154 660 122" stroke="#C158D6" stroke-width="2" fill="none"/>
  <text x="672" y="125" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#7E22CE" text-anchor="start">EMA 100</text>
  <text x="55" y="30" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#065F46">Las tres alineadas: 20 sobre 50 sobre 100</text>

  <line x1="360" y1="30" x2="360" y2="45" stroke="#0B1916" stroke-width="2"/>
  <rect x="347" y="45" width="26" height="40" rx="2" fill="#DCFCE7" stroke="#10B981" stroke-width="2"/>
  <line x1="360" y1="85" x2="360" y2="135" stroke="#0B1916" stroke-width="2"/>

  <circle cx="360" cy="112" r="5" fill="#E84040"/>
  <text x="378" y="122" font-size="9.5" font-weight="600" fill="#334155">Perfora la EMA 20 y cierra arriba</text>

  <line x1="360" y1="30" x2="500" y2="30" stroke="#50C0A8" stroke-width="1.5" stroke-dasharray="3,3"/>
  <rect x="503" y="18" width="185" height="26" rx="4" fill="#F0FDF4" stroke="#50C0A8" stroke-width="1"/>
  <text x="513" y="35" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#065F46">BUY_STOP en el máximo</text>
</svg>
</div>

## 5.3 · Rebote en rango

*El precio se salió de la banda y volvió a entrar.*

* **Cuándo aplica**: **solo** en clima Calma, y con **ADX bajo 20**.
* **Las tres condiciones, todas obligatorias**:
  1. La vela **anterior** cerró **fuera** de la banda de Bollinger, bajo la inferior en compras y sobre la superior en ventas.
  2. La vela **actual** cierra **de regreso adentro**.
  3. El **RSI** marca extremo: **bajo 35** en compras, **sobre 65** en ventas. Los dos lados tienen umbral, no solo el de compra.
* **Entrada**: `BUY_LIMIT` en el **precio de cierre** de la vela que reingresó (en ventas, `SELL_LIMIT` en ese mismo cierre). Es orden límite y no a mercado: si el precio se va sin ti, la operación no era.
* **Objetivo obligatorio**: la **media central de las bandas**, que es la media simple de 20. Nada más lejos. En un mercado lateral, buscar objetivos amplios es pedirle al precio algo que en rango no hace.

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 180" width="100%" height="180" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <line x1="40" y1="95" x2="600" y2="95" stroke="#E8783C" stroke-width="2" stroke-dasharray="4,4"/>
  <text x="608" y="99" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#9A3412" text-anchor="start">BANDA INFERIOR</text>

  <line x1="200" y1="80" x2="200" y2="98" stroke="#0B1916" stroke-width="1.5"/>
  <rect x="187" y="98" width="26" height="35" rx="2" fill="#FEF2F2" stroke="#E84040" stroke-width="1.5"/>
  <line x1="200" y1="133" x2="200" y2="148" stroke="#0B1916" stroke-width="1.5"/>
  <text x="200" y="160" font-size="8.5" font-weight="600" fill="#64748B" text-anchor="middle">1. Cierra afuera</text>

  <line x1="300" y1="45" x2="300" y2="60" stroke="#0B1916" stroke-width="1.5"/>
  <rect x="287" y="60" width="26" height="45" rx="2" fill="#DCFCE7" stroke="#10B981" stroke-width="1.5"/>
  <line x1="300" y1="105" x2="300" y2="125" stroke="#0B1916" stroke-width="1.5"/>
  <text x="300" y="160" font-family="'Goldman', sans-serif" font-size="8.5" font-weight="700" fill="#065F46" text-anchor="middle">2. Reingresa (gatillo)</text>

  <line x1="40" y1="32" x2="600" y2="32" stroke="#50C0A8" stroke-width="2"/>
  <text x="608" y="36" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#065F46" text-anchor="start">MEDIA CENTRAL</text>
  <text x="608" y="47" font-size="8" font-weight="700" fill="#047857" text-anchor="start">objetivo obligatorio</text>

  <rect x="360" y="108" width="330" height="42" rx="4" fill="#F0FDF4" stroke="#50C0A8" stroke-width="1"/>
  <text x="372" y="125" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#065F46">BUY_LIMIT en el cierre · RSI bajo 35</text>
  <text x="372" y="140" font-size="8.5" font-weight="600" fill="#047857">Exige clima Calma y ADX bajo 20, o no aplica</text>
</svg>
</div>

---

# 🛡️ MÓDULO 6 · El stop y el objetivo

**Pregunta que responde**: ¿dónde pongo el stop y hasta dónde aspiro, sin inventar?

---

## 6.1 · El stop: dos reglas, en este orden

Aquí hay una idea que conviene entender antes que la mecánica. **El stop no se pone donde te duele menos: se pone donde la operación deja de tener sentido.** Un stop muy pegado al precio te saca por ruido normal; uno muy lejano te hace perder más de lo presupuestado.

El método resuelve esa tensión con una regla de dos pasos:

```
Paso 1 · Mide la distancia al swing:
         distancia = | entrada − mínimo de las últimas 20 velas |
         (en ventas: máximo de las últimas 20 velas)

Paso 2 · Decide:
         si  0,5 × ATR  ≤  distancia  ≤  1,5 × ATR   →  stop = ese mínimo (o máximo)
         si no                                        →  stop = entrada − 1,5 × ATR
                                                          (en ventas: entrada + 1,5 × ATR)
```

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

```
riesgo    = | entrada − stop |
beneficio = | primer objetivo − entrada |
relación  = beneficio / riesgo
```

**Si la relación queda bajo 1,0, la operación no se toma.** Sin excepciones, sin "pero el setup estaba lindo".

**Y esto ocurre más seguido de lo que parece.** Fíjate en la aritmética: cuando el stop cae en la rama de 1,5 × ATR y el primer objetivo está a 1,0 × ATR, la relación es 1,0 / 1,5 = **0,67**, y la operación se cae sola. Es el caso del ejemplo del Módulo 4.3.

Dicho de otro modo: **este método solo autoriza la operación cuando el stop pudo apoyarse en un swing cercano**, porque solo entonces el riesgo es menor que el objetivo. Ese es el filtro trabajando, no una falla.

## 6.4 · La salida asimétrica: cuando no hay objetivo fijo

En activos con sesgo fuerte y sostenido, sobre todo el **Oro**, el método **prohíbe el objetivo rígido**. La razón es del Módulo 2.6: cerrar en un objetivo fijo te saca de la tendencia que justamente querías acompañar.

Se reemplaza por un **stop que persigue al precio**:

```
En compras:  stop = máximo de las últimas 22 velas  −  3,0 × ATR
En ventas:   stop = mínimo de las últimas 22 velas  +  3,0 × ATR
```

**Dos cosas que no se cambian:**

1. **El stop solo se mueve a favor.** Si el cálculo da un nivel peor que el actual, se ignora y el stop se queda donde está. Nunca se afloja.
2. **Las 22 velas y el 3,0 van juntos.** Son un par calibrado y separarlos deja el nivel indeterminado. Con 22 velas el nivel es utilizable; con 50, el "stop" puede quedar por encima del precio en una tendencia alcista normal, que es una contradicción y no un stop ceñido.

Contra la intuición: **una ventana más larga aprieta el stop, no lo suelta**, porque el máximo de más velas es más alto y el nivel resultante sube.

## 6.5 · Cuando la operación ya va ganando

Cuando el precio recorre la mitad del camino hacia el primer objetivo, o cuando cierra una vela H1 a tu favor, **puedes mover el stop al precio exacto de entrada**. A partir de ahí la operación no puede costarte dinero.

Es opcional y conservador: reduce tanto la pérdida posible como la probabilidad de aguantar hasta el segundo objetivo. Decídelo antes de entrar, no en el momento.

---

# 💰 MÓDULO 7 · El tamaño de la posición

**Pregunta que responde**: ¿cuántos lotes pongo para que una pérdida no me haga daño?

---

Este es el módulo que decide si sobrevives. Un método con buenas señales y mal tamaño quiebra la cuenta; un método con señales mediocres y buen tamaño aguanta.

## 7.1 · La regla: el 1 % es un presupuesto, no una meta

**Si la operación falla y toca el stop, la pérdida antes de costos debe ser el 1,0 % de tu capital.** Ese es todo el criterio.

```
                    Capital × 1 %
Lote  =  ─────────────────────────────────────────────
          Distancia al stop  ×  Valor de 1 unidad por lote
```

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

Medido contra una cuenta en pesos chilenos el **2026-09-04**, con el dólar en 935,60:

| Activo | Contrato | 1 unidad de cotización | Valor de 1 unidad por lote | 1 punto |
|---|---|---|---|---|
| **USD/CLP** | 100.000 USD | 1,00 peso | **$100.000 CLP** | $1.000 CLP |
| **Oro (XAU/USD)** | 100 onzas | 1,00 dólar | **$93.560 CLP** | $936 CLP |
| **WTI** | 100 barriles | 1,00 dólar | **$93.560 CLP** | $94 CLP |
| **Brent** | 100 barriles | 1,00 dólar | **$93.560 CLP** | $94 CLP |
| **Nasdaq 100** | 1 contrato | 1,00 punto de índice | **$936 CLP** | $9 CLP |

> [!NOTE]
> **Los valores en pesos se mueven con el dólar.** Salvo el USD/CLP, todos los demás cotizan en dólares, así que su valor en pesos cambia cuando cambia el tipo de cambio. La estructura (el contrato) es fija; la conversión no.
>
> **Verifícalo tú mismo en MT5** en vez de confiar en esta tabla: abre una operación de prueba en cuenta demo con 0,01 lotes, mira el resultado flotante y divide por el movimiento del precio. Es un minuto y te deja el número exacto de tu cuenta.

## 7.4 · Los cuatro pasos, con casos reales

Cuenta de **$1.000.000 CLP**, presupuesto del 1 % = **$10.000 CLP**. Los ATR son los medidos en H1 el 2026-09-04, y el tuyo será otro.

| Activo | ATR H1 | Stop (1,5 × ATR) | Lote teórico | **Lote real** | Pérdida en el stop | % de la cuenta |
|---|---|---|---|---|---|---|
| **USD/CLP** | 2,41 | 3,62 pesos | 0,0276 | **0,02** | $7.240 | 0,72 % |
| **WTI** | 0,771 | 1,157 dólares | 0,0924 | **0,09** | $9.742 | 0,97 % |
| **Nasdaq 100** | 84,47 | 126,70 puntos | 0,0844 | **0,08** | $9.483 | 0,95 % |
| **Oro** | 22,54 | 33,81 dólares | 0,0032 | **no operable** | no aplica | no aplica |

**Siempre se redondea hacia abajo.** 0,0276 baja a 0,02 y no sube a 0,03. Redondear hacia arriba rompe el presupuesto, y por eso las pérdidas reales de la tabla quedan bajo el 1 % y nunca sobre.

## 7.5 · Cuando un activo no alcanza para tu cuenta

Mira la última fila. El Oro pide un lote teórico de **0,0032**, y el volumen mínimo que acepta la plataforma es **0,01**. Ese mínimo, con un stop de 33,81 dólares, arriesga **$31.633 CLP**, o sea **3,16 %** de la cuenta: más del triple del presupuesto.

**La conclusión honesta es que hoy el Oro no es operable con una cuenta de $1.000.000 bajo la regla del 1 %.** Para que el lote mínimo represente el 1 % harían falta cerca de **$3.163.000 CLP**.

Esto no es una limitación del método, es aritmética del tamaño del contrato. Y responde una pregunta que casi todos se hacen alguna vez:

> [!IMPORTANT]
> **Si el lote que te sale es menor al mínimo, ese activo no es para tu cuenta todavía.** No se opera con el mínimo "porque es lo más chico que se puede". La alternativa correcta es elegir otro de los cinco activos, cuyo lote sí quepa, y volver al Oro cuando la cuenta lo permita.

## 7.6 · Comprueba que el margen entra

Un último paso rápido. El margen es la garantía que la plataforma retiene:

```
Margen = Lote × Contrato × (precio, convertido a la moneda de la cuenta) / apalancamiento
```

Para el caso del USD/CLP: 0,02 × 100.000 × 935,60 / 100 = **$18.712 CLP**, que sobre una cuenta de $1.000.000 no es problema.

Conviene mirarlo cuando el lote sale grande: **si el margen se come una fracción importante de la cuenta, el tamaño está mal** aunque la cuenta de riesgo cierre.

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

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 120" width="100%" height="120" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <line x1="40" y1="60" x2="680" y2="60" stroke="#CBD5E1" stroke-width="3"/>

  <circle cx="100" cy="60" r="10" fill="#50C0A8"/>
  <text x="100" y="40" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#065F46" text-anchor="middle">SESIÓN NORMAL</text>

  <rect x="215" y="30" width="125" height="60" rx="4" fill="#FEF2F2" stroke="#FCA5A5" stroke-width="1.5"/>
  <text x="277" y="52" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#991B1B" text-anchor="middle">ANTES DEL DATO</text>
  <text x="277" y="68" font-size="8" font-weight="600" fill="#B91C1C" text-anchor="middle">Cancelar pendientes</text>

  <circle cx="400" cy="60" r="16" fill="#E84040"/>
  <text x="400" y="66" font-family="'Goldman', sans-serif" font-size="13" font-weight="700" fill="#FFFFFF" text-anchor="middle">!</text>
  <text x="400" y="22" font-family="'Goldman', sans-serif" font-size="9.5" font-weight="700" fill="#991B1B" text-anchor="middle">DATO MACRO</text>

  <rect x="460" y="30" width="140" height="60" rx="4" fill="#FEF2F2" stroke="#FCA5A5" stroke-width="1.5"/>
  <text x="530" y="52" font-family="'Goldman', sans-serif" font-size="9" font-weight="700" fill="#991B1B" text-anchor="middle">DESPUÉS DEL DATO</text>
  <text x="530" y="68" font-size="8" font-weight="600" fill="#B91C1C" text-anchor="middle">Esperar vela cerrada</text>
</svg>
</div>

| Evento | Antes | Después |
|---|---|---|
| **Decisión de tasas de la Reserva Federal** | 30 min | **75 min** |
| **Empleo en EE.UU. (nóminas no agrícolas)** | 15 min | 30 min |
| **Inflación de EE.UU.** | 15 min | 30 min |
| **Reunión de política monetaria del Banco Central de Chile** | 15 min | 45 min · bloquea el USD/CLP |
| **Imacec e inflación de Chile** | 15 min | 20 min · bloquea el USD/CLP |

La ventana más larga es la de la Reserva Federal, y con razón: después del comunicado viene la conferencia de prensa, y el movimiento grande suele estar ahí y no en el número.

## 8.4 · Filtro de confirmación cruzada

Este filtro es el que le da el nombre al método, y es el que más se olvida. **La señal técnica de un activo tiene que estar respaldada por el mercado que lo mueve.**

| Activo | Qué se confirma | Se aprueba la compra si… |
|---|---|---|
| **USD/CLP** | Cobre | El cobre cae o está plano en 5 días, **o** el clima es Tormenta, Recesión o Inflación |
| **Oro** | Tasa real de EE.UU. | El clima es Tormenta o Inflación, **o** la tasa real está bajo 2,20 % |
| **WTI y Brent** | El propio petróleo | El clima es Tormenta, **o** el crudo sube más de 2,0 % en 5 días |
| **Nasdaq 100** | Tasa del bono a 10 años | La tasa está en 4,70 % o menos **y** el clima no es Tormenta ni Inflación |

**La lógica en una línea**: comprar dólar mientras el cobre sube es operar contra el motor del tipo de cambio en Chile. Comprar Nasdaq con la tasa del bono sobre 4,70 % es comprar acciones de crecimiento justo cuando el costo del dinero las castiga.

Si el respaldo no está, la operación queda en rojo aunque los ocho campos de la ficha estén completos.

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

## 9.1 · Los cuatro límites

| Límite | Umbral | Qué haces cuando se toca |
|---|---|---|
| **Riesgo simultáneo** | 2,5 % del capital en posiciones abiertas a la vez | No abres una más hasta cerrar alguna |
| **Pérdida diaria** | 2 operaciones perdedoras en el día (unos 2,0 %) | **Cierras la plataforma** y no operas más hoy |
| **Pérdida semanal** | 4,0 % acumulado en la semana | Suspendes hasta el lunes siguiente |
| **Racha** | 3 pérdidas consecutivas | Bajas el riesgo por operación al **0,5 %** hasta encadenar 2 ganadoras |

## 9.2 · Por qué el límite diario es de operaciones y no de porcentaje

Podría estar escrito como "para cuando pierdas el 2 %". Está escrito como **dos operaciones** a propósito: es un número que no admite interpretación en el momento en que menos ganas tienes de ser objetivo.

Dos pérdidas seguidas suelen significar que el mercado no está haciendo lo que tu lectura decía. La tercera operación de ese día casi nunca es análisis: es querer recuperar.

## 9.3 · La regla que evita el daño mayor

**Después de una pérdida, el tamaño no sube.** Ni "para recuperar lo de antes", ni porque la próxima señal se ve mejor. El presupuesto del 1 % se calcula sobre el capital **actual**, así que después de perder, el monto arriesgado baja solo. Eso es correcto y hay que dejarlo trabajar.

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

**Qué lo mueve**: la tasa real de EE.UU. (es el driver dominante y va en contra: si la tasa real sube, el oro sufre), la inflación esperada, y la tensión geopolítica.

| Condición | Sesgo | Dirección permitida | Prohibido |
|---|---|---|---|
| Clima Tormenta o Inflación, **o** tasa real bajo 2,20 % | +1,80 **fuerte alcista** | Solo compra: retroceso a EMA 20 o ruptura | **Vender, incluso con RSI en 80** |
| Resto | +0,40 alcista moderado | Compra: retroceso a EMA 50 o ruptura | Venta agresiva |

> [!IMPORTANT]
> **El Oro no lleva objetivo fijo.** Su salida es siempre el stop que persigue al precio del Módulo 6.4. Poner un objetivo rígido en Oro contradice la ficha.
>
> Y ojo con el Módulo 7.5: el Oro es el activo con el contrato más pesado de los cinco, así que suele ser el primero que queda fuera del alcance de una cuenta chica.

## 10.3 · WTI y Brent · Petróleo

**Qué lo mueve**: la demanda mundial, las decisiones de la OPEP (Organización de Países Exportadores de Petróleo) y la geopolítica. Pero lo que decide **cuánto riesgo tomas** es el cobre.

| Condición | Sesgo | Stop que persigue | Tamaño de la posición |
|---|---|---|---|
| Crudo al alza **con** el cobre subiendo 1,5 % o más | +1,50 alcista | 3,0 × ATR | **Completo** |
| Crudo al alza **sin** respaldo del cobre | +1,50 alcista | **2,0 × ATR** (más ceñido) | **La mitad** |
| Resto | 0,00 neutral | no aplica | Solo rango |

**Esta es la aplicación práctica del Módulo 2.3.** Si el crudo sube y el cobre lo acompaña, es demanda industrial real y la tendencia tiene respaldo. Si el crudo sube solo, sin el cobre detrás, responde a riesgo de suministro: el movimiento es más frágil y se puede dar vuelta rápido, así que se opera con la mitad del tamaño y el stop más cerca.

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

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 250" width="100%" height="250" xmlns="http://www.w3.org/2000/svg" style="background:#F8FAFC; border:1.5px solid #50C0A8; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <rect x="0" y="0" width="720" height="32" fill="#0B1916"/>
  <text x="20" y="21" font-family="'Goldman', sans-serif" font-size="11" font-weight="700" fill="#FFFFFF">CHECKLIST ANTES DEL CLIC</text>

  <circle cx="35" cy="58" r="10" fill="#50C0A8"/>
  <text x="35" y="62" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#04100D" text-anchor="middle">1</text>
  <text x="55" y="62" font-size="10" font-weight="600" fill="#0B1916">¿El clima está confirmado por 2 días y la confianza sobre 65 %?</text>

  <circle cx="35" cy="90" r="10" fill="#50C0A8"/>
  <text x="35" y="94" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#04100D" text-anchor="middle">2</text>
  <text x="55" y="94" font-size="10" font-weight="600" fill="#0B1916">¿La dirección que quiero tomar es la que el clima permite? (M10)</text>

  <circle cx="35" cy="122" r="10" fill="#50C0A8"/>
  <text x="35" y="126" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#04100D" text-anchor="middle">3</text>
  <text x="55" y="126" font-size="10" font-weight="600" fill="#0B1916">¿El setup calificó sobre una vela H1 CERRADA, con todas sus condiciones?</text>

  <circle cx="35" cy="154" r="10" fill="#50C0A8"/>
  <text x="35" y="158" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#04100D" text-anchor="middle">4</text>
  <text x="55" y="158" font-size="10" font-weight="600" fill="#0B1916">¿El stop sale de las 20 velas o de 1,5 × ATR, y el R:R llega a 1,0?</text>

  <circle cx="35" cy="186" r="10" fill="#50C0A8"/>
  <text x="35" y="190" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#04100D" text-anchor="middle">5</text>
  <text x="55" y="190" font-size="10" font-weight="600" fill="#0B1916">¿El lote es del 1 %, redondeado hacia abajo, y en la misma unidad?</text>

  <circle cx="35" cy="218" r="10" fill="#50C0A8"/>
  <text x="35" y="222" font-family="'Goldman', sans-serif" font-size="10" font-weight="700" fill="#04100D" text-anchor="middle">6</text>
  <text x="55" y="222" font-size="10" font-weight="600" fill="#0B1916">¿Spread bajo el tope del activo, horario válido, sin blackout, con confirmación?</text>
</svg>
</div>

Y una última pregunta que no está en el diagrama y conviene hacerse:

> **¿Estoy tomando esta operación porque calificó, o porque quiero recuperar la anterior?** Si la respuesta honesta es la segunda, revisa el Módulo 9.

<!-- INICIO caso-transversal (generado por scripts/caso_transversal.py) -->

## 11.1 · Un caso completo, de principio a fin

Hasta acá cada módulo resolvió una parte. Este caso las recorre todas de una sola vez, con un día real: el **24 de enero de 2023** en el USD/CLP. Todas las cifras salen de la serie del terminal, así que puedes reproducirlas en tu propia plataforma.

### Paso 1 · El clima (Módulo 3)

Ese día el clima confirmado era **Calma**, y no era del día: el episodio corrió del 19 al 24 de enero de 2023, o sea 4 días hábiles seguidos. La regla de los dos días estaba cumplida con holgura.

### Paso 2 · La dirección permitida (Módulos 3.3 y 10)

En Calma el cobre desempata, y acá está la parte que casi nadie revisa. El cobre venía **+0,72 % en cinco días**, o sea plano: ni cayendo 2,5 % ni subiendo 1,5 %. Con el cobre plano el sesgo del USD/CLP es neutral, y eso habilita **operar el rango**: compra en soporte, venta en resistencia.

> **Ojo con este paso, porque es el que más filtra.** En los últimos años hubo cinco rebotes del USD/CLP que cumplían el setup técnico completo. En cuatro de ellos el cobre venía subiendo más de 1,5 %, así que el sesgo era bajista y **la compra estaba prohibida**. Sobrevivió uno: este. El desempate del cobre no es un detalle, es lo que descarta la mayoría.

### Paso 3 · El setup, sobre una vela H1 cerrada (Módulo 5)

Con el clima en Calma y el ADX por debajo de 20, el orden de precedencia del Módulo 5.0 manda al **rebote en rango (5.3)**. Sus tres condiciones, más la que pide el clima, en esta vela:

| Condición | Se cumple con |
|---|---|
| La vela **anterior** cerró fuera de la banda inferior | cerró en 799,80 y la banda estaba en 800,56 |
| La vela **actual** cierra de regreso adentro | cerró en 802,55 con la banda en 799,78 |
| El **RSI** marca extremo, bajo 35 | RSI en 34,6 |
| Y el clima exige ADX bajo 20 | ADX en 19,3 |

La vela abrió en 800,00, marcó un máximo de 803,30, un mínimo de 800,00 y cerró en 802,55. **La entrada es una orden `BUY_LIMIT` en ese cierre: 802,55.** No a mercado: si el precio se va sin ti, la operación no era.

### Paso 4 · El stop (Módulo 6.1)

El ATR de 14 en H1 estaba en **4,63 pesos**. El mínimo de las últimas 20 velas era 797,80, o sea a **1,02 veces el ATR** de la entrada.

Esa distancia cae dentro de la banda de aceptación (entre 0,5 y 1,5 × ATR), así que el stop **se apoya en el swing**: 797,80. Es el mejor stop posible, porque es un nivel que el mercado ya respetó.

Riesgo por unidad: **4,75 pesos** de distancia entre la entrada y el stop.

### Paso 5 · El objetivo y el filtro de riesgo/beneficio (Módulos 6.2 y 6.3)

El rebote en rango tiene objetivo obligatorio y no se elige: **la media central de las bandas**, que estaba en 813,63. Beneficio esperado: 11,08 pesos.

```
relación = 11,08 / 4,75 = 2,33
```

**2,33 está sobre el mínimo de 1,0, así que la operación sigue viva.** Acá es donde se cae la mayoría de las fichas, y conviene ver por qué esta pasa: el stop se apoyó en un swing cercano en vez de irse a la distancia fija, y el objetivo del rebote es la media central, que estaba lejos porque el precio venía de tocar la banda de abajo.

### Paso 6 · El tamaño (Módulo 7)

La cuenta del ejemplo es de 1.000.000 pesos, así que el 1 % son 10.000 pesos. En el USD/CLP un peso de movimiento vale 100.000 pesos por lote (Módulo 7.3), y la distancia al stop está en **pesos**, que es la unidad de cotización: las dos cifras en la misma unidad, que es la regla segura del Módulo 7.2.

```
lote = 10.000 / (4,75 × 100.000) = 0,0211
```

Se redondea **hacia abajo**: **0,02 lotes**. Con ese volumen, si el stop se toca la pérdida es de 9.500 pesos, o sea el 0,95 % de la cuenta. Queda bajo el 1 % y nunca sobre, que es justamente para lo que sirve redondear hacia abajo.

El margen que inmoviliza la posición es de unos 16.051 pesos con apalancamiento 1:100, el 1,61 % de la cuenta, así que entra sin problema (Módulo 7.6).

### Paso 7 · Los filtros que faltan (Módulo 8)

Dos de los cinco filtros **no se pueden verificar sobre una serie histórica**, y los tienes que revisar tú en el momento:

* **El spread** (8.1): se lee en tu plataforma al momento de operar. En el USD/CLP el tope es el 15 % de la distancia al stop.
* **El horario** (8.2): el USD/CLP solo se opera entre las 09:00 y las 14:00 de Chile. La serie histórica viene en hora del servidor del broker, y ese desfase se mide contra el terminal conectado, así que este caso no te afirma una hora: la lees en tu pantalla.

El de noticias (8.3), el del Playbook y el de riesgo/beneficio (8.5) ya quedaron cubiertos en los pasos anteriores.

### La ficha completa

| Campo | Valor | Módulo |
|---|---|---|
| Activo | USD/CLP | tu elección |
| Clima confirmado | Calma, 4 días hábiles | M3 |
| Dirección permitida | Rango: compra en soporte (cobre +0,72 %) | M3.3, M10 |
| Setup activado | Rebote en rango | M5.3 |
| Entrada | `BUY_LIMIT` en 802,55 | M5.3 |
| Stop loss | 797,80 (swing de 20 velas, a 1,02 × ATR) | M6.1 |
| Objetivo | 813,63 (media central) · R:R 2,33 | M6.2, M6.3 |
| Volumen | 0,02 lotes · riesgo 9.500 pesos (0,95 %) | M7 |

> [!IMPORTANT]
> **Compara esta ficha con la del Módulo 4.3.** Son el mismo trabajo y terminan distinto: aquella se cayó en el campo 8 porque la relación quedó en 0,67, y esta pasa con 2,33. La diferencia no está en el setup ni en la suerte: está en que acá **el stop encontró un swing cercano** y el objetivo del rebote quedó lejos. Cuando el stop tiene que irse a la distancia fija, la relación no da y la ficha se cae. Eso es el método protegiéndote, no fallándote.

<!-- FIN caso-transversal -->
---

# 📚 ANEXO A1 · Glosario

---

### Del gráfico y los indicadores

* **Vela H1 cerrada**: una vela de una hora cuyo tiempo terminó, al minuto :00. Es el único dato que este método considera confiable.
* **Cuerpo y mecha**: el cuerpo es el rectángulo (de apertura a cierre); las mechas son las líneas finas que marcan los extremos rechazados.
* **ATR (rango medio real)**: cuánto se mueve típicamente un activo en un período. Es la medida de volatilidad que usa este método para el stop, el objetivo y el tamaño. Acá siempre se usa el de 14 períodos en H1.
* **EMA (media móvil exponencial)**: el promedio del precio de las últimas N velas, dando más peso a las recientes. Este método usa las de 20, 50 y 100.
* **SMA (media móvil simple)**: el mismo promedio pero sin dar más peso a las recientes. Es la línea central de las Bandas de Bollinger y el objetivo del rebote en rango. **No es lo mismo que la EMA 20**, aunque las dos usen 20 períodos.
* **Canal Donchian de 50**: el borde superior y el borde inferior de las últimas 50 velas. Define la compresión y la ruptura.
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
* **Racha (drawdown)**: la caída acumulada del capital desde su punto más alto.

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

# 📊 ANEXO A2 · Umbrales exactos del clima

---

Con esta tabla puedes verificar por tu cuenta la clasificación que publicamos. Todas las variaciones son a **5 días**.

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

> [!NOTE]
> **Dos ramas que es fácil pasar por alto** y que hacen que el clima se active más seguido de lo que parece: en **Inflación**, la curva plana **o** el bono subiendo más de 5 bps (cualquiera de las dos basta). En **Día bueno**, además del cobre y el bono estables, se exige que la tasa real **no suba**.

### Parámetros de riesgo, en una tabla

| Parámetro | Valor |
|---|---|
| Riesgo por operación | 1,0 % del capital |
| Distancia del stop, intradía | 1,5 × ATR de 14 en H1 |
| Distancia del stop, swing | 2,5 × ATR de 20 en diario |
| Stop que persigue | máximo de 22 velas − 3,0 × ATR |
| Stop que persigue, crudo sin respaldo del cobre | máximo de 22 velas − 2,0 × ATR |
| Canal Donchian | 50 períodos, ancho máximo 2,5 × ATR |
| Vencimiento de la orden pendiente | 2 velas H1 |
| Relación riesgo/beneficio mínima | 1,0 |
| Tope de spread | 15 % USD/CLP · 12 % Nasdaq · 10 % Oro, WTI y Brent |
| Confianza mínima del modelo | 65 % |

---

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
