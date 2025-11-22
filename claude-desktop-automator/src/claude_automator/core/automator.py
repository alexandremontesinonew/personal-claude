"""Main automation orchestrator for Claude Desktop."""

import time
from pathlib import Path
from typing import List, Optional

from ..utils.config import Config
from ..utils.helpers import humanized_delay, save_error_screenshot
from ..utils.logger import get_logger
from .controller import ClaudeDesktopController
from .detector import LimitDetector
from .session import SessionManager

logger = get_logger(__name__)


class Automator:
    """Main orchestrator for Claude Desktop automation."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize the automator.

        Args:
            config_path: Optional path to config file
        """
        self.config = Config(config_path) if config_path else Config()

        # Initialize components
        self.controller = ClaudeDesktopController(self.config)
        self.detector = LimitDetector(self.config)
        self.session = SessionManager(self.config)

        self._is_running = False
        self._recovery_attempts = 0
        self._max_recovery_attempts = self.config.get("recovery.max_recovery_attempts", 5)

        logger.info("Automator initialized")

    def initialize(self) -> bool:
        """
        Initialize the automation (connect to window, load instructions).

        Returns:
            True if successful, False otherwise
        """
        logger.info("Initializing automator...")

        # Find Claude Desktop window
        if not self.controller.find_window():
            logger.error("Failed to find Claude Desktop window")
            return False

        # Load base instructions if specified
        instructions_path = self.config.get("automation.base_instructions")
        if instructions_path:
            instructions_file = self.config.resolve_path(instructions_path)
            if instructions_file.exists():
                with open(instructions_file, "r", encoding="utf-8") as f:
                    base_instructions = f.read()
                self.session.set_base_instructions(base_instructions)
                logger.info("Base instructions loaded")

                # Send base instructions
                if not self.send_with_retry(base_instructions):
                    logger.warning("Failed to send base instructions")
            else:
                logger.warning(f"Base instructions file not found: {instructions_file}")

        logger.info("Automator initialized successfully")
        return True

    def run(self, prompts: List[str], interactive: bool = False) -> bool:
        """
        Run automation with a list of prompts.

        Args:
            prompts: List of prompts to send
            interactive: If True, waits for user confirmation between prompts

        Returns:
            True if completed successfully, False otherwise
        """
        if not self._is_running:
            if not self.initialize():
                logger.error("Initialization failed")
                return False

        self._is_running = True

        try:
            for i, prompt in enumerate(prompts):
                logger.info(f"Processing prompt {i + 1}/{len(prompts)}")

                # Send prompt with retry
                response = self.send_with_retry(prompt)

                if response is None:
                    logger.error(f"Failed to process prompt {i + 1}")
                    if not self._attempt_recovery():
                        logger.error("Recovery failed, stopping automation")
                        return False

                    # Retry the same prompt after recovery
                    response = self.send_with_retry(prompt)
                    if response is None:
                        logger.error(f"Failed to process prompt {i + 1} after recovery")
                        return False

                # Check for rate limit
                if self.detector.check_limit_reached(text=response):
                    logger.warning("Rate limit detected")
                    if not self._attempt_recovery():
                        logger.error("Recovery failed after rate limit")
                        return False

                    # Retry the same prompt after recovery
                    response = self.send_with_retry(prompt)
                    if response is None:
                        logger.error(f"Failed to process prompt {i + 1} after rate limit")
                        return False

                # Interactive mode: wait for user
                if interactive and i < len(prompts) - 1:
                    input("Press Enter to continue to next prompt...")

            logger.info("All prompts processed successfully")
            return True

        except KeyboardInterrupt:
            logger.info("Automation interrupted by user")
            return False
        except Exception as e:
            logger.error(f"Automation error: {e}")
            save_error_screenshot(self.config, "automation_error")
            return False
        finally:
            self._is_running = False

    def send_with_retry(self, prompt: str) -> Optional[str]:
        """
        Send a prompt with automatic retry on failure.

        Args:
            prompt: Prompt text to send

        Returns:
            Response text or None if failed
        """
        max_retries = self.config.get("automation.max_retries", 3)
        retry_delay = self.config.get("automation.retry_delay_sec", 5)

        for attempt in range(max_retries):
            try:
                logger.debug(f"Sending prompt (attempt {attempt + 1}/{max_retries})")

                # Send the prompt
                if not self.controller.send_prompt(prompt):
                    logger.warning(f"Failed to send prompt (attempt {attempt + 1})")
                    if attempt < max_retries - 1:
                        humanized_delay(retry_delay)
                        continue
                    return None

                # Record the prompt
                self.session.add_prompt(prompt)

                # Wait for response
                timeout = self.config.get("claude_desktop.response_timeout_sec", 120)
                if not self.controller.wait_for_response_complete(timeout):
                    logger.warning("Response timeout")
                    if attempt < max_retries - 1:
                        humanized_delay(retry_delay)
                        continue
                    return None

                # Read the response
                response = self.controller.read_response()
                if not response:
                    logger.warning("Failed to read response")
                    if attempt < max_retries - 1:
                        humanized_delay(retry_delay)
                        continue
                    return None

                # Record the response
                self.session.add_response(response)

                logger.info("Prompt processed successfully")
                return response

            except Exception as e:
                logger.error(f"Error sending prompt (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    humanized_delay(retry_delay)
                    continue
                return None

        logger.error(f"Failed to send prompt after {max_retries} attempts")
        return None

    def _attempt_recovery(self) -> bool:
        """
        Attempt to recover from error or rate limit.

        Returns:
            True if recovery successful, False otherwise
        """
        if self._recovery_attempts >= self._max_recovery_attempts:
            logger.error(
                f"Maximum recovery attempts ({self._max_recovery_attempts}) reached"
            )
            return False

        self._recovery_attempts += 1
        logger.info(f"Attempting recovery (attempt {self._recovery_attempts})")

        try:
            # Save current context
            self.session.save_context(force=True)

            # Start new chat
            if not self.controller.start_new_chat():
                logger.error("Failed to start new chat")
                self.session.record_recovery("new_chat_failed", False)
                return False

            # Restore base instructions
            base_instructions = self.session.get_base_instructions()
            if base_instructions:
                logger.info("Restoring base instructions")
                if not self.controller.send_prompt(base_instructions):
                    logger.warning("Failed to restore base instructions")
                    self.session.record_recovery("restore_instructions_failed", False)
                    return False

                # Wait for response
                timeout = self.config.get("claude_desktop.response_timeout_sec", 120)
                self.controller.wait_for_response_complete(timeout)

            # Reset recovery counter on success
            self._recovery_attempts = 0
            self.detector.reset_detection_count()

            logger.info("Recovery successful")
            self.session.record_recovery("rate_limit", True)
            return True

        except Exception as e:
            logger.error(f"Recovery failed: {e}")
            self.session.record_recovery("exception", False)
            save_error_screenshot(self.config, "recovery_error")
            return False

    def send_interactive(self) -> None:
        """Run in interactive mode (user enters prompts one by one)."""
        if not self.initialize():
            logger.error("Initialization failed")
            return

        logger.info("Interactive mode started. Type 'exit' or 'quit' to stop.")

        try:
            while True:
                prompt = input("\n> ")

                if prompt.lower() in ["exit", "quit", "q"]:
                    logger.info("Exiting interactive mode")
                    break

                if not prompt.strip():
                    continue

                response = self.send_with_retry(prompt)

                if response:
                    print(f"\nClaude: {response}\n")
                else:
                    print("\nFailed to get response. Attempting recovery...")
                    if self._attempt_recovery():
                        print("Recovery successful. Please try again.")
                    else:
                        print("Recovery failed. Exiting.")
                        break

        except KeyboardInterrupt:
            logger.info("Interactive mode interrupted")
        except Exception as e:
            logger.error(f"Interactive mode error: {e}")

    def send_batch(self, prompts_file: Path) -> bool:
        """
        Run automation with prompts from a file.

        Args:
            prompts_file: Path to file containing prompts (one per line)

        Returns:
            True if successful, False otherwise
        """
        if not prompts_file.exists():
            logger.error(f"Prompts file not found: {prompts_file}")
            return False

        with open(prompts_file, "r", encoding="utf-8") as f:
            prompts = [line.strip() for line in f if line.strip()]

        logger.info(f"Loaded {len(prompts)} prompts from {prompts_file}")
        return self.run(prompts)

    def get_stats(self) -> dict:
        """
        Get automation statistics.

        Returns:
            Dict containing statistics
        """
        stats = self.session.get_session_stats()
        stats["recovery_attempts"] = self._recovery_attempts
        stats["limit_detections"] = self.detector.detection_count
        return stats

    def stop(self) -> None:
        """Stop the automation and cleanup."""
        logger.info("Stopping automator...")

        self._is_running = False

        # Save final session
        self.session.save_context(force=True)

        # Close controller
        self.controller.close()

        logger.info("Automator stopped")

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
