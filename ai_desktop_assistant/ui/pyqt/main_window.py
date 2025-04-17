"""
Main window implementation for the PyQt5-based UI.
"""

import os
import time
import json
import logging

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QMessageBox,
)
from PyQt5.QtCore import QTimer

from ai_desktop_assistant.core.di import DependencyContainer
from ai_desktop_assistant.core.events import EventBus, EventType
from ai_desktop_assistant.core.app import ApplicationController
from ai_desktop_assistant.core.config import AppConfig
from ai_desktop_assistant.ui.pyqt.screens.dashboard import DashboardScreen
from ai_desktop_assistant.ui.pyqt.screens.settings import SettingsScreen
from ai_desktop_assistant.ui.pyqt.screens.help import HelpScreen
from ai_desktop_assistant.ui.pyqt.widgets.caption_overlay import CaptionOverlay

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main window for the AI Desktop Assistant PyQt5 UI."""

    def __init__(self, container: DependencyContainer, event_bus: EventBus):
        super().__init__()
        self.container = container
        self.event_bus = event_bus
        self.app_controller = container.resolve(ApplicationController)
        self.config = container.resolve(AppConfig)

        # Initialize UI components
        self.caption_overlay = CaptionOverlay()

        # Setup UI
        self.setWindowTitle("AI Desktop Assistant")
        self.setMinimumSize(950, 750)
        self.setup_ui()

        # Connect to application controller events
        self.connect_signals()

        # Register the main window with the app controller
        self.app_controller.register_ui(self)

    def setup_ui(self):
        """Set up the main UI components."""
        # Apply stylesheet
        self.apply_stylesheet()

        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Create tab widget for main content
        self.tabs = QTabWidget()

        # Create and add tab screens
        self.dashboard = DashboardScreen(self.container, self.event_bus)
        self.settings = SettingsScreen(self.container, self.event_bus)
        self.help = HelpScreen()

        self.tabs.addTab(self.dashboard, "Dashboard")
        self.tabs.addTab(self.settings, "Settings")
        self.tabs.addTab(self.help, "Help")

        # Add tabs to main layout
        main_layout.addWidget(self.tabs)

        # Set central widget
        self.setCentralWidget(main_widget)

        # Create status bar
        self.statusBar().showMessage("Ready")

        # Load and apply settings
        QTimer.singleShot(100, self.load_settings)

    def apply_stylesheet(self):
        """Apply the application stylesheet."""
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background-color: #2d2d2d; color: #e0e0e0; }
            QGroupBox { 
                border: 1px solid #555; 
                border-radius: 5px; 
                margin-top: 10px; 
                font-weight: bold; 
                color: #e0e0e0; 
                padding-top: 10px; 
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                subcontrol-position: top left; 
                left: 10px; 
                padding: 0 5px; 
                background-color: #2d2d2d; 
            }
            QPushButton { 
                background-color: #3c3c3c; 
                border: 1px solid #555; 
                border-radius: 4px; 
                padding: 8px 15px; 
                color: #e0e0e0; 
            }
            QPushButton:hover { background-color: #4c4c4c; }
            QPushButton:pressed { background-color: #2a2a2a; }
            QPushButton:disabled { 
                background-color: #2a2a2a; 
                color: #666; 
                border: 1px solid #444;
            }
            QTextEdit, QLineEdit { 
                background-color: #333; 
                border: 1px solid #555; 
                border-radius: 3px; 
                color: #e0e0e0; 
                padding: 4px; 
            }
            QComboBox { 
                background-color: #333; 
                border: 1px solid #555; 
                border-radius: 3px; 
                color: #e0e0e0; 
                padding: 4px; 
            }
            QComboBox::drop-down { border: none; width: 15px; }
            QSlider::groove:horizontal { 
                border: 1px solid #555; 
                height: 8px; 
                background: #333; 
                margin: 2px 0; 
                border-radius: 4px;
            }
            QSlider::handle:horizontal { 
                background: #777; 
                border: 1px solid #888; 
                width: 18px; 
                margin: -5px 0; 
                border-radius: 9px;
            }
            QLabel { color: #e0e0e0; padding: 2px; }
            QCheckBox, QRadioButton { color: #e0e0e0; padding: 3px;}
            QCheckBox::indicator, QRadioButton::indicator { 
                width: 13px; 
                height: 13px; 
                border: 1px solid #777; 
                border-radius: 3px; 
                background-color: #444;
            }
            QCheckBox::indicator:checked, QRadioButton::indicator:checked { 
                background-color: #5e9de0; 
                border: 1px solid #77b; 
            }
            QRadioButton::indicator { border-radius: 7px; }
            QTabWidget::pane { 
                border: 1px solid #555; 
                background-color: #2d2d2d; 
                padding: 10px; 
            }
            QTabBar::tab { 
                background-color: #3c3c3c; 
                color: #e0e0e0; 
                border: 1px solid #555; 
                border-bottom: none; 
                border-top-left-radius: 4px; 
                border-top-right-radius: 4px; 
                padding: 8px 15px; 
                margin-right: 2px;
            }
            QTabBar::tab:selected { 
                background-color: #4c5a6b; 
                border-bottom: 1px solid #4c5a6b; 
            }
            QTabBar::tab:hover { background-color: #4c4c4c; }
            QToolTip { 
                background-color: #383838; 
                color: #ddd; 
                border: 1px solid #555; 
            }
        """
        )

    def connect_signals(self):
        """Connect to application controller signals."""
        # Connect dashboard signals
        self.dashboard.start_button.clicked.connect(self.toggle_assistant)
        self.dashboard.pause_button.clicked.connect(self.toggle_pause)
        self.dashboard.stop_button.clicked.connect(self.emergency_stop)

        # Connect settings signals
        self.settings.apply_button.clicked.connect(self.apply_settings)

        # Connect app controller signals
        self.event_bus.subscribe(EventType.STATE_CHANGED, self.on_state_changed)
        self.event_bus.subscribe(EventType.ERROR, self.on_error)

    def load_settings(self):
        """Load application settings and update UI."""
        config_file = os.path.join(os.path.expanduser("~"), ".ai_assistant_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    config_data = json.load(f)
                    # Update settings screen with loaded values
                    self.settings.update_from_config(config_data)
                    logger.info(f"Settings loaded from {config_file}")
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
                QMessageBox.warning(
                    self, "Settings Error", f"Failed to load settings: {e}"
                )

    def apply_settings(self):
        """Apply settings from the settings screen."""
        settings = self.settings.get_settings()

        # Save settings to file
        config_file = os.path.join(os.path.expanduser("~"), ".ai_assistant_config.json")
        try:
            with open(config_file, "w") as f:
                json.dump(settings, f, indent=4)
            logger.info(f"Settings saved to {config_file}")
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.warning(self, "Settings Error", f"Failed to save settings: {e}")
            return False

        # Apply settings to app controller
        # This will depend on your specific settings structure
        # self.app_controller.update_config(settings)

        return True

    def toggle_assistant(self):
        """Start or stop the assistant."""
        if self.app_controller.state == "idle":
            # Apply settings before starting
            if not self.apply_settings():
                return

            # Start assistant
            self.dashboard.set_running_state(True)
            self.statusBar().showMessage("Starting assistant...")
            self.app_controller.start_assistant()
        else:
            # Stop assistant
            self.dashboard.set_running_state(False)
            self.statusBar().showMessage("Stopping assistant...")
            self.app_controller.stop_assistant()

    def toggle_pause(self):
        """Pause or resume the assistant."""
        if self.app_controller.state == "paused":
            self.app_controller.resume_assistant()
            self.dashboard.set_paused_state(False)
            self.statusBar().showMessage("Assistant resumed")
        else:
            self.app_controller.pause_assistant()
            self.dashboard.set_paused_state(True)
            self.statusBar().showMessage("Assistant paused")

    def emergency_stop(self):
        """Emergency stop the assistant."""
        self.app_controller.emergency_stop()
        self.dashboard.set_running_state(False)
        self.statusBar().showMessage("Emergency stop activated")
        self.add_log("Emergency stop activated")

    def on_state_changed(self, state_name, state_value):
        """Handle state change events from the app controller."""
        if state_name == "assistant_state":
            self.dashboard.update_status(state_value)
            self.statusBar().showMessage(f"Assistant: {state_value}")
        elif state_name == "is_busy":
            self.dashboard.update_busy_indicator(state_value)

    def on_error(self, error_type, error_message):
        """Handle error events from the app controller."""
        self.add_log(f"Error ({error_type}): {error_message}")
        self.statusBar().showMessage(f"Error: {error_type}")

    def add_log(self, text):
        """Add text to the log widget."""
        timestamp = time.strftime("%H:%M:%S")
        self.dashboard.log_text.append(f"{timestamp} - {text}")
        # Auto-scroll to bottom
        self.dashboard.log_text.verticalScrollBar().setValue(
            self.dashboard.log_text.verticalScrollBar().maximum()
        )

    def update_caption(self, text):
        """Update the caption overlay text."""
        if hasattr(self, "caption_overlay"):
            self.caption_overlay.update_text(text)

    def closeEvent(self, event):
        """Handle application close event."""
        # Stop the assistant if running
        if self.app_controller.state != "idle":
            self.app_controller.stop_assistant()

        # Wait a bit for graceful shutdown
        QTimer.singleShot(500, self.finalize_close)

        # Accept the close event
        event.accept()

    def finalize_close(self):
        """Finalize the closing process."""
        # Hide caption overlay
        if hasattr(self, "caption_overlay"):
            self.caption_overlay.hide()

        # Additional cleanup if needed
        logger.info("Application UI closed")
