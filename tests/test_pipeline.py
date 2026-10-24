"""
Tests for each stage plus end-to-end runs. Standard library only:

    python -m unittest discover -s tests -v
"""

import copy
import json
import logging
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from qualifier.decide import decide  # noqa: E402
from qualifier.ingest import (apply_reference_date, clean_text, load_leads, parse_company_size,  # noqa: E402
                              parse_date, resolve_reference_date)
from qualifier.judge import BatchJudge, extract_json, parse_results  # noqa: E402
from qualifier.llm_client import (CallStats, InvalidResponseError, MockProvider, PermanentLLMError,  # noqa: E402
                                  Provider, TransientLLMError, call_with_retry)
from qualifier.models import Lead, LLMJudgment  # noqa: E402
from qualifier.pipeline import run  # noqa: E402
from qualifier.rubric import Rubric  # noqa: E402

CONFIG = yaml.safe_load(open(ROOT / "config.yaml", encoding="utf-8"))
CONFIG["llm"]["provider"] = "mock"   # tests never call a real API
REF = date(2024, 1, 20)
logging.disable(logging.CRITICAL)


def make_lead(**kw) -> Lead:
    base = dict(lead_id="L001", row_number=2, name="Alice Chen", company="CloudScale AI", company_size=50,
                industry="SaaS", source="Inbound demo request", last_interaction=date(2024, 1, 15))
    base.update(kw)
    return Lead(**base)


