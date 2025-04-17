"""
Asynchronous Utilities

Provides helper functions and classes for working with asyncio.
"""

import asyncio
import time
import logging
from typing import Callable, Any, TypeVar, Coroutine
from functools import wraps, partial

T = TypeVar("T")
logger = logging.getLogger(__name__)


async def run_sync_in_executor(
    sync_func: Callable[..., T], *args: Any, **kwargs: Any
) -> T:
    """
    Runs a synchronous function in the default asyncio executor pool
    to avoid blocking the main event loop.

    Args:
        sync_func: The synchronous function to execute.
        *args: Positional arguments for the function.
        **kwargs: Keyword arguments for the function.

    Returns:
        The result of the synchronous function.

    Raises:
        Exception: Propagates any exception raised by the sync_func.
    """
    loop = asyncio.get_running_loop()
    # Use functools.partial to handle keyword arguments correctly
    func_call = partial(sync_func, *args, **kwargs)
    try:
        # logger.debug(f"Running sync function {sync_func.__name__} in executor.")
        result = await loop.run_in_executor(
            None, func_call
        )  # None uses default ThreadPoolExecutor
        # logger.debug(f"Sync function {sync_func.__name__} completed.")
        return result
    except Exception as e:
        logger.error(
            f"Error executing sync function {sync_func.__name__} in executor: {e}",
            exc_info=False,
        )  # Log concisely
        raise  # Re-raise the exception


class RateLimiter:
    """
    A simple asyncio-compatible rate limiter using the token bucket algorithm.

    Allows a certain number of operations per time period.
    """

    def __init__(self, rate: float, capacity: float):
        """
        Initialize the RateLimiter.

        Args:
            rate: The rate at which tokens are refilled per second.
            capacity: The maximum number of tokens the bucket can hold.
        """
        if rate <= 0 or capacity <= 0:
            raise ValueError("Rate and capacity must be positive")
        self.rate = rate
        self.capacity = capacity
        self._tokens = capacity
        self._last_refill_time = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.monotonic()
        elapsed = now - self._last_refill_time
        if elapsed > 0:
            tokens_to_add = elapsed * self.rate
            self._tokens = min(self.capacity, self._tokens + tokens_to_add)
            self._last_refill_time = now

    async def acquire(self, tokens: float = 1.0) -> bool:
        """
        Acquire the specified number of tokens, waiting if necessary.

        Args:
            tokens: The number of tokens required for the operation.

        Returns:
            True once the tokens have been acquired.
        """
        if tokens > self.capacity:
            raise ValueError(
                f"Requested tokens ({tokens}) exceeds capacity ({self.capacity})"
            )

        async with self._lock:
            while True:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    # logger.debug(f"RateLimiter acquired {tokens} tokens. Remaining: {self._tokens:.2f}")
                    return True
                else:
                    # Calculate time needed to wait for enough tokens
                    needed = tokens - self._tokens
                    wait_time = needed / self.rate
                    # logger.debug(f"RateLimiter waiting for {wait_time:.3f}s for {tokens} tokens. Have: {self._tokens:.2f}")
                    await asyncio.sleep(wait_time)

    def try_acquire(self, tokens: float = 1.0) -> bool:
        """
        Try to acquire tokens without waiting.

        Args:
            tokens: The number of tokens required.

        Returns:
            True if tokens were acquired immediately, False otherwise.
        """
        if tokens > self.capacity:
            return False  # Cannot acquire more than capacity

        # Use locking to ensure atomicity even in try_acquire
        # Although less critical here than in acquire, it prevents race conditions
        # if multiple tasks call try_acquire concurrently after a refill.
        # If performance is critical and concurrent calls rare, lock can be skipped.
        # async with self._lock: # Optional lock
        self._refill()  # Check current token level
        if self._tokens >= tokens:
            self._tokens -= tokens
            # logger.debug(f"RateLimiter try_acquire succeeded for {tokens} tokens. Remaining: {self._tokens:.2f}")
            return True
        else:
            # logger.debug(f"RateLimiter try_acquire failed for {tokens} tokens. Have: {self._tokens:.2f}")
            return False

    async def __aenter__(self):
        """Allows using the rate limiter with 'async with'."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Context manager exit (no specific action needed)."""
        pass


def async_wrap(func: Callable[..., T]) -> Callable[..., Coroutine[Any, Any, T]]:
    """
    Decorator to wrap a synchronous function to run in the default executor.

    Usage:
        @async_wrap
        def my_sync_blocking_function(arg1, arg2):
            # ... does blocking work ...
            return result

        # Now call it as an async function:
        async def main():
            result = await my_sync_blocking_function(1, 2)
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await run_sync_in_executor(func, *args, **kwargs)

    return wrapper
