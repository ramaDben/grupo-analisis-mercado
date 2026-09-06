@echo off
rem punto-de-entrada: tarea programada de Windows GI-CalculadoraLotaje (verificada Ready el 2026-09-06); tambien se corre a mano
setlocal enabledelayedexpansion
rem ============================================================================
rem Refresco de la calculadora de lotaje publica (Grupo Inteligencia).
rem
rem Lee MT5, regenera el index.html del sitio y lo publica en GitHub Pages.
rem Pensado para el Programador de tareas de Windows, pero se puede correr a mano.
rem
rem Requisitos: MT5 abierto y logueado en la cuenta CLP del broker.
rem Si el generador falla, NO se publica nada: queda la version anterior.
rem
rem Codigos de salida: 0 publicado o sin cambios | 1 generador fallo | 2 git fallo
rem ============================================================================

set "REPO=C:\Users\bbrav\grupo-analisis-mercado"
set "SITIO=C:\Users\bbrav\gi-calculadora-lotaje"
set "UV=C:\Users\bbrav\.local\bin\uv.exe"
set "LOG=%USERPROFILE%\calculadora-lotaje.log"

echo. >> "%LOG%"
echo ===== %date% %time% ===== >> "%LOG%"

if not exist "%UV%" (
    echo ERROR: no se encontro uv en %UV% >> "%LOG%"
    exit /b 1
)

pushd "%REPO%" || (echo ERROR: no se pudo entrar a %REPO% >> "%LOG%" & exit /b 1)

"%UV%" run --with MetaTrader5 python scripts\generar_calculadora.py --out "%SITIO%\index.html" >> "%LOG%" 2>&1
if errorlevel 1 (
    echo RESULTADO: el generador fallo, no se publica ^(queda la version anterior^) >> "%LOG%"
    popd
    exit /b 1
)

popd

git -C "%SITIO%" add index.html >> "%LOG%" 2>&1

git -C "%SITIO%" diff --cached --quiet
if not errorlevel 1 (
    echo RESULTADO: el HTML no cambio, no se publica >> "%LOG%"
    exit /b 0
)

git -C "%SITIO%" commit -m "chore: refresco de datos del broker" >> "%LOG%" 2>&1
if errorlevel 1 (
    echo ERROR: fallo el commit >> "%LOG%"
    exit /b 2
)

git -C "%SITIO%" push origin main >> "%LOG%" 2>&1
if errorlevel 1 (
    echo ERROR: fallo el push ^(revisar credenciales de git^) >> "%LOG%"
    exit /b 2
)

echo RESULTADO: publicado en https://ramadben.github.io/gi-calculadora-lotaje/ >> "%LOG%"
exit /b 0
