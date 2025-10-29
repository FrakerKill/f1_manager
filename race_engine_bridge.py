# race_engine_bridge.py
import random

class RaceEngineBridge:
    @staticmethod
    def calculate_mechanical_failure_risk(car_components, current_lap, total_laps, incidents):
        """Calcula el riesgo de falla mecánica - PROBABILIDADES MUCHO MÁS OPTIMISTAS"""
        try:
            # Calcular fiabilidad promedio - asumir que los componentes son buenos por defecto
            if not car_components:
                reliability = 80  # Base alta por defecto
            else:
                reliability = sum(comp.get('reliability', 75) for comp in car_components) / len(car_components)
            
            # RIESGO BASE MUY BAJO (0-0.04% base)
            base_risk = (100 - reliability) / 10000  # 0-0.02% base
            
            # SOLO aumentar riesgo en ÚLTIMAS 3 VUELTAS y muy poco
            if current_lap > total_laps - 3:
                late_race_factor = ((current_lap - (total_laps - 3)) / 3) * 0.005  # Máximo 0.5% extra
                base_risk += late_race_factor
            
            # AUMENTO MUY PEQUEÑO por incidentes (solo si muchos incidentes)
            incident_factor = max(0, (incidents - 2)) * 0.0005  # Solo después de 2 incidentes
            base_risk += incident_factor
            
            # COMPONENTES SOLO si son EXTREMADAMENTE malos (fiabilidad < 10)
            component_risk = 0
            for component in car_components:
                comp_reliability = component.get('reliability', 75)
                if comp_reliability < 10:  # Solo componentes catastróficamente malos
                    component_risk += (10 - comp_reliability) * 0.0001  # Mínimo
            
            base_risk += component_risk
            
            # MÁXIMO ABSOLUTO 1% por vuelta (solo en condiciones extremas)
            final_risk = min(0.01, base_risk)
            
            # REDUCIR AÚN MÁS en primeras vueltas
            if current_lap < 10:
                final_risk *= 0.5
                
            return final_risk
            
        except Exception as e:
            print(f"Error en calculo de riesgo: {e}")
            return 0.002  # Fallback muy bajo
    
    @staticmethod
    def determine_failed_component(car_components):
        """Determina que componente falla - MUY conservador"""
        if not car_components:
            return "motor"
        
        # 80% de probabilidad de que no falle ningún componente específico (falla genérica)
        if random.random() < 0.8:
            return "sistema"
        
        components_with_risk = []
        for component in car_components:
            reliability = component.get('reliability', 75)
            # SOLO componentes con fiabilidad < 20 tienen riesgo real
            if reliability < 20:
                risk = (100 - reliability) * (0.3 + 0.7 * random.random())
            else:
                risk = (100 - reliability) * 0.005 * random.random()  # Riesgo casi cero
            
            components_with_risk.append({
                'type': component.get('component_type', 'unknown'),
                'reliability': reliability,
                'risk': risk
            })
        
        # Si no hay componentes malos, falla genérica
        if not any(comp['risk'] > 5 for comp in components_with_risk):
            return "sistema"
        
        components_with_risk.sort(key=lambda x: x['risk'], reverse=True)
        return components_with_risk[0]['type'] if components_with_risk else "sistema"