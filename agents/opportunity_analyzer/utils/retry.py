import functools
import time
from typing import Callable, TypeVar

from agents.opportunity_analyzer.utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    backoff_seconds: float = 1.5,
    exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """
    Retries a function on failure with exponential backoff.
    Logs each failed attempt. Re-raises the last exception if all attempts fail.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(
                        "%s failed on attempt %d/%d: %s",
                        func.__name__,
                        attempt,
                        max_attempts,
                        e,
                    )
                    if attempt < max_attempts:
                        time.sleep(backoff_seconds * attempt)
            raise last_exception  # type: ignore[misc]

        return wrapper

    return decorator
