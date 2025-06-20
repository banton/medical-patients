"""
API router for configuration management.
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from config import get_settings
from patient_generator.config_manager import ConfigurationManager
from patient_generator.nationality_data import NationalityDataProvider
from patient_generator.repository import ConfigurationRepository
from patient_generator.schemas_config import ConfigurationTemplateCreate, ConfigurationTemplateDB, FrontDefinition
from src.api.v1.dependencies.database import get_database
from src.core.cache_utils import cache_configuration_template, get_cached_configuration, invalidate_configuration_cache
from src.core.security_enhanced import verify_api_key
from src.infrastructure.database_adapter import EnhancedDatabase

# Initialize router (prefix will be added by main app)
router = APIRouter(prefix="/configurations", tags=["configurations"], dependencies=[Depends(verify_api_key)])

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@router.post("/", response_model=ConfigurationTemplateDB, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_configuration(
    request: Request, config: ConfigurationTemplateCreate, db: EnhancedDatabase = Depends(get_database)
) -> ConfigurationTemplateDB:
    """Create a new configuration template."""
    repo = ConfigurationRepository(db)
    return repo.create_configuration(config)


@router.get("/", response_model=List[ConfigurationTemplateDB])
@limiter.limit("30/minute")
async def list_configurations(
    request: Request, db: EnhancedDatabase = Depends(get_database)
) -> List[ConfigurationTemplateDB]:
    """List all configuration templates."""
    repo = ConfigurationRepository(db)
    return repo.list_configurations()


@router.get("/{config_id}", response_model=ConfigurationTemplateDB)
@limiter.limit("30/minute")
async def get_configuration(
    request: Request, config_id: str, db: EnhancedDatabase = Depends(get_database)
) -> ConfigurationTemplateDB:
    """Get a specific configuration template, checking cache first."""
    # Try to get from cache first
    cached_config = await get_cached_configuration(config_id)
    if cached_config:
        # Return cached configuration (already validated)
        return ConfigurationTemplateDB(**cached_config)

    repo = ConfigurationRepository(db)
    config = repo.get_configuration(config_id)

    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Configuration {config_id} not found")

    # Cache the configuration for future requests
    await cache_configuration_template(config_id, config.dict())

    return config


@router.put("/{config_id}", response_model=ConfigurationTemplateDB)
@limiter.limit("10/minute")
async def update_configuration(
    request: Request,
    config_id: str,
    config_update: ConfigurationTemplateCreate,
    db: EnhancedDatabase = Depends(get_database),
) -> ConfigurationTemplateDB:
    """Update a configuration template and invalidate cache."""
    repo = ConfigurationRepository(db)

    # Check if configuration exists
    existing = repo.get_configuration(config_id)
    if not existing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Configuration {config_id} not found")

    # Update the configuration
    updated = repo.update_configuration(config_id, config_update)
    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update configuration")

    # Invalidate cache for this configuration
    await invalidate_configuration_cache(config_id)

    # Cache the updated configuration
    await cache_configuration_template(config_id, updated.dict())

    return updated


@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_configuration(request: Request, config_id: str, db: EnhancedDatabase = Depends(get_database)) -> None:
    """Delete a configuration template and invalidate cache."""
    repo = ConfigurationRepository(db)

    if not repo.get_configuration(config_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Configuration {config_id} not found")

    repo.delete_configuration(config_id)

    # Invalidate cache for this configuration
    await invalidate_configuration_cache(config_id)

    # Return 204 No Content with no response body


@router.post("/validate/")
@limiter.limit("30/minute")
async def validate_configuration(request: Request, config: ConfigurationTemplateCreate) -> Dict[str, Any]:
    """Validate a configuration without saving it."""
    # The Pydantic model validation happens automatically by FastAPI
    # If we reach this point, the configuration is valid

    # Additional business logic validation could go here
    errors = []

    # Check injury distribution sums to reasonable value
    if config.injury_distribution:
        total = sum(config.injury_distribution.values())
        if total > 110.0:  # Allow some tolerance
            errors.append("Injury distribution percentages sum to more than 100%")

    # Check that there are some front configs or valid configuration
    if not config.front_configs or len(config.front_configs) == 0:
        errors.append("At least one front configuration is required")

    if errors:
        return {"valid": False, "errors": errors}

    return {"valid": True, "errors": []}


# Public configuration endpoint (no authentication required)
public_router = APIRouter(prefix="/config", tags=["public"])


@public_router.get("/frontend")
async def get_frontend_config() -> Dict[str, Any]:
    """Get frontend configuration including API key."""
    settings = get_settings()

    return {
        "apiKey": settings.API_KEY,
        "appName": settings.APP_NAME,
        "version": settings.VERSION,
        "debug": settings.DEBUG,
    }


# Reference data endpoints (don't require API key, prefix will be added by main app)
reference_router = APIRouter(prefix="/configurations/reference", tags=["reference"])


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
async def get_static_front_definitions(db: EnhancedDatabase = Depends(get_database)) -> Optional[List[FrontDefinition]]:
    """
    Get static front definitions from fronts_config.json.
    Returns None if file not found or invalid.
    """
    config_manager = ConfigurationManager(database_instance=db)
    return config_manager.get_static_front_definitions()
