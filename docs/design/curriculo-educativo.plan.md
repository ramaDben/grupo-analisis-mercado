# Currículo Educativo Evolutivo — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir la capa proactiva del subsistema educativo (comando `/curriculo` + 4 capas de datos) para correr la beta en WhatsApp.

**Architecture:** 4 capas de datos JSON (conocimiento / ruta / entrega / métricas) sobre el grafo existente `mapa_conceptos.json`, más un comando markdown `/curriculo` que reutiliza `/rencuesta` y `/concepto` para entregar. Todo aditivo: `/rencuesta` no se toca.

**Tech Stack:** Slash commands de Claude Code (markdown) + archivos de datos JSON. Verificación = validez JSON (`node -e` / `python -m json.tool`) + escenarios manuales (no hay test harness automático en el repo).

**Spec:** `docs/design/curriculo-educativo.design.md`

---

### Task 1: Capa 1 — extender `mapa_conceptos.json`

**Files:**
- Modify: `data/mapa_conceptos.json`

- [ ] **Step 1: Añadir campos a los 3 nodos existentes + 7 nodos nivel-1 nuevos**

Reescribir `data/mapa_conceptos.json` con `tipo`, `nivel`, `glosario` en cada nodo y aristas `prerequisito-de`. Los 3 nodos actuales (`stop-loss`, `confluencia`, `puntos-interes`) se enriquecen; se agregan `leer-un-grafico`, `velas`, `temporalidades`, `tendencia`, `soporte-resistencia`, `volatilidad-atr`, `riesgo`.

```json
{
  "conceptos": {
    "leer-un-grafico": { "nombre": "Leer un gráfico", "tipo": "tecnico", "nivel": 1, "glosario": "Qué muestra un gráfico: precio, tiempo y velas.", "nota": null, "estado": "pendiente", "anclas": [], "encuestas": [], "aristas": { "prerequisito-de": ["velas", "temporalidades", "tendencia"] } },
    "velas": { "nombre": "Velas japonesas", "tipo": "tecnico", "nivel": 1, "glosario": "Cada vela resume el precio de un periodo: cuerpo y mechas.", "nota": null, "estado": "pendiente", "anclas": [], "encuestas": [], "aristas": {} },
    "temporalidades": { "nombre": "Temporalidades", "tipo": "tecnico", "nivel": 1, "glosario": "15M/1H/4H/1D: cada una implica una operativa distinta.", "nota": null, "estado": "pendiente", "anclas": [], "encuestas": [], "aristas": {} },
    "tendencia": { "nombre": "Tendencia", "tipo": "tecnico", "nivel": 1, "glosario": "Hacia dónde va el precio: alcista, bajista o lateral.", "nota": null, "estado": "pendiente", "anclas": [], "encuestas": [], "aristas": { "prerequisito-de": ["soporte-resistencia", "volatilidad-atr"] } },
    "soporte-resistencia": { "nombre": "Soporte y resistencia", "tipo": "tecnico", "nivel": 1, "glosario": "Niveles donde el precio suele reaccionar.", "nota": null, "estado": "pendiente", "anclas": [], "encuestas": [], "aristas": { "prerequisito-de": ["puntos-interes"] } },
    "puntos-interes": { "nombre": "Puntos de interés", "tipo": "tecnico", "nivel": 1, "glosario": "Zonas clave a vigilar en el gráfico.", "nota": null, "estado": "pendiente", "anclas": [], "encuestas": [], "aristas": { "prerequisito-de": ["confluencia"] } },
    "confluencia": { "nombre": "Confluencia", "tipo": "tecnico", "nivel": 1, "glosario": "Varios factores apuntando al mismo nivel.", "nota": null, "estado": "pendiente", "anclas": [], "encuestas": [], "aristas": { "prerequisito-de": ["stop-loss"] } },
    "volatilidad-atr": { "nombre": "Volatilidad (ATR)", "tipo": "tecnico", "nivel": 1, "glosario": "Cuánto se mueve normalmente el activo; clave en USD/CLP.", "nota": null, "estado": "pendiente", "anclas": ["atr"], "encuestas": [], "aristas": {} },
    "riesgo": { "nombre": "Riesgo", "tipo": "tecnico", "nivel": 1, "glosario": "Cuánto estás dispuesto a perder en una operación.", "nota": null, "estado": "pendiente", "anclas": ["riesgo"], "encuestas": [], "aristas": { "prerequisito-de": ["stop-loss"] } },
    "stop-loss": { "nombre": "Stop loss", "tipo": "tecnico", "nivel": 1, "glosario": "Tu freno de emergencia: cierra la operación si el precio va en contra.", "nota": "conceptos/stop-loss.md", "estado": "explicado", "anclas": ["atr", "riesgo"], "encuestas": ["2026-06-02_educativa_USDCLP_stoploss"], "aristas": { "se-apoya-en": ["confluencia"], "usa": ["atr", "riesgo"], "relacionado": ["puntos-interes"] } }
  }
}
```

