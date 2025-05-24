# Domain Knowledge: Medical and Military Context

This document provides background information on the medical and military concepts that form the foundation of the Military Medical Exercise Patient Generator. Understanding this context is crucial for developing and configuring realistic scenarios.

## NATO Medical Support Structure (Echelons of Care)

The system models the NATO echelon-based military medical support structure, representing a progressive chain of medical care:

1.  **Point of Injury (POI)**:
    *   The location where a casualty occurs.
    *   Initial care is often self-aid, buddy aid, or by a combat medic.
    *   Focus: Immediate life-saving interventions (e.g., stopping hemorrhage, airway management).

2.  **Role 1 (R1) - Battalion/Regimental Level**:
    *   Equivalent to a Battalion Aid Station or Regimental Aid Post.
    *   Provides primary healthcare, triage, resuscitation, and emergency medical treatment.
    *   Limited holding capacity (typically hours).
    *   Staffed by medical officers, physician assistants, and combat medics/medical technicians.
    *   Capabilities: Advanced trauma life support, minor surgical procedures, preparation for evacuation.

3.  **Role 2 (R2) - Brigade/Division Level**:
    *   Offers a forward surgical capability (Damage Control Surgery).
    *   Provides resuscitation, limited inpatient holding (24-72 hours), and preparation for further evacuation.
    *   Can be "Light Maneuver" (more mobile, basic surgery) or "Enhanced" (more capabilities, imaging, dental).
    *   Capabilities: Emergency surgery, blood transfusion, basic imaging (X-ray), limited laboratory support.

4.  **Role 3 (R3) - Corps/Theater Level**:
    *   Equivalent to a Combat Support Hospital or Field Hospital.
    *   Provides comprehensive multidisciplinary medical and surgical care.
    *   Significant inpatient holding capacity.
    *   Specialist surgical and medical capabilities (e.g., neurosurgery, orthopedics, internal medicine).
    *   Full range of diagnostic services (lab, X-ray, CT), intensive care unit (ICU).

5.  **Role 4 (R4) - Definitive Care / Strategic Level**:
    *   Represents definitive, comprehensive hospital care, often in the home nation or a secure third country.
    *   Full spectrum of medical and surgical specialties.
    *   Long-term treatment and rehabilitation capabilities.

## Patient Flow Concepts

The generator simulates casualty flow based on these principles:

1.  **Triage Categories (Example NATO Standard)**:
    *   **T1 (Immediate/Critical)**: Life-threatening injuries requiring immediate intervention to save life, limb, or eyesight.
    *   **T2 (Delayed/Urgent)**: Serious injuries requiring surgical or medical intervention, but can tolerate a delay without undue threat to life or limb.
    *   **T3 (Minimal/Routine)**: Minor injuries; "walking wounded" who can wait for treatment or assist with care.
    *   *(T4 - Expectant: Not actively modeled for progression in many simulation contexts, as resources are focused on salvageable casualties).*
    *   The system allows configuration of how triage categories influence flow and outcomes.

2.  **Evacuation Chain**:
    *   Casualties typically move from POI through progressively higher echelons of care (R1 → R2 → R3 → R4).
    *   The specific path and probabilities of movement (e.g., POI to R1, R1 to R2, R1 to RTD) are **configurable** within a scenario.
    *   Patients can be returned to duty (RTD) from various echelons if their condition improves sufficiently.
    *   Killed in Action (KIA) can occur at any point, with probabilities also being **configurable**.

3.  **Configurable Casualty Rates & Distributions**:
    *   The system allows for dynamic configuration of:
        *   Total patient numbers.
        *   Distribution of casualties across different "fronts" or operational areas.
        *   Mix of nationalities within each front.
        *   Overall distribution of injury types (e.g., Disease, Non-Battle Injury, Battle Injury).
        *   Timing of casualty presentation (e.g., distribution over exercise days/hours).
    *   While historical data (e.g., DNBI often outnumbering battle casualties) can inform scenario design, the generator allows planners to define these parameters.

## Medical Coding Systems

