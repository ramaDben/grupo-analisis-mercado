//+------------------------------------------------------------------+
//|                                                ElderImpulse.mq5  |
//|                                      Copyright 2024, Antigravity |
//|                                                                  |
//+------------------------------------------------------------------+
#property copyright "Basado en El Nuevo Vivir del Trading - Alexander Elder"
#property link      "https://www.mql5.com"
#property version   "1.00"
#property indicator_chart_window
#property indicator_buffers 5
#property indicator_plots   1

//--- configuración del gráfico de velas de colores
#property indicator_label1  "Elder Impulse System"
#property indicator_type1   DRAW_COLOR_CANDLES
#property indicator_color1  clrLimeGreen, clrRed, clrDodgerBlue
#property indicator_style1  STYLE_SOLID
#property indicator_width1  2

//--- parámetros de entrada según el sistema de Alexander Elder
input int                  InpEmaPeriod  = 13;          // EMA Period
input int                  InpMacdFast   = 12;          // MACD Fast EMA
input int                  InpMacdSlow   = 26;          // MACD Slow EMA
input int                  InpMacdSignal = 9;           // MACD Signal SMA
input ENUM_APPLIED_PRICE   InpPrice      = PRICE_CLOSE; // Applied Price

//--- buffers del indicador para dibujar las velas y su color
double         OpenBuffer[];
double         HighBuffer[];
double         LowBuffer[];
double         CloseBuffer[];
double         ColorBuffer[];

//--- handles para obtener los datos de los indicadores
int            ema_handle;
int            macd_handle;

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
  {
//--- mapeo de los buffers del indicador
   SetIndexBuffer(0, OpenBuffer, INDICATOR_DATA);
   SetIndexBuffer(1, HighBuffer, INDICATOR_DATA);
   SetIndexBuffer(2, LowBuffer, INDICATOR_DATA);
   SetIndexBuffer(3, CloseBuffer, INDICATOR_DATA);
   SetIndexBuffer(4, ColorBuffer, INDICATOR_COLOR_INDEX);

   IndicatorSetString(INDICATOR_SHORTNAME, "Elder Impulse (" + IntegerToString(InpEmaPeriod) + ")");
   IndicatorSetInteger(INDICATOR_DIGITS, _Digits);

//--- configurar los arrays como series (el índice 0 es la vela actual)
   ArraySetAsSeries(OpenBuffer, true);
   ArraySetAsSeries(HighBuffer, true);
   ArraySetAsSeries(LowBuffer, true);
   ArraySetAsSeries(CloseBuffer, true);
   ArraySetAsSeries(ColorBuffer, true);

//--- inicializar el handle de la EMA
   ema_handle = iMA(_Symbol, _Period, InpEmaPeriod, 0, MODE_EMA, InpPrice);
   if(ema_handle == INVALID_HANDLE)
     {
      Print("Error al cargar la EMA: ", GetLastError());
      return(INIT_FAILED);
     }

//--- inicializar el handle del MACD
   macd_handle = iMACD(_Symbol, _Period, InpMacdFast, InpMacdSlow, InpMacdSignal, InpPrice);
   if(macd_handle == INVALID_HANDLE)
     {
      Print("Error al cargar el MACD: ", GetLastError());
      return(INIT_FAILED);
     }

   return(INIT_SUCCEEDED);
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
//--- necesitamos suficientes barras para el MACD
   if(rates_total < InpMacdSlow)
      return(0);

//--- determinar cuántas barras copiar
   int to_copy;
   if(prev_calculated == 0)
      to_copy = rates_total;
   else
      to_copy = rates_total - prev_calculated + 1;

//--- buffers temporales
   double ema[];
   double macd_main[];
   double macd_signal[];
   
   ArraySetAsSeries(ema, true);
   ArraySetAsSeries(macd_main, true);
   ArraySetAsSeries(macd_signal, true);
   
   ArraySetAsSeries(open, true);
   ArraySetAsSeries(high, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(close, true);

//--- copiamos los datos necesarios. Se copia to_copy + 1 porque necesitamos evaluar el cambio con respecto a la vela anterior (i+1)
   if(CopyBuffer(ema_handle, 0, 0, to_copy + 1, ema) <= 0) return 0;
   if(CopyBuffer(macd_handle, 0, 0, to_copy + 1, macd_main) <= 0) return 0;
   if(CopyBuffer(macd_handle, 1, 0, to_copy + 1, macd_signal) <= 0) return 0;

//--- límite de iteración
   int limit = to_copy - 1;
   if (prev_calculated == 0)
      limit = rates_total - 2; // Evitamos desbordamiento en la primera barra

//--- cálculo del sistema de impulso de Elder
   for(int i = limit; i >= 0; i--)
     {
      // 1. Dibujar los valores de las velas sobre el gráfico
      OpenBuffer[i] = open[i];
      HighBuffer[i] = high[i];
      LowBuffer[i] = low[i];
      CloseBuffer[i] = close[i];

      // 2. Extraer datos actuales y anteriores
      double ema_current = ema[i];
      double ema_prev    = ema[i+1];
      
      // En el libro "El Nuevo Vivir del Trading", el histograma MACD es la diferencia entre la línea principal y la señal.
      double macd_hist_current = macd_main[i] - macd_signal[i];
      double macd_hist_prev    = macd_main[i+1] - macd_signal[i+1];
      
      // 3. Evaluar el impulso
      bool is_ema_up   = (ema_current > ema_prev);
      bool is_ema_down = (ema_current < ema_prev);
      
      bool is_macd_up   = (macd_hist_current > macd_hist_prev);
      bool is_macd_down = (macd_hist_current < macd_hist_prev);
      
      // 4. Asignar el color
      if(is_ema_up && is_macd_up)
         ColorBuffer[i] = 0; // Verde: Tendencia y Momento al alza (Toros al control)
      else if(is_ema_down && is_macd_down)
         ColorBuffer[i] = 1; // Rojo: Tendencia y Momento a la baja (Osos al control)
      else
         ColorBuffer[i] = 2; // Azul/DodgerBlue: Divergencia entre ambos (Neutralidad)
     }

   return(rates_total);
  }
//+------------------------------------------------------------------+
