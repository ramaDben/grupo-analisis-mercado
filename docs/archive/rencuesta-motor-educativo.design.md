# DISEÑO TÉCNICO — `/rencuesta`: motor educativo + malla de conceptos

## Contexto

La encuesta `educativa` sobre stop loss (`2026-06-02_educativa_USDCLP_stoploss`) tuvo **muy poca participación**. El director lo lee como una señal: el tema **no se domina**. La respuesta no es repetir la encuesta, sino **desarrollar el concepto de forma didáctica** — y al hacerlo se descubre que el stop loss se decide por la **confluencia de puntos de interés**, lo que a su vez abre el concepto **puntos de interés**.

De ahí nace `/rencuesta`: un comando que **desarrolla los temas tratados** en las encuestas y va construyendo una **malla de conceptos relacionados, como un mapa**. Materializa la misión del `CLAUDE.md`: *pasar de un modelo de señales a un modelo de análisis + educación donde el cliente aprende a leer el mercado*.

`/rencuesta` reemplaza y formaliza el `/encuesta revelar [id]` que `encuesta.md` menciona pero **nunca se implementó** — pero con un alcance mayor: no solo revela, **enseña y mapea**.

### Decisiones del director (brainstorming)

- **Foco**: el corazón NO es "revelar la respuesta correcta", sino **desarrollar el tema** y **construir la malla de conceptos**. La revelación es un caso menor.
- **Rol de la malla**: estructura interna persistente en el repo **+** vista visual del mapa compartida periódicamente al cliente como repaso. *(Las dos cosas.)*
- **Disparador**: `/rencuesta` sin argumento → última encuesta del historial. `/rencuesta <tema>` → ese concepto. *(Ambos.)*
- **Estructura de la malla**: **híbrido** — grafo JSON central (`data/mapa_conceptos.json`) para las relaciones + una nota markdown por concepto (`conceptos/<id>.md`) para el contenido didáctico.
- **Fuente de verdad**: Claude redacta el borrador con su conocimiento **anclado al repo** (`CLAUDE.md`, `docs/activos-y-drivers.md`) y a la voz novata del grupo; el director corrige/aprueba; lo aprobado queda en `conceptos/<id>.md` como **canon** y fuente para futuras profundizaciones. *(Modelo anclado + validación.)*

---

## Hallazgos clave

- `data/historial_encuestas.json` ya guarda encuestas con `id, fecha, tipo, activo, pregunta, opciones, estado`. Los tipos pedagógicos (`post_evento`, `educativa`) quedan en `estado: "pendiente_revelacion"`.
  - Las `educativa` **ya traen** `respuesta_correcta` (conceptual, no depende del mercado).
  - Las `post_evento` **no la traen** — depende de cómo reaccionó el activo al día siguiente.
- `encuesta.md` (línea ~192) promete `/encuesta revelar [id_encuesta]` que **no existe como comando**. `/rencuesta` lo cubre.
- El `CLAUDE.md` ya define los indicadores canónicos del grupo (ATR, RSI, MACD, medias móviles) y `docs/activos-y-drivers.md` los drivers — son el **anclaje** obligatorio del contenido educativo (ej. "stop loss" se explica con el ATR que el grupo ya usa en USD/CLP, no en abstracto).
- El proyecto NO tiene aún una carpeta `conceptos/` ni un mapa de conocimiento — son artefactos nuevos.
- Patrón de comandos: interactivos, paso a paso, con flujo de aprobación → guardado en `data/mensajes/YYYY-MM-DD_HH-MM_[tipo].txt`. El tipo `encuesta` ya está permitido; se reutiliza (no se inventa un tipo nuevo).
- Estos conceptos son **atemporales** (análisis técnico), no datos de mercado: `WebSearch` NO es fuente principal — solo entra si un concepto necesita un ejemplo con un dato real reciente.

---

## Componentes

### Nuevo: `.claude/commands/rencuesta.md`

Comando interactivo. Tres modos según argumento:

| Invocación | Acción |
|---|---|
| `/rencuesta` | Toma la **última encuesta** del historial, extrae su(s) concepto(s) y los desarrolla. |
| `/rencuesta <tema>` | Desarrolla/profundiza ese concepto (exista o no en la malla). |
| `/rencuesta mapa` | Genera la **vista visual** del estado actual de la malla para repaso. |

#### PASO 1 — Resolver el tema

- **Sin argumento**: leer `data/historial_encuestas.json`, tomar la encuesta más reciente. Identificar el/los concepto(s) que trató. Si trató varios, listarlos y que el director elija el central.
- **Con `<tema>`**: normalizar a un `id` kebab-case (ej. `"puntos de interés"` → `puntos-interes`).
- **`mapa`**: saltar a PASO 5.

