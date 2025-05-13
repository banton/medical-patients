import random
import datetime
from .patient import Patient

class PatientFlowSimulator:
    """Simulates patient flow through medical treatment facilities"""
    
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
    
    def generate_casualty_flow(self, total_casualties=1440):
        """Generate the initial casualties and their flow through facilities"""
        
        # Create patients with initial status
        for i in range(total_casualties):
            patient = self._create_initial_patient(i)
            self.patients.append(patient)
            
        # Simulate flow through medical facilities
        self._simulate_patient_flow()
        
        return self.patients
    
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
        
        # Assign triage category (more severe for battle trauma)
        if patient.injury_type == "BATTLE_TRAUMA":
            triage_weights = {"T1": 0.4, "T2": 0.4, "T3": 0.2}
        else:
            triage_weights = {"T1": 0.2, "T2": 0.3, "T3": 0.5}
        patient.triage_category = self._select_weighted_item(triage_weights)
        
        # Record initial POI event
        patient.add_treatment(
            facility="POI",
            date=self._get_date_for_day(patient.day_of_injury)
        )
        
        return patient
    
    def _simulate_patient_flow(self):
        """Simulate the movement of patients through facilities"""
        for patient in self.patients:
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
        # Get the probabilities from the configuration
        if current_location == "POI":
            kia_prob = 0.20  # 20% KIA at POI
            rtd_prob = 0.0   # No RTD at POI
            evac_prob = 0.80  # 80% evacuated to R1
            
            if random.random() < kia_prob:
                return "KIA"
            else:
                return "R1"
        
        elif current_location == "R1":
            # Based on the provided table
            kia_prob = 0.12  # 12% KIA at R1
            rtd_prob = 0.60  # 60% RTD at R1
            evac_prob = 0.28  # 28% evacuated to R2
            
            rand = random.random()
            if rand < kia_prob:
                return "KIA"
            elif rand < kia_prob + rtd_prob:
                return "RTD"
            else:
                return "R2"
        
        elif current_location == "R2":
            kia_prob = 0.137  # 13.7% KIA at R2
            rtd_prob = 0.55   # 55% RTD at R2
            evac_prob = 0.313  # 31.3% evacuated to R3
            
            rand = random.random()
            if rand < kia_prob:
                return "KIA"
            elif rand < kia_prob + rtd_prob:
                return "RTD"
            else:
                return "R3"
        
        elif current_location == "R3":
            kia_prob = 0.121  # 12.1% KIA at R3
            rtd_prob = 0.30   # 30% RTD at R3
            evac_prob = 0.579  # 57.9% evacuated to R4
            
            rand = random.random()
            if rand < kia_prob:
                return "KIA"
            elif rand < kia_prob + rtd_prob:
                return "RTD"
            else:
                return "R4"
        
        # R4 is terminal state
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
        """Select an item from a dictionary based on weights"""
        items = list(weights_dict.keys())
        weights = list(weights_dict.values())
        return random.choices(items, weights=weights, k=1)[0]
    
    def _get_date_for_day(self, day_label):
        """Convert day label to actual date"""
        base_date_str = self.config.get("base_date", "2025-06-01")
        base_date = datetime.datetime.strptime(base_date_str, "%Y-%m-%d").date()
        
        day_offsets = {
            "Day 1": 0,
            "Day 2": 1,
            "Day 4": 3,
            "Day 8": 7
        }
        
        offset = day_offsets.get(day_label, 0)
        return base_date + datetime.timedelta(days=offset)
    
    def _get_treatment_date(self, injury_day, current_location, next_location):
        """Calculate treatment date based on injury day and facility transit times"""
        base_date = self._get_date_for_day(injury_day)
        
        # Add hours based on transit between facilities
        transit_hours = {
            ("POI", "R1"): 1,
            ("R1", "R2"): 2,
            ("R2", "R3"): 4,
            ("R3", "R4"): 12
        }
        
        transit_key = (current_location, next_location)
        hours_to_add = transit_hours.get(transit_key, 0)
        
        return datetime.datetime.combine(base_date, datetime.time()) + datetime.timedelta(hours=hours_to_add)