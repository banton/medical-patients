# API & UI Integration Plan for Medical Simulation Enhancements

## Current State Analysis

### Architecture Overview
```
CLI (run_generator.py) 
  └─> PatientGeneratorApp 
      └─> FlowSimulator 
          └─> MedicalSimulationBridge ✅ WORKING

API (/api/v1/generation/)
  └─> AsyncPatientGenerationService
      └─> PatientGenerationPipeline
          └─> FlowSimulator (but bridge not activated) ❌ NOT WORKING

Admin UI (static/js/app.js)
  └─> ApiClient (/api/v1/)
      └─> Generation interface ❌ Doesn't show enhanced features

Timeline Viewer (patient-timeline-viewer/)
  └─> React app
      └─> Loads JSON files ✅ Already supports enhanced format
```

### Key Files
- **API Service**: `src/domain/services/patient_generation_service.py`
- **Flow Simulator**: `patient_generator/flow_simulator.py` 
- **Medical Bridge**: `patient_generator/medical_simulation_bridge.py`
- **UI App**: `static/js/app.js`
- **UI API Client**: `static/js/services/api.js`

## Phase 1: API Integration (Priority 1)

### Step 1.1: Modify FlowSimulator initialization in API
**File**: `src/domain/services/patient_generation_service.py`
**Line**: ~196
```python
# Current:
flow_simulator=PatientFlowSimulator(self.config_manager)

# Change to:
flow_simulator=PatientFlowSimulator(self.config_manager, use_medical_simulation=True)
```

### Step 1.2: Ensure environment variables are passed
**File**: `patient_generator/flow_simulator.py`
**Modification**: Already checks `os.environ.get('ENABLE_MEDICAL_SIMULATION')`

### Step 1.3: Verify bridge activation
The flow_simulator already has this code (lines 302-308):
```python
if self.use_medical_simulation:
    try:
        from .medical_simulation_bridge import MedicalSimulationBridge
        self.medical_bridge = MedicalSimulationBridge()
```

## Phase 2: API Response Models

### Step 2.1: Check current response structure
- Patient objects now include:
  - `treatments`: Enhanced treatments (buddy_aid, tourniquet, etc.)
  - `timeline_events`: Facility movement events
  - `diagnostics`: Diagnostic refinements
  - `polytrauma_indicators`: Multiple injury tracking

### Step 2.2: Ensure API serialization handles new fields
**File**: `patient_generator/patient.py`
- Check `to_dict()` method includes all new fields

## Phase 3: UI Updates

### Admin UI Updates (Generation Interface)

#### Step 3.1: Update Generation Status Display
**File**: `static/js/app.js`
**Purpose**: Show users that enhanced simulation is active
**Changes**:
- Add indicator showing "Enhanced Medical Simulation: Active"
- Update progress messages to reflect probabilistic models
- Show summary statistics after generation (mortality rate, polytrauma %)

#### Step 3.2: Display Generation Metrics
**File**: `static/js/app.js`
**Current**: Basic completion message
**Update**: Show enhanced metrics:
```javascript
// Display after generation:
- Total Patients: 100
- Mortality Rate: 15.2% (realistic)
- Polytrauma Cases: 44%
- Facility Distribution: POI→Role1 (85%), Direct Evac (3%)
- Warfare Pattern: Urban Combat
- Enhanced Treatments Applied: ✓
```

#### Step 3.3: Update Configuration Display
**Purpose**: Show available warfare patterns and treatment protocols
**Changes**:
- Add warfare scenario selector (if configurable)
- Show treatment protocol version
- Display Markov chain routing status

### Timeline Viewer Validation

#### Step 3.4: Verify Timeline Viewer Compatibility
**File**: `patient-timeline-viewer/src/types/patient.types.ts`
**Check**: Ensure types match enhanced data structure
**Status**: Already compatible - handles timeline_events, treatments, facility flow

#### Step 3.5: Test Timeline Viewer with Enhanced Data
**Action**: Load enhanced JSON into timeline viewer
**Expected**: Should display facility progression, KIA/RTD tallies correctly