#### PASO 2 — Cargar estado desde la malla

Leer `data/mapa_conceptos.json`:
- Concepto **nuevo** (no existe nodo) → se creará.
- Concepto **`pendiente`** (existe como vecino pero sin nota) → primera explicación.
- Concepto **`explicado`** → **profundizar** la siguiente capa leyendo `conceptos/<id>.md` (no repetir lo ya dicho).

#### PASO 3 — Desarrollar el contenido (fuente anclada)

Redactar el contenido didáctico:
1. Anclado a los indicadores/drivers que el repo ya define (`CLAUDE.md`, `docs/activos-y-drivers.md`).
2. En voz novata — sin jerga sin explicar (regla de estilo del grupo).
3. Si ya existe `conceptos/<id>.md`, partir de él (canon) y profundizar.
4. `WebSearch` solo si hace falta un ejemplo con dato real reciente.

Identificar **conceptos vecinos** que el desarrollo abre (ej. stop-loss → `se-apoya-en` → confluencia → `abre` → puntos-interes). Cada vecino = nodo/arista propuesto.

#### PASO 4 — Proponer al director (aprobación)

Mostrar:
- El **mensaje WhatsApp** (entregable A, formato abajo).
- Los **nodos/aristas** que se agregarían a la malla.
- Pregunta estándar: *"¿Apruebas? ¿Adjuntar chart? ¿Enviar al grupo?"*

> La malla **nunca** se modifica sin aprobación — consistente con todo el proyecto.

**Al aprobar**:
- Escribir/actualizar `conceptos/<id>.md` (nota canónica con frontmatter + enlaces `[[vecino]]`).
- Actualizar `data/mapa_conceptos.json` (nodo + aristas + `estado: "explicado"`).
- Guardar el mensaje en `data/mensajes/YYYY-MM-DD_HH-MM_encuesta.txt`.
- Si el tema vino de una encuesta, marcar esa encuesta `estado: "revelada"` y enlazarla al concepto (`encuestas: [...]`).

#### PASO 5 — Vista del mapa (`/rencuesta mapa`)

Recorrer `data/mapa_conceptos.json` y renderizar un árbol ASCII (entregable B) para compartir como repaso periódico. Marca `✅ explicado` / `🆕 nuevo` / `⏳ pendiente`.

---

### Nuevo: `data/mapa_conceptos.json` (el grafo)

```json
{
  "conceptos": {
    "stop-loss": {
      "nombre": "Stop loss",
      "nota": "conceptos/stop-loss.md",
      "estado": "explicado",
      "encuestas": ["2026-06-02_educativa_USDCLP_stoploss"],
      "aristas": { "se-apoya-en": ["confluencia"], "usa": ["atr", "riesgo"] }
    },
    "confluencia": {
      "nombre": "Confluencia",
      "nota": null,
      "estado": "pendiente",
      "encuestas": [],
      "aristas": { "abre": ["puntos-interes"] }
    },
    "puntos-interes": {
      "nombre": "Puntos de interés",
      "nota": null,
      "estado": "pendiente",
      "encuestas": [],
      "aristas": {}
    }
  }
}
```

**Tipos de arista** (semántica de la relación): `se-apoya-en`, `usa`, `abre`, `prerequisito-de`, `relacionado`. Mantienen el mapa legible y permiten etiquetar la flecha en la vista visual.

**Seed inicial**: el grafo nace sembrado con el caso que motivó la feature — `stop-loss` (ya explicado, enlazado a la encuesta real) → `confluencia` → `puntos-interes`.

---

### Nuevo: carpeta `conceptos/` + notas `<id>.md`

Una nota por concepto. Frontmatter + contenido didáctico canónico:

```markdown
---
id: stop-loss
nombre: Stop loss
estado: explicado
encuestas: [2026-06-02_educativa_USDCLP_stoploss]
ancla: [atr, riesgo]
---

El stop loss es tu "freno de emergencia": cierra la operación si el precio
va en contra, para limitar la pérdida.

No es un número al azar — se decide por la [[confluencia]] de varios
[[puntos-interes]]. En USD/CLP, el [[atr]] te dice cuánto se mueve
normalmente el activo, y de ahí sale una distancia razonable.
```

Los enlaces `[[vecino]]` en el texto reflejan las aristas del grafo (fuente humana-legible de la malla).

---

### Entregable A — mensaje educativo WhatsApp

Respeta las 6 reglas de formato del `CLAUDE.md` (resumen arriba, emojis de color, separadores, negrita solo en jerarquía, above-the-fold, cierre práctico).

