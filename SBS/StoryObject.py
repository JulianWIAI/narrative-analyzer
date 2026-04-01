"""
StoryObject.py
--------------
Defines the StoryObject dataclass, which models an important item or artifact
within a story.  Story objects are the second major entity type (alongside
characters and arcs) analysed by the Narrative Pattern Analyzer's trope-
matching engine.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class StoryObject:
    """
    Represents an important object or item in a story.

    Story objects range from quest MacGuffins and collectible power items to
    inherited heirlooms.  The ``get_all_traits`` method derives a flat tag
    list from all fields, providing a unified interface for the
    ``PatternMatcher`` to apply object-category tropes.
    """

    name: str
    story: str

    # Classification
    object_type: str = "item"  # "device", "weapon", "artifact", "collectible", etc.

    # Properties
    traits: List[str] = field(default_factory=list)
    powers: List[str] = field(default_factory=list)

    # Story importance
    plot_importance: str = "minor"  # "minor", "major", "central"
    given_by: Optional[str] = None  # Who gives it to the hero
    inherited: bool = False

    # For collectibles
    is_collectible: bool = False
    total_count: Optional[int] = None

    # Custom metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """
        Serialise the story object to a plain dictionary for JSON output.

        Returns:
            A dictionary containing every attribute of this object.
        """
        return {
            "name": self.name,
            "story": self.story,
            "object_type": self.object_type,
            "traits": self.traits,
            "powers": self.powers,
            "plot_importance": self.plot_importance,
            "given_by": self.given_by,
            "inherited": self.inherited,
            "is_collectible": self.is_collectible,
            "total_count": self.total_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "StoryObject":
        """
        Construct a StoryObject from a raw dictionary (e.g. parsed JSON).

        Args:
            data: Dictionary with story-object attribute values.  Missing keys
                  are replaced with sensible defaults.

        Returns:
            A fully initialised StoryObject instance.
        """
        return cls(
            name=data.get("name", "Unknown"),
            story=data.get("story", "Unknown"),
            object_type=data.get("object_type", "item"),
            traits=data.get("traits", []),
            powers=data.get("powers", []),
            plot_importance=data.get("plot_importance", "minor"),
            given_by=data.get("given_by"),
            inherited=data.get("inherited", False),
            is_collectible=data.get("is_collectible", False),
            total_count=data.get("total_count"),
            metadata=data.get("metadata", {}),
        )

    def get_all_traits(self) -> List[str]:
        """
        Build and return a de-duplicated list of all traits for this object.

        Derives additional tags from structured fields:

        - ``object_type`` is always appended.
        - Objects with ``plot_importance`` of "major" or "central" receive the
          ``plot_essential`` tag consumed by the MacGuffin trope.
        - ``inherited`` objects receive the ``inherited`` tag.
        - ``is_collectible`` objects receive ``collectible`` and
          ``set_of_items`` tags.
        - If ``given_by`` is set, the ``given_by_mentor`` tag is appended.
        - All ``powers`` entries are included directly.

        Returns:
            A deduplicated list of trait strings ready for matching.
        """
        all_traits = list(self.traits)

        all_traits.append(self.object_type)

        if self.plot_importance in ["major", "central"]:
            all_traits.append("plot_essential")

        if self.inherited:
            all_traits.append("inherited")

        if self.is_collectible:
            all_traits.append("collectible")
            all_traits.append("set_of_items")

        if self.given_by:
            all_traits.append("given_by_mentor")

        all_traits.extend(self.powers)

        return list(set(all_traits))
