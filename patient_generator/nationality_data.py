# patient_generator/nationality_data.py
import json
import os
from typing import Any, Dict, List, Optional

# Assuming schemas_config.py contains NationalityConfig Pydantic model
# from .schemas_config import NationalityConfig # Not strictly needed for this data provider class itself


class NationalityDataProvider:
    _data: Dict[str, Any] = {}
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, data_file_path: Optional[str] = None):
        if self._initialized:
            return

        if data_file_path is None:
            # Default path relative to this file's directory or project root
            # Assuming this file is in patient_generator directory
            base_dir = os.path.dirname(os.path.abspath(__file__))
            data_file_path = os.path.join(base_dir, "demographics.json")

        if not os.path.exists(data_file_path):
            # Fallback if not found in patient_generator, try one level up (project root)
            # This might happen if the script is run from the project root
            # and the path was meant to be relative to that.
            # However, for a module, relative to its own location is more robust.
            # For now, let's assume it's correctly placed in patient_generator/
            print(f"Warning: Demographics data file not found at {data_file_path}")
            # Try path relative to CWD if it's different from script's dir
            # cwd_data_file_path = os.path.join(os.getcwd(), "patient_generator", "demographics.json")
            # if os.path.exists(cwd_data_file_path):
            #     data_file_path = cwd_data_file_path
            # else:
            #     self._data = {} # Initialize with empty data if file not found
            #     self._initialized = True
            #     raise FileNotFoundError(f"Demographics data file not found at {data_file_path}")
            # For simplicity, if not found at expected path, we'll operate with empty data or raise.
            # Let's raise for now to make it explicit if the file is missing.
            msg = f"Demographics data file not found at {data_file_path}. Ensure 'demographics.json' is in the 'patient_generator' directory."
            raise FileNotFoundError(msg)

        try:
            with open(data_file_path, encoding="utf-8") as f:
                self._data = json.load(f).get("NATO_NATIONS", {})
            print(f"Successfully loaded demographics data from {data_file_path}")
        except FileNotFoundError:
            print(f"Error: Demographics data file not found at {data_file_path}.")
            self._data = {}  # Initialize with empty data
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {data_file_path}.")
            self._data = {}  # Initialize with empty data
        except Exception as e:
            print(f"An unexpected error occurred while loading demographics data: {e}")
            self._data = {}

        self._initialized = True

    def get_nationality_data(self, country_code: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves all data for a given NATO country code (e.g., "USA").
        Returns None if the country code is not found.
        """
        return self._data.get(country_code.upper())

    def list_available_nationalities(self) -> List[Dict[str, str]]:
        """
        Lists all available NATO nationalities with their codes and names.
        """
        return [{"code": code, "name": details.get("name", "N/A")} for code, details in self._data.items()]

    def get_first_names(self, country_code: str, gender: str) -> Optional[List[str]]:
        """
        Retrieves a list of first names for a given country code and gender ('male' or 'female').
        """
        nation_data = self.get_nationality_data(country_code)
        if nation_data:
            return nation_data.get("first_names", {}).get(gender.lower())
        return None

    def get_last_names(self, country_code: str) -> Optional[List[str]]:
        """
        Retrieves a list of last names for a given country code.
        """
        nation_data = self.get_nationality_data(country_code)
        if nation_data:
            return nation_data.get("last_names")
        return None

    def get_id_format(self, country_code: str) -> Optional[str]:
        """
        Retrieves the ID format (regex string) for a given country code.
        """
        nation_data = self.get_nationality_data(country_code)
        if nation_data:
            return nation_data.get("id_format")
        return None

    def get_id_generator_script(self, country_code: str) -> Optional[str]:
        """
        Retrieves the ID generator JavaScript function string for a given country code.
        Note: Executing this script requires a JavaScript runtime.
        """
        nation_data = self.get_nationality_data(country_code)
        if nation_data:
            return nation_data.get("id_generator")
        return None

    def get_language_codes(self, country_code: str) -> Optional[List[str]]:
        """
        Retrieves the language code(s) for a given country code.
        Returns a list of strings, as some countries have multiple official languages.
        """
        nation_data = self.get_nationality_data(country_code)
        if nation_data:
            languages_str = nation_data.get("language")
            if languages_str:
                return [lang.strip() for lang in languages_str.split(",")]
        return None


# Example Usage (for testing or direct use):
# if __name__ == "__main__":
#     try:
#         provider = NationalityDataProvider() # Assumes demographics.json is in the same directory or accessible
#         print("Available Nationalities:", provider.list_available_nationalities())
#         usa_data = provider.get_nationality_data("USA")
#         if usa_data:
#             print("\nUSA Data:", usa_data["name"])
#             print("Male Names:", provider.get_first_names("USA", "male")[:5])
#             print("Last Names:", provider.get_last_names("USA")[:5])
#             print("ID Format:", provider.get_id_format("USA"))
#             # print("ID Generator Script:", provider.get_id_generator_script("USA"))
#             print("Languages:", provider.get_language_codes("USA"))

#         bel_data = provider.get_nationality_data("BEL")
#         if bel_data:
#             print("\nBelgium Languages:", provider.get_language_codes("BEL"))

#     except FileNotFoundError as e:
#         print(e)
#     except Exception as e:
#         print(f"An error occurred during example usage: {e}")
