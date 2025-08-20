# Treatment Protocol System - Implementation Plan

## Problem Statement
Currently, the system applies random treatments to injuries without medical logic. We need a probabilistic system that:
- Maps injuries to medically appropriate treatments
- Considers facility capabilities and resource constraints
- Models treatment sequences and dependencies
- Incorporates temporal factors and deterioration

## Proposed Architecture

### 1. Treatment Protocol Engine (`treatment_protocol_engine.py`)

#### Core Components:

**A. Injury-Treatment Mapping Structure**
```
INJURY_TREATMENT_PROTOCOLS = {
    "injury_code": {
        "primary_treatments": [
            {"treatment": "tourniquet", "probability": 0.95, "indication": "extremity_hemorrhage"},
            {"treatment": "pressure_bandage", "probability": 0.8, "indication": "moderate_bleeding"}
        ],
        "supportive_treatments": [
            {"treatment": "iv_fluids", "probability": 0.7, "indication": "volume_loss"},
            {"treatment": "pain_management", "probability": 0.9, "indication": "pain_control"}
        ],
        "definitive_treatments": [
            {"treatment": "surgery", "probability": 0.6, "indication": "internal_injury"}
        ]
    }
}
```

**B. Treatment Decision Tree**
- Use Bayesian network for treatment dependencies
- Model: P(Treatment|Injury, Facility, Resources, Time)
- Incorporate contraindications and complications

**C. Temporal Treatment Sequencing**
- Treatment phases: Immediate → Stabilization → Definitive
- Time windows for effectiveness (golden hour effects)
- Treatment expiration (tourniquet timing)

### 2. Resource Management System (`resource_manager.py`)

**A. Resource Tracking**
```
FACILITY_RESOURCES = {
    "role2": {
        "blood_units": {"initial": 20, "replenish_rate": 2/hour},
        "operating_rooms": {"capacity": 2, "surgery_duration": 2 hours},
        "personnel": {"surgeons": 2, "nurses": 6}
    }
}
```

**B. Resource Allocation Algorithm**
- Priority queue based on triage category
- Stochastic availability during mass casualties
- Resource exhaustion protocols

### 3. Treatment Effectiveness Model (`treatment_effectiveness.py`)

**A. Success Rate Calculation**
```
effectiveness = base_effectiveness 
    * facility_modifier 
    * time_modifier 
    * personnel_skill_modifier 
    * resource_availability_modifier
```

**B. Complication Modeling**
- Infection risk over time
- Treatment interactions
- Adverse reactions

### 4. Clinical Pathways (`clinical_pathways.json`)

Structured treatment protocols by injury pattern:

```json
{
  "hemorrhagic_shock": {
    "phases": {
      "immediate": ["tourniquet", "pressure_bandage"],
      "stabilization": ["iv_access", "blood_transfusion"],
      "definitive": ["surgery"]
    },
    "decision_points": {
      "blood_pressure < 90": "expedite_surgery",
      "hemoglobin < 7": "massive_transfusion_protocol"
    }
  }
}
```

## Integration Points

### 1. Modify `medical.py`
Add treatment indication tags to injuries:
```python
self.battle_trauma_conditions = [
    {
        "code": "262574004", 
        "display": "Bullet wound",
        "indications": ["hemorrhage_control", "surgery", "antibiotics"]
    }
]
```

### 2. Extend `patient.py`
Add treatment tracking:
```python
class Patient:
    def __init__(self):
        self.treatment_plan = []  # Ordered treatment sequence
        self.treatments_received = []  # Completed treatments
        self.treatment_outcomes = []  # Success/complications
        self.contraindications = []  # Patient-specific
```

### 3. Connect to `flow_simulator.py`
Replace random treatment generation:
```python
def _generate_treatments(self, patient, facility):
    protocol_engine = TreatmentProtocolEngine()
    return protocol_engine.select_treatments(
        injuries=patient.primary_conditions,
        facility=facility,
        triage=patient.triage_category,
        time_since_injury=patient.get_hours_since_injury()
    )
```

## Probability Distributions

### 1. Treatment Selection
**Multinomial Distribution** for treatment choice:
- Parameters derived from injury severity and facility
- P(treatment_i | injury_j, facility_k) from clinical guidelines

