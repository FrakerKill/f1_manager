// static/js/race_engine.js - VERSIÓN COMPLETA CON COMPONENTES

class RaceEngine {
    constructor() {
        this.debug = true;
    }

    // CALCULAR RENDIMIENTO DEL COCHE BASADO EN COMPONENTES
    calculateCarPerformance(carComponents) {
        if (!carComponents || carComponents.length === 0) {
            return { strength: 50, reliability: 50 };
        }

        // Calcular promedios ponderados
        let totalStrength = 0;
        let totalReliability = 0;
        let componentCount = carComponents.length;

        carComponents.forEach(component => {
            totalStrength += component.strength || 50;
            totalReliability += component.reliability || 50;
        });

        return {
            strength: totalStrength / componentCount,
            reliability: totalReliability / componentCount
        };
    }

    // CALCULAR BONUS/PENALIZACIÓN POR RENDIMIENTO DEL COCHE
    calculateCarEffect(carComponents) {
        const performance = this.calculateCarPerformance(carComponents);
        
        // Efecto de fuerza en velocidad (-0.1s por cada 10 puntos sobre 50)
        const strengthEffect = (performance.strength - 50) * -0.01;
        
        // Efecto de fiabilidad en consistencia (menos variabilidad)
        const reliabilityEffect = (performance.reliability - 50) * -0.005;
        
        return {
            speedBonus: strengthEffect,
            consistencyBonus: reliabilityEffect,
            rawPerformance: performance
        };
    }

    // CALCULAR PROBABILIDAD DE FALLA MECÁNICA BASADA EN FIABILIDAD
    calculateMechanicalFailureRisk(carComponents, currentLap, totalLaps, incidents) {
        const performance = this.calculateCarPerformance(carComponents);
        
        // RIESGO BASE POR FIABILIDAD (más bajo = más riesgo)
        let baseRisk = (100 - performance.reliability) / 500; // 0-10% base
        
        // AUMENTAR RIESGO EN VUELTAS FINALES
        const lateRaceFactor = (currentLap / totalLaps) * 0.05;
        baseRisk += lateRaceFactor;
        
        // AUMENTAR RIESGO POR INCIDENTES PREVIOS
        const incidentFactor = incidents * 0.02;
        baseRisk += incidentFactor;
        
        // COMPONENTES INDIVIDUALES CON BAJA FIABILIDAD AÑADEN RIESGO EXTRA
        let componentRisk = 0;
        carComponents.forEach(component => {
            if (component.reliability < 30) {
                componentRisk += (30 - component.reliability) * 0.001;
            }
        });
        baseRisk += componentRisk;
        
        return Math.min(0.15, baseRisk); // Máximo 15% de riesgo por vuelta
    }

