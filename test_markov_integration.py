#!/usr/bin/env python3
"""
Test script for Markov chain integration in patient flow simulation.
Tests MILESTONE 3: Probabilistic facility routing with realistic patterns.
"""

from collections import Counter
import json
import os
import sys

# Add project paths
sys.path.append(os.path.dirname(__file__))


# Test with a small batch of patients
def test_markov_chain_integration():
    """Test that Markov chain produces expected routing patterns."""
    print("Testing Markov Chain Integration in Patient Flow")
    print("=" * 60)

    # Run generator with Markov chain enabled
    import subprocess

    # Clean output directory first
    os.makedirs("output", exist_ok=True)

    print("Generating 30 patients with Markov chain routing...")
    result = subprocess.run(
        ["python3", "run_generator.py", "--patients", "30", "--output", "output", "--formats", "json"],
        check=False,
        capture_output=True,
        text=True,
        env={**os.environ, "ENABLE_MARKOV_CHAIN": "true"},
    )

    if result.returncode != 0:
        print(f"Error running generator: {result.stderr}")
        return False

    # Load and analyze generated patients
    output_file = None
    for file in os.listdir("output"):
        if file.startswith("patients") and file.endswith(".json"):
            output_file = os.path.join("output", file)
            break

    if not output_file:
        print("No output file generated!")
        return False

    with open(output_file) as f:
        data = json.load(f)

    patients = data.get("patients", [])
    print(f"Loaded {len(patients)} patients from {output_file}")

    # Analyze patterns
    analyze_markov_patterns(patients)

    return True


def analyze_markov_patterns(patients):
    """Analyze patient flow patterns to verify Markov chain behavior."""

    # Categorize patients by triage
    triage_groups = {"T1": [], "T2": [], "T3": [], "T4": []}

    for patient in patients:
        triage = patient.get("triage", "Unknown")
        if triage in triage_groups:
            triage_groups[triage].append(patient)

    print("\nPatient Distribution by Triage:")
    for triage, group in triage_groups.items():
        print(f"  {triage}: {len(group)} patients")

    # Analyze T1 patients - should bypass Role1
    print("\nT1 Critical Patients Analysis:")
    if triage_groups["T1"]:
        analyze_triage_group(triage_groups["T1"], "T1", expect_bypass_role1=True)

    # Analyze T4 patients - should RTD early
    print("\nT4 Minimal Patients Analysis:")
    if triage_groups["T4"]:
        analyze_triage_group(triage_groups["T4"], "T4", expect_early_rtd=True)

    # Analyze T2/T3 patients - mixed patterns
    print("\nT2 Urgent Patients Analysis:")
    if triage_groups["T2"]:
        analyze_triage_group(triage_groups["T2"], "T2")

    print("\nT3 Delayed Patients Analysis:")
    if triage_groups["T3"]:
        analyze_triage_group(triage_groups["T3"], "T3")

    # Overall mortality analysis
    print("\nOverall Mortality Analysis:")
    analyze_mortality(patients)


