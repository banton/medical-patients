# Warfare Pattern Integration with Probabilistic Models

## Overview

The `warfare_patterns.json` file contains rich warfare-specific data that must be integrated throughout all 12 probabilistic models and Markov chains. This document shows how warfare patterns modify every aspect of the simulation.

## Warfare Types and Their Impact

### 1. Artillery/Indirect Fire
**Characteristics:**
- Mass casualty probability: 80%
- Cluster size: 15-50 casualties
- Surge pattern: 3 surges/day, 5x intensity during surges
- Injury modifier: Battle Injury 2.5x

**Markov Chain Modifications:**
```python
class ArtilleryWarfareModifier:
    def modify_facility_chain(self, base_P):
        """Artillery casualties have different flow patterns"""
        P = base_P.copy()
        
        # Higher immediate mortality (blast injuries)
        P['POI']['Died'] *= 1.8
        
        # More bypass to Role2 (severe polytrauma)
        P['POI']['Role2'] *= 1.5
        P['POI']['Role1'] *= 0.8
        
        # Higher surgical needs
        P['Role1']['Role2'] *= 1.3
        
        return self.normalize(P)
    
    def modify_health_chain(self, base_Q):
        """Blast injuries deteriorate faster"""
        Q = base_Q.copy()
        
        # Faster progression through health states
        Q['Compensatory']['Decompensation'] *= 1.5
        Q['Decompensation']['Critical'] *= 1.4
        Q['Critical']['Died'] *= 1.3
        
        return Q
    
    def modify_injury_generation(self):
        """Artillery creates specific injury patterns"""
        return {
            'primary_blast': 0.8,    # Overpressure injuries
            'secondary_blast': 0.9,   # Fragment injuries
            'tertiary_blast': 0.6,    # Displacement injuries
            'thermal': 0.3,           # Burns from explosions
            'crush': 0.4              # Building collapse
        }
```

### 2. Urban Combat
**Characteristics:**
- Mass casualty probability: 40%
- Dispersed casualties over time
- High civilian mix
- Complex evacuation

**Markov Chain Modifications:**
```python
class UrbanCombatModifier:
    def modify_facility_chain(self, base_P):
        """Urban combat has delayed evacuation"""
        P = base_P.copy()
        
        # Longer time at POI (access issues)
        P['POI']['POI'] = 0.2  # Self-loop for delay
        P['POI']['Role1'] *= 0.7
        
        # More RTD at lower levels (minor injuries)
        P['Role1']['RTD'] *= 1.3
        
        return self.normalize(P)
    
    def modify_diagnostic_hmm(self, base_emissions):
        """Urban injuries harder to diagnose (multiple mechanisms)"""
        emissions = base_emissions.copy()
        
        # Reduce diagnostic accuracy at POI
        emissions['POI']['accuracy'] *= 0.9
        
        # Increase confusion between injury types
        emissions['POI']['confusion_matrix']['ballistic']['blast'] = 0.3
        emissions['POI']['confusion_matrix']['crush']['fracture'] = 0.4
        
        return emissions
```

### 3. IED (Improvised Explosive Device)
**Characteristics:**
- Classic triad: TBI + amputation + burns
- Small cluster size: 3-8 casualties
- Random timing
- High severity

**Probabilistic Model Modifications:**
```python
class IEDWarfareModifier:
    def modify_poisson_process(self):
        """IEDs have random timing"""
        return {
            'type': 'homogeneous',  # No time pattern
            'base_rate': 2.0,       # Events per day
            'casualties_per_event': PoissonDistribution(lambda=4)
        }
    
    def modify_injury_correlation(self):
        """IED injuries are highly correlated (classic triad)"""
        correlation_matrix = np.array([
            [1.0, 0.8, 0.7],  # TBI correlates with amputation
            [0.8, 1.0, 0.9],  # Amputation correlates with burns
            [0.7, 0.9, 1.0]   # Burns correlate with both
        ])
        return GaussianCopula(correlation_matrix)
    
    def modify_treatment_urgency(self):
        """IED casualties need immediate surgery"""
        return {
            'golden_hour': 0.5,  # 30 minutes for tourniquets
            'surgery_window': 2.0,  # 2 hours for amputation
            'blood_requirement': 'massive',  # 10+ units typical
        }
```

### 4. Counterinsurgency
**Characteristics:**
- Low intensity, persistent
- Mixed combatant/civilian
- Psychological stress high
- Disease component

