# Location: ai_desktop_assistant/output/notifications.py
"""
Notifications Output Provider

This module implements the notifications output provider for system notifications.
"""

import logging
import os
import platform
from typing import Optional

from ai_desktop_assistant.core.events import EventBus, EventType
from ai_desktop_assistant.core.exceptions import OutputError
from ai_desktop_assistant.interfaces.output_provider import OutputProvider


class NotificationsOutputProvider(OutputProvider):
    """Implementation of the notifications output provider."""

    def __init__(self, event_bus: EventBus):
        """
        Initialize the notifications output provider.

        Args:
            event_bus: The application event bus
        """
        self.logger = logging.getLogger(__name__)
        self.event_bus = event_bus
        self.notifier = None

    async def initialize(self) -> None:
        """Initialize the notifications output provider."""
        self.logger.info("Initializing notifications output provider")

        try:
            # Initialize platform-specific notification system
            system = platform.system()

            if system == "Windows":
                from win10toast import ToastNotifier

                self.notifier = ToastNotifier()
            elif system == "Darwin":  # macOS
                # For macOS, we'll use the built-in osascript
                self.notifier = "MacOS"
            else:  # Linux and others
                try:
                    import notify2

                    notify2.init("AI Desktop Assistant")
                    self.notifier = notify2
                except ImportError:
                    self.logger.warning(
                        "notify2 not available. Using fallback notification method."
                    )
                    self.notifier = "Fallback"

            self.logger.info("Notifications output provider initialized")

        except Exception as e:
            self.logger.error(f"Error initializing notifications: {e}")
            self.logger.info("Continuing without notifications support")

    async def shutdown(self) -> None:
        """Shut down the notifications output provider."""
        self.logger.info("Shutting down notifications output provider")
        self.notifier = None
        self.logger.info("Notifications output provider shut down")

    async def send_notification(
        self, title: str, message: str, icon: Optional[str] = None
    ) -> None:
        """
        Send a system notification.

        Args:
            title: The notification title
            message: The notification message
            icon: Path to an icon file (optional)

        Raises:
            OutputError: If sending the notification fails
        """
        if not self.notifier:
            self.logger.warning("Notifications not available")
            return

        try:
            self.logger.debug(f"Sending notification: {title} - {message}")

            # Publish notification event
            self.event_bus.publish(
                EventType.OUTPUT_START, "notification", title, message
            )

            # Send notification using platform-specific method
            if isinstance(self.notifier, str):
                if self.notifier == "MacOS":
                    # Use osascript for macOS
                    os.system(
                        f'osascript -e \'display notification "{message}" with title "{title}"\''
                    )
                else:  # Fallback
                    # Just log the notification
                    self.logger.info(f"Notification: {title} - {message}")
            else:
                # Use the platform-specific notifier
                if platform.system() == "Windows":
                    self.notifier.show_toast(title, message, duration=5, icon_path=icon)
                else:  # Linux with notify2
                    notification = self.notifier.Notification(title, message)
                    if icon:
                        notification.set_icon_from_pixbuf(icon)
                    notification.show()

            self.event_bus.publish(EventType.OUTPUT_END, "notification")

        except Exception as e:
            self.logger.error(f"Error sending notification: {e}")
            raise OutputError(f"Failed to send notification: {e}")
