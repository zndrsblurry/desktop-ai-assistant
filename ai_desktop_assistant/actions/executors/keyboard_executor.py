# Location: ai_desktop_assistant/actions/executors/keyboard_executor.py
"""
Keyboard Executor

This module implements the keyboard action executor.
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Set

try:
    import pyautogui

    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

from ai_desktop_assistant.core.events import EventBus
from ai_desktop_assistant.core.exceptions import ActionError, SecurityError
from ai_desktop_assistant.interfaces.action_executor import ActionExecutor


class KeyboardExecutor(ActionExecutor):
    """Implementation of the keyboard action executor."""

    # Set of supported action types
    SUPPORTED_ACTIONS: Set[str] = {"keyboard_type", "keyboard_press", "keyboard_hotkey"}

    # Set of disallowed key combinations for security reasons
    DISALLOWED_KEYS: Set[str] = {
        "win",
        "command",
        "cmd",  # Windows/Mac OS key
        "alt+f4",  # Close application
        "ctrl+alt+del",
        "ctrl+shift+esc",  # System operations
    }

    def __init__(self, event_bus: EventBus):
        """
        Initialize the keyboard executor.

        Args:
            event_bus: The application event bus
        """
        self.logger = logging.getLogger(__name__)
        self.event_bus = event_bus

    async def initialize(self) -> None:
        """Initialize the keyboard executor."""
        if not PYAUTOGUI_AVAILABLE:
            self.logger.warning(
                "PyAutoGUI not available. Keyboard actions will not be available."
            )
            return

        self.logger.info("Initializing keyboard executor")
        self.logger.info("Keyboard executor initialized")

    async def shutdown(self) -> None:
        """Shut down the keyboard executor."""
        self.logger.info("Shutting down keyboard executor")
        self.logger.info("Keyboard executor shut down")

    async def execute_action(
        self, action_type: str, params: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Execute a keyboard action.

        Args:
            action_type: The type of action to execute
            params: Action parameters

        Returns:
            The action result or None if the action doesn't produce a result

        Raises:
            ActionError: If execution fails
            SecurityError: If a disallowed key combination is attempted
        """
        if not PYAUTOGUI_AVAILABLE:
            raise ActionError(
                "PyAutoGUI not available. Keyboard actions are not supported."
            )

        if not self.can_execute(action_type):
            raise ActionError(f"Unsupported action type: {action_type}")

        try:
            if action_type == "keyboard_type":
                await self._keyboard_type(params)
            elif action_type == "keyboard_press":
                await self._keyboard_press(params)
            elif action_type == "keyboard_hotkey":
                await self._keyboard_hotkey(params)

            return None

        except Exception as e:
            self.logger.error(f"Error executing keyboard action {action_type}: {e}")
            raise ActionError(f"Failed to execute keyboard action {action_type}: {e}")

    def can_execute(self, action_type: str) -> bool:
        """
        Check if this executor can execute the given action type.

        Args:
            action_type: The action type to check

        Returns:
            True if this executor can execute the action, False otherwise
        """
        return action_type in self.SUPPORTED_ACTIONS

    def _check_security(self, key: str) -> None:
        """
        Check if a key or key combination is allowed.

        Args:
            key: The key or key combination to check

        Raises:
            SecurityError: If the key is disallowed
        """
        key_lower = key.lower()

        # Check if the key is in the disallowed list
        if key_lower in self.DISALLOWED_KEYS:
            raise SecurityError(f"Disallowed key or key combination: {key}")

        # Check for Windows key combinations
        if (
            key_lower.startswith("win+")
            or key_lower.startswith("command+")
            or key_lower.startswith("cmd+")
        ):
            raise SecurityError(
                f"Disallowed key combination with Windows/Command key: {key}"
            )

    async def _keyboard_type(self, params: Dict[str, Any]) -> None:
        """
        Type text.

        Args:
            params: Action parameters
                text: The text to type
                interval: Time between keypresses in seconds (optional)
        """
        # Get parameters
        text = params.get("text")
        interval = params.get("interval", 0.0)

        # Validate parameters
        if text is None:
            raise ActionError("Missing required parameter: text")

        # Execute in a thread to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: pyautogui.write(text, interval=interval)
        )

    async def _keyboard_press(self, params: Dict[str, Any]) -> None:
        """
        Press a key.

        Args:
            params: Action parameters
                key: The key to press
        """
        # Get parameters
        key = params.get("key")

        # Validate parameters
        if key is None:
            raise ActionError("Missing required parameter: key")

        # Check security
        self._check_security(key)

        # Execute in a thread to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: pyautogui.press(key))

    async def _keyboard_hotkey(self, params: Dict[str, Any]) -> None:
        """
        Press a key combination.

        Args:
            params: Action parameters
                keys: The keys to press (list)
        """
        # Get parameters
        keys = params.get("keys")

        # Validate parameters
        if not keys or not isinstance(keys, list):
            raise ActionError("Missing or invalid required parameter: keys")

        # Check security for each key
        for key in keys:
            self._check_security(key)

        # Check security for the key combination
        hotkey = "+".join(keys).lower()
        self._check_security(hotkey)

        # Execute in a thread to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: pyautogui.hotkey(*keys))
