# Location: ai_desktop_assistant/utils/platform.py
"""
Platform Utilities

This module provides platform-specific utilities.
"""

import os
import platform
import sys
from enum import Enum, auto


class PlatformType(Enum):
    """Enumeration of supported platforms."""

    WINDOWS = auto()
    MACOS = auto()
    LINUX = auto()
    UNKNOWN = auto()


def get_platform_type() -> PlatformType:
    """
    Get the current platform type.

    Returns:
        The platform type (WINDOWS, MACOS, LINUX, or UNKNOWN)
    """
    system = platform.system().lower()

    if system == "windows":
        return PlatformType.WINDOWS
    elif system == "darwin":
        return PlatformType.MACOS
    elif system == "linux":
        return PlatformType.LINUX
    else:
        return PlatformType.UNKNOWN


def get_app_data_dir() -> str:
    """
    Get the application data directory for the current platform.

    Returns:
        The path to the application data directory
    """
    app_name = "ai-desktop-assistant"
    platform_type = get_platform_type()

    if platform_type == PlatformType.WINDOWS:
        # Windows: AppData/Roaming
        base_dir = os.environ.get("APPDATA")
        app_dir = os.path.join(base_dir, app_name)
    elif platform_type == PlatformType.MACOS:
        # macOS: ~/Library/Application Support
        base_dir = os.path.join(
            os.path.expanduser("~"), "Library", "Application Support"
        )
        app_dir = os.path.join(base_dir, app_name)
    else:
        # Linux and others: ~/.config
        base_dir = os.path.join(os.path.expanduser("~"), ".config")
        app_dir = os.path.join(base_dir, app_name)

    # Create the directory if it doesn't exist
    os.makedirs(app_dir, exist_ok=True)

    return app_dir


def get_resource_path(relative_path: str) -> str:
    """
    Get the absolute path to a resource file.

    When running as a packaged application, resources are in a different location.
    This function handles the correct path resolution.

    Args:
        relative_path: The relative path to the resource

    Returns:
        The absolute path to the resource
    """
    # Check if running as a bundled app or from source
    if getattr(sys, "frozen", False):
        # Running as a bundled application
        base_path = sys._MEIPASS
    else:
        # Running from source
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    return os.path.join(base_path, relative_path)


def is_admin() -> bool:
    """
    Check if the application is running with administrator privileges.

    Returns:
        True if running as administrator, False otherwise
    """
    platform_type = get_platform_type()

    if platform_type == PlatformType.WINDOWS:
        try:
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except (AttributeError, ImportError):
            return False
    else:
        # For Unix-based systems
        return os.geteuid() == 0 if hasattr(os, "geteuid") else False


def get_platform_info() -> dict:
    """
    Get platform information.

    Returns:
        A dictionary with platform information
    """
    return {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
        "is_admin": is_admin(),
    }
