from __future__ import annotations

"""Real smoke test: run the same prompt against each provider for real.

This does NOT use failover (because failover only happens on error). Instead it
verifies that Codex, Gemini, and Claude can *all* produce an answer right now.

Run (PowerShell):
  cd <repo>\llm-router
  $env:PYTHONPATH = (Get-Location).Path
  python .\scripts\real_triple_smoke_test.py
"""

import time

from llm_router.config import load_config
from llm_router.logging import JsonlLogger
from llm_router.providers import AnthropicClaudeProvider, GoogleGeminiProvider, OpenAICodexProvider


PROMPT = "Reply with exactly: OK"


def run_one(name: str, provider, timeout_s: int = 120) -> str:
    t0 = time.time()
    resp = provider.run(prompt=PROMPT, model="", timeout_seconds=timeout_s, max_output_tokens=200)
    dt = int((time.time() - t0) * 1000)
    text = (resp.text or "").strip()
    print(f"[{name}] {dt}ms -> {text!r}")
    return text


def main() -> int:
    cfg = load_config(None)
    _ = JsonlLogger(cfg.router.log_dir, log_prompts=False)  # ensure log dir exists

    codex = OpenAICodexProvider(name="openai_codex", cli_cmd="codex")
    gemini = GoogleGeminiProvider(name="google_gemini", cli_cmd="gemini")
    claude = AnthropicClaudeProvider(name="anthropic_claude", cli_cmd="C:/Users/HomePC/.local/bin/claude.exe")

    print("Real triple-provider smoke test (no failover):")
    ok1 = run_one("openai_codex", codex)
    ok2 = run_one("google_gemini", gemini)
    ok3 = run_one("anthropic_claude", claude)

    print("\n--- SUMMARY ---")
    print("openai_codex:", ok1)
    print("google_gemini:", ok2)
    print("anthropic_claude:", ok3)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
