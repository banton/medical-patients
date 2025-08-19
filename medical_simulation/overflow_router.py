"""
Overflow Router for Medical Simulation
Routes patients to appropriate facilities based on capacity and triage
"""
from typing import Any, Dict, List, Optional

from medical_simulation.facility_capacity_manager import FacilityCapacityManager


class OverflowRouter:
    """
    Routes patients to medical facilities based on:
    - Triage category (T1/T2/T3)
    - Facility capacity and queues
    - Medical capabilities required
    - Transport time constraints
    """

    def __init__(self, capacity_manager: FacilityCapacityManager):
        """Initialize with facility capacity manager"""
        self.capacity_manager = capacity_manager

        # Triage to facility preference mapping
        self.triage_preferences = {
            "T1": ["Role2", "Role3"],  # Urgent - need surgery
            "T2": ["Role1", "CSU", "Role2"],  # Delayed - can wait
            "T3": ["Role1", "CSU"],  # Routine - minor injuries
            "Expectant": ["Role1"]  # Comfort care
        }

        # Transport times in minutes (simplified)
        self.transport_times = {
            "POI_to_Role1": 10,
            "POI_to_CSU": 15,
            "Role1_to_CSU": 5,
            "Role1_to_Role2": 20,
            "CSU_to_Role2": 15,
            "Role2_to_Role3": 45
        }

        # Metrics tracking
        self.routing_metrics = {
            "total_routed": 0,
            "overflow_events": 0,
            "by_facility": {},
            "by_triage": {}
        }

    def find_available_facility(self, triage: str) -> Optional[str]:
        """
        Find best available facility for triage category.

        Args:
            triage: Patient triage category

        Returns:
            Facility name or None if all full
        """
        preferences = self.triage_preferences.get(triage, ["Role1", "CSU", "Role2"])

        for facility in preferences:
            if self.capacity_manager.get_available_beds(facility) > 0:
                # Also check queue length
                queue_length = self.capacity_manager.get_queue_length(facility)
                if queue_length < 5:  # Acceptable queue
                    return facility

        # If all preferred facilities full, find any available
        for facility in ["Role1", "CSU", "Role2", "Role3"]:
            if self.capacity_manager.get_available_beds(facility) > 0:
                return facility

        return None

    def route_by_triage(self, triage: str) -> Optional[str]:
        """
        Route patient based on triage category.

        Args:
            triage: T1, T2, T3, or Expectant

        Returns:
            Recommended facility
        """
        return self.find_available_facility(triage)

    def route_patient(
        self,
        patient_id: str,
        triage: str,
        priority: str = "routine",
        constraints: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Route a patient to appropriate facility.

        Args:
            patient_id: Unique patient identifier
            triage: Triage category
            priority: urgent or routine
            constraints: Optional routing constraints

        Returns:
            Routing result with facility and reason
        """
        # Update metrics
        self.routing_metrics["total_routed"] += 1
        self.routing_metrics["by_triage"][triage] = \
            self.routing_metrics["by_triage"].get(triage, 0) + 1

        # Check constraints
        max_transport = None
        if constraints:
            max_transport = constraints.get("max_transport_time")

        # Get preferred facilities for triage
        preferences = self.triage_preferences.get(triage, ["Role1", "CSU", "Role2"])

        # Try primary preference
        primary = preferences[0] if preferences else "Role1"
        if self.capacity_manager.get_available_beds(primary) > 0:
            # Check transport time if constrained
            if max_transport:
                transport_key = f"POI_to_{primary}"
                if self.transport_times.get(transport_key, 30) <= max_transport:
                    result = self._admit_to_facility(patient_id, primary, priority)
                    result["reason"] = "primary_available"
                    result["transport_time"] = self.transport_times.get(transport_key, 30)
                    return result
            else:
                result = self._admit_to_facility(patient_id, primary, priority)
                result["reason"] = "primary_available"
                return result

        # Primary full, try overflow routing
        self.routing_metrics["overflow_events"] += 1

        # Load balance across available facilities
        best_facility = None
        min_utilization = 1.0

        for facility in ["Role1", "CSU", "Role2", "Role3"]:
            status = self.capacity_manager.get_facility_status(facility)

            # Skip if full or high queue
            if status["available"] == 0:
                continue
            if status["queue_length"] > 10:
                continue

            # Check transport constraint
            if max_transport:
                transport_key = f"POI_to_{facility}"
                if self.transport_times.get(transport_key, 30) > max_transport:
                    continue

            # Find least utilized facility
            if status["utilization"] < min_utilization:
                min_utilization = status["utilization"]
                best_facility = facility

        if best_facility:
            result = self._admit_to_facility(patient_id, best_facility, priority)
            result["reason"] = "load_balancing" if primary != best_facility else "primary_full"
            if max_transport:
                result["transport_time"] = self.transport_times.get(f"POI_to_{best_facility}", 30)
            return result

        # All facilities full - add to queue of best option
        fallback = preferences[0] if preferences else "Role1"
        self.capacity_manager.admit_patient(patient_id, fallback, priority)
        return {
            "routed_to": fallback,
            "admitted": False,
            "queued": True,
            "reason": "all_facilities_full",
            "priority": priority
        }

    def _admit_to_facility(self, patient_id: str, facility: str, priority: str) -> Dict:
        """Helper to admit patient and track metrics"""
        result = self.capacity_manager.admit_patient(patient_id, facility, priority)

        # Track facility metrics
        self.routing_metrics["by_facility"][facility] = \
            self.routing_metrics["by_facility"].get(facility, 0) + 1

        return {
            "routed_to": facility,
            "admitted": result["success"],
            "queued": result.get("queued", False),
            "priority": priority
        }

    def mass_casualty_routing(self, patients: List[Dict]) -> List[Dict]:
        """
        Route multiple patients during mass casualty event.

        Args:
            patients: List of patient dicts with id and triage

        Returns:
            List of routing results
        """
        results = []

        # Sort by triage priority (T1 first)
        triage_order = {"T1": 0, "T2": 1, "T3": 2, "Expectant": 3}
        sorted_patients = sorted(
            patients,
            key=lambda p: triage_order.get(p["triage"], 99)
        )

        for patient in sorted_patients:
            result = self.route_patient(
                patient["id"],
                patient["triage"],
                priority="urgent" if patient["triage"] == "T1" else "routine"
            )
            results.append(result)

        return results

    def get_evacuation_priority(self, facility: str, count: int = 10) -> List[Dict]:
        """
        Get prioritized list of patients for evacuation.

        Args:
            facility: Facility to evacuate from
            count: Number of patients to evacuate

        Returns:
            List of patients prioritized for evacuation
        """
        status = self.capacity_manager.get_facility_status(facility)
        patients = status.get("patients", [])

        # In real system, would check patient stability
        # For now, return first N patients
        evac_list = []
        for i, patient_id in enumerate(patients[:count]):
            evac_list.append({
                "patient_id": patient_id,
                "priority": i + 1,
                "reason": "stable_for_transfer"
            })

        return evac_list

    def get_facility_recommendations(
        self,
        injury_type: str,
        triage: str
    ) -> List[str]:
        """
        Get facility recommendations based on injury and triage.

        Args:
            injury_type: Type of injury
            triage: Triage category

        Returns:
            Ordered list of recommended facilities
        """
        # Surgical cases need Role2 or Role3
        surgical_injuries = [
            "penetrating_trauma", "gunshot", "blast_injury",
            "traumatic_amputation", "internal_bleeding"
        ]

        if any(inj in injury_type.lower() for inj in surgical_injuries):
            return ["Role2", "Role3", "Role1"]

        # Use standard triage preferences
        return self.triage_preferences.get(triage, ["Role1", "CSU", "Role2"])

    def get_routing_metrics(self) -> Dict[str, Any]:
        """Get routing metrics and statistics"""
        # Calculate average utilization
        overview = self.capacity_manager.get_system_overview()
        avg_utilization = overview["system_utilization"]

        self.routing_metrics["average_utilization"] = avg_utilization
        return self.routing_metrics.copy()
