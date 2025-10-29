from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date, timezone
from race_engine_bridge import RaceEngineBridge
import json
import random
import math
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from config import Config

app = Flask(__name__, 
    static_folder='static',
    template_folder='templates'
)
app.config.from_object(Config)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# CONTEXT PROCESSOR PARA INYECTAR 'now' EN TODAS LAS PLANTILLAS
@app.context_processor
def utility_processor():
    def get_tyre_badge_color(tyre_type):
        colors = {
            'soft': 'danger', 'medium': 'warning', 'hard': 'secondary',
            'wet': 'info', 'extreme_wet': 'primary'
        }
        return colors.get(tyre_type, 'primary')
    
    def get_tyre_display_name(tyre_type):
        names = {
            'soft': 'Blando', 'medium': 'Medio', 'hard': 'Duro',
            'wet': 'Lluvia', 'extreme_wet': 'Lluvia Extrema'
        }
        return names.get(tyre_type, tyre_type)
    
    return {
        'now': datetime.utcnow(),
        'get_tyre_badge_color': get_tyre_badge_color,
        'get_tyre_display_name': get_tyre_display_name
    }

# Modelos de la base de datos
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    team_name = db.Column(db.String(100), nullable=False)
    money = db.Column(db.Float, default=Config.STARTING_MONEY)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    drivers = db.relationship('Driver', backref='team', lazy=True)
    mechanics = db.relationship('Mechanic', backref='team', lazy=True)
    engineers = db.relationship('Engineer', backref='team', lazy=True)
    car_components = db.relationship('CarComponent', backref='team', lazy=True)
    test_sessions = db.relationship('TestSession', backref='team', lazy=True)
    race_strategies = db.relationship('RaceStrategy', backref='team', lazy=True)

class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    salary = db.Column(db.Float, nullable=False)
    skill = db.Column(db.Integer, default=50)
    experience = db.Column(db.Integer, default=50)
    aggression = db.Column(db.Integer, default=50)
    consistency = db.Column(db.Integer, default=50)
    growth_potential = db.Column(db.Integer, default=50)
    team_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    market_available = db.Column(db.Boolean, default=True)
    last_trained = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def is_retired(self):
        """Verifica si el piloto debe jubilarse (más de 40 años)"""
        today = date.today()
        age = today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
        return age >= 40

class Mechanic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    salary = db.Column(db.Float, nullable=False)
    pit_stop_skill = db.Column(db.Integer, default=50)
    reliability_skill = db.Column(db.Integer, default=50)
    growth_potential = db.Column(db.Integer, default=50)
    team_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    market_available = db.Column(db.Boolean, default=True)
    last_trained = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def is_retired(self):
        """Verifica si el mecánico debe jubilarse (más de 65 años)"""
        today = date.today()
        age = today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
        return age >= 65

class Engineer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    salary = db.Column(db.Float, nullable=False)
    innovation = db.Column(db.Integer, default=50)
    development_speed = db.Column(db.Integer, default=50)
    growth_potential = db.Column(db.Integer, default=50)
    team_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    market_available = db.Column(db.Boolean, default=True)
    last_trained = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @property
    def is_retired(self):
        """Verifica si el ingeniero debe jubilarse (más de 70 años)"""
        today = date.today()
        age = today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
        return age >= 70

class CarComponent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    component_type = db.Column(db.String(20), nullable=False)
    strength = db.Column(db.Integer, default=50)
    reliability = db.Column(db.Integer, default=50)
    upgrade_progress = db.Column(db.Integer, default=0)
    upgrade_ends_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Upgrade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    component_type = db.Column(db.String(20), nullable=False)
    level = db.Column(db.Integer, nullable=False)  # 1, 2, 3
    weeks = db.Column(db.Integer, nullable=False)  # 1, 2, 3
    total_cost = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    
    @property
    def progress(self):
        if self.completed:
            return 100
            
        total_seconds = (self.end_date - self.start_date).total_seconds()
        elapsed_seconds = (datetime.utcnow() - self.start_date).total_seconds()
        
        if total_seconds <= 0:
            return 100
            
        progress = min(100, (elapsed_seconds / total_seconds) * 100)
        return progress
    
    @property
    def remaining_days(self):
        if self.completed:
            return 0
            
        remaining_seconds = (self.end_date - datetime.utcnow()).total_seconds()
        remaining_days = max(0, remaining_seconds / (24 * 3600))
        return int(remaining_days) + 1  # +1 para redondear hacia arriba
        
class Training(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    staff_type = db.Column(db.String(20), nullable=False)  # driver, mechanic, engineer
    staff_id = db.Column(db.Integer, nullable=False)  # ID del piloto/mecánico/ingeniero
    attribute = db.Column(db.String(30), nullable=False)  # atributo a mejorar
    level = db.Column(db.Integer, nullable=False)  # 1, 2, 3
    weeks = db.Column(db.Integer, nullable=False)  # 1, 2, 3
    total_cost = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    
    @property
    def progress(self):
        if self.completed:
            return 100
            
        total_seconds = (self.end_date - self.start_date).total_seconds()
        elapsed_seconds = (datetime.utcnow() - self.start_date).total_seconds()
        
        if total_seconds <= 0:
            return 100
            
        progress = min(100, (elapsed_seconds / total_seconds) * 100)
        return progress
    
    @property
    def remaining_days(self):
        if self.completed:
            return 0
            
        remaining_seconds = (self.end_date - datetime.utcnow()).total_seconds()
        remaining_days = max(0, remaining_seconds / (24 * 3600))
        return int(remaining_days) + 1  # +1 para redondear hacia arriba

class Circuit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    timezone = db.Column(db.String(50), nullable=False)
    laps = db.Column(db.Integer, nullable=False)

class Race(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    circuit_id = db.Column(db.Integer, db.ForeignKey('circuit.id'), nullable=False)
    round_number = db.Column(db.Integer, nullable=False)
    season_year = db.Column(db.Integer, nullable=False)
    test_session = db.Column(db.DateTime, nullable=False)
    qualifying_session = db.Column(db.DateTime, nullable=False)
    sprint_session = db.Column(db.DateTime)
    race_session = db.Column(db.DateTime, nullable=False)
    
    circuit = db.relationship('Circuit', backref='races')
    live_events = db.relationship('LiveEvent', backref='race', lazy=True)  # AÑADE ESTA LÍNEA
    
class QualifyingSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    tyre_choice = db.Column(db.String(20), nullable=False)  # soft, medium, hard, wet, extreme_wet
    q1_time = db.Column(db.Float)  # Tiempo en Q1
    q2_time = db.Column(db.Float)  # Tiempo en Q2  
    q3_time = db.Column(db.Float)  # Tiempo en Q3
    final_position = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    race = db.relationship('Race', backref='qualifying_sessions')
    team = db.relationship('User', backref='qualifying_sessions')
    driver = db.relationship('Driver', backref='qualifying_sessions')

class RaceResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    position = db.Column(db.Integer)
    points = db.Column(db.Integer, default=0)
    tyre_usage = db.Column(db.Integer, default=0)
    pit_stops = db.Column(db.Integer, default=0)
    fastest_lap = db.Column(db.Boolean, default=False)
    dnf = db.Column(db.Boolean, default=False)
    dnf_reason = db.Column(db.String(50))

class LiveEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'), nullable=False)
    team_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    lap = db.Column(db.Integer, nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    session_type = db.Column(db.String(20), nullable=False, default='race')  # 'qualifying' o 'race'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Nuevos modelos para el sistema de tests
class TyreType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)  # soft, medium, hard, wet, extreme_wet
    dry_performance = db.Column(db.Integer, nullable=False)
    wet_performance = db.Column(db.Integer, nullable=False)
    durability = db.Column(db.Integer, nullable=False)
    warmup_time = db.Column(db.Integer, nullable=False)  # en segundos

class TestSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    driver = db.relationship('Driver')
    race = db.relationship('Race')

class TestLap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_session_id = db.Column(db.Integer, db.ForeignKey('test_session.id'), nullable=False)
    lap_number = db.Column(db.Integer, nullable=False)
    tyre_type = db.Column(db.String(20), nullable=False)
    lap_time = db.Column(db.Float, nullable=False)  # tiempo en segundos
    tyre_wear = db.Column(db.Integer, nullable=False)  # desgaste de 0-100
    track_condition = db.Column(db.String(20), nullable=False)  # dry, wet, heavy_rain
    
    test_session = db.relationship('TestSession', backref='laps')

class RaceStrategy(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    strategy_name = db.Column(db.String(100), nullable=False)
    total_pit_stops = db.Column(db.Integer, nullable=False)
    starting_tyre = db.Column(db.String(20), default='soft')
    rain_strategy = db.Column(db.String(20), default='continue')  # continue, pit_wet, pit_extreme, next_pit
    heavy_rain_strategy = db.Column(db.String(20), default='continue')  # continue, pit_extreme, immediate_pit
    dry_strategy = db.Column(db.String(20), default='continue')  # continue, pit_soft, pit_medium, next_pit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    driver = db.relationship('Driver')
    race = db.relationship('Race')

class StrategySegment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    strategy_id = db.Column(db.Integer, db.ForeignKey('race_strategy.id'), nullable=False)
    segment_order = db.Column(db.Integer, nullable=False)
    tyre_type = db.Column(db.String(20), nullable=False)
    laps_planned = db.Column(db.Integer, nullable=False)
    
    strategy = db.relationship('RaceStrategy', backref='segments')
    
# Añadir después de los modelos existentes en app.py

class WeatherForecast(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'), nullable=False)
    session_type = db.Column(db.String(20), nullable=False)  # test, qualifying, race
    forecast_time = db.Column(db.DateTime, nullable=False)
    condition = db.Column(db.String(20), nullable=False)  # dry, light_rain, heavy_rain
    probability = db.Column(db.Float, nullable=False)  # 0-1
    
    race = db.relationship('Race', backref='weather_forecasts')
    
# Añadir después del modelo WeatherForecast en app.py

class WeatherChange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'), nullable=False)
    session_type = db.Column(db.String(20), nullable=False)  # test, qualifying, race
    change_lap = db.Column(db.Integer, nullable=False)  # vuelta en la que cambia el tiempo
    from_condition = db.Column(db.String(20), nullable=False)  # condición anterior
    to_condition = db.Column(db.String(20), nullable=False)  # nueva condición
    probability = db.Column(db.Float, nullable=False)  # 0-1
    
    race = db.relationship('Race', backref='weather_changes')

class ChampionshipStandings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'), nullable=False)
    points = db.Column(db.Integer, default=0)
    position = db.Column(db.Integer)
    fastest_lap = db.Column(db.Boolean, default=False)
    dnf = db.Column(db.Boolean, default=False)
    
    team = db.relationship('User', backref='championship_results')
    driver = db.relationship('Driver', backref='championship_results')
    race = db.relationship('Race', backref='championship_results')
    
class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=False)
    race_id = db.Column(db.Integer, db.ForeignKey('race.id'), nullable=False)
    initial_tyre = db.Column(db.String(20), nullable=False)
    track_condition = db.Column(db.String(20), nullable=False)
    total_laps = db.Column(db.Integer, nullable=False)
    best_lap = db.Column(db.Float, nullable=False)
    avg_lap = db.Column(db.Float, nullable=False)
    incidents = db.Column(db.Integer, default=0)
    pit_stops = db.Column(db.Integer, default=0)
    total_time_lost = db.Column(db.Float, default=0.0)
    lap_data = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones - Asegúrate de que estén así
    team = db.relationship('User', backref='tests')
    driver = db.relationship('Driver', backref='tests')
    race = db.relationship('Race', backref='tests')

class TestCleanupSystem:
    @staticmethod
    def cleanup_old_tests():
        """Elimina automáticamente los tests de carreras ya completadas"""
        try:
            now = datetime.utcnow()
            
            # Encontrar carreras que ya han terminado (más de 2 horas después de la sesión de carrera)
            completed_races = Race.query.filter(
                Race.race_session < now - timedelta(hours=2)
            ).all()
            
            deleted_count = 0
            for race in completed_races:
                # Eliminar todos los tests asociados a esta carrera
                race_tests_deleted = Test.query.filter_by(race_id=race.id).delete()
                deleted_count += race_tests_deleted
                
                print(f"✅ Tests eliminados automáticamente para la carrera {race.circuit.name}: {race_tests_deleted} tests")
            
            db.session.commit()
            return deleted_count
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error en cleanup_old_tests: {str(e)}")
            return 0

    @staticmethod
    def get_remaining_tests_count(team_id):
        """Obtiene el número de tests activos que tiene un equipo"""
        # Solo contar tests de carreras que aún no han terminado
        now = datetime.utcnow()
        
        active_tests_count = db.session.query(Test).join(
            Race, Test.race_id == Race.id
        ).filter(
            Test.team_id == team_id,
            Race.race_session >= now - timedelta(hours=2)  # Carreras activas o recientes
        ).count()
        
        return active_tests_count

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Funciones de cálculo de salarios (para usar en el mercado)
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

# Sistema del juego
class RaceSimulator:
    @staticmethod
    def calculate_race_points(position, has_fastest_lap=False):
        """Calcula los puntos según la posición y vuelta rápida"""
        POINTS_SYSTEM = {
            1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1
        }
        FASTEST_LAP_POINT = 1
        
        points = POINTS_SYSTEM.get(position, 0)
        if has_fastest_lap and position <= 10:
            points += FASTEST_LAP_POINT
        return points

    @staticmethod
    def simulate_qualifying(race_id):
        teams = User.query.filter(User.drivers.any()).all()
        results = []
        
        for team in teams:
            for driver in team.drivers:
                base_time = 90 + random.random() * 10
                driver_skill = (driver.skill + driver.experience) / 2
                car_performance = sum(comp.strength for comp in team.car_components) / 4
                
                final_time = base_time - (driver_skill / 100 * 5) - (car_performance / 100 * 3) + (random.random() * 2 - 1)
                
                results.append({
                    'team_id': team.id,
                    'driver_id': driver.id,
                    'driver_name': driver.name,
                    'team_name': team.team_name,
                    'time': final_time
                })
        
        results.sort(key=lambda x: x['time'])
        return results

    @staticmethod
    def simulate_race(race_id):
        race = Race.query.get(race_id)
        teams = User.query.filter(User.drivers.any()).all()
        events = []
        
        # Simular resultados de carrera
        results = []
        for team in teams:
            for driver in team.drivers:
                # Calcular rendimiento basado en habilidades del piloto y coche
                driver_performance = (driver.skill * 0.4 + driver.experience * 0.3 + 
                                    driver.consistency * 0.2 + driver.aggression * 0.1)
                car_performance = sum(comp.strength for comp in team.car_components) / 4
                
                # Factor aleatorio
                luck = random.uniform(0.8, 1.2)
                
                # Calcular puntuación final
                performance_score = (driver_performance + car_performance) * luck
                
                # 5% de probabilidad de DNF (No termina)
                dnf = random.random() < 0.05
                
                results.append({
                    'team_id': team.id,
                    'driver_id': driver.id,
                    'driver_name': driver.name,
                    'team_name': team.team_name,
                    'performance_score': performance_score,
                    'dnf': dnf
                })
        
        # Ordenar por puntuación (mayor a menor)
        results.sort(key=lambda x: x['performance_score'], reverse=True)
        
        # Asignar posiciones y puntos
        fastest_lap_assigned = False
        for i, result in enumerate(results):
            position = i + 1
            
            # Si es DNF, posición final basada en cuando abandonó
            if result['dnf']:
                dnf_position = random.randint(11, len(results))
                position = dnf_position
                # Reordenar para mantener coherencia
                results = sorted(results, 
                               key=lambda x: 0 if x['dnf'] else x['performance_score'], 
                               reverse=True)
                for j, res in enumerate(results):
                    if res['dnf']:
                        res['position'] = j + 1
                    else:
                        res['position'] = j + 1 - len([r for r in results[:j] if r['dnf']])
                break
            
            result['position'] = position
            
            # Asignar vuelta rápida aleatoriamente al top 10
            if position <= 10 and not fastest_lap_assigned and random.random() < 0.3:
                result['fastest_lap'] = True
                fastest_lap_assigned = True
            else:
                result['fastest_lap'] = False
            
            # Calcular puntos
            result['points'] = RaceSimulator.calculate_race_points(
                position, result.get('fastest_lap', False)
            )
        
        # Simular eventos durante la carrera
        for lap in range(1, race.circuit.laps + 1):
            for team in teams:
                if random.random() < 0.05:  # 5% de probabilidad de evento por vuelta
                    event_type = random.choice(['overtake', 'pit_stop', 'spin', 'fast_lap'])
                    event_desc = RaceSimulator.generate_event_description(event_type, team.drivers[0].name)
                    
                    event = LiveEvent(
                        race_id=race_id,
                        team_id=team.id,
                        driver_id=team.drivers[0].id,
                        lap=lap,
                        event_type=event_type,
                        description=event_desc
                    )
                    db.session.add(event)
                    events.append(event)
            
            # Pequeña pausa para simular tiempo real
            # db.session.commit()  # Comentado para evitar múltiples commits
        
        # Guardar resultados en la base de datos
        for result in results:
            standing = ChampionshipStandings(
                team_id=result['team_id'],
                driver_id=result['driver_id'],
                race_id=race_id,
                points=result['points'],
                position=result['position'],
                fastest_lap=result.get('fastest_lap', False),
                dnf=result['dnf']
            )
            db.session.add(standing)
            
            # Crear evento para DNF
            if result['dnf']:
                event = LiveEvent(
                    race_id=race_id,
                    team_id=result['team_id'],
                    driver_id=result['driver_id'],
                    lap=random.randint(1, race.circuit.laps),
                    event_type='dnf',
                    description=f"¡{result['driver_name']} se retira de la carrera!"
                )
                db.session.add(event)
                events.append(event)
        
        db.session.commit()
        return events

    @staticmethod
    def generate_event_description(event_type, driver_name):
        descriptions = {
            'overtake': f'¡{driver_name} realiza un espectacular adelantamiento!',
            'pit_stop': f'{driver_name} entra en boxes para cambiar neumáticos',
            'spin': f'¡{driver_name} da un trompo pero continua!',
            'fast_lap': f'¡{driver_name} marca el giro más rápido de la carrera!',
            'dnf': f'¡{driver_name} se retira de la carrera!'
        }
        return descriptions.get(event_type, f'{driver_name} tiene un incidente')

# Sistema de puntos F1 actual (desde 2022)
POINTS_SYSTEM = {
    1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1
}
FASTEST_LAP_POINT = 1

class FinancialTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # income, expense
    category = db.Column(db.String(50), nullable=False)  # salary, upgrade, training, sponsorship, race_prize, etc.
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    balance_after = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    team = db.relationship('User', backref='financial_transactions')

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    allocated_amount = db.Column(db.Float, nullable=False)
    spent_amount = db.Column(db.Float, default=0.0)
    month = db.Column(db.Integer, nullable=False)  # 1-12
    year = db.Column(db.Integer, nullable=False)
    
    team = db.relationship('User', backref='budgets')

class FinanceSystem:
    @staticmethod
    def get_financial_summary(team_id, months=6):
        """Obtiene un resumen financiero de los últimos meses"""
        cutoff_date = datetime.utcnow() - timedelta(days=30*months)
        
        # Consultas separadas para ingresos y gastos
        income_data = db.session.query(
            db.func.strftime('%Y-%m', FinancialTransaction.created_at).label('month'),
            db.func.sum(FinancialTransaction.amount).label('amount')
        ).filter(
            FinancialTransaction.team_id == team_id,
            FinancialTransaction.transaction_type == 'income',
            FinancialTransaction.created_at >= cutoff_date
        ).group_by('month').all()
        
        expense_data = db.session.query(
            db.func.strftime('%Y-%m', FinancialTransaction.created_at).label('month'),
            db.func.sum(FinancialTransaction.amount).label('amount')
        ).filter(
            FinancialTransaction.team_id == team_id,
            FinancialTransaction.transaction_type == 'expense',
            FinancialTransaction.created_at >= cutoff_date
        ).group_by('month').all()
        
        # Convertir a diccionarios para fácil acceso
        income_dict = {item.month: item.amount or 0 for item in income_data}
        expense_dict = {item.month: item.amount or 0 for item in expense_data}
        
        # Combinar todos los meses únicos
        all_months = sorted(set(list(income_dict.keys()) + list(expense_dict.keys())))
        
        monthly_data = []
        for month in all_months:
            monthly_data.append({
                'month': month,
                'income': income_dict.get(month, 0),
                'expenses': expense_dict.get(month, 0)
            })
        
        # Totales por categoría
        category_totals = db.session.query(
            FinancialTransaction.category,
            FinancialTransaction.transaction_type,
            db.func.sum(FinancialTransaction.amount).label('total')
        ).filter(
            FinancialTransaction.team_id == team_id,
            FinancialTransaction.created_at >= cutoff_date
        ).group_by(FinancialTransaction.category, FinancialTransaction.transaction_type).all()
        
        return {
            'monthly_data': monthly_data,
            'category_totals': category_totals
        }

    @staticmethod
    def record_transaction(team_id, transaction_type, category, amount, description):
        """Registra una transacción financiera"""
        user = User.query.get(team_id)
        if not user:
            return False
            
        # Actualizar el saldo del usuario según el tipo de transacción
        if transaction_type == 'income':
            user.money += amount
        elif transaction_type == 'expense':
            user.money -= amount
        
        transaction = FinancialTransaction(
            team_id=team_id,
            transaction_type=transaction_type,
            category=category,
            amount=amount,
            description=description,
            balance_after=user.money
        )
        
        db.session.add(transaction)
        db.session.commit()
        return True

# Rutas de la aplicación
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        team_name = request.form['team_name']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first():
            return render_template('register.html', error='Usuario ya existe')
        
        user = User(
            username=username,
            email=email,
            team_name=team_name,
            password_hash=generate_password_hash(password),
            money=Config.STARTING_MONEY
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Crear componentes iniciales del coche
        components = ['engine', 'aerodynamics', 'brakes', 'suspension']
        for comp_type in components:
            component = CarComponent(
                team_id=user.id,
                component_type=comp_type,
                strength=50,
                reliability=50
            )
            db.session.add(component)
        
        # GENERAR NUEVO PERSONAL usando el módulo externo
        from staff_generator import generate_staff_batch
        generate_staff_batch(drivers_count=4, mechanics_count=8, engineers_count=8)
        
        db.session.commit()
        
        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        
        return render_template('login.html', error='Credenciales inválidas')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    team_info = {
        'money': current_user.money,
        'drivers': current_user.drivers,
        'mechanics': current_user.mechanics,
        'engineers': current_user.engineers,
        'car_components': current_user.car_components
    }
    
    # Obtener mejora activa
    active_upgrade = Upgrade.query.filter_by(
        team_id=current_user.id, 
        completed=False
    ).first()
    
    # Obtener entrenamiento activo
    active_training = Training.query.filter_by(
        team_id=current_user.id, 
        completed=False
    ).first()
    
    # Obtener posición en el campeonato del equipo
    team_standings_result = db.session.query(
        User.team_name,
        db.func.sum(ChampionshipStandings.points).label('total_points'),
        db.func.count(ChampionshipStandings.id).label('races_entered')
    ).join(ChampionshipStandings, User.id == ChampionshipStandings.team_id
    ).group_by(User.id, User.team_name
    ).order_by(db.desc('total_points')).all()
    
    # Encontrar la posición del equipo actual
    team_standings = None
    leader_standings = None
    
    for i, standing in enumerate(team_standings_result):
        if standing.team_name == current_user.team_name:
            team_standings = {
                'position': i + 1,
                'total_points': standing.total_points or 0,
                'races_entered': standing.races_entered or 0
            }
        
        # Guardar también el líder para calcular diferencia
        if i == 0:
            leader_standings = {
                'total_points': standing.total_points or 0
            }
    
    # Encontrar el próximo evento
    now = datetime.utcnow()
    next_event = None
    
    # Buscar en todas las carreras
    races = Race.query.all()
    for race in races:
        sessions = [
            ('test', race.test_session),
            ('qualifying', race.qualifying_session), 
            ('race', race.race_session)
        ]
        
        for session_type, session_time in sessions:
            if session_time > now:
                if not next_event or session_time < next_event['session_datetime']:
                    next_event = {
                        'race_id': race.id,
                        'circuit': race.circuit,
                        'session_type': session_type,
                        'session_datetime': session_time
                    }
    
    return render_template('dashboard.html', 
                         team=team_info, 
                         next_event=next_event,
                         active_upgrade=active_upgrade,
                         active_training=active_training,
                         team_standings=team_standings,
                         leader_standings=leader_standings)

@app.route('/team')
@login_required
def team_management():
    from datetime import datetime
    current_date = datetime.utcnow()
    return render_template('team.html', team=current_user, current_date=current_date)

@app.route('/market')
@login_required
def market():
    available_drivers = Driver.query.filter_by(market_available=True).all()
    available_mechanics = Mechanic.query.filter_by(market_available=True).all()
    available_engineers = Engineer.query.filter_by(market_available=True).all()
    
    return render_template('market.html', 
                         drivers=available_drivers,
                         mechanics=available_mechanics,
                         engineers=available_engineers)

@app.route('/buy/driver/<int:driver_id>')
@login_required
def buy_driver(driver_id):
    if len(current_user.drivers) >= Config.MAX_DRIVERS:
        return jsonify({'success': False, 'message': 'Límite de pilotos alcanzado'})
    
    driver = Driver.query.get(driver_id)
    purchase_cost = driver.salary  # 1 salario como adelanto
    
    if driver and driver.market_available and current_user.money >= purchase_cost:
        # ELIMINAR esta línea: current_user.money -= purchase_cost
        driver.team_id = current_user.id
        driver.market_available = False
        
        # Registrar transacción (esto ya actualiza el dinero automáticamente)
        FinanceSystem.record_transaction(
            current_user.id,
            'expense',
            'salary_advance',
            purchase_cost,
            f'Adelanto de salario - {driver.name}'
        )
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Piloto comprado'})
    
    return jsonify({'success': False, 'message': 'Error en la compra'})

@app.route('/buy/mechanic/<int:mechanic_id>')
@login_required
def buy_mechanic(mechanic_id):
    if len(current_user.mechanics) >= Config.MAX_MECHANICS:
        return jsonify({'success': False, 'message': 'Límite de mecánicos alcanzado'})
    
    mechanic = Mechanic.query.get(mechanic_id)
    if mechanic and mechanic.market_available and current_user.money >= mechanic.salary:
        mechanic.team_id = current_user.id
        mechanic.market_available = False
        
        # Registrar transacción
        FinanceSystem.record_transaction(
            current_user.id,
            'expense',
            'salary_advance',
            mechanic.salary,
            f'Adelanto de salario - {mechanic.name}'
        )
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Mecánico contratado'})
    
    return jsonify({'success': False, 'message': 'Error en la contratación'})

@app.route('/buy/engineer/<int:engineer_id>')
@login_required
def buy_engineer(engineer_id):
    if len(current_user.engineers) >= Config.MAX_ENGINEERS:
        return jsonify({'success': False, 'message': 'Límite de ingenieros alcanzado'})
    
    engineer = Engineer.query.get(engineer_id)
    if engineer and engineer.market_available and current_user.money >= engineer.salary:
        engineer.team_id = current_user.id
        engineer.market_available = False
        
        # Registrar transacción
        FinanceSystem.record_transaction(
            current_user.id,
            'expense',
            'salary_advance',
            engineer.salary,
            f'Adelanto de salario - {engineer.name}'
        )
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Ingeniero contratado'})
    
    return jsonify({'success': False, 'message': 'Error en la contratación'})

# Modificar las rutas de despido en app.py

@app.route('/fire/driver/<int:driver_id>')
@login_required
def fire_driver(driver_id):
    driver = Driver.query.get(driver_id)
    if driver and driver.team_id == current_user.id:
        # Calcular años con el equipo
        years_with_team = (datetime.utcnow().date() - driver.created_at.date()).days // 365
        
        # Calcular indemnización
        from staff_generator import calculate_severance_payment
        severance_payment = calculate_severance_payment(driver.salary, years_with_team)
        
        # Verificar si el usuario tiene suficiente dinero
        if current_user.money < severance_payment:
            return jsonify({
                'success': False, 
                'message': f'No tienes suficiente dinero para pagar la indemnización (€{severance_payment:,.0f})'
            })
        
        # Aplicar el pago
        current_user.money -= severance_payment
        
        # Despedir al piloto
        driver.team_id = None
        driver.market_available = True
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Piloto despedido. Indemnización pagada: €{severance_payment:,.0f}'
        })
    
    return jsonify({'success': False, 'message': 'Error al despedir'})

@app.route('/fire/mechanic/<int:mechanic_id>')
@login_required
def fire_mechanic(mechanic_id):
    mechanic = Mechanic.query.get(mechanic_id)
    if mechanic and mechanic.team_id == current_user.id:
        # Calcular años con el equipo
        years_with_team = (datetime.utcnow().date() - mechanic.created_at.date()).days // 365
        
        # Calcular indemnización
        from staff_generator import calculate_severance_payment
        severance_payment = calculate_severance_payment(mechanic.salary, years_with_team)
        
        # Verificar si el usuario tiene suficiente dinero
        if current_user.money < severance_payment:
            return jsonify({
                'success': False, 
                'message': f'No tienes suficiente dinero para pagar la indemnización (€{severance_payment:,.0f})'
            })
        
        # Aplicar el pago
        current_user.money -= severance_payment
        
        # Despedir al mecánico
        mechanic.team_id = None
        mechanic.market_available = True
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Mecánico despedido. Indemnización pagada: €{severance_payment:,.0f}'
        })
    
    return jsonify({'success': False, 'message': 'Error al despedir'})

