"""
Settings screen for the PyQt5-based AI Desktop Assistant.
"""

import logging
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QLineEdit,
    QCheckBox,
    QComboBox,
    QRadioButton,
    QButtonGroup,
    QSlider,
    QFormLayout,
)
from PyQt5.QtCore import Qt

from ai_desktop_assistant.core.di import DependencyContainer
from ai_desktop_assistant.core.events import EventBus

logger = logging.getLogger(__name__)


class SettingsScreen(QWidget):
    """Settings screen for configuring the assistant."""

    def __init__(self, container: DependencyContainer, event_bus: EventBus):
        super().__init__()
        self.container = container
        self.event_bus = event_bus

        # Setup UI components
        self.setup_ui()

    def setup_ui(self):
        """Set up the settings UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # API Settings Group
        api_group = QGroupBox("API Settings")
        api_form_layout = QFormLayout(api_group)

        # API Key input
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter your API key")
        api_form_layout.addRow("API Key:", self.api_key_input)

        # Model selection
        self.model_selection = QComboBox()
        self.model_selection.addItems(
            ["gemini-pro", "gemini-1.5-pro", "gemini-1.5-flash"]
        )
        api_form_layout.addRow("Model:", self.model_selection)

        main_layout.addWidget(api_group)

        # Features Group
        features_group = QGroupBox("Assistant Features")
        features_layout = QVBoxLayout(features_group)

        # Feature checkboxes
        features_row = QHBoxLayout()
        self.voice_enabled = QCheckBox("Enable Voice Feedback")
        self.voice_enabled.setToolTip("Speak responses aloud using text-to-speech")

        self.captions_enabled = QCheckBox("Enable Screen Captions")
        self.captions_enabled.setToolTip(
            "Show assistant's text responses as an overlay"
        )

        features_row.addWidget(self.voice_enabled)
        features_row.addWidget(self.captions_enabled)
        features_row.addStretch()
        features_layout.addLayout(features_row)

        # TTS Options
        tts_group = QGroupBox("Text-to-Speech Settings")
        tts_layout = QVBoxLayout(tts_group)

        # TTS Type Selection
        tts_type_layout = QHBoxLayout()
        tts_type_label = QLabel("Voice Type:")
        self.tts_type_group = QButtonGroup(tts_group)

        self.standard_tts_radio = QRadioButton("Standard (Offline)")
        self.standard_tts_radio.setToolTip("Faster, works offline, less natural voice")

        self.natural_tts_radio = QRadioButton("Natural (Online)")
        self.natural_tts_radio.setToolTip("More natural voice, requires internet")

        self.tts_type_group.addButton(self.standard_tts_radio)
        self.tts_type_group.addButton(self.natural_tts_radio)

        tts_type_layout.addWidget(tts_type_label)
        tts_type_layout.addWidget(self.standard_tts_radio)
        tts_type_layout.addWidget(self.natural_tts_radio)
        tts_type_layout.addStretch()
        tts_layout.addLayout(tts_type_layout)

        # Voice Selection
        voice_layout = QHBoxLayout()
        voice_label = QLabel("Voice:")
        self.voice_combo = QComboBox()
        self.voice_combo.addItems(["alloy", "echo", "fable", "onyx", "nova", "shimmer"])

        # Connect the radio button to enable/disable combo
        self.natural_tts_radio.toggled.connect(self.voice_combo.setEnabled)

        voice_layout.addWidget(voice_label)
        voice_layout.addWidget(self.voice_combo)
        voice_layout.addStretch()
        tts_layout.addLayout(voice_layout)

        # Voice Rate
        rate_layout = QHBoxLayout()
        rate_label = QLabel("Voice Speed:")
        self.voice_rate_slider = QSlider(Qt.Horizontal)
        self.voice_rate_slider.setMinimum(100)
        self.voice_rate_slider.setMaximum(350)
        self.voice_rate_slider.setSingleStep(10)

        self.voice_rate_value = QLabel("180 WPM")
        self.voice_rate_slider.valueChanged.connect(
            lambda value: self.voice_rate_value.setText(f"{value} WPM")
        )

        rate_layout.addWidget(rate_label)
        rate_layout.addWidget(self.voice_rate_slider)
        rate_layout.addWidget(self.voice_rate_value)
        tts_layout.addLayout(rate_layout)

        features_layout.addWidget(tts_group)

        # Performance Settings
        perf_group = QGroupBox("Performance")
        perf_layout = QVBoxLayout(perf_group)

        # Screen Capture Interval
        interval_layout = QHBoxLayout()
        interval_label = QLabel("Screen Analysis Interval:")
        self.interval_slider = QSlider(Qt.Horizontal)
        self.interval_slider.setMinimum(5)  # 0.5 sec
        self.interval_slider.setMaximum(50)  # 5.0 sec

        self.interval_value = QLabel("1.0 s")
        self.interval_slider.valueChanged.connect(
            lambda value: self.interval_value.setText(f"{value / 10.0:.1f} s")
        )

        interval_layout.addWidget(interval_label)
        interval_layout.addWidget(self.interval_slider)
        interval_layout.addWidget(self.interval_value)
        perf_layout.addLayout(interval_layout)

        features_layout.addWidget(perf_group)

        main_layout.addWidget(features_group)

        # Hotkeys Group
        hotkeys_group = QGroupBox("Hotkeys")
        hotkeys_form = QFormLayout(hotkeys_group)

        self.emergency_key = QComboBox()
        self.emergency_key.addItems(["esc", "f1", "f10", "f11", "ctrl+shift+esc"])
        hotkeys_form.addRow("Emergency Stop Key:", self.emergency_key)

        self.pause_key = QComboBox()
        self.pause_key.addItems(["f12", "f8", "f9", "pause", "scroll lock"])
        hotkeys_form.addRow("Pause/Resume Key:", self.pause_key)

        main_layout.addWidget(hotkeys_group)

        # Apply Button
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.apply_button = QPushButton("Apply Settings")
        self.apply_button.setMinimumHeight(35)
        button_layout.addWidget(self.apply_button)

        main_layout.addLayout(button_layout)
        main_layout.addStretch()

        # Set default values
        self.standard_tts_radio.setChecked(True)
        self.voice_combo.setEnabled(False)
        self.voice_enabled.setChecked(True)
        self.captions_enabled.setChecked(True)
        self.voice_rate_slider.setValue(180)
        self.interval_slider.setValue(10)  # 1.0 sec

    def update_from_config(self, config_data):
        """Update UI elements from configuration data."""
        # Update API settings
        if "api_key" in config_data:
            self.api_key_input.setText(config_data["api_key"])

        if "model" in config_data:
            model_index = self.model_selection.findText(config_data["model"])
            if model_index >= 0:
                self.model_selection.setCurrentIndex(model_index)

        # Update feature settings
        if "voice_enabled" in config_data:
            self.voice_enabled.setChecked(config_data["voice_enabled"])

        if "caption_enabled" in config_data:
            self.captions_enabled.setChecked(config_data["caption_enabled"])

        # Update TTS settings
        if "use_natural_tts" in config_data:
            self.natural_tts_radio.setChecked(config_data["use_natural_tts"])
            self.standard_tts_radio.setChecked(not config_data["use_natural_tts"])
            self.voice_combo.setEnabled(config_data["use_natural_tts"])

        if "tts_voice" in config_data:
            voice_index = self.voice_combo.findText(config_data["tts_voice"])
            if voice_index >= 0:
                self.voice_combo.setCurrentIndex(voice_index)

        if "voice_rate" in config_data:
            self.voice_rate_slider.setValue(config_data["voice_rate"])

        # Update performance settings
        if "screen_capture_interval" in config_data:
            # Convert from seconds to slider value (x10)
            interval_value = int(config_data["screen_capture_interval"] * 10)
            self.interval_slider.setValue(interval_value)

        # Update hotkey settings
        if "emergency_key" in config_data:
            emergency_index = self.emergency_key.findText(config_data["emergency_key"])
            if emergency_index >= 0:
                self.emergency_key.setCurrentIndex(emergency_index)

        if "pause_key" in config_data:
            pause_index = self.pause_key.findText(config_data["pause_key"])
            if pause_index >= 0:
                self.pause_key.setCurrentIndex(pause_index)

    def get_settings(self):
        """Get current settings from UI elements."""
        settings = {
            "api_key": self.api_key_input.text(),
            "model": self.model_selection.currentText(),
            "voice_enabled": self.voice_enabled.isChecked(),
            "caption_enabled": self.captions_enabled.isChecked(),
            "use_natural_tts": self.natural_tts_radio.isChecked(),
            "tts_voice": self.voice_combo.currentText(),
            "voice_rate": self.voice_rate_slider.value(),
            "screen_capture_interval": self.interval_slider.value() / 10.0,
            "emergency_key": self.emergency_key.currentText(),
            "pause_key": self.pause_key.currentText(),
            # Additional settings can be added here as needed
        }
        return settings
