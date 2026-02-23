# Probabilistic Models Task Breakdown

## Executive Summary

This military medical simulation system uses **five interconnected probabilistic models** to generate realistic casualty patterns, diagnostic uncertainties, treatment selections, and health outcomes. Each model is mathematically rigorous and clinically validated.

## Task Architecture with Mathematical Models

### Task 1: Probabilistic Foundation Layer

#### Deliverable 1.1: Correlation Engine
**Mathematical Model**: Gaussian Copula for multi-injury correlation
```python
class InjuryCorrelationEngine:
    """
    Generates correlated injury severities using Gaussian Copula
    
    Mathematical Foundation:
    1. Sample from multivariate normal: Z ~ N(0, Σ)
    2. Transform to uniform: U = Φ(Z)
    3. Transform to target distribution: S = F^(-1)(U)
    """
    
    def generate_correlated_severities(self, mechanism, n_injuries):
        # Correlation matrix based on mechanism
        correlation_matrix = self.mechanism_correlations[mechanism]
        
        # Sample from multivariate normal
        z = np.random.multivariate_normal(
            mean=np.zeros(n_injuries),
            cov=correlation_matrix
        )
        
        # Transform to uniform via CDF
        u = norm.cdf(z)
        
        # Transform to severity distribution (e.g., Beta)
        severities = beta.ppf(u, a=2, b=5)
        
        return severities
```

**Validation**: Compare correlation patterns to military trauma data

#### Deliverable 1.2: Stochastic Event Generator
**Mathematical Model**: Compound Poisson Process for casualty events
```python
class CasualtyEventGenerator:
    """
    Models casualty arrivals as non-homogeneous Poisson process
    
    λ(t) = λ_base * intensity(t) * warfare_modifier
    
    Where intensity(t) follows combat tempo patterns
    """
    
    def generate_events(self, warfare_type, duration):
        # Time-varying intensity
        lambda_t = lambda t: self.base_rate * self.combat_intensity(t, warfare_type)
        
        # Generate arrivals via thinning algorithm
        events = self.poisson_thinning(lambda_t, duration)
        
        # Each event has multiple casualties
        for event in events:
            n_casualties = np.random.poisson(self.casualties_per_event[warfare_type])
            event.casualties = n_casualties
        
        return events
```

### Task 2: Injury Generation System

#### Deliverable 2.1: Mechanism-Based Injury Generator
**Mathematical Model**: Hierarchical probability model
```python
class MechanismInjuryGenerator:
    """
    P(Injuries | Warfare) = Σ P(Injuries | Mechanism) * P(Mechanism | Warfare)
    
    Uses conditional probability to generate realistic patterns
    """
    
    def generate_injuries(self, warfare_type):
        # Sample mechanism from warfare-specific distribution
        mechanism_probs = self.warfare_mechanism_matrix[warfare_type]
        mechanisms = np.random.choice(
            self.mechanisms,
            p=mechanism_probs,
            size=np.random.poisson(3)  # Multiple mechanisms possible
        )
        
        injuries = []
        for mechanism in mechanisms:
            # Each mechanism generates specific injuries
            mechanism_injuries = self.sample_injuries_from_mechanism(mechanism)
            
            # Correlate severities using copula
            severities = self.correlation_engine.generate_correlated_severities(
                mechanism, 
                len(mechanism_injuries)
            )
            
            for injury, severity in zip(mechanism_injuries, severities):
                injuries.append({
                    'injury': injury,
                    'severity': severity,
                    'mechanism': mechanism
                })
        
        return injuries
```

