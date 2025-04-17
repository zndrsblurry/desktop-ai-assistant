# Location: ai_desktop_assistant/actions/factory.py
"""
Action Factory

This module implements the action factory for creating and executing commands.
"""

import logging
from typing import Any, Dict, List, Optional, Type

from ai_desktop_assistant.actions.commands.base import BaseCommand
from ai_desktop_assistant.actions.executors.mouse_executor import MouseExecutor
from ai_desktop_assistant.actions.executors.keyboard_executor import KeyboardExecutor
from ai_desktop_assistant.actions.executors.system_executor import SystemExecutor
from ai_desktop_assistant.actions.executors.web_executor import WebExecutor
from ai_desktop_assistant.core.di import DependencyContainer
from ai_desktop_assistant.core.events import EventBus, EventType
from ai_desktop_assistant.core.exceptions import ActionError
from ai_desktop_assistant.interfaces.action_executor import ActionExecutor


class ActionFactory:
    """
    Factory for creating and executing action commands.

    This class manages the available action executors and creates
    the appropriate command objects for executing actions.
    """

    def __init__(self, container: DependencyContainer, event_bus: EventBus):
        """
        Initialize the action factory.

        Args:
            container: The dependency injection container
            event_bus: The application event bus
        """
        self.logger = logging.getLogger(__name__)
        self.container = container
        self.event_bus = event_bus
        self.executors: List[ActionExecutor] = []

        # Initialize executors
        self._init_executors()

    def _init_executors(self) -> None:
        """Initialize the available action executors."""
        self.logger.info("Initializing action executors")

        # Create executors
        self.executors = [
            MouseExecutor(self.event_bus),
            KeyboardExecutor(self.event_bus),
            SystemExecutor(self.event_bus),
            WebExecutor(self.event_bus),
        ]

        # Register executors with the container
        for executor in self.executors:
            self.container.register_instance(executor)
            self.logger.debug(f"Registered executor: {type(executor).__name__}")

    async def create_command(
        self, action_type: str, params: Dict[str, Any]
    ) -> Optional[BaseCommand]:
        """
        Create a command for the given action type.

        Args:
            action_type: The type of action to create
            params: Action parameters

        Returns:
            The created command object or None if no executor can handle the action

        Raises:
            ActionError: If command creation fails
        """
        try:
            # Find an executor that can handle this action
            executor = self._find_executor(action_type)
            if not executor:
                self.logger.warning(f"No executor found for action: {action_type}")
                return None

            # Create the command
            command_class = self._get_command_class(action_type, executor)
            if not command_class:
                self.logger.warning(f"No command class found for action: {action_type}")
                return None

            # Instantiate the command
            command = command_class(executor, params)
            self.logger.debug(f"Created command: {command.__class__.__name__}")

            return command

        except Exception as e:
            self.logger.error(f"Error creating command for action {action_type}: {e}")
            raise ActionError(f"Failed to create command for action {action_type}: {e}")

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

        Raises:
            ActionError: If execution fails
        """
        try:
            self.logger.info(f"Executing action: {action_type}")
            self.event_bus.publish(EventType.ACTION_START, action_type, params)

            # Find an executor that can handle this action
            executor = self._find_executor(action_type)
            if not executor:
                error_msg = f"No executor found for action: {action_type}"
                self.logger.warning(error_msg)
                self.event_bus.publish(EventType.ACTION_FAILED, action_type, error_msg)
                raise ActionError(error_msg)

            # Execute the action
            result = await executor.execute_action(action_type, params)

            self.event_bus.publish(EventType.ACTION_COMPLETE, action_type, result)
            return result

        except Exception as e:
            self.logger.error(f"Error executing action {action_type}: {e}")
            self.event_bus.publish(EventType.ACTION_FAILED, action_type, str(e))
            raise ActionError(f"Failed to execute action {action_type}: {e}")

    def _find_executor(self, action_type: str) -> Optional[ActionExecutor]:
        """
        Find an executor that can handle the given action type.

        Args:
            action_type: The action type to find an executor for

        Returns:
            The executor or None if no executor can handle the action
        """
        for executor in self.executors:
            if executor.can_execute(action_type):
                return executor
        return None

    def _get_command_class(
        self, action_type: str, executor: ActionExecutor
    ) -> Optional[Type[BaseCommand]]:
        """
        Get the command class for the given action type.

        Args:
            action_type: The action type to get a command class for
            executor: The executor that will execute the command

        Returns:
            The command class or None if no command class is found
        """
        # This would be implemented by looking up the command class
        # in a registry or by asking the executor for the command class
        # For now, we'll just return None as a placeholder
        return None
