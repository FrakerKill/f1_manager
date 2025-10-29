# init_db.py
from app import app, db, Driver, Mechanic, Engineer, Circuit, Race, CarComponent, TyreType, WeatherForecast, WeatherChange, Upgrade, Training, ChampionshipStandings
from datetime import datetime, timedelta
import random
import os
from werkzeug.security import generate_password_hash

# ELIMINAR las siguientes funciones de init_db.py (ya están en staff_generator.py):
# - generate_random_name()
# - generate_mechanic_name() 
# - generate_engineer_name()
# - calculate_driver_salary()
# - calculate_mechanic_salary()
# - calculate_engineer_salary()

# Añadir import del nuevo módulo
from staff_generator import generate_initial_staff, generate_random_name

def init_car_components_base():
    """Inicializa componentes base del coche (para referencia de mejoras)"""
    component_types = ['engine', 'aerodynamics', 'brakes', 'suspension']
    print(f"   - Tipos de componentes definidos: {component_types}")
    return component_types

def init_upgrade_system():
    """Inicializa datos del sistema de mejoras"""
    print("   - Sistema de mejoras configurado y listo")

def init_training_system():
    """Inicializa datos del sistema de entrenamientos"""
    print("   - Sistema de entrenamientos configurado y listo")

def init_tyres():
    """Inicializa los tipos de neumáticos"""
    tyre_types = [
        {'name': 'soft', 'dry_performance': 100, 'wet_performance': 45, 'durability': 50, 'warmup_time': 2},
        {'name': 'medium', 'dry_performance': 85, 'wet_performance': 35, 'durability': 75, 'warmup_time': 3},
        {'name': 'hard', 'dry_performance': 70, 'wet_performance': 25, 'durability': 100, 'warmup_time': 4},
        {'name': 'wet', 'dry_performance': 45, 'wet_performance': 85, 'durability': 100, 'warmup_time': 1},
        {'name': 'extreme_wet', 'dry_performance': 30, 'wet_performance': 100, 'durability': 100, 'warmup_time': 1}
    ]
    
    for tyre_data in tyre_types:
        tyre = TyreType(**tyre_data)
        db.session.add(tyre)
    
    db.session.commit()

def init_weather_forecasts():
    """Crea pronósticos meteorológicos para las carreras"""
    races = Race.query.all()
    weather_conditions = ['dry', 'light_rain', 'heavy_rain']
    
    for race in races:
        # Crear pronóstico para cada sesión
        sessions = [
            ('test', race.test_session),
            ('qualifying', race.qualifying_session),
            ('race', race.race_session)
        ]
        
        for session_type, session_time in sessions:
            # 70% probabilidad de seco, 20% lluvia ligera, 10% lluvia fuerte
            condition_weights = [0.7, 0.2, 0.1]
            condition = random.choices(weather_conditions, weights=condition_weights)[0]
            
            forecast = WeatherForecast(
                race_id=race.id,
                session_type=session_type,
                forecast_time=session_time - timedelta(hours=2),  # Pronóstico 2 horas antes
                condition=condition,
                probability=random.uniform(0.6, 0.95)
            )
            db.session.add(forecast)
    
    db.session.commit()

def init_weather_changes():
    """Crea cambios meteorológicos durante las carreras con transiciones lógicas y secuenciales"""
    races = Race.query.all()
    
    for race in races:
        # Para cada carrera, crear 1-3 cambios meteorológicos posibles
        num_changes = random.randint(1, 3)
        
        # Condición inicial de la carrera (basada en el pronóstico de carrera)
        race_forecast = WeatherForecast.query.filter_by(
            race_id=race.id, 
            session_type='race'
        ).first()
        
        current_condition = race_forecast.condition if race_forecast else 'dry'
        last_change_lap = 0
        
        for change_num in range(num_changes):
            # Espaciar cambios mínimamente 10 vueltas entre ellos
            min_lap = last_change_lap + 10
            max_lap = race.circuit.laps - 5 - (num_changes - change_num - 1) * 10
            
            if min_lap >= max_lap:
                break  # No hay espacio para más cambios
                
            change_lap = random.randint(min_lap, max_lap)
            last_change_lap = change_lap
            
            # Transiciones lógicas basadas en la condición actual
            possible_transitions = {
                'dry': ['light_rain'],
                'light_rain': ['dry', 'heavy_rain'],
                'heavy_rain': ['light_rain']
            }
            
            # Verificar transiciones posibles
            if current_condition in possible_transitions:
                to_condition = random.choice(possible_transitions[current_condition])
                
                weather_change = WeatherChange(
                    race_id=race.id,
                    session_type='race',
                    change_lap=change_lap,
                    from_condition=current_condition,
                    to_condition=to_condition,
                    probability=random.uniform(0.3, 0.8)  # 30-80% de probabilidad
                )
                db.session.add(weather_change)
                
                # Actualizar condición actual para el próximo cambio
                current_condition = to_condition
    
    db.session.commit()

