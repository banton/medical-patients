# Complete System Design: Goals, Flow, and Deliverables

## System Goal

Create a **mathematically rigorous military medical simulation** that models casualty flow through evacuation chains with realistic uncertainty, using probabilistic models to capture the chaos and complexity of combat medicine.

## Core Design Principles

1. **Probabilistic Over Deterministic**: Every decision point uses probability distributions based on real data
2. **Mechanism-Based Generation**: ~50 injury mechanisms generate thousands of realistic patterns
3. **Progressive Uncertainty Reduction**: Diagnostic accuracy improves through evacuation chain
4. **Resource-Constrained Decisions**: Queue theory models limited resources
5. **Non-Linear Health Dynamics**: Realistic deterioration with phase transitions and cliff events

## Complete Patient Journey with Mathematical Models

### Stage 1: Warfare Event Generation
**Goal**: Generate realistic casualty events based on warfare type

**Mathematical Model**: Non-homogeneous Poisson Process
```
Event Generation:
- Warfare Type: "Artillery Barrage"
- Time: t = 14:30
- Intensity: λ(t) = 8 casualties/hour (peak combat)
- Location: Urban area, 30km from Role2

Calculation:
P(n events in interval) = (λt)^n * e^(-λt) / n!
Result: 12 casualties generated
```

**Deliverable**: Time-stamped casualty events with warfare context

### Stage 2: Injury Pattern Generation
**Goal**: Create medically accurate polytrauma patterns

**Mathematical Models**: 
- Categorical distribution for mechanism selection
- Gaussian Copula for severity correlation
- Beta distribution for burn areas

```
Patient #1 (Artillery victim):
1. Sample mechanisms from warfare distribution:
   P(blast|artillery) = 0.8 → Selected
   P(fragments|artillery) = 0.9 → Selected
   P(building_collapse|artillery) = 0.3 → Selected

2. Generate injuries per mechanism:
   Blast → {TBI (severe), Blast lung (moderate), TM rupture (mild)}
   Fragments → Poisson(λ=5) = 7 shrapnel wounds
   Collapse → {Crush injury (severe), Fractures (moderate)}

3. Correlate severities using Copula:
   Correlation matrix Σ = [[1, 0.7, 0.5], [0.7, 1, 0.6], [0.5, 0.6, 1]]
   Result: All blast injuries have correlated high severity

4. Calculate burn area (if thermal component):
   BSA ~ Beta(2, 5) * 0.4 = 12% body surface area
```

**Deliverable**: Patients with realistic, correlated polytrauma patterns

### Stage 3: Point of Injury (POI) Assessment
**Goal**: Model realistic field diagnosis with high uncertainty

**Mathematical Model**: Bayesian Diagnostic Network with 65% accuracy

```
True Injuries: 
- Internal bleeding (splenic laceration)
- Multiple shrapnel wounds
- Moderate TBI

POI Diagnosis (under fire, 30 seconds to assess):
1. Observable signs: hypotension, visible wounds, confusion
2. Bayesian update:
   P(internal bleeding | hypotension) = 0.4
   P(shock | hypotension) = 0.3
   P(blood loss from visible wounds | hypotension) = 0.3

3. Apply facility accuracy (65%):
   Correct diagnosis probability = 0.65
   Random draw = 0.72 → Misdiagnosis

POI Diagnosed Conditions:
- "Hemorrhagic shock from external wounds" (missed internal)
- Multiple shrapnel wounds (correct)
- "Combat stress" (missed TBI)
```

**Deliverable**: Initial diagnosis with realistic error rate

### Stage 4: POI Treatment Selection
**Goal**: Select treatments based on diagnosis (not truth)

**Mathematical Model**: Softmax selection with utility function

```
Treatment Options at POI:
- Tourniquet (utility for external bleeding = 0.9)
- Pressure dressing (utility = 0.7)
- IV fluids (utility for shock = 0.8)
- Morphine (utility for pain = 0.6)

Utility Calculation:
U(tourniquet) = 0.9 * appropriate + 0.1 * available = 0.85
U(IV) = 0.8 * appropriate + 0.1 * available = 0.75
U(morphine) = 0.6 * appropriate + 0.1 * available = 0.55

Softmax Selection (τ = 0.1):
P(tourniquet) = exp(0.85/0.1) / Σ = 0.72
P(IV) = 0.24
P(morphine) = 0.04

Selected: Tourniquet + IV fluids
Problem: Tourniquet won't help internal bleeding!
```

**Deliverable**: Medically logical but potentially wrong treatments

### Stage 5: Health Deterioration During Transport
**Goal**: Model realistic health progression with treatment effects

**Mathematical Model**: Logistic decay with cliff events

