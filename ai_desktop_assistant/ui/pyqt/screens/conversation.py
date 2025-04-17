"""
Conversation screen for the PyQt5-based AI Desktop Assistant.

This screen provides a chat interface where the user can type prompts or use voice input.
"""
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextBrowser,
    QLineEdit,
    QPushButton,
)
from PyQt5.QtCore import Qt

from ai_desktop_assistant.core.di import DependencyContainer
from ai_desktop_assistant.core.events import EventBus, EventType
from ai_desktop_assistant.core.app import ApplicationController


class ConversationScreen(QWidget):
    """Conversation screen with text input, mic control, and message display."""

    def __init__(self, container: DependencyContainer, event_bus: EventBus):
        super().__init__()
        self.container = container
        self.event_bus = event_bus
        # Storage for AI audio bytes keyed by identifier
        self.audio_messages = {}
        # Get application controller to send inputs
        self.app_controller = container.resolve(ApplicationController)

        # Set up UI components
        self.setup_ui()
        # Subscribe to input and AI response events
        # Use TEXT_INPUT for user messages (includes voice transcripts)
        self.event_bus.subscribe(EventType.TEXT_INPUT, self.on_user_message)
        # Remove duplicate VOICE_TRANSCRIPT subscription to avoid processing messages twice
        # self.event_bus.subscribe(EventType.VOICE_TRANSCRIPT, self.on_user_message)
        self.event_bus.subscribe(EventType.AI_RESPONSE, self.on_ai_response)
        # Subscribe to speech end events to handle audio playback links
        self.event_bus.subscribe(EventType.SPEECH_END, self.on_speech_end)

    def setup_ui(self):
        """Set up the conversation UI."""
        layout = QVBoxLayout(self)
        # Display area for conversation
        # Use QTextBrowser to enable clickable audio links
        self.conversation_view = QTextBrowser()
        # Disable automatic link opening to handle clicks manually
        self.conversation_view.setOpenExternalLinks(False)
        self.conversation_view.setOpenLinks(False)
        # Connect link clicks to handler
        self.conversation_view.anchorClicked.connect(self.on_anchor_clicked)
        layout.addWidget(self.conversation_view)

        # Input area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type your message here...")
        self.send_button = QPushButton("Send")
        self.mic_button = QPushButton("🎤")
        self.mic_button.setCheckable(True)
        # Connect signals
        self.send_button.clicked.connect(self.on_send_clicked)
        self.input_field.returnPressed.connect(self.on_send_clicked)
        self.mic_button.toggled.connect(self.on_mic_toggled)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        input_layout.addWidget(self.mic_button)
        layout.addLayout(input_layout)

    def append_message(self, sender: str, message: str):
        """Append a message to the conversation view."""
        self.conversation_view.append(f"<b>{sender}:</b> {message}")

    def on_user_message(self, text: str):
        """Handler for user messages (text or voice)."""
        # Note: EventType.VOICE_TRANSCRIPT also routes here
        self.append_message("User", text)

    def on_ai_response(self, response: str):
        """Handler for AI responses."""
        self.append_message("AI", response)

    def on_send_clicked(self):
        """Send the text from the input field to the AI service."""
        text = self.input_field.text().strip()
        if not text:
            return
        self.input_field.clear()
        # Send text via application controller
        self.app_controller.sendTextInput(text)

    def on_mic_toggled(self, listening: bool):
        """Start or stop voice input."""
        if listening:
            self.app_controller.startListening()
            self.mic_button.setText("Stop Mic")
        else:
            self.app_controller.stopListening()
            self.mic_button.setText("🎤")
    
    def on_speech_end(self, audio_bytes: bytes):
        """
        Handler for AI TTS audio ready events; store audio and append playback link.
        """
        import uuid
        msg_id = uuid.uuid4().hex
        self.audio_messages[msg_id] = audio_bytes
        self.conversation_view.append(f'<i><a href="ai_audio://{msg_id}">▶️ Play Audio</a></i>')

    def on_anchor_clicked(self, qurl):
        """
        Handle clicks on audio playback links.
        """
        if qurl.scheme() != 'ai_audio':
            return
        msg_id = qurl.path().lstrip('/')
        audio_bytes = self.audio_messages.get(msg_id)
        if not audio_bytes:
            return
        from ai_desktop_assistant.output.speaker import SpeakerOutputProvider
        from ai_desktop_assistant.core.app import ApplicationController
        import asyncio
        speaker = self.container.resolve(SpeakerOutputProvider)
        controller = self.container.resolve(ApplicationController)
        asyncio.run_coroutine_threadsafe(speaker.play_audio(audio_bytes), controller._loop)