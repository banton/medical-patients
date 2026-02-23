import json
import logging
import os
import random
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class MedicalConditionGenerator:
    """Generates military-specific medical conditions using configurable SNOMED CT codes."""

    def __init__(self):
        # Load conditions from JSON config
        self._config = self._load_medical_conditions()

        # Initialize condition pools from config
        self.battle_trauma_conditions = self._config.get("battle_trauma_conditions", [])
        self.non_battle_injuries = self._config.get("non_battle_injuries", [])
        self.disease_conditions = self._config.get("disease_conditions", [])
        self.severity_modifiers = self._config.get("severity_modifiers", [])
        self._related_conditions = self._config.get("related_conditions", {})
        self._allergy_list = self._config.get("allergies", [])
        self._medication_list = self._config.get("medications", [])
        self._condition_med_map = self._config.get("condition_medication_map", {})

        # Validate loaded data
        if not self.battle_trauma_conditions:
            logger.warning("No battle trauma conditions loaded, using defaults")
            self._load_default_conditions()

    def _load_medical_conditions(self) -> Dict[str, Any]:
        """Load medical_conditions.json configuration."""
        config_path = os.path.join(os.path.dirname(__file__), "medical_conditions.json")
        try:
            with open(config_path) as f:
                config = json.load(f)
                # Filter out comment fields
                return {k: v for k, v in config.items() if not k.startswith("_")}
        except FileNotFoundError:
            logger.warning("medical_conditions.json not found, using defaults")
            return {}
        except json.JSONDecodeError as e:
            logger.error("Error parsing medical_conditions.json: %s", e)
            return {}

    def _load_default_conditions(self):
        """Load hardcoded default conditions as fallback."""
        self.battle_trauma_conditions = [
            {"code": "125670008", "display": "War injury"},
            {"code": "262574004", "display": "Bullet wound"},
            {"code": "125689001", "display": "Shrapnel injury"},
            {"code": "125605004", "display": "Traumatic shock"},
            {"code": "19130008", "display": "Traumatic brain injury"},
        ]
        self.non_battle_injuries = [
            {"code": "37782003", "display": "Fracture of bone"},
            {"code": "372963008", "display": "Heat exhaustion"},
            {"code": "302914006", "display": "Ankle sprain"},
        ]
        self.disease_conditions = [
            {"code": "195662009", "display": "Acute respiratory illness"},
            {"code": "43878008", "display": "Streptococcal pharyngitis"},
            {"code": "25374005", "display": "Gastroenteritis"},
        ]
        self.severity_modifiers = [
            {"code": "371923003", "display": "Mild to moderate"},
            {"code": "371924009", "display": "Moderate"},
            {"code": "371925005", "display": "Moderate to severe"},
            {"code": "24484000", "display": "Severe"},
        ]

    def generate_condition(self, injury_type: str, triage_category: str) -> Dict[str, str]:
        """Generate a medical condition based on injury type and triage."""
        # Normalize injury type to handle variations
        injury_type_upper = injury_type.upper()

        # Select appropriate condition pool
        if "BATTLE" in injury_type_upper and "NON" not in injury_type_upper:
            conditions_pool = self.battle_trauma_conditions
        elif "NON" in injury_type_upper or "NON_BATTLE" in injury_type_upper:
            conditions_pool = self.non_battle_injuries
        else:  # DISEASE or Disease
            conditions_pool = self.disease_conditions

        # Select a base condition
        base_condition = random.choice(conditions_pool)

        # Add severity based on triage category
        severity = self._get_severity_for_triage(triage_category)

        # Combine into a complete condition
        return {
            "code": base_condition["code"],
            "display": base_condition["display"],
            "severity": severity["display"],
            "severity_code": severity["code"],
        }

    def _get_severity_for_triage(self, triage_category: str) -> Dict[str, str]:
        """Get severity modifier based on triage category."""
        if not self.severity_modifiers:
            return {"code": "371924009", "display": "Moderate"}

        if triage_category == "T1":
            return self.severity_modifiers[-1]  # Severe (last in list)
        if triage_category == "T2":
            # Moderate or Moderate to severe (middle options)
            mid_start = max(1, len(self.severity_modifiers) // 2 - 1)
            mid_end = min(len(self.severity_modifiers) - 1, mid_start + 2)
            return random.choice(self.severity_modifiers[mid_start:mid_end])
        # T3
        return self.severity_modifiers[0]  # Mild to moderate (first in list)

    def generate_multiple_conditions(
        self, injury_type: str, triage_category: str, count: int = 2
    ) -> List[Dict[str, str]]:
        """Generate multiple medical conditions of the same injury type."""
        conditions = []

        # Normalize injury type to handle variations
        injury_type_upper = injury_type.upper()

        # Select appropriate condition pool
        if "BATTLE" in injury_type_upper and "NON" not in injury_type_upper:
            conditions_pool = self.battle_trauma_conditions.copy()
        elif "NON" in injury_type_upper or "NON_BATTLE" in injury_type_upper:
            conditions_pool = self.non_battle_injuries.copy()
        else:  # DISEASE or Disease
            conditions_pool = self.disease_conditions.copy()

        # Prevent duplicates by sampling without replacement
        count = min(count, len(conditions_pool))

        # Randomly select 'count' conditions from the pool
        selected_base_conditions = random.sample(conditions_pool, count)

        # Add severity based on triage category
        for base_condition in selected_base_conditions:
            severity = self._get_severity_for_triage(triage_category)

            # Combine into a complete condition
            complete_condition = {
                "code": base_condition["code"],
                "display": base_condition["display"],
                "severity": severity["display"],
                "severity_code": severity["code"],
            }

            conditions.append(complete_condition)

        return conditions

    def generate_additional_conditions(
        self, primary_condition: Dict[str, str], count: int = 0
    ) -> List[Dict[str, str]]:
        """Generate additional conditions that might accompany the primary one."""
        related_conditions: List[Dict[str, str]] = []

        # Based on primary condition, add related conditions from config
        primary_code = primary_condition.get("code", "")

        # Check if we have related conditions defined for this primary condition
        if primary_code in self._related_conditions:
            for related in self._related_conditions[primary_code]:
                probability = related.get("probability", 0.5)
                if random.random() < probability:
                    related_conditions.append({
                        "code": related["code"],
                        "display": related["display"]
                    })

        # Add random additional conditions up to the requested count
        additional_needed = max(0, count - len(related_conditions))
        all_conditions = (
            self.battle_trauma_conditions +
            self.non_battle_injuries +
            self.disease_conditions
        )

        # Remove the primary condition from the pool
        all_conditions = [c for c in all_conditions if c["code"] != primary_code]

        # Add random conditions
        if additional_needed > 0 and all_conditions:
            additional = random.sample(
                all_conditions, min(additional_needed, len(all_conditions))
            )
            related_conditions.extend(additional)

        return related_conditions

    def generate_allergies(self, count: int = 0) -> List[Dict[str, str]]:
        """Generate random allergies."""
        if count <= 0 or not self._allergy_list:
            return []

        return random.sample(self._allergy_list, min(count, len(self._allergy_list)))

    def generate_medications(
        self, conditions: List[Dict[str, Any]], count: int = 1
    ) -> List[Dict[str, str]]:
        """Generate medications based on conditions."""
        medications: List[Dict[str, str]] = []

        if not self._medication_list:
            return medications

        # First add condition-specific medications
        for condition in conditions:
            condition_code = (
                condition["code"]
                if isinstance(condition, dict) and "code" in condition
                else str(condition)
            )

            if condition_code in self._condition_med_map:
                for med_code in self._condition_med_map[condition_code]:
                    med = next(
                        (m for m in self._medication_list if m["code"] == med_code),
                        None
                    )
                    if med and med not in medications:
                        medications.append(med)

        # Add random medications to reach the requested count
        while len(medications) < count and self._medication_list:
            med = random.choice(self._medication_list)
            if med not in medications:
                medications.append(med)

        return medications
