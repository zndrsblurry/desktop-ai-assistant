"""
Dashboard screen for the PyQt5-based AI Desktop Assistant.
"""

import time
import logging
import numpy as np
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QPushButton,
    QTextEdit,
    QRadioButton,
    QButtonGroup,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QPixmap, QImage

from ai_desktop_assistant.core.di import DependencyContainer
from ai_desktop_assistant.core.events import EventBus
from ai_desktop_assistant.ui.pyqt.widgets.screen_capture import ScreenCaptureThread

logger = logging.getLogger(__name__)


class DashboardScreen(QWidget):
    """Dashboard screen with monitor selection, preview, and controls."""

    def __init__(self, container: DependencyContainer, event_bus: EventBus):
        super().__init__()
        self.container = container
        self.event_bus = event_bus

        # Setup UI components
        self.setup_ui()

        # Initialize screen capture thread
        self.screen_capture_thread = None
        QTimer.singleShot(200, self.setup_screen_capture)

    def setup_ui(self):
        """Set up the dashboard UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Top Section: Monitor Selection and Preview
        top_layout = QHBoxLayout()

        # Monitor Selection Group
        self.monitors_group = QGroupBox("Monitor Selection")
        monitors_layout = QVBoxLayout(self.monitors_group)

        # We'll add monitor radio buttons dynamically later
        self.monitor_button_group = QButtonGroup(self.monitors_group)
        self.monitor_buttons = []

        # Add placeholder text
        placeholder_label = QLabel("Loading monitors...")
        monitors_layout.addWidget(placeholder_label)

        top_layout.addWidget(self.monitors_group, 1)  # Stretch factor 1

        # Screen Preview Group
        preview_group = QGroupBox("Live Screen Preview")
        preview_layout = QVBoxLayout(preview_group)

        self.screen_label = QLabel("Preview Loading...")
        self.screen_label.setAlignment(Qt.AlignCenter)
        self.screen_label.setMinimumSize(480, 270)
        self.screen_label.setStyleSheet(
            "background-color: #222; border: 1px solid #444; color: #777;"
        )

        preview_layout.addWidget(self.screen_label)
        top_layout.addWidget(preview_group, 3)  # Stretch factor 3

        main_layout.addLayout(top_layout)

        # Monitor Info and Refresh Button
        info_layout = QHBoxLayout()

        self.screen_info_label = QLabel("Select monitor above or Refresh.")
        self.screen_info_label.setStyleSheet("font-style: italic; color: #aaa;")

        self.refresh_button = QPushButton("Refresh Monitor List")
        self.refresh_button.setToolTip("Scan for connected monitors again.")
        self.refresh_button.clicked.connect(self.refresh_monitor_list)

        info_layout.addWidget(self.screen_info_label)
        info_layout.addStretch()
        info_layout.addWidget(self.refresh_button)

        main_layout.addLayout(info_layout)

        # Controls Group
        controls_group = QGroupBox("Assistant Controls")
        controls_layout = QHBoxLayout(controls_group)

        self.start_button = QPushButton("Start Assistant")
        self.start_button.setStyleSheet("background-color: #4a7f4a;")  # Green
        self.start_button.setToolTip("Start or Stop the AI Assistant.")

        self.pause_button = QPushButton("Pause")
        self.pause_button.setToolTip("Pause or Resume the assistant.")
        self.pause_button.setEnabled(False)  # Disabled initially

        self.stop_button = QPushButton("Emergency Stop")
        self.stop_button.setStyleSheet("background-color: #a04040;")  # Red
        self.stop_button.setToolTip("Immediately stop the assistant.")
        self.stop_button.setEnabled(False)  # Disabled initially

        controls_layout.addWidget(self.start_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.stop_button)

        main_layout.addWidget(controls_group)

        # Log Group
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFontFamily("Consolas, Courier New, monospace")
        self.log_text.setMinimumHeight(150)

        log_layout.addWidget(self.log_text)

        main_layout.addWidget(log_group, 1)  # Make log group stretch

        # Status Bar
        status_layout = QHBoxLayout()

        status_label = QLabel("Status:")
        self.status_text = QLabel("Ready")
        self.status_text.setStyleSheet("font-weight: bold;")

        status_layout.addWidget(status_label)
        status_layout.addWidget(self.status_text, 1)  # Stretch
        status_layout.addStretch()

        main_layout.addLayout(status_layout)

    def setup_screen_capture(self):
        """Initialize the screen capture thread for preview."""
        if self.screen_capture_thread and self.screen_capture_thread.isRunning():
            self.screen_capture_thread.stop()

        # Default to monitor 1 (or 0 if only one monitor)
        monitor_index = 1

        self.screen_capture_thread = ScreenCaptureThread(
            monitor_index, 0.5
        )  # 0.5s refresh rate
        self.screen_capture_thread.update_frame.connect(
            self.update_screen_image, Qt.QueuedConnection
        )
        self.screen_capture_thread.start()

        # Now refresh the monitor list UI
        self.refresh_monitor_list()

        # Add initial log message
        self.add_log("Dashboard initialized. Screen capture preview started.")

    def refresh_monitor_list(self):
        """Refresh the list of available monitors."""
        # Clear existing radio buttons
        for button in self.monitor_buttons:
            self.monitor_button_group.removeButton(button)
            button.deleteLater()

        self.monitor_buttons = []

        # Get current layout of the monitors group
        monitors_layout = self.monitors_group.layout()

        # Clear all widgets from the layout
        while monitors_layout.count():
            item = monitors_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            # Import MSS here to avoid potential import issues
            import mss

            with mss.mss() as sct:
                monitors = sct.monitors

                # Add "All Monitors" option (index 0)
                combined_monitor = monitors[0]
                radio_text = f"All Monitors: {combined_monitor['width']}x{combined_monitor['height']}"
                combined_radio = QRadioButton(radio_text)
                combined_radio.setToolTip(
                    f"Position: ({combined_monitor['left']}, {combined_monitor['top']})"
                )
                combined_radio.monitor_index = 0

                self.monitor_buttons.append(combined_radio)
                self.monitor_button_group.addButton(combined_radio)
                monitors_layout.addWidget(combined_radio)

                # Add individual monitors
                for i in range(1, len(monitors)):
                    monitor = monitors[i]
                    radio_text = f"Monitor {i}: {monitor['width']}x{monitor['height']}"
                    radio = QRadioButton(radio_text)
                    radio.setToolTip(f"Position: ({monitor['left']}, {monitor['top']})")
                    radio.monitor_index = i

                    self.monitor_buttons.append(radio)
                    self.monitor_button_group.addButton(radio)
                    monitors_layout.addWidget(radio)

                # Connect signals after adding all buttons
                for button in self.monitor_buttons:
                    button.toggled.connect(
                        lambda checked, idx=button.monitor_index: (
                            self.select_monitor(idx) if checked else None
                        )
                    )

                # Select monitor 1 by default, or 0 if only one monitor
                default_monitor = 1 if len(monitors) > 1 else 0
                if default_monitor < len(self.monitor_buttons):
                    self.monitor_buttons[default_monitor].setChecked(True)
                elif self.monitor_buttons:
                    self.monitor_buttons[0].setChecked(True)

                self.add_log(f"Found {len(monitors)} monitors")

        except Exception as e:
            error_label = QLabel(f"Error listing monitors: {str(e)}")
            error_label.setStyleSheet("color: #ff6666;")
            monitors_layout.addWidget(error_label)
            self.add_log(f"Error refreshing monitor list: {str(e)}")

    def select_monitor(self, monitor_index):
        """Handle monitor selection change."""
        self.add_log(f"Selected monitor {monitor_index}")

        # Update the info label
        try:
            import mss

            with mss.mss() as sct:
                monitors = sct.monitors
                if 0 <= monitor_index < len(monitors):
                    monitor = monitors[monitor_index]
                    if monitor_index == 0:
                        info_text = f"Selected: All Monitors (Combined View) ({monitor['width']}x{monitor['height']})"
                    else:
                        info_text = f"Selected: Mon {monitor_index} ({monitor['width']}x{monitor['height']} at ({monitor['left']},{monitor['top']}))"
                    self.screen_info_label.setText(info_text)
                    self.screen_info_label.setStyleSheet(
                        "font-style: normal; color: #e0e0e0;"
                    )

                    # Update screen capture thread
                    if (
                        self.screen_capture_thread
                        and self.screen_capture_thread.isRunning()
                    ):
                        self.screen_capture_thread.set_monitor(monitor_index)
                else:
                    self.screen_info_label.setText(
                        f"Selected: Monitor {monitor_index} (Invalid Index!)"
                    )
                    self.screen_info_label.setStyleSheet(
                        "font-style: italic; color: #ffaaaa;"
                    )
        except Exception as e:
            self.screen_info_label.setText(f"Error getting monitor details: {str(e)}")
            self.screen_info_label.setStyleSheet("font-style: italic; color: #ffaaaa;")
            self.add_log(f"Error updating monitor info: {str(e)}")

    @pyqtSlot(np.ndarray)
    def update_screen_image(self, frame):
        """Update the screen preview image."""
        if not hasattr(self, "screen_label") or not self.screen_label.isVisible():
            return

        try:
            h, w, ch = frame.shape
            if h == 0 or w == 0:
                return

            # Convert numpy array to QImage
            bytes_per_line = ch * w
            qt_image = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

            # Scale while maintaining aspect ratio
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(
                self.screen_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            )

            self.screen_label.setPixmap(scaled_pixmap)
        except Exception:
            # Don't log screen update errors to avoid spam
            pass

    def update_status(self, status_text):
        """Update the status text label."""
        self.status_text.setText(status_text)

    def update_busy_indicator(self, is_busy):
        """Update UI indicators based on busy state."""
        pass  # We can implement visual busy indicators if needed

    def set_running_state(self, is_running):
        """Update UI for running/stopped state."""
        if is_running:
            self.start_button.setText("Stop Assistant")
            self.start_button.setStyleSheet("background-color: #a04040;")  # Red
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            # Disable settings-related controls
            self.monitors_group.setEnabled(False)
            self.refresh_button.setEnabled(False)
        else:
            self.start_button.setText("Start Assistant")
            self.start_button.setStyleSheet("background-color: #4a7f4a;")  # Green
            self.pause_button.setEnabled(False)
            self.pause_button.setText("Pause")
            self.stop_button.setEnabled(False)
            # Re-enable settings-related controls
            self.monitors_group.setEnabled(True)
            self.refresh_button.setEnabled(True)

    def set_paused_state(self, is_paused):
        """Update UI for paused/resumed state."""
        if is_paused:
            self.pause_button.setText("Resume")
            self.update_status("Paused")
        else:
            self.pause_button.setText("Pause")
            self.update_status("Running")

    def add_log(self, text):
        """Add timestamped text to the log."""
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"{timestamp} - {text}")
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
