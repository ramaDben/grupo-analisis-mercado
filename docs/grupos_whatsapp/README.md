# Estructura Modular de Canales y Grupos de Alertas (WhatsApp)

**Grupo de Análisis de Mercado — Grupo Inteligencia SpA**  
*Documento y kit de despliegue para la modularización de canales de mensajería y alertas.*

---

## 📌 1. Visión General de la Modularización

Para optimizar la experiencia de los clientes e inversionistas, evitar la sobrecarga de notificaciones y entregar contenido hiper-focalizado según los intereses de cada perfil, la difusión de alertas y análisis de mercado se estructura en **7 módulos temáticos independientes**.

Cada carpeta contiene:
1. `foto_perfil.jpg`: Imagen optimizada de alta resolución para la foto de perfil del grupo/canal en WhatsApp.
2. `info_grupo.txt`: Documento de texto listo para **copiar y pegar**, con nombres oficiales sugeridos, alternativos y la descripción formateada con emojis, negritas y saltos de línea compatibles con WhatsApp.

---

## 🗂️ 2. Matriz de Canales y Asignación de Activos

| Carpeta | Canal / Grupo en WhatsApp | Activos Principales | Foto Asignada | Propósito Editorial |
|---|---|---|---|---|
| [`01_macro_y_apertura`](./01_macro_y_apertura/) | **Grupo Inteligencia \| Comunidad de Traders** _(grupo de Avisos)_ | Calendario Económico, Tasas (Fed, BCCh, BCE, BoJ), Yields USA, DXY | `LOGO-Fondo-Negro.jpg` | Contexto macro de la mañana, datos de alto impacto e informes PDF. **No es un canal temático**: es el grupo de Avisos de la comunidad. |
| [`02_forex_divisas`](./02_forex_divisas/) | **GI · Forex & Divisas** | USD/CLP, EUR/USD, USD/JPY, GBP/USD, DXY | `usdclp.jpg` | Monitoreo del tipo de cambio, diferenciales de tasas y niveles técnicos MT5. |
| [`03_commodities_materias_primas`](./03_commodities_materias_primas/) | **GI · Commodities & Materias Primas** | Oro (XAU/USD), WTI, Cobre (COPPER USD/t), Plata (XAG/USD) | `oro.jpg` | Metales y energía con drivers de OPEP+, inventarios EIA y demanda China. |
| [`04_indices_bursatiles`](./04_indices_bursatiles/) | **GI · Índices Bursátiles** | Nasdaq 100 (US100), S&P 500 (US500), Dow Jones (US30), DAX 40 | `us100.jpg` | Apertura de Wall Street, rotación sectorial y sentimiento de riesgo. |
| [`05_acciones_etfs`](./05_acciones_etfs/) | **GI · Acciones & ETFs** | Mega-caps (#AAPL, #MSFT, #NVDA, #MELI), Bancos, ETFs (QQQ, SPY, SOXX, IWM) | `tech-circuito.jpg` | Temporada de earnings, ciclo de semiconductores/IA y fondos cotizados. |
| [`06_criptoactivos`](./06_criptoactivos/) | **GI · Criptoactivos & Digital Assets** | Bitcoin (BTC/USD), Ethereum (ETH/USD), Solana (SOL/USD), Altcoins | `eth.jpg` | Análisis cuantitativo sobrio en 4H/1D y flujos institucionales en ETFs spot. |
| [`07_oportunidades_cuantitativas`](./07_oportunidades_cuantitativas/) | **GI · Oportunidades & Trading Cuantitativo** | Multiactivo (Setups VIP Playbook V2) | `us500.jpg` | Señales tácticas selectivas (máx 3/sem) con TP y SL calculados en CLP. |

---

## 🛠️ 3. Instrucciones de Configuración en WhatsApp

Para configurar cada grupo o canal oficial:

1. **Crear el Grupo o Canal**:
   - En WhatsApp Business o WhatsApp Web/Móvil, seleccionar *Nuevo grupo* o *Nuevo canal*.
2. **Asignar la Foto de Perfil**:
   - Subir el archivo `foto_perfil.jpg` ubicado dentro de la carpeta correspondiente.
3. **Pegar el Nombre del Grupo**:
   - Copiar el nombre recomendado desde `info_grupo.txt` (ej. `GI · Forex & Divisas`).
4. **Pegar la Descripción**:
   - Copiar el bloque completo de descripción desde `info_grupo.txt` y pegarlo en la sección de información del grupo.
5. **Ajustar Permisos de Envío**:
   - En *Ajustes del grupo > Enviar mensajes*, seleccionar **Solo administradores** para asegurar un canal limpio, profesional y enfocado en la entrega de análisis de valor.

---

## ⚖️ 4. Estándares Editoriales de la Marca

- **Claridad y Dirección**: Cada publicación responde hacia dónde se dirige el activo (alcista, bajista o lateral) sin rodeos ni ambigüedades.
- **Tono Pedagógico y Cercano**: Se explica con paciencia y profesionalismo, sin usar lenguaje dramático o catastrófico.
- **Precios Verificados**: Cero estimaciones manuales. Todos los niveles y decimales respetan la tabla `digits` de MetaTrader 5 (`USDCLP`: 2, `USDJPY`: 3, `XAUUSD`: 2, `WTI`: 3, `COPPER`: 1 en USD/t).
- **Aviso de Riesgo y No Asesoría**: Todos los canales operan bajo la premisa de educación financiera y análisis de mercado, sin promesas de rentabilidad ni gestión de fondos de terceros.
