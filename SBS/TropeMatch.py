"""
TropeMatch.py
-------------
Defines the TropeMatch dataclass, which represents a single successful match
between a story entity (character, object, or plot arc) and a known trope
definition from the configuration catalogue.  TropeMatch instances are the
primary output of PatternMatcher's per-entity matching methods.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class TropeMatch:
    """
    Represents a match between a story entity and a known trope.

    A TropeMatch is produced whenever an entity (character, object, or arc)
    satisfies the required traits for a trope defined in ``config.KNOWN_TROPES``.
    The ``score`` field (0.0–1.0) reflects how completely the entity embodies
    the trope, taking both required and associated traits into account.

    Attributes:
        trope_id:       The key used to look up the trope in KNOWN_TROPES.
        trope_name:     Human-readable trope name for display purposes.
        entity_name:    Name of the matched character, object, or arc.
        entity_type:    One of ``'character'``, ``'object'``, or ``'arc'``.
        story:          Title of the story the entity belongs to.
        score:          Match quality score in the range [0.0, 1.0].
        matched_traits: Traits from the trope definition that were found on
                        the entity.
        missing_traits: Required traits from the trope definition that were
                        NOT found (empty for a full match).
    """

    trope_id: str
    trope_name: str
    entity_name: str
    entity_type: str  # "character", "object", or "arc"
    story: str
    score: float
    matched_traits: List[str]
    missing_traits: List[str]

    def to_dict(self) -> dict:
        """
        Serialise the trope match to a plain dictionary for JSON output.

        Returns:
            A flat dictionary containing all match attributes.
        """
        return {
            "trope_id": self.trope_id,
            "trope_name": self.trope_name,
            "entity_name": self.entity_name,
            "entity_type": self.entity_type,
            "story": self.story,
            "score": self.score,
            "matched_traits": self.matched_traits,
            "missing_traits": self.missing_traits,
        }
