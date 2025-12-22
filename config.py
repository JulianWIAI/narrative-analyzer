"""
Narrative Pattern Analyzer - Configuration & Trope Definitions

This file contains:
- Known story tropes and patterns
- Character archetype definitions
- Plot element categories
- Matching rules and weights
"""

# ============================================================================
# KNOWN TROPES - Predefined patterns found across stories
# ============================================================================

KNOWN_TROPES = {
    # Character-based tropes
    "colorful_hair_treasure_woman": {
        "name": "Colorful Hair Treasure Woman",
        "description": "A female character with unusual/colorful hair who is associated with treasure, money, or valuable items",
        "category": "character",
        "required_traits": ["female", "unusual_hair_color"],
        "associated_traits": ["loves_money", "treasure_hunter", "navigator", "smart", "technical"],
        "examples": ["Nami (One Piece)", "Bulma (Dragon Ball)"],
        "weight": 0.8
    },
    
    "broken_family_hero": {
        "name": "Broken Family Hero",
        "description": "The main protagonist has missing, dead, or absent parents/family",
        "category": "character",
        "required_traits": ["protagonist", "orphan_or_absent_parent"],
        "associated_traits": ["raised_by_relative", "raised_by_mentor", "seeks_family", "lonely_childhood"],
        "examples": ["Ash Ketchum", "Goku", "Luffy", "Naruto", "Harry Potter", "Batman"],
        "weight": 0.9
    },
    
    "elderly_mentor": {
        "name": "Elderly Mentor at Start",
        "description": "An old, wise character who guides the hero at the beginning of their journey",
        "category": "character",
        "required_traits": ["old", "mentor", "appears_early"],
        "associated_traits": ["wise", "powerful", "mysterious_past", "teaches_protagonist", "grandfather_figure"],
        "examples": ["Professor Oak", "Grandpa Gohan", "Dumbledore", "Gandalf", "Master Roshi"],
        "weight": 0.85
    },
    
    "talking_animal_companion": {
        "name": "Talking Animal Companion",
        "description": "An animal or creature that can speak and accompanies the main characters",
        "category": "character",
        "required_traits": ["animal_or_creature", "can_speak"],
        "associated_traits": ["comic_relief", "loyal", "small", "mascot", "unique_among_species"],
        "examples": ["Meowth", "Chopper", "Pikachu", "Happy (Fairy Tail)", "Morgana (Persona 5)"],
        "weight": 0.75
    },
    
    "rival_friend": {
        "name": "Rival Who Becomes Friend",
        "description": "A character who starts as antagonist/rival but becomes ally",
        "category": "character",
        "required_traits": ["starts_as_rival", "becomes_ally"],
        "associated_traits": ["proud", "skilled", "similar_age_to_hero", "competitive", "redemption_arc"],
        "examples": ["Gary Oak/Blue", "Vegeta", "Sasuke", "Kaiba"],
        "weight": 0.8
    },
    
    "gentle_giant": {
        "name": "Gentle Giant",
        "description": "A physically large/strong character who is kind and protective",
        "category": "character",
        "required_traits": ["large_or_strong", "kind_personality"],
        "associated_traits": ["protective", "simple_minded", "loves_food", "loyal", "scary_appearance"],
        "examples": ["Hagrid", "Chopper (monster form)", "Buu (good)", "Franky"],
        "weight": 0.7
    },
    
    "mysterious_antagonist": {
        "name": "Mysterious Main Antagonist",
        "description": "The main villain whose true identity, motives, or power is hidden initially",
        "category": "character",
        "required_traits": ["antagonist", "mysterious"],
        "associated_traits": ["hidden_identity", "grand_plan", "connected_to_hero", "appears_late"],
        "examples": ["Voldemort", "Madara", "Blackbeard", "Giovanni"],
        "weight": 0.8
    },
    
    # Object/Item-based tropes
    "macguffin_device": {
        "name": "Technical MacGuffin Device",
        "description": "A special device or tool that drives the plot or is essential for the journey",
        "category": "object",
        "required_traits": ["device_or_tool", "plot_essential"],
        "associated_traits": ["unique", "technical", "guides_journey", "given_by_mentor", "upgradeable"],
        "examples": ["Pokédex", "Dragon Radar", "Log Pose", "Millennium Puzzle", "Death Note"],
        "weight": 0.85
    },
    
    "collectible_power_items": {
        "name": "Collectible Power Items",
        "description": "A set of items that must be collected, each granting power or progress",
        "category": "object",
        "required_traits": ["collectible", "set_of_items", "grants_power_or_progress"],
        "associated_traits": ["scattered", "numbered", "villains_want_them", "final_wish_or_power"],
        "examples": ["Dragon Balls", "Gym Badges", "Chaos Emeralds", "Infinity Stones", "Horcruxes"],
        "weight": 0.9
    },
    
    "inherited_item": {
        "name": "Inherited Special Item",
        "description": "A powerful item passed down from parent/predecessor to the hero",
        "category": "object",
        "required_traits": ["inherited", "special_power"],
        "associated_traits": ["from_parent", "unique", "symbol_of_legacy", "unlocks_potential"],
        "examples": ["Straw Hat", "Goku's Power Pole", "Harry's Cloak", "Luffy's Hat"],
        "weight": 0.75
    },
    
    # Plot-based tropes
    "tournament_arc": {
        "name": "Tournament Arc",
        "description": "A story arc centered around a competition or tournament",
        "category": "plot",
        "required_traits": ["competition", "multiple_fighters"],
        "associated_traits": ["bracket_style", "reveals_new_characters", "power_showcase", "interrupted_by_villain"],
        "examples": ["Pokémon League", "World Martial Arts Tournament", "Chunin Exams", "U.A. Sports Festival"],
        "weight": 0.85
    },
    
    "training_arc": {
        "name": "Training Arc",
        "description": "A period where the hero trains to become stronger",
        "category": "plot",
        "required_traits": ["training", "power_increase"],
        "associated_traits": ["time_skip", "new_mentor", "harsh_conditions", "new_technique_learned"],
        "examples": ["Hyperbolic Time Chamber", "Sage Training", "Time Skip training"],
        "weight": 0.8
    },
    
    "rescue_arc": {
        "name": "Rescue Arc",
        "description": "The heroes must rescue a captured teammate or friend",
        "category": "plot",
        "required_traits": ["teammate_captured", "rescue_mission"],
        "associated_traits": ["infiltration", "enemy_base", "team_splits_up", "power_of_friendship"],
        "examples": ["Enies Lobby", "Sasuke Retrieval", "Rescue Rukia"],
        "weight": 0.8
    },
    
    "world_ending_threat": {
        "name": "World-Ending Threat",
        "description": "A villain or event that threatens to destroy the world",
        "category": "plot",
        "required_traits": ["world_destruction_threat"],
        "associated_traits": ["final_arc", "all_heroes_unite", "sacrifice", "new_power_unlocked"],
        "examples": ["Buu Saga", "Fourth Shinobi War", "Marineford"],
        "weight": 0.85
    },
    
    "journey_quest": {
        "name": "Journey/Quest Structure",
        "description": "The story follows a journey to reach a destination or find something",
        "category": "plot",
        "required_traits": ["journey", "destination_goal"],
        "associated_traits": ["companions_join", "episodic_locations", "grow_stronger_on_way"],
        "examples": ["Pokémon Journey", "Finding One Piece", "Finding Dragon Balls", "Lord of the Rings"],
        "weight": 0.9
    },
    
    # Theme-based tropes
    "power_of_friendship": {
        "name": "Power of Friendship",
        "description": "Characters gain strength or win through bonds with friends",
        "category": "theme",
        "required_traits": ["friendship_empowers"],
        "associated_traits": ["team_attacks", "emotional_moments", "flashbacks_to_bonds", "never_give_up"],
        "examples": ["Fairy Tail", "One Piece", "Naruto", "My Hero Academia"],
        "weight": 0.8
    },
    
    "hidden_potential": {
        "name": "Hidden Potential/Chosen One",
        "description": "The hero has hidden powers or is destined for greatness",
        "category": "theme",
        "required_traits": ["hidden_power", "special_destiny"],
        "associated_traits": ["unknown_heritage", "prophecy", "unlocks_in_crisis", "surpasses_limits"],
        "examples": ["Goku (Saiyan)", "Naruto (Nine-Tails)", "Luffy (inherited will)", "Harry Potter"],
        "weight": 0.85
    },
    
    "dream_goal": {
        "name": "Character Dream/Goal",
        "description": "Each main character has a clearly stated dream or life goal",
        "category": "theme",
        "required_traits": ["stated_dream"],
        "associated_traits": ["motivates_actions", "shared_with_team", "symbolic"],
        "examples": ["Pirate King", "Pokémon Master", "Hokage", "World's Greatest Swordsman"],
        "weight": 0.9
    },
    
    # Structure-based tropes
    "team_composition": {
        "name": "Classic Team Composition",
        "description": "The main group follows a classic team structure with defined roles",
        "category": "structure",
        "required_traits": ["team", "defined_roles"],
        "associated_traits": ["leader", "smart_one", "strong_one", "comic_relief", "female_member"],
        "examples": ["Straw Hat Crew", "Z Fighters", "Team 7", "Pokémon Trainers"],
        "weight": 0.75
    },
    
    "generation_system": {
        "name": "Generation/Era System",
        "description": "The story world is divided into generations, eras, or versions",
        "category": "structure",
        "required_traits": ["multiple_generations"],
        "associated_traits": ["legacy_characters", "new_protagonist_per_gen", "callbacks"],
        "examples": ["Pokémon Generations", "JoJo Parts", "Avatar Cycles", "Gundam Series"],
        "weight": 0.7
    },
}

