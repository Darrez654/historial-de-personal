@echo off
title DHP - RECEPTOR de datos (para tu servidor)
cd /d "%~dp0\.."

echo ============================================
echo   DHP - RECEPTOR DE DATOS
echo ============================================
echo.
echo   Este servidor RECIBE los formularios DHP
echo   desde las computadoras de los usuarios.
echo.
echo   Para USARLO:
echo     1. Despliega este script en tu SERVIDOR
echo     2. Abre el puerto 5000 en el firewall
echo     3. Configura las PC de los usuarios:
echo        DHP_EXTERNAL_API_URL=http://TU_IP:5000/api/dhp/recibir
echo        DHP_EXTERNAL_ENABLED=true
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
%PYTHON_CMD% -m pip install flask flask-cors requests

echo.
echo ============================================
echo   RECEPTOR INICIADO
echo   Escuchando en: http://0.0.0.0:5000
echo   Endpoint:      POST /api/dhp/recibir
echo ============================================
echo.

%PYTHON_CMD% -m receiver.server

pause
