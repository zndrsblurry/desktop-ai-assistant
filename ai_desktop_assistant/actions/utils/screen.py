"""
Screen Utilities

Provides functions for interacting with the screen, such as capturing images,
getting monitor information, and basic window identification.
"""

import logging
import platform
from typing import Optional, Dict, List, Any

# Screen capture
try:
    import mss
    import numpy as np

    MSS_AVAILABLE = True
except ImportError:
    logging.warning(
        "mss or numpy not found. Screen capture functionality will be limited."
    )
    mss = None
    np = None
    MSS_AVAILABLE = False

# Screen information (monitors)
try:
    import screeninfo

    SCREENINFO_AVAILABLE = True
except ImportError:
    logging.warning("screeninfo not found. Monitor information will be unavailable.")
    screeninfo = None
    SCREENINFO_AVAILABLE = False

# Window information (platform-specific)
IS_WINDOWS = platform.system() == "Windows"
IS_MACOS = platform.system() == "Darwin"
IS_LINUX = platform.system() == "Linux"

if IS_WINDOWS:
    try:
        import pygetwindow as gw

        PYGETWINDOW_AVAILABLE = True
    except ImportError:
        logging.warning(
            "pygetwindow not found. Window management features limited on Windows. Install with: pip install pygetwindow"
        )
        gw = None
        PYGETWINDOW_AVAILABLE = False
elif IS_MACOS:
    try:
        # Using AppKit via pyobjc requires more setup, or use pygetwindow if it works
        import AppKit  # Often available via system python or pyobjc

        APPKIT_AVAILABLE = True
    except ImportError:
        logging.warning(
            "AppKit (pyobjc) not found. Window management features limited on macOS."
        )
        AppKit = None
        APPKIT_AVAILABLE = False
    # Fallback check for pygetwindow on mac
    if not APPKIT_AVAILABLE:
        try:
            import pygetwindow as gw

            PYGETWINDOW_AVAILABLE = True
            logging.info("Using pygetwindow on macOS as AppKit fallback.")
        except ImportError:
            gw = None
            PYGETWINDOW_AVAILABLE = False
elif IS_LINUX:
    # pygetwindow often works on Linux with X11/Wayland backends installed
    try:
        import pygetwindow as gw

        PYGETWINDOW_AVAILABLE = True
    except ImportError:
        logging.warning(
            "pygetwindow not found. Window management features limited on Linux. Install with: pip install pygetwindow"
        )
        gw = None
        PYGETWINDOW_AVAILABLE = False
else:  # Other platforms
    PYGETWINDOW_AVAILABLE = False


logger = logging.getLogger(__name__)


def capture_screen_mss(
    monitor_id: int = 0, region: Optional[Dict[str, int]] = None
) -> Optional[np.ndarray]:
    """
    Captures the screen or a region using the MSS library.

    Args:
        monitor_id: The monitor number (0 for all, 1 for primary, etc.).
        region: A dictionary {'x': int, 'y': int, 'width': int, 'height': int}
                relative to the specified monitor (or primary if monitor_id=0).

    Returns:
        A NumPy array representing the captured image in BGRA format, or None on failure.
    """
    if not MSS_AVAILABLE:
        logger.error("MSS library is required for screen capture.")
        return None

    try:
        with mss.mss() as sct:
            monitors = sct.monitors
            if not monitors:
                logger.error("No monitors found by MSS.")
                return None

            if monitor_id >= len(monitors):
                logger.warning(
                    f"Invalid monitor_id {monitor_id}. Using primary monitor (1)."
                )
                monitor_id = 1  # Default to primary if invalid

            if monitor_id == 0 and len(monitors) > 1:
                # Use primary monitor as reference if region is given with monitor_id=0
                capture_monitor = monitors[1]
            elif monitor_id < len(monitors):
                capture_monitor = monitors[monitor_id]
            else:  # Fallback if only one monitor exists total
                capture_monitor = monitors[0]

            if region:
                # Adjust region relative to the chosen monitor's top-left
                capture_region = {
                    "top": capture_monitor["top"] + region["y"],
                    "left": capture_monitor["left"] + region["x"],
                    "width": region["width"],
                    "height": region["height"],
                    "mon": monitor_id,  # Inform mss which monitor geometry is used
                }
                # Basic bounds check
                if (
                    capture_region["left"] + capture_region["width"]
                    > capture_monitor["left"] + capture_monitor["width"]
                    or capture_region["top"] + capture_region["height"]
                    > capture_monitor["top"] + capture_monitor["height"]
                    or capture_region["width"] <= 0
                    or capture_region["height"] <= 0
                ):
                    logger.error(
                        f"Capture region {region} exceeds bounds of monitor {monitor_id}."
                    )
                    return None
            else:
                # Capture the whole selected monitor
                capture_region = capture_monitor

            logger.debug(f"Capturing region: {capture_region}")
            sct_img = sct.grab(capture_region)

            # Convert to NumPy array (BGRA format)
            img = np.array(sct_img)
            return img

    except Exception as e:
        logger.exception(f"Failed to capture screen: {e}")
        return None


