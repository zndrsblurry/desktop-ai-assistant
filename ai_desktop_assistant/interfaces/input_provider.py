# Location: ai_desktop_assistant/interfaces/input_provider.py
"""
Input Provider Protocol

This module defines the interface for input provider implementations.
"""

import abc
from typing import Any, Optional


class InputProvider(abc.ABC):
    """Interface for input provider implementations."""

    @abc.abstractmethod
    async def initialize(self) -> None:
        """Initialize the input provider."""
        pass

    @abc.abstractmethod
    async def shutdown(self) -> None:
        """Shut down the input provider."""
        pass


class TextInputProvider(InputProvider):
    """Interface for text input providers."""

    @abc.abstractmethod
    async def process_text(self, text: str) -> Any:
        """
        Process text input.

        Args:
            text: The text input to process

        Returns:
            The processing result
        """
        pass


class VoiceInputProvider(InputProvider):
    """Interface for voice input providers."""

    @abc.abstractmethod
    async def start_listening(self) -> None:
        """Start listening for voice input."""
        pass

    @abc.abstractmethod
    async def stop_listening(self) -> None:
        """Stop listening for voice input."""
        pass

    @abc.abstractmethod
    async def get_transcript(self, audio_data: bytes) -> Optional[str]:
        """
        Get transcript from audio data.

        Args:
            audio_data: Raw audio data bytes

        Returns:
            The transcribed text or None if transcription failed
        """
        pass
