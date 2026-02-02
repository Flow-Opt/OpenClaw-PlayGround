from __future__ import annotations

from dataclasses import dataclass

from ..errors import ProviderError


@dataclass
class ProviderResponse:
    text: str
    model: str
    degraded: bool
    latency_ms: int


class Provider:
    name: str

    def preflight(self) -> None:
        """Should raise ProviderError (AUTH/TRANSIENT) if not usable."""
        return None

    def run(self, prompt: str, model: str, timeout_seconds: int, max_output_tokens: int) -> ProviderResponse:
        raise NotImplementedError

    def last_raw_error(self) -> str | None:
        return None
