# punto-de-entrada: orquestador para el Programador de tareas, TODAVIA SIN REGISTRAR. Lo toma la spec de cobertura de eventos macro
# PowerShell script: ejecutar_agenda_macro.ps1
# Orquestador para Windows Task Scheduler o ejecucion manual bajo demanda.

[CmdletBinding()]
param(
    [switch]$Force,
    [switch]$SoloAgenda
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BaseDir = Split-Path -Parent $ScriptDir

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " GRUPO INTELIGENCIA -- ECOSISTEMA DE DATOS MACRO Y REPORTES" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

if ($SoloAgenda) {
    & python "$BaseDir\.agents\skills\ecosistema-datos-macro\scripts\agenda.py"
    exit 0
}

# 1. Consultar Agenda
& python "$BaseDir\.agents\skills\ecosistema-datos-macro\scripts\agenda.py"

# 2. Ejecutar Ingesta
$argsPipeline = @()
if ($Force) {
    $argsPipeline += "--force"
}

Write-Host ""
Write-Host "Ejecutando pipeline de ingesta..." -ForegroundColor Yellow
& python "$BaseDir\.agents\skills\ecosistema-datos-macro\scripts\pipeline_ingesta.py" @argsPipeline

Write-Host ""
Write-Host "Proceso completado exitosamente." -ForegroundColor Green
