import random
import datetime
import concurrent.futures
from typing import List, Dict, Any, Optional

try:
    from .patient import Patient
    from .config_manager import ConfigurationManager
    from .schemas_config import FacilityConfig, FrontConfig as DBFrontConfig, FrontDefinition, FrontDefinitionNation # Updated imports
except ImportError:
    from patient_generator.patient import Patient
    from patient_generator.config_manager import ConfigurationManager
    from patient_generator.schemas_config import FacilityConfig, FrontConfig as DBFrontConfig, FrontDefinition, FrontDefinitionNation # Updated imports


class PatientFlowSimulator:
    """Optimized simulator for patient flow through medical treatment facilities, using dynamic configurations."""
    
    def __init__(self, config_manager: ConfigurationManager):
        self.config_manager = config_manager
        self.patients: List[Patient] = []
        active_config = self.config_manager.get_active_configuration()

        if not active_config:
            raise ValueError("PatientFlowSimulator requires an active configuration to be loaded in ConfigurationManager.")

        # --- Load configurations from ConfigurationManager ---
        self.total_patients_to_generate = active_config.total_patients
        
        # Front distribution:
        # Normalize casualty_rates from front_configs to create a distribution.
        # If casualty_rate is None or 0 for all, distribute evenly.
        self.front_configs: List[Dict[str, Any]] = self.config_manager.get_front_configs() or []
        self.front_distribution: Dict[str, float] = {}
        total_casualty_weight = sum(fc.get('casualty_rate', 0.0) for fc in self.front_configs if fc.get('casualty_rate', 0.0) > 0)
        
        if total_casualty_weight > 0:
            for fc in self.front_configs:
                rate = fc.get('casualty_rate', 0.0)
                if rate > 0:
                    self.front_distribution[fc['id']] = rate / total_casualty_weight
        elif self.front_configs: # If no rates, distribute evenly
            even_share = 1.0 / len(self.front_configs)
            for fc in self.front_configs:
                self.front_distribution[fc['id']] = even_share
        
        # Nationality distribution is now within each front_config object
        # self.nationality_distribution will be accessed dynamically per front in _create_initial_patient

        self.injury_distribution: Dict[str, float] = self.config_manager.get_injury_distribution() or {}
        
        # Facility configurations and dynamic transition probabilities
        self.facility_configs_ordered: List[Dict[str, Any]] = self.config_manager.get_facility_configs() or []
        self._transition_probabilities: Dict[str, Dict[str, float]] = self._build_transition_matrix()

        # --- Other parameters (some might become configurable later) ---
        self.day_distribution = { # TODO: Make this configurable
            "Day 1": 0.20, "Day 2": 0.40, "Day 4": 0.30, "Day 8": 0.10
        }
        self._triage_weights = { # TODO: Make this configurable
            "BATTLE_TRAUMA": {"T1": 0.4, "T2": 0.4, "T3": 0.2},
            "NON_BATTLE": {"T1": 0.2, "T2": 0.3, "T3": 0.5},
            "DISEASE": {"T1": 0.2, "T2": 0.3, "T3": 0.5}
        }
        self._base_date_str = active_config.created_at.strftime("%Y-%m-%d") # Or a dedicated config field

        # Parallelization settings
        self.batch_size = 100
        try:
            import multiprocessing
            self.num_workers = max(2, min(multiprocessing.cpu_count(), 8))
            if self.total_patients_to_generate > 5000:
                self.batch_size = 250
        except:
            self.num_workers = 4

    def _build_transition_matrix(self) -> Dict[str, Dict[str, float]]:
        """Dynamically build the transition matrix based on configured facilities."""
        matrix: Dict[str, Dict[str, float]] = {}
        
        # POI (Point of Injury) transitions - assuming some initial KIA rate before first facility
        # TODO: Make POI KIA rate configurable
        poi_kia_rate_val = self.config_manager.get_config_value("poi_kia_rate", 0.20)
        poi_kia_rate: float = 0.20 # Default
        if isinstance(poi_kia_rate_val, (int, float)):
            poi_kia_rate = float(poi_kia_rate_val)
        else:
            print(f"Warning: poi_kia_rate from config is not a number: {poi_kia_rate_val}. Defaulting to {poi_kia_rate}.")

        matrix["POI"] = {"KIA": poi_kia_rate} # This now assigns Dict[str, float]
        
        # Calculate remaining probability for POI to transition to the first facility or RTD
        poi_remaining_prob = 1.0 - poi_kia_rate
        if poi_remaining_prob < 0: poi_remaining_prob = 0.0 # Clamp if poi_kia_rate was > 1

        if self.facility_configs_ordered:
            first_facility_id = self.facility_configs_ordered[0]["id"]
            matrix["POI"][first_facility_id] = poi_remaining_prob
        else: # No facilities, all remaining from POI are effectively RTD or some other status
            matrix["POI"]["RTD"] = poi_remaining_prob # Or another terminal status

        for i, facility_data in enumerate(self.facility_configs_ordered):
            facility_id = facility_data["id"]
            
            # Initialize with defaults, then try to update from facility_data
            kia_rate: float = 0.1 
            rtd_rate: float = 0.3

            try:
                # These should be present and floats due to FacilityConfig Pydantic model
                kia_val_from_dict = facility_data["kia_rate"]
                rtd_val_from_dict = facility_data["rtd_rate"]
                
                # Ensure they are indeed numbers before casting
                if not isinstance(kia_val_from_dict, (int, float)):
                    raise ValueError(f"kia_rate '{kia_val_from_dict}' is not a number")
                if not isinstance(rtd_val_from_dict, (int, float)):
                    raise ValueError(f"rtd_rate '{rtd_val_from_dict}' is not a number")

                kia_rate = float(kia_val_from_dict)
                rtd_rate = float(rtd_val_from_dict)

            except KeyError as e:
                print(f"Critical Error: Missing rate key {e} in facility data for {facility_id}. Using default rates.")
            except ValueError as e: 
                print(f"Critical Error: Rate value issue for facility {facility_id}. Data: {facility_data}. Error: {e}. Using default rates.")

            # Pydantic validator on FacilityConfig should ensure kia_rate + rtd_rate <= 1.0
            # and that they are between 0.0 and 1.0. These are now post-retrieval/defaulting.
            # if (kia_rate + rtd_rate) > 1.0:
            #     print(f"Warning: KIA ({kia_rate}) + RTD ({rtd_rate}) > 1 for facility {facility_id}. Normalizing.")
            #     total_rate = kia_rate + rtd_rate
            #     kia_rate = kia_rate / total_rate
            #     rtd_rate = rtd_rate / total_rate
            
            matrix[facility_id] = {"KIA": kia_rate, "RTD": rtd_rate}
            
            # remaining_prob should be >= 0 due to Pydantic validation on FacilityConfig
            remaining_prob = 1.0 - kia_rate - rtd_rate 
            # Clamping for safety, though ideally not needed if Pydantic validation is effective
            if remaining_prob < -1e-9: # Using small tolerance for float issues
                 print(f"Warning: Negative remaining_prob ({remaining_prob}) for {facility_id} after KIA/RTD. Clamping to 0.")
                 remaining_prob = 0.0
            elif remaining_prob > 1.0: # Should also not happen
                 remaining_prob = 1.0


            if i < len(self.facility_configs_ordered) - 1: # If there's a next facility
                next_facility_id = self.facility_configs_ordered[i+1]["id"]
                matrix[facility_id][next_facility_id] = remaining_prob
            else: # Last facility in the chain, remaining go to RTD or are considered "evacuated out"
                  # For simplicity, let's add to RTD if any probability remains.
                  # Or, this could be a new terminal state like "EVAC_OUT_OF_THEATER"
                if remaining_prob > 0:
                    matrix[facility_id]["RTD"] += remaining_prob # Add to existing RTD
                    # Ensure RTD does not exceed 1.0 after this addition
                    if matrix[facility_id]["RTD"] > 1.0: matrix[facility_id]["RTD"] = 1.0
        return matrix

    def generate_casualty_flow(self): # total_casualties now comes from config
        """Generate the initial casualties and their flow through facilities"""
        total_casualties = self.total_patients_to_generate
        use_parallel = total_casualties >= 500 and self.num_workers > 1
        
        if use_parallel:
            return self._generate_flow_parallel(total_casualties)
        else:
            return self._generate_flow_sequential(total_casualties)
    
    def _generate_flow_sequential(self, total_casualties: int):
        patients = []
        for i in range(total_casualties):
            patient = self._create_initial_patient(i)
            self._simulate_patient_flow_single(patient)
            patients.append(patient)
        return patients
    
    def _generate_flow_parallel(self, total_casualties: int):
        patient_ids = list(range(total_casualties))
        patients = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            id_batches = [patient_ids[i:i + self.batch_size] for i in range(0, len(patient_ids), self.batch_size)]
            future_to_batch = { executor.submit(self._create_patient_batch, batch): batch for batch in id_batches }
            for future in concurrent.futures.as_completed(future_to_batch):
                patients.extend(future.result())
        
        patients.sort(key=lambda p: p.id) # Maintain order
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            patient_batches = [patients[i:i + self.batch_size] for i in range(0, len(patients), self.batch_size)]
            future_to_batch = { executor.submit(self._simulate_patient_flow_batch, batch): batch for batch in patient_batches }
            for future in concurrent.futures.as_completed(future_to_batch):
                _ = future.result() # Ensure completion
        return patients
    
    def _create_patient_batch(self, id_batch: List[int]):
        return [self._create_initial_patient(i) for i in id_batch]
    
    def _simulate_patient_flow_batch(self, patient_batch: List[Patient]):
        for patient in patient_batch:
            self._simulate_patient_flow_single(patient)
        return patient_batch # Though modified in place
    
    def _create_initial_patient(self, patient_id: int) -> Patient:
        patient = Patient(patient_id)
        
        static_front_defs: Optional[List[FrontDefinition]] = self.config_manager.get_static_front_definitions()

        if static_front_defs:
            # Use static fronts_config.json
            front_distribution_static = {front_def.name: front_def.ratio for front_def in static_front_defs if front_def.ratio > 0}
            
            if not front_distribution_static:
                 patient.front = "N/A_StaticEmpty"
                 patient.nationality = "N/A_StaticEmpty"
            else:
                selected_front_name = self._select_weighted_item(front_distribution_static)
                # Find the selected FrontDefinition object by its name
                selected_front_def = next((fdef for fdef in static_front_defs if fdef.name == selected_front_name), None)

                if selected_front_def:
                    patient.front = selected_front_def.name
                    nat_dist_static = {nat_def.iso: nat_def.ratio for nat_def in selected_front_def.nations if nat_def.ratio > 0}
                    if not nat_dist_static:
                        patient.nationality = "N/A_FrontHasNoNations"
                    else:
                        patient.nationality = self._select_weighted_item(nat_dist_static)
                else: 
                    patient.front = "ErrorStaticFront" # Should not happen if logic is correct
                    patient.nationality = "N/A"
        else:
            # Fallback to DB-based front_configs (using self.front_distribution calculated in __init__)
            if not self.front_distribution: 
                patient.front = "N/A_DB_NoFrontDist"
                patient.nationality = "N/A_DB_NoFrontDist"
            else:
                # self.front_distribution is Dict[str(front_id), float(casualty_rate_normalized)]
                front_id = self._select_weighted_item(self.front_distribution)
                # self.front_configs is List[Dict[str, Any]] from DB
                selected_front_config_db = next((fc for fc in self.front_configs if fc['id'] == front_id), None)
                
                if selected_front_config_db:
                    patient.front = selected_front_config_db.get("name", front_id)
                    # DB nationality_distribution is Dict[str(iso_code), float(percentage 0-100)]
                    current_front_nat_dist_db = selected_front_config_db.get("nationality_distribution", {})
                    if current_front_nat_dist_db:
                        # Filter for positive ratios before passing to _select_weighted_item
                        valid_nat_dist_db = {iso: ratio for iso, ratio in current_front_nat_dist_db.items() if ratio > 0}
                        if valid_nat_dist_db:
                            patient.nationality = self._select_weighted_item(valid_nat_dist_db)
                        else:
                            patient.nationality = "N/A_DBFrontHasNoValidNationRatios"
                    else:
                        patient.nationality = "N/A_DBFrontHasNoNations"
                else: # Should not happen if front_id came from self.front_distribution keys
                    patient.front = "ErrorDBFront"
                    patient.nationality = "N/A"

        patient.gender = random.choice(['male', 'female'])
        patient.day_of_injury = self._select_weighted_item(self.day_distribution)
        patient.injury_type = self._select_weighted_item(self.injury_distribution)
        patient.triage_category = self._select_weighted_item(self._triage_weights[patient.injury_type])
        
        patient.add_treatment(facility="POI", date=self._get_date_for_day(patient.day_of_injury))
        return patient
    
    def _simulate_patient_flow_single(self, patient: Patient):
        current_location = "POI"
        
        # Determine the ID of the last facility in the configured chain
        last_facility_in_chain_id = None
        if self.facility_configs_ordered:
            last_facility_in_chain_id = self.facility_configs_ordered[-1]["id"]

        while current_location not in ["RTD", "KIA"]:
            if current_location == last_facility_in_chain_id and current_location != "POI" : # If at the last configured facility
                # From the last facility, can only go to KIA or RTD based on its rates
                # (or a new terminal state like "EVAC_OUT_OF_THEATER" if defined)
                # The _determine_next_location will handle this based on the matrix.
                pass # Let _determine_next_location handle terminal states from last facility

            next_location = self._determine_next_location(patient, current_location)
            
            if next_location not in ["RTD", "KIA"]:
                # patient.day_of_injury is Optional[str], _get_treatment_date expects str
                # _create_initial_patient always sets it, so it should be a string here.
                assert patient.day_of_injury is not None, "day_of_injury should be set before simulating flow"
                treatment_date = self._get_treatment_date(patient.day_of_injury, current_location, next_location)
                treatments = self._generate_treatments(patient, next_location) # next_location is the facility ID
                observations = self._generate_observations(patient, next_location)
                patient.add_treatment(facility=next_location, date=treatment_date, treatments=treatments, observations=observations)
            
            patient.current_status = next_location
            current_location = next_location

            # Break if at last facility and next state is not KIA/RTD (should not happen if matrix is correct)
            if current_location == last_facility_in_chain_id and next_location not in ["KIA", "RTD"]:
                 # This implies the patient is "stuck" at the last facility but not KIA/RTD.
                 # The transition matrix for the last facility should only lead to KIA/RTD.
                 # If it leads to itself, it's an infinite loop.
                 # If it leads to another facility not in KIA/RTD, it's a logic error in matrix build.
                 # For now, if this state is reached, consider them as "remains at facility"
                 # which is effectively a terminal state for this simulation pass.
                 break


    def _determine_next_location(self, patient: Patient, current_facility_id: str) -> str:
        if current_facility_id in self._transition_probabilities:
            transitions = self._transition_probabilities[current_facility_id]
            # TODO: Add logic for patient condition affecting transitions if needed, similar to old POI logic
            # Example: if current_facility_id == "POI" and patient.injury_type == "BATTLE_TRAUMA": ...
            
            rand = random.random()
            cumulative_prob = 0.0
            for location, probability in transitions.items():
                cumulative_prob += probability
                if rand < cumulative_prob:
                    return location
        
        # Fallback: if no transitions defined (should not happen for POI or configured facilities)
        # or if at a terminal state already (though loop condition should prevent this call)
        print(f"Warning: No transitions defined for {current_facility_id} or invalid state. Patient status: {patient.current_status}")
        return "UNKNOWN_STATE" # Or current_facility_id to signify no change / error

    def _generate_treatments(self, patient: Patient, facility_id: str):
        # Find facility config by ID to get its name/type for treatment logic
        facility_config = next((f for f in self.facility_configs_ordered if f["id"] == facility_id), None)
        facility_name_or_type = facility_id # Fallback to ID
        if facility_config:
            facility_name_or_type = facility_config.get("name", facility_id) 
            # Could also add a "type" field to FacilityConfig like "Role1", "Role2" for generic treatment logic

        treatments = []
        # Simplified example: logic can be expanded based on facility_name_or_type or other props
        if "R1" in facility_name_or_type.upper() or "ROLE 1" in facility_name_or_type.upper(): # Example check
            if patient.injury_type == "BATTLE_TRAUMA": treatments.append({"code": "225317000", "display": "Initial dressing"})
            else: treatments.append({"code": "225343006", "display": "Medication admin"})
        elif "R2" in facility_name_or_type.upper() or "ROLE 2" in facility_name_or_type.upper():
            if patient.injury_type == "BATTLE_TRAUMA" and random.random() < 0.5: treatments.append({"code": "387713003", "display": "Surgery"})
            treatments.append({"code": "385968004", "display": "Fluid management"})
        elif "R3" in facility_name_or_type.upper() or "ROLE 3" in facility_name_or_type.upper():
            if patient.injury_type == "BATTLE_TRAUMA" and random.random() < 0.7: treatments.append({"code": "387713003", "display": "Major Surgery"})
            treatments.append({"code": "225352004", "display": "Intensive care"})
        # Add more specific treatments based on actual facility capabilities from config if available
        return treatments
    
    def _generate_observations(self, patient: Patient, facility_id: str):
        # Similar to treatments, can be made more dynamic based on facility_id/type
        observations = []
        observations.append({"code": "8310-5", "display": "Body temperature", "value": round(random.normalvariate(37.0, 0.8), 1), "unit": "Cel"})
        observations.append({"code": "8867-4", "display": "Heart rate", "value": int(random.normalvariate(80, 15)), "unit": "/min"})
        # ... more observations
        return observations
    
    def _select_weighted_item(self, weights_dict: Dict[str, float]):
        if not weights_dict: return "N/A" # Handle empty distribution
        
        # Filter out items with zero or negative weights if any, though Pydantic should prevent negative
        valid_weights_dict = {item: weight for item, weight in weights_dict.items() if weight > 0}
        if not valid_weights_dict: return "N/A" # All weights were zero or less

        total_weight = sum(valid_weights_dict.values())
        if total_weight == 0: return random.choice(list(valid_weights_dict.keys())) # If all valid weights are 0, pick one randomly

        # Normalize weights if they don't sum to 1 (e.g. if they are just ratios)
        # For random.choices, weights don't strictly need to sum to 1, but it's good practice for clarity.
        # Here, we assume weights are probabilities or can be treated as relative weights.
        
        items = list(valid_weights_dict.keys())
        weights = list(valid_weights_dict.values())
        
        return random.choices(items, weights=weights, k=1)[0]
    
    def _get_date_for_day(self, day_label: str) -> datetime.datetime:
        if not hasattr(self, '_cached_base_date_obj'):
            # Use the base_date_str derived from config in __init__
            self._cached_base_date_obj = datetime.datetime.strptime(self._base_date_str, "%Y-%m-%d").date()
            self._day_offsets = {"Day 1": 0, "Day 2": 1, "Day 4": 3, "Day 8": 7} # TODO: Make configurable
        
        offset = self._day_offsets.get(day_label, 0)
        event_date = self._cached_base_date_obj + datetime.timedelta(days=offset)
        return datetime.datetime.combine(event_date, datetime.time.min) 
    
    def _get_treatment_date(self, injury_day_label: str, current_facility_id: str, next_facility_id: str) -> datetime.datetime:
        base_event_time = self._get_date_for_day(injury_day_label)
        
        if not hasattr(self, '_transit_hours'):
            self._transit_hours = { # TODO: Make this configurable, perhaps per facility in FacilityConfig
                ("POI", self.facility_configs_ordered[0]["id"] if self.facility_configs_ordered else "R1_fallback"): 1,
            }
            # Dynamically add transit times between configured facilities
            for i in range(len(self.facility_configs_ordered) - 1):
                fac_curr_id = self.facility_configs_ordered[i]["id"]
                fac_next_id = self.facility_configs_ordered[i+1]["id"]
                # Default transit times, can be overridden by config later
                default_transit = 2 * (i + 1) # e.g. R1->R2 = 2hrs, R2->R3 = 4hrs
                self._transit_hours[(fac_curr_id, fac_next_id)] = default_transit


        transit_key = (current_facility_id, next_facility_id)
        hours_to_add = self._transit_hours.get(transit_key, 1) # Default 1hr if specific transit not found
        
        return base_event_time + datetime.timedelta(hours=hours_to_add)
