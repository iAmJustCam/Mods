#logger.py module
# coding: utf-8
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logging(
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_file_name: str = "log.txt",
    file_log_level: int = None,
    console_log_level: int = None
) -> None:
    """
    Set up logging with given configurations.

    :param log_format: The format of the logging messages.
    :param log_file_name: The name of the log file to save logs.
    :param file_log_level: Logging level for the log file.
    :param console_log_level: Logging level for console output.
    """
    file_log_level = file_log_level or int(os.environ.get('FILE_LOG_LEVEL', logging.INFO))
    console_log_level = console_log_level or int(os.environ.get('CONSOLE_LOG_LEVEL', logging.INFO))

    log_filename = os.path.join(os.path.dirname(__file__), log_file_name)

    # Setup Rotating Log Files
    file_handler = RotatingFileHandler(log_filename, "a", "utf-8", maxBytes=10*1024*1024, backupCount=3)
    file_handler.setLevel(file_log_level)
    file_handler.setFormatter(logging.Formatter(log_format))

    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_log_level)
    console_handler.setFormatter(logging.Formatter(log_format))

    logging.basicConfig(level=min(file_log_level, console_log_level), handlers=[file_handler, console_handler])

    # Handle potential file operation exceptions
    try:
        with open(log_filename, 'a'):
            pass
    except Exception as e:
        logging.error(f"Failed to create or access the log file: {e}")


def get_logger(name: str) -> logging.Logger:
    """
    Returns a logger with the given name.

    :param name: Name of the logger.
    :return: An instance of a logger.
    """
    return logging.getLogger(name)


if __name__ == "__main__":
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Logger initialized in main execution.")
    logger.error("This is an error log for demonstration purposes.")
    logger.debug("This is a debug log for demonstration purposes.")
    logger.warning("This is a warning log for demonstration purposes.")
    logger.critical("This is a critical log for demonstration purposes.")
