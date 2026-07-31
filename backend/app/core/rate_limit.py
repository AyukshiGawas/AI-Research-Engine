"""Rate limiting core module using slowapi."""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize Limiter keying on remote IP address
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])
