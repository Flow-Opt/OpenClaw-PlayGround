from __future__ import annotations

import re

from .errors import ErrorCategory


class ErrorClassifier:
    """Provider-agnostic pattern matcher.

    This intentionally errs on the conservative side: we only classify as a
    "limit" when strong signals exist.
    """

    _RATE_LIMIT = re.compile(r"\b(rate\s*limit|too\s*many\s*requests|http\s*429|429)\b", re.I)
    _QUOTA = re.compile(
        r"\b(quota\s*exceeded|insufficient\s*quota|insufficient_quota|usage\s*limit\s*reached|billing\s*(?:hard\s*)?limit|exceeded\s*your\s*current\s*quota)\b",
        re.I,
    )
    _AUTH = re.compile(r"\b(unauthorized|forbidden|invalid\s*api\s*key|invalid\s*token|expired\s*token|no\s*api\s*key|not\s*logged\s*in|authentication\s*failed|http\s*401|401|http\s*403|403)\b", re.I)
    _TRANSIENT = re.compile(r"\b(timeout|timed\s*out|temporarily\s*unavailable|overloaded|try\s*again\s*later|connection\s*(?:reset|refused)|dns|network\s*error|econnreset|econnrefused)\b", re.I)
    _INVALID = re.compile(r"\b(invalid\s*request|bad\s*request|http\s*400|400|unknown\s*model|model\s*not\s*found|invalid\s*argument|unsupported)\b", re.I)

    def classify(self, text: str) -> ErrorCategory:
        if not text:
            return ErrorCategory.UNKNOWN

        t = text.strip()

        if self._QUOTA.search(t):
            return ErrorCategory.QUOTA_EXHAUSTED
        if self._RATE_LIMIT.search(t):
            return ErrorCategory.RATE_LIMITED
        if self._AUTH.search(t):
            return ErrorCategory.AUTH_ERROR
        if self._INVALID.search(t):
            return ErrorCategory.INVALID_REQUEST
        if self._TRANSIENT.search(t):
            return ErrorCategory.TRANSIENT_NETWORK

        return ErrorCategory.UNKNOWN
