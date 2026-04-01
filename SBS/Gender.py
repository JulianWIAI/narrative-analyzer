"""
Gender.py
---------
Defines the Gender enumeration used throughout the Narrative Pattern Analyzer
to represent a character's gender identity in a structured, type-safe way.
"""

from enum import Enum


class Gender(Enum):
    """
    Enumeration of recognized gender values for story characters.

    This enum ensures that gender attributes are always stored as a controlled
    vocabulary rather than free-form strings, which simplifies comparisons and
    prevents typos from silently propagating through analysis results.

    Values:
        MALE:    Identifies a male character.
        FEMALE:  Identifies a female character.
        OTHER:   Covers non-binary or otherwise specified genders.
        UNKNOWN: Used when gender information is absent or undefined.
    """

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"
