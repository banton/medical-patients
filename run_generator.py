#!/usr/bin/env python
"""
Optimized Military Medical Exercise Patient Generator
Run this script directly to test the optimized generator.
"""

import argparse
from collections import Counter
from datetime import datetime
import json
import os
import shutil
import sys
import time

# Add the parent directory to the Python path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from patient_generator.app import PatientGeneratorApp
    from patient_generator.config_manager import ConfigurationManager
    from patient_generator.nationality_data import NationalityDataProvider
    from patient_generator.schemas_config import ConfigurationTemplateDB
except ImportError:
    print("Error importing patient_generator package. Please make sure it's installed or in your Python path.")
    print("Try running: pip install -e .")
    sys.exit(1)


def create_config_from_args(args, config_data=None):
    """Create ConfigurationTemplateDB from command line arguments or config data."""
    if config_data:
        # From loaded JSON config
        return ConfigurationTemplateDB(
            id="cli-config",
            name="CLI Configuration",
            description="Configuration from command line",
            total_patients=config_data.get("total_patients", args.patients),
            injury_distribution={"Disease": 0.1, "Non-Battle Injury": 0.2, "Battle Injury": 0.7},
            front_configs=[],
            facility_configs=[],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    # From args directly
    return ConfigurationTemplateDB(
        id="cli-config",
        name="CLI Configuration",
        description="Configuration from command line",
        total_patients=args.patients,
        injury_distribution={"Disease": 0.1, "Non-Battle Injury": 0.2, "Battle Injury": 0.7},
        front_configs=[],
        facility_configs=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


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


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Generate patient data for military medical exercises")

    parser.add_argument("--patients", type=int, default=1440, help="Number of patients to generate (default: 1440)")

    parser.add_argument(
        "--output", type=str, default="output", help="Output directory for generated files (default: 'output')"
    )

    parser.add_argument("--threads", type=int, default=0, help="Number of worker threads (default: auto-detect)")

    parser.add_argument("--batch-size", type=int, default=0, help="Batch size for processing (default: auto-calculate)")

    parser.add_argument(
        "--polish", type=float, default=50.0, help="Percentage of casualties from Polish front (default: 50.0)"
    )

    parser.add_argument(
        "--estonian", type=float, default=33.3, help="Percentage of casualties from Estonian front (default: 33.3)"
    )

    parser.add_argument(
        "--finnish", type=float, default=16.7, help="Percentage of casualties from Finnish front (default: 16.7)"
    )

    parser.add_argument(
        "--formats",
        type=str,
        default="json,xml",
        help="Output formats (comma-separated, e.g., 'json,xml', default: 'json,xml')",
    )

    parser.add_argument("--no-compress", action="store_true", help="Disable compression of output files")

    parser.add_argument("--no-encrypt", action="store_true", help="Disable encryption of output files")

    parser.add_argument("--config", type=str, help="JSON configuration file path")

    parser.add_argument("--benchmark", action="store_true", help="Run in benchmark mode with timing information")

    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary files (don't clean up)")

    parser.add_argument("--temp-dir", type=str, help="Specify custom directory for temporary files")

    parser.add_argument("--clean-output", action="store_true", help="Remove output directory before starting")

    parser.add_argument("--max-memory", type=int, help="Maximum memory usage in MB")

    parser.add_argument(
        "--enable-medical-simulation",
        action="store_true",
        help="Enable enhanced medical simulation for realistic patient flow",
    )

    parser.add_argument("--medical-config", type=str, help="Path to medical simulation configuration file (JSON)")

    parser.add_argument(
        "--compare-performance",
        action="store_true",
        help="Run twice (with and without medical simulation) to compare performance",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    # Load configuration from file if provided
    config_data = None
    if args.config:
        try:
            with open(args.config) as f:
                config_data = json.load(f)
        except Exception as e:
            print(f"Error loading configuration file: {e}")
            sys.exit(1)

    # Clean output directory if requested
    output_dir = args.output if not config_data else config_data.get("output_directory", args.output)
    if args.clean_output and os.path.exists(output_dir):
        print(f"Cleaning output directory: {output_dir}")
        try:
            shutil.rmtree(output_dir)
        except Exception as e:
            print(f"Error cleaning output directory: {e}")

    # Set environment variables based on arguments
    if args.temp_dir:
        os.environ["PATIENT_GENERATOR_TEMP_DIR"] = args.temp_dir
    if args.keep_temp:
        os.environ["PATIENT_GENERATOR_CLEANUP_TEMP"] = "0"
    if args.max_memory:
        os.environ["PATIENT_GENERATOR_MAX_MEMORY"] = str(args.max_memory)

    # Medical simulation is now the default behavior
    os.environ["ENABLE_MEDICAL_SIMULATION"] = "true"
    if not args.enable_medical_simulation:
        # Only show message if explicitly disabled (which we don't support anymore)

        # Load medical config if provided
        if args.medical_config:
            try:
                with open(args.medical_config) as f:
                    medical_config = json.load(f)
                    # Could store this config for later use
                    os.environ["MEDICAL_SIMULATION_CONFIG"] = json.dumps(medical_config)
            except Exception as e:
                print(f"Warning: Could not load medical configuration: {e}")

    # Print startup information
    print("Military Medical Exercise Patient Generator (Optimized Version)")
    print("==============================================================")

    # Create configuration from arguments or loaded config
    config = create_config_from_args(args, config_data)

    print(f"Generating {config.total_patients} patients...")
    print(f"Output directory: {output_dir}")

    # Print front distribution
    print(f"Front distribution: Polish {args.polish:.1f}%, Estonian {args.estonian:.1f}%, Finnish {args.finnish:.1f}%")

    output_formats = args.formats.split(",")
    use_compression = not args.no_compress
    use_encryption = not args.no_encrypt

    print(f"Output formats: {', '.join(output_formats)}")
    print(f"Compression: {'Enabled' if use_compression else 'Disabled'}")
    print(f"Encryption: {'Enabled' if use_encryption else 'Disabled'}")

    # Create mock database with our config
    mock_db = MockDatabase(config)

    # Create ConfigurationManager with mock database
    config_manager = ConfigurationManager(database_instance=mock_db)

    # Monkey-patch the repository to return our config
    config_manager._repository = MockRepository(mock_db)
    config_manager._active_configuration = config

    # Create nationality provider
    nationality_provider = NationalityDataProvider()

    # Initialize and run the generator
    generator = PatientGeneratorApp(config_manager, nationality_provider)

    # Override performance settings if provided
    if args.threads > 0:
        generator.num_workers = args.threads
    if args.batch_size > 0:
        generator.batch_size = args.batch_size
    generator.output_directory = output_dir

    print(f"Using {generator.num_workers} worker threads with batch size of {generator.batch_size}")
    print("\nStarting generation...")

    start_time = time.time()
    patients, bundles, output_files, summary = generator.run(
        output_directory=output_dir,
        output_formats=output_formats,
        use_compression=use_compression,
        use_encryption=use_encryption,
    )
    end_time = time.time()

    # Calculate performance metrics
    total_time = end_time - start_time
    patients_per_second = len(patients) / total_time if total_time > 0 else 0
    time_per_patient = (total_time / len(patients)) * 1000 if patients else 0  # milliseconds

    # Print summary statistics
    status_counts = Counter([p.current_status for p in patients])

    print("\nGeneration complete!")
    print(f"Generated {len(patients)} patient records:")
    print(f"  - Killed in Action (KIA): {status_counts.get('KIA', 0)}")
    print(f"  - Returned to Duty (RTD): {status_counts.get('RTD', 0)}")
    print(f"  - Still in treatment: {sum(status_counts.get(status, 0) for status in ['R1', 'R2', 'R3', 'R4'])}")

    # Print nationality distribution
    nationality_counts = Counter([p.nationality for p in patients])
    print("\nNationality distribution:")
    for nationality, count in nationality_counts.most_common():
        print(f"  - {nationality}: {count} ({count / len(patients) * 100:.1f}%)")

    # Print performance metrics
    print("\n" + "=" * 60)
    print("PERFORMANCE METRICS")
    print("=" * 60)
    print(f"Total generation time:    {total_time:.2f} seconds")
    print(f"Patients per second:      {patients_per_second:.1f}")
    print(f"Time per patient:         {time_per_patient:.1f} ms")
    print(f"Worker threads:           {generator.num_workers}")
    print(f"Batch size:               {generator.batch_size}")

    # Medical simulation metrics if enabled
    if args.enable_medical_simulation:
        print("\nMedical Simulation Metrics:")
        try:
            # Try to get metrics from the bridge if it exists
            if hasattr(generator, "flow_simulator") and hasattr(generator.flow_simulator, "medical_bridge"):
                bridge_metrics = generator.flow_simulator.medical_bridge.metrics
                avg_time = (
                    bridge_metrics["total_time"] / bridge_metrics["total_enhanced"] * 1000
                    if bridge_metrics["total_enhanced"] > 0
                    else 0
                )
                print(f"  - Patients enhanced:    {bridge_metrics['total_enhanced']}")
                print(f"  - Avg enhancement time: {avg_time:.1f} ms")
                print(f"  - Slowest patient:      {bridge_metrics['slowest_patient'] * 1000:.1f} ms")

                # Calculate overhead
                time_per_patient - avg_time
                overhead_pct = (avg_time / time_per_patient * 100) if time_per_patient > 0 else 0
                print(f"  - Medical sim overhead: {overhead_pct:.1f}%")
        except Exception:
            print("  - Metrics unavailable (may need ConfigurationManager fix)")

    print("=" * 60)

    print(f"\nOutput files saved to {output_dir} directory.")
    if output_files:
        print("Generated files:")
        for file in output_files:
            print(f"  - {file}")

    if args.benchmark:
        # Write benchmark results to file
        benchmark_file = "benchmark_results.txt"
        with open(benchmark_file, "a") as f:
            f.write(
                f"{config.total_patients},{generator.num_workers},{generator.batch_size},{total_time:.2f},{patients_per_second:.2f}\n"
            )
        print(f"Benchmark results appended to {benchmark_file}")


if __name__ == "__main__":
    main()
