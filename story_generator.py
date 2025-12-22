#!/usr/bin/env python3
"""
AI-Assisted Story Data Generator

Instead of scraping wikis (which gives poor data), this tool helps you
generate accurate story JSON files using AI assistance.

Two modes:
1. INTERACTIVE: Answer questions about a story, generates JSON
2. TEMPLATE: Use pre-built templates for popular franchises

For best results, use this with an AI assistant (ChatGPT, Claude, etc.)
to generate the character data, then paste it here.

Usage:
------
# Interactive mode - answer questions
python story_generator.py interactive "Naruto" -o data/naruto.json

# Use a pre-built template
python story_generator.py template naruto -o data/naruto.json

# List available templates
python story_generator.py template --list

# Generate from a text description
python story_generator.py from-text description.txt -o data/story.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# ============================================================================
# PRE-BUILT STORY TEMPLATES
# These are complete, accurate story data for popular franchises
# ============================================================================

STORY_TEMPLATES = {
    "naruto": {
        "title": "Naruto",
        "category": "anime",
        "year": 1999,
        "genre": ["action", "adventure", "martial_arts", "fantasy"],
        "themes": ["hard_work", "friendship", "recognition", "bonds", "loneliness"],
        "setting": "Ninja World",
        "power_system": "chakra",
        "has_generations": True,
        "generation_count": 2,
        "characters": [
            {
                "name": "Naruto Uzumaki",
                "gender": "male",
                "age": "12-17",
                "species": "human",
                "role": "protagonist",
                "team": "Team 7",
                "hair_color": "blonde",
                "family_status": "orphan",
                "occupation": "Ninja",
                "traits": ["determined", "never_gives_up", "loud", "optimistic", "lonely_childhood", "hidden_power", "prankster", "loyal"],
                "dream": "Become Hokage",
                "abilities": ["shadow_clone", "rasengan", "sage_mode", "nine_tails_chakra"],
                "power_source": "chakra"
            },
            {
                "name": "Sasuke Uchiha",
                "gender": "male",
                "age": "12-17",
                "species": "human",
                "role": "rival",
                "team": "Team 7",
                "hair_color": "black",
                "family_status": "orphan",
                "occupation": "Ninja",
                "traits": ["prodigy", "cold", "revenge_driven", "starts_as_rival", "becomes_ally", "lone_wolf", "traumatized"],
                "dream": "Avenge clan",
                "abilities": ["sharingan", "chidori", "fire_style"],
                "power_source": "chakra"
            },
            {
                "name": "Sakura Haruno",
                "gender": "female",
                "age": "12-17",
                "species": "human",
                "role": "deuteragonist",
                "team": "Team 7",
                "hair_color": "pink",
                "family_status": "full_family",
                "occupation": "Ninja",
                "traits": ["intelligent", "hot_headed", "medical_ninja", "unusual_hair_color", "grows_stronger"],
                "abilities": ["medical_ninjutsu", "super_strength"],
                "power_source": "chakra"
            },
            {
                "name": "Kakashi Hatake",
                "gender": "male",
                "age": "adult",
                "species": "human",
                "role": "mentor",
                "team": "Team 7",
                "hair_color": "silver",
                "family_status": "orphan",
                "occupation": "Jonin",
                "traits": ["wise", "mysterious", "powerful", "lazy", "always_late", "teaches_protagonist", "appears_early", "tragic_past", "mask"],
                "abilities": ["sharingan", "lightning_blade", "thousand_jutsu"],
                "power_source": "chakra"
            },
            {
                "name": "Jiraiya",
                "gender": "male",
                "age": "old",
                "species": "human",
                "role": "mentor",
                "hair_color": "white",
                "family_status": "single",
                "occupation": "Sannin",
                "traits": ["old", "wise", "perverted", "powerful", "mentor", "grandfather_figure", "legendary", "author"],
                "dream": "Find peace",
                "abilities": ["sage_mode", "rasengan", "summoning"],
                "power_source": "chakra"
            },
            {
                "name": "Hinata Hyuga",
                "gender": "female",
                "species": "human",
                "role": "love_interest",
                "hair_color": "dark_blue",
                "traits": ["shy", "kind", "loyal", "grows_confident", "loves_protagonist", "unusual_hair_color"],
                "abilities": ["byakugan", "gentle_fist"],
                "power_source": "chakra"
            },
            {
                "name": "Rock Lee",
                "gender": "male",
                "species": "human",
                "role": "supporting",
                "traits": ["hard_working", "no_talent", "determination", "comedic", "youth", "underdog"],
                "abilities": ["taijutsu", "eight_gates"],
                "power_source": "physical"
            },
            {
                "name": "Gaara",
                "gender": "male",
                "species": "human",
                "role": "rival",
                "hair_color": "red",
                "family_status": "broken_family",
                "traits": ["lonely", "dangerous", "starts_as_rival", "becomes_ally", "redemption_arc", "jinchuriki", "unusual_hair_color"],
                "abilities": ["sand_control", "one_tail"],
                "power_source": "chakra"
            },
            {
                "name": "Orochimaru",
                "gender": "male",
                "species": "human",
                "role": "antagonist",
                "traits": ["villain", "genius", "immortality_obsessed", "snake_themed", "former_hero", "experiments"],
                "abilities": ["forbidden_jutsu", "immortality", "snake_summoning"],
                "power_source": "chakra"
            },
            {
                "name": "Itachi Uchiha",
                "gender": "male",
                "species": "human",
                "role": "antagonist",
                "hair_color": "black",
                "traits": ["mysterious", "tragic", "actually_good", "genius", "sacrificed_everything", "connected_to_rival"],
                "abilities": ["mangekyo_sharingan", "tsukuyomi", "amaterasu"],
                "power_source": "chakra"
            },
            {
                "name": "Madara Uchiha",
                "gender": "male",
                "species": "human",
                "role": "antagonist",
                "traits": ["main_villain", "legendary", "appears_late", "grand_plan", "godlike_power", "ancient"],
                "abilities": ["rinnegan", "perfect_susanoo"],
                "power_source": "chakra"
            }
        ],
        "objects": [
            {
                "name": "Headband",
                "object_type": "symbol",
                "traits": ["symbol_of_belonging", "village_affiliation"],
                "plot_importance": "major"
            },
            {
                "name": "Scroll of Sealing",
                "object_type": "artifact",
                "traits": ["forbidden", "plot_starter"],
                "plot_importance": "minor"
            }
        ],
        "arcs": [
            {
                "name": "Chunin Exams",
                "arc_type": "tournament",
                "traits": ["tournament", "multiple_fighters", "reveals_new_characters", "interrupted_by_villain"],
                "themes": ["competition", "growth"]
            },
            {
                "name": "Sasuke Retrieval",
                "arc_type": "rescue",
                "traits": ["rescue_mission", "team_splits_up", "failure"],
                "themes": ["friendship", "loss"]
            },
            {
                "name": "Pain Arc",
                "arc_type": "war",
                "traits": ["village_destruction", "sacrifice", "new_power_unlocked", "talk_no_jutsu"],
                "themes": ["pain", "forgiveness", "cycle_of_hatred"]
            },
            {
                "name": "Fourth Shinobi War",
                "arc_type": "war",
                "traits": ["world_destruction_threat", "all_heroes_unite", "final_arc", "sacrifice"],
                "themes": ["unity", "peace"],
                "is_final_arc": True
            }
        ]
    },
    
    "bleach": {
        "title": "Bleach",
        "category": "anime",
        "year": 2001,
        "genre": ["action", "supernatural", "adventure"],
        "themes": ["death", "protection", "identity", "duty"],
        "setting": "Human World and Soul Society",
        "power_system": "reiatsu",
        "characters": [
            {
                "name": "Ichigo Kurosaki",
                "gender": "male",
                "age": "15-17",
                "species": "human_shinigami_hollow_quincy",
                "role": "protagonist",
                "hair_color": "orange",
                "family_status": "single_parent",
                "traits": ["protective", "hot_headed", "unusual_hair_color", "hidden_power", "hybrid", "scowling"],
                "dream": "Protect everyone",
                "abilities": ["zangetsu", "bankai", "hollow_mask", "fullbring"],
                "power_source": "reiatsu"
            },
            {
                "name": "Rukia Kuchiki",
                "gender": "female",
                "species": "shinigami",
                "role": "deuteragonist",
                "hair_color": "black",
                "family_status": "orphan",
                "traits": ["noble", "serious", "gives_power", "mentor_to_hero", "rescued"],
                "abilities": ["sode_no_shirayuki", "kido"],
                "power_source": "reiatsu"
            },
            {
                "name": "Uryu Ishida",
                "gender": "male",
                "species": "quincy",
                "role": "rival",
                "hair_color": "black",
                "traits": ["proud", "intelligent", "glasses", "starts_as_rival", "becomes_ally", "archer"],
                "abilities": ["quincy_bow", "letzt_stil"],
                "power_source": "reiatsu"
            },
            {
                "name": "Orihime Inoue",
                "gender": "female",
                "species": "human",
                "role": "love_interest",
                "hair_color": "orange",
                "traits": ["kind", "healer", "unusual_hair_color", "loves_protagonist", "captured"],
                "abilities": ["shun_shun_rikka", "rejection"],
                "power_source": "reiatsu"
            },
            {
                "name": "Chad",
                "gender": "male",
                "species": "human",
                "role": "sidekick",
                "traits": ["gentle_giant", "quiet", "loyal", "strong", "protective"],
                "abilities": ["brazo_derecha", "fullbring"],
                "power_source": "reiatsu"
            },
            {
                "name": "Kisuke Urahara",
                "gender": "male",
                "age": "old",
                "species": "shinigami",
                "role": "mentor",
                "hair_color": "blonde",
                "traits": ["mysterious", "genius", "eccentric", "mentor", "shop_keeper", "former_captain", "knows_everything"],
                "abilities": ["benihime", "bankai", "kido_master"],
                "power_source": "reiatsu"
            },
            {
                "name": "Byakuya Kuchiki",
                "gender": "male",
                "species": "shinigami",
                "role": "rival",
                "hair_color": "black",
                "traits": ["cold", "noble", "starts_as_enemy", "becomes_ally", "brother_figure"],
                "abilities": ["senbonzakura", "bankai"],
                "power_source": "reiatsu"
            },
            {
                "name": "Aizen Sosuke",
                "gender": "male",
                "species": "shinigami",
                "role": "antagonist",
                "hair_color": "brown",
                "traits": ["main_villain", "genius", "manipulative", "hidden_identity", "god_complex", "all_according_to_plan"],
                "abilities": ["kyoka_suigetsu", "hogyoku"],
                "power_source": "reiatsu"
            },
            {
                "name": "Kenpachi Zaraki",
                "gender": "male",
                "species": "shinigami",
                "role": "supporting",
                "traits": ["battle_maniac", "brutal", "no_technique", "pure_power", "eyepatch_limiter"],
                "abilities": ["raw_power", "bankai"],
                "power_source": "reiatsu"
            }
        ],
        "objects": [
            {
                "name": "Zanpakuto",
                "object_type": "weapon",
                "traits": ["soul_weapon", "unique_to_each", "has_spirit", "unlocks_power"],
                "plot_importance": "central"
            },
            {
                "name": "Hogyoku",
                "object_type": "artifact",
                "traits": ["macguffin", "grants_wishes", "plot_central", "villains_want_it"],
                "plot_importance": "central"
            }
        ],
        "arcs": [
            {
                "name": "Soul Society Arc",
                "arc_type": "rescue",
                "traits": ["rescue_mission", "infiltration", "enemy_base", "team_splits_up"],
                "themes": ["justice", "law_vs_morality"]
            },
            {
                "name": "Arrancar Arc",
                "arc_type": "war",
                "traits": ["invasion", "new_enemies", "power_ups"],
                "themes": ["war", "sacrifice"]
            },
            {
                "name": "Thousand Year Blood War",
                "arc_type": "war",
                "traits": ["world_destruction_threat", "final_arc", "all_heroes_unite", "deaths"],
                "themes": ["legacy", "balance"],
                "is_final_arc": True
            }
        ]
    },
    
    "attack_on_titan": {
        "title": "Attack on Titan",
        "category": "anime",
        "year": 2009,
        "genre": ["action", "dark_fantasy", "horror", "drama"],
        "themes": ["freedom", "war", "cycle_of_hatred", "sacrifice", "moral_ambiguity"],
        "setting": "Post-apocalyptic walled world",
        "power_system": "titan_shifting",
        "characters": [
            {
                "name": "Eren Yeager",
                "gender": "male",
                "age": "15-19",
                "species": "human_titan",
                "role": "protagonist",
                "hair_color": "brown",
                "family_status": "orphan",
                "traits": ["determined", "rage", "freedom_obsessed", "transforms", "hidden_power", "becomes_antagonist"],
                "dream": "Destroy all titans / See the ocean / Freedom",
                "abilities": ["attack_titan", "founding_titan", "war_hammer"],
                "power_source": "titan_power"
            },
            {
                "name": "Mikasa Ackerman",
                "gender": "female",
                "age": "15-19",
                "species": "human",
                "role": "deuteragonist",
                "hair_color": "black",
                "family_status": "orphan",
                "traits": ["stoic", "deadly", "protective", "loves_protagonist", "ackerman_strength", "scarf"],
                "abilities": ["superhuman_combat", "odm_master"],
                "power_source": "ackerman_blood"
            },
            {
                "name": "Armin Arlert",
                "gender": "male",
                "species": "human_titan",
                "role": "deuteragonist",
                "hair_color": "blonde",
                "traits": ["intelligent", "strategic", "cowardly_to_brave", "dreamer", "narrator"],
                "abilities": ["colossal_titan", "tactics"],
                "power_source": "titan_power"
            },
            {
                "name": "Levi Ackerman",
                "gender": "male",
                "species": "human",
                "role": "supporting",
                "hair_color": "black",
                "family_status": "orphan",
                "traits": ["strongest_soldier", "stoic", "clean_freak", "short", "tragic_past", "fan_favorite"],
                "abilities": ["superhuman_combat", "odm_master"],
                "power_source": "ackerman_blood"
            },
            {
                "name": "Erwin Smith",
                "gender": "male",
                "species": "human",
                "role": "mentor",
                "hair_color": "blonde",
                "traits": ["leader", "strategic", "sacrifices_soldiers", "charismatic", "mysterious_goal", "one_arm"],
                "abilities": ["leadership", "tactics"],
                "dream": "Prove father's theory"
            },
            {
                "name": "Reiner Braun",
                "gender": "male",
                "species": "human_titan",
                "role": "antagonist",
                "traits": ["traitor", "split_personality", "guilt", "warrior", "sympathetic_villain"],
                "abilities": ["armored_titan"],
                "power_source": "titan_power"
            },
            {
                "name": "Zeke Yeager",
                "gender": "male",
                "species": "human_titan",
                "role": "antagonist",
                "hair_color": "blonde",
                "family_status": "broken_family",
                "traits": ["antagonist", "genius", "nihilistic", "brother", "glasses", "monkey"],
                "abilities": ["beast_titan", "royal_blood"],
                "power_source": "titan_power"
            }
        ],
        "objects": [
            {
                "name": "ODM Gear",
                "object_type": "device",
                "traits": ["technical", "mobility", "essential_for_combat"],
                "plot_importance": "major"
            },
            {
                "name": "Founding Titan",
                "object_type": "power",
                "traits": ["ultimate_power", "memory_control", "requires_royal_blood"],
                "plot_importance": "central"
            }
        ],
        "arcs": [
            {
                "name": "Fall of Shiganshina",
                "arc_type": "tragedy",
                "traits": ["inciting_incident", "loss", "mystery"],
                "themes": ["loss", "survival"]
            },
            {
                "name": "Female Titan Arc",
                "arc_type": "mystery",
                "traits": ["traitor_reveal", "investigation"],
                "themes": ["trust", "betrayal"]
            },
            {
                "name": "Return to Shiganshina",
                "arc_type": "war",
                "traits": ["major_battle", "sacrifice", "truth_revealed"],
                "themes": ["sacrifice", "truth"]
            },
            {
                "name": "Rumbling",
                "arc_type": "war",
                "traits": ["world_destruction", "final_arc", "protagonist_is_villain", "moral_ambiguity"],
                "themes": ["genocide", "freedom", "cycle_of_hatred"],
                "is_final_arc": True
            }
        ]
    },
    
    "my_hero_academia": {
        "title": "My Hero Academia",
        "category": "anime",
        "year": 2014,
        "genre": ["action", "superhero", "school"],
        "themes": ["heroism", "hard_work", "legacy", "what_makes_a_hero"],
        "setting": "Superhero society",
        "power_system": "quirks",
        "characters": [
            {
                "name": "Izuku Midoriya",
                "gender": "male",
                "age": "14-16",
                "species": "human",
                "role": "protagonist",
                "hair_color": "green",
                "family_status": "single_parent",
                "traits": ["quirkless_to_powerful", "analytical", "crybaby", "determined", "fanboy", "inherits_power", "unusual_hair_color"],
                "dream": "Become greatest hero",
                "abilities": ["one_for_all", "multiple_quirks"],
                "power_source": "quirk"
            },
            {
                "name": "Katsuki Bakugo",
                "gender": "male",
                "species": "human",
                "role": "rival",
                "hair_color": "blonde",
                "traits": ["arrogant", "explosive_temper", "prodigy", "starts_as_bully", "becomes_ally", "inferiority_complex"],
                "abilities": ["explosion"],
                "power_source": "quirk"
            },
            {
                "name": "Ochaco Uraraka",
                "gender": "female",
                "species": "human",
                "role": "love_interest",
                "hair_color": "brown",
                "traits": ["cheerful", "kind", "loves_protagonist", "underrated", "money_motivated"],
                "abilities": ["zero_gravity"],
                "power_source": "quirk"
            },
            {
                "name": "Shoto Todoroki",
                "gender": "male",
                "species": "human",
                "role": "rival",
                "hair_color": "red_white",
                "family_status": "broken_family",
                "traits": ["stoic", "powerful", "daddy_issues", "unusual_hair_color", "dual_powers"],
                "abilities": ["half_cold_half_hot"],
                "power_source": "quirk"
            },
            {
                "name": "All Might",
                "gender": "male",
                "age": "adult",
                "species": "human",
                "role": "mentor",
                "hair_color": "blonde",
                "traits": ["symbol_of_peace", "mentor", "weakening", "inspiring", "appears_early", "gives_power", "secret_weakness"],
                "abilities": ["one_for_all"],
                "power_source": "quirk"
            },
            {
                "name": "Tomura Shigaraki",
                "gender": "male",
                "species": "human",
                "role": "antagonist",
                "hair_color": "light_blue",
                "family_status": "orphan",
                "traits": ["main_villain", "manchild", "destructive", "manipulated", "tragic_past", "grows_threatening"],
                "abilities": ["decay", "all_for_one"],
                "power_source": "quirk"
            },
            {
                "name": "All For One",
                "gender": "male",
                "age": "ancient",
                "species": "human",
                "role": "antagonist",
                "traits": ["true_villain", "manipulator", "ancient_evil", "connected_to_mentor", "steals_powers"],
                "abilities": ["all_for_one"],
                "power_source": "quirk"
            }
        ],
        "objects": [
            {
                "name": "One For All",
                "object_type": "power",
                "traits": ["inherited", "grows_stronger", "multiple_users", "central_to_plot"],
                "plot_importance": "central"
            },
            {
                "name": "Hero License",
                "object_type": "status",
                "traits": ["goal", "proof_of_hero"],
                "plot_importance": "major"
            }
        ],
        "arcs": [
            {
                "name": "U.A. Sports Festival",
                "arc_type": "tournament",
                "traits": ["tournament", "multiple_fighters", "reveals_characters", "broadcast"],
                "themes": ["competition", "proving_oneself"]
            },
            {
                "name": "Hero Killer Arc",
                "arc_type": "adventure",
                "traits": ["villain_introduction", "ideology_conflict"],
                "themes": ["true_heroism", "corruption"]
            },
            {
                "name": "Paranormal Liberation War",
                "arc_type": "war",
                "traits": ["major_battle", "deaths", "society_collapse"],
                "themes": ["sacrifice", "heroism"]
            }
        ]
    },
    
    "one_punch_man": {
        "title": "One Punch Man",
        "category": "anime",
        "year": 2009,
        "genre": ["action", "comedy", "parody", "superhero"],
        "themes": ["boredom", "meaning", "heroism", "power"],
        "setting": "Superhero world",
        "power_system": "various",
        "characters": [
            {
                "name": "Saitama",
                "gender": "male",
                "species": "human",
                "role": "protagonist",
                "traits": ["overpowered", "bored", "bald", "simple", "comedic", "one_punch", "unrecognized"],
                "dream": "Find worthy opponent",
                "abilities": ["unlimited_strength", "speed", "durability"],
                "power_source": "training"
            },
            {
                "name": "Genos",
                "gender": "male",
                "species": "cyborg",
                "role": "sidekick",
                "traits": ["serious", "loyal", "always_loses", "disciple", "cyborg"],
                "abilities": ["incinerate", "machine_gun_blows"],
                "power_source": "technology"
            },
            {
                "name": "King",
                "gender": "male",
                "species": "human",
                "role": "supporting",
                "traits": ["fraud", "lucky", "reputation", "comedic", "coward", "gamer"],
                "abilities": ["intimidation", "luck"]
            },
            {
                "name": "Garou",
                "gender": "male",
                "species": "human",
                "role": "antagonist",
                "traits": ["anti_villain", "martial_artist", "hero_hunter", "sympathetic", "monster_obsessed"],
                "abilities": ["martial_arts", "adaptation"],
                "power_source": "martial_arts"
            }
        ],
        "arcs": [
            {
                "name": "Hero Association Saga",
                "arc_type": "adventure",
                "traits": ["world_building", "comedic"],
                "themes": ["heroism", "recognition"]
            },
            {
                "name": "Monster Association Arc",
                "arc_type": "war",
                "traits": ["major_battle", "multiple_villains"],
                "themes": ["humanity", "monsters"]
            }
        ]
    },
    
    "fairy_tail": {
        "title": "Fairy Tail",
        "category": "anime",
        "year": 2006,
        "genre": ["action", "adventure", "fantasy", "comedy"],
        "themes": ["friendship", "family", "guild", "nakama_power"],
        "setting": "Magic World",
        "power_system": "magic",
        "characters": [
            {
                "name": "Natsu Dragneel",
                "gender": "male",
                "species": "human_dragon",
                "role": "protagonist",
                "hair_color": "pink",
                "family_status": "orphan",
                "traits": ["hot_headed", "loyal", "motion_sick", "fire_user", "raised_by_dragon", "unusual_hair_color", "hidden_power"],
                "dream": "Find Igneel",
                "abilities": ["fire_dragon_slayer", "dragon_force"],
                "power_source": "magic"
            },
            {
                "name": "Lucy Heartfilia",
                "gender": "female",
                "species": "human",
                "role": "deuteragonist",
                "hair_color": "blonde",
                "family_status": "orphan",
                "traits": ["celestial_mage", "kind", "runaway_rich", "fanservice", "narrator"],
                "abilities": ["celestial_spirits"],
                "power_source": "magic"
            },
            {
                "name": "Gray Fullbuster",
                "gender": "male",
                "species": "human",
                "role": "rival",
                "hair_color": "black",
                "traits": ["ice_user", "stripping_habit", "rivalry_with_natsu", "tragic_past"],
                "abilities": ["ice_make"],
                "power_source": "magic"
            },
            {
                "name": "Erza Scarlet",
                "gender": "female",
                "species": "human",
                "role": "deuteragonist",
                "hair_color": "red",
                "family_status": "orphan",
                "traits": ["strongest_female", "scary", "armor_mage", "cake_lover", "unusual_hair_color", "tragic_past"],
                "abilities": ["requip", "multiple_armors"],
                "power_source": "magic"
            },
            {
                "name": "Happy",
                "gender": "male",
                "species": "exceed",
                "role": "sidekick",
                "traits": ["animal_or_creature", "can_speak", "flying_cat", "comedic", "mascot", "aye"],
                "abilities": ["flight", "max_speed"],
                "power_source": "magic"
            },
            {
                "name": "Makarov Dreyar",
                "gender": "male",
                "age": "old",
                "species": "human",
                "role": "mentor",
                "traits": ["old", "wise", "guild_master", "grandfather_figure", "powerful", "perverted"],
                "abilities": ["giant", "fairy_law"],
                "power_source": "magic"
            },
            {
                "name": "Zeref",
                "gender": "male",
                "age": "ancient",
                "species": "human",
                "role": "antagonist",
                "hair_color": "black",
                "traits": ["main_villain", "immortal", "tragic", "connected_to_hero", "god_of_death"],
                "abilities": ["death_magic", "immortality"],
                "power_source": "magic"
            }
        ],
        "arcs": [
            {
                "name": "Grand Magic Games",
                "arc_type": "tournament",
                "traits": ["tournament", "guild_competition", "reveals_new_characters"],
                "themes": ["guild_pride", "competition"]
            },
            {
                "name": "Alvarez Empire Arc",
                "arc_type": "war",
                "traits": ["final_arc", "world_destruction_threat", "all_guilds_unite"],
                "themes": ["family", "sacrifice"],
                "is_final_arc": True
            }
        ]
    },
    
    "death_note": {
        "title": "Death Note",
        "category": "anime",
        "year": 2003,
        "genre": ["thriller", "psychological", "supernatural", "mystery"],
        "themes": ["justice", "morality", "power_corrupts", "god_complex"],
        "setting": "Modern Japan",
        "power_system": "death_note",
        "characters": [
            {
                "name": "Light Yagami",
                "gender": "male",
                "age": "17-23",
                "species": "human",
                "role": "protagonist",
                "hair_color": "brown",
                "family_status": "full_family",
                "traits": ["genius", "god_complex", "villain_protagonist", "manipulative", "handsome", "corrupted_by_power"],
                "dream": "Create new world as god",
                "abilities": ["death_note", "manipulation", "planning"],
                "power_source": "death_note"
            },
            {
                "name": "L",
                "gender": "male",
                "species": "human",
                "role": "rival",
                "hair_color": "black",
                "family_status": "orphan",
                "traits": ["genius", "eccentric", "detective", "sweet_tooth", "mysterious", "sits_weird"],
                "abilities": ["deduction", "investigation"],
                "power_source": "intellect"
            },
            {
                "name": "Misa Amane",
                "gender": "female",
                "species": "human",
                "role": "supporting",
                "hair_color": "blonde",
                "family_status": "orphan",
                "traits": ["obsessed_with_light", "second_kira", "goth", "model", "devoted"],
                "abilities": ["shinigami_eyes", "death_note"],
                "power_source": "death_note"
            },
            {
                "name": "Ryuk",
                "gender": "male",
                "species": "shinigami",
                "role": "supporting",
                "traits": ["death_god", "bored", "apple_obsessed", "observer", "comedic", "neutral"],
                "abilities": ["immortal", "invisible", "flight"]
            },
            {
                "name": "Near",
                "gender": "male",
                "species": "human",
                "role": "supporting",
                "hair_color": "white",
                "family_status": "orphan",
                "traits": ["L_successor", "genius", "toys", "emotionless"],
                "abilities": ["deduction"],
                "power_source": "intellect"
            }
        ],
        "objects": [
            {
                "name": "Death Note",
                "object_type": "artifact",
                "traits": ["central_to_plot", "kills", "rules", "supernatural", "corrupts"],
                "powers": ["write_name_to_kill"],
                "plot_importance": "central"
            }
        ],
        "arcs": [
            {
                "name": "L Arc",
                "arc_type": "cat_and_mouse",
                "traits": ["mind_games", "investigation", "hidden_identity"],
                "themes": ["justice", "morality"]
            },
            {
                "name": "Near and Mello Arc",
                "arc_type": "cat_and_mouse",
                "traits": ["final_confrontation", "successors"],
                "themes": ["legacy", "downfall"],
                "is_final_arc": True
            }
        ]
    },
    
    "fullmetal_alchemist": {
        "title": "Fullmetal Alchemist",
        "category": "anime",
        "year": 2001,
        "genre": ["action", "adventure", "fantasy", "drama"],
        "themes": ["equivalent_exchange", "sacrifice", "redemption", "brotherhood"],
        "setting": "Amestris",
        "power_system": "alchemy",
        "characters": [
            {
                "name": "Edward Elric",
                "gender": "male",
                "age": "15-16",
                "species": "human",
                "role": "protagonist",
                "hair_color": "blonde",
                "family_status": "orphan",
                "traits": ["short", "hot_headed", "genius_alchemist", "automail", "protective_brother", "atheist"],
                "dream": "Restore brother's body",
                "abilities": ["alchemy_without_circle", "automail_arm"],
                "power_source": "alchemy"
            },
            {
                "name": "Alphonse Elric",
                "gender": "male",
                "species": "human_soul",
                "role": "deuteragonist",
                "traits": ["armor_body", "kind", "cat_lover", "soulbound", "gentle"],
                "dream": "Get body back",
                "abilities": ["alchemy", "armor_body"],
                "power_source": "alchemy"
            },
            {
                "name": "Roy Mustang",
                "gender": "male",
                "species": "human",
                "role": "supporting",
                "hair_color": "black",
                "occupation": "Colonel",
                "traits": ["ambitious", "flame_alchemist", "womanizer", "war_guilt", "useless_in_rain"],
                "dream": "Become Fuhrer",
                "abilities": ["flame_alchemy"],
                "power_source": "alchemy"
            },
            {
                "name": "Winry Rockbell",
                "gender": "female",
                "species": "human",
                "role": "love_interest",
                "hair_color": "blonde",
                "family_status": "orphan",
                "traits": ["mechanic", "childhood_friend", "loves_protagonist", "wrench_violence"],
                "abilities": ["automail_engineering"]
            },
            {
                "name": "Scar",
                "gender": "male",
                "species": "human",
                "role": "antagonist",
                "traits": ["revenge", "anti_villain", "ishvalan", "becomes_ally", "destroys_alchemists"],
                "abilities": ["destruction_alchemy"],
                "power_source": "alchemy"
            },
            {
                "name": "Father",
                "gender": "male",
                "species": "homunculus",
                "role": "antagonist",
                "traits": ["main_villain", "god_complex", "created_homunculi", "ancient", "philosopher_stone"],
                "abilities": ["all_alchemy", "philosopher_stone"],
                "power_source": "philosopher_stone"
            }
        ],
        "objects": [
            {
                "name": "Philosopher's Stone",
                "object_type": "artifact",
                "traits": ["macguffin", "powered_by_souls", "amplifies_alchemy", "villains_want_it"],
                "plot_importance": "central"
            },
            {
                "name": "Automail",
                "object_type": "technology",
                "traits": ["prosthetic", "mechanical", "combat_capable"],
                "plot_importance": "major"
            }
        ],
        "arcs": [
            {
                "name": "Philosopher's Stone Hunt",
                "arc_type": "journey",
                "traits": ["journey", "investigation", "dark_discoveries"],
                "themes": ["equivalent_exchange", "morality"]
            },
            {
                "name": "Promised Day",
                "arc_type": "war",
                "traits": ["final_battle", "all_heroes_unite", "sacrifice"],
                "themes": ["sacrifice", "humanity"],
                "is_final_arc": True
            }
        ]
    }
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
    parser = argparse.ArgumentParser(description="AI-Assisted Story Data Generator")
    
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
        print("  python story_generator.py template naruto -o data/naruto.json")
        print("  python story_generator.py template bleach -o data/bleach.json")
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
