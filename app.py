from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
import json
import random
import math
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# CONTEXT PROCESSOR PARA INYECTAR 'now' EN TODAS LAS PLANTILLAS
@app.context_processor
def inject_now():
    """Inyecta la fecha/hora actual en todas las plantillas"""
    return {'now': datetime.utcnow()}

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

@app.context_processor
def utility_processor():
    def get_tyre_badge_color(tyre_type):
        colors = {
            'soft': 'danger',
            'medium': 'warning', 
            'hard': 'secondary',
            'wet': 'info',
            'extreme_wet': 'primary'
        }
        return colors.get(tyre_type, 'primary')
    
    def get_tyre_display_name(tyre_type):
        names = {
            'soft': 'Blando',
            'medium': 'Medio',
            'hard': 'Duro',
            'wet': 'Lluvia',
            'extreme_wet': 'Lluvia Extrema'
        }
        return names.get(tyre_type, tyre_type)
    
    return {
        'get_tyre_badge_color': get_tyre_badge_color,
        'get_tyre_display_name': get_tyre_display_name
    }

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

# Tareas programadas
scheduler = BackgroundScheduler()

# Configurar las tareas programadas
scheduler.add_job(scheduled_training_completion, 'interval', hours=1)
scheduler.add_job(scheduled_upgrade_completion, 'interval', hours=1)
scheduler.add_job(scheduled_retirement_check, 'interval', hours=24) # Verificar jubilaciones cada 24 horas
scheduler.add_job(scheduled_aging_update, 'interval', days=30)

def simulate_scheduled_races():
    with app.app_context():
        now = datetime.utcnow()
        upcoming_races = Race.query.filter(Race.race_session <= now).all()
        
        for race in upcoming_races:
            RaceSimulator.simulate_race(race.id)

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
    
    # Verificar que el circuito esté cargado
    if not race.circuit:
        return "Error: Circuito no encontrado para esta carrera", 500
        
    now = datetime.utcnow()
    return render_template('race.html', race=race, now=now)

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

@app.route('/live_race/<int:race_id>')
@login_required
def live_race(race_id):
    race = Race.query.get(race_id)
    return render_template('live_race.html', race=race)

@app.route('/api/live_events/<int:race_id>')
@login_required
def live_events(race_id):
    events = LiveEvent.query.filter_by(race_id=race_id).order_by(LiveEvent.created_at.desc()).limit(20).all()
    events_data = [{
        'description': event.description,
        'lap': event.lap,
        'type': event.event_type
    } for event in events]
    
    return jsonify(events_data)
    
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
                         
