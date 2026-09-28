# Guía Táctica USD/CLP: Cobre, Fed y Tasas
<!-- ambito: ambos -->
**Grupo Inteligencia SpA · Área de Post Venta y Análisis de Mercado**  
*Documento de Formación Cuantitativa y Gestión de Riesgo para Operadores e Inversionistas Chilenos*  
*Edición Oficial · 10 de Septiembre de 2026 · Distribución 100% Abierta (Anti-Blur)*

---

## 1. Anatomía y Formación de Precios del Dólar en Chile
### Cómo se fija realmente el tipo de cambio y quiénes mueven el mercado interbancario

El tipo de cambio **USD/CLP** no es un número abstracto fijado por decreto: es el resultado del balance instantáneo entre la oferta y la demanda de divisas en el **mercado interbancario de Santiago (SIF/DATATEC)**, operando formalmente entre las **09:00 y las 13:30 CLT**, en constante arbitraje con las pantallas del mercado spot global (*over-the-counter*). 

Comprender la anatomía del mercado local es la primera línea de defensa para no ser víctima de la volatilidad ni de los diferenciales de precios injustificados (*spreads*).

<!-- TOKEN_DIAGRAMA_FLUJO_MERCADO -->

### 1. El Hecho Técnico: Las Manos Fuertes del Mercado Local
Tres grandes jugadores institucionales definen la liquidez en Chile:
1. **La Gran Minería (Oferentes de USD)**: Empresas mineras (Codelco y privadas) liquidan dólares en el mercado local para pagar sueldos, impuestos y proveedores en pesos chilenos. El cobre es una fuente estructural de divisas para Chile.
2. **Las AFPs y Fondos de Inversión (Demandantes Estructurales)**: Administran el ahorro previsional y rebalancean permanentemente carteras externas, demandando u ofreciendo cientos de millones de dólares según límites regulatorios.
3. **El Sector No Residente (Off-shore & Derivados)**: Bancos y hedge funds globales que operan principalmente vía contratos **Forwards**, especulando o cubriendo exposición en mercados emergentes. La posición forward vigente es de **{{FORWARD}}M USD**.

### 2. Implicancia Económica: De la Pantalla a la Economía Real
Cuando el dólar sube en Santiago, el impacto no se queda en las pantallas financieras. Chile importa una parte relevante de sus combustibles, trigo, tecnología y vehículos. Una depreciación persistente del peso puede encarecer bienes importados y presionar la inflación, aunque el traslado depende del producto, los contratos y la política de precios vigente.

> [!IMPORTANT]
> **Gestión de Riesgo y Regla del 1%: Evita la Trampa de la Apertura (09:00 - 09:15 CLT)**  
> En los primeros 15 minutos de la sesión local, los bancos están cuadrando saldos nocturnos y la horquilla de compra-venta (*spread*) suele duplicarse o triplicarse (pasando de 0.30 CLP a más de 1.50 CLP por dólar). **Prohibido abrir órdenes a mercado antes de las 09:15 CLT**. Espera a que la liquidez interbancaria se estabilice para no regalar margen al broker.

---

## 2. El Termómetro Rojo: Correlación USD/CLP vs. Cobre (`COPPER`)
### La relación inversa más poderosa del mercado cambiario latinoamericano

Chile es uno de los principales productores de cobre del mundo. Esa exposición convierte al mineral rojo en un **driver estructural del peso chileno**. La relación entre cobre y USD/CLP suele ser inversa, pero no es constante: también intervienen el dólar global, las tasas, los flujos financieros y el riesgo internacional. En esta guía, el valor operativo se expresa con el símbolo `COPPER` de MT5 en USD/t.

<!-- TOKEN_DIAGRAMA_BALANCIN_COBRE -->

### 1. El Hecho Técnico: La Mecánica del Balancín Macro
La regla cuantitativa es implacable:
* **Cobre al Alza (Superávit de Divisas)**: Si el cobre sube (cotizando actualmente a **${{COPPER}} USD/t** en `COPPER`), mejora la señal de ingresos externos y el peso puede recibir apoyo, provocando una caída en la cotización del **USD/CLP**.
* **Cobre a la Baja (Estrés Cambiario)**: Una caída en el precio del cobre reduce el flujo proyectado de ingresos fiscales y divisas comerciales. El dólar se vuelve un bien escaso en Santiago y su precio se dispara frente al peso.

