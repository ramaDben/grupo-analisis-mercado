# Guía de Análisis y Operación: Trading Intermercado
### De la Macroeconomía Real a tu Plataforma MetaTrader 5
**Grupo de Análisis de Mercado — Departamento de Estudios y Research**  
*Manual Formativo para el Trader: Aprende a leer el clima económico, interpretar el semáforo y gestionar tu riesgo paso a paso.*

---

> [!CAUTION]
> Este documento es un material educativo y formativo de Grupo Inteligencia para que el **trader** aprenda a interpretar el análisis macroeconómico intermercado y aplicarlo de forma disciplinada en MetaTrader 5 (MT5). No constituye asesoría financiera personalizada ni garantiza rentabilidades futuras. El trading en Contratos por Diferencia (CFDs) con apalancamiento conlleva un alto riesgo de pérdida de capital.  
> 
> Esta guía es una herramienta de estudio y práctica analítica; **no es un robot que opera solo**. El sistema publica análisis y fichas técnicas diarias, pero tú eres el operador responsable que toma cada decisión y ejecuta manualmente las órdenes en tu propia plataforma bajo tu estricto criterio y control de riesgo.

---

# 📖 SECCIÓN 1: Qué Estás Haciendo de Verdad al Operar

---

## 💡 La Realidad del Mercado de CFDs

Antes de mirar cualquier gráfico o presionar un botón, como trader debes entender con total transparencia qué ocurre cuando operas en MetaTrader:

1. **No compras activos físicos**: Cuando abres una operación en USD/CLP, Oro (XAU/USD) o Nasdaq (US100), no estás comprando lingotes de oro en una bóveda ni acciones en Wall Street. Estás operando un **Contrato por Diferencia (CFD)** con tu broker, donde acuerdas intercambiar la diferencia entre el precio de entrada y el precio de salida.
2. **El arma de doble filo: El Apalancamiento**: Los brokers de CFDs te permiten operar montos mayores a tu dinero depositado. Si utilizas un tamaño de posición (lote) demasiado grande para el tamaño de tu cuenta, una pequeña variación en el precio en tu contra puede causarte pérdidas severas muy rápidamente.
3. **El Sistema te Orienta, Tú Decides**: Grupo Inteligencia analiza cada mañana las variables de la economía mundial y publica un **reporte de clima diario** y **fichas de operación**. El sistema nunca envía órdenes automáticas por ti. La disciplina, el cálculo del lote y la ejecución de la orden son 100% responsabilidad tuya como operador.

---

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 150" width="100%" height="150" xmlns="http://www.w3.org/2000/svg" style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Puerta 1 -->
  <rect x="25" y="20" width="185" height="55" rx="6" fill="#FFFFFF" stroke="#0F172A" stroke-width="1.5"/>
  <text x="117" y="42" font-size="10.5" font-weight="700" fill="#0F172A" text-anchor="middle">1. BRÚJULA MACRO (D1)</text>
  <text x="117" y="58" font-size="9" fill="#64748B" text-anchor="middle">¿Clima Confirmado por 2 Días?</text>
  
  <!-- Flecha SÍ 1 -->
  <line x1="210" y1="47" x2="255" y2="47" stroke="#10B981" stroke-width="2"/>
  <polygon points="255,47 248,43 248,51" fill="#10B981"/>
  <text x="232" y="40" font-size="8.5" font-weight="700" fill="#059669" text-anchor="middle">SÍ</text>

  <!-- Flecha NO 1 -->
  <line x1="117" y1="75" x2="117" y2="105" stroke="#E84040" stroke-width="1.5"/>
  <polygon points="117,105 113,98 121,98" fill="#E84040"/>
  <text x="127" y="93" font-size="8" font-weight="700" fill="#DC2626">NO</text>

  <!-- Puerta 2 -->
  <rect x="260" y="20" width="185" height="55" rx="6" fill="#FFFFFF" stroke="#0F172A" stroke-width="1.5"/>
  <text x="352" y="42" font-size="10.5" font-weight="700" fill="#0F172A" text-anchor="middle">2. FICHA TÉCNICA (H1)</text>
  <text x="352" y="58" font-size="9" fill="#64748B" text-anchor="middle">¿Semáforo en Luz Verde?</text>
  
  <!-- Flecha SÍ 2 -->
  <line x1="445" y1="47" x2="490" y2="47" stroke="#10B981" stroke-width="2"/>
  <polygon points="490,47 483,43 483,51" fill="#10B981"/>
  <text x="467" y="40" font-size="8.5" font-weight="700" fill="#059669" text-anchor="middle">SÍ</text>

  <!-- Flecha NO 2 -->
  <line x1="352" y1="75" x2="352" y2="105" stroke="#E84040" stroke-width="1.5"/>
  <polygon points="352,105 348,98 356,98" fill="#E84040"/>
  <text x="362" y="93" font-size="8" font-weight="700" fill="#DC2626">NO</text>

  <!-- Puerta 3 (Meta) -->
  <rect x="495" y="20" width="200" height="55" rx="6" fill="#ECFDF5" stroke="#10B981" stroke-width="2"/>
  <text x="595" y="42" font-size="10.5" font-weight="700" fill="#065F46" text-anchor="middle">3. EJECUCIÓN EN MT5</text>
  <text x="595" y="58" font-size="9" fill="#047857" text-anchor="middle">Lote 1% + Horario + Blackout</text>

  <!-- Cajas de NO OPERAR -->
  <rect x="45" y="105" width="145" height="28" rx="4" fill="#FEF2F2" stroke="#EF4444" stroke-width="1"/>
  <text x="117" y="123" font-size="9" font-weight="700" fill="#991B1B" text-anchor="middle">🛑 MANOS QUIETAS</text>

  <rect x="280" y="105" width="145" height="28" rx="4" fill="#FEF2F2" stroke="#EF4444" stroke-width="1"/>
  <text x="352" y="123" font-size="9" font-weight="700" fill="#991B1B" text-anchor="middle">🛑 MANOS QUIETAS</text>
</svg>
</div>

---

# 🕯️ SECCIÓN 2: Las Tres Palabras del Gráfico

---

## 🎯 Cuerpo, Mecha y Cierre: La Vela Japonesa de 1 Hora

