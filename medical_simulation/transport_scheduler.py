"""
Transport Scheduler for Medical Simulation
Manages medical transport vehicles and patient transfers between facilities
"""

from collections import deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import uuid


class TransportScheduler:
    """
    Schedules and tracks medical transport between facilities.

    Vehicle types:
    - Ground ambulances: Standard transport
    - Air ambulances: Critical/urgent transport
    - Buses: Batch transport for CSU

    Tracks transport times, deterioration risk, and died-in-transit events.
    """

    def __init__(self):
        """Initialize transport resources"""
        # Vehicle fleet - Realistic for military medical exercise
        # Each front would have multiple ambulances
        self.ground_ambulances = 40  # Was 4 - unrealistic for 200 patients
        self.air_ambulances = 4      # Was 1 - need more for critical cases
        self.buses = 6               # Was 2 - for batch transport

        # Available vehicles
        self.available_ground = self.ground_ambulances
        self.available_air = self.air_ambulances
        self.available_buses = self.buses

        # Transport times in minutes
        self.transport_times = {
            "Role1_to_Role2": 20,
            "Role1_to_CSU": 5,
            "CSU_to_Role2": 15,
            "Role2_to_Role3": 45,
            "Role1_to_Role3": 60,
            "POI_to_Role1": 10,
            "POI_to_CSU": 15,
        }

        # Air transport is 3x faster
        self.air_speed_multiplier = 0.33

        # Active transports
        self.active_transports = {}
        self.transport_queue = deque()
        self.priority_queue = deque()

        # Metrics
        self.transport_metrics = {
            "total_transports": 0,
            "completed": 0,
            "died_in_transit": 0,
            "by_vehicle_type": {"ground_ambulance": 0, "air_ambulance": 0, "bus": 0},
        }

    def schedule_transport(
        self,
        patient_id: str,
        from_facility: str,
        to_facility: str,
        priority: str = "routine",
        patient_health: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Schedule patient transport.

        Args:
            patient_id: Patient to transport
            from_facility: Origin facility
            to_facility: Destination facility
            priority: urgent or routine
            patient_health: Current health (for deterioration risk)

        Returns:
            Transport details including ID and status
        """
        transport_id = str(uuid.uuid4())[:8]

        # Calculate transport duration
        route_key = f"{from_facility}_to_{to_facility}"
        base_duration = self.transport_times.get(route_key, 30)

        # Determine vehicle type based on priority and availability
        vehicle_type = self._select_vehicle(priority, base_duration)

        if vehicle_type == "air_ambulance":
            duration = int(base_duration * self.air_speed_multiplier)
            if self.available_air > 0:
                self.available_air -= 1
                status = "scheduled"
            else:
                status = "queued"
        elif vehicle_type == "ground_ambulance":
            duration = base_duration
            if self.available_ground > 0:
                self.available_ground -= 1
                status = "scheduled"
            else:
                status = "queued"
        else:
            duration = base_duration
            status = "queued"

        # Calculate deterioration risk
        deterioration_risk = self._calculate_deterioration_risk(patient_health, duration)

        # Create transport record
        transport = {
            "transport_id": transport_id,
            "patient_id": patient_id,
            "from": from_facility,
            "to": to_facility,
            "vehicle_type": vehicle_type,
            "duration_minutes": duration,
            "status": status,
            "priority": priority,
            "scheduled_time": datetime.now(),
            "estimated_arrival": datetime.now() + timedelta(minutes=duration),
            "deterioration_risk": deterioration_risk,
        }

        if status == "scheduled":
            self.active_transports[transport_id] = transport
            self.transport_metrics["total_transports"] += 1
            self.transport_metrics["by_vehicle_type"][vehicle_type] += 1
        # Add to queue
        elif priority == "urgent":
            self.priority_queue.append(transport)
            transport["queue_position"] = len(self.priority_queue)
        else:
            self.transport_queue.append(transport)
            transport["queue_position"] = len(self.priority_queue) + len(self.transport_queue)

        return transport

    def _select_vehicle(self, priority: str, duration: int) -> str:
        """Select appropriate vehicle type"""
        # Urgent or long distance gets air if available
        if (priority == "urgent" or duration > 30) and self.available_air > 0:
            return "air_ambulance"

        # Default to ground
        return "ground_ambulance"

    def _calculate_deterioration_risk(self, patient_health: Optional[int], duration: int) -> str:
        """Calculate risk of deterioration during transport"""
        if patient_health is None:
            return "unknown"

        # Risk based on health and transport time
        if patient_health < 20 and duration > 30:
            return "high"
        if patient_health < 40 or duration > 45:
            return "moderate"
        return "low"

    def complete_transport(self, transport_id: str, outcome: str = "delivered") -> Dict[str, Any]:
        """
        Complete a transport.

        Args:
            transport_id: Transport to complete
            outcome: delivered or died_in_transit

        Returns:
            Completion result
        """
        if transport_id not in self.active_transports:
            return {"success": False, "reason": "transport_not_found"}

        transport = self.active_transports[transport_id]
        vehicle_type = transport["vehicle_type"]

        # Free up vehicle
        if vehicle_type == "air_ambulance":
            self.available_air += 1
        elif vehicle_type == "ground_ambulance":
            self.available_ground += 1
        elif vehicle_type == "bus":
            self.available_buses += 1

        # Update metrics
        self.transport_metrics["completed"] += 1
        if outcome == "died_in_transit":
            self.transport_metrics["died_in_transit"] += 1

        # Remove from active
        del self.active_transports[transport_id]

        # Process queue if vehicles available
        self._process_queue()

        return {"success": True, "transport_id": transport_id, "outcome": outcome}

    def _process_queue(self):
        """Process waiting transports when vehicles become available"""
        # Process priority queue first
        while self.priority_queue and (self.available_ground > 0 or self.available_air > 0):
            transport = self.priority_queue.popleft()
            self._activate_transport(transport)

        # Then regular queue
        while self.transport_queue and self.available_ground > 0:
            transport = self.transport_queue.popleft()
            self._activate_transport(transport)

    def _activate_transport(self, transport: Dict):
        """Activate a queued transport"""
        vehicle_type = transport["vehicle_type"]

        if vehicle_type == "air_ambulance" and self.available_air > 0:
            self.available_air -= 1
        elif vehicle_type == "ground_ambulance" and self.available_ground > 0:
            self.available_ground -= 1
        else:
            return  # Can't activate yet

        transport["status"] = "in_transit"
        transport["scheduled_time"] = datetime.now()
        transport["estimated_arrival"] = datetime.now() + timedelta(minutes=transport["duration_minutes"])

        self.active_transports[transport["transport_id"]] = transport
        self.transport_metrics["total_transports"] += 1
        self.transport_metrics["by_vehicle_type"][vehicle_type] += 1

    def schedule_batch_transport(self, patients: List[str], from_facility: str, to_facility: str) -> Dict[str, Any]:
        """
        Schedule batch transport (CSU batch transfer).

        Args:
            patients: List of patient IDs
            from_facility: Origin (usually CSU)
            to_facility: Destination (usually Role2)

        Returns:
            Batch transport details
        """
        transport_id = str(uuid.uuid4())[:8]

        # Calculate duration
        route_key = f"{from_facility}_to_{to_facility}"
        duration = self.transport_times.get(route_key, 30)

        # Check bus availability
        if self.available_buses > 0:
            self.available_buses -= 1
            status = "scheduled"
        else:
            status = "queued"

        transport = {
            "transport_id": transport_id,
            "patients": patients,
            "patient_count": len(patients),
            "from": from_facility,
            "to": to_facility,
            "vehicle_type": "bus",
            "duration_minutes": duration,
            "status": status,
            "scheduled_time": datetime.now(),
            "estimated_arrival": datetime.now() + timedelta(minutes=duration),
        }

        if status == "scheduled":
            self.active_transports[transport_id] = transport
            self.transport_metrics["total_transports"] += 1
            self.transport_metrics["by_vehicle_type"]["bus"] += 1

        return transport

    def get_transport_status(self, transport_id: str) -> Dict[str, Any]:
        """Get current status of a transport"""
        if transport_id not in self.active_transports:
            return {"status": "not_found"}

        transport = self.active_transports[transport_id]
        time_elapsed = (datetime.now() - transport["scheduled_time"]).seconds / 60
        time_remaining = max(0, transport["duration_minutes"] - time_elapsed)

        return {
            "transport_id": transport_id,
            "patient_id": transport.get("patient_id"),
            "status": "in_transit",
            "vehicle_type": transport["vehicle_type"],
            "time_elapsed": round(time_elapsed, 1),
            "time_remaining": round(time_remaining, 1),
            "estimated_arrival": transport["estimated_arrival"].isoformat(),
        }

    def get_vehicle_availability(self) -> Dict[str, int]:
        """Get current vehicle availability"""
        return {
            "ground_available": self.available_ground,
            "ground_total": self.ground_ambulances,
            "air_available": self.available_air,
            "air_total": self.air_ambulances,
            "buses_available": self.available_buses,
            "buses_total": self.buses,
        }

    def get_transport_metrics(self) -> Dict[str, Any]:
        """Get transport metrics"""
        metrics = self.transport_metrics.copy()

        # Calculate average duration
        if metrics["completed"] > 0:
            # Simplified - would track actual durations in production
            metrics["average_duration"] = 25  # Average of typical routes
        else:
            metrics["average_duration"] = 0

        # Add current status
        metrics["active_transports"] = len(self.active_transports)
        metrics["queued_transports"] = len(self.transport_queue) + len(self.priority_queue)

        return metrics
