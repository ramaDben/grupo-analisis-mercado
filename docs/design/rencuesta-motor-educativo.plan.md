# `/rencuesta` — Motor educativo + malla de conceptos — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Crear el comando `/rencuesta` que desarrolla didácticamente los temas de las encuestas y construye una malla de conceptos persistente (grafo JSON + notas markdown), con vista visual de repaso.

**Architecture:** El comando es un archivo de instrucciones markdown (`.claude/commands/rencuesta.md`) que Claude Code interpreta paso a paso. La malla es híbrida: `data/mapa_conceptos.json` guarda nodos + aristas tipadas (estructura), y `conceptos/<id>.md` guarda el contenido didáctico canónico. Dos plantillas formatean los entregables WhatsApp (concepto + mapa). Se siembra el grafo con el caso real stop-loss → confluencia → puntos-interés.

**Tech Stack:** Markdown (comandos/notas/plantillas), JSON (grafo), Python 3 para validación (el repo ya usa `scripts/*.py`). Sin frameworks de test — la verificación es parseo JSON + chequeo de existencia/consistencia.

**Nota de testing:** Este proyecto no tiene suite de tests para los comandos (son prompts). Cada tarea verifica su artefacto con el método apropiado: `python -c "import json; ..."` para JSON, `Test-Path` para existencia, y `Select-String`/`grep` para referencias cruzadas. No se inventan tests pytest donde no aplica.

---

## Estructura de archivos

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `data/mapa_conceptos.json` | Grafo: nodos (conceptos) + aristas tipadas + estado | Crear (seed) |
| `conceptos/stop-loss.md` | Nota canónica del primer concepto | Crear (seed) |
| `conceptos/README.md` | Explica qué es la carpeta y el formato de nota | Crear |
| `templates/concepto_didactico.txt` | Plantilla entregable A (mensaje educativo) | Crear |
| `templates/mapa_conceptos.txt` | Plantilla entregable B (vista del mapa) | Crear |
| `.claude/commands/rencuesta.md` | El comando: 3 modos, flujo de aprobación, persistencia | Crear |
| `.claude/commands/encuesta.md` | Referencia `/encuesta revelar` → `/rencuesta` | Modificar |
| `CLAUDE.md` | Lista de comandos (19→20) + estructura del proyecto | Modificar |

---

## Task 1: Seed del grafo de conceptos

**Files:**
- Create: `data/mapa_conceptos.json`

- [ ] **Step 1: Crear el grafo sembrado**

Crear `data/mapa_conceptos.json` con el caso real que motivó la feature. `stop-loss` ya está explicado (existe la encuesta real); `confluencia` y `puntos-interes` quedan `pendiente`:

```json
{
  "conceptos": {
    "stop-loss": {
      "nombre": "Stop loss",
      "nota": "conceptos/stop-loss.md",
      "estado": "explicado",
      "encuestas": ["2026-06-02_educativa_USDCLP_stoploss"],
      "aristas": {
        "se-apoya-en": ["confluencia"],
        "usa": ["atr", "riesgo"]
      }
    },
    "confluencia": {
      "nombre": "Confluencia",
      "nota": null,
      "estado": "pendiente",
      "encuestas": [],
      "aristas": {
        "abre": ["puntos-interes"]
      }
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

- [ ] **Step 2: Validar que el JSON parsea**

Run: `python -c "import json; d=json.load(open('data/mapa_conceptos.json', encoding='utf-8')); print(list(d['conceptos'].keys()))"`
Expected: `['stop-loss', 'confluencia', 'puntos-interes']`

- [ ] **Step 3: Validar integridad referencial de aristas**

Cada destino de arista debe existir como nodo. Run:

```bash
python -c "import json; d=json.load(open('data/mapa_conceptos.json', encoding='utf-8'))['conceptos']; nodos=set(d); faltan=[t for n in d.values() for arr in n['aristas'].values() for t in arr if t not in nodos and t not in ('atr','riesgo')]; print('OK' if not faltan else 'FALTAN: '+str(faltan))"
```
Expected: `OK`
(Nota: `atr` y `riesgo` son vecinos aún no nodeados — se crearán cuando se desarrollen; se permiten como aristas pendientes.)

- [ ] **Step 4: Commit**

```bash
git add data/mapa_conceptos.json
git commit -m "feat(rencuesta): seed del grafo de conceptos (stop-loss -> confluencia -> puntos-interes)"
```

---

## Task 2: Carpeta `conceptos/` + nota canónica seed

**Files:**
- Create: `conceptos/README.md`
- Create: `conceptos/stop-loss.md`

- [ ] **Step 1: Crear el README de la carpeta**

Crear `conceptos/README.md`:

```markdown
# Conceptos — notas canónicas de la malla educativa

