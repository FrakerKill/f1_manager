from app import app, db, Driver, Mechanic, Engineer, Circuit, Race, CarComponent, TyreType, WeatherForecast, WeatherChange, Upgrade, Training, ChampionshipStandings
from datetime import datetime, timedelta
import random
import os
from werkzeug.security import generate_password_hash

def generate_random_name():
    """Genera nombres aleatorios para pilotos, mecánicos e ingenieros"""
    first_names = [
        'Carlos', 'Fernando', 'Lewis', 'Max', 'Charles', 'Lando', 'George', 'Sergio',
        'Esteban', 'Pierre', 'Valtteri', 'Kevin', 'Daniel', 'Sebastian', 'Kimi', 'Nico',
        'Alex', 'Yuki', 'Zhou', 'Nicholas', 'Mick', 'Lance', 'Antonio', 'Romain',
        'Marcus', 'Robert', 'Jenson', 'Felipe', 'Rubens', 'Giancarlo', 'Heikki', 'Jarno',
        'Mark', 'David', 'Adrian', 'Pastor', 'Bruno', 'Kamui', 'Vitaly', 'Jaime'
    ]
    
    last_names = [
        'Sainz', 'Alonso', 'Hamilton', 'Verstappen', 'Leclerc', 'Norris', 'Russell', 'Pérez',
        'Ocon', 'Gasly', 'Bottas', 'Magnussen', 'Ricciardo', 'Vettel', 'Räikkönen', 'Hülkenberg',
        'Albon', 'Tsunoda', 'Guanyu', 'Latifi', 'Schumacher', 'Stroll', 'Giovinazzi', 'Grosjean',
        'Ericsson', 'Kubica', 'Button', 'Massa', 'Barrichello', 'Fisichella', 'Kovalainen', 'Trulli',
        'Webber', 'Coulthard', 'Sutil', 'Maldonado', 'Senna', 'Kobayashi', 'Petrov', 'Alguersuari'
    ]
    
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def generate_mechanic_name():
    """Genera nombres aleatorios para mecánicos"""
    first_names = [
        'John', 'Mike', 'David', 'Chris', 'Paul', 'Mark', 'James', 'Robert',
        'Steve', 'Kevin', 'Brian', 'Jason', 'Eric', 'Scott', 'Jeff', 'Tim',
        'Richard', 'Daniel', 'Patrick', 'Anthony', 'Steven', 'Thomas', 'Ryan',
        'Matthew', 'Andrew', 'Joshua', 'Justin', 'Jonathan', 'Nicholas', 'Benjamin'
    ]
    
    last_names = [
        'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
        'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
        'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
        'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson'
    ]
    
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def generate_engineer_name():
    """Genera nombres aleatorios para ingenieros"""
    first_names = [
        'Alexander', 'Benjamin', 'Christopher', 'Dominic', 'Edward', 'Frederick', 'Gregory',
        'Harrison', 'Isaac', 'Jonathan', 'Kenneth', 'Lawrence', 'Maxwell', 'Nathaniel',
        'Oliver', 'Patrick', 'Quentin', 'Reginald', 'Sebastian', 'Theodore', 'Victor',
        'William', 'Xavier', 'Zachary', 'Adrian', 'Benedict', 'Cedric', 'Desmond'
    ]
    
    last_names = [
        'Anderson', 'Bennett', 'Carter', 'Davidson', 'Edwards', 'Fitzgerald', 'Grayson',
        'Harrington', 'Ingram', 'Jefferson', 'Kensington', 'Livingston', 'Montgomery',
        'Norton', 'Oswald', 'Pembroke', 'Quinn', 'Rutherford', 'Sutherland', 'Thornton',
        'Underwood', 'Vance', 'Whitaker', 'Xavier', 'Yates', 'Zimmerman', 'Arlington',
        'Blackwood'
    ]
    
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def calculate_driver_salary(age, skill, experience, aggression, consistency, growth_potential):
    """Calcula el salario del piloto basado en sus atributos"""
    # Base salary por ser piloto de F1
    base_salary = 500000
    
    # Factores de ajuste
    age_factor = 1.0
    if age <= 25:
        age_factor = 0.7  # Jóvenes ganan menos
    elif age <= 30:
        age_factor = 1.0  # Edad óptima
    elif age <= 35:
        age_factor = 1.2  # Experimentados
    else:
        age_factor = 1.5  # Veteranos muy valorados
    
    # Habilidad y experiencia son los factores más importantes
    skill_factor = skill / 50.0  # 50 es el promedio
    experience_factor = experience / 50.0
    
    # Factores secundarios
    consistency_factor = consistency / 50.0
    growth_factor = growth_potential / 50.0
    
    # La agresión puede ser positiva o negativa dependiendo del nivel
    aggression_factor = 1.0
    if aggression < 50:
        aggression_factor = 0.9  # Muy conservador
    elif aggression > 80:
        aggression_factor = 1.1  # Muy agresivo (arriesgado pero puede dar resultados)
    
    # Cálculo final del salario
    salary = base_salary * age_factor * skill_factor * experience_factor * consistency_factor * growth_factor * aggression_factor
    
    # Ajustar rango razonable para pilotos de F1
    salary = max(200000, min(15000000, salary))
    
    return int(salary)