- [ ] **Step 2: Validar que el JSON parsea**

Run: `node -e "JSON.parse(require('fs').readFileSync('data/mapa_conceptos.json','utf8')); console.log('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add data/mapa_conceptos.json
git commit -m "feat(curriculo): extiende el grafo con tipo/nivel/glosario + nodos nivel 1"
```

---

### Task 2: Capa 2 — crear `data/curriculo.json`

**Files:**
- Create: `data/curriculo.json`

- [ ] **Step 1: Crear la ruta novato con la secuencia completa (validada contra el DAG)**

El orden respeta los `prerequisito-de` del grafo: cada concepto va después de sus prerrequisitos.

```json
{
  "rutas": {
    "novatos": {
      "nombre": "Ruta Novato",
      "nivel": 1,
      "descripcion": "Primeros pasos: leer el mercado sin perderse.",
      "secuencia": [
        { "concepto": "leer-un-grafico",     "semana_objetivo": "2026-W24", "estado": "planificado" },
        { "concepto": "velas",               "semana_objetivo": "2026-W24", "estado": "planificado" },
        { "concepto": "temporalidades",      "semana_objetivo": "2026-W24", "estado": "planificado" },
        { "concepto": "tendencia",           "semana_objetivo": "2026-W25", "estado": "planificado" },
        { "concepto": "soporte-resistencia", "semana_objetivo": "2026-W25", "estado": "planificado" },
        { "concepto": "puntos-interes",      "semana_objetivo": "2026-W26", "estado": "planificado" },
        { "concepto": "confluencia",         "semana_objetivo": "2026-W26", "estado": "planificado" },
        { "concepto": "volatilidad-atr",     "semana_objetivo": "2026-W27", "estado": "planificado" },
        { "concepto": "riesgo",              "semana_objetivo": "2026-W27", "estado": "planificado" },
        { "concepto": "stop-loss",           "semana_objetivo": "2026-W27", "estado": "entregado" }
      ]
    }
  },
  "actualizado": "2026-06-02"
}
```

- [ ] **Step 2: Validar JSON + chequear orden de prerrequisitos a mano**

Run: `node -e "JSON.parse(require('fs').readFileSync('data/curriculo.json','utf8')); console.log('OK')"`
Expected: `OK`. Confirmar que cada concepto aparece después de sus prerrequisitos (ej. `stop-loss` después de `riesgo` y `confluencia`).

- [ ] **Step 3: Commit**

```bash
git add data/curriculo.json
git commit -m "feat(curriculo): siembra la ruta novato (Capa 2)"
```

---

### Task 3: Capa 3 y 4 — archivos de entregas y métricas

**Files:**
- Create: `data/entregas_educativas.json`
- Create: `data/metricas_educativas.json`

- [ ] **Step 1: Crear `data/entregas_educativas.json` con la entrega real de stop-loss**

```json
{
  "entregas": [
    {
      "id": "2026-06-02_stop-loss_whatsapp",
      "concepto": "stop-loss",
      "ruta": "novatos",
      "canal": "whatsapp",
      "fecha": "2026-06-02",
      "mensaje": null,
      "encuesta": "2026-06-02_educativa_USDCLP_stoploss",
      "comando_origen": "rencuesta"
    }
  ]
}
```

- [ ] **Step 2: Crear `data/metricas_educativas.json` vacío**

```json
{
  "snapshots": []
}
```

- [ ] **Step 3: Validar ambos JSON**

Run: `node -e "['data/entregas_educativas.json','data/metricas_educativas.json'].forEach(f=>JSON.parse(require('fs').readFileSync(f,'utf8'))); console.log('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add data/entregas_educativas.json data/metricas_educativas.json
git commit -m "feat(curriculo): archivos de entregas y metricas (Capas 3 y 4)"
```

---

### Task 4: Templates de salida

**Files:**
- Create: `templates/ruta_curriculo.txt`
- Create: `templates/dashboard_metricas.txt`

- [ ] **Step 1: Crear `templates/ruta_curriculo.txt`** (roadmap WhatsApp, 6 reglas de formato)