**Markov Chain Modifications:**
```python
class CounterinsurgencyModifier:
    def modify_all_chains(self):
        modifications = {
            'facility_chain': {
                'POI->RTD': 1.5,  # More minor injuries
                'Role1->Psych': 2.0  # Higher psychological
            },
            'health_chain': {
                'deterioration_rate': 0.7,  # Slower progression
                'cliff_probability': 0.5  # Fewer acute events
            },
            'diagnostic_hmm': {
                'psychological_detection': 1.5,  # Better psych screening
                'disease_detection': 1.3  # More disease awareness
            }
        }
        return modifications
```

## Complete Warfare Pattern Integration

### Master Warfare Context Manager
```python
class WarfareContextManager:
    """
    Maintains warfare context throughout patient journey
    and modifies all probabilistic models accordingly
    """
    
    def __init__(self):
        self.patterns = self.load_warfare_patterns()
        self.active_warfare = None
        self.modifiers = {
            'artillery': ArtilleryWarfareModifier(),
            'urban': UrbanCombatModifier(),
            'ied': IEDWarfareModifier(),
            'conventional': ConventionalWarfareModifier(),
            'counterinsurgency': CounterinsurgencyModifier()
        }
    
    def set_warfare_context(self, warfare_type):
        """Set active warfare type for simulation"""
        self.active_warfare = warfare_type
        self.active_pattern = self.patterns[warfare_type]
        self.active_modifier = self.modifiers[warfare_type]
    
    def get_modified_markov_chains(self):
        """Return all Markov chains modified for warfare type"""
        return {
            'facility': self.active_modifier.modify_facility_chain(
                self.base_facility_chain
            ),
            'health': self.active_modifier.modify_health_chain(
                self.base_health_chain
            ),
            'diagnostic': self.active_modifier.modify_diagnostic_hmm(
                self.base_diagnostic_hmm
            ),
            'treatment': self.active_modifier.modify_treatment_chain(
                self.base_treatment_chain
            ),
            'resource': self.active_modifier.modify_resource_chain(
                self.base_resource_chain
            )
        }
    
    def get_injury_mechanism_distribution(self):
        """Get warfare-specific injury mechanism probabilities"""
        base_mechanisms = {
            'blast': 0.1,
            'ballistic': 0.3,
            'burn': 0.05,
            'crush': 0.05,
            'psychological': 0.1
        }
        
        # Apply warfare-specific modifiers
        warfare_mods = self.active_pattern['injury_mechanism_modifiers']
        
        modified = {}
        for mechanism, base_prob in base_mechanisms.items():
            modified[mechanism] = base_prob * warfare_mods.get(mechanism, 1.0)
        
        # Normalize to sum to 1
        total = sum(modified.values())
        return {k: v/total for k, v in modified.items()}
    
    def get_temporal_intensity(self, time_of_day):
        """Get casualty intensity based on warfare temporal pattern"""
        pattern = self.active_pattern['temporal_pattern']
        
        if pattern['type'] == 'surge':
            # Artillery-style surges
            if time_of_day in pattern['preferred_hours']:
                return pattern['surge_intensity']
            else:
                return pattern['between_surge_intensity']
                
        elif pattern['type'] == 'sustained_combat':
            # Conventional warfare
            if time_of_day in pattern['peak_hours']:
                return pattern['peak_intensity']
            elif self.is_night(time_of_day):
                return pattern['base_intensity'] * pattern['night_reduction']
            else:
                return pattern['base_intensity']
                
        elif pattern['type'] == 'random':
            # IED pattern
            return pattern['base_intensity']  # Constant rate
            
        else:
            return 1.0
    
    def get_triage_distribution(self, injury_type):
        """Get warfare-specific triage distribution"""
        return self.active_pattern['triage_weights'][injury_type]
    
    def get_mass_casualty_parameters(self):
        """Get mass casualty event parameters"""
        clustering = self.active_pattern['casualty_clustering']
        
        if np.random.random() < clustering['mass_casualty_probability']:
            # Generate mass casualty event
            size = np.random.randint(
                clustering['cluster_size_range'][0],
                clustering['cluster_size_range'][1]
            )
            duration = np.random.uniform(
                clustering.get('cluster_duration_minutes', [10, 30])[0],
                clustering.get('cluster_duration_minutes', [10, 30])[1]
            )
            return {'is_mass_casualty': True, 'size': size, 'duration': duration}
        else:
            return {'is_mass_casualty': False, 'size': 1, 'duration': 0}
```

