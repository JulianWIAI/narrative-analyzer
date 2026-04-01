#!/usr/bin/env python3
"""
tools/scraper_api.py
--------------------
CLI entry point for scraping story data from Fandom wikis (via the MediaWiki
API) and MyAnimeList (via the Jikan API).  All scraping logic lives in the
SBS package; this file contains only argument parsing and command dispatch.

Usage:
------
python tools/scraper_api.py fandom "onepiece" -o data/onepiece.json
python tools/scraper_api.py fandom "naruto" --list-categories
python tools/scraper_api.py mal "Attack on Titan" -o data/aot.json
python tools/scraper_api.py batch wikis.txt -o scraped_stories/
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any

# Ensure the project root is on the path when this script is run from tools/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from SBS.FandomScraper import FandomScraper, MAX_CHARACTERS_DEFAULT
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
    disk.

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

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(story, f, indent=2, ensure_ascii=False)

    print(f"\nStory saved to: {output_path}")
    return story


def cmd_fandom(args):
    """
    Handle the 'fandom' sub-command: scrape characters from a Fandom wiki.

    Args:
        args: Parsed argument namespace from argparse.

    Returns:
        0 on success, 1 on failure.
    """
    scraper = FandomScraper(args.wiki)

    if args.list_categories:
        print(f"Categories on {args.wiki}.fandom.com:\n")
        for cat in scraper.list_categories():
            print(f"  - {cat}")
        return 0

    info = scraper.get_story_info()
    info["source"] = f"{args.wiki}.fandom.com"

    print(f"\nScraping: {info['title']}")
    print(f"Wiki: {scraper.base_url}")
    print(f"Category: {args.category}")
    print(f"Max characters: {args.max_chars}")
    print("-" * 50)

    characters = scraper.scrape_characters(
        category=args.category,
        max_chars=args.max_chars
    )

    if not characters:
        print("No characters found. Try --list-categories to see available categories.")
        return 1

    output_path = args.output or f"{args.wiki}_story.json"
    generate_story_json(info, characters, output_path)

    print(f"\n{'=' * 50}")
    print("SCRAPING COMPLETE")
    print(f"{'=' * 50}")
    print(f"Characters scraped: {len(characters)}")
    print(f"Output: {output_path}")

    all_traits = []
    for c in characters:
        all_traits.extend(c.traits)
    trait_counts: Dict[str, int] = {}
    for t in all_traits:
        trait_counts[t] = trait_counts.get(t, 0) + 1

    if trait_counts:
        print("\nDetected traits:")
        for trait, count in sorted(trait_counts.items(), key=lambda x: -x[1])[:10]:
            print(f"  {trait}: {count}")

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


def cmd_batch(args):
    """
    Handle the 'batch' sub-command: scrape multiple wikis from a text file.

    Each non-comment line in the file should be:
        wiki_name[, category]

    Args:
        args: Parsed argument namespace from argparse.

    Returns:
        0 on completion.
    """
    wikis = []
    with open(args.file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split(',')
                wiki_name = parts[0].strip()
                category = parts[1].strip() if len(parts) > 1 else "Characters"
                wikis.append((wiki_name, category))

    print(f"Batch scraping {len(wikis)} wikis...")

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for wiki_name, category in wikis:
        print(f"\n{'=' * 50}")
        print(f"Scraping: {wiki_name}")
        print(f"{'=' * 50}")

        try:
            scraper = FandomScraper(wiki_name)
            info = scraper.get_story_info()
            info["source"] = f"{wiki_name}.fandom.com"

            characters = scraper.scrape_characters(
                category=category,
                max_chars=args.max_chars
            )

            if characters:
                output_path = str(output_dir / f"{wiki_name}.json")
                generate_story_json(info, characters, output_path)
        except Exception as e:
            print(f"Error scraping {wiki_name}: {e}")

        time.sleep(2)

    print(f"\nBatch complete! Output in: {output_dir}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Story Data Scraper (API) — generate story JSON from Fandom wikis and MAL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Scraper source")

    fandom_parser = subparsers.add_parser("fandom", help="Scrape from a Fandom wiki")
    fandom_parser.add_argument("wiki", help="Wiki name (e.g. 'onepiece', 'naruto')")
    fandom_parser.add_argument("-c", "--category", default="Characters",
                               help="Category to scrape (default: Characters)")
    fandom_parser.add_argument("-m", "--max-chars", type=int, default=MAX_CHARACTERS_DEFAULT,
                               help=f"Maximum characters (default: {MAX_CHARACTERS_DEFAULT})")
    fandom_parser.add_argument("-o", "--output", help="Output JSON file")
    fandom_parser.add_argument("--list-categories", action="store_true",
                               help="List available categories and exit")

    mal_parser = subparsers.add_parser("mal", help="Scrape from MyAnimeList")
    mal_parser.add_argument("query", help="Anime title to search")
    mal_parser.add_argument("-m", "--max-chars", type=int, default=MAX_CHARACTERS_DEFAULT,
                            help=f"Maximum characters (default: {MAX_CHARACTERS_DEFAULT})")
    mal_parser.add_argument("-o", "--output", help="Output JSON file")

    batch_parser = subparsers.add_parser("batch", help="Batch scrape multiple wikis")
    batch_parser.add_argument("file", help="Text file with wiki names (one per line)")
    batch_parser.add_argument("-o", "--output-dir", default="scraped_stories",
                              help="Output directory (default: scraped_stories)")
    batch_parser.add_argument("-m", "--max-chars", type=int, default=50,
                              help="Max characters per wiki (default: 50)")

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        print("\nExamples:")
        print("  python tools/scraper_api.py fandom onepiece -o data/onepiece.json")
        print("  python tools/scraper_api.py fandom naruto --list-categories")
        print("  python tools/scraper_api.py mal 'Attack on Titan' -o data/aot.json")
        print("  python tools/scraper_api.py batch wikis.txt -o scraped_stories/")
        return 1

    commands = {
        "fandom": cmd_fandom,
        "mal": cmd_mal,
        "batch": cmd_batch,
    }
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
