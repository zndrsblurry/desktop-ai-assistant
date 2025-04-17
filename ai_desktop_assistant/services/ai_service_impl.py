# Location: ai_desktop_assistant/services/ai_service_impl.py
"""
AI Service Implementation

This module implements the AI service interface using the Gemini client.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types as genai_types

from ai_desktop_assistant.ai.gemini_client import GeminiClient
from ai_desktop_assistant.ai.prompt_templates import create_system_prompt
from ai_desktop_assistant.core.events import EventBus, EventType
from ai_desktop_assistant.core.exceptions import APIError
from ai_desktop_assistant.interfaces.ai_service import AIService
from websockets.exceptions import ConnectionClosed


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

        try:
            # Import the speech recognition library here
            try:
                import speech_recognition as sr
            except ImportError:
                self.logger.warning(
                    "speech_recognition library not installed; using placeholder transcription."
                )
                transcription = "Hello, how can you help me?"
            else:
                # Use the speech recognition library to transcribe the audio
                recognizer = sr.Recognizer()
                sample_width = 2  # Assuming 16-bit audio
                rate = 16000  # Assuming 16kHz sample rate
                audio_data_obj = sr.AudioData(audio_data, rate, sample_width)
                try:
                    transcription = await asyncio.to_thread(
                        recognizer.recognize_google, audio_data_obj
                    )
                except sr.UnknownValueError:
                    self.logger.warning("Could not understand audio, using default response")
                    transcription = ""  # Empty transcription will be handled by the AI
                except Exception as e:
                    self.logger.error(f"Error transcribing audio: {e}")
                    transcription = ""  # Empty transcription will be handled by the AI

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
            # Use a shared Gemini client audio instance (v1alpha) for TTS streaming
            audio_client = self.gemini_client.get_tts_client()
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
            # Publish event with audio bytes for UI playback/storage
            try:
                # SPEECH_END indicates TTS audio for the AI response is ready
                self.event_bus.publish(EventType.SPEECH_END, audio_bytes)
            except Exception:
                # Swallow any errors during event publishing
                pass
            return audio_bytes

        except Exception as e:
            self.logger.error(f"Error converting text to speech: {e}")
            raise APIError(f"Failed to convert text to speech: {e}")
    
    async def live_audio_conversation(self, mic_input, speaker_output) -> None:
        """
        Stream live bidirectional audio with the AI: capture mic, send to live session,
        and play back AI audio responses, publishing text when available.
        """
        try:
            # Ensure live audio session is started
            await self.start_live_session_audio()
            # Prepare microphone stream
            if not getattr(mic_input, 'pyaudio', None):
                raise APIError("PyAudio not initialized for live streaming")
            pya = mic_input.pyaudio
            mic_info = pya.get_default_input_device_info()
            stream = await asyncio.to_thread(
                pya.open,
                format=mic_input.FORMAT,
                channels=mic_input.CHANNELS,
                rate=mic_input.RATE,
                input=True,
                input_device_index=mic_info['index'],
                frames_per_buffer=mic_input.CHUNK,
            )
            # Use overflow handling in debug mode
            if __debug__:
                kwargs = {'exception_on_overflow': False}
            else:
                kwargs = {}

            async def _send_audio():
                while True:
                    data = await asyncio.to_thread(stream.read, mic_input.CHUNK, **kwargs)
                    # Send raw audio PCM to live session
                    await self.gemini_client.live_session.send(
                        input={'data': data, 'mime_type': 'audio/pcm'}
                    )

            async def _receive_audio():
                # Receive responses continuously
                while True:
                    turn = self.gemini_client.live_session.receive()
                    async for response in turn:
                        # Play audio data if present
                        if getattr(response, 'data', None):
                            try:
                                await speaker_output.play_audio(response.data)
                            except Exception as exc:
                                self.logger.error(f"Error playing live AI audio: {exc}")
                        # (no TTS-retrigger here — we already played the model’s audio)

            # Run send and receive concurrently
            await asyncio.gather(_send_audio(), _receive_audio())
        except ConnectionClosed:
            # Normal closure of WebSocket session
            self.logger.info("Live audio conversation ended normally")
            return
        except Exception as e:
            self.logger.error(f"Error in live audio conversation: {e}")
            self.event_bus.publish(EventType.AI_ERROR, str(e))
            raise
