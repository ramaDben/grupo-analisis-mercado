//+------------------------------------------------------------------+
//|                                           GI_Risk_Cockpit.mq5    |
//|                    Grupo Inteligencia - Análisis de Mercado      |
//|               Cockpit Institucional de Gestión de Riesgo         |
//+------------------------------------------------------------------+
#property copyright   "Grupo Inteligencia"
#property link        "https://grupointeligencia.cl"
#property version     "1.21"
#property description "Asesor Experto institucional que transforma la subventana inferior"
#property description "en un centro de mando con cálculo dinámico de lotaje por riesgo y"
#property description "botones dedicados para fijar SL y TP a las directrices de TV con precios en vivo,"
#property description "proyección gráfica en ventana principal y espaciado elástico superior."

#include <Trade\Trade.mqh>
#include <Trade\PositionInfo.mqh>
#include <Trade\AccountInfo.mqh>

//+------------------------------------------------------------------+
//| ENUMERACIONES                                                    |
//+------------------------------------------------------------------+
enum ENUM_MODO_RIESGO
  {
   RIESGO_05_PCT,
   RIESGO_10_PCT,
   RIESGO_20_PCT,
   RIESGO_FIJO_USD
  };

enum ENUM_SL_LINEA
  {
   SL_SEGURIDAD,      // 🟢 Seguridad (Piso/Techo dinámico)
   SL_SOPORTE_SR,      // 🟡 Soporte S/R (Horizontal estructural)
   SL_SEGUIMIENTO,     // 🟢 Seguimiento (Abanico acelerado)
   SL_ACCION,          // 🔴 Acción (Gatillo/Pullback)
   SL_CONTEXTO_D1,     // 🟣 Contexto D1 (Directriz mayor)
   SL_PISO_RANGO       // ⚪ Piso Rango (Mínimo lateral)
  };

enum ENUM_TP_LINEA
  {
   TP_RESISTENCIA_SR,  // 🟡 Resistencia S/R (Horizontal estructural)
   TP_ACCION_QUIEBRE,  // 🔴 Acción Quiebre (Gatillo contrario)
   TP_CONTEXTO_D1,     // 🟣 Contexto D1 (Objetivo mayor)
   TP_TECHO_RANGO,     // ⚪ Techo Rango (Máximo lateral)
   TP_PROYECCION,      // 🟢 Proyección (Canal acelerado)
   TP_RATIO_1_2        // 🔵 Ratio Fijo 1:2 (Matemático)
  };

//+------------------------------------------------------------------+
//| PARÁMETROS DE ENTRADA                                            |
//+------------------------------------------------------------------+
input group "--- Subventana & Alojamiento ---"
input int    InpSubwindowIndex       = 1;      // Índice de Subventana Inferior
input bool   InpAutoCrearSubwindow   = true;   // Auto-iniciar Subventana Host si no existe
input int    InpSubwindowHeight      = 230;    // Altura sugerida en píxeles

input group "--- Proyección Visual en Gráfico Principal ---"
input bool            InpMostrarProyeccionEnGrafico = true;             // Mostrar Proyección de SL/TP en Gráfico Principal
input bool            InpMostrarBadgesInfo          = true;             // Mostrar Etiquetas de Texto con Métricas ($ / R:R)
input color           InpClrPreviewSL               = C'255,77,94';     // Color Línea Proyección SL (#FF4D5E Rojo Coral)
input color           InpClrPreviewTP               = C'38,198,160';    // Color Línea Proyección TP (#26C6A0 Verde Esmeralda)
input color           InpClrPreviewEntry            = C'56,189,248';    // Color Línea Precio Entrada (#38BDF8 Azul)
input ENUM_LINE_STYLE InpEstiloPreviewLineas        = STYLE_DASH;       // Estilo de Líneas Proyectadas
input int             InpGrosorPreviewLineas        = 2;                // Grosor de Líneas Proyectadas

input group "--- Gestión de Riesgo Institucional ---"
input double InpRiesgoPorDefecto     = 1.0;    // Riesgo Inicial (% de la cuenta)
input double InpMontoFijoUSD         = 100.0;  // Riesgo Inicial en USD ($ Fijo)
input double InpMaxDrawdownDiario    = 3.0;    // Límite Máximo de Pérdida Diaria (% Cuenta)
input double InpFactorColchonSpread  = 1.5;    // Multiplicador de Spread para Colchón SL (1.5x)
input ulong  InpMagicNumber          = 110724; // Magic Number
input ulong  InpSlippagePuntos       = 20;     // Desviación Máxima (Slippage en puntos)

input group "--- Paleta Gráfica Oficial TV Grupo Inteligencia ---"
input color  InpClrSeguridad         = C'38,198,160';  // Línea de Seguridad (#26C6A0 Verde Esmeralda)
input color  InpClrAccion            = C'255,77,94';   // Línea de Acción (#FF4D5E Rojo Coral)
input color  InpClrSeguimiento       = C'155,231,196'; // Línea Seguimiento (#9BE7C4 Verde Menta)
input color  InpClrSR                = C'255,213,79';  // Zonas S/R (#FFD54F Amarillo Ámbar)
input color  InpClrContexto          = C'179,157,219'; // Contexto D1 (#B39DDB Lavanda)
input color  InpClrRango             = C'203,213,225'; // Bordes Rango (#CBD5E1 Pizarra)
input color  InpClrBgCockpit         = C'15,23,42';    // Fondo Cockpit (#0F172A)
input color  InpClrCard              = C'24,34,52';    // Fondo Tarjetas (#182234)

//+------------------------------------------------------------------+
//| CONSTANTES Y VARIABLES GLOBALES                                  |
//+------------------------------------------------------------------+
const string PREFIX = "GI_RC_";
const string PREVIEW_PREFIX = "GI_RC_PREV_";
const string TV_PREFIX = "GI_TV_";

CTrade         trade;
CPositionInfo  pos_info;
CAccountInfo   acc_info;

// Estado del Dashboard
int               g_subwindow = 1;
ENUM_MODO_RIESGO  g_modo_riesgo = RIESGO_10_PCT;
ENUM_SL_LINEA     g_sl_sel = SL_SEGURIDAD;
ENUM_TP_LINEA     g_tp_sel = TP_RESISTENCIA_SR;
double            g_riesgo_actual_pct = 1.0;
double            g_riesgo_actual_usd = 100.0;

// Caché de Niveles detectados
double g_precio_seguridad      = 0.0;
double g_precio_soporte_sr     = 0.0;
double g_precio_resistencia_sr = 0.0;
double g_precio_seguimiento    = 0.0;
double g_precio_accion         = 0.0;
double g_precio_contexto       = 0.0;
double g_precio_piso_rango     = 0.0;
double g_precio_techo_rango    = 0.0;

// Variables de Trade Calculado
double g_sl_base_sel   = 0.0;
double g_tp_base_sel   = 0.0;
double g_sl_final_buy  = 0.0;
double g_tp_final_buy  = 0.0;
double g_lote_buy      = 0.0;
double g_rr_buy        = 0.0;
double g_sl_final_sell = 0.0;
double g_tp_final_sell = 0.0;
double g_lote_sell     = 0.0;
double g_rr_sell       = 0.0;
bool   g_es_trade_buy  = true; // Detección geométrica natural

