"""
Diagnostic Uncertainty Module - Hidden Markov Model Implementation

This module implements probabilistic diagnostic accuracy that improves as patients
move through the military medical facility chain (POI -> Role1 -> Role2 -> Role3 -> Role4).

Mathematical Model:
- HMM with diagnostic states and SNOMED code observations
- Facility-specific emission probabilities (65% POI -> 98% Role4)
- Confusion matrices for realistic misdiagnosis patterns
- Environmental and severity modifiers

Author: Medical SME Agent + Probabilistic Math SME Agent
Version: 1.0.0
"""

import json
import os
import random
from typing import Any, Dict, List, Optional

import numpy as np


class DiagnosticUncertaintyEngine:
    """
    Implements HMM-based diagnostic uncertainty with facility-specific accuracy rates.
    
    Key Features:
    - Progressive diagnostic accuracy: 65% (POI) -> 98% (Role4)
    - Realistic confusion matrices for common misdiagnoses
    - Environmental and severity modifiers
    - Time-based diagnostic improvement
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the diagnostic uncertainty engine.
        
        Args:
            config_path: Path to confusion_matrices.json config file
        """
        self.config_path = config_path or os.path.join(
            os.path.dirname(__file__), "confusion_matrices.json"
        )
        self.confusion_data = self._load_confusion_matrices()

        # Extract key configuration
        self.facility_accuracy = self.confusion_data["diagnostic_accuracy"]
        self.confusion_matrices = self.confusion_data["confusion_matrices"]
        self.hmm_params = self.confusion_data["hmm_parameters"]
        self.improvement_factors = self.confusion_data["diagnostic_improvement_factors"]
        self.severity_impact = self.confusion_data["severity_impact"]
        self.environmental_factors = self.confusion_data["environmental_factors"]

        # HMM state tracking per patient
        self.patient_diagnostic_states = {}

    def _load_confusion_matrices(self) -> Dict[str, Any]:
        """Load confusion matrices configuration from JSON file."""
        try:
            with open(self.config_path) as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Confusion matrices config not found: {self.config_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in confusion matrices config: {e}")

    def get_diagnostic_accuracy(self, facility: str, modifiers: Optional[Dict[str, Any]] = None) -> float:
        """
        Calculate diagnostic accuracy for a facility with modifiers.
        
        Args:
            facility: Military medical facility (POI, Role1, Role2, Role3, Role4)
            modifiers: Optional dict with severity, environmental factors, etc.
            
        Returns:
            Diagnostic accuracy probability [0.0, 1.0]
        """
        base_accuracy = self.facility_accuracy.get(facility, 0.65)

        if not modifiers:
            return base_accuracy

        # Apply severity modifier
        if "triage_category" in modifiers:
            triage = modifiers["triage_category"]
            severity_mod = self.severity_impact.get(triage, {}).get("modifier", 0.0)
            base_accuracy += severity_mod

        # Apply environmental modifiers
        for env_factor, impact in self.environmental_factors.items():
            if modifiers.get(env_factor, False):
                base_accuracy += impact

        # Apply time-with-patient improvement
        if "time_with_patient_hours" in modifiers:
            time_hours = modifiers["time_with_patient_hours"]
            time_params = self.improvement_factors["time_with_patient"].get(facility, {})
            if time_params:
                max_improvement = time_params.get("max_improvement", 0.0)
                time_factor = time_params.get("time_factor", 0.1)
                time_improvement = max_improvement * (1 - np.exp(-time_factor * time_hours))
                base_accuracy += time_improvement

        # Clamp to valid probability range
        return max(0.0, min(1.0, base_accuracy))

    def diagnose_condition(
        self,
        true_condition_code: str,
        facility: str,
        patient_id: str,
        modifiers: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform probabilistic diagnosis with potential misdiagnosis.
        
        Args:
            true_condition_code: Actual SNOMED code of condition
            facility: Current medical facility
            patient_id: Unique patient identifier
            modifiers: Environmental/patient factors affecting diagnosis
            
        Returns:
            Dict with diagnosed_code, confidence, true_positive, misdiagnosis_type
        """
        # Calculate diagnostic accuracy for this facility/context
        accuracy = self.get_diagnostic_accuracy(facility, modifiers)

        # Determine if diagnosis is correct
        is_correct = random.random() < accuracy

        if is_correct:
            return {
                "diagnosed_code": true_condition_code,
                "confidence": accuracy,
                "true_positive": True,
                "misdiagnosis_type": None,
                "facility": facility,
                "diagnostic_accuracy": accuracy
            }

        # Handle misdiagnosis - select from confusion matrix
        misdiagnosed_code = self._select_misdiagnosis(true_condition_code, facility)

        return {
            "diagnosed_code": misdiagnosed_code,
            "confidence": accuracy,
            "true_positive": False,
            "misdiagnosis_type": "facility_confusion",
            "true_condition": true_condition_code,
            "facility": facility,
            "diagnostic_accuracy": accuracy
        }

    def _select_misdiagnosis(self, true_condition_code: str, facility: str) -> str:
        """
        Select a misdiagnosis from the confusion matrix.
        
        Args:
            true_condition_code: True SNOMED code
            facility: Current medical facility
            
        Returns:
            SNOMED code of misdiagnosed condition
        """
        facility_matrix = self.confusion_matrices.get(facility, {})
        condition_misdiagnoses = facility_matrix.get("common_misdiagnoses", {}).get(
            true_condition_code, {}
        ).get("misdiagnosed_as", [])

        if not condition_misdiagnoses:
            # Fallback to generic misdiagnosis pattern
            return self._generic_misdiagnosis(true_condition_code)

        # Select weighted random misdiagnosis
        total_prob = sum(item["probability"] for item in condition_misdiagnoses)

        if total_prob == 0:
            return self._generic_misdiagnosis(true_condition_code)

        # Normalize probabilities
        normalized_probs = [item["probability"] / total_prob for item in condition_misdiagnoses]

        # Select misdiagnosis using weighted random choice
        selected_idx = np.random.choice(len(condition_misdiagnoses), p=normalized_probs)
        return condition_misdiagnoses[selected_idx]["code"]

    def _generic_misdiagnosis(self, true_condition_code: str) -> str:
        """
        Fallback generic misdiagnosis patterns.
        
        Args:
            true_condition_code: True SNOMED code
            
        Returns:
            Generic misdiagnosed SNOMED code
        """
        # Common generic misdiagnoses for unknown conditions
        generic_misdiagnoses = [
            "22253000",   # Pain
            "125667009",  # Contusion
            "422587007",  # Nausea
            "271807003",  # Rash
            "386807006"   # Memory impairment
        ]
        return random.choice(generic_misdiagnoses)

    def update_diagnosis_with_progression(
        self,
        patient_id: str,
        current_diagnosis: str,
        new_facility: str,
        additional_info: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Update diagnosis as patient progresses through facilities.
        
        Args:
            patient_id: Unique patient identifier
            current_diagnosis: Current diagnosed condition code
            new_facility: New facility with better diagnostic capability
            additional_info: List of additional diagnostic information available
            
        Returns:
            Updated diagnosis with improvement probability
        """
        # Get previous diagnostic state
        if patient_id not in self.patient_diagnostic_states:
            self.patient_diagnostic_states[patient_id] = {
                "diagnostic_history": [],
                "current_state": "initial_assessment"
            }

        patient_state = self.patient_diagnostic_states[patient_id]

        # Calculate improvement probability
        old_accuracy = self.facility_accuracy.get(patient_state["diagnostic_history"][-1]["facility"] if patient_state["diagnostic_history"] else "POI", 0.65)
        new_accuracy = self.facility_accuracy.get(new_facility, 0.65)

        improvement_prob = new_accuracy - old_accuracy

        # Apply additional information modifiers
        if additional_info:
            for info_type in additional_info:
                if info_type in self.improvement_factors["additional_information"]:
                    improvement_prob += self.improvement_factors["additional_information"][info_type]

        # Update HMM state
        self._update_hmm_state(patient_id)

        # Record diagnostic progression
        diagnostic_update = {
            "facility": new_facility,
            "diagnosis": current_diagnosis,
            "accuracy": new_accuracy,
            "improvement_probability": max(0.0, improvement_prob),
            "hmm_state": patient_state["current_state"],
            "additional_info": additional_info or []
        }

        patient_state["diagnostic_history"].append(diagnostic_update)

        return diagnostic_update

    def _update_hmm_state(self, patient_id: str):
        """
        Update Hidden Markov Model state for patient diagnostic progression.
        
        Args:
            patient_id: Unique patient identifier
        """
        if patient_id not in self.patient_diagnostic_states:
            return

        current_state = self.patient_diagnostic_states[patient_id]["current_state"]
        transition_probs = self.hmm_params["transition_probabilities"][current_state]

        # Select next state based on transition probabilities
        states = list(transition_probs.keys())
        probabilities = list(transition_probs.values())

        next_state = np.random.choice(states, p=probabilities)
        self.patient_diagnostic_states[patient_id]["current_state"] = next_state

    def get_diagnostic_confidence(self, patient_id: str) -> Dict[str, Any]:
        """
        Get current diagnostic confidence for a patient.
        
        Args:
            patient_id: Unique patient identifier
            
        Returns:
            Dict with confidence metrics and diagnostic history
        """
        if patient_id not in self.patient_diagnostic_states:
            return {"confidence": 0.0, "diagnostic_history": [], "hmm_state": "initial_assessment"}

        patient_state = self.patient_diagnostic_states[patient_id]

        # Calculate overall confidence from diagnostic history
        if not patient_state["diagnostic_history"]:
            return {"confidence": 0.0, "diagnostic_history": [], "hmm_state": patient_state["current_state"]}

        latest_diagnosis = patient_state["diagnostic_history"][-1]

        return {
            "confidence": latest_diagnosis["accuracy"],
            "diagnostic_history": patient_state["diagnostic_history"],
            "hmm_state": patient_state["current_state"],
            "improvement_trend": self._calculate_improvement_trend(patient_state["diagnostic_history"])
        }

    def _calculate_improvement_trend(self, diagnostic_history: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate diagnostic improvement trend from history.
        
        Args:
            diagnostic_history: List of diagnostic events
            
        Returns:
            Dict with trend metrics
        """
        if len(diagnostic_history) < 2:
            return {"trend": 0.0, "total_improvement": 0.0}

        accuracies = [event["accuracy"] for event in diagnostic_history]
        total_improvement = accuracies[-1] - accuracies[0]

        # Calculate linear trend
        trend = np.polyfit(range(len(accuracies)), accuracies, 1)[0] if len(accuracies) > 1 else 0.0

        return {
            "trend": trend,
            "total_improvement": total_improvement,
            "initial_accuracy": accuracies[0],
            "final_accuracy": accuracies[-1]
        }

    def reset_patient_state(self, patient_id: str):
        """
        Reset diagnostic state for a patient (useful for new scenarios).
        
        Args:
            patient_id: Unique patient identifier
        """
        if patient_id in self.patient_diagnostic_states:
            del self.patient_diagnostic_states[patient_id]


# Utility functions for integration

def create_diagnostic_uncertainty_engine(config_path: Optional[str] = None) -> DiagnosticUncertaintyEngine:
    """
    Factory function to create diagnostic uncertainty engine.
    
    Args:
        config_path: Optional path to confusion matrices config
        
    Returns:
        Configured DiagnosticUncertaintyEngine instance
    """
    return DiagnosticUncertaintyEngine(config_path)


def get_facility_diagnostic_accuracy(facility: str) -> float:
    """
    Quick lookup for facility diagnostic accuracy.
    
    Args:
        facility: Military medical facility name
        
    Returns:
        Base diagnostic accuracy for facility
    """
    accuracy_map = {
        "POI": 0.65,
        "Role1": 0.75,
        "Role2": 0.85,
        "Role3": 0.95,
        "Role4": 0.98
    }
    return accuracy_map.get(facility, 0.65)


if __name__ == "__main__":
    # Test the diagnostic uncertainty engine
    engine = DiagnosticUncertaintyEngine()

    # Test diagnostic progression
    patient_id = "test_patient_001"
    true_condition = "19130008"  # Traumatic brain injury

    print("Testing Diagnostic Uncertainty Engine")
    print("=====================================")

    # POI diagnosis
    poi_diagnosis = engine.diagnose_condition(true_condition, "POI", patient_id)
    print(f"POI Diagnosis: {poi_diagnosis}")

    # Role1 progression
    engine.update_diagnosis_with_progression(
        patient_id, poi_diagnosis["diagnosed_code"], "Role1"
    )
    role1_diagnosis = engine.diagnose_condition(true_condition, "Role1", patient_id)
    print(f"Role1 Diagnosis: {role1_diagnosis}")

    # Final confidence
    confidence = engine.get_diagnostic_confidence(patient_id)
    print(f"Diagnostic Confidence: {confidence}")
