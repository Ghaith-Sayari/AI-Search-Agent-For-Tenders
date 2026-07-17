"""Optional LangSmith wiring for Gatekeeper tracing."""

from __future__ import annotations

import os
from typing import Any, Callable

from agents.gatekeeper.classifiers.settings import GatekeeperSettings

try:
    from langsmith import traceable as _langsmith_traceable
except Exception:  # pragma: no cover - optional dependency
    _langsmith_traceable = None


def traceable(*args: Any, **kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Return a LangSmith traceable decorator when available, else a no-op."""
    if _langsmith_traceable is None:
        def _noop_decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func
        return _noop_decorator

    return _langsmith_traceable(*args, **kwargs)


def configure_langsmith(settings: GatekeeperSettings) -> None:
    """Hydrate LangSmith env vars from Gatekeeper settings when tracing is enabled."""
    if not settings.langsmith_tracing:
        return

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ.setdefault("LANGSMITH_PROJECT", settings.langsmith_project)

    if settings.langsmith_endpoint:
        os.environ.setdefault("LANGSMITH_ENDPOINT", settings.langsmith_endpoint)

    if settings.langsmith_api_key:
        os.environ.setdefault("LANGSMITH_API_KEY", settings.langsmith_api_key)
