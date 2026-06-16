"""
Provider-agnostic AI interface.

Everything the app needs from an AI provider is one method: take a system +
user prompt, return a parsed JSON object, or `None` if the provider is
unavailable or the call fails for ANY reason. Returning None (never raising)
is deliberate — every caller has a deterministic fallback, so an AI outage
degrades gracefully instead of breaking a request.
"""
from typing import Protocol, runtime_checkable


@runtime_checkable
class AIProvider(Protocol):
    name: str

    def complete_json(self, system: str, user: str) -> dict | None:
        """Return a parsed JSON object, or None on unavailability/failure."""
        ...
