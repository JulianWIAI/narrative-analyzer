"""
FandomScraperHTML.py
--------------------
Defines the FandomScraperHTML class, an HTML-parsing fallback scraper for
Fandom wikis.  Unlike FandomScraper (which uses the MediaWiki REST API),
this class bypasses API-level blocks by requesting ordinary HTML pages and
parsing them with BeautifulSoup.  Additional techniques — rotating user
agents, random inter-request delays, and Cloudflare challenge detection —
make it more resilient to bot-protection measures.
"""

import re
import time
import random
from typing import Dict, List, Optional, Any
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

from SBS.ScrapedCharacter import ScrapedCharacter

# ---------------------------------------------------------------------------
# Module-level configuration
# ---------------------------------------------------------------------------

DELAY_MIN = 1.0
DELAY_MAX = 2.5
MAX_CHARACTERS_DEFAULT = 50
MAX_RETRIES = 3

# Five real browser user-agent strings cycled randomly to reduce fingerprinting
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 '
    '(KHTML, like Gecko) Version/17.2 Safari/605.1.15',
]

# Trait and role detection — same keyword tables as FandomScraper
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

ROLE_PATTERNS = {
    "protagonist": [
        r"main\s*(character|protagonist)",
        r"is\s*the\s*(hero|protagonist)",
        r"series\s*follows",
    ],
    "antagonist": [
        r"main\s*(villain|antagonist|enemy)",
        r"is\s*the\s*(villain|antagonist)",
        r"arch[\s-]?enemy",
    ],
    "mentor": [
        r"mentor",
        r"teaches?\s*(the\s*)?(protagonist|hero|main)",
        r"trains?\s*(the\s*)?(protagonist|hero|main)",
    ],
    "rival": [r"rival", r"competes?\s*with", r"nemesis"],
    "sidekick": [r"sidekick", r"companion", r"best\s*friend", r"partner"],
}


