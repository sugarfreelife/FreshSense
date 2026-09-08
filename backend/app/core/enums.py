from enum import Enum


class FreshnessEnum(str, Enum):
    FRESH = "fresh"
    MODERATELY_FRESH = "moderately_fresh"
    SPOILED = "spoiled"


class ExpiryStatus(str, Enum):
    VALID = "valid"
    EXPIRING_SOON = "expiring_soon"
    EXPIRED = "expired"
    UNKNOWN = "unknown"


class ModelType(str, Enum):
    REAL_MODEL = "real_model"
    PROTOTYPE = "prototype"
    NOT_IMPLEMENTED = "not_implemented"
