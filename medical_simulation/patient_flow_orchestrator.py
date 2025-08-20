"""
Patient Flow Orchestrator - Agent 3: Integration Coordinator
Main integration module that connects all medical simulation components.
Coordinates patient movement from POI through the entire medical system.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from medical_simulation.csu_batch_coordinator import CSUBatchCoordinator
from medical_simulation.death_tracker import DeathTracker
from medical_simulation.deterioration_calculator import DeteriorationCalculator
from medical_simulation.facility_capacity_manager import FacilityCapacityManager
from medical_simulation.health_score_engine import HealthScoreEngine
from medical_simulation.overflow_router import OverflowRouter
from medical_simulation.transport_scheduler import TransportScheduler
from medical_simulation.treatment_modifiers import TreatmentModifiers
from medical_simulation.triage_mapper import TriageMapper


class PatientState(Enum):
    """Patient states in the medical system."""
    AT_POI = "at_poi"
    IN_TRIAGE = "in_triage"
    IN_TREATMENT = "in_treatment"
    IN_TRANSPORT = "in_transport"
    IN_QUEUE = "in_queue"
    TRANSFERRED = "transferred"
    EVACUATED = "evacuated"
    DIED = "died"
    DISCHARGED = "discharged"


@dataclass
class Patient:
    """Patient with full medical and location tracking."""
    id: str
    injury_type: str
    initial_health: int
    current_health: int
    triage_category: str
    state: PatientState
    current_location: str
    destination: Optional[str] = None
    transport_id: Optional[str] = None
    treatments_received: List[Dict] = None
    timeline: List[Dict] = None
    died_at: Optional[datetime] = None

    def __post_init__(self):
        if self.treatments_received is None:
            self.treatments_received = []
        if self.timeline is None:
            self.timeline = []


class PatientFlowOrchestrator:
    """
    Orchestrates patient flow through the entire medical system.
    Integrates all Agent 1 and Agent 2 modules for complete simulation.
    """

    def __init__(self):
        # Agent 1: Medical Core modules
        self.health_engine = HealthScoreEngine()
        self.deterioration_calc = DeteriorationCalculator()
        self.treatment_mods = TreatmentModifiers()
        self.triage_mapper = TriageMapper()
        self.death_tracker = DeathTracker()

        # Agent 2: Facility & Logistics modules
        self.facility_manager = FacilityCapacityManager()
        self.overflow_router = OverflowRouter(self.facility_manager)
        self.csu_coordinator = CSUBatchCoordinator(self.facility_manager)
        self.transport_scheduler = TransportScheduler()

        # Patient tracking
        self.patients: Dict[str, Patient] = {}
        self.simulation_time = datetime.now()

        # Metrics
        self.metrics = {
            "total_patients": 0,
            "patients_treated": 0,
            "patients_died": 0,
            "patients_evacuated": 0,
            "average_time_to_treatment": 0,
            "facility_overflow_events": 0,
            "csu_batches_processed": 0,
            "transport_missions": 0
        }

    def initialize_patient(self, patient_id: str, injury_type: str,
                          severity: str, location: str = "POI") -> Patient:
        """
        Initialize a new patient entering the medical system.

        Args:
            patient_id: Unique patient identifier
            injury_type: Type of injury (gunshot, blast, etc.)
            severity: Injury severity (critical, moderate, minor)
            location: Initial location (default POI)

        Returns:
            Initialized Patient object
        """
        # Calculate initial health score
        initial_health = self.health_engine.get_initial_health(
            injury_type, severity
        )

        # Determine triage category
        triage_result = self.triage_mapper.calculate_triage_category(
            initial_health, severity
        )
        triage_category = triage_result[0]  # Get category from tuple

        # Create patient
        patient = Patient(
            id=patient_id,
            injury_type=injury_type,
            initial_health=initial_health,
            current_health=initial_health,
            triage_category=triage_category,
            state=PatientState.AT_POI,
            current_location=location
        )

        # Add to timeline
        patient.timeline.append({
            "timestamp": self.simulation_time,
            "event": "arrived_at_poi",
            "location": location,
            "health": initial_health,
            "triage": triage_category
        })

        # Track patient
        self.patients[patient_id] = patient
        self.metrics["total_patients"] += 1

        return patient

    def process_triage(self, patient_id: str) -> Tuple[str, str]:
        """
        Process patient through triage and determine initial facility.

        Args:
            patient_id: Patient identifier

        Returns:
            Tuple of (triage_category, assigned_facility)
        """
        patient = self.patients.get(patient_id)
        if not patient:
            msg = f"Patient {patient_id} not found"
            raise ValueError(msg)

        # Update state
        patient.state = PatientState.IN_TRIAGE

        # Re-assess triage based on current health
        severity = "critical" if patient.current_health < 30 else "moderate" if patient.current_health < 70 else "minor"
        triage_result = self.triage_mapper.calculate_triage_category(
            patient.current_health, severity
        )
        patient.triage_category = triage_result[0]  # Get category from tuple

        # Determine initial facility based on triage
        facility_map = {
            "T1": "Role2",  # Critical -> Role2 or higher
            "T2": "Role1",  # Urgent -> Role1 can stabilize
            "T3": "Role1",  # Delayed -> Role1 for basic care
            "T4": "Role1"   # Minimal -> Role1 for observation
        }

        initial_facility = facility_map.get(patient.triage_category, "Role1")

        # Check capacity and route if needed
        available_beds = self.facility_manager.get_available_beds(initial_facility)
        if available_beds <= 0:
            initial_facility = self.overflow_router.route_patient(
                patient.triage_category,
                initial_facility
            )

        # Update patient
        patient.destination = initial_facility
        patient.timeline.append({
            "timestamp": self.simulation_time,
            "event": "triaged",
            "triage": patient.triage_category,
            "assigned_to": initial_facility
        })

        return patient.triage_category, initial_facility

    def apply_treatment(self, patient_id: str, treatments: List[Dict]) -> int:
        """
        Apply treatments to patient and update health.

        Args:
            patient_id: Patient identifier
            treatments: List of treatment dictionaries

        Returns:
            Updated health score
        """
        patient = self.patients.get(patient_id)
        if not patient:
            msg = f"Patient {patient_id} not found"
            raise ValueError(msg)

        # Update state
        patient.state = PatientState.IN_TREATMENT

        # Apply treatment modifiers
        treatment_effect = self.treatment_mods.calculate_stacked_effects(treatments)

        # Calculate new health (bound between 0-100)
        new_health = min(100, patient.current_health + treatment_effect)
        new_health = max(0, new_health)

        # Update patient
        patient.current_health = new_health
        patient.treatments_received.extend(treatments)

        # Check for death
        if new_health <= 0:
            self.handle_patient_death(patient_id, "treatment_failed")
        else:
            patient.timeline.append({
                "timestamp": self.simulation_time,
                "event": "treatment_applied",
                "treatments": [t["name"] for t in treatments],
                "health_before": patient.current_health - treatment_effect,
                "health_after": new_health,
                "location": patient.current_location
            })

        return new_health

    def simulate_deterioration(self, patient_id: str, time_minutes: int) -> int:
        """
        Simulate patient deterioration over time.

        Args:
            patient_id: Patient identifier
            time_minutes: Time elapsed in minutes

        Returns:
            Updated health score
        """
        patient = self.patients.get(patient_id)
        if not patient:
            msg = f"Patient {patient_id} not found"
            raise ValueError(msg)

        # Don't deteriorate if dead
        if patient.state == PatientState.DIED:
            return 0

        # Calculate deterioration based on severity
        severity = "critical" if patient.current_health < 30 else "moderate" if patient.current_health < 70 else "minor"
        base_deterioration = self.deterioration_calc.calculate_base_deterioration(
            patient.injury_type,
            severity
        )
        # Scale by time (base is per minute)
        deterioration = base_deterioration * time_minutes

        # Update health
        patient.current_health = max(0, patient.current_health - deterioration)

        # Check for death
        if patient.current_health <= 0:
            self.handle_patient_death(patient_id, "deterioration")

        return patient.current_health

    def transport_patient(self, patient_id: str, destination: str) -> Optional[str]:
        """
        Transport patient to destination facility.

        Args:
            patient_id: Patient identifier
            destination: Target facility

        Returns:
            Transport ID if scheduled, None if no transport available
        """
        patient = self.patients.get(patient_id)
        if not patient:
            msg = f"Patient {patient_id} not found"
            raise ValueError(msg)

        # Schedule transport
        priority = "urgent" if patient.triage_category == "T1" else "routine"
        transport = self.transport_scheduler.schedule_transport(
            patient_id,
            patient.current_location,
            destination,
            priority,
            patient.current_health
        )

        if transport:
            # Update patient
            patient.state = PatientState.IN_TRANSPORT
            patient.destination = destination
            patient.transport_id = transport["transport_id"]

            patient.timeline.append({
                "timestamp": self.simulation_time,
                "event": "transport_started",
                "from": patient.current_location,
                "to": destination,
                "transport_type": transport["vehicle_type"],
                "estimated_time": transport["duration_minutes"]
            })

            self.metrics["transport_missions"] += 1
            return transport["transport_id"]

        return None

    def complete_transport(self, patient_id: str) -> bool:
        """
        Complete patient transport and admit to destination.

        Args:
            patient_id: Patient identifier

        Returns:
            True if successfully admitted, False if died in transit
        """
        patient = self.patients.get(patient_id)
        if not patient or not patient.transport_id:
            return False

        # Complete transport
        result = self.transport_scheduler.complete_transport(patient.transport_id)
        
        # Map the result to expected format
        if not result.get("success", False):
            return False
            
        # Check if died in transit based on outcome
        died_in_transit = result.get("outcome") == "died_in_transit"
        actual_time = result.get("actual_duration", 30)

        if died_in_transit:
            self.handle_patient_death(patient_id, "died_in_transit")
            return False

        # Admit to destination
        admission = self.facility_manager.admit_patient(
            patient_id,
            patient.destination,
            patient.triage_category
        )
        if admission.get("success", True):
            patient.current_location = patient.destination
            patient.state = PatientState.IN_TREATMENT
            patient.destination = None
            patient.transport_id = None

            patient.timeline.append({
                "timestamp": self.simulation_time + timedelta(minutes=actual_time),
                "event": "arrived_at_facility",
                "facility": patient.current_location,
                "transport_time": actual_time
            })

            return True
        # Facility full, find overflow
        new_destination = self.overflow_router.route_patient(
            patient.triage_category,
            patient.destination
        )
        patient.destination = new_destination
        self.metrics["facility_overflow_events"] += 1
        return self.transport_patient(patient_id, new_destination) is not None

    def evacuate_to_csu(self, patient_ids: List[str]) -> bool:
        """
        Evacuate patients to CSU for further treatment.

        Args:
            patient_ids: List of patient IDs to evacuate

        Returns:
            True if batch scheduled for CSU, False otherwise
        """
        # Add patients to CSU batch
        for patient_id in patient_ids:
            patient = self.patients.get(patient_id)
            if patient and patient.state != PatientState.DIED:
                self.csu_coordinator.add_to_batch(patient_id, patient.triage_category)

        # Check if batch ready
        if self.csu_coordinator.is_batch_ready():
            batch = self.csu_coordinator.prepare_batch_transfer()

            # Schedule batch transport
            for patient_data in batch["patients"]:
                patient_id = patient_data["patient_id"]
                patient = self.patients.get(patient_id)
                if patient:
                    patient.state = PatientState.EVACUATED
                    patient.timeline.append({
                        "timestamp": self.simulation_time,
                        "event": "evacuated_to_csu",
                        "batch_id": batch.get("batch_id", "batch-001"),
                        "hold_time": patient_data.get("wait_time", 0)
                    })

            self.metrics["csu_batches_processed"] += 1
            self.metrics["patients_evacuated"] += len(batch["patients"])
            return True

        return False

    def handle_patient_death(self, patient_id: str, cause: str):
        """
        Handle patient death and update tracking.

        Args:
            patient_id: Patient identifier
            cause: Cause of death
        """
        patient = self.patients.get(patient_id)
        if not patient:
            return

        # Update death tracker
        location = patient.current_location
        if patient.state == PatientState.IN_TRANSPORT:
            location = "in_transit"

        self.death_tracker.track_death({
            "patient_id": patient_id,
            "time_of_death": self.simulation_time,
            "location": location,
            "cause": cause,
            "injury_type": patient.injury_type,
            "initial_health": patient.initial_health,
            "final_health": patient.current_health,
            "treatments": patient.treatments_received
        })

        # Update patient
        patient.state = PatientState.DIED
        patient.died_at = self.simulation_time
        patient.current_health = 0

        patient.timeline.append({
            "timestamp": self.simulation_time,
            "event": "died",
            "cause": cause,
            "location": location
        })

        # Update metrics
        self.metrics["patients_died"] += 1

        # Free up facility bed if applicable
        if patient.current_location in ["Role1", "Role2", "Role3", "CSU"]:
            self.facility_manager.discharge_patient(
                patient_id,
                patient.current_location
            )

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.

        Returns:
            Dictionary with complete system status
        """
        return {
            "simulation_time": self.simulation_time.isoformat(),
            "patients": {
                "total": self.metrics["total_patients"],
                "alive": sum(1 for p in self.patients.values()
                           if p.state != PatientState.DIED),
                "died": self.metrics["patients_died"],
                "evacuated": self.metrics["patients_evacuated"],
                "in_treatment": sum(1 for p in self.patients.values()
                                  if p.state == PatientState.IN_TREATMENT),
                "in_transport": sum(1 for p in self.patients.values()
                                  if p.state == PatientState.IN_TRANSPORT)
            },
            "facilities": {"Role1": self.facility_manager.get_occupancy("Role1"),
             "Role2": self.facility_manager.get_occupancy("Role2"),
             "Role3": self.facility_manager.get_occupancy("Role3"),
             "CSU": self.facility_manager.get_occupancy("CSU")},
            "transport": self.transport_scheduler.get_transport_metrics(),
            "csu_batch": self.csu_coordinator.get_batch_hold_info(),
            "death_statistics": self.death_tracker.get_statistics() if hasattr(self.death_tracker, 'get_statistics') else {},
            "metrics": self.metrics
        }

    def advance_time(self, minutes: int):
        """
        Advance simulation time and process time-dependent events.

        Args:
            minutes: Minutes to advance
        """
        self.simulation_time += timedelta(minutes=minutes)

        # Process deterioration for all non-dead patients
        for patient in self.patients.values():
            if patient.state not in [PatientState.DIED, PatientState.EVACUATED]:
                self.simulate_deterioration(patient.id, minutes)

        # CSU batches are managed internally
        # Transport times are managed internally
