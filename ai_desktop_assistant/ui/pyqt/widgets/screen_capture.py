"""
Screen capture thread for capturing desktop screenshots.
"""

import time
import logging
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker

logger = logging.getLogger(__name__)


class ScreenCaptureThread(QThread):
    """Thread for capturing screenshots and emitting them as signals."""

    update_frame = pyqtSignal(np.ndarray)

    def __init__(self, monitor_num=1, interval=1.0):
        """
        Initialize screen capture thread.

        Args:
            monitor_num: Index of monitor to capture (0 for all monitors)
            interval: Capture interval in seconds
        """
        super().__init__()
        self.monitor_num = monitor_num
        self.interval = max(0.1, interval)  # Ensure minimum interval
        self.running = False
        self.paused = False
        self._mutex = QMutex()  # For thread-safe access to properties
        self._sct = None
        self._monitors = []

    def run(self):
        """Main thread loop."""
        try:
            # Import mss here to avoid startup import issues
            import mss

            self.running = True
            self._sct = mss.mss()
            self._refresh_monitors()

            logger.info(
                f"Screen capture thread started (Monitor: {self.monitor_num}, Interval: {self.interval}s)"
            )

            while self.running:
                if not self.paused:
                    try:
                        with QMutexLocker(self._mutex):
                            current_monitor_num = self.monitor_num
                            if 0 <= current_monitor_num < len(self._monitors):
                                monitor = self._monitors[current_monitor_num]
                            else:
                                # Invalid monitor index, try refreshing
                                logger.warning(
                                    f"Invalid monitor index: {current_monitor_num}, refreshing monitors"
                                )
                                self._refresh_monitors()
                                # Try to use monitor 1, then fall back to 0 if needed
                                current_monitor_num = (
                                    1 if 1 < len(self._monitors) else 0
                                )
                                self.monitor_num = current_monitor_num
                                if current_monitor_num < len(self._monitors):
                                    monitor = self._monitors[current_monitor_num]
                                    logger.info(
                                        f"Switched to monitor {current_monitor_num}"
                                    )
                                else:
                                    logger.error(
                                        "No valid monitors found after refresh"
                                    )
                                    time.sleep(2.0)
                                    continue

                        # Capture screen
                        screenshot = self._sct.grab(monitor)
                        frame = np.array(screenshot)
                        # Convert from BGRA to RGB
                        import cv2

                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)

                        # Emit frame
                        self.update_frame.emit(frame_rgb)

                    except Exception as e:
                        logger.error(f"Screen capture error: {str(e)}")
                        time.sleep(1.0)  # Wait a bit longer after error

                # Sleep based on interval
                time.sleep(self.interval)

            # Clean up
            if self._sct:
                self._sct.close()
            logger.info("Screen capture thread finished")

        except ImportError:
            logger.error("Failed to import mss module, screen capture disabled")
            self.running = False

    def _refresh_monitors(self):
        """Refresh the list of available monitors."""
        with QMutexLocker(self._mutex):
            if self._sct:
                self._monitors = self._sct.monitors
            else:
                self._monitors = []

    def stop(self):
        """Stop the capture thread."""
        logger.info("Stopping screen capture thread")
        self.running = False
        self.wait(2000)  # Wait up to 2 seconds
        if self.isRunning():
            logger.warning("Screen capture thread did not terminate gracefully")
            self.terminate()

    def pause(self):
        """Pause screen capturing."""
        with QMutexLocker(self._mutex):
            self.paused = True

    def resume(self):
        """Resume screen capturing."""
        with QMutexLocker(self._mutex):
            self.paused = False

    def set_monitor(self, monitor_num):
        """Change the monitor being captured."""
        with QMutexLocker(self._mutex):
            self.monitor_num = monitor_num

    def set_interval(self, interval):
        """Change the capture interval."""
        with QMutexLocker(self._mutex):
            self.interval = max(0.1, interval)  # Ensure reasonable minimum
