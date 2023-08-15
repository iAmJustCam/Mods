# coding: utf-8
# main.py
import asyncio
from argparse import ArgumentParser
from datetime import datetime, timedelta
from time import time

from trainer import MachineLearning
from prompter import Prompter, ScheduleScraperStrategy
from logger import get_logger, setup_logging
from constants import CONSTANTS
from fetcher import ScheduleFetcher, StatsFetcher, ResultsFetcher
from cacher import Cache, CacheBackend
from config import ConfigurationManager

# Argument Parsing
parser = ArgumentParser(description="Execution Module for the System")
parser.add_argument(
    "--backtest-period", type=int, default=7, help="Backtest period in days"
)
parser.add_argument(
    "--config-file",
    type=str,
    default="config.ini",
    help="Path to the configuration file",
)
parser.add_argument(
    "--log-file", type=str, default="log.txt", help="Path to the log file"
)
args = parser.parse_args()

# Setup Logging and Configuration
setup_logging(log_file_name=args.log_file)
logger = get_logger(__name__)
config_manager = ConfigurationManager(config_file=args.config_file)

# Cache Setup
cache_backend = CacheBackend(capacity=CONSTANTS.CACHE_SIZE)
cache = Cache(backend=cache_backend)

# Prompter Setup
scraper_instance = (
    ScheduleScraperStrategy()
)  # Assuming this is initialized without arguments
prompter = Prompter(scraper_instance, interactive_mode=True)
prompter.run()  # This will prompt the user for various configurations

# Setup Logging and Configuration
setup_logging(log_file_name=args.log_file)
logger = get_logger(__name__)
config_manager = ConfigurationManager(config_file=args.config_file)

# Cache Setup
cache_backend = CacheBackend(capacity=CONSTANTS.CACHE_SIZE)
cache = Cache(backend=cache_backend)

# Retry Decorator
def retry(attempts=3, delay=5):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for attempt in range(attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    error_msg = (
                        f"Error in {func.__name__}: {e}. "
                        f"Retrying in {delay} seconds..."
                    )
                    logger.error(error_msg)
                    await asyncio.sleep(delay)
            logger.error(
                f"Failed to execute {func.__name__} after {attempts} attempts."
            )

        return wrapper

    return decorator


# Main Execution Function
async def main():
    backtest_period = prompter.backtest_period
    start_date = datetime.now() - timedelta(days=backtest_period)
    schedule_fetcher = ScheduleFetcher(config_manager, cache)
    stats_fetcher = StatsFetcher(config_manager, cache)
    results_fetcher = ResultsFetcher(config_manager, cache)
    ml_model = MachineLearning()

    for day in range(backtest_period):
        date = start_date + timedelta(days=day)
        start_time = time()
        matchups = await schedule_fetcher.get_matchups(date)
        latency = time() - start_time
        logger.info(f"Fetched matchups for {date} in {latency} seconds.")

        if not matchups:
            logger.info(f"No games found for {date}. Skipping...")
            continue

        # Fetch stats and process matchups concurrently
        tasks = [process_matchup(matchup, stats_fetcher, date) for matchup in matchups]
        matchups_data = await asyncio.gather(*tasks)

        results = await results_fetcher.get_results(date)
        projected_winners = [data["projected_winner"] for data in matchups_data]

        features, labels = ml_model.load_training_data(projected_winners, results)
        features = ml_model.preprocess_data(features)
        ml_model.evaluate_models(features, labels)
        ml_model.tune_hyperparams(features, labels)
        ml_model.train_model(features, labels)
        accuracy = ml_model.evaluate_model(features, labels)

        logger.info(f"Model accuracy for {date}: {accuracy}")

    logger.info("Backtesting and training completed.")


@retry()
async def process_matchup(matchup, stats_fetcher, date):
    home_team = matchup["home"]  # Assuming 'home' and 'away' are keys in matchup dict
    away_team = matchup["away"]

    # Fetch stats concurrently for efficiency
    home_stats, away_stats = await asyncio.gather(
        stats_fetcher.get_team_stats(home_team, date),
        stats_fetcher.get_team_stats(away_team, date),
    )

    points = stats_fetcher.compare_stats(home_stats, away_stats)
    projected_winner = home_team if points["home"] > points["away"] else away_team

    return {
        "matchup": matchup,
        "home_stats": home_stats,
        "away_stats": away_stats,
        "points": points,
        "projected_winner": projected_winner,
    }


if __name__ == "__main__":
    asyncio.run(main())
