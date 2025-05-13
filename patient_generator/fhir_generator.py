import uuid
import datetime
import weakref
import json
from functools import lru_cache

class FHIRBundleGenerator:
    """Converts Patient objects to HL7 FHIR bundles with performance optimizations"""
    
    def __init__(self, demographics_generator=None):
        self.demographics_generator = demographics_generator
        # Cache for commonly used coding blocks
        self._coding_cache = {}
        
    def create_fhir_bundles(self, patients):
        """Create FHIR bundles for all patients"""
        # Memory-optimized implementation - avoid storing all bundles at once
        # Instead, yield bundles one at a time as a generator
        for patient in patients:
            yield self.create_patient_bundle(patient)
            
    def create_patient_bundle(self, patient):
        """Create a complete FHIR bundle for a single patient"""
        # Generate a unique ID for the bundle
        bundle_id = str(uuid.uuid4())
        
        # Create patient resource
        patient_resource = self._create_patient_resource(patient)
        
        # Create resources for medical history
        medical_resources = self._create_medical_resources(patient, patient_resource["id"])
        
        # Create NFC metadata
        nfc_id = f"NFC-{str(uuid.uuid4())[:8]}"
        timestamp = datetime.datetime.now().isoformat()
        
        # Assemble the bundle
        bundle = {
            "resourceType": "Bundle",
            "id": bundle_id,
            "type": "collection",
            "timestamp": timestamp,
            "extension": [{
                "url": "http://example.org/fhir/StructureDefinition/nfc-tag-id",
                "valueString": nfc_id
            }],
            "entry": [
                {"resource": patient_resource}
            ]
        }
        
        # Add all medical resources to the bundle
        for resource in medical_resources:
            bundle["entry"].append({"resource": resource})
        
        return bundle
    
    @lru_cache(maxsize=32)
    def _get_cached_coding(self, system, code, display):
        """Return a cached coding block to reduce memory duplication"""
        key = f"{system}|{code}|{display}"
        if key not in self._coding_cache:
            self._coding_cache[key] = [{
                "system": system,
                "code": code,
                "display": display
            }]
        return self._coding_cache[key]
    
    def _create_patient_resource(self, patient):
        """Create a FHIR Patient resource"""
        patient_id = str(uuid.uuid4())
        
        # Use demographics from patient object if available
        demographics = patient.demographics
        
        # Fallback to generating demographics if not available
        if not demographics and self.demographics_generator:
            demographics = self.demographics_generator.generate_person(patient.nationality, patient.gender)
        
        # Create basic patient resource
        patient_resource = {
            "resourceType": "Patient",
            "id": patient_id,
            "gender": patient.gender or "unknown",
            "extension": []
        }
        
        # Add name if available
        if demographics and 'family_name' in demographics and 'given_name' in demographics:
            patient_resource["name"] = [{
                "family": demographics['family_name'],
                "given": [demographics['given_name']]
            }]
        
        # Add birthdate if available
        if demographics and 'birthdate' in demographics:
            patient_resource["birthDate"] = demographics['birthdate']
        
        # Add nationality extension if available
        if patient.nationality:
            patient_resource["extension"].append({
                "url": "http://example.org/fhir/StructureDefinition/nationality",
                "valueString": patient.nationality
            })
        
        # Add religion if available
        if demographics and 'religion' in demographics and demographics['religion']:
            patient_resource["extension"].append({
                "url": "http://terminology.hl7.org/CodeSystem/v3-ReligiousAffiliation",
                "valueCodeableConcept": {
                    "coding": self._get_cached_coding(
                        "http://terminology.hl7.org/CodeSystem/v3-ReligiousAffiliation",
                        demographics['religion'],
                        None
                    )
                }
            })
        
        # Add identifiers
        patient_resource["identifier"] = []
        
        if demographics and 'id_number' in demographics and demographics['id_number']:
            system = "http://fhir.nl/fhir/NamingSystem/bsn" if patient.nationality == 'NLD' else "http://example.org/identifier"
            patient_resource["identifier"].append({
                "system": system,
                "value": demographics['id_number']
            })
        
        return patient_resource
    
    def _create_medical_resources(self, patient, patient_id):
        """Create FHIR resources for the patient's medical history"""
        resources = []
        
        # Create condition resources based on primary condition
        if hasattr(patient, 'primary_condition') and patient.primary_condition:
            condition_resource = self._create_condition_resource(patient.primary_condition, patient_id)
            resources.append(condition_resource)
        
        # Add additional conditions
        if hasattr(patient, 'additional_conditions'):
            for condition in patient.additional_conditions:
                condition_resource = self._create_condition_resource(condition, patient_id)
                resources.append(condition_resource)
        
        # Create resources for each treatment facility visit
        for visit in patient.treatment_history:
            # Add procedure resources for treatments
            for treatment in visit.get("treatments", []):
                procedure = self._create_procedure_resource(
                    patient_id, 
                    treatment["code"], 
                    treatment["display"],
                    visit["date"]
                )
                resources.append(procedure)
            
            # Add observation resources
            for obs in visit.get("observations", []):
                observation = self._create_observation_resource(
                    patient_id,
                    obs["code"],
                    obs["display"],
                    obs["value"],
                    obs.get("unit"),
                    visit["date"]
                )
                resources.append(observation)
        
        # Add demographics-based observations
        if patient.demographics:
            # Add blood type observation if available
            if 'blood_type' in patient.demographics:
                blood_type_obs = self._create_blood_type_observation(patient_id, patient.demographics["blood_type"])
                resources.append(blood_type_obs)
            
            # Add weight observation if available
            if 'weight' in patient.demographics:
                weight_obs = self._create_weight_observation(patient_id, patient.demographics["weight"])
                resources.append(weight_obs)
        
        return resources
    
    def _create_condition_resource(self, condition, patient_id):
        """Create a Condition resource"""
        condition_id = str(uuid.uuid4())
        
        # Handle both dictionary and simple object conditions
        if isinstance(condition, dict):
            code = condition.get("code")
            display = condition.get("display")
            severity = condition.get("severity")
            severity_code = condition.get("severity_code")
        else:
            code = getattr(condition, "code", None)
            display = getattr(condition, "display", None)
            severity = getattr(condition, "severity", None)
            severity_code = getattr(condition, "severity_code", None)
        
        # Create condition resource
        condition_resource = {
            "resourceType": "Condition",
            "id": condition_id,
            "subject": {"reference": f"Patient/{patient_id}"},
            "code": {
                "coding": self._get_cached_coding(
                    "http://snomed.info/sct",
                    code,
                    display
                )
            },
            "clinicalStatus": {
                "coding": self._get_cached_coding(
                    "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "active",
                    "Active"
                )
            },
            "verificationStatus": {
                "coding": self._get_cached_coding(
                    "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "confirmed",
                    "Confirmed"
                )
            },
            "onsetDateTime": datetime.datetime.now().isoformat()
        }
        
        # Add severity if available
        if severity and severity_code:
            condition_resource["severity"] = {
                "coding": self._get_cached_coding(
                    "http://snomed.info/sct",
                    severity_code,
                    severity
                )
            }
        
        return condition_resource
    
    def _create_procedure_resource(self, patient_id, code, display, date):
        """Create a Procedure resource"""
        procedure_id = str(uuid.uuid4())
        
        procedure = {
            "resourceType": "Procedure",
            "id": procedure_id,
            "subject": {"reference": f"Patient/{patient_id}"},
            "status": "completed",
            "code": {
                "coding": self._get_cached_coding(
                    "http://snomed.info/sct",
                    code,
                    display
                )
            }
        }
        
        # Add date if available
        if date:
            if isinstance(date, datetime.datetime) or isinstance(date, datetime.date):
                date_str = date.isoformat()
            else:
                date_str = str(date)
            procedure["performedDateTime"] = date_str
        
        return procedure
    
    def _create_observation_resource(self, patient_id, code, display, value, unit, date):
        """Create an Observation resource"""
        observation_id = str(uuid.uuid4())
        
        observation = {
            "resourceType": "Observation",
            "id": observation_id,
            "status": "final",
            "subject": {"reference": f"Patient/{patient_id}"},
            "code": {
                "coding": self._get_cached_coding(
                    "http://loinc.org",
                    code,
                    display
                )
            }
        }
        
        # Add value
        if unit:
            observation["valueQuantity"] = {
                "value": value,
                "unit": unit,
                "system": "http://unitsofmeasure.org",
                "code": unit
            }
        else:
            observation["valueString"] = str(value)
        
        # Add date if available
        if date:
            if isinstance(date, datetime.datetime) or isinstance(date, datetime.date):
                date_str = date.isoformat()
            else:
                date_str = str(date)
            observation["effectiveDateTime"] = date_str
        
        return observation
    
    def _create_blood_type_observation(self, patient_id, blood_type):
        """Create a blood type observation"""
        observation_id = str(uuid.uuid4())
        
        # Map to SNOMED CT codes
        blood_type_codes = {
            "A": "112144000",
            "B": "165743006",
            "AB": "112149005",
            "O": "58460004"
        }
        
        code = blood_type_codes.get(blood_type, "112144000")
        
        observation = {
            "resourceType": "Observation",
            "id": observation_id,
            "status": "final",
            "subject": {"reference": f"Patient/{patient_id}"},
            "code": {
                "coding": self._get_cached_coding(
                    "http://loinc.org",
                    "883-9",
                    "ABO group"
                )
            },
            "valueCodeableConcept": {
                "coding": self._get_cached_coding(
                    "http://snomed.info/sct",
                    code,
                    f"Blood group {blood_type}"
                )
            },
            "effectiveDateTime": datetime.datetime.now().isoformat()
        }
        
        return observation
    
    def _create_weight_observation(self, patient_id, weight):
        """Create a weight observation"""
        observation_id = str(uuid.uuid4())
        
        observation = {
            "resourceType": "Observation",
            "id": observation_id,
            "status": "final",
            "subject": {"reference": f"Patient/{patient_id}"},
            "code": {
                "coding": self._get_cached_coding(
                    "http://loinc.org",
                    "29463-7",
                    "Body weight"
                )
            },
            "valueQuantity": {
                "value": weight,
                "unit": "kg",
                "system": "http://unitsofmeasure.org",
                "code": "kg"
            },
            "effectiveDateTime": datetime.datetime.now().isoformat()
        }
        
        return observation