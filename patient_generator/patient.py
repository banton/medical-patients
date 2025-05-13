class Patient:
    """Represents a patient with demographics and medical history"""
    
    def __init__(self, patient_id):
        self.id = patient_id
        self.demographics = {}
        self.medical_data = {}
        self.treatment_history = []
        self.current_status = "POI"  # POI, R1, R2, R3, R4, RTD, KIA
        self.day_of_injury = None
        self.injury_type = None  # "DISEASE", "NON_BATTLE", "BATTLE_TRAUMA"
        self.triage_category = None  # T1, T2, T3
        self.nationality = None
        self.front = None  # Polish, Estonian, Finnish
        self.primary_condition = None
        self.additional_conditions = []
        self.gender = None
        
    def add_treatment(self, facility, date, treatments=None, observations=None):
        """Add a treatment event to the patient's history"""
        self.treatment_history.append({
            "facility": facility,
            "date": date,
            "treatments": treatments or [],
            "observations": observations or []
        })
        self.current_status = facility
        
    def set_demographics(self, demographics):
        """Set patient demographics"""
        self.demographics = demographics
        if 'gender' in demographics:
            self.gender = demographics['gender']
            
    def get_age(self):
        """Calculate patient age from birthdate"""
        if 'birthdate' not in self.demographics:
            return None
            
        import datetime
        birthdate = datetime.datetime.strptime(self.demographics['birthdate'], "%Y-%m-%d")
        today = datetime.datetime.now()
        age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
        return age