#!/usr/bin/env python3
"""
main.py
-------
Command-line interface for the Narrative Pattern Analyzer.

Provides six sub-commands for loading, analysing, comparing, and templating
story data.  All heavy lifting is delegated to the SBS package.

Usage:
------
# Analyze all stories in data folder
python main.py analyze ./data -o ./output

# Analyze specific stories
python main.py analyze ./data/demo_ironclad_guild.json ./data/demo_starcross_academy.json

# Find similarities between two stories
python main.py compare ./data/demo_ironclad_guild.json ./data/demo_voidwalkers.json

# List known tropes
python main.py tropes

# Create a new story template
python main.py template "My Story" -o my_story.json
"""

import argparse
import sys
import json
from pathlib import Path

from SBS.Story import Story
from SBS.StoryCollection import StoryCollection
from SBS.Character import Character
from SBS.StoryObject import StoryObject
from SBS.PlotArc import PlotArc
from SBS.PatternMatcher import PatternMatcher
from SBS.ArchetypeMatcher import ArchetypeMatcher
from SBS.ReportGenerator import ReportGenerator
from config import KNOWN_TROPES, CHARACTER_ARCHETYPES


def cmd_analyze(args):
    """Analyze stories for patterns and tropes."""
    print("=" * 70)
    print("NARRATIVE PATTERN ANALYZER")
    print("=" * 70)
    
    # Load stories
    collection = StoryCollection(name=args.name or "Analysis")
    
    for path in args.input:
        path = Path(path)
        if path.is_dir():
            # Load all JSON files in directory
            for json_file in path.glob("*.json"):
                try:
                    story = Story.load(str(json_file))
                    collection.add_story(story)
                    print(f"Loaded: {story.title}")
                except Exception as e:
                    print(f"Error loading {json_file}: {e}")
        elif path.is_file():
            try:
                story = Story.load(str(path))
                collection.add_story(story)
                print(f"Loaded: {story.title}")
            except Exception as e:
                print(f"Error loading {path}: {e}")
    
    if not collection.stories:
        print("No stories loaded. Exiting.")
        return 1
    
    print(f"\nAnalyzing {len(collection.stories)} stories...")
    print(f"Total characters: {len(collection.get_all_characters())}")
    print(f"Total objects: {len(collection.get_all_objects())}")
    print(f"Total arcs: {len(collection.get_all_arcs())}")
    
    # Generate reports
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nGenerating reports...")
    generator = ReportGenerator(collection)
    generator.save_all_reports(str(output_dir))
    
    # Print summary to console
    print("\n" + generator.generate_text_report())
    
    return 0


def cmd_compare(args):
    """Compare two stories side by side."""
    print("=" * 70)
    print("STORY COMPARISON")
    print("=" * 70)
    
    # Load both stories
    try:
        story1 = Story.load(args.story1)
        story2 = Story.load(args.story2)
    except Exception as e:
        print(f"Error loading stories: {e}")
        return 1
    
    print(f"\nComparing: {story1.title} vs {story2.title}")
    print("-" * 40)
    
    # Create collection and analyze
    collection = StoryCollection(name="Comparison")
    collection.add_story(story1)
    collection.add_story(story2)
    
    matcher = PatternMatcher()
    
    # Find shared tropes
    trope_matches = matcher.find_all_trope_matches(collection)
    
    print("\n## SHARED TROPES")
    for trope_id, matches in trope_matches.items():
        story1_matches = [m for m in matches if m.story == story1.title]
        story2_matches = [m for m in matches if m.story == story2.title]
        
        if story1_matches and story2_matches:
            trope = KNOWN_TROPES[trope_id]
            print(f"\n  {trope['name']}:")
            print(f"    {story1.title}: {', '.join([m.entity_name for m in story1_matches[:3]])}")
            print(f"    {story2.title}: {', '.join([m.entity_name for m in story2_matches[:3]])}")
    
    # Find similar characters
    similarities = matcher.find_all_similar_pairs(collection, cross_story_only=True)
    
    print("\n## SIMILAR CHARACTERS")
    for sim in similarities[:10]:
        print(f"\n  [{sim.score:.0%}] {sim.entity1_name} ({sim.entity1_story})")
        print(f"         ↔ {sim.entity2_name} ({sim.entity2_story})")
        print(f"         Shared: {', '.join(sim.shared_traits[:5])}")
    
    return 0


def cmd_tropes(args):
    """List all known tropes."""
    print("=" * 70)
    print("KNOWN STORY TROPES")
    print("=" * 70)
    
    categories = {}
    for trope_id, trope in KNOWN_TROPES.items():
        cat = trope.get("category", "other")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append((trope_id, trope))
    
    for category, tropes in sorted(categories.items()):
        print(f"\n## {category.upper()}")
        print("-" * 40)
        for trope_id, trope in tropes:
            print(f"\n  {trope['name']}")
            print(f"    {trope['description']}")
            print(f"    Required: {', '.join(trope.get('required_traits', []))}")
            if trope.get('examples'):
                print(f"    Examples: {', '.join(trope['examples'][:3])}")
    
    return 0


