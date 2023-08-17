# coding: utf-8
from enum import Enum, auto

# Constants for Prompter.py
class MotivationalQuotes(Enum):
    QUOTE_1 = "Believe you can and you're halfway there."
    QUOTE_2 = "The future belongs to those who believe in the beauty of their dreams."
    QUOTE_3 = "It always seems impossible until it's done."

PROMPTER_NAME = "Promptly"

class Themes(Enum):
    LIGHT = ("black", "white")
    DARK = ("white", "black")

CURRENT_THEME = Themes.LIGHT
DEFAULT_BACKTEST_PERIOD = 7
DEFAULT_CONFIG_FILE = "prompter_config.json"
DEFAULT_EXPORT_PATH = "results"

class PositiveReinforcements(Enum):
    MESSAGE_1 = "Well done!"
    MESSAGE_2 = "Keep it up!"
    MESSAGE_3 = "Fantastic job!"

class ExportFormats(Enum):
    JSON = "json"
    CSV = "csv"

class ColumnNames(Enum):
    MATCHUP = "Matchup"
    CATEGORY = "Category"
    AWAY_RANK = "Away Rank"
    HOME_RANK = "Home Rank"
    POINT_AWARDED_TO = "Point Awarded To"
    AWAY_POINT_TOTAL = "Away Point Total"
    HOME_POINT_TOTAL = "Home Point Total"
    PROJECTED_WINNER = "Projected Winner"

class Config(Enum):
    COLUMNS = [column.value for column in ColumnNames]
    DATE_FORMAT = "%Y-%m-%d"
    CACHE_SIZE = 100
