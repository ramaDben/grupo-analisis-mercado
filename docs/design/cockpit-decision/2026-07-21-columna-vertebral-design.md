# Cockpit de Decisión del Director — Columna Vertebral (diseño)

> **Fecha:** 2026-07-21
> **Tipo:** diseño técnico vigente (ciclo Pulse) — insumo del issue `[Discovery]` que arranca el flujo SDD.
> **Alcance de este documento:** SOLO la **columna vertebral** (la espina común). Los pilares, las unidades y el screener son issues aparte que se cuelgan de esta espina; aquí se nombran para fijar dependencias, pero **no se diseñan**.

---

## 1. El giro

El repo deja de ser una **fábrica de contenido para clientes** y pasa a ser el **cockpit de decisión personal del director de inversiones y trading**. El mismo motor (MCP `market-data`: MT5 + calendario + specs) se reutiliza, pero el output cambia de raíz:

| Antes | Ahora |
|---|---|
| Genera **mensajes para clientes** (WhatsApp) | Genera **informes de decisión para el director** |
| El foco es publicar contenido diario | El foco es **decidir** con evidencia trazable |
| WhatsApp es el producto | WhatsApp es un **export secundario opcional** |

**Interfaz elegida:** Claude Code como cockpit (consultas/comandos bajo demanda que producen informes de decisión). Sin frontend nuevo. Máximo aprovechamiento del motor actual, mínima ingeniería nueva.

### Relación con "El motor como cerebro de un hub" (GI)
La propuesta `motor-como-cerebro-hub-gi` es **complementaria, no rival**: es una visión de negocio para GI (hub interno/externo vía WordPress) cuyo output es contenido segmentado. El cockpit de decisión **profundiza el motor mismo** — un motor capaz de producir tesis rigurosas con pruebas sería un mejor cerebro para ese hub si algún día avanza. El "modo cliente" que aquí se archiva sigue disponible para alimentar el hub externo. Ambas visiones conviven: una mira hacia afuera (GI), esta mira hacia la decisión del director.

---

## 2. Qué es la columna vertebral

Es la **espina común** de la que cuelgan todas las unidades y todos los pilares. Define cuatro cosas y nada más:

1. **El modelo conceptual** — qué es una Tesis, un Factor, una Decisión.
2. **La política de fuentes** — de dónde sale cada dato y con qué rigor (la "constitución" que heredan los pilares).
3. **La memoria** — cómo y dónde se persiste la tesis en el tiempo.
4. **El archivado del modo cliente** — cómo se retira lo de cliente sin romperlo, y cómo se adelgaza el `CLAUDE.md`.

Sin esta espina, cada pilar produciría datos sueltos que no se pueden juntar en una decisión.

---

## 3. Modelo conceptual

### 3.1 La Tesis = síntesis de factores que convergen

Una tesis (premisa) **no se escribe a mano: emerge** de juntar piezas de evidencia fundamentales y técnicas. La convicción **no es arbitraria: sale del grado de convergencia** de esos factores. Si casi todos apuntan al mismo lado → convicción alta; si hay conflicto → media/baja, y el conflicto se nombra explícitamente (antídoto al sesgo de confirmación).

**Dos capas de horizonte** (la clave de unir inversión + trading):
- **Sesgo de fondo** ← factores fundamentales/macro (semanas/meses) = el lado *inversión / value*.
- **Sesgo táctico** ← factores técnicos (horas/días) = el lado *trading*.
- La acción recomendada **reconcilia ambos** (ej. "de fondo comprador, corto plazo corrigiendo → esperar la corrección para comprar").

### 3.2 El Factor (unidad atómica de evidencia, con prueba)

Cada factor lleva su **ficha de procedencia**: todo es auditable, nada se afirma sin respaldo.

```json
{
  "id": "tec-usdclp-rechazo-945",
  "fuente_pilar": "tecnico | fundamental | macro",
  "nombre": "Rechazo en resistencia 945.00 (4H)",
  "direccion": "alcista | bajista | neutro",
  "peso": "alto | medio | bajo",
  "horizonte": "tactico | fondo",
  "valor": "el precio rechazó 3 veces $945.00 en 4H",
  "procedencia": {
    "fuente": "MT5 (MCP market-data / get_asset_levels)",
    "referencia": "get_asset_levels(USDCLP, H4) @ 2026-07-21 09:30",
    "fecha_dato": "2026-07-21 09:30 CLT",
    "confianza": "alta | media | baja"
  },
  "derivacion": "techo defendido → favorece continuación bajista",
  "nota": ""
}
```

- `confianza`: **alta** = fuente oficial/determinista (MT5, organismo, EDGAR); **media** = agregador citado (Investing.com); **baja** = inferencia/estimación propia. Se muestra siempre.

