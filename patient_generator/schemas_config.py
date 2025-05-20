# patient_generator/schemas_config.py
from pydantic import BaseModel, validator, Field
from typing import List, Dict, Optional, Any # Removed Callable as it's not directly used now
from datetime import datetime

# Forward declaration for recursive models if needed, though not immediately apparent here.

class NationalityDistributionItem(BaseModel):
    nationality_code: str = Field(..., description="ISO 3166-1 alpha-3 country code")
    percentage: float = Field(..., ge=0, le=100, description="Percentage for this nationality")

class FrontConfig(BaseModel):
    id: str = Field(..., description="Unique identifier for the front")
    name: str = Field(..., description="Display name of the front")
    description: Optional[str] = Field(None, description="Optional description of the front")
    nationality_distribution: List[NationalityDistributionItem] = Field(..., description="List of nationality distributions, percentages should sum to 100")
    casualty_rate: Optional[float] = Field(None, description="Overall casualty rate from this front (e.g., 0.1 for 10%)")
    # additional_params: Dict[str, Any] = {} # For future extensibility

    @validator('nationality_distribution')
    def validate_distribution_sum(cls, v: List[NationalityDistributionItem]):
        if not v:
            # Depending on requirements, an empty list might be valid or not.
            # If it must be non-empty, raise ValueError here.
            # For now, assume it can be empty, or the UI/creation logic ensures it's not.
            return v
        total_percentage = sum(item.percentage for item in v)
        if abs(total_percentage - 100.0) > 0.1: # Tolerance for float sum
            raise ValueError("Nationality distribution percentages must sum to 100")
        # Individual item.percentage validation (0-100) is handled by NationalityDistributionItem's Field definition.
        return v

    @validator('casualty_rate')
    def validate_casualty_rate(cls, v: Optional[float]):
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("Casualty rate must be between 0.0 and 1.0")
        return v

class NationalityConfig(BaseModel): # Primarily for reference data structure
    code: str = Field(..., description="ISO 3166-1 alpha-3 country code (e.g., DEU)")
    name: str = Field(..., description="Full name of the nation (e.g., Germany)")
    demographics_source: str = Field(..., description="Reference to detailed demographics data (e.g., filename or DB key)")
    id_format_type: Optional[str] = Field(None, description="Type/name of ID formatting function/template to use")
    language: Optional[str] = Field(None, description="Primary language ISO 639-1 code (e.g., de)")
    # additional_params: Dict[str, Any] = {}

class FacilityConfig(BaseModel):
    id: str = Field(..., description="Unique identifier for the facility (e.g., R1, R2_Alpha)")
    name: str = Field(..., description="Display name of the facility")
    description: Optional[str] = Field(None, description="Optional description")
    capacity: Optional[int] = Field(None, gt=0, description="Patient capacity (must be > 0 if specified)")
    kia_rate: float = Field(..., ge=0.0, le=1.0, description="KIA probability at this facility (0.0 to 1.0)")
    rtd_rate: float = Field(..., ge=0.0, le=1.0, description="RTD probability from this facility (0.0 to 1.0)")
    # Evacuation path is determined by the order in ConfigurationTemplate.facility_configs

    @validator('kia_rate', 'rtd_rate')
    def check_rates_valid(cls, v: float):
        # ge/le in Field definition handles 0-1. This validator is mostly a placeholder
        # if more complex cross-field validation (e.g. kia_rate + rtd_rate <= 1) were needed here.
        # For now, individual validity is sufficient.
        return v
    
    @validator('rtd_rate') # Example of cross-field validation if needed
    def check_total_probabilities(cls, v: float, values: Dict[str, Any]):
        kia_rate = values.get('kia_rate')
        if kia_rate is not None and (v + kia_rate > 1.0):
            raise ValueError("Sum of KIA rate and RTD rate cannot exceed 1.0")
        return v