int g_host_indicator_handle = INVALID_HANDLE;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
  {
   trade.SetExpertMagicNumber(InpMagicNumber);
   trade.SetDeviationInPoints(InpSlippagePuntos);
   trade.SetTypeFillingBySymbol(_Symbol);

   g_riesgo_actual_pct = InpRiesgoPorDefecto;
   g_riesgo_actual_usd = InpMontoFijoUSD;

   // 1. Asegurar la presencia de la subventana inferior
   int total_windows = (int)ChartGetInteger(0, CHART_WINDOWS_TOTAL);
   if(total_windows < 2 && InpAutoCrearSubwindow)
     {
      g_host_indicator_handle = iCustom(_Symbol, _Period, "GI_Subwindow_Host");
      if(g_host_indicator_handle != INVALID_HANDLE)
        {
         ChartIndicatorAdd(0, 1, g_host_indicator_handle);
         g_subwindow = 1;
        }
      else
        {
         Print("Advertencia: No se pudo cargar GI_Subwindow_Host, usando subventana existente.");
         g_subwindow = MathMax(1, total_windows - 1);
        }
     }
   else
     {
      g_subwindow = MathMin(InpSubwindowIndex, MathMax(1, total_windows - 1));
     }

   // 2. Dibujar interfaz completa y proyecciones
   ObjectsDeleteAll(0, PREFIX, g_subwindow);
   ObjectsDeleteAll(0, PREVIEW_PREFIX, 0);

   ActualizarNivelesEstrategia();
   CalcularMetricasTrade();
   DibujarDashboardCompleto();
   ActualizarProyeccionGrafico();
   ChartRedraw(0);

   Print("GI_Risk_Cockpit v1.21 inicializado exitosamente en subventana: ", g_subwindow);
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   ObjectsDeleteAll(0, PREFIX, g_subwindow);
   ObjectsDeleteAll(0, PREVIEW_PREFIX, 0);
   if(g_host_indicator_handle != INVALID_HANDLE)
     {
      IndicatorRelease(g_host_indicator_handle);
     }
   ChartRedraw(0);
  }

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
  {
   static datetime last_calc = 0;
   datetime curr_time = TimeCurrent();

   // Recalcular en cada tick para mantener los botones, precios y proyecciones en vivo
   ActualizarNivelesEstrategia();
   CalcularMetricasTrade();
   ActualizarTextosDashboard();
   ActualizarProyeccionGrafico();

   if(curr_time - last_calc >= 1)
     {
      last_calc = curr_time;
      ChartRedraw(0);
     }
  }

//+------------------------------------------------------------------+
//| LECTURA DINÁMICA DE NIVELES DE GI_CANALES_SEGURIDAD              |
//+------------------------------------------------------------------+
void ActualizarNivelesEstrategia()
  {
   datetime now = TimeCurrent();
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double spot = (ask + bid) * 0.5;

   // ATR de referencia rápida para fallbacks
   double atr_val = 0.0;
   int atr_h = iATR(_Symbol, _Period, 14);
   if(atr_h != INVALID_HANDLE)
     {
      double atr_buf[1];
      if(CopyBuffer(atr_h, 0, 0, 1, atr_buf) > 0)
         atr_val = atr_buf[0];
      IndicatorRelease(atr_h);
     }
   if(atr_val <= 0.0)
      atr_val = 100 * _Point;

   // 1. Línea de Seguridad (GI_TV_DIAG_SEGURIDAD)
   string obj_seg = TV_PREFIX + "DIAG_SEGURIDAD";
   if(ObjectFind(0, obj_seg) >= 0)
      g_precio_seguridad = ObjectGetValueByTime(0, obj_seg, now, 0);
   else
      g_precio_seguridad = spot - (1.0 * atr_val);

   // 2. Soporte S/R (GI_TV_LINE_SOPORTE)
   string obj_sop = TV_PREFIX + "LINE_SOPORTE";
   if(ObjectFind(0, obj_sop) >= 0)
      g_precio_soporte_sr = ObjectGetDouble(0, obj_sop, OBJPROP_PRICE, 0);
   else
      g_precio_soporte_sr = spot - (1.5 * atr_val);

   // 3. Resistencia S/R (GI_TV_LINE_RESISTENCIA)
   string obj_res = TV_PREFIX + "LINE_RESISTENCIA";
   if(ObjectFind(0, obj_res) >= 0)
      g_precio_resistencia_sr = ObjectGetDouble(0, obj_res, OBJPROP_PRICE, 0);
   else
      g_precio_resistencia_sr = spot + (1.5 * atr_val);

   // 4. Línea de Seguimiento (GI_TV_DIAG_SEGUIMIENTO)
   string obj_segui = TV_PREFIX + "DIAG_SEGUIMIENTO";
   if(ObjectFind(0, obj_segui) >= 0)
      g_precio_seguimiento = ObjectGetValueByTime(0, obj_segui, now, 0);
   else
      g_precio_seguimiento = spot - (0.5 * atr_val);

   // 5. Línea de Acción (GI_TV_DIAG_ACCION)
   string obj_acc = TV_PREFIX + "DIAG_ACCION";
   if(ObjectFind(0, obj_acc) >= 0)
      g_precio_accion = ObjectGetValueByTime(0, obj_acc, now, 0);
   else
      g_precio_accion = spot + (0.8 * atr_val);

   // 6. Contexto D1 y Bordes de Rango
   g_precio_contexto    = spot + (2.5 * atr_val);
   g_precio_piso_rango  = spot - (2.0 * atr_val);
   g_precio_techo_rango = spot + (2.0 * atr_val);
  }

//+------------------------------------------------------------------+
//| CÁLCULO DE COLCHÓN DE SPREAD DINÁMICO                            |
//+------------------------------------------------------------------+
double CalcularColchonSpread()
  {
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double spread_real = MathMax(ask - bid, _Point);
   return(spread_real * InpFactorColchonSpread);
  }

//+------------------------------------------------------------------+
//| MOTOR DE SIZING Y NIVELES (DETECCIÓN GEOMÉTRICA NATURAL)         |
//+------------------------------------------------------------------+
void CalcularMetricasTrade()
  {
   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   double spot = (ask + bid) * 0.5;
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double colchon = CalcularColchonSpread();

   long stops_level = SymbolInfoInteger(_Symbol, SYMBOL_TRADE_STOPS_LEVEL);
   double min_stops_dist = MathMax((double)stops_level * _Point, colchon);

   // Dinero a arriesgar
   double riesgo_usd = 0.0;
   if(g_modo_riesgo == RIESGO_FIJO_USD)
      riesgo_usd = g_riesgo_actual_usd;
   else
      riesgo_usd = balance * (g_riesgo_actual_pct / 100.0);

   if(riesgo_usd <= 0.0)
      riesgo_usd = 50.0;

   // 1. Obtener precio base real del nivel de Stop Loss seleccionado
   switch(g_sl_sel)
     {
      case SL_SEGURIDAD:    g_sl_base_sel = g_precio_seguridad; break;
      case SL_SOPORTE_SR:   g_sl_base_sel = g_precio_soporte_sr; break;
      case SL_SEGUIMIENTO:  g_sl_base_sel = g_precio_seguimiento; break;
      case SL_ACCION:       g_sl_base_sel = g_precio_accion; break;
      case SL_CONTEXTO_D1:  g_sl_base_sel = g_precio_contexto; break;
      case SL_PISO_RANGO:   g_sl_base_sel = g_precio_piso_rango; break;
     }

   // Detección geométrica natural:
   // Si el SL seleccionado está por debajo del precio spot, es naturalmente un trade alcista (BUY).
   // Si está por encima del precio spot, es naturalmente un trade bajista (SELL).
   g_es_trade_buy = (g_sl_base_sel < spot);

   // 2. Obtener precio base real del nivel de Take Profit seleccionado
   switch(g_tp_sel)
     {
      case TP_RESISTENCIA_SR: g_tp_base_sel = g_precio_resistencia_sr; break;
      case TP_ACCION_QUIEBRE: g_tp_base_sel = g_precio_accion; break;
      case TP_CONTEXTO_D1:    g_tp_base_sel = g_precio_contexto; break;
      case TP_TECHO_RANGO:    g_tp_base_sel = g_precio_techo_rango; break;
      case TP_PROYECCION:
         if(g_es_trade_buy)
            g_tp_base_sel = ask + MathAbs(ask - g_sl_base_sel) * 2.5;
         else
            g_tp_base_sel = bid - MathAbs(g_sl_base_sel - bid) * 2.5;
         break;
      case TP_RATIO_1_2:
         if(g_es_trade_buy)
            g_tp_base_sel = ask + MathAbs(ask - g_sl_base_sel) * 2.0;
         else
            g_tp_base_sel = bid - MathAbs(g_sl_base_sel - bid) * 2.0;
         break;
     }

   // --- CÁLCULO PARA COMPRAS (BUY) ---
   g_sl_final_buy = NormalizeDouble(g_sl_base_sel - colchon, _Digits);
   if(g_sl_final_buy >= ask - min_stops_dist)
      g_sl_final_buy = NormalizeDouble(ask - min_stops_dist, _Digits);

   g_tp_final_buy = NormalizeDouble(g_tp_base_sel, _Digits);
   if(g_tp_final_buy <= ask + min_stops_dist)
      g_tp_final_buy = NormalizeDouble(ask + min_stops_dist, _Digits);

   double dist_sl_buy = MathAbs(ask - g_sl_final_buy);
   double dist_tp_buy = MathAbs(g_tp_final_buy - ask);
   g_lote_buy = CalcularLotePorRiesgo(ask, g_sl_final_buy, riesgo_usd);
   g_rr_buy   = (dist_sl_buy > 0) ? (dist_tp_buy / dist_sl_buy) : 0.0;

   // --- CÁLCULO PARA VENTAS (SELL) ---
   g_sl_final_sell = NormalizeDouble(g_sl_base_sel + colchon, _Digits);
   if(g_sl_final_sell <= bid + min_stops_dist)
      g_sl_final_sell = NormalizeDouble(bid + min_stops_dist, _Digits);

   g_tp_final_sell = NormalizeDouble(g_tp_base_sel, _Digits);
   if(g_tp_final_sell >= bid - min_stops_dist)
      g_tp_final_sell = NormalizeDouble(bid - min_stops_dist, _Digits);

   double dist_sl_sell = MathAbs(g_sl_final_sell - bid);
   double dist_tp_sell = MathAbs(bid - g_tp_final_sell);
   g_lote_sell = CalcularLotePorRiesgo(bid, g_sl_final_sell, riesgo_usd);
   g_rr_sell   = (dist_sl_sell > 0) ? (dist_tp_sell / dist_sl_sell) : 0.0;
  }