En las plataformas de trading, el precio no se dibuja como una línea simple, sino a través de tres conceptos fundamentales: **Cuerpo**, **Mecha** y **Cierre** en bloques de tiempo de **1 Hora (H1)**.

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 220" width="100%" height="220" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Sombra / Mecha Superior -->
  <line x1="220" y1="20" x2="220" y2="60" stroke="#0F172A" stroke-width="2"/>
  <!-- Cuerpo de la Vela -->
  <rect x="175" y="60" width="90" height="100" rx="4" fill="#D1FAE5" stroke="#10B981" stroke-width="2"/>
  <!-- Sombra / Mecha Inferior -->
  <line x1="220" y1="160" x2="220" y2="200" stroke="#0F172A" stroke-width="2"/>

  <!-- Anotaciones Izquierda -->
  <text x="155" y="25" font-size="11" font-weight="700" fill="#0F172A" text-anchor="end">Máximo (High)</text>
  <line x1="160" y1="20" x2="210" y2="20" stroke="#94A3B8" stroke-width="1" stroke-dasharray="2,2"/>
  
  <text x="155" y="65" font-size="11" font-weight="700" fill="#059669" text-anchor="end">Cierre (Close)</text>
  <line x1="160" y1="60" x2="175" y2="60" stroke="#059669" stroke-width="1.5"/>

  <text x="155" y="165" font-size="11" font-weight="700" fill="#0F172A" text-anchor="end">Apertura (Open)</text>
  <line x1="160" y1="160" x2="175" y2="160" stroke="#94A3B8" stroke-width="1.5"/>

  <text x="155" y="205" font-size="11" font-weight="700" fill="#0F172A" text-anchor="end">Mínimo (Low)</text>
  <line x1="160" y1="200" x2="210" y2="200" stroke="#94A3B8" stroke-width="1" stroke-dasharray="2,2"/>

  <!-- Explicaciones Derecha -->
  <rect x="310" y="25" width="380" height="170" rx="6" fill="#F8FAFC" stroke="#E2E8F0" stroke-width="1"/>
  <text x="330" y="52" font-size="12" font-weight="700" fill="#0F172A">ANATOMÍA CLAVE PARA EL TRADER:</text>
  
  <circle cx="338" cy="78" r="4" fill="#10B981"/>
  <text x="350" y="82" font-size="10.5" font-weight="600" fill="#334155"><tspan font-weight="700" fill="#065F46">1. Cuerpo Pintado:</tspan> La batalla neta ganada entre 00:00 y 59:59.</text>
  
  <circle cx="338" cy="110" r="4" fill="#64748B"/>
  <text x="350" y="114" font-size="10.5" font-weight="600" fill="#334155"><tspan font-weight="700" fill="#0F172A">2. Mechas / Sombras:</tspan> Precios extremos que fueron rechazados.</text>
  
  <rect x="325" y="138" width="350" height="42" rx="4" fill="#EFF6FF" stroke="#BFDBFE" stroke-width="1"/>
  <text x="340" y="156" font-size="10" font-weight="700" fill="#1E40AF">⏱️ 3. EL CIERRE: OPERAMOS AL MINUTO :00</text>
  <text x="340" y="170" font-size="9" fill="#1E3A8A">Nunca a mitad de hora. Esperamos que la vela de 1H cierre por completo.</text>
</svg>
</div>

* **El Cuerpo Pintado**: Es el rectángulo central. Muestra la batalla real entre compradores y vendedores entre el inicio y el fin de esa hora.
* **Las Mechas (Sombras)**: Son las líneas delgadas arriba y abajo. Muestran los precios extremos donde el mercado intentó llegar pero fue rechazado.

> [!IMPORTANT]
> **Nunca operes a mitad de hora.** A las 10:20 una vela puede parecer una gran subida verde, pero a las 10:55 puede revertirse por completo y cerrar como una mecha de rechazo. Nuestro sistema evalúa y confirma patrones **únicamente cuando la vela de 1 hora ha cerrado por completo (al minuto :00)**.

---

# 🌍 SECCIÓN 3: El Clima Económico (6 Metáforas en Fácil)

---

Detrás de las reglas del mercado hay décadas de investigación económica formal. Aquí tienes los 6 pilares explicados a través de analogías cotidianas para el trader:

---

### 1. La Fábula de "Ricitos de Oro" (*Goldilocks Economy*)
* **La Metáfora**: En el cuento infantil, la niña prueba tres platos de sopa: uno está muy caliente, otro muy frío y el tercero está **en el punto perfecto**.
* **En Economía**: Es el clima soñado. La economía crece a paso firme (las fábricas producen y demandan cobre), pero la inflación está tranquila y las tasas de interés no suben.
* **Qué Hacemos**: Es el mejor escenario para las acciones tecnológicas (**Nasdaq 100 / US100**) y para que el peso chileno se fortalezca (**sesgo bajista en USD/CLP**).

---

### 2. El Dilema del Oro y las Tasas Reales
* **La Metáfora**: El Oro es un activo refugio histórico, pero **no paga dividendos, no genera intereses ni produce arriendos**.
* **En Economía**: Si el gobierno de EE.UU. te ofrece un bono soberano seguro indexado a inflación (TIPS 10 años) que paga una tasa de interés real atractiva, los grandes inversionistas prefieren cobrar ese interés antes que guardar lingotes en una bóveda. Cuando las tasas reales bajan o hay pánico de guerra, el dinero huye al Oro.
* **Qué Hacemos**: En climas de inflación o tensión bélica, **está prohibido apostar a la baja en Oro**.

---

### 3. Los Dos Tipos de Petróleo: ¿Demanda o Guerra?
* **La Metáfora**: No todas las subidas de combustible tienen el mismo impacto.
* **En Economía**:
  1. **Subida por Demanda Sana**: El comercio mundial acelera, hay más transporte y barcos consumiendo combustible → Las bolsas y el petróleo suben juntos.
  2. **Subida por Shock de Guerra**: El crudo se dispara por miedo a cortes de suministro en Medio Oriente → El combustible caro encarece los costos a las empresas y frena el consumo, castigando a las bolsas.
* **Qué Hacemos**: Cuando el petróleo sube con violencia junto a las tasas, el sistema clasifica un **shock de costos** y busca compras tácticas en Petróleo protegiéndose de caídas en acciones.

> ### ⚖️ Petróleo y Oro: Ni Gemelos ni Enemigos
> * Petróleo y oro no son gemelos ni enemigos.  
> * Si el mundo produce más, el petróleo puede subir y el oro no.  
> * Si hay guerra, a menudo suben los dos.  
> * Si el petróleo sube y el banco central se pone duro (sube tasas reales y el dólar se fortalece), el oro puede bajar el mismo día.  
> * **Eso no autoriza vender oro "porque el crudo subió".** Solo opera si la **ficha del oro está en verde**.

---

### 4. La Verdulería del Cobre y el Dólar en Chile
* **La Metáfora**: Más de la mitad de las exportaciones chilenas corresponden al cobre.
* **En Economía**: Si el precio del cobre sube en Londres y Nueva York, las empresas mineras reciben más dólares en el extranjero. Para pagar sueldos, proveedores e impuestos en Chile, traen esos dólares a Santiago y compran pesos chilenos.
* **Qué Hacemos**: Mucha oferta de dólares en Santiago hace que el tipo de cambio baje (peso fuerte). Si el cobre se derrumba, el dólar en Chile tiende a subir con fuerza.

