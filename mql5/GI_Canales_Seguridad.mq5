//+------------------------------------------------------------------+
//|                                       GI_Canales_Seguridad.mq5   |
//|                    Grupo Inteligencia - Análisis de Mercado      |
//|               Motor Matemático TradingView / Tori Trades         |
//+------------------------------------------------------------------+
#property copyright   "Grupo Inteligencia"
#property link        "https://grupointeligencia.cl"
#property version     "1.00"
#property description "Indicador nativo MT5 que replica exactamente la matemática"
#property description "de canales, líneas de seguridad, acción y zonas S/R de las"
#property description "imágenes TradingView de WhatsApp (Estrategia Tori / GI)."
#property indicator_chart_window
#property indicator_buffers 0
#property indicator_plots   0

//+------------------------------------------------------------------+
//| ENUMERACIONES                                                    |
//+------------------------------------------------------------------+
enum ENUM_DIRECCION
  {
   DIR_ALCISTA,
   DIR_BAJISTA,
   DIR_LATERAL
  };

enum ENUM_ESTADO
  {
   EST_TENDENCIA,
   EST_RUPTURA,
   EST_REBOTE,
   EST_RANGO
  };

//+------------------------------------------------------------------+
//| PARÁMETROS DE ENTRADA (Mismo estándar que tori/parametros.py)     |
//+------------------------------------------------------------------+
input group "--- Algoritmo de Trazado (Doctrina Tori Trades) ---"
input double InpZigZagATR          = 2.0;    // Umbral ZigZag Pivotes (x ATR)
input double InpTolToqueATR        = 0.25;   // Tolerancia de Toque (x ATR)
input double InpSepToqueATR        = 1.0;    // Separación entre Toques (x ATR)
input double InpPendMinATR         = 0.02;   // Pendiente Mínima Diagonal (x ATR)
input double InpPendEmpinadaATR    = 0.5;    // Umbral Pendiente Empinada (x ATR)
input int    InpMaxBarras          = 250;    // Ventana de Velas de Análisis
input int    InpProyeccionBarras   = 14;     // Velas de Proyección a la Derecha

input group "--- Soportes y Resistencias (Zonas Horizontales) ---"
input bool   InpMostrarZonasSR     = true;   // Mostrar Zonas de Soporte y Resistencia
input double InpZigZagHorizATR     = 1.5;    // Umbral ZigZag Horizontal (x ATR)
input double InpTolHorizATR        = 0.5;    // Tolerancia Cluster Horizontal (x ATR)
input double InpMinDistanciaATR    = 1.0;    // Distancia Mínima Operable S/R (x ATR)
input double InpMediaZonaATR       = 0.18;   // Semiancho de Zona S/R (0.18 x ATR como en TV)
input int    InpMinToquesHoriz     = 2;      // Mínimo Toques para S/R Válido

input group "--- Paleta Gráfica Oficial TV Grupo Inteligencia ---"
input color  InpColorSeguridad     = C'38,198,160'; // Línea de Seguridad (#26C6A0 Verde Esmeralda)
input color  InpColorAccion        = C'255,77,94';  // Línea de Acción (#FF4D5E Rojo Coral)
input color  InpColorSeguimiento   = C'155,231,196';// Línea Seguimiento (#9BE7C4 Verde Menta)
input color  InpColorRango         = C'203,213,225';// Borde de Rango (#CBD5E1 Pizarra)
input color  InpColorZonaSR        = C'255,213,79'; // Zonas S/R (#FFD54F Amarillo TradingView)

input group "--- Panel Informativo HUD ---"
input bool   InpMostrarPanel       = true;   // Mostrar Panel HUD en Pantalla
input int    InpPanelX             = 20;     // Posición X del Panel
input int    InpPanelY             = 35;     // Posición Y del Panel

//+------------------------------------------------------------------+
//| ESTRUCTURAS DE DATOS                                             |
//+------------------------------------------------------------------+
struct Pivot
  {
   int      idx;    // índice cronológico (0 = más viejo en ventana, N-1 = actual)
   datetime time;
   double   price;
   char     type;   // 'H' = High, 'L' = Low
  };

struct Trazo
  {
   bool     valido;
   bool     vigente;
   bool     alcista;
   int      idx_a;
   datetime time_a;
   double   price_a;
   int      idx_b;
   datetime time_b;
   double   price_b;
   double   pendiente;
   int      toques;
   int      idx_ruptura;
   datetime time_ruptura;
   string   calidad;  // "A+", "B"
   bool     empinada;
  };

