"""
CharacterRole.py
----------------
Defines the CharacterRole enumeration used throughout the Narrative Pattern
Analyzer to classify a character's narrative function within their story.
"""

from enum import Enum


class CharacterRole(Enum):
    """
    Enumeration of canonical narrative roles a character can hold.

    Assigning roles from a fixed vocabulary allows the pattern-matching engine
    to compare character functions across different stories reliably.  Each
    value corresponds to a well-established storytelling archetype so that
    trope detection logic can reference role names without hard-coding raw
    strings.

    Values:
        PROTAGONIST:    The primary main character the story follows.
        DEUTERAGONIST:  The secondary main character who shares significant
                        screen or page time with the protagonist.
        ANTAGONIST:     The primary opposing force or villain.
        MENTOR:         A wise or experienced guide who aids the protagonist.
        SIDEKICK:       A loyal companion who supports the protagonist.
        RIVAL:          A recurring opponent who often challenges the hero.
        LOVE_INTEREST:  A character with a romantic connection to a lead.
        COMIC_RELIEF:   A character whose primary function is humor.
        SUPPORTING:     A secondary character without a more specific role.
        MINOR:          A background or one-off character.
    """

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
