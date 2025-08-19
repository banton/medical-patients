"""Tests for Triage Mapper"""
from medical_simulation.triage_mapper import TriageMapper


def test_basic_triage_categories():
    """Test basic health-based triage assignment"""
    tm = TriageMapper()
    
    # T1 - Immediate (health < 40)
    cat, details = tm.calculate_triage_category(25, "Severe")
    assert cat == "T1"
    assert details["name"] == "Immediate"
    assert details["priority"] == 1
    
    # T2 - Delayed (40-70)
    cat, details = tm.calculate_triage_category(55, "Moderate")
    assert cat == "T2"
    assert details["name"] == "Delayed"
    
    # T3 - Minimal (70+)
    cat, details = tm.calculate_triage_category(85, "Mild")
    assert cat == "T3"
    assert details["name"] == "Minimal"
    
    # T4 - Expectant (health < 10)
    cat, details = tm.calculate_triage_category(5, "Severe")
    assert cat == "T4"
    assert details["name"] == "Expectant"


def test_injury_overrides():
    """Test specific injuries override health-based triage"""
    tm = TriageMapper()
    
    # Arterial bleeding forces T1 even with moderate health
    cat, _ = tm.calculate_triage_category(
        60, "Moderate", ["arterial_bleeding"]
    )
    assert cat == "T1", "Arterial bleeding should force T1"
    
    # Massive head trauma with low health becomes T4
    cat, _ = tm.calculate_triage_category(
        15, "Severe", ["massive_head_trauma"]
    )
    assert cat == "T4", "Massive head trauma with low health should be T4"
    
    # Simple fracture stays T3 if health good
    cat, _ = tm.calculate_triage_category(
        75, "Mild", ["simple_fracture"]
    )
    assert cat == "T3"


def test_mass_casualty_adjustments():
    """Test triage changes during mass casualty events"""
    tm = TriageMapper()
    
    # Normal triage
    normal_cat, _ = tm.calculate_triage_category(
        35, "Severe", ["hemorrhage"], mass_casualty=False
    )
    
    # Mass casualty - same patient might be triaged differently
    mass_cat, details = tm.calculate_triage_category(
        12, "Severe", ["hemorrhage"], mass_casualty=True
    )
    
    # Very low health + severe in mass casualty might become T4
    assert details["mass_casualty_adjusted"] is True
    
    # Borderline T2 becomes T3 in mass casualty
    cat, _ = tm.calculate_triage_category(
        68, "Mild to moderate", [], mass_casualty=True
    )
    assert cat == "T3", "Borderline T2 should become T3 in mass casualty"


def test_bed_assignments():
    """Test bed type assignments match triage categories"""
    tm = TriageMapper()
    
    assert tm.get_bed_assignment("T1") == "T1_bed"
    assert tm.get_bed_assignment("T2") == "T2_bed"
    assert tm.get_bed_assignment("T3") == "T3_bed"
    assert tm.get_bed_assignment("T4") is None  # No bed for expectant


def test_treatment_priority_sorting():
    """Test patients are sorted by priority correctly"""
    tm = TriageMapper()
    
    patients = [
        {"id": "A", "health_score": 60, "triage_category": "T2"},
        {"id": "B", "health_score": 25, "triage_category": "T1"},
        {"id": "C", "health_score": 80, "triage_category": "T3"},
        {"id": "D", "health_score": 15, "triage_category": "T1"},
        {"id": "E", "health_score": 5, "triage_category": "T4"},
    ]
    
    sorted_patients = tm.calculate_treatment_priority(patients)
    
    # Check order: T1 patients first, sorted by health within category
    order = [p["id"] for p in sorted_patients]
    
    # D should be first (T1 with lowest health)
    assert order[0] == "D", "Lowest health T1 should be first"
    # B should be second (T1 with higher health)
    assert order[1] == "B", "Higher health T1 should be second"
    # T2 patient should be third
    assert order[2] == "A", "T2 should come after T1"
    # T3 should be fourth
    assert order[3] == "C", "T3 should come after T2"
    # T4 should be last
    assert order[4] == "E", "T4 should be last"


def test_survival_probability():
    """Test survival probability calculations"""
    tm = TriageMapper()
    
    # T1 with immediate treatment
    prob = tm.estimate_survival_probability("T1", 30, has_treatment=True)
    assert 0.7 < prob < 1.0, "T1 with treatment should have good survival"
    
    # T1 with excessive wait
    prob_delayed = tm.estimate_survival_probability("T1", 180, has_treatment=False)
    assert prob_delayed < 0.5, "T1 with long wait should have poor survival"
    
    # T3 should have excellent survival
    prob_minor = tm.estimate_survival_probability("T3", 60, has_treatment=False)
    assert prob_minor > 0.95, "T3 should have excellent survival"
    
    # T4 has poor prognosis regardless
    prob_expectant = tm.estimate_survival_probability("T4", 10, has_treatment=True)
    assert prob_expectant < 0.1, "T4 should have very poor survival"


def test_triage_wait_times():
    """Test maximum wait times for each category"""
    tm = TriageMapper()
    
    categories = tm.categories
    
    # T1 should have shortest max wait
    assert categories["T1"]["max_wait_minutes"] <= 60
    # T2 can wait a few hours
    assert 120 <= categories["T2"]["max_wait_minutes"] <= 360
    # T3 can wait much longer
    assert categories["T3"]["max_wait_minutes"] >= 720
    # T4 has no wait (comfort care only)
    assert categories["T4"]["max_wait_minutes"] == 0


if __name__ == "__main__":
    test_basic_triage_categories()
    print("✅ Basic triage categories test passed")
    
    test_injury_overrides()
    print("✅ Injury overrides test passed")
    
    test_mass_casualty_adjustments()
    print("✅ Mass casualty adjustments test passed")
    
    test_bed_assignments()
    print("✅ Bed assignments test passed")
    
    test_treatment_priority_sorting()
    print("✅ Treatment priority sorting test passed")
    
    test_survival_probability()
    print("✅ Survival probability test passed")
    
    test_triage_wait_times()
    print("✅ Triage wait times test passed")
    
    print("\n✅ All triage mapper tests passed!")