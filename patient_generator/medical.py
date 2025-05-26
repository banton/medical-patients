import random


class MedicalConditionGenerator:
    """Generates military-specific medical conditions"""

    def __init__(self):
        # Initialize common conditions by type
        self.battle_trauma_conditions = [
            {"code": "125670008", "display": "War injury"},
            {"code": "262574004", "display": "Bullet wound"},
            {"code": "125689001", "display": "Shrapnel injury"},
            {"code": "125605004", "display": "Traumatic shock"},
            {"code": "19130008", "display": "Traumatic brain injury"},
            {"code": "125596004", "display": "Injury by explosive"},
            {"code": "284551006", "display": "Traumatic amputation of limb"},
            {"code": "361220002", "display": "Penetrating injury"},
            {"code": "7200002", "display": "Burn of skin"},
            {"code": "2055003", "display": "Laceration of hand"},
        ]

        self.non_battle_injuries = [
            {"code": "37782003", "display": "Fracture of bone"},
            {"code": "372963008", "display": "Heat exhaustion"},
            {"code": "302914006", "display": "Ankle sprain"},
            {"code": "55566008", "display": "Burn injury"},
            {"code": "428794004", "display": "Malnutrition"},
            {"code": "409711008", "display": "Vehicle accident injury"},
            {"code": "275272006", "display": "Crush injury"},
            {"code": "87991007", "display": "Abdominal pain"},
            {"code": "23924001", "display": "Tight chest"},
            {"code": "267036007", "display": "Dyspnea"},
        ]

        self.disease_conditions = [
            {"code": "195662009", "display": "Acute respiratory illness"},
            {"code": "43878008", "display": "Streptococcal pharyngitis"},
            {"code": "25374005", "display": "Gastroenteritis"},
            {"code": "16932000", "display": "Nausea and vomiting"},
            {"code": "68566005", "display": "Urinary tract infection"},
            {"code": "62315008", "display": "Diarrhea"},
            {"code": "45170000", "display": "Psychological stress"},
            {"code": "73249009", "display": "Mental exhaustion"},
            {"code": "386661006", "display": "Fever"},
            {"code": "9826008", "display": "Conjunctivitis"},
        ]

        # Add severity modifiers
        self.severity_modifiers = [
            {"code": "371923003", "display": "Mild to moderate"},
            {"code": "371924009", "display": "Moderate"},
            {"code": "371925005", "display": "Moderate to severe"},
            {"code": "24484000", "display": "Severe"},
        ]

    def generate_condition(self, injury_type, triage_category):
        """Generate a medical condition based on injury type and triage"""
        # Select appropriate condition pool
        if injury_type == "BATTLE_TRAUMA":
            conditions_pool = self.battle_trauma_conditions
        elif injury_type == "NON_BATTLE":
            conditions_pool = self.non_battle_injuries
        else:  # DISEASE
            conditions_pool = self.disease_conditions

        # Select a base condition
        base_condition = random.choice(conditions_pool)

        # Add severity based on triage category
        if triage_category == "T1":
            severity = self.severity_modifiers[3]  # Severe
        elif triage_category == "T2":
            severity = random.choice(self.severity_modifiers[1:3])  # Moderate or Moderate to severe
        else:  # T3
            severity = self.severity_modifiers[0]  # Mild to moderate

        # Combine into a complete condition
        return {
            "code": base_condition["code"],
            "display": base_condition["display"],
            "severity": severity["display"],
            "severity_code": severity["code"],
        }

    def generate_multiple_conditions(self, injury_type, triage_category, count=2):
        """Generate multiple medical conditions of the same injury type"""
        conditions = []

        # Select appropriate condition pool
        if injury_type == "BATTLE_TRAUMA":
            conditions_pool = self.battle_trauma_conditions.copy()
        elif injury_type == "NON_BATTLE":
            conditions_pool = self.non_battle_injuries.copy()
        else:  # DISEASE
            conditions_pool = self.disease_conditions.copy()

        # Prevent duplicates by sampling without replacement
        count = min(count, len(conditions_pool))

        # Randomly select 'count' conditions from the pool
        selected_base_conditions = random.sample(conditions_pool, count)

        # Add severity based on triage category
        for base_condition in selected_base_conditions:
            if triage_category == "T1":
                severity = self.severity_modifiers[3]  # Severe
            elif triage_category == "T2":
                severity = random.choice(self.severity_modifiers[1:3])  # Moderate or Moderate to severe
            else:  # T3
                severity = self.severity_modifiers[0]  # Mild to moderate

            # Combine into a complete condition
            complete_condition = {
                "code": base_condition["code"],
                "display": base_condition["display"],
                "severity": severity["display"],
                "severity_code": severity["code"],
            }

            conditions.append(complete_condition)

        return conditions

    def generate_additional_conditions(self, primary_condition, count=0):
        """Generate additional conditions that might accompany the primary one"""
        related_conditions = []

        # Based on primary condition, add related conditions
        primary_code = primary_condition["code"]

        # Example: For traumatic brain injury, add related conditions
        if primary_code == "19130008":  # TBI
            if random.random() < 0.7:
                related_conditions.append({"code": "62106007", "display": "Concussion with loss of consciousness"})
            if random.random() < 0.4:
                related_conditions.append({"code": "309557009", "display": "Intracranial hemorrhage"})

        # Example: For bullet wound, add related trauma
        elif primary_code == "262574004":  # Bullet wound
            if random.random() < 0.6:
                related_conditions.append({"code": "20376005", "display": "Hemorrhage"})
            if random.random() < 0.3:
                related_conditions.append({"code": "125640002", "display": "Traumatic rupture of organ"})

        # Add random additional conditions up to the requested count
        additional_needed = max(0, count - len(related_conditions))
        all_conditions = self.battle_trauma_conditions + self.non_battle_injuries + self.disease_conditions

        # Remove the primary condition from the pool
        all_conditions = [c for c in all_conditions if c["code"] != primary_condition["code"]]

        # Add random conditions
        if additional_needed > 0 and all_conditions:
            additional = random.sample(all_conditions, min(additional_needed, len(all_conditions)))
            related_conditions.extend(additional)

        return related_conditions

    def generate_allergies(self, count=0):
        """Generate random allergies"""
        allergies = []

        allergy_list = [
            {"code": "300916003", "display": "Allergy to penicillin"},
            {"code": "294000004", "display": "Allergy to morphine"},
            {"code": "294617006", "display": "Allergy to tetracycline"},
            {"code": "417532002", "display": "Allergy to aspirin"},
            {"code": "420126008", "display": "Allergy to peanuts"},
            {"code": "425525006", "display": "Allergy to shellfish"},
            {"code": "91934008", "display": "Allergy to animal dander"},
            {"code": "418689008", "display": "Allergy to grass pollen"},
            {"code": "300438000", "display": "Allergy to mushrooms"},
            {"code": "300913005", "display": "Allergy to latex"},
        ]

        if count > 0:
            allergies = random.sample(allergy_list, min(count, len(allergy_list)))

        return allergies

    def generate_medications(self, conditions, count=1):
        """Generate medications based on conditions"""
        medications = []

        medication_list = [
            {"code": "372767008", "display": "Morphine"},
            {"code": "387517004", "display": "Paracetamol"},
            {"code": "372522002", "display": "Ibuprofen"},
            {"code": "374957002", "display": "Amoxicillin"},
            {"code": "370167007", "display": "Diazepam"},
            {"code": "373337001", "display": "Ciprofloxacin"},
            {"code": "372756003", "display": "Metronidazole"},
            {"code": "385057009", "display": "Prednisolone"},
            {"code": "374352003", "display": "Acyclovir"},
            {"code": "387160009", "display": "Progesterone"},
        ]

        # Map conditions to relevant medications
        condition_med_map = {
            "262574004": ["372767008", "387517004"],  # Bullet wound -> Morphine, Paracetamol
            "19130008": ["372767008", "370167007"],  # TBI -> Morphine, Diazepam
            "125605004": ["372767008"],  # Traumatic shock -> Morphine
            "195662009": ["387517004", "372522002"],  # Respiratory illness -> Paracetamol, Ibuprofen
            "43878008": ["374957002"],  # Strep throat -> Amoxicillin
            "68566005": ["373337001"],  # UTI -> Ciprofloxacin
        }

        # First add condition-specific medications
        for condition in conditions:
            condition_code = condition["code"] if isinstance(condition, dict) and "code" in condition else condition

            if condition_code in condition_med_map:
                for med_code in condition_med_map[condition_code]:
                    med = next((m for m in medication_list if m["code"] == med_code), None)
                    if med and med not in medications:
                        medications.append(med)

        # Add random medications to reach the requested count
        while len(medications) < count and medication_list:
            med = random.choice(medication_list)
            if med not in medications:
                medications.append(med)

        return medications