## Warfare-Specific Probability Modifications

### 1. Poisson Process Modifications
```python
def get_warfare_modified_poisson_rate(warfare_type, base_rate, time):
    """Modify Poisson rate based on warfare pattern"""
    
    context = WarfareContextManager()
    context.set_warfare_context(warfare_type)
    
    # Base rate modification
    weight_multiplier = context.active_pattern['weight_multiplier']
    
    # Temporal modification
    temporal_intensity = context.get_temporal_intensity(time)
    
    # Mass casualty adjustment
    mass_cas_params = context.get_mass_casualty_parameters()
    if mass_cas_params['is_mass_casualty']:
        return base_rate * weight_multiplier * temporal_intensity * 5
    else:
        return base_rate * weight_multiplier * temporal_intensity
```

### 2. Gaussian Copula Correlation Modifications
```python
def get_warfare_correlation_matrix(warfare_type):
    """Get injury correlation matrix for warfare type"""
    
    matrices = {
        'artillery': np.array([
            [1.0, 0.8, 0.7, 0.6],  # Blast injuries highly correlated
            [0.8, 1.0, 0.7, 0.5],
            [0.7, 0.7, 1.0, 0.4],
            [0.6, 0.5, 0.4, 1.0]
        ]),
        'ied': np.array([
            [1.0, 0.9, 0.8],  # Classic triad strongly correlated
            [0.9, 1.0, 0.9],
            [0.8, 0.9, 1.0]
        ]),
        'urban': np.array([
            [1.0, 0.3, 0.2, 0.2],  # Mixed injuries, lower correlation
            [0.3, 1.0, 0.2, 0.1],
            [0.2, 0.2, 1.0, 0.1],
            [0.2, 0.1, 0.1, 1.0]
        ])
    }
    
    return matrices.get(warfare_type, np.eye(4) * 0.5)
```

### 3. Treatment Utility Modifications
```python
def modify_treatment_utility_weights(warfare_type):
    """Adjust treatment utility weights based on warfare"""
    
    base_weights = {
        'appropriateness': 0.5,
        'resources': 0.3,
        'time': 0.2
    }
    
    warfare_adjustments = {
        'artillery': {
            'time': 0.4,  # Golden hour more critical
            'resources': 0.2,  # Resources overwhelmed anyway
            'appropriateness': 0.4
        },
        'ied': {
            'time': 0.5,  # Immediate surgery needed
            'appropriateness': 0.4,
            'resources': 0.1
        },
        'counterinsurgency': {
            'appropriateness': 0.6,  # More time for proper care
            'resources': 0.3,
            'time': 0.1
        }
    }
    
    return warfare_adjustments.get(warfare_type, base_weights)
```

## Integration Points in Master Controller

```python
class MasterSimulationController:
    def __init__(self, scenario):
        # Initialize warfare context first
        self.warfare_context = WarfareContextManager()
        self.warfare_context.set_warfare_context(scenario.warfare_type)
        
        # Get modified Markov chains
        modified_chains = self.warfare_context.get_modified_markov_chains()
        
        # Initialize chains with warfare modifications
        self.facility_chain = modified_chains['facility']
        self.health_chain = modified_chains['health']
        self.diagnostic_hmm = modified_chains['diagnostic']
        self.treatment_chain = modified_chains['treatment']
        self.resource_chain = modified_chains['resource']
        
        # Initialize other models with warfare context
        self.injury_generator = InjuryGenerator(
            mechanism_dist=self.warfare_context.get_injury_mechanism_distribution(),
            correlation_matrix=get_warfare_correlation_matrix(scenario.warfare_type)
        )
        
        self.treatment_selector = TreatmentSelector(
            utility_weights=modify_treatment_utility_weights(scenario.warfare_type)
        )
        
        self.event_generator = CasualtyEventGenerator(
            rate_modifier=lambda t: self.warfare_context.get_temporal_intensity(t)
        )
    
    def generate_patient(self, event):
        """Generate patient with warfare context"""
        
        # Get warfare-specific injury mechanisms
        mechanisms = self.warfare_context.get_injury_mechanism_distribution()
        
        # Sample mechanisms based on warfare type
        selected_mechanisms = np.random.choice(
            list(mechanisms.keys()),
            p=list(mechanisms.values()),
            size=np.random.poisson(3)  # Average 3 mechanisms
        )
        
        # Generate correlated injuries
        correlation_matrix = get_warfare_correlation_matrix(
            self.warfare_context.active_warfare
        )
        injuries = self.injury_generator.generate_polytrauma(
            selected_mechanisms,
            correlation_matrix
        )
        
        # Assign warfare-specific triage
        injury_type = self.classify_injury_type(injuries)
        triage_dist = self.warfare_context.get_triage_distribution(injury_type)
        triage = np.random.choice(
            ['T1', 'T2', 'T3'],
            p=list(triage_dist.values())
        )
        
        return Patient(
            injuries=injuries,
            triage=triage,
            warfare_context=self.warfare_context.active_warfare,
            mass_casualty=event.is_mass_casualty
        )
```

