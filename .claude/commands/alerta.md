Busca automáticamente qué está moviendo el mercado AHORA y genera una alerta para el grupo.

## PASO 1 — Detectar eventos en tiempo real

Busca eventos de las últimas 2 horas que impacten nuestros activos:
- Con `WebSearch` detecta breaking news de las últimas ~2 horas (Fed, datos sorpresivos, geopolítica, earnings) sobre investing.com + fuentes oficiales.
- Si no hay eventos recientes que muevan el mercado: informar al director "Sin eventos relevantes en este momento" y DETENER el comando.

**Filtros de prioridad** (en orden):
1. 🏛️ Bancos centrales: Fed, BCCh, BCE — cualquier discurso, declaración, decisión
2. 📊 Datos macro sorpresivos: IPC, NFP, PCE, PMI fuera del consenso por >0.3 puntos
3. 🌍 Geopolítica: tensiones que afecten Oro o WTI (Oriente Medio, Rusia, etc.)
4. 💻 Earnings tech: resultados de Nvidia, Apple, Microsoft, Amazon fuera del horario normal
5. ⛽ OPEP+: decisiones de producción inesperadas

## PASO 2 — Evaluar si hay evento real

**Si NO hay eventos relevantes** (mercados normales):
```
📊 Sin eventos de alto impacto en las últimas 2 horas.
Mercados operando con normalidad.

Próximos datos: [listar 1-2 datos del calendario de hoy/mañana con hora CLT]
```
Mostrar este mensaje al director. Preguntar si igualmente desea enviar al grupo.

**Si HAY evento(s)**: continuar al PASO 3.

## PASO 3 — Validar: ¿ya se envió esta alerta?

Verifica si en la sesión actual ya se generó una alerta sobre el mismo evento (no repetir la misma alerta en 1 hora).

Si es repetición: avisar al director "Ya se generó alerta sobre este evento hace menos de 1 hora."

## PASO 4 — Generar la alerta

```
⚠️ *ALERTA DE MERCADO*
━━━━━━━━━━━━━━━━━━━
🕐 [Hora CLT]

*¿Qué pasó?*
[2 líneas MÁXIMO. Claro y directo. Qué ocurrió y dónde.]

*¿Cómo afecta nuestros activos?*
🇨🇱 USD/CLP: *Alcista/Bajista* — [1 línea explicando por qué] (impacto estimado: ~Xh)
🥇 Oro: *Alcista/Bajista* — [1 línea] (impacto estimado: ~Xh)
⛽ WTI: *Alcista/Bajista* — [1 línea si aplica] (impacto estimado: ~Xh)
📱 US100: *Alcista/Bajista* — [1 línea si aplica] (impacto estimado: ~Xh)
[Incluir solo los activos realmente impactados]

[Si aplica: conexión con escenario macro]
_[Ej: "Esto refuerza/complica el escenario de recorte de tasas de la Fed"]_

━━━━━━━━━━━━━━━━━━━
🟢 *Alcista* (intra-day): [qué tendría que pasar]
🟡 *Esperar* (base): [qué se espera si no hay más sorpresas]
🔴 *Bajista* (intra-day): [qué activaría más caída/alza adversa]
━━━━━━━━━━━━━━━━━━━
```

**Tono**: urgente pero NO alarmista. El objetivo es informar, no generar pánico.

## PASO 5 — Aprobación y envío

"⚠️ Esta alerta tiene tono fuerte — revisar antes de enviar. ¿Apruebas? ¿Enviar al grupo WhatsApp?"

Si aprueba: llama MCP WhatsApp con prioridad urgente.
Si MCP no disponible: muestra texto listo para copiar.

## PASO 6 — Encadenar encuesta post-evento (reactivo)

Después de enviar la alerta, registrar el evento y ofrecer la encuesta pedagógica. La alerta es el detonante natural de una encuesta de causa-efecto: el grupo acaba de recibir un evento caliente.

1. Escribir/actualizar `data/ultimo_evento.json` con el evento de la alerta:
```json
{
  "tipo": "alerta",
  "activo": "[ticker del activo principal impactado]",
  "evento": "[qué pasó, en 1 frase corta]",
  "dato_real": "[valor si aplica, ej: dato sorpresivo; si no, null]",
  "dato_esperado": "[consenso si aplica, si no null]",
  "timestamp": "[datetime actual ISO]"
}
```
2. Preguntar al director:
   > "📊 La alerta ya salió. ¿Lanzo la encuesta post-evento para que el grupo razone qué debería pasar con *[activo]*? (s/n)"
3. Si responde que sí → ejecutar el flujo de `/encuesta post_evento [activo] "[qué pasó]"`: genera las 3 opciones causa-efecto y guarda en `data/historial_encuestas.json`.
4. Si responde que no → terminar sin generar encuesta.

**No encadenar automáticamente sin preguntar:** tras una alerta urgente el director puede preferir esperar a que el mercado reaccione antes de abrir la encuesta.

## Modo ejecutivo (flag `ejecutivo`)

Si `ejecutivo` aparece en los argumentos, además del mensaje de cliente genera el **guion de venta interno** siguiendo `.claude/shared/modo_ejecutivo.md` (formato, banner `🔒 INTERNO · NO ENVIAR AL CLIENTE`, flujo de aprobación y guardrails). Para esta pieza:
- **Tipo de guion**: `guion_alerta`.
- **`-Activo`**: el ticker del activo principal impactado.
- Mismo `-Hora` que el mensaje de cliente.

Muestra ambas salidas rotuladas `📤 MENSAJE CLIENTE` y `🔒 GUION EJECUTIVO`; al aprobar, guarda el guion con `scripts\ruta_mensaje.ps1`.

## REGLAS
- No repetir la misma alerta en 1 hora.
- Máximo 2 líneas para "qué pasó".
- Solo incluir activos realmente impactados.
- Tono: mentor confiable informando, no alarmista.
- Si hay chart relevante (ej: WTI tras decisión OPEP), ofrecer adjuntarlo.
- **Dirección explícita**: SIEMPRE usar `*Alcista* 🟢` o `*Bajista* 🔴` por activo — nunca "puede subir/bajar" ni "podría moverse".
- **Temporalidad obligatoria**: incluir `(impacto estimado: ~Xh)` por cada activo y horizonte `(intra-day)` en los escenarios. Si no se puede determinar: `*Esperar confirmación* 🟡`.