class TestIngest(unittest.TestCase):
    def test_missing_tokens_and_placeholders(self):
        self.assertEqual(clean_text("  NA "), (None, None))
        self.assertEqual(clean_text(""), (None, None))
        value, issue = clean_text("Unknown Source")
        self.assertIsNone(value)
        self.assertIn("placeholder", issue)
        self.assertEqual(clean_text("  saas  ")[0], "saas")

    def test_company_size_parsing(self):
        self.assertEqual(parse_company_size("1,200")[0], 1200)
        self.assertEqual(parse_company_size("25-50")[0], 38)
        self.assertEqual(parse_company_size("5k")[0], 5000)
        self.assertEqual(parse_company_size("NA"), (None, None))
        self.assertIsNone(parse_company_size("abc")[0])
        self.assertIsNone(parse_company_size("0")[0])

    def test_date_parsing(self):
        self.assertEqual(parse_date("2024-01-15"), (date(2024, 1, 15), None))
        d, issue = parse_date("01/15/2024")
        self.assertEqual(d, date(2024, 1, 15))
        self.assertIn("non-standard", issue)
        self.assertIsNone(parse_date("2024-13-45")[0])

    def test_testing_file_loads_without_crash(self):
        leads, stats = load_leads(ROOT / "data" / "leads_testing.csv")
        self.assertEqual(len(leads), 20)
        missing_size = next(l for l in leads if l.name == "Test_MissingSize")
        self.assertIsNone(missing_size.company_size)
        name_only = next(l for l in leads if l.name == "Test_NameOnly")
        self.assertIsNone(name_only.industry)

    def test_duplicates_flagged(self):
        leads, stats = load_leads(ROOT / "data" / "leads_edge_cases_extra.csv")
        self.assertEqual(stats["duplicates"], 1)
        self.assertTrue(any(l.duplicate_of for l in leads))

    def test_reference_date_ignores_outlier_and_future_dates_dropped(self):
        leads, _ = load_leads(ROOT / "data" / "leads_edge_cases_extra.csv")
        ref = resolve_reference_date(leads, "auto")
        self.assertEqual(ref, REF)                 # the 2025 typo doesn't become "today"
        apply_reference_date(leads, ref)
        future = next(l for l in leads if l.company == "Future Date Co")
        self.assertIsNone(future.last_interaction)

    def test_missing_column_degrades_gracefully(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("name,company,industry\nAlice,CloudScale,SaaS\n")
        leads, stats = load_leads(f.name)
        self.assertEqual(len(leads), 1)
        self.assertIn("company_size", stats["missing_columns"])


class TestRubric(unittest.TestCase):
    def setUp(self):
        self.rubric = Rubric(CONFIG["rubric"])

    def test_ideal_lead_scores_high(self):
        r = self.rubric.score(make_lead(company_size=200, last_interaction=date(2024, 1, 19)), REF)
        self.assertEqual(r.base_score, 10.0)

    def test_scores_are_deterministic(self):
        lead = make_lead()
        self.assertEqual(self.rubric.score(lead, REF).base_score, self.rubric.score(lead, REF).base_score)

    def test_industry_normalisation(self):
        self.assertEqual(self.rubric.industry_tier("NonProfit"), "low")
        self.assertEqual(self.rubric.industry_tier("non-profit"), "low")
        self.assertEqual(self.rubric.industry_tier("  saas "), "core")
        self.assertEqual(self.rubric.industry_tier("Space Mining"), "unmapped")

    def test_missing_values_use_defaults_and_are_marked(self):
        r = self.rubric.score(make_lead(company_size=None, source=None), REF)
        self.assertTrue(r.factor("company_size").is_default)
        self.assertTrue(r.factor("intent_signal").is_default)

    def test_caps(self):
        self.assertEqual([c["rule"] for c in self.rubric.score(make_lead(company_size=3), REF).caps], ["micro_company"])
        stale = self.rubric.score(make_lead(last_interaction=date(2022, 6, 15)), REF)
        self.assertEqual([c["rule"] for c in stale.caps], ["stale_contact"])


class TestDecide(unittest.TestCase):
    def setUp(self):
        self.rubric = Rubric(CONFIG["rubric"])

    def _decide(self, lead, adj=0.0, conf="high", reason="x"):
        return decide(lead, self.rubric.score(lead, REF), LLMJudgment(adjustment=adj, adjustment_reason=reason,
                                                                      confidence=conf, source="llm"), CONFIG["rubric"])

    def test_qualified(self):
        self.assertEqual(self._decide(make_lead()).decision, "qualified")

    def test_llm_cannot_break_cap(self):
        d = self._decide(make_lead(company_size=3), adj=1.0)
        self.assertLessEqual(d.final_score, 6.0)
        self.assertNotEqual(d.decision, "qualified")

    def test_low_confidence_goes_to_review(self):
        self.assertEqual(self._decide(make_lead(), conf="low").decision, "review")

    def test_missing_company_goes_to_review(self):
        lead = make_lead(company=None)
        lead.add_issue("company", "missing company", "critical")
        self.assertEqual(self._decide(lead).decision, "review")

    def test_could_qualify_if_unknown_is_favourable(self):
        # Scores 4.5 (rejected) with an unknown source - but a demo request would make it 7.25.
        # Don't reject on a guess: send it to a human.
        lead = make_lead(company_size=200, industry="Government", source=None, last_interaction=date(2023, 12, 11))
        self.assertEqual(self.rubric.score(lead, REF).base_score, 4.5)
        self.assertEqual(self._decide(lead).decision, "review")

    def test_unknown_that_cannot_change_outcome_stays_qualified(self):
        # Missing size, but even the worst size (0.5) keeps it at 8.0 -> still qualified.
        self.assertEqual(self._decide(make_lead(company_size=None)).decision, "qualified")

    def test_display_rounding_is_half_up(self):
        self.assertEqual(self._decide(make_lead()).final_score, 9.3)   # 9.25 -> 9.3, not 9.2

    def test_rejected_has_reasons(self):
        d = self._decide(make_lead(company_size=6, industry="Agriculture", source="Content download",
                                   last_interaction=date(2023, 9, 1)))
        self.assertEqual(d.decision, "rejected")
        self.assertGreater(len(d.decision_reasons), 1)


class TestResponseParsing(unittest.TestCase):
    def test_fenced_json(self):
        self.assertEqual(extract_json('```json\n{"results": []}\n```'), {"results": []})

    def test_json_with_preamble(self):
        self.assertEqual(extract_json('Here you go: {"results": []} hope it helps'), {"results": []})

    def test_inline_thinking_is_stripped(self):
        self.assertEqual(extract_json('<think>hmm, L001 looks good</think>\n{"results": []}'), {"results": []})

    def test_garbage_raises(self):
        with self.assertRaises(InvalidResponseError):
            extract_json("Sure, these leads all look great!")

    def test_adjustment_clamped_snapped_and_needs_reason(self):
        text = json.dumps({"results": [
            {"lead_id": "L001", "adjustment": 5, "adjustment_reason": "huge", "confidence": "high"},
            {"lead_id": "L002", "adjustment": 0.3, "adjustment_reason": "small", "confidence": "weird"},
            {"lead_id": "L003", "adjustment": 1, "adjustment_reason": ""},
            {"lead_id": "L999", "adjustment": 1, "adjustment_reason": "not in batch"},
        ]})
        out = parse_results(text, {"L001", "L002", "L003"}, 1.0, 0.5, "llm")
        self.assertEqual(out["L001"].adjustment, 1.0)      # clamped
        self.assertEqual(out["L002"].adjustment, 0.5)      # snapped to step
        self.assertEqual(out["L002"].confidence, "medium")  # invalid -> default
        self.assertEqual(out["L003"].adjustment, 0.0)      # no reason -> ignored
        self.assertNotIn("L999", out)


class FlakyProvider(Provider):
    """Fails N times, then behaves like the mock."""
    name = "flaky"

    def __init__(self, failures, exc):
        super().__init__(model="flaky")
        self.failures, self.exc, self.calls, self.inner = failures, exc, 0, MockProvider()

    def complete(self, system, user):
        self.calls += 1
        if self.calls <= self.failures:
            raise self.exc
        return self.inner.complete(system, user)


class TestHttpErrorMapping(unittest.TestCase):
    def _raise(self, code, body):
        import io
        import urllib.error
        from unittest import mock
        from qualifier.llm_client import _post_json
        err = urllib.error.HTTPError("http://x", code, "err", {}, io.BytesIO(body.encode()))
        with mock.patch("urllib.request.urlopen", side_effect=err):
            _post_json("http://x", {}, {}, 5)

    def test_daily_quota_is_permanent(self):
        with self.assertRaises(PermanentLLMError):
            self._raise(429, '{"error": {"details": [{"quotaId": "GenerateRequestsPerDayPerProjectPerModel-FreeTier"}]}}')

    def test_per_minute_rate_limit_is_transient(self):
        with self.assertRaises(TransientLLMError):
            self._raise(429, '{"error": {"message": "Resource exhausted, retry later"}}')


class TestRetryAndFallback(unittest.TestCase):
    def test_retry_then_success(self):
        stats, n = CallStats(), {"i": 0}

        def fn():
            n["i"] += 1
            if n["i"] < 3:
                raise TransientLLMError("429", retry_after=0)
            return "ok"
        self.assertEqual(call_with_retry(fn, max_retries=4, base_delay=0, max_delay=0, stats=stats, sleep=lambda s: None), "ok")
        self.assertEqual(stats.retries, 2)

    def test_retries_exhausted(self):
        def fn():
            raise TransientLLMError("503")
        with self.assertRaises(TransientLLMError):
            call_with_retry(fn, max_retries=2, base_delay=0, max_delay=0, stats=CallStats(), sleep=lambda s: None)

    def test_permanent_error_not_retried(self):
        stats = CallStats()

        def fn():
            raise PermanentLLMError("401")
        with self.assertRaises(PermanentLLMError):
            call_with_retry(fn, max_retries=4, base_delay=0, max_delay=0, stats=stats, sleep=lambda s: None)
        self.assertEqual(stats.retries, 0)

    def _run(self, provider, path="leads_full_scale_100.csv"):
        cfg = copy.deepcopy(CONFIG)
        cfg["llm"].update(base_delay_seconds=0, requests_per_minute=0)
        with tempfile.TemporaryDirectory() as tmp:
            return run(ROOT / "data" / path, cfg, provider=provider, out_dir=tmp, sleep=lambda s: None)

    def test_bad_key_falls_back_for_every_lead(self):
        rep = self._run(FlakyProvider(10 ** 6, PermanentLLMError("401 invalid key")))
        self.assertEqual(rep["stats"]["total_processed"], 100)
        self.assertEqual(rep["stats"]["llm"]["judgment_source_counts"], {"fallback": 100})
        self.assertEqual(rep["stats"]["llm"]["api_calls"], 1)       # fail fast, no retry storm
        self.assertTrue(rep["stats"]["llm"]["circuit_breaker_opened"])

    def test_outage_opens_circuit_breaker(self):
        rep = self._run(FlakyProvider(10 ** 6, TransientLLMError("503")))
        llm = rep["stats"]["llm"]
        self.assertTrue(llm["circuit_breaker_opened"])
        self.assertEqual(llm["batches_sent"], 3)                    # stops after 3 failed batches

    def test_recovers_after_transient_errors(self):
        rep = self._run(FlakyProvider(2, TransientLLMError("429", retry_after=0)))
        self.assertEqual(rep["stats"]["llm"]["judgment_source_counts"], {"llm": 100})

    def test_unexpected_exception_does_not_crash_run(self):
        rep = self._run(FlakyProvider(10 ** 6, KeyError("bug in provider")))
        self.assertEqual(rep["stats"]["total_processed"], 100)
        self.assertTrue(rep["stats"]["llm"]["circuit_breaker_opened"])

    def test_chaos_run_never_loses_a_lead(self):
        from qualifier.llm_client import ChaosProvider
        rep = self._run(ChaosProvider(MockProvider(), failure_rate=0.5, seed=3))
        self.assertEqual(len(rep["leads"]), 100)
        self.assertTrue(all(l["decision"] in {"qualified", "review", "rejected"} for l in rep["leads"]))


class TestEndToEnd(unittest.TestCase):
    def test_all_datasets(self):
        for name in ["leads_training.csv", "leads_testing.csv", "leads_full_scale_100.csv", "leads_edge_cases_extra.csv"]:
            with self.subTest(name), tempfile.TemporaryDirectory() as tmp:
                rep = run(ROOT / "data" / name, CONFIG, out_dir=tmp)
                n = rep["stats"]["total_processed"]
                self.assertEqual(len(rep["leads"]), n)
                for l in rep["leads"]:
                    self.assertTrue(1 <= l["qualification_score"] <= 10)
                    self.assertTrue(l["reasoning"])
                    if l["decision"] == "qualified":
                        self.assertTrue(l["outreach"]["message"])
                        self.assertIsNotNone(l["priority_rank"])
                for f in ("output_report.json", "leads_scored.csv", "summary.md"):
                    self.assertTrue((Path(tmp) / f).exists())

    def test_batching_uses_few_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            rep = run(ROOT / "data" / "leads_full_scale_100.csv", CONFIG, out_dir=tmp)
        self.assertEqual(rep["stats"]["llm"]["batches_sent"], 10)   # 100 leads / batch_size 10


if __name__ == "__main__":
    unittest.main()
