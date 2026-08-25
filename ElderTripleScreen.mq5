//+------------------------------------------------------------------+
//|                                            ElderTripleScreen.mq5 |
//|                                      Alexander Elder EA Strategy |
//+------------------------------------------------------------------+
#property copyright "Generado por Asistente de IA"
#property link      ""
#property version   "1.00"
#property description "Sistema de Trading de Triple Pantalla y Sistema Impulso de Alexander Elder"

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>este
#include <Trade\AccountInfo.mqh>
#include <Trade\SymbolInfo.mqh>


//--- Parámetros de Entrada (Inputs)
input ENUM_TIMEFRAMES InpTimeframeBase = PERIOD_D1; // 1. Gráfico Intermedio (Tactical)
input ENUM_TIMEFRAMES InpTimeframeTrend = PERIOD_W1; // 1. Gráfico a Largo Plazo (Strategic - x5)
input int InpEmaImpulsePeriod = 13; // 2. Periodos EMA Impulso
input int InpMacdFast = 12; // 2. MACD Rápida
input int InpMacdSlow = 26; // 2. MACD Lenta
input int InpMacdSignal = 9; // 2. MACD Señal
input int InpForceIndexPeriod = 2; // 3. Periodos Oscilador Índice de Fuerza
input int InpEmaBasePeriod = 13; // 4. EMA para penetración
input int InpAtrPeriod = 14; // 5. Periodos ATR
input double InpRiskPercent = 2.0; // 5. Regla del 2% por trade
input double InpMaxMonthlyDrawdown = 6.0; // 5. Regla del 6% mensual
input double InpAtrStopLossMult = 2.0; // Distancia del SL en ATRs
input double InpAtrTakeProfitMult = 2.5; // Multiplicador para TP en el canal
input int InpPenetrationLookback = 50; // Barras para calcular penetración promedio

CTrade trade;
CPositionInfo posInfo;
CAccountInfo accInfo;
CSymbolInfo symInfo;

//--- Handles de los indicadores
int handleEmaTrend;
int handleMacdTrend;
int handleForceIndexBase;
int handleEmaBase;
int handleAtrBase;

//--- Variables para la gestión del 6%
double initialMonthlyEquity = 0;
int currentMonth = -1;
double initialMonthlyBalance = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   symInfo.Name(_Symbol);
   
   // Inicialización de indicadores
   handleEmaTrend = iMA(_Symbol, InpTimeframeTrend, InpEmaImpulsePeriod, 0, MODE_EMA, PRICE_CLOSE);
   handleMacdTrend = iMACD(_Symbol, InpTimeframeTrend, InpMacdFast, InpMacdSlow, InpMacdSignal, PRICE_CLOSE);
   handleForceIndexBase = iForce(_Symbol, InpTimeframeBase, InpForceIndexPeriod, MODE_EMA, VOLUME_TICK);
   handleEmaBase = iMA(_Symbol, InpTimeframeBase, InpEmaBasePeriod, 0, MODE_EMA, PRICE_CLOSE);
   handleAtrBase = iATR(_Symbol, InpTimeframeBase, InpAtrPeriod);
   
   if(handleEmaTrend == INVALID_HANDLE || handleMacdTrend == INVALID_HANDLE || 
      handleForceIndexBase == INVALID_HANDLE || handleEmaBase == INVALID_HANDLE || handleAtrBase == INVALID_HANDLE)
     {
      Print("Error inicializando los indicadores. Código: ", GetLastError());
      return(INIT_FAILED);
     }
     
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   IndicatorRelease(handleEmaTrend);
   IndicatorRelease(handleMacdTrend);
   IndicatorRelease(handleForceIndexBase);
   IndicatorRelease(handleEmaBase);
   IndicatorRelease(handleAtrBase);
  }

//+------------------------------------------------------------------+
//| Revisar e inicializar el control del 6% mensual                  |
//+------------------------------------------------------------------+
void CheckMonthlyEquity()
  {
   MqlDateTime dt;
   TimeCurrent(dt);
   // Si cambiamos de mes, actualizamos el equity inicial
   if(dt.mon != currentMonth)
     {
      currentMonth = dt.mon;
      initialMonthlyEquity = accInfo.Equity();
     }
  }

//+------------------------------------------------------------------+
//| Regla del 6% (Control de Pirañas)                                |
//+------------------------------------------------------------------+
bool IsSixPercentRuleViolated()
  {
   // Pérdida permitida es el 6% del equity inicial del mes
   double allowedDrawdown = initialMonthlyEquity * (InpMaxMonthlyDrawdown / 100.0);
   double currentDrawdown = initialMonthlyEquity - accInfo.Equity();
   
   if(currentDrawdown >= allowedDrawdown)
     {
      return true; // Sistema bloqueado para este mes
     }
   return false;
  }