@app.route('/simulate_test', methods=['POST'])
@login_required
def simulate_test():
    """Simula una sesión de tests y guarda los resultados"""
    try:
        data = request.json
        
        # Validar datos
        required_fields = ['driver_id', 'tyre_type', 'total_laps', 'track_condition', 'race_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'message': f'Campo requerido faltante: {field}'})
        
        # Verificar que el piloto pertenece al equipo
        driver = Driver.query.filter_by(id=data['driver_id'], team_id=current_user.id).first()
        if not driver:
            return jsonify({'success': False, 'message': 'Piloto no válido'})
        
        # Crear sesión de test
        test_session = TestSession(
            team_id=current_user.id,
            driver_id=data['driver_id'],
            race_id=data['race_id']
        )
        db.session.add(test_session)
        db.session.flush()
        
        # Simular vueltas
        lap_results = simulate_test_laps(
            driver, 
            data['tyre_type'], 
            data['total_laps'], 
            data['track_condition']
        )
        
        # Guardar vueltas
        for lap_data in lap_results:
            test_lap = TestLap(
                test_session_id=test_session.id,
                lap_number=lap_data['lap_number'],
                tyre_type=lap_data['tyre_type'],
                lap_time=lap_data['lap_time'],
                tyre_wear=lap_data['tyre_wear'],
                track_condition=lap_data['track_condition']
            )
            db.session.add(test_lap)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Test completado exitosamente',
            'results': lap_results
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error en la simulación: {str(e)}'})

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

# Funciones auxiliares para la simulación de tests
def simulate_test_laps(driver, initial_tyre, total_laps, track_condition):
    """Simula las vueltas del test"""
    import random
    lap_results = []
    current_tyre = initial_tyre
    tyre_wear = 0
    incidents_count = 0
    total_time_lost = 0
    
    for lap in range(1, total_laps + 1):
        # Simular condiciones cambiantes (10% de probabilidad)
        current_track_condition = track_condition
        if lap > 5 and random.random() < 0.1:
            conditions = ['dry', 'light_rain', 'heavy_rain']
            current_track_condition = random.choice(conditions)
        
        # Calcular desgaste
        base_wear_rate = get_wear_rate(current_tyre, current_track_condition)
        skill_factor = (100 - driver.skill) / 200
        wear_rate = base_wear_rate * (1 + skill_factor) + random.random() * 3
        tyre_wear += wear_rate
        
        # Calcular tiempo de vuelta
        base_time = get_base_time(current_tyre, current_track_condition)
        wear_penalty = calculate_wear_penalty(tyre_wear, current_tyre)
        driver_time_bonus = (100 - driver.skill) / 50
        
        lap_time = base_time - driver_time_bonus + wear_penalty
        
        # Verificar incidentes
        incident_occurred = False
        time_lost_this_lap = 0
        
        if (tyre_wear > 80 or 
            is_wrong_tyre_for_conditions(current_tyre, current_track_condition)):
            incident_chance = calculate_incident_chance(
                tyre_wear, driver.consistency, current_tyre, current_track_condition
            )
            if random.random() * 100 < incident_chance:
                incident = generate_incident(tyre_wear, current_track_condition)
                time_lost_this_lap = calculate_time_lost(incident)
                lap_time += time_lost_this_lap
                incidents_count += 1
                total_time_lost += time_lost_this_lap
                incident_occurred = True
                
                # En tests, cambio de neumáticos por incidente grave
                if incident['type'] in ['Pinchazo', 'Hidroplaneo']:
                    current_tyre = get_appropriate_tyre(current_track_condition)
                    tyre_wear = 0
        
        # Cambio de neumáticos por desgaste
        if tyre_wear >= get_max_wear(current_tyre) and not incident_occurred:
            current_tyre = get_next_tyre(current_tyre, current_track_condition)
            tyre_wear = 0
        
        lap_results.append({
            'lap_number': lap,
            'tyre_type': current_tyre,
            'lap_time': round(lap_time, 3),
            'tyre_wear': min(150, int(tyre_wear)),  # Máximo 150% para mostrar degradación extrema
            'track_condition': current_track_condition,
            'incident_occurred': incident_occurred,
            'time_lost': time_lost_this_lap
        })
    
    return lap_results

def get_wear_rate(tyre_type, track_condition):
    base_rates = {
        'soft': 6, 'medium': 4, 'hard': 2.5, 
        'wet': 3, 'extreme_wet': 2
    }
    rate = base_rates.get(tyre_type, 4)
    
    if track_condition != 'dry' and tyre_type in ['soft', 'medium', 'hard']:
        rate *= 1.5
    
    return rate

def get_base_time(tyre_type, track_condition):
    dry_times = {
        'soft': 82, 'medium': 84, 'hard': 86, 
        'wet': 95, 'extreme_wet': 98
    }
    base_time = dry_times.get(tyre_type, 84)
    
    if track_condition == 'light_rain':
        if tyre_type in ['soft', 'medium', 'hard']:
            base_time += 15
        elif tyre_type == 'wet':
            base_time += 2
        else:
            base_time += 5
    elif track_condition == 'heavy_rain':
        if tyre_type in ['soft', 'medium', 'hard']:
            base_time += 25
        elif tyre_type == 'wet':
            base_time += 8
        else:
            base_time += 3
    
    return base_time

def calculate_wear_penalty(tyre_wear, tyre_type):
    if tyre_wear <= 50:
        return 0
    elif tyre_wear <= 80:
        return (tyre_wear - 50) * 0.1
    elif tyre_wear <= 100:
        return 3 + (tyre_wear - 80) * 0.2
    else:
        return 7 + (tyre_wear - 100) * 0.3

def is_wrong_tyre_for_conditions(tyre_type, track_condition):
    if track_condition == 'dry':
        return tyre_type in ['wet', 'extreme_wet']
    elif track_condition == 'light_rain':
        return tyre_type in ['soft', 'medium', 'hard']
    elif track_condition == 'heavy_rain':
        return tyre_type != 'extreme_wet'
    return False

def calculate_incident_chance(tyre_wear, driver_consistency, tyre_type, track_condition):
    base_chance = 0
    
    if tyre_wear > 120:
        base_chance = 40
    elif tyre_wear > 100:
        base_chance = 25
    elif tyre_wear > 90:
        base_chance = 15
    elif tyre_wear > 80:
        base_chance = 8
    
    if is_wrong_tyre_for_conditions(tyre_type, track_condition):
        base_chance *= 3
    
    if tyre_type == 'soft':
        base_chance *= 1.3
    elif tyre_type == 'medium':
        base_chance *= 1.1
    
    consistency_factor = (100 - driver_consistency) / 100
    return base_chance * (1 + consistency_factor * 0.5)

def generate_incident(tyre_wear, track_condition):
    import random
    incidents = [
        {'type': 'Trompo', 'severity': 'medium', 'base_time': 3},
        {'type': 'Salida de pista', 'severity': 'low', 'base_time': 2},
        {'type': 'Bloqueo de ruedas', 'severity': 'low', 'base_time': 1.5},
        {'type': 'Pinchazo', 'severity': 'high', 'base_time': 15},
        {'type': 'Pérdida de aerodinámica', 'severity': 'medium', 'base_time': 5}
    ]
    
    if track_condition != 'dry':
        incidents.extend([
            {'type': 'Hidroplaneo', 'severity': 'high', 'base_time': 10},
            {'type': 'Visibilidad cero', 'severity': 'medium', 'base_time': 6}
        ])
    
    if tyre_wear > 100:
        incidents = [i for i in incidents if i['severity'] != 'low']
    if tyre_wear > 120:
        incidents = [i for i in incidents if i['severity'] == 'high']
    
    return random.choice(incidents)

def calculate_time_lost(incident):
    import random
    return incident['base_time'] + random.random() * incident['base_time'] * 0.5

def get_appropriate_tyre(track_condition):
    if track_condition == 'dry':
        return 'soft'
    elif track_condition == 'light_rain':
        return 'wet'
    return 'extreme_wet'

def get_max_wear(tyre_type):
    max_wear = {
        'soft': 120, 'medium': 130, 'hard': 140, 
        'wet': 150, 'extreme_wet': 150
    }
    return max_wear.get(tyre_type, 120)

def get_next_tyre(current_tyre, track_condition):
    if track_condition != 'dry':
        if current_tyre == 'wet':
            return 'extreme_wet'
        return 'wet'
    
    sequence = ['soft', 'medium', 'hard']
    if current_tyre in sequence:
        current_index = sequence.index(current_tyre)
        return sequence[(current_index + 1) % len(sequence)]
    return 'soft'

# Solo iniciar el scheduler si estamos ejecutando app.py directamente
if __name__ == '__main__':
    scheduler.start()
    app.run(debug=True)