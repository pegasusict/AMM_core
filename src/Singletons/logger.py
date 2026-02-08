# -*- coding: utf-8 -*-
#  Copyleft 2021-2026 Mattijs Snepvangers.
#  This file is part of Audiophiles' Music Manager, hereafter named AMM.
#
#  AMM is free software: you can redistribute it and/or modify  it under the terms of the
#   GNU General Public License as published by  the Free Software Foundation, either version 3
#   of the License or any later version.
#
#  AMM is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#   without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#   PURPOSE.  See the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#   along with AMM.  If not, see <https://www.gnu.org/licenses/>.

import logging
from logging import getLogger, FileHandler, Formatter, StreamHandler, Logger as PyLogger

from .config import Config


class Logger:
    """
    This class is used to log messages to a file.
    It uses the logging library to log messages to a file.
    """

    def __init__(self, config: Config | None = None) -> None:
        """
        Initializes the Logger class.

        Args:
            config: The configuration object.
        """
        self.config = config or Config()
        self.log_file = self.config.get_string("logging", "file", "amm.log")
        self.log_level = self.config.get_string("logging", "level", "INFO")
        self.log_format = "%(asctime)s - %(levelname)s - %(message)s"
        self.logger = self._setup_logger()

        self.logger.info("Logger initialized")
        log_msg = f"Log file: {self.log_file}"
        self.logger.info(log_msg)
        log_msg = f"Log level: {self.log_level}"
        self.logger.info(log_msg)
        log_msg = f"Log format: {self.log_format}"
        self.logger.info(log_msg)
        self.logger.info("Logger setup complete")

    def _setup_logger(self) -> PyLogger:
        """Sets up the logger with the specified log file, log level, and log format."""
        logger = getLogger(__name__)
        level = self._translate_loglevel()
        file_handler = FileHandler(str(self.log_file))
        file_handler.setLevel(level)

        # Create console handler
        console_handler = StreamHandler()
        console_handler.setLevel(level)

        # Create console handler
        console_handler = StreamHandler()
        level_for_console = self._translate_loglevel()
        console_handler.setLevel(level_for_console)

        # Create formatter
        formatter = Formatter(self.log_format)

        # Add formatter to handlers
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    def _translate_loglevel(self) -> int:
        result = self.log_level
        if isinstance(result, str):
            result = logging._nameToLevel.get(result.upper(), logging.INFO) # type: ignore
        if not isinstance(result, int):
            result = logging.INFO
        return result

    def debug(self, message: str) -> None:
        """Logs a debug message."""
        self.logger.debug(message)

    def info(self, message: str) -> None:
        """Logs an info message."""
        self.logger.info(message)

    def warning(self, message: str) -> None:
        """Logs a warning message."""
        self.logger.warning(message)

    def error(self, message: str) -> None:
        """Logs an error message."""
        self.logger.error(message)

    def critical(self, message: str) -> None:
        """Logs a critical message."""
        self.logger.critical(message)

    def exception(self, message: str) -> None:
        """Logs an exception message with traceback."""
        self.logger.exception(message)

    def set_log_file(self, log_file: str) -> None:
        """Sets the log file for the logger."""
        self.log_file = log_file

        for handler in self.logger.handlers:
            handler.close()
            self.logger.removeHandler(handler)

        self.logger = self._setup_logger()

        log_msg = f"Log file set to {log_file}"
        self.logger.info(log_msg)

    def set_log_format(self, log_format: str) -> None:
        """Sets the log format for the logger."""
        self.log_format = log_format

        for handler in self.logger.handlers:
            handler.setFormatter(Formatter(log_format))

        log_msg = f"Log format set to {log_format}"
        self.logger.info(log_msg)

    def get_log_file(self) -> str:
        """Returns the log file for the logger."""
        return str(self.log_file) if self.log_file is not None else ""

    def get_log_level(self) -> str:
        """Returns the log level for the logger."""
        return str(self.log_level) if self.log_level is not None else ""

    def get_log_format(self) -> str:
        """Returns the log format for the logger."""
        return self.log_format

    def get_logger(self) -> PyLogger:
        """Returns the logger."""
        return self.logger
