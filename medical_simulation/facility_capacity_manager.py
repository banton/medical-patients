"""
Facility Capacity Manager for Medical Simulation
Manages bed availability, queues, and patient flow through medical facilities
"""

from collections import deque
from typing import Any, Dict, List, Optional


class FacilityCapacityManager:
    """
    Manages medical facility capacities and patient admissions.

    Facilities:
    - Role1: Battalion Aid Station (20 beds)
    - Role2: Forward Surgical Team (60 beds)
    - Role3: Combat Support Hospital (200 beds)
    - CSU: Casualty Staging Unit (50 beds, batch operations)
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize facility configurations"""
        # Default military medical facility capacities
        self.facilities = {
            "Role1": {
                "capacity": 20,
                "occupied": 0,
                "patients": [],
                "queue": deque(),
                "overflow_threshold": 0.8,  # Trigger overflow at 80%
            },
            "Role2": {"capacity": 60, "occupied": 0, "patients": [], "queue": deque(), "overflow_threshold": 0.85},
            "Role3": {"capacity": 200, "occupied": 0, "patients": [], "queue": deque(), "overflow_threshold": 0.9},
            "CSU": {
                "capacity": 50,
                "occupied": 0,
                "patients": [],
                "queue": deque(),
                "overflow_threshold": 0.8,
                "batch_size": 10,  # CSU moves patients in batches
            },
        }

        # Priority queue for urgent cases
        self.priority_queues = {facility: deque() for facility in self.facilities}

    def get_capacity(self, facility: str) -> int:
        """Get total bed capacity for a facility"""
        if facility not in self.facilities:
            return 0
        return self.facilities[facility]["capacity"]

    def get_occupancy(self, facility: str) -> int:
        """Get current number of occupied beds"""
        if facility not in self.facilities:
            return 0
        return self.facilities[facility]["occupied"]

    def get_available_beds(self, facility: str) -> int:
        """Get number of available beds"""
        if facility not in self.facilities:
            return 0
        return self.facilities[facility]["capacity"] - self.facilities[facility]["occupied"]

    def admit_patient(self, patient_id: str, facility: str, priority: str = "routine") -> Dict[str, Any]:
        """
        Admit a patient to a facility.

        Args:
            patient_id: Unique patient identifier
            facility: Target facility name
            priority: "urgent" or "routine"

        Returns:
            Result dictionary with success status
        """
        if facility not in self.facilities:
            return {"success": False, "reason": "invalid_facility"}

        fac = self.facilities[facility]

        # Check if beds available
        if fac["occupied"] < fac["capacity"]:
            fac["patients"].append(patient_id)
            fac["occupied"] += 1
            return {"success": True, "facility": facility, "bed_number": fac["occupied"]}
        # Add to queue
        if priority == "urgent":
            self.priority_queues[facility].append(patient_id)
        else:
            fac["queue"].append(patient_id)

        return {
            "success": False,
            "reason": "facility_full",
            "queued": True,
            "queue_position": len(fac["queue"]) + len(self.priority_queues[facility]),
        }

    def discharge_patient(self, patient_id: str, facility: str) -> Dict[str, Any]:
        """
        Discharge a patient from a facility.

        Args:
            patient_id: Patient to discharge
            facility: Current facility

        Returns:
            Result dictionary
        """
        if facility not in self.facilities:
            return {"success": False, "reason": "invalid_facility"}

        fac = self.facilities[facility]

        if patient_id in fac["patients"]:
            fac["patients"].remove(patient_id)
            fac["occupied"] -= 1
            return {"success": True, "facility": facility}

        return {"success": False, "reason": "patient_not_found"}

    def transfer_patient(self, patient_id: str, from_facility: str, to_facility: str) -> Dict[str, Any]:
        """
        Transfer patient between facilities.

        Args:
            patient_id: Patient to transfer
            from_facility: Current facility
            to_facility: Destination facility

        Returns:
            Result dictionary
        """
        # Discharge from current facility
        discharge_result = self.discharge_patient(patient_id, from_facility)
        if not discharge_result["success"]:
            return discharge_result

        # Admit to new facility
        admit_result = self.admit_patient(patient_id, to_facility)
        if not admit_result["success"]:
            # Rollback - readmit to original facility
            self.admit_patient(patient_id, from_facility)
            return {"success": False, "reason": "transfer_failed"}

        return {"success": True, "from": from_facility, "to": to_facility}

    def get_queue_length(self, facility: str) -> int:
        """Get number of patients in queue"""
        if facility not in self.facilities:
            return 0
        return len(self.facilities[facility]["queue"]) + len(self.priority_queues[facility])

    def get_queue(self, facility: str) -> List[str]:
        """Get ordered queue (priority patients first)"""
        if facility not in self.facilities:
            return []

        # Priority patients first, then routine
        return list(self.priority_queues[facility]) + list(self.facilities[facility]["queue"])

    def process_queue(self, facility: str) -> List[str]:
        """
        Process queue when beds become available.

        Returns:
            List of patients admitted from queue
        """
        if facility not in self.facilities:
            return []

        admitted = []
        fac = self.facilities[facility]

        # Process priority queue first
        while fac["occupied"] < fac["capacity"] and self.priority_queues[facility]:
            patient_id = self.priority_queues[facility].popleft()
            result = self.admit_patient(patient_id, facility)
            if result["success"]:
                admitted.append(patient_id)

        # Then process regular queue
        while fac["occupied"] < fac["capacity"] and fac["queue"]:
            patient_id = fac["queue"].popleft()
            result = self.admit_patient(patient_id, facility)
            if result["success"]:
                admitted.append(patient_id)

        return admitted

    def get_facility_status(self, facility: str) -> Dict[str, Any]:
        """Get comprehensive status for a facility"""
        if facility not in self.facilities:
            return {}

        fac = self.facilities[facility]
        capacity = fac["capacity"]
        occupied = fac["occupied"]

        return {
            "capacity": capacity,
            "occupied": occupied,
            "available": capacity - occupied,
            "utilization": occupied / capacity if capacity > 0 else 0,
            "queue_length": self.get_queue_length(facility),
            "patients": fac["patients"][:],  # Return copy
            "overflow_triggered": (occupied / capacity) >= fac["overflow_threshold"] if capacity > 0 else False,
        }

    def get_system_overview(self) -> Dict[str, Any]:
        """Get overview of entire medical system"""
        total_capacity = sum(f["capacity"] for f in self.facilities.values())
        total_occupied = sum(f["occupied"] for f in self.facilities.values())

        facilities_status = {}
        for name in self.facilities:
            status = self.get_facility_status(name)
            facilities_status[name] = {
                "occupied": status["occupied"],
                "available": status["available"],
                "utilization": status["utilization"],
                "queue": status["queue_length"],
            }

        return {
            "total_capacity": total_capacity,
            "total_occupied": total_occupied,
            "total_available": total_capacity - total_occupied,
            "system_utilization": total_occupied / total_capacity if total_capacity > 0 else 0,
            "facilities": facilities_status,
        }

    def check_overflow_needed(self, facility: str) -> bool:
        """Check if facility needs overflow routing"""
        if facility not in self.facilities:
            return False

        fac = self.facilities[facility]
        utilization = fac["occupied"] / fac["capacity"] if fac["capacity"] > 0 else 0
        return utilization >= fac["overflow_threshold"]

    def get_overflow_recommendation(self, facility: str) -> Dict[str, str]:
        """Get recommended overflow facilities"""
        # Standard overflow cascade
        overflow_routes = {
            "Role1": ["CSU", "Role2"],
            "Role2": ["Role3"],
            "Role3": [],  # No overflow from Role3
            "CSU": ["Role2", "Role3"],
        }

        if facility not in overflow_routes:
            return {}

        routes = overflow_routes[facility]
        return {"primary": routes[0] if len(routes) > 0 else None, "secondary": routes[1] if len(routes) > 1 else None}

    def is_csu_batch_ready(self) -> bool:
        """Check if CSU has enough patients for batch transfer"""
        if "CSU" not in self.facilities:
            return False

        csu = self.facilities["CSU"]
        batch_size = csu.get("batch_size", 10)
        return csu["occupied"] >= batch_size

    def get_csu_batch(self) -> List[str]:
        """Get batch of patients from CSU for transfer"""
        if "CSU" not in self.facilities:
            return []

        csu = self.facilities["CSU"]
        batch_size = csu.get("batch_size", 10)

        # Return first batch_size patients
        return csu["patients"][:batch_size]
