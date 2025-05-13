import random
import datetime

class DemographicsGenerator:
    """Generates realistic demographics based on nationality"""
    
    def __init__(self):
        # Initialize data sources for different nationalities
        self._init_name_data()
        self._init_id_formats()
        
    def _init_name_data(self):
        """Initialize name data for different nationalities"""
        # These would be loaded from files in a real implementation
        self.first_names = {
            "POL": {
                "male": ["Jakub", "Jan", "Adam", "Piotr", "Michał", "Paweł", "Tomasz", "Krzysztof", "Andrzej", "Marcin", 
                         "Marek", "Łukasz", "Grzegorz", "Józef", "Zbigniew", "Jerzy", "Mateusz", "Tadeusz", "Dariusz", "Daniel"],
                "female": ["Anna", "Maria", "Katarzyna", "Małgorzata", "Agnieszka", "Barbara", "Krystyna", "Ewa", "Elżbieta", 
                           "Zofia", "Janina", "Teresa", "Joanna", "Magdalena", "Monika", "Jadwiga", "Danuta", "Aleksandra", "Halina", "Irena"]
            },
            "EST": {
                "male": ["Andres", "Jaan", "Margus", "Tõnu", "Rein", "Tarmo", "Marko", "Aivar", "Toomas", "Tiit", 
                         "Mart", "Peeter", "Jaak", "Ants", "Urmas", "Mati", "Raul", "Ivo", "Kristjan", "Priit"],
                "female": ["Tiina", "Kadri", "Anne", "Kristiina", "Mari", "Piret", "Sirje", "Kristi", "Liis", 
                           "Katrin", "Eve", "Laura", "Liina", "Marju", "Merle", "Marika", "Riina", "Ülle", "Triin", "Karin"]
            },
            "FIN": {
                "male": ["Juha", "Timo", "Matti", "Kari", "Mikko", "Pekka", "Antti", "Jari", "Jukka", "Markku", 
                         "Sami", "Hannu", "Heikki", "Ari", "Ville", "Petri", "Marko", "Janne", "Esa", "Jaakko"],
                "female": ["Maria", "Helena", "Johanna", "Kaarina", "Liisa", "Anne", "Tiina", "Leena", "Päivi", 
                           "Katja", "Anna", "Sari", "Hanna", "Marja", "Satu", "Tarja", "Eeva", "Tuula", "Riitta", "Maija"]
            },
            "GBR": {
                "male": ["James", "John", "Robert", "Michael", "William", "David", "Thomas", "Richard", "Charles", "Christopher", 
                         "Daniel", "Matthew", "George", "Joseph", "Andrew", "Edward", "Mark", "Steven", "Paul", "Kenneth"],
                "female": ["Mary", "Patricia", "Jennifer", "Elizabeth", "Linda", "Barbara", "Susan", "Margaret", "Sarah", 
                           "Dorothy", "Jessica", "Helen", "Emily", "Karen", "Nancy", "Betty", "Lisa", "Sandra", "Ashley", "Kimberly"]
            },
            "USA": {
                "male": ["John", "Robert", "James", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Christopher", 
                         "Charles", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Andrew", "Paul", "Joshua"],
                "female": ["Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", 
                           "Karen", "Lisa", "Nancy", "Betty", "Margaret", "Sandra", "Ashley", "Kimberly", "Emily", "Amanda", "Melissa"]
            },
            "LIT": {
                "male": ["Jonas", "Tomas", "Lukas", "Mantas", "Darius", "Andrius", "Vytautas", "Mindaugas", "Gediminas", "Paulius", 
                         "Marius", "Rolandas", "Robertas", "Kęstutis", "Ričardas", "Valdas", "Algis", "Saulius", "Rimas", "Juozas"],
                "female": ["Greta", "Ieva", "Egle", "Ruta", "Laura", "Agne", "Lina", "Rasa", "Vaida", 
                           "Jurgita", "Aušra", "Ingrida", "Kristina", "Gabija", "Jovita", "Monika", "Simona", "Edita", "Dalia", "Inga"]
            },
            "ESP": {
                "male": ["Antonio", "José", "Manuel", "Francisco", "Juan", "David", "Javier", "Carlos", "Jesús", "Daniel", 
                         "Miguel", "Alejandro", "Rafael", "Pedro", "Ángel", "Fernando", "Pablo", "Luis", "Sergio", "Jorge"],
                "female": ["María", "Carmen", "Ana", "Laura", "Isabel", "Dolores", "Pilar", "Teresa", "Cristina", 
                           "Josefa", "Marta", "Rosario", "Lucía", "Mercedes", "Francisca", "Marina", "Elena", "Beatriz", "Rosa", "Raquel"]
            },
            "NLD": {
                "male": ["Jan", "Peter", "Johannes", "Hendrik", "Willem", "Cornelis", "Gerrit", "Johan", "Antonius", "Petrus", 
                         "Dirk", "Jacobus", "Martinus", "Nicolaas", "Franciscus", "Marinus", "Theodorus", "Paulus", "Wilhelmus", "Andreas"],
                "female": ["Maria", "Johanna", "Anna", "Elisabeth", "Cornelia", "Catharina", "Wilhelmina", "Petronella", "Adriana", 
                           "Hendrika", "Margaretha", "Geertruida", "Helena", "Jacoba", "Alida", "Gezina", "Aaltje", "Grietje", "Neeltje", "Trijntje"]
            }
        }
        
        self.last_names = {
            "POL": ["Nowak", "Kowalski", "Wiśniewski", "Wójcik", "Kowalczyk", "Kamiński", "Lewandowski", "Zieliński", "Szymański", "Woźniak",
                   "Dąbrowski", "Kozłowski", "Jankowski", "Mazur", "Kwiatkowski", "Krawczyk", "Piotrowski", "Grabowski", "Nowakowski", "Pawłowski"],
            "EST": ["Tamm", "Saar", "Sepp", "Mägi", "Kask", "Kukk", "Rebane", "Ilves", "Luik", "Koppel",
                   "Kaasik", "Saks", "Kuusk", "Raudsepp", "Oja", "Pärn", "Karu", "Vaher", "Teder", "Rand"],
            "FIN": ["Korhonen", "Virtanen", "Mäkinen", "Nieminen", "Mäkelä", "Hämäläinen", "Laine", "Heikkinen", "Koskinen", "Järvinen",
                   "Lehtonen", "Lehtinen", "Saarinen", "Salminen", "Heinonen", "Niemi", "Heikkilä", "Kinnunen", "Salonen", "Turunen"],
            "GBR": ["Smith", "Jones", "Williams", "Taylor", "Brown", "Davies", "Wilson", "Evans", "Thomas", "Johnson",
                   "Roberts", "Walker", "Wright", "Robinson", "Thompson", "White", "Hughes", "Edwards", "Green", "Hall"],
            "USA": ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor",
                   "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson"],
            "LIT": ["Kazlauskas", "Petrauskas", "Jankauskas", "Žukauskas", "Butkus", "Vasiliauskas", "Paulauskas", "Urbonas", "Kavaliauskas", "Stankevičius",
                   "Navickas", "Mickevičius", "Balčiūnas", "Ivanovas", "Lukoševičius", "Grigas", "Bakšys", "Žilinskas", "Vaitkus", "Valaitis"],
            "ESP": ["García", "Fernández", "González", "Rodríguez", "López", "Martínez", "Sánchez", "Pérez", "Gómez", "Martín",
                   "Jiménez", "Ruiz", "Hernández", "Díaz", "Moreno", "Álvarez", "Muñoz", "Romero", "Alonso", "Gutiérrez"],
            "NLD": ["De Jong", "Jansen", "De Vries", "Van den Berg", "Van Dijk", "Bakker", "Janssen", "Visser", "Smit", "Meijer",
                   "De Boer", "Mulder", "De Groot", "Bos", "Vos", "Peters", "Hendriks", "Van Leeuwen", "Dekker", "Brouwer"]
        }
    
    def _init_id_formats(self):
        """Initialize ID number formats for different nationalities"""
        self.id_formats = {
            "POL": lambda: f"{random.randint(1, 9)}{random.randint(1, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}",
            "EST": lambda: f"{random.randint(1, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}",
            "FIN": lambda: f"{random.randint(0, 3)}{random.randint(1, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}-{random.choice('ABCDEFHJKLMNPRSTUVWXY')}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}",
            "GBR": lambda: f"{random.choice('ABCEGHJKLMNPRSTWXYZ')}{random.choice('ABCEGHJKLMNPRSTWXYZ')}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.choice('ABCD')}",
            "USA": lambda: f"{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}-{random.randint(0, 9)}{random.randint(0, 9)}-{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}",
            "LIT": lambda: f"{random.randint(3, 6)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}",
            "ESP": lambda: f"{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}-{random.choice('ABCDEFGHJKLMNPQRSTVWXYZ')}",
            "NLD": lambda: f"{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"
        }
    
    def generate_person(self, nationality, gender=None):
        """Generate a complete person profile for the given nationality"""
        # If gender not specified, choose randomly
        if gender is None:
            gender = random.choice(['male', 'female'])
        
        # Default to USA if nationality not found
        if nationality not in self.first_names:
            nationality = "USA"
        
        # Generate first and last name
        first_name = random.choice(self.first_names[nationality][gender])
        last_name = random.choice(self.last_names[nationality])
        
        # Generate ID number if format exists
        id_number = None
        if nationality in self.id_formats:
            id_number = self.id_formats[nationality]()
        
        # Generate birthdate (between 18-50 years old)
        years_ago = random.randint(18, 50)
        days_variation = random.randint(-180, 180)
        birthdate = (datetime.datetime.now() - datetime.timedelta(days=365.25*years_ago + days_variation)).strftime("%Y-%m-%d")
        
        # Generate religion (optional)
        religions = [
            "1013", # Roman Catholic
            "1025", # Lutheran
            "1026", # Protestant
            "1049", # Anglican
            "1051", # Baptist
            "1068", # Orthodox
            "1077", # Methodist
            None,   # No religion
            None    # No religion (weighted to be more common)
        ]
        religion = random.choice(religions)
        
        # Generate random weight based on gender (more realistic distribution)
        if gender == 'male':
            weight = round(random.normalvariate(80, 12), 1)  # Male: mean 80kg, SD 12kg
        else:
            weight = round(random.normalvariate(65, 10), 1)  # Female: mean 65kg, SD 10kg
        
        # Generate blood type
        blood_type = random.choice(["A", "B", "AB", "O"])
        
        return {
            "family_name": last_name,
            "given_name": first_name,
            "gender": gender,
            "id_number": id_number,
            "birthdate": birthdate,
            "nationality": nationality,
            "religion": religion,
            "weight": weight,
            "blood_type": blood_type
        }