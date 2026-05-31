# Activos y drivers

El sistema cubre 20 activos organizados en tres categorías. Esta referencia explica qué mueve a cada uno, cuándo opera y cómo se analiza.

---

## Forex y Commodities

### USD/CLP — Dólar / Peso Chileno
**Ticker MT5**: `USDCLP` | **Horario**: 09:00-16:00 CLT

El par más relevante para los clientes chilenos. Mide cuántos pesos vale un dólar.

**Qué lo mueve**:
- **Cobre**: Chile es el mayor productor mundial. Cuando el cobre sube, el peso chileno se fortalece (USD/CLP baja). Cuando el cobre cae, el peso se debilita (USD/CLP sube).
- **Dollar Index (DXY)**: fortaleza global del dólar. Si el dólar sube en todo el mundo, USD/CLP sube también.
- **Tasas BCCh vs Fed**: diferencial de tasas entre el Banco Central de Chile y la Reserva Federal. Si la Fed sube tasas más que el BCCh, el capital fluye hacia EE.UU. y el peso se debilita.
- **Flujos de capital**: exportaciones/importaciones, inversión extranjera directa, venta de cobre en mercado internacional.

**Temporalidades usadas**: 4H — swing, 1H — intradía, 15M — scalper

**Indicador destacado**: ATR — mide la volatilidad diaria en puntos, útil para dimensionar el SL.

---

### XAU/USD — Oro
**Ticker MT5**: `XAUUSD` | **Horario**: 24h (sesión principal: NY 10:30-17:00 CLT)

Activo refugio por excelencia. Sube en contextos de incertidumbre y baja cuando el dólar y las tasas reales suben.

**Qué lo mueve**:
- **Dollar Index (DXY)**: relación inversa. Dólar fuerte → oro baja. Dólar débil → oro sube.
- **Tasas reales**: tasa del Treasury a 10 años menos inflación esperada. Tasas reales altas compiten con el oro (que no paga intereses).
- **Decisiones de la Fed**: expectativas de recorte de tasas impulsan el oro; expectativas de alza lo presionan.
- **Coberturas de bancos centrales**: compras masivas de reservas en oro por parte de bancos centrales emergentes (China, India, Russia) sostienen el precio a largo plazo.
- **Geopolítica**: conflictos, elecciones, tensiones globales elevan la demanda de refugio.

**Temporalidades usadas**: 4H — swing, 1H — intradía, 15M — scalper

---

### WTI — Petróleo West Texas Intermediate
**Ticker MT5**: `WTI.spot` | **Horario**: 24h (sesión principal: NY) — todas las referencias horarias en hora Chile (CLT/CLST)

Referencia mundial del precio del petróleo crudo ligero de EE.UU.

**Qué lo mueve**:
- **Inventarios EIA**: la Energy Information Administration publica datos de inventarios cada miércoles — consultar calendario oficial en hora Chile (CLT/CLST) — fuente: calendario económico oficial de Investing.com. Inventarios que suben más de lo esperado presionan el precio a la baja; inventarios que bajan lo impulsan.
- **Decisiones OPEP+**: recortes de producción suben el precio; aumentos de cuota lo presionan.
- **Demanda China**: China es el mayor importador de petróleo. PMI manufacturero chino débil → menor demanda → precio cae.
- **Geopolítica**: tensiones en Medio Oriente o sanciones a productores afectan la oferta y elevan el precio.

**Temporalidades usadas**: 4H — swing, 1H — intradía

---

## Índices

### US100 — Nasdaq 100
**Ticker MT5**: `US100.spot` | **Horario**: 10:30-17:00 CLT (sesión regular NYSE/NASDAQ)

Índice de las 100 mayores empresas no financieras del NASDAQ. Dominado por tecnología.

