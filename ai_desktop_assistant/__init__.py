"""
AI Desktop Assistant - Main Application Package

This package contains the core source code for the AI Desktop Assistant,
a tool enabling natural language control of your computer using Google's
Gemini Live API and LangChain.

Key Sub-packages:
- ai: Handles AI model interaction, prompts, tools, and LangChain integration.
- core: Provides foundational components like the main app controller, event bus,
        dependency injection, state, configuration, and exceptions.
- interfaces: Defines abstract base classes (protocols) for key components.
- ui: Contains all user interface elements (PyQt6, QML, widgets, assets).
- services: Implements core services like the AI service wrapper.
- input: Provides input sources (microphone, keyboard listeners).
- output: Manages output channels (speakers, UI captions, notifications).
- actions: Defines and executes actions requested by the AI (mouse, keyboard, etc.).
- utils: Contains shared utility functions and classes.

See README.md for setup and usage instructions.
"""

import sys
import os
import logging

__version__ = "0.1.0"  # Keep aligned with pyproject.toml manually or via automation

__author__ = "Alexander Unabia"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2025 Alexander Unabia"

# --- Application Constants ---
APP_NAME = "AI Desktop Assistant"
APP_ID = (
    "com.yourdomain.ai-desktop-assistant"  # Use reverse domain notation for unique ID
)
APP_ORGANIZATION = "AI Assistant Project"  # Optional organization name

# Version tuple for easy comparison
try:
    VERSION_INFO = tuple(map(int, __version__.split(".")))
except ValueError:
    VERSION_INFO = (0, 0, 0)  # Fallback for non-standard versions

# --- Environment Setup / Checks (Optional) ---
# Example: Check Python version compatibility early
MIN_PYTHON_VERSION = (3, 10)
if sys.version_info < MIN_PYTHON_VERSION:
    print(
        f"ERROR: {APP_NAME} requires Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} or later. "
        f"You are using Python {sys.version.split()[0]}.",
        file=sys.stderr,
    )
    # sys.exit(1) # Exit early if desired

# Example: Set environment variable for Qt library selection if needed
# os.environ['QT_API'] = 'pyqt6'

# --- Logging Initialization (Minimal) ---
# Configure basic logging here just in case setup_logging isn't called early enough elsewhere.
# This prevents "No handler found" warnings from libraries used during import.


_log = logging.getLogger(__name__)
if not logging.getLogger("ai_desktop_assistant").hasHandlers():
    _null_handler = logging.NullHandler()
    logging.getLogger("ai_desktop_assistant").addHandler(_null_handler)

_log.info(f"Initializing {APP_NAME} package version {__version__}")

__all__ = [
    "__version__",
    "APP_NAME",
    "APP_ID",
]
