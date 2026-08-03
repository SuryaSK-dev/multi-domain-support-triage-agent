import time

MIN_INTERVAL_SECONDS = 20  # ~3 calls/minute, safely under the 5 RPM ceiling

_last_call_time = [0.0]

def throttle():
    """Blocks until at least MIN_INTERVAL_SECONDS has passed since the last API call."""
    now = time.time()
    elapsed = now - _last_call_time[0]
    if elapsed < MIN_INTERVAL_SECONDS:
        wait = MIN_INTERVAL_SECONDS - elapsed
        print(f"Throttling: waiting {wait:.0f}s to stay under rate limit...")
        time.sleep(wait)
    _last_call_time[0] = time.time()