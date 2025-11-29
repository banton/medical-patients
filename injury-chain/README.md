# Military Medical Simulation - Documentation Index

## CURRENT DOCUMENTATION (Use These)

### Primary Implementation Documents

1. **[MASTER_IMPLEMENTATION_PLAN.md](MASTER_IMPLEMENTATION_PLAN.md)** ⭐
   - **Purpose**: Consolidated implementation plan with full warfare pattern integration
   - **Status**: CURRENT - Primary reference document
   - **Contains**: Complete roadmap, all 12 probabilistic models, warfare context throughout

2. **[WARFARE_PATTERN_INTEGRATION.md](WARFARE_PATTERN_INTEGRATION.md)** ⭐ **NEW**
   - **Purpose**: Complete warfare pattern integration with probabilistic models
   - **Status**: CURRENT - Critical component
   - **Contains**: How warfare types modify all Markov chains, injury patterns, and system behavior

3. **[COMPLETE_PROBABILISTIC_INTEGRATION.md](COMPLETE_PROBABILISTIC_INTEGRATION.md)** ⭐
   - **Purpose**: Comprehensive integration of all probabilistic models
   - **Status**: CURRENT - Technical reference
   - **Contains**: All 12 probability models working together, complete flow

4. **[MARKOV_CHAIN_INTEGRATION.md](MARKOV_CHAIN_INTEGRATION.md)** ⭐
   - **Purpose**: Detailed Markov chain implementations
   - **Status**: CURRENT - Critical addition
   - **Contains**: 5 Markov chains, HMM for diagnosis, validation methods

### Supporting Documents

5. **[UNIFIED_SYSTEM_ARCHITECTURE.md](UNIFIED_SYSTEM_ARCHITECTURE.md)**
   - **Purpose**: Complete system architecture with mathematical models
   - **Status**: Current - Architecture reference
   - **Contains**: Component structure, data flow, mathematical foundations

6. **[IMPLEMENTATION_ROADMAP.md](IMPLEMENTATION_ROADMAP.md)**
   - **Purpose**: Detailed 4-week implementation timeline
   - **Status**: Current - Project management
   - **Contains**: Daily tasks, validation checkpoints, deliverables

7. **[PROBABILISTIC_MODELS_IMPLEMENTATION.md](PROBABILISTIC_MODELS_IMPLEMENTATION.md)**
   - **Purpose**: Detailed code examples for all models
   - **Status**: Current - Code reference
   - **Contains**: Python implementations, validation tests

8. **[COMPLETE_SYSTEM_DESIGN.md](COMPLETE_SYSTEM_DESIGN.md)**
   - **Purpose**: Full patient journey with calculations
   - **Status**: Current - System flow reference
   - **Contains**: Stage-by-stage flow, example calculations

---

## DEPRECATED DOCUMENTATION (Historical Reference Only)

The following documents are outdated and have been superseded by the current documentation above:

- `PROMPT_FOR_NEW_SESSION.md` - Old session context (superseded by MASTER_IMPLEMENTATION_PLAN)
- `SESSION_FILES_SUMMARY.md` - Old session summary (no longer relevant)
- `START_NEW_SESSION_PROMPT.txt` - Old prompt (superseded by this README)
- `CURRENT_VS_PROPOSED_COMPARISON.md` - Early comparison (integrated into current docs)
- `IMPLEMENTATION_CHECKLIST.md` - Old checklist (replaced by MASTER_IMPLEMENTATION_PLAN)
- `ARCHITECTURE_SUMMARY.md` - Early architecture (superseded by UNIFIED_SYSTEM_ARCHITECTURE)
- `DIAGNOSTIC_ACCURACY_SYSTEM.md` - Old diagnostic details (integrated into COMPLETE_PROBABILISTIC_INTEGRATION)
- `TREATMENT_IMPLEMENTATION_GUIDE.md` - Old treatment guide (integrated into current docs)

