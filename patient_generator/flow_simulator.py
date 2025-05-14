import random
import datetime
import concurrent.futures

# Use absolute imports instead of relative imports
try:
    # Try relative import first (when used as a package)
    from .patient import Patient
except ImportError:
    # Fall back to absolute imports (when run directly)
    from patient_generator.patient import Patient

class PatientFlowSimulator:
    """Optimized simulator for patient flow through medical treatment facilities"""
    
    def __init__(self, config):
        self.config = config
        self.patients = []
        
        # Distribution of patients across days
        self.day_distribution = {
            "Day 1": 0.20,
            "Day 2": 0.40,
            "Day 4": 0.30,
            "Day 8": 0.10
        }
        
        # Distribution of patients across fronts
        self.front_distribution = {
            "Polish": self.config.get("front_distribution", {}).get("Polish", 0.50),
            "Estonian": self.config.get("front_distribution", {}).get("Estonian", 0.333),
            "Finnish": self.config.get("front_distribution", {}).get("Finnish", 0.167)
        }
        
        # Nationality distribution within each front
        self.nationality_distribution = self.config.get("nationality_distribution", {
            "Polish": {
                "POL": 0.50,
                "GBR": 0.10,
                "LIT": 0.30,
                "USA": 0.05,
                "ESP": 0.05
            },
            "Estonian": {
                "EST": 0.70,
                "GBR": 0.30
            },
            "Finnish": {
                "FIN": 0.40,
                "USA": 0.60
            }
        })
        
        # Types of injuries
        self.injury_distribution = self.config.get("injury_distribution", {
            "DISEASE": 0.52,
            "NON_BATTLE": 0.33,
            "BATTLE_TRAUMA": 0.15
        })
        
        # Pre-calculate facility transition probabilities for efficiency
        self._transition_probabilities = {
            "POI": {"KIA": 0.20, "R1": 0.80},
            "R1": {"KIA": 0.12, "RTD": 0.60, "R2": 0.28},
            "R2": {"KIA": 0.137, "RTD": 0.55, "R3": 0.313},
            "R3": {"KIA": 0.121, "RTD": 0.30, "R4": 0.579}
        }
        
        # Pre-calculate triage weights based on injury type
        self._triage_weights = {
            "BATTLE_TRAUMA": {"T1": 0.4, "T2": 0.4, "T3": 0.2},
            "NON_BATTLE": {"T1": 0.2, "T2": 0.3, "T3": 0.5},
            "DISEASE": {"T1": 0.2, "T2": 0.3, "T3": 0.5}
        }
        
        # Calculate batch size for parallelization
        self.batch_size = 100  # Default batch size
        
        # Detect available CPU cores and adjust batch sizes
        try:
            import multiprocessing
            self.num_workers = max(2, min(multiprocessing.cpu_count(), 8))
            # Adjust batch size based on total patients and worker count
            if self.config.get("total_patients", 1440) > 5000:
                self.batch_size = 250
        except:
            self.num_workers = 4  # Default to 4 workers if detection fails
    
    def generate_casualty_flow(self, total_casualties=1440):
        """Generate the initial casualties and their flow through facilities"""
        # Determine if parallelization should be used
        use_parallel = total_casualties >= 500 and self.num_workers > 1
        
        if use_parallel:
            # For large datasets, use parallel processing
            return self._generate_flow_parallel(total_casualties)
        else:
            # For smaller datasets, use sequential processing
            return self._generate_flow_sequential(total_casualties)
    
    def _generate_flow_sequential(self, total_casualties):
        """Generate patient flow sequentially for smaller datasets"""
        patients = []
        
        # Create patients with initial status
        for i in range(total_casualties):
            patient = self._create_initial_patient(i)
            self._simulate_patient_flow_single(patient)
            patients.append(patient)
            
        return patients
    
    def _generate_flow_parallel(self, total_casualties):
        """Generate patient flow using parallel processing for large datasets"""
        # First create all patients with initial attributes
        patient_ids = list(range(total_casualties))
        
        # Create patients in parallel batches
        patients = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Split ids into batches
            id_batches = [patient_ids[i:i + self.batch_size] for i in range(0, len(patient_ids), self.batch_size)]
            
            # Submit batch creation jobs
            future_to_batch = {
                executor.submit(self._create_patient_batch, batch): batch for batch in id_batches
            }
            
            # Collect created patients
            for future in concurrent.futures.as_completed(future_to_batch):
                batch_patients = future.result()
                patients.extend(batch_patients)
        
        # Sort patients by ID to maintain consistent order
        patients.sort(key=lambda p: p.id)
        
        # Now simulate patient flow for all patients
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Split patients into batches
            patient_batches = [patients[i:i + self.batch_size] for i in range(0, len(patients), self.batch_size)]
            
            # Submit batch simulation jobs
            future_to_batch = {
                executor.submit(self._simulate_patient_flow_batch, batch): batch for batch in patient_batches
            }
            
            # Wait for all simulations to complete
            for future in concurrent.futures.as_completed(future_to_batch):
                batch = future_to_batch[future]
                # No need to collect as patients are modified in-place
        
        return patients
    
    def _create_patient_batch(self, id_batch):
        """Create a batch of patients with initial attributes"""
        return [self._create_initial_patient(i) for i in id_batch]
    
    def _simulate_patient_flow_batch(self, patient_batch):
        """Simulate patient flow for a batch of patients"""
        for patient in patient_batch:
            self._simulate_patient_flow_single(patient)
        return patient_batch
    
    def _create_initial_patient(self, patient_id):
        """Create a new patient with initial casualty state"""
        patient = Patient(patient_id)
        
        # First select which front the casualty is from
        front = self._select_weighted_item(self.front_distribution)
        
        # Then select nationality based on the front's distribution
        nationality = self._select_weighted_item(self.nationality_distribution[front])
        patient.nationality = nationality
        patient.front = front
        
        # Randomly assign gender
        patient.gender = random.choice(['male', 'female'])
        
        # Assign day of injury
        patient.day_of_injury = self._select_weighted_item(self.day_distribution)
        
        # Assign injury type
        patient.injury_type = self._select_weighted_item(self.injury_distribution)
        
        # Assign triage category based on injury type
        triage_weights = self._triage_weights[patient.injury_type]
        patient.triage_category = self._select_weighted_item(triage_weights)
        
        # Record initial POI event
        patient.add_treatment(
            facility="POI",
            date=self._get_date_for_day(patient.day_of_injury)
        )
        
        return patient
    
    def _simulate_patient_flow_single(self, patient):
        """Simulate the movement of a single patient through facilities"""
        current_location = "POI"
        
        # Loop until patient reaches final state (RTD, KIA, or R4)
        while current_location not in ["RTD", "KIA", "R4"]:
            # Determine next location based on probabilities
            next_location = self._determine_next_location(patient, current_location)
            
            # If status changed, add to treatment history
            if next_location not in ["RTD", "KIA"]:
                treatment_date = self._get_treatment_date(
                    patient.day_of_injury, 
                    current_location, 
                    next_location
                )
                
                treatments = self._generate_treatments(patient, next_location)
                observations = self._generate_observations(patient, next_location)
                
                patient.add_treatment(
                    facility=next_location,
                    date=treatment_date,
                    treatments=treatments,
                    observations=observations
                )
            
            # Update patient status
            patient.current_status = next_location
            current_location = next_location
    
    def _determine_next_location(self, patient, current_location):
        """Determine the next location for a patient based on probabilities"""
        # Get the transition probabilities for the current location
        if current_location in self._transition_probabilities:
            transitions = self._transition_probabilities[current_location]
            
            # Adjust probabilities based on patient's condition if needed
            if current_location == "POI" and patient.injury_type == "BATTLE_TRAUMA" and patient.triage_category == "T1":
                # Higher KIA rate for severe battle trauma
                transitions = transitions.copy()  # Create a copy to avoid modifying the shared dict
                transitions["KIA"] = transitions["KIA"] * 1.2  # 20% higher KIA chance
                transitions["R1"] = 1.0 - transitions["KIA"]  # Adjust R1 probability
            
            # Generate random number and determine outcome
            rand = random.random()
            cumulative_prob = 0.0
            
            for location, probability in transitions.items():
                cumulative_prob += probability
                if rand < cumulative_prob:
                    return location
        
        # Default to staying at current location if no transition defined
        return current_location
    
    def _generate_treatments(self, patient, facility):
        """Generate appropriate treatments for the patient at this facility"""
        treatments = []
        
        # Base treatments on facility level and patient condition
        if facility == "R1":
            # Basic first aid, stabilization
            if patient.injury_type == "BATTLE_TRAUMA":
                treatments.append({"code": "225317000", "display": "Initial dressing of wound"})
                if patient.triage_category == "T1":
                    treatments.append({"code": "225310008", "display": "Insertion of intravenous cannula"})
            elif patient.injury_type == "NON_BATTLE":
                treatments.append({"code": "225358003", "display": "Wound care"})
            else:  # DISEASE
                treatments.append({"code": "225343006", "display": "Administration of medication"})
        
        elif facility == "R2":
            # More advanced treatments including surgery for some
            if patient.injury_type == "BATTLE_TRAUMA":
                # 50% chance of surgery at R2 for battle trauma
                if random.random() < 0.5:
                    treatments.append({"code": "387713003", "display": "Surgical procedure"})
                treatments.append({"code": "385968004", "display": "Fluid management"})
            elif patient.injury_type == "NON_BATTLE":
                treatments.append({"code": "225362007", "display": "Casting of fracture"})
            else:  # DISEASE
                treatments.append({"code": "225343006", "display": "Administration of medication"})
                treatments.append({"code": "182777000", "display": "Patient monitoring"})
        
        elif facility == "R3":
            # Specialized treatments
            if patient.injury_type == "BATTLE_TRAUMA":
                # 70% chance of surgery at R3 for battle trauma
                if random.random() < 0.7:
                    treatments.append({"code": "387713003", "display": "Surgical procedure"})
                treatments.append({"code": "225352004", "display": "Intensive care management"})
            elif patient.injury_type == "NON_BATTLE":
                # 30% chance of surgery for non-battle injuries
                if random.random() < 0.3:
                    treatments.append({"code": "387713003", "display": "Surgical procedure"})
                treatments.append({"code": "225363002", "display": "Specialized treatment"})
            else:  # DISEASE
                treatments.append({"code": "225343006", "display": "Administration of medication"})
                treatments.append({"code": "306237005", "display": "Referral to specialist"})
        
        return treatments
    
    def _generate_observations(self, patient, facility):
        """Generate observations appropriate for the facility level"""
        observations = []
        
        # Add vital signs for all patients at all facilities
        observations.append({
            "code": "8310-5",
            "display": "Body temperature",
            "value": round(random.normalvariate(37.0, 0.8), 1),
            "unit": "Cel"
        })
        
        observations.append({
            "code": "8867-4",
            "display": "Heart rate",
            "value": int(random.normalvariate(80, 15)),
            "unit": "/min"
        })
        
        observations.append({
            "code": "8480-6",
            "display": "Systolic blood pressure",
            "value": int(random.normalvariate(120, 20)),
            "unit": "mm[Hg]"
        })
        
        observations.append({
            "code": "8462-4",
            "display": "Diastolic blood pressure",
            "value": int(random.normalvariate(80, 10)),
            "unit": "mm[Hg]"
        })
        
        # Add facility-specific observations
        if facility == "R2" or facility == "R3":
            # Lab tests at R2 and R3
            observations.append({
                "code": "718-7",
                "display": "Hemoglobin",
                "value": round(random.normalvariate(14, 2), 1),
                "unit": "g/dL"
            })
            
            observations.append({
                "code": "6690-2",
                "display": "White blood cell count",
                "value": round(random.normalvariate(8, 3), 1),
                "unit": "10*3/uL"
            })
        
        if facility == "R3":
            # More specialized tests at R3
            observations.append({
                "code": "2345-7",
                "display": "Glucose",
                "value": int(random.normalvariate(100, 20)),
                "unit": "mg/dL"
            })
            
            if patient.injury_type == "BATTLE_TRAUMA":
                observations.append({
                    "code": "882-1",
                    "display": "ABO group",
                    "value": random.choice(["A", "B", "AB", "O"]),
                    "unit": ""
                })
        
        return observations
    
    # Helper methods
    def _select_weighted_item(self, weights_dict):
        """Select an item from a dictionary based on weights - optimized version"""
        # Convert to list of (item, weight) tuples for faster processing
        items = []
        weights = []
        
        for item, weight in weights_dict.items():
            items.append(item)
            weights.append(weight)
        
        # Use random.choices for more efficient weighted selection
        return random.choices(items, weights=weights, k=1)[0]
    
    def _get_date_for_day(self, day_label):
        """Convert day label to actual date"""
        # Using a cached base date for efficiency
        if not hasattr(self, '_base_date'):
            base_date_str = self.config.get("base_date", "2025-06-01")
            self._base_date = datetime.datetime.strptime(base_date_str, "%Y-%m-%d").date()
            
            # Pre-calculate day offsets
            self._day_offsets = {
                "Day 1": 0,
                "Day 2": 1,
                "Day 4": 3,
                "Day 8": 7
            }
        
        offset = self._day_offsets.get(day_label, 0)
        event_date = self._base_date + datetime.timedelta(days=offset)
        return datetime.datetime.combine(event_date, datetime.time.min) # Ensure datetime object
    
    def _get_treatment_date(self, injury_day, current_location, next_location):
        """Calculate treatment date based on injury day and facility transit times"""
        # Get the base date
        base_date = self._get_date_for_day(injury_day)
        
        # Cached transit times for efficiency
        if not hasattr(self, '_transit_hours'):
            self._transit_hours = {
                ("POI", "R1"): 1,
                ("R1", "R2"): 2,
                ("R2", "R3"): 4,
                ("R3", "R4"): 12
            }
        
        transit_key = (current_location, next_location)
        hours_to_add = self._transit_hours.get(transit_key, 0)
        
        return datetime.datetime.combine(base_date, datetime.time()) + datetime.timedelta(hours=hours_to_add)
