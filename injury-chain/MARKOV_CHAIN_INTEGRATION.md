# Markov Chain Integration for Military Medical Simulation

## Critical Addition: Markov Chain Framework

The military medical evacuation chain is inherently a **Markov process** where future states depend only on the current state, not the entire history. This document shows how Markov chains should be integrated throughout the system.

## 1. Facility Transition Markov Chain

### State Space
```
S = {POI, Role1, Role2, Role3, Role4, Died, RTD}
```

### Transition Probability Matrix

```python
class FacilityTransitionChain:
    """
    Models patient flow through evacuation chain as Markov process
    P(next_facility | current_facility, patient_state)
    """
    
    def __init__(self):
        # Base transition matrix (healthy patient)
        self.base_transitions = {
            'POI': {
                'Role1': 0.70,    # Most go to Role1
                'Role2': 0.15,    # Critical bypass Role1
                'Died': 0.10,     # Die at POI
                'RTD': 0.05       # Return to duty (minor)
            },
            'Role1': {
                'Role2': 0.60,    # Need higher care
                'Role3': 0.10,    # Bypass Role2 (stable)
                'RTD': 0.20,      # Treated and released
                'Died': 0.10      # Die at Role1
            },
            'Role2': {
                'Role3': 0.70,    # Post-surgery recovery
                'Role4': 0.05,    # Long-term care
                'RTD': 0.15,      # Recovered
                'Died': 0.10      # Surgical mortality
            },
            'Role3': {
                'Role4': 0.40,    # Rehab needed
                'RTD': 0.50,      # Recovered
                'Died': 0.10      # Complications
            },
            'Role4': {
                'RTD': 0.90,      # Eventually recover
                'Died': 0.10      # Long-term mortality
            },
            'Died': {
                'Died': 1.0       # Absorbing state
            },
            'RTD': {
                'RTD': 1.0        # Absorbing state
            }
        }
    
    def get_transition_matrix(self, patient_state):
        """
        Modify base transitions based on patient condition
        """
        P = copy.deepcopy(self.base_transitions)
        
        # Adjust based on health score
        if patient_state.health < 30:  # Critical
            # Increase death probability
            for state in P:
                if 'Died' in P[state]:
                    P[state]['Died'] *= 2.0
                    # Renormalize
                    total = sum(P[state].values())
                    for next_state in P[state]:
                        P[state][next_state] /= total
        
        # Adjust based on injury severity
        if patient_state.iss > 25:  # Severe polytrauma
            # Must go through all roles
            P['POI']['Role2'] = 0  # Can't skip Role1
            P['Role1']['Role3'] = 0  # Can't skip Role2
        
        return P
    
    def simulate_trajectory(self, initial_state, patient):
        """
        Generate complete evacuation path using Markov chain
        """
        trajectory = [initial_state]
        current = initial_state
        
        while current not in ['Died', 'RTD']:
            P = self.get_transition_matrix(patient)
            transitions = P[current]
            
            # Sample next state
            states = list(transitions.keys())
            probs = list(transitions.values())
            current = np.random.choice(states, p=probs)
            
            trajectory.append(current)
            
            # Update patient state at new facility
            patient.update_at_facility(current)
        
        return trajectory
```

## 2. Health State Markov Chain

### Three-Phase Health Model as Markov Process