---

### 5. La Carretera con Lluvia: El Tamaño de tu Posición
* **La Metáfora**: Si conduces en una autopista despejada en un día soleado, puedes ir a 120 km/h con seguridad. Si cae una lluvia torrencial con granizo y neblina, reduces tu velocidad a 50 km/h para mantener el mismo nivel de seguridad física.
* **En Economía**: En el trading, **tu velocidad es el tamaño del lote**.
* **Qué Hacemos**: Si el mercado entra en un día de tormenta y la volatilidad habitual se duplica, **tú reduces manualmente el tamaño de tu lote a la mitad**. De esa forma, tu riesgo en dinero se mantiene siempre bajo control en el límite presupuestado.

---

### 6. No Adivinar Techos ni Pisos
* **La Metáfora**: Las tendencias macroeconómicas son como trenes de carga pesados: demoran en frenar mucho más de lo que la intuición cree.
* **Qué Hacemos**: Queda prohibido apostar en contra de una tendencia macro sólida solo porque el precio "ya subió mucho". Se acompaña la estructura con órdenes pendientes y Stop Loss.

---

> [!NOTE]
> Las metáforas económicas te explican el **porqué** se mueve el dinero en el mundo. Sin embargo, para abrir una operación en tu plataforma, **el cuento no basta**: necesitas que el sistema emita una ficha en **Luz Verde (Listo para operar)**. Si la ficha dice esperar o bloquear, el cuento del cobre no autoriza hacer clic.

---

# 🌦️ SECCIÓN 4: Los 5 Climas del Mercado en Lenguaje Humano

---

Cada mañana, el análisis clasifica el mercado en uno de estos 5 escenarios oficiales evaluando datos soberanos:

| Clima | Nombre Técnico | Qué está pasando en la Economía | Qué suele ir mejor / peor | Qué te está Prohibido |
|---|---|---|---|---|
| 🌪️ **Tormenta** | `R3_ESTANFLACION_SHOCK` | El petróleo y las tasas suben con fuerza por tensiones geopolíticas o recortes de oferta. | Oro y Petróleo suelen ir fuertes *(si las tasas reales pegan muy fuerte, el oro puede no acompañar)*; acciones bajo presión; USD/CLP al alza. | **Prohibido vender Oro** o comprar acciones sin confirmación. |
| 🛒 **Inflación** | `R1_SHOCK_INFLACIONARIO` | Las expectativas de inflación suben más rápido que el crecimiento. | Oro firme; Dólar global firme; cautela en bolsas. | Prohibido operar contra la subida de tasas. |
| 📉 **Recesión** | `R4_RECESION_VUELO_CALIDAD` | El cobre se derrumba (≤ -2.5%) y la curva de bonos anticipa enfriamiento económico. | Fuerte alza en USD/CLP (peso débil); materias primas en caída. | **Prohibido apostar a la baja en USD/CLP**. |
| ☀️ **Día Bueno** | `R2_GOLDILOCKS_EXPANSION` | El cobre sube (fábricas activas) con tasas de interés e inflación estables. | Fuertes subidas en Nasdaq (US100); USD/CLP a la baja (peso fuerte). | Prohibido vender acciones en tendencia. |
| 🏖️ **Calma / Lateral** | `R0_CALMA_RANGO` | Variables en equilibrio, sin noticias graves ni tendencias desatadas. | Precios rebotan ordenados entre pisos y techos. | **Prohibido perseguir rupturas**; solo rebotes a la media. |

### 🛡️ Regla de los Dos Días (Anti-Ruido)
No cambiamos el clima por un solo día raro o una noticia pasajera. El sistema exige que el nuevo escenario se repita durante **2 días hábiles seguidos** antes de confirmar el cambio de sesgo (salvo eventos extremos de shock superior al 150%).

---

# 🚦 SECCIÓN 5: El Semáforo de Operación

---

Cada activo monitoreado presenta un estado claro en el reporte diario:

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 180" width="100%" height="180" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Tarjeta Verde -->
  <g transform="translate(10, 10)">
    <rect width="165" height="160" rx="6" fill="#F0FDF4" stroke="#10B981" stroke-width="1.5"/>
    <circle cx="28" cy="30" r="12" fill="#10B981"/>
    <text x="28" y="34" font-size="11" font-weight="700" fill="#FFFFFF" text-anchor="middle">✓</text>
    <text x="48" y="34" font-size="11" font-weight="700" fill="#065F46">VERDE</text>
    <text x="14" y="62" font-size="9" font-weight="700" fill="#047857">Listo para operar</text>
    <text x="14" y="80" font-size="8" fill="#334155">Vela H1 cerrada.</text>
    <text x="14" y="93" font-size="8" fill="#334155">Reglas cumplidas.</text>
    <rect x="10" y="115" width="145" height="32" rx="4" fill="#10B981"/>
    <text x="82" y="135" font-size="8.5" font-weight="700" fill="#FFFFFF" text-anchor="middle">¡INGRESAR EN MT5!</text>
  </g>

  <!-- Tarjeta Amarilla -->
  <g transform="translate(185, 10)">
    <rect width="165" height="160" rx="6" fill="#FFFBEB" stroke="#F59E0B" stroke-width="1.5"/>
    <circle cx="28" cy="30" r="12" fill="#F59E0B"/>
    <text x="28" y="34" font-size="11" font-weight="700" fill="#FFFFFF" text-anchor="middle">⏳</text>
    <text x="48" y="34" font-size="11" font-weight="700" fill="#92400E">AMARILLO</text>
    <text x="14" y="62" font-size="9" font-weight="700" fill="#B45309">Aún no cierra</text>
    <text x="14" y="80" font-size="8" fill="#334155">Patrón en formación.</text>
    <text x="14" y="93" font-size="8" fill="#334155">Esperar minuto :00.</text>
    <rect x="10" y="115" width="145" height="32" rx="4" fill="#F59E0B"/>
    <text x="82" y="135" font-size="8.5" font-weight="700" fill="#FFFFFF" text-anchor="middle">MANOS QUIETAS</text>
  </g>

  <!-- Tarjeta Blanca -->
  <g transform="translate(360, 10)">
    <rect width="165" height="160" rx="6" fill="#F8FAFC" stroke="#94A3B8" stroke-width="1.5"/>
    <circle cx="28" cy="30" r="12" fill="#94A3B8"/>
    <text x="28" y="34" font-size="11" font-weight="700" fill="#FFFFFF" text-anchor="middle">⚪</text>
    <text x="48" y="34" font-size="11" font-weight="700" fill="#334155">BLANCO</text>
    <text x="14" y="62" font-size="9" font-weight="700" fill="#475569">Hoy no hay trade</text>
    <text x="14" y="80" font-size="8" fill="#64748B">Mercado en calma</text>
    <text x="14" y="93" font-size="8" fill="#64748B">o sin dirección clara.</text>
    <rect x="10" y="115" width="145" height="32" rx="4" fill="#64748B"/>
    <text x="82" y="135" font-size="8.5" font-weight="700" fill="#FFFFFF" text-anchor="middle">CERO ÓRDENES</text>
  </g>

  <!-- Tarjeta Roja -->
  <g transform="translate(535, 10)">
    <rect width="175" height="160" rx="6" fill="#FEF2F2" stroke="#E84040" stroke-width="1.5"/>
    <circle cx="28" cy="30" r="12" fill="#E84040"/>
    <text x="28" y="34" font-size="11" font-weight="700" fill="#FFFFFF" text-anchor="middle">✕</text>
    <text x="48" y="34" font-size="11" font-weight="700" fill="#991B1B">ROJO</text>
    <text x="14" y="62" font-size="9" font-weight="700" fill="#B91C1C">Bloqueado</text>
    <text x="14" y="80" font-size="8" fill="#334155">Filtro activo:</text>
    <text x="14" y="93" font-size="8" fill="#334155">Spread, noticia o riesgo.</text>
    <rect x="10" y="115" width="155" height="32" rx="4" fill="#E84040"/>
    <text x="87" y="135" font-size="8.5" font-weight="700" fill="#FFFFFF" text-anchor="middle">PROHIBIDO OPERAR</text>
  </g>
