# Indicador MT5: GI Canales, Zonas S/R y Líneas de Seguridad

Este indicador nativo MQL5 (`GI_Canales_Seguridad.mq5` / `GI_Canales_Seguridad.ex5`) traslada con **100% de paridad matemática y visual** el motor de trazado de TradingView (`scripts/tradingview_grafico.py` y `scripts/estrategia/tori/`) directamente al terminal MetaTrader 5.

---

## 1. Fundamento Matemático del Trazado

El motor se rige por la doctrina institucional de **Tori Trades** y el estándar editorial de **Grupo Inteligencia**:

### A. Unidad de Medida Dinámica: ATR(14) Wilder
Todas las tolerancias, holguras, distancias de pivote y espesores de zonas no usan puntos fijos, sino múltiplos de la volatilidad real del marco mediante el **Average True Range (14 periodos)**:
$$TR_t = \max(High_t - Low_t, \; |High_t - Close_{t-1}|, \; |Low_t - Close_{t-1}|)$$
$$ATR_t = \frac{ATR_{t-1} \times 13 + TR_t}{14}$$

### B. Detección de Pivotes (ZigZag Adaptativo)
- **Umbral de giro:** $\text{InpZigZagATR} = 2.0 \times ATR$ para diagonales; $1.5 \times ATR$ para horizontales.
- Un pivote de Máximo ($H$) o Mínimo ($L$) se confirma solo cuando el precio retrocede esa distancia desde el extremo.

### C. Directrices Diagonales (Semirrectas)
1. **Punto A (Ancla inicial):** Extremo absoluto visible y confirmado ($L$ mínimo para alcistas, $H$ máximo para bajistas).
2. **Punto B (Segundo anclaje):** Pivote posterior que maximiza los toques respetando la pendiente ($>0$ alcista, $<0$ bajista, $|m| \ge 0.02 \times ATR$) sin violar la condición de no-intersección.
3. **Condición de No-Intersección:**
   $$\text{holgura} = Low_t - \text{línea}_t \quad (\text{alcista})$$
   $$\text{holgura} = \text{línea}_t - High_t \quad (\text{bajista})$$
   - Si $\text{holgura} < -0.25 \times ATR$ antes de $B$, la directriz es descartada (línea no limpia).
   - Si una vela **cierra** con holgura $< -0.25 \times ATR$ después de $B$, se registra la **ruptura** por cierre.
4. **Conteo de Toques con Histéresis:**
   - Toque registrado si $\text{holgura} \le 0.25 \times ATR$.
   - Separación mínima para siguiente toque: $\ge 1.0 \times ATR$.
   - Calidad **A+**: $\ge 3$ toques y duración $\ge 30$ velas.

### D. Asignación de Roles Estratégicos
- **Línea de Seguridad (`#26C6A0` - Verde Esmeralda):** Directriz activa que sostiene la tendencia (directriz alcista por mínimos en compras; bajista por máximos en ventas). Define la referencia técnica de salida y trailing stop.
- **Línea de Acción (`#FF4D5E` - Rojo Coral):** Directriz opuesta rota que gatilló el setup (en ruptura) o directriz superior del canal.
- **Línea de Seguimiento (`#9BE7C4` - Verde Menta):** Abanico acelerado con mayor pendiente trazado desde el último toque para trailing ceñido.

### E. Zonas de Soporte y Resistencia Horizontales Operables
- **Separación de Directrices Diagonales:** Las líneas de tendencia dinámicas (Seguridad y Acción) ya no se confunden con niveles horizontales de soporte/resistencia.
- **Filtro de Distancia Mínima Operable (`InpMinDistanciaATR = 1.0`):** Excluye cualquier nivel a menos de $1,0 \times ATR$ del precio spot para evitar colapsos contra la vela en curso y garantizar un ratio Riesgo/Beneficio ($\ge 1,5$).
- **Clustering:** Agrupamiento de pivotes a distancia $\le 0.5 \times ATR$.
- **Espesor de la Zona (Idéntico a TradingView):**
  $$\text{Semiancho} = \text{media\_zona} = 0.18 \times ATR_{14}$$
  $$\text{Zona} = [\text{Nivel} - 0.18 \times ATR, \;\; \text{Nivel} + 0.18 \times ATR]$$
- Se dibujan como rectángulos semitransparentes en amarillo ámbar (`#FFD54F`) con línea central punteada y etiqueta de precio.

---

## 2. Instalación en MetaTrader 5

El archivo compilado ya está colocado en la carpeta de terminal activa:
- **Ruta instalada:** `%APPDATA%\MetaQuotes\Terminal\D0E8209F77C8CF37AD8BF550E51FF075\MQL5\Indicators\GI_Canales_Seguridad.ex5`
- **Ruta fuente en repo:** `mql5/GI_Canales_Seguridad.mq5`

### Pasos para usar en MT5:
1. Abre tu MetaTrader 5.
2. En la ventana **Navegador** (Ctrl+N), despliega **Indicadores**.
3. Haz clic derecho sobre la carpeta "Indicadores" y selecciona **Actualizar** (Refresh) si no aparece de inmediato.
4. Arrastra **GI_Canales_Seguridad** al gráfico de cualquier activo (ej. `USDCLP`, `XAUUSD`, `EURUSD`, `WTI.spot`) en temporalidad **H4** o **H1**.
5. En la pestaña de parámetros puedes personalizar los colores, umbrales o activar/desactivar el HUD.

---

## 3. Elementos en el Gráfico MT5

1. **Directrices de Tendencia:** Ray proyectado a la derecha con el color de su rol.
2. **Franjas Rectangulares S/R:** Zonas de soporte y resistencia que coinciden con los niveles de las piezas publicadas.
3. **HUD Dashboard:** Panel en la esquina superior izquierda con:
   - Sesgo y Estado (`TENDENCIA`, `RUPTURA`, `REBOTE`, `RANGO`).
   - Precio de la Línea de Seguridad y calidad (`A+`/`B`).
   - Soporte y Resistencia clave.
   - ATR(14) en valor nominal.
