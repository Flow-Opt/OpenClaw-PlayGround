from llm_router.classifier import ErrorClassifier
from llm_router.errors import ErrorCategory


def test_classify_rate_limited():
    c = ErrorClassifier()
    assert c.classify("HTTP 429 Too Many Requests") == ErrorCategory.RATE_LIMITED


def test_classify_quota_exhausted():
    c = ErrorClassifier()
    assert c.classify("insufficient_quota") == ErrorCategory.QUOTA_EXHAUSTED


def test_classify_auth_error():
    c = ErrorClassifier()
    assert c.classify("HTTP 401 Unauthorized") == ErrorCategory.AUTH_ERROR


def test_classify_transient_network():
    c = ErrorClassifier()
    assert c.classify("connection reset by peer") == ErrorCategory.TRANSIENT_NETWORK


def test_classify_invalid_request():
    c = ErrorClassifier()
    assert c.classify("invalid request: unknown model") == ErrorCategory.INVALID_REQUEST
