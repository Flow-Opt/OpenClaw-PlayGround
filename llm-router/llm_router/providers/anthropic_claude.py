from __future__ import annotations

from .cli_provider import CliProvider


class AnthropicClaudeProvider(CliProvider):
    def build_command(self, prompt: str, model: str, max_output_tokens: int) -> list[str]:
        # Placeholder. Replace with official Claude CLI invocation you use.
        # Example (illustrative only):
        # return [self.cli_cmd, "--model", model, "--max-tokens", str(max_output_tokens), "--print", prompt]
        return [self.cli_cmd, "--help"]
