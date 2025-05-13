# Data Structures

## Core Data Models and Formats

This document details the key data structures used throughout the Military Medical Exercise Patient Generator, including internal models and output formats.

### Patient Object

The central data model representing a military patient with their complete medical history.

```python
class Patient:
    id                     # Unique identifier (integer)
    demographics           # Dictionary of personal information
    medical_data           # Dictionary of additional medical data
    treatment_history      # List of treatment events
    current_status         # Current location or status (string: "POI", "R1", "R2", "R3", "R4", "RTD", "KIA")
    day_of_injury          # When the casualty occurred (string: "Day 1", "Day 2", "Day 4", "Day 8")
    injury_type            # Category of injury (string: "DISEASE", "NON_BATTLE", "BATTLE_TRAUMA")
    triage_category        # Severity classification (string: "T1", "T2", "T3")
    nationality            # ISO3166 country code (string: "POL", "EST", etc.)
    front                  # Geographic origin (string: "Polish", "Estonian", "Finnish")
    primary_condition      # Main medical condition (dictionary)
    additional_conditions  # List of secondary conditions (list of dictionaries)
    gender                 # Patient gender (string: "male", "female")
    allergies              # List of allergies (list of dictionaries)
    medications            # List of medications (list of dictionaries)
```

### Treatment History Event

Records an encounter at a medical treatment facility.

```python
{
    "facility": string,       # Facility code (e.g., "R1", "R2")
    "date": datetime,         # Date and time of treatment
    "treatments": [           # List of treatments performed
        {
            "code": string,   # SNOMED CT code
            "display": string # Human-readable description
        }
    ],
    "observations": [         # List of observations recorded
        {
            "code": string,   # LOINC code
            "display": string, # Human-readable description
            "value": number/string, # Measurement value
            "unit": string     # Unit of measurement
        }
    ]
}
```

### Demographics Data

Personal information for a patient.

```python
{
    "family_name": string,    # Last name appropriate to nationality
    "given_name": string,     # First name appropriate to nationality and gender
    "gender": string,         # "male" or "female"
    "id_number": string,      # ID formatted according to nationality standards
    "birthdate": string,      # ISO8601 date (YYYY-MM-DD)
    "nationality": string,    # ISO3166 alpha-3 country code
    "religion": string,       # Optional religion code
    "weight": float,          # Weight in kg
    "blood_type": string      # Blood type (A, B, AB, O)
}
```

### Medical Condition

Represents a diagnosis or medical problem.

```python
{
    "code": string,           # SNOMED CT code
    "display": string,        # Human-readable description
    "severity": string,       # Textual description of severity
    "severity_code": string   # SNOMED CT code for severity
}
```

### FHIR Bundle

The primary output format following HL7 FHIR R4 standard.

```json
{
    "resourceType": "Bundle",
    "id": string,             // UUID
    "type": "collection",
    "timestamp": string,      // ISO8601 datetime
    "extension": [            // Custom extensions
        {
            "url": "http://example.org/fhir/StructureDefinition/nfc-tag-id",
            "valueString": string  // NFC tag ID
        }
    ],
    "entry": [                // Bundle entries
        {
            "resource": {     // Patient resource
                "resourceType": "Patient",
                "id": string,
                "gender": string,
                "name": [{
                    "family": string,
                    "given": [string]
                }],
                "birthDate": string,
                "extension": [
                    // Nationality, religion, etc.
                ],
                "identifier": [
                    // ID numbers
                ]
            }
        },
        {
            "resource": {     // Condition resource
                "resourceType": "Condition",
                "id": string,
                "subject": {"reference": string},  // Reference to patient
                "code": {
                    "coding": [{
                        "system": "http://snomed.info/sct",
                        "code": string,
                        "display": string
                    }]
                },
                "clinicalStatus": {...},
                "verificationStatus": {...},
                "onsetDateTime": string,
                "severity": {...}  // Optional severity
            }
        },
        // Additional resources: Procedures, Observations, etc.
    ]
}
```

### FHIR Resources

#### Patient Resource

```json
{
    "resourceType": "Patient",
    "id": string,             // UUID
    "gender": string,         // "male", "female", "unknown"
    "name": [{
        "family": string,
        "given": [string]
    }],
    "birthDate": string,      // ISO8601 date
    "extension": [
        {
            "url": "http://example.org/fhir/StructureDefinition/nationality",
            "valueString": string  // ISO3166 country code
        },
        // Additional extensions (religion, etc.)
    ],
    "identifier": [
        {
            "system": string, // Identifier system URL
            "value": string   // ID number
        }
    ]
}
```

#### Condition Resource

