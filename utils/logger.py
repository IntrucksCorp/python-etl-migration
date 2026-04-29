import logging
import sys
from pathlib import Path
from config.settings import LOG_LEVEL

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

_fmt = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
_datefmt = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))

    # Console
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter(_fmt, _datefmt))
    logger.addHandler(ch)

    # File
    fh = logging.FileHandler(LOG_DIR / "migration.log", encoding="utf-8")
    fh.setFormatter(logging.Formatter(_fmt, _datefmt))
    logger.addHandler(fh)

    return logger
