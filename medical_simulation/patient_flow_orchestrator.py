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

# Import diagnostic uncertainty engine - handle import gracefully
try:
    import os
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from patient_generator.diagnostic_uncertainty import DiagnosticUncertaintyEngine

    DIAGNOSTIC_UNCERTAINTY_AVAILABLE = True
except ImportError:
    DIAGNOSTIC_UNCERTAINTY_AVAILABLE = False
    DiagnosticUncertaintyEngine = None


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
    severity: str  # Original severity level for deterioration calculation
    initial_health: int
    current_health: int
    triage_category: str
    state: PatientState
    current_location: str
    body_part: Optional[str] = None  # Anatomical location of injury
    destination: Optional[str] = None
    transport_id: Optional[str] = None
    treatments_received: List[Dict] = None
    timeline: List[Dict] = None
    died_at: Optional[datetime] = None

    # Diagnostic uncertainty fields
    true_condition: Optional[str] = None  # True SNOMED condition code
    diagnosed_conditions: List[Dict] = None  # Diagnostic history per facility
    diagnostic_confidence: float = 0.0  # Current diagnostic confidence

    def __post_init__(self):
        if self.treatments_received is None:
            self.treatments_received = []
        if self.timeline is None:
            self.timeline = []
        if self.diagnosed_conditions is None:
            self.diagnosed_conditions = []


