# coding: utf-8
# extractor.py
from bs4 import BeautifulSoup
import logging
from typing import Any, Callable, Dict, List, NamedTuple
import asyncio

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Constants
CACHE_EXPIRATION = 3600  # 1 hour in seconds

class ParsingError(Exception):
    pass

class FetchingError(Exception):
    pass

Matchup = NamedTuple("Matchup", [("home", str), ("away", str), ("date", str)])

class DataTransformer:

    @staticmethod
    def transform(html_content: str, categories: List[str], parsing_func: Callable) -> Dict[str, Any]:
        if not html_content or not categories:
            raise ParsingError("Invalid input for transformation")
        return parsing_func(html_content, categories)

class DataExtractor:

    def __init__(self, fetcher: "AsyncFetcher", cache: "Cache"):
        self.fetcher = fetcher
        self.cache = cache

    async def fetch_content(self, url: str, params: Dict[str, Any]) -> str:
        try:
            return await self.fetcher.fetch(url, params)
        except Exception as e:
            logging.error(f"Failed to fetch data from {url}. Reason: {e}")
            raise FetchingError from e

    async def clear_cache(self) -> None:
        await self.cache.clear()

    async def cache_stats(self) -> Dict[str, int]:
        return await self.cache.stats()

class TeamRankingService:

    def __init__(self, extractor: "DataExtractor", transformer: "DataTransformer", cache: "Cache"):
        self.extractor = extractor
        self.transformer = transformer
        self.cache = cache

    async def fetch_and_transform(self, url: str, params: Dict[str, Any], categories: List[str], parsing_func: Callable) -> Dict[str, Any]:
        html_content = await self.extractor.fetch_content(url, params)
        if not html_content:
            raise FetchingError(f"Failed to fetch content from {url}")

        cache_key = (hash(html_content), frozenset(categories))
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            return cached_data

        transformed_data = self.transformer.transform(html_content, categories, parsing_func)
        await self.cache.put(cache_key, transformed_data)
        return transformed_data

def sample_parsing_func(html_content: str, categories: List[str]) -> Dict[str, Any]:
    soup = BeautifulSoup(html_content, "html.parser")
    return {cat: soup.find("div", class_=cat).text for cat in categories}

if __name__ == "__main__":
    from fetcher import AsyncFetcher
    from cacher import Cache, CacheBackend

    fetcher = AsyncFetcher()
    backend = CacheBackend(capacity=100)
    cache = Cache(backend=backend, ttl=CACHE_EXPIRATION)
    extractor = DataExtractor(fetcher, cache)
    transformer = DataTransformer()
    service = TeamRankingService(extractor, transformer, cache)
    asyncio.run(
        service.fetch_and_transform(
            "https://someurl.com",
            params={"some": "param"},
            categories=["Football", "Cricket"],
            parsing_func=sample_parsing_func,
        )
    )
