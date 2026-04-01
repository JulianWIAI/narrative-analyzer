"""
PatternMatcher.py
-----------------
Defines the PatternMatcher class, the core analysis engine of the Narrative
Pattern Analyzer.  It is responsible for matching characters, objects, and
plot arcs against the pre-defined trope catalogue, computing cross-story
character similarity scores, and discovering novel trait patterns that do not
yet appear in the catalogue.
"""

from typing import List, Dict, Tuple, Optional
from collections import defaultdict
import re

from SBS.Character import Character
from SBS.StoryObject import StoryObject
from SBS.PlotArc import PlotArc
from SBS.StoryCollection import StoryCollection
from SBS.TropeMatch import TropeMatch
from SBS.SimilarityMatch import SimilarityMatch
from SBS.DiscoveredPattern import DiscoveredPattern
from config import KNOWN_TROPES, TRAIT_SYNONYMS, SIMILARITY_WEIGHTS, OUTPUT_SETTINGS


class PatternMatcher:
    """
    Core engine for matching patterns and finding similarities across stories.

    PatternMatcher encapsulates all matching logic.  On construction it loads
    the trope catalogue, archetype definitions, synonym table, scoring weights,
    and the minimum similarity threshold from the configuration module.  All
    public methods are stateless with respect to the stories they analyse —
    the same instance can safely be reused across multiple collections.
    """

    def __init__(self):
        self.tropes = KNOWN_TROPES
        self.synonyms = TRAIT_SYNONYMS
        self.weights = SIMILARITY_WEIGHTS
        self.min_score = OUTPUT_SETTINGS["min_similarity_score"]

    def normalize_trait(self, trait: str) -> str:
        """
        Normalise a trait string for case-insensitive, format-agnostic comparison.

        Converts to lower-case and replaces spaces and hyphens with underscores
        so that ``'Hot-Headed'``, ``'hot headed'``, and ``'hot_headed'`` all
        compare as equal.

        Args:
            trait: Raw trait string from a character, object, or trope definition.

        Returns:
            Normalised trait string.
        """
        return trait.lower().strip().replace(" ", "_").replace("-", "_")

    def expand_trait(self, trait: str) -> List[str]:
        """
        Expand a trait to include all known synonyms from the synonym table.

        The expansion is bidirectional: if the supplied trait is a synonym of a
        canonical term, both the canonical term and all other synonyms are
        included.  If it is already canonical, its synonyms are appended.

        Args:
            trait: Normalised trait string to expand.

        Returns:
            De-duplicated list of trait strings that are semantically equivalent
            to the supplied trait.
        """
        normalized = self.normalize_trait(trait)
        expanded = [normalized]

        for canonical, synonyms in self.synonyms.items():
            if normalized in [self.normalize_trait(s) for s in synonyms]:
                expanded.append(canonical)
                expanded.extend([self.normalize_trait(s) for s in synonyms])
            elif normalized == canonical:
                expanded.extend([self.normalize_trait(s) for s in synonyms])

        return list(set(expanded))

    def traits_match(self, trait1: str, trait2: str) -> Tuple[bool, float]:
        """
        Check whether two trait strings are equivalent and return a quality score.

        Three levels of matching are attempted in order:
        1. Exact match after normalisation → full score from weights table.
        2. Synonym match via ``expand_trait`` → reduced score.
        3. Substring containment (one string contained in the other) → 0.5.

        Args:
            trait1: First trait string (will be normalised internally).
            trait2: Second trait string (will be normalised internally).

        Returns:
            A ``(matched, score)`` tuple where ``matched`` is ``True`` if any
            matching level succeeded and ``score`` is the corresponding quality
            value between 0.0 and 1.0.
        """
        t1 = self.normalize_trait(trait1)
        t2 = self.normalize_trait(trait2)

        # Exact match
        if t1 == t2:
            return True, self.weights["exact_trait_match"]

        # Synonym match
        t1_expanded = self.expand_trait(t1)
        t2_expanded = self.expand_trait(t2)

        if set(t1_expanded) & set(t2_expanded):
            return True, self.weights["synonym_match"]

        # Partial match (one contains the other)
        if t1 in t2 or t2 in t1:
            return True, 0.5

        return False, 0.0

    def calculate_trait_overlap(
        self, traits1: List[str], traits2: List[str]
    ) -> Tuple[List[str], float]:
        """
        Calculate the trait overlap between two lists and return a normalised score.

        Iterates over every trait in the first list and checks it against every
        trait in the second list using ``traits_match``.  The raw match score is
        accumulated and then divided by the size of the smaller list so the
        result is always in [0.0, 1.0], regardless of how long the lists are.

        Args:
            traits1: First trait list.
            traits2: Second trait list.

        Returns:
            A ``(shared_traits, score)`` tuple where ``shared_traits`` is the
            list of normalised traits that matched and ``score`` is the
            normalised overlap quality.
        """
        if not traits1 or not traits2:
            return [], 0.0

        shared = []
        total_score = 0.0

        normalized1 = [self.normalize_trait(t) for t in traits1]
        normalized2 = [self.normalize_trait(t) for t in traits2]

        for t1 in normalized1:
            for t2 in normalized2:
                match, score = self.traits_match(t1, t2)
                if match and t1 not in shared:
                    shared.append(t1)
                    total_score += score
                    break

        max_possible = min(len(traits1), len(traits2))
        if max_possible > 0:
            normalized_score = total_score / max_possible
        else:
            normalized_score = 0.0

        return shared, min(normalized_score, 1.0)

    def match_character_to_trope(
        self, character: Character, trope_id: str
    ) -> Optional[TropeMatch]:
        """
        Attempt to match a single character against a specific trope.

        All required traits from the trope definition must be satisfied for a
        match to be returned.  Associated (optional) traits contribute a bonus
        to the score.  The final score is capped at 1.0 and must exceed the
        configured minimum threshold.

        Args:
            character: The Character to evaluate.
            trope_id:  Key into ``config.KNOWN_TROPES`` for the target trope.

        Returns:
            A TropeMatch instance if all required traits are satisfied and the
            score meets the threshold, or ``None`` otherwise.
        """
        if trope_id not in self.tropes:
            return None

        trope = self.tropes[trope_id]

        # Only evaluate character-category tropes against characters
        if trope["category"] != "character":
            return None

        char_traits = character.get_all_traits()
        char_traits_normalized = [self.normalize_trait(t) for t in char_traits]

        required = trope.get("required_traits", [])
        required_matched = []
        required_missing = []

        for req in required:
            matched = False
            for char_trait in char_traits_normalized:
                match, _ = self.traits_match(req, char_trait)
                if match:
                    matched = True
                    required_matched.append(req)
                    break
            if not matched:
                required_missing.append(req)

        # A missing required trait disqualifies the match entirely
        if required_missing:
            return None

        # Associated traits provide a bonus score contribution
        associated = trope.get("associated_traits", [])
        associated_matched = []

        for assoc in associated:
            for char_trait in char_traits_normalized:
                match, _ = self.traits_match(assoc, char_trait)
                if match:
                    associated_matched.append(assoc)
                    break

        required_score = len(required_matched) / len(required) if required else 1.0
        associated_score = len(associated_matched) / len(associated) if associated else 0.0

        # Required traits carry 70 % of the weight; associated carry 30 %
        base_score = (required_score * 0.7) + (associated_score * 0.3)
        final_score = base_score * trope.get("weight", 1.0)

        if final_score < self.min_score:
            return None

        return TropeMatch(
            trope_id=trope_id,
            trope_name=trope["name"],
            entity_name=character.name,
            entity_type="character",
            story=character.story,
            score=round(final_score, 3),
            matched_traits=required_matched + associated_matched,
            missing_traits=required_missing
        )

    def match_object_to_trope(
        self, obj: StoryObject, trope_id: str
    ) -> Optional[TropeMatch]:
        """
        Attempt to match a story object against a specific trope.

        Only tropes with ``category == 'object'`` are considered.  Scoring
        logic mirrors ``match_character_to_trope``.

        Args:
            obj:      The StoryObject to evaluate.
            trope_id: Key into ``config.KNOWN_TROPES`` for the target trope.

        Returns:
            A TropeMatch instance on success, or ``None``.
        """
        if trope_id not in self.tropes:
            return None

        trope = self.tropes[trope_id]

        if trope["category"] != "object":
            return None

        obj_traits = obj.get_all_traits()
        obj_traits_normalized = [self.normalize_trait(t) for t in obj_traits]

        required = trope.get("required_traits", [])
        required_matched = []
        required_missing = []

        for req in required:
            matched = False
            for obj_trait in obj_traits_normalized:
                match, _ = self.traits_match(req, obj_trait)
                if match:
                    matched = True
                    required_matched.append(req)
                    break
            if not matched:
                required_missing.append(req)

        if required_missing:
            return None

        associated = trope.get("associated_traits", [])
        associated_matched = []

        for assoc in associated:
            for obj_trait in obj_traits_normalized:
                match, _ = self.traits_match(assoc, obj_trait)
                if match:
                    associated_matched.append(assoc)
                    break

        required_score = len(required_matched) / len(required) if required else 1.0
        associated_score = len(associated_matched) / len(associated) if associated else 0.0

        base_score = (required_score * 0.7) + (associated_score * 0.3)
        final_score = base_score * trope.get("weight", 1.0)

        if final_score < self.min_score:
            return None

        return TropeMatch(
            trope_id=trope_id,
            trope_name=trope["name"],
            entity_name=obj.name,
            entity_type="object",
            story=obj.story,
            score=round(final_score, 3),
            matched_traits=required_matched + associated_matched,
            missing_traits=required_missing
        )

    def match_arc_to_trope(
        self, arc: PlotArc, trope_id: str
    ) -> Optional[TropeMatch]:
        """
        Attempt to match a plot arc against a specific trope.

        Only tropes with ``category`` of ``'plot'`` or ``'theme'`` are
        considered.  The arc's ``traits``, ``themes``, and ``arc_type`` fields
        are combined into a single list for matching.

        Args:
            arc:      The PlotArc to evaluate.
            trope_id: Key into ``config.KNOWN_TROPES`` for the target trope.

        Returns:
            A TropeMatch instance on success, or ``None``.
        """
        if trope_id not in self.tropes:
            return None

        trope = self.tropes[trope_id]

        if trope["category"] not in ["plot", "theme"]:
            return None

        arc_traits = arc.traits + arc.themes + [arc.arc_type]
        arc_traits_normalized = [self.normalize_trait(t) for t in arc_traits]

        required = trope.get("required_traits", [])
        required_matched = []
        required_missing = []

        for req in required:
            matched = False
            for arc_trait in arc_traits_normalized:
                match, _ = self.traits_match(req, arc_trait)
                if match:
                    matched = True
                    required_matched.append(req)
                    break
            if not matched:
                required_missing.append(req)

        if required_missing:
            return None

        associated = trope.get("associated_traits", [])
        associated_matched = []

        for assoc in associated:
            for arc_trait in arc_traits_normalized:
                match, _ = self.traits_match(assoc, arc_trait)
                if match:
                    associated_matched.append(assoc)
                    break

        required_score = len(required_matched) / len(required) if required else 1.0
        associated_score = len(associated_matched) / len(associated) if associated else 0.0

        base_score = (required_score * 0.7) + (associated_score * 0.3)
        final_score = base_score * trope.get("weight", 1.0)

        if final_score < self.min_score:
            return None

        return TropeMatch(
            trope_id=trope_id,
            trope_name=trope["name"],
            entity_name=arc.name,
            entity_type="arc",
            story=arc.story,
            score=round(final_score, 3),
            matched_traits=required_matched + associated_matched,
            missing_traits=required_missing
        )

    def find_all_trope_matches(
        self, collection: StoryCollection
    ) -> Dict[str, List[TropeMatch]]:
        """
        Find all trope matches for every entity in the collection.

        Iterates over all stories, characters, objects, and arcs and attempts
        every trope in the catalogue for each entity.  Results are grouped by
        trope ID and sorted by descending score within each group.

        Args:
            collection: The StoryCollection to analyse.

        Returns:
            A dictionary mapping trope IDs to sorted lists of TropeMatch
            instances.  Tropes with no matches are omitted.
        """
        matches_by_trope = defaultdict(list)

        for story in collection.stories:
            for character in story.characters:
                for trope_id in self.tropes:
                    match = self.match_character_to_trope(character, trope_id)
                    if match:
                        matches_by_trope[trope_id].append(match)

            for obj in story.objects:
                for trope_id in self.tropes:
                    match = self.match_object_to_trope(obj, trope_id)
                    if match:
                        matches_by_trope[trope_id].append(match)

            for arc in story.arcs:
                for trope_id in self.tropes:
                    match = self.match_arc_to_trope(arc, trope_id)
                    if match:
                        matches_by_trope[trope_id].append(match)

        for trope_id in matches_by_trope:
            matches_by_trope[trope_id].sort(key=lambda x: x.score, reverse=True)

        return dict(matches_by_trope)

    def find_similar_characters(
        self, char1: Character, char2: Character
    ) -> Optional[SimilarityMatch]:
        """
        Compute the similarity between two characters and return a match if significant.

        Trait overlap drives the base score.  If both characters independently
        match any of the same tropes, the score receives a bonus of 0.1 per
        shared trope (capped at 1.0).

        Args:
            char1: First character to compare.
            char2: Second character to compare.

        Returns:
            A SimilarityMatch if the final score meets the minimum threshold,
            or ``None`` if the characters are too dissimilar.
        """
        traits1 = char1.get_all_traits()
        traits2 = char2.get_all_traits()

        shared_traits, score = self.calculate_trait_overlap(traits1, traits2)

        if score < self.min_score:
            return None

        shared_tropes = []
        for trope_id in self.tropes:
            match1 = self.match_character_to_trope(char1, trope_id)
            match2 = self.match_character_to_trope(char2, trope_id)
            if match1 and match2:
                shared_tropes.append(self.tropes[trope_id]["name"])

        # Shared trope membership is a strong structural signal — reward it
        if shared_tropes:
            score = min(score + (len(shared_tropes) * 0.1), 1.0)

        return SimilarityMatch(
            entity1_name=char1.name,
            entity1_story=char1.story,
            entity2_name=char2.name,
            entity2_story=char2.story,
            score=round(score, 3),
            shared_traits=shared_traits,
            shared_tropes=shared_tropes
        )

    def find_all_similar_pairs(
        self, collection: StoryCollection, cross_story_only: bool = True
    ) -> List[SimilarityMatch]:
        """
        Find all significantly similar character pairs in the collection.

        Uses an O(n²) comparison over all characters.  When ``cross_story_only``
        is ``True`` (the default), characters from the same story are skipped
        to focus on inter-story structural parallels.

        Args:
            collection:       The StoryCollection to analyse.
            cross_story_only: If ``True``, skip character pairs from the same
                              story.  Defaults to ``True``.

        Returns:
            A list of SimilarityMatch instances sorted by descending score.
        """
        characters = collection.get_all_characters()
        similarities = []

        for i, char1 in enumerate(characters):
            for char2 in characters[i + 1:]:
                if cross_story_only and char1.story == char2.story:
                    continue

                match = self.find_similar_characters(char1, char2)
                if match:
                    similarities.append(match)

        similarities.sort(key=lambda x: x.score, reverse=True)

        return similarities

    def discover_patterns(
        self,
        collection: StoryCollection,
        min_frequency: int = 2,
        min_shared_traits: int = 3
    ) -> List[DiscoveredPattern]:
        """
        Discover novel trait combinations that recur across multiple stories.

        The method generates all combinations of size ``min_shared_traits``
        from each character's trait set, then counts how many different stories
        contain at least one character with that combination.  Combinations
        that are already explained by a known trope are excluded to surface
        only genuinely new patterns.

        Args:
            collection:         The StoryCollection to mine.
            min_frequency:      Minimum number of distinct stories a combination
                                must appear in to be reported.
            min_shared_traits:  Size of the trait combinations to search for.

        Returns:
            Up to 50 DiscoveredPattern instances sorted by
            ``frequency × confidence`` in descending order.
        """
        characters = collection.get_all_characters()

        from itertools import combinations

        trait_combos = defaultdict(list)  # combo → list of {"name", "story"} dicts

        for char in characters:
            traits = [self.normalize_trait(t) for t in char.get_all_traits()]
            traits = list(set(traits))

            for combo in combinations(sorted(traits), min_shared_traits):
                trait_combos[combo].append({
                    "name": char.name,
                    "story": char.story
                })

        patterns = []

        for combo, examples in trait_combos.items():
            stories = set(ex["story"] for ex in examples)
            if len(stories) >= min_frequency:
                # Skip combinations that are subsets of a known trope's required traits
                combo_set = set(combo)
                is_known = False
                for trope in self.tropes.values():
                    required = set(
                        self.normalize_trait(t) for t in trope.get("required_traits", [])
                    )
                    if required and required.issubset(combo_set):
                        is_known = True
                        break

                if not is_known:
                    pattern_name = " + ".join(
                        t.replace("_", " ").title() for t in combo[:3]
                    )

                    pattern = DiscoveredPattern(
                        pattern_name=pattern_name,
                        description=f"Characters sharing: {', '.join(combo)}",
                        shared_traits=list(combo),
                        examples=examples[:10],
                        frequency=len(examples),
                        confidence=len(stories) / len(collection.stories)
                    )
                    patterns.append(pattern)

        patterns.sort(key=lambda x: x.frequency * x.confidence, reverse=True)

        return patterns[:50]
