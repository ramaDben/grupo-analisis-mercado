# DISEÑO TÉCNICO — `/curriculo`: currículo educativo evolutivo + métricas

## Contexto

El Grupo de Análisis de Mercado tiene hoy un **motor educativo reactivo**: `/rencuesta` +
`data/mapa_conceptos.json` + `conceptos/<id>.md`. Parte de una encuesta con baja
participación y desarrolla el concepto, tejiendo la malla **hacia adelante, concepto a
concepto, según lo que va surgiendo**. Funciona, pero es reactivo: no hay un plan.

El directorio quiere la pieza que falta: una **capa proactiva** que permita **planificar
con antelación** qué conceptos enseñar, en qué orden (de menos a más), agendados,
documentados y **medibles** (participación, comprensión, cobertura, satisfacción), para
**proyectar el impacto, la visión y medir el éxito**.

### Norte (visión a gran escala)

Esto es el **primer paso de un sistema completamente automatizado y escalable**:
- Un "área viva" comandada por **agentes de IA** que leen el mercado en continuo y
  **conectan cada evento con el currículo** educativo.
- Entrega que escala: **WhatsApp (beta, foco novatos)** → **plataforma web con login y
  segmentación**, donde **cada trader recorre su propia ruta**.
- Captura/medición: **WhatsApp + Google Forms** en la beta; datos **por-trader** en la web.

El diseño de hoy debe **correr la beta en WhatsApp** dejando la arquitectura desacoplada
para que web/login/segmentación/agentes enchufen después **sin rehacer**.

### Decisiones del director (brainstorming)

- **Alcance hoy**: fundación curricular agnóstica al canal + loop beta WhatsApp/Forms.
  Web/login/segmentación/agentes-de-mercado se documentan como arquitectura objetivo, no
  se construyen hoy.
- **Progresión**: **niveles + prerrequisitos** (híbrido). Los niveles mapean a los futuros
  segmentos de trader; los prerrequisitos garantizan la base.
- **Operación**: comando nuevo `/curriculo` (el cerebro) que **reutiliza** `/rencuesta` y
  `/concepto` para la entrega (las manos).
- **Métricas**: las 4 — participación, comprensión, cobertura, satisfacción.
- **Arquitectura**: **4 capas**, con un **grafo de prerrequisitos como Capa 1**. El grafo
  no es opcional: un prerrequisito *es* una arista, y las rutas personalizadas del futuro
  son traversals sobre ese grafo. Se simplifica a **una sola arista estructural**
  (`prerequisito-de`); las demás quedan como metadato blando para el repaso.
- **Ruta**: **curada por el director, validada contra el DAG**. El director fija el orden
  (su visión); el sistema impide violar prerrequisitos y sugiere el siguiente.

---

## Arquitectura — 4 capas

| Capa | Qué es | Beta (WhatsApp) | Escala (web) |
|---|---|---|---|
| **1. Conocimiento** | Conceptos (nodos) con `nivel` + anclas + contenido; arista estructural `prerequisito-de` (el DAG). | Extiende `data/mapa_conceptos.json` | → tablas `conceptos` + `prerrequisitos` |
| **2. Ruta/Currículo** | Secuencia curada sobre el DAG, validada. Beta: 1 ruta "novatos". | `data/curriculo.json` | → rutas por segmento de trader |
| **3. Entrega** | Cada enseñanza = un evento (concepto, **canal**, fecha, link al mensaje). Agnóstico al canal. | `data/entregas_educativas.json` | → canal `web`/`login` |
| **4. Progreso + Métricas** | Agregaciones sobre entregas + encuestas. | `data/metricas_educativas.json` | → por-trader (mismo modelo, distinto sujeto) |

El formato JSON-por-capa mapea 1:1 a tablas/colecciones de DB: el camino a la web es
directo, sin rehacer.

---

## Capa 1 — Conocimiento (extensión *aditiva* de `mapa_conceptos.json`)

No rompe nada de lo que `/rencuesta` ya usa. **Agrega** 3 campos por nodo y eleva una arista:

```json
"stop-loss": {
  "nombre": "Stop loss",
  "tipo": "tecnico",          // NUEVO: tecnico | glosario | macro
  "nivel": 1,                 // NUEVO: 1 Novato · 2 Intermedio · 3 Avanzado
  "glosario": "Tu freno de emergencia: cierra la operación si el precio va en contra.",
  "nota": "conceptos/stop-loss.md",
  "estado": "explicado",      // pendiente | explicado
  "anclas": ["atr", "riesgo"],
  "encuestas": ["2026-06-02_educativa_USDCLP_stoploss"],
  "aristas": {
    "prerequisito-de": ["confluencia"],   // ESTRUCTURAL: manda el orden del currículo
    "relacionado": ["puntos-interes"]      // BLANDA: solo para el mapa de repaso
  }
}
```

