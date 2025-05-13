#!/usr/bin/env python
"""
Optimized Military Medical Exercise Patient Generator
Run this script directly to test the optimized generator.
"""

import os
import sys
import time
import argparse
import json
from collections import Counter

# Add the parent directory to the Python path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from patient_generator.app import PatientGeneratorApp
except ImportError:
    print("Error importing patient_generator package. Please make sure it's installed or in your Python path.")
    print("Try running: pip install -e .")
    sys.exit(1)

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Generate patient data for military medical exercises")
    
    parser.add_argument("--patients", type=int, default=1440,
                        help="Number of patients to generate (default: 1440)")
    
    parser.add_argument("--output", type=str, default="output",
                        help="Output directory for generated files (default: 'output')")
    
    parser.add_argument("--threads", type=int, default=0,
                        help="Number of worker threads (default: auto-detect)")
    
    parser.add_argument("--batch-size", type=int, default=0,
                        help="Batch size for processing (default: auto-calculate)")
    
    parser.add_argument("--polish", type=float, default=50.0,
                        help="Percentage of casualties from Polish front (default: 50.0)")
    
    parser.add_argument("--estonian", type=float, default=33.3,
                        help="Percentage of casualties from Estonian front (default: 33.3)")
    
    parser.add_argument("--finnish", type=float, default=16.7,
                        help="Percentage of casualties from Finnish front (default: 16.7)")
    
    parser.add_argument("--formats", type=str, default="json,xml",
                        help="Output formats (comma-separated, e.g., 'json,xml', default: 'json,xml')")
    
    parser.add_argument("--no-compress", action="store_true",
                        help="Disable compression of output files")
    
    parser.add_argument("--no-encrypt", action="store_true",
                        help="Disable encryption of output files")
    
    parser.add_argument("--config", type=str,
                        help="JSON configuration file path")
    
    parser.add_argument("--benchmark", action="store_true",
                        help="Run in benchmark mode with timing information")
    
    parser.add_argument("--keep-temp", action="store_true",
                        help="Keep temporary files (don't clean up)")
    
    parser.add_argument("--temp-dir", type=str,
                        help="Specify custom directory for temporary files")
    
    parser.add_argument("--clean-output", action="store_true",
                        help="Remove output directory before starting")
    
    parser.add_argument("--max-memory", type=int,
                        help="Maximum memory usage in MB")
    
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # Initialize configuration
    if args.config:
        # Load configuration from file
        try:
            with open(args.config, 'r') as f:
                config = json.load(f)
        except Exception as e:
            print(f"Error loading configuration file: {e}")
            sys.exit(1)
    else:
        # Create configuration from command line arguments
        config = {
            "total_patients": args.patients,
            "output_directory": args.output,
            "front_distribution": {
                "Polish": args.polish / 100.0,
                "Estonian": args.estonian / 100.0,
                "Finnish": args.finnish / 100.0
            },
            "output_formats": args.formats.split(','),
            "use_compression": not args.no_compress,
            "use_encryption": not args.no_encrypt
        }
        
        # Add performance configuration
        performance_config = {}
        if args.threads > 0:
            performance_config["num_workers"] = args.threads
        if args.batch_size > 0:
            performance_config["batch_size"] = args.batch_size
        if args.max_memory:
            performance_config["max_memory_mb"] = args.max_memory
        if args.temp_dir:
            performance_config["temp_dir"] = args.temp_dir
        if args.keep_temp:
            performance_config["cleanup_temp"] = False
            
        if performance_config:
            config["performance"] = performance_config
            
    # Clean output directory if requested
    if args.clean_output and os.path.exists(config["output_directory"]):
        print(f"Cleaning output directory: {config['output_directory']}")
        try:
            shutil.rmtree(config["output_directory"])
        except Exception as e:
            print(f"Error cleaning output directory: {e}")
            
    # Set environment variables based on arguments
    if args.temp_dir:
        os.environ["PATIENT_GENERATOR_TEMP_DIR"] = args.temp_dir
    if args.keep_temp:
        os.environ["PATIENT_GENERATOR_CLEANUP_TEMP"] = "0"
    if args.max_memory:
        os.environ["PATIENT_GENERATOR_MAX_MEMORY"] = str(args.max_memory)
    
    # Print startup information
    print("Military Medical Exercise Patient Generator (Optimized Version)")
    print("==============================================================")
    
    print(f"Generating {config['total_patients']} patients...")
    print(f"Output directory: {config['output_directory']}")
    
    # Print front distribution
    front_dist = config.get('front_distribution', {})
    print(f"Front distribution: Polish {front_dist.get('Polish', 0.5)*100:.1f}%, "
          f"Estonian {front_dist.get('Estonian', 0.333)*100:.1f}%, "
          f"Finnish {front_dist.get('Finnish', 0.167)*100:.1f}%")
    
    print(f"Output formats: {', '.join(config.get('output_formats', ['json', 'xml']))}")
    print(f"Compression: {'Enabled' if config.get('use_compression', True) else 'Disabled'}")
    print(f"Encryption: {'Enabled' if config.get('use_encryption', True) else 'Disabled'}")
    
    # Initialize and run the generator
    generator = PatientGeneratorApp(config)
    
    print(f"Using {generator.num_workers} worker threads with batch size of {generator.batch_size}")
    print("\nStarting generation...")
    
    start_time = time.time()
    patients, bundles = generator.run()
    end_time = time.time()
    
    # Calculate performance metrics
    total_time = end_time - start_time
    patients_per_second = len(patients) / total_time if total_time > 0 else 0
    
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
        print(f"  - {nationality}: {count} ({count/len(patients)*100:.1f}%)")
    
    # Print performance metrics
    print("\nPerformance metrics:")
    print(f"  - Total generation time: {total_time:.2f} seconds")
    print(f"  - Patients per second: {patients_per_second:.2f}")
    print(f"  - Worker threads: {generator.num_workers}")
    print(f"  - Batch size: {generator.batch_size}")
    
    print(f"\nOutput files saved to {config['output_directory']} directory.")
    
    if args.benchmark:
        # Write benchmark results to file
        benchmark_file = "benchmark_results.txt"
        with open(benchmark_file, "a") as f:
            f.write(f"{config['total_patients']},{generator.num_workers},{generator.batch_size},{total_time:.2f},{patients_per_second:.2f}\n")
        print(f"Benchmark results appended to {benchmark_file}")

if __name__ == "__main__":
    main()