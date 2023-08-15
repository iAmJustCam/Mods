# coding: utf-8
# config.py module
import configparser
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import quote_plus

from pydantic import BaseModel, validator, ValidationError

from logger import setup_logging

setup_logging()


class Metrics:
    """Class to track metrics."""
    files_written: int = 0
    errors: int = 0


class TeamName(Enum):
    # This will be dynamically generated based on config.ini
    pass


class Config:
    """Singleton class for configuration usage."""
    DATE_FORMAT: str = "%Y-%m-%d"
    MAX_CONCURRENT_REQUESTS: int = 5
    TEAM_BASE_URL: str = "https://www.teamrankings.com/mlb/team/"
    
    _config_data: Dict[str, Any] = {}
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    @classmethod
    def load_config_data(cls, data: Dict[str, Any]):
        cls._config_data = data

    @property
    def DATE_FORMAT(self):
        return self._config_data.get('DATE_FORMAT', Config.DATE_FORMAT)

    @property
    def MAX_CONCURRENT_REQUESTS(self):
        return self._config_data.get('MAX_CONCURRENT_REQUESTS', Config.MAX_CONCURRENT_REQUESTS)

    @property
    def TEAM_BASE_URL(self):
        return self._config_data.get('TEAM_BASE_URL', Config.TEAM_BASE_URL)


class Matchup(BaseModel):
    date: str
    home: TeamName
    away: TeamName

    @validator("date")
    def validate_date(cls, value: str) -> str:
        """Validates the date format."""
        try:
            datetime.strptime(value, Config().DATE_FORMAT)
            return value
        except ValueError:
            raise ValueError("Invalid date format")


class ConfigurationManager:
    """Manages configuration and related utilities."""

    def __init__(self, config_file: Optional[str] = None) -> None:
        self._config_file_path: Optional[Path] = (
            Path(config_file) if config_file else None
        )
        self._config: configparser.ConfigParser = self._load_config()
        self._validate_and_load_to_singleton()

    @property
    def config(self) -> configparser.ConfigParser:
        return self._config

    def _load_config(self) -> configparser.ConfigParser:
        """Load the config from file."""
        if not self._config_file_path or not self._config_file_path.exists():
            logging.error(f"Config file '{self._config_file_path}' not found.")
            Metrics.errors += 1
            raise FileNotFoundError("Config file not found.")

        config = configparser.ConfigParser()
        config.read(self._config_file_path)
        return config

    def _validate_and_load_to_singleton(self) -> None:
        """Validates and loads the necessary fields in the config to the singleton."""
        try:
            # Using sections directly for flexibility and future enhancements
            config_data = {
                "DATE_FORMAT": self._config.get("Config", "DATE_FORMAT"),
                "MAX_CONCURRENT_REQUESTS": self._config.getint("Config", "MAX_CONCURRENT_REQUESTS"),
                "TEAM_BASE_URL": self._config.get("Config", "TEAM_BASE_URL")
            }
            Config.load_config_data(config_data)

            # Dynamically create TeamName Enum based on config.ini
            team_mapping = self._config["team_name_mapping"]
            for team, _ in team_mapping.items():
                TeamName[team.upper().replace(" ", "_")] = team
        except Exception as e:
            logging.error(f"Validation or Loading Error: {e}")
            Metrics.errors += 1
            raise

    def get_team_url(self, team_name: TeamName) -> str:
        """Generate a URL for the given team name."""
        encoded_name = quote_plus(team_name.value.replace(" ", "-"))
        url = f"{Config().TEAM_BASE_URL}{encoded_name}"
        logging.info(f"Generated URL for {team_name}: {url}")
        return url


# This is for demonstrating how to use the ConfigurationManager
if __name__ == "__main__":
    config_manager = ConfigurationManager("config.ini")
    team_url = config_manager.get_team_url(TeamName.LA_DODGERS)
    print(team_url)
