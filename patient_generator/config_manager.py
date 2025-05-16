# patient_generator/config_manager.py
from typing import Optional, Dict, Any, List # Added List
from .database import Database, ConfigurationRepository
from .schemas_config import ConfigurationTemplateDB

class ConfigurationManager:
    """
    Manages loading and providing access to the active scenario configuration template.
    """
    _active_configuration: Optional[ConfigurationTemplateDB] = None
    _config_id_loaded: Optional[str] = None
    _repository: ConfigurationRepository

    def __init__(self, database_instance: Optional[Database] = None):
        """
        Initializes the ConfigurationManager.
        If database_instance is not provided, it gets a default instance.
        """
        db = database_instance or Database.get_instance()
        self._repository = ConfigurationRepository(db)
        # Note: Consider if loading a default config immediately is desired,
        # or if it should wait for an explicit load_configuration call.

    def load_configuration(self, config_id: str) -> bool:
        """
        Loads a specific configuration template by its ID and sets it as active.
        Returns True if successful, False otherwise.
        """
        try:
            config = self._repository.get_configuration(config_id)
            if config:
                self._active_configuration = config
                self._config_id_loaded = config_id
                print(f"Successfully loaded configuration: {config.name} (ID: {config_id})")
                return True
            else:
                print(f"Configuration with ID '{config_id}' not found.")
                self._active_configuration = None
                self._config_id_loaded = None
                return False
        except Exception as e:
            print(f"Error loading configuration ID '{config_id}': {e}")
            self._active_configuration = None
            self._config_id_loaded = None
            return False

    def get_active_configuration(self) -> Optional[ConfigurationTemplateDB]:
        """
        Returns the currently active configuration template.
        """
        if self._active_configuration is None:
            print("Warning: No active configuration loaded. Call load_configuration() first or set a default.")
        return self._active_configuration

    def get_config_value(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Retrieves a specific value from the active configuration by key.
        This is a generic getter; specific getters for fronts, facilities etc. are preferred.
        """
        if self._active_configuration:
            return getattr(self._active_configuration, key, default)
        return default

    # Specific getters for commonly accessed configuration parts
    def get_front_configs(self) -> Optional[List[Dict[str, Any]]]: # Returns list of dicts from Pydantic model
        if self._active_configuration:
            # Convert Pydantic FrontConfig models to dicts if downstream code expects dicts
            return [fc.model_dump() for fc in self._active_configuration.front_configs]
        return None

    def get_facility_configs(self) -> Optional[List[Dict[str, Any]]]: # Returns list of dicts
        if self._active_configuration:
            return [fc.model_dump() for fc in self._active_configuration.facility_configs]
        return None

    def get_injury_distribution(self) -> Optional[Dict[str, float]]:
        if self._active_configuration:
            return self._active_configuration.injury_distribution
        return None

    def get_total_patients(self) -> Optional[int]:
        if self._active_configuration:
            return self._active_configuration.total_patients
        return None

    def is_configuration_loaded(self) -> bool:
        """Checks if a configuration is currently loaded."""
        return self._active_configuration is not None

# Example Usage:
# if __name__ == '__main__':
#     # This example assumes the DB is up and has some configurations.
#     # You would typically run this within your FastAPI app or generation script.
#     try:
#         db_manager = Database.get_instance() # Initializes DB connection pool
#         config_manager = ConfigurationManager(db_manager)
        
#         # Example: Load a configuration (replace 'your_config_id' with an actual ID)
#         # First, create one if it doesn't exist using ConfigurationRepository directly or an API
#         # repo = ConfigurationRepository(db_manager)
#         # from .schemas_config import ConfigurationTemplateCreate, FrontConfig, FacilityConfig
#         # dummy_front = FrontConfig(id="f1", name="Test Front", nationality_distribution={"USA": 100.0})
#         # dummy_facility = FacilityConfig(id="r1", name="Role 1", kia_rate=0.1, rtd_rate=0.2)
#         # test_config_create = ConfigurationTemplateCreate(
#         #     name="Test Scenario Alpha",
#         #     front_configs=[dummy_front],
#         #     facility_configs=[dummy_facility],
#         #     total_patients=100,
#         #     injury_distribution={"BATTLE_TRAUMA": 100.0}
#         # )
#         # created_config = repo.create_configuration(test_config_create)
#         # print(f"Created dummy config with ID: {created_config.id}")
#         # your_config_id = created_config.id

#         your_config_id = "some_existing_config_id" # Replace with a real ID from your DB
        
#         if config_manager.load_configuration(your_config_id):
#             active_conf = config_manager.get_active_configuration()
#             if active_conf:
#                 print(f"\nActive configuration name: {active_conf.name}")
#                 print(f"Total patients: {config_manager.get_total_patients()}")
#                 fronts = config_manager.get_front_configs()
#                 if fronts:
#                     print(f"First front name: {fronts[0]['name']}")
#         else:
#             print(f"Could not load configuration with ID: {your_config_id}")
            
#     except Exception as e:
#         print(f"An error occurred in ConfigurationManager example: {e}")
#     finally:
#         if 'db_manager' in locals():
#             db_manager.close_pool()
