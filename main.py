
#main.py module
#Handling CLI arguments and initialization
#Configuring application context
#Constructing core components
#Starting orchestration and lifecycle
import argparse
import asyncio
import logging
from config import AppConfig
from logger import setup_logging, get_logger
from dependency_container import DependencyContainer
from workflow_orchestrator import WorkflowOrchestrator
from api import APIEndpoints

# Setup logging
setup_logging()
logger = get_logger(__name__)

def setup_cli_arguments():
    parser = argparse.ArgumentParser(description="Main application for data processing and analysis.")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to the configuration file.")
    parser.add_argument('-m', '--mode', choices=['backtest', 'project'], default='backtest', help="Choose mode: Backtest or Project.")
    parser.add_argument('-p', '--period', type=int, default=7, help="Specify the period for backtesting or projection.")
    return parser.parse_args()

def validate_args(args):
    # This function can be expanded for more complex validations
    if args.period <= 0:
        logger.error("Period value must be greater than 0.")
        raise ValueError("Invalid period value.")

def initialize_config(config_path):
    return AppConfig(config_path)

def initialize_dependency_container(config):
    return DependencyContainer(config)

def handle_uncaught_exceptions():
    logger.error("An unhandled exception occurred.", exc_info=True)

def main():
    try:
        # Parse command line arguments and flags
        args = setup_cli_arguments()

        # Validate the arguments
        validate_args(args)

        # Log the mode and period values
        logger.info(f"Mode selected: {args.mode}")
        logger.info(f"Period value: {args.period}")

        # Print confirmation of mode selected
        print(f"Running in {args.mode} mode with a period of {args.period} days.")

        # Initialize configuration module
        config = initialize_config(args.config)

        # Initialize dependency injection container
        container = initialize_dependency_container(config)

        # Construct application components
        orchestrator = WorkflowOrchestrator(container, args.mode, args.period)

        # Kick off workflow orchestration
        orchestrator.start()

        # Expose any external API endpoints
        api = APIEndpoints(container)
        api.start()

        # Start application lifecycle
        asyncio.run(orchestrator.run())

    except Exception as e:
        handle_uncaught_exceptions()

if __name__ == "__main__":
    main()