class FandomScraperHTML:
    """
    Fandom wiki scraper using direct HTML parsing (API-bypass strategy).

    This class targets the same Fandom wikis as FandomScraper but avoids the
    MediaWiki API entirely.  Instead it:
    1. Randomly rotates the User-Agent header on ~30 % of requests.
    2. Introduces a random delay (1.0–2.5 s) between every request.
    3. Detects Cloudflare challenge pages and retries after a longer wait.
    4. Falls back to multiple HTML selectors to handle varying wiki layouts.

    Use this scraper when ``FandomScraper`` is blocked (HTTP 403 or empty API
    results) for a particular wiki.
    """

    def __init__(self, wiki_name: str):
        """
        Initialise the scraper for the given Fandom wiki.

        Args:
            wiki_name: Subdomain of the target wiki (e.g. ``'naruto'``).
        """
        self.wiki_name = wiki_name
        self.base_url = f"https://{wiki_name}.fandom.com"
        self.session = requests.Session()
        self._update_headers()

    def _update_headers(self):
        """
        Assign a random browser user-agent and a full set of browser-like
        request headers to the session.

        Called on initialisation and optionally on subsequent requests to
        rotate the apparent browser identity.
        """
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
        """
        Sleep for a uniformly random duration between DELAY_MIN and DELAY_MAX seconds.

        The delay is intentionally randomised (rather than fixed) to produce
        human-like request spacing, which both reduces server load and complies
        with Fandom's Terms of Service on automated access.  Never remove or
        shorten this delay when scraping live wikis.
        """
        time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    def _get(self, url: str, retries: int = MAX_RETRIES) -> Optional[requests.Response]:
        """
        Perform a GET request with automatic retries, user-agent rotation,
        and Cloudflare detection.

        On each attempt there is a 30 % chance of rotating the user-agent.
        Cloudflare challenge pages (detected by ``'challenge'`` in the first
        1000 characters) trigger a 5-second wait and a retry.  HTTP 429
        responses trigger a 10-second wait; 403 responses trigger a
        user-agent rotation and a 3-second wait.

        Args:
            url:     Full URL to request.
            retries: Maximum number of attempts.

        Returns:
            A successful ``requests.Response`` object, or ``None``.
        """
        for attempt in range(retries):
            try:
                if random.random() < 0.3:
                    self._update_headers()

                response = self.session.get(url, timeout=30)

                if response.status_code == 200:
                    # Check for Cloudflare challenge page
                    if ('challenge' in response.text.lower()[:1000] or
                            'cf-' in response.text.lower()[:1000]):
                        print("  Cloudflare detected, waiting...")
                        time.sleep(5)
                        continue
                    return response
                elif response.status_code == 429:
                    print("  Rate limited, waiting...")
                    time.sleep(10)
                elif response.status_code == 403:
                    print("  Blocked (403), trying different UA...")
                    self._update_headers()
                    time.sleep(3)
            except Exception as e:
                if attempt == retries - 1:
                    print(f"  Error: {e}")

            self._delay()

        return None

    def get_character_list_from_category_page(
        self, category: str = "Characters"
    ) -> List[Dict[str, str]]:
        """
        Scrape the HTML category page to obtain a list of character page links.

        Tries multiple URL formats and three different CSS selector strategies
        (``category-page__member-link``, ``#mw-pages``, and
        ``category-page__members``) to handle the variety of Fandom wiki
        layouts.

        Args:
            category: Category name (default ``'Characters'``).

        Returns:
            List of ``{'title': ..., 'url': ...}`` dictionaries.
        """
        characters = []

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

            # Strategy 1: Fandom-specific member link class
            for link in soup.find_all('a', class_='category-page__member-link'):
                title = link.get('title', '') or link.get_text().strip()
                href = link.get('href', '')
                if title and href and not self._should_skip(title):
                    characters.append({"title": title, "url": urljoin(self.base_url, href)})

            # Strategy 2: Standard MediaWiki category listing
            category_div = soup.find('div', id='mw-pages') or soup.find('div', class_='mw-category')
            if category_div:
                for link in category_div.find_all('a'):
                    title = link.get('title', '') or link.get_text().strip()
                    href = link.get('href', '')
                    if title and href and not self._should_skip(title):
                        entry = {"title": title, "url": urljoin(self.base_url, href)}
                        if entry not in characters:
                            characters.append(entry)

            # Strategy 3: Fandom members container div
            members_div = soup.find('div', class_='category-page__members')
            if members_div:
                for link in members_div.find_all('a'):
                    title = link.get('title', '') or link.get_text().strip()
                    href = link.get('href', '')
                    if title and href and not self._should_skip(title):
                        entry = {"title": title, "url": urljoin(self.base_url, href)}
                        if entry not in characters:
                            characters.append(entry)

            if characters:
                break

            self._delay()

        return characters

    def get_characters_from_list_page(
        self, list_page: str = "List_of_characters"
    ) -> List[Dict[str, str]]:
        """
        Scrape a ``List of characters`` wiki page to obtain character links.

        Tries several common list-page URL patterns and extracts all
        ``/wiki/`` links from the main content area.

        Args:
            list_page: Primary page name to try first.

        Returns:
            List of ``{'title': ..., 'url': ...}`` dictionaries.
        """
        characters = []

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
            content = soup.find('div', class_='mw-parser-output')
            if not content:
                continue

            for link in content.find_all('a'):
                href = link.get('href', '')
                title = link.get('title', '') or link.get_text().strip()

                if not href or not title:
                    continue
                if href.startswith('#') or 'Category:' in href or 'File:' in href:
                    continue
                if self._should_skip(title):
                    continue

                if '/wiki/' in href:
                    entry = {"title": title, "url": urljoin(self.base_url, href)}
                    if entry not in characters:
                        characters.append(entry)

            if characters:
                print(f"  Found {len(characters)} potential characters")
                break

            self._delay()

        return characters

    def _should_skip(self, title: str) -> bool:
        """
        Determine whether a page title should be excluded from the character list.

        Filters out administrative, structural, and non-character pages by
        checking for known skip keywords.

        Args:
            title: Wiki page title string.

        Returns:
            ``True`` if the page should be skipped, ``False`` otherwise.
        """
        skip_patterns = [
            'category:', 'template:', 'file:', 'image:', 'list of',
            'episode', 'chapter', 'volume', 'arc', 'saga', 'gallery',
            'navigation', 'main page', 'wiki', 'help:', 'user:',
            'special:', 'talk:', 'disambiguation'
        ]
        title_lower = title.lower()
        return any(skip in title_lower for skip in skip_patterns)

    def get_character_page(
        self, url: str, title: str
    ) -> Optional[ScrapedCharacter]:
        """
        Scrape a single character wiki page and return the parsed data.

        Fetches the page, looks for a first meaningful paragraph as the
        description (skipping very short or citation-only paragraphs), then
        parses the infobox and runs trait/role detection heuristics.
        Only characters that yield a non-empty description are kept (checked
        by the caller in ``scrape_characters``).

        Args:
            url:   Full URL of the character page.
            title: Display title used as the character name.

        Returns:
            A populated ScrapedCharacter instance, or ``None`` if the page
            could not be fetched.
        """
        response = self._get(url)

        if not response:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        infobox = (
            soup.find('aside', class_='portable-infobox') or
            soup.find('table', class_='infobox') or
            soup.find('div', class_='infobox')
        )

        character = ScrapedCharacter(name=title, url=url)

        # Extract the first paragraph with meaningful content
        content = soup.find('div', class_='mw-parser-output')
        if content:
            for p in content.find_all('p', recursive=False):
                text = p.get_text().strip()
                if text and len(text) > 50 and not text.startswith('['):
                    character.description = text[:1000]
                    break

        if infobox:
            character = self._parse_infobox(infobox, character)

        if character.description:
            character.traits = self._detect_traits(character.description)
            detected_role = self._detect_role(character.description)
            if detected_role != "supporting":
                character.role = detected_role

        abilities_header = soup.find(
            ['h2', 'h3'],
            string=re.compile(r'abilities|powers|skills|techniques', re.I)
        )
        if abilities_header:
            abilities_content = []
            for sibling in abilities_header.find_next_siblings():
                if sibling.name in ['h2', 'h3']:
                    break
                abilities_content.append(sibling.get_text())
            character.abilities = self._extract_abilities(' '.join(abilities_content))

        return character

    def _parse_infobox(
        self, infobox, character: ScrapedCharacter
    ) -> ScrapedCharacter:
        """
        Extract structured character fields from a Fandom portable infobox.

        Handles both the modern ``data-source`` attribute format and the
        classic ``label`` / ``value`` class-based format, as well as plain
        ``<th>`` / ``<td>`` table rows used by older wikis.

        Args:
            infobox:   BeautifulSoup element for the infobox.
            character: ScrapedCharacter to populate in-place.

        Returns:
            The updated ScrapedCharacter instance.
        """
        for item in infobox.find_all(['div', 'tr', 'section']):
            label_elem = item.find(
                ['h3', 'th', 'div'],
                class_=lambda c: c and (
                    'label' in str(c).lower() or 'pi-data-label' in str(c).lower()
                )
            )
            value_elem = item.find(
                ['div', 'td'],
                class_=lambda c: c and (
                    'value' in str(c).lower() or 'pi-data-value' in str(c).lower()
                )
            )

            if not label_elem:
                label_elem = item.find('th')
            if not value_elem:
                value_elem = item.find('td')

            # Modern Fandom infobox: data-source attribute carries the field name
            if not label_elem and item.get('data-source'):
                label = item.get('data-source', '').lower()
                value_elem = item.find(
                    ['div'], class_=lambda c: c and 'value' in str(c).lower()
                )
                if value_elem:
                    value = value_elem.get_text().strip()
                    self._apply_infobox_value(character, label, value)
                continue

            if label_elem and value_elem:
                label = label_elem.get_text().strip().lower()
                value = value_elem.get_text().strip()
                self._apply_infobox_value(character, label, value)

        return character

    def _apply_infobox_value(
        self, character: ScrapedCharacter, label: str, value: str
    ):
        """
        Map a single infobox label/value pair to the appropriate character field.

        Args:
            character: The ScrapedCharacter to update.
            label:     Normalised lower-case label string.
            value:     Raw text value from the infobox cell.
        """
        if any(g in label for g in ['gender', 'sex']):
            if 'female' in value.lower() or 'woman' in value.lower() or 'girl' in value.lower():
                character.gender = 'female'
            elif 'male' in value.lower() or 'man' in value.lower() or 'boy' in value.lower():
                character.gender = 'male'

        if any(s in label for s in ['species', 'race', 'type', 'classification']):
            character.species = value.split(',')[0].strip().lower()[:50]

        if 'hair' in label:
            character.hair_color = value.split(',')[0].strip().lower()[:30]

        if any(o in label for o in ['occupation', 'job', 'profession', 'position', 'rank', 'title']):
            character.occupation = value.split(',')[0].strip()[:100]

        if any(a in label for a in ['affiliation', 'team', 'group', 'crew', 'organization', 'village', 'clan']):
            affiliations = [a.strip() for a in re.split(r'[,\n]', value) if a.strip()]
            character.affiliations.extend(affiliations[:5])

        if any(f in label for f in ['family', 'relative', 'parent', 'status']):
            if any(w in value.lower() for w in ['unknown', 'deceased', 'none', 'orphan', 'dead']):
                character.family_status = 'orphan'

    def _detect_traits(self, text: str) -> List[str]:
        """
        Scan description text for known trait keywords.

        Args:
            text: Character description text.

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

        Args:
            text: Character description text.

        Returns:
            Role string, defaulting to ``'supporting'``.
        """
        text_lower = text.lower()

        for role, patterns in ROLE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return role

        return "supporting"

    def _extract_abilities(self, text: str) -> List[str]:
        """
        Extract ability names from an abilities/powers/skills section.

        Accepts lines between 10 and 80 characters long that are not
        cross-references, notes, or edit links.

        Args:
            text: Raw text of the abilities section.

        Returns:
            Up to 10 ability strings.
        """
        abilities = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if line and 10 < len(line) < 80:
                line = re.sub(r'^[\-\*\u2022:]\s*', '', line)
                if line and not any(
                    skip in line.lower() for skip in ['see also', 'reference', 'note', 'edit']
                ):
                    abilities.append(line)

        return abilities[:10]

    def scrape_characters(
        self,
        category: str = "Characters",
        max_chars: int = MAX_CHARACTERS_DEFAULT
    ) -> List[ScrapedCharacter]:
        """
        Scrape characters from the wiki, trying category pages first then list pages.

        Only characters whose pages yield a non-empty description are retained,
        ensuring that navigation stubs or disambiguation pages are excluded.

        Args:
            category:  Category name to try first (default ``'Characters'``).
            max_chars: Maximum number of characters to return.

        Returns:
            List of ScrapedCharacter instances.
        """
        print(f"\nFetching character list...")

        members = self.get_character_list_from_category_page(category)

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
            if char and char.description:  # Only keep characters with scraped content
                characters.append(char)
                print("\u2713")
            else:
                print("\u2717 (no content)")

            self._delay()

        return characters

    def get_story_info(self) -> Dict[str, Any]:
        """
        Retrieve basic story metadata from the wiki's main page.

        Attempts to read the ``og:site_name`` meta tag for a clean title.
        Falls back to a title derived from the wiki subdomain name.

        Returns:
            Dictionary with ``title``, ``category``, ``genre``, and
            ``themes`` keys.
        """
        response = self._get(f"{self.base_url}/wiki/Main_Page")

        info = {
            "title": self.wiki_name.replace("-", " ").replace("_", " ").title(),
            "category": "anime",
            "genre": [],
            "themes": [],
        }

        if response:
            soup = BeautifulSoup(response.text, 'html.parser')

            og_title = soup.find('meta', property='og:site_name')
            if og_title:
                title = og_title.get('content', '')
                title = re.sub(r'\s*wiki\s*$', '', title, flags=re.I).strip()
                if title:
                    info["title"] = title

        return info
