"""
PyQt5-based UI implementation for the AI Desktop Assistant.
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication
from ai_desktop_assistant.core.di import DependencyContainer
from ai_desktop_assistant.core.events import EventBus
from ai_desktop_assistant.ui.pyqt.main_window import MainWindow

logger = logging.getLogger(__name__)


def run_pyqt_ui(container: DependencyContainer, event_bus: EventBus):
    """Run the PyQt5-based UI for the assistant."""
    logger.info("Initializing PyQt5 UI")
    app = QApplication(sys.argv)

    # Set application metadata for QSettings
    app.setOrganizationName("AI-Desktop-Assistant")
    app.setOrganizationDomain("ai-assistant.local")
    app.setApplicationName("AI Desktop Assistant")

    # Create main window with dependency injection
    main_window = MainWindow(container, event_bus)
    main_window.show()

    logger.info("PyQt5 UI initialized and displayed")
    return app.exec_()
