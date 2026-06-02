Planifica el currículo educativo evolutivo del grupo y despacha conceptos en orden, midiendo el avance.

## Argumentos
$ARGUMENTS — uno de:
- *(vacío)* → estado de la ruta + recomendación del próximo concepto.
- `despachar <concepto>` → despacha ese concepto (delega en /rencuesta o /concepto).
- `ruta` → render del roadmap completo para el grupo / directorio.
- `progreso` → snapshot de las 4 métricas + dashboard.
- `agregar <concepto>` → cura la ruta (añadir/reordenar), validando prerrequisitos.

## Principio
El currículo es el cerebro; /rencuesta y /concepto son las manos. La ruta la cura el director (su visión); el sistema impide violar prerrequisitos. Voz novata, español chileno neutro (tuteo), 6 reglas de formato del CLAUDE.md, decimales MT5. Nada se envía sin aprobación.

## PASO 1 — Resolver modo
Leer $ARGUMENTS y ramificar a uno de los modos de abajo.

## MODO vacío — Estado + recomendación
1. Leer `data/curriculo.json` (ruta `novatos`) y `data/mapa_conceptos.json`.
2. Próximo recomendado = primer item con `estado: "planificado"` cuyos `prerequisito-de` (mirados en el grafo, es decir, los conceptos que lo tienen como destino) estén todos `entregado` en la ruta.
3. Mostrar: dónde va la ruta (entregados/total) y el próximo recomendado. Preguntar: "¿Lo despachamos con /curriculo despachar <concepto>?"

## MODO despachar <concepto>
1. Validar que los prerrequisitos del concepto estén `entregado`. Si falta alguno → avisar cuál y ofrecer despacharlo primero. No continuar.
2. Elegir delegado: si el concepto es nuevo o `pendiente` en el grafo → `/rencuesta <concepto>`; si es para el "concepto de la semana" del lunes → `/concepto`.
3. Ejecutar el delegado (genera el mensaje WhatsApp + nota canónica si aplica) y pasar por su flujo de aprobación.
4. **Al aprobar**:
   - Agregar registro a `data/entregas_educativas.json` (`concepto`, `ruta`, `canal: "whatsapp"`, `fecha`, `mensaje` = ruta del archivo guardado, `encuesta` si aplica, `comando_origen`).
   - En `data/curriculo.json`, poner ese item `estado: "entregado"`.
   - En `data/mapa_conceptos.json`, si el nodo era `pendiente`, dejarlo `explicado` (lo hace /rencuesta).

## MODO ruta
1. Leer `data/curriculo.json` + `data/mapa_conceptos.json`.
2. Construir un árbol/lista ASCII por nivel siguiendo la secuencia. Marca: ✅ `entregado`, ⏳ `planificado`, 🆕 si se entregó en la última corrida.
3. Renderizar dentro de `templates/ruta_curriculo.txt` (`{NOMBRE_RUTA}`, `{DESCRIPCION_RUTA}`, `{ARBOL_RUTA}`, `{PROXIMO_CONCEPTO}`).
4. Mostrar al director: "¿Apruebas enviar esta ruta?". Al aprobar, guardar en `data/mensajes/YYYY-MM-DD_HH-MM_concepto.txt`.

## MODO progreso
1. **Cobertura (automática)**: contar nodos `explicado` vs total y por `nivel` en `data/mapa_conceptos.json`.
2. **Participación / Comprensión / Satisfacción**: pedir al director los números de la semana (votos promedio, % aciertos, valor de satisfacción + nº respuestas + canal).
3. Escribir un snapshot nuevo en `data/metricas_educativas.json` (`fecha`, `semana` ISO, los 4 bloques).
4. Renderizar `templates/dashboard_metricas.txt` y mostrarlo (uso interno del directorio; no se envía al grupo salvo que el director lo pida).

## MODO agregar <concepto>
1. Normalizar a `id` kebab-case.
2. Validar contra el DAG: los prerrequisitos del concepto deben quedar antes en la secuencia. Si rompe el orden → rechazar con el detalle.
3. Insertar/reordenar el item en `data/curriculo.json` (`estado: "planificado"`, `semana_objetivo` propuesta). Si el nodo no existe en el grafo, avisar que se creará al despacharlo.

## REGLAS
- Voz novata SIEMPRE (< 30 s para un cliente nuevo). Español chileno neutro (tuteo), nunca voseo argentino.
- La ruta y el grafo NUNCA se modifican sin aprobación.
- Nunca enviar nada al grupo sin aprobación explícita.
- Respetar decimales MT5 y hora Chile si se mencionan precios/horarios.
- No violar jamás el orden de prerrequisitos.
