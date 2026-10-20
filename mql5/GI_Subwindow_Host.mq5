//+------------------------------------------------------------------+
//|                                         GI_Subwindow_Host.mq5    |
//|                    Grupo Inteligencia - Análisis de Mercado      |
//|               Lienzo Dedicado en Subventana Inferior MT5         |
//+------------------------------------------------------------------+
#property copyright   "Grupo Inteligencia"
#property link        "https://grupointeligencia.cl"
#property version     "1.02"
#property description "Indicador ultra-ligero y elástico que reserva y hospeda la subventana"
#property description "inferior para el Asesor Experto GI_Risk_Cockpit."
#property indicator_separate_window
#property indicator_buffers 0
#property indicator_plots   0

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
  {
   IndicatorSetString(INDICATOR_SHORTNAME, "GI Risk Cockpit Dock");
   IndicatorSetInteger(INDICATOR_DIGITS, 0);
   IndicatorSetInteger(INDICATOR_HEIGHT, 225); // Altura cómoda inicial en píxeles
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
   return(rates_total);
  }
//+------------------------------------------------------------------+
