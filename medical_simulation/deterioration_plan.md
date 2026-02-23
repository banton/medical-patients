# Simplified Deterioration Model - Implementation Plan

## Executive Summary
This document outlines the implementation plan for a simplified health deterioration system that tracks patient health states through a single health score (0-100) and deterioration rates, avoiding the complexity of individual vital signs while maintaining realistic medical simulation.

## Core Concepts

### 1. Health Score Model
- **Range**: 0 (dead) to 100 (healthy)
- **Initial Value**: Based on injury severity
- **Deterioration**: Linear decay with modifiers
- **Stochastic Variation**: ±20% randomness for realism

### 2. Triage Mapping
- **T3 (Walking Wounded)**: Health > 70
- **T2 (Delayed)**: Health 40-70
- **T1 (Immediate)**: Health 10-40
- **Expectant**: Health < 10

### 3. Blood Volume Tracking
- **Range**: 0-100% of normal volume
- **Only for**: Hemorrhaging patients
- **Critical Threshold**: 40% (accelerates deterioration)
- **Death Threshold**: 30%

## Configuration Files Structure

### 1. deterioration_rates.json
```json
{
  "version": "3.0",
  "injury_deterioration_rates": {
    "battle_trauma": {
      "gsw": {
        "base_rate": 25,
        "variance": 5,
        "initial_health": 60
      },
      "shrapnel": {
        "base_rate": 15,
        "variance": 3,
        "initial_health": 70
      },
      "blast": {
        "base_rate": 30,
        "variance": 6,
        "initial_health": 55
      },
      "burn": {
        "base_rate": 20,
        "variance": 4,
        "initial_health": 65
      },
      "tbi": {
        "base_rate": 35,
        "variance": 7,
        "initial_health": 50
      },
      "amputation": {
        "base_rate": 40,
        "variance": 8,
        "initial_health": 45
      }
    },
    "non_battle_injury": {
      "fracture": {
        "base_rate": 5,
        "variance": 2,
        "initial_health": 85
      },
      "heat_injury": {
        "base_rate": 10,
        "variance": 3,
        "initial_health": 75
      },
      "vehicle_accident": {
        "base_rate": 20,
        "variance": 5,
        "initial_health": 65
      }
    },
    "disease": {
      "respiratory": {
        "base_rate": 8,
        "variance": 2,
        "initial_health": 80
      },
      "gastroenteritis": {
        "base_rate": 6,
        "variance": 2,
        "initial_health": 85
      },
      "infection": {
        "base_rate": 12,
        "variance": 3,
        "initial_health": 75
      }
    }
  },
  "triage_thresholds": {
    "T3": 70,
    "T2": 40,
    "T1": 10,
    "Expectant": 0
  },
  "deterioration_modifiers": {
    "complications": {
      "untreated_hemorrhage": 2.0,
      "airway_compromise": 3.0,
      "shock": 2.5,
      "sepsis": 1.8,
      "organ_failure": 2.2
    },
    "treatments": {
      "tourniquet_applied": 0.5,
      "pressure_bandage": 0.7,
      "airway_secured": 0.4,
      "iv_fluids": 0.8,
      "antibiotics": 0.9,
      "surgery_completed": 0.3
    },
    "environmental": {
      "extreme_heat": 1.3,
      "extreme_cold": 1.4,
      "high_altitude": 1.2,
      "contaminated_environment": 1.5
    },
    "time_factors": {
      "golden_hour": 0.3,
      "within_3_hours": 0.5,
      "within_6_hours": 0.7,
      "delayed_over_6_hours": 1.5
    }
  }
}
```

### 2. blood_loss.json
```json
{
  "version": "3.0",
  "hemorrhage_profiles": {
    "minor": {
      "blood_loss_rate": 5,
      "variance": 1,
      "controllable": true,
      "tourniquet_effectiveness": 0.95
    },
    "moderate": {
      "blood_loss_rate": 15,
      "variance": 3,
      "controllable": true,
      "tourniquet_effectiveness": 0.85
    },
    "severe": {
      "blood_loss_rate": 30,
      "variance": 5,
      "controllable": false,
      "surgical_requirement": true
    },
    "catastrophic": {
      "blood_loss_rate": 60,
      "variance": 10,
      "controllable": false,
      "immediate_surgery_required": true
    }
  },
  "blood_volume_thresholds": {
    "normal": 100,
    "needs_transfusion": 60,
    "critical": 40,
    "death": 30
  },
  "transfusion_effects": {
    "units_per_treatment": 2,
    "volume_restored_per_unit": 10,
    "max_units_per_hour": 4
  }
}
```

