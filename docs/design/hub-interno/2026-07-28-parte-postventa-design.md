# Parte de post-venta — diseño

- **Fecha**: 2026-07-28
- **Dominio**: hub interno (ejecutivos / post-venta)
- **Estado**: diseño aprobado por el director, pendiente de plan de implementación
- **Origen**: pedido del director — "un formato para el usuario interno tipo post venta que sea más útil e informativo"

---

## 1. Problema

El repo tiene dos formatos internos, y ambos sirven a la **captación**:

| Formato | Qué hace | Audiencia |
|---|---|---|
| `guion_ejecutivo` (flag `ejecutivo`, `.claude/shared/modo_ejecutivo.md`) | Gancho + para quién + qué decir + objeciones + CTA (abrir cuenta / subir de plan / reactivar) | Ejecutivos de venta |
| `/ventas` | Oportunidad del Día: evento → entrada/TP/SL en CLP, ticket mínimo, temporalidad | Equipo comercial |

No existe nada para **post-venta**: el equipo que atiende al cliente que **ya está adentro y ya opera**. Su trabajo no es convertir, es retener — y las preguntas que recibe son distintas ("¿cierro?", "¿aguanto?", "¿por qué pasó esto?"). Hoy cada ejecutivo improvisa esa respuesta, lo que produce mensajes inconsistentes y, en el peor caso, promesas de dirección que el mercado no cumple.

Esto conecta directo con la misión del proyecto (retención, NPS, reducción de churn) y materializa el HUB INTERNO descrito en `docs/design/motor-como-cerebro-hub-gi.brief.md`.

## 2. Qué se construye

Un comando nuevo `/postventa` que produce **un parte diario consolidado** para el grupo interno de post-venta.

Artefactos:
- `.claude/commands/postventa.md` — el comando.
- `templates/parte_postventa.txt` — la plantilla del parte.
- Entradas nuevas en `CLAUDE.md`: el comando en la tabla de slash commands (25 → 26) y `postventa` en la lista de tipos de archivo de `data/mensajes/`.

Decisiones tomadas con el director:
- **Canal**: WhatsApp del grupo interno (obliga a bloques cortos y a un above-the-fold real).
- **Alcance**: híbrido — desarrollo completo del activo protagonista del evento del día, más una línea por cada otro activo de la rotación.
- **Datos de cliente**: ninguno. La pieza habla por **segmentos genéricos**; el ejecutivo cruza con lo que sabe de su cartera. No depende del CRM ni de la Manager API del bróker (bloqueante externo descrito en el brief del hub).
- **Frecuencia**: una vez al día, típicamente al cierre de la jornada o tras el evento principal. Sin límite duro.

## 3. Estructura de la pieza

Siete bloques, en este orden. El orden es parte del diseño: el bloque 1 es lo que el ejecutivo ve sin abrir el "leer más" de WhatsApp (~200 caracteres visibles).

1. **🚨 La consulta que va a entrar hoy** — una sola pregunta anticipada, con su respuesta en dos líneas. Above the fold.
2. **❓ Preguntas frecuentes de hoy** — 3 preguntas más, cada una con la respuesta **redactada para copiar y adaptar**, no un bullet de tema.
3. **📞 A quién contactar hoy** — por segmento, con la excusa de contacto y qué decir.
4. **🧭 Si tiene posición abierta en \[activo protagonista\]** — escenario vigente, nivel que lo invalida, y cómo hablar del riesgo sin prometer.
5. **📊 Los otros activos, en una línea** — una línea por cada otro activo de la rotación del día: estado y qué decir.
6. **📋 Qué dijimos vs. qué pasó** — contraste entre lo que se envió al grupo y el resultado real, más cómo contarlo al cliente.
7. **⚠️ Lo que NO se promete hoy** — límites explícitos del día.

Encabezado fijo con fecha y hora Chile, y el banner `🔒 INTERNO · NO ENVIAR AL CLIENTE` inmediatamente debajo. Separadores `━━━━━━━━━━━━━━━━━━━` entre bloques, igual que el resto del repo.

### Justificación de los tres puntos no obvios

- **Respuestas redactadas, no temas.** La diferencia entre un formato útil y uno decorativo es que el ejecutivo pueda copiar bajo presión, con el cliente esperando.
- **El bloque 7 no estaba en el pedido original.** Se agrega porque post-venta trabaja bajo presión de retener, y ahí es donde se promete dirección que el mercado no cumple. Es el bloque que protege a GI.
- **El bloque 6 es la razón de que esto sea un comando y no un flag.** Rendir cuentas requiere memoria de lo enviado; un flag pegado a una pieza individual no sabe qué más salió ese día.

## 4. Fuentes de datos

| Bloque | Fuente | Disponible hoy |
|---|---|---|
| 1. Consulta que entra | `data/ultimo_evento.json` + `obtener_calendario_macro` | Sí — ya lo escriben `/dato_macro` y `/noticia` |
| 2. Preguntas frecuentes | Redacción sobre el evento + niveles reales del protagonista | Sí |
| 3. A quién contactar | Catálogo cerrado de segmentos (§5) + evento del día | Sí |
| 4. Posición abierta | `get_asset_levels` del protagonista: niveles para el escenario, ATR para el párrafo de riesgo | Sí |
| 5. Otros activos | `get_asset_levels` × activos de `data/plan_hoy.json` | Sí |
| 6. Qué dijimos vs. qué pasó | Lectura de `data/mensajes/<fecha>/` + campo `actual` del calendario | Sí — histórico existe desde el issue #45 |
| 7. Lo que NO se promete | Guidance del evento + reglas de tono de `CLAUDE.md` | Sí |

