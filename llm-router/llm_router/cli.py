from __future__ import annotations

import argparse
import sys

from .config import load_config
from .errors import ProviderError
from .logging import JsonlLogger
from .providers import AnthropicClaudeProvider, GoogleGeminiProvider, OpenAICodexProvider
from .router import Router


def build_providers(cfg) -> dict[str, object]:
    p = {}
    # CLI adapters (minimal). Real invocation flags are left configurable.
    o = cfg.providers.get("openai_codex")
    a = cfg.providers.get("anthropic_claude")
    g = cfg.providers.get("google_gemini")

    p["openai_codex"] = OpenAICodexProvider(name="openai_codex", cli_cmd=o.cli_cmd if o else "codex")
    p["anthropic_claude"] = AnthropicClaudeProvider(name="anthropic_claude", cli_cmd=a.cli_cmd if a else "claude")
    p["google_gemini"] = GoogleGeminiProvider(name="google_gemini", cli_cmd=g.cli_cmd if g else "gemini")
    return p


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="llm-run", description="Route LLM requests across multiple providers with failover")
    ap.add_argument("prompt", help="User prompt")
    ap.add_argument("--config", dest="config", default=None, help="Path to config.yml")
    ap.add_argument("--provider", dest="provider", default=None, help="Force provider (openai_codex|anthropic_claude|google_gemini)")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--log-prompts", action="store_true", help="Log prompts to JSONL (redacted). Off by default.")
    ap.add_argument("--max-output-tokens", type=int, default=None)

    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    logger = JsonlLogger(log_dir=cfg.router.log_dir, log_prompts=(cfg.router.log_prompts or args.log_prompts))
    providers = build_providers(cfg)

    router = Router(cfg=cfg, providers=providers, logger=logger)

    try:
        resp = router.run(
            args.prompt,
            force_provider=args.provider,
            verbose=args.verbose,
            log_prompts=args.log_prompts,
            max_output_tokens=args.max_output_tokens,
        )
        sys.stdout.write(resp.text + "\n")
    except ProviderError as e:
        # Print user-friendly message, do not dump raw tokens.
        sys.stderr.write(str(e) + "\n")
        if args.verbose and e.raw:
            sys.stderr.write("--- raw ---\n" + str(e.raw) + "\n")
        if e.provider == "router" and "All providers are currently at usage limits" in e.message:
            sys.stderr.write(e.message + "\n")
            sys.exit(2)
        sys.exit(1)


if __name__ == "__main__":
    main()
