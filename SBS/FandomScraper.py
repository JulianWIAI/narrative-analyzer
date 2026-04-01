"""
FandomScraper.py
----------------
Defines the FandomScraper class, which retrieves character data from Fandom
wikis via the MediaWiki REST API.  This is the primary scraper strategy;
``FandomScraperHTML`` in the same package is used as a fallback when API
access is blocked.
"""

import re
import time
import random
from typing import Dict, List, Optional, Any
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from SBS.ScrapedCharacter import ScrapedCharacter

# ---------------------------------------------------------------------------
# Module-level configuration
# ---------------------------------------------------------------------------

# Deliberate random delay between every outbound request.
# This is intentional and required to respect the website's rate limits and
# Terms of Service.  A fixed delay is easy to detect and circumvent; a random
# range (1.0–2.5 s) produces more human-like traffic patterns.
DELAY_MIN = 1.0
DELAY_MAX = 2.5

MAX_CHARACTERS_DEFAULT = 100
MAX_RETRIES = 3

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                  '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}

# Trait detection: maps canonical trait name to trigger keywords
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
    "wealthy": ["rich", "wealthy", "billionaire", "fortune"],
    "poor": ["poor", "poverty", "humble origins"],
    "tall": ["tall", "towering", "giant"],
    "short": ["short", "small", "petite", "tiny"],
    "muscular": ["muscular", "strong", "buff", "powerful build"],
    "hidden_power": ["hidden power", "latent", "dormant", "awakens", "unlocks"],
    "transforms": ["transform", "transformation", "forms", "evolve"],
}

# Role detection: maps role name to regex patterns applied to page text
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
    "rival": [r"rival", r"competes?\s*with", r"nemesis"],
    "sidekick": [
        r"sidekick", r"companion", r"best\s*friend", r"partner", r"travels?\s*with"
    ],
}


