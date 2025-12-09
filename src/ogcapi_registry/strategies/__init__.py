"""OGC API validation strategies.

This module provides the Strategy pattern implementation for validating
OpenAPI documents against different OGC API specifications.
"""

from .base import CompositeValidationStrategy, ValidationStrategy
from .common import CommonStrategy
from .features import FeaturesStrategy
from .other import (
    CoveragesStrategy,
    EDRStrategy,
    MapsStrategy,
    RoutesStrategy,
    StylesStrategy,
)
from .processes import ProcessesStrategy
from .records import RecordsStrategy
from .tiles import TilesStrategy

__all__ = [
    # Base classes
    "ValidationStrategy",
    "CompositeValidationStrategy",
    # Concrete strategies
    "CommonStrategy",
    "FeaturesStrategy",
    "TilesStrategy",
    "ProcessesStrategy",
    "RecordsStrategy",
    "CoveragesStrategy",
    "EDRStrategy",
    "MapsStrategy",
    "StylesStrategy",
    "RoutesStrategy",
]
