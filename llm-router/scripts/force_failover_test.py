from __future__ import annotations

from llm_router.config import load_config
from llm_router.errors import ErrorCategory, ProviderError
from llm_router.logging import JsonlLogger
from llm_router.providers import AnthropicClaudeProvider, GoogleGeminiProvider, OpenAICodexProvider
from llm_router.router import Router


def main() -> int:
    cfg = load_config(None)
    logger = JsonlLogger(cfg.router.log_dir, log_prompts=False)

    providers = {
        "openai_codex": OpenAICodexProvider(name="openai_codex", cli_cmd="codex"),
        "anthropic_claude": AnthropicClaudeProvider(
            name="anthropic_claude", cli_cmd="C:/Users/HomePC/.local/bin/claude.exe"
        ),
        "google_gemini": GoogleGeminiProvider(name="google_gemini", cli_cmd="gemini"),
    }

    # Force Codex to fail with a simulated quota error to prove failover.
    def codex_fail(*args, **kwargs):
        raise ProviderError(
            "openai_codex",
            ErrorCategory.QUOTA_EXHAUSTED,
            "simulated quota",
            raw="insufficient_quota",
        )

    providers["openai_codex"].run = codex_fail  # type: ignore

    router = Router(cfg=cfg, providers=providers, logger=logger)
    resp = router.run("Say OK", verbose=True)

    print("\n--- RESULT ---")
    print(f"model_used={resp.model}")
    print(resp.text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
