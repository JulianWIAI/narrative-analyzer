"""
StoryCollection.py
------------------
Defines the StoryCollection dataclass, which groups multiple Story instances
for cross-story analysis.  The collection is the top-level input accepted by
PatternMatcher and ReportGenerator, enabling trope matching, similarity
detection, and pattern discovery across an arbitrary set of titles.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from SBS.Story import Story
from SBS.Character import Character
from SBS.StoryObject import StoryObject
from SBS.PlotArc import PlotArc


@dataclass
class StoryCollection:
    """
    A named collection of Story instances used for cross-story analysis.

    StoryCollection acts as the entry point for the analysis pipeline.
    Stories can be added individually, loaded from single JSON files, or
    bulk-loaded from a directory.  The ``get_all_*`` helpers flatten the
    nested per-story lists into single sequences that the matching engine
    can iterate over without knowing the story boundaries.
    """

    name: str
    stories: List[Story] = field(default_factory=list)

    def add_story(self, story: Story):
        """
        Add an already-constructed Story to the collection.

        Args:
            story: A Story instance to append to the internal list.
        """
        self.stories.append(story)

    def add_story_from_file(self, filepath: str):
        """
        Load a story from a JSON file and add it to the collection.

        Args:
            filepath: Path to a story JSON file on disk.
        """
        story = Story.load(filepath)
        self.stories.append(story)

    def get_all_characters(self) -> List[Character]:
        """
        Return a flat list of every character across all stories.

        Returns:
            Concatenated list of Character instances from every story in
            the collection, in story-insertion order.
        """
        characters = []
        for story in self.stories:
            characters.extend(story.characters)
        return characters

    def get_all_objects(self) -> List[StoryObject]:
        """
        Return a flat list of every story object across all stories.

        Returns:
            Concatenated list of StoryObject instances from every story.
        """
        objects = []
        for story in self.stories:
            objects.extend(story.objects)
        return objects

    def get_all_arcs(self) -> List[PlotArc]:
        """
        Return a flat list of every plot arc across all stories.

        Returns:
            Concatenated list of PlotArc instances from every story.
        """
        arcs = []
        for story in self.stories:
            arcs.extend(story.arcs)
        return arcs

    def to_dict(self) -> dict:
        """
        Serialise the collection and all contained stories to a plain dictionary.

        Returns:
            A dictionary with the collection name and a ``'stories'`` list of
            serialised story dictionaries.
        """
        return {
            "name": self.name,
            "stories": [s.to_dict() for s in self.stories]
        }

    def save(self, filepath: str):
        """
        Persist the entire collection to a JSON file on disk.

        Args:
            filepath: Destination file path.  The file will be created or
                      overwritten.
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, filepath: str) -> "StoryCollection":
        """
        Load a collection from a JSON file previously saved with ``save``.

        Args:
            filepath: Path to the collection JSON file.

        Returns:
            A StoryCollection with all stories reconstructed.
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        collection = cls(name=data.get("name", "Unknown"))
        for story_data in data.get("stories", []):
            collection.stories.append(Story.from_dict(story_data))

        return collection

    @classmethod
    def load_from_directory(cls, directory: str, name: str = "Collection") -> "StoryCollection":
        """
        Bulk-load all story JSON files found in a directory.

        Each ``*.json`` file in the directory is treated as a single story.
        Files that cannot be parsed are skipped with an error message so that
        one bad file does not abort the entire load.

        Args:
            directory: Path to the directory containing story JSON files.
            name:      Human-readable name for the resulting collection.

        Returns:
            A StoryCollection containing every successfully loaded story.
        """
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