//+------------------------------------------------------------------+
//| Técnica de Entrada: Calcular la penetración promedio (Pantalla 3)|
//+------------------------------------------------------------------+
double GetAveragePenetration(bool isBuy)
  {
   double emaBase[];
   double low[], high[];
   ArraySetAsSeries(emaBase, true);
   ArraySetAsSeries(low, true);
   ArraySetAsSeries(high, true);
   
   if(CopyBuffer(handleEmaBase, 0, 1, InpPenetrationLookback, emaBase) <= 0) return 0;
   if(CopyLow(_Symbol, InpTimeframeBase, 1, InpPenetrationLookback, low) <= 0) return 0;
   if(CopyHigh(_Symbol, InpTimeframeBase, 1, InpPenetrationLookback, high) <= 0) return 0;
   
   double totalPenetration = 0;
   int count = 0;
   
   for(int i = 0; i < InpPenetrationLookback; i++)
     {
      if(isBuy)
        {
         if(low[i] < emaBase[i]) // Cuánto cae por debajo de la EMA rápida
           {
            totalPenetration += (emaBase[i] - low[i]);
            count++;
           }
        }
      else
        {
         if(high[i] > emaBase[i]) // Cuánto sube por encima de la EMA rápida
           {
            totalPenetration += (high[i] - emaBase[i]);
            count++;
           }
        }
     }
   
   if(count > 0) return totalPenetration / count;
   return 0; // Si no hay penetraciones, devuelve 0
  }

//+------------------------------------------------------------------+
//| Poner las esposas a la operación (Trailing Stop)                 |
//+------------------------------------------------------------------+
void ManageTrailingStops()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      if(posInfo.SelectByIndex(i))
        {
         if(posInfo.Symbol() == _Symbol)
           {
            double openPrice = posInfo.PriceOpen();
            double tp = posInfo.TakeProfit();
            double sl = posInfo.StopLoss();
            
            if(posInfo.PositionType() == POSITION_TYPE_BUY)
              {
               double distToTp = tp - openPrice;
               // Si ha avanzado al menos un 30% del TP, movemos a Break Even
               if(distToTp > 0 && symInfo.Bid() >= openPrice + (distToTp * 0.30))
                 {
                  if(sl < openPrice) // Solo si no está ya en break even
                    {
                     trade.PositionModify(posInfo.Ticket(), openPrice, tp);
                    }
                 }
              }
            else if(posInfo.PositionType() == POSITION_TYPE_SELL)
              {
               double distToTp = openPrice - tp;
               if(distToTp > 0 && symInfo.Ask() <= openPrice - (distToTp * 0.30))
                 {
                  if(sl > openPrice || sl == 0) // Solo si no está ya en break even
                    {
                     trade.PositionModify(posInfo.Ticket(), openPrice, tp);
                    }
                 }
              }
           }
        }
     }
  }