```
Transport to Role1 (45 minutes):
Initial Health: H₀ = 75

Without proper treatment for internal bleeding:
H(t) = 75 / (1 + exp(-0.6*(t - 2))) 

At t = 0.75 hours:
Base health = 75 / (1 + exp(-0.6*(0.75 - 2))) = 71

Treatment effects:
- IV fluids: +2 health (partial help)
- Tourniquet: 0 (doesn't address internal bleeding)
- Untreated internal bleeding: -8 health

Cliff event check:
P(cliff) = 0.05 * time = 0.0375
Random draw = 0.02 → Cliff occurs!
Cliff magnitude = -20 health

Final health at Role1: 71 + 2 - 8 - 20 = 45 (Critical)
```

**Deliverable**: Time-based health trajectory with stochastic events

### Stage 6: Role1 Diagnosis Refinement
**Goal**: Improve diagnosis with better tools

**Mathematical Model**: Bayesian update with 75% accuracy

```
Role1 Assessment (PA with ultrasound):
1. FAST exam performed
2. New evidence: free fluid in abdomen
3. Bayesian update:
   P(internal bleeding | free fluid + hypotension) = 0.85
   
4. Apply facility accuracy (75%):
   Correct diagnosis probability = 0.75
   Random draw = 0.71 → Correct diagnosis!

Updated Diagnosis:
- Internal bleeding suspected (correct)
- Multiple shrapnel wounds (correct)
- Possible TBI (partially correct)

Triage category updated: T1 (Immediate)
```

**Deliverable**: Refined diagnosis with improved accuracy

### Stage 7: Role1 Treatment with Resource Constraints
**Goal**: Provide treatment considering resources

**Mathematical Model**: M/M/c queue for resource allocation

```
Role1 Resources:
- Blood units: 20 available
- OR time: 1 table, 3 patients waiting

Queue calculation:
λ = 4 patients/hour arriving
μ = 1.5 patients/hour served
c = 1 server (OR)
ρ = λ/(c*μ) = 2.67 → System overloaded!

Wait time: W = ∞ (system unstable)
Decision: Stabilize and evacuate to Role2

Treatments given:
- Blood transfusion (2 units) - partially addresses bleeding
- Continue IV fluids
- Priority medevac to Role2
```

**Deliverable**: Resource-constrained treatment decisions

### Stage 8: Evacuation Decision Making
**Goal**: Prioritize evacuation based on condition

**Mathematical Model**: Multi-criteria decision analysis

```
Evacuation Priority Score:
S = w₁*severity + w₂*deterioration_rate + w₃*benefit_from_evacuation

Patient scores:
- Severity: 0.9 (critical)
- Deterioration rate: 0.8 (rapid without surgery)
- Benefit from Role2: 0.95 (needs surgery)

Score = 0.4*0.9 + 0.3*0.8 + 0.3*0.95 = 0.885

Rank: 2nd in queue (another patient has tension pneumo)
Wait time: 15 minutes for helicopter
```

**Deliverable**: Priority-based evacuation queue

### Stage 9: Role2 Definitive Diagnosis
**Goal**: Achieve near-certain diagnosis

**Mathematical Model**: High-confidence Bayesian diagnosis (85% accuracy)

```
Role2 Assessment (ER with CT):
1. CT scan confirms splenic laceration Grade III
2. Head CT shows moderate TBI with small contusion
3. X-ray shows 5 retained fragments

Diagnostic confidence: 95%
All conditions correctly identified

Time since injury: 2.5 hours
Golden hour exceeded for some treatments
```

**Deliverable**: Definitive diagnosis with imaging confirmation

### Stage 10: Role2 Surgical Treatment
**Goal**: Provide definitive care with golden hour effects

**Mathematical Model**: Exponential decay of treatment effectiveness

```
Surgery Decision:
Base effectiveness = 0.9 (if within golden hour)
Time since injury = 2.5 hours
Golden hour for spleen = 1 hour

Effectiveness = 0.9 * exp(-0.3 * (2.5 - 1)) = 0.59

Surgical outcome:
- Splenectomy performed
- Success probability = 0.59
- Random draw = 0.45 → Success!
- Bleeding controlled

Post-op complications check:
P(complication) = 0.1 * time_delay_factor = 0.15
Random draw = 0.22 → No complications
```

**Deliverable**: Time-sensitive surgical outcomes

### Stage 11: Recovery and Outcome Prediction
**Goal**: Calculate final patient outcome

**Mathematical Model**: Logistic regression for survival probability

```
Survival Calculation:
logit(P(survival)) = β₀ + β₁*ISS + β₂*time_to_treatment + β₃*age + β₄*facility

ISS (Injury Severity Score) = 28
Time to definitive care = 2.5 hours
Age = 24
Facility = Role2

logit(P) = 3.2 - 0.08*28 - 0.3*2.5 + 0.02*24 + 0.5
P(survival) = 1/(1 + exp(-0.93)) = 0.72

Random draw = 0.68 → Patient survives!

Final status: Evacuated to Role3 for recovery
Disability: Moderate (splenectomy + TBI effects)
```

