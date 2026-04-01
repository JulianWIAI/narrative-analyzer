"""
MALScraper.py
-------------
Defines the MALScraper class, which retrieves anime metadata and character
lists from MyAnimeList via the unofficial Jikan REST API (v4).  No API key
is required.  This scraper is shared between story_scraper_api.py and
story_scraper_html_fallback.py.
"""

import time
import random
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import quote

import requests

from SBS.ScrapedCharacter import ScrapedCharacter

MAX_CHARACTERS_DEFAULT = 50
MAX_RETRIES = 3

# Rotating user agents — used to reduce the risk of request throttling
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 '
    '(KHTML, like Gecko) Version/17.2 Safari/605.1.15',
]


class MALScraper:
    """
    Retrieves anime information and character lists from MyAnimeList via Jikan.

    Jikan (https://api.jikan.moe/v4) is an unofficial MyAnimeList REST API
    that requires no authentication.  This class wraps the ``/anime`` and
    ``/anime/{id}/characters`` endpoints, mapping the API response structure
    to the internal ScrapedCharacter format.

    Note:
        Jikan enforces strict rate limits (~3 req/s burst, 60 req/min).
        The ``_get`` method sleeps 1 second between retries to respect this.
    """

    def __init__(self):
        """Initialise the scraper with a Jikan base URL and a requests session."""
        self.api_base = "https://api.jikan.moe/v4"
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': random.choice(USER_AGENTS)})

    def _get(self, endpoint: str) -> Optional[dict]:
        """
        Perform a GET request to a Jikan API endpoint with automatic retries.

        Handles 429 (rate limited) responses by waiting 2–3 seconds before
        the next attempt.

        Args:
            endpoint: Path after the base URL (e.g. ``'anime?q=naruto&limit=1'``).

        Returns:
            Parsed JSON response dictionary, or ``None`` if all attempts fail.
        """
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
        """
        Search MyAnimeList for an anime by title and return the top result.

        Args:
            query: Anime title search string (e.g. ``'One Piece'``).

        Returns:
            The first result's data dictionary from the Jikan response, or
            ``None`` if nothing was found.
        """
        data = self._get(f"anime?q={quote(query)}&limit=1")
        if data and data.get("data"):
            return data["data"][0]
        return None

    def get_characters(self, anime_id: int) -> List[ScrapedCharacter]:
        """
        Retrieve the character list for a specific anime by its MAL ID.

        Maps the Jikan ``role`` field (``'Main'`` / ``'Supporting'``) to the
        internal role vocabulary (``'protagonist'`` / ``'supporting'``).

        Args:
            anime_id: The MyAnimeList numeric ID for the anime.

        Returns:
            A list of ScrapedCharacter instances (with minimal data — Jikan's
            character endpoint does not include full descriptions).
        """
        data = self._get(f"anime/{anime_id}/characters")

        if not data or not data.get("data"):
            return []

        characters = []
        for char_data in data["data"]:
            char_info = char_data.get("character", {})
            role = char_data.get("role", "").lower()

            # Map Jikan role strings to internal vocabulary
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

    def scrape_anime(
        self, query: str, max_chars: int = MAX_CHARACTERS_DEFAULT
    ) -> Tuple[Dict[str, Any], List[ScrapedCharacter]]:
        """
        Search for an anime and return its metadata together with its characters.

        Performs a search, then fetches the character list for the found anime.
        A 1-second sleep is inserted between requests to respect Jikan's rate
        limit.

        Args:
            query:     Anime title to search for.
            max_chars: Maximum number of characters to return.

        Returns:
            A ``(info, characters)`` tuple where ``info`` is a story metadata
            dictionary and ``characters`` is the truncated character list.
            Returns ``({}, [])`` if the anime is not found.
        """
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
        # Deliberate pause between the two API calls.
        # Jikan (api.jikan.moe) enforces a rate limit of ~3 requests/second and
        # 60 requests/minute.  This delay respects those limits and the Jikan ToS.
        # Randomisation prevents a fixed-interval fingerprint.
        time.sleep(random.uniform(1.0, 2.0))
        characters = self.get_characters(anime_id)

        print(f"Found {len(characters)} characters")

        return info, characters[:max_chars]
