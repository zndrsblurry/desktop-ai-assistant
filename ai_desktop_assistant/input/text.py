# Location: ai_desktop_assistant/input/text.py
"""
Text Input Provider

This module implements the text input provider interface.
"""

import logging
from typing import Any

from ai_desktop_assistant.core.events import EventBus, EventType
from ai_desktop_assistant.core.exceptions import InputError
from ai_desktop_assistant.interfaces.input_provider import TextInputProvider


class TextInputProvider(TextInputProvider):
    """Implementation of the text input provider."""

    def __init__(self, event_bus: EventBus):
        """
        Initialize the text input provider.

        Args:
            event_bus: The application event bus
        """
        self.logger = logging.getLogger(__name__)
        self.event_bus = event_bus

    async def initialize(self) -> None:
        """Initialize the text input provider."""
        self.logger.info("Initializing text input provider")
        self.logger.info("Text input provider initialized")

    async def shutdown(self) -> None:
        """Shut down the text input provider."""
        self.logger.info("Shutting down text input provider")
        self.logger.info("Text input provider shut down")

    async def process_text(self, text: str) -> Any:
        """
        Process text input.

        Args:
            text: The text input to process

        Returns:
            The processing result

        Raises:
            InputError: If processing fails
        """
        try:
            # Clean and validate the input
            text = text.strip()
            if not text:
                raise InputError("Input text is empty")

            # Publish the text input event
            self.logger.debug(f"Processing text input: {text}")
            self.event_bus.publish(EventType.TEXT_INPUT, text)

            return text

        except Exception as e:
            self.logger.error(f"Error processing text input: {e}")
            self.event_bus.publish(EventType.ERROR, "input", str(e))
            raise InputError(f"Failed to process text input: {e}")
