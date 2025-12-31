"""Logging configuration for dev-start."""
import logging
import sys
from pathlib import Path
from typing import Optional
from colorama import Fore, Style, init

from .constants import LOG_FORMAT, LOG_DATE_FORMAT, LOG_FILE_NAME, get_tools_dir

# Initialize colorama for Windows
init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""

    COLORS = {
        logging.DEBUG: Fore.CYAN,
        logging.INFO: Fore.GREEN,
        logging.WARNING: Fore.YELLOW,
        logging.ERROR: Fore.RED,
        logging.CRITICAL: Fore.RED + Style.BRIGHT,
    }

    # Use ASCII-safe symbols for Windows compatibility
    SYMBOLS = {
        logging.DEBUG: '[DEBUG]',
        logging.INFO: '[OK]',
        logging.WARNING: '[WARN]',
        logging.ERROR: '[ERROR]',
        logging.CRITICAL: '[CRITICAL]',
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, '')
        symbol = self.SYMBOLS.get(record.levelno, '')
        reset = Style.RESET_ALL

        # Format the message with color and symbol
        formatted_message = f"{color}{symbol} {record.getMessage()}{reset}"

        # Add details if present
        if hasattr(record, 'details') and record.details:
            formatted_message += f"\n  {Fore.CYAN}Details: {record.details}{reset}"

        return formatted_message


class FileFormatter(logging.Formatter):
    """Formatter for file output (no colors)."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, LOG_DATE_FORMAT)
        level = record.levelname
        name = record.name
        message = record.getMessage()

        formatted = f"{timestamp} - {name} - {level} - {message}"

        # Add details if present
        if hasattr(record, 'details') and record.details:
            formatted += f"\n  Details: {record.details}"

        return formatted


class DevStartLogger:
    """Logger wrapper for dev-start with colored output and file logging."""

    def __init__(self, name: str, log_to_file: bool = False):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Remove existing handlers
        self.logger.handlers = []

        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredFormatter())
        self.logger.addHandler(console_handler)

        # File handler (optional)
        if log_to_file:
            self._add_file_handler()

    def _add_file_handler(self):
        """Add file handler for persistent logging."""
        log_dir = get_tools_dir().parent
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / LOG_FILE_NAME

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(FileFormatter())
        self.logger.addHandler(file_handler)

    def debug(self, message: str, details: Optional[str] = None):
        """Log debug message."""
        extra = {'details': details} if details else {}
        self.logger.debug(message, extra=extra)

    def info(self, message: str, details: Optional[str] = None):
        """Log info message."""
        extra = {'details': details} if details else {}
        self.logger.info(message, extra=extra)

    def success(self, message: str, details: Optional[str] = None):
        """Log success message (alias for info with green color)."""
        self.info(message, details)

    def warning(self, message: str, details: Optional[str] = None):
        """Log warning message."""
        extra = {'details': details} if details else {}
        self.logger.warning(message, extra=extra)

    def error(self, message: str, details: Optional[str] = None):
        """Log error message."""
        extra = {'details': details} if details else {}
        self.logger.error(message, extra=extra)

    def critical(self, message: str, details: Optional[str] = None):
        """Log critical message."""
        extra = {'details': details} if details else {}
        self.logger.critical(message, extra=extra)

    def section(self, title: str, char: str = '=', width: int = 60):
        """Print a section header."""
        line = char * width
        print(f"\n{Fore.CYAN}{line}")
        print(f"{title}")
        print(f"{line}{Style.RESET_ALL}\n")

    def subsection(self, title: str, char: str = '-', width: int = 40):
        """Print a subsection header."""
        line = char * width
        print(f"\n{Fore.CYAN}{line}")
        print(f"{title}")
        print(f"{line}{Style.RESET_ALL}")

    def banner(self, title: str, subtitle: str = ''):
        """Print application banner."""
        print(f"{Fore.CYAN}{Style.BRIGHT}")
        print("╔════════════════════════════════════════════════════════════╗")
        print(f"║{title.center(60)}║")
        if subtitle:
            print(f"║{subtitle.center(60)}║")
        print("╚════════════════════════════════════════════════════════════╝")
        print(Style.RESET_ALL)

    def progress(self, message: str):
        """Print a progress message (no symbol)."""
        print(f"{Fore.CYAN}{message}{Style.RESET_ALL}")

    def result(self, label: str, value: str, success: bool = True):
        """Print a result line."""
        color = Fore.GREEN if success else Fore.RED
        print(f"  {label}: {color}{value}{Style.RESET_ALL}")


def get_logger(name: str, log_to_file: bool = False) -> DevStartLogger:
    """Get a logger instance for the given module name."""
    return DevStartLogger(name, log_to_file)
