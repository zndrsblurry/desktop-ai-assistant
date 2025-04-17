# Location: ai_desktop_assistant/core/state.py
"""
Application State Management

This module contains the application state class and related functionality.
"""

import enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class AssistantStateEnum(enum.Enum):
    """Enumeration of assistant states."""

    IDLE = "idle"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    ACTING = "acting"
    ERROR = "error"


@dataclass
class Conversation:
    """Class representing the conversation history."""

    messages: List[Dict[str, Any]] = field(default_factory=list)

    def add_user_message(self, text: str) -> None:
        """
        Add a user message to the conversation.

        Args:
            text: The message text
        """
        self.messages.append({"role": "user", "parts": [{"text": text}]})

    def add_assistant_message(self, text: str) -> None:
        """
        Add an assistant message to the conversation.

        Args:
            text: The message text
        """
        self.messages.append({"role": "model", "parts": [{"text": text}]})

    def get_last_n_messages(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Get the last N messages from the conversation.

        Args:
            n: The number of messages to retrieve

        Returns:
            List of the last N messages
        """
        return self.messages[-n:] if n < len(self.messages) else self.messages.copy()

    def clear(self) -> None:
        """Clear the conversation history."""
        self.messages.clear()


@dataclass
class AppState:
    """Class representing the application state."""

    # Assistant state
    assistant_state: str = AssistantStateEnum.IDLE.value
    is_busy: bool = False

    # Input/output settings
    voice_enabled: bool = True

    # Current conversation
    conversation: Conversation = field(default_factory=Conversation)

    # Error state
    last_error: Optional[str] = None

    # Other state variables
    extra: Dict[str, Any] = field(default_factory=dict)

    def set_assistant_state(self, state: AssistantStateEnum) -> None:
        """
        Set the assistant state.

        Args:
            state: The new assistant state
        """
        self.assistant_state = state.value
        self.is_busy = state not in (AssistantStateEnum.IDLE, AssistantStateEnum.ERROR)

    def get_state_value(self, key: str) -> Optional[Any]:
        """
        Get a state value by key.

        Args:
            key: The state key

        Returns:
            The state value or None if not found
        """
        if hasattr(self, key):
            return getattr(self, key)
        return self.extra.get(key)

    def set_state_value(self, key: str, value: Any) -> None:
        """
        Set a state value.

        Args:
            key: The state key
            value: The state value
        """
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            self.extra[key] = value