- **`tipo`** integra glosario (IPC, NFP, Dollar Index…) y macro/noticias (cómo leer el IPC)
  en el **mismo grafo**, solo etiquetados. El "glosario fijado" del grupo pasa a ser una
  **vista filtrada** (`tipo: glosario`), nunca una estructura aparte que se desincronice.
- **`nivel`** es lo que mañana mapea a segmentos de trader en la web.
- **`prerequisito-de`** es la única arista con peso estructural. Las demás
  (`relacionado`, y las que ya usa `/rencuesta`: `se-apoya-en`, `usa`, `abre`) quedan para
  el mapa de repaso. **Cero cambios al comportamiento de `/rencuesta`** (lee los campos
  nuevos solo si los necesita).

### Semilla — Ruta Novato (nivel 1)

Los 3 nodos actuales (`stop-loss`, `confluencia`, `puntos-interes`) encajan sin forzar.
Se siembran 7 nodos nuevos para que la beta arranque con contenido real:

```
1. leer-un-grafico      qué muestra un gráfico: precio, tiempo, velas        [nuevo]
2. velas                cómo leer una vela (cuerpo, mecha)        prereq: 1   [nuevo]
3. temporalidades       15M/1H/4H/1D y qué operativa implica      prereq: 1   [nuevo]
4. tendencia            alcista / bajista / lateral               prereq: 1   [nuevo]
5. soporte-resistencia  niveles donde el precio reacciona         prereq: 4   [nuevo]
6. puntos-interes       zonas clave a vigilar                     prereq: 5   [ya existe ⏳]
7. confluencia          varios factores apuntando al mismo nivel  prereq: 6   [ya existe ⏳]
8. volatilidad-atr      cuánto se mueve el activo (ATR en USD/CLP) prereq: 4   [nuevo]
9. riesgo               cuánto estás dispuesto a perder           (base)      [nuevo]
10. stop-loss           tu freno de emergencia          prereq: 9 + 7         [ya existe ✅]
```

Progresión "de menos a más": *ver* el gráfico → *leerlo* → *encontrar niveles* →
*gestionar riesgo*. Glosario y macro (IPC, NFP, Dollar Index, cómo leer un dato macro)
se reservan para **nivel 2**: el novato primero lee un gráfico, luego interpreta noticias.

---

## Capa 2 — Ruta/Currículo (`data/curriculo.json`, nuevo)

Ruta **curada por el director**, validada contra el DAG de la Capa 1:

```json
{
  "rutas": {
    "novatos": {
      "nombre": "Ruta Novato",
      "nivel": 1,
      "descripcion": "Primeros pasos: leer el mercado sin perderse.",
      "secuencia": [
        { "concepto": "leer-un-grafico", "semana_objetivo": "2026-W24", "estado": "planificado" },
        { "concepto": "velas",           "semana_objetivo": "2026-W24", "estado": "planificado" },
        { "concepto": "riesgo",          "semana_objetivo": "2026-W25", "estado": "planificado" },
        { "concepto": "stop-loss",       "semana_objetivo": "2026-W25", "estado": "entregado" }
      ]
    }
  },
  "actualizado": "2026-06-02"
}
```

- **`secuencia`** = el orden que fija el director (su visión). Agendamiento ligero por
  `semana_objetivo` (semana ISO), sin calendario pesado.
- **Validación (garantía evolutiva)**: al guardar, para cada item se chequea que sus
  `prerequisito-de` aparezcan **antes** en la secuencia. Si no, el sistema avisa y no
  guarda. Así nunca se enseña algo sin su base.
- **Estados del item**: `planificado` | `entregado`.
- **Beta = 1 ruta (`novatos`)**. La estructura `rutas{}` deja la puerta abierta a
  `intermedios`/`avanzados`/segmentos sin rehacer nada.

---

## Capa 3 — Entrega (`data/entregas_educativas.json`, nuevo)

`/curriculo` **no redacta el mensaje** — delega en `/rencuesta` o `/concepto` (voz novata,
6 reglas de formato). La Capa 3 **registra** que un concepto se entregó, por qué canal y
cuándo. Eso la hace agnóstica al canal.