### 2. Treatment Timing
**Exponential Distribution** for time to treatment:
- λ = 1/mean_treatment_time
- Modified by triage priority and resource availability

### 3. Complication Risk
**Beta Distribution** for complication probability:
- α, β parameters from historical complication rates
- Updated via Bayesian inference with outcomes

### 4. Resource Availability
**Poisson Process** for resource consumption:
- Models arrival of casualties and resource depletion
- Queue theory for OR availability

## Validation Strategy

### 1. Clinical Accuracy
- Compare treatment sequences to Tactical Combat Casualty Care (TCCC) guidelines
- Validate against Joint Trauma System Clinical Practice Guidelines

### 2. Statistical Validation
- Monte Carlo simulation of 10,000 casualty scenarios
- Compare mortality rates to published military medical data
- Sensitivity analysis on key parameters

### 3. Edge Case Handling
- Mass casualty resource exhaustion
- Psychological conditions at combat facilities (limited to buddy care)
- Disease management in trauma facilities (supportive care only)

## Implementation Phases

### Phase 1: Core Protocol Engine (Week 1)
1. Create injury-treatment mapping database
2. Implement basic treatment selection algorithm
3. Add facility capability constraints

### Phase 2: Temporal & Sequential Logic (Week 2)
1. Add treatment sequencing rules
2. Implement golden hour effects
3. Add treatment expiration logic

### Phase 3: Resource Management (Week 3)
1. Implement resource tracking
2. Add mass casualty degradation
3. Create priority queuing system

### Phase 4: Probabilistic Enhancements (Week 4)
1. Add Bayesian network for dependencies
2. Implement complication modeling
3. Add learning from outcomes

## Key Design Decisions

### 1. Why Bayesian Networks?
- Natural representation of medical decision-making
- Handles uncertainty and missing information
- Can incorporate expert knowledge and data

### 2. Why Not Pure Monte Carlo?
- Too computationally expensive for real-time
- Lacks explainability for medical validation
- Harder to incorporate clinical guidelines

### 3. Temporal Modeling Approach
- Discrete time steps (5-minute intervals)
- State transitions at each step
- Allows for interrupted treatments

## Files to Create

1. `patient_generator/treatment_protocol_engine.py` - Main protocol logic
2. `patient_generator/resource_manager.py` - Resource tracking
3. `patient_generator/treatment_effectiveness.py` - Outcome modeling
4. `patient_generator/config/clinical_pathways.json` - Treatment protocols
5. `patient_generator/config/injury_treatment_map.json` - Injury-treatment mappings
6. `tests/test_treatment_protocols.py` - Validation tests

## Configuration Schema

```json
{
  "injury_treatment_mappings": {
    "262574004": {  // Bullet wound
      "name": "Gunshot Wound Protocol",
      "treatments": {
        "immediate": {
          "hemorrhage_control": {
            "options": ["tourniquet", "pressure_bandage"],
            "selection": "severity_based",
            "probability_weights": [0.7, 0.3]
          }
        },
        "stabilization": {
          "resuscitation": {
            "options": ["iv_fluids", "blood_transfusion"],
            "selection": "sequential",
            "trigger": "blood_pressure < 90"
          }
        }
      }
    }
  },
  
  "treatment_dependencies": {
    "blood_transfusion": {
      "requires": ["iv_access"],
      "contraindications": ["no_crossmatch"],
      "complications": {
        "transfusion_reaction": 0.02,
        "volume_overload": 0.05
      }
    }
  },
  
  "facility_capabilities": {
    "role1": {
      "max_treatment_level": "immediate",
      "skill_modifier": 0.8,
      "resource_constraints": {
        "tourniquets": 10,
        "iv_kits": 20
      }
    }
  }
}
```

## Success Metrics

1. **Clinical Appropriateness**: >95% of treatments match clinical guidelines
2. **Mortality Accuracy**: Within 5% of published military casualty data
3. **Resource Utilization**: Realistic depletion during mass casualties
4. **Temporal Accuracy**: Treatment timing matches golden hour principles
5. **Edge Case Handling**: Appropriate degradation under constraints

## Next Steps

1. Review plan with medical SMEs
2. Gather treatment probability data from literature
3. Create minimal viable protocol engine
4. Test with representative injury patterns
5. Iterate based on validation results
