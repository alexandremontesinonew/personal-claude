"""Tests for configuration module."""

import pytest
from pathlib import Path
from claude_automator.utils.config import Config


def test_config_initialization():
    """Test config initialization."""
    # This test requires the config file to exist
    # In a real test suite, you'd use a fixture with a test config
    pass


def test_config_get():
    """Test config.get() method."""
    # Mock config for testing
    config = Config.__new__(Config)
    config._config = {
        "claude_desktop": {
            "window_title": "Claude",
            "input_delay_ms": 50
        }
    }

    assert config.get("claude_desktop.window_title") == "Claude"
    assert config.get("claude_desktop.input_delay_ms") == 50
    assert config.get("nonexistent.key", "default") == "default"


def test_config_properties():
    """Test config property accessors."""
    config = Config.__new__(Config)
    config._config = {
        "claude_desktop": {"window_title": "Claude"},
        "automation": {"max_retries": 3}
    }

    assert config.claude_desktop == {"window_title": "Claude"}
    assert config.automation == {"max_retries": 3}


# Add more tests as needed