```json
{
  "entregas": [
    {
      "id": "2026-06-09_stop-loss_whatsapp",
      "concepto": "stop-loss",
      "ruta": "novatos",
      "canal": "whatsapp",        // whatsapp | forms | web (futuro, sin cambios)
      "fecha": "2026-06-09",
      "mensaje": "data/mensajes/2026-06-09_09-15_encuesta.txt",
      "encuesta": "2026-06-09_educativa_USDCLP_stoploss",
      "comando_origen": "rencuesta"
    }
  ]
}
```

Al aprobar el mensaje (flujo existente → `data/mensajes/`), `/curriculo`:
1. escribe el registro de entrega,
2. marca el item de la ruta como `entregado`,
3. si el concepto era nuevo, deja el nodo del grafo `explicado`.

El campo **`canal`** es lo único que cambia el día que sea web; el resto es idéntico.

---

## Capa 4 — Métricas (`data/metricas_educativas.json`, nuevo)

Las 4 métricas, en *snapshots* semanales (lo que el directorio usa para proyectar):

```json
{
  "snapshots": [
    {
      "fecha": "2026-06-13", "semana": "2026-W24",
      "participacion": { "encuestas": 2, "votos_promedio": 14 },
      "comprension":   { "encuestas_evaluadas": 1, "aciertos_pct": 62 },
      "cobertura":     { "total": 10, "entregados": 4, "pct": 40, "por_nivel": { "1": "40%", "2": "0%", "3": "0%" } },
      "satisfaccion":  { "tipo": "nps", "valor": 7.5, "respuestas": 9, "canal": "forms" }
    }
  ]
}
```

Origen de cada dato:
- **Cobertura** → 100% automática (del grafo + `curriculo.json`). Métrica de proyección:
  *"¿vamos al ritmo planeado?"*.
- **Participación / Comprensión** → de los resultados de las encuestas educativas. En beta
  los ingresa el director al correr `/curriculo progreso` (captura manual ligera). La web
  los capturará solo.
- **Satisfacción** → pulso periódico (encuesta WhatsApp simple o **link a Google Forms**)
  cuyo resultado ingresa el director. El campo `canal` distingue el origen.

> La integración *automática* con Google Forms queda fuera de hoy, pero el modelo
> (`canal`, `respuestas`) ya está listo para enchufarla sin rehacer.

---

## El comando `/curriculo` (`.claude/commands/curriculo.md`, nuevo)

Un comando, varios modos (igual que `/rencuesta`):

| Invocación | Acción |
|---|---|
| `/curriculo` | **Estado + recomendación**: muestra la ruta novato, dónde vamos, y recomienda el **próximo concepto coherente** (el siguiente `planificado` cuyos prerrequisitos ya están `entregado`). Pregunta: *"¿lo despachamos?"* |
| `/curriculo despachar [concepto]` | Valida prerrequisitos → **delega en `/rencuesta [concepto]`** (desarrolla, crea la nota canónica, teje la malla) o `/concepto` para el formato del lunes. Al aprobar: registra entrega + avanza la ruta. |
| `/curriculo ruta` | Render del **roadmap completo** por nivel (árbol ASCII, estados ✅⏳🆕). Doble uso: proyección ante el directorio **y** repaso para el grupo. |
| `/curriculo progreso` | Calcula las **4 métricas**, escribe el snapshot semanal y muestra el dashboard. |
| `/curriculo agregar [concepto]` | **Curar la ruta**: añadir/reordenar un concepto, con validación de prerrequisitos. |

### Flujo de despacho (el loop de la beta)

```
/curriculo                → recomienda "confluencia" (prereqs ok)
  └ aprueba
/curriculo despachar confluencia
  └ delega → /rencuesta confluencia   (mensaje WhatsApp + nota canónica)
  └ aprueba el mensaje (flujo existente → data/mensajes/)
  └ /curriculo registra: entrega(canal=whatsapp) + ruta.confluencia=entregado
                         + grafo.confluencia=explicado
```

### Pasos internos del comando

1. **Resolver modo** según `$ARGUMENTS` (vacío / `despachar` / `ruta` / `progreso` / `agregar`).
2. **`/curriculo`** → leer `curriculo.json` + `mapa_conceptos.json`; calcular el próximo
   recomendado (primer item `planificado` con todos sus prerrequisitos `entregado`);
   mostrar ruta + recomendación.
