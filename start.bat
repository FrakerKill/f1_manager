@echo off
setlocal EnableDelayedExpansion

echo ========================================
echo    INICIANDO MANAGER DE F1
echo ========================================

:: Crear carpeta de logs si no existe
if not exist "logs" mkdir logs

:: Usar PowerShell para obtener fecha sin espacios
for /f "delims=" %%i in ('powershell -Command "Get-Date -Format 'yyyy-MM-dd'"') do set LOG_DATE=%%i
set LOG_FILE=logs\f1_manager_%LOG_DATE%.log

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

echo ========================================
echo    INICIANDO SERVIDOR WEB...
echo ========================================
echo La aplicacion estara disponible en:
echo.
echo Logs guardados en: %LOG_FILE%
echo Presiona Ctrl+C para detener el servidor
echo.

echo [%time%] Iniciando servidor Flask... >> "%LOG_FILE%"
echo [%time%] Ejecutando: python run.py >> "%LOG_FILE%"

:: Ejecutar Flask y capturar TODA la salida
echo [%time%] --- INICIO EJECUCION FLASK --- >> "%LOG_FILE%"
python run.py >> "%LOG_FILE%" 2>&1
set FLASK_EXIT_CODE=%errorlevel%
echo [%time%] --- FIN EJECUCION FLASK (Codigo: !FLASK_EXIT_CODE!) --- >> "%LOG_FILE%"

echo. >> "%LOG_FILE%"
echo [%time%] Servidor detenido >> "%LOG_FILE%"
echo [%time%] Desactivando entorno virtual... >> "%LOG_FILE%"
call venv\Scripts\deactivate.bat
echo [%time%] Entorno virtual desactivado >> "%LOG_FILE%"

echo.
echo Aplicacion cerrada.
echo Logs guardados en: %LOG_FILE%
pause