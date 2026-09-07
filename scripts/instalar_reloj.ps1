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

# El ancla del disparador tiene que ser una hora que EXISTA.
#
# La version anterior anclaba a `(Get-Date).Date`, la medianoche de hoy, para
# que los latidos cayeran en :00/:15/:30/:45. Y el 2026-09-06 el instalador no
# pudo registrar la tarea: Chile entro en horario de verano esa madrugada,
# el reloj salto de las 23:59 a la 01:00 y **la medianoche de ese dia no
# existio**. El Programador de tareas rechaza el ancla con "el valor
# especificado representa una hora no valida".
#
# Es exactamente el defecto del que advierte el diseno del reloj, aplicado a su
# propio instalador: dos veces al ano hay horas locales que no ocurren, y una
# tarea anclada a una de ellas no se registra o no dispara nunca. Asi que el
# ancla se corre hacia adelante en pasos de $CadaMinutos hasta dar con una hora
# real, conservando la fase de :00/:15/:30/:45.
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
if ($Intentos -gt 0) {
    Write-Host ("Aviso: la medianoche de hoy no existe en {0} (cambio de hora). " -f $Zona.Id +
                "El ancla se corrio a {0:HH:mm}." -f $Ancla)
}

# Un solo disparador que repite indefinidamente. La ventana es todo el dia a
# proposito: acotarla seria otro parametro que puede quedar mal cuando el
# desfase se mueve, y el costo de un latido es un proceso que lee dos JSON.
$Disparador = New-ScheduledTaskTrigger -Once -At $Ancla `
    -RepetitionInterval (New-TimeSpan -Minutes $CadaMinutos)

# Los dos flags de bateria van explicitos porque el Programador de tareas los
# pone en True por defecto, y con eso el latido NO ARRANCA con el equipo
# desenchufado y SE CORTA si lo desenchufas a mitad de corrida. Las dos cosas
# fallan en silencio: la tarea figura "Ready", nadie ve un error, y la tanda de
# las 09:30 simplemente no existe. El costo de un latido es un proceso que lee
# dos JSON, asi que la bateria no es una razon para saltarselo.
$Config = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -DontStopOnIdleEnd `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
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
