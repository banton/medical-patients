"""Tests for Death Tracker module"""

from medical_simulation.death_tracker import DeathTracker


class TestDeathTracker:
    """Test suite for Death Tracker functionality"""

    def test_initialize_death_tracker(self):
        """Test basic initialization"""
        tracker = DeathTracker()
        assert tracker is not None
        assert tracker.death_categories == ["KIA", "DOW", "DNB", "Non-Battle Death"]

    def test_categorize_death_kia(self):
        """Test KIA (Killed in Action) categorization - death at POI"""
        tracker = DeathTracker()

        # Death at T+5 minutes at POI
        death_info = {
            "time_of_death": 5,  # minutes from injury
            "location": "POI",
            "health_at_death": 0,
            "injury_type": "Battle Injury",
        }

        category = tracker.categorize_death(death_info)
        assert category == "KIA"

    def test_categorize_death_dow_role1(self):
        """Test DOW (Died of Wounds) at Role1"""
        tracker = DeathTracker()

        death_info = {
            "time_of_death": 45,  # minutes from injury
            "location": "Role1",
            "health_at_death": 0,
            "injury_type": "Battle Injury",
        }

        category = tracker.categorize_death(death_info)
        assert category == "DOW"

    def test_categorize_death_dow_role2(self):
        """Test DOW at Role2"""
        tracker = DeathTracker()

        death_info = {
            "time_of_death": 180,  # 3 hours from injury
            "location": "Role2",
            "health_at_death": 0,
            "injury_type": "Battle Injury",
        }

        category = tracker.categorize_death(death_info)
        assert category == "DOW"

    def test_categorize_death_dnb(self):
        """Test DNB (Disease Non-Battle) death"""
        tracker = DeathTracker()

        death_info = {
            "time_of_death": 4320,  # 3 days
            "location": "Role3",
            "health_at_death": 0,
            "injury_type": "Disease",
        }

        category = tracker.categorize_death(death_info)
        assert category == "DNB"

    def test_categorize_non_battle_death(self):
        """Test Non-Battle Death (accidents, etc)"""
        tracker = DeathTracker()

        death_info = {
            "time_of_death": 60,
            "location": "Role1",
            "health_at_death": 0,
            "injury_type": "Non-Battle Injury",
        }

        category = tracker.categorize_death(death_info)
        assert category == "Non-Battle Death"

    def test_track_patient_death(self):
        """Test tracking a patient death with full details"""
        tracker = DeathTracker()

        patient_data = {
            "id": "US-001",
            "injury_type": "Battle Injury",
            "initial_health": 25,
            "health_timeline": [
                {"time": 0, "health": 25, "location": "POI"},
                {"time": 15, "health": 18, "location": "POI"},
                {"time": 30, "health": 10, "location": "Role1"},
                {"time": 45, "health": 0, "location": "Role1"},
            ],
        }

        death_record = tracker.track_death(patient_data)

        assert death_record["patient_id"] == "US-001"
        assert death_record["death_category"] == "DOW"
        assert death_record["time_of_death"] == 45
        assert death_record["location_of_death"] == "Role1"
        assert death_record["preventable"] is not None

    def test_determine_preventability_golden_hour(self):
        """Test determining if death was preventable (golden hour)"""
        tracker = DeathTracker()

        # Death within golden hour without treatment - potentially preventable
        death_info = {
            "time_of_death": 45,  # Within golden hour
            "treatments_applied": [],
            "location": "Role1",
            "initial_health": 30,
        }

        preventable = tracker.determine_preventability(death_info)
        assert preventable is True

        # Death within golden hour WITH treatment - not preventable
        death_info_treated = {
            "time_of_death": 45,
            "treatments_applied": ["tourniquet", "IV fluids"],
            "location": "Role1",
            "initial_health": 15,
        }

        preventable_treated = tracker.determine_preventability(death_info_treated)
        assert preventable_treated is False

    def test_determine_preventability_late_death(self):
        """Test preventability for deaths after golden hour"""
        tracker = DeathTracker()

        # Death after golden hour - generally not preventable
        death_info = {
            "time_of_death": 180,  # 3 hours
            "treatments_applied": ["tourniquet"],
            "location": "Role2",
            "initial_health": 25,
        }

        preventable = tracker.determine_preventability(death_info)
        assert preventable is False

    def test_get_death_statistics(self):
        """Test getting aggregate death statistics"""
        tracker = DeathTracker()

        # Track multiple deaths
        patients = [
            {
                "id": "US-001",
                "injury_type": "Battle Injury",
                "initial_health": 15,
                "health_timeline": [
                    {"time": 0, "health": 15, "location": "POI"},
                    {"time": 10, "health": 0, "location": "POI"},
                ],
            },
            {
                "id": "US-002",
                "injury_type": "Battle Injury",
                "initial_health": 30,
                "health_timeline": [
                    {"time": 0, "health": 30, "location": "POI"},
                    {"time": 60, "health": 0, "location": "Role1"},
                ],
            },
            {
                "id": "US-003",
                "injury_type": "Disease",
                "initial_health": 60,
                "health_timeline": [
                    {"time": 0, "health": 60, "location": "Role2"},
                    {"time": 2880, "health": 0, "location": "Role3"},
                ],
            },
        ]

        for patient in patients:
            tracker.track_death(patient)

        stats = tracker.get_statistics()

        assert stats["total_deaths"] == 3
        assert stats["by_category"]["KIA"] == 1
        assert stats["by_category"]["DOW"] == 1
        assert stats["by_category"]["DNB"] == 1
        assert "preventable_deaths" in stats
        assert "mortality_rate" in stats

    def test_export_death_summary(self):
        """Test exporting death tracking summary"""
        tracker = DeathTracker()

        # Track a death
        patient = {
            "id": "UK-001",
            "injury_type": "Battle Injury",
            "initial_health": 20,
            "health_timeline": [
                {"time": 0, "health": 20, "location": "POI"},
                {"time": 30, "health": 0, "location": "POI"},
            ],
        }

        tracker.track_death(patient)
        summary = tracker.export_summary()

        assert "deaths" in summary
        assert "statistics" in summary
        assert len(summary["deaths"]) == 1
        assert summary["deaths"][0]["patient_id"] == "UK-001"
