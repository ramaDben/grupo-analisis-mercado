# DISEÑO TÉCNICO — Conversión determinista de la hora de eventos económicos a hora Chile

## Contexto
Basado en el issue de Discovery [#38](https://github.com/bbenja11/grupo-analisis-mercado/issues/38).

El reloj de la **hora actual** de Chile (PASO 1A de `/dato_macro`) ya es determinista vía `TimeZoneInfo('Pacific SA Standard Time')` (commit `e1181c9`). Pero la **hora de cada evento económico** (PASO 1B punto 3) se convierte "a mano" por el modelo con una instrucción vaga (*"identifica la zona origen y conviértela a hora Chile (CLT/CLST)"*), sin método.

Reproducción confirmada (3-jun-2026): la lista mostró ADP `07:15` (real `08:15`) e ISM Servicios `09:00` (real `10:00`) — ambos −1h, porque se tomaron en **EST (UTC-5)** cuando en junio el Este de EE.UU. está en **EDT (UTC-4)**. Factory Orders y Beige Book, en la misma lista, salieron correctos: el error es **inconsistente intra-lista**, el sello de un método no determinista.

## Objetivo
Hacer la conversión hora-evento→Chile **determinista, consistente y con etiqueta CLT/CLST correcta**, replicando para 1B el patrón que `e1181c9` aplicó a 1A. La conversión nunca debe depender del juicio del modelo ni de la zona (ambigua) en que la fuente muestre las horas.

## Principio de diseño
**Anclar cada dato a la zona horaria de su organismo emisor** (que tiene DST conocido) y convertir con `TimeZoneInfo`. Las zonas de Windows ya aplican el horario de verano automáticamente — prohibido usar offsets fijos (`UTC-5`, `GMT-3`), que son la causa raíz.

---

## Hallazgos clave

- No hay código de conversión: la lógica vive en los prompts de los comandos. El fix es de **prompt + un helper determinista**, no de refactor de código Python.
- 7 comandos heredan el patrón vago: `dato_macro` (fuente), `lunes`, `martes`, `miercoles`, `jueves`, `viernes_am`, `domingo`. Además `noticia`, `alerta`, `earnings`, `accion` muestran horas.
- IDs de zona de Windows verificados (offset/DST correctos hoy):

| Origen | Organismos | Windows TZ ID | DST automático |
|--------|-----------|---------------|----------------|
| EE.UU. (Este) | BLS, ISM, ADP, EIA, Fed | `Eastern Standard Time` | EDT/EST (−4/−5) |
| Zona Euro | Eurostat, BCE | `W. Europe Standard Time` | CEST/CET (+2/+1) |
| China | NBS, Caixin | `China Standard Time` | sin DST (+8) |
| Chile | BCCh, INE | `Pacific SA Standard Time` | CLST/CLT (−3/−4) |
| Reino Unido | BoE | `GMT Standard Time` | BST/GMT (+1/0) |

---

## Cambios por área

### ÁREA A — Helper determinista de conversión (núcleo)

Nuevo script `scripts/hora_chile.ps1` reutilizable. Contrato:

```powershell
# Uso: convierte la hora oficial de un evento (en su zona de origen) a hora Chile + etiqueta.
param(
  [Parameter(Mandatory)][string]$Hora,        # "08:15"  (hora oficial en la zona de origen)
  [Parameter(Mandatory)][string]$ZonaOrigen,  # "Eastern Standard Time"
  [string]$Fecha = (Get-Date -Format 'yyyy-MM-dd')
)
$tzO   = [System.TimeZoneInfo]::FindSystemTimeZoneById($ZonaOrigen)
$tzC   = [System.TimeZoneInfo]::FindSystemTimeZoneById('Pacific SA Standard Time')
$local = [DateTime]::ParseExact("$Fecha $Hora", 'yyyy-MM-dd HH:mm', $null)
$utc   = [System.TimeZoneInfo]::ConvertTimeToUtc($local, $tzO)
$cl    = [System.TimeZoneInfo]::ConvertTimeFromUtc($utc, $tzC)
$etiq  = if ($tzC.IsDaylightSavingTime($cl)) { 'CLST' } else { 'CLT' }
'{0:HH:mm} {1}' -f $cl, $etiq      # ej: "08:15 CLT"
```

Propiedades: determinista, maneja DST de ambas puntas, devuelve la etiqueta correcta (resuelve P9). Verificable con casos del Discovery (ADP 08:15 ET → 08:15 CLT; ISM 10:00 ET → 10:00 CLT).

### ÁREA B — `/dato_macro` PASO 1B (reescritura de la regla de conversión)

Reemplazar *"identifica la zona origen y conviértela a hora Chile (CLT/CLST)"* por un procedimiento explícito:

1. Obtén la hora del evento **en la zona de su organismo emisor** (hora oficial), NO la hora "ya convertida" que muestre investing.com (su zona es ambigua/variable).
2. Mapea el país/organismo a su `Windows TZ ID` (tabla de §Hallazgos).
3. Convierte con `scripts/hora_chile.ps1 -Hora <hh:mm> -ZonaOrigen <id> -Fecha <FECHA>`.
4. Usa el resultado (hora + etiqueta) en la lista del PASO 2 y en el mensaje del PASO 3.
5. Alto impacto (Fed, BCCh, NFP): contrasta la hora oficial contra la fuente del organismo.

**Regla anti-error explícita**: prohibido asumir offsets fijos (`UTC-5`, `GMT-3`) o copiar la hora "tal cual" de un snippet sin identificar su zona.

### ÁREA C — Propagación a comandos de día y afines

`lunes`, `martes`, `miercoles`, `jueves`, `viernes_am`, `domingo` (calendario) + `noticia`, `alerta`, `earnings`, `accion` (horas): redirigir su conversión al procedimiento de `/dato_macro` 1B (referenciar, no duplicar). `earnings` BMO/AMC se ancla a la apertura/cierre de NY vía `Eastern Standard Time` (P12).

### ÁREA D — Regla canónica en CLAUDE.md

Extender la sección *"Fecha y hora actual — regla canónica"*: separar explícitamente (1) **hora actual** (reloj del sistema, ya documentado) de (2) **hora de eventos** (zona de origen + helper). Incluir la tabla de zonas.

### ÁREA E — Limpieza de scripts legacy (P9/P10)

- `scripts/market_data.py:102`, `scripts/mt5_integration.py:256,317`: `datetime.now().strftime("%H:%M CLT")` etiqueta "CLT" estático y usa hora local. Derivar etiqueta del offset real o documentar que dependen de la zona del SO.
- `scripts/senal_manager.py`, `scripts/orquestador.py`: el cálculo de semana con `date.today()` depende de la hora local; documentar el supuesto "máquina en zona Chile".

---

## Riesgos y mitigaciones
- **`tzdata` de Windows desactualizado** (decretos DST de Chile, P8) → el helper hereda el riesgo del SO; mitigación: mantener Windows actualizado; opcionalmente verificar offset esperado en fechas de transición (abr/sep).
- **La fuente no entrega la hora en zona de origen sino "ya convertida"** → la regla anti-error obliga a identificar la zona; en duda, usar la hora del organismo oficial.
- **Magallanes (P11)** → fuera de alcance; se asume Chile continental (Santiago).

## Fuera de alcance
- `get_asset_levels` (MT5) y niveles técnicos.
- Conexión WhatsApp/Evolution API.
- Reescritura de los scripts legacy (solo se documentan/etiquetan; su corrección es secundaria).

---

## Decisión abierta para el director
**¿Helper como script `scripts/hora_chile.ps1` (recomendado) o como bloque canónico inline en CLAUDE.md que el modelo ejecuta cada vez?**
- Script (A): una sola fuente de verdad, testeable, reutilizable. Recomendado.
- Inline (B): sin archivo nuevo, pero repite la lógica en cada comando y es más frágil.

## Plan de implementación (fase apply — NO ejecutar aún)
1. Crear `scripts/hora_chile.ps1` + casos de verificación (ADP, ISM, Eurozona).
2. Reescribir PASO 1B de `.claude/commands/dato_macro.md` (procedimiento + regla anti-error).
3. Propagar en comandos de día y afines (ÁREA C).
4. Extender la regla canónica en `CLAUDE.md` (ÁREA D).
5. Documentar supuestos de scripts legacy (ÁREA E).
6. Validar: re-ejecutar `/dato_macro` del 3-jun y confirmar ADP 08:15 / ISM 10:00; probar una fecha de verano austral (ene) y una de transición (sep).