struct Horizontal
  {
   double   precio;
   int      toques;
   datetime time_primero;
  };

// Prefijo único para evitar interferencias
const string PREFIX = "GI_TV_";

//+------------------------------------------------------------------+
//| Custom indicator initialization function                         |
//+------------------------------------------------------------------+
int OnInit()
  {
   LimpiarObjetos();
   return(INIT_SUCCEEDED);
  }

//+------------------------------------------------------------------+
//| Custom indicator deinitialization function                       |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
  {
   LimpiarObjetos();
   ChartRedraw(0);
  }

//+------------------------------------------------------------------+
//| Limpia todos los objetos creados por el indicador                |
//+------------------------------------------------------------------+
void LimpiarObjetos()
  {
   ObjectsDeleteAll(0, PREFIX);
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
   if(rates_total < 40)
      return(0);

   // Solo recalculamos en cada barra o cada cierto intervalo para máxima fluidez
   static datetime ultima_barra = 0;
   datetime barra_actual = time[rates_total - 1];
   if(prev_calculated > 0 && barra_actual == ultima_barra)
     {
      // Podemos refrescar solo el panel en ticks entre barras
      return(rates_total);
     }
   ultima_barra = barra_actual;

   // 1. Determinar ventana de análisis
   int n = MathMin(rates_total, InpMaxBarras);
   int offset = rates_total - n;

   // 2. Calcular ATR(14) con el método Wilder de TradingView
   double atrs[];
   ArrayResize(atrs, n);
   double trs[];
   ArrayResize(trs, n);

   for(int i = 0; i < n; i++)
     {
      int real_idx = offset + i;
      double h = high[real_idx];
      double l = low[real_idx];
      double c_prev = (i == 0) ? close[real_idx] : close[real_idx - 1];
      trs[i] = MathMax(h - l, MathMax(MathAbs(h - c_prev), MathAbs(l - c_prev)));
     }

   double sum_tr = 0;
   for(int i = 0; i < 14 && i < n; i++)
      sum_tr += trs[i];
   double current_atr = (n >= 14) ? sum_tr / 14.0 : trs[0];

   for(int i = 14; i < n; i++)
      current_atr = (current_atr * 13.0 + trs[i]) / 14.0;

   if(current_atr <= 0)
      current_atr = (high[rates_total - 1] - low[rates_total - 1]);
   if(current_atr <= 0)
      return(rates_total);

   // 3. Detectar Pivotes ZigZag para Diagonales
   double umbral_zigzag = InpZigZagATR * current_atr;
   Pivot pivotes[];
   ObtenerPivotesZigzag(high, low, offset, n, umbral_zigzag, pivotes);

   // 4. Trazar Directriz Alcista y Bajista
   Trazo trazo_alcista;
   Trazo trazo_bajista;
   TrazarMejorDiagonal(true, pivotes, high, low, close, time, offset, n, current_atr, trazo_alcista);
   TrazarMejorDiagonal(false, pivotes, high, low, close, time, offset, n, current_atr, trazo_bajista);

   // 5. Determinar Estructura y Roles (Seguridad, Acción, Canal)
   ENUM_ESTADO estado;
   ENUM_DIRECCION direccion;
   Trazo trazo_seguridad;
   Trazo trazo_accion;
   DeterminarEstructura(trazo_alcista, trazo_bajista, close[rates_total - 1], offset, n, current_atr,
                        estado, direccion, trazo_seguridad, trazo_accion);

   // 6. Detectar Soportes y Resistencias Horizontales (Zonas)
   Horizontal s_r[];
   DetectarHorizontales(high, low, close, time, offset, n, current_atr, s_r);

   double soporte_val = 0;
   double resistencia_val = 0;
   double precio_cierre = close[rates_total - 1];
   ObtenerNivelesPublicados(s_r, high, low, offset, n, current_atr, precio_cierre, soporte_val, resistencia_val);

   // 7. Renderizar en el gráfico de MT5
   LimpiarObjetos();

   // Dibujar Línea de Seguridad
   if(trazo_seguridad.valido)
     {
      string desc_seg = StringFormat("Línea de Seguridad [%s] (%d toques)", trazo_seguridad.calidad, trazo_seguridad.toques);
      DibujarLineaDiagonal("SEGURIDAD", trazo_seguridad, InpColorSeguridad, 3, STYLE_SOLID, desc_seg);
     }

   // Dibujar Línea de Acción (si existe y es distinta)
   if(trazo_accion.valido)
     {
      string desc_acc = StringFormat("Línea de Acción (%s)", trazo_accion.vigente ? "Canal/Prueba" : "Gatillo Roto");
      ENUM_LINE_STYLE estilo_acc = trazo_accion.vigente ? STYLE_SOLID : STYLE_DASH;
      DibujarLineaDiagonal("ACCION", trazo_accion, InpColorAccion, 2, estilo_acc, desc_acc);
     }

   // Dibujar Zonas de Soporte y Resistencia Horizontales
   if(InpMostrarZonasSR)
     {
      datetime t_inicio = time[offset];
      datetime t_fin    = time[rates_total - 1] + (datetime)(InpProyeccionBarras * PeriodSeconds());
      double media_zona = InpMediaZonaATR * current_atr;

      if(soporte_val > 0)
         DibujarZonaSR("SOPORTE", soporte_val, media_zona, t_inicio, t_fin, InpColorZonaSR, "SOPORTE");
      if(resistencia_val > 0)
         DibujarZonaSR("RESISTENCIA", resistencia_val, media_zona, t_inicio, t_fin, InpColorZonaSR, "RESISTENCIA");
     }

   // 8. Dibujar Panel Informativo HUD
   if(InpMostrarPanel)
     {
      DibujarHUD(estado, direccion, trazo_seguridad, soporte_val, resistencia_val, current_atr, precio_cierre);
     }

   ChartRedraw(0);
   return(rates_total);
  }