# ============================================================================
# CHARACTER ARCHETYPES - Common character types
# ============================================================================

CHARACTER_ARCHETYPES = {
    "the_hero": {
        "name": "The Hero/Protagonist",
        "traits": ["brave", "determined", "grows_stronger", "protects_others", "never_gives_up"],
        "common_backgrounds": ["orphan", "humble_origins", "hidden_heritage"],
    },
    "the_mentor": {
        "name": "The Mentor",
        "traits": ["wise", "old", "powerful", "teaches_hero", "mysterious_past"],
        "common_backgrounds": ["former_hero", "retired_legend", "guardian"],
    },
    "the_rival": {
        "name": "The Rival",
        "traits": ["competitive", "skilled", "proud", "similar_to_hero"],
        "common_backgrounds": ["privileged", "prodigy", "dark_past"],
    },
    "the_sidekick": {
        "name": "The Sidekick/Best Friend",
        "traits": ["loyal", "supportive", "comic_relief", "brave_when_needed"],
        "common_backgrounds": ["childhood_friend", "first_ally", "rescued_by_hero"],
    },
    "the_love_interest": {
        "name": "The Love Interest",
        "traits": ["attractive", "capable", "supports_hero", "has_own_goals"],
        "common_backgrounds": ["princess", "fellow_fighter", "childhood_friend"],
    },
    "the_trickster": {
        "name": "The Trickster",
        "traits": ["cunning", "unpredictable", "morally_grey", "comic_relief"],
        "common_backgrounds": ["thief", "con_artist", "reformed_villain"],
    },
    "the_big_bad": {
        "name": "The Main Villain",
        "traits": ["powerful", "ambitious", "cruel", "connected_to_hero"],
        "common_backgrounds": ["fallen_hero", "ancient_evil", "corrupted_by_power"],
    },
}