### 3.3 La Tesis vigente (síntesis)

```json
{
  "activo": "USDCLP",
  "actualizada": "2026-07-21 09:40 CLT",
  "sesgo_fondo": "neutro-bajista",
  "sesgo_tactico": "bajista",
  "conviccion": 3,
  "horizonte_dominante": "swing de jornada (1-3 días)",
  "niveles": { "resistencia": 945.00, "zona_interes": [935.00, 938.00],
               "soporte": 920.00, "invalidacion": 947.50 },
  "factores": [ "...lista de Factores (3.2)..." ],
  "conflictos": ["DXY lateral-alto frena la caída"],
  "accion": "esperar rechazo en 935.00–938.00 para buscar cortos hacia 920.00",
  "catalizador_proximo": "IPC Chile — jueves 08:00 CLT"
}
```

- **Convicción (1–5): juicio razonado, no aritmética ciega.** Es un nivel cualitativo *derivado* del grado de convergencia y justificado en texto — **no** un promedio de pesos (falsa precisión). Va **siempre acompañada del recuento de evidencia visible** (cuántos factores a favor/en contra y con qué peso) para que la base sea auditable sin fingir una fórmula — ver el ejemplo en §6.
- Los **precios respetan `digits` de `config/activos.json`** (USDCLP = 2 → `$945.00`). Regla ya vigente en el repo.

---

## 4. Política de fuentes — rigor máximo *dirigido*

**Regla constitucional (la heredan los 3 pilares):**
> Rastreabilidad total: **todo** factor cita fuente, valor y fecha. Se construye integración propia **solo donde la fuente oficial aporta algo único** — no se duplica lo que un agregador ya entrega idéntico.

| Tipo de dato | Fuente | ¿Integración propia? | Por qué |
|---|---|---|---|
| Precios / niveles / indicadores | MT5 (MCP `market-data`) | Ya existe | Determinista |
| **Número puntual** macro (IPC, NFP, PMI) | Investing.com (`actual` + consenso), con link oficial | **No** | El agregador trae el mismo número; un scraper del INE para el idéntico valor es redundante y frágil |
| **Guidance / decisión** (comunicado FOMC, dot plot/SEP, IPoM y RPM del BCCh, comunicado BCE + Lagarde) | Organismo oficial, directo | **Sí** | El matiz no está en el agregador; pocas fuentes, altísimo valor |
| **Probabilidad de tasas de mercado** (CME FedWatch y análogos) | CME / futuros | **Sí** (nuevo) | "Prueba de mercado" de lo que se espera; central para proyectar tasas |
| **Estados financieros** (Graham) | SEC EDGAR / API financiera | **Sí** (nuevo) | EDGAR es API gratuita, estable y estructurada — rigor máximo *barato* |

Esto da rigor máximo (todo auditable a fuente autoritativa) **sin** gastar esfuerzo en scrapers que leen un número ya disponible.

---

## 5. Memoria — estado vivo + historial

Opción elegida (🅰): por cada activo, **estado vigente + historial append-only**.

```text
data/tesis/<activo_slug>/
├── tesis.md          ← foto ACTUAL legible (se reescribe): sesgo, convicción, niveles, factores, acción
└── historial.jsonl   ← 1 snapshot compacto por cambio relevante (solo se agrega)
```

- `<activo_slug>` = misma convención de `ruta_mensaje.ps1` (`lowercase(ticker_mt5)` sin `.spot`/`#`/`/`).
- `historial.jsonl`: cada línea guarda `{fecha, sesgo_fondo, sesgo_tactico, conviccion, factores_resumen, nota}` — compacto pero **con los factores que sostenían la tesis ese día**, para poder auditar *"¿con qué datos pensaba esto el 14 de julio?"*.
- Se escribe una línea nueva **solo cuando cambia algo relevante** (sesgo, convicción, niveles clave), no en cada consulta — mantiene el archivo liviano.
- Un helper determinista (hermano de `ruta_mensaje.ps1`) construye la ruta y crea carpetas. Los `data/tesis/*` van **gitignored** (como charts/mensajes/stories).

---

## 6. El informe de decisión (output central del cockpit)

Es lo que el director ve al consultar. Se genera con **`/tesis [activo]`**. Estructura canónica (above-the-fold primero, como el resto del repo):