### 3. treatment_effects.json
```json
{
  "version": "3.0",
  "treatments": {
    "immediate_interventions": {
      "tourniquet": {
        "deterioration_modifier": 0.5,
        "blood_loss_modifier": 0.1,
        "application_time_minutes": 2,
        "skill_required": "basic"
      },
      "pressure_bandage": {
        "deterioration_modifier": 0.7,
        "blood_loss_modifier": 0.5,
        "application_time_minutes": 5,
        "skill_required": "basic"
      },
      "airway_management": {
        "deterioration_modifier": 0.4,
        "application_time_minutes": 10,
        "skill_required": "advanced"
      }
    },
    "medical_treatments": {
      "iv_fluids": {
        "deterioration_modifier": 0.8,
        "blood_volume_boost": 10,
        "duration_minutes": 30,
        "skill_required": "intermediate"
      },
      "blood_transfusion": {
        "deterioration_modifier": 0.6,
        "blood_volume_boost": 20,
        "duration_minutes": 60,
        "skill_required": "intermediate"
      },
      "surgery": {
        "deterioration_modifier": 0.3,
        "fixes_hemorrhage": true,
        "duration_minutes": 120,
        "skill_required": "expert"
      }
    }
  },
  "treatment_availability": {
    "point_of_injury": ["tourniquet", "pressure_bandage"],
    "role1": ["tourniquet", "pressure_bandage", "airway_management", "iv_fluids"],
    "role2": ["all_immediate", "iv_fluids", "blood_transfusion"],
    "role3": ["all"]
  }
}
```

## Implementation Modules

### 1. deterioration_engine.py
```python
"""
Core deterioration calculation engine
- Calculate health score at any time point
- Apply modifiers dynamically
- Track state transitions
- Generate deterioration timeline
"""

class DeteriorationEngine:
    def __init__(self, config_loader):
        self.rates = config_loader.get_deterioration_rates()
        self.modifiers = config_loader.get_modifiers()
        
    def calculate_health_state(self, patient, elapsed_hours):
        """Calculate current health score"""
        
    def get_deterioration_rate(self, injury_type, modifiers):
        """Calculate effective deterioration rate"""
        
    def apply_treatment(self, patient, treatment_type):
        """Apply treatment effects to patient"""
        
    def predict_triage_transition(self, patient):
        """Predict when patient will transition triage categories"""
```

### 2. blood_loss_tracker.py
```python
"""
Blood volume and hemorrhage tracking
- Track blood volume over time
- Calculate transfusion requirements
- Determine criticality
"""

class BloodLossTracker:
    def __init__(self, config_loader):
        self.profiles = config_loader.get_hemorrhage_profiles()
        self.thresholds = config_loader.get_blood_thresholds()
        
    def calculate_blood_loss(self, hemorrhage_type, elapsed_hours):
        """Calculate blood volume remaining"""
        
    def apply_transfusion(self, patient, units):
        """Apply blood transfusion effects"""
        
    def is_critical(self, blood_volume):
        """Check if blood loss is critical"""
```

### 3. health_state_manager.py
```python
"""
Orchestrator for health state management
- Coordinate deterioration and blood loss
- Manage treatment applications
- Generate timeline events
"""

class HealthStateManager:
    def __init__(self, deterioration_engine, blood_tracker):
        self.deterioration = deterioration_engine
        self.blood = blood_tracker
        
    def update_patient_state(self, patient, elapsed_time):
        """Update all health parameters"""
        
    def generate_timeline(self, patient, duration_hours):
        """Generate complete health timeline"""
        
    def apply_intervention(self, patient, intervention_type, time):
        """Apply medical intervention at specific time"""
```