//+------------------------------------------------------------------+
//| Función principal - OnTick                                       |
//+------------------------------------------------------------------+
void OnTick()
  {
   if(!symInfo.RefreshRates()) return;
   
   // 5. Verificar Regla del 6% y tracking mensual
   CheckMonthlyEquity();
   if(IsSixPercentRuleViolated()) return; // Abortar trading
   
   // 6. Gestionar salidas y "esposas" (Trailing to Break Even)
   ManageTrailingStops();
   
   // Lógica de EAs conservadores: Operar una posición a la vez
   if(PositionsTotal() > 0 || OrdersTotal() > 0) return; 
   
   //--- Obtener datos de Indicadores ---
   double emaTrend[], macdMain[], macdSignal[], forceBase[], emaBase[], atrBase[];
   // Usamos ArraySetAsSeries para leer [0] como la vela anterior (cerrada) y [1] como la penúltima
   ArraySetAsSeries(emaTrend, true); ArraySetAsSeries(macdMain, true); ArraySetAsSeries(macdSignal, true);
   ArraySetAsSeries(forceBase, true); ArraySetAsSeries(emaBase, true); ArraySetAsSeries(atrBase, true);
   
   if(CopyBuffer(handleEmaTrend, 0, 1, 2, emaTrend) <= 0) return;
   if(CopyBuffer(handleMacdTrend, 0, 1, 2, macdMain) <= 0) return; 
   if(CopyBuffer(handleMacdTrend, 1, 1, 2, macdSignal) <= 0) return;
   if(CopyBuffer(handleForceIndexBase, 0, 1, 2, forceBase) <= 0) return;
   if(CopyBuffer(handleEmaBase, 0, 1, 2, emaBase) <= 0) return;
   if(CopyBuffer(handleAtrBase, 0, 1, 1, atrBase) <= 0) return;
   
   // 2. Primera Pantalla (Sistema Impulso) en timeframe estratégico
   // Histograma MACD = Línea MACD - Línea Señal
   double histTrendCurrent = macdMain[0] - macdSignal[0];
   double histTrendPrev = macdMain[1] - macdSignal[1];
   
   bool isGreen = (emaTrend[0] > emaTrend[1]) && (histTrendCurrent > histTrendPrev);
   bool isRed = (emaTrend[0] < emaTrend[1]) && (histTrendCurrent < histTrendPrev);
   
   // 3. Segunda Pantalla y 4. Tercera Pantalla (Técnica de Entrada Limitada)
   if(!isRed && forceBase[0] < 0) 
     {
      // Permitido comprar (Luz Verde o Azul) y Force Index indica sobreventa
      double avgPen = GetAveragePenetration(true);
      double entryPrice = emaBase[0] - avgPen; // Orden Limit por debajo del valor
      
      // Sanitizar precio limit (debe ser menor al ask actual)
      if (entryPrice > symInfo.Ask()) entryPrice = symInfo.Ask() - (10 * symInfo.Point()); 
      
      // 5. Gestión del Riesgo
      double sl = entryPrice - (atrBase[0] * InpAtrStopLossMult);
      double tp = emaBase[0] + (atrBase[0] * InpAtrTakeProfitMult); 
      
      double riskPerUnit = entryPrice - sl;
      
      if(riskPerUnit > 0)
        {
         // Regla del 2%
         double accountRiskAmount = accInfo.Equity() * (InpRiskPercent / 100.0);
         double tickVal = symInfo.TickValue();
         double ticksAtRisk = riskPerUnit / symInfo.Point();
         
         double rawLots = accountRiskAmount / (ticksAtRisk * tickVal);
         double lotSize = MathFloor(rawLots / symInfo.LotStep()) * symInfo.LotStep();
         
         if(lotSize >= symInfo.LotMin())
           {
            trade.BuyLimit(lotSize, entryPrice, _Symbol, sl, tp, ORDER_TIME_GTC);
           }
         else
           {
            Print("Operación abortada: El lote mínimo arriesga más del ", InpRiskPercent, "%");
           }
        }
     }
   else if(!isGreen && forceBase[0] > 0)
     {
      // Permitido vender (Luz Roja o Azul) y Force Index indica sobrecompra
      double avgPen = GetAveragePenetration(false);
      double entryPrice = emaBase[0] + avgPen;
      
      if (entryPrice < symInfo.Bid()) entryPrice = symInfo.Bid() + (10 * symInfo.Point());
      
      double sl = entryPrice + (atrBase[0] * InpAtrStopLossMult);
      double tp = emaBase[0] - (atrBase[0] * InpAtrTakeProfitMult);
      
      double riskPerUnit = sl - entryPrice;
      
      if(riskPerUnit > 0)
        {
         // Regla del 2%
         double accountRiskAmount = accInfo.Equity() * (InpRiskPercent / 100.0);
         double tickVal = symInfo.TickValue();
         double ticksAtRisk = riskPerUnit / symInfo.Point();
         
         double rawLots = accountRiskAmount / (ticksAtRisk * tickVal);
         double lotSize = MathFloor(rawLots / symInfo.LotStep()) * symInfo.LotStep();
         
         if(lotSize >= symInfo.LotMin())
           {
            trade.SellLimit(lotSize, entryPrice, _Symbol, sl, tp, ORDER_TIME_GTC);
           }
         else
           {
            Print("Operación abortada: El lote mínimo arriesga más del ", InpRiskPercent, "%");
           }
        }
     }
  }
//+------------------------------------------------------------------+
//| Criterio Custom para Walk-Forward (IS vs OOS)                    |
//+------------------------------------------------------------------+
double OnTester()
  {
   double profit = TesterStatistics(STAT_PROFIT);
   double max_dd = TesterStatistics(STAT_EQUITY_DD);
   double trades = TesterStatistics(STAT_TRADES);
   
   if(trades < 10) return -1.0; // Penalizar fuertemente si no hay operaciones suficientes
   
   double win_rate = TesterStatistics(STAT_PROFIT_TRADES) / trades;
   if(max_dd == 0.0) max_dd = 0.01; // Prevenir división por cero
   
   // Puntaje de Eficiencia WF = Factor de Recuperación * WinRate * Log(Frecuencia)
   double custom_score = (profit / max_dd) * win_rate * MathLog(trades);
   
   // Retorna el valor al optimizador (busca maximizar este número)
   return custom_score;
  }
//+------------------------------------------------------------------+
