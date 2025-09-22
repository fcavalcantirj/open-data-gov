"""
Rate Limiter Module
Prevents API rate limit issues and connection failures
"""

import time
from typing import Dict, Optional
from datetime import datetime, timedelta


class RateLimiter:
    """Simple rate limiter to prevent API throttling"""

    def __init__(self):
        self.call_times: Dict[str, list] = {}
        self.limits = {
            "tse": {"calls": 10, "period": 60},  # 10 calls per minute
            "deputados": {"calls": 30, "period": 60},  # 30 calls per minute
            "default": {"calls": 20, "period": 60}  # Default: 20 calls per minute
        }

    def wait_if_needed(self, api_name: str = "default") -> None:
        """Wait if rate limit would be exceeded"""
        if api_name not in self.call_times:
            self.call_times[api_name] = []

        limit_config = self.limits.get(api_name, self.limits["default"])
        max_calls = limit_config["calls"]
        period = limit_config["period"]

        now = datetime.now()
        cutoff = now - timedelta(seconds=period)

        # Remove old calls
        self.call_times[api_name] = [
            call_time for call_time in self.call_times[api_name]
            if call_time > cutoff
        ]

        # Check if we need to wait
        if len(self.call_times[api_name]) >= max_calls:
            oldest_call = min(self.call_times[api_name])
            wait_time = (oldest_call + timedelta(seconds=period) - now).total_seconds()
            if wait_time > 0:
                print(f"⏳ Rate limit: waiting {wait_time:.1f}s for {api_name} API...")
                time.sleep(wait_time)

        # Record this call
        self.call_times[api_name].append(now)

    def add_delay(self, seconds: float = 0.5) -> None:
        """Add a simple delay between calls"""
        time.sleep(seconds)


# Global rate limiter instance
rate_limiter = RateLimiter()