def calculate_mechanic_salary(age, pit_stop_skill, reliability_skill, growth_potential):
    """Calcula el salario del mecánico basado en sus atributos"""
    base_salary = 80000
    
    # Factores de ajuste
    age_factor = 1.0
    if age <= 30:
        age_factor = 0.8  # Jóvenes ganan menos
    elif age <= 45:
        age_factor = 1.0  # Edad óptima
    elif age <= 55:
        age_factor = 1.3  # Experimentados muy valorados
    else:
        age_factor = 1.5  # Veteranos con mucha experiencia
    
    # Habilidades principales
    pit_skill_factor = pit_stop_skill / 50.0
    reliability_factor = reliability_skill / 50.0
    growth_factor = growth_potential / 50.0
    
    # Cálculo final
    salary = base_salary * age_factor * pit_skill_factor * reliability_factor * growth_factor
    
    # Ajustar rango razonable para mecánicos de F1
    salary = max(50000, min(400000, salary))
    
    return int(salary)

def calculate_engineer_salary(age, innovation, development_speed, growth_potential):
    """Calcula el salario del ingeniero basado en sus atributos"""
    base_salary = 120000
    
    # Factores de ajuste
    age_factor = 1.0
    if age <= 35:
        age_factor = 0.8  # Jóvenes ganan menos
    elif age <= 50:
        age_factor = 1.0  # Edad óptima
    elif age <= 65:
        age_factor = 1.4  # Experimentados muy valorados
    else:
        age_factor = 1.6  # Veteranos con mucha experiencia
    
    # Habilidades principales
    innovation_factor = innovation / 50.0
    development_factor = development_speed / 50.0
    growth_factor = growth_potential / 50.0
    
    # Cálculo final
    salary = base_salary * age_factor * innovation_factor * development_factor * growth_factor
    
    # Ajustar rango razonable para ingenieros de F1
    salary = max(80000, min(600000, salary))
    
    return int(salary)

def init_car_components_base():
    """Inicializa componentes base del coche (para referencia de mejoras)"""
    # Estos son los tipos de componentes que se crearán cuando un usuario se registre
    component_types = ['engine', 'aerodynamics', 'brakes', 'suspension']
    print(f"   - Tipos de componentes definidos: {component_types}")
    return component_types

def init_upgrade_system():
    """Inicializa datos del sistema de mejoras"""
    # No creamos mejoras iniciales, ya que los usuarios las crearán
    # Pero verificamos que el modelo Upgrade esté disponible
    print("   - Sistema de mejoras configurado y listo")