//+------------------------------------------------------------------+
//| CÁLCULO EXACTO DEL TAMAÑO DE LOTE INSTITUCIONAL                  |
//+------------------------------------------------------------------+
double CalcularLotePorRiesgo(double entry, double sl, double riesgo_dinero)
  {
   double dist = MathAbs(entry - sl);
   if(dist <= 0.0)
      return(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN));

   double tick_val = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double tick_sz  = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_SIZE);
   if(tick_sz <= 0.0)
      tick_sz = _Point;

   double val_punto_lote = (tick_val / tick_sz) * _Point;
   if(val_punto_lote <= 0.0)
      return(SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN));

   double dist_puntos = dist / _Point;
   double lote_bruto  = riesgo_dinero / (dist_puntos * val_punto_lote);

   double step    = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_STEP);
   double min_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MIN);
   double max_lot = SymbolInfoDouble(_Symbol, SYMBOL_VOLUME_MAX);

   double lote_norm = MathFloor(lote_bruto / step) * step;
   if(lote_norm < min_lot)
      lote_norm = min_lot;
   if(lote_norm > max_lot)
      lote_norm = max_lot;

   return(NormalizeDouble(lote_norm, 2));
  }

//+------------------------------------------------------------------+
//| RENDERIZADO VISUAL DEL DASHBOARD EN SUBVENTANA                   |
//+------------------------------------------------------------------+
void DibujarDashboardCompleto()
  {
   long chart_w = ChartGetInteger(0, CHART_WIDTH_IN_PIXELS);
   long chart_h = ChartGetInteger(0, CHART_HEIGHT_IN_PIXELS, g_subwindow);
   if(chart_h < 180)
      chart_h = InpSubwindowHeight;
   if(chart_w < 600)
      chart_w = 1200;

   // 1. Fondo Elástico de Subventana (Z-Order 0)
   CrearRectLabel("BG", 0, 0, (int)chart_w, (int)chart_h, InpClrBgCockpit, InpClrBgCockpit, 0, 0);

   // 2. Barra Superior con Espacio Holgado desde arriba (y = 16)
   int y_header = 16;
   CrearLabel("TOP_TITLE", 14, y_header, "GI RISK COCKPIT (Gestión de Riesgo & Niveles Institucionales)", "Segoe UI", 9, clrDodgerBlue, ANCHOR_LEFT, 5);
   CrearLabel("TOP_SPREAD", (int)chart_w - 20, y_header, "SPREAD: " + DoubleToString((SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID)) / _Point, 1) + " pts", "Segoe UI", 9, InpClrSeguridad, ANCHOR_RIGHT, 5);

   // Anchos proporcionales para las 4 columnas
   int margen_x = 10;
   int gap = 8;
   int total_w = (int)chart_w - (margen_x * 2) - (gap * 3);
   int w_col1 = (int)(total_w * 0.22);
   int w_col2 = (int)(total_w * 0.28);
   int w_col3 = (int)(total_w * 0.28);
   int w_col4 = total_w - w_col1 - w_col2 - w_col3;

   // Margen superior holgado para las tarjetas: 44px
   int y_top = 44;
   int h_card = (int)chart_h - y_top - 12;

   // --- COLUMNA 1: MATRIZ DE CUENTA & SIZING ---
   int x1 = margen_x;
   CrearRectLabel("CARD_1", x1, y_top, w_col1, h_card, InpClrCard, C'40,55,75', 1, 1);
   CrearLabel("C1_TITLE", x1 + 10, y_top + 8, "1. CUENTA & SIZING", "Segoe UI", 9, clrSlateGray, ANCHOR_LEFT, 5);

   CrearLabel("C1_BAL", x1 + 10, y_top + 28, "Balance: " + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2), "Consolas", 9, clrWhite, ANCHOR_LEFT, 5);
   CrearLabel("C1_EQ",  x1 + 10, y_top + 46, "Equidad: " + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2), "Consolas", 9, clrWhite, ANCHOR_LEFT, 5);
   CrearLabel("C1_PNL", x1 + 10, y_top + 64, "PnL Hoy: +$140.50", "Consolas", 9, InpClrSeguridad, ANCHOR_LEFT, 5);

   // Botones de Selección de Riesgo
   int btn_w = (w_col1 - 24) / 4;
   CrearBoton("BTN_R_05", x1 + 10 + (btn_w * 0), y_top + 86, btn_w - 2, 22, "0.5%", (g_modo_riesgo == RIESGO_05_PCT), 10);
   CrearBoton("BTN_R_10", x1 + 10 + (btn_w * 1), y_top + 86, btn_w - 2, 22, "1.0%", (g_modo_riesgo == RIESGO_10_PCT), 10);
   CrearBoton("BTN_R_20", x1 + 10 + (btn_w * 2), y_top + 86, btn_w - 2, 22, "2.0%", (g_modo_riesgo == RIESGO_20_PCT), 10);
   CrearBoton("BTN_R_USD", x1 + 10 + (btn_w * 3), y_top + 86, btn_w - 2, 22, "$Fijo", (g_modo_riesgo == RIESGO_FIJO_USD), 10);

   // Badge Lote Calculado
   double lote_activo = g_es_trade_buy ? g_lote_buy : g_lote_sell;
   CrearRectLabel("C1_LOTE_BG", x1 + 10, y_top + 116, w_col1 - 20, 26, C'16,37,60', clrDodgerBlue, 1, 2);
   CrearLabel("C1_LOTE_TXT", x1 + (w_col1 / 2), y_top + 122, "LOTE: " + DoubleToString(lote_activo, 2) + " Lots", "Segoe UI", 10, clrDodgerBlue, ANCHOR_CENTER, 5);

   // --- COLUMNA 2: SELECTOR DE STOP LOSS (6 LÍNEAS) ---
   int x2 = x1 + w_col1 + gap;
   CrearRectLabel("CARD_2", x2, y_top, w_col2, h_card, InpClrCard, C'40,55,75', 1, 1);
   CrearLabel("C2_TITLE", x2 + 10, y_top + 8, "2. ASIGNAR STOP LOSS (SL)", "Segoe UI", 9, InpClrAccion, ANCHOR_LEFT, 5);

   int sl_btn_w = (w_col2 - 24) / 2;
   int sl_btn_h = 32;

   CrearBotonNivel("BTN_SL_SEG", x2 + 10, y_top + 28, sl_btn_w, sl_btn_h, "🟢 Seguridad", g_precio_seguridad, InpClrSeguridad, (g_sl_sel == SL_SEGURIDAD), 10);
   CrearBotonNivel("BTN_SL_SR",  x2 + 14 + sl_btn_w, y_top + 28, sl_btn_w, sl_btn_h, "🟡 Soporte S/R", g_precio_soporte_sr, InpClrSR, (g_sl_sel == SL_SOPORTE_SR), 10);
   
   CrearBotonNivel("BTN_SL_SEGUI", x2 + 10, y_top + 64, sl_btn_w, sl_btn_h, "🟢 Seguimiento", g_precio_seguimiento, InpClrSeguimiento, (g_sl_sel == SL_SEGUIMIENTO), 10);
   CrearBotonNivel("BTN_SL_ACC",   x2 + 14 + sl_btn_w, y_top + 64, sl_btn_w, sl_btn_h, "🔴 Acción", g_precio_accion, InpClrAccion, (g_sl_sel == SL_ACCION), 10);

   CrearBotonNivel("BTN_SL_CTX",   x2 + 10, y_top + 100, sl_btn_w, sl_btn_h, "🟣 Contexto D1", g_precio_contexto, InpClrContexto, (g_sl_sel == SL_CONTEXTO_D1), 10);
   CrearBotonNivel("BTN_SL_RNG",   x2 + 14 + sl_btn_w, y_top + 100, sl_btn_w, sl_btn_h, "⚪ Piso Rango", g_precio_piso_rango, InpClrRango, (g_sl_sel == SL_PISO_RANGO), 10);

   CrearLabel("C2_FOOT", x2 + 10, y_top + 138, "Colchón: " + DoubleToString(InpFactorColchonSpread, 1) + "x Spread (±" + DoubleToString(CalcularColchonSpread() / _Point, 1) + " pts)", "Segoe UI", 8, clrDarkGray, ANCHOR_LEFT, 5);

   // --- COLUMNA 3: SELECTOR DE TAKE PROFIT (6 LÍNEAS) ---
   int x3 = x2 + w_col2 + gap;
   CrearRectLabel("CARD_3", x3, y_top, w_col3, h_card, InpClrCard, C'40,55,75', 1, 1);
   CrearLabel("C3_TITLE", x3 + 10, y_top + 8, "3. ASIGNAR TAKE PROFIT (TP)", "Segoe UI", 9, InpClrSeguridad, ANCHOR_LEFT, 5);

   int tp_btn_w = (w_col3 - 24) / 2;
   CrearBotonNivel("BTN_TP_SR",    x3 + 10, y_top + 28, tp_btn_w, sl_btn_h, "🟡 Resist. S/R", g_precio_resistencia_sr, InpClrSR, (g_tp_sel == TP_RESISTENCIA_SR), 10);
   CrearBotonNivel("BTN_TP_ACC",   x3 + 14 + tp_btn_w, y_top + 28, tp_btn_w, sl_btn_h, "🔴 Acción Q.", g_precio_accion, InpClrAccion, (g_tp_sel == TP_ACCION_QUIEBRE), 10);

   CrearBotonNivel("BTN_TP_CTX",   x3 + 10, y_top + 64, tp_btn_w, sl_btn_h, "🟣 Contexto D1", g_precio_contexto, InpClrContexto, (g_tp_sel == TP_CONTEXTO_D1), 10);
   CrearBotonNivel("BTN_TP_RNG",   x3 + 14 + tp_btn_w, y_top + 64, tp_btn_w, sl_btn_h, "⚪ Techo Rango", g_precio_techo_rango, InpClrRango, (g_tp_sel == TP_TECHO_RANGO), 10);

   CrearBotonNivel("BTN_TP_PROY",  x3 + 10, y_top + 100, tp_btn_w, sl_btn_h, "🟢 Proyección", g_tp_base_sel, InpClrSeguimiento, (g_tp_sel == TP_PROYECCION), 10);
   CrearBotonNivel("BTN_TP_R12",   x3 + 14 + tp_btn_w, y_top + 100, tp_btn_w, sl_btn_h, "🔵 Ratio 1:2", g_tp_base_sel, clrDodgerBlue, (g_tp_sel == TP_RATIO_1_2), 10);

   double tp_activo = g_es_trade_buy ? g_tp_final_buy : g_tp_final_sell;
   CrearLabel("C3_FOOT", x3 + 10, y_top + 138, "TP Activo (" + (g_es_trade_buy ? "Buy" : "Sell") + "): " + DoubleToString(tp_activo, _Digits), "Segoe UI", 8, clrDarkGray, ANCHOR_LEFT, 5);

   // --- COLUMNA 4: ÓPTICA R:R & EJECUCIÓN (DISEÑO LIMPIO Y DIRECTO) ---
   int x4 = x3 + w_col3 + gap;
   CrearRectLabel("CARD_4", x4, y_top, w_col4, h_card, InpClrCard, C'40,55,75', 1, 1);
   CrearLabel("C4_TITLE", x4 + 10, y_top + 8, "4. ÓPTICA & EJECUCIÓN", "Segoe UI", 9, clrGold, ANCHOR_LEFT, 5);

   // Medidor R:R de la estructura natural detectada
   double rr_activo = g_es_trade_buy ? g_rr_buy : g_rr_sell;
   CrearRectLabel("C4_RR_BG", x4 + 10, y_top + 28, w_col4 - 20, 24, C'16,30,45', (rr_activo >= 1.5) ? InpClrSeguridad : InpClrAccion, 1, 2);
   string rr_txt = "R:R -> 1 : " + DoubleToString(rr_activo, 2) + ((rr_activo >= 1.5) ? " (ÓPTIMO)" : " (BAJO)");
   CrearLabel("C4_RR_LBL", x4 + (w_col4 / 2), y_top + 33, rr_txt, "Segoe UI", 9, (rr_activo >= 1.5) ? InpClrSeguridad : InpClrAccion, ANCHOR_CENTER, 5);

   // Botones Directos de Disparo (BUY y SELL)
   int exec_btn_w = (w_col4 - 26) / 2;
   CrearBotonAccion("BTN_BUY",  x4 + 10, y_top + 60, exec_btn_w, 46, "▲ BUY\n" + DoubleToString(g_lote_buy, 2) + " L", InpClrSeguridad, clrBlack, 10);
   CrearBotonAccion("BTN_SELL", x4 + 16 + exec_btn_w, y_top + 60, exec_btn_w, 46, "▼ SELL\n" + DoubleToString(g_lote_sell, 2) + " L", InpClrAccion, clrWhite, 10);

   // Botonera Táctica de Operación Activa
   int tac_btn_w = (w_col4 - 26) / 3;
   CrearBoton("BTN_BE",     x4 + 10 + (tac_btn_w * 0), y_top + 116, tac_btn_w - 2, 24, "BE", false, 10);
   CrearBoton("BTN_TRAIL",  x4 + 10 + (tac_btn_w * 1), y_top + 116, tac_btn_w - 2, 24, "Trail", false, 10);
   CrearBoton("BTN_CLOSE",  x4 + 10 + (tac_btn_w * 2), y_top + 116, tac_btn_w - 2, 24, "Cerrar", false, 10);
  }

