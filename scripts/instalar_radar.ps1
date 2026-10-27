# punto-de-entrada: lo corre el director a mano para registrar la tarea GI-Radar
<#
.SYNOPSIS
  Registra la tarea programada del radar multifractal en el Programador de tareas de Windows.

.DESCRIPTION
  El radar corre de lunes a viernes a las 07:30 hora de Santiago y genera la matriz
  HTML interna con los activos que presentan confluencia de eventos tecnicos sobre
  sus lineas.

  Por que una tarea programada propia y no un momento del reloj de sucesos (spec 4.3):
  El reloj de sucesos es el canal de publicacion hacia clientes y cada momento
  mapea obligatoriamente a un canal de salida (lo impone test_todo_momento_llega_a_algun_canal).
  El radar es una herramienta interna del director (cockpit) que no publica nada a clientes.
  Ademas, las 07:30 Santiago se pisaria con el momento avisos_agenda (07:45 Santiago)
  dentro de la ventana de 20 minutos (lo impone test_ningun_par_de_momentos_se_pisa_en_ningun_desfase_del_ano).
  Por ello, cuenta con su propia tarea independiente 'GI-Radar'.

  A las 07:30 en Santiago no hay riesgo de salto de hora: los cambios de horario en Chile
  ocurren siempre a medianoche, por lo que las 07:30 siempre existe como hora valida.

.PARAMETER Instalar
  Registra la tarea. Sin este parametro el script solo muestra que haria.

.PARAMETER Quitar
  Elimina la tarea.

.EXAMPLE
  scripts\instalar_radar.ps1              # muestra que haria, no toca nada
  scripts\instalar_radar.ps1 -Instalar    # registra la tarea GI-Radar
  scripts\instalar_radar.ps1 -Quitar      # la elimina
#>
param(
    [switch]$Instalar,
    [switch]$Quitar
)

$ErrorActionPreference = "Stop"
$Tarea = "GI-Radar"
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

# uvw es uv sin consola: con uv.exe el proceso abriria una ventana de consola.
# El radar lee MT5, por lo que requiere MetaTrader5 en el entorno.
$Uvw = Join-Path (Split-Path -Parent $Uv.Source) "uvw.exe"
if (-not (Test-Path $Uvw)) {
    Write-Host "No encuentro uvw.exe junto a $($Uv.Source); sin el, se abriria una ventana."
    exit 1
}

$Argumentos = "run --with MetaTrader5 python scripts/radar_multifractal.py --sin-abrir"
$Accion = New-ScheduledTaskAction `
    -Execute $Uvw `
    -Argument $Argumentos `
    -WorkingDirectory $Repo

# Disparador semanal: lunes a viernes a las 07:30 hora local (Santiago).
# 07:30 siempre existe en Santiago porque el cambio de horario ocurre a medianoche.
$Disparador = New-ScheduledTaskTrigger -Weekly `
    -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
    -At 07:30

# Configuracion de energia y ejecucion:
# StartWhenAvailable para correr si el equipo estaba apagado a las 07:30.
# AllowStartIfOnBatteries y DontStopIfGoingOnBatteries para no fallar en laptops desenchufados.
# Limite de 30 minutos e IgnoreNew para no solapar ejecuciones.
$Config = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 30) `
    -MultipleInstances IgnoreNew

Write-Host "Tarea      : $Tarea"
Write-Host "Comando    : $Uvw $Argumentos"
Write-Host "Directorio : $Repo"
Write-Host "Disparador : Lunes a Viernes a las 07:30"
Write-Host "Limite     : 30 min por corrida, sin instancias paralelas"
Write-Host ""

if (-not $Instalar) {
    Write-Host "Esto es solo una vista previa. Para registrarla:"
    Write-Host "  scripts\instalar_radar.ps1 -Instalar"
    exit 0
}

if (Get-ScheduledTask -TaskName $Tarea -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $Tarea -Confirm:$false
    Write-Host "Tarea previa eliminada."
}

Register-ScheduledTask -TaskName $Tarea -Action $Accion -Trigger $Disparador `
    -Settings $Config -Description "Radar multifractal de Grupo Inteligencia. Genera la matriz visual matutina en HTML; no envia nada." | Out-Null

Write-Host "Tarea '$Tarea' registrada. Para probar el radar ahora mismo:"
Write-Host "  uv run --with MetaTrader5 python scripts/radar_multifractal.py"
