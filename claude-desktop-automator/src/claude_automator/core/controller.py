"""Claude Desktop window controller."""

import time
from typing import Optional

import pyautogui
import pyperclip
from pywinauto import Application
from pywinauto.findwindows import ElementNotFoundError

from ..utils.config import Config
from ..utils.helpers import (
    ensure_window_focused,
    get_window_region,
    humanized_delay,
    press_hotkey,
    save_error_screenshot,
    type_text,
)
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ClaudeDesktopController:
    """Controls the Claude Desktop application window."""

    def __init__(self, config: Optional[Config] = None) -> None:
        """
        Initialize the controller.

        Args:
            config: Configuration object. If None, uses default config.
        """
        self.config = config or Config()
        self.window = None
        self.app = None
        self._last_response = ""

    def find_window(self) -> bool:
        """
        Find and connect to Claude Desktop window.

        Returns:
            True if window found, False otherwise
        """
        window_title = self.config.get("claude_desktop.window_title", "Claude")
        window_class = self.config.get("claude_desktop.window_class")

        logger.info(f"Searching for Claude Desktop window (title: {window_title})")

        try:
            # Try to find by title first
            if window_title:
                self.app = Application(backend="uia").connect(
                    title_re=f".*{window_title}.*", timeout=5
                )
                self.window = self.app.window(title_re=f".*{window_title}.*")

            # Fallback to class name if specified
            elif window_class:
                self.app = Application(backend="uia").connect(
                    class_name=window_class, timeout=5
                )
                self.window = self.app.window(class_name=window_class)
            else:
                logger.error("No window title or class specified in config")
                return False

            logger.info("Claude Desktop window found")
            return True

        except ElementNotFoundError:
            logger.warning(
                f"Claude Desktop window not found. "
                f"Make sure Claude Desktop is running and the window title contains '{window_title}'"
            )
            return False
        except Exception as e:
            logger.error(f"Error finding window: {e}")
            save_error_screenshot(self.config, "find_window_error")
            return False

    def send_prompt(self, text: str, use_clipboard: bool = True) -> bool:
        """
        Send a prompt to Claude Desktop.

        Args:
            text: Text to send
            use_clipboard: If True, uses clipboard for faster/more reliable input

        Returns:
            True if successful, False otherwise
        """
        if not self.window:
            logger.error("Window not connected. Call find_window() first.")
            return False

        try:
            # Ensure window is focused
            if not ensure_window_focused(self.window):
                logger.error("Failed to focus Claude Desktop window")
                return False

            logger.info(f"Sending prompt ({len(text)} characters)")

            if use_clipboard:
                # Use clipboard for faster input (less prone to missing characters)
                pyperclip.copy(text)
                humanized_delay(0.2)
                press_hotkey("ctrl", "v")
            else:
                # Type character by character
                delay_ms = self.config.get("claude_desktop.input_delay_ms", 50)
                humanize = self.config.get("automation.humanize_delays", True)
                type_text(text, delay_ms=delay_ms, humanize=humanize)

            # Wait a bit before pressing Enter
            initial_wait = self.config.get("claude_desktop.initial_wait_sec", 2)
            humanized_delay(initial_wait)

            # Press Enter to send
            press_hotkey("enter")

            logger.info("Prompt sent successfully")
            return True

        except Exception as e:
            logger.error(f"Error sending prompt: {e}")
            save_error_screenshot(self.config, "send_prompt_error")
            return False

    def read_response(self, use_clipboard: bool = True) -> str:
        """
        Read the latest response from Claude.

        Args:
            use_clipboard: If True, uses clipboard to read response (more reliable)

        Returns:
            Response text or empty string if failed
        """
        if not self.window:
            logger.error("Window not connected. Call find_window() first.")
            return ""

        try:
            if not ensure_window_focused(self.window):
                logger.error("Failed to focus window for reading response")
                return ""

            if use_clipboard:
                # Select all text in the last message (this is app-specific and may need adjustment)
                # For now, we'll use a simple approach: triple-click to select paragraph
                # then copy to clipboard

                # Note: This is a simplified implementation. In production, you might need
                # to use OCR or more sophisticated methods to read the response.

                pyperclip.copy("")  # Clear clipboard

                # Try to select and copy the response
                # This might need adjustment based on Claude Desktop's actual UI
                press_hotkey("ctrl", "a")
                humanized_delay(0.2)
                press_hotkey("ctrl", "c")
                humanized_delay(0.3)

                response = pyperclip.paste()
                self._last_response = response

                logger.debug(f"Read response ({len(response)} characters)")
                return response
            else:
                # Fallback: use OCR (implemented in LimitDetector)
                logger.warning("OCR-based response reading not implemented in this method")
                return ""

        except Exception as e:
            logger.error(f"Error reading response: {e}")
            save_error_screenshot(self.config, "read_response_error")
            return ""

    def start_new_chat(self) -> bool:
        """
        Start a new chat in Claude Desktop.

        Returns:
            True if successful, False otherwise
        """
        if not self.window:
            logger.error("Window not connected. Call find_window() first.")
            return False

        try:
            logger.info("Starting new chat")

            if not ensure_window_focused(self.window):
                logger.error("Failed to focus window for new chat")
                return False

            # Press Ctrl+N to start new chat
            press_hotkey("ctrl", "n")

            # Wait for new chat to be ready
            delay = self.config.get("recovery.new_chat_delay_sec", 3)
            humanized_delay(delay)

            logger.info("New chat started successfully")
            return True

        except Exception as e:
            logger.error(f"Error starting new chat: {e}")
            save_error_screenshot(self.config, "new_chat_error")
            return False

    def is_responding(self) -> bool:
        """
        Check if Claude is currently generating a response.

        Note: This is a simplified implementation. In production, you might want to
        check for specific UI elements that indicate Claude is typing.

        Returns:
            True if currently responding, False otherwise
        """
        # This is a placeholder implementation
        # In a real scenario, you'd check for UI elements like a "typing" indicator
        # or monitor for changes in the response area

        # For now, we'll just return False
        # You can enhance this by:
        # 1. Looking for specific UI elements (loading spinner, etc.)
        # 2. Using OCR to detect "Claude is typing..." text
        # 3. Monitoring changes in the window content

        return False

    def wait_for_response_complete(self, timeout: Optional[int] = None) -> bool:
        """
        Wait until Claude finishes responding.

        Args:
            timeout: Maximum time to wait in seconds. If None, uses config value.

        Returns:
            True if response completed, False if timeout
        """
        if timeout is None:
            timeout = self.config.get("claude_desktop.response_timeout_sec", 120)

        logger.info(f"Waiting for response (timeout: {timeout}s)")

        check_interval = self.config.get("detection.check_interval_sec", 2)
        elapsed = 0

        while elapsed < timeout:
            if not self.is_responding():
                logger.info("Response completed")
                return True

            time.sleep(check_interval)
            elapsed += check_interval

        logger.warning(f"Response timeout after {timeout}s")
        return False

    def get_window_region(self) -> Optional[tuple]:
        """
        Get the window's screen region.

        Returns:
            Tuple of (x, y, width, height) or None if failed
        """
        if not self.window:
            logger.error("Window not connected")
            return None

        return get_window_region(self.window)

    def is_window_available(self) -> bool:
        """
        Check if the window is still available and responsive.

        Returns:
            True if window is available, False otherwise
        """
        if not self.window:
            return False

        try:
            # Try to access window properties
            self.window.is_enabled()
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close the connection to the window."""
        self.window = None
        self.app = None
        logger.info("Controller closed")
