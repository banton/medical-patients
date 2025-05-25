# Simplified schemas_config.py for quick startup fix
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Simplified models without validators for immediate startup fix
class NationalityDistributionItem(BaseModel):
    nationality_code: str = Field(..., description="ISO 3166-1 alpha-3 country code")
    percentage: float = Field(..., ge=0, le=100, description="Percentage for this nationality")

class FrontConfig(BaseModel):
    id: str = Field(..., description="Unique identifier for the front")
    name: str = Field(..., description="Display name of the front")
    nationality_distribution: List[NationalityDistributionItem] = Field(
        ..., description="Distribution of nationalities"
    )
    casualty_rate: Optional[float] = Field(None, description="Overall casualty rate from this front")

class FacilityConfig(BaseModel):
    id: str = Field(..., description="Unique identifier for the facility")
    name: str = Field(..., description="Display name of the facility")
    description: Optional[str] = Field(None, description="Optional description")
    capacity: Optional[int] = Field(None, gt=0, description="Patient capacity")
    kia_rate: float = Field(..., ge=0.0, le=1.0, description="KIA probability at this facility")
    rtd_rate: float = Field(..., ge=0.0, le=1.0, description="RTD probability from this facility")

class ConfigurationTemplateBase(BaseModel):
    name: str = Field(..., description="Name of the configuration template")
    description: Optional[str] = Field(None, description="Optional description")
    front_configs: List[FrontConfig] = Field(..., description="List of front configurations")
    facility_configs: List[FacilityConfig] = Field(..., description="List of facility configurations")
    total_patients: int = Field(..., gt=0, description="Total number of patients to generate")
    injury_distribution: Dict[str, float] = Field(
        ..., description="Overall distribution of injury types"
    )
    version: Optional[int] = Field(default=1, ge=1, description="Version number")
    parent_config_id: Optional[str] = Field(None, description="ID of the parent template")

class ConfigurationTemplateCreate(ConfigurationTemplateBase):
    version: Optional[int] = Field(default=1, ge=1, description="Version number, defaults to 1 for new templates")

class ConfigurationTemplateDB(ConfigurationTemplateBase):
    id: str = Field(..., description="Unique identifier for the template")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

# Reference data models
class NationalityConfig(BaseModel):
    code: str = Field(..., description="ISO 3166-1 alpha-3 country code")
    name: str = Field(..., description="Display name of the nationality")

class FrontDefinitionNation(BaseModel):
    nationality_code: str = Field(..., description="ISO 3166-1 alpha-3 country code")
    percentage: float = Field(..., ge=0.0, le=100.0, description="Percentage of this nationality within the front")

class FrontDefinition(BaseModel):
    name: str = Field(..., description="Display name of the front")
    ratio: float = Field(..., ge=0.0, le=1.0, description="Ratio of total soldiers/patients allocated to this front")
    nations: List[FrontDefinitionNation] = Field(..., description="List of nations participating in this front")

class FrontsConfiguration(BaseModel):
    fronts: List[FrontDefinition] = Field(..., description="List of battle front definitions")