**Qué lo mueve**:
- **Tasas Fed**: índice muy sensible a tasas. Tasas altas descuentan más los flujos futuros de las empresas de crecimiento → caída del índice. Tasas bajas o recortes → rally.
- **Earnings tecnológicos**: resultados de #AAPL, #MSFT, #NVDA, #AMZN mueven el índice entero.
- **Rendimientos del Treasury a 10 años**: tasa libre de riesgo. Cuando sube, los inversores migran de acciones tech a bonos.
- **Sentimiento AI/chips**: narrativa de inteligencia artificial impacta directamente a los semiconductores (#NVDA) y al índice.

**Componentes clave**: #AAPL · #MSFT · #NVDA · #AMZN

**Temporalidades usadas**: 4H — swing, 1H — intradía

---

### US500 — S&P 500
**Ticker MT5**: `US500.spot` | **Horario**: 10:30-17:00 CLT

Índice amplio de las 500 mayores empresas de EE.UU. Referencia global del mercado de renta variable.

**Qué lo mueve**:
- **Tasas Fed**: como US100, pero con menor sensibilidad por incluir sectores defensivos (utilities, consumo básico).
- **Earnings agregados**: los resultados trimestrales del conjunto de las 500 empresas.
- **Datos macro EE.UU.**: IPC, PCE, NFP, PMI afectan las expectativas de tasas y el índice.
- **Rendimientos Treasury**: mismo mecanismo que US100.

**Componentes clave**: #AAPL · #MSFT · #NVDA · #JPM · #BAC

**Temporalidades usadas**: 4H — swing, 1H — intradía

---

### US30 — Dow Jones Industrial Average
**Ticker MT5**: `US30.spot` | **Horario**: 10:30-17:00 CLT

Índice de las 30 mayores empresas industriales y bancarias de EE.UU. Más defensivo que US100.

**Qué lo mueve**:
- **Datos macro EE.UU.**: PMI manufactura, pedidos de bienes duraderos, gasto en infraestructura.
- **Earnings industriales y bancarios**: resultados de #BA, #CAT, #GS, #JPM.
- **Tasas Fed**: impacto en márgenes bancarios (curva de rendimientos).
- **Ciclo económico**: más correlacionado con la economía real que US100.

**Componentes clave**: #BA · #CAT · #GS · #JPM

**Temporalidades usadas**: 4H — swing, 1H — intradía

---

## Acciones individuales (12)

### Sector Tecnológico (índice relacionado: US100)

| Ticker | Empresa | Qué mueve su precio |
|--------|---------|---------------------|
| `#AAPL` | Apple Inc. | Ventas iPhone, servicios (App Store, iCloud), demanda China, earnings trimestrales |
| `#MSFT` | Microsoft Corp. | Azure/cloud, IA (Copilot), licencias enterprise, earnings |
| `#NVDA` | NVIDIA Corp. | Demanda chips de IA, data centers, regulación de exportación a China, earnings |
| `#AMZN` | Amazon.com | AWS/cloud, retail, márgenes operativos, earnings |

**Driver de sector**: tasas Fed, ciclo de innovación AI/chips, regulación tech, rendimientos Treasury.

---

### Sector Bancario (índice relacionado: US30)

| Ticker | Empresa | Qué mueve su precio |
|--------|---------|---------------------|
| `#JPM` | JPMorgan Chase | Margen de interés, banca de inversión, provisiones de crédito, earnings |
| `#BAC` | Bank of America | Margen de interés, crédito al consumo, exposición a tasas, earnings |
| `#GS` | Goldman Sachs | Trading revenue, banca de inversión, actividad M&A, earnings |
| `#MS` | Morgan Stanley | Wealth management, trading, mercados de capital, earnings |

**Driver de sector**: tasas Fed (curva de rendimientos), margen de interés neto, regulación financiera, trading revenue.

---

### Sector Industrial (índice relacionado: US30)

| Ticker | Empresa | Qué mueve su precio |
|--------|---------|---------------------|
| `#BA` | Boeing Co. | Pedidos de aviones, producción 737/787, defensa, earnings |
| `#CAT` | Caterpillar Inc. | Demanda en construcción y minería, demanda China, earnings |
| `#GE` | GE Aerospace | Motores de aviación, servicios aeroespaciales, demanda de aerolíneas, earnings |
| `#DE` | Deere & Co. | Demanda agrícola, precios de commodities agrícolas, maquinaria, earnings |

**Driver de sector**: PMI manufactura, gasto en infraestructura, demanda global, comercio internacional.

---

## Activos complementarios (referencia, no análisis directo)

| Activo | Ticker MT5 | Relevancia |
|--------|-----------|------------|
| Cobre | `COPPER` | Driver principal del USD/CLP. Chile es el mayor productor mundial. |
| Dollar Index | `USDIDX` | Fortaleza global del dólar. Afecta a todos los activos. |
| DAX 40 | `GER40.spot` | Referencia para sentimiento europeo (opcional). |

---

## Datos macro que más impactan

| Dato | Frecuencia | Activos afectados | Por qué importa |
|------|-----------|------------------|-----------------|
| **NFP** (Non-Farm Payrolls) | 1er viernes del mes | USD/CLP, Oro, US100 | Dato de empleo más importante de EE.UU. → expectativas Fed |
| **IPC EE.UU.** | Mensual | Oro, USD/CLP, US100 | Inflación alta → Fed mantiene tasas altas → presiona oro y tech |
| **PCE** | Mensual | Oro, US100 | Inflación favorita de la Fed para tomar decisiones |
| **Tasas Fed** | 8 veces/año | Todos | Decisión más impactante del año |
| **PMI manufacturero** | Mensual | WTI, US30, #CAT | Salud de la economía real → demanda de petróleo e industriales |
| **Inventarios EIA** | Semanal (miércoles) | WTI | Oferta/demanda real de petróleo en EE.UU. |
| **Jobless Claims** | Semanal (jueves) | USD/CLP, US100 | Salud del mercado laboral → expectativas Fed |
| **Tasas BCCh** | Periódico | USD/CLP | Diferencial de tasas Chile-EE.UU. |
