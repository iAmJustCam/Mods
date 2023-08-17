# coding: utf-8
# config.py module
import configparser
import json
import logging
import os
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union
from urllib.parse import quote_plus

import yaml
from dynaconf import Dynaconf, Validator
from pydantic import BaseModel, BaseSettings, Field, ValidationError, validator

from logger import setup_logging

setup_logging()


class ConfigError(Exception):
    """Custom exception for configuration issues."""
    pass


class Environment(str, Enum):
    DEV = "dev"
    PROD = "prod"
    TEST = "test"

# Configuration data for the fetcher.
class FetcherConfig(BaseModel):
    url: str
    timeout: int

# Configuration data for the main module.
class MainConfig(BaseModel):
    CACHE_CAPACITY: int
    CACHE_TTL: int
    SCRAPER_URL: str
    TRAINING_DATA_PATH: str
    FETCHER: FetcherConfig
    CONFIG_FILE_PATH: str
    OUTPUT_FILE: str


class AppSettings(BaseSettings):
    environment: Environment = Environment.DEV
    debug: bool = False

    class Config:
        env_file = ".env"


settings = Dynaconf(
    envvar_prefix="DYNACONF",
    settings_files=['settings.toml', 'settings.yaml', '.secrets.toml'],
    environments=True,
    load_dotenv=True,
    validators=[
        Validator("CACHE_CAPACITY", must_exist=True, default=100),
        # ... Add more validators as needed
    ]
)


def reload_config():
    """Reload the configuration without restarting the application."""
    settings.reload()


def post_load_hook(callback: Callable):
    """Execute a callback function after loading the config."""
    callback()


def load_config_from_file(file_path: str) -> Dict[str, Any]:
    """Load configuration from a YAML or JSON file."""
    with open(file_path, 'r') as file:
        if file_path.endswith(('.yaml', '.yml')):
            return yaml.safe_load(file)
        elif file_path.endswith('.json'):
            return json.load(file)
        raise ConfigError(f"Unsupported config file format: {file_path}")


def pre_load_hook(callback: Callable):
    """Execute a callback function before loading the config."""
    callback()


class Metrics:
    """Class to track metrics."""
    files_written: int = 0
    errors: int = 0


class TeamName(Enum):
    """Team names, dynamically generated based on config.ini."""
    pass


class ConfigSingleton:
    """Singleton class for configuration usage."""
    _config_data: Dict[str, Any] = {}
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigSingleton, cls).__new__(cls)
        return cls._instance

    @classmethod
    def load_config_data(cls, data: Dict[str, Any]):
        cls._config_data = data

    @property
    def DATE_FORMAT(self) -> str:
        return self._config_data.get("DATE_FORMAT", "%Y-%m-%d")

    @property
    def MAX_CONCURRENT_REQUESTS(self) -> int:
        return self._config_data.get("MAX_CONCURRENT_REQUESTS", 5)

    @property
    def TEAM_BASE_URL(self) -> str:
        return self._config_data.get("TEAM_BASE_URL", "https://www.teamrankings.com/mlb/team/")


class Matchup(BaseModel):
    date: str
    home: TeamName
    away: TeamName

    @validator("date")
    def validate_date(cls, value: str) -> str:
        """Validates the date format."""
        try:
            datetime.strptime(value, ConfigSingleton().DATE_FORMAT)
            return value
        except ValueError:
            raise ValueError("Invalid date format")


class ConfigParser:
    """Handles parsing of the configuration file."""

    def __init__(self, config_file: Optional[str] = None):
        self._config_file_path: Optional[Path] = (
            Path(config_file) if config_file else None
        )
        self._config: configparser.ConfigParser = self._load_config()

    def _load_config(self) -> configparser.ConfigParser:
        """Load the config from file."""
        if not self._config_file_path or not self._config_file_path.exists():
            logging.error(f"Config file '{self._config_file_path}' not found.")
            Metrics.errors += 1
            raise FileNotFoundError("Config file not found.")

        config = configparser.ConfigParser()
        config.read(self._config_file_path)
        return config

    def get_config(self) -> configparser.ConfigParser:
        return self._config


class ConfigValidator:
    """Handles validation of the configuration data."""

    @staticmethod
    def validate(config: configparser.ConfigParser):
        try:
            config_data = {
                "DATE_FORMAT": config.get("Config", "DATE_FORMAT"),
                "MAX_CONCURRENT_REQUESTS": config.getint("Config", "MAX_CONCURRENT_REQUESTS"),
                "TEAM_BASE_URL": config.get("Config", "TEAM_BASE_URL"),
            }
            ConfigSingleton.load_config_data(config_data)
            team_mapping = config["team_name_mapping"]
            TeamName = Enum("TeamName", {team.upper().replace(" ", "_"): team for team in team_mapping.keys()})
        except Exception as e:
            logging.error(f"Validation Error: {e}")
            Metrics.errors += 1
            raise


class ConfigurationManager:
    """Manages configuration and related utilities."""

    def __init__(self, config_file: Optional[str] = None) -> None:
        self.parser = ConfigParser(config_file)
        self.validator = ConfigValidator
        self.validator.validate(self.parser.get_config())

    def get_team_url(self, team_name: TeamName) -> str:
        """Generate a URL for the given team name."""
        encoded_name = quote_plus(team_name.value.replace(" ", "-"))
        url = f"{ConfigSingleton().TEAM_BASE_URL}{encoded_name}"
        logging.info(f"Generated URL for {team_name}: {url}")
        return url

    def reload_config(self):
        """Reload the configuration without restarting the application."""
        self.parser = ConfigParser(self.parser._config_file_path)
        self.validator.validate(self.parser.get_config())


if __name__ == "__main__":
    config_manager = ConfigurationManager("config.ini")
    team_url = config_manager.get_team_url(TeamName.LA_DODGERS)
    print(team_url)