    // SIMULACIÓN DE VUELTA MEJORADA CON COMPONENTES
    simulateLap(driver, carComponents, tyreType, trackCondition, lapNumber, previousData = {}) {
        const carEffect = this.calculateCarEffect(carComponents);
        const mechanicalRisk = this.calculateMechanicalFailureRisk(carComponents, lapNumber, 
            previousData.totalLaps || 60, previousData.incidents || 0);

        const result = {
            lapTime: 0,
            tyreWear: previousData.tyreWear || 0,
            tyreTemperature: previousData.tyreTemperature || 0,
            tyreCondition: previousData.tyreCondition || 'cold',
            incident: null,
            timeLost: 0,
            pitStop: false,
            consistencyVariation: 0,
            consecutiveFastLaps: previousData.consecutiveFastLaps || 0,
            mechanicalFailure: false,
            failureComponent: null,
            carPerformance: carEffect.rawPerformance,
            isNewTyre: previousData.pitStop || false
        };

        // VERIFICAR FALLA MECÁNICA
        if (Math.random() < mechanicalRisk) {
            result.mechanicalFailure = true;
            result.failureComponent = this.determineFailedComponent(carComponents);
            result.incident = {
                type: 'Falla Mecánica',
                severity: 'high',
                baseTime: 30, // Tiempo perdido significativo
                description: `Falla en ${result.failureComponent}`
            };
            result.timeLost = result.incident.baseTime;
            return result; // No procesar más la vuelta si hay falla mecánica
        }

        // 1. ACTUALIZAR TEMPERATURA DE NEUMÁTICOS
        this.updateTyreTemperature(result, tyreType, trackCondition, lapNumber, previousData);

        // 2. CALCULAR VARIABILIDAD DEL PILOTO + BONUS COCHE
        result.consistencyVariation = this.calculateConsistencyVariation(
            driver.consistency, 
            lapNumber, 
            previousData.incidents || 0,
            carEffect.consistencyBonus
        );

        // 3. CALCULAR DESGASTE
        result.tyreWear = this.calculateTyreWear(
            result.tyreWear,
            tyreType,
            trackCondition,
            driver.skill,
            result.tyreCondition,
            lapNumber,
            result.isNewTyre,
            previousData.lastLapTime
        );

        // 4. CALCULAR TIEMPO DE VUELTA CON BONUS DEL COCHE
        result.lapTime = this.calculateLapTime(
            driver,
            carComponents,
            tyreType,
            trackCondition,
            result.tyreWear,
            result.tyreTemperature,
            result.tyreCondition,
            result.consistencyVariation,
            previousData.lastLapTime,
            result.isNewTyre,
            carEffect.speedBonus
        );

        // 5. CONTROL DE VUELTAS RÁPIDAS CONSECUTIVAS
        if (previousData.lastLapTime) {
            const lapImprovement = previousData.lastLapTime - result.lapTime;
            
            if (lapImprovement > 0.5 && 
                result.tyreCondition === 'optimal' && 
                result.tyreWear < 70) {
                result.consecutiveFastLaps = (previousData.consecutiveFastLaps || 0) + 1;
            } else {
                result.consecutiveFastLaps = 0;
            }
            
            if (result.consecutiveFastLaps >= 3) {
                result.tyreTemperature += 5 + (result.consecutiveFastLaps - 3) * 1.0;
            }
        }

        // 6. VERIFICAR INCIDENTES (solo si no hay falla mecánica)
        const incidentResult = this.checkIncidents(
            result.tyreWear,
            driver.consistency,
            tyreType,
            trackCondition,
            result.tyreCondition,
            result.consecutiveFastLaps,
            result.isNewTyre,
            lapNumber,
            carEffect.rawPerformance.reliability
        );

        if (incidentResult.incident) {
            result.incident = incidentResult.incident;
            result.timeLost = incidentResult.timeLost;
            result.lapTime += result.timeLost;
            
            if (incidentResult.pitStop) {
                result.pitStop = true;
                result.tyreWear = 0;
                result.tyreTemperature = 0;
                result.tyreCondition = 'cold';
                result.consecutiveFastLaps = 0;
                result.isNewTyre = true;
            }
        }

        // 7. VERIFICAR CAMBIO DE NEUMÁTICOS POR DESGASTE
        if ((result.tyreWear >= this.getMaxWear(tyreType) || result.tyreWear >= 140) && !result.pitStop) {
            result.pitStop = true;
            result.tyreWear = 0;
            result.tyreTemperature = 0;
            result.tyreCondition = 'cold';
            result.consecutiveFastLaps = 0;
            result.isNewTyre = true;
        }

        // 8. Marcar que ya no es neumático nuevo después de la primera vuelta
        if (result.isNewTyre) {
            result.isNewTyre = false;
        }

        return result;
    }

    // DETERMINAR QUÉ COMPONENTE FALLA
    determineFailedComponent(carComponents) {
        // Los componentes con menor fiabilidad tienen más probabilidad de fallar
        const componentsWithRisk = carComponents.map(component => ({
            type: component.component_type,
            reliability: component.reliability,
            risk: (100 - component.reliability) * Math.random()
        }));
        
        componentsWithRisk.sort((a, b) => b.risk - a.risk);
        return componentsWithRisk[0].type;
    }

    // CÁLCULO DE TIEMPO DE VUELTA CON COMPONENTES
    calculateLapTime(driver, carComponents, tyreType, trackCondition, tyreWear, temperature, 
                    condition, consistencyVariation, lastLapTime, isNewTyre, carSpeedBonus) {
        const baseTime = this.getBaseTime(tyreType, trackCondition);
        const wearPenalty = this.calculateWearPenalty(tyreWear, tyreType);
        const driverTimeBonus = (100 - driver.skill) / 50;
        const temperatureEffect = this.calculateTemperatureEffect(temperature, condition, isNewTyre);
        const consistencyEffect = consistencyVariation * 0.5;
        
        // BONUS DEL COCHE EN VELOCIDAD
        const carEffect = carSpeedBonus || 0;
        
        // BONUS POR NEUMÁTICO NUEVO
        const newTyreBonus = isNewTyre ? -1.5 : 0;
        
        let lapTime = baseTime - driverTimeBonus - carEffect + wearPenalty + 
                     temperatureEffect + consistencyEffect - newTyreBonus;
        
        // Variabilidad natural
        const variability = isNewTyre ? 0.2 : 0.5;
        const naturalVariation = (Math.random() - 0.5) * variability;
        lapTime += naturalVariation;
        
        return Math.max(60, lapTime);
    }