class ConfigurationTemplate(BaseModel):
    id: Optional[str] = Field(None, description="Unique identifier for the saved configuration (e.g., UUID, assigned on save)")
    name: str = Field(..., min_length=1, description="User-defined name for this configuration template")
    description: Optional[str] = Field(None, description="Optional description for the template")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Timestamp of creation")
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Timestamp of last update")
    
    front_configs: List[FrontConfig] = Field(..., description="List of combat front configurations")
    facility_configs: List[FacilityConfig] = Field(..., description="Ordered list of medical facility configurations defining the evac chain")
    
    total_patients: int = Field(..., gt=0, description="Total number of patients to generate for this scenario")
    injury_distribution: Dict[str, float] = Field(..., description="Overall distribution of injury types (percentages summing to 100)")

    version: int = Field(default=1, ge=1, description="Version number of the configuration template")
    parent_config_id: Optional[str] = Field(None, description="ID of the parent template this was derived from, if any")

    @validator('facility_configs')
    def validate_facility_ids_unique(cls, v: List[FacilityConfig]):
        if not v: # An evacuation chain must have at least one facility
            raise ValueError("Facility configurations cannot be empty.")
        ids = [facility.id for facility in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Facility IDs within a configuration must be unique")
        return v

    @validator('front_configs')
    def validate_front_ids_unique(cls, v: List[FrontConfig]):
        if not v: # A scenario must have at least one front
            raise ValueError("Front configurations cannot be empty.")
        ids = [front.id for front in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Front IDs within a configuration must be unique")
        return v
        
    @validator('injury_distribution')
    def validate_injury_distribution_sum(cls, v: Dict[str, float]):
        if not v:
            raise ValueError("Injury distribution cannot be empty")
        total = sum(v.values())
        if abs(total - 100.0) > 0.1: # Tolerance for float sum
            raise ValueError("Injury distribution percentages must sum to 100")
        for percentage in v.values():
            if not (0 <= percentage <= 100):
                raise ValueError("Injury distribution percentages must be between 0 and 100")
        return v

# API Specific Models
class ConfigurationTemplateCreate(BaseModel): # Model for creating a new template via API. Inherits from BaseModel directly.
    name: str = Field(..., min_length=1, description="User-defined name for this configuration template")
    description: Optional[str] = Field(None, description="Optional description for the template")
    # Fields from ConfigurationTemplate that are provided on creation:
    front_configs: List[FrontConfig]
    facility_configs: List[FacilityConfig]
    total_patients: int = Field(..., gt=0)
    injury_distribution: Dict[str, float] = Field(..., description="Overall distribution of injury types (percentages summing to 100)")
    parent_config_id: Optional[str] = Field(None, description="Optional ID of a parent template to denote derivation")
    # version will default to 1 if not provided, or can be set if creating a new version of an existing one (app logic dependent)
    version: Optional[int] = Field(default=1, ge=1, description="Version number, defaults to 1 for new templates")


    # Validators are inherited from the field definitions in FrontConfig, FacilityConfig
    # and the main ConfigurationTemplate model if this inherited from it.
    # Since it inherits from BaseModel, we need to redefine or ensure they are called.
    # Pydantic v2 automatically runs validators for nested models.
    # For clarity, specific validators for create context can be added if behavior differs.

    # Example: if we wanted to ensure front_configs is not empty specifically on create
    @validator('front_configs')
    def check_front_configs_on_create(cls, v: List[FrontConfig]):
        if not v:
            raise ValueError("Front configurations cannot be empty on creation.")
        # Call parent validator if this class inherited from ConfigurationTemplate
        # For now, Pydantic will validate each FrontConfig item internally.
        # Re-validating uniqueness here as well for safety, though Pydantic might do it.
        ids = [front.id for front in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Front IDs within a configuration must be unique")
        return v

    @validator('facility_configs')
    def check_facility_configs_on_create(cls, v: List[FacilityConfig]):
        if not v:
            raise ValueError("Facility configurations cannot be empty on creation.")
        ids = [facility.id for facility in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Facility IDs within a configuration must be unique")
        return v

    @validator('injury_distribution')
    def check_injury_distribution_on_create(cls, v: Dict[str, float]):
        if not v:
            raise ValueError("Injury distribution cannot be empty on creation")
        total = sum(v.values())
        if abs(total - 100.0) > 0.1:
            raise ValueError("Injury distribution percentages must sum to 100")
        for percentage in v.values():
            if not (0 <= percentage <= 100):
                raise ValueError("Injury distribution percentages must be between 0 and 100")
        return v


class ConfigurationTemplateDB(ConfigurationTemplate): # Model for representing template from DB
    id: str = Field(..., description="Unique identifier for the saved configuration")
    # Override fields from parent. Since parent had default_factory, child must specify a default.
    # Using default=... marks them as required, expecting values from DB.
    created_at: datetime = Field(default=..., description="Timestamp of creation")
    updated_at: datetime = Field(default=..., description="Timestamp of last update")
    # version and parent_config_id are inherited from ConfigurationTemplate

    class Config:
        # orm_mode = True # Pydantic V1
        from_attributes = True # Pydantic V2