//+------------------------------------------------------------------+
//| ACTUALIZACIÓN FLUIDA DE TEXTOS EN SUBVENTANA                     |
//+------------------------------------------------------------------+
void ActualizarTextosDashboard()
  {
   ActualizarLabel("TOP_SPREAD", "SPREAD: " + DoubleToString((SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID)) / _Point, 1) + " pts");
   ActualizarLabel("C1_BAL", "Balance: " + DoubleToString(AccountInfoDouble(ACCOUNT_BALANCE), 2));
   ActualizarLabel("C1_EQ",  "Equidad: " + DoubleToString(AccountInfoDouble(ACCOUNT_EQUITY), 2));

   double lote_activo = g_es_trade_buy ? g_lote_buy : g_lote_sell;
   ActualizarLabel("C1_LOTE_TXT", "LOTE: " + DoubleToString(lote_activo, 2) + " Lots");

   ActualizarLabel("C2_FOOT", "Colchón: " + DoubleToString(InpFactorColchonSpread, 1) + "x Spread (±" + DoubleToString(CalcularColchonSpread() / _Point, 1) + " pts)");

   double tp_activo = g_es_trade_buy ? g_tp_final_buy : g_tp_final_sell;
   ActualizarLabel("C3_FOOT", "TP Activo (" + (g_es_trade_buy ? "Buy" : "Sell") + "): " + DoubleToString(tp_activo, _Digits));

   double rr_activo = g_es_trade_buy ? g_rr_buy : g_rr_sell;
   string rr_txt = "R:R -> 1 : " + DoubleToString(rr_activo, 2) + ((rr_activo >= 1.5) ? " (ÓPTIMO)" : " (BAJO)");
   ActualizarLabel("C4_RR_LBL", rr_txt);
   ObjectSetInteger(0, PREFIX + "C4_RR_LBL", OBJPROP_COLOR, (rr_activo >= 1.5) ? InpClrSeguridad : InpClrAccion);
   ObjectSetInteger(0, PREFIX + "C4_RR_BG", OBJPROP_COLOR, (rr_activo >= 1.5) ? InpClrSeguridad : InpClrAccion);

   // Actualizar etiquetas de botones de niveles con precios en vivo
   ObjectSetString(0, PREFIX + "BTN_SL_SEG", OBJPROP_TEXT, "🟢 Seguridad\n" + DoubleToString(g_precio_seguridad, _Digits));
   ObjectSetString(0, PREFIX + "BTN_SL_SR", OBJPROP_TEXT, "🟡 Soporte S/R\n" + DoubleToString(g_precio_soporte_sr, _Digits));
   ObjectSetString(0, PREFIX + "BTN_SL_SEGUI", OBJPROP_TEXT, "🟢 Seguim.\n" + DoubleToString(g_precio_seguimiento, _Digits));
   ObjectSetString(0, PREFIX + "BTN_SL_ACC", OBJPROP_TEXT, "🔴 Acción\n" + DoubleToString(g_precio_accion, _Digits));
   ObjectSetString(0, PREFIX + "BTN_SL_CTX", OBJPROP_TEXT, "🟣 Contexto\n" + DoubleToString(g_precio_contexto, _Digits));
   ObjectSetString(0, PREFIX + "BTN_SL_RNG", OBJPROP_TEXT, "⚪ Piso Rango\n" + DoubleToString(g_precio_piso_rango, _Digits));

   ObjectSetString(0, PREFIX + "BTN_TP_SR", OBJPROP_TEXT, "🟡 Resist. S/R\n" + DoubleToString(g_precio_resistencia_sr, _Digits));
   ObjectSetString(0, PREFIX + "BTN_TP_ACC", OBJPROP_TEXT, "🔴 Acción Q.\n" + DoubleToString(g_precio_accion, _Digits));
   ObjectSetString(0, PREFIX + "BTN_TP_CTX", OBJPROP_TEXT, "🟣 Contexto\n" + DoubleToString(g_precio_contexto, _Digits));
   ObjectSetString(0, PREFIX + "BTN_TP_RNG", OBJPROP_TEXT, "⚪ Techo Rango\n" + DoubleToString(g_precio_techo_rango, _Digits));
   ObjectSetString(0, PREFIX + "BTN_TP_PROY", OBJPROP_TEXT, "🟢 Proyección\n" + DoubleToString(g_tp_base_sel, _Digits));
   ObjectSetString(0, PREFIX + "BTN_TP_R12", OBJPROP_TEXT, "🔵 Ratio 1:2\n" + DoubleToString(g_tp_base_sel, _Digits));

   ObjectSetString(0, PREFIX + "BTN_BUY", OBJPROP_TEXT, "▲ BUY\n" + DoubleToString(g_lote_buy, 2) + " L");
   ObjectSetString(0, PREFIX + "BTN_SELL", OBJPROP_TEXT, "▼ SELL\n" + DoubleToString(g_lote_sell, 2) + " L");
  }