```python
class HealthStateMarkovChain:
    """
    Models health deterioration phases as Markov chain
    States: {Stable, Compensatory, Decompensation, Critical, Died}
    """
    
    def __init__(self):
        self.states = ['Stable', 'Compensatory', 'Decompensation', 'Critical', 'Died']
        
        # Transition rates (per hour) - continuous-time Markov chain
        self.Q_matrix = {
            'Stable': {
                'Stable': -0.1,
                'Compensatory': 0.1,
                'Decompensation': 0,
                'Critical': 0,
                'Died': 0
            },
            'Compensatory': {
                'Stable': 0.05,  # Can improve with treatment
                'Compensatory': -0.25,
                'Decompensation': 0.2,
                'Critical': 0,
                'Died': 0
            },
            'Decompensation': {
                'Stable': 0,
                'Compensatory': 0.02,  # Rare improvement
                'Decompensation': -0.42,
                'Critical': 0.35,
                'Died': 0.05
            },
            'Critical': {
                'Stable': 0,
                'Compensatory': 0,
                'Decompensation': 0.01,  # Very rare improvement
                'Critical': -0.51,
                'Died': 0.5
            },
            'Died': {
                'Died': 0  # Absorbing state
            }
        }
    
    def modify_transitions_with_treatment(self, Q, treatments):
        """
        Treatments modify transition rates
        """
        Q_modified = copy.deepcopy(Q)
        
        for treatment in treatments:
            if treatment.type == 'stabilizing':
                # Reduce deterioration rates
                Q_modified['Compensatory']['Decompensation'] *= 0.5
                Q_modified['Decompensation']['Critical'] *= 0.6
                
            elif treatment.type == 'lifesaving':
                # Increase improvement rates
                Q_modified['Critical']['Decompensation'] *= 2
                Q_modified['Decompensation']['Compensatory'] *= 1.5
                
            elif treatment.type == 'supportive':
                # Slow all transitions
                for state in Q_modified:
                    for next_state in Q_modified[state]:
                        if state != next_state:
                            Q_modified[state][next_state] *= 0.8
        
        return Q_modified
    
    def compute_state_probability(self, initial_state, time, treatments=[]):
        """
        Solve Kolmogorov forward equation for state probabilities
        P'(t) = P(t) * Q
        """
        Q = self.modify_transitions_with_treatment(self.Q_matrix, treatments)
        
        # Convert to matrix form
        Q_matrix = self._dict_to_matrix(Q)
        
        # Matrix exponential for continuous-time Markov chain
        P_t = expm(Q_matrix * time)
        
        # Get initial state vector
        initial_vector = self._state_to_vector(initial_state)
        
        # Compute state probabilities at time t
        state_probs = initial_vector @ P_t
        
        return dict(zip(self.states, state_probs))
    
    def sample_trajectory(self, initial_state, duration, dt=0.1, treatments=[]):
        """
        Sample health state trajectory using Gillespie algorithm
        """
        trajectory = [(0, initial_state)]
        current_state = initial_state
        current_time = 0
        
        Q = self.modify_transitions_with_treatment(self.Q_matrix, treatments)
        
        while current_time < duration and current_state != 'Died':
            # Get transition rates from current state
            rates = {s: max(0, r) for s, r in Q[current_state].items() if s != current_state}
            
            if not rates or sum(rates.values()) == 0:
                break
            
            # Time to next transition (exponential)
            total_rate = sum(rates.values())
            time_to_transition = np.random.exponential(1/total_rate)
            
            current_time += time_to_transition
            
            if current_time > duration:
                break
            
            # Choose next state
            states = list(rates.keys())
            probs = [r/total_rate for r in rates.values()]
            current_state = np.random.choice(states, p=probs)
            
            trajectory.append((current_time, current_state))
        
        return trajectory
```

## 3. Diagnostic Refinement Markov Chain

### Progressive Diagnosis as Hidden Markov Model (HMM)

