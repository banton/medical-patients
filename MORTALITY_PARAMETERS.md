# Mortality Parameters Reference Guide

## Overview
This document lists ALL parameters that affect patient mortality in the medical simulation system, their current values, file locations, and recommended adjustments to achieve realistic ~20% mortality rates.

---

## 1. INITIAL HEALTH PARAMETERS

### Location: `medical_simulation/config/injuries.json`

#### Initial Health by Injury Type
```json
CURRENT VALUES:
"battle_trauma": {
  "gsw": {
    "initial_triage_distribution": {
      "T1": 0.20, "T2": 0.30, "T3": 0.40, "T4": 0.10
    }
  }
}

HEALTH MAPPING (medical_simulation/health_score_engine.py):
- T1 (Critical): 15-30 health points
- T2 (Urgent): 35-50 health points  
- T3 (Delayed): 55-70 health points
- T4 (Expectant): 5-15 health points

RECOMMENDED ADJUSTMENTS:
- T1: 30-50 health points (increase by 15-20)
- T2: 50-70 health points (increase by 15-20)
- T3: 70-90 health points (increase by 15-20)
- T4: 5-10 health points (keep low, expectant)
```

---

## 2. DETERIORATION PARAMETERS

### Location: `patient_generator/injuries.json`

#### Base Deterioration Rates
```json
CURRENT VALUES:
"deterioration_model": {
  "Battle Injury": {
    "Severe": {
      "initial_health": 25,
      "deterioration_rate": 30,    // Per hour
      "variance": 5,
      "hemorrhage_multiplier": 1.8
    },
    "Moderate to severe": {
      "deterioration_rate": 20     // Per hour
    },
    "Moderate": {
      "deterioration_rate": 12     // Per hour
    },
    "Mild to moderate": {
      "deterioration_rate": 5      // Per hour
    }
  }
}

RECOMMENDED ADJUSTMENTS:
"Severe": {
  "deterioration_rate": 10,        // Was 30
  "hemorrhage_multiplier": 1.3     // Was 1.8
},
"Moderate to severe": {
  "deterioration_rate": 7          // Was 20
},
"Moderate": {
  "deterioration_rate": 4          // Was 12
},
"Mild to moderate": {
  "deterioration_rate": 2          // Was 5
}
```

#### Golden Hour Effect
```json
CURRENT VALUES:
"golden_hour_effect": {
  "hours_before_golden_hour": 1,
  "multiplier_after_golden_hour": 1.5,   // Applied after 1 hour
  "max_multiplier_at_hours": 6,
  "max_multiplier_value": 2.5            // Maximum at 6 hours
}

RECOMMENDED ADJUSTMENTS:
"golden_hour_effect": {
  "hours_before_golden_hour": 1,
  "multiplier_after_golden_hour": 1.2,   // Was 1.5
  "max_multiplier_at_hours": 6,
  "max_multiplier_value": 1.5            // Was 2.5
}
```

#### Cliff Events (Sudden Deterioration)
```json
CURRENT VALUES:
"cliff_events": {
  "enabled": true,
  "probability_per_hour": 0.05,          // 5% chance
  "applies_to_health_range": [20, 60],
  "health_drop_range": [15, 30]          // Sudden drop
}

RECOMMENDED ADJUSTMENTS:
"cliff_events": {
  "enabled": true,
  "probability_per_hour": 0.02,          // Was 0.05
  "health_drop_range": [10, 20]          // Was [15, 30]
}
```

### Location: `medical_simulation/config/deterioration_rates.json`

#### Triage-Based Multipliers
```json
CURRENT VALUES:
"triage_multipliers": {
  "T1": 2.0,    // Critical patients deteriorate 2x faster
  "T2": 1.5,    // Urgent patients 1.5x faster
  "T3": 1.0,    // Delayed normal rate
  "T4": 0.5     // Expectant slower (already dying)
}

RECOMMENDED ADJUSTMENTS:
"triage_multipliers": {
  "T1": 1.5,    // Was 2.0
  "T2": 1.2,    // Was 1.5
  "T3": 0.8,    // Was 1.0
  "T4": 0.5     // Keep same
}
```