@app.route('/fire/engineer/<int:engineer_id>')
@login_required
def fire_engineer(engineer_id):
    engineer = Engineer.query.get(engineer_id)
    if engineer and engineer.team_id == current_user.id:
        # Calcular años con el equipo
        years_with_team = (datetime.utcnow().date() - engineer.created_at.date()).days // 365
        
        # Calcular indemnización
        from staff_generator import calculate_severance_payment
        severance_payment = calculate_severance_payment(engineer.salary, years_with_team)
        
        # Verificar si el usuario tiene suficiente dinero
        if current_user.money < severance_payment:
            return jsonify({
                'success': False, 
                'message': f'No tienes suficiente dinero para pagar la indemnización (€{severance_payment:,.0f})'
            })
        
        # Aplicar el pago
        current_user.money -= severance_payment
        
        # Despedir al ingeniero
        engineer.team_id = None
        engineer.market_available = True
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'Ingeniero despedido. Indemnización pagada: €{severance_payment:,.0f}'
        })
    
    return jsonify({'success': False, 'message': 'Error al despedir'})

@app.route('/upgrades')
@login_required
def upgrades():
    # Obtener mejora activa
    active_upgrade = Upgrade.query.filter_by(
        team_id=current_user.id, 
        completed=False
    ).first()
    
    # Obtener historial (últimas 10 mejoras)
    upgrade_history = Upgrade.query.filter_by(
        team_id=current_user.id
    ).order_by(Upgrade.start_date.desc()).limit(10).all()
    
    return render_template('upgrades.html', 
                         team=current_user,
                         active_upgrade=active_upgrade,
                         upgrade_history=upgrade_history)

@app.route('/start_upgrade', methods=['POST'])
@login_required
def start_upgrade():
    try:
        # Obtener datos del JSON
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Datos no válidos'})
        
        component_type = data.get('component_type')
        level = int(data.get('level', 1))
        weeks = int(data.get('weeks', 1))
        
        # Validar datos
        if not component_type:
            return jsonify({'success': False, 'message': 'Tipo de componente requerido'})
        
        valid_components = ['engine', 'aerodynamics', 'brakes', 'suspension']
        if component_type not in valid_components:
            return jsonify({'success': False, 'message': 'Tipo de componente no válido'})
        
        # Calcular costo basado en nivel y semanas
        base_cost = 500000 * level
        total_cost = base_cost * weeks
        
        if current_user.money < total_cost:
            return jsonify({'success': False, 'message': f'Fondos insuficientes. Necesitas €{total_cost:,.0f}'})
        
        # Verificar si ya hay una mejora en progreso
        active_upgrade = Upgrade.query.filter_by(
            team_id=current_user.id, 
            completed=False
        ).first()
        
        if active_upgrade:
            return jsonify({'success': False, 'message': 'Ya tienes una mejora en progreso'})
        
        # Crear la mejora
        upgrade = Upgrade(
            team_id=current_user.id,
            component_type=component_type,
            level=level,
            weeks=weeks,
            total_cost=total_cost,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(weeks=weeks),
            completed=False
        )
        
        # Registrar transacción financiera
        FinanceSystem.record_transaction(
            current_user.id,
            'expense',
            'upgrade',
            total_cost,
            f'Mejora de {component_type} - Nivel {level} ({weeks} semanas)'
        )
        
        db.session.add(upgrade)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Mejora de {component_type} iniciada. Costo: €{total_cost:,.0f}',
            'cost': total_cost
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al iniciar mejora: {str(e)}'})

@app.route('/complete_upgrade/<int:upgrade_id>', methods=['POST'])
@login_required
def complete_upgrade(upgrade_id):
    upgrade = Upgrade.query.get_or_404(upgrade_id)
    
    # Verificar permisos
    if upgrade.team_id != current_user.id:
        flash('No autorizado', 'danger')
        return redirect(url_for('upgrades'))
    
    # Verificar si la mejora está completa
    if upgrade.progress < 100:
        flash('La mejora aún no está completa', 'warning')
        return redirect(url_for('upgrades'))
    
    # Aplicar mejora al componente
    component = CarComponent.query.filter_by(
        team_id=current_user.id,
        component_type=upgrade.component_type
    ).first()
    
    if component:
        # Calcular mejoras basadas en el nivel
        strength_improvement = upgrade.level * 5  # +5, +10, +15
        reliability_improvement = upgrade.level * 3  # +3, +6, +9
        
        component.strength = min(100, component.strength + strength_improvement)
        component.reliability = min(100, component.reliability + reliability_improvement)
    
    # Marcar como completada
    upgrade.completed = True
    
    db.session.commit()
    
    flash(f'¡Mejora completada! +{strength_improvement} fuerza, +{reliability_improvement} fiabilidad', 'success')
    return redirect(url_for('upgrades'))

