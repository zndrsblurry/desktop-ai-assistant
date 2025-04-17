"""
Keyboard Input Provider (Global Listener)

Listens for global keyboard events system-wide using pynput to detect
hotkeys, such as the emergency stop key or custom shortcuts.
"""

import asyncio
import logging
import threading
from typing import Optional, Dict, Any, Set

# Use try-except for robustness
try:
    from pynput import keyboard

    PYNPUT_AVAILABLE = True
except ImportError:
    logging.critical(
        "pynput not found. Global keyboard listener disabled. Install with: pip install pynput"
    )
    keyboard = None  # Define for type hints
    PYNPUT_AVAILABLE = False

from ai_desktop_assistant.core.events import EventBus, Events
from ai_desktop_assistant.interfaces.input_provider import InputProvider
from ai_desktop_assistant.core.config import AppConfig
from ai_desktop_assistant.core.exceptions import InitializationError
from ai_desktop_assistant.utils.logging import get_logger

# Define Key type alias for clarity
PynputKey = Any  # Represents keyboard.Key or keyboard.KeyCode

# Mapping from string names to pynput keys (expand as needed)
# Reuse map from keyboard_executor? Maybe centralize in utils? For now, redefine.
if PYNPUT_AVAILABLE:
    _KEY_MAP_LOWER = {
        # Special keys from keyboard.Key enum
        "esc": keyboard.Key.esc,  # Changed from 'escape'
        "ctrl": keyboard.Key.ctrl,
        "alt": keyboard.Key.alt,
        "shift": keyboard.Key.shift,
        "enter": keyboard.Key.enter,
        "space": keyboard.Key.space,
        "tab": keyboard.Key.tab,
        "backspace": keyboard.Key.backspace,
        "delete": keyboard.Key.delete,
        "insert": keyboard.Key.insert,
        "home": keyboard.Key.home,
        "end": keyboard.Key.end,
        "page_up": keyboard.Key.page_up,
        "page_down": keyboard.Key.page_down,
        "up": keyboard.Key.up,
        "down": keyboard.Key.down,
        "left": keyboard.Key.left,
        "right": keyboard.Key.right,
        # Common aliases
        "win": keyboard.Key.cmd,
        "windows": keyboard.Key.cmd,
        "super": keyboard.Key.cmd,
        "command": keyboard.Key.cmd,
        "option": keyboard.Key.alt,
        "altgr": keyboard.Key.alt_gr,
        "return": keyboard.Key.enter,
        "del": keyboard.Key.delete,
        "ins": keyboard.Key.insert,
        "pgup": keyboard.Key.page_up,
        "pgdn": keyboard.Key.page_down,
        "printscreen": keyboard.Key.print_screen,
        "scrolllock": keyboard.Key.scroll_lock,
        "numlock": keyboard.Key.num_lock,
        # Function keys
        **{f"f{i}": keyboard.Key[f"f{i}"] for i in range(1, 21)},
    }

    # Define modifier keys set
    _MODIFIER_KEYS = {
        keyboard.Key.ctrl,
        keyboard.Key.alt,
        keyboard.Key.shift,
        keyboard.Key.cmd,
        keyboard.Key.alt_gr,
        # Add left/right variants
        keyboard.Key.ctrl_l,
        keyboard.Key.ctrl_r,
        keyboard.Key.alt_l,
        keyboard.Key.alt_r,
        keyboard.Key.shift_l,
        keyboard.Key.shift_r,
        keyboard.Key.cmd_l,
        keyboard.Key.cmd_r,
    }
else:
    _KEY_MAP_LOWER = {}
    _MODIFIER_KEYS = set()


def parse_key_string(key_str: str) -> Optional[PynputKey]:
    """Parses a string (like 'esc', 'f1', 'a') into a pynput key object."""
    if not PYNPUT_AVAILABLE:
        return None

    key_str_lower = key_str.lower()

    # Check direct mapping first
    if key_str_lower in _KEY_MAP_LOWER:
        return _KEY_MAP_LOWER[key_str_lower]

    # Handle single characters
    elif len(key_str) == 1:
        return keyboard.KeyCode.from_char(key_str)  # Preserve original case

    # Log warning for unknown keys
    else:
        logging.warning(f"Could not parse key string: '{key_str}'")
        return None


