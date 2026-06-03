<#
.SYNOPSIS
    Convierte la hora oficial de un evento económico (en la zona de su organismo
    emisor) a hora de Chile, con la etiqueta CLT/CLST correcta.

.DESCRIPTION
    Resuelve de forma DETERMINISTA el desfase de ±1h documentado en el issue #38
    (ver docs/design/conversion-hora-eventos.design.md). Usa TimeZoneInfo, que
    aplica el horario de verano de ambas puntas automáticamente. NUNCA usar
    offsets fijos (UTC-5, GMT-3): esa asunción es la causa raíz del bug.

.PARAMETER Hora
    Hora oficial del evento en su zona de origen, formato 24h "HH:mm" (ej: "08:15").

.PARAMETER ZonaOrigen
    ID de zona horaria de Windows del organismo emisor. Valores canónicos:
      EE.UU. (BLS/ISM/ADP/EIA/Fed) -> "Eastern Standard Time"
      Zona Euro (Eurostat/BCE)     -> "W. Europe Standard Time"
      China (NBS/Caixin)           -> "China Standard Time"
      Chile (BCCh/INE)             -> "Pacific SA Standard Time"
      Reino Unido (BoE)            -> "GMT Standard Time"

.PARAMETER Fecha
    Fecha del evento "yyyy-MM-dd". Por defecto, hoy. Importa porque el offset
    depende de la fecha (horario de verano).

.OUTPUTS
    String "HH:mm CLT" o "HH:mm CLST" (ej: "08:15 CLT").

.EXAMPLE
    .\hora_chile.ps1 -Hora "08:15" -ZonaOrigen "Eastern Standard Time" -Fecha "2026-06-03"
    # -> "08:15 CLT"   (ADP: 08:15 ET en junio = 08:15 en Chile, NO 07:15)
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Hora,
    [Parameter(Mandatory)][string]$ZonaOrigen,
    [string]$Fecha = (Get-Date -Format 'yyyy-MM-dd')
)

$ErrorActionPreference = 'Stop'

try {
    $tzOrigen = [System.TimeZoneInfo]::FindSystemTimeZoneById($ZonaOrigen)
} catch {
    throw "Zona de origen desconocida: '$ZonaOrigen'. Usa un ID de Windows valido (ej: 'Eastern Standard Time'). Ver docs/design/conversion-hora-eventos.design.md."
}
$tzChile = [System.TimeZoneInfo]::FindSystemTimeZoneById('Pacific SA Standard Time')

$local = [DateTime]::ParseExact("$Fecha $Hora", 'yyyy-MM-dd HH:mm', [System.Globalization.CultureInfo]::InvariantCulture)
$utc   = [System.TimeZoneInfo]::ConvertTimeToUtc($local, $tzOrigen)
$cl    = [System.TimeZoneInfo]::ConvertTimeFromUtc($utc, $tzChile)
$etiq  = if ($tzChile.IsDaylightSavingTime($cl)) { 'CLST' } else { 'CLT' }

'{0:HH:mm} {1}' -f $cl, $etiq
