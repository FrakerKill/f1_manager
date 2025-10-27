@echo off
setlocal EnableDelayedExpansion

echo ========================================
echo    INICIANDO MANAGER DE F1
echo ========================================

:: Crear carpeta de logs si no existe
if not exist "logs" mkdir logs

:: Obtener fecha para el archivo de log (manejar espacios)
for /f "tokens=1-3 delims=/" %%a in ('date /t') do (
    set _day=%%a
    set _month=%%b
    set _year=%%c
)

:: Eliminar espacios de las variables
set _day=%_day: =%
set _month=%_month: =%
set _year=%_year: =%

:: Asegurar formato de 2 dígitos para día y mes
if !_day! lss 10 set _day=0!_day!
if !_month! lss 10 set _month=0!_month!

set LOG_FILE=logs\f1_manager_%_year%-%_month%-%_day%.log

echo [%time%] Verificando Python... > "%LOG_FILE%"
python --version >nul 2>&1
if errorlevel 1 (
    echo [%time%] ERROR: Python no esta instalado o no esta en el PATH >> "%LOG_FILE%"
    echo ERROR: Python no esta instalado o no esta en el PATH
    pause
    exit /b 1
)
echo [%time%] Python verificado correctamente >> "%LOG_FILE%"

echo. >> "%LOG_FILE%"
echo [%time%] Activando entorno virtual... >> "%LOG_FILE%"
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [%time%] ERROR: No se pudo activar el entorno virtual >> "%LOG_FILE%"
    echo ERROR: No se pudo activar el entorno virtual
    echo Ejecuta first_run.bat primero
    pause
    exit /b 1
)
echo [%time%] Entorno virtual activado >> "%LOG_FILE%"

echo. >> "%LOG_FILE%"
echo [%time%] ======================================== >> "%LOG_FILE%"
echo [%time%]    INICIANDO SERVIDOR WEB... >> "%LOG_FILE%"
echo [%time%] ======================================== >> "%LOG_FILE%"
echo. >> "%LOG_FILE%"

:: Mostrar información al usuario
echo ========================================
echo    INICIANDO SERVIDOR WEB...
echo ========================================
echo La aplicacion estara disponible en:
echo http://localhost:5000
echo.
echo Logs guardados en: %LOG_FILE%
echo Presiona Ctrl+C para detener el servidor
echo.

:: Registrar inicio en log
echo [%time%] Iniciando servidor Flask... >> "%LOG_FILE%"
echo [%time%] Aplicacion disponible en: http://localhost:5000 >> "%LOG_FILE%"

:: Ejecutar la aplicación y redirigir salida al log
echo [%time%] Ejecutando: python run.py >> "%LOG_FILE%"
python run.py 1>> "%LOG_FILE%" 2>&1

:: Registrar cierre
echo. >> "%LOG_FILE%"
echo [%time%] Servidor detenido >> "%LOG_FILE%"

echo. >> "%LOG_FILE%"
echo [%time%] Desactivando entorno virtual... >> "%LOG_FILE%"
call venv\Scripts\deactivate.bat
echo [%time%] Entorno virtual desactivado >> "%LOG_FILE%"

echo.
echo Aplicacion cerrada.
echo Logs guardados en: %LOG_FILE%
pause