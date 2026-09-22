<#
.SYNOPSIS
    Iniciador blindado de la Jornada Matutina para Grupo Inteligencia.
.DESCRIPTION
    Encadena los gates de seguridad y ejecuta el flujo de apertura matutina:
    1. Diagnóstico de MT5, WhatsApp y navegadores.
    2. Ingesta soberana y cadena de datos macro (pipeline_datos.py).
    3. Agenda económica y alertas de sesión.
    4. Escáner cuantitativo (pipeline_carrusel.py --preparar).
    5. Auditoría con linter editorial (sin voseo, sin guiones largos).
    6. Renderizado de gráficos TradingView 300 DPI.
    7. Certificación visual en GI · Banco de Pruebas.
    8. Despacho oficial con protección anti-envío accidental.
.EXAMPLE
    .\scripts\iniciar_jornada.ps1 -Diagnostico
    .\scripts\iniciar_jornada.ps1 -Todo
    .\scripts\iniciar_jornada.ps1 -Despachar -Confirmar
#>
[CmdletBinding()]
param (
    [switch]$Diagnostico,
    [switch]$Datos,
    [switch]$Agenda,
    [switch]$Preparar,
    [switch]$Auditar,
    [switch]$Rendir,
    [switch]$Probar,
    [switch]$Despachar,
    [switch]$Confirmar,
    [switch]$Todo,
    [int]$Top = 3,
    [switch]$Matriz,
    [string]$Tanda = ""
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir

# Argumentos base para el orquestador Python
$pyArgs = @("run", "--with", "MetaTrader5", "python", "scripts/jornada_matutina.py")

if ($Diagnostico) {
    $pyArgs += "--diagnostico"
} elseif ($Datos) {
    $pyArgs += "--datos"
} elseif ($Agenda) {
    $pyArgs += "--agenda"
} elseif ($Preparar) {
    $pyArgs += "--preparar"
    $pyArgs += "--top"
    $pyArgs += $Top.ToString()
    if ($Matriz) { $pyArgs += "--matriz" }
} elseif ($Auditar) {
    $pyArgs += "--auditar"
    if ($Tanda) { $pyArgs += $Tanda }
} elseif ($Rendir) {
    $pyArgs += "--rendir"
    if ($Tanda) { $pyArgs += $Tanda }
} elseif ($Probar) {
    $pyArgs += "--probar"
    if ($Tanda) { $pyArgs += $Tanda }
} elseif ($Despachar) {
    $pyArgs += "--despachar"
    if ($Tanda) { $pyArgs += $Tanda }
    if ($Confirmar) { $pyArgs += "--confirmar" }
} elseif ($Todo) {
    $pyArgs += "--todo"
    if ($Confirmar) { $pyArgs += "--confirmar" }
} else {
    # Por defecto, ejecuta diagnóstico y ayuda
    Write-Host "Iniciador de Jornada Matutina · Grupo Inteligencia" -ForegroundColor Cyan
    Write-Host "Uso disponible:"
    Write-Host "  .\scripts\iniciar_jornada.ps1 -Diagnostico   (Verifica salud de MT5, WhatsApp y navegador)"
    Write-Host "  .\scripts\iniciar_jornada.ps1 -Datos         (Ejecuta cadena de datos macroeconómicos)"
    Write-Host "  .\scripts\iniciar_jornada.ps1 -Agenda        (Consulta eventos y blackouts del día)"
    Write-Host "  .\scripts\iniciar_jornada.ps1 -Preparar      (Ejecuta escáner cuantitativo)"
    Write-Host "  .\scripts\iniciar_jornada.ps1 -Auditar       (Audita textos con linter editorial)"
    Write-Host "  .\scripts\iniciar_jornada.ps1 -Rendir        (Genera gráficos TradingView 300 DPI)"
    Write-Host "  .\scripts\iniciar_jornada.ps1 -Probar        (Envía prueba a GI · Banco de Pruebas)"
    Write-Host "  .\scripts\iniciar_jornada.ps1 -Despachar -Confirmar (Emite a canales oficiales)"
    Write-Host "  .\scripts\iniciar_jornada.ps1 -Todo          (Ejecuta el flujo secuencial completo)"
    exit 0
}

Push-Location $RepoRoot
try {
    & uv $pyArgs
} finally {
    Pop-Location
}
