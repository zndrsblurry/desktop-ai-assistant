#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
AI Desktop Assistant - Main Entry Point

This module is the entry point for the AI Desktop Assistant application.
It initializes the core components and starts the UI.
"""

import sys
import asyncio

from ai_desktop_assistant.core.config import AppConfig
from ai_desktop_assistant.core.di import DependencyContainer
from ai_desktop_assistant.core.events import EventBus
from ai_desktop_assistant.core.app import ApplicationController

# Import UI (we now support both QML and PyQt5)
from ai_desktop_assistant.ui.pyqt_ui import run_pyqt_ui


# Configure logging
from ai_desktop_assistant.utils.logging import setup_logging

logger = setup_logging()

# Import core components


async def init_app(container: DependencyContainer, event_bus: EventBus):
    """Initialize the application components asynchronously."""
    logger.info("Initializing application controller")
    app_controller = container.resolve(ApplicationController)
    await app_controller.initialize()
    return app_controller


def main():
    """Main entry point for the application."""
    try:
        logger.info("Starting AI Desktop Assistant")

        # Load configuration
        config = AppConfig()
        print(f"Loaded configuration: {config.app_name} v{config.app_version}")
        logger.info(f"Loaded configuration: {config.app_name} v{config.app_version}")

        # Initialize dependency container and event bus
        container = DependencyContainer()
        event_bus = EventBus()

        # Register core components
        container.register_instance(config)
        container.register_instance(event_bus)

        # Create application controller
        app_controller = ApplicationController(container, event_bus)
        container.register_instance(app_controller)

        # Initialize components asynchronously
        loop = asyncio.get_event_loop()
        loop.run_until_complete(app_controller.initialize())

        # Start the PyQt5 UI
        exit_code = run_pyqt_ui(container, event_bus)

        # Perform graceful shutdown
        logger.info("Shutting down application")
        loop.run_until_complete(app_controller.shutdown())

        return exit_code

    except Exception as e:
        logger.exception(f"Fatal error: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
