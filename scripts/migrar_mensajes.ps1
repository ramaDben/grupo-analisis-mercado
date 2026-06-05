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
$script:planned = @()  # destinos ya asignados (para dedup, incluso en DryRun)
# Solo archivos planos en la raiz (no recursivo): los ya migrados se ignoran.
Get-ChildItem -Path $root -Filter '*.txt' -File | ForEach-Object {
    $name = $_.BaseName  # ej: 2026-06-04_09-01_dato_macro  o  2026-06-02_08-30_niveles_wti
    if ($name -match '^(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2})_(.+)$') {
        $fecha = $Matches[1]; $hora = $Matches[2]; $resto = $Matches[3].ToLowerInvariant()
    }
    elseif ($name -match '^(\d{4}-\d{2}-\d{2})_(.+)$') {
        # Archivo antiguo sin marca HH-MM: hora fallback 00-00 (revisar manualmente).
        $fecha = $Matches[1]; $hora = '00-00'; $resto = $Matches[2].ToLowerInvariant()
    }
    else {
        Write-Warning "No parseable, se omite: $($_.Name)"; return
    }

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

    # Evitar colisiones: varios archivos pueden compartir fecha/hora/tipo/activo
    # (ej. concepto_1, concepto_2). Sufijar _2, _3... para no perder ninguno.
    $destAbs = Join-Path (Join-Path $PSScriptRoot '..') $dest
    if ((Test-Path $destAbs) -or ($script:planned -contains $destAbs)) {
        $i = 2
        do {
            $cand = [System.IO.Path]::ChangeExtension($destAbs, $null).TrimEnd('.') + "_$i.txt"
            $i++
        } while ((Test-Path $cand) -or ($script:planned -contains $cand))
        $destAbs = $cand
        $dest = $dest -replace '\.txt$', "_$($i-1).txt"
    }
    $script:planned += $destAbs

    if (-not $activo) { $general += "$($_.Name) -> $dest" }

    if ($DryRun) { Write-Host "$($_.Name)  =>  $dest" }
    else {
        Move-Item -LiteralPath $_.FullName -Destination $destAbs -Force
    }
}

Write-Host "`n--- Archivos sin activo (a _general), revisar manualmente ---"
$general | ForEach-Object { Write-Host "  $_" }
if ($DryRun) { Write-Host "`n(DryRun: no se movio nada)" }
