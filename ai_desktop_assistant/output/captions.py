# Location: ai_desktop_assistant/output/captions.py
"""
Captions Output Provider

This module implements the captions output provider for displaying spoken text.
"""

import logging

from ai_desktop_assistant.core.events import EventBus, EventType
from ai_desktop_assistant.core.exceptions import OutputError
from ai_desktop_assistant.interfaces.output_provider import TextOutputProvider


class CaptionsOutputProvider(TextOutputProvider):
    """Implementation of the captions output provider."""

    def __init__(self, event_bus: EventBus):
        """
        Initialize the captions output provider.

        Args:
            event_bus: The application event bus
        """
        self.logger = logging.getLogger(__name__)
        self.event_bus = event_bus

    async def initialize(self) -> None:
        """Initialize the captions output provider."""
        self.logger.info("Initializing captions output provider")
        self.logger.info("Captions output provider initialized")

    async def shutdown(self) -> None:
        """Shut down the captions output provider."""
        self.logger.info("Shutting down captions output provider")
        self.logger.info("Captions output provider shut down")

    async def output_text(self, text: str) -> None:
        """
        Output text as captions.

        Args:
            text: The text to output

        Raises:
            OutputError: If outputting captions fails
        """
        try:
            self.logger.debug(f"Outputting caption: {text}")

            # Publish caption event
            self.event_bus.publish(EventType.OUTPUT_START, "caption", text)

            # In a real implementation, this would display captions in the UI
            # For now, just log the text

            self.event_bus.publish(EventType.OUTPUT_END, "caption")

        except Exception as e:
            self.logger.error(f"Error outputting caption: {e}")
            raise OutputError(f"Failed to output caption: {e}")
