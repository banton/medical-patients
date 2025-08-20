# COMPREHENSIVE PROMPT FOR NEW CHAT SESSION

## Context
I'm working on a military medical patient generator at `/Users/banton/Sites/medical-patients`. The system simulates casualty flow through military medical facilities (POI → Role1 → Role2 → Role3 → Role4) with realistic injury patterns, deterioration, and treatment protocols.

## Current State
The codebase has sophisticated components that aren't properly integrated:
- `warfare_patterns.json` has rich warfare-specific data but only affects timing, not injury types
- `medical_simulation/` folder has non-linear health models that aren't used
- Treatments are randomly assigned without medical logic
- Health deterioration is linear despite having complex models available

## Architecture Decisions Made

### 1. Mechanism-Based Injury System
Instead of mapping thousands of injuries, use ~50 injury mechanisms (blast, ballistic, crush, thermal) that generate realistic patterns:
- Artillery → primary/secondary/tertiary blast → polytrauma
- Urban warfare → building collapse → crush syndrome + delayed complications
- IED → characteristic triad (TBI + amputation + burns)

### 2. Diagnostic Accuracy Layer
Add realistic misdiagnosis rates that decrease as patients move through care:
- POI: 65% accuracy (medic under fire)
- Role1: 75% (PA with ultrasound)  
- Role2: 85% (ER doc with CT)
- Role3: 95% (specialists)

Misdiagnosis → wrong treatment → continued deterioration → realistic mortality

### 3. Treatment Protocol Engine
Replace random treatment with medical logic:
- Injury category → treatment protocol → facility filtering → resource availability → actual treatment
- Treatment sequences (tourniquet → IV → blood → surgery)
- Golden hour effects (effectiveness decays over time)
- Resource exhaustion during mass casualties

## Key Files and Locations

### Core System
- `/patient_generator/flow_simulator.py` - Main patient flow (needs warfare context added)
- `/patient_generator/medical.py` - Basic injury lists (needs mechanism metadata)
- `/patient_generator/patient.py` - Patient model (needs diagnostic history, treatment protocols)
- `/patient_generator/temporal_generator.py` - Creates casualty events with warfare type
- `/patient_generator/warfare_patterns.json` - Rich warfare data (underutilized)

### Unused Assets to Integrate
- `/medical_simulation/health_score_engine.py` - Non-linear health progression
- `/medical_simulation/deterioration_calculator.py` - Realistic deterioration
- `/medical_simulation/config/complications.json` - Detailed complications
- `/medical_simulation/config/treatment_effects.json` - Treatment definitions

### Documentation Created
- `/ARCHITECTURE_SUMMARY.md` - Overall system design
- `/TREATMENT_PROTOCOL_PLAN.md` - Treatment system details
- `/TREATMENT_IMPLEMENTATION_GUIDE.md` - Integration guide
- `/DIAGNOSTIC_ACCURACY_SYSTEM.md` - Diagnostic layer specification
- `/patient_generator/config/injury_treatment_map.json` - Injury-treatment mappings

## Critical Integration Points

1. **Connect warfare context**: Modify `generate_temporal_casualties()` to pass warfare type to individual patients
2. **Fix treatment selection**: Replace `_generate_treatments()` random selection with protocol engine
3. **Add diagnostic layer**: Insert diagnosis step between injury and treatment
4. **Use non-linear health**: Replace linear deterioration with existing health_score_engine

## Mathematical Models to Implement

1. **Injury Generation**: Poisson for counts, Gaussian copula for correlation, Beta for burn area
2. **Health Progression**: Logistic decay with cliff events, three phases (compensatory/decompensation/critical)
3. **Treatment Selection**: Bayesian network for dependencies, M/M/c queue for resources
4. **Diagnostic Accuracy**: Progressive refinement with facility-specific detection rates

## Immediate Next Steps

1. Create `warfare_context_manager.py` to maintain warfare type through patient creation
2. Build `injury_mechanism_system.py` for mechanism-based injury generation
3. Implement `treatment_protocol_engine.py` for medical logic
4. Add `diagnostic_accuracy_model.py` for misdiagnosis simulation
5. Connect existing `health_score_engine.py` to patient deterioration

## Key Insights

- The system has all the pieces but they're not connected
- Warfare type gets lost between temporal generation and patient creation
- Rich medical simulation modules exist but aren't used
- Treatment assignment has no medical logic
- Perfect diagnosis at all levels is unrealistic

## Validation Requirements

- Compare to Tactical Combat Casualty Care (TCCC) guidelines
- Mortality rates within 5% of published military medical data
- Realistic resource exhaustion during mass casualties
- Appropriate treatment-injury matching >95% of time

## Questions/Concerns

1. Context window management - lots of interconnected systems
2. How to validate against potentially classified medical data
3. Balance between realism and computational efficiency
4. How to handle edge cases (psychological conditions in combat, etc.)

When continuing, focus on:
1. Implementing the mechanism-based injury system first
2. Then adding the treatment protocol engine
3. Finally integrating the diagnostic accuracy layer
4. Testing with 100-patient scenarios at each step

The goal is realistic casualty simulation that captures the chaos and uncertainty of combat medicine while maintaining medical accuracy.
