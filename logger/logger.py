# coding utf-8
# ᛝ


import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

def setup_logger(
    name: str,
    logfile: str | Path,
    level: int = logging.INFO,
    mode: str = 'all'
) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    if logger.handlers:
        return logger

    logfile = Path(logfile)
    logfile.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    if mode in ('console', 'all'):
        console = logging.StreamHandler()
        console.setLevel(level)
        console.setFormatter(formatter)
        logger.addHandler(console)
    
    if mode in ('file', 'all'):
        file = RotatingFileHandler(
            logfile,
            maxBytes=10 * 1024 * 1024, # 10MiB
            backupCount=5,
            encoding="utf-8"
        )
        file.setLevel(level)
        file.setFormatter(formatter)
        logger.addHandler(file)

    return logger