@app.route('/training')
@login_required
def training():
    # Obtener entrenamiento activo
    active_training = Training.query.filter_by(
        team_id=current_user.id, 
        completed=False
    ).first()
    
    # Obtener historial (últimos 10 entrenamientos)
    training_history = Training.query.filter_by(
        team_id=current_user.id
    ).order_by(Training.start_date.desc()).limit(10).all()
    
    return render_template('training.html', 
                         team=current_user,
                         active_training=active_training,
                         training_history=training_history)

@app.route('/start_training', methods=['POST'])
@login_required
def start_training():
    try:
        # Obtener datos del JSON
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Datos no válidos'})
        
        staff_type = data.get('staff_type')
        staff_id = int(data.get('staff_id'))
        attribute = data.get('attribute')
        level = int(data.get('level', 1))
        weeks = int(data.get('weeks', 1))
        
        # Validar datos
        if not all([staff_type, staff_id, attribute]):
            return jsonify({'success': False, 'message': 'Datos incompletos'})
        
        valid_staff_types = ['driver', 'mechanic', 'engineer']
        if staff_type not in valid_staff_types:
            return jsonify({'success': False, 'message': 'Tipo de personal no válido'})
        
        # Verificar que el personal pertenece al equipo
        staff = None
        if staff_type == 'driver':
            staff = Driver.query.filter_by(id=staff_id, team_id=current_user.id).first()
        elif staff_type == 'mechanic':
            staff = Mechanic.query.filter_by(id=staff_id, team_id=current_user.id).first()
        elif staff_type == 'engineer':
            staff = Engineer.query.filter_by(id=staff_id, team_id=current_user.id).first()
        
        if not staff:
            return jsonify({'success': False, 'message': 'Personal no encontrado o no pertenece a tu equipo'})
        
        # Calcular costo basado en nivel y semanas
        base_cost = 500000 * level
        total_cost = base_cost * weeks
        
        if current_user.money < total_cost:
            return jsonify({'success': False, 'message': f'Fondos insuficientes. Necesitas €{total_cost:,.0f}'})
        
        # Verificar si ya hay un entrenamiento en progreso para este staff
        active_training = Training.query.filter_by(
            team_id=current_user.id,
            staff_id=staff_id,
            completed=False
        ).first()
        
        if active_training:
            return jsonify({'success': False, 'message': 'Este miembro ya tiene un entrenamiento en progreso'})
        
        # Crear el entrenamiento
        training = Training(
            team_id=current_user.id,
            staff_type=staff_type,
            staff_id=staff_id,
            attribute=attribute,
            level=level,
            weeks=weeks,
            total_cost=total_cost,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(weeks=weeks),
            completed=False
        )
        
        # Registrar transacción financiera
        FinanceSystem.record_transaction(
            current_user.id,
            'expense',
            'training',
            total_cost,
            f'Entrenamiento {staff_type} - {attribute} (Nivel {level})'
        )
        
        db.session.add(training)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Entrenamiento iniciado. Costo: €{total_cost:,.0f}',
            'cost': total_cost
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al iniciar entrenamiento: {str(e)}'})

@app.route('/complete_training/<int:training_id>', methods=['POST'])
@login_required
def complete_training(training_id):
    training = Training.query.get_or_404(training_id)
    
    # Verificar permisos
    if training.team_id != current_user.id:
        flash('No autorizado', 'danger')
        return redirect(url_for('training'))
    
    # Verificar si el entrenamiento está completo
    if training.progress < 100:
        flash('El entrenamiento aún no está completo', 'warning')
        return redirect(url_for('training'))
    
    # Aplicar mejora al personal
    staff = None
    if training.staff_type == 'driver':
        staff = Driver.query.filter_by(id=training.staff_id, team_id=current_user.id).first()
    elif training.staff_type == 'mechanic':
        staff = Mechanic.query.filter_by(id=training.staff_id, team_id=current_user.id).first()
    elif training.staff_type == 'engineer':
        staff = Engineer.query.filter_by(id=training.staff_id, team_id=current_user.id).first()
    
    if staff:
        # Calcular mejora basada en el nivel
        improvement = training.level * 3  # +3, +6, +9 puntos
        
        # Aplicar mejora al atributo correspondiente
        if hasattr(staff, training.attribute):
            current_value = getattr(staff, training.attribute)
            new_value = min(100, current_value + improvement)
            setattr(staff, training.attribute, new_value)
            
            # Actualizar fecha de último entrenamiento
            staff.last_trained = datetime.utcnow().date()
    
    # Marcar como completado
    training.completed = True
    
    db.session.commit()
    
    flash(f'¡Entrenamiento completado! +{improvement} {training.attribute}', 'success')
    return redirect(url_for('training'))

# Actualizar el sistema programado para completar entrenamientos
class TrainingSystem:
    @staticmethod
    def complete_trainings():
        """Completa los entrenamientos que han terminado su tiempo"""
        trainings = Training.query.filter(
            Training.end_date <= datetime.utcnow(),
            Training.completed == False
        ).all()
        
        for training in trainings:
            # Aplicar mejora (similar a complete_training)
            staff = None
            if training.staff_type == 'driver':
                staff = Driver.query.filter_by(id=training.staff_id, team_id=training.team_id).first()
            elif training.staff_type == 'mechanic':
                staff = Mechanic.query.filter_by(id=training.staff_id, team_id=training.team_id).first()
            elif training.staff_type == 'engineer':
                staff = Engineer.query.filter_by(id=training.staff_id, team_id=training.team_id).first()
            
            if staff:
                improvement = training.level * 3
                if hasattr(staff, training.attribute):
                    current_value = getattr(staff, training.attribute)
                    new_value = min(100, current_value + improvement)
                    setattr(staff, training.attribute, new_value)
                    staff.last_trained = datetime.utcnow().date()
            
            training.completed = True
        
        db.session.commit()
        
# Añadir esta clase después de TrainingSystem
class UpgradeSystem:
    @staticmethod
    def complete_upgrades():
        """Completa las mejoras que han terminado su tiempo"""
        upgrades = Upgrade.query.filter(
            Upgrade.end_date <= datetime.utcnow(),
            Upgrade.completed == False
        ).all()
        
        for upgrade in upgrades:
            # Aplicar mejora al componente
            component = CarComponent.query.filter_by(
                team_id=upgrade.team_id,
                component_type=upgrade.component_type
            ).first()
            
            if component:
                # Calcular mejoras basadas en el nivel
                strength_improvement = upgrade.level * 5  # +5, +10, +15
                reliability_improvement = upgrade.level * 3  # +3, +6, +9
                
                component.strength = min(100, component.strength + strength_improvement)
                component.reliability = min(100, component.reliability + reliability_improvement)
            
            # Marcar como completada
            upgrade.completed = True
        
        db.session.commit()

# Actualizar la tarea programada para mejoras
def scheduled_upgrade_completion():
    with app.app_context():
        UpgradeSystem.complete_upgrades()

# Actualizar la tarea programada
def scheduled_training_completion():
    with app.app_context():
        TrainingSystem.complete_trainings()

# Añadir una ruta para forzar jubilaciones (para testing)
@app.route('/admin/retire_staff')
@login_required
def admin_retire_staff():
    """Ruta administrativa para forzar jubilaciones (solo para testing)"""
    if current_user.username != 'admin':  # Solo permitir a un usuario admin
        return jsonify({'success': False, 'message': 'No autorizado'})
    
    from staff_generator import handle_retirements
    retired_count = handle_retirements()
    return jsonify({'success': True, 'message': f'{retired_count} empleados jubilados'})

# Actualizar el sistema programado para incluir jubilaciones
def scheduled_retirement_check():
    """Verificación programada de jubilaciones"""
    with app.app_context():
        from staff_generator import handle_retirements
        retired_count = handle_retirements()
        if retired_count > 0:
            print(f"✅ {retired_count} empleados jubilados automáticamente y reemplazados")

def scheduled_aging_update():
    """Actualización programada del envejecimiento del personal"""
    with app.app_context():
        from staff_generator import update_staff_aging
        update_staff_aging()
        print("✅ Sistema de envejecimiento del personal actualizado")
        
def scheduled_test_cleanup():
    """Limpieza programada de tests antiguos"""
    with app.app_context():
        deleted_count = TestCleanupSystem.cleanup_old_tests()
        if deleted_count > 0:
            print(f"🧹 {deleted_count} tests antiguos eliminados automáticamente")
            
def scheduled_session_starter():
    """Inicia automáticamente las simulaciones cuando llega la hora programada"""
    with app.app_context():
        try:
            now = datetime.utcnow()
            print(f"🔍 Verificando sesiones programadas - {now}")
            
            # Buscar carreras que tengan sesiones que deben iniciarse
            races = Race.query.all()
            
            for race in races:
                # Verificar sesión de clasificación
                if should_start_session(race.qualifying_session, now):
                    print(f"🏁 Iniciando clasificación automática para {race.circuit.name}")
                    start_qualifying_simulation(race.id)
                
                # Verificar sesión de carrera
                if should_start_session(race.race_session, now):
                    print(f"🏎️ Iniciando carrera automática para {race.circuit.name}")
                    start_race_simulation(race.id)
                    
        except Exception as e:
            print(f"❌ Error en scheduled_session_starter: {str(e)}")

def should_start_session(session_time, current_time):
    """Determina si una sesión debe iniciarse"""
    if not session_time:
        return False
    
    # Convertir a timezone-naive para comparación
    session_naive = session_time.replace(tzinfo=None)
    current_naive = current_time.replace(tzinfo=None)
    
    # Verificar si la hora actual está dentro de la ventana de inicio (± 2 minutos)
    time_diff = (current_naive - session_naive).total_seconds()
    return abs(time_diff) <= 120  # 2 minutos de margen

def start_qualifying_simulation(race_id):
    """Inicia la simulación de clasificación en segundo plano"""
    try:
        race = Race.query.get(race_id)
        if not race:
            print(f"❌ Carrera {race_id} no encontrada")
            return False
        
        print(f"🚀 Iniciando simulación de clasificación en segundo plano para {race.circuit.name}")
        
        # Usar threading para ejecutar en segundo plano
        import threading
        thread = threading.Thread(
            target=run_qualifying_simulation, 
            args=(race_id, 0)  # 0 para usuario del sistema
        )
        thread.daemon = True
        thread.start()
        
        # Registrar el inicio en la base de datos
        event = LiveEvent(
            race_id=race_id,
            team_id=0,
            driver_id=0,
            lap=0,
            event_type='qualifying_auto_start',
            description=f'🏁 CLASIFICACIÓN INICIADA AUTOMÁTICAMENTE - {race.circuit.name}',
            session_type='qualifying'
        )
        db.session.add(event)
        db.session.commit()
        
        print(f"✅ Clasificación automática iniciada para {race.circuit.name}")
        return True
        
    except Exception as e:
        print(f"❌ Error iniciando clasificación automática: {str(e)}")
        db.session.rollback()
        return False

def start_race_simulation(race_id):
    """Inicia la simulación de carrera en segundo plano"""
    try:
        race = Race.query.get(race_id)
        if not race:
            print(f"❌ Carrera {race_id} no encontrada")
            return False
        
        print(f"🚀 Iniciando simulación de carrera en segundo plano para {race.circuit.name}")
        
        # Usar threading para ejecutar en segundo plano
        import threading
        thread = threading.Thread(
            target=run_race_simulation_wrapper, 
            args=(race_id,)
        )
        thread.daemon = True
        thread.start()
        
        # Registrar el inicio en la base de datos
        event = LiveEvent(
            race_id=race_id,
            team_id=0,
            driver_id=0,
            lap=0,
            event_type='race_auto_start',
            description=f'🏎️ CARRERA INICIADA AUTOMÁTICAMENTE - {race.circuit.name}',
            session_type='race'
        )
        db.session.add(event)
        db.session.commit()
        
        print(f"✅ Carrera automática iniciada para {race.circuit.name}")
        return True
        
    except Exception as e:
        print(f"❌ Error iniciando carrera automática: {str(e)}")
        db.session.rollback()
        return False

def run_race_simulation_wrapper(race_id):
    """Wrapper para ejecutar la simulación de carrera en segundo plano"""
    with app.app_context():
        try:
            race = Race.query.get(race_id)
            if not race:
                return
            
            # LIMPIAR SOLO EVENTOS DE CARRERA anteriores
            LiveEvent.query.filter_by(race_id=race_id, session_type='race').delete()
            
            # Obtener parrilla de salida desde qualifying
            qualifying_results = QualifyingSession.query.filter_by(
                race_id=race_id
            ).order_by(QualifyingSession.final_position.asc()).all()
            
            if not qualifying_results:
                print("❌ No hay resultados de clasificación para esta carrera")
                return
            
            # Obtener pronóstico meteorológico para la carrera
            race_weather = WeatherForecast.query.filter_by(
                race_id=race_id, 
                session_type='race'
            ).first()
            
            # EVENTO DE INICIO DE CARRERA
            start_event = LiveEvent(
                race_id=race_id,
                team_id=0,
                driver_id=0,
                lap=0,
                event_type='race_start',
                description='INICIA EL GRAN PREMIO! - SIMULACIÓN AUTOMÁTICA',
                session_type='race'
            )
            db.session.add(start_event)
            db.session.commit()
            
            # SIMULAR CARRERA CON ESTRATEGIAS
            race_results = simulate_race_with_strategies(race_id, qualifying_results, race.circuit.laps, race_weather)
            
            # GUARDAR RESULTADOS EN LA BASE DE DATOS
            save_race_results_improved(race_id, race_results)
            
            # EVENTO DE FINAL DE CARRERA
            finished_cars = [car for car in race_results if not car['dnf']]
            if finished_cars:
                winner = finished_cars[0]
                finish_event = LiveEvent(
                    race_id=race_id,
                    team_id=winner['team_id'],
                    driver_id=winner['driver_id'],
                    lap=race.circuit.laps,
                    event_type='race_finish',
                    description=f'BANDERAS A CUADROS! {winner["driver_name"]} GANA EL GRAN PREMIO! - SIMULACIÓN AUTOMÁTICA COMPLETADA',
                    session_type='race'
                )
                db.session.add(finish_event)
            else:
                finish_event = LiveEvent(
                    race_id=race_id,
                    team_id=0,
                    driver_id=0,
                    lap=race.circuit.laps,
                    event_type='race_finish',
                    description='BANDERAS A CUADROS! TODOS LOS PILOTOS ABANDONARON! - SIMULACIÓN AUTOMÁTICA COMPLETADA',
                    session_type='race'
                )
                db.session.add(finish_event)
            
            db.session.commit()
            print(f"✅ Simulación automática de carrera completada para {race.circuit.name}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERROR en simulación automática de carrera: {str(e)}")
            import traceback
            traceback.print_exc()

# Tareas programadas
scheduler = BackgroundScheduler()

# Configurar las tareas programadas
scheduler.add_job(scheduled_training_completion, 'interval', hours=1)
scheduler.add_job(scheduled_upgrade_completion, 'interval', hours=1)
scheduler.add_job(scheduled_retirement_check, 'interval', hours=24) # Verificar jubilaciones cada 24 horas
scheduler.add_job(scheduled_aging_update, 'interval', days=30)
scheduler.add_job(scheduled_test_cleanup, 'interval', hours=6)  # Cada 6 horas
scheduler.add_job(scheduled_session_starter, 'interval', minutes=1)

def simulate_scheduled_races():
    """Tarea programada para simular carreras (mantener compatibilidad)"""
    with app.app_context():
        print("🔍 Ejecutando verificación de carreras programadas (legacy)")
        scheduled_session_starter()

scheduler.add_job(simulate_scheduled_races, 'interval', minutes=30)

@app.route('/calendar')
@login_required
def calendar():
    races = Race.query.all()
    now = datetime.utcnow()
    
    # Encontrar la próxima carrera
    next_race = None
    for race in races:
        if race.race_session > now:
            next_race = race
            break
    
    return render_template('calendar.html', races=races, next_race=next_race, now=now)

@app.route('/race/<int:race_id>')
@login_required
def race_details(race_id):
    race = Race.query.get_or_404(race_id)
    
    # Obtener eventos de esta carrera
    live_events = LiveEvent.query.filter_by(race_id=race_id).all()
    
    # Obtener resultados de qualifying y carrera para la lógica
    qualifying_results = QualifyingSession.query.filter_by(race_id=race_id).all()
    race_results = ChampionshipStandings.query.filter_by(race_id=race_id).all()
    
    # Verificar que el circuito esté cargado
    if not race.circuit:
        return "Error: Circuito no encontrado para esta carrera", 500
        
    # Obtener pronósticos meteorológicos
    weather_forecasts = WeatherForecast.query.filter_by(race_id=race_id).all()
        
    now = datetime.utcnow()
    
    # Determinar si hay eventos/results para mostrar los botones correctos
    has_qualifying_events = any(event.event_type and 'qualifying' in event.event_type for event in live_events)
    has_race_events = any(event.event_type and 'race' in event.event_type for event in live_events)
    
    # Si no hay eventos pero sí hay resultados en la base de datos, también mostrar botones "Ver"
    has_qualifying_results = len(qualifying_results) > 0
    has_race_results = len(race_results) > 0
    
    return render_template('race.html', 
                         race=race, 
                         now=now, 
                         weather_forecasts=weather_forecasts,
                         live_events=live_events,
                         has_qualifying_events=has_qualifying_events or has_qualifying_results,
                         has_race_events=has_race_events or has_race_results)

