//+------------------------------------------------------------------+
//|                                     Sistema_Impulso_Elder.mq5    |
//|                    Desarrollado desde cero para cumplir reglas   |
//|                    del Dr. Alexander Elder ("Vivir del Trading") |
//+------------------------------------------------------------------+
#property copyright   "Generado a medida, código 100% original"
#property description "Sistema Impulso de Alexander Elder"
#property description "Color verde: Alcista (Prohibido Cortos)"
#property description "Color rojo: Bajista (Prohibido Largos)"
#property description "Color azul: Neutral (Sin restricciones)"
#property version     "1.00"
#property indicator_chart_window
#property indicator_buffers 5
#property indicator_plots   1

//--- Configuración de la gráfica de velas
#property indicator_label1  "Impulso Elder"
#property indicator_type1   DRAW_COLOR_CANDLES
#property indicator_color1  clrLimeGreen, clrRed, clrDodgerBlue
#property indicator_style1  STYLE_SOLID
#property indicator_width1  2

//--- Parámetros del sistema de trading
input int                  InpPeriodoEMA = 13;          // Período de la EMA Rápida
input int                  InpMACDFast   = 12;          // Período MACD Rápido
input int                  InpMACDSlow   = 26;          // Período MACD Lento
input int                  InpMACDSignal = 9;           // Período Señal MACD
input ENUM_APPLIED_PRICE   InpPrecio     = PRICE_CLOSE; // Precio Aplicado

//--- Buffers para renderizar las velas OHLC y su color
double BufferOpen[];
double BufferHigh[];
double BufferLow[];
double BufferClose[];
double BufferColor[];

//--- Variables para guardar las referencias (handles) a los indicadores nativos
int handle_ema;
int handle_macd;

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
  {
   // Mapeo de los buffers al gráfico
   SetIndexBuffer(0, BufferOpen, INDICATOR_DATA);
   SetIndexBuffer(1, BufferHigh, INDICATOR_DATA);
   SetIndexBuffer(2, BufferLow, INDICATOR_DATA);
   SetIndexBuffer(3, BufferClose, INDICATOR_DATA);
   SetIndexBuffer(4, BufferColor, INDICATOR_COLOR_INDEX);

   IndicatorSetString(INDICATOR_SHORTNAME, "Impulso Elder Original ("+(string)InpPeriodoEMA+")");
   IndicatorSetInteger(INDICATOR_DIGITS, _Digits);

   // Solicitamos a MetaTrader los handles para los indicadores técnicos que necesitamos
   handle_ema = iMA(_Symbol, _Period, InpPeriodoEMA, 0, MODE_EMA, InpPrecio);
   if(handle_ema == INVALID_HANDLE) 
     {
      Print("Error crítico: Imposible crear el handle para la EMA.");
      return INIT_FAILED;
     }

   handle_macd = iMACD(_Symbol, _Period, InpMACDFast, InpMACDSlow, InpMACDSignal, InpPrecio);
   if(handle_macd == INVALID_HANDLE) 
     {
      Print("Error crítico: Imposible crear el handle para el MACD.");
      return INIT_FAILED;
     }

   return INIT_SUCCEEDED;
  }

//+------------------------------------------------------------------+
//| Custom indicator iteration function                              |
//+------------------------------------------------------------------+
int OnCalculate(const int rates_total,
                const int prev_calculated,
                const datetime &time[],
                const double &open[],
                const double &high[],
                const double &low[],
                const double &close[],
                const long &tick_volume[],
                const long &volume[],
                const int &spread[])
  {
   // Requerimos al menos tantas barras como el período lento del MACD
   if(rates_total < InpMACDSlow) return 0;

   // Convertimos todos los arrays al formato "Serie temporal", 
   // donde el índice 0 es la barra actual en formación (la más reciente a la derecha).
   ArraySetAsSeries(open, true);
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(close, true);
   
   ArraySetAsSeries(BufferOpen, true);
   ArraySetAsSeries(BufferHigh, true);
   ArraySetAsSeries(BufferLow, true);
   ArraySetAsSeries(BufferClose, true);
   ArraySetAsSeries(BufferColor, true);

   // Calculamos el límite de barras que debemos actualizar.
   // Esto asegura que no recalculemos todo el histórico en cada tick, ahorrando CPU.
   int limit;
   if(prev_calculated == 0)
      limit = rates_total - 2; // -2 para no salirnos del rango al mirar i+1 (vela anterior)
   else
      limit = rates_total - prev_calculated; 

   if(limit < 0) limit = 0;

   // Buffers locales para recoger los datos de EMA y MACD
   double val_ema[];
   double val_macd_main[];
   double val_macd_signal[];
   
   ArraySetAsSeries(val_ema, true);
   ArraySetAsSeries(val_macd_main, true);
   ArraySetAsSeries(val_macd_signal, true);

   // Copiamos solamente los datos que necesitamos actualizar + 2 barras extra de historial
   if(CopyBuffer(handle_ema, 0, 0, limit + 2, val_ema) <= 0) return 0;
   if(CopyBuffer(handle_macd, 0, 0, limit + 2, val_macd_main) <= 0) return 0;
   if(CopyBuffer(handle_macd, 1, 0, limit + 2, val_macd_signal) <= 0) return 0;

   // Bucle principal: recorremos de atrás hacia adelante hasta llegar a la barra actual (0)
   for(int i = limit; i >= 0; i--)
     {
      // 1. Dibujamos el cuerpo de la vela actual copiando los OHLC
      BufferOpen[i]  = open[i];
      BufferHigh[i]  = high[i];
      BufferLow[i]   = low[i];
      BufferClose[i] = close[i];
      
      // 2. Extraemos valores de la EMA
      double ema_curr = val_ema[i];
      double ema_prev = val_ema[i+1];
      
      // 3. Calculamos el Histograma MACD (MACD Línea principal - MACD Señal)
      double hist_curr = val_macd_main[i] - val_macd_signal[i];
      double hist_prev = val_macd_main[i+1] - val_macd_signal[i+1];
      
      // 4. Determinamos las pendientes
      bool ema_sube  = (ema_curr > ema_prev);
      bool ema_baja  = (ema_curr < ema_prev);
      
      bool hist_sube = (hist_curr > hist_prev);
      bool hist_baja = (hist_curr < hist_prev);
      
      // 5. Aplicamos la lógica de color del Sistema Impulso
      if(ema_sube && hist_sube)
         BufferColor[i] = 0; // ClrLimeGreen (Toros al control)
      else if(ema_baja && hist_baja)
         BufferColor[i] = 1; // ClrRed (Osos al control)
      else
         BufferColor[i] = 2; // ClrDodgerBlue (Neutral, se puede ir largo o corto)
     }
     
   return rates_total;
  }
//+------------------------------------------------------------------+
