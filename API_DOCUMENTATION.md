# Medical Patients Generator API Documentation

## Overview
The Medical Patients Generator API provides endpoints for generating realistic military medical exercise data with advanced simulation features.

## Base URL
- Local: `http://localhost:8000`
- Production: Contact administrator

## Authentication
All API endpoints require authentication via API key in the `X-API-Key` header.

```bash
curl -H "X-API-Key: your_api_key_here" http://localhost:8000/api/v1/generation/
```

## Core Endpoints

### 1. Generate Patients
`POST /api/v1/generation/`

Starts a new patient generation job with specified configuration.

#### Request Body
```json
{
  "configuration": {
    "total_patients": 1440,
    "days_of_fighting": 8,
    "base_date": "2025-06-01",
    "injury_mix": {
      "Disease": 0.52,
      "Non-Battle Injury": 0.33,
      "Battle Injury": 0.15
    },
    "warfare_types": {
      "conventional": true,
      "artillery": true,
      "urban": false,
      "drone": true
    },
    "medical_simulation": {
      "enable_treatment_utility": true,
      "enable_diagnostic_uncertainty": true,
      "enable_markov_chain": true,
      "enable_warfare_modifiers": true
    },
    "front_configs": [...],
    "facility_configs": [...],
    "advanced_overrides": {...}
  },
  "output_formats": ["json", "csv"]
}
```

## Configuration Parameters Explained

### Basic Configuration

#### `total_patients` (integer, 1-10000)
Total number of patients to generate across the entire scenario.

#### `days_of_fighting` (integer, 1-30)
Duration of the scenario in days. Patients are distributed across these days based on tempo patterns.

#### `base_date` (string, YYYY-MM-DD)
Starting date for the scenario. All timestamps will be relative to this date.

#### `injury_mix` (object)
Distribution of injury types as percentages (must sum to 1.0):
- **Disease**: Non-combat medical conditions (0.0-1.0)
- **Non-Battle Injury**: Accidents, training injuries (0.0-1.0)
- **Battle Injury**: Combat-related casualties (0.0-1.0)

### Warfare Types Configuration

Controls which warfare scenarios are active and affects injury patterns:

```json
"warfare_types": {
  "conventional": true,    // Standard combined arms warfare
  "artillery": true,        // Indirect fire, bombardment
  "urban": false,          // Urban combat, building clearing
  "guerrilla": false,      // Asymmetric warfare, IEDs
  "drone": true,           // UAV strikes, loitering munitions
  "naval": false,          // Maritime operations
  "cbrn": false,           // Chemical/Biological/Radiological/Nuclear
  "peacekeeping": false    // Low-intensity peacekeeping ops
}
```

Each warfare type affects:
- **Injury severity distribution** (e.g., artillery causes more T1 casualties)
- **Temporal patterns** (e.g., guerrilla attacks are sporadic)
- **Polytrauma rates** (e.g., explosions cause multiple injuries)

### Medical Simulation Features

#### `enable_treatment_utility` (boolean)
Enables the Treatment Utility Model which simulates:
- Treatment effectiveness based on interventions applied
- Deterioration over time without treatment
- Stacking effects of multiple treatments

#### `enable_diagnostic_uncertainty` (boolean)
Simulates realistic diagnostic accuracy:
- POI (Point of Injury): 60% accuracy
- Role 1: 75% accuracy
- Role 2: 85% accuracy
- Role 3: 95% accuracy
- Role 4: 99% accuracy

#### `enable_markov_chain` (boolean)
Uses Markov Chain modeling for patient routing:
- Probabilistic transitions between facilities
- Realistic patient flow based on triage category
- Accounts for capacity constraints

#### `enable_warfare_modifiers` (boolean)
Applies warfare-specific injury patterns:
- Different injury distributions per warfare type
- Polytrauma probability adjustments
- Environmental impact on casualties

### Advanced Overrides

#### Scenario Modifiers

##### `intensity` (string)
Controls overall combat intensity:
- **low**: 50% baseline casualties, reduced mass casualty events
- **medium**: Normal casualty rates (default)
- **high**: 150% casualties, increased mass casualty events
- **extreme**: 200% casualties, frequent mass casualty events

