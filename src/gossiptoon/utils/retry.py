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
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        exponential_base: Base for exponential backoff
        max_delay: Maximum delay between retries
        exceptions: Tuple of exceptions to catch and retry

    Returns:
        Decorated function
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception: Optional[Exception] = None
            delay = initial_delay

            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                        delay = min(delay * exponential_base, max_delay)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts: {e}"
                        )

            raise RetryExhaustedError(func.__name__, max_retries) from last_exception

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            import time

            last_exception: Optional[Exception] = None
            delay = initial_delay

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * exponential_base, max_delay)
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
