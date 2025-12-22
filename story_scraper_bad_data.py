#!/usr/bin/env python3
"""
Story Data Scraper - Auto-generate story JSON from wikis

Scrapes character and plot information from Fandom wikis and other sources
to automatically create JSON files for the Narrative Pattern Analyzer.

Supported sources:
- Fandom wikis (any wiki on fandom.com) - HTML scraping method
- MyAnimeList (via Jikan API - no key needed)

Usage:
------
# Scrape from a Fandom wiki
python story_scraper.py fandom "naruto" -o naruto.json

# Scrape from MyAnimeList  
python story_scraper.py mal "One Piece" -o onepiece.json

# Scrape with character limit
python story_scraper.py fandom "dragonball" --max-chars 50 -o dragonball.json
"""

import argparse
import json
import re
import sys
import time
import random
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import quote, urljoin, unquote
from dataclasses import dataclass, field
import requests
from bs4 import BeautifulSoup

# Configuration
DELAY_MIN = 1.0
DELAY_MAX = 2.5
MAX_CHARACTERS_DEFAULT = 50
MAX_RETRIES = 3

# Rotating user agents to avoid detection
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
]

# Trait detection keywords
TRAIT_KEYWORDS = {
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
    "protagonist": ["protagonist", "main character", "hero", "heroine"],
    "antagonist": ["antagonist", "villain", "enemy", "evil"],
    "mentor": ["mentor", "teacher", "master", "sensei", "trains"],
    "rival": ["rival", "competitor", "nemesis"],
    "orphan": ["orphan", "parents died", "no parents", "lost parents", "raised by"],
    "royalty": ["prince", "princess", "king", "queen", "royal"],
    "hidden_power": ["hidden power", "latent", "dormant", "awakens", "unlocks"],
    "transforms": ["transform", "transformation", "forms", "evolve"],
}

# Role detection patterns
ROLE_PATTERNS = {
    "protagonist": [r"main\s*(character|protagonist)", r"is\s*the\s*(hero|protagonist)", r"series\s*follows"],
    "antagonist": [r"main\s*(villain|antagonist|enemy)", r"is\s*the\s*(villain|antagonist)", r"arch[\s-]?enemy"],
    "mentor": [r"mentor", r"teaches?\s*(the\s*)?(protagonist|hero|main)", r"trains?\s*(the\s*)?(protagonist|hero|main)"],
    "rival": [r"rival", r"competes?\s*with", r"nemesis"],
    "sidekick": [r"sidekick", r"companion", r"best\s*friend", r"partner"],
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
            "metadata": {"source_url": self.url, "affiliations": self.affiliations}
        }


