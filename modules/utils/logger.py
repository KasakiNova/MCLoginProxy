# coding=utf-8
"""Structured logging with colour support and optional file output."""
import logging
import os
import sys
from datetime import datetime
from glob import glob

RESET = "\033[0m"
COLORS = {
    "DEBUG": "\033[36m",
    "INFO": RESET,
    "WARNING": "\033[33m",
    "ERROR": "\033[31m",
    "CRITICAL": "\033[41m",
}

LOG_PREFIX = "MCLoginProxy"


class NoCommandFilter(logging.Filter):
    """Filter out log records tagged with ``command=True`` (console echoes)."""

    def filter(self, record: logging.LogRecord) -> bool:
        return not getattr(record, "command", False)


class ColoredFormatter(logging.Formatter):
    """Colourize log level names for terminal output."""

    def __init__(self, fmt=None, datefmt=None, *, use_colors: bool = True):
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        if self.use_colors:
            original = record.levelname
            color = COLORS.get(original, RESET)
            record.levelname = f"{color}{original}{RESET}"
            result = super().format(record)
            record.levelname = original
            return result
        return super().format(record)


_logger = logging.getLogger("YggdrasilProxy")
_logger.setLevel(logging.INFO)
_logger.handlers.clear()
_default_console = logging.StreamHandler()
_default_console.setFormatter(ColoredFormatter("[%(levelname)s] %(message)s"))
_logger.addHandler(_default_console)


def _cleanup_old_logs(log_dir: str, max_save_log: int) -> None:
    """Remove excess log files so at most *max_save_log* remain."""
    pattern = os.path.join(log_dir, f"{LOG_PREFIX}_*.log")
    files = sorted(glob(pattern))
    if len(files) > max_save_log:
        for log_file in files[:-max_save_log]:
            try:
                os.remove(log_file)
            except OSError:
                pass


def setup_logger(config: dict, debug: bool = False) -> None:
    """Reconfigure the application logger from *config*.

    Adds a file handler when ``[Log].save-log`` is true.
    """
    _logger.propagate = False
    _logger.setLevel(logging.DEBUG if debug else logging.INFO)
    _logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.addFilter(NoCommandFilter())
    if debug:
        console_handler.setFormatter(
            ColoredFormatter(
                "%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%H:%M:%S"
            )
        )
    else:
        console_handler.setFormatter(
            ColoredFormatter("[%(levelname)s] %(message)s")
        )
    _logger.addHandler(console_handler)

    _patch_third_party_logger("waitress", console_handler)
    _patch_third_party_logger("wsgi", console_handler)
    _patch_third_party_logger("werkzeug", console_handler)

    log_config = config.get("Log", {})
    if log_config.get("save-log", False):
        log_dir = log_config.get("log_dir", "logs")
        max_save_log = int(log_config.get("max_save_log", 5))
        os.makedirs(log_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = os.path.join(log_dir, f"{LOG_PREFIX}_{timestamp}.log")

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        _logger.addHandler(file_handler)
        _cleanup_old_logs(log_dir, max_save_log)

        _patch_third_party_logger("waitress", file_handler)
        _patch_third_party_logger("wsgi", file_handler)
        _patch_third_party_logger("werkzeug", file_handler)


def _patch_third_party_logger(name: str,
                              handler: logging.Handler) -> None:
    """Redirect a third-party logger through our handler."""
    target = logging.getLogger(name)
    target.propagate = False
    target.handlers.clear()
    target.setLevel(logging.INFO)
    target.addHandler(handler)


def debug(msg: str) -> None:
    _logger.debug(msg)


def info(msg: str) -> None:
    _logger.info(msg)


def warning(msg: str) -> None:
    _logger.warning(msg)


def error(msg: str) -> None:
    _logger.error(msg)


def critical(msg: str) -> None:
    _logger.critical(msg)


def command_log(msg: str) -> None:
    _logger.info(msg, extra={"command": True})
