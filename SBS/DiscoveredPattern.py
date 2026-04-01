"""
DiscoveredPattern.py
--------------------
Defines the DiscoveredPattern dataclass, which captures a novel trait
combination that appears across multiple stories but does not correspond to
any pre-defined trope in the configuration catalogue.  Discovered patterns
surface organic, data-driven insights from the corpus.
"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class DiscoveredPattern:
    """
    A newly discovered cross-story pattern not covered by known tropes.

    DiscoveredPattern instances are produced by
    ``PatternMatcher.discover_patterns``, which mines the full character
    corpus for trait combinations that recur across at least a configurable
    minimum number of stories.  The ``confidence`` value normalises frequency
    relative to the total story count so that patterns from small corpora are
    not over-weighted.

    Attributes:
        pattern_name:   Auto-generated human-readable label derived from the
                        top traits in the combination.
        description:    Short text summary of the pattern.
        shared_traits:  The specific trait strings that define the pattern.
        examples:       Up to 10 sample entities (each a dict with ``'name'``
                        and ``'story'`` keys) that exhibit the pattern.
        frequency:      Total number of characters displaying this combination.
        confidence:     Fraction of stories in the corpus that contain at
                        least one matching character (0.0–1.0).
    """

    pattern_name: str
    description: str
    shared_traits: List[str]
    examples: List[Dict[str, str]]  # [{"name": ..., "story": ...}, ...]
    frequency: int
    confidence: float

    def to_dict(self) -> dict:
        """
        Serialise the discovered pattern to a plain dictionary for JSON output.

        Returns:
            A flat dictionary containing all pattern attributes.
        """
        return {
            "pattern_name": self.pattern_name,
            "description": self.description,
            "shared_traits": self.shared_traits,
            "examples": self.examples,
            "frequency": self.frequency,
            "confidence": self.confidence,
        }
