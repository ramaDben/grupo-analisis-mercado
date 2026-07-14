# DISEÑO TÉCNICO — Formato único de mensajes de niveles (`/apertura` PASO 5)

> Issue: #35 · Rama: `fix/35-niveles-formato-unico`

## Contexto

Cuando se ejecuta un comando de día (`/martes`, `/miercoles`, `/jueves`, `/viernes_am`, `/lunes`) y se generan niveles vía `/apertura`, los mensajes salen con **formato inconsistente** entre ejecuciones y respecto al estándar acordado. La auditoría de `data/mensajes/` confirmó *drift* en 6 ejes (terminología, fecha, escenarios, indicador, emoji de precio, nº de niveles).

**Estándar de referencia (fuente de verdad):** `data/mensajes/2026-06-02_08-31_niveles_us100.txt`.

**Causa raíz:** la plantilla de render del **PASO 5 de `.claude/commands/apertura.md`** diverge del estándar (usa "Techo 1/Suelo 1", omite T2/Su2, no fija el formato de fecha y no prohíbe variantes). Al no ser fuente de verdad estricta, el modelo improvisa cada vez.

## Decisiones del director (confirmadas)

1. **Terminología única**: `Techo más próximo / Techo siguiente / Suelo más próximo / Suelo siguiente`. **Prohibido**: `Resistencia/Soporte`, `objetivo/inmediato/fuerte`. (Alineado al fix #33.)
2. **Niveles**: "más próximo" de cada lado **siempre**; "siguiente" (T2/Su2) **opcional** (solo si el director los ingresó).
3. **Unificación total**: todo mensaje de niveles tras comando diario usa EXACTAMENTE la plantilla canónica. Se eliminan los formatos propios (USD/CLP "Sesgo del día", "Seguimiento RSI 4H").

---

## Plantilla canónica (carácter por carácter)

Esta es la **única** salida válida del PASO 5. Las líneas `[entre corchetes]` son sustituciones; las líneas marcadas `← opcional` se **omiten por completo** (sin dejar línea en blanco) cuando no aplican.

```text
🎯 Activo: [NOMBRE ACTIVO]
📌 Nivel a vigilar: [T1 o Su1 según sesgo]
⚡ Qué esperar: [1 línea de acción concreta]
━━━━━━━━━━━━━━━━━━━

📊 *APERTURA DE MERCADO — [D de mes de YYYY]*
━━━━━━━━━━━━━━━━━━━
📈 *[NOMBRE ACTIVO]* — Niveles en [TEMPORALIDAD]
{{lectura_temporalidad}}

💰 Precio actual: [precio]
• Techo más próximo: [T1]
• Techo siguiente: [T2]          ← opcional (solo si hay T2)
• Suelo más próximo: [Su1]
• Suelo siguiente: [Su2]         ← opcional (solo si hay Su2)
• Zona de interés: [Su1] – [T1]
{{lectura_indicador}}            ← opcional (solo si RSI/ATR)

🔎 ¿Qué lo mueve hoy?
[Drivers del activo en 2-3 líneas simples, consulta config/drivers.json]

━━━━━━━━━━━━━━━━━━━
🟢 *Alcista* — Precio sobre [T1] → tendencia compradora (intra-day)
🟡 *Esperar* — Entre [Su1] y [T1] → sin confirmación de dirección
🔴 *Bajista* — Precio bajo [Su1] → tendencia vendedora (intra-day)
━━━━━━━━━━━━━━━━━━━
{{lectura_temporalidad}}
```

### Reglas de las sustituciones

- **`[NOMBRE ACTIVO]`**: el `nombre` legible de `config/activos.json` (ej. "Nasdaq 100", "Petróleo WTI", "Dólar / Peso Chileno (USD/CLP)").
- **`[D de mes de YYYY]`**: fecha en hora Chile, formato `2 de junio de 2026`. **Sin** día de la semana ("martes"), **sin** abreviar, **sin** sustituir por el nombre del activo.
- **`{{lectura_temporalidad}}`** (aparece 2 veces: tras el título y al cierre):

  | TF | Línea |
  |----|-------|
  | 15M | `_Lectura en 15M — marco scalper (movimientos rápidos del día)_` |
  | 1H  | `_Lectura en 1H — marco intradía corto_` |
  | 4H  | `_Lectura en 4H — marco intradía / swing corto_` |
  | 1D  | `_Lectura en 1D — lectura general del activo_` |

- **`[precio]` y todos los niveles**: respetar `digits` de `config/activos.json` (regla MT5). Nunca truncar ceros.
- **Orden de niveles**: primero todos los **techos** (más próximo, luego siguiente), después todos los **suelos** (más próximo, luego siguiente), después **Zona de interés**. La zona usa siempre los "más próximos": `[Suelo más próximo] – [Techo más próximo]`.
- **`{{lectura_indicador}}`** (omitir si "Limpio"):
  - RSI → `📐 RSI [TF]: [rsi_14] — [sobrecompra >70 / sobreventa <30 / neutro]`
  - ATR → `📐 ATR [TF]: [atr_14] — volatilidad de referencia del marco`
- **`[T1 o Su1 según sesgo]`** del encabezado: si el precio actual está más cerca del techo / con sesgo alcista, usar T1; si está sobre el suelo / sesgo bajista, usar Su1.

---

## Cambios concretos respecto al PASO 5 actual

| Aspecto | Actual (`apertura.md` PASO 5) | Nuevo (canónico) |
|---|---|---|
| Niveles | `• Techo 1: [T1]` / `• Suelo 1: [Su1]` | `• Techo más próximo: [T1]` / `• Suelo más próximo: [Su1]` |
| T2/Su2 | **No se renderizan** | `• Techo siguiente` / `• Suelo siguiente` opcionales |
| Fecha | `[FECHA]` (ambiguo) | `[D de mes de YYYY]` con ejemplo explícito |
| Emoji precio | `💰 Precio actual` (ya OK) | sin cambio, pero se **prohíbe** `📊`/`📌` como rótulo de precio |
| Indicador | `📐 RSI [TF]:` (ya OK) | sin cambio, pero se **prohíbe** `⚠️ *RSI*` y `• RSI:` inline |

### Bloque nuevo en REGLAS GENERALES de `apertura.md`

Agregar lista explícita de **PROHIBIDO** para cerrarle la puerta al *drift*:

- ❌ `Resistencia` / `Soporte` (usar Techo/Suelo).
- ❌ `Techo objetivo` / `Techo inmediato` / `Suelo fuerte` (usar más próximo/siguiente).
- ❌ `📊 *Precio actual*` o `📌 Precio actual` como rótulo de precio (usar `💰 Precio actual`).
- ❌ `⚠️ *RSI*` o `• RSI:` inline (usar `📐 RSI [TF]:`).
- ❌ Día de la semana en la fecha del encabezado (`martes 2 de junio` → `2 de junio de 2026`).
- ❌ Bloque de escenarios con orden invertido o emoji duplicado (`🟢 Sobre X → *Alcista* 🟢`). El orden canónico es `🟢 *Alcista* — Precio sobre X → ... (intra-day)`.

---

## Puntos de integración (comandos de día)

Verificar que **no redefinan formato propio** en su pieza de apertura; deben delegar 100% en `/apertura`:

- `.claude/commands/martes.md` — PIEZA 1
- `.claude/commands/miercoles.md` — PIEZA 1
- `.claude/commands/jueves.md` — PIEZA 1
- `.claude/commands/viernes_am.md` — PIEZA 1 (3 activos)
- `.claude/commands/lunes.md` — bloque de apertura
- `domingo.md` queda **fuera** (su pieza 1 es noticias de fin de semana, no niveles)

`templates/apertura_mercado.txt` — **diverge confirmado**, es fuente secundaria de drift. Diferencias vs estándar:
- `📊 *APERTURA DE MERCADO* — {{fecha}}` (guion/fecha **fuera** de la negrita) vs canónico `📊 *APERTURA DE MERCADO — [fecha]*` (dentro).
- **Falta** la línea `📈 *[Activo]* — Niveles en [TF]`.
- Tiene línea extra `Sesgo: {{sesgo_emoji}} {{sesgo}}` que **no** existe en el estándar.
- `🔎 *¿Qué lo está moviendo?*` (negrita + otra redacción) vs canónico `🔎 ¿Qué lo mueve hoy?` (sin negrita).
- **Falta** el `{{lectura_temporalidad}}` de cierre.
- Lleva un bloque `📰 DATO DEL DÍA` adosado (es otra pieza; no debe ir en el template de niveles).

**Decisión (director)**: el `.txt` se marca **DEPRECADO** (no se alinea). Ningún comando lo consume; se conserva como referencia histórica con un encabezado `⚠️ DEPRECADO (issue #35) — NO USAR`. La fuente de verdad única es el PASO 5 de `apertura.md`.

---

## Fuera de alcance

- El MCP `mcp__market-data__get_asset_levels` **no se toca** (sigue dando price/rsi_14/atr_14).
- La lógica interactiva de PASOS 1-4 (selección de activo/TF/indicador, fetch de precio) **no cambia**; solo cambia el render del PASO 5 y las reglas.
- No se agregan indicadores nuevos (MACD/SMA/Bollinger siguen "Próximamente").

---

## Criterios de aceptación

- [ ] PASO 5 de `apertura.md` reproduce exactamente la plantilla canónica (incluye T2/Su2 opcionales y `[D de mes de YYYY]`).
- [ ] REGLAS GENERALES incluyen la lista de PROHIBIDO.
- [ ] Comandos de día no reintroducen formato propio de niveles.
- [ ] `templates/apertura_mercado.txt` alineado.
- [ ] Validación manual: regenerar mentalmente los 7 mensajes auditados produce estructura idéntica al estándar.
