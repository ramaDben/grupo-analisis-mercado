# Reorganización de `data/mensajes/` (día → activo → tipo) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reorganizar `data/mensajes/` en `<fecha>/<activo>/<tipo>/` mediante un helper de ruta determinista, migrar los archivos existentes y actualizar la convención en `CLAUDE.md` y los comandos.

**Architecture:** Un helper PowerShell `ruta_mensaje.ps1` (gemelo de `hora_chile.ps1`) centraliza la construcción de la ruta y la creación de carpetas. Un script `migrar_mensajes.ps1` reubica los archivos planos existentes. Los comandos (prosa markdown) pasan a invocar el helper en su línea de guardado.

**Tech Stack:** Windows PowerShell 5.1, archivos markdown de comandos.

**Spec:** `docs/superpowers/specs/2026-06-04-mensajes-carpetas-dia-activo-design.md`

---

### Task 1: Helper `scripts/ruta_mensaje.ps1`

**Files:**
- Create: `scripts/ruta_mensaje.ps1`

- [ ] **Step 1: Escribir el helper**

```powershell
<#
.SYNOPSIS
    Construye la ruta canonica de un mensaje en data/mensajes/ y crea sus carpetas.
.DESCRIPTION
    Convencion (issue #45): data/mensajes/<Fecha>/<activo>/<Tipo>/<Hora>_<Tipo>.txt
    Si -Activo se omite o es vacio, usa "_general". El slug de activo es
    lowercase(ticker_mt5) sin ".spot", "#" ni "/". Gemelo de hora_chile.ps1.
.PARAMETER Fecha
    Fecha del mensaje "yyyy-MM-dd". Por defecto, hoy (hora Chile no necesaria aqui).
.PARAMETER Tipo
    Tipo de pieza: niveles, dato_macro, noticia, alerta, encuesta, senal,
    concepto, pregunta, cierre, earnings.
.PARAMETER Hora
    Marca horaria "HH-mm" (ej: "09-01").
.PARAMETER Activo
    ticker_mt5 o slug (ej: "USDCLP", "WTI.spot", "#AAPL", "usdclp"). Opcional.
.OUTPUTS
    String con la ruta relativa al repo, ej:
    data/mensajes/2026-06-04/usdclp/dato_macro/09-01_dato_macro.txt
.EXAMPLE
    .\ruta_mensaje.ps1 -Fecha "2026-06-04" -Activo "USDCLP" -Tipo "dato_macro" -Hora "09-01"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Fecha,
    [Parameter(Mandatory)][string]$Tipo,
    [Parameter(Mandatory)][string]$Hora,
    [string]$Activo = ''
)

$ErrorActionPreference = 'Stop'

function ConvertTo-Slug([string]$a) {
    if ([string]::IsNullOrWhiteSpace($a)) { return '_general' }
    $s = $a.ToLowerInvariant() -replace '\.spot$', '' -replace '[#/]', ''
    if ([string]::IsNullOrWhiteSpace($s)) { return '_general' }
    return $s
}

$slug = ConvertTo-Slug $Activo
$root = Join-Path $PSScriptRoot '..\data\mensajes'
$dir  = Join-Path (Join-Path (Join-Path $root $Fecha) $slug) $Tipo
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }

$rel = "data/mensajes/$Fecha/$slug/$Tipo/${Hora}_$Tipo.txt"
$rel
```

- [ ] **Step 2: Probar slug con activo, creacion de carpeta e idempotencia**

Run:
```powershell
$p = scripts\ruta_mensaje.ps1 -Fecha "2099-01-01" -Activo "WTI.spot" -Tipo "dato_macro" -Hora "10-30"
if ($p -ne "data/mensajes/2099-01-01/wti/dato_macro/10-30_dato_macro.txt") { throw "RUTA MAL: $p" }
if (-not (Test-Path "data/mensajes/2099-01-01/wti/dato_macro")) { throw "NO CREO CARPETA" }
scripts\ruta_mensaje.ps1 -Fecha "2099-01-01" -Activo "WTI.spot" -Tipo "dato_macro" -Hora "10-30" | Out-Null  # idempotente
"OK slug+carpeta"
```
Expected: imprime `OK slug+carpeta` sin throw.