### 2. Implicancia para el USD/CLP: Por Qué Mirar a China al Despertar
China es un consumidor central de cobre. Cualquier dato publicado en Pekín durante la madrugada chilena, como el PMI manufacturero, estímulos inmobiliarios o tasas del Banco Popular de China (PBoC), puede mover las expectativas sobre demanda y afectar al USD/CLP. Esa señal no anticipa con certeza la apertura: debe confirmarse con el dólar global y la liquidez local.

> [!WARNING]
> **Qué NO Hacer: No Operes la Correlación a Ciegas**  
> Una trampa común para novatos es vender dólares simplemente porque el cobre subió unos centavos en el día. Si al mismo tiempo el dólar global (DXY) se está apreciando con fuerza o la Reserva Federal emite un mensaje agresivo (*Hawkish*), la correlación con el cobre puede desacoplarse temporalmente. Revisa siempre el contexto macroeconómico integral antes de gatillar una operación.

---

## 3. La Gravedad de las Tasas: Banco Central vs. Reserva Federal
### El diferencial de política monetaria y la mecánica del Carry Trade

El tipo de cambio no solo responde al comercio exterior de mercancías: responde con extrema ferocidad a los **flujos de capital financiero**. Los grandes fondos internacionales mueven billones de dólares buscando el mayor rendimiento ajustado por riesgo entre los bancos centrales. El factor determinante en esta ecuación es el **Spread de Tasas** entre la Tasa de Política Monetaria del Banco Central de Chile (TPM) y la tasa de fondos federales de la Reserva Federal de EE.UU. (Fed Funds).

<!-- TOKEN_MATRIZ_CUADRANTES_MACRO -->

### 1. El Hecho Técnico: El Diferencial Actual y el Carry Trade
Actualmente, el escenario de política monetaria comparada se configura así:
* **Tasa TPM BCCh**: **{{TPM}}%** (en proceso de normalización monetaria).
* **Tasa Fed Funds EE.UU.**: **{{FED}}%** (Rendimiento del Bono del Tesoro a 10 años: **{{TREASURY10}}%**).
* **Diferencial Nominal**: lectura vigente del diferencial entre Chile y Estados Unidos.

Cuando el Banco Central de Chile recorta su tasa de interés con mayor agresividad que la Reserva Federal, el diferencial a favor del peso se achica. Los inversionistas institucionales desarman sus posiciones de *Carry Trade* (venden pesos y compran dólares para refugiarse en letras del Tesoro norteamericano con riesgo crediticio cero), generando una fuerte presión alcista en el USD/CLP.

### 2. Transmisión a la Economía Real: Créditos Hipotecarios y Dólar
Cuando el Banco Central de Chile baja las tasas, su objetivo es reactivar el crédito local, abaratar el costo de los préstamos hipotecarios y comerciales para las familias. Sin embargo, la contracara automática de esa medida suele ser un dólar más caro en el corto plazo. El equilibrio del banco central es una cuerda floja permanente entre la inflación importada y la reactivación interna.

> [!CRITICAL]
> **Qué NO Hacer: Protocolo de Blackout en Días de Decisión de Tasas**  
> Prohibido operar en el mercado spot dentro de los **15 minutos previos y 30 minutos posteriores** a la publicación de un comunicado de TPM del BCCh o del FOMC de la Fed. La falta de liquidez en el libro de órdenes genera *slippage* (deslizamiento de precios) severo que puede ejecutar tu orden a decenas de pesos de distancia de tu nivel previsto.

---

## 4. Análisis Técnico Cuantitativo en Gráfico H1 (TradingView · Feed Grupo Inteligencia)
### Decodificación de niveles institucionales, medias móviles y rangos de volatilidad

Este panel traduce una lectura H1 del USD/CLP a cuatro señales fáciles de seguir: las velas muestran quién dominó cada hora, la EMA 50 sigue el pulso reciente, la EMA 200 marca la estructura amplia y el RSI alerta cuando el movimiento se estira. Los niveles e indicadores se visualizan a través del motor TradingView alimentado directamente por el feed de datos institucional de Grupo Inteligencia. No es una señal automática: es un mapa para decidir dónde esperar confirmación.

