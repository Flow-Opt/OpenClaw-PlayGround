from __future__ import annotations

import shutil
import subprocess
import time

from ..classifier import ErrorClassifier
from ..errors import ErrorCategory, ProviderError
from .base import Provider, ProviderResponse


class CliProvider(Provider):
    def __init__(self, name: str, cli_cmd: str | None):
        self.name = name
        self.cli_cmd = cli_cmd or name
        self._resolved_cmd: str | None = None
        self._last_err: str | None = None
        self._classifier = ErrorClassifier()

    def preflight(self) -> None:
        resolved = shutil.which(self.cli_cmd)
        if not resolved:
            raise ProviderError(self.name, ErrorCategory.AUTH_ERROR, f"CLI not found: {self.cli_cmd}")
        self._resolved_cmd = resolved

    def build_command(self, prompt: str, model: str, max_output_tokens: int) -> list[str]:
        """Override per provider if you want real execution.

        Default is a placeholder that will always fail unless overridden.
        """
        return [self.cli_cmd, "--help"]

    def run(self, prompt: str, model: str, timeout_seconds: int, max_output_tokens: int) -> ProviderResponse:
        self.preflight()
        cmd = self.build_command(prompt=prompt, model=model, max_output_tokens=max_output_tokens)
        start = time.time()

        # On Windows, many CLIs are distributed as .cmd shims (npm). Those cannot be executed
        # directly via CreateProcess without going through `cmd.exe /c`.
        run_cmd: list[str]
        if self._resolved_cmd and self._resolved_cmd.lower().endswith((".cmd", ".bat")):
            run_cmd = ["cmd.exe", "/c"] + cmd
        else:
            run_cmd = cmd

        try:
            p = subprocess.run(
                run_cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired as e:
            self._last_err = str(e)
            raise ProviderError(self.name, ErrorCategory.TRANSIENT_NETWORK, "timeout", raw=self._last_err)

        latency_ms = int((time.time() - start) * 1000)
        out = (p.stdout or "").strip()
        err = (p.stderr or "").strip()
        self._last_err = err or out

        if p.returncode != 0:
            cat = self._classifier.classify(err or out)
            raise ProviderError(self.name, cat, "provider execution failed", raw=err or out)

        # Many official CLIs print progress/status to stderr; only treat stdout as the answer.
        if not out and err:
            # If a CLI returns 0 but only prints to stderr, classify and failover conservatively.
            cat = self._classifier.classify(err)
            raise ProviderError(self.name, cat if cat != ErrorCategory.UNKNOWN else ErrorCategory.UNKNOWN, "empty stdout", raw=err)

        return ProviderResponse(text=out, model=model, degraded=False, latency_ms=latency_ms)

    def last_raw_error(self) -> str | None:
        return self._last_err