```text
🎯 *CONCEPTO — Stop Loss*
━━━━━━━━━━━━━━━━━━━
📌 En 1 línea: tu freno de emergencia que cierra la operación si el precio va en contra.
━━━━━━━━━━━━━━━━━━━
📚 *Qué es*: [explicación simple, 2-3 líneas]
🧩 *Cómo se decide bien*: no es un número al azar — se apoya en la *confluencia* de varios puntos de interés.
🎯 *Para aplicarlo*: [acción concreta, anclada al ATR del grupo]
━━━━━━━━━━━━━━━━━━━
🔗 *Esto conecta con*: Confluencia · Puntos de interés
💬 La próxima encuesta profundiza en uno de estos 👇
```

Plantilla: `templates/concepto_didactico.txt`.
Above-the-fold = título + "en 1 línea" (quien no abre "leer más" igual capta lo esencial).

---

### Entregable B — vista del mapa WhatsApp

```text
🗺️ *MAPA DE CONCEPTOS — repaso*
━━━━━━━━━━━━━━━━━━━
Gestión de riesgo
 └─ Stop loss ✅
     └─ se apoya en → Confluencia ✅
         └─ que usa → Puntos de interés 🆕
━━━━━━━━━━━━━━━━━━━
✅ ya visto · 🆕 nuevo · ⏳ pendiente
```

Plantilla: `templates/mapa_conceptos.txt`.

---

## Flujo de datos

```
/rencuesta [arg]
  │
  ├─ sin arg ─→ historial_encuestas.json (última) ─→ extrae concepto(s)
  ├─ <tema>  ─→ normaliza a id kebab-case
  └─ mapa    ─→ PASO 5 (render árbol) ─→ FIN
                    │
  concepto ─→ mapa_conceptos.json (estado?) ─→ conceptos/<id>.md (canon si existe)
                    │
              desarrollar (anclado a CLAUDE.md + docs/activos-y-drivers.md)
                    │
              detectar vecinos ─→ nodos/aristas propuestos
                    │
              MOSTRAR al director (mensaje + cambios al mapa)
                    │
              aprobar ─→ escribe conceptos/<id>.md
                       ─→ actualiza mapa_conceptos.json
                       ─→ guarda data/mensajes/...encuesta.txt
                       ─→ marca encuesta "revelada" (si aplica)
```

---

## Manejo de errores / edge cases

- **Sin encuestas y sin argumento** → pedir un tema explícito.
- **Concepto ya `explicado`** → profundizar siguiente capa, no repetir (leer la nota canónica primero).
- **Encuesta con varios conceptos** → listar y que el director elija el central.
- **Tema con varios vecinos nuevos** → proponerlos todos pero crear nota solo del concepto central; los vecinos quedan como nodos `pendiente` (se desarrollan en futuras ejecuciones).
- **`mapa` con grafo vacío** → avisar que aún no hay conceptos en la malla.
- **`post_evento` sin respuesta pre-cargada** → `WebSearch` del movimiento real del activo desde la fecha; si fue lateral/ambiguo, revelarlo como tal (también enseña).

---

## Archivos

**Nuevos**:
- `.claude/commands/rencuesta.md` — el comando.
- `data/mapa_conceptos.json` — el grafo (seed: stop-loss → confluencia → puntos-interes).
- `conceptos/stop-loss.md` — primera nota canónica (semilla).
- `templates/concepto_didactico.txt` — plantilla entregable A.
- `templates/mapa_conceptos.txt` — plantilla entregable B.

**Modificados**:
- `.claude/commands/encuesta.md` — la línea del `/encuesta revelar` huérfano → apunta a `/rencuesta`.
- `CLAUDE.md` — lista de comandos (19 → 20) + estructura del proyecto (carpeta `conceptos/`, `data/mapa_conceptos.json`).

---

## Testing / verificación

- **Caso 1 — sin argumento**: con la encuesta de stop loss como última del historial, `/rencuesta` debe extraer `stop-loss`, generar el mensaje educativo anclado al ATR, y proponer las aristas hacia confluencia/puntos-interes.
- **Caso 2 — tema libre**: `/rencuesta confluencia` desarrolla el nodo `pendiente`, crea su nota y lo marca `explicado`.
- **Caso 3 — profundizar**: re-ejecutar `/rencuesta stop-loss` debe leer la nota canónica y profundizar, no repetir.
- **Caso 4 — vista**: `/rencuesta mapa` renderiza el árbol con los estados correctos.
- **Formato**: todos los mensajes cumplen las 6 reglas y la regla de decimales MT5; lenguaje validado como novato (un cliente nuevo lo entiende en < 30 s).

## YAGNI — fuera de alcance (v1)

- Sin generación de imagen del mapa (la vista es ASCII en texto — robusto en WhatsApp).
- Sin métricas de participación automáticas (la decisión de qué profundizar la toma el director).
- Sin cierre de encuestas `tendencia`/`precio` por resultado de mercado (acordado: solo conceptos con contenido educativo).
