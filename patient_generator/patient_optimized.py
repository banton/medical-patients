"""
Optimized Patient class with reduced memory footprint.
Part of EPIC-003: Production Scalability Improvements - Phase 3
"""

from dataclasses import dataclass
import datetime
from typing import Any, Dict, List, Optional, Tuple


@dataclass(slots=True)
class OptimizedPatient:
    """
    Memory-optimized Patient class using slots to reduce memory footprint.

    Using __slots__ prevents the creation of __dict__ for each instance,
    significantly reducing memory usage when creating many patients.
    """

    # Core identification
    id: int

    # Status fields
    current_status: str = "POI"  # POI, R1, R2, R3, R4, RTD, KIA
    final_status: Optional[str] = None
    last_facility: Optional[str] = None

    # Demographics - store as tuple for immutability and memory efficiency
    demographics_data: Optional[Tuple[str, ...]] = None  # (first_name, last_name, birthdate, gender, etc.)

    # Medical data - use compact representation
    injury_type: Optional[str] = None
    triage_category: Optional[str] = None
    primary_condition_code: Optional[str] = None  # Store code instead of full dict

    # Identity
    nationality: Optional[str] = None
    front: Optional[str] = None
    gender: Optional[str] = None

    # Timeline - use more compact representation
    injury_timestamp: Optional[float] = None  # Store as timestamp float instead of datetime
    movement_events: Optional[List[Tuple[str, str, float]]] = None  # (event_type, facility, timestamp)

    # Temporal fields
    warfare_scenario: Optional[str] = None
    casualty_event_id: Optional[str] = None
    is_mass_casualty: bool = False
    environmental_flags: int = 0  # Use bit flags instead of list

    # Cached computed values
    _age: Optional[int] = None
    _demographics_dict: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Initialize mutable fields."""
        if self.movement_events is None:
            self.movement_events = []

    def set_demographics(self, demographics: Dict[str, Any]):
        """Set patient demographics in optimized format."""
        # Store as tuple for memory efficiency
        self.demographics_data = (
            demographics.get("first_name", ""),
            demographics.get("last_name", ""),
            demographics.get("birthdate", ""),
            demographics.get("gender", ""),
            demographics.get("nationality", ""),
            demographics.get("blood_type", ""),
        )

        if "gender" in demographics:
            self.gender = demographics["gender"]

        # Clear cached dict
        self._demographics_dict = None

    @property
    def demographics(self) -> Dict[str, Any]:
        """Get demographics as dictionary (computed on demand)."""
        if self._demographics_dict is None and self.demographics_data:
            self._demographics_dict = {
                "first_name": self.demographics_data[0],
                "last_name": self.demographics_data[1],
                "birthdate": self.demographics_data[2],
                "gender": self.demographics_data[3],
                "nationality": self.demographics_data[4],
                "blood_type": self.demographics_data[5],
            }
        return self._demographics_dict or {}

    def get_age(self) -> Optional[int]:
        """Calculate patient age from birthdate (cached)."""
        if self._age is not None:
            return self._age

        if not self.demographics_data or not self.demographics_data[2]:
            return None

        try:
            birthdate_str = self.demographics_data[2]
            birthdate_obj = datetime.datetime.strptime(birthdate_str, "%Y-%m-%d").date()
            today = datetime.date.today()
            self._age = (
                today.year - birthdate_obj.year - ((today.month, today.day) < (birthdate_obj.month, birthdate_obj.day))
            )
            return self._age
        except ValueError:
            return None

    def add_timeline_event(self, event_type: str, facility: str, timestamp: datetime.datetime):
        """Add a movement event in optimized format."""
        if self.movement_events is None:
            self.movement_events = []

        # Store as compact tuple
        self.movement_events.append(
            (
                event_type,
                facility,
                timestamp.timestamp(),  # Store as float
            )
        )

        # Update current facility
        if event_type in ["arrival", "kia", "rtd"]:
            self.last_facility = facility
            if event_type in ["kia", "rtd"]:
                self.final_status = event_type.upper()

    @property
    def movement_timeline(self) -> List[Dict[str, Any]]:
        """Get movement timeline as list of dicts (computed on demand)."""
        if not self.movement_events:
            return []

        timeline = []
        injury_ts = self.injury_timestamp or 0

        for event_type, facility, timestamp in self.movement_events:
            hours_since_injury = round((timestamp - injury_ts) / 3600, 1) if injury_ts else 0
            timeline.append(
                {
                    "event_type": event_type,
                    "facility": facility,
                    "timestamp": datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc).isoformat(),
                    "hours_since_injury": hours_since_injury,
                }
            )

        return timeline

    def set_environmental_condition(self, condition: str, value: bool = True):
        """Set environmental condition using bit flags."""
        # Map conditions to bit positions
        conditions_map = {
            "night_operations": 0,
            "extreme_weather": 1,
            "urban_combat": 2,
            "mountain_terrain": 3,
            "desert_conditions": 4,
            "arctic_conditions": 5,
            "jungle_terrain": 6,
            "amphibious_ops": 7,
        }

        if condition in conditions_map:
            bit_position = conditions_map[condition]
            if value:
                self.environmental_flags |= 1 << bit_position
            else:
                self.environmental_flags &= ~(1 << bit_position)

    def get_environmental_conditions(self) -> List[str]:
        """Get list of active environmental conditions."""
        conditions_map = {
            0: "night_operations",
            1: "extreme_weather",
            2: "urban_combat",
            3: "mountain_terrain",
            4: "desert_conditions",
            5: "arctic_conditions",
            6: "jungle_terrain",
            7: "amphibious_ops",
        }

        active_conditions = []
        for bit_position, condition in conditions_map.items():
            if self.environmental_flags & (1 << bit_position):
                active_conditions.append(condition)

        return active_conditions

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        # Build efficient dict representation
        result = {
            "id": self.id,
            "current_status": self.current_status,
            "demographics": self.demographics,
            "injury_type": self.injury_type,
            "triage_category": self.triage_category,
            "nationality": self.nationality,
            "front": self.front,
            "gender": self.gender,
        }

        # Add optional fields only if present
        if self.final_status:
            result["final_status"] = self.final_status

        if self.last_facility:
            result["last_facility"] = self.last_facility

        if self.injury_timestamp:
            result["injury_timestamp"] = datetime.datetime.fromtimestamp(self.injury_timestamp, tz=datetime.timezone.utc).isoformat()

        if self.movement_events:
            result["movement_timeline"] = self.movement_timeline

        if self.warfare_scenario:
            result["warfare_scenario"] = self.warfare_scenario

        if self.casualty_event_id:
            result["casualty_event_id"] = self.casualty_event_id

        if self.is_mass_casualty:
            result["is_mass_casualty"] = self.is_mass_casualty

        if self.environmental_flags:
            result["environmental_conditions"] = self.get_environmental_conditions()

        if self.primary_condition_code:
            result["primary_condition"] = {"code": self.primary_condition_code}
            result["primary_conditions"] = [{"code": self.primary_condition_code}]

        # Add calculated age if available
        age = self.get_age()
        if age is not None:
            result["age"] = age

        return result


def migrate_patient(old_patient: Any) -> OptimizedPatient:
    """
    Migrate from old Patient class to OptimizedPatient.

    Args:
        old_patient: Instance of the old Patient class

    Returns:
        OptimizedPatient instance with same data
    """
    # Create new optimized patient
    new_patient = OptimizedPatient(id=old_patient.id)

    # Copy basic fields
    new_patient.current_status = old_patient.current_status
    new_patient.final_status = old_patient.final_status
    new_patient.last_facility = old_patient.last_facility
    new_patient.injury_type = old_patient.injury_type
    new_patient.triage_category = old_patient.triage_category
    new_patient.nationality = old_patient.nationality
    new_patient.front = old_patient.front
    new_patient.gender = old_patient.gender
    new_patient.warfare_scenario = old_patient.warfare_scenario
    new_patient.casualty_event_id = old_patient.casualty_event_id
    new_patient.is_mass_casualty = old_patient.is_mass_casualty

    # Set demographics
    if old_patient.demographics:
        new_patient.set_demographics(old_patient.demographics)

    # Convert injury timestamp
    if old_patient.injury_timestamp:
        new_patient.injury_timestamp = old_patient.injury_timestamp.timestamp()

    # Convert movement timeline
    if old_patient.movement_timeline:
        new_patient.movement_events = []
        for event in old_patient.movement_timeline:
            timestamp = datetime.datetime.fromisoformat(event["timestamp"])
            new_patient.movement_events.append((event["event_type"], event["facility"], timestamp.timestamp()))

    # Convert environmental conditions
    if hasattr(old_patient, "environmental_conditions"):
        for condition in old_patient.environmental_conditions:
            new_patient.set_environmental_condition(condition, True)

    # Extract condition code if available
    if old_patient.primary_condition:
        new_patient.primary_condition_code = old_patient.primary_condition.get("code", "UNKNOWN")

    return new_patient
