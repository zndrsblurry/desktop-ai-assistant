"""
Telemetry Service (Optional)

Collects and sends anonymized usage data and error reports if enabled by the user.
Helps improve the application by providing insights into usage patterns and common issues.
"""

import asyncio
import platform
import uuid
import time
from typing import Dict, Any, Optional, Deque
from collections import deque
import hashlib  # For anonymizing potentially sensitive data

# Async HTTP Client
try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    aiohttp = None  # Mark as unavailable
    AIOHTTP_AVAILABLE = False

# Application Info & Core Components
from ai_desktop_assistant import __version__
from ai_desktop_assistant.core.config import AppConfig
from ai_desktop_assistant.core.events import EventBus, Events
from ai_desktop_assistant.utils.logging import get_logger

# Constants
DEFAULT_TELEMETRY_ENDPOINT = (
    "https://your-telemetry-endpoint.example.com/v1/track"  # REPLACE THIS
)
BATCH_SIZE = 10  # Send events in batches
BATCH_INTERVAL = 60.0  # Send batch every 60 seconds, or when batch size is reached
MAX_QUEUE_SIZE = 1000  # Limit memory usage if endpoint is unavailable


class TelemetryService:
    """
    Optional service for collecting and sending anonymized telemetry data.

    Subscribes to relevant application events and periodically sends batched,
    anonymized data to a configured endpoint. Respects user's choice via configuration.
    """

    def __init__(self, config: AppConfig, event_bus: EventBus):
        """Initialize the Telemetry Service."""
        self.logger = get_logger("services.telemetry")
        self.config = config
        self.event_bus = event_bus

        # Determine if enabled based on config and library availability
        self.is_enabled = config.telemetry.enabled and AIOHTTP_AVAILABLE
        if config.telemetry.enabled and not AIOHTTP_AVAILABLE:
            self.logger.warning(
                "Telemetry configured enabled, but 'aiohttp' not installed. Disabling telemetry."
            )
        elif not config.telemetry.enabled:
            self.logger.info("Telemetry is disabled by configuration.")
        else:
            self.logger.info("Telemetry Service initialized (enabled).")

        self._endpoint = config.telemetry.endpoint or DEFAULT_TELEMETRY_ENDPOINT
        if self._endpoint == DEFAULT_TELEMETRY_ENDPOINT and self.is_enabled:
            self.logger.warning(
                f"Telemetry using default placeholder endpoint: {DEFAULT_TELEMETRY_ENDPOINT}. Data will not be sent correctly."
            )
            # Consider disabling if endpoint is still the placeholder
            # self.is_enabled = False

        self._session: Optional[aiohttp.ClientSession] = None
        self._device_id: Optional[str] = None  # Anonymous, persistent device ID
        self._session_id: str = str(uuid.uuid4())  # Unique ID for this application run
        self._event_queue: Deque[Dict[str, Any]] = deque(maxlen=MAX_QUEUE_SIZE)
        self._send_task: Optional[asyncio.Task] = None
        self._stop_requested = asyncio.Event()

    async def initialize(self) -> bool:
        """Initialize device ID and HTTP client session."""
        if not self.is_enabled:
            return True  # Nothing to initialize

        self._get_or_create_device_id()
        if not self._device_id:
            self.logger.error("Failed to obtain device ID. Disabling telemetry.")
            self.is_enabled = False
            return False

        if not self._session:
            try:
                # Use longer total timeout, but shorter connect timeout
                timeout = aiohttp.ClientTimeout(total=30, connect=5)
                # Consider adding headers if needed by the endpoint (e.g., API key for telemetry service)
                headers = {"Content-Type": "application/json"}
                self._session = aiohttp.ClientSession(timeout=timeout, headers=headers)
                self.logger.info(
                    f"Telemetry HTTP session initialized for endpoint: {self._endpoint}"
                )
                return True
            except Exception as e:
                self.logger.error(f"Failed to initialize telemetry HTTP session: {e}")
                self.is_enabled = False
                return False
        return True

    def _get_or_create_device_id(self):
        """Load or generate a unique, anonymous device ID stored locally."""
        id_file = self.config.CONFIG_DIR / ".ai_assistant_id"  # Use a generic name
        try:
            if id_file.exists():
                device_id_str = id_file.read_text().strip()
                # Validate format (basic UUID check)
                uuid.UUID(device_id_str)
                self._device_id = device_id_str
                self.logger.debug(
                    f"Loaded existing device ID: ...{self._device_id[-12:]}"
                )
            else:
                self._device_id = str(uuid.uuid4())
                id_file.parent.mkdir(parents=True, exist_ok=True)
                id_file.write_text(self._device_id)
                self.logger.info(f"Generated new device ID: ...{self._device_id[-12:]}")
        except (ValueError, OSError, Exception) as e:
            self.logger.error(
                f"Failed to load/create telemetry device ID from {id_file}: {e}. Generating ephemeral ID."
            )
            # Fallback to ephemeral ID for this session only if file I/O fails
            self._device_id = str(uuid.uuid4())

    async def start(self) -> None:
        """Start the background task for sending batched events."""
        if not self.is_enabled:
            return
        if not await self.initialize():  # Ensure client is ready
            self.logger.error("Telemetry disabled due to initialization failure.")
            self.is_enabled = False
            return

        self.logger.info("Starting Telemetry Service background tasks and listeners.")
        self._stop_requested.clear()

        # Subscribe to events
        await self._subscribe_events()

        # Start the background sending task
        if self._send_task and not self._send_task.done():
            self.logger.warning("Telemetry send task already running.")
        else:
            self._send_task = asyncio.create_task(
                self._batch_sender_loop(), name="TelemetryBatchSender"
            )

        # Track session start
        await self.track_event("session_start", {"start_time": time.time()})

    async def stop(self) -> None:
        """Stop listeners, send any remaining events, and close session."""
        if (
            not self.is_enabled and not self._send_task
        ):  # Check task too in case it was started then disabled
            return

        self.logger.info("Stopping Telemetry Service...")
        self._stop_requested.set()  # Signal sender loop to stop

        # Unsubscribe from events
        await self._unsubscribe_events()

        # Wait for the sender task to finish sending remaining events
        if self._send_task and not self._send_task.done():
            self.logger.debug("Waiting for telemetry sender task to finish...")
            try:
                # Give it some time to send the last batch
                await asyncio.wait_for(self._send_task, timeout=BATCH_INTERVAL / 2)
            except asyncio.TimeoutError:
                self.logger.warning(
                    "Telemetry sender task timed out during stop. Cancelling."
                )
                self._send_task.cancel()
            except Exception as e:
                self.logger.error(f"Error waiting for telemetry sender task: {e}")
                if not self._send_task.done():
                    self._send_task.cancel()
            # Final await after potential cancellation
            try:
                await self._send_task
            except asyncio.CancelledError:
                pass
        self._send_task = None

        # Close HTTP session
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
            self.logger.info("Telemetry HTTP session closed.")
        self.logger.info("Telemetry Service stopped.")

    async def _subscribe_events(self):
        """Subscribe to events for telemetry tracking."""
        self.logger.debug("Subscribing to telemetry events...")
        # --- Choose events carefully to balance insight and privacy ---
        await self.event_bus.subscribe(
            Events.STARTUP_COMPLETE,
            lambda d: asyncio.create_task(self.track_event("app_startup_complete")),
        )
        await self.event_bus.subscribe(
            Events.APP_EXITING,
            lambda d: asyncio.create_task(self.track_event("app_shutdown")),
        )
        await self.event_bus.subscribe(
            Events.ERROR, lambda d: asyncio.create_task(self._handle_error(d))
        )
        await self.event_bus.subscribe(
            Events.ACTION_COMPLETED,
            lambda d: asyncio.create_task(self._handle_action(d, True)),
        )
        await self.event_bus.subscribe(
            Events.ACTION_FAILED,
            lambda d: asyncio.create_task(self._handle_action(d, False)),
        )
        # Track feature usage (examples)
        await self.event_bus.subscribe(
            Events.VOICE_INPUT_START,
            lambda d: asyncio.create_task(
                self.track_event("feature_use", {"feature": "voice_input"})
            ),
        )
        await self.event_bus.subscribe(
            Events.RESET_CONVERSATION,
            lambda d: asyncio.create_task(
                self.track_event("feature_use", {"feature": "reset_conversation"})
            ),
        )
        # Add more event subscriptions as needed

    async def _unsubscribe_events(self):
        """Unsubscribe from all telemetry events."""
        self.logger.debug("Unsubscribing from telemetry events...")
        # Use try/except block if specific handlers are stored and need removal
        # For lambda functions, this is harder. If EventBus uses weakrefs, may not be needed.
        # If not using weakrefs, store handler references during subscribe to unsubscribe here.

    async def track_event(
        self, event_name: str, properties: Optional[Dict[str, Any]] = None
    ):
        """
        Adds an event to the queue for batch sending.

        Args:
            event_name: Name of the event.
            properties: Dictionary of event properties (must be JSON serializable).
        """
        if not self.is_enabled:
            return

        # Prepare payload structure expected by the batch sender
        event_data = {
            "event": event_name,
            "properties": {
                "distinct_id": self._device_id,  # Anonymous user ID
                "session_id": self._session_id,
                "$insert_id": str(uuid.uuid4()),  # Unique ID for this specific event
                "time": int(time.time()),  # Timestamp in seconds
                # Standard properties added automatically
                "app_version": __version__,
                "os_name": platform.system(),
                # Add other standard context if desired (e.g., os_version, python_version)
                **(properties or {}),  # Merge custom properties
            },
        }

        # Basic check for PII (very naive, improve significantly if needed)
        if properties:
            for key, value in properties.items():
                if isinstance(value, str) and len(value) > 50:  # Check long strings
                    # Example: Hash potentially sensitive long strings
                    if (
                        "path" in key
                        or "query" in key
                        or "message" in key
                        or "code" in key
                    ):
                        event_data["properties"][
                            key
                        ] = f"hashed:{hashlib.sha256(value.encode()).hexdigest()[:16]}"

        if len(self._event_queue) < MAX_QUEUE_SIZE:
            self._event_queue.append(event_data)
            # self.logger.debug(f"Queued telemetry event: {event_name}")
        else:
            self.logger.warning("Telemetry queue full. Discarding event.")

    async def _batch_sender_loop(self):
        """Periodically sends queued events in batches."""
        self.logger.info("Telemetry batch sender loop started.")
        while not self._stop_requested.is_set():
            try:
                await asyncio.sleep(BATCH_INTERVAL)  # Wait for the interval

                if self._event_queue:  # Check if there's anything to send
                    await self._send_batch()

            except asyncio.CancelledError:
                self.logger.info("Telemetry batch sender loop cancelled.")
                break
            except Exception as e:
                self.logger.error(
                    f"Error in telemetry batch sender loop: {e}", exc_info=True
                )
                # Avoid tight loop on error, wait before continuing
                await asyncio.sleep(BATCH_INTERVAL * 2)

        # Send any final remaining events before exiting
        self.logger.info("Telemetry loop stopping. Sending final batch...")
        if self._event_queue:
            await self._send_batch()
        self.logger.info("Telemetry batch sender loop finished.")

    async def _send_batch(self):
        """Sends the current queue content as a batch."""
        if not self.is_enabled or not self._session or not self._event_queue:
            return

        # Drain the queue up to BATCH_SIZE
        events_to_send = []
        while self._event_queue and len(events_to_send) < BATCH_SIZE:
            events_to_send.append(self._event_queue.popleft())

        if not events_to_send:
            return

        self.logger.debug(f"Sending telemetry batch of {len(events_to_send)} events...")
        # Endpoint might expect a specific batch format (e.g., list of events in a JSON body)
        # Adjust payload format based on your telemetry backend (e.g., PostHog, Mixpanel)
        batch_payload = events_to_send  # Simple list of events for now

        try:
            # Send data asynchronously
            async with self._session.post(
                self._endpoint, json=batch_payload
            ) as response:
                if response.status >= 300:
                    response_text = await response.text()
                    self.logger.warning(
                        f"Telemetry batch request failed: Status {response.status}, Response: {response_text[:200]}"
                    )
                    # Handle failure: Re-queue events? Discard? Log?
                    # For simplicity, we discard failed batches here. Robust implementation might re-queue.
                else:
                    self.logger.debug(
                        f"Telemetry batch sent successfully (Status {response.status})."
                    )
        except aiohttp.ClientConnectionError as e:
            self.logger.warning(
                f"Failed to connect to telemetry endpoint {self._endpoint}: {e}. Events remain queued."
            )
            # Re-queue the events if connection failed? Be careful not to create infinite loop/memory issue.
            # Adding back to the left ensures order is maintained on retry.
            for event in reversed(events_to_send):
                self._event_queue.appendleft(event)
        except asyncio.TimeoutError:
            self.logger.warning(
                f"Telemetry request timed out for endpoint {self._endpoint}. Events remain queued."
            )
            for event in reversed(events_to_send):
                self._event_queue.appendleft(event)
        except Exception as e:
            self.logger.error(
                f"Unexpected error sending telemetry batch: {e}", exc_info=True
            )
            # Discard batch on unexpected error to prevent loops

    # --- Specific Event Handlers with Anonymization ---

    async def _handle_error(self, data: Dict[str, Any]) -> None:
        """Handle error events for telemetry."""
        props = {
            "error_type": data.get("type", "generic"),
            # Anonymize potentially sensitive info from error messages/details
            "error_message": str(data.get("message", "Unknown error"))[
                :500
            ],  # Limit length
            # "error_details": json.dumps(data.get("details", {})) # Careful with details
        }
        # Add specific details if safe (e.g., error class name)
        if data.get("error"):
            props["error_class"] = type(data["error"]).__name__

        await self.track_event("error_occurred", props)

    async def _handle_action(self, data: Dict[str, Any], success: bool) -> None:
        """Handle action completed/failed events."""
        action_id = data.get("action_id", "unknown")
        event_name = "action_completed" if success else "action_failed"
        props = {"action_id": action_id}
        # Avoid sending potentially sensitive parameters directly
        if "parameters" in data:
            # Track *which* parameters were used, not their values
            props["parameters_keys"] = list(data["parameters"].keys())
        if not success:
            props["error_message"] = str(data.get("error", "Unknown failure"))[:200]

        await self.track_event(event_name, props)
