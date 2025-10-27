@echo off
echo ========================================
echo    F1 MANAGER - PREPARANDO SSL
echo ========================================

call venv\Scripts\activate.bat

echo Verificando directorios SSL...
if not exist "ssl\live\localhost" (
    echo Creando directorios SSL...
    mkdir "ssl\live\localhost"
)

echo Verificando certificados SSL...
if not exist "ssl\live\localhost\fullchain.pem" (
    echo Certificados no encontrados, generando...
    python generate_ssl.py
    echo.
) else (
    echo Certificados SSL ya existen.
)

echo.
echo Preparacion SSL completada.
echo Ahora ejecuta: start.bat
echo.
pause