from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .redact import redact


@dataclass
class LogEvent:
    ts: float
    kind: str
    provider: str | None = None
    model: str | None = None
    latency_ms: int | None = None
    degraded: bool | None = None
    error_category: str | None = None
    error_message: str | None = None
    reason: str | None = None
    prompt: str | None = None  # only if explicitly enabled


class JsonlLogger:
    def __init__(self, log_dir: str, log_prompts: bool = False):
        self.log_prompts = log_prompts
        expanded = os.path.expandvars(os.path.expanduser(log_dir))
        self.log_dir = Path(expanded)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.log_dir / "router.jsonl"

    def write(self, event: LogEvent) -> None:
        d: dict[str, Any] = asdict(event)
        if not self.log_prompts:
            d.pop("prompt", None)
        else:
            if d.get("prompt"):
                d["prompt"] = redact(str(d["prompt"]))

        # Always redact error message.
        if d.get("error_message"):
            d["error_message"] = redact(str(d["error_message"]))

        line = json.dumps(d, ensure_ascii=False)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(line + "\n")


def now_ts() -> float:
    return time.time()