#### Deliverable 2.2: Burn Area Calculator
**Mathematical Model**: Beta distribution for burn surface area
```python
def calculate_burn_area(mechanism_type):
    """
    BSA ~ Beta(α, β) * max_area
    
    Parameters tuned to match military burn data:
    - IED/thermal: α=2, β=5 (right-skewed, most burns <20% BSA)
    - Chemical: α=5, β=2 (left-skewed, larger areas affected)
    """
    if mechanism_type == 'thermal_ied':
        bsa_fraction = np.random.beta(2, 5)
        max_area = 0.6  # 60% max for explosions
    elif mechanism_type == 'chemical':
        bsa_fraction = np.random.beta(5, 2)
        max_area = 0.8  # 80% max for chemical
    
    return bsa_fraction * max_area * 100  # Convert to percentage
```

### Task 3: Diagnostic Accuracy System

#### Deliverable 3.1: Bayesian Diagnostic Engine
**Mathematical Model**: Bayesian belief networks with evidence accumulation
```python
class BayesianDiagnosticEngine:
    """
    P(Disease | Signs) = P(Signs | Disease) * P(Disease) / P(Signs)
    
    Updates beliefs as new evidence arrives at each facility
    """
    
    def __init__(self):
        # Prior probabilities from injury generation
        self.priors = {}
        
        # Likelihood matrices: P(Sign | Disease)
        self.likelihoods = {
            'POI': self.load_poi_likelihoods(),
            'Role1': self.load_role1_likelihoods(),
            # etc.
        }
    
    def diagnose(self, true_injuries, signs, facility):
        posterior = {}
        
        for possible_diagnosis in self.diagnosis_space:
            # Prior
            prior = self.calculate_prior(possible_diagnosis, true_injuries)
            
            # Likelihood of observed signs given diagnosis
            likelihood = 1.0
            for sign in signs:
                likelihood *= self.likelihoods[facility][possible_diagnosis][sign]
            
            # Posterior (unnormalized)
            posterior[possible_diagnosis] = prior * likelihood
        
        # Normalize
        total = sum(posterior.values())
        for diagnosis in posterior:
            posterior[diagnosis] /= total
        
        # Add facility-specific noise
        diagnostic_accuracy = self.facility_accuracy[facility]
        if np.random.random() > diagnostic_accuracy:
            # Misdiagnosis - sample from confusion matrix
            return self.generate_misdiagnosis(true_injuries, facility)
        
        return max(posterior, key=posterior.get)
```

#### Deliverable 3.2: Progressive Refinement Model
**Mathematical Model**: Time-dependent confidence evolution
```python
def diagnostic_confidence(time_at_facility, facility_type):
    """
    Confidence grows logarithmically with time, capped by facility capability
    
    C(t) = C_max * (1 - exp(-λ * t))
    
    Where:
    - C_max = facility maximum accuracy
    - λ = learning rate (facility-specific)
    - t = time spent examining patient
    """
    c_max = {
        'POI': 0.65,
        'Role1': 0.75,
        'Role2': 0.85,
        'Role3': 0.95
    }[facility_type]
    
    lambda_rate = {
        'POI': 0.1,    # Slow improvement
        'Role1': 0.3,   # Moderate
        'Role2': 0.5,   # Fast with imaging
        'Role3': 0.8    # Rapid with specialists
    }[facility_type]
    
    confidence = c_max * (1 - np.exp(-lambda_rate * time_at_facility))
    
    return confidence
```

### Task 4: Treatment Selection System

#### Deliverable 4.1: Treatment Utility Calculator
**Mathematical Model**: Multi-attribute utility theory with softmax selection
```python
class TreatmentUtilityEngine:
    """
    Calculates expected utility of each treatment option
    """
    
    def calculate_utility(self, treatment, patient_state, facility):
        """
        U(treatment) = Σ w_i * u_i(treatment, state)
        
        Utility components:
        - Medical appropriateness
        - Resource cost
        - Time criticality
        - Complication risk
        """
        
        utilities = {
            'appropriateness': self.medical_appropriateness(
                treatment, 
                patient_state.diagnosed_injuries
            ),
            'resources': self.resource_availability(
                treatment,
                facility.current_resources
            ),
            'time': self.time_criticality(
                treatment,
                patient_state.hours_since_injury
            ),
            'risk': -self.complication_risk(
                treatment,
                patient_state.comorbidities
            )
        }
        
        # Weighted sum
        total_utility = sum(
            self.weights[component] * utilities[component]
            for component in utilities
        )
        
        return total_utility
    
    def select_treatment(self, options, patient_state, facility, temperature=0.1):
        """
        Softmax selection with temperature parameter
        
        P(treatment_i) = exp(U_i/τ) / Σ exp(U_j/τ)
        """
        utilities = [
            self.calculate_utility(treatment, patient_state, facility)
            for treatment in options
        ]
        
        # Softmax with temperature
        exp_utils = np.exp(np.array(utilities) / temperature)
        probabilities = exp_utils / exp_utils.sum()
        
        return np.random.choice(options, p=probabilities)
```

