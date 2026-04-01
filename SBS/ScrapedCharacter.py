"""
ScrapedCharacter.py
-------------------
Defines the ScrapedCharacter dataclass, a lightweight data container for
character information obtained by the story scrapers (FandomScraper,
FandomScraperHTML, and MALScraper).  Its ``to_dict`` method converts the
scraped data into the standard character dictionary format expected by the
``generate_story_json`` function and the rest of the analysis pipeline.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ScrapedCharacter:
    """
    Holds character data retrieved from an external source (wiki or API).

    Instances of this class are produced by the scraper classes and are
    transient: they are converted to the canonical story JSON format via
    ``to_dict`` before being written to disk.  Fields that cannot be
    determined from the source page default to ``None`` or empty collections.

    Attributes:
        name:             Display name of the character.
        url:              Source URL from which this character was scraped.
        description:      First paragraph or introductory text from the source.
        gender:           Detected gender string (``'male'``, ``'female'``, or
                          ``'unknown'``).
        species:          Species or race of the character (defaults to
                          ``'human'``).
        role:             Narrative role detected from text (e.g.
                          ``'protagonist'``, ``'supporting'``).
        traits:           List of personality/trait tags extracted from the
                          description.
        abilities:        List of ability or skill descriptions.
        affiliations:     List of team, group, or organisation names.
        family_status:    Family situation tag (e.g. ``'orphan'``) if
                          detectable.
        hair_color:       Hair colour string if available.
        occupation:       Job or title string if available.
        first_appearance: Episode or chapter of first appearance if available.
    """

    name: str
    url: str
    description: str = ""
    gender: str = "unknown"
    species: str = "human"
    role: str = "supporting"
    traits: List[str] = field(default_factory=list)
    abilities: List[str] = field(default_factory=list)
    affiliations: List[str] = field(default_factory=list)
    family_status: Optional[str] = None
    hair_color: Optional[str] = None
    occupation: Optional[str] = None
    first_appearance: Optional[str] = None

    def to_dict(self) -> dict:
        """
        Convert the scraped character to the canonical story character format.

        The resulting dictionary is compatible with the JSON schema expected
        by ``Story.from_dict`` and the analysis engine, with scraper-specific
        fields (source URL and affiliations) stored inside ``'metadata'``.

        Returns:
            A dictionary ready for inclusion in a story JSON file.
        """
        return {
            "name": self.name,
            "gender": self.gender,
            "species": self.species,
            "role": self.role,
            "traits": self.traits,
            "abilities": self.abilities,
            "family_status": self.family_status,
            "hair_color": self.hair_color,
            "occupation": self.occupation,
            "metadata": {
                "source_url": self.url,
                "affiliations": self.affiliations,
            }
        }