class KeyboardListener(InputProvider):
    """
    Global keyboard listener using pynput in a separate thread.

    Detects configured hotkeys (especially emergency stop) and publishes events.
    Requires appropriate OS permissions (e.g., Input Monitoring on macOS).
    """

    def __init__(self, event_bus: EventBus, config: AppConfig):
        """
        Initialize the Keyboard Listener.

        Args:
            event_bus: Application event bus.
            config: Application configuration for hotkey settings.
        """
        self.logger = get_logger("input.keyboard")
        if not PYNPUT_AVAILABLE:
            raise InitializationError(
                "KeyboardListener cannot be initialized: pynput library not found."
            )

        self.event_bus = event_bus
        self.config = config

        self._listener_thread: Optional[threading.Thread] = None
        self._pynput_listener: Optional[keyboard.Listener] = None
        self._active: bool = False
        self._stop_requested = threading.Event()  # Thread-safe event for stopping

        # State tracked by the listener thread
        self._current_modifiers: Set[PynputKey] = set()
        self._lock = (
            threading.Lock()
        )  # Lock for accessing shared state (_current_modifiers)

        # Configured keys
        self._emergency_stop_key: Optional[PynputKey] = None
        self._parse_config()  # Parse keys from config

        # Get main event loop for publishing events from thread
        try:
            self._main_loop = asyncio.get_running_loop()
        except RuntimeError:
            self.logger.error(
                "KeyboardListener initialized outside of a running asyncio event loop. Event publishing might fail."
            )
            self._main_loop = None  # Need to get it later or handle differently

        self.logger.info("KeyboardListener initialized.")

    def _parse_config(self):
        """Parse hotkey configurations."""
        # Check if config is the full AppConfig object or just the system config
        if hasattr(self.config, "system"):
            # If it's the full config object
            stop_key_str = (
                self.config.system.get("emergency_stop_key")
                if isinstance(self.config.system, dict)
                else self.config.system.emergency_stop_key
            )
        else:
            # If it's just the system config dictionary
            stop_key_str = self.config.get("emergency_stop_key")

        # Default to "esc" if not found
        stop_key_str = stop_key_str or "esc"

        self._emergency_stop_key = parse_key_string(stop_key_str)
        if not self._emergency_stop_key:
            self.logger.error(f"Failed to parse emergency stop key: {stop_key_str}")

    async def start(self) -> None:
        """Start the keyboard listener thread."""
        if not PYNPUT_AVAILABLE:
            self.logger.error("Cannot start keyboard listener: pynput not available.")
            return
        if self._listener_thread and self._listener_thread.is_alive():
            self.logger.warning("Keyboard listener already running.")
            return

        # Get loop reference if not already set
        if not self._main_loop:
            try:
                self._main_loop = asyncio.get_running_loop()
            except RuntimeError:
                self.logger.critical(
                    "Cannot start KeyboardListener: No running asyncio event loop found."
                )
                raise InitializationError(
                    "KeyboardListener needs a running asyncio loop."
                )

        self.logger.info("Starting global keyboard listener thread...")
        self._stop_requested.clear()
        self._active = True

        self._listener_thread = threading.Thread(
            target=self._run_listener_thread, daemon=True, name="PynputListenerThread"
        )
        self._listener_thread.start()
        self.logger.info("Keyboard listener thread started.")

    async def stop(self) -> None:
        """Stop the keyboard listener thread."""
        if not self._listener_thread or not self._listener_thread.is_alive():
            self.logger.info("Keyboard listener already stopped or never started.")
            return

        self.logger.info("Stopping global keyboard listener thread...")
        self._active = False
        self._stop_requested.set()  # Signal thread loop to stop

        if self._pynput_listener:
            self.logger.debug("Requesting pynput listener stop...")
            # This should interrupt the listener's internal join/wait
            self._pynput_listener.stop()

        # Wait for the thread to finish
        self.logger.debug("Waiting for listener thread to join...")
        await asyncio.to_thread(
            self._listener_thread.join, timeout=2.0
        )  # Use asyncio.to_thread

        if self._listener_thread.is_alive():
            self.logger.warning(
                "Keyboard listener thread did not exit gracefully after 2 seconds."
            )
        else:
            self.logger.info("Keyboard listener thread joined.")

        self._listener_thread = None
        self._pynput_listener = None
        self.logger.info("Keyboard listener stopped.")

    def _run_listener_thread(self) -> None:
        """Target function for the listener thread."""
        self.logger.debug("Keyboard listener thread started execution.")
        try:
            # Create and start the listener within the thread
            with keyboard.Listener(
                on_press=self._on_press_threadsafe,
                on_release=self._on_release_threadsafe,
            ) as listener:
                self._pynput_listener = listener  # Store reference for stopping
                self.logger.info("pynput listener running...")
                # Wait until stop() is called externally or listener stops itself
                listener.join()

        except Exception as e:
            # Catch potential errors during listener setup or runtime
            # Common issues: OS permissions (Input Monitoring on macOS, access on Linux), display server issues
            self.logger.critical(
                f"FATAL Error in keyboard listener thread: {e}", exc_info=True
            )
            self._active = False
            # Publish error event (needs careful handling from thread)
            self._publish_event_threadsafe(
                Events.ERROR,
                {
                    "message": f"Keyboard listener failed: {e}",
                    "type": "input.keyboard",
                    "error": str(e),
                },
            )
        finally:
            self._pynput_listener = None  # Clear reference
            self.logger.info("Keyboard listener thread finished execution.")

    def _publish_event_threadsafe(self, event_name: str, data: Dict[str, Any]):
        """Safely schedules event publishing on the main asyncio loop."""
        if self._main_loop and self._main_loop.is_running():
            # Schedule the publish coroutine on the main loop
            asyncio.run_coroutine_threadsafe(
                self.event_bus.publish(event_name, data), self._main_loop
            )
            # Optional: Get future and check result/errors, but usually fire-and-forget
        else:
            self.logger.error(
                f"Cannot publish event '{event_name}' from keyboard thread: Main event loop not available or not running."
            )

    def _on_press_threadsafe(self, key: PynputKey) -> Optional[bool]:
        """Thread-safe callback for key press events."""
        if not self._active or self._stop_requested.is_set():
            return False  # Stop listener if inactive or stop requested

        # --- Update Modifier State (Thread-Safe) ---
        is_modifier = key in _MODIFIER_KEYS
        if is_modifier:
            with self._lock:
                self._current_modifiers.add(key)
            # self.logger.debug(f"Modifiers: {self._current_modifiers}")

        # --- Check Hotkeys ---
        try:
            # Check Emergency Stop
            if self._emergency_stop_key and key == self._emergency_stop_key:
                # Check if modifiers are required for stop key (e.g., Ctrl+Esc) - currently only checks key
                # with self._lock:
                #     required_mods_pressed = True # Add logic here if needed
                # if required_mods_pressed:
                self.logger.warning(f"Emergency stop key pressed: {key}")
                self._publish_event_threadsafe(
                    Events.SHUTDOWN_REQUESTED, {"source": "keyboard_emergency_stop"}
                )
                # Optionally return False here to stop listener immediately after Esc press

            # Check other configured hotkeys here
            # Example: Toggle listening hotkey
            # toggle_key_str = self.config.system.hotkey_toggle_listening
            # if toggle_key_str:
            #     # Parse toggle_key_str into key and required modifiers
            #     # If key matches and required modifiers in self._current_modifiers:
            #     #     self._publish_event_threadsafe(Events.VOICE_INPUT_TOGGLE, {"source": "hotkey"})
            #     pass

            # Debug logging (optional)
            # key_repr = getattr(key, 'char', None) or str(key)
            # self.logger.debug(f"Key Pressed: {key_repr}")

        except Exception as e:
            self.logger.error(
                f"Error processing key press '{key}' in thread: {e}", exc_info=False
            )

        return None  # Continue listening

    def _on_release_threadsafe(self, key: PynputKey) -> Optional[bool]:
        """Thread-safe callback for key release events."""
        if not self._active or self._stop_requested.is_set():
            return False  # Stop listener

        # --- Update Modifier State (Thread-Safe) ---
        if key in _MODIFIER_KEYS:
            with self._lock:
                self._current_modifiers.discard(
                    key
                )  # Use discard, ignore if not present
            # self.logger.debug(f"Modifiers: {self._current_modifiers}")

        # Debug logging (optional)
        # key_repr = getattr(key, 'char', None) or str(key)
        # self.logger.debug(f"Key Released: {key_repr}")

        # Check stop again in case it was set during press handling
        if self._stop_requested.is_set():
            return False

        return None  # Continue listening

    # --- InputProvider Interface Implementation ---

    @property
    def is_active(self) -> bool:
        """Check if the keyboard listener thread is active."""
        return (
            self._active
            and self._listener_thread is not None
            and self._listener_thread.is_alive()
        )

    async def set_active(self, active: bool) -> None:
        """Enable or disable the keyboard listener thread."""
        if active and not self.is_active:
            await self.start()
        elif not active and self.is_active:
            await self.stop()

    def get_capabilities(self) -> Dict[str, bool]:
        """Return the capabilities."""
        return {
            "global_hotkeys": PYNPUT_AVAILABLE,
            "emergency_stop": PYNPUT_AVAILABLE and bool(self._emergency_stop_key),
        }

    @property
    def input_type(self) -> str:
        """Return the input type."""
        return "keyboard_global"

    async def process_config(
        self, config_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Re-parse hotkey configurations if config changes."""
        # If config object itself is updated elsewhere, just re-parse
        self.logger.info(
            "Processing potential configuration changes for KeyboardListener."
        )
        self._parse_config()  # Re-read keys from self.config