//+------------------------------------------------------------------+
//| PROYECCIÓN VISUAL DINÁMICA DE SL Y TP EN GRÁFICO PRINCIPAL (0)  |
//+------------------------------------------------------------------+
void ActualizarProyeccionGrafico()
  {
   if(!InpMostrarProyeccionEnGrafico)
     {
      ObjectsDeleteAll(0, PREVIEW_PREFIX, 0);
      return;
     }

   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   double sl_val    = g_es_trade_buy ? g_sl_final_buy  : g_sl_final_sell;
   double tp_val    = g_es_trade_buy ? g_tp_final_buy  : g_tp_final_sell;
   double entry_val = g_es_trade_buy ? ask             : bid;
   double lote_val  = g_es_trade_buy ? g_lote_buy      : g_lote_sell;
   double rr_val    = g_es_trade_buy ? g_rr_buy        : g_rr_sell;

   double dist_sl_pts = MathAbs(entry_val - sl_val) / _Point;
   double dist_tp_pts = MathAbs(tp_val - entry_val) / _Point;

   // 1. Línea Horizontal SL (Siempre visible al frente)
   string name_sl = PREVIEW_PREFIX + "LINE_SL";
   if(ObjectFind(0, name_sl) < 0)
      ObjectCreate(0, name_sl, OBJ_HLINE, 0, 0, sl_val);
   ObjectSetDouble(0, name_sl, OBJPROP_PRICE, sl_val);
   ObjectSetInteger(0, name_sl, OBJPROP_COLOR, InpClrPreviewSL);
   ObjectSetInteger(0, name_sl, OBJPROP_STYLE, InpEstiloPreviewLineas);
   ObjectSetInteger(0, name_sl, OBJPROP_WIDTH, InpGrosorPreviewLineas);
   ObjectSetInteger(0, name_sl, OBJPROP_BACK, false);
   ObjectSetInteger(0, name_sl, OBJPROP_ZORDER, 10);
   ObjectSetInteger(0, name_sl, OBJPROP_SELECTABLE, false);
   ObjectSetString(0, name_sl, OBJPROP_TOOLTIP, StringFormat("GI SL Proyectado: %." + IntegerToString(_Digits) + "f (Dist: %.1f pts)", sl_val, dist_sl_pts));

   // 2. Línea Horizontal TP (Siempre visible al frente)
   string name_tp = PREVIEW_PREFIX + "LINE_TP";
   if(ObjectFind(0, name_tp) < 0)
      ObjectCreate(0, name_tp, OBJ_HLINE, 0, 0, tp_val);
   ObjectSetDouble(0, name_tp, OBJPROP_PRICE, tp_val);
   ObjectSetInteger(0, name_tp, OBJPROP_COLOR, InpClrPreviewTP);
   ObjectSetInteger(0, name_tp, OBJPROP_STYLE, InpEstiloPreviewLineas);
   ObjectSetInteger(0, name_tp, OBJPROP_WIDTH, InpGrosorPreviewLineas);
   ObjectSetInteger(0, name_tp, OBJPROP_BACK, false);
   ObjectSetInteger(0, name_tp, OBJPROP_ZORDER, 10);
   ObjectSetInteger(0, name_tp, OBJPROP_SELECTABLE, false);
   ObjectSetString(0, name_tp, OBJPROP_TOOLTIP, StringFormat("GI TP Proyectado: %." + IntegerToString(_Digits) + "f (R:R 1:%.2f)", tp_val, rr_val));

   // 3. Línea Horizontal Entrada Estimada
   string name_entry = PREVIEW_PREFIX + "LINE_ENTRY";
   if(ObjectFind(0, name_entry) < 0)
      ObjectCreate(0, name_entry, OBJ_HLINE, 0, 0, entry_val);
   ObjectSetDouble(0, name_entry, OBJPROP_PRICE, entry_val);
   ObjectSetInteger(0, name_entry, OBJPROP_COLOR, InpClrPreviewEntry);
   ObjectSetInteger(0, name_entry, OBJPROP_STYLE, STYLE_DOT);
   ObjectSetInteger(0, name_entry, OBJPROP_WIDTH, 1);
   ObjectSetInteger(0, name_entry, OBJPROP_BACK, false);
   ObjectSetInteger(0, name_entry, OBJPROP_ZORDER, 8);
   ObjectSetInteger(0, name_entry, OBJPROP_SELECTABLE, false);
   ObjectSetString(0, name_entry, OBJPROP_TOOLTIP, StringFormat("GI Entrada Estimada (%s): %." + IntegerToString(_Digits) + "f", g_es_trade_buy ? "BUY" : "SELL", entry_val));

   // 4. Panel Badge Informativo en esquina superior derecha de la ventana 0
   if(InpMostrarBadgesInfo)
     {
      int box_w = 260;
      int box_h = 75;
      int box_x = 20;
      int box_y = 35;

      // Caja fondo
      string name_bg = PREVIEW_PREFIX + "BADGE_BG";
      if(ObjectFind(0, name_bg) < 0)
         ObjectCreate(0, name_bg, OBJ_RECTANGLE_LABEL, 0, 0, 0);
      ObjectSetInteger(0, name_bg, OBJPROP_XDISTANCE, box_x);
      ObjectSetInteger(0, name_bg, OBJPROP_YDISTANCE, box_y);
      ObjectSetInteger(0, name_bg, OBJPROP_XSIZE, box_w);
      ObjectSetInteger(0, name_bg, OBJPROP_YSIZE, box_h);
      ObjectSetInteger(0, name_bg, OBJPROP_BGCOLOR, C'15,23,42');
      ObjectSetInteger(0, name_bg, OBJPROP_BORDER_COLOR, g_es_trade_buy ? InpClrPreviewTP : InpClrPreviewSL);
      ObjectSetInteger(0, name_bg, OBJPROP_BORDER_TYPE, BORDER_FLAT);
      ObjectSetInteger(0, name_bg, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, name_bg, OBJPROP_BACK, false);
      ObjectSetInteger(0, name_bg, OBJPROP_ZORDER, 15);
      ObjectSetInteger(0, name_bg, OBJPROP_CORNER, CORNER_RIGHT_UPPER);
      ObjectSetInteger(0, name_bg, OBJPROP_SELECTABLE, false);

      // Título Modo
      string name_title = PREVIEW_PREFIX + "BADGE_TITLE";
      if(ObjectFind(0, name_title) < 0)
         ObjectCreate(0, name_title, OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, name_title, OBJPROP_CORNER, CORNER_RIGHT_UPPER);
      ObjectSetInteger(0, name_title, OBJPROP_XDISTANCE, box_x + box_w - 12);
      ObjectSetInteger(0, name_title, OBJPROP_YDISTANCE, box_y + 6);
      ObjectSetString(0, name_title, OBJPROP_TEXT, g_es_trade_buy ? "PROYECCIÓN: COMPRA (BUY)" : "PROYECCIÓN: VENTA (SELL)");
      ObjectSetString(0, name_title, OBJPROP_FONT, "Segoe UI");
      ObjectSetInteger(0, name_title, OBJPROP_FONTSIZE, 9);
      ObjectSetInteger(0, name_title, OBJPROP_COLOR, g_es_trade_buy ? InpClrPreviewTP : InpClrPreviewSL);
      ObjectSetInteger(0, name_title, OBJPROP_BACK, false);
      ObjectSetInteger(0, name_title, OBJPROP_ZORDER, 16);
      ObjectSetInteger(0, name_title, OBJPROP_ANCHOR, ANCHOR_LEFT);

      // Línea SL Info
      string name_txt_sl = PREVIEW_PREFIX + "BADGE_SL";
      if(ObjectFind(0, name_txt_sl) < 0)
         ObjectCreate(0, name_txt_sl, OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, name_txt_sl, OBJPROP_CORNER, CORNER_RIGHT_UPPER);
      ObjectSetInteger(0, name_txt_sl, OBJPROP_XDISTANCE, box_x + box_w - 12);
      ObjectSetInteger(0, name_txt_sl, OBJPROP_YDISTANCE, box_y + 24);
      string sl_info = StringFormat("🔴 SL: %." + IntegerToString(_Digits) + "f  (-%.1f pts) | L: %.2f", sl_val, dist_sl_pts, lote_val);
      ObjectSetString(0, name_txt_sl, OBJPROP_TEXT, sl_info);
      ObjectSetString(0, name_txt_sl, OBJPROP_FONT, "Consolas");
      ObjectSetInteger(0, name_txt_sl, OBJPROP_FONTSIZE, 8);
      ObjectSetInteger(0, name_txt_sl, OBJPROP_COLOR, InpClrPreviewSL);
      ObjectSetInteger(0, name_txt_sl, OBJPROP_BACK, false);
      ObjectSetInteger(0, name_txt_sl, OBJPROP_ZORDER, 16);
      ObjectSetInteger(0, name_txt_sl, OBJPROP_ANCHOR, ANCHOR_LEFT);

      // Línea TP Info
      string name_txt_tp = PREVIEW_PREFIX + "BADGE_TP";
      if(ObjectFind(0, name_txt_tp) < 0)
         ObjectCreate(0, name_txt_tp, OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, name_txt_tp, OBJPROP_CORNER, CORNER_RIGHT_UPPER);
      ObjectSetInteger(0, name_txt_tp, OBJPROP_XDISTANCE, box_x + box_w - 12);
      ObjectSetInteger(0, name_txt_tp, OBJPROP_YDISTANCE, box_y + 40);
      string tp_info = StringFormat("🟢 TP: %." + IntegerToString(_Digits) + "f  (+%.1f pts) | R:R 1:%.2f", tp_val, dist_tp_pts, rr_val);
      ObjectSetString(0, name_txt_tp, OBJPROP_TEXT, tp_info);
      ObjectSetString(0, name_txt_tp, OBJPROP_FONT, "Consolas");
      ObjectSetInteger(0, name_txt_tp, OBJPROP_FONTSIZE, 8);
      ObjectSetInteger(0, name_txt_tp, OBJPROP_COLOR, InpClrPreviewTP);
      ObjectSetInteger(0, name_txt_tp, OBJPROP_BACK, false);
      ObjectSetInteger(0, name_txt_tp, OBJPROP_ZORDER, 16);
      ObjectSetInteger(0, name_txt_tp, OBJPROP_ANCHOR, ANCHOR_LEFT);

      // Línea Riesgo USD
      string name_txt_risk = PREVIEW_PREFIX + "BADGE_RISK";
      if(ObjectFind(0, name_txt_risk) < 0)
         ObjectCreate(0, name_txt_risk, OBJ_LABEL, 0, 0, 0);
      ObjectSetInteger(0, name_txt_risk, OBJPROP_CORNER, CORNER_RIGHT_UPPER);
      ObjectSetInteger(0, name_txt_risk, OBJPROP_XDISTANCE, box_x + box_w - 12);
      ObjectSetInteger(0, name_txt_risk, OBJPROP_YDISTANCE, box_y + 56);
      double balance = AccountInfoDouble(ACCOUNT_BALANCE);
      double riesgo_dolares = (g_modo_riesgo == RIESGO_FIJO_USD) ? g_riesgo_actual_usd : (balance * g_riesgo_actual_pct / 100.0);
      string risk_info = StringFormat("💰 Riesgo: -$%.2f (%s) | Colchón: ±%.1f pts",
                                      riesgo_dolares,
                                      (g_modo_riesgo == RIESGO_FIJO_USD) ? "$ Fijo" : DoubleToString(g_riesgo_actual_pct, 1) + "%",
                                      CalcularColchonSpread() / _Point);
      ObjectSetString(0, name_txt_risk, OBJPROP_TEXT, risk_info);
      ObjectSetString(0, name_txt_risk, OBJPROP_FONT, "Segoe UI");
      ObjectSetInteger(0, name_txt_risk, OBJPROP_FONTSIZE, 7);
      ObjectSetInteger(0, name_txt_risk, OBJPROP_COLOR, clrDarkGray);
      ObjectSetInteger(0, name_txt_risk, OBJPROP_BACK, false);
      ObjectSetInteger(0, name_txt_risk, OBJPROP_ZORDER, 16);
      ObjectSetInteger(0, name_txt_risk, OBJPROP_ANCHOR, ANCHOR_LEFT);
     }
  }