```python
class DiagnosticHMM:
    """
    Hidden Markov Model where:
    - Hidden states: True medical conditions
    - Observations: Diagnosed conditions at each facility
    - Emission probabilities: Diagnostic accuracy
    """
    
    def __init__(self):
        # Hidden states (true conditions)
        self.hidden_states = [
            'internal_bleeding',
            'tbi_moderate',
            'tension_pneumo',
            'hemorrhagic_shock',
            'multiple_trauma'
        ]
        
        # Observable states (diagnoses)
        self.observations = [
            'shock_unspecified',
            'head_injury',
            'chest_trauma',
            'bleeding_visible',
            'polytrauma'
        ]
        
        # Emission probabilities P(observation | true_state, facility)
        self.emission_probs = {
            'POI': {
                'internal_bleeding': {
                    'shock_unspecified': 0.4,
                    'bleeding_visible': 0.2,
                    'polytrauma': 0.1,
                    # 30% missed entirely
                },
                'tbi_moderate': {
                    'head_injury': 0.5,
                    'shock_unspecified': 0.2,
                    # 30% missed
                }
            },
            'Role1': {
                'internal_bleeding': {
                    'shock_unspecified': 0.2,
                    'bleeding_visible': 0.5,
                    'polytrauma': 0.2,
                    # 10% missed
                }
            },
            'Role2': {
                'internal_bleeding': {
                    'bleeding_visible': 0.85,
                    'polytrauma': 0.1,
                    # 5% missed
                }
            }
        }
        
        # Transition matrix for true conditions (they don't change, but can develop complications)
        self.condition_transitions = {
            'internal_bleeding': {
                'internal_bleeding': 0.7,
                'hemorrhagic_shock': 0.3  # Can progress
            },
            'tbi_moderate': {
                'tbi_moderate': 0.9,
                'multiple_trauma': 0.1  # Can reveal additional injuries
            }
        }
    
    def forward_backward(self, observations, facilities):
        """
        Forward-backward algorithm to compute probability of true conditions
        given sequence of diagnoses across facilities
        """
        T = len(observations)
        N = len(self.hidden_states)
        
        # Forward pass
        alpha = np.zeros((T, N))
        
        # Initialize
        for i, state in enumerate(self.hidden_states):
            alpha[0, i] = self.prior[state] * self.emission_probs[facilities[0]][state].get(observations[0], 0.01)
        
        # Recurse
        for t in range(1, T):
            for j, state_j in enumerate(self.hidden_states):
                for i, state_i in enumerate(self.hidden_states):
                    alpha[t, j] += alpha[t-1, i] * self.condition_transitions[state_i].get(state_j, 0) * \
                                   self.emission_probs[facilities[t]][state_j].get(observations[t], 0.01)
        
        # Backward pass
        beta = np.zeros((T, N))
        beta[T-1, :] = 1
        
        for t in range(T-2, -1, -1):
            for i, state_i in enumerate(self.hidden_states):
                for j, state_j in enumerate(self.hidden_states):
                    beta[t, i] += beta[t+1, j] * self.condition_transitions[state_i].get(state_j, 0) * \
                                  self.emission_probs[facilities[t+1]][state_j].get(observations[t+1], 0.01)
        
        # Compute posterior probabilities
        gamma = alpha * beta
        gamma = gamma / gamma.sum(axis=1, keepdims=True)
        
        return gamma
    
    def viterbi(self, observations, facilities):
        """
        Find most likely sequence of true conditions given observations
        """
        T = len(observations)
        N = len(self.hidden_states)
        
        # Initialize
        delta = np.zeros((T, N))
        psi = np.zeros((T, N), dtype=int)
        
        for i, state in enumerate(self.hidden_states):
            delta[0, i] = np.log(self.prior[state]) + \
                         np.log(self.emission_probs[facilities[0]][state].get(observations[0], 0.01))
        
        # Recurse
        for t in range(1, T):
            for j, state_j in enumerate(self.hidden_states):
                probabilities = []
                for i, state_i in enumerate(self.hidden_states):
                    prob = delta[t-1, i] + \
                           np.log(self.condition_transitions[state_i].get(state_j, 0.01)) + \
                           np.log(self.emission_probs[facilities[t]][state_j].get(observations[t], 0.01))
                    probabilities.append(prob)
                
                delta[t, j] = max(probabilities)
                psi[t, j] = np.argmax(probabilities)
        
        # Backtrack
        path = np.zeros(T, dtype=int)
        path[T-1] = np.argmax(delta[T-1, :])
        
        for t in range(T-2, -1, -1):
            path[t] = psi[t+1, path[t+1]]
        
        return [self.hidden_states[i] for i in path]
```

## 4. Treatment Outcome Markov Chain

### Treatment Response as Markov Process

