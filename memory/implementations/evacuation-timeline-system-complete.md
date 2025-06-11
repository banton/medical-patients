# Evacuation Timeline System - Complete Implementation

## 🎯 System Overview

**Status**: ✅ PRODUCTION READY - Complete evacuation timeline system operational

The **Comprehensive Patient Care Continuum Tracking with Evacuation/Transit Times** system provides realistic military medical timing for patient progression through medical facilities with detailed timeline tracking.

## 🏗️ Architecture Components

### 1. Core Timing Engine
**File**: `patient_generator/evacuation_time_manager.py`
- **EvacuationTimeManager** class with configuration loading and validation
- **Triage-based timing calculations** for evacuation and transit durations
- **Rate modifiers** for KIA/RTD probabilities based on triage category
- **Facility hierarchy management** (POI → Role1 → Role2 → Role3 → Role4)

### 2. Timing Configuration
**File**: `patient_generator/evacuation_transit_times.json`
- **Realistic military timing data** based on medical evacuation protocols
- **Facility evacuation times** by triage category (T1/T2/T3)
- **Transit times** between facilities with triage-based variations
- **Rate modifiers** for KIA (T1=1.5x, T2=1.0x, T3=0.5x) and RTD (T1=0.8x, T2=1.0x, T3=1.2x)

### 3. Enhanced Patient Model  
**File**: `patient_generator/patient.py`
- **Timeline tracking fields**: `movement_timeline`, `last_facility`, `final_status`, `injury_timestamp`
- **Event management**: `add_timeline_event()`, `set_final_status()`, `get_timeline_summary()`
- **JSON serialization**: `to_dict()`, `to_json()`, `from_dict()`, `from_json()` methods
- **Timeline validation**: `validate_timeline_consistency()` for data integrity

### 4. FlowSimulator Integration
**File**: `patient_generator/flow_simulator.py`  
- **Enhanced patient flow simulation** using EvacuationTimeManager
- **Realistic timeline generation** with proper KIA/RTD timing rules
- **Facility progression** through complete medical hierarchy
- **Event logging** for arrival, evacuation, transit, and final status

## 🔧 Technical Implementation

### KIA/RTD Timing Rules
```python
# KIA can occur during evacuation OR transit
if random.random() < adjusted_kia_rate:
    kia_time = current_time + timedelta(hours=random.uniform(0, evacuation_hours))
    patient.set_final_status("KIA", facility, kia_time, kia_timing="during_evacuation")

# RTD only allowed during evacuation (not transit)  
if facility != "Role4" and random.random() < adjusted_rtd_rate:
    rtd_time = current_time + timedelta(hours=random.uniform(0, evacuation_hours))
    patient.set_final_status("RTD", facility, rtd_time, rtd_timing="during_evacuation")

# Role4 auto-RTD if no KIA
if facility == "Role4":
    patient.set_final_status("RTD", facility, current_time, rtd_timing="auto_role4")
```

### JSON Serialization Pattern
```python
# CORRECT: Use patient.to_dict() for JSON export
patient_data = {"patient": patient.to_dict(), "fhir_bundle": bundle}
json.dump(patient_data, stream, indent=2)

# INCORRECT: Never use patient.__dict__ (datetime serialization fails)
# patient_data = {"patient": patient.__dict__, "fhir_bundle": bundle}
```

### Timeline Event Structure
```json
{
  "event_type": "evacuation_start",
  "facility": "POI", 
  "timestamp": "2024-01-01T06:00:00",
  "hours_since_injury": 6.0,
  "evacuation_duration_hours": 6.5,
  "triage_category": "T1"
}
```

## 🌐 API Endpoints

### 1. Evacuation Configuration
```http
GET /api/v1/timeline/configuration/evacuation-times
Authorization: X-API-Key: your_secret_api_key_here

Response: {
  "evacuation_times": {...},
  "transit_times": {...}, 
  "kia_rate_modifiers": {...},
  "facility_hierarchy": ["POI", "Role1", "Role2", "Role3", "Role4"]
}
```

### 2. Patient Timeline
```http
GET /api/v1/timeline/jobs/{job_id}/patients/{patient_id}
Response: {
  "timeline": [...],
  "summary": {...},
  "patient_details": {...}
}
```

