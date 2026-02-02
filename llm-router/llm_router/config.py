from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ProviderConfig:
    mode: str
    cli_cmd: str | None = None
    model_primary: str | None = None
    model_degraded: str | None = None


@dataclass
class RouterConfig:
    providers: list[str]
    routing_policy: str
    log_dir: str
    log_prompts: bool
    timeout_seconds: int
    degrade_enabled: bool
    degrade_max_output_tokens: int


@dataclass
class Config:
    router: RouterConfig
    providers: dict[str, ProviderConfig]


def default_config_path() -> Path:
    # Windows and Unix both handle ~.
    return Path(os.path.expanduser("~/.llm-router/config.yml"))


def load_config(path: str | None) -> Config:
    cfg_path = Path(path) if path else default_config_path()
    if not cfg_path.exists():
        # Minimal defaults; user can create config later.
        router = RouterConfig(
            providers=["openai_codex", "google_gemini"],
            routing_policy="failover_then_degrade",
            log_dir="~/.llm-router/logs",
            log_prompts=False,
            timeout_seconds=120,
            degrade_enabled=True,
            degrade_max_output_tokens=800,
        )
        providers = {
            "openai_codex": ProviderConfig(mode="cli", cli_cmd="codex", model_primary="gpt-5-codex", model_degraded="gpt-5-codex-mini"),
            "google_gemini": ProviderConfig(mode="cli", cli_cmd="gemini", model_primary="gemini-2.0-flash", model_degraded="gemini-2.0-flash-lite"),
            # Claude is supported but disabled by default until the local CLI runs reliably in your environment.
            # "anthropic_claude": ProviderConfig(mode="cli", cli_cmd="claude", model_primary="claude-3-7-sonnet", model_degraded="claude-3-5-haiku"),
        }
        return Config(router=router, providers=providers)

    data: dict[str, Any] = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

    r = data.get("router", {})
    router = RouterConfig(
        providers=list(r.get("providers", ["openai_codex", "anthropic_claude", "google_gemini"])),
        routing_policy=str(r.get("routing_policy", "failover_then_degrade")),
        log_dir=str(r.get("log_dir", "~/.llm-router/logs")),
        log_prompts=bool(r.get("log_prompts", False)),
        timeout_seconds=int(r.get("timeouts", {}).get("provider_seconds", r.get("timeout_seconds", 120))),
        degrade_enabled=bool(r.get("degrade", {}).get("enabled", True)),
        degrade_max_output_tokens=int(r.get("degrade", {}).get("max_output_tokens", 800)),
    )

    providers: dict[str, ProviderConfig] = {}
    for name, p in data.items():
        if name == "router":
            continue
        if not isinstance(p, dict):
            continue
        providers[name] = ProviderConfig(
            mode=str(p.get("mode", "cli")),
            cli_cmd=p.get("cli_cmd"),
            model_primary=p.get("model_primary"),
            model_degraded=p.get("model_degraded"),
        )

    # Ensure entries exist for ordered providers.
    for n in router.providers:
        providers.setdefault(n, ProviderConfig(mode="cli"))

    return Config(router=router, providers=providers)
