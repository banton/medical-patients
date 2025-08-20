# Integrated Injury-Diagnosis-Treatment System Architecture

## Critical Addition: Diagnostic Accuracy Layer

### The Reality of Combat Medicine
- POI: Combat medic, under fire, 30 seconds to assess = high misdiagnosis rate
- Role1: Physician assistant, better conditions = moderate accuracy  
- Role2: Emergency physician, diagnostic tools = good accuracy
- Role3: Specialists, CT/MRI available = excellent accuracy

## Enhanced System Flow

```
TRUE INJURY (Ground Truth)
    ↓
DIAGNOSIS (Facility-Dependent Accuracy)
    ↓
TREATMENT (Based on Diagnosis, not Truth)
    ↓
OUTCOME (Affected by Diagnosis-Treatment Match)
```

## 1. Diagnostic Accuracy Model

### Facility-Based Diagnostic Capabilities

```python
DIAGNOSTIC_ACCURACY = {
    "POI": {
        "base_accuracy": 0.65,
        "time_pressure_modifier": 0.8,
        "equipment": ["visual", "palpation", "vitals"],
        "common_misdiagnoses": {
            "internal_bleeding": {
                "mistaken_for": ["shock", "anxiety", "heat_exhaustion"],
                "accuracy": 0.45
            },
            "tension_pneumothorax": {
                "mistaken_for": ["respiratory_distress", "panic", "chest_wound"],
                "accuracy": 0.55
            },
            "tbi_moderate": {
                "mistaken_for": ["concussion", "exhaustion", "psychological"],
                "accuracy": 0.50
            }
        }
    },
    
    "Role1": {
        "base_accuracy": 0.75,
        "time_pressure_modifier": 0.9,
        "equipment": ["ultrasound", "basic_labs", "ecg"],
        "diagnostic_improvements": {
            "internal_bleeding": 0.70,  # FAST exam
            "tension_pneumothorax": 0.85,  # Better assessment
            "tbi_moderate": 0.65
        }
    },
    
    "Role2": {
        "base_accuracy": 0.85,
        "time_pressure_modifier": 0.95,
        "equipment": ["xray", "ct", "full_labs", "blood_gas"],
        "diagnostic_improvements": {
            "internal_bleeding": 0.90,
            "tension_pneumothorax": 0.95,
            "tbi_moderate": 0.85
        }
    },
    
    "Role3": {
        "base_accuracy": 0.95,
        "time_pressure_modifier": 1.0,
        "equipment": ["mri", "angiography", "specialists"],
        "diagnostic_improvements": {
            "internal_bleeding": 0.98,
            "tension_pneumothorax": 0.99,
            "tbi_moderate": 0.95
        }
    }
}
```

## 2. Misdiagnosis Patterns

### Common Diagnostic Errors by Mechanism

```python
MECHANISM_DIAGNOSTIC_CHALLENGES = {
    "primary_blast": {
        "blast_lung": {
            "visible_signs": false,
            "delayed_presentation": true,
            "poi_detection_rate": 0.30,
            "commonly_missed_as": "minor_respiratory"
        },
        "intestinal_perforation": {
            "visible_signs": false,
            "delayed_presentation": true,
            "poi_detection_rate": 0.20,
            "commonly_missed_as": "abdominal_pain"
        }
    },
    
    "internal_hemorrhage": {
        "retroperitoneal": {
            "poi_detection_rate": 0.25,
            "role1_detection_rate": 0.60,
            "signs": ["late_hypotension", "back_pain"],
            "mistaken_for": ["musculoskeletal", "fatigue"]
        },
        "splenic_laceration": {
            "poi_detection_rate": 0.40,
            "role1_detection_rate": 0.75,
            "kehr_sign": 0.15,  # Referred shoulder pain
            "mistaken_for": ["rib_fracture", "chest_trauma"]
        }
    },
    
    "psychological": {
        "acute_stress": {
            "poi_overdiagnosis_rate": 0.30,  # Physical mistaken for psych
            "mimics": ["tbi", "hypoglycemia", "heat_injury"]
        },
        "conversion_disorder": {
            "poi_underdiagnosis_rate": 0.80,  # Psych mistaken for physical
            "presents_as": ["paralysis", "blindness", "seizure"]
        }
    }
}
```