## Validation of Warfare Pattern Integration

```python
def validate_warfare_patterns():
    """Ensure warfare patterns properly modify system behavior"""
    
    results = {}
    
    for warfare_type in ['artillery', 'urban', 'ied', 'conventional']:
        # Run 1000 simulations for each warfare type
        controller = MasterSimulationController(
            scenario=Scenario(warfare_type=warfare_type)
        )
        
        outcomes = []
        for _ in range(1000):
            patient = controller.generate_patient(event)
            journey = controller.simulate_patient_journey(patient)
            outcomes.append(journey)
        
        # Validate warfare-specific patterns
        results[warfare_type] = {
            'polytrauma_rate': calculate_polytrauma_rate(outcomes),
            'mortality_rate': calculate_mortality_rate(outcomes),
            'mass_casualty_rate': calculate_mass_casualty_rate(outcomes),
            'evacuation_pattern': analyze_evacuation_paths(outcomes),
            'resource_exhaustion': check_resource_exhaustion(outcomes)
        }
    
    # Expected patterns
    assert results['artillery']['polytrauma_rate'] > 0.80
    assert results['artillery']['mass_casualty_rate'] > 0.70
    assert results['ied']['polytrauma_rate'] > 0.90  # Classic triad
    assert results['urban']['evacuation_pattern']['delayed'] > 0.30
    assert results['counterinsurgency']['mortality_rate'] < 0.10
    
    return results
```

## Configuration File Integration

```yaml
# warfare_integration_config.yaml
warfare_modifications:
  artillery:
    markov_chains:
      facility_transition:
        POI_to_Died: 1.8
        POI_to_Role2: 1.5
      health_state:
        deterioration_multiplier: 1.4
      diagnostic_accuracy:
        POI_accuracy: 0.55  # Harder under fire
    
    injury_mechanisms:
      primary_blast: 0.8
      secondary_blast: 0.9
      tertiary_blast: 0.6
    
    correlation_strength: 0.8
    
    poisson_rate_multiplier: 2.5
    
  urban:
    markov_chains:
      facility_transition:
        POI_self_loop: 0.2  # Delayed evac
        Role1_to_RTD: 1.3
      health_state:
        deterioration_multiplier: 1.1
    
    injury_mechanisms:
      ballistic: 0.5
      crush: 0.3
      burn: 0.2
    
    correlation_strength: 0.3
    
  ied:
    markov_chains:
      facility_transition:
        POI_to_Role2: 2.0  # Bypass for surgery
      health_state:
        cliff_event_probability: 2.0
    
    injury_mechanisms:
      blast: 0.9
      amputation: 0.7
      burn: 0.6
      tbi: 0.8
    
    correlation_strength: 0.9  # Classic triad
```

## Summary

The warfare patterns are now fully integrated throughout the system:

1. **Markov Chain Modifications**: Each warfare type modifies all 5 Markov chain transition matrices
2. **Injury Generation**: Warfare determines mechanism distribution and correlation strength
3. **Temporal Patterns**: Poisson process rates vary based on warfare-specific timing
4. **Triage Distribution**: Warfare type affects initial triage categories
5. **Resource Strain**: Mass casualty probabilities affect queue behavior
6. **Treatment Priorities**: Utility weights adjust based on warfare urgency
7. **Diagnostic Challenges**: HMM emission probabilities modified by warfare chaos

This ensures that an artillery barrage produces fundamentally different casualty patterns, flow dynamics, and outcomes than urban combat or IED attacks, making the simulation realistic for different warfare scenarios.