---

## Quick Start Guide

### For Implementation:
1. Start with **MASTER_IMPLEMENTATION_PLAN.md** for the complete roadmap
2. Review **WARFARE_PATTERN_INTEGRATION.md** for warfare-specific modifications
3. Reference **COMPLETE_PROBABILISTIC_INTEGRATION.md** for mathematical details
4. Use **MARKOV_CHAIN_INTEGRATION.md** for state transition implementations

### For Architecture Understanding:
1. Review **UNIFIED_SYSTEM_ARCHITECTURE.md** for system structure
2. Study **COMPLETE_SYSTEM_DESIGN.md** for patient flow examples
3. Understand **WARFARE_PATTERN_INTEGRATION.md** for warfare impact

### For Coding:
1. Use **PROBABILISTIC_MODELS_IMPLEMENTATION.md** for code templates
2. Follow **IMPLEMENTATION_ROADMAP.md** for daily tasks
3. Reference **WARFARE_PATTERN_INTEGRATION.md** for warfare modifications

---

## System Summary

A military medical simulation using **12 interconnected probabilistic models** with **warfare patterns driving all parameters**:

### Markov Chains (5)
1. Facility transition chain (POI → Role1 → Role2 → Death/RTD)
2. Health state chain (Stable → Compensatory → Critical → Death)
3. Diagnostic HMM (hidden conditions, observed diagnoses)
4. Treatment outcome chain (No Effect → Improving → Complication)
5. Resource availability chain (birth-death process)

### Other Probabilistic Models (7)
6. Poisson processes (casualty arrivals, complications)
7. Gaussian Copula (injury correlations)
8. Beta distribution (burn areas)
9. Bayesian networks (diagnostic updates)
10. Softmax selection (treatment choices)
11. M/M/c queues (resource allocation)
12. Exponential decay (golden hour effects)

### Warfare Pattern Integration
The **warfare type** (artillery, urban, IED, conventional, counterinsurgency) fundamentally modifies:
- **All Markov chain transition matrices** (different flow per warfare)
- **Injury mechanism distributions** (blast vs ballistic vs crush)
- **Temporal casualty patterns** (surges vs sustained vs random)
- **Correlation matrices** (polytrauma patterns)
- **Triage distributions** (severity mix)
- **Resource strain** (mass casualty probabilities)

### Key Innovation
The system uses:
1. **Warfare patterns as primary drivers** - All models adapt to warfare type
2. **Mechanism-based injury generation** - 50 mechanisms → thousands of patterns
3. **Markov chains for state transitions** - Proper probability propagation
4. **Realistic uncertainty modeling** - Diagnostic accuracy increases through chain

### Success Metrics by Warfare Type

#### Artillery
- Polytrauma rate: 70-90%
- Mass casualty events: 70-90%
- Mortality: 25-35%

#### Urban Combat
- Delayed evacuation: 20-40%
- Mixed mechanisms: ✓
- Civilian mix: 10-30%

#### IED
- Classic triad: 60-80%
- Amputation rate: 30-50%
- Immediate surgery: 70-90%

#### Conventional
- Sustained flow: ✓
- Moderate strain: ✓
- Mortality: 15-25%

#### Counterinsurgency
- Psychological: 15-30%
- Disease: 10-20%
- Low mortality: 5-15%

### Performance Targets
- <100ms per patient per timestep
- <10KB memory per patient
- 10 seconds for 100-patient mass casualty

---

## Implementation Priority

1. **Core Infrastructure**: Markov chains with warfare context manager
2. **Warfare Integration**: Modify all models based on warfare type
3. **Patient Generation**: Warfare-specific injury patterns
4. **Simulation Flow**: Complete journey with all models
5. **Validation**: Warfare-specific pattern validation

---

## Contact for Questions

Refer to the codebase at `/Users/banton/Sites/medical-patients` for implementation details.
