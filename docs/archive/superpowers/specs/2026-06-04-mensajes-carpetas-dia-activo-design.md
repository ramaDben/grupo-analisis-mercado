# Diseño — Reorganización de `data/mensajes/` (día → activo → tipo)

**Issue:** #45
**Fecha:** 2026-06-04
**Rama:** `feat/mensajes-carpetas-dia-activo`

## Problema

`data/mensajes/` es una carpeta plana con ~70 archivos sueltos nombrados
`YYYY-MM-DD_HH-MM_[tipo].txt`. El director pide organizar el contenido en
**carpetas por día y por activo** (issue #45). La "Regla de guardado" actual de
`CLAUDE.md` prescribe explícitamente la ruta plana, y cada comando la replica a
mano (fuente de drift, como el que cerró el issue #35).

`data/mensajes/` está **gitignored** (`.gitignore` línea 17): los archivos son
100% locales, no versionados. Esto hace la migración de bajo riesgo.

## Convención de ruta (nueva)

```
data/mensajes/<YYYY-MM-DD>/<activo>/<tipo>/<HH-MM>_<tipo>.txt
```

- Pieza con activo protagonista:
  `2026-06-04/usdclp/dato_macro/09-01_dato_macro.txt`
- Pieza transversal (sin activo): `<activo>` = `_general`:
  `2026-06-04/_general/pregunta/09-20_pregunta.txt`
- El nombre conserva `<HH-MM>_<tipo>` (auto-descriptivo aunque se mueva).

## Slug de carpeta de activo

Regla determinista: `lowercase(ticker_mt5)` quitando `.spot`, `#` y `/`.

| ticker_mt5 | slug   | ticker_mt5  | slug   |
|------------|--------|-------------|--------|
| USDCLP     | usdclp | US100.spot  | us100  |
| XAUUSD     | xauusd | US500.spot  | us500  |
| WTI.spot   | wti    | US30.spot   | us30   |
| #AAPL      | aapl   | COPPER      | copper |

## Tipos canónicos (carpeta `<tipo>`)

`niveles` (salida de `/apertura`), `dato_macro`, `noticia`, `alerta`,
`encuesta`, `señal`, `concepto`, `pregunta`, `cierre`, `earnings`.
(`respuesta` se sumará en #47.)

## Regla de clasificación activo vs `_general`

- **Carpeta del activo** cuando hay protagonista claro: `niveles`, `señal`, y
  `dato_macro`/`noticia`/`alerta`/`encuesta` cuando giran en torno a un activo.
- **`_general`** lo transversal: `concepto`, `pregunta`, `cierre` semanal,
  encuesta de la semana, `earnings`, paquete dominical.

## Componentes

### 1. Helper `scripts/ruta_mensaje.ps1` (determinista)

Gemelo de `scripts/hora_chile.ps1`. Firma:

```powershell
scripts\ruta_mensaje.ps1 -Fecha "2026-06-04" -Activo "USDCLP" -Tipo "dato_macro" -Hora "09-01"
# -> data/mensajes/2026-06-04/usdclp/dato_macro/09-01_dato_macro.txt
```

- Normaliza `-Activo` al slug (lowercase, sin `.spot`/`#`/`/`).
- Si `-Activo` se omite o es vacío → `_general`.
- Crea las carpetas (`día/activo/tipo`) si no existen (`mkdir -p`).
- Devuelve la ruta completa (relativa al repo) lista para el `Write`.
- Acepta `ticker_mt5` o slug ya normalizado indistintamente.

Los comandos lo invocan antes del `Write`, igual que hoy invocan
`hora_chile.ps1`.

### 2. Migración `scripts/migrar_mensajes.ps1` (una sola vez, idempotente)

- Recorre los `*.txt` planos en `data/mensajes/`.
- Parsea `YYYY-MM-DD_HH-MM_<resto>.txt`: extrae fecha, hora, y del `<resto>`
  detecta el `tipo` (primer token tipo conocido) y el slug de activo si aparece
  (ej. `apertura_usdclp`→usdclp, `niveles_wti`→wti, `dato_macro_eia`→wti).
- Sin activo detectado → `_general`.
- **Mueve** (no borra) cada archivo a la nueva ruta vía `ruta_mensaje.ps1`.
- Modo `-DryRun`: imprime el plan sin mover.
- Idempotente: si un archivo ya está en la estructura nueva, lo ignora.
- Reporta al final los archivos que quedaron en `_general` (revisión manual).

### 3. Documentación y comandos

- `CLAUDE.md`: reescribir **"Regla de guardado"** y la lista de **"Tipos de
  archivo"** con la nueva convención y el uso de `ruta_mensaje.ps1`.
- Actualizar la línea de guardado en todos los comandos que escriben en
  `data/mensajes/` (apertura, dato_macro, noticia, encuesta, señal, concepto,
  pregunta, alerta, earnings + comandos de día) para que llamen al helper.
- `.gitignore`: **sin cambios** (`data/mensajes/` ya ignorado; subcarpetas
  heredan).

## Testing

- `ruta_mensaje.ps1`: casos USDCLP, WTI.spot, #AAPL, activo omitido (`_general`),
  creación de carpetas, idempotencia.
- `migrar_mensajes.ps1`: `-DryRun` sobre el set real; verificar que cuenta de
  archivos antes == después; verificar muestras (con activo y sin activo).

## Fuera de alcance

- Cambiar el formato interno de los mensajes.
- Versionar `data/mensajes/` en git.
- El comando `/respuesta` (issue #47, dependiente de este).