- [ ] **Step 3: Probar activo omitido (_general) y prefijo #**

Run:
```powershell
$g = scripts\ruta_mensaje.ps1 -Fecha "2099-01-01" -Tipo "pregunta" -Hora "09-20"
if ($g -ne "data/mensajes/2099-01-01/_general/pregunta/09-20_pregunta.txt") { throw "GENERAL MAL: $g" }
$a = scripts\ruta_mensaje.ps1 -Fecha "2099-01-01" -Activo "#AAPL" -Tipo "niveles" -Hora "08-52"
if ($a -ne "data/mensajes/2099-01-01/aapl/niveles/08-52_niveles.txt") { throw "ACCION MAL: $a" }
"OK general+accion"
```
Expected: imprime `OK general+accion`.

- [ ] **Step 4: Limpiar carpeta de prueba y commit**

```powershell
Remove-Item -Recurse -Force "data/mensajes/2099-01-01"
git add scripts/ruta_mensaje.ps1
git commit -m "feat(scripts): helper ruta_mensaje.ps1 para data/mensajes por dia/activo/tipo (#45)"
```

---

### Task 2: Script de migración `scripts/migrar_mensajes.ps1`

**Files:**
- Create: `scripts/migrar_mensajes.ps1`

- [ ] **Step 1: Escribir el script de migración**

