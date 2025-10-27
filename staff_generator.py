# staff_generator.py
import random
from datetime import date, datetime
from app import db, Driver, Mechanic, Engineer
from app import calculate_driver_salary, calculate_mechanic_salary, calculate_engineer_salary

def generate_random_name():
    """Genera nombres aleatorios para pilotos, mecánicos e ingenieros"""
    first_names_male = [
        'Carlos', 'Fernando', 'Lewis', 'Max', 'Charles', 'Lando', 'George', 'Sergio',
        'Esteban', 'Pierre', 'Valtteri', 'Kevin', 'Daniel', 'Sebastian', 'Kimi', 'Nico',
        'Alex', 'Yuki', 'Zhou', 'Nicholas', 'Mick', 'Lance', 'Antonio', 'Romain',
        'Marcus', 'Robert', 'Jenson', 'Felipe', 'Rubens', 'Giancarlo', 'Heikki', 'Jarno',
        'Mark', 'David', 'Adrian', 'Pastor', 'Bruno', 'Kamui', 'Vitaly', 'Jaime',
        'Oliver', 'Theo', 'Lucas', 'Hugo', 'Adam', 'Samuel', 'Thomas', 'Victor'
    ]
    
    first_names_female = [
        'Sophie', 'Emma', 'Olivia', 'Ava', 'Isabella', 'Mia', 'Charlotte', 'Amelia',
        'Harper', 'Evelyn', 'Abigail', 'Emily', 'Elizabeth', 'Sofia', 'Ella', 'Scarlett',
        'Grace', 'Chloe', 'Victoria', 'Riley', 'Aria', 'Lily', 'Aurora', 'Zoe',
        'Hannah', 'Lillian', 'Addison', 'Eleanor', 'Natalie', 'Leah', 'Sarah', 'Anna'
    ]
    
    last_names = [
        'Sainz', 'Alonso', 'Hamilton', 'Verstappen', 'Leclerc', 'Norris', 'Russell', 'Pérez',
        'Ocon', 'Gasly', 'Bottas', 'Magnussen', 'Ricciardo', 'Vettel', 'Räikkönen', 'Hülkenberg',
        'Albon', 'Tsunoda', 'Guanyu', 'Latifi', 'Schumacher', 'Stroll', 'Giovinazzi', 'Grosjean',
        'Ericsson', 'Kubica', 'Button', 'Massa', 'Barrichello', 'Fisichella', 'Kovalainen', 'Trulli',
        'Webber', 'Coulthard', 'Sutil', 'Maldonado', 'Senna', 'Kobayashi', 'Petrov', 'Alguersuari',
        'Powell', 'Chen', 'Rossi', 'Weber', 'Kim', 'Silva', 'Müller', 'Papadopoulos', 'Andersen',
        'Kowalski', 'Nakamura', 'Santos', 'Ibrahim', 'Khan', 'Costa', 'Dubois', 'Lopez', 'Nowak'
    ]
    
    # 70% nombres masculinos, 30% femeninos para diversidad
    if random.random() < 0.7:
        first_name = random.choice(first_names_male)
    else:
        first_name = random.choice(first_names_female)
    
    return f"{first_name} {random.choice(last_names)}"

def generate_driver():
    """Genera un nuevo piloto con atributos aleatorios"""
    today = date.today()
    min_birth_year = today.year - 35
    max_birth_year = today.year - 18
    birth_year = random.randint(min_birth_year, max_birth_year)
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    
    date_of_birth = date(birth_year, birth_month, birth_day)
    age = today.year - birth_year
    
    skill = random.randint(40, 95)
    experience = random.randint(30, 90)
    aggression = random.randint(40, 85)
    consistency = random.randint(45, 95)
    growth_potential = random.randint(50, 90)
    
    salary = calculate_driver_salary(age, skill, experience, aggression, consistency, growth_potential)
    
    driver = Driver(
        name=generate_random_name(),
        date_of_birth=date_of_birth,
        age=age,
        salary=salary,
        skill=skill,
        experience=experience,
        aggression=aggression,
        consistency=consistency,
        growth_potential=growth_potential,
        market_available=True,
        team_id=None
    )
    
    return driver

def generate_mechanic():
    """Genera un nuevo mecánico con atributos aleatorios"""
    today = date.today()
    min_birth_year = today.year - 65
    max_birth_year = today.year - 25
    birth_year = random.randint(min_birth_year, max_birth_year)
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    
    date_of_birth = date(birth_year, birth_month, birth_day)
    age = today.year - birth_year
    
    pit_stop_skill = random.randint(50, 95)
    reliability_skill = random.randint(50, 90)
    growth_potential = random.randint(50, 85)
    
    salary = calculate_mechanic_salary(age, pit_stop_skill, reliability_skill, growth_potential)
    
    mechanic = Mechanic(
        name=generate_random_name(),
        date_of_birth=date_of_birth,
        age=age,
        salary=salary,
        pit_stop_skill=pit_stop_skill,
        reliability_skill=reliability_skill,
        growth_potential=growth_potential,
        market_available=True,
        team_id=None
    )
    
    return mechanic