//+------------------------------------------------------------------+
//| ALGORITMO ZIGZAG ADAPTATIVO POR ATR                              |
//+------------------------------------------------------------------+
void ObtenerPivotesZigzag(const double &high[], const double &low[],
                         int offset, int n, double umbral, Pivot &pivotes[])
  {
   ArrayResize(pivotes, 0);
   if(n < 3 || umbral <= 0)
      return;

   int dir = 0; // 0 = inicio, 1 = buscando H, -1 = buscando L
   double ext_h = high[offset];
   double ext_l = low[offset];
   int ext_hi_i = 0;
   int ext_lo_i = 0;

   for(int i = 0; i < n; i++)
     {
      int r = offset + i;
      double h = high[r];
      double l = low[r];

      if(dir >= 0)
        {
         if(h >= ext_h)
           {
            ext_h = h;
            ext_hi_i = i;
           }
         if(dir == 1 && (ext_h - l) >= umbral)
           {
            AgregarPivote(pivotes, ext_hi_i, ext_h, 'H');
            dir = -1;
            ext_l = l;
            ext_lo_i = i;
            continue;
           }
        }

      if(dir <= 0)
        {
         if(l <= ext_l)
           {
            ext_l = l;
            ext_lo_i = i;
           }
         if(dir == -1 && (h - ext_l) >= umbral)
           {
            AgregarPivote(pivotes, ext_lo_i, ext_l, 'L');
            dir = 1;
            ext_h = h;
            ext_hi_i = i;
            continue;
           }
        }

      if(dir == 0)
        {
         if((ext_h - l) >= umbral && ext_hi_i < i)
           {
            AgregarPivote(pivotes, ext_hi_i, ext_h, 'H');
            dir = -1;
            ext_l = l;
            ext_lo_i = i;
           }
         else if((h - ext_l) >= umbral && ext_lo_i < i)
           {
            AgregarPivote(pivotes, ext_lo_i, ext_l, 'L');
            dir = 1;
            ext_h = h;
            ext_hi_i = i;
           }
        }
     }
  }

void AgregarPivote(Pivot &pivotes[], int idx, double price, char type)
  {
   int sz = ArraySize(pivotes);
   ArrayResize(pivotes, sz + 1);
   pivotes[sz].idx = idx;
   pivotes[sz].price = price;
   pivotes[sz].type = type;
  }

