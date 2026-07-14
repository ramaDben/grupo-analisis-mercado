<#
.SYNOPSIS
    Construye la ruta canonica de una Story GI en data/stories/ y crea sus carpetas.
.DESCRIPTION
    Convencion (issue #109): data/stories/<Fecha>/<activo>/<Plantilla>/<Hora>_<Plantilla>.png
    Si -Activo se omite o es vacio, usa "_general". El slug de activo es
    lowercase(ticker_mt5) sin ".spot", "#" ni "/". Gemelo de ruta_mensaje.ps1 (#45),
    sin modificarlo (RNF1 del design de #109).
.PARAMETER Fecha
    Fecha de la Story "yyyy-MM-dd". Por defecto, hoy (hora Chile no necesaria aqui).
.PARAMETER Plantilla
    Nombre de la plantilla renderizada: alerta (piloto #109); las demas llegan
    con #111-#115.
.PARAMETER Hora
    Marca horaria "HH-mm" (ej: "11-45").
.PARAMETER Activo
    ticker_mt5 o slug (ej: "XAUUSD", "WTI.spot", "#AAPL", "usdclp"). Opcional.
.OUTPUTS
    String con la ruta relativa al repo, ej:
    data/stories/2026-07-13/xauusd/alerta/11-45_alerta.png
.EXAMPLE
    .\ruta_story.ps1 -Fecha "2026-07-13" -Activo "XAUUSD" -Plantilla "alerta" -Hora "11-45"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Fecha,
    [Parameter(Mandatory)][string]$Plantilla,
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
$root = Join-Path $PSScriptRoot '..\data\stories'
$dir  = Join-Path (Join-Path (Join-Path $root $Fecha) $slug) $Plantilla
if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }

$rel = "data/stories/$Fecha/$slug/$Plantilla/${Hora}_$Plantilla.png"
$rel
