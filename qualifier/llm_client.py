"""
LLM access layer: providers + retry/backoff + rate limiting.

DESIGN: every provider exposes ONE method, `complete(system, user) -> str`.
The rest of the system never knows which vendor it's talking to, so switching
from Groq to Gemini is a config change, and tests can plug in a fake provider.

Errors are sorted into three kinds, because each needs a different reaction:
  TransientLLMError  - 429 rate limit, 5xx, timeout, network blip -> wait and retry
  PermanentLLMError  - bad API key, bad request, unknown model    -> don't retry; stop
  InvalidResponseError - call worked but the text isn't usable     -> handled by judge.py
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
import socket
import threading
import time
import urllib.error
import urllib.request
from typing import Callable, Optional

log = logging.getLogger("lead_qualifier.llm")


# ---------------------------------------------------------------------------
# Error types
# ---------------------------------------------------------------------------

class LLMError(Exception):
    pass


class TransientLLMError(LLMError):
    def __init__(self, message: str, retry_after: Optional[float] = None):
        super().__init__(message)
        self.retry_after = retry_after


class PermanentLLMError(LLMError):
    pass


class InvalidResponseError(LLMError):
    pass


RETRYABLE_STATUS = {408, 409, 425, 429, 500, 502, 503, 504, 529}


# ---------------------------------------------------------------------------
# Retry with exponential backoff + jitter, and a simple rate limiter
# ---------------------------------------------------------------------------

class CallStats:
    """Counters that end up in the report, so robustness is visible, not claimed."""
    def __init__(self):
        self.api_calls = 0
        self.retries = 0
        self.transient_errors = 0
        self.permanent_errors = 0
        self.invalid_responses = 0
        self.total_wait_seconds = 0.0

    def to_dict(self) -> dict:
        return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in vars(self).items()}


class RateLimiter:
    """Guarantees at least 60/rpm seconds between calls (client-side throttle).
    Cheaper than hitting the provider's limit and being told to back off."""
    def __init__(self, requests_per_minute: float, clock=time.monotonic, sleep=time.sleep):
        self.min_interval = 60.0 / requests_per_minute if requests_per_minute > 0 else 0.0
        self._last = None
        self._lock = threading.Lock()
        self._clock, self._sleep = clock, sleep

    def wait(self) -> float:
        with self._lock:
            waited = 0.0
            if self._last is not None and self.min_interval:
                waited = max(0.0, self.min_interval - (self._clock() - self._last))
                if waited:
                    self._sleep(waited)
            self._last = self._clock()
            return waited


def call_with_retry(fn: Callable[[], str], *, max_retries: int, base_delay: float, max_delay: float,
                    stats: CallStats, sleep: Callable[[float], None] = time.sleep,
                    rng: random.Random | None = None) -> str:
    """
    Run fn(); on TransientLLMError retry up to max_retries times.

    Delay for attempt n (0-based) = min(max_delay, base_delay * 2**n), then
    "full jitter" (a random value between 50% and 100% of it) so that many
    clients that failed together don't all retry at the same instant. If the
    server sent Retry-After, we respect it instead.
    """
    rng = rng or random.Random()
    attempt = 0
    while True:
        try:
            stats.api_calls += 1
            return fn()
        except TransientLLMError as e:
            stats.transient_errors += 1
            if attempt >= max_retries:
                log.error("Giving up after %d retries: %s", max_retries, e)
                raise
            delay = min(max_delay, base_delay * (2 ** attempt)) * rng.uniform(0.5, 1.0)
            if e.retry_after is not None:
                delay = min(max_delay, max(delay, e.retry_after))
            log.warning("Transient LLM error (%s) - retry %d/%d in %.1fs", e, attempt + 1, max_retries, delay)
            stats.retries += 1
            stats.total_wait_seconds += delay
            sleep(delay)
            attempt += 1
        except PermanentLLMError:
            stats.permanent_errors += 1
            raise


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------

class Provider:
    name = "base"

    def __init__(self, model: str = "", timeout: float = 90, max_output_tokens: int = 8000):
        self.model = model
        self.timeout = timeout
        self.max_output_tokens = max_output_tokens

    def complete(self, system: str, user: str) -> str:  # pragma: no cover - interface
        raise NotImplementedError


def _require_key(env_var: str, provider: str) -> str:
    key = os.environ.get(env_var, "").strip()
    if not key:
        raise PermanentLLMError(f"{env_var} is not set. Add it to your environment or .env file to use provider '{provider}'.")
    return key