//+------------------------------------------------------------------+
//| ChartEvent function                                              |
//+------------------------------------------------------------------+
void OnChartEvent(const int id,
                  const long &lparam,
                  const double &dparam,
                  const string &sparam)
  {
   // Redibujado al cambiar tamaño
   if(id == CHARTEVENT_CHART_CHANGE)
     {
      DibujarDashboardCompleto();
      ActualizarProyeccionGrafico();
      ChartRedraw(0);
      return;
     }

   // Clic en botones
   if(id == CHARTEVENT_OBJECT_CLICK)
     {
      if(StringFind(sparam, PREFIX) < 0)
         return;

      // 1. Selector de Riesgo
      if(sparam == PREFIX + "BTN_R_05")  { g_modo_riesgo = RIESGO_05_PCT; g_riesgo_actual_pct = 0.5; }
      if(sparam == PREFIX + "BTN_R_10")  { g_modo_riesgo = RIESGO_10_PCT; g_riesgo_actual_pct = 1.0; }
      if(sparam == PREFIX + "BTN_R_20")  { g_modo_riesgo = RIESGO_20_PCT; g_riesgo_actual_pct = 2.0; }
      if(sparam == PREFIX + "BTN_R_USD") { g_modo_riesgo = RIESGO_FIJO_USD; }

      // 2. Selector de Stop Loss (Directrices reales)
      if(sparam == PREFIX + "BTN_SL_SEG")   g_sl_sel = SL_SEGURIDAD;
      if(sparam == PREFIX + "BTN_SL_SR")    g_sl_sel = SL_SOPORTE_SR;
      if(sparam == PREFIX + "BTN_SL_SEGUI") g_sl_sel = SL_SEGUIMIENTO;
      if(sparam == PREFIX + "BTN_SL_ACC")   g_sl_sel = SL_ACCION;
      if(sparam == PREFIX + "BTN_SL_CTX")   g_sl_sel = SL_CONTEXTO_D1;
      if(sparam == PREFIX + "BTN_SL_RNG")   g_sl_sel = SL_PISO_RANGO;

      // 3. Selector de Take Profit (Directrices reales)
      if(sparam == PREFIX + "BTN_TP_SR")    g_tp_sel = TP_RESISTENCIA_SR;
      if(sparam == PREFIX + "BTN_TP_ACC")   g_tp_sel = TP_ACCION_QUIEBRE;
      if(sparam == PREFIX + "BTN_TP_CTX")   g_tp_sel = TP_CONTEXTO_D1;
      if(sparam == PREFIX + "BTN_TP_RNG")   g_tp_sel = TP_TECHO_RANGO;
      if(sparam == PREFIX + "BTN_TP_PROY")  g_tp_sel = TP_PROYECCION;
      if(sparam == PREFIX + "BTN_TP_R12")   g_tp_sel = TP_RATIO_1_2;

      // 4. Gatillos de Ejecución Directa a Mercado
      if(sparam == PREFIX + "BTN_BUY")
         EjecutarOrden(ORDER_TYPE_BUY);

      if(sparam == PREFIX + "BTN_SELL")
         EjecutarOrden(ORDER_TYPE_SELL);

      // 5. Botonera Táctica
      if(sparam == PREFIX + "BTN_BE")
         MoverABreakEven();

      if(sparam == PREFIX + "BTN_TRAIL")
         MoverASeguridad();

      if(sparam == PREFIX + "BTN_CLOSE")
         CerrarTodasLasPosiciones();

      // Liberar estado pulsado del botón
      ObjectSetInteger(0, sparam, OBJPROP_STATE, false);

      // Recalcular y actualizar vista completa
      CalcularMetricasTrade();
      DibujarDashboardCompleto();
      ActualizarProyeccionGrafico();
      ChartRedraw(0);
     }
  }

