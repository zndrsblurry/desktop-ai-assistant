"""
Caption overlay widget for displaying assistant responses on screen.
"""

import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication

logger = logging.getLogger(__name__)


class CaptionOverlay(QWidget):
    """Floating caption overlay widget that displays assistant responses."""

    def __init__(self):
        super().__init__()

        # Setup window properties
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Set initial size and position
        self.setGeometry(0, 0, 600, 100)

        # Setup layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create caption label
        self.label = QLabel("")
        self.label.setStyleSheet(
            """
            background-color: rgba(0, 0, 0, 180);
            color: white;
            border-radius: 8px;
            padding: 8px 12px;
            font-size: 18px;
            font-weight: bold;
        """
        )
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)

        layout.addWidget(self.label)

        # Initially hidden
        self.hide()

    def update_text(self, text):
        """Update caption text and resize/reposition as needed."""
        if not text:
            self.hide()
            return

        # Update text
        self.label.setText(text)

        # Get current screen size
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()

        # Calculate ideal size
        max_width = int(screen_geometry.width() * 0.7)  # Max 70% of screen width
        min_width = 300

        # Get label's natural size
        label_size = self.label.sizeHint()

        # Determine final dimensions
        width = max(min_width, min(label_size.width() + 40, max_width))
        height = label_size.height() + 20  # Add padding

        # Resize
        self.resize(int(width), int(height))

        # Position at bottom center
        x = (screen_geometry.width() - self.width()) // 2
        y = screen_geometry.height() - self.height() - 40  # 40px from bottom

        self.move(x, y)

        # Show if not already visible
        if not self.isVisible():
            self.show()

    def set_visible(self, visible):
        """Set visibility of the overlay."""
        if visible:
            # Don't actually show here - showing happens in update_text
            # This is just to enable visibility in general
            pass
        else:
            self.hide()