---

## 3. WAIT TIME PARAMETERS

### Location: `patient_generator/evacuation_transit_times.json`

#### POI Evacuation Wait Times
```json
CURRENT VALUES:
"evacuation_times": {
  "POI": {
    "T1": { "min_hours": 3, "max_hours": 8 },
    "T2": { "min_hours": 5, "max_hours": 12 },
    "T3": { "min_hours": 8, "max_hours": 12 }
  }
}

RECOMMENDED ADJUSTMENTS:
"POI": {
  "T1": { "min_hours": 0.5, "max_hours": 2 },    // Was 3-8
  "T2": { "min_hours": 1, "max_hours": 4 },      // Was 5-12
  "T3": { "min_hours": 2, "max_hours": 6 }       // Was 8-12
}
```

#### Transit Times Between Facilities
```json
CURRENT VALUES:
"transit_times": {
  "POI_to_Role1": { "min_hours": 1, "max_hours": 4 },
  "Role1_to_Role2": { "min_hours": 2, "max_hours": 6 },
  "Role2_to_Role3": { "min_hours": 4, "max_hours": 8 }
}

RECOMMENDED ADJUSTMENTS:
"transit_times": {
  "POI_to_Role1": { "min_hours": 0.5, "max_hours": 2 },   // Was 1-4
  "Role1_to_Role2": { "min_hours": 1, "max_hours": 3 },    // Was 2-6
  "Role2_to_Role3": { "min_hours": 2, "max_hours": 4 }     // Was 4-8
}
```

### Location: `patient_generator/medical_simulation_bridge.py`

#### Combat Medic Response Times
```python
CURRENT VALUES (lines 160-170):
if is_mass_casualty:
    medic_arrival_minutes = random.randint(60, 240)  # 1-4 hours
else:
    medic_arrival_minutes = random.randint(10, 60)   # 10-60 minutes

RECOMMENDED ADJUSTMENTS:
if is_mass_casualty:
    medic_arrival_minutes = random.randint(30, 90)   # 30-90 minutes
else:
    medic_arrival_minutes = random.randint(5, 30)    # 5-30 minutes
```

---

## 4. TREATMENT EFFECT PARAMETERS

### Location: `medical_simulation/treatment_modifiers.py`

#### Treatment Health Boosts and Deterioration Modifiers
```python
CURRENT VALUES:
self.treatments = {
    "tourniquet": {
        "health_boost": 5,
        "deterioration_modifier": 0.2    # Reduces to 20% of original
    },
    "pressure_bandage": {
        "health_boost": 3,
        "deterioration_modifier": 0.5
    },
    "hemostatic_gauze": {
        "health_boost": 4,
        "deterioration_modifier": 0.4
    },
    "iv_fluids": {
        "health_boost": 10,
        "deterioration_modifier": 0.7
    },
    "blood_transfusion": {
        "health_boost": 20,
        "deterioration_modifier": 0.5
    },
    "surgery": {
        "health_boost": 20,
        "deterioration_modifier": 0.1
    }
}

RECOMMENDED ADJUSTMENTS:
"tourniquet": {
    "health_boost": 10,                  # Was 5
    "deterioration_modifier": 0.3        # Was 0.2
},
"pressure_bandage": {
    "health_boost": 8,                   # Was 3
    "deterioration_modifier": 0.5
},
"hemostatic_gauze": {
    "health_boost": 10,                  # Was 4
    "deterioration_modifier": 0.4
},
"iv_fluids": {
    "health_boost": 15,                  # Was 10
    "deterioration_modifier": 0.6        # Was 0.7
}
```

### Location: `medical_simulation/config/treatment_effects.json`

#### Treatment Stacking Effects
```json
CURRENT VALUES:
"treatment_combinations": {
  "hemorrhage_control": {
    "treatments": ["tourniquet", "pressure_bandage", "hemostatic_gauze"],
    "combined_modifier": 0.3
  },
  "shock_management": {
    "treatments": ["iv_fluids", "blood_transfusion"],
    "combined_modifier": 0.4
  }
}

RECOMMENDED ADJUSTMENTS:
"hemorrhage_control": {
  "combined_modifier": 0.2    // Was 0.3 (better when combined)
},
"shock_management": {
  "combined_modifier": 0.3    // Was 0.4 (better when combined)
}
```

