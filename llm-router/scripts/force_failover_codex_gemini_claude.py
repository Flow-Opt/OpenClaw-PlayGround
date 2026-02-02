from __future__ import annotations

"""Force a failover chain in the specific order:

Codex -> Gemini -> Claude

We do this by *simulating* failures for Codex and Gemini, then letting Claude run
for real. This proves the router honors the provider ordering.

Run (PowerShell):
  cd <repo>\llm-router
  $env:PYTHONPATH = (Get-Location).Path
  python .\scripts\force_failover_codex_gemini_claude.py
"""

from llm_router.config import load_config
from llm_router.errors import ErrorCategory, ProviderError
from llm_router.logging import JsonlLogger
from llm_router.providers import AnthropicClaudeProvider, GoogleGeminiProvider, OpenAICodexProvider
from llm_router.router import Router


def main() -> int:
    cfg = load_config(None)
    # Force the ordering for this test.
    cfg.router.providers = ["openai_codex", "google_gemini", "anthropic_claude"]

    logger = JsonlLogger(cfg.router.log_dir, log_prompts=False)

    providers = {
        "openai_codex": OpenAICodexProvider(name="openai_codex", cli_cmd="codex"),
        "google_gemini": GoogleGeminiProvider(name="google_gemini", cli_cmd="gemini"),
        "anthropic_claude": AnthropicClaudeProvider(
            name="anthropic_claude", cli_cmd="C:/Users/HomePC/.local/bin/claude.exe"
        ),
    }

    # Simulate Codex failure
    def codex_fail(*args, **kwargs):
        raise ProviderError(
            "openai_codex",
            ErrorCategory.QUOTA_EXHAUSTED,
            "simulated quota",
            raw="insufficient_quota",
        )

    # Simulate Gemini failure
    def gemini_fail(*args, **kwargs):
        raise ProviderError(
            "google_gemini",
            ErrorCategory.RATE_LIMITED,
            "simulated rate limit",
            raw="429 too many requests",
        )

    providers["openai_codex"].run = codex_fail  # type: ignore
    providers["google_gemini"].run = gemini_fail  # type: ignore

    router = Router(cfg=cfg, providers=providers, logger=logger)

    # Claude should run for real here.
    resp = router.run("Say OK", verbose=True)

    print("\n--- RESULT ---")
    print(f"final_provider=anthropic_claude")
    print(f"model_used={resp.model}")
    print(resp.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