Cada archivo `<id>.md` es la **fuente de verdad** del contenido didáctico de un
concepto, curada y aprobada por el director. El comando `/rencuesta` la lee para
profundizar sin repetir, y la actualiza al aprobar contenido nuevo.

La estructura de relaciones (qué concepto se conecta con cuál) vive en
`data/mapa_conceptos.json`. Aquí vive el **contenido**.

## Formato de una nota

```markdown
---
id: stop-loss            # kebab-case, igual a la clave en mapa_conceptos.json
nombre: Stop loss
estado: explicado        # explicado | pendiente
encuestas: [id_encuesta] # encuestas que trataron el concepto
ancla: [atr, riesgo]     # indicadores/drivers del repo en los que se apoya
---

Contenido didáctico en voz novata. Los enlaces [[otro-concepto]] reflejan
las aristas del grafo y tejen la malla.
```
```

- [ ] **Step 2: Crear la nota canónica de stop-loss**

Crear `conceptos/stop-loss.md`:

```markdown
---
id: stop-loss
nombre: Stop loss
estado: explicado
encuestas: [2026-06-02_educativa_USDCLP_stoploss]
ancla: [atr, riesgo]
---

El stop loss es tu "freno de emergencia": una orden que cierra la operación
automáticamente si el precio va en tu contra, para que la pérdida no crezca
sin control.

No es un número puesto al azar ni "lo que estoy dispuesto a perder a ojo".
Se decide por la [[confluencia]] de varios [[puntos-interes]]: niveles donde
el precio ya reaccionó antes (soportes, resistencias) y la volatilidad real
del activo.

En USD/CLP, el [[atr]] te dice cuánto se mueve normalmente el dólar en una
vela. Si el ATR de 1H es 2.5 pesos, poner el stop a 2.5 pesos de la entrada
respeta el "ruido" normal del activo: no te saca por un movimiento corriente,
pero te protege si la idea falla de verdad.

