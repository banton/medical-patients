# patient_generator/schemas_config.py
from datetime import datetime
from typing import Any, Dict, List, Optional  # Removed Callable as it's not directly used now

from pydantic import BaseModel, Field, validator

# Forward declaration for recursive models if needed, though not immediately apparent here.

# --- Base Configuration Models ---


class NationalityDistributionItem(BaseModel):
    nationality_code: str = Field(..., description="ISO 3166-1 alpha-3 country code")
    percentage: float = Field(
        ..., ge=0, le=100, description="Percentage for this nationality, must be between 0 and 100"
    )


class FrontConfig(BaseModel):
    id: str = Field(..., description="Unique identifier for the front")
    name: str = Field(..., description="Display name of the front")
    description: Optional[str] = Field(None, description="Optional description of the front")
    nationality_distribution: List[NationalityDistributionItem] = Field(
        ...,
        description="Distribution of nationalities. Must contain at least one item, and percentages must sum to 100.",
    )
    casualty_rate: Optional[float] = Field(
        None, description="Overall casualty rate from this front (e.g., 0.1 for 10%)"
    )
    # additional_params: Dict[str, Any] = {} # For future extensibility

    @validator("nationality_distribution")
    def validate_nationality_distribution(self, v: List[NationalityDistributionItem]):
        if not v:
            msg = "Nationality distribution must contain at least one nationality."
            raise ValueError(msg)

        total_percentage = sum(item.percentage for item in v)
        if abs(total_percentage - 100.0) > 0.1:  # Tolerance for float sum
            msg = "Nationality distribution percentages must sum to 100."
            raise ValueError(msg)

        seen_nationalities = set()
        for item in v:
            if not (
                0 <= item.percentage <= 100
            ):  # This check is somewhat redundant due to NationalityDistributionItem's Field
                msg = f"Percentage for {item.nationality_code} must be between 0 and 100."
                raise ValueError(msg)
            if item.nationality_code in seen_nationalities:
                msg = f"Duplicate nationality_code '{item.nationality_code}' in distribution."
                raise ValueError(msg)
            seen_nationalities.add(item.nationality_code)
        return v

    @validator("casualty_rate")
    def validate_casualty_rate(self, v: Optional[float]):
        if v is not None and not (0.0 <= v <= 1.0):
            msg = "Casualty rate must be between 0.0 and 1.0"
            raise ValueError(msg)
        return v


class NationalityConfig(BaseModel):  # Primarily for reference data structure, not directly part of main config template
    code: str = Field(..., description="ISO 3166-1 alpha-3 country code (e.g., DEU)")
    name: str = Field(..., description="Full name of the nation (e.g., Germany)")
    demographics_source: str = Field(
        ..., description="Reference to detailed demographics data (e.g., filename or DB key)"
    )
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

    @validator("kia_rate", "rtd_rate")
    def check_rates_valid(self, v: float):
        # ge/le in Field definition handles 0-1. This validator is mostly a placeholder
        # if more complex cross-field validation (e.g. kia_rate + rtd_rate <= 1) were needed here.
        # For now, individual validity is sufficient.
        return v

    @validator("rtd_rate")  # Example of cross-field validation if needed
    def check_total_probabilities(self, v: float, values: Dict[str, Any]):
        kia_rate = values.get("kia_rate")
        if kia_rate is not None and (v + kia_rate > 1.0):
            msg = "Sum of KIA rate and RTD rate cannot exceed 1.0"
            raise ValueError(msg)
        return v


# --- Configuration Template Models ---


class ConfigurationTemplateBase(BaseModel):
    """Base model for common configuration template fields."""

    name: str = Field(..., min_length=1, description="User-defined name for this configuration template")
    description: Optional[str] = Field(None, description="Optional description for the template")

    front_configs: List[FrontConfig] = Field(..., description="List of combat front configurations")
    facility_configs: List[FacilityConfig] = Field(
        ..., description="Ordered list of medical facility configurations defining the evac chain"
    )

    total_patients: int = Field(..., gt=0, description="Total number of patients to generate for this scenario")
    injury_distribution: Dict[str, float] = Field(
        ...,
        description="Overall distribution of injury types (Battle Injury, Disease, Non-Battle Injury), percentages summing to 100",
    )

    version: Optional[int] = Field(
        default=1, ge=1, description="Version number of the configuration template"
    )  # Made Optional for consistency
    parent_config_id: Optional[str] = Field(None, description="ID of the parent template this was derived from, if any")

    @validator("facility_configs")
    def validate_facility_ids_unique(self, v: List[FacilityConfig]):
        if not v:
            msg = "Facility configurations cannot be empty."
            raise ValueError(msg)
        ids = [facility.id for facility in v]
        if len(ids) != len(set(ids)):
            msg = "Facility IDs within a configuration must be unique"
            raise ValueError(msg)
        return v

    @validator("front_configs")
    def validate_front_ids_unique(self, v: List[FrontConfig]):
        if not v:
            msg = "Front configurations cannot be empty."
            raise ValueError(msg)
        ids = [front.id for front in v]
        if len(ids) != len(set(ids)):
            msg = "Front IDs within a configuration must be unique"
            raise ValueError(msg)
        return v

    @validator("injury_distribution")
    def validate_injury_distribution(self, v: Dict[str, float]):
        EXPECTED_KEYS = {"Battle Injury", "Disease", "Non-Battle Injury"}

        if not v:
            msg = "Injury distribution cannot be empty and must contain Battle Injury, Disease, and Non-Battle Injury."
            raise ValueError(msg)

        if set(v.keys()) != EXPECTED_KEYS:
            msg = f"Injury distribution must contain exactly the keys: {', '.join(EXPECTED_KEYS)}."
            raise ValueError(msg)

        total_percentage = sum(v.values())
        if abs(total_percentage - 100.0) > 0.1:  # Tolerance for float sum
            msg = "Injury distribution percentages must sum to 100."
            raise ValueError(msg)

        for key, percentage in v.items():
            if not (0 <= percentage <= 100):
                msg = f"Percentage for injury type '{key}' must be between 0 and 100."
                raise ValueError(msg)
        return v