3. **`despachar [concepto]`** → validar prerrequisitos; elegir delegado (`/rencuesta` si el
   concepto necesita desarrollo educativo / es nuevo; `/concepto` para el "concepto de la
   semana"); al aprobar, registrar entrega + avanzar estados.
4. **`ruta`** → render del roadmap por nivel desde `curriculo.json` (plantilla
   `templates/ruta_curriculo.txt`).
5. **`progreso`** → calcular cobertura (automática); pedir al director los números de
   participación/comprensión/satisfacción; escribir snapshot; render dashboard
   (`templates/dashboard_metricas.txt`).
6. **`agregar [concepto]`** → insertar/reordenar en la secuencia con validación de DAG.

### Integración ligera con la agenda (anotada, no construida hoy)

El slot `concepto_semana` de los lunes (`config/agenda_semanal.json`, comando `/lunes`)
podrá en el futuro llamar a `/curriculo` para elegir el concepto de la semana. Punto de
extensión, fuera de este spec.

---

## Flujo de datos

```
/curriculo [modo]
  │
  ├─ (vacío) ─→ curriculo.json + mapa_conceptos.json ─→ próximo recomendado ─→ MOSTRAR
  ├─ despachar ─→ validar DAG ─→ delega /rencuesta|/concepto ─→ aprueba
  │                 └─→ entregas_educativas.json (+registro)
  │                 └─→ curriculo.json (item=entregado)
  │                 └─→ mapa_conceptos.json (nodo=explicado)
  ├─ ruta ─────→ curriculo.json ─→ render árbol ─→ FIN
  ├─ progreso ─→ grafo+curriculo (cobertura auto) + input director ─→ metricas_educativas.json ─→ dashboard
  └─ agregar ──→ validar DAG ─→ curriculo.json (+item)
```

---

## Manejo de errores / edge cases

- **Despachar un concepto con prerrequisitos sin entregar** → avisar cuáles faltan y no
  despachar (ofrecer despachar el prerrequisito primero).
- **`agregar` que rompe el orden evolutivo** → rechazar con el detalle del prerrequisito
  faltante.
- **`/curriculo` sin ningún item `planificado`** → avisar que la ruta está completa o que
  hay que `agregar` conceptos.
- **`progreso` sin encuestas en la semana** → snapshot con participación/comprensión en
  cero o `null`, cobertura igual se calcula.
- **Concepto en la ruta que no existe en el grafo** → crearlo como nodo `pendiente` al
  despacharlo (lo hace `/rencuesta`), o avisar en `agregar`.
- **Nodo sin `nivel`** (heredado del esquema viejo) → tratarlo como nivel 1 por defecto.

---

## Archivos

**Nuevos**:
- `.claude/commands/curriculo.md` — el comando.
- `data/curriculo.json` — la ruta novato sembrada.
- `data/entregas_educativas.json` — registro de entregas (inicia vacío o con la entrega real de stop-loss).
- `data/metricas_educativas.json` — snapshots (inicia vacío).
- `templates/ruta_curriculo.txt` — plantilla del roadmap.
- `templates/dashboard_metricas.txt` — plantilla del dashboard.

**Modificados (aditivo)**:
- `data/mapa_conceptos.json` — + `tipo`, `nivel`, `glosario` en los 3 nodos actuales + 7 nodos nivel-1 nuevos + aristas `prerequisito-de`.
- `CLAUDE.md` — lista de comandos (20 → 21) + estructura del proyecto (nuevos archivos de datos y templates).

**Sin tocar**:
- `.claude/commands/rencuesta.md` — sigue igual; lee campos nuevos solo si los necesita.

---

## Testing / verificación

- **Caso 1 — recomendación**: con la ruta sembrada, `/curriculo` recomienda el primer
  `planificado` con prerrequisitos cubiertos (ej. `leer-un-grafico`, sin prereqs).
- **Caso 2 — despacho**: `/curriculo despachar leer-un-grafico` delega a `/rencuesta`,
  y al aprobar deja entrega registrada + item `entregado` + nodo `explicado`.
- **Caso 3 — validación**: `/curriculo agregar confluencia` antes que `puntos-interes`
  debe rechazarse por prerrequisito faltante.
- **Caso 4 — ruta**: `/curriculo ruta` renderiza el roadmap por nivel con estados.
- **Caso 5 — métricas**: `/curriculo progreso` calcula cobertura automática y produce un
  snapshot con los números ingresados.
- **Formato**: todo mensaje al grupo cumple las 6 reglas + decimales MT5 + voz novata
  (< 30 s) + español chileno neutro.

---

## YAGNI — fuera de alcance (v1 beta)

- Sin plataforma web, login ni segmentación por trader (documentado como norte, no construido).
- Sin agentes de IA de mercado-vivo (la conexión evento→concepto es manual por ahora).
- Sin integración automática con Google Forms (el modelo la admite; la captura es manual).
- Sin métricas por-trader (solo agregados de grupo).
- Sin generación de imágenes del roadmap (ASCII, robusto en WhatsApp).
- Sin múltiples rutas activas (solo `novatos` en beta; la estructura ya las admite).
```
