"""Rate limit detection for Claude Desktop."""

import re
from typing import List, Optional

import pytesseract
from PIL import Image

from ..utils.config import Config
from ..utils.helpers import save_error_screenshot, take_screenshot
from ..utils.logger import get_logger

logger = get_logger(__name__)


class LimitDetector:
    """Detects when rate limits or message limits are reached."""

    def __init__(self, config: Optional[Config] = None) -> None:
        """
        Initialize the detector.

        Args:
            config: Configuration object. If None, uses default config.
        """
        self.config = config or Config()
        self.limit_keywords = self.config.get(
            "detection.limit_keywords",
            [
                "limit",
                "aguarde",
                "rate limit",
                "too many",
                "try again later",
                "maximum number",
            ],
        )
        self.use_ocr = self.config.get("detection.use_ocr", True)
        self.ocr_lang = self.config.get("detection.ocr_lang", "eng+por")
        self._last_detection_time: Optional[float] = None
        self._detection_count = 0

    def check_limit_reached(
        self,
        text: Optional[str] = None,
        screenshot: Optional[Image.Image] = None,
        region: Optional[tuple] = None,
    ) -> bool:
        """
        Check if rate limit has been reached.

        Args:
            text: Optional text to check. If None and use_ocr is True, will take screenshot.
            screenshot: Optional screenshot to use for OCR
            region: Optional region to screenshot (x, y, width, height)

        Returns:
            True if limit detected, False otherwise
        """
        try:
            # If text is provided, check it directly
            if text:
                return self._check_text_for_limit(text)

            # If OCR is enabled and no text provided, use OCR
            if self.use_ocr:
                if screenshot is None:
                    ocr_region = self.config.get("detection.ocr_region") or region
                    screenshot = take_screenshot(region=ocr_region)

                text = self._extract_text_from_image(screenshot)
                return self._check_text_for_limit(text)

            logger.warning("No text provided and OCR is disabled")
            return False

        except Exception as e:
            logger.error(f"Error checking for limit: {e}")
            save_error_screenshot(self.config, "limit_check_error")
            return False

    def _check_text_for_limit(self, text: str) -> bool:
        """
        Check if text contains limit-related keywords.

        Args:
            text: Text to check

        Returns:
            True if limit keywords found, False otherwise
        """
        if not text:
            return False

        text_lower = text.lower()

        for keyword in self.limit_keywords:
            # Use word boundaries for more accurate matching
            pattern = r"\b" + re.escape(keyword.lower()) + r"\b"
            if re.search(pattern, text_lower):
                logger.warning(f"Limit keyword detected: '{keyword}'")
                self._detection_count += 1
                return True

        return False

    def _extract_text_from_image(self, image: Image.Image) -> str:
        """
        Extract text from image using OCR.

        Args:
            image: PIL Image object

        Returns:
            Extracted text
        """
        try:
            # Configure tesseract
            config = f"-l {self.ocr_lang} --psm 6"
            text = pytesseract.image_to_string(image, config=config)

            logger.debug(f"OCR extracted {len(text)} characters")
            return text

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return ""

    def get_limit_type(self, text: Optional[str] = None) -> str:
        """
        Determine the type of limit that was reached.

        Args:
            text: Optional text to analyze

        Returns:
            String describing the limit type ("rate_limit", "message_limit", "unknown")
        """
        if not text:
            return "unknown"

        text_lower = text.lower()

        # Check for different types of limits
        if any(
            keyword in text_lower
            for keyword in ["rate limit", "too many requests", "try again later"]
        ):
            return "rate_limit"

        if any(
            keyword in text_lower
            for keyword in ["maximum number", "message limit", "conversation limit"]
        ):
            return "message_limit"

        if any(keyword in text_lower for keyword in ["aguarde", "wait", "espere"]):
            return "rate_limit"

        return "unknown"

    def check_error_message(
        self, screenshot: Optional[Image.Image] = None, region: Optional[tuple] = None
    ) -> Optional[str]:
        """
        Check for error messages in the Claude Desktop window.

        Args:
            screenshot: Optional screenshot to analyze
            region: Optional region to screenshot

        Returns:
            Error message if found, None otherwise
        """
        try:
            if screenshot is None:
                screenshot = take_screenshot(region=region)

            text = self._extract_text_from_image(screenshot)

            # Look for common error patterns
            error_patterns = [
                r"error[:\s]+(.*?)(?:\n|$)",
                r"sorry[,\s]+(.*?)(?:\n|$)",
                r"unable to[:\s]+(.*?)(?:\n|$)",
                r"failed to[:\s]+(.*?)(?:\n|$)",
            ]

            for pattern in error_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    error_msg = match.group(1).strip()
                    logger.warning(f"Error message detected: {error_msg}")
                    return error_msg

            return None

        except Exception as e:
            logger.error(f"Error checking for error messages: {e}")
            return None

    def reset_detection_count(self) -> None:
        """Reset the detection counter."""
        self._detection_count = 0
        logger.debug("Detection count reset")

    @property
    def detection_count(self) -> int:
        """Get the number of times limit has been detected."""
        return self._detection_count

    def is_claude_busy(
        self, screenshot: Optional[Image.Image] = None, region: Optional[tuple] = None
    ) -> bool:
        """
        Check if Claude is currently processing (typing/thinking).

        Args:
            screenshot: Optional screenshot to analyze
            region: Optional region to screenshot

        Returns:
            True if Claude appears to be busy, False otherwise
        """
        try:
            if screenshot is None:
                screenshot = take_screenshot(region=region)

            text = self._extract_text_from_image(screenshot)

            # Look for indicators that Claude is typing
            busy_indicators = [
                "typing",
                "thinking",
                "generating",
                "processing",
                "...",  # Ellipsis often indicates loading
            ]

            text_lower = text.lower()
            for indicator in busy_indicators:
                if indicator in text_lower:
                    logger.debug(f"Claude appears busy (indicator: '{indicator}')")
                    return True

            return False

        except Exception as e:
            logger.error(f"Error checking if Claude is busy: {e}")
            return False

    def check_response_complete(
        self,
        previous_text: str,
        current_text: str,
        stable_checks: int = 3,
        check_interval: float = 1.0,
    ) -> bool:
        """
        Check if response is complete by comparing text over time.

        Args:
            previous_text: Previously captured text
            current_text: Currently captured text
            stable_checks: Number of consecutive stable checks required
            check_interval: Interval between checks in seconds

        Returns:
            True if response appears complete, False otherwise
        """
        # If text hasn't changed and is not empty, response might be complete
        if current_text and previous_text == current_text:
            return True

        return False
