from __future__ import annotations

from .cli_provider import CliProvider


class OpenAICodexProvider(CliProvider):
    """Adapter for OpenAI Codex.

    Note: command flags differ by Codex CLI version. Keep this adapter minimal
    and configurable; the router core is provider-agnostic.
    """

    def build_command(self, prompt: str, model: str, max_output_tokens: int) -> list[str]:
        # Placeholder. Replace with official Codex CLI invocation you use.
        # Example (illustrative only):
        # return [self.cli_cmd, "run", "--model", model, "--max-tokens", str(max_output_tokens), prompt]
        return [self.cli_cmd, "--help"]
