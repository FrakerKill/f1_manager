F1 Manager - Simulador de Gestión de Equipo de Fórmula 1

https://img.shields.io/badge/F1-Manager-blue
https://img.shields.io/badge/Python-3.8%252B-green
https://img.shields.io/badge/Flask-2.0%252B-lightgrey

Una aplicación web de simulación estratégica donde gestionas tu propio equipo de Fórmula 1. Contrata pilotos, personal técnico, desarrolla tu coche y compite en carreras con estrategias dinámicas.
🚀 Características Principales
👥 Gestión de Equipo

    Pilotos: Contrata y gestiona hasta 2 pilotos con estadísticas únicas (habilidad, experiencia, consistencia)
    Mecánicos: Equipo de 4 mecánicos especializados en paradas en boxes y fiabilidad
    Ingenieros: 4 ingenieros para desarrollo técnico e innovación
    Componentes del coche: Mejora motor, chasis, aerodinámica y electrónica

🏁 Simulación de Carreras

    Sesiones de Práctica: Realiza tests para recopilar datos de rendimiento
    Calificación: Sistema de Q1, Q2, Q3 para determinar la parrilla de salida
    Carrera Principal: Simulación completa con estrategias, cambios climáticos y incidentes
    Condiciones Meteorológicas: Pronósticos dinámicos que afectan el rendimiento

📊 Mercado y Economía

    Mercado de Transferencias: Contrata pilotos y personal disponible
    Gestión de Presupuesto: Controla salarios y finanzas del equipo
    Relación Valor: Indicadores de costo-beneficio para contrataciones

🎯 Estrategia en Tiempo Real

    Neumáticos: 5 tipos diferentes con características únicas
    Paradas en Boxes: Estrategias de múltiples paradas
    Gestión de Desgaste: Monitoriza el estado de neumáticos y componentes
    Incidentes Dinámicos: Trompos, pinchazos, condiciones climáticas

🛠️ Instalación
Prerrequisitos

    Python 3.8 o superior
    pip (gestor de paquetes de Python)

Instalación Automática
Windows
cmd
first_run.bat

Linux/macOS
bash

chmod +x first_run.sh
./first_run.sh

Instalación Manual
bash

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Inicializar base de datos
python init_db.py

🚀 Ejecución
Windows
cmd
start.bat

Linux/macOS
bash
chmod +x start.sh
./start.sh

Manual
bash

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Ejecutar aplicación
python run.py

La aplicación estará disponible en: http://localhost:5000
🎮 Cómo Jugar

    Configura tu Equipo: Elige nombre y presupuesto inicial
    Contrata Personal: Ve al mercado para contratar pilotos y personal
    Desarrolla el Coche: Mejora los componentes del monoplaza
    Participa en Carreras:
        Realiza sesiones de práctica para recoger datos
        Establece estrategias de neumáticos y paradas
        Compite en calificación y carrera
    Gestiona Finanzas: Controla salarios y presupuesto

📁 Estructura del Proyecto
text

f1-manager/
├── app/
│   ├── templates/          # Plantillas HTML
│   ├── static/            # Archivos estáticos (CSS, JS, imágenes)
│   ├── models.py          # Modelos de datos
│   ├── routes.py          # Rutas de la aplicación
│   └── simulation.py      # Lógica de simulación
├── venv/                  # Entorno virtual (generado)
├── requirements.txt       # Dependencias de Python
├── init_db.py            # Inicialización de base de datos
├── run.py                # Punto de entrada de la aplicación
├── first_run.bat         # Instalador Windows
├── first_run.sh          # Instalador Unix
├── start.bat             # Ejecutor Windows
└── start.sh              # Ejecutor Unix

🛠️ Tecnologías Utilizadas

    Backend: Python, Flask, SQLite
    Frontend: HTML5, CSS3, JavaScript, Bootstrap 5
    Base de Datos: SQLAlchemy ORM
    Simulación: Lógica personalizada para carreras y estrategias

🎯 Características Técnicas

    Sistema de simulación realista de neumáticos y desgaste
    Modelo climático dinámico con probabilidades
    Gestión económica con salarios y presupuestos
    Base de datos persistente para progreso del jugador
    Interfaz responsive compatible con dispositivos móviles

🤝 Contribuir

Las contribuciones son bienvenidas. Para cambios importantes:

    Fork el proyecto
    Crea una rama para tu feature (git checkout -b feature/AmazingFeature)
    Commit tus cambios (git commit -m 'Add some AmazingFeature')
    Push a la rama (git push origin feature/AmazingFeature)
    Abre un Pull Request

📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo LICENSE para detalles.
🆕 Próximas Características

    Modo carrera con temporada completa
    Desarrollo técnico de componentes
    Contratos y renovaciones
    Sistema de sponsors
    Multijugador online

¿Listo para convertirte en el próximo jefe de equipo de F1? 🏆