    // VARIABILIDAD CON BONUS DE FIABILIDAD
    calculateConsistencyVariation(driverConsistency, lap, totalIncidents, reliabilityBonus = 0) {
        const baseVariation = (100 - driverConsistency) / 200;
        const fatigueEffect = (lap / 50) * 0.1;
        const incidentEffect = totalIncidents * 0.03;
        const randomMoment = (Math.random() - 0.5) * 0.15;
        
        // REDUCIR VARIABILIDAD CON MEJOR FIABILIDAD
        const reliabilityEffect = reliabilityBonus * 2;
        
        return baseVariation + fatigueEffect + incidentEffect + randomMoment - reliabilityEffect;
    }

    // SISTEMA DE INCIDENTES CON FIABILIDAD
    checkIncidents(tyreWear, driverConsistency, tyreType, trackCondition, tyreCondition, 
                  consecutiveFastLaps, isNewTyre, lapNumber, carReliability) {
        const result = { incident: null, timeLost: 0, pitStop: false };
        
        let baseChance = 0;
        
        // PROBABILIDADES BASE POR DESGASTE - REDUCIDAS POR FIABILIDAD
        if (tyreWear > 130) baseChance = 40;    // Reducido de 50
        else if (tyreWear > 120) baseChance = 28; // Reducido de 35
        else if (tyreWear > 110) baseChance = 20; // Reducido de 25
        else if (tyreWear > 100) baseChance = 12; // Reducido de 15
        else if (tyreWear > 90) baseChance = 6;   // Reducido de 8
        else if (tyreWear > 80) baseChance = 3;   // Reducido de 4
        else if (tyreWear > 70) baseChance = 1.5; // Reducido de 2
        
        // REDUCIR PROBABILIDAD POR BUENA FIABILIDAD DEL COCHE
        const reliabilityReduction = (carReliability - 50) * 0.1;
        baseChance = Math.max(0, baseChance - reliabilityReduction);

        // NEUMÁTICOS NUEVOS MÁS SEGUROS
        if (isNewTyre && lapNumber <= 5) {
            baseChance *= 0.1;
        }
        
        // FACTORES DE RIESGO
        const riskFactors = [];
        
        if (this.isWrongTyreForConditions(tyreType, trackCondition)) {
            riskFactors.push(2.0);
        }
        if (tyreCondition === 'cold') {
            riskFactors.push(1.5);
        }
        if (tyreCondition === 'overheating') {
            riskFactors.push(2.0);
        }
        if (consecutiveFastLaps >= 3) {
            riskFactors.push(1.5);
        }
        
        // RIESGO ADICIONAL POR DESGASTE EXTREMO
        if (tyreWear > 100) {
            const extraRisk = 1.0 + ((tyreWear - 100) * 0.05);
            riskFactors.push(extraRisk);
        }
        
        // CALCULAR FACTOR COMPUESTO
        let compoundRisk = 1;
        riskFactors.forEach(factor => {
            compoundRisk *= factor;
        });
        
        const consistencyFactor = (100 - driverConsistency) / 100;
        const finalChance = baseChance * compoundRisk * (1 + consistencyFactor);
        
        if (Math.random() * 100 < finalChance) {
            result.incident = this.generateIncident(tyreWear, trackCondition, tyreCondition, 
                                                  consecutiveFastLaps, isNewTyre, carReliability);
            result.timeLost = this.calculateTimeLost(result.incident);
            
            if (this.requiresPitStop(result.incident, tyreWear)) {
                result.pitStop = true;
            }
        }
        
        return result;
    }