class FandomScraper:
    """
    Scrapes character data from Fandom wikis using the MediaWiki API.

    Each instance targets one wiki (e.g. ``'onepiece'`` → onepiece.fandom.com).
    Characters are discovered via the ``Category:Characters`` API endpoint,
    then scraped individually from their wiki pages.

    The MediaWiki API approach is preferred over direct HTML parsing because
    it provides structured pagination and avoids per-page Cloudflare checks.
    Use ``FandomScraperHTML`` if the API is blocked for a particular wiki.
    """

    def __init__(self, wiki_name: str):
        """
        Initialise the scraper for the given Fandom wiki.

        Args:
            wiki_name: Subdomain of the target wiki (e.g. ``'onepiece'``,
                       ``'naruto'``, ``'dragonball'``).
        """
        self.wiki_name = wiki_name
        self.base_url = f"https://{wiki_name}.fandom.com"
        self.api_url = f"{self.base_url}/api.php"
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _get(self, url: str, retries: int = MAX_RETRIES) -> Optional[requests.Response]:
        """
        Perform a GET request with automatic retries and rate-limit handling.

        Sleeps briefly between attempts.  If a 429 response is received, the
        method waits 5 seconds before retrying.  All other errors are logged
        and retried up to the ``retries`` limit.

        Args:
            url:     Full URL to request.
            retries: Maximum number of attempts before returning ``None``.

        Returns:
            A successful ``requests.Response`` object, or ``None`` if all
            attempts fail.
        """
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    time.sleep(5)  # Rate limited — wait longer than usual
            except Exception as e:
                if attempt == retries - 1:
                    print(f"  Error fetching {url}: {e}")
            # Polite delay — respects website ToS and avoids overwhelming the server
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
        return None

    def get_category_members(self, category: str, limit: int = 500) -> List[Dict[str, str]]:
        """
        Retrieve all wiki pages belonging to the specified category via the API.

        Handles pagination automatically using the ``cmcontinue`` token
        returned by the MediaWiki API until ``limit`` members have been
        collected or the category is exhausted.

        Args:
            category: Category name without the ``Category:`` prefix
                      (e.g. ``'Characters'``).
            limit:    Maximum total number of members to return.

        Returns:
            A list of ``{'title': ..., 'pageid': ...}`` dictionaries.
        """
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

            response = self._get(
                f"{self.api_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
            )
            if not response:
                break

            data = response.json()
            query_members = data.get("query", {}).get("categorymembers", [])

            for member in query_members:
                members.append({
                    "title": member["title"],
                    "pageid": member.get("pageid"),
                })

            if "continue" in data:
                continue_param = data["continue"].get("cmcontinue")
            else:
                break

            # Polite delay — respects website ToS and avoids overwhelming the server
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

        return members[:limit]

    def search_pages(self, query: str, limit: int = 50) -> List[Dict[str, str]]:
        """
        Search the wiki for pages matching the given query string.

        Used as a fallback when ``get_category_members`` returns no results.

        Args:
            query: Search term (e.g. ``'character'``).
            limit: Maximum number of results to return.

        Returns:
            A list of ``{'title': ..., 'pageid': ...}`` dictionaries.
        """
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "srlimit": limit,
            "format": "json",
        }

        response = self._get(
            f"{self.api_url}?{'&'.join(f'{k}={quote(str(v))}' for k, v in params.items())}"
        )
        if not response:
            return []

        data = response.json()
        results = data.get("query", {}).get("search", [])

        return [{"title": r["title"], "pageid": r.get("pageid")} for r in results]

    def list_categories(self) -> List[str]:
        """
        Return a filtered list of category names likely to contain characters.

        Queries the MediaWiki ``allcategories`` API and returns up to 30
        categories whose names contain character-related keywords.

        Returns:
            List of category name strings (without the ``Category:`` prefix).
        """
        params = {
            "action": "query",
            "list": "allcategories",
            "aclimit": 100,
            "format": "json",
        }

        response = self._get(
            f"{self.api_url}?{'&'.join(f'{k}={v}' for k, v in params.items())}"
        )
        if not response:
            return []

        data = response.json()
        categories = data.get("query", {}).get("allcategories", [])

        character_keywords = ["character", "people", "individual", "cast",
                              "hero", "villain", "male", "female"]
        filtered = []

        for cat in categories:
            cat_name = cat.get("*", "")
            if any(kw in cat_name.lower() for kw in character_keywords):
                filtered.append(cat_name)

        return filtered[:30]

    def get_character_page(self, title: str) -> Optional[ScrapedCharacter]:
        """
        Scrape a single character wiki page and return the parsed data.

        Fetches the HTML page, extracts the first paragraph as the
        description, parses the portable infobox for structured fields, then
        runs trait/role detection heuristics on the description text.

        Args:
            title: Wiki page title (spaces allowed; will be URL-encoded).

        Returns:
            A populated ScrapedCharacter instance, or ``None`` if the page
            could not be fetched.
        """
        url = f"{self.base_url}/wiki/{quote(title.replace(' ', '_'))}"
        response = self._get(url)

        if not response:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        character = ScrapedCharacter(name=title, url=url)

        # Extract description from the first content paragraph
        content = soup.find('div', class_='mw-parser-output')
        if content:
            first_p = content.find('p', recursive=False)
            if first_p:
                character.description = first_p.get_text().strip()[:1000]

        # Parse structured infobox if present
        infobox = (soup.find('aside', class_='portable-infobox') or
                   soup.find('table', class_='infobox'))
        if infobox:
            character = self._parse_infobox(infobox, character)

        character.traits = self._detect_traits(character.description)
        character.role = self._detect_role(character.description)

        # Extract abilities from a dedicated section if one exists
        abilities_section = soup.find(
            ['h2', 'h3'], string=re.compile(r'abilities|powers|skills', re.I)
        )
        if abilities_section:
            abilities_content = []
            for sibling in abilities_section.find_next_siblings():
                if sibling.name in ['h2', 'h3']:
                    break
                abilities_content.append(sibling.get_text())
            character.abilities = self._extract_abilities(' '.join(abilities_content))

        return character

    def _parse_infobox(
        self, infobox, character: ScrapedCharacter
    ) -> ScrapedCharacter:
        """
        Extract structured fields from a Fandom portable infobox.

        Iterates over ``<div>`` and ``<tr>`` elements looking for label/value
        pairs and maps recognised labels to character attributes.

        Args:
            infobox:   BeautifulSoup element representing the infobox.
            character: ScrapedCharacter instance to populate in-place.

        Returns:
            The same ScrapedCharacter instance with fields updated.
        """
        for item in infobox.find_all(['div', 'tr']):
            label_elem = item.find(
                ['h3', 'th', 'td'],
                class_=lambda c: c and 'label' in str(c).lower()
            )
            value_elem = item.find(
                ['div', 'td'],
                class_=lambda c: c and 'value' in str(c).lower()
            )

            if not label_elem:
                label_elem = item.find('th')
            if not value_elem:
                value_elem = item.find('td')

            if label_elem and value_elem:
                label = label_elem.get_text().strip().lower()
                value = value_elem.get_text().strip()

                if any(g in label for g in ['gender', 'sex']):
                    if 'female' in value.lower() or 'woman' in value.lower():
                        character.gender = 'female'
                    elif 'male' in value.lower() or 'man' in value.lower():
                        character.gender = 'male'

                if any(s in label for s in ['species', 'race', 'type']):
                    character.species = value.split(',')[0].strip().lower()

                if 'hair' in label:
                    character.hair_color = value.split(',')[0].strip().lower()

                if any(o in label for o in ['occupation', 'job', 'profession', 'position']):
                    character.occupation = value.split(',')[0].strip()

                if any(a in label for a in ['affiliation', 'team', 'group', 'crew', 'organization']):
                    affiliations = [a.strip() for a in value.split(',')]
                    character.affiliations.extend(affiliations)

                if any(f in label for f in ['family', 'relative', 'parent']):
                    if any(w in value.lower() for w in ['unknown', 'deceased', 'none', 'orphan']):
                        character.family_status = 'orphan'

                if 'first' in label and 'appear' in label:
                    character.first_appearance = value

        return character

    def _detect_traits(self, text: str) -> List[str]:
        """
        Scan description text for known trait keywords and return matched tags.

        Args:
            text: Character description text (typically the first paragraph).

        Returns:
            De-duplicated list of detected trait tags.
        """
        text_lower = text.lower()
        detected = []

        for trait, keywords in TRAIT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    detected.append(trait)
                    break

        return list(set(detected))

    def _detect_role(self, text: str) -> str:
        """
        Infer the character's narrative role from description text.

        Applies role-detection regex patterns in priority order and returns
        the first match, defaulting to ``'supporting'``.

        Args:
            text: Character description text.

        Returns:
            Role string (e.g. ``'protagonist'``, ``'antagonist'``).
        """
        text_lower = text.lower()

        for role, patterns in ROLE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return role

        return "supporting"

    def _extract_abilities(self, text: str) -> List[str]:
        """
        Extract a list of ability names from an abilities/powers section.

        Splits the section text into lines and returns non-trivial lines
        (10–100 characters, not cross-references or notes) as ability strings.

        Args:
            text: Raw text from the abilities/powers section.

        Returns:
            Up to 10 ability strings.
        """
        abilities = []

        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) < 100 and not line.endswith(':'):
                line = re.sub(r'^[\-\*\u2022]\s*', '', line)
                if line and not any(
                    skip in line.lower() for skip in ['see also', 'reference', 'note']
                ):
                    abilities.append(line)

        return abilities[:10]

    def scrape_characters(
        self,
        category: str = "Characters",
        max_chars: int = MAX_CHARACTERS_DEFAULT,
        progress_callback=None
    ) -> List[ScrapedCharacter]:
        """
        Scrape all characters from the given category up to ``max_chars``.

        First attempts to list members via the category API; falls back to a
        keyword search if no members are found.  Pages whose titles match
        known non-character patterns (episode, chapter, arc, etc.) are skipped.

        Args:
            category:          Category name to scrape (default ``'Characters'``).
            max_chars:         Maximum number of characters to return.
            progress_callback: Optional ``callable(current, total)`` invoked
                               after each page is processed.

        Returns:
            List of ScrapedCharacter instances.
        """
        print(f"Fetching character list from category: {category}")

        members = self.get_category_members(category, limit=max_chars * 2)

        if not members:
            print("Category not found, trying search...")
            members = self.search_pages("character", limit=max_chars)

        print(f"Found {len(members)} potential character pages")

        characters = []
        for i, member in enumerate(members):
            if len(characters) >= max_chars:
                break

            title = member["title"]

            skip_patterns = ['category:', 'template:', 'list of', 'episode',
                             'chapter', 'volume', 'arc']
            if any(skip in title.lower() for skip in skip_patterns):
                continue

            print(f"  [{i+1}/{len(members)}] Scraping: {title}...", end=" ", flush=True)

            char = self.get_character_page(title)
            if char:
                characters.append(char)
                print("\u2713")
            else:
                print("\u2717")

            if progress_callback:
                progress_callback(i + 1, len(members))

            # Polite delay — respects website ToS and avoids overwhelming the server
            time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

        return characters

    def get_story_info(self) -> Dict[str, Any]:
        """
        Retrieve basic story metadata from the wiki's main page.

        Attempts to read the page title from the ``<h1>`` or ``<title>``
        element.  Returns a minimal info dictionary if the main page cannot
        be fetched.

        Returns:
            Dictionary with ``title``, ``category``, ``genre``, and ``themes``
            keys.
        """
        response = self._get(f"{self.base_url}/wiki/Main_Page")

        info = {
            "title": self.wiki_name.replace("-", " ").title(),
            "category": "anime",
            "genre": [],
            "themes": [],
        }

        if response:
            soup = BeautifulSoup(response.text, 'html.parser')

            title_elem = soup.find('h1') or soup.find('title')
            if title_elem:
                title_text = title_elem.get_text()
                title_text = re.sub(r'\s*wiki\s*$', '', title_text, flags=re.I)
                title_text = re.sub(r'\s*\|.*$', '', title_text)
                if title_text:
                    info["title"] = title_text.strip()

        return info
