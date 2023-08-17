# coding: utf-8
# config.py module
import configparser
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import quote_plus

from logger import setup_logging

setup_logging()


class ConfigError(Exception):
    """Custom exception for configuration issues."""
    pass


class TeamName(Enum):
    """Team names, dynamically generated based on config.ini."""
    pass


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
            raise FileNotFoundError("Config file not found.")

        config = configparser.ConfigParser()
        config.read(self._config_file_path)
        return config

    def get_config(self) -> configparser.ConfigParser:
        return self._config


class ConfigValidator:
    """Handles validation of the configuration data."""

    @staticmethod
    def validate(config: configparser.ConfigParser) -> Dict[str, Any]:
        try:
            config_data = {
                "DATE_FORMAT": config.get("Config", "DATE_FORMAT"),
                "MAX_CONCURRENT_REQUESTS": config.getint("Config", "MAX_CONCURRENT_REQUESTS"),
                "TEAM_BASE_URL": config.get("Config", "TEAM_BASE_URL"),
            }
            team_mapping = config["team_name_mapping"]
            TeamName = Enum("TeamName", {team.upper().replace(" ", "_"): team for team in team_mapping.keys()})
            return config_data
        except Exception as e:
            logging.error(f"Validation Error: {e}")
            raise


class ConfigurationManager:
    """Manages configuration and related utilities."""

    def __init__(self, config_file: Optional[str] = None) -> None:
        self.parser = ConfigParser(config_file)
        self.config_data = ConfigValidator.validate(self.parser.get_config())

    def get_team_url(self, team_name: TeamName) -> str:
        """Generate a URL for the given team name."""
        encoded_name = quote_plus(team_name.value.replace(" ", "-"))
        url = f"{self.config_data['TEAM_BASE_URL']}{encoded_name}"
        logging.info(f"Generated URL for {team_name}: {url}")
        return url

    def reload_config(self):
        """Reload the configuration without restarting the application."""
        self.parser = ConfigParser(self.parser._config_file_path)
        self.config_data = ConfigValidator.validate(self.parser.get_config())


if __name__ == "__main__":
    config_manager = ConfigurationManager("config.ini")
    team_url = config_manager.get_team_url(TeamName.LA_DODGERS)
    print(team_url)
