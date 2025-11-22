"""Helper utilities for Claude Desktop Automator."""

import random
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import pyautogui
from PIL import Image

from .config import Config
from .logger import get_logger

logger = get_logger(__name__)


def humanized_delay(base_delay: float, variance: float = 0.2) -> None:
    """
    Sleep for a randomized duration to appear more human-like.

    Args:
        base_delay: Base delay in seconds
        variance: Variance percentage (e.g., 0.2 = ±20%)
    """
    min_delay = base_delay * (1 - variance)
    max_delay = base_delay * (1 + variance)
    actual_delay = random.uniform(min_delay, max_delay)
    time.sleep(actual_delay)


def take_screenshot(
    region: Optional[Tuple[int, int, int, int]] = None,
    save_path: Optional[Path] = None,
) -> Image.Image:
    """
    Take a screenshot of the screen or a specific region.

    Args:
        region: Optional region tuple (x, y, width, height)
        save_path: Optional path to save the screenshot

    Returns:
        PIL Image object
    """
    try:
        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()

        if save_path:
            save_path.parent.mkdir(parents=True, exist_ok=True)
            screenshot.save(str(save_path))
            logger.debug(f"Screenshot saved to {save_path}")

        return screenshot
    except Exception as e:
        logger.error(f"Failed to take screenshot: {e}")
        raise


def save_error_screenshot(config: Config, error_msg: str = "") -> Optional[Path]:
    """
    Save a screenshot when an error occurs.

    Args:
        config: Configuration object
        error_msg: Error message to include in filename

    Returns:
        Path to saved screenshot or None if disabled/failed
    """
    if not config.get("logging.screenshot_on_error", True):
        return None

    try:
        screenshot_dir = config.resolve_path(
            config.get("logging.screenshot_dir", "logs/screenshots")
        )
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_error = "".join(c for c in error_msg if c.isalnum() or c in (" ", "_"))[:50]
        filename = f"error_{timestamp}_{safe_error}.png".replace(" ", "_")

        save_path = screenshot_dir / filename
        take_screenshot(save_path=save_path)

        logger.info(f"Error screenshot saved: {save_path}")
        return save_path
    except Exception as e:
        logger.error(f"Failed to save error screenshot: {e}")
        return None


def type_text(text: str, delay_ms: int = 50, humanize: bool = True) -> None:
    """
    Type text with humanized delays.

    Args:
        text: Text to type
        delay_ms: Base delay between keystrokes in milliseconds
        humanize: Whether to add random variance to delays
    """
    delay_sec = delay_ms / 1000.0

    for char in text:
        pyautogui.write(char, interval=0)
        if humanize:
            humanized_delay(delay_sec, variance=0.3)
        else:
            time.sleep(delay_sec)


def get_window_region(window_handle) -> Optional[Tuple[int, int, int, int]]:
    """
    Get the region (bounding box) of a window.

    Args:
        window_handle: Window handle from pywinauto

    Returns:
        Tuple of (x, y, width, height) or None if failed
    """
    try:
        rect = window_handle.rectangle()
        return (rect.left, rect.top, rect.width(), rect.height())
    except Exception as e:
        logger.error(f"Failed to get window region: {e}")
        return None


def ensure_window_focused(window_handle) -> bool:
    """
    Ensure a window is focused and in foreground.

    Args:
        window_handle: Window handle from pywinauto

    Returns:
        True if successful, False otherwise
    """
    try:
        window_handle.set_focus()
        time.sleep(0.5)  # Wait for window to be focused
        return True
    except Exception as e:
        logger.error(f"Failed to focus window: {e}")
        return False


def click_at_position(x: int, y: int, clicks: int = 1, button: str = "left") -> None:
    """
    Click at a specific position with humanized movement.

    Args:
        x: X coordinate
        y: Y coordinate
        clicks: Number of clicks
        button: Mouse button ('left', 'right', 'middle')
    """
    # Move with slight randomness
    offset_x = random.randint(-2, 2)
    offset_y = random.randint(-2, 2)

    pyautogui.moveTo(x + offset_x, y + offset_y, duration=random.uniform(0.1, 0.3))
    humanized_delay(0.1)
    pyautogui.click(clicks=clicks, button=button)


def press_hotkey(*keys: str, delay: float = 0.1) -> None:
    """
    Press a keyboard hotkey combination.

    Args:
        *keys: Keys to press (e.g., 'ctrl', 'n')
        delay: Delay after pressing
    """
    pyautogui.hotkey(*keys)
    time.sleep(delay)
