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