</svg>
</div>

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 170" width="100%" height="170" xmlns="http://www.w3.org/2000/svg" style="background:#F8FAFC; border:1.5px solid #10B981; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <rect x="0" y="0" width="720" height="32" fill="#10B981"/>
  <text x="20" y="21" font-size="11" font-weight="700" fill="#FFFFFF">FICHA DE OPERACIÓN (EJEMPLO EN LUZ VERDE)</text>
  <text x="700" y="21" font-size="10" font-weight="700" fill="#FFFFFF" text-anchor="end">🟢 LISTO PARA OPERAR</text>

  <!-- Campos Ficha -->
  <text x="30" y="60" font-size="10" font-weight="700" fill="#64748B">SÍMBOLO:</text>
  <text x="120" y="60" font-size="11" font-weight="700" fill="#0F172A">USDCLP (Dólar vs Peso)</text>

  <text x="30" y="85" font-size="10" font-weight="700" fill="#64748B">CLIMA:</text>
  <text x="120" y="85" font-size="10.5" font-weight="600" fill="#0F172A">Recesión (Confirmado)</text>

  <text x="30" y="110" font-size="10" font-weight="700" fill="#64748B">PATRÓN:</text>
  <text x="120" y="110" font-size="10.5" font-weight="600" fill="#0F172A">Ruptura por Compresión</text>

  <text x="30" y="135" font-size="10" font-weight="700" fill="#64748B">TIPO ORDEN:</text>
  <text x="120" y="135" font-size="11" font-weight="700" fill="#059669">BUY_STOP (Pendiente - Expira 2h)</text>

  <!-- Lado Derecho: Precios -->
  <line x1="380" y1="45" x2="380" y2="155" stroke="#E2E8F0" stroke-width="1.5"/>

  <text x="400" y="60" font-size="10" font-weight="700" fill="#64748B">PRECIO ENTRADA:</text>
  <text x="540" y="60" font-size="11" font-weight="700" fill="#0F172A">934.00 (1 tick sobre max)</text>

  <text x="400" y="85" font-size="10" font-weight="700" fill="#64748B">STOP LOSS:</text>
  <text x="540" y="85" font-size="11" font-weight="700" fill="#DC2626">930.50 (Protección)</text>

  <text x="400" y="110" font-size="10" font-weight="700" fill="#64748B">OBJETIVO (TP1):</text>
  <text x="540" y="110" font-size="11" font-weight="700" fill="#059669">938.00 (Ganancia 1R)</text>

  <text x="400" y="135" font-size="10" font-weight="700" fill="#64748B">BENEFICIO/RIESGO:</text>
  <text x="540" y="135" font-size="10.5" font-weight="700" fill="#0F172A">1.14 (Mayor a 1.0 ✓)</text>
</svg>
</div>

> ### 🛑 El Mantra Operativo de Mesa
> * **El contexto macro explica.**
> * **La ficha autoriza.**
> * **El stop protege.**
> * **El tamaño limita.**
> * **Si no está en VERDE, no hay orden.**

---

# 📐 SECCIÓN 6: Tres Formas de Entrar al Mercado

---

En gráficos de 1 Hora, el sistema solo utiliza 3 patrones matemáticos precisos sobre velas cerradas:

---

### 1. Ruptura por Compresión (El precio estaba apretado y cerró fuera)
* **Cuándo se usa**: En climas con tendencia (Recesión, Tormenta, Inflación o Expansión).
* **Qué busca**: El precio estuvo comprimido en un rango estrecho durante las últimas 50 horas y de pronto una vela de 1 hora **cierra con fuerza rompiendo el techo** (en compras) o el piso (en ventas).
* **La Regla del Cuerpo**: La parte pintada de la vela debe representar **al menos la mitad (≥ 50%) de todo su tamaño** (no una mecha larga).
* **Cómo se entra en MT5**: Se coloca una orden pendiente `BUY_STOP` 1 tick por encima del máximo de esa vela ya cerrada, con **vencimiento a 2 horas (2 barras H1)**.
* **Stop Loss**: Estrictamente **1 tick por debajo del mínimo** de esa misma vela de ruptura.

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 180" width="100%" height="180" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <rect x="20" y="15" width="220" height="150" rx="4" fill="#F8FAFC" stroke="#E2E8F0" stroke-dasharray="3,3"/>
  <text x="130" y="35" font-size="9.5" font-weight="700" fill="#64748B" text-anchor="middle">50 HORAS COMPRIMIDAS</text>
  <line x1="30" y1="55" x2="230" y2="55" stroke="#CBD5E1" stroke-width="1.5"/>
  <line x1="30" y1="135" x2="230" y2="135" stroke="#CBD5E1" stroke-width="1.5"/>
  <text x="130" y="100" font-size="9" fill="#94A3B8" text-anchor="middle">Canal Estrecho Donchian 50</text>

  <!-- Vela de Ruptura -->
  <line x1="310" y1="20" x2="310" y2="40" stroke="#0F172A" stroke-width="2"/>
  <rect x="285" y="40" width="50" height="90" rx="3" fill="#D1FAE5" stroke="#10B981" stroke-width="2"/>
  <line x1="310" y1="130" x2="310" y2="160" stroke="#0F172A" stroke-width="2"/>

  <!-- Anotaciones de Entrada -->
  <line x1="310" y1="20" x2="480" y2="20" stroke="#059669" stroke-width="1.5" stroke-dasharray="3,3"/>
  <rect x="485" y="8" width="215" height="26" rx="4" fill="#ECFDF5" stroke="#10B981" stroke-width="1"/>
  <text x="495" y="25" font-size="9.5" font-weight="700" fill="#065F46">ORDEN: BUY_STOP (Expira en 2h)</text>

  <!-- Cierre con Cuerpo Dominante -->
  <text x="345" y="60" font-size="10" font-weight="700" fill="#059669">Cierre 933.50</text>
  <text x="345" y="75" font-size="8.5" fill="#334155">Cierra fuera del canal previo</text>
  <text x="345" y="90" font-size="8.5" font-weight="700" fill="#047857">Cuerpo = 71% de la vela (≥ 50% ✓)</text>

  <!-- Stop Loss -->
  <line x1="310" y1="160" x2="480" y2="160" stroke="#DC2626" stroke-width="1.5" stroke-dasharray="3,3"/>
  <rect x="485" y="148" width="215" height="26" rx="4" fill="#FEF2F2" stroke="#EF4444" stroke-width="1"/>
  <text x="495" y="165" font-size="9.5" font-weight="700" fill="#991B1B">STOP LOSS: 930.50 (Bajo mínimo)</text>