    // GENERAR INCIDENTES CON FIABILIDAD
    generateIncident(tyreWear, trackCondition, tyreCondition, consecutiveFastLaps, isNewTyre, carReliability) {
        // INCIDENTES LEVES
        let mildIncidents = [
            { type: 'Bloqueo de ruedas', severity: 'low', baseTime: 1.0 },
            { type: 'Salida de pista', severity: 'low', baseTime: 1.5 },
            { type: 'Trompo leve', severity: 'low', baseTime: 2.0 },
            { type: 'Falta de agarre', severity: 'low', baseTime: 1.2 }
        ];
        
        // INCIDENTES MEDIOS
        let mediumIncidents = [
            { type: 'Trompo', severity: 'medium', baseTime: 2.5 },
            { type: 'Pérdida de aerodinámica', severity: 'medium', baseTime: 3.0 },
            { type: 'Problemas de frenos', severity: 'medium', baseTime: 4.0 },
            { type: 'Falla de suspensión', severity: 'medium', baseTime: 3.5 }
        ];
        
        // INCIDENTES GRAVES (menos probables con buena fiabilidad)
        let severeIncidents = [
            { type: 'Pinchazo', severity: 'high', baseTime: 25 },
            { type: 'Reventón', severity: 'high', baseTime: 35 },
            { type: 'Falla mecánica grave', severity: 'high', baseTime: 30 }
        ];
        
        // REDUCIR INCIDENTES GRAVES CON BUENA FIABILIDAD
        let availableIncidents = [...mildIncidents, ...mediumIncidents];
        
        // Solo incluir incidentes graves si la fiabilidad es baja o el desgaste es alto
        if (tyreWear > 90 && carReliability < 70) {
            availableIncidents = [...availableIncidents, ...severeIncidents];
        }
        
        // FILTRAR POR GRAVEDAD SEGÚN DESGASTE Y FIABILIDAD
        let incidentPool = availableIncidents;
        
        if (tyreWear < 50) {
            incidentPool = availableIncidents.filter(i => i.severity === 'low');
        }
        else if (tyreWear < 80) {
            incidentPool = availableIncidents.filter(i => i.severity !== 'high');
        }
        else if (tyreWear > 100 && carReliability < 60) {
            const graveProbability = Math.min(0.6, (tyreWear - 100) * 0.02);
            if (Math.random() < graveProbability) {
                incidentPool = availableIncidents.filter(i => i.severity === 'high');
            } else {
                incidentPool = availableIncidents.filter(i => i.severity !== 'low');
            }
        }
        
        if (incidentPool.length === 0) {
            incidentPool = mildIncidents;
        }
        
        return incidentPool[Math.floor(Math.random() * incidentPool.length)];
    }

    // DETERMINAR SI UN INCIDENTE REQUIERE PIT STOP
    requiresPitStop(incident, tyreWear) {
        // INCIDENTES QUE SIEMPRE REQUIEREN PIT STOP
        if (incident.type === 'Pinchazo' || 
            incident.type === 'Reventón' ||
            incident.type === 'Destrucción de neumático') {
            return true;
        }
        
        // INCIDENTES QUE REQUIEREN PIT STOP SOLO CON ALTO DESGASTE
        if ((incident.type === 'Degradación acelerada' && tyreWear > 90) ||
            (incident.type === 'Sobrecalentamiento crítico' && tyreWear > 100) ||
            (incident.type === 'Hidroplaneo grave' && tyreWear > 80)) {
            return true;
        }
        
        // DESGASTE CRÍTICO OBLIGA A BOXES (140+)
        if (tyreWear >= 140) {
            return true;
        }
        
        return false;
    }

