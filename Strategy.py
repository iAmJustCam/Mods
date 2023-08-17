# coding: utf-8
# Strategy.py

from abc import ABC, abstractmethod
from constants import ColumnNames
from extractor import TeamRankingExtractor

class Event:
    """Simple event system."""
    def __init__(self):
        self._listeners = []

    def add_listener(self, listener):
        self._listeners.append(listener)

    def remove_listener(self, listener):
        self._listeners.remove(listener)

    def emit(self, *args, **kwargs):
        for listener in self._listeners:
            listener(*args, **kwargs)

class Strategy(ABC):
    """Base class for all strategies."""

    def __init__(self):
        self.before_execute = Event()
        self.after_execute = Event()

    @abstractmethod
    def __call__(self, *args, **kwargs) -> None:
        """Execute the strategy."""
        pass

class Context:
    """Common context to share state between strategies without coupling them."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

class DataExtractionStrategy(Strategy):
    """Implementation of a data extraction strategy."""

    def __init__(self, extractor: TeamRankingExtractor):
        super().__init__()
        self.extractor = extractor

    def __call__(self, url: str, params: dict, categories: list, context: Context = None) -> dict:
        self.before_execute.emit()
        
        result = self.extractor.fetch_and_transform(url, params, categories)
        
        self.after_execute.emit()
        return result
