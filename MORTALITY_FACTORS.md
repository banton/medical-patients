# Medical Simulation Mortality Factors

## Overview
This document describes all factors that influence patient mortality in the military medical simulation system. Currently showing **100% mortality** with **88% dying at POI**, which demonstrates realistic combat casualty deterioration but needs tuning.

## Timeline Configuration

### 1. Simulation Duration
- **Total simulation time**: 6+ hours (extended from original ~1 hour)
- **Purpose**: Allows realistic deterioration over combat-realistic timeframes
- **Location**: `medical_simulation_bridge.py` lines 140-180

### 2. Wait Times at POI

#### Wait for Combat Medic
**Individual Casualty**:
- **Time**: 10-60 minutes (random)
- **Code**: `medic_arrival_minutes = random.randint(10, 60)`

**Mass Casualty Event**:
- **Time**: 60-240 minutes (1-4 hours)
- **Code**: `medic_arrival_minutes = random.randint(60, 240)`
- **Rationale**: "Even the combat medics are down"

#### Wait for Evacuation (After Triage)
Based on `evacuation_transit_times.json`:
```json
"POI": {
  "T1": { "min_hours": 3, "max_hours": 8 },
  "T2": { "min_hours": 5, "max_hours": 12 },
  "T3": { "min_hours": 8, "max_hours": 12 }
}
```
- **T1 (Urgent)**: 3-8 hours wait
- **T2 (Delayed)**: 5-12 hours wait  
- **T3 (Minimal)**: 8-12 hours wait

### 3. Transit Times Between Facilities
From `evacuation_transit_times.json`:
```json
"transit_times": {
  "POI_to_Role1": { "min_hours": 1, "max_hours": 4 },
  "Role1_to_Role2": { "min_hours": 2, "max_hours": 6 },
  "Role2_to_Role3": { "min_hours": 4, "max_hours": 8 }
}
```

## Deterioration Factors

### 1. Initial Health Score
**Source**: `health_score_engine.py`
- Mapped from injury type and severity
- **Battle Injury + Severe**: ~15-30 initial health
- **Battle Injury + Moderate**: ~35-50 initial health
- **Battle Injury + Mild**: ~55-70 initial health

**Severity Mapping** (1-10 scale to text):
- 9-10 → "Severe" 
- 7-8 → "Moderate to severe"
- 4-6 → "Moderate"
- 1-3 → "Mild to moderate"

### 2. Base Deterioration Rate
**Source**: `deterioration_calculator.py`
- **Base rate**: 5-30 health points per hour (depending on severity)
- **Triage-based multipliers**:
  - T1: 2.0x deterioration
  - T2: 1.5x deterioration
  - T3: 1.0x deterioration
  - T4: 0.5x deterioration

### 3. Golden Hour Effect (Exponential Deterioration)
From `injuries.json`:
```json
"golden_hour_effect": {
  "hours_before_golden_hour": 1,
  "multiplier_after_golden_hour": 1.5,
  "max_multiplier_at_hours": 6,
  "max_multiplier_value": 2.5
}
```
- First hour: Normal deterioration
- After 1 hour: 1.5x multiplier
- Scales up to 2.5x by hour 6
- **Result**: Exponential worsening over time

### 4. Cliff Events (Sudden Deterioration)
From `injuries.json`:
```json
"cliff_events": {
  "enabled": true,
  "probability_per_hour": 0.05,
  "applies_to_health_range": [20, 60],
  "health_drop_range": [15, 30]
}
```
- 5% chance per hour
- Sudden 15-30 health point drop
- Only affects patients with 20-60 health

### 5. Environmental Factors
**Heat exposure**:
- Additional 20% deterioration rate
- Applied during wait and transport

**Combat stress**:
- Additional 10% deterioration rate

## Treatment Effects

