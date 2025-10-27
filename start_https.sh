#!/bin/bash

echo "========================================"
echo "    F1 MANAGER - PREPARANDO SSL"
echo "========================================"

# Activar entorno virtual
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Entorno virtual activado"
else
    echo "Error: No se encontró el entorno virtual"
    echo "Ejecuta first_run.sh primero"
    exit 1
fi

# Verificar y crear directorios SSL
echo "Verificando directorios SSL..."
mkdir -p ssl/live/localhost

# Verificar certificados SSL
echo "Verificando certificados SSL..."
if [ ! -f "ssl/live/localhost/fullchain.pem" ] || [ ! -f "ssl/live/localhost/privkey.pem" ]; then
    echo "Certificados no encontrados, generando..."
    python generate_ssl.py
else
    echo "Certificados SSL ya existen."
fi

echo ""
echo "Preparacion SSL completada."
echo "Ahora ejecuta: ./start.sh"