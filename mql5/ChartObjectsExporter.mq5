//+------------------------------------------------------------------+
//| ChartObjectsExporter.mq5                                         |
//| Service: exporta los objetos dibujados a mano (lineas            |
//| horizontales, trendlines, canales, rectangulos) de TODOS los     |
//| graficos abiertos a Common/Files/chart_objects.json, mas un      |
//| screenshot PNG por grafico. Lo consume el MCP market-data         |
//| (tool get_chart_objects). Sub-proyecto A.                        |
//+------------------------------------------------------------------+
#property service
#property strict

input int RefrescoSegundos = 60;     // re-exporta cada N segundos
input int AnchoPNG         = 1280;   // ancho del screenshot
input int AltoPNG          = 720;    // alto del screenshot

//--- escapa comillas/backslash para JSON
string JsonEscape(string s)
{
   StringReplace(s, "\\", "\\\\");
   StringReplace(s, "\"", "\\\"");
   return(s);
}

//--- normaliza separadores de fecha de MT5 (".") al guion ISO que parsea Python
string FechaIso(string s)
{
   StringReplace(s, ".", "-");
   return(s);
}

//--- "YYYY.MM.DD HH:MM" -> "YYYY-MM-DD_HH-MM" para nombres de archivo
string FechaArchivo(datetime t)
{
   string s = TimeToString(t, TIME_DATE|TIME_MINUTES);
   StringReplace(s, ".", "-");
   StringReplace(s, " ", "_");
   StringReplace(s, ":", "-");
   return(s);
}

//--- slug del proyecto: lowercase(symbol) sin .spot / # / /  (convencion charts #81)
string SlugSimbolo(string symbol)
{
   string s = symbol;
   StringToLower(s);
   StringReplace(s, ".spot", "");
   StringReplace(s, "#", "");
   StringReplace(s, "/", "");
   return(s);
}

//--- "PERIOD_H4" -> "H4"
string TimeframeStr(ENUM_TIMEFRAMES tf)
{
   string s = EnumToString(tf);
   return(StringSubstr(s, 7));
}

//--- copia un archivo del sandbox local (MQL5/Files) a Common/Files (binario)
bool CopiarACommon(string nombre)
{
   int hr = FileOpen(nombre, FILE_READ|FILE_BIN);
   if(hr == INVALID_HANDLE) return(false);
   uchar data[];
   uint n = FileReadArray(hr, data);
   FileClose(hr);

   int hw = FileOpen(nombre, FILE_WRITE|FILE_BIN|FILE_COMMON);
   if(hw == INVALID_HANDLE) return(false);
   if(n > 0) FileWriteArray(hw, data);
   FileClose(hw);
   return(true);
}

//--- nombre del tipo de canal para el JSON
string TipoCanal(long objtype)
{
   if(objtype == OBJ_STDDEVCHANNEL) return("stddev");
   if(objtype == OBJ_REGRESSION)    return("regression");
   return("equidistant");
}

