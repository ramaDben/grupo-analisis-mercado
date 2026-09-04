<#
.SYNOPSIS
  Registra el latido del reloj de sucesos en el Programador de tareas de Windows.

.DESCRIPTION
  El latido dispara cada 15 minutos y NO sabe nada de mercados: solo llama a
  `scripts/reloj_gi.py --ejecutar`, que lee la agenda, convierte la hora en ese
  momento y decide si a alguna clase de activo le toca salir.

  Por que un latido y no una tarea por momento: el Programador de tareas dispara
  en hora LOCAL. Una tarea a las 08:30 de Chile es 08:30 de Nueva York hoy y
  06:30 de Nueva York en noviembre, dos horas antes del dato que justifica la
  hora. Ademas, la noche en que Chile entra en horario de verano una hora local
  simplemente no existe, asi que una tarea anclada a esa hora no dispararia.

  El reloj SOLO PREPARA. Nada sale a un canal sin la aprobacion del director.

.PARAMETER Instalar
  Registra la tarea. Sin este parametro el script solo muestra que haria.

.PARAMETER Quitar
  Elimina la tarea.

.EXAMPLE
  scripts\instalar_reloj.ps1              # muestra que haria, no toca nada
  scripts\instalar_reloj.ps1 -Instalar    # registra la tarea GI-Reloj
  scripts\instalar_reloj.ps1 -Quitar      # la elimina
#>
param(
    [switch]$Instalar,
    [switch]$Quitar,
    [int]$CadaMinutos = 15
)

$ErrorActionPreference = "Stop"
$Tarea = "GI-Reloj"
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

$Accion = New-ScheduledTaskAction `
    -Execute $Uv.Source `
    -Argument "run python scripts/reloj_gi.py --ejecutar" `
    -WorkingDirectory $Repo

# Un solo disparador que repite indefinidamente. La ventana es todo el dia a
# proposito: acotarla seria otro parametro que puede quedar mal cuando el
# desfase se mueve, y el costo de un latido es un proceso que lee dos JSON.
$Disparador = New-ScheduledTaskTrigger -Once -At (Get-Date).Date `
    -RepetitionInterval (New-TimeSpan -Minutes $CadaMinutos)

$Config = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 20) `
    -MultipleInstances IgnoreNew

Write-Host "Tarea      : $Tarea"
Write-Host "Comando    : $($Uv.Source) run python scripts/reloj_gi.py --ejecutar"
Write-Host "Directorio : $Repo"
Write-Host "Cadencia   : cada $CadaMinutos minutos, todo el dia"
Write-Host "Limite     : 20 min por corrida, sin instancias paralelas"
Write-Host ""

if (-not $Instalar) {
    Write-Host "Esto es solo una vista previa. Para registrarla:"
    Write-Host "  scripts\instalar_reloj.ps1 -Instalar"
    exit 0
}

if (Get-ScheduledTask -TaskName $Tarea -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $Tarea -Confirm:$false
    Write-Host "Tarea previa eliminada."
}

Register-ScheduledTask -TaskName $Tarea -Action $Accion -Trigger $Disparador `
    -Settings $Config -Description "Latido del reloj de sucesos de Grupo Inteligencia. Solo prepara; no envia nada." | Out-Null

Write-Host "Tarea '$Tarea' registrada. Para revisar que decide ahora mismo:"
Write-Host "  uv run python scripts/reloj_gi.py --verificar"