class FandomScraperHTML:
    """Scraper for Fandom wikis using HTML parsing (bypasses API blocks)."""
    
    def __init__(self, wiki_name: str):
        self.wiki_name = wiki_name
        self.base_url = f"https://{wiki_name}.fandom.com"
        self.session = requests.Session()
        self._update_headers()
    
    def _update_headers(self):
        """Update session headers with random user agent."""
        self.session.headers.update({
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
    
    def _delay(self):
        """Random delay between requests."""
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
    
    def _get(self, url: str, retries: int = MAX_RETRIES) -> Optional[requests.Response]:
        """Make a GET request with retries."""
        for attempt in range(retries):
            try:
                # Rotate user agent occasionally
                if random.random() < 0.3:
                    self._update_headers()
                
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    # Check for Cloudflare challenge
                    if 'challenge' in response.text.lower()[:1000] or 'cf-' in response.text.lower()[:1000]:
                        print(f"  Cloudflare detected, waiting...")
                        time.sleep(5)
                        continue
                    return response
                elif response.status_code == 429:
                    print(f"  Rate limited, waiting...")
                    time.sleep(10)
                elif response.status_code == 403:
                    print(f"  Blocked (403), trying different UA...")
                    self._update_headers()
                    time.sleep(3)
            except Exception as e:
                if attempt == retries - 1:
                    print(f"  Error: {e}")
            
            self._delay()
        
        return None
    
    def get_character_list_from_category_page(self, category: str = "Characters") -> List[Dict[str, str]]:
        """Get character list by scraping the category page HTML."""
        characters = []
        
        # Try different category page formats
        category_urls = [
            f"{self.base_url}/wiki/Category:{category}",
            f"{self.base_url}/wiki/Category:{category.replace(' ', '_')}",
        ]
        
        for url in category_urls:
            print(f"  Trying: {url}")
            response = self._get(url)
            
            if not response:
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find character links in category page
            # Method 1: category-page__member-link
            for link in soup.find_all('a', class_='category-page__member-link'):
                title = link.get('title', '') or link.get_text().strip()
                href = link.get('href', '')
                if title and href and not self._should_skip(title):
                    characters.append({"title": title, "url": urljoin(self.base_url, href)})
            
            # Method 2: Standard MediaWiki category listing
            category_div = soup.find('div', id='mw-pages') or soup.find('div', class_='mw-category')
            if category_div:
                for link in category_div.find_all('a'):
                    title = link.get('title', '') or link.get_text().strip()
                    href = link.get('href', '')
                    if title and href and not self._should_skip(title):
                        full_url = urljoin(self.base_url, href)
                        if {"title": title, "url": full_url} not in characters:
                            characters.append({"title": title, "url": full_url})
            
            # Method 3: category-page__members
            members_div = soup.find('div', class_='category-page__members')
            if members_div:
                for link in members_div.find_all('a'):
                    title = link.get('title', '') or link.get_text().strip()
                    href = link.get('href', '')
                    if title and href and not self._should_skip(title):
                        full_url = urljoin(self.base_url, href)
                        if {"title": title, "url": full_url} not in characters:
                            characters.append({"title": title, "url": full_url})
            
            if characters:
                break
            
            self._delay()
        
        return characters
    
    def get_characters_from_list_page(self, list_page: str = "List_of_characters") -> List[Dict[str, str]]:
        """Get characters from a 'List of characters' page."""
        characters = []
        
        # Try different list page names
        list_urls = [
            f"{self.base_url}/wiki/{list_page}",
            f"{self.base_url}/wiki/List_of_Characters",
            f"{self.base_url}/wiki/Characters",
            f"{self.base_url}/wiki/Main_Characters",
        ]
        
        for url in list_urls:
            print(f"  Trying list page: {url}")
            response = self._get(url)
            
            if not response:
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the main content area
            content = soup.find('div', class_='mw-parser-output')
            if not content:
                continue
            
            # Look for character links in tables, lists, or galleries
            for link in content.find_all('a'):
                href = link.get('href', '')
                title = link.get('title', '') or link.get_text().strip()
                
                # Skip non-character links
                if not href or not title:
                    continue
                if href.startswith('#') or 'Category:' in href or 'File:' in href:
                    continue
                if self._should_skip(title):
                    continue
                
                # Must be a wiki link
                if '/wiki/' in href:
                    full_url = urljoin(self.base_url, href)
                    if {"title": title, "url": full_url} not in characters:
                        characters.append({"title": title, "url": full_url})
            
            if characters:
                print(f"  Found {len(characters)} potential characters")
                break
            
            self._delay()
        
        return characters
    
    def _should_skip(self, title: str) -> bool:
        """Check if a page should be skipped."""
        skip_patterns = [
            'category:', 'template:', 'file:', 'image:', 'list of', 
            'episode', 'chapter', 'volume', 'arc', 'saga', 'gallery',
            'navigation', 'main page', 'wiki', 'help:', 'user:',
            'special:', 'talk:', 'disambiguation'
        ]
        title_lower = title.lower()
        return any(skip in title_lower for skip in skip_patterns)
    
    def get_character_page(self, url: str, title: str) -> Optional[ScrapedCharacter]:
        """Scrape a character page."""
        response = self._get(url)
        
        if not response:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if it's actually a character page (has infobox)
        infobox = soup.find('aside', class_='portable-infobox') or \
                  soup.find('table', class_='infobox') or \
                  soup.find('div', class_='infobox')
        
        character = ScrapedCharacter(name=title, url=url)
        
        # Get description from first paragraph
        content = soup.find('div', class_='mw-parser-output')
        if content:
            # Skip infobox and find first real paragraph
            for p in content.find_all('p', recursive=False):
                text = p.get_text().strip()
                if text and len(text) > 50 and not text.startswith('['):
                    character.description = text[:1000]
                    break
        
        # Parse infobox if exists
        if infobox:
            character = self._parse_infobox(infobox, character)
        
        # Detect traits and role from description
        if character.description:
            character.traits = self._detect_traits(character.description)
            detected_role = self._detect_role(character.description)
            if detected_role != "supporting":
                character.role = detected_role
        
        # Get abilities section
        abilities_header = soup.find(['h2', 'h3'], string=re.compile(r'abilities|powers|skills|techniques', re.I))
        if abilities_header:
            abilities_content = []
            for sibling in abilities_header.find_next_siblings():
                if sibling.name in ['h2', 'h3']:
                    break
                abilities_content.append(sibling.get_text())
            character.abilities = self._extract_abilities(' '.join(abilities_content))
        
        return character
    
    def _parse_infobox(self, infobox, character: ScrapedCharacter) -> ScrapedCharacter:
        """Parse infobox for character data."""
        
        # Portable infobox (Fandom style)
        for item in infobox.find_all(['div', 'tr', 'section']):
            # Try to find label/value pairs
            label_elem = item.find(['h3', 'th', 'div'], class_=lambda c: c and ('label' in str(c).lower() or 'pi-data-label' in str(c).lower()))
            value_elem = item.find(['div', 'td'], class_=lambda c: c and ('value' in str(c).lower() or 'pi-data-value' in str(c).lower()))
            
            # Fallback to th/td
            if not label_elem:
                label_elem = item.find('th')
            if not value_elem:
                value_elem = item.find('td')
            
            # Also check data-source attribute
            if not label_elem and item.get('data-source'):
                label = item.get('data-source', '').lower()
                value_elem = item.find(['div'], class_=lambda c: c and 'value' in str(c).lower())
                if value_elem:
                    value = value_elem.get_text().strip()
                    self._apply_infobox_value(character, label, value)
                continue
            
            if label_elem and value_elem:
                label = label_elem.get_text().strip().lower()
                value = value_elem.get_text().strip()
                self._apply_infobox_value(character, label, value)
        
        return character
    
    def _apply_infobox_value(self, character: ScrapedCharacter, label: str, value: str):
        """Apply a single infobox value to the character."""
        # Gender
        if any(g in label for g in ['gender', 'sex']):
            if 'female' in value.lower() or 'woman' in value.lower() or 'girl' in value.lower():
                character.gender = 'female'
            elif 'male' in value.lower() or 'man' in value.lower() or 'boy' in value.lower():
                character.gender = 'male'
        
        # Species/Race
        if any(s in label for s in ['species', 'race', 'type', 'classification']):
            character.species = value.split(',')[0].strip().lower()[:50]
        
        # Hair color
        if 'hair' in label:
            character.hair_color = value.split(',')[0].strip().lower()[:30]
        
        # Occupation
        if any(o in label for o in ['occupation', 'job', 'profession', 'position', 'rank', 'title']):
            character.occupation = value.split(',')[0].strip()[:100]
        
        # Affiliation
        if any(a in label for a in ['affiliation', 'team', 'group', 'crew', 'organization', 'village', 'clan']):
            affiliations = [a.strip() for a in re.split(r'[,\n]', value) if a.strip()]
            character.affiliations.extend(affiliations[:5])
        
        # Family
        if any(f in label for f in ['family', 'relative', 'parent', 'status']):
            if any(w in value.lower() for w in ['unknown', 'deceased', 'none', 'orphan', 'dead']):
                character.family_status = 'orphan'
    
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
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and 10 < len(line) < 80:
                line = re.sub(r'^[\-\*•:]\s*', '', line)
                if line and not any(skip in line.lower() for skip in ['see also', 'reference', 'note', 'edit']):
                    abilities.append(line)
        
        return abilities[:10]
    
    def scrape_characters(self, category: str = "Characters", max_chars: int = MAX_CHARACTERS_DEFAULT) -> List[ScrapedCharacter]:
        """Scrape characters from the wiki."""
        print(f"\nFetching character list...")
        
        # Try category page first
        members = self.get_character_list_from_category_page(category)
        
        # If that fails, try list pages
        if not members:
            print("  Category page didn't work, trying list pages...")
            members = self.get_characters_from_list_page()
        
        if not members:
            print("  No character list found!")
            return []
        
        print(f"Found {len(members)} character pages to scrape")
        print(f"Scraping up to {max_chars} characters...\n")
        
        characters = []
        for i, member in enumerate(members):
            if len(characters) >= max_chars:
                break
            
            title = member["title"]
            url = member["url"]
            
            print(f"  [{i+1}/{min(len(members), max_chars)}] {title}...", end=" ", flush=True)
            
            char = self.get_character_page(url, title)
            if char and char.description:  # Only keep chars with descriptions
                characters.append(char)
                print("✓")
            else:
                print("✗ (no content)")
            
            self._delay()
        
        return characters
    
    def get_story_info(self) -> Dict[str, Any]:
        """Get basic story info from the wiki."""
        response = self._get(f"{self.base_url}/wiki/Main_Page")
        
        info = {
            "title": self.wiki_name.replace("-", " ").replace("_", " ").title(),
            "category": "anime",
            "genre": [],
            "themes": [],
        }
        
        if response:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get title
            og_title = soup.find('meta', property='og:site_name')
            if og_title:
                title = og_title.get('content', '')
                title = re.sub(r'\s*wiki\s*$', '', title, flags=re.I).strip()
                if title:
                    info["title"] = title
        
        return info


class MALScraper:
    """Scraper for MyAnimeList using Jikan API."""
    
    def __init__(self):
        self.api_base = "https://api.jikan.moe/v4"
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
    
    def _get(self, endpoint: str) -> Optional[dict]:
        """Make API request."""
        url = f"{self.api_base}/{endpoint}"
        
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    print("  Rate limited, waiting...")
                    time.sleep(3)
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
            
            role_map = {"main": "protagonist", "supporting": "supporting"}
            
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
        
        info = {
            "title": anime.get("title", query),
            "category": "anime",
            "year": anime.get("year"),
            "genre": [g["name"].lower() for g in anime.get("genres", [])],
            "themes": [t["name"].lower() for t in anime.get("themes", [])],
        }
        
        print("Fetching characters...")
        time.sleep(1)
        characters = self.get_characters(anime_id)
        
        print(f"Found {len(characters)} characters")
        
        return info, characters[:max_chars]


def generate_story_json(info: Dict[str, Any], characters: List[ScrapedCharacter], output_path: str) -> dict:
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
    
    for char in story["characters"]:
        char["story"] = story["title"]
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(story, f, indent=2, ensure_ascii=False)
    
    print(f"\nStory saved to: {output_path}")
    
    return story


def cmd_fandom(args):
    """Scrape from a Fandom wiki."""
    scraper = FandomScraperHTML(args.wiki)
    
    # Get story info
    info = scraper.get_story_info()
    info["source"] = f"{args.wiki}.fandom.com"
    
    print(f"\n{'=' * 60}")
    print(f"Scraping: {info['title']}")
    print(f"Wiki: {scraper.base_url}")
    print(f"Category: {args.category}")
    print(f"Max characters: {args.max_chars}")
    print(f"{'=' * 60}")
    
    # Scrape characters
    characters = scraper.scrape_characters(category=args.category, max_chars=args.max_chars)
    
    if not characters:
        print("\nNo characters found. The wiki might have different category names.")
        print("Try these categories: 'Characters', 'Main_Characters', 'Protagonists'")
        return 1
    
    # Generate JSON
    output_path = args.output or f"{args.wiki}_story.json"
    generate_story_json(info, characters, output_path)
    
    # Summary
    print(f"\n{'=' * 60}")
    print("SCRAPING COMPLETE")
    print(f"{'=' * 60}")
    print(f"Characters scraped: {len(characters)}")
    print(f"Output: {output_path}")
    
    # Trait summary
    all_traits = []
    for c in characters:
        all_traits.extend(c.traits)
    
    if all_traits:
        trait_counts = {}
        for t in all_traits:
            trait_counts[t] = trait_counts.get(t, 0) + 1
        
        print(f"\nDetected traits:")
        for trait, count in sorted(trait_counts.items(), key=lambda x: -x[1])[:10]:
            print(f"  {trait}: {count}")
    
    # Role summary
    roles = {}
    for c in characters:
        roles[c.role] = roles.get(c.role, 0) + 1
    
    print(f"\nRoles detected:")
    for role, count in sorted(roles.items(), key=lambda x: -x[1]):
        print(f"  {role}: {count}")
    
    return 0


def cmd_mal(args):
    """Scrape from MyAnimeList."""
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
        description="Story Data Scraper - Auto-generate story JSON from wikis",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Scraper source")
    
    # Fandom command
    fandom_parser = subparsers.add_parser("fandom", help="Scrape from a Fandom wiki")
    fandom_parser.add_argument("wiki", help="Wiki name (e.g., 'naruto', 'onepiece', 'dragonball')")
    fandom_parser.add_argument("-c", "--category", default="Characters", help="Category to scrape")
    fandom_parser.add_argument("-m", "--max-chars", type=int, default=MAX_CHARACTERS_DEFAULT, help="Max characters")
    fandom_parser.add_argument("-o", "--output", help="Output JSON file")
    
    # MAL command
    mal_parser = subparsers.add_parser("mal", help="Scrape from MyAnimeList")
    mal_parser.add_argument("query", help="Anime name to search")
    mal_parser.add_argument("-m", "--max-chars", type=int, default=MAX_CHARACTERS_DEFAULT, help="Max characters")
    mal_parser.add_argument("-o", "--output", help="Output JSON file")
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        print("\nExamples:")
        print("  python story_scraper.py fandom naruto -o data/naruto.json")
        print("  python story_scraper.py fandom onepiece --max-chars 30")
        print("  python story_scraper.py mal 'Attack on Titan' -o aot.json")
        return 1
    
    commands = {"fandom": cmd_fandom, "mal": cmd_mal}
    return commands[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
