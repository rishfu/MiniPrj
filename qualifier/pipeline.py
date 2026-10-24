"""
The pipeline: intake -> analyze (rules) -> analyze (LLM) -> decide -> output.

This file only wires the stages together; each stage lives in its own module,
which keeps every step small enough to test on its own.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .decide import attach_message, decide, rank_and_plan
from .ingest import apply_reference_date, load_leads, resolve_reference_date
from .judge import BatchJudge
from .llm_client import ChaosProvider, Provider, build_provider
from .messages import value_prop_for
from .models import LeadDecision
from .prompts import build_system_prompt, build_user_prompt, lead_payload
from .report import build_stats, lead_record, output_paths, pick_samples, queue_entry, write_outputs
from .rubric import Rubric

log = logging.getLogger("lead_qualifier.pipeline")

MANUAL_MINUTES_PER_LEAD = 10   # midpoint of the brief's 8-12 minutes


def run(input_path: str | Path, config: dict, *, provider: Optional[Provider] = None,
        provider_name: Optional[str] = None, model: Optional[str] = None,
        out_dir: Optional[str | Path] = None, reference_date: Optional[str] = None,
        failure_rate: float = 0.0, use_llm: bool = True, sleep=None) -> dict:
    t0 = time.monotonic()
    input_path = Path(input_path)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    rubric_cfg, llm_cfg, seller = config["rubric"], dict(config["llm"]), config["seller"]

    # 1. INTAKE ---------------------------------------------------------------
    leads, ingest_stats = load_leads(input_path)
    ref = resolve_reference_date(leads, reference_date or config["run"].get("reference_date", "auto"))
    apply_reference_date(leads, ref)
    log.info("Reference date for recency: %s", ref)

    # 2a. RULES ---------------------------------------------------------------
    rubric = Rubric(rubric_cfg)
    scored = [(lead, rubric.score(lead, ref)) for lead in leads]

    # 2b. LLM (batched) -------------------------------------------------------
    provider = provider or build_provider(llm_cfg, "mock" if not use_llm else provider_name, model)
    if failure_rate > 0:
        provider = ChaosProvider(provider, failure_rate)
        # Keep the demo fast: simulated failures don't need real 2-16s waits.
        llm_cfg["base_delay_seconds"] = min(llm_cfg.get("base_delay_seconds", 2.0), 0.2)
        llm_cfg["requests_per_minute"] = 0
    if provider.name.startswith("mock"):
        llm_cfg["requests_per_minute"] = 0   # nothing to throttle offline

    th, adj = rubric_cfg["thresholds"], rubric_cfg["llm_adjustment"]
    payloads, write_msg = [], {}
    for lead, rr in scored:
        # Only ask for a message when the lead can still reach "qualified" after
        # the best possible LLM nudge (saves output tokens on obvious rejects).
        cap = min((c["max_score"] for c in rr.caps), default=10.0)
        can_qualify = rr.base_score + adj["max_abs"] >= th["qualified_min"] and cap >= th["qualified_min"]
        write_msg[lead.lead_id] = can_qualify
        payloads.append(lead_payload(lead, rr, can_qualify, value_prop_for(lead.industry, seller["value_props"])))

    judge = BatchJudge(provider, llm_cfg, adj, build_system_prompt(seller, rubric.summary_text()),
                       build_user_prompt, sleep=sleep)
    judgments = judge.judge_all(payloads)

    # 3. DECIDE ---------------------------------------------------------------
    decisions: list[LeadDecision] = []
    for lead, rr in scored:
        d = decide(lead, rr, judgments[lead.lead_id], rubric_cfg)
        bad_msg = attach_message(d, seller, write_msg[lead.lead_id] or d.decision == "qualified")
        if bad_msg:
            log.info("%s: LLM message rejected (%s) - template used", lead.lead_id, bad_msg)
        decisions.append(d)
    rank_and_plan(decisions, rubric_cfg)

    # 4. OUTPUT ---------------------------------------------------------------
    elapsed = time.monotonic() - t0
    records = {d.lead.lead_id: lead_record(d) for d in decisions}
    by = lambda dec: sorted((queue_entry(records[d.lead.lead_id]) for d in decisions if d.decision == dec),
                            key=lambda r: (r["priority_rank"] or 10 ** 6, -r["qualification_score"]))
    report = {
        "run": {
            "run_id": run_id,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "input_file": input_path.name,
            "reference_date": ref.isoformat(),
            "llm_provider": provider.name,
            "llm_model": provider.model,
            "batch_size": llm_cfg.get("batch_size"),
            "rubric_version": rubric_cfg["version"],
            "rubric_summary": rubric.summary_text(),
        },
        "stats": build_stats(decisions, ingest_stats, judge, elapsed, MANUAL_MINUTES_PER_LEAD),
        "priority_queue": by("qualified"),
        "review_queue": by("review"),
        "disqualified": sorted(by("rejected"), key=lambda r: -r["qualification_score"]),
        "sample_outreach_messages": pick_samples(decisions, config["run"].get("sample_messages", 5)),
        "leads": [records[d.lead.lead_id] for d in decisions],
    }
    out_dir = Path(out_dir) if out_dir else Path(config["run"].get("output_root", "output")) / input_path.stem
    report["output_files"] = {k: str(v) for k, v in output_paths(out_dir).items()}
    write_outputs(report, decisions, out_dir)
    return report