@app.route('/tests/<int:race_id>')
@login_required
def test_session(race_id):
    race = Race.query.get_or_404(race_id)
    strategies = RaceStrategy.query.filter_by(
        team_id=current_user.id, 
        race_id=race_id
    ).all()
    # Obtener pronósticos meteorológicos
    weather_forecasts = WeatherForecast.query.filter_by(race_id=race_id).all()
    return render_template('tests.html', race=race, team=current_user, strategies=strategies, weather_forecasts=weather_forecasts)

@app.route('/race_strategy/<int:race_id>')
@login_required
def race_strategy(race_id):
    race = Race.query.get_or_404(race_id)
    strategies = RaceStrategy.query.filter_by(
        team_id=current_user.id, 
        race_id=race_id
    ).all()
    # Obtener pronósticos meteorológicos
    weather_forecasts = WeatherForecast.query.filter_by(race_id=race_id).all()
    return render_template('race_strategy.html', race=race, team=current_user, strategies=strategies, weather_forecasts=weather_forecasts)

@app.route('/save_race_strategy', methods=['POST'])
@login_required
def save_race_strategy():
    data = request.json
    
    # Verificar que el piloto pertenece al equipo
    driver = Driver.query.get(data['driver_id'])
    if not driver or driver.team_id != current_user.id:
        return jsonify({'success': False, 'message': 'Piloto no válido'})
    
    # Crear nueva estrategia
    strategy = RaceStrategy(
        team_id=current_user.id,
        race_id=data['race_id'],
        driver_id=data['driver_id'],
        strategy_name=data['strategy_name'],
        total_pit_stops=len(data['segments']) - 1,
        starting_tyre=data.get('starting_tyre', 'soft'),
        rain_strategy=data.get('rain_strategy', 'continue'),
        heavy_rain_strategy=data.get('heavy_rain_strategy', 'continue'),
        dry_strategy=data.get('dry_strategy', 'continue')
    )
    db.session.add(strategy)
    db.session.flush()
    
    # Crear segmentos
    for segment_data in data['segments']:
        segment = StrategySegment(
            strategy_id=strategy.id,
            segment_order=segment_data['segment_order'],
            tyre_type=segment_data['tyre_type'],
            laps_planned=segment_data['laps_planned']
        )
        db.session.add(segment)
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Estrategia guardada'})

@app.route('/delete_strategy/<int:strategy_id>')
@login_required
def delete_strategy(strategy_id):
    strategy = RaceStrategy.query.get(strategy_id)
    if strategy and strategy.team_id == current_user.id:
        # Eliminar segmentos primero
        StrategySegment.query.filter_by(strategy_id=strategy_id).delete()
        db.session.delete(strategy)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Estrategia eliminada'})
    
    return jsonify({'success': False, 'message': 'Error al eliminar'})

@app.route('/get_tyre_data')
@login_required
def get_tyre_data():
    tyres = TyreType.query.all()
    tyre_data = {}
    for tyre in tyres:
        tyre_data[tyre.name] = {
            'dry_performance': tyre.dry_performance,
            'wet_performance': tyre.wet_performance,
            'durability': tyre.durability,
            'warmup_time': tyre.warmup_time
        }
    return jsonify(tyre_data)

@app.route('/standings')
@login_required
def standings():
    """Página principal de clasificaciones"""
    return render_template('standings.html')

@app.route('/api/standings/drivers')
@login_required
def api_driver_standings():
    """API para clasificación de pilotos (totales)"""
    # Obtener todos los resultados agrupados por piloto
    driver_results = db.session.query(
        Driver.id,
        Driver.name,
        User.team_name,
        db.func.sum(ChampionshipStandings.points).label('total_points'),
        db.func.count(ChampionshipStandings.id).label('races_entered')
    ).join(ChampionshipStandings, Driver.id == ChampionshipStandings.driver_id
    ).join(User, ChampionshipStandings.team_id == User.id
    ).group_by(Driver.id, Driver.name, User.team_name
    ).order_by(db.desc('total_points')).all()
    
    standings = []
    for i, result in enumerate(driver_results):
        standings.append({
            'position': i + 1,
            'driver_name': result.name,
            'team_name': result.team_name,
            'total_points': result.total_points or 0,
            'races_entered': result.races_entered or 0
        })
    
    return jsonify(standings)

@app.route('/api/standings/teams')
@login_required
def api_team_standings():
    """API para clasificación de escuderías (totales)"""
    # Obtener todos los resultados agrupados por equipo
    team_results = db.session.query(
        User.id,
        User.team_name,
        db.func.sum(ChampionshipStandings.points).label('total_points'),
        db.func.count(ChampionshipStandings.id).label('races_entered')
    ).join(ChampionshipStandings, User.id == ChampionshipStandings.team_id
    ).group_by(User.id, User.team_name
    ).order_by(db.desc('total_points')).all()
    
    standings = []
    for i, result in enumerate(team_results):
        standings.append({
            'position': i + 1,
            'team_name': result.team_name,
            'total_points': result.total_points or 0,
            'races_entered': result.races_entered or 0
        })
    
    return jsonify(standings)

@app.route('/api/standings/race/<int:race_id>/drivers')
@login_required
def api_race_driver_standings(race_id):
    """API para clasificación de pilotos por carrera específica"""
    race_results = db.session.query(
        ChampionshipStandings.position,
        Driver.name,
        User.team_name,
        ChampionshipStandings.points,
        ChampionshipStandings.fastest_lap,
        ChampionshipStandings.dnf
    ).join(Driver, ChampionshipStandings.driver_id == Driver.id
    ).join(User, ChampionshipStandings.team_id == User.id
    ).filter(ChampionshipStandings.race_id == race_id
    ).order_by(ChampionshipStandings.position).all()
    
    standings = []
    for result in race_results:
        standings.append({
            'position': result.position,
            'driver_name': result.name,
            'team_name': result.team_name,
            'points': result.points,
            'fastest_lap': result.fastest_lap,
            'dnf': result.dnf,
            'status': 'DNF' if result.dnf else 'Finished'
        })
    
    return jsonify(standings)

@app.route('/api/standings/race/<int:race_id>/teams')
@login_required
def api_race_team_standings(race_id):
    """API para clasificación de escuderías por carrera específica"""
    team_results = db.session.query(
        User.team_name,
        db.func.sum(ChampionshipStandings.points).label('race_points')
    ).join(ChampionshipStandings, User.id == ChampionshipStandings.team_id
    ).filter(ChampionshipStandings.race_id == race_id
    ).group_by(User.team_name
    ).order_by(db.desc('race_points')).all()
    
    standings = []
    for i, result in enumerate(team_results):
        standings.append({
            'position': i + 1,
            'team_name': result.team_name,
            'points': result.race_points or 0
        })
    
    return jsonify(standings)

@app.route('/api/races')
@login_required
def api_races():
    """API para listar todas las carreras"""
    races = Race.query.all()
    races_data = []
    for race in races:
        races_data.append({
            'id': race.id,
            'name': race.circuit.name,
            'country': race.circuit.country,
            'round_number': race.round_number,
            'race_date': race.race_session.strftime('%Y-%m-%d')
        })
    
    return jsonify(races_data)
    
@app.route('/championship')
@login_required
def championship():
    """Página de clasificación del campeonato"""
    # Obtener todas las carreras para el selector
    races = Race.query.all()
    
    # Obtener clasificación actual de pilotos
    driver_standings = db.session.query(
        Driver.id,
        Driver.name,
        User.team_name,
        db.func.sum(ChampionshipStandings.points).label('total_points'),
        db.func.count(ChampionshipStandings.id).label('races_entered')
    ).join(ChampionshipStandings, Driver.id == ChampionshipStandings.driver_id
    ).join(User, ChampionshipStandings.team_id == User.id
    ).group_by(Driver.id, Driver.name, User.team_name
    ).order_by(db.desc('total_points')).all()
    
    # Obtener clasificación actual de equipos
    team_standings = db.session.query(
        User.id,
        User.team_name,
        db.func.sum(ChampionshipStandings.points).label('total_points'),
        db.func.count(ChampionshipStandings.id).label('races_entered')
    ).join(ChampionshipStandings, User.id == ChampionshipStandings.team_id
    ).group_by(User.id, User.team_name
    ).order_by(db.desc('total_points')).all()
    
    return render_template('championship.html', 
                         races=races,
                         driver_standings=driver_standings,
                         team_standings=team_standings)
                         
