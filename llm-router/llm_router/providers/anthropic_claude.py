from __future__ import annotations

from .cli_provider import CliProvider


class AnthropicClaudeProvider(CliProvider):
    def build_command(self, prompt: str, model: str, max_output_tokens: int) -> list[str]:
        # Claude Code supports non-interactive output with `-p/--print`.
        cmd: list[str] = [self.cli_cmd, "-p", "--output-format", "text", "--permission-mode", "default"]
        if model:
            cmd += ["--model", model]
        cmd += [prompt]
        return cmd
