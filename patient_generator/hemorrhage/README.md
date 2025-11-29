# Hemorrhage Modeling System Implementation

## Overview
This implementation connects the uncontrolled bleeding model from Table 1 of the SIMEDIS research to your existing medical patient generator. The system maps injury types to body locations and calculates realistic hemorrhage parameters.

## Key Features

### 1. Body Region Modeling (`body_regions.py`)
- **10 body regions** defined (head, neck, chest, abdomen, pelvis, arms, legs, back)
- **Vessel types** categorized (major artery, limb artery, small vessel, organ, capillary)
- **Tourniquetable regions** identified (arms and legs only)
- **Anatomical mapping** of major vessels and organs per region

### 2. Hemorrhage Categories (`hemorrhage_model.py`)
Directly implements Table 1 from the research:

| Category | α₀ (hr⁻¹) | k Factor | Blood Loss (ml/min) |
|----------|-----------|----------|-------------------|
| Small limb wounds | 0.1-0.3 | 0.02 | 10-30 |
| Major limb artery | 2.0-5.0 | 0.05 | 200-500 |
| Torso wound | 0.5-2.0 | 0.10 | 50-200 |
| Multiple penetrating | 1.0-3.0 | 0.15 | 100-300 |
| Massive hemorrhage | >10.0 | 0.30 | 1000-2500 |

### 3. SNOMED Code Mapping
Your existing injury codes are mapped to hemorrhage profiles:
- **262574004** (Bullet wound) → High risk, deep vessel damage
- **284551006** (Traumatic amputation) → Critical risk, major artery
- **125689001** (Shrapnel) → Moderate risk, multiple small wounds
- **361220002** (Penetrating injury) → High risk, organ damage
- And more...

### 4. Integration Features (`integration.py`)
- **Blood volume tracking** over time with lethal triad progression
- **Tourniquet effects** (95% bleeding reduction when applicable)
- **Treatment priority** calculation based on time to critical
- **Clinical reports** generation

## Usage Examples

### Basic Usage
```python
from patient_generator.hemorrhage import HemorrhageModel, BodyRegion

# Calculate hemorrhage for a bullet wound to the leg
profile = HemorrhageModel.calculate_hemorrhage_profile(
    injury_code="262574004",  # Bullet wound SNOMED code
    body_region=BodyRegion.LEFT_LEG,
    severity="Severe"
)

print(f"Blood loss rate: {profile.blood_loss_ml_per_min} ml/min")
print(f"Tourniquetable: {profile.controllable}")
print(f"Time to exsanguination: {profile.time_to_exsanguination_min} min")
```

### With Existing Medical Generator
```python
from patient_generator.hemorrhage.enhanced_medical_generator import EnhancedMedicalConditionGenerator

generator = EnhancedMedicalConditionGenerator()

# Generate condition with hemorrhage profile
condition = generator.generate_condition_with_hemorrhage(
    injury_type="Battle Injury",
    triage_category="T1"
)

# Access hemorrhage data
if condition['hemorrhage']['has_hemorrhage']:
    print(f"Category: {condition['hemorrhage']['category']}")
    print(f"Blood loss: {condition['hemorrhage']['blood_loss_ml_min']} ml/min")
    print(f"Body region: {condition['body_location']['region']}")
```

### Multiple Injuries (Polytrauma)
```python
# Generate multiple injuries with combined effects
conditions = generator.generate_multiple_conditions_with_hemorrhage(
    "Battle Injury", "T1", count=3
)

# Calculate combined hemorrhage effects
combined = generator.calculate_combined_hemorrhage_effects(conditions)
print(f"Total blood loss: {combined['total_blood_loss_ml_min']} ml/min")
print(f"Time to critical: {combined['time_to_critical_min']} minutes")
print(f"Recommended triage: {combined['recommended_triage']}")
```

## Key Algorithms

### Blood Volume Depletion
```
BV(t) = BV₀ * e^(-αt)
Where α = α₀ + kt (lethal triad progression)
```

### Death Conditions
- Blood volume < 40% (2L of 5L total)
- Hemorrhagic shock threshold

### Tourniquet Effects
- Applicable only to limb regions
- Reduces bleeding by 95% when applied
- Not effective for junctional areas (neck, pelvis, shoulders)

## Testing
Run the test script to verify the implementation:
```bash
python test_hemorrhage_model.py
```

This will demonstrate:
1. Direct hemorrhage calculations
2. Integration with medical generator
3. Blood volume timeline simulation
4. Category mapping verification

## Integration Path

### Phase 1: Current Implementation ✓
- Hemorrhage model as separate module
- Maps to existing SNOMED codes
- Calculates bleeding parameters

### Phase 2: Database Integration (Next)
- Add hemorrhage_profiles table
- Store blood volume timelines
- Track tourniquet applications

### Phase 3: Full SimedisScore System
- Implement complete SS calculation
- Add Gompertz deterioration curves
- Integrate treatment effects

## Benefits
1. **Realistic bleeding modeling** based on validated research
2. **Body location awareness** for tourniquet decisions
3. **Multiple injury handling** with combined effects
4. **Treatment prioritization** based on hemorrhage severity
5. **Compatible** with existing medical condition generator

## Next Steps
1. Test with your actual patient data
2. Adjust parameters based on your specific scenarios
3. Add to patient flow simulator for timeline tracking
4. Integrate with visualization components
