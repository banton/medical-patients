# Patient Care Continuum Tracking with Evacuation/Transit Times - Implementation Plan

## 🎯 Project Overview

**Goal**: Implement comprehensive patient care continuum tracking with detailed timeline tracking, evacuation/transit times, and triage-based timing models for military medical facilities (POI → Role1 → Role2 → Role3 → Role4).

**Current State**: Basic patient flow tracking exists but lacks detailed timeline tracking and evacuation/transit time modeling.

**Target State**: Complete patient journey tracking with realistic timing, KIA/RTD rules, and detailed movement timeline APIs.

## 📋 Requirements Analysis

### Core Features Required
1. **Final State Tracking**: Last facility visited and final status (KIA/RTD/Remains_Role4)
2. **Movement Timeline**: Detailed patient movement with timestamps and hours since injury
3. **Evacuation Times**: Triage-based time spent at each facility (treatment period)
4. **Transit Times**: Time spent traveling between facilities based on triage category
5. **KIA/RTD Timing Rules**:
   - KIA: Can occur during evacuation time OR transit time
   - RTD: Can ONLY occur during evacuation time (not transit)
   - Role 4 Special Rule: Auto-RTD after evacuation time if not KIA
6. **Triage-Based Timing**: Different evacuation/transit times for T1/T2/T3 categories

### API Design Requirements

#### New Endpoints
- `GET /api/v1/patients/{patient_id}/timeline` - Detailed movement timeline
- `GET /api/v1/statistics/evacuation-times` - Aggregated timing statistics

#### Timeline Event Types
- `arrival` - Patient arrives at facility
- `evacuation_start` - Begin evacuation period at facility
- `transit_start` - Begin transit to next facility
- `kia` - Patient dies (during evacuation or transit)
- `rtd` - Patient returns to duty (only during evacuation)

## 🏗️ Implementation Architecture

### Component Structure
```
patient_generator/
├── evacuation_transit_times.json     # Configuration file
├── evacuation_time_manager.py        # Core timing logic
├── patient.py                        # Enhanced with timeline tracking
├── flow_simulator.py                 # Enhanced with detailed flow
└── models_db.py                      # Database schema updates

src/api/v1/routers/
├── patients.py                       # New timeline endpoints
└── statistics.py                     # Evacuation statistics

tests/
├── test_evacuation_times.py          # Comprehensive test suite
├── test_patient_timeline.py          # Timeline tracking tests
└── test_integration_flow.py          # End-to-end flow tests
```

### Data Flow
1. **Configuration Loading**: Load evacuation/transit times from JSON
2. **Patient Creation**: Initialize with timeline tracking
3. **Flow Simulation**: Apply triage-based timing rules
4. **Timeline Events**: Record all movement events with timestamps
5. **KIA/RTD Logic**: Apply timing-based mortality/return rules
6. **API Exposure**: Serve detailed timeline and statistics

## 📊 Configuration Design

### Evacuation Times Structure
```json
{
  "evacuation_times": {
    "POI": {
      "T1": { "min_hours": 3, "max_hours": 8 },
      "T2": { "min_hours": 5, "max_hours": 12 },
      "T3": { "min_hours": 8, "max_hours": 12 }
    },
    "Role1": { /* similar structure */ },
    // ... other facilities
  },
  "transit_times": {
    "POI_to_Role1": {
      "T1": { "min_hours": 1, "max_hours": 3 },
      // ... other triage categories
    },
    // ... other routes
  },
  "kia_rate_modifiers": {
    "T1": 1.5,  // Higher KIA rate for urgent cases
    "T2": 1.0,  // Baseline rate
    "T3": 0.5   // Lower KIA rate for less urgent
  }
}
```

### Timing Logic Rules
- **T1 (Urgent)**: Shorter evacuation times, faster transit, higher KIA risk
- **T2 (Delayed)**: Medium timing across all phases
- **T3 (Minimal)**: Longer evacuation times, slower transit, lower KIA risk
- **Role4 Special**: Auto-RTD if survives full evacuation period

## 🧪 Test-Driven Development Strategy

### Test Categories
1. **Unit Tests**: Individual component testing
   - EvacuationTimeManager timing calculations
   - Patient timeline event tracking
   - Triage modifier applications

2. **Integration Tests**: Component interaction testing
   - Complete patient flow simulation
   - Timeline consistency validation
   - KIA/RTD timing rule enforcement

3. **API Tests**: Endpoint validation
   - Timeline API response format
   - Statistics aggregation accuracy
   - Error handling for missing patients

### Key Test Scenarios
- **T1 Patient Fast Track**: POI → Role1 → KIA during evacuation
- **T3 Patient Long Journey**: POI → Role1 → Role2 → Role3 → Role4 → RTD
- **Transit KIA**: Patient dies while being transported
- **Role4 Auto-RTD**: Patient completes Role4 evacuation period
- **Timeline Consistency**: Events in chronological order with valid durations

## 📈 Implementation Phases