```json
{
    "resourceType": "Condition",
    "id": string,             // UUID
    "subject": {
        "reference": string   // Reference to Patient (e.g., "Patient/1234")
    },
    "code": {
        "coding": [{
            "system": "http://snomed.info/sct",
            "code": string,   // SNOMED CT code
            "display": string // Human-readable description
        }]
    },
    "clinicalStatus": {
        "coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
            "code": "active",
            "display": "Active"
        }]
    },
    "verificationStatus": {
        "coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
            "code": "confirmed",
            "display": "Confirmed"
        }]
    },
    "onsetDateTime": string,  // ISO8601 datetime
    "severity": {             // Optional severity
        "coding": [{
            "system": "http://snomed.info/sct",
            "code": string,
            "display": string
        }]
    }
}
```

#### Procedure Resource

```json
{
    "resourceType": "Procedure",
    "id": string,             // UUID
    "subject": {
        "reference": string   // Reference to Patient
    },
    "status": "completed",
    "code": {
        "coding": [{
            "system": "http://snomed.info/sct",
            "code": string,
            "display": string
        }]
    },
    "performedDateTime": string  // ISO8601 datetime
}
```

#### Observation Resource

```json
{
    "resourceType": "Observation",
    "id": string,             // UUID
    "status": "final",
    "subject": {
        "reference": string   // Reference to Patient
    },
    "code": {
        "coding": [{
            "system": "http://loinc.org",
            "code": string,
            "display": string
        }]
    },
    "valueQuantity": {        // For numeric values with units
        "value": number,
        "unit": string,
        "system": "http://unitsofmeasure.org",
        "code": string
    },
    // OR
    "valueString": string,    // For string values
    // OR
    "valueCodeableConcept": { // For coded values (e.g., blood type)
        "coding": [{
            "system": string,
            "code": string,
            "display": string
        }]
    },
    "effectiveDateTime": string  // ISO8601 datetime
}
```

### NDEF Message Format

Used for NFC tag data formatting.

```json
{
    "header": {
        "TNF": 0x02,        // Type Name Format (Media type)
        "IL": 0,            // ID Length field
        "MB": 1,            // Message Begin
        "ME": 1,            // Message End
        "CF": 0,            // Not chunked
        "SR": 0,            // Not a short record
        "type": string      // MIME type
    },
    "payload": binary/string // Patient data
}
```

### Web API Data Structures

#### GeneratorConfig

Configuration parameters for the generator.

```python
class GeneratorConfig(BaseModel):
    total_patients: int = 1440
    polish_front_percent: float = 50.0
    estonian_front_percent: float = 33.3
    finnish_front_percent: float = 16.7
    disease_percent: float = 52.0
    non_battle_percent: float = 33.0
    battle_trauma_percent: float = 15.0
    formats: list = ["json", "xml"]
    use_compression: bool = True
    use_encryption: bool = True
    base_date: str = "2025-06-01"
    encryption_password: str = ""
```

#### Job Status

Status information for a generation job.

```json
{
    "status": string,        // "queued", "running", "completed", "failed"
    "config": object,        // Original generator configuration
    "created_at": string,    // ISO8601 datetime
    "completed_at": string,  // ISO8601 datetime (if completed)
    "output_files": [string], // List of generated filenames
    "progress": number,      // Percentage complete (0-100)
    "summary": {             // Statistics on generated data
        "total_patients": number,
        "nationalities": {   // Count by nationality
            "POL": number,
            "EST": number,
            // etc.
        },
        "fronts": {          // Count by front
            "Polish": number,
            "Estonian": number,
            "Finnish": number
        },
        "injury_types": {    // Count by injury type
            "DISEASE": number,
            "NON_BATTLE": number,
            "BATTLE_TRAUMA": number
        },
        "final_status": {    // Count by final status
            "KIA": number,
            "RTD": number,
            "R1": number,
            "R2": number,
            "R3": number,
            "R4": number
        },
        "kia_count": number,
        "rtd_count": number,
        "still_in_treatment": number
    },
    "file_types": {         // Count of file extensions
        ".json": number,
        ".xml": number,
        ".gz": number,
        // etc.
    },
    "total_size": number,   // Total size in bytes
    "total_size_formatted": string // Human-readable size
}
```

### Data Transformation Flow

The patient data goes through these transformations during processing:

1. **Initial Patient Object**:
   - Basic demographics
   - Injury type and triage category
   - Initial POI event

2. **Enhanced Patient Object**:
   - Complete demographics
   - Primary and additional conditions
   - Medications and allergies
   - Treatment history with observations

3. **FHIR Bundle**:
   - Standards-compliant resources
   - Properly coded medical content
   - Complete references between resources

4. **Output Formats**:
   - JSON/XML
   - Optional compression
   - Optional encryption
   - NDEF formatting for NFC
