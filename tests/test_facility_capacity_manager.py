"""Tests for Facility Capacity Manager module"""

from medical_simulation.facility_capacity_manager import FacilityCapacityManager


class TestFacilityCapacityManager:
    """Test suite for Facility Capacity Manager"""

    def test_initialize_facility_manager(self):
        """Test basic initialization with facility configurations"""
        manager = FacilityCapacityManager()
        assert manager is not None
        assert "Role1" in manager.facilities
        assert "Role2" in manager.facilities
        assert "Role3" in manager.facilities
        assert "CSU" in manager.facilities

    def test_get_facility_capacity(self):
        """Test getting bed capacity for each facility"""
        manager = FacilityCapacityManager()

        # Check typical capacities based on military medical doctrine
        assert manager.get_capacity("Role1") == 20  # Battalion Aid Station
        assert manager.get_capacity("Role2") == 60  # Forward Surgical Team
        assert manager.get_capacity("Role3") == 200  # Combat Support Hospital
        assert manager.get_capacity("CSU") == 50  # Casualty Staging Unit

    def test_admit_patient(self):
        """Test admitting a patient to a facility"""
        manager = FacilityCapacityManager()

        # Admit patient to Role1
        result = manager.admit_patient("US-001", "Role1")
        assert result["success"] is True
        assert result["facility"] == "Role1"
        assert manager.get_occupancy("Role1") == 1
        assert manager.get_available_beds("Role1") == 19

    def test_facility_full_rejection(self):
        """Test that full facilities reject new patients"""
        manager = FacilityCapacityManager()

        # Fill Role1 to capacity
        for i in range(20):
            result = manager.admit_patient(f"US-{i:03d}", "Role1")
            assert result["success"] is True

        # Try to admit one more patient
        result = manager.admit_patient("US-021", "Role1")
        assert result["success"] is False
        assert result["reason"] == "facility_full"
        assert manager.get_queue_length("Role1") == 1

    def test_discharge_patient(self):
        """Test discharging a patient from a facility"""
        manager = FacilityCapacityManager()

        # Admit then discharge
        manager.admit_patient("US-001", "Role1")
        assert manager.get_occupancy("Role1") == 1

        result = manager.discharge_patient("US-001", "Role1")
        assert result["success"] is True
        assert manager.get_occupancy("Role1") == 0
        assert manager.get_available_beds("Role1") == 20

    def test_transfer_patient(self):
        """Test transferring patient between facilities"""
        manager = FacilityCapacityManager()

        # Admit to Role1
        manager.admit_patient("US-001", "Role1")

        # Transfer to Role2
        result = manager.transfer_patient("US-001", "Role1", "Role2")
        assert result["success"] is True
        assert manager.get_occupancy("Role1") == 0
        assert manager.get_occupancy("Role2") == 1

    def test_queue_management(self):
        """Test queue management when facility is full"""
        manager = FacilityCapacityManager()

        # Fill Role1
        for i in range(20):
            manager.admit_patient(f"US-{i:03d}", "Role1")

        # Add patients to queue
        manager.admit_patient("US-020", "Role1")
        manager.admit_patient("US-021", "Role1")

        assert manager.get_queue_length("Role1") == 2
        queue = manager.get_queue("Role1")
        assert queue[0] == "US-020"
        assert queue[1] == "US-021"

        # Discharge one patient
        manager.discharge_patient("US-001", "Role1")

        # Process queue - first queued patient should be admitted
        processed = manager.process_queue("Role1")
        assert processed == ["US-020"]
        assert manager.get_occupancy("Role1") == 20
        assert manager.get_queue_length("Role1") == 1

    def test_get_facility_status(self):
        """Test getting comprehensive facility status"""
        manager = FacilityCapacityManager()

        # Add some patients
        manager.admit_patient("US-001", "Role1")
        manager.admit_patient("US-002", "Role1")
        manager.admit_patient("US-003", "Role2")

        status = manager.get_facility_status("Role1")
        assert status["capacity"] == 20
        assert status["occupied"] == 2
        assert status["available"] == 18
        assert status["utilization"] == 0.1  # 10% utilized
        assert status["queue_length"] == 0

    def test_get_system_overview(self):
        """Test getting overview of entire medical system"""
        manager = FacilityCapacityManager()

        # Add patients across facilities
        for i in range(5):
            manager.admit_patient(f"US-R1-{i:03d}", "Role1")
        for i in range(10):
            manager.admit_patient(f"US-R2-{i:03d}", "Role2")

        overview = manager.get_system_overview()
        assert overview["total_capacity"] == 330  # 20+60+200+50
        assert overview["total_occupied"] == 15
        assert overview["total_available"] == 315
        assert overview["system_utilization"] < 0.05  # Less than 5%

        # Check facility breakdowns
        assert "facilities" in overview
        assert overview["facilities"]["Role1"]["occupied"] == 5
        assert overview["facilities"]["Role2"]["occupied"] == 10

    def test_priority_admission(self):
        """Test priority admission for critical patients"""
        manager = FacilityCapacityManager()

        # Fill Role1
        for i in range(20):
            manager.admit_patient(f"US-{i:03d}", "Role1")

        # Add regular patient to queue
        manager.admit_patient("US-020", "Role1", priority="routine")

        # Add critical patient - should go to front of queue
        manager.admit_patient("US-021", "Role1", priority="urgent")

        queue = manager.get_queue("Role1")
        assert queue[0] == "US-021"  # Urgent patient first
        assert queue[1] == "US-020"  # Routine patient second

    def test_csu_batch_operations(self):
        """Test CSU-specific batch operations"""
        manager = FacilityCapacityManager()

        # Add patients to CSU
        patients = []
        for i in range(10):
            patient_id = f"US-CSU-{i:03d}"
            patients.append(patient_id)
            manager.admit_patient(patient_id, "CSU")

        assert manager.get_occupancy("CSU") == 10

        # Check if batch is ready (10 patients)
        batch_ready = manager.is_csu_batch_ready()
        assert batch_ready is True

        # Get batch for transfer
        batch = manager.get_csu_batch()
        assert len(batch) == 10
        assert batch == patients

    def test_facility_overflow_trigger(self):
        """Test overflow trigger thresholds"""
        manager = FacilityCapacityManager()

        # Fill Role1 to 80% (16/20 beds)
        for i in range(16):
            manager.admit_patient(f"US-{i:03d}", "Role1")

        # Check overflow status
        overflow_needed = manager.check_overflow_needed("Role1")
        assert overflow_needed is True  # 80% triggers overflow

        # Get overflow recommendations
        overflow_plan = manager.get_overflow_recommendation("Role1")
        assert overflow_plan["primary"] == "CSU"  # CSU is first overflow
        assert overflow_plan["secondary"] == "Role2"  # Then Role2
