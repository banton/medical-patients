"""
Test memory efficiency of optimized Patient class.
Part of EPIC-003: Production Scalability Improvements - Phase 3
"""

import datetime
import sys
from typing import List

from patient_generator.patient import Patient
from patient_generator.patient_optimized import OptimizedPatient, migrate_patient


class TestPatientMemoryOptimization:
    """Test memory optimization of Patient class."""

    def test_patient_size_comparison(self):
        """Compare memory size of regular vs optimized patient."""
        # Create regular patient
        regular = Patient(patient_id=1)
        regular.set_demographics(
            {
                "first_name": "John",
                "last_name": "Doe",
                "birthdate": "1990-01-01",
                "gender": "male",
                "nationality": "USA",
                "blood_type": "O+",
            }
        )
        regular.injury_type = "BATTLE_TRAUMA"
        regular.triage_category = "T2"
        regular.nationality = "USA"
        regular.front = "North"
        regular.gender = "male"
        regular.injury_timestamp = datetime.datetime.now()

        # Add timeline events
        for i in range(5):
            regular.add_timeline_event(
                "arrival",
                f"Facility_{i}",
                datetime.datetime.now() + datetime.timedelta(hours=i),
            )

        # Create optimized patient
        optimized = OptimizedPatient(id=1)
        optimized.set_demographics(
            {
                "first_name": "John",
                "last_name": "Doe",
                "birthdate": "1990-01-01",
                "gender": "male",
                "nationality": "USA",
                "blood_type": "O+",
            }
        )
        optimized.injury_type = "BATTLE_TRAUMA"
        optimized.triage_category = "T2"
        optimized.nationality = "USA"
        optimized.front = "North"
        optimized.gender = "male"
        optimized.injury_timestamp = datetime.datetime.now().timestamp()

        # Add timeline events
        for i in range(5):
            optimized.add_timeline_event(
                "arrival",
                f"Facility_{i}",
                datetime.datetime.now() + datetime.timedelta(hours=i),
            )

        # Compare sizes
        regular_size = sys.getsizeof(regular.__dict__)
        optimized_size = sys.getsizeof(optimized)

        # Print comparison
        print("\nMemory comparison:")
        print(f"  Regular patient dict size: {regular_size} bytes")
        print(f"  Optimized patient size: {optimized_size} bytes")
        print(
            f"  Savings: {regular_size - optimized_size} bytes ({(regular_size - optimized_size) / regular_size * 100:.1f}%)"
        )

        # Optimized should be smaller
        assert optimized_size < regular_size

    def test_patient_migration(self):
        """Test migration from regular to optimized patient."""
        # Create regular patient with full data
        regular = Patient(patient_id=42)
        regular.set_demographics(
            {
                "first_name": "Jane",
                "last_name": "Smith",
                "birthdate": "1985-05-15",
                "gender": "female",
                "nationality": "GBR",
                "blood_type": "A+",
            }
        )
        regular.injury_type = "DISEASE"
        regular.triage_category = "T3"
        regular.nationality = "GBR"
        regular.front = "South"
        regular.gender = "female"
        regular.final_status = "RTD"
        regular.last_facility = "Role4_Hospital"
        regular.warfare_scenario = "urban_combat"
        regular.casualty_event_id = "event_123"
        regular.is_mass_casualty = True
        regular.injury_timestamp = datetime.datetime.now()
        regular.environmental_conditions = ["night_operations", "urban_combat"]
        regular.primary_condition = {"code": "TRAUMA_001", "description": "Blast injury"}

        # Add timeline
        base_time = datetime.datetime.now()
        regular.add_timeline_event("injury", "POI", base_time)
        regular.add_timeline_event("arrival", "Role1", base_time + datetime.timedelta(minutes=30))
        regular.add_timeline_event("arrival", "Role2", base_time + datetime.timedelta(hours=2))
        regular.add_timeline_event("rtd", "Role4", base_time + datetime.timedelta(hours=24))

        # Migrate to optimized
        optimized = migrate_patient(regular)

        # Verify all data migrated correctly
        assert optimized.id == regular.id
        assert optimized.injury_type == regular.injury_type
        assert optimized.triage_category == regular.triage_category
        assert optimized.nationality == regular.nationality
        assert optimized.front == regular.front
        assert optimized.gender == regular.gender
        assert optimized.final_status == regular.final_status
        assert optimized.last_facility == regular.last_facility
        assert optimized.warfare_scenario == regular.warfare_scenario
        assert optimized.casualty_event_id == regular.casualty_event_id
        assert optimized.is_mass_casualty == regular.is_mass_casualty
        assert optimized.primary_condition_code == "TRAUMA_001"

        # Check demographics
        demographics = optimized.demographics
        assert demographics["first_name"] == "Jane"
        assert demographics["last_name"] == "Smith"
        assert demographics["birthdate"] == "1985-05-15"
        assert demographics["gender"] == "female"

        # Check age calculation
        assert optimized.get_age() == regular.get_age()

        # Check environmental conditions
        assert set(optimized.get_environmental_conditions()) == {"night_operations", "urban_combat"}

        # Check timeline
        assert len(optimized.movement_events) == len(regular.movement_timeline)

    def test_to_dict_conversion(self):
        """Test conversion to dictionary for JSON serialization."""
        # Create optimized patient
        patient = OptimizedPatient(id=100)
        patient.set_demographics(
            {
                "first_name": "Test",
                "last_name": "Patient",
                "birthdate": "2000-01-01",
                "gender": "male",
                "nationality": "USA",
                "blood_type": "B+",
            }
        )
        patient.injury_type = "NON_BATTLE"
        patient.triage_category = "T1"
        patient.nationality = "USA"
        patient.front = "East"
        patient.gender = "male"
        patient.primary_condition_code = "DISEASE_001"
        patient.set_environmental_condition("desert_conditions", True)
        patient.set_environmental_condition("extreme_weather", True)

        # Add timeline
        base_time = datetime.datetime(2025, 1, 1, 12, 0)
        patient.injury_timestamp = base_time.timestamp()
        patient.add_timeline_event("injury", "POI", base_time)
        patient.add_timeline_event("arrival", "Role1", base_time + datetime.timedelta(hours=1))

        # Convert to dict
        patient_dict = patient.to_dict()

        # Verify structure
        assert patient_dict["id"] == 100
        assert patient_dict["injury_type"] == "NON_BATTLE"
        assert patient_dict["triage_category"] == "T1"
        assert patient_dict["demographics"]["first_name"] == "Test"
        assert patient_dict["demographics"]["last_name"] == "Patient"
        assert patient_dict["primary_condition"]["code"] == "DISEASE_001"
        assert set(patient_dict["environmental_conditions"]) == {"desert_conditions", "extreme_weather"}
        assert len(patient_dict["movement_timeline"]) == 2
        assert patient_dict["movement_timeline"][0]["event_type"] == "injury"
        assert patient_dict["movement_timeline"][0]["facility"] == "POI"
        assert "injury_timestamp" in patient_dict
        assert "age" in patient_dict

    def test_memory_efficiency_at_scale(self):
        """Test memory efficiency with many patients."""
        patient_count = 1000

        # Create many regular patients
        regular_patients: List[Patient] = []
        for i in range(patient_count):
            patient = Patient(patient_id=i)
            patient.set_demographics(
                {
                    "first_name": f"Patient{i}",
                    "last_name": "Test",
                    "birthdate": "1990-01-01",
                    "gender": "male" if i % 2 == 0 else "female",
                    "nationality": "USA",
                    "blood_type": "O+",
                }
            )
            patient.injury_type = "BATTLE_TRAUMA"
            patient.triage_category = f"T{(i % 3) + 1}"
            regular_patients.append(patient)

        # Create many optimized patients
        optimized_patients: List[OptimizedPatient] = []
        for i in range(patient_count):
            patient = OptimizedPatient(id=i)
            patient.set_demographics(
                {
                    "first_name": f"Patient{i}",
                    "last_name": "Test",
                    "birthdate": "1990-01-01",
                    "gender": "male" if i % 2 == 0 else "female",
                    "nationality": "USA",
                    "blood_type": "O+",
                }
            )
            patient.injury_type = "BATTLE_TRAUMA"
            patient.triage_category = f"T{(i % 3) + 1}"
            optimized_patients.append(patient)

        # Calculate total memory (approximate)
        regular_total = sum(sys.getsizeof(p.__dict__) for p in regular_patients)
        optimized_total = sum(sys.getsizeof(p) for p in optimized_patients)

        print(f"\nMemory usage for {patient_count} patients:")
        print(f"  Regular patients: {regular_total / 1024:.1f} KB")
        print(f"  Optimized patients: {optimized_total / 1024:.1f} KB")
        print(
            f"  Savings: {(regular_total - optimized_total) / 1024:.1f} KB ({(regular_total - optimized_total) / regular_total * 100:.1f}%)"
        )

        # Optimized should use significantly less memory
        # Note: Memory behavior can vary across Python versions and platforms
        # Ubuntu 24.04 with Python 3.12 may have different allocation patterns
        assert optimized_total < regular_total * 0.8  # At least 20% savings