//+------------------------------------------------------------------+
//| TRAZADO DE DIAGONALES SEGÚN TORI TRADES                          |
//+------------------------------------------------------------------+
void TrazarMejorDiagonal(bool alcista, const Pivot &pivotes[],
                         const double &high[], const double &low[], const double &close[],
                         const datetime &time[], int offset, int n, double atr,
                         Trazo &mejor_trazo)
  {
   mejor_trazo.valido = false;
   char tipo_buscado = alcista ? 'L' : 'H';

   // Filtrar pivotes del tipo adecuado
   int candidatos_piv[];
   for(int i = 0; i < ArraySize(pivotes); i++)
     {
      if(pivotes[i].type == tipo_buscado)
        {
         int sz = ArraySize(candidatos_piv);
         ArrayResize(candidatos_piv, sz + 1);
         candidatos_piv[sz] = i;
        }
     }

   if(ArraySize(candidatos_piv) < 2)
      return;

   // Buscar el extremo inicial confirmado (mínimo más bajo para alcista / máximo más alto para bajista)
   int idx_extremo = -1;
   double precio_ext = alcista ? DBL_MAX : -DBL_MAX;

   for(int i = 0; i < ArraySize(candidatos_piv); i++)
     {
      int p_idx = candidatos_piv[i];
      int bar_i = pivotes[p_idx].idx;

      // Verificación de confirmado: antes de él hubo una distancia de al menos 1 giro
      bool confirmado = false;
      if(bar_i > 0)
        {
         double max_prev = -DBL_MAX;
         double min_prev = DBL_MAX;
         for(int k = 0; k < bar_i; k++)
           {
            if(high[offset + k] > max_prev) max_prev = high[offset + k];
            if(low[offset + k] < min_prev)  min_prev = low[offset + k];
           }
         if(alcista && (max_prev - low[offset + bar_i]) >= (InpZigZagATR * atr))
            confirmado = true;
         if(!alcista && (high[offset + bar_i] - min_prev) >= (InpZigZagATR * atr))
            confirmado = true;
        }

      if(confirmado)
        {
         if(alcista && pivotes[p_idx].price < precio_ext)
           {
            precio_ext = pivotes[p_idx].price;
            idx_extremo = bar_i;
           }
         else if(!alcista && pivotes[p_idx].price > precio_ext)
           {
            precio_ext = pivotes[p_idx].price;
            idx_extremo = bar_i;
           }
        }
     }

   if(idx_extremo < 0 && ArraySize(candidatos_piv) > 0)
      idx_extremo = pivotes[candidatos_piv[0]].idx;

   // Evaluar directrices desde el extremo inicial
   Trazo candidato;
   Trazo mejor_vigente;
   mejor_vigente.valido = false;
   Trazo mejor_rota;
   mejor_rota.valido = false;

   for(int b_p = 0; b_p < ArraySize(candidatos_piv); b_p++)
     {
      int idx_b = pivotes[candidatos_piv[b_p]].idx;
      if(idx_b <= idx_extremo)
         continue;

      if(EvaluarTrazo(alcista, idx_extremo, idx_b, high, low, close, time, offset, n, atr, candidato))
        {
         if(candidato.vigente)
           {
            if(!mejor_vigente.valido || candidato.toques > mejor_vigente.toques ||
               (candidato.toques == mejor_vigente.toques && MathAbs(candidato.pendiente) > MathAbs(mejor_vigente.pendiente)))
              {
               mejor_vigente = candidato;
              }
           }
         else
           {
            if(!mejor_rota.valido || candidato.toques > mejor_rota.toques)
              {
               mejor_rota = candidato;
              }
           }
        }
     }

   if(mejor_vigente.valido)
      mejor_trazo = mejor_vigente;
   else if(mejor_rota.valido)
      mejor_trazo = mejor_rota;
  }

