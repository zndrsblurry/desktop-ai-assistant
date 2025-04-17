# Location: ai_desktop_assistant/output/speaker.py
"""
Speaker Output Provider

This module implements the speaker output provider interface for audio output.
"""

import asyncio
import logging
import tempfile
import threading

try:
    import pyaudio
    import wave

    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

from ai_desktop_assistant.core.config import AppConfig
from ai_desktop_assistant.core.exceptions import OutputError
from ai_desktop_assistant.interfaces.output_provider import AudioOutputProvider


class SpeakerOutputProvider(AudioOutputProvider):
    """Implementation of the speaker output provider for audio output."""

    # Audio playback parameters
    CHUNK = 1024
    FORMAT = pyaudio.paInt16 if PYAUDIO_AVAILABLE else 8
    CHANNELS = 1
    RATE = 24000  # 24kHz for TTS output matching Gemini's output format

    def __init__(self, config: AppConfig):
        """
        Initialize the speaker output provider.

        Args:
            config: The application configuration
        """
        self.logger = logging.getLogger(__name__)
        self.config = config

        # Audio playback state
        self.pyaudio = None
        self.stream = None
        self.is_speaking = False
        self.playback_thread = None
        self.stop_event = threading.Event()

    async def initialize(self) -> None:
        """
        Initialize the speaker output provider.

        Raises:
            OutputError: If initialization fails
        """
        if not PYAUDIO_AVAILABLE:
            self.logger.warning(
                "PyAudio not available. Audio output will not be available."
            )
            return

        self.logger.info("Initializing speaker output provider")

        try:
            # Initialize PyAudio
            self.pyaudio = pyaudio.PyAudio()
            self.logger.info("Speaker output provider initialized")

        except Exception as e:
            self.logger.error(f"Error initializing speaker: {e}")
            raise OutputError(f"Failed to initialize speaker: {e}")

    async def shutdown(self) -> None:
        """Shut down the speaker output provider."""
        if not PYAUDIO_AVAILABLE:
            return

        self.logger.info("Shutting down speaker output provider")

        # Stop any ongoing speech
        await self.stop_speaking()

        # Terminate PyAudio
        if self.pyaudio:
            self.pyaudio.terminate()
            self.pyaudio = None

        self.logger.info("Speaker output provider shut down")

    async def play_audio(self, audio_data: bytes) -> None:
        """
        Play audio data.

        Args:
            audio_data: Raw audio data bytes

        Raises:
            OutputError: If playing audio fails
        """
        if not PYAUDIO_AVAILABLE:
            raise OutputError("PyAudio not available. Audio output is not supported.")

        try:
            self.logger.debug(f"Playing audio: {len(audio_data)} bytes")

            # Stop any ongoing playback
            await self.stop_speaking()

            # Save audio data to a temporary file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                temp_filename = tmp_file.name

                # Create a WAV file with the audio data
                with wave.open(temp_filename, "wb") as wf:
                    wf.setnchannels(self.CHANNELS)
                    wf.setsampwidth(self.pyaudio.get_sample_size(self.FORMAT))
                    wf.setframerate(self.RATE)
                    wf.writeframes(audio_data)

            # Play the audio file
            self.is_speaking = True
            self.stop_event.clear()
            self.playback_thread = threading.Thread(
                target=self._play_audio_file, args=(temp_filename,)
            )
            self.playback_thread.start()

        except Exception as e:
            self.logger.error(f"Error playing audio: {e}")
            raise OutputError(f"Failed to play audio: {e}")

    async def speak_text(self, text: str) -> None:
        """
        Convert text to speech and play it.

        Args:
            text: The text to speak

        Raises:
            OutputError: If speaking fails
        """
        # This would be implemented using a text-to-speech service
        # For now, we'll just log the text

        self.logger.info(f"Speaking: {text}")

        # In a real implementation, this would convert text to audio
        # and then play it using play_audio()

        # Placeholder for TTS (simulate speaking with a delay)
        await asyncio.sleep(len(text) * 0.05)  # Rough estimate of speaking time

    async def stop_speaking(self) -> None:
        """
        Stop any ongoing speech output.

        Raises:
            OutputError: If stopping speech fails
        """
        if not self.is_speaking:
            return

        try:
            self.logger.debug("Stopping speech")

            # Signal the playback thread to stop
            self.stop_event.set()

            # Wait for the playback thread to finish
            if self.playback_thread and self.playback_thread.is_alive():
                self.playback_thread.join(timeout=1.0)

            # Close the stream
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None

            self.is_speaking = False

        except Exception as e:
            self.logger.error(f"Error stopping speech: {e}")
            raise OutputError(f"Failed to stop speech: {e}")

    def _play_audio_file(self, filename: str) -> None:
        """
        Play an audio file.

        Args:
            filename: The filename to play
        """
        try:
            with wave.open(filename, "rb") as wf:
                # Open stream
                self.stream = self.pyaudio.open(
                    format=self.pyaudio.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True,
                )

                # Read and play audio data
                data = wf.readframes(self.CHUNK)
                while data and not self.stop_event.is_set():
                    self.stream.write(data)
                    data = wf.readframes(self.CHUNK)

                # Close stream
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None

            self.is_speaking = False

        except Exception as e:
            self.logger.error(f"Error playing audio file: {e}")
            self.is_speaking = False
