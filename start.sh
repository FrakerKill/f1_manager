#!/bin/bash

echo "========================================"
echo "   INICIANDO MANAGER DE F1"
echo "========================================"

echo -n "Verificando Python... "
python3 --version >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR"
    echo "ERROR: Python3 no está instalado o no está en el PATH"
    exit 1
fi
echo "OK"

echo
echo "Activando entorno virtual..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: No se pudo activar el entorno virtual"
    echo "Ejecuta first_run.sh primero"
    exit 1
fi

echo
echo "========================================"
echo "   INICIANDO SERVIDOR WEB..."
echo "========================================"
echo "La aplicación estará disponible en:"
echo "http://localhost:5000"
echo
echo "Presiona Ctrl+C para detener el servidor"
echo

# Ejecutar la aplicación
python3 run.py

echo
echo "Desactivando entorno virtual..."
deactivate

echo
echo "Aplicación cerrada."