def _post_json(url: str, headers: dict, body: dict, timeout: float) -> dict:
    """POST JSON with the standard library and map failures to our error types."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:300]
        retry_after = None
        if e.headers and e.headers.get("Retry-After"):
            try:
                retry_after = float(e.headers["Retry-After"])
            except ValueError:
                pass
        if e.code in RETRYABLE_STATUS:
            raise TransientLLMError(f"HTTP {e.code}: {detail}", retry_after) from e
        raise PermanentLLMError(f"HTTP {e.code}: {detail}") from e
    except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
        raise TransientLLMError(f"network error: {e}") from e
    except json.JSONDecodeError as e:
        raise InvalidResponseError(f"provider returned non-JSON HTTP body: {e}") from e


class OpenAICompatibleProvider(Provider):
    """Works for OpenAI and Groq (Groq exposes an OpenAI-compatible endpoint)."""

    def __init__(self, name: str, base_url: str, key_env: str, **kw):
        super().__init__(**kw)
        self.name, self.base_url, self.key_env = name, base_url, key_env

    def complete(self, system: str, user: str) -> str:
        key = _require_key(self.key_env, self.name)
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.2,                         # low = more consistent judgments
            "max_tokens": self.max_output_tokens,
            "response_format": {"type": "json_object"},  # ask the API to guarantee JSON
        }
        resp = _post_json(f"{self.base_url}/chat/completions", {"Authorization": f"Bearer {key}"}, body, self.timeout)
        try:
            choice = resp["choices"][0]
            if choice.get("finish_reason") == "length":
                raise InvalidResponseError("response truncated (hit max_tokens)")
            return choice["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise InvalidResponseError(f"unexpected response shape: {str(resp)[:200]}") from e


class GeminiProvider(Provider):
    name = "gemini"

    def complete(self, system: str, user: str) -> str:
        key = _require_key("GEMINI_API_KEY", self.name)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"
        body = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": self.max_output_tokens,
                                 "responseMimeType": "application/json"},
        }
        resp = _post_json(url, {"x-goog-api-key": key}, body, self.timeout)
        try:
            cand = resp["candidates"][0]
            if cand.get("finishReason") == "MAX_TOKENS":
                raise InvalidResponseError("response truncated (hit maxOutputTokens)")
            return "".join(p.get("text", "") for p in cand["content"]["parts"])
        except (KeyError, IndexError, TypeError) as e:
            raise InvalidResponseError(f"unexpected response shape: {str(resp)[:200]}") from e


class MockProvider(Provider):
    """
    Offline stand-in for an LLM so the whole pipeline runs with no API key.
    It returns well-formed JSON with NO score adjustment, and leaves messages
    empty so the deterministic templates are used. Use it to test plumbing,
    never to judge the quality of LLM output.
    """
    name = "mock"

    def complete(self, system: str, user: str) -> str:
        leads = json.loads(user.split("LEADS_JSON:", 1)[1].strip())
        return json.dumps({"results": [{
            "lead_id": l["lead_id"],
            "adjustment": 0,
            "adjustment_reason": "Mock provider: no LLM judgment applied.",
            "confidence": "medium",
            "summary": f"{l.get('company') or 'Unknown company'}: rubric score {l['rubric']['base_score']}/10.",
            "outreach_message": None,
        } for l in leads]})


class ChaosProvider(Provider):
    """
    Wraps a real provider and injects failures at a given rate, to PROVE the
    error handling works: rate limits, server errors, garbage text, truncated
    JSON, and responses that silently drop a lead.
    """
    name = "chaos"

    def __init__(self, inner: Provider, failure_rate: float, seed: int = 7):
        super().__init__(model=inner.model)
        self.inner, self.failure_rate, self.rng = inner, failure_rate, random.Random(seed)
        self.name = f"{inner.name}+chaos"

    def complete(self, system: str, user: str) -> str:
        if self.rng.random() < self.failure_rate:
            kind = self.rng.choice(["rate_limit", "server_error", "timeout", "garbage", "truncated", "drop_lead"])
            log.debug("Chaos: injecting %s", kind)
            if kind == "rate_limit":
                raise TransientLLMError("HTTP 429 (simulated)", retry_after=0.1)
            if kind == "server_error":
                raise TransientLLMError("HTTP 503 (simulated)")
            if kind == "timeout":
                raise TransientLLMError("timeout (simulated)")
            out = self.inner.complete(system, user)
            if kind == "garbage":
                return "Sure! Here are my thoughts on these leads: they all look great."
            if kind == "truncated":
                return out[: len(out) // 2]
            data = json.loads(out)
            data["results"] = data["results"][1:]   # silently drop the first lead
            return json.dumps(data)
        return self.inner.complete(system, user)


def build_provider(llm_cfg: dict, provider: Optional[str] = None, model: Optional[str] = None) -> Provider:
    name = (provider or llm_cfg.get("provider") or "mock").lower()
    model = model or llm_cfg.get("models", {}).get(name, "")
    common = dict(model=model, timeout=llm_cfg.get("timeout_seconds", 90),
                  max_output_tokens=llm_cfg.get("max_output_tokens", 8000))
    if name == "mock":
        return MockProvider(**{**common, "model": "mock"})
    if name == "groq":
        return OpenAICompatibleProvider("groq", "https://api.groq.com/openai/v1", "GROQ_API_KEY", **common)
    if name == "openai":
        return OpenAICompatibleProvider("openai", "https://api.openai.com/v1", "OPENAI_API_KEY", **common)
    if name == "gemini":
        return GeminiProvider(**common)
    raise ValueError(f"Unknown provider '{name}'. Choose: mock, groq, gemini, openai")


def load_dotenv(path: str = ".env") -> None:
    """Tiny .env reader (KEY=value lines) so we don't need python-dotenv.
    Existing environment variables win over the file."""
    if not os.path.exists(path):
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$", line)
            if m and not line.lstrip().startswith("#"):
                os.environ.setdefault(m.group(1), m.group(2).strip("'\""))