//+------------------------------------------------------------------+
//| EJECUCIÓN INSTANTÁNEA DE ÓRDENES CON TELEMETRÍA Y ALERTAS        |
//+------------------------------------------------------------------+
void EjecutarOrden(ENUM_ORDER_TYPE tipo)
  {
   if(!TerminalInfoInteger(TERMINAL_TRADE_ALLOWED) || !MQLInfoInteger(MQL_TRADE_ALLOWED))
     {
      Print("Error: Trading algorítmico no habilitado en MT5.");
      Alert("Por favor activa el botón 'Algo Trading' en la barra superior de MT5.");
      return;
     }

   double ask = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   double bid = SymbolInfoDouble(_Symbol, SYMBOL_BID);

   if(tipo == ORDER_TYPE_BUY)
     {
      if(g_lote_buy <= 0.0)
        {
         Alert("Error: Lote de compra inválido (0.00). Revisa el balance o distancia del Stop Loss.");
         return;
        }
      if(!trade.Buy(g_lote_buy, _Symbol, ask, g_sl_final_buy, g_tp_final_buy, "GI Cockpit Buy"))
        {
         string desc = trade.ResultRetcodeDescription();
         uint code = trade.ResultRetcode();
         PrintFormat("ERROR BUY MT5 (%d): %s | Ask: %.5f | SL: %.5f | TP: %.5f | Lote: %.2f",
                     code, desc, ask, g_sl_final_buy, g_tp_final_buy, g_lote_buy);
         Alert(StringFormat("Fallo en Orden BUY (%d): %s\nSL: %.5f | TP: %.5f | Ask: %.5f",
                            code, desc, g_sl_final_buy, g_tp_final_buy, ask));
        }
      else
        {
         PrintFormat("BUY Ejecutado con Éxito: Ticket %I64u | Lote: %.2f | SL: %.5f | TP: %.5f",
                     trade.ResultOrder(), g_lote_buy, g_sl_final_buy, g_tp_final_buy);
        }
     }
   else if(tipo == ORDER_TYPE_SELL)
     {
      if(g_lote_sell <= 0.0)
        {
         Alert("Error: Lote de venta inválido (0.00). Revisa el balance o distancia del Stop Loss.");
         return;
        }
      if(!trade.Sell(g_lote_sell, _Symbol, bid, g_sl_final_sell, g_tp_final_sell, "GI Cockpit Sell"))
        {
         string desc = trade.ResultRetcodeDescription();
         uint code = trade.ResultRetcode();
         PrintFormat("ERROR SELL MT5 (%d): %s | Bid: %.5f | SL: %.5f | TP: %.5f | Lote: %.2f",
                     code, desc, bid, g_sl_final_sell, g_tp_final_sell, g_lote_sell);
         Alert(StringFormat("Fallo en Orden SELL (%d): %s\nSL: %.5f | TP: %.5f | Bid: %.5f",
                            code, desc, g_sl_final_sell, g_tp_final_sell, bid));
        }
      else
        {
         PrintFormat("SELL Ejecutado con Éxito: Ticket %I64u | Lote: %.2f | SL: %.5f | TP: %.5f",
                     trade.ResultOrder(), g_lote_sell, g_sl_final_sell, g_tp_final_sell);
        }
     }
  }

//+------------------------------------------------------------------+
//| GESTIÓN EN VIVO: MOVER A BREAK-EVEN                              |
//+------------------------------------------------------------------+
void MoverABreakEven()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      if(pos_info.SelectByIndex(i))
        {
         if(pos_info.Symbol() == _Symbol && pos_info.Magic() == InpMagicNumber)
           {
            double precio_apertura = pos_info.PriceOpen();
            double sl_actual = pos_info.StopLoss();
            double spread = (SymbolInfoDouble(_Symbol, SYMBOL_ASK) - SymbolInfoDouble(_Symbol, SYMBOL_BID));

            if(pos_info.PositionType() == POSITION_TYPE_BUY)
              {
               double nuevo_sl = NormalizeDouble(precio_apertura + spread, _Digits);
               if(nuevo_sl > sl_actual)
                  trade.PositionModify(pos_info.Ticket(), nuevo_sl, pos_info.TakeProfit());
              }
            else if(pos_info.PositionType() == POSITION_TYPE_SELL)
              {
               double nuevo_sl = NormalizeDouble(precio_apertura - spread, _Digits);
               if(sl_actual == 0.0 || nuevo_sl < sl_actual)
                  trade.PositionModify(pos_info.Ticket(), nuevo_sl, pos_info.TakeProfit());
              }
           }
        }
     }
  }

