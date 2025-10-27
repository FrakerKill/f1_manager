#!/bin/bash

echo "========================================"
echo "   INICIANDO MANAGER DE F1"
echo "========================================"

# Crear carpeta de logs si no existe
mkdir -p logs

# Obtener fecha para el archivo de log
LOG_DATE=$(date +%Y-%m-%d)
LOG_FILE="logs/f1_manager_${LOG_DATE}.log"

# Iniciar log
echo "[$(date +%T)] Iniciando F1 Manager..." > "$LOG_FILE"

echo "[$(date +%T)] Verificando Python..." >> "$LOG_FILE"
python3 --version >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "[$(date +%T)] ERROR: Python3 no está instalado" >> "$LOG_FILE"
    echo "ERROR: Python3 no está instalado o no está en el PATH"
    exit 1
fi

echo "" >> "$LOG_FILE"
echo "[$(date +%T)] Activando entorno virtual..." >> "$LOG_FILE"
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "[$(date +%T)] ERROR: No se pudo activar el entorno virtual" >> "$LOG_FILE"
    echo "ERROR: No se pudo activar el entorno virtual"
    echo "Ejecuta first_run.sh primero"
    exit 1
fi

# Mostrar información al usuario
echo "========================================"
echo "   INICIANDO SERVIDOR WEB..."
echo "========================================"
echo "Buscando direcciones disponibles..."
echo "Logs guardados en: $LOG_FILE"
echo "Presiona Ctrl+C para detener el servidor"
echo ""

# Registrar en log
echo "" >> "$LOG_FILE"
echo "[$(date +%T)] ========================================" >> "$LOG_FILE"
echo "[$(date +%T)]    INICIANDO SERVIDOR WEB..." >> "$LOG_FILE"
echo "[$(date +%T)] ========================================" >> "$LOG_FILE"

# Función para extraer y mostrar direcciones
show_addresses() {
    while IFS= read -r line; do
        echo "$line" >> "$LOG_FILE"
        if echo "$line" | grep -q "Running on"; then
            echo "$line"
        fi
    done
}

# Configurar trap para Ctrl+C
cleanup() {
    echo "" >> "$LOG_FILE"
    echo "[$(date +%T)] Servidor detenido por el usuario" >> "$LOG_FILE"
    echo "Desactivando entorno virtual..." >> "$LOG_FILE"
    deactivate
    echo "[$(date +%T)] Entorno virtual desactivado" >> "$LOG_FILE"
    echo "Aplicación cerrada. Logs guardados en: $LOG_FILE"
    exit 0
}

trap cleanup SIGINT

# Ejecutar y procesar salida
echo "[$(date +%T)] Ejecutando: python3 run.py" >> "$LOG_FILE"
python3 run.py 2>&1 | show_addresses

# Si llegamos aquí, el servidor se detuvo
echo "" >> "$LOG_FILE"
echo "[$(date +%T)] Servidor detenido normalmente" >> "$LOG_FILE"
echo "[$(date +%T)] Desactivando entorno virtual..." >> "$LOG_FILE"
deactivate
echo "[$(date +%T)] Entorno virtual desactivado" >> "$LOG_FILE"

echo ""
echo "Aplicación cerrada."
echo "Logs guardados en: $LOG_FILE"