</svg>
</div>

---

### 2. Retroceso al Promedio (El precio descansó y volvió a subir)
* **Cuándo se usa**: En mercados con tendencia direccional activa y fuerte.
* **Qué busca**: El precio venía subiendo, hace una pausa bajando hasta su promedio móvil rápido (EMA 20), pero durante la hora los compradores reaccionan y la vela **cierra por encima del promedio**.
* **Cómo se entra en MT5**: Orden pendiente `BUY_STOP` 1 tick sobre el máximo de la vela de rebote, con **vencimiento a 2 horas**.
* **Stop Loss**: Estrictamente **1 tick por debajo del mínimo de la mecha de rechazo intradiaria**.

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 180" width="100%" height="180" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Línea de Promedio Móvil EMA 20 -->
  <path d="M 40 130 Q 250 110 680 70" stroke="#0284C7" stroke-width="2.5" fill="none"/>
  <text x="680" y="60" font-size="10" font-weight="700" fill="#0284C7" text-anchor="end">PROMEDIO RÁPIDO (EMA 20)</text>

  <!-- Vela de Rebote -->
  <line x1="360" y1="30" x2="360" y2="45" stroke="#0F172A" stroke-width="2"/>
  <rect x="335" y="45" width="50" height="40" rx="3" fill="#D1FAE5" stroke="#10B981" stroke-width="2"/>
  <line x1="360" y1="85" x2="360" y2="135" stroke="#0F172A" stroke-width="2"/>

  <!-- Anotación de la mecha tocando EMA -->
  <circle cx="360" cy="105" r="5" fill="#E84040"/>
  <text x="380" y="115" font-size="9.5" font-weight="600" fill="#334155">Perfora la EMA intradiario pero <tspan font-weight="700" fill="#059669">cierra arriba</tspan></text>

  <!-- Entrada BUY STOP -->
  <line x1="360" y1="30" x2="520" y2="30" stroke="#059669" stroke-width="1.5" stroke-dasharray="3,3"/>
  <rect x="525" y="18" width="180" height="26" rx="4" fill="#ECFDF5" stroke="#10B981" stroke-width="1"/>
  <text x="535" y="35" font-size="9.5" font-weight="700" fill="#065F46">BUY_STOP: Sobre el máximo</text>
</svg>
</div>

---

### 3. Rebote en Calma (El precio se salió de la banda y volvió a entrar)
* **Cuándo se usa**: Estrictamente en clima de **Calma / Rango**.
* **Qué busca**: El precio cayó fuera de los límites habituales (Banda de Bollinger inferior), y la siguiente vela **cierra de regreso dentro del canal** con el oscilador marcando sobreventa extrema (RSI < 35).
* **Cómo se entra en MT5**: Orden de compra al minuto :00 inmediatamente tras confirmar el cierre de la barra adentro.
* **Stop Loss**: Estrictamente en el **mínimo de la excursión previa fuera de la banda**.
* **Salida Obligatoria**: Tu ganancia se toma **exclusivamente en el promedio central de la banda (SMA 20)**. Prohibido buscar objetivos lejanos en mercados laterales.

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 180" width="100%" height="180" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <!-- Banda Inferior Bollinger -->
  <line x1="40" y1="90" x2="680" y2="90" stroke="#F59E0B" stroke-width="2" stroke-dasharray="4,4"/>
  <text x="680" y="80" font-size="10" font-weight="700" fill="#D97706" text-anchor="end">BANDA INFERIOR (PISO DEL CANAL)</text>

  <!-- Vela 1 (Cierra afuera) -->
  <line x1="200" y1="70" x2="200" y2="85" stroke="#0F172A" stroke-width="1.5"/>
  <rect x="185" y="85" width="30" height="35" rx="2" fill="#FEE2E2" stroke="#EF4444" stroke-width="1.5"/>
  <line x1="200" y1="120" x2="200" y2="135" stroke="#0F172A" stroke-width="1.5"/>
  <text x="200" y="155" font-size="8.5" fill="#64748B" text-anchor="middle">Cierra fuera</text>

  <!-- Vela 2 (Reingresa adentro) -->
  <line x1="300" y1="40" x2="300" y2="55" stroke="#0F172A" stroke-width="1.5"/>
  <rect x="285" y="55" width="30" height="45" rx="2" fill="#D1FAE5" stroke="#10B981" stroke-width="1.5"/>
  <line x1="300" y1="100" x2="300" y2="120" stroke="#0F172A" stroke-width="1.5"/>
  <text x="300" y="155" font-size="8.5" font-weight="700" fill="#059669" text-anchor="middle">Reingresa (Gatillo)</text>

  <!-- Objetivo TP1 en SMA20 -->
  <line x1="40" y1="30" x2="680" y2="30" stroke="#10B981" stroke-width="2"/>
  <text x="680" y="22" font-size="10" font-weight="700" fill="#059669" text-anchor="end">PROMEDIO CENTRAL SMA 20 (SALIDA OBLIGATORIA TP1)</text>

  <rect x="420" y="105" width="270" height="40" rx="4" fill="#F0FDF4" stroke="#50C0A8" stroke-width="1"/>
  <text x="430" y="122" font-size="9" font-weight="700" fill="#065F46">ENTRADA: Compra al minuto :00 (924.00)</text>
  <text x="430" y="136" font-size="8.5" fill="#047857">TP1 obligatorio en la media (929.00). SL bajo mínimo exterior.</text>
