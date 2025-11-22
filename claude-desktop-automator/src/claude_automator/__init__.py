"""
Claude Desktop Automator

A Python automation system for Claude Desktop App with rate limit detection
and automatic session recovery.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from .core.controller import ClaudeDesktopController
from .core.detector import LimitDetector
from .core.session import SessionManager
from .core.automator import Automator

__all__ = [
    "ClaudeDesktopController",
    "LimitDetector",
    "SessionManager",
    "Automator",
]