class PatientFlowOrchestrator:
    """
    Orchestrates patient flow through the entire medical system.
    Integrates all Agent 1 and Agent 2 modules for complete simulation.
    """

    def __init__(self, enable_diagnostic_uncertainty: bool = True):
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

        # Diagnostic uncertainty engine (MILESTONE 2)
        self.diagnostic_engine = None
        self.diagnostic_uncertainty_enabled = enable_diagnostic_uncertainty and DIAGNOSTIC_UNCERTAINTY_AVAILABLE
        if self.diagnostic_uncertainty_enabled:
            try:
                self.diagnostic_engine = DiagnosticUncertaintyEngine()
                print("Diagnostic uncertainty engine enabled - progressive diagnosis accuracy")
            except Exception as e:
                print(f"Warning: Could not initialize diagnostic uncertainty engine: {e}")
                self.diagnostic_uncertainty_enabled = False

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
            "transport_missions": 0,
            "diagnostic_accuracy": 0.0,
            "correct_diagnoses": 0,
            "misdiagnoses": 0,
        }

    def initialize_patient(
        self,
        patient_id: str,
        injury_type: str,
        severity: str,
        location: str = "POI",
        true_condition_code: Optional[str] = None,
        triage_override: Optional[str] = None,
        body_part: Optional[str] = None,
    ) -> Patient:
        """
        Initialize a new patient entering the medical system.

        Args:
            patient_id: Unique patient identifier
            injury_type: Type of injury (gunshot, blast, etc.)
            severity: Injury severity (critical, moderate, minor)
            location: Initial location (default POI)
            true_condition_code: True SNOMED condition code for diagnostic uncertainty

        Returns:
            Initialized Patient object
        """
        # Calculate initial health score
        initial_health = self.health_engine.get_initial_health(injury_type, severity)

        # Determine triage category
        if triage_override:
            # Use the provided triage category from warfare generation
            triage_category = triage_override
        else:
            # Calculate triage based on health if not provided
            triage_result = self.triage_mapper.calculate_triage_category(initial_health, severity)
            triage_category = triage_result[0]  # Get category from tuple

        # Create patient
        patient = Patient(
            id=patient_id,
            injury_type=injury_type,
            severity=severity,  # Store original severity
            initial_health=initial_health,
            current_health=initial_health,
            triage_category=triage_category,
            state=PatientState.AT_POI,
            current_location=location,
            true_condition=true_condition_code,
        )

        # Track patient FIRST (needed for diagnosis)
        self.patients[patient_id] = patient
        self.metrics["total_patients"] += 1

        # Initialize diagnostic uncertainty if enabled
        if self.diagnostic_uncertainty_enabled and true_condition_code:
            initial_diagnosis = self.perform_diagnosis(patient_id, location, {"triage_category": triage_category})
            patient.diagnosed_conditions.append(initial_diagnosis)
            patient.diagnostic_confidence = initial_diagnosis.get("confidence", 0.0)

        # Add to timeline
        patient.timeline.append(
            {
                "timestamp": self.simulation_time,
                "event": "arrived_at_poi",
                "location": location,
                "health": initial_health,
                "triage": triage_category,
            }
        )
    
        # Set body_part if provided
        if body_part:
            patient.body_part = body_part

        return patient

    def perform_diagnosis(
        self, patient_id: str, facility: str, modifiers: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform diagnosis at the current facility with progressive accuracy.

        Args:
            patient_id: Patient identifier
            facility: Current medical facility
            modifiers: Additional factors affecting diagnostic accuracy

        Returns:
            Diagnosis result with confidence and accuracy metrics
        """
        patient = self.patients.get(patient_id)
        if not patient or not self.diagnostic_uncertainty_enabled:
            return {"diagnosed_code": None, "confidence": 0.0, "facility": facility}

        # Use true condition if available, otherwise use a default based on injury type
        true_condition = patient.true_condition
        if not true_condition:
            # Map injury types to common SNOMED codes for testing
            injury_to_condition_map = {
                "gunshot": "19130008",  # Traumatic brain injury
                "blast": "48333001",  # Burn injury
                "shrapnel": "361220002",  # Penetrating injury
                "vehicle": "125605004",  # Fracture of bone
                "fall": "125667009",  # Contusion
            }
            true_condition = injury_to_condition_map.get(patient.injury_type, "22253000")  # Default to Pain

        # Perform diagnosis using uncertainty engine
        diagnosis_result = self.diagnostic_engine.diagnose_condition(true_condition, facility, patient_id, modifiers)

        # Update metrics
        if diagnosis_result.get("true_positive", False):
            self.metrics["correct_diagnoses"] += 1
        else:
            self.metrics["misdiagnoses"] += 1

        # Calculate running diagnostic accuracy
        total_diagnoses = self.metrics["correct_diagnoses"] + self.metrics["misdiagnoses"]
        if total_diagnoses > 0:
            self.metrics["diagnostic_accuracy"] = self.metrics["correct_diagnoses"] / total_diagnoses

        return diagnosis_result

    def update_diagnosis_on_transfer(self, patient_id: str, new_facility: str) -> Optional[Dict[str, Any]]:
        """
        Update patient diagnosis when transferred to a new facility with better capabilities.

        Args:
            patient_id: Patient identifier
            new_facility: New facility with potentially better diagnostic accuracy

        Returns:
            Updated diagnosis or None if no improvement
        """
        patient = self.patients.get(patient_id)
        if not patient or not self.diagnostic_uncertainty_enabled:
            return None

        # Get current diagnosis
        current_diagnosis_code = None
        if patient.diagnosed_conditions:
            current_diagnosis_code = patient.diagnosed_conditions[-1].get("diagnosed_code")

        # Update diagnostic progression in engine
        if current_diagnosis_code:
            self.diagnostic_engine.update_diagnosis_with_progression(
                patient_id, current_diagnosis_code, new_facility
            )

            # Perform new diagnosis at the better facility
            modifiers = {
                "triage_category": patient.triage_category,
                "time_with_patient_hours": 0.5,  # Assume 30min examination
                "additional_information": ["multiple_examinations"],
            }

            new_diagnosis = self.perform_diagnosis(patient_id, new_facility, modifiers)

            # Update patient records
            patient.diagnosed_conditions.append(new_diagnosis)
            patient.diagnostic_confidence = new_diagnosis.get("confidence", 0.0)

            # Add to timeline
            patient.timeline.append(
                {
                    "timestamp": self.simulation_time,
                    "event": "diagnosis_updated",
                    "facility": new_facility,
                    "previous_diagnosis": current_diagnosis_code,
                    "new_diagnosis": new_diagnosis.get("diagnosed_code"),
                    "confidence": new_diagnosis.get("confidence", 0.0),
                    "accuracy_improvement": new_diagnosis.get("diagnostic_accuracy", 0.0)
                    - patient.diagnosed_conditions[-2].get("diagnostic_accuracy", 0.0)
                    if len(patient.diagnosed_conditions) > 1
                    else 0.0,
                }
            )

            return new_diagnosis

        return None

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
        triage_result = self.triage_mapper.calculate_triage_category(patient.current_health, severity)
        patient.triage_category = triage_result[0]  # Get category from tuple

        # Determine initial facility based on triage
        facility_map = {
            "T1": "Role2",  # Critical -> Role2 or higher
            "T2": "Role1",  # Urgent -> Role1 can stabilize
            "T3": "Role1",  # Delayed -> Role1 for basic care
            "T4": "Role1",  # Minimal -> Role1 for observation
        }

        initial_facility = facility_map.get(patient.triage_category, "Role1")

        # Check capacity and route if needed
        available_beds = self.facility_manager.get_available_beds(initial_facility)
        if available_beds <= 0:
            routing_result = self.overflow_router.route_patient(
                patient_id,  # route_patient expects patient_id as first param
                patient.triage_category,
                "routine",
                None,
            )
            # Extract facility string from routing result
            initial_facility = routing_result.get("facility", initial_facility)

        # Update patient
        patient.destination = initial_facility
        patient.timeline.append(
            {
                "timestamp": self.simulation_time,
                "event": "triaged",
                "triage": patient.triage_category,
                "assigned_to": initial_facility,
            }
        )

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
            patient.timeline.append(
                {
                    "timestamp": self.simulation_time,
                    "event": "treatment_applied",
                    "treatments": [t["name"] for t in treatments],
                    "health_before": round(patient.current_health - treatment_effect),
                    "health_after": round(new_health),
                    "location": patient.current_location,
                }
            )

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

        # Don't deteriorate if dead or discharged (RTD)
        if patient.state in [PatientState.DIED, PatientState.DISCHARGED]:
            return patient.current_health if patient.state == PatientState.DISCHARGED else 0

        # Calculate deterioration based on original severity
        base_deterioration = self.deterioration_calc.calculate_base_deterioration(
            patient.injury_type,
            patient.severity,  # Use stored severity, not recalculated
        )
        
        # Apply triage-based deterioration multiplier (T1 patients deteriorate faster)
        base_deterioration = self.deterioration_calc.apply_triage_multiplier(
            base_deterioration,
            patient.triage_category
        )
        
        # Apply treatment-based deterioration modifiers
        # Get the best (lowest) deterioration modifier from all treatments
        treatment_deterioration_modifier = 1.0
        if patient.treatments_received:
            for treatment in patient.treatments_received:
                treatment_name = treatment.get("name") or treatment.get("treatment")
                if treatment_name and treatment_name in self.treatment_mods.treatments:
                    treatment_def = self.treatment_mods.treatments[treatment_name]
                    modifier = treatment_def.get("deterioration_modifier", 1.0)
                    # Use the best (lowest) modifier
                    treatment_deterioration_modifier = min(treatment_deterioration_modifier, modifier)
        
        # Apply the treatment modifier to base deterioration
        # E.g., tourniquet reduces deterioration by 70% (modifier = 0.3)
        effective_deterioration = base_deterioration * treatment_deterioration_modifier
        
        # Convert from per hour to per minute and scale by time
        deterioration_per_minute = effective_deterioration / 60.0
        deterioration = deterioration_per_minute * time_minutes

        # Update health
        patient.current_health = max(0, patient.current_health - deterioration)

        # Check for death
        if patient.current_health <= 0:
            self.handle_patient_death(patient_id, "deterioration")
        # Check for RTD (Return to Duty) - only fully recovered patients
        # RTD requires medical assessment at Role1 or higher (not at POI)
        elif patient.current_health >= 100:  # Must be fully healthy (100 health)
            # Only discharge after medical assessment at treatment facility
            if patient.current_location in ["Role1", "Role2", "Role3", "Role4"]:
                # Additional check: has patient been treated/assessed?
                if patient.treatments_received:  # Only if received some treatment/assessment
                    self.handle_patient_discharge(patient_id, "recovered")

        return patient.current_health

    def simulate_recovery(self, patient_id: str, time_minutes: int, recovery_rate_per_hour: float = 5.0) -> int:
        """
        Simulate patient recovery at advanced medical facilities.
        
        This models active treatment and healing at Role2+ facilities where patients
        receive definitive care and should improve rather than deteriorate.
        
        Args:
            patient_id: Patient identifier
            time_minutes: Time elapsed in minutes
            recovery_rate_per_hour: Health gain per hour (default 5.0 for Role3)
                                   Typical values:
                                   - Role2: 2.0 (emergency surgery, stabilization)
                                   - Role3: 5.0 (full surgical capabilities, ICU)
                                   - Role4: 8.0 (hospital care, rehabilitation)
        
        Returns:
            Updated health score
        """
        patient = self.patients.get(patient_id)
        if not patient:
            msg = f"Patient {patient_id} not found"
            raise ValueError(msg)

        # Don't recover if dead or already discharged
        if patient.state in [PatientState.DIED, PatientState.DISCHARGED]:
            return patient.current_health if patient.state == PatientState.DISCHARGED else 0

        # Calculate recovery
        recovery_per_minute = recovery_rate_per_hour / 60.0
        recovery = recovery_per_minute * time_minutes

        # Apply recovery (capped at 100)
        old_health = patient.current_health
        patient.current_health = min(100, patient.current_health + recovery)

        # Check for RTD (Return to Duty) eligibility
        # DISABLED: Automatic RTD during recovery can cause state conflicts in treatment loop
        # RTD should be handled by the facility transfer logic in MedicalSimulationBridge
        # if patient.current_health >= 90 and patient.current_location in ["Role1", "Role2", "Role3", "Role4"]:
        #     if patient.treatments_received:
        #         self.handle_patient_discharge(patient_id, "recovered")

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
            patient_id, patient.current_location, destination, priority, patient.current_health
        )

        if transport:
            # Update patient
            patient.state = PatientState.IN_TRANSPORT
            patient.destination = destination
            patient.transport_id = transport["transport_id"]

            patient.timeline.append(
                {
                    "timestamp": self.simulation_time,
                    "event": "transport_started",
                    "from": patient.current_location,
                    "to": destination,
                    "transport_type": transport["vehicle_type"],
                    "estimated_time": transport["duration_minutes"],
                }
            )

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
        admission = self.facility_manager.admit_patient(patient_id, patient.destination, patient.triage_category)
        if admission.get("success", True):
            patient.current_location = patient.destination
            patient.state = PatientState.IN_TREATMENT

            # Update diagnosis with better facility capability
            if self.diagnostic_uncertainty_enabled:
                updated_diagnosis = self.update_diagnosis_on_transfer(patient_id, patient.current_location)
                if updated_diagnosis:
                    print(
                        f"Patient {patient_id} diagnosis updated at {patient.current_location}: "
                        f"confidence {updated_diagnosis.get('confidence', 0.0):.2f}"
                    )

            patient.destination = None
            patient.transport_id = None

            patient.timeline.append(
                {
                    "timestamp": self.simulation_time + timedelta(minutes=actual_time),
                    "event": "arrived_at_facility",
                    "facility": patient.current_location,
                    "transport_time": actual_time,
                }
            )

            return True
        # Facility full, find overflow
        routing_result = self.overflow_router.route_patient(
            patient_id,
            patient.triage_category,
            "urgent" if patient.triage_category == "T1" else "routine"
        )
        new_destination = routing_result.get("routed_to")
        if new_destination:
            patient.destination = new_destination
            self.metrics["facility_overflow_events"] += 1
            return self.transport_patient(patient_id, new_destination) is not None
        return False

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
                    patient.timeline.append(
                        {
                            "timestamp": self.simulation_time,
                            "event": "evacuated_to_csu",
                            "batch_id": batch.get("batch_id", "batch-001"),
                            "hold_time": patient_data.get("wait_time", 0),
                        }
                    )

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

        self.death_tracker.track_death(
            {
                "patient_id": patient_id,
                "time_of_death": self.simulation_time,
                "location": location,
                "cause": cause,
                "injury_type": patient.injury_type,
                "initial_health": patient.initial_health,
                "final_health": patient.current_health,
                "treatments": patient.treatments_received,
            }
        )

        # Update patient
        patient.state = PatientState.DIED
        patient.died_at = self.simulation_time
        patient.current_health = 0

        patient.timeline.append(
            {"timestamp": self.simulation_time, "event": "died", "cause": cause, "location": location}
        )

        # Update metrics
        self.metrics["patients_died"] += 1

        # Free up facility bed if applicable
        if patient.current_location in ["Role1", "Role2", "Role3", "CSU"]:
            self.facility_manager.discharge_patient(patient_id, patient.current_location)

    def handle_patient_discharge(self, patient_id: str, reason: str):
        """
        Handle patient discharge (Return to Duty) and update tracking.

        Args:
            patient_id: Patient identifier
            reason: Reason for discharge (e.g., "recovered")
        """
        patient = self.patients.get(patient_id)
        if not patient or patient.state == PatientState.DIED:
            return

        # Update patient state
        patient.state = PatientState.DISCHARGED
        patient.discharged_at = self.simulation_time
        
        patient.timeline.append(
            {
                "timestamp": self.simulation_time,
                "event": "discharged_rtd",
                "reason": reason,
                "location": patient.current_location,
                "final_health": patient.current_health
            }
        )

        # Update metrics
        if "patients_discharged" not in self.metrics:
            self.metrics["patients_discharged"] = 0
        self.metrics["patients_discharged"] += 1

        # Free up facility bed if applicable
        if patient.current_location in ["Role1", "Role2", "Role3", "CSU"]:
            self.facility_manager.discharge_patient(patient_id, patient.current_location)

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
                "alive": sum(1 for p in self.patients.values() if p.state != PatientState.DIED),
                "died": self.metrics["patients_died"],
                "evacuated": self.metrics["patients_evacuated"],
                "in_treatment": sum(1 for p in self.patients.values() if p.state == PatientState.IN_TREATMENT),
                "in_transport": sum(1 for p in self.patients.values() if p.state == PatientState.IN_TRANSPORT),
            },
            "facilities": {
                "Role1": self.facility_manager.get_occupancy("Role1"),
                "Role2": self.facility_manager.get_occupancy("Role2"),
                "Role3": self.facility_manager.get_occupancy("Role3"),
                "CSU": self.facility_manager.get_occupancy("CSU"),
            },
            "transport": self.transport_scheduler.get_transport_metrics(),
            "csu_batch": self.csu_coordinator.get_batch_hold_info(),
            "death_statistics": self.death_tracker.get_statistics()
            if hasattr(self.death_tracker, "get_statistics")
            else {},
            "metrics": self.metrics,
        }

    def advance_time(self, minutes: int):
        """
        Advance simulation time and process time-dependent events.

        Args:
            minutes: Minutes to advance
        """
        self.simulation_time += timedelta(minutes=minutes)

        # Process deterioration for all non-dead patients
        # Use list() to create a copy to avoid RuntimeError during iteration
        for patient in list(self.patients.values()):
            if patient.state not in [PatientState.DIED, PatientState.EVACUATED]:
                self.simulate_deterioration(patient.id, minutes)

        # CSU batches are managed internally
        # Transport times are managed internally