### Phase 1: Foundation (Test-First)
1. **Create Configuration File**: evacuation_transit_times.json
2. **Write Test Suite**: Comprehensive test coverage for all scenarios
3. **Implement EvacuationTimeManager**: Core timing logic with triage support

### Phase 2: Patient Model Enhancement
1. **Update Patient Class**: Add timeline tracking, final status fields
2. **Timeline Event System**: Structured event recording with timestamps
3. **Validation Logic**: Ensure timeline consistency and rule compliance

### Phase 3: Flow Simulation Enhancement
1. **Enhanced Flow Logic**: Integrate timing-based decisions
2. **KIA/RTD Rules**: Implement timing-based mortality and return logic
3. **Role4 Special Handling**: Auto-RTD rule implementation

### Phase 4: API Development
1. **Timeline Endpoint**: Detailed patient movement history
2. **Statistics Endpoint**: Aggregated evacuation/transit time analytics
3. **Response Models**: Pydantic models for consistent API responses

### Phase 5: Database Integration
1. **Schema Updates**: Add timeline and final status columns
2. **Migration Scripts**: Safe database schema evolution
3. **Performance Optimization**: Indexing for timeline queries

### Phase 6: Integration & Documentation
1. **End-to-End Testing**: Complete workflow validation
2. **API Documentation**: OpenAPI specs for new endpoints
3. **Performance Testing**: Timeline query optimization

## 🔧 Technical Implementation Details

### Database Schema Changes
```sql
ALTER TABLE patients ADD COLUMN last_facility VARCHAR(50);
ALTER TABLE patients ADD COLUMN final_status VARCHAR(50);
ALTER TABLE patients ADD COLUMN movement_timeline JSONB;
ALTER TABLE patients ADD COLUMN injury_timestamp TIMESTAMP;
```

### Key Classes to Implement

#### EvacuationTimeManager
- Load configuration from JSON
- Calculate triage-based evacuation times
- Calculate route-based transit times
- Apply triage modifiers to KIA rates

#### Enhanced Patient Model
- Timeline event tracking
- Final status determination
- Hours since injury calculations
- Timeline consistency validation

#### Enhanced FlowSimulator
- Detailed step-by-step simulation
- Timing-based KIA/RTD decisions
- Role4 auto-RTD implementation
- Complete timeline generation

## ⚠️ Edge Cases & Considerations

### Critical Edge Cases
1. **Immediate KIA**: Patient dies on arrival (0 evacuation time)
2. **Facility Skipping**: Non-standard evacuation routes
3. **Transit KIA**: Death during transport (affects last_facility)
4. **Missing Triage**: Default behavior for unassigned triage
5. **Concurrent Events**: KIA/RTD at decision boundary times

### Performance Considerations
- **Timeline Storage**: JSONB for flexible timeline queries
- **Indexing Strategy**: patient_id, facility, timestamp indexes
- **Memory Usage**: Efficient timeline event generation
- **Query Optimization**: Aggregation for statistics endpoints

### Validation Requirements
- **Time Consistency**: Events in chronological order
- **Facility Chain**: Valid facility progression
- **Triage Mapping**: All triage categories have timing data
- **Range Validation**: min_hours ≤ max_hours in configuration

## 📚 Documentation Requirements

### API Documentation Updates
- New endpoint specifications
- Timeline event type definitions
- Evacuation timing logic explanation
- Triage category impact documentation

### Code Documentation
- EvacuationTimeManager usage examples
- Timeline event structure documentation
- KIA/RTD rule explanations
- Configuration file format specification

## 🎯 Success Criteria

### Functional Requirements
- ✅ All patients have complete movement timeline
- ✅ KIA/RTD timing rules correctly enforced
- ✅ Triage categories affect all timing calculations
- ✅ Role4 auto-RTD rule implemented
- ✅ API endpoints return accurate timeline data

### Technical Requirements
- ✅ 100% test coverage for timing logic
- ✅ Timeline queries perform under 100ms
- ✅ Configuration validation on startup
- ✅ Database schema migration successful
- ✅ API responses follow OpenAPI specification

### Quality Requirements
- ✅ No timeline inconsistencies in generated data
- ✅ Realistic timing distributions match military protocols
- ✅ Edge cases handled gracefully
- ✅ Memory usage scales linearly with patient count
- ✅ API error handling provides clear feedback

## 🚀 Next Steps

1. **Begin TDD Implementation**: Start with test_evacuation_times.py
2. **Create Configuration**: evacuation_transit_times.json with realistic values
3. **Implement Core Logic**: EvacuationTimeManager with triage support
4. **Enhance Patient Model**: Timeline tracking and final status
5. **Update Flow Simulator**: Detailed timing-based simulation
6. **Create API Endpoints**: Timeline and statistics services
7. **Database Migration**: Schema updates and data migration
8. **Integration Testing**: End-to-end workflow validation
9. **Documentation**: API specs and usage guides
10. **Performance Optimization**: Query tuning and caching

This comprehensive implementation will transform the medical patient generator from basic flow tracking to a sophisticated patient care continuum simulation with realistic timing, detailed analytics, and military-grade accuracy.