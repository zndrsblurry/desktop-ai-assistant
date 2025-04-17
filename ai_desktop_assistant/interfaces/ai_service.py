# Location: ai_desktop_assistant/interfaces/ai_service.py
"""
AI Service Protocol

This module defines the interface for AI service implementations.
"""

import abc
from typing import Any, Dict, List, Optional


class AIService(abc.ABC):
    """Interface for AI service implementations."""

    @abc.abstractmethod
    async def initialize(self) -> None:
        """Initialize the AI service."""
        pass

    @abc.abstractmethod
    async def shutdown(self) -> None:
        """Shut down the AI service."""
        pass

    @abc.abstractmethod
    async def process_text(
        self, text: str, conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Process text input and generate a response.

        Args:
            text: The input text to process
            conversation_history: Optional conversation history for context

        Returns:
            The generated response text
        """
        pass

    @abc.abstractmethod
    async def process_voice(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Process voice input and generate a response.

        Args:
            audio_data: Raw audio data bytes

        Returns:
            Dict containing the transcription and response
        """
        pass

    @abc.abstractmethod
    async def get_speech(self, text: str) -> bytes:
        """
        Convert text to speech.

        Args:
            text: The text to convert to speech

        Returns:
            Raw audio data bytes
        """
        pass