    // ACTUALIZAR TEMPERATURA DE NEUMÁTICOS
    updateTyreTemperature(result, tyreType, trackCondition, lap, previousData) {
        const warmupRates = {
            'soft': 18, 'medium': 15, 'hard': 12, 'wet': 20, 'extreme_wet': 18
        };
        
        const optimalTemps = {
            'soft': { min: 65, max: 80 },
            'medium': { min: 60, max: 75 },
            'hard': { min: 55, max: 70 },
            'wet': { min: 40, max: 55 },
            'extreme_wet': { min: 35, max: 50 }
        };
        
        const coolDownRates = {
            'soft': 6, 'medium': 5, 'hard': 4, 'wet': 8, 'extreme_wet': 7
        };
        
        const warmupRate = warmupRates[tyreType] || 15;
        const coolDownRate = coolDownRates[tyreType] || 5;
        const optimalTemp = optimalTemps[tyreType] || { min: 60, max: 75 };
        
        // CALENTAMIENTO ACELERADO POST-PIT STOP
        if (previousData.pitStop || result.isNewTyre) {
            result.tyreTemperature += warmupRate * 1.8;
        }
        // FASE DE CALENTAMIENTO INICIAL
        else if (result.tyreTemperature < optimalTemp.min) {
            const progress = result.tyreTemperature / optimalTemp.min;
            const boostFactor = 1.5 - (progress * 0.7);
            result.tyreTemperature += warmupRate * boostFactor * (0.8 + Math.random() * 0.4);
        } 
        // FASE DE MANTENIMIENTO DINÁMICO
        else {
            // Calor generado por el desgaste y uso
            const wearHeat = (result.tyreWear / 100) * 2.0;
            const drivingHeat = 1.0 + (Math.random() * 1.0);
            
            // Enfriamiento natural
            const naturalCooling = coolDownRate * (0.8 + Math.random() * 0.4);
            const trackCooling = this.getTrackCoolingEffect(trackCondition);
            
            // EFECTO DE VELOCIDAD
            const speedEffect = previousData.lastLapTime ? 
                Math.max(0, (76 - previousData.lastLapTime) * 0.5) : 0;
            
            const netHeat = (wearHeat + drivingHeat + speedEffect) - (naturalCooling + trackCooling);
            result.tyreTemperature += netHeat;
            
            // ENFRIAMIENTO ALEATORIO NATURAL
            if (result.tyreTemperature > optimalTemp.max && Math.random() < 0.4) {
                const coolDown = 3 + (Math.random() * 4);
                result.tyreTemperature -= coolDown;
            }
            
            // SOBRECALENTAMIENTO TEMPORAL
            if (result.tyreCondition === 'overheating' && Math.random() < 0.3) {
                result.tyreTemperature -= 5 + (Math.random() * 3);
            }
        }
        
        // EFECTO DE CONDICIONES DE PISTA
        if (trackCondition === 'dry') {
            result.tyreTemperature *= 1.05;
        } else if (trackCondition === 'light_rain') {
            result.tyreTemperature *= 0.6;
        } else if (trackCondition === 'heavy_rain') {
            result.tyreTemperature *= 0.4;
        }
        
        // LÍMITES FÍSICOS
        result.tyreTemperature = Math.max(15, Math.min(110, result.tyreTemperature));
        
        // DETERMINAR CONDICIÓN BASADA EN TEMPERATURA ÓPTIMA
        if (result.tyreTemperature < optimalTemp.min - 15) {
            result.tyreCondition = 'cold';
        } else if (result.tyreTemperature < optimalTemp.min - 5) {
            result.tyreCondition = 'warming';
        } else if (result.tyreTemperature < optimalTemp.min) {
            result.tyreCondition = 'warming';
        } else if (result.tyreTemperature <= optimalTemp.max) {
            result.tyreCondition = 'optimal';
        } else if (result.tyreTemperature <= optimalTemp.max + 8) {
            result.tyreCondition = 'warming';
        } else if (result.tyreTemperature <= optimalTemp.max + 15) {
            result.tyreCondition = 'warming';
        } else {
            result.tyreCondition = 'overheating';
        }
        
        // REGRESIÓN A ÓPTIMO
        if (result.tyreCondition === 'overheating' && Math.random() < 0.25) {
            result.tyreTemperature = optimalTemp.max - 2 + (Math.random() * 4);
            result.tyreCondition = 'optimal';
        }
    }