# ============================================================================
# TRAIT SYNONYMS - For flexible matching
# ============================================================================

TRAIT_SYNONYMS = {
    # Family status
    "orphan_or_absent_parent": ["orphan", "no_parents", "absent_father", "absent_mother", "dead_parents", 
                                 "abandoned", "raised_by_other", "missing_parents", "unknown_parents"],
    
    # Hair colors
    "unusual_hair_color": ["blue_hair", "pink_hair", "green_hair", "purple_hair", "orange_hair", 
                          "red_hair", "white_hair", "colorful_hair", "bright_hair"],
    
    # Personality
    "kind_personality": ["kind", "gentle", "caring", "compassionate", "friendly", "warm", "loving"],
    "proud": ["proud", "arrogant", "confident", "cocky", "boastful"],
    
    # Physical
    "large_or_strong": ["large", "tall", "muscular", "giant", "big", "strong", "powerful_build"],
    "small": ["small", "tiny", "short", "petite", "compact"],
    
    # Role
    "protagonist": ["protagonist", "main_character", "hero", "mc", "lead"],
    "antagonist": ["antagonist", "villain", "enemy", "bad_guy", "evil"],
    "mentor": ["mentor", "teacher", "master", "sensei", "guide", "trainer"],
    
    # Story position
    "appears_early": ["appears_early", "first_episode", "beginning", "start", "intro"],
    "appears_late": ["appears_late", "revealed_later", "final_arc", "end_game"],
    
    # Animal
    "animal_or_creature": ["animal", "creature", "pet", "monster", "beast", "mascot"],
    "can_speak": ["can_speak", "talks", "speaking", "verbal", "communicates"],
    
    # Relationships
    "starts_as_rival": ["starts_as_rival", "initial_enemy", "first_opponent", "competitor"],
    "becomes_ally": ["becomes_ally", "joins_team", "redemption", "turns_good", "befriends_hero"],
}

# ============================================================================
# PLOT ELEMENTS - Story structure components
# ============================================================================

PLOT_ELEMENTS = {
    "inciting_incident": {
        "description": "The event that starts the hero's journey",
        "common_types": ["receives_item", "meets_mentor", "discovers_power", "tragedy", "called_to_action"]
    },
    "first_ally": {
        "description": "The first companion to join the hero",
        "common_types": ["childhood_friend", "rescued_character", "rival_turned_friend", "mentor_figure"]
    },
    "first_villain": {
        "description": "The first antagonist encountered",
        "common_types": ["minor_villain", "rival", "monster", "organization_grunt"]
    },
    "power_system": {
        "description": "How powers/abilities work in this world",
        "common_types": ["magic", "ki/chakra", "technology", "creatures", "mutations", "items"]
    },
    "goal_introduction": {
        "description": "When the main goal is established",
        "common_types": ["stated_dream", "inherited_mission", "revenge", "protection", "discovery"]
    },
}

# ============================================================================
# SIMILARITY WEIGHTS - How much each match type contributes
# ============================================================================

SIMILARITY_WEIGHTS = {
    "exact_trait_match": 1.0,
    "synonym_match": 0.8,
    "category_match": 0.6,
    "archetype_match": 0.7,
    "plot_element_match": 0.75,
    "theme_match": 0.65,
}

# ============================================================================
# OUTPUT SETTINGS
# ============================================================================

OUTPUT_SETTINGS = {
    "min_similarity_score": 0.3,  # Minimum score to report a match
    "max_results_per_trope": 10,  # Maximum examples per trope
    "report_format": "detailed",   # "simple" or "detailed"
}
