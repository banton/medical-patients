import datetime
import json
from typing import Any, Dict, List, Optional


class Patient:
    """Represents a patient with demographics and medical history"""

    # Version tracking for compatibility checking
    PATIENT_MODEL_VERSION = "1.0.0"

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

        # Temporal generation fields
        self.warfare_scenario: Optional[str] = None  # Type of warfare that caused injury
        self.casualty_event_id: Optional[str] = None  # Unique event identifier
        self.is_mass_casualty: bool = False  # Part of mass casualty event
        self.environmental_conditions: List[str] = []  # Active environmental factors

        # Medical simulation fields (v1.0.0)
        self.health_score: Optional[int] = None  # Current health 0-100
        self.initial_health: Optional[int] = None  # Health at injury time
        self.deterioration_rate: Optional[float] = None  # Health loss per hour
        self.health_timeline: List[Dict[str, Any]] = []  # [{time: "T+0", health: 60}, ...]
        self.treatments_applied: List[Dict[str, Any]] = []  # [{treatment: "tourniquet", time: "T+0.5h", effect: 0.5}]

        # Facility and care tracking
        self.bed_type_assigned: Optional[str] = None  # "T1", "T2", "T3" bed currently in
        self.care_quality: Optional[float] = None  # 1.0 = appropriate care, <1.0 = degraded

        # Death tracking (if applicable)
        self.death_details: Optional[Dict[str, Any]] = None  # Category, time, preventability, bottleneck

        # Transport and overflow tracking
        self.transport_events: List[Dict[str, Any]] = []  # Transport history with durations
        self.overflow_count: int = 0  # Times redirected due to capacity
        self.total_wait_time: Optional[float] = None  # Hours spent waiting (CSU, queues)

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

        for _i, event in enumerate(self.movement_timeline):
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

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert patient to optimized JSON-serializable dictionary.
        - Removes null values
        - Rounds floats to 1 decimal
        - Uses numeric severity scale
        - Eliminates redundancy
        """
        def round_float(value, decimals=1):
            """Round float values to specified decimals"""
            if isinstance(value, float):
                return round(value, decimals)
            return value
        
        # Convert triage to numeric severity (0-9 scale)
        severity_map = {
            "T1": 9,  # Critical
            "T2": 7,  # Urgent  
            "T3": 4,  # Delayed
            "T4": 1,  # Minimal
        }
        
        # Build optimized output
        result = {
            "id": self.id,
            "nationality": self.nationality,
            "gender": self.gender or (self.demographics.get("gender") if self.demographics else None),
            "injury_type": self.injury_type,
            "severity": severity_map.get(self.triage_category, 5),
            "status": self.current_status,
            "front": self.front,
        }
        
        # Add demographics (skip nulls)
        if self.demographics:
            demo = {}
            for k, v in self.demographics.items():
                if v is not None:
                    if k == "weight" and isinstance(v, float):
                        demo[k] = round_float(v)
                    else:
                        demo[k] = v
            if demo:
                result["demographics"] = demo
        
        # Add health score from medical_data
        if self.medical_data and "health_score" in self.medical_data:
            health = self.medical_data["health_score"]
            if health is not None:
                result["health"] = round_float(health)
        
        # Use primary_conditions only (not both primary_condition and primary_conditions)
        if self.primary_conditions:
            conditions = []
            for cond in self.primary_conditions:
                if isinstance(cond, dict):
                    # Simplify condition structure
                    conditions.append({
                        "code": cond.get("code"),
                        "name": cond.get("display")
                    })
            if conditions:
                result["conditions"] = conditions
        
        # Add additional conditions if present
        if self.additional_conditions:
            additional = []
            for cond in self.additional_conditions:
                if isinstance(cond, dict):
                    additional.append({
                        "code": cond.get("code"),
                        "name": cond.get("display")
                    })
            if additional:
                result["additional_conditions"] = additional
        
        # Add treatments if present
        if self.treatment_history:
            result["treatments"] = self.treatment_history
        
        # Add timeline if it has events
        if self.movement_timeline:
            timeline = []
            for event in self.movement_timeline:
                clean_event = {}
                for k, v in event.items():
                    if v is not None:
                        if isinstance(v, (datetime.datetime, datetime.date)):
                            clean_event[k] = v.isoformat()
                        elif hasattr(v, 'isoformat'):  # Catch any datetime-like objects
                            clean_event[k] = v.isoformat()
                        elif isinstance(v, float):
                            clean_event[k] = round_float(v)
                        else:
                            clean_event[k] = v
                timeline.append(clean_event)
            if timeline:
                result["timeline"] = timeline
        
        # Add injury time if present
        if self.injury_timestamp:
            if hasattr(self.injury_timestamp, 'isoformat'):
                result["injury_time"] = self.injury_timestamp.isoformat()
            elif isinstance(self.injury_timestamp, str):
                result["injury_time"] = self.injury_timestamp
        
        # Add scenario info if present
        if hasattr(self, "warfare_scenario") and self.warfare_scenario:
            result["scenario"] = self.warfare_scenario
        if hasattr(self, "casualty_event_id") and self.casualty_event_id:
            result["event_id"] = self.casualty_event_id
        if hasattr(self, "is_mass_casualty") and self.is_mass_casualty:
            result["mass_casualty"] = True
        
        # Add day of injury if present
        if self.day_of_injury:
            result["day"] = self.day_of_injury
            
        # Add timeline events from medical simulation if present
        if hasattr(self, 'timeline_events') and self.timeline_events:
            result["events"] = self.timeline_events
            
        return result

    def to_json(self) -> str:
        """
        Convert patient to JSON string.
        """
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Patient":
        """
        Create Patient instance from dictionary.
        Handles deserializing datetime strings back to datetime objects.
        """
        patient = cls(data["id"])

        # Set basic attributes
        patient.demographics = data.get("demographics", {})
        patient.medical_data = data.get("medical_data", {})
        patient.treatment_history = data.get("treatment_history", [])
        patient.current_status = data.get("current_status", "POI")
        patient.day_of_injury = data.get("day_of_injury")
        patient.injury_type = data.get("injury_type")
        patient.triage_category = data.get("triage_category")
        patient.nationality = data.get("nationality")
        patient.front = data.get("front")
        patient.primary_condition = data.get("primary_condition")
        patient.primary_conditions = data.get("primary_conditions", [])
        patient.additional_conditions = data.get("additional_conditions", [])
        patient.gender = data.get("gender")

        # Enhanced timeline fields
        patient.last_facility = data.get("last_facility")
        patient.final_status = data.get("final_status")
        patient.movement_timeline = data.get("movement_timeline", [])

        # Convert injury_timestamp back to datetime if present
        injury_timestamp_str = data.get("injury_timestamp")
        if injury_timestamp_str:
            patient.injury_timestamp = datetime.datetime.fromisoformat(injury_timestamp_str)

        # Temporal generation fields
        patient.warfare_scenario = data.get("warfare_scenario")
        patient.casualty_event_id = data.get("casualty_event_id")
        patient.is_mass_casualty = data.get("is_mass_casualty", False)
        patient.environmental_conditions = data.get("environmental_conditions", [])

        return patient

    @classmethod
    def from_json(cls, json_str: str) -> "Patient":
        """
        Create Patient instance from JSON string.
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
