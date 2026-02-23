"""Tests for CSU Batch Coordinator module"""

from medical_simulation.csu_batch_coordinator import CSUBatchCoordinator
from medical_simulation.facility_capacity_manager import FacilityCapacityManager


class TestCSUBatchCoordinator:
    """Test suite for CSU Batch Coordinator"""

    def test_initialize_csu_coordinator(self):
        """Test basic initialization"""
        capacity_manager = FacilityCapacityManager()
        coordinator = CSUBatchCoordinator(capacity_manager)
        assert coordinator is not None
        assert coordinator.batch_size == 10
        assert coordinator.capacity_manager is capacity_manager

    def test_add_patient_to_batch(self):
        """Test adding patients to CSU batch"""
        capacity_manager = FacilityCapacityManager()
        coordinator = CSUBatchCoordinator(capacity_manager)

        # Add patient
        result = coordinator.add_to_batch("US-001", "T2")
        assert result["success"] is True
        assert result["batch_count"] == 1
        assert result["batch_ready"] is False

    def test_batch_ready_detection(self):
        """Test detection when batch is ready"""
        capacity_manager = FacilityCapacityManager()
        coordinator = CSUBatchCoordinator(capacity_manager)

        # Add 9 patients
        for i in range(9):
            result = coordinator.add_to_batch(f"US-{i:03d}", "T2")
            assert result["batch_ready"] is False

        # Add 10th patient - batch should be ready
        result = coordinator.add_to_batch("US-009", "T2")
        assert result["batch_ready"] is True
        assert result["batch_count"] == 10

    def test_prepare_batch_transfer(self):
        """Test preparing batch for transfer"""
        capacity_manager = FacilityCapacityManager()
        coordinator = CSUBatchCoordinator(capacity_manager)

        # Add 10 patients
        for i in range(10):
            coordinator.add_to_batch(f"US-{i:03d}", "T2")

        # Prepare batch
        batch = coordinator.prepare_batch_transfer()
        assert len(batch["patients"]) == 10
        assert batch["destination"] == "Role2"  # Default destination
        assert batch["transport_required"] is True

    def test_execute_batch_transfer(self):
        """Test executing batch transfer to Role2"""
        capacity_manager = FacilityCapacityManager()
        coordinator = CSUBatchCoordinator(capacity_manager)

        # Add 10 patients to CSU
        for i in range(10):
            capacity_manager.admit_patient(f"US-{i:03d}", "CSU")
            coordinator.add_to_batch(f"US-{i:03d}", "T2")

        # Execute transfer
        result = coordinator.execute_batch_transfer("Role2")
        assert result["success"] is True
        assert result["transferred_count"] == 10
        assert result["destination"] == "Role2"

        # Check CSU is empty
        assert capacity_manager.get_occupancy("CSU") == 0
        # Check Role2 has patients
        assert capacity_manager.get_occupancy("Role2") == 10

    def test_batch_prioritization(self):
        """Test prioritization within batch"""
        capacity_manager = FacilityCapacityManager()
        coordinator = CSUBatchCoordinator(capacity_manager)

        # Add mix of triage categories
        coordinator.add_to_batch("US-001", "T3")
        coordinator.add_to_batch("US-002", "T1")  # Urgent
        coordinator.add_to_batch("US-003", "T2")
        coordinator.add_to_batch("US-004", "T1")  # Urgent

        # Get prioritized batch
        batch = coordinator.get_prioritized_batch()
        # T1 patients should be first
        assert batch[0]["triage"] == "T1"
        assert batch[1]["triage"] == "T1"

    def test_batch_hold_time(self):
        """Test batch hold time tracking"""
        capacity_manager = FacilityCapacityManager()
        coordinator = CSUBatchCoordinator(capacity_manager)

        # Add patients and track time
        for i in range(10):
            coordinator.add_to_batch(f"US-{i:03d}", "T2")

        # Check hold time
        hold_info = coordinator.get_batch_hold_info()
        assert "first_patient_time" in hold_info
        assert "current_hold_duration" in hold_info
        assert hold_info["batch_size"] == 10

    def test_partial_batch_transfer(self):
        """Test forcing transfer of partial batch"""
        capacity_manager = FacilityCapacityManager()
        coordinator = CSUBatchCoordinator(capacity_manager)

        # Add only 5 patients
        for i in range(5):
            capacity_manager.admit_patient(f"US-{i:03d}", "CSU")
            coordinator.add_to_batch(f"US-{i:03d}", "T2")

        # Force transfer despite not full
        result = coordinator.execute_batch_transfer("Role2", force=True)
        assert result["success"] is True
        assert result["transferred_count"] == 5
        assert result["partial_batch"] is True

    def test_destination_selection(self):
        """Test automatic destination selection"""
        capacity_manager = FacilityCapacityManager()
        coordinator = CSUBatchCoordinator(capacity_manager)

        # Fill Role2 significantly
        for i in range(55):  # 55 of 60 beds
            capacity_manager.admit_patient(f"R2-{i:03d}", "Role2")

        # Add batch
        for i in range(10):
            coordinator.add_to_batch(f"US-{i:03d}", "T2")

        # Should recommend Role3 instead of Role2
        destination = coordinator.recommend_destination()
        assert destination == "Role3"  # Role2 too full

    def test_batch_metrics(self):
        """Test batch transfer metrics"""
        capacity_manager = FacilityCapacityManager()
        coordinator = CSUBatchCoordinator(capacity_manager)

        # Execute multiple batches
        for batch_num in range(3):
            # Fill batch
            for i in range(10):
                patient_id = f"B{batch_num}-{i:03d}"
                capacity_manager.admit_patient(patient_id, "CSU")
                coordinator.add_to_batch(patient_id, "T2")
            # Transfer
            coordinator.execute_batch_transfer("Role2")

        # Get metrics
        metrics = coordinator.get_batch_metrics()
        assert metrics["total_batches"] == 3
        assert metrics["total_patients_transferred"] == 30
        assert "average_batch_size" in metrics
