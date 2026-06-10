//+------------------------------------------------------------------+
//| CalendarExporter.mq5                                             |
//| Service: exporta el calendario macro nativo de MT5 a un JSON    |
//| en Common/Files cada hora. Lo consume el MCP market-data.       |
//| Issue #53.                                                       |
//+------------------------------------------------------------------+
#property service
#property strict

input int RefrescoSegundos = 3600;   // refresh cada 1 h (issue #53)

//--- mapea importancia MT5 a etiqueta del proyecto
string ImpactoStr(ENUM_CALENDAR_EVENT_IMPORTANCE imp)
{
   if(imp == CALENDAR_IMPORTANCE_HIGH)     return("alto");
   if(imp == CALENDAR_IMPORTANCE_MODERATE) return("medio");
   return("bajo");
}

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

void ExportarCalendario()
{
   datetime ahora = TimeTradeServer();
   datetime inicio = ahora - 12*3600;   // ventana: hoy +/- margen
   datetime fin    = ahora + 36*3600;

   MqlCalendarValue values[];
   int n = CalendarValueHistory(values, inicio, fin);

   string eventos = "";
   for(int i = 0; i < n; i++)
   {
      MqlCalendarEvent ev;
      if(!CalendarEventById(values[i].event_id, ev)) continue;
      if(ev.importance == CALENDAR_IMPORTANCE_NONE) continue;  // filtra ruido

      MqlCalendarCountry pais;
      CalendarCountryById(ev.country_id, pais);

      string nombre  = JsonEscape(ev.name);          // ya localizado al idioma del terminal
      string paisStr = JsonEscape(pais.name);
      string divisa  = JsonEscape(pais.currency);
      string periodo = JsonEscape(FechaIso(TimeToString(values[i].period, TIME_DATE)));
      string hora    = FechaIso(TimeToString(values[i].time, TIME_DATE|TIME_MINUTES));

      string previo   = values[i].HasPreviousValue() ? DoubleToString(values[i].GetPreviousValue(), 2) : "";
      string forecast = values[i].HasForecastValue() ? DoubleToString(values[i].GetForecastValue(), 2) : "";
      string actual   = values[i].HasActualValue()   ? DoubleToString(values[i].GetActualValue(), 2)   : "null";

      if(eventos != "") eventos += ",\n";
      eventos += StringFormat(
         "    {\"event_id\": %I64u, \"nombre\": \"%s\", \"pais\": \"%s\", \"divisa\": \"%s\", "
         "\"impacto\": \"%s\", \"hora_servidor\": \"%s\", \"periodo\": \"%s\", "
         "\"previo\": \"%s\", \"forecast\": \"%s\", \"actual\": %s}",
         ev.id, nombre, paisStr, divisa, ImpactoStr(ev.importance), hora, periodo,
         previo, forecast, (actual == "null" ? "null" : "\"" + actual + "\""));
   }

   string generado = FechaIso(TimeToString(ahora, TIME_DATE|TIME_MINUTES));
   string json = StringFormat(
      "{\n  \"generated_at\": \"%s\",\n"
      "  \"server_tz_note\": \"hora servidor MT5 (broker actual = hora Chile)\",\n"
      "  \"eventos\": [\n%s\n  ]\n}\n", generado, eventos);

   //--- FILE_COMMON => Common/Files, accesible por el MCP
   int h = FileOpen("calendario_macro.json", FILE_WRITE|FILE_TXT|FILE_ANSI|FILE_COMMON);
   if(h != INVALID_HANDLE)
   {
      FileWriteString(h, json);
      FileClose(h);
      Print("CalendarExporter: calendario_macro.json escrito (", n, " valores).");
   }
   else
      Print("CalendarExporter: error abriendo archivo: ", GetLastError());
}

void OnStart()
{
   while(!IsStopped())
   {
      ExportarCalendario();
      Sleep(RefrescoSegundos * 1000);
   }
}
