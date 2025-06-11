import datetime
from typing import Any, Dict, List, Optional


class Patient:
    """Represents a patient with demographics and medical history"""

    def __init__(self, patient_id: int):  # patient_id is an int from range()
        self.id: int = patient_id
        self.demographics: Dict[str, Any] = {}
        self.medical_data: Dict[str, Any] = {}  # Or more specific type
        self.treatment_history: List[Dict[str, Any]] = []
        self.current_status: str = "POI"  # POI, R1, R2, R3, R4, RTD, KIA (or dynamic facility IDs)
        self.day_of_injury: Optional[str] = None  # e.g., "Day 1", "Day 2"
        self.injury_type: Optional[str] = None  # "DISEASE", "NON_BATTLE", "BATTLE_TRAUMA"
        self.triage_category: Optional[str] = None  # T1, T2, T3
        self.nationality: Optional[str] = None  # e.g., "USA", "POL"
        self.front: Optional[str] = None  # Name or ID of the front
        self.primary_condition: Optional[Dict[str, Any]] = None  # For single primary condition logic if ever needed
        self.primary_conditions: List[Dict[str, Any]] = []  # List for multiple primary conditions
        self.additional_conditions: List[Dict[str, Any]] = []
        self.gender: Optional[str] = None  # 'male', 'female'

        # Enhanced timeline tracking fields
        self.last_facility: Optional[str] = None  # Last facility visited before final status
        self.final_status: Optional[str] = None  # KIA, RTD, Remains_Role4
        self.movement_timeline: List[Dict[str, Any]] = []  # Detailed movement timeline
        self.injury_timestamp: Optional[datetime.datetime] = None  # When injury occurred

    def add_treatment(
        self,
        facility: str,
        date: datetime.datetime,
        treatments: Optional[List[Dict[str, str]]] = None,
        observations: Optional[List[Dict[str, Any]]] = None,
    ):
        """Add a treatment event to the patient's history"""
        self.treatment_history.append(
            {
                "facility": facility,
                "date": date.isoformat(),  # Store as ISO string for JSON compatibility if needed later
                "treatments": treatments or [],
                "observations": observations or [],
            }
        )
        self.current_status = facility  # This should be the facility ID/name

    def set_demographics(self, demographics: Dict[str, Any]):
        """Set patient demographics"""
        self.demographics = demographics
        if "gender" in demographics:
            self.gender = demographics["gender"]

    def get_age(self):
        """Calculate patient age from birthdate"""
        if "birthdate" not in self.demographics or not self.demographics["birthdate"]:
            return None

        try:
            birthdate_obj = datetime.datetime.strptime(self.demographics["birthdate"], "%Y-%m-%d").date()
            today = datetime.date.today()  # Use datetime.date for comparison with date object
            return (
                today.year - birthdate_obj.year - ((today.month, today.day) < (birthdate_obj.month, birthdate_obj.day))
            )
        except ValueError:
            return None  # Invalid date format

    def add_timeline_event(self, event_type: str, facility: str, timestamp: datetime.datetime, **kwargs):
        """
        Add a movement event to the patient's timeline.

        Args:
            event_type: Type of event (arrival, evacuation_start, transit_start, kia, rtd)
            facility: Facility name where event occurred
            timestamp: When the event occurred
            **kwargs: Additional event-specific data
        """
        # Calculate hours since injury
        hours_since_injury = 0.0
        if self.injury_timestamp:
            delta = timestamp - self.injury_timestamp
            hours_since_injury = round(delta.total_seconds() / 3600, 1)

        event = {
            "event_type": event_type,
            "facility": facility,
            "timestamp": timestamp.isoformat(),
            "hours_since_injury": hours_since_injury,
        }

        # Add any additional kwargs to the event
        event.update(kwargs)

        self.movement_timeline.append(event)

        # Update last facility if this is a facility-based event
        if event_type in ["arrival", "evacuation_start"] and facility not in ["KIA", "RTD"]:
            self.last_facility = facility

    def set_injury_timestamp(self, timestamp: datetime.datetime):
        """
        Set the injury timestamp (when patient was first injured).

        Args:
            timestamp: When the injury occurred
        """
        self.injury_timestamp = timestamp

        # If this is the first timeline event, add arrival at POI
        if not self.movement_timeline:
            self.add_timeline_event("arrival", "POI", timestamp)

    def set_final_status(self, status: str, facility: str, timestamp: datetime.datetime, **kwargs):
        """
        Set the final status of the patient (KIA, RTD, or Remains_Role4).

        Args:
            status: Final status (KIA, RTD, Remains_Role4)
            facility: Facility where final status was determined
            timestamp: When final status was determined
            **kwargs: Additional status-specific data
        """
        self.final_status = status

        # Add timeline event for final status
        event_type = status.lower()  # kia, rtd
        if status == "Remains_Role4":
            event_type = "remains_role4"

        self.add_timeline_event(event_type, facility, timestamp, **kwargs)

    def get_hours_since_injury(self, timestamp: Optional[datetime.datetime] = None) -> float:
        """
        Calculate hours since injury occurred.

        Args:
            timestamp: Reference timestamp (defaults to current time)

        Returns:
            Hours since injury as float
        """
        if not self.injury_timestamp:
            return 0.0

        if timestamp is None:
            timestamp = datetime.datetime.now()

        delta = timestamp - self.injury_timestamp
        return round(delta.total_seconds() / 3600, 1)

    def get_timeline_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the patient's movement timeline.

        Returns:
            Dictionary with timeline summary
        """
        if not self.movement_timeline:
            return {
                "total_events": 0,
                "total_duration_hours": 0.0,
                "facilities_visited": [],
                "final_status": self.final_status,
                "last_facility": self.last_facility,
            }

        # Extract facilities visited (excluding status events)
        facilities_visited = []
        for event in self.movement_timeline:
            if event["event_type"] in ["arrival", "evacuation_start"] and event["facility"] not in facilities_visited:
                facilities_visited.append(event["facility"])

        # Calculate total duration
        total_duration = 0.0
        if self.movement_timeline:
            last_event = self.movement_timeline[-1]
            total_duration = last_event["hours_since_injury"]

        return {
            "total_events": len(self.movement_timeline),
            "total_duration_hours": total_duration,
            "facilities_visited": facilities_visited,
            "final_status": self.final_status,
            "last_facility": self.last_facility,
        }

    def validate_timeline_consistency(self) -> Dict[str, Any]:
        """
        Validate that the timeline events are consistent and chronological.

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        if not self.movement_timeline:
            return {"is_valid": True, "errors": [], "warnings": []}

        # Check chronological order
        for i in range(len(self.movement_timeline) - 1):
            current_time = self.movement_timeline[i]["hours_since_injury"]
            next_time = self.movement_timeline[i + 1]["hours_since_injury"]

            if current_time > next_time:
                errors.append(f"Timeline not chronological at index {i}: {current_time} > {next_time}")

        # Check for logical consistency
        evacuation_active = {}  # Track active evacuations by facility

        for i, event in enumerate(self.movement_timeline):
            event_type = event["event_type"]
            facility = event["facility"]

            if event_type == "evacuation_start":
                if facility in evacuation_active:
                    warnings.append(f"Multiple evacuations started at {facility}")
                evacuation_active[facility] = event

            elif event_type == "transit_start":
                # Transit should start after evacuation ends
                if facility in evacuation_active:
                    evac_event = evacuation_active[facility]
                    evac_duration = evac_event.get("evacuation_duration_hours", 0)
                    evac_end_time = evac_event["hours_since_injury"] + evac_duration

                    if event["hours_since_injury"] < evac_end_time:
                        errors.append(f"Transit started before evacuation ended at {facility}")

                del evacuation_active[facility]  # Evacuation complete

        # Check final status consistency
        if self.final_status:
            final_events = [e for e in self.movement_timeline if e["event_type"] in ["kia", "rtd", "remains_role4"]]
            if len(final_events) > 1:
                errors.append("Multiple final status events found")

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