    // CALCULAR DESGASTE DE NEUMÁTICOS
    calculateTyreWear(currentWear, tyreType, trackCondition, driverSkill, tyreCondition, lapNumber, isNewTyre, lastLapTime) {
        const baseWearRates = { 
            'soft': 6.0,    // ~15-18 vueltas máximas
            'medium': 4.0,  // ~25 vueltas máximas  
            'hard': 2.5,    // ~40 vueltas máximas
            'wet': 1.5,     // Muy duraderos en lluvia
            'extreme_wet': 1.2 
        };
        
        let wearRate = baseWearRates[tyreType] || 4.0;
        
        // FACTOR DE HABILIDAD DEL PILOTO
        const skillFactor = (100 - driverSkill) / 300;
        
        // EFECTO DE VELOCIDAD
        let speedFactor = 1.0;
        if (lastLapTime) {
            const baseLapTime = this.getBaseTime(tyreType, trackCondition);
            const intensity = Math.max(0.8, (baseLapTime - lastLapTime) / baseLapTime + 1);
            speedFactor = 0.8 + (intensity * 0.4);
        }
        
        // EFECTO DE TEMPERATURA
        let temperatureFactor = 1.0;
        switch(tyreCondition) {
            case 'cold':
                temperatureFactor = 1.3;
                break;
            case 'warming':
                temperatureFactor = 1.05;
                break;
            case 'optimal':
                temperatureFactor = 0.85;
                break;
            case 'overheating':
                temperatureFactor = 1.4;
                break;
        }
        
        // EFECTO DE CONDICIONES DE PISTA
        let trackFactor = 1.0;
        if (trackCondition !== 'dry' && ['soft', 'medium', 'hard'].includes(tyreType)) {
            trackFactor = 1.8;
        } else if (trackCondition === 'dry' && ['wet', 'extreme_wet'].includes(tyreType)) {
            trackFactor = 3.0;
        }
        
        // BONUS POR NEUMÁTICO NUEVO
        let newTyreFactor = 1.0;
        if (isNewTyre && lapNumber <= 3) {
            newTyreFactor = 0.6;
        }
        
        // DESGASTE ACELERADO SOLO EN NEUMÁTICOS MUY GASTADOS
        let wearAcceleration = 1.0;
        if (currentWear > 85) {
            wearAcceleration = 1.0 + ((currentWear - 85) / 15);
        }
        
        // CÁLCULO FINAL DEL DESGASTE
        let wearThisLap = wearRate * 
                         (1 + skillFactor) * 
                         speedFactor * 
                         temperatureFactor * 
                         trackFactor * 
                         newTyreFactor * 
                         wearAcceleration;
        
        // VARIABILIDAD (±15%)
        const randomVariation = 0.85 + (Math.random() * 0.3);
        wearThisLap *= randomVariation;
        
        // MÍNIMO DE DESGASTE POR VUELTA
        wearThisLap = Math.max(0.5, wearThisLap);
        
        const newWear = currentWear + wearThisLap;
        
        return Math.max(0, newWear);
    }

    // EFECTO DE TEMPERATURA EN TIEMPO DE VUELTA
    calculateTemperatureEffect(temperature, condition, isNewTyre) {
        const newTyreFactor = isNewTyre ? 0.6 : 1.0;
        
        if (condition === 'cold') {
            const coldPenalty = 2.0 + ((40 - Math.min(temperature, 40)) * 0.15);
            return (coldPenalty + (Math.random() * 0.8)) * newTyreFactor;
        } else if (condition === 'optimal') {
            return (Math.random() - 0.5) * 0.05 * newTyreFactor;
        } else if (condition === 'warming') {
            const warmPenalty = 0.8 + ((Math.max(temperature, 70) - 70) * 0.08);
            return (warmPenalty + (Math.random() * 0.4)) * newTyreFactor;
        } else {
            const overheatPenalty = 2.0 + ((Math.max(temperature, 85) - 85) * 0.15);
            return (overheatPenalty + (Math.random() * 0.8)) * newTyreFactor;
        }
    }

    // PENALIZACIÓN POR DESGASTE
    calculateWearPenalty(tyreWear, tyreType) {
        if (tyreWear <= 20) return 0;
        else if (tyreWear <= 40) return (tyreWear - 20) * 0.05;
        else if (tyreWear <= 60) return 1.0 + (tyreWear - 40) * 0.08;
        else if (tyreWear <= 80) return 2.6 + (tyreWear - 60) * 0.12;
        else if (tyreWear <= 100) return 5.0 + (tyreWear - 80) * 0.25;
        else if (tyreWear <= 120) return 10.0 + (tyreWear - 100) * 0.5;
        else return 20.0 + (tyreWear - 120) * 1.0;
    }

    // TIEMPO BASE POR TIPO DE NEUMÁTICO Y CONDICIONES
    getBaseTime(tyreType, trackCondition) {
        const dryTimes = { 
            'soft': 76,    // Más rápido
            'medium': 78,  // Intermedio  
            'hard': 80,    // Más lento
            'wet': 84,     // Reducida penalización en seco
            'extreme_wet': 88 
        };
        
        let baseTime = dryTimes[tyreType] || 78;
        
        // PENALIZACIONES POR CONDICIONES
        if (trackCondition === 'light_rain') {
            if (['soft', 'medium', 'hard'].includes(tyreType)) {
                baseTime += 6;
            } else if (tyreType === 'wet') {
                baseTime += 0.5;
            } else {
                baseTime += 2;
            }
        } else if (trackCondition === 'heavy_rain') {
            if (['soft', 'medium', 'hard'].includes(tyreType)) {
                baseTime += 12;
            } else if (tyreType === 'wet') {
                baseTime += 3;
            } else {
                baseTime += 1;
            }
        }
        
        return baseTime;
    }