//+------------------------------------------------------------------+
//| Evalúa un trazo específico entre dos pivotes A y B               |
//+------------------------------------------------------------------+
bool EvaluarTrazo(bool alcista, int a, int b,
                 const double &high[], const double &low[], const double &close[],
                 const datetime &time[], int offset, int n, double atr,
                 Trazo &t)
  {
   double p_a = alcista ? low[offset + a] : high[offset + a];
   double p_b = alcista ? low[offset + b] : high[offset + b];
   double pendiente = (p_b - p_a) / (double)(b - a);

   // Validar dirección de la pendiente
   if(alcista && pendiente <= 0) return(false);
   if(!alcista && pendiente >= 0) return(false);

   // Validar que no sea plana
   if(MathAbs(pendiente) < InpPendMinATR * atr) return(false);

   double tol   = InpTolToqueATR * atr;
   double lejos = InpSepToqueATR * atr;

   int toques = 0;
   bool en_episodio = false;
   double min_holgura = DBL_MAX;
   int ruptura = -1;

   for(int i = a; i < n; i++)
     {
      double val_linea = p_a + pendiente * (i - a);
      double holgura = alcista ? (low[offset + i] - val_linea) : (val_linea - high[offset + i]);

      // Penetración de la línea
      if(holgura < -tol)
        {
         double holgura_cierre = alcista ? (close[offset + i] - val_linea) : (val_linea - close[offset + i]);
         if(i > b && holgura_cierre < -tol)
           {
            ruptura = i; // Ruptura confirmada por cierre de vela
            break;
           }
         if(i <= b)
           {
            return(false); // Corta velas antes de B: línea no limpia, se descarta
           }
        }

      // Conteo de toques con histéresis
      if(holgura <= tol)
        {
         en_episodio = true;
         if(holgura < min_holgura) min_holgura = holgura;
        }
      else if(holgura >= lejos)
        {
         if(en_episodio)
           {
            toques++;
            en_episodio = false;
            min_holgura = DBL_MAX;
           }
        }
     }

   if(en_episodio)
      toques++;

   if(toques < 2)
      return(false);

   t.valido = true;
   t.alcista = alcista;
   t.idx_a = a;
   t.time_a = time[offset + a];
   t.price_a = p_a;
   t.idx_b = b;
   t.time_b = time[offset + b];
   t.price_b = p_b;
   t.pendiente = pendiente;
   t.toques = toques;
   t.idx_ruptura = ruptura;
   t.time_ruptura = (ruptura >= 0) ? time[offset + ruptura] : 0;
   t.vigente = (ruptura < 0);

   // Calidad A+ si tiene >= 3 toques y abarca buena cantidad de barras
   bool semanas_ok = ((b - a) >= 30);
   t.calidad = (toques >= 3 && semanas_ok) ? "A+" : "B";
   t.empinada = (MathAbs(pendiente) > InpPendEmpinadaATR * atr);

   return(true);
  }

//+------------------------------------------------------------------+
//| DETERMINA LA ESTRUCTURA Y LOS ROLES DE LAS LÍNEAS                |
//+------------------------------------------------------------------+
void DeterminarEstructura(const Trazo &alcista, const Trazo &bajista,
                         double precio_actual, int offset, int n, double atr,
                         ENUM_ESTADO &estado, ENUM_DIRECCION &dir,
                         Trazo &seguridad, Trazo &accion)
  {
   seguridad.valido = false;
   accion.valido = false;

   // 1. Revisar si hay ruptura reciente (últimas 30 velas)
   int ultimo = n - 1;
   int desde_alc = (alcista.valido && !alcista.vigente) ? (ultimo - alcista.idx_ruptura) : 9999;
   int desde_baj = (bajista.valido && !bajista.vigente) ? (ultimo - bajista.idx_ruptura) : 9999;

   if(desde_alc <= 30 || desde_baj <= 30)
     {
      if(desde_alc <= desde_baj)
        {
         estado = EST_RUPTURA;
         dir = DIR_BAJISTA; // Ruptura de directriz alcista genera sesgo bajista
         accion = alcista;
         if(bajista.valido && bajista.vigente)
            seguridad = bajista;
         return;
        }
      else
        {
         estado = EST_RUPTURA;
         dir = DIR_ALCISTA; // Ruptura de directriz bajista genera sesgo alcista
         accion = bajista;
         if(alcista.valido && alcista.vigente)
            seguridad = alcista;
         return;
        }
     }

   // 2. Si no hay ruptura, clasificar directrices vigentes
   if(alcista.valido && alcista.vigente && bajista.valido && bajista.vigente)
     {
      // Ambas vigentes: forman un canal
      if(alcista.toques >= bajista.toques)
        {
         estado = EST_TENDENCIA;
         dir = DIR_ALCISTA;
         seguridad = alcista;
         accion = bajista;
        }
      else
        {
         estado = EST_TENDENCIA;
         dir = DIR_BAJISTA;
         seguridad = bajista;
         accion = alcista;
        }
      return;
     }

   if(alcista.valido && alcista.vigente)
     {
      estado = EST_TENDENCIA;
      dir = DIR_ALCISTA;
      seguridad = alcista;
      return;
     }

   if(bajista.valido && bajista.vigente)
     {
      estado = EST_TENDENCIA;
      dir = DIR_BAJISTA;
      seguridad = bajista;
      return;
     }

   // Sin diagonales vigentes
   estado = EST_RANGO;
   dir = DIR_LATERAL;
  }

