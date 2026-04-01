#!/usr/bin/env python3
"""
tools/scraper_html_fallback.py
------------------------------
CLI entry point for scraping story data using direct HTML parsing — a
resilient fallback for Fandom wikis that block the MediaWiki API.  All
scraping logic lives in the SBS package; this file contains only argument
parsing and command dispatch.

Use this scraper when scraper_api.py returns empty results or HTTP 403 errors
for a particular wiki.

Usage:
------
python tools/scraper_html_fallback.py fandom "naruto" -o data/naruto.json
python tools/scraper_html_fallback.py fandom "onepiece" --max-chars 30
python tools/scraper_html_fallback.py mal "Attack on Titan" -o data/aot.json
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any

# Ensure the project root is on the path when this script is run from tools/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from SBS.FandomScraperHTML import FandomScraperHTML, MAX_CHARACTERS_DEFAULT
from SBS.MALScraper import MALScraper
from SBS.ScrapedCharacter import ScrapedCharacter


def generate_story_json(
    info: Dict[str, Any],
    characters: List[ScrapedCharacter],
    output_path: str
) -> dict:
    """
    Build and save a story JSON file from scraped data.

    Converts scraped character objects to the canonical story JSON schema
    expected by the Narrative Pattern Analyzer, then writes the result to
    disk.  Creates parent directories if they do not exist.

    Args:
        info:        Story metadata dictionary (title, category, genre, etc.).
        characters:  List of ScrapedCharacter instances.
        output_path: Destination file path for the output JSON.

    Returns:
        The story dictionary that was written to disk.
    """
    story = {
        "title": info.get("title", "Unknown"),
        "category": info.get("category", "anime"),
        "year": info.get("year"),
        "genre": info.get("genre", []),
        "themes": info.get("themes", []),
        "setting": info.get("setting", ""),
        "power_system": info.get("power_system", ""),
        "has_generations": False,
        "characters": [c.to_dict() for c in characters],
        "objects": [],
        "arcs": [],
        "metadata": {
            "auto_generated": True,
            "source": info.get("source", "wiki"),
            "character_count": len(characters),
        }
    }

    # Inject story title into each character dict
    for char in story["characters"]:
        char["story"] = story["title"]

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(story, f, indent=2, ensure_ascii=False)

    print(f"\nStory saved to: {output_path}")
    return story


def cmd_fandom(args):
    """
    Handle the 'fandom' sub-command: scrape characters using HTML parsing.

    Args:
        args: Parsed argument namespace from argparse.

    Returns:
        0 on success, 1 on failure.
    """
    scraper = FandomScraperHTML(args.wiki)

    info = scraper.get_story_info()
    info["source"] = f"{args.wiki}.fandom.com"

    print(f"\n{'=' * 60}")
    print(f"Scraping: {info['title']}")
    print(f"Wiki: {scraper.base_url}")
    print(f"Category: {args.category}")
    print(f"Max characters: {args.max_chars}")
    print(f"{'=' * 60}")

    characters = scraper.scrape_characters(
        category=args.category,
        max_chars=args.max_chars
    )

    if not characters:
        print("\nNo characters found. The wiki might have different category names.")
        print("Try these categories: 'Characters', 'Main_Characters', 'Protagonists'")
        return 1

    output_path = args.output or f"{args.wiki}_story.json"
    generate_story_json(info, characters, output_path)

    print(f"\n{'=' * 60}")
    print("SCRAPING COMPLETE")
    print(f"{'=' * 60}")
    print(f"Characters scraped: {len(characters)}")
    print(f"Output: {output_path}")

    all_traits = []
    for c in characters:
        all_traits.extend(c.traits)

    if all_traits:
        trait_counts: Dict[str, int] = {}
        for t in all_traits:
            trait_counts[t] = trait_counts.get(t, 0) + 1
        print("\nDetected traits:")
        for trait, count in sorted(trait_counts.items(), key=lambda x: -x[1])[:10]:
            print(f"  {trait}: {count}")

    roles: Dict[str, int] = {}
    for c in characters:
        roles[c.role] = roles.get(c.role, 0) + 1
    print("\nRoles detected:")
    for role, count in sorted(roles.items(), key=lambda x: -x[1]):
        print(f"  {role}: {count}")

    return 0


def cmd_mal(args):
    """
    Handle the 'mal' sub-command: scrape anime info and characters from MAL.

    Args:
        args: Parsed argument namespace from argparse.

    Returns:
        0 on success, 1 on failure.
    """
    scraper = MALScraper()
    info, characters = scraper.scrape_anime(args.query, args.max_chars)

    if not characters:
        print("Failed to scrape anime")
        return 1

    info["source"] = "MyAnimeList"
    output_path = args.output or f"{args.query.lower().replace(' ', '_')}_story.json"
    generate_story_json(info, characters, output_path)

    print(f"\nCharacters scraped: {len(characters)}")
    print(f"Output: {output_path}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Story Data Scraper (HTML fallback) — for wikis that block the API",
    )

    subparsers = parser.add_subparsers(dest="command", help="Scraper source")

    fandom_parser = subparsers.add_parser("fandom", help="Scrape a Fandom wiki via HTML")
    fandom_parser.add_argument("wiki", help="Wiki name (e.g. 'naruto', 'onepiece')")
    fandom_parser.add_argument("-c", "--category", default="Characters",
                               help="Category to scrape (default: Characters)")
    fandom_parser.add_argument("-m", "--max-chars", type=int, default=MAX_CHARACTERS_DEFAULT,
                               help=f"Maximum characters (default: {MAX_CHARACTERS_DEFAULT})")
    fandom_parser.add_argument("-o", "--output", help="Output JSON file")

    mal_parser = subparsers.add_parser("mal", help="Scrape from MyAnimeList")
    mal_parser.add_argument("query", help="Anime title to search")
    mal_parser.add_argument("-m", "--max-chars", type=int, default=MAX_CHARACTERS_DEFAULT,
                            help=f"Maximum characters (default: {MAX_CHARACTERS_DEFAULT})")
    mal_parser.add_argument("-o", "--output", help="Output JSON file")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        print("\nExamples:")
        print("  python tools/scraper_html_fallback.py fandom naruto -o data/naruto.json")
        print("  python tools/scraper_html_fallback.py fandom onepiece --max-chars 30")
        print("  python tools/scraper_html_fallback.py mal 'Attack on Titan' -o data/aot.json")
        return 1

    commands = {"fandom": cmd_fandom, "mal": cmd_mal}
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
