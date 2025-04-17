"""
Code Executor

Handles execution of code snippets (e.g., Python) provided by the AI.
This is a potentially DANGEROUS operation and requires strict sandboxing
and security measures.

NOTE: Implementing a truly safe code executor is complex and beyond the
scope of a simple implementation. This example provides a basic structure
but lacks robust sandboxing. Use with EXTREME caution or disable entirely
in production environments unless properly secured.
"""

import asyncio
import logging
import time
import sys
import os
from typing import Dict, Any, Optional, List, Tuple
import tempfile

# Sandboxing options (complex to implement correctly):
# - Docker containers
# - Dedicated low-privilege user accounts + restricted environments
# - WebAssembly runtimes (e.g., wasmtime)
# - Specialized sandboxing libraries (e.g., nsjail - Linux only)

from ai_desktop_assistant.interfaces.action_executor import ActionExecutorInterface
from ai_desktop_assistant.core.events import EventBus, Events
from ai_desktop_assistant.core.config import AppConfig
from ai_desktop_assistant.core.exceptions import (
    ActionExecutionError,
    ActionTimeoutError,
    RestrictedOperationError,
)

# Configuration for code execution
CODE_EXECUTION_TIMEOUT = 10.0  # Timeout in seconds
ENABLE_NETWORK_ACCESS = (
    False  # DANGEROUS: Should network access be allowed in the sandbox?
)
ALLOWED_IMPORTS = {
    "math",
    "random",
    "datetime",
    "time",
    "json",
    "re",
}  # Whitelist safe imports


