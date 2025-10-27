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
echo "La aplicación estará disponible en:"
echo "http://localhost:5000"
echo ""
echo "Logs guardados en: $LOG_FILE"
echo "Presiona Ctrl+C para detener el servidor"
echo ""

# Registrar en log
echo "" >> "$LOG_FILE"
echo "[$(date +%T)] ========================================" >> "$LOG_FILE"
echo "[$(date +%T)]    INICIANDO SERVIDOR WEB..." >> "$LOG_FILE"
echo "[$(date +%T)] ========================================" >> "$LOG_FILE"
echo "[$(date +%T)] Aplicación disponible en: http://localhost:5000" >> "$LOG_FILE"

# Función para manejar la señal de interrupción
cleanup() {
    echo "" >> "$LOG_FILE"
    echo "[$(date +%T)] Servidor detenido por el usuario" >> "$LOG_FILE"
    echo "Desactivando entorno virtual..." >> "$LOG_FILE"
    deactivate
    echo "[$(date +%T)] Entorno virtual desactivado" >> "$LOG_FILE"
    echo "Aplicación cerrada. Logs guardados en: $LOG_FILE"
    exit 0
}

# Configurar trap para Ctrl+C
trap cleanup SIGINT

# Ejecutar la aplicación y redirigir salida al log
echo "[$(date +%T)] Ejecutando: python3 run.py" >> "$LOG_FILE"
python3 run.py >> "$LOG_FILE" 2>&1

# Registrar cierre normal
echo "" >> "$LOG_FILE"
echo "[$(date +%T)] Servidor detenido normalmente" >> "$LOG_FILE"
echo "[$(date +%T)] Desactivando entorno virtual..." >> "$LOG_FILE"
deactivate
echo "[$(date +%T)] Entorno virtual desactivado" >> "$LOG_FILE"

echo ""
echo "Aplicación cerrada."
echo "Logs guardados en: $LOG_FILE"