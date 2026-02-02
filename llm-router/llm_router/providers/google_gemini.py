from __future__ import annotations

from .cli_provider import CliProvider


class GoogleGeminiProvider(CliProvider):
    def build_command(self, prompt: str, model: str, max_output_tokens: int) -> list[str]:
        # Gemini CLI supports one-shot prompts via positional args.
        cmd: list[str] = [self.cli_cmd, "--output-format", "text"]
        if model:
            cmd += ["--model", model]
        cmd += [prompt]
        return cmd