# class InjuryDistributionItem(BaseModel): # No longer needed
#     type: str = Field(..., description="Type of injury")
#     percentage: float = Field(..., ge=0, le=100, description="Percentage for this injury type")


class ConfigurationTemplate(ConfigurationTemplateBase):
    """General configuration template model, includes optional ID and timestamps with defaults."""

    id: Optional[str] = Field(
        None, description="Unique identifier for the saved configuration (e.g., UUID, assigned on save)"
    )
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Timestamp of creation")
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Timestamp of last update")


class ConfigurationTemplateCreate(ConfigurationTemplateBase):
    """Model for creating a new template via API. Inherits common fields from Base."""

    # name, description, front_configs, facility_configs, total_patients, injury_distribution, parent_config_id
    # are inherited from ConfigurationTemplateBase.
    # version is also inherited with its default. If it needs to be optional on create:
    version: Optional[int] = Field(default=1, ge=1, description="Version number, defaults to 1 for new templates")

    # Re-define validators if behavior needs to be stricter or different for creation context.
    # Pydantic V2 runs validators from base classes automatically.
    # These are redundant if base validators are sufficient.
    @validator("front_configs")
    def check_front_configs_on_create(self, v: List[FrontConfig]):  # Example if stricter check needed
        if not v:
            msg = "Front configurations cannot be empty on creation."
            raise ValueError(msg)
        # Base validator for uniqueness will also run.
        return v

    @validator("facility_configs")
    def check_facility_configs_on_create(self, v: List[FacilityConfig]):  # Example
        if not v:
            msg = "Facility configurations cannot be empty on creation."
            raise ValueError(msg)
        return v

    @validator("injury_distribution")
    def check_injury_distribution_on_create(self, v: Dict[str, float]):  # Validator for create
        # The main validator in ConfigurationTemplateBase will handle the detailed checks.
        # This one can be simpler or ensure non-emptiness if base allows empty for some reason.
        if not v:  # Should be caught by base, but as an example
            msg = "Injury distribution cannot be empty on creation."
            raise ValueError(msg)
        return v


class ConfigurationTemplateDB(ConfigurationTemplate):  # Model for representing template from DB
    id: str = Field(..., description="Unique identifier for the saved configuration")
    # Override fields from parent. Since parent had default_factory, child must specify a default.
    # Using default=... marks them as required, expecting values from DB.
    created_at: datetime = Field(default=..., description="Timestamp of creation")
    updated_at: datetime = Field(default=..., description="Timestamp of last update")
    # version and parent_config_id are inherited from ConfigurationTemplate

    class Config:
        from_attributes = True  # Pydantic V2


# --- Models for external fronts_config.json ---


class FrontDefinitionNation(BaseModel):
    nationality_code: str = Field(..., description="ISO 3166-1 alpha-3 country code")
    percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Percentage of this nationality within the front (sums to 100.0 for the front)",
    )

    @validator("percentage")
    def validate_percentage_range(self, v: float):
        if not (0.0 <= v <= 100.0):
            msg = "Nation percentage must be between 0.0 and 100.0"
            raise ValueError(msg)
        return v


class FrontDefinition(BaseModel):
    name: str = Field(..., description="Display name of the front")
    ratio: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Ratio of total soldiers/patients allocated to this front (sums to 1.0 across all fronts)",
    )
    nations: List[FrontDefinitionNation] = Field(
        ..., description="List of nations participating in this front and their percentages"
    )

    @validator("ratio")
    def validate_front_ratio_range(self, v: float):
        if not (0.0 <= v <= 1.0):
            msg = "Front ratio must be between 0.0 and 1.0"
            raise ValueError(msg)
        return v

    @validator("nations")
    def validate_nation_percentages_sum(self, v: List[FrontDefinitionNation]):
        if not v:
            msg = "Nations list cannot be empty for a front."
            raise ValueError(msg)
        total_nation_percentage = sum(nation.percentage for nation in v)
        if abs(total_nation_percentage - 100.0) > 0.1:  # Tolerance for float sum
            msg = "Sum of nation percentages within a front must be 100.0"
            raise ValueError(msg)
        return v


class FrontsConfiguration(BaseModel):
    fronts: List[FrontDefinition] = Field(..., description="List of battle front definitions")

    @validator("fronts")
    def validate_front_ratios_sum(self, v: List[FrontDefinition]):
        if not v:
            msg = "Fronts list cannot be empty in the configuration."
            raise ValueError(msg)
        total_front_ratio = sum(front.ratio for front in v)
        if abs(total_front_ratio - 1.0) > 0.001:  # Tolerance for float sum
            msg = "Sum of ratios for all fronts must be 1.0"
            raise ValueError(msg)
        # Ensure unique front names if necessary, though not strictly part of this task's JSON structure
        # names = [front.name for front in v]
        # if len(names) != len(set(names)):
        #     raise ValueError("Front names must be unique.")
        return v
