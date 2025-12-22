"""
Narrative Pattern Analyzer - Pattern Matching Engine

This module contains the core logic for:
- Matching characters/objects/plots against known tropes
- Finding similarities across stories
- Discovering new patterns
- Calculating similarity scores
"""

from typing import List, Dict, Tuple, Optional, Any
from collections import defaultdict
from dataclasses import dataclass
import re

from models import Character, StoryObject, PlotArc, Story, StoryCollection
from config import (KNOWN_TROPES, CHARACTER_ARCHETYPES, TRAIT_SYNONYMS, 
                   PLOT_ELEMENTS, SIMILARITY_WEIGHTS, OUTPUT_SETTINGS)


@dataclass
class TropeMatch:
    """Represents a match between an entity and a trope."""
    trope_id: str
    trope_name: str
    entity_name: str
    entity_type: str  # "character", "object", "arc"
    story: str
    score: float
    matched_traits: List[str]
    missing_traits: List[str]
    
    def to_dict(self) -> dict:
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


@dataclass
class SimilarityMatch:
    """Represents a similarity between two entities."""
    entity1_name: str
    entity1_story: str
    entity2_name: str
    entity2_story: str
    score: float
    shared_traits: List[str]
    shared_tropes: List[str]
    
    def to_dict(self) -> dict:
        return {
            "entity1": {"name": self.entity1_name, "story": self.entity1_story},
            "entity2": {"name": self.entity2_name, "story": self.entity2_story},
            "score": self.score,
            "shared_traits": self.shared_traits,
            "shared_tropes": self.shared_tropes,
        }


@dataclass
class DiscoveredPattern:
    """A newly discovered pattern across stories."""
    pattern_name: str
    description: str
    shared_traits: List[str]
    examples: List[Dict[str, str]]  # [{"name": ..., "story": ...}, ...]
    frequency: int
    confidence: float
    
    def to_dict(self) -> dict:
        return {
            "pattern_name": self.pattern_name,
            "description": self.description,
            "shared_traits": self.shared_traits,
            "examples": self.examples,
            "frequency": self.frequency,
            "confidence": self.confidence,
        }


