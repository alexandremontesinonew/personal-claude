"""Configuration management for Claude Desktop Automator."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv


class Config:
    """Configuration manager for the automator."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize configuration.

        Args:
            config_path: Path to config.yaml file. If None, uses default location.
        """
        # Load environment variables
        load_dotenv()

        # Determine project root
        self.project_root = Path(__file__).parent.parent.parent.parent

        # Load config file
        if config_path is None:
            config_path = str(self.project_root / "config" / "config.yaml")

        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        return config or {}

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.

        Args:
            key_path: Configuration key path (e.g., "claude_desktop.window_title")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key_path.split(".")
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable.

        Args:
            key: Environment variable name
            default: Default value if not found

        Returns:
            Environment variable value or default
        """
        return os.getenv(key, default)

    def resolve_path(self, path: str) -> Path:
        """
        Resolve path relative to project root.

        Args:
            path: Path string (can be relative or absolute)

        Returns:
            Absolute Path object
        """
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj
        return self.project_root / path

    @property
    def claude_desktop(self) -> Dict[str, Any]:
        """Get Claude Desktop configuration section."""
        return self._config.get("claude_desktop", {})

    @property
    def automation(self) -> Dict[str, Any]:
        """Get automation configuration section."""
        return self._config.get("automation", {})

    @property
    def detection(self) -> Dict[str, Any]:
        """Get detection configuration section."""
        return self._config.get("detection", {})

    @property
    def recovery(self) -> Dict[str, Any]:
        """Get recovery configuration section."""
        return self._config.get("recovery", {})

    @property
    def logging(self) -> Dict[str, Any]:
        """Get logging configuration section."""
        return self._config.get("logging", {})

    @property
    def session(self) -> Dict[str, Any]:
        """Get session configuration section."""
        return self._config.get("session", {})
