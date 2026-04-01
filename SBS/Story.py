"""
Story.py
--------
Defines the Story dataclass, the top-level container for all narrative data
belonging to a single title (anime, game, movie, etc.).  A Story aggregates
Character, StoryObject, and PlotArc collections and provides serialisation,
persistence, and convenience query methods used throughout the analyzer.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional, Any

from SBS.Character import Character
from SBS.StoryObject import StoryObject
from SBS.PlotArc import PlotArc


@dataclass
class Story:
    """
    Represents a complete story (anime, game, movie, book, etc.).

    Story is the primary unit of analysis.  It owns the full set of
    characters, objects, and plot arcs for one title and exposes helper
    methods for common queries (e.g. retrieving the protagonist or all
    characters belonging to the main team).

    Serialisation round-trips are supported via ``to_dict`` / ``from_dict``
    and the ``save`` / ``load`` convenience wrappers.
    """

    title: str
    category: str = "anime"  # anime, game, movie, etc.

    # Publication / release metadata
    year: Optional[int] = None
    genre: List[str] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)

    # Core narrative elements
    characters: List[Character] = field(default_factory=list)
    objects: List[StoryObject] = field(default_factory=list)
    arcs: List[PlotArc] = field(default_factory=list)

    # World-building details
    setting: Optional[str] = None
    power_system: Optional[str] = None

    # Structural flags
    has_generations: bool = False
    generation_count: Optional[int] = None

    # Arbitrary extension data
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """
        Serialise the story and all its nested entities to a plain dictionary.

        Returns:
            A fully nested dictionary suitable for ``json.dump``, where
            characters, objects, and arcs are each represented as lists of
            their own ``to_dict()`` results.
        """
        return {
            "title": self.title,
            "category": self.category,
            "year": self.year,
            "genre": self.genre,
            "themes": self.themes,
            "characters": [c.to_dict() for c in self.characters],
            "objects": [o.to_dict() for o in self.objects],
            "arcs": [a.to_dict() for a in self.arcs],
            "setting": self.setting,
            "power_system": self.power_system,
            "has_generations": self.has_generations,
            "generation_count": self.generation_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Story":
        """
        Construct a Story and all its nested entities from a raw dictionary.

        The method injects ``story`` (the story title) into each character,
        object, and arc sub-dictionary before delegating to their own
        ``from_dict`` constructors, ensuring every entity knows which story
        it belongs to even when the JSON omits that field.

        Args:
            data: Nested dictionary as produced by ``to_dict`` or loaded from
                  a story JSON file.

        Returns:
            A fully populated Story instance with Character, StoryObject, and
            PlotArc lists reconstructed from the supplied data.
        """
        story = cls(
            title=data.get("title", "Unknown"),
            category=data.get("category", "anime"),
            year=data.get("year"),
            genre=data.get("genre", []),
            themes=data.get("themes", []),
            setting=data.get("setting"),
            power_system=data.get("power_system"),
            has_generations=data.get("has_generations", False),
            generation_count=data.get("generation_count"),
            metadata=data.get("metadata", {}),
        )

        # Load characters — inject story title so entities are self-contained
        for char_data in data.get("characters", []):
            char_data["story"] = story.title
            story.characters.append(Character.from_dict(char_data))

        # Load objects
        for obj_data in data.get("objects", []):
            obj_data["story"] = story.title
            story.objects.append(StoryObject.from_dict(obj_data))

        # Load arcs
        for arc_data in data.get("arcs", []):
            arc_data["story"] = story.title
            story.arcs.append(PlotArc.from_dict(arc_data))

        return story

    def save(self, filepath: str):
        """
        Persist the story to a JSON file on disk.

        Args:
            filepath: Destination file path.  The file will be created or
                      overwritten.
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath: str) -> "Story":
        """
        Load a story from a JSON file on disk.

        Args:
            filepath: Path to a JSON file previously produced by ``save``.

        Returns:
            A fully populated Story instance.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)

    def get_protagonist(self) -> Optional[Character]:
        """
        Return the first character whose role is ``'protagonist'``.

        Returns:
            The protagonist Character, or ``None`` if no protagonist is
            defined in this story.
        """
        for char in self.characters:
            if char.role == "protagonist":
                return char
        return None

    def get_characters_by_role(self, role: str) -> List[Character]:
        """
        Return all characters that have a specific narrative role.

        Args:
            role: Role string to filter by (e.g. ``'mentor'``, ``'rival'``).

        Returns:
            A list of matching Character instances; empty if none match.
        """
        return [c for c in self.characters if c.role == role]

    def get_main_team(self) -> List[Character]:
        """
        Return the characters that form the protagonist's primary team.

        If the protagonist belongs to a named team, all characters sharing
        that team name are returned.  Otherwise, protagonists, deuteragonists,
        and sidekicks are returned as an approximation of the main group.

        Returns:
            A list of Character instances representing the core team.
        """
        protagonist = self.get_protagonist()
        if protagonist and protagonist.team:
            return [c for c in self.characters if c.team == protagonist.team]
        return [c for c in self.characters if c.role in ["protagonist", "deuteragonist", "sidekick"]]
