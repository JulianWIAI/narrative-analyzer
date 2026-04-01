"""
SBS (Story Building System) — Package Initialisation
-----------------------------------------------------
Central import hub for all Narrative Pattern Analyzer components.

Importing from this package gives access to every class in the system without
needing to know the exact sub-module it lives in:

    from SBS import Character, PatternMatcher, ReportGenerator

All public classes are re-exported here so that external modules can use
either the short ``from SBS import X`` form or the explicit
``from SBS.X import X`` form interchangeably.
"""

# ---------------------------------------------------------------------------
# Data model — enumerations
# ---------------------------------------------------------------------------
from SBS.Gender import Gender
from SBS.CharacterRole import CharacterRole
from SBS.StoryCategory import StoryCategory

# ---------------------------------------------------------------------------
# Data model — story entities
# ---------------------------------------------------------------------------
from SBS.Character import Character
from SBS.StoryObject import StoryObject
from SBS.PlotArc import PlotArc
from SBS.Story import Story
from SBS.StoryCollection import StoryCollection

# ---------------------------------------------------------------------------
# Pattern matching — result types
# ---------------------------------------------------------------------------
from SBS.TropeMatch import TropeMatch
from SBS.SimilarityMatch import SimilarityMatch
from SBS.DiscoveredPattern import DiscoveredPattern

# ---------------------------------------------------------------------------
# Pattern matching — engines
# ---------------------------------------------------------------------------
from SBS.PatternMatcher import PatternMatcher
from SBS.ArchetypeMatcher import ArchetypeMatcher

# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
from SBS.ReportGenerator import ReportGenerator

# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------
from SBS.NarrativeAnalyzerGUI import NarrativeAnalyzerGUI

# ---------------------------------------------------------------------------
# Scrapers
# ---------------------------------------------------------------------------
from SBS.ScrapedCharacter import ScrapedCharacter
from SBS.FandomScraper import FandomScraper
from SBS.FandomScraperHTML import FandomScraperHTML
from SBS.MALScraper import MALScraper

__all__ = [
    # Enums
    "Gender",
    "CharacterRole",
    "StoryCategory",
    # Story entities
    "Character",
    "StoryObject",
    "PlotArc",
    "Story",
    "StoryCollection",
    # Match result types
    "TropeMatch",
    "SimilarityMatch",
    "DiscoveredPattern",
    # Engines
    "PatternMatcher",
    "ArchetypeMatcher",
    # Report
    "ReportGenerator",
    # GUI
    "NarrativeAnalyzerGUI",
    # Scrapers
    "ScrapedCharacter",
    "FandomScraper",
    "FandomScraperHTML",
    "MALScraper",
]
