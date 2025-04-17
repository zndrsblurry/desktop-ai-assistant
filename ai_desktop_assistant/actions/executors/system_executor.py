# Location: ai_desktop_assistant/actions/executors/system_executor.py
"""
System Executor

This module implements the system action executor for system-level operations.
"""

import asyncio
import logging
import os
import sys
from typing import Any, Dict, Optional, Set

from ai_desktop_assistant.core.events import EventBus
from ai_desktop_assistant.core.exceptions import ActionError, SecurityError
from ai_desktop_assistant.interfaces.action_executor import ActionExecutor


class SystemExecutor(ActionExecutor):
    """Implementation of the system action executor."""

    # Set of supported action types
    SUPPORTED_ACTIONS: Set[str] = {
        "launch_application",
        "open_file",
        "open_folder",
        "open_url",
        "get_clipboard",
        "set_clipboard",
        "take_screenshot",
    }

    def __init__(self, event_bus: EventBus):
        """
        Initialize the system executor.

        Args:
            event_bus: The application event bus
        """
        self.logger = logging.getLogger(__name__)
        self.event_bus = event_bus

    async def initialize(self) -> None:
        """Initialize the system executor."""
        self.logger.info("Initializing system executor")
        self.logger.info("System executor initialized")

    async def shutdown(self) -> None:
        """Shut down the system executor."""
        self.logger.info("Shutting down system executor")
        self.logger.info("System executor shut down")

    async def execute_action(
        self, action_type: str, params: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Execute a system action.

        Args:
            action_type: The type of action to execute
            params: Action parameters

        Returns:
            The action result or None if the action doesn't produce a result

        Raises:
            ActionError: If execution fails
            SecurityError: If a security violation is detected
        """
        if not self.can_execute(action_type):
            raise ActionError(f"Unsupported action type: {action_type}")

        try:
            if action_type == "launch_application":
                return await self._launch_application(params)
            elif action_type == "open_file":
                return await self._open_file(params)
            elif action_type == "open_folder":
                return await self._open_folder(params)
            elif action_type == "open_url":
                return await self._open_url(params)
            elif action_type == "get_clipboard":
                return await self._get_clipboard(params)
            elif action_type == "set_clipboard":
                return await self._set_clipboard(params)
            elif action_type == "take_screenshot":
                return await self._take_screenshot(params)

            return None

        except Exception as e:
            self.logger.error(f"Error executing system action {action_type}: {e}")
            raise ActionError(f"Failed to execute system action {action_type}: {e}")

    def can_execute(self, action_type: str) -> bool:
        """
        Check if this executor can execute the given action type.

        Args:
            action_type: The action type to check

        Returns:
            True if this executor can execute the action, False otherwise
        """
        return action_type in self.SUPPORTED_ACTIONS

    def _check_path_security(self, path: str) -> None:
        """
        Check if a file or folder path is safe to access.

        Args:
            path: The path to check

        Raises:
            SecurityError: If the path is potentially unsafe
        """
        # Convert to absolute path
        abs_path = os.path.abspath(path)

        # Check for sensitive directories
        sensitive_dirs = [
            "/etc",
            "/var",
            "/boot",
            "/root",
            "/usr/bin",
            "/usr/sbin",
            "/System",
            "/Library/SystemExtensions",
            "C:\\Windows",
            "C:\\Program Files",
            "C:\\Program Files (x86)",
        ]

        for sensitive_dir in sensitive_dirs:
            if abs_path.startswith(sensitive_dir):
                raise SecurityError(
                    f"Access to sensitive directory not allowed: {abs_path}"
                )

    async def _launch_application(self, params: Dict[str, Any]) -> bool:
        """
        Launch an application.

        Args:
            params: Action parameters
                app_name: The name of the application to launch

        Returns:
            True if the application was launched successfully, False otherwise
        """
        # Get parameters
        app_name = params.get("app_name")

        # Validate parameters
        if app_name is None:
            raise ActionError("Missing required parameter: app_name")

        # Different approaches for different platforms
        platform = sys.platform

        try:
            if platform == "win32":
                # Windows
                await asyncio.create_subprocess_shell(f"start {app_name}")
            elif platform == "darwin":
                # macOS
                await asyncio.create_subprocess_shell(f"open -a '{app_name}'")
            else:
                # Linux and others
                await asyncio.create_subprocess_shell(app_name)

            return True

        except Exception as e:
            self.logger.error(f"Error launching application {app_name}: {e}")
            return False

    async def _open_file(self, params: Dict[str, Any]) -> bool:
        """
        Open a file with the default application.

        Args:
            params: Action parameters
                file_path: The path of the file to open

        Returns:
            True if the file was opened successfully, False otherwise
        """
        # Get parameters
        file_path = params.get("file_path")

        # Validate parameters
        if file_path is None:
            raise ActionError("Missing required parameter: file_path")

        # Check security
        self._check_path_security(file_path)

        # Different approaches for different platforms
        platform = sys.platform

        try:
            if platform == "win32":
                # Windows
                os.startfile(file_path)
            elif platform == "darwin":
                # macOS
                await asyncio.create_subprocess_shell(f"open '{file_path}'")
            else:
                # Linux and others
                await asyncio.create_subprocess_shell(f"xdg-open '{file_path}'")

            return True

        except Exception as e:
            self.logger.error(f"Error opening file {file_path}: {e}")
            return False

    async def _open_folder(self, params: Dict[str, Any]) -> bool:
        """
        Open a folder in the file explorer.

        Args:
            params: Action parameters
                folder_path: The path of the folder to open

        Returns:
            True if the folder was opened successfully, False otherwise
        """
        # Get parameters
        folder_path = params.get("folder_path")

        # Validate parameters
        if folder_path is None:
            raise ActionError("Missing required parameter: folder_path")

        # Check security
        self._check_path_security(folder_path)

        # Different approaches for different platforms
        platform = sys.platform

        try:
            if platform == "win32":
                # Windows
                os.startfile(folder_path)
            elif platform == "darwin":
                # macOS
                await asyncio.create_subprocess_shell(f"open '{folder_path}'")
            else:
                # Linux and others
                await asyncio.create_subprocess_shell(f"xdg-open '{folder_path}'")

            return True

        except Exception as e:
            self.logger.error(f"Error opening folder {folder_path}: {e}")
            return False

    async def _open_url(self, params: Dict[str, Any]) -> bool:
        """
        Open a URL in the default web browser.

        Args:
            params: Action parameters
                url: The URL to open

        Returns:
            True if the URL was opened successfully, False otherwise
        """
        # Get parameters
        url = params.get("url")

        # Validate parameters
        if url is None:
            raise ActionError("Missing required parameter: url")

        # Validate URL format
        if not url.startswith(("http://", "https://")):
            url = "https://" + url

        try:
            # Use the webbrowser module to open the URL
            import webbrowser

            # Execute in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, lambda: webbrowser.open(url))

            return success

        except Exception as e:
            self.logger.error(f"Error opening URL {url}: {e}")
            return False

    async def _get_clipboard(self, params: Dict[str, Any]) -> str:
        """
        Get the current clipboard content.

        Returns:
            The clipboard content as a string
        """
        try:
            # Use pyperclip or equivalent to get clipboard content
            try:
                import pyperclip

                # Execute in a thread to avoid blocking
                loop = asyncio.get_event_loop()
                clipboard_content = await loop.run_in_executor(
                    None, lambda: pyperclip.paste()
                )

                return clipboard_content

            except ImportError:
                raise ActionError("Clipboard access requires the pyperclip package")

        except Exception as e:
            self.logger.error(f"Error getting clipboard content: {e}")
            raise ActionError(f"Failed to get clipboard content: {e}")

    async def _set_clipboard(self, params: Dict[str, Any]) -> bool:
        """
        Set the clipboard content.

        Args:
            params: Action parameters
                text: The text to set as the clipboard content

        Returns:
            True if the clipboard was set successfully, False otherwise
        """
        # Get parameters
        text = params.get("text")

        # Validate parameters
        if text is None:
            raise ActionError("Missing required parameter: text")

        try:
            # Use pyperclip or equivalent to set clipboard content
            try:
                import pyperclip

                # Execute in a thread to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: pyperclip.copy(text))

                return True

            except ImportError:
                raise ActionError("Clipboard access requires the pyperclip package")

        except Exception as e:
            self.logger.error(f"Error setting clipboard content: {e}")
            return False

    async def _take_screenshot(self, params: Dict[str, Any]) -> Optional[str]:
        """
        Take a screenshot.

        Args:
            params: Action parameters
                output_path: The path to save the screenshot (optional)
                region: The region to capture (optional)

        Returns:
            The path to the saved screenshot or None if the screenshot failed
        """
        try:
            # Use pyautogui or equivalent to take a screenshot
            try:
                import pyautogui
                from datetime import datetime

                # Get parameters
                output_path = params.get("output_path")
                region = params.get("region")  # (left, top, width, height)

                # If no output path is provided, create one
                if output_path is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_path = os.path.join(
                        os.path.expanduser("~/Pictures"), f"screenshot_{timestamp}.png"
                    )

                # Take the screenshot
                loop = asyncio.get_event_loop()
                if region:
                    screenshot = await loop.run_in_executor(
                        None, lambda: pyautogui.screenshot(region=region)
                    )
                else:
                    screenshot = await loop.run_in_executor(
                        None, lambda: pyautogui.screenshot()
                    )

                # Save the screenshot
                await loop.run_in_executor(None, lambda: screenshot.save(output_path))

                return output_path

            except ImportError:
                raise ActionError(
                    "Screenshot functionality requires the pyautogui package"
                )

        except Exception as e:
            self.logger.error(f"Error taking screenshot: {e}")
            return None
