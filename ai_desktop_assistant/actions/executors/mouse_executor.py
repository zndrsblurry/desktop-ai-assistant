# Location: ai_desktop_assistant/actions/executors/mouse_executor.py
"""
Mouse Executor

This module implements the mouse action executor.
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
from ai_desktop_assistant.core.exceptions import ActionError
from ai_desktop_assistant.interfaces.action_executor import ActionExecutor


class MouseExecutor(ActionExecutor):
    """Implementation of the mouse action executor."""

    # Set of supported action types
    SUPPORTED_ACTIONS: Set[str] = {
        "mouse_move",
        "mouse_click",
        "mouse_drag",
        "mouse_scroll",
    }

    def __init__(self, event_bus: EventBus):
        """
        Initialize the mouse executor.

        Args:
            event_bus: The application event bus
        """
        self.logger = logging.getLogger(__name__)
        self.event_bus = event_bus

        if PYAUTOGUI_AVAILABLE:
            # Configure PyAutoGUI
            pyautogui.FAILSAFE = True  # Move mouse to corner to abort
            pyautogui.PAUSE = 0.1  # Add small delay between actions

    async def initialize(self) -> None:
        """Initialize the mouse executor."""
        if not PYAUTOGUI_AVAILABLE:
            self.logger.warning(
                "PyAutoGUI not available. Mouse actions will not be available."
            )
            return

        self.logger.info("Initializing mouse executor")
        self.logger.info("Mouse executor initialized")

    async def shutdown(self) -> None:
        """Shut down the mouse executor."""
        self.logger.info("Shutting down mouse executor")
        self.logger.info("Mouse executor shut down")

    async def execute_action(
        self, action_type: str, params: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Execute a mouse action.

        Args:
            action_type: The type of action to execute
            params: Action parameters

        Returns:
            The action result or None if the action doesn't produce a result

        Raises:
            ActionError: If execution fails
        """
        if not PYAUTOGUI_AVAILABLE:
            raise ActionError(
                "PyAutoGUI not available. Mouse actions are not supported."
            )

        if not self.can_execute(action_type):
            raise ActionError(f"Unsupported action type: {action_type}")

        try:
            if action_type == "mouse_move":
                await self._mouse_move(params)
            elif action_type == "mouse_click":
                await self._mouse_click(params)
            elif action_type == "mouse_drag":
                await self._mouse_drag(params)
            elif action_type == "mouse_scroll":
                await self._mouse_scroll(params)

            return None

        except Exception as e:
            self.logger.error(f"Error executing mouse action {action_type}: {e}")
            raise ActionError(f"Failed to execute mouse action {action_type}: {e}")

    def can_execute(self, action_type: str) -> bool:
        """
        Check if this executor can execute the given action type.

        Args:
            action_type: The action type to check

        Returns:
            True if this executor can execute the action, False otherwise
        """
        return action_type in self.SUPPORTED_ACTIONS

    async def _mouse_move(self, params: Dict[str, Any]) -> None:
        """
        Move the mouse to a position.

        Args:
            params: Action parameters
                x: X coordinate
                y: Y coordinate
                duration: Movement duration in seconds (optional)
        """
        # Get parameters
        x = params.get("x")
        y = params.get("y")
        duration = params.get("duration", 0.5)

        # Validate parameters
        if x is None or y is None:
            raise ActionError("Missing required parameters: x and y")

        # Execute in a thread to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: pyautogui.moveTo(x, y, duration=duration)
        )

    async def _mouse_click(self, params: Dict[str, Any]) -> None:
        """
        Click the mouse.

        Args:
            params: Action parameters
                button: Mouse button (left, right, middle)
                clicks: Number of clicks
                x: X coordinate (optional)
                y: Y coordinate (optional)
        """
        # Get parameters
        button = params.get("button", "left")
        clicks = params.get("clicks", 1)
        x = params.get("x")
        y = params.get("y")

        # Execute in a thread to avoid blocking
        loop = asyncio.get_event_loop()

        if x is not None and y is not None:
            # Click at the specified position
            await loop.run_in_executor(
                None, lambda: pyautogui.click(x, y, clicks=clicks, button=button)
            )
        else:
            # Click at the current position
            await loop.run_in_executor(
                None, lambda: pyautogui.click(clicks=clicks, button=button)
            )

    async def _mouse_drag(self, params: Dict[str, Any]) -> None:
        """
        Drag the mouse from one position to another.

        Args:
            params: Action parameters
                start_x: Starting X coordinate
                start_y: Starting Y coordinate
                end_x: Ending X coordinate
                end_y: Ending Y coordinate
                button: Mouse button (left, right, middle)
                duration: Drag duration in seconds (optional)
        """
        # Get parameters
        start_x = params.get("start_x")
        start_y = params.get("start_y")
        end_x = params.get("end_x")
        end_y = params.get("end_y")
        button = params.get("button", "left")
        duration = params.get("duration", 0.5)

        # Validate parameters
        if start_x is None or start_y is None or end_x is None or end_y is None:
            raise ActionError(
                "Missing required parameters: start_x, start_y, end_x, end_y"
            )

        # Execute in a thread to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: pyautogui.dragTo(
                end_x, end_y, button=button, duration=duration, _pause=False
            ),
        )

    async def _mouse_scroll(self, params: Dict[str, Any]) -> None:
        """
        Scroll the mouse wheel.

        Args:
            params: Action parameters
                clicks: Number of clicks (positive for up, negative for down)
        """
        # Get parameters
        clicks = params.get("clicks", 1)

        # Execute in a thread to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: pyautogui.scroll(clicks))
