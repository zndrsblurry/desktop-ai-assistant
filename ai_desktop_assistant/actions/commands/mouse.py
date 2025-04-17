# Location: ai_desktop_assistant/actions/commands/mouse.py
"""
Mouse Commands

This module defines command classes for mouse actions.
"""

from ai_desktop_assistant.actions.commands.base import BaseCommand
from ai_desktop_assistant.core.exceptions import ActionError


class MouseMoveCommand(BaseCommand):
    """Command for moving the mouse to a position."""

    async def execute(self) -> None:
        """
        Execute the mouse move command.

        Returns:
            None

        Raises:
            ActionError: If execution fails
        """
        try:
            # Validate parameters
            self.validate_params(["x", "y"])

            # Get parameters
            x = self.params["x"]
            y = self.params["y"]

            # Execute the action
            await self.executor.execute_action("mouse_move", {"x": x, "y": y})

            # Mark as executed
            self._set_executed()

        except Exception as e:
            self.logger.error(f"Error executing mouse move command: {e}")
            raise ActionError(f"Failed to execute mouse move command: {e}")

    async def undo(self) -> None:
        """
        Undo the mouse move command.

        Note: Mouse move commands cannot be undone in a meaningful way.
        """
        self.logger.warning("Cannot undo mouse move command")


class MouseClickCommand(BaseCommand):
    """Command for clicking the mouse."""

    async def execute(self) -> None:
        """
        Execute the mouse click command.

        Returns:
            None

        Raises:
            ActionError: If execution fails
        """
        try:
            # Get parameters with defaults
            button = self.params.get("button", "left")
            double = self.params.get("double", False)

            # Execute the action
            await self.executor.execute_action(
                "mouse_click", {"button": button, "double": double}
            )

            # Mark as executed
            self._set_executed()

        except Exception as e:
            self.logger.error(f"Error executing mouse click command: {e}")
            raise ActionError(f"Failed to execute mouse click command: {e}")

    async def undo(self) -> None:
        """
        Undo the mouse click command.

        Note: Mouse click commands cannot be undone in a meaningful way.
        """
        self.logger.warning("Cannot undo mouse click command")


class MouseDragCommand(BaseCommand):
    """Command for dragging the mouse from one position to another."""

    async def execute(self) -> None:
        """
        Execute the mouse drag command.

        Returns:
            None

        Raises:
            ActionError: If execution fails
        """
        try:
            # Validate parameters
            self.validate_params(["start_x", "start_y", "end_x", "end_y"])

            # Get parameters
            start_x = self.params["start_x"]
            start_y = self.params["start_y"]
            end_x = self.params["end_x"]
            end_y = self.params["end_y"]
            button = self.params.get("button", "left")

            # Execute the action
            await self.executor.execute_action(
                "mouse_drag",
                {
                    "start_x": start_x,
                    "start_y": start_y,
                    "end_x": end_x,
                    "end_y": end_y,
                    "button": button,
                },
            )

            # Mark as executed
            self._set_executed()

        except Exception as e:
            self.logger.error(f"Error executing mouse drag command: {e}")
            raise ActionError(f"Failed to execute mouse drag command: {e}")

    async def undo(self) -> None:
        """
        Undo the mouse drag command.

        Note: Mouse drag commands cannot be undone in a meaningful way.
        """
        self.logger.warning("Cannot undo mouse drag command")
