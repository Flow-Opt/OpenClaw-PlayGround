from __future__ import annotations

from dataclasses import dataclass

from .classifier import ErrorClassifier
from .config import Config
from .errors import ErrorCategory, ProviderError
from .logging import JsonlLogger, LogEvent, now_ts
from .providers.base import Provider, ProviderResponse


@dataclass
class RouteDecision:
    provider: str
    model: str
    degraded: bool


class Router:
    def __init__(self, cfg: Config, providers: dict[str, Provider], logger: JsonlLogger):
        self.cfg = cfg
        self.providers = providers
        self.logger = logger
        self.classifier = ErrorClassifier()

    def _should_failover(self, err: ProviderError) -> bool:
        return err.category in {
            ErrorCategory.RATE_LIMITED,
            ErrorCategory.QUOTA_EXHAUSTED,
            ErrorCategory.TRANSIENT_NETWORK,
            ErrorCategory.AUTH_ERROR,
        }

    def _pick_model(self, provider_name: str, near_limit: bool) -> tuple[str, bool]:
        pcfg = self.cfg.providers.get(provider_name)
        primary = (pcfg.model_primary if pcfg else None) or ""
        degraded_model = (pcfg.model_degraded if pcfg else None) or primary

        if self.cfg.router.degrade_enabled and near_limit and degraded_model:
            return degraded_model, True

        return primary or degraded_model or "", False

    def run(self, prompt: str, *, force_provider: str | None = None, verbose: bool = False, log_prompts: bool = False, max_output_tokens: int | None = None) -> ProviderResponse:
        ordered = [force_provider] if force_provider else list(self.cfg.router.providers)

        last_limit_like = False
        last_error: ProviderError | None = None

        for i, p_name in enumerate(ordered):
            if not p_name:
                continue
            provider = self.providers.get(p_name)
            if not provider:
                continue

            # Near-limit heuristic: if previous provider hit rate/quota, degrade next attempt.
            model, degraded = self._pick_model(p_name, near_limit=last_limit_like)
            out_tokens = max_output_tokens or (self.cfg.router.degrade_max_output_tokens if degraded else 1200)

            self.logger.write(
                LogEvent(
                    ts=now_ts(),
                    kind="attempt",
                    provider=p_name,
                    model=model,
                    degraded=degraded,
                    reason=("degraded_after_limit" if degraded else None),
                    prompt=prompt if log_prompts else None,
                )
            )

            try:
                resp = provider.run(prompt=prompt, model=model, timeout_seconds=self.cfg.router.timeout_seconds, max_output_tokens=out_tokens)
                resp.degraded = degraded
                self.logger.write(
                    LogEvent(
                        ts=now_ts(),
                        kind="success",
                        provider=p_name,
                        model=model,
                        latency_ms=resp.latency_ms,
                        degraded=degraded,
                    )
                )
                return resp
            except ProviderError as e:
                last_error = e
                cat = e.category

                self.logger.write(
                    LogEvent(
                        ts=now_ts(),
                        kind="error",
                        provider=p_name,
                        model=model,
                        degraded=degraded,
                        error_category=cat.value,
                        error_message=e.raw or e.message,
                        reason="failover" if (i < len(ordered) - 1) else "final",
                    )
                )

                if verbose:
                    print(f"[{p_name}] {cat.value}: {e.message}")

                last_limit_like = cat in {ErrorCategory.RATE_LIMITED, ErrorCategory.QUOTA_EXHAUSTED}

                if force_provider:
                    raise
                if self._should_failover(e):
                    continue
                raise

        # If we got here, we failed across all providers.
        if last_error and last_error.category in {ErrorCategory.RATE_LIMITED, ErrorCategory.QUOTA_EXHAUSTED}:
            raise ProviderError(
                provider="router",
                category=ErrorCategory.QUOTA_EXHAUSTED,
                message="All providers are currently at usage limits. Try again later or reduce request size.",
            )

        raise ProviderError(
            provider="router",
            category=ErrorCategory.UNKNOWN,
            message="All providers failed. Try again later or check provider auth/health.",
        )