def generate_engineer():
    """Genera un nuevo ingeniero con atributos aleatorios"""
    today = date.today()
    min_birth_year = today.year - 70
    max_birth_year = today.year - 28
    birth_year = random.randint(min_birth_year, max_birth_year)
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)
    
    date_of_birth = date(birth_year, birth_month, birth_day)
    age = today.year - birth_year
    
    innovation = random.randint(50, 95)
    development_speed = random.randint(50, 90)
    growth_potential = random.randint(50, 85)
    
    salary = calculate_engineer_salary(age, innovation, development_speed, growth_potential)
    
    engineer = Engineer(
        name=generate_random_name(),
        date_of_birth=date_of_birth,
        age=age,
        salary=salary,
        innovation=innovation,
        development_speed=development_speed,
        growth_potential=growth_potential,
        market_available=True,
        team_id=None
    )
    
    return engineer

def generate_staff_batch(drivers_count=4, mechanics_count=8, engineers_count=8):
    """
    Genera un lote de nuevo personal
    
    Args:
        drivers_count: Número de pilotos a generar
        mechanics_count: Número de mecánicos a generar  
        engineers_count: Número de ingenieros a generar
    """
    staff_created = {
        'drivers': [],
        'mechanics': [],
        'engineers': []
    }
    
    # Generar pilotos
    for _ in range(drivers_count):
        driver = generate_driver()
        db.session.add(driver)
        staff_created['drivers'].append(driver)
    
    # Generar mecánicos
    for _ in range(mechanics_count):
        mechanic = generate_mechanic()
        db.session.add(mechanic)
        staff_created['mechanics'].append(mechanic)
    
    # Generar ingenieros
    for _ in range(engineers_count):
        engineer = generate_engineer()
        db.session.add(engineer)
        staff_created['engineers'].append(engineer)
    
    # Guardar en la base de datos
    try:
        db.session.commit()
        print(f"Personal generado: {drivers_count} pilotos, {mechanics_count} mecánicos, {engineers_count} ingenieros")
        return staff_created
    except Exception as e:
        db.session.rollback()
        print(f"Error al generar personal: {e}")
        return None

def generate_initial_staff():
    """Genera el personal inicial para la base de datos"""
    print("Generando personal inicial...")
    
    # Generar 20 pilotos iniciales
    for _ in range(20):
        driver = generate_driver()
        db.session.add(driver)
    
    # Generar 30 mecánicos iniciales
    for _ in range(30):
        mechanic = generate_mechanic()
        db.session.add(mechanic)
    
    # Generar 30 ingenieros iniciales
    for _ in range(30):
        engineer = generate_engineer()
        db.session.add(engineer)
    
    try:
        db.session.commit()
        print("Personal inicial generado correctamente")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error al generar personal inicial: {e}")
        return False
        
# Añadir al final de staff_generator.py

def handle_retirements():
    """Maneja las jubilaciones automáticas del personal"""
    # Jubilar pilotos mayores de 40 años
    retired_drivers = Driver.query.filter(Driver.team_id.isnot(None)).all()
    retired_drivers = [driver for driver in retired_drivers if driver.is_retired]
    
    for driver in retired_drivers:
        driver.team_id = None
        driver.market_available = False  # No disponible en el mercado
    
    # Jubilar mecánicos mayores de 65 años
    retired_mechanics = Mechanic.query.filter(Mechanic.team_id.isnot(None)).all()
    retired_mechanics = [mechanic for mechanic in retired_mechanics if mechanic.is_retired]
    
    for mechanic in retired_mechanics:
        mechanic.team_id = None
        mechanic.market_available = False
    
    # Jubilar ingenieros mayores de 70 años
    retired_engineers = Engineer.query.filter(Engineer.team_id.isnot(None)).all()
    retired_engineers = [engineer for engineer in retired_engineers if engineer.is_retired]
    
    for engineer in retired_engineers:
        engineer.team_id = None
        engineer.market_available = False
    
    db.session.commit()
    
    # Generar reemplazos por los jubilados
    if retired_drivers:
        replacements_needed = len(retired_drivers) + len(retired_mechanics) + len(retired_engineers)
        if replacements_needed > 0:
            generate_staff_batch(
                drivers_count=len(retired_drivers),
                mechanics_count=len(retired_mechanics),
                engineers_count=len(retired_engineers)
            )
    
    return len(retired_drivers) + len(retired_mechanics) + len(retired_engineers)