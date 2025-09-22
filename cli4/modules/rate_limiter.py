"""
CLI4 Rate Limiter
Simple API rate limiting - no overcomplicated nonsense
"""

import time
from typing import Dict, Optional


class CLI4RateLimiter:
    """Simple rate limiter for API calls"""

    def __init__(self):
        # Track last call time per API
        self.last_calls: Dict[str, float] = {}

        # Rate limits per API (seconds between calls)
        self.limits = {
            'camara': 0.5,    # 2 calls/second max
            'tse': 1.0,       # 1 call/second max
            'senado': 0.5,    # 2 calls/second max
            'portal': 1.0,    # 1 call/second max (has API key)
            'tcu': 1.5,       # Conservative for government site
            'datajud': 2.0,   # Very conservative for judicial data
            'default': 1.0    # Default for unknown APIs
        }

    def wait_if_needed(self, api: str) -> float:
        """Wait if needed to respect rate limits"""
        api = api.lower()
        limit = self.limits.get(api, self.limits['default'])

        current_time = time.time()
        last_call = self.last_calls.get(api, 0)

        time_since_last = current_time - last_call

        if time_since_last < limit:
            wait_time = limit - time_since_last
            time.sleep(wait_time)
            current_time = time.time()

        self.last_calls[api] = current_time
        return current_time - last_call if last_call > 0 else 0

    def get_api_stats(self) -> Dict[str, Dict]:
        """Get rate limiting statistics"""
        current_time = time.time()
        stats = {}

        for api, last_call in self.last_calls.items():
            time_since = current_time - last_call
            limit = self.limits.get(api, self.limits['default'])

            stats[api] = {
                'last_call_ago': time_since,
                'rate_limit': limit,
                'can_call_now': time_since >= limit
            }

        return stats

    def reset_api(self, api: str):
        """Reset rate limiting for specific API"""
        api = api.lower()
        if api in self.last_calls:
            del self.last_calls[api]

    def reset_all(self):
        """Reset all rate limiting"""
        self.last_calls.clear()