Ningún bloque depende de la Manager API del bróker ni del CRM. El comando es construible en su totalidad con lo que el motor ya expone.

## 5. Catálogo cerrado de segmentos

El bloque 3 usa **solo** estas cinco etiquetas, para que el parte no invente segmentos nuevos cada día y el equipo aprenda a reconocerlos:

1. Con exposición al activo protagonista
2. Dormido (no opera hace 2+ semanas)
3. Novato en formación
4. Operador frecuente
5. Con la posición en contra

El quinto es el caso central de post-venta y el que peor se resuelve cuando se improvisa.

## 6. Flujo del comando

1. Obtener la hora de Chile con el reloj del sistema (regla canónica de `CLAUDE.md`, nunca `WebSearch`).
2. Leer `data/ultimo_evento.json` y **validar frescura** (`timestamp` de hoy).
   - Fresco → ese es el evento del día.
   - Desfasado o ausente → avisar al director y preguntar cuál es el evento del día. No inventar uno ni seguir con datos viejos.
3. Activo protagonista = `ultimo_evento.activo`.
4. Llamar `get_asset_levels` del protagonista. Si retorna `{"error": ...}`, pedir los valores manualmente (mismo patrón que `apertura.md` PASO 4A).
5. Leer `data/plan_hoy.json` para los otros activos de la rotación; validar frescura igual que `/encuesta` PASO 2. Si está desfasado, pedir los activos al director. Llamar `get_asset_levels` por cada uno; una fila que falle se pide manual sin abortar el resto.
6. Leer `data/mensajes/<fecha de hoy>/` para reconstruir qué se envió al grupo y armar el bloque 6.
7. Redactar los siete bloques.
8. Mostrar el parte completo al director y pedir aprobación.
9. Al aprobar, guardar (§7). Si no aprueba, no guardar nada.

## 7. Guardado

Ruta construida con el helper determinista, nunca a mano:

```powershell
scripts\ruta_mensaje.ps1 -Fecha "2026-07-28" -Activo "USDCLP" -Tipo "postventa" -Hora "18-20"
# -> data/mensajes/2026-07-28/usdclp/postventa/18-20_postventa.txt
```

`-Activo` es siempre el protagonista del evento. La hora sale del reloj de Chile.

## 8. Guardrails

- Banner `🔒 INTERNO · NO ENVIAR AL CLIENTE` en toda salida, sin excepción.
- **No acepta el flag `ejecutivo`**: su contenido ya es 100% interno, mismo criterio que `/ventas`. Si aparece en los argumentos, avisar y continuar con el flujo normal.
- Nunca nombra clientes concretos — solo las cinco etiquetas de segmento.
- Precios con los `digits` de `config/activos.json`, sin truncar ceros.
- Horas en hora Chile (CLT/CLST).
- Registro directo y profesional para audiencia interna (no exige explicar cada sigla como al cliente), manteniendo la prohibición de dramatización catastrófica de `CLAUDE.md`.
- Sin envío automático: el flujo termina en texto listo para copiar, igual que el resto del pipeline.

## 9. Qué NO hace (YAGNI)

- No lee el CRM (Zoho) ni ninguna base de clientes.
- No ve posiciones reales — eso depende de la Manager API del bróker, bloqueada.
- No genera imagen ni Story.
- No reemplaza al guion ejecutivo: audiencias distintas, trabajos opuestos (captar vs. retener). Ambos coexisten.
- No duplica `/ventas`: ese propone una operación nueva con entrada/TP/SL; este acompaña al cliente que ya opera.

## 10. Criterios de aceptación

1. `/postventa` produce un parte con los siete bloques en el orden especificado.
2. El bloque 1 (consulta + respuesta) cabe en ~200 caracteres.
3. Las respuestas de los bloques 1 y 2 están redactadas en primera persona del ejecutivo, listas para copiar.
4. El bloque 3 usa exclusivamente las cinco etiquetas del catálogo.
5. El bloque 5 tiene una línea por cada activo de `plan_hoy.json` distinto del protagonista.
6. Cuando hubo al menos una pieza enviada ese día, el bloque 6 la cita con su hora. Si no hubo ninguna, el bloque se omite entero (no se rellena con texto vacío).
7. Con `ultimo_evento.json` desfasado, el comando pregunta en vez de inventar el evento.
8. Con el flag `ejecutivo`, avisa que no aplica y continúa.
9. Al aprobar, el archivo queda en `data/mensajes/<fecha>/<activo>/postventa/<hora>_postventa.txt`.
10. Si el director no aprueba, no se escribe nada.

## 11. Riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| El parte queda largo para WhatsApp | Medio — nadie lo lee entero | Alcance híbrido (§2) + bloque 1 above the fold + una línea por activo secundario |
| Los segmentos se vuelven genéricos y el equipo los ignora | Medio | Catálogo cerrado de cinco, ligados al evento del día con excusa de contacto concreta |
| El bloque 6 queda vacío los días sin pieza previa | Bajo | Si no hay pieza enviada ese día, el bloque se omite entero en vez de rellenarse con texto vacío |
| Se filtra al cliente | Alto — contenido interno | Banner obligatorio + carpeta `postventa/` separada + regla explícita de no mezclar con mensajes de cliente |

## 12. Relación con documentos existentes

- `docs/design/motor-como-cerebro-hub-gi.brief.md` — este comando es una pieza concreta del HUB INTERNO descrito ahí.
- `.claude/shared/modo_ejecutivo.md` — contrato del flag `ejecutivo`; **no se modifica**. `/postventa` se suma a la lista de no elegibles.
- `.claude/commands/ventas.md` — precedente del patrón "comando 100% interno que rechaza el flag `ejecutivo`".