The system uses international medical coding standards for interoperability:

1.  **SNOMED CT (Systematized Nomenclature of Medicine - Clinical Terms)**:
    *   A comprehensive, multilingual clinical healthcare terminology.
    *   Used for coding medical conditions, procedures, findings, and severity.
    *   Examples: `125670008` (War injury), `19130008` (Traumatic brain injury).

2.  **LOINC (Logical Observation Identifiers Names and Codes)**:
    *   A standard for identifying medical laboratory observations, vital signs, and other clinical measurements.
    *   Used for coding observations like blood pressure, heart rate, lab results.
    *   Examples: `8310-5` (Body temperature), `8867-4` (Heart rate).

3.  **HL7 FHIR (Fast Healthcare Interoperability Resources)**:
    *   A standard for exchanging healthcare information electronically, using web technologies (RESTful APIs, JSON/XML).
    *   The generator produces FHIR R4 compliant bundles. Key resources include:
        *   `Patient`: Demographics.
        *   `Condition`: Diagnoses.
        *   `Observation`: Measurements, vital signs.
        *   `Procedure`: Treatments performed.
        *   `Bundle`: A collection of related resources for a patient.

## Military Medical Standards Compliance

The system aims to produce data compatible with:
*   **AMedP-8.1 (Minimal Core Medical Data)**: NATO standard for essential medical information.
*   **AMedP-8.8 (Medical Warning Tag)**: NATO standard for emergency medical information.
*   **International Patient Summary (ISO 27269:2021)**: Standard for a core patient data summary.

## Injury and Disease Patterns

The system can model various medical conditions, with specific types and frequencies being **configurable**:

1.  **Battle Trauma**: Injuries from combat (e.g., penetrating wounds, blast injuries, burns, amputations, TBI).
2.  **Non-Battle Injuries (NBI)**: Accidental injuries (e.g., vehicle accidents, falls, training injuries, environmental exposure).
3.  **Disease**: Illnesses and infections (e.g., respiratory, gastrointestinal, psychological stress reactions, skin infections).

## Demographics in Military Context

The generator creates patient demographics appropriate for military personnel, with parameters being **configurable**:
*   **Nationality Distribution**: Reflects exercise participants, configurable per front.
*   **Military-Appropriate Demographics**:
    *   Age ranges typical for military personnel.
    *   Gender distribution (configurable).
    *   Names appropriate to nationality (sourced from `demographics.json` via `NationalityDataProvider`).
    *   ID numbers (formats can be defined).
    *   Physical attributes (weight, blood type).

## NFC Technology in Military Medicine

The system supports data preparation for Near Field Communication (NFC) smart tags:
*   **Medical Smarttags**: NFC tags can carry essential patient medical data for tracking and interoperability.
*   **NDEF Format**: Data is formatted according to the NFC Data Exchange Format standard.
*   **Security**: Output can be compressed and encrypted for secure use on tags.

## Military Exercise Scenarios

The generator is designed to support various exercise types by allowing flexible configuration of casualty numbers, types, and flow:
*   Battalion-level exercises.
*   Multi-national training events.
*   Field Training Exercises (FTX).
*   Command Post Exercises (CPX).

## Configurable Casualty Distribution Examples

The following are *examples* of parameters that are **configurable** within the system, not hardcoded values:

*   **Time-Based Distribution**: Casualties can be configured to appear at different rates over exercise days/hours.
    *   *Example Pattern*: Day 1: 20%, Day 2: 40%, Day 4: 30%, Day 8: 10%.
*   **Geographic/Front Distribution**: The percentage of total casualties originating from different defined fronts.
    *   *Example Pattern*: Front Alpha: 60%, Front Bravo: 40%.
*   **Treatment Outcomes & Flow Probabilities**: For each facility, the probability of a patient moving to another specific facility, RTD, or KIA.
    *   *Example Pattern for R1*: 10% KIA, 50% RTD, 40% to R2.

These examples illustrate the types of parameters that users can define within a `ConfigurationScenario` to tailor the patient generation to their specific exercise needs.
