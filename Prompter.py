# prompter.py module
# coding: utf-8
import logging
import matplotlib.pyplot as plt
import json
import os
import asyncio
from evaluator import MatchupManager, ScheduleScraperStrategy, DateFormatError, Backtester

class BacktestManager:
    def __init__(self, scraper: ScheduleScraperStrategy):
        self.backtester = Backtester(7, scraper)

    def run_backtesting(self):
        loop = asyncio.get_event_loop()
        results = loop.run_until_complete(self.backtester.execute_backtest())
        return results

class Prompter:
    def __init__(self, scraper: ScheduleScraperStrategy, interactive_mode=False, config_file="prompter_config.json"):
        self.backtest_period = 7
        self.interactive_mode = interactive_mode
        self.config_file = config_file
        self.load_config()
        self.logger = logging.getLogger(__name__)
        self.backtest_manager = BacktestManager(scraper)


    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as file:
                config = json.load(file)
                self.backtest_period = config.get("backtest_period", self.backtest_period)

    def save_config(self):
        with open(self.config_file, "w") as file:
            json.dump({"backtest_period": self.backtest_period}, file)

    def prompt_logging_level(self):
        levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        user_input = input("\033[93m" + f"Choose logging level ({', '.join(levels)}): " + "\033[0m").upper()
        if user_input in levels:
            logging.basicConfig(level=getattr(logging, user_input))
            self.logger.info(f"User set logging level to {user_input}")

    def prompt_backtest_period(self):
        user_input = input("\033[94m" + f"Please enter the backtest period in days (default is {self.backtest_period}): " + "\033[0m")
        self.logger.info(f"User input for backtest period: {user_input}")
        if user_input:
            self.backtest_period = int(user_input)
            if self.backtest_period <= 0:
                raise ValueError("Backtest period must be greater than 0.")
            return self.backtest_period

    def confirm_start(self):
        user_input = input("\033[93mDo you want to start the backtesting process? (Y/N): \033[0m").lower()
        self.logger.info(f"User input for starting backtesting: {user_input}")
        return user_input == "y"

    def display_win_rate(self, win_rate):
        print("\033[92m" + f"Total win rate for the strategy over the backtest period: {win_rate * 100:.2f}%" + "\033[0m")

    def display_error(self, error_message):
        print("\033[91m" + f"An error occurred: {error_message}" + "\033[0m")

    def display_progress(self, message, total_steps=None):
        if total_steps:
            for _ in tqdm(range(total_steps), desc=message):
                time.sleep(0.1)  # Simulating a task
        else:
            print(message)

    def prompt_view_metrics(self, metrics):
        user_input = input("\033[93mDo you want to view full metrics like accuracy, precision, etc.? (Y/N): \033[0m").lower()
        if user_input == "y":
            print(metrics)

    def prompt_interactive_mode(self):
        if self.interactive_mode:
            user_input = input("\033[93mDo you want to change parameters and re-run? (Y/N): \033[0m").lower()
            return user_input == "y"
        return False

    def plot_metrics(self, metrics):
        user_input = input("\033[93mDo you want to plot graphs of metrics? (Y/N): \033[0m").lower()
        if user_input == "y":
            for metric, values in metrics.items():
                plt.plot(values, label=metric)
            plt.legend()
            plt.xlabel("Backtest Day")
            plt.ylabel("Value")
            plt.title("Metrics Over Backtest Period")
            plt.show()

    def prompt_for_confirmation(self, message):
        user_input = input(f"\033[93m{message} (Y/N): \033[0m").lower()
        return user_input == "y"

    def run_backtesting(self):
        try:
            # Execute backtesting
            loop = asyncio.get_event_loop()
            results = loop.run_until_complete(self.backtester.execute_backtest())

            win_rate = results.get("win_rate", 0)
            metrics = {
                "accuracy": results.get("accuracy", 0),
                "precision": results.get("precision", 0)
            }

            self.display_win_rate(win_rate)
            self.prompt_view_metrics(metrics)
            self.plot_metrics(metrics)
            
        except DateFormatError as dfe:
            self.display_error(f"Date format error: {dfe}")
        except Exception as e:
            self.display_error(str(e))

    def perform_backtest(self, schedule_data):
        win_rate = 0.8
        metrics = {"accuracy": [0.9, 0.91, 0.92], "precision": [0.85, 0.86, 0.87]}
        return win_rate, metrics

    def run(self):
        self.prompt_logging_level()
        while True:
            self.prompt_backtest_period()
            if self.prompt_for_confirmation("Do you want to start the backtesting process?"):
                results = self.backtest_manager.run_backtesting()
                win_rate = results.get("win_rate", 0)
                metrics = {
                    "accuracy": results.get("accuracy", 0),
                    "precision": results.get("precision", 0)
                }
                self.display_win_rate(win_rate)
                self.prompt_view_metrics(metrics)
                self.plot_metrics(metrics)
            self.save_config()
            if not self.interactive_mode or not self.prompt_for_confirmation("Do you want to re-run?"):
                break

if __name__ == "__main__":
    scraper_instance = ScheduleScraperStrategy()
    prompter = Prompter(scraper_instance)
    prompter.run()
