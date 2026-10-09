# punto-de-entrada: el director lo corre a mano una vez (docs/bot-analistas.md, Puesta en marcha)
<#
.SYNOPSIS
  Registra el bot de analistas en el Programador de tareas: arranca al iniciar
  sesion y se reinicia si se cae.

.DESCRIPTION
  Corre `scripts/bot_analistas.py --escuchar` con MetaTrader5 y los extras de
  render, el mismo entorno que el despacho (CLAUDE.md, "El despacho se invoca
  con --with MetaTrader5"): sin el paquete, las piezas con precios no salen.

  Arranca AL INICIAR SESION y no al encender el equipo, porque necesita el
  terminal MT5 de la sesion del usuario y la carpeta de Google Drive para
  escritorio, que solo existen con la sesion abierta.

  Dos flags que el Programador pone en contra por defecto y que GI-Reloj ya
  pago caro: sin -AllowStartIfOnBatteries la tarea no arranca con el equipo
  desenchufado, y sin -DontStopIfGoingOnBatteries se corta al desenchufarlo. La
  tarea figura 'Ready' y nadie ve el error.

.PARAMETER Instalar
  Registra la tarea. Sin este parametro el script solo muestra que haria.

.PARAMETER Quitar
  Elimina la tarea.

.EXAMPLE
  scripts\instalar_bot_telegram.ps1              # muestra que haria, no toca nada
  scripts\instalar_bot_telegram.ps1 -Instalar    # registra GI-BotTelegram
  scripts\instalar_bot_telegram.ps1 -Quitar      # la elimina
#>
param(
    [switch]$Instalar,
    [switch]$Quitar
)

$ErrorActionPreference = "Stop"
$Tarea = "GI-BotTelegram"
$Repo = Split-Path -Parent $PSScriptRoot
$Uv = (Get-Command uv -ErrorAction SilentlyContinue)

if (-not $Uv) {
    Write-Host "No encuentro 'uv' en el PATH. La tarea lo necesita para correr el bot."
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

# Sin ventana (pedido del director): conhost --headless le da al bot una consola
# OCULTA, y todo lo que lanza (agy, git, el render) la hereda. Con uvw solo el
# primer proceso queda sin ventana y cada hijo de consola abre la suya. Mismo
# metodo que la tarea GI-CalculadoraLotaje.
$Conhost = Join-Path $env:SystemRoot "System32\conhost.exe"
$Argumentos = "run --with MetaTrader5 --extra stories --extra informe python scripts/bot_analistas.py --escuchar"
$Accion = New-ScheduledTaskAction -Execute $Conhost `
    -Argument "--headless `"$($Uv.Source)`" $Argumentos" -WorkingDirectory $Repo
$Disparador = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

# Sin limite de duracion: el bot escucha todo el dia. Si muere, el Programador
# lo levanta de nuevo cada minuto hasta 10 veces.
$Ajustes = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 10 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -MultipleInstances IgnoreNew

if (-not $Instalar) {
    Write-Host "Tarea:      $Tarea"
    Write-Host "Disparador: al iniciar sesion de $env:USERNAME"
    Write-Host "Comando:    $Conhost --headless `"$($Uv.Source)`" $Argumentos"
    Write-Host "Carpeta:    $Repo"
    Write-Host ""
    Write-Host "No se instalo nada. Para registrarla: scripts\instalar_bot_telegram.ps1 -Instalar"
    exit 0
}

if (Get-ScheduledTask -TaskName $Tarea -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $Tarea -Confirm:$false
}
Register-ScheduledTask -TaskName $Tarea -Action $Accion -Trigger $Disparador -Settings $Ajustes `
    -Description "Bot de Telegram del equipo: piezas a pedido en HTML (docs/bot-analistas.md)" | Out-Null
Write-Host "Tarea '$Tarea' registrada. Arranca en el proximo inicio de sesion, o ahora con:"
Write-Host "  Start-ScheduledTask -TaskName $Tarea"