</svg>
</div>

### 🛡️ Gestión de la Operación Abierta (Break-Even)
Una vez que tu orden pendiente se activa y el precio avanza a tu favor alcanzando el **50% del recorrido hacia el Objetivo 1** (o cuando cierra la siguiente vela de 1 hora a tu favor), puedes mover tu Stop Loss al precio exacto de entrada (**Break-Even**). Con esto eliminas el riesgo financiero de la posición.

---

# 💰 SECCIÓN 7: Cuánto Arriesgar (Presupuesto del 1.0%)

---

## 🛡️ El Riesgo es un Presupuesto Teórico, No una Garantía Mágica

El cálculo del tamaño de tu posición (lote) tiene un único objetivo: **definir que si la operación falla y toca el Stop Loss, la pérdida teórica previa a costos sea del 1.0% de tu capital**.

### ⚖️ Regla de Viabilidad por Spread (Fricción Real)
En MetaTrader 5, el spread típico de USD/CLP durante la rueda bancaria es de **0.40 a 0.60 pesos (40 a 60 puntos)**:
* **Filtro Obligatorio**: Si el spread actual supera el **15% de la distancia al Stop Loss** (Spread / Distancia SL > 0.15), la operación queda automáticamente **bloqueada por fricción excesiva**.
* *Ejemplo*: Si tu Stop Loss está a 3.50 pesos, el spread máximo tolerable es de 0.52 pesos (3.50 x 0.15). Si el broker tiene 0.80 pesos de spread en ese momento, no se opera.

---

## 📋 Caso Práctico Resuelto: Cuenta con $1.000.000 CLP

Imaginemos un operador con una cuenta real de **$1.000.000 de pesos chilenos** (o su equivalente de ~$1.050 USD a un tipo de cambio de $950 CLP/USD).

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 180" width="100%" height="180" xmlns="http://www.w3.org/2000/svg" style="background:#F8FAFC; border:1.5px solid #CBD5E1; border-radius:8px; font-family:'Space Grotesk', monospace;">
  <rect x="0" y="0" width="720" height="28" fill="#0F172A"/>
  <text x="20" y="19" font-size="11" font-weight="700" fill="#FFFFFF" font-family="'Plus Jakarta Sans', sans-serif;">CASO PRÁCTICO RESUELTO EN USD/CLP (CUENTA: $1.000.000 CLP)</text>

  <text x="30" y="55" font-size="10" fill="#334155">1. Capital Total Cuenta: $ 1.000.000 CLP</text>
  <text x="30" y="78" font-size="10" font-weight="700" fill="#059669">2. Riesgo 1.0% Teórico: $ 10.000 CLP</text>
  <text x="30" y="101" font-size="10" fill="#334155">3. Entrada (934) - SL (930.50): 3.50 pesos</text>
  <text x="30" y="124" font-size="10" fill="#334155">4. Valor Punto (1 lote MT5): $ 100.000 CLP</text>

  <line x1="370" y1="40" x2="370" y2="165" stroke="#E2E8F0" stroke-width="1.5"/>

  <text x="390" y="55" font-size="10" fill="#334155">5. Lote Teórico: 10.000 / (3.50 x 100.000) = 0.028</text>
  <text x="390" y="78" font-size="10" font-weight="700" fill="#059669">6. Lote Redondeado ↓ (step 0.01): 0.02 lotes</text>
  <text x="390" y="101" font-size="10" fill="#334155">7. Pérdida Teórica Real en SL: $ 7.000 CLP (&lt; $10k ✓)</text>
  <text x="390" y="124" font-size="10" font-weight="700" fill="#0284C7">8. Margen Necesario (1:100): ~$18.680 CLP (¡Margen OK!)</text>

  <rect x="20" y="142" width="680" height="26" rx="4" fill="#ECFDF5" stroke="#A7F3D0" stroke-width="1"/>
  <text x="360" y="159" font-size="9" font-weight="700" fill="#065F46" text-anchor="middle" font-family="'Plus Jakarta Sans', sans-serif;">Al redondear hacia abajo (0.02 lotes), tu riesgo real ($7.000 CLP) queda estrictamente protegido bajo tu límite de $10.000 CLP.</text>
</svg>
</div>

---

## 🖥️ Cómo Introducir la Orden en MetaTrader 5

En MetaTrader 5, presiona la tecla **F9** o haz clic en **Nueva Orden**. Selecciona **Tipo: Orden Pendiente** para ingresar los parámetros de la ficha:

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 180" width="100%" height="180" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1.5px solid #CBD5E1; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <rect x="0" y="0" width="720" height="28" fill="#1E293B"/>
  <text x="20" y="19" font-size="11" font-weight="700" fill="#FFFFFF">VENTANA DE ORDEN EN METATRADER 5 (MOCKUP VISUAL)</text>

  <g transform="translate(30, 45)">
    <text x="0" y="15" font-size="10" font-weight="700" fill="#475569">Símbolo:</text>
    <rect x="70" y="0" width="180" height="24" rx="3" fill="#F8FAFC" stroke="#CBD5E1"/>
    <text x="80" y="16" font-size="10.5" font-weight="700" fill="#0F172A">USDCLP (Dólar vs Peso)</text>

    <text x="0" y="45" font-size="10" font-weight="700" fill="#475569">Tipo:</text>
    <rect x="70" y="30" width="180" height="24" rx="3" fill="#EFF6FF" stroke="#3B82F6"/>
    <text x="80" y="46" font-size="10.5" font-weight="700" fill="#1D4ED8">Orden Pendiente (Buy Stop)</text>

    <text x="0" y="75" font-size="10" font-weight="700" fill="#475569">Volumen:</text>
    <rect x="70" y="60" width="180" height="24" rx="3" fill="#F0FDF4" stroke="#10B981"/>
    <text x="80" y="76" font-size="11" font-weight="700" fill="#065F46">0.02 (Lote Calculado)</text>
  </g>

  <g transform="translate(360, 45)">
    <text x="0" y="15" font-size="10" font-weight="700" fill="#475569">Precio Entrada:</text>
    <rect x="110" y="0" width="180" height="24" rx="3" fill="#F8FAFC" stroke="#CBD5E1"/>
    <text x="120" y="16" font-size="11" font-weight="700" fill="#0F172A">934.00</text>

    <text x="0" y="45" font-size="10" font-weight="700" fill="#DC2626">Stop Loss:</text>
    <rect x="110" y="30" width="180" height="24" rx="3" fill="#FEF2F2" stroke="#EF4444"/>
    <text x="120" y="46" font-size="11" font-weight="700" fill="#DC2626">930.50 (Protección)</text>

    <text x="0" y="75" font-size="10" font-weight="700" fill="#059669">Take Profit 1:</text>
    <rect x="110" y="60" width="180" height="24" rx="3" fill="#ECFDF5" stroke="#10B981"/>
    <text x="120" y="76" font-size="11" font-weight="700" fill="#059669">938.00 (Ganancia 1R)</text>
  </g>

  <rect x="260" y="140" width="200" height="28" rx="4" fill="#059669"/>
  <text x="360" y="158" font-size="11" font-weight="700" fill="#FFFFFF" text-anchor="middle">COLOCAR ORDEN EN MT5</text>