<!-- TOKEN_GRAFICO_TRADINGVIEW_H1 -->

### 1. El Hecho Técnico: Arquitectura de Niveles y Medias Clave
Analizando la estructura técnica vigente en el gráfico TradingView con feed de Grupo Inteligencia:
* **Precio Spot Actual**: **${{USDCLP_SPOT}} CLP** (por encima de las medias estructurales).
* **Media Móvil Exponencial Rápida (EMA 50 H1)**: **${{EMA50}} CLP** (Primer soporte dinámico clave).
* **Media Móvil Exponencial Lenta (EMA 200 H1)**: **${{EMA200}} CLP** (Frontera estructural alcista/bajista institucional).
* **Canal Donchian 50 Periodos**: Techo en **${{DONCHIAN_HIGH}} CLP** y Piso en **${{DONCHIAN_LOW}} CLP**.
* **Volatilidad ATR(14) en H1**: **${{ATR_H1}} CLP** por vela horaria.

La configuración técnica muestra al precio testeando la resistencia superior del canal Donchian. Mientras el precio se mantenga por sobre la **EMA 50 ({{EMA50}})**, la estructura favorece la continuación de compras en retrocesos controlados (*pullbacks*). Un quiebre confirmado con vela horaria cerrada bajo **{{EMA200}} (EMA 200)** invalidaría el sesgo comprador de corto plazo.

### 2. Aplicación para una Empresa Expuesta al Dólar
Para una empresa importadora que debe liquidar facturas a fin de mes, un gráfico H1 con tendencia definida sobre la EMA 200 indica que esperar "a que baje de 900" sin cobertura es una apuesta de alto riesgo. Monitorear los soportes técnicos permite calendarizar las compras de divisas en zonas de descuento dinámico en lugar de pagar el precio máximo por pánico.

> [!CAUTION]
> **Qué NO Hacer: No Compres en la Punta de la Vela (RSI en Sobrecompra)**  
> Con el indicador de fuerza relativa en H1 marcando **RSI(14) = {{RSI_H1}}**, el activo se encuentra en zona de sobrecompra extrema. Comprar en el techo del canal persiguiendo el precio es el error más recurrente del operador novato. La disciplina cuantitativa exige esperar pacientemente el retroceso hacia la zona de soporte dinámico ({{EMA50}} CLP y el precio de confirmación del terminal).

---

## 5. La Matemática del Blindaje: Volatility Targeting y la Regla del 1%
### Cómo dimensionar tu posición para que ninguna mala racha destruya tu patrimonio

El 90% de las personas que pierden dinero en los mercados financieros no fallan por su análisis técnico ni por culpa de las noticias: **fracasan por sobreapalancamiento y falta de gestión matemática del riesgo**. El profesional no se enfoca en "cuánto va a ganar", sino en calcular exactamente cuánto dinero está dispuesto a arriesgar antes de apretar un solo botón.

<!-- TOKEN_DIAGRAMA_LOTAJES -->

### 1. El Hecho Técnico: La Fórmula Oficial de Asignación por Volatilidad
En Grupo Inteligencia aplicamos de forma estricta la **Regla del 1%**: bajo ninguna circunstancia se permite arriesgar más del 1% del capital líquido total en una sola operación. El tamaño de la posición (*lotaje*) no se adivina: se deriva matemáticamente mediante la siguiente ecuación:

<div class="formula" aria-label="Fórmula de lotaje por riesgo">
  <span>Lotes a operar =</span>
  <span class="formula-fraccion">
    <span class="numerador">Capital líquido (USD) × 0,01</span>
    <span class="denominador">Distancia al Stop Loss (CLP) × multiplicador de contrato</span>
  </span>
</div>

Para un contrato estándar de USD/CLP (donde 1 lote equivale a $100.000 USD y cada peso chileno de variación equivale a aproximadamente $100 USD en la cuenta): si tu Stop Loss técnico está ubicado a **$10 CLP** de distancia de tu punto de entrada:

