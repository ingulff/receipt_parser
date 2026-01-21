# coding utf-8
# ᛝ

import logging
from logging.handlers import RotatingFileHandler
from uuid import uuid4

from logger.logger import setup_logger


def test_setup_logger_creates_rotating_file_handler(tmp_path):
    name = f'test_logger_{uuid4().hex}'
    logfile = tmp_path / 'logs' / 'service.log'

    logger = setup_logger(name, logfile, mode='file')

    try:
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], RotatingFileHandler)
        assert logger.propagate is False
    finally:
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()
