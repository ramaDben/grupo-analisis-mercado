# Spec: `/apertura` — niveles ingresados manualmente

**Fase**: Specify  
**Issue**: #14  
**Idea**: `docs/ideas/apertura-niveles-manuales.idea.md`  
**Archivo a modificar**: `.claude/commands/apertura.md`

---

## Cambio en resumen

Reemplazar el **PASO 4** (fetch automático `get_asset_levels`) por un **prompt manual** donde
el director escribe los niveles que observó en su chart de MT5.

Los PASOs 1, 2, 3 y 5 no cambian.

---

## PASO 4 — Nuevo comportamiento (reemplaza el actual)

El paso es **híbrido**: el director ingresa los niveles de precio, el MCP sigue trayendo los indicadores.

### 4A — Prompt manual (niveles)

Para **cada activo**, mostrar al director:

```
📥 Ingresa los niveles para [NOMBRE ACTIVO] ([TEMPORALIDAD]):
  Precio actual:
  Resistencia 1 (R1):
  Resistencia 2 (R2):   ← opcional, escribe "–" para omitir
  Soporte 1 (S1):
  Soporte 2 (S2):       ← opcional, escribe "–" para omitir
```

### 4B — Fetch automático (indicadores)

Solo si el director eligió RSI o ATR en el PASO 3, llamar:

```
mcp__market-data__get_asset_levels({"ticker": "[TICKER_MT5]", "timeframe": "[TF]"})
```

Usar **únicamente** los campos `rsi_14` o `atr_14` del resultado. Ignorar `price, s1, s2, r1, r2, trend`.

Si el resultado contiene `"error"`: mostrar `⚠️ No se pudo obtener [RSI/ATR] desde MT5 — puedes ingresarlo manualmente o continuar sin indicador.` y preguntar al director cómo proceder.

Si el director eligió **Limpio** en PASO 3: omitir el fetch completamente.

### Reglas de parsing (niveles manuales)

- Aceptar número con o sin `$`, coma de miles o espacios.  
  Ejemplos válidos: `889.60`, `$889.60`, `4,539.72`, `4539.72`.
- Normalizar a `float` y formatear según `digits` del activo en `config/activos.json`.
- Si el director escribe `"–"`, `"-"` o deja vacío para R2 o S2: ese nivel se omite del mensaje.
- Si el valor no es numérico: pedir de nuevo con `⚠️ Valor inválido. Ingresa solo el número.`

### Campos

| Campo       | Origen | Obligatorio |
|-------------|--------|-------------|
| Precio actual | Director | Sí |
| R1          | Director | Sí |
| S1          | Director | Sí |
| R2          | Director | No (opcional) |
| S2          | Director | No (opcional) |
| RSI (14)    | MCP (`rsi_14`) | Solo si PASO 3 = RSI |
| ATR (14)    | MCP (`atr_14`) | Solo si PASO 3 = ATR |

---

## PASO 5 — Sin cambios

La plantilla del mensaje y las reglas de formato son idénticas al spec actual.  
La única diferencia es que los valores de precio/niveles/indicador vienen del input del director
en lugar del MCP.

Si R2 o S2 fueron omitidos: no incluir esas líneas en el mensaje final.

---

## Criterios de aceptación

- [ ] El prompt solicita precio actual + R1, R2, S1, S2 (R2/S2 opcionales) al director.
- [ ] El MCP solo se llama para obtener `rsi_14` o `atr_14` si el director eligió RSI o ATR en PASO 3.
- [ ] Si indicador = Limpio, no se llama al MCP en absoluto.
- [ ] R2 y S2 omitidos no generan errores en el render.
- [ ] Error del MCP en fetch de indicador muestra aviso y ofrece ingreso manual o continuar sin indicador.
- [ ] Decimales del output respetan `digits` de `config/activos.json`.
- [ ] El mensaje final (PASO 5) es visualmente idéntico al actual cuando todos los campos están completos.
- [ ] Entrada inválida muestra aviso y repregunta sin abortar.

---

## Notas de implementación

- El cambio es **solo en `.claude/commands/apertura.md`** (documento de instrucciones, no código Python).
- No requiere cambios en `config/`, `scripts/`, `templates/` ni otros comandos.
- Los comandos de día (`/lunes`, `/martes`, etc.) que delegan en `/apertura` heredan el cambio automáticamente.
