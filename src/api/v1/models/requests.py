"""
Standardized API request models with comprehensive validation.
All endpoints should use these request models for consistent input validation.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class GenerationRequest(BaseModel):
    """Enhanced request model for patient generation with comprehensive validation."""

    configuration_id: Optional[str] = Field(None, min_length=1, description="ID of existing configuration to use")

    configuration: Optional[Dict[str, Any]] = Field(
        None, description="Inline configuration object (alternative to configuration_id)"
    )

    output_formats: List[str] = Field(default=["json"], min_items=1, description="List of output formats to generate")

    use_compression: bool = Field(default=False, description="Whether to compress output files")

    use_encryption: bool = Field(default=False, description="Whether to encrypt output files")

    encryption_password: Optional[str] = Field(
        None, min_length=8, description="Password for encryption (required if use_encryption=True)"
    )

    priority: str = Field(default="normal", description="Job priority level")

    @field_validator("output_formats")
    @classmethod
    def validate_output_formats(cls, v):
        """Validate that all output formats are supported."""
        valid_formats = ["json", "csv", "xlsx", "xml", "fhir"]

        for fmt in v:
            if fmt not in valid_formats:
                msg = f"Invalid output format: {fmt}. Valid formats: {valid_formats}"
                raise ValueError(msg)

        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        """Validate priority level."""
        valid_priorities = ["low", "normal", "high"]
        if v not in valid_priorities:
            msg = f"Invalid priority: {v}. Valid priorities: {valid_priorities}"
            raise ValueError(msg)
        return v

    @model_validator(mode="after")
    def validate_configuration_source(self):
        """Validate that either configuration_id or configuration is provided, but not both."""
        config_id = self.configuration_id
        config_obj = self.configuration

        if not config_id and not config_obj:
            msg = "Either configuration_id or configuration must be provided"
            raise ValueError(msg)

        if config_id and config_obj:
            msg = "Provide either configuration_id or configuration, not both"
            raise ValueError(msg)

        return self

    @model_validator(mode="after")
    def validate_encryption_requirements(self):
        """Validate encryption password is provided when encryption is enabled."""
        use_encryption = self.use_encryption
        encryption_password = self.encryption_password

        if use_encryption and not encryption_password:
            msg = "encryption_password is required when use_encryption=True"
            raise ValueError(msg)

        if not use_encryption and encryption_password:
            # Clear password if encryption is disabled
            self.encryption_password = None

        return self

    class Config:
        """Pydantic configuration."""

        schema_extra = {
            "example": {
                "configuration_id": "nato-exercise-2024",
                "output_formats": ["json", "csv"],
                "use_compression": True,
                "use_encryption": False,
                "priority": "normal",
            }
        }


class ConfigurationCreateRequest(BaseModel):
    """Request model for creating new configurations."""

    name: str = Field(..., min_length=1, max_length=100, description="Configuration name")

    description: Optional[str] = Field(None, max_length=500, description="Configuration description")

    template: Dict[str, Any] = Field(..., description="Configuration template data")

    is_active: bool = Field(default=True, description="Whether configuration should be active")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate configuration name."""
        if not v.strip():
            msg = "Configuration name cannot be empty"
            raise ValueError(msg)
        return v.strip()

    @field_validator("template")
    @classmethod
    def validate_template(cls, v):
        """Basic template validation."""
        if not isinstance(v, dict):
            msg = "Template must be a dictionary"
            raise ValueError(msg)

        required_fields = ["demographics", "medical", "count"]
        for field in required_fields:
            if field not in v:
                msg = f"Template missing required field: {field}"
                raise ValueError(msg)

        return v

    class Config:
        """Pydantic configuration."""

        schema_extra = {
            "example": {
                "name": "NATO Exercise 2024",
                "description": "Configuration for NATO medical exercise",
                "template": {
                    "demographics": {"nationalities": ["US", "GB", "DE"]},
                    "medical": {"injury_severity": "mixed"},
                    "count": 100,
                },
                "is_active": True,
            }
        }


class ConfigurationUpdateRequest(BaseModel):
    """Request model for updating existing configurations."""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated configuration name")

    description: Optional[str] = Field(None, max_length=500, description="Updated configuration description")

    template: Optional[Dict[str, Any]] = Field(None, description="Updated configuration template data")

    is_active: Optional[bool] = Field(None, description="Whether configuration should be active")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v):
        """Validate configuration name if provided."""
        if v is not None and not v.strip():
            msg = "Configuration name cannot be empty"
            raise ValueError(msg)
        return v.strip() if v else v

    @field_validator("template")
    @classmethod
    def validate_template(cls, v):
        """Basic template validation if provided."""
        if v is not None:
            if not isinstance(v, dict):
                msg = "Template must be a dictionary"
                raise ValueError(msg)

            # Don't require all fields for updates, but validate structure if provided
            if "demographics" in v and not isinstance(v["demographics"], dict):
                msg = "Demographics must be a dictionary"
                raise ValueError(msg)

            if "medical" in v and not isinstance(v["medical"], dict):
                msg = "Medical must be a dictionary"
                raise ValueError(msg)

            if "count" in v and not isinstance(v["count"], int):
                msg = "Count must be an integer"
                raise ValueError(msg)

        return v


class ConfigurationValidationRequest(BaseModel):
    """Request model for configuration validation."""

    template: Dict[str, Any] = Field(..., description="Configuration template to validate")

    strict: bool = Field(default=False, description="Whether to perform strict validation")

    @field_validator("template")
    @classmethod
    def validate_template_structure(cls, v):
        """Validate basic template structure."""
        if not isinstance(v, dict):
            msg = "Template must be a dictionary"
            raise ValueError(msg)
        return v

    class Config:
        """Pydantic configuration."""

        schema_extra = {
            "example": {
                "template": {
                    "demographics": {"nationalities": ["US", "GB"]},
                    "medical": {"injury_severity": "mixed"},
                    "count": 50,
                },
                "strict": True,
            }
        }
