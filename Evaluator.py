#evaluator.py module
# coding: utf-8
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import aiohttp
from aiohttp import ClientSession

# Constants
DATE_FORMAT = "%Y-%m-%d"
CACHE_EXPIRATION_DAYS = 7  # Define a cache expiration time in days

# Setting up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DateFormatError(Exception):
    """Raised when there is an issue with date format conversion."""


class InvalidMatchupError(Exception):
    """Raised when matchup data is not as expected."""


class DateConverter:
    @staticmethod
    def to_date(date_str: str) -> Optional[datetime]:
        try:
            return datetime.strptime(date_str, DATE_FORMAT)
        except ValueError as e:
            logger.warning(f"Invalid date format for {date_str}: {e}")
            raise DateFormatError from e

    @staticmethod
    def to_string(date_obj: datetime) -> str:
        return date_obj.strftime(DATE_FORMAT)


class MatchupDataCleaner:
    @staticmethod
    def clean(raw_data: List[Dict]) -> List[Dict]:
        return [
            matchup
            for matchup in raw_data
            if matchup.get("date") and matchup.get("home") and matchup.get("away")
        ]


class MatchupManager:
    def __init__(self, backtest_period: int, scraper: "ScheduleScraperStrategy"):
        self.backtest_period = backtest_period
        self.scraper = scraper
        self.semaphore = asyncio.Semaphore(10)
        self.cache = {}
        self.cache_dates = set()  # To track dates of data in cache

    async def get_schedule(self) -> Dict[str, List[Dict]]:
        end_date = datetime.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=self.backtest_period - 1)
        date_values = [
            (start_date + timedelta(days=i)).strftime(DATE_FORMAT)
            for i in range((end_date - start_date).days + 1)
        ]
        schedule_data = []

        async with aiohttp.ClientSession() as session:
            tasks = [self._fetch_data(session, date) for date in date_values]
            results = await asyncio.gather(*tasks)

            for date, daily_schedule in zip(date_values, results):
                if not daily_schedule:
                    logger.warning(f"Consistent data miss for date: {date}")
                cleaned_data = MatchupDataCleaner.clean(daily_schedule)
                self.cache[date] = cleaned_data
                self.cache_dates.add(date)
                schedule_data.extend(cleaned_data)

        self._invalidate_stale_cache()
        return {"matchups": schedule_data}

    async def _fetch_data(self, session: ClientSession, date: str) -> List[Dict]:
        retries = 3
        for i in range(retries):
            async with self.semaphore:
                result = await self.scraper.fetch_schedule_data(session, date)
                if result:
                    return result
                await asyncio.sleep(2**i)
        return []

    def _invalidate_stale_cache(self):
        today = datetime.today().date()
        stale_dates = {
            date for date in self.cache_dates
            if DateConverter.to_date(date) + timedelta(days=CACHE_EXPIRATION_DAYS) < today
        }

        for date in stale_dates:
            self.cache.pop(date, None)
            self.cache_dates.remove(date)


class Backtester:
    def __init__(self, backtest_period: int, scraper: "ScheduleScraperStrategy"):
        self.backtest_period = backtest_period
        self.scraper = scraper
        self.matchup_manager = MatchupManager(backtest_period, scraper)
        
    async def execute_backtest(self):
        data = await self.matchup_manager.get_schedule()
        # Actual backtesting logic and interaction with other modules would go here.
        # For example:
        #   1. Use PointsProjector to project scores.
        #   2. Fetch player rankings with RankingsFetcher.
        #   3. Calculate scores with ScoringCalculator.
        #   4. Compare the projected scores with actuals.
        #   5. Return results such as win rate, accuracy, etc.
        return {"win_rate": 0.75, "accuracy": 0.82, "precision": 0.80}


# Testing should include both unit and integration tests. 
def test_end_to_end():
    # Testing logic should go here.
    pass
