"""Logging setup for Claude Desktop Automator."""

import sys
from pathlib import Path
from typing import Optional

from loguru import logger

from .config import Config


class Logger:
    """Logger configuration and management."""

    _initialized = False

    @classmethod
    def setup(cls, config: Optional[Config] = None) -> None:
        """
        Setup logging configuration.

        Args:
            config: Configuration object. If None, uses default config.
        """
        if cls._initialized:
            return

        if config is None:
            config = Config()

        # Remove default handler
        logger.remove()

        # Get logging config
        log_config = config.logging
        level = log_config.get("level", "INFO")
        log_file = config.resolve_path(log_config.get("file", "logs/automator.log"))
        max_size = log_config.get("max_file_size_mb", 10) * 1024 * 1024  # Convert to bytes
        backup_count = log_config.get("backup_count", 5)
        console = log_config.get("console", True)

        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Add console handler if enabled
        if console:
            logger.add(
                sys.stderr,
                format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
                level=level,
                colorize=True,
            )

        # Add file handler
        logger.add(
            str(log_file),
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=level,
            rotation=max_size,
            retention=backup_count,
            compression="zip",
        )

        cls._initialized = True
        logger.info("Logger initialized")

    @staticmethod
    def get_logger(name: str = "claude_automator"):
        """
        Get logger instance.

        Args:
            name: Logger name

        Returns:
            Logger instance
        """
        return logger.bind(name=name)


def get_logger(name: str = "claude_automator"):
    """
    Get logger instance (convenience function).

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return Logger.get_logger(name)
