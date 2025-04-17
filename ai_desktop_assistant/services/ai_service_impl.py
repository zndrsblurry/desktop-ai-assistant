# Location: ai_desktop_assistant/services/ai_service_impl.py
"""
AI Service Implementation

This module implements the AI service interface using the Gemini client.
"""

import logging
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types as genai_types

from ai_desktop_assistant.ai.gemini_client import GeminiClient
from ai_desktop_assistant.ai.prompt_templates import create_system_prompt
from ai_desktop_assistant.core.events import EventBus, EventType
from ai_desktop_assistant.core.exceptions import APIError
from ai_desktop_assistant.interfaces.ai_service import AIService
from ai_desktop_assistant.core.events import EventType


class AIServiceImpl(AIService):
    """Implementation of the AI service using the Gemini client."""

    def __init__(self, gemini_client: GeminiClient, event_bus: EventBus):
        """
        Initialize the AI service.

        Args:
            gemini_client: The Gemini client instance
            event_bus: The application event bus
        """
        self.logger = logging.getLogger(__name__)
        self.gemini_client = gemini_client
        self.event_bus = event_bus
        self.system_prompt = create_system_prompt()
        self.is_live_session_active = False

    async def initialize(self) -> None:
        """Initialize the AI service."""
        self.logger.info("Initializing AI service")
        await self.gemini_client.initialize()
        self.logger.info("AI service initialized")

    async def shutdown(self) -> None:
        """Shut down the AI service."""
        self.logger.info("Shutting down AI service")
        if self.is_live_session_active:
            await self.gemini_client.close_live_session()
            self.is_live_session_active = False
        self.logger.info("AI service shut down")

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

        Raises:
            APIError: If processing fails
        """
        try:
            self.event_bus.publish(EventType.AI_THINKING)

            # Use the live session if we're doing multiple back-and-forth
            if not self.is_live_session_active:
                await self.gemini_client.start_live_session(
                    system_instruction=self.system_prompt
                )
                self.is_live_session_active = True

            # Send the message and get the response
            response = await self.gemini_client.send_message_to_live_session(text)

            self.event_bus.publish(EventType.AI_RESPONSE, response)
            return response

        except Exception as e:
            self.logger.error(f"Error processing text: {e}")
            self.event_bus.publish(EventType.AI_ERROR, str(e))
            raise APIError(f"Failed to process text: {e}")

    async def start_live_session_audio(self) -> None:
        """
        Explicitly start a live session in AUDIO mode using the system prompt.
        """
        try:
            await self.gemini_client.start_live_session(
                response_modality="AUDIO",
                system_instruction=self.system_prompt,
            )
            self.is_live_session_active = True
        except Exception as e:
            self.logger.error(f"Error starting live audio session: {e}")
            self.event_bus.publish(EventType.AI_ERROR, str(e))
            raise APIError(f"Failed to start live audio session: {e}")

    async def process_voice(self, audio_data: bytes) -> Dict[str, Any]:
        """
        Process voice input and generate a response.

        Args:
            audio_data: Raw audio data bytes

        Returns:
            Dict containing the transcription and response

        Raises:
            APIError: If processing fails
        """
        # For now, we'll need to transcribe the audio data first
        # This would be handled by a separate speech-to-text service
        # For simplicity, we'll implement a placeholder

        try:
            # This would be replaced with actual transcription
            transcription = "Hello, how can you help me?"

            # Log the transcription
            self.logger.info(f"Transcribed: {transcription}")
            self.event_bus.publish(EventType.VOICE_TRANSCRIPT, transcription)

            # Process the text
            response = await self.process_text(transcription)

            return {"transcription": transcription, "response": response}

        except Exception as e:
            self.logger.error(f"Error processing voice: {e}")
            self.event_bus.publish(EventType.AI_ERROR, str(e))
            raise APIError(f"Failed to process voice: {e}")

    async def get_speech(self, text: str) -> bytes:
        """
        Convert text to speech.

        Args:
            text: The text to convert to speech

        Returns:
            Raw audio data bytes

        Raises:
            APIError: If conversion fails
        """
        # Implement text-to-speech using Gemini Live API audio streaming.
        try:
            # Use a separate Gemini client instance for audio (v1alpha) to support TTS streaming
            audio_client = genai.Client(
                api_key=self.gemini_client.api_key,
                http_options={"api_version": "v1alpha"},
            )
            # Configure for audio-only response
            config = {"response_modalities": ["AUDIO"]}
            # Add preferred voice if specified
            if voice := self.gemini_client.config.preferred_voice:
                config["speech_config"] = genai_types.SpeechConfig(
                    voice_config=genai_types.VoiceConfig(
                        prebuilt_voice_config=genai_types.PrebuiltVoiceConfig(
                            voice_name=voice
                        )
                    )
                )

            # Open a live session for TTS
            async with audio_client.aio.live.connect(
                model="gemini-2.0-flash-live-001", config=config
            ) as session:
                # Send the text as user input
                await session.send_client_content(
                    turns={"role": "user", "parts": [{"text": text}]},
                    turn_complete=True,
                )
                # Collect audio data chunks
                audio_bytes = b""
                async for response in session.receive():
                    if response.data:
                        audio_bytes += response.data
            return audio_bytes

        except Exception as e:
            self.logger.error(f"Error converting text to speech: {e}")
            raise APIError(f"Failed to convert text to speech: {e}")
