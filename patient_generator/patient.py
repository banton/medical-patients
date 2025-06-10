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