Regla simple para el cliente nuevo: **antes de entrar, ya tenés que saber
dónde está tu stop**. Si no sabés dónde ponerlo, todavía no es momento de
operar.
```

- [ ] **Step 3: Verificar que el frontmatter id coincide con la clave del grafo**

Run:
```bash
python -c "import json; d=json.load(open('data/mapa_conceptos.json', encoding='utf-8'))['conceptos']['stop-loss']; print('OK' if d['nota']=='conceptos/stop-loss.md' else 'MISMATCH')"
```
Expected: `OK`

- [ ] **Step 4: Verificar que la nota existe y tiene los enlaces esperados**

Run (PowerShell): `Select-String -Path conceptos/stop-loss.md -Pattern '\[\[confluencia\]\]','\[\[puntos-interes\]\]','\[\[atr\]\]' | Measure-Object | Select-Object -ExpandProperty Count`
Expected: `3` (los tres enlaces presentes)

- [ ] **Step 5: Commit**

```bash
git add conceptos/README.md conceptos/stop-loss.md
git commit -m "feat(rencuesta): carpeta conceptos/ + nota canonica seed de stop-loss"
```

---

## Task 3: Plantillas de los dos entregables WhatsApp

**Files:**
- Create: `templates/concepto_didactico.txt`
- Create: `templates/mapa_conceptos.txt`

- [ ] **Step 1: Crear la plantilla del mensaje educativo (entregable A)**

Crear `templates/concepto_didactico.txt`. Cumple las 6 reglas de formato del `CLAUDE.md` (resumen arriba, separadores, negrita solo en jerarquía, above-the-fold, conexión al final):

```text
🎯 *CONCEPTO — {NOMBRE_CONCEPTO}*
━━━━━━━━━━━━━━━━━━━
📌 En 1 línea: {RESUMEN_UNA_LINEA}
━━━━━━━━━━━━━━━━━━━
📚 *Qué es*: {QUE_ES}
🧩 *Cómo se decide bien*: {COMO_APLICA}
🎯 *Para aplicarlo*: {ACCION_CONCRETA}
━━━━━━━━━━━━━━━━━━━
🔗 *Esto conecta con*: {VECINOS}
💬 La próxima encuesta profundiza en uno de estos 👇
```

- [ ] **Step 2: Crear la plantilla de la vista del mapa (entregable B)**

Crear `templates/mapa_conceptos.txt`:

```text
🗺️ *MAPA DE CONCEPTOS — repaso*
━━━━━━━━━━━━━━━━━━━
{ARBOL_ASCII}
━━━━━━━━━━━━━━━━━━━
✅ ya visto · 🆕 nuevo · ⏳ pendiente
```

- [ ] **Step 3: Verificar que ambas plantillas existen**

Run (PowerShell): `Test-Path templates/concepto_didactico.txt; Test-Path templates/mapa_conceptos.txt`
Expected: `True` y `True`

- [ ] **Step 4: Commit**

```bash
git add templates/concepto_didactico.txt templates/mapa_conceptos.txt
git commit -m "feat(rencuesta): plantillas WhatsApp de concepto educativo y vista del mapa"
```

---

## Task 4: El comando `/rencuesta`

**Files:**
- Create: `.claude/commands/rencuesta.md`

Este es el corazón. El comando se escribe de una vez (es un documento de instrucciones, no código incremental), siguiendo el estilo de `.claude/commands/apertura.md` (pasos numerados, bloques de aprobación). Se verifica que cubre los 3 modos y referencia las rutas correctas.

- [ ] **Step 1: Escribir el comando completo**

Crear `.claude/commands/rencuesta.md` con este contenido exacto:

````markdown
Desarrolla didácticamente los temas tratados en las encuestas y construye la malla de conceptos del grupo.

## Argumentos
$ARGUMENTS — uno de:
- *(vacío)* → toma la última encuesta de `data/historial_encuestas.json` y desarrolla su concepto.
- `<tema>` → desarrolla/profundiza ese concepto (ej. `confluencia`, `"puntos de interés"`).
- `mapa` → genera la vista visual de la malla actual para repaso.

## Principio
NO es "revelar la respuesta correcta". Es **enseñar el concepto** en voz de cliente nuevo (sin jerga sin explicar) y **mapear** cómo se conecta con otros conceptos. Materializa la misión: pasar de señales a educación.

---

## PASO 1 — Resolver el tema

**Si `$ARGUMENTS` es `mapa`** → ir directo al PASO 5.

**Si `$ARGUMENTS` está vacío**:
1. Leer `data/historial_encuestas.json`, tomar la encuesta con `fecha` más reciente.
2. Identificar el/los concepto(s) que trató (de `pregunta`/`opciones`/`trigger`). Normalizar a `id` kebab-case (ej. "stop loss" → `stop-loss`).
3. Si trató varios conceptos, listarlos al director y pedir que elija el central.

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
2. **Voz novata**: un cliente nuevo lo entiende en < 30 s. Nada de jerga sin explicar.
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
- Guardar el mensaje en `data/mensajes/YYYY-MM-DD_HH-MM_encuesta.txt`.
- Si el tema vino de una encuesta, en `data/historial_encuestas.json` poner esa encuesta `estado: "revelada"` y enlazarla (`conceptos/<id>.md` ya la lista en `encuestas`).

---

## PASO 5 — Vista del mapa (`/rencuesta mapa`)

1. Leer `data/mapa_conceptos.json`.
2. Construir un árbol ASCII partiendo de los nodos raíz (los que ningún otro nodo apunta) y descendiendo por las aristas. Etiquetar la flecha con el tipo de arista (ej. `se apoya en →`, `que usa →`).
3. Marcar cada nodo: `✅` si `explicado`, `⏳` si `pendiente`, `🆕` si se creó/explicó en la última corrida.
4. Renderizar dentro de `templates/mapa_conceptos.txt` (`{ARBOL_ASCII}`).
5. Mostrar al director: *"¿Apruebas enviar este mapa de repaso?"*. Al aprobar, guardar en `data/mensajes/YYYY-MM-DD_HH-MM_encuesta.txt`.

Si el grafo está vacío → avisar que aún no hay conceptos en la malla.

---

## REGLAS
- Voz novata SIEMPRE (regla de oro: < 30 s para un cliente nuevo).
- Respetar la regla de decimales MT5 si se menciona algún precio.
- Las 6 reglas de formato del `CLAUDE.md` aplican a ambos entregables.
- Nunca enviar nada sin aprobación explícita del director.
- Concepto ya `explicado` → profundizar, no repetir.
- Hora en hora Chile si se menciona algún horario.
````

- [ ] **Step 2: Verificar que el comando referencia todas las rutas correctas**

Run (PowerShell):
```powershell
Select-String -Path .claude/commands/rencuesta.md -Pattern 'data/mapa_conceptos.json','conceptos/','templates/concepto_didactico.txt','templates/mapa_conceptos.txt','data/historial_encuestas.json' | Measure-Object | Select-Object -ExpandProperty Count
```
Expected: un número ≥ 5 (todas las rutas referenciadas)

- [ ] **Step 3: Verificar que cubre los 3 modos**

Run (PowerShell): `Select-String -Path .claude/commands/rencuesta.md -Pattern 'PASO 1','PASO 5','mapa' | Measure-Object | Select-Object -ExpandProperty Count`
Expected: un número ≥ 3 (los modos y pasos presentes)

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/rencuesta.md
git commit -m "feat(rencuesta): comando /rencuesta con 3 modos (encuesta, tema, mapa)"
```

