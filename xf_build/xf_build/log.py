#!/usr/bin/env python3

import logging
from rich.logging import RichHandler


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'NOTSET': '\033[97m',
        'DEBUG': '\033[94m',
        'INFO': '\033[92m',
        'WARNING': '\033[93m',
        'ERROR': '\033[91m',
        'CRITICAL': '\033[95m'
    }
    RESET = '\033[0m'

    def format(self, record) -> str:
        log_color = self.COLORS.get(record.levelname, '')
        record.msg = log_color + super().format(record) + self.RESET
        return record.msg


def logging_setup(level, rich=False) -> None:
    if rich:
        logging.basicConfig(
            level=level,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler()]
        )
        return
    logger: logging.Logger = logging.getLogger()

    handler = logging.StreamHandler()
    formatter = ColoredFormatter(
        '%(asctime)s: %(message)s', datefmt="%H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level=level)
