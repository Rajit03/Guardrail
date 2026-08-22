from enum import Enum
from typing import Dict


class Exploitability(str, Enum):
    VERY_HIGH = "VERY_HIGH"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


EXPLOITABILITY_WEIGHTS: Dict[Exploitability, float] = {
    Exploitability.VERY_HIGH: 1.0,
    Exploitability.HIGH: 0.8,
    Exploitability.MEDIUM: 0.5,
    Exploitability.LOW: 0.2,
    Exploitability.UNKNOWN: 0.4,
}


class Exposure(str, Enum):
    INTERNET = "INTERNET"
    EXTERNAL = "EXTERNAL"
    INTERNAL = "INTERNAL"
    LOCAL = "LOCAL"
    UNKNOWN = "UNKNOWN"


EXPOSURE_WEIGHTS: Dict[Exposure, float] = {
    Exposure.INTERNET: 1.0,
    Exposure.EXTERNAL: 0.8,
    Exposure.INTERNAL: 0.5,
    Exposure.LOCAL: 0.2,
    Exposure.UNKNOWN: 0.4,
}


class AssetCriticality(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


ASSET_CRITICALITY_WEIGHTS: Dict[AssetCriticality, float] = {
    AssetCriticality.CRITICAL: 1.0,
    AssetCriticality.HIGH: 0.8,
    AssetCriticality.MEDIUM: 0.5,
    AssetCriticality.LOW: 0.2,
    AssetCriticality.UNKNOWN: 0.4,
}


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


CONFIDENCE_WEIGHTS: Dict[Confidence, float] = {
    Confidence.HIGH: 1.0,
    Confidence.MEDIUM: 0.75,
    Confidence.LOW: 0.5,
    Confidence.UNKNOWN: 0.7,
}


def get_exploitability_weight(val: str | Exploitability) -> float:
    if isinstance(val, Exploitability):
        return EXPLOITABILITY_WEIGHTS[val]
    try:
        return EXPLOITABILITY_WEIGHTS[Exploitability(str(val).upper())]
    except Exception:
        return EXPLOITABILITY_WEIGHTS[Exploitability.UNKNOWN]


def get_exposure_weight(val: str | Exposure) -> float:
    if isinstance(val, Exposure):
        return EXPOSURE_WEIGHTS[val]
    try:
        return EXPOSURE_WEIGHTS[Exposure(str(val).upper())]
    except Exception:
        return EXPOSURE_WEIGHTS[Exposure.UNKNOWN]


def get_asset_criticality_weight(val: str | AssetCriticality) -> float:
    if isinstance(val, AssetCriticality):
        return ASSET_CRITICALITY_WEIGHTS[val]
    try:
        return ASSET_CRITICALITY_WEIGHTS[AssetCriticality(str(val).upper())]
    except Exception:
        return ASSET_CRITICALITY_WEIGHTS[AssetCriticality.UNKNOWN]


def get_confidence_weight(val: str | Confidence) -> float:
    if isinstance(val, Confidence):
        return CONFIDENCE_WEIGHTS[val]
    try:
        return CONFIDENCE_WEIGHTS[Confidence(str(val).upper())]
    except Exception:
        return CONFIDENCE_WEIGHTS[Confidence.UNKNOWN]
