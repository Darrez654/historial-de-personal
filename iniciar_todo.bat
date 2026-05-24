@echo off
title DHP - Todos los Servicios
cd /d "%~dp0"

echo ============================================
echo   DHP - Iniciando TODOS los servicios
echo ============================================
echo.
echo   [1] API Local     → http://localhost:8765
echo   [2] Streamlit     → http://localhost:8501
echo.
echo ============================================
echo.

:: Verificar Python
where py >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=py -3"
    goto check_python
)
where python >nul 2>nul
if %errorlevel% equ 0 (
    set "PYTHON_CMD=python"
    goto check_python
)
echo [ERROR] No se encontro Python.
pause
exit /b 1

:check_python
echo [OK] Python detectado: %PYTHON_CMD%

:: Instalar dependencias
if exist requirements.txt (
    echo [+] Instalando dependencias...
    %PYTHON_CMD% -m pip install -r requirements.txt
) else (
    %PYTHON_CMD% -m pip install streamlit flask flask-cors pandas requests
)
echo.

:: Iniciar API en segundo plano
echo [+] Iniciando API Local (puerto 8765)...
start "DHP-API" cmd /c "%PYTHON_CMD% api_server.py"
echo.

:: Esperar 2 segundos para que la API arranque
timeout /t 2 /nobreak >nul

:: Iniciar Streamlit
echo [+] Iniciando Streamlit...
echo [+] El navegador se abrira automaticamente.
echo [+] Para cerrar todo: Ctrl+C en esta ventana o cierra las ventanas.
echo.
%PYTHON_CMD% -m streamlit run app_streamlit.py

echo.
echo [INFO] Servicios detenidos.
pause
