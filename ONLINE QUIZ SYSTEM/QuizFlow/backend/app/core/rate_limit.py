"""
In-memory Rate Limiting & Brute-Force Protection for QuizFlow Authentication.
Implements progressive backoff and sliding window lockout to protect instructor
and administrator accounts from automated credential stuffing and dictionary attacks.
"""
import time
from collections import defaultdict
from typing import Dict, List, Optional, Tuple


class RateLimiter:
    def __init__(
        self,
        max_attempts: int = 5,
        window_seconds: int = 300,
        lockout_seconds: int = 300,
    ):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lockout_seconds = lockout_seconds
        self._attempts: Dict[str, List[float]] = defaultdict(list)
        self._lockouts: Dict[str, float] = {}

    def is_rate_limited(self, key: str) -> Tuple[bool, int]:
        """
        Check if the key is currently locked out.
        Returns: (is_limited, retry_after_seconds)
        """
        now = time.time()
        # Check active lockout
        lockout_until = self._lockouts.get(key, 0)
        if now < lockout_until:
            return True, int(lockout_until - now)

        # Clean up stale attempts outside the window
        cutoff = now - self.window_seconds
        self._attempts[key] = [t for t in self._attempts[key] if t > cutoff]

        if len(self._attempts[key]) >= self.max_attempts:
            # Trigger progressive lockout
            multiplier = 1 + (len(self._attempts[key]) - self.max_attempts) // 2
            penalty = self.lockout_seconds * min(multiplier, 5)
            self._lockouts[key] = now + penalty
            return True, penalty

        return False, 0

    def record_attempt(self, key: str, success: bool = False):
        """Record an attempt. If successful, clear lockout and attempts."""
        if success:
            self.reset(key)
        else:
            now = time.time()
            self._attempts[key].append(now)

    def reset(self, key: str):
        """Reset attempts and lockouts for a key upon successful login."""
        self._attempts.pop(key, None)
        self._lockouts.pop(key, None)


# Global limiter instances for auth endpoints
auth_rate_limiter = RateLimiter(max_attempts=5, window_seconds=300, lockout_seconds=300)