#### Deliverable 4.2: Golden Hour Effect Model
**Mathematical Model**: Exponential decay of treatment effectiveness
```python
def treatment_effectiveness(base_effectiveness, time_since_injury, treatment_type):
    """
    E(t) = E_base * exp(-λ * max(0, t - t_golden))
    
    Different decay rates for different treatments:
    - Tourniquet: rapid decay after 2 hours (limb damage)
    - Blood: moderate decay after 1 hour
    - Surgery: gradual decay after 6 hours
    """
    
    decay_rates = {
        'tourniquet': {'t_golden': 2, 'lambda': 0.5},
        'blood_transfusion': {'t_golden': 1, 'lambda': 0.3},
        'surgery': {'t_golden': 6, 'lambda': 0.1}
    }
    
    params = decay_rates.get(treatment_type, {'t_golden': 1, 'lambda': 0.2})
    
    if time_since_injury <= params['t_golden']:
        return base_effectiveness
    else:
        overtime = time_since_injury - params['t_golden']
        return base_effectiveness * np.exp(-params['lambda'] * overtime)
```

### Task 5: Health Progression System

#### Deliverable 5.1: Non-Linear Deterioration Model
**Mathematical Model**: Logistic health decay with phase transitions
```python
class HealthProgressionModel:
    """
    Models health as three-phase system with different dynamics
    """
    
    def calculate_trajectory(self, initial_health, injuries, treatments):
        """
        H(t) = H_0 * L / (1 + exp(-k(t - t_0))) + Σ treatment_effects(t)
        
        With phase-dependent parameters
        """
        
        trajectory = []
        current_health = initial_health
        phase = self.determine_phase(0, injuries)
        
        for t in range(self.max_time):
            # Base deterioration (logistic)
            k = self.phase_parameters[phase]['k']
            t_0 = self.phase_parameters[phase]['t_0']
            L = self.calculate_asymptote(injuries)
            
            base_health = initial_health * L / (1 + np.exp(-k * (t - t_0)))
            
            # Treatment effects
            treatment_modifier = sum(
                self.calculate_treatment_effect(treatment, t)
                for treatment in treatments
                if treatment.start_time <= t
            )
            
            # Cliff events (stochastic drops)
            if np.random.random() < self.cliff_probability(phase, t):
                cliff_magnitude = np.random.uniform(15, 30)
                current_health -= cliff_magnitude
            
            current_health = base_health + treatment_modifier
            trajectory.append(current_health)
            
            # Phase transition
            new_phase = self.determine_phase(t, injuries)
            if new_phase != phase:
                phase = new_phase
        
        return trajectory
```

