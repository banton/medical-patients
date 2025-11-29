# Medical Simulation Enhancement - Implementation Plan

## Overview
Comprehensive plan to enhance the medical patient generator with realistic deterioration, transport logistics, and efficient data handling.

## Completed Design Work ✅

### Configuration Files Created
1. **deterioration_rates.json** - Health score system (0-100) with modifiers
2. **blood_loss.json** - Hemorrhage profiles and transfusion effects
3. **treatment_effects.json** - Treatment modifiers by medical role
4. **mtf_capacities.json** - Facility capacities with CSU locations
5. **transport_logistics.json** - Nation-specific medical assets
6. **overflow_rules.json** - Evacuation doctrine and routing logic

### Architectural Decisions
- **Simplified health score** instead of complex vital signs
- **Simple hemorrhage modifiers** instead of 1127-line overengineered system
- **Two-tier metadata** for API messaging and retrospective analysis
- **Single-file gzip compression** for 90% size reduction

## Implementation Phases

### Phase 1: Core Health System (Week 1)
- [ ] Build config_loader module with validation
- [ ] Implement simplified deterioration_engine.py
- [ ] Implement blood_loss_tracker.py
- [ ] Extend Patient model with health score
- [ ] Add hemorrhage as simple modifier

**Deliverables**: Patients with health scores that deteriorate over time

### Phase 2: Transport & Facilities (Week 2)
- [ ] Implement facility_manager.py with overflow logic
- [ ] Implement transport_coordinator.py
- [ ] Add CSU batch evacuation logic
- [ ] Implement "died in transit" tracking
- [ ] Add 3-zone body regions (extremity/junctional/central)

**Deliverables**: Realistic patient flow through medical facilities

### Phase 3: Enhanced Realism (Week 3)
- [ ] Implement tourniquet time windows
- [ ] Add surgery priority scoring
- [ ] Implement cliff events for deterioration
- [ ] Add mass casualty incident tags
- [ ] Create surgical requirements config

**Deliverables**: Nuanced medical decisions and outcomes

### Phase 4: Data Optimization (Week 4)
- [ ] Implement data compression strategy
- [ ] Update patient generator for optimized output
- [ ] Update React viewer for compressed files
- [ ] Design comprehensive patient metadata structure
- [ ] Implement retrospective analysis features

**Deliverables**: Efficient data handling with rich metadata

### Phase 5: Testing & Documentation (Week 5)
- [ ] Write tests for overflow scenarios
- [ ] Test deterioration accuracy
- [ ] Validate transport logistics
- [ ] Create comprehensive documentation
- [ ] Performance optimization

**Deliverables**: Production-ready system with documentation

## Key Features to Implement

### 1. Health Score System
```python
# Simple deterioration
health = 100 - (deterioration_rate * hours * modifiers)
# Map to triage
T3: >70, T2: 40-70, T1: 10-40, Expectant: <10
```

### 2. Hemorrhage Modifiers
```python
# Simple approach - no complex anatomy
if hemorrhage_severe:
    deterioration_rate *= 2.0
if tourniquet_applied:
    deterioration_rate *= 0.5
```

### 3. Body Regions (3 zones only)
```python
zones = {
    "extremity": {"tourniquetable": True},
    "junctional": {"tourniquetable": False},  # Groin/armpit
    "central": {"tourniquetable": False}      # Torso/head
}
```

### 4. Tourniquet Time Windows
```python
effectiveness = {
    "0-5min": 0.3,     # 70% reduction
    "5-30min": 0.5,    # 50% reduction
    "30-120min": 0.7,  # 30% reduction
    "120+min": 1.2     # Harmful
}
```

### 5. Surgery Priority
```python
priority = hemorrhage_severity * (100 - blood_volume) / 100
```

### 6. Cliff Events
```python
events = {
    "moved_unstable": 1.5,
    "hypothermic": 1.3,
    "failed_airway": 3.0
}
```

### 7. Data Compression
```javascript
// 90% size reduction
patients.json (20MB) → patients.json.gz (2MB)
// Abbreviated keys, numeric codes, omit defaults
```

## Success Metrics

1. **Realism**: Combat medics recognize patterns
2. **Performance**: Generate 1000 patients < 30 seconds
3. **Data Size**: < 2KB per patient compressed
4. **API Ready**: Legitimate medical scenarios
5. **Training Value**: Identifies improvement areas

## Risk Mitigation

1. **Overengineering**: Keep solutions simple (< 100 lines per module)
2. **Performance**: Profile early, optimize critical paths
3. **Compatibility**: No legacy concerns in early development
4. **Validation**: Test against real medical patterns

## Next Steps

1. Start with Phase 1 core health system
2. Test deterioration calculations
3. Integrate with existing patient generator
4. Validate with sample scenarios
5. Iterate based on feedback

## Notes

- No need for database migrations (early development)
- Breaking changes acceptable
- Focus on API legitimacy over UI features
- Maintain single-file portability
- Balance realism with simplicity

---

*This plan provides a roadmap for implementing realistic medical simulation while maintaining system simplicity and data efficiency.*