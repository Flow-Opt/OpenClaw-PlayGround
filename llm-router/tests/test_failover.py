from __future__ import annotations

from dataclasses import dataclass

from llm_router.config import Config, ProviderConfig, RouterConfig
from llm_router.errors import ErrorCategory, ProviderError
from llm_router.logging import JsonlLogger
from llm_router.providers.base import Provider, ProviderResponse
from llm_router.router import Router


@dataclass
class FakeProvider(Provider):
    name: str
    # sequence of actions: either ProviderResponse or ProviderError
    actions: list[object]

    def run(self, prompt: str, model: str, timeout_seconds: int, max_output_tokens: int) -> ProviderResponse:
        if not self.actions:
            raise ProviderError(self.name, ErrorCategory.UNKNOWN, "no actions")
        a = self.actions.pop(0)
        if isinstance(a, ProviderError):
            raise a
        assert isinstance(a, ProviderResponse)
        return a


def _cfg() -> Config:
    router = RouterConfig(
        providers=["openai_codex", "anthropic_claude", "google_gemini"],
        routing_policy="failover_then_degrade",
        log_dir="./.test-logs",
        log_prompts=False,
        timeout_seconds=1,
        degrade_enabled=True,
        degrade_max_output_tokens=800,
    )
    providers = {
        "openai_codex": ProviderConfig(mode="cli", cli_cmd="codex", model_primary="x", model_degraded="x-mini"),
        "anthropic_claude": ProviderConfig(mode="cli", cli_cmd="claude", model_primary="y", model_degraded="y-mini"),
        "google_gemini": ProviderConfig(mode="cli", cli_cmd="gemini", model_primary="z", model_degraded="z-mini"),
    }
    return Config(router=router, providers=providers)


def test_codex_quota_then_claude_success(tmp_path):
    cfg = _cfg()
    cfg.router.log_dir = str(tmp_path)

    codex = FakeProvider(
        name="openai_codex",
        actions=[ProviderError("openai_codex", ErrorCategory.QUOTA_EXHAUSTED, "quota", raw="insufficient_quota")],
    )
    claude = FakeProvider(
        name="anthropic_claude",
        actions=[ProviderResponse(text="ok", model="y", degraded=False, latency_ms=10)],
    )
    gemini = FakeProvider(
        name="google_gemini",
        actions=[ProviderResponse(text="should_not_run", model="z", degraded=False, latency_ms=10)],
    )

    router = Router(cfg, {"openai_codex": codex, "anthropic_claude": claude, "google_gemini": gemini}, JsonlLogger(str(tmp_path)))
    resp = router.run("hi")
    assert resp.text == "ok"


def test_claude_rate_limit_then_gemini_success(tmp_path):
    cfg = _cfg()
    cfg.router.log_dir = str(tmp_path)

    codex = FakeProvider(
        name="openai_codex",
        actions=[ProviderError("openai_codex", ErrorCategory.QUOTA_EXHAUSTED, "quota", raw="insufficient_quota")],
    )
    claude = FakeProvider(
        name="anthropic_claude",
        actions=[ProviderError("anthropic_claude", ErrorCategory.RATE_LIMITED, "rate", raw="429 too many requests")],
    )
    gemini = FakeProvider(
        name="google_gemini",
        actions=[ProviderResponse(text="ok2", model="z", degraded=False, latency_ms=10)],
    )

    router = Router(cfg, {"openai_codex": codex, "anthropic_claude": claude, "google_gemini": gemini}, JsonlLogger(str(tmp_path)))
    resp = router.run("hi")
    assert resp.text == "ok2"


def test_all_fail_limits_returns_quota_exhausted_message(tmp_path):
    cfg = _cfg()
    cfg.router.log_dir = str(tmp_path)

    codex = FakeProvider(
        name="openai_codex",
        actions=[ProviderError("openai_codex", ErrorCategory.QUOTA_EXHAUSTED, "quota", raw="insufficient_quota")],
    )
    claude = FakeProvider(
        name="anthropic_claude",
        actions=[ProviderError("anthropic_claude", ErrorCategory.RATE_LIMITED, "rate", raw="429")],
    )
    gemini = FakeProvider(
        name="google_gemini",
        actions=[ProviderError("google_gemini", ErrorCategory.QUOTA_EXHAUSTED, "quota", raw="quota exceeded")],
    )

    router = Router(cfg, {"openai_codex": codex, "anthropic_claude": claude, "google_gemini": gemini}, JsonlLogger(str(tmp_path)))

    try:
        router.run("hi")
        assert False, "expected error"
    except ProviderError as e:
        assert e.category == ErrorCategory.QUOTA_EXHAUSTED
        assert (
            e.message
            == "All providers are currently at usage limits. Try again later or reduce request size."
        )
