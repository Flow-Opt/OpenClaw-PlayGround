from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ErrorCategory(str, Enum):
    RATE_LIMITED = "rate_limited"
    QUOTA_EXHAUSTED = "quota_exhausted"
    AUTH_ERROR = "auth_error"
    TRANSIENT_NETWORK = "transient_network"
    INVALID_REQUEST = "invalid_request"
    UNKNOWN = "unknown"


@dataclass
class ProviderError(Exception):
    provider: str
    category: ErrorCategory
    message: str
    raw: str | None = None

    def __str__(self) -> str:
        return f"{self.provider}:{self.category}: {self.message}"