def cmd_archetypes(args):
    """List character archetypes."""
    print("=" * 70)
    print("CHARACTER ARCHETYPES")
    print("=" * 70)
    
    for arch_id, archetype in CHARACTER_ARCHETYPES.items():
        print(f"\n## {archetype['name']}")
        print(f"   Traits: {', '.join(archetype['traits'])}")
        print(f"   Backgrounds: {', '.join(archetype.get('common_backgrounds', []))}")
    
    return 0


def cmd_template(args):
    """Generate a story template."""
    story = Story(
        title=args.title,
        category=args.category,
        year=None,
        genre=[],
        themes=[],
        setting="",
        power_system="",
        characters=[
            Character(
                name="Protagonist Name",
                story=args.title,
                role="protagonist",
                traits=["brave", "determined"],
                family_status="orphan_or_absent_parent",
                dream="Their main goal"
            ),
            Character(
                name="Mentor Name",
                story=args.title,
                role="mentor",
                traits=["old", "wise", "appears_early"],
                age="old"
            ),
            Character(
                name="Rival Name",
                story=args.title,
                role="rival",
                traits=["proud", "skilled", "starts_as_rival"]
            )
        ],
        objects=[
            StoryObject(
                name="Important Item",
                story=args.title,
                object_type="device",
                traits=["plot_essential", "given_by_mentor"],
                plot_importance="major"
            )
        ],
        arcs=[
            PlotArc(
                name="Main Arc",
                story=args.title,
                arc_type="journey",
                traits=["journey", "destination_goal"]
            )
        ]
    )
    
    output_path = args.output or f"{args.title.lower().replace(' ', '_')}.json"
    story.save(output_path)
    print(f"Template saved to: {output_path}")
    print("\nEdit this file to add your story's characters, objects, and plot details.")
    print("Then run: python main.py analyze your_story.json")
    
    return 0


def cmd_character(args):
    """Analyze a single character against archetypes and tropes."""
    # Load story
    try:
        story = Story.load(args.story)
    except Exception as e:
        print(f"Error loading story: {e}")
        return 1
    
    # Find character
    char = None
    for c in story.characters:
        if c.name.lower() == args.name.lower():
            char = c
            break
    
    if not char:
        print(f"Character '{args.name}' not found in {story.title}")
        print(f"Available: {', '.join([c.name for c in story.characters])}")
        return 1
    
    print("=" * 70)
    print(f"CHARACTER ANALYSIS: {char.name}")
    print("=" * 70)
    
    print(f"\nStory: {story.title}")
    print(f"Role: {char.role}")
    print(f"Traits: {', '.join(char.get_all_traits())}")
    
    # Match archetypes
    arch_matcher = ArchetypeMatcher()
    archetypes = arch_matcher.match_character_to_archetype(char)
    
    print("\n## ARCHETYPE MATCHES")
    for arch_name, score in archetypes[:5]:
        print(f"  [{score:.0%}] {arch_name}")
    
    # Match tropes
    matcher = PatternMatcher()
    print("\n## TROPE MATCHES")
    for trope_id in KNOWN_TROPES:
        match = matcher.match_character_to_trope(char, trope_id)
        if match:
            print(f"  [{match.score:.0%}] {match.trope_name}")
            print(f"         Matched: {', '.join(match.matched_traits)}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Narrative Pattern Analyzer - Find story patterns across narratives",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py analyze ./data -o ./output
  python main.py compare data/demo_ironclad_guild.json data/demo_voidwalkers.json
  python main.py tropes
  python main.py template "My Story" -o my_story.json
  python main.py character data/demo_ironclad_guild.json "Kael Duskvane"
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze stories for patterns")
    analyze_parser.add_argument("input", nargs="+", help="Story JSON files or directories")
    analyze_parser.add_argument("-o", "--output", default="output", help="Output directory")
    analyze_parser.add_argument("-n", "--name", help="Collection name")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare two stories")
    compare_parser.add_argument("story1", help="First story JSON file")
    compare_parser.add_argument("story2", help="Second story JSON file")
    
    # Tropes command
    tropes_parser = subparsers.add_parser("tropes", help="List known tropes")
    
    # Archetypes command
    arch_parser = subparsers.add_parser("archetypes", help="List character archetypes")
    
    # Template command
    template_parser = subparsers.add_parser("template", help="Generate story template")
    template_parser.add_argument("title", help="Story title")
    template_parser.add_argument("-c", "--category", default="anime", 
                                 help="Category (anime, game, movie, etc.)")
    template_parser.add_argument("-o", "--output", help="Output file path")
    
    # Character command
    char_parser = subparsers.add_parser("character", help="Analyze a single character")
    char_parser.add_argument("story", help="Story JSON file")
    char_parser.add_argument("name", help="Character name")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return 1
    
    commands = {
        "analyze": cmd_analyze,
        "compare": cmd_compare,
        "tropes": cmd_tropes,
        "archetypes": cmd_archetypes,
        "template": cmd_template,
        "character": cmd_character,
    }
    
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
