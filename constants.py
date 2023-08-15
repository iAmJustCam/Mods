# coding: utf-8
import os
from typing import NamedTuple, Union
from enum import Enum

class ColumnNames(Enum):
    MATCHUP = "Matchup"
    CATEGORY = "Category"
    AWAY_RANK = "Away Rank"
    HOME_RANK = "Home Rank"
    POINT_AWARDED_TO = "Point Awarded To"
    AWAY_POINT_TOTAL = "Away Point Total"
    HOME_POINT_TOTAL = "Home Point Total"
    PROJECTED_WINNER = "Projected Winner"


class Environment:
    """Class to manage environment variables."""
    
    @staticmethod
    def fetch(variable_name: str, default: Union[str, int], expected_type: type) -> Union[str, int]:
        """Fetch an environment variable, ensuring type safety and providing default values."""
        raw_value = os.getenv(variable_name, default=default)

        try:
            return expected_type(raw_value)
        except ValueError:
            print(f"Warning: Invalid value for environment variable '{variable_name}'. Using default: {default}.")
            return default


class Config:
    """Class to organize configuration constants."""
    
    COLUMNS = [column.value for column in ColumnNames]
    DATE_FORMAT = Environment.fetch("DATE_FORMAT", "%Y-%m-%d", str)
    CACHE_SIZE = Environment.fetch("CACHE_SIZE", 100, int)