**What it does:**
- Modifies the frequency and severity of casualty events
- Affects mass casualty event probability
- Does NOT change total patient count (that's fixed by `total_patients`)

##### `tempo` (string)
Controls casualty distribution pattern across days:
- **sustained**: Even distribution across all days
- **escalating**: Gradually increasing casualties (40% → 180%)
- **surge**: Peak in middle days (50% → 200% → 50%)
- **declining**: Gradually decreasing (180% → 40%)
- **intermittent**: Alternating high/low days

**What it does:**
- Redistributes patients across the scenario timeline
- Creates realistic operational patterns
- Affects when casualties occur, not how many

##### `special_events` (object)
Triggers specific high-casualty incidents:

```json
"special_events": {
  "major_offensive": false,  // 3x casualties for 4 hours
  "ambush": true,            // 2x casualties for 1 hour
  "mass_casualty": true      // Single event with 30-100 casualties
}
```

**What they do:**
- Create spikes in casualty flow
- Test surge capacity of medical facilities
- Generate realistic scenario challenges

##### `environmental_conditions` (object)
Modifies casualty patterns based on environment:

```json
"environmental_conditions": {
  "night_operations": true,     // 30% reduction in casualties at night
  "extreme_weather": false,     // Delays evacuation by 30-90 minutes
  "mountainous_terrain": false, // Increases evacuation time
  "urban_environment": false    // Increases Non-Battle Injuries
}
```

**Effects:**
- **night_operations**: Reduces combat intensity during night hours
- **extreme_weather**: Delays medical evacuation, increases disease
- **mountainous_terrain**: Longer evacuation times, more trauma
- **urban_environment**: More building collapses, civilian casualties

#### Treatment Effectiveness
Override success rates for medical interventions (0.0-1.0):

```json
"treatment_effectiveness": {
  "tourniquet": 0.95,          // 95% effective at stopping bleeding
  "pressure_dressing": 0.85,    // 85% effective
  "hemostatic_gauze": 0.90,    // 90% effective
  "iv_fluids": 0.80,           // 80% effective at stabilization
  "blood_transfusion": 0.95    // 95% effective
}
```

#### Diagnostic Accuracy
Override diagnostic accuracy by facility level (0.0-1.0):

```json
"diagnostic_accuracy": {
  "POI": 0.60,    // Point of Injury - field medics
  "Role1": 0.75,  // Battalion Aid Station
  "Role2": 0.85,  // Forward Surgical Team
  "Role3": 0.95,  // Combat Support Hospital
  "Role4": 0.99   // Definitive care facility
}
```

#### Polytrauma Rates
Probability of multiple injuries by warfare type (0.0-1.0):

```json
"polytrauma_rates": {
  "conventional": 0.15,  // 15% chance of multiple injuries
  "artillery": 0.45,     // 45% - blast injuries affect multiple systems
  "urban": 0.25,        // 25% - building collapses, explosions
  "drone": 0.35         // 35% - precision strikes but significant trauma
}
```

## Example: High-Intensity Urban Combat Scenario

```json
{
  "configuration": {
    "total_patients": 2000,
    "days_of_fighting": 5,
    "base_date": "2025-07-01",
    "injury_mix": {
      "Disease": 0.20,
      "Non-Battle Injury": 0.30,
      "Battle Injury": 0.50
    },
    "warfare_types": {
      "conventional": true,
      "artillery": true,
      "urban": true,
      "drone": true
    },
    "medical_simulation": {
      "enable_treatment_utility": true,
      "enable_diagnostic_uncertainty": true,
      "enable_markov_chain": true,
      "enable_warfare_modifiers": true
    },
    "advanced_overrides": {
      "scenario_modifiers": {
        "intensity": "high",
        "tempo": "surge",
        "special_events": {
          "major_offensive": true,
          "mass_casualty": true
        },
        "environmental_conditions": {
          "urban_environment": true,
          "night_operations": false
        }
      },
      "polytrauma_rates": {
        "urban": 0.40,
        "artillery": 0.55
      }
    }
  },
  "output_formats": ["json", "csv"]
}
```

This configuration creates:
- 2000 casualties over 5 days
- 50% combat injuries due to urban warfare
- Surge pattern with peak casualties on days 2-3
- Major offensive event creating 3x normal casualties
- Higher polytrauma rates due to urban combat
- Full medical simulation for realistic treatment outcomes

## Response Format

### Success Response (201 Created)
```json
{
  "job_id": "7b16431d-88f3-41a0-9610-7eb8b65853c5",
  "status": "pending",
  "created_at": "2025-01-15T14:30:00Z",
  "estimated_duration_seconds": 45,
  "message": "Patient generation job created successfully"
}
```

### Error Response (422 Validation Error)
```json
{
  "error": "Validation Error",
  "detail": "injury_mix percentages must sum to 1.0",
  "timestamp": "2025-01-15T14:30:00Z"
}
```

## Job Management

### Check Job Status
`GET /api/v1/jobs/{job_id}`

### List All Jobs
`GET /api/v1/jobs/`

### Download Results
`GET /api/v1/downloads/{job_id}`

Returns a ZIP file containing generated patient data in requested formats.

## Rate Limits

- Demo API Key: 50 patients per request, 100 requests per day
- Standard API Key: 10,000 patients per request, 1000 requests per day
- Enterprise: Contact for custom limits

## Best Practices

1. **Start Simple**: Begin with basic configuration, add complexity gradually
2. **Test Small**: Generate 10-50 patients first to verify configuration
3. **Use Warfare Modifiers**: Enable for realistic injury patterns
4. **Monitor Jobs**: Poll job status every 2-5 seconds
5. **Cache Configurations**: Save successful configurations for reuse

## Support

For API issues or questions:
- Documentation: `/docs` (Swagger UI)
- GitHub: [Report Issues](https://github.com/your-org/medical-patients)
- Email: support@your-domain.com