### 1. Treatment Modifiers
From `treatment_modifiers.py`:
```python
"tourniquet": {
  "health_boost": 5,
  "deterioration_modifier": 0.2  # Reduces deterioration to 20%
}
"iv_fluids": {
  "health_boost": 10,
  "deterioration_modifier": 0.7
}
"morphine": {
  "health_boost": 0,
  "deterioration_modifier": 0.9
}
"surgery": {
  "health_boost": 20,
  "deterioration_modifier": 0.1
}
```

### 2. Treatment Availability by Facility
- **POI**: Basic first aid only (tourniquet, pressure)
- **Role1**: IV fluids, morphine, basic stabilization
- **Role2**: Surgery, blood products
- **Role3**: Full surgical capability
- **Role4**: Definitive care

## Death Triggers

### 1. Health Reaching Zero
- Patient dies when `current_health <= 0`
- Location of death recorded (POI, Role1, Role2, transit, etc.)

### 2. Time-Based Death Risk
- Patients waiting >6 hours at POI with T1 triage: Very high mortality
- Patients in transit >4 hours with critical injuries: High mortality

### 3. Untreated Conditions
- Hemorrhage without tourniquet: Rapid deterioration
- Tension pneumothorax without decompression: Death within 1-2 hours

## Current Issues Causing 100% Mortality

### 1. Excessive Wait Times
- **Medic arrival**: Up to 4 hours for mass casualty
- **Evacuation wait**: Up to 12 hours for T2/T3
- **Total time at POI**: Can exceed 16 hours

### 2. Aggressive Deterioration
- Base rate (5-30/hour) × Triage multiplier (2.0) × Golden hour (2.5) = **Up to 150 health loss/hour**
- Most patients start with 15-50 health
- **Result**: Death within 1-2 hours

### 3. Limited Treatment at POI
- No significant health restoration at POI
- Treatments only slow deterioration, don't reverse it
- By the time evacuation arrives, patients already dead

## Recommended Adjustments for 20% POI Mortality

### 1. Reduce Wait Times
```json
"POI": {
  "T1": { "min_hours": 0.5, "max_hours": 2 },
  "T2": { "min_hours": 1, "max_hours": 4 },
  "T3": { "min_hours": 2, "max_hours": 6 }
}
```

### 2. Adjust Deterioration Rates
- Base rate: 2-10 health/hour (instead of 5-30)
- Golden hour multiplier: 1.2-1.5x (instead of 1.5-2.5x)
- Cliff event probability: 0.02 (instead of 0.05)

### 3. Improve POI Treatment
- Allow basic stabilization to add 10-20 health
- Reduce deterioration modifier to 0.3-0.5 with treatment
- Add "field medic" treatment option with better outcomes

### 4. Vary Initial Health by Injury
- T1 injuries: 30-50 initial health (not 15-30)
- T2 injuries: 50-70 initial health
- T3 injuries: 70-90 initial health

## Configuration Locations

1. **Wait times**: `patient_generator/evacuation_transit_times.json`
2. **Deterioration model**: `patient_generator/injuries.json`
3. **Treatment effects**: `medical_simulation/treatment_modifiers.py`
4. **Health scoring**: `medical_simulation/health_score_engine.py`
5. **Timeline generation**: `patient_generator/medical_simulation_bridge.py`
6. **UI configuration**: `static/index.html` (Advanced Configuration section)

## Current Metrics (200 patients)
- **Total mortality**: 100%
- **POI deaths**: 88.5%
- **Role2 deaths**: 5%
- **Transit deaths**: 6.5%
- **T1 mortality**: 100%
- **T2 mortality**: 100%
- **T3 mortality**: 0% (no T3 patients generated)
- **T4 mortality**: 100%

## Target Metrics (Realistic Combat)
- **Total mortality**: 15-25%
- **POI deaths**: 15-20% of total patients
- **Role1 deaths**: 3-5%
- **Role2 deaths**: 1-2%
- **Transit deaths**: 2-3%
- **T1 mortality**: 40-60%
- **T2 mortality**: 10-20%
- **T3 mortality**: <5%
- **T4 mortality**: 100% (expectant)