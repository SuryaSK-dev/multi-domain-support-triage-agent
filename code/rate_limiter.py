import time
from collections import deque

MAX_CALLS_PER_MINUTE = 4  # stay under the 5 RPM ceiling with a safety margin
WINDOW_SECONDS = 60

_call_times = deque()

def throttle():
    """Blocks until it's safe to make another API call, staying under quota."""
    now = time.time()
    while _call_times and now - _call_times[0] > WINDOW_SECONDS:
        _call_times.popleft()

    if len(_call_times) >= MAX_CALLS_PER_MINUTE:
        wait = WINDOW_SECONDS - (now - _call_times[0]) + 1
        if wait > 0:
            print(f"Throttling: waiting {wait:.0f}s to stay under rate limit...")
            time.sleep(wait)

    _call_times.append(time.time())