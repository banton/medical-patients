# Installation and Setup Guide

This guide provides detailed instructions for installing and setting up the Military Medical Exercise Patient Generator on different platforms.

## Prerequisites

Before installing the patient generator, ensure you have the following prerequisites:

- Python 3.8 or higher
- Pip (Python package installer)
- Git (optional, for cloning the repository)

## Installation

### Option 1: Install from ZIP file

1. Extract the ZIP file to a location of your choice
2. Open a terminal/command prompt and navigate to the extracted directory
3. Create a virtual environment:

   ```bash
   # On Windows
   python -m venv venv
   venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

4. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Install the package in development mode:

   ```bash
   pip install -e .
   ```

### Option 2: Install from GitHub

1. Clone the repository:

   ```bash
   git clone https://github.com/yourusername/military-patient-generator.git
   cd military-patient-generator
   ```

2. Follow steps 3-5 from Option 1.

## Running the Application

### Web Interface

To start the web application:

```bash
python app.py
```

Then open a web browser and navigate to http://localhost:8000.

### Command Line Demo

To run the command-line demo script:

```bash
python demo.py
```

This will generate a small set of patient data and save it to the `demo_output` directory.

## Configuration

The generator can be configured in several ways:

1. **Web Interface**: Use the form controls to adjust parameters.

2. **Python API**: When using the generator as a library, pass configuration parameters to the `PatientGeneratorApp` constructor:

   ```python
   from patient_generator.app import PatientGeneratorApp
   
   config = {
       "total_patients": 1440,
       "front_distribution": {
           "Polish": 0.50,
           "Estonian": 0.333,
           "Finnish": 0.167
       },
       "output_formats": ["json", "xml"],
       "output_directory": "my_output"
   }
   
   generator = PatientGeneratorApp(config)
   bundles = generator.run()
   ```

3. **Configuration File**: Create a JSON configuration file:

   ```json
   {
       "total_patients": 1440,
       "front_distribution": {
           "Polish": 0.50,
           "Estonian": 0.333,
           "Finnish": 0.167
       },
       "output_formats": ["json", "xml"],
       "output_directory": "my_output"
   }
   ```

   Then load it in your code:

   ```python
   import json
   from patient_generator.app import PatientGeneratorApp
   
   with open('config.json', 'r') as f:
       config = json.load(f)
   
   generator = PatientGeneratorApp(config)
   bundles = generator.run()
   ```

## Running Tests

To run the test suite:

```bash
python -m unittest tests.py
```

## Troubleshooting

### Common Issues

- **ModuleNotFoundError**: Ensure the package is installed correctly and the virtual environment is activated.
- **Permission Errors**: Ensure you have write permissions to the output directory.
- **Memory Issues**: If generating a large number of patients, increase available memory or reduce the batch size.

### Getting Help

If you encounter issues not covered in this guide, please:

1. Check the README.md file for additional information
2. Check the project's GitHub issue tracker
3. Contact the development team at your.email@example.com

## Advanced Configuration

### Encryption Settings

For advanced encryption settings, you can configure:

```python
config = {
    # ... other settings
    "use_encryption": True,
    "encryption_password": "your-secure-password"
}
```

### Custom SNOMED CT Codes

To use custom SNOMED CT codes, extend the `MedicalConditionGenerator` class:

```python
from patient_generator.medical import MedicalConditionGenerator

class CustomMedicalConditionGenerator(MedicalConditionGenerator):
    def __init__(self):
        super().__init__()
        # Add custom conditions
        self.battle_trauma_conditions.extend([
            {"code": "123456789", "display": "Custom condition"}
        ])
```