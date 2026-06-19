@echo off
title Hard Squid - Tienda Flask
cd /d "%~dp0"
set DB_PORT=3307

echo.
echo ==========================================
echo   HARD SQUID - TIENDA WEB
echo ==========================================
echo.
echo 1) Antes de continuar, abre XAMPP Control Panel.
echo 2) Presiona START en MySQL. Este proyecto usara el puerto 3307.
echo 3) Si MySQL ya esta en verde, vuelve a esta ventana.
echo.
pause

if not exist ".venv\Scripts\python.exe" (
  echo.
  echo Creando entorno virtual...
  py -m venv .venv
)

call ".venv\Scripts\activate.bat"

echo.
echo Revisando dependencias...
python -m pip show Flask >nul 2>nul
if errorlevel 1 (
  python -m pip install -r requirements.txt
)

echo.
echo Preparando base de datos hard_squid...
echo Puerto MySQL: %DB_PORT%
flask --app app init-db
if errorlevel 1 (
  echo.
  echo No se pudo conectar con MySQL.
  echo Abre XAMPP como administrador, inicia MySQL y vuelve a ejecutar este archivo.
  echo No cierres esta ventana sin leer el error de arriba.
  echo.
  pause
  exit /b 1
)

echo.
echo Abriendo la tienda en el navegador...
start http://127.0.0.1:5000
echo.
echo Si el navegador no abre solo, entra a:
echo http://127.0.0.1:5000
echo.
echo Usuario administrador:
echo admin@hardsquid.mx
echo Contrasena:
echo Admin123!
echo.
flask --app app run --debug
pause
