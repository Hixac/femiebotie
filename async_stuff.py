import asyncio
from functools import wraps
import time

def throttle(interval_seconds: float, from_start: bool = True):
    """
    Decorator that skips function calls if called within `interval_seconds`
    of the last execution.
    
    :param interval_seconds: Minimum required seconds between calls
    :param from_start: If True, measures interval from start of last call.
                       If False, measures from end of last call.
    """
    def decorator(func):
        last_called = 0
        lock = asyncio.Lock()

        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal last_called
            async with lock:  # Ensures non-concurrent execution
                current_time = time.monotonic()
                if current_time - last_called < interval_seconds:
                    return  # Skip call
                
                if from_start:
                    last_called = current_time
                
                try:
                    return await func(*args, **kwargs)
                finally:
                    if not from_start:
                        last_called = time.monotonic()
        return wrapper
    return decorator
