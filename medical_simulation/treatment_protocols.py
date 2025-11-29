"""
Military Medical Treatment Protocols
Maps SNOMED injury codes to appropriate treatment protocols based on military medical standards.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Set


class TreatmentCategory(Enum):
    """Categories of medical treatments."""

    HEMORRHAGE_CONTROL = "hemorrhage_control"
    AIRWAY_MANAGEMENT = "airway_management"
    CIRCULATION_SUPPORT = "circulation_support"
    TRAUMA_SURGERY = "trauma_surgery"
    BURN_CARE = "burn_care"
    NEUROLOGICAL = "neurological"
    INFECTION_PREVENTION = "infection_prevention"
    PAIN_MANAGEMENT = "pain_management"
    STABILIZATION = "stabilization"


class FacilityLevel(Enum):
    """Military medical facility levels."""

    POI = "point_of_injury"
    ROLE1 = "role1"
    ROLE2 = "role2"
    ROLE3 = "role3"
    ROLE4 = "role4"


@dataclass
class TreatmentProtocol:
    """Defines a treatment protocol for a specific injury."""

    snomed_code: str
    injury_name: str
    categories: List[TreatmentCategory]
    primary_treatments: Dict[FacilityLevel, List[str]]
    secondary_treatments: Dict[FacilityLevel, List[str]]
    contraindicated_treatments: List[str]
    critical_time_window_minutes: int
    notes: str


class TreatmentProtocolManager:
    """Manages treatment protocols for military medical injuries."""

    def __init__(self):
        self.protocols = self._initialize_protocols()
        self.treatment_by_category = self._map_treatments_by_category()

    def _initialize_protocols(self) -> Dict[str, TreatmentProtocol]:
        """Initialize all treatment protocols based on SNOMED codes."""
        protocols = {}

        # Battle Trauma Protocols
        protocols["262574004"] = TreatmentProtocol(
            snomed_code="262574004",
            injury_name="Gunshot Wound",
            categories=[TreatmentCategory.HEMORRHAGE_CONTROL, TreatmentCategory.TRAUMA_SURGERY],
            primary_treatments={
                FacilityLevel.POI: ["tourniquet", "pressure_bandage", "hemostatic_gauze"],
                FacilityLevel.ROLE1: ["iv_access", "iv_fluids", "pain_management"],
                FacilityLevel.ROLE2: ["blood_transfusion", "damage_control_surgery"],
                FacilityLevel.ROLE3: ["definitive_surgery", "antibiotics"],
                FacilityLevel.ROLE4: ["definitive_surgery", "rehabilitation"],
            },
            secondary_treatments={
                FacilityLevel.POI: ["airway_positioning"],
                FacilityLevel.ROLE1: ["antibiotics", "needle_decompression"],
                FacilityLevel.ROLE2: ["chest_tube", "intubation"],
                FacilityLevel.ROLE3: ["specialized_surgery"],
                FacilityLevel.ROLE4: ["reconstructive_surgery"],
            },
            contraindicated_treatments=[],
            critical_time_window_minutes=60,
            notes="Prioritize hemorrhage control and rapid evacuation",
        )

        protocols["125689001"] = TreatmentProtocol(
            snomed_code="125689001",
            injury_name="Shrapnel/Fragment Injury",
            categories=[TreatmentCategory.HEMORRHAGE_CONTROL, TreatmentCategory.INFECTION_PREVENTION],
            primary_treatments={
                FacilityLevel.POI: ["pressure_bandage", "hemostatic_gauze"],
                FacilityLevel.ROLE1: ["iv_access", "antibiotics", "pain_management"],
                FacilityLevel.ROLE2: ["surgical_debridement", "blood_transfusion"],
                FacilityLevel.ROLE3: ["definitive_surgery", "wound_closure"],
                FacilityLevel.ROLE4: ["reconstructive_surgery", "rehabilitation"],
            },
            secondary_treatments={
                FacilityLevel.POI: ["tourniquet"],
                FacilityLevel.ROLE1: ["iv_fluids"],
                FacilityLevel.ROLE2: ["damage_control_surgery"],
                FacilityLevel.ROLE3: ["antibiotics"],
                FacilityLevel.ROLE4: ["specialized_surgery"],
            },
            contraindicated_treatments=[],
            critical_time_window_minutes=120,
            notes="Multiple fragments require careful assessment",
        )

        protocols["125596004"] = TreatmentProtocol(
            snomed_code="125596004",
            injury_name="Blast/Explosive Injury",
            categories=[
                TreatmentCategory.HEMORRHAGE_CONTROL,
                TreatmentCategory.AIRWAY_MANAGEMENT,
                TreatmentCategory.BURN_CARE,
            ],
            primary_treatments={
                FacilityLevel.POI: ["tourniquet", "airway_positioning", "pressure_bandage"],
                FacilityLevel.ROLE1: ["needle_decompression", "iv_access", "pain_management"],
                FacilityLevel.ROLE2: ["intubation", "damage_control_surgery", "blood_transfusion"],
                FacilityLevel.ROLE3: ["definitive_surgery", "burn_treatment", "chest_tube"],
                FacilityLevel.ROLE4: ["specialized_surgery", "burn_reconstruction", "rehabilitation"],
            },
            secondary_treatments={
                FacilityLevel.POI: ["hemostatic_gauze"],
                FacilityLevel.ROLE1: ["antibiotics", "iv_fluids"],
                FacilityLevel.ROLE2: ["surgical_airway"],
                FacilityLevel.ROLE3: ["antibiotics"],
                FacilityLevel.ROLE4: ["psychological_support"],
            },
            contraindicated_treatments=[],
            critical_time_window_minutes=30,
            notes="Complex polytrauma requiring multiple simultaneous interventions",
        )

        protocols["361220002"] = TreatmentProtocol(
            snomed_code="361220002",
            injury_name="Penetrating Injury",
            categories=[TreatmentCategory.HEMORRHAGE_CONTROL, TreatmentCategory.TRAUMA_SURGERY],
            primary_treatments={
                FacilityLevel.POI: ["pressure_bandage", "hemostatic_gauze"],
                FacilityLevel.ROLE1: ["iv_access", "iv_fluids", "pain_management"],
                FacilityLevel.ROLE2: ["damage_control_surgery", "blood_transfusion"],
                FacilityLevel.ROLE3: ["definitive_surgery", "antibiotics"],
                FacilityLevel.ROLE4: ["specialized_surgery", "rehabilitation"],
            },
            secondary_treatments={
                FacilityLevel.POI: ["airway_positioning"],
                FacilityLevel.ROLE1: ["antibiotics"],
                FacilityLevel.ROLE2: ["chest_tube"],
                FacilityLevel.ROLE3: ["wound_closure"],
                FacilityLevel.ROLE4: ["reconstructive_surgery"],
            },
            contraindicated_treatments=["tourniquet"],  # Avoid if torso/head injury
            critical_time_window_minutes=45,
            notes="Do not remove impaled objects",
        )

        protocols["7200002"] = TreatmentProtocol(
            snomed_code="7200002",
            injury_name="Burn Injury",
            categories=[TreatmentCategory.BURN_CARE, TreatmentCategory.AIRWAY_MANAGEMENT],
            primary_treatments={
                FacilityLevel.POI: ["airway_positioning", "burn_dressing"],
                FacilityLevel.ROLE1: ["iv_access", "iv_fluids", "pain_management"],
                FacilityLevel.ROLE2: ["intubation", "burn_resuscitation", "antibiotics"],
                FacilityLevel.ROLE3: ["burn_surgery", "skin_grafting", "infection_control"],
                FacilityLevel.ROLE4: ["burn_reconstruction", "rehabilitation", "scar_management"],
            },
            secondary_treatments={
                FacilityLevel.POI: ["hypothermia_prevention"],
                FacilityLevel.ROLE1: ["antibiotics"],
                FacilityLevel.ROLE2: ["escharotomy"],
                FacilityLevel.ROLE3: ["nutritional_support"],
                FacilityLevel.ROLE4: ["psychological_support"],
            },
            contraindicated_treatments=["tourniquet"],
            critical_time_window_minutes=60,
            notes="Airway burns are critical priority",
        )

        protocols["19130008"] = TreatmentProtocol(
            snomed_code="19130008",
            injury_name="Traumatic Brain Injury",
            categories=[TreatmentCategory.NEUROLOGICAL, TreatmentCategory.AIRWAY_MANAGEMENT],
            primary_treatments={
                FacilityLevel.POI: ["airway_positioning", "c_spine_immobilization"],
                FacilityLevel.ROLE1: ["neurological_monitoring", "oxygen_therapy"],
                FacilityLevel.ROLE2: ["intubation", "icp_monitoring", "mannitol"],
                FacilityLevel.ROLE3: ["neurosurgery", "craniotomy", "icp_management"],
                FacilityLevel.ROLE4: ["neuro_rehabilitation", "cognitive_therapy"],
            },
            secondary_treatments={
                FacilityLevel.POI: ["pressure_bandage"],  # For scalp bleeding
                FacilityLevel.ROLE1: ["iv_access"],
                FacilityLevel.ROLE2: ["seizure_prophylaxis"],
                FacilityLevel.ROLE3: ["antibiotics"],
                FacilityLevel.ROLE4: ["specialized_rehabilitation"],
            },
            contraindicated_treatments=["hypotonic_fluids", "hyperventilation"],
            critical_time_window_minutes=30,
            notes="Avoid hypotension and hypoxia",
        )

        protocols["284551006"] = TreatmentProtocol(
            snomed_code="284551006",
            injury_name="Traumatic Amputation",
            categories=[TreatmentCategory.HEMORRHAGE_CONTROL, TreatmentCategory.TRAUMA_SURGERY],
            primary_treatments={
                FacilityLevel.POI: ["tourniquet", "pressure_bandage", "hemostatic_gauze"],
                FacilityLevel.ROLE1: ["iv_access", "iv_fluids", "pain_management"],
                FacilityLevel.ROLE2: ["blood_transfusion", "damage_control_surgery", "stump_revision"],
                FacilityLevel.ROLE3: ["definitive_surgery", "antibiotics", "wound_closure"],
                FacilityLevel.ROLE4: ["prosthetic_fitting", "rehabilitation", "psychological_support"],
            },
            secondary_treatments={
                FacilityLevel.POI: ["limb_preservation"],  # Save amputated part if possible
                FacilityLevel.ROLE1: ["antibiotics"],
                FacilityLevel.ROLE2: ["replantation_assessment"],
                FacilityLevel.ROLE3: ["vascular_surgery"],
                FacilityLevel.ROLE4: ["occupational_therapy"],
            },
            contraindicated_treatments=[],
            critical_time_window_minutes=30,
            notes="Preserve amputated part for possible replantation",
        )

        protocols["125605004"] = TreatmentProtocol(
            snomed_code="125605004",
            injury_name="Traumatic Shock",
            categories=[TreatmentCategory.CIRCULATION_SUPPORT, TreatmentCategory.STABILIZATION],
            primary_treatments={
                FacilityLevel.POI: ["tourniquet", "pressure_bandage", "shock_position"],
                FacilityLevel.ROLE1: ["iv_access", "iv_fluids", "warm_fluids"],
                FacilityLevel.ROLE2: ["blood_transfusion", "vasopressors", "damage_control_surgery"],
                FacilityLevel.ROLE3: ["massive_transfusion_protocol", "definitive_surgery"],
                FacilityLevel.ROLE4: ["icu_management", "organ_support"],
            },
            secondary_treatments={
                FacilityLevel.POI: ["hypothermia_prevention"],
                FacilityLevel.ROLE1: ["antibiotics"],
                FacilityLevel.ROLE2: ["coagulopathy_management"],
                FacilityLevel.ROLE3: ["renal_replacement"],
                FacilityLevel.ROLE4: ["rehabilitation"],
            },
            contraindicated_treatments=["excessive_crystalloids"],
            critical_time_window_minutes=15,
            notes="Immediate hemorrhage control and resuscitation critical",
        )

        # Non-Battle Injury Protocols
        protocols["37782003"] = TreatmentProtocol(
            snomed_code="37782003",
            injury_name="Fracture",
            categories=[TreatmentCategory.STABILIZATION, TreatmentCategory.PAIN_MANAGEMENT],
            primary_treatments={
                FacilityLevel.POI: ["splinting", "pain_management"],
                FacilityLevel.ROLE1: ["iv_access", "pain_management", "xray"],
                FacilityLevel.ROLE2: ["reduction", "casting", "orthopedic_surgery"],
                FacilityLevel.ROLE3: ["definitive_fixation", "antibiotics"],
                FacilityLevel.ROLE4: ["rehabilitation", "physical_therapy"],
            },
            secondary_treatments={
                FacilityLevel.POI: ["pressure_bandage"],  # If open fracture
                FacilityLevel.ROLE1: ["antibiotics"],  # If open fracture
                FacilityLevel.ROLE2: ["compartment_syndrome_release"],
                FacilityLevel.ROLE3: ["bone_grafting"],
                FacilityLevel.ROLE4: ["occupational_therapy"],
            },
            contraindicated_treatments=[],
            critical_time_window_minutes=360,
            notes="Open fractures require urgent antibiotics",
        )

        protocols["125666000"] = TreatmentProtocol(
            snomed_code="125666000",
            injury_name="Heat Injury",
            categories=[TreatmentCategory.STABILIZATION, TreatmentCategory.CIRCULATION_SUPPORT],
            primary_treatments={
                FacilityLevel.POI: ["cooling", "oral_hydration"],
                FacilityLevel.ROLE1: ["iv_access", "iv_fluids", "active_cooling"],
                FacilityLevel.ROLE2: ["core_cooling", "electrolyte_management"],
                FacilityLevel.ROLE3: ["icu_monitoring", "organ_support"],
                FacilityLevel.ROLE4: ["rehabilitation", "heat_acclimatization"],
            },
            secondary_treatments={
                FacilityLevel.POI: ["rest_in_shade"],
                FacilityLevel.ROLE1: ["temperature_monitoring"],
                FacilityLevel.ROLE2: ["seizure_management"],
                FacilityLevel.ROLE3: ["dialysis"],  # If rhabdomyolysis
                FacilityLevel.ROLE4: ["return_to_duty_assessment"],
            },
            contraindicated_treatments=["antipyretics"],
            critical_time_window_minutes=30,
            notes="Rapid cooling essential for heat stroke",
        )

        # Disease Protocols
        protocols["386661006"] = TreatmentProtocol(
            snomed_code="386661006",
            injury_name="Fever",
            categories=[TreatmentCategory.INFECTION_PREVENTION, TreatmentCategory.STABILIZATION],
            primary_treatments={
                FacilityLevel.POI: ["antipyretics", "oral_hydration"],
                FacilityLevel.ROLE1: ["iv_access", "antibiotics", "blood_cultures"],
                FacilityLevel.ROLE2: ["broad_spectrum_antibiotics", "sepsis_protocol"],
                FacilityLevel.ROLE3: ["targeted_antibiotics", "source_control"],
                FacilityLevel.ROLE4: ["long_term_antibiotics", "rehabilitation"],
            },
            secondary_treatments={
                FacilityLevel.POI: ["cooling_measures"],
                FacilityLevel.ROLE1: ["malaria_testing"],
                FacilityLevel.ROLE2: ["infectious_disease_consult"],
                FacilityLevel.ROLE3: ["abscess_drainage"],
                FacilityLevel.ROLE4: ["return_to_duty_assessment"],
            },
            contraindicated_treatments=[],
            critical_time_window_minutes=120,
            notes="Consider tropical diseases in deployment areas",
        )

        protocols["62315008"] = TreatmentProtocol(
            snomed_code="62315008",
            injury_name="Diarrhea",
            categories=[TreatmentCategory.STABILIZATION, TreatmentCategory.INFECTION_PREVENTION],
            primary_treatments={
                FacilityLevel.POI: ["oral_rehydration", "loperamide"],
                FacilityLevel.ROLE1: ["iv_fluids", "electrolyte_replacement"],
                FacilityLevel.ROLE2: ["antibiotics", "stool_cultures"],
                FacilityLevel.ROLE3: ["targeted_therapy", "nutritional_support"],
                FacilityLevel.ROLE4: ["rehabilitation", "return_to_duty"],
            },
            secondary_treatments={
                FacilityLevel.POI: ["rest"],
                FacilityLevel.ROLE1: ["antiemetics"],
                FacilityLevel.ROLE2: ["parasitology_testing"],
                FacilityLevel.ROLE3: ["colonoscopy"],
                FacilityLevel.ROLE4: ["dietary_counseling"],
            },
            contraindicated_treatments=["opioids"],  # Can worsen some infections
            critical_time_window_minutes=240,
            notes="Consider infectious causes in deployment",
        )

        return protocols

    def _map_treatments_by_category(self) -> Dict[TreatmentCategory, Set[str]]:
        """Map treatment categories to specific treatments."""
        return {
            TreatmentCategory.HEMORRHAGE_CONTROL: {
                "tourniquet",
                "pressure_bandage",
                "hemostatic_gauze",
                "blood_transfusion",
                "massive_transfusion_protocol",
            },
            TreatmentCategory.AIRWAY_MANAGEMENT: {
                "airway_positioning",
                "intubation",
                "surgical_airway",
                "needle_decompression",
                "oxygen_therapy",
            },
            TreatmentCategory.CIRCULATION_SUPPORT: {
                "iv_access",
                "iv_fluids",
                "blood_transfusion",
                "vasopressors",
                "warm_fluids",
            },
            TreatmentCategory.TRAUMA_SURGERY: {
                "damage_control_surgery",
                "definitive_surgery",
                "surgical_debridement",
                "wound_closure",
            },
            TreatmentCategory.BURN_CARE: {
                "burn_dressing",
                "burn_resuscitation",
                "escharotomy",
                "burn_surgery",
                "skin_grafting",
            },
            TreatmentCategory.NEUROLOGICAL: {
                "neurological_monitoring",
                "icp_monitoring",
                "mannitol",
                "neurosurgery",
                "craniotomy",
                "seizure_prophylaxis",
            },
            TreatmentCategory.INFECTION_PREVENTION: {
                "antibiotics",
                "broad_spectrum_antibiotics",
                "targeted_antibiotics",
                "wound_irrigation",
                "tetanus_prophylaxis",
            },
            TreatmentCategory.PAIN_MANAGEMENT: {
                "pain_management",
                "regional_anesthesia",
                "ketamine",
                "morphine",
                "fentanyl",
            },
            TreatmentCategory.STABILIZATION: {
                "splinting",
                "c_spine_immobilization",
                "pelvic_binder",
                "chest_tube",
                "shock_position",
            },
        }

    def get_protocol(self, snomed_code: str) -> Optional[TreatmentProtocol]:
        """Get treatment protocol for a SNOMED code."""
        return self.protocols.get(snomed_code)

    def get_appropriate_treatments(
        self,
        snomed_code: str,
        facility: FacilityLevel,
        severity: str = "moderate",
        time_elapsed_minutes: int = 0,
        body_part: Optional[str] = None,
    ) -> List[str]:
        """
        Get appropriate treatments for an injury at a specific facility.

        Args:
            snomed_code: SNOMED code of the injury
            facility: Current medical facility level
            severity: Injury severity (affects treatment selection)
            time_elapsed_minutes: Time since injury occurred
            body_part: Anatomical location of injury (optional)

        Returns:
            List of appropriate treatment names
        """
        protocol = self.get_protocol(snomed_code)
        if not protocol:
            # Fallback to generic trauma protocol
            return self._get_generic_treatments(facility, severity, body_part)

        treatments = []

        # Get primary treatments for this facility
        if facility in protocol.primary_treatments:
            treatments.extend(protocol.primary_treatments[facility])

        # Add secondary treatments based on severity
        if severity in ["severe", "critical"] and facility in protocol.secondary_treatments:
            treatments.extend(protocol.secondary_treatments[facility])

        # Filter out contraindicated treatments
        treatments = [t for t in treatments if t not in protocol.contraindicated_treatments]

        # Filter based on body part constraints
        if body_part:
            treatments = [t for t in treatments if self._validate_treatment_for_body_part(t, body_part)]

        # Prioritize based on critical time window
        if time_elapsed_minutes <= protocol.critical_time_window_minutes:
            # Within critical window - prioritize life-saving interventions
            treatments = self._prioritize_critical_treatments(treatments)

        return treatments

    def _validate_treatment_for_body_part(self, treatment: str, body_part: str) -> bool:
        """Validate if treatment is appropriate for the body part."""
        # Define constraints mapping treatment -> allowed body parts
        # If treatment not in list, it's allowed everywhere
        constraints = {
            "tourniquet": ["arm", "leg", "extremity"],
            "chest_seal": ["torso", "chest", "back"],
            "needle_decompression": ["torso", "chest"],
            "chest_tube": ["torso", "chest"],
            "cervical_collar": ["head", "neck"],
            "craniotomy": ["head"],
            "icp_monitoring": ["head"],
            "intubation": ["head", "neck"],  # Airway access
            "surgical_airway": ["neck"],
            "splint": ["arm", "leg", "extremity"],
            "casting": ["arm", "leg", "extremity"],
        }

        # Normalize inputs
        treatment_lower = treatment.lower()
        body_part_lower = body_part.lower()

        # Check specific constraints
        for constrained_treatment, allowed_parts in constraints.items():
            if constrained_treatment in treatment_lower:
                # Check if body part matches any allowed part
                is_allowed = any(part in body_part_lower for part in allowed_parts)
                if not is_allowed:
                    return False

        return True

    def _get_generic_treatments(
        self, facility: FacilityLevel, severity: str, body_part: Optional[str] = None
    ) -> List[str]:
        """Get generic treatments when specific protocol not found."""
        generic = {
            FacilityLevel.POI: ["pressure_bandage", "airway_positioning"],
            FacilityLevel.ROLE1: ["iv_access", "pain_management", "antibiotics"],
            FacilityLevel.ROLE2: ["blood_transfusion", "damage_control_surgery"],
            FacilityLevel.ROLE3: ["definitive_surgery", "antibiotics"],
            FacilityLevel.ROLE4: ["rehabilitation", "specialized_care"],
        }

        treatments = generic.get(facility, [])

        # Add more treatments for severe cases
        if severity in ["severe", "critical"]:
            if facility == FacilityLevel.POI:
                # Only add tourniquet if appropriate for body part
                if body_part and self._validate_treatment_for_body_part("tourniquet", body_part):
                    treatments.append("tourniquet")
                elif not body_part:
                    # If no body part known, assume it might be needed but warn/risk
                    treatments.append("tourniquet")
            elif facility in [FacilityLevel.ROLE2, FacilityLevel.ROLE3]:
                treatments.append("intubation")

        return treatments

    def _prioritize_critical_treatments(self, treatments: List[str]) -> List[str]:
        """Prioritize treatments for critical time window."""
        # Define priority order for critical interventions
        priority_order = [
            "tourniquet",
            "airway_positioning",
            "needle_decompression",
            "pressure_bandage",
            "hemostatic_gauze",
            "iv_access",
            "blood_transfusion",
            "damage_control_surgery",
            "intubation",
        ]

        # Sort treatments by priority
        prioritized = []
        for treatment in priority_order:
            if treatment in treatments:
                prioritized.append(treatment)

        # Add remaining treatments
        for treatment in treatments:
            if treatment not in prioritized:
                prioritized.append(treatment)

        return prioritized

    def validate_treatment_combination(self, treatments: List[str], snomed_code: str) -> bool:
        """
        Validate if a combination of treatments is appropriate.

        Args:
            treatments: List of treatment names
            snomed_code: SNOMED code of the injury

        Returns:
            True if combination is valid
        """
        protocol = self.get_protocol(snomed_code)
        if not protocol:
            return True  # Allow if no protocol defined

        # Check for contraindicated treatments
        for treatment in treatments:
            if treatment in protocol.contraindicated_treatments:
                return False

        # Additional validation rules can be added here
        # For example, checking for incompatible treatment combinations

        return True

    def get_treatment_sequence(
        self, snomed_code: str, facilities_visited: List[FacilityLevel]
    ) -> Dict[FacilityLevel, List[str]]:
        """
        Get the full treatment sequence across multiple facilities.

        Args:
            snomed_code: SNOMED code of the injury
            facilities_visited: List of facilities in order of visit

        Returns:
            Dictionary mapping each facility to its treatments
        """
        protocol = self.get_protocol(snomed_code)
        if not protocol:
            return {}

        sequence = {}
        time_elapsed = 0

        for facility in facilities_visited:
            # Estimate time elapsed based on facility progression
            if facility == FacilityLevel.POI:
                time_elapsed = 5
            elif facility == FacilityLevel.ROLE1:
                time_elapsed = 30
            elif facility == FacilityLevel.ROLE2:
                time_elapsed = 90
            elif facility == FacilityLevel.ROLE3:
                time_elapsed = 180
            else:
                time_elapsed = 360

            treatments = self.get_appropriate_treatments(
                snomed_code,
                facility,
                severity="severe",  # Assume severe for sequence planning
                time_elapsed_minutes=time_elapsed,
            )

            sequence[facility] = treatments

        return sequence
