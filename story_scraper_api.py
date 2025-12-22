#!/usr/bin/env python3
"""
Story Data Scraper - Auto-generate story JSON from wikis

Scrapes character and plot information from Fandom wikis and other sources
to automatically create JSON files for the Narrative Pattern Analyzer.

Supported sources:
- Fandom wikis (any wiki on fandom.com)
- Wikipedia (basic info)
- MyAnimeList (via Jikan API - no key needed)

Usage:
------
# Scrape from a Fandom wiki
python story_scraper.py fandom "onepiece" -o onepiece.json

# Scrape from MyAnimeList
python story_scraper.py mal "One Piece" -o onepiece.json

# Scrape with character limit
python story_scraper.py fandom "naruto" --max-chars 50 -o naruto.json

# List available categories on a wiki
python story_scraper.py fandom "dragonball" --list-categories
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import quote, urljoin
from dataclasses import dataclass, field
import requests
from bs4 import BeautifulSoup

# Configuration
DELAY_BETWEEN_REQUESTS = 0.5
MAX_CHARACTERS_DEFAULT = 100
MAX_RETRIES = 3

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# Trait detection keywords
TRAIT_KEYWORDS = {
    # Personality
    "brave": ["brave", "courageous", "fearless", "heroic"],
    "kind": ["kind", "caring", "gentle", "compassionate", "friendly"],
    "determined": ["determined", "persistent", "never gives up", "willpower"],
    "intelligent": ["intelligent", "smart", "genius", "brilliant", "clever"],
    "loyal": ["loyal", "faithful", "devoted"],
    "arrogant": ["arrogant", "proud", "cocky", "overconfident"],
    "naive": ["naive", "innocent", "simple", "gullible"],
    "hot_headed": ["hot-headed", "short-tempered", "angry", "temper"],
    "calm": ["calm", "composed", "cool", "collected"],
    "comedic": ["comedic", "funny", "comic relief", "humorous"],
    
    # Role indicators
    "protagonist": ["protagonist", "main character", "hero", "heroine"],
    "antagonist": ["antagonist", "villain", "enemy", "evil"],
    "mentor": ["mentor", "teacher", "master", "sensei", "trains"],
    "rival": ["rival", "competitor", "nemesis"],
    
    # Background
    "orphan": ["orphan", "parents died", "no parents", "lost parents", "raised by"],
    "royalty": ["prince", "princess", "king", "queen", "royal"],
    "wealthy": ["rich", "wealthy", "billionaire", "fortune"],
    "poor": ["poor", "poverty", "humble origins"],
    
    # Physical
    "tall": ["tall", "towering", "giant"],
    "short": ["short", "small", "petite", "tiny"],
    "muscular": ["muscular", "strong", "buff", "powerful build"],
    
    # Special
    "hidden_power": ["hidden power", "latent", "dormant", "awakens", "unlocks"],
    "transforms": ["transform", "transformation", "forms", "evolve"],
}

# Role detection patterns
ROLE_PATTERNS = {
    "protagonist": [
        r"main\s*(character|protagonist)",
        r"is\s*the\s*(hero|protagonist)",
        r"series\s*follows",
        r"story\s*centers\s*on",
    ],
    "antagonist": [
        r"main\s*(villain|antagonist|enemy)",
        r"is\s*the\s*(villain|antagonist)",
        r"arch[\s-]?enemy",
        r"primary\s*antagonist",
    ],
    "mentor": [
        r"mentor",
        r"teaches?\s*(the\s*)?(protagonist|hero|main)",
        r"trains?\s*(the\s*)?(protagonist|hero|main)",
        r"master\s*of",
    ],
    "rival": [
        r"rival",
        r"competes?\s*with",
        r"nemesis",
    ],
    "sidekick": [
        r"sidekick",
        r"companion",
        r"best\s*friend",
        r"partner",
        r"travels?\s*with",
    ],
}


@dataclass
class ScrapedCharacter:
    """Scraped character data."""
    name: str
    url: str
    description: str = ""
    gender: str = "unknown"
    species: str = "human"
    role: str = "supporting"
    traits: List[str] = field(default_factory=list)
    abilities: List[str] = field(default_factory=list)
    affiliations: List[str] = field(default_factory=list)
    family_status: Optional[str] = None
    hair_color: Optional[str] = None
    occupation: Optional[str] = None
    first_appearance: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "gender": self.gender,
            "species": self.species,
            "role": self.role,
            "traits": self.traits,
            "abilities": self.abilities,
            "family_status": self.family_status,
            "hair_color": self.hair_color,
            "occupation": self.occupation,
            "metadata": {
                "source_url": self.url,
                "affiliations": self.affiliations,
            }
        }


class FandomScraper:
    """Scraper for Fandom wikis."""
    
    def __init__(self, wiki_name: str):
        self.wiki_name = wiki_name
        self.base_url = f"https://{wiki_name}.fandom.com"
        self.api_url = f"{self.base_url}/api.php"
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    def _get(self, url: str, retries: int = MAX_RETRIES) -> Optional[requests.Response]:
        """Make a GET request with retries."""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    time.sleep(5)  # Rate limited, wait longer
            except Exception as e:
                if attempt == retries - 1:
                    print(f"  Error fetching {url}: {e}")
            time.sleep(DELAY_BETWEEN_REQUESTS)
        return None
    
    def get_category_members(self, category: str, limit: int = 500) -> List[Dict[str, str]]:
        """Get all pages in a category using the MediaWiki API."""
        members = []
        continue_param = None
        
        while len(members) < limit:
            params = {
                "action": "query",
                "list": "categorymembers",
                "cmtitle": f"Category:{category}",
                "cmlimit": min(50, limit - len(members)),
                "format": "json",
            }
            if continue_param:
                params["cmcontinue"] = continue_param
            
            response = self._get(f"{self.api_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}")
            if not response:
                break
            
            data = response.json()
            query_members = data.get("query", {}).get("categorymembers", [])
            
            for member in query_members:
                members.append({
                    "title": member["title"],
                    "pageid": member.get("pageid"),
                })
            
            # Check for continuation
            if "continue" in data:
                continue_param = data["continue"].get("cmcontinue")
            else:
                break
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        return members[:limit]
    
    def search_pages(self, query: str, limit: int = 50) -> List[Dict[str, str]]:
        """Search for pages."""
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json",
        }
        
        response = self._get(f"{self.api_url}?{'&'.join(f'{k}={quote(str(v))}' for k, v in params.items())}")
        if not response:
            return []
        
        data = response.json()
        results = data.get("query", {}).get("search", [])
        
        return [{"title": r["title"], "pageid": r.get("pageid")} for r in results]
    
    def list_categories(self) -> List[str]:
        """List main categories on the wiki."""
        params = {
            "action": "query",
            "list": "allcategories",
            "aclimit": 100,
            "format": "json",
        }
        
        response = self._get(f"{self.api_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}")
        if not response:
            return []
        
        data = response.json()
        categories = data.get("query", {}).get("allcategories", [])
        
        # Filter for likely character categories
        character_keywords = ["character", "people", "individual", "cast", "hero", "villain", "male", "female"]
        filtered = []
        
        for cat in categories:
            cat_name = cat.get("*", "")
            if any(kw in cat_name.lower() for kw in character_keywords):
                filtered.append(cat_name)
        
        return filtered[:30]
    
    def get_character_page(self, title: str) -> Optional[ScrapedCharacter]:
        """Scrape a character page."""
        url = f"{self.base_url}/wiki/{quote(title.replace(' ', '_'))}"
        response = self._get(url)
        
        if not response:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        character = ScrapedCharacter(name=title, url=url)
        
        # Get description from first paragraph
        content = soup.find('div', class_='mw-parser-output')
        if content:
            first_p = content.find('p', recursive=False)
            if first_p:
                character.description = first_p.get_text().strip()[:1000]
        
        # Parse infobox
        infobox = soup.find('aside', class_='portable-infobox') or soup.find('table', class_='infobox')
        if infobox:
            character = self._parse_infobox(infobox, character)
        
        # Detect traits from description
        character.traits = self._detect_traits(character.description)
        
        # Detect role from description
        character.role = self._detect_role(character.description)
        
        # Get abilities section
        abilities_section = soup.find(['h2', 'h3'], string=re.compile(r'abilities|powers|skills', re.I))
        if abilities_section:
            abilities_content = []
            for sibling in abilities_section.find_next_siblings():
                if sibling.name in ['h2', 'h3']:
                    break
                abilities_content.append(sibling.get_text())
            character.abilities = self._extract_abilities(' '.join(abilities_content))
        
        return character
    
    def _parse_infobox(self, infobox, character: ScrapedCharacter) -> ScrapedCharacter:
        """Parse infobox for character data."""
        # Try different infobox formats
        
        # Portable infobox (newer Fandom style)
        for item in infobox.find_all(['div', 'tr']):
            label_elem = item.find(['h3', 'th', 'td'], class_=lambda c: c and 'label' in str(c).lower())
            value_elem = item.find(['div', 'td'], class_=lambda c: c and 'value' in str(c).lower())
            
            if not label_elem:
                label_elem = item.find('th')
            if not value_elem:
                value_elem = item.find('td')
            
            if label_elem and value_elem:
                label = label_elem.get_text().strip().lower()
                value = value_elem.get_text().strip()
                
                # Gender
                if any(g in label for g in ['gender', 'sex']):
                    if 'female' in value.lower() or 'woman' in value.lower():
                        character.gender = 'female'
                    elif 'male' in value.lower() or 'man' in value.lower():
                        character.gender = 'male'
                
                # Species
                if any(s in label for s in ['species', 'race', 'type']):
                    character.species = value.split(',')[0].strip().lower()
                
                # Hair color
                if 'hair' in label:
                    character.hair_color = value.split(',')[0].strip().lower()
                
                # Occupation
                if any(o in label for o in ['occupation', 'job', 'profession', 'position']):
                    character.occupation = value.split(',')[0].strip()
                
                # Affiliation
                if any(a in label for a in ['affiliation', 'team', 'group', 'crew', 'organization']):
                    affiliations = [a.strip() for a in value.split(',')]
                    character.affiliations.extend(affiliations)
                
                # Family
                if any(f in label for f in ['family', 'relative', 'parent']):
                    if any(w in value.lower() for w in ['unknown', 'deceased', 'none', 'orphan']):
                        character.family_status = 'orphan'
                
                # First appearance
                if 'first' in label and 'appear' in label:
                    character.first_appearance = value
        
        return character
    
    def _detect_traits(self, text: str) -> List[str]:
        """Detect character traits from text."""
        text_lower = text.lower()
        detected = []
        
        for trait, keywords in TRAIT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected.append(trait)
                    break
        
        return list(set(detected))
    
    def _detect_role(self, text: str) -> str:
        """Detect character role from text."""
        text_lower = text.lower()
        
        for role, patterns in ROLE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return role
        
        return "supporting"
    
    def _extract_abilities(self, text: str) -> List[str]:
        """Extract abilities from text."""
        abilities = []
        
        # Look for bullet points or listed items
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) < 100 and not line.endswith(':'):
                # Clean up
                line = re.sub(r'^[\-\*•]\s*', '', line)
                if line and not any(skip in line.lower() for skip in ['see also', 'reference', 'note']):
                    abilities.append(line)
        
        return abilities[:10]
    
    def scrape_characters(self, category: str = "Characters", max_chars: int = MAX_CHARACTERS_DEFAULT,
                         progress_callback=None) -> List[ScrapedCharacter]:
        """Scrape all characters from a category."""
        print(f"Fetching character list from category: {category}")
        
        members = self.get_category_members(category, limit=max_chars * 2)
        
        if not members:
            # Try searching instead
            print("Category not found, trying search...")
            members = self.search_pages("character", limit=max_chars)
        
        print(f"Found {len(members)} potential character pages")
        
        characters = []
        for i, member in enumerate(members):
            if len(characters) >= max_chars:
                break
            
            title = member["title"]
            
            # Skip non-character pages
            skip_patterns = ['category:', 'template:', 'list of', 'episode', 'chapter', 'volume', 'arc']
            if any(skip in title.lower() for skip in skip_patterns):
                continue
            
            print(f"  [{i+1}/{len(members)}] Scraping: {title}...", end=" ", flush=True)
            
            char = self.get_character_page(title)
            if char:
                characters.append(char)
                print("✓")
            else:
                print("✗")
            
            if progress_callback:
                progress_callback(i + 1, len(members))
            
            time.sleep(DELAY_BETWEEN_REQUESTS)
        
        return characters
    
    def get_story_info(self) -> Dict[str, Any]:
        """Get basic story info from the main page."""
        response = self._get(f"{self.base_url}/wiki/Main_Page")
        
        info = {
            "title": self.wiki_name.replace("-", " ").title(),
            "category": "anime",
            "genre": [],
            "themes": [],
        }
        
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to get title from page
            title_elem = soup.find('h1') or soup.find('title')
            if title_elem:
                title_text = title_elem.get_text()
                # Clean up
                title_text = re.sub(r'\s*wiki\s*$', '', title_text, flags=re.I)
                title_text = re.sub(r'\s*\|.*$', '', title_text)
                if title_text:
                    info["title"] = title_text.strip()
        
        return info


class MALScraper:
    """Scraper for MyAnimeList using Jikan API (unofficial MAL API)."""
    
    def __init__(self):
        self.api_base = "https://api.jikan.moe/v4"
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    def _get(self, endpoint: str) -> Optional[dict]:
        """Make API request."""
        url = f"{self.api_base}/{endpoint}"
        
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    time.sleep(2)  # Rate limited
            except Exception as e:
                print(f"  API error: {e}")
            time.sleep(1)
        
        return None
    
    def search_anime(self, query: str) -> Optional[dict]:
        """Search for an anime."""
        data = self._get(f"anime?q={quote(query)}&limit=1")
        if data and data.get("data"):
            return data["data"][0]
        return None
    
    def get_characters(self, anime_id: int) -> List[ScrapedCharacter]:
        """Get characters for an anime."""
        data = self._get(f"anime/{anime_id}/characters")
        
        if not data or not data.get("data"):
            return []
        
        characters = []
        for char_data in data["data"]:
            char_info = char_data.get("character", {})
            role = char_data.get("role", "").lower()
            
            # Map MAL roles to our roles
            role_map = {
                "main": "protagonist",
                "supporting": "supporting",
            }
            
            char = ScrapedCharacter(
                name=char_info.get("name", "Unknown"),
                url=char_info.get("url", ""),
                role=role_map.get(role, "supporting"),
            )
            
            characters.append(char)
        
        return characters
    
    def scrape_anime(self, query: str, max_chars: int = MAX_CHARACTERS_DEFAULT) -> Tuple[Dict[str, Any], List[ScrapedCharacter]]:
        """Scrape anime info and characters."""
        print(f"Searching MAL for: {query}")
        
        anime = self.search_anime(query)
        if not anime:
            print("Anime not found")
            return {}, []
        
        anime_id = anime["mal_id"]
        print(f"Found: {anime['title']} (ID: {anime_id})")
        
        # Get story info
        info = {
            "title": anime.get("title", query),
            "category": "anime",
            "year": anime.get("year"),
            "genre": [g["name"].lower() for g in anime.get("genres", [])],
            "themes": [t["name"].lower() for t in anime.get("themes", [])],
        }
        
        # Get characters
        print("Fetching characters...")
        time.sleep(1)  # Rate limiting
        characters = self.get_characters(anime_id)
        
        print(f"Found {len(characters)} characters")
        
        return info, characters[:max_chars]


def generate_story_json(info: Dict[str, Any], characters: List[ScrapedCharacter], 
                       output_path: str) -> dict:
    """Generate story JSON file."""
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
    
    # Add story name to each character
    for char in story["characters"]:
        char["story"] = story["title"]
    
    # Save
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(story, f, indent=2, ensure_ascii=False)
    
    print(f"\nStory saved to: {output_path}")
    
    return story


def cmd_fandom(args):
    """Scrape from a Fandom wiki."""
    scraper = FandomScraper(args.wiki)
    
    if args.list_categories:
        print(f"Categories on {args.wiki}.fandom.com:\n")
        categories = scraper.list_categories()
        for cat in categories:
            print(f"  - {cat}")
        return 0
    
    # Get story info
    info = scraper.get_story_info()
    info["source"] = f"{args.wiki}.fandom.com"
    
    print(f"\nScraping: {info['title']}")
    print(f"Wiki: {scraper.base_url}")
    print(f"Category: {args.category}")
    print(f"Max characters: {args.max_chars}")
    print("-" * 50)
    
    # Scrape characters
    characters = scraper.scrape_characters(
        category=args.category,
        max_chars=args.max_chars
    )
    
    if not characters:
        print("No characters found. Try --list-categories to see available categories.")
        return 1
    
    # Generate JSON
    output_path = args.output or f"{args.wiki}_story.json"
    generate_story_json(info, characters, output_path)
    
    # Print summary
    print(f"\n{'=' * 50}")
    print(f"SCRAPING COMPLETE")
    print(f"{'=' * 50}")
    print(f"Characters scraped: {len(characters)}")
    print(f"Output: {output_path}")
    
    # Show trait summary
    all_traits = []
    for c in characters:
        all_traits.extend(c.traits)
    trait_counts = {}
    for t in all_traits:
        trait_counts[t] = trait_counts.get(t, 0) + 1
    
    if trait_counts:
        print(f"\nDetected traits:")
        for trait, count in sorted(trait_counts.items(), key=lambda x: -x[1])[:10]:
            print(f"  {trait}: {count}")
    
    return 0


def cmd_mal(args):
    """Scrape from MyAnimeList."""
    scraper = MALScraper()
    
    info, characters = scraper.scrape_anime(args.query, args.max_chars)
    
    if not characters:
        print("Failed to scrape anime")
        return 1
    
    info["source"] = "MyAnimeList"
    
    # Generate JSON
    output_path = args.output or f"{args.query.lower().replace(' ', '_')}_story.json"
    generate_story_json(info, characters, output_path)
    
    print(f"\nCharacters scraped: {len(characters)}")
    print(f"Output: {output_path}")
    
    return 0


def cmd_batch(args):
    """Batch scrape multiple wikis."""
    wikis = []
    
    # Read from file
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
        
        time.sleep(2)  # Be nice between wikis
    
    print(f"\nBatch complete! Output in: {output_dir}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Story Data Scraper - Auto-generate story JSON from wikis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Scraper source")
    
    # Fandom command
    fandom_parser = subparsers.add_parser("fandom", help="Scrape from a Fandom wiki")
    fandom_parser.add_argument("wiki", help="Wiki name (e.g., 'onepiece', 'naruto', 'dragonball')")
    fandom_parser.add_argument("-c", "--category", default="Characters", 
                               help="Category to scrape (default: Characters)")
    fandom_parser.add_argument("-m", "--max-chars", type=int, default=MAX_CHARACTERS_DEFAULT,
                               help=f"Maximum characters to scrape (default: {MAX_CHARACTERS_DEFAULT})")
    fandom_parser.add_argument("-o", "--output", help="Output JSON file")
    fandom_parser.add_argument("--list-categories", action="store_true",
                               help="List available categories and exit")
    
    # MAL command
    mal_parser = subparsers.add_parser("mal", help="Scrape from MyAnimeList")
    mal_parser.add_argument("query", help="Anime name to search")
    mal_parser.add_argument("-m", "--max-chars", type=int, default=MAX_CHARACTERS_DEFAULT,
                            help=f"Maximum characters (default: {MAX_CHARACTERS_DEFAULT})")
    mal_parser.add_argument("-o", "--output", help="Output JSON file")
    
    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Batch scrape multiple wikis")
    batch_parser.add_argument("file", help="Text file with wiki names (one per line)")
    batch_parser.add_argument("-o", "--output-dir", default="scraped_stories",
                              help="Output directory")
    batch_parser.add_argument("-m", "--max-chars", type=int, default=50,
                              help="Max characters per wiki")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        print("\nExamples:")
        print("  python story_scraper.py fandom onepiece -o onepiece.json")
        print("  python story_scraper.py fandom naruto --list-categories")
        print("  python story_scraper.py mal 'Attack on Titan' -o aot.json")
        return 1
    
    commands = {
        "fandom": cmd_fandom,
        "mal": cmd_mal,
        "batch": cmd_batch,
    }
    
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
