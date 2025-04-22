"""Rate limiter decorator"""

from fastapi import Request, Response
from typing import Callable, Any
from datetime import datetime, UTC
import functools

from backend.exceptions import TooManyRequests

# Tuples of request count and window size. X request per Y seconds.
KEY_LIMITS = {
    "forced": (60, 60), # this will always allow requests through
    "main": (3, 5),
    "auth": (2, 30), # login takes 1, refresh takes potentially 2 if they redirect to login page and then log in really fast
    "account": (3, 5),
    "from_email": (1, 30),
    "board": (2, 5),
    "board_action": (5, 5),
    "submit_report": (1, 30),
    "media": (1, 10),
    "static": (3, 5),
}

# Usage dictionary
USAGE = {}

# Decorator to take in the key
def limit(key: str = "main", *, no_content: bool = False, is_async = False):
    return_type = None if no_content else Any

    # Nested decorator that takes the actual request function
    def decorator(route_function: Callable[..., Any]) -> Callable[..., Any]:

        # Call the route function if this host has not exceeded the window
        @functools.wraps(route_function)
        async def limiter(request: Request, *args, **kwargs) -> return_type: # type: ignore
            # Extract actual limits
            if key not in KEY_LIMITS:
                raise ValueError(f"Unrecognized key {key}")
            count, window_size = KEY_LIMITS[key]

            host: str = request.client.host
            time: int = datetime.now(UTC).timestamp()

            # If this does not force traffic through, check for limiting
            if key != "forced":
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
                    print(f"Window Size: {window_size}\tWindow Count: {count}\tCurrent Count: {len(window)}")
                    raise TooManyRequests()

            # Proceed to the actual route function, making sure to return a 204 if applicable
            result: Any = await route_function(request, *args, **kwargs) if is_async else route_function(request, *args, **kwargs)
            if not no_content:
                return result

        return limiter
    return decorator