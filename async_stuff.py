import asyncio
from functools import wraps
import time

def throttle(interval_seconds: float, from_start: bool = True):
    def decorator(func):
        last_called = 0
        lock = asyncio.Lock()

        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal last_called
            async with lock:
                current_time = time.monotonic()
                if current_time - last_called < interval_seconds:
                    return
                
                if from_start:
                    last_called = current_time
                
                try:
                    return await func(*args, **kwargs)
                finally:
                    if not from_start:
                        last_called = time.monotonic()
        return wrapper
    return decorator