## Phase 4: Testing Plan

### Step 4.1: API Testing
```bash
# Generate via API
curl -X POST http://localhost:8000/api/v1/generation/ \
  -H "X-API-Key: your_api_key" \
  -d '{"total_patients": 10}'

# Compare with CLI
python run_generator.py --patients 10 --output output_cli
```

### Step 4.2: Validation Criteria
- [ ] API returns enhanced treatments (not "Medication admin")
- [ ] Timeline events include facility progression
- [ ] Diagnostic refinements present
- [ ] Polytrauma cases detected
- [ ] Mortality rate ~10-20% (not 75%)

## Phase 5: UI Implementation Details

### Admin UI Enhancements

1. **Generation Summary Panel**
```javascript
// Add to app.js after generation completes
const displayGenerationSummary = (jobData) => {
  const stats = analyzePatientData(jobData.patients);
  return {
    totalPatients: stats.count,
    mortalityRate: `${stats.kiaRate}%`,
    polytraumaRate: `${stats.polytraumaRate}%`,
    facilityFlow: stats.facilityDistribution,
    enhancedSimulation: "Active",
    warfarePattern: stats.detectedPattern
  };
};
```

2. **Enhanced Status Messages**
```javascript
// Update progressMessages array to include:
'Applying warfare-specific injury patterns...',
'Running Markov chain facility routing...',
'Calculating treatment utility scores...',
'Simulating diagnostic uncertainty...',
'Processing polytrauma casualties...'
```

3. **Configuration Indicators**
```javascript
// Show active features in UI
const features = {
  medicalSimulation: true,
  markovChainRouting: true,
  warfareModifiers: true,
  treatmentUtility: true,
  diagnosticUncertainty: true
};
```

### Timeline Viewer (No Changes Needed)

The Timeline Viewer already supports:
- `timeline_events` with facility progression
- Patient names and demographics
- KIA/RTD status tracking
- Facility column display (POI, Role1-4)
- Animation of patient movement

**Validation Only**: Test with enhanced data to confirm compatibility

## Implementation Order

1. **Fix API Integration** (1 hour)
   - Modify patient_generation_service.py (1 line change)
   - Test with curl commands
   - Verify enhanced output

2. **Update Response Models** (30 min)
   - Verify patient.to_dict() includes all fields
   - Document new response structure

3. **Admin UI Updates** (2 hours)
   - Add generation summary panel
   - Update progress messages
   - Show active features indicator
   - Display enhanced metrics post-generation

4. **Timeline Viewer Validation** (30 min)
   - Test with enhanced JSON data
   - Verify facility flow displays correctly
   - Confirm KIA/RTD tracking works

5. **Integration Testing** (1 hour)
   - API vs CLI comparison
   - Admin UI generation flow
   - Timeline viewer with API-generated data
   - End-to-end validation

## Success Criteria

### API Success
- [x] Environment variables set in docker-compose
- [ ] API uses medical_simulation_bridge
- [ ] Enhanced treatments in API response
- [ ] Timeline events populated
- [ ] Realistic mortality rates (10-20%)

### UI Success
- [ ] Displays enhanced treatment names
- [ ] Shows facility progression
- [ ] Indicates polytrauma cases
- [ ] Warfare pattern visibility
- [ ] Timeline compatibility

## Risks & Mitigations

1. **Performance Impact**
   - Risk: Medical simulation adds latency
   - Mitigation: Already tested at ~10ms per patient

2. **Backward Compatibility**
   - Risk: Existing integrations break
   - Mitigation: New fields are additive, not breaking

3. **UI Complexity**
   - Risk: Too much information displayed
   - Mitigation: Progressive disclosure, collapsible sections

## Notes

- The medical_simulation_bridge is already default enabled (set to 'true')
- Docker environment variables already configured
- UI framework is vanilla JS with Tailwind CSS (no React in main UI)
- Separate React timeline viewer exists but is standalone