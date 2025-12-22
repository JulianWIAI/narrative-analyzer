"""
Narrative Pattern Analyzer - Data Models

Data structures for representing stories, characters, objects, and plot elements.
These can be loaded from JSON/YAML files or created programmatically.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from enum import Enum
import json
from pathlib import Path


class Gender(Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"


class CharacterRole(Enum):
    PROTAGONIST = "protagonist"
    DEUTERAGONIST = "deuteragonist"  # Secondary main character
    ANTAGONIST = "antagonist"
    MENTOR = "mentor"
    SIDEKICK = "sidekick"
    RIVAL = "rival"
    LOVE_INTEREST = "love_interest"
    COMIC_RELIEF = "comic_relief"
    SUPPORTING = "supporting"
    MINOR = "minor"


class StoryCategory(Enum):
    ANIME = "anime"
    MANGA = "manga"
    GAME = "game"
    MOVIE = "movie"
    TV_SHOW = "tv_show"
    BOOK = "book"
    COMIC = "comic"
    OTHER = "other"


@dataclass
class Character:
    """Represents a character in a story."""
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
        """Get all traits including derived ones."""
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


@dataclass
class StoryObject:
    """Represents an important object/item in a story."""
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
        """Get all traits including derived ones."""
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


@dataclass
class PlotArc:
    """Represents a story arc or major plot event."""
    name: str
    story: str
    
    # Type
    arc_type: str = "adventure"  # "tournament", "training", "rescue", "war", etc.
    
    # Characters involved
    main_characters: List[str] = field(default_factory=list)
    villains: List[str] = field(default_factory=list)
    
    # Plot elements
    traits: List[str] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)
    
    # Position in story
    is_final_arc: bool = False
    arc_number: Optional[int] = None
    
    # Custom metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
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


@dataclass
class Story:
    """Represents a complete story (anime, game, movie, etc.)."""
    title: str
    category: str = "anime"  # anime, game, movie, etc.
    
    # Basic info
    year: Optional[int] = None
    genre: List[str] = field(default_factory=list)
    themes: List[str] = field(default_factory=list)
    
    # Story elements
    characters: List[Character] = field(default_factory=list)
    objects: List[StoryObject] = field(default_factory=list)
    arcs: List[PlotArc] = field(default_factory=list)
    
    # World/Setting
    setting: Optional[str] = None
    power_system: Optional[str] = None
    
    # Structure
    has_generations: bool = False
    generation_count: Optional[int] = None
    
    # Custom metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
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
        
        # Load characters
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
        """Save story to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, filepath: str) -> "Story":
        """Load story from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    def get_protagonist(self) -> Optional[Character]:
        """Get the main protagonist."""
        for char in self.characters:
            if char.role == "protagonist":
                return char
        return None
    
    def get_characters_by_role(self, role: str) -> List[Character]:
        """Get all characters with a specific role."""
        return [c for c in self.characters if c.role == role]
    
    def get_main_team(self) -> List[Character]:
        """Get the main team/group of characters."""
        protagonist = self.get_protagonist()
        if protagonist and protagonist.team:
            return [c for c in self.characters if c.team == protagonist.team]
        return [c for c in self.characters if c.role in ["protagonist", "deuteragonist", "sidekick"]]


@dataclass
class StoryCollection:
    """A collection of multiple stories for cross-analysis."""
    name: str
    stories: List[Story] = field(default_factory=list)
    
    def add_story(self, story: Story):
        self.stories.append(story)
    
    def add_story_from_file(self, filepath: str):
        story = Story.load(filepath)
        self.stories.append(story)
    
    def get_all_characters(self) -> List[Character]:
        """Get all characters from all stories."""
        characters = []
        for story in self.stories:
            characters.extend(story.characters)
        return characters
    
    def get_all_objects(self) -> List[StoryObject]:
        """Get all objects from all stories."""
        objects = []
        for story in self.stories:
            objects.extend(story.objects)
        return objects
    
    def get_all_arcs(self) -> List[PlotArc]:
        """Get all arcs from all stories."""
        arcs = []
        for story in self.stories:
            arcs.extend(story.arcs)
        return arcs
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "stories": [s.to_dict() for s in self.stories]
        }
    
    def save(self, filepath: str):
        """Save collection to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, filepath: str) -> "StoryCollection":
        """Load collection from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        collection = cls(name=data.get("name", "Unknown"))
        for story_data in data.get("stories", []):
            collection.stories.append(Story.from_dict(story_data))
        
        return collection
    
    @classmethod
    def load_from_directory(cls, directory: str, name: str = "Collection") -> "StoryCollection":
        """Load all story JSON files from a directory."""
        collection = cls(name=name)
        dir_path = Path(directory)
        
        for json_file in dir_path.glob("*.json"):
            try:
                story = Story.load(str(json_file))
                collection.stories.append(story)
                print(f"Loaded: {story.title}")
            except Exception as e:
                print(f"Error loading {json_file}: {e}")
        
        return collection