## Database Schema Changes

### New Tables

```sql
-- health_states table
CREATE TABLE health_states (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    timestamp TIMESTAMP NOT NULL,
    health_score DECIMAL(5,2) NOT NULL,
    blood_volume DECIMAL(5,2),
    triage_category VARCHAR(10) NOT NULL,
    deterioration_rate DECIMAL(5,2) NOT NULL,
    active_modifiers JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- treatment_applications table
CREATE TABLE treatment_applications (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    treatment_type VARCHAR(50) NOT NULL,
    applied_at TIMESTAMP NOT NULL,
    location VARCHAR(20),  -- POI, Role1, Role2, Role3
    effectiveness DECIMAL(3,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- hemorrhage_tracking table
CREATE TABLE hemorrhage_tracking (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER REFERENCES patients(id),
    severity VARCHAR(20) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    blood_loss_rate DECIMAL(5,2) NOT NULL,
    controlled BOOLEAN DEFAULT FALSE,
    control_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Modified Tables

```sql
-- Add to patients table
ALTER TABLE patients ADD COLUMN initial_health_score DECIMAL(5,2);
ALTER TABLE patients ADD COLUMN current_health_score DECIMAL(5,2);
ALTER TABLE patients ADD COLUMN blood_volume_percent DECIMAL(5,2) DEFAULT 100;
ALTER TABLE patients ADD COLUMN has_active_hemorrhage BOOLEAN DEFAULT FALSE;
```

## API Endpoints

### Health State Endpoints

```yaml
/api/v1/health/calculate:
  post:
    description: Calculate current health state
    parameters:
      - patient_id
      - elapsed_hours
      - active_modifiers
    response:
      - health_score
      - triage_category
      - deterioration_rate
      - blood_volume

/api/v1/health/timeline:
  get:
    description: Get health timeline for patient
    parameters:
      - patient_id
      - duration_hours
    response:
      - timeline_events[]
      - critical_points[]
      - treatments_applied[]

/api/v1/health/apply_treatment:
  post:
    description: Apply treatment to patient
    parameters:
      - patient_id
      - treatment_type
      - application_time
    response:
      - treatment_effect
      - new_health_state
```

## Testing Strategy

### Unit Tests
1. Test deterioration rate calculations
2. Test modifier applications
3. Test blood loss calculations
4. Test triage transitions
5. Test treatment effects

### Integration Tests
1. Test full patient timeline generation
2. Test multiple treatment interactions
3. Test database persistence
4. Test API endpoints

### Validation Tests
1. Compare against known medical patterns
2. Validate triage distribution
3. Verify mortality rates
4. Check golden hour effects

## Implementation Timeline

### Week 1: Foundation
- [ ] Create configuration files
- [ ] Implement deterioration_engine.py
- [ ] Implement blood_loss_tracker.py
- [ ] Write unit tests

### Week 2: Integration
- [ ] Implement health_state_manager.py
- [ ] Extend Patient model
- [ ] Create database migrations
- [ ] Integration with patient generator

### Week 3: API & Persistence
- [ ] Create API endpoints
- [ ] Implement database layer
- [ ] Add caching for performance
- [ ] Write integration tests

### Week 4: Polish & Validation
- [ ] Performance optimization
- [ ] Comprehensive testing
- [ ] Documentation
- [ ] Validation against medical data

## Success Metrics

1. **Simplicity**: < 500 lines of core code
2. **Performance**: < 10ms per health calculation
3. **Accuracy**: ±10% of expected mortality rates
4. **Coverage**: > 90% test coverage
5. **Usability**: Clear, intuitive configuration

## Risk Mitigation

1. **Over-simplification**: Validate against medical data
2. **Performance**: Cache calculations, optimize queries
3. **Configuration complexity**: Provide sensible defaults
4. **Integration issues**: Use feature flags for rollout

## Next Steps

1. Review and approve plan
2. Create feature branch
3. Implement configuration files
4. Begin core module development
5. Set up testing framework

---

*This plan provides a practical, implementable approach to health deterioration that balances realism with simplicity.*