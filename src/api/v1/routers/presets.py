"""
API router for scenario presets with v1 standardization.
Provides endpoints for listing and using pre-configured exercise scenarios.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.v1.models import ErrorResponse
from src.core.security_enhanced import verify_api_key

logger = logging.getLogger(__name__)

# Router configuration with v1 prefix and standardized responses
router = APIRouter(
    prefix="/presets",
    tags=["presets"],
    dependencies=[Depends(verify_api_key)],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Resource Not Found"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
)


class PresetSummary(BaseModel):
    """Summary of a scenario preset for listing."""

    id: str = Field(..., description="Unique preset identifier")
    name: str = Field(..., description="Human-readable preset name")
    description: str = Field(..., description="Detailed preset description")
    category: str = Field(..., description="Preset category (e.g., conventional_warfare)")
    difficulty: str = Field(..., description="Difficulty level (low, high, extreme)")
    total_patients: int = Field(..., description="Number of patients to generate")
    duration_days: int = Field(..., description="Scenario duration in days")


class PresetDetail(PresetSummary):
    """Full preset details including configuration."""

    fronts: List[Dict[str, Any]] = Field(..., description="Front configurations")
    injury_distribution: Dict[str, float] = Field(..., description="Injury type distribution")
    warfare_type: str = Field(..., description="Type of warfare scenario")
    triage_override: Optional[Dict[str, Dict[str, float]]] = Field(
        None, description="Optional triage weight overrides"
    )


class PresetsListResponse(BaseModel):
    """Response model for listing presets."""

    presets: List[PresetSummary] = Field(..., description="List of available presets")
    categories: Dict[str, Dict[str, str]] = Field(..., description="Category metadata")
    difficulty_levels: Dict[str, Dict[str, str]] = Field(..., description="Difficulty level metadata")
    total_count: int = Field(..., description="Total number of presets")


class PresetConfigResponse(BaseModel):
    """Response model for getting preset configuration."""

    preset: PresetDetail = Field(..., description="Full preset configuration")
    generation_config: Dict[str, Any] = Field(
        ..., description="Ready-to-use generation configuration"
    )


def _load_presets() -> Dict[str, Any]:
    """Load presets from JSON file."""
    presets_path = os.path.join(
        os.path.dirname(__file__),
        "..", "..", "..", "..",
        "patient_generator", "scenario_presets.json"
    )
    presets_path = os.path.normpath(presets_path)

    try:
        with open(presets_path) as f:
            data = json.load(f)
            # Filter out comment fields
            return {k: v for k, v in data.items() if not k.startswith("_")}
    except FileNotFoundError:
        logger.error("Presets file not found at %s", presets_path)
        return {"presets": {}, "categories": {}, "difficulty_levels": {}}
    except json.JSONDecodeError as e:
        logger.error("Error parsing presets file: %s", e)
        return {"presets": {}, "categories": {}, "difficulty_levels": {}}


def _preset_to_summary(preset_id: str, preset: Dict[str, Any]) -> PresetSummary:
    """Convert preset data to summary model."""
    return PresetSummary(
        id=preset_id,
        name=preset.get("name", preset_id),
        description=preset.get("description", ""),
        category=preset.get("category", "unknown"),
        difficulty=preset.get("difficulty", "medium"),
        total_patients=preset.get("total_patients", 100),
        duration_days=preset.get("duration_days", 1),
    )


def _preset_to_detail(preset_id: str, preset: Dict[str, Any]) -> PresetDetail:
    """Convert preset data to detail model."""
    return PresetDetail(
        id=preset_id,
        name=preset.get("name", preset_id),
        description=preset.get("description", ""),
        category=preset.get("category", "unknown"),
        difficulty=preset.get("difficulty", "medium"),
        total_patients=preset.get("total_patients", 100),
        duration_days=preset.get("duration_days", 1),
        fronts=preset.get("fronts", []),
        injury_distribution=preset.get("injury_distribution", {}),
        warfare_type=preset.get("warfare_type", "conventional"),
        triage_override=preset.get("triage_override"),
    )


def _preset_to_generation_config(preset_id: str, preset: Dict[str, Any]) -> Dict[str, Any]:
    """Convert preset to a generation API-compatible configuration."""
    return {
        "total_patients": preset.get("total_patients", 100),
        "front_configs": [
            {
                "id": f"front_{i}",
                "name": front.get("name", f"Front {i+1}"),
                "nationality_distribution": front.get("nationality_distribution", []),
                "casualty_rate": front.get("casualty_rate", 0.5),
            }
            for i, front in enumerate(preset.get("fronts", []))
        ],
        "injury_distribution": preset.get("injury_distribution", {
            "Battle Injury": 0.4,
            "Non-Battle Injury": 0.3,
            "Disease": 0.3,
        }),
        "facility_configs": [
            {"id": "Role1", "name": "Role 1 - Battalion Aid Station", "kia_rate": 0.08, "rtd_rate": 0.25},
            {"id": "Role2", "name": "Role 2 - Forward Surgical Team", "kia_rate": 0.06, "rtd_rate": 0.35},
            {"id": "Role3", "name": "Role 3 - Combat Support Hospital", "kia_rate": 0.04, "rtd_rate": 0.45},
            {"id": "Role4", "name": "Role 4 - Definitive Care", "kia_rate": 0.02, "rtd_rate": 0.70},
        ],
        "output_formats": ["json"],
        "preset_id": preset_id,
        "preset_name": preset.get("name", preset_id),
        "warfare_type": preset.get("warfare_type", "conventional"),
        "duration_days": preset.get("duration_days", 1),
    }


@router.get(
    "",
    response_model=PresetsListResponse,
    summary="List Available Presets",
    description="""
    Retrieve a list of all available scenario presets.

    Presets provide pre-configured exercise scenarios for common military
    medical training situations. Each preset includes:
    - Total patient count
    - Front configurations with nationality distributions
    - Injury type distributions
    - Warfare type and duration

    Available categories:
    - conventional_warfare: Standard military operations
    - urban_warfare: Urban assault scenarios
    - peacekeeping: UN peacekeeping missions
    - cbrn: Chemical/biological incidents
    - training: Small-scale training exercises
    - mass_casualty: Single-event mass casualty
    - cold_weather: Arctic/winter operations
    - maritime: Naval and amphibious operations
    """,
    response_description="List of available presets with metadata",
)
async def list_presets(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
) -> PresetsListResponse:
    """List all available scenario presets."""
    try:
        data = _load_presets()
        presets_data = data.get("presets", {})

        # Filter by category if specified
        if category:
            presets_data = {
                k: v for k, v in presets_data.items()
                if v.get("category") == category
            }

        # Filter by difficulty if specified
        if difficulty:
            presets_data = {
                k: v for k, v in presets_data.items()
                if v.get("difficulty") == difficulty
            }

        presets = [
            _preset_to_summary(preset_id, preset)
            for preset_id, preset in presets_data.items()
        ]

        return PresetsListResponse(
            presets=presets,
            categories=data.get("categories", {}),
            difficulty_levels=data.get("difficulty_levels", {}),
            total_count=len(presets),
        )

    except Exception as e:
        logger.error("Error listing presets: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list presets: {e!s}"
        )


@router.get(
    "/{preset_id}",
    response_model=PresetConfigResponse,
    summary="Get Preset Configuration",
    description="""
    Retrieve detailed configuration for a specific preset.

    Returns the full preset configuration along with a ready-to-use
    generation configuration that can be passed directly to the
    generation endpoint.
    """,
    response_description="Full preset details and generation configuration",
)
async def get_preset(preset_id: str) -> PresetConfigResponse:
    """Get detailed configuration for a specific preset."""
    try:
        data = _load_presets()
        presets_data = data.get("presets", {})

        if preset_id not in presets_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preset '{preset_id}' not found"
            )

        preset = presets_data[preset_id]

        return PresetConfigResponse(
            preset=_preset_to_detail(preset_id, preset),
            generation_config=_preset_to_generation_config(preset_id, preset),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting preset %s: %s", preset_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preset: {e!s}"
        )


@router.get(
    "/categories/list",
    summary="List Preset Categories",
    description="Get all available preset categories with metadata.",
)
async def list_categories() -> Dict[str, Any]:
    """List all preset categories."""
    try:
        data = _load_presets()
        categories = data.get("categories", {})

        # Count presets per category
        presets_data = data.get("presets", {})
        category_counts: dict[str, int] = {}
        for preset in presets_data.values():
            cat = preset.get("category", "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "categories": [
                {
                    "id": cat_id,
                    "name": cat_info.get("name", cat_id),
                    "icon": cat_info.get("icon", "default"),
                    "preset_count": category_counts.get(cat_id, 0),
                }
                for cat_id, cat_info in categories.items()
            ],
            "total_categories": len(categories),
        }

    except Exception as e:
        logger.error("Error listing categories: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list categories: {e!s}"
        )
