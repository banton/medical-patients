# Project Brief

## Core Requirements & Goals

The Military Medical Exercise Patient Generator is a web-based application designed to generate realistic dummy patient data for military medical exercises. The system supports multiple treatment facilities, nationalities, and injury types following NATO medical standards.

### Primary Goals

1. **Generate Realistic Medical Data**: Create simulated patient data that accurately represents the types and distributions of injuries and diseases encountered during military operations.

2. **Model Patient Flow**: Simulate patient movement through different medical treatment facilities (POI, R1, R2, R3, R4) with realistic progression statistics.

3. **Support Multiple Nationalities**: Generate patient data with appropriate demographics for different participating countries (POL, EST, GBR, FIN, USA, ESP, LIT, NLD).

4. **Comply with Medical Standards**: Produce data that complies with international medical data standards including:
   - Minimal Core Medical Data (AMedP-8.1)
   - Medical Warning tag (AMedP-8.8)
   - International Patient Summary ISO27269:2021
   - HL7 FHIR R4 formatted bundles

5. **Provide Multiple Output Formats**: Generate data in JSON, XML and other formats with optional compression and encryption.

6. **Support NFC Integration**: Prepare data for NDEF/NFC smarttag deployment for field use.

### Key Requirements

1. **Configurable Generation Parameters**:
   - Total patient count (default: 1440)
   - Distribution across fronts (Polish, Estonian, Finnish)
   - Injury type distribution (Disease, Non-battle, Battle trauma)
   - Output formats and security options

2. **Medical Accuracy**:
   - Realistic medical conditions using SNOMED CT codes
   - Appropriate treatment progression based on injury severity
   - Realistic vital signs and observations with LOINC codes

3. **Security Options**:
   - Compression (gzip)
   - Encryption (AES-256-GCM)
   - Password-based key derivation

4. **User Interface**:
   - Web-based configuration interface
   - Job management for batch processing
   - Visual summaries of generated data

5. **Command Line Support**:
   - For scripted/batch operations
   - Configuration via JSON files
