# Location: ai_desktop_assistant/core/events.py
"""
Event Bus System

This module implements a simple event bus for publish-subscribe communication
between application components.
"""

import asyncio
import enum
import logging
from collections import defaultdict
from typing import Any, Callable, Dict, List


class EventType(enum.Enum):
    """Enumeration of event types used in the application."""

    # System events
    INITIALIZED = "initialized"
    SHUTDOWN = "shutdown"
    ERROR = "error"

    # State events
    STATE_CHANGED = "state_changed"

    # Input events
    TEXT_INPUT = "text_input"
    VOICE_INPUT_START = "voice_input_start"
    VOICE_INPUT_STOP = "voice_input_stop"
    VOICE_DATA = "voice_data"
    VOICE_TRANSCRIPT = "voice_transcript"

    # AI events
    AI_THINKING = "ai_thinking"
    AI_RESPONSE = "ai_response"
    AI_ERROR = "ai_error"

    # Output events
    OUTPUT_START = "output_start"
    OUTPUT_END = "output_end"
    SPEECH_START = "speech_start"
    SPEECH_END = "speech_end"

    # Action events
    ACTION_START = "action_start"
    ACTION_COMPLETE = "action_complete"
    ACTION_FAILED = "action_failed"


# Type alias for event handlers
EventHandler = Callable[[Any], None]


class EventBus:
    """
    Event bus for publish-subscribe communication between components.

    Components can publish events and subscribe to event types.
    """

    def __init__(self):
        """Initialize the event bus."""
        self.logger = logging.getLogger(__name__)
        self._subscribers: Dict[EventType, List[EventHandler]] = defaultdict(list)
        self._loop = asyncio.get_event_loop()

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Subscribe a handler function to an event type.

        Args:
            event_type: The event type to subscribe to
            handler: The handler function to call when the event is published
        """
        self._subscribers[event_type].append(handler)
        self.logger.debug(f"Subscribed to {event_type.name}: {handler.__qualname__}")

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Unsubscribe a handler function from an event type.

        Args:
            event_type: The event type to unsubscribe from
            handler: The handler function to unsubscribe
        """
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)
            self.logger.debug(
                f"Unsubscribed from {event_type.name}: {handler.__qualname__}"
            )

    def unsubscribe_all(self) -> None:
        """Unsubscribe all handlers from all event types."""
        self._subscribers.clear()
        self.logger.debug("All subscribers cleared")

    def publish(self, event_type: EventType, *args, **kwargs) -> None:
        """
        Publish an event.

        Args:
            event_type: The type of event to publish
            *args: Positional arguments to pass to handler functions
            **kwargs: Keyword arguments to pass to handler functions
        """
        if event_type not in self._subscribers:
            # No subscribers for this event type
            return

        handlers = self._subscribers[event_type].copy()
        self.logger.debug(
            f"Publishing {event_type.name} to {len(handlers)} subscribers"
        )

        # Invoke handlers immediately for synchronous updates; schedule coroutines on the asyncio loop
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    # Schedule coroutine handler on the event loop
                    self._loop.create_task(handler(*args, **kwargs))
                else:
                    # Call synchronous handler directly
                    handler(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"Error in event handler {handler.__qualname__}: {e}")

    async def publish_async(self, event_type: EventType, *args, **kwargs) -> None:
        """
        Publish an event asynchronously.

        Args:
            event_type: The type of event to publish
            *args: Positional arguments to pass to handler functions
            **kwargs: Keyword arguments to pass to handler functions
        """
        if event_type not in self._subscribers:
            # No subscribers for this event type
            return

        handlers = self._subscribers[event_type].copy()
        self.logger.debug(
            f"Publishing async {event_type.name} to {len(handlers)} subscribers"
        )

        for handler in handlers:
            try:
                # For async handlers, await them; for sync handlers, run directly
                if asyncio.iscoroutinefunction(handler):
                    await handler(*args, **kwargs)
                else:
                    handler(*args, **kwargs)
            except Exception as e:
                self.logger.error(
                    f"Error in async event handler {handler.__qualname__}: {e}"
                )
