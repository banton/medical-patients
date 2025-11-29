# QUICK IMPLEMENTATION CHECKLIST

## Priority 1: Connect Warfare Context (2 hours)

### Create: `warfare_context_manager.py`
```python
class WarfareContextManager:
    - Load warfare_patterns.json
    - Track which warfare type generated each patient
    - Provide injury_modifier and triage_weights from warfare data
```

### Modify: `flow_simulator.py`
- Line ~100: Use warfare-specific triage weights
- Line ~400: Pass warfare context to patient creation
- Add: `self.warfare_context_mgr` 

## Priority 2: Mechanism-Based Injuries (4 hours)

### Create: `injury_mechanism_system.py`
```python
MECHANISMS = {
    "primary_blast": {...},
    "secondary_blast": {...},
    "ballistic": {...}
}

WARFARE_MECHANISM_PROFILES = {
    "artillery": {"primary_blast": 0.7, "secondary_blast": 0.9},
    "urban": {"ballistic": 0.4, "crush": 0.2}
}
```

### Key Functions:
- `generate_injuries_for_warfare(warfare_type)` → multi-injury pattern
- `_apply_mechanism(mechanism)` → specific injuries
- `_correlate_severities()` → realistic correlation

## Priority 3: Treatment Protocols (4 hours)

### Create: `treatment_protocol_engine.py`
```python
def select_treatments(injury_codes, facility, triage, time_since_injury):
    1. Categorize injuries (hemorrhage, airway, fracture, etc.)
    2. Get protocol for category
    3. Filter by facility capability
    4. Apply probability distribution
    5. Check contraindications
```

### Use existing: `/patient_generator/config/injury_treatment_map.json`

### Modify: `flow_simulator.py` line ~450
Replace random treatment with protocol engine call

## Priority 4: Diagnostic Accuracy (3 hours)

### Create: `diagnostic_accuracy_model.py`
```python
DIAGNOSTIC_ACCURACY = {
    "POI": 0.65,
    "Role1": 0.75,
    "Role2": 0.85,
    "Role3": 0.95
}

def diagnose_at_facility(true_injuries, facility):
    - Apply facility accuracy
    - Generate misdiagnosis for missed injuries
    - Return diagnosed_injuries (not true!)
```

### Integration:
- Diagnosis happens BEFORE treatment selection
- Treatment based on diagnosis, not true injury
- Outcome depends on diagnosis-treatment-truth alignment

## Priority 5: Non-Linear Health (2 hours)

### Connect existing: `health_score_engine.py`
- Already has deterioration models
- Just needs to be called

### Modify: `patient.py`
```python
def calculate_health_trajectory():
    - Get initial health from injury severity
    - Apply deterioration model
    - Add cliff events (5% chance/hour)
    - Return trajectory with phases
```

## Testing Checkpoints

After each priority:
1. Generate 10 patients
2. Verify expected behavior
3. Check output makes medical sense
4. Compare to baseline mortality

## File Mapping

NEW FILES NEEDED:
- `warfare_context_manager.py`
- `injury_mechanism_system.py`  
- `treatment_protocol_engine.py`
- `diagnostic_accuracy_model.py`

EXISTING FILES TO MODIFY:
- `flow_simulator.py` (3 locations)
- `patient.py` (add fields and methods)
- `patient_generation_service.py` (call new modules)

EXISTING FILES TO USE AS-IS:
- `warfare_patterns.json` (data source)
- `health_score_engine.py` (deterioration)
- `injury_treatment_map.json` (protocols)
- `treatment_effects.json` (modifiers)

## Key Formulas

**Injury Count**: `n ~ Poisson(λ=3)` for shrapnel

**Health Decay**: `H(t) = L/(1 + e^(-k(t-t0)))` where t0=golden hour

**Diagnostic Accuracy**: `P(correct) = base_accuracy * facility_mod * time_pressure`

**Treatment Effect**: `E = base * golden_hour_mod * resource_mod * skill_mod`

## Remember
- Warfare context is lost between temporal_generator and patient creation - THIS IS THE KEY FIX
- Diagnosis ≠ Truth (critical for realism)
- Mechanisms generate patterns, not individual injuries
- Golden hour is real: tourniquet at 6 hours can cause amputation
