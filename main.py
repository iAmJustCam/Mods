import config
import Prompter
import fetcher
import extractor
import cacher
import analyzer
import Trainer
import Evaluator
import writer
import logger

def main():
    # Setup logging
    logger.setup_logging()
    log = logger.get_logger(__name__)

    # Setup cache
    backend = cacher.CacheBackend(capacity=100)
    cache = cacher.Cache(backend=backend, ttl=300)

    # Setup prompter
    scraper_instance = fetcher.MlbScheduleScraper()
    prompter = Prompter.Prompter(scraper_instance)
    
    # Setup machine learning instance
    ml_instance = Trainer.MachineLearning()
    
    # Setup fetcher
    fetcher_instance = fetcher.Fetcher(fetcher.FetcherConfig(), "https://example.com/data")
    
    # Setup configuration manager
    config_manager = config.ConfigurationManager("config.ini")
    
    # Setup extractor
    fetcher_config = fetcher.FetcherConfig(...)
    async_fetcher = fetcher.AsyncFetcher(fetcher_config)
    cache_instance = aiocache.SimpleMemoryCache(max_size=100, ttl=3600)
    team_ranking_extractor = extractor.TeamRankingExtractor(async_fetcher, cache_instance)

    try:
        # 1. Load configurations
        configurations = config.load_config()

        # 2. Prompt the user for input and configurations
        backtest_period = prompter.run() or 7

        # 3. Fetch and extract data
        end_date = datetime.today() - timedelta(days=1)
        start_date = end_date - timedelta(days=backtest_period - 1)
        date_values = [
            (start_date + timedelta(days=i)).strftime(config.Config().DATE_FORMAT)
            for i in range((end_date - start_date).days + 1)
        ]

        for date in date_values:
            data = asyncio.run(fetcher_instance.fetch(f"https://example.com/data/{date}", {}))
            extracted_data = extractor.extract_data(data)
            asyncio.run(cache.put(f"extracted_data_{date}", extracted_data))

        # 4. Analyze the data
        validated_matches = analyzer.TeamMatchValidator.validate(extracted_data)
        for match in validated_matches:
            points = analyzer.PointsCalculator.award_points(match)
            winner = analyzer.WinnerDeterminer.determine_winner(points)

        # 5. Train any models if needed
        ml_instance.load_training_data(validated_matches)
        ml_instance.evaluate_models()

        # 6. Evaluate the results
        evaluation_results = Evaluator.evaluate_model(ml_instance.model)

        # 7. Write the results or any output
        formatter = writer.JSONFormatter()
        file_writer = writer.FileWriter()
        data_writer = writer.DataWriter(formatter, file_writer)
        with open("output.json", "w") as file:
            asyncio.run(data_writer.write_data(file, evaluation_results))

    except Exception as e:
        # 8. Log any important information or errors
        log.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
