from enum import Enum


class Variant(str, Enum):
    """The implementation variants: vulnerable and safe."""

    VULNERABLE = "vulnerable"
    SAFE = "safe"
