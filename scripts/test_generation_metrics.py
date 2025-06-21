#!/usr/bin/env python3
"""
Test generation pipeline metrics without requiring database.
This script tests the optimizations directly by monitoring memory and performance.
"""

import asyncio
import gc
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from typing import Dict, List
from unittest.mock import MagicMock, patch

import psutil

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from patient_generator.config_manager import ConfigurationManager
from patient_generator.demographics import DemographicsGenerator
from patient_generator.flow_simulator import PatientFlowSimulator
from patient_generator.formatter import OutputFormatter
from patient_generator.medical import MedicalConditionGenerator
from patient_generator.schemas_config import ConfigurationTemplateDB
from src.core.metrics import get_metrics_collector
from src.domain.services.patient_generation_service import (
    AsyncPatientGenerationService,
    GenerationContext,
    PatientGenerationPipeline,
)


class GenerationMetricsTester:
    """Test generation pipeline with metrics collection."""

    def __init__(self):
        self.results = []
        self.process = psutil.Process()
        self.metrics_collector = get_metrics_collector()

    def get_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024

    def parse_metrics(self) -> Dict:
        """Parse current Prometheus metrics."""
        metrics_bytes = self.metrics_collector.get_metrics()
        metrics_text = metrics_bytes.decode("utf-8")

        parsed = {}
        for line in metrics_text.split("\n"):
            if line and not line.startswith("#"):
                parts = line.split(" ")
                if len(parts) == 2:
                    metric_name = parts[0].split("{")[0]
                    try:
                        value = float(parts[1])
                        parsed[metric_name] = value
                    except ValueError:
                        pass
        return parsed

    async def test_generation(
        self,
        patient_count: int,
        use_temporal: bool = False,
        output_formats: List[str] = None
    ) -> Dict:
        """Test generation with metrics."""
        if output_formats is None:
            output_formats = ["json"]

        print(f"\n🧪 Testing: {patient_count} patients, "
              f"{'temporal' if use_temporal else 'standard'}, "
              f"formats: {output_formats}")

        # Record baseline
        metrics_before = self.parse_metrics()
        memory_before = self.get_memory_mb()
        gc.collect()  # Clean baseline

        # Create mock configuration
        from datetime import datetime

        config = ConfigurationTemplateDB(
            id=f"test-{patient_count}",
            name=f"Test {patient_count}",
            description="Metrics test",
            total_patients=patient_count,
            injury_distribution={
                "Disease": 0.52,
                "Non-Battle Injury": 0.33,
                "Battle Injury": 0.15
            },
            front_configs=[],
            facility_configs=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )

        # Create temporal config if needed
        temporal_config = None
        if use_temporal:
            temporal_config = {
                "warfare_types": {"conventional": True, "urban": True},
                "base_date": "2025-06-01",
                "days_of_fighting": 8,
                "total_patients": patient_count,
                "intensity": "high",
                "tempo": "sustained",
                "environmental_conditions": {"night_operations": True},
                "special_events": {"mass_casualty": True},
                "injury_mix": config.injury_distribution
            }

        # Create generation context
        with tempfile.TemporaryDirectory() as tmpdir:
            context = GenerationContext(
                config=config,
                job_id=f"test-{int(time.time())}",
                output_directory=tmpdir,
                output_formats=output_formats,
                use_compression=False,
                temporal_config=temporal_config
            )

            # Mock database and create service
            with patch("src.infrastructure.database_adapter.get_enhanced_database"):
                service = AsyncPatientGenerationService()

                # Mock config manager
                mock_config_manager = MagicMock(spec=ConfigurationManager)
                mock_config_manager.get_active_configuration.return_value = MagicMock(
                    total_patients=patient_count,
                    created_at=MagicMock(strftime=MagicMock(return_value="2025-01-01"))
                )
                mock_config_manager.get_front_configs.return_value = [
                    {"id": "front1", "casualty_rate": 1.0}
                ]
                mock_config_manager.get_injury_distribution.return_value = config.injury_distribution
                mock_config_manager.get_facility_configs.return_value = [
                    {"id": "POI", "kia_rate": 0.1, "rtd_rate": 0.1}
                ]

                # Create pipeline components
                flow_simulator = PatientFlowSimulator(mock_config_manager, temporal_config)
                demographics_gen = DemographicsGenerator()
                medical_gen = MedicalConditionGenerator()
                formatter = OutputFormatter()

                # Create pipeline
                service.pipeline = PatientGenerationPipeline(
                    flow_simulator=flow_simulator,
                    demographics_generator=demographics_gen,
                    medical_generator=medical_gen,
                    output_formatter=formatter
                )

                # Mock cache warming
                service.cached_demographics.warm_cache = asyncio.coroutine(lambda: None)
                service.cached_medical.warm_cache = asyncio.coroutine(lambda: None)

                # Track memory during generation
                memory_samples = []
                generation_start = time.time()

                async def progress_callback(progress_data):
                    memory_samples.append(self.get_memory_mb())

                # Run generation
                try:
                    result = await service.generate_patients(context, progress_callback)
                    success = True
                    error = None
                except Exception as e:
                    success = False
                    error = str(e)
                    result = {}

                generation_time = time.time() - generation_start

                # Get final metrics
                metrics_after = self.parse_metrics()
                memory_after = self.get_memory_mb()

                # Check output files
                file_sizes = {}
                if success:
                    for fmt in output_formats:
                        file_path = Path(tmpdir) / f"patients.{fmt}"
                        if file_path.exists():
                            file_sizes[fmt] = file_path.stat().st_size / 1024 / 1024  # MB

                # Calculate metrics
                peak_memory = max(memory_samples) if memory_samples else memory_after
                avg_memory = sum(memory_samples) / len(memory_samples) if memory_samples else memory_after

                # Extract generation metrics
                generation_count_diff = (
                    metrics_after.get("patients_generated_total", 0) -
                    metrics_before.get("patients_generated_total", 0)
                )

                return {
                    "patient_count": patient_count,
                    "use_temporal": use_temporal,
                    "output_formats": output_formats,
                    "success": success,
                    "error": error,
                    "generation_time": generation_time,
                    "patients_per_second": patient_count / generation_time if generation_time > 0 else 0,
                    "memory_before_mb": memory_before,
                    "memory_after_mb": memory_after,
                    "memory_peak_mb": peak_memory,
                    "memory_avg_mb": avg_memory,
                    "memory_increase_mb": memory_after - memory_before,
                    "memory_per_patient_mb": (peak_memory - memory_before) / patient_count if patient_count > 0 else 0,
                    "file_sizes_mb": file_sizes,
                    "chunked_generation": patient_count > 1000,
                    "metrics_generation_count": generation_count_diff
                }

    async def run_tests(self):
        """Run comprehensive tests."""
        print("🚀 Testing Generation Pipeline Optimizations (Task 2)")
        print("=" * 60)

        # Test configurations
        test_configs = [
            # Small tests (no chunking)
            {"patient_count": 100},
            {"patient_count": 500},
            {"patient_count": 1000},

            # Large tests (with chunking)
            {"patient_count": 2500},
            {"patient_count": 5000},
            {"patient_count": 10000},

            # Very large test
            {"patient_count": 25000},

            # Temporal tests
            {"patient_count": 1000, "use_temporal": True},
            {"patient_count": 5000, "use_temporal": True},

            # Multiple formats
            {"patient_count": 1000, "output_formats": ["json", "csv"]},
            {"patient_count": 1000, "output_formats": ["json", "xml", "csv"]},
        ]

        for config in test_configs:
            try:
                # Force GC before test
                gc.collect()
                await asyncio.sleep(0.5)

                result = await self.test_generation(**config)
                self.results.append(result)

                # Print result
                if result["success"]:
                    print(f"  ✅ Success in {result['generation_time']:.2f}s")
                    print(f"  🚄 Speed: {result['patients_per_second']:.0f} patients/sec")
                    print(f"  💾 Memory: {result['memory_before_mb']:.0f} → "
                          f"{result['memory_peak_mb']:.0f} MB (peak)")
                    print(f"  📊 Memory per patient: {result['memory_per_patient_mb']:.3f} MB")

                    if result["chunked_generation"]:
                        print("  📦 Used chunked generation")

                    for fmt, size in result["file_sizes_mb"].items():
                        print(f"  📄 {fmt}: {size:.1f} MB")
                else:
                    print(f"  ❌ Failed: {result['error']}")

            except Exception as e:
                print(f"  ❌ Error: {e}")

        # Print summary
        self._print_summary()

    def _print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📈 OPTIMIZATION TEST SUMMARY")
        print("=" * 60)

        successful = [r for r in self.results if r["success"]]

        if not successful:
            print("❌ No successful tests")
            return

        # Chunking analysis
        print("\n🔍 Chunking Effectiveness:")
        chunked = [r for r in successful if r["chunked_generation"]]
        non_chunked = [r for r in successful if not r["chunked_generation"]]

        if chunked:
            avg_memory_per_patient_chunked = sum(r["memory_per_patient_mb"] for r in chunked) / len(chunked)
            max_patients_chunked = max(r["patient_count"] for r in chunked)
            print(f"  ✅ Chunked generation handled up to {max_patients_chunked:,} patients")
            print(f"  ✅ Average memory per patient: {avg_memory_per_patient_chunked:.3f} MB")

        if non_chunked:
            avg_memory_per_patient_non_chunked = sum(r["memory_per_patient_mb"] for r in non_chunked) / len(non_chunked)
            print(f"  ✅ Non-chunked average memory per patient: {avg_memory_per_patient_non_chunked:.3f} MB")

        if chunked and non_chunked:
            improvement = (1 - avg_memory_per_patient_chunked / avg_memory_per_patient_non_chunked) * 100
            print(f"  ✅ Memory efficiency improvement: {improvement:.0f}%")

        # Speed analysis
        print("\n🚄 Generation Speed:")
        speed_by_size = {}
        for r in successful:
            size = r["patient_count"]
            if size not in speed_by_size:
                speed_by_size[size] = []
            speed_by_size[size].append(r["patients_per_second"])

        for size in sorted(speed_by_size.keys()):
            speeds = speed_by_size[size]
            avg_speed = sum(speeds) / len(speeds)
            print(f"  {size:>6} patients: {avg_speed:>6.0f} patients/sec")

        # Memory scaling
        print("\n💾 Memory Scaling:")
        print(f"  {'Size':<10} {'Peak MB':<10} {'MB/Patient':<12} {'Chunked':<8}")
        print("  " + "-" * 45)

        for r in sorted(successful, key=lambda x: x["patient_count"]):
            print(f"  {r['patient_count']:<10} {r['memory_peak_mb']:<10.0f} "
                  f"{r['memory_per_patient_mb']:<12.3f} "
                  f"{'Yes' if r['chunked_generation'] else 'No':<8}")

        # Key achievements
        print("\n🎯 Key Achievements:")
        max_patients = max(r["patient_count"] for r in successful)
        print(f"  ✅ Successfully generated {max_patients:,} patients")

        avg_speed = sum(r["patients_per_second"] for r in successful) / len(successful)
        print(f"  ✅ Average generation speed: {avg_speed:.0f} patients/sec")

        # Save results
        results_file = Path("generation_metrics_results.json")
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Results saved to: {results_file}")


async def main():
    """Run metrics tests."""
    tester = GenerationMetricsTester()
    await tester.run_tests()


if __name__ == "__main__":
    asyncio.run(main())
