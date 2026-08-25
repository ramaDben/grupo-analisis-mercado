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

Genera el mensaje para WhatsApp y la Story visual asociada (`/story alerta` con `lienzo: "alto"` y bloque `Impulso ADC/ATR`):

```
🎯 Activo: [Nombre del activo protagonista (TICKER)]
📌 Nivel a vigilar: [Precio de resistencia o soporte clave con digits]
⚡ Qué esperar: [1 línea de acción direccional clara: quiebre o rebote hacia nivel objetivo]

━━━━━━━━━━━━━━━━━━━
⚠️ *ALERTA DE MERCADO: [TITULAR DIRECCIONAL]*
🕐 [Hora CLT]

*¿Qué pasó?*
[2 líneas MÁXIMO. Claro y directo. Qué ocurrió técnica y fundamentalmente.]

*Impacto y Drivers Intermercado:*
• 🏛️ *Tasas y Bonos / Macro:* [1 línea explicando el driver soberano o macro que mueve el activo]
• 📊 *Modelo ADC + ATR:* [Explicación pedagógica sin fórmulas matemáticas: canal operativo, impulso proyectado en puntos y capacidad validada frente a la volatilidad de la jornada]
• 📱 *[ACTIVO] (Sesgo Intradía):* *[Alcista/Bajista]* con objetivo técnico en [Nivel R1] y extensión a [Nivel R2].

━━━━━━━━━━━━━━━━━━━
🟢 Sobre [Resistencia] → fuerza compradora hacia [Objetivo / R2]
🟡 Entre [Soporte] y [Resistencia] → consolidación y espera de confirmación
🔴 Bajo [Soporte] → presión vendedora hacia [Soporte 2]
━━━━━━━━━━━━━━━━━━━
```

**Reglas de formato y redacción:**
- **Above-the-fold obligatorio**: Las 3 primeras líneas entregan Activo, Nivel y Qué esperar.
- **Sin fórmulas matemáticas en texto**: Prohibido escribir `1.5 x ATR14`, LaTeX o fórmulas crudas en el mensaje; explicar el concepto cuantitativo en voz pedagógica.
- **Cero guiones largos ni medios**: Prohibido el uso de `—` o `–` en el texto.
- **Formato decimales**: Precios y niveles respetando `config/activos.json` (USD/JPY: 3 decimales, USD/CLP: 2 decimales, US100: 2 decimales).
- **Gráfico de Story Alerta**: Utilizar estrictamente temporalidad H1 (60 velas) con `lienzo: "alto"` y el token `vol_pct` configurado con el impulso en puntos para el bloque `Impulso ADC/ATR`.

## PASO 5: Aprobación y envío
1. Muestra el mensaje de WhatsApp y el preview de la Story al director.
2. Pregunta: "¿Apruebas? ¿Generar Story final y guardar para enviar?"
3. Al aprobar:
   - Guarda el mensaje con `scripts\ruta_mensaje.ps1 -Tipo "alerta"`.
   - Genera y guarda la Story PNG (horizontal y vertical) con `scripts\ruta_story.ps1 -Plantilla "alerta"`.
   - Muestra el texto listo para copiar.