### 3. Evacuation Statistics
```http
GET /api/v1/timeline/jobs/{job_id}/statistics
Response: {
  "outcome_statistics": {...},
  "timing_statistics": {...},
  "triage_breakdown": {...}
}
```

## 💾 Database Schema

### PatientDBModel
**Table**: `patients`
```sql
CREATE TABLE patients (
    job_id VARCHAR PRIMARY KEY,
    patient_id INTEGER PRIMARY KEY,
    -- Timeline tracking fields
    last_facility VARCHAR,
    final_status VARCHAR,  -- KIA, RTD, Remains_Role4
    movement_timeline JSONB NOT NULL DEFAULT '[]',
    injury_timestamp TIMESTAMPTZ,
    -- Performance fields
    total_duration_hours FLOAT,
    facilities_visited JSONB NOT NULL DEFAULT '[]',
    total_events INTEGER NOT NULL DEFAULT 0,
    -- Standard fields...
    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
);
```

## 🧪 Testing Coverage

### Test Suite: `tests/test_evacuation_times.py`
**29/29 tests passing** ✅

- **TestEvacuationTimeManager** (8 tests) - Configuration loading, timing calculations, modifiers
- **TestPatientTimelineTracking** (5 tests) - Event tracking, chronological validation
- **TestKIAAndRTDTimingRules** (6 tests) - Timing-based mortality and RTD logic
- **TestCompletePatientJourney** (6 tests) - Integration tests for full patient flow
- **TestEdgeCases** (4 tests) - Edge case handling and error conditions

### Key Test Scenarios
- ✅ Evacuation time calculation by facility and triage
- ✅ Transit time calculation for all routes
- ✅ KIA/RTD rate modifiers applied correctly
- ✅ Timeline event chronological consistency
- ✅ Role4 auto-RTD rule implementation
- ✅ RTD blocked during transit periods
- ✅ Complete patient journey simulation

## 🚀 Production Deployment

### System Status
- ✅ **36/36 tests passing** (29 evacuation + 7 smoke tests)
- ✅ **Database migration applied** (revision: 491f84d4f7ce)
- ✅ **API endpoints deployed** and tested in production
- ✅ **JSON serialization fixed** - patient generation jobs working
- ✅ **Timeline data export** functioning with proper datetime handling

### Performance Characteristics
- **Evacuation time ranges**: 3-96 hours based on facility and triage
- **Transit time ranges**: 1-8 hours based on route and urgency
- **Timeline events**: 4-20 events per patient journey
- **JSON export size**: ~2-5KB per patient with full timeline data

## 💡 Usage Examples

### Generate Patient with Timeline
```python
from patient_generator.flow_simulator import PatientFlowSimulator
from patient_generator.config_manager import ConfigurationManager

config_manager = ConfigurationManager()
flow_simulator = PatientFlowSimulator(config_manager)

# Creates patient with complete timeline tracking
patients = flow_simulator.generate_casualty_flow()

# Access timeline data
for patient in patients:
    print(f"Patient {patient.id}: {patient.final_status} at {patient.last_facility}")
    print(f"Timeline events: {len(patient.movement_timeline)}")
    print(f"Total duration: {patient.get_timeline_summary()['total_duration_hours']} hours")
```

### Export Timeline Data
```python
# JSON serialization with proper datetime handling
patient_json = patient.to_json()
patient_dict = patient.to_dict()

# Timeline summary for quick access
summary = patient.get_timeline_summary()
# Returns: {total_events, total_duration_hours, facilities_visited, final_status, last_facility}
```

## 🔮 Future Enhancements

### Ready for Implementation
1. **Patient database storage** - PatientDBModel ready for optional structured storage
2. **Advanced timeline queries** - Database schema supports complex evacuation analytics
3. **Real-time timeline tracking** - API endpoints support live patient monitoring
4. **Custom timing configurations** - JSON structure supports user-defined timing parameters

### Frontend Integration Ready
- **Timeline visualization** - JSON data ready for timeline charts
- **Evacuation statistics dashboard** - API endpoints provide comprehensive metrics
- **Patient tracking interface** - Individual patient timeline data available
- **Configuration editor** - Evacuation timing JSON ready for frontend editing

---

**Implementation Status**: ✅ COMPLETE - Production-ready evacuation timeline system with comprehensive testing and documentation

**Next Phase**: Frontend evacuation configuration panel + final code quality improvements