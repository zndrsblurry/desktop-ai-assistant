# Location: ai_desktop_assistant/interfaces/action_executor.py
"""
Action Executor Protocol

This module defines the interface for action executor implementations.
"""

import abc
from typing import Any, Dict, Optional


class ActionExecutor(abc.ABC):
    """Interface for action executor implementations."""

    @abc.abstractmethod
    async def initialize(self) -> None:
        """Initialize the action executor."""
        pass

    @abc.abstractmethod
    async def shutdown(self) -> None:
        """Shut down the action executor."""
        pass

    @abc.abstractmethod
    async def execute_action(
        self, action_type: str, params: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Execute an action.

        Args:
            action_type: The type of action to execute
            params: Action parameters

        Returns:
            The action result or None if the action doesn't produce a result
        """
        pass

    @abc.abstractmethod
    def can_execute(self, action_type: str) -> bool:
        """
        Check if this executor can execute the given action type.

        Args:
            action_type: The action type to check

        Returns:
            True if this executor can execute the action, False otherwise
        """
        pass


class Command(abc.ABC):
    """Interface for command objects."""

    @abc.abstractmethod
    async def execute(self) -> Optional[Any]:
        """
        Execute the command.

        Returns:
            The command result or None if the command doesn't produce a result
        """
        pass

    @abc.abstractmethod
    async def undo(self) -> None:
        """Undo the command if possible."""
        pass
