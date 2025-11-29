"""
Death Tracker for Medical Simulation
Categorizes and tracks patient deaths (KIA, DOW, DNB, Non-Battle)
"""

from typing import Any, Dict, List


class DeathTracker:
    """
    Tracks and categorizes patient deaths according to military medical standards.

    Death Categories:
    - KIA (Killed in Action): Death at POI from battle injuries
    - DOW (Died of Wounds): Death at medical facility from battle injuries
    - DNB (Disease Non-Battle): Death from disease
    - Non-Battle Death: Death from non-battle injuries/accidents
    """

    def __init__(self):
        """Initialize death tracking system"""
        self.death_categories = ["KIA", "DOW", "DNB", "Non-Battle Death"]
        self.tracked_deaths: List[Dict] = []
        self.golden_hour_threshold = 60  # minutes

    def categorize_death(self, death_info: Dict[str, Any]) -> str:
        """
        Categorize a death based on location, time, and injury type.

        Args:
            death_info: Dictionary containing:
                - time_of_death: Minutes from injury
                - location: Where death occurred (POI, Role1, Role2, etc)
                - injury_type: "Battle Injury", "Non-Battle Injury", or "Disease"

        Returns:
            Death category string
        """
        injury_type = death_info.get("injury_type", "Unknown")
        location = death_info.get("location", "Unknown")

        # Disease deaths are always DNB
        if injury_type == "Disease":
            return "DNB"

        # Non-battle injuries are Non-Battle Deaths
        if injury_type == "Non-Battle Injury":
            return "Non-Battle Death"

        # Battle injuries categorized by location
        if injury_type == "Battle Injury":
            if location == "POI":
                return "KIA"
            return "DOW"

        # Default for unknown cases
        return "Non-Battle Death"

    def track_death(self, patient_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Track a patient death with full details.

        Args:
            patient_data: Dictionary containing either:
                Format 1 (from orchestrator):
                    - patient_id: Patient identifier
                    - time_of_death: When death occurred (datetime or minutes)
                    - location: Where death occurred
                    - cause: Cause of death
                    - injury_type: Type of injury
                    - initial_health: Starting health score
                    - final_health: Health at death
                    - treatments: List of treatments received
                Format 2 (legacy):
                    - id: Patient identifier
                    - injury_type: Type of injury
                    - initial_health: Starting health score
                    - health_timeline: List of health states over time

        Returns:
            Death record with category and analysis
        """
        # Handle Format 1 (from orchestrator) - preferred format
        if "patient_id" in patient_data or "time_of_death" in patient_data:
            # Direct format from orchestrator
            death_info = {
                "time_of_death": patient_data.get("time_of_death", 0),
                "location": patient_data.get("location", "Unknown"),
                "health_at_death": patient_data.get("final_health", 0),
                "injury_type": patient_data.get("injury_type", "Unknown"),
            }
            patient_id = patient_data.get("patient_id", patient_data.get("id", "Unknown"))
            initial_health = patient_data.get("initial_health", 50)
            treatments = patient_data.get("treatments", patient_data.get("treatments_applied", []))
        else:
            # Handle Format 2 (legacy with health_timeline)
            timeline = patient_data.get("health_timeline", [])
            if not timeline:
                return {}

            # Find death event (health = 0)
            death_event = None
            for event in timeline:
                if event.get("health", 100) <= 0:
                    death_event = event
                    break

            if not death_event:
                # No death found in timeline
                return {}

            death_info = {
                "time_of_death": death_event.get("time", 0),
                "location": death_event.get("location", "Unknown"),
                "health_at_death": death_event.get("health", 0),
                "injury_type": patient_data.get("injury_type", "Unknown"),
            }
            patient_id = patient_data.get("id", "Unknown")
            initial_health = patient_data.get("initial_health", 50)
            treatments = patient_data.get("treatments_applied", [])

        # Categorize the death
        category = self.categorize_death(death_info)

        # Determine preventability
        preventability_info = {
            "time_of_death": death_info["time_of_death"],
            "treatments_applied": treatments,
            "location": death_info["location"],
            "initial_health": initial_health,
        }
        preventable = self.determine_preventability(preventability_info)

        # Create death record
        death_record = {
            "patient_id": patient_id,
            "death_category": category,
            "time_of_death": death_info["time_of_death"],
            "location_of_death": death_info["location"],
            "preventable": preventable,
            "injury_type": death_info["injury_type"],
            "initial_health": initial_health,
            "cause": patient_data.get("cause", "Unknown"),
        }

        # Store the record
        self.tracked_deaths.append(death_record)

        return death_record

    def determine_preventability(self, death_info: Dict[str, Any]) -> bool:
        """
        Determine if a death was potentially preventable.

        Criteria for preventable deaths:
        - Occurred within golden hour (60 min) without treatment
        - Initial health > 20 (not expectant category)
        - At a location where treatment was available

        Args:
            death_info: Dictionary with death details

        Returns:
            True if death was potentially preventable
        """
        time_of_death = death_info.get("time_of_death", 0)
        treatments = death_info.get("treatments_applied", [])
        initial_health = death_info.get("initial_health", 50)

        # Deaths with very low initial health are not preventable
        if initial_health < 20:
            return False

        # Deaths after golden hour are generally not preventable
        if time_of_death > self.golden_hour_threshold:
            return False

        # Deaths within golden hour without treatment are potentially preventable
        return time_of_death <= self.golden_hour_threshold and not treatments

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get aggregate statistics on tracked deaths.

        Returns:
            Dictionary with death statistics
        """
        if not self.tracked_deaths:
            return {
                "total_deaths": 0,
                "by_category": dict.fromkeys(self.death_categories, 0),
                "preventable_deaths": 0,
                "mortality_rate": 0.0,
            }

        # Count by category
        by_category = dict.fromkeys(self.death_categories, 0)
        preventable_count = 0

        for death in self.tracked_deaths:
            category = death.get("death_category", "Unknown")
            if category in by_category:
                by_category[category] += 1

            if death.get("preventable", False):
                preventable_count += 1

        return {
            "total_deaths": len(self.tracked_deaths),
            "by_category": by_category,
            "preventable_deaths": preventable_count,
            "mortality_rate": preventable_count / len(self.tracked_deaths) if self.tracked_deaths else 0.0,
        }

    def export_summary(self) -> Dict[str, Any]:
        """
        Export complete death tracking summary.

        Returns:
            Dictionary with all death records and statistics
        """
        return {"deaths": self.tracked_deaths, "statistics": self.get_statistics()}