---

## Task 5: Actualizar referencia en `encuesta.md`

**Files:**
- Modify: `.claude/commands/encuesta.md:192`

- [ ] **Step 1: Localizar la línea del comando huérfano**

Run (PowerShell): `Select-String -Path .claude/commands/encuesta.md -Pattern 'encuesta revelar'`
Expected: muestra la línea ~192 con `Para revelar la respuesta al día siguiente, usar: /encuesta revelar [id_encuesta]`

- [ ] **Step 2: Reemplazar la referencia por `/rencuesta`**

Editar esa línea para que apunte al comando real. Texto nuevo:

```text
Para desarrollar el concepto y revelar al día siguiente, usar: `/rencuesta` (sin argumento toma la última encuesta) — desarrolla el tema de forma didáctica y lo agrega a la malla de conceptos. Ver `docs/design/rencuesta-motor-educativo.design.md`.
```

- [ ] **Step 3: Verificar que ya no queda la referencia huérfana**

Run (PowerShell): `Select-String -Path .claude/commands/encuesta.md -Pattern '/encuesta revelar'`
Expected: sin coincidencias (vacío)

- [ ] **Step 4: Commit**

```bash
git add .claude/commands/encuesta.md
git commit -m "docs(encuesta): apunta el revelado al nuevo comando /rencuesta"
```

---

## Task 6: Actualizar `CLAUDE.md` (lista de comandos + estructura)

**Files:**
- Modify: `CLAUDE.md` (sección "Slash Commands disponibles" + "Estructura del proyecto")

- [ ] **Step 1: Actualizar el encabezado del conteo de comandos**

Buscar `## Slash Commands disponibles (19)` y cambiar a `## Slash Commands disponibles (20)`.

Run para localizar: `Select-String -Path CLAUDE.md -Pattern 'Slash Commands disponibles'`

- [ ] **Step 2: Agregar `/rencuesta` a la tabla Capa 2**

En la tabla "Capa 2 — Comandos de tarea (ad hoc)", después de la fila de `/encuesta`, agregar:

```text
| `/rencuesta` | Desarrolla didácticamente el tema de una encuesta y construye la malla de conceptos. `/rencuesta` (última encuesta), `/rencuesta [tema]`, `/rencuesta mapa` (vista de repaso). |
```

- [ ] **Step 3: Agregar los artefactos nuevos a la sección "Estructura del proyecto"**