</svg>
</div>

---

## 🛠️ Guía Rápida: Cómo Instalar los Indicadores en MT5

Para ver exactamente lo mismo que el sistema en tu gráfico de 1 Hora (H1):

1. **Canal Donchian (50 periodos)**: En MT5 ve al menú superior: *Insertar → Indicadores → Free Indicators / Ejemplos → Donchian Channel* (o *Price Channel*). Configura el **Período en 50 barras**.
2. **Promedios Móviles Exponenciales (EMA 20, 50, 100)**: Ve a *Insertar → Indicadores → Tendenciales → Moving Average*. Elige **Método: Exponential**, y agrega 3 medias: una de 20 (azul), una de 50 (naranja) y una de 100 (morada).
3. **Bandas de Bollinger (20, 2σ)**: Ve a *Insertar → Indicadores → Tendenciales → Bollinger Bands*. Configura **Período: 20**, **Desviaciones: 2.000**, aplicado al cierre.

---

# 🛑 SECCIÓN 8: Cuándo Sentarte en las Manos y Gestión de Pérdidas

---

En el trading cuantitativo profesional, **saber cuándo NO operar y cómo protegerse de rachas es más importante que buscar ganancias**:

---

### 1. Protocolo de Protección por Drawdown (Gestión de Racha Perdedora)
* **Techo de Riesgo Simultáneo**: Máximo **2.5% de riesgo total de la cuenta** en posiciones abiertas al mismo tiempo.
* **Límite Diario de Pérdida**: Si se acumulan **2 operaciones perdedoras en el día (-2.0%)**, el operador **cierra la plataforma y no opera más por el resto de la jornada**.
* **Límite Semanal**: Si se acumula un -4.0% en la semana, se suspende la operativa hasta el lunes siguiente.
* **Reducción por Racha**: Tras 3 operaciones perdedoras consecutivas, el riesgo se reduce automáticamente al **0.5% por operación** hasta encadenar 2 operaciones ganadoras.

---

### 2. Horario Exclusivo para el Dólar en Chile (USD/CLP)
* El dólar en Chile solo tiene liquidez institucional profunda durante la **rueda bancaria de Santiago: de 09:00 a 14:00 horas (hora de Chile)**. Esto deja exactamente **4 velas H1 operables al día** (cierres de 10:00, 11:00, 12:00 y 13:00 CLT).
* Al cierre de las 14:00 horas la liquidez desaparece y los spreads se abren. Se cancelan todas las órdenes pendientes.

---

### 3. Protocolo de Bloqueo por Noticias de Alto Impacto (Blackout)
Durante la publicación de noticias económicas mayores, los spreads se abren abruptamente y el precio puede saltar violentamente:

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 120" width="100%" height="120" xmlns="http://www.w3.org/2000/svg" style="background:#FFFFFF; border:1px solid #E2E8F0; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <line x1="40" y1="60" x2="680" y2="60" stroke="#CBD5E1" stroke-width="3"/>

  <!-- Zona 1: Normal -->
  <circle cx="100" cy="60" r="10" fill="#10B981"/>
  <text x="100" y="40" font-size="9.5" font-weight="700" fill="#065F46" text-anchor="middle">SESIÓN NORMAL</text>

  <!-- Zona 2: Bloqueo Pre -->
  <rect x="220" y="30" width="120" height="60" rx="4" fill="#FEF2F2" stroke="#EF4444" stroke-width="1.5"/>
  <text x="280" y="52" font-size="9" font-weight="700" fill="#991B1B" text-anchor="middle">15-30 MIN ANTES</text>
  <text x="280" y="68" font-size="8" fill="#B91C1C" text-anchor="middle">Cancelar órdenes</text>

  <!-- Evento Noticia -->
  <circle cx="400" cy="60" r="16" fill="#E84040"/>
  <text x="400" y="65" font-size="14" fill="#FFFFFF" text-anchor="middle">💥</text>
  <text x="400" y="22" font-size="9.5" font-weight="700" fill="#E84040" text-anchor="middle">NOTICIA MACRO TIER-1</text>

  <!-- Zona 3: Bloqueo Post -->
  <rect x="460" y="30" width="140" height="60" rx="4" fill="#FEF2F2" stroke="#EF4444" stroke-width="1.5"/>
  <text x="530" y="52" font-size="9" font-weight="700" fill="#991B1B" text-anchor="middle">30-60 MIN DESPUÉS</text>
  <text x="530" y="68" font-size="8" fill="#B91C1C" text-anchor="middle">Esperar vela cerrada</text>
</svg>
</div>

* **Eventos con Bloqueo Obligatorio**:
  1. **Tasas de Interés de la Reserva Federal (FOMC)**: Cancelar órdenes 30 minutos antes y no operar hasta 60 minutos después de la conferencia de prensa.
  2. **Datos de Empleo en EE.UU. (NFP) e Inflación (IPC)**: Bloqueo desde 15 minutos antes hasta 30 minutos después.
  3. **Reunión de Tasas del Banco Central de Chile (RPM) e Imacec**: Bloqueo total en USD/CLP (no operar la primera vela tras el anuncio).

---

# 📋 SECCIÓN 9: Los 5 Pasos Antes del Clic (Checklist del Trader)

---

Antes de presionar cualquier botón en MetaTrader 5, recorre esta lista mental paso a paso:

