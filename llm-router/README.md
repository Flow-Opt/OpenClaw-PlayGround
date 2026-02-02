# llm-router

A small **CLI-first LLM router** that runs a prompt against multiple providers with **graceful failover**.

- Order (configurable): **OpenAI Codex → Google Gemini** (Claude optional)
- Uses **official CLIs/APIs only** (no bypassing rate limits, no ToS violations)
- Detects limit/health errors and fails over safely
- Writes **structured JSONL logs** (secrets redacted; prompts not logged by default)

> This project is designed to be cross-platform (Windows/macOS/Linux).

## Install

Python 3.11+ recommended.

```bash
cd llm-router
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
# source .venv/bin/activate

pip install -r requirements.txt
```

## Quick start

```bash
python -m llm_router.cli "Refactor this repo to be more readable"
```

### Examples

```bash
# basic
llm-run "Refactor this repo..."

# force one provider
llm-run --provider openai_codex "..."

# verbose routing decisions
llm-run --verbose "..."
```

## Config

Default config path:

- Windows: `%USERPROFILE%\.llm-router\config.yml`
- macOS/Linux: `~/.llm-router/config.yml`

Example:

```yaml
router:
  providers: [openai_codex, google_gemini]

# Enable Claude later if desired:
#   - add `anthropic_claude` back into router.providers
#   - ensure `claude -p "Say OK" --output-format text` works reliably
  routing_policy: failover_then_degrade
  log_dir: ~/.llm-router/logs
  log_prompts: false
  timeouts:
    provider_seconds: 120
  degrade:
    enabled: true
    max_output_tokens: 800

openai_codex:
  mode: cli
  cli_cmd: codex
  model_primary: gpt-5-codex
  model_degraded: gpt-5-codex-mini

anthropic_claude:
  mode: cli
  cli_cmd: claude
  model_primary: claude-3-7-sonnet
  model_degraded: claude-3-5-haiku

google_gemini:
  mode: cli
  cli_cmd: gemini
  model_primary: gemini-2.0-flash
  model_degraded: gemini-2.0-flash-lite
```

## Logging

Logs are JSONL written to `~/.llm-router/logs/router.jsonl`.

By default logs include:
- provider, model, latency
- error category (if any)
- failover reason

Prompts are **not logged** unless you pass `--log-prompts`.

## Tests

```bash
pytest -q
```

Acceptance tests covered:
- Codex quota error → uses Claude
- Claude rate limit → uses Gemini
- All fail → returns: `All providers are currently at usage limits. Try again later or reduce request size.`
- Logs show provider switching + reasons
