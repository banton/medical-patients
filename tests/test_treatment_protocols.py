"""Test treatment protocol system."""

import pytest

from medical_simulation.treatment_protocols import FacilityLevel, TreatmentCategory, TreatmentProtocolManager


class TestTreatmentProtocolManager:
    """Test treatment protocol manager functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = TreatmentProtocolManager()

    def test_protocol_exists_for_all_snomed_codes(self):
        """Test that protocols exist for key SNOMED codes."""
        snomed_codes = [
            "262574004",  # Gunshot Wound
            "125689001",  # Shrapnel
            "125596004",  # Blast
            "361220002",  # Penetrating
            "7200002",  # Burn
            "19130008",  # TBI
            "284551006",  # Amputation
            "125605004",  # Traumatic Shock
            "37782003",  # Fracture
            "125666000",  # Heat Injury
            "386661006",  # Fever
            "62315008",  # Diarrhea
        ]

        for code in snomed_codes:
            protocol = self.manager.get_protocol(code)
            assert protocol is not None, f"Missing protocol for SNOMED code {code}"
            assert protocol.snomed_code == code
            assert len(protocol.categories) > 0
            assert len(protocol.primary_treatments) > 0

    def test_get_appropriate_treatments_poi_gunshot(self):
        """Test POI treatments for gunshot wound."""
        treatments = self.manager.get_appropriate_treatments(
            snomed_code="262574004",  # Gunshot
            facility=FacilityLevel.POI,
            severity="severe",
            time_elapsed_minutes=5,
        )

        assert "tourniquet" in treatments
        assert "pressure_bandage" in treatments
        assert "hemostatic_gauze" in treatments
        # POI shouldn't have advanced treatments
        assert "damage_control_surgery" not in treatments

    def test_get_appropriate_treatments_role2_blast(self):
        """Test Role2 treatments for blast injury."""
        treatments = self.manager.get_appropriate_treatments(
            snomed_code="125596004",  # Blast
            facility=FacilityLevel.ROLE2,
            severity="critical",
            time_elapsed_minutes=45,
        )

        assert "intubation" in treatments
        assert "damage_control_surgery" in treatments
        assert "blood_transfusion" in treatments
        # Should include secondary treatments for critical
        assert len(treatments) > 3

    def test_get_appropriate_treatments_tbi(self):
        """Test treatments for traumatic brain injury."""
        treatments = self.manager.get_appropriate_treatments(
            snomed_code="19130008",  # TBI
            facility=FacilityLevel.ROLE1,
            severity="severe",
            time_elapsed_minutes=20,
        )

        assert "neurological_monitoring" in treatments
        assert "oxygen_therapy" in treatments
        # Should not have contraindicated treatments
        assert "hypotonic_fluids" not in treatments
        assert "hyperventilation" not in treatments

    def test_contraindicated_treatments_excluded(self):
        """Test that contraindicated treatments are excluded."""
        # Burn injury should not have tourniquet
        treatments = self.manager.get_appropriate_treatments(
            snomed_code="7200002",  # Burn
            facility=FacilityLevel.POI,
            severity="severe",
            time_elapsed_minutes=10,
        )

        assert "tourniquet" not in treatments
        assert "airway_positioning" in treatments

    def test_prioritize_critical_treatments(self):
        """Test treatment prioritization in critical time window."""
        treatments = self.manager.get_appropriate_treatments(
            snomed_code="125605004",  # Traumatic Shock
            facility=FacilityLevel.POI,
            severity="critical",
            time_elapsed_minutes=10,  # Within 15 min critical window
        )

        # Tourniquet should be first for hemorrhage control
        assert treatments[0] == "tourniquet"
        # Other critical treatments should follow
        assert "pressure_bandage" in treatments[:3]

    def test_generic_treatments_fallback(self):
        """Test fallback to generic treatments for unknown SNOMED codes."""
        treatments = self.manager.get_appropriate_treatments(
            snomed_code="999999999",  # Unknown code
            facility=FacilityLevel.POI,
            severity="moderate",
            time_elapsed_minutes=30,
        )

        assert len(treatments) > 0
        assert "pressure_bandage" in treatments
        assert "airway_positioning" in treatments

    def test_facility_progression_treatments(self):
        """Test treatment progression across facilities."""
        snomed_code = "262574004"  # Gunshot

        # POI treatments
        poi_treatments = self.manager.get_appropriate_treatments(
            snomed_code=snomed_code, facility=FacilityLevel.POI, severity="severe", time_elapsed_minutes=5
        )

        # Role1 treatments
        role1_treatments = self.manager.get_appropriate_treatments(
            snomed_code=snomed_code, facility=FacilityLevel.ROLE1, severity="severe", time_elapsed_minutes=30
        )

        # Role2 treatments
        role2_treatments = self.manager.get_appropriate_treatments(
            snomed_code=snomed_code, facility=FacilityLevel.ROLE2, severity="severe", time_elapsed_minutes=90
        )

        # POI should have basic treatments
        assert "tourniquet" in poi_treatments
        assert "iv_access" not in poi_treatments

        # Role1 should have intermediate treatments
        assert "iv_access" in role1_treatments
        assert "iv_fluids" in role1_treatments
        assert "damage_control_surgery" not in role1_treatments

        # Role2 should have advanced treatments
        assert "blood_transfusion" in role2_treatments
        assert "damage_control_surgery" in role2_treatments

    def test_validate_treatment_combination(self):
        """Test treatment combination validation."""
        # Valid combination for gunshot
        valid_treatments = ["tourniquet", "pressure_bandage", "iv_fluids"]
        assert self.manager.validate_treatment_combination(valid_treatments, "262574004") is True

        # Invalid combination for burn (tourniquet contraindicated)
        invalid_treatments = ["tourniquet", "burn_dressing"]
        assert self.manager.validate_treatment_combination(invalid_treatments, "7200002") is False

    def test_get_treatment_sequence(self):
        """Test getting full treatment sequence across facilities."""
        facilities = [FacilityLevel.POI, FacilityLevel.ROLE1, FacilityLevel.ROLE2, FacilityLevel.ROLE3]

        sequence = self.manager.get_treatment_sequence(
            snomed_code="284551006",  # Amputation
            facilities_visited=facilities,
        )

        assert FacilityLevel.POI in sequence
        assert FacilityLevel.ROLE3 in sequence

        # POI should have tourniquet
        assert "tourniquet" in sequence[FacilityLevel.POI]

        # Role3 should have definitive surgery
        assert "definitive_surgery" in sequence[FacilityLevel.ROLE3]

    def test_treatment_categories_mapping(self):
        """Test that treatment categories are properly mapped."""
        hemorrhage_treatments = self.manager.treatment_by_category[TreatmentCategory.HEMORRHAGE_CONTROL]

        assert "tourniquet" in hemorrhage_treatments
        assert "pressure_bandage" in hemorrhage_treatments
        assert "hemostatic_gauze" in hemorrhage_treatments
        assert "blood_transfusion" in hemorrhage_treatments

        airway_treatments = self.manager.treatment_by_category[TreatmentCategory.AIRWAY_MANAGEMENT]

        assert "airway_positioning" in airway_treatments
        assert "intubation" in airway_treatments
        assert "surgical_airway" in airway_treatments


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
