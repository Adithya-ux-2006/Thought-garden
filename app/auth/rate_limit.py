import threading
import time
from collections import deque


class FailedLoginLimiter:
    """Sliding window of failed logins per key (client IP).

    State lives in this process only: correct for the single-process
    deployment this app targets, not shared across multiple workers.
    """

    MAX_KEYS = 10_000

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self._failures = {}
        self._lock = threading.Lock()

    def reset(self):
        with self._lock:
            self._failures.clear()

    def _recent(self, key, window, now):
        attempts = self._failures.get(key)
        if attempts is None:
            return None
        while attempts and attempts[0] <= now - window:
            attempts.popleft()
        if not attempts:
            del self._failures[key]
            return None
        return attempts

    def retry_after(self, key, max_attempts, window):
        """Seconds until `key` may try again, or 0 if not blocked."""
        with self._lock:
            now = self.clock()
            attempts = self._recent(key, window, now)
            if attempts is None or len(attempts) < max_attempts:
                return 0
            return attempts[-max_attempts] + window - now

    def record_failure(self, key, window):
        with self._lock:
            now = self.clock()
            if key not in self._failures and len(self._failures) >= self.MAX_KEYS:
                for stale in list(self._failures):
                    self._recent(stale, window, now)
                if len(self._failures) >= self.MAX_KEYS:
                    self._failures.pop(next(iter(self._failures)))
            self._failures.setdefault(key, deque()).append(now)
