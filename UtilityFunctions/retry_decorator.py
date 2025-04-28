import time
from functools import wraps
from typing import Callable, Any

def retry(max_attempts: int = 3, delay: float = 3.0):
    """
    A decorator that retries a function call if it fails.
    
    Args:
        max_attempts (int): Maximum number of attempts before giving up
        delay (float): Delay in seconds between retries
        
    Usage:
        @retry(max_attempts=3, delay=3.0)
        def my_function():
            # function code here
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:  # Don't wait on the last attempt
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator 