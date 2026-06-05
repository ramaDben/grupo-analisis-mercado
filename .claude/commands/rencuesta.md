Desarrolla didácticamente los temas tratados en las encuestas y construye la malla de conceptos del grupo.

## Argumentos
$ARGUMENTS — uno de:
- *(vacío)* → toma la última encuesta de `data/historial_encuestas.json` y desarrolla su concepto.
- `<tema>` → desarrolla/profundiza ese concepto (ej. `confluencia`, `"puntos de interés"`).
- `mapa` → genera la vista visual de la malla actual para repaso.

## Principio
NO es "revelar la respuesta correcta". Es **enseñar el concepto** en voz de cliente nuevo (sin jerga sin explicar) y **mapear** cómo se conecta con otros conceptos. Materializa la misión: pasar de señales a educación. Todo el texto para clientes va en **español chileno neutro** (tuteo: "tú tienes", "tú sabes") — nunca voseo argentino ("tenés", "sabés").

---

## PASO 1 — Resolver el tema

**Si `$ARGUMENTS` es `mapa`** → ir directo al PASO 5.

**Si `$ARGUMENTS` está vacío**:
1. Leer `data/historial_encuestas.json`. **Ignorar los tipos de sentimiento**
   (`posicion`, `tendencia`, `movimiento`, estado `registrada`): no tienen concepto
   educativo que desarrollar. Considerar solo encuestas educativas (las que tienen
   `respuesta_correcta` o trigger educativo, ej. `post_evento`/`educativa`).
2. Tomar la encuesta **educativa** con `fecha` más reciente.
3. Si no hay ninguna encuesta educativa → avisar: "No hay tema educativo pendiente. Usa
   `/rencuesta [tema]` para desarrollar un concepto puntual." y detener.
4. Identificar el/los concepto(s) que trató (de `pregunta`/`opciones`/`trigger`). Normalizar a `id` kebab-case (ej. "stop loss" → `stop-loss`).
5. Si trató varios conceptos, listarlos al director y pedir que elija el central.

**Si `$ARGUMENTS` es un tema** → normalizar a `id` kebab-case (sin tildes, espacios → guiones: "puntos de interés" → `puntos-interes`).

---

## PASO 2 — Cargar estado desde la malla

Leer `data/mapa_conceptos.json`:
- **Nodo no existe** → concepto nuevo, se creará.
- **`estado: "pendiente"`** → primera explicación.
- **`estado: "explicado"`** → leer su `conceptos/<id>.md` (canon) y **profundizar la siguiente capa**, NO repetir lo ya dicho.

---

## PASO 3 — Desarrollar el contenido (fuente anclada)

Redactar el contenido didáctico:
1. **Anclado al repo**: usar los indicadores del `CLAUDE.md` (ATR, RSI, MACD, medias) y los drivers de `docs/activos-y-drivers.md`. Ej.: "stop loss" se explica con el ATR que el grupo usa en USD/CLP, no en abstracto.
2. **Voz novata**: un cliente nuevo lo entiende en < 30 s. Nada de jerga sin explicar. Español chileno neutro (tuteo), nunca voseo argentino.
3. Si ya existe `conceptos/<id>.md`, partir de él y profundizar.
4. `WebSearch` SOLO si hace falta un ejemplo con un dato real reciente (estos conceptos son atemporales — normalmente no se necesita).

Identificar los **conceptos vecinos** que el desarrollo abre (ej. stop-loss `se-apoya-en` confluencia `abre` puntos-interes). Cada vecino = nodo/arista propuesto. Tipos de arista válidos: `se-apoya-en`, `usa`, `abre`, `prerequisito-de`, `relacionado`.

---

## PASO 4 — Proponer al director (aprobación)

Mostrar:
1. El **mensaje WhatsApp** usando `templates/concepto_didactico.txt`:
   - `{NOMBRE_CONCEPTO}`, `{RESUMEN_UNA_LINEA}`, `{QUE_ES}`, `{COMO_APLICA}`, `{ACCION_CONCRETA}`.
   - `{VECINOS}` = nombres legibles separados por ` · ` (ej. `Confluencia · Puntos de interés`).
2. Los **cambios al mapa**: qué nodos se crean, qué aristas se agregan, qué pasa a `explicado`.
3. Preguntar: *"¿Apruebas? ¿Adjuntar chart? ¿Enviar al grupo WhatsApp?"*

> La malla NUNCA se modifica sin aprobación.

**Al aprobar**:
- Escribir/actualizar `conceptos/<id>.md` (frontmatter `id, nombre, estado, encuestas, ancla` + contenido con enlaces `[[vecino]]`).
- Actualizar `data/mapa_conceptos.json`: crear/actualizar el nodo (`estado: "explicado"`, `nota`, `aristas`) y crear los nodos vecinos nuevos en `estado: "pendiente"`.
- Guardar el mensaje con la ruta de `scripts\ruta_mensaje.ps1 -Fecha [FECHA] -Tipo encuesta -Hora [HH-MM]` (transversal → `_general`).
- Si el tema vino de una encuesta, en `data/historial_encuestas.json` poner esa encuesta `estado: "revelada"` y enlazarla (`conceptos/<id>.md` ya la lista en `encuestas`).

---

## PASO 5 — Vista del mapa (`/rencuesta mapa`)

1. Leer `data/mapa_conceptos.json`.
2. Construir un árbol ASCII partiendo de los nodos raíz (los que ningún otro nodo apunta) y descendiendo por las aristas. Etiquetar la flecha con el tipo de arista (ej. `se apoya en →`, `que usa →`).
3. Marcar cada nodo: `✅` si `explicado`, `⏳` si `pendiente`, `🆕` si se creó/explicó en la última corrida.
4. Renderizar dentro de `templates/mapa_conceptos.txt` (`{ARBOL_ASCII}`).
5. Mostrar al director: *"¿Apruebas enviar este mapa de repaso?"*. Al aprobar, guardar con la ruta de `scripts\ruta_mensaje.ps1 -Fecha [FECHA] -Tipo encuesta -Hora [HH-MM]` (transversal → `_general`).

Si el grafo está vacío → avisar que aún no hay conceptos en la malla.

---

## REGLAS
- Voz novata SIEMPRE (regla de oro: < 30 s para un cliente nuevo).
- Español chileno neutro (tuteo). Nunca voseo argentino ("tenés", "sabés").
- Respetar la regla de decimales MT5 si se menciona algún precio.
- Las 6 reglas de formato del `CLAUDE.md` aplican a ambos entregables.
- Nunca enviar nada sin aprobación explícita del director.
- Concepto ya `explicado` → profundizar, no repetir.
- Hora en hora Chile si se menciona algún horario.