```powershell
<#
.SYNOPSIS
    Migra los .txt planos de data/mensajes/ a la estructura <fecha>/<activo>/<tipo>/ (#45).
.DESCRIPTION
    Best-effort, idempotente, no destructivo (mueve, no borra). Usa ruta_mensaje.ps1.
.PARAMETER DryRun
    Imprime el plan sin mover archivos.
#>
[CmdletBinding()]
param([switch]$DryRun)

$ErrorActionPreference = 'Stop'
$root = Join-Path $PSScriptRoot '..\data\mensajes'
$helper = Join-Path $PSScriptRoot 'ruta_mensaje.ps1'

# Slugs de activo conocidos (lowercase). Orden: mas largos primero para evitar choques.
$slugs = @('usdclp','xauusd','us100','us500','us30','wti','copper','dxy','usdidx',
           'aapl','msft','nvda','amzn','jpm','bac','gs','ms','ba','cat','ge','de')
# Tipos canonicos conocidos.
$tipos = @('niveles','dato_macro','noticia','alerta','encuesta','senal','señal',
           'concepto','pregunta','cierre','earnings','apertura','respuesta')

$general = @()
# Solo archivos planos en la raiz (no recursivo): los ya migrados se ignoran.
Get-ChildItem -Path $root -Filter '*.txt' -File | ForEach-Object {
    $name = $_.BaseName  # ej: 2026-06-04_09-01_dato_macro  o  2026-06-02_08-30_niveles_wti
    if ($name -notmatch '^(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})_(.+)$') {
        Write-Warning "No parseable, se omite: $($_.Name)"; return
    }
    $fecha = $Matches[1]; $hora = $Matches[2]; $resto = $Matches[3].ToLowerInvariant()

    # Detectar activo
    $activo = ''
    foreach ($s in $slugs) { if ($resto -match "(^|_)$s(_|$)") { $activo = $s; break } }

    # Detectar tipo: apertura -> niveles; primer tipo conocido presente
    $tipo = ''
    if ($resto -match '(^|_)apertura(_|$)') { $tipo = 'niveles' }
    else {
        foreach ($t in $tipos) {
            if ($resto -match "(^|_)$t(_|$)") { $tipo = ($t -replace 'señal','senal'); break }
        }
    }
    if (-not $tipo) { $tipo = 'noticia' }  # fallback neutro; se reporta abajo si fue _general

    $dest = & $helper -Fecha $fecha -Tipo $tipo -Hora $hora -Activo $activo
    if (-not $activo) { $general += "$($_.Name) -> $dest" }

    if ($DryRun) { Write-Host "$($_.Name)  =>  $dest" }
    else {
        $destAbs = Join-Path (Join-Path $PSScriptRoot '..') $dest
        Move-Item -LiteralPath $_.FullName -Destination $destAbs -Force
    }
}

Write-Host "`n--- Archivos sin activo (a _general), revisar manualmente ---"
$general | ForEach-Object { Write-Host "  $_" }
if ($DryRun) { Write-Host "`n(DryRun: no se movio nada)" }
```

- [ ] **Step 2: Ejecutar en modo DryRun y revisar el plan**

Run:
```powershell
scripts\migrar_mensajes.ps1 -DryRun
```
Expected: lista `archivo => destino` para los ~70 archivos, y al final el bloque de los que van a `_general`. Verificar a ojo que niveles/dato_macro con activo en el nombre se mapean al activo correcto (ej. `..._niveles_wti.txt => .../wti/niveles/...`).

- [ ] **Step 3: Commit del script (aún sin ejecutar la migración real)**

```powershell
git add scripts/migrar_mensajes.ps1
git commit -m "feat(scripts): migrar_mensajes.ps1 reubica mensajes planos a dia/activo/tipo (#45)"
```

---

### Task 3: Actualizar `CLAUDE.md` (Regla de guardado + Tipos)

**Files:**
- Modify: `CLAUDE.md` (sección "Regla de guardado" dentro del flujo de aprobación, y línea "Tipos de archivo")

- [ ] **Step 1: Reescribir la Regla de guardado**

Reemplazar el párrafo que empieza con `**Regla de guardado**:` por:

```markdown
**Regla de guardado**: después de cada aprobación, SIEMPRE guardar el mensaje final en `data/mensajes/` con la estructura **día → activo → tipo** (issue #45). Construir la ruta con el helper determinista `scripts\ruta_mensaje.ps1` (NUNCA armarla a mano):
```powershell
scripts\ruta_mensaje.ps1 -Fecha "2026-06-04" -Activo "USDCLP" -Tipo "dato_macro" -Hora "09-01"
# -> data/mensajes/2026-06-04/usdclp/dato_macro/09-01_dato_macro.txt
```
El helper crea las carpetas y devuelve la ruta lista para `Write`. Si la pieza no tiene un activo protagonista (concepto, pregunta, cierre semanal, encuesta de la semana, earnings, paquete dominical), omitir `-Activo` y el helper la guarda en `_general/`. La hora `HH-mm` sale del reloj de Chile (regla canónica). Usar luego la herramienta Write sobre la ruta devuelta.
```

- [ ] **Step 2: Actualizar la línea de Tipos de archivo**

Reemplazar la línea `**Tipos de archivo**: ...` por:

```markdown
**Tipos de archivo** (carpeta `<tipo>`): niveles, dato_macro, noticia, alerta, encuesta, señal, concepto, pregunta, cierre, earnings. La salida de `/apertura` usa tipo `niveles`.
```

- [ ] **Step 3: Commit**

```powershell
git add CLAUDE.md
git commit -m "docs(CLAUDE): regla de guardado por dia/activo/tipo via ruta_mensaje.ps1 (#45)"
```

---

### Task 4: Actualizar la línea de guardado en los comandos

**Files:**
- Modify: `.claude/commands/apertura.md:177`, `encuesta.md:106`, `curriculo.md:35`, `rencuesta.md:68,79`, `domingo.md:53,88,126,155,185`

- [ ] **Step 1: apertura.md** — reemplazar la línea 177 por:

```markdown
Al aprobar: construye la ruta con `scripts\ruta_mensaje.ps1 -Fecha [FECHA] -Activo [TICKER_MT5] -Tipo niveles -Hora [HH-MM]` y guarda ahí con Write. Muestra el texto listo para copiar. Si WhatsApp MCP no disponible: solo texto + ruta de imagen.
```

- [ ] **Step 2: encuesta.md** — reemplazar la línea 106 por:

```markdown
- Guardar en **un único** archivo cuya ruta da `scripts\ruta_mensaje.ps1 -Fecha [FECHA] -Activo [TICKER_MT5 o omitir si es transversal] -Tipo encuesta -Hora [HH-MM]` (si son varios polls, separados por `━━━━━━━━━━━━━━━━━━━`).
```

- [ ] **Step 3: curriculo.md** — reemplazar la línea 35 por:

```markdown
4. Mostrar al director: "¿Apruebas enviar esta ruta?". Al aprobar, guardar con la ruta de `scripts\ruta_mensaje.ps1 -Fecha [FECHA] -Tipo concepto -Hora [HH-MM]` (transversal → `_general`).
```

- [ ] **Step 4: rencuesta.md** — reemplazar las líneas 68 y 79 (ambas) por:

```markdown
Guardar el mensaje con la ruta de `scripts\ruta_mensaje.ps1 -Fecha [FECHA] -Tipo encuesta -Hora [HH-MM]` (transversal → `_general`).
```

- [ ] **Step 5: domingo.md** — las 5 líneas (53, 88, 126, 155, 185) son piezas del paquete dominical (transversales). Reemplazar cada `Al aprobar: guardar como data/mensajes/YYYY-MM-DD_HH-MM_domingo_<X>.txt` por:

```markdown
Al aprobar: guardar con la ruta de `scripts\ruta_mensaje.ps1 -Fecha [FECHA] -Tipo cierre -Hora [HH-MM]` para el paquete dominical (transversal → `_general/cierre/`).
```
(Usar `-Tipo cierre` para todo el paquete dominical; conservar el contenido de cada pieza.)

- [ ] **Step 6: Verificar que no quedan rutas planas hardcodeadas**

Run:
```powershell
Select-String -Path '.claude/commands/*.md' -Pattern 'data/mensajes/YYYY-MM-DD_HH-MM'
```
Expected: sin resultados.

- [ ] **Step 7: Commit**

```powershell
git add .claude/commands/*.md
git commit -m "refactor(commands): guardado via ruta_mensaje.ps1 (dia/activo/tipo) (#45)"
```

---

### Task 5: Ejecutar la migración real y cerrar

**Files:** ninguno (operación de datos local)

- [ ] **Step 1: Backup rápido y migración real**

```powershell
Copy-Item -Recurse data/mensajes "data/_mensajes_backup_pre45"
scripts\migrar_mensajes.ps1
```

- [ ] **Step 2: Verificar conteo antes == después**

```powershell
$post = (Get-ChildItem -Recurse data/mensajes -Filter *.txt -File | Measure-Object).Count
$bak  = (Get-ChildItem -Recurse data/_mensajes_backup_pre45 -Filter *.txt -File | Measure-Object).Count
if ($post -ne $bak) { throw "CONTEO DISTINTO: post=$post backup=$bak" }
if (Get-ChildItem data/mensajes -Filter *.txt -File) { throw "QUEDARON ARCHIVOS PLANOS EN LA RAIZ" }
"OK conteo=$post, sin archivos planos en raiz"
```
Expected: `OK conteo=<n>, sin archivos planos en raiz`.

- [ ] **Step 3: Eliminar backup tras verificación**

```powershell
Remove-Item -Recurse -Force "data/_mensajes_backup_pre45"
```
(`data/mensajes/` está gitignored, así que la migración no genera diff; no hay commit de datos.)

- [ ] **Step 4: Push y PR**

```powershell
git push -u origin feat/mensajes-carpetas-dia-activo
gh pr create --title "feat: reorganizar data/mensajes por dia/activo/tipo (#45)" --body "Cierra #45. Helper ruta_mensaje.ps1 + migracion + convencion en CLAUDE.md y comandos."
```

---

## Notas de testing

No hay framework de tests (Pester) en el repo; los helpers PowerShell se prueban con invocación directa y aserciones `throw`, igual que el estilo de `hora_chile.ps1`. Las carpetas de prueba (`2099-01-01`) se limpian al final de cada task.