def init_database():
    with app.app_context():
        # Verificar si la base de datos ya existe
        db_path = 'instance/f1_manager.db'
        if os.path.exists(db_path):
            print("⚠️  La base de datos ya existe.")
            response = input("¿Quieres borrarla y crear una nueva? (s/N): ")
            if response.lower() != 's':
                print("Operación cancelada.")
                return
            else:
                print("Borrando base de datos existente...")
                # Eliminar archivo de base de datos
                try:
                    os.remove(db_path)
                except OSError as e:
                    print(f"Error al borrar la base de datos: {e}")
                    return
        
        # Crear todas las tablas
        print("Creando tablas de la base de datos...")
        db.create_all()
        
        # Inicializar sistemas de mejoras y entrenamientos
        print("Configurando sistemas de desarrollo...")
        component_types = init_car_components_base()
        init_upgrade_system()
        init_training_system()
        
        # NO crear usuarios de ejemplo - el primer usuario se creará al registrarse
        
        # USAR EL MÓDULO EXTERNO para generar personal inicial
        generate_initial_staff()
        
        # Crear circuitos del calendario 2025
        print("Creando circuitos...")
        circuits_data = [
            {'name': 'Albert Park', 'country': 'Australia', 'timezone': 'Australia/Melbourne', 'laps': 58},
            {'name': 'Circuito Internacional de Shanghái', 'country': 'China', 'timezone': 'Asia/Shanghai', 'laps': 56},
            {'name': 'Circuito Internacional de Suzuka', 'country': 'Japón', 'timezone': 'Asia/Tokyo', 'laps': 53},
            {'name': 'Circuito Internacional de Baréin', 'country': 'Bahréin', 'timezone': 'Asia/Bahrain', 'laps': 57},
            {'name': 'Circuito de Jeddah', 'country': 'Arabia Saudita', 'timezone': 'Asia/Riyadh', 'laps': 50},
            {'name': 'Autódromo Internacional de Miami', 'country': 'Miami', 'timezone': 'America/New_York', 'laps': 57},
            {'name': 'Autódromo Enzo e Dino Ferrari', 'country': 'Emilia-Romaña', 'timezone': 'Europe/Rome', 'laps': 63},
            {'name': 'Circuito de Mónaco', 'country': 'Mónaco', 'timezone': 'Europe/Monaco', 'laps': 78},
            {'name': 'Circuito de Barcelona-Cataluña', 'country': 'España', 'timezone': 'Europe/Madrid', 'laps': 66},
            {'name': 'Circuito Gilles Villeneuve', 'country': 'Canadá', 'timezone': 'America/Toronto', 'laps': 70},
            {'name': 'Red Bull Ring', 'country': 'Austria', 'timezone': 'Europe/Vienna', 'laps': 71},
            {'name': 'Circuito de Silverstone', 'country': 'Gran Bretaña', 'timezone': 'Europe/London', 'laps': 52},
            {'name': 'Hungaroring', 'country': 'Hungría', 'timezone': 'Europe/Budapest', 'laps': 70},
            {'name': 'Circuito de Spa-Francorchamps', 'country': 'Bélgica', 'timezone': 'Europe/Brussels', 'laps': 44},
            {'name': 'Circuito de Zandvoort', 'country': 'Países Bajos', 'timezone': 'Europe/Amsterdam', 'laps': 72},
            {'name': 'Autódromo Nacional de Monza', 'country': 'Italia', 'timezone': 'Europe/Rome', 'laps': 53},
            {'name': 'Circuito Urbano de Bakú', 'country': 'Azerbaiyán', 'timezone': 'Asia/Baku', 'laps': 51},
            {'name': 'Circuito Urbano de Marina Bay', 'country': 'Singapur', 'timezone': 'Asia/Singapore', 'laps': 62},
            {'name': 'Circuito de las Américas', 'country': 'Estados Unidos', 'timezone': 'America/Chicago', 'laps': 56},
            {'name': 'Autódromo Hermanos Rodríguez', 'country': 'México', 'timezone': 'America/Mexico_City', 'laps': 71},
            {'name': 'Autódromo José Carlos Pace', 'country': 'Brasil', 'timezone': 'America/Sao_Paulo', 'laps': 71},
            {'name': 'Circuito Callejero de Las Vegas', 'country': 'Las Vegas', 'timezone': 'America/Los_Angeles', 'laps': 50},
            {'name': 'Circuito Internacional de Losail', 'country': 'Qatar', 'timezone': 'Asia/Qatar', 'laps': 57},
            {'name': 'Circuito de Yas Marina', 'country': 'Abu Dabi', 'timezone': 'Asia/Dubai', 'laps': 55}
        ]
        
        circuits = []
        for circuit_data in circuits_data:
            circuit = Circuit(**circuit_data)
            circuits.append(circuit)
            db.session.add(circuit)
        
        db.session.commit()
        
        # Inicializar neumáticos
        print("Inicializando neumáticos...")
        init_tyres()
        
        # Crear carreras del calendario 2025 con horarios realistas
        print("Creando carreras...")
        base_date = datetime.utcnow().replace(hour=8, minute=0, second=0, microsecond=0)
        for i, circuit in enumerate(circuits):
            race_date = base_date + timedelta(days=i*7)
            
            # Horarios típicos de F1 (todo en UTC)
            # Tests: Viernes 10:00
            # Clasificación: Sábado 14:00  
            # Carrera: Domingo 13:00
            race = Race(
                circuit_id=circuit.id,
                round_number=i + 1,
                season_year=2025,
                test_session=race_date + timedelta(days=2, hours=2),  # Viernes 10:00
                qualifying_session=race_date + timedelta(days=3, hours=5),  # Sábado 14:00
                race_session=race_date + timedelta(days=4, hours=6)  # Domingo 13:00
            )
            db.session.add(race)
        
        db.session.commit()
        
        # Los componentes de coche se crearán cuando el usuario cree su equipo
        
        # Inicializar pronósticos meteorológicos
        print("Creando pronósticos meteorológicos...")
        init_weather_forecasts()
        
        # Inicializar cambios meteorológicos
        print("Configurando cambios meteorológicos...")
        init_weather_changes()
        
        db.session.commit()
        print("✅ Base de datos inicializada correctamente con calendario 2025!")
        print("   - Personal inicial generado usando staff_generator.py")
        print(f"   - 20 pilotos creados (todos disponibles en el mercado)")
        print(f"   - 30 mecánicos creados (todos disponibles en el mercado)") 
        print(f"   - 30 ingenieros creados (todos disponibles en el mercado)")
        print(f"   - {len(circuits)} circuitos del calendario 2025 creados")
        print("   - 5 tipos de neumáticos creados (incluyendo lluvia)")
        print("   - Pronósticos meteorológicos creados para todas las sesiones")
        print("   - Cambios meteorológicos configurados para las carreras")
        
        print("\n🔧 Sistemas de Desarrollo Configurados:")
        print("   - Mejoras de Vehículo:")
        print("     * 4 componentes: Motor, Aerodinámica, Frenos, Suspensión")
        print("     * 3 niveles de mejora (€500K, €1M, €1.5M)")
        print("     * 3 duraciones (1, 2, 3 semanas)")
        print("     * Mejoras: +5/3, +10/6, +15/9 puntos por nivel (fuerza/fiabilidad)")
        print("   - Entrenamientos de Personal:")
        print("     * 3 tipos: Pilotos, Mecánicos, Ingenieros")
        print("     * Atributos específicos por tipo de personal")
        print("     * 3 niveles de entrenamiento (€200K, €400K, €600K)")
        print("     * 3 duraciones (1, 2, 3 semanas)")
        print("     * Mejoras: +3, +6, +9 puntos por nivel")
        
        print("\n📅 Calendario 2025:")
        for i, circuit in enumerate(circuits, 1):
            print(f"   {i:2d}. {circuit.country:15} - {circuit.name} ({circuit.laps} vueltas)")
        
        print("\n💰 Sistema de salarios implementado:")
        print("   - Pilotos: €200K - €15M por carrera")
        print("   - Mecánicos: €50K - €400K por carrera") 
        print("   - Ingenieros: €80K - €600K por carrera")
        print("   - Salarios basados en edad, habilidad y experiencia")
        
        print("\n🎯 Listo para usar:")
        print("   - Los componentes del coche se crearán al registrar un equipo")
        print("   - Sistemas de mejoras y entrenamientos completamente funcionales")
        print("   - Todos los pilotos, mecánicos e ingenieros disponibles para contratar")
        print("   - El calendario completo 2025 está configurado")
        print("   - El primer usuario se creará cuando te registres en la aplicación")

if __name__ == '__main__':
    init_database()