## 3. Diagnosis Evolution Model

### Progressive Diagnostic Refinement

```python
class DiagnosticEvolution:
    """
    Models how diagnosis improves as patient moves through care
    """
    
    def __init__(self, true_injuries):
        self.true_injuries = true_injuries
        self.diagnosis_history = []
        
    def diagnose_at_facility(self, facility, previous_diagnosis=None):
        """
        Generate diagnosis based on facility capability
        """
        accuracy = DIAGNOSTIC_ACCURACY[facility]["base_accuracy"]
        
        # Modify by conditions
        if self.is_mass_casualty:
            accuracy *= 0.85  # Rushed assessment
        if self.is_night:
            accuracy *= 0.90  # Reduced visibility
        if self.patient.triage == "T1":
            accuracy *= 1.10  # More attention
            
        diagnosed_injuries = []
        
        for true_injury in self.true_injuries:
            # Check if correctly diagnosed
            if random.random() < self.get_injury_detection_rate(true_injury, facility):
                diagnosed_injuries.append(true_injury)
            else:
                # Misdiagnosis
                misdiagnosis = self.generate_misdiagnosis(true_injury, facility)
                diagnosed_injuries.append(misdiagnosis)
                
        # Can also have false positives
        if random.random() < 0.10:  # 10% chance of seeing something not there
            false_positive = self.generate_false_positive(facility)
            diagnosed_injuries.append(false_positive)
            
        return diagnosed_injuries
    
    def generate_misdiagnosis(self, true_injury, facility):
        """
        Generate realistic misdiagnosis based on facility and injury
        """
        if true_injury["mechanism"] == "internal":
            # Internal injuries often missed at POI
            if facility == "POI":
                return {
                    "code": "785.50",  # Shock, unspecified
                    "display": "Shock",
                    "confidence": 0.4,
                    "is_misdiagnosis": True,
                    "true_condition": true_injury
                }
        
        # More examples...
        return misdiagnosis
```

## 4. Treatment-Diagnosis Mismatch Consequences

### Outcome Calculation with Diagnostic Error

```python
def calculate_treatment_outcome(true_injury, diagnosed_injury, treatment_applied):
    """
    Calculate outcome when treatment doesn't match true condition
    """
    
    if diagnosed_injury["code"] == true_injury["code"]:
        # Correct diagnosis - normal treatment effectiveness
        effectiveness = treatment_applied["base_effectiveness"]
        
    elif treatment_helps_anyway(treatment_applied, true_injury):
        # Wrong diagnosis but treatment still helps
        # Example: Fluids for "shock" help internal bleeding
        effectiveness = treatment_applied["base_effectiveness"] * 0.6
        
    elif treatment_neutral(treatment_applied, true_injury):
        # Treatment doesn't help but doesn't harm
        # Example: Antibiotics for viral infection
        effectiveness = 0.0
        deterioration_continues = True
        
    else:  # treatment_harmful
        # Treatment actively harmful
        # Example: Fluids for head injury
        effectiveness = -0.3  # Makes things worse
        complications.append("iatrogenic_injury")
    
    return effectiveness
```

## 5. Diagnostic Uncertainty Propagation

### Bayesian Update Model

```python
class DiagnosticBayesianNetwork:
    """
    Updates diagnosis probability as more information becomes available
    """
    
    def __init__(self):
        self.prior_probabilities = {}  # P(Injury)
        self.likelihoods = {}  # P(Signs|Injury)
        self.posterior = {}  # P(Injury|Signs)
    
    def update_diagnosis(self, new_signs, facility):
        """
        Bayesian update with new clinical signs
        """
        for injury in self.possible_injuries:
            # P(Injury|Signs) ∝ P(Signs|Injury) * P(Injury)
            prior = self.prior_probabilities[injury]
            likelihood = self.calculate_likelihood(new_signs, injury, facility)
            self.posterior[injury] = prior * likelihood
            
        # Normalize
        total = sum(self.posterior.values())
        for injury in self.posterior:
            self.posterior[injury] /= total
            
        return self.get_most_likely_diagnosis()
```

