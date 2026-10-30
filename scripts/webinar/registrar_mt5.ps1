<#
.SYNOPSIS
  Registra el protocolo gi-mt5:// para que el botón "Abrir MT5" del lienzo del webinar abra el terminal.

.DESCRIPTION
  Una página web no puede lanzar programas, pero Windows sí asocia protocolos con programas.
  Esto crea HKCU\Software\Classes\gi-mt5 (solo tu usuario, sin administrador) apuntando a terminal64.exe.
  No pasa el enlace como argumento: el terminal se abre solo, o trae al frente la instancia que ya corre.
  Hay que registrarlo una vez por equipo.

.EXAMPLE
  .\registrar_mt5.ps1              # registra, buscando el terminal en ejecución o en la ruta estándar
  .\registrar_mt5.ps1 -Terminal "D:\MT5\terminal64.exe"
  .\registrar_mt5.ps1 -Quitar      # lo deja como estaba
#>
param(
    [switch]$Quitar,
    [string]$Terminal
)

$clave = 'HKCU:\Software\Classes\gi-mt5'

if ($Quitar) {
    if (Test-Path $clave) { Remove-Item $clave -Recurse -Force; 'Protocolo gi-mt5 eliminado.' }
    else { 'No había nada que quitar.' }
    return
}

if (-not $Terminal) {
    $proc = Get-Process terminal64 -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($proc) { $Terminal = $proc.Path }
    else { $Terminal = 'C:\Program Files\MetaTrader 5\terminal64.exe' }
}
if (-not (Test-Path -LiteralPath $Terminal)) {
    throw "No encuentro terminal64.exe en '$Terminal'. Pásalo con -Terminal."
}

New-Item -Path $clave -Value 'URL:GI MetaTrader 5' -Force | Out-Null
New-ItemProperty -Path $clave -Name 'URL Protocol' -Value '' -PropertyType String -Force | Out-Null
New-Item -Path "$clave\shell\open\command" -Value ('"{0}"' -f $Terminal) -Force | Out-Null

"Protocolo gi-mt5:// registrado para: $Terminal"
