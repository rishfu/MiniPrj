"""
Stage 2b - ANALYZE (LLM): send leads to the LLM in batches and validate what comes back.

Failure strategy, from cheapest to most drastic:

  1. Retry with backoff        (llm_client.call_with_retry) - for 429/5xx/timeouts
  2. Re-ask for missing leads   - the reply was valid but skipped some lead_ids
  3. Split the batch in half    - a bad/garbled/truncated reply for 10 leads is
                                  often fine for 5 (shorter output, less to go wrong)
  4. Rule-only fallback per lead - score = rubric only, template message, flagged
  5. Circuit breaker            - after N whole batches in a row got nothing from
                                  the LLM (or on a bad API key), stop calling the
                                  API for the rest of the run instead of burning
                                  minutes on retries

  Splitting (3) is only used for UNUSABLE RESPONSES. For outages (retries
  exhausted) splitting would just multiply calls to a service that is down.

Whatever happens, every lead leaves this stage with a judgment, and the
report records which ones came from the LLM and which from the fallback.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Callable

from .llm_client import (CallStats, InvalidResponseError, PermanentLLMError, Provider, RateLimiter,
                         TransientLLMError, call_with_retry)
from .models import LLMJudgment

log = logging.getLogger("lead_qualifier.judge")

VALID_CONFIDENCE = {"high", "medium", "low"}


def extract_json(text: str):
    """Models sometimes wrap JSON in ```fences``` or add a sentence before it."""
    if not text or not text.strip():
        raise InvalidResponseError("empty response")
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.IGNORECASE)
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    start, end = t.find("{"), t.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(t[start:end + 1])
        except json.JSONDecodeError:
            pass
    raise InvalidResponseError(f"could not parse JSON from response: {text[:120]!r}")


def parse_results(text: str, expected_ids: set[str], max_abs: float, step: float, source: str) -> dict[str, LLMJudgment]:
    """Validate the reply item by item. Bad items are dropped (and re-asked later), not trusted."""
    data = extract_json(text)
    items = data.get("results") if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise InvalidResponseError("JSON has no 'results' list")

    out: dict[str, LLMJudgment] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        lid = str(item.get("lead_id", "")).strip()
        if lid not in expected_ids:
            log.warning("LLM returned unknown lead_id %r - ignored", lid)
            continue
        try:
            adj = float(item.get("adjustment", 0) or 0)
        except (TypeError, ValueError):
            adj = 0.0
        # Guardrail 1: clamp to +/-max_abs and snap to the allowed step.
        clamped = max(-max_abs, min(max_abs, round(adj / step) * step))
        if clamped != adj:
            log.info("%s: LLM adjustment %s clamped to %s", lid, adj, clamped)
        reason = str(item.get("adjustment_reason") or "").strip()
        # Guardrail 2: no unexplained adjustments.
        if clamped != 0 and not reason:
            log.info("%s: adjustment %s had no reason - ignored", lid, clamped)
            clamped = 0.0
        conf = str(item.get("confidence", "medium")).lower().strip()
        msg = item.get("outreach_message")
        out[lid] = LLMJudgment(
            adjustment=clamped, adjustment_reason=reason,
            confidence=conf if conf in VALID_CONFIDENCE else "medium",
            summary=str(item.get("summary") or "").strip(),
            outreach_message=msg.strip() if isinstance(msg, str) and msg.strip() else None,
            source=source,
        )
    if not out:
        raise InvalidResponseError("response contained no valid results for this batch")
    return out


class BatchJudge:
    def __init__(self, provider: Provider, llm_cfg: dict, adj_cfg: dict, system_prompt: str,
                 build_user_prompt: Callable[[list[dict]], str], sleep=None):
        self.provider = provider
        self.cfg = llm_cfg
        self.max_abs, self.step = adj_cfg["max_abs"], adj_cfg["step"]
        self.system_prompt = system_prompt
        self.build_user_prompt = build_user_prompt
        self.stats = CallStats()
        self.limiter = RateLimiter(llm_cfg.get("requests_per_minute", 0), **({"sleep": sleep} if sleep else {}))
        self.sleep = sleep
        self.consecutive_failures = 0
        self.circuit_open = False
        self.circuit_reason = ""
        self.batches_sent = 0
        self.batch_splits = 0
        self.fallback_reasons: dict[str, str] = {}
        self.source_label = "mock" if provider.name.startswith("mock") else "llm"

    # -- public ---------------------------------------------------------------

    def judge_all(self, payloads: list[dict]) -> dict[str, LLMJudgment]:
        size = max(1, int(self.cfg.get("batch_size", 10)))
        results: dict[str, LLMJudgment] = {}
        batches = [payloads[i:i + size] for i in range(0, len(payloads), size)]
        for n, batch in enumerate(batches, 1):
            log.info("Batch %d/%d: %d leads", n, len(batches), len(batch))
            got = self._judge_batch(batch)
            results.update(got)
            # Circuit breaker counts whole batches that got NOTHING from the LLM,
            # so one bad batch that recovered after a split doesn't trip it.
            if all(j.source == "fallback" for j in got.values()):
                self.consecutive_failures += 1
                if not self.circuit_open and self.consecutive_failures >= self.cfg.get("circuit_breaker_failures", 3):
                    self.circuit_open, self.circuit_reason = True, f"{self.consecutive_failures} batches in a row failed"
                    log.error("Circuit breaker opened: %s - remaining leads use rule-only scoring", self.circuit_reason)
            else:
                self.consecutive_failures = 0
        return results

    # -- internals ------------------------------------------------------------

    def _fallback(self, batch: list[dict], why: str) -> dict[str, LLMJudgment]:
        for p in batch:
            self.fallback_reasons[p["lead_id"]] = why
        log.warning("Rule-only fallback for %d lead(s): %s", len(batch), why)
        return {p["lead_id"]: LLMJudgment(source="fallback", confidence="medium",
                                          adjustment_reason="", note=f"LLM unavailable: {why}")
                for p in batch}

    def _call(self, batch: list[dict]) -> dict[str, LLMJudgment]:
        user = self.build_user_prompt(batch)
        kwargs = dict(max_retries=self.cfg.get("max_retries", 4),
                      base_delay=self.cfg.get("base_delay_seconds", 2.0),
                      max_delay=self.cfg.get("max_delay_seconds", 30.0), stats=self.stats)
        if self.sleep:
            kwargs["sleep"] = self.sleep

        def once():
            self.limiter.wait()
            return self.provider.complete(self.system_prompt, user)

        self.batches_sent += 1
        text = call_with_retry(once, **kwargs)
        return parse_results(text, {p["lead_id"] for p in batch}, self.max_abs, self.step, self.source_label)

    def _judge_batch(self, batch: list[dict], depth: int = 0) -> dict[str, LLMJudgment]:
        if self.circuit_open:
            return self._fallback(batch, f"circuit breaker open ({self.circuit_reason})")
        try:
            got = self._call(batch)
        except PermanentLLMError as e:
            # Bad key / unknown model: retrying or splitting can't fix this.
            self.circuit_open, self.circuit_reason = True, f"permanent error: {e}"
            log.error("Permanent LLM error - disabling LLM for the rest of the run: %s", e)
            return self._fallback(batch, str(e))
        except TransientLLMError as e:
            # Retries are already exhausted: the API is struggling. Splitting would
            # only multiply calls to a service that is down, so fall back.
            log.warning("Batch of %d failed after retries: %s", len(batch), e)
            return self._fallback(batch, f"API unavailable after retries: {e}")
        except InvalidResponseError as e:
            # The API answered but the text was unusable (garbled, truncated,
            # refused). A smaller request is shorter and often succeeds.
            self.stats.invalid_responses += 1
            log.warning("Batch of %d returned an unusable response: %s", len(batch), e)
            if len(batch) > 1 and depth < 3:
                self.batch_splits += 1
                mid = len(batch) // 2
                log.info("Splitting batch into %d + %d and retrying", mid, len(batch) - mid)
                return {**self._judge_batch(batch[:mid], depth + 1), **self._judge_batch(batch[mid:], depth + 1)}
            return self._fallback(batch, f"unusable LLM response: {e}")
        except Exception as e:  # noqa: BLE001 - last line of defence
            # A bug or an unexpected library error must not crash a 100-lead run.
            # Log the full traceback, fall back for this batch, keep going.
            log.exception("Unexpected error while judging a batch of %d", len(batch))
            return self._fallback(batch, f"unexpected error: {type(e).__name__}: {e}")

        missing = [p for p in batch if p["lead_id"] not in got]
        if missing:
            log.warning("LLM skipped %d lead(s): %s - asking again", len(missing), [p["lead_id"] for p in missing])
            if depth < 3:
                got.update(self._judge_batch(missing, depth + 1))
            else:
                got.update(self._fallback(missing, "LLM repeatedly omitted these leads"))
        return got