<div style="width: 100%; margin: 16px 0; display: flex; justify-content: center;">
<svg viewBox="0 0 720 220" width="100%" height="220" xmlns="http://www.w3.org/2000/svg" style="background:#F8FAFC; border:1.5px solid #50C0A8; border-radius:8px; font-family:'Plus Jakarta Sans', sans-serif;">
  <rect x="0" y="0" width="720" height="32" fill="#064E3B"/>
  <text x="20" y="21" font-size="11" font-weight="700" fill="#FFFFFF">CHECKLIST DIARIO PARA EL TRADER</text>

  <!-- Paso 1 -->
  <circle cx="35" cy="58" r="10" fill="#10B981"/>
  <text x="35" y="62" font-size="10" font-weight="700" fill="#FFFFFF" text-anchor="middle">1</text>
  <text x="55" y="62" font-size="10" font-weight="700" fill="#0F172A">¿El clima económico del día está confirmado por 2 días hábiles?</text>

  <!-- Paso 2 -->
  <circle cx="35" cy="92" r="10" fill="#10B981"/>
  <text x="35" y="96" font-size="10" font-weight="700" fill="#FFFFFF" text-anchor="middle">2</text>
  <text x="55" y="96" font-size="10" font-weight="700" fill="#0F172A">¿La ficha de operación del activo está en Luz Verde (Listo para operar)?</text>

  <!-- Paso 3 -->
  <circle cx="35" cy="126" r="10" fill="#10B981"/>
  <text x="35" y="130" font-size="10" font-weight="700" fill="#FFFFFF" text-anchor="middle">3</text>
  <text x="55" y="130" font-size="10" font-weight="700" fill="#0F172A">¿Filtro de Horario, Spread (&lt; 15% del SL) y Blackout de noticias aprobado?</text>

  <!-- Paso 4 -->
  <circle cx="35" cy="160" r="10" fill="#10B981"/>
  <text x="35" y="164" font-size="10" font-weight="700" fill="#FFFFFF" text-anchor="middle">4</text>
  <text x="55" y="164" font-size="10" font-weight="700" fill="#0F172A">¿Calculaste tu lote al 1% teórico redondeando hacia abajo y con margen seguro?</text>

  <!-- Paso 5 -->
  <circle cx="35" cy="194" r="10" fill="#10B981"/>
  <text x="35" y="198" font-size="10" font-weight="700" fill="#FFFFFF" text-anchor="middle">5</text>
  <text x="55" y="198" font-size="10" font-weight="700" fill="#0F172A">¿Ingresaste la orden pendiente con Stop Loss, Take Profit y vencimiento a 2h?</text>
</svg>
</div>

---

# 📚 SECCIÓN 10: Anexo Técnico, Glosario y Automatización

---

### 📖 Glosario de Términos en Fácil:
* **Vela Cerrada**: Una vela de 1 hora cuyo tiempo ha finalizado (al minuto :00). Es la única que tomamos como dato confiable.
* **Stop Loss (SL)**: Nivel de precio donde asumes una pérdida controlada y sales del mercado para proteger tu cuenta.
* **Take Profit (TP)**: Nivel de precio donde recoges tu ganancia planificada.
* **Ratio Riesgo/Beneficio (R:R)**: Relación entre lo que arriesgas y lo que aspiras a ganar. Nuestro sistema exige R:R ≥ 1.0 al primer objetivo.
* **Puntos Base (bps)**: 100 puntos base equivalen a 1.00%. Por ende, 10 bps es un movimiento de 0.10% en la tasa de interés del bono.
* **Curva Invertida (2s10s)**: El termómetro de la economía se da vuelta: prestarle dinero al gobierno a 2 años paga más interés que a 10 años porque los grandes inversionistas tienen miedo a una recesión inminente.
* **Bull Steepener**: Escenario donde las tasas de corto plazo caen con fuerza porque el banco central baja tasas con urgencia para reactivar la economía.
* **Spread**: La diferencia de precio entre comprar y vender que cobra el broker. Si supera el 15% de la distancia al SL, la operación se cancela.
* **TIPS (Bonos del Tesoro Indexados a Inflación)**: Bonos de EE.UU. que pagan una tasa de interés real, compitiendo directamente contra el Oro.

---

### Umbrales Numéricos Oficiales del Sistema de Análisis:

| Clima | Condiciones Cuantitativas de Activación |
|---|---|
| **R3 (Tormenta / Estanflación)** | Petróleo sube ≥ +3.5% en 5 días **Y** (Tasa del bono a 10 años sube ≥ +10 bps o Tasa TIPS sube ≥ +8 bps). |
| **R1 (Inflación)** | Expectativa de inflación a 10 años sube ≥ +10 bps en 5 días **Y** la curva 2s10s está comprimida (≤ 20 bps). |
| **R4 (Recesión / Vuelo a Calidad)** | Cobre cae ≤ -2.5% en 5 días **Y** [Curva de bonos 2s10s invertida (< 0.0%) **O** el bono a 2 años cae fuerte ≤ -15 bps mientras la curva se empina ≥ +10 bps]. |
| **R2 (Día Bueno / Expansión)** | Cobre sube ≥ +1.5% en 5 días **Y** Tasas del bono a 10 años estables (variación dentro de ± 6 bps). |
| **R0 (Calma / Rango)** | Todas las variables económicas dentro de rangos normales sin movimientos bruscos. |

> **Jerarquía de Precedencia:** En caso de activación simultánea de condiciones, la prioridad oficial es:  
> **R3 (Tormenta) > R1 (Inflación) > R4 (Recesión) > R2 (Expansión) > R0 (Calma)**.  
> Un **Shock Extremo (> 1.5x)** se define cuando una variable supera el 150% de su umbral (ej. Petróleo ≥ +5.25% en 5 días), activando el régimen de forma inmediata sin esperar la regla de 2 días.

---

### 🤖 Visión a Futuro: Escalabilidad y Automatización (MQL5)

Muchos operadores manejan agendas con reuniones laborales continuas y no pueden estar frente a la pantalla al minuto :00 exacto de cada hora. 

Debido a que todas las reglas de esta guía son **100% matemáticas, lógicas y deterministas** (sin ambigüedades subjetivas), están diseñadas para ser trasladadas en el futuro a un **Asesor Experto (Expert Advisor en MQL5)**. 

La arquitectura lógica del robot contempla 4 módulos sencillos:
1. **Módulo de Ingesta:** Lectura del archivo de sesgo diario para conocer el clima oficial confirmado.
2. **Módulo de Gatillo (`OnBar`):** Detección de patrones únicamente en el tick 0 de apertura de una nueva vela H1.
3. **Módulo de Dimensionamiento:** Cálculo automático de lotaje al 1.0% contra `AccountBalance()` y `SymbolInfoDouble(SYMBOL_TRADE_TICK_VALUE)`, redondeando al `VolumeStep`.
4. **Módulo de Ejecución:** Envío de órdenes pendientes (`BUY_STOP` / `BUY_LIMIT`) con vencimiento automático a 2 barras y gestión de Break-Even.

---

## 🎓 Conclusión: La Disciplina es tu Mayor Protección

El trading no consiste en adivinar el futuro ni en apostar por impulsos emocionales. Consiste en seguir un método riguroso: entender el clima del mundo, esperar pacientemente a que aparezca una ficha en luz verde sobre una vela cerrada y respetar siempre tu gestión de riesgo.

*¡Buena disciplina, cero operaciones por ansiedad y estricto respeto a tu capital, estimado trader!*
