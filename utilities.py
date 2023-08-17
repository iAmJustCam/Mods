# coding: utf-8
from typing import List, Dict, Union, Tuple, Any
from constants import Environment
import progressbar
from colorama import Fore, init
import matplotlib.pyplot as plt
import qrcode
import pyperclip

init(autoreset=True)  # Initialize colorama

class UtilitiesError(Exception):
    """Custom exception for utilities errors."""

class Utilities:
    """Utility class providing generic utility functions and classes."""

    @staticmethod
    def list_chunks(lst: List, n: int) -> List[List]:
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]

    @staticmethod
    def string_reverse(s: str) -> str:
        """Reverse a string."""
        return s[::-1]

    @staticmethod
    def is_palindrome(s: str) -> bool:
        """Check if a string is a palindrome."""
        return s == s[::-1]

    @staticmethod
    def fetch_environment_variable(variable_name: str, default: Union[str, int], expected_type: type) -> Union[str, int]:
        try:
            return Environment.fetch(variable_name, default, expected_type)
        except Exception as e:
            raise UtilitiesError(f"Failed to fetch environment variable {variable_name}. Reason: {e}") from e

    @staticmethod
    def format_header(header: str) -> str:
        """Format a header string with clear separators."""
        return f"{Fore.BLUE}{'=' * 5} {header} {'=' * 5}"

    @staticmethod
    def format_section(section: str) -> str:
        """Format a section string with clear separators."""
        return f"{Fore.GREEN}{'-' * 5} {section} {'-' * 5}"

    @staticmethod
    def format_tabulated_data(data: List[Dict[str, Any]]) -> str:
        """Format data into a tabulated string for better presentation."""
        if not data:
            return ""
        headers = data[0].keys()
        formatted_data = [headers]
        for row in data:
            formatted_data.append(tuple(row.values()))
        return "\n".join(["\t".join(map(str, row)) for row in formatted_data])

    @staticmethod
    def calculate_win_rate(actual_winners: List[str], projected_winners: List[str]) -> float:
        """Calculate win rate by comparing actual winners with projected winners."""
        if len(actual_winners) != len(projected_winners):
            raise UtilitiesError("Length of actual winners and projected winners lists must be the same.")
        correct_predictions = sum(1 for actual, projected in zip(actual_winners, projected_winners) if actual == projected)
        return correct_predictions / len(actual_winners) * 100

    @staticmethod
    def show_progress_bar(iterable, max_value=None):
        """Display a dynamic progress bar in the console."""
        bar = progressbar.ProgressBar(max_value=max_value or len(iterable))
        for item in bar(iterable):
            pass

    @staticmethod
    def plot_data(x, y, plot_type="line", title="", xlabel="", ylabel=""):
        """Provide simple functions to plot data."""
        if plot_type == "bar":
            plt.bar(x, y)
        elif plot_type == "pie":
            plt.pie(y, labels=x)
        else:
            plt.plot(x, y)
        plt.title(title)
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.show()

    @staticmethod
    def generate_qr_code(data: str) -> None:
        """Convert URLs or text into QR codes for easy sharing."""
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.show()

    @staticmethod
    def copy_to_clipboard(data: str) -> None:
        """Allow users to copy data directly to their clipboard."""
        pyperclip.copy(data)

    @staticmethod
    def fetch_from_clipboard() -> str:
        """Fetch data from the clipboard."""
        return pyperclip.paste()

# Additional utility functions can be added here