**Deliverable**: Probabilistic outcome with disability assessment

## System Architecture Components

### Core Modules and Their Responsibilities

```
1. Event Generator (warfare_event_generator.py)
   - Input: Warfare scenario parameters
   - Process: Poisson process for timing
   - Output: CasualtyEvent objects with context

2. Injury Generator (mechanism_injury_generator.py)
   - Input: CasualtyEvent with warfare type
   - Process: Mechanism sampling + Copula correlation
   - Output: Patient with polytrauma patterns

3. Diagnostic Engine (bayesian_diagnostic_engine.py)
   - Input: True injuries + facility type
   - Process: Bayesian inference with noise
   - Output: Diagnosed conditions with confidence

4. Treatment Selector (treatment_protocol_engine.py)
   - Input: Diagnosis + facility + resources
   - Process: Utility calculation + softmax selection
   - Output: Treatment plan

5. Health Progression (health_trajectory_model.py)
   - Input: Injuries + treatments + time
   - Process: Logistic decay + cliff events
   - Output: Health trajectory array

6. Resource Manager (queue_resource_manager.py)
   - Input: Patient flow + facility capacity
   - Process: M/M/c queue theory
   - Output: Wait times + resource allocation

7. Evacuation Controller (evacuation_decision_engine.py)
   - Input: Patient states + transport availability
   - Process: Multi-criteria scoring
   - Output: Evacuation priorities

8. Outcome Calculator (outcome_prediction_model.py)
   - Input: Complete patient history
   - Process: Logistic regression
   - Output: Survival probability + disability
```

## Validation Framework

### Statistical Validation Metrics
1. **Mortality by ISS**: Within 5% of published rates
2. **Polytrauma Patterns**: 70% of blast victims have 2+ injuries
3. **Diagnostic Accuracy**: POI=65%, Role1=75%, Role2=85%, Role3=95%
4. **Treatment Appropriateness**: >95% match clinical guidelines
5. **Golden Hour Effect**: 30-40% effectiveness reduction after deadline

### Clinical Validation Scenarios
1. **Mass Casualty Event**: 50+ patients, resource exhaustion visible
2. **Delayed Evacuation**: Prolonged POI time → higher mortality
3. **Misdiagnosis Chain**: Wrong diagnosis → wrong treatment → death
4. **Resource Triage**: T1 patients prioritized correctly

### Performance Requirements
- 100ms per patient per timestep
- 10 seconds for 100-patient scenario
- <100MB memory for 1000 patients

## Deliverables

### Phase 1: Mathematical Foundation (Week 1)
- [ ] Probability distribution implementations
- [ ] Correlation matrix generators
- [ ] Queue theory models
- [ ] Unit tests with fixtures

### Phase 2: Medical Domain Models (Week 2)
- [ ] Injury mechanism mappings
- [ ] Diagnostic confusion matrices
- [ ] Treatment protocol database
- [ ] Clinical validation tests

### Phase 3: Integration Layer (Week 3)
- [ ] Patient state management
- [ ] Simulation controller
- [ ] Event scheduling system
- [ ] Integration tests

### Phase 4: Validation & Tuning (Week 4)
- [ ] Monte Carlo simulations (10,000 patients)
- [ ] Statistical comparison reports
- [ ] Parameter sensitivity analysis
- [ ] Performance optimization

### Documentation Deliverables
1. **Technical Specification**: Mathematical models and algorithms
2. **API Documentation**: Module interfaces and usage
3. **Clinical Guide**: Medical interpretation of outputs
4. **Configuration Manual**: Parameter tuning guide
5. **Validation Report**: Statistical and clinical accuracy

## Success Criteria

### Quantitative Metrics
- Mortality rates match published data (±5%)
- Polytrauma correlation matches clinical patterns
- Diagnostic progression shows 15-20% improvement per role
- Resource exhaustion occurs at realistic patient loads
- Golden hour effects visible in outcomes

### Qualitative Assessment
- Medical SME review confirms clinical realism
- Emergent behaviors match battlefield reports
- Edge cases handled appropriately
- System suitable for training and planning

## Risk Mitigation

### Technical Risks
- **Computational complexity**: Use approximations where needed
- **Parameter sensitivity**: Extensive testing across parameter ranges
- **Integration complexity**: Modular design with clear interfaces

### Domain Risks
- **Data limitations**: Use unclassified analogues
- **Validation challenges**: Partner with military medical experts
- **Edge cases**: Comprehensive test coverage

## Configuration Philosophy

All medical parameters externalized to enable:
- SME adjustment without code changes
- A/B testing of different protocols
- Scenario-specific configurations
- Easy updates as new data becomes available

This design creates a scientifically rigorous, medically accurate simulation that captures the full complexity of military medical care while remaining computationally tractable and clinically valid.
