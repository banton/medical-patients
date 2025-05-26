"""
API router for configuration management.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from patient_generator.config_manager import ConfigurationManager
from patient_generator.database import ConfigurationRepository, Database
from patient_generator.nationality_data import NationalityDataProvider
from patient_generator.schemas_config import ConfigurationTemplateCreate, ConfigurationTemplateDB, FrontDefinition
from src.api.v1.dependencies.database import get_database
from src.core.security import verify_api_key

# Initialize router
router = APIRouter(prefix="/api/v1/configurations", tags=["configurations"], dependencies=[Depends(verify_api_key)])

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.post("/", response_model=ConfigurationTemplateDB, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_configuration(
    request: Request, config: ConfigurationTemplateCreate, db: Database = Depends(get_database)
) -> ConfigurationTemplateDB:
    """Create a new configuration template."""
    repo = ConfigurationRepository(db)
    return repo.create_configuration(config)


@router.get("/", response_model=List[ConfigurationTemplateDB])
@limiter.limit("30/minute")
async def list_configurations(request: Request, db: Database = Depends(get_database)) -> List[ConfigurationTemplateDB]:
    """List all configuration templates."""
    repo = ConfigurationRepository(db)
    return repo.list_configurations()


@router.get("/{config_id}", response_model=ConfigurationTemplateDB)
@limiter.limit("30/minute")
async def get_configuration(
    request: Request, config_id: str, db: Database = Depends(get_database)
) -> ConfigurationTemplateDB:
    """Get a specific configuration template."""
    repo = ConfigurationRepository(db)
    config = repo.get_configuration(config_id)

    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Configuration {config_id} not found")

    return config


@router.put("/{config_id}", response_model=ConfigurationTemplateDB)
@limiter.limit("10/minute")
async def update_configuration(
    request: Request, config_id: str, config_update: ConfigurationTemplateCreate, db: Database = Depends(get_database)
) -> ConfigurationTemplateDB:
    """Update a configuration template."""
    repo = ConfigurationRepository(db)

    # Check if configuration exists
    existing = repo.get_configuration(config_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Configuration {config_id} not found")

    # Update the configuration
    updated = repo.update_configuration(config_id, config_update)
    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update configuration")

    return updated


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_configuration(request: Request, config_id: str, db: Database = Depends(get_database)) -> None:
    """Delete a configuration template."""
    repo = ConfigurationRepository(db)

    if not repo.get_configuration(config_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Configuration {config_id} not found")

    repo.delete_configuration(config_id)


@router.post("/validate/")
@limiter.limit("30/minute")
async def validate_configuration(request: Request, config: ConfigurationTemplateCreate) -> Dict[str, Any]:
    """Validate a configuration without saving it."""
    try:
        # The Pydantic model itself does validation
        # Additional business logic validation could go here
        return {"valid": True, "errors": []}
    except Exception as e:
        return {"valid": False, "errors": [str(e)]}


# Reference data endpoints (don't require API key)
reference_router = APIRouter(prefix="/api/v1/configurations/reference", tags=["reference"])


@reference_router.get("/nationalities/")
async def get_nationalities() -> List[Dict[str, str]]:
    """Get list of available nationalities."""
    provider = NationalityDataProvider()
    return provider.list_available_nationalities()


@reference_router.get("/condition-types/")
async def get_condition_types() -> List[str]:
    """Get list of condition types."""
    return ["DISEASE", "NON_BATTLE", "BATTLE_TRAUMA"]


@reference_router.get("/facility-types/")
async def get_facility_types() -> List[Dict[str, str]]:
    """Get list of standard facility types."""
    return [
        {"id": "POI", "name": "Point of Injury"},
        {"id": "R1", "name": "Role 1"},
        {"id": "R2", "name": "Role 2"},
        {"id": "R3", "name": "Role 3"},
        {"id": "R4", "name": "Role 4"},
    ]


@reference_router.get("/static-fronts/")
async def get_static_front_definitions(db: Database = Depends(get_database)) -> Optional[List[FrontDefinition]]:
    """
    Get static front definitions from fronts_config.json.
    Returns None if file not found or invalid.
    """
    config_manager = ConfigurationManager(database_instance=db)
    return config_manager.get_static_front_definitions()
