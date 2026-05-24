@echo off
setlocal EnableExtensions
title DHP - Sistema Historial Personal
cd /d "%~dp0\.."

echo ============================================
echo   DHP - Declaracion de Historial Personal
echo ============================================
echo.
echo   OTROS ACCESOS DISPONIBLES:
echo   - iniciar_todo.bat           (API + Streamlit)
echo   - iniciar_api.bat            (solo API)
echo   - iniciar_receptor.bat       (servidor remoto)
echo   - iniciar_con_envio_externo  (con envio a tu app)
echo.
echo Carpeta: %CD%
echo.

set "PYTHON_CMD="

:: Preferir el lanzador "py" de Windows
where py >nul 2>nul
if %errorlevel% equ 0 (
    py -3 -c "import sys" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=py -3"
        goto python_ok
    )
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    python -c "import sys" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=python"
        goto python_ok
    )
)

echo [ERROR] No se encontro Python usable en este equipo.
echo.
echo Solucion:
echo   1. Instale Python desde https://www.python.org/downloads/
echo   2. Durante la instalacion marque "Add python.exe to PATH"
echo   3. Desactive el alias de la Microsoft Store:
echo      Configuracion - Aplicaciones - Alias de ejecucion
echo      Desactivar "python.exe" y "python3.exe"
echo.
goto fin_error

:python_ok
echo [OK] Python detectado: %PYTHON_CMD%
echo.

if not exist "app\controllers\web.py" (
    echo [ERROR] No se encuentra app/controllers/web.py.
    echo Ejecute este archivo desde la carpeta del proyecto DHP.
    goto fin_error
)

if exist requirements.txt (
    echo [+] Instalando o actualizando dependencias...
    %PYTHON_CMD% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Fallo la instalacion de dependencias.
        goto fin_error
    )
    echo.
) else (
    echo [+] Instalando dependencias basicas...
    %PYTHON_CMD% -m pip install streamlit flask flask-cors pandas requests
    if errorlevel 1 goto fin_error
    echo.
)

echo [+] Iniciando aplicacion (Streamlit + API de base de datos)...
echo [+] El navegador se abrira automaticamente.
echo [+] Para cerrar el servidor: Ctrl+C en esta ventana.
echo.

%PYTHON_CMD% -m streamlit run app/controllers/web.py

echo.
if errorlevel 1 (
    echo [ERROR] Streamlit termino con un error.
) else (
    echo [INFO] La aplicacion se cerro.
)
goto fin

:fin_error
echo.

:fin
echo Presione una tecla para cerrar esta ventana...
pause >nul
endlocal
