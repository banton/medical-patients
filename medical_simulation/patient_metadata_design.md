# Patient Metadata Design for Retrospective Analysis

## Purpose
Generate realistic patient records with comprehensive metadata for:
1. API messages to external training systems
2. Post-exercise retrospective analysis
3. Statistical analysis of battlefield medicine outcomes
4. After-action review (AAR) training insights

## Core Patient Metadata Structure

### 1. Initial Injury Metadata
```json
{
  "patient_id": "POL-2024-00142",
  "injury_timestamp": "2024-03-15T06:42:00Z",
  "injury_mechanism": "gsw",
  "body_region": "extremity",  // extremity|junctional|central
  "specific_location": "right_upper_thigh",
  "hemorrhage_classification": {
    "severity": "severe",
    "rate_per_hour": 5.0,
    "tourniquetable": true,
    "control_attempted": "2024-03-15T06:47:00Z",
    "control_method": "tourniquet",
    "control_effectiveness": 0.3  // 70% reduction
  },
  "initial_triage": "T1",
  "initial_health_score": 55,
  "blood_volume_percent": 100
}
```

### 2. Treatment Timeline Metadata
```json
{
  "treatments_applied": [
    {
      "timestamp": "2024-03-15T06:47:00Z",
      "treatment": "tourniquet",
      "location": "POI",
      "provider": "combat_medic",
      "effectiveness": 0.3,
      "time_to_treatment_min": 5,
      "quality_score": 0.9,  // How well was it applied
      "complications": []
    },
    {
      "timestamp": "2024-03-15T07:15:00Z",
      "treatment": "iv_fluids",
      "location": "Role1",
      "provider": "physician_assistant",
      "effectiveness": 0.8,
      "time_to_treatment_min": 33,
      "quality_score": 0.95,
      "complications": ["difficult_iv_access"]
    }
  ],
  "golden_hour_status": "partial",  // met|partial|missed
  "tourniquet_time_window": "optimal"  // optimal|effective|degraded|harmful
}
```

### 3. Deterioration Events Metadata
```json
{
  "deterioration_events": [
    {
      "timestamp": "2024-03-15T07:45:00Z",
      "event": "moved_while_unstable",
      "health_before": 48,
      "health_after": 42,
      "deterioration_multiplier": 1.5,
      "location": "Role1_to_CSU",
      "preventable": true
    },
    {
      "timestamp": "2024-03-15T08:30:00Z",
      "event": "facility_full_bypass",
      "health_before": 38,
      "health_after": 32,
      "deterioration_multiplier": 1.2,
      "location": "Role2_bypass_to_Role3",
      "preventable": "potentially"
    }
  ],
  "cliff_events": [
    {
      "timestamp": "2024-03-15T09:15:00Z",
      "event": "hemorrhagic_shock",
      "triggered_by": "blood_volume_below_40",
      "cascade_effects": ["tachycardia", "hypotension", "altered_mental_status"]
    }
  ]
}
```

### 4. Facility Flow Metadata
```json
{
  "facility_timeline": [
    {
      "facility": "POI",
      "arrival": "2024-03-15T06:42:00Z",
      "departure": "2024-03-15T07:00:00Z",
      "duration_min": 18,
      "reason_for_transfer": "standard_evacuation",
      "health_on_arrival": 55,
      "health_on_departure": 52
    },
    {
      "facility": "Role1",
      "arrival": "2024-03-15T07:10:00Z",
      "departure": "2024-03-15T07:45:00Z",
      "duration_min": 35,
      "reason_for_transfer": "capacity_exceeded",
      "queue_position": 3,
      "health_on_arrival": 50,
      "health_on_departure": 48
    },
    {
      "facility": "CSU_Forward",
      "arrival": "2024-03-15T07:50:00Z",
      "departure": "2024-03-15T08:30:00Z",
      "duration_min": 40,
      "reason_for_transfer": "batch_evacuation",
      "batch_size": 6,
      "health_on_arrival": 45,
      "health_on_departure": 42
    }
  ],
  "total_transit_time_min": 85,
  "total_treatment_time_min": 93,
  "facilities_bypassed": ["Role2"],
  "overflow_events": 2
}
```

### 5. Surgery and OR Metadata
```json
{
  "surgery_required": true,
  "surgery_priority_score": 2.4,  // (severity × blood_loss)
  "surgery_queue": {
    "entered_queue": "2024-03-15T09:00:00Z",
    "position_in_queue": 3,
    "queue_length": 7,
    "wait_time_min": 120,
    "queue_deterioration_multiplier": 1.3
  },
  "surgery_performed": {
    "start_time": "2024-03-15T11:00:00Z",
    "end_time": "2024-03-15T12:30:00Z",
    "duration_min": 90,
    "type": "damage_control",
    "surgeon": "trauma_surgeon",
    "success": true,
    "complications": ["required_massive_transfusion"]
  }
}
```