```python
class TreatmentOutcomeChain:
    """
    Models treatment outcomes as Markov chain
    States: {No Effect, Improving, Stable, Deteriorating, Complication}
    """
    
    def __init__(self):
        self.states = ['No_Effect', 'Improving', 'Stable', 'Deteriorating', 'Complication']
        
    def build_transition_matrix(self, treatment_appropriateness, time_to_treatment, patient_state):
        """
        Transition probabilities depend on:
        - How appropriate the treatment is
        - How quickly it was administered
        - Patient's current state
        """
        
        # Base transitions for appropriate treatment within golden hour
        if treatment_appropriateness > 0.8 and time_to_treatment < 1:  # Good treatment, quick
            P = {
                'No_Effect': {'No_Effect': 0.1, 'Improving': 0.7, 'Stable': 0.2},
                'Improving': {'Improving': 0.6, 'Stable': 0.35, 'Deteriorating': 0.05},
                'Stable': {'Improving': 0.2, 'Stable': 0.7, 'Deteriorating': 0.1},
                'Deteriorating': {'Stable': 0.3, 'Deteriorating': 0.5, 'Complication': 0.2},
                'Complication': {'Deteriorating': 0.4, 'Complication': 0.6}
            }
            
        elif treatment_appropriateness > 0.5:  # Partially appropriate
            P = {
                'No_Effect': {'No_Effect': 0.3, 'Improving': 0.4, 'Stable': 0.3},
                'Improving': {'Improving': 0.4, 'Stable': 0.4, 'Deteriorating': 0.2},
                'Stable': {'Improving': 0.1, 'Stable': 0.6, 'Deteriorating': 0.3},
                'Deteriorating': {'Stable': 0.1, 'Deteriorating': 0.6, 'Complication': 0.3},
                'Complication': {'Deteriorating': 0.3, 'Complication': 0.7}
            }
            
        else:  # Poor treatment
            P = {
                'No_Effect': {'No_Effect': 0.5, 'Deteriorating': 0.5},
                'Improving': {'Stable': 0.3, 'Deteriorating': 0.7},
                'Stable': {'Stable': 0.3, 'Deteriorating': 0.7},
                'Deteriorating': {'Deteriorating': 0.7, 'Complication': 0.3},
                'Complication': {'Complication': 1.0}
            }
        
        # Modify based on golden hour
        if time_to_treatment > 6:  # Well past golden hour
            # Increase deterioration probabilities
            for state in P:
                if 'Deteriorating' in P[state]:
                    P[state]['Deteriorating'] *= 1.5
                if 'Complication' in P[state]:
                    P[state]['Complication'] *= 2.0
                # Renormalize
                total = sum(P[state].values())
                for next_state in P[state]:
                    P[state][next_state] /= total
        
        return P
    
    def simulate_treatment_response(self, initial_state, treatment_plan, duration_hours):
        """
        Simulate patient response to treatment over time
        """
        trajectory = [(0, initial_state)]
        current = initial_state
        
        for hour in range(1, duration_hours + 1):
            # Get transition matrix based on current treatment
            active_treatment = treatment_plan.get_active_treatment(hour)
            
            if active_treatment:
                appropriateness = self.calculate_appropriateness(active_treatment, patient.diagnosis)
                time_since_injury = hour
                P = self.build_transition_matrix(appropriateness, time_since_injury, patient)
            else:
                # No treatment - use deterioration matrix
                P = self.no_treatment_matrix()
            
            # Sample next state
            current_probs = P[current]
            states = list(current_probs.keys())
            probs = list(current_probs.values())
            current = np.random.choice(states, p=probs)
            
            trajectory.append((hour, current))
            
            # Update patient health based on state
            self.update_patient_health(patient, current)
        
        return trajectory
```

## 5. Resource Availability Markov Chain

### Dynamic Resource State Model