//+------------------------------------------------------------------+
//| DETECCIÓN DE SOPORTES Y RESISTENCIAS HORIZONTALES (CLUSTERS)     |
//+------------------------------------------------------------------+
void DetectarHorizontales(const double &high[], const double &low[], const double &close[],
                         const datetime &time[], int offset, int n, double atr,
                         Horizontal &niveles[])
  {
   ArrayResize(niveles, 0);
   double umbral_h = InpZigZagHorizATR * atr;
   Pivot p_horiz[];
   ObtenerPivotesZigzag(high, low, offset, n, umbral_h, p_horiz);

   if(ArraySize(p_horiz) < 2)
      return;

   // Agrupar pivotes cercanos en clusters
   double tol = InpTolHorizATR * atr;
   int total_p = ArraySize(p_horiz);

   // Ordenar precios
   double precios[];
   ArrayResize(precios, total_p);
   for(int i = 0; i < total_p; i++) precios[i] = p_horiz[i].price;
   ArraySort(precios);

   double suma = precios[0];
   int conteo = 1;
   double base = precios[0];

   for(int i = 1; i < total_p; i++)
     {
      if((precios[i] - base) <= tol)
        {
         suma += precios[i];
         conteo++;
        }
      else
        {
         if(conteo >= InpMinToquesHoriz)
           {
            int sz = ArraySize(niveles);
            ArrayResize(niveles, sz + 1);
            niveles[sz].precio = suma / conteo;
            niveles[sz].toques = conteo;
            niveles[sz].time_primero = time[offset];
           }
         base = precios[i];
         suma = precios[i];
         conteo = 1;
        }
     }
   if(conteo >= InpMinToquesHoriz)
     {
      int sz = ArraySize(niveles);
      ArrayResize(niveles, sz + 1);
      niveles[sz].precio = suma / conteo;
      niveles[sz].toques = conteo;
      niveles[sz].time_primero = time[offset];
     }
  }

//+------------------------------------------------------------------+
//| Obtiene los niveles de Soporte y Resistencia publicados          |
//+------------------------------------------------------------------+
void ObtenerNivelesPublicados(const Horizontal &s_r[], const double &high[], const double &low[],
                             int offset, int n, double atr, double precio,
                             double &soporte, double &resistencia)
  {
   soporte = 0;
   resistencia = 0;
   double min_dist_res = DBL_MAX;
   double min_dist_sop = DBL_MAX;
   double min_dist = InpMinDistanciaATR * atr;

   // 1. Buscar en clusters horizontales que cumplan con la distancia mínima operable
   for(int i = 0; i < ArraySize(s_r); i++)
     {
      double p = s_r[i].precio;
      if(p >= (precio + min_dist) && (p - precio) < min_dist_res)
        {
         min_dist_res = p - precio;
         resistencia = p;
        }
      else if(p <= (precio - min_dist) && (precio - p) < min_dist_sop)
        {
         min_dist_sop = precio - p;
         soporte = p;
        }
     }

   // 2. Si no hay resistencia con margen completo, intentar con margen reducido (0.5 ATR)
   if(resistencia == 0 && min_dist > 0)
     {
      double margen_reducido = 0.5 * min_dist;
      for(int i = 0; i < ArraySize(s_r); i++)
        {
         double p = s_r[i].precio;
         if(p >= (precio + margen_reducido) && (p - precio) < min_dist_res)
           {
            min_dist_res = p - precio;
            resistencia = p;
           }
        }
     }

   // 3. Si no hay soporte con margen completo, intentar con margen reducido (0.5 ATR)
   if(soporte == 0 && min_dist > 0)
     {
      double margen_reducido = 0.5 * min_dist;
      for(int i = 0; i < ArraySize(s_r); i++)
        {
         double p = s_r[i].precio;
         if(p <= (precio - margen_reducido) && (precio - p) < min_dist_sop)
           {
            min_dist_sop = precio - p;
            soporte = p;
           }
        }
     }

   // 4. Si aún falta alguno en la ventana, buscar el extremo visible mayor (High/Low)
   if(resistencia == 0)
     {
      double max_h = -DBL_MAX;
      for(int i = 0; i < n; i++)
        {
         if(high[offset + i] > max_h)
            max_h = high[offset + i];
        }
      if(max_h >= precio + min_dist)
         resistencia = max_h;
     }

   if(soporte == 0)
     {
      double min_l = DBL_MAX;
      for(int i = 0; i < n; i++)
        {
         if(low[offset + i] < min_l)
            min_l = low[offset + i];
        }
      if(min_l <= precio - min_dist)
         soporte = min_l;
     }
  }

