"""
SimilarityMatch.py
------------------
Defines the SimilarityMatch dataclass, which records a computed similarity
between two story entities (currently characters) that share a meaningful
overlap of traits and/or tropes.  These results drive the cross-story
comparison sections of analysis reports.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class SimilarityMatch:
    """
    Represents a similarity between two story entities from different stories.

    A SimilarityMatch is produced by ``PatternMatcher.find_similar_characters``
    when the trait-overlap score between two characters meets or exceeds the
    configured minimum threshold.  Shared trope memberships further boost the
    score to reward structurally equivalent characters.

    Attributes:
        entity1_name:   Name of the first entity.
        entity1_story:  Story the first entity belongs to.
        entity2_name:   Name of the second entity.
        entity2_story:  Story the second entity belongs to.
        score:          Similarity score in the range [0.0, 1.0].
        shared_traits:  Trait strings that both entities possess (after
                        synonym expansion).
        shared_tropes:  Names of tropes that both entities match.
    """

    entity1_name: str
    entity1_story: str
    entity2_name: str
    entity2_story: str
    score: float
    shared_traits: List[str]
    shared_tropes: List[str]

    def to_dict(self) -> dict:
        """
        Serialise the similarity match to a plain dictionary for JSON output.

        Returns:
            A dictionary with entity identifiers nested under ``'entity1'``
            and ``'entity2'`` keys, plus flat ``score``, ``shared_traits``,
            and ``shared_tropes`` fields.
        """
        return {
            "entity1": {"name": self.entity1_name, "story": self.entity1_story},
            "entity2": {"name": self.entity2_name, "story": self.entity2_story},
            "score": self.score,
            "shared_traits": self.shared_traits,
            "shared_tropes": self.shared_tropes,
        }