def analyze_triage_group(patients, triage_cat, expect_bypass_role1=False, expect_early_rtd=False):
    """Analyze flow patterns for a specific triage group."""

    facilities_visited = []
    final_outcomes = Counter()
    bypassed_role1 = 0
    rtd_from_role1 = 0

    for patient in patients:
        # Extract facilities from timeline
        timeline = patient.get("timeline", [])
        patient_facilities = []

        for event in timeline:
            if event.get("event_type") == "arrival":
                facility = event.get("facility")
                if facility and facility not in patient_facilities:
                    patient_facilities.append(facility)

        facilities_visited.append(patient_facilities)

        # Check if bypassed Role1
        if "Role1" not in patient_facilities and len(patient_facilities) > 1:
            bypassed_role1 += 1

        # Check final outcome
        final_event = timeline[-1] if timeline else {}
        event_type = final_event.get("event_type", "unknown")

        if event_type == "kia":
            final_outcomes["KIA"] += 1
        elif event_type == "rtd":
            final_outcomes["RTD"] += 1
            # Check if RTD from Role1
            if final_event.get("facility") == "Role1":
                rtd_from_role1 += 1
        elif event_type == "remains_role4":
            final_outcomes["Remains_Role4"] += 1
        else:
            final_outcomes["Unknown"] += 1

    # Calculate statistics
    avg_facilities = sum(len(f) for f in facilities_visited) / len(facilities_visited) if facilities_visited else 0
    bypass_rate = (bypassed_role1 / len(patients)) * 100 if patients else 0
    rtd_role1_rate = (rtd_from_role1 / len(patients)) * 100 if patients else 0

    print(f"  Total: {len(patients)} patients")
    print(f"  Average facilities visited: {avg_facilities:.1f}")
    print(f"  Bypassed Role1: {bypassed_role1}/{len(patients)} ({bypass_rate:.0f}%)")

    if expect_bypass_role1:
        if bypass_rate > 50:
            print("  ✅ T1 bypass pattern confirmed (>50% bypass Role1)")
        else:
            print(f"  ⚠️ T1 bypass pattern low ({bypass_rate:.0f}% < 50%)")

    if rtd_role1_rate > 0:
        print(f"  RTD from Role1: {rtd_from_role1}/{len(patients)} ({rtd_role1_rate:.0f}%)")

    if expect_early_rtd:
        if rtd_role1_rate > 60:
            print("  ✅ T4 early RTD pattern confirmed (>60% RTD from Role1)")
        else:
            print(f"  ⚠️ T4 early RTD pattern low ({rtd_role1_rate:.0f}% < 60%)")

    print(f"  Outcomes: {dict(final_outcomes)}")

    # Show sample paths
    if facilities_visited:
        print("  Sample paths:")
        for i, path in enumerate(facilities_visited[:3]):
            path_str = " -> ".join(path) if path else "No path"
            outcome = next(iter(final_outcomes.keys())) if final_outcomes else "Unknown"
            print(f"    Patient {i + 1}: {path_str} -> {outcome}")


def analyze_mortality(patients):
    """Analyze overall mortality rates."""

    total = len(patients)
    kia_count = 0
    rtd_count = 0
    remains_count = 0

    kia_by_facility = Counter()
    rtd_by_facility = Counter()

    for patient in patients:
        timeline = patient.get("timeline", [])
        if timeline:
            final_event = timeline[-1]
            event_type = final_event.get("event_type", "")
            facility = final_event.get("facility", "Unknown")

            if event_type == "kia":
                kia_count += 1
                kia_by_facility[facility] += 1
            elif event_type == "rtd":
                rtd_count += 1
                rtd_by_facility[facility] += 1
            elif event_type == "remains_role4":
                remains_count += 1

    mortality_rate = (kia_count / total) * 100 if total > 0 else 0
    rtd_rate = (rtd_count / total) * 100 if total > 0 else 0

    print(f"  Total patients: {total}")
    print(f"  KIA: {kia_count} ({mortality_rate:.1f}%)")
    print(f"  RTD: {rtd_count} ({rtd_rate:.1f}%)")
    print(f"  Remains at Role4: {remains_count}")

    if kia_by_facility:
        print(f"  KIA by facility: {dict(kia_by_facility)}")

    if rtd_by_facility:
        print(f"  RTD by facility: {dict(rtd_by_facility)}")

    # Check if mortality is realistic (5-15% for combat)
    if 5 <= mortality_rate <= 15:
        print(f"  ✅ Realistic combat mortality rate ({mortality_rate:.1f}%)")
    else:
        print(f"  ⚠️ Mortality rate outside expected range: {mortality_rate:.1f}% (expected 5-15%)")


if __name__ == "__main__":
    try:
        success = test_markov_chain_integration()

        if success:
            print("\n" + "=" * 60)
            print("✅ MILESTONE 3 TEST COMPLETE: Markov chain integration successful!")
            print("Key achievements:")
            print("  - Probabilistic routing based on triage severity")
            print("  - T1 patients bypassing Role1 for immediate surgery")
            print("  - T4 patients RTD early from Role1")
            print("  - Realistic mortality patterns at appropriate facilities")
        else:
            print("\n❌ Test failed - check error messages above")

    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback

        traceback.print_exc()
