Genera la Oportunidad del Día para el equipo de ventas: noticia/evento más relevante del día traducido en una alternativa de inversión accionable (entrada/TP/SL, ticket mínimo, temporalidad), en dos formatos (email + WhatsApp). No genera infografías ni envía automáticamente.

## Rechazo del flag `ejecutivo`

Si los argumentos incluyen `ejecutivo`:
```
ℹ️ /ventas no soporta el modo ejecutivo — su contenido ya es 100% interno para el equipo
comercial, no necesita un guion adicional. Continuando con la Oportunidad del Día normal.
```
Continuar normalmente con el PASO 1 (no abortar).

## PASO 1 — Detectar el evento

1. Llamar `obtener_calendario_macro` para el día de hoy (hora Chile). Si hay un evento agendado de alto impacto ya publicado o próximo en las próximas horas, es candidato principal.
2. Complementar con `WebSearch` de breaking news de las últimas ~2 horas, mismos filtros de prioridad que `/alerta`:
```
1. 🏛️ Bancos centrales: Fed, BCCh, BCE
2. 📊 Datos macro sorpresivos (>0.3 pts vs consenso)
3. 🌍 Geopolítica (Oro/WTI)
4. 💻 Earnings tech fuera de horario normal
5. ⛽ OPEP+ decisiones inesperadas
```
3. Si ninguna fuente entrega un candidato con relevancia suficiente:
```
📊 Sin oportunidad clara hoy.
```
**→ DETENER. No continuar.** Nunca forzar una oportunidad artificial.

## PASO 2 — Activo protagonista

Determinar el único activo más directamente impactado por el evento del PASO 1 (siempre 1 activo, obligatorio — nunca se genera una Oportunidad del Día sin activo asociado).

```
🎯 Activo protagonista: [ticker] — [1 línea de por qué]
```

## PASO 3 — Niveles técnicos

Llamar `mcp__market-data__get_asset_levels(ticker, timeframe)` directamente (sin pedir confirmación manual antes de mostrar el borrador — mismo patrón que `/accion`).

`timeframe` por defecto:
- `"1H"` si el evento es un dato agendado de alto impacto (reacción rápida esperada).
- `"4H"` si el evento tiene inercia mayor (geopolítica, banco central).

El director puede ajustar los niveles propuestos en el PASO 7 (aprobación).

## PASO 4 — Cálculo de CLP y R/R

1. TC USD/CLP: `obtener_precio_actual("USD/CLP")` vía MT5; si falla, usar `WebSearch`.
2. `tamaño_contrato`: intentar `mcp__market-data__get_symbol_spec(ticker).contract_size`; si la tool retorna `{"error": ...}` o el campo no viene, usar la fuente histórica (dato manual / `config/activos.json`).
3. Calcular:
   - `TP_CLP = abs(TP - Entrada) * volumen * TC_USDCLP * tamaño_contrato`
   - `SL_CLP = abs(SL - Entrada) * volumen * TC_USDCLP * tamaño_contrato`
   - `RR = TP_CLP / SL_CLP`
4. Formatear todo precio según `digits` de `config/activos.json` para ese activo.
5. Si `RR < 1.5`:
```
⚠️ Ratio R/R bajo ([RR]). Considera ajustar TP o SL.
```
Esto **no detiene** el comando — es una advertencia informativa que se muestra junto al resto del borrador hasta el paso de aprobación.

## PASO 5 — Ticket mínimo y temporalidad

- **Ticket mínimo**: siempre `$5.000.000 CLP` (constante fija, no preguntar al director, no varía por corrida ni por activo).
- **Temporalidad** (default calculado, confirmable en PASO 7):
  - Evento = dato agendado de alto impacto (ya publicado, reacción inmediata esperada) → `"Intradía"`.
  - Evento = con inercia de 24-48h (decisión de política monetaria, geopolítica, discurso de banco central) → `"24-48 horas"`.
  - Empate/ambiguo → usar `volatilidad`/`nota_volatilidad` del activo en `config/activos.json` como desempate (activo de alta volatilidad → sesgo a `"Intradía"`).

Mostrar el default junto al resto del borrador — se confirma/ajusta en el mismo PASO 7, no como pregunta aparte.

## PASO 6 — Render de las dos piezas

Rellenar `templates/ventas_email.txt` y `templates/ventas_whatsapp.txt` con los mismos datos de fondo (activo, evento, sentido de la operación, entrada/TP/SL en precio y CLP, ticket mínimo, temporalidad). Mostrar ambas piezas, siempre juntas (nunca solo una), rotuladas:

```
📧 EMAIL (equipo de ventas)
[contenido]

📱 WHATSAPP (equipo de ventas)
[contenido]
```

## PASO 7 — Aprobación

Mostrar el borrador completo (PASO 2-6) y preguntar al director:
```
¿Apruebas la Oportunidad del Día?
¿Ajustar niveles o temporalidad?
¿Enviar por correo? ¿Enviar por WhatsApp?
```

- Si pide ajustar niveles/temporalidad: volver al PASO 3/PASO 5 con los nuevos valores y volver a presentar para aprobación.
- "¿Enviar por correo/WhatsApp?" es informativo — no dispara ningún envío automático (Evolution API para WhatsApp no está conectada; no existe integración de email en el proyecto).
- Si el director **no aprueba**: **DETENER. No guardar nada** (ni en `data/historial_ventas.json` ni en `data/mensajes/`).

## PASO 8 — Guardado

Tras aprobar:

1. Guardar el email: `scripts\ruta_mensaje.ps1 -Fecha <hoy> -Activo <ticker> -Tipo "ventas_email" -Hora <HH-mm>`.
2. Guardar el WhatsApp: mismo comando con `-Tipo "ventas_whatsapp"`, misma `-Hora` que el email.
3. Agregar una entrada a `data/historial_ventas.json`:
```json
{
  "id": "[yyyyMMdd-HHmm, hora Chile]",
  "fecha_hora": "[datetime ISO, hora Chile]",
  "activo": "[ticker]",
  "evento": "[1 frase de la noticia/evento detectado]",
  "sentido_operacion": "COMPRA/VENTA",
  "entrada": "[precio]",
  "take_profit": "[precio]",
  "stop_loss": "[precio]",
  "ticket_minimo_clp": 5000000,
  "temporalidad": "[texto confirmado por el director]",
  "email_generado": true,
  "whatsapp_generado": true
}
```

No hay límite semanal sobre este historial (a diferencia de `data/historial_senales.json`) — es un registro de trazabilidad, no un control de cupo.

## REGLAS

- Nunca generar una Oportunidad del Día sin un evento con relevancia suficiente (PASO 1) ni sin un activo protagonista (PASO 2).
- Ticket mínimo SIEMPRE `$5.000.000 CLP`, como texto fijo — nunca placeholder variable.
- Ambas piezas (email + WhatsApp) se generan siempre juntas.
- Sin envío automático — solo texto listo para copiar, igual que el resto del pipeline hasta que Evolution API esté conectada.
- No genera infografías — eso lo conecta otro equipo, fuera de este comando.
- `/ventas` no soporta el flag `ejecutivo` — su contenido ya es 100% interno, no necesita un guion complementario.
- Registro directo y profesional para la audiencia comercial interna (sin obligación de explicar siglas como al cliente final), manteniendo siempre la norma general de evitar dramatización catastrófica.