| Capital de Cuenta | Riesgo Máximo 1% | Distancia SL Técnica | Lotaje Exacto Autorizado |
|---|:---:|:---:|:---:|
| **$1.000 USD** | **$10 USD** | 10.0 CLP | **0.01 Lotes (Micro Lote)** |
| **$5.000 USD** | **$50 USD** | 10.0 CLP | **0.05 Lotes** |
| **$10.000 USD** | **$100 USD** | 10.0 CLP | **0.10 Lotes (Mini Lote)** |

### 2. Gestión de Riesgo: Sobrevivir a 20 Operaciones Adversas Seguidas
Si arriesgas el 1% por operación, tendrías que cometer 20 errores consecutivos para que tu cuenta sufra un drawdown del 18.2%. Si en cambio operas con lotajes arbitrarios ("0.50 lotes en una cuenta de $1.000"), bastará un movimiento inesperado de $20 pesos en el dólar para perder el 100% de tus ahorros en un solo día. La matemática del riesgo es la armadura del operador inteligente.

> [!CRITICAL]
> **Qué NO Hacer: Prohibido Entrar al Mercado sin Stop Loss Precargado**  
> Jamás envíes una orden al mercado diciendo "cerraré manualmente si se va en contra". En momentos de alta volatilidad, la mente humana sufre congelamiento por aversión a la pérdida. El Stop Loss debe estar programado en el servidor del broker en el milisegundo exacto de la ejecución.

---

## 6. Protocolo de Entrada: El Checklist Operativo de 5 Pasos
### El sistema de validación previa para eliminar la improvisación y la duda

Un cirujano o un piloto de aviación jamás despegan confiando únicamente en su intuición: siguen rigurosamente un protocolo de verificación de seguridad. En los mercados financieros ocurre exactamente lo mismo. Ninguna operación de compra o venta en USD/CLP debe ejecutarse sin que el operador haya verificado y aprobado los **5 pasos del Checklist Operativo de Grupo Inteligencia**.

<!-- TOKEN_DIAGRAMA_CHECKLIST_HUD -->

### 1. El Hecho Técnico: Los 5 Filtros del Sistema
Cada orden ejecutada debe cumplir con la alineación simultánea de los siguientes parámetros:
1. **Filtro Macro Cobre**: Comprobar la dirección de `COPPER` y el contexto de demanda global. Si el cobre pierde fuerza, el sesgo puede favorecer compras de USD/CLP; si gana fuerza, puede favorecer ventas de USD/CLP.
2. **Filtro de Calendario Económico**: Confirmar que no existan datos de alto impacto programados para las próximas 2 horas (IPoM, IPC de EE.UU. o Chile, comparecencia de Powell o Rosanna Costa).
3. **Filtro de Tendencia H1**: El precio debe encontrarse en una zona de confluencia con las medias institucionales (EMA 50 / EMA 200). Prohibido operar en contra de la tendencia estructural horaria.
4. **Cálculo Matemático de Lotaje**: Determinar el volumen exacto de la orden aplicando la fórmula de la Regla del 1% según el capital de la cuenta.
5. **Configuración de la Orden (Riesgo/Beneficio >= 1:2)**: El objetivo de ganancia (*Take Profit*) debe ser al menos el doble de la distancia del *Stop Loss*.

### 2. Aplicación Operativa: Reducir el Estrés y las Horas Frente a la Pantalla
El checklist transforma el trading de una actividad angustiante a un proceso metódico y predecible. Si en una mañana los 5 pasos no se cumplen al 100%, el operador no ejecuta ninguna orden y preserva su capital intacto. En el mercado, **la inacción disciplinada también es una posición ganadora**.

> [!IMPORTANT]
> **Qué NO Hacer: Nunca Muevas el Stop Loss para "Darle Aire" a la Posición**  
> Si el precio se acerca a tu nivel de invalidación, asume la pérdida planificada del 1%. Mover el Stop Loss más lejos es violar el contrato que hiciste contigo mismo y transformar una pequeña pérdida controlada en un golpe devastador para tu patrimonio.

---

## 7. El Horario de Oro: Cronograma de Liquidez y Sesiones
### Cuándo operar para tener los mejores spreads y cuándo apagar la pantalla