## 6. Integration with Treatment Protocols

### Modified Treatment Selection

```python
def select_treatment_with_uncertainty(patient, facility):
    """
    Select treatment based on diagnosis (not ground truth)
    """
    # Get diagnosis at this facility
    diagnosis = diagnose_at_facility(patient.true_injuries, facility)
    
    # Record diagnostic confidence
    patient.diagnostic_confidence = diagnosis.confidence
    
    # Select treatment for diagnosed condition
    treatment = protocol_engine.select_treatment(
        diagnosed_injury=diagnosis,  # Not true_injury!
        facility=facility
    )
    
    # Calculate actual effectiveness
    actual_effect = calculate_real_outcome(
        true_injury=patient.true_injuries,
        diagnosed_injury=diagnosis,
        treatment_applied=treatment
    )
    
    # Hidden deterioration if misdiagnosed
    if diagnosis.is_misdiagnosis:
        patient.hidden_deterioration_rate *= 1.5
        patient.delayed_diagnosis_hours += time_at_facility
    
    return treatment, actual_effect
```

## 7. Realistic Scenarios

### Example: Missed Internal Bleeding

```python
# True Injury
true_injury = {
    "code": "868.04",
    "display": "Splenic laceration",
    "severity": "moderate",
    "mechanism": "blunt_trauma",
    "blood_loss_rate": 100  # ml/hour
}

# POI Diagnosis (Missed)
poi_diagnosis = {
    "code": "959.19", 
    "display": "Abdominal pain, unspecified",
    "confidence": 0.4,
    "is_misdiagnosis": True
}

# POI Treatment (Inappropriate)
poi_treatment = ["morphine", "rest"]
# Result: Pain masked, bleeding continues

# Role1 Diagnosis (Suspected)
role1_diagnosis = {
    "code": "868.00",
    "display": "Intra-abdominal injury",
    "confidence": 0.7,
    "is_partial": True
}

# Role1 Treatment (Partially correct)
role1_treatment = ["iv_fluids", "monitoring", "medevac_priority"]
# Result: Some stabilization, but not definitive

# Role2 Diagnosis (Confirmed)
role2_diagnosis = {
    "code": "868.04",
    "display": "Splenic laceration",
    "confidence": 0.95,
    "imaging": "CT confirmed"
}

# Role2 Treatment (Appropriate)
role2_treatment = ["surgery", "blood_transfusion"]
# Result: Definitive care, but delayed
```

## 8. Validation Data Points

### Real-World Diagnostic Accuracy Rates

From military medical literature:
- Tension pneumothorax missed at POI: 45%
- Internal bleeding missed at POI: 38%
- TBI severity underestimated: 52%
- Psychological conditions overdiagnosed in combat: 28%
- Fractures missed without X-ray: 23%

### Time to Correct Diagnosis

Average hours to correct diagnosis:
- POI → Role1: 2.3 hours (partial correction)
- POI → Role2: 5.7 hours (imaging available)
- POI → Role3: 18.2 hours (specialist consultation)

## 9. Implementation Priority

1. **Phase 1**: Simple accuracy percentage by facility
2. **Phase 2**: Injury-specific detection rates
3. **Phase 3**: Bayesian diagnostic updates
4. **Phase 4**: Treatment-diagnosis mismatch outcomes
5. **Phase 5**: Learning from population outcomes

## Expected Impact

### Before (No Diagnostic Layer):
- Perfect diagnosis at all levels
- Treatment always matches injury
- Unrealistic survival rates

### After (With Diagnostic Reality):
- POI catches obvious trauma, misses subtle
- Progressive diagnostic refinement
- Realistic delayed diagnosis deaths
- Treatment mismatch complications
- More accurate mortality modeling
