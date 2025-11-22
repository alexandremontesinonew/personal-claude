"""Session management for Claude Desktop Automator."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..utils.config import Config
from ..utils.logger import get_logger

logger = get_logger(__name__)


class SessionManager:
    """Manages automation sessions and context preservation."""

    def __init__(self, config: Optional[Config] = None) -> None:
        """
        Initialize the session manager.

        Args:
            config: Configuration object. If None, uses default config.
        """
        self.config = config or Config()
        self.session_dir = self.config.resolve_path(
            self.config.get("session.save_path", "logs/sessions")
        )
        self.session_dir.mkdir(parents=True, exist_ok=True)

        self.current_session: Dict[str, Any] = {
            "session_id": self._generate_session_id(),
            "start_time": datetime.now().isoformat(),
            "base_instructions": "",
            "prompts": [],
            "responses": [],
            "recoveries": 0,
            "total_messages": 0,
            "metadata": {},
        }

        self.auto_save = self.config.get("session.auto_save", True)
        self._last_save_time = datetime.now()

    def _generate_session_id(self) -> str:
        """
        Generate a unique session ID.

        Returns:
            Session ID string
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"session_{timestamp}"

    def save_context(
        self, context: Optional[Dict[str, Any]] = None, force: bool = False
    ) -> bool:
        """
        Save current session context to disk.

        Args:
            context: Optional context dict to save. If None, saves current session.
            force: Force save even if auto_save is disabled

        Returns:
            True if saved successfully, False otherwise
        """
        if not self.auto_save and not force:
            logger.debug("Auto-save disabled, skipping save")
            return False

        try:
            if context:
                save_data = context
            else:
                save_data = self.current_session.copy()

            session_id = save_data.get("session_id", self._generate_session_id())
            save_path = self.session_dir / f"{session_id}.json"

            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)

            self._last_save_time = datetime.now()
            logger.debug(f"Session saved to {save_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False

    def load_context(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Load session context from disk.

        Args:
            session_id: Session ID to load. If None, loads most recent session.

        Returns:
            Session context dict or empty dict if failed
        """
        try:
            if session_id:
                session_path = self.session_dir / f"{session_id}.json"
            else:
                # Find most recent session
                session_files = list(self.session_dir.glob("session_*.json"))
                if not session_files:
                    logger.warning("No saved sessions found")
                    return {}

                session_path = max(session_files, key=lambda p: p.stat().st_mtime)

            if not session_path.exists():
                logger.warning(f"Session file not found: {session_path}")
                return {}

            with open(session_path, "r", encoding="utf-8") as f:
                context = json.load(f)

            logger.info(f"Session loaded from {session_path}")
            return context

        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return {}

    def add_prompt(self, prompt: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a prompt to the current session.

        Args:
            prompt: Prompt text
            metadata: Optional metadata for the prompt
        """
        prompt_entry = {
            "timestamp": datetime.now().isoformat(),
            "text": prompt,
            "metadata": metadata or {},
        }

        self.current_session["prompts"].append(prompt_entry)
        self.current_session["total_messages"] += 1

        if self.auto_save:
            self._auto_save_if_needed()

    def add_response(self, response: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a response to the current session.

        Args:
            response: Response text
            metadata: Optional metadata for the response
        """
        response_entry = {
            "timestamp": datetime.now().isoformat(),
            "text": response,
            "metadata": metadata or {},
        }

        self.current_session["responses"].append(response_entry)
        self.current_session["total_messages"] += 1

        if self.auto_save:
            self._auto_save_if_needed()

    def record_recovery(self, reason: str, success: bool) -> None:
        """
        Record a recovery attempt.

        Args:
            reason: Reason for recovery
            success: Whether recovery was successful
        """
        recovery_entry = {
            "timestamp": datetime.now().isoformat(),
            "reason": reason,
            "success": success,
            "message_count": self.current_session["total_messages"],
        }

        if "recovery_history" not in self.current_session:
            self.current_session["recovery_history"] = []

        self.current_session["recovery_history"].append(recovery_entry)
        self.current_session["recoveries"] += 1

        logger.info(f"Recovery recorded: {reason} (success: {success})")

        if self.auto_save:
            self.save_context(force=True)

    def set_base_instructions(self, instructions: str) -> None:
        """
        Set base instructions for the session.

        Args:
            instructions: Base instructions text
        """
        self.current_session["base_instructions"] = instructions
        logger.debug("Base instructions set")

    def get_base_instructions(self) -> str:
        """
        Get base instructions for the session.

        Returns:
            Base instructions text
        """
        return self.current_session.get("base_instructions", "")

    def get_last_prompt(self) -> Optional[str]:
        """
        Get the last prompt sent in this session.

        Returns:
            Last prompt text or None if no prompts sent
        """
        prompts = self.current_session.get("prompts", [])
        if prompts:
            return prompts[-1]["text"]
        return None

    def get_last_response(self) -> Optional[str]:
        """
        Get the last response received in this session.

        Returns:
            Last response text or None if no responses received
        """
        responses = self.current_session.get("responses", [])
        if responses:
            return responses[-1]["text"]
        return None

    def get_conversation_history(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get conversation history as alternating prompts and responses.

        Args:
            last_n: Optional number of last exchanges to return

        Returns:
            List of conversation exchanges
        """
        prompts = self.current_session.get("prompts", [])
        responses = self.current_session.get("responses", [])

        # Interleave prompts and responses
        conversation = []
        max_len = max(len(prompts), len(responses))

        for i in range(max_len):
            if i < len(prompts):
                conversation.append({"role": "user", "content": prompts[i]})
            if i < len(responses):
                conversation.append({"role": "assistant", "content": responses[i]})

        if last_n:
            return conversation[-last_n * 2 :]  # *2 because each exchange has 2 messages

        return conversation

    def _auto_save_if_needed(self) -> None:
        """Automatically save if enough time has passed."""
        save_interval = self.config.get("session.save_interval_sec", 60)
        elapsed = (datetime.now() - self._last_save_time).total_seconds()

        if elapsed >= save_interval:
            self.save_context()

    def recover_session(self, session_id: Optional[str] = None) -> bool:
        """
        Recover a previous session.

        Args:
            session_id: Session ID to recover. If None, recovers most recent.

        Returns:
            True if recovered successfully, False otherwise
        """
        try:
            context = self.load_context(session_id)
            if not context:
                logger.error("No session context to recover")
                return False

            # Create a new session but preserve important context
            old_session_id = context.get("session_id")
            new_session_id = self._generate_session_id()

            self.current_session = {
                "session_id": new_session_id,
                "start_time": datetime.now().isoformat(),
                "recovered_from": old_session_id,
                "base_instructions": context.get("base_instructions", ""),
                "prompts": [],  # Start fresh
                "responses": [],
                "recoveries": 0,
                "total_messages": 0,
                "metadata": context.get("metadata", {}),
            }

            logger.info(f"Session recovered from {old_session_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to recover session: {e}")
            return False

    def export_session(self, output_path: Optional[Path] = None) -> bool:
        """
        Export current session to a file.

        Args:
            output_path: Path to export to. If None, uses default location.

        Returns:
            True if exported successfully, False otherwise
        """
        try:
            if output_path is None:
                output_path = (
                    self.session_dir / f"{self.current_session['session_id']}_export.json"
                )

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(self.current_session, f, indent=2, ensure_ascii=False)

            logger.info(f"Session exported to {output_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export session: {e}")
            return False

    def clear_session(self) -> None:
        """Clear current session data (start fresh)."""
        self.current_session = {
            "session_id": self._generate_session_id(),
            "start_time": datetime.now().isoformat(),
            "base_instructions": "",
            "prompts": [],
            "responses": [],
            "recoveries": 0,
            "total_messages": 0,
            "metadata": {},
        }
        logger.info("Session cleared")

    def get_session_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current session.

        Returns:
            Dict containing session statistics
        """
        return {
            "session_id": self.current_session["session_id"],
            "start_time": self.current_session["start_time"],
            "total_messages": self.current_session["total_messages"],
            "prompts_sent": len(self.current_session["prompts"]),
            "responses_received": len(self.current_session["responses"]),
            "recoveries": self.current_session["recoveries"],
            "uptime_minutes": (
                datetime.now()
                - datetime.fromisoformat(self.current_session["start_time"])
            ).total_seconds()
            / 60,
        }
