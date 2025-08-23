"""Tests for Overflow Router module"""

from medical_simulation.facility_capacity_manager import FacilityCapacityManager
from medical_simulation.overflow_router import OverflowRouter


class TestOverflowRouter:
    """Test suite for Overflow Router functionality"""

    def test_initialize_overflow_router(self):
        """Test basic initialization"""
        capacity_manager = FacilityCapacityManager()
        router = OverflowRouter(capacity_manager)
        assert router is not None
        assert router.capacity_manager is capacity_manager

    def test_find_available_facility(self):
        """Test finding available facility for patient"""
        capacity_manager = FacilityCapacityManager()
        router = OverflowRouter(capacity_manager)

        # All facilities empty, should prefer Role1
        facility = router.find_available_facility("T2")  # Moderate injury
        assert facility == "Role1"

        # Fill Role1
        for i in range(20):
            capacity_manager.admit_patient(f"US-{i:03d}", "Role1")

        # Should now route to CSU or Role2
        facility = router.find_available_facility("T2")
        assert facility in ["CSU", "Role2"]

    def test_route_by_triage(self):
        """Test routing based on triage category"""
        capacity_manager = FacilityCapacityManager()
        router = OverflowRouter(capacity_manager)

        # T1 (urgent) should go to Role2 if available
        facility = router.route_by_triage("T1")
        assert facility == "Role2"

        # T3 (routine) should go to Role1 if available
        facility = router.route_by_triage("T3")
        assert facility == "Role1"

        # T2 (delayed) can go to Role1 or CSU
        facility = router.route_by_triage("T2")
        assert facility in ["Role1", "CSU"]

    def test_overflow_cascade(self):
        """Test overflow cascade when primary facility is full"""
        capacity_manager = FacilityCapacityManager()
        router = OverflowRouter(capacity_manager)

        # Fill Role1 completely
        for i in range(20):
            capacity_manager.admit_patient(f"US-R1-{i:03d}", "Role1")

        # Try to route T3 patient (normally Role1)
        result = router.route_patient("US-NEW-001", "T3")
        assert result["routed_to"] in ["CSU", "Role2"]  # Overflow destinations
        assert result["reason"] == "primary_full"

    def test_smart_routing_with_queue(self):
        """Test smart routing considering queue lengths"""
        capacity_manager = FacilityCapacityManager()
        router = OverflowRouter(capacity_manager)

        # Fill Role1 and add queue
        for i in range(25):  # 20 beds + 5 queue
            capacity_manager.admit_patient(f"US-R1-{i:03d}", "Role1")

        # Fill CSU partially
        for i in range(40):  # 40 of 50 beds
            capacity_manager.admit_patient(f"US-CSU-{i:03d}", "CSU")

        # Should route to Role2 (Role1 has queue, CSU almost full)
        result = router.route_patient("US-NEW-001", "T2")
        assert result["routed_to"] == "Role2"
        assert result["reason"] == "load_balancing"

    def test_critical_patient_priority(self):
        """Test critical patients get priority routing"""
        capacity_manager = FacilityCapacityManager()
        router = OverflowRouter(capacity_manager)

        # Fill Role2 partially
        for i in range(50):  # 50 of 60 beds
            capacity_manager.admit_patient(f"US-R2-{i:03d}", "Role2")

        # Critical T1 patient should still go to Role2
        result = router.route_patient("US-CRIT-001", "T1", priority="urgent")
        assert result["routed_to"] == "Role2"
        assert result["priority"] == "urgent"

    def test_mass_casualty_routing(self):
        """Test routing during mass casualty event"""
        capacity_manager = FacilityCapacityManager()
        router = OverflowRouter(capacity_manager)

        # Simulate mass casualty - route 100 patients
        results = router.mass_casualty_routing(
            [{"id": f"US-MC-{i:03d}", "triage": ["T1", "T2", "T3"][i % 3]} for i in range(100)]
        )

        # Check distribution
        facility_counts = {}
        for result in results:
            facility = result["routed_to"]
            facility_counts[facility] = facility_counts.get(facility, 0) + 1

        # Should have distributed across multiple facilities
        assert len(facility_counts) >= 2
        assert facility_counts.get("Role1", 0) <= 20  # Respect capacity

    def test_evacuation_priority(self):
        """Test evacuation priority from overwhelmed facility"""
        capacity_manager = FacilityCapacityManager()
        router = OverflowRouter(capacity_manager)

        # Fill Role1 beyond capacity (queue)
        for i in range(30):  # 20 beds + 10 queue
            capacity_manager.admit_patient(f"US-{i:03d}", "Role1")

        # Get evacuation list
        evac_list = router.get_evacuation_priority("Role1", count=5)
        assert len(evac_list) == 5
        assert evac_list[0]["reason"] == "stable_for_transfer"

    def test_facility_recommendations(self):
        """Test facility recommendations based on injury"""
        capacity_manager = FacilityCapacityManager()
        router = OverflowRouter(capacity_manager)

        # Surgical case should prefer Role2
        recommendations = router.get_facility_recommendations(injury_type="penetrating_trauma", triage="T1")
        assert recommendations[0] == "Role2"  # Has surgery capability

        # Minor injury should prefer Role1
        recommendations = router.get_facility_recommendations(injury_type="minor_laceration", triage="T3")
        assert recommendations[0] == "Role1"

    def test_transport_time_consideration(self):
        """Test routing considers transport time"""
        capacity_manager = FacilityCapacityManager()
        router = OverflowRouter(capacity_manager)

        # Critical patient with limited time
        result = router.route_patient(
            "US-CRIT-001",
            "T1",
            constraints={"max_transport_time": 15},  # 15 minutes max
        )

        # Should route to closest available facility
        assert result["routed_to"] in ["Role1", "CSU"]  # Closest options
        assert "transport_time" in result

    def test_overflow_metrics(self):
        """Test overflow routing metrics"""
        capacity_manager = FacilityCapacityManager()
        router = OverflowRouter(capacity_manager)

        # Route multiple patients
        for i in range(50):
            triage = ["T1", "T2", "T3"][i % 3]
            router.route_patient(f"US-{i:03d}", triage)

        # Get metrics
        metrics = router.get_routing_metrics()
        assert "total_routed" in metrics
        assert "overflow_events" in metrics
        assert "average_utilization" in metrics
        assert metrics["total_routed"] == 50
