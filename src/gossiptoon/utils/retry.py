"""Retry utilities with exponential backoff."""

import asyncio
import functools
import logging
from typing import Any, Callable, Optional, Type, TypeVar, Union

from gossiptoon.core.exceptions import RetryExhaustedError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    max_delay: float = 60.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    custom_intervals: Optional[list[float]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying functions with exponential backoff or custom intervals.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds (ignored if custom_intervals is set)
        exponential_base: Base for exponential backoff (ignored if custom_intervals is set)
        max_delay: Maximum delay between retries (ignored if custom_intervals is set)
        exceptions: Tuple of exceptions to catch and retry
        custom_intervals: Optional list of fixed retry intervals in seconds.
                         If provided, overrides exponential backoff.
                         Example: [1.0, 10.0, 30.0] for 1s, 10s, 30s delays

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None
            
            # Use custom intervals if provided, otherwise use exponential backoff
            if custom_intervals:
                delays = custom_intervals
            else:
                # Generate exponential backoff delays
                delays = []
                delay = initial_delay
                for _ in range(max_retries - 1):
                    delays.append(delay)
                    delay = min(delay * exponential_base, max_delay)

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        current_delay = delays[attempt] if attempt < len(delays) else delays[-1]
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts: {e}"
                        )

            raise RetryExhaustedError(func.__name__, max_retries) from last_exception

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            import time

            last_exception: Optional[Exception] = None
            
            # Use custom intervals if provided, otherwise use exponential backoff
            if custom_intervals:
                delays = custom_intervals
            else:
                # Generate exponential backoff delays
                delays = []
                delay = initial_delay
                for _ in range(max_retries - 1):
                    delays.append(delay)
                    delay = min(delay * exponential_base, max_delay)

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        current_delay = delays[attempt] if attempt < len(delays) else delays[-1]
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts: {e}"
                        )

            raise RetryExhaustedError(func.__name__, max_retries) from last_exception

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator
