# Military Medical Exercise Patient Generator

A web-based application to generate realistic dummy patient data for military medical exercises, with support for multiple treatment facilities, nationalities, and injury types following NATO medical standards.

## Overview

This application generates simulated patient data for military medical exercises, specifically designed to model patient flow through different medical treatment facilities (POI, R1, R2, R3, R4) with realistic progression statistics. The generated data complies with international medical data standards including:

- Minimal Core Medical Data (AMedP-8.1)
- Medical Warning tag (AMedP-8.8)
- International Patient Summary ISO27269:2021
- HL7 FHIR R4 formatted bundles

## Features

- **Realistic Patient Flow Simulation**: Models 1400+ patients through the full medical evacuation chain
- **Configurable Nationality Distribution**: Support for multiple nationalities (POL, EST, GBR, FIN, USA, ESP, LIT, NLD)
- **Medical Condition Generation**: Creates realistic medical conditions using SNOMED CT codes
- **Treatment Facility Progression**: Simulates patient flow through POI, R1, R2, R3, and R4 facilities
- **Multiple Output Formats**: Generates data in JSON, XML and other formats
- **Data Security Options**: Supports gzip compression and AES-256-GCM encryption
- **NFC-Ready Formatting**: Prepares data for NDEF/NFC smarttag deployment
- **Web-based Interface**: Simple single-page application for configuring and generating patient data

## Architecture

The application follows a modular design with these main components:

1. **Web Interface**: Single-page application for configuration and batch processing
2. **Backend API**: FastAPI-based server handling job management and file generation 
3. **Generator Engine**: Core Python modules for creating patient data:
   - Patient flow simulator
   - Demographics generator
   - Medical condition generator
   - FHIR bundle generator
   - Output formatter

## Installation

### Requirements

- Python 3.8+
- Required Python packages (see `requirements.txt`)

### Setup

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/military-patient-generator.git
   cd military-patient-generator
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python app.py
   ```

4. Access the web interface at http://localhost:8000

### Docker Deployment

For containerized deployment, refer to the [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) guide for detailed instructions on building and running the application using Docker and Docker Compose. Various configurations (development, production, Traefik, etc.) are provided.

## Usage

1. **Configure Generation Parameters**:
   - Set the total number of patients (default: 1400)
   - Adjust the distribution across fronts (Polish, Estonian, Finnish)
   - Configure injury type distribution (Disease, Non-battle, Battle trauma)
   - Select output formats (JSON, XML)
   - Enable/disable compression and encryption

2. **Generate Patients**:
   - Click "Generate Patients" to start a generation job
   - View progress in the Jobs panel
   - Download results as a ZIP archive when complete

3. **Use Generated Data**:
   - Import into exercise management systems
   - Deploy to NFC smarttags
   - Use in medical treatment facility simulations

## Data Structure

The generated patient data follows the HL7 FHIR R4 standard with the following key components:

- **Patient Resources**: Demographics, identification, nationality
- **Condition Resources**: Medical conditions using SNOMED CT codes
- **Observation Resources**: Vital signs and measurements with LOINC codes
- **Procedure Resources**: Treatments performed at each facility
- **Bundle Resources**: Complete patient records with timestamps

## Configuration Options

| Parameter | Description | Default |
|-----------|-------------|---------|
| Total Patients | Number of patients to generate | 1440 |
| Polish Front % | Percentage of casualties from Polish front | 50.0% |
| Estonian Front % | Percentage of casualties from Estonian front | 33.3% |
| Finnish Front % | Percentage of casualties from Finnish front | 16.7% |
| Disease % | Percentage of patients with disease | 52.0% |
| Non-Battle % | Percentage with non-battle injuries | 33.0% |
| Battle Trauma % | Percentage with battle trauma | 15.0% |
| Base Date | Starting date for the exercise scenario | 2025-06-01 |
| Output Formats | Available formats (JSON, XML) | Both |
| Compression | Generate compressed files | Enabled |
| Encryption | Generate encrypted files | Enabled |

## Security

The application supports AES-256-GCM encryption for sensitive patient data. You can either:
- Provide a password (which will be used with PBKDF2 to derive a key)
- Let the system generate a random key (suitable for testing)

## Project Structure

```
military-patient-generator/
├── app.py                      # Main FastAPI application
├── requirements.txt            # Python dependencies
├── static/                     # Static web files
│   └── index.html              # Single page interface
│
└── patient_generator/          # Core generation modules
    ├── __init__.py
    ├── app.py                  # PatientGeneratorApp
    ├── patient.py              # Patient class
    ├── flow_simulator.py       # Patient flow simulator
    ├── demographics.py         # Demographics generator
    ├── medical.py              # Medical condition generator
    ├── fhir_generator.py       # FHIR bundle generator
    └── formatter.py            # Output formatter
```

## Standards Compliance

This generator creates data compliant with:
- HL7 FHIR R4 standard
- SNOMED CT for conditions, procedures and other medical items
- LOINC for lab values and observations
- ISO3166 alpha-3 for country codes
- ISO8601 for dates and times
- NDEF format specifications for NFC compatibility

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Git Branching Strategy

This project follows a structured Git branching model:

-   **`main`**: This branch represents the most stable, production-ready version of the code. Only tested and approved code from the `develop` branch is merged into `main`, typically during a release. Direct commits to `main` are discouraged.
-   **`develop`**: This is the primary integration branch for new features and ongoing development. All feature branches are created from `develop` and merged back into `develop` upon completion and review. Nightly builds or CI/CD processes may run against this branch.
-   **Feature Branches (`feature/<epic-name>/<task-name>`)**:
    *   When starting a new feature or task (e.g., as defined in `memory-bank/active-context.md`), create a new branch from `develop`.
    *   Use a descriptive naming convention, for example: `feature/config-api/add-crud-endpoints` or `feature/db-migration/setup-postgres`.
    *   Commit work regularly to your feature branch.
    *   Once the feature is complete, tested, and reviewed, create a Pull Request to merge it into `develop`.
-   **Release Branches (`release/vX.Y.Z`)**:
    *   When `develop` has accumulated enough features for a new release, a `release` branch is created from `develop`.
    *   This branch is used for final testing, bug fixes, and preparing release-specific documentation. No new features are added here.
    *   Once ready, the `release` branch is merged into `main` (and tagged with the version number, e.g., `v1.2.0`) and also back into `develop` to ensure any fixes made during the release process are incorporated into future development.
-   **Hotfix Branches (`hotfix/<issue-id>` or `hotfix/<description>`)**:
    *   If a critical bug is found in `main` (production), a `hotfix` branch is created directly from `main`.
    *   The fix is applied and tested on this branch.
    *   Once complete, the `hotfix` branch is merged into `main` (and tagged with an incremented patch version, e.g., `v1.2.1`) and also into `develop` to ensure the fix is included in ongoing development.

This strategy helps maintain a clean and stable `main` branch while allowing for parallel development and organized integration of new features.

### Key Development Files

- `.gitignore`: Specifies intentionally untracked files that Git should ignore. This has been recently updated to include common OS-generated files, Node.js artifacts, and log files.
- `.clinerules`: Contains project-specific intelligence and patterns for Cline (the AI assistant).
- `memory-bank/`: Stores contextual information about the project to aid AI-assisted development.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- This tool was developed to support NATO medical interoperability exercises
- Special thanks to the medical subject matter experts who provided guidance on realistic patient flow and treatment scenarios