class PatternMatcher:
    """Core engine for matching patterns and finding similarities."""
    
    def __init__(self):
        self.tropes = KNOWN_TROPES
        self.archetypes = CHARACTER_ARCHETYPES
        self.synonyms = TRAIT_SYNONYMS
        self.weights = SIMILARITY_WEIGHTS
        self.min_score = OUTPUT_SETTINGS["min_similarity_score"]
    
    def normalize_trait(self, trait: str) -> str:
        """Normalize a trait string for comparison."""
        return trait.lower().strip().replace(" ", "_").replace("-", "_")
    
    def expand_trait(self, trait: str) -> List[str]:
        """Expand a trait to include synonyms."""
        normalized = self.normalize_trait(trait)
        expanded = [normalized]
        
        # Check if trait is in synonyms
        for canonical, synonyms in self.synonyms.items():
            if normalized in [self.normalize_trait(s) for s in synonyms]:
                expanded.append(canonical)
                expanded.extend([self.normalize_trait(s) for s in synonyms])
            elif normalized == canonical:
                expanded.extend([self.normalize_trait(s) for s in synonyms])
        
        return list(set(expanded))
    
    def traits_match(self, trait1: str, trait2: str) -> Tuple[bool, float]:
        """
        Check if two traits match (including synonyms).
        Returns (match, score).
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
    
    def calculate_trait_overlap(self, traits1: List[str], traits2: List[str]) -> Tuple[List[str], float]:
        """
        Calculate overlap between two trait lists.
        Returns (shared_traits, score).
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
        
        # Normalize score
        max_possible = min(len(traits1), len(traits2))
        if max_possible > 0:
            normalized_score = total_score / max_possible
        else:
            normalized_score = 0.0
        
        return shared, min(normalized_score, 1.0)
    
    def match_character_to_trope(self, character: Character, trope_id: str) -> Optional[TropeMatch]:
        """Match a character against a specific trope."""
        if trope_id not in self.tropes:
            return None
        
        trope = self.tropes[trope_id]
        
        # Only match character tropes
        if trope["category"] != "character":
            return None
        
        char_traits = character.get_all_traits()
        char_traits_normalized = [self.normalize_trait(t) for t in char_traits]
        
        # Check required traits
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
        
        # Must have all required traits
        if required_missing:
            return None
        
        # Check associated traits for bonus score
        associated = trope.get("associated_traits", [])
        associated_matched = []
        
        for assoc in associated:
            for char_trait in char_traits_normalized:
                match, _ = self.traits_match(assoc, char_trait)
                if match:
                    associated_matched.append(assoc)
                    break
        
        # Calculate score
        required_score = len(required_matched) / len(required) if required else 1.0
        associated_score = len(associated_matched) / len(associated) if associated else 0.0
        
        # Weighted combination
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
    
    def match_object_to_trope(self, obj: StoryObject, trope_id: str) -> Optional[TropeMatch]:
        """Match an object against a specific trope."""
        if trope_id not in self.tropes:
            return None
        
        trope = self.tropes[trope_id]
        
        # Only match object tropes
        if trope["category"] != "object":
            return None
        
        obj_traits = obj.get_all_traits()
        obj_traits_normalized = [self.normalize_trait(t) for t in obj_traits]
        
        # Check required traits
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
        
        # Associated traits
        associated = trope.get("associated_traits", [])
        associated_matched = []
        
        for assoc in associated:
            for obj_trait in obj_traits_normalized:
                match, _ = self.traits_match(assoc, obj_trait)
                if match:
                    associated_matched.append(assoc)
                    break
        
        # Calculate score
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
    
    def match_arc_to_trope(self, arc: PlotArc, trope_id: str) -> Optional[TropeMatch]:
        """Match a plot arc against a specific trope."""
        if trope_id not in self.tropes:
            return None
        
        trope = self.tropes[trope_id]
        
        # Only match plot/theme tropes
        if trope["category"] not in ["plot", "theme"]:
            return None
        
        arc_traits = arc.traits + arc.themes + [arc.arc_type]
        arc_traits_normalized = [self.normalize_trait(t) for t in arc_traits]
        
        # Check required traits
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
        
        # Associated traits
        associated = trope.get("associated_traits", [])
        associated_matched = []
        
        for assoc in associated:
            for arc_trait in arc_traits_normalized:
                match, _ = self.traits_match(assoc, arc_trait)
                if match:
                    associated_matched.append(assoc)
                    break
        
        # Calculate score
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
    
    def find_all_trope_matches(self, collection: StoryCollection) -> Dict[str, List[TropeMatch]]:
        """Find all trope matches across a story collection."""
        matches_by_trope = defaultdict(list)
        
        for story in collection.stories:
            # Match characters
            for character in story.characters:
                for trope_id in self.tropes:
                    match = self.match_character_to_trope(character, trope_id)
                    if match:
                        matches_by_trope[trope_id].append(match)
            
            # Match objects
            for obj in story.objects:
                for trope_id in self.tropes:
                    match = self.match_object_to_trope(obj, trope_id)
                    if match:
                        matches_by_trope[trope_id].append(match)
            
            # Match arcs
            for arc in story.arcs:
                for trope_id in self.tropes:
                    match = self.match_arc_to_trope(arc, trope_id)
                    if match:
                        matches_by_trope[trope_id].append(match)
        
        # Sort by score
        for trope_id in matches_by_trope:
            matches_by_trope[trope_id].sort(key=lambda x: x.score, reverse=True)
        
        return dict(matches_by_trope)
    
    def find_similar_characters(self, char1: Character, char2: Character) -> Optional[SimilarityMatch]:
        """Find similarity between two characters."""
        traits1 = char1.get_all_traits()
        traits2 = char2.get_all_traits()
        
        shared_traits, score = self.calculate_trait_overlap(traits1, traits2)
        
        if score < self.min_score:
            return None
        
        # Find shared tropes
        shared_tropes = []
        for trope_id in self.tropes:
            match1 = self.match_character_to_trope(char1, trope_id)
            match2 = self.match_character_to_trope(char2, trope_id)
            if match1 and match2:
                shared_tropes.append(self.tropes[trope_id]["name"])
        
        # Boost score if they share tropes
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
    
    def find_all_similar_pairs(self, collection: StoryCollection, 
                               cross_story_only: bool = True) -> List[SimilarityMatch]:
        """Find all similar character pairs in the collection."""
        characters = collection.get_all_characters()
        similarities = []
        
        for i, char1 in enumerate(characters):
            for char2 in characters[i+1:]:
                # Skip same-story comparisons if requested
                if cross_story_only and char1.story == char2.story:
                    continue
                
                match = self.find_similar_characters(char1, char2)
                if match:
                    similarities.append(match)
        
        # Sort by score
        similarities.sort(key=lambda x: x.score, reverse=True)
        
        return similarities
    
    def discover_patterns(self, collection: StoryCollection, 
                         min_frequency: int = 2,
                         min_shared_traits: int = 3) -> List[DiscoveredPattern]:
        """
        Discover new patterns across stories.
        Looks for trait combinations that appear frequently.
        """
        characters = collection.get_all_characters()
        
        # Count trait combinations
        from itertools import combinations
        
        trait_combos = defaultdict(list)  # combo -> list of characters
        
        for char in characters:
            traits = [self.normalize_trait(t) for t in char.get_all_traits()]
            traits = list(set(traits))  # Remove duplicates
            
            # Generate combinations of size min_shared_traits
            for combo in combinations(sorted(traits), min_shared_traits):
                trait_combos[combo].append({
                    "name": char.name,
                    "story": char.story
                })
        
        # Filter by frequency and cross-story requirement
        patterns = []
        
        for combo, examples in trait_combos.items():
            # Must appear in at least min_frequency different stories
            stories = set(ex["story"] for ex in examples)
            if len(stories) >= min_frequency:
                # Check if this is a known trope (skip if so)
                combo_set = set(combo)
                is_known = False
                for trope in self.tropes.values():
                    required = set(self.normalize_trait(t) for t in trope.get("required_traits", []))
                    if required and required.issubset(combo_set):
                        is_known = True
                        break
                
                if not is_known:
                    # Generate pattern name from traits
                    pattern_name = " + ".join(t.replace("_", " ").title() for t in combo[:3])
                    
                    pattern = DiscoveredPattern(
                        pattern_name=pattern_name,
                        description=f"Characters sharing: {', '.join(combo)}",
                        shared_traits=list(combo),
                        examples=examples[:10],  # Limit examples
                        frequency=len(examples),
                        confidence=len(stories) / len(collection.stories)
                    )
                    patterns.append(pattern)
        
        # Sort by frequency * confidence
        patterns.sort(key=lambda x: x.frequency * x.confidence, reverse=True)
        
        return patterns[:50]  # Return top 50 patterns


class ArchetypeMatcher:
    """Matches characters to known archetypes."""
    
    def __init__(self):
        self.archetypes = CHARACTER_ARCHETYPES
        self.synonyms = TRAIT_SYNONYMS
    
    def normalize_trait(self, trait: str) -> str:
        return trait.lower().strip().replace(" ", "_").replace("-", "_")
    
    def match_character_to_archetype(self, character: Character) -> List[Tuple[str, float]]:
        """
        Match a character to archetypes.
        Returns list of (archetype_name, score) sorted by score.
        """
        char_traits = [self.normalize_trait(t) for t in character.get_all_traits()]
        matches = []
        
        for arch_id, archetype in self.archetypes.items():
            arch_traits = [self.normalize_trait(t) for t in archetype["traits"]]
            
            # Count matches
            matched = 0
            for arch_trait in arch_traits:
                for char_trait in char_traits:
                    if arch_trait == char_trait or arch_trait in char_trait or char_trait in arch_trait:
                        matched += 1
                        break
            
            if matched > 0:
                score = matched / len(arch_traits)
                matches.append((archetype["name"], round(score, 3)))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
