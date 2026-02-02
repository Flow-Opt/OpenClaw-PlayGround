from __future__ import annotations

from .cli_provider import CliProvider


class OpenAICodexProvider(CliProvider):
    """Adapter for OpenAI Codex.

    Note: command flags differ by Codex CLI version. Keep this adapter minimal
    and configurable; the router core is provider-agnostic.
    """

    def build_command(self, prompt: str, model: str, max_output_tokens: int) -> list[str]:
        # Official Codex CLI supports non-interactive runs via `codex exec`.
        # We'll capture the assistant's final message via `--output-last-message`.
        #
        # Note: Codex CLI currently does not expose a stable "max output tokens" flag;
        # we keep it in the router API but do not enforce it here.
        cmd: list[str] = [self.cli_cmd, "exec", "--skip-git-repo-check", "--sandbox", "read-only"]
        if model:
            cmd += ["--model", model]
        # prompt is the trailing argument
        cmd += [prompt]
        return cmd
