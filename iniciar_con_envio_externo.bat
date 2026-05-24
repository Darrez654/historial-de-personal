@echo off
title DHP - CON ENVIO A SERVIDOR EXTERNO
cd /d "%~dp0"

echo ============================================
echo   DHP - CON ENVIO A SERVIDOR EXTERNO
echo ============================================
echo.
echo   IMPORTANTE: Configura las variables abajo
echo   ANTES de ejecutar.
echo.
echo ============================================
echo.

:: ===================================================
:: CONFIGURACION - EDITAR SEGUN TU SERVIDOR
:: ===================================================
:: URL de tu servidor donde corre receiver_api.py
set DHP_EXTERNAL_API_URL=http://localhost:5000/api/dhp/recibir

:: API Key (opcional, coincide con RECEIVER_API_KEY)
set DHP_EXTERNAL_API_KEY=mi-clave-secreta

:: Activar envio externo
set DHP_EXTERNAL_ENABLED=true
:: ===================================================

echo   Enviando datos a: %DHP_EXTERNAL_API_URL%
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
    %PYTHON_CMD% -m pip install -r requirements.txt
) else (
    %PYTHON_CMD% -m pip install streamlit flask flask-cors pandas requests
)
echo.

:: Iniciar API en segundo plano (con las variables de entorno)
echo [+] Iniciando API Local (reenvio externo ACTIVADO)...
start "DHP-API" cmd /c "%PYTHON_CMD% api_server.py"
timeout /t 2 /nobreak >nul

:: Iniciar Streamlit
echo [+] Iniciando Streamlit con envio externo activado...
%PYTHON_CMD% -m streamlit run app_streamlit.py

echo.
pause
