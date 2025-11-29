"""
Simple Performance Metrics for Medical Patients Generator
========================================================

Minimal overhead performance monitoring with CLI-friendly output.
Designed for identifying bottlenecks in patient generation pipeline.
"""

from contextlib import contextmanager
from dataclasses import dataclass
import threading
import time
from typing import Dict, Optional

import psutil


@dataclass
class PhaseMetrics:
    """Metrics for a single phase of execution."""

    name: str
    start_time: float = 0.0
    end_time: float = 0.0
    start_memory: int = 0
    peak_memory: int = 0
    end_memory: int = 0
    patient_count: int = 0
    thread_count: int = 0
    cpu_percent: Optional[float] = None

    @property
    def duration(self) -> float:
        """Total duration in seconds."""
        return self.end_time - self.start_time if self.end_time > self.start_time else 0.0

    @property
    def patients_per_second(self) -> float:
        """Throughput rate."""
        return self.patient_count / self.duration if self.duration > 0 else 0.0

    @property
    def memory_delta_mb(self) -> float:
        """Memory change in MB."""
        return (self.end_memory - self.start_memory) / (1024 * 1024)

    @property
    def peak_memory_mb(self) -> float:
        """Peak memory usage in MB."""
        return self.peak_memory / (1024 * 1024)


class PerformanceMonitor:
    """
    Ultra-simple performance monitor for patient generator.

    Usage:
        monitor = PerformanceMonitor()
        with monitor.time_phase("patient_generation", patient_count=1000):
            # ... generate patients ...

        monitor.report()  # Print CLI-friendly report
    """

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.metrics: Dict[str, PhaseMetrics] = {}
        self.process = psutil.Process()
        self.overall_start_time = time.time()
        self.overall_start_memory = self.process.memory_info().rss

    @contextmanager
    def time_phase(self, phase_name: str, patient_count: int = 0):
        """Context manager to time a phase of execution."""
        if not self.enabled:
            yield
            return

        phase = PhaseMetrics(
            name=phase_name,
            start_time=time.time(),
            start_memory=self.process.memory_info().rss,
            patient_count=patient_count,
            thread_count=threading.active_count(),
        )

        # Track CPU at start
        try:
            phase.cpu_percent = self.process.cpu_percent()
        except Exception:
            phase.cpu_percent = None

        self.metrics[phase_name] = phase

        try:
            yield phase
        finally:
            phase.end_time = time.time()
            phase.end_memory = self.process.memory_info().rss

            # Update peak memory if we can
            try:
                current_memory = self.process.memory_info().rss
                phase.peak_memory = max(phase.start_memory, current_memory, phase.end_memory)
            except Exception:
                phase.peak_memory = phase.end_memory

    def update_patient_count(self, phase_name: str, count: int):
        """Update patient count for a phase (useful for dynamic counting)."""
        if phase_name in self.metrics:
            self.metrics[phase_name].patient_count = count

    def report(self) -> str:
        """Generate CLI-friendly performance report."""
        if not self.enabled or not self.metrics:
            return "Performance monitoring disabled or no metrics collected."

        overall_time = time.time() - self.overall_start_time
        overall_memory_delta = (self.process.memory_info().rss - self.overall_start_memory) / (1024 * 1024)

        lines = [
            "\n" + "=" * 80,
            "PERFORMANCE METRICS REPORT",
            "=" * 80,
            f"Overall Runtime: {overall_time:.2f}s | Memory Delta: {overall_memory_delta:+.1f}MB",
            "-" * 80,
        ]

        # Phase breakdown
        lines.append(f"{'Phase':<20} {'Time(s)':<10} {'Rate(p/s)':<12} {'Memory(MB)':<12} {'Threads':<8}")
        lines.append("-" * 80)

        total_patients = 0
        for phase in self.metrics.values():
            total_patients += phase.patient_count

            lines.append(
                f"{phase.name:<20} "
                f"{phase.duration:<10.2f} "
                f"{phase.patients_per_second:<12.1f} "
                f"{phase.memory_delta_mb:+<12.1f} "
                f"{phase.thread_count:<8}"
            )

        # Summary statistics
        lines.extend(
            [
                "-" * 80,
                f"Total Patients: {total_patients}",
                f"Overall Rate: {total_patients / overall_time:.1f} patients/second"
                if overall_time > 0
                else "Overall Rate: N/A",
                f"Peak Memory: {max(p.peak_memory_mb for p in self.metrics.values()):.1f}MB"
                if self.metrics
                else "Peak Memory: N/A",
                "=" * 80,
            ]
        )

        report_text = "\n".join(lines)
        print(report_text)
        return report_text

    def get_bottleneck_analysis(self) -> str:
        """Simple bottleneck identification."""
        if not self.metrics:
            return "No metrics to analyze."

        # Find slowest phase
        slowest_phase = max(self.metrics.values(), key=lambda p: p.duration)

        # Find memory hog
        memory_hog = max(self.metrics.values(), key=lambda p: abs(p.memory_delta_mb))

        # Find inefficient phase (low throughput)
        inefficient_phases = [p for p in self.metrics.values() if p.patient_count > 0 and p.patients_per_second < 10]

        analysis = [
            "\nBOTTLENECK ANALYSIS:",
            f"• Slowest Phase: {slowest_phase.name} ({slowest_phase.duration:.2f}s)",
            f"• Memory Impact: {memory_hog.name} ({memory_hog.memory_delta_mb:+.1f}MB)",
        ]

        if inefficient_phases:
            analysis.append(f"• Low Throughput: {', '.join(p.name for p in inefficient_phases)}")
        else:
            analysis.append("• Throughput: All phases performing well")

        return "\n".join(analysis)


# Global instance for easy CLI usage
_global_monitor: Optional[PerformanceMonitor] = None


def get_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor(enabled=False)  # Disabled by default
    return _global_monitor


def enable_monitoring():
    """Enable performance monitoring globally."""
    global _global_monitor
    _global_monitor = PerformanceMonitor(enabled=True)


def disable_monitoring():
    """Disable performance monitoring globally."""
    global _global_monitor
    if _global_monitor:
        _global_monitor.enabled = False
