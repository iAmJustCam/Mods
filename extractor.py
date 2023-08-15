#extractor.py module
# coding: utf-8
from bs4 import BeautifulSoup
import logging
from typing import Any, Callable, Dict, List, NamedTuple
import asyncio
from fetcher import AsyncFetcher, FetcherConfig
import aiocache

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Constants
CACHE_EXPIRATION = 3600  # 1 hour in seconds

# Exceptions
class ParsingError(Exception):
    """Exception raised for parsing related errors."""


class FetchingError(Exception):
    """Exception raised when fetching data fails."""


# NamedTuple for Matchup
Matchup = NamedTuple("Matchup", [("home", str), ("away", str), ("date", str)])


class Parser:
    """Utility class to parse HTML content."""

    @staticmethod
    def parse(
        html_content: str, categories: List[str], parsing_func: Callable
    ) -> Dict[str, Any]:
        if not html_content or not categories:
            raise ParsingError("Invalid input for parsing")
        return parsing_func(html_content, categories)


class TeamRankingExtractor:
    def __init__(self, fetcher: AsyncFetcher, cache: aiocache.SimpleMemoryCache):
        self.fetcher = fetcher
        self.cache = cache
        self.parser = Parser()

    async def fetch_and_extract(
        self,
        url: str,
        params: Dict[str, Any],
        categories: List[str],
        parsing_func: Callable,
    ) -> Dict[str, Any]:
        html_content = await self._fetch_content(url, params)
        if not html_content:
            raise FetchingError(f"Failed to fetch content from {url}")

        cache_key = (hash(html_content), frozenset(categories))
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data

        extracted_data = self.parser.parse(html_content, categories, parsing_func)
        await self.cache.set(cache_key, extracted_data, ttl=CACHE_EXPIRATION)
        return extracted_data

    async def _fetch_content(self, url: str, params: Dict[str, Any]) -> str:
        try:
            return await self.fetcher.fetch(url, params)
        except Exception as e:
            logging.error(f"Failed to fetch data from {url}. Reason: {e}")
            raise FetchingError from e

    async def clear_cache(self) -> None:
        await self.cache.clear()

    async def cache_stats(self) -> Dict[str, int]:
        return await self.cache.stats()


def sample_parsing_func(html_content: str, categories: List[str]) -> Dict[str, Any]:
    soup = BeautifulSoup(html_content, "html.parser")

    def _extract_category_rank(soup_obj: BeautifulSoup, category: str) -> Any:
        # As a placeholder, you would implement the logic here to parse the rank for a given category
        return soup_obj.find("div", class_=category).text

    return {cat: _extract_category_rank(soup, cat) for cat in categories}


if __name__ == "__main__":
    fetcher = AsyncFetcher(FetcherConfig(...))
    cache = aiocache.SimpleMemoryCache(max_size=100, ttl=CACHE_EXPIRATION)
    extractor = TeamRankingExtractor(fetcher, cache)
    asyncio.run(
        extractor.fetch_and_extract(
            "https://someurl.com",
            params={"some": "param"},
            categories=["Football", "Cricket"],
            parsing_func=sample_parsing_func,
        )
    )