---

## 5. ENVIRONMENTAL FACTORS

### Location: `medical_simulation/deterioration_calculator.py`

#### Environmental Modifiers
```python
CURRENT VALUES:
environmental_factors = {
    "heat_exposure": 1.2,        # 20% faster deterioration
    "cold_exposure": 1.1,        # 10% faster
    "combat_stress": 1.1,        # 10% faster
    "altitude": 1.05             # 5% faster
}

RECOMMENDED ADJUSTMENTS:
environmental_factors = {
    "heat_exposure": 1.1,        # Was 1.2
    "cold_exposure": 1.05,       # Was 1.1
    "combat_stress": 1.05,       # Was 1.1
    "altitude": 1.02             # Was 1.05
}
```

---

## 6. DEATH THRESHOLD PARAMETERS

### Location: `medical_simulation/patient_flow_orchestrator.py`

#### Death Conditions
```python
CURRENT VALUES:
DEATH_THRESHOLD = 0              # Dies when health <= 0
CRITICAL_THRESHOLD = 20          # Enters critical state
STABLE_THRESHOLD = 50            # Considered stable

RECOMMENDED ADJUSTMENTS:
# Keep thresholds the same, adjust deterioration rates instead
```

---

## 7. MASS CASUALTY EVENT PARAMETERS

### Location: `patient_generator/medical_simulation_bridge.py`

#### Mass Casualty Detection
```python
CURRENT VALUES:
is_mass_casualty = random.random() < 0.3  # 30% chance

RECOMMENDED ADJUSTMENTS:
is_mass_casualty = random.random() < 0.15  # 15% chance (less frequent)
```

---

## 8. FACILITY TREATMENT PARAMETERS

### Location: `medical_simulation/config/mtf_capacities.json`

#### Facility Capabilities
```json
CURRENT VALUES:
"Role1": {
  "max_simultaneous_patients": 4,
  "treatment_time_multiplier": 1.5,
  "available_treatments": ["basic", "iv_fluids", "pain_management"]
},
"Role2": {
  "max_simultaneous_patients": 10,
  "treatment_time_multiplier": 1.0,
  "available_treatments": ["all_emergency", "surgery", "blood"]
}

RECOMMENDED ADJUSTMENTS:
"Role1": {
  "max_simultaneous_patients": 6,        // Was 4
  "treatment_time_multiplier": 1.2,      // Was 1.5 (faster)
},
"Role2": {
  "max_simultaneous_patients": 15,       // Was 10
  "treatment_time_multiplier": 0.8,      // Was 1.0 (faster)
}
```

---

## QUICK REFERENCE: KEY PARAMETERS TO ADJUST

### To Reduce Mortality from 100% to ~20%:

1. **Deterioration Rate**: 30 → 10 (severe), 20 → 7 (moderate)
2. **Golden Hour Max**: 2.5x → 1.5x
3. **POI Wait (T1)**: 3-8 hrs → 0.5-2 hrs
4. **Medic Response**: 60-240 min → 30-90 min (mass casualty)
5. **Initial Health**: +15-20 points for all triage levels
6. **Treatment Boost**: +5-10 points for POI treatments
7. **Triage Multipliers**: T1: 2.0 → 1.5, T2: 1.5 → 1.2

---

## TESTING COMMAND

After adjusting parameters, test with:
```bash
ENABLE_TREATMENT_UTILITY_MODEL=true \
ENABLE_MARKOV_CHAIN=true \
ENABLE_WARFARE_MODIFIERS=true \
python3 run_generator.py --patients 100 --output test_mortality --formats json
```

Then analyze mortality in output JSON files.

---

## TARGET METRICS

- **Total Mortality**: 15-25%
- **POI Deaths**: 15-20% of total patients
- **T1 Mortality**: 40-60%
- **T2 Mortality**: 10-20%
- **T3 Mortality**: <5%
- **Average Time to Death**: 2-4 hours (not 30-60 minutes)