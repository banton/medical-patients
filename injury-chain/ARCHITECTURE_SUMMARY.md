# Military Medical Patient Generator - Comprehensive Architecture Summary

## Project Context
Military medical simulation system at `/Users/banton/Sites/medical-patients` that generates realistic casualty flows through evacuation chain (POI → Role1 → Role2 → Role3 → Role4).

## Current System Analysis

### Core Files Structure
```
/patient_generator/
  - flow_simulator.py (main patient flow logic)
  - medical.py (basic injury lists)
  - temporal_generator.py (casualty event timing)
  - warfare_patterns.json (rich but underutilized)
  - injuries.json (has deterioration models)
  - patient.py (patient data model)
  - medical_simulation_bridge.py (optional enhancement)

/medical_simulation/
  - health_score_engine.py (unused non-linear health)
  - deterioration_calculator.py (unused realistic deterioration)
  - config/
    - complications.json (detailed complication models)
    - blood_loss.json (hemorrhage patterns)
    - treatment_effects.json (treatment definitions)
```

### Critical Problems Identified

1. **Linear Health Deterioration**: Despite having sophisticated models, uses simple linear decline
2. **Disconnected Warfare Patterns**: `warfare_patterns.json` has rich data but doesn't influence injury generation
3. **Random Treatment Assignment**: No medical logic connecting injuries to treatments
4. **No Diagnostic Layer**: Perfect diagnosis at all facilities (unrealistic)
5. **No Multi-Injury Patterns**: Single random injuries instead of realistic polytrauma

## Proposed Three-Layer Architecture

### Layer 1: Mechanism-Based Injury Generation

**Core Concept**: Warfare Type → Injury Mechanisms → Specific Injuries

```python
WARFARE → MECHANISMS → INJURIES
artillery → [primary_blast, secondary_blast, tertiary_blast] → polytrauma pattern
urban → [ballistic, crush, thermal] → location-based injuries  
IED → [blast + fragments] → classic triad (TBI + amputation + burns)
```

**Key Design Decisions**:
- Use ~50 mechanism combinations instead of thousands of injury mappings
- Mechanisms naturally create correlated injuries (blast → multiple related injuries)
- Based on military medical literature patterns

**Files Created**:
- `/TREATMENT_PROTOCOL_PLAN.md` - Overall implementation plan
- `/patient_generator/config/injury_treatment_map.json` - Initial mappings

### Layer 2: Diagnostic Accuracy Model

**Core Concept**: True Injury → Facility-Dependent Diagnosis → Treatment Based on Diagnosis

```python
DIAGNOSTIC_ACCURACY = {
    "POI": 0.65,    # Combat medic under fire
    "Role1": 0.75,  # PA with ultrasound
    "Role2": 0.85,  # ER doc with CT
    "Role3": 0.95   # Specialists with MRI
}
```

**Key Insights**:
- Internal bleeding missed 38% at POI
- Blast lung often has delayed presentation
- Misdiagnosis leads to wrong treatment → worse outcomes
- Progressive diagnostic refinement as patient moves through care

**File Created**:
- `/DIAGNOSTIC_ACCURACY_SYSTEM.md` - Complete diagnostic layer specification

### Layer 3: Treatment Protocol Engine

**Core Concept**: Diagnosis + Facility + Resources → Medically Appropriate Treatment

```python
Treatment Selection = f(
    diagnosed_injuries,  # Not true injuries!
    facility_capabilities,
    triage_priority,
    time_since_injury,
    resource_availability
)
```

**Key Features**:
- Treatment sequences (tourniquet → IV → transfusion → surgery)
- Golden hour effects (effectiveness decays over time)
- Resource exhaustion during mass casualties
- Contraindications and complications

**Files Created**:
- `/TREATMENT_IMPLEMENTATION_GUIDE.md` - Implementation details
- `/patient_generator/config/injury_treatment_map.json` - Protocol mappings

## Integration Points with Current Code

### 1. In `flow_simulator.py`:
- Line ~100: Replace static `_triage_weights` with warfare-specific weights
- Line ~400: Add warfare context to `_create_initial_patient()`
- Line ~450: Replace random treatment with protocol engine

### 2. In `patient.py`:
- Add: `injury_mechanisms`, `diagnostic_history`, `treatment_protocols`
- Add: `calculate_health_trajectory()` for non-linear progression

### 3. New Connections:
- `temporal_generator.py` CasualtyEvents → pass warfare context to patients
- Use existing `health_score_engine.py` for non-linear deterioration
- Connect `treatment_effects.json` to actual treatment selection

## Mathematical Models

### 1. Injury Generation
- **Poisson** for fragment counts: `count ~ Poisson(λ=3)`
- **Gaussian Copula** for severity correlation between injuries
- **Beta** for burn surface area: `BSA ~ Beta(2,5) * 60`

### 2. Health Progression
- **Logistic Deterioration**: `health(t) = L / (1 + e^(-k(t-t0)))`
- **Cliff Events**: 5% probability/hour of sudden 15-30 point drop
- **Phases**: Compensatory (0-2h) → Decompensation (2-6h) → Critical (6+h)

### 3. Treatment Selection
- **Bayesian Network**: P(Treatment|Injury, Facility, Resources, Time)
- **Resource Queue**: M/M/c model for OR availability
- **Effectiveness Decay**: `effectiveness(t) = base * exp(-λ(t - t_golden))`

## Validation Approach

1. **Clinical**: Compare to TCCC guidelines and Joint Trauma System CPGs
2. **Statistical**: Monte Carlo 10,000 patients, compare mortality to published rates
3. **Edge Cases**: Mass casualties, psychological conditions, resource exhaustion

## Implementation Priority

**Week 1**: Mechanism-based injury generation
**Week 2**: Treatment protocol engine with basic mappings
**Week 3**: Diagnostic accuracy layer
**Week 4**: Non-linear health progression integration

## Key Insights from Codebase Analysis

1. **Underutilized Assets**: Rich models exist in `medical_simulation/` folder but aren't connected
2. **Warfare Patterns**: Comprehensive `warfare_patterns.json` only used for timing, not injury types
3. **Missing Link**: No connection between warfare context and individual patient creation
4. **Treatment Logic**: `treatment_effects.json` exists but no logic for when to apply

## Critical Design Decisions

1. **Mechanism-Based**: More maintainable than exhaustive injury lists
2. **Diagnostic Layer**: Essential for realistic mortality (misdiagnosis → delays → death)
3. **Bayesian Approach**: Natural fit for medical uncertainty and decision-making
4. **Phased Implementation**: Can integrate incrementally without breaking existing system

## Next Session Focus Areas

1. Connect warfare context from temporal_generator to patient creation
2. Implement mechanism-based injury generation
3. Create treatment protocol engine
4. Add diagnostic accuracy layer
5. Integrate existing non-linear health models

## Questions to Address

1. How to handle combination injuries (e.g., blast + ballistic)?
2. Resource management during prolonged mass casualty events?
3. Learning/adaptation from outcomes?
4. Validation against classified military medical data?
