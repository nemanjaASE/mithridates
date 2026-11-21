"""The two variants of the feature under attack."""
from .__safe__ import __Safe__Feature
from .vulnerable import VulnerableFeature

__all__ = ["__Safe__Feature", "VulnerableFeature"]
