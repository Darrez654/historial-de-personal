@echo off
title DHP - Servidor API Local
cd /d "%~dp0"
echo ============================================
echo   DHP - Iniciando Servidor API Local
echo ============================================
echo.
echo   Puerto: 8765
echo   URL:    http://localhost:8765
echo.
echo ============================================
echo.
python api_server.py
pause
