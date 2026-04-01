"""
StoryCategory.py
----------------
Defines the StoryCategory enumeration used to classify the medium or format
of a story within the Narrative Pattern Analyzer.
"""

from enum import Enum


class StoryCategory(Enum):
    """
    Enumeration of supported story media categories.

    Storing the category as a controlled vocabulary makes it straightforward
    to filter or group stories by medium when generating cross-media reports
    and comparisons.

    Values:
        ANIME:    Japanese animated series.
        MANGA:    Japanese comic / graphic novel.
        GAME:     Video game narrative.
        MOVIE:    Feature-length film.
        TV_SHOW:  Live-action or western animated television series.
        BOOK:     Novel or written prose work.
        COMIC:    Western comic book or graphic novel.
        OTHER:    Any medium not covered by the above categories.
    """

    ANIME = "anime"
    MANGA = "manga"
    GAME = "game"
    MOVIE = "movie"
    TV_SHOW = "tv_show"
    BOOK = "book"
    COMIC = "comic"
    OTHER = "other"
