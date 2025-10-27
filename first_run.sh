#!/bin/bash

echo "========================================"
echo "   INICIALIZACION PRIMERA VEZ"
echo "========================================"

echo -n "Verificando Python... "
python3 --version >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR"
    echo "ERROR: Python3 no está instalado o no está en el PATH"
    echo "En Ubuntu/Debian: sudo apt install python3 python3-venv"
    echo "En CentOS/RHEL: sudo yum install python3"
    echo "En macOS: brew install python"
    exit 1
fi
echo "OK"

echo
echo "Creando entorno virtual..."
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "ERROR: No se pudo crear el entorno virtual"
    exit 1
fi

echo
echo "Activando entorno virtual..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: No se pudo activar el entorno virtual"
    exit 1
fi

echo
echo "Actualizando pip..."
pip install --upgrade pip >/dev/null 2>&1

echo
echo "Instalando dependencias..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: No se pudieron instalar las dependencias"
    exit 1
fi

echo
echo "Creando base de datos inicial..."
python3 init_db.py
if [ $? -ne 0 ]; then
    echo "ERROR: No se pudo crear la base de datos"
    exit 1
fi

echo
echo "========================================"
echo "   INICIALIZACION COMPLETADA"
echo "========================================"
echo
echo "Ahora puedes usar start.sh para ejecutar la aplicación"
echo "sin perder tus datos."
echo
echo "Para activar manualmente el entorno virtual:"
echo "source venv/bin/activate"
echo