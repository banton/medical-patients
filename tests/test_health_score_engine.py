"""Tests for Health Score Engine"""

from medical_simulation.health_score_engine import HealthScoreEngine


def test_initial_health_scores():
    """Test initial health score assignment"""
    engine = HealthScoreEngine()

    # Test different severities (values from injuries.json config)
    severe = engine.get_initial_health("Battle Injury", "Severe")
    assert 60 <= severe <= 80, f"Severe battle injury should be 60-80 (70±10), got {severe}"

    moderate = engine.get_initial_health("Battle Injury", "Moderate")
    assert 75 <= moderate <= 85, f"Moderate should be 75-85 (80±5), got {moderate}"

    mild = engine.get_initial_health("Battle Injury", "Mild to moderate")
    assert 85 <= mild <= 95, f"Mild should be 85-95 (90±5), got {mild}"

    # Disease severe (from config: 60±5)
    disease = engine.get_initial_health("Disease", "Severe")
    assert 55 <= disease <= 65, f"Severe disease should be 55-65 (60±5), got {disease}"


def test_deterioration_without_treatment():
    """Test patient deteriorates without treatment"""
    engine = HealthScoreEngine()

    timeline = engine.calculate_health_timeline(
        injury_type="Battle Injury", severity="Severe", duration_hours=5, deterioration_rate=30, modifiers=None
    )

    # Should deteriorate each hour
    assert len(timeline) >= 2
    assert timeline[0]["health"] > timeline[1]["health"]

    # Should die within a few hours with severe injury
    final_health = timeline[-1]["health"]
    assert final_health <= 0, "Severe injury without treatment should be fatal"


def test_treatment_effects():
    """Test that treatments slow deterioration"""
    engine = HealthScoreEngine()

    # Without treatment
    timeline_no_treatment = engine.calculate_health_timeline(
        injury_type="Battle Injury", severity="Moderate", duration_hours=5, deterioration_rate=12, modifiers=None
    )

    # With treatment
    modifiers = [
        {"hour": 1, "type": "treatment", "modifier": 0.5}  # Tourniquet
    ]
    timeline_with_treatment = engine.calculate_health_timeline(
        injury_type="Battle Injury", severity="Moderate", duration_hours=5, deterioration_rate=12, modifiers=modifiers
    )

    # Patient with treatment should have better health
    assert timeline_with_treatment[-1]["health"] > timeline_no_treatment[-1]["health"]


def test_golden_hour_effect():
    """Test golden hour increases deterioration"""
    engine = HealthScoreEngine()

    timeline = engine.calculate_health_timeline(
        injury_type="Battle Injury", severity="Moderate", duration_hours=3, deterioration_rate=10, modifiers=None
    )

    # Check deterioration rates increase after golden hour
    if len(timeline) >= 3:
        # First hour normal, after that accelerated
        hour1_rate = timeline[1].get("deterioration_rate", 0)
        hour2_rate = timeline[2].get("deterioration_rate", 0)
        assert hour2_rate > hour1_rate, "Golden hour should increase deterioration"


def test_outcome_prediction():
    """Test outcome prediction from timeline"""
    engine = HealthScoreEngine()

    # Dead patient
    dead_timeline = [
        {"hour": 0, "health": 30, "status": "unstable"},
        {"hour": 1, "health": 10, "status": "critical"},
        {"hour": 2, "health": 0, "status": "dead"},
    ]
    outcome = engine.predict_outcome(dead_timeline)
    assert outcome["outcome"] == "death"
    assert outcome["category"] == "DOW"

    # Surviving patient
    survivor_timeline = [
        {"hour": 0, "health": 75, "status": "good"},
        {"hour": 1, "health": 65, "status": "stable"},
        {"hour": 2, "health": 55, "status": "stable"},
    ]
    outcome = engine.predict_outcome(survivor_timeline)
    assert outcome["outcome"] == "stable_survival"
    assert outcome["final_health"] == 55


def test_treatment_application():
    """Test applying treatments to health scores"""
    engine = HealthScoreEngine()

    # Test tourniquet
    new_health, modifier = engine.apply_treatment_effect(50, "tourniquet")
    assert new_health == 55  # +5 health
    assert modifier == 0.2  # Greatly reduces bleeding

    # Test IV fluids
    new_health, modifier = engine.apply_treatment_effect(40, "iv_fluids")
    assert new_health == 50  # +10 health
    assert modifier == 0.7  # Moderately reduces deterioration


if __name__ == "__main__":
    test_initial_health_scores()
    print("✅ Initial health scores test passed")

    test_deterioration_without_treatment()
    print("✅ Deterioration test passed")

    test_treatment_effects()
    print("✅ Treatment effects test passed")

    test_golden_hour_effect()
    print("✅ Golden hour test passed")

    test_outcome_prediction()
    print("✅ Outcome prediction test passed")

    test_treatment_application()
    print("✅ Treatment application test passed")

    print("\n✅ All health score engine tests passed!")
