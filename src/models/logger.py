"""
Logger wrapper
"""
import logging

from logging.handlers import RotatingFileHandler

FILE = ('/tmp/fpl_manager.log')
FILE_MAXSIZE = 10 * 1024 * 1024  # 10MB
FILE_BACKUP_CNT = 2
LOG_FORMAT = ('%(asctime)s:%(module)s:%(levelname)s - %(message)s')
LOG_TIME_FORMAT = ('%Y-%m-%d %H:%M:%S')


def get_logger(name, fname=FILE, max_bytes=FILE_MAXSIZE,
               backup_count=FILE_BACKUP_CNT):
    """
    Configure Logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # String format log
    handler = logging.StreamHandler()
    formatter = logging.Formatter(LOG_FORMAT, LOG_TIME_FORMAT)
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    rotate_file_handler = RotatingFileHandler(fname, max_bytes, backup_count)

    logger.addHandler(rotate_file_handler)
    return logger
