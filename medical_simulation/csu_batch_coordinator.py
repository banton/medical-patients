"""
CSU Batch Coordinator for Medical Simulation
Manages batch operations for Casualty Staging Unit transfers
"""
from datetime import datetime
from typing import Any, Dict, List

from medical_simulation.facility_capacity_manager import FacilityCapacityManager


class CSUBatchCoordinator:
    """
    Coordinates batch transfers from CSU (Casualty Staging Unit).
    CSU holds patients temporarily and moves them in batches for efficiency.

    Standard batch size: 10 patients
    Transfer when: Batch full OR max hold time exceeded
    """

    def __init__(self, capacity_manager: FacilityCapacityManager, batch_size: int = 10):
        """Initialize with capacity manager and batch configuration"""
        self.capacity_manager = capacity_manager
        self.batch_size = batch_size
        self.max_hold_time = 60  # Maximum minutes to hold partial batch

        # Current batch tracking
        self.current_batch = []
        self.batch_start_time = None

        # Metrics
        self.batch_metrics = {
            "total_batches": 0,
            "total_patients_transferred": 0,
            "partial_batches": 0,
            "full_batches": 0
        }

    def add_to_batch(self, patient_id: str, triage: str) -> Dict[str, Any]:
        """
        Add patient to current batch.

        Args:
            patient_id: Patient identifier
            triage: Patient triage category

        Returns:
            Batch status including readiness
        """
        # Track first patient time
        if not self.current_batch:
            self.batch_start_time = datetime.now()

        # Add to batch
        self.current_batch.append({
            "patient_id": patient_id,
            "triage": triage,
            "added_time": datetime.now()
        })

        batch_ready = len(self.current_batch) >= self.batch_size

        return {
            "success": True,
            "batch_count": len(self.current_batch),
            "batch_ready": batch_ready,
            "batch_size": self.batch_size
        }

    def is_batch_ready(self) -> bool:
        """Check if batch is ready for transfer"""
        if len(self.current_batch) >= self.batch_size:
            return True

        # Check if hold time exceeded
        if self.batch_start_time:
            hold_duration = (datetime.now() - self.batch_start_time).seconds / 60
            if hold_duration >= self.max_hold_time:
                return True

        return False

    def prepare_batch_transfer(self) -> Dict[str, Any]:
        """
        Prepare batch for transfer.

        Returns:
            Batch information including patients and destination
        """
        if not self.current_batch:
            return {
                "patients": [],
                "destination": None,
                "transport_required": False
            }

        # Get prioritized patient list
        patients = self.get_prioritized_batch()

        # Determine best destination
        destination = self.recommend_destination()

        return {
            "patients": patients,
            "destination": destination,
            "transport_required": True,
            "batch_size": len(patients)
        }

    def execute_batch_transfer(
        self,
        destination: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Execute batch transfer to destination facility.

        Args:
            destination: Target facility (usually Role2)
            force: Force transfer even if batch not full

        Returns:
            Transfer result
        """
        # Check if batch ready or forced
        if not force and not self.is_batch_ready():
            return {
                "success": False,
                "reason": "batch_not_ready",
                "current_size": len(self.current_batch),
                "required_size": self.batch_size
            }

        # Check destination capacity
        available = self.capacity_manager.get_available_beds(destination)
        batch_size = len(self.current_batch)

        if available < batch_size:
            return {
                "success": False,
                "reason": "insufficient_capacity",
                "required": batch_size,
                "available": available
            }

        # Transfer each patient
        transferred = []
        for patient_info in self.current_batch:
            patient_id = patient_info["patient_id"]

            # Transfer from CSU to destination
            result = self.capacity_manager.transfer_patient(
                patient_id, "CSU", destination
            )

            if result["success"]:
                transferred.append(patient_id)

        # Update metrics
        self.batch_metrics["total_batches"] += 1
        self.batch_metrics["total_patients_transferred"] += len(transferred)

        if len(transferred) < self.batch_size:
            self.batch_metrics["partial_batches"] += 1
        else:
            self.batch_metrics["full_batches"] += 1

        # Clear batch
        self.current_batch = []
        self.batch_start_time = None

        return {
            "success": True,
            "transferred_count": len(transferred),
            "destination": destination,
            "partial_batch": len(transferred) < self.batch_size
        }

    def get_prioritized_batch(self) -> List[Dict]:
        """
        Get batch prioritized by triage category.

        Returns:
            Prioritized list of patients (T1 first)
        """
        # Sort by triage priority
        triage_priority = {"T1": 0, "T2": 1, "T3": 2, "Expectant": 3}

        return sorted(
            self.current_batch,
            key=lambda p: triage_priority.get(p["triage"], 99)
        )


    def get_batch_hold_info(self) -> Dict[str, Any]:
        """
        Get information about current batch hold time.

        Returns:
            Hold time information
        """
        if not self.batch_start_time:
            return {
                "batch_size": 0,
                "hold_duration": 0,
                "max_hold_time": self.max_hold_time
            }

        hold_duration = (datetime.now() - self.batch_start_time).seconds / 60

        return {
            "batch_size": len(self.current_batch),
            "first_patient_time": self.batch_start_time.isoformat(),
            "current_hold_duration": round(hold_duration, 1),
            "max_hold_time": self.max_hold_time,
            "time_remaining": max(0, self.max_hold_time - hold_duration)
        }

    def recommend_destination(self) -> str:
        """
        Recommend best destination for batch transfer.

        Returns:
            Recommended facility name
        """
        # Check Role2 availability (primary destination)
        role2_available = self.capacity_manager.get_available_beds("Role2")
        role2_utilization = self.capacity_manager.get_facility_status("Role2")["utilization"]

        # If Role2 has space and not too full
        if role2_available >= self.batch_size and role2_utilization < 0.9:
            return "Role2"

        # Check Role3 as alternative
        role3_available = self.capacity_manager.get_available_beds("Role3")
        if role3_available >= self.batch_size:
            return "Role3"

        # Default to Role2 even if tight on space
        return "Role2"

    def get_batch_metrics(self) -> Dict[str, Any]:
        """Get batch operation metrics"""
        metrics = self.batch_metrics.copy()

        # Calculate averages
        if metrics["total_batches"] > 0:
            metrics["average_batch_size"] = (
                metrics["total_patients_transferred"] / metrics["total_batches"]
            )
            metrics["partial_batch_rate"] = (
                metrics["partial_batches"] / metrics["total_batches"]
            )
        else:
            metrics["average_batch_size"] = 0
            metrics["partial_batch_rate"] = 0

        # Add current batch info
        metrics["current_batch_size"] = len(self.current_batch)
        metrics["current_batch_ready"] = self.is_batch_ready()

        return metrics