def init_training_system():
    """Inicializa datos del sistema de entrenamientos"""
    # No creamos entrenamientos iniciales, ya que los usuarios los crearán
    # Pero verificamos que el modelo Training esté disponible
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
    """Crea cambios meteorológicos durante las carreras"""
    races = Race.query.all()
    
    for race in races:
        # Para cada carrera, crear 1-3 cambios meteorológicos posibles
        num_changes = random.randint(1, 3)
        for _ in range(num_changes):
            change_lap = random.randint(5, race.circuit.laps - 5)  # Cambio entre vuelta 5 y final-5
            
            # Posibles transiciones meteorológicas
            transitions = [
                ('dry', 'light_rain'),
                ('light_rain', 'dry'),
                ('light_rain', 'heavy_rain'),
                ('heavy_rain', 'light_rain'),
                ('dry', 'heavy_rain'),
                ('heavy_rain', 'dry')
            ]
            
            from_condition, to_condition = random.choice(transitions)
            
            weather_change = WeatherChange(
                race_id=race.id,
                session_type='race',
                change_lap=change_lap,
                from_condition=from_condition,
                to_condition=to_condition,
                probability=random.uniform(0.3, 0.8)  # 30-80% de probabilidad
            )
            db.session.add(weather_change)
    
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
        
        # Crear pilotos aleatorios (todos disponibles en el mercado)
        print("Creando pilotos disponibles en el mercado...")
        drivers = []
        for i in range(20):  # Crear 20 pilotos aleatorios
            age = random.randint(18, 39)
            skill = random.randint(40, 95)
            experience = random.randint(30, 90)
            aggression = random.randint(40, 85)
            consistency = random.randint(45, 95)
            growth_potential = random.randint(50, 90)
            
            salary = calculate_driver_salary(age, skill, experience, aggression, consistency, growth_potential)
            
            driver = Driver(
                name=generate_random_name(),
                age=age,
                salary=salary,
                skill=skill,
                experience=experience,
                aggression=aggression,
                consistency=consistency,
                growth_potential=growth_potential,
                market_available=True,
                team_id=None  # Todos disponibles en el mercado
            )
            drivers.append(driver)
            db.session.add(driver)
        
        # Crear mecánicos aleatorios (todos disponibles en el mercado)
        print("Creando mecánicos disponibles en el mercado...")
        for i in range(30):  # Crear 30 mecánicos aleatorios
            # Variar las edades para tener algunos cerca de la jubilación
            if i < 8:  # Algunos mecánicos mayores
                age = random.randint(55, 65)
            else:  # Mecánicos más jóvenes
                age = random.randint(25, 54)
            
            pit_stop_skill = random.randint(50, 95)
            reliability_skill = random.randint(50, 90)
            growth_potential = random.randint(50, 85)
            
            salary = calculate_mechanic_salary(age, pit_stop_skill, reliability_skill, growth_potential)
            
            mechanic = Mechanic(
                name=generate_mechanic_name(),
                age=age,
                salary=salary,
                pit_stop_skill=pit_stop_skill,
                reliability_skill=reliability_skill,
                growth_potential=growth_potential,
                market_available=True,
                team_id=None  # Todos disponibles en el mercado
            )
            db.session.add(mechanic)
        
        # Crear ingenieros aleatorios (todos disponibles en el mercado)
        print("Creando ingenieros disponibles en el mercado...")
        for i in range(30):  # Crear 30 ingenieros aleatorios
            # Variar las edades para tener algunos cerca de la jubilación
            if i < 8:  # Algunos ingenieros mayores
                age = random.randint(65, 75)
            else:  # Ingenieros más jóvenes
                age = random.randint(28, 64)
            
            innovation = random.randint(50, 95)
            development_speed = random.randint(50, 90)
            growth_potential = random.randint(50, 85)
            
            salary = calculate_engineer_salary(age, innovation, development_speed, growth_potential)
            
            engineer = Engineer(
                name=generate_engineer_name(),
                age=age,
                salary=salary,
                innovation=innovation,
                development_speed=development_speed,
                growth_potential=growth_potential,
                market_available=True,
                team_id=None  # Todos disponibles en el mercado
            )
            db.session.add(engineer)
        
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
                qualifying_session=race_date + timedelta(days=3, hours=6),  # Sábado 14:00
                race_session=race_date + timedelta(days=4, hours=5)  # Domingo 13:00
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
        print(f"   - {len(drivers)} pilotos creados (todos disponibles en el mercado)")
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