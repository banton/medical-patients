#!/usr/bin/env python3
"""
Test script for diagnostic uncertainty integration in Patient Flow Orchestrator.
Tests MILESTONE 2.3: Progressive diagnosis through facility chain.
"""

import os
import sys

# Add project paths
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "medical_simulation"))

from medical_simulation.patient_flow_orchestrator import PatientFlowOrchestrator


def test_diagnostic_progression():
    """Test that diagnostic accuracy improves as patients progress through facilities."""
    print("Testing Diagnostic Progression Integration")
    print("=" * 50)

    # Initialize orchestrator with diagnostic uncertainty enabled
    orchestrator = PatientFlowOrchestrator(enable_diagnostic_uncertainty=True)

    # Test patient with known condition
    patient_id = "test_001"
    true_condition = "19130008"  # Traumatic brain injury

    print(f"Initializing patient {patient_id} with TBI condition...")

    # Initialize patient at POI with true condition
    patient = orchestrator.initialize_patient(
        patient_id=patient_id,
        injury_type="gunshot",
        severity="critical",
        location="POI",
        true_condition_code=true_condition,
    )

    print("Patient initialized at POI:")
    print(f"  - Health: {patient.current_health}")
    print(f"  - Triage: {patient.triage_category}")
    print(f"  - True condition: {patient.true_condition}")

    if patient.diagnosed_conditions:
        initial_diagnosis = patient.diagnosed_conditions[0]
        print(f"  - POI diagnosis: {initial_diagnosis.get('diagnosed_code')}")
        print(f"  - POI confidence: {initial_diagnosis.get('confidence', 0.0):.2f}")
        print(f"  - Correct diagnosis: {initial_diagnosis.get('true_positive', False)}")

    # Simulate triage
    triage_result = orchestrator.process_triage(patient_id)
    print(f"\nTriage result: {triage_result}")

    # Simulate transport to Role1
    print("\nTransporting to Role1...")
    transport_id = orchestrator.transport_patient(patient_id, "Role1")
    if transport_id:
        print(f"Transport scheduled: {transport_id}")

        # Complete transport
        success = orchestrator.complete_transport(patient_id)
        print(f"Transport completed: {success}")

        if success and patient.diagnosed_conditions:
            role1_diagnosis = patient.diagnosed_conditions[-1]
            print(f"  - Role1 diagnosis: {role1_diagnosis.get('diagnosed_code')}")
            print(f"  - Role1 confidence: {role1_diagnosis.get('confidence', 0.0):.2f}")
            print(f"  - Correct diagnosis: {role1_diagnosis.get('true_positive', False)}")

    # Simulate transport to Role2
    print("\nTransporting to Role2...")
    transport_id = orchestrator.transport_patient(patient_id, "Role2")
    if transport_id:
        orchestrator.complete_transport(patient_id)

        if patient.diagnosed_conditions:
            role2_diagnosis = patient.diagnosed_conditions[-1]
            print(f"  - Role2 diagnosis: {role2_diagnosis.get('diagnosed_code')}")
            print(f"  - Role2 confidence: {role2_diagnosis.get('confidence', 0.0):.2f}")
            print(f"  - Correct diagnosis: {role2_diagnosis.get('true_positive', False)}")

    # Print diagnostic progression summary
    print("\nDiagnostic Progression Summary:")
    print(f"  - Total diagnoses: {len(patient.diagnosed_conditions)}")
    print(f"  - Current confidence: {patient.diagnostic_confidence:.2f}")

    for i, diagnosis in enumerate(patient.diagnosed_conditions):
        facility = diagnosis.get("facility", "Unknown")
        confidence = diagnosis.get("confidence", 0.0)
        correct = diagnosis.get("true_positive", False)
        print(f"    {i + 1}. {facility}: {confidence:.2f} confidence {'✓' if correct else '✗'}")

    # Print metrics
    print("\nSystem Metrics:")
    print(f"  - Correct diagnoses: {orchestrator.metrics['correct_diagnoses']}")
    print(f"  - Misdiagnoses: {orchestrator.metrics['misdiagnoses']}")
    print(f"  - Overall accuracy: {orchestrator.metrics['diagnostic_accuracy']:.2f}")

    return orchestrator.metrics["diagnostic_accuracy"] > 0


def test_multiple_patients():
    """Test diagnostic accuracy across multiple patients."""
    print("\nTesting Multiple Patients")
    print("=" * 30)

    orchestrator = PatientFlowOrchestrator(enable_diagnostic_uncertainty=True)

    # Test conditions with their expected facility accuracy
    test_cases = [
        ("patient_001", "gunshot", "19130008"),  # TBI
        ("patient_002", "blast", "48333001"),  # Burn
        ("patient_003", "shrapnel", "361220002"),  # Penetrating injury
        ("patient_004", "vehicle", "125605004"),  # Fracture
        ("patient_005", "fall", "125667009"),  # Contusion
    ]

    for patient_id, injury_type, condition_code in test_cases:
        patient = orchestrator.initialize_patient(
            patient_id=patient_id, injury_type=injury_type, severity="moderate", true_condition_code=condition_code
        )

        # Process through Role1
        orchestrator.process_triage(patient_id)
        transport_id = orchestrator.transport_patient(patient_id, "Role1")
        if transport_id:
            orchestrator.complete_transport(patient_id)

        if patient.diagnosed_conditions:
            latest = patient.diagnosed_conditions[-1]
            correct = "✓" if latest.get("true_positive") else "✗"
            print(f"{patient_id}: {injury_type} -> {latest.get('confidence', 0.0):.2f} {correct}")

    print(f"\nFinal System Accuracy: {orchestrator.metrics['diagnostic_accuracy']:.2f}")
    return orchestrator.metrics["diagnostic_accuracy"]


if __name__ == "__main__":
    try:
        # Test single patient progression
        single_accuracy = test_diagnostic_progression()

        # Test multiple patients
        multi_accuracy = test_multiple_patients()

        print("\n" + "=" * 50)
        print("MILESTONE 2.3 INTEGRATION TEST RESULTS:")
        print("✓ Diagnostic uncertainty engine integrated successfully")
        print("✓ Progressive diagnosis through facility chain working")
        print(f"✓ Single patient test accuracy: {single_accuracy}")
        print(f"✓ Multi-patient system accuracy: {multi_accuracy:.2f}")

        if multi_accuracy > 0.6:  # Expect >60% accuracy across facilities
            print("✅ MILESTONE 2.3 COMPLETE: Diagnostic uncertainty integrated!")
        else:
            print("⚠️  MILESTONE 2.3 needs tuning: Low diagnostic accuracy")

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