```text
🗺️ *RUTA EDUCATIVA — {NOMBRE_RUTA}*
━━━━━━━━━━━━━━━━━━━
{DESCRIPCION_RUTA}
━━━━━━━━━━━━━━━━━━━
{ARBOL_RUTA}
━━━━━━━━━━━━━━━━━━━
✅ visto · 🆕 nuevo · ⏳ planificado
📌 Próximo: {PROXIMO_CONCEPTO}
```

- [ ] **Step 2: Crear `templates/dashboard_metricas.txt`** (uso interno del directorio)

```text
📊 *DASHBOARD EDUCATIVO — semana {SEMANA}*
━━━━━━━━━━━━━━━━━━━
👥 Participación: {VOTOS_PROMEDIO} votos/encuesta ({N_ENCUESTAS} encuestas)
🧠 Comprensión: {ACIERTOS_PCT}% de aciertos
📚 Cobertura: {COBERTURA_PCT}% ({ENTREGADOS}/{TOTAL}) · N1 {N1} · N2 {N2} · N3 {N3}
😊 Satisfacción: {SATISFACCION} ({RESPUESTAS} respuestas, {CANAL})
━━━━━━━━━━━━━━━━━━━
```

- [ ] **Step 3: Commit**

```bash
git add templates/ruta_curriculo.txt templates/dashboard_metricas.txt
git commit -m "feat(curriculo): templates de ruta y dashboard"
```

---

### Task 5: El comando `.claude/commands/curriculo.md`

**Files:**
- Create: `.claude/commands/curriculo.md`

- [ ] **Step 1: Escribir el comando con los 5 modos**

Seguir el patrón de `.claude/commands/rencuesta.md` (interactivo, paso a paso, aprobación → guardado). Contenido:

```markdown
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
```

- [ ] **Step 2: Verificación de escenario (manual)**

Leer el comando y simular mentalmente: con la ruta sembrada, modo vacío recomienda `leer-un-grafico` (sin prereqs, primer `planificado`). `despachar confluencia` debe bloquear porque `puntos-interes` no está `entregado`. `agregar confluencia` antes de `puntos-interes` debe rechazarse.
Expected: las 3 ramas se comportan según el spec.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/curriculo.md
git commit -m "feat(curriculo): comando /curriculo con 5 modos"
```

---

### Task 6: Actualizar `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md` (sección "Slash Commands disponibles" y "Estructura del proyecto")

- [ ] **Step 1: Subir el conteo 20 → 21 y agregar `/curriculo` a la tabla Capa 2**

Añadir fila en la tabla "Capa 2 — Comandos de tarea (ad hoc)":

```markdown
| `/curriculo` | Planifica el currículo educativo evolutivo (niveles + prerrequisitos), despacha conceptos en orden reutilizando `/rencuesta`/`/concepto` y mide el avance (4 métricas). Modos: `/curriculo`, `despachar`, `ruta`, `progreso`, `agregar`. |
```

Cambiar el encabezado "## Slash Commands disponibles (20)" a "(21)".

- [ ] **Step 2: Reflejar los archivos nuevos en el árbol de "Estructura del proyecto"**

Agregar bajo `data/`: `curriculo.json`, `entregas_educativas.json`, `metricas_educativas.json`; bajo `templates/`: `ruta_curriculo.txt`, `dashboard_metricas.txt`; bajo `.claude/commands/`: `curriculo.md`.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(curriculo): registra /curriculo y archivos nuevos en CLAUDE.md"
```

---

## Self-Review

- **Spec coverage**: Capa 1 → Task 1; Capa 2 → Task 2; Capas 3-4 → Task 3; templates → Task 4; comando 5 modos → Task 5; CLAUDE.md (comando 20→21 + estructura) → Task 6. Sin huecos.
- **Placeholder scan**: cada tarea trae el contenido real (JSON completo, texto de templates, cuerpo del comando). Sin TBD/TODO.
- **Type consistency**: nombres de campos consistentes con el spec (`tipo`, `nivel`, `glosario`, `aristas.prerequisito-de`, `secuencia[].estado`, `entregas[].canal`, `snapshots[]`). Estados usados: nodo `pendiente|explicado`; item de ruta `planificado|entregado`.

## Notas de verificación del repo

No hay test runner automático para slash commands. La verificación es: (1) `node -e "JSON.parse(...)"` para cada archivo de datos, (2) recorrido manual de los escenarios del spec (Casos 1-5). Si se prefiere Python: `python -m json.tool <archivo> > NUL`.