En el bloque de árbol de `config/` y `data/`, agregar las entradas nuevas. Bajo `data/`:

```text
│   ├── mapa_conceptos.json ← grafo de la malla de conceptos educativos
```

Y agregar una entrada de carpeta nueva a nivel raíz del árbol (junto a `templates/`):

```text
├── conceptos/             ← notas canónicas de conceptos educativos (malla /rencuesta)
│   ├── README.md · stop-loss.md
```

- [ ] **Step 4: Verificar las ediciones**

Run (PowerShell):
```powershell
Select-String -Path CLAUDE.md -Pattern 'Slash Commands disponibles \(20\)','/rencuesta','mapa_conceptos.json','conceptos/' | Measure-Object | Select-Object -ExpandProperty Count
```
Expected: número ≥ 4

- [ ] **Step 5: Commit**

```bash
git add CLAUDE.md
git commit -m "docs(claude): registra /rencuesta y la malla de conceptos en CLAUDE.md"
```

---

## Task 7: Verificación de integración end-to-end

**Files:** (sin cambios — solo verificación)

- [ ] **Step 1: Validar que todo el JSON del repo sigue parseando**

Run:
```bash
python -c "import json; [json.load(open(f, encoding='utf-8')) for f in ['data/mapa_conceptos.json','data/historial_encuestas.json']]; print('JSON OK')"
```
Expected: `JSON OK`

- [ ] **Step 2: Validar coherencia nota ↔ grafo**

Cada nodo con `nota` no-null debe apuntar a un archivo existente. Run:
```bash
python -c "import json,os; d=json.load(open('data/mapa_conceptos.json', encoding='utf-8'))['conceptos']; bad=[n for n,v in d.items() if v['nota'] and not os.path.exists(v['nota'])]; print('OK' if not bad else 'FALTAN NOTAS: '+str(bad))"
```
Expected: `OK`

- [ ] **Step 3: Confirmar que todos los archivos de la feature existen**

Run (PowerShell):
```powershell
'data/mapa_conceptos.json','conceptos/README.md','conceptos/stop-loss.md','templates/concepto_didactico.txt','templates/mapa_conceptos.txt','.claude/commands/rencuesta.md' | ForEach-Object { "$_ -> $(Test-Path $_)" }
```
Expected: todos `True`

- [ ] **Step 4: Revisión manual de voz novata (checklist, no comando)**

Leer `conceptos/stop-loss.md` y el `templates/concepto_didactico.txt` con ojos de cliente nuevo:
- ¿Hay jerga sin explicar? (Si aparece "ATR", ¿se dice qué es?)
- ¿Las primeras líneas entregan lo esencial (above-the-fold)?
- ¿Un cliente sin experiencia lo entiende en < 30 s?
Si algo falla, corregir la nota/plantilla y re-commitear.

- [ ] **Step 5: Commit final (si hubo correcciones de voz)**

```bash
git add -A
git commit -m "chore(rencuesta): ajustes finales de voz novata y verificacion de integracion"
```

---

## Self-Review (cubierto por el plan)

- **Cobertura del spec**: Task 1 (grafo) · Task 2 (notas/canon) · Task 3 (plantillas A y B) · Task 4 (comando, 3 modos, fuente anclada, aprobación, persistencia, edge cases) · Task 5 (referencia huérfana de encuesta.md) · Task 6 (CLAUDE.md lista+estructura) · Task 7 (integración + voz novata). Todos los archivos de la sección "Archivos" del spec tienen tarea.
- **Sin placeholders**: el contenido de cada archivo está escrito completo; los `{CAMPO}` en las plantillas son marcadores de plantilla intencionales (no placeholders del plan).
- **Consistencia de tipos**: claves del grafo (`stop-loss`, `confluencia`, `puntos-interes`), tipos de arista (`se-apoya-en`, `usa`, `abre`, `prerequisito-de`, `relacionado`) y estados (`explicado`, `pendiente`) son idénticos en spec, grafo, nota y comando.

## Fuera de alcance (v1)
- Sin imagen del mapa (ASCII en texto).
- Sin métricas de participación automáticas.
- Sin cierre de encuestas `tendencia`/`precio` por resultado de mercado.
