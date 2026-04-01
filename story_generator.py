#!/usr/bin/env python3
"""
story_generator.py
------------------
Story data generator with pre-built templates and an interactive mode.

All templates in this file use entirely fictional, original universes created
for this project.  They contain no characters or content from any existing
franchise or copyrighted work.

Two modes:
1. TEMPLATE  : Use one of the pre-built fictional story templates.
2. INTERACTIVE: Answer questions about a story; generates a starter JSON file.

Usage:
------
# List available templates
python story_generator.py template --list

# Use a pre-built template
python story_generator.py template ironclad_guild -o data/ironclad.json

# Interactive mode
python story_generator.py interactive "My Story" -o data/my_story.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# ============================================================================
# PRE-BUILT STORY TEMPLATES
# These templates use entirely fictional, original universes created for this
# project.  They contain no characters or content from any existing franchise
# or copyrighted work.
# ============================================================================

STORY_TEMPLATES = {
    "ironclad_guild": {
        "title": "Ironclad Guild Chronicles",
        "category": "anime",
        "year": 2024,
        "genre": ["action", "adventure", "fantasy"],
        "themes": ["friendship", "guild", "redemption", "found_family"],
        "setting": "Kingdom of Vaelthorn",
        "power_system": "runic_forging",
        "characters": [
            {
                "name": "Kael Duskvane",
                "gender": "male",
                "species": "human",
                "role": "protagonist",
                "hair_color": "black",
                "family_status": "orphan",
                "traits": [
                    "determined", "hot_headed", "loyal",
                    "hidden_power", "unusual_hair_color", "brave"
                ],
                "dream": "Become the strongest Runeforger in the kingdom",
                "abilities": ["rune_strike", "iron_skin", "forge_burst"],
                "power_source": "runic_forging"
            },
            {
                "name": "Seraphine Coldwell",
                "gender": "female",
                "species": "human",
                "role": "deuteragonist",
                "hair_color": "silver",
                "traits": [
                    "intelligent", "calm", "kind",
                    "unusual_hair_color", "strategic"
                ],
                "dream": "Uncover the truth about the Runic Collapse",
                "abilities": ["rune_analysis", "barrier_glyph", "arcane_counter"],
                "power_source": "runic_forging"
            },
            {
                "name": "Breck Hammerfall",
                "gender": "male",
                "species": "dwarf",
                "role": "sidekick",
                "traits": ["comedic", "loyal", "brave", "proud", "can_speak"],
                "dream": "Restore his clan's legendary forge",
                "abilities": ["earth_rune", "shield_bash", "war_cry"],
                "power_source": "runic_forging"
            },
            {
                "name": "Grand Warden Orvyn",
                "gender": "male",
                "age": "old",
                "species": "human",
                "role": "mentor",
                "traits": [
                    "wise", "old", "powerful",
                    "grandfather_figure", "calm"
                ],
                "dream": "Ensure the guild survives after his retirement",
                "abilities": ["master_rune", "world_seal", "ancient_knowledge"],
                "power_source": "runic_forging"
            },
            {
                "name": "Vael Ashborne",
                "gender": "male",
                "species": "half_elf",
                "role": "rival",
                "hair_color": "white",
                "traits": [
                    "arrogant", "intelligent", "rival",
                    "unusual_hair_color", "tragic_past",
                    "starts_as_rival", "becomes_ally"
                ],
                "dream": "Prove that nobles are the rightful masters of runic power",
                "abilities": ["noble_rune", "void_edge", "pressure_field"],
                "power_source": "runic_forging"
            },
            {
                "name": "Mora Dusk",
                "gender": "female",
                "species": "human",
                "role": "antagonist",
                "hair_color": "red",
                "traits": [
                    "main_villain", "tragic", "intelligent",
                    "connected_to_hero", "unusual_hair_color",
                    "mysterious", "hidden_identity", "grand_plan"
                ],
                "dream": "Erase the existing guild system and rebuild the world",
                "abilities": ["collapse_rune", "soul_fracture", "forbidden_forge"],
                "power_source": "corrupted_runes"
            }
        ],
        "objects": [
            {
                "name": "The Primordial Anvil",
                "object_type": "artifact",
                "traits": [
                    "legendary", "ancient",
                    "collectible_power_item", "sought_by_villain",
                    "plot_essential"
                ],
                "plot_importance": "central"
            }
        ],
        "arcs": [
            {
                "name": "Guild Entrance Trials",
                "arc_type": "tournament",
                "traits": [
                    "tournament", "competition", "multiple_fighters",
                    "proves_worth", "reveals_new_characters"
                ],
                "themes": ["competition", "self_discovery"]
            },
            {
                "name": "The Collapse Conspiracy",
                "arc_type": "investigation",
                "traits": ["mystery", "world_building", "villain_revealed"],
                "themes": ["truth", "betrayal"]
            },
            {
                "name": "Battle for the Primordial Anvil",
                "arc_type": "war",
                "traits": [
                    "final_arc", "world_destruction_threat",
                    "all_heroes_unite", "sacrifice"
                ],
                "themes": ["sacrifice", "found_family"],
                "is_final_arc": True
            }
        ]
    },

    "starcross_academy": {
        "title": "Starcross Academy",
        "category": "anime",
        "year": 2024,
        "genre": ["action", "school", "sci-fi", "romance"],
        "themes": ["coming_of_age", "identity", "rivalry", "perseverance"],
        "setting": "Starcross Academy for Stellar Combatants",
        "power_system": "stellar_channeling",
        "characters": [
            {
                "name": "Ryuu Solente",
                "gender": "male",
                "species": "human",
                "role": "protagonist",
                "hair_color": "orange",
                "family_status": "orphan",
                "traits": [
                    "determined", "naive", "loyal", "hidden_power",
                    "brave", "unusual_hair_color", "hot_headed",
                    "friendship_empowers", "stated_dream"
                ],
                "dream": "Reach Class S and find his missing older sister",
                "abilities": ["solar_burst", "heat_aura", "nova_charge"],
                "power_source": "stellar_channeling"
            },
            {
                "name": "Lira Frostmere",
                "gender": "female",
                "species": "human",
                "role": "deuteragonist",
                "hair_color": "blue",
                "traits": [
                    "intelligent", "calm", "kind",
                    "unusual_hair_color", "determined"
                ],
                "dream": "Develop a new stellar technique accessible to low-rank students",
                "abilities": ["ice_lance", "cryo_field", "absolute_zero"],
                "power_source": "stellar_channeling"
            },
            {
                "name": "Zeno Brightmark",
                "gender": "male",
                "species": "human",
                "role": "rival",
                "hair_color": "blond",
                "traits": [
                    "arrogant", "intelligent", "rival",
                    "royalty", "wealthy",
                    "starts_as_rival", "becomes_ally"
                ],
                "dream": "Graduate first in his class and surpass his legendary father",
                "abilities": ["lightning_draw", "volt_step", "thunderfall"],
                "power_source": "stellar_channeling"
            },
            {
                "name": "Director Yuen Cassara",
                "gender": "female",
                "age": "middle_aged",
                "species": "human",
                "role": "mentor",
                "traits": [
                    "wise", "calm", "powerful",
                    "mysterious", "guardian_figure",
                    "appears_early", "teaches_protagonist"
                ],
                "dream": "Protect the next generation from repeating her generation's mistakes",
                "abilities": ["stellar_mastery", "void_step", "constellation_seal"],
                "power_source": "stellar_channeling"
            },
            {
                "name": "Nox",
                "gender": "male",
                "species": "construct",
                "role": "sidekick",
                "traits": [
                    "comedic", "loyal", "can_speak",
                    "animal_or_creature", "mascot"
                ],
                "dream": "Understand what it means to have a dream",
                "abilities": ["data_scan", "holographic_display", "energy_shield"],
                "power_source": "artificial"
            },
            {
                "name": "Caelus Vanthorn",
                "gender": "male",
                "species": "human",
                "role": "antagonist",
                "hair_color": "black",
                "traits": [
                    "main_villain", "intelligent", "tragic",
                    "connected_to_hero", "calm",
                    "mysterious", "hidden_identity", "grand_plan"
                ],
                "dream": "Collapse the Academy's ranking system and expose the corruption at its core",
                "abilities": ["dark_star", "erasure_field", "stellar_inversion"],
                "power_source": "corrupted_stellar"
            }
        ],
        "objects": [
            {
                "name": "The Stellar Codex",
                "object_type": "artifact",
                "traits": [
                    "legendary", "ancient",
                    "collectible_power_item", "key_to_mystery",
                    "plot_essential"
                ],
                "plot_importance": "central"
            }
        ],
        "arcs": [
            {
                "name": "Placement Exams",
                "arc_type": "tournament",
                "traits": [
                    "tournament", "competition", "multiple_fighters",
                    "class_ranking", "reveals_new_characters"
                ],
                "themes": ["first_impressions", "potential"]
            },
            {
                "name": "The Phantom Student Incident",
                "arc_type": "mystery",
                "traits": ["mystery", "school_threat", "villain_hinted"],
                "themes": ["identity", "trust"]
            },
            {
                "name": "The Grand Stellar Games",
                "arc_type": "tournament",
                "traits": [
                    "tournament", "inter_school",
                    "high_stakes", "competition", "multiple_fighters",
                    "power_showcase"
                ],
                "themes": ["teamwork", "growth"]
            },
            {
                "name": "The Dark Star Crisis",
                "arc_type": "war",
                "traits": [
                    "final_arc", "world_destruction_threat",
                    "villain_revealed", "all_heroes_unite", "sacrifice"
                ],
                "themes": ["sacrifice", "redemption"],
                "is_final_arc": True
            }
        ]
    },

    "voidwalkers": {
        "title": "Voidwalkers",
        "category": "manga",
        "year": 2024,
        "genre": ["dark_fantasy", "action", "psychological"],
        "themes": ["survival", "moral_ambiguity", "sacrifice", "humanity"],
        "setting": "The Fractured Reaches (post-apocalyptic dimension)",
        "power_system": "void_resonance",
        "characters": [
            {
                "name": "Eryn Shade",
                "gender": "female",
                "species": "human",
                "role": "protagonist",
                "hair_color": "dark_grey",
                "family_status": "orphan",
                "traits": [
                    "determined", "calm", "brave",
                    "hidden_power", "tragic_past",
                    "unusual_hair_color", "stated_dream"
                ],
                "dream": "Close the Void Gates and end the dimensional bleed",
                "abilities": ["void_step", "shadow_bind", "resonance_pulse"],
                "power_source": "void_resonance"
            },
            {
                "name": "Matthis Greave",
                "gender": "male",
                "species": "human",
                "role": "deuteragonist",
                "hair_color": "brown",
                "traits": [
                    "loyal", "kind", "brave",
                    "determined", "comedic",
                    "large_or_strong", "kind_personality", "protective"
                ],
                "dream": "Protect the surviving settlements at any cost",
                "abilities": ["impact_burst", "iron_will", "fortify"],
                "power_source": "physical_enhancement"
            },
            {
                "name": "Ix",
                "gender": "male",
                "species": "void_construct",
                "role": "rival",
                "traits": [
                    "arrogant", "intelligent", "calm",
                    "mysterious", "transforms",
                    "starts_as_rival", "becomes_ally"
                ],
                "dream": "Determine whether humans are worth preserving",
                "abilities": ["void_blade", "dimensional_slash", "null_field"],
                "power_source": "void_resonance"
            },
            {
                "name": "The Archivist",
                "gender": "male",
                "age": "ancient",
                "species": "unknown",
                "role": "mentor",
                "traits": [
                    "wise", "old", "calm",
                    "mysterious", "powerful",
                    "appears_early", "teaches_protagonist",
                    "grandfather_figure"
                ],
                "dream": "Pass on the knowledge needed to seal the Void before he fades",
                "abilities": ["memory_read", "barrier_absolute", "time_lock"],
                "power_source": "ancient_resonance"
            },
            {
                "name": "Vael the Unmade",
                "gender": "female",
                "species": "human_corrupted",
                "role": "antagonist",
                "hair_color": "white",
                "traits": [
                    "main_villain", "tragic", "intelligent",
                    "immortal", "connected_to_hero",
                    "unusual_hair_color", "transforms",
                    "mysterious", "hidden_identity", "grand_plan",
                    "appears_late"
                ],
                "dream": "Merge all dimensions into the Void to end all suffering permanently",
                "abilities": ["total_erasure", "dimensional_collapse", "corruption_spread"],
                "power_source": "corrupted_void"
            }
        ],
        "objects": [
            {
                "name": "Void Core Shards",
                "object_type": "collectible",
                "traits": [
                    "collectible", "set_of_items", "grants_power_or_progress",
                    "scattered", "villains_want_them",
                    "dangerous", "key_to_sealing"
                ],
                "plot_importance": "central"
            },
            {
                "name": "The Archivist's Tome",
                "object_type": "artifact",
                "traits": [
                    "device_or_tool", "plot_essential",
                    "inherited", "special_power",
                    "from_parent", "symbol_of_legacy",
                    "unique", "guides_journey", "given_by_mentor"
                ],
                "plot_importance": "major"
            }
        ],
        "arcs": [
            {
                "name": "Awakening in the Reaches",
                "arc_type": "introduction",
                "traits": [
                    "journey", "destination_goal",
                    "world_building", "power_awakening", "first_loss"
                ],
                "themes": ["survival", "disorientation"]
            },
            {
                "name": "The Shard Hunt",
                "arc_type": "quest",
                "traits": [
                    "journey", "destination_goal",
                    "collectible_power_items", "cross_faction",
                    "moral_choices", "companions_join",
                    "episodic_locations", "grow_stronger_on_way"
                ],
                "themes": ["trust", "sacrifice"]
            },
            {
                "name": "The Final Convergence",
                "arc_type": "war",
                "traits": [
                    "final_arc", "world_destruction_threat",
                    "hero_sacrifice", "all_heroes_unite"
                ],
                "themes": ["humanity", "cost_of_victory"],
                "is_final_arc": True
            }
        ]
    },
}


def save_template(template_name: str, output_path: str) -> bool:
    """Save a pre-built template to file."""
    template_key = template_name.lower().replace(" ", "_").replace("-", "_")

    if template_key not in STORY_TEMPLATES:
        print(f"Template '{template_name}' not found.")
        print(f"Available templates: {', '.join(STORY_TEMPLATES.keys())}")
        return False

    story = STORY_TEMPLATES[template_key].copy()

    # Add story name to each character
    for char in story.get("characters", []):
        char["story"] = story["title"]

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(story, f, indent=2, ensure_ascii=False)

    print(f"Template saved to: {output_path}")
    print(f"  Title: {story['title']}")
    print(f"  Characters: {len(story.get('characters', []))}")
    print(f"  Objects: {len(story.get('objects', []))}")
    print(f"  Arcs: {len(story.get('arcs', []))}")

    return True


def list_templates():
    """List all available templates."""
    print("\nAvailable Story Templates:")
    print("=" * 50)

    for key, template in STORY_TEMPLATES.items():
        char_count = len(template.get("characters", []))
        print(f"  {key:<25} - {template['title']} ({char_count} characters)")

    print("\nUsage: python story_generator.py template <name> -o output.json")


def interactive_generator(title: str, output_path: str):
    """Interactive story generator - prompts user for information."""
    print(f"\n{'=' * 60}")
    print(f"INTERACTIVE STORY GENERATOR: {title}")
    print(f"{'=' * 60}")
    print("\nI'll ask you questions about the story. Answer as best you can.")
    print("Press Enter to skip any question.\n")

    story = {
        "title": title,
        "category": input("Category (anime/game/movie/book) [anime]: ").strip() or "anime",
        "year": None,
        "genre": [],
        "themes": [],
        "characters": [],
        "objects": [],
        "arcs": []
    }

    # Year
    year_input = input("Release year: ").strip()
    if year_input.isdigit():
        story["year"] = int(year_input)

    # Genre
    genre_input = input("Genres (comma-separated): ").strip()
    if genre_input:
        story["genre"] = [g.strip().lower() for g in genre_input.split(",")]

    # Themes
    theme_input = input("Themes (comma-separated): ").strip()
    if theme_input:
        story["themes"] = [t.strip().lower() for t in theme_input.split(",")]

    # Power system
    story["power_system"] = input("Power system (e.g., 'chakra', 'magic', 'ki'): ").strip()

    print("\n--- CHARACTERS ---")
    print("Enter character info. Type 'done' when finished.\n")

    while True:
        name = input("Character name (or 'done'): ").strip()
        if name.lower() == 'done' or not name:
            break

        char = {"name": name, "story": title}

        role = input(f"  Role (protagonist/rival/mentor/antagonist/sidekick/supporting): ").strip()
        char["role"] = role if role else "supporting"

        gender = input(f"  Gender (male/female): ").strip()
        char["gender"] = gender if gender else "unknown"

        traits = input(f"  Traits (comma-separated, e.g., 'brave, loyal, orphan'): ").strip()
        char["traits"] = [t.strip() for t in traits.split(",")] if traits else []

        dream = input(f"  Dream/goal: ").strip()
        if dream:
            char["dream"] = dream

        story["characters"].append(char)
        print()

    # Save
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(story, f, indent=2, ensure_ascii=False)

    print(f"\nStory saved to: {output_path}")
    print(f"Characters: {len(story['characters'])}")

    print("\nTIP: You can manually edit the JSON file to add more details,")
    print("or use an AI assistant to generate more complete character data.")


def main():
    parser = argparse.ArgumentParser(description="Story Data Generator")

    subparsers = parser.add_subparsers(dest="command")

    # Template command
    template_parser = subparsers.add_parser("template", help="Use a pre-built story template")
    template_parser.add_argument("name", nargs="?", help="Template name")
    template_parser.add_argument("-o", "--output", help="Output JSON file")
    template_parser.add_argument("--list", action="store_true", help="List available templates")

    # Interactive command
    interactive_parser = subparsers.add_parser("interactive", help="Interactive story creation")
    interactive_parser.add_argument("title", help="Story title")
    interactive_parser.add_argument("-o", "--output", required=True, help="Output JSON file")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        print("\nExamples:")
        print("  python story_generator.py template --list")
        print("  python story_generator.py template ironclad_guild -o data/ironclad.json")
        print("  python story_generator.py template starcross_academy -o data/starcross.json")
        print("  python story_generator.py interactive 'My Story' -o data/mystory.json")
        return 0

    if args.command == "template":
        if args.list or not args.name:
            list_templates()
            return 0

        output = args.output or f"data/{args.name.lower()}.json"
        if save_template(args.name, output):
            return 0
        return 1

    elif args.command == "interactive":
        interactive_generator(args.title, args.output)
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
