import logging
import sys
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QColor


class Color:
    red = QColor(255, 0, 0)
    green = QColor(0, 255, 0)
    yellow = QColor(255, 255, 0)
    white = QColor(255, 255, 255)


class ColoredFormatter(logging.Formatter):
    COLORS = {'DEBUG': '\033[94m', 'INFO': '\033[92m', 'WARNING': '\033[93m',
              'ERROR': '\033[91m', 'CRITICAL': '\033[95m'}

    def format(self, record):
        log_fmt = f"{self.COLORS.get(record.levelname, '')}" \
                  f"[%(levelname)s] - [%(threadName)s] - %(message)s"
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


_log_format_file = f"%(asctime)s - [%(levelname)s] - [%(threadName)s] - %(name)s - " \
              f"(%(filename)s).%(funcName)s(%(lineno)d) - %(message)s"


def get_file_handler():
    file_handler = logging.FileHandler("logfile.log")
    file_handler.setLevel(logging.WARNING)
    file_handler.setFormatter(logging.Formatter(_log_format_file))
    return file_handler


def get_stream_handler():
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(ColoredFormatter())
    return stream_handler


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(get_file_handler())
    logger.addHandler(get_stream_handler())
    return logger