//+------------------------------------------------------------------+
//| DIBUJO DE LÍNEAS DIAGONALES EN MT5                               |
//+------------------------------------------------------------------+
void DibujarLineaDiagonal(string rol, const Trazo &t, color clr, int ancho, ENUM_LINE_STYLE estilo, string desc)
  {
   string obj_name = PREFIX + "DIAG_" + rol;
   ObjectDelete(0, obj_name);

   if(!ObjectCreate(0, obj_name, OBJ_TREND, 0, t.time_a, t.price_a, t.time_b, t.price_b))
      return;

   ObjectSetInteger(0, obj_name, OBJPROP_RAY_RIGHT, true);
   ObjectSetInteger(0, obj_name, OBJPROP_COLOR, clr);
   ObjectSetInteger(0, obj_name, OBJPROP_WIDTH, ancho);
   ObjectSetInteger(0, obj_name, OBJPROP_STYLE, estilo);
   ObjectSetInteger(0, obj_name, OBJPROP_BACK, false);
   ObjectSetInteger(0, obj_name, OBJPROP_SELECTABLE, false);
   ObjectSetString(0, obj_name, OBJPROP_TOOLTIP, desc);
  }

//+------------------------------------------------------------------+
//| DIBUJO DE ZONAS S/R (RECTÁNGULOS ESTILO TRADINGVIEW)             |
//+------------------------------------------------------------------+
void DibujarZonaSR(string rol, double precio, double media_zona,
                   datetime t1, datetime t2, color clr, string etiqueta)
  {
   string obj_rect = PREFIX + "ZONA_" + rol;
   string obj_line = PREFIX + "LINE_" + rol;
   string obj_text = PREFIX + "TEXT_" + rol;

   ObjectDelete(0, obj_rect);
   ObjectDelete(0, obj_line);
   ObjectDelete(0, obj_text);

   double p_sup = precio + media_zona;
   double p_inf = precio - media_zona;

   // Rectángulo con relleno semitransparente de fondo
   if(ObjectCreate(0, obj_rect, OBJ_RECTANGLE, 0, t1, p_sup, t2, p_inf))
     {
      ObjectSetInteger(0, obj_rect, OBJPROP_COLOR, clr);
      ObjectSetInteger(0, obj_rect, OBJPROP_FILL, true);
      ObjectSetInteger(0, obj_rect, OBJPROP_BACK, true);
      ObjectSetInteger(0, obj_rect, OBJPROP_SELECTABLE, false);
     }

   // Línea central punteada en el precio exacto
   if(ObjectCreate(0, obj_line, OBJ_TREND, 0, t1, precio, t2, precio))
     {
      ObjectSetInteger(0, obj_line, OBJPROP_RAY_RIGHT, true);
      ObjectSetInteger(0, obj_line, OBJPROP_COLOR, clr);
      ObjectSetInteger(0, obj_line, OBJPROP_WIDTH, 1);
      ObjectSetInteger(0, obj_line, OBJPROP_STYLE, STYLE_DOT);
      ObjectSetInteger(0, obj_line, OBJPROP_SELECTABLE, false);
     }

   // Etiqueta de texto descriptiva a la derecha
   if(ObjectCreate(0, obj_text, OBJ_TEXT, 0, t2, precio))
     {
      string texto = StringFormat("  %s: %.*f", etiqueta, _Digits, precio);
      ObjectSetString(0, obj_text, OBJPROP_TEXT, texto);
      ObjectSetString(0, obj_text, OBJPROP_FONT, "Space Grotesk");
      ObjectSetInteger(0, obj_text, OBJPROP_FONTSIZE, 9);
      ObjectSetInteger(0, obj_text, OBJPROP_COLOR, clr);
      ObjectSetInteger(0, obj_text, OBJPROP_ANCHOR, ANCHOR_LEFT);
      ObjectSetInteger(0, obj_text, OBJPROP_SELECTABLE, false);
     }
  }

