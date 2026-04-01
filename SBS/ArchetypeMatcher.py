"""
ArchetypeMatcher.py
-------------------
Defines the ArchetypeMatcher class, which scores a character against each of
the canonical character archetypes defined in ``config.CHARACTER_ARCHETYPES``.
Archetype matching complements trope matching by providing a higher-level,
role-based classification (e.g. "The Hero", "The Mentor") rather than
story-specific pattern recognition.
"""

from typing import List, Tuple

from SBS.Character import Character
from config import CHARACTER_ARCHETYPES, TRAIT_SYNONYMS


class ArchetypeMatcher:
    """
    Matches characters to the canonical archetypes in the configuration.

    Unlike PatternMatcher, ArchetypeMatcher uses simple string-containment
    matching (substring check in both directions) rather than the full synonym
    expansion pipeline.  This keeps archetype scoring lightweight while still
    handling minor naming variations between the archetype trait definitions
    and the character's actual trait tags.
    """

    def __init__(self):
        self.archetypes = CHARACTER_ARCHETYPES
        self.synonyms = TRAIT_SYNONYMS

    def normalize_trait(self, trait: str) -> str:
        """
        Normalise a trait string for comparison.

        Applies the same normalisation used by PatternMatcher: lower-case,
        strip whitespace, replace spaces and hyphens with underscores.

        Args:
            trait: Raw trait string.

        Returns:
            Normalised trait string.
        """
        return trait.lower().strip().replace(" ", "_").replace("-", "_")

    def match_character_to_archetype(
        self, character: Character
    ) -> List[Tuple[str, float]]:
        """
        Score a character against every known archetype.

        For each archetype, the method counts how many archetype traits are
        present in the character's full trait set (using substring containment
        to allow partial matches).  The score is the fraction of archetype
        traits that matched.

        Args:
            character: The Character instance to evaluate.

        Returns:
            A list of ``(archetype_name, score)`` tuples sorted by score in
            descending order.  Only archetypes with at least one matching
            trait are included.
        """
        char_traits = [self.normalize_trait(t) for t in character.get_all_traits()]
        matches = []

        for arch_id, archetype in self.archetypes.items():
            arch_traits = [self.normalize_trait(t) for t in archetype["traits"]]

            matched = 0
            for arch_trait in arch_traits:
                for char_trait in char_traits:
                    # Accept exact matches and substring containment in either direction
                    if arch_trait == char_trait or arch_trait in char_trait or char_trait in arch_trait:
                        matched += 1
                        break

            if matched > 0:
                score = matched / len(arch_traits)
                matches.append((archetype["name"], round(score, 3)))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
