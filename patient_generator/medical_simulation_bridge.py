"""
Bridge between patient_generator and medical_simulation modules.
Enhances patient generation with realistic medical simulation.
"""

import os
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from medical_simulation.patient_flow_orchestrator import (
    PatientFlowOrchestrator,
    PatientState
)
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
        self.enabled = os.environ.get('ENABLE_MEDICAL_SIMULATION', 'true').lower() == 'true'
        
        # Initialize treatment utility model independently (works with or without medical simulation)
        self.utility_model_enabled = os.environ.get('ENABLE_TREATMENT_UTILITY_MODEL', 'true').lower() == 'true'
        self.treatment_model = TreatmentUtilityModel() if self.utility_model_enabled else None
        
        # Track conversions for batch operations
        self.patient_mapping = {}  # Maps patient_generator ID to medical_sim ID
        
        # Simple performance metrics
        self.metrics = {
            'total_enhanced': 0,
            'total_time': 0.0,
            'slowest_patient': 0.0,
            'treatment_selections': 0,
            'utility_model_used': 0,
            'fallback_used': 0
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
        patient_injury = getattr(patient, 'injury', None) or getattr(patient, 'injury_type', 'unknown')
        
        # First map to standard injury category for health engine
        injury_category = self._map_injury_category(patient_injury)
        severity = self._map_severity(patient.triage_category)
        
        # Initialize patient in medical simulation with proper injury category
        sim_patient = self.orchestrator.initialize_patient(
            patient_id=sim_patient_id,
            injury_type=injury_category,  # Use category for health engine
            severity=severity,
            location="POI"
        )
        
        # Run through medical simulation flow
        self._simulate_medical_flow(sim_patient_id, patient)
        
        # Apply simulation results back to original patient
        self._apply_simulation_results(patient, sim_patient_id)
        
        # Update metrics
        elapsed = time.time() - start_time
        self.metrics['total_enhanced'] += 1
        self.metrics['total_time'] += elapsed
        self.metrics['slowest_patient'] = max(self.metrics['slowest_patient'], elapsed)
        
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
            "Blunt": "blunt_trauma"
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
            "Minimal": "Mild to moderate"
        }
        
        return severity_mapping.get(triage, "Moderate")

    def _simulate_medical_flow(self, sim_patient_id: str, original_patient: Patient):
        """
        Run patient through medical simulation flow.
        
        Args:
            sim_patient_id: Medical simulation patient ID
            original_patient: Original patient for context
        """
        # Process triage
        triage_category, initial_facility = self.orchestrator.process_triage(sim_patient_id)
        
        # Simulate initial deterioration (time to triage)
        self.orchestrator.simulate_deterioration(sim_patient_id, 10)  # 10 minutes to triage
        
        # Transport to initial facility
        if initial_facility:
            transport_id = self.orchestrator.transport_patient(sim_patient_id, initial_facility)
            
            if transport_id:
                # Advance time for transport
                self.orchestrator.advance_time(15)  # Average transport time
                
                # Complete transport
                arrived = self.orchestrator.complete_transport(sim_patient_id)
                
                if arrived:
                    # Apply initial treatment
                    patient_injury = getattr(original_patient, 'injury', None) or getattr(original_patient, 'injury_type', 'unknown')
                    treatments = self._get_treatments_for_injury(patient_injury, original_patient)
                    if treatments:
                        self.orchestrator.apply_treatment(sim_patient_id, treatments)
                    
                    # Simulate time in treatment
                    self.orchestrator.advance_time(30)  # 30 minutes treatment
                    
                    # Check if needs further evacuation
                    sim_patient = self.orchestrator.patients[sim_patient_id]
                    if sim_patient.current_health > 50 and sim_patient.state != PatientState.DIED:
                        # Consider evacuation to higher care
                        if initial_facility == "Role1":
                            self.orchestrator.transport_patient(sim_patient_id, "Role2")
                            self.orchestrator.advance_time(20)
                            self.orchestrator.complete_transport(sim_patient_id)

    def _get_treatments_for_injury(self, injury: str, patient: Optional[Patient] = None) -> List[Dict[str, Any]]:
        """
        Get appropriate treatments based on injury type using utility model.
        
        Args:
            injury: Injury type or SNOMED code
            patient: Optional patient for additional context
            
        Returns:
            List of treatments to apply
        """
        base_time = datetime.now()
        
        # Use utility model if available
        if self.treatment_model and self.utility_model_enabled and patient:
            return self._get_treatments_utility_based(injury, patient)
        
        # Fallback to legacy keyword matching
        treatment_protocols = {
            "gunshot": [
                {"name": "tourniquet", "applied_at": base_time},
                {"name": "hemostatic_dressing", "applied_at": base_time},
                {"name": "morphine", "applied_at": base_time}
            ],
            "blast": [
                {"name": "pressure_bandage", "applied_at": base_time},
                {"name": "splint", "applied_at": base_time},
                {"name": "iv_fluids", "applied_at": base_time}
            ],
            "burn": [
                {"name": "burn_dressing", "applied_at": base_time},
                {"name": "morphine", "applied_at": base_time},
                {"name": "iv_fluids", "applied_at": base_time}
            ],
            "shrapnel": [
                {"name": "pressure_bandage", "applied_at": base_time},
                {"name": "hemostatic_dressing", "applied_at": base_time}
            ]
        }
        
        injury_lower = injury.lower()
        for injury_type, treatments in treatment_protocols.items():
            if injury_type in injury_lower:
                self.metrics['fallback_used'] += 1
                return treatments
                
        # Default treatment
        self.metrics['fallback_used'] += 1
        return [{"name": "basic_bandage", "applied_at": base_time}]
    
    def _get_treatments_utility_based(self, injury: str, patient: Patient) -> List[Dict[str, Any]]:
        """
        Get treatments using the utility-based model.
        
        Args:
            injury: Injury type or SNOMED code
            patient: Patient object with condition details
            
        Returns:
            List of treatments selected by utility model
        """
        self.metrics['utility_model_used'] += 1
        
        # Get SNOMED code from patient conditions
        snomed_code = None
        if hasattr(patient, 'primary_condition') and isinstance(patient.primary_condition, dict):
            snomed_code = patient.primary_condition.get('code')
        elif hasattr(patient, 'primary_conditions') and patient.primary_conditions:
            # Use first condition if multiple
            first_condition = patient.primary_conditions[0]
            if isinstance(first_condition, dict):
                snomed_code = first_condition.get('code')
        
        # If no SNOMED code, try to map injury type
        if not snomed_code:
            snomed_code = self._map_injury_to_snomed(injury)
        
        # Get severity
        severity = "Moderate"  # Default
        if hasattr(patient, 'severity'):
            if isinstance(patient.severity, str):
                severity = patient.severity
            elif isinstance(patient.severity, int):
                # Map numeric severity back to text
                severity_map = {1: "Mild", 2: "Mild to moderate", 4: "Moderate",
                              6: "Moderate to severe", 8: "Severe", 9: "Critical"}
                severity = severity_map.get(patient.severity, "Moderate")
        
        # Determine current facility (default to POI for initial treatment)
        facility = "POI"
        if hasattr(patient, 'last_facility') and patient.last_facility:
            facility = patient.last_facility
        
        # Get time elapsed (simplified - could be enhanced)
        time_elapsed = 0
        if hasattr(patient, 'injury_timestamp'):
            time_elapsed = 30  # Assume 30 minutes for now
        
        try:
            # Use treatment utility model
            treatments = self.treatment_model.select_treatments(
                injury_code=snomed_code,
                severity=severity,
                facility=facility,
                time_elapsed_minutes=time_elapsed,
                available_resources={'supplies': 100},  # Simplified resource model
                max_treatments=3
            )
            
            self.metrics['treatment_selections'] += len(treatments)
            return treatments
            
        except Exception as e:
            # Log error and fall back to basic treatment
            print(f"Treatment utility model error: {e}")
            self.metrics['fallback_used'] += 1
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
            "blast": "125596004",    # Explosive injury  
            "burn": "7200002",       # Burn of skin
            "shrapnel": "125689001", # Shrapnel injury
            "fracture": "37782003",  # Fracture of bone
            "tbi": "19130008",       # Traumatic brain injury
            "amputation": "284551006", # Traumatic amputation
            "stress": "45170000",    # Psychological stress
            "diarrhea": "62315008",  # Diarrhea
            "respiratory": "195662009", # Acute respiratory illness
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
            PatientState.DISCHARGED: "RTD"
        }
        
        patient.current_status = status_mapping.get(sim_patient.state, "In Treatment")
        
        # Update health score in medical_data
        if not hasattr(patient, 'medical_data'):
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
                    if k in ['health', 'health_before', 'health_after', 'current_health']:
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
                    "details": {k: v for k, v in clean_event.items() 
                              if k not in ["timestamp", "event", "location", "facility"]}
                }
            # For transition events (triage, transport) that happen between locations
            elif event_type in ["triaged", "transport_started"]:
                enhanced_event = {
                    "timestamp": clean_event.get("timestamp"),
                    "event_type": event_type,
                    "details": {k: v for k, v in clean_event.items() 
                              if k not in ["timestamp", "event"]}
                }
            else:
                # Generic structure for unknown events
                enhanced_event = clean_event
                enhanced_event["event_type"] = event_type
            
            enhanced_events.append(enhanced_event)
        
        # Merge with existing timeline
        if hasattr(patient, 'timeline_events'):
            patient.timeline_events.extend(enhanced_events)
        else:
            patient.timeline_events = enhanced_events
            
        # Update triage category from simulation
        patient.triage_category = sim_patient.triage_category
        
        # Add treatments received
        if sim_patient.treatments_received:
            patient.treatment_history = [
                {
                    "treatment": t.get("name", "unknown"),
                    "timestamp": t.get("applied_at", datetime.now()).isoformat(),
                    "location": sim_patient.current_location
                }
                for t in sim_patient.treatments_received
            ]

    def _map_facility_to_role(self, facility: str) -> str:
        """
        Map medical simulation facility to patient_generator role status.
        
        Args:
            facility: Facility name from medical simulation
            
        Returns:
            Role status for patient_generator
        """
        mapping = {
            "Role1": "R1",
            "Role2": "R2", 
            "Role3": "R3",
            "CSU": "R4",
            "POI": "POI"
        }
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
            "system_status": self.orchestrator.get_system_status()
        }