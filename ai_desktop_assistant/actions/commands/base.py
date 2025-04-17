# Location: ai_desktop_assistant/actions/commands/base.py
"""
Base Command

This module defines the base command class for the command pattern.
"""

import abc
import logging
from typing import Any, Dict, Optional

from ai_desktop_assistant.core.exceptions import ActionError
from ai_desktop_assistant.interfaces.action_executor import ActionExecutor, Command


class BaseCommand(Command):
    """
    Base class for command objects.

    This class implements the command pattern for executing actions.
    """

    def __init__(self, executor: ActionExecutor, params: Dict[str, Any]):
        """
        Initialize the command.

        Args:
            executor: The executor that will execute the command
            params: Command parameters
        """
        self.logger = logging.getLogger(__name__)
        self.executor = executor
        self.params = params
        self.executed = False
        self.result = None

    @abc.abstractmethod
    async def execute(self) -> Optional[Any]:
        """
        Execute the command.

        Returns:
            The command result or None if the command doesn't produce a result

        Raises:
            ActionError: If execution fails
        """
        pass

    @abc.abstractmethod
    async def undo(self) -> None:
        """
        Undo the command if possible.

        Raises:
            ActionError: If undo fails
        """
        pass

    def validate_params(self, required_params: list) -> None:
        """
        Validate that required parameters are present.

        Args:
            required_params: List of required parameter names

        Raises:
            ActionError: If a required parameter is missing
        """
        for param in required_params:
            if param not in self.params:
                raise ActionError(f"Missing required parameter: {param}")

    def _set_executed(self, result: Optional[Any] = None) -> None:
        """
        Mark the command as executed and store the result.

        Args:
            result: The command result
        """
        self.executed = True
        self.result = result