```python
class ResourceAvailabilityChain:
    """
    Models resource availability as birth-death Markov chain
    States: Number of available units (0 to capacity)
    """
    
    def __init__(self, resource_type, capacity):
        self.resource_type = resource_type
        self.capacity = capacity
        self.states = list(range(capacity + 1))
        
    def build_generator_matrix(self, arrival_rate, service_rate):
        """
        Build infinitesimal generator for continuous-time Markov chain
        Birth rate: λ (resources becoming available)
        Death rate: μ (resources being consumed)
        """
        Q = np.zeros((self.capacity + 1, self.capacity + 1))
        
        for i in range(self.capacity + 1):
            if i > 0:
                # Resources can be consumed
                Q[i, i-1] = arrival_rate  # Resource used
            if i < self.capacity:
                # Resources can become available
                Q[i, i+1] = service_rate * min(i, self.capacity)  # Resource freed
            
            # Diagonal elements
            Q[i, i] = -sum(Q[i, :])
        
        return Q
    
    def steady_state_distribution(self, arrival_rate, service_rate):
        """
        Compute steady-state probability distribution
        π * Q = 0, sum(π) = 1
        """
        Q = self.build_generator_matrix(arrival_rate, service_rate)
        
        # Add constraint that probabilities sum to 1
        A = np.vstack([Q.T[:-1], np.ones(self.capacity + 1)])
        b = np.zeros(self.capacity + 1)
        b[-1] = 1
        
        steady_state = np.linalg.solve(A, b)
        
        return steady_state
    
    def availability_probability(self, needed_units, arrival_rate, service_rate):
        """
        Probability that at least 'needed_units' are available
        """
        pi = self.steady_state_distribution(arrival_rate, service_rate)
        return sum(pi[needed_units:])
```

## 6. Complete System Integration

### Master Markov Chain Orchestrator

```python
class MasterMarkovSystem:
    """
    Coordinates all Markov chains in the system
    """
    
    def __init__(self):
        self.facility_chain = FacilityTransitionChain()
        self.health_chain = HealthStateMarkovChain()
        self.diagnostic_hmm = DiagnosticHMM()
        self.treatment_chain = TreatmentOutcomeChain()
        self.resource_chains = {}
        
    def simulate_patient_journey(self, patient, warfare_context):
        """
        Complete patient simulation using interconnected Markov chains
        """
        journey = {
            'facility_trajectory': [],
            'health_trajectory': [],
            'diagnostic_trajectory': [],
            'treatment_trajectory': [],
            'resource_impacts': []
        }
        
        # Initialize
        current_facility = 'POI'
        current_health_state = self.determine_initial_health_state(patient.injuries)
        observations = []
        facilities_visited = []
        
        while current_facility not in ['Died', 'RTD']:
            # 1. Diagnostic process (HMM)
            diagnosis = self.diagnostic_hmm.observe(patient.true_condition, current_facility)
            observations.append(diagnosis)
            facilities_visited.append(current_facility)
            
            # Update belief about true condition
            if len(observations) > 1:
                posterior = self.diagnostic_hmm.forward_backward(observations, facilities_visited)
                patient.diagnostic_confidence = posterior.max()
            
            # 2. Check resource availability (Birth-Death chain)
            resources_needed = self.determine_resource_needs(diagnosis)
            for resource in resources_needed:
                if resource in self.resource_chains:
                    availability = self.resource_chains[resource].check_availability()
                    if availability < 0.5:  # Resource scarce
                        # Modify treatment options
                        journey['resource_impacts'].append((current_facility, resource, 'scarce'))
            
            # 3. Treatment selection and outcome (Treatment chain)
            treatment = self.select_treatment(diagnosis, current_facility, resource_availability)
            treatment_state = 'No_Effect'
            treatment_trajectory = self.treatment_chain.simulate_treatment_response(
                treatment_state, treatment, duration=4  # 4 hours at facility
            )
            journey['treatment_trajectory'].extend(treatment_trajectory)
            
            # 4. Health state evolution (Health state chain)
            health_trajectory = self.health_chain.sample_trajectory(
                current_health_state, 
                duration=4,
                treatments=[treatment]
            )
            journey['health_trajectory'].extend(health_trajectory)
            current_health_state = health_trajectory[-1][1]
            
            # 5. Facility transition decision (Facility chain)
            patient.update_state(current_health_state, treatment_trajectory[-1][1])
            next_facility = self.facility_chain.sample_next_state(current_facility, patient)
            
            journey['facility_trajectory'].append((current_facility, next_facility))
            current_facility = next_facility
        
        return journey
    
    def analyze_system_performance(self, n_simulations=1000):
        """
        Monte Carlo analysis using Markov chains
        """
        results = {
            'mortality_by_path': defaultdict(int),
            'average_facilities_visited': [],
            'diagnostic_convergence': [],
            'resource_bottlenecks': defaultdict(int)
        }
        
        for _ in range(n_simulations):
            patient = self.generate_patient()
            journey = self.simulate_patient_journey(patient, warfare_context)
            
            # Analyze paths
            path = '->'.join([f[0] for f in journey['facility_trajectory']])
            outcome = journey['facility_trajectory'][-1][1]
            results['mortality_by_path'][path] += (1 if outcome == 'Died' else 0)
            
            # Diagnostic convergence
            if len(journey['diagnostic_trajectory']) > 0:
                convergence_rate = journey['diagnostic_trajectory'][-1]['confidence'] / len(journey['facility_trajectory'])
                results['diagnostic_convergence'].append(convergence_rate)
            
            # Resource bottlenecks
            for facility, resource, status in journey['resource_impacts']:
                if status == 'scarce':
                    results['resource_bottlenecks'][(facility, resource)] += 1
        
        return results
```

