@echo off
echo ========================================
echo    INICIALIZACION PRIMERA VEZ
echo ========================================

echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no esta instalado o no esta en el PATH
    pause
    exit /b 1
)

echo.
echo Creando entorno virtual...
python -m venv venv
if errorlevel 1 (
    echo ERROR: No se pudo crear el entorno virtual
    pause
    exit /b 1
)

echo.
echo Activando entorno virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: No se pudo activar el entorno virtual
    pause
    exit /b 1
)

echo.
echo Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: No se pudieron instalar las dependencias
    pause
    exit /b 1
)

echo.
echo Creando base de datos inicial...
python init_db.py
if errorlevel 1 (
    echo ERROR: No se pudo crear la base de datos
    pause
    exit /b 1
)

echo.
echo ========================================
echo    INICIALIZACION COMPLETADA
echo ========================================
echo.
echo Ahora puedes usar start.bat para ejecutar la aplicacion
echo sin perder tus datos.
echo.
pause