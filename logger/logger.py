# coding utf-8
# ᛝ


import logging

def setup_logger(
    name: str,
    logfile: str,
    level: int = logging.INFO,
    mode: str = 'all'
):
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )

    if mode in ('console', 'all'):
        console = logging.StreamHandler()
        console.setLevel(level)
        console.setFormatter(formatter)
        logger.addHandler(console)
    
    file = RotatingFleHandler(
        logfile,
        maxBytes= 10 * 1024 * 1024, # 10MiB
        backupCount=5,
        encoding="utf-8"
    )
    file.setLevel(level)
    file.setFotmatter(formatter)
    
    logger.addHandler(file)

    return logger
