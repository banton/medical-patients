#!/usr/bin/env python3
"""
Simple wrapper for patient generator that works without database.
Creates ConfigurationManager with in-memory configuration.
"""

import argparse
import json
import os
import sys
import time
from collections import Counter

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from patient_generator.config_manager import ConfigurationManager
from patient_generator.app import PatientGeneratorApp
from patient_generator.schemas_config import ConfigurationTemplateDB
from patient_generator.nationality_data import NationalityDataProvider


def create_config_from_args(args):
    """Create ConfigurationTemplateDB from command line arguments."""
    from datetime import datetime
    
    return ConfigurationTemplateDB(
        id="cli-config",
        name="CLI Configuration",
        description="Configuration from command line",
        total_patients=args.patients,
        injury_distribution={
            "Disease": 0.1,
            "Non-Battle Injury": 0.2,
            "Battle Injury": 0.7
        },
        front_configs=[],
        facility_configs=[],
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate patient data for military medical exercises")
    
    parser.add_argument("--patients", type=int, default=100, 
                       help="Number of patients to generate (default: 100)")
    
    parser.add_argument("--output", type=str, default="output",
                       help="Output directory for generated files (default: 'output')")
    
    parser.add_argument("--enable-medical-simulation", action="store_true",
                       help="Enable enhanced medical simulation for realistic patient flow")
    
    parser.add_argument("--threads", type=int, default=4,
                       help="Number of worker threads (default: 4)")
    
    parser.add_argument("--batch-size", type=int, default=50,
                       help="Batch size for processing (default: 50)")
    
    return parser.parse_args()


class MockDatabase:
    """Mock database that returns our CLI configuration."""
    def __init__(self, config):
        self.config = config
        

class MockRepository:
    """Mock repository that returns our CLI configuration."""
    def __init__(self, db):
        self.config = db.config
    
    def get_configuration(self, config_id):
        return self.config


def main():
    args = parse_arguments()
    
    # Set medical simulation environment variable
    if args.enable_medical_simulation:
        os.environ["ENABLE_MEDICAL_SIMULATION"] = "true"
        print("Medical simulation enhancement enabled")
    
    print("Military Medical Exercise Patient Generator (Simple Version)")
    print("=" * 60)
    print(f"Generating {args.patients} patients...")
    print(f"Output directory: {args.output}")
    
    # Create configuration from arguments
    config = create_config_from_args(args)
    
    # Create mock database with our config
    mock_db = MockDatabase(config)
    
    # Create ConfigurationManager with mock database
    config_manager = ConfigurationManager(database_instance=mock_db)
    
    # Monkey-patch the repository to return our config
    config_manager._repository = MockRepository(mock_db)
    config_manager._active_configuration = config
    
    # Create nationality provider
    nationality_provider = NationalityDataProvider()
    
    # Initialize generator with ConfigurationManager
    try:
        generator = PatientGeneratorApp(config_manager, nationality_provider)
        
        # Override performance settings
        generator.num_workers = args.threads
        generator.batch_size = args.batch_size
        generator.output_directory = args.output
        
        print(f"Using {generator.num_workers} worker threads with batch size of {generator.batch_size}")
        print("\nStarting generation...")
        
        start_time = time.time()
        patients, bundles, output_files, summary = generator.run(
            output_directory=args.output,
            output_formats=["json", "xml"],
            use_compression=True,
            use_encryption=False
        )
        end_time = time.time()
        
        # Calculate performance metrics
        total_time = end_time - start_time
        patients_per_second = len(patients) / total_time if total_time > 0 else 0
        time_per_patient = (total_time / len(patients)) * 1000 if patients else 0
        
        # Print results
        print("\nGeneration complete!")
        print(f"Generated {len(patients)} patient records")
        
        # Print performance metrics
        print("\n" + "="*60)
        print("PERFORMANCE METRICS")
        print("="*60)
        print(f"Total generation time:    {total_time:.2f} seconds")
        print(f"Patients per second:      {patients_per_second:.1f}")
        print(f"Time per patient:         {time_per_patient:.1f} ms")
        print(f"Worker threads:           {generator.num_workers}")
        print(f"Batch size:               {generator.batch_size}")
        
        # Medical simulation metrics if enabled
        if args.enable_medical_simulation:
            print("\nMedical Simulation Metrics:")
            try:
                if hasattr(generator, 'flow_simulator') and hasattr(generator.flow_simulator, 'medical_bridge'):
                    bridge_metrics = generator.flow_simulator.medical_bridge.metrics
                    if bridge_metrics['total_enhanced'] > 0:
                        avg_time = (bridge_metrics['total_time'] / bridge_metrics['total_enhanced'] * 1000)
                        print(f"  - Patients enhanced:    {bridge_metrics['total_enhanced']}")
                        print(f"  - Avg enhancement time: {avg_time:.1f} ms")
                        print(f"  - Slowest patient:      {bridge_metrics['slowest_patient']*1000:.1f} ms")
                        overhead_pct = (avg_time / time_per_patient * 100) if time_per_patient > 0 else 0
                        print(f"  - Medical sim overhead: {overhead_pct:.1f}%")
                    else:
                        print("  - No patients were enhanced (check integration)")
            except Exception as e:
                print(f"  - Metrics unavailable: {e}")
        
        print("="*60)
        print(f"\nOutput files saved to {args.output} directory.")
        
    except Exception as e:
        print(f"Error during generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()