### 6. Mass Casualty Context
```json
{
  "mci_declared": true,
  "mci_start": "2024-03-15T06:30:00Z",
  "total_casualties_in_event": 47,
  "triage_category_override": {
    "original": "T1",
    "mci_category": "red_salvageable",
    "reason": "resource_allocation"
  },
  "resource_competition": {
    "competed_for_transport": 12,
    "competed_for_or": 7,
    "competed_for_blood": 15
  }
}
```

### 7. Outcome Metadata
```json
{
  "final_outcome": "survived",
  "outcome_timestamp": "2024-03-16T14:00:00Z",
  "total_duration_hours": 31.3,
  "death_category": null,  // or "died_in_transit", "died_waiting_for_surgery", etc.
  "preventable_death_analysis": {
    "was_preventable": false,
    "critical_factors": [],
    "improvement_opportunities": []
  },
  "disability_score": 0.2,  // 0=none, 1=total
  "return_to_duty_days": 45
}
```

### 8. Retrospective Analysis Metadata
```json
{
  "critical_decision_points": [
    {
      "timestamp": "2024-03-15T06:47:00Z",
      "decision": "apply_tourniquet",
      "outcome": "positive",
      "alternative": "pressure_dressing",
      "impact": "saved_life"
    },
    {
      "timestamp": "2024-03-15T08:00:00Z",
      "decision": "bypass_role2",
      "outcome": "mixed",
      "alternative": "wait_at_role2",
      "impact": "longer_transport_but_faster_surgery"
    }
  ],
  "quality_metrics": {
    "golden_hour_achieved": false,
    "tourniquet_time_optimal": true,
    "appropriate_triage": true,
    "timely_surgery": false,
    "blood_product_usage": "appropriate"
  },
  "training_insights": [
    "Tourniquet applied within golden 5 minutes",
    "Facility overflow caused 2-hour surgery delay",
    "CSU batch evacuation saved transport resources"
  ]
}
```

## Implementation Strategy

### Phase 1: Core Metadata (Week 1)
- Patient ID and demographics
- Injury classification with hemorrhage
- Basic treatment timeline
- Facility flow tracking

### Phase 2: Enhanced Tracking (Week 2)
- Deterioration events
- Surgery queue metadata
- Blood volume tracking
- Transport details

### Phase 3: Analysis Features (Week 3)
- Critical decision points
- Quality metrics calculation
- Preventable death analysis
- Training insights generation

### Phase 4: API Integration (Week 4)
- FHIR message generation
- Event streaming
- Batch export formats
- Statistical rollups

## API Message Example

```json
{
  "message_type": "patient_update",
  "timestamp": "2024-03-15T09:00:00Z",
  "patient_id": "POL-2024-00142",
  "current_location": "Role3",
  "current_health": 35,
  "blood_volume": 45,
  "triage": "T1",
  "hemorrhage_status": "controlled",
  "treatments_last_hour": ["blood_transfusion", "antibiotics"],
  "surgery_status": "queued_position_3",
  "deterioration_rate": 8.5,
  "expected_outcome": "survived_if_surgery_within_2hrs",
  "metadata_version": "3.0"
}
```

## Retrospective Analysis Queries

1. **What percentage of tourniquet applications happened within 5 minutes?**
2. **How many died waiting for surgery vs in transit?**
3. **What was the average overflow rate at Role2?**
4. **Which decisions could have prevented deaths?**
5. **What was the impact of CSU batch evacuations?**

## Storage Considerations

- Each patient generates ~10-20KB of metadata
- 1000 patients = ~20MB of rich training data
- Compress completed exercises
- Index by: patient_id, timestamp, facility, outcome
- Partition by: exercise_id, date, front

## Success Metrics

1. **Realism**: Do experienced combat medics recognize the patterns?
2. **Training Value**: Can we identify specific improvement areas?
3. **API Compatibility**: Do external systems accept our messages?
4. **Performance**: Can we generate 1000 patients in <1 minute?
5. **Analysis Depth**: Can we answer "what if" questions?

---

This metadata design provides comprehensive patient records suitable for:
- Real-time API messaging during exercises
- Post-exercise statistical analysis
- Individual patient case reviews
- System-wide performance metrics
- Training improvement identification