class CodeExecutor(ActionExecutorInterface):
    """Executes code snippets provided by the AI in a restricted environment."""

    SUPPORTED_ACTIONS = ["execute_python_code"]

    def __init__(self, config: AppConfig, event_bus: EventBus):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.event_bus = event_bus
        self._current_action_task: Optional[asyncio.Task] = None
        self._executing_action_id: Optional[str] = None
        self.is_code_execution_enabled = getattr(
            config, "enable_code_execution", False
        )  # Default disabled

        if not self.is_code_execution_enabled:
            self.logger.warning(
                "Code Execution is DISABLED in configuration. CodeExecutor will reject requests."
            )

    async def initialize(self) -> bool:
        """Initialize the code executor."""
        self.logger.info("Code Executor Initialized.")
        if not self.is_code_execution_enabled:
            self.logger.warning("Code Execution remains disabled.")
        # Perform sandbox setup checks if applicable
        return True

    async def start(self) -> None:
        """Subscribe to relevant action events."""
        if not self.is_code_execution_enabled:
            return

        self.logger.info("Starting Code Executor.")
        for action_id in self.SUPPORTED_ACTIONS:
            await self.event_bus.subscribe(
                Events.ACTION_REQUESTED,
                lambda data, current_action_id=action_id: self._handle_action_request(
                    data, current_action_id
                ),
            )
        self.logger.info(
            f"Code Executor subscribed to events for: {self.SUPPORTED_ACTIONS}"
        )

    async def stop(self) -> None:
        """Unsubscribe and cancel ongoing actions."""
        if not self.is_code_execution_enabled:
            return
        self.logger.info("Stopping Code Executor.")
        # Unsubscribe logic
        await self.cancel_action()

    async def _handle_action_request(
        self, data: Dict[str, Any], expected_action_id: str
    ):
        """Handle incoming action requests if they match this executor."""
        request_action_id = data.get("action_id")
        if request_action_id == expected_action_id:
            if not self.is_code_execution_enabled:
                err = "Code execution is disabled by configuration."
                self.logger.error(err)
                await self._publish_result(
                    request_action_id,
                    data.get("parameters", {}),
                    success=False,
                    error=err,
                )
                return

            if self.is_busy:
                self.logger.warning(
                    f"CodeExecutor is busy. Ignoring request for {request_action_id}."
                )
                return

            parameters = data.get("parameters", {})
            self._executing_action_id = request_action_id
            self._current_action_task = asyncio.create_task(
                self.execute(request_action_id, parameters),
                name=f"Exec-Code-{request_action_id}",
            )
            self._current_action_task.add_done_callback(self._action_task_done)

    def _action_task_done(self, task: asyncio.Task):
        """Callback when an action task finishes."""
        try:
            exc = task.exception()
            if exc:
                self.logger.error(
                    f"Code execution task '{task.get_name()}' failed with exception: {exc}"
                )
        except asyncio.CancelledError:
            self.logger.info(f"Code execution task '{task.get_name()}' was cancelled.")
        finally:
            self._current_action_task = None
            self._executing_action_id = None
            self.logger.debug(f"Resetting busy state after task '{task.get_name()}'.")

    async def execute(
        self, action_id: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a specific code action."""
        if not self.is_code_execution_enabled:
            return {"success": False, "error": "Code execution is disabled."}

        self.logger.info(f"Executing code action: {action_id}")
        result = {"success": False, "error": "Action not implemented or failed."}

        try:
            is_valid, error_msg = self.validate_parameters(action_id, parameters)
            if not is_valid:
                raise ValueError(error_msg or "Invalid parameters")

            if action_id == "execute_python_code":
                result = await self._execute_python_code(parameters)
            else:
                result["error"] = f"Unsupported code action: {action_id}"

            await self._publish_result(action_id, parameters, **result)
            return result

        except (
            ActionTimeoutError,
            ActionExecutionError,
            ValueError,
            RestrictedOperationError,
        ) as e:
            self.logger.error(f"Error executing {action_id}: {e}")
            result = {"success": False, "error": str(e)}
            await self._publish_result(action_id, parameters, **result)
            return result
        except Exception as e:
            self.logger.exception(f"Unexpected error during {action_id}: {e}")
            result = {"success": False, "error": f"Unexpected error: {e}"}
            await self._publish_result(action_id, parameters, **result)
            return result

    async def cancel_action(self, action_id: Optional[str] = None) -> bool:
        """Cancel the currently running code execution."""
        # Requires terminating the subprocess or sandbox environment.
        if self._current_action_task and not self._current_action_task.done():
            if action_id is None or action_id == self._executing_action_id:
                self.logger.info(
                    f"Cancelling current code execution: {self._executing_action_id}"
                )
                # Attempt to terminate the subprocess if running
                # This needs access to the process object created in _execute_python_code
                # process = getattr(self._current_action_task, "process", None) # Needs attaching process to task
                # if process and process.poll() is None:
                #     try:
                #         process.terminate()
                #         await asyncio.sleep(0.1) # Give time to terminate
                #         if process.poll() is None:
                #             process.kill()
                #         self.logger.info("Terminated code execution subprocess.")
                #     except Exception as e:
                #         self.logger.error(f"Failed to terminate code execution process: {e}")

                self._current_action_task.cancel()
                await asyncio.sleep(0.05)
                return True
        self.logger.debug("No active code execution to cancel or action_id mismatch.")
        return False

    def get_supported_actions(self) -> List[Dict[str, Any]]:
        """Return descriptions of supported code actions."""
        return [
            {
                "action_id": "execute_python_code",
                "description": "Executes a snippet of Python code.",
                "parameters": {"code": "str"},
            },
        ]

    def validate_parameters(
        self, action_id: str, parameters: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate parameters for a given code action."""
        if action_id == "execute_python_code":
            if (
                "code" not in parameters
                or not isinstance(parameters["code"], str)
                or not parameters["code"].strip()
            ):
                return (
                    False,
                    "Missing, invalid, or empty 'code' parameter (string) for execute_python_code.",
                )
            # Add basic security checks here (e.g., disallow imports like 'os', 'subprocess')
            if self._contains_disallowed_patterns(parameters["code"]):
                return (
                    False,
                    "Code contains potentially unsafe patterns or disallowed imports.",
                )
        elif action_id not in self.SUPPORTED_ACTIONS:
            return False, f"Unsupported code action: {action_id}"

        return True, None

    def _contains_disallowed_patterns(self, code: str) -> bool:
        """Basic check for disallowed patterns (needs significant improvement for security)."""
        disallowed_imports = {
            "os",
            "subprocess",
            "sys",
            "shutil",
            "requests",
            "socket",
            "http",
            "urllib",
            "glob",
        }
        # Very basic check, easily bypassable
        for pattern in disallowed_imports:
            if f"import {pattern}" in code or f"from {pattern}" in code:
                self.logger.warning(
                    f"Disallowed import pattern '{pattern}' found in code."
                )
                return True
        # Add checks for file access, network access, etc.
        if "open(" in code:  # Very naive check
            self.logger.warning("Potential file access pattern 'open()' found.")
            # Return True # Decide if this should be blocked by default
        return False

    @property
    def is_busy(self) -> bool:
        """Check if the executor is currently busy."""
        return (
            self._current_action_task is not None
            and not self._current_action_task.done()
        )

    @property
    def current_action(self) -> Optional[str]:
        """Get the ID of the currently executing action."""
        return self._executing_action_id if self.is_busy else None

    @property
    def category(self) -> str:
        """Return the action category."""
        return "code"

    async def _publish_result(
        self,
        action_id: str,
        parameters: Dict[str, Any],
        success: bool,
        message: Optional[str] = None,
        error: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ):
        """Publish the result of the action execution."""
        event_name = Events.ACTION_COMPLETED if success else Events.ACTION_FAILED
        payload = {
            "action_id": action_id,
            "parameters": {
                "code": parameters.get("code", "")[:100] + "..."
            },  # Avoid logging full code
            "success": success,
            "message": message,
            "error": error,
            "data": data or {},  # Store stdout/stderr here
            "timestamp": time.time(),
        }
        await self.event_bus.publish(event_name, payload)

    # --- Specific Action Implementations ---

    async def _execute_python_code(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implementation for executing Python code.

        WARNING: This is a simplified example using subprocess. It lacks
        robust sandboxing and is vulnerable. DO NOT use in production
        without implementing proper security measures (Docker, nsjail, etc.).
        """
        code = params["code"]
        self.logger.warning(
            f"Executing Python code (UNSAFE IMPLEMENTATION): {code[:100]}..."
        )

        # Create a temporary file to store the code
        # Using NamedTemporaryFile ensures cleanup
        stdout_lines = []
        stderr_lines = []
        process = None  # Define process variable

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as tmp_file:
                # Write allowed imports and the user code
                # This is a very weak form of import control
                # for allowed_import in ALLOWED_IMPORTS:
                #     tmp_file.write(f"import {allowed_import}\n")
                # tmp_file.write("\n")
                tmp_file.write("import sys\n")
                tmp_file.write(
                    "import json\n"
                )  # Allow json for potential structured output
                # Redirect stdout/stderr within the script if needed, or capture from subprocess
                tmp_file.write(code)
                tmp_file_path = tmp_file.name

            # Command to execute the script using the same Python interpreter
            # Add flags for restricted execution if Python supports them (e.g., -I for isolated mode)
            command = [
                sys.executable,
                "-I",
                tmp_file_path,
            ]  # -I isolates from user site packages

            # Execute in a separate process using asyncio's subprocess
            self.logger.debug(f"Running command: {' '.join(command)}")
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                # Add arguments for resource limits (e.g., ulimit in shell, platform specific)
                # Add arguments for network restrictions (complex, depends on OS/sandbox)
                # Add arguments for filesystem restrictions (complex, depends on OS/sandbox)
            )

            # Attach process to task for potential cancellation
            # setattr(asyncio.current_task(), "process", process) # Be careful with modifying tasks

            # Read stdout and stderr concurrently with timeout
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), timeout=CODE_EXECUTION_TIMEOUT
                )
                stdout = stdout_bytes.decode("utf-8", errors="replace").strip()
                stderr = stderr_bytes.decode("utf-8", errors="replace").strip()
            except asyncio.TimeoutError:
                self.logger.error(
                    f"Code execution timed out after {CODE_EXECUTION_TIMEOUT} seconds."
                )
                if process.returncode is None:  # Process still running
                    try:
                        process.terminate()
                        await asyncio.sleep(0.1)
                        if process.returncode is None:
                            process.kill()
                        self.logger.info("Terminated timed-out code execution process.")
                    except Exception as term_e:
                        self.logger.error(
                            f"Failed to terminate timed-out process: {term_e}"
                        )
                raise ActionTimeoutError(
                    f"Code execution timed out after {CODE_EXECUTION_TIMEOUT}s."
                ) from None
            except Exception as comm_e:
                self.logger.error(
                    f"Error communicating with code execution process: {comm_e}"
                )
                stderr = f"Communication Error: {comm_e}"  # Add communication error to stderr
                stdout = ""

            # Wait for process exit and get return code
            return_code = (
                await process.wait()
            )  # process.returncode should be set after communicate

            self.logger.info(f"Code execution finished with return code: {return_code}")
            if stdout:
                self.logger.debug(f"Code stdout:\n{stdout}")
            if stderr:
                self.logger.warning(f"Code stderr:\n{stderr}")

            if return_code == 0:
                return {
                    "success": True,
                    "message": "Code executed successfully.",
                    "data": {
                        "stdout": stdout,
                        "stderr": stderr,
                        "return_code": return_code,
                    },
                }
            else:
                return {
                    "success": False,
                    "error": f"Code execution failed with return code {return_code}.",
                    "data": {
                        "stdout": stdout,
                        "stderr": stderr,
                        "return_code": return_code,
                    },
                }

        except RestrictedOperationError as e:
            # Re-raise security errors directly
            raise e
        except Exception as e:
            self.logger.exception(f"Failed to execute Python code: {e}")
            raise ActionExecutionError(f"Error during code execution: {e}") from e
        finally:
            # Clean up the temporary file
            if "tmp_file_path" in locals() and os.path.exists(tmp_file_path):
                try:
                    os.remove(tmp_file_path)
                    self.logger.debug(f"Removed temporary code file: {tmp_file_path}")
                except Exception as e:
                    self.logger.error(
                        f"Failed to remove temporary code file {tmp_file_path}: {e}"
                    )
