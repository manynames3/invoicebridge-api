from dataclasses import dataclass

from fastapi import Request


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    reason: str | None = None


class BaseRateLimiter:
    def allow(self, request: Request) -> RateLimitDecision:
        raise NotImplementedError


class NoopRateLimiter(BaseRateLimiter):
    """Placeholder interface for future tenant/API-key based limits."""

    def allow(self, request: Request) -> RateLimitDecision:
        return RateLimitDecision(allowed=True)