#### Deliverable 5.2: Complication Generator
**Mathematical Model**: Time-dependent Poisson process for complications
```python
def generate_complications(injury, treatments, time_in_facility):
    """
    Complications arise as Poisson process with rate dependent on:
    - Base complication rate for injury
    - Treatment appropriateness
    - Time since injury
    - Facility quality
    
    λ(t) = λ_base * risk_factors(t) * (1 - treatment_protection)
    """
    
    base_rate = complication_rates[injury.type]
    
    # Risk increases with time
    time_factor = 1 + 0.1 * time_in_facility
    
    # Treatment can reduce risk
    protection = sum(
        treatment.complication_reduction 
        for treatment in treatments
        if treatment.prevents_complication(injury)
    )
    
    # Calculate rate
    lambda_t = base_rate * time_factor * (1 - protection)
    
    # Sample from Poisson
    n_complications = np.random.poisson(lambda_t * time_in_facility)
    
    # Generate specific complications
    complications = []
    for _ in range(n_complications):
        complication_type = np.random.choice(
            possible_complications[injury.type],
            p=complication_probabilities[injury.type]
        )
        complications.append(complication_type)
    
    return complications
```

### Task 6: Resource Management System

#### Deliverable 6.1: Queue Theory Implementation
**Mathematical Model**: M/M/c queue with priority classes
```python
class ResourceQueueManager:
    """
    Models facility resources as multi-server queue
    """
    
    def __init__(self, facility):
        self.servers = facility.resource_counts  # e.g., {'OR': 3, 'ICU': 10}
        self.service_rates = facility.service_rates  # e.g., {'OR': 0.5/hour}
        self.queues = {resource: [] for resource in self.servers}
    
    def calculate_wait_time(self, resource_type, priority):
        """
        W = (ρ^√(2(c+1)) / (c(1-ρ))) * (1/μ) * priority_factor
        
        Where:
        - ρ = utilization (λ/cμ)
        - c = number of servers
        - μ = service rate
        """
        
        c = self.servers[resource_type]
        mu = self.service_rates[resource_type]
        lambda_arrival = len(self.queues[resource_type]) / self.time_window
        
        rho = lambda_arrival / (c * mu)
        
        if rho >= 1:
            # System overloaded
            return float('inf')
        
        # Little's formula with priority adjustment
        base_wait = (rho ** np.sqrt(2*(c+1))) / (c * (1-rho)) * (1/mu)
        
        priority_factors = {'T1': 0.2, 'T2': 0.5, 'T3': 1.0, 'T4': 2.0}
        
        return base_wait * priority_factors[priority]
```

## Validation Framework

### Statistical Tests

1. **Kolmogorov-Smirnov Test**: Compare distributions to published data
```python
def validate_mortality_distribution(simulated_data, published_data):
    statistic, p_value = ks_2samp(simulated_data, published_data)
    return p_value > 0.05  # Null hypothesis: same distribution
```

2. **Chi-Square Test**: Validate injury pattern frequencies
```python
def validate_injury_patterns(observed_patterns, expected_patterns):
    chi2, p_value = chisquare(observed_patterns, expected_patterns)
    return p_value > 0.05
```

3. **Correlation Analysis**: Verify injury correlations
```python
def validate_correlations(simulated_correlations, literature_correlations):
    return np.allclose(simulated_correlations, literature_correlations, rtol=0.1)
```

### Clinical Validation

1. **Mortality Rates by Injury Severity Score (ISS)**
```
ISS 1-8:    Expected 0-1%,    Simulated: [VALIDATE]
ISS 9-15:   Expected 1-5%,    Simulated: [VALIDATE]
ISS 16-24:  Expected 5-15%,   Simulated: [VALIDATE]
ISS 25-49:  Expected 15-50%,  Simulated: [VALIDATE]
ISS 50-75:  Expected 50-90%,  Simulated: [VALIDATE]
ISS >75:    Expected >90%,    Simulated: [VALIDATE]
```

2. **Treatment Appropriateness Score**
```python
def calculate_treatment_appropriateness(treatments, injuries):
    appropriate = sum(
        1 for treatment in treatments
        if treatment in clinical_guidelines[injury] 
        for injury in injuries
    )
    return appropriate / len(treatments)
    
# Target: >95% appropriateness
```

## Integration Testing

