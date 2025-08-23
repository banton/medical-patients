"""Tests for Deterioration Calculator"""
from medical_simulation.deterioration_calculator import DeteriorationCalculator


def test_base_deterioration_rates():
    """Test base deterioration calculation for different severities"""
    calc = DeteriorationCalculator()

    # Test different severities
    severe = calc.calculate_base_deterioration("Battle Injury", "Severe")
    assert 25 <= severe <= 35, f"Severe should be ~30, got {severe}"

    moderate = calc.calculate_base_deterioration("Battle Injury", "Moderate")
    assert 10 <= moderate <= 15, f"Moderate should be ~12, got {moderate}"

    # Disease should have lower rates
    disease = calc.calculate_base_deterioration("Disease", "Severe")
    assert 8 <= disease <= 12, f"Disease should be ~10, got {disease}"


def test_hemorrhage_detection():
    """Test that hemorrhage injuries increase deterioration"""
    calc = DeteriorationCalculator()

    # Without hemorrhage
    base_rate = calc.calculate_base_deterioration("Battle Injury", "Severe")

    # With hemorrhage
    hemorrhage_injuries = [{"condition": "Arterial bleeding from leg"}]
    hemorrhage_rate = calc.calculate_base_deterioration(
        "Battle Injury", "Severe", hemorrhage_injuries
    )

    assert hemorrhage_rate > base_rate, "Hemorrhage should increase deterioration"
    assert hemorrhage_rate >= base_rate * 1.5, "Hemorrhage multiplier should be at least 1.5x"


def test_environmental_modifiers():
    """Test environmental factors affect deterioration"""
    calc = DeteriorationCalculator()

    base_rate = 20.0

    # Extreme cold should increase deterioration
    cold_rate = calc.apply_environmental_factors(base_rate, ["extreme_cold"])
    assert cold_rate > base_rate, "Cold should increase deterioration"

    # Multiple conditions compound
    harsh_rate = calc.apply_environmental_factors(
        base_rate, ["extreme_cold", "extreme_heat"]
    )
    assert harsh_rate > cold_rate, "Multiple conditions should compound"


def test_compound_injuries():
    """Test multiple injuries create compound deterioration"""
    calc = DeteriorationCalculator()

    # Single injury
    single = calc.calculate_compound_deterioration([
        {"type": "Battle Injury", "severity": "Moderate"}
    ])

    # Multiple injuries
    multiple = calc.calculate_compound_deterioration([
        {"type": "Battle Injury", "severity": "Severe"},
        {"type": "Battle Injury", "severity": "Moderate"}
    ])

    assert multiple > single, "Multiple injuries should deteriorate faster"
    # But not simply additive (diminishing returns)
    severe_alone = calc.calculate_base_deterioration("Battle Injury", "Severe")
    moderate_alone = calc.calculate_base_deterioration("Battle Injury", "Moderate")
    assert multiple < severe_alone + moderate_alone, "Should have diminishing returns"


def test_stabilization_windows():
    """Test time windows for medical intervention"""
    calc = DeteriorationCalculator()

    # Severe injuries have shorter windows
    severe_windows = calc.get_stabilization_window("Battle Injury", "Severe")
    assert severe_windows["platinum_10_minutes"] == 10
    assert severe_windows["golden_hour"] == 60

    # Moderate injuries have longer windows
    moderate_windows = calc.get_stabilization_window("Battle Injury", "Moderate")
    assert moderate_windows["golden_hour"] > severe_windows["golden_hour"]

    # Disease has much longer windows
    disease_windows = calc.get_stabilization_window("Disease", "Severe")
    assert disease_windows["golden_hour"] > severe_windows["golden_hour"] * 2


def test_intervention_points():
    """Test calculation of critical intervention points"""
    calc = DeteriorationCalculator()

    points = calc.calculate_intervention_points(
        deterioration_rate=20,  # 20 health/hour
        initial_health=60
    )

    # Should have intervention points
    assert len(points) > 0

    # First intervention should be for urgent treatment (50 health)
    first = points[0]
    assert first["health_threshold"] == 50
    assert 0.4 < first["time_hours"] < 0.6  # (60-50)/20 = 0.5 hours

    # Critical intervention at 30
    critical = [p for p in points if p["category"] == "critical_intervention"]
    assert len(critical) > 0
    assert 1.4 < critical[0]["time_hours"] < 1.6  # (60-30)/20 = 1.5 hours


if __name__ == "__main__":
    test_base_deterioration_rates()
    print("✅ Base deterioration test passed")

    test_hemorrhage_detection()
    print("✅ Hemorrhage detection test passed")

    test_environmental_modifiers()
    print("✅ Environmental modifiers test passed")

    test_compound_injuries()
    print("✅ Compound injuries test passed")

    test_stabilization_windows()
    print("✅ Stabilization windows test passed")

    test_intervention_points()
    print("✅ Intervention points test passed")

    print("\n✅ All deterioration calculator tests passed!")