El mercado del dólar en Chile no tiene la misma profundidad a lo largo del día. Existen ventanas horarias donde la liquidez es abundante y los costos de transacción son mínimos, y existen "zonas muertas" donde operar es equivalente a caminar en un campo minado de horquillas abiertas y deslizamientos de precios.

<!-- TOKEN_TIMELINE_SESIONES -->

### 1. El Hecho Técnico: El Cruce de Sesiones y la Liquidez
El mapa operativo diario para el USD/CLP se divide en cuatro fases críticas:
* **09:00 - 09:15 CLT (Fase de Asentamiento)**: Apertura del mercado interbancario de Santiago. Alta volatilidad inicial, spreads amplios mientras se cruzan las órdenes acumuladas de la noche. **Observación pasiva**.
* **09:15 - 12:30 CLT (La Ventana de Oro)**: Máxima confluencia de volumen. El mercado de Santiago opera en paralelo con la apertura de Wall Street (09:30 CLT) y los cierres de posición de metales en Londres. Spreads más ajustados del día. **Ventana recomendada para ejecutar operaciones**.
* **12:30 - 13:30 CLT (Cierre Interbancario Local)**: Los bancos locales cuadran sus libros y cierran operaciones por sistema. El volumen cae de forma abrupta.
* **13:30 CLT en adelante (Mercado Spot Off-shore)**: La plaza chilena cierra. Solo quedan cotizando plataformas internacionales con baja profundidad. Los spreads se multiplican y el riesgo de gaps es extremo.

### 2. Aplicación Operativa: Cómo Afecta a Quienes Trabajan
Muchos inversionistas cometen el error de intentar operar en sus tiempos libres por la tarde (16:00 o 18:00 hrs) cuando ya salieron de sus oficinas. Operar USD/CLP a esa hora es sumamente ineficiente debido a los costos de spread. Es preferible dedicar 30 minutos disciplinados entre las 09:30 y las 10:30 de la mañana, dejar las órdenes condicionadas con su Stop Loss y Take Profit automáticos, y continuar con la jornada laboral habitual.

> [!WARNING]
> **Qué NO Hacer: No Dejes Posiciones Abiertas el Fin de Semana (Riesgo de Gap)**  
> Salvo que tu estrategia sea de posición macro de largo plazo con un apalancamiento mínimo (< 1:2), evita mantener operaciones intradiarias abiertas el viernes por la tarde. Cualquier evento geopolítico o anuncio económico durante el fin de semana puede hacer que el mercado abra el lunes con un salto de 15 pesos por sobre tu Stop Loss.

---

## 8. La Psicología del Capital: Drawdown, Sesgos y Registro Estadístico
### La matemática de la recuperación y la disciplina del cuaderno de bitácora

En el ámbito del análisis técnico cuantitativo, la mente del operador es con frecuencia su mayor adversario. El ser humano está biológicamente programado para huir del dolor y buscar la recompensa inmediata, patrones que en los mercados financieros conducen directamente a la quiebra del operador no preparado.

<!-- TOKEN_GRAFICO_DRAWDOWN -->

### 1. El Hecho Técnico: La Asimetría Matemática del Drawdown
La recuperación de capital no es lineal. Debido a la naturaleza multiplicativa de los rendimientos, el porcentaje de ganancia requerido para volver al punto de equilibrio (*break-even*) crece exponencialmente a medida que aumenta la pérdida acumulada:

| Pérdida de Capital (Drawdown) | Ganancia Requerida para Recuperarse | Viabilidad Psicológica y Técnica |
|:---:|:---:|---|
| **-5%** | **+5.3%** | Rutinaria con disciplina de riesgo estándar |
| **-10%** | **+11.1%** | Perfectamente alcanzable en semanas |
| **-20%** | **+25.0%** | Requiere paciencia y reajuste operativo |
| **-50%** | **+100.0%** | Casi imposible: induce a la desesperación y quiebra |

Esta tabla demuestra por qué limitar cada pérdida individual al 1% es la única forma de garantizar la longevidad matemática en el mercado. Un operador con una racha negativa de 5 operaciones pierde solo un 4.9% de su cuenta, lo cual se recupera rápidamente sin alterar su plan de trading.

