# Enfoque direccional operativo — rediseño editorial

**Fecha:** 2026-06-15
**Rama:** `feat/enfoque-direccional-operativo`
**Tipo:** Cambio editorial (ediciones de prompts/instrucciones, no código)

## Contexto y motivación

El director redirige la línea editorial del grupo. El foco pasa de "análisis técnico
neutral, no operativo" a **enfoque direccional operativo**: el cliente debe entender
siempre hacia dónde se dirige el activo para saber qué operar, con un tono que genera
interés y apetito por operar sin caer en lo coloquial ni catastrófico.

Varios cambios **revierten decisiones recientes** de forma deliberada:
- El principio fundamental "100% cliente novato, neutral" se flexibiliza a audiencia mixta
  (novatos + expertos) con gancho operativo.
- La regla de `/apertura` "NO es señal" pasa a "sesgo operativo implícito".
- La prohibición de `Soporte/Resistencia` (issue #35) se **invierte**: ahora lo prohibido
  es `Techo/Suelo`.
- La prohibición de la línea `Sesgo:` se levanta: ahora hay "sesgo del equipo".
- El tono profesional (commit `54ff7dd`) se **relaja, no se borra**: se permite énfasis
  direccional persuasivo; sigue prohibido lo extremo/emocional/coloquial.

## Decisiones tomadas (brainstorming)

1. **Tono**: equilibrio profesional + persuasivo (no reemplazo total).
2. **Señal implícita en `/apertura`**: sesgo + niveles accionables ("sobre X se activa
   sesgo comprador"), SIN entrada/TP/SL en pesos y SIN contar para el límite 3/semana.
3. **Rotación de acciones**: el mecanismo definitivo es un **market screener (issue
   futuro, fuera de este alcance)**. Fuente interina: las 2 acciones destacadas por
   `/earnings`.
4. **Filtro EE.UU. en `/dato_macro`**: el filtro "solo 3★" aplica también a la **lista**
   del PASO 2, no solo al desarrollo.

## Alcance — archivos a modificar

### 1. `CLAUDE.md` — Principio fundamental + Regla de oro

Reescribir el bloque "Principio fundamental" bajo el modelo equilibrio:
- Mantener: comprensible en 30 s, no coloquial, no catástrofes, siglas explicadas.
- Añadir: permiso explícito para enfatizar la tendencia, dar dirección clara y generar
  interés/apetito por operar, considerando audiencia mixta (novatos + expertos).
- **Nueva Regla de oro** (enunciado principal): *"El cliente debe entender siempre hacia
  dónde se dirige el activo, para saber qué operar."* La regla de "30 segundos" queda
  como criterio de claridad subordinado, no como enunciado principal.

### 2. `CLAUDE.md` — Sección "Registro y tono profesional"

Relajar (no borrar) las tablas "evitar/usar":
- Sigue prohibido: lenguaje extremo, catastrófico, coloquial, atribuir emociones al
  mercado, vaticinar finales catastróficos.
- Se permite: énfasis direccional persuasivo, señalar la tendencia con claridad, invitar
  a operar.
- Añadir nota que explica el equilibrio (profesional ≠ neutral sin dirección).
- Actualizar memoria `feedback_registro_tono_profesional.md` para reflejar el matiz.

### 3. `CLAUDE.md` — "Activos cubiertos"

Añadir que la rotación diaria **puede incluir 1-2 acciones** elegidas por análisis previo.
- Mecanismo definitivo = **market screener (issue futuro)** — marcar como pendiente.
- Fuente interina = las 2 acciones destacadas por `/earnings`.

### 4. `.claude/commands/apertura.md` (pieza "niveles")

- **Terminología**: `Techo/Suelo` → `Soporte/Resistencia` en toda la plantilla del PASO 5
  (rótulos, zona de interés, escenarios) y en los PASOS 4B/4C.
  - Mapeo: `Techo` → `Resistencia`, `Suelo` → `Soporte`.
  - `Resistencia más próxima` / `Resistencia siguiente`, `Soporte más próximo` /
    `Soporte siguiente`.
- **Invertir lista PROHIBIDO (issue #35)**: ahora lo prohibido es `Techo/Suelo`; lo válido
  es `Soporte/Resistencia`.
- **Dirección siempre explícita**: alcista/bajista en escenarios (se mantiene y refuerza).
- **Sesgo del equipo**: nueva línea que nombra el escenario más probable
  (`🧭 Sesgo del equipo: *Alcista/Bajista/Lateral* — [1 línea de por qué]`). Levanta la
  prohibición previa de la línea `Sesgo:`.
- **Señal implícita**: reemplazar el bloque "NO es señal" por "sesgo operativo implícito":
  los niveles se presentan como zonas accionables ("sobre [Resistencia] se activa sesgo
  comprador"), SIN entrada/TP/SL en pesos, SIN contar para el límite 3/semana de
  `/señal`. Mantener la distinción clara con `/señal` (que sí lleva entrada/TP/SL/CLP).
- **Canales de tendencia**: bloque opcional que describe el canal vigente (línea de
  tendencia alcista/bajista con techo y piso del canal) cuando aplique.

### 5. `.claude/commands/dato_macro.md`

- **Filtro por país en la lista (PASO 2) y en el desarrollo**:
  - **Zona Euro**: solo decisión de tasas del BCE. Otros datos euro se omiten.
  - **EE.UU.**: solo 3★ (★★★). Cada uno se enmarca en la narrativa de la **decisión de
    tasas** (¿empuja tasas arriba o abajo?) y se traduce a impacto en **índices
    bursátiles** (US100/US30 suben/bajan).
  - **Chile**: se reduce a **balanza comercial** (eliminar exportaciones de cobre,
    producción manufacturera, ventas minoristas de la cobertura). El resto de datos Chile
    relevantes se mantiene.
- **Temporalidad del impacto**: nueva línea en el mensaje (ambos modos) que indica si el
  efecto es de minutos (scalper) / intradía / swing de jornada / posicional, alineada con
  las 4 etiquetas canónicas de temporalidad de CLAUDE.md.
- **Alto impacto (modo resultado)**: mostrar solo sub-lecturas **anual + mensual** y
  **normal + subyacente** según corresponda; las demás sub-lecturas no se incluyen.

### 6. `.claude/commands/earnings.md`

- Nuevo bloque "⭐ Las 2 más atractivas de la semana" con un "por qué" breve por cada una
  (catalizador/foco del trimestre, peso en el índice).
- Conectar con la sección de rotación de acciones (estas 2 son las candidatas interinas a
  la rotación diaria).

### 7. `.claude/commands/concepto.md`

- El concepto de la semana se **ancla por defecto en los datos macro de la semana** como
  fuente prioritaria (se mantiene la opción técnica como alternativa, pero macro es el
  foco por defecto en PASO 1/PASO 2).

## Fuera de alcance (explícito)

- **Market screener de acciones** (recorrer acciones en MT5 para elegir las 2 mejores):
  issue aparte, más adelante. Aquí solo se documenta la intención y la fuente interina.
- Cambios de código en el MCP `market-data` o en scripts.
- Cambios en otros comandos de día (`/martes`, `/miercoles`, etc.) más allá de lo que
  hereden automáticamente al delegar en `/apertura` y `/dato_macro`.

## Criterios de aceptación

- `CLAUDE.md` refleja el nuevo principio fundamental, la nueva regla de oro y el tono
  equilibrado, sin contradicciones internas con las secciones de formato.
- `/apertura` usa Soporte/Resistencia de forma consistente, incluye sesgo del equipo,
  zonas accionables, canal de tendencia opcional, y ya no afirma "NO es señal" (sí aclara
  que no es señal formal con TP/SL).
- La lista PROHIBIDO de `/apertura` queda coherente con la nueva terminología.
- `/dato_macro` filtra por país (Euro=tasas, EE.UU.=3★+narrativa tasas/índices,
  Chile=balanza comercial) en lista y desarrollo, añade temporalidad de impacto y limita
  sub-lecturas de alto impacto a anual/mensual + normal/subyacente.
- `/earnings` destaca 2 acciones atractivas.
- `/concepto` prioriza datos macro de la semana.
- Memoria `feedback_registro_tono_profesional.md` actualizada al nuevo equilibrio.

## Riesgos

- **Contradicciones residuales**: CLAUDE.md tiene varias referencias cruzadas a tono y a
  terminología de niveles. Revisar coincidencias de `techo/suelo`, "NO es señal",
  "Sesgo prohibido" y la tabla evitar/usar para no dejar restos inconsistentes.
- **Confusión con `/señal`**: hay que mantener nítida la frontera (apertura = sesgo
  implícito sin TP/SL/CLP; señal = formal, con TP/SL/CLP y límite 3/semana).
