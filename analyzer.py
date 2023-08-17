# coding: utf-8
import os
import questionary
from rich import print as rprint
from rich.progress import track
import random
from playsound import playsound
from dataclasses import dataclass
from typing import List, Union, Dict, Tuple
from datetime import datetime, timezone
import logging
import json
import pandas as pd
from functools import lru_cache
from abc import ABC, abstractmethod

# Constants (default values)
MAX_SCORE = 20
MIN_SCORE = 0

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("analyzer.log")
    ]
)

# Sample motivational quotes
QUOTES = [
    "Keep going!",
    "You're doing great!",
    "Fantastic job!",
    "On the right track!"
]

RankDict = Dict[str, int]

@dataclass
class TeamMatch:
    team1: str
    team2: str
    date: datetime
    team1_score: int
    team2_score: int

    def analyze_match(self) -> Dict[str, Union[str, int]]:
        if not isinstance(self.team1, str) or not isinstance(self.team2, str):
            raise InvalidInputError("Team names must be strings.")
        if not (MIN_SCORE <= self.team1_score <= MAX_SCORE) or not (MIN_SCORE <= self.team2_score <= MAX_SCORE):
            raise InvalidInputError(f"Scores must be between {MIN_SCORE} and {MAX_SCORE}.")
        
        logging.info(f"Analyzing match between {self.team1} and {self.team2}.")
        return {
            "team1": self.team1,
            "team2": self.team2,
            "team1_score": self.team1_score,
            "team2_score": self.team2_score
        }

    def generate_insights(self) -> str:
        logging.info("Generating insights for the match.")
        if self.team1_score > self.team2_score:
            return f"{self.team1} won against {self.team2}."
        elif self.team1_score < self.team2_score:
            return f"{self.team2} won against {self.team1}."
        else:
            return f"It's a tie between {self.team1} and {self.team2}."

class InvalidScoreError(Exception):
    """Exception raised when team scores are negative or unrealistic."""

class InvalidInputError(Exception):
    """Exception raised for invalid input data."""

class DataValidationError(Exception):
    """Exception raised for data validation errors."""

class FutureDateError(DataValidationError):
    """Exception raised when match date is in the future."""

class TeamMatchValidator:
    """Class responsible for validating team match data."""

    @staticmethod
    def validate(
        match_data: List[Dict[str, Union[str, datetime, int]]]
    ) -> List[TeamMatch]:
        validated_matches = []
        for row in match_data:
            validated_match = TeamMatchValidator._validate_single_row(row)
            validated_matches.append(validated_match)
        return validated_matches

    @staticmethod
    def _validate_single_row(row: Dict[str, Union[str, datetime, int]]) -> TeamMatch:
        match = TeamMatch(**row)
        TeamMatchValidator._validate_date(match.date)
        TeamMatchValidator._validate_scores(match.team1_score, match.team2_score)
        TeamMatchValidator._validate_team_names(match.team1, match.team2)
        return match

    @staticmethod
    def _validate_date(date: datetime):
        if date > datetime.now(timezone.utc):
            raise FutureDateError(f"Invalid match date (in the future): {date}")

    @staticmethod
    def _validate_scores(score1: int, score2: int):
        if score1 < 0 or score2 < 0 or score1 > 20 or score2 > 20:
            raise InvalidScoreError(f"Invalid scores: {score1} and {score2}")

    @staticmethod
    def _validate_team_names(team1: str, team2: str):
        if not team1.strip() or not team2.strip():
            raise DataValidationError("Team names cannot be empty.")

class PointsCalculator:
    """Calculate points based on match results."""

    @staticmethod
    def award_points(match: TeamMatch) -> Dict[str, int]:
        if match.team1_score > match.team2_score:
            return {match.team1: 3, match.team2: 0}
        elif match.team1_score < match.team2_score:
            return {match.team1: 0, match.team2: 3}
        else:
            log_msg = f"Tie between {match.team1} and {match.team2}. Each team receives 1 point."
            logging.info(log_msg)
            return {match.team1: 1, match.team2: 1}

class WinnerDeterminer:
    """Determine match winner based on awarded points."""

    @staticmethod
    def determine_winner(points: Dict[str, int]) -> str:
        team, score = max(points.items(), key=lambda x: x[1])
        if list(points.values()).count(score) > 1:
            return "It's a Tie!"
        return team

@lru_cache(maxsize=128)
def save_results_to_file(results: List[Dict[str, Union[str, int]]], filename: str, file_format: str):
    if file_format == "json":
        with open(filename, 'w') as f:
            json.dump(results, f)
    elif file_format == "excel":
        df = pd.DataFrame(results)
        df.to_excel(filename, index=False)

def display_help():
    """Display detailed help documentation."""
    rprint("[bold blue]Help Documentation[/bold blue]")
    rprint("1. Choose the file type you'd like to analyze.")
    rprint("2. If analyzing in batch, provide the directory path.")
    rprint("3. Follow the on-screen prompts.")
    rprint("4. Enjoy the analysis results!")

def analyze_file(file_type: str, file_path: str):
    """Analyze a single file."""
    for _ in track(range(100), description=f"Analyzing {file_type}..."):
        pass  # Simulating some work

    # Randomly play a sound or display a motivational quote
    if random.choice([True, False]):
        rprint(random.choice(QUOTES))
    else:
        # Assuming you have a sound file named "success.mp3" in the current directory
        if os.path.exists("success.mp3"):
            playsound("success.mp3")

def batch_analysis(directory: str):
    """Analyze multiple files in a directory."""
    for _ in track(range(100), description="Batch analyzing..."):
        pass  # Simulating some work

if __name__ == "__main__":
    # Display help documentation
    display_help()

    # Ask user for file type
    file_type = questionary.select(
        "Which file type would you like to analyze?",
        choices=["text", "CSV", "JSON", "Batch Analysis"]
    ).ask()

    if file_type == "Batch Analysis":
        directory = questionary.text("Enter the directory path for batch analysis:").ask()
        batch_analysis(directory)
    else:
        file_path = questionary.text(f"Enter the path to your {file_type} file:").ask()
        analyze_file(file_type, file_path)

    sample_data = [
        {
            "team1": "Team A",
            "team2": "Team B",
            "date": datetime.now(timezone.utc),
            "team1_score": 3,
            "team2_score": 2,
        },
        {
            "team1": "Team C",
            "team2": "Team D",
            "date": datetime.now(timezone.utc),
            "team1_score": 1,
            "team2_score": 1,
        },
    ]

    try:
        validated_matches = TeamMatchValidator.validate(sample_data)
        results = []

        for match in validated_matches:
            insights = match.generate_insights()
            logging.info(insights)
            points = PointsCalculator.award_points(match)
            winner = WinnerDeterminer.determine_winner(points)
            log_msg = f"Points: {points}. Winner: {winner}"
            logging.info(log_msg)
            results.append({
                "team1": match.team1,
                "team2": match.team2,
                "points": points,
                "winner": winner
            })

        save_results_to_file(results, "results.json", "json")

    except FutureDateError:
        logging.error("One of the match dates is set in the future.")
    except InvalidScoreError:
        logging.error("One of the scores is invalid.")
    except DataValidationError as e:
        logging.error(f"Data validation error: {e}")
