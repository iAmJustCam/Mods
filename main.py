import asyncio
from datetime import datetime, timedelta

import config
from config import MainConfig, ConfigurationManager
import Prompter
import fetcher
import extractor
import cacher
import analyzer
import Trainer
import Evaluator
import writer
import logger

# Setup
logger.setup_logging()
log = logger.get_logger(__name__)

async def main():
    # Load configuration
    config_manager = ConfigurationManager(MainConfig.CONFIG_FILE_PATH)

    # Setup cache
    backend = cacher.AsyncCacheBackend(capacity=MainConfig.CACHE_CAPACITY, ttl=MainConfig.CACHE_TTL)
    cache = cacher.Cache(backend=backend)

    # Setup fetcher
    scraper_instance = fetcher.MlbScheduleScraper(MainConfig.SCRAPER_URL)
    fetcher_instance = fetcher.Fetcher(MainConfig.FETCHER, MainConfig.FETCHER.url)

    # Setup prompter
    backtest_manager = Prompter.BacktestManager(scraper_instance)
    prompter = Prompter.Prompter(backtest_manager)

    # Setup machine learning instance
    ml_instance = Trainer.MachineLearning(MainConfig.TRAINING_DATA_PATH)

    # Setup extractor
    async_fetcher = fetcher.AsyncFetcher(MainConfig.FETCHER)
    cache_instance = cacher.AsyncCacheBackend(capacity=MainConfig.CACHE_CAPACITY)
    team_ranking_extractor = extractor.TeamRankingExtractor(async_fetcher, cache_instance)

    # Setup evaluator
    evaluator_instance = Evaluator.Backtester(prompter.backtest_period, scraper_instance)

    try:
        # 2. Prompt the user for input and configurations
        await prompter.run()

        # 3. Fetch and extract data
        end_date = datetime.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=prompter.backtest_period - 1)
        date_values = [
            (start_date + timedelta(days=i)).strftime(Config().DATE_FORMAT)
            for i in range((end_date - start_date).days + 1)
        ]

        for date in date_values:
            data = await fetcher_instance.fetch(f"{MainConfig.FETCHER.url}/{date}", {})
            extracted_data = extractor.extract_data(data)
            await cache.put(f"extracted_data_{date}", extracted_data)

        # 4. Analyze the data
        validated_matches = analyzer.TeamMatchValidator.validate(extracted_data)
        for match in validated_matches:
            points = analyzer.PointsCalculator.award_points(match)
            winner = analyzer.WinnerDeterminer.determine_winner(points)

        # 5. Train any models if needed
        ml_instance.load_training_data(validated_matches)
        ml_instance.evaluate_models()

        # 6. Evaluate the results using the evaluator instance
        evaluation_results = await evaluator_instance.execute_backtest()

        # 7. Write the results or any output
        formatter = writer.JSONFormatter()
        file_writer = writer.FileWriter()
        data_writer = writer.DataWriter(formatter, file_writer)
        with open(MainConfig.OUTPUT_FILE, "w") as file:
            await data_writer.write_data(file, evaluation_results)

    except Exception as e:
        # 8. Log any important information or errors
        log.error(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