## 7. Validation Using Markov Chain Properties

### Analytical Validation

```python
def validate_markov_properties():
    """
    Verify Markov chains satisfy required properties
    """
    
    # 1. Verify transition matrices are stochastic
    facility_chain = FacilityTransitionChain()
    P = facility_chain.base_transitions
    
    for state in P:
        row_sum = sum(P[state].values())
        assert abs(row_sum - 1.0) < 1e-6, f"Row {state} doesn't sum to 1: {row_sum}"
    
    # 2. Verify absorbing states
    absorbing_states = ['Died', 'RTD']
    for state in absorbing_states:
        assert P[state][state] == 1.0, f"{state} is not absorbing"
    
    # 3. Calculate expected time to absorption
    transient_states = [s for s in P if s not in absorbing_states]
    Q = extract_transient_submatrix(P, transient_states)
    N = np.linalg.inv(np.eye(len(Q)) - Q)  # Fundamental matrix
    
    expected_steps = N.sum(axis=1)  # Expected time to absorption
    print(f"Expected steps to outcome: {expected_steps.mean():.2f}")
    
    # 4. Steady-state analysis for health states
    health_chain = HealthStateMarkovChain()
    eigenvalues, eigenvectors = np.linalg.eig(health_chain.Q_matrix)
    
    # Find steady-state (eigenvalue = 0)
    steady_state_idx = np.argmin(np.abs(eigenvalues))
    steady_state = np.abs(eigenvectors[:, steady_state_idx])
    steady_state /= steady_state.sum()
    
    print(f"Long-term health distribution: {dict(zip(health_chain.states, steady_state))}")
    
    # 5. Compute transition probability after n steps
    n_steps = 10
    P_n = matrix_power(P, n_steps)
    print(f"Probability POI->RTD in {n_steps} steps: {P_n['POI']['RTD']:.3f}")
```

## Key Benefits of Markov Chain Integration

1. **Analytical Tractability**: Can compute exact probabilities for outcomes
2. **Memoryless Property**: Simplifies computation while maintaining realism
3. **Steady-State Analysis**: Understand long-term system behavior
4. **Absorption Times**: Calculate expected time to outcomes
5. **Sensitivity Analysis**: See how transition probability changes affect outcomes

## Implementation Priority

1. **Immediate**: Add FacilityTransitionChain to replace current random transitions
2. **High**: Implement HealthStateMarkovChain for realistic phase transitions  
3. **High**: Add DiagnosticHMM for diagnostic uncertainty modeling
4. **Medium**: Integrate TreatmentOutcomeChain for treatment response
5. **Medium**: Add ResourceAvailabilityChain for dynamic resources

## Validation Metrics Using Markov Chains

- **Path Analysis**: Most common evacuation paths match real data
- **Absorption Probability**: P(Death|Severity) matches published rates
- **Mean Time to Treatment**: Average steps to definitive care
- **Diagnostic Convergence**: Information gain per facility transition
- **Resource Utilization**: Steady-state resource availability

This Markov chain framework provides the mathematical rigor to properly model the probabilistic transitions throughout the military medical system, ensuring that outcomes emerge naturally from the state-dependent probability structure rather than being hardcoded.