//+------------------------------------------------------------------+
//| PANEL HUD EN PANTALLA (ALTO CONTRASTE GRUPO INTELIGENCIA)        |
//+------------------------------------------------------------------+
void DibujarHUD(ENUM_ESTADO est, ENUM_DIRECCION dir, const Trazo &seg,
                double soporte, double resistencia, double atr, double precio)
  {
   string bg = PREFIX + "HUD_BG";
   ObjectDelete(0, bg);

   int ancho_box = 320;
   int alto_box  = 165;

   if(ObjectCreate(0, bg, OBJ_RECTANGLE_LABEL, 0, 0, 0))
     {
      ObjectSetInteger(0, bg, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, bg, OBJPROP_XDISTANCE, InpPanelX);
      ObjectSetInteger(0, bg, OBJPROP_YDISTANCE, InpPanelY);
      ObjectSetInteger(0, bg, OBJPROP_XSIZE, ancho_box);
      ObjectSetInteger(0, bg, OBJPROP_YSIZE, alto_box);
      ObjectSetInteger(0, bg, OBJPROP_BGCOLOR, C'7,13,20'); // Fondo oscuro TV #070D14
      ObjectSetInteger(0, bg, OBJPROP_BORDER_COLOR, C'80,192,168'); // Borde turquesa
      ObjectSetInteger(0, bg, OBJPROP_BORDER_TYPE, BORDER_FLAT);
      ObjectSetInteger(0, bg, OBJPROP_SELECTABLE, false);
     }

   string str_dir = "LATERAL ↔️";
   color clr_dir = C'203,213,225';
   if(dir == DIR_ALCISTA) { str_dir = "ALCISTA ⬆️"; clr_dir = InpColorSeguridad; }
   if(dir == DIR_BAJISTA) { str_dir = "BAJISTA ⬇️"; clr_dir = InpColorAccion; }

   string str_est = "TENDENCIA";
   if(est == EST_RUPTURA) str_est = "RUPTURA VIGENTE ⚡";
   if(est == EST_REBOTE)   str_est = "REBOTE TÉCNICO 🛡️";
   if(est == EST_RANGO)    str_est = "RANGO LATERAL ⏸️";

   double val_seg_actual = 0;
   if(seg.valido)
      val_seg_actual = seg.price_a + seg.pendiente * (InpMaxBarras - seg.idx_a);

   CrearLabelHUD("TITULO", "GI ENGINE · CANALES & SEGURIDAD", InpPanelX + 14, InpPanelY + 12, C'80,192,168', 10, true);
   CrearLabelHUD("DIR",    StringFormat("Sesgo: %s  |  %s", str_dir, str_est), InpPanelX + 14, InpPanelY + 36, clr_dir, 9, true);

   string txt_seg = seg.valido ? StringFormat("Línea Seguridad: %.*f [%s]", _Digits, val_seg_actual, seg.calidad) : "Línea Seguridad: Sin directriz activa";
   CrearLabelHUD("SEG", txt_seg, InpPanelX + 14, InpPanelY + 60, InpColorSeguridad, 9, false);

   string txt_res = (resistencia > 0) ? StringFormat("Resistencia Clave: %.*f", _Digits, resistencia) : "Resistencia: En máximos abiertos";
   CrearLabelHUD("RES", txt_res, InpPanelX + 14, InpPanelY + 84, InpColorZonaSR, 9, false);

   string txt_sop = (soporte > 0) ? StringFormat("Soporte Clave:     %.*f", _Digits, soporte) : "Soporte: En mínimos abiertos";
   CrearLabelHUD("SOP", txt_sop, InpPanelX + 14, InpPanelY + 106, InpColorZonaSR, 9, false);

   string txt_atr = StringFormat("ATR(14): %.*f  |  Precio: %.*f", _Digits, atr, _Digits, precio);
   CrearLabelHUD("ATR", txt_atr, InpPanelX + 14, InpPanelY + 130, C'148,163,184', 8, false);
  }

void CrearLabelHUD(string id, string texto, int x, int y, color clr, int size, bool bold)
  {
   string name = PREFIX + "LBL_" + id;
   ObjectDelete(0, name);

   if(ObjectCreate(0, name, OBJ_LABEL, 0, 0, 0))
     {
      ObjectSetInteger(0, name, OBJPROP_CORNER, CORNER_LEFT_UPPER);
      ObjectSetInteger(0, name, OBJPROP_XDISTANCE, x);
      ObjectSetInteger(0, name, OBJPROP_YDISTANCE, y);
      ObjectSetString(0, name, OBJPROP_TEXT, texto);
      ObjectSetString(0, name, OBJPROP_FONT, bold ? "Plus Jakarta Sans Bold" : "Space Grotesk");
      ObjectSetInteger(0, name, OBJPROP_FONTSIZE, size);
      ObjectSetInteger(0, name, OBJPROP_COLOR, clr);
      ObjectSetInteger(0, name, OBJPROP_SELECTABLE, false);
     }
  }
//+------------------------------------------------------------------+
