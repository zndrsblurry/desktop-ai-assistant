"""
Security Utilities

Provides helper functions related to security, such as data sanitization,
permission checks (if applicable), and potentially handling sensitive data.

Note: Security is hard. These utilities are likely insufficient for truly
robust security and should be reviewed and potentially replaced with
dedicated security libraries or practices depending on the application's
exposure and requirements.
"""

import logging
import re
import os

logger = logging.getLogger(__name__)

# Define potentially dangerous characters for filenames or paths
# This list might need adjustment based on the target OS and context
FILENAME_DANGEROUS_CHARS = r'[<>:"/\\|?*\x00-\x1f]'
# Slightly more permissive for paths, allowing separators, but still risky
PATH_DANGEROUS_CHARS = r'[<>:"|?*\x00-\x1f]'


def sanitize_filename(filename: str, replacement: str = "_") -> str:
    """
    Removes or replaces potentially dangerous characters from a filename.

    Args:
        filename: The original filename string.
        replacement: The character to replace dangerous characters with.

    Returns:
        A sanitized filename string.
    """
    if not isinstance(filename, str):
        logger.warning(f"sanitize_filename received non-string input: {type(filename)}")
        return ""  # Return empty string for non-strings

    # Replace dangerous characters
    sanitized = re.sub(FILENAME_DANGEROUS_CHARS, replacement, filename)

    # Optional: Collapse multiple replacements
    sanitized = re.sub(f"{re.escape(replacement)}+", replacement, sanitized)

    # Optional: Remove leading/trailing replacements/whitespace
    sanitized = sanitized.strip(replacement + " \t\n\r")

    # Optional: Limit length
    # MAX_FILENAME_LENGTH = 200
    # sanitized = sanitized[:MAX_FILENAME_LENGTH]

    if sanitized != filename:
        logger.debug(f"Sanitized filename: '{filename}' -> '{sanitized}'")

    return sanitized


def sanitize_path_component(component: str, replacement: str = "_") -> str:
    """
    Sanitizes a single component of a path (e.g., a directory or file name).
    More restrictive than sanitize_filename, typically used when constructing paths.
    """
    # Use the same logic as sanitize_filename for individual components
    return sanitize_filename(component, replacement)


def check_permissions(resource_path: str, permission_type: str = "read") -> bool:
    """
    Checks if the current process has specific permissions for a file/directory.
    NOTE: This is a basic check and might not be reliable across all platforms
    or for complex permission scenarios (ACLs, etc.).

    Args:
        resource_path: The path to the file or directory.
        permission_type: 'read', 'write', or 'execute'.

    Returns:
        True if the permission likely exists, False otherwise.
    """
    logger.debug(f"Checking '{permission_type}' permission for: {resource_path}")
    try:
        if not os.path.exists(resource_path):
            logger.warning(
                f"Permission check failed: Path does not exist: {resource_path}"
            )
            return False  # Cannot have permissions for non-existent path

        permission_map = {
            "read": os.R_OK,
            "write": os.W_OK,
            "execute": os.X_OK,
        }

        mode = permission_map.get(permission_type.lower())
        if mode is None:
            logger.error(f"Invalid permission type specified: {permission_type}")
            return False

        has_permission = os.access(resource_path, mode)
        logger.debug(
            f"Permission check result for '{permission_type}' on '{resource_path}': {has_permission}"
        )
        return has_permission

    except Exception as e:
        logger.error(f"Error checking permissions for '{resource_path}': {e}")
        return False  # Assume no permission on error


def is_sandboxed() -> bool:
    """
    Attempts to detect if the application is running in a known sandbox.
    Detection is heuristic and not guaranteed to be accurate.

    Returns:
        True if a known sandbox environment is detected, False otherwise.
    """
    # Check for common sandbox environment variables or file paths
    # Examples (add more based on specific sandboxes like Docker, Flatpak, Snap):

    # Docker check
    if os.path.exists("/.dockerenv"):
        logger.info("Detected Docker sandbox environment.")
        return True

    # Flatpak check
    if "FLATPAK_ID" in os.environ or "/app/bin" in os.environ.get("PATH", ""):
        logger.info("Detected Flatpak sandbox environment.")
        return True

    # Snap check
    if "SNAP" in os.environ and "SNAP_NAME" in os.environ:
        logger.info("Detected Snap sandbox environment.")
        return True

    # Add checks for other sandboxes if relevant

    return False


# Add more security-related functions as needed, e.g., for input validation,
# secure temporary file creation, checking for restricted operations before
# they are attempted by executors, etc.
