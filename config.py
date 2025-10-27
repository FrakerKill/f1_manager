import os
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'f1-manager-super-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'f1_manager.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de sesión
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # Configuración del juego
    STARTING_MONEY = 20000000  # 20 millones
    MAX_DRIVERS = 2
    MAX_MECHANICS = 4
    MAX_ENGINEERS = 4
    DRIVER_RETIREMENT_AGE = 40
    MECHANIC_RETIREMENT_AGE = 60  # Nuevo: retiro de mecánicos a 60 años
    ENGINEER_RETIREMENT_AGE = 70