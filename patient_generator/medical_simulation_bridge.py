"""
Bridge between patient_generator and medical_simulation modules.
Enhances patient generation with realistic medical simulation.
"""

from datetime import datetime
import json
import os
import random
import time
from typing import Any, Dict, List, Optional

from medical_simulation.patient_flow_orchestrator import PatientFlowOrchestrator, PatientState
from medical_simulation.treatment_protocols import FacilityLevel, TreatmentProtocolManager
from patient_generator.patient import Patient
from patient_generator.treatment_utility_model import TreatmentUtilityModel


class MedicalSimulationBridge:
    """
    Bridge that integrates medical simulation modules with patient generator.
    Enhances basic patient data with realistic medical flow simulation.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the medical simulation bridge.

        Args:
            config: Optional configuration for medical simulation
        """
        self.orchestrator = PatientFlowOrchestrator()
        self.config = config or {}
        self.enabled = os.environ.get("ENABLE_MEDICAL_SIMULATION", "true").lower() == "true"

        # Load realistic evacuation and transit times
        evac_times_path = os.path.join(os.path.dirname(__file__), "evacuation_transit_times.json")
        with open(evac_times_path) as f:
            self.timing_config = json.load(f)

        # Initialize treatment utility model independently (works with or without medical simulation)
        self.utility_model_enabled = os.environ.get("ENABLE_TREATMENT_UTILITY_MODEL", "true").lower() == "true"
        self.treatment_model = TreatmentUtilityModel() if self.utility_model_enabled else None

        # Initialize treatment protocol manager
        self.protocol_manager = TreatmentProtocolManager()

        # Track conversions for batch operations
        self.patient_mapping = {}  # Maps patient_generator ID to medical_sim ID

        # Simple performance metrics
        self.metrics = {
            "total_enhanced": 0,
            "total_time": 0.0,
            "slowest_patient": 0.0,
            "treatment_selections": 0,
            "utility_model_used": 0,
            "fallback_used": 0,
        }

    def enhance_patient(self, patient: Patient) -> Patient:
        """
        Enhance a single patient with medical simulation.

        Args:
            patient: Patient from patient_generator

        Returns:
            Enhanced patient with realistic medical timeline
        """
        if not self.enabled:
            return patient

        # Track timing
        start_time = time.time()

        # Convert patient ID to string for medical simulation
        sim_patient_id = str(patient.id)
        self.patient_mapping[patient.id] = sim_patient_id

        # Map injury type and severity
        # Handle both 'injury' and 'injury_type' attributes for compatibility
        patient_injury = getattr(patient, "injury", None) or getattr(patient, "injury_type", "unknown")

        # First map to standard injury category for health engine
        injury_category = self._map_injury_category(patient_injury)
        severity = self._map_severity(patient.triage_category)

        # Initialize patient in medical simulation with proper injury category
        # Pass the original triage category to preserve warfare-generated triage
        self.orchestrator.initialize_patient(
            patient_id=sim_patient_id,
            injury_type=injury_category,  # Use category for health engine
            severity=severity,
            location="POI",
            triage_override=patient.triage_category,  # Preserve original triage
            body_part=getattr(patient, "body_part", None),  # Pass body_part if available
        )

        # Run through medical simulation flow
        self._simulate_medical_flow(sim_patient_id, patient)

        # Apply simulation results back to original patient
        self._apply_simulation_results(patient, sim_patient_id)

        # Update metrics
        elapsed = time.time() - start_time
        self.metrics["total_enhanced"] += 1
        self.metrics["total_time"] += elapsed
        self.metrics["slowest_patient"] = max(self.metrics["slowest_patient"], elapsed)

        return patient

    def _map_injury_category(self, injury: str) -> str:
        """
        Map patient injury to standard category for health engine.

        Args:
            injury: Raw injury type from patient

        Returns:
            Standard category: "Battle Injury", "Non-Battle Injury", or "Disease"
        """
        injury_lower = injury.lower()

        # Disease mappings
        if any(term in injury_lower for term in ["disease", "illness", "infection", "fever", "covid", "malaria"]):
            return "Disease"

        # Battle injury mappings
        if any(term in injury_lower for term in ["gsw", "gunshot", "blast", "ied", "shrapnel", "combat", "battle"]):
            return "Battle Injury"

        # Non-battle injury mappings
        if any(term in injury_lower for term in ["mvc", "fall", "accident", "crush", "burn", "non-battle"]):
            return "Non-Battle Injury"

        # Default based on common patterns
        if "battle" in injury_lower:
            return "Battle Injury"

        # Default to Non-Battle Injury
        return "Non-Battle Injury"

    def _map_injury_type(self, injury: str) -> str:
        """
        Map patient_generator injury types to medical_simulation types.

        Args:
            injury: Injury from patient_generator

        Returns:
            Mapped injury type for medical simulation
        """
        # Map common military injury types
        injury_mapping = {
            "GSW": "gunshot",
            "Gunshot": "gunshot",
            "Blast": "blast",
            "IED": "blast",
            "Shrapnel": "shrapnel",
            "Burn": "burn",
            "Burns": "burn",
            "Crush": "crush",
            "Fall": "blunt_trauma",
            "MVC": "blunt_trauma",  # Motor Vehicle Crash
            "Blunt": "blunt_trauma",
        }

        # Default to the original if no mapping found
        for key, value in injury_mapping.items():
            if key.lower() in injury.lower():
                return value

        return injury.lower()

    def _map_severity(self, triage: str) -> str:
        """
        Map triage category to severity level expected by health engine.

        Args:
            triage: Triage category (T1, T2, T3, T4, etc.)

        Returns:
            Severity level matching injuries.json (Severe, Moderate to severe, etc.)
        """
        severity_mapping = {
            "T1": "Severe",
            "T2": "Moderate to severe",
            "T3": "Moderate",
            "T4": "Mild to moderate",
            "Urgent": "Severe",
            "Delayed": "Moderate to severe",
            "Minimal": "Mild to moderate",
        }

        return severity_mapping.get(triage, "Moderate")

    def _simulate_medical_flow(self, sim_patient_id: str, original_patient: Patient):
        """
        Run patient through medical simulation flow with realistic combat times.

        Args:
            sim_patient_id: Medical simulation patient ID
            original_patient: Original patient for context
        """
        sim_patient = self.orchestrator.patients.get(sim_patient_id)
        if not sim_patient:
            return

        # Determine if this is a mass casualty event (affects medic response time)
        is_mass_casualty = getattr(original_patient, "is_mass_casualty", False)

        # REALISTIC WAIT FOR COMBAT MEDIC AT POI
        # Individual casualty: 5-30 minutes
        # Mass casualty (10+ casualties): 30-90 minutes when medics are overwhelmed
        if is_mass_casualty:
            # Mass casualty - medics overwhelmed but still responding
            medic_arrival_minutes = random.randint(30, 90)  # 30-90 minutes
        else:
            # Individual casualty - faster response
            medic_arrival_minutes = random.randint(5, 30)  # 5-30 minutes

        # Simulate waiting for medic (patient deteriorates while waiting)
        self.orchestrator.simulate_deterioration(sim_patient_id, medic_arrival_minutes)

        # Check if patient died or discharged waiting for medic
        sim_patient = self.orchestrator.patients.get(sim_patient_id)
        if sim_patient and sim_patient.state in [PatientState.DIED, PatientState.DISCHARGED]:
            # Died at POI or recovered (RTD) before medic arrived
            return

        # Medic arrives and performs triage (may be incorrect)
        triage_category, initial_facility = self.orchestrator.process_triage(sim_patient_id)

        # APPLY INITIAL FIELD TREATMENTS (Critical Fix)
        # Medic should apply treatments immediately upon arrival, before evacuation wait
        patient_injury = getattr(original_patient, "injury", None) or getattr(
            original_patient, "injury_type", "unknown"
        )
        initial_treatments = self._get_treatments_for_injury(patient_injury, original_patient)
        if initial_treatments:
            # Filter for POI-appropriate treatments if needed, but _get_treatments_for_injury handles this
            self.orchestrator.apply_treatment(sim_patient_id, initial_treatments)

        # Get REALISTIC evacuation wait time from JSON (hours, not minutes!)
        evac_times = self.timing_config["evacuation_times"]["POI"]
        triage_key = sim_patient.triage_category if sim_patient.triage_category in evac_times else "T2"
        wait_hours = random.uniform(evac_times[triage_key]["min_hours"], evac_times[triage_key]["max_hours"])
        wait_minutes = int(wait_hours * 60)

        # Simulate waiting for evacuation (this is where many die)
        self.orchestrator.simulate_deterioration(sim_patient_id, wait_minutes)

        # Check if patient died or discharged waiting for evacuation
        sim_patient = self.orchestrator.patients.get(sim_patient_id)
        if sim_patient and sim_patient.state in [PatientState.DIED, PatientState.DISCHARGED]:
            # Died at POI or recovered (RTD) waiting for evacuation
            return

        # Process triage again after wait (condition may have changed)
        _triage_category, initial_facility = self.orchestrator.process_triage(sim_patient_id)

        # Transport to initial facility
        if initial_facility:
            transport_id = self.orchestrator.transport_patient(sim_patient_id, initial_facility)

            if transport_id:
                # Get REALISTIC transit time from JSON
                transit_key = f"POI_to_{initial_facility}"
                if transit_key in self.timing_config["transit_times"]:
                    transit_times = self.timing_config["transit_times"][transit_key]
                    triage_key = sim_patient.triage_category if sim_patient.triage_category in transit_times else "T2"
                    transit_hours = random.uniform(
                        transit_times[triage_key]["min_hours"], transit_times[triage_key]["max_hours"]
                    )
                    transit_minutes = int(transit_hours * 60)
                else:
                    # Fallback if route not defined
                    transit_minutes = 120  # 2 hours default

                # Simulate transit time (patients can die in transit)
                self.orchestrator.simulate_deterioration(sim_patient_id, transit_minutes)

                # Complete transport
                arrived = self.orchestrator.complete_transport(sim_patient_id)

                # Debug: Log transport outcome
                if not arrived:
                    sim_patient = self.orchestrator.patients.get(sim_patient_id)
                    if sim_patient and sim_patient.state not in [PatientState.DIED, PatientState.DISCHARGED]:
                        # Patient alive but transport failed - likely no transport_id
                        if not sim_patient.transport_id:
                            print(f"DEBUG: Patient {sim_patient_id} has no transport_id after transport_patient call")

                # Check patient state after transport completion
                sim_patient = self.orchestrator.patients.get(sim_patient_id)
                if sim_patient and sim_patient.state in [PatientState.DIED, PatientState.DISCHARGED]:
                    return  # Patient died or discharged (RTD) during transport

                if not arrived and sim_patient:
                    # Transport failed but patient alive - likely facility full
                    # Apply basic treatment at POI while waiting
                    patient_injury = getattr(original_patient, "injury", None) or getattr(
                        original_patient, "injury_type", "unknown"
                    )
                    treatments = self._get_treatments_for_injury(patient_injury, original_patient)
                    if treatments:
                        self.orchestrator.apply_treatment(sim_patient_id, treatments)

                    # Mark patient as still at POI but treated
                    sim_patient.current_location = "POI"
                    return  # End processing for this patient

                if arrived:
                    # Start care chain progression loop - continue until patient reaches Role4 or dies
                    max_transfers = 4  # Safety limit to prevent infinite loops
                    transfer_count = 0
                    stay_count = 0

                    while transfer_count < max_transfers:
                        sim_patient = self.orchestrator.patients.get(sim_patient_id)
                        if not sim_patient or sim_patient.state in [PatientState.DIED, PatientState.DISCHARGED]:
                            return  # Patient died or discharged (RTD), stop processing

                        current_facility = sim_patient.current_location

                        # Apply treatments at current facility
                        patient_injury = getattr(original_patient, "injury", None) or getattr(
                            original_patient, "injury_type", "unknown"
                        )
                        # Pass current facility to ensure appropriate treatment selection
                        sim_patient.last_facility = current_facility  # Store for utility model
                        treatments = self._get_treatments_for_injury(patient_injury, original_patient)
                        if treatments:
                            self.orchestrator.apply_treatment(sim_patient_id, treatments)

                        # Get treatment time at this facility
                        if current_facility in self.timing_config["evacuation_times"]:
                            facility_times = self.timing_config["evacuation_times"][current_facility]
                            triage_key = (
                                sim_patient.triage_category if sim_patient.triage_category in facility_times else "T2"
                            )
                            treatment_hours = random.uniform(
                                facility_times[triage_key]["min_hours"], facility_times[triage_key]["max_hours"]
                            )
                        else:
                            treatment_hours = 6  # Default 6 hours if not specified

                        treatment_minutes = int(treatment_hours * 60)

                        # FACILITY-SPECIFIC BEHAVIOR
                        # Different facilities have different care models

                        if current_facility == "POI":
                            # Point of Injury: Full deterioration, no recovery
                            # This shouldn't happen in this loop (POI handled earlier)
                            self.orchestrator.simulate_deterioration(sim_patient_id, treatment_minutes)

                        elif current_facility == "Role1":
                            # Battalion Aid Station: Stabilization only
                            # Reduced deterioration through active treatment
                            # Apply treatments in cycles to maintain stabilization
                            hours_per_cycle = 2
                            total_cycles = int(treatment_hours / hours_per_cycle)

                            for _cycle_num in range(total_cycles):
                                # Check patient state
                                sim_patient = self.orchestrator.patients.get(sim_patient_id)
                                if not sim_patient or sim_patient.state in [PatientState.DIED, PatientState.DISCHARGED]:
                                    break

                                # Deteriorate for this cycle
                                self.orchestrator.simulate_deterioration(sim_patient_id, hours_per_cycle * 60)

                                # Reapply treatments if critical
                                sim_patient = self.orchestrator.patients.get(sim_patient_id)
                                if sim_patient and sim_patient.current_health < 50 and treatments:
                                    self.orchestrator.apply_treatment(sim_patient_id, treatments)

                        elif current_facility == "Role2":
                            # Forward Surgical Team: Emergency surgery + stabilization
                            # Minimal deterioration + modest recovery
                            # Split time: 60% active treatment (recovery), 40% waiting (slow deterioration)
                            treatment_time = int(treatment_minutes * 0.6)
                            wait_time = treatment_minutes - treatment_time

                            # Active treatment period: recovery
                            self.orchestrator.simulate_recovery(
                                sim_patient_id, treatment_time, recovery_rate_per_hour=3.0
                            )

                            # Waiting period: slow deterioration
                            self.orchestrator.simulate_deterioration(sim_patient_id, wait_time)

                        elif current_facility in ["Role3", "Role4"]:
                            # Combat Support Hospital / Homeland Hospital: Full care + recovery
                            # Pure recovery, no deterioration
                            recovery_rate = 5.0 if current_facility == "Role3" else 8.0
                            self.orchestrator.simulate_recovery(
                                sim_patient_id, treatment_minutes, recovery_rate_per_hour=recovery_rate
                            )

                        # After treatment at current facility, check if needs further evacuation
                        sim_patient = self.orchestrator.patients.get(sim_patient_id)
                        if not sim_patient or sim_patient.state in [PatientState.DIED, PatientState.DISCHARGED]:
                            return  # Patient died or discharged (RTD), stop processing

                        # Stop if already at Role4
                        if current_facility == "Role4":
                            break

                        # Determine if patient needs higher level care based on health and triage
                        next_facility = None

                        # T1 patients: Move through chain with lower thresholds
                        if sim_patient.triage_category == "T1":
                            if current_facility == "Role1" and sim_patient.current_health >= 5:
                                next_facility = "Role2"
                            elif current_facility == "Role2" and sim_patient.current_health >= 10:
                                next_facility = "Role3"
                            elif current_facility == "Role3" and sim_patient.current_health >= 15:
                                next_facility = "Role4"

                        # T2 patients: Move with moderate thresholds
                        elif sim_patient.triage_category == "T2":
                            if current_facility == "Role1" and sim_patient.current_health >= 15:
                                next_facility = "Role2"
                            elif current_facility == "Role2" and sim_patient.current_health >= 20:
                                next_facility = "Role3"
                            elif current_facility == "Role3" and sim_patient.current_health >= 25:
                                next_facility = "Role4"

                        # T3 patients: Move if stable
                        elif sim_patient.triage_category == "T3":
                            if current_facility == "Role1" and sim_patient.current_health >= 20:
                                next_facility = "Role2"

                        # Execute transfer if needed
                        if next_facility and next_facility != current_facility:
                            # Transport to next facility
                            transport_id = self.orchestrator.transport_patient(sim_patient_id, next_facility)

                            if transport_id:
                                # Get REALISTIC transit time from JSON
                                transit_key = f"{current_facility}_to_{next_facility}"
                                if transit_key in self.timing_config["transit_times"]:
                                    transit_times = self.timing_config["transit_times"][transit_key]
                                    triage_key = (
                                        sim_patient.triage_category
                                        if sim_patient.triage_category in transit_times
                                        else "T2"
                                    )
                                    transit_hours = random.uniform(
                                        transit_times[triage_key]["min_hours"], transit_times[triage_key]["max_hours"]
                                    )
                                    transit_minutes = int(transit_hours * 60)
                                else:
                                    # Fallback if route not defined
                                    transit_minutes = 120  # 2 hours default

                                # Simulate transit time (patients can die in transit)
                                self.orchestrator.simulate_deterioration(sim_patient_id, transit_minutes)

                                # Complete transport
                                arrived = self.orchestrator.complete_transport(sim_patient_id)

                                if arrived:
                                    transfer_count += 1
                                    stay_count = 0  # Reset stay count on transfer
                                else:
                                    # Transport failed (e.g. died in transit)
                                    break
                            else:
                                # Transport failed to start
                                break
                        else:
                            # No further evacuation needed or possible, or staying at same facility
                            # Increment stay count
                            stay_count += 1

                            # If we've stayed too long or are at Role4, stop
                            if stay_count > 3:
                                # Check if critical - if so, they die (DOW)
                                # Patients stuck at Role1/Role2 with critical health are assumed to have died of wounds
                                if sim_patient.current_health < 15:
                                    sim_patient.state = PatientState.DIED
                                    sim_patient.death_location = current_facility
                                    # Record death in orchestrator if possible, or just let the state update handle it
                                    # The bridge updates status based on state at the end

                                # Check if recovered - if so, RTD
                                elif sim_patient.current_health >= 90:
                                    self.orchestrator.handle_patient_discharge(sim_patient_id, "recovered")

                                break

                            if current_facility == "Role4":
                                # At Role4, if healthy enough, discharge
                                if sim_patient.current_health >= 90:
                                    self.orchestrator.handle_patient_discharge(sim_patient_id, "recovered")
                                break

                            # Otherwise, continue loop to simulate another period at this facility

    def _get_treatments_for_injury(self, injury: str, patient: Optional[Patient] = None) -> List[Dict[str, Any]]:
        """
        Get appropriate treatments based on injury type using protocol manager.
        Now prevents repeated treatments and restricts field treatments to POI only.

        Args:
            injury: Injury type or SNOMED code
            patient: Optional patient for additional context

        Returns:
            List of treatments to apply
        """
        base_time = datetime.now()

        # Get sim_patient to check already applied treatments
        sim_patient = None
        already_applied = set()
        if patient and hasattr(patient, "id"):
            sim_patient_id = f"sim_{patient.id}"
            sim_patient = self.orchestrator.patients.get(sim_patient_id) if hasattr(self, "orchestrator") else None

            # Track what's already been applied
            if sim_patient and hasattr(sim_patient, "treatments_received"):
                for treatment in sim_patient.treatments_received:
                    if isinstance(treatment, dict):
                        treatment_name = treatment.get("name", treatment.get("treatment"))
                        if treatment_name:
                            already_applied.add(treatment_name)

        # Try protocol-based treatment first
        if patient:
            # Get SNOMED code
            snomed_code = self._map_injury_to_snomed(injury)

            # Get current facility
            facility_str = getattr(patient, "last_facility", "POI")
            facility_mapping = {
                "POI": FacilityLevel.POI,
                "point_of_injury": FacilityLevel.POI,
                "Role1": FacilityLevel.ROLE1,
                "role1": FacilityLevel.ROLE1,
                "Role2": FacilityLevel.ROLE2,
                "role2": FacilityLevel.ROLE2,
                "Role3": FacilityLevel.ROLE3,
                "role3": FacilityLevel.ROLE3,
                "Role4": FacilityLevel.ROLE4,
                "role4": FacilityLevel.ROLE4,
            }
            facility_level = facility_mapping.get(facility_str, FacilityLevel.POI)

            # Get severity
            severity = "moderate"
            if hasattr(patient, "triage_category"):
                triage_mapping = {"T1": "critical", "T2": "severe", "T3": "moderate", "T4": "expectant"}
                severity = triage_mapping.get(patient.triage_category, "moderate")

            # Get treatments from protocol manager
            # Pass body_part if available
            body_part = getattr(patient, "body_part", None)

            treatments = self.protocol_manager.get_appropriate_treatments(
                snomed_code=snomed_code,
                facility=facility_level,
                severity=severity,  # Use triage-derived severity
                time_elapsed_minutes=0,  # Could be calculated
                body_part=body_part,
            )

            # Define POI-only treatments (field emergency treatments)
            poi_only_treatments = {"tourniquet", "pressure_bandage", "hemostatic_agent", "hemostatic_gauze"}

            if treatments:
                filtered_treatments = []
                for treatment_name in treatments[:3]:  # Limit to 3 treatments
                    # Skip if already applied
                    if treatment_name in already_applied:
                        continue

                    # Skip POI-only treatments at medical facilities
                    if treatment_name in poi_only_treatments and facility_str not in ["POI", "point_of_injury"]:
                        continue

                    filtered_treatments.append(
                        {"name": treatment_name, "applied_at": base_time, "protocol_based": True}
                    )

                if filtered_treatments:  # Only return if we have new treatments
                    self.metrics["treatment_selections"] += len(filtered_treatments)
                    return filtered_treatments

        # Use utility model if available
        if self.treatment_model and self.utility_model_enabled and patient:
            return self._get_treatments_utility_based(injury, patient)

        # Fallback to legacy keyword matching
        treatment_protocols = {
            "gunshot": [
                {"name": "tourniquet", "applied_at": base_time},
                {"name": "hemostatic_gauze", "applied_at": base_time},
                {"name": "pain_management", "applied_at": base_time},
            ],
            "blast": [
                {"name": "pressure_bandage", "applied_at": base_time},
                {"name": "airway_positioning", "applied_at": base_time},
                {"name": "iv_fluids", "applied_at": base_time},
            ],
            "burn": [
                {"name": "burn_dressing", "applied_at": base_time},
                {"name": "pain_management", "applied_at": base_time},
                {"name": "iv_fluids", "applied_at": base_time},
            ],
            "shrapnel": [
                {"name": "pressure_bandage", "applied_at": base_time},
                {"name": "hemostatic_gauze", "applied_at": base_time},
            ],
        }

        injury_lower = injury.lower()
        for injury_type, potential_treatments in treatment_protocols.items():
            if injury_type in injury_lower:
                # Filter out already applied treatments
                filtered_treatments = []
                for treatment in potential_treatments:
                    if treatment["name"] not in already_applied:
                        filtered_treatments.append(treatment)

                if filtered_treatments:
                    self.metrics["fallback_used"] += 1
                    return filtered_treatments

        # Default treatment - only if not already applied
        if "pressure_bandage" not in already_applied:
            self.metrics["fallback_used"] += 1
            return [{"name": "pressure_bandage", "applied_at": base_time}]

        # No treatments available if everything has been applied
        return []

    def _get_treatments_utility_based(self, injury: str, patient: Patient) -> List[Dict[str, Any]]:
        """
        Get treatments using the utility-based model.

        Args:
            injury: Injury type or SNOMED code
            patient: Patient object with condition details

        Returns:
            List of treatments selected by utility model
        """
        self.metrics["utility_model_used"] += 1

        # Get SNOMED code from patient conditions
        snomed_code = None
        if hasattr(patient, "conditions") and patient.conditions:
            # Use first condition from the conditions list
            first_condition = patient.conditions[0]
            if isinstance(first_condition, dict):
                snomed_code = first_condition.get("code")
        elif hasattr(patient, "primary_condition") and isinstance(patient.primary_condition, dict):
            snomed_code = patient.primary_condition.get("code")
        elif hasattr(patient, "primary_conditions") and patient.primary_conditions:
            # Use first condition if multiple
            first_condition = patient.primary_conditions[0]
            if isinstance(first_condition, dict):
                snomed_code = first_condition.get("code")

        # If no SNOMED code, try to map injury type
        if not snomed_code:
            snomed_code = self._map_injury_to_snomed(injury)

        # Get severity
        severity = "Moderate"  # Default
        if hasattr(patient, "severity"):
            if isinstance(patient.severity, str):
                severity = patient.severity
            elif isinstance(patient.severity, int):
                # Map numeric severity back to text
                severity_map = {
                    1: "Mild",
                    2: "Mild to moderate",
                    4: "Moderate",
                    6: "Moderate to severe",
                    8: "Severe",
                    9: "Critical",
                }
                severity = severity_map.get(patient.severity, "Moderate")

        # Determine current facility (default to POI for initial treatment)
        facility = "POI"
        if hasattr(patient, "last_facility") and patient.last_facility:
            facility = patient.last_facility
        elif hasattr(patient, "current_location") and patient.current_location:
            facility = patient.current_location

        # Get time elapsed (simplified - could be enhanced)
        time_elapsed = 0
        if hasattr(patient, "injury_timestamp"):
            time_elapsed = 30  # Assume 30 minutes for now

        try:
            # Use treatment utility model
            treatments = self.treatment_model.select_treatments(
                injury_code=snomed_code,
                severity=severity,
                facility=facility,
                time_elapsed_minutes=time_elapsed,
                available_resources={"supplies": 100},  # Simplified resource model
                max_treatments=3,
            )

            self.metrics["treatment_selections"] += len(treatments)
            return treatments

        except Exception as e:
            # Log error and fall back to basic treatment
            print(f"Treatment utility model error: {e}")
            self.metrics["fallback_used"] += 1
            return [{"name": "supportive_care", "applied_at": datetime.now()}]

    def _map_injury_to_snomed(self, injury: str) -> str:
        """
        Map injury description to SNOMED code.

        Args:
            injury: Injury description

        Returns:
            SNOMED code or default
        """
        # Simple mapping - could be enhanced with more sophisticated matching
        injury_mapping = {
            "gunshot": "262574004",  # Bullet wound
            "blast": "125596004",  # Explosive injury
            "burn": "7200002",  # Burn of skin
            "shrapnel": "125689001",  # Shrapnel injury
            "fracture": "37782003",  # Fracture of bone
            "tbi": "19130008",  # Traumatic brain injury
            "amputation": "284551006",  # Traumatic amputation
            "stress": "45170000",  # Psychological stress
            "diarrhea": "62315008",  # Diarrhea
            "respiratory": "195662009",  # Acute respiratory illness
        }

        injury_lower = injury.lower()
        for key, code in injury_mapping.items():
            if key in injury_lower:
                return code

        # Default to general war injury
        return "125670008"

    def _apply_simulation_results(self, patient: Patient, sim_patient_id: str):
        """
        Apply medical simulation results back to original patient.

        Args:
            patient: Original patient to enhance
            sim_patient_id: Medical simulation patient ID
        """
        sim_patient = self.orchestrator.patients.get(sim_patient_id)
        if not sim_patient:
            return

        # Update patient status based on simulation state
        status_mapping = {
            PatientState.DIED: "KIA" if sim_patient.current_location == "POI" else "DOW",
            PatientState.EVACUATED: "Evacuated",
            PatientState.IN_TREATMENT: self._map_facility_to_role(sim_patient.current_location),
            PatientState.DISCHARGED: "RTD",
        }

        patient.current_status = status_mapping.get(sim_patient.state, "In Treatment")

        # Update health score in medical_data
        if not hasattr(patient, "medical_data"):
            patient.medical_data = {}
        patient.medical_data["health_score"] = sim_patient.current_health

        # Enhanced timeline with medical simulation events
        enhanced_events = []
        for event in sim_patient.timeline:
            # Convert all datetime objects in the event to ISO strings and clean up structure
            clean_event = {}
            for k, v in event.items():
                if isinstance(v, datetime):
                    clean_event[k] = v.isoformat()
                elif isinstance(v, float):
                    # Round health values to nearest integer using mathematical rounding
                    if k in ["health", "health_before", "health_after", "current_health"]:
                        clean_event[k] = round(v)  # Proper mathematical rounding
                    else:
                        clean_event[k] = round(v, 1)
                else:
                    clean_event[k] = v

            # Use the event type to determine the appropriate structure
            event_type = event.get("event", "unknown")

            # For events that happen at a location (treatment, arrival, death)
            if event_type in ["treatment_applied", "arrived_at_poi", "arrived_at_facility", "died"]:
                enhanced_event = {
                    "timestamp": clean_event.get("timestamp"),
                    "event_type": event_type,
                    "location": clean_event.get("location", clean_event.get("facility", "POI")),
                    "details": {
                        k: v for k, v in clean_event.items() if k not in ["timestamp", "event", "location", "facility"]
                    },
                }
            # For transition events (triage, transport) that happen between locations
            elif event_type in ["triaged", "transport_started"]:
                enhanced_event = {
                    "timestamp": clean_event.get("timestamp"),
                    "event_type": event_type,
                    "details": {k: v for k, v in clean_event.items() if k not in ["timestamp", "event"]},
                }
            else:
                # Generic structure for unknown events
                enhanced_event = clean_event
                enhanced_event["event_type"] = event_type

            enhanced_events.append(enhanced_event)

        # Merge with existing timeline (use movement_timeline which is what to_dict expects)
        if hasattr(patient, "movement_timeline"):
            patient.movement_timeline.extend(enhanced_events)
        else:
            patient.movement_timeline = enhanced_events

        # Also set timeline_events for backward compatibility
        patient.timeline_events = enhanced_events

        # Triage category is already set from warfare generation, don't override
        # patient.triage_category = sim_patient.triage_category  # REMOVED - preserve original triage

        # Add treatments received
        if sim_patient.treatments_received:
            patient.treatment_history = [
                {
                    "treatment": t.get("name", "unknown"),
                    "timestamp": t.get("applied_at", datetime.now()).isoformat(),
                    "location": sim_patient.current_location,
                }
                for t in sim_patient.treatments_received
            ]

        # Transfer body_part from simulation patient to original patient
        if hasattr(sim_patient, "body_part") and sim_patient.body_part:
            patient.body_part = sim_patient.body_part

    def _map_facility_to_role(self, facility: str) -> str:
        """
        Map medical simulation facility to patient_generator role status.

        Args:
            facility: Facility name from medical simulation

        Returns:
            Role status for patient_generator
        """
        mapping = {"Role1": "R1", "Role2": "R2", "Role3": "R3", "CSU": "R4", "POI": "POI"}
        return mapping.get(facility, facility)

    def get_simulation_metrics(self) -> Dict[str, Any]:
        """
        Get metrics from the medical simulation.

        Returns:
            Dictionary of simulation metrics
        """
        if not self.enabled:
            return {"enabled": False}

        return {
            "enabled": True,
            "metrics": self.orchestrator.metrics,
            "system_status": self.orchestrator.get_system_status(),
        }
