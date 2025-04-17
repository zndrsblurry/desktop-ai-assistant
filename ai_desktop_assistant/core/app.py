"""
Application Controller

This module contains the main application controller class that coordinates
all the assistant's components and services.
"""

import asyncio
import logging

from PySide6.QtCore import QObject, Slot, Signal, Property
from PySide6.QtQml import QQmlContext

from ai_desktop_assistant.ai.gemini_client import GeminiClient
from ai_desktop_assistant.core.config import AppConfig
from ai_desktop_assistant.core.di import DependencyContainer
from ai_desktop_assistant.core.events import EventBus, EventType
from ai_desktop_assistant.core.state import AppState
from ai_desktop_assistant.input.microphone import MicrophoneInputProvider
from ai_desktop_assistant.input.text import TextInputProvider
from ai_desktop_assistant.output.speaker import SpeakerOutputProvider
from ai_desktop_assistant.services.ai_service_impl import AIServiceImpl
from ai_desktop_assistant.actions.factory import ActionFactory


class ApplicationController(QObject):
    """
    Main application controller that coordinates all components and services.

    This class is responsible for initializing and managing all services,
    handling global events, and coordinating between the UI and backend services.
    """

    # QML property change signals
    stateChanged = Signal(str)
    isBusyChanged = Signal(bool)
    voiceEnabledChanged = Signal(bool)

    def __init__(self, container: DependencyContainer, event_bus: EventBus):
        """
        Initialize the application controller.

        Args:
            container: The dependency injection container
            event_bus: The application's event bus
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._container = container
        self._event_bus = event_bus
        self._state = AppState()
        self._is_initialized = False
        self._main_window = None  # For PyQt5 UI reference

        # Register event handlers
        self._event_bus.subscribe(EventType.STATE_CHANGED, self._on_state_changed)
        self._event_bus.subscribe(EventType.ERROR, self._on_error)

        # Store services for easy access
        self._ai_service = None
        self._mic_input = None
        self._text_input = None
        self._speaker_output = None

        # Capture the asyncio event loop for scheduling coroutines from the UI thread
        # This loop is started in a background thread via run_forever in main
        self._loop = asyncio.get_event_loop()

    async def initialize(self):
        """Initialize all services and components."""
        if self._is_initialized:
            return

        self.logger.info("Initializing application controller")
        config = self._container.resolve(AppConfig)

        # Register application state
        self._container.register_instance(self._state)

        # Initialize AI service with Gemini client
        gemini_client = GeminiClient(config)
        self._container.register_instance(gemini_client)

        self._ai_service = AIServiceImpl(gemini_client, self._event_bus)
        self._container.register_instance(self._ai_service)

        # Initialize input providers
        self._mic_input = MicrophoneInputProvider(self._event_bus)
        self._container.register_instance(self._mic_input)

        self._text_input = TextInputProvider(self._event_bus)
        self._container.register_instance(self._text_input)

        # Initialize output providers
        self._speaker_output = SpeakerOutputProvider(config)
        self._container.register_instance(self._speaker_output)

        # Initialize action system
        action_factory = ActionFactory(self._container, self._event_bus)
        self._container.register_instance(action_factory)

        # Initialize all components that need async initialization
        # Initialize microphone and AI service
        await self._mic_input.initialize()
        await self._ai_service.initialize()
        # Initialize speaker output provider for TTS feedback
        await self._speaker_output.initialize()
        # Wire text input events to AI service processing
        from ai_desktop_assistant.core.events import EventType
        self._event_bus.subscribe(EventType.TEXT_INPUT, self._ai_service.process_text)
        # Subscribe to AI responses to speak them via speaker output
        self._event_bus.subscribe(EventType.AI_RESPONSE, self._on_ai_response)

        # Mark as initialized
        self._is_initialized = True
        self.logger.info("Application controller initialized")

    async def shutdown(self):
        """Clean up resources and shut down all services."""
        self.logger.info("Shutting down application controller")

        # Shut down services in reverse order
        await self._ai_service.shutdown()
        await self._mic_input.shutdown()
        await self._speaker_output.shutdown()

        self._event_bus.unsubscribe_all()
        self.logger.info("Application controller shutdown complete")

    def register_qml_context(self, context: QQmlContext):
        """
        Register this controller and other objects with the QML context.

        Args:
            context: The QML root context to register with
        """
        context.setContextProperty("appController", self)
        context.setContextProperty("appState", self._state)

    def register_ui(self, main_window):
        """
        Register the PyQt5 main window with the controller.

        Args:
            main_window: The PyQt5 main window instance
        """
        self._main_window = main_window
        self.logger.info("Main window registered with application controller")
    
    async def _init_session_and_greet(self, greeting: str) -> None:
        """
        Ensure a live audio session is active and send the greeting.
        """
        try:
            # Send the greeting prompt as AI text and handle the response
            response = await self._ai_service.process_text(greeting)
            self.logger.info(f"AI greeting response: {response}")
            # Trigger the AI response event to ensure it's processed
            self._event_bus.publish(EventType.AI_RESPONSE, response)
        except Exception as e:
            self.logger.error(f"Error sending greeting: {e}")

    def start_assistant(self):
        """Start the assistant."""
        # Ensure initialization
        if not self._is_initialized:
            self.logger.error("Cannot start assistant: Not initialized")
            self._event_bus.publish(EventType.ERROR, "init", "Assistant not initialized")
            return

        # Transition to starting state
        self._state.assistant_state = "starting"
        self._event_bus.publish(EventType.STATE_CHANGED, "assistant_state", "starting")
        self.logger.info("Starting assistant")
        # Start listening for microphone activity to update UI volume indicator
        asyncio.run_coroutine_threadsafe(
            self._mic_input.start_listening(), self._loop
        )

        # Start live audio conversation: stream mic directly to AI and play responses
        asyncio.run_coroutine_threadsafe(
            self._ai_service.live_audio_conversation(self._mic_input, self._speaker_output),
            self._loop
        )

        # Transition to listening state
        self._state.assistant_state = "listening"
        self._event_bus.publish(EventType.STATE_CHANGED, "assistant_state", "listening")

        # Prompt the AI to greet the user via the live session (ensure session initialized)
        greeting_prompt = "Hi boss, how can I help you today?"
        try:
            # Synchronously send greeting before proceeding
            future = asyncio.run_coroutine_threadsafe(
                self._init_session_and_greet(greeting_prompt), self._loop
            )
            # Wait for greeting to complete (with timeout)
            future.result(timeout=5)
            self.logger.info(f"Greeting sent: {greeting_prompt}")
        except Exception as e:
            self.logger.error(f"Error sending greeting: {e}")

    def stop_assistant(self):
        """Stop the assistant."""
        # Transition to stopping state
        self._state.assistant_state = "stopping"
        self._event_bus.publish(EventType.STATE_CHANGED, "assistant_state", "stopping")
        self.logger.info("Stopping assistant")

        # Stop voice recognition: schedule stop on the background asyncio loop
        asyncio.run_coroutine_threadsafe(
            self._mic_input.stop_listening(), self._loop
        )

        # Transition to idle state
        self._state.assistant_state = "idle"
        self._event_bus.publish(EventType.STATE_CHANGED, "assistant_state", "idle")
        # Ensure live session and related resources are cleaned up
        asyncio.run_coroutine_threadsafe(
            self._ai_service.shutdown(), self._loop
        )

    def pause_assistant(self):
        """Pause the assistant."""
        if self._state.assistant_state != "idle":
            self._state.assistant_state = "paused"
            self._event_bus.publish(
                EventType.STATE_CHANGED, "assistant_state", "paused"
            )
            self.logger.info("Assistant paused")

    def resume_assistant(self):
        """Resume the assistant after pausing."""
        if self._state.assistant_state == "paused":
            self._state.assistant_state = "listening"
            self._event_bus.publish(
                EventType.STATE_CHANGED, "assistant_state", "listening"
            )
            self.logger.info("Assistant resumed")

    def emergency_stop(self):
        """Emergency stop all assistant activities."""
        self.logger.warning("Emergency stop triggered")
        # Here you would stop all activities immediately
        self._state.assistant_state = "idle"
        self._event_bus.publish(EventType.STATE_CHANGED, "assistant_state", "idle")
        self.logger.info("Assistant emergency stopped")

    # Event handlers
    def _on_state_changed(self, state_name: str, state_value: any):
        """Handle state change events."""
        self.logger.debug(f"State changed: {state_name} = {state_value}")
        if state_name == "assistant_state":
            self.stateChanged.emit(state_value)
        elif state_name == "is_busy":
            self.isBusyChanged.emit(state_value)
        elif state_name == "voice_enabled":
            self.voiceEnabledChanged.emit(state_value)

        # Forward state changes to main window if using PyQt5
        if self._main_window and hasattr(self._main_window, "on_state_changed"):
            self._main_window.on_state_changed(state_name, state_value)

    def _on_error(self, error_type: str, error_message: str):
        """Handle error events."""
        self.logger.error(f"Error ({error_type}): {error_message}")

        # Forward errors to main window if using PyQt5
        if self._main_window and hasattr(self._main_window, "on_error"):
            self._main_window.on_error(error_type, error_message)
        
    def _on_ai_response(self, response: str) -> None:
        """Handle AI_RESPONSE events by speaking the response via speaker output."""
        # Speak AI response via TTS and audio playback on the asyncio loop
        try:
            async def _speak():
                try:
                    # Convert text to speech (get raw audio bytes)
                    audio_bytes = await self._ai_service.get_speech(response)
                    # Play the audio data
                    await self._speaker_output.play_audio(audio_bytes)
                except Exception as exc:
                    self.logger.error(f"Error playing AI response: {exc}")
            # Schedule coroutine on background event loop
            asyncio.run_coroutine_threadsafe(_speak(), self._loop)
        except Exception as e:
            self.logger.error(f"Failed to schedule AI response speaking: {e}")

    # QML exposed methods
    @Slot(str)
    def sendTextInput(self, text: str):
        """
        Send text input to the assistant.

        Args:
            text: The text to process
        """
        # Schedule text processing coroutine on the background asyncio loop
        asyncio.run_coroutine_threadsafe(
            self._text_input.process_text(text), self._loop
        )

    @Slot()
    def startListening(self):
        """Start listening for voice input."""
        # Schedule microphone start coroutine on the background asyncio loop
        asyncio.run_coroutine_threadsafe(
            self._mic_input.start_listening(), self._loop
        )

    @Slot()
    def stopListening(self):
        """Stop listening for voice input."""
        # Schedule microphone stop coroutine on the background asyncio loop
        asyncio.run_coroutine_threadsafe(
            self._mic_input.stop_listening(), self._loop
        )

    @Slot(bool)
    def setVoiceEnabled(self, enabled: bool):
        """
        Enable or disable voice input/output.

        Args:
            enabled: Whether voice mode is enabled
        """
        self._state.voice_enabled = enabled
        self._event_bus.publish(EventType.STATE_CHANGED, "voice_enabled", enabled)

    # QML properties
    @Property(str, notify=stateChanged)
    def state(self):
        """Get the current assistant state."""
        return self._state.assistant_state

    @Property(bool, notify=isBusyChanged)
    def isBusy(self):
        """Get whether the assistant is busy."""
        return self._state.is_busy

    @Property(bool, notify=voiceEnabledChanged)
    def voiceEnabled(self):
        """Get whether voice mode is enabled."""
        return self._state.voice_enabled
