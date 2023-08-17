# evaluator.py
# coding: utf-8
import logging
import asyncio
from typing import Dict, List, Optional, Union, Type, Any
from datetime import datetime, timedelta
import aiohttp
from abc import ABC, abstractmethod
from multiprocessing import Pool

# Constants
DATE_FORMAT = "%Y-%m-%d"
CACHE_EXPIRATION_DAYS = 7
MAX_RETRIES = 3
BATCH_SIZE = 10  # Number of dates to process in parallel

# Setting up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Module level documentation
"""
Evaluator Module:

This module provides functionality for backtesting prediction models against historical data.
It includes utilities for data fetching, metrics calculation, and backtesting.

Architecture Overview:
- DateConverter: Utility for date string and datetime object conversions.
- MatchupDataCleaner: Cleans raw matchup data.
- ScheduleScraperStrategy: Abstract base class for schedule scraper strategies.
- DataFetcher: Fetches data asynchronously with caching.
- MetricsCalculator: Calculates metrics based on predictions.
- Backtester: Executes backtests, calculates metrics, and logs results.
"""

class DateFormatError(Exception):
    """Exception raised when there's an issue with date format conversion."""


class InvalidMatchupError(Exception):
    """Exception raised when matchup data is not as expected."""


class DateConverter:
    @staticmethod
    def to_date(date_str: str) -> Optional[datetime]:
        """Converts a string to a datetime object."""
        try:
            return datetime.strptime(date_str, DATE_FORMAT)
        except ValueError as e:
            logger.warning(f"Invalid date format for {date_str}: {e}")
            raise DateFormatError from e

    @staticmethod
    def to_string(date_obj: datetime) -> str:
        """Converts a datetime object to a string."""
        return date_obj.strftime(DATE_FORMAT)


class MatchupDataCleaner:
    @staticmethod
    def clean(raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Cleans raw matchup data."""
        cleaned_data = [
            matchup
            for matchup in raw_data
            if all(key in matchup for key in ["date", "home", "away"])
        ]
        logger.debug(f"Cleaned data: {cleaned_data}")
        return cleaned_data

class ScheduleScraperStrategy(ABC):
    """Abstract base class for schedule scraper strategies."""

    @abstractmethod
    async def fetch_schedule_data(self, session: aiohttp.ClientSession, date: str) -> List[Dict]:
        pass


class DataFetcher:
    def __init__(self, scraper: "ScheduleScraperStrategy"):
        """Initializes the DataFetcher with a scraper strategy."""
        self.scraper = scraper
        self.semaphore = asyncio.Semaphore(10)
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        self.cache_dates = set()

    async def fetch_data(self, session: aiohttp.ClientSession, date: str) -> List[Dict[str, Any]]:
        """Fetches data asynchronously."""
        retries = 3
        for i in range(retries):
            async with self.semaphore:
                result = await self.scraper.fetch_schedule_data(session, date)
                if result:
                    return result
                await asyncio.sleep(2**i)
        return []

    def invalidate_stale_cache(self) -> None:
        """Invalidates stale cache entries."""
        current_date = datetime.today().date()
        stale_dates = {
            date
            for date in self.cache_dates
            if DateConverter.to_date(date).date() + timedelta(days=CACHE_EXPIRATION_DAYS)
            < current_date
        }

        for date in stale_dates:
            self._cache.pop(date, None)
            self.cache_dates.remove(date)

    def __repr__(self) -> str:
        return f"<DataFetcher with {len(self._cache)} cached items>"

class MetricsCalculator:
    def __init__(self):
        """Initializes the MetricsCalculator."""
        pass

    def calculate_metrics(self, correct_predictions: int, total_predictions: int) -> Dict[str, float]:
        """Calculates accuracy, precision, recall, and F1 score."""
        accuracy = correct_predictions / total_predictions if total_predictions else 0
        precision = correct_predictions / total_predictions if total_predictions else 0
        recall = correct_predictions / total_predictions if total_predictions else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) else 0

        return {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1_score
        }

    def __repr__(self) -> str:
        return "<MetricsCalculator>"

class Backtester:
    def __init__(self, backtest_period: int, scraper: "ScheduleScraperStrategy", predictor: Optional[Type] = None):
        """Initializes the Backtester with a period, scraper strategy, and optional predictor."""
        if backtest_period <= 0:
            raise ValueError("Backtest period must be positive.")
        self.backtest_period = backtest_period
        self.data_fetcher = DataFetcher(scraper)
        self.predictor = predictor

    async def _execute_single_backtest(self, date: str) -> List[Dict[str, Any]]:
        """Executes a single backtest for a specific date."""
        async with aiohttp.ClientSession() as session:
            for _ in range(MAX_RETRIES):
                data = await self.data_fetcher.fetch_data(session, date)
                if data:
                    return data
        return []

    async def _parallel_backtest(self, date_range: List[str]) -> List[List[Dict[str, Any]]]:
        """Executes backtests in parallel for a range of dates."""
        tasks = [self._execute_single_backtest(date) for date in date_range]
        results = await asyncio.gather(*tasks)
        return results


    async def execute_backtest(self) -> Dict[str, Union[float, Dict[str, float]]]:
        """Executes the backtest and returns metrics."""
        start_time = datetime.now()

        end_date = datetime.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=self.backtest_period - 1)
        date_values = [
            (start_date + timedelta(days=i)).strftime(DATE_FORMAT)
            for i in range((end_date - start_date).days + 1)
        ]

        all_results = self._parallel_backtest(date_values)

        # Flatten the results
        schedule_data = [MatchupDataCleaner.clean(data) for sublist in all_results for data in sublist]

        correct_predictions = sum(1 for matchup in schedule_data if matchup["home"] > matchup["away"])
        total_predictions = len(schedule_data)

        win_rate = correct_predictions / total_predictions if total_predictions else 0
        metrics_calculator = MetricsCalculator()
        metrics = metrics_calculator.calculate_metrics(correct_predictions, total_predictions)

        # Logging
        logger.info(f"Backtest results for period {self.backtest_period}: {metrics}")

        return {"win_rate": win_rate, "metrics": metrics}

    def __repr__(self) -> str:
        return f"<Backtester for period {self.backtest_period}>"
