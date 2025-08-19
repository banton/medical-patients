"""Tests for Transport Scheduler module"""
import pytest
from datetime import datetime, timedelta
from medical_simulation.transport_scheduler import TransportScheduler


class TestTransportScheduler:
    """Test suite for Transport Scheduler"""
    
    def test_initialize_transport_scheduler(self):
        """Test basic initialization"""
        scheduler = TransportScheduler()
        assert scheduler is not None
        assert scheduler.ground_ambulances > 0
        assert scheduler.air_ambulances > 0
    
    def test_schedule_ground_transport(self):
        """Test scheduling ground ambulance transport"""
        scheduler = TransportScheduler()
        
        transport = scheduler.schedule_transport(
            patient_id="US-001",
            from_facility="Role1",
            to_facility="Role2",
            priority="routine"
        )
        
        assert transport["transport_id"] is not None
        assert transport["vehicle_type"] == "ground_ambulance"
        assert transport["duration_minutes"] == 20  # Role1 to Role2
        assert transport["status"] == "scheduled"
    
    def test_schedule_air_transport(self):
        """Test scheduling air ambulance for critical patient"""
        scheduler = TransportScheduler()
        
        transport = scheduler.schedule_transport(
            patient_id="US-CRIT-001",
            from_facility="Role2",
            to_facility="Role3",
            priority="urgent"
        )
        
        assert transport["vehicle_type"] == "air_ambulance"  # Urgent gets air
        assert transport["duration_minutes"] == 15  # Faster than ground (45)
        assert transport["status"] == "scheduled"
    
    def test_transport_capacity_limits(self):
        """Test transport vehicle capacity limits"""
        scheduler = TransportScheduler()
        
        # Schedule all ground ambulances
        for i in range(scheduler.ground_ambulances):
            transport = scheduler.schedule_transport(
                patient_id=f"US-{i:03d}",
                from_facility="Role1",
                to_facility="Role2",
                priority="routine"
            )
            assert transport["status"] == "scheduled"
        
        # Next request should be queued
        transport = scheduler.schedule_transport(
            patient_id="US-OVERFLOW",
            from_facility="Role1",
            to_facility="Role2",
            priority="routine"
        )
        assert transport["status"] == "queued"
        assert transport["queue_position"] > 0
    
    def test_complete_transport(self):
        """Test completing a transport"""
        scheduler = TransportScheduler()
        
        # Schedule transport
        transport = scheduler.schedule_transport(
            patient_id="US-001",
            from_facility="Role1",
            to_facility="Role2",
            priority="routine"
        )
        transport_id = transport["transport_id"]
        
        # Complete transport
        result = scheduler.complete_transport(transport_id)
        assert result["success"] is True
        assert result["outcome"] == "delivered"
        
        # Vehicle should be available again
        status = scheduler.get_vehicle_availability()
        assert status["ground_available"] == scheduler.ground_ambulances
    
    def test_patient_deterioration_during_transport(self):
        """Test patient deterioration during long transport"""
        scheduler = TransportScheduler()
        
        # Schedule long transport
        transport = scheduler.schedule_transport(
            patient_id="US-001",
            from_facility="Role2",
            to_facility="Role3",
            priority="routine",
            patient_health=15  # Low health
        )
        
        # Check deterioration risk
        assert "deterioration_risk" in transport
        assert transport["deterioration_risk"] == "high"  # Low health + long transport
    
    def test_died_in_transit(self):
        """Test tracking death during transport"""
        scheduler = TransportScheduler()
        
        # Schedule transport for critical patient
        transport = scheduler.schedule_transport(
            patient_id="US-CRIT-001",
            from_facility="Role1",
            to_facility="Role3",
            priority="routine",
            patient_health=5  # Very low health
        )
        transport_id = transport["transport_id"]
        
        # Complete with death outcome
        result = scheduler.complete_transport(
            transport_id,
            outcome="died_in_transit"
        )
        assert result["success"] is True
        assert result["outcome"] == "died_in_transit"
        
        # Check metrics
        metrics = scheduler.get_transport_metrics()
        assert metrics["died_in_transit"] == 1
    
    def test_batch_transport(self):
        """Test batch transport for CSU transfers"""
        scheduler = TransportScheduler()
        
        # Schedule batch transport (10 patients)
        patients = [f"US-{i:03d}" for i in range(10)]
        transport = scheduler.schedule_batch_transport(
            patients=patients,
            from_facility="CSU",
            to_facility="Role2"
        )
        
        assert transport["vehicle_type"] == "bus"  # Batch uses bus
        assert transport["patient_count"] == 10
        assert transport["duration_minutes"] == 15  # CSU to Role2
    
    def test_transport_queue_management(self):
        """Test transport queue prioritization"""
        scheduler = TransportScheduler()
        
        # Fill all vehicles
        for i in range(scheduler.ground_ambulances + scheduler.air_ambulances):
            scheduler.schedule_transport(
                patient_id=f"FILL-{i:03d}",
                from_facility="Role1",
                to_facility="Role2",
                priority="routine"
            )
        
        # Add routine patient to queue
        routine = scheduler.schedule_transport(
            patient_id="US-ROUTINE",
            from_facility="Role1",
            to_facility="Role2",
            priority="routine"
        )
        
        # Add urgent patient - should jump queue
        urgent = scheduler.schedule_transport(
            patient_id="US-URGENT",
            from_facility="Role1",
            to_facility="Role2",
            priority="urgent"
        )
        
        assert urgent["queue_position"] < routine["queue_position"]
    
    def test_get_transport_status(self):
        """Test getting transport status"""
        scheduler = TransportScheduler()
        
        # Schedule transport
        transport = scheduler.schedule_transport(
            patient_id="US-001",
            from_facility="Role1",
            to_facility="Role2",
            priority="routine"
        )
        transport_id = transport["transport_id"]
        
        # Get status
        status = scheduler.get_transport_status(transport_id)
        assert status["patient_id"] == "US-001"
        assert status["status"] == "in_transit"
        assert "estimated_arrival" in status
    
    def test_transport_metrics(self):
        """Test transport metrics tracking"""
        scheduler = TransportScheduler()
        
        # Schedule and complete multiple transports
        for i in range(5):
            transport = scheduler.schedule_transport(
                patient_id=f"US-{i:03d}",
                from_facility="Role1",
                to_facility="Role2",
                priority="routine"
            )
            scheduler.complete_transport(transport["transport_id"])
        
        # Get metrics
        metrics = scheduler.get_transport_metrics()
        assert metrics["total_transports"] == 5
        assert metrics["completed"] == 5
        assert metrics["average_duration"] > 0
        assert "by_vehicle_type" in metrics