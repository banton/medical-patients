import random
import datetime
from typing import Dict, Any, Optional

# Use absolute imports
try:
    from .nationality_data import NationalityDataProvider
except ImportError:
    # Fallback for direct execution or different project structures
    from patient_generator.nationality_data import NationalityDataProvider

# Consider using a library like 'rstr' or 'exrex' for generating strings from regex if needed.
# For now, a placeholder or simplified approach for ID generation from regex.
# import rstr # Example, would need to be added to requirements.txt

class DemographicsGenerator:
    """Generates realistic demographics based on nationality using NationalityDataProvider."""
    
    def __init__(self, nationality_provider: Optional[NationalityDataProvider] = None):
        """
        Initializes the DemographicsGenerator.
        Args:
            nationality_provider: An instance of NationalityDataProvider. 
                                  If None, a default instance will be created.
        """
        self.provider = nationality_provider or NationalityDataProvider()
        
    def _generate_id_from_regex(self, regex_pattern: str) -> str:
        """
        Generates a string that loosely matches a given regex pattern.
        This is a simplified placeholder. For robust generation from complex regex,
        a dedicated library (e.g., 'exrex', 'rstr') would be better.
        """
        # Placeholder: Replaces common regex constructs with random examples.
        # This is very basic and won't cover all regex complexities.
        # Example: \d -> random digit, [A-Z] -> random uppercase letter
        generated_id = ""
        i = 0
        while i < len(regex_pattern):
            char = regex_pattern[i]
            if char == '\\':
                if i + 1 < len(regex_pattern):
                    next_char = regex_pattern[i+1]
                    if next_char == 'd':
                        generated_id += str(random.randint(0, 9))
                    else:
                        generated_id += next_char # Keep escaped char like \.
                    i += 1
                else:
                    generated_id += char # Trailing backslash
            elif char == '[':
                # Basic range, e.g., [A-Z], [0-9]
                try:
                    end_bracket = regex_pattern.index(']', i)
                    range_content = regex_pattern[i+1:end_bracket]
                    if range_content == "A-Z":
                        generated_id += chr(random.randint(65, 90))
                    elif range_content == "a-z":
                        generated_id += chr(random.randint(97, 122))
                    elif range_content == "0-9":
                        generated_id += str(random.randint(0,9))
                    else: # If more complex, just pick a char from it or a placeholder
                        generated_id += random.choice(range_content) if range_content else "?"
                    i = end_bracket
                except ValueError: # No closing bracket, treat as literal
                    generated_id += char
            elif char in '.?*+{}()|^$': # Special regex chars, ignore or handle simply
                pass # For this basic generator, we might skip them or add a placeholder
            else:
                generated_id += char
            i += 1
        # If generated_id is too short due to skipping special chars, pad it.
        # This is highly dependent on the complexity of regex_pattern.
        # A real implementation would use a proper regex generation library.
        if not generated_id:
            return "ID_GEN_ERROR"
        return generated_id


    def generate_person(self, nationality_code: str, gender: Optional[str] = None) -> Dict[str, Any]:
        """Generate a complete person profile for the given nationality code."""
        
        nat_data = self.provider.get_nationality_data(nationality_code)
        if not nat_data:
            print(f"Warning: Nationality code '{nationality_code}' not found in demographics data. Defaulting to placeholder.")
            # Fallback to some very generic data or raise error
            return {
                "family_name": "Doe", "given_name": "John" if gender != 'female' else "Jane",
                "gender": gender or random.choice(['male', 'female']), "id_number": "N/A",
                "birthdate": (datetime.datetime.now() - datetime.timedelta(days=365.25*30)).strftime("%Y-%m-%d"),
                "nationality": nationality_code, "religion": None, "weight": 70.0, "blood_type": "O"
            }

        if gender is None:
            gender = random.choice(['male', 'female'])
        elif gender.lower() not in ['male', 'female']:
            print(f"Warning: Invalid gender '{gender}' provided. Defaulting to random.")
            gender = random.choice(['male', 'female'])
        
        first_names = self.provider.get_first_names(nationality_code, gender)
        last_names = self.provider.get_last_names(nationality_code)

        first_name = random.choice(first_names) if first_names else "FN_Placeholder"
        last_name = random.choice(last_names) if last_names else "LN_Placeholder"
        
        id_number_format_regex = self.provider.get_id_format(nationality_code)
        id_number = None
        if id_number_format_regex:
            # id_number = rstr.xeger(id_number_format_regex) # Example with rstr library
            id_number = self._generate_id_from_regex(id_number_format_regex) # Using placeholder
        else:
            id_number = "ID_FORMAT_UNAVAILABLE"
            
        years_ago = random.randint(18, 50)
        days_variation = random.randint(-180, 180) # Approx +/- 6 months
        birthdate_dt = datetime.date.today() - datetime.timedelta(days=int(365.25 * years_ago) + days_variation)
        birthdate = birthdate_dt.strftime("%Y-%m-%d")
        
        religions = [ # TODO: Make this configurable or nationality-specific
            "1013", "1025", "1026", "1049", "1051", "1068", "1077", None, None
        ]
        religion = random.choice(religions)
        
        weight = round(random.normalvariate(80 if gender == 'male' else 65, 12 if gender == 'male' else 10), 1)
        blood_type = random.choice(["A", "B", "AB", "O"]) # TODO: Could be nationality-specific distribution
        
        return {
            "family_name": last_name,
            "given_name": first_name,
            "gender": gender,
            "id_number": id_number,
            "birthdate": birthdate,
            "nationality": nationality_code, # Store the code
            "religion": religion,
            "weight": weight,
            "blood_type": blood_type,
            "language_codes": self.provider.get_language_codes(nationality_code) # Add language
        }

# Example Usage:
# if __name__ == "__main__":
#     try:
#         # Ensure demographics.json is in the same directory as nationality_data.py for this example
#         # Or provide the correct path to NationalityDataProvider
#         demo_gen = DemographicsGenerator()
#         print("USA Person:", demo_gen.generate_person("USA", "male"))
#         print("\nPOL Person:", demo_gen.generate_person("POL", "female"))
#         print("\nDEU Person:", demo_gen.generate_person("DEU")) # Random gender
#         # Test a country not in the original hardcoded list but in JSON
#         print("\nFRA Person:", demo_gen.generate_person("FRA"))
#         # Test a country that might be missing from JSON (should use fallback)
#         # print("\nXYZ Person:", demo_gen.generate_person("XYZ")) 
#     except FileNotFoundError as e:
#         print(f"Error during example: {e}")
#     except Exception as e:
#         print(f"An unexpected error occurred in DemographicsGenerator example: {e}")
