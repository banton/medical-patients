# Medical and Military Context

## Domain-Specific Knowledge

This document provides background information on the medical and military concepts that form the foundation of the Military Medical Exercise Patient Generator.

### NATO Medical Support Structure

The system models the NATO echelon-based military medical support structure:

1. **Point of Injury (POI)**:
   - Initial casualty location
   - Basic first aid or buddy care
   - Typically provided by combat medics or fellow soldiers
   - Focus on immediate life-saving interventions

2. **Role 1 (R1)**:
   - Battalion Aid Station or equivalent
   - Primary healthcare, triage, and basic emergency care
   - Limited holding capacity (usually hours, not days)
   - Staffed by medical officers and combat medics
   - Capabilities include basic trauma management, fluid resuscitation, and damage control

3. **Role 2 (R2)**:
   - Forward Surgical Capability
   - Damage control surgery and resuscitation
   - Limited holding capacity (24-72 hours)
   - Light and mobile (R2 Light) or enhanced (R2 Enhanced)
   - Capabilities include blood transfusion, emergency surgery, basic imaging

4. **Role 3 (R3)**:
   - Combat Support Hospital or Field Hospital
   - Comprehensive multidisciplinary care
   - Significant holding capacity
   - Specialist surgical capabilities
   - Full range of medical support including lab, X-ray, CT, and ICU

5. **Role 4 (R4)**:
   - Definitive Care Facility
   - Usually in home nation or safe third country
   - Full spectrum of medical care
   - Rehabilitation capabilities
   - Long-term treatment

### Patient Flow Concepts

The simulator models realistic casualty flow patterns:

1. **Triage Categories**:
   - **T1 (Immediate)**: Life-threatening conditions requiring immediate intervention
   - **T2 (Urgent)**: Serious injury requiring intervention within 2-4 hours
   - **T3 (Delayed)**: Less severe injuries that can wait 4+ hours
   - **T4 (Expectant)**: Not used in the simulator; those unlikely to survive despite care

2. **Evacuation Chain**:
   - Casualties move from point of injury through progressive levels of care
   - Movement depends on injury severity, capacity, and tactical situation
   - Casualties can be returned to duty (RTD) at any level if their condition allows
   - KIA (Killed in Action) can occur at any level but is more common at lower levels

3. **Realistic Casualty Rates**:
   - Based on historical data from modern conflicts
   - Disease and Non-Battle Injuries (DNBI) typically outnumber battle casualties
   - The default 52% disease, 33% non-battle injury, and 15% battle trauma reflects actual military operations
   - Different fronts may have different casualty patterns

### Medical Coding Systems

The system uses international medical coding standards:

1. **SNOMED CT (Systematized Nomenclature of Medicine - Clinical Terms)**:
   - International clinical terminology for electronic health records
   - Used for medical conditions, procedures, and severity
   - Hierarchical structure with unique codes
   - Examples in the system:
     - 125670008: War injury
     - 19130008: Traumatic brain injury
     - 7200002: Burn of skin

2. **LOINC (Logical Observation Identifiers Names and Codes)**:
   - Standard for identifying medical laboratory observations
   - Used for vital signs and lab tests
   - Examples in the system:
     - 8310-5: Body temperature
     - 8867-4: Heart rate
     - 8480-6: Systolic blood pressure
     - 718-7: Hemoglobin

3. **HL7 FHIR (Fast Healthcare Interoperability Resources)**:
   - Standard for exchanging healthcare information electronically
   - REST-based API with resource types
   - Main resources used:
     - Patient (demographics)
     - Condition (diagnoses)
     - Observation (measurements)
     - Procedure (treatments)
     - Bundle (collection of resources)

### Military Medical Standards

The system complies with several military medical data standards:

1. **AMedP-8.1 (Minimal Core Medical Data)**:
   - NATO standard for essential medical information
   - Ensures interoperability between nations
   - Includes patient identification, clinical data, and evacuation information

2. **AMedP-8.8 (Medical Warning Tag)**:
   - NATO standard for emergency medical information
   - Information carried by individual soldiers
   - Includes allergies, medications, and key medical history

3. **International Patient Summary (ISO27269:2021)**:
   - International standard for core patient data
   - Dataset for emergency or unplanned care
   - Supports cross-border healthcare

### Injury and Disease Patterns

The system models realistic medical conditions:

1. **Battle Trauma**:
   - Penetrating injuries (bullets, shrapnel)
   - Blast injuries
   - Burns
   - Traumatic amputations
   - Traumatic brain injuries

2. **Non-Battle Injuries**:
   - Vehicle accidents
   - Environmental injuries (heat, cold)
   - Sports/training injuries
   - Falls and crush injuries
   - Workplace accidents

3. **Disease**:
   - Respiratory infections
   - Gastrointestinal illnesses
   - Psychological stress reactions
   - Skin infections
   - Urinary tract infections

### Demographics in Military Context

The system generates realistic demographics for different participating nations:

1. **Nationality Distribution**:
   - Reflects typical NATO exercise participation
   - Different nationalities are concentrated on different "fronts"
   - Each front has a primary nation and supporting nations

2. **Military-Appropriate Demographics**:
   - Age ranges typical for military personnel (18-50 years)
   - Realistic gender distribution
   - Appropriate names for nationality
   - ID numbers following national formats
   - Realistic physical attributes (weight, blood type)

### NFC Technology in Military Medicine

The system supports Near Field Communication (NFC) technology use:

1. **Medical Smarttags**:
   - NFC tags containing patient medical data
   - Used to track casualties through medical system
   - Replaces or augments paper records
   - Enhances medical interoperability

2. **NDEF Format**:
   - NFC Data Exchange Format standard
   - Structured format for NFC tag data
   - Different MIME types for different content formats
   - Used to prepare data for NFC deployment

3. **Security Considerations**:
   - Compression to fit more data on limited-size tags
   - Encryption for sensitive medical information
   - Different security levels for different exercises

### Military Exercise Scenarios

The system is designed to support these common exercise types:

1. **Battalion-level Exercises**:
   - Typically 1400+ simulated casualties
   - Full medical evacuation chain
   - Multiple participating units

2. **Multi-national Training**:
   - Forces from different NATO and partner nations
   - Focus on interoperability challenges
   - Multiple languages and medical systems

3. **Field Training Exercises**:
   - Physical deployment of medical units
   - Actual movement of simulated casualties
   - Use of medical tags and records

4. **Command Post Exercises**:
   - Focus on command and control
   - Larger number of simulated casualties
   - Testing information flow and decision-making

### Realistic Casualty Distribution

The system models time-based casualty flow:

1. **Day Distribution**:
   - Day 1: 20% (initial engagement)
   - Day 2: 40% (peak of operations)
   - Day 4: 30% (continued operations)
   - Day 8: 10% (final operations)

2. **Geographic Distribution**:
   - Polish Front: 50% (main effort)
   - Estonian Front: 33.3% (secondary effort)
   - Finnish Front: 16.7% (supporting effort)

3. **Treatment Outcomes**:
   - At POI: 20% KIA, 80% to R1
   - At R1: 12% KIA, 60% RTD, 28% to R2
   - At R2: 13.7% KIA, 55% RTD, 31.3% to R3
   - At R3: 12.1% KIA, 30% RTD, 57.9% to R4
   - R4 is a terminal state (definitive care)