//+------------------------------------------------------------------+
//| GESTIÓN EN VIVO: MOVER STOP A LÍNEA DE SEGURIDAD                 |
//+------------------------------------------------------------------+
void MoverASeguridad()
  {
   double colchon = CalcularColchonSpread();
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      if(pos_info.SelectByIndex(i))
        {
         if(pos_info.Symbol() == _Symbol && pos_info.Magic() == InpMagicNumber)
           {
            if(pos_info.PositionType() == POSITION_TYPE_BUY)
              {
               double nuevo_sl = NormalizeDouble(g_precio_seguridad - colchon, _Digits);
               trade.PositionModify(pos_info.Ticket(), nuevo_sl, pos_info.TakeProfit());
              }
            else if(pos_info.PositionType() == POSITION_TYPE_SELL)
              {
               double nuevo_sl = NormalizeDouble(g_precio_seguridad + colchon, _Digits);
               trade.PositionModify(pos_info.Ticket(), nuevo_sl, pos_info.TakeProfit());
              }
           }
        }
     }
  }

//+------------------------------------------------------------------+
//| GESTIÓN EN VIVO: CERRAR TODAS LAS POSICIONES                     |
//+------------------------------------------------------------------+
void CerrarTodasLasPosiciones()
  {
   for(int i = PositionsTotal() - 1; i >= 0; i--)
     {
      if(pos_info.SelectByIndex(i))
        {
         if(pos_info.Symbol() == _Symbol && pos_info.Magic() == InpMagicNumber)
           {
            trade.PositionClose(pos_info.Ticket());
           }
        }
     }
  }

//+------------------------------------------------------------------+
//| HELPERS GRÁFICOS DE MQL5 EN SUBVENTANA CON GESTIÓN DE Z-ORDER    |
//+------------------------------------------------------------------+
void CrearRectLabel(string id, int x, int y, int w, int h, color bg_color, color border_color, int border_width, int z_order)
  {
   string name = PREFIX + id;
   ObjectDelete(0, name);
   if(ObjectCreate(0, name, OBJ_RECTANGLE_LABEL, g_subwindow, 0, 0))
     {
      ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
      ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
      ObjectSetInteger(0, name, OBJPROP_XSIZE, w);
      ObjectSetInteger(0, name, OBJPROP_YSIZE, h);
      ObjectSetInteger(0, name, OBJPROP_BGCOLOR, bg_color);
      ObjectSetInteger(0, name, OBJPROP_BORDER_COLOR, border_color);
      ObjectSetInteger(0, name, OBJPROP_BORDER_TYPE, BORDER_FLAT);
      ObjectSetInteger(0, name, OBJPROP_WIDTH, border_width);
      ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, name, OBJPROP_BACK, false);
      ObjectSetInteger(0, name, OBJPROP_ZORDER, z_order);
      ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
     }
  }

void CrearLabel(string id, int x, int y, string text, string font, int font_size, color clr, ENUM_ANCHOR_POINT anchor, int z_order)
  {
   string name = PREFIX + id;
   ObjectDelete(0, name);
   if(ObjectCreate(0, name, OBJ_LABEL, g_subwindow, 0, 0))
     {
      ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
      ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
      ObjectSetString(0, name, OBJPROP_TEXT, text);
      ObjectSetString(0, name, OBJPROP_FONT, font);
      ObjectSetInteger(0, name, OBJPROP_FONTSIZE, font_size);
      ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
      ObjectSetInteger(0, name, OBJPROP_ANCHOR, anchor);
      ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, name, OBJPROP_BACK, false);
      ObjectSetInteger(0, name, OBJPROP_ZORDER, z_order);
      ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
     }
  }

void ActualizarLabel(string id, string text)
  {
   string name = PREFIX + id;
   ObjectSetString(0, name, OBJPROP_TEXT, text);
  }

void CrearBoton(string id, int x, int y, int w, int h, string text, bool activo, int z_order)
  {
   string name = PREFIX + id;
   ObjectDelete(0, name);
   if(ObjectCreate(0, name, OBJ_BUTTON, g_subwindow, 0, 0))
     {
      ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
      ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
      ObjectSetInteger(0, name, OBJPROP_XSIZE, w);
      ObjectSetInteger(0, name, OBJPROP_YSIZE, h);
      ObjectSetString(0, name, OBJPROP_TEXT, text);
      ObjectSetString(0, name, OBJPROP_FONT, "Segoe UI");
      ObjectSetInteger(0, name, OBJPROP_FONTSIZE, 8);
      ObjectSetInteger(0, name, OBJPROP_COLOR, activo ? clrWhite : clrDarkGray);
      ObjectSetInteger(0, name, OBJPROP_BGCOLOR, activo ? clrDodgerBlue : C'28,38,55');
      ObjectSetInteger(0, name, OBJPROP_BORDER_COLOR, activo ? clrDeepSkyBlue : C'50,65,85');
      ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, name, OBJPROP_BACK, false);
      ObjectSetInteger(0, name, OBJPROP_ZORDER, z_order);
      ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
     }
  }

void CrearBotonNivel(string id, int x, int y, int w, int h, string titulo, double precio, color clr_linea, bool activo, int z_order)
  {
   string name = PREFIX + id;
   ObjectDelete(0, name);
   if(ObjectCreate(0, name, OBJ_BUTTON, g_subwindow, 0, 0))
     {
      ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
      ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
      ObjectSetInteger(0, name, OBJPROP_XSIZE, w);
      ObjectSetInteger(0, name, OBJPROP_YSIZE, h);
      
      string txt = titulo + "\n" + DoubleToString(precio, _Digits);
      ObjectSetString(0, name, OBJPROP_TEXT, txt);
      ObjectSetString(0, name, OBJPROP_FONT, "Segoe UI");
      ObjectSetInteger(0, name, OBJPROP_FONTSIZE, 8);
      ObjectSetInteger(0, name, OBJPROP_COLOR, activo ? clrWhite : clrLightGray);
      ObjectSetInteger(0, name, OBJPROP_BGCOLOR, activo ? C'35,50,75' : C'20,28,42');
      ObjectSetInteger(0, name, OBJPROP_BORDER_COLOR, activo ? clrWhite : clr_linea);
      ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, name, OBJPROP_BACK, false);
      ObjectSetInteger(0, name, OBJPROP_ZORDER, z_order);
      ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
     }
  }

void CrearBotonAccion(string id, int x, int y, int w, int h, string text, color bg, color fg, int z_order)
  {
   string name = PREFIX + id;
   ObjectDelete(0, name);
   if(ObjectCreate(0, name, OBJ_BUTTON, g_subwindow, 0, 0))
     {
      ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
      ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
      ObjectSetInteger(0, name, OBJPROP_XSIZE, w);
      ObjectSetInteger(0, name, OBJPROP_YSIZE, h);
      ObjectSetString(0, name, OBJPROP_TEXT, text);
      ObjectSetString(0, name, OBJPROP_FONT, "Segoe UI");
      ObjectSetInteger(0, name, OBJPROP_FONTSIZE, 9);
      ObjectSetInteger(0, name, OBJPROP_COLOR, fg);
      ObjectSetInteger(0, name, OBJPROP_BGCOLOR, bg);
      ObjectSetInteger(0, name, OBJPROP_BORDER_COLOR, bg);
      ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, name, OBJPROP_BACK, false);
      ObjectSetInteger(0, name, OBJPROP_ZORDER, z_order);
      ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
     }
  }
//+------------------------------------------------------------------+
