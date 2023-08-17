#scraper.py
# coding: utf-8
import aiohttp
from bs4 import BeautifulSoup
import logging
from cacher import Cache, CacheBackend, CacheStorage
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class ScraperError(Exception):
    """Custom exception for scraper errors."""

class BaseScraper(ABC):
    """Base class for all scraper strategies."""

    def __init__(self, cache_backend: Optional[CacheBackend] = None):
        self.cache_backend = cache_backend

    @abstractmethod
    async def scrape(self, url: str, *args, **kwargs) -> BeautifulSoup:
        """Scrape the content of the provided URL."""
        pass

class AsyncScraper(BaseScraper):
    """Async scraper using aiohttp and BeautifulSoup."""

    async def scrape(self, url: str, *args, **kwargs) -> BeautifulSoup:
        if self.cache_backend:
            cached_content = await self.cache_backend.get(url)
            if cached_content:
                return BeautifulSoup(cached_content, 'html.parser')

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    content = await response.text()
                    if self.cache_backend:
                        await self.cache_backend.put(url, content)
                    return BeautifulSoup(content, 'html.parser')
            except aiohttp.ClientError as e:
                logging.error(f"Failed to scrape {url}. Reason: {e}")
                raise ScraperError(f"Failed to scrape {url}") from e

# Additional scraper strategies can be added here