@app.route('/api/simulate_test', methods=['POST'])
@login_required
def api_simulate_test():
    """API para simular tests y guardar en base de datos"""
    try:
        # VERIFICAR LÍMITE ANTES DE SIMULAR
        active_tests_count = TestCleanupSystem.get_remaining_tests_count(current_user.id)
        if active_tests_count >= 5:
            return jsonify({
                'success': False, 
                'message': f'Has alcanzado el límite máximo de 5 tests activos. Los tests se eliminarán automáticamente después de cada carrera.'
            })
        
        data = request.get_json()
        
        # Validar datos
        required_fields = ['driver_id', 'tyre_type', 'total_laps', 'track_condition', 'test_results']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Campo requerido faltante: {field}'})
        
        # Verificar que el piloto pertenece al equipo
        driver = Driver.query.filter_by(id=data['driver_id'], team_id=current_user.id).first()
        if not driver:
            return jsonify({'success': False, 'message': 'Piloto no válido'})
        
        # Calcular estadísticas del test
        lap_times = [lap['lap_time'] for lap in data['test_results']]
        best_lap = min(lap_times)
        avg_lap = sum(lap_times) / len(lap_times)
        incidents = sum(1 for lap in data['test_results'] if lap.get('incident_occurred', False))
        pit_stops = sum(1 for lap in data['test_results'] if lap.get('pit_stop', False))
        total_time_lost = sum(lap.get('time_lost', 0) for lap in data['test_results'])
        
        # Crear y guardar el test en la base de datos
        test = Test(
            team_id=current_user.id,
            driver_id=data['driver_id'],
            race_id=data.get('race_id', 1),  # Usar la carrera actual o default
            initial_tyre=data['tyre_type'],
            track_condition=data['track_condition'],
            total_laps=data['total_laps'],
            best_lap=best_lap,
            avg_lap=avg_lap,
            incidents=incidents,
            pit_stops=pit_stops,
            total_time_lost=total_time_lost,
            lap_data=json.dumps(data['test_results'])  # Guardar todos los datos de vueltas como JSON
        )
        
        db.session.add(test)
        db.session.commit()
        
        # Verificar el nuevo conteo
        new_count = TestCleanupSystem.get_remaining_tests_count(current_user.id)
        
        return jsonify({
            'success': True, 
            'message': f'Test simulado y guardado exitosamente. Tests activos: {new_count}/5',
            'test_id': test.id,
            'best_lap': best_lap,
            'avg_lap': avg_lap,
            'tests_remaining': max(0, 5 - new_count)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error en la simulación: {str(e)}'})
        
@app.route('/api/tests/leaderboard')
@login_required
def api_tests_leaderboard():
    """API para obtener la clasificación general de tests - VERSIÓN CORREGIDA"""
    try:
        print(f"DEBUG: Solicitando leaderboard para usuario: {current_user.id}")
        
        # Obtener TODOS los tests ordenados por mejor vuelta
        leaderboard_query = db.session.query(
            Test.id,
            Test.driver_id,
            Driver.name.label('driver_name'),
            User.id.label('team_id'),
            User.team_name,
            Test.best_lap,
            Test.total_laps,
            Test.initial_tyre,
            Test.created_at
        ).join(Driver, Test.driver_id == Driver.id
        ).join(User, Test.team_id == User.id
        ).order_by(Test.best_lap.asc()).limit(50).all()
        
        print(f"DEBUG: Encontrados {len(leaderboard_query)} tests en total")
        
        # Para debugging, mostrar todos los tests encontrados
        for test in leaderboard_query:
            print(f"DEBUG - Test: driver={test.driver_name}, team={test.team_name}, best_lap={test.best_lap}")
        
        leaderboard_data = []
        seen_drivers = set()  # Para evitar duplicados
        
        for i, result in enumerate(leaderboard_query):
            # Solo mostrar el mejor resultado por piloto
            if result.driver_id not in seen_drivers:
                seen_drivers.add(result.driver_id)
                
                # Contar cuántos tests tiene este piloto
                tests_count = Test.query.filter_by(driver_id=result.driver_id).count()
                
                leaderboard_data.append({
                    'position': len(seen_drivers),
                    'driver_id': result.driver_id,
                    'driver_name': result.driver_name,
                    'team_id': result.team_id,
                    'team_name': result.team_name,
                    'best_lap': result.best_lap,
                    'total_laps': result.total_laps,
                    'initial_tyre': result.initial_tyre,
                    'tests_count': tests_count,
                    'created_at': result.created_at.strftime('%Y-%m-%d %H:%M'),
                    'is_my_team': result.team_id == current_user.id
                })
        
        print(f"DEBUG: Leaderboard final con {len(leaderboard_data)} pilotos únicos")
        return jsonify(leaderboard_data)
        
    except Exception as e:
        print(f"ERROR en api_tests_leaderboard: {str(e)}")
        return jsonify([])

@app.route('/api/tests/my_team')
@login_required
def api_my_team_tests():
    """API para obtener los tests del equipo actual - VERSIÓN CORREGIDA"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        print(f"DEBUG: Solicitando tests del equipo {current_user.id}, página {page}")
        
        tests = Test.query.filter_by(team_id=current_user.id).order_by(
            Test.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        print(f"DEBUG: Encontrados {tests.total} tests para el equipo {current_user.id}")
        
        tests_data = []
        for test in tests.items:
            # Asegurarse de que las relaciones estén cargadas
            driver_name = test.driver.name if test.driver else "Piloto Desconocido"
            circuit_name = test.race.circuit.name if test.race and test.race.circuit else "Circuito Desconocido"
            
            tests_data.append({
                'id': test.id,
                'driver_name': driver_name,
                'circuit_name': circuit_name,
                'best_lap': test.best_lap,
                'avg_lap': test.avg_lap,
                'total_laps': test.total_laps,
                'incidents': test.incidents,
                'pit_stops': test.pit_stops,
                'initial_tyre': test.initial_tyre,
                'track_condition': test.track_condition,
                'created_at': test.created_at.strftime('%d/%m/%Y %H:%M')
            })
            
            print(f"DEBUG - Test equipo: {driver_name}, best_lap={test.best_lap}")
        
        return jsonify({
            'tests': tests_data,
            'total_pages': tests.pages,
            'current_page': page,
            'has_next': tests.has_next,
            'has_prev': tests.has_prev,
            'total_tests': tests.total
        })
        
    except Exception as e:
        print(f"ERROR en api_my_team_tests: {str(e)}")
        return jsonify({
            'tests': [],
            'total_pages': 0,
            'current_page': page,
            'has_next': False,
            'has_prev': False,
            'total_tests': 0
        })

@app.route('/api/tests/my_team/count')
@login_required
def api_my_team_tests_count():
    """API para obtener el número de tests activos del equipo"""
    try:
        active_tests_count = TestCleanupSystem.get_remaining_tests_count(current_user.id)
        
        return jsonify({
            'count': active_tests_count,
            'limit': 5,
            'remaining': max(0, 5 - active_tests_count)
        })
        
    except Exception as e:
        print(f"ERROR en api_my_team_tests_count: {str(e)}")
        return jsonify({
            'count': 0,
            'limit': 5,
            'remaining': 5
        })

@app.route('/finances')
@login_required
def finances():
    """Página principal de finanzas"""
    # Obtener transacciones recientes
    recent_transactions = FinancialTransaction.query.filter_by(
        team_id=current_user.id
    ).order_by(FinancialTransaction.created_at.desc()).limit(50).all()
    
    # Calcular gastos mensuales en salarios
    monthly_salary_cost = 0
    for driver in current_user.drivers:
        monthly_salary_cost += driver.salary
    for mechanic in current_user.mechanics:
        monthly_salary_cost += mechanic.salary
    for engineer in current_user.engineers:
        monthly_salary_cost += engineer.salary
    
    # Calcular totales
    total_income = sum(t.amount for t in recent_transactions if t.transaction_type == 'income')
    total_expenses = sum(t.amount for t in recent_transactions if t.transaction_type == 'expense')
    net_balance = total_income - total_expenses
    
    return render_template('finances.html',
                         transactions=recent_transactions,
                         monthly_salary_cost=monthly_salary_cost,
                         total_income=total_income,
                         total_expenses=total_expenses,
                         net_balance=net_balance)

@app.route('/api/finances/transactions')
@login_required
def api_finance_transactions():
    """API para obtener transacciones con filtros"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Filtros
    transaction_type = request.args.get('type')
    category = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = FinancialTransaction.query.filter_by(team_id=current_user.id)
    
    if transaction_type and transaction_type != 'all':
        query = query.filter_by(transaction_type=transaction_type)
    
    if category and category != 'all':
        query = query.filter_by(category=category)
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(FinancialTransaction.created_at >= start_date)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(FinancialTransaction.created_at <= end_date)
        except ValueError:
            pass
    
    transactions = query.order_by(FinancialTransaction.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    transactions_data = []
    for transaction in transactions.items:
        transactions_data.append({
            'id': transaction.id,
            'type': transaction.transaction_type,
            'category': transaction.category,
            'amount': transaction.amount,
            'description': transaction.description,
            'balance_after': transaction.balance_after,
            'date': transaction.created_at.strftime('%d/%m/%Y %H:%M')
        })
    
    return jsonify({
        'transactions': transactions_data,
        'total_pages': transactions.pages,
        'current_page': page,
        'has_next': transactions.has_next,
        'has_prev': transactions.has_prev
    })

@app.route('/api/finances/stats')
@login_required
def api_finance_stats():
    """API para obtener estadísticas financieras"""
    # Últimos 6 meses
    cutoff_date = datetime.utcnow() - timedelta(days=180)
    
    # Ingresos y gastos por mes
    monthly_stats = db.session.query(
        db.func.strftime('%Y-%m', FinancialTransaction.created_at).label('month'),
        db.func.sum(
            db.case(
                (FinancialTransaction.transaction_type == 'income', FinancialTransaction.amount),
                else_=0
            )
        ).label('income'),
        db.func.sum(
            db.case(
                (FinancialTransaction.transaction_type == 'expense', FinancialTransaction.amount),
                else_=0
            )
        ).label('expenses')
    ).filter(
        FinancialTransaction.team_id == current_user.id,
        FinancialTransaction.created_at >= cutoff_date
    ).group_by('month').order_by('month').all()
    
    # Gastos por categoría (último mes)
    last_month = datetime.utcnow().replace(day=1) - timedelta(days=1)
    category_stats = db.session.query(
        FinancialTransaction.category,
        db.func.sum(FinancialTransaction.amount).label('total')
    ).filter(
        FinancialTransaction.team_id == current_user.id,
        FinancialTransaction.transaction_type == 'expense',
        db.func.strftime('%Y-%m', FinancialTransaction.created_at) == last_month.strftime('%Y-%m')
    ).group_by(FinancialTransaction.category).all()
    
    return jsonify({
        'monthly_stats': [{
            'month': stat.month,
            'income': stat.income or 0,
            'expenses': stat.expenses or 0
        } for stat in monthly_stats],
        'category_stats': [{
            'category': stat.category,
            'total': stat.total or 0
        } for stat in category_stats]
    })

# Añadir en app.py después de las rutas existentes

@app.route('/qualifying/<int:race_id>')
@login_required
def qualifying_session(race_id):
    """Página de preparación para la clasificación"""
    race = Race.query.get_or_404(race_id)
    
    # Obtener pronóstico específico para la clasificación
    qualifying_weather = WeatherForecast.query.filter_by(
        race_id=race_id, 
        session_type='qualifying'
    ).first()
    
    # CORREGIDO: Obtener elecciones existentes de forma más precisa
    existing_choices = []
    team_drivers = current_user.drivers
    
    # DEBUG detallado
    print(f"DEBUG: Iniciando busqueda de elecciones para equipo {current_user.id}")
    print(f"DEBUG: Pilotos del equipo: {[d.id for d in team_drivers]}")
    
    for driver in team_drivers:
        choice = QualifyingSession.query.filter_by(
            race_id=race_id,
            team_id=current_user.id,
            driver_id=driver.id
        ).first()
        
        if choice:
            existing_choices.append(choice)
            print(f"DEBUG: [MATCH] Eleccion para {driver.name} (ID:{driver.id}): {choice.tyre_choice}")
        else:
            print(f"DEBUG: [NO MATCH] Sin eleccion para {driver.name} (ID:{driver.id})")
    
    # Verificar si hay elecciones huérfanas (para otros pilotos)
    orphan_choices = QualifyingSession.query.filter_by(
        race_id=race_id,
        team_id=current_user.id
    ).filter(
        ~QualifyingSession.driver_id.in_([d.id for d in team_drivers])
    ).all()
    
    if orphan_choices:
        print(f"DEBUG: [ALERTA] {len(orphan_choices)} elecciones huerfanas encontradas")
        for choice in orphan_choices:
            driver = Driver.query.get(choice.driver_id)
            driver_name = driver.name if driver else f"Piloto-{choice.driver_id}"
            print(f"DEBUG: [Huerfana] Driver ID: {choice.driver_id} ({driver_name}), Tyre: {choice.tyre_choice}")
    
    # Lógica de preparación
    total_drivers = len(team_drivers)
    drivers_with_choices = len(existing_choices)
    is_fully_prepared = drivers_with_choices == total_drivers
    
    print(f"DEBUG: Resumen final - Elecciones: {drivers_with_choices}/{total_drivers}, Preparado: {is_fully_prepared}")
    
    return render_template('qualifying.html', 
                         race=race,
                         qualifying_weather=qualifying_weather,
                         existing_choices=existing_choices,
                         is_fully_prepared=is_fully_prepared,
                         team=current_user)
    
    # DEBUG: Verificar todas las elecciones en la base de datos para este equipo
    all_choices = QualifyingSession.query.filter_by(
        race_id=race_id,
        team_id=current_user.id
    ).all()
    
    print(f"DEBUG: Total elecciones en BD para equipo {current_user.id}: {len(all_choices)}")
    for choice in all_choices:
        driver_name = Driver.query.get(choice.driver_id).name if Driver.query.get(choice.driver_id) else "N/A"
        print(f"DEBUG: - Eleccion BD: driver_id={choice.driver_id} ({driver_name}), tyre={choice.tyre_choice}")
    
    # CORREGIDO: Lógica de preparación
    total_drivers = len(team_drivers)
    drivers_with_choices = len(existing_choices)
    is_fully_prepared = drivers_with_choices == total_drivers
    
    print(f"DEBUG: Resumen - {drivers_with_choices}/{total_drivers} pilotos preparados, Completamente preparado: {is_fully_prepared}")
    
    return render_template('qualifying.html', 
                         race=race,
                         qualifying_weather=qualifying_weather,
                         existing_choices=existing_choices,
                         is_fully_prepared=is_fully_prepared,
                         team=current_user)

@app.route('/api/qualifying_results/<int:race_id>')
@login_required
def api_qualifying_results(race_id):
    """API para obtener resultados de clasificación"""
    try:
        print(f"DEBUG: Solicitando resultados de clasificación para carrera {race_id}")
        
        # Obtener resultados de clasificación ordenados por posición final
        results = QualifyingSession.query.filter_by(race_id=race_id).join(
            Driver, QualifyingSession.driver_id == Driver.id
        ).join(
            User, QualifyingSession.team_id == User.id
        ).order_by(
            QualifyingSession.final_position.asc()
        ).all()
        
        print(f"DEBUG: Encontrados {len(results)} resultados de clasificación")
        
        results_data = []
        for result in results:
            results_data.append({
                'driver_name': result.driver.name,
                'team_name': result.team.team_name,
                'tyre_choice': result.tyre_choice,
                'q1_time': result.q1_time,
                'q2_time': result.q2_time,
                'q3_time': result.q3_time,
                'final_position': result.final_position
            })
            print(f"DEBUG - Resultado: {result.driver.name}, Pos: {result.final_position}, Q1: {result.q1_time}")
        
        return jsonify(results_data)
        
    except Exception as e:
        print(f"Error en api_qualifying_results: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify([])

@app.route('/api/qualifying/tyre_choice', methods=['POST'])
@login_required
def set_qualifying_tyre():
    """API para elegir neumáticos de clasificación"""
    try:
        data = request.get_json()
        race_id = data.get('race_id')
        driver_id = data.get('driver_id')
        tyre_choice = data.get('tyre_choice')
        strategy = data.get('strategy', 'balanced')
        
        print(f"DEBUG: Recibiendo eleccion - race_id: {race_id}, driver_id: {driver_id}, tyre: {tyre_choice}")
        
        # Validaciones
        if not all([race_id, driver_id, tyre_choice]):
            return jsonify({'success': False, 'message': 'Datos incompletos'})
        
        # Verificar que el piloto pertenece al equipo
        driver = Driver.query.filter_by(id=driver_id, team_id=current_user.id).first()
        if not driver:
            print(f"DEBUG: ERROR - Piloto {driver_id} no pertenece al equipo {current_user.id}")
            return jsonify({'success': False, 'message': 'Piloto no válido'})
        
        # Verificar neumático válido
        valid_tyres = ['soft', 'medium', 'hard', 'wet', 'extreme_wet']
        if tyre_choice not in valid_tyres:
            return jsonify({'success': False, 'message': 'Neumático no válido'})
        
        # Verificar si ya existe una elección
        existing = QualifyingSession.query.filter_by(
            race_id=race_id,
            team_id=current_user.id,
            driver_id=driver_id
        ).first()
        
        if existing:
            # Actualizar elección existente
            existing.tyre_choice = tyre_choice
            action = "actualizada"
            print(f"DEBUG: Eleccion actualizada para piloto {driver_id}")
        else:
            # Crear nueva elección
            qualifying = QualifyingSession(
                race_id=race_id,
                team_id=current_user.id,
                driver_id=driver_id,
                tyre_choice=tyre_choice
            )
            db.session.add(qualifying)
            action = "guardada"
            print(f"DEBUG: Nueva eleccion creada para piloto {driver_id}")
        
        db.session.commit()
        print(f"DEBUG: Eleccion {action} exitosamente para piloto {driver_id}")
        
        return jsonify({
            'success': True, 
            'message': f'Neumáticos {tyre_choice} seleccionados para la clasificación'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"ERROR: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})
        
@app.route('/debug/qualifying_detailed/<int:race_id>')
@login_required
def debug_qualifying_detailed(race_id):
    """Diagnóstico detallado del problema"""
    team_drivers = current_user.drivers
    all_choices = QualifyingSession.query.filter_by(
        race_id=race_id,
        team_id=current_user.id
    ).all()
    
    # Diagnóstico detallado
    diagnostic = {
        'team': {
            'id': current_user.id,
            'name': current_user.team_name,
            'drivers': []
        },
        'choices_in_db': [],
        'matching_analysis': []
    }
    
    # Información de los pilotos del equipo
    for driver in team_drivers:
        diagnostic['team']['drivers'].append({
            'id': driver.id,
            'name': driver.name
        })
    
    # Información de las elecciones en BD
    for choice in all_choices:
        driver = Driver.query.get(choice.driver_id)
        diagnostic['choices_in_db'].append({
            'choice_id': choice.id,
            'driver_id': choice.driver_id,
            'driver_name': driver.name if driver else 'N/A',
            'tyre_choice': choice.tyre_choice,
            'team_id': choice.team_id
        })
    
    # Análisis de matching
    for driver in team_drivers:
        choice = QualifyingSession.query.filter_by(
            race_id=race_id,
            team_id=current_user.id,
            driver_id=driver.id
        ).first()
        
        diagnostic['matching_analysis'].append({
            'driver_id': driver.id,
            'driver_name': driver.name,
            'has_choice': choice is not None,
            'choice_tyre': choice.tyre_choice if choice else None,
            'choice_driver_id': choice.driver_id if choice else None
        })
    
    return jsonify(diagnostic)
    
@app.route('/debug/qualifying_status/<int:race_id>')
@login_required
def debug_qualifying_status(race_id):
    """Diagnóstico del estado de la clasificación"""
    # Verificar equipos y pilotos
    all_teams = User.query.filter(User.drivers.any()).all()
    team_info = []
    
    for team in all_teams:
        team_info.append({
            'team_id': team.id,
            'team_name': team.team_name,
            'drivers_count': len(team.drivers),
            'drivers': [{'id': d.id, 'name': d.name} for d in team.drivers]
        })
    
    # Verificar elecciones de neumáticos
    qualifying_choices = QualifyingSession.query.filter_by(race_id=race_id).all()
    choices_info = []
    
    for choice in qualifying_choices:
        choices_info.append({
            'team_id': choice.team_id,
            'driver_id': choice.driver_id,
            'driver_name': choice.driver.name if choice.driver else 'N/A',
            'tyre_choice': choice.tyre_choice
        })
    
    return jsonify({
        'teams': team_info,
        'qualifying_choices': choices_info,
        'total_teams': len(all_teams),
        'total_choices': len(qualifying_choices)
    })
        
@app.route('/api/qualifying/clear_choices', methods=['POST'])
@login_required
def clear_qualifying_choices():
    """API para limpiar todas las elecciones de neumáticos del equipo"""
    try:
        data = request.get_json()
        race_id = data.get('race_id')
        
        if not race_id:
            return jsonify({'success': False, 'message': 'ID de carrera no proporcionado'})
        
        # DEBUG: Verificar qué se va a eliminar
        choices_to_delete = QualifyingSession.query.filter_by(
            race_id=race_id,
            team_id=current_user.id
        ).all()
        
        print(f"DEBUG: Eliminando {len(choices_to_delete)} elecciones para equipo {current_user.id}")
        for choice in choices_to_delete:
            driver_name = Driver.query.get(choice.driver_id).name if Driver.query.get(choice.driver_id) else "N/A"
            print(f"DEBUG: - Eliminando: {driver_name} ({choice.tyre_choice})")
        
        # Eliminar todas las elecciones del equipo para esta carrera
        deleted_count = QualifyingSession.query.filter_by(
            race_id=race_id,
            team_id=current_user.id
        ).delete()
        
        db.session.commit()
        
        print(f"DEBUG: {deleted_count} elecciones eliminadas para el equipo {current_user.id}")
        
        return jsonify({
            'success': True, 
            'message': f'{deleted_count} elecciones de neumáticos eliminadas'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"ERROR al limpiar elecciones: {str(e)}")
        return jsonify({'success': False, 'message': f'Error al limpiar elecciones: {str(e)}'})
        
@app.route('/api/qualifying/clear_driver_choice', methods=['POST'])
@login_required
def clear_driver_qualifying_choice():
    """API para limpiar la elección de neumáticos de un piloto específico"""
    try:
        data = request.get_json()
        race_id = data.get('race_id')
        driver_id = data.get('driver_id')
        
        if not all([race_id, driver_id]):
            return jsonify({'success': False, 'message': 'Datos incompletos'})
        
        # Verificar que el piloto pertenece al equipo
        driver = Driver.query.filter_by(id=driver_id, team_id=current_user.id).first()
        if not driver:
            return jsonify({'success': False, 'message': 'Piloto no válido'})
        
        # Eliminar la elección específica
        deleted_count = QualifyingSession.query.filter_by(
            race_id=race_id,
            team_id=current_user.id,
            driver_id=driver_id
        ).delete()
        
        db.session.commit()
        
        driver_name = driver.name
        print(f"DEBUG: Elección eliminada para piloto {driver_id} ({driver_name})")
        
        return jsonify({
            'success': True, 
            'message': f'Elección eliminada para {driver_name}'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"ERROR al limpiar elección individual: {str(e)}")
        return jsonify({'success': False, 'message': f'Error al eliminar elección: {str(e)}'})

@app.route('/simulate_qualifying/<int:race_id>')
@login_required
def simulate_qualifying(race_id):
    """Simular la sesión de clasificación"""
    try:
        # Obtener todas las elecciones de neumáticos
        qualifying_choices = QualifyingSession.query.filter_by(race_id=race_id).all()
        
        if not qualifying_choices:
            return jsonify({'success': False, 'message': 'No hay equipos preparados para la clasificación'})
        
        # Obtener pronóstico meteorológico
        weather = WeatherForecast.query.filter_by(
            race_id=race_id, 
            session_type='qualifying'
        ).first()
        
        # Simular Q1, Q2, Q3
        results = simulate_qualifying_session(qualifying_choices, weather)
        
        # Guardar resultados
        for result in results:
            qualifying = QualifyingSession.query.filter_by(
                race_id=race_id,
                team_id=result['team_id'],
                driver_id=result['driver_id']
            ).first()
            
            if qualifying:
                qualifying.q1_time = result['q1_time']
                qualifying.q2_time = result.get('q2_time')
                qualifying.q3_time = result.get('q3_time')
                qualifying.final_position = result['final_position']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Clasificación simulada exitosamente',
            'results': results
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error en la simulación: {str(e)}'})

def simulate_qualifying_session(qualifying_choices, weather):
    """Simula las tres partes de la clasificación"""
    results = []
    
    # Simular Q1 - Todos los pilotos
    q1_results = []
    for choice in qualifying_choices:
        base_time = calculate_base_qualifying_time(choice.driver, choice.team, choice.tyre_choice, weather)
        q1_time = apply_weather_effects(base_time, choice.tyre_choice, weather)
        q1_results.append({
            'team_id': choice.team_id,
            'driver_id': choice.driver_id,
            'driver_name': choice.driver.name,
            'team_name': choice.team.team_name,
            'tyre_choice': choice.tyre_choice,
            'q1_time': q1_time
        })
    
    # Ordenar Q1 y eliminar los más lentos (top 15 pasan a Q2)
    q1_results.sort(key=lambda x: x['q1_time'])
    q2_participants = q1_results[:15]
    
    # Simular Q2
    for participant in q2_participants:
        base_time = calculate_base_qualifying_time(
            Driver.query.get(participant['driver_id']),
            User.query.get(participant['team_id']),
            participant['tyre_choice'],
            weather
        )
        q2_time = apply_weather_effects(base_time, participant['tyre_choice'], weather)
        participant['q2_time'] = q2_time
    
    # Ordenar Q2 y eliminar los más lentos (top 10 pasan a Q3)
    q2_participants.sort(key=lambda x: x['q2_time'])
    q3_participants = q2_participants[:10]
    
    # Simular Q3
    for participant in q3_participants:
        base_time = calculate_base_qualifying_time(
            Driver.query.get(participant['driver_id']),
            User.query.get(participant['team_id']),
            participant['tyre_choice'],
            weather
        )
        q3_time = apply_weather_effects(base_time, participant['tyre_choice'], weather)
        participant['q3_time'] = q3_time
    
    # Ordenar final por Q3 (o Q2 si no hay Q3)
    q3_participants.sort(key=lambda x: x.get('q3_time', x['q2_time']))
    
    # Asignar posiciones finales
    for i, participant in enumerate(q3_participants):
        participant['final_position'] = i + 1
    
    # Combinar todos los resultados
    all_participants = q3_participants + [p for p in q1_results if p not in q3_participants]
    for i, participant in enumerate(all_participants):
        if 'final_position' not in participant:
            participant['final_position'] = i + 1
    
    return all_participants

def calculate_base_qualifying_time(driver, team, tyre_choice, weather):
    """Calcula el tiempo base para una vuelta de clasificación"""
    # Tiempo base según circuito (aproximado)
    base_time = 85.0  # 1:25.000 como referencia
    
    # Efecto del piloto
    driver_skill = (driver.skill + driver.experience) / 2
    driver_effect = (100 - driver_skill) / 200  # Mejor piloto = menos tiempo
    
    # Efecto del coche
    car_performance = sum(comp.strength for comp in team.car_components) / 4
    car_effect = (100 - car_performance) / 150
    
    # Efecto del neumático
    tyre_effects = {
        'soft': -2.0,    # Más rápido
        'medium': -1.0,  # Intermedio
        'hard': 0.0,     # Neutral
        'wet': 8.0,      # Más lento en seco
        'extreme_wet': 12.0  # Mucho más lento en seco
    }
    tyre_effect = tyre_effects.get(tyre_choice, 0.0)
    
    # Ajustar neumático según condiciones
    if weather and weather.condition != 'dry':
        if weather.condition == 'light_rain':
            if tyre_choice in ['soft', 'medium', 'hard']:
                tyre_effect += 15.0  # Muy lento con neumáticos de seco en lluvia
            elif tyre_choice == 'wet':
                tyre_effect = 2.0    # Bueno para lluvia ligera
            else:  # extreme_wet
                tyre_effect = 4.0    # Demasiado conservador
        elif weather.condition == 'heavy_rain':
            if tyre_choice in ['soft', 'medium', 'hard']:
                tyre_effect += 25.0  # Extremadamente lento/peligroso
            elif tyre_choice == 'wet':
                tyre_effect += 8.0   # Riesgoso en lluvia intensa
            else:  # extreme_wet
                tyre_effect = 3.0    # Ideal para lluvia intensa
    
    # Factor aleatorio
    random_factor = random.uniform(-0.5, 0.5)
    
    # Cálculo final
    final_time = base_time - driver_effect - car_effect + tyre_effect + random_factor
    return round(final_time, 3)

def apply_weather_effects(base_time, tyre_choice, weather):
    """Aplica efectos meteorológicos adicionales"""
    if not weather:
        return base_time
    
    time_penalty = 0
    
    # Penalizaciones por neumático incorrecto
    if weather.condition == 'light_rain' and tyre_choice in ['soft', 'medium', 'hard']:
        time_penalty += random.uniform(2.0, 5.0)  # Alta penalización
    elif weather.condition == 'heavy_rain' and tyre_choice != 'extreme_wet':
        time_penalty += random.uniform(5.0, 10.0) # Penalización muy alta
    
    # Variabilidad por condiciones
    if weather.condition != 'dry':
        variability = random.uniform(-1.0, 3.0)
        time_penalty += variability
    
    return round(base_time + time_penalty, 3)
    
@app.route('/qualifying_results/<int:race_id>')
@login_required
def qualifying_results(race_id):
    """Página de resultados de clasificación"""
    race = Race.query.get_or_404(race_id)
    results = QualifyingSession.query.filter_by(race_id=race_id).order_by(
        QualifyingSession.final_position.asc()
    ).all()
    
    return render_template('qualifying_results.html', 
                         race=race, 
                         results=results)

# Añadir después de las rutas existentes en app.py

@app.route('/live_session/<int:race_id>/<session_type>')
@login_required
def live_session(race_id, session_type):
    """Página unificada de transmisión en vivo para quali y carrera"""
    race = Race.query.get_or_404(race_id)
    now = datetime.utcnow()
    
    # Determinar estado
    session_time = None
    if session_type == 'qualifying':
        session_time = race.qualifying_session
    elif session_type == 'race':
        session_time = race.race_session
    
    session_status = "upcoming"
    if session_time:
        time_diff = (session_time.replace(tzinfo=None) - now.replace(tzinfo=None)).total_seconds()
        if time_diff <= 600 and time_diff > -3600:  # 10 min antes hasta 1 hora después
            session_status = "live"
        elif time_diff <= -3600:
            session_status = "replay"
    
    return render_template('live_session.html',
                         race=race,
                         session_type=session_type,
                         session_status=session_status,
                         session_time=session_time)

@app.route('/api/live_session_events/<int:race_id>/<session_type>')
@login_required
def live_session_events(race_id, session_type):
    """API para eventos de transmisión en vivo - FILTRADO PRECISO POR EVENT_TYPE"""
    try:
        print(f"DEBUG: Iniciando API para race_id={race_id}, session_type={session_type}")
        
        # Filtrar eventos por event_type según la sesión con filtros más precisos
        if session_type == 'qualifying':
            # Solo eventos que empiecen con 'qualifying_' en event_type
            all_events = LiveEvent.query.filter(
                LiveEvent.race_id == race_id,
                LiveEvent.event_type.like('qualifying_%')
            ).order_by(LiveEvent.created_at.desc()).limit(50).all()
        elif session_type == 'race':
            # Solo eventos que empiecen con 'race_' en event_type
            all_events = LiveEvent.query.filter(
                LiveEvent.race_id == race_id,
                LiveEvent.event_type.like('race_%')
            ).order_by(LiveEvent.created_at.desc()).limit(50).all()
        else:
            # Para otros tipos de sesión, devolver vacío
            all_events = []
        
        print(f"DEBUG: Consulta completada, {len(all_events)} eventos de {session_type} encontrados")
        
        # Si no hay eventos, retornar vacío inmediatamente
        if not all_events:
            print("DEBUG: No hay eventos, retornando []")
            return jsonify([])
        
        # Procesar eventos
        events_data = []
        for event in all_events:
            # Obtener nombre del piloto de forma segura
            driver_name = "Piloto"
            if event.driver_id and event.driver_id > 0:
                driver = Driver.query.get(event.driver_id)
                if driver:
                    driver_name = driver.name
            
            events_data.append({
                'type': event.event_type or 'unknown',
                'title': get_safe_event_title(event.event_type, driver_name),
                'description': event.description or 'Sin descripción',
                'lap': event.lap or 0,
                'timestamp': event.created_at.isoformat() if event.created_at else datetime.utcnow().isoformat(),
                'driver_name': driver_name
            })
        
        print(f"DEBUG: Procesamiento completado. {len(events_data)} eventos listos")
        return jsonify(events_data)
            
    except Exception as e:
        print(f"ERROR: Error general en la API: {str(e)}")
        import traceback
        print("DEBUG - TRACEBACK:")
        traceback.print_exc()
        return jsonify([])


def get_safe_event_title(event_type, driver_name="Piloto"):
    """Títulos de eventos seguros"""
    if not event_type:
        return "Evento"
    
    safe_driver_name = str(driver_name)[:50]
    
    titles = {
        # Eventos de qualifying
        'qualifying_start': 'Inicio de clasificación',
        'qualifying_end': 'Final de clasificación', 
        'qualifying_fast_lap': f'{safe_driver_name} marca vuelta rápida',
        'qualifying_incident': f'Incidente de {safe_driver_name}',
        'qualifying_spin': f'{safe_driver_name} da un trompo',
        'qualifying_eliminated': f'{safe_driver_name} eliminado',
        'qualifying_pole': f'{safe_driver_name} consigue la POLE!',
        
        # Eventos de race
        'race_start': 'INICIO DE CARRERA',
        'race_finish': f'{safe_driver_name} finaliza',
        'race_overtake': f'{safe_driver_name} adelanta',
        'race_pit_stop': f'{safe_driver_name} entra a boxes',
        'race_spin': f'{safe_driver_name} da un trompo',
        'race_fast_lap': f'{safe_driver_name} vuelta rápida',
        'race_dnf': f'{safe_driver_name} ABANDONA',
        'race_safety_car': 'SAFETY CAR',
        'race_virtual_safety_car': 'VIRTUAL SAFETY CAR',
    }
    
    return titles.get(event_type, f'Evento: {event_type}')
    
@app.route('/debug/events/<int:race_id>')
@login_required
def debug_events(race_id):
    """Diagnóstico de eventos en la base de datos"""
    events = LiveEvent.query.filter_by(race_id=race_id).all()
    
    diagnostic = {
        'total_events': len(events),
        'events': []
    }
    
    for event in events:
        diagnostic['events'].append({
            'id': event.id,
            'event_type': event.event_type,
            'driver_id': event.driver_id,
            'team_id': event.team_id,
            'lap': event.lap,
            'description': event.description,
            'created_at': event.created_at.isoformat() if event.created_at else None
        })
    
    return jsonify(diagnostic)

@app.route('/api/simulate_qualifying_live/<int:race_id>')
@login_required
def simulate_qualifying_live(race_id):
    """Inicia la simulación de clasificación en segundo plano"""
    try:
        race = Race.query.get(race_id)
        if not race:
            return jsonify({'success': False, 'message': 'Carrera no encontrada'})
        
        # INICIAR SIMULACIÓN EN SEGUNDO PLANO
        import threading
        thread = threading.Thread(
            target=run_qualifying_simulation, 
            args=(race_id, current_user.id)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': '🏁 Simulación de clasificación iniciada en segundo plano',
            'redirect_url': url_for('live_session', race_id=race_id, session_type='qualifying')
        })
        
    except Exception as e:
        print(f"ERROR iniciando simulación: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

def run_qualifying_simulation(race_id, user_id):
    """Ejecuta la simulación de clasificación en segundo plano"""
    with app.app_context():
        try:
            print(f"=== INICIANDO SIMULACIÓN EN SEGUNDO PLANO PARA CARRERA {race_id} ===")
            
            race = Race.query.get(race_id)
            if not race:
                print("ERROR: Carrera no encontrada")
                return
            
            # LIMPIAR SOLO EVENTOS DE QUALIFYING anteriores
            LiveEvent.query.filter_by(race_id=race_id, session_type='qualifying').delete()
            
            # Obtener TODOS los equipos registrados que tengan pilotos
            all_teams = User.query.filter(User.drivers.any()).all()
            print(f"DEBUG: Equipos encontrados: {len(all_teams)}")
            
            # Crear o verificar elecciones de neumáticos para TODOS los pilotos
            qualifying_choices = []
            for team in all_teams:
                for driver in team.drivers:
                    # Verificar si ya existe elección
                    existing_choice = QualifyingSession.query.filter_by(
                        race_id=race_id,
                        team_id=team.id,
                        driver_id=driver.id
                    ).first()
                    
                    if existing_choice:
                        qualifying_choices.append(existing_choice)
                        print(f"DEBUG: Elección existente - {driver.name}: {existing_choice.tyre_choice}")
                    else:
                        # Crear elección automática
                        tyre_choice = random.choice(['soft', 'medium', 'hard'])
                        new_choice = QualifyingSession(
                            race_id=race_id,
                            team_id=team.id,
                            driver_id=driver.id,
                            tyre_choice=tyre_choice
                        )
                        db.session.add(new_choice)
                        qualifying_choices.append(new_choice)
                        print(f"DEBUG: Nueva elección - {driver.name}: {tyre_choice}")
            
            db.session.commit()
            print(f"DEBUG: Total elecciones preparadas: {len(qualifying_choices)}")
            
            # EVENTO DE INICIO DE QUALIFYING
            start_event = LiveEvent(
                race_id=race_id,
                team_id=0,
                driver_id=0,
                lap=0,
                event_type='qualifying_start',
                description='🏁 SESIÓN DE CLASIFICACIÓN INICIADA - TODOS LOS PILOTOS EN PISTA!',
                session_type='qualifying'
            )
            db.session.add(start_event)
            db.session.commit()
            
            # SIMULAR Q1, Q2, Q3 CON EL MOTOR MEJORADO
            final_results = simulate_qualifying_with_engine(qualifying_choices, race_id)
            
            # GUARDAR RESULTADOS EN LA BASE DE DATOS
            for i, result in enumerate(final_results):
                qualifying = QualifyingSession.query.filter_by(
                    race_id=race_id,
                    team_id=result['team_id'],
                    driver_id=result['driver_id']
                ).first()
                
                if qualifying:
                    qualifying.q1_time = result.get('q1_time')
                    qualifying.q2_time = result.get('q2_time')
                    qualifying.q3_time = result.get('q3_time')
                    qualifying.final_position = i + 1
            
            # EVENTO FINAL DE QUALIFYING CON POLE
            if final_results:
                pole_winner = final_results[0]
                pole_event = LiveEvent(
                    race_id=race_id,
                    team_id=pole_winner['team_id'],
                    driver_id=pole_winner['driver_id'],
                    lap=0,
                    event_type='qualifying_pole',
                    description=f'🏆 {pole_winner["driver_name"]} CONSIGUE LA POLE POSITION! - {pole_winner.get("q3_time", pole_winner.get("q2_time", pole_winner.get("q1_time", 0))):.3f}s',
                    session_type='qualifying'
                )
                db.session.add(pole_event)
            
            db.session.commit()
            print(f"✅ Simulación completada para carrera {race_id}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ ERROR en simulación en segundo plano: {str(e)}")
            import traceback
            traceback.print_exc()

def simulate_qualifying_with_engine(qualifying_choices, race_id):
    """Simula clasificación con componentes del coche - VERSIÓN MEJORADA"""
    import random
    
    print(f"DEBUG: Simulando clasificación MEJORADA para {len(qualifying_choices)} pilotos")
    
    # LIMPIAR EVENTOS ANTERIORES DE QUALIFYING
    LiveEvent.query.filter_by(race_id=race_id, session_type='qualifying').delete()
    
    # EVENTO DE INICIO
    start_event = LiveEvent(
        race_id=race_id,
        team_id=0,
        driver_id=0,
        lap=0,
        event_type='qualifying_start',
        description='🏁 INICIO DE CLASIFICACIÓN - Q1 COMIENZA!',
        session_type='qualifying'
    )
    db.session.add(start_event)
    db.session.commit()
    
    # SIMULAR Q1 - TODOS LOS PILOTOS CON COMPONENTES
    print("=== Q1 INICIADO (CON COMPONENTES) ===")
    q1_results = []
    
    for choice in qualifying_choices:
        # OBTENER COMPONENTES DEL COCHE
        car_components = CarComponent.query.filter_by(
            team_id=choice.team_id
        ).all()
        
        # CALCULAR RENDIMIENTO DEL COCHE
        car_performance = calculate_car_performance(car_components)
        
        # CALCULAR TIEMPO BASE CON COMPONENTES
        base_time = calculate_qualifying_base_time(choice.tyre_choice)
        
        # EFECTO DEL PILOTO (más fuerte en clasificación)
        driver_effect = (100 - choice.driver.skill) / 80
        
        # EFECTO DEL COCHE (strength afecta directamente)
        car_effect = (car_performance['strength'] - 50) * -0.015  # Efecto amplificado en clasificación
        
        # VARIABILIDAD REDUCIDA EN CLASIFICACIÓN
        consistency_variation = (100 - choice.driver.consistency) / 300
        random_variation = (random.random() - 0.5) * 0.8
        
        # CÁLCULO FINAL
        q1_time = base_time - driver_effect - car_effect + consistency_variation + random_variation
        
        q1_results.append({
            'team_id': choice.team_id,
            'driver_id': choice.driver_id,
            'driver_name': choice.driver.name,
            'team_name': choice.team.team_name,
            'tyre_choice': choice.tyre_choice,
            'q1_time': q1_time,
            'driver_skill': choice.driver.skill,
            'car_performance': car_performance,
            'car_components': [comp.component_type for comp in car_components]
        })
        
        # EVENTO DE VUELTA RÁPIDA OCASIONAL
        if random.random() < 0.3:  # 30% de probabilidad de evento por piloto
            event = LiveEvent(
                race_id=race_id,
                team_id=choice.team_id,
                driver_id=choice.driver_id,
                lap=1,
                event_type='qualifying_fast_lap',
                description=f'🚀 {choice.driver.name} marca {q1_time:.3f}s en Q1',
                session_type='qualifying'
            )
            db.session.add(event)
    
    db.session.commit()
    
    # Ordenar Q1 y eliminar los más lentos
    q1_results.sort(key=lambda x: x['q1_time'])
    q2_participants = q1_results[:15] if len(q1_results) > 15 else q1_results
    eliminated_q1 = q1_results[15:] if len(q1_results) > 15 else []
    
    # Evento de eliminación Q1
    if eliminated_q1:
        elimination_event = LiveEvent(
            race_id=race_id,
            team_id=0,
            driver_id=0,
            lap=1,
            event_type='qualifying_end',
            description=f'🏁 Q1 FINALIZADO - {len(eliminated_q1)} pilotos eliminados',
            session_type='qualifying'
        )
        db.session.add(elimination_event)
    
    # SIMULAR Q2 - TOP 15
    print("=== Q2 INICIADO (CON COMPONENTES) ===")
    q2_results = []
    
    for participant in q2_participants:
        # MEJORA EN Q2 (pilotos presionan más)
        q2_improvement = random.uniform(0.3, 1.0)
        q2_time = participant['q1_time'] - q2_improvement
        q2_time = max(74.0, q2_time)
        participant['q2_time'] = q2_time
        q2_results.append(participant)
        
        # EVENTO DE MEJORA
        if random.random() < 0.4:
            event = LiveEvent(
                race_id=race_id,
                team_id=participant['team_id'],
                driver_id=participant['driver_id'],
                lap=2,
                event_type='qualifying_fast_lap',
                description=f'💨 {participant["driver_name"]} mejora a {q2_time:.3f}s en Q2',
                session_type='qualifying'
            )
            db.session.add(event)
    
    # Ordenar Q2 y eliminar los más lentos
    q2_results.sort(key=lambda x: x['q2_time'])
    q3_participants = q2_results[:10] if len(q2_results) > 10 else q2_results
    eliminated_q2 = q2_results[10:] if len(q2_results) > 10 else []
    
    # Evento final Q2
    if eliminated_q2:
        q2_end = LiveEvent(
            race_id=race_id,
            team_id=0,
            driver_id=0,
            lap=2,
            event_type='qualifying_end',
            description=f'🏁 Q2 FINALIZADO - {len(eliminated_q2)} pilotos eliminados',
            session_type='qualifying'
        )
        db.session.add(q2_end)
    
    # SIMULAR Q3 - TOP 10 (SHOOTOUT)
    print("=== Q3 INICIADO (CON COMPONENTES) ===")
    q3_results = []
    
    for participant in q3_participants:
        # MEJORA EN Q3 (máximo esfuerzo)
        q3_improvement = random.uniform(0.5, 1.5)
        q3_time = participant['q2_time'] - q3_improvement
        q3_time = max(73.0, q3_time)
        participant['q3_time'] = q3_time
        q3_results.append(participant)
        
        # EVENTO DE VUELTA DEFINITIVA
        event = LiveEvent(
            race_id=race_id,
            team_id=participant['team_id'],
            driver_id=participant['driver_id'],
            lap=3,
            event_type='qualifying_fast_lap',
            description=f'🏎️ {participant["driver_name"]} marca {q3_time:.3f}s en Q3!',
            session_type='qualifying'
        )
        db.session.add(event)
    
    # Ordenar Q3 para determinar pole
    q3_results.sort(key=lambda x: x['q3_time'])
    pole_winner = q3_results[0] if q3_results else None
    
    # Evento final CON pole
    if q3_results:
        final_event = LiveEvent(
            race_id=race_id,
            team_id=0,
            driver_id=0,
            lap=3,
            event_type='qualifying_end',
            description=f'🏁 CLASIFICACIÓN FINALIZADA - {pole_winner["driver_name"]} consigue la POLE POSITION con {pole_winner.get("q3_time", 0):.3f}s!',
            session_type='qualifying'
        )
        db.session.add(final_event)
    
    db.session.commit()
    
    print(f"DEBUG: Clasificación MEJORADA completada - Pole: {pole_winner['driver_name'] if pole_winner else 'N/A'}")
    
    # COMBINAR TODOS LOS RESULTADOS FINALES
    final_results = q3_results + eliminated_q2 + eliminated_q1
    
    # ASIGNAR POSICIONES FINALES
    for i, result in enumerate(final_results):
        result['final_position'] = i + 1
    
    return final_results

def calculate_qualifying_base_time(tyre_choice):
    """Calcula tiempo base para clasificación según neumático"""
    base_times = {
        'soft': 75.0,
        'medium': 76.5, 
        'hard': 78.0,
        'wet': 82.0,
        'extreme_wet': 85.0
    }
    return base_times.get(tyre_choice, 76.0)

def calculate_car_performance(car_components):
    """Calcula el rendimiento general del coche basado en componentes"""
    if not car_components:
        return {'strength': 50, 'reliability': 50}
    
    total_strength = sum(comp.strength for comp in car_components)
    total_reliability = sum(comp.reliability for comp in car_components)
    component_count = len(car_components)
    
    return {
        'strength': total_strength / component_count,
        'reliability': total_reliability / component_count
    }

@app.route('/api/race_results/<int:race_id>')
@login_required
def api_race_results(race_id):
    """API para obtener resultados de carrera"""
    try:
        print(f"DEBUG: Solicitando resultados de carrera para carrera {race_id}")
        
        # Obtener resultados de carrera ordenados por posición
        results = ChampionshipStandings.query.filter_by(race_id=race_id).join(
            Driver, ChampionshipStandings.driver_id == Driver.id
        ).join(
            User, ChampionshipStandings.team_id == User.id
        ).order_by(
            ChampionshipStandings.position.asc()
        ).all()
        
        print(f"DEBUG: Encontrados {len(results)} resultados de carrera")
        
        results_data = []
        for result in results:
            results_data.append({
                'driver_name': result.driver.name,
                'team_name': result.team.team_name,
                'position': result.position,
                'points': result.points,
                'fastest_lap': result.fastest_lap,
                'dnf': result.dnf,
                'status': 'DNF' if result.dnf else 'Finished'
            })
            print(f"DEBUG - Resultado carrera: {result.driver.name}, Pos: {result.position}, Puntos: {result.points}")
        
        return jsonify(results_data)
        
    except Exception as e:
        print(f"Error en api_race_results: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify([])

@app.route('/api/simulate_race_live/<int:race_id>')
@login_required
def simulate_race_live(race_id):
    """Simula carrera usando el motor de simulacion mejorado CON PROBABILIDADES DEL RACE_ENGINE Y ESTRATEGIAS"""
    try:
        race = Race.query.get(race_id)
        if not race:
            return jsonify({'success': False, 'message': 'Carrera no encontrada'})
        
        print(f"=== INICIANDO SIMULACION DE CARRERA CON ESTRATEGIAS PARA CARRERA {race_id} ===")
        
        # Limpiar SOLO eventos de carrera anteriores
        LiveEvent.query.filter_by(race_id=race_id, session_type='race').delete()
        
        # Obtener parrilla de salida desde qualifying
        qualifying_results = QualifyingSession.query.filter_by(
            race_id=race_id
        ).order_by(QualifyingSession.final_position.asc()).all()
        
        if not qualifying_results:
            return jsonify({'success': False, 'message': 'No hay resultados de clasificacion para esta carrera'})
        
        # Obtener pronóstico meteorológico para la carrera
        race_weather = WeatherForecast.query.filter_by(
            race_id=race_id, 
            session_type='race'
        ).first()
        
        # EVENTO DE INICIO DE CARRERA
        start_event = LiveEvent(
            race_id=race_id,
            team_id=0,
            driver_id=0,
            lap=0,
            event_type='race_start',
            description='INICIA EL GRAN PREMIO!',
            session_type='race'
        )
        db.session.add(start_event)
        db.session.commit()
        
        # SIMULAR CARRERA CON ESTRATEGIAS Y NEUMÁTICOS POR DEFECTO
        race_results = simulate_race_with_strategies(race_id, qualifying_results, race.circuit.laps, race_weather)
        
        # GUARDAR RESULTADOS EN LA BASE DE DATOS
        save_race_results_improved(race_id, race_results)
        
        # EVENTO DE FINAL DE CARRERA - SOLO SI HAY GANADOR
        finished_cars = [car for car in race_results if not car['dnf']]  # Solo los que terminaron
        if finished_cars:
            winner = finished_cars[0]  # El primero de los que terminaron
            finish_event = LiveEvent(
                race_id=race_id,
                team_id=winner['team_id'],
                driver_id=winner['driver_id'],
                lap=race.circuit.laps,
                event_type='race_finish',
                description=f'BANDERAS A CUADROS! {winner["driver_name"]} GANA EL GRAN PREMIO!',
                session_type='race'
            )
            db.session.add(finish_event)
        else:
            # Si todos abandonaron
            finish_event = LiveEvent(
                race_id=race_id,
                team_id=0,
                driver_id=0,
                lap=race.circuit.laps,
                event_type='race_finish',
                description='BANDERAS A CUADROS! TODOS LOS PILOTOS ABANDONARON!',
                session_type='race'
            )
            db.session.add(finish_event)
        
        db.session.commit()
        
        # Determinar mensaje final
        if finished_cars:
            winner_name = finished_cars[0]["driver_name"]
            message = f'Carrera simulada - {winner_name} gana!'
        else:
            message = 'Carrera simulada - Todos los pilotos abandonaron!'
        
        return jsonify({
            'success': True,
            'message': message,
            'winner': finished_cars[0]["driver_name"] if finished_cars else None,
            'events_generated': LiveEvent.query.filter_by(race_id=race_id, session_type='race').count(),
            'laps': race.circuit.laps,
            'redirect_url': url_for('live_session', race_id=race_id, session_type='race')
        })
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_trace = traceback.format_exc()
        # Limpiar caracteres problematicos del traceback
        error_trace = error_trace.encode('ascii', 'ignore').decode('ascii')
        print(f"ERROR en simulate_race_live: {str(e)}")
        print(error_trace)
        return jsonify({'success': False, 'message': f'Error en la simulacion: {str(e)}'})

def simulate_race_with_strategies(race_id, qualifying_results, total_laps, race_weather):
    """Simula carrera usando estrategias definidas o neumáticos por defecto según condiciones"""
    import random
    import time
    
    print(f"DEBUG: Simulando carrera con ESTRATEGIAS para {len(qualifying_results)} pilotos, {total_laps} vueltas")
    
    # Determinar condición climática base
    weather_condition = race_weather.condition if race_weather else 'dry'
    print(f"DEBUG: Condición climática: {weather_condition}")
    
    # Crear lista de coches en parrilla de salida
    cars = []
    for i, qualifying in enumerate(qualifying_results):
        # Obtener componentes del coche
        car_components = []
        for component in qualifying.team.car_components:
            car_components.append({
                'component_type': component.component_type,
                'strength': component.strength,
                'reliability': component.reliability
            })
        
        # Obtener estrategia definida para este piloto
        strategy = RaceStrategy.query.filter_by(
            race_id=race_id,
            driver_id=qualifying.driver_id,
            team_id=qualifying.team_id
        ).first()
        
        # Determinar neumático inicial según estrategia o condiciones climáticas
        if strategy and strategy.segments:
            # Usar estrategia definida - primer segmento define neumático de salida
            starting_tyre = strategy.starting_tyre
            strategy_segments = sorted(strategy.segments, key=lambda x: x.segment_order)
            has_strategy = True
        else:
            # Sin estrategia definida - usar neumáticos por defecto según condiciones
            if weather_condition == 'dry':
                starting_tyre = 'hard'
            elif weather_condition == 'light_rain':
                starting_tyre = 'wet'
            else:  # heavy_rain
                starting_tyre = 'extreme_wet'
            strategy_segments = []
            has_strategy = False
        
        car_data = {
            'qualifying': qualifying,
            'driver_id': qualifying.driver_id,
            'driver_name': qualifying.driver.name,
            'team_id': qualifying.team_id,
            'team_name': qualifying.team.team_name,
            'current_tyre': starting_tyre,
            'current_position': i + 1,
            'grid_position': i + 1,
            'lap_times': [],
            'pit_stops': 0,
            'car_components': car_components,
            'incidents': 0,
            'mechanical_failures': 0,
            'dnf': False,
            'dnf_reason': None,
            'total_time': 0,
            'driver_skill': qualifying.driver.skill,
            'driver_consistency': qualifying.driver.consistency,
            'last_pit_lap': 0,
            'tyre_wear': 0,
            'finished': False,
            'has_strategy': has_strategy,
            'strategy': strategy,
            'strategy_segments': strategy_segments,
            'current_segment': 0,  # Índice del segmento actual
            'segment_laps_completed': 0,  # Vueltas completadas en el segmento actual
            'weather_condition': weather_condition,
            'rain_strategy': strategy.rain_strategy if strategy else 'continue',
            'heavy_rain_strategy': strategy.heavy_rain_strategy if strategy else 'continue',
            'dry_strategy': strategy.dry_strategy if strategy else 'continue'
        }
        cars.append(car_data)
    
    # EVENTO DE INICIO
    start_event = LiveEvent(
        race_id=race_id,
        team_id=0,
        driver_id=0,
        lap=1,
        event_type='race_start',
        description='LUCES VERDES! LA CARRERA ESTA EN MARCHA!',
        session_type='race'
    )
    db.session.add(start_event)
    db.session.commit()
    
    # SIMULAR VUELTA POR VUELTA
    for lap in range(1, total_laps + 1):
        print(f"DEBUG: Vuelta {lap}/{total_laps}")
        
        # Ordenar coches por posicion actual (solo los que no han abandonado)
        active_cars = [car for car in cars if not car['dnf']]
        active_cars.sort(key=lambda x: x['current_position'])
        
        # Actualizar posiciones de los coches activos
        for i, car in enumerate(active_cars):
            car['current_position'] = i + 1
        
        # Simular eventos de vuelta (solo si hay coches activos)
        if lap > 1 and active_cars:
            simulate_lap_events_simple(race_id, active_cars, lap, total_laps)
        
        # VERIFICAR FALLAS MECANICAS CON RACE_ENGINE
        for car in active_cars:
            check_mechanical_failure(race_id, car, lap, total_laps, cars)
        
        # GESTIONAR ESTRATEGIAS Y CAMBIOS DE NEUMÁTICOS
        manage_race_strategies(race_id, active_cars, lap, total_laps, weather_condition)
        
        # Actualizar rendimiento (solo coches activos)
        update_car_performance_simple(active_cars, lap)
        
        # Simular adelantamientos basicos (solo coches activos)
        simulate_overtakes_simple(race_id, active_cars, lap)
        
        # Verificar paradas por desgaste (solo coches activos)
        check_tyre_wear_pit_stops(race_id, active_cars, lap)
        
        # Marcar coches que terminan la carrera
        if lap == total_laps:
            for car in active_cars:
                car['finished'] = True
                print(f"TERMINO: {car['driver_name']} completa la carrera en posicion {car['current_position']}")
        
        # Pequena pausa
        time.sleep(0.05)
        
        # Si no quedan coches activos, terminar la carrera anticipadamente
        if not active_cars:
            print("CARRERA TERMINADA ANTICIPADAMENTE - TODOS ABANDONARON")
            break
    
    # CALCULAR RESULTADOS FINALES
    finished_cars = [car for car in cars if car['finished']]  # Solo los que terminaron
    dnf_cars = [car for car in cars if car['dnf']]  # Los que abandonaron
    
    # Ordenar por tiempo total (solo los que terminaron)
    finished_cars.sort(key=lambda x: x['total_time'])
    
    # Asignar posiciones finales
    final_results = finished_cars + dnf_cars
    for i, car in enumerate(final_results):
        car['final_position'] = i + 1
        if car['finished']:  # Solo dar puntos a los que terminaron
            points_system = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
            car['points'] = points_system.get(i + 1, 0)
            # Vuelta rapida para el ganador (70% probabilidad)
            if i == 0 and random.random() < 0.7:
                car['fastest_lap'] = True
                car['points'] += 1
            else:
                car['fastest_lap'] = False
        else:
            car['points'] = 0
            car['fastest_lap'] = False
    
    print(f"DEBUG: Simulacion completada - {len(finished_cars)} terminaron, {len(dnf_cars)} abandonos")
    
    return final_results

def manage_race_strategies(race_id, active_cars, current_lap, total_laps, current_weather):
    """Gestiona las estrategias de carrera y cambios de neumáticos"""
    for car in active_cars:
        if car['dnf']:
            continue
            
        # Incrementar contador de vueltas en segmento actual
        car['segment_laps_completed'] += 1
        
        # VERIFICAR CAMBIOS CLIMÁTICOS Y APLICAR ESTRATEGIAS
        check_weather_changes_strategy(race_id, car, current_lap, current_weather)
        
        # VERIFICAR FIN DE SEGMENTO DE ESTRATEGIA
        if car['has_strategy'] and car['strategy_segments']:
            current_segment_idx = car['current_segment']
            current_segment = car['strategy_segments'][current_segment_idx]
            planned_laps = current_segment.laps_planned
            
            # Si hemos completado las vueltas planificadas para este segmento
            if car['segment_laps_completed'] >= planned_laps and current_segment_idx < len(car['strategy_segments']) - 1:
                # Cambiar al siguiente segmento
                next_segment_idx = current_segment_idx + 1
                next_segment = car['strategy_segments'][next_segment_idx]
                
                # Realizar parada para cambio de neumáticos
                execute_strategy_pit_stop(race_id, car, current_lap, 
                                        current_segment.tyre_type, 
                                        next_segment.tyre_type,
                                        f"Estrategia programada: {current_segment.tyre_type} -> {next_segment.tyre_type}")
                
                # Actualizar contadores de segmento
                car['current_segment'] = next_segment_idx
                car['segment_laps_completed'] = 0
        
        # PARA COCHES SIN ESTRATEGIA: Verificar desgaste extremo y cambiar según condiciones
        elif not car['has_strategy'] and car['tyre_wear'] > 85:
            # Cambio por desgaste - usar neumático por defecto según condiciones
            if current_weather == 'dry':
                new_tyre = 'hard'
            elif current_weather == 'light_rain':
                new_tyre = 'wet'
            else:  # heavy_rain
                new_tyre = 'extreme_wet'
            
            if new_tyre != car['current_tyre']:
                execute_strategy_pit_stop(race_id, car, current_lap, 
                                        car['current_tyre'], new_tyre,
                                        f"Cambio por desgaste: {car['current_tyre']} -> {new_tyre}")

def check_weather_changes_strategy(race_id, car, current_lap, current_weather):
    """Verifica cambios climáticos y aplica estrategias correspondientes"""
    # Simular cambio climático aleatorio (en una implementación real, usarías WeatherChange)
    weather_change_prob = 0.02  # 2% de probabilidad por vuelta de cambio climático
    
    if random.random() < weather_change_prob:
        new_weather = random.choice(['dry', 'light_rain', 'heavy_rain'])
        if new_weather != current_weather:
            # Aplicar estrategia según el cambio climático
            apply_weather_change_strategy(race_id, car, current_lap, current_weather, new_weather)

def apply_weather_change_strategy(race_id, car, current_lap, old_weather, new_weather):
    """Aplica la estrategia definida para cambios climáticos"""
    
    # Determinar neumático apropiado para la nueva condición
    appropriate_tyre = get_appropriate_tyre_for_weather(new_weather)
    
    # Verificar si el neumático actual es apropiado
    current_tyre_appropriate = is_tyre_appropriate_for_weather(car['current_tyre'], new_weather)
    
    if not current_tyre_appropriate:
        # El neumático actual no es apropiado - aplicar estrategia
        strategy_to_apply = None
        
        if new_weather == 'light_rain':
            strategy_to_apply = car['rain_strategy']
        elif new_weather == 'heavy_rain':
            strategy_to_apply = car['heavy_rain_strategy']
        elif new_weather == 'dry':
            strategy_to_apply = car['dry_strategy']
        
        # Ejecutar la estrategia
        if strategy_to_apply == 'pit_wet' and new_weather == 'light_rain':
            execute_strategy_pit_stop(race_id, car, current_lap, 
                                    car['current_tyre'], 'wet',
                                    f"Cambio por lluvia: {car['current_tyre']} -> Wet")
        
        elif strategy_to_apply == 'pit_extreme' and new_weather in ['light_rain', 'heavy_rain']:
            execute_strategy_pit_stop(race_id, car, current_lap, 
                                    car['current_tyre'], 'extreme_wet',
                                    f"Cambio por lluvia intensa: {car['current_tyre']} -> Extreme Wet")
        
        elif strategy_to_apply == 'immediate_pit':
            execute_strategy_pit_stop(race_id, car, current_lap, 
                                    car['current_tyre'], appropriate_tyre,
                                    f"Boxes inmediato: {car['current_tyre']} -> {appropriate_tyre}")
        
        elif strategy_to_apply in ['pit_soft', 'pit_medium'] and new_weather == 'dry':
            new_tyre = 'soft' if strategy_to_apply == 'pit_soft' else 'medium'
            execute_strategy_pit_stop(race_id, car, current_lap, 
                                    car['current_tyre'], new_tyre,
                                    f"Cambio a seco: {car['current_tyre']} -> {new_tyre}")
        
        # Para 'continue' o 'next_pit', no hacer nada - esperar parada programada

def get_appropriate_tyre_for_weather(weather):
    """Devuelve el neumático apropiado para las condiciones climáticas"""
    if weather == 'dry':
        return 'hard'  # Por defecto para coches sin estrategia
    elif weather == 'light_rain':
        return 'wet'
    else:  # heavy_rain
        return 'extreme_wet'

def is_tyre_appropriate_for_weather(tyre, weather):
    """Verifica si un neumático es apropiado para las condiciones climáticas"""
    if weather == 'dry':
        return tyre in ['soft', 'medium', 'hard']
    elif weather == 'light_rain':
        return tyre in ['wet', 'extreme_wet']
    else:  # heavy_rain
        return tyre == 'extreme_wet'

def execute_strategy_pit_stop(race_id, car, lap, old_tyre, new_tyre, reason):
    """Ejecuta una parada en boxes por estrategia"""
    pit_time = 2.5 + random.uniform(0, 1.0)
    car['pit_stops'] += 1
    car['last_pit_lap'] = lap
    car['tyre_wear'] = 0
    car['current_tyre'] = new_tyre
    
    # Reemplazar caracteres Unicode problemáticos
    safe_reason = reason.replace('→', '->')
    
    event = LiveEvent(
        race_id=race_id,
        team_id=car['team_id'],
        driver_id=car['driver_id'],
        lap=lap,
        event_type='race_pit_stop',
        description=f'BOXES {car["driver_name"]} - {safe_reason} - {pit_time:.1f}s',
        session_type='race'
    )
    db.session.add(event)
    
    car['total_time'] += pit_time
    db.session.commit()
    
    print(f"STRATEGY: {car['driver_name']} - {safe_reason} en vuelta {lap}")
    
def check_mechanical_failure(race_id, car, current_lap, total_laps, cars):
    """Verifica fallas mecanicas - PROTECCIÓN CONTRA MÚLTIPLES ABANDONOS DEL MISMO EQUIPO"""
    from race_engine_bridge import RaceEngineBridge
    
    # Solo verificar si el coche no ha abandonado
    if car['dnf']:
        return
    
    # CONTAR cuántos coches del mismo equipo ya abandonaron
    team_abandoned_count = sum(1 for c in cars if c['team_id'] == car['team_id'] and c['dnf'])
    
    # Calcular riesgo base usando el motor
    base_risk = RaceEngineBridge.calculate_mechanical_failure_risk(
        car['car_components'],
        current_lap,
        total_laps,
        car['incidents']
    )
    
    # FACTOR SUERTE DEL PILOTO (habilidad y experiencia reducen riesgo)
    luck_factor = (car['driver_skill'] + car['driver_consistency']) / 200  # 0.5 a 1.0
    final_risk = base_risk * (1.3 - luck_factor)  # Pilotos buenos tienen menos riesgo
    
    # PROTECCIÓN: Reducir riesgo si ya hay abandonos en el mismo equipo
    if team_abandoned_count >= 1:
        final_risk *= 0.3  # 70% menos riesgo si ya hay un abandono en el equipo
    if team_abandoned_count >= 2:
        final_risk *= 0.1  # 90% menos riesgo si ya hay dos abandonos
    
    # PROTECCIÓN: Reducir riesgo si muchos coches ya abandonaron
    total_abandoned = sum(1 for c in cars if c['dnf'])
    if total_abandoned >= len(cars) // 2:  # Si la mitad o más abandonaron
        final_risk *= 0.2  # 80% menos riesgo
    
    # RIESGO MÍNIMO por vuelta (0.02%)
    final_risk = max(0.0002, final_risk)
    
    # Solo mostrar riesgo si es > 0.05%
    if final_risk > 0.0005:
        print(f"MECANICA {car['driver_name']} - Riesgo: {final_risk:.4f} en vuelta {current_lap}")
    
    # Verificar si ocurre falla (probabilidad muy baja)
    if random.random() < final_risk:
        failed_component = RaceEngineBridge.determine_failed_component(car['car_components'])
        car['dnf'] = True
        car['dnf_reason'] = f'FALLA MECANICA EN {failed_component.upper()}'
        car['mechanical_failures'] += 1
        
        # Crear evento de abandono
        event = LiveEvent(
            race_id=race_id,
            team_id=car['team_id'],
            driver_id=car['driver_id'],
            lap=current_lap,
            event_type='race_dnf',
            description=f'FALLA! {car["driver_name"]} ABANDONA! - {car["dnf_reason"]}',
            session_type='race'
        )
        db.session.add(event)
        db.session.commit()
        
        print(f"ABANDONO INUSUAL: {car['driver_name']} - {car['dnf_reason']}")

def check_tyre_wear_pit_stops(race_id, cars, lap):
    """Verifica paradas por desgaste de neumaticos"""
    for car in cars:
        if car['dnf'] or lap - car['last_pit_lap'] < 10:
            continue
            
        # Aumentar desgaste
        wear_increase = random.uniform(2, 6)
        car['tyre_wear'] += wear_increase
        
        # Parada si desgaste > 80%
        if car['tyre_wear'] > 80 and random.random() < 0.3:
            execute_pit_stop(race_id, car, lap)

def execute_pit_stop(race_id, car, lap):
    """Ejecuta una parada en boxes"""
    pit_time = 2.5 + random.uniform(0, 1.0)
    car['pit_stops'] += 1
    car['last_pit_lap'] = lap
    car['tyre_wear'] = 0
    
    # Elegir nuevo neumatico
    new_tyre = random.choice(['soft', 'medium', 'hard'])
    car['current_tyre'] = new_tyre
    
    event = LiveEvent(
        race_id=race_id,
        team_id=car['team_id'],
        driver_id=car['driver_id'],
        lap=lap,
        event_type='race_pit_stop',
        description=f'BOXES {car["driver_name"]} - Parada en boxes - {pit_time:.1f}s - Cambio a {new_tyre.upper()}',
        session_type='race'
    )
    db.session.add(event)
    
    car['total_time'] += pit_time
    db.session.commit()

def update_car_performance_simple(cars, lap):
    """Actualizacion simple del rendimiento"""
    for car in cars:
        if car['dnf']:
            continue
            
        # Tiempo base + efectos
        base_time = 80.0
        skill_effect = (100 - car['driver_skill']) * 0.04
        wear_penalty = car['tyre_wear'] * 0.08
        random_variation = random.uniform(-0.2, 0.2)
        
        lap_time = base_time + skill_effect + wear_penalty + random_variation
        car['lap_times'].append(lap_time)
        car['total_time'] += lap_time

def simulate_overtakes_simple(race_id, cars, lap):
    """Adelantamientos simples"""
    for i in range(len(cars) - 1):
        car_ahead = cars[i]
        car_behind = cars[i + 1]
        
        if car_ahead['dnf'] or car_behind['dnf']:
            continue
            
        # Probabilidad basada en diferencia de habilidad y desgaste
        skill_diff = (car_behind['driver_skill'] - car_ahead['driver_skill']) / 100
        tyre_advantage = (car_ahead['tyre_wear'] - car_behind['tyre_wear']) / 100
        overtake_chance = 0.05 + skill_diff * 0.1 + tyre_advantage * 0.15
        
        if random.random() < overtake_chance:
            # Intercambiar posiciones
            cars[i], cars[i + 1] = cars[i + 1], cars[i]
            
            event = LiveEvent(
                race_id=race_id,
                team_id=car_behind['team_id'],
                driver_id=car_behind['driver_id'],
                lap=lap,
                event_type='race_overtake',
                description=f'ADELANTAMIENTO {car_behind["driver_name"]} ADELANTA A {car_ahead["driver_name"]}',
                session_type='race'
            )
            db.session.add(event)
            db.session.commit()

def simulate_lap_events_simple(race_id, cars, lap, total_laps):
    """Eventos simples por vuelta"""
    import random
    
    # Solo un evento por vuelta para evitar spam
    if random.random() < 0.15 and cars:  # 15% de probabilidad por vuelta y hay coches activos
        car = random.choice(cars)
        
        event_types = [
            ('race_fast_lap', f'VUELTA RAPIDA {car["driver_name"]} MARCA VUELTA RAPIDA'),
            ('race_spin', f'TROMPO {car["driver_name"]} DA UN TROMPO PERO CONTINUA'),
            ('race_off_track', f'FUERA PISTA {car["driver_name"]} SE SALE DE LA PISTA')
        ]
        
        event_type, description = random.choice(event_types)
        
        event = LiveEvent(
            race_id=race_id,
            team_id=car['team_id'],
            driver_id=car['driver_id'],
            lap=lap,
            event_type=event_type,
            description=description,
            session_type='race'
        )
        db.session.add(event)
        
        if 'spin' in event_type or 'off_track' in event_type:
            car['incidents'] += 1
            # Pequena penalizacion de tiempo por incidente
            car['total_time'] += random.uniform(2, 5)
        
        db.session.commit()

def save_race_results_improved(race_id, race_results):
    """Guarda los resultados de la carrera en la base de datos - VERSION MEJORADA"""
    # Primero eliminar resultados anteriores de esta carrera para evitar duplicados
    ChampionshipStandings.query.filter_by(race_id=race_id).delete()
    RaceResult.query.filter_by(race_id=race_id).delete()
    
    for result in race_results:
        standing = ChampionshipStandings(
            team_id=result['team_id'],
            driver_id=result['driver_id'],
            race_id=race_id,
            points=result.get('points', 0),
            position=result['final_position'],
            fastest_lap=result.get('fastest_lap', False),
            dnf=result['dnf']
        )
        db.session.add(standing)
        
        # Tambien crear un RaceResult
        race_result = RaceResult(
            race_id=race_id,
            team_id=result['team_id'],
            driver_id=result['driver_id'],
            position=result['final_position'],
            points=result.get('points', 0),
            tyre_usage=result.get('pit_stops', 0),
            pit_stops=result.get('pit_stops', 0),
            fastest_lap=result.get('fastest_lap', False),
            dnf=result['dnf'],
            dnf_reason=result.get('dnf_reason')
        )
        db.session.add(race_result)
    
    db.session.commit()
    print(f"RESULTADOS GUARDADOS para carrera {race_id}: {len(race_results)} pilotos")

@app.route('/api/lap_times/qualifying/<int:race_id>')
@login_required
def api_qualifying_lap_times(race_id):
    """API para obtener tiempos por vuelta de clasificación"""
    try:
        # Obtener eventos de tiempos de vuelta específicos
        lap_time_events = LiveEvent.query.filter_by(
            race_id=race_id,
            session_type='qualifying',
            event_type='qualifying_lap_time'
        ).order_by(LiveEvent.created_at.desc()).limit(20).all()
        
        lap_times = []
        for event in lap_time_events:
            # Extraer datos del evento
            try:
                event_data = json.loads(event.description)
                lap_times.append({
                    'driver_id': event.driver_id,
                    'driver_name': event.driver.name if event.driver else "Piloto",
                    'driver_initials': ''.join([name[0] for name in event.driver.name.split()]) if event.driver else "P",
                    'team_name': event.team.team_name if event.team else "Equipo",
                    'lap_number': event.lap,
                    'lap_time': event_data.get('lap_time', 0),
                    'lap_type': event_data.get('lap_type', 'normal'),
                    'tyre_type': event_data.get('tyre_type', 'soft'),
                    'is_personal_best': event_data.get('is_personal_best', False),
                    'is_session_best': event_data.get('is_session_best', False),
                    'gap_to_leader': event_data.get('gap_to_leader', 0),
                    'gap_to_previous': event_data.get('gap_to_previous', 0),
                    'timestamp': event.created_at.isoformat()
                })
            except:
                continue
        
        # Ordenar por tiempo más rápido
        lap_times.sort(key=lambda x: x['lap_time'])
        
        return jsonify(lap_times)
        
    except Exception as e:
        print(f"Error en api_qualifying_lap_times: {str(e)}")
        return jsonify([])

@app.route('/api/lap_times/race/<int:race_id>')
@login_required
def api_race_lap_times(race_id):
    """API para obtener tiempos por vuelta de carrera"""
    try:
        # Obtener eventos de tiempos de vuelta específicos
        lap_time_events = LiveEvent.query.filter_by(
            race_id=race_id,
            session_type='race',
            event_type='race_lap_time'
        ).order_by(LiveEvent.created_at.desc()).limit(30).all()
        
        lap_times = []
        for event in lap_time_events:
            try:
                event_data = json.loads(event.description)
                lap_times.append({
                    'driver_id': event.driver_id,
                    'driver_name': event.driver.name if event.driver else "Piloto",
                    'driver_initials': ''.join([name[0] for name in event.driver.name.split()]) if event.driver else "P",
                    'team_name': event.team.team_name if event.team else "Equipo",
                    'lap_number': event.lap,
                    'lap_time': event_data.get('lap_time', 0),
                    'lap_type': event_data.get('lap_type', 'normal'),
                    'tyre_type': event_data.get('tyre_type', 'soft'),
                    'is_personal_best': event_data.get('is_personal_best', False),
                    'is_session_best': event_data.get('is_session_best', False),
                    'gap_to_leader': event_data.get('gap_to_leader', 0),
                    'gap_to_previous': event_data.get('gap_to_previous', 0),
                    'position': event_data.get('position', 1),
                    'timestamp': event.created_at.isoformat()
                })
            except:
                continue
        
        # Ordenar por posición en carrera
        lap_times.sort(key=lambda x: x.get('position', 1))
        
        return jsonify(lap_times[:20])  # Mostrar solo los primeros 20
        
    except Exception as e:
        print(f"Error en api_race_lap_times: {str(e)}")
        return jsonify([])

# Solo iniciar el scheduler si estamos ejecutando app.py directamente
if __name__ == '__main__':
    scheduler.start()
    app.run(debug=True)