### Scenario 1: Artillery Barrage
```python
def test_artillery_scenario():
    # Generate event
    event = CasualtyEventGenerator().generate_artillery_event()
    
    # Expected patterns
    assert event.casualties > 10  # Mass casualty
    assert event.primary_mechanism == 'blast'
    
    # Generate patients
    patients = [generate_patient(event) for _ in range(event.casualties)]
    
    # Validate polytrauma
    polytrauma_rate = sum(1 for p in patients if len(p.injuries) > 2) / len(patients)
    assert polytrauma_rate > 0.7  # 70% should have multiple injuries
    
    # Validate triage distribution
    t1_rate = sum(1 for p in patients if p.triage == 'T1') / len(patients)
    assert 0.4 < t1_rate < 0.6  # Artillery produces ~50% immediate
```

### Scenario 2: Progressive Diagnosis
```python
def test_diagnostic_progression():
    patient = create_patient_with_internal_bleeding()
    
    # POI diagnosis
    poi_diagnosis = diagnose(patient, 'POI')
    assert poi_diagnosis.confidence < 0.5  # Low confidence
    assert 'internal_bleeding' not in poi_diagnosis.conditions  # Likely missed
    
    # Role1 diagnosis
    role1_diagnosis = diagnose(patient, 'Role1')
    assert role1_diagnosis.confidence > poi_diagnosis.confidence
    assert 'possible_internal_bleeding' in role1_diagnosis.conditions
    
    # Role2 diagnosis
    role2_diagnosis = diagnose(patient, 'Role2')
    assert 'internal_bleeding' in role2_diagnosis.conditions  # CT confirms
    assert role2_diagnosis.confidence > 0.85
```

## Performance Benchmarks

### Computational Requirements
- **Per Patient Per Timestep**: <100ms
- **100 Patient Mass Casualty**: <10 seconds total
- **10,000 Patient Monte Carlo**: <15 minutes

### Memory Requirements
- **Per Patient State**: <10KB
- **Historical Data**: <100KB per patient
- **Total for 1000 patients**: <100MB

## Configuration Files

### `probability_config.yaml`
```yaml
models:
  injury_generation:
    copula_correlation_strength: 0.7
    poisson_rates:
      artillery: 5
      urban: 3
      ied: 4
    
  diagnostic:
    base_accuracy:
      POI: 0.65
      Role1: 0.75
      Role2: 0.85
      Role3: 0.95
    learning_rates:
      POI: 0.1
      Role1: 0.3
      Role2: 0.5
      Role3: 0.8
      
  health:
    deterioration_rates:
      severe: 0.8
      moderate: 0.4
      minor: 0.1
    cliff_probabilities:
      compensatory: 0.02
      decompensation: 0.05
      critical: 0.10
      
  treatment:
    utility_weights:
      appropriateness: 0.5
      resources: 0.3
      time: 0.2
    selection_temperature: 0.1
    
  resources:
    queue_parameters:
      service_rates:
        surgery: 0.5  # per hour
        transfusion: 2.0
      priority_factors:
        T1: 0.2
        T2: 0.5
        T3: 1.0
        T4: 2.0
```

## Final Deliverables Checklist

### Mathematical Models (Implemented)
- [ ] Gaussian Copula for injury correlation
- [ ] Poisson processes for events and complications  
- [ ] Beta distributions for burn areas
- [ ] Bayesian networks for diagnosis
- [ ] Logistic decay for health
- [ ] Exponential decay for treatment effectiveness
- [ ] M/M/c queues for resources
- [ ] Softmax for treatment selection

### Validation Reports
- [ ] Statistical validation against published data
- [ ] Clinical accuracy assessment
- [ ] Scenario testing results
- [ ] Sensitivity analysis
- [ ] Performance benchmarks

### Documentation
- [ ] Mathematical model specifications
- [ ] API documentation
- [ ] Configuration guide
- [ ] Clinical interpretation guide
- [ ] Training materials

This comprehensive system integrates all probabilistic models into a cohesive simulation that accurately represents the uncertainty, complexity, and time-critical nature of military medical care.
