import json
from pathlib import Path
from colorama import Fore, init
import readline
import time
from logger import get_logger
import random
from enum import Enum
import sys
import argparse

# Import constants
from constants import (
    MOTIVATIONAL_QUOTES, PROMPTER_NAME, THEMES, CURRENT_THEME,
    DEFAULT_BACKTEST_PERIOD, DEFAULT_CONFIG_FILE, DEFAULT_EXPORT_PATH,
    POSITIVE_REINFORCEMENTS, EXPORT_FORMATS
)

# Import configurations
from config import FetcherConfig, MainConfig, settings

# Initialize colorama for colored output
init(autoreset=True)

class ModeChoice(Enum):
    BACKTEST = "1"
    PROJECTION = "2"

class PrompterUI:
    @staticmethod
    def print_help_text() -> None:
        """Prints the help text for the Prompter."""
        help_text = f"""
        {Fore.CYAN}Welcome to the Prompter!{Fore.RESET}
        Follow the on-screen instructions to navigate through the options.
        """
        print(help_text)

    @staticmethod
    def prompt_yes_no(message: str) -> bool:
        while True:
            user_input = input(f"\033[93m{message} (Y/N): \033[0m").lower()
            if user_input in ['y', 'n']:
                return user_input == "y"
            print(f"{Fore.RED}Invalid input. Please enter Y or N.{Fore.RESET}")


    @staticmethod
    def prompt_logging_level() -> str:
        levels = ["INFO", "DEBUG", "ERROR"]
        while True:
            choice = input("\033[93m" + f"Choose logging level ({', '.join(levels)}): " + "\033[0m").upper()
            if choice in levels:
                return choice
            print("Invalid choice. Please select a valid logging level.", file=sys.stderr)

    @staticmethod
    def prompt_config_file() -> str:
        while True:
            file_path = input("Enter path to config file (default is prompter_config.json): ")
            if Path(file_path).exists() or not file_path:  # Empty input uses the default
                return file_path
            print(f"{Fore.RED}File not found. Please enter a valid path.{Fore.RESET}")

    @staticmethod
    def prompt_backtest_period() -> int:
        while True:
            try:
                period = int(input(f"Enter backtest period (default is {DEFAULT_BACKTEST_PERIOD}): "))
                if period > 0:
                    return period
                print(f"{Fore.RED}Please enter a positive number.{Fore.RESET}")
            except ValueError:
                print(f"{Fore.RED}Invalid input. Please enter a valid number.{Fore.RESET}")


    @staticmethod
    def prompt_mode_choice() -> str:
        while True:
            choice = input("1. Backtest Mode\n2. Projection Mode\nEnter choice: ")
            if choice in ModeChoice._value2member_map_:
                return choice
            print("Invalid choice. Please try again.", file=sys.stderr)

    @staticmethod
    def prompt_export_format() -> str:
        while True:
            choice = input(f"\033[93mChoose export format ({'/'.join(EXPORT_FORMATS)}): \033[0m").lower()
            if choice in EXPORT_FORMATS:
                return choice
            print(f"{Fore.RED}Invalid choice. Please select from {', '.join(EXPORT_FORMATS)}.")


    @staticmethod
    def prompt_main_menu() -> str:
        print(f"{Fore.CYAN}Choose an option:{Fore.RESET}")
        print("1. Start Backtest")
        print("2. Export Results")
        print("3. Load Config")
        print("4. Set Backtest Parameters")
        print("5. Quit")
        return input(f"{Fore.YELLOW}> {Fore.RESET}")

class Prompter:
    def __init__(self, strategy):
        self.strategy = strategy
        self.logger = get_logger(__name__)
        self.user_name = self.get_user_name()
        self.greet_user()

    def display_win_rate(self, win_rate):
        print(f"Total win rate for the strategy over the backtest period: {win_rate * 100:.2f}%")

    def get_user_name(self):
        if not hasattr(self, 'user_name'):
            self.user_name = input("Hello! What's your name? ")
        return self.user_name

    def greet_user(self):
        greetings = [
            f"Hello, {self.user_name}! Ready to get started?",
            f"Welcome back, {self.user_name}! Let's dive in.",
            f"Good to see you, {self.user_name}! Let's make some progress today."
        ]
        print(random.choice(greetings))

def run(self) -> None:
    try:
        UserIO.print_help_text()
        print(random.choice(MOTIVATIONAL_QUOTES))
        while True:
            choice = PrompterUI.prompt_main_menu()
            if choice == "1":
                results = self.strategy.execute()
                results.display()
                print(random.choice(POSITIVE_REINFORCEMENTS))
            elif choice == "2":
                self.export_results(results)
            elif choice == "3":
                # Use the reload_config method from config.py
                settings.reload()
            elif choice == "4":
                period = PrompterUI.prompt_backtest_period()
                self.strategy.set_parameters({"backtest_period": period})
            elif choice == "5":
                print(f"{Fore.GREEN}Exiting...{Fore.RESET}")
                break
            else:
                print(f"{Fore.RED}Invalid choice. Please try again.{Fore.RESET}")
    except Exception as e:
        self.logger.error(f"An unexpected error occurred: {e}")
        print(f"{Fore.RED}An unexpected error occurred. Please try again later.{Fore.RESET}")


def main():
    parser = argparse.ArgumentParser(description="Run the Prompter.")
    parser.add_argument("--config", type=Path, help="Path to the configuration file.")
    args = parser.parse_args()
    prompter = Prompter(BacktestStrategy(ScheduleScraperStrategy()))
    print(f"Hello! I'm {PROMPTER_NAME}. Let's get started!")
    prompter.run()

if __name__ == "__main__":
    main()