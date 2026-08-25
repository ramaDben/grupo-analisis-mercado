Busca automáticamente qué está moviendo el mercado AHORA y genera una alerta conectada con el motor cuantitativo de sesgo macro.

## PASO 1: Detectar eventos en tiempo real

Busca eventos de las últimas 2 horas que impacten nuestros activos:
- Consulta `get_macro_bias` o lee `data central/DATA DRIVERS USDCLP/macro_bias_output.json` y `data central/DATA AGENDA/estado_ejecucion.json`.
- Con `WebSearch` detecta breaking news de las últimas ~2 horas (Fed, BoJ, BCCh, datos sorpresivos, geopolítica) sobre fuentes oficiales.
- Si no hay eventos recientes que muevan el mercado: informar al director "Sin eventos relevantes en este momento" y DETENER el comando.

**Filtros de prioridad**:
1. 🏛️ Bancos centrales: Fed, BCCh, BoJ, BCE: discursos, declaraciones o decisiones de emergencia.
2. 📊 Datos macro sorpresivos: IPC, NFP, PCE, PMI fuera del consenso por >0.3 puntos.
3. 🌍 Geopolítica: tensiones que afecten Oro o WTI.
4. 💻 Earnings tech: resultados fuera del horario normal.
5. ⛽ OPEP+: decisiones de producción inesperadas.

## PASO 2: Evaluar si hay evento real

**Si NO hay eventos relevantes**:
```
📊 Sin eventos de alto impacto en las últimas 2 horas.
Mercados operando con normalidad.

Próximos datos: [listar 1-2 datos del calendario de hoy/mañana con hora CLT]
```

**Si HAY evento(s)**: continuar al PASO 3.

## PASO 3: Validar: ¿ya se envió esta alerta?
Verifica si en la sesión actual ya se generó una alerta sobre el mismo evento (no repetir en menos de 1 hora).

## PASO 4: Generar la alerta

```
⚠️ *ALERTA DE MERCADO*
━━━━━━━━━━━━━━━━━━━
🕐 [Hora CLT]

*¿Qué pasó?*
[2 líneas MÁXIMO. Claro y directo. Qué ocurrió y dónde.]

*¿Cómo afecta nuestros activos?*
🇨🇱 USD/CLP: *Alcista/Bajista*: [1 línea explicando por qué] (impacto estimado: ~Xh)
🇯🇵 USD/JPY: *Alcista/Bajista*: [1 línea explicando por qué] (impacto estimado: ~Xh)
🥇 Oro: *Alcista/Bajista*: [1 línea] (impacto estimado: ~Xh)
⛽ WTI: *Alcista/Bajista*: [1 línea si aplica] (impacto estimado: ~Xh)
📱 US100: *Alcista/Bajista*: [1 línea si aplica] (impacto estimado: ~Xh)
[Incluir solo los activos realmente impactados]

[Si aplica: conexión con escenario macro]
_[Ej: "Esto refuerza el escenario de recorte de tasas de la Fed"]_

━━━━━━━━━━━━━━━━━━━
🟢 *Alcista*: [qué nivel tendría que superar para activar impulso comprador]
🟡 *Esperar*: [rango base de oscilación sin sorpresas]
🔴 *Bajista*: [qué soporte activaría presión vendedora]
━━━━━━━━━━━━━━━━━━━
```

**Tono**: urgente pero NO alarmista. Mentor confiable informando.
**Cero guiones largos**: Prohibido el uso de `—` o `–` en el texto.
**Formato decimales**: Precios y niveles respetando `config/activos.json` (USD/JPY: 3 decimales, USD/CLP: 2 decimales).

## PASO 5: Aprobación y envío
Pregunta al director: "¿Apruebas? ¿Enviar al grupo WhatsApp?"
Al aprobar, muestra el texto listo para copiar.
