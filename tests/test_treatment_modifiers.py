"""Tests for Treatment Modifiers"""

from medical_simulation.treatment_modifiers import TreatmentModifiers


def test_facility_capabilities():
    """Test different facilities have appropriate treatments"""
    tm = TreatmentModifiers()

    # POI has only basic interventions
    poi_treatments = tm.get_available_treatments("poi")
    assert "tourniquet" in poi_treatments
    assert "major_surgery" not in poi_treatments

    # Role2 has surgical capability
    role2_treatments = tm.get_available_treatments("role2")
    assert "surgical_stabilization" in role2_treatments
    assert "blood_transfusion" in role2_treatments
    assert "major_surgery" not in role2_treatments  # Only at Role3

    # Role3 has everything
    role3_treatments = tm.get_available_treatments("role3")
    assert "major_surgery" in role3_treatments
    assert "organ_repair" in role3_treatments


def test_condition_specific_treatments():
    """Test treatments filtered by patient condition"""
    tm = TreatmentModifiers()

    # Extremity hemorrhage - tourniquet appropriate
    leg_treatments = tm.get_available_treatments("role1", "femoral artery bleeding")
    assert "tourniquet" in leg_treatments
    assert "iv_fluids" in leg_treatments

    # Chest wound - NO tourniquet!
    chest_treatments = tm.get_available_treatments("role1", "chest wound with pneumothorax")
    assert "tourniquet" not in chest_treatments, "Tourniquet should NOT be available for chest wounds"
    assert "pressure_dressing" in chest_treatments
    assert "iv_fluids" in chest_treatments

    # Abdominal injury - NO tourniquet!
    abdomen_treatments = tm.get_available_treatments("role2", "abdominal trauma")
    assert "tourniquet" not in abdomen_treatments
    assert "pressure_dressing" in abdomen_treatments
    assert "surgical_stabilization" in abdomen_treatments

    # Head injury - very limited options
    head_treatments = tm.get_available_treatments("role1", "head trauma")
    assert "tourniquet" not in head_treatments
    assert "pressure_dressing" in head_treatments
    assert len(head_treatments) <= 3  # Limited options for head injuries


def test_treatment_application():
    """Test applying treatments modifies health and deterioration"""
    tm = TreatmentModifiers()

    # Apply tourniquet to bleeding patient
    initial_health = 30
    initial_deterioration = 25.0

    new_health, new_deterioration, info = tm.apply_treatment("tourniquet", initial_health, initial_deterioration)

    assert new_health == 35  # +5 health boost
    assert new_deterioration == 5.0  # 25 * 0.2 = 5
    assert info["name"] == "tourniquet"
    assert info["duration_hours"] == 2

    # Apply blood transfusion
    new_health2, new_deterioration2, info2 = tm.apply_treatment("blood_transfusion", new_health, new_deterioration)

    assert new_health2 == 55  # +20 health boost
    assert new_deterioration2 == 2.5  # 5 * 0.5 = 2.5


def test_stacked_treatments():
    """Test multiple treatments stack with diminishing returns"""
    tm = TreatmentModifiers()

    # Single treatment
    single = tm.calculate_stacked_effects([{"name": "tourniquet"}])
    assert abs(single - 0.2) < 0.01  # Tourniquet alone (with floating point tolerance)

    # Two treatments
    double = tm.calculate_stacked_effects([{"name": "tourniquet"}, {"name": "iv_fluids"}])
    # Second treatment at 80% effectiveness
    # 0.2 * (1 - (1-0.7)*0.8) = 0.2 * 0.76 = 0.152
    assert 0.15 < double < 0.16

    # Three treatments show further diminishing returns
    triple = tm.calculate_stacked_effects([{"name": "tourniquet"}, {"name": "iv_fluids"}, {"name": "morphine"}])
    assert triple < double  # More treatments, lower combined modifier
    assert triple >= 0.1  # Never below 10%


def test_treatment_prioritization():
    """Test treatments are prioritized by patient condition"""
    tm = TreatmentModifiers()

    # Critical patient
    available = ["morphine", "tourniquet", "antibiotics", "iv_fluids"]
    priority = tm.get_treatment_priority(available, patient_health=20, deterioration_rate=30)

    # Tourniquet should be first for critical bleeding patient
    assert priority[0] == "tourniquet"
    assert "iv_fluids" in priority[:2]  # IV fluids high priority
    assert "antibiotics" in priority[-2:]  # Antibiotics lower priority

    # Stable patient
    priority_stable = tm.get_treatment_priority(available, patient_health=70, deterioration_rate=5)

    # Different priority for stable patient
    assert priority_stable != priority


def test_treatment_duration():
    """Test treatments have appropriate durations"""
    tm = TreatmentModifiers()

    treatments = tm.treatments

    # Quick interventions
    assert treatments["tourniquet"]["time_to_apply_minutes"] <= 2
    assert treatments["morphine"]["time_to_apply_minutes"] <= 5

    # Longer procedures
    assert treatments["surgical_stabilization"]["time_to_apply_minutes"] >= 30
    assert treatments["major_surgery"]["time_to_apply_minutes"] >= 120

    # Duration makes sense
    assert treatments["tourniquet"]["duration_hours"] < treatments["iv_fluids"]["duration_hours"]
    assert treatments["antibiotics"]["duration_hours"] >= 24


if __name__ == "__main__":
    test_facility_capabilities()
    print("✅ Facility capabilities test passed")

    test_condition_specific_treatments()
    print("✅ Condition-specific treatments test passed")

    test_treatment_application()
    print("✅ Treatment application test passed")

    test_stacked_treatments()
    print("✅ Stacked treatments test passed")

    test_treatment_prioritization()
    print("✅ Treatment prioritization test passed")

    test_treatment_duration()
    print("✅ Treatment duration test passed")

    print("\n✅ All treatment modifier tests passed!")
