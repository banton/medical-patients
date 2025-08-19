"""Body region definitions for hemorrhage modeling."""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


class BodyRegion(Enum):
    """Major body regions for injury localization."""
    HEAD = "head"
    NECK = "neck"
    CHEST = "chest"
    ABDOMEN = "abdomen"
    PELVIS = "pelvis"
    LEFT_ARM = "left_arm"
    RIGHT_ARM = "right_arm"
    LEFT_LEG = "left_leg"
    RIGHT_LEG = "right_leg"
    BACK = "back"


class VesselType(Enum):
    """Types of blood vessels that can be damaged."""
    MAJOR_ARTERY = "major_artery"  # Aorta, iliac, carotid
    LIMB_ARTERY = "limb_artery"    # Femoral, brachial
    SMALL_VESSEL = "small_vessel"   # Small arteries and veins
    ORGAN = "organ"                 # Internal organ bleeding
    CAPILLARY = "capillary"         # Surface/soft tissue


@dataclass
class BodyLocation:
    """Detailed body location with anatomical information."""
    region: BodyRegion
    specific_area: str  # e.g., "upper thigh", "forearm", "liver"
    major_vessels: List[str]  # Named vessels in this area
    organs: List[str]  # Organs in this area
    tourniquetable: bool  # Can a tourniquet be applied here?
    
    
# Anatomical mapping of body regions to structures
BODY_REGION_ANATOMY: Dict[BodyRegion, Dict] = {
    BodyRegion.HEAD: {
        "vessels": ["carotid_artery", "jugular_vein", "cerebral_arteries"],
        "organs": ["brain", "eyes", "skull"],
        "tourniquetable": False,
        "hemorrhage_risk": "high"  # Due to inability to compress
    },
    BodyRegion.NECK: {
        "vessels": ["carotid_artery", "jugular_vein", "vertebral_artery"],
        "organs": ["trachea", "esophagus", "thyroid"],
        "tourniquetable": False,
        "hemorrhage_risk": "critical"
    },
    BodyRegion.CHEST: {
        "vessels": ["aorta", "pulmonary_artery", "subclavian_artery", "intercostal_arteries"],
        "organs": ["heart", "lungs", "great_vessels"],
        "tourniquetable": False,
        "hemorrhage_risk": "critical"
    },
    BodyRegion.ABDOMEN: {
        "vessels": ["abdominal_aorta", "celiac_artery", "mesenteric_arteries", "renal_arteries"],
        "organs": ["liver", "spleen", "kidneys", "intestines", "stomach"],
        "tourniquetable": False,
        "hemorrhage_risk": "high"
    },
    BodyRegion.PELVIS: {
        "vessels": ["iliac_artery", "iliac_vein", "femoral_artery_proximal"],
        "organs": ["bladder", "reproductive_organs", "rectum"],
        "tourniquetable": False,  # Junctional area
        "hemorrhage_risk": "critical"
    },
    BodyRegion.LEFT_ARM: {
        "vessels": ["brachial_artery", "radial_artery", "ulnar_artery"],
        "organs": [],
        "tourniquetable": True,
        "hemorrhage_risk": "moderate"
    },
    BodyRegion.RIGHT_ARM: {
        "vessels": ["brachial_artery", "radial_artery", "ulnar_artery"],
        "organs": [],
        "tourniquetable": True,
        "hemorrhage_risk": "moderate"
    },
    BodyRegion.LEFT_LEG: {
        "vessels": ["femoral_artery", "popliteal_artery", "tibial_arteries"],
        "organs": [],
        "tourniquetable": True,
        "hemorrhage_risk": "high"  # Femoral can be fatal
    },
    BodyRegion.RIGHT_LEG: {
        "vessels": ["femoral_artery", "popliteal_artery", "tibial_arteries"],
        "organs": [],
        "tourniquetable": True,
        "hemorrhage_risk": "high"
    },
    BodyRegion.BACK: {
        "vessels": ["posterior_intercostal_arteries", "lumbar_arteries"],
        "organs": ["kidneys", "spine"],
        "tourniquetable": False,
        "hemorrhage_risk": "moderate"
    }
}


def get_body_location(region: BodyRegion, specific_area: Optional[str] = None) -> BodyLocation:
    """
    Create a BodyLocation object for a given region.
    
    Args:
        region: The body region
        specific_area: Optional specific anatomical area
        
    Returns:
        BodyLocation object with anatomical details
    """
    anatomy = BODY_REGION_ANATOMY.get(region, {})
    
    return BodyLocation(
        region=region,
        specific_area=specific_area or region.value,
        major_vessels=anatomy.get("vessels", []),
        organs=anatomy.get("organs", []),
        tourniquetable=anatomy.get("tourniquetable", False)
    )


def get_hemorrhage_risk_regions(risk_level: str = "high") -> List[BodyRegion]:
    """
    Get body regions with a specific hemorrhage risk level.
    
    Args:
        risk_level: "critical", "high", or "moderate"
        
    Returns:
        List of body regions with that risk level
    """
    regions = []
    for region, anatomy in BODY_REGION_ANATOMY.items():
        if anatomy.get("hemorrhage_risk") == risk_level:
            regions.append(region)
    return regions


def is_junctional_area(region: BodyRegion) -> bool:
    """
    Check if a body region is a junctional area (groin, shoulder, neck).
    These areas cannot be effectively controlled with standard tourniquets.
    
    Args:
        region: The body region to check
        
    Returns:
        True if junctional area
    """
    junctional_regions = [BodyRegion.NECK, BodyRegion.PELVIS]
    return region in junctional_regions


def get_affected_vessel_type(region: BodyRegion, injury_depth: str = "deep") -> VesselType:
    """
    Determine the likely vessel type affected based on region and injury depth.
    
    Args:
        region: Body region injured
        injury_depth: "superficial", "moderate", or "deep"
        
    Returns:
        Most likely vessel type affected
    """
    if injury_depth == "superficial":
        return VesselType.CAPILLARY
    
    # Deep injuries in critical areas
    if region in [BodyRegion.CHEST, BodyRegion.ABDOMEN, BodyRegion.PELVIS]:
        if injury_depth == "deep":
            return VesselType.MAJOR_ARTERY
        return VesselType.ORGAN
    
    # Limb injuries
    if region in [BodyRegion.LEFT_LEG, BodyRegion.RIGHT_LEG, 
                  BodyRegion.LEFT_ARM, BodyRegion.RIGHT_ARM]:
        if injury_depth == "deep":
            return VesselType.LIMB_ARTERY
        return VesselType.SMALL_VESSEL
    
    # Head and neck
    if region in [BodyRegion.HEAD, BodyRegion.NECK]:
        if injury_depth == "deep":
            return VesselType.MAJOR_ARTERY
        return VesselType.SMALL_VESSEL
    
    return VesselType.SMALL_VESSEL
