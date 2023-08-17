#fetcher.py
# coding: utf-8
import logging
import re
import asyncio

# Third Party Imports
import aiohttp
from aiohttp import ClientSession
from tenacity import retry, wait_exponential, stop_after_attempt
from bs4 import BeautifulSoup
from extractor import Matchup, TeamRankingExtractor
from typing import Callable, Dict, List, Any, Optional
from cacher import Cache, CacheBackend

# Setting up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class AsyncFetcher:
    def __init__(self, session=None, http_timeout=10):
        self.session = session or aiohttp.ClientSession()
        self.http_timeout = http_timeout
        backend = CacheBackend(capacity=100)  # Set up the cache backend
        self.cache = Cache(backend=backend, ttl=3600)  # Set up the cache with a TTL of 1 hour

    async def fetch(self, url: str) -> str:
        cached_response = await self.cache.get(url)
        if cached_response:
            logger.info(f"Cache hit for URL: {url}")
            return cached_response

        try:
            async with self.session.get(url, timeout=self.http_timeout) as response:
                response.raise_for_status()
                content = await response.text()
                await self.cache.set(url, content)
                logger.info(f"Fetched data from URL: {url}")
                return content
        except aiohttp.ClientResponseError as e:
            logger.error(f"HTTP error {e.status} when fetching {url}")
            raise
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            raise

    async def close(self):
        await self.session.close()


class ScheduleScraperStrategy:
    ttl = 3600  # Default 1 hour
    max_size = 1000  # Default size

    async def fetch_schedule_data(self, session: ClientSession, date_value: str, page: int = 1) -> List[Matchup]:
        raise NotImplementedError()

class MlbScheduleScraper(ScheduleScraperStrategy):
    ttl = 60 * 60  # 1 hour
    max_size = 10000

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10), reraise=True)
    async def fetch_schedule_data(self, session: ClientSession, date_value: str, page: int = 1) -> List[Matchup]:
        url = f"https://www.teamrankings.com/mlb/schedules/?date={date_value}&page={page}"
        logger.info("Fetching schedule from: %s", url)

        response = await session.get(url)
        if response.status != 200:
            logger.error(f"HTTP error {response.status}: {response.reason}")
            response.raise_for_status()
        schedule_html = await response.text()

        soup = BeautifulSoup(schedule_html, "html.parser")
        schedule_data = [
            Matchup(date=date_value, home=home_team, away=away_team)
            for td in soup.find_all("td", {"class": "text-left nowrap"})
            for link in td.find_all("a")
            if "matchup" in link.get("href")
            for home_team, away_team in [re.sub(r"#[0-9]*", "", link.string).strip().split(" at ")]
        ]
        return schedule_data

class FetcherConfig:
    def __init__(self, concurrent_limit: int = 10, retries: int = 3, timeout: int = 10, retry_strategy: Callable = None):
        self.concurrent_limit = concurrent_limit
        self.retries = retries
        self.timeout = timeout
        self.retry_strategy = retry_strategy or self.default_retry_strategy

    @staticmethod
    def default_retry_strategy(attempt: int) -> float:
        return 2**attempt

class Fetcher:
    def __init__(self, config: FetcherConfig, url: str):
        self.url = url
        self._semaphore = asyncio.Semaphore(config.concurrent_limit)
        self.retries = config.retries
        self.timeout = config.timeout
        self.retry_strategy = config.retry_strategy
        backend = CacheBackend(capacity=100)
        self.error_cache = Cache(backend=backend, ttl=3600)
        self.latency = []
        self.session = aiohttp.ClientSession()



    async def _make_request(self, url: str, params: Dict[str, Any]) -> Optional[str]:
        for attempt in range(self.retries):
            try:
                async with self._semaphore, self.session.get(url, params=params, timeout=self.timeout) as response:
                    self.latency.append(response.elapsed.total_seconds())
                    return await response.text()
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                wait_time = await self.retry_strategy(attempt)
                logger.warning(f"Attempt {attempt + 1} failed for {url}. Error: {e}. Retrying after {wait_time} seconds...")
                await asyncio.sleep(wait_time)
        return None

    async def fetch(self, url: str, params: Dict[str, Any]) -> Optional[str]:
        content = await self._make_request(url, params)
        if not content or "no data available" in content.lower():
            logger.error(f"No relevant data found in {url}")
            return None
        return content

    def metrics(self) -> Dict[str, Any]:
        avg_latency = sum(self.latency) / len(self.latency) if self.latency else 0
        return {"average_latency": avg_latency, "errors": len(self.error_cache.keys())}

class RankingsFetcher:
    def __init__(self, sport_url: str, extractor: TeamRankingExtractor, config_manager: Any):
        self.BASE_URL = sport_url
        self.extractor = extractor
        self.config_manager = config_manager
        backend = CacheBackend(capacity=100)
        self.rankings_cache = Cache(backend=backend, ttl=3600)

    async def get_or_fetch_rank(self, session: ClientSession, team: str) -> Dict[str, Any]:
        ranks = await self.rankings_cache.get(team)
        if ranks is None:
            ranks = await self._fetch_rank(session, team)
            await self.rankings_cache.set(team, ranks)
        return ranks

    @retry(wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _fetch_rank(self, session: ClientSession, team: str) -> Dict[str, Any]:
        return await self.extractor.fetch_and_extract(session, self.construct_url(team), team, self.config_manager.get_scoring_categories())

    def construct_url(self, team: str) -> str:
        return f"{self.BASE_URL}{team.lower().replace(' ', '-')}-stats"

if __name__ == "__main__":
    fetcher_config = FetcherConfig()
