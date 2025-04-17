# Location: ai_desktop_assistant/interfaces/output_provider.py
"""
Output Provider Protocol

This module defines the interface for output provider implementations.
"""

import abc


class OutputProvider(abc.ABC):
    """Interface for output provider implementations."""

    @abc.abstractmethod
    async def initialize(self) -> None:
        """Initialize the output provider."""
        pass

    @abc.abstractmethod
    async def shutdown(self) -> None:
        """Shut down the output provider."""
        pass


class TextOutputProvider(OutputProvider):
    """Interface for text output providers."""

    @abc.abstractmethod
    async def output_text(self, text: str) -> None:
        """
        Output text.

        Args:
            text: The text to output
        """
        pass


class AudioOutputProvider(OutputProvider):
    """Interface for audio output providers."""

    @abc.abstractmethod
    async def play_audio(self, audio_data: bytes) -> None:
        """
        Play audio data.

        Args:
            audio_data: Raw audio data bytes
        """
        pass

    @abc.abstractmethod
    async def speak_text(self, text: str) -> None:
        """
        Convert text to speech and play it.

        Args:
            text: The text to speak
        """
        pass

    @abc.abstractmethod
    async def stop_speaking(self) -> None:
        """Stop any ongoing speech output."""
        pass
