@echo off
echo ========================================
echo    INICIANDO MANAGER DE F1
echo ========================================

echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    pause
    exit /b 1
)

echo.
echo Activando entorno virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: No se pudo activar el entorno virtual
    echo Ejecuta first_run.bat primero
    pause
    exit /b 1
)

echo.
echo ========================================
echo    INICIANDO SERVIDOR WEB...
echo ========================================
echo La aplicacion estara disponible en:
echo http://localhost:5000
echo.
echo Presiona Ctrl+C para detener el servidor
echo.

python run.py

echo.
echo Desactivando entorno virtual...
call venv\Scripts\deactivate.bat

echo.
echo Aplicacion cerrada.
pause