```text
🎯 [ACTIVO] — Informe de decisión           (2026-07-21 09:40 CLT)
Fondo: [sesgo] · Táctico: [sesgo] · Convicción: [N/5]
Acción: [1 línea accionable]
────────────────────────────────────────────
FACTORES QUE CONVERGEN
  Fundamental / Macro (horizonte: fondo)
    [🟢🔴🟡] [nombre]  [peso]  → [derivación]        (fuente · fecha)
  Técnico (horizonte: táctico)
    [🟢🔴🟡] [nombre]  [peso]  → [derivación]        (fuente · fecha)
────────────────────────────────────────────
SÍNTESIS → convicción [N/5]
  Base: [n 🔴 (pesos)] · [n 🟢 (pesos)] · [n 🟡]   ← recuento visible, sin fórmula
  Por qué [N] y no [N±1]: [qué factor de peso contradice o refuerza]
⚠️ Conflicto a vigilar: [qué invalidaría la tesis]
📌 Catalizador próximo: [evento · hora CLT]
────────────────────────────────────────────
🧾 Pruebas: cada factor es auditable (fuente · valor · fecha).
```

Desde este informe, opcionalmente, se deriva el mensaje de WhatsApp (export secundario) reutilizando las reglas de formato de cliente ya existentes.

---

## 7. Archivado del modo cliente + adelgazamiento del `CLAUDE.md`

Primera tarea del issue de columna vertebral (la de mayor ahorro recurrente de tokens):

- Los **25 slash commands de cliente** no se borran: pasan a **modo secundario**. Se mantienen funcionales para el export a WhatsApp, pero dejan de ser el eje del proyecto.
- El **`CLAUDE.md`** se reescribe: hoy es ~90% manual de modo-cliente y se carga entero **cada sesión**. Se adelgaza a un núcleo enfocado en el cockpit de decisión + la política de fuentes, moviendo el detalle de modo-cliente a **`CLAUDE.cliente.md`** (un solo archivo en la raíz), que **no** se auto-carga y solo se lee cuando se usa ese modo. Meta: contexto por sesión mucho más liviano sin perder capacidad.
- **No se toca el motor** (MCP `market-data`, helpers deterministas, `config/activos.json`): se conservan intactos.

---

## 8. Roadmap de issues (Pulse SDD) y dependencias

Cada pieza es un Change independiente con su ciclo `explore → specify → design → apply → review → close`.

```text
[Épico] Reorientar el repo a cockpit de decisión del director
│
├── ⭐ Columna vertebral (ESTE diseño) ── va primero; todo depende de él
│       modelo (Tesis/Factor) · política de fuentes · memoria · archivado modo-cliente
│
├── Pilares (transversales, alimentan unidades y screener; pueden ir en paralelo)
│     ├── Técnico amplio
│     ├── Fundamental Graham
│     └── Radar macro → proyección de tasas (BCCh/Fed/BCE)
│
├── Unidades (dependen de la columna)
│     ├── Watchlist con tesis viva  ← poblado por el Market Screener
│     ├── Libro de posiciones / portafolio
│     ├── Bitácora de decisiones puntuales
│     └── Consulta ad-hoc
│
└── Integración
      └── Market Screener basado en research  ← consume los 3 pilares, puebla el watchlist
```

**Dependencias:** columna vertebral primero → pilares en paralelo → screener necesita los pilares → unidades necesitan la columna. **No se crean todos los issues de golpe**: se arranca solo por la columna vertebral; el resto queda como backlog ordenado.

---

## 9. Decisiones tomadas (validadas 2026-07-21)

1. **Convicción = juicio razonado (1–5), no score aritmético.** Nivel cualitativo justificado por la convergencia, acompañado **siempre** del recuento de evidencia visible (§3.3, §6). Se descarta el promedio de pesos por falsa precisión.
2. **Comando de entrada = `/tesis [activo]`** (alineado con el objeto central del modelo; "premisa" queda como sinónimo).
3. **Manual de modo-cliente = `CLAUDE.cliente.md`** (un solo archivo en la raíz, no auto-cargado).

---

## 10. Criterios de éxito de la columna vertebral

- Existe un **esquema de Factor y de Tesis** documentado que cualquier pilar puede producir/consumir.
- Una tesis se puede **auditar factor por factor** (fuente, valor, fecha).
- La memoria (`tesis.md` + `historial.jsonl`) permite reconstruir **cómo evolucionó** una tesis.
- La política de fuentes está escrita y es la referencia que heredan los pilares.
- El `CLAUDE.md` queda adelgazado y el modo-cliente sigue funcionando en modo secundario.
- **Sin frontend nuevo**; todo corre en Claude Code sobre el motor actual.

---

## 11. Fuera de alcance (explícito)

- El detalle interno de cada pilar (qué indicadores técnicos, qué ratios de Graham, qué método exacto de proyección de tasas) → **issues de pilar**.
- El algoritmo del screener y qué es "research" (multi-factor / value-first / cualitativo) → **issue del screener**.
- Cualquier hub GI, WordPress o API en la nube → visión `motor-como-cerebro-hub-gi`, fuera de este esfuerzo.
