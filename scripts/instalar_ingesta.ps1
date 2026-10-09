<#
.SYNOPSIS
  Registra la ingesta macro en el Programador de tareas de Windows.

.DESCRIPTION
  Hasta ahora `data central/` solo se refrescaba con el hook de arranque de
  Claude Code. Con el bot de analistas corriendo solo, un dia sin abrir una
  sesion dejaba la curva de tasas vencida (umbral de 24 h) y cada pieza salia
  sin el bloque de tasas.

  La tarea late cada hora y llama a `scripts/hook_ingesta_macro.py --refrescar`,
  el mismo modo del hook: si la ultima ingesta tiene menos de 6 h no hace nada,
  y un lock impide dos ingestas a la vez si justo arranca una sesion. Asi el dato
  nunca pasa de ~7 h sin depender de que alguien abra Claude Code.

.PARAMETER Instalar
  Registra la tarea. Sin este parametro el script solo muestra que haria.

.PARAMETER Quitar
  Elimina la tarea.

.EXAMPLE
  scripts\instalar_ingesta.ps1              # muestra que haria, no toca nada
  scripts\instalar_ingesta.ps1 -Instalar    # registra la tarea GI-Ingesta
  scripts\instalar_ingesta.ps1 -Quitar      # la elimina
#>
param(
    [switch]$Instalar,
    [switch]$Quitar,
    [int]$CadaMinutos = 60
)

$ErrorActionPreference = "Stop"
$Tarea = "GI-Ingesta"
$Repo = Split-Path -Parent $PSScriptRoot
$Uv = (Get-Command uv -ErrorAction SilentlyContinue)

if (-not $Uv) {
    Write-Host "No encuentro 'uv' en el PATH. La tarea lo necesita para correr el script."
    exit 1
}

if ($Quitar) {
    if (Get-ScheduledTask -TaskName $Tarea -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $Tarea -Confirm:$false
        Write-Host "Tarea '$Tarea' eliminada."
    } else {
        Write-Host "No existe la tarea '$Tarea'."
    }
    exit 0
}

# uvw es uv sin consola: con uv.exe la tarea abre una ventana de Python cada
# hora. El hijo que lanza la ingesta pide CREATE_NO_WINDOW por el mismo motivo.
$Uvw = Join-Path (Split-Path -Parent $Uv.Source) "uvw.exe"
if (-not (Test-Path $Uvw)) {
    Write-Host "No encuentro uvw.exe junto a $($Uv.Source); sin el, la tarea abriria una ventana."
    exit 1
}
$Argumentos = "run python scripts/hook_ingesta_macro.py --refrescar"
$Accion = New-ScheduledTaskAction -Execute $Uvw -Argument $Argumentos -WorkingDirectory $Repo

# El ancla tiene que ser una hora que EXISTA: la noche en que Chile entra en
# horario de verano la medianoche no ocurre y el Programador rechaza el ancla
# (mismo defecto que se encontro en instalar_reloj.ps1 el 2026-09-06).
$Ancla = (Get-Date).Date
$Zona = [System.TimeZoneInfo]::Local
$Intentos = 0
while ($Zona.IsInvalidTime($Ancla) -and $Intentos -lt (1440 / $CadaMinutos)) {
    $Ancla = $Ancla.AddMinutes($CadaMinutos)
    $Intentos++
}
if ($Zona.IsInvalidTime($Ancla)) {
    Write-Host "No encontre una hora de ancla valida en las proximas 24 h. Esto no deberia pasar."
    exit 1
}

$Disparador = New-ScheduledTaskTrigger -Once -At $Ancla `
    -RepetitionInterval (New-TimeSpan -Minutes $CadaMinutos)

# Los flags de bateria van explicitos: por defecto la tarea no arranca con el
# equipo desenchufado y se corta si lo desenchufas, y las dos cosas fallan en
# silencio. La ingesta medida tarda ~1 min; el limite de 15 cubre una API lenta.
$Config = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 15) `
    -MultipleInstances IgnoreNew

Write-Host "Tarea      : $Tarea"
Write-Host "Comando    : $Uvw $Argumentos"
Write-Host "Directorio : $Repo"
Write-Host "Cadencia   : cada $CadaMinutos minutos; refresca solo si la ingesta tiene mas de 6 h"
Write-Host "Bitacora   : data\logs\hook_ingesta_macro.log"
Write-Host ""

if (-not $Instalar) {
    Write-Host "Esto es solo una vista previa. Para registrarla:"
    Write-Host "  scripts\instalar_ingesta.ps1 -Instalar"
    exit 0
}

if (Get-ScheduledTask -TaskName $Tarea -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $Tarea -Confirm:$false
    Write-Host "Tarea previa eliminada."
}

Register-ScheduledTask -TaskName $Tarea -Action $Accion -Trigger $Disparador `
    -Settings $Config -Description "Ingesta macro de Grupo Inteligencia (data central). Solo baja datos; no envia nada." | Out-Null

Write-Host "Tarea '$Tarea' registrada. Para probarla ahora:"
Write-Host "  Start-ScheduledTask -TaskName $Tarea"
