# Getting Started

This guide will walk you through using the Military Medical Exercise Patient Generator to create realistic medical data for your exercises.

## Basic Concepts

The patient generator simulates casualties flowing through different medical treatment facilities:

- **Point of Injury (POI)**: Initial casualty location
- **Role 1 (R1)**: Battalion aid station or similar basic treatment
- **Role 2 (R2)**: Forward surgical capability
- **Role 3 (R3)**: Combat support hospital with specialist capabilities
- **Role 4 (R4)**: Definitive care, often in home country

Patients can also reach these end states:
- **RTD**: Return to duty
- **KIA**: Killed in action

## Using the Web Interface

1. **Configure Generation Parameters**
   
   ![Configuration Panel](https://placeholder.com/web-interface.png)
   
   - Set total number of patients (typically 1400 for battalion-level exercises)
   - Adjust nationality distributions across the three fronts
   - Configure injury types distribution
   - Select output formats and options

2. **Generate Patients**
   
   Click "Generate Patients" to start the generation job. The progress will be displayed in the Jobs panel.

3. **Download Results**
   
   Once the job completes, click "Download Files" to get a ZIP archive containing:
   - All generated patient records in selected formats (JSON, XML)
   - Optional compressed and encrypted versions
   - Sample NDEF files for NFC tag testing

## Using the Command Line

For scripted or batch operations, first ensure your environment is set up:

```bash
# Set Python path (required for modular imports)
export PYTHONPATH=/path/to/medical-patients

# Run the generator directly
python src/main.py

# Or use Docker
docker compose up

# Generate specific nationality distribution
python -m patient_generator.cli --polish 60 --estonian 25 --finnish 15
```

## Using the API

The REST API provides programmatic access to all functionality:

```bash
# List all configurations
curl -H "X-API-Key: your_api_key" http://localhost:8000/api/v1/configurations/

# Create a new configuration
curl -X POST -H "X-API-Key: your_api_key" -H "Content-Type: application/json" \
  -d @config.json http://localhost:8000/api/v1/configurations/

# Generate patients
curl -X POST -H "X-API-Key: your_api_key" -H "Content-Type: application/json" \
  -d '{"configuration_id": "config-uuid"}' http://localhost:8000/api/generate

# Check job status
curl -H "X-API-Key: your_api_key" http://localhost:8000/api/jobs/{job_id}
```

See the [API Documentation](http://localhost:8000/docs) for complete details.

## Integration with Other Systems

### NDEF Smarttags

The generator produces sample NDEF-formatted data ready for loading onto NFC smarttags:

- **Plain Format**: `sample_plain.ndef.json`
- **Compressed**: `sample_gzip.ndef.bin`
- **Encrypted**: `sample_encrypted.ndef.bin`
- **Compressed and Encrypted**: `sample_gzip_encrypted.ndef.bin`

### FHIR Bundles

All patient data is structured as HL7 FHIR R4 bundles, making it compatible with:

- Electronic health record (EHR) systems
- Medical simulation software
- FHIR-compatible databases
- Medical visualization tools

## Example Scenarios

### Battalion-level Exercise

For a typical battalion-level exercise with 1400 patients:

1. Configure the generator with the default settings
2. Generate JSON and XML outputs
3. Import the JSON into your exercise management system
4. Distribute a subset of records to RFID/NFC tags for field use

### Multi-national Training

For an exercise involving multiple countries:

1. Adjust the nationality distribution to match participating forces
2. Generate data with multiple language support
3. Use the encrypted output option for sensitive information
4. Share the encryption key through secure channels

## Tips for Realistic Scenarios

- **Time Distribution**: Use the default distribution (Day 1: 20%, Day 2: 40%, Day 4: 30%, Day 8: 10%) for realistic casualty flow
- **Injury Mix**: The standard 52% disease, 33% non-battle injury, and 15% battle trauma reflects real-world military operations
- **Treatment Facilities**: The generator simulates realistic patient flow with appropriate evacuation rates and return-to-duty percentages

## Next Steps

- Try the [demo script](demo.py) to see a small-scale example
- Review the [full documentation](https://github.com/yourusername/military-patient-generator/wiki) for advanced features
- Join our [user community](https://example.com/forum) to share experiences and best practices