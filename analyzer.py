#analyzer.py module
# coding: utf-8
from dataclasses import dataclass
from typing import List, Union, Dict
from datetime import datetime, timezone
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s"
)

RankDict = Dict[str, int]


@dataclass
class TeamMatch:
    team1: str
    team2: str
    date: datetime
    team1_score: int
    team2_score: int


class InvalidScoreError(Exception):
    """Exception raised when team scores are negative or unrealistic."""


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
        if date > datetime.now(timezone.utc):  # Adjusted for timezone awareness
            raise FutureDateError(f"Invalid match date (in the future): {date}")

    @staticmethod
    def _validate_scores(score1: int, score2: int):
        if score1 < 0 or score2 < 0 or score1 > 20 or score2 > 20:
            # Added an upper limit check for realistic scores
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
        if list(points.values()).count(score) > 1:  # Handle ties
            return "It's a Tie!"
        return team


if __name__ == "__main__":
    # Sample usage to demonstrate the new structure.
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

        # Calculate and display points, and determine the winner for the validated matches
        for match in validated_matches:
            points = PointsCalculator.award_points(match)
            winner = WinnerDeterminer.determine_winner(points)
            log_msg = f"Points: {points}. Winner: {winner}"
            logging.info(log_msg)
    except FutureDateError:
        logging.error("One of the match dates is set in the future.")
    except InvalidScoreError:
        logging.error("One of the scores is invalid.")
    except DataValidationError as e:
        logging.error(f"Data validation error: {e}")