    // LÍMITES MÁXIMOS DE DESGASTE
    getMaxWear(tyreType) {
        const maxWear = { 
            'soft': 140,    // Puede aguantar hasta 140% pero con alto riesgo
            'medium': 150,  // Un poco más resistente
            'hard': 160,    // Más resistente aún
            'wet': 180,     // Muy resistentes
            'extreme_wet': 180 
        };
        return maxWear[tyreType] || 150;
    }

    // VERIFICAR SI EL NEUMÁTICO ES INCORRECTO PARA LAS CONDICIONES
    isWrongTyreForConditions(tyreType, trackCondition) {
        if (trackCondition === 'dry') return ['wet', 'extreme_wet'].includes(tyreType);
        if (trackCondition === 'light_rain') return ['soft', 'medium', 'hard'].includes(tyreType);
        if (trackCondition === 'heavy_rain') return tyreType !== 'extreme_wet';
        return false;
    }

    // CALCULAR TIEMPO PERDIDO POR INCIDENTE
    calculateTimeLost(incident) {
        return incident.baseTime + Math.random() * incident.baseTime * 0.4;
    }

    // OBTENER NEUMÁTICO APROPIADO PARA CONDICIONES
    getAppropriateTyre(trackCondition) {
        if (trackCondition === 'dry') return 'soft';
        else if (trackCondition === 'light_rain') return 'wet';
        else return 'extreme_wet';
    }

    // EFECTO DE ENFRIAMIENTO DE PISTA
    getTrackCoolingEffect(trackCondition) {
        switch(trackCondition) {
            case 'dry': return 1.0 + (Math.random() * 0.5);
            case 'light_rain': return 3.0 + (Math.random() * 1.0);
            case 'heavy_rain': return 5.0 + (Math.random() * 2.0);
            default: return 2.0;
        }
    }

    // SIMULAR VUELTA DE CLASIFICACIÓN CON COMPONENTES
    simulateQualifyingLap(driver, carComponents, tyreType, trackCondition) {
        const carEffect = this.calculateCarEffect(carComponents);
        
        // TIEMPO BASE CON BONUS DEL COCHE
        const baseTime = this.getBaseTime(tyreType, trackCondition);
        const driverEffect = (100 - driver.skill) / 80; // Efecto más fuerte en clasificación
        const carBonus = carEffect.speedBonus * 1.5; // Bonus amplificado en clasificación
        
        // VARIABILIDAD REDUCIDA EN CLASIFICACIÓN
        const consistencyVariation = (100 - driver.consistency) / 300;
        const randomVariation = (Math.random() - 0.5) * 0.8; // Menos variabilidad
        
        let lapTime = baseTime - driverEffect - carBonus + consistencyVariation + randomVariation;
        
        // EFECTO DE NEUMÁTICO NUEVO (siempre nuevos en clasificación)
        const newTyreBonus = -1.2;
        lapTime += newTyreBonus;
        
        return Math.max(70, lapTime);
    }
}

// Instancia global del motor
const raceEngine = new RaceEngine();

// Funciones globales para compatibilidad
function getAppropriateTyre(trackCondition) {
    return raceEngine.getAppropriateTyre(trackCondition);
}

function getMaxWear(tyreType) {
    return raceEngine.getMaxWear(tyreType);
}

// NUEVA FUNCIÓN: Calcular rendimiento del coche para la UI
function calculateCarPerformance(carComponents) {
    return raceEngine.calculateCarPerformance(carComponents);
}

// SIMULAR CLASIFICACIÓN COMPLETA
function simulateQualifyingSession(driversWithCars, trackCondition) {
    const results = [];
    
    driversWithCars.forEach(entry => {
        const lapTime = raceEngine.simulateQualifyingLap(
            entry.driver,
            entry.carComponents,
            entry.tyreType,
            trackCondition
        );
        
        results.push({
            driver: entry.driver,
            team: entry.team,
            carComponents: entry.carComponents,
            tyreType: entry.tyreType,
            lapTime: lapTime
        });
    });
    
    // Ordenar por tiempo (más rápido primero)
    results.sort((a, b) => a.lapTime - b.lapTime);
    
    return results;
}