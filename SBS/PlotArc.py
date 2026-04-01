"""
PlotArc.py
----------
Defines the PlotArc dataclass, which models a single story arc or major plot
event within a narrative.  Plot arcs are the third primary entity type that
the Narrative Pattern Analyzer evaluates for trope membership, alongside
characters and story objects.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class PlotArc:
    """
    Represents a story arc or major plot event.

    A PlotArc captures the structural and thematic details of one distinct
    narrative segment — for example a tournament arc, a training sequence, or
    a rescue mission.  The ``arc_type``, ``traits``, and ``themes`` fields are
    the primary inputs consumed by the ``PatternMatcher`` when evaluating plot-
    and theme-category tropes.
    """

    name: str
    story: str

    # Type classification for this arc
    arc_type: str = "adventure"  # e.g. "tournament", "training", "rescue", "war"

    # Characters participating in this arc
    main_characters: List[str] = field(default_factory=list)
    villains: List[str] = field(default_factory=list)

    # Descriptive tags and thematic keywords
    traits: List[str] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)

    # Positional metadata within the overall story
    is_final_arc: bool = False
    arc_number: Optional[int] = None

    # Arbitrary extension data
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """
        Serialise the plot arc to a plain dictionary for JSON output.

        Returns:
            A dictionary containing every attribute of this arc, ready for
            ``json.dump``.
        """
        return {
            "name": self.name,
            "story": self.story,
            "arc_type": self.arc_type,
            "main_characters": self.main_characters,
            "villains": self.villains,
            "traits": self.traits,
            "themes": self.themes,
            "is_final_arc": self.is_final_arc,
            "arc_number": self.arc_number,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PlotArc":
        """
        Construct a PlotArc instance from a raw dictionary (e.g. parsed JSON).

        Args:
            data: Dictionary with plot-arc attribute values.  Missing keys are
                  silently replaced with sensible defaults so that partial data
                  files load without errors.

        Returns:
            A fully initialised PlotArc instance.
        """
        return cls(
            name=data.get("name", "Unknown"),
            story=data.get("story", "Unknown"),
            arc_type=data.get("arc_type", "adventure"),
            main_characters=data.get("main_characters", []),
            villains=data.get("villains", []),
            traits=data.get("traits", []),
            themes=data.get("themes", []),
            is_final_arc=data.get("is_final_arc", False),
            arc_number=data.get("arc_number"),
            metadata=data.get("metadata", {}),
        )
