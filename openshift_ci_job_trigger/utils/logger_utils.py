from flask import Flask

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from colorlog import ColoredFormatter

FLASK_APP = Flask("openshift-ci-job-trigger")


class WrapperLogFormatter(ColoredFormatter):
    def formatTime(self, record, datefmt=None):  # noqa: N802
        return datetime.fromtimestamp(record.created).isoformat()


def setup_logger():
    log_format = "%(asctime)s %(levelname)s \033[1;36m%(filename)s:%(lineno)d\033[1;0m %(name)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)

    # Add color to log level names
    logging.addLevelName(logging.DEBUG, "\033[1;34mDEBUG\033[1;0m")
    logging.addLevelName(logging.INFO, "\033[1;32mINFO\033[1;0m")
    logging.addLevelName(logging.WARNING, "\033[1;33mWARNING\033[1;0m")
    logging.addLevelName(logging.ERROR, "\033[1;31mERROR\033[1;0m")
    logging.addLevelName(logging.CRITICAL, "\033[1;41mCRITICAL\033[1;0m")

    log_file = os.environ.get("WEBHOOK_SERVER_LOG_FILE")
    if log_file:
        log_handler = RotatingFileHandler(filename=log_file, maxBytes=104857600, backupCount=20)
        file_log_formatter = WrapperLogFormatter(
            fmt="%(asctime)s %(levelname)s \033[1;36m%(filename)s:%(lineno)d\033[1;0m %(name)s: %(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
            secondary_log_colors={},
        )
        log_handler.setFormatter(fmt=file_log_formatter)
        FLASK_APP.logger.addHandler(hdlr=log_handler)


setup_logger()