### 2. Disciplina del Operador: Aversión a la Pérdida y Sesgo de Revancha
Cuando un operador no preparado sufre una pérdida, suele experimentar *Revenge Trading* (operar por revancha): abre de inmediato una posición con el doble de lotaje para "recuperar lo que el mercado le quitó". Este comportamiento es puramente emocional y representa la causa número uno de liquidación de cuentas personales.

> [!TIP]
> **El Secreto Profesional: La Bitácora de Operaciones (Trading Journal)**  
> Todo inversionista serio debe llevar un registro estricto de cada operación: 1) Fecha y hora, 2) Razón técnica de entrada (según el checklist), 3) Lotaje y riesgo en USD, 4) Resultado final y 5) Estado emocional. Lo que no se mide, no se puede mejorar.

---

## 9. De la Teoría a la Práctica: El Próximo Paso en la Mesa Técnica
### Lleva este conocimiento a la práctica en vivo con el equipo de analistas de Grupo Inteligencia

Has completado las 8 lecciones cuantitativas fundamentales para comprender y operar el tipo de cambio USD/CLP de forma profesional, responsable y matemáticamente blindada. Has aprendido a leer el mercado interbancario, correlacionar el cobre, monitorear el diferencial de tasas, decodificar un gráfico H1 de MetaTrader 5 y calcular tu lotaje seguro al 1% de riesgo.

Sin embargo, **la teoría sin ejecución guiada suele diluirse ante la velocidad del mercado real**. Por esta razón, el Área de Research y Estrategia de Grupo Inteligencia pone a tu disposición un espacio técnico semanal:

<!-- TOKEN_TICKET_MESA_TECNICA -->

### Tu Invitación a la Clínica Táctica USD/CLP en Vivo
Cada **Martes a las 19:30 hrs (Horario de Santiago de Chile)**, nuestro equipo de analistas cuantitativos abre la sala privada de análisis técnico para clientes y prospectos calificados. En esta sesión de 40 minutos rigurosos:
1. **Análisis del Terminal MT5 en Pantalla Real**: Revisamos los 60 periodos H1, los niveles de soporte dinámico, el spread interbancario y el posicionamiento forward vigente.
2. **Aplicación Práctica de la Plantilla de Lotaje**: Te entregamos y configuramos en vivo la herramienta de cálculo automatizado de riesgo para que jamás cometas un error de sobreapalancamiento.
3. **Preguntas y Respuestas Directas con Analistas**: Resuelve dudas concretas sobre tus posiciones, coberturas cambiarias de empresas o estrategias de inversión personal.

### Cómo Coordinar tu Acceso con tu Asesor Asignado
Para recibir el enlace de acceso directo a la sesión de este martes y obtener tu copia de la **Plantilla Automatizada de Volatility Targeting en Excel/Google Sheets**, comunícate directamente con tu asesor institucional asignado o responde al mensaje de confirmación que recibiste al solicitar esta guía.

### Aviso Legal y Regulatorio Canónico (Disclaimer Obligatorio)
> [!CRITICAL]
> **GRUPO INTELIGENCIA SpA · ADVERTENCIA DE RIESGO INSTITUCIONAL Y COMPLIANCE**  
> El presente documento constituye material estrictamente educativo, pedagógico y de divulgación de análisis técnico intermercado. **Grupo Inteligencia SpA no realiza recomendaciones individuales de compra o venta de instrumentos financieros, no presta servicios de asesoría financiera personalizada ni administra fondos de terceros ni cuentas de inversión**.  
>  
> Las menciones a cotizaciones pasadas, niveles de soporte/resistencia y ejemplos matemáticos tienen fines exclusivamente ilustrativos y no garantizan rendimientos futuros. Operar con derivados financieros, divisas (Forex) y contratos por diferencia (CFDs) conlleva un **alto nivel de riesgo de pérdida de capital** debido al efecto del apalancamiento, no siendo un producto adecuado para todos los perfiles de inversionista. Asegúrese de comprender cabalmente los riesgos y opere siempre bajo un protocolo estricto de preservación de capital.  
> *Grupo Inteligencia SpA · Santiago de Chile · Todos los derechos reservados.*
