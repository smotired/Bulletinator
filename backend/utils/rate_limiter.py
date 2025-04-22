"""Rate limiter decorator"""

from fastapi import Request
from typing import Callable, Any

from backend.exceptions import TooManyRequests

# Tuples of request count and window size. X request per Y seconds.
KEY_LIMITS = {
    "main": (5, 5),
}

# Decorator to take in the key
def limit(key: str | None = None, *, limit: tuple[int, int] | None = None):
    # Extract parameters
    if limit is None:
        if key is None:
            raise ValueError("Must provide a limit or a key")
        if key not in KEY_LIMITS:
            raise ValueError(f"Key '{key}' does not exist.")
        limit = KEY_LIMITS[key]
    count, window_size = limit

    # Nested decorator that takes the actual request function
    def decorator(route_function: Callable[[Request], Any]) -> Callable[[Request], Any]:

        # Call the route function if this host has not exceeded the window
        async def limiter(request: Request) -> Any:
            host: str = request.client.host
            print(f"Limit: {count}r / {window_size}s\tHost Address: {host}")
            return route_function()

        return limiter
    return decorator