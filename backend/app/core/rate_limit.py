"""Rate limiting core module using slowapi."""

import os
import sys
from typing import Any, Callable

from slowapi import Limiter
from slowapi.util import get_remote_address


class NoopLimiter:
    """Test-safe limiter that disables rate limiting for pytest runs."""

    def limit(self, *args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator


def _is_test_environment() -> bool:
    """Return True when the app is running under pytest or test mode only."""
    env_name = os.getenv("APP_ENV", "").lower()
    if env_name in {"test", "testing"}:
        return True
    return "pytest" in sys.modules


# Initialize Limiter keying on remote IP address
limiter = NoopLimiter() if _is_test_environment() else Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"],
)
