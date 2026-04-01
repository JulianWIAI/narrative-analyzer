"""
Character.py
------------
Defines the Character dataclass, the primary data model for representing
a single character within a story in the Narrative Pattern Analyzer.
Characters are the central unit of analysis: trope matching, similarity
comparison, and archetype detection all operate on Character instances.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class Character:
    """
    Represents a character in a story.

    This dataclass captures all narrative-relevant attributes of a character,
    from basic biographical information (name, gender, age) through to
    story-structural details (role, arc appearances) and combat capabilities
    (abilities, power source).  The ``get_all_traits`` method synthesises a
    flat, de-duplicated tag list from all fields, which is the primary input
    consumed by the pattern-matching engine.
    """

    name: str
    story: str  # Which story they belong to

    # Basic info
    gender: str = "unknown"
    age: Optional[str] = None  # Can be number or description like "teenager"
    species: str = "human"

    # Role and relationships
    role: str = "supporting"  # protagonist, antagonist, mentor, etc.
    team: Optional[str] = None  # Group they belong to
    relationships: Dict[str, str] = field(default_factory=dict)  # name -> relationship type

    # Appearance
    hair_color: Optional[str] = None
    eye_color: Optional[str] = None
    notable_appearance: List[str] = field(default_factory=list)  # ["scar", "tall", "muscular"]

    # Background
    family_status: Optional[str] = None  # "orphan", "single_parent", "full_family"
    origin: Optional[str] = None
    occupation: Optional[str] = None

    # Personality and traits (free-form tags)
    traits: List[str] = field(default_factory=list)

    # Story-specific
    appears_in_episode: Optional[int] = None  # When they first appear
    arc_appearances: List[str] = field(default_factory=list)

    # Goals and motivations
    dream: Optional[str] = None
    motivation: Optional[str] = None

    # Powers/Abilities
    abilities: List[str] = field(default_factory=list)
    power_source: Optional[str] = None  # "magic", "ki", "devil_fruit", etc.

    # Custom metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """
        Serialise the character to a plain dictionary suitable for JSON output.

        Returns:
            A dictionary containing every attribute of this character, with
            complex sub-structures (relationships, metadata) preserved as
            nested dicts or lists.
        """
        return {
            "name": self.name,
            "story": self.story,
            "gender": self.gender,
            "age": self.age,
            "species": self.species,
            "role": self.role,
            "team": self.team,
            "relationships": self.relationships,
            "hair_color": self.hair_color,
            "eye_color": self.eye_color,
            "notable_appearance": self.notable_appearance,
            "family_status": self.family_status,
            "origin": self.origin,
            "occupation": self.occupation,
            "traits": self.traits,
            "appears_in_episode": self.appears_in_episode,
            "arc_appearances": self.arc_appearances,
            "dream": self.dream,
            "motivation": self.motivation,
            "abilities": self.abilities,
            "power_source": self.power_source,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Character":
        """
        Construct a Character instance from a raw dictionary (e.g. parsed JSON).

        Args:
            data: Dictionary containing character attribute values.  Missing
                  keys are replaced with sensible defaults so that partially
                  specified data files load without errors.

        Returns:
            A fully initialised Character instance.
        """
        return cls(
            name=data.get("name", "Unknown"),
            story=data.get("story", "Unknown"),
            gender=data.get("gender", "unknown"),
            age=data.get("age"),
            species=data.get("species", "human"),
            role=data.get("role", "supporting"),
            team=data.get("team"),
            relationships=data.get("relationships", {}),
            hair_color=data.get("hair_color"),
            eye_color=data.get("eye_color"),
            notable_appearance=data.get("notable_appearance", []),
            family_status=data.get("family_status"),
            origin=data.get("origin"),
            occupation=data.get("occupation"),
            traits=data.get("traits", []),
            appears_in_episode=data.get("appears_in_episode"),
            arc_appearances=data.get("arc_appearances", []),
            dream=data.get("dream"),
            motivation=data.get("motivation"),
            abilities=data.get("abilities", []),
            power_source=data.get("power_source"),
            metadata=data.get("metadata", {}),
        )

    def get_all_traits(self) -> List[str]:
        """
        Build and return a de-duplicated list of all traits for this character.

        In addition to the explicit ``traits`` list, this method derives
        additional tags from other fields so that the pattern-matching engine
        has a single unified surface to work against:

        - The character's ``role`` is appended as a trait tag.
        - A non-unknown ``gender`` is appended.
        - ``family_status`` values that indicate an absent parent are
          normalised to the canonical tag ``orphan_or_absent_parent``.
        - ``hair_color`` is appended as ``<color>_hair``, and uncommon colours
          also produce the ``unusual_hair_color`` tag.
        - Non-human ``species`` values add both ``animal_or_creature`` and the
          species name itself.
        - Appearance notes from ``notable_appearance`` are included directly.
        - If any ability description contains the words "speech" or "talk",
          the tag ``can_speak`` is added (used for the Talking Animal trope).

        Returns:
            A deduplicated list of trait strings ready for matching.

        Note:
            The set conversion at the end removes duplicates but does not
            guarantee a stable ordering; callers that need sorted output
            should sort the result themselves.
        """
        all_traits = list(self.traits)

        # Add role as trait
        if self.role:
            all_traits.append(self.role)

        # Add gender as trait
        if self.gender and self.gender != "unknown":
            all_traits.append(self.gender)

        # Add family status
        if self.family_status:
            all_traits.append(self.family_status)
            if self.family_status in ["orphan", "single_parent", "absent_father", "absent_mother"]:
                all_traits.append("orphan_or_absent_parent")

        # Add hair color
        if self.hair_color:
            all_traits.append(f"{self.hair_color}_hair")
            if self.hair_color.lower() not in ["black", "brown", "blonde"]:
                all_traits.append("unusual_hair_color")

        # Add species
        if self.species and self.species != "human":
            all_traits.append("animal_or_creature")
            all_traits.append(self.species)

        # Add appearance traits
        all_traits.extend(self.notable_appearance)

        # Add abilities as traits
        if self.abilities:
            if "speech" in str(self.abilities).lower() or "talk" in str(self.abilities).lower():
                all_traits.append("can_speak")

        return list(set(all_traits))