//+------------------------------------------------------------------+
//| Serializa los objetos de un chart a un fragmento JSON            |
//+------------------------------------------------------------------+
string SerializarChart(long chart_id)
{
   string symbol = ChartSymbol(chart_id);
   if(symbol == "") return("");

   ENUM_TIMEFRAMES period = ChartPeriod(chart_id);
   string tf = TimeframeStr(period);
   int    digits = (int)SymbolInfoInteger(symbol, SYMBOL_DIGITS);
   double precio = SymbolInfoDouble(symbol, SYMBOL_BID);
   datetime ahora = TimeCurrent();

   string hlines = "", trendlines = "", channels = "", rectangles = "";

   int total = ObjectsTotal(chart_id, -1, -1);
   for(int i = 0; i < total; i++)
   {
      string name = ObjectName(chart_id, i, -1, -1);
      long   t    = ObjectGetInteger(chart_id, name, OBJPROP_TYPE);
      string nm   = JsonEscape(name);

      if(t == OBJ_HLINE)
      {
         double price = ObjectGetDouble(chart_id, name, OBJPROP_PRICE, 0);
         if(hlines != "") hlines += ", ";
         hlines += StringFormat("{\"name\": \"%s\", \"price\": %s}",
                                nm, DoubleToString(price, digits));
      }
      else if(t == OBJ_TREND)
      {
         double   p1 = ObjectGetDouble(chart_id, name, OBJPROP_PRICE, 0);
         double   p2 = ObjectGetDouble(chart_id, name, OBJPROP_PRICE, 1);
         datetime t1 = (datetime)ObjectGetInteger(chart_id, name, OBJPROP_TIME, 0);
         datetime t2 = (datetime)ObjectGetInteger(chart_id, name, OBJPROP_TIME, 1);
         double   actual = ObjectGetValueByTime(chart_id, name, ahora, 0);

         // pendiente segun orden cronologico de las anclas
         double delta = (t2 >= t1) ? (p2 - p1) : (p1 - p2);
         string pend = (delta > 0) ? "alcista" : (delta < 0 ? "bajista" : "plana");

         if(trendlines != "") trendlines += ", ";
         trendlines += StringFormat(
            "{\"name\": \"%s\", \"p1\": %s, \"t1\": \"%s\", \"p2\": %s, \"t2\": \"%s\", "
            "\"valor_actual\": %s, \"pendiente\": \"%s\"}",
            nm, DoubleToString(p1, digits), FechaIso(TimeToString(t1, TIME_DATE|TIME_MINUTES)),
            DoubleToString(p2, digits), FechaIso(TimeToString(t2, TIME_DATE|TIME_MINUTES)),
            DoubleToString(actual, digits), pend);
      }
      else if(t == OBJ_CHANNEL || t == OBJ_STDDEVCHANNEL || t == OBJ_REGRESSION)
      {
         // recolecta valores de las lineas del canal al tiempo actual
         double sup = -1.0, inf = -1.0;
         for(int line = 0; line <= 2; line++)
         {
            double v = ObjectGetValueByTime(chart_id, name, ahora, line);
            if(v <= 0.0) continue;          // 0 => linea inexistente / error
            if(sup < 0.0 || v > sup) sup = v;
            if(inf < 0.0 || v < inf) inf = v;
         }
         if(sup < 0.0) continue;            // canal sin valores utiles
         if(channels != "") channels += ", ";
         channels += StringFormat(
            "{\"name\": \"%s\", \"tipo\": \"%s\", \"banda_superior\": %s, \"banda_inferior\": %s}",
            nm, TipoCanal(t), DoubleToString(sup, digits), DoubleToString(inf, digits));
      }
      else if(t == OBJ_RECTANGLE)
      {
         double a = ObjectGetDouble(chart_id, name, OBJPROP_PRICE, 0);
         double b = ObjectGetDouble(chart_id, name, OBJPROP_PRICE, 1);
         double mn = MathMin(a, b), mx = MathMax(a, b);
         if(rectangles != "") rectangles += ", ";
         rectangles += StringFormat("{\"name\": \"%s\", \"min\": %s, \"max\": %s}",
                                    nm, DoubleToString(mn, digits), DoubleToString(mx, digits));
      }
   }

   // screenshot: ChartScreenShot escribe en MQL5/Files; luego lo copiamos a Common/Files
   string png = SlugSimbolo(symbol) + "_" + tf + "_" + FechaArchivo(ahora) + ".png";
   if(ChartScreenShot(chart_id, png, AnchoPNG, AltoPNG, ALIGN_RIGHT))
      CopiarACommon(png);
   else
      png = "";   // sin screenshot disponible este ciclo

   return StringFormat(
      "    {\"symbol\": \"%s\", \"timeframe\": \"%s\", \"digits\": %d, "
      "\"current_price\": %s, \"screenshot\": \"%s\", "
      "\"hlines\": [%s], \"trendlines\": [%s], \"channels\": [%s], \"rectangles\": [%s]}",
      JsonEscape(symbol), tf, digits, DoubleToString(precio, digits), JsonEscape(png),
      hlines, trendlines, channels, rectangles);
}

//+------------------------------------------------------------------+
//| Recorre todos los charts abiertos y escribe el JSON              |
//+------------------------------------------------------------------+
void ExportarObjetos()
{
   string charts = "";
   long id = ChartFirst();
   while(id >= 0)
   {
      string frag = SerializarChart(id);
      if(frag != "")
      {
         if(charts != "") charts += ",\n";
         charts += frag;
      }
      id = ChartNext(id);
   }

   string generado = FechaIso(TimeToString(TimeCurrent(), TIME_DATE|TIME_MINUTES));
   string json = StringFormat(
      "{\n  \"generated_at\": \"%s\",\n"
      "  \"server_tz_note\": \"hora servidor MT5 (broker actual = hora Chile)\",\n"
      "  \"charts\": [\n%s\n  ]\n}\n", generado, charts);

   int h = FileOpen("chart_objects.json", FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
   if(h != INVALID_HANDLE)
   {
      FileWriteString(h, json);
      FileClose(h);
      Print("ChartObjectsExporter: chart_objects.json escrito.");
   }
   else
      Print("ChartObjectsExporter: error abriendo archivo: ", GetLastError());
}

//+------------------------------------------------------------------+
void OnStart()
{
   while(!IsStopped())
   {
      ExportarObjetos();
      Sleep(RefrescoSegundos * 1000);
   }
}