def get_monitor_info() -> List[Dict[str, Any]]:
    """
    Gets information about connected monitors using screeninfo or mss.

    Returns:
        A list of dictionaries, each describing a monitor.
        Keys might include: 'x', 'y', 'width', 'height', 'name', 'is_primary'.
        Returns an empty list on failure.
    """
    monitors_info = []
    if SCREENINFO_AVAILABLE:
        try:
            monitors = screeninfo.get_monitors()
            for m in monitors:
                monitors_info.append(
                    {
                        "x": m.x,
                        "y": m.y,
                        "width": m.width,
                        "height": m.height,
                        "name": m.name,
                        "is_primary": m.is_primary,
                    }
                )
            logger.debug(
                f"Retrieved monitor info using screeninfo: {len(monitors_info)} monitors."
            )
            return monitors_info
        except Exception as e:
            logger.warning(f"screeninfo failed to get monitors: {e}. Trying mss.")

    # Fallback to MSS if screeninfo failed or wasn't available
    if MSS_AVAILABLE:
        try:
            with mss.mss() as sct:
                # mss monitors list: 0=all, 1=primary, 2=secondary...
                # We skip index 0 (all screens)
                for i, m in enumerate(sct.monitors[1:]):
                    monitors_info.append(
                        {
                            "x": m["left"],
                            "y": m["top"],
                            "width": m["width"],
                            "height": m["height"],
                            "name": f"Monitor {i + 1}",  # mss doesn't provide names
                            "is_primary": i == 0,  # Index 1 is primary
                        }
                    )
                logger.debug(
                    f"Retrieved monitor info using mss: {len(monitors_info)} monitors."
                )
                return monitors_info
        except Exception as e:
            logger.error(f"mss failed to get monitors: {e}")

    logger.error("Could not retrieve monitor information using available libraries.")
    return []


def find_window_by_title(
    title_substring: str, exact_match: bool = False
) -> Optional[Any]:
    """
    Finds a window based on a substring of its title (case-insensitive).

    Args:
        title_substring: The substring to search for in window titles.
        exact_match: If True, requires an exact title match.

    Returns:
        A window object (type depends on the backend library, e.g., pygetwindow),
        or None if no matching window is found or the library is unavailable.
    """
    if not PYGETWINDOW_AVAILABLE:
        logger.warning("Window finding requires pygetwindow library.")
        # Add platform-specific alternatives if needed (AppKit, Xlib)
        return None

    try:
        windows = gw.getAllWindows()
        title_lower = title_substring.lower()

        for window in windows:
            # Skip windows with empty titles or specific unwanted titles
            if not window.title or window.title.strip() == "":
                continue
            # Add filtering for background processes/invisible windows if possible

            window_title_lower = window.title.lower()

            if exact_match:
                if window_title_lower == title_lower:
                    logger.info(f"Found exact window match: '{window.title}'")
                    return window
            else:
                if title_lower in window_title_lower:
                    logger.info(f"Found window containing title: '{window.title}'")
                    return window

        logger.debug(
            f"No window found with title {'exactly' if exact_match else 'containing'} '{title_substring}'."
        )
        return None
    except Exception as e:
        logger.error(f"Error finding window by title '{title_substring}': {e}")
        return None


def get_active_window_title() -> Optional[str]:
    """
    Gets the title of the currently active/foreground window.

    Returns:
        The title string, or None if it cannot be determined or library unavailable.
    """
    if not PYGETWINDOW_AVAILABLE:
        logger.warning("Cannot get active window title without pygetwindow.")
        # Add platform-specific alternatives if needed
        return None

    try:
        active_window = gw.getActiveWindow()
        if active_window:
            # Ensure title is not None or empty before returning
            title = getattr(active_window, "title", None)
            return title if title else None
        else:
            logger.debug("No active window found by pygetwindow.")
            return None
    except Exception as e:
        # Sometimes getActiveWindow raises exceptions, e.g., on specific Linux setups
        logger.error(f"Error getting active window title: {e}")
        return None
