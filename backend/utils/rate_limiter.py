"""Rate limiter decorator"""

from fastapi import Request
from typing import Callable, Any
from datetime import datetime, UTC

from backend.exceptions import TooManyRequests

# Tuples of request count and window size. X request per Y seconds.
KEY_LIMITS = {
    "forced": (60, 60), # this will always allow requests through
    "main": (3, 5),
    "auth": (2, 5), # login takes 1, refresh takes potentially 2 if they redirect to login page and then log in really fast
    "account": (3, 5),
    "from_email": (1, 30),
    "board_action": (5, 5),
    "submit_report": (1, 30),
    "upload_media": (1, 10),
    "static": (3, 5),
}

# Usage dictionary
USAGE = {}

# Decorator to take in the key
def limit(key: str = "main"):
    # Extract actual parameters
    if key not in KEY_LIMITS:
        raise ValueError(f"Unrecognized key {key}")
    count, window_size = KEY_LIMITS[key]

    # Nested decorator that takes the actual request function
    def decorator(route_function: Callable[[Request], Any]) -> Callable[[Request], Any]:

        # Call the route function if this host has not exceeded the window
        async def limiter(request: Request) -> Any:
            host: str = request.client.host
            time: int = datetime.now(UTC).timestamp()

            # If this forces traffic through return early
            if key == "forced":
                return await route_function()
            
            # Make sure the window exists for this key and get a reference
            if host not in USAGE:
                USAGE[host] = {}
            if key not in USAGE[host]:
                USAGE[host][key] = []
            window = USAGE[host][key]
            
            # Remove outdated entries and add one
            window[:] = [ t for t in window if time - t < window_size]
            window.append(time)

            # If the limit has been exceeded, throw an error
            if (len(window) > count):
                raise TooManyRequests()

            # Proceed to the actual route function
            return await route_function()

        return limiter
    return decorator