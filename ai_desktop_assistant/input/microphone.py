# Location: ai_desktop_assistant/input/microphone.py
"""
Microphone Input Provider

This module implements the microphone input provider interface for voice input.
"""

import asyncio
import logging
import numpy as np
import queue
import threading
from typing import Optional

try:
    import pyaudio

    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

from ai_desktop_assistant.core.events import EventBus, EventType
from ai_desktop_assistant.core.exceptions import InputError
from ai_desktop_assistant.interfaces.input_provider import VoiceInputProvider


class MicrophoneInputProvider(VoiceInputProvider):
    """Implementation of the microphone input provider for voice input."""

    # Audio stream parameters
    CHUNK = 1024
    FORMAT = pyaudio.paInt16 if PYAUDIO_AVAILABLE else 8
    CHANNELS = 1
    RATE = 16000  # 16kHz for speech recognition

    def __init__(self, event_bus: EventBus):
        """
        Initialize the microphone input provider.

        Args:
            event_bus: The application event bus
        """
        self.logger = logging.getLogger(__name__)
        self.event_bus = event_bus

        # Audio processing state
        self.pyaudio = None
        self.stream = None
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.recording_thread = None
        self.processing_task = None

    async def initialize(self) -> None:
        """
        Initialize the microphone input provider.

        Raises:
            InputError: If initialization fails
        """
        if not PYAUDIO_AVAILABLE:
            self.logger.warning(
                "PyAudio not available. Voice input will not be available."
            )
            return

        self.logger.info("Initializing microphone input provider")

        try:
            # Initialize PyAudio
            self.pyaudio = pyaudio.PyAudio()
            self.logger.info("Microphone input provider initialized")

        except Exception as e:
            self.logger.error(f"Error initializing microphone: {e}")
            raise InputError(f"Failed to initialize microphone: {e}")

    async def shutdown(self) -> None:
        """Shut down the microphone input provider."""
        if not PYAUDIO_AVAILABLE:
            return

        self.logger.info("Shutting down microphone input provider")

        # Stop listening if active
        if self.is_listening:
            await self.stop_listening()

        # Terminate PyAudio
        if self.pyaudio:
            self.pyaudio.terminate()
            self.pyaudio = None

        self.logger.info("Microphone input provider shut down")

    async def start_listening(self) -> None:
        """
        Start listening for voice input.

        Raises:
            InputError: If starting listening fails
        """
        if not PYAUDIO_AVAILABLE:
            raise InputError("PyAudio not available. Voice input is not supported.")

        if self.is_listening:
            self.logger.info("Already listening")
            return

        try:
            self.logger.info("Starting to listen")
            self.event_bus.publish(EventType.VOICE_INPUT_START)

            # Create audio stream
            self.stream = self.pyaudio.open(
                format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK,
            )

            # Clear the audio queue
            while not self.audio_queue.empty():
                self.audio_queue.get()

            # Start recording thread
            self.is_listening = True
            self.recording_thread = threading.Thread(target=self._record_audio)
            self.recording_thread.start()

            # Start processing task
            self.processing_task = asyncio.create_task(self._process_audio())

        except Exception as e:
            self.logger.error(f"Error starting listening: {e}")
            self.event_bus.publish(EventType.ERROR, "input", str(e))
            raise InputError(f"Failed to start listening: {e}")

    async def stop_listening(self) -> None:
        """
        Stop listening for voice input.

        Raises:
            InputError: If stopping listening fails
        """
        if not PYAUDIO_AVAILABLE or not self.is_listening:
            return

        try:
            self.logger.info("Stopping listening")
            self.event_bus.publish(EventType.VOICE_INPUT_STOP)

            # Stop recording
            self.is_listening = False

            # Wait for recording thread to finish
            if self.recording_thread and self.recording_thread.is_alive():
                self.recording_thread.join(timeout=1.0)

            # Close stream
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None

            # Cancel processing task
            if self.processing_task:
                self.processing_task.cancel()
                try:
                    await self.processing_task
                except asyncio.CancelledError:
                    pass
                self.processing_task = None

        except Exception as e:
            self.logger.error(f"Error stopping listening: {e}")
            self.event_bus.publish(EventType.ERROR, "input", str(e))
            raise InputError(f"Failed to stop listening: {e}")

    async def get_transcript(self, audio_data: bytes) -> Optional[str]:
        """
        Get transcript from audio data.

        Args:
            audio_data: Raw audio data bytes

        Returns:
            The transcribed text or None if transcription failed

        Raises:
            InputError: If transcription fails
        """
        # Transcribe audio data using SpeechRecognition
        try:
            import speech_recognition as sr
        except ImportError:
            self.logger.warning(
                "speech_recognition library not installed; voice input disabled."
            )
            return None

        recognizer = sr.Recognizer()
        sample_width = (
            self.pyaudio.get_sample_size(self.FORMAT) if self.pyaudio else 2
        )
        audio_data_obj = sr.AudioData(audio_data, self.RATE, sample_width)
        try:
            transcript = await asyncio.to_thread(
                recognizer.recognize_google, audio_data_obj
            )
            return transcript
        except sr.UnknownValueError:
            return None
        except Exception as e:
            self.logger.error(f"Error transcribing audio: {e}")
            raise InputError(f"Failed to transcribe audio: {e}")

    def _record_audio(self) -> None:
        """
        Record audio from the microphone and add it to the queue.

        This method runs in a separate thread.
        """
        try:
            while self.is_listening and self.stream:
                # Read audio chunk
                data = self.stream.read(self.CHUNK, exception_on_overflow=False)
                self.audio_queue.put(data)
        except Exception as e:
            self.logger.error(f"Error recording audio: {e}")
            self.is_listening = False

    async def _process_audio(self) -> None:
        """
        Process audio chunks from the queue.

        This method detects voice activity and sends audio data to the event bus.
        """
        frames = []
        silence_threshold = 500  # Adjust this value based on your microphone
        silence_count = 0
        max_silence_count = 30  # About 1 second of silence at CHUNK=1024, RATE=16000

        try:
            while self.is_listening:
                # Get audio chunk from queue
                try:
                    data = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue

                frames.append(data)

                # Convert to numpy array for analysis
                audio_array = np.frombuffer(data, dtype=np.int16)
                volume = np.abs(audio_array).mean()

                # Publish audio data for visualization
                self.event_bus.publish(EventType.VOICE_DATA, volume)

                # Check for silence
                if volume < silence_threshold:
                    silence_count += 1
                    if silence_count >= max_silence_count and len(frames) > 5:
                        # Enough silence after speech, process the audio
                        audio_data = b"".join(frames)
                        await self._handle_audio_data(audio_data)
                        frames = []
                        silence_count = 0
                else:
                    silence_count = 0

            # Process any remaining audio
            if frames:
                audio_data = b"".join(frames)
                await self._handle_audio_data(audio_data)

        except asyncio.CancelledError:
            # Task was cancelled, clean up
            if frames:
                audio_data = b"".join(frames)
                await self._handle_audio_data(audio_data)
            raise
        except Exception as e:
            self.logger.error(f"Error processing audio: {e}")

    async def _handle_audio_data(self, audio_data: bytes) -> None:
        """
        Handle processed audio data.

        Args:
            audio_data: Raw audio data bytes
        """
        try:
            # Get transcript
            transcript = await self.get_transcript(audio_data)
            if transcript:
                self.logger.info(f"Transcribed: {transcript}")
                self.event_bus.publish(EventType.VOICE_TRANSCRIPT, transcript)
                self.event_bus.publish(EventType.TEXT_INPUT, transcript)
        except Exception as e:
            self.logger.error(f"Error handling audio data: {e}")
