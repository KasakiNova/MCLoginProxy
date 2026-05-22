# coding=utf-8
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
    def filter(self, record):
        return not getattr(record, "command", False)


class ColoredFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None, *, use_colors=True):
        super().__init__(fmt, datefmt)
        self.use_colors = use_colors and sys.stdout.isatty()

    def format(self, record):
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


def _cleanup_old_logs(log_dir: str, max_save_log: int):
    pattern = os.path.join(log_dir, f"{LOG_PREFIX}_*.log")
    files = sorted(glob(pattern))
    if len(files) > max_save_log:
        for f in files[:-max_save_log]:
            try:
                os.remove(f)
            except OSError:
                pass


def setup_logger(config: dict, debug: bool = False):
    _logger.propagate = False
    _logger.setLevel(logging.DEBUG if debug else logging.INFO)
    _logger.handlers.clear()

    console_handler = logging.StreamHandler()
    console_handler.addFilter(NoCommandFilter())
    if debug:
        console_handler.setFormatter(
            ColoredFormatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
        )
    else:
        console_handler.setFormatter(ColoredFormatter("[%(levelname)s] %(message)s"))
    _logger.addHandler(console_handler)

    waitress_logger = logging.getLogger("waitress")
    waitress_logger.propagate = False
    waitress_logger.handlers.clear()
    waitress_logger.setLevel(logging.INFO)
    waitress_logger.addHandler(console_handler)

    wsgi_logger = logging.getLogger("wsgi")
    wsgi_logger.propagate = False
    wsgi_logger.handlers.clear()
    wsgi_logger.setLevel(logging.INFO)
    wsgi_logger.addHandler(console_handler)

    werkzeug_logger = logging.getLogger("werkzeug")
    werkzeug_logger.propagate = False
    werkzeug_logger.handlers.clear()
    werkzeug_logger.setLevel(logging.INFO)
    werkzeug_logger.addHandler(console_handler)

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

        waitress_logger.addHandler(file_handler)
        wsgi_logger.addHandler(file_handler)
        werkzeug_logger.addHandler(file_handler)


def debug(msg): _logger.debug(msg)
def info(msg): _logger.info(msg)
def warning(msg): _logger.warning(msg)
def error(msg): _logger.error(msg)
def critical(msg): _logger.critical(msg)
def command_log(msg): _logger.info(msg, extra={"command": True})
