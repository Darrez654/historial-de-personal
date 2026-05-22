@echo off
title DHP - Servidor Streamlit
echo Iniciando el entorno Streamlit para la aplicacion DHP...
echo.

:: Verificar si Python está instalado
where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        echo [ERROR] No se encontro Python en el sistema.
        echo Por favor, instale Python (https://www.python.org/) y asegurese de marcar la opcion "Add Python to PATH" durante la instalacion.
        echo.
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=py
    )
) else (
    set PYTHON_CMD=python
)

:: Verificar si Streamlit está instalado
%PYTHON_CMD% -c "import streamlit" >nul 2>nul
if %errorlevel% neq 0 (
    echo [+] Streamlit no esta instalado en este entorno de Python.
    echo [+] Intentando instalar Streamlit automaticamente mediante pip...
    echo.
    %PYTHON_CMD% -m pip install streamlit
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] No se pudo instalar Streamlit. Verifique su conexion a internet o ejecute:
        echo   %PYTHON_CMD% -m pip install streamlit
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [+] Streamlit instalado correctamente.
    echo.
)

echo [+] Ejecutando: streamlit run app_streamlit.py
echo.
%PYTHON_CMD% -m streamlit run app_streamlit.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Hubo un problema al ejecutar Streamlit.